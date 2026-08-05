# Stage 4.0 – Object Provider Foundation

## Ziel

Stage 4.0 überführt die bisher fest im Canvas-Code verdrahteten Objektzugriffe in eine explizite, prüfbare Provider-Schicht. Die fachlichen Objekttypen werden damit schrittweise einheitlich für Listenansicht, Neuerfassung, Laden, Bearbeiten und Speichern registriert.

## Ausgangslage

Stage 3.6 stellt einen dynamischen Editor mit Choice-, Lookup- und Personenprovidern bereit. Vollständige Save-Provider existieren aktuell nur für `Asset` und `System`. Die übrigen fachlichen Objekttypen sind in Navigation und Metadaten vorhanden, besitzen aber noch keine einheitlich deklarierte Laufzeitunterstützung.

## Neuer Registry-Vertrag

Die Datei `powerplatform/config/ObjectProviderRegistry.json` ist die technische Registrierung der typisierten Objektprovider. Pro Objekttyp werden mindestens festgelegt:

- `objectTypeKey`
- physische SharePoint-Datenquelle
- Titel-, Governance-ID- und Aktiv-Feld
- Unterstützung für Listenansicht, Neuerfassung, Bearbeiten und Speichern

Registrierte Kernobjekte:

- Asset
- System
- Contact
- Incident
- Problem
- Change
- Risk
- Control
- Measure

`Asset` und `System` sind bereits vollständig für Edit/Save freigeschaltet. Die übrigen Provider starten bewusst mit Listen- und Create-Fähigkeit; Edit/Save wird je Provider erst nach implementiertem Load-/Save-Mapping aktiviert.

## Build-Gate

`Validate-ObjectProviderRegistry.ps1` prüft:

- Registry und Schema-Version vorhanden
- keine doppelten `objectTypeKey`
- alle Kernobjekte registriert
- Pflichtattribute gefüllt
- keine inkonsistente Capability-Kombination

Der vollständige Build bricht bei einer ungültigen Registry ab.

## Nächste Implementierungsschritte

1. Registry in `App.OnStart` als typisierte `colObjectProviderRegistry` spiegeln.
2. einheitlichen Record-List-Cache `colObjectRecords` einführen.
3. statische Provider-Zweige für alle registrierten SharePoint-Listen implementieren.
4. Objektliste nach Auswahl eines Objekttyps laden.
5. Record-Auswahl und Edit-Modus mit Defaultwerten implementieren.
6. Load-/Save-Mapping für Incident, Problem und Change ergänzen.
7. danach Risk, Control, Measure und Contact ergänzen.

## Abnahmekriterien dieser Zwischenstufe

- Registry enthält alle neun Kernobjekte.
- Build validiert die Registry automatisch.
- Asset und System sind als vollständig unterstützt markiert.
- Noch nicht implementierte Edit-/Save-Provider werden nicht fälschlich als verfügbar ausgewiesen.
- Der weitere Canvas-Ausbau kann ohne zusätzliche hart codierte Navigationslogik erfolgen.
