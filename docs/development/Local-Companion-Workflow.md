# Lokaler Git- und Companion-Workflow

## Ziel

Entwicklungsstände werden nicht mehr als ZIP verteilt. Änderungen werden in GitHub-Branches bereitgestellt und lokal per Fast-Forward aktualisiert. Tests und Builds können über eine kleine lokale Weboberfläche gestartet werden.

## Erstmalige Einrichtung

```bash
git clone https://github.com/MindBringer/GovernancePlattform.git
cd GovernancePlattform
chmod +x start-local.sh
```

Voraussetzungen: Git, Python 3, PowerShell 7 und Power Platform CLI.

## Branch testen

```bash
git fetch origin
git switch --track origin/<branch>
./start-local.sh
```

Bei bereits vorhandenem lokalen Branch:

```bash
git switch <branch>
git pull --ff-only
./start-local.sh
```

Die Oberfläche ist unter `http://127.0.0.1:8765` erreichbar.

## Aktionen

- **Status:** aktueller Branch und lokale Änderungen
- **Fetch:** Remote-Referenzen aktualisieren und gelöschte Referenzen entfernen
- **Pull --ff-only:** nur bei sauberem Arbeitsverzeichnis; keine automatischen Merge-Commits
- **Connector-Referenzen prüfen:** lokalisierte Office-365-Personenreferenzen prüfen
- **Canvas validieren:** SourceCode-Prüfung starten
- **Vollständigen Build starten:** Version, Canvas-Pack, Referenzprüfung und Solution-Pack

## Sicherheitsgrenzen

Der Companion bindet ausschließlich an `127.0.0.1`. Die API akzeptiert nur fest codierte Aktionen und keine freien Shell-Kommandos. `pull` wird bei lokalen Änderungen abgebrochen. Commit, Push, PR und Merge bleiben in der ersten Ausbaustufe bewusst manuelle Schritte.

## Empfohlener Freigabeablauf

1. Branch per Git aktualisieren.
2. Status prüfen.
3. Connector-Referenzen und Canvas validieren.
4. Vollständigen Build ausführen.
5. Solution in DEV importieren und veröffentlichen.
6. Smoke-Test gemäß Iterationsdokument durchführen.
7. Testergebnis im Pull Request dokumentieren.
8. Erst danach nach `main` mergen.

Eine spätere Ausbaustufe kann analog zum Cashflow-Portfolio PR-Erstellung, Check-Überwachung und kontrolliertes Release ergänzen. Für Power-Platform-Artefakte bleibt der Import- und Studio-Smoke-Test jedoch ein verpflichtendes manuelles Gate.
