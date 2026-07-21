# Git baseline candidate 6.2.5

Commit the extracted directory contents, not the release ZIP. Keep `architecture/`, `provisioning/`, `migration/`, `tests/` and `docs/` under source control. Logs and generated artifacts are reproducible and excluded by `.gitignore`.

## Acceptance before first Git baseline

1. Run local syntax and architecture validation.
2. Execute a complete SharePoint DryRun with artifact export.
3. Confirm the final `Provisioning completed successfully` log entry.
4. Review warnings and generated schema artifacts.
5. Execute a second DryRun; it must report no unexpected create/update operations.
6. Only then initialize Git and create tag `v6.2.5`.
