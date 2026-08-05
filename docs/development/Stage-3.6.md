# Stage 3.6 – typisierte Choice- und Person-Provider

## Ziel

Stage 3.6 stabilisiert dynamische Controls in `galEditorFields`, ohne das
Metadatenmodell oder die bestehenden Save-Provider zu verwerfen.

Die Controls verwenden jetzt feldbezogene, typisierte Provider-Collections:

- `colEditorChoiceOptions`
- `colEditorPersonSelections`
- bestehend: `colLookupValues` und `colEditorLookupSelections`

## Person-Provider

`SearchUserV2` wird auf ein stabiles Anzeigeschema normalisiert:

- `DisplayText`
- `SecondaryText`

`Items` und `DefaultSelectedItems` besitzen dadurch dasselbe Schema. Eine
Änderung in einem zweiten Personenfeld führt nicht mehr dazu, dass bereits
gewählte Personen nach einem Gallery-Rerender verschwinden.

Die Rückgabefelder des vorhandenen Connectors werden in PascalCase verarbeitet,
entsprechend dem per JSON geprüften Tenant-Schema.

## Choice-Provider

Choice-Controls lesen nicht mehr direkt aus `colChoiceValues`. Beim Öffnen des
Editors wird je Feld eine Optionsmenge in `colEditorChoiceOptions`
materialisiert. Die Zuordnung erfolgt eindeutig über `EditorFieldKey`.

Damit werden Scope- und Schemafehler zwischen Choice-, Lookup- und
Personencontrols reduziert.

## Test

1. Asset öffnen.
2. Verantwortlich auswählen.
3. Stellvertretung mit einer anderen Person auswählen.
4. Beide Werte müssen sichtbar bleiben.
5. Einen Wert löschen; nur das betroffene Feld darf leer werden.
6. Choice-Felder prüfen.
7. Lookup-Felder prüfen.
8. Abbrechen/Verwerfen prüfen.
9. Speichern und erneutes Öffnen prüfen, soweit der Load-Provider bereits
   verfügbar ist.

## Architekturhinweis

Canvas Apps unterstützen keine dynamische Dereferenzierung beliebiger
Datenquellen oder Controls aus Textmetadaten. Stage 3.6 verwendet daher
typisierte Provider-Collections innerhalb des bestehenden Renderers statt
unterschiedliche physische Datenquellen in einem gemeinsamen Controlschema.
