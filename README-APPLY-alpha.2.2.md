# Anwendung v1.0.0-alpha.2.2

Dieses Paket im Repository-Stamm entpacken und vorhandene Dateien überschreiben.

```powershell
Expand-Archive ./GovernancePlattform-v1.0.0-alpha.2.2-visible-shell.zip -DestinationPath . -Force
pwsh ./powerplatform/scripts/Build.ps1
```

Danach die erzeugte unmanaged Solution in DEV importieren und den Smoke-Test unter `docs/iterations/v1.0.0-alpha.2.2-visible-shell.md` durchführen.

Vor dem Commit:

```powershell
git status --short
git diff --check
git add powerplatform docs
git commit -m "feat(canvas): add visible responsive application shell"
git push
```
