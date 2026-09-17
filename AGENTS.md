# Agent / Assistant Working Contract – GovernancePlattform

<!-- local-agent-workflow: 1.2.0 -->
## Verbindlicher Einstieg

1. Bei neuer Profilversion `docs/project/Local-Agent-Workflow.md` lesen.
2. Tatsächlichen Git-/PR-/CI-Stand und den aktiven Stage-4.1-Entwicklungsbranch prüfen.
3. Aktuelle Zustandsquellen lesen, sofern auf dem Branch vorhanden; Chatverlauf allein ist keine Source of Truth.
4. Architektur-/Canvas-/Providerquellen und Entwicklungsdokumente nur soweit für das aktive Arbeitspaket relevant laden.
5. Semantische Modellklasse nach tatsächlicher Paketkomplexität wählen.
6. Vollständige verfügbare Projekt-Gates am Paketabschluss, nicht nach jedem Reparaturversuch.
7. Genau den belegten primären nächsten Projektschritt als Default-Scope verwenden.

- Lokal-first: Sitzungsstart → Arbeitspaket → gezielte Reparaturschleife → Abschluss-Gate → Handoff.
- Aktuellen Entwicklungsbranch erhalten, `main` nicht direkt bearbeiten. Vorhandene Änderungen nicht durch Pull/Stash/Reset/Clean/Branchwechsel verdrängen.
- Ein schreibender Agent je Worktree; Connector und lokaler Agent schreiben nicht gleichzeitig denselben Branch.
- Tatsächlichen Kandidaten einschließlich neuer/uncommitted Dateien prüfen.
- Modellklasse `fast`, `standard-reasoning` oder `deep-reasoning`; erst anhand belegter Komplexität/Fehlschläge eskalieren.
- Commit/Push nur im beauftragten Umfang; Merge/Release/Live-Writes separat. `weiter` autorisiert nur das belegte Arbeitspaket.

## Projektspezifische Grenzen

- `architecture/*.yaml` ist führend für Schema und Runtime-Metadaten.
- `powerplatform/canvas/GovernancePortal/` ist der einzige kanonische Canvas-SourceTree; Build-/Staging-/Interchange-Artefakte sind keine zweite Bearbeitungsquelle.
- Provisioning-Version in `VERSION` und Canvas-/Solution-Version in `powerplatform/VERSION` getrennt halten.
- Provider-/Personen-/Choice-/Capability-Verträge erhalten; keine fachlichen Refactorings allein wegen des Arbeitsmodus.
- Keine automatische Provisionierung, Seed-/Reset-Aktion, DEV-Übernahme, Import, Publish All oder Deployment. DEV→Git ebenfalls nur ausdrücklich beauftragt.
- Keine Secrets, Tenantsettings, persönlichen Daten, Logs oder Build-Ausgaben committen; synthetische/redigierte Fixtures.
- Fehlende PAC-/PowerShell-/Studio-/Tenant-Evidenz offen ausweisen; Offline-Prüfung ist keine Live-Abnahme.

## Framework-Status

Profil und Framework-Runtime bleiben getrennt. Der separate Conformance-PR #6 bleibt gesperrt und wird nicht implizit integriert. Keine Framework-Locks oder Runtimeversionen für diese Profil-Adoption erzeugen.

AGENTS erteilt keine technische Berechtigung. Keine globalen Full-Access-Settings oder Hintergrundaufgaben.

## Abschluss

Geänderte Dateien, Kandidat, Gates/Exit-Codes, CI-Head, Skips/Blocker, Freigaben und Git-Zustand dokumentieren. Genau ein primäres nächstes Arbeitspaket hinterlassen. Keine Tests abschwächen, um Grün zu erzeugen.
<!-- /local-agent-workflow -->
