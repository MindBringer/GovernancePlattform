# Stage 3.6 – typisierte Choice- und Person-Provider

## Ziel

Stage 3.6 stabilisiert dynamische Controls in `galEditorFields`, ohne das Metadatenmodell oder die bestehenden Save-Provider zu verwerfen.

Verwendete Provider-Collections:

- `colEditorChoiceOptions`
- `colEditorPersonSelections`
- `colLookupValues`
- `colEditorLookupSelections`

## Person-Provider

Der in der deutschen Power-Apps-Umgebung eingebundene Connector heißt in Formeln:

```powerfx
'Office365-Benutzer'
```

Die Suche erfolgt über:

```powerfx
'Office365-Benutzer'.SearchUserV2(...).value
```

Das V2-Ergebnis verwendet im aktuellen Connector-Schema camelCase-Felder, unter anderem:

- `displayName`
- `mail`
- `userPrincipalName`
- `jobTitle`
- `department`
- `givenName`
- `surname`
- `city`
- `id`

Für ComboBox und Auswahl-Collection wird das Ergebnis auf ein stabiles Schema normalisiert:

- `DisplayText`
- `SecondaryText`

`Items` und `DefaultSelectedItems` müssen kompatible Anzeigeattribute besitzen. Die eigentliche SharePoint-Personenstruktur wird erst beim Patch aus E-Mail, Claims, Anzeigename, Abteilung und Funktion aufgebaut.

## Bekannter Fehler aus der 3.6.0-Baseline

Die initiale Git-Baseline referenzierte noch `Office365Users` und PascalCase-Rückgabefelder. Das passt weder zum deutschen Datenquellennamen noch zum tatsächlich gebundenen V2-Schema. Folge: `cmbEditorPerson` lieferte keine verwertbaren Anzeigenamen oder E-Mail-Felder.

Der Fix normalisiert deshalb den Connectornamen und die Rückgabefelder vor dem Build. Die statische Referenzprüfung muss künftig beide Fehlerbilder erkennen.

## Choice-Provider

Choice-Controls lesen nicht direkt aus `colChoiceValues`. Beim Öffnen des Editors wird je Feld eine Optionsmenge in `colEditorChoiceOptions` materialisiert. Die Zuordnung erfolgt über `EditorFieldKey`.

## Test

1. Fix-Branch per Git aktualisieren.
2. `pwsh ./powerplatform/scripts/Build.ps1` ausführen.
3. erzeugte unmanaged Solution in DEV importieren und veröffentlichen.
4. Asset öffnen.
5. Verantwortlich auswählen.
6. Stellvertretung mit einer anderen Person auswählen.
7. Beide Werte müssen sichtbar bleiben.
8. Einen Wert löschen; nur das betroffene Feld darf leer werden.
9. Choice- und Lookup-Felder prüfen.
10. Speichern und erneutes Öffnen prüfen.
11. Power Apps App Checker ohne Connector- oder Formelbindungsfehler ausführen.

## Architekturhinweis

Canvas Apps unterstützen keine dynamische Dereferenzierung beliebiger Datenquellen aus Textmetadaten. Stage 3.6 verwendet daher typisierte Provider-Collections innerhalb des gemeinsamen Renderers. Lokalisierte Datenquellennamen gehören zur exportierten App-Bindung und müssen bei einem Studio-Rebind erneut gegen den SourceCode geprüft werden.
