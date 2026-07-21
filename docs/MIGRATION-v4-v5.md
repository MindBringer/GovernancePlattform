# Migration from v4 to v5

The v5 provisioner first provisions additive structures, then evaluates known v4 mismatches.

## Non-destructive rules

1. Existing lists and content remain untouched.
2. Existing incompatible fields are not modified.
3. Choice fields are not converted to text automatically.
4. Text-to-lookup changes require a side-by-side field and an explicit mapping.
5. Legacy lookup fields remain until the Canvas App and flows have switched to the central relation graph.

## Known decisions

- `Assets.AssetType`: retain the current text field; future candidate `AssetTypeRef`.
- `Problems.KnownError`: retain the existing Note field until semantics are clarified.
- Catalog Choice fields remain Choice.
- v4 AI fields, where already created, are considered legacy. New AI processing writes to `AIMetadata`.
- `GovernanceRelations` becomes the canonical relationship store; existing direct lookups may remain as compatibility fields.

Run with `-AssessMigration -ExportArtifacts` to produce an environment-specific assessment.
