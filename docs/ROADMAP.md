# Governance Portal Roadmap

Stand: 2026-09-09

## 1. Aktueller Entwicklungsstrang

Die aktuelle technische Basis folgt weiterhin dem bestehenden Produktpfad:

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

## 5. BIA / Business Service – spätere Roadmap

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

Ein dediziertes Business-Service-/BIA-Modell wird erst eingeführt, wenn der generische Nutzen für Governance Portal geklärt ist. RTO/RPO sollen nicht redundant als Freitext in mehreren Objekten gepflegt werden.

## 6. Priorisierung

NIS2-relevante Änderungen werden in dieser Reihenfolge eingeplant:

1. bestehenden Object-Provider-Ausbau stabil abschließen,
2. Schutzbedarf/Kritikalität sauber trennen,
3. Schutzbedarfsbegründungen,
4. Rechtsträger-Modell,
5. Qualitätsmetriken für Assets/Systeme,
6. danach Architektur-/Netz-/Flow-Modell,
7. danach Business-Service-/BIA-Modell.

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