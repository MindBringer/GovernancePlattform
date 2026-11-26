"""Build the invoker-bound Finding workflow for the two access boundaries."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from build_control_write import body, identifier, permission
from build_evidence_upload import CONNECTOR, TRANSIENT, after, compose, condition

ARCHITECTURE = Path(__file__).resolve().parents[2] / "architecture"
ITEM_FIELDS = (
    "Id,Title,Description,GovernanceID,OwnerId,AuthorId,EditorId,IsActive,EffectiveBasePermissions,"
    "FindingStatus,FindingDueDate,FindingSourceItemID,FindingMeasureItemID,FindingEvidenceItemID,"
    "FindingClosureNote,FindingClosedById,FindingClosedAt,FindingEvidenceVersion,OData__UIVersionString"
)
SCOPE = {"review": ("Findings", "FND-"), "audit": ("AuditFindings", "FNA-")}


def field(record, name):
    return f"{record}?['{name}']"


def eq(left, right):
    return f"equals({left}, {right})"


def both(*expressions):
    return "and(" + ", ".join(expressions) + ")"


def one_of(*expressions):
    return "or(" + ", ".join(expressions) + ")"


def clean(expression):
    return f"trim(coalesce({expression}, ''))"


def literal(value):
    return "'" + value.replace("'", "''") + "'"


def choices(model):
    data = json.loads((ARCHITECTURE / "status-models.yaml").read_text(encoding="utf-8"))
    return {key: label for key, label, *_ in next(row["states"] for row in data["statusModels"] if row["key"] == model)}


def build_flow(site, reference, findings_list, audit_findings_list, reviews_list, audit_library,
               measures_list, evidence_library, time_zone):
    parts = urlsplit(site)
    if (parts.scheme != "https" or not parts.hostname or not parts.hostname.endswith(".sharepoint.com")
            or parts.netloc != parts.hostname or not re.fullmatch(r"/sites/[A-Za-z0-9_-]+", parts.path)
            or parts.query or parts.fragment):
        raise ValueError("Expected a SharePoint site URL")
    if not re.fullmatch(r"[A-Za-z0-9_]+", reference) or not re.fullmatch(r"[A-Za-z0-9 .()+-]{1,80}", time_zone):
        raise ValueError("Expected the connection reference and site time zone")
    ids = [str(UUID(value)) for value in (findings_list, audit_findings_list, reviews_list, audit_library,
                                        measures_list, evidence_library)]
    if len(set(ids)) != 6:
        raise ValueError("Review and audit must have different finding lists and dedicated sources")
    findings, audit_findings, reviews, audit, measures, evidence = (f"_api/web/lists(guid'{value}')" for value in ids)
    labels = choices("Finding")
    measure_labels = choices("Measure")
    states = json.loads((ARCHITECTURE / "status-models.yaml").read_text(encoding="utf-8"))["statusModels"]
    finding_states = next(row["states"] for row in states if row["key"] == "Finding")
    assert [(state[0], state[4]) for state in finding_states] == [
        ("Open", ["InProgress"]), ("InProgress", ["Closed"]), ("Closed", [])
    ]

    def request(name, default):
        return f"coalesce(triggerBody()?['{name}'], {default})"

    scope, action, expected = (request(name, "''") for name in ("text", "text_1", "text_2"))
    item = request("number", 0)
    audit_mode = eq(scope, "'audit'")
    create_mode, plan_mode, close_mode = (eq(action, "'"+name+"'") for name in ("create", "plan", "close"))
    prepare_mode = eq(action, "'prepare'")
    args = "outputs('Parse_request')"
    title, description, owner_claim, due, note, key = (
        clean(field(args, name)) for name in ("title", "description", "owner", "due", "note", "key")
    )
    source_id, new_measure, new_evidence = (
        f"coalesce({field(args, name)}, 0)" for name in ("source", "measure", "evidence")
    )
    row = body("Read_finding")
    finding_list = "outputs('Finding_list')"
    finding_uri = "outputs('Finding_uri')"
    revision = f"coalesce({row}?['__metadata']?['etag'], '')"
    actor = f"int(coalesce({body('Read_actor')}?['Id'], 0))"
    status = field(row, "FindingStatus")
    open_state, in_progress, closed_state = (f"'{labels[name]}'" for name in ("Open", "InProgress", "Closed"))
    assignee = body("Read_owner")
    owner_id = field(assignee, "Id")
    can_edit = both(eq(field(row, "IsActive"), "true"), permission(row, 4), f"not({eq(status, closed_state)})")
    needs_plan = one_of(create_mode, plan_mode)
    measure_id = f"if({close_mode}, coalesce({field(row, 'FindingMeasureItemID')}, 0), if({needs_plan}, {new_measure}, 0))"
    evidence_id = f"if({close_mode}, coalesce({field(row, 'FindingEvidenceItemID')}, 0), if({needs_plan}, {new_evidence}, 0))"
    proof = body("Read_evidence")
    verification_version = clean(field(proof, "OData__UIVersionString"))

    def rest(uri, previous, *, data=None, match=None, outcomes=None):
        headers = {"Accept": "application/json;odata=verbose"}
        parameters = {"dataset": site, "parameters/method": "POST" if data else "GET",
                      "parameters/uri": uri, "parameters/headers": headers}
        inputs = {"host": {"apiId": f"/providers/Microsoft.PowerApps/apis/{CONNECTOR}",
                           "connectionName": CONNECTOR, "operationId": "HttpRequest"},
                  "parameters": parameters, "authentication": "@parameters('$authentication')"}
        if data:
            headers["Content-Type"] = "application/json;odata=verbose"
            parameters["parameters/body"] = f"@string(outputs('{data}'))"
            inputs["retryPolicy"] = {"type": "none"}
        if match:
            headers.update({"X-HTTP-Method": "MERGE", "IF-MATCH": match})
        return {"type": "OpenApiConnection", "inputs": inputs, "runAfter": after(previous, outcomes),
                "runtimeConfiguration": {"secureData": {"properties": ["inputs", "outputs"]}}}

    def set_value(name, value, previous=None, outcomes=None):
        return {"type": "SetVariable", "inputs": {"name": name, "value": value},
                "runAfter": after(previous, outcomes)}

    defaults = {"status": "invalid", "itemid": 0, "revision": "", "canedit": False, "nativeversion": ""}
    schema = {name: {"title": name, "type": {str: "string", int: "number", bool: "boolean"}[type(value)],
                     "x-ms-dynamically-added": True} for name, value in defaults.items()}

    def report(status_code, previous=None, **values):
        return set_value("result", {**defaults, "status": status_code, **values}, previous)

    def stage_ready():
        return report("ready")

    def is_result(code):
        return eq("variables('result')?['status']", f"'{code}'")

    def ready():
        return is_result("ready")

    def select_item(path, number, fields):
        return f"@concat({literal(path + '/items(')}, string(int({number})), ')?$select={fields}')"

    def native_day(value):
        return f"convertTimeZone(coalesce({value}, '1900-01-01T12:00:00Z'), 'UTC', '{time_zone}', 'yyyy-MM-dd')"

    def native_midnight(value):
        return f"convertTimeZone(concat({value}, 'T00:00:00'), '{time_zone}', 'UTC', 'yyyy-MM-ddTHH:mm:ssZ')"

    def optional_id(value):
        return f"@if({eq(value, 0)}, json('null'), int({value}))"

    def quote(external_text):
        return f"uriComponent(replace({external_text}, '''', ''''''))"

    # All item IDs are validated before any source request. Only the bound source is read.
    source_uri = (
        f"@concat(if({audit_mode}, {literal(audit + '/items(')}, {literal(reviews + '/items(')}), "
        f"string(int({source_id})), if({audit_mode}, ')?$select=Id,FileSystemObjectType', "
        "')?$select=Id,ManualReviewState'))"
    )
    source = body("Read_source")
    completed_review = eq(field(source, "ManualReviewState"), "'Abgeschlossen'")
    audit_file = eq(field(source, "FileSystemObjectType"), 0)
    verified_source = both(eq(field(source, "Id"), source_id), f"if({audit_mode}, {audit_file}, {completed_review})")
    # The query has a fixed field and a safely encoded OData string literal.
    request_lookup = (
        f"@concat({finding_list}, '/items?$select={ITEM_FIELDS}&$top=2"
        f"&$filter=GovernanceID%20eq%20%27', {quote(key)}, '%27')"
    )
    register = body("Read_list")
    due_format = eq(f"formatDateTime(parseDateTime({due}, 'en-US', 'yyyy-MM-dd'), 'yyyy-MM-dd')", due)
    known_action = f"contains(createArray('prepare','create','plan','start','close'), {action})"
    valid_revision = f"and(not(empty({expected})), not(equals({expected}, '*')), lessOrEquals(length({expected}), 180))"
    prefix = f"if({audit_mode}, '{SCOPE['audit'][1]}', '{SCOPE['review'][1]}')"
    create_input = both(eq(item, 0), identifier(source_id), f"startsWith({key}, {prefix})",
                        eq(f"length({key})", 36), f"greater(length({title}), 0)",
                        f"lessOrEquals(length({title}), 255)", f"greater(length({description}), 0)",
                        f"lessOrEquals(length({description}), 4000)")
    plan_input = both(f"contains({owner_claim}, '@')", f"lessOrEquals(length({owner_claim}), 254)",
                      f"not(contains({owner_claim}, ''''))", eq(f"length({due})", 10),
                      one_of(eq(new_measure, 0), identifier(new_measure)),
                      one_of(eq(new_evidence, 0), identifier(new_evidence)))
    close_input = both(f"greater(length({note}), 0)", f"lessOrEquals(length({note}), 2000)")

    def optional_lookup(previous, number, default_code, action_name, uri, valid):
        return condition(f"@and({ready()}, greater({number}, 0))", {
            "Pending_" + action_name: report(default_code),
            action_name: rest(uri, "Pending_" + action_name),
            "Confirm_" + action_name: condition(f"@{valid}", {"Allow_" + action_name: stage_ready()}, action_name)
        }, previous, outcomes=TRANSIENT)

    measure = body("Read_measure")
    measure_status = field(measure, "MeasureStatus")
    verified_measure = both(eq(field(measure, "Id"), measure_id), eq(field(measure, "IsActive"), "true"),
                            one_of(f"not({close_mode})", f"contains(createArray('{measure_labels['Effective']}', "
                                   f"'{measure_labels['Closed']}'), {measure_status})"))
    verified_proof = both(eq(field(proof, "Id"), evidence_id), eq(field(proof, "IsActive"), "true"),
                          eq(field(proof, "FileSystemObjectType"), 0), f"not(empty({verification_version}))")
    plan_fields = {"OwnerId": f"@{owner_id}", "FindingDueDate": f"@{native_midnight(due)}",
                   "FindingMeasureItemID": optional_id(new_measure), "FindingEvidenceItemID": optional_id(new_evidence)}
    create_fields = {"Title": f"@{title}", "Description": f"@{description}", "GovernanceID": f"@{key}",
                     "FindingSourceItemID": f"@int({source_id})", "FindingStatus": labels["Open"], "IsActive": True,
                     **plan_fields}
    close_fields = {"FindingStatus": labels["Closed"], "FindingClosedById": f"@{actor}", "FindingClosedAt": "@utcNow()",
                    "FindingEvidenceVersion": f"@{verification_version}", "FindingClosureNote": f"@{note}"}
    edit_entity = {"__metadata": {"type": f"@{row}?['__metadata']?['type']"}}
    creation = "first(outputs('Findings_with_key'))"
    new_matches = (
        eq(field(creation, "AuthorId"), actor),
        eq(field(creation, "Title"), title),
        eq(field(creation, "Description"), description),
        eq(field(creation, "FindingSourceItemID"), source_id),
        eq(field(creation, "OwnerId"), owner_id),
        eq(native_day(field(creation, "FindingDueDate")), due),
        eq(f"coalesce({field(creation, 'FindingMeasureItemID')}, 0)", new_measure),
        eq(f"coalesce({field(creation, 'FindingEvidenceItemID')}, 0)", new_evidence),
    )
    saved = body("Read_after_edit")
    payload = "outputs('Edit_payload')"
    immutable = ("Title", "Description", "GovernanceID", "AuthorId", "IsActive", "FindingSourceItemID")
    writable = ("OwnerId", "FindingStatus", "FindingMeasureItemID", "FindingEvidenceItemID", "FindingClosureNote",
                "FindingClosedById", "FindingEvidenceVersion")
    same_immutable = [eq(field(saved, name), field(row, name)) for name in immutable]
    expected_values = [eq(field(saved, name), f"if(contains({payload}, '{name}'), {field(payload, name)}, {field(row, name)})")
                       for name in writable]
    verified_date = eq(native_day(field(saved, "FindingDueDate")),
                       f"if({plan_mode}, {due}, {native_day(field(row, 'FindingDueDate'))})")
    closure_date_matches = (
        f"if({close_mode}, not(empty({field(saved, 'FindingClosedAt')})), "
        f"{eq(field(saved, 'FindingClosedAt'), field(row, 'FindingClosedAt'))})"
    )
    saved_revision = f"{saved}?['__metadata']?['etag']"
    version_changed = f"not({eq(field(saved, 'OData__UIVersionString'), field(row, 'OData__UIVersionString'))})"
    edit_matches = both(eq(field(saved, "Id"), item), eq(field(saved, "EditorId"), actor),
                        f"not({eq(saved_revision, revision)})", version_changed, verified_date,
                        closure_date_matches, *same_immutable, *expected_values)
    body_json = request("text_3", "'{}'")
    can_start = both(eq(action, "'start'"), eq(status, open_state))
    create_hits = "length(outputs('Findings_with_key'))"

    actions = {
        "Initialize_result": {"type": "InitializeVariable", "inputs": {"variables": [
            {"name": "result", "type": "object", "value": defaults},
            {"name": "payload", "type": "object", "value": {}}
        ]}, "runAfter": {}},
        "Parse_request": compose(f"@json({body_json})", "Initialize_result"),
        "Finding_list": compose(f"@if({audit_mode}, {literal(audit_findings)}, {literal(findings)})", "Parse_request"),
        "Finding_uri": compose(f"@concat({finding_list}, '/items(', string(int({item})), ')')", "Finding_list"),
        "Validate_request": condition(
            f"@and(contains(createArray('review','audit'), {scope}), {known_action}, "
            f"if({create_mode}, {create_input}, {identifier(item)}), "
            f"or({create_mode}, {prepare_mode}, {valid_revision}), "
            f"or(not(or({create_mode}, {plan_mode})), {plan_input}), or(not({close_mode}), {close_input}))",
            {"Request_valid": report("input_ok")}, "Finding_uri"),
        "Authorize_actor": condition(f"@{is_result('input_ok')}", {
            "Actor_unavailable": report("unavailable"),
            "Read_actor": rest("_api/web/currentuser?$select=Id", "Actor_unavailable"),
            "Verified_actor": condition(f"@greater({actor}, 0)", {"Actor_ready": report("authorized")}, "Read_actor"),
        }, "Validate_request", outcomes=TRANSIENT),
        "Authorize_finding": condition(f"@{is_result('authorized')}", {
            "Create_or_edit": condition(f"@{create_mode}", {
                "List_unavailable": report("denied"),
                "Read_list": rest(f"@concat({finding_list}, '?$select=ListItemEntityTypeFullName,EffectiveBasePermissions')", "List_unavailable"),
                "Can_create": condition(f"@{permission(register, 2)}", {
                    "Unverified_key": report("request_key_unavailable"),
                    "Read_key": rest(f"@concat({finding_list}, '/fields/getbyinternalnameortitle(%27GovernanceID%27)?$select=Indexed,EnforceUniqueValues')",
                                     "Unverified_key"),
                    "Unique_key": condition(f"@and({eq(field(body('Read_key'), 'Indexed'), 'true')}, "
                                            f"{eq(field(body('Read_key'), 'EnforceUniqueValues'), 'true')})",
                                            {"Create_ready": stage_ready()}, "Read_key"),
                }, "Read_list"),
            }, None, {
                "Item_unavailable": report("unavailable"),
                "Read_finding": rest(f"@concat({finding_uri}, '?$select={ITEM_FIELDS}')", "Item_unavailable"),
                "Prepare_or_edit": condition(f"@{prepare_mode}", {
                    "Prepared": report("ready_to_edit", itemid=f"@{item}", revision=f"@{revision}", canedit=f"@{can_edit}",
                                       nativeversion=f"@{clean(field(row, 'OData__UIVersionString'))}"),
                }, "Read_finding", {
                    "Check_native_version": condition(f"@{eq(revision, expected)}", {
                        "Native_edit_permission": condition(f"@{can_edit}", {
                            "Lifecycle_allows_action": condition(
                                f"@or({plan_mode}, {can_start}, "
                                f"and({close_mode}, {eq(status, in_progress)}, {eq(field(row, 'OwnerId'), actor)}, "
                                f"{identifier(measure_id)}, {identifier(evidence_id)}))",
                                {"Edit_ready": stage_ready()}, None, {"Invalid_transition": report("invalid_transition")}),
                        }, None, {"Cannot_edit": report("denied")}),
                    }, None, {"Stale_version": report("conflict")}),
                }),
            }),
        }, "Authorize_actor", outcomes=TRANSIENT),
        "Verify_source": condition(f"@and({ready()}, {create_mode})", {
            "Source_unavailable": report("source_unavailable"),
            "Read_source": rest(source_uri, "Source_unavailable"),
            "Source_verified": condition(f"@{verified_source}", {"Source_ready": stage_ready()}, "Read_source"),
        }, "Authorize_finding", outcomes=TRANSIENT),
        "Verify_plan": condition(f"@and({ready()}, or({create_mode}, {plan_mode}))", {
            "Invalid_date": report("invalid_date"),
            "Date_valid": condition(f"@{due_format}", {
                "Owner_unavailable": report("owner_unavailable"),
                "Read_owner": rest("@concat('_api/web/siteusers/getbyloginname(@login)?$select=Id,PrincipalType&@login=%27', "
                                   f"uriComponent(concat('i:0#.f|membership|', toLower({owner_claim}))), '%27')", "Owner_unavailable"),
                "Owner_verified": condition(f"@and(greater(coalesce({owner_id}, 0), 0), "
                                            f"{eq(field(assignee, 'PrincipalType'), 1)})",
                                            {"Plan_ready": stage_ready()}, "Read_owner"),
            }, "Invalid_date")
        }, "Verify_source", outcomes=TRANSIENT),
        "Verify_measure": optional_lookup("Verify_plan", measure_id, "measure_unavailable", "Read_measure",
                                          select_item(measures, measure_id, "Id,IsActive,MeasureStatus"), verified_measure),
        "Verify_evidence": optional_lookup("Verify_measure", evidence_id, "evidence_unavailable", "Read_evidence",
                                           select_item(evidence, evidence_id, "Id,IsActive,FileSystemObjectType,OData__UIVersionString"),
                                           verified_proof),
        "Save_new_finding": condition(f"@and({ready()}, {create_mode})", {
            "Uncertain_create": report("uncertain"),
            "Read_before_create": rest(request_lookup, "Uncertain_create"),
            "Only_create_if_absent": condition(f"@empty({body('Read_before_create')}?['results'])", {
                "Create_payload": compose({"__metadata": {"type": f"@{field(register, 'ListItemEntityTypeFullName')}"}, **create_fields}),
                "Create_finding": rest(f"@concat({finding_list}, '/items')", "Create_payload", data="Create_payload"),
            }, "Read_before_create"),
            "Read_after_create": rest(request_lookup, "Only_create_if_absent", outcomes=TRANSIENT),
            "Findings_with_key": compose(f"@{body('Read_after_create')}?['results']", "Read_after_create"),
            "Verify_create": condition(f"@{eq(create_hits, 1)}", {
                "Create_matches_request": condition(f"@{both(*new_matches)}", {
                    "New_finding_confirmed": report("saved", itemid="@first(outputs('Findings_with_key'))?['Id']"),
                }, None, {"Duplicate_request_conflict": report("request_conflict")}),
            }, "Findings_with_key"),
        }, "Verify_evidence", outcomes=TRANSIENT),
        "Build_edit": condition(f"@and({ready()}, not({create_mode}))", {
            "Plan_or_transition": condition(f"@{plan_mode}", {
                "Planning_fields": set_value("payload", {**edit_entity, **plan_fields}),
            }, None, {
                "Start_or_close": condition(f"@{close_mode}", {
                    "Closure_fields": set_value("payload", {**edit_entity, **close_fields}),
                }, None, {"Start_fields": set_value("payload", {**edit_entity, "FindingStatus": labels["InProgress"]})}),
            }),
        }, "Save_new_finding", outcomes=TRANSIENT),
        "Save_edit": condition(f"@and({ready()}, not(empty(variables('payload'))))", {
            "Uncertain_edit": report("uncertain"),
            "Edit_payload": compose("@variables('payload')", "Uncertain_edit"),
            "Merge_finding": rest(f"@{finding_uri}", "Edit_payload", data="Edit_payload", match=f"@{revision}"),
            "Handle_precondition": condition("@equals(outputs('Merge_finding')?['statusCode'], 412)",
                                            {"Concurrent_write": report("conflict")}, "Merge_finding", outcomes=["Failed"]),
            "Read_after_edit": rest(f"@concat({finding_uri}, '?$select={ITEM_FIELDS}')", "Merge_finding"),
            "Verify_edit": condition(f"@{edit_matches}",
                {"Edit_confirmed": report("saved", itemid=f"@{item}")}, "Read_after_edit"),
        }, "Build_edit", outcomes=TRANSIENT),
        "Respond": {"type": "Response", "kind": "PowerApp", "inputs": {"statusCode": 200,
                    "body": {name: f"@variables('result')?['{name}']" for name in schema},
                    "schema": {"type": "object", "properties": schema}}, "runAfter": after("Save_edit", TRANSIENT)},
    }
    inputs = {name: {"title": label, "type": "number" if name == "number" else "string",
                     "x-ms-dynamically-added": True, "x-ms-content-hint": "NUMBER" if name == "number" else "TEXT"}
              for name, label in (("text", "Findings-Bereich"), ("text_1", "Aktion"), ("number", "Finding-ID"),
                                  ("text_2", "Revision"), ("text_3", "Findings-Felder"))}
    definition = {"$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                  "contentVersion": "1.0.0.0", "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                                                             "$connections": {"defaultValue": {}, "type": "Object"}},
                  "triggers": {"manual": {"type": "Request", "kind": "PowerAppV2",
                               "inputs": {"schema": {"type": "object", "properties": inputs, "required": list(inputs)}},
                               "runtimeConfiguration": {"secureData": {"properties": ["outputs"]}}}},
                  "actions": actions, "outputs": {}}
    return {"properties": {"connectionReferences": {CONNECTOR: {"runtimeSource": "invoker", "api": {"name": CONNECTOR},
             "connection": {"connectionReferenceLogicalName": reference}}}, "definition": definition, "templateName": ""}, "schemaVersion": "1.0.0.0"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    flow = build_flow(**json.loads(args.config.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(flow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
