# Admin-Ablauf für den ersten Copilot-Import

**Gilt für Governance Portal Beta 7 ab Solution 30529 in IT-Steinicke.** Ziel ist ein realer Geschäftsprozess mit einem eindeutig zugeordneten Asset und System. Wenn fachlich belegt, gehören Risiko, BIA, Kontrollen, Dokumente und Nachweise in denselben Vorschlagsblock.

In Beta 7 bedeutet Import die **kuratierte Übernahme einzelner Einträge über die vorhandenen Formulare**. Copilot recherchiert und erzeugt den Block im Chat. Der Admin prüft ihn als Ganzes und speichert die freigegebenen Teile in Abhängigkeitsreihenfolge. Jeder Speichervorgang wirkt sofort auf seinen Eintrag. Der Block bleibt das gemeinsame Protokoll.

## 1. Konto, Fall und Ablage vorbereiten

1. Öffne die [Governance-Startseite](https://groupsteinicke.sharepoint.com/sites/GovernancePortal/SitePages/Home.aspx) und klicke **Governance Portal öffnen**. Prüfe im Player die Anzeige **1.0.0-beta.7** und oben rechts dein Geschäftskonto. Verwende für Änderungen ein autorisiertes Bearbeiterkonto, für den späteren Lesetest das vorgesehene Lesekonto.
2. Prüfe, ob du in **Governance → Assets in der App öffnen** und **Governance → Systeme in der App öffnen** die Anlageaktion **Neu** siehst. Öffne auch **Betrieb → Geschäftsprozesse und BCM in der App öffnen**. Fehlt ein benötigter Zugang, lass ihn über den bestehenden Rollenweg klären. Plane für die BIA-Bestätigung die Mitwirkung der verantwortlichen Person mit ihrem eigenen Konto ein.
3. Lege einen internen Arbeitsort für **einen Fall** fest, beispielsweise einen vorhandenen, berechtigten Projektordner. Dort bleiben der Vorschlagsblock, die Freigabe und das Übernahmeprotokoll zusammen. Der mögliche Startfall ist IT-Onboarding. Prozess, Owner, Asset und führendes System bleiben Vorschläge, bis die verantwortliche Person sie bestätigt.

## 2. Copilot-Block erzeugen und Rückfragen beantworten

1. Öffne von der SharePoint-Startseite **Copilot-Prompt zur Erstbefüllung** oder in der App **Dokumente → Runbooks** die Prompt-Datei. Kopiere den vollständigen Text in Microsoft 365 Copilot mit dem Geschäftskonto des fachkundigen Nutzers. Der Admin kann den Block auch von dieser Person vorbereiten lassen. [Prompt in der Git-Doku](COPILOT-ERSTBEFUELLUNG.md)
2. Nenne den Prozess, den betroffenen Bereich und den relevanten Zeitraum. Ergänze bekannte SharePoint-, Teams- oder Mail-Quellen als Verweise. Prüfe Copilots Quellenabdeckung. Bei fehlendem Zugriff auf Arbeitsquellen gib gezielt eine für den Fall zulässige Datei oder einen freigegebenen Auszug. Übertrage Quellen mit eingeschränktem Leserkreis nur in den dafür berechtigten Arbeitsbereich.
3. Beantworte die Rückfragen im selben Chat. Fordere eine aktualisierte Fassung mit denselben Blockreferenzen wie `A1` für das Asset und `S1` für das System an. Speichere die Fassung **Zur Admin-Prüfung** im Arbeitsbereich. Ein noch unklarer Pflichtwert bleibt im Block offen und stoppt seine Übernahme.

## 3. Den Block fachlich freigeben

- Prüfe je Zeile **Quelle, Feldwert, vorhandenes Objekt, Beziehung und zulässigen Leserkreis**. Suche im Portal nach Titel, Alias und vorhandener Kennung. Ein Treffer gilt erst nach Abgleich der Quellliste und nativen Listen-ID als derselbe Gegenstand. Generische Bestandsnamen wie „Asset“ allein reichen für eine Wiederverwendung nicht aus.
- Entscheide je Zeile zwischen **wiederverwenden**, **gezielt aktualisieren**, **neu anlegen** oder **zurückstellen**. Halte die Gründe für neue Einträge fest. Die verantwortliche Person bestätigt Prozessgrenze, Ausfallfolgen, Notbetrieb und MTPD, RTO sowie RPO in Minuten. Für eine BIA braucht der Fall ein aktives, als geschäftskritisch markiertes Asset und ein aktives System. RTO muss unter MTPD liegen. RPO 0 bezeichnet null tolerierten Datenverlust.
- Lass die zuständige Freigabeperson die Blockfassung, den Umfang der Änderungen und den Leser- und Nachweiskreis bestätigen. Notiere **Name, Datum und Entscheidung** im Block. Prüfe, ob eine Mail oder Teams-Nachricht als Verweis genügt. Eine in Evidence abgelegte Kopie kann für einen anderen Personenkreis sichtbar werden.

## 4. Freigegebene Einträge in dieser Reihenfolge übernehmen

1. **Asset.** Öffne **Governance → Assets in der App öffnen**. Öffne das bestätigte Bestandsasset oder wähle **Neu**. Übernimm den eindeutigen Titel, Owner, Stellvertretung, Status und vereinbarten nächsten Reviewtermin. Trage freigegebenen Zweck, Einsatzbereich und Zusatzinfos bei Bedarf mehrzeilig in **Asset-Beschreibung** ein. Verlasse das Feld vor dem Speichern, damit die App die Eingabe übernimmt. Öffne das Asset danach erneut und gleiche den Beschreibungstext ab. Lies die native Listen-ID zurück. Für den BIA-Pfad prüfe am bestätigten Eintrag in der SharePoint-Liste **Assets** das Feld **Geschäftskritisch**. Pflege dieses Feld bei Bedarf in SharePoint am exakten Datensatz im bestätigten Umfang.
2. **System.** Öffne **Governance → Systeme in der App öffnen**. Nutze das bestätigte Bestandssystem oder lege über **Neu** den aktiven Systemdatensatz mit Name, Beschreibung, Umgebung und Owner an. Setze **Verknüpftes Asset** auf die bestätigte Asset-ID. Speichere und lies System-ID und Lookup zurück.
3. **Risiko, falls bestätigt.** Öffne **Risiko & Compliance → Risiken in der App öffnen** und wähle den Bestandseintrag oder **Neu**. Erfasse Szenario, Risk Owner, betroffene Asset-ID und die fachlich bestätigten Bewertungen und Behandlung. Halte offene Bewertungen offen. Den Akzeptanzschritt führt der vorgesehene Risk Owner im dafür vorgesehenen Ablauf aus.
4. **Geschäftsprozess und BIA.** Öffne **Betrieb → Geschäftsprozesse und BCM in der App öffnen → Neu**. Erfasse Titel, Ausfallfolgen mit Zeitbezug, Mindestniveau im Notbetrieb und Verantwortliche. Wähle das bestätigte Asset und System per Titel und ID, trage die bestätigten Minutenwerte ein und wähle **Als Entwurf speichern**. Öffne den gespeicherten Eintrag erneut. Die eingetragene verantwortliche Person wählt **BIA bearbeiten → Bewertung bestätigen**, wenn alle Werte stimmen.
5. **Nachweise und optionale Ergänzungen.** Am Asset führt **Nachweise → Datei hinzufügen → Datei ablegen und zuordnen** zur freigegebenen Datei. Prüfe vorher, ob dieselbe Zuordnung bereits besteht. Kontrollen führen unter **Risiko & Compliance → Kontrollen** die Zuordnung zum Risiko. Unter **Maßnahmen** kannst du eine Kontrolle und einen vorhandenen Nachweis zuordnen. Dokumententwürfe legst du im genehmigten Umfang in **Policies**, **Procedures** oder **Runbooks** ab und reichst sie über **Freigabe · ID** ein. Eine BCM-Übung wird erst nach der Durchführung über **Übung dokumentieren** mit Datum, Ergebnis und der ausgewählten Evidence-Version erfasst.

Trage nach jedem Speichern Liste, ID, Version und Zielbezug in das Übernahmeprotokoll ein. Bei Fehler oder unklarer Antwort lade den Datensatz neu und prüfe zuerst SharePoint und die protokollierte ID. Halte den Block auf **Teilweise übernommen**, wenn noch freigegebene Zeilen fehlen. Kläre Berechtigungs- und Datenkonflikte mit der zuständigen Person, bevor du fortsetzt.

**Asset-Kontext.** Halte den geprüften Vorschlag und die native Asset-ID in derselben Blockzeile fest. Ist **Asset-Beschreibung** im Player noch nicht sichtbar, aktualisiere die App. Die SharePoint-Spalte `Assets.Description` ist schreibgeschützt. Die Beschreibung des zugehörigen Systems steht separat im Systemformular.

## 5. Abnahme und Abschluss

1. Öffne Asset, System, Prozess und freigegebenen Nachweis erneut. Gleiche Owner, Termine, Referenzen, Status und Dateiversionen mit dem freigegebenen Block und den zugehörigen SharePoint-Einträgen ab.
2. Wenn der erste Asset-Review im Pilotumfang fachlich ansteht, öffne **Prüfungen → Reviews in der App öffnen**. Wähle **Assets**, gib die Listen-ID ein und wähle **Suchen → Review erfassen**. Die Aktion ist für aktive Objekte mit einem überfälligen oder innerhalb der nächsten 30 Tage liegenden Termin verfügbar. Der dafür berechtigte Reviewer prüft den Nachweis, wählt das tatsächliche Ergebnis und setzt einen Folgetermin nach heute und nach dem bisherigen Termin. Er wählt **Review abschließen** und kontrolliert anschließend **Reviewhistorie** sowie den gespeicherten Folgetermin. Steht der Review später an, halte Termin und Verantwortlichkeit fest. Die vollständige P7b-Abnahme folgt auf den realen Review.
3. Öffne denselben Fall mit der benannten Leserrolle. Prüfe die freigegebenen Objekt- und Nachweisdetails sowie die fehlenden Schreibaktionen im Fachablauf. Bei Abweichungen bleibt der Fall offen. Halte für P7b Pilotstart, Supportkontakt und Rückweg in der Betriebsfreigabe fest.

### Kopiervorlage für das Übernahmeprotokoll

```text
Fall / Blockfassung
Fachliche Freigabe durch / Datum
Bearbeiter / Prozessverantwortung / Leserprüfung
Freigegebener Quellen- und Nachweisumfang
Blockreferenz | Aktion | Zielliste | Listen-ID | Version | Bezug | geprüft durch
Review-ID / Folgetermin
Offene oder zurückgestellte Zeilen
Betriebsfreigabe / Start / Supportkontakt / Rückweg
```

Die ausgefüllte Fassung bleibt im zugriffsberechtigten Arbeitsbereich des Falls. In den Portal-Runbooks liegt die allgemeine Anleitung. [ER-Diagramm](ER-DIAGRAMM.md) · [Lieferplan](GOV-PORTAL-LIEFERPLAN.md#p7b--erster-begrenzter-echtbetrieb)
