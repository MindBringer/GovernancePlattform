# Projektgedächtnis – GovernancePlattform

<!-- project-memory-schema: 2 -->
<!-- current-version: 6.2.5 -->
<!-- next-step: governance-framework-1.3.12-conformance -->
<!-- updated-at: 2026-08-30 -->
<!-- release-status: candidate -->
<!-- release-source-branch: chore/framework-1.3.12-conformance -->
<!-- release-target-branch: main -->
<!-- release-pr: n/a -->

## Aktueller Stand

GovernancePlattform steht fachlich auf Stage 4.1 aus PR #5 (`afe6528d…`). Parallel wird ausschließlich auf `chore/framework-1.3.12-conformance` die Existing-Repo-Adoption des Project Engineering Framework 1.3.12 geprüft. Der alte monolithische Companion-Server wird durch den Framework-Server ersetzt; PAC-/ALM-Logik bleibt project-owned.

## Aktuelle Iteration

Ziel ist der vierte Consumer-Nachweis für Framework 1.3.12: Existing-Repo-Adoption, Erhalt der Governance-/Power-Platform-Quellen und repository-only Verifikation ohne DEV-/Tenant-Write.

## Umgesetzt

- Isolierter Conformance-Branch auf Baseline `afe6528d…`.
- Framework 1.3.12 kontrolliert adoptiert.
- Governance-PAC-/ALM-Flächen project-owned klassifiziert.
- Power-Platform Validate/Build/Canvas-Fix-Pfade konfiguriert.
- Verification-Evidence-Klassen für Repository, Read-only, DEV-Write und Deployment getrennt.

## Nicht umgesetzt / Nicht-Ziele

Noch offen: Governance-Actions in `project_actions.py`, repository-only Non-Mutating-Lauf, Draft-Conformance-PR und Remote-CI.

Nicht-Ziele: kein `pac solution import`, kein Publish All, kein Deploy to DEV, kein DEV→Git Studio Sync und keine Änderung der Stage-4.1-Fachfunktion.

## Qualität und Verifikation

Project Version 6.2.5 · Canvas 1.0.0-alpha.4.1.0 · Framework 1.3.12. Repository/CI-Evidence ist pending; DEV-Write und Deployment bleiben deferred. CI ersetzt ausdrücklich keinen DEV- oder Tenant-Smoke.

## Altlasten und bekannte Probleme

Der alte monolithische Companion-Server ist Architektur-Altbestand und wird durch Framework-Core plus project-owned Adapter ersetzt. Für die Framework-Adoption sind derzeit keine fachlichen Governance-Blocker bekannt.

## Nächster geplanter Schritt

**governance-framework-1.3.12-conformance** – Framework-, Canvas-, Provider-Registry- und Provisioning-Gates repository-only und non-mutating verifizieren und danach Remote-CI über einen isolierten Draft-PR belegen.

## Wiederaufnahme nach Chat-Abbruch

`cd /Users/janjansen/git/GovernancePlattform` → Conformance-Branch prüfen → Framework Lock → Repository Audit → Project Memory → Validate → Frameworktests. Keine PAC-Import-/Publish-/Deploy-Aktion ausführen.

## Iterationsübergabe

Consumer: GovernancePlattform · Archetyp: Existing Repo + Power Platform ALM · Baseline: `afe6528d` · Framework: 1.3.12 · Write Boundary: repository-only · DEV/Tenant Writes: prohibited · Merge/Release: not performed.
