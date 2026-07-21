# Governance Portal – Entwicklungsroadmap

**Status:** Living Document  
**Branching:** Feature Branch → Pull Request → `main`

## Versionslogik

- `alpha`: technische Grundlagen und erste Vertical Slices
- `beta`: vollständige Kernprozesse, Stabilisierung und Berechtigungstests
- `1.0.0`: erste produktionsreife Version

## Geplante Iterationen

| Version | Schwerpunkt | Ergebnis | Status |
|---|---|---|---|
| `v1.0.0-alpha.1` | Entwicklungsprozess und Dokumentationsbasis | verbindlicher Iterationsablauf, Roadmap und Iterationsprotokoll | Bereit zur Prüfung |
| `v1.0.0-alpha.2` | App Foundation | responsiver Shell-Screen, Theme, Header, Navigation, Workspace, Lade- und Fehlerzustände | Geplant |
| `v1.0.0-alpha.3` | Runtime Loader | Laden und Validieren der Runtime-Listen, AppSettings, Texte, Navigation und Statusdarstellung | Geplant |
| `v1.0.0-alpha.4` | Assets Vertical Slice | Übersicht, Suche, Filter, Detail, Neu, Bearbeiten und Speichern | Geplant |
| `v1.0.0-alpha.5` | Systems und Beziehungen | Systemverwaltung sowie Asset-System-Verknüpfung | Geplant |
| `v1.0.0-alpha.6` | Contacts | Kontaktverwaltung und Objektbeziehungen | Geplant |
| `v1.0.0-alpha.7` | Incidents und Problems | Incident-Erfassung, Problemzuordnung und Drill-down | Geplant |
| `v1.0.0-alpha.8` | Changes | Change-Lifecycle und Beziehungen zu Problems, Assets und Systems | Geplant |
| `v1.0.0-alpha.9` | Risks und Controls | Risiko- und Kontrollverwaltung einschließlich Verknüpfungen | Geplant |
| `v1.0.0-alpha.10` | Measures und Dokumente | Maßnahmen sowie Verweise auf Policies, Procedures, Runbooks, Architecture und Evidence | Geplant |
| `v1.0.0-beta.1` | Vollständigkeit und Stabilisierung | CRUD für Kernobjekte, Validierung, Berechtigungen, Fehlerbehandlung und Regressionstests | Geplant |
| `v1.0.0` | Produktivfreigabe | dokumentierte, getestete und deploybare Erstversion | Geplant |

## Leitprinzipien

1. Git ist die führende Quelle für Quellcode und Dokumentation.
2. Provisioning und App verwenden dasselbe Architekturmodell.
3. Runtime-Metadaten steuern Navigation, Formulare und Darstellung, soweit technisch sinnvoll.
4. Jede Iteration endet mit einem importierbaren und getesteten Stand.
5. Bibliotheksinhalte werden durch Reset- und Migrationsprozesse nicht unbeabsichtigt gelöscht.
6. Direkte Maker-Portal-Änderungen werden vor dem Merge exportiert, entpackt und geprüft.

## Nächster Entwicklungsschritt

Nach Abschluss von `v1.0.0-alpha.1` beginnt `v1.0.0-alpha.2 – App Foundation`.
