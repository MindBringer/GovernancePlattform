# Governance Platform 6.2.5

Metadata-driven SharePoint foundation for the IT Governance Portal and its responsive Canvas App.

## Status

Git-baseline candidate. Promote to the repository baseline only after a complete successful DryRun and a second idempotency DryRun.

## Requirements

- PowerShell 7.4 or later
- PnP.PowerShell 3.2.0 or compatible
- SharePoint Site Owner permissions for provisioning

## Dry run

```powershell
.\provisioning\Provision-GovernancePlatform.ps1 `
    -SiteUrl "https://tenant.sharepoint.com/sites/GovernancePortal" `
    -Interactive `
    -DryRun `
    -ExportArtifacts
```


## Authentication

Use exactly one authentication mode. `-DeviceLogin` is recommended when the interactive browser window does not appear reliably.

```powershell
.\provisioning\Provision-GovernancePlatform.ps1 `
    -SiteUrl "https://tenant.sharepoint.com/sites/GovernancePortal" `
    -DeviceLogin `
    -DryRun `
    -ExportArtifacts
```

`-Interactive` and `-OSLogin` remain available. The log now records the authentication stage before PnP.PowerShell starts the blocking sign-in call.

## Productive provisioning

```powershell
.\provisioning\Provision-GovernancePlatform.ps1 `
    -SiteUrl "https://tenant.sharepoint.com/sites/GovernancePortal" `
    -Interactive `
    -ExportArtifacts
```

## Assessment

```powershell
.\provisioning\Reset-GovernancePlatform.ps1 `
    -SiteUrl "https://tenant.sharepoint.com/sites/GovernancePortal" `
    -Interactive `
    -AssessmentOnly
```

## Safety

The libraries Policies, Procedures, Runbooks, Architecture and Evidence are protected. Productive destructive actions require the confirmation token defined in `architecture/cleanup.yaml`. Dry runs never require a token.

## Repository policy

Architecture definitions and source scripts are versioned. Runtime logs, generated reports and release ZIP files are ignored.
