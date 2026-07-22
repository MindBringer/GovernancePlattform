# Alpha 3.0 anwenden

Das Paket im Stamm des lokalen Repositorys entpacken und vorhandene Dateien ersetzen.

```powershell
Expand-Archive `
  "./GovernancePlattform-v1.0.0-alpha.3.0-metadata-framework.zip" `
  -DestinationPath "." `
  -Force

git status --short
git diff --check
pwsh ./powerplatform/scripts/Build.ps1
```

Danach die erzeugte unmanaged Solution in DEV importieren und den Smoke-Test in
`docs/iterations/v1.0.0-alpha.3.0-metadata-framework.md` durchführen.
