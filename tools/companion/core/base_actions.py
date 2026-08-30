from __future__ import annotations

import sys
from pathlib import Path

from .actions import ActionRegistry, ActionSpec
from .config import ProjectConfig
from .git_status import guard_clean_worktree


def register_base_actions(registry: ActionRegistry, root: Path, config: ProjectConfig) -> None:
    if config.enabled("git"):
        registry.register(ActionSpec(
            id="status", label="Git-Status", category="Repository",
            description="Zeigt Branch und lokale Änderungen.",
            commands=[["git", "status", "--short", "--branch"]], timeout=60,
        ))
        registry.register(ActionSpec(
            id="fetch", label="Fetch", category="Repository",
            description="Aktualisiert Remote-Referenzen ohne Merge.",
            commands=[["git", "fetch", "--prune", "origin"]], timeout=300,
        ))
        registry.register(ActionSpec(
            id="pull", label="Pull --ff-only", category="Repository",
            description="Fast-forward-only; nur bei sauberem Arbeitsverzeichnis.",
            commands=[["git", "pull", "--ff-only"]], guard=guard_clean_worktree, timeout=300,
        ))
        registry.register(ActionSpec(
            id="repository-policy", label="Repository Policy prüfen", category="Repository",
            description="Prüft den Base Branch auf GitHub-Protection/Ruleset und erzwingt die Policy nur, wenn dies in der Projekt-Config aktiviert ist.",
            commands=[[sys.executable, "tools/framework/repository_policy.py"]], timeout=120,
            non_mutating=True,
        ))

    if config.project.get("key") == "project-template":
        registry.register(ActionSpec(
            id="framework-lock-refresh", label="Framework Lock aktualisieren", category="Qualität",
            description="Erzeugt den Hash-Lock für framework-managed Dateien neu. Nur im zentralen Template zulässig.",
            commands=[[sys.executable, "tools/framework/sync.py", "lock"]], timeout=300,
        ))
    registry.register(ActionSpec(
        id="framework-lock-check", label="Framework Lock prüfen", category="Qualität",
        description="Prüft, ob Manifest/Framework-Version, Config und alle managed Datei-Hashes zum Lock passen.",
        commands=[[sys.executable, "tools/framework/sync.py", "verify-lock"]], timeout=300,
        non_mutating=True,
    ))
    registry.register(ActionSpec(
        id="framework-integrity", label="Framework Integrity", category="Qualität",
        description="Nicht mutierender Ownership-/Lock-Check. Versionsdelta ist erlaubt; Drift framework-managed Dateien blockiert.",
        commands=[[sys.executable, "tools/framework/sync.py", "integrity"]], timeout=300,
        non_mutating=True,
    ))
    registry.register(ActionSpec(
        id="syntax-check", label="Python Syntax prüfen", category="Qualität",
        description="Kompiliert Framework-/Companion-Pythonquellen ohne Seiteneffekte auf getrackte Dateien.",
        commands=[[sys.executable, "-m", "compileall", "-q", "tools", "tests"]], timeout=300,
        non_mutating=True,
    ))
    registry.register(ActionSpec(
        id="project-memory-contract", label="Projektgedächtnis prüfen", category="Qualität",
        description="Prüft Version, Iterations-Handoff, Dokumentationsstatus, Altlastenreview und genau einen nächsten Schritt.",
        commands=[[sys.executable, "tools/framework/project_memory.py"]], timeout=300,
        non_mutating=True,
    ))
    registry.register(ActionSpec(
        id="verification-evidence", label="Verification Evidence prüfen", category="Qualität",
        description="Prüft die getrennten Evidenzklassen und blockiert den Release nur gemäß expliziter releasePolicy; CI-Erfolg wird nicht als Runtime-/Deployment-Acceptance umgedeutet.",
        commands=[[sys.executable, "tools/framework/verification_evidence.py", "--release"]], timeout=300,
        non_mutating=True,
    ))
    registry.register(ActionSpec(
        id="technical-debt-review", label="Altlasten-Sweep & Review", category="Qualität",
        description="Abwärtskompatibler, nicht mutierender Review-Gate: sucht Blocker, TODO/FIXME, Legacy-/versionierte Implementierungen und Dubletten, ohne Project State zu verändern.",
        commands=[[sys.executable, "tools/framework/technical_debt.py"]], timeout=600,
        non_mutating=True,
    ))
    registry.register(ActionSpec(
        id="technical-debt-record", label="Altlasten-Review dokumentieren", category="Qualität",
        description="Bewusst mutierende Aktion: führt den Altlasten-Sweep aus und schreibt das Review-Ergebnis in den Project State. Kein Required-/Release-Gate.",
        commands=[[sys.executable, "tools/framework/technical_debt.py", "--review"]], timeout=600,
    ))
    registry.register(ActionSpec(
        id="technical-debt-check", label="Altlasten-Sweep prüfen", category="Qualität",
        description="Nicht mutierender CI-/Build-Check auf technische Altlasten und harte Blocker.",
        commands=[[sys.executable, "tools/framework/technical_debt.py"]], timeout=600,
        non_mutating=True,
    ))
    registry.register(ActionSpec(
        id="framework-validate", label="Framework validieren", category="Qualität",
        description="Prüft Config, Struktur, Manifest, Projektgedächtnis, Modulvoraussetzungen und Framework-Integrität.",
        commands=[
            [sys.executable, "tools/framework/validate.py"],
            [sys.executable, "tools/framework/sync.py", "integrity"],
        ], timeout=300,
        non_mutating=True,
    ))

    if config.enabled("audit"):
        registry.register(ActionSpec(
            id="repo-audit", label="Repository-Audit", category="Qualität",
            description="Prüft Repository-Hygiene und versehentlich getrackte lokale Dateien.",
            commands=[[sys.executable, "tools/framework/audit_repo.py"]], timeout=300,
            non_mutating=True,
        ))

    if config.enabled("build") or config.enabled("audit"):
        registry.register(ActionSpec(
            id="tests", label="Framework-Tests", category="Qualität",
            description="Führt die Framework-Unit-Tests aus.",
            commands=[[sys.executable, "-m", "unittest", "discover", "-s", "tests/framework", "-p", "test_*.py"]], timeout=900,
            non_mutating=True,
        ))

    if config.project.get("key") == "project-template":
        registry.register(ActionSpec(
            id="bootstrap-smoke", label="Template Bootstrap Smoke", category="Build & Test",
            description="Erzeugt frische Plain-, Power-Platform- und Provisioning-Projekte und validiert Initialisierung, Memory und Companion-Runtime.",
            commands=[[sys.executable, "tools/framework/bootstrap_smoke.py"]], timeout=1200,
            non_mutating=True,
        ))

    registry.register(ActionSpec(
        id="engineering-contract", label="Engineering Contract", category="Build & Test",
        description="Verbindlicher, nicht mutierender Handoff-Check: Integrity, Audit, Syntax, Altlastencheck, Projektgedächtnis, Framework-Validierung und Tests.",
        commands=[
            [sys.executable, "tools/framework/sync.py", "integrity"],
            [sys.executable, "tools/framework/audit_repo.py"],
            [sys.executable, "-m", "compileall", "-q", "tools", "tests"],
            [sys.executable, "tools/framework/technical_debt.py"],
            [sys.executable, "tools/framework/project_memory.py"],
            [sys.executable, "tools/framework/validate.py"],
            [sys.executable, "tools/framework/sync.py", "integrity"],
            [sys.executable, "-m", "unittest", "discover", "-s", "tests/framework", "-p", "test_*.py"],
        ], timeout=1200,
        non_mutating=True,
    ))

    if config.enabled("build"):
        registry.register(ActionSpec(
            id="build", label="Engineering Build", category="Build & Test",
            description="Nicht mutierender reproduzierbarer Build: Validate, Audit, Syntax, Altlastencheck, Memory Contract, Integrity und Framework-Tests.",
            commands=[
                [sys.executable, "tools/framework/validate.py"],
                [sys.executable, "tools/framework/audit_repo.py"],
                [sys.executable, "-m", "compileall", "-q", "tools", "tests"],
                [sys.executable, "tools/framework/technical_debt.py"],
                [sys.executable, "tools/framework/project_memory.py"],
                [sys.executable, "tools/framework/sync.py", "integrity"],
                [sys.executable, "-m", "unittest", "discover", "-s", "tests/framework", "-p", "test_*.py"],
            ], timeout=1200,
            non_mutating=True,
        ))

    release = config.data.get("release", {})
    if release.get("createTag", True) or release.get("createGitHubRelease", False):
        registry.register(ActionSpec(
            id="release-artifacts", label="Release-Artefakte reparieren", category="Release",
            description="Idempotente Reparatur/Erzeugung von immutable Git-Tag und optionalem GitHub Release auf dem Target-Branch.",
            commands=[[sys.executable, "tools/framework/release_artifacts.py"]], timeout=600,
            confirmation="PUBLISH RELEASE", danger=True,
        ))
