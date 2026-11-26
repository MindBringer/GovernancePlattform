"""Build the invoker-bound workflow for restricted Problem records and links."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from build_control_write import body, identifier, permission
from build_evidence_upload import CONNECTOR, TRANSIENT, after, compose, condition

FIELDS = ("Id,Title,RootCause,Workaround,KnownError,RelatedIncidentsId,ResolvingChangesId,IsActive,"
          "EditorId,EffectiveBasePermissions,OData__UIVersionString")
NOTES = ("RootCause", "Workaround", "KnownError")
LOOKUPS = ("RelatedIncidentsId", "ResolvingChangesId")
MODEL = Path(__file__).resolve().parents[2] / "architecture" / "relations.yaml"


def build_flow(site, reference, problems_list, incidents_list, changes_list):
    parts = urlsplit(site)
    if (parts.scheme != "https" or not parts.hostname or not parts.hostname.endswith(".sharepoint.com")
            or parts.netloc != parts.hostname or not re.fullmatch(r"/sites/[A-Za-z0-9_-]+", parts.path)
            or parts.query or parts.fragment):
        raise ValueError("Expected a SharePoint site URL")
    if not re.fullmatch(r"[A-Za-z0-9_]+", reference):
        raise ValueError("Expected the native SharePoint connection reference")
    ids = [str(UUID(value)) for value in (problems_list, incidents_list, changes_list)]
    if len(set(ids)) != 3:
        raise ValueError("Three distinct native lists are required")
    problems, incidents, changes = (f"_api/web/lists(guid'{value}')" for value in ids)
    relation_types = json.loads(MODEL.read_text(encoding="utf-8"))["relationTypes"]
    for key, source, target in (("IncidentCausesProblem", "Incident", "Problem"), ("ProblemResolvedByChange", "Problem", "Change")):
        relation, = (row for row in relation_types if row["key"] == key)
        if (relation["source"], relation["target"], relation["directional"], relation["multiple"]) != (source, target, True, True):
            raise ValueError(f"Unexpected model for {key}")

    def param(name, default):
        return f"coalesce(triggerBody()?['{name}'], {default})"

    def get(row, name):
        return f"{row}?['{name}']"

    def text(row, name):
        return f"coalesce({get(row, name)}, '')"

    def array(row, name):
        return f"coalesce({get(row, name)}?['results'], json('[]'))"

    def rest(uri, previous=None, *, write=False, outcomes=None):
        headers = {"Accept": "application/json;odata=verbose"}
        parameters = {"dataset": site, "parameters/method": "POST" if write else "GET",
                      "parameters/uri": uri, "parameters/headers": headers}
        inputs = {"host": {"apiId": f"/providers/Microsoft.PowerApps/apis/{CONNECTOR}",
                           "connectionName": CONNECTOR, "operationId": "HttpRequest"},
                  "parameters": parameters, "authentication": "@parameters('$authentication')"}
        if write:
            headers.update({"Content-Type": "application/json;odata=verbose", "X-HTTP-Method": "MERGE", "IF-MATCH": f"@{etag}"})
            parameters["parameters/body"] = "@string(outputs('Write_payload'))"
            inputs["retryPolicy"] = {"type": "none"}
        return {"type": "OpenApiConnection", "inputs": inputs, "runAfter": after(previous, outcomes),
                "runtimeConfiguration": {"secureData": {"properties": ["inputs", "outputs"]}}}

    defaults = {"status": "invalid", "itemid": 0, "revision": "", "canedit": False}
    schema = {name: {"title": name, "type": {str: "string", int: "number", bool: "boolean"}[type(value)],
                     "x-ms-dynamically-added": True} for name, value in defaults.items()}

    def report(status, previous=None, **values):
        return {"type": "SetVariable", "inputs": {"name": "result", "value": {**defaults, "status": status, **values}},
                "runAfter": after(previous)}

    row, saved, source = (body(name) for name in ("Read_problem", "Read_back", "Read_link_source"))
    action, etag = param("text", "''"), param("text_1", "''")
    problem_id, link_id = param("number", 0), param("number_1", 0)
    problem_int, link_int = f"int({problem_id})", f"int({link_id})"
    actor = f"int(coalesce({body('Read_actor')}?['Id'], 0))"
    revision = f"coalesce({row}?['__metadata']?['etag'], '')"
    version = text(row, "OData__UIVersionString")
    can_edit = f"and(equals({get(row, 'IsActive')}, true), {permission(row, 4)})"
    empty_json = "'{}'"
    request = f"json({param('text_2', empty_json)})"
    note_values = {column: text(request, column) for column in NOTES}
    normalized = {column: f"trim({value})" for column, value in note_values.items()}
    note_match = ", ".join(f"equals({text(row, column)}, {value})" for column, value in normalized.items())
    original_matches = ", ".join(f"equals({text(row, column)}, {value})" for column, value in note_values.items())
    note_limit = ", ".join(f"and(contains({request}, '{column}'), lessOrEquals(length({value}), 4000))"
                           for column, value in note_values.items())
    incident_mode = f"equals({action}, 'incident')"
    old_incidents, old_changes = (array(row, column) for column in LOOKUPS)
    old_links = f"if({incident_mode}, {old_incidents}, {old_changes})"
    empty_object = "json('{}')"
    metadata_type = f"{row}?['__metadata']?['type']"
    entity = f"setProperty({empty_object}, '__metadata', setProperty({empty_object}, 'type', {metadata_type}))"
    analysis_payload = entity
    for column, value in normalized.items():
        analysis_payload = f"setProperty({analysis_payload}, '{column}', {value})"
    lookup_name = f"if({incident_mode}, '{LOOKUPS[0]}', '{LOOKUPS[1]}')"
    lookup_ids = f"setProperty({empty_object}, 'results', union({old_links}, createArray({link_int})))"
    link_payload = f"setProperty({entity}, {lookup_name}, {lookup_ids})"
    read_link = {
        "Unverified_source": report("source_unavailable"),
        "Incident_items": compose(f"{incidents}/items(", "Unverified_source"),
        "Change_items": compose(f"{changes}/items(", "Incident_items"),
        "Read_link_source": rest(f"@concat(if({incident_mode}, outputs('Incident_items'), outputs('Change_items')), "
                                 f"string({link_int}), ')?$select=Id,IsActive')", "Change_items"),
        "Source_matches": condition(f"@and(equals({get(source, 'Id')}, {link_int}), equals({get(source, 'IsActive')}, true))", {
            "Already_linked": condition(f"@contains({old_links}, {link_int})", {
                "Confirm_link_exists": report("unchanged", itemid=f"@{problem_int}"),
            }, None, {"Authorize_link_merge": report("write_ready")}),
        }, "Read_link_source"),
    }

    def expected(column):
        payload = "outputs('Write_payload')"
        if column in LOOKUPS:
            present = array(saved, column)
            target = f"if(contains({payload}, '{column}'), {array(payload, column)}, {array(row, column)})"
            return (f"and(equals(length({present}), length({target})), "
                    f"equals(length(union({present}, {target})), length({target})))")
        return (f"equals({text(saved, column)}, "
                f"if(contains({payload}, '{column}'), {text(payload, column)}, {text(row, column)}))")

    verify = ", ".join(expected(column) for column in (*NOTES, *LOOKUPS))
    actions = {
        "Initialize_result": {"type": "InitializeVariable", "inputs": {"variables": [
            {"name": "result", "type": "object", "value": defaults}]}, "runAfter": {}},
        "Validate_input": condition(
            f"@and({identifier(problem_id)}, or(equals({action}, 'prepare'), "
            f"and(not(empty({etag})), not(equals({etag}, '*')), lessOrEquals(length({etag}), 180), "
            f"or(and(equals({action}, 'analysis'), {note_limit}), "
            f"and(contains(createArray('incident','change'), {action}), {identifier(link_id)})))))", {
                "Unreadable_problem": report("unavailable"),
                "Problems_items": compose(f"{problems}/items(", "Unreadable_problem"),
                "Problem_uri": compose(f"@concat(outputs('Problems_items'), string({problem_int}), ')')", "Problems_items"),
                "Problem_select": compose(f"@concat(outputs('Problem_uri'), '?$select={FIELDS}')", "Problem_uri"),
                "Read_actor": rest("_api/web/currentuser?$select=Id", "Problem_select"),
                "Read_problem": rest("@outputs('Problem_select')", "Read_actor"),
                "Problem_matches": condition(f"@and(equals({get(row, 'Id')}, {problem_int}), greater({actor}, 0), "
                                             f"not(empty({revision})), not(equals({revision}, '*')), not(empty({version})))", {
                    "Prepare_or_write": condition(f"@equals({action}, 'prepare')", {
                        "Problem_ready": report("ready", itemid=f"@{problem_int}", revision=f"@{revision}",
                                                canedit=f"@and({can_edit}, {original_matches})"),
                    }, None, {
                        "Problem_blocked": report("blocked"),
                        "Require_edit": condition(f"@{can_edit}", {
                            "Require_revision": condition(f"@equals({revision}, {etag})",
                                {"Authorize_write": report("authorized")}, None, {"Stale_problem": report("conflict")}),
                        }, "Problem_blocked"),
                    }),
                }, "Read_problem"),
            }, "Initialize_result"),
        "Dispatch_write": condition("@equals(variables('result')?['status'], 'authorized')", {
            "Analysis_or_link": condition(f"@equals({action}, 'analysis')", {
                "Analysis_changed": condition(f"@not(and({note_match}))", {
                    "Authorize_analysis_merge": report("write_ready"),
                }, None, {"Analysis_unchanged": report("unchanged", itemid=f"@{problem_int}")}),
            }, None, read_link),
        }, "Validate_input", outcomes=TRANSIENT),
        "Persist_problem": condition("@equals(variables('result')?['status'], 'write_ready')", {
            "Write_unverified": report("unverified"),
            "Write_payload": {**compose(f"@if(equals({action}, 'analysis'), {analysis_payload}, {link_payload})", "Write_unverified"),
                              "runtimeConfiguration": {"secureData": {"properties": ["inputs"]}}},
            "Write_problem": rest("@outputs('Problem_uri')", "Write_payload", write=True),
            "Write_conflict": condition("@equals(coalesce(outputs('Write_problem')?['statusCode'], 0), 412)",
                                        {"Concurrent_change": report("conflict")}, "Write_problem", outcomes=["Failed"]),
            "Read_back": rest("@outputs('Problem_select')", "Write_problem"),
            "Confirm_problem": condition(f"@and(equals({get(saved, 'Id')}, {problem_int}), equals({get(saved, 'EditorId')}, {actor}), "
                                         f"not(equals({saved}?['__metadata']?['etag'], {revision})), "
                                         f"not(equals({text(saved, 'OData__UIVersionString')}, {version})), "
                                         f"equals({get(saved, 'IsActive')}, true), equals({text(saved, 'Title')}, {text(row, 'Title')}), "
                                         f"{verify})", {"Problem_saved": report("saved", itemid=f"@{problem_int}")}, "Read_back"),
        }, "Dispatch_write", outcomes=TRANSIENT),
        "Respond": {"type": "Response", "kind": "PowerApp", "inputs": {"statusCode": 200,
                    "body": {name: f"@variables('result')?['{name}']" for name in schema},
                    "schema": {"type": "object", "properties": schema}}, "runAfter": after("Persist_problem", TRANSIENT)},
    }
    fields = {key: {"title": title, "type": "number" if key.startswith("number") else "string",
                    "x-ms-dynamically-added": True, "x-ms-content-hint": "NUMBER" if key.startswith("number") else "TEXT"}
                    for key, title in (("number", "Problem-ID"), ("text", "Aktion"), ("text_1", "Revision"), ("number_1", "Quell-ID"),
                                       ("text_2", "Analysefelder"))}
    definition = {"$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                  "contentVersion": "1.0.0.0", "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                                                             "$connections": {"defaultValue": {}, "type": "Object"}},
                  "triggers": {"manual": {"type": "Request", "kind": "PowerAppV2", "inputs": {"schema": {"type": "object",
                               "properties": fields, "required": list(fields)}}}}, "actions": actions, "outputs": {}}
    definition["triggers"]["manual"]["runtimeConfiguration"] = {"secureData": {"properties": ["outputs"]}}
    return {"properties": {"connectionReferences": {CONNECTOR: {"runtimeSource": "invoker", "api": {"name": CONNECTOR},
             "connection": {"connectionReferenceLogicalName": reference}}}, "definition": definition, "templateName": ""}, "schemaVersion": "1.0.0.0"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    flow = build_flow(**json.loads(args.config.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(flow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
