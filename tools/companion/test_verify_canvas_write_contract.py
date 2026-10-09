import json
import copy
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from verify_canvas_write_contract import (patch_fields, read_sources, read_connections, validate,
                                         validate_connections, validate_change_required,
                                         change_datetime_fields, validate_change_datetime)


def fixture(permission="read-write", field="SystemDescription"):
    metadata = {"schema": {"items": {"properties": {
        "Title": {"type": "string", "x-ms-permission": "read-write"},
        field: {"type": "string", "x-ms-permission": permission},
    }}}}
    return [{"Name": "Systems", "IsWritable": True, "TableName": "synthetic-systems",
             "DataEntityMetadataJson": {"synthetic-systems": json.dumps(metadata)}}]


class CanvasWriteContractRegression(unittest.TestCase):
    def change_fixture(self, required):
        sources = fixture()
        source = sources[0]
        source["Name"] = "Changes"
        metadata = json.loads(source["DataEntityMetadataJson"][source["TableName"]])
        metadata["schema"]["items"]["required"] = required
        source["DataEntityMetadataJson"][source["TableName"]] = json.dumps(metadata)
        return sources

    def test_writable_cached_required_fields_still_block_incomplete_draft(self):
        sources = self.change_fixture(["Title", "Criticality", "ChangeType"])
        self.assertEqual(validate(sources, {"Changes": ["Title"]}), [])
        errors = validate_change_required(sources, {"Title"})
        self.assertEqual(len(errors), 1)
        self.assertIn("cached connector required-field drift", errors[0])
        self.assertIn("Criticality", errors[0])
        self.assertIn("ChangeType", errors[0])

    def test_connector_title_only_requirement_accepts_incomplete_draft(self):
        self.assertEqual(validate_change_required(self.change_fixture(["Title"]), {"Title"}), [])

    def datetime_fixture(self, prop):
        sources = self.change_fixture(["Title"])
        source = sources[0]
        metadata = json.loads(source["DataEntityMetadataJson"][source["TableName"]])
        metadata["schema"]["items"]["properties"]["ApprovedDate"] = prop
        source["DataEntityMetadataJson"][source["TableName"]] = json.dumps(metadata)
        return sources

    def test_writable_date_only_approved_date_is_rejected(self):
        sources = self.datetime_fixture({"type": "string", "format": "date", "x-ms-permission": "read-write"})
        self.assertEqual(validate(sources, {"Changes": ["ApprovedDate"]}), [])
        self.assertEqual(validate_change_required(sources, {"Title"}), [])
        self.assertIn("date-only", validate_change_datetime(sources, {"ApprovedDate"})[0])

    def test_generated_timestamp_approved_date_passes(self):
        sources = self.datetime_fixture({"type": "string", "format": "date-time", "x-ms-permission": "read-write"})
        self.assertEqual(validate_change_datetime(sources, {"ApprovedDate"}), [])

    def test_missing_malformed_or_wrong_timestamp_type_fails_closed(self):
        for prop in [None, {}, {"type": "string"}, {"type": "number", "format": "date-time"}, "date-time"]:
            with self.subTest(prop=prop):
                self.assertTrue(validate_change_datetime(self.datetime_fixture(prop), {"ApprovedDate"}))
        sources = self.change_fixture(["Title"])
        self.assertTrue(validate_change_datetime(sources, {"ApprovedDate"}))

    def test_timestamp_requires_unique_source_and_bound_table_metadata(self):
        sources = self.datetime_fixture({"type": "string", "format": "date-time"})
        self.assertTrue(validate_change_datetime([], {"ApprovedDate"}))
        self.assertTrue(validate_change_datetime(sources * 2, {"ApprovedDate"}))
        sources[0]["TableName"] = "wrong-table"
        self.assertIn("bound-table", validate_change_datetime(sources, {"ApprovedDate"})[0])

    def test_only_explicit_change_instants_require_connector_timestamp_format(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "architecture").mkdir()
            fields = [
                {"objectTypeKey": "Change", "internalName": "ApprovedDate", "type": "DateTime", "dateFormat": "DateTime"},
                {"objectTypeKey": "Change", "internalName": "PlannedStart", "type": "DateTime"},
                {"objectTypeKey": "Change", "internalName": "ActualEnd", "type": "DateTime", "dateFormat": "DateOnly"},
                {"objectTypeKey": "Asset", "internalName": "LastReviewDate", "type": "DateTime", "dateFormat": "DateTime"},
            ]
            (root / "architecture/object-fields.yaml").write_text(json.dumps({"objectFields": fields}))
            self.assertEqual(change_datetime_fields(root), {"ApprovedDate"})
        self.assertEqual(validate_change_datetime([], set()), [])

    def test_missing_permanent_title_requirement_is_rejected(self):
        self.assertIn("missing=['Title']", validate_change_required(self.change_fixture([]), {"Title"})[0])

    def test_each_stale_optional_requirement_is_rejected(self):
        for name in ["Criticality", "ChangeType"]:
            with self.subTest(name=name):
                self.assertIn(name, validate_change_required(self.change_fixture(["Title", name]), {"Title"})[0])

    def test_duplicate_or_malformed_connector_requirements_fail_closed(self):
        for required in [["Title", "Title"], "Title", None, ["Title", 42]]:
            with self.subTest(required=required):
                self.assertIn("malformed or duplicate", validate_change_required(self.change_fixture(required), {"Title"})[0])

    def test_30444_readonly_description_is_rejected(self):
        errors = validate(fixture("read-only", "Description"), {"Systems": ["Title", "Description"]})
        self.assertEqual(len(errors), 1)
        self.assertIn("Systems.Description: connector permission read-only", errors[0])

    def test_new_architecture_field_requires_generated_reference(self):
        errors = validate(fixture(field="Description"), {"Systems": ["Title", "SystemDescription"]})
        self.assertEqual(errors, ["Systems.SystemDescription: missing generated connector field"])

    def test_verified_writable_reference_passes(self):
        self.assertEqual(validate(fixture(), {"Systems": ["Title", "SystemDescription"]}), [])

    def test_missing_permission_fails_closed(self):
        sources = fixture(None)
        self.assertEqual(len(validate(sources, {"Systems": ["SystemDescription"]})), 1)

    def test_other_table_metadata_cannot_substitute(self):
        sources = fixture()
        sources[0]["TableName"] = "different-table"
        self.assertEqual(validate(sources, {"Systems": ["Title"]}), ["Systems: missing metadata for the bound native table"])

    def test_duplicate_and_readonly_sources_are_rejected(self):
        sources = fixture()
        self.assertTrue(validate(sources * 2, {"Systems": ["Title"]}))
        sources[0]["IsWritable"] = False
        self.assertEqual(validate(sources, {"Systems": ["Title"]}), ["Systems: connector is not writable"])

    def test_nested_payload_members_are_not_patch_columns(self):
        source = '''Patch(Assets, gblAssetRecord, {
    Title: "literal with } and ""quote""",
    Owner: If(true, {\n        Claims: "synthetic",\n        Email: "synthetic@tenant.invalid"\n    }, Blank())
}); Patch(Systems, If(true, gblSystemRecord, Defaults(Systems)), {
    Title: "SYNTHETIC",
    SystemDescription: ""\n});'''
        self.assertEqual(patch_fields(source), {"Assets": ["Title", "Owner"], "Systems": ["Title", "SystemDescription"]})

    def test_missing_provider_is_rejected(self):
        with self.assertRaises(ValueError):
            patch_fields('Patch(Systems, Defaults(Systems), {\n  Title: "x"\n})')

    def test_change_patch_cannot_escape_the_connector_write_gate(self):
        source = '''Patch(Assets, Defaults(Assets), {
    Title: "SYNTHETIC"
}); Patch(Systems, Defaults(Systems), {
    Title: "SYNTHETIC"
}); Patch(Changes, gblChangeRecord, {
    Title: "SYNTHETIC",
    LinkedAsset: {\n        Id: 42,\n        Value: "SYNTHETIC"\n    },
    ChangeStatus: {\n        Value: "Entwurf"\n    }
});'''
        contracts = patch_fields(source)
        self.assertEqual(contracts["Changes"], ["Title", "LinkedAsset", "ChangeStatus"])
        self.assertEqual(validate(fixture(), {"Changes": contracts["Changes"]}),
                         ["Changes: expected one native data source"])

    def test_change_architecture_does_not_grant_connector_permissions(self):
        sources = fixture("read-only", "ChangeStatus")
        sources[0]["Name"] = "Changes"
        self.assertEqual(validate(sources, {"Changes": ["ChangeStatus"]}),
                         ["Changes.ChangeStatus: connector permission read-only, expected read-write"])
        self.assertEqual(validate(sources, {"Changes": ["LinkedAsset"]}),
                         ["Changes.LinkedAsset: missing generated connector field"])

    def test_zip_paths_support_canonical_and_studio_separators(self):
        for name in ("msapp/References/DataSources.json", "References\\DataSources.json"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "synthetic.msapp"
                with ZipFile(path, "w") as archive:
                    archive.writestr(name, json.dumps({"DataSources": fixture()}))
                self.assertEqual(read_sources(path), fixture())


def connection_fixture():
    sources = [
        {"Name": "Assets", "ApiId": "synthetic-sharepoint-api", "DatasetName": "synthetic-alias", "TableName": "synthetic-assets"},
        {"Name": "Changes", "ApiId": "synthetic-sharepoint-api", "DatasetName": "https://tenant.invalid/synthetic", "TableName": "synthetic-changes"},
        {"Name": "SyntheticUsers", "ApiId": "synthetic-users-api"},
        {"Name": "ComboBoxSample", "IsSampleData": True},
    ]
    local = {
        "synthetic-sharepoint": {
            "connectionRef": {"id": "synthetic-sharepoint-api"},
            "dataSources": ["Assets", "Changes"],
            "datasets": {"https://tenant.invalid/synthetic": {"dataSources": {
                "Assets": {"tableName": "synthetic-assets"},
                "Changes": {"tableName": "synthetic-changes"},
            }}},
        },
        "synthetic-users": {"connectionRef": {"id": "synthetic-users-api"}, "dataSources": ["SyntheticUsers"], "datasets": {}},
    }
    solution = {key: {"id": value["connectionRef"]["id"], "dataSources": copy.deepcopy(value["dataSources"]),
                      "dataSets": copy.deepcopy(value["datasets"])} for key, value in local.items()}
    return sources, local, solution


class CanvasConnectionContractRegression(unittest.TestCase):
    def test_30451_source_and_dataset_omission_is_rejected(self):
        sources, local, solution = connection_fixture()
        solution["synthetic-sharepoint"]["dataSources"].remove("Changes")
        del solution["synthetic-sharepoint"]["dataSets"]["https://tenant.invalid/synthetic"]["dataSources"]["Changes"]
        self.assertEqual(validate_connections(sources, local, solution), [
            "Changes: missing Solution source registration",
            "Solution dataset/table bindings differ from Canvas references",
        ])

    def test_complete_alias_and_service_bindings_pass(self):
        self.assertEqual(validate_connections(*connection_fixture()), [])

    def test_source_registration_alone_does_not_fix_wrong_solution_table(self):
        sources, local, solution = connection_fixture()
        solution["synthetic-sharepoint"]["dataSets"]["https://tenant.invalid/synthetic"]["dataSources"]["Changes"]["tableName"] = "different-table"
        self.assertEqual(validate_connections(sources, local, solution), ["Solution dataset/table bindings differ from Canvas references"])

    def test_canvas_binding_must_use_its_generated_native_table(self):
        sources, local, solution = connection_fixture()
        sources[1]["TableName"] = "different-table"
        self.assertEqual(validate_connections(sources, local, solution), ["Changes: Canvas dataset does not bind its native table"])

    def test_other_connector_cannot_substitute(self):
        sources, local, solution = connection_fixture()
        solution["synthetic-sharepoint"]["id"] = "different-api"
        self.assertIn("Solution connector API differs from Canvas references", validate_connections(sources, local, solution))

    def test_local_connections_support_both_package_layouts(self):
        _, local, _ = connection_fixture()
        for entry in ("msapp/Properties.json", "msapp\\Properties.json", "Properties.json"):
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "synthetic.msapp"
                with ZipFile(path, "w") as archive:
                    archive.writestr(entry, json.dumps({"LocalConnectionReferences": json.dumps(local)}))
                self.assertEqual(read_connections(path), local)


if __name__ == "__main__":
    unittest.main()
