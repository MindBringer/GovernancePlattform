# Lokaler Agent-Workflow – GovernancePlattform

Profil **1.0.0**, Adoption 2026-09-17; Quelle `MindBringer/Project-Engineering-Template`, Commit `23a4f6acf98c3304276f025e60daccee79f7a12a`, integriert durch Template PR #45.

## Geltungsbereich und Quellen

Dieses project-owned Profil gilt für den aktiven Stage-4.1-Entwicklungszweig. Die separate Runtime-Adoption auf `chore/framework-1.3.12-conformance` ist kein bereits integrierter Framework-Stand. Deren PR #6 trägt ausdrücklich DO NOT MERGE und wird durch diesen Auftrag nicht freigegeben. Keine Frameworkdateien aus diesem Prüfbranch herüberkopieren, keinen Lock erzeugen und keine Version erhöhen.

Vor Änderungen lesen: `AGENTS.md`, dieses Profil, `README.md`, `MIGRATION.md`, `CHANGELOG.md`, `docs/development/Local-Companion-Workflow.md`, relevante `docs/development/`-Dokumente sowie die kanonischen `architecture/*.yaml` und betroffenen Canvas-/Providerquellen. Falls auf einem späteren Branch PROJECT_STATE, Framework-Vertrag, Config und State vorhanden sind, zusätzlich diese lesen. Fehlende Frameworkdateien nicht durch eine erneute Erst-Adoption erzeugen.

README-Stageangaben sind teilweise älter als der aktuelle PR-/Code-Stand. Branch, Commit, VERSION und powerplatform/VERSION sowie Live-PR/CI tatsächlich abgleichen; Provisioning- und Canvas-Version bleiben getrennt. „Weiter“ setzt den belegten nächsten Schritt fort, keine alte Stage allein aufgrund eines Chatverlaufs.

## Lokale Arbeit

Repository-Root, Remote, HEAD/Branch, Upstream und `git status --short --branch` prüfen. Bestehende Änderungen erhalten; kein automatisches Pull, Stash, Reset, Clean oder Branchwechsel darüber. Nicht auf main implementieren. Parallele Aufgaben benötigen eigene Worktrees; nur ein schreibender Agent je Worktree und keine gleichzeitigen Connector-Writes auf demselben Branch.

Scope, Nicht-Ziele, Datenrisiko, Baseline und Abschlusskriterien festhalten → kleinste kohärente Änderung → gezielt testen → Fehler korrigieren → vollständige verfügbare Projektprüfungen → Diff und Dokumentation prüfen. Innerhalb des Auftrags selbstständig iterieren. An Berechtigungs-/Architekturgrenzen oder nach drei gleichen erfolglosen Versuchen ohne neue Erkenntnis mit einem konkreten Blocker stoppen. Keine Tests/Assertions/CI-Gates abschwächen, um Grün zu erzeugen.

AGENTS ist keine technische Berechtigung. Tatsächliche Shell-, Datei-, Netzwerk- und Gitrechte prüfen; Work liest die Regeln ausdrücklich. Keine globale Full-Access-Konfiguration oder Hintergrundautomation einrichten.

## Architektur und Live-Grenze

- `architecture/*.yaml` bleibt führend für das Schema-/Runtime-Metadatenmodell. Generierte Quellen nicht unabhängig pflegen.
- `powerplatform/canvas/GovernancePortal/` bleibt der einzige kanonische Canvas-SourceTree; Solution und .msapp sind kontrollierte Build-/Interchange-Pfade.
- Provider-Registry, Runtime-Synchronisierung, lokale Personen-/Choice-Verträge und Capability-Grenzen erhalten; keine neue parallele Implementierung.
- PAC-Pack/Unpack und Studio-Übernahmen über Staging, Identitäts-/Artefaktprüfung und Diff-Review. Maker-/Studio-Validierung nicht durch einen erfolgreichen Textedit vortäuschen.
- DEV→Git Studio Sync liest einen echten Tenant und kann lokale Quellen ersetzen. Git→DEV importiert/veröffentlicht. Beide sind explizit beauftragte Runbook-Schritte, keine automatischen Tests.
- Publish All ist umgebungsweit; Provisioning/Seed/Reset/Import/Deploy benötigen separate Ziel- und Freigabeprüfung. Keine produktiven Bibliotheksinhalte verändern oder löschen.
- Keine Credentials, lokalen Settings, unredigierten Tenant-/Personendaten oder Build-/Log-Artefakte committen. Synthetische Fixtures verwenden.

## Projektprüfungen

Die vorhandene README dokumentiert aus dem Repository-Root:

```bash
pwsh ./provisioning/Scripts/Test-PowerShellSyntax.ps1
pwsh ./provisioning/Scripts/Test-Architecture.ps1
pwsh ./provisioning/Scripts/Test-ArchitectureConsistency.ps1
pwsh ./powerplatform/scripts/Build.ps1
```

Vor Ausführung der Build-/PAC-Schritte die aktuellen Skripte und benötigten lokalen Werkzeuge prüfen. Build ist von Import/Publish zu trennen. Die aktuellen Workflows unter `.github/workflows/` und zusätzliche Canvas-/Providerprüfungen aus der Entwicklungsdokumentation bleiben verbindlich. Fehlendes PowerShell/PAC oder fehlende Live-Abnahme offen als `not run`/`blocked` ausweisen; reine Syntax-CI ist kein vollständiger fachlicher oder DEV-Nachweis.

Den tatsächlichen Änderungskandidaten prüfen. Ein neuer Worktree aus HEAD enthält uncommitted Änderungen und neue Dateien nicht: genehmigten lokalen Checkpoint oder isolierte Kopie des vollständigen aufgabenbezogenen Diffs verwenden. Commit oder Basis plus Diff-/Dateihashes, Befehl, Exit-Code, Tests/Skips und CI-Head dokumentieren.

## Git und Übergabe

Nur Aufgaben-Dateien stagen. Commit/Push im beauftragten Umfang; vor Push Remote-/Zielzustand erneut prüfen, kein force-push/History-Rewrite. Merge, Release/Tag und Live-Aktionen getrennt freigeben. Nur eigene Prozesse beenden.

Handoff: Kandidat, Diff, tatsächlich ausgeführte Prüfungen, fehlende PAC-/Studio-/Tenant-Evidenz, lokale Änderungen und genau ein nächster Schritt. Das Profil verändert weder die laufende Fachplanung noch eine bestehende Produkt-/Runtime-Freigabe.
