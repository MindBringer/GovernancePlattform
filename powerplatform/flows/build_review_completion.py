"""Render the invoker-bound Power Apps flow for manual review completion."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from build_evidence_upload import CONNECTOR, TRANSIENT, after, compose, condition

OBJECT_TYPES = ("Asset", "Change", "Risk")
MODEL = Path(__file__).resolve().parents[2] / "architecture" / "choices.yaml"
PENDING = "In Prüfung"
COMPLETED = "Abgeschlossen"
DATE_FORMAT = "yyyy-MM-dd"


def build_flow(site, reference, target_lists, reviews_list, reviewer_logins, time_zone):
    site_url = urlsplit(site)
    if (site_url.scheme != "https" or not site_url.hostname or not site_url.hostname.endswith(".sharepoint.com")
            or site_url.netloc != site_url.hostname or not re.fullmatch(r"/sites/[A-Za-z0-9_-]+", site_url.path)
            or site_url.query or site_url.fragment):
        raise ValueError("Expected the prechecked SharePoint site URL")
    if not re.fullmatch(r"[A-Za-z0-9_]+", reference):
        raise ValueError("Expected a SharePoint connection reference logical name")
    if set(target_lists) != set(OBJECT_TYPES):
        raise ValueError("Exactly the three supported target types must be configured")
    targets = {kind: str(UUID(target_lists[kind])) for kind in OBJECT_TYPES}
    reviews = str(UUID(reviews_list))
    if len(set(targets.values()) | {reviews}) != 4:
        raise ValueError("Target lists and Reviews must be distinct")
    logins = sorted({login.strip().lower() for login in reviewer_logins})
    if not logins or any(not re.fullmatch(r"i:0#\.f\|membership\|[a-z0-9._+%#-]+@[a-z0-9.-]+\.[a-z]+", login) for login in logins):
        raise ValueError("Expected explicitly approved SharePoint user login names")
    if not re.fullmatch(r"[A-Za-z0-9 .()+-]{1,80}", time_zone):
        raise ValueError("Expected the prechecked Windows timezone of the SharePoint site")

    choices = {entry["key"]: dict((row[0], row[1]) for row in entry["values"])
               for entry in json.loads(MODEL.read_text(encoding="utf-8"))["choiceSets"]}
    labels = {kind: choices["ReviewObjectType"][kind] for kind in OBJECT_TYPES}
    decisions = choices["ReviewResult"]
    if choices["ManualReviewState"] != {"InProgress": PENDING, "Completed": COMPLETED}:
        raise ValueError("Unexpected manual review status model")

    def expr_json(value):
        return "json('" + json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("'", "''") + "')"

    def param(name):
        return f"coalesce(triggerBody()?['{name}'], '')"

    def row(action):
        return f"body('{action}')?['d']"

    def value(action, key):
        return f"{row(action)}?['{key}']"

    def etag(item):
        return f"{item}?['__metadata']?['etag']"

    def entity_type(item):
        return f"{item}?['__metadata']?['type']"

    def date_at_site(field):
        # Older records can have empty dates. ISO normalization uses the site's date, including at DST boundaries.
        return f"convertTimeZone(coalesce({field}, '1900-01-01T12:00:00Z'), 'UTC', '{time_zone}', '{DATE_FORMAT}')"

    def date_for_list(day):
        return f"convertTimeZone(concat({day}, 'T00:00:00'), '{time_zone}', 'UTC', 'yyyy-MM-ddTHH:mm:ssZ')"

    def has_permission(action, mask):
        return f"equals(mod(div(int(coalesce({value(action, 'EffectiveBasePermissions')}?['Low'], '0')), {mask}), 2), 1)"

    def result(status, previous=None, *, target=False, review_id=0, due="", revision="", next_due="", review_date=""):
        fields = {"status": status, "targetid": request_id if target else 0,
                  "targettype": f"@{request_type}" if target else "", "reviewid": review_id,
                  "due": due, "revision": revision, "nextdue": next_due, "reviewdate": review_date}
        return {"type": "SetVariable", "inputs": {"name": "result", "value": fields},
                "runAfter": after(previous)}

    def phase(name):
        return {"type": "SetVariable", "inputs": {"name": "phase", "value": name}, "runAfter": {}}

    def rest(uri, previous=None, *, outcomes=None, body=None, match=None):
        headers = {"Accept": "application/json;odata=verbose"}
        parameters = {"dataset": site, "parameters/method": "POST" if body else "GET",
                      "parameters/uri": uri, "parameters/headers": headers}
        inputs = {"host": {"apiId": f"/providers/Microsoft.PowerApps/apis/{CONNECTOR}",
                           "connectionName": CONNECTOR, "operationId": "HttpRequest"},
                  "parameters": parameters, "authentication": "@parameters('$authentication')"}
        if body:
            headers["Content-Type"] = "application/json;odata=verbose"
            parameters["parameters/body"] = f"@string(outputs('{body}'))"
            inputs["retryPolicy"] = {"type": "none"}
        if match:
            headers.update({"IF-MATCH": f"@{match}", "X-HTTP-Method": "MERGE"})
        return {"type": "OpenApiConnection", "inputs": inputs, "runAfter": after(previous, outcomes)}

    request_type, mode = param("text"), param("text_1")
    original_due, revision, outcome, next_due = (param(f"text_{index}") for index in range(2, 6))
    id_input = "triggerBody()?['number']"
    request_id = f"@int({id_input})"
    target_lookup = (
        f"@concat('_api/web/lists(guid''', {expr_json(targets)}?[{request_type}], "
        f"''')/items(', string(int({id_input})), ')')"
    )
    target_select = "?$select=Id,Title,GovernanceID,IsActive,LastReviewDate,NextReviewDate,EffectiveBasePermissions"
    target_url = f"@concat(outputs('Target_url'), '{target_select}')"
    review_list = f"_api/web/lists(guid'{reviews}')"
    review_select = ("Id,GovernanceID,ReviewedObjectType,ReviewedItemID,AuthorId,ReviewerId,ReviewDate,ReviewResult,"
                     "NextReviewDate,ReviewPreviousDueDate,ReviewTargetETag,ManualReviewState")
    review_query = (f"@concat('{review_list.replace(chr(39), chr(39) * 2)}/items?$select={review_select}"
                    "&$top=2&$filter=GovernanceID%20eq%20%27', uriComponent(outputs('Review_key')), '%27')")
    reviewer_id = value("Current_user", "Id")
    target = row("Target")
    target_due = date_at_site(f"{target}?['NextReviewDate']")
    today = "outputs('Today_at_site')"
    last_date = date_at_site("outputs('Receipt')?['ReviewDate']")
    new_due = date_at_site("outputs('Receipt')?['NextReviewDate']")
    saved_due = date_at_site("outputs('Receipt')?['ReviewPreviousDueDate']")
    receipt = "outputs('Receipt')"
    receipt_etag = f"{receipt}?['ReviewTargetETag']"
    receipt_id = f"@int({receipt}?['Id'])"
    receipt_state = f"{receipt}?['ManualReviewState']"
    stable = f"equals({receipt_state}, '{COMPLETED}')"
    outcome_label = f"{expr_json(decisions)}?[{outcome}]"
    type_label = f"{expr_json(labels)}?[{request_type}]"
    review_rows = f"{row('Find_after_insert')}?['results']"
    in_window = (f"and(equals({target}?['IsActive'], true), not(empty({target}?['NextReviewDate'])), "
                 f"greaterOrEquals(ticks(concat({target_due}, 'T00:00:00Z')), ticks('1900-01-01T00:00:00Z')), "
                 f"lessOrEquals(ticks(concat({target_due}, 'T00:00:00Z')), ticks(addDays(concat({today}, 'T00:00:00Z'), 30))))")

    def verified_target(action):
        return (f"and(equals({value(action, 'Id')}, int({id_input})), "
                f"not(empty({value(action, 'LastReviewDate')})), not(empty({value(action, 'NextReviewDate')})), "
                f"equals({date_at_site(value(action, 'LastReviewDate'))}, {last_date}), "
                f"equals({date_at_site(value(action, 'NextReviewDate'))}, {new_due}))")

    def completed(prev=None):
        return result("saved", prev, target=True, review_id=receipt_id,
                      due=f"@{saved_due}", next_due=f"@{new_due}", review_date=f"@{last_date}")

    receipt_url = (f"@concat('{review_list.replace(chr(39), chr(39) * 2)}/items(', "
                   f"string({receipt}?['Id']), ')')")
    confirm_status = {
        "Receipt_url": compose(receipt_url),
        "Mark_payload": compose({"__metadata": {"type": f"@{entity_type(receipt)}"},
                                 "ManualReviewState": COMPLETED}, "Receipt_url"),
        "Mark_completed": rest("@outputs('Receipt_url')", "Mark_payload", body="Mark_payload", match=etag(receipt)),
        "Read_completed": rest(f"@concat(outputs('Receipt_url'), '?$select={review_select}')",
                              "Mark_completed", outcomes=TRANSIENT),
        "Confirm_completed": condition(
            f"@and(equals({value('Read_completed','Id')}, {receipt}?['Id']), "
            f"equals({value('Read_completed','GovernanceID')}, outputs('Review_key')), "
            f"equals({value('Read_completed','ReviewedObjectType')}, {type_label}), "
            f"equals({value('Read_completed','ReviewedItemID')}, int({id_input})), "
            f"equals({value('Read_completed','AuthorId')}, {reviewer_id}), "
            f"equals({value('Read_completed','ReviewerId')}, {reviewer_id}), "
            f"equals({value('Read_completed','ReviewResult')}, {receipt}?['ReviewResult']), "
            f"equals({value('Read_completed','ReviewTargetETag')}, {receipt_etag}), "
            f"equals({date_at_site(value('Read_completed','ReviewDate'))}, {last_date}), "
            f"equals({date_at_site(value('Read_completed','ReviewPreviousDueDate'))}, {saved_due}), "
            f"equals({date_at_site(value('Read_completed','NextReviewDate'))}, {new_due}), "
            f"equals({value('Read_completed','ManualReviewState')}, '{COMPLETED}'))",
            {"Report_review_saved": completed()}, "Read_completed"),
    }

    apply_schedule = {
        "Mark_recovery_required": result("pending", target=True, review_id=receipt_id, due=f"@{saved_due}"),
        "Read_target_before_merge": rest(target_url, "Mark_recovery_required"),
        "Check_original_target_version": condition(
            f"@and(equals({value('Read_target_before_merge','Id')}, int({id_input})), "
            f"equals({value('Read_target_before_merge','IsActive')}, true), "
            f"{has_permission('Read_target_before_merge', 4)}, not(empty({receipt_etag})), "
            f"not(equals({receipt_etag}, '*')), equals({etag(row('Read_target_before_merge'))}, {receipt_etag}), "
            f"equals({date_at_site(value('Read_target_before_merge','NextReviewDate'))}, {saved_due}))",
            {
                "Schedule_payload": compose({
                    "__metadata": {"type": f"@{entity_type(row('Read_target_before_merge'))}"},
                    "LastReviewDate": f"@{date_for_list(last_date)}",
                    "NextReviewDate": f"@{date_for_list(new_due)}",
                }),
                "Update_schedule": rest("@outputs('Target_url')", "Schedule_payload",
                                        body="Schedule_payload", match=receipt_etag),
            }, "Read_target_before_merge"),
        "Read_target_after_merge": rest(target_url, "Check_original_target_version", outcomes=TRANSIENT),
        "Verify_schedule": condition(
            f"@and({verified_target('Read_target_after_merge')}, not(empty({etag(receipt)})), "
            f"not(equals({etag(receipt)}, '*')), not(empty({entity_type(receipt)})))",
            confirm_status, "Read_target_after_merge",
            {"Classify_schedule_conflict": condition(
                f"@not(equals({etag(row('Read_target_after_merge'))}, {receipt_etag}))",
                {"Report_target_conflict": result("conflict", target=True, review_id=receipt_id, due=f"@{saved_due}")},
                None,
            )},
        ),
    }

    valid_receipt = (f"and(equals({receipt}?['GovernanceID'], outputs('Review_key')), "
                     f"equals({receipt}?['ReviewedItemID'], int({id_input})), "
                     f"equals({receipt}?['ReviewedObjectType'], {type_label}), "
                     f"equals({receipt}?['AuthorId'], {reviewer_id}), "
                     f"equals({receipt}?['ReviewerId'], {reviewer_id}), "
                     f"equals({saved_due}, {original_due}), "
                     f"contains({expr_json(list(decisions.values()))}, {receipt}?['ReviewResult']), "
                     f"not(empty({receipt}?['ReviewDate'])), not(empty({receipt}?['NextReviewDate'])), "
                     f"greater(ticks(concat({new_due}, 'T00:00:00Z')), ticks(concat({saved_due}, 'T00:00:00Z'))), "
                     f"greater(ticks(concat({new_due}, 'T00:00:00Z')), ticks(concat({last_date}, 'T00:00:00Z'))), "
                     f"or(equals({mode}, 'resume'), and(equals({outcome_label}, {receipt}?['ReviewResult']), "
                     f"equals({next_due}, {new_due}), equals({revision}, {receipt_etag}))), "
                     f"contains(createArray('{PENDING}', '{COMPLETED}'), {receipt_state}))")

    create_receipt = {
        "Create_payload": compose({
            "__metadata": {"type": f"@{value('Reviews_contract', 'ListItemEntityTypeFullName')}"},
            "Title": "@outputs('Review_key')",
            "GovernanceID": "@outputs('Review_key')",
            "ReviewedObjectType": f"@{type_label}",
            "ReviewedItemID": request_id,
            "ReviewedTitle": f"@coalesce({target}?['Title'], '')",
            "ReviewedGovernanceID": f"@coalesce({target}?['GovernanceID'], '')",
            "ReviewDate": f"@{date_for_list(today)}",
            "ReviewerId": f"@int({reviewer_id})",
            "ReviewResult": f"@{outcome_label}",
            "ReviewPreviousDueDate": f"@{date_for_list(original_due)}",
            "NextReviewDate": f"@{date_for_list(next_due)}",
            "ReviewTargetETag": f"@{etag(target)}",
            "ManualReviewState": PENDING,
        }),
        "Mark_insert_in_doubt": result("retry", "Create_payload", target=True, due=f"@{original_due}"),
        "Create_receipt": rest(review_list + "/items", "Mark_insert_in_doubt", body="Create_payload"),
    }
    valid_new_review = (
        f"and(equals({mode}, 'save'), empty({row('Find_existing')}?['results']), {in_window}, "
        f"equals({target_due}, {original_due}), equals({etag(target)}, {revision}), "
        f"not(empty({etag(target)})), not(equals({etag(target)}, '*')), "
        f"greater(ticks(concat({next_due}, 'T00:00:00Z')), ticks(concat({original_due}, 'T00:00:00Z'))), "
        f"greater(ticks(concat({next_due}, 'T00:00:00Z')), ticks(concat({today}, 'T00:00:00Z'))))"
    )
    persisted = {
        "Key_contract": rest(review_list + "/fields/getbyinternalnameortitle('GovernanceID')?$select=EnforceUniqueValues,Indexed"),
        "Require_unique_key": condition(
            f"@and(equals({value('Key_contract','EnforceUniqueValues')}, true), equals({value('Key_contract','Indexed')}, true))",
            {
                "Mark_initial_conflict": result("conflict", target=True),
                "Review_key": compose(f"@concat('RVR-', {request_type}, '-', string(int({id_input})), '-', {original_due})",
                                      "Mark_initial_conflict"),
                "Find_existing": rest(review_query, "Review_key"),
                "Reserve_if_new": condition(f"@{valid_new_review}", create_receipt, "Find_existing"),
                "Find_after_insert": rest(review_query, "Reserve_if_new", outcomes=TRANSIENT),
                "Require_one_record": condition(
                    f"@equals(length({review_rows}), 1)", {
                        "Receipt": compose(f"@first({review_rows})"),
                        "Check_receipt": condition(f"@{valid_receipt}",
                            {"Accept_frozen_intent": phase("receipt_verified")},
                            "Receipt", {"Report_receipt_conflict": result("conflict", target=True)}),
                    }, "Find_after_insert"),
            }, "Key_contract",
            {"Report_key_configuration": result("configuration", target=True)}),
    }
    after_roles = {
        "Today_at_site": compose(f"@convertTimeZone(utcNow(), 'UTC', '{time_zone}', '{DATE_FORMAT}')"),
        "Prepare_or_write": condition(
            f"@equals({mode}, 'prepare')",
            {
                "Review_eligible": condition(f"@and({in_window}, not(empty({etag(target)})), not(equals({etag(target)}, '*')))",
                    {"Report_ready": result("ready", target=True, due=f"@{target_due}", revision=f"@{etag(target)}")},
                    None, {"Report_not_due": result("not_due", target=True)}),
            }, "Today_at_site", persisted),
    }
    authorized = {
        "Target_url": compose(target_lookup),
        "Target": rest(target_url, "Target_url"),
        "Reviews_contract": rest(review_list + "?$select=EffectiveBasePermissions,ListItemEntityTypeFullName", "Target"),
        "Require_native_edit": condition(
            f"@and(equals({target}?['Id'], int({id_input})), {has_permission('Target', 4)}, "
            f"{has_permission('Reviews_contract', 2)}, {has_permission('Reviews_contract', 4)}, "
            f"not(empty({value('Reviews_contract','ListItemEntityTypeFullName')})))",
            {"Accept_target_permissions": phase("target_authorized")}, "Reviews_contract",
            {"Report_native_denied": result("blocked", target=True)}),
    }

    initial = {"status": "invalid", "targetid": 0, "targettype": "", "reviewid": 0,
               "due": "", "revision": "", "nextdue": "", "reviewdate": ""}
    schema = {name: {"title": name, "type": "number" if isinstance(default, int) else "string",
                     "x-ms-dynamically-added": True} for name, default in initial.items()}
    # Shape validation is separated from date parsing so malformed or empty values can never reach SharePoint.
    date_shape = (f"and(equals(length({original_due}), 10), "
                  f"or(equals({mode}, 'resume'), and(equals(length({next_due}), 10), "
                  f"contains({expr_json(list(decisions))}, {outcome}), not(empty({revision})), "
                  f"not(equals({revision}, '*')), lessOrEquals(length({revision}), 180))))")
    day_for_validation = f"if(equals({mode}, 'prepare'), '1900-01-01', {original_due})"
    next_for_validation = f"if(equals({mode}, 'save'), {next_due}, '1900-01-01')"
    date_valid = (
        f"@and(or(equals({mode}, 'prepare'), equals(formatDateTime({day_for_validation}, '{DATE_FORMAT}'), {original_due})), "
        f"or(not(equals({mode}, 'save')), equals(formatDateTime({next_for_validation}, '{DATE_FORMAT}'), {next_due})))"
    )
    actions = {
        "Initial_result": {"type": "InitializeVariable", "inputs": {"variables": [
            {"name": "result", "type": "object", "value": initial},
            {"name": "phase", "type": "string", "value": ""},
        ]}, "runAfter": {}},
        "Validate_input": condition(
            f"@and(contains({expr_json(OBJECT_TYPES)}, {request_type}), contains(createArray('prepare','save','resume'), {mode}), "
            f"greater({id_input}, 0), lessOrEquals({id_input}, 2147483647), equals({id_input}, int({id_input})), "
            f"or(equals({mode}, 'prepare'), {date_shape}))",
            {
                "Require_valid_dates": condition(
                    date_valid,
                    {
                        "Default_denied": result("blocked", target=True),
                        "Current_user": rest("_api/web/currentuser?$select=Id,LoginName", "Default_denied"),
                        "Require_reviewer": condition(
                            f"@and(greater(int(coalesce({reviewer_id}, 0)), 0), "
                            f"contains({expr_json(logins)}, toLower(coalesce({value('Current_user','LoginName')}, ''))))",
                            {"Accept_reviewer_identity": phase("reviewer_verified")}, "Current_user"),
                    }, None),
            }, "Initial_result"),
        "Load_authorized_target": condition(
            "@equals(variables('phase'), 'reviewer_verified')",
            authorized, "Validate_input", outcomes=TRANSIENT),
        "Read_or_reserve_review": condition(
            "@equals(variables('phase'), 'target_authorized')",
            after_roles, "Load_authorized_target", outcomes=TRANSIENT),
        "Complete_verified_review": condition(
            "@equals(variables('phase'), 'receipt_verified')",
            {"Already_completed": condition(f"@{stable}", {"Replay_saved": completed()}, None, apply_schedule)},
            "Read_or_reserve_review", outcomes=TRANSIENT),
        "Respond": {"type": "Response", "kind": "PowerApp", "inputs": {
            "statusCode": 200, "body": {name: f"@variables('result')?['{name}']" for name in schema},
            "schema": {"type": "object", "properties": schema},
        }, "runAfter": after("Complete_verified_review", TRANSIENT)},
    }
    trigger_fields = {}
    for wire_name, title, data_type in (
        ("number", "Objekt-ID", "number"), ("text", "Objekttyp", "string"), ("text_1", "Aktion", "string"),
        ("text_2", "Bisheriger Termin", "string"), ("text_3", "Objektversion", "string"),
        ("text_4", "Entscheidung", "string"), ("text_5", "Folgetermin", "string"),
    ):
        trigger_fields[wire_name] = {"title": title, "description": title, "type": data_type,
                                     "x-ms-dynamically-added": True,
                                     "x-ms-content-hint": "NUMBER" if data_type == "number" else "TEXT"}
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
                        help="Private deployment JSON with site, reference, target_lists, reviews_list, reviewer_logins and time_zone")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    request = json.loads(args.config.read_text(encoding="utf-8"))
    args.output.write_text(json.dumps(build_flow(**request), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
