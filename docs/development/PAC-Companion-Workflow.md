# PAC-Workflow im Developer Companion

## Zweck

Der Companion unterstützt einen kontrollierten Round-Trip zwischen Power Apps DEV und Git. Die DEV-Umgebung wird ausschließlich über eine lokale, nicht versionierte Konfiguration adressiert.

## Lokale Konfiguration

```bash
cp tools/companion/local.settings.example.json tools/companion/local.settings.json
```

Beispiel:

```json
{
  "environmentUrl": "https://YOUR-ORG.crm4.dynamics.com",
  "solutionUniqueName": "GovernancePortal",
  "authProfileName": "GovernancePortal-DEV"
}
```

Optional kann `deploymentSettingsFile` auf eine lokale oder versionierte PAC-Deployment-Settings-Datei zeigen.

## Studio nach Git

1. App in Power Apps Studio speichern und veröffentlichen.
2. **PAC prüfen**.
3. **DEV auswählen**.
4. **Solution aus DEV exportieren**.
5. **Solution entpacken**.
6. **Canvas synchronisieren**.
7. **Git-Diff anzeigen**.
8. Fachliche Studio-Änderungen prüfen.
9. Vollständigen Build ausführen.

Der Export wird unter `artifacts/inbound/` abgelegt. Die Solution wird kontrolliert nach `powerplatform/solution/` entpackt. Anschließend wird die enthaltene `.msapp` in den kanonischen SourceTree `powerplatform/canvas/GovernancePortal/` überführt.

## Git nach DEV

1. Vollständigen Build ausführen.
2. **Solution nach DEV importieren**.
3. Import/Publikation nur im konkret freigegebenen Umfang: Stage 4.1 importiert ohne Publish All, prüft den Postexport und öffnet den Kandidaten im Studio. Personen-Items unterstützt neu binden, kanonische Formel erhalten, Checker prüfen; anschließend nur diese App gezielt speichern/veröffentlichen. Ein Import kann die Canvas-Version bereits als Live markieren, ohne dass Studio den SourceCode erfolgreich geladen hat.
4. Frischen Player öffnen und den ausdrücklich freigegebenen DEV-Smoke-Test durchführen. Bei Studio-/Quellenfehler zuerst lokal einen neuen Kandidaten bauen; dessen DEV-Übernahme erneut konkret freigeben.
5. Erst danach den vollständigen Git-Release starten.

## Sicherheitsgrenzen

- Die lokale Konfigurationsdatei wird durch `.gitignore` ausgeschlossen.
- Export, Unpack und Canvas-Sync sind getrennte Aktionen.
- Vor dem Release ist ein sichtbarer Git-Diff vorgesehen.
- Import und Publish zielen ausschließlich auf die konfigurierte DEV-URL.
- Der Companion akzeptiert keine freien Shell-Kommandos.
- `pac canvas pack/unpack` ist in aktuellen PAC-Versionen als veraltet markiert. Es wird hier weiter verwendet, weil das Repository bereits den SourceCode-Layout-Workflow nutzt. Eine spätere Migration auf native Power Platform Git Integration ist separat zu planen.
