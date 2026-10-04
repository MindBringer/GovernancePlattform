# P1 – Systembeschreibung und sichtbare Speicherfehler

Stand: 2026-10-04 · `codex/stage41-p1` · [Draft #17](https://github.com/MindBringer/GovernancePlattform/pull/17) · Modellklasse `deep-reasoning`.

## Ergebnis und Ursache

Der lokale **Quellenkandidat 30445** erhält die fachliche Beschreibung über eine eigene Systems-Spalte `SystemDescription`, Anzeige **Beschreibung**, Typ Note/Plain Text. Load, Formularfilter und Patch verwenden denselben Namen; der Systemumfang bleibt 16, Asset 17 Felder. Originale native Patch-Basisrecords, unveränderte Personenobjekte, Choices, positive/leere Lookup-Referenzen und Modified-/Conflict-Prüfung bleiben erhalten.

Die lesende native Prüfung mit dem bestehenden Testkonto belegt für `Systems.Description`: `TypeAsString=Note`, `ReadOnlyField=true`, `Sealed=true`, `Hidden=false`, `FromBaseType=false`; SchemaXml nennt die SharePoint-Feldquelle und Gruppe `_Hidden`. Die Spalte erscheint nicht in der Liste bearbeitbarer Systemspalten. Der gepackte/publizierte Connector-Schreibschutz entspricht also dem nativen Schema. Seine konkrete ursprüngliche Provisionierungshistorie ist damit nicht bewiesen. ReadOnly/Sealed oder Connector-Permissions werden nicht umgestellt. Die bestehende Description-Spalte, ihre Werte und ihr Architekturvertrag bleiben erhalten; andere Provider werden nicht umgebaut.

`App.OnError` übernimmt unhandled Errors auch auf der Editorseite nach Rücksetzen von SaveBusy. Die konkrete Meldung bleibt sichtbar und sperrt erneutes Speichern bei unklarem Ausgang für New und Edit. Das Fehlerlabel wächst, kündigt Fehler über Live.Assertive an und verschiebt die Formularfelder entsprechend seiner Höhe. Die Prüfung belegt die tatsächlichen lokalen Formeln; sichtbares Host-/Screenreaderverhalten ist noch in DEV zu prüfen. Microsoft beschreibt App.OnError als Behandlung unhandled Errors, die nach Fehlerbehandlung innerhalb der Formel verbleiben ([Fehlerbehandlung](https://learn.microsoft.com/en-us/power-platform/power-fx/error-handling)); aus dem lokalen Busy-Zeitfenster folgt kein abschließender Nachweis des historischen Host-Ablaufs.

**DEV bleibt 30444 / Canvas 193 Live. Keine Live-Writes, kein Import, Publish, globales Provisioning/Seed oder DEV→Git in diesem Reparaturpaket.** Die bisherigen Diagnosekontingente Create/Edit/Delete je 1/1 sind abgeschlossen und bereinigt.

## Lokale Prüfungen und tatsächliche Grenze

- Der tatsächliche Architekturcompiler und Metadatengenerator ergeben ausschließlich **eine zusätzliche Systems-Note-Spalte und zwei zusätzliche Runtimezeilen**. Alle bestehenden Schemafelder und **1.016 Metadatenzeilen** sind unverändert. Der echte XML-Generator verwendet den neuen internen Namen, Plain Text und keine ReadOnly-/Sealed-Attribute. Der Plan wird offline mit `Test-SystemDescriptionContract.ps1 -PlanPath <ignorierter Pfad>` erzeugt; keine Authentifizierung oder PnP-Aufrufe.
- Die tatsächlichen Record-Formeln prüfen die eigene Beschreibung einschließlich unverändertem Titel-Edit, mehrzeiligem Text und explizitem Leeren. Der echte Power-Fx-Interpreter führt App.OnError für späte New-/Edit-Fehler, Busy-Fehler und reine Listenfehler aus; Guards, Fehlervorrang und Formularversatz werden ausgewertet. Personen-/Choice-/Lookup-/Konfliktregressionen bleiben erhalten.
- Neun synthetische Connector-Regressionen prüfen read-only aus 30444, fehlendes neues Feld, fehlende Permission, falsche Tabelle, doppelte/nicht schreibbare Quellen, echte Patch-Top-Level-Felder und Studio-ZIP-Pfadseparatoren. Keine Tenant-/Personenfixture versioniert.
- `Validate-CanvasReferences.ps1` prüft nach dem Pack zusätzlich alle **33 tatsächlichen Patch-Spalten** im kanonischen Referenzpaket und im gepackten msapp. Das Gate ändert keine Permission. Vor der Quellkorrektur scheitert es am echten `Systems.Description/read-only`; danach an der noch fehlenden `Systems.SystemDescription`-Referenz.
- **PAC 2.9.3 SourceCode-Pack und Unpack Exit 0**, vier kanonische YAMLs im Round-Trip identisch. **Vollständiger Build Exit 1** am neuen Schreibvertrags-Gate, bevor Pack-Solution ausgeführt wird. Die lokale Solution-Manifestversion ist 1.0.0.30445; Canvas bleibt 1.0.0-alpha.4.1.0, Provisioning 6.2.5. Der gepackte Quellenkandidat ist **kein importfähiger/abgenommener Deploymentkandidat**; kein 30445-Deployment-ZIP erzeugt. Das generierte Referenzpaket bleibt unverändert.

**Abschlusslauf: 19/20 Projekt-Gates Exit 0; ausschließlich Connector-Referenzen / Exit 1.** 770 tatsächliche Power-Fx-Assertions (137 Capability + 212 Choice + 421 Record Core, davon 45 zusätzliche Record-Assertions), 56 Formeln geparst; 13 Python-Regressionen (4 YAML + 9 Connector) Exit 0. Architecture/Consistency, Syntax, Asset-/System-Title, additive Beschreibung, Canvas, Accessibility, Registry/Runtime, Person, Artefaktidentität, Audit und Diff bestehen. Build / Exit 1 ist dieselbe belegte fehlende Referenz; Pack/Unpack jeweils Exit 0.

msapp-Quellenkandidat SHA-256: `6d500a037f8de5ad247f38020be154be7723d1c6c096912bc899c2e3a3b5dca5`. Gegenüber 30444 ändern sich im msapp ausschließlich die zwei bearbeiteten YAMLs und packed.json; Connector-Referenzen sind bytegleich. Das kanonische msapr bleibt SHA-256 `c82fbc03334753a72a8eb43bbe274fd96ef17fbf221b779f82a291e054fd2528`. Kein neuer Solution-ZIP-Hash, da Pack-Solution durch das Gate gestoppt wurde.

Der vollständige Abschlusslauf, tatsächliche Exit-Codes, msapp-SHA, Git-/CI-Head und fehlende Werkzeuge stehen im ignorierten Handoff unter `artifacts/p1-20261002/repair-description-20261004/`. Die Checks dieser PR validieren Quellen und synthetische/Compiler-Verträge; ein grüner CI-Head hebt die Build-Sperre nicht auf. Pester fehlt und PAC canvas validate ist nicht verfügbar; Offline-Pack ist keine Maker-/Tenant-Abnahme.

## Genau ein primäres nächstes Arbeitspaket

**P1 · DEV-Voraussetzung für SystemDescription und erzeugte Connector-Referenz herstellen.** Diese Vorbereitung benötigt eine neue konkrete Freigabe nach [AGENTS.md](../../AGENTS.md): „Keine automatische Provisionierung, Seed-/Reset-Aktion, DEV-Übernahme, Import, Publish All oder Deployment. DEV→Git ebenfalls nur ausdrücklich beauftragt.“ Das aktuelle `weiter` beauftragt die lokale Reparatur; die Vorbereitung schreibt Schema/Runtime-Metadaten und aktualisiert einen DEV-Draft.

Der konkret vorbereitete Umfang ist:

1. Native `Systems.SystemDescription` lesen. Bei Abwesenheit ausschließlich diese eine Note-Spalte nach dem Architektur-XML anlegen: Name/StaticName `SystemDescription`, DisplayName Beschreibung, Required/Indexed/EnforceUniqueValues false, NumLines 8, RichText false. Bei bereits vorhandener Spalte nur bei exakt passendem Typ, Anzeige und schreibbaren/unversiegelten Attributen weiter; sonst stoppen. Keine Änderung an Description, Liste/Inhaltstyp, Rollen oder anderen Feldern.
2. Ausschließlich die folgenden zwei **neuen** Runtimezeilen aus dem tatsächlichen offline generierten Plan anlegen. Existierende identische Zeilen überspringen; abweichende oder doppelte Zeilen stoppen statt überschreiben. Genau zwei mögliche Metadatenneuanlagen, alle bestehenden Zeilen erhalten.

| Liste | Schlüssel | Vertrag |
|---|---|---|
| FieldDefinitions | `System:SystemDescription` | System, SystemDescription, Anzeige Beschreibung, SharePointType/ControlType Note, General, SortOrder 15, IsRequired/IsReadOnly/AllowMultiple/IsIndexed false, IsVisible/IsActive true; übrige Werte aus dem generierten Plan |
| FormFieldDefinitions | `System:Edit:SystemDescription` | System:Edit, Edit, General, RowNumber 29, ColumnNumber/Width 1, SortOrder 290, IsActive true; keine Umnummerierung |

3. Native Attribute und die zwei Zeilen lesend verifizieren. In der richtigen Governance-Portal-App ausschließlich die **Systems-Datenquelle unterstützt aktualisieren** und den aktualisierten Draft einmal manuell speichern/exportieren; automatische Studio-Draftstände dokumentieren. Bestehendes Testkonto/Connector verwenden, keine neue Berechtigung oder private Suchregel. Kein Publish. Der generierte neue Feldvertrag muss String/read-write sein; Description bleibt read-only.
4. Den gespeicherten Export in ignoriertes Staging unpacken. Nur das **erzeugte msapr-Referenzpaket** in `powerplatform/canvas/GovernancePortal/` übernehmen; aktuelles `Src/` unverändert lassen, keine DEV-Formeln übernehmen. Referenzdiff auf neue Systems-Spalte und notwendige unterstützte Referenzregeneration prüfen; keine Tokens, persönlichen Daten oder Logs versionieren. Abweichende Fachformeln nicht übernehmen. Danach vollständigen Build/Artefaktidentität und verfügbare Gates schließen.

**Stop-Regeln:** unerwarteter Typ/Schreibschutz, abweichende bestehende Metadaten, fehlende erzeugte Referenz, zusätzliche fachliche Änderung oder fehlgeschlagene Prüfung stoppen die Vorbereitung. Keine Wiederholung eines fehlgeschlagenen Schreibversuchs ohne Quellenprüfung. Kein allgemeines Provisioning, Seed, Reset, Delete/Purge, Import, Publish oder fachlicher App-Save in diesem Scope.

## Danach separat freizugebende Abnahme

Erst nach bestandener Vorbereitung/Build wird ein exakter ZIP-/msapp-/Quellenkandidat für Import, unterstützte Hostkompilierung/Rebinding und gezieltes App-Publish festgehalten. Der spätere begrenzte Retest muss Beschreibung mit Mehrzeilentext anlegen, unverändert wiederöffnen, einen Titel-Edit bei leerem Lookup mit Erhalt von Beschreibung/Person/Choices prüfen, Beschreibung ändern/leeren und positive Lookup-Auswahl/Erhalt/Leeren belegen. Jeder Edit verlangt eigene Quellen-/Versionsprüfung und keine stillen Retries; synthetische Daten anschließend reversibel bereinigen. Umfang, Marker und Zähler dieses Retests sind vor seiner eigenen Freigabe festzulegen. P1 bleibt bis dahin offen; P2 folgt nach P1-Abnahme.
