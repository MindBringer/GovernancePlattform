"""Build the invoker-bound BIA and exercise workflow from the BCM schema."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from build_control_write import body, identifier, permission
from build_evidence_upload import CONNECTOR, TRANSIENT, after, compose, condition
from build_finding_write import both, choices, clean, eq, field, literal, one_of

FIELDS = (
    "Id,Title,GovernanceID,Description,OwnerId,AuthorId,EditorId,IsActive,EffectiveBasePermissions,"
    "BiaStatus,BiaAssetItemID,BiaSystemItemID,BiaMtpdMinutes,BiaRtoMinutes,BiaRpoMinutes,"
    "BiaMinimumService,BiaAssessedAt,BiaAssessedById,BcmExerciseDate,BcmExerciseResult,"
    "BcmEvidenceItemID,BcmEvidenceVersion,OData__UIVersionString"
)


def build_flow(site, reference, processes_list, assets_list, systems_list, evidence_library, time_zone):
    url = urlsplit(site)
    if (url.scheme != "https" or not url.hostname or not url.hostname.endswith(".sharepoint.com")
            or url.netloc != url.hostname or not re.fullmatch(r"/sites/[A-Za-z0-9_-]+", url.path)
            or url.query or url.fragment):
        raise ValueError("Expected a SharePoint site URL")
    if not re.fullmatch(r"[A-Za-z0-9_]+", reference) or not re.fullmatch(r"[A-Za-z0-9 .()+-]{1,80}", time_zone):
        raise ValueError("Expected a SharePoint connection reference and the site time zone")
    ids = [str(UUID(value)) for value in (processes_list, assets_list, systems_list, evidence_library)]
    if len(set(ids)) != len(ids):
        raise ValueError("BCM lists and Evidence must be distinct")
    processes, assets, systems, evidence = (f"_api/web/lists(guid'{value}')" for value in ids)
    labels = choices("BusinessContinuity")

    def param(name, default):
        return f"coalesce(triggerBody()?['{name}'], {default})"

    action, supplied_revision = (param(name, "''") for name in ("text", "text_1"))
    item = param("number", 0)
    args = "outputs('Parse_request')"
    create, prepare, save, assess, exercise, capabilities = (eq(action, literal(name))
                                            for name in ("create", "prepare", "save", "assess", "exercise", "capabilities"))
    planning = one_of(create, save, assess)
    title, key, owner_mail, impact, minimum_service, day, result = (
        clean(field(args, name)) for name in ("title", "key", "owner", "impact", "minimumService", "day", "result")
    )
    numbers = {
        "BiaAssetItemID": ("asset", 1), "BiaSystemItemID": ("system", 1),
        "BiaMtpdMinutes": ("mtpd", 1), "BiaRtoMinutes": ("rto", 1), "BiaRpoMinutes": ("rpo", 0),
        "BcmEvidenceItemID": ("evidence", 1),
    }
    measured = {name: f"string(coalesce({field(args, key_name)}, ''))" for name, (key_name, _) in numbers.items()}

    def integer(name):
        value = measured[name]
        return f"int(if(isInt({value}), {value}, '-1'))"

    def valid_number(name):
        value = integer(name)
        return both(f"greaterOrEquals({value}, {numbers[name][1]})", f"lessOrEquals({value}, 2147483647)")

    def not_given(name):
        return f"empty({measured[name]})"

    def optional_number(name):
        return f"@if({not_given(name)}, json('null'), {integer(name)})"

    asset, system, proof_id = (integer(name) for name in ("BiaAssetItemID", "BiaSystemItemID", "BcmEvidenceItemID"))
    mtpd, rto = (integer(name) for name in ("BiaMtpdMinutes", "BiaRtoMinutes"))
    row, list_row, owner, proof = (body(name) for name in ("Read_process", "Read_list", "Read_owner", "Read_evidence"))
    actor = f"coalesce({field(body('Read_actor'), 'Id')}, 0)"
    owner_id = field(owner, "Id")
    etag = f"coalesce({row}?['__metadata']?['etag'], '')"
    read_uri = f"@concat(outputs('Process_uri'), '?$select={FIELDS},Owner/Name,Owner/Title&$expand=Owner')"
    canedit = both(eq(field(row, "IsActive"), "true"), permission(row, 4))
    draft, assessed = labels["Draft"], labels["Assessed"]
    proof_version = clean(field(proof, "OData__UIVersionString"))
    known_version = lambda revision: both(f"not(empty({revision}))", f"not({eq(revision, literal('*'))})",
                                         f"lessOrEquals(length({revision}), 180)")

    def get_item(path, ident, fields):
        return f"@concat({literal(path + '/items(')}, string(int({ident})), ')?$select={fields}')"

    def native_day(value):
        return f"convertTimeZone(coalesce({value}, '1900-01-01T12:00:00Z'), 'UTC', '{time_zone}', 'yyyy-MM-dd')"

    def rest(uri, previous, *, payload=None, match=None, outcomes=None):
        headers = {"Accept": "application/json;odata=verbose"}
        params = {"dataset": site, "parameters/method": "POST" if payload else "GET",
                  "parameters/uri": uri, "parameters/headers": headers}
        inputs = {"host": {"apiId": f"/providers/Microsoft.PowerApps/apis/{CONNECTOR}",
                           "connectionName": CONNECTOR, "operationId": "HttpRequest"},
                  "parameters": params, "authentication": "@parameters('$authentication')"}
        if payload:
            headers["Content-Type"] = "application/json;odata=verbose"
            params["parameters/body"] = f"@string(outputs('{payload}'))"
            inputs["retryPolicy"] = {"type": "none"}
        if match:
            headers.update({"X-HTTP-Method": "MERGE", "IF-MATCH": match})
        return {"type": "OpenApiConnection", "inputs": inputs, "runAfter": after(previous, outcomes),
                "runtimeConfiguration": {"secureData": {"properties": ["inputs", "outputs"]}}}

    defaults = {"status": "invalid", "itemid": 0, "revision": "", "canedit": False, "cancreate": False, "snapshot": ""}
    schema = {name: {"title": name, "type": {str: "string", int: "number", bool: "boolean"}[type(value)],
                     "x-ms-dynamically-added": True} for name, value in defaults.items()}

    def report(code, previous=None, **values):
        return {"type": "SetVariable", "inputs": {"name": "result", "value": {**defaults, "status": code, **values}},
                "runAfter": after(previous)}

    def ready():
        return eq("variables('result')?['status']", "'write_ready'")

    def verify_source(previous, cond, path, ident, name, constraints):
        lookup = body(name)
        return condition(f"@{both(ready(), cond)}", {
            "Pending_" + name: report("source_unavailable"),
            name: rest(get_item(path, ident, constraints[0]), "Pending_" + name),
            "Confirm_" + name: condition(f"@{both(eq(field(lookup, 'Id'), ident), *constraints[1])}",
                                        {"Verified_" + name: report("write_ready")}, name),
        }, previous, outcomes=TRANSIENT)

    planning_fields = {
        "Title": f"@{title}", "OwnerId": f"@{owner_id}", "Description": f"@{impact}",
        "BiaMinimumService": f"@{minimum_service}",
        "BiaStatus": f"@if({assess}, {literal(assessed)}, {literal(draft)})",
        "BiaAssessedAt": f"@if({assess}, formatDateTime(utcNow(), 'yyyy-MM-ddTHH:mm:ssZ'), json('null'))",
        "BiaAssessedById": f"@if({assess}, {actor}, json('null'))",
        **{name: optional_number(name) for name in numbers if name != "BcmEvidenceItemID"},
    }
    new_fields = {**planning_fields, "GovernanceID": f"@{key}", "IsActive": True}
    exercise_fields = {
        "BcmExerciseDate": f"@convertTimeZone(concat({day}, 'T00:00:00'), '{time_zone}', 'UTC', 'yyyy-MM-ddTHH:mm:ssZ')",
        "BcmExerciseResult": f"@{result}", "BcmEvidenceItemID": f"@{proof_id}", "BcmEvidenceVersion": f"@{proof_version}",
    }

    def bounded(value, length, required=False):
        limits = [f"lessOrEquals(length({value}), {length})"]
        return both(f"not(empty({value}))", *limits) if required else limits[0]

    plan = both(
        bounded(title, 255, True), bounded(owner_mail, 254, True), f"contains({owner_mail}, '@')",
        f"not(contains({owner_mail}, ''''))", bounded(impact, 4000), bounded(minimum_service, 4000),
        *(one_of(not_given(name), valid_number(name)) for name in planning_fields if name in numbers),
        one_of(not_given("BiaMtpdMinutes"), not_given("BiaRtoMinutes"), f"less({rto}, {mtpd})"),
        one_of(f"not({assess})", both(
            f"not(empty({impact}))", f"not(empty({minimum_service}))",
            *(valid_number(name) for name in planning_fields if name in numbers),
        )),
    )
    exercise_input = both(eq(f"length({day})", 10), bounded(result, 4000, True), valid_number("BcmEvidenceItemID"))
    # Power Automate string constants containing SharePoint's GUID literal need escaped apostrophes.
    lookup_key = (f"@concat({literal(processes + '/items?$select=' + FIELDS + '&$top=2&$filter=GovernanceID%20eq%20%27')}, "
                  f"uriComponent(replace({key}, '''', '''''')), '%27')")
    new_row = "first(outputs('Rows_with_key'))"
    written = body("Read_after_edit")
    payload = "outputs('Edit_payload')"

    def stored_value(record, name):
        value = field(record, name)
        return (
            f"coalesce({value}, '')" if name in {"Description", "BiaMinimumService", "BcmExerciseResult", "BcmEvidenceVersion"}
            else native_day(value) if name == "BcmExerciseDate"
            else f"ticks(coalesce({value}, '1900-01-01T00:00:00Z'))" if name == "BiaAssessedAt"
            else value
        )

    editable_snapshot = {
        "title": f"@{field(row, 'Title')}", "impact": f"@{clean(field(row, 'Description'))}",
        "owner": f"@last(split(coalesce({field(field(row, 'Owner'), 'Name')}, ''), '|'))",
        "ownerName": f"@{clean(field(field(row, 'Owner'), 'Title'))}",
        "minimumService": f"@{clean(field(row, 'BiaMinimumService'))}",
        "status": f"@{field(row, 'BiaStatus')}",
        **{name: f"@{field(row, name)}" for name in numbers if name != "BcmEvidenceItemID"},
    }
    before_payload = "outputs('Create_payload')"
    after_payload = lambda name: f"if(contains({payload}, '{name}'), {stored_value(payload, name)}, {stored_value(row, name)})"
    unchanged_on_create = [eq(stored_value(new_row, name), stored_value(before_payload, name)) for name in new_fields]
    write_columns = set(planning_fields) | set(exercise_fields)
    edit_checks = [eq(stored_value(written, name), after_payload(name)) for name in sorted(write_columns)]

    valid_create = both(create, eq(item, 0), eq(f"length({key})", 36), f"startsWith({key}, 'BIA-')")
    valid_edit = both(known_version(supplied_revision), one_of(save, assess, exercise))
    valid_request = both(one_of(both(capabilities, eq(item, 0)), valid_create, both(identifier(item), one_of(prepare, valid_edit))),
                         one_of(f"not({planning})", plan), one_of(f"not({exercise})", exercise_input))
    authorized = both(eq("variables('result')?['status']", "'valid'"), identifier(actor))
    may_exercise = one_of(f"not({exercise})", both(eq(field(row, "BiaStatus"), literal(assessed)),
                                                  eq(field(row, "OwnerId"), actor)))
    formatted_day = f"formatDateTime(parseDateTime({day}, 'en-US', 'yyyy-MM-dd'), 'yyyy-MM-dd')"
    today = native_day("utcNow()")
    day_is_current_or_past = f"lessOrEquals(ticks(concat({day}, 'T00:00:00Z')), ticks(concat({today}, 'T00:00:00Z')))"
    new_etag = f"{written}?['__metadata']?['etag']"
    verified_edit = both(
        eq(field(written, "Id"), item), eq(field(written, "EditorId"), actor),
        f"not({eq(new_etag, etag)})",
        f"not({eq(field(written, 'OData__UIVersionString'), field(row, 'OData__UIVersionString'))})",
        *(eq(field(written, name), field(row, name)) for name in ("GovernanceID", "AuthorId", "IsActive")),
        *edit_checks,
    )

    actions = {
        "Initialize_result": {"type": "InitializeVariable", "inputs": {"variables": [
            {"name": "result", "type": "object", "value": defaults}]}, "runAfter": {}},
        "Parse_request": compose(f"@json({param('text_2', literal('{}'))})", "Initialize_result"),
        "Process_uri": compose(f"@concat({literal(processes + '/items(')}, string(int({item})), ')')", "Parse_request"),
        "Validate_input": condition(f"@{valid_request}", {"Input_valid": report("valid")}, "Process_uri"),
        "Read_actor": rest("_api/web/currentuser?$select=Id", "Validate_input"),
        "Read_capabilities": condition(f"@{both(authorized, capabilities)}", {
            "Rights_unavailable": report("denied"),
            "Read_process_list_rights": rest(f"{processes}?$select=EffectiveBasePermissions", "Rights_unavailable"),
            "Rights": report("capabilities", "Read_process_list_rights",
                             cancreate=f"@{permission(body('Read_process_list_rights'), 2)}",
                             canedit=f"@{permission(body('Read_process_list_rights'), 4)}"),
        }, "Read_actor", outcomes=TRANSIENT),
        "Authorize": condition(f"@{both(authorized, f'not({capabilities})')}", {
            "Validate_create_or_item": condition(f"@{create}", {
                "List_unavailable": report("denied"),
                "Read_list": rest(f"{processes}?$select=ListItemEntityTypeFullName,EffectiveBasePermissions", "List_unavailable"),
                "Can_create": condition(f"@{permission(list_row, 2)}", {
                    "Key_unverified": report("request_key_unavailable"),
                    "Read_key": rest(f"{processes}/fields/getbyinternalnameortitle('GovernanceID')?$select=Indexed,EnforceUniqueValues", "Key_unverified"),
                    "Unique_key": condition(f"@{both(eq(field(body('Read_key'), 'Indexed'), 'true'), eq(field(body('Read_key'), 'EnforceUniqueValues'), 'true'))}",
                                            {"Create_ready": report("write_ready")}, "Read_key"),
                }, "Read_list"),
            }, None, {
                "Item_unavailable": report("unavailable"),
                "Read_process": rest(read_uri, "Item_unavailable"),
                "Item_matches": condition(f"@{both(eq(field(row, 'Id'), item), known_version(etag))}", {
                    "Prepare_or_edit": condition(f"@{prepare}", {
                        "Prepared_snapshot": compose(editable_snapshot),
                        "Prepared": report("ready_to_edit", "Prepared_snapshot", itemid=f"@{item}", revision=f"@{etag}",
                                           canedit=f"@{canedit}", snapshot="@string(outputs('Prepared_snapshot'))"),
                    }, None, {
                        "Item_denied": report("denied"),
                        "Can_edit": condition(f"@{canedit}", {
                            "Revision_matches": condition(f"@{eq(etag, supplied_revision)}", {
                                "Exercise_valid": condition(f"@{may_exercise}",
                                    {"Edit_ready": report("write_ready")}, None, {"Exercise_not_allowed": report("exercise_not_allowed")}),
                            }, None, {"Stale_version": report("conflict")}),
                        }, "Item_denied"),
                    }),
                }, "Read_process"),
            }),
        }, "Read_capabilities", outcomes=TRANSIENT),
        "Verify_owner": condition(f"@{both(ready(), planning)}", {
            "Owner_unavailable": report("owner_unavailable"),
            "Read_owner": rest("@concat('_api/web/siteusers/getbyloginname(@login)?$select=Id,PrincipalType&@login=%27', "
                               f"uriComponent(concat('i:0#.f|membership|', toLower({owner_mail}))), '%27')", "Owner_unavailable"),
            "Owner_exists": condition(f"@{both(identifier(f'coalesce({owner_id}, 0)'), eq(field(owner, 'PrincipalType'), 1))}", {
                "Can_assess": condition(f"@{one_of(f'not({assess})', both(eq(owner_id, actor), eq(field(row, 'OwnerId'), actor)))}",
                    {"Owner_verified": report("write_ready")}, None, {"Assessment_denied": report("assessment_denied")}),
            }, "Read_owner"),
        }, "Authorize", outcomes=TRANSIENT),
        "Verify_asset": verify_source("Verify_owner", both(planning, f"greater({asset}, 0)"), assets, asset,
                                        "Read_asset", ("Id,IsActive,BusinessCritical",
                                         [eq(field(body("Read_asset"), col), "true") for col in ("IsActive", "BusinessCritical")])),
        "Verify_system": verify_source("Verify_asset", both(planning, f"greater({system}, 0)"), systems, system,
                                          "Read_system", ("Id,IsActive", [eq(field(body("Read_system"), "IsActive"), "true")])),
        "Verify_exercise_day": condition(f"@{both(ready(), exercise)}", {
            "Invalid_day": report("invalid_exercise_date"),
            "Date_exists": condition(f"@{both(eq(formatted_day, day), day_is_current_or_past)}",
                                     {"Exercise_day_verified": report("write_ready")}, "Invalid_day"),
        }, "Verify_system", outcomes=TRANSIENT),
        "Verify_evidence": verify_source("Verify_exercise_day", exercise, evidence, proof_id,
                                           "Read_evidence", ("Id,IsActive,FileSystemObjectType,OData__UIVersionString",
                                            [eq(field(proof, "IsActive"), "true"), eq(field(proof, "FileSystemObjectType"), 0),
                                             f"not(empty({proof_version}))"])),
        "Save_new_process": condition(f"@{both(ready(), create)}", {
            "Uncertain_create": report("uncertain"),
            "Create_payload": compose({"__metadata": {"type": f"@{field(list_row, 'ListItemEntityTypeFullName')}"}, **new_fields}, "Uncertain_create"),
            "Read_before_create": rest(lookup_key, "Create_payload"),
            "Only_create_if_absent": condition(f"@empty({field(body('Read_before_create'), 'results')})", {
                "Create_process": rest(processes + "/items", None, payload="Create_payload"),
            }, "Read_before_create"),
            "Read_after_create": rest(lookup_key, "Only_create_if_absent", outcomes=TRANSIENT),
            "Rows_with_key": compose(f"@{field(body('Read_after_create'), 'results')}", "Read_after_create"),
            "One_created_process": condition("@equals(length(outputs('Rows_with_key')), 1)", {
                "Created_matches_request": condition(f"@{both(eq(field(new_row, 'AuthorId'), actor), *unchanged_on_create)}",
                    {"Created": report("saved", itemid=f"@{field(new_row, 'Id')}")}, None,
                    {"Key_conflict": report("request_conflict")}),
            }, "Rows_with_key"),
        }, "Verify_evidence", outcomes=TRANSIENT),
        "Save_existing_process": condition(f"@{both(ready(), f'not({create})')}", {
            "Uncertain_edit": report("uncertain"),
            "Exercise_or_plan": condition(f"@{exercise}", {
                "Exercise_payload": compose({"__metadata": {"type": f"@{row}?['__metadata']?['type']"}, **exercise_fields}),
            }, "Uncertain_edit", {
                "Planning_payload": compose({"__metadata": {"type": f"@{row}?['__metadata']?['type']"}, **planning_fields}),
            }),
            "Edit_payload": compose(f"@if({exercise}, outputs('Exercise_payload'), outputs('Planning_payload'))", "Exercise_or_plan"),
            "Merge_process": rest("@outputs('Process_uri')", "Edit_payload", payload="Edit_payload", match=f"@{etag}"),
            "Precondition_failed": condition("@equals(outputs('Merge_process')?['statusCode'], 412)",
                                             {"Conflict": report("conflict")}, "Merge_process", outcomes=["Failed"]),
            "Read_after_edit": rest(read_uri, "Merge_process"),
            "Verify_edit": condition(f"@{verified_edit}",
                                     {"Edit_confirmed": report("saved", itemid=f"@{item}")}, "Read_after_edit"),
        }, "Save_new_process", outcomes=TRANSIENT),
        "Respond": {"type": "Response", "kind": "PowerApp", "inputs": {"statusCode": 200,
                    "body": {name: f"@variables('result')?['{name}']" for name in schema},
                    "schema": {"type": "object", "properties": schema}}, "runAfter": after("Save_existing_process", TRANSIENT)},
    }
    inputs = {name: {"type": kind, "title": label, "x-ms-dynamically-added": True,
                     "x-ms-content-hint": "NUMBER" if kind == "number" else "TEXT"}
              for name, kind, label in (("text", "string", "Aktion"), ("number", "number", "Prozess-ID"),
                                         ("text_1", "string", "Revision"), ("text_2", "string", "BIA-Felder"))}
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
