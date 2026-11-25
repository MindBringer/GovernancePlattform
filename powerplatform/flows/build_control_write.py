"""Build the invoker-bound workflow for reassignment and linking of Controls."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from build_evidence_upload import CONNECTOR, TRANSIENT, after, compose, condition

MODEL = Path(__file__).resolve().parents[2] / "architecture/relations.yaml"
CONTROL_FIELDS = "Id,OwnerId,Owner/Name,EditorId,IsActive,EffectiveBasePermissions"
LINK_FIELDS = "Id,RelationID,RelationKey,RelationTypeKey,SourceObjectTypeKey,SourceItemID,TargetObjectTypeKey,TargetItemID,IsActive"


def body(action):
    return f"body('{action}')?['d']"


def permission(row, bit):
    return f"equals(mod(div(int(coalesce({row}?['EffectiveBasePermissions']?['Low'], '0')), {bit}), 2), 1)"


def identifier(value):
    return f"and(greater({value}, 0), lessOrEquals({value}, 2147483647), equals({value}, int({value})))"


def build_flow(site, reference, controls_list, risks_list, evidence_list, relations_list):
    parts = urlsplit(site)
    if (parts.scheme != "https" or not parts.hostname or not parts.hostname.endswith(".sharepoint.com")
            or parts.netloc != parts.hostname or not re.fullmatch(r"/sites/[A-Za-z0-9_-]+", parts.path)
            or parts.query or parts.fragment):
        raise ValueError("Expected a SharePoint site URL")
    if not re.fullmatch(r"[A-Za-z0-9_]+", reference):
        raise ValueError("Expected a Dataverse connection reference logical name")
    lists = [str(UUID(value)) for value in (controls_list, risks_list, evidence_list, relations_list)]
    if len(set(lists)) != 4:
        raise ValueError("Controls, Risks, Evidence and GovernanceRelations must be distinct lists")
    controls, risks, evidence, relations = (f"_api/web/lists(guid'{value}')" for value in lists)

    relation_model = {row["key"]: row for row in json.loads(MODEL.read_text(encoding="utf-8"))["relationTypes"]}
    risk_key, evidence_key = "RiskMitigatedByControl", "EvidenceSupportsObject"
    for key, source, target in ((risk_key, "Risk", "Control"), (evidence_key, "Evidence", "*")):
        row = relation_model[key]
        if (row["source"], row["target"], row["directional"], row["multiple"]) != (source, target, True, True):
            raise ValueError(f"Unexpected direction or cardinality for {key}")

    def parameter(name, default):
        return f"coalesce(triggerBody()?['{name}'], {default})"

    action, expected, principal = (parameter(key, "''") for key in ("text", "text_1", "text_2"))
    control_id, source_id = (parameter(key, 0) for key in ("number", "number_1"))
    initial_row, updated = body("Read_control"), body("Read_owner_write")
    row = "variables('control')"
    revision = f"coalesce({row}?['__metadata']?['etag'], '')"
    can_edit = f"and(equals({row}?['IsActive'], true), {permission(row, 4)})"
    actor = f"int(coalesce({body('Read_actor')}?['Id'], 0))"
    owner = f"int(coalesce({body('Read_owner')}?['Id'], 0))"

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

    defaults = {"status": "invalid", "itemid": 0, "revision": "", "canedit": False, "relationid": 0, "ownerclaim": ""}
    schema = {name: {"title": name, "type": {str: "string", int: "number", bool: "boolean"}[type(value)],
                     "x-ms-dynamically-added": True} for name, value in defaults.items()}

    def report(status, previous=None, **values):
        return {"type": "SetVariable", "inputs": {"name": "result", "value": {**defaults, "status": status, **values}},
                "runAfter": after(previous)}

    owner_write = {
        "Missing_owner": report("owner_unavailable"),
        "Read_owner": rest(
            "@concat('_api/web/siteusers/getbyloginname(@login)?$select=Id,PrincipalType&@login=%27', "
            f"uriComponent(concat('i:0#.f|membership|', toLower({principal}))), '%27')", "Missing_owner"),
        "Verify_owner": condition(
            f"@and(greater({owner}, 0), equals({body('Read_owner')}?['PrincipalType'], 1))", {
                "Owner_already_assigned": condition(f"@equals({row}?['OwnerId'], {owner})", {
                    "Same_owner": report("unchanged", itemid=f"@int({control_id})"),
                }, None, {
                    "Owner_pending": report("unverified"),
                    "Owner_payload": compose({"__metadata": {"type": f"@{row}?['__metadata']?['type']"},
                                              "OwnerId": f"@{owner}"}, "Owner_pending"),
                    "Write_owner": rest("@outputs('Control_uri')", "Owner_payload", payload="Owner_payload", match=f"@{expected}"),
                    "Owner_race": condition("@equals(coalesce(outputs('Write_owner')?['statusCode'], 0), 412)",
                                            {"Conflicted_owner": report("conflict")}, "Write_owner", outcomes=["Failed"]),
                    "Read_owner_write": rest("@outputs('Control_select')", "Write_owner"),
                    "Confirm_owner": condition(
                        f"@and(equals({updated}?['OwnerId'], {owner}), equals({updated}?['EditorId'], {actor}), "
                        f"equals({updated}?['Id'], int({control_id})), not(equals({updated}?['__metadata']?['etag'], {expected})))",
                        {"Owner_saved": report("assigned", itemid=f"@int({control_id})")}, "Read_owner_write"),
                }),
            }, "Read_owner"),
    }

    source = body("Read_source")
    risk_mode = f"equals({action}, 'risk')"
    source_type, relation_type, relation_key = (f"outputs('{name}')" for name in ("Source_type", "Relation_type", "Relation_key"))
    kind = {"SourceObjectTypeKey": f"@{source_type}", "SourceItemID": f"@int({source_id})",
            "TargetObjectTypeKey": "Control", "TargetItemID": f"@int({control_id})", "IsActive": True}
    details = {"RelationID": f"@{relation_key}", "RelationKey": f"@{relation_key}", "RelationTypeKey": f"@{relation_type}", **kind}
    rows = f"{body('Verify_relation')}?['results']"
    saved = f"first({rows})"
    match = f"and(equals({saved}?['RelationID'], {relation_key}), equals({saved}?['RelationKey'], {relation_key}), " \
            f"equals({saved}?['RelationTypeKey'], {relation_type}), equals({saved}?['SourceObjectTypeKey'], {source_type}), " \
            f"equals({saved}?['SourceItemID'], int({source_id})), equals({saved}?['TargetObjectTypeKey'], 'Control'), " \
            f"equals({saved}?['TargetItemID'], int({control_id})), equals({saved}?['IsActive'], true), greater({saved}?['Id'], 0))"
    create_or_read = {
        "Link_pending": report("unverified"),
        "Source_type": compose(f"@if({risk_mode}, 'Risk', 'Evidence')", "Link_pending"),
        "Relation_type": compose(f"@if({risk_mode}, '{risk_key}', '{evidence_key}')", "Source_type"),
        "Relation_key": compose(f"@concat({relation_type}, ':', {source_type}, ':', string(int({source_id})), ':Control:', string(int({control_id})))", "Relation_type"),
        "Relation_query": compose(
            "@concat(outputs('Relation_items'), '?$select=" + LINK_FIELDS + "&$top=2&$filter=RelationKey%20eq%20%27', "
            f"uriComponent({relation_key}), '%27')", "Relation_key"),
        "Read_existing_relation": rest("@outputs('Relation_query')", "Relation_query"),
        "Insert_when_missing": condition(f"@empty({body('Read_existing_relation')}?['results'])", {
            "Link_payload": compose({"__metadata": {"type": f"@{body('Read_relation_list')}?['ListItemEntityTypeFullName']"},
                                     "Title": f"@{relation_key}", **details, "CreatedByApp": True}),
            "Insert_relation": rest("@outputs('Relation_items')", "Link_payload", payload="Link_payload"),
        }, "Read_existing_relation"),
        "Verify_relation": rest("@outputs('Relation_query')", "Insert_when_missing", outcomes=TRANSIENT),
        "Unique_readback": condition(f"@equals(length({rows}), 1)", {
            "Verify_endpoints": condition(f"@{match}", {
                "Relation_confirmed": report("linked", itemid=f"@int({control_id})", relationid=f"@int({saved}?['Id'])"),
            }, None, {"Wrong_relation": report("relation_conflict")}),
        }, "Verify_relation", {"Check_duplicate": condition(f"@greater(length({rows}), 1)", {
            "Duplicate_relation": report("relation_conflict"),
        }, None)}),
    }
    link_write = {
        "Source_unavailable": report("source_unavailable"),
        "Risk_items": compose(f"{risks}/items(", "Source_unavailable"),
        "Evidence_items": compose(f"{evidence}/items(", "Risk_items"),
        "Read_source": rest(f"@concat(if({risk_mode}, outputs('Risk_items'), outputs('Evidence_items')), "
                            f"string(int({source_id})), if({risk_mode}, ')?$select=Id,IsActive', ')?$select=Id,FileSystemObjectType'))", "Evidence_items"),
        "Check_source": condition(f"@and(equals({source}?['Id'], int({source_id})), if({risk_mode}, "
                                  f"equals({source}?['IsActive'], true), equals({source}?['FileSystemObjectType'], 0)))", {
            "Relation_blocked": report("blocked"),
            "Read_relation_list": rest(f"{relations}?$select=EffectiveBasePermissions,ListItemEntityTypeFullName", "Relation_blocked"),
            "Relation_write_allowed": condition(f"@{permission(body('Read_relation_list'), 2)}", {
                "Key_unavailable": report("configuration"),
                "Read_key_contract": rest(f"{relations}/fields/getbyinternalnameortitle('RelationKey')?$select=Indexed,EnforceUniqueValues",
                                          "Key_unavailable"),
                "Require_unique_key": condition(f"@and(equals({body('Read_key_contract')}?['EnforceUniqueValues'], true), "
                                                f"equals({body('Read_key_contract')}?['Indexed'], true))", create_or_read, "Read_key_contract"),
            }, "Read_relation_list"),
        }, "Read_source"),
    }

    trigger_fields = {key: {"title": title, "type": "number" if key.startswith("number") else "string",
                            "x-ms-dynamically-added": True, "x-ms-content-hint": "NUMBER" if key.startswith("number") else "TEXT"}
                      for key, title in (("number", "Kontroll-ID"), ("text", "Aktion"), ("text_1", "Revision"),
                                         ("number_1", "Quell-ID"), ("text_2", "Verantwortliche Person"))}
    owner_valid = f"and(equals({action}, 'owner'), contains({principal}, '@'), not(contains({principal}, '''')), lessOrEquals(length({principal}), 254))"
    link_valid = f"and(contains(createArray('risk','evidence'), {action}), {identifier(source_id)})"
    input_valid = f"@and({identifier(control_id)}, or(equals({action}, 'prepare'), or({owner_valid}, {link_valid})))"
    actions = {
        "Initial_result": {"type": "InitializeVariable", "inputs": {"variables": [
            {"name": "result", "type": "object", "value": defaults}]}, "runAfter": {}},
        "Initial_control": {"type": "InitializeVariable", "inputs": {"variables": [
            {"name": "control", "type": "object", "value": {}}]}, "runAfter": after("Initial_result")},
        "Initial_write_gate": {"type": "InitializeVariable", "inputs": {"variables": [
            {"name": "writeAllowed", "type": "boolean", "value": False}]}, "runAfter": after("Initial_control")},
        "Validate_request": condition(input_valid, {
            "Missing_control": report("unavailable"),
            "Controls_items": compose(f"{controls}/items(", "Missing_control"),
            "Control_uri": compose(f"@concat(outputs('Controls_items'), string(int({control_id})), ')')", "Controls_items"),
            "Control_select": compose(f"@concat(outputs('Control_uri'), '?$select={CONTROL_FIELDS}&$expand=Owner')", "Control_uri"),
            "Relation_items": compose(f"{relations}/items", "Control_select"),
            "Read_actor": rest("_api/web/currentuser?$select=Id", "Relation_items"),
            "Read_control": rest("@outputs('Control_select')", "Read_actor"),
            "Control_matches": condition(f"@and(equals({initial_row}?['Id'], int({control_id})), greater({actor}, 0), "
                                         f"not(empty(coalesce({initial_row}?['__metadata']?['etag'], ''))), "
                                         f"not(equals({initial_row}?['__metadata']?['etag'], '*')))", {
                "Keep_control": {"type": "SetVariable", "inputs": {"name": "control", "value": f"@{initial_row}"}, "runAfter": {}},
            }, "Read_control"),
        }, "Initial_write_gate"),
        "Prepare_or_authorize": condition(f"@not(empty({row}))", {
            "Prepare_or_write": condition(f"@equals({action}, 'prepare')", {
                "Control_ready": report("ready", itemid=f"@int({control_id})", revision=f"@{revision}", canedit=f"@{can_edit}",
                                        ownerclaim=f"@coalesce({row}?['Owner']?['Name'], '')"),
            }, None, {
                "Control_read_only": report("blocked"),
                "Require_edit_permission": condition(f"@{can_edit}", {
                    "Match_control_revision": condition(f"@equals({expected}, {revision})", {
                        "Authorize_write": {"type": "SetVariable", "inputs": {"name": "writeAllowed", "value": True}, "runAfter": {}},
                    }, None, {"Stale_control": report("conflict")}),
                }, "Control_read_only"),
            }),
        }, "Validate_request", outcomes=TRANSIENT),
        "Dispatch_write": condition("@variables('writeAllowed')", {
            "Assign_or_link": condition(f"@equals({action}, 'owner')", owner_write, None, link_write),
        }, "Prepare_or_authorize"),
        "Respond": {"type": "Response", "kind": "PowerApp", "inputs": {"statusCode": 200,
                    "body": {name: f"@variables('result')?['{name}']" for name in schema},
                    "schema": {"type": "object", "properties": schema}}, "runAfter": after("Dispatch_write", TRANSIENT)},
    }
    definition = {"$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                  "contentVersion": "1.0.0.0", "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                                                              "$connections": {"defaultValue": {}, "type": "Object"}},
                  "triggers": {"manual": {"type": "Request", "kind": "PowerAppV2", "inputs": {"schema": {"type": "object",
                               "properties": trigger_fields, "required": list(trigger_fields)}}}}, "actions": actions, "outputs": {}}
    return {"properties": {"connectionReferences": {CONNECTOR: {"runtimeSource": "invoker", "api": {"name": CONNECTOR},
             "connection": {"connectionReferenceLogicalName": reference}}}, "definition": definition, "templateName": ""}, "schemaVersion": "1.0.0.0"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    flow = build_flow(**json.loads(args.config.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(flow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
