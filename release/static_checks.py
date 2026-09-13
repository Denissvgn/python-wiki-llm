"""Run all independent static qualification checks and retain their evidence."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys


@dataclass(frozen=True)
class Check:
    name: str
    command: tuple[str, ...]
    accepted_codes: tuple[int, ...] = (0,)
    report: Path | None = None
    report_kind: str | None = None


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _report_error(check: Check) -> str | None:
    if check.report is None:
        return None
    try:
        data = json.loads(check.report.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"Required report is unreadable: {exc}"
    if check.report_kind == "bandit":
        metrics = data.get("metrics") if isinstance(data, dict) else None
        totals = metrics.get("_totals") if isinstance(metrics, dict) else None
        lines = totals.get("loc") if isinstance(totals, dict) else None
        valid = (
            isinstance(data, dict)
            and isinstance(data.get("results"), list)
            and data.get("errors") == []
            and type(lines) is int
            and lines > 0
        )
    elif check.report_kind == "pip-audit":
        valid = (
            isinstance(data, dict)
            and isinstance(data.get("dependencies"), list)
            and bool(data["dependencies"])
        )
    else:
        valid = False
    return None if valid else "Required report is incomplete or records analysis errors"


def default_checks(root: Path, evidence: Path) -> list[Check]:
    def module(name: str, *args: str) -> tuple[str, ...]:
        return (sys.executable, "-m", name, *args)

    bandit_report = evidence / "bandit-full.json"
    audit_report = evidence / "pip-audit.json"
    return [
        Check("pip-check", module("pip", "check")),
        Check("pyright", module("pyright", "--pythonpath", sys.executable)),
        Check(
            "ruff",
            module(
                "ruff",
                "check",
                "src",
                "tests",
                "integrations/github-action/render_summary.py",
            ),
        ),
        Check(
            "bandit-full",
            module(
                "bandit",
                "-r",
                "src/llm_wiki_cli",
                "-f",
                "json",
                "-o",
                str(bandit_report),
            ),
            accepted_codes=(0, 1),
            report=bandit_report,
            report_kind="bandit",
        ),
        Check(
            "bandit-blocking",
            module("bandit", "-r", "src/llm_wiki_cli", "-lll", "-iii"),
        ),
        Check(
            "pip-audit",
            module(
                "pip_audit",
                "--local",
                "--format",
                "json",
                "--output",
                str(audit_report),
            ),
            report=audit_report,
            report_kind="pip-audit",
        ),
        Check(
            "actionlint",
            (
                "actionlint",
                *(
                    str(path)
                    for path in sorted((root / ".github/workflows").glob("*.yml"))
                ),
            ),
        ),
    ]


def run_checks(checks: list[Check], root: Path, evidence: Path) -> dict:
    evidence.mkdir(parents=True, exist_ok=True)
    results = []
    for check in checks:
        error = None
        returncode = None
        log = evidence / f"{check.name}.log"
        try:
            if check.report is not None:
                check.report.unlink(missing_ok=True)
            with log.open("wb") as stream:
                result = subprocess.run(
                    check.command,
                    cwd=root,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    check=False,
                    timeout=600,
                )
            returncode = result.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            error = str(exc)
        error = error or _report_error(check)
        passed = returncode in check.accepted_codes and error is None
        results.append(
            {
                "name": check.name,
                "command": list(check.command),
                "returncode": returncode,
                "error": error,
                "passed": passed,
                "log": log.name,
            }
        )
        print(
            f"{check.name}: {'PASS' if passed else 'FAIL'} (exit {returncode})",
            flush=True,
        )
        if not passed:
            print(
                log.read_text(encoding="utf-8", errors="replace")
                if log.exists()
                else error,
                flush=True,
            )
    payload = {
        "passed": bool(results) and all(item["passed"] for item in results),
        "checks": results,
    }
    _write_json(evidence / "checks.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence.absolute()
    evidence.mkdir(parents=True, exist_ok=True)
    environment = {"executable": sys.executable, "prefix": sys.prefix, "versions": {}}
    try:
        importlib.import_module("tokenizers")
        environment["versions"] = {
            name: version(name)
            for name in (
                "agent-wiki-cli",
                "tokenizers",
                "mcp",
                "pyright",
                "ruff",
                "bandit",
                "pip-audit",
            )
        }
    except (ImportError, ValueError) as exc:
        environment["error"] = str(exc)
        _write_json(evidence / "environment.json", environment)
        _write_json(
            evidence / "checks.json", {"passed": False, "checks": [], "error": str(exc)}
        )
        print(f"Qualification environment preflight failed: {exc}", file=sys.stderr)
        return 1
    _write_json(evidence / "environment.json", environment)
    return (
        0
        if run_checks(default_checks(Path.cwd(), evidence), Path.cwd(), evidence)[
            "passed"
        ]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
