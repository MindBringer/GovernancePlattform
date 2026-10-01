# Changelog

Dieses Changelog enthält sowohl die Provisioning-/Architektur-Baseline als auch die Canvas-Entwicklung. Die Versionsreihen bleiben getrennt.

## Unreleased

### Canvas Stage 4.1 – Entwicklungsbranch

- P0: Neu-/Save-Befehle prüfen passende Provider-Capabilities, Edit-Modus/ID und Busy-Status vor Mutationen; nicht speicherbare Typen öffnen kein Neuanlageformular.
- Nicht delegierbare Asset-Gesamtzahl aus dem Dashboard entfernt; `30431` nach Freigabe in DEV und Canvas 168 Live geprüft. Asset-Save bleibt ohne erfolgreiche Quellen-/Bereinigungsevidenz offen.
- Lokaler Reparaturkandidat `30432`: verpflichtender nativer Asset-Titel durch Architektur/Metadatengenerator, Guard und getrimmten Patch ohne Fallback; zwei zusätzliche Metadatensätze, bestehende Zeilen unverändert.
- Asset-Kernaktionen auf Classic-Buttons umgestellt; Eingaben/Galerien mit Labels, Tastatur/Fokus und gesperrtem Modal-Hintergrund. 76 Offline-Power-Fx-Assertions sowie CI-Verträge für Asset-Title/Metadaten und Accessibility; Live-Abnahme von `30432` ausstehend.

- Read-only-DEV-Export mit dem lokalen Stage-4.1-Reconciliation-Stand abgeglichen; Personenfeld- und Asset-Speicherlogik in den kanonischen Canvas-Quellcode übernommen.
- Diagnostisches Suchlabel aus dem Quellcode entfernt; Solution-Manifest auf die DEV-Baseline `1.0.0.30428` ausgerichtet und Canvas-/Solution-Paket lokal neu erstellt.
- CI prüft nun auch, ob das versionierte `.msapp` die vier aktuellen Canvas-YAMLs enthält. Studio-Validierung und DEV-Smoke bleiben für die fachliche Abnahme erforderlich.
- Canvas-Version `1.0.0-alpha.4.1.0` zwischen Versionsdatei, App und Entwicklerkonfiguration abgeglichen.
- Object-Provider-Registry in der Canvas-Runtime synchronisiert; Auswahl bindet den aktiven Provider und der Neu-Befehl prüft dessen Create-Fähigkeit.
- Synchronisierer gegen eine fälschlich erkannte Provider-Bindung korrigiert; CI prüft Canvas-Version, Registry und Runtime ohne automatische Reparatur.
- DEV-Baseline `30430` wurde am 28.09.2026 freigegeben importiert und als Canvas 165 Live geprüft; P0-Speicher-/Quellen-/Bereinigungsabnahme des lokalen Reparaturkandidaten `30432` steht vor Stage-4.1-Integration aus.

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
