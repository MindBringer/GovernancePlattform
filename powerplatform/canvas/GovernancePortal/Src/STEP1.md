# Step 1 – Editor State (1.0.0-alpha.3.2)

Ersetzt werden:

- `powerplatform/canvas/GovernancePortal/Src/App.pa.yaml`
- `powerplatform/canvas/GovernancePortal/Src/scrShell.pa.yaml`

Enthalten:

- typisierte `colEditorValues`
- `gblEditorDirty`
- `gblEditorCanSave`
- Aufbau des Editorzustands beim Klick auf **Neu**
- Gallery an `colEditorValues` gebunden
- definierte Bereinigung bei **Abbrechen** und Navigation

Danach:

```powershell
./powerplatform/scripts/Build.ps1
```
