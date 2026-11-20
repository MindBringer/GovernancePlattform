"""Contract checks for the rendered workflow and its Canvas entry."""
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "powerplatform/flows/build_evidence_upload.py"
spec = importlib.util.spec_from_file_location("evidence_upload", BUILDER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

ASSETS = "00000000-0000-0000-0000-000000000001"
RELATIONS = "00000000-0000-0000-0000-000000000002"
CHANGES = "00000000-0000-0000-0000-000000000003"
RISKS = "00000000-0000-0000-0000-000000000004"
SITE = "https://example.sharepoint.com/sites/Governance"
CONNECTION = "test_sharepoint"


def actions_at(actions, *names):
    current = actions
    for name in names[:-1]:
        current = current[name]["actions"]
    return current[names[-1]]


def all_actions(actions):
    for action in actions.values():
        yield action
        yield from all_actions(action.get("actions", {}))
        yield from all_actions(action.get("else", {}).get("actions", {}))


class EvidenceWorkflowContract(unittest.TestCase):
    def setUp(self):
        self.flow = module.build_flow(SITE, CONNECTION, ASSETS, RELATIONS)["properties"]
        self.definition = self.flow["definition"]
        self.actions = self.definition["actions"]
        self.valid = self.actions["Validate_request"]["actions"]
        self.rights = self.valid["Can_add_to_both"]["actions"]
        self.upload = self.rights["Require_unique_key"]["actions"]
        self.compare = self.upload["Validate_file_readback"]["actions"]["Confirm_file"]
        self.link = self.compare["actions"]

    def test_trusted_connection_and_identities(self):
        refs = self.flow["connectionReferences"]
        self.assertEqual(list(refs), [module.CONNECTOR])
        self.assertEqual(refs[module.CONNECTOR]["runtimeSource"], "invoker")
        self.assertEqual(refs[module.CONNECTOR]["connection"]["connectionReferenceLogicalName"], CONNECTION)
        for action in all_actions(self.actions):
            if action["type"] == "OpenApiConnection":
                self.assertEqual(action["inputs"]["parameters"]["dataset"], SITE)
                self.assertEqual(action["inputs"]["host"]["connectionName"], module.CONNECTOR)
        self.assertEqual(self.valid["Read_asset"]["inputs"]["parameters"]["table"], ASSETS)
        self.assertEqual(self.link["Read_relation"]["inputs"]["parameters"]["table"], RELATIONS)
        self.assertIn("int(triggerBody()?['number'])", self.valid["Read_asset"]["inputs"]["parameters"]["id"])

    def test_no_file_write_without_asset_permissions_and_native_unique_key(self):
        self.assertEqual(self.valid["Evidence_permissions"]["runAfter"], {"Read_asset": ["Succeeded"]})
        rights = self.valid["Can_add_to_both"]
        self.assertIn("EffectiveBasePermissions", rights["expression"])
        self.assertIn("Relation_permissions", rights["expression"])
        self.assertIn("Evidence_permissions", rights["expression"])
        key = self.rights["Require_unique_key"]
        self.assertEqual(key["expression"], "@equals(body('Read_relation_key_contract')?['EnforceUniqueValues'], true)")
        writes = [action for action in all_actions(self.actions) if action["type"] == "OpenApiConnection"
                  and action["inputs"].get("retryPolicy")]
        self.assertEqual(len(writes), 2)
        self.assertTrue(all(action["inputs"]["retryPolicy"] == {"type": "none"} for action in writes))

    def test_file_create_is_repeatable_even_after_an_uncertain_response(self):
        self.assertEqual(self.upload["Create_if_not_found"]["expression"], "@equals(outputs('Find_file')?['statusCode'], 404)")
        writer = actions_at(self.upload, "Create_if_not_found", "Create_file_no_overwrite")
        parameters = writer["inputs"]["parameters"]
        self.assertIn("overwrite=false", parameters["parameters/uri"])
        self.assertIn("uriComponent(outputs('Stored_filename'))", parameters["parameters/uri"])
        self.assertTrue(parameters["parameters/body"].startswith("@base64ToBinary("))
        self.assertIn("Failed", self.upload["Read_file"]["runAfter"]["Create_if_not_found"])
        self.assertEqual(self.upload["Read_file_bytes"]["inputs"]["parameters"]["path"], "@outputs('File_path')")
        self.assertIn("body('Read_asset')?['ID']", self.upload["Stored_filename"]["inputs"])

    def test_only_verified_bytes_can_be_linked_or_reported_as_a_conflict(self):
        guard = self.upload["Validate_file_readback"]
        self.assertEqual(guard["runAfter"], {"Read_file_bytes": ["Succeeded"]})
        self.assertIn("not(empty(coalesce(outputs('Read_file_bytes')?['body']?['$content'], '')))", guard["expression"])
        self.assertEqual(guard["else"]["actions"], {})
        self.assertEqual(self.upload["Mark_transfer_pending"]["inputs"]["value"]["status"], "retry")
        self.assertEqual(self.compare["expression"],
                         "@equals(base64ToBinary(outputs('Read_file_bytes')?['body']?['$content']), "
                         "base64ToBinary(triggerBody()?['file']?['contentBytes']))")
        self.assertEqual(set(self.compare["else"]["actions"]), {"Mark_other_content"})
        self.assertEqual(self.compare["else"]["actions"]["Mark_other_content"]["inputs"]["value"]["status"],
                         "file_conflict")

    def test_relation_uses_unique_instance_and_reads_back_after_conflict(self):
        key = self.link["Relation_key"]["inputs"]
        for expected in ("EvidenceSupportsObject:Evidence:", ":Asset:", "Read_file", "Read_asset"):
            self.assertIn(expected, key)
        writer = actions_at(self.link, "Insert_if_absent", "Create_relation")["inputs"]["parameters"]
        self.assertEqual(writer["item/RelationKey"], "@outputs('Relation_key')")
        self.assertEqual(writer["item/RelationID"], "@outputs('Relation_key')")
        self.assertIn("Read_file", writer["item/SourceItemID"])
        self.assertIn("Read_asset", writer["item/TargetItemID"])
        read_after = self.link["Verify_relation"]
        self.assertIn("Failed", read_after["runAfter"]["Insert_if_absent"])
        self.assertEqual(read_after["inputs"]["parameters"], self.link["Read_relation"]["inputs"]["parameters"])
        self.assertEqual(read_after["inputs"]["parameters"]["$top"], 2)
        self.assertIn("equals(length(", self.link["Confirm_one_relation"]["expression"])
        match = actions_at(self.link, "Confirm_one_relation", "Confirm_relation_content")["expression"]
        for field in ("SourceItemID", "TargetItemID", "SourceObjectTypeKey", "TargetObjectTypeKey", "IsActive", "RelationKey"):
            self.assertIn(field, match)

    def test_failure_and_response_are_explicit_and_numeric(self):
        self.assertEqual(self.link["Mark_unlinked"]["inputs"]["value"]["status"], "unlinked")
        self.assertIn("Read_file", self.link["Mark_unlinked"]["inputs"]["value"]["evidenceid"])
        response = self.actions["Respond_to_canvas"]["inputs"]
        schema = response["schema"]["properties"]
        self.assertEqual(set(response["body"]), {"status", "assetid", "evidenceid", "relationid"})
        self.assertEqual(response["body"],
                         {name: f"@variables('result')?['{name}']" for name in schema})
        self.assertTrue(all(field["x-ms-dynamically-added"] for field in schema.values()))
        self.assertEqual({field for field, value in schema.items() if value["type"] == "number"},
                         {"assetid", "evidenceid", "relationid"})
        self.assertEqual(self.definition["triggers"]["manual"]["kind"], "PowerAppV2")
        inputs = self.definition["triggers"]["manual"]["inputs"]["schema"]["properties"]
        self.assertTrue(all(field.get("description") for field in inputs.values()))


    def test_canvas_uses_attachment_picking_without_creating_an_asset(self):
        canvas = (ROOT / "powerplatform/canvas/GovernancePortal/Src/scrAssetEvidenceUpload.pa.yaml").read_text()
        self.assertIn("Control: Attachments@", canvas)
        self.assertIn("DataSource: =Assets", canvas)
        self.assertIn("MaxAttachments: =1", canvas)
        self.assertIn("GPAssetEvidenceUpload.Run(evidenceUploadTargetId,", canvas)
        self.assertIn("targetid: assetAnswer.assetid", canvas)
        self.assertIn("GPObjectEvidenceUpload.Run(evidenceUploadTargetId, evidenceUploadTargetType,", canvas)
        self.assertIn("answer.targetid = evidenceUploadTargetId && answer.targettype = evidenceUploadTargetType", canvas)
        self.assertIn("gblAssetPilotCanWrite", canvas)
        self.assertIsNone(re.search(r"\b(?:SubmitForm|Patch|Collect|Remove)\(", canvas))

    def test_architecture_makes_instance_key_unique_but_reuses_types(self):
        model = json.loads((ROOT / "architecture/fields.yaml").read_text())["fields"]
        fields = {row["internalName"]: row for row in model if row.get("scope") == "relation"}
        self.assertTrue(fields["RelationKey"]["unique"])
        self.assertTrue(fields["RelationKey"]["indexed"])
        self.assertFalse(fields["RelationTypeKey"].get("unique", False))


class ObjectEvidenceWorkflowContract(unittest.TestCase):
    def setUp(self):
        self.flow = module.build_flow(SITE, CONNECTION, None, RELATIONS,
                                      changes_list=CHANGES, risks_list=RISKS)["properties"]
        self.definition = self.flow["definition"]
        self.actions = self.definition["actions"]
        self.request = self.actions["Validate_request"]
        self.authorized = self.request["actions"]
        self.transfer = actions_at(self.authorized, "Can_add_to_both", "Require_unique_key")["actions"]
        self.link = actions_at(self.transfer, "Validate_file_readback", "Confirm_file")["actions"]

    def test_allowlisted_object_type_resolves_preconfigured_list_and_native_id(self):
        inputs = self.definition["triggers"]["manual"]["inputs"]["schema"]
        self.assertEqual(inputs["required"], ["number", "text", "file"])
        self.assertEqual(inputs["properties"]["text"]["type"], "string")
        self.assertIn("contains(createArray('Change','Risk'), triggerBody()?['text'])", self.request["expression"])
        self.assertIn("equals(triggerBody()?['number'], int(triggerBody()?['number']))", self.request["expression"])
        self.assertEqual(self.request["else"]["actions"], {})
        self.assertEqual(self.authorized["Target_list"]["inputs"],
                         f"@if(equals(triggerBody()?['text'], 'Change'), '{CHANGES}', '{RISKS}')")
        read = self.authorized["Read_target"]
        self.assertEqual(read["inputs"]["parameters"]["parameters/method"], "GET")
        self.assertEqual(read["runAfter"], {"Target_list": ["Succeeded"]})
        self.assertIn("outputs('Target_list')", read["inputs"]["parameters"]["parameters/uri"])
        self.assertIn("string(int(triggerBody()?['number']))", read["inputs"]["parameters"]["parameters/uri"])

    def test_inaccessible_or_read_only_target_cannot_reach_either_write(self):
        self.assertEqual(self.flow["connectionReferences"][module.CONNECTOR]["runtimeSource"], "invoker")
        self.assertEqual(self.authorized["Mark_blocked"]["inputs"]["value"]["status"], "blocked")
        self.assertEqual(self.authorized["Evidence_permissions"]["runAfter"], {"Read_target": ["Succeeded"]})
        self.assertIn("EffectiveBasePermissions", self.authorized["Read_target"]["inputs"]["parameters"]["parameters/uri"])
        gate = self.authorized["Can_add_to_both"]
        self.assertIn("equals(triggerBody()?['number'], int(body('Read_target')?['Id']))", gate["expression"])
        self.assertIn("equals(mod(div(int(body('Read_target')?['EffectiveBasePermissions']?['Low']), 4), 2), 1)",
                      gate["expression"])
        self.assertEqual(gate["else"]["actions"], {})
        policy = self.authorized["Can_add_to_both"]["actions"]["Require_unique_key"]
        self.assertEqual(policy["expression"], "@equals(body('Read_relation_key_contract')?['EnforceUniqueValues'], true)")
        writes = [x for x in all_actions(self.actions)
                  if x["type"] == "OpenApiConnection" and x["inputs"].get("retryPolicy")]
        transfer_writes = [x for x in all_actions(self.transfer)
                           if x["type"] == "OpenApiConnection" and x["inputs"].get("retryPolicy")]
        self.assertEqual(writes, transfer_writes)
        self.assertEqual(len(transfer_writes), 2)

    def test_file_and_relation_identity_both_include_object_type(self):
        self.assertEqual(self.transfer["Stored_filename"]["inputs"],
                         "@concat(toLower(triggerBody()?['text']), '-', string(body('Read_target')?['Id']), '--', outputs('Filename'))")
        key = self.link["Relation_key"]["inputs"]
        self.assertIn("triggerBody()?['text']", key)
        self.assertIn("body('Read_target')?['Id']", key)
        self.assertNotIn(":Asset:", key)
        relation = actions_at(self.link, "Insert_if_absent", "Create_relation")["inputs"]["parameters"]
        self.assertEqual(relation["item/TargetObjectTypeKey"], "@triggerBody()?['text']")
        self.assertEqual(relation["item/TargetItemID"], "@int(body('Read_target')?['Id'])")
        self.assertEqual(relation["item/TargetTitle"], "@body('Read_target')?['Title']")
        confirmed = actions_at(self.link, "Confirm_one_relation", "Confirm_relation_content")
        self.assertIn("?['TargetObjectTypeKey'], triggerBody()?['text']", confirmed["expression"])
        saved = confirmed["actions"]["Mark_saved"]["inputs"]["value"]
        self.assertEqual(saved["targettype"], "@triggerBody()?['text']")
        self.assertEqual(saved["targetid"], "@int(body('Read_target')?['Id'])")
        schema = self.actions["Respond_to_canvas"]["inputs"]["schema"]["properties"]
        self.assertEqual(schema["targettype"]["type"], "string")
        self.assertEqual(schema["targetid"]["type"], "number")
        self.assertNotIn("assetid", schema)

    def test_ambiguous_list_configuration_fails_before_rendering(self):
        for asset, change, risk in ((ASSETS, CHANGES, RISKS), (None, CHANGES, None),
                                    (None, CHANGES, CHANGES), (None, RELATIONS, RISKS)):
            with self.subTest(asset=asset, change=change, risk=risk), self.assertRaises(ValueError):
                module.build_flow(SITE, CONNECTION, asset, RELATIONS, changes_list=change, risks_list=risk)


if __name__ == "__main__":
    unittest.main()
