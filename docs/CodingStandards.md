# Governance Portal – Canvas Coding Standards

## Benennung

| Typ | Präfix | Beispiel |
|---|---|---|
| globale Variable | `gbl` | `gblCurrentPage` |
| Collection | `col` | `colNavigation` |
| lokale Kontextvariable | `loc` | `locEditMode` |
| Screen | `scr` | `scrShell` |
| Container | `con` | `conWorkspace` |
| Component | `cmp` | `cmpNavigation` |
| Gallery | `gal` | `galAssets` |
| Form | `frm` | `frmAsset` |
| Button | `btn` | `btnSave` |
| Label | `lbl` | `lblTitle` |
| Text Input | `txt` | `txtSearch` |

## Layout

- Screens erhalten genau einen Root-Container.
- Größen werden aus `Parent`, `App.Width`, `App.Height` oder zentralen Theme-Werten abgeleitet.
- Keine festen Bildschirmgrößen in fachlichen Screens.
- Breakpoints werden zentral in `gblTheme` gepflegt.
- Der Workspace darf Header und Footer nicht überlagern.

## Power Fx

- Globale Zustände nur für appweite Belange verwenden.
- Fachliche Seiteneinstellungen bevorzugt als Kontextvariable führen.
- Datenänderungen mit klarer Fehlerbehandlung ausführen.
- Wiederholte Literale in Theme-, Runtime- oder Definitionsdaten auslagern.
- Formeln so formatieren, dass jede fachliche Operation separat lesbar ist.

## Iterationen

- Pro Iteration genau ein klar abgegrenztes Ziel.
- Vor dem Commit müssen Canvas und Solution erfolgreich gepackt werden.
- Änderungen aus Power Apps Studio werden vor weiterer Quellcodearbeit erneut exportiert und entpackt.
