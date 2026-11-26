# Changelog

Dieses Changelog enthält sowohl die Provisioning-/Architektur-Baseline als auch die Canvas-Entwicklung. Die Versionsreihen bleiben getrennt.

## Unreleased

### Documentation and repository

- Root-README auf das Gesamtprojekt ausgerichtet.
- Architektur und Roadmap auf Provisioning 6.2.5 sowie Canvas Stage 3.4.1 aktualisiert.
- Entwicklungs- und Build-Prozeduren vereinheitlicht.
- konkurrierende Dokumente und den zweiten Canvas-SourceTree entfernt.
- historische Iterations- und Migrationsunterlagen archiviert.
- `DeveloperPlatform.psd1` auf Canvas `1.0.0-alpha.3.4.1` synchronisiert.

## Canvas 1.0.0-beta.3

- Maßnahmen unter „Risiko & Compliance“ erfassen. Verantwortlichkeit und Frist pflegen sowie Kontrollen und vorhandene Nachweisdateien zuordnen.
- Maßnahmen von „Geplant“ bis „Geschlossen“ führen. Für „Wirksam“ verlangt der Ablauf einen zugeordneten Nachweis und ein Prüfergebnis.
- Rollenabnahme und Betriebsfreigabe für Solution `1.0.0.30511` dokumentiert. [Lieferplan](docs/GOV-PORTAL-LIEFERPLAN.md#p11--maßnahmen-kontrollbezug-und-wirksamkeitsnachweis)

## Canvas 1.0.0-beta.2

- Kontrollen unter „Risiko & Compliance“ erfassen, verantwortlichen Personen zuweisen und mit Risiken und vorhandenen Nachweisen verknüpfen.
- Veraltete Verantwortungsänderungen abweisen und wiederholte Zuordnungen anhand desselben Relationsschlüssels erkennen.
- Rollenabnahme und Betriebsfreigabe für Solution `1.0.0.30508` dokumentiert. [Lieferplan](docs/GOV-PORTAL-LIEFERPLAN.md#p10--kontrollen-mit-risiken-und-nachweisen)

## Canvas 1.0.0-beta.1

- Betriebsstörungen und Sicherheitsvorfälle mit Systembezug, Verantwortung, Priorität und Statusverlauf in der App erfassen.
- Statuswechsel gegen die native SharePoint-Version absichern und beide Incident-Arten über die IT-Listenrechte schützen.
- Betriebsfreigabe für Solution `1.0.0.30503` mit Live-Rollenprüfung dokumentiert. [Lieferplan](docs/GOV-PORTAL-LIEFERPLAN.md#p9--betriebsfreigabe-als-beta)

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
