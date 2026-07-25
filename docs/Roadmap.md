# IT Governance Portal – Roadmap

**Arbeitsmodell:** Feature Branch → Pull Request → `main`  
**Provisioning-Baseline:** `6.2.5`  
**Canvas-Baseline:** `1.0.0-alpha.3.4.1`

## Abgeschlossene Grundlagen

| Bereich | Ergebnis | Status |
|---|---|---|
| Provisioning 6.2.5 | 50 Listen/Runtime-Strukturen, konsistente Rollen- und Feldreferenzen, DryRun- und Architekturprüfungen | abgeschlossen |
| Canvas Foundation | responsiver Shell-Screen, Theme, globale Zustände und Runtime-Bootstrap | abgeschlossen |
| Stage 3.1–3.2 | dynamischer Editor, typisierte Editorwerte, Renderer und Choice-Provider | abgeschlossen |
| Stage 3.3 | Lookup-Registry, Cache, Lazy Loading und Person-Provider | abgeschlossen |
| Stage 3.4 | Person-/Lookup-Persistenz und Versionierung | abgeschlossen |
| Stage 3.4.1 | selbsttragender SourceCode-Build und Save-Provider für Assets/Systems | abgeschlossen |

## Aktuelle Iteration – Stage 3.5 Stabilisierung

| Inkrement | Ziel | Status |
|---|---|---|
| 3.5.1 Editor-Lifecycle | `colEditorLookupSelections` und `colEditorPersonSelections`, korrekte DefaultSelectedItems, Vorbereitung auf Mehrfachauswahl | als Nächstes |
| 3.5.2 Zentrale Validierung | wiederholte Dirty-/CanSave-Logik durch zentralen FieldChanged/ValidateField/ValidateEditor-Ablauf ersetzen | geplant |
| 3.5.3 Save-Provider | Incidents, Problems, Changes, Risks, Controls, Measures und Contacts ergänzen | geplant |
| 3.5.4 Stabilität | konsistente Fehlerbehandlung, Save-Progress, Abbruch-/Dirty-Dialog und Regressionstests | geplant |

## Stage 4 – Navigation, Details und Beziehungen

- generische Objektlisten mit Suche, Filter und Saved Views
- generische Detailansicht
- Relation Engine auf Basis von `GovernanceRelations`
- Drill-down zwischen Asset, System, Incident, Problem, Change, Risk und Control
- berechtigungsgesteuerte Aktionen

## Stage 5 – Prozesse und Dokumente

- Lifecycle-Aktionen und Freigaben
- Integration generischer Power-Automate-Flows
- Verknüpfung von Policies, Procedures, Runbooks, Architecture und Evidence
- Benachrichtigungen, Timeline, Aufgaben und Reviews
- Reporting und Governance-Dashboards

## Beta und Release 1.0

### `1.0.0-beta.1`

- vollständiges CRUD der Kernobjekte
- getestete Relation- und Lifecycle-Funktionen
- Rollen-/Berechtigungstests
- Fehler-, Performance- und Regressionstests
- dokumentierter Deployment- und Recovery-Prozess

### `1.0.0`

- produktionsfähige unmanaged/managed Release-Pakete
- freigegebene Architektur- und Betriebsdokumentation
- nachvollziehbare Migration von der Baseline
- Abnahme der Kernprozesse und Bibliotheksintegrationen

## Leitplanken

1. Jede Iteration endet mit einem validierbaren und importierbaren Stand.
2. Git bleibt führend für Code und Dokumentation.
3. Runtime-Metadaten werden nur dort verwendet, wo Power Apps sie zuverlässig auswerten kann.
4. Direkte Maker-Portal-Änderungen werden immer zurück nach SourceCode synchronisiert.
5. Neue Funktionen dürfen die idempotente Provisionierung und den Erhalt der Dokumentbibliotheken nicht gefährden.
