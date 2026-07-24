# Governance Portal – Befehlssammlung

**Solution für Entwicklung holen**
1. Power-Apps: unmanaged Solution exportieren
2. Zip-Download in ./artifacts/inbound legen
3. pwsh entpacken:
pac solution unpack `
  --zipfile ./artifacts/inbound/GovernancePortal_1_0_0_30402.zip `
  --folder ./powerplatform/solution `
  --packagetype Unmanaged `
  --allowDelete true `
  --allowWrite true 
4. pwsh SourceCode neu erzeugen:
pac canvas unpack `
  --msapp ./powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp `
  --sources ./powerplatform/canvas/GovernancePortal `
  --layout SourceCode `
  --overwrite

5. Commit:
git add .
git commit -m "baseline: v1.0.0.30402 with systems and office365 connector"

	ODER:
git commit -m "feat(canvas): stage 2 metadata editor foundation

- metadata-driven editor collection
- dynamic renderer
- typed editor state
- validation
- dirty state
- save placeholder
- template control baseline
- successful pack/unpack roundtrip"

6. Taggen:
git tag canvas-v1.0.3.8-stage2
git push origin main --tags