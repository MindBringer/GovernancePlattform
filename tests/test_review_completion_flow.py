"""Run the emitted review workflow against deterministic SharePoint failure scenarios."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import unquote
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "powerplatform/flows"))
from build_review_completion import build_flow  # noqa: E402

SITE = "https://example.sharepoint.com/sites/Portal"
REVIEWER = "i:0#.f|membership|reviewer@example.org"
LISTS = {kind: f"00000000-0000-0000-0000-00000000000{number}"
         for number, kind in enumerate(("Asset", "Change", "Risk"), 1)}
REVIEWS = "00000000-0000-0000-0000-000000000004"
MODEL = build_flow(SITE, "sp_test", LISTS, REVIEWS, [REVIEWER], "W. Europe Standard Time")
DEFINITION = MODEL["properties"]["definition"]
TOKEN = re.compile(r"\s*('(?:''|[^'])*'|[A-Za-z_$][\w$]*|[0-9]+|[?()[\],])")
ZONES = {"UTC": timezone.utc, "W. Europe Standard Time": ZoneInfo("Europe/Berlin")}
FORMATS = {"yyyy-MM-dd": "%Y-%m-%d", "yyyy-MM-ddTHH:mm:ssZ": "%Y-%m-%dT%H:%M:%SZ"}


def iso(value, assumed=timezone.utc):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=assumed)


class EvaluationError(Exception):
    pass


class Workflow:
    """Interpret only the documented WDL subset emitted by this builder."""

    def __init__(self, body, sharepoint):
        self.body, self.sharepoint = body, sharepoint
        self.variables, self.outputs, self.states = {}, {}, {}

    def evaluate(self, value):
        if isinstance(value, dict):
            return {k: self.evaluate(v) for k, v in value.items()}
        if not isinstance(value, str) or not value.startswith("@"):
            return value
        tokens = TOKEN.findall(value[1:])
        unrecognized = TOKEN.sub("", value[1:]).strip()
        assert not unrecognized, (value, unrecognized)
        cursor = 0

        def take(wanted=None):
            nonlocal cursor
            token = tokens[cursor]
            if wanted is not None:
                assert token == wanted, (wanted, token, value)
            cursor += 1
            return token

        def read():
            token = take()
            if token.startswith("'"):
                result = token[1:-1].replace("''", "'")
            elif token.isdecimal():
                result = int(token)
            elif token in ("true", "false"):
                result = token == "true"
            else:
                take("(")
                args = []
                if tokens[cursor] != ")":
                    args.append(read())
                    while tokens[cursor] == ",":
                        take(",")
                        args.append(read())
                take(")")
                result = self.call(token, args)
            while cursor < len(tokens) and tokens[cursor] == "?":
                take("?")
                take("[")
                key = read()
                take("]")
                result = result.get(key) if isinstance(result, dict) else None
            return result

        evaluated = read()
        assert cursor == len(tokens), value
        return evaluated

    def call(self, name, args):
        from urllib.parse import quote
        functions = {
            "and": lambda *items: all(items), "or": lambda *items: any(items), "not": lambda x: not x,
            "equals": lambda a, b: a == b, "greater": lambda a, b: a > b,
            "greaterOrEquals": lambda a, b: a >= b, "lessOrEquals": lambda a, b: a <= b,
            "contains": lambda seq, item: item in seq, "int": int, "length": len, "empty": lambda x: not x,
            "coalesce": lambda *items: next((x for x in items if x is not None), None),
            "createArray": lambda *items: list(items), "if": lambda test, yes, no: yes if test else no,
            "json": json.loads, "string": lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else str(v),
            "concat": lambda *items: "".join(items), "toLower": str.lower, "first": lambda x: x[0],
            "div": lambda a, b: a // b, "mod": lambda a, b: a % b,
            "triggerBody": lambda: self.body, "body": self.outputs.get, "outputs": self.outputs.get,
            "variables": self.variables.get, "parameters": lambda _: {},
            "utcNow": lambda: "2026-10-25T00:30:00Z",
            "formatDateTime": lambda dt, form: iso(dt).strftime(FORMATS[form]),
            "convertTimeZone": lambda dt, src, dst, form: iso(dt, ZONES[src]).astimezone(ZONES[dst]).strftime(FORMATS[form]),
            "addDays": lambda dt, days: (iso(dt) + timedelta(days=days)).isoformat(),
            "ticks": lambda dt: iso(dt).timestamp(), "uriComponent": lambda s: quote(s, safe=""),
        }
        assert name in functions, name
        return functions[name](*args)

    def run(self, actions):
        failed = False
        for name, action in actions.items():
            dependencies = action["runAfter"]
            assert all(key in self.states for key in dependencies), (name, dependencies)
            if any(self.states[key] not in states for key, states in dependencies.items()):
                self.states[name] = "Skipped"
                continue
            try:
                kind = action["type"]
                if kind == "If":
                    branch = action["actions"] if self.evaluate(action["expression"]) else action["else"]["actions"]
                    if self.run(branch):
                        raise EvaluationError()
                else:
                    inputs = self.evaluate(action["inputs"])
                    if kind == "Compose":
                        self.outputs[name] = inputs
                    elif kind == "OpenApiConnection":
                        self.outputs[name] = self.sharepoint.http(name, inputs)
                    elif kind == "InitializeVariable":
                        self.variables.update({v["name"]: v["value"] for v in inputs["variables"]})
                    elif kind == "SetVariable":
                        self.variables[inputs["name"]] = inputs["value"]
                    elif kind == "Response":
                        self.outputs[name] = inputs["body"]
                    else:
                        raise AssertionError(kind)
                self.states[name] = "Succeeded"
            except (EvaluationError, ValueError, TypeError):
                self.states[name] = "Failed"
                failed = True
        return failed


class SharePoint:
    def __init__(self, kind="Asset"):
        self.kind = kind
        self.target = {"Id": 7, "Title": "Synthetisches Objekt", "GovernanceID": "OBJ-7", "IsActive": True,
                       "NextReviewDate": "2026-10-23T22:00:00Z", "LastReviewDate": None,
                       "EffectiveBasePermissions": {"Low": "7"},
                       "__metadata": {"etag": '"8"', "type": "SP.Data.ObjectsListItem"}}
        self.reviews = {}
        self.user = {"Id": 19, "LoginName": REVIEWER.upper()}
        self.list_permissions = "7"
        self.unique = True
        self.failed_before = set()
        self.failed_after = set()
        self.revise_before_schedule_write = False
        self.requests = []
        self.writes = []

    def http(self, action, inputs):
        p = inputs["parameters"]
        assert p["dataset"] == SITE
        uri = unquote(p["parameters/uri"])
        post = p["parameters/method"] == "POST"
        self.requests.append(action)
        if action in self.failed_before:
            self.failed_before.remove(action)
            raise EvaluationError(action)
        if uri.startswith("_api/web/currentuser?"):
            row = self.user
        elif LISTS[self.kind] in uri:
            assert "/items(7)" in uri, uri
            row = self.target
        elif REVIEWS in uri:
            if "/fields/" in uri:
                row = {"EnforceUniqueValues": self.unique, "Indexed": self.unique}
            elif "$filter=GovernanceID eq " in uri:
                key, = re.findall("GovernanceID eq '([^']+)'", uri)
                row = {"results": [self.reviews[key]] if key in self.reviews else []}
            elif "/items(" in uri:
                item_id = int(uri.split("/items(")[1].split(")")[0])
                row, = [r for r in self.reviews.values() if r["Id"] == item_id]
            elif not post:
                row = {"EffectiveBasePermissions": {"Low": self.list_permissions},
                       "ListItemEntityTypeFullName": "SP.Data.ReviewsListItem"}
            else:
                row = None
        else:
            raise AssertionError(uri)
        if post:
            assert inputs["retryPolicy"] == {"type": "none"}
            payload = json.loads(p["parameters/body"])
            if action == "Create_receipt":
                key = payload["GovernanceID"]
                if key in self.reviews:
                    raise EvaluationError("unique key")
                assert payload["ReviewerId"] == self.user["Id"]
                row = self.reviews[key] = {**payload, "Id": 40, "AuthorId": self.user["Id"],
                                           "__metadata": {**payload["__metadata"], "etag": '"1"'}}
            else:
                headers = p["parameters/headers"]
                assert headers["X-HTTP-Method"] == "MERGE"
                if action == "Update_schedule" and self.revise_before_schedule_write:
                    row["__metadata"]["etag"] = '"99"'
                    self.revise_before_schedule_write = False
                if headers["IF-MATCH"] != row["__metadata"]["etag"]:
                    raise EvaluationError("412")
                row.update({k: v for k, v in payload.items() if k != "__metadata"})
                stamp = int(row["__metadata"]["etag"].strip('"'))
                row["__metadata"]["etag"] = f'"{stamp + 1}"'
            self.writes.append((action, payload))
        if action in self.failed_after:
            self.failed_after.remove(action)
            raise EvaluationError("lost response")
        return {"d": deepcopy(row)}

    def submit(self, mode, *, due="2026-10-24", etag='"8"', outcome="Updated", next_due="2026-11-01"):
        if mode == "prepare":
            due = etag = outcome = next_due = "-"
        body = {"number": 7, "text": self.kind, "text_1": mode, "text_2": due, "text_3": etag,
                "text_4": outcome, "text_5": next_due}
        run = Workflow(body, self)
        run.run(DEFINITION["actions"])
        return run.outputs["Respond"]


class ReviewWorkflowTests(unittest.TestCase):
    def test_prepare_and_all_target_types_preserve_pilot_permissions(self):
        self.assertEqual(MODEL["properties"]["connectionReferences"]["shared_sharepointonline"]["runtimeSource"], "invoker")
        for kind, label in zip(LISTS, ("Asset", "Change", "Risiko")):
            with self.subTest(kind=kind):
                sp = SharePoint(kind)
                ready = sp.submit("prepare")
                self.assertEqual((ready["status"], ready["revision"], ready["due"]), ("ready", '"8"', "2026-10-24"))
                self.assertEqual(sp.writes, [])
                saved = sp.submit("save")
                self.assertEqual((saved["status"], saved["targetid"], saved["targettype"], saved["reviewid"]), ("saved", 7, kind, 40))
                record, = sp.reviews.values()
                self.assertEqual(record["ReviewedObjectType"], label)
                self.assertEqual(record["ManualReviewState"], "Abgeschlossen")
                self.assertEqual(sp.target["LastReviewDate"], "2026-10-24T22:00:00Z")
                self.assertEqual(sp.target["NextReviewDate"], "2026-10-31T23:00:00Z")
                self.assertEqual(set(sp.writes[1][1]), {"__metadata", "LastReviewDate", "NextReviewDate"})
                self.assertEqual(sp.submit("save"), saved)
                self.assertEqual(len(sp.writes), 3)

    def test_no_writes_with_invalid_request_or_insufficient_permission(self):
        for case in ("reader", "other_editor", "review_list", "shared_key", "stale_parent", "too_early", "invalid_date", "same_day"):
            with self.subTest(case=case):
                sp = SharePoint()
                args = {}
                if case == "reader":
                    sp.target["EffectiveBasePermissions"]["Low"] = "1"
                elif case == "other_editor":
                    sp.user["LoginName"] = "i:0#.f|membership|other@example.org"
                elif case == "review_list":
                    sp.list_permissions = "3"
                elif case == "shared_key":
                    sp.unique = False
                elif case == "stale_parent":
                    sp.target["__metadata"]["etag"] = '"9"'
                elif case == "too_early":
                    sp.target["NextReviewDate"] = "2027-04-10T00:00:00Z"
                elif case == "invalid_date":
                    args["next_due"] = "2026-02-31"
                else:
                    args["next_due"] = "2026-10-25"
                self.assertNotEqual(sp.submit("save", **args)["status"], "saved")
                self.assertEqual(sp.writes, [])

    def test_lost_create_response_is_read_back_before_advancing(self):
        sp = SharePoint()
        sp.failed_after.add("Create_receipt")
        self.assertEqual(sp.submit("save")["status"], "saved")
        self.assertEqual([name for name, _ in sp.writes], ["Create_receipt", "Update_schedule", "Mark_completed"])

    def test_failed_schedule_can_resume_frozen_decision_with_only_one_history_item(self):
        sp = SharePoint()
        sp.failed_before.add("Update_schedule")
        self.assertEqual(sp.submit("save")["status"], "pending")
        self.assertEqual(len(sp.reviews), 1)
        self.assertEqual(sp.submit("save", outcome="Retire")["status"], "conflict")
        resumed = sp.submit("resume", etag="-", outcome="-", next_due="-")
        self.assertEqual((resumed["status"], resumed["reviewid"], resumed["nextdue"]), ("saved", 40, "2026-11-01"))
        self.assertEqual([name for name, _ in sp.writes], ["Create_receipt", "Update_schedule", "Mark_completed"])

    def test_reconcile_written_schedule_without_rewriting_it(self):
        for lost in ("Update_schedule", "Mark_completed"):
            with self.subTest(action=lost):
                sp = SharePoint()
                sp.failed_after.add(lost)
                self.assertEqual(sp.submit("save")["status"], "saved")
                self.assertEqual([name for name, _ in sp.writes], ["Create_receipt", "Update_schedule", "Mark_completed"])
        sp = SharePoint()
        sp.failed_before.add("Mark_completed")
        self.assertEqual(sp.submit("save")["status"], "pending")
        self.assertEqual(sp.submit("resume")["status"], "saved")
        self.assertEqual([name for name, _ in sp.writes], ["Create_receipt", "Update_schedule", "Mark_completed"])

    def test_another_editor_revision_is_not_overwritten(self):
        sp = SharePoint()
        sp.failed_before.add("Update_schedule")
        self.assertEqual(sp.submit("save")["status"], "pending")
        sp.target["__metadata"]["etag"] = '"9"'
        self.assertEqual(sp.submit("resume")["status"], "conflict")
        self.assertEqual([name for name, _ in sp.writes], ["Create_receipt"])

    def test_sharepoint_412_cannot_advance_the_schedule(self):
        sp = SharePoint()
        sp.revise_before_schedule_write = True
        result = sp.submit("save")
        self.assertEqual((result["status"], result["reviewid"]), ("conflict", 40))
        self.assertIsNone(sp.target["LastReviewDate"])
        self.assertEqual([name for name, _ in sp.writes], ["Create_receipt"])

    def test_added_review_fields_preserve_existing_records(self):
        fields = json.loads((ROOT / "architecture/object-fields.yaml").read_text())["objectFields"]
        fields = {row["internalName"]: row for row in fields if row["objectTypeKey"] == "Review"}
        expected = {"ManualReviewState": "Choice", "ReviewPreviousDueDate": "DateTime",
                    "ReviewTargetETag": "Text"}
        for field, kind in expected.items():
            self.assertEqual(fields[field]["type"], kind)
            self.assertFalse(fields[field]["required"])
        self.assertEqual(fields["ManualReviewState"]["choiceSet"], "ManualReviewState")
        base = json.loads((ROOT / "architecture/fields.yaml").read_text())["fields"]
        self.assertTrue(next(row["unique"] for row in base if row["internalName"] == "GovernanceID"))

    def test_intent_must_belong_to_native_creator(self):
        sp = SharePoint()
        sp.failed_before.add("Update_schedule")
        self.assertEqual(sp.submit("save")["status"], "pending")
        record, = sp.reviews.values()
        record["AuthorId"] = 23
        self.assertEqual(sp.submit("resume")["status"], "conflict")
        self.assertEqual(len(sp.writes), 1)


if __name__ == "__main__":
    unittest.main()
