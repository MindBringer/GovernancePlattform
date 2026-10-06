# P1 – Systembeschreibung und sichtbare Speicherfehler

Stand: 2026-10-06 · `codex/stage41-p1` · [Draft #17](https://github.com/MindBringer/GovernancePlattform/pull/17) · Modellklasse `deep-reasoning`.

## Aktuelle freigegebene DEV-Abnahme

**P1 ist im begrenzten DEV-Scope fachlich abgenommen (06.10.2026): Solution 30445 / Canvas 196 Live, Draft 196.** Beide synthetischen App-Creates und alle fünf System-Edits bestehen: Titel bei leerem Lookup (v2.0), mehrzeilige Beschreibung mit positivem Asset-12-Lookup (v3.0), Titel bei positivem Lookup (v4.0), Beschreibung leeren (v5.0), Lookup leeren (v6.0). Vor jedem Save sind die nativen Quellwerte geprüft; danach bleiben alle übrigen gemappten Felder einschließlich Personenidentität und Choices unverändert. Jedes erneute Öffnen zeigt die gespeicherten Werte, „Keine Änderungen“ und gesperrtes Save. Nach genau einem Quellen-Titel-Edit auf v7.0 blockiert die App den veralteten Save mit sichtbarer Konfliktmeldung; sämtliche Quellwerte und Version bleiben erhalten. System ID 5 zuerst und Asset ID 12 danach reversibel bereinigt, beide nach Titel/Listenherkunft/ID im ersten Papierkorb nachgewiesen. Vorbestand exakt wiederhergestellt: Systems leer, Assets IDs 4–7 mit unveränderten nativen Feldwerten und Versionen. Suchregeln und publizierter Host bleiben exportgeprüft; keine erneute Kompilierung, Veröffentlichung oder DEV→Git-Übernahme. Formel-/Laufzeitchecker ohne Fehler; 72 Accessibility-, zwölf Leistungs- und zwei Datenquellenwarnungen bleiben. Das belegt weder Produktivrollen, große Datenmengen noch atomaren ETag-Konfliktschutz.

Verbrauch 30445: Import **1/1**, Personen-/Lookup-Rebinding **je 1/1**, manuelles Save **1/1**, gezieltes Publish **1/1**, Creates **2/2**, System-Edits **5/5**, Konflikt-Quellen-Edit / blockierter App-Save **je 1/1**, reversible Deletes **2/2**. Schema-/Metadaten-/Bestands-Writes, Publish All und Save-/Import-Retries **0**. Alle drei unveränderten Kandidaten-Hashes bestätigt; Einstieg mit drei CI-Checks SUCCESS am Dokumentationshead `9958e7c44c1e057b42eb2c6fb689ced76643b62b`. Abschluss-Gates und CI am neuen Dokumentationshead werden im Draft-PR und privaten Handoff festgehalten. Exporte, Zähler, Quellenwerte und Screenshots ignoriert unter `artifacts/p1-20261002/dev-abnahme-30445-20261005/`. Kein neuer Build oder DEV→Git.

Der gespeicherte Host vor Rebindings hat SHA-256 `a8060e665e555ec956f5b1fa2082bf9424e8e9a46a44a7d0bcfbbad32487d291`. Nach öffentlichen PrimaryText-/SearchField-Auswahlen (Person DisplayName, Lookup DisplayText; vorhandenes SecondaryText erhalten) hat der native Draft-Export SHA-256 `bea9768eee852f5e8d61f1e48135b715de216325d6261289aba3b7c3e0b18e74`. Nur beide erzeugten SearchItems ändern sich semantisch; Lookup SearchFields enthält zusätzlich allein eine Whitespace-Differenz. Publizierter Export SHA-256 `13d31bdc4be10feebac6914cdd78fec343f1cf2a4b043ca249ed19fce8631a3f`: Controls und DataSources bytegleich zum geprüften Draft. PAC-Unpack und tatsächlicher Schreibvertrag Exit 0. Kein weiteres manuelles Save und keine Übernahme der Hostquellen. Die Fortsetzung am 06.10.2026 verwendet dieselbe freigegebene Version und dieselben erzeugten IDs. Nach bestätigter Anmeldung mit dem bestehenden Testkonto sind alle nativen Quellwerte erneut geprüft. Die vorhandene App-Browseranbindung übernimmt den verbliebenen fachlichen Test mit sichtbar funktionierenden Eingabeereignissen; kein Save aus der unzuverlässigen nativen Edge-Steuerung. Alle vier verbliebenen Edits, Konfliktsperre und Cleanup sind abgeschlossen.

## Abgeschlossene Voraussetzung vor dem Import

**Die konkret freigegebene DEV-Voraussetzung und die danach getrennt freigegebene begrenzte P1-Abnahme sind abgeschlossen; Deploymentkandidat 30445 bleibt unverändert.** Stand am Ende der Vorbereitung: Solution 30444 / Canvas 193 Live, Draft 194 nicht veröffentlicht. Dieses Vorbereitungspaket enthält keinen Import, Publish oder fachlichen App-Save.

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

Am 06.10.2026 sind am tatsächlichen unveränderten Kandidaten erneut **20/20 verfügbare Projekt-Gates mit Exit 0** abgeschlossen: 770 tatsächliche Power-Fx-Assertions / 56 Formeln und 13 Python-Regressionen. Artefaktidentität und Diff bestehen. Die drei Kandidaten-Hashes sind unverändert; kein neuer Build/Pack oder DEV→Git. Pester fehlt, PAC canvas validate bleibt nicht verfügbar. CI am abschließenden Dokumentationshead wird im PR/Handoff nachgewiesen.

## Ergebnisse der begrenzten DEV-Abnahme

| Prüfung | Native Quelle / sichtbares Ergebnis |
|---|---|
| Create und Titel bei leerem Lookup | Asset 12/v1.0 und System 5/v1.0; Titel-Edit auf System v2.0, Beschreibung und übrige Werte erhalten |
| Beschreibung und positives Lookup | v3.0: exakte zwei Textzeilen, LookupId 12 und passender LookupValue |
| Titel bei positivem Lookup | v4.0: Titel geändert, Beschreibung, Personenobjekt und Lookup unverändert |
| Beschreibung explizit leeren | v5.0: SystemDescription nativ null; Lookup und alle übrigen gemappten Felder erhalten |
| Lookup explizit leeren | v6.0: LinkedAsset nativ null; alle übrigen gemappten Felder erhalten |
| Sauberes Wiederöffnen | Nach jedem Create/Edit gespeicherte Werte; „Keine Änderungen“, Save gesperrt, Owner und repräsentative Choices erhalten |
| Parallel geänderter Titel | Zweiter Client ändert ausschließlich den Testsystem-Titel auf v7.0; veralteter App-Save wird mit „Der Datensatz wurde inzwischen geändert. Änderungen verwerfen und neu öffnen.“ blockiert, Save gesperrt, alle Quellwerte/v7.0 erhalten |
| Reversibles Cleanup | System 5 vor Asset 12; beide exakt nach Titel/Listenherkunft/LeafName im ersten Papierkorb. Erste 500-Zeilen-Abfrage für System unvollständig; vollständiges lesendes Rücklesen bestätigt Herkunft, keine Löschwiederholung |
| Vorbestand | Assets IDs 4–7 mit allen nativen Baseline-Feldwerten/Versionen unverändert; Systems leer, auch im aktualisierten Player |

Die sichtbare Konfliktmeldung im Editor ist belegt. Späte unhandled Errors, Screenreader-Verhalten, atomarer ETag-Schutz, reale Rollen und große Datenmengen bleiben getrennte Abnahmen. Keine künstlichen Berechtigungs-/Schemafehler erzeugt. In dieser Fortsetzung wurden keine Kandidatenquellen, Architektur-/Runtime-Metadaten oder Versionen geändert.

## Genau ein primäres nächstes Arbeitspaket

**P2 · begrenzte DEV-Abnahme von 30446**, Modellklasse `standard-reasoning`. Den lokal geprüften Asset-Kandidaten nach eigener Freigabe einmal in DEV übernehmen, unterstützt in Studio kompilieren und gezielt veröffentlichen. An genau einem synthetischen Asset alle fünf Personenfelder, Status/Kritikalität, Reviewtermine und optionale Leerwerte mit nativer Rückleseprüfung und sauberem Wiederöffnen abnehmen; anschließend reversibel bereinigen. [Kandidat, genaue Schrittfolge, Höchstzahlen und Stop-Regeln](Stage-4.1-P2-Asset-Verantwortliche.md). P1-Abnahme und Bestandsdaten bleiben abgeschlossen; P3 beginnt erst nach bestandener P2-Abnahme. Keine aktuelle Freigabe für Import, Publish oder fachliche Tenant-Writes.

## Abgeschlossene P1-Freigabe und Grenzen

Die nachfolgend dokumentierte Freigabe vom 05.10.2026 ist vollständig ausgeführt und verbraucht; sie autorisiert keine weiteren Writes. Nach [AGENTS.md](../../AGENTS.md) bleibt die lokale P2-Umsetzung das einzige nächste Paket.

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

P1 ist innerhalb dieses begrenzten DEV-Scope abgenommen. P2 ist lokal als 30446 vorbereitet; dessen DEV-Abnahme folgt separat. Merge/Integration und Produktivfreigabe bleiben eigene Schritte.
