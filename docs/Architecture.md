# Governance Portal – Architektur

## Canvas Runtime

Die Canvas-App besteht aus vier Schichten:

1. **Application Foundation** – Initialisierung, Theme, globale Zustände und Fehler-/Busy-Handling.
2. **Shell** – Header, Navigation, Workspace und Footer.
3. **Runtime Metadata** – Objekt-, Feld-, Formular-, Status- und Navigationsdefinitionen aus SharePoint.
4. **Feature Modules** – Assets, Systems, Contacts, Incidents, Problems, Changes, Risks, Controls und Measures.

## Responsive Shell

```text
scrShell
└── conRoot
    ├── conHeader
    ├── conBody
    │   ├── conNavigation
    │   └── conWorkspace
    │       └── conWorkspaceContent
    ├── conFooter
    └── conBusyOverlay
```

Die Navigation ist bei einer App-Breite unter 900 Pixeln kompakt. Alle anderen Bereiche berechnen ihre Maße aus dem Parent-Container.

## Zustandsmodell der Foundation

| Zustand | Zweck |
|---|---|
| `gblInitialized` | Abschluss der App-Initialisierung |
| `gblBusy` | globaler blockierender Ladezustand |
| `gblBusyMessage` | Beschreibung des laufenden Vorgangs |
| `gblCurrentPage` | aktives Modul bzw. Route |
| `gblEnvironment` | sichtbare Zielumgebung |
| `gblUser` | aktueller Power-Apps-Benutzer |
| `gblTheme` | zentrale Farben, Maße und Breakpoints |
