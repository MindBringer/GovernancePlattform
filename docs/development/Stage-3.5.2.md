# Stage 3.5.2

## Inhalt

- Studio-basierte 3.5.1-Canvas-Baseline mit `Systems` und `Office365Users`
- zentrale Berechnung von `gblEditorDirty` und `gblEditorCanSave`
- modale Bestätigung beim Verwerfen ungespeicherter Änderungen
- deaktivierter Speichern-Control während ungültigem oder laufendem Save
- automatische Erhöhung der numerischen Solution-Version bei jedem Build
- Build-Prüfung auf fehlende Datenquellenreferenzen
- Canvas-Anzeigeversion `1.0.0-alpha.3.5.2`

## Build

```powershell
./powerplatform/scripts/Build.ps1
```

Ohne Erhöhung der numerischen Solution-Version:

```powershell
./powerplatform/scripts/Build.ps1 -SkipSolutionIncrement
```

## Test

1. Asset und System öffnen.
2. Lookup und Person auswählen.
3. Feld ändern und Abbrechen klicken.
4. Weiter bearbeiten und Verwerfen testen.
5. Pflichtfeld leeren; Speichern muss deaktiviert sein.
6. Build erneut ausführen; die vierte Solution-Komponente muss steigen.
7. Import prüfen, ohne Systems oder Office365-Benutzer erneut hinzuzufügen.
