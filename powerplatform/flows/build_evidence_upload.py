"""Render the native Power Apps V2 Evidence flow with a deployment's SharePoint connection."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

CONNECTOR = "shared_sharepointonline"
TRANSIENT = ["Succeeded", "Failed", "TimedOut", "Skipped"]
ACCEPT = "application/json;odata=nometadata"
MAX_BYTES = 5_000_000
NAME_CHARACTERS = "abcdefghijklmnopqrstuvwxyzäöüß0123456789._- "


def after(action, outcomes=None):
    return {action: outcomes or ["Succeeded"]} if action else {}


def compose(value, previous=None, outcomes=None):
    return {"type": "Compose", "inputs": value, "runAfter": after(previous, outcomes)}


def condition(expression, actions, previous, otherwise=None, outcomes=None):
    return {"type": "If", "expression": expression, "actions": actions,
            "else": {"actions": otherwise or {}}, "runAfter": after(previous, outcomes)}


def build_flow(site, reference, assets_list, relations_list, *, changes_list=None, risks_list=None):
    """Use a known file path and an enforced list key as independent atomic create guards."""
    parts = urlsplit(site)
    if (parts.scheme != "https" or not parts.hostname or not parts.hostname.endswith(".sharepoint.com")
            or parts.netloc != parts.hostname or not re.fullmatch(r"/sites/[A-Za-z0-9_-]+", parts.path)
            or parts.query or parts.fragment):
        raise ValueError("Expected the prechecked SharePoint site URL")
    if not re.fullmatch(r"[A-Za-z0-9_]+", reference):
        raise ValueError("Expected a Dataverse SharePoint connection reference logical name")

    object_flow = changes_list is not None or risks_list is not None
    if object_flow:
        if not changes_list or not risks_list or assets_list is not None:
            raise ValueError("Provide both Changes and Risks, without an Assets list, for the object flow")
        changes_list = str(UUID(changes_list))
        risks_list = str(UUID(risks_list))
        if len({changes_list, risks_list, str(UUID(relations_list))}) != 3:
            raise ValueError("Changes, Risks and GovernanceRelations must be distinct lists")
    else:
        assets_list = str(UUID(assets_list))
    relations_list = str(UUID(relations_list))

    target_input = "triggerBody()?['number']"
    type_input = "triggerBody()?['text']"
    read_action = "Read_target" if object_flow else "Read_asset"
    target_row = f"body('{read_action}')"
    id_field = "Id" if object_flow else "ID"
    target_id_value = f"{target_row}?['{id_field}']"
    target_id = f"@int({target_id_value})"
    target_type = f"@{type_input}" if object_flow else "Asset"
    type_expression = type_input if object_flow else "'Asset'"
    response_id = "targetid" if object_flow else "assetid"

    def result_value(status, target=0, evidence=0, relation=0, kind=""):
        value = {"status": status, response_id: target, "evidenceid": evidence, "relationid": relation}
        if object_flow:
            value["targettype"] = kind
        return value

    def result(status, previous, target, evidence=0, relation=0):
        return {"type": "SetVariable", "inputs": {"name": "result", "value":
                result_value(status, target, evidence, relation, target_type)}, "runAfter": after(previous)}

    def sp(operation, parameters, previous=None, outcomes=None, write=False, sensitive=None):
        inputs = {
            "host": {"apiId": f"/providers/Microsoft.PowerApps/apis/{CONNECTOR}",
                     "connectionName": CONNECTOR, "operationId": operation},
            "parameters": {"dataset": site, **parameters},
            "authentication": "@parameters('$authentication')",
        }
        if write:
            inputs["retryPolicy"] = {"type": "none"}
        action = {"type": "OpenApiConnection", "inputs": inputs,
                  "runAfter": after(previous, outcomes)}
        if sensitive:
            action["runtimeConfiguration"] = {"secureData": {"properties": sensitive}}
        return action

    def rest(method, uri, previous=None, data=None):
        headers = {"Accept": ACCEPT}
        parameters = {"parameters/method": method, "parameters/uri": uri, "parameters/headers": headers}
        if data is not None:
            headers["Content-Type"] = "application/octet-stream"
            parameters["parameters/body"] = data
        return sp("HttpRequest", parameters, previous, write=method == "POST",
                  sensitive=["inputs", "outputs"] if method == "POST" else None)

    file_input = "triggerBody()?['file']?['contentBytes']"
    stored_file_input = "outputs('Read_file_bytes')?['body']?['$content']"
    file_id = "@int(body('Read_file')?['ItemId'])"
    relation_rows = "body('Verify_relation')?['value']"
    relation_row = f"first({relation_rows})"
    relation_id = f"@int({relation_row}?['ID'])"
    query = {"table": relations_list, "$top": 2,
             "$filter": "@concat('RelationKey eq ''', outputs('Relation_key'), '''')"}
    result_fields = {
        name: {"title": name, "type": kind, "x-ms-dynamically-added": True}
        for name, kind in (("status", "string"), (response_id, "number"),
                           ("evidenceid", "number"), ("relationid", "number"))
    }
    if object_flow:
        result_fields["targettype"] = {"title": "targettype", "type": "string", "x-ms-dynamically-added": True}
    relation_suffix = f"':', {type_expression}, ':', " if object_flow else "':Asset:', "
    verify_relation = {
        "Mark_unlinked": result("unlinked", None, target_id, file_id),
        "Relation_key": compose(
            "@concat('EvidenceSupportsObject:Evidence:', string(body('Read_file')?['ItemId']), "
            f"{relation_suffix}string({target_id_value}))", "Mark_unlinked"),
        "Read_relation": sp("GetItems", query, "Relation_key"),
        "Insert_if_absent": condition(
            "@empty(body('Read_relation')?['value'])", {
                "Create_relation": sp("PostItem", {
                    "table": relations_list, "item/Title": "@outputs('Filename')",
                    "item/RelationID": "@outputs('Relation_key')", "item/RelationKey": "@outputs('Relation_key')",
                    "item/RelationTypeKey": "EvidenceSupportsObject",
                    "item/SourceObjectTypeKey": "Evidence", "item/SourceItemID": file_id,
                    "item/SourceTitle": "@outputs('Filename')",
                    "item/TargetObjectTypeKey": target_type, "item/TargetItemID": target_id,
                    "item/TargetTitle": f"@{target_row}?['Title']",
                    "item/TargetGovernanceID": f"@{target_row}?['GovernanceID']",
                    "item/IsActive": True, "item/CreatedByApp": True,
                }, write=True),
            }, "Read_relation"),
        # An uncertain create response or a competing writer is resolved by reading the unique key.
        "Verify_relation": sp("GetItems", query, "Insert_if_absent", TRANSIENT),
        "Confirm_one_relation": condition(
            f"@equals(length({relation_rows}), 1)", {
                "Confirm_relation_content": condition(
                    "@and("
                    f"equals({relation_row}?['RelationKey'], outputs('Relation_key')), "
                    f"equals({relation_row}?['RelationTypeKey'], 'EvidenceSupportsObject'), "
                    f"equals({relation_row}?['SourceObjectTypeKey'], 'Evidence'), "
                    f"equals({relation_row}?['TargetObjectTypeKey'], {type_expression}), "
                    f"equals({relation_row}?['SourceItemID'], body('Read_file')?['ItemId']), "
                    f"equals({relation_row}?['TargetItemID'], {target_id_value}), "
                    f"equals({relation_row}?['IsActive'], true), greater(int({relation_row}?['ID']), 0))",
                    {"Mark_saved": result("saved", None, target_id, file_id, relation_id)}, None,
                    {"Mark_inconsistent_relation": result("relation_conflict", None, target_id, file_id)},
                ),
            }, "Verify_relation", {
                "Mark_duplicate_relations": condition(
                    f"@greater(length({relation_rows}), 1)",
                    {"Mark_duplicate": result("relation_conflict", None, target_id, file_id)}, None),
            }),
    }
    file_prefix = f"toLower({type_expression}), '-', " if object_flow else "'asset-', "
    transfer = {
        "Mark_transfer_pending": result("retry", None, target_id),
        "Stored_filename": compose(
            f"@concat({file_prefix}string({target_id_value}), '--', outputs('Filename'))",
            "Mark_transfer_pending"),
        "File_path": compose("@concat('/Evidence/', outputs('Stored_filename'))", "Stored_filename"),
        "Find_file": sp("GetFileMetadataByPath", {"path": "@outputs('File_path')"}, "File_path"),
        "Create_if_not_found": condition(
            "@equals(outputs('Find_file')?['statusCode'], 404)", {
                "Create_file_no_overwrite": rest(
                    "POST",
                    "@concat('_api/web/lists/getbytitle(''Evidence'')/RootFolder/Files/Add(url=''', "
                    "uriComponent(outputs('Stored_filename')), ''', overwrite=false)')",
                    data=f"@base64ToBinary({file_input})",
                ),
            }, "Find_file", outcomes=TRANSIENT),
        "Read_file": sp("GetFileMetadataByPath", {"path": "@outputs('File_path')"}, "Create_if_not_found", TRANSIENT),
        "Read_file_bytes": sp("GetFileContentByPath", {"path": "@outputs('File_path')", "inferContentType": False},
                              "Read_file", sensitive=["outputs"]),
        "Validate_file_readback": condition(
            "@and(greater(int(body('Read_file')?['ItemId']), 0), "
            "equals(body('Read_file')?['IsFolder'], false), "
            f"not(empty(coalesce({stored_file_input}, ''))))", {
                # Compare the decoded octets, independently of the Base64 representation.
                "Confirm_file": condition(
                    f"@equals(base64ToBinary({stored_file_input}), base64ToBinary({file_input}))",
                    verify_relation, None,
                    {"Mark_other_content": result("file_conflict", None, target_id, file_id)},
                ),
            }, "Read_file_bytes",
        ),
    }
    # The AddListItems and EditListItems masks are 2 and 4 in SharePoint's low word.
    def has_permission(name, mask):
        return f"equals(mod(div(int(body('{name}')?['EffectiveBasePermissions']?['Low']), {mask}), 2), 1)"

    authorized = {"Mark_blocked": result("blocked", None, 0)}
    target_gate = ""
    if object_flow:
        authorized.update({
            "Target_list": compose(
                f"@if(equals({type_input}, 'Change'), '{changes_list}', '{risks_list}')", "Mark_blocked"),
            read_action: rest(
                "GET",
                "@concat('_api/web/lists(guid''', outputs('Target_list'), ''')/items(', "
                f"string(int({target_input})), ')?$select=Id,Title,GovernanceID,EffectiveBasePermissions')",
                "Target_list"),
        })
        target_gate = f"{has_permission(read_action, 4)}, "
    else:
        authorized[read_action] = sp("GetItem", {"table": assets_list, "id": f"@int({target_input})"}, "Mark_blocked")
    authorized.update({
        "Evidence_permissions": rest(
            "GET", "_api/web/lists/getbytitle('Evidence')?$select=EffectiveBasePermissions", read_action),
        "Relation_permissions": rest(
            "GET", "_api/web/lists/getbytitle('GovernanceRelations')?$select=EffectiveBasePermissions", "Evidence_permissions"),
        "Can_add_to_both": condition(
            f"@and(equals({target_input}, int({target_id_value})), {target_gate}"
            f"{has_permission('Evidence_permissions', 2)}, {has_permission('Relation_permissions', 2)})", {
                "Mark_schema_blocked": result("configuration", None, target_id),
                "Read_relation_key_contract": rest(
                    "GET",
                    "_api/web/lists/getbytitle('GovernanceRelations')/fields/getbyinternalnameortitle('RelationKey')"
                    "?$select=EnforceUniqueValues",
                    "Mark_schema_blocked",
                ),
                "Require_unique_key": condition(
                    "@equals(body('Read_relation_key_contract')?['EnforceUniqueValues'], true)",
                    transfer, "Read_relation_key_contract"),
            }, "Relation_permissions"),
    })
    type_gate = f"contains(createArray('Change','Risk'), {type_input}), lessOrEquals({target_input}, 2147483647), " if object_flow else ""
    actions = {
        "Initial_result": {"type": "InitializeVariable", "inputs": {"variables": [
            {"name": "result", "type": "object", "value": result_value("invalid")},
        ]}, "runAfter": {}},
        "Filename": compose("@toLower(coalesce(triggerBody()?['file']?['name'], ''))", "Initial_result"),
        "Invalid_filename_characters": {
            "type": "Query", "inputs": {"from": "@range(0,length(outputs('Filename')))",
                                      "where": f"@not(contains('{NAME_CHARACTERS}',substring(outputs('Filename'),item(),1)))"},
            "runAfter": after("Filename"),
        },
        "Validate_request": condition(
            f"@and({type_gate}greater({target_input}, 0), equals({target_input}, int({target_input})), "
            "greater(length(outputs('Filename')), 0), lessOrEquals(length(outputs('Filename')), 100), "
            "not(startsWith(outputs('Filename'), '.')), not(endsWith(outputs('Filename'), '.')), "
            "equals(trim(outputs('Filename')), outputs('Filename')), "
            "not(contains(outputs('Filename'), '..')), not(contains(outputs('Filename'), '_vti_')), "
            "empty(body('Invalid_filename_characters')), "
            f"greater(length(coalesce({file_input}, '')), 0), "
            f"lessOrEquals(sub(div(mul(length(coalesce({file_input}, '')), 3), 4), "
            f"if(endsWith(coalesce({file_input}, ''), '=='), 2, if(endsWith(coalesce({file_input}, ''), '='), 1, 0))), {MAX_BYTES}))",
            authorized, "Invalid_filename_characters"),
        "Respond_to_canvas": {"type": "Response", "kind": "PowerApp", "inputs": {
            "statusCode": 200, "body": {
                name: f"@variables('result')?['{name}']" for name in result_fields
            },
            "schema": {"type": "object", "properties": result_fields},
        }, "runAfter": after("Validate_request", TRANSIENT)},
    }
    schema = {
        "type": "object", "required": ["number", "file"],
        "properties": {
            "number": {"title": "Asset-ID", "description": "Native SharePoint-ID des ausgewählten Assets", "type": "number",
                       "x-ms-dynamically-added": True, "x-ms-content-hint": "NUMBER"},
            "file": {"title": "Nachweisdatei", "description": "Dateiname und Inhalt eines Nachweises bis 5 MB", "type": "object",
                     "x-ms-dynamically-added": True, "x-ms-content-hint": "FILE",
                     "properties": {"name": {"type": "string"},
                                    "contentBytes": {"type": "string", "format": "byte"}},
                     "required": ["name", "contentBytes"]},
        },
    }
    if object_flow:
        schema["required"] = ["number", "text", "file"]
        schema["properties"] = {
            "number": {"title": "Objekt-ID", "description": "Native SharePoint-ID des ausgewählten Changes oder Risikos",
                       "type": "number", "x-ms-dynamically-added": True, "x-ms-content-hint": "NUMBER"},
            "text": {"title": "Objekttyp", "description": "Change oder Risk aus der Liste der Portalobjekte",
                     "type": "string", "x-ms-dynamically-added": True, "x-ms-content-hint": "TEXT"},
            "file": schema["properties"]["file"],
        }
    return {
        "properties": {
            "connectionReferences": {CONNECTOR: {
                "runtimeSource": "invoker",
                "connection": {"connectionReferenceLogicalName": reference},
                "api": {"name": CONNECTOR},
            }},
            "definition": {
                "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                "contentVersion": "1.0.0.0",
                "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                               "$connections": {"defaultValue": {}, "type": "Object"}},
                "triggers": {"manual": {"type": "Request", "kind": "PowerAppV2", "inputs": {"schema": schema},
                                        "runtimeConfiguration": {"secureData": {"properties": ["outputs"]}}}},
                "actions": actions, "outputs": {},
            },
            "templateName": "",
        },
        "schemaVersion": "1.0.0.0",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", required=True)
    parser.add_argument("--connection-reference", required=True)
    parser.add_argument("--assets-list")
    parser.add_argument("--changes-list")
    parser.add_argument("--risks-list")
    parser.add_argument("--relations-list", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not (args.assets_list and not (args.changes_list or args.risks_list)
            or not args.assets_list and args.changes_list and args.risks_list):
        parser.error("Provide --assets-list or both --changes-list and --risks-list")
    flow = build_flow(args.site, args.connection_reference, args.assets_list, args.relations_list,
                      changes_list=args.changes_list, risks_list=args.risks_list)
    args.output.write_text(json.dumps(flow, indent=2, ensure_ascii=False) + "\n")
