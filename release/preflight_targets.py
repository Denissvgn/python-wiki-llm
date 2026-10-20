"""Repository-owned adapter from maintained proof declarations to target data.

This is deliberately not a universal CI parser. Expressions, custom runners and
unobservable architecture/patch selections remain unknown, never host defaults.
"""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import re

WORKFLOW = ".github/workflows/release-qualification.yml"
RUNNER_PLATFORMS = {
    "ubuntu-24.04": "linux",
    "windows-2025": "win32",
    "macos-15": "darwin",
}


def declarations(root: Path, read_bytes):
    from llm_wiki_cli.services.yaml_syntax import load_yaml_documents

    inputs = {}

    def read(name):
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            raise ValueError("unsafe proof declaration path")
        raw = read_bytes(name)
        if len(raw) > 1024 * 1024:
            raise ValueError("proof declaration exceeds byte limit")
        inputs[name] = hashlib.sha256(raw).hexdigest()
        documents, issues = load_yaml_documents(raw.decode("utf-8"))
        if issues or len(documents) != 1:
            raise ValueError("ambiguous, unsupported or over-budget proof declaration")
        return documents[0]

    workflow = read(WORKFLOW)
    if not isinstance(workflow, dict) or not isinstance(workflow.get("jobs"), dict):
        raise ValueError("proof workflow jobs are unavailable")
    targets = []
    for job_id, job in workflow.get("jobs", {}).items():
        if not isinstance(job, dict) or not isinstance(job.get("steps", []), list):
            raise ValueError("proof owner steps are unavailable")
        for position, step in enumerate(job.get("steps", [])):
            if not isinstance(step, dict) or not isinstance(step.get("with", {}), dict):
                raise ValueError("proof owner inputs are unavailable")
            options = step.get("with", {})
            if not options.get("maintenance-candidate-sha"):
                continue
            uses = step.get("uses", "")
            prefix = options.get("src-dir")
            runner = job.get("runs-on")
            target = {
                "owner": WORKFLOW + "#" + job_id + "/step-" + str(position),
                "platform": RUNNER_PLATFORMS.get(runner)
                if isinstance(runner, str) and not job.get("container")
                else None,
                "machine": None,
                "python": None,
                "implementation": None,
                "capture_route": "Review the maintained target-host owning convergence route, authenticate its complete snapshot including removals, then obtain fresh native proof.",
            }
            # The declared source root identifies the frozen checkout prefix.
            if (
                isinstance(prefix, str)
                and isinstance(uses, str)
                and uses.startswith("./" + prefix + "/")
                and "${{" not in prefix
            ):
                action = uses[len("./" + prefix + "/") :].rstrip("/") + "/action.yml"
                composite = read(action)
                if not isinstance(composite, dict) or not isinstance(
                    composite.get("runs"), dict
                ):
                    raise ValueError("composite proof runtime is unavailable")
                setups = [
                    s
                    for s in composite.get("runs", {}).get("steps", [])
                    if isinstance(s.get("uses"), str)
                    and s["uses"].startswith("actions/setup-python@")
                ]
                if len(setups) == 1 and not setups[0].get("if"):
                    declared = setups[0].get("with", {})
                    version = declared.get("python-version")
                    if isinstance(version, str) and re.fullmatch(
                        r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", version
                    ):
                        target.update(python=version, implementation="CPython")
                    architecture = declared.get("architecture")
                    target["machine"] = {
                        "x64": "AMD64" if target["platform"] == "win32" else "x86_64",
                        "arm64": "arm64",
                    }.get(architecture)
            targets.append(target)
    return targets, inputs


def inspect(root: Path, wiki_dir: str, read_bytes):
    try:
        from llm_wiki_cli.services.analysis_targets import inspect_targets

        targets, inputs = declarations(root, read_bytes)
        report = inspect_targets(root / wiki_dir, targets)
        report["declaration_inputs"] = inputs
        return report
    except (
        ImportError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        return {
            "status": "unknown",
            "reason": str(exc)[:500],
            "target_execution_verified": False,
            "source_inventory_performed": False,
            "declaration_inputs": {},
        }
