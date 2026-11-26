"""Run the Finding workflow against synthetic SharePoint permission and revision fixtures."""

from copy import deepcopy
import json
import unittest
from urllib.parse import unquote
from uuid import UUID

from test_measure_write_flow import MeasureWorkflow
from test_review_completion_flow import EvaluationError
from build_finding_write import CONNECTOR, build_flow

SITE = "https://example.sharepoint.com/sites/Portal"
LISTS = {name: str(UUID(int=index)) for index, name in
         enumerate(("Findings", "AuditFindings", "Reviews", "Audit", "Measures", "Evidence"), 1)}
FLOW = build_flow(SITE, "sp_test", *LISTS.values(), "W. Europe Standard Time")["properties"]


class FindingWorkflow(MeasureWorkflow):
    def call(self, name, args):
        if name == "startsWith":
            return args[0].startswith(args[1])
        if name == "replace":
            return args[0].replace(args[1], args[2])
        return super().call(name, args)


class SharePoint:
    def __init__(self):
        self.actor = 25
        self.owner = {"Id": 25, "PrincipalType": 1}
        self.rights = {"Findings": 7, "AuditFindings": 7}
        self.source = {"Reviews": {"Id": 5, "ManualReviewState": "Abgeschlossen"},
                       "Audit": {"Id": 5, "FileSystemObjectType": 0},
                       "Measures": {"Id": 9, "IsActive": True, "MeasureStatus": "Wirksam"},
                       "Evidence": {"Id": 8, "IsActive": True, "FileSystemObjectType": 0, "OData__UIVersionString": "3.0"}}
        self.rows = {"Findings": {}, "AuditFindings": {}}
        self.calls, self.writes = [], []
        self.failed_outputs = {}
        self.lost_create_reply = self.race = self.readback_drift = False
        self.unique_key = True

    def http(self, action, request):
        self.calls.append(action)
        args = request["parameters"]
        method, uri = args["parameters/method"], unquote(args["parameters/uri"])
        assert args["dataset"] == SITE
        if action == "Read_actor":
            return {"d": {"Id": self.actor}}
        if action == "Read_owner":
            assert "@login='i:0#.f|membership|owner@example.org'" in uri
            return {"d": deepcopy(self.owner)}
        name, = (name for name, guid in LISTS.items() if f"lists(guid'{guid}')" in uri)
        if name in self.source:
            row = self.source[name]
            if not row or f"/items({row['Id']})?" not in uri:
                raise EvaluationError("Source not found or not readable")
            assert method == "GET"
            return {"d": deepcopy(row)}
        rights = self.rights[name]
        if not rights & 1:
            raise EvaluationError("No list access")
        fields = self.rows[name]
        if method == "POST":
            assert request["retryPolicy"] == {"type": "none"}
            data = json.loads(args["parameters/body"])
            metadata = data.pop("__metadata")
            assert metadata == {"type": f"SP.Data.{name}ListItem"}
            if action == "Create_finding":
                assert rights & 2 and all(r["GovernanceID"] != data["GovernanceID"] for r in fields.values())
                row = {**data, "Id": len(fields) + 1, "AuthorId": self.actor, "EditorId": self.actor,
                       "OData__UIVersionString": "1.0", "__metadata": {**metadata, "etag": '"1"'}}
                fields[row["Id"]] = row
            else:
                assert action == "Merge_finding" and rights & 4
                row = fields[int(uri.split("/items(")[1].split(")")[0])]
                headers = args["parameters/headers"]
                assert headers["X-HTTP-Method"] == "MERGE"
                if self.race or headers["IF-MATCH"] != row["__metadata"]["etag"]:
                    self.failed_outputs[action] = {"statusCode": 412}
                    raise EvaluationError("412")
                version = int(row["OData__UIVersionString"].split(".")[0]) + 1
                row.update(data, EditorId=self.actor, OData__UIVersionString=f"{version}.0")
                row["__metadata"]["etag"] = f'"{version}"'
            self.writes.append((name, action, data))
            if action == "Create_finding" and self.lost_create_reply:
                raise EvaluationError("Timed out after create")
            return {}
        if action == "Read_list":
            return {"d": {"ListItemEntityTypeFullName": f"SP.Data.{name}ListItem",
                          "EffectiveBasePermissions": {"Low": str(rights)}}}
        if action == "Read_key":
            assert "'GovernanceID'" in uri
            return {"d": {"EnforceUniqueValues": self.unique_key, "Indexed": True}}
        if action in {"Read_before_create", "Read_after_create"}:
            key = uri.split("GovernanceID eq '", 1)[1][:-1].replace("''", "'")
            return {"d": {"results": [deepcopy(r) for r in fields.values() if r["GovernanceID"] == key]}}
        row = deepcopy(fields[int(uri.split("/items(")[1].split(")")[0])])
        row["EffectiveBasePermissions"] = {"Low": str(rights)}
        if action == "Read_after_edit" and self.readback_drift:
            row["FindingEvidenceItemID"] = 99
        return {"d": row}

    def run(self, action, scope="review", args=None, revision=None):
        name = "AuditFindings" if scope == "audit" else "Findings"
        item = self.rows[name].get(1)
        revision = revision if revision is not None else (item["__metadata"]["etag"] if item else "-")
        inputs = {"text": scope, "text_1": action, "number": 0 if action == "create" else 1,
                  "text_2": revision, "text_3": json.dumps(args or {})}
        workflow = FindingWorkflow(inputs, self)
        workflow.run(FLOW["definition"]["actions"])
        return workflow.outputs["Respond"]

    def create(self, scope="review", **changes):
        prefix = "FNA-" if scope == "audit" else "FND-"
        args = {"key": prefix + "A" * 32, "title": "Synthetische Feststellung", "description": "Abweichung",
                "source": 5, "owner": "owner@example.org", "due": "2026-10-26", "measure": 9, "evidence": 8}
        return self.run("create", scope, args={**args, **changes})


class FindingTests(unittest.TestCase):
    def test_isolated_review_and_audit_with_read_only_actor(self):
        sp = SharePoint()
        for scope in ("review", "audit"):
            self.assertEqual(sp.create(scope)["status"], "saved")
        self.assertEqual([name for name, _, _ in sp.writes], ["Findings", "AuditFindings"])
        sp.rights = {"Findings": 1, "AuditFindings": 0}
        self.assertFalse(sp.run("prepare")["canedit"])
        self.assertEqual(sp.run("start")["status"], "denied")
        self.assertEqual(sp.run("prepare", "audit")["status"], "unavailable")
        self.assertEqual(sp.create("audit")["status"], "denied")
        self.assertEqual(len(sp.writes), 2)

    def test_source_kind_and_active_targets(self):
        sp = SharePoint()
        sp.source["Audit"]["FileSystemObjectType"] = 1
        sp.source["Reviews"]["ManualReviewState"] = "In Prüfung"
        self.assertEqual(sp.create()["status"], "source_unavailable")
        self.assertEqual(sp.create("audit")["status"], "source_unavailable")
        sp.source["Reviews"]["ManualReviewState"] = "Abgeschlossen"
        sp.source["Evidence"]["FileSystemObjectType"] = 1
        self.assertEqual(sp.create()["status"], "evidence_unavailable")
        self.assertFalse(sp.writes)

    def test_creation_is_idempotent_and_uses_native_key(self):
        sp = SharePoint()
        sp.unique_key = False
        self.assertEqual(sp.create()["status"], "request_key_unavailable")
        sp.unique_key = True
        sp.lost_create_reply = True
        self.assertEqual(sp.create()["status"], "saved")
        self.assertEqual(sp.create()["itemid"], 1)
        self.assertEqual(sp.create(title="Abweichender Wiederholungsversuch")["status"], "request_conflict")
        self.assertEqual(len(sp.writes), 1)

    def test_closure_requires_owner_effective_measure_and_versioned_evidence(self):
        sp = SharePoint()
        self.assertEqual(sp.create()["status"], "saved")
        self.assertEqual(sp.run("start")["status"], "saved")
        note = {"note": "Ergebnis nachvollzogen"}
        sp.actor = 42
        self.assertEqual(sp.run("close", args=note)["status"], "invalid_transition")
        sp.actor = 25
        sp.source["Measures"]["MeasureStatus"] = "In Umsetzung"
        self.assertEqual(sp.run("close", args=note)["status"], "measure_unavailable")
        sp.source["Measures"]["MeasureStatus"] = "Wirksam"
        sp.source["Evidence"]["OData__UIVersionString"] = ""
        self.assertEqual(sp.run("close", args=note)["status"], "evidence_unavailable")
        sp.source["Evidence"]["OData__UIVersionString"] = "3.0"
        self.assertEqual(sp.run("close", args=note)["status"], "saved")
        row = sp.rows["Findings"][1]
        self.assertEqual((row["FindingStatus"], row["FindingClosedById"], row["FindingEvidenceVersion"]),
                         ("Abgeschlossen", 25, "3.0"))
        self.assertFalse(sp.run("prepare")["canedit"])
        self.assertEqual(len(sp.writes), 3)

    def test_planning_normalizes_due_date_and_stops_on_conflict(self):
        sp = SharePoint()
        self.assertEqual(sp.create(measure=0, evidence=0)["status"], "saved")
        plan = {"owner": "owner@example.org", "due": "2026-10-27", "measure": 9, "evidence": 8}
        self.assertEqual(sp.run("plan", args=plan, revision='"0"')["status"], "conflict")
        sp.race = True
        self.assertEqual(sp.run("plan", args=plan)["status"], "conflict")
        sp.race = False
        self.assertEqual(sp.run("plan", args=plan)["status"], "saved")
        self.assertEqual(sp.rows["Findings"][1]["FindingDueDate"], "2026-10-26T23:00:00Z")
        sp.readback_drift = True
        self.assertEqual(sp.run("start")["status"], "uncertain")
        self.assertEqual(len(sp.writes), 3)

    def test_invoker_and_platform_nesting(self):
        def depth(actions):
            return max((1 + max(depth(a.get("actions", {})), depth(a.get("else", {}).get("actions", {})))
                        for a in actions.values()), default=0)
        self.assertEqual(FLOW["connectionReferences"][CONNECTOR]["runtimeSource"], "invoker")
        self.assertLessEqual(depth(FLOW["definition"]["actions"]), 8)


if __name__ == "__main__":
    unittest.main()
