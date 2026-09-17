# Agent / Assistant Working Contract – GovernancePlattform

<!-- local-agent-workflow: 1.0.0 -->
## Verbindlicher Einstieg

Vor jeder Implementierung `docs/project/Local-Agent-Workflow.md` vollständig lesen. Anschließend die dort genannten bestehenden Entwicklungsdokumente, die betroffenen kanonischen Architektur-/Canvasquellen und den tatsächlichen Git-/PR-/CI-Stand prüfen. Chatverlauf allein ist keine Source of Truth.

- Lokal-first im explizit geöffneten Repository arbeiten: Scope/Baseline → Änderung → Tests → Fehlerkorrektur → vollständiger verfügbarer Gate → Diff/Doku/Handoff.
- Aktuellen Entwicklungsbranch erhalten, main nicht direkt bearbeiten. Vorhandene Änderungen nicht durch Pull, Stash, Reset, Clean oder Branchwechsel verdrängen.
- Ein schreibender Agent je Worktree. Parallele Tasks in getrennten Worktrees; Connector und lokaler Agent schreiben nicht gleichzeitig denselben Branch.
- Tatsächlichen Kandidaten einschließlich neuer/uncommitted Dateien prüfen; ein Worktree aus altem HEAD ist kein entsprechender Testnachweis.
- Commit/Push nur im beauftragten Umfang, Merge/Release/Live-Writes separat. „Weiter“ autorisiert nur den belegten nächsten Projektschritt.

## Projektspezifische Grenzen

- `architecture/*.yaml` ist führend für Schema und Runtime-Metadaten.
- `powerplatform/canvas/GovernancePortal/` ist der einzige kanonische Canvas-SourceTree; kontrollierte Build-/Staging-/Interchange-Artefakte sind keine zweite Bearbeitungsquelle.
- Provisioning-Version in VERSION und Canvas-/Solution-Version in powerplatform/VERSION getrennt halten.
- Provider-/Personen-/Choice- und Capability-Verträge erhalten; keine fachlichen Refactorings allein wegen des neuen Arbeitsmodus.
- Keine automatische Provisionierung, Seed-/Reset-Aktion, DEV-Übernahme, Import, Publish All oder Deployment. Auch DEV→Git braucht einen ausdrücklich beauftragten Schritt und darf lokale Quellen nicht ungeprüft ersetzen.
- Keine Secrets, lokale Tenantsettings, persönlichen Daten, Logs oder Build-Ausgaben committen. Nur synthetische/freigegeben redigierte Fixtures.
- Fehlende PAC-/PowerShell-/Studio-/Tenant-Evidenz offen ausweisen. Offline-Syntaxprüfungen und echte fachliche/live Abnahme nicht gleichsetzen.

## Framework-Status

Das lokale Entwicklungsprofil ist unabhängig von der Framework-Runtime adoptiert. Der separate Conformance-PR #6 bleibt gesperrt und wird nicht implizit integriert. Vorhandene Framework-Verträge auf anderen Branches lesen, aber keine Framework-Locks oder Runtimeversionen für diese Dokumentations-Adoption neu erzeugen.

AGENTS ist keine Sandbox-/Netzwerk-/Git-/Tenantfreigabe. Work muss die Regeln ausdrücklich lesen; automatische Übernahme wird nicht vorausgesetzt. Keine globalen Full-Access-Settings oder Hintergrundaufgaben einrichten.

## Abschluss

Geänderte Dateien, getesteten Kandidaten, Befehle/Exit-Codes, CI-Head, Skips/Blocker und lokale Änderungen dokumentieren. Aktive Entwicklungsdokumentation entsprechend der tatsächlich erreichten Facharbeit pflegen und genau einen nächsten Schritt hinterlassen. Keine Tests abschwächen, um Grün zu erzeugen.
<!-- /local-agent-workflow -->
