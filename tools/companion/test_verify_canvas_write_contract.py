import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from verify_canvas_write_contract import patch_fields, read_sources, validate


def fixture(permission="read-write", field="SystemDescription"):
    metadata = {"schema": {"items": {"properties": {
        "Title": {"type": "string", "x-ms-permission": "read-write"},
        field: {"type": "string", "x-ms-permission": permission},
    }}}}
    return [{"Name": "Systems", "IsWritable": True, "TableName": "synthetic-systems",
             "DataEntityMetadataJson": {"synthetic-systems": json.dumps(metadata)}}]


class CanvasWriteContractRegression(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
