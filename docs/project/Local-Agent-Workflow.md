# Lokaler Agent-Workflow – GovernancePlattform

Profil **1.2.0**, Adoption 2026-09-17; Quelle `MindBringer/Project-Engineering-Template`, Merge `1555a15baa786f17381c5d9ecd7c2bd0c1050ca6`.

Dieses project-owned Profil gilt für den aktiven Stage-4.1-Entwicklungszweig. Der separate Conformance-PR #6 bleibt DO NOT MERGE; keine Frameworkdateien daraus übernehmen, keinen Lock erzeugen und keine Version erhöhen.

## Operatives Modell

**Sitzungsstart:** Root/Remote/Branch/HEAD/Änderungen und Live-PR/CI prüfen. `AGENTS.md`, vorhandene aktuelle Zustandsquellen und den für das Paket nötigen Ausschnitt der Entwicklungsdokumentation lesen. README-/Stageangaben gegen Branch, Commit, `VERSION` und `powerplatform/VERSION` verifizieren.

**Arbeitspaket:** Ziel, Nicht-Ziele, Datenrisiko, betroffene Architektur-/Canvas-/Providerverträge, Freigaben, relevante Quellen, gezielte Tests und Abschlusskriterien festlegen. `architecture/*.yaml`, Canvasquellen, README/MIGRATION/CHANGELOG/Local-Companion-Doku nur soweit scope-relevant laden.

**Reparaturschleife:** kleinste kohärente Änderung → gezielte Offline-Prüfung → Fehleranalyse/Korrektur. Kein vollständiger Dokumenten-/Gate-Neueinstieg nach jedem Edit.

**Abschluss-Gate:** tatsächlichen Kandidaten vollständig mit den für den Scope verfügbaren Projektprüfungen verifizieren, Diff/Doku prüfen und Handoff erzeugen.

## Semantisches Model Routing

```text
fast               → mechanische, klar lokalisierte, risikoarme Änderung
standard-reasoning → normale Architektur-/Canvas-/Provider-/Test-/Doku-Arbeit
deep-reasoning     → hohe Mehrdeutigkeit, Provider+Canvas+Runtime-Kopplung,
                     Architekturentscheidungen, komplexe Root-Cause, großer Radius
```

Signale: `complexity`, `ambiguity`, `blastRadius`, `crossSubsystem`, `novelty`, `dataRisk`, `failedAttempts`. Keine konkreten Modellnamen persistieren. Nach zwei gleichartigen erfolglosen Reparaturen oder wesentlich größerem Scope Reasoning/Klasse eskalieren; nach drei ohne Erkenntnis Blocker. Stärkeres Modell ersetzt keine PAC-/Studio-/Tenantfreigabe.

Codex/lokal für Repo-Implementierung/Tests; Work für systemübergreifende Recherche/Artefakte; Chat für Scope-/Architektur-/Freigabeentscheidungen.

## Architektur- und Live-Grenzen

- `architecture/*.yaml` bleibt führend; generierte Quellen nicht unabhängig pflegen.
- `powerplatform/canvas/GovernancePortal/` bleibt einziger kanonischer Canvas-SourceTree.
- Provider-Registry, Runtime-Synchronisierung, Personen-/Choice-/Capability-Grenzen erhalten.
- PAC-Pack/Unpack und Studio-Übernahmen nur über Staging, Identitäts-/Artefaktprüfung und Diff-Review; Textedit ist keine Maker-Validierung.
- DEV→Git liest echten Tenant und kann lokale Quellen ersetzen; Git→DEV importiert/veröffentlicht. Beide explizit beauftragt.
- Publish All, Provisioning, Seed, Reset, Import, Deploy separat freigeben. Keine produktiven Inhalte verändern/löschen.
- Keine Credentials, Tenantsettings, unredigierten Personen-/Tenantdaten oder Build-/Log-Artefakte committen.

## Testökonomie

Während Reparaturen kleinste aussagekräftige Prüfungen. Am Paketabschluss aktuelle Skripte/Workflows für den Scope verwenden, typischerweise PowerShell-Syntax, Architecture, ArchitectureConsistency, Canvas-/Providerprüfungen und Build. Vor PAC-/Build-Schritten Toolchain und Seiteneffekte prüfen. Build ist von Import/Publish getrennt.

Fehlendes PowerShell/PAC oder Live-Evidenz als `not run`/`blocked`; Syntax-CI nicht als DEV-Abnahme ausgeben. Identische Prüfungen nicht wegen unterschiedlicher Namen doppeln. Vollständige Logs als Artefakt; Agentenkontext auf Status/Fehlerausschnitte begrenzen.

## Git und Übergabe

Bestehende Änderungen erhalten; kein automatisches Pull/Stash/Reset/Clean. Ein schreibender Agent je Worktree. Nur Aufgaben-Dateien stagen; Commit/Push im beauftragten Umfang, kein Force-Push. Merge/Release/Live-Aktionen separat.

Handoff enthält Kandidat, Diff, Gates, fehlende PAC-/Studio-/Tenant-Evidenz, Freigaben, Git-Zustand und genau ein primäres nächstes Arbeitspaket. Profil-Adoption verändert weder Fachplanung noch Produkt-/Runtime-Freigabe.
