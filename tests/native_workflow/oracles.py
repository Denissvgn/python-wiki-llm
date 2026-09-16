"""Held-out scoring and owned-fixture oracles, outside the provider runtime."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from tests.provider_conformance import python_ast


def source_facts(path: Path) -> dict:
    """Independent AST observations; never import the target module."""
    text = path.read_text(encoding="utf-8")
    return {"source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            **python_ast.observe(text), "calls": python_ast.calls(text)}


def score_claims(expected: dict, claims: list[dict]) -> dict:
    """Score unique factual claims; repetitions cannot inflate coverage."""
    seen = set()
    present, wrong, stale, unknown, conflicts = set(), set(), set(), set(), set()
    for claim in claims:
        identity = json.dumps(claim, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if identity in seen:
            continue
        seen.add(identity)
        fact_id = claim.get("id")
        truth = expected.get(fact_id)
        if truth is None:
            wrong.add(identity)
            continue
        if claim.get("status") in {"unknown", "unsupported", "omitted", "ambiguous"}:
            if claim.get("status") == truth.get("state", "supported"):
                unknown.add(fact_id)
            elif claim.get("status") in {"omitted", "ambiguous", "unknown"}:
                # Qualified absence is honest but does not satisfy an answerable fact.
                unknown.add(fact_id)
            else:
                wrong.add(identity)
            continue
        if claim.get("freshness") == "stale":
            stale.add(identity)
            conflicts.add(fact_id)
        elif (truth.get("state", "supported") == "supported"
              and claim.get("value") == truth.get("value")
              and claim.get("citation") == truth.get("citation")):
            present.add(fact_id)
        else:
            wrong.add(identity)
            conflicts.add(fact_id)
    present -= conflicts
    return {"required": len(expected), "present": sorted(present),
            "missing": sorted(set(expected) - present), "wrong_claims": len(wrong),
            "stale_claims": len(stale), "qualified_unknowns": sorted(unknown),
            "coverage": len(present) / len(expected) if expected else None,
            "semantic_adequacy": "not-evaluated"}


def verify_corpus(root: Path) -> dict:
    manifest = json.loads((root / "corpus.json").read_text())
    tasks = manifest["tasks"]
    if [task["id"] for task in tasks] != [f"T{i:02}" for i in range(1, 13)]:
        raise ValueError("All twelve stable task families are required")
    for task in tasks:
        if not task["required_facts"] or not task["disconfirming_outcomes"]:
            raise ValueError("Task lacks falsifiable requirements")
        for relative, expected in task["input_sha256"].items():
            path = root / "fixtures" / task["id"] / relative
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Frozen input changed: {task['id']}/{relative}")
        project = root / "fixtures" / task["id"] / "project"
        if any(p.name in {"oracles.py", "expectations.json", "prior-runs", "patches", "sessions"}
               for p in project.rglob("*")):
            raise ValueError("Held-out material leaked into project")
    return manifest


def observe_owned_retry_patch(project: Path) -> dict:
    """Execute only the deliberately owned retry fixture during oracle checks.

    This is a local fixture control, not admission for arbitrary target projects
    or evidence of a real model run. General campaign execution belongs to the
    separately admitted external host.
    """
    try:
        compile((project / "retry.py").read_text(), "retry.py", "exec")
        ast.parse((project / "client.py").read_text())
    except (SyntaxError, ValueError):
        return {"compiled": False, "process_exit": None, "oracle_passed": False}
    script = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
from client import fetch
checks = []
for success_at in (1, 2, 3, None):
    calls = []
    def operation():
        calls.append(1)
        if len(calls) == success_at:
            return "ok"
        raise ValueError("transient")
    try:
        result = fetch(operation)
        checks.append(success_at is not None and result == "ok" and len(calls) == success_at)
    except ValueError:
        checks.append(success_at is None and len(calls) == 3)
print(json.dumps({"checks": checks, "oracle_passed": all(checks)}))
'''
    environment = {k: v for k, v in os.environ.items()
                   if k in {"PATH", "SYSTEMROOT", "WINDIR", "TMPDIR", "TEMP", "TMP"}}
    try:
        result = subprocess.run([sys.executable, "-I", "-c", script, str(project.resolve())],
                                capture_output=True, text=True, timeout=5, env=environment,
                                cwd=project)
    except subprocess.TimeoutExpired:
        return {"compiled": True, "process_exit": None, "oracle_passed": False,
                "status": "timed-out"}
    observed = json.loads(result.stdout) if result.returncode == 0 else {"oracle_passed": False}
    return {"compiled": True, "process_exit": result.returncode, **observed}


def summarize_attempts(attempts: list[dict]) -> dict:
    categories = {key: 0 for key in ("passed", "failed", "cancelled", "timed-out",
                                    "unsupported", "unavailable", "integration-failed")}
    ids = set()
    for attempt in attempts:
        if attempt["id"] in ids or attempt["status"] not in categories:
            raise ValueError("Duplicate attempt or unknown disposition")
        ids.add(attempt["id"])
        categories[attempt["status"]] += 1
    return {"attempts": len(attempts), "categories": categories,
            "model_execution_established": False}
