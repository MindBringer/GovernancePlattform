# Lokaler Git- und Companion-Workflow

## Ziel

Entwicklungsstände werden nicht mehr als ZIP verteilt. Änderungen werden in GitHub-Branches bereitgestellt und lokal per Fast-Forward aktualisiert. Tests und Builds können über den Governance Developer Companion gestartet werden.

## Voraussetzungen

Git, Python 3, PowerShell 7 und Power Platform CLI.

## Branch testen

```bash
git fetch origin
git switch --track origin/<branch>
bash ./start-local.sh
```

Bei bereits vorhandenem lokalen Branch:

```bash
git switch <branch>
git pull --ff-only
bash ./start-local.sh
```

`start-local.sh` wird bewusst über Bash gestartet. Ein vorheriges `chmod +x` ist nicht nötig und kann auf Systemen mit versioniertem Dateimodus eine lokale Änderung erzeugen, die den nächsten Pull blockiert.

## Port und Browser

Ohne Parameter sucht der Companion ab Port `8770` automatisch den nächsten freien Port und öffnet den Browser.

Fester Port:

```bash
bash ./start-local.sh 8780
```

Ohne automatischen Browserstart:

```bash
GOVERNANCE_COMPANION_NO_BROWSER=1 bash ./start-local.sh
```

## Aktionen

- **Status:** Branch und lokale Änderungen
- **Fetch:** Remote-Referenzen aktualisieren und gelöschte Referenzen entfernen
- **Pull --ff-only:** nur bei sauberem Arbeitsverzeichnis
- **Repository-Audit:** doppelte SourceTrees und versionierte Altlasten prüfen
- **Connector prüfen:** lokalisierte Office-365-Personenreferenzen prüfen
- **Canvas validieren:** SourceCode-Prüfung starten
- **Vollständigen Build starten:** Versionierung, Canvas-Pack, Referenzprüfung und Solution-Pack

## Lokale Änderung vor dem ersten Pull beseitigen

Falls `start-local.sh` ausschließlich durch `chmod +x` verändert wurde:

```bash
git restore start-local.sh
git pull --ff-only
bash ./start-local.sh
```

Vor `git restore` kann die Änderung geprüft werden:

```bash
git diff --summary -- start-local.sh
git diff -- start-local.sh
```

## Sicherheitsgrenzen

Der Companion bindet ausschließlich an `127.0.0.1`. Die API akzeptiert nur fest definierte Aktionen und keine freien Shell-Kommandos. Pull wird bei lokalen Änderungen abgebrochen. Repository-Audit, Commit, Push, PR, Merge und Power-Platform-Import verändern nicht ungefragt produktive Systeme; Audit ist rein lesend.

## Freigabeablauf

1. Branch aktualisieren.
2. Repository-Audit ausführen.
3. Connectorprüfung und Canvas-Validierung ausführen.
4. vollständigen Build ausführen.
5. Solution in DEV importieren und veröffentlichen.
6. Smoke-Test gemäß Iterationsdokument durchführen.
7. Testergebnis im Pull Request dokumentieren.
8. Erst danach nach `main` mergen.

Die fachliche Spezifikation der Zwischenstufe steht unter [Stage 3.7 – Developer Companion](Stage-3.7-Developer-Companion.md).
