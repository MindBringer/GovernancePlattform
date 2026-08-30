# Architecture Decisions – GovernancePlattform

## ADR-0001 · Project Engineering Framework 1.3.12

GovernancePlattform übernimmt den generischen Framework-Core für Engineering, Project Memory, Companion und Release-Orchestrierung. Power-Platform-, Provisioning- und Governance-ALM-Quellen bleiben project-owned.

## ADR-0002 · Companion Adapter statt monolithischem Server

Der bisherige Governance-spezifische `tools/companion/server.py` wird durch den Framework-Server ersetzt. Die fachliche PAC-/ALM-Implementierung bleibt in `tools/companion/pac_workflow.py` und wird über `tools/companion/project_actions.py` exponiert. Produktive DEV-Aktionen benötigen explizite Bestätigung und sind kein Bestandteil der Framework-Conformance.
