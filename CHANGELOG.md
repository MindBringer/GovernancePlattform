# Changelog

Dieses Changelog enthält sowohl die Provisioning-/Architektur-Baseline als auch die Canvas-Entwicklung. Die Versionsreihen bleiben getrennt.

## Unreleased

### Canvas Stage 4.1 – Entwicklungsbranch

- **30444 fachlicher DEV-Test (03.10.2026):** Titeleingabe im getrennten sichtbaren Player korrekt; veröffentlichte Text-/Revalidierungsregeln kanonisch. Asset ID 11 und System ID 3 je einmal angelegt, Quelle/Wiederöffnen mit repräsentativen Person-/Choice-Werten belegt; Lookup semantisch leer (`0;#`), Player nach Asset-Create frisch gestartet. Erster System-Titel-Edit persistiert nicht; Quelle ursprünglicher Titel/Version 1.0/alle sichtbaren Felder unverändert, Player dirty. Vier Folge-Edits gestoppt, kein Retry; beide Testdatensätze in Reihenfolge System → Asset reversibel gelöscht und im Papierkorb belegt, Vorbestand wiederhergestellt. Verbrauch Creates 2/2, System-Edit-Versuche 1/5, Deletes 2/2. Live-Monitor-Ereignisse und gültiger ungespeicherter Entwurf für das einzige nächste Paket vorbereitet (Verbindung vor neuen Saves erneuern): ein neues System, ein überwacht ausgelöster Titel-Edit, ein reversibles Cleanup nach konkreter neuer Freigabe. Noch kein zusätzlicher Save, kein Quell-/Build-/Versionswechsel, Import/Rebinding/Studio-Save/Publish nicht wiederholt.
- **30444 DEV-Fortsetzung / Canvas 193 Live (03.10.2026):** Studio-Sperre ohne Sitzungsüberschreibung gelöst; je ein öffentliches Personen-/Lookup-Rebinding mit erhaltener Spaltenstruktur und Suchaktivierung ausgeführt. Gespeicherter Draft enthält kanonische Load-/Payload-/Default-/Items-Formeln und korrekt generierte echte Suchquellen statt `ComboBoxSample`; keine weitere fachliche Formelabweichung. Native Formelprüfung fehlerfrei, ein gezielter manueller Save-Versuch und eine App-Veröffentlichung; Maker 193 Live und publizierter Export mit identischen kompilierten Regeln belegt. Frischer Player aktualisiert. Erste Asset-Vorbereitung zeigt Person/Choice, Titeleingabe bleibt jedoch als fehlendes Pflichtfeld markiert, Save gesperrt; manuelle Gegenprobe offen. Kein fachlicher Saveversuch, Creates 0/2, System-Edits 0/5, Deletes 0/2. Nächstes Paket: native Titeleingabe klären und denselben freigegebenen Rest-Round-Trip ausführen. Kein weiterer Import/Publish, Quellkandidat unverändert, kein DEV→Git.
- **30444 DEV / Canvas 192 Live, Draft 193 (03.10.2026):** konkrete Freigabe begonnen, Vorzustand 30443/191 und Metadaten je ID 721 gelesen. Genau ein Import ohne Publish All/`--publish-changes`: PAC Timeout / Exit 1, serverseitiger Import laut Solution-Verlauf erfolgreich; Postexport Exit 0 mit bytegleichem Kandidaten-msapp. Kein Import-Retry. Studio öffnet die richtige App und speichert 193 automatisch; Bedienung über die verfügbare Browsersteuerung scheitert, nach Reload/frischem Tab zusätzlich Sitzungsschreibschutz. Keine Überschreibung, kein Rebinding/manuelles Save/gezieltes Publish, keine fachlichen Testwrites. Assets 4–7/Systems leer. P1 bleibt offen; einziges nächstes Paket ist der bereits freigegebene Rest der 30444-DEV-Abnahme nach Wiederherstellung der Studio-Bedienbarkeit. Kein neuer Kandidat oder DEV→Git.
- **30444 lokal (02.10.2026):** System-Lookup-IDs 0/negativ werden beim Laden/Default/Speichern als leer behandelt, gültige Referenzen und übrige Save-Felder erhalten. Kein Phantom-Lookup aus dem leeren Quellsentinel; Pflichtreferenz verlangt positives Ziel. Öffentliche Lookup-Suchbindung explizit und ohne private SearchItems-Property geprüft. Gleichwertige ShowColumns-Projektion für Mehrfachdefaults, im realen Interpreter geprüft. Regression reproduzierte ID-0-Fehler vor Korrektur; 95 zusätzliche tatsächliche Record-Assertions, insgesamt 725 (137/212/376), 53 Formeln, Build/Round-Trip/18 Gates Exit 0. Kandidat nicht importiert/veröffentlicht; historische Pack-Controls sind kein Hostnachweis. Einziges nächstes Paket: konkrete 30444-DEV-Abnahme mit zwei Creates, fünf System-Edits und zwei reversiblen Löschungen nach neuer Freigabe.
- **30443 DEV / Canvas 191 Live (02.10.2026):** kanonische öffentliche Personenfelder ohne neue Fachformel wiederhergestellt, generierte V2-Suche im gespeicherten Draft und publizierten Export belegt; Formelchecker ohne Fehler. Asset/System neu angelegt, nach ID sauber geladen, Person/Choices begrenzt wieder angezeigt. Asset-Titel-Edit bestätigt; einmaliger System-Titel-Edit nicht in der Quelle, kein Retry. Lookup-Suche verweist intern noch auf `ComboBoxSample`. Kontrollierter Asset-Konflikt-Save mit sichtbarer Meldung blockiert, Quellversion 3.0 erhalten. System ID 2 und Asset ID 10 reversibel bereinigt, ursprüngliche Assets 4–7/Systems leer. Kontingente verbraucht, P1 bleibt offen; nächstes Paket System-Save-/Lookup-Reparatur vor neuer konkreter Tenant-Freigabe. Keine neue Quell-/Buildversion oder DEV→Git-Übernahme.
- **30442 DEV / 30443 lokal (02.10.2026):** freigegebener Import 30442 ohne Publish All/`--publish-changes`, Postexport bytegleich, Canvas 186 Live. Studio öffnet und speichert 187 automatisch, nicht veröffentlicht; Checker meldet zwei Fehler im Formularfilter (`ObjectTypeKey` unbekannt, Error/Text-Vergleich). Keine fachlichen Testwrites oder gezielte Publikation. Lokale Korrektur `formField.ObjectTypeKey` in 30443; Test des tatsächlichen Filters reproduziert beide Hostfehler vor der Korrektur und besteht danach, sechs zusätzliche Scope-Assertions und CI-Aliasvertrag. 630 Power-Fx-Assertions (137/212/281), 53 Formeln, vier YAML-Regressionstests, Build/Round-Trip/18 Gates Exit 0. Einziges nächstes Paket: konkret freizugebende P1-DEV-Fortsetzung mit 30443.

- **P1 lokal (02.10.2026), Solution 30441:** native Asset-/System-Galerien mit Titelanfang/ID-Suche und Seitenführung, Load nach ID und Bearbeiten auf Basis der vorhandenen 17/16 Save-Felder. Hydrierung erhält leere Werte, Datum/Uhrzeit, Personen-/Choice-/Lookup-Verträge; unveränderte Defaults erzeugen keine Änderungen. Native Original-Records als Patch-Basis, frische Modified-Prüfung, sichtbare Fehler/Konflikte und Navigation mit Verwerfen-Dialog.
- Capabilities nur für ausführbare Asset/System-Pfade; andere Typen melden List/Create/Edit/Save als false. System-Title in führender Architektur und Metadatengenerator ergänzt: exakt zwei zusätzliche Zeilen, andere 1.014 unverändert. CI um Record-Quell-/Compilervertrag und System-Title-Gate erweitert; Accessibility-Vertrag auf 20 Controls/fünf Galerien und Ladesperren erweitert.
- **P1-DEV-Versuch (02.10.2026):** genau zwei System-Title-Metadatenzeilen nach Reload geprüft. 30441 unmanaged ohne Publish All/`--publish-changes` importiert, Postexport bytegleich; Maker zeigt trotzdem Canvas 185 Live. Studio scheitert vor Öffnen an PA1001/YamlInvalidSyntax in der neuen Öffnen-Beschriftung. Keine fachlichen Creates/Edits oder gezielte Studio-Publikation; P1 nicht abgenommen.
- **Reparaturkandidat 30442 lokal:** beide Öffnen-Beschriftungen als YAML-Blockskalare ohne Formeländerung; echter YAML-Parser vor Pack und in CI, vier Regressionstests für den Hostfehler, Formelerhalt, nicht skalare Properties und doppelte Schlüssel. 624 Offline-Power-Fx-Assertions (137 Capability/212 Choice/275 Record), 53 geparste Formeln, vier YAMLs im SourceCode-Round-Trip gleich und alle 18 verfügbaren Gates/Build Exit 0. 30442 wurde danach ausdrücklich freigegeben übernommen; der weitere Studio-Befund und aktuelle 30443-Fortsetzung stehen oben. Keine Produktivfreigabe.

- P0: Provider-/Modus-/ID-/Busy-Guards und Pflicht-Title ohne Fallback; zwei zusätzliche Title-Metadaten, 1.012 vorhandene unverändert. Classic-Button-/Input-Verträge und Guards aller neun Eingabeereignisse. Textvalidierung live funktionsfähig.
- DEV **30440 / Canvas 184 Live**: Import ohne Publish All, unterstütztes Studio-Rebinding der kanonischen Personensuche und gezielte Veröffentlichung. Studio-Checker ohne Formel-/Laufzeitbefund; Accessibility-/Leistungsgrenzen dokumentiert.
- 30440: feldbezogener Choice-Default, erfasster Choice-OnChange-Record, alle zehn vorhandenen nativen Choice-Adapter verwenden Compiler-Anzeigenamen; unbekannte nicht leere Schlüssel sperren Save. Interne Schlüssel/Architektur unverändert. 347 tatsächliche Offline-Power-Fx-Assertions, Choice-Quell-/Compilervertrag und vier negative Personen-Fixtures.
- **P0 technisch in DEV abgeschlossen (02.10.2026)**: nach früherem fehlerhaftem ID-8-Test genau ein zusätzlicher freigegebener Asset-Save ID 9 im frischen Player. Title getrimmt, Owner korrekt, Kritikalität Anzeige/Quelle Hoch; reversible Bereinigung/ID-Filter/Papierkorb und vier Bestandsassets verifiziert. P1 folgt mit eigener lokaler Umsetzung/DEV-Abnahme; keine vollständige Asset-/Produktivfreigabe.

- Read-only-DEV-Export mit dem lokalen Stage-4.1-Reconciliation-Stand abgeglichen; Personenfeld- und Asset-Speicherlogik in den kanonischen Canvas-Quellcode übernommen.
- Diagnostisches Suchlabel aus dem Quellcode entfernt; Solution-Manifest auf die DEV-Baseline `1.0.0.30428` ausgerichtet und Canvas-/Solution-Paket lokal neu erstellt.
- CI prüft nun auch, ob das versionierte `.msapp` die vier aktuellen Canvas-YAMLs enthält. Studio-Validierung und DEV-Smoke bleiben für die fachliche Abnahme erforderlich.
- Canvas-Version `1.0.0-alpha.4.1.0` zwischen Versionsdatei, App und Entwicklerkonfiguration abgeglichen.
- Object-Provider-Registry in der Canvas-Runtime synchronisiert; Auswahl bindet den aktiven Provider und der Neu-Befehl prüft dessen Create-Fähigkeit.
- Synchronisierer gegen eine fälschlich erkannte Provider-Bindung korrigiert; CI prüft Canvas-Version, Registry und Runtime ohne automatische Reparatur.
- DEV-Baseline `30430` wurde am 28.09.2026 freigegeben importiert und als Canvas 165 Live geprüft; P0-Choice-Abnahme `30440` ist abgeschlossen; Stage-4.1-Integration bleibt separat.

### Documentation and repository

- Root-README auf das Gesamtprojekt und den Stage-4.1-Entwicklungsstand ausgerichtet.
- Architektur und Roadmap auf Provisioning 6.2.5 sowie den aktuellen Provider-Ausbau aktualisiert.
- Entwicklungs- und Build-Prozeduren vereinheitlicht.
- konkurrierende Dokumente und den zweiten Canvas-SourceTree entfernt.
- historische Iterations- und Migrationsunterlagen archiviert.
- `DeveloperPlatform.psd1` auf Canvas `1.0.0-alpha.4.1.0` synchronisiert.

## Canvas 1.0.0-alpha.3.4.1

- selbsttragender SourceCode-Build hergestellt
- Lookup-Registry, Cache und Lazy Lookup Provider stabilisiert
- Office365Users-Personenprovider integriert
- Save-Provider für Assets und Systems ergänzt
- Versionierung zwischen Canvas und Solution automatisiert

## Canvas 1.0.0-alpha.3.0–3.4

- metadatengetriebenes Anwendungsframework und dynamischer Editor
- typisierte Editorwerte, Validierung und Dirty State
- Choice-, Lookup- und Person-Controls
- responsive Shell und Runtime-Bootstrap

## Provisioning 6.2.5 – Git baseline

- explizite SharePoint-Authentifizierungsmodi (`Interactive`, `DeviceLogin`, `OSLogin`)
- konsistente Rollenreferenzen und PermissionDefinitions
- korrigierte Choice-Filter und Pflichtfelder für Geschäftsregeln
- normalisierte Navigations-URLs
- Eindeutigkeit stabiler Governance- und Konfigurationsschlüssel
- statische Architekturprüfungen für Rollen, Felder, URLs und Choice-Filter

## Provisioning 6.2.4

- metadatengetriebene Provisioning-Baseline mit 50 Listen
- Canvas-Runtime-Metadaten, Search Index, Timeline, Notification Templates, Saved Views und User Preferences
- Korrekturen früherer Parserfehler
