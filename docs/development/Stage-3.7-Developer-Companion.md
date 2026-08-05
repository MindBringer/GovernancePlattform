# Stage 3.7 – Developer Companion

## Einordnung

Stage 3.7 ist eine Entwicklungszwischenstufe. Die Canvas-Funktionalität bleibt auf `1.0.0-alpha.3.6.0`; Stage 3.7 verbessert den Git-, Prüf-, Build- und Testworkflow.

## Ziele

- Änderungen werden direkt in Git-Branches bereitgestellt.
- Lokale Tests beginnen mit `git fetch` und `git pull --ff-only`.
- Wiederkehrende Terminalaktionen werden über eine lokale Weboberfläche gestartet.
- Der Companion führt nur fest definierte Kommandos aus.
- Power-Platform-Import, Veröffentlichung und Studio-Smoke-Test bleiben manuelle Freigabeschritte.

## Funktionsumfang

### Repository

- Branch-, Versions- und Dirty-Status
- Fetch mit Remote-Pruning
- Pull nur als Fast-Forward und nur bei sauberem Arbeitsverzeichnis
- Repository-Audit

### Repository-Audit

Der Audit prüft unter anderem:

- kanonischen Canvas-SourceTree unter `powerplatform/canvas/GovernancePortal/Src`
- zusätzliche oder veraltete Canvas-SourceTrees
- versionierte Build-, Cache-, Log- und Virtual-Environment-Artefakte
- notwendige Basisdateien
- bekannte alte Remote-Branches als manuelle Bereinigungskandidaten

Der Audit löscht nichts automatisch.

### Canvas und Build

- lokalisierte Office-365-Connectorreferenzen prüfen
- Canvas-SourceCode validieren
- vollständigen Build ausführen

## Start

Das Script wird absichtlich über Bash gestartet. Dadurch erzeugt `chmod +x` keine lokale Mode-Änderung, die einen späteren Pull blockiert.

```bash
bash ./start-local.sh
```

Der Server sucht ab Port `8770` automatisch den nächsten freien Port und öffnet den Browser. Ein fester Port kann angegeben werden:

```bash
bash ./start-local.sh 8780
```

Ohne automatischen Browserstart:

```bash
GOVERNANCE_COMPANION_NO_BROWSER=1 bash ./start-local.sh
```

## Testabfolge

1. lokale Änderung am alten `start-local.sh` verwerfen, falls nur durch `chmod` entstanden
2. Branch per Fast-Forward aktualisieren
3. Companion starten
4. Repository-Audit ausführen
5. Connectorprüfung ausführen
6. Canvas validieren
7. vollständigen Build ausführen
8. Solution in DEV importieren und veröffentlichen
9. Person-, Choice- und Lookup-Controls testen
10. Testergebnis im Pull Request dokumentieren

## Sicherheitsgrenzen

- Bindung ausschließlich an `127.0.0.1`
- keine freien Shell-Kommandos
- kein automatischer Commit, Push, Merge oder Solution-Import
- Pull-Abbruch bei lokalen Änderungen
- Audit ohne automatische Löschungen

## Weitere Ausbaustufen

Nach stabiler Nutzung können kontrollierte Aktionen für Commit, Push, PR-Erstellung, Check-Überwachung und Release ergänzt werden. Ein automatischer DEV-Import sollte erst nach klarer Environment- und Connection-Reference-Validierung umgesetzt werden.
