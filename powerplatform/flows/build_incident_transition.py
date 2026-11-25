"""Build the invoker-bound transition flow for a restricted Incident list."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from build_evidence_upload import CONNECTOR, TRANSIENT, after, compose, condition

MODEL = Path(__file__).resolve().parents[2] / "architecture" / "status-models.yaml"
FIELDS = ("Id,PortalStatus,ResolvedDate,OwnerId,LinkedSystemId,Priority,SecurityIncident,"
          "EditorId,EffectiveBasePermissions,OData__UIVersionString")


def build_flow(site, reference, incidents_list, time_zone):
    parts = urlsplit(site)
    if (parts.scheme != "https" or not parts.hostname or not parts.hostname.endswith(".sharepoint.com")
            or parts.netloc != parts.hostname or not re.fullmatch(r"/sites/[A-Za-z0-9_-]+", parts.path)
            or parts.query or parts.fragment):
        raise ValueError("Expected the prechecked SharePoint site URL")
    if not re.fullmatch(r"[A-Za-z0-9_]+", reference):
        raise ValueError("Expected a SharePoint connection reference logical name")
    if not re.fullmatch(r"[A-Za-z0-9 .()+-]{1,80}", time_zone):
        raise ValueError("Expected the prechecked Windows timezone of the SharePoint site")
    target_list = str(UUID(incidents_list))
    states = next(model["states"] for model in json.loads(MODEL.read_text(encoding="utf-8"))["statusModels"]
                  if model["key"] == "Incident")
    steps = {key: targets[0] for key, _, _, _, targets in states if targets}

    def string_parameter(name):
        return f"coalesce(triggerBody()?['{name}'], '')"

    def metadata(row, name):
        return f"{row}?['__metadata']?['{name}']"

    def field(row, name):
        return f"{row}?['{name}']"

    def text(row, name):
        return f"coalesce({field(row, name)}, '')"

    def safe_etag(value):
        return f"and(not(empty({value})), not(equals({value}, '*')), lessOrEquals(length({value}), 180))"

    def local_day(value):
        return f"convertTimeZone(coalesce({value}, '1900-01-01T12:00:00Z'), 'UTC', '{time_zone}', 'yyyy-MM-dd')"

    def info(row):
        etag = f"coalesce({metadata(row, 'etag')}, '')"
        return (f"and(equals({field(row, 'Id')}, int({item_id})), "
                f"{safe_etag(etag)}, not(empty(coalesce({metadata(row, 'type')}, ''))), "
                f"not(empty({text(row, 'OData__UIVersionString')})))")

    def rest(uri, previous, *, etag=None):
        headers = {"Accept": "application/json;odata=verbose"}
        parameters = {"dataset": site, "parameters/method": "POST" if etag else "GET",
                      "parameters/uri": uri, "parameters/headers": headers}
        inputs = {"host": {"apiId": f"/providers/Microsoft.PowerApps/apis/{CONNECTOR}",
                           "connectionName": CONNECTOR, "operationId": "HttpRequest"},
                  "parameters": parameters, "authentication": "@parameters('$authentication')"}
        if etag:
            headers.update({"Content-Type": "application/json;odata=verbose", "X-HTTP-Method": "MERGE", "IF-MATCH": etag})
            parameters["parameters/body"] = "@string(outputs('Transition_payload'))"
            inputs["retryPolicy"] = {"type": "none"}
        return {"type": "OpenApiConnection", "inputs": inputs, "runAfter": after(previous),
                "runtimeConfiguration": {"secureData": {"properties": ["inputs", "outputs"]}}}

    initial = {"status": "invalid", "itemid": 0, "portalstatus": "", "nextstatus": "", "revision": "",
               "nativeversion": "", "securityincident": False, "canadvance": False}
    schema = {name: {"title": name, "type": {str: "string", int: "number", bool: "boolean"}[type(default)],
                     "x-ms-dynamically-added": True} for name, default in initial.items()}

    def successor(row):
        mapping = json.dumps(steps, ensure_ascii=False, separators=(",", ":"))
        return f"coalesce(json('{mapping}')?[{text(row, 'PortalStatus')}], '')"

    def can_advance(row):
        mask = f"int(coalesce({field(row, 'EffectiveBasePermissions')}?['Low'], '0'))"
        has_resolution_date = f"not(empty({text(row, 'ResolvedDate')}))"
        return (f"and(greater({actor}, 0), equals(mod(div({mask}, 4), 2), 1), "
                f"not(empty({successor(row)})), greater(coalesce({field(row, 'OwnerId')}, 0), 0), "
                f"greater(coalesce({field(row, 'LinkedSystemId')}, 0), 0), not(empty({text(row, 'Priority')})), "
                f"equals(equals({text(row, 'PortalStatus')}, 'Resolved'), {has_resolution_date}), "
                f"or(equals({field(row, 'SecurityIncident')}, true), equals({field(row, 'SecurityIncident')}, false)))")

    def report(code, previous=None, *, row=None):
        result = {**initial, "status": code}
        if row:
            result.update(itemid=f"@int({item_id})", portalstatus=f"@{text(row, 'PortalStatus')}",
                          nextstatus=f"@{successor(row)}", revision=f"@{metadata(row, 'etag')}",
                          nativeversion=f"@{text(row, 'OData__UIVersionString')}",
                          securityincident=f"@coalesce({field(row, 'SecurityIncident')}, false)",
                          canadvance=f"@{can_advance(row)}")
        return {"type": "SetVariable", "inputs": {"name": "result", "value": result}, "runAfter": after(previous)}

    mode, expected_tag, version, next_status = map(string_parameter, ("text", "text_1", "text_2", "text_3"))
    item_id = "coalesce(triggerBody()?['number'], 0)"
    row = "body('Read_incident')?['d']"
    updated = "body('Readback')?['d']"
    actor = "int(coalesce(body('Current_user')?['d']?['Id'], 0))"
    select_uri = f"@concat(outputs('Incident_uri'), '?$select={FIELDS}')"
    exact_snapshot = (f"and(equals({metadata(row, 'etag')}, {expected_tag}), "
                      f"equals({field(row, 'OData__UIVersionString')}, {version}))")
    verified = (f"and({info(updated)}, equals({field(updated, 'PortalStatus')}, {next_status}), "
                f"equals({field(updated, 'EditorId')}, {actor}), not(equals({metadata(updated, 'etag')}, {expected_tag})), "
                f"not(equals({field(updated, 'OData__UIVersionString')}, {version})), "
                f"equals({field(updated, 'SecurityIncident')}, {field(row, 'SecurityIncident')}), "
                f"equals({field(updated, 'OwnerId')}, {field(row, 'OwnerId')}), "
                f"equals({field(updated, 'LinkedSystemId')}, {field(row, 'LinkedSystemId')}), "
                f"equals({field(updated, 'Priority')}, {field(row, 'Priority')}), "
                f"if(equals({next_status}, 'Resolved'), equals({local_day(field(updated, 'ResolvedDate'))}, outputs('Resolution_day')), "
                f"equals({field(updated, 'ResolvedDate')}, {field(row, 'ResolvedDate')})))")
    payload = {"__metadata": {"type": f"@{metadata(row, 'type')}"}, "PortalStatus": f"@{next_status}"}
    resolution_date = f"@convertTimeZone(concat(outputs('Resolution_day'), 'T00:00:00'), '{time_zone}', 'UTC', 'yyyy-MM-ddTHH:mm:ssZ')"
    write = {
        "Require_match": condition(f"@{exact_snapshot}", {
            "Default_blocked": report("blocked"),
            "Can_advance": condition(f"@and({can_advance(row)}, equals({next_status}, {successor(row)}))", {
                "Unknown_before_write": report("unverified"),
                "Resolution_day": compose(f"@{local_day('utcNow()')}", "Unknown_before_write"),
                "Set_payload": condition(f"@equals({next_status}, 'Resolved')", {
                    "Resolved_payload": {"type": "SetVariable", "inputs": {"name": "payload", "value": {
                        **payload, "ResolvedDate": resolution_date}}, "runAfter": {}},
                }, "Resolution_day", {
                    "Status_payload": {"type": "SetVariable", "inputs": {"name": "payload", "value": payload}, "runAfter": {}},
                }),
                "Transition_payload": compose("@variables('payload')", "Set_payload"),
                "Merge_transition": rest("@outputs('Incident_uri')", "Transition_payload", etag=f"@{expected_tag}"),
                "Conflict_during_merge": condition("@equals(coalesce(outputs('Merge_transition')?['statusCode'], 0), 412)",
                    {"Conflicted_merge": report("conflict")}, "Merge_transition", outcomes=["Failed"]),
                "Readback": rest(select_uri, "Merge_transition"),
                "Verified_transition": condition(f"@{verified}", {"Saved": report("saved", row=updated)}, "Readback"),
            }, "Default_blocked"),
        }, None, {"Stale_snapshot": report("conflict")}),
    }
    trigger_fields = {name: {"title": label, "type": "number" if name == "number" else "string",
                             "x-ms-dynamically-added": True, "x-ms-content-hint": "NUMBER" if name == "number" else "TEXT"}
                      for name, label in (("number", "Listen-ID"), ("text", "Aktion"), ("text_1", "Listenrevision"),
                                          ("text_2", "SharePoint-Version"), ("text_3", "Zielstatus"))}
    actions = {
        "Initialize_result": {"type": "InitializeVariable", "inputs": {"variables": [
            {"name": "result", "type": "object", "value": initial}]}, "runAfter": {}},
        "Initialize_payload": {"type": "InitializeVariable", "inputs": {"variables": [
            {"name": "payload", "type": "object", "value": {}}]}, "runAfter": after("Initialize_result")},
        "Validate_input": condition(
            f"@and(greater({item_id}, 0), lessOrEquals({item_id}, 2147483647), equals({item_id}, int({item_id})), "
            f"or(equals({mode}, 'prepare'), and(equals({mode}, 'advance'), {safe_etag(expected_tag)}, "
            f"not(empty({version})), lessOrEquals(length({version}), 32))))", {
                "Default_unavailable": report("unavailable"),
                "Incident_uri": compose(f"@concat('_api/web/lists(guid''{target_list}'')/items(', string(int({item_id})), ')')",
                                        "Default_unavailable"),
                "Current_user": rest("_api/web/currentuser?$select=Id", "Incident_uri"),
                "Read_incident": rest(select_uri, "Current_user"),
                "Require_snapshot": condition(f"@{info(row)}", {"Prepare_or_advance": condition(
                    f"@equals({mode}, 'prepare')", {"Snapshot": report("ready", row=row)}, None, write)}, "Read_incident"),
            }, "Initialize_payload"),
        "Respond": {"type": "Response", "kind": "PowerApp", "inputs": {"statusCode": 200,
                    "body": {name: f"@variables('result')?['{name}']" for name in schema}, "schema": {"type": "object", "properties": schema}},
                    "runAfter": after("Validate_input", TRANSIENT)},
    }
    return {"properties": {"connectionReferences": {CONNECTOR: {"runtimeSource": "invoker", "api": {"name": CONNECTOR},
            "connection": {"connectionReferenceLogicalName": reference}}}, "definition": {
                "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                "contentVersion": "1.0.0.0", "parameters": {"$authentication": {"defaultValue": {}, "type": "SecureObject"},
                                                             "$connections": {"defaultValue": {}, "type": "Object"}},
                "triggers": {"manual": {"type": "Request", "kind": "PowerAppV2", "inputs": {"schema": {
                    "type": "object", "properties": trigger_fields, "required": list(trigger_fields)}}}},
                "actions": actions, "outputs": {},
            }, "templateName": ""}, "schemaVersion": "1.0.0.0"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    flow = build_flow(**json.loads(args.config.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(flow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
