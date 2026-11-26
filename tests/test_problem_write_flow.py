"""Exercise the emitted workflow with synthetic versioned SharePoint records."""

from copy import deepcopy
import json
import unittest
from uuid import UUID

from test_control_write_flow import ControlWorkflow
from test_review_completion_flow import EvaluationError
from build_problem_write import CONNECTOR, NOTES, build_flow

SITE = "https://example.sharepoint.com/sites/Portal"
LISTS = {name: str(UUID(int=index)) for index, name in enumerate(("Problems", "Incidents", "Changes"), 1)}
FLOW = build_flow(SITE, "sp_test", *LISTS.values())["properties"]
ANALYSIS = {"RootCause": 'Zeile 1\n"Zeile 2" Ä', "Workaround": "  Puffer verwenden  ", "KnownError": "synthetisch"}


class ProblemWorkflow(ControlWorkflow):
    def call(self, name, args):
        if name == "trim":
            return args[0].strip()
        if name == "union":
            return list(dict.fromkeys(value for values in args for value in values))
        if name == "setProperty":
            obj, key, value = args
            return {**obj, key: value}
        return super().call(name, args)


class SharePoint:
    def __init__(self):
        self.row = {"Id": 7, "Title": "Synthetic problem", "IsActive": True,
                    **dict.fromkeys(NOTES),
                    "RelatedIncidentsId": {"results": [2]}, "ResolvingChangesId": {"results": []},
                    "EditorId": 13, "OData__UIVersionString": "1.0",
                    "__metadata": {"type": "SP.Data.ProblemsListItem", "etag": '"1"'}}
        self.sources = {"Incidents": {3: True, 4: False, 5: True}, "Changes": {3: True}}
        self.denied = set()
        self.permissions = 7
        self.calls = []
        self.writes = []
        self.failed_outputs = {}
        self.race = False
        self.readback_drift = False

    def http(self, action, request):
        self.calls.append(action)
        args = request["parameters"]
        assert args["dataset"] == SITE
        method, uri, headers = (args[f"parameters/{key}"] for key in ("method", "uri", "headers"))
        if action == "Read_actor":
            assert method == "GET" and uri == "_api/web/currentuser?$select=Id"
            return {"d": {"Id": 25}}
        list_name, = (name for name, guid in LISTS.items() if f"lists(guid'{guid}')" in uri)
        if list_name in self.denied:
            raise EvaluationError("access denied")
        if action == "Read_link_source":
            source_id = int(uri.split("/items(")[1].split(")")[0])
            assert method == "GET" and uri.endswith("?$select=Id,IsActive") and list_name != "Problems"
            if source_id not in self.sources[list_name]:
                raise EvaluationError("source not found")
            return {"d": {"Id": source_id, "IsActive": self.sources[list_name][source_id]}}
        assert list_name == "Problems" and "/items(7)" in uri
        if method == "POST":
            assert action == "Write_problem" and request["retryPolicy"] == {"type": "none"}
            assert headers["X-HTTP-Method"] == "MERGE" and self.permissions & 4
            if self.race or headers["IF-MATCH"] != self.row["__metadata"]["etag"]:
                self.failed_outputs[action] = {"statusCode": 412}
                raise EvaluationError("revision changed")
            payload = json.loads(args["parameters/body"])
            self.writes.append(payload)
            assert payload.pop("__metadata") == {"type": self.row["__metadata"]["type"]}
            version = int(self.row["OData__UIVersionString"].split(".")[0]) + 1
            self.row["__metadata"]["etag"] = f'"{version}"'
            self.row.update(payload, EditorId=25, OData__UIVersionString=f"{version}.0")
            return {}
        assert method == "GET" and action in {"Read_problem", "Read_back"}
        row = {**deepcopy(self.row), "EffectiveBasePermissions": {"Low": str(self.permissions)}}
        if action == "Read_back" and self.readback_drift:
            row["Workaround"] = "unexpected readback"
        return {"d": row}

    def run(self, action="prepare", source=0, notes=None, revision=None):
        if notes is None:
            notes = {key: self.row[key] or "" for key in NOTES} if action == "prepare" else {}
        request = {"number": 7, "text": action, "text_1": self.row["__metadata"]["etag"] if revision is None else revision,
                   "number_1": source, "text_2": json.dumps(notes)}
        workflow = ProblemWorkflow(request, self)
        workflow.run(FLOW["definition"]["actions"])
        return workflow.outputs["Respond"]


class ProblemTests(unittest.TestCase):
    def test_analysis_uses_confirmed_revision_and_preserves_links(self):
        sp = SharePoint()
        self.assertTrue(sp.run()["canedit"])
        self.assertFalse(sp.run(notes=ANALYSIS)["canedit"])
        self.assertEqual(sp.run("analysis", notes=ANALYSIS)["status"], "saved")
        self.assertEqual({key: sp.row[key] for key in NOTES}, {key: value.strip() for key, value in ANALYSIS.items()})
        self.assertEqual(sp.row["RelatedIncidentsId"]["results"], [2])
        self.assertEqual(sp.run("analysis", notes=ANALYSIS)["status"], "unchanged")
        self.assertEqual(sp.run("analysis", notes={**ANALYSIS, "Workaround": ""})["status"], "saved")
        self.assertEqual(sp.row["Workaround"], "")
        self.assertEqual(sp.run("analysis", notes={"RootCause": "partial"})["status"], "invalid")
        self.assertEqual(sp.run("analysis", notes={**ANALYSIS, "Workaround": "x" * 4001})["status"], "invalid")
        self.assertEqual(len(sp.writes), 2)

    def test_links_are_typed_additive_and_idempotent(self):
        sp = SharePoint()
        for mode, source in (("incident", 3), ("change", 3), ("incident", 5)):
            self.assertEqual(sp.run(mode, source)["status"], "saved")
            self.assertEqual(sp.run(mode, source)["status"], "unchanged")
        self.assertEqual(sp.row["RelatedIncidentsId"]["results"], [2, 3, 5])
        self.assertEqual(sp.row["ResolvingChangesId"]["results"], [3])
        self.assertEqual([set(payload) for payload in sp.writes],
                         [{"RelatedIncidentsId"}, {"ResolvingChangesId"}, {"RelatedIncidentsId"}])

    def test_invoker_must_access_problem_and_active_source(self):
        sp = SharePoint()
        sp.denied.add("Problems")
        self.assertEqual(sp.run(), {"status": "unavailable", "itemid": 0, "revision": "", "canedit": False})
        sp.denied.clear()
        sp.permissions = 1
        self.assertFalse(sp.run()["canedit"])
        self.assertEqual(sp.run("incident", 3)["status"], "blocked")
        sp.permissions = 7
        sp.denied.add("Incidents")
        self.assertEqual(sp.run("incident", 3)["status"], "source_unavailable")
        sp.denied.clear()
        self.assertEqual(sp.run("incident", 4)["status"], "source_unavailable")
        self.assertEqual(sp.run("change", 99)["status"], "source_unavailable")
        self.assertFalse(sp.writes)

    def test_conflict_and_unconfirmed_write_are_not_retried(self):
        sp = SharePoint()
        self.assertEqual(sp.run("incident", 3, revision='"0"')["status"], "conflict")
        self.assertNotIn("Write_problem", sp.calls)
        sp.race = True
        self.assertEqual(sp.run("incident", 3)["status"], "conflict")
        self.assertEqual(sp.calls.count("Write_problem"), 1)
        sp.race = False
        sp.readback_drift = True
        self.assertEqual(sp.run("analysis", notes=ANALYSIS)["status"], "unverified")
        self.assertEqual(sp.calls.count("Write_problem"), 2)

    def test_invoker_secure_payload_and_workflow_limits(self):
        def walk(actions, level=1):
            for name, action in actions.items():
                yield name, action, level
                yield from walk(action.get("actions", {}), level + 1)
                yield from walk(action.get("else", {}).get("actions", {}), level + 1)

        self.assertEqual(FLOW["connectionReferences"][CONNECTOR]["runtimeSource"], "invoker")
        actions = {name: (action, level) for name, action, level in walk(FLOW["definition"]["actions"])}
        self.assertLessEqual(max(level for _, level in actions.values()), 8)
        self.assertEqual(set(actions["Respond"][0]["inputs"]["body"]), {"status", "itemid", "revision", "canedit"})
        for name in ("Read_problem", "Write_problem", "Read_back"):
            self.assertEqual(actions[name][0]["runtimeConfiguration"]["secureData"]["properties"], ["inputs", "outputs"])
        self.assertEqual(FLOW["definition"]["triggers"]["manual"]["runtimeConfiguration"]["secureData"]["properties"], ["outputs"])


if __name__ == "__main__":
    unittest.main()
