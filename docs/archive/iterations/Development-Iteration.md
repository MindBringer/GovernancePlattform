# Governance Portal – Ablauf einer Entwicklungsiteration

**Dokumenttyp:** Arbeitsanweisung / Cheat-Sheet  
**Version:** 1.0  
**Status:** Verbindlicher Entwicklungsablauf  
**Zielplattform:** macOS, PowerShell 7, Git, Power Platform CLI

## Ziel

Jede Iteration erzeugt einen nachvollziehbaren, testbaren und reproduzierbaren Stand des Governance Portals. Git ist die führende Quelle. Änderungen im Maker Portal gelten erst nach Export, Unpack und Commit als Bestandteil des Projekts.

## Verzeichnisübersicht

```text
architecture/                       Domänen- und Plattformmodell
provisioning/                       SharePoint-Provisionierung
powerplatform/solution/             entpackte Power-Platform-Solution
powerplatform/canvas/               Canvas SourceCode-Layout für Review/Diffs
powerplatform/canvas-editable/      PAC Experimental-Layout für Pack/Unpack
powerplatform/scripts/              Build-, Pack- und Deployment-Skripte
docs/                               Architektur- und Entwicklungsdokumentation
artifacts/                           lokale Exporte und Build-Ergebnisse; nicht versionieren
```

## 1. Iteration festlegen

Vor Beginn müssen Ziel, Umfang und Abnahmekriterien in `docs/iterations/` beschrieben sein.

Beispiel:

```text
docs/iterations/v1.0.0-alpha.2-app-foundation.md
```

Eine Iteration enthält nur einen fachlich klar abgegrenzten Umfang.

## 2. Repository und Branch vorbereiten

```powershell
git switch main
git pull --ff-only
git status
git switch -c feature/<kurzer-name>
```

Prüfpunkte:

- richtiger Ausgangsbranch
- Working Tree vor Beginn sauber
- keine lokalen Artefakte im Commit
- Branchname beschreibt die Iteration

## 3. Ausgangsstand sichern

Nur erforderlich, wenn die Solution oder Canvas-App seit dem letzten Commit im Maker Portal geändert wurde.

1. Unmanaged Solution aus DEV exportieren.
2. ZIP unter `artifacts/inbound/` ablegen.
3. Solution neu entpacken.
4. Canvas-App in beide Quelllayouts entpacken.
5. Diff prüfen und nur erwartete Änderungen übernehmen.

### Solution entpacken

```powershell
pac solution unpack `
  --zipfile "artifacts/inbound/GovernancePortal_<version>.zip" `
  --folder "powerplatform/solution" `
  --packagetype Unmanaged `
  --allowDelete true `
  --allowWrite true `
  --clobber
```

### Canvas SourceCode-Layout aktualisieren

```powershell
pac canvas unpack `
  --msapp "powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp" `
  --sources "powerplatform/canvas/GovernancePortal" `
  --layout SourceCode `
  --overwrite
```

### Canvas Editable-Layout aktualisieren

```powershell
pac canvas unpack `
  --msapp "powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp" `
  --sources "powerplatform/canvas-editable/GovernancePortal" `
  --layout Experimental `
  --overwrite
```

> `pac canvas pack/unpack` ist ein Übergangsworkflow. Nach jedem Pack muss die App in DEV importiert und im Power Apps Studio validiert werden.

## 4. Entwicklung durchführen

Änderungen erfolgen ausschließlich in den zum Umfang gehörenden Bereichen.

Typische Zuordnung:

| Änderung | Führender Bereich |
|---|---|
| SharePoint-Listen, Felder, Views | `architecture/`, `provisioning/` |
| Canvas-Oberfläche und Power Fx | `powerplatform/canvas-editable/` |
| Solution-Metadaten | `powerplatform/solution/` |
| Build und Deployment | `powerplatform/scripts/`, `.github/workflows/` |
| Architekturentscheidungen | `docs/`, `docs/ADR/` |

Regeln:

- keine direkten Änderungen in exportierten ZIP-Dateien
- keine Zugangsdaten oder benutzerspezifischen Deployment-Werte committen
- keine generierten Logs oder Build-Artefakte committen
- keine unabhängigen Features in derselben Iteration vermischen
- Änderungen an generierten Dateien nur über den vorgesehenen Pack/Unpack-Prozess

## 5. Lokale Validierung

### Git-Diff prüfen

```powershell
git status --short
git diff --check
git diff --stat
git diff
```

### Provisioning und Architektur testen

```powershell
pwsh ./provisioning/Scripts/Test-PowerShellSyntax.ps1
pwsh ./provisioning/Scripts/Test-Architecture.ps1
pwsh ./provisioning/Scripts/Test-ArchitectureConsistency.ps1
```

Alle Tests müssen erfolgreich sein. Warnungen sind zu bewerten und im Iterationsdokument zu dokumentieren.

## 6. Canvas-App packen

Vor dem Pack sicherstellen, dass das Zielverzeichnis existiert:

```powershell
New-Item -ItemType Directory -Force "artifacts/outbound" | Out-Null
```

Editable-Quellen zur MSAPP packen:

```powershell
pac canvas pack `
  --sources "powerplatform/canvas-editable/GovernancePortal" `
  --msapp "powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp"
```

Danach das SourceCode-Layout aus der neu gepackten MSAPP aktualisieren:

```powershell
pac canvas unpack `
  --msapp "powerplatform/solution/CanvasApps/gp_governanceportal_c93a1_DocumentUri.msapp" `
  --sources "powerplatform/canvas/GovernancePortal" `
  --layout SourceCode `
  --overwrite
```

## 7. Solution packen

```powershell
pac solution pack `
  --folder "powerplatform/solution" `
  --zipfile "artifacts/outbound/GovernancePortal_<version>.zip" `
  --packagetype Unmanaged
```

Build-Ergebnis prüfen:

```powershell
Get-Item "artifacts/outbound/GovernancePortal_<version>.zip"
& /usr/bin/unzip -t "artifacts/outbound/GovernancePortal_<version>.zip"
```

## 8. Import und Smoke-Test in DEV

Die gepackte unmanaged Solution in die DEV-Umgebung importieren. Connection References und Environment Variables kontrollieren.

### Pflicht-Smoke-Test

- App startet ohne Formel- oder Ladefehler.
- Startscreen und Navigation werden korrekt angezeigt.
- SharePoint-Datenquellen sind verbunden.
- Runtime-Metadaten werden geladen.
- geänderte Funktion verhält sich gemäß Akzeptanzkriterien.
- Speichern, Bearbeiten und Abbrechen funktionieren, sofern Teil der Iteration.
- Fehler werden verständlich angezeigt.
- Desktop-Browser und schmaler Viewport wurden geprüft.
- bestehende Funktionen zeigen keine Regression.

Testergebnisse im Iterationsdokument festhalten.

## 9. Commit erstellen

Nur geprüfte Dateien stagen:

```powershell
git status --short
git add <geprüfte-pfade>
git diff --cached --check
git diff --cached --stat
git commit -m "<typ>(<bereich>): <beschreibung>"
```

Zulässige Commit-Typen:

```text
feat      neue Funktion
fix       Fehlerkorrektur
refactor  interne Umstrukturierung ohne Funktionsänderung
docs      Dokumentation
test      Tests
build     Build- oder Packprozess
ci        GitHub Actions / Pipeline
chore     technische Wartung
```

Beispiele:

```text
docs(dev): add iteration workflow and roadmap
feat(canvas): add responsive application shell
fix(provisioning): preserve library contents during reset
```

## 10. Push und Pull Request

```powershell
git push -u origin HEAD
```

Der Pull Request enthält mindestens:

- Ziel der Iteration
- umgesetzte Änderungen
- nicht umgesetzte oder verschobene Punkte
- Testschritte und Ergebnis
- bekannte Einschränkungen
- Screenshots bei UI-Änderungen

## 11. Merge, Tag und Abschluss

Nach erfolgreicher Prüfung:

```powershell
git switch main
git pull --ff-only
git tag -a v<version> -m "Governance Portal <version>"
git push origin v<version>
```

Das Iterationsdokument erhält den Status `Abgeschlossen`, das Testdatum und das Ergebnis.

## Definition of Done

Eine Iteration ist abgeschlossen, wenn:

- der vereinbarte Umfang umgesetzt ist
- Architektur- und Syntaxprüfungen erfolgreich sind
- Canvas-App und Solution packbar sind
- Import in DEV erfolgreich ist
- Smoke-Test und Akzeptanzkriterien erfüllt sind
- Dokumentation und Roadmap aktualisiert sind
- keine Geheimnisse oder lokalen Artefakte committed wurden
- Commit und Pull Request nachvollziehbar sind
- ein lauffähiger Stand auf `main` vorliegt

## Schnellablauf

```text
1. main aktualisieren
2. Feature-Branch erstellen
3. Iterationsziel prüfen
4. Änderungen umsetzen
5. Git-Diff und Tests ausführen
6. Canvas packen
7. SourceCode-Layout aktualisieren
8. Solution packen
9. In DEV importieren
10. Smoke-Test durchführen
11. Dokumentation aktualisieren
12. Commit, Push, Pull Request
13. Merge und Tag
```

## Abbruchkriterien

Iteration nicht mergen, wenn:

- Pack oder Import fehlschlägt
- die App nicht startet
- Datenquellen oder Connection References beschädigt sind
- bestehende Kernfunktionen regressiv sind
- Akzeptanzkriterien nicht erfüllt sind
- Änderungen nicht reproduzierbar oder nicht dokumentiert sind
