"""Build the invoker-bound flow for Measure planning, links, and lifecycle."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from build_control_write import LINK_FIELDS, body, identifier, permission
from build_evidence_upload import CONNECTOR, TRANSIENT, after, compose, condition

ARCHITECTURE = Path(__file__).resolve().parents[2] / "architecture"
FIELDS = ("Id,OwnerId,Owner/Name,DueDate,MeasureStatus,IsActive,EditorId,EffectiveBasePermissions,"
          "EffectivenessValidationDate,EffectivenessValidationResult,OData__UIVersionString")


def build_flow(site, reference, measures_list, controls_list, evidence_list, relations_list, time_zone):
    parts = urlsplit(site)
    if (parts.scheme != "https" or not parts.hostname or not parts.hostname.endswith(".sharepoint.com")
            or parts.netloc != parts.hostname or not re.fullmatch(r"/sites/[A-Za-z0-9_-]+", parts.path)
            or parts.query or parts.fragment):
        raise ValueError("Expected a SharePoint site URL")
    if not re.fullmatch(r"[A-Za-z0-9_]+", reference) or not re.fullmatch(r"[A-Za-z0-9 .()+-]{1,80}", time_zone):
        raise ValueError("Expected the native SharePoint connection reference and site time zone")
    ids = [str(UUID(value)) for value in (measures_list, controls_list, evidence_list, relations_list)]
    if len(set(ids)) != 4:
        raise ValueError("Four distinct SharePoint lists are required")
    measures, controls, evidence, relations = (f"_api/web/lists(guid'{value}')" for value in ids)

    models = json.loads((ARCHITECTURE / "status-models.yaml").read_text(encoding="utf-8"))["statusModels"]
    states = next(row["states"] for row in models if row["key"] == "Measure")
    labels = {key: label for key, label, *_ in states}
    choices = json.loads((ARCHITECTURE / "choices.yaml").read_text(encoding="utf-8"))["choiceSets"]
    assert labels == {key: label for key, label, _ in next(row["values"] for row in choices if row["key"] == "MeasureStatus")}
    relations_model = json.loads((ARCHITECTURE / "relations.yaml").read_text(encoding="utf-8"))["relationTypes"]
    control_key, evidence_key = "ControlImplementedByMeasure", "EvidenceSupportsObject"
    for key, source, target in ((control_key, "Control", "Measure"), (evidence_key, "Evidence", "*")):
        relation = next(row for row in relations_model if row["key"] == key)
        assert (relation["source"], relation["target"], relation["directional"], relation["multiple"]) == (source, target, True, True)

    def param(name, fallback):
        return f"coalesce(triggerBody()?['{name}'], {fallback})"

    def field(record, name):
        return f"{record}?['{name}']"

    def safe_etag(tag):
        return f"and(not(empty({tag})), not(equals({tag}, '*')), lessOrEquals(length({tag}), 180))"

    def day(value):
        return f"convertTimeZone(coalesce({value}, '1900-01-01T12:00:00Z'), 'UTC', '{time_zone}', 'yyyy-MM-dd')"

    def midnight(value):
        return f"convertTimeZone(concat({value}, 'T00:00:00'), '{time_zone}', 'UTC', 'yyyy-MM-ddTHH:mm:ssZ')"

    def rest(uri, previous=None, *, payload=None, match=None, outcomes=None):
        headers = {"Accept": "application/json;odata=verbose"}
        parameters = {"dataset": site, "parameters/method": "POST" if payload else "GET",
                      "parameters/uri": uri, "parameters/headers": headers}
        inputs = {"host": {"apiId": f"/providers/Microsoft.PowerApps/apis/{CONNECTOR}",
                           "connectionName": CONNECTOR, "operationId": "HttpRequest"},
                  "parameters": parameters, "authentication": "@parameters('$authentication')"}
        if payload:
            headers["Content-Type"] = "application/json;odata=verbose"
            parameters["parameters/body"] = f"@string(outputs('{payload}'))"
            inputs["retryPolicy"] = {"type": "none"}
        if match:
            headers.update({"X-HTTP-Method": "MERGE", "IF-MATCH": match})
        return {"type": "OpenApiConnection", "inputs": inputs, "runAfter": after(previous, outcomes),
                "runtimeConfiguration": {"secureData": {"properties": ["inputs", "outputs"]}}}

    defaults = {"status": "invalid", "itemid": 0, "revision": "", "nativeversion": "", "measurestatus": "",
                "ownerclaim": "", "dueday": "", "canedit": False, "relationid": 0}
    schema = {name: {"title": name, "type": {str: "string", int: "number", bool: "boolean"}[type(value)],
                     "x-ms-dynamically-added": True} for name, value in defaults.items()}

    def report(status, previous=None, **values):
        return {"type": "SetVariable", "inputs": {"name": "result", "value": {**defaults, "status": status, **values}},
                "runAfter": after(previous)}

    def prepare_merge(fields, previous=None):
        return {"type": "SetVariable", "inputs": {"name": "payload", "value": {**item_type, **fields}},
                "runAfter": after(previous)}

    action, expected, argument, detail = (param(key, "''") for key in ("text", "text_1", "text_2", "text_3"))
    measure_id, source_id = (param(key, 0) for key in ("number", "number_1"))
    row, saved = body("Read_measure"), body("Read_measure_write")
    item_id, source_item_id = f"int({measure_id})", f"int({source_id})"
    actor = f"int(coalesce({body('Read_actor')}?['Id'], 0))"
    tag = f"coalesce({row}?['__metadata']?['etag'], '')"
    version = f"coalesce({field(row, 'OData__UIVersionString')}, '')"
    status = f"coalesce({field(row, 'MeasureStatus')}, '')"
    item_type = {"__metadata": {"type": f"@{row}?['__metadata']?['type']"}}
    can_edit = f"and(equals({field(row, 'IsActive')}, true), {permission(row, 4)}, not(equals({status}, '{labels['Closed']}')))"
    planning = f"not(equals({status}, '{labels['Effective']}'))"
    owner = body("Read_owner")
    planned_owner = f"int(coalesce({field(owner, 'Id')}, 0))"
    request_fields = f"and(contains({argument}, '@'), not(contains({argument}, '''')), lessOrEquals(length({argument}), 254), equals(length({detail}), 10))"
    date_format = f"equals(formatDateTime(parseDateTime({detail}, 'en-US', 'yyyy-MM-dd'), 'yyyy-MM-dd'), {detail})"

    plan = {
        "Invalid_plan": report("invalid_plan"),
        "Parse_plan": condition(f"@and({planning}, {request_fields})", {
            "Plan_date_valid": condition(f"@{date_format}", {
                "Missing_owner": report("owner_unavailable"),
                "Read_owner": rest(
                    "@concat('_api/web/siteusers/getbyloginname(@login)?$select=Id,PrincipalType&@login=%27', "
                    f"uriComponent(concat('i:0#.f|membership|', toLower({argument}))), '%27')", "Missing_owner"),
                "Plan_owner_valid": condition(f"@and(greater({planned_owner}, 0), equals({field(owner, 'PrincipalType')}, 1))", {
                    "Same_plan": condition(
                        f"@and(equals({field(row, 'OwnerId')}, {planned_owner}), not(empty({field(row, 'DueDate')})), "
                        f"equals({day(field(row, 'DueDate'))}, {detail}))",
                        {"Plan_already_saved": report("unchanged", itemid=f"@{item_id}")}, None,
                        {"Plan_payload": prepare_merge({"OwnerId": f"@{planned_owner}", "DueDate": f"@{midnight(detail)}"})}),
                }, "Read_owner"),
            }, None),
        }, "Invalid_plan"),
    }

    source_type = "outputs('Link_source_type')"
    relation_type = "outputs('Link_relation_type')"
    key = "outputs('Link_key')"
    control_mode = f"equals({action}, 'control')"
    link_rows = f"{body('Confirm_link')}?['results']"
    relation = f"first({link_rows})"
    edge_expressions = {"RelationID": key, "RelationKey": key, "RelationTypeKey": relation_type,
                        "SourceObjectTypeKey": source_type, "SourceItemID": source_item_id, "TargetItemID": item_id}
    edges = {**{name: f"@{value}" for name, value in edge_expressions.items()}, "TargetObjectTypeKey": "Measure", "IsActive": True}
    relation_matches = [f"equals({field(relation, name)}, {value})" for name, value in
                        {**edge_expressions, "TargetObjectTypeKey": "'Measure'", "IsActive": "true"}.items()]
    relation_create = {
        "Link_pending": report("unverified"),
        "Link_source_type": compose(f"@if({control_mode}, 'Control', 'Evidence')", "Link_pending"),
        "Link_relation_type": compose(f"@if({control_mode}, '{control_key}', '{evidence_key}')", "Link_source_type"),
        "Link_key": compose(f"@concat({relation_type}, ':', {source_type}, ':', string({source_item_id}), ':Measure:', string({item_id}))",
                            "Link_relation_type"),
        "Link_query": compose(f"@concat(outputs('Relation_items'), '?$select={LINK_FIELDS}&$top=2&$filter=RelationKey%20eq%20%27', "
                              f"uriComponent({key}), '%27')", "Link_key"),
        "Read_existing_link": rest("@outputs('Link_query')", "Link_query"),
        "Insert_if_missing": condition(f"@empty({body('Read_existing_link')}?['results'])", {
            "Link_payload": compose({"__metadata": {"type": f"@{body('Read_link_list')}?['ListItemEntityTypeFullName']"},
                                      "Title": f"@{key}", **edges, "CreatedByApp": True}),
            "Write_link": rest(f"{relations}/items", "Link_payload", payload="Link_payload"),
        }, "Read_existing_link"),
        "Confirm_link": rest("@outputs('Link_query')", "Insert_if_missing", outcomes=TRANSIENT),
        "Unique_link": condition(f"@equals(length({link_rows}), 1)", {
            "Exact_link": condition(f"@and(greater({field(relation, 'Id')}, 0), {', '.join(relation_matches)})",
                                    {"Link_saved": report("linked", itemid=f"@{item_id}", relationid=f"@int({field(relation, 'Id')})")},
                                    None, {"Link_disagrees": report("relation_conflict")}),
        }, "Confirm_link", {"Duplicate_link": condition(f"@greater(length({link_rows}), 1)",
                                                         {"Link_duplicate": report("relation_conflict")}, None)}),
    }
    source = body("Read_link_source")
    link = {
        "Link_unavailable": report("source_unavailable"),
        "Control_items": compose(f"{controls}/items(", "Link_unavailable"),
        "Evidence_items": compose(f"{evidence}/items(", "Control_items"),
        "Read_link_source": rest(f"@concat(if({control_mode}, outputs('Control_items'), outputs('Evidence_items')), "
                                 f"string({source_item_id}), if({control_mode}, ')?$select=Id,IsActive', ')?$select=Id,FileSystemObjectType'))",
                                 "Evidence_items"),
        "Verify_link_source": condition(f"@and(equals({field(source, 'Id')}, {source_item_id}), "
                                        f"if({control_mode}, equals({field(source, 'IsActive')}, true), "
                                        f"equals({field(source, 'FileSystemObjectType')}, 0)))", {
            "Link_permission_missing": report("blocked"),
            "Read_link_list": rest(f"{relations}?$select=EffectiveBasePermissions,ListItemEntityTypeFullName", "Link_permission_missing"),
            "Allow_link_create": condition(f"@{permission(body('Read_link_list'), 2)}", {
                "Link_contract_missing": report("configuration"),
                "Read_link_key": rest(f"{relations}/fields/getbyinternalnameortitle('RelationKey')?$select=Indexed,EnforceUniqueValues",
                                      "Link_contract_missing"),
                "Unique_link_key": condition(f"@and(equals({body('Read_link_key')}?['Indexed'], true), "
                                             f"equals({body('Read_link_key')}?['EnforceUniqueValues'], true))", relation_create, "Read_link_key"),
            }, "Read_link_list"),
        }, "Read_link_source"),
    }

    target_filter = (f"TargetItemID%20eq%20', string({item_id}), '%20and%20TargetObjectTypeKey%20eq%20%27Measure%27"
                     "%20and%20IsActive%20eq%201")
    transition = "or(" + ", ".join(f"and(equals({status}, '{label}'), equals({argument}, '{labels[target]}'))"
                                    for _, label, _, _, allowed in states for target in allowed) + ")"
    ready = f"equals({argument}, '{labels['Effective']}')"
    closed = f"equals({argument}, '{labels['Closed']}')"
    transition_payload = {"MeasureStatus": f"@{argument}"}
    validation_date = midnight("outputs('Today')")
    proof = body("Read_proof")
    control_rows = f"{body('Read_control_links')}?['results']"
    advance = {
        "Transition_blocked": report("blocked"),
        "Valid_transition": condition(f"@and({transition}, greater(coalesce({field(row, 'OwnerId')}, 0), 0), "
                                      f"not(empty({field(row, 'DueDate')})), if({closed}, "
                                      f"and(not(empty({field(row, 'EffectivenessValidationDate')})), "
                                      f"not(empty(trim(coalesce({field(row, 'EffectivenessValidationResult')}, ''))))), true))", {
            "Control_required": report("control_required"),
            "Read_control_links": rest(f"@concat(outputs('Relation_items'), '?$select=Id&$top=1&$filter={target_filter}"
                                       f"%20and%20RelationTypeKey%20eq%20%27{control_key}%27"
                                       "%20and%20SourceObjectTypeKey%20eq%20%27Control%27')", "Control_required"),
            "Control_connected": condition(f"@not(empty({control_rows}))", {
                "Proof_required_or_status": condition(f"@{ready}", {
                    "Proof_required": report("proof_required"),
                    "Review_input_valid": condition(f"@and({identifier(source_id)}, not(empty(trim({detail}))), lessOrEquals(length({detail}), 2000))", {
                        "Read_proof_link": rest(f"@concat(outputs('Relation_items'), '?$select=Id&$top=2&$filter={target_filter}"
                                                f"%20and%20RelationTypeKey%20eq%20%27{evidence_key}%27"
                                                "%20and%20SourceObjectTypeKey%20eq%20%27Evidence%27%20and%20SourceItemID%20eq%20', "
                                                f"string({source_item_id}))"),
                        "Proof_connected": condition(f"@equals(length({body('Read_proof_link')}?['results']), 1)", {
                            "Proof_items": compose(f"{evidence}/items("),
                            "Read_proof": rest(f"@concat(outputs('Proof_items'), string({source_item_id}), ')?$select=Id,FileSystemObjectType')", "Proof_items"),
                            "Proof_is_file": condition(f"@and(equals({field(proof, 'Id')}, {source_item_id}), "
                                                       f"equals({field(proof, 'FileSystemObjectType')}, 0))", {
                                "Effectiveness_payload": prepare_merge({**transition_payload,
                                    "EffectivenessValidationDate": f"@{validation_date}",
                                    "EffectivenessValidationResult": f"@trim({detail})"}),
                            }, "Read_proof"),
                        }, "Read_proof_link"),
                    }, "Proof_required"),
                }, None, {"Status_payload": prepare_merge(transition_payload)}),
            }, "Read_control_links"),
        }, "Transition_blocked"),
    }

    verified_fields = ("MeasureStatus", "OwnerId", "DueDate", "EffectivenessValidationDate", "EffectivenessValidationResult", "IsActive")

    def expected_field(name):
        payload = "outputs('Measure_payload')"
        if name in {"DueDate", "EffectivenessValidationDate"}:
            return (f"if(contains({payload}, '{name}'), "
                    f"equals({day(field(saved, name))}, {day(field(payload, name))}), equals({field(saved, name)}, {field(row, name)}))")
        return f"equals({field(saved, name)}, if(contains({payload}, '{name}'), {field(payload, name)}, {field(row, name)}))"

    def initialize(name, value):
        return {"type": "InitializeVariable", "inputs": {"variables": [{"name": name, "type": "object", "value": value}]}, "runAfter": {}}

    actions = {
        "Initialize_result": initialize("result", defaults),
        "Initialize_payload": {**initialize("payload", {}), "runAfter": after("Initialize_result")},
        "Validate_input": condition(f"@and({identifier(measure_id)}, contains(createArray('prepare','plan','advance','control','evidence'), {action}))", {
            "Measure_unavailable": report("unavailable"),
            "Measure_items": compose(f"{measures}/items(", "Measure_unavailable"),
            "Measure_uri": compose(f"@concat(outputs('Measure_items'), string({item_id}), ')')", "Measure_items"),
            "Measure_select": compose(f"@concat(outputs('Measure_uri'), '?$select={FIELDS}&$expand=Owner')", "Measure_uri"),
            "Relation_items": compose(f"{relations}/items", "Measure_select"),
            "Read_actor": rest("_api/web/currentuser?$select=Id", "Relation_items"),
            "Read_measure": rest("@outputs('Measure_select')", "Read_actor"),
        }, "Initialize_payload"),
        "Today": compose(f"@{day('utcNow()')}", "Validate_input"),
        "Authorize": condition(f"@and(equals({field(row, 'Id')}, {item_id}), greater({actor}, 0), {safe_etag(tag)}, not(empty({version})))", {
            "Prepare_or_write": condition(f"@equals({action}, 'prepare')", {
                "Measure_ready": report("ready", itemid=f"@{item_id}", revision=f"@{tag}", nativeversion=f"@{version}",
                                        measurestatus=f"@{status}", ownerclaim=f"@coalesce({row}?['Owner']?['Name'], '')",
                                        dueday=f"@if(empty({field(row, 'DueDate')}), '', {day(field(row, 'DueDate'))})",
                                        canedit=f"@{can_edit}"),
            }, None, {
                "Measure_blocked": report("blocked"),
                "Allow_measure_write": condition(f"@{can_edit}", {
                    "Require_revision": condition(f"@equals({tag}, {expected})", {
                        "Authorize_request": report("authorized"),
                    }, None, {"Revision_conflict": report("conflict")}),
                }, "Measure_blocked"),
            }),
        }, "Today"),
        "Dispatch_plan": condition(f"@and(equals(variables('result')?['status'], 'authorized'), equals({action}, 'plan'))", plan, "Authorize"),
        "Dispatch_advance": condition(f"@and(equals(variables('result')?['status'], 'authorized'), equals({action}, 'advance'))",
                                      advance, "Dispatch_plan", outcomes=TRANSIENT),
        "Dispatch_link": condition(f"@and(equals(variables('result')?['status'], 'authorized'), "
                                   f"contains(createArray('control','evidence'), {action}), {identifier(source_id)}, {planning})",
                                   link, "Dispatch_advance", outcomes=TRANSIENT),
        "Persist_measure": condition("@not(empty(variables('payload')))", {
            "Write_unverified": report("unverified"),
            "Measure_payload": compose("@variables('payload')", "Write_unverified"),
            "Write_measure": rest("@outputs('Measure_uri')", "Measure_payload", payload="Measure_payload", match=f"@{expected}"),
            "Write_conflict": condition("@equals(coalesce(outputs('Write_measure')?['statusCode'], 0), 412)",
                                        {"Concurrent_change": report("conflict")}, "Write_measure", outcomes=["Failed"]),
            "Read_measure_write": rest("@outputs('Measure_select')", "Write_measure"),
            "Confirm_measure": condition(f"@and(equals({field(saved, 'Id')}, {item_id}), equals({field(saved, 'EditorId')}, {actor}), "
                                         f"not(equals({saved}?['__metadata']?['etag'], {tag})), "
                                         f"not(equals({field(saved, 'OData__UIVersionString')}, {version})), "
                                         + ", ".join(map(expected_field, verified_fields)) + ")",
                                         {"Measure_saved": report("saved", itemid=f"@{item_id}")}, "Read_measure_write"),
        }, "Dispatch_link", outcomes=TRANSIENT),
        "Respond": {"type": "Response", "kind": "PowerApp", "inputs": {"statusCode": 200,
                    "body": {name: f"@variables('result')?['{name}']" for name in schema},
                    "schema": {"type": "object", "properties": schema}}, "runAfter": after("Persist_measure", TRANSIENT)},
    }
    fields = {key: {"title": title, "type": "number" if key.startswith("number") else "string",
                    "x-ms-dynamically-added": True, "x-ms-content-hint": "NUMBER" if key.startswith("number") else "TEXT"}
              for key, title in (("number", "Maßnahmen-ID"), ("text", "Aktion"), ("text_1", "Revision"), ("number_1", "Quell-ID"),
                                 ("text_2", "Verantwortliche Person oder Zielstatus"), ("text_3", "Frist oder Prüfergebnis"))}
    definition = {"$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                  "contentVersion": "1.0.0.0", "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                                                             "$connections": {"defaultValue": {}, "type": "Object"}},
                  "triggers": {"manual": {"type": "Request", "kind": "PowerAppV2", "inputs": {"schema": {"type": "object",
                               "properties": fields, "required": list(fields)}}}}, "actions": actions, "outputs": {}}
    return {"properties": {"connectionReferences": {CONNECTOR: {"runtimeSource": "invoker", "api": {"name": CONNECTOR},
             "connection": {"connectionReferenceLogicalName": reference}}}, "definition": definition, "templateName": ""}, "schemaVersion": "1.0.0.0"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    flow = build_flow(**json.loads(args.config.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(flow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
