"""Exercise the generated document flow and its SharePoint concurrency checks."""

from copy import deepcopy
import json
import unittest

from test_review_completion_flow import EvaluationError, Workflow
from build_document_approval import KINDS, build_flow


SITE = "https://example.sharepoint.com/sites/Portal"
EDITOR = "i:0#.f|membership|editor@example.org"
APPROVER = "i:0#.f|membership|approver@example.org"
READER = "i:0#.f|membership|reader@example.org"
LIBRARIES = {kind: f"00000000-0000-0000-0000-00000000000{number}"
             for number, kind in enumerate(KINDS, 1)}
FLOW = build_flow(SITE, "sp_test", LIBRARIES, [EDITOR], [APPROVER], "W. Europe Standard Time")
ACTIONS = FLOW["properties"]["definition"]["actions"]


class SharePoint:
    def __init__(self, kind="Policy"):
        self.url = f"_api/web/lists(guid'{LIBRARIES[kind]}')/items(7)"
        self.item = {
            "Id": 7, "Title": "", "FileLeafRef": "synthetic.txt", "FileSystemObjectType": 0,
            "DocumentStatus": None, "DocumentOwnerId": None, "DocumentReviewDate": None,
            "OData__UIVersionString": "1.0", "__metadata": {"etag": '"8"', "type": "SP.Data.DocumentItem"},
        }
        self.roles = {EDITOR: (15, "7", "Editor"), APPROVER: (16, "7", "Approver"), READER: (17, "1", "Reader")}
        self.login = EDITOR
        self.race = False
        self.failed_readback = False
        self.invalid_readback = False
        self.requests, self.writes, self.failed_outputs = [], [], {}

    def http(self, action, request):
        params = request["parameters"]
        uri = params["parameters/uri"]
        self.requests.append((action, uri))
        assert params["dataset"] == SITE
        actor, permissions, name = self.roles[self.login]
        if action == "Current_user":
            assert uri == "_api/web/currentuser?$select=Id,LoginName"
            return {"d": {"Id": actor, "LoginName": self.login.upper()}}
        assert uri.startswith(self.url), uri
        if params["parameters/method"] == "GET":
            assert uri == self.url or uri.startswith(self.url + "?$select=")
            if action.endswith("_readback") and self.failed_readback:
                raise EvaluationError(action)
            document = deepcopy(self.item)
            document["EffectiveBasePermissions"] = {"Low": permissions}
            for field in ("DocumentOwner", "ApprovedBy"):
                document[field] = next(({"Title": role[2]} for role in self.roles.values()
                                        if role[0] == document.get(field + "Id")), None)
            if action.endswith("_readback") and self.invalid_readback:
                document["DocumentStatus"] = "Unbekannt"
            return {"d": document}
        assert request["retryPolicy"] == {"type": "none"}
        headers = params["parameters/headers"]
        assert headers["X-HTTP-Method"] == "MERGE"
        if self.race:
            self.revise()
        if headers["IF-MATCH"] != self.item["__metadata"]["etag"]:
            self.failed_outputs[action] = {"statusCode": 412}
            raise EvaluationError(action)
        assert permissions == "7"
        payload = json.loads(params["parameters/body"])
        assert payload.pop("__metadata") == {"type": self.item["__metadata"]["type"]}
        self.writes.append((actor, payload))
        self.item.update(payload, EditorId=actor)
        self.revise()
        return {}

    def revise(self):
        self.item["__metadata"]["etag"] = f'"{int(self.item["__metadata"]["etag"][1:-1]) + 1}"'
        self.item["OData__UIVersionString"] = f"{int(self.item['OData__UIVersionString'].split('.')[0]) + 1}.0"


class DocumentWorkflow(Workflow):
    def call(self, name, args):
        if name == "trim":
            return args[0].strip()
        if name == "outputs" and args[0] in self.sharepoint.failed_outputs:
            return self.sharepoint.failed_outputs[args[0]]
        return super().call(name, args)


def execute(sp, mode="prepare", *, snapshot=None, title="-", due="-", kind="Policy", item_id=7):
    snapshot = snapshot or {}
    engine = DocumentWorkflow({
        "number": item_id, "text": kind, "text_1": mode, "text_2": snapshot.get("revision", "-"),
        "text_3": snapshot.get("nativeversion", "-"), "text_4": title, "text_5": due,
    }, sp)
    engine.run(ACTIONS)
    return engine.outputs["Respond"]


class DocumentApprovalTests(unittest.TestCase):
    def test_successful_lifecycle_for_each_library(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                sp = SharePoint(kind)
                prepared = execute(sp, kind=kind)
                self.assertEqual((prepared["status"], prepared["documentstatus"]), ("ready", "Entwurf"))
                self.assertTrue(prepared["canedit"])
                self.assertFalse(prepared["cansubmit"])
                saved = execute(sp, "save", snapshot=prepared, title="  Dokument  ", due="2026-10-25", kind=kind)
                self.assertEqual((saved["status"], saved["title"], saved["reviewdate"]),
                                 ("saved", "Dokument", "2026-10-25"))
                self.assertEqual(sp.item["DocumentReviewDate"], "2026-10-24T22:00:00Z")
                self.assertEqual(saved["owner"], "Editor")
                submitted = execute(sp, "submit", snapshot=saved, kind=kind)
                self.assertEqual(submitted["documentstatus"], "In Prüfung")
                self.assertFalse(submitted["canapprove"])
                sp.login = APPROVER
                approved = execute(sp, "approve", snapshot=execute(sp, kind=kind), kind=kind)
                self.assertEqual((approved["status"], approved["documentstatus"]), ("saved", "Veröffentlicht"))
                self.assertEqual((approved["approvedby"], approved["approveddate"], approved["approvedversion"]),
                                 ("Approver", "2026-10-25", submitted["nativeversion"]))
                self.assertNotEqual(approved["approvedversion"], approved["nativeversion"])
                self.assertEqual(len(sp.writes), 3)
                sp.login = READER
                readonly = execute(sp, kind=kind)
                self.assertEqual(readonly["approvedversion"], submitted["nativeversion"])
                self.assertFalse(any(readonly[r] for r in ("canedit", "cansubmit", "canapprove", "canreturn")))

    def test_return_uses_native_audit_without_creating_approval(self):
        sp = SharePoint()
        sp.item.update(DocumentStatus="In Prüfung", Title="Dokument",
                       DocumentOwnerId=15, DocumentReviewDate="2026-10-24T22:00:00Z")
        sp.login = APPROVER
        returned = execute(sp, "return", snapshot=execute(sp))
        self.assertEqual((returned["status"], returned["documentstatus"]), ("saved", "Entwurf"))
        self.assertEqual(sp.writes, [(16, {"DocumentStatus": "Entwurf"})])

    def test_caller_and_native_permissions_are_both_required(self):
        for login, can_edit, can_approve in ((READER, False, False), (EDITOR, True, False), (APPROVER, False, True)):
            with self.subTest(login=login):
                sp = SharePoint()
                sp.login = login
                draft = execute(sp)
                self.assertEqual(draft["canedit"], can_edit)
                sp.item.update(DocumentStatus="In Prüfung", Title="Dokument",
                       DocumentOwnerId=15, DocumentReviewDate="2026-10-24T22:00:00Z")
                review = execute(sp)
                self.assertEqual(review["canapprove"], can_approve)
                if not can_approve:
                    self.assertEqual(execute(sp, "approve", snapshot=review)["status"], "blocked")
                self.assertFalse(sp.writes)
        sp = SharePoint()
        sp.login = APPROVER
        sp.roles[APPROVER] = (16, "1", "Approver")
        sp.item.update(DocumentStatus="In Prüfung", Title="Dokument",
                       DocumentOwnerId=15, DocumentReviewDate="2026-10-24T22:00:00Z")
        self.assertEqual(execute(sp, "approve", snapshot=execute(sp))["status"], "blocked")
        self.assertFalse(sp.writes)

    def test_foreign_owner_cannot_be_overwritten(self):
        sp = SharePoint()
        sp.item["DocumentOwnerId"] = 16
        prepared = execute(sp)
        self.assertFalse(prepared["canedit"])
        self.assertEqual(execute(sp, "save", snapshot=prepared, title="Dokument", due="2026-10-26")["status"], "blocked")
        self.assertFalse(sp.writes)

    def test_wrong_library_invalid_id_folder_and_wildcard_are_rejected(self):
        sp = SharePoint()
        for kind, item_id in (("Unknown", 7), ("Policy", 7.5), ("Policy", 0), ("Policy", 2147483648)):
            self.assertEqual(execute(sp, kind=kind, item_id=item_id)["status"], "invalid")
        self.assertFalse(sp.requests)
        sp.item["FileSystemObjectType"] = 1
        self.assertEqual(execute(sp)["status"], "unavailable")
        self.assertEqual(execute(sp, "approve", snapshot={"revision": "*", "nativeversion": "1.0"})["status"], "invalid")
        self.assertFalse(sp.writes)

    def test_date_checks_and_unassigned_entwurf(self):
        for due in ("2026-02-30", "2026-10-24", "2026-1-01", "x"):
            sp = SharePoint()
            self.assertIn(execute(sp, "save", snapshot=execute(sp), title="Dokument", due=due)["status"],
                          ("invalid", "blocked"))
            self.assertFalse(sp.writes)
        sp = SharePoint()
        self.assertEqual(execute(sp, "submit", snapshot=execute(sp))["status"], "blocked")
        self.assertFalse(sp.writes)

    def test_stale_and_concurrent_approval_never_overwrite(self):
        sp = SharePoint()
        sp.login = APPROVER
        sp.item.update(DocumentStatus="In Prüfung", Title="Dokument",
                       DocumentOwnerId=15, DocumentReviewDate="2026-10-24T22:00:00Z")
        prepared = execute(sp)
        sp.revise()
        self.assertEqual(execute(sp, "approve", snapshot=prepared)["status"], "conflict")
        self.assertFalse(sp.writes)
        sp.race = True
        self.assertEqual(execute(sp, "approve", snapshot=execute(sp))["status"], "conflict")
        self.assertFalse(sp.writes)
        self.assertEqual(sp.item["DocumentStatus"], "In Prüfung")

    def test_unknown_or_incorrect_readback_requires_a_fresh_snapshot(self):
        for failure in ("failed_readback", "invalid_readback"):
            sp = SharePoint()
            setattr(sp, failure, True)
            first = execute(sp)
            self.assertEqual(execute(sp, "save", snapshot=first, title="Dokument", due="2026-10-26")["status"],
                             "unverified")
            self.assertEqual(execute(sp, "save", snapshot=first, title="Dokument", due="2026-10-26")["status"],
                             "conflict")
            self.assertEqual(len(sp.writes), 1)

    def test_invoker_binding_and_private_configuration_validation(self):
        self.assertEqual(FLOW["properties"]["connectionReferences"]["shared_sharepointonline"]["runtimeSource"],
                         "invoker")
        for libraries, editors, approvers in ((LIBRARIES, [], [APPROVER]),
                                               (LIBRARIES, [EDITOR], ["display name"]),
                                               (dict.fromkeys(KINDS, LIBRARIES["Policy"]), [EDITOR], [APPROVER])):
            with self.assertRaises(ValueError):
                build_flow(SITE, "sp_test", libraries, editors, approvers, "W. Europe Standard Time")

    def test_platform_nesting_limit_for_condition_actions(self):
        def depth(actions):
            return max((1 + max(depth(action.get("actions", {})),
                                depth(action.get("else", {}).get("actions", {})))
                        for action in actions.values()), default=0)

        self.assertLessEqual(depth(ACTIONS), 8)


if __name__ == "__main__":
    unittest.main()
