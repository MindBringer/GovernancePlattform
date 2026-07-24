# Governance Portal – Migration to Canvas SourceCode

## Target structure

```text
powerplatform/
  canvas/
    GovernancePortal/
      Src/
        App.pa.yaml
        scrShell.pa.yaml
        ...
      ...                         # remaining files produced by PAC
  solution/
    canvas/GovernancePortal/
      gp_governanceportal_c93a1_DocumentUri.msapr
  scripts/
    DeveloperPlatform.psd1
    Common.ps1
    Validate-CanvasSource.ps1
    Initialize-CanvasSourceCode.ps1
    Pack-Canvas.ps1
    Pack-Solution.ps1
    Build.ps1
artifacts/
  inbound/                        # ignored
  work/                           # ignored
  outbound/                       # ignored
```

There is exactly one canonical Canvas source tree: `powerplatform/canvas/GovernancePortal` using `Src/*.pa.yaml`.
Do not retain `canvas-editable`, `*.fx.yaml`, or `Other/Src`.

## Clean migration

1. Commit or archive the current repository state.
2. Open the current working app in Power Apps Studio, save and publish it.
3. Download a fresh `.msapp` from Power Apps Studio (`Save as` / `Download a copy`).
4. Put it in `artifacts/inbound/GovernancePortal-current.msapp`.
5. Replace the scripts with this package.
6. Initialize the canonical source:

```powershell
./powerplatform/scripts/Initialize-CanvasSourceCode.ps1 `
  -MsAppPath ./artifacts/inbound/GovernancePortal-current.msapp `
  -Force
```

7. Remove the legacy tree after comparing the result:

```powershell
Remove-Item ./powerplatform/canvas-editable -Recurse -Force
```

8. Ensure `Src/App.pa.yaml` contains the configured version and run:

```powershell
./powerplatform/scripts/Build.ps1
```

9. Import the generated unmanaged solution from `artifacts/outbound`, publish all customizations, and smoke-test in a new browser session.

## Git ignore additions

```gitignore
.DS_Store
artifacts/inbound/
artifacts/work/
artifacts/outbound/
```

## Important operating rule

A fresh Power Apps Studio export is the safest baseline. PAC `canvas pack/unpack` remains preview/deprecated in current Microsoft documentation. Keep the round-trip validation and always validate the resulting app in DEV before merging.
