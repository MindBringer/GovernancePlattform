# Governance Portal Roadmap

Stand: 2026-10-02 · Ziel: erste relevante Anwendungsfälle zügig und belastbar in der Power App nutzen

## Zielbild und Ausgangslage

Der **erste produktive Umfang** umfasst Assets, Changes, Risks und Evidence in der Power App. Verantwortliche können zugeordnet und nach erneutem Öffnen wieder angezeigt werden. Für diese Objekte lassen sich Reviews planen, durchführen und nachvollziehen. Ein Datensatz ist erst unterstützt, wenn Anlegen, Wiederfinden, Öffnen, Ändern und Speichern mit echten Nutzerrollen geprüft sind. Nicht benötigte Objektarten und Komfortfunktionen folgen später.

Die Architektur definiert Listen, Bibliotheken und Metadaten. P1 ergänzt Listen, Suche, Laden und Bearbeiten für Asset/System auf Basis ihrer bestehenden Save-Mappings (17/16 Felder). DEV 30441/Canvas 185 scheitert beim Studio-Öffnen an einem YAML-Fehler; Reparaturkandidat 30442 ist lokal gebaut, DEV-Abnahme steht aus. Zwei System-Title-Metadaten sind geprüft übernommen; fachliche Testwrites noch ungenutzt. Change/Risk haben keinen ausführbaren Save-Vertrag. Evidence und Reviews sind noch keine abgenommenen App-Abläufe.

**P0 ist technisch in DEV abgeschlossen: Solution 30440 / Canvas 184 Live.** Nach unterstütztem Studio-Rebinding/Checker und gezielter Veröffentlichung wurde genau ein zusätzlich freigegebenes Asset angelegt (ID 9): getrimmter Titel, zugelassenes Testkonto und Kritikalität **Hoch** stimmen in der Quelle; der Testdatensatz ist reversibel bereinigt, alle vier Bestandsassets erhalten. Der Test erfolgte im frischen Player; der alte Player wurde wegen Rücksprung ohne Save verworfen. 347 Offline-Power-Fx-Assertions und Projekt-Gates bestehen. Die erfolgreiche P0-Neuanlage ist keine vollständige Asset-/Produktivabnahme. [Belege und Grenzen](development/Stage-4.1-P0-Abnahme.md).

**Primärer nächster Schritt: P1 · DEV-Fortsetzung mit 30442.** Beide YAML-Beschriftungen korrigiert, echter Parser vor Pack/in CI und vier Regressionstests ergänzt; 624 Offline-Power-Fx-Assertions, 53 geparste Formeln, Build und 18 verfügbare Gates bestehen. Neue Freigabe bezieht sich auf den korrigierten Kandidaten; bereits vorhandene Metadaten werden nicht erneut geschrieben. Studio-/Delegations-/Konfliktprüfung und begrenzte Create/Edit-Round-Trips je eines synthetischen Asset/System bilden den [Abnahmeumfang](development/Stage-4.1-P1-Datensatzkern.md). Modellklasse `deep-reasoning`; P2 beginnt nach diesem Nachweis. Stage-4.1-Integration/Merge und Produktivfreigabe bleiben eigenständige Entscheidungen.

**Schnitt der Einführung:** Die vier genannten Anwendungsfälle und nötigen Querschnittsfunktionen werden vorgezogen. Ein Asset-Pilot ist ein Zwischenziel; weitere Listen werden mit ausführbarem Round-Trip nachfolgend eingebunden.

## Arbeitspakete bis zum ersten produktiven Einsatz

Die Modellwahl beschreibt die **Codex-Arbeit am Paket**, kein KI-Modell im Portal. `standard-reasoning` und `deep-reasoning` sind die Klassen des [lokalen Arbeitsprofils](project/Local-Agent-Workflow.md). Konkrete Empfehlungen beziehen sich auf die [aktuelle offizielle OpenAI-Modellauswahl](https://developers.openai.com/api/docs/guides/model-selection) und werden beim Paketstart gegen die dann verfügbaren Modelle geprüft. Für deterministische Teilaufgaben innerhalb eines Pakets genügt `fast`/GPT-6 Luna (low); die fachliche Abnahme bleibt menschlich.

| Paket | Ergebnis und Abnahme | Abhängigkeit | Modellklasse / Empfehlung |
|---|---|---|---|
| **P0 · Stage 4.1 schließen** | DEV-Testdaten können sicher bereinigt werden; eine Asset-Neuanlage wird gespeichert, in der DEV-Datenquelle verifiziert und bereinigt. App-Checker-Hinweise werden nach Auswirkung bewertet; nicht speicherbare Provider führen nicht in einen scheinbar nutzbaren Speicherdialog. PR #14 bleibt bis zur Abnahme Draft. | **in DEV abgeschlossen (30440/184)** | `deep-reasoning`: belegte Host-/Compiler-/Connector-Kopplung und Datenintegritätsfehler |
| **P1 · Datensatzkern** | Echte Datensatzliste mit Suche/Seitenführung, Laden nach ID, Bearbeiten und Speichern für unterstützte Typen. Provider-Capabilities und UI entsprechen den ausführbaren Pfaden. Fehler, leere Werte und parallele Änderungen werden sichtbar behandelt. Ein Round-Trip mit bestehendem Datensatz besteht. | P0 abgeschlossen; **DEV 30441/185 Studio-Blocker, Reparatur 30442 lokal bereit** | `deep-reasoning` · **GPT-6 Astra, high**: Canvas, SharePoint, Provider und Datenintegrität greifen ineinander |
| **P2 · Asset und Verantwortliche** | Asset anlegen, laden und ändern; Owner, Stellvertretung sowie fachlich/technisch Verantwortliche bleiben nach erneutem Öffnen korrekt. Status, Kritikalität und nächster Reviewtermin sind nutzbar. Nicht unterstützte Feldtypen werden implementiert oder bewusst aus dem Pilotformular entfernt. | P1 | `standard-reasoning` · **GPT-6 Sol, high**: begrenzter Fachtyp mit mehreren Feld- und Personenverträgen |
| **P3 · Change** | Change anlegen, finden und ändern; Bezug zum betroffenen Asset, verantwortliche Person, Genehmiger, Planung, Risiko, Umsetzungs- und Rollback-Plan sowie Status werden gespeichert. Der fachliche Genehmigungsschritt ist eindeutig und nachvollziehbar; automatische Freigabe-Flows sind für den Start nicht nötig. | P1; P2 als Muster | `deep-reasoning` · **GPT-6 Astra, medium**: Lifecycle und Genehmigungssemantik |
| **P4 · Risk** | Risiko anlegen, finden und ändern; Owner, Szenario, Eintritt/Auswirkung, Bewertung, Behandlung und befristete Akzeptanz funktionieren. Bewertungsregel und zulässige Statuswechsel sind dokumentiert und getestet. Verknüpfung zum betroffenen Asset ist nutzbar. | P1; parallel zu P3 möglich | `deep-reasoning` · **GPT-6 Astra, medium**: Bewertungs- und Akzeptanzregeln |
| **P5 · Evidence** | Datei aus der App in die Evidence-Bibliothek hochladen, wiederfinden, öffnen und mit Asset/Change/Risk verbinden. Metadaten, Owner, Version und Zugriffsrechte bleiben beim Wiederöffnen korrekt. | P1; parallel zu P3/P4 möglich | `deep-reasoning` · **GPT-6 Astra, high**: Dateitransfer, Bibliothek, Relationen und Berechtigungen |
| **P6 · Reviews** | Fällige Reviews für den ersten Umfang sind sichtbar. Reviewer kann Objekt und Evidence öffnen, Ergebnis dokumentieren, nächsten Termin setzen und Historie nachvollziehen. Owner-/Reviewer-Rechte werden geprüft. Erinnerungen werden erst automatisiert, wenn der manuelle Ablauf stabil ist. | P2–P5 | `deep-reasoning` · **GPT-6 Astra, high**: objektübergreifender Prozess und Termin-/Statuslogik |
| **P7 · Produktivfreigabe** | End-to-End-Tests mit realen Rollen in einer Vorproduktionsumgebung; Berechtigungen, Audit/Fehlerbehandlung, Datenqualität, Backup/Rückweg, Deployment und Supportweg sind nachgewiesen. Alle vier Objektarten bestehen den Round-Trip, Reviews und Evidence die Verknüpfungstests. Erst danach Produktivimport und Canvas-Veröffentlichung. | P0–P6 | `standard-reasoning` · **GPT-6 Sol, high** für Abnahme/ALM; gezielte Sicherheits- und Datenintegritätsprüfung mit `deep-reasoning`/Astra |

P3, P4 und P5 können nach dem stabilen Datensatzkern in getrennten Branches/Worktrees parallel entstehen. Entscheidungen und Tests bleiben je Paket getrennt. P6 integriert nur tatsächlich abgenommene Objektarten. Ein stärkeres Modell ersetzt weder Maker-/PAC-Prüfung noch Tenant- oder Produktivfreigabe.

### Meilensteine

1. **Asset-Pilot nach P0–P2:** kleine benannte Nutzergruppe, kontrollierte Daten, Owner- und Reviewtermin-Pflege. Change/Risk/Evidence/Review gelten dadurch noch nicht als unterstützt.
2. **Erster produktiver Umfang nach P0–P7:** Asset, Change, Risk, Evidence, Verantwortliche und Reviews in der App. Die Freigabe beruht auf beobachteten Round-Trips, nicht nur auf Schema, CI oder sichtbaren Formularen.

## Ausbau nach der ersten Einführung

**Nächste Provider:** System ist in P1 mit den bestehenden 16 Save-Feldern enthalten; seine vollständigen Fachfelder folgen im Ausbau. Incident und Problem werden danach über denselben Datensatzkern eingebunden; danach Control, Measure und Contact. Die frühere Stage-4.2-Planung für Incident/Problem/Change wird geteilt: Datensatzkern und Change gehören zum ersten Umfang, Incident und Problem folgen. Weitere Objektarten werden erst mit funktionsfähigem Load-/Save-Mapping als unterstützt markiert. Für begrenzte Provider-Implementierung ist `standard-reasoning`/GPT-6 Sol (medium) passend; reine Metadaten- und Testanpassungen können `fast`/GPT-6 Luna (low) übernehmen. Neue generische Verträge oder unklare Datenmigrationen gehen an `deep-reasoning`/GPT-6 Astra.

**Komfort und Automatisierung:** erweiterte Dashboards, automatische Erinnerungen und Eskalationen, Benachrichtigungen, Massenpflege, persönliche Ansichten und zusätzliche Dokumentbibliotheken folgen den abgenommenen Kernabläufen. Das Engineering-Framework-Consumer-Paket gemäß [Issue #7](https://github.com/MindBringer/GovernancePlattform/issues/7) ist ein separates technisches Arbeitspaket; der isolierte Conformance-PR #6 wird nicht nebenbei integriert.

**NIS2-Fachausbau:** Das Repository `MindBringer/NIS2` beschreibt Anforderungen, dieses Repository implementiert generische Portal-Funktionen. Nach dem ersten Einsatz folgen in fachlich bestätigter Reihenfolge:

1. Schutzbedarf (`Normal / Hoch / Sehr hoch`) von betrieblicher `Criticality` trennen; bestehende Werte vor Migration prüfen.
2. C/I/A-Begründungen für Assets ergänzen, ohne Reviewdaten zu duplizieren.
3. Rechtsträger-Zuordnung für Asset, System, Risk und Control als eigenes `Organization`-/`LegalEntity`-Modell klären.
4. Qualitätskennzahlen aus dem Objektmodell ableiten: fehlender Owner/Rechtsträger/Reviewtermin/Schutzbedarf, kritische Assets ohne Systembezug und Systeme ohne Betriebsstatus.
5. Ein generisches Finding-/Abweichungsmodell für Audit, Schwachstellen, Reviews und technische Ist-Abgleiche entscheiden; mindestens mit ID, Quelle, Severity, Owner, Status, Frist, betroffenen Objekten, Maßnahme, Verifikation und Evidence.

Netz-/Architekturmodell (Standorte, Zonen, Segmente, Beziehungen, Datenflüsse) und Business-Service-/BIA-Modell folgen erst nach eigenem Architektur-Slice. Sensible Netzdaten erhalten eine bewusste Schutzentscheidung; RTO/RPO werden nicht redundant gepflegt. NIS2 verändert weder die führende Quelle `architecture/*.yaml` noch die Freigabegrenzen des Portalprojekts.
