"""Exercise the emitted BCM workflow with role, recovery and conflict fixtures."""
from copy import deepcopy
import json
import re
import unittest
from urllib.parse import unquote
from uuid import UUID

from test_finding_write_flow import FindingWorkflow
from test_review_completion_flow import EvaluationError
from build_business_continuity_write import CONNECTOR, build_flow

SITE = "https://example.sharepoint.com/sites/Portal"
LISTS = {name: str(UUID(int=index))
         for index, name in enumerate(("Processes", "Assets", "Systems", "Evidence"), 1)}
FLOW = build_flow(SITE, "sp_test", *LISTS.values(), "W. Europe Standard Time")["properties"]
OWNERS = {"owner@example.org": 25, "other@example.org": 26}
KEY = "BIA-" + "1" * 32
INPUT = {
    "key": KEY, "title": "Synthetischer Prozess", "owner": "owner@example.org",
    "impact": "Nach vier Stunden fällt der vereinbarte Service aus.",
    "minimumService": "Dringende Vorgänge manuell bearbeiten.",
    "asset": "5", "system": "6", "mtpd": "240", "rto": "90", "rpo": "0",
}
EXERCISE = {"day": "2026-10-24", "result": "Die Priorität wurde in der Tischübung bestätigt.", "evidence": "8"}


class BcmWorkflow(FindingWorkflow):
    def call(self, name, args):
        if name == "isInt":
            return re.fullmatch(r"[+-]?\d+", args[0]) is not None
        if name == "less":
            return args[0] < args[1]
        if name == "split":
            return args[0].split(args[1])
        if name == "last":
            return args[0][-1]
        return super().call(name, args)


class SharePoint:
    def __init__(self):
        self.actor = 25
        self.rights = 7
        self.unique_key = True
        self.rows = {}
        self.sources = {
            "Assets": {"Id": 5, "IsActive": True, "BusinessCritical": True},
            "Systems": {"Id": 6, "IsActive": True},
            "Evidence": {"Id": 8, "IsActive": True, "FileSystemObjectType": 0, "OData__UIVersionString": "2.0"},
        }
        self.failed_outputs = {}
        self.calls = []
        self.writes = []
        self.lost_reply = self.race = self.readback_drift = False

    def http(self, name, request):
        self.calls.append(name)
        params = request["parameters"]
        method, uri = params["parameters/method"], unquote(params["parameters/uri"])
        assert params["dataset"] == SITE
        if name == "Read_actor":
            return {"d": {"Id": self.actor}}
        if name == "Read_owner":
            email = uri.split("membership|", 1)[1][:-1]
            return {"d": {"Id": OWNERS.get(email, 0), "PrincipalType": 1}}
        source, = (source for source, guid in LISTS.items() if f"lists(guid'{guid}')" in uri)
        if source in self.sources:
            row = self.sources[source]
            if not row or f"/items({row['Id']})?" not in uri:
                raise EvaluationError("Unavailable source")
            assert method == "GET"
            return {"d": deepcopy(row)}
        if not self.rights & 1:
            raise EvaluationError("Unreadable list")
        def native_row(ident):
            row = deepcopy(self.rows[ident])
            email = next(email for email, owner in OWNERS.items() if owner == row["OwnerId"])
            row["Owner"] = {"Name": "i:0#.f|membership|" + email, "Title": "Verantwortliche Testperson"}
            row["EffectiveBasePermissions"] = {"Low": str(self.rights)}
            return row
        if name in {"Read_list", "Read_process_list_rights"}:
            return {"d": {"ListItemEntityTypeFullName": "SP.Data.BusinessProcessesListItem",
                          "EffectiveBasePermissions": {"Low": str(self.rights)}}}
        if name == "Read_key":
            assert "'GovernanceID'" in uri
            return {"d": {"Indexed": True, "EnforceUniqueValues": self.unique_key}}
        if name in {"Read_before_create", "Read_after_create"}:
            exact, = re.findall("GovernanceID eq '([^']+)'", uri)
            return {"d": {"results": [native_row(ident) for ident, row in self.rows.items()
                                       if row["GovernanceID"] == exact]}}
        if method == "POST":
            assert request["retryPolicy"] == {"type": "none"}
            data = json.loads(params["parameters/body"])
            meta = data.pop("__metadata")
            assert meta["type"] == "SP.Data.BusinessProcessesListItem"
            if name == "Create_process":
                assert self.rights & 2 and self.unique_key
                assert all(row["GovernanceID"] != data["GovernanceID"] for row in self.rows.values())
                ident = len(self.rows) + 1
                row = {**data, "Id": ident, "AuthorId": self.actor, "EditorId": self.actor,
                       "OData__UIVersionString": "1.0", "__metadata": {**meta, "etag": '"1"'}}
                self.rows[ident] = row
            else:
                assert name == "Merge_process" and self.rights & 4
                row = self.rows[int(uri.split("/items(", 1)[1].split(")", 1)[0])]
                headers = params["parameters/headers"]
                assert headers["X-HTTP-Method"] == "MERGE"
                if self.race or headers["IF-MATCH"] != row["__metadata"]["etag"]:
                    self.failed_outputs[name] = {"statusCode": 412}
                    raise EvaluationError("412")
                version = int(row["OData__UIVersionString"].split(".")[0]) + 1
                row.update(data, EditorId=self.actor, OData__UIVersionString=f"{version}.0")
                row["__metadata"]["etag"] = f'"{version}"'
            self.writes.append(name)
            if name == "Create_process" and self.lost_reply:
                raise EvaluationError("Lost reply after committed create")
            return {}
        row = native_row(int(uri.split("/items(", 1)[1].split(")", 1)[0]))
        if name == "Read_after_edit" and self.readback_drift:
            row["BiaRpoMinutes"] = 42
        return {"d": row}

    def run(self, action, args=None, revision=None):
        latest = self.rows.get(1, {}).get("__metadata", {}).get("etag", "-")
        payload = INPUT if args is None else args
        workflow = BcmWorkflow({"text": action, "number": 0 if action in {"create", "capabilities"} else 1,
                               "text_1": revision if revision is not None else latest,
                               "text_2": json.dumps(payload)}, self)
        workflow.run(FLOW["definition"]["actions"])
        return workflow.outputs["Respond"]


class BusinessContinuityTests(unittest.TestCase):
    def test_draft_assess_and_record_exercise(self):
        sp = SharePoint()
        self.assertEqual(sp.run("create")["status"], "saved")
        self.assertEqual(sp.rows[1]["BiaStatus"], "Entwurf")
        prepared = sp.run("prepare", {})
        snap = json.loads(prepared["snapshot"])
        self.assertEqual((prepared["revision"], snap["BiaRpoMinutes"], snap["owner"]), ('"1"', 0, "owner@example.org"))
        self.assertEqual(sp.run("exercise", EXERCISE)["status"], "exercise_not_allowed")
        self.assertEqual(sp.run("assess")["status"], "saved")
        self.assertEqual((sp.rows[1]["BiaStatus"], sp.rows[1]["BiaAssessedById"]), ("Bewertet", 25))
        self.assertEqual(sp.run("exercise", EXERCISE)["status"], "saved")
        row = sp.rows[1]
        self.assertEqual((row["BcmExerciseDate"], row["BcmEvidenceItemID"], row["BcmEvidenceVersion"]),
                         ("2026-10-23T22:00:00Z", 8, "2.0"))
        self.assertEqual(row["BiaRpoMinutes"], 0)
        self.assertEqual(sp.run("save", {**INPUT, "rto": "100"})["status"], "saved")
        self.assertIsNone(row["BiaAssessedAt"])
        self.assertIsNone(row["BiaAssessedById"])
        self.assertEqual((row["BiaStatus"], row["BcmEvidenceVersion"]), ("Entwurf", "2.0"))

    def test_missing_and_invalid_recovery_values_do_not_write(self):
        sp = SharePoint()
        for override in ({"rto": "240"}, {"rto": "245"}, {"rto": "0"}, {"rpo": "-1"},
                         {"rto": "1.5"}, {"mtpd": "2147483648"}):
            self.assertEqual(sp.run("create", {**INPUT, **override})["status"], "invalid")
        self.assertFalse(sp.writes)
        minimal = {key: INPUT[key] for key in ("key", "title", "owner")}
        self.assertEqual(sp.run("create", minimal)["status"], "saved")
        self.assertIsNone(sp.rows[1]["BiaRpoMinutes"])
        self.assertEqual(sp.run("assess", {**INPUT, "rpo": ""})["status"], "invalid")
        self.assertEqual(sp.run("assess", {**INPUT, "impact": ""})["status"], "invalid")
        self.assertEqual(sp.run("assess", {**INPUT, "system": ""})["status"], "invalid")
        self.assertEqual(sp.writes, ["Create_process"])

    def test_reader_and_foreign_assessor_are_blocked(self):
        sp = SharePoint()
        self.assertEqual(sp.run("create")["status"], "saved")
        self.assertTrue(sp.run("capabilities", {})["cancreate"])
        self.assertTrue(sp.run("capabilities", {})["canedit"])
        sp.rights = 1
        reader = sp.run("capabilities", {})
        self.assertEqual((reader["status"], reader["cancreate"], reader["canedit"]), ("capabilities", False, False))
        self.assertFalse(sp.run("prepare", {})["canedit"])
        for action in ("create", "save", "assess", "exercise"):
            self.assertEqual(sp.run(action, EXERCISE if action == "exercise" else INPUT)["status"], "denied")
        sp.rights, sp.actor = 7, 26
        self.assertEqual(sp.run("assess")["status"], "assessment_denied")
        self.assertEqual(sp.run("assess", {**INPUT, "owner": "other@example.org"})["status"], "assessment_denied")
        self.assertEqual(sp.writes, ["Create_process"])

    def test_dependency_and_exercise_checks(self):
        sp = SharePoint()
        sp.sources["Assets"]["BusinessCritical"] = False
        self.assertEqual(sp.run("create")["status"], "source_unavailable")
        sp.sources["Assets"]["BusinessCritical"] = True
        sp.sources["Systems"]["IsActive"] = False
        self.assertEqual(sp.run("create")["status"], "source_unavailable")
        sp.sources["Systems"]["IsActive"] = True
        sp.run("create")
        sp.run("assess")
        for day in ("2026-11-01", "2026-02-31"):
            self.assertEqual(sp.run("exercise", {**EXERCISE, "day": day})["status"], "invalid_exercise_date")
        for field, value in (("IsActive", False), ("FileSystemObjectType", 1), ("OData__UIVersionString", "")):
            old = sp.sources["Evidence"][field]
            sp.sources["Evidence"][field] = value
            self.assertEqual(sp.run("exercise", EXERCISE)["status"], "source_unavailable")
            sp.sources["Evidence"][field] = old
        self.assertEqual(sp.writes, ["Create_process", "Merge_process"])

    def test_exact_create_recovery_and_conflict(self):
        sp = SharePoint()
        sp.unique_key = False
        self.assertEqual(sp.run("create")["status"], "request_key_unavailable")
        sp.unique_key, sp.lost_reply = True, True
        self.assertEqual(sp.run("create")["status"], "saved")
        self.assertEqual(sp.run("create")["status"], "saved")
        self.assertEqual(sp.run("create", {**INPUT, "title": "Differenter Alias"})["status"], "request_conflict")
        self.assertEqual(sp.writes, ["Create_process"])

    def test_stale_and_racing_revisions_and_uncertain_readback(self):
        sp = SharePoint()
        sp.run("create")
        self.assertEqual(sp.run("save", revision='"0"')["status"], "conflict")
        self.assertEqual(sp.run("save", revision="*")["status"], "invalid")
        sp.race = True
        self.assertEqual(sp.run("save")["status"], "conflict")
        sp.race, sp.readback_drift = False, True
        self.assertEqual(sp.run("save")["status"], "uncertain")
        self.assertEqual(sp.writes, ["Create_process", "Merge_process"])

    def test_invoker_and_platform_action_depth(self):
        def depth(actions):
            return max((1 + max(depth(row.get("actions", {})), depth(row.get("else", {}).get("actions", {})))
                        for row in actions.values()), default=0)
        self.assertEqual(FLOW["connectionReferences"][CONNECTOR]["runtimeSource"], "invoker")
        self.assertLessEqual(depth(FLOW["definition"]["actions"]), 8)


if __name__ == "__main__":
    unittest.main()
