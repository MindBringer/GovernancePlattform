"""Run the generated transition definition against SharePoint protocol fixtures."""

from copy import deepcopy
import json
import unittest

from test_review_completion_flow import EvaluationError, Workflow
from build_incident_transition import CONNECTOR, build_flow


SITE = "https://example.sharepoint.com/sites/Portal"
LIST = "00000000-0000-0000-0000-000000000001"
FLOW = build_flow(SITE, "sp_test", LIST, "W. Europe Standard Time")["properties"]


class SharePoint:
    def __init__(self, security=False):
        self.uri = f"_api/web/lists(guid'{LIST}')/items(7)"
        self.item = {
            "Id": 7, "PortalStatus": "New", "ResolvedDate": None, "OwnerId": 21, "LinkedSystemId": 3,
            "Priority": "Hoch", "SecurityIncident": security, "EditorId": 21, "OData__UIVersionString": "1.0",
            "__metadata": {"etag": '"1"', "type": "SP.Data.IncidentsListItem"},
        }
        self.actor = 21
        self.permissions = 7
        self.requests = []
        self.writes = []
        self.failed_outputs = {}
        self.race = False
        self.readback_fault = None

    def revise(self):
        version = int(self.item["OData__UIVersionString"].split(".", 1)[0]) + 1
        self.item.update(OData__UIVersionString=f"{version}.0")
        self.item["__metadata"]["etag"] = f'"{version}"'

    def http(self, action, request):
        parameters = request["parameters"]
        self.requests.append(action)
        assert parameters["dataset"] == SITE
        uri = parameters["parameters/uri"]
        if action == "Current_user":
            assert uri == "_api/web/currentuser?$select=Id"
            return {"d": {"Id": self.actor}}
        if parameters["parameters/method"] == "GET":
            assert uri.startswith(self.uri + "?$select=")
            if not self.permissions & 1:
                raise EvaluationError("403")
            if action == "Readback" and self.readback_fault == "connection":
                raise EvaluationError("readback interrupted")
            item = deepcopy(self.item)
            item["EffectiveBasePermissions"] = {"Low": str(self.permissions)}
            if action == "Readback" and self.readback_fault == "data":
                item["SecurityIncident"] = not item["SecurityIncident"]
            return {"d": item}
        assert self.permissions & 4 and uri == self.uri
        assert request["retryPolicy"] == {"type": "none"}
        headers = parameters["parameters/headers"]
        assert headers["X-HTTP-Method"] == "MERGE"
        if self.race:
            self.revise()
        if headers["IF-MATCH"] != self.item["__metadata"]["etag"]:
            self.failed_outputs[action] = {"statusCode": 412}
            raise EvaluationError("412")
        payload = json.loads(parameters["parameters/body"])
        assert payload.pop("__metadata")["type"] == self.item["__metadata"]["type"]
        self.writes.append(payload)
        self.item.update(payload, EditorId=self.actor)
        self.revise()
        return {}


class IncidentWorkflow(Workflow):
    def call(self, name, args):
        if name == "outputs" and args[0] in self.sharepoint.failed_outputs:
            return self.sharepoint.failed_outputs[args[0]]
        return super().call(name, args)


def execute(sp, mode="prepare", snapshot=None, target=""):
    snapshot = snapshot or {}
    engine = IncidentWorkflow({"number": 7, "text": mode, "text_1": snapshot.get("revision", ""),
                               "text_2": snapshot.get("nativeversion", ""), "text_3": target}, sp)
    engine.run(FLOW["definition"]["actions"])
    return engine.outputs["Respond"]


class IncidentTransitionTests(unittest.TestCase):
    def test_operation_and_security_lifecycles(self):
        self.assertEqual(FLOW["connectionReferences"][CONNECTOR]["runtimeSource"], "invoker")
        for kind in (False, True):
            with self.subTest(security=kind):
                sp = SharePoint(security=kind)
                for successor in ("InProgress", "Resolved", "Closed"):
                    snapshot = execute(sp)
                    self.assertEqual((snapshot["status"], snapshot["nextstatus"], snapshot["canadvance"]),
                                     ("ready", successor, True))
                    saved = execute(sp, "advance", snapshot, successor)
                    self.assertEqual((saved["status"], saved["portalstatus"], saved["securityincident"]),
                                     ("saved", successor, kind))
                self.assertFalse(saved["canadvance"])
                self.assertEqual(sp.writes, [{"PortalStatus": "InProgress"},
                    {"PortalStatus": "Resolved", "ResolvedDate": "2026-10-24T22:00:00Z"}, {"PortalStatus": "Closed"}])
                self.assertEqual(sp.item["ResolvedDate"], "2026-10-24T22:00:00Z")

    def test_outside_it_cannot_read_or_write_either_kind(self):
        for kind in (False, True):
            with self.subTest(security=kind):
                sp = SharePoint(security=kind)
                snapshot = execute(sp)
                sp.actor, sp.permissions = 34, 0
                self.assertEqual((execute(sp)["status"], execute(sp, "advance", snapshot, "InProgress")["status"]),
                                 ("unavailable", "unavailable"))
                self.assertFalse(sp.writes)

    def test_reader_bad_transitions_and_missing_context_are_blocked(self):
        for change, target in (({"permissions": 1}, "InProgress"), ({}, "Resolved"),
                               ({"item": {"PortalStatus": ""}}, "InProgress"),
                               ({"item": {"LinkedSystemId": None}}, "InProgress"),
                               ({"item": {"OwnerId": None}}, "InProgress")):
            with self.subTest(change=change, target=target):
                sp = SharePoint()
                sp.item.update(change.get("item", {}))
                sp.permissions = change.get("permissions", 7)
                self.assertEqual(execute(sp, "advance", execute(sp), target)["status"], "blocked")
                self.assertNotIn("Merge_transition", sp.requests)

    def test_exact_revision_and_atomic_conflict(self):
        sp = SharePoint()
        old = execute(sp)
        sp.revise()
        self.assertEqual(execute(sp, "advance", old, "InProgress")["status"], "conflict")
        self.assertNotIn("Merge_transition", sp.requests)
        self.assertEqual(execute(sp, "advance", {**old, "revision": "*"}, "InProgress")["status"], "invalid")
        sp.race = True
        self.assertEqual(execute(sp, "advance", execute(sp), "InProgress")["status"], "conflict")
        self.assertEqual(sp.requests.count("Merge_transition"), 1)
        self.assertFalse(sp.writes)

    def test_write_result_requires_matching_readback(self):
        for fault in ("connection", "data"):
            with self.subTest(fault=fault):
                sp = SharePoint(security=True)
                sp.readback_fault = fault
                self.assertEqual(execute(sp, "advance", execute(sp), "InProgress")["status"], "unverified")
                self.assertEqual(len(sp.writes), 1)


if __name__ == "__main__":
    unittest.main()
