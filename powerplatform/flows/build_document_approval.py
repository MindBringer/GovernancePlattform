"""Render the invoker-bound document metadata and approval flow."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from build_evidence_upload import CONNECTOR, TRANSIENT, after, compose, condition

KINDS = ("Policy", "Procedure", "Runbook")
MODEL = Path(__file__).resolve().parents[2] / "architecture" / "choices.yaml"
REVIEW_DATE_FORMAT = "yyyy-MM-dd"
SELECT = (
    "?$select=Id,Title,EditorId,FileSystemObjectType,FileLeafRef,OData__UIVersionString,EffectiveBasePermissions,"
    "DocumentStatus,DocumentOwnerId,DocumentOwner/Title,DocumentReviewDate,ApprovedById,ApprovedBy/Title,"
    "ApprovedDate,DocumentVersion&$expand=DocumentOwner,ApprovedBy"
)


def build_flow(site, reference, libraries, editor_logins, approver_logins, time_zone):
    site_url = urlsplit(site)
    if (site_url.scheme != "https" or not site_url.hostname or not site_url.hostname.endswith(".sharepoint.com")
            or site_url.netloc != site_url.hostname or not re.fullmatch(r"/sites/[A-Za-z0-9_-]+", site_url.path)
            or site_url.query or site_url.fragment):
        raise ValueError("Expected the prechecked SharePoint site URL")
    if not re.fullmatch(r"[A-Za-z0-9_]+", reference):
        raise ValueError("Expected a SharePoint connection reference logical name")
    if set(libraries) != set(KINDS):
        raise ValueError("Exactly the three document libraries must be configured")
    targets = {kind: str(UUID(libraries[kind])) for kind in KINDS}
    if len(set(targets.values())) != len(KINDS):
        raise ValueError("Document libraries must be distinct")
    if not re.fullmatch(r"[A-Za-z0-9 .()+-]{1,80}", time_zone):
        raise ValueError("Expected the prechecked Windows timezone of the SharePoint site")

    def approved_logins(values):
        logins = sorted({login.strip().lower() for login in values})
        if not logins or any(not re.fullmatch(r"i:0#\.f\|membership\|[a-z0-9._+%#-]+@[a-z0-9.-]+\.[a-z]+", login)
                             for login in logins):
            raise ValueError("Expected explicit, prechecked SharePoint user logins")
        return logins

    editors = approved_logins(editor_logins)
    approvers = approved_logins(approver_logins)
    choices = json.loads(MODEL.read_text(encoding="utf-8"))["choiceSets"]
    status = next(entry for entry in choices if entry["key"] == "DocumentStatus")
    labels = {row[0]: row[1] for row in status["values"]}
    draft, review, published = (labels[key] for key in ("Draft", "InReview", "Published"))

    def json_expression(value):
        return "json('" + json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("'", "''") + "')"

    def param(name):
        return f"coalesce(triggerBody()?['{name}'], '')"

    def row(action):
        return f"body('{action}')?['d']"

    def field(item, name):
        return f"{item}?['{name}']"

    def etag(item):
        return f"{item}?['__metadata']?['etag']"

    def value_or_empty(item, name):
        return f"coalesce({field(item, name)}, '')"

    def day_at_site(value):
        return (f"convertTimeZone(coalesce({value}, '1900-01-01T12:00:00Z'), "
                f"'UTC', '{time_zone}', '{REVIEW_DATE_FORMAT}')")

    def date_for_list(day):
        return f"convertTimeZone(concat({day}, 'T00:00:00'), '{time_zone}', 'UTC', 'yyyy-MM-ddTHH:mm:ssZ')"

    def date_or_empty(value):
        return f"if(empty(coalesce({value}, '')), '', {day_at_site(value)})"

    def valid_tag(value):
        return (f"and(not(empty(coalesce({value}, ''))), not(equals({value}, '*')), "
                f"lessOrEquals(length(coalesce({value}, '')), 180))")

    kind, mode = param("text"), param("text_1")
    expected_etag, expected_version = param("text_2"), param("text_3")
    title, due = f"trim({param('text_4')})", param("text_5")
    item_id = "coalesce(triggerBody()?['number'], 0)"
    user = row("Current_user")
    login = f"toLower({value_or_empty(user, 'LoginName')})"
    actor = f"int(coalesce({field(user, 'Id')}, 0))"
    target = row("Read_document")
    target_url = "@outputs('Document_url')"
    select_url = f"@concat(outputs('Document_url'), '{SELECT}')"

    def can_write(item):
        mask = f"int(coalesce({field(item, 'EffectiveBasePermissions')}?['Low'], '0'))"
        return f"and(greater({actor}, 0), equals(mod(div({mask}, 4), 2), 1))"

    def state(item):
        value = value_or_empty(item, "DocumentStatus")
        return f"if(empty({value}), '{draft}', {value})"

    def can_edit(item, allow_claim):
        owner = f"int(coalesce({field(item, 'DocumentOwnerId')}, 0))"
        owner_allowed = f"or(equals({owner}, 0), equals({owner}, {actor}))" if allow_claim else f"equals({owner}, {actor})"
        return (f"and({can_write(item)}, contains({json_expression(editors)}, {login}), "
                f"equals({state(item)}, '{draft}'), {owner_allowed})")

    def has_review_details(item):
        return (f"and(greater(int(coalesce({field(item, 'DocumentOwnerId')}, 0)), 0), "
                f"not(empty(trim({value_or_empty(item, 'Title')}))), "
                f"not(empty({value_or_empty(item, 'DocumentReviewDate')})))")

    def can_submit(item):
        return (f"and({can_edit(item, False)}, {has_review_details(item)}, "
                f"greaterOrEquals(ticks(concat({day_at_site(field(item, 'DocumentReviewDate'))}, 'T00:00:00Z')), "
                f"ticks(concat({day_at_site('utcNow()')}, 'T00:00:00Z'))))")

    def can_decide(item):
        return (f"and({can_write(item)}, contains({json_expression(approvers)}, {login}), "
                f"equals({state(item)}, '{review}'))")

    def can_approve(item):
        return f"and({can_decide(item)}, {has_review_details(item)})"

    def valid_document(item):
        return (f"and(equals({field(item, 'Id')}, int({item_id})), "
                f"equals({field(item, 'FileSystemObjectType')}, 0), {valid_tag(etag(item))}, "
                f"not(empty(coalesce({item}?['__metadata']?['type'], ''))), "
                f"not(empty({value_or_empty(item, 'OData__UIVersionString')})))")

    def rest(uri, previous=None, *, outcomes=None, body=None):
        headers = {"Accept": "application/json;odata=verbose"}
        parameters = {"dataset": site, "parameters/method": "POST" if body else "GET",
                      "parameters/uri": uri, "parameters/headers": headers}
        inputs = {"host": {"apiId": f"/providers/Microsoft.PowerApps/apis/{CONNECTOR}",
                           "connectionName": CONNECTOR, "operationId": "HttpRequest"},
                  "parameters": parameters, "authentication": "@parameters('$authentication')"}
        if body:
            headers.update({"Content-Type": "application/json;odata=verbose",
                            "IF-MATCH": f"@{expected_etag}", "X-HTTP-Method": "MERGE"})
            parameters["parameters/body"] = f"@string(outputs('{body}'))"
            inputs["retryPolicy"] = {"type": "none"}
        return {"type": "OpenApiConnection", "inputs": inputs, "runAfter": after(previous, outcomes)}

    initial = {"status": "invalid", "itemid": 0, "kind": "", "title": "", "filename": "", "owner": "",
               "reviewdate": "", "documentstatus": "", "revision": "", "nativeversion": "",
               "approvedversion": "", "approvedby": "", "approveddate": "", "canedit": False,
               "cansubmit": False, "canapprove": False, "canreturn": False}
    field_types = {bool: "boolean", int: "number", str: "string"}
    schema = {name: {"title": name, "type": field_types[type(default)], "x-ms-dynamically-added": True}
              for name, default in initial.items()}

    def report(code, previous=None, *, item=None, outcomes=None):
        fields = {**initial, "status": code}
        if item:
            fields.update({
                "itemid": f"@int({item_id})", "kind": f"@{kind}",
                "title": f"@{value_or_empty(item, 'Title')}", "filename": f"@{value_or_empty(item, 'FileLeafRef')}",
                "owner": f"@coalesce({field(item, 'DocumentOwner')}?['Title'], '')",
                "reviewdate": f"@{date_or_empty(field(item, 'DocumentReviewDate'))}",
                "documentstatus": f"@{state(item)}", "revision": f"@{etag(item)}",
                "nativeversion": f"@{value_or_empty(item, 'OData__UIVersionString')}",
                "approvedversion": f"@{value_or_empty(item, 'DocumentVersion')}",
                "approvedby": f"@coalesce({field(item, 'ApprovedBy')}?['Title'], '')",
                "approveddate": f"@{date_or_empty(field(item, 'ApprovedDate'))}",
                "canedit": f"@{can_edit(item, True)}", "cansubmit": f"@{can_submit(item)}",
                "canapprove": f"@{can_approve(item)}", "canreturn": f"@{can_decide(item)}",
            })
        return {"type": "SetVariable", "inputs": {"name": "result", "value": fields},
                "runAfter": after(previous, outcomes)}

    actions = {
        "Initialize_result": {"type": "InitializeVariable",
                              "inputs": {"variables": [{"name": "result", "type": "object", "value": initial}]},
                              "runAfter": {}},
    }
    approval_day = "outputs('Approval_day')"
    changes = {
        "save": {
            "DocumentStatus": draft, "Title": f"@{title}", "DocumentOwnerId": f"@{actor}",
            "DocumentReviewDate": f"@{date_for_list(due)}",
        },
        "submit": {"DocumentStatus": review},
        "return": {"DocumentStatus": draft},
        "approve": {
            "DocumentStatus": published, "ApprovedById": f"@{actor}", "ApprovedDate": f"@{date_for_list(approval_day)}",
            "DocumentVersion": f"@{expected_version}",
        },
    }
    edit_contract = (f"and({can_edit(target, True)}, not(empty({title})), lessOrEquals(length({title}), 255), "
                     f"equals(length({due}), 10), equals(formatDateTime({due}, '{REVIEW_DATE_FORMAT}'), {due}), "
                     f"greaterOrEquals(ticks(concat({due}, 'T00:00:00Z')), "
                     f"ticks(concat({day_at_site('utcNow()')}, 'T00:00:00Z'))))")
    eligibility = {"save": edit_contract, "submit": can_submit(target),
                   "return": can_decide(target), "approve": can_approve(target)}
    def verify_fields(action, item):
        if action == "save":
            return (
                f"equals({field(item, 'Title')}, {title})",
                f"equals({field(item, 'DocumentOwnerId')}, {actor})",
                f"equals({day_at_site(field(item, 'DocumentReviewDate'))}, {due})",
            )
        if action == "approve":
            return (
                f"equals({field(item, 'ApprovedById')}, {actor})",
                f"equals({field(item, 'DocumentVersion')}, {expected_version})",
                f"equals({day_at_site(field(item, 'ApprovedDate'))}, {approval_day})",
            )
        return ()

    decisions = {"Approval_day": compose(f"@{day_at_site('utcNow()')}", "Default_blocked")}
    for action, payload in changes.items():
        key = action.capitalize()
        payload_action = f"{key}_payload"
        update_action, read_action = f"{key}_metadata", f"{key}_readback"
        readback = row(read_action)
        expected_checks = [valid_document(readback), f"not(equals({etag(readback)}, {expected_etag}))",
                           f"equals({field(readback, 'EditorId')}, {actor})",
                           f"equals({field(readback, 'DocumentStatus')}, '{payload['DocumentStatus']}')",
                           *verify_fields(action, readback)]
        write = {
            f"{key}_unknown_before_write": report("unverified"),
            payload_action: compose(
                {"__metadata": {"type": f"@{target}?['__metadata']?['type']"}, **payload},
                f"{key}_unknown_before_write",
            ),
            update_action: rest(target_url, payload_action, body=payload_action),
            # A successful write receives a readback. Never infer success from a changed item after a failed write.
            read_action: rest(select_url, update_action),
            f"{key}_verified": condition(
                f"@and({', '.join(expected_checks)})",
                {f"{key}_saved": report("saved", item=readback)}, read_action),
            f"{key}_failed": condition(
                f"@equals(coalesce(outputs('{update_action}')?['statusCode'], 0), 412)",
                {f"{key}_conflict": report("conflict")}, update_action, outcomes=["Failed"]),
        }
        decisions[f"Handle_{action}"] = condition(
            f"@equals({mode}, '{action}')",
            {f"{key}_eligible": condition(f"@{eligibility[action]}", write, None)},
            "Approval_day",
        )

    actions.update({
        "Validate_input": condition(
            f"@and(contains({json_expression(KINDS)}, {kind}), greater({item_id}, 0), "
            f"lessOrEquals({item_id}, 2147483647), equals({item_id}, int({item_id})), "
            f"or(equals({mode}, 'prepare'), and(contains({json_expression(list(changes))}, {mode}), "
            f"{valid_tag(expected_etag)}, not(empty({expected_version})), lessOrEquals(length({expected_version}), 32))))",
            {
                "Default_unavailable": report("unavailable"),
                "Document_url": compose(
                    f"@concat('_api/web/lists(guid''', {json_expression(targets)}?[{kind}], "
                    f"''')/items(', string(int({item_id})), ')')", "Default_unavailable"),
                "Current_user": rest("_api/web/currentuser?$select=Id,LoginName", "Document_url"),
                "Read_document": rest(select_url, "Current_user"),
                "Require_document": condition(
                    f"@{valid_document(target)}",
                    {"Prepare_or_write": condition(
                        f"@equals({mode}, 'prepare')", {"Report_snapshot": report("ready", item=target)}, None,
                        {"Require_snapshot": condition(
                            f"@and(equals({etag(target)}, {expected_etag}), "
                            f"equals({field(target, 'OData__UIVersionString')}, {expected_version}))",
                            {"Default_blocked": report("blocked"), **decisions},
                            None, {"Reject_stale_snapshot": report("conflict")},
                        )},
                    )}, "Read_document"),
            }, "Initialize_result"),
        "Respond": {"type": "Response", "kind": "PowerApp", "inputs": {
            "statusCode": 200, "body": {name: f"@variables('result')?['{name}']" for name in schema},
            "schema": {"type": "object", "properties": schema},
        }, "runAfter": after("Validate_input", TRANSIENT)},
    })

    trigger_fields = {}
    for wire_name, label in (
        ("number", "Listen-ID"), ("text", "Dokumentart"), ("text_1", "Aktion"),
        ("text_2", "Listenrevision"), ("text_3", "SharePoint-Version"),
        ("text_4", "Titel"), ("text_5", "Reviewtermin"),
    ):
        number = wire_name == "number"
        trigger_fields[wire_name] = {"title": label, "description": label,
                                     "type": "number" if number else "string",
                                     "x-ms-dynamically-added": True,
                                     "x-ms-content-hint": "NUMBER" if number else "TEXT"}
    return {"properties": {
        "connectionReferences": {CONNECTOR: {"runtimeSource": "invoker", "api": {"name": CONNECTOR},
                                             "connection": {"connectionReferenceLogicalName": reference}}},
        "definition": {
            "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
            "contentVersion": "1.0.0.0",
            "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                           "$connections": {"defaultValue": {}, "type": "Object"}},
            "triggers": {"manual": {"type": "Request", "kind": "PowerAppV2", "inputs": {"schema": {
                "type": "object", "properties": trigger_fields, "required": list(trigger_fields),
            }}}},
            "actions": actions,
            "outputs": {},
        },
        "templateName": "",
    }, "schemaVersion": "1.0.0.0"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path,
                        help="Private JSON with site, reference, libraries, editor_logins, approver_logins and time_zone")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    request = json.loads(args.config.read_text(encoding="utf-8"))
    args.output.write_text(json.dumps(build_flow(**request), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
