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

## Canvas 1.0.0-beta.7

- Kritische Geschäftsprozesse unter „Betrieb → Geschäftsprozesse und BCM“ erfassen. Verantwortung, Ausfallfolgen, Wiederanlaufziele und die primäre Asset- und Systemabhängigkeit dokumentieren.
- BIA durch die verantwortliche Person bestätigen und Übungen mit Datum, Ergebnis und genauer Nachweisversion festhalten. Der Workflow prüft Ziele, Rechte und SharePoint-Version.
- Am 26. November 2026 als Solution `1.0.0.30526` in IT-Steinicke veröffentlicht. Schreibablauf, Negativfälle und Lesegrenze wurden mit den beiden Pilotrollen geprüft. [Lieferplan](docs/GOV-PORTAL-LIEFERPLAN.md#p14--kritische-geschäftsprozesse-und-bcm)

## Canvas 1.0.0-beta.6

- Findings unter „Prüfungen“ aus abgeschlossenen Reviews oder Auditdateien erfassen, filtern und mit Verantwortung, Frist, Maßnahme und Abschlussnachweis verfolgen.
- Beim Abschluss die geprüfte Nachweisversion speichern. Veraltete Schreibversuche und Abschlüsse ohne wirksame Maßnahme abweisen.
- Review-Findings für die Leserrolle öffnen und Audit-Findings auf IT und die nötigen Administratoren beschränken.
- Am 26. November 2026 als Solution `1.0.0.30521` in IT-Steinicke veröffentlicht und mit beiden Rollen geprüft. [Lieferplan](docs/GOV-PORTAL-LIEFERPLAN.md#p13--findings-und-abweichungen)

## Canvas 1.0.0-beta.5

- Durchsuchbare Statusansichten für Incidents, Problems, Changes, Risiken, Kontrollen, Maßnahmen, Assets, Systeme, Policies, Procedures und Runbooks.
- Sammelfilter für Fälle mit Handlungsbedarf, genaue Statuswerte und Einträge ohne Status. Direkte ID- und Anlagecode-Suchen bleiben verfügbar.
- Am 26. November 2026 als Solution `1.0.0.30518` veröffentlicht und mit Bearbeiter- und Leserrolle im Live-Player geprüft.

## Canvas 1.0.0-beta.4

- Problems unter „Betrieb“ erfassen, Ursachenanalyse, Workaround und bekannte Fehler pflegen und Incidents sowie Changes zuordnen.
- Zuordnungen im geschützten Problem-Datensatz speichern und Änderungen gegen die native SharePoint-Version prüfen. [Lieferplan](docs/GOV-PORTAL-LIEFERPLAN.md#p12--problems-mit-incident--und-change-bezug)
- Die Betriebsfreigabe für Solution `1.0.0.30514` und die Live-Prüfung beider Rollen sind dokumentiert. [Lieferplan](docs/GOV-PORTAL-LIEFERPLAN.md#p12--problems-mit-incident--und-change-bezug)

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
