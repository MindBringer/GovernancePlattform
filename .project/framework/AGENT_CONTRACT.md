# Framework Agent Contract

Dieses Dokument ist framework-managed. Es definiert den gemeinsamen Arbeitsvertrag für ChatGPT, Codex und andere Coding-Agenten in allen Consumer-Projekten. Projektspezifische Ergänzungen gehören in `AGENTS.md` und werden vom Framework-Sync nicht überschrieben.

## Einstieg

1. `AGENTS.md` für projektspezifische Regeln lesen.
2. `PROJECT_STATE.md` vollständig lesen.
3. `.project/project.config.json`, `.project/framework.manifest.json`, `.project/framework.lock.json` und `.project/state/current.json` lesen.
4. Installierte Framework-Version und Lock-Integrität feststellen. Eine neuere zentrale Framework-Version ist allein nur ein Hinweis und blockiert project-owned Arbeit nicht.
5. Live-Zustand mit `git status -sb`, aktuellem Commit, offenem PR und CI abgleichen.
6. Falls vorhanden `tools/companion/project_runtime.py`, `project_actions.py` und `project_ui.py` als project-owned Integrationspunkte prüfen.
7. Scope gegen die Ownership-Grenzen des Framework-Manifests prüfen.
8. `python3 tools/framework/project_memory.py` ausführen.
9. `python3 tools/framework/technical_debt.py` ausführen.
10. Genau den dokumentierten Next Step als Default-Scope verwenden.

## Iterationsvertrag

```text
Repo-Memory lesen
→ Live-Git/PR/CI rekonstruieren
→ Framework-Version, Lock und Ownership prüfen
→ Scope, Nicht-Ziele und Datenrisiko festhalten
→ implementieren
→ Project Actions / Project Runtime / Project UI / fachliche Tests
→ projektspezifische Tests, Runtime-Health und Build-Gates
→ Altlasten-/Legacy-Sweep
→ Doku-/ADR-/Runbook-Impact aktualisieren
→ Project Memory Contract
→ Release/PR/CI
→ Release-Historie
→ genau einen Next Step hinterlassen
```

## Framework Touch & Integrity Contract

- Ein Versionsdelta zwischen installiertem Consumer-Framework und aktueller zentraler Template-Version ist **kein allgemeiner Stopper**. Rein project-owned Änderungen dürfen auf der installierten, gültig gelockten Framework-Version weiterentwickelt und released werden.
- Vor jeder Iteration ist trotzdem festzustellen, ob eine neuere zentrale Framework-Version existiert und ob der Scope framework-managed Bereiche oder generische Framework-Verträge berührt.
- Sobald eine geplante Änderung eine framework-managed Datei, ein Framework-Schema, einen Framework-Vertrag oder generische Companion-Funktionalität verändern würde, ist Consumer-Implementierung an dieser Stelle zu stoppen.
- Framework-Änderungen werden ausschließlich im zentralen `Project-Engineering-Template` auf Basis seines aktuellen zentralen Stands entwickelt, getestet und released.
- Vor Framework-Arbeit wird der zentrale Template-Clone aktualisiert (`fetch`/`pull --ff-only`) und sein Framework-Lock verifiziert. Ein veralteter Consumer darf nicht als Ausgangsbasis für eine generische Framework-Änderung dienen.
- Erst nach veröffentlichtem Framework-Update wird der Consumer kontrolliert mit `tools/framework/sync.py check/apply --source <aktuelles Template>` synchronisiert.
- Consumer dürfen framework-managed Änderungen nicht durch lokales Neugenerieren des Framework-Locks legitimieren. Ein neuer Consumer-Lock entsteht nur durch Adoption oder kontrollierten Framework-Sync.
- Abweichende Hashes framework-managed Dateien sind Framework-Drift und blockieren Build/Release, unabhängig davon, ob die installierte Framework-Version grundsätzlich noch unterstützt ist.
- Generische Erkenntnisse aus Consumer-Projekten werden upstream im zentralen Template umgesetzt; project-owned Fachlogik bleibt im Consumer.

Kurzform:

```text
Versionsdelta                    → erlaubt / Hinweis
project-owned Änderung           → erlaubt
Framework-Drift                  → blockiert
Framework-Touch im Consumer      → upstream erforderlich
Framework-Touch auf altem Stand  → zuerst zentrales aktuelles Template
Consumer-Lock neu erzeugen       → nicht erlaubt
```

## Verbindliche Regeln

- Repository-Zustand ist die persistente Source of Truth; Chats sind nur Arbeitskontext.
- Keine Secrets, Tenant-Credentials oder lokale Settings committen.
- Keine beliebigen Shell-Kommandos aus Browser oder deklarativer Config ausführen.
- Actions und lokale Runtimes verwenden explizite Argumentlisten; keine Shell-Interpolation dynamischer Werte.
- Gefährliche Actions benötigen explizite Confirmation oder ein projektspezifisches Token.
- Release-Gates müssen reproduzierbar und lokal wie in CI ausführbar sein.
- Neue Legacy-/Compatibility-Schichten benötigen Begründung und Retirement-Trigger.
- Tote Implementierungen, Dubletten und obsolete Doku werden bei jeder Iteration aktiv geprüft.
- Doku wird in derselben Änderung wie Code aktualisiert.
- Nach Abbruch muss ein neuer Agent allein aus Repository, Git/PR/CI und dem dokumentierten Next Step weiterarbeiten können.

## Project Runtime Contract

- Framework-Runtimecode unter `tools/companion/core/project_runtime.py` ist framework-managed.
- Projektspezifische Runtime-Registrierung gehört ausschließlich in `tools/companion/project_runtime.py`.
- Runtime-Kommandos sind code-reviewte Argumentlisten und werden mit `shell=False` gestartet.
- Runtime- und Health-URLs müssen auf Loopback-Adressen zeigen; Engineering Companion und Produktserver verwenden getrennte Ports.
- Eine bereits laufende gesunde Runtime gilt als extern und darf vom Companion nicht beendet werden.
- Der Companion beendet ausschließlich Child-Prozesse, die er selbst gestartet hat.
- Produktstart, Workspace-Recovery, virtuelle Umgebung oder Dependency-Bootstrap bleiben project-owned und werden nicht in den Framework-Core verschoben.

## Project UI Contract

- Framework-Webdateien unter `tools/companion/web/` werden nicht projektspezifisch verändert.
- Projektspezifische Cockpit-Views gehören in `tools/companion/project_ui.py`.
- Optionale project-owned Renderer/CSS/Bilder gehören ausschließlich nach `tools/companion/project_web/`.
- View-Provider sind read-only und liefern JSON-Objekte. Mutationen, Deployments und Neustarts bleiben registrierte Actions in `project_actions.py` oder klar abgegrenzten Projektmodulen.
- Custom Assets benötigen `ui.projectUI.allowCustomAssets=true` und dürfen nicht auf externe Script-URLs oder Repository-Escape-Pfade zeigen.
- Neue UI-Funktionen müssen den bestehenden Action-/CSRF-/Confirmation-Vertrag wiederverwenden statt parallele Mutationsendpunkte zu schaffen.
- Ein Framework-Update darf project-owned Runtime, UI und Actions nicht überschreiben.

## Existing Repository Adoption

- `tools/framework/adopt_existing.py` darf fachliche Quellen nicht löschen.
- Standardmäßig ist ein sauberer Worktree erforderlich.
- Überschriebene Framework-/Bootstrap-Dateien werden vor der Adoption gesichert.
- Die Adoption erzeugt project-owned Action-, Runtime- und UI-Adapter sowie Config, State und Framework Lock.
- Die fachliche Zuordnung der Adapter erfolgt erst im Consumer-Branch.

## Release-Vertrag

Vor Merge müssen mindestens konsistent sein:

- Projekt- und Framework-Version;
- Framework-Manifest, Config und Lock;
- keine unkontrollierte Drift framework-managed Dateien;
- aktuelles Iterationsziel, Status, Nicht-Ziele und Datenrisiko;
- Technical-Debt-Review ohne harte Blocker;
- erforderliche Dokumentationsbereiche `current` oder `n/a`;
- genau ein Next Step;
- grüne Framework- und projektspezifische Gates;
- vollständiger Handoff in `PROJECT_STATE.md`.

Persistente State-Dateien dürfen Live-Branch/Live-Commit nicht als dauerhaft gültigen Zustand vortäuschen; aktuelle Git-Daten werden immer aus dem Repository ermittelt.
