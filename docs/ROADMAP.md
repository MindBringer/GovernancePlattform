# Governance Portal Roadmap

Stand 27. November 2026

Die Betriebs-App läuft in IT-Steinicke auf **Beta 7** (`1.0.0-beta.7`, Canvas 234, Solution `1.0.0.30529`). P14 ergänzt das Prozessregister, die Business-Impact-Analyse und dokumentierte BCM-Übungen. Für den ersten Copilot-Import stehen die Fachbearbeitung über die Entra-Gruppe IT und das mehrzeilige Feld **Asset-Beschreibung** bereit. [Rollout und Rollenabnahme](GOV-PORTAL-LIEFERPLAN.md#it-zugriff-und-asset-beschreibung)

**Nächster Schritt ist der kuratierte Import einer realen Asset-/Prozesskette mit Copilot.** Eine fachkundige Person erstellt mit dem [veröffentlichten Prompt](COPILOT-ERSTBEFUELLUNG.md) genau einen zusammenhängenden Vorschlagsblock. Die verantwortliche Person bestätigt dessen Umfang und Inhalte. Ein Admin übernimmt die bestätigten Einträge und Beziehungen in Beta 7 und prüft sie mit der vorgesehenen Leserrolle. Die [Durchführung für Admins](COPILOT-IMPORT-ADMIN-ABLAUF.md) beschreibt den Weg bis zur Betriebsfreigabe für P7b.

## 1. Technischer Entwicklungspfad

Beta 7 baut auf dem bestehenden Produktpfad auf.

1. Stage 3.6 – dynamischer Editor / Choice-, Lookup- und Personenprovider
2. Stage 3.7 – Developer Companion / lokaler Git- und Audit-Workflow
3. Stage 4.0 – Object Provider Foundation
4. danach schrittweise vollständige Load-/Edit-/Save-Unterstützung der registrierten Kernobjekte

NIS2 ändert diese Reihenfolge nicht und darf keine parallele Implementierungsschiene erzeugen.

## 2. NIS2 als fachlicher Verbraucher der Plattform

Das NIS2-Dokumentationsprojekt nutzt das Governance Portal langfristig als operative Source of Truth für:

- Assets und Systeme,
- Risiken,
- Controls,
- Maßnahmen,
- Incidents,
- Reviews,
- Findings/Abweichungen,
- Evidence,
- später freigegebene Governance-Dokumente.

Die fachlichen NIS2-Anforderungen werden im Repository `MindBringer/NIS2` dokumentiert. Dieses Projekt übernimmt daraus nur Anforderungen, die ohnehin sinnvoll in das generische Governance-Modell passen.

## 3. NIS2-relevante Roadmap-Erweiterungen – nach aktuellem Provider-Ausbau

### GP-NIS2-01 – Schutzbedarf fachlich von Kritikalität trennen

Ziel:

- eigenes ChoiceSet für Schutzbedarf mit `Normal / Hoch / Sehr hoch`,
- `ConfidentialityRequirement`, `IntegrityRequirement`, `AvailabilityRequirement` darauf ausrichten,
- vorhandenes `Criticality`-Modell unverändert für betriebliche Kritikalität weiterverwenden.

Wichtig:

- keine stille Umdeutung bestehender Werte,
- Migration vorhandener Daten vor Änderung prüfen.

### GP-NIS2-02 – Schutzbedarfsbegründungen ergänzen

Für Assets sollen Begründungen getrennt je C/I/A erfassbar sein:

- Vertraulichkeit,
- Integrität,
- Verfügbarkeit.

Optional später getrennte Review-Metadaten nur dann ergänzen, wenn der normale Asset-Review dafür nicht ausreicht.

### GP-NIS2-03 – Rechtsträger-Zuordnung generisch modellieren

Für Assets, Systeme, Risiken und Controls muss langfristig erkennbar sein, welcher Rechtsträger betroffen ist bzw. ob ein Objekt gruppenweit gilt.

Bevorzugte Zielarchitektur:

- eigener `Organization`-/`LegalEntity`-Objekttyp,
- Relation von Governance-Objekten auf Rechtsträger,
- keine zweckentfremdete Nutzung von `ComplianceScope`.

Eine kurzfristige Choice-Lösung ist nur als Übergang sinnvoll.

### GP-NIS2-04 – Asset-/System-Qualitätsmetriken

Für den späteren NIS2-Betrieb sollen Auswertungen möglich sein, z. B.:

- Assets ohne Owner,
- Assets ohne Rechtsträger,
- Assets ohne aktuelle C/I/A-Bewertung,
- Assets ohne Reviewtermin,
- kritische Assets ohne verknüpfte Systeme,
- Systeme ohne Monitoring-/Backup-/Authentifizierungsstatus.

Die Kennzahlen sollen aus dem vorhandenen Objektmodell abgeleitet werden, nicht in einem separaten NIS2-Datenbestand.

### GP-NIS2-05 – Generisches Finding-/Abweichungsmodell

Für Schwachstellenmanagement, Audits, Reviews, technische Ist-Abgleiche und andere Governance-Abweichungen wird ein generisches steuerbares Objekt benötigt.

P13 modelliert Review- und Audit-Findings mit demselben Lebenszyklus. Für die unterschiedlichen Leserechte liegen sie in zwei SharePoint-Listen. Die erste Ausbaustufe erfasst eine geprüfte Quelle, Verantwortung, Frist, Maßnahme und Abschlussnachweis.

Mindestens erforderlich sind langfristig:

- stabile Governance-ID,
- Finding-/Quelltyp,
- Beschreibung,
- Priorität/Severity,
- Owner,
- Status/Lifecycle,
- Erkannt-am / Zieltermin,
- betroffene Assets/Systeme/Controls/Risiken/Lieferanten/Incidents,
- Maßnahme bzw. Remediation,
- Ausnahme-/Risikoakzeptanz mit Ablauf,
- Verifikationsstatus,
- Evidence-Verknüpfung,
- Review-/Eskalationsfähigkeit.

Das Modell kann später um technische Quellen, zusätzliche Zielobjekte, Priorisierung und Risikoakzeptanz erweitert werden.

## 4. Architektur-/Netzmodell – spätere Roadmap

Das NIS2-Dokument `ARCH-NET-001` beschreibt langfristig Bedarf für:

- Standorte,
- Sicherheitszonen,
- Netzsegmente,
- Kommunikationsbeziehungen,
- Datenflüsse.

Diese Objekte werden **nicht** vorschnell als Freitextfelder auf `Asset` oder `System` ergänzt.

Vor einer Implementierung ist ein eigener Architektur-Slice erforderlich, der entscheidet:

1. welche Objekte eigene Governance-IDs benötigen,
2. welche Relationen erforderlich sind,
3. welche Details im Portal und welche in technischen Fachsystemen verbleiben,
4. wie sensible Netz-/Flow-Daten geschützt werden.

## 5. BIA / Business Service

Für NIS2/BCM wird perspektivisch ein belastbarer Bezug zwischen:

```text
Business Service / Prozess
        ↓
Asset
        ↓
System
        ↓
Risk / Control / Evidence
```

benötigt.

Die erste BIA je Geschäftsprozess umfasst Prozessverantwortung, primäre Asset- und Systemreferenzen, strukturierte Wiederanlaufziele und einen versionierten Übungsnachweis. Die Wiederanlaufziele werden am Prozessdatensatz gepflegt. Die fachliche Freigabe des ersten realen BIA-Falls erfolgt im Rahmen des Copilot-gestützten Imports. [Admin-Ablauf](COPILOT-IMPORT-ADMIN-ABLAUF.md) · [P14 im Lieferplan](GOV-PORTAL-LIEFERPLAN.md#p14--kritische-geschäftsprozesse-und-bcm)

## 6. Priorisierung

Nach der Abnahme der ersten realen Asset-/Prozesskette gilt für NIS2-relevante Änderungen diese Reihenfolge.

1. bestehenden Object-Provider-Ausbau stabil abschließen,
2. Schutzbedarf/Kritikalität sauber trennen,
3. Schutzbedarfsbegründungen,
4. Rechtsträger-Modell,
5. Qualitätsmetriken für Assets/Systeme,
6. generisches Finding-/Abweichungsmodell,
7. danach Architektur-/Netz-/Flow-Modell,
8. Business-Service-/BIA-Modell auf Basis des in P14 veröffentlichten Prozessregisters weiterentwickeln.

Die konkrete Reihenfolge der Punkte 2–6 darf im Governance-Portal-Projekt neu priorisiert werden, wenn Abhängigkeiten oder der generische Plattformnutzen dies sinnvoll machen.

## 7. Abgrenzung zum NIS2-Dokumentationsrepo

`MindBringer/NIS2` darf:

- Anforderungen und Sollmodell dokumentieren,
- Mapping-Lücken benennen,
- diese Roadmap als Zielprojekt referenzieren.

`MindBringer/NIS2` darf **nicht**:

- Architektur-YAMLs dieses Repos verändern,
- Canvas oder Provisioning anpassen,
- technische Implementierung über fremde Feature-Branches steuern,
- operative Portalobjekte erzeugen.

Die Umsetzung bleibt vollständig in der Governance-Portal-Produktentwicklung.
