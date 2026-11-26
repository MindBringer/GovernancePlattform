"""Run the emitted Measure workflow against synthetic SharePoint protocol fixtures."""

from copy import deepcopy
from datetime import datetime
import json
import re
import unittest
from urllib.parse import unquote
from uuid import UUID

from test_control_write_flow import ControlWorkflow
from test_review_completion_flow import EvaluationError
from build_measure_write import build_flow

SITE = "https://example.sharepoint.com/sites/Portal"
LISTS = {name: str(UUID(int=i)) for i, name in enumerate(("measures", "controls", "evidence", "relations"), 1)}
FLOW = build_flow(SITE, "sp_test", *LISTS.values(), "W. Europe Standard Time")["properties"]


class MeasureWorkflow(ControlWorkflow):
    def call(self, name, args):
        if name == "parseDateTime":
            assert args[1:] == ["en-US", "yyyy-MM-dd"]
            return datetime.strptime(args[0], "%Y-%m-%d").isoformat()
        if name == "trim":
            return args[0].strip()
        return super().call(name, args)


class SharePoint:
    def __init__(self):
        self.measure = {"Id": 7, "OwnerId": 11, "Owner": {"Name": "i:0#.f|membership|owner@example.org"},
                        "MeasureStatus": "Geplant", "DueDate": "2026-10-23T22:00:00Z", "IsActive": True,
                        "EffectivenessValidationDate": None, "EffectivenessValidationResult": None,
                        "EditorId": 11, "OData__UIVersionString": "1.0",
                        "__metadata": {"type": "SP.Data.MeasuresListItem", "etag": '"1"'}}
        self.actor = 25
        self.permissions, self.link_permissions = 7, 7
        self.key_unique = True
        self.control = {"Id": 3, "IsActive": True}
        self.evidence = {"Id": 9, "FileSystemObjectType": 0}
        self.rows = {}
        self.calls = []
        self.writes = []
        self.failed_outputs = {}
        self.race = False
        self.lost_relation_response = False

    def http(self, action, request):
        self.calls.append(action)
        parameters = request["parameters"]
        assert parameters["dataset"] == SITE
        uri = unquote(parameters["parameters/uri"])
        if parameters["parameters/method"] == "POST":
            assert request["retryPolicy"] == {"type": "none"}
            payload = json.loads(parameters["parameters/body"])
            if action == "Write_measure":
                assert LISTS["measures"] in uri and self.permissions & 4
                headers = parameters["parameters/headers"]
                assert headers["X-HTTP-Method"] == "MERGE"
                if self.race or headers["IF-MATCH"] != self.measure["__metadata"]["etag"]:
                    self.failed_outputs[action] = {"statusCode": 412}
                    raise EvaluationError("revision changed")
                version = int(self.measure["OData__UIVersionString"].split(".")[0]) + 1
                self.measure["__metadata"]["etag"] = f'"{version}"'
                self.measure.update({k: v for k, v in payload.items() if k != "__metadata"})
                self.measure.update(OData__UIVersionString=f"{version}.0", EditorId=self.actor)
            else:
                assert action == "Write_link" and LISTS["relations"] in uri and self.link_permissions & 2
                assert self.key_unique and payload["RelationKey"] not in self.rows
                self.rows[payload["RelationKey"]] = {**payload, "Id": 31 + len(self.rows)}
            self.writes.append((action, payload))
            if action == "Write_link" and self.lost_relation_response:
                raise EvaluationError("unconfirmed relation response")
            return {}

        if action == "Read_actor":
            return {"d": {"Id": self.actor}}
        if action in {"Read_measure", "Read_measure_write"}:
            assert LISTS["measures"] in uri and "/items(7)?" in uri
            return {"d": {**deepcopy(self.measure), "EffectiveBasePermissions": {"Low": str(self.permissions)}}}
        if action == "Read_owner":
            assert "@login='i:0#.f|membership|planner@example.org'" in uri
            return {"d": {"PrincipalType": 1, "Id": 42}}
        if action in {"Read_link_source", "Read_proof"}:
            source = self.control if LISTS["controls"] in uri else self.evidence
            assert f"/items({source['Id']})?" in uri
            return {"d": source}
        assert LISTS["relations"] in uri
        if action == "Read_link_list":
            return {"d": {"EffectiveBasePermissions": {"Low": str(self.link_permissions)},
                          "ListItemEntityTypeFullName": "SP.Data.GovernanceRelationsListItem"}}
        if action == "Read_link_key":
            return {"d": {"Indexed": True, "EnforceUniqueValues": self.key_unique}}
        if action in {"Read_control_links", "Read_proof_link"}:
            assert "TargetItemID eq 7 and TargetObjectTypeKey eq 'Measure' and IsActive eq 1" in uri, uri
            key = "ControlImplementedByMeasure:Control:3:Measure:7"
            if action == "Read_proof_link":
                evidence_id = int(uri.rsplit("SourceItemID eq ", 1)[1])
                assert "RelationTypeKey eq 'EvidenceSupportsObject' and SourceObjectTypeKey eq 'Evidence'" in uri
                key = f"EvidenceSupportsObject:Evidence:{evidence_id}:Measure:7"
            row = self.rows.get(key)
            return {"d": {"results": [row] if row and row["IsActive"] else []}}
        key, = re.findall("RelationKey eq '([^']+)'", uri)
        return {"d": {"results": [self.rows[key]] if key in self.rows else []}}

    def run(self, action="prepare", argument="-", detail="-", source=0, revision=None):
        request = {"number": 7, "text": action, "text_1": revision or self.measure["__metadata"]["etag"],
                   "number_1": source, "text_2": argument, "text_3": detail}
        workflow = MeasureWorkflow(request, self)
        workflow.run(FLOW["definition"]["actions"])
        return workflow.outputs["Respond"]


class MeasureTests(unittest.TestCase):
    def test_invoker_and_platform_nesting_limit(self):
        def depth(actions):
            return max((1 + max(depth(row.get("actions", {})), depth(row.get("else", {}).get("actions", {})))
                        for row in actions.values()), default=0)

        self.assertEqual(FLOW["connectionReferences"]["shared_sharepointonline"]["runtimeSource"], "invoker")
        self.assertLessEqual(depth(FLOW["definition"]["actions"]), 8)

    def test_plan_with_site_day_and_conflicting_revision(self):
        sp = SharePoint()
        self.assertEqual(sp.run()["dueday"], "2026-10-24")
        self.assertEqual(sp.run("plan", "planner@example.org", "2026-10-26")["status"], "saved")
        self.assertEqual((sp.measure["OwnerId"], sp.measure["DueDate"]), (42, "2026-10-25T23:00:00Z"))
        self.assertEqual(sp.run("plan", "planner@example.org", "2026-10-26")["status"], "unchanged")
        self.assertEqual(sp.run("plan", "planner@example.org", "2026-10-27", revision='"1"')["status"], "conflict")
        sp.race = True
        self.assertEqual(sp.run("plan", "planner@example.org", "2026-10-27")["status"], "conflict")
        self.assertEqual(len(sp.writes), 1)

    def test_full_lifecycle_requires_control_and_exact_linked_file(self):
        sp = SharePoint()
        self.assertEqual(sp.run("advance", "In Umsetzung")["status"], "control_required")
        self.assertEqual(sp.run("control", source=3)["status"], "linked")
        self.assertEqual(sp.run("advance", "In Prüfung")["status"], "blocked")
        for status in ("In Umsetzung", "In Prüfung", "In Umsetzung", "In Prüfung"):
            self.assertEqual(sp.run("advance", status)["status"], "saved")
        self.assertEqual(sp.run("advance", "Wirksam", "Bestanden", source=9)["status"], "proof_required")
        self.assertEqual(sp.run("evidence", source=9)["status"], "linked")
        self.assertEqual(sp.run("advance", "Wirksam", "  ", source=9)["status"], "proof_required")
        self.assertEqual(sp.run("advance", "Wirksam", "Bestanden", source=8)["status"], "proof_required")
        sp.evidence["FileSystemObjectType"] = 1
        self.assertEqual(sp.run("advance", "Wirksam", "Bestanden", source=9)["status"], "proof_required")
        sp.evidence["FileSystemObjectType"] = 0
        self.assertEqual(sp.run("advance", "Wirksam", " Bestanden ", source=9)["status"], "saved")
        self.assertEqual((sp.measure["EffectivenessValidationResult"], sp.measure["EffectivenessValidationDate"]),
                         ("Bestanden", "2026-10-24T22:00:00Z"))
        self.assertEqual(sp.run("advance", "Geschlossen")["status"], "saved")
        self.assertEqual(sp.run("plan", "planner@example.org", "2026-10-29")["status"], "blocked")
        self.assertEqual(sp.measure["EffectivenessValidationResult"], "Bestanden")

    def test_reader_cannot_write_even_if_owner(self):
        sp = SharePoint()
        sp.permissions, sp.actor = 1, sp.measure["OwnerId"]
        self.assertFalse(sp.run()["canedit"])
        for action in ("plan", "advance", "control", "evidence"):
            self.assertEqual(sp.run(action, source=3)["status"], "blocked")
        self.assertFalse(sp.writes)

    def test_link_recovery_and_repetition_preserve_id_and_no_titles(self):
        for action, source in (("control", 3), ("evidence", 9)):
            with self.subTest(action=action):
                sp = SharePoint()
                sp.lost_relation_response = True
                first = sp.run(action, source=source)
                self.assertEqual((first["status"], first["relationid"]), ("linked", 31))
                self.assertEqual(sp.run(action, source=source), first)
                self.assertEqual(len(sp.writes), 1)
                link, = sp.rows.values()
                self.assertNotIn("SourceTitle", link)
                link["IsActive"] = False
                self.assertEqual(sp.run(action, source=source)["status"], "relation_conflict")
                self.assertEqual(len(sp.writes), 1)


if __name__ == "__main__":
    unittest.main()
