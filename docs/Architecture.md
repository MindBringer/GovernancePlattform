# IT Governance Portal – Architektur

## 1. Zielbild

Das Portal stellt Governance-Objekte wie Assets, Systems, Contacts, Incidents, Problems, Changes, Risks, Controls und Measures in einer gemeinsamen, metadatengetriebenen Plattform bereit. SharePoint Online dient als Daten- und Dokumentenbasis; Power Apps bildet die Benutzeroberfläche; PowerShell provisioniert und prüft die Umgebung.

## 2. Architekturprinzipien

1. **Metadata first:** Objekt-, Feld-, Choice-, Status-, Formular-, View-, Relations- und Berechtigungsdefinitionen werden zentral in `architecture/*.yaml` gepflegt.
2. **Ein kanonischer SourceTree:** Canvas-Quellcode liegt ausschließlich unter `powerplatform/canvas/GovernancePortal`.
3. **Idempotentes Provisioning:** Wiederholte Läufe erzeugen keine unkontrollierten Duplikate und verändern bestehende Inhalte nur nach definierten Regeln.
4. **Trennung von Code und Artefakten:** Git enthält Quellen; Logs, Pakete und temporäre Build-Ausgaben entstehen unter ignorierten Artefaktpfaden.
5. **Explizite Migration:** Inkompatible Feldänderungen werden nicht stillschweigend durchgeführt, sondern über versionierte Migrationsregeln behandelt.

## 3. Schichten und Verantwortlichkeiten

### 3.1 Architekturmodell

| Datei | Verantwortung |
|---|---|
| `platform.yaml` | Objekttypen, Basisklassen, technische Objekte und Navigation |
| `fields.yaml` | wiederverwendbare physische Felddefinitionen |
| `object-fields.yaml` | objektbezogene Felder und UI-Metadaten |
| `choices.yaml` | kontrollierte Wertebereiche |
| `status-models.yaml` | Lifecycle- und Statusmodelle |
| `relations.yaml` | zulässige Beziehungstypen |
| `forms.yaml` | dynamische Formulare und Abschnitte |
| `views.yaml` | SharePoint- und Canvas-Ansichten |
| `workflows.yaml` | generische Workflow-Konfiguration |
| `permissions.yaml` | Rollen und Anwendungscapabilities |
| `canvas-runtime.yaml` | Canvas-spezifische Runtime-Konfiguration |
| `ai.yaml` | kontrollierte KI-Skills und Prompt-Metadaten |

### 3.2 Provisioning

`provisioning/Provision-GovernancePlatform.ps1` lädt das Architekturmodell, kompiliert es, validiert Referenzen und provisioniert die SharePoint-Strukturen. Module unter `provisioning/Modules/` trennen Compiler, Schema, Migration, Cleanup, Reporting und Validierung.

Wesentliche Betriebsmodi:

- DryRun und Architekturprüfung
- additive Provisionierung
- explizite Migration
- Reset von Listeninhalten bei Erhalt der Dokumentbibliotheken
- Export von Inventar, Schema und Assessment-Artefakten

### 3.3 SharePoint Runtime

Die Plattform enthält fachliche Listen, Dokumentbibliotheken und technische Runtime-Listen. Die Canvas-App liest insbesondere ObjectTypes, FieldDefinitions, FormDefinitions, ViewDefinitions, StatusModels, ChoiceValues, RelationTypes und PermissionDefinitions.

Die Bibliotheken Policies, Procedures, Runbooks, Architecture und Evidence bleiben von Listen-Resets getrennt, damit bereits erzeugte Dokumente erhalten werden.

### 3.4 Canvas App

Die Canvas-App besteht aus vier logischen Schichten:

1. **Application Foundation:** Initialisierung, Theme, globale Zustände, Busy- und Fehlerbehandlung.
2. **Responsive Shell:** Header, Navigation, Workspace, Footer und Overlay.
3. **Metadata Runtime:** Loader und Provider für Objekte, Felder, Formulare, Choices, Lookups und Personen.
4. **Feature-/Save-Provider:** objektspezifische Persistenz und spätere Relations- sowie Prozessfunktionen.

Aktuell implementiert sind die Foundation, der dynamische Renderer, Choice-Provider, Lookup-Registry/Cache/Lazy Loading, Office365Users-Personensuche sowie Save-Provider für Assets und Systems. Der Quellcode trägt die Version `1.0.0-alpha.3.4.1`.

Responsive Shell:

```text
scrShell
└── conRoot
    ├── conHeader
    ├── conBody
    │   ├── conNavigation
    │   └── conWorkspace
    ├── conFooter
    └── conBusyOverlay
```

### 3.5 Build und ALM

```text
Canvas SourceCode (*.pa.yaml)
        ↓ Validate-CanvasSource.ps1
pac canvas pack
        ↓
Canvas .msapp
        ↓ in entpackte Solution übernehmen
pac solution pack
        ↓
importierbare unmanaged Solution
```

`powerplatform/scripts/Build.ps1` synchronisiert Versionen, validiert den SourceTree, packt Canvas und Solution und legt die Ausgabe unter `artifacts/outbound/` ab.

## 4. Beziehungskonzept

`GovernanceRelations` ist das langfristig kanonische Beziehungsmodell. Direkte Lookup-Felder können als fachlich sinnvolle oder vorübergehende Kompatibilitätsfelder bestehen bleiben. Stage 4 ergänzt die generische Relation-Navigation und Drill-downs, beispielsweise:

- Asset ↔ System
- Incident → Problem
- Problem → Change
- Risk → Asset/System
- Control ↔ Risk

## 5. Sicherheits- und Berechtigungsmodell

Berechtigungen werden über `permissions.yaml`, SharePoint-Gruppen/Rollen und Runtime-Capabilities definiert. Die Canvas-App soll Funktionen nicht nur visuell verbergen, sondern vor Aktionen die erforderliche Capability prüfen. Technische Konten und Connection References werden getrennt von persönlichen Maker-Verbindungen betrieben.

## 6. Versionsmodell

- `VERSION`: Provisioning-/Architekturpaket, aktuell `6.2.5`
- `powerplatform/VERSION`: Canvas-/Solution-Version, aktuell `1.0.0-alpha.3.4.1`
- `powerplatform/scripts/DeveloperPlatform.psd1`: muss dieselbe Canvas-Version tragen
- Solution.xml: numerische, aus SemVer abgeleitete Version

## 7. Noch offene Architekturarbeit

- zentraler Editor-Lifecycle für Lookup- und Personenauswahl
- zentrale Feld- und Formularvalidierung
- Save-Provider für weitere Kernobjekte
- generische Objektlisten und Detailansichten
- Relation Engine und konsistente Drill-down-Navigation
- Berechtigungs- und Regressionstests
- kontrollierte Power-Automate-Integration für Lifecycle-Prozesse
