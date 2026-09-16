# Self-Hosted CI

## Ziel

Der verpflichtende Engineering Contract läuft standardmäßig auf einem eigenen GitHub Actions Runner mit dem Label `local-ci`. Dadurch hängt der normale Entwicklungs- und Releaseflow nicht vom GitHub-hosted Minutenkontingent ab.

Die GitHub-hosted Cross-Platform-Matrix bleibt als **manuell gestarteter Kompatibilitätstest** erhalten und blockiert den regulären Release nicht, solange sie nicht für denselben aktiven Release-Head manuell gestartet wird.

Seit Framework 1.3.12 gilt zusätzlich ein expliziter **Hermeticity-Vertrag**: Ein persistenter Self-Hosted Runner darf keinen alten Checkout-Zustand, keine persönliche lokale Workspace-/Profilkonfiguration und keine implizit geerbten Secrets in den Required Engineering Contract hineintragen.

## CI-Vertrag

Automatisch bei Pull Requests und `main`:

```text
Engineering Contract
└─ Local CI · required
   └─ runs-on: [self-hosted, local-ci]
```

Nur manuell über GitHub Actions:

```text
Hosted Compatibility Matrix
├─ Ubuntu · Python 3.12 · full
├─ Ubuntu · Python 3.14
├─ Windows · Python 3.12
└─ macOS · Python 3.12
```

Der automatische Workflow nutzt `concurrency.cancel-in-progress=true`. Wird derselbe PR-Branch erneut gepusht, wird ein alter noch laufender Engineering-Contract für diesen PR abgebrochen und nur der neue Head validiert.

## Hermetischer Checkout

Der Required Workflow verwendet `actions/checkout@v4` ausdrücklich mit:

```yaml
fetch-depth: 0
clean: true
persist-credentials: false
```

`clean: true` erzwingt bei einem wiederverwendeten Runner-Workspace einen sauberen Checkout. Die Checkout-Action führt dafür den Git-Cleanup-/Reset-Vertrag aus; stale Build-, Cache-, Test- oder lokale Konfigurationsartefakte dürfen nicht aus einem vorherigen Run weiterleben.

`persist-credentials: false` verhindert, dass das vom Checkout verwendete GitHub-Credential nach dem Checkout als Repository-Git-Credential liegen bleibt. Falls ein späterer projektspezifischer CI-Schritt bewusst GitHub-Schreibzugriff benötigt, muss dieser Zugriff separat und explizit modelliert werden; der Required Engineering Contract erhält ihn nicht implizit.

Direkt nach Runtime-Prüfung läuft:

```text
python3 tools/framework/ci_hermeticity.py
```

Der Gate prüft vor allen fachlichen/Framework-Tests:

- Working Tree inklusive untracked Dateien ist sauber;
- `cwd` entspricht im GitHub-Run dem `GITHUB_WORKSPACE`;
- lokale Dateien wie `.env` oder `local.settings.json` sind im CI-Checkout nicht vorhanden, auch wenn sie normalerweise ignoriert würden;
- sensible Environment-Variablen wie `*_TOKEN`, `*_SECRET`, `*_PASSWORD`, `*_API_KEY` werden nicht still vom Runner-Prozess geerbt;
- externe Runtime-/Workspace-Pfade wie `*_WORKSPACE`, `*_CONFIG_HOME`, `*_PROFILE_ROOT` oder `*_DATA_DIR` zeigen nicht unbemerkt auf persönliche Pfade außerhalb von Repository bzw. `RUNNER_TEMP`.

GitHub-/Actions-/Runner-interne Variablen (`GITHUB_*`, `ACTIONS_*`, `RUNNER_*`) sind vom Framework erlaubt. Eine projektspezifische zusätzliche Environment-Variable darf nur bewusst freigegeben werden:

```text
ENGINEERING_CI_ALLOWED_ENV=NAME1,NAME2
```

Diese Allowlist ist eine ausdrückliche Projektentscheidung und kein automatischer Fallback. Secrets oder Live-Runtime-Kontext sollen in normalen Required Gates grundsätzlich nicht erforderlich sein. Reale Tenant-, DEV-, Server-, Hardware- oder Provider-Smokes gehören in explizite Runtime-/Deployment-Evidenz und nicht in den hermetischen Repository-CI-Vertrag.

## Voraussetzungen des Local Runners

Der Self-Hosted Runner bringt seine Runtime selbst mit. Der required Workflow installiert Python bewusst **nicht** über `actions/setup-python`, weil diese Action auf Self-Hosted-Systemen einen GitHub-Hosted-Toolcache voraussetzen kann und dort unnötige Schreib-/Installationsprobleme erzeugt.

Erforderlich:

```text
Git
Python >= 3.12
python3 im PATH
Netzwerkzugriff auf GitHub Actions
```

Der Workflow prüft `command -v python3`, `python3 --version` und bricht bei Python < 3.12 mit einer eindeutigen Meldung ab. Auf dem aktuellen macOS-/Bazzite-Ziel ist damit keine Laufzeitinstallation pro CI-Job nötig.

## Runner einmalig registrieren

GitHub öffnen:

```text
Repository
→ Settings
→ Actions
→ Runners
→ New self-hosted runner
```

Das tatsächliche Betriebssystem und die Architektur des Runner-Rechners auswählen. GitHub zeigt anschließend die aktuellen Download- und Registrierungsbefehle. Diese Befehle verwenden, statt Versionsnummern oder Registration Tokens aus diesem Runbook zu kopieren.

Bei der Registrierung zusätzlich das benutzerdefinierte Label eingeben:

```text
local-ci
```

Empfohlener Runner-Name:

```text
<hostname>-local-ci
```

Beispiel:

```text
jans-macbook-local-ci
bazzite-local-ci
```

## Betriebsmodus

Für einen ersten Test kann der Runner interaktiv gestartet werden. Für den dauerhaften Betrieb den von GitHub mitgelieferten Service-Mechanismus des jeweiligen Runner-Pakets verwenden.

Der Runner soll:

- unter einem normalen Benutzerkonto laufen, nicht als `root`/Administrator;
- nur für vertrauenswürdige private Repositories verwendet werden;
- Internetzugriff auf GitHub und die von Actions benötigten Download-Endpunkte haben;
- Git und Python >= 3.12 lokal bereitstellen;
- keine unnötigen persönlichen Secrets oder privilegierten Systemzugriffe erhalten;
- keine persönliche Produkt-Workspace-/Profilkonfiguration als Service-Environment erhalten.

## Kontrolle in GitHub

Unter `Settings → Actions → Runners` muss der Runner erscheinen als:

```text
Idle
Labels: self-hosted, <os>, <arch>, local-ci
```

Sobald ein PR einen neuen Head erhält, soll der Check

```text
Engineering Contract / Local CI · required
```

vom lokalen Runner übernommen werden.

## Lokale Kontrolle

Der Workflow führt auf jedem PR-Head aus:

```text
Runtime / Python >= 3.12
Self-hosted CI hermeticity
Repository audit
Python syntax check
Technical debt check
Project memory contract
Validate framework
Framework tests
Template bootstrap smoke
Verify framework lock
```

Damit bleibt die gleiche Releasequalität erhalten; der Ausführungsort ist lokal, der Prüfkontext bleibt trotzdem repository-deterministisch.

## Hosted Compatibility Matrix

Die Hosted-Matrix wird nicht automatisch gestartet. Wenn GitHub-hosted Minuten verfügbar sind und ein echter Cross-Platform-Nachweis benötigt wird:

```text
GitHub
→ Actions
→ Hosted Compatibility Matrix
→ Run workflow
```

Typische Anlässe:

- Änderungen an `start-local.ps1` oder Windows-spezifischem Verhalten;
- Änderungen an Shell-/Dateisystem-Portabilität;
- Framework-Release mit relevanten macOS-/Windows-Runtimeänderungen;
- gezielter Python-3.14-Kompatibilitätsnachweis.

Nicht bei jedem Dokumentations-, Memory- oder Release-Metadatencommit starten.

## Verhalten bei ausgeschöpftem GitHub-hosted Quota

Der reguläre PR-/Releaseflow bleibt verfügbar, weil der required Engineering Contract ausschließlich auf `self-hosted, local-ci` läuft.

Ein ausgeschöpftes Hosted-Kontingent betrifft dann nur einen bewusst manuell gestarteten `Hosted Compatibility Matrix`-Lauf.

Es gibt absichtlich **keinen** Mechanismus `Hosted fehlgeschlagen → automatisch Local`, weil ein echter Testfehler sonst mit einem Quota-Problem verwechselt werden könnte.

## Verhalten wenn der Local Runner offline ist

Ein neuer `Local CI · required`-Job bleibt in GitHub auf `Queued`, bis ein passender Runner mit Label `local-ci` online kommt. Der Release soll in diesem Zustand nicht gemergt werden.

Vorgehen:

1. Runner-Rechner einschalten bzw. Runner-Service starten.
2. Unter `Settings → Actions → Runners` Status `Idle` prüfen.
3. Der bereits wartende Job sollte automatisch übernommen werden.
4. Falls nötig, nur den betroffenen Workflow-Run erneut starten.

## Mehrere Repositories

Ein Repository-Level Self-Hosted Runner gehört genau zu diesem Repository. Für weitere Consumer-Repositories wie Portfolio Manager, Governance oder UserLifeCycle wird jeweils eine eigene Runner-Registrierung benötigt, sofern kein gemeinsamer Organization-Level Runner verfügbar ist.

Auf derselben Maschine können mehrere Runner-Instanzen betrieben werden. Dafür getrennte Installationsverzeichnisse und eindeutige Runner-Namen verwenden, z. B.:

```text
~/actions-runners/project-engineering
~/actions-runners/cashflow-portfolio
~/actions-runners/governance
~/actions-runners/user-lifecycle
```

Alle können das gemeinsame Label `local-ci` tragen, da sie jeweils repository-scoped registriert sind.

## Sicherheitsgrenze

Self-Hosted Runner führen Workflow-Code direkt auf dem eigenen Rechner aus. Deshalb:

- keine unkontrollierten öffentlichen Fork-PRs auf diesem Runner ausführen;
- Workflow-Änderungen reviewen wie ausführbaren Code;
- Runner nicht mit persönlichen Cloud-/Admin-Credentials ausstatten;
- Secrets nur gezielt über GitHub Actions bereitstellen und im hermetischen Required Contract möglichst vermeiden;
- persönliche Consumer-Workspaces und lokale Settings nicht als impliziten CI-Kontext verwenden;
- bei späterem Multi-User-/Organization-Betrieb Runner-Groups und Zugriffsbeschränkungen verwenden.
