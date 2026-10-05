# P1 – Systembeschreibung und sichtbare Speicherfehler

Stand: 2026-10-05 · `codex/stage41-p1` · [Draft #17](https://github.com/MindBringer/GovernancePlattform/pull/17) · Modellklasse `deep-reasoning`.

## Aktuelle freigegebene DEV-Abnahme

**DEV: Solution 30445 / Canvas 195 Live, gespeicherter Draft 196.** Der einmalige Import und bytegleiche Postexport sind abgeschlossen. Formel- und Laufzeitchecker zeigen jeweils „Keine Fehler gefunden“; 72 Accessibility-, zwölf Leistungs- und zwei Datenquellenwarnungen bleiben. Ein manueller Studio-Save bestätigt „Alle Änderungen wurden gespeichert“; der native Download wurde geprüft. Alle 83 Controls sind gegenüber den kanonischen Quellen semantisch gleich; 45 im Studio ausgelassene Defaults sind kompiliert gleichwertig. Alle 19 Quellenbindungen und Metadatensnapshots sind gleich, sämtliche 33 tatsächlichen Patch-Spalten writable. Beide erzeugten SearchItems verwenden jedoch `ComboBoxSample`; die freigegebenen öffentlichen Personen-/Lookup-Rebindings sind deshalb vor Publish erforderlich. Keine private Regel authoriert, kein Rebinding, gezielter Publish oder fachlicher Write ausgeführt. Parallele native Edge-Steuerung aus dem Chat „Projektstatus prüfen“ im Projekt UserLifeCycle ist als Ursache der Fenster-/Eingabewechsel belegt; weitere native Eingaben warten auf exklusive Bedienung. Die vorhandene Restscope-Freigabe bleibt bestehen.

Verbrauch 30445: Import **1/1**; Personen-/Lookup-Rebinding **je 0/1**, manuelles Save **1/1**, gezieltes Publish **0/1**, Creates **0/2**, System-Edits **0/5**, Konflikt-Quellen-Edit / blockierter App-Save **je 0/1**, reversible Deletes **0/2**. Schema-/Metadaten-/Bestands-Writes, Publish All und Import-Retries **0**. Alle drei Kandidaten-Hashes und CI am Kandidaten-Head `4ad92326028877ed1d381fdda9c647e27bce6af7` geprüft; drei Checks SUCCESS. Exporte, Zähler, Logs und Screenshots ignoriert unter `artifacts/p1-20261002/dev-abnahme-30445-20261005/`. Kein neuer Build oder DEV→Git.

Der gespeicherte Studio-Download hat SHA-256 `a8060e665e555ec956f5b1fa2082bf9424e8e9a46a44a7d0bcfbbad32487d291`; PAC-Unpack und Prüfung seines tatsächlichen Schreibvertrags jeweils Exit 0. Die erzeugten Suchregeln sind keine kanonischen Bearbeitungsquellen und wurden nicht manuell geändert. Keine DEV→Git-Übernahme der Hostquellen. Ein weiteres manuelles Save ist aus diesem Scope nicht verfügbar; automatisch gespeicherte Änderungen nach den erlaubten öffentlichen Rebindings werden separat über Version und Download belegt. Die Koordination mit dem anderen Chat benötigt ausdrückliche Nutzerautorisierung zum Senden einer Pausen-Nachricht; bis dahin keine weitere native Edge-Eingabe.

## Abgeschlossene Voraussetzung vor dem Import

**Die konkret freigegebene DEV-Voraussetzung ist abgeschlossen; Deploymentkandidat 30445 ist vollständig gebaut. P1 bleibt bis zur getrennten DEV-Abnahme offen.** Stand am Ende der Vorbereitung: Solution 30444 / Canvas 193 Live, Draft 194 nicht veröffentlicht. Dieses Vorbereitungspaket enthält keinen Import, Publish oder fachlichen App-Save.

Native lesende Prüfung belegt `Systems.Description` als Note mit ReadOnlyField=true und Sealed=true, Hidden=false / FromBaseType=false, Gruppe `_Hidden`. Der Connector-Schreibschutz entspricht dem nativen Feld. Die ursprüngliche Provisionierungshistorie ist nicht bewiesen. Description, seine Werte und sein Architekturvertrag bleiben erhalten; ReadOnly/Sealed und Connector-Permissions werden nicht umgestellt. Eine Datenmigration ist nicht Teil dieses Pakets.

Kandidat 30445 verwendet für die fachliche Beschreibung die eigene optionale Note-Spalte `SystemDescription`, Anzeige **Beschreibung**. Load, Formularfilter und Patch verwenden denselben internen Namen; System behält 16, Asset 17 Felder. Native Patch-Basisrecords, unveränderte Personenobjekte, Choices, positive/leere Lookups und Modified-/Conflict-Prüfung bleiben erhalten. Vier kanonische Src-YAMLs in der DEV-Vorbereitung nicht verändert.

Die zuvor lokal implementierte Fehlerbehandlung übernimmt unhandled Errors auch im Editor nach Rücksetzen von SaveBusy. Konkrete SaveError hat Vorrang; unklarer Ausgang sperrt New-/Edit-Retry. Das Fehlerlabel wächst, nutzt Live.Assertive und verschiebt das Formular. Der tatsächliche lokale Power-Fx-Interpreter prüft diese Formeln; sichtbares Host-/Screenreaderverhalten bleibt separat zu prüfen. [Microsoft-Fehlerbehandlung](https://learn.microsoft.com/en-us/power-platform/power-fx/error-handling).

## Ausgeführter freigegebener Voraussetzungsscope

1. Spalte und beide Schlüssel vor dem ersten Write gelesen: jeweils nicht vorhanden. Mit bestehendem Testkonto/PnP-App genau eine eigene Systems-Note nach dem echten Architektur-XML angelegt: Name/StaticName SystemDescription, Anzeige Beschreibung, Required/Indexed/EnforceUniqueValues false, NumLines 8, RichText false, Gruppe Governance Platform 6.2.5. Rücklesen bestätigt schreibbar/unversiegelt; Description unverändert. Ein erster lokaler PnP-Verbindungsfehler stoppte vor jedem Write; nach korrigierter Verbindungsübergabe und erneuter Quellenprüfung keine Wiederholung eines Schreibversuchs.
2. Genau zwei neue Runtimezeilen aus dem tatsächlichen Generatorplan angelegt, jeweils ID 722: FieldDefinitions `System:SystemDescription` und FormFieldDefinitions `System:Edit:SystemDescription`. Alle Planwerte zurückgelesen. In beiden Listen jeweils 362 → 363 Zeilen; die zusammen **724 zuvor vorhandenen Zeilen** bleiben nach ID/Modified/Version gleich. Kein globales Provisioning/Seed, keine Umnummerierung, andere Listen nicht geschrieben.
3. Nur Systems einmal unterstützt in Studio aktualisiert. In-App-Frame-Bedienung nicht verfügbar; temporäre Sitzungen geschlossen, im vorhandenen nativen Edge/Testkonto eigene alte Sitzungssteuerung übernommen. Ein manueller Draft-Save-Versuch; Maker belegt Draft 194 und weiter 193 Live. Nach Sitzungsablauf ohne erneuten Refresh/Save den gespeicherten Draft lesend mit **Kopie herunterladen** exportiert. PAC canvas download lieferte hier weiter die publizierte 193-Version und wurde nicht zur Referenzübernahme verwendet.
4. Nativen Export per PAC SourceCode in ignoriertes Staging unpackt, **nur erzeugtes msapr** in den kanonischen Tree übernommen. SystemDescription string/read-write; Description weiter read-only. Alle 19 Quellen-/Tabellenbindungen gleich. 14 SharePoint-Snapshots zeigen notwendige unterstützte Regeneration: CdpRevision-Zeitstempel, reservierte Thumbnail-Metadaten entfernt, IsFolder-Anzeigename mit Leerzeichen. Nur Systems erhält die eigene neue Spalte samt Note-Sortier-/Filtergrenzen und Anzeigeordnung. Alle bisherigen Fachfelder/Permissions gleich. Zwei Studio-Formelstellen disambiguieren nur den Anzeigenamen der alten Description zu `Beschreibung (Description)`; nach dieser lexikalischen Normalisierung sind alle vier DEV-YAMLs bytegleich zum Vorzustand. Diese DEV-YAMLs wurden nicht übernommen.

| Liste | Neuer Schlüssel | Zurückgelesener Vertrag |
|---|---|---|
| FieldDefinitions | `System:SystemDescription` | System, SystemDescription, Beschreibung, SharePointType/ControlType Note, General, SortOrder 15; IsRequired/IsReadOnly/AllowMultiple/IsIndexed false, IsVisible/IsActive true; übrige Werte aus dem Generatorplan |
| FormFieldDefinitions | `System:Edit:SystemDescription` | System:Edit, Edit, General, RowNumber 29, ColumnNumber/Width 1, SortOrder 290, IsActive true |

Verbrauch Vorbereitung: native Spaltenneuanlage **1/1**, neue Metadatenzeilen **2/2**, Systems-Refresh **1/1**, manueller Draft-Save-Versuch **1/1**, nativer Draft-Export **1**. Import/Publish/fachliche Creates/Edits/Deletes **0**. Die früheren 30444-Abnahme-/Diagnosekontingente bleiben verbraucht.

## Kandidat und Abschluss-Gates

Vollständiger **Build / Exit 0**, PAC 2.9.3 SourceCode-Pack, Solution-Pack und Unpack jeweils Exit 0. Solution-Version bleibt **1.0.0.30445**, da der zuvor gesperrte Quellenkandidat nie importiert wurde; Canvas **1.0.0-alpha.4.1.0**, Provisioning **6.2.5** unverändert. Vier kanonische Src-Dateien bytegleich zum Einstieg und im Round-Trip.

**20/20 verfügbare Projekt-Gates Exit 0.** Architecture/Consistency, PowerShell-Syntax, Asset-/System-Title, additive Beschreibung, YAML, Canvas, Accessibility, Registry/Runtime, Referenzen, Personen, Artefaktidentität, Power-Fx Choice/Capability/Record, Audit und Diff bestehen. **770 tatsächliche Power-Fx-Assertions** (137 Capability + 212 Choice + 421 Record) / 56 Formeln, **13 Python-Regressionen** (4 YAML + 9 Connector). Das Schreibvertrags-Gate prüft alle **33 tatsächlichen Patch-Spalten** im kanonischen und gepackten Connector; keine Permission wird verändert. Pester fehlt, PAC canvas validate nicht verfügbar. Offline-Pack ist keine Maker-/Tenant-Abnahme des neuen Kandidaten.

| Artefakt | SHA-256 |
|---|---|
| `GovernancePortal_1.0.0.30445_1.0.0-alpha.4.1.0.zip` | `439c8f50a8314b834aa6fda91b0b2113115c938b021fa384a8d282ced178739c` |
| `gp_governanceportal_c93a1_DocumentUri.msapp` | `09516cb679d1a23c45249953401741959f5d56bfe1db4b15b350420608388c0c` |
| Kanonisches erzeugtes msapr | `addc5517a8f8abd5ba74b3b7510b827132eb20b0bdd9c54e2c1fc3f5323a802f` |

ZIP enthält bytegleich das geprüfte msapp. Private Logs, native Vor-/Rückleseprüfung, Referenzreview, Gates/Exit-Codes, Kandidat und Screenshots liegen ignoriert unter `artifacts/p1-20261002/dev-preparation-20261004/`; keine Tenantsettings, Tokens, persönlichen Daten oder Logs versioniert. Historische lokale Reparatur: 19/20 Gates und Build Exit 1 wegen fehlender Referenz; dieses Hindernis ist durch die freigegebene Vorbereitung behoben.

## Genau ein primäres nächstes Arbeitspaket

**P1 · Öffentliche Suchbindungen regenerieren und die freigegebene 30445-DEV-Abnahme beenden**, Modellklasse `deep-reasoning`. Nach exklusiver nativer Edge-Bedienung Personen- und Lookup-Bindung jeweils höchstens einmal öffentlich regenerieren, automatisch gespeicherten Hostexport einschließlich erzeugter Suchregeln und unveränderter Fachformeln prüfen, dann höchstens ein gezieltes App-Publish und den freigegebenen synthetischen Round-Trip ausführen. Import und manueller Studio-Save sind jeweils 1/1 verbraucht und werden nicht wiederholt; Rebindings je 0/1 und Publish 0/1. Die bestehende Freigabe bleibt erhalten. P1 bleibt offen, P2 folgt danach. Die separate Freigabe ist am 05.10.2026 erteilt; der Import ist verbraucht. Nach [AGENTS.md](../../AGENTS.md) wird ausschließlich der verbleibende Scope ausgeführt. Exakter ZIP/msapp oben und folgende Grenzen bilden den konkreten nächsten Scope; die abgeschlossene Spalten-/Metadaten-/Referenzvorbereitung wird nicht wiederholt.

| Aktion | Höchstzahl / Grenze |
|---|---|
| Import | 1 unmanaged DEV-Import des oben gehashten ZIP; kein Publish All / `--publish-changes`; bei Timeout serverseitigen Verlauf/Postexport lesen, kein blinder Retry |
| Unterstützte Hostkompilierung | Richtige Governance-Portal-App; falls nötig höchstens ein öffentliches Personen- und ein Lookup-Rebinding mit unveränderten Fachformeln; ein manueller Draft-Save-Versuch, automatische Draftversionen dokumentieren; keine neue Permission/private SearchItems-Regel |
| App-Publish | 1 gezielte App-Veröffentlichung nach Checker/Quell-/Artefaktvergleich; kein sonstiges Deployment |
| Synthetische Creates | 2: Asset als Lookup-Ziel, System mit mehrzeiliger Beschreibung, Testkonto, repräsentativen Choices und leerem LinkedAsset |
| System-Edits | 5: Titel bei leerem Lookup ändern/Beschreibung erhalten; Beschreibung ändern/positives Lookup setzen; Titel bei positivem Lookup ändern/übrige Werte erhalten; Beschreibung leeren/Lookup erhalten; Lookup leeren |
| Konfliktprüfung | 1 zusätzlicher Quellen-Titel-Edit ausschließlich am synthetischen System; 1 anschließend blockierter App-Save, Quellenversion erhalten; kein stiller Retry |
| Reversibles Cleanup | 2: ausschließlich neu erzeugte IDs, System vor Asset; keine Papierkorbleerung |

Bereits freigegebene Marker: `GP-P1-30445-20261005-ASSET` / `GP-P1-30445-20261005-SYSTEM`; Titel-Edits ausschließlich an diesen neu erzeugten IDs. Zähler dieses neuen Pakets sind oben dokumentiert; alte Abnahme-/Diagnosekontingente bleiben verbraucht. Vor jedem Save Quell-ID/Version und geladene Werte prüfen; danach native Quelle und erneutes Öffnen einschließlich unveränderter Person/Choices belegen. Bei Fehler, unklarem Ausgang oder Versionsabweichung stoppen und Quellen prüfen. Keine Bestandsdatensätze, Rollen, Schema/Metadaten oder weitere Provider ändern. Fehleranzeige im Host nur als belegt ausweisen, wenn tatsächlich beobachtet; keine neuen künstlichen Berechtigungs-/Schemafehler erzeugen.

P1 bleibt bis zur belegten DEV-Abnahme offen; P2 folgt danach. Merge/Integration und Produktivfreigabe bleiben eigene Schritte.
