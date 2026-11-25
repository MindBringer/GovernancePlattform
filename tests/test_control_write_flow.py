"""Exercise the emitted Control workflow with native SharePoint protocol fixtures."""

from copy import deepcopy
import json
import re
import unittest
from urllib.parse import unquote

from test_review_completion_flow import EvaluationError, Workflow
from build_control_write import build_flow


SITE = "https://example.sharepoint.com/sites/Portal"
LISTS = {name: f"00000000-0000-0000-0000-00000000000{i}"
         for i, name in enumerate(("controls", "risks", "evidence", "relations"), 1)}
FLOW = build_flow(SITE, "sp_test", *(LISTS[key] for key in LISTS))["properties"]


class SharePoint:
    def __init__(self):
        self.actor, self.permissions, self.relation_permissions = 25, 7, 7
        self.control = {"Id": 7, "OwnerId": 20, "IsActive": True, "EditorId": 20,
                        "__metadata": {"type": "SP.Data.ControlsListItem", "etag": '"1"'}}
        self.owner, self.risk, self.evidence = {"Id": 23, "PrincipalType": 1}, {"Id": 8, "IsActive": True}, {"Id": 8, "FileSystemObjectType": 0}
        self.key_unique = True
        self.rows = {}
        self.writes = []
        self.calls = []
        self.failed_outputs = {}
        self.before_owner_write = False
        self.compete_for_link = False
        self.lost_link_reply = False

    def http(self, action, request):
        self.calls.append(action)
        parameters = request["parameters"]
        assert parameters["dataset"] == SITE
        uri = unquote(parameters["parameters/uri"])
        if parameters["parameters/method"] == "POST":
            payload = json.loads(parameters["parameters/body"])
            assert request["retryPolicy"] == {"type": "none"}
            if action == "Write_owner":
                assert LISTS["controls"] in uri and self.permissions & 4
                headers = parameters["parameters/headers"]
                assert headers["X-HTTP-Method"] == "MERGE"
                if self.before_owner_write:
                    self.control["__metadata"]["etag"] = '"2"'
                if headers["IF-MATCH"] != self.control["__metadata"]["etag"]:
                    self.failed_outputs[action] = {"statusCode": 412}
                    raise EvaluationError("412")
                assert set(payload) == {"__metadata", "OwnerId"}
                self.control.update(OwnerId=payload["OwnerId"], EditorId=self.actor)
                self.control["__metadata"]["etag"] = '"2"'
            else:
                assert action == "Insert_relation" and LISTS["relations"] in uri and self.relation_permissions & 2
                key = payload["RelationKey"]
                assert key not in self.rows
                self.rows[key] = {**payload, "Id": 51}
                if self.compete_for_link:
                    raise EvaluationError("unique conflict")
            self.writes.append((action, payload))
            if self.lost_link_reply and action == "Insert_relation":
                raise EvaluationError("uncertain response")
            return {}
        if action == "Read_actor":
            return {"d": {"Id": self.actor}}
        if action in ("Read_control", "Read_owner_write"):
            assert LISTS["controls"] in uri and "/items(7)?" in uri
            if not self.permissions & 1:
                raise EvaluationError("403")
            return {"d": {**deepcopy(self.control), "EffectiveBasePermissions": {"Low": str(self.permissions)}}}
        if action == "Read_owner":
            assert "@login='i:0#.f|membership|operator@example.org'" in uri
            if not self.owner:
                raise EvaluationError("404")
            return {"d": self.owner}
        if action == "Read_source":
            assert "/items(8)?" in uri
            row = self.risk if LISTS["risks"] in uri else self.evidence
            if not row:
                raise EvaluationError("403")
            return {"d": row}
        assert LISTS["relations"] in uri
        if action == "Read_relation_list":
            return {"d": {"EffectiveBasePermissions": {"Low": str(self.relation_permissions)},
                          "ListItemEntityTypeFullName": "SP.Data.GovernanceRelationsListItem"}}
        if action == "Read_key_contract":
            return {"d": {"EnforceUniqueValues": self.key_unique, "Indexed": True}}
        key, = re.findall("RelationKey eq '([^']+)'", uri)
        return {"d": {"results": [self.rows[key]] if key in self.rows else []}}


class ControlWorkflow(Workflow):
    def call(self, name, args):
        if name == "outputs" and args[0] in self.sharepoint.failed_outputs:
            return self.sharepoint.failed_outputs[args[0]]
        return super().call(name, args)


def execute(sp, action="prepare", revision='"1"', source=8, owner="operator@example.org", control=7):
    run = ControlWorkflow({"number": control, "text": action, "text_1": revision, "number_1": source, "text_2": owner}, sp)
    run.run(FLOW["definition"]["actions"])
    return run.outputs["Respond"]


class ControlWorkflowTests(unittest.TestCase):
    def test_power_automate_control_action_nesting_limit(self):
        def depth(actions):
            return max((1 + max(depth(action.get("actions", {})), depth(action.get("else", {}).get("actions", {})))
                        for action in actions.values()), default=0)

        self.assertLessEqual(depth(FLOW["definition"]["actions"]), 8)

    def test_owner_assignment_and_native_revision(self):
        sp = SharePoint()
        self.assertEqual(FLOW["connectionReferences"]["shared_sharepointonline"]["runtimeSource"], "invoker")
        before = execute(sp)
        self.assertEqual((before["status"], before["revision"], before["canedit"]), ("ready", '"1"', True))
        self.assertEqual(execute(sp, "owner")["status"], "assigned")
        self.assertEqual(sp.control["OwnerId"], 23)
        self.assertEqual(execute(sp, "owner", revision='"2"')["status"], "unchanged")
        self.assertEqual(len(sp.writes), 1)
        self.assertEqual(execute(sp, "owner")["status"], "conflict")

    def test_retry_and_competing_create_resolve_to_one_link(self):
        kinds = {"risk": "RiskMitigatedByControl:Risk:8:Control:7", "evidence": "EvidenceSupportsObject:Evidence:8:Control:7"}
        for action, key in kinds.items():
            for lost_reply, race in ((True, False), (False, True), (False, False)):
                with self.subTest(action=action, lost=lost_reply, race=race):
                    sp = SharePoint()
                    sp.lost_link_reply, sp.compete_for_link = lost_reply, race
                    first = execute(sp, action)
                    self.assertEqual((first["status"], first["relationid"]), ("linked", 51))
                    self.assertEqual(execute(sp, action), first)
                    self.assertEqual(list(sp.rows), [key])
                    self.assertEqual(sp.calls.count("Insert_relation"), 1)
                    self.assertNotIn("SourceTitle", sp.rows[key])
                    self.assertNotIn("TargetTitle", sp.rows[key])

    def test_reader_blocks_all_writes_despite_other_access(self):
        sp = SharePoint()
        sp.permissions = 1
        self.assertFalse(execute(sp)["canedit"])
        for action in ("owner", "risk", "evidence"):
            self.assertEqual(execute(sp, action)["status"], "blocked")
        self.assertFalse(sp.writes)

    def test_run_permissions_invalid_source_and_nonunique_schema_fail_closed(self):
        cases = (("risk", "risk", {"Id": 8, "IsActive": False}, "source_unavailable"),
                 ("risk", "risk", None, "source_unavailable"),
                 ("evidence", "evidence", {"Id": 8, "FileSystemObjectType": 1}, "source_unavailable"),
                 ("evidence", "relation_permissions", 1, "blocked"),
                 ("risk", "key_unique", False, "configuration"),
                 ("owner", "owner", None, "owner_unavailable"))
        for action, attr, value, status in cases:
            with self.subTest(action=action, attr=attr):
                sp = SharePoint()
                setattr(sp, attr, value)
                self.assertEqual(execute(sp, action)["status"], status)
                self.assertFalse(sp.writes)

    def test_owner_race_has_no_write_and_tombstone_is_not_reactivated(self):
        sp = SharePoint()
        sp.before_owner_write = True
        self.assertEqual(execute(sp, "owner")["status"], "conflict")
        self.assertEqual(sp.control["OwnerId"], 20)
        key = "RiskMitigatedByControl:Risk:8:Control:7"
        sp.rows[key] = {"Id": 52, "RelationKey": key, "IsActive": False}
        self.assertEqual(execute(sp, "risk", revision='"2"')["status"], "relation_conflict")
        self.assertFalse(sp.writes)
        self.assertFalse(sp.rows[key]["IsActive"])

    def test_invalid_mode_identifiers_and_principal_never_reach_sharepoint(self):
        for kwargs in ({"action": "delete"}, {"control": 0}, {"action": "risk", "source": 8.5},
                       {"action": "owner", "owner": "o'hara@example.org"}):
            sp = SharePoint()
            self.assertEqual(execute(sp, **kwargs)["status"], "invalid")
            self.assertFalse(sp.calls)


if __name__ == "__main__":
    unittest.main()
