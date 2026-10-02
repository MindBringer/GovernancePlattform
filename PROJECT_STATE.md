# Projektübergabe – GovernancePlattform

Stand: 2026-10-02 · Branch `codex/stage41-p1`, Basis `5caee00823032b4306f0bdaa900ca9817a53610e` aus [P0-PR #16](https://github.com/MindBringer/GovernancePlattform/pull/16). [P1-Draft #17](https://github.com/MindBringer/GovernancePlattform/pull/17) liegt auf `codex/stage41-p0` zur Prüfung bereit. Fachlicher Zielzweig bleibt `feature/canvas-stage-4.1-provider-engine`; kein Merge.

## Kandidat und belegter DEV-Stand

- **P1 lokal gebaut: Solution 30441**, Canvas `1.0.0-alpha.4.1.0`, Provisioning `6.2.5`. Kein P1-Tenant-Write, Import oder Publish. DEV zuletzt belegt: **P0 Solution 30440 / Canvas 184 Live**.
- P1 enthält native Asset-/System-Listen mit Titelanfangssuche, genauer ID und Galerie-Seitenführung; Load nach ID, gemeinsamer New-/Edit-Editor und Save gegen den original geladenen nativen Datensatz. Die Formulare enthalten genau die bereits vorhandenen Save-Mappings: Asset 17 / System 16 Felder. Weitere Asset-Felder, zusätzliche Provider, Reviews und Produktivrollen folgen den späteren Roadmap-Paketen.
- Vollständige Hydrierung erhält leere Werte, `0`, `false`, Datum/Uhrzeit, Choice-Schlüssel, Personenidentität und bestehende Lookup-Auswahl. Unveränderte Personenobjekte bleiben nativ erhalten. Unbekannte gespeicherte Choices sowie fehlende/falsch typisierte Metadaten sperren Save. Geladene Defaults dürfen keine Felder als geändert markieren.
- Load-/Save-/Modal-Sperren, Abbruch und Navigation mit Verwerfen-Dialog; Lade-/Speicherfehler bleiben sichtbar. Edit verlangt positive und übereinstimmende geladene ID, vollständigen Load und echte Änderung. Vor Save wird `Modified` frisch verglichen; fehlender/gelöschter Datensatz oder Konflikt verhindert den Patch. Der originale Connector-Record und `ErrorKind.Conflict` bleiben erhalten. Atomarer SharePoint-Konfliktschutz ist erst in DEV zu belegen.
- Capabilities entsprechen den ausführbaren Pfaden: nur Asset/System melden List/Create/Edit/Save; die übrigen sieben Registry-Typen melden alle vier Fähigkeiten als false. Das bezeichnet Implementierungsfähigkeit, keine Live-/Produktivabnahme.
- System benötigt zusätzlich genau **zwei** aus der Architektur erzeugte Metadatenzeilen (`System:Title`, `System:Edit:Title`). Native Title-Spalte ist vorhanden; 1.014 andere Metadatenzeilen bleiben unverändert. Die zwei vorhandenen Asset-Title-Zeilen werden nicht erneut übernommen. [Kandidat, Gates, Test- und Freigabeumfang](docs/development/Stage-4.1-P1-Datensatzkern.md).

## P0-Abnahme bleibt die Live-Baseline

P0 ist technisch begrenzt abgeschlossen: ein ausdrücklich freigegebener Asset-Save ID 9 im frischen Player, Title getrimmt, Owner korrekt, Kritikalität Anzeige/Quelle Hoch. Der synthetische Datensatz wurde reversibel entfernt; ID-Filter/Papierkorb und vier Bestandsassets belegt. Frühere ID 8 unter 30439 scheiterte und ist bereinigt. Unterstütztes Studio-Rebinding der kanonischen Personensuche und gezieltes Publish sind erforderlich; der alte Player wurde ohne Save verworfen. Studio 184 ohne Formel-/Laufzeitbefunde, mit 56 Accessibility-Befunden und zwölf Leistungswarnungen. [P0-Belege und Grenzen](docs/development/Stage-4.1-P0-Abnahme.md). Daraus folgt keine vollständige Asset-, Rollen- oder Produktivfreigabe.

## Gates und Git

P1: **624 tatsächliche Offline-Power-Fx-Assertions / Exit 0** (137 Capability + 212 Choice + 275 Record Core); 51 mehrzeilige Formeln erfolgreich geparst. Recordtests verwenden die tatsächlichen Load-Projektionen, Hydrierung, Save-Payloads, Guards und Galerieabfragen; synthetische Voll-/Leerwerte sowie 3.000-Zeilen-Fixtures. Der lokale Fixture-Test ist kein Nachweis der Serverdelegation.

PAC 2.9.3 Build / Exit 0; SourceCode-Pack/-Unpack vier YAMLs unverändert, Artefaktprüfung 4/4. Architektur/Konsistenz, PowerShell-Syntax, beide Title-Verträge, Registry/Runtime, Referenzen, Personenvertrag mit vier negativen Fixtures, Accessibility-Quellvertrag 20 Controls / fünf Galerien, Audit und Diff bestehen am Kandidaten jeweils mit Exit 0; Exit-Codes im P1-Handoff. CI am Implementierungshead `ebdf97e1888fbf87fc4fa5e06f6cc30efb672499`: alle drei Checks erfolgreich (Provisioning Push/PR, Repository PR). Ergebnis des finalen Dokumentationsheads und exakter Head stehen am P1-Draft und in der lokalen Übergabe. Pester fehlt; PAC `canvas validate` nicht verfügbar; Studio, Rollen, echte Delegation und Connector-Konfliktverhalten offen.

Ursprünglicher Workspace `codex/stage-4.1-dev-baseline` mit elf gestagten Dateien und P0-Branch unverändert. P1 im separaten lokalen Clone. Keine Framework-Locks/Runtimeversionen; PR #6 bleibt isoliert/DO NOT MERGE. Keine Secrets, Tenantsettings, Personen-/Log-/Buildausgaben neu versioniert; bestehendes versioniertes msapp als geprüftes Solution-Artefakt aktualisiert.

## Primäres nächstes Arbeitspaket

**P1 · DEV-Abnahme des Datensatzkerns**, Modellklasse `deep-reasoning`: genau zwei System-Title-Metadatenzeilen, Kandidat 30441 importieren, unterstütztes Studio-Rebinding/Checker, gezielte Veröffentlichung und frischer Player. Je ein synthetisches Asset/System anlegen, danach über Liste/ID öffnen, nur den Titel ändern, erneut öffnen und alle übrigen gemappten Werte mit der Quelle vergleichen; kontrollierter Asset-Konflikttest und reversible Bereinigung ausschließlich dieser zwei Testdatensätze. Umfang und Stop-Kriterien stehen im P1-Dokument. Neue Live-Writes benötigen diese konkrete Freigabe; frühere P0-Save-Freigaben sind verbraucht. P2 erst nach belegtem P1-Round-Trip.
