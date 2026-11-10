# Lieferplan für das Governance Portal

Stand 10. November 2026. Ziel ist ein produktiver Einstieg mit einer kleinen, benannten Gruppe, die Assets und Verantwortliche pflegt. Die nächste Ausbaustufe verbindet Assets, Changes und Risks mit Evidence und dem manuellen Reviewprozess.

## Umgebungsmodell bis zur vollständigen Produktivfreigabe

Entwicklung, Tests und Abnahme laufen in derselben Power-Platform-Umgebung und in der bestehenden Lösung Governance Portal. Die Umgebung übernimmt nach der jeweiligen Freigabe den produktiven Betrieb. Abnahme und Produktivnutzung sind Freigabestufen derselben App-Version. Getestet wird bis zur Freigabe mit synthetischen Datensätzen und den vorgesehenen Rollen.

Die Pilotrollen sind Bearbeitung, Lesen und Betriebsfreigabe. Die benannten Konten stehen in der internen Übergabe. Die Lesegrenze wird im Player und an der SharePoint-Datenquelle geprüft.

Nach vollständiger Produktivfreigabe und Aufnahme des Echtbetriebs wird für die Weiterentwicklung eine separate DEV-Instanz eingerichtet. Dann werden Zielbindungen, Zugriff, Testdaten und der Freigabeweg für die getrennten Umgebungen festgelegt.

## Pakete und Abnahmekriterien

| Paket | Ergebnis | Grün, wenn |
|---|---|---|
| GP-00 Lieferplan | Reihenfolge, Verantwortlichkeiten und Freigabestufen für die bestehende Lösung sind nachvollziehbar. | Der Plan enthält eine abgrenzbare erste Pilotstufe, Abnahmekriterien pro Paket und einen Rückweg. |
| P4d.1 Risk-Vorprüfung | Der lokale Risk-Kandidat ist mit der tatsächlichen DEV-App, den Verbindungen, dem Schema und den Runtime-Metadaten abgeglichen. | Zielidentität, Kandidatenhash, letzte gespeicherte und veröffentlichte App-Version sowie Abweichungen sind belegt. Der Testumfang und seine Schreibgrenzen sind vor dem Import festgelegt. |
| P7a.1 Asset-Pilot vorbereiten | Für die bestehende Lösung ist ein Releasepaket mit auf Assets begrenztem Pilotumfang gewählt. Die Pilotgruppe, ihre Rollen und die Betriebsverantwortung stehen fest. | Benannte Bearbeiter und Leser können anhand des Rollenkonzepts geprüft werden. Zielbindungen, Pilotdatensätze, Freigabeperson und Rückweg sind dokumentiert. Die tatsächlich erreichbaren App-Pfade entsprechen dem Pilotumfang. |
| P7a.2 Asset-Pilot abnehmen und produktiv freigeben | Asset anlegen, finden, bearbeiten und erneut öffnen. Owner, Stellvertretung, Kritikalität und Reviewtermin bleiben korrekt. | Der Round-Trip, ein negativer Rollentest, konkurrierende Änderungen, Datenqualität, Audit, Rückweg und Supportübergabe sind mit realen Rollen in der bestehenden Lösung geprüft. Nach Betriebsfreigabe besteht der Pilot-Smoke mit genau der abgenommenen Live-Version. |
| P4d.2 Risk in DEV abnehmen | Die geprüfte App-Version läuft in DEV mit dem nativen Risk-Adapter. | Live-Monitor und SharePoint-Readback belegen Draft, Bewertung, Behandlung, explizite Akzeptanz durch den gespeicherten Risk Owner, Abschluss, Leerwerte und Konfliktverhalten. Eine fremde Person kann das Risiko nicht akzeptieren. Die bestehenden Asset-, System- und Change-Pfade bestehen die Regression. |
| P5a Evidence für Assets | Ein Nutzer kann einen Nachweis aus der App hochladen, einem Asset zuordnen und wieder öffnen. | Datei, Metadaten, Autorisierung, Link und Versionsverhalten stimmen nach dem Wiederöffnen. Ein Fehler zwischen Dateiablage und Verknüpfung bleibt sichtbar und kann gezielt behoben werden. |
| P5b Evidence für Change und Risk | Derselbe Evidence-Pfad unterstützt abgenommene Changes und Risks. | Die Zuordnung verwendet die richtige Objektart und ID. Fremde oder unzugängliche Ziele werden abgewiesen. Die Asset-Verknüpfung besteht weiterhin. |
| P6 Manueller Review | Ein Reviewer sieht fällige Reviews, öffnet Objekt und Evidence, erfasst das Ergebnis und setzt den nächsten Termin. | Reviewer- und Owner-Rechte, Terminfortschreibung und Historie sind im Round-Trip nachgewiesen. Der Ablauf erfordert eine ausdrückliche Reviewer-Entscheidung. |
| P7b Erweiterte Produktivfreigabe | Die Pilotgruppe kann die zusammenhängenden Kernabläufe für Assets, Changes, Risks, Evidence und Reviews produktiv nutzen. | Der integrierte Round-Trip besteht mit den vorgesehenen Rollen. Datenbindungen, Audit, Betrieb, Rückweg und Support sind für den erweiterten Umfang abgenommen. Die abgenommene Live-Version und der Übergang in den Echtbetrieb sind dokumentiert. |

P4d.1 ist der nächste Entwicklungsschritt. P7a.1 kann parallel vorbereitet werden. P7a.2 hängt von P7a.1 und der vorhandenen DEV-Abnahme für Assets ab. P4d.2 folgt auf P4d.1. P5a benötigt einen abgenommenen Asset-Datensatzkern. P5b benötigt zusätzlich die native Change- und Risk-Abnahme. P6 setzt die abgenommenen Objekt- und Evidence-Pfade voraus, die im Review angeboten werden. P7b schließt den erweiterten Umfang ab.

## Abschluss und Veröffentlichung je Paket

1. Ausgangscommit, fachlichen Umfang, Ziel und Abnahmekriterien festhalten. Bei App-Paketen zusätzlich Solution-Version und Paket-Hash erfassen.
2. Auf einem Entwicklungsbranch arbeiten und die zum Paket gehörenden Änderungen und Tests gemeinsam prüfen. Die verfügbaren Projekt-Gates am Abschluss ausführen und ihre Ergebnisse zum Kandidaten dokumentieren.
3. Den geprüften Commit an beide GitHub-Repos pushen und den Commit auf beiden Zielbranches nachlesen. CI-Ergebnisse beziehen sich auf diesen Commit. Unterschiede bei erforderlichen Checks oder ein fehlgeschlagener Push bleiben bis zur Klärung sichtbar.
4. Grüne Funktionspakete gezielt zur Abnahme in der bestehenden Lösung veröffentlichen. Vor jedem Import und Publish App, Paket, aktuellen Live-Stand, Testzugriff und Rückweg prüfen. Die veröffentlichte Version mit Player, Rollen und Datensatz-Readback abnehmen. Ein Paket mit offenem Pflichtnachweis bleibt in der aktuellen Stufe.
5. Für den Echtbetrieb die jeweilige P7-Stufe mit Betriebsfreigabe und Pilotgruppe abnehmen. Bei Grün die abgenommene Live-Version für den festgelegten Umfang zur Nutzung freigeben und den vereinbarten Pilot-Smoke ausführen. Ein kritischer Smoke-Fehler führt zum vorher vereinbarten Rückweg.

Im gemeinsamen Repo stehen Status, Commit, Paket-Hash, Abnahmekriterien und bereinigte Testergebnisse. Operative Ziel-IDs, Personenzuordnungen, native Exporte und Monitor-Rohdaten gehören in die interne Übergabe. Der Quellcommit wird für beide Remotes gemeinsam geprüft.
