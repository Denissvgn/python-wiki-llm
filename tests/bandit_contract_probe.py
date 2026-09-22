"""Opt-in pinned Bandit CLI controls; fixture source is scanned, never executed."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import itertools
import json
from pathlib import Path
import subprocess
import sys
import time

RANKS = ("UNDEFINED", "LOW", "MEDIUM", "HIGH")
PINNED_BANDIT = "1.9.4"

# Only the issue-producing plugin is controlled. Argument parsing, threshold
# filtering, metrics, report formatting, and exit status are the pinned CLI's.
CONTROL_PLUGIN = r'''
from types import SimpleNamespace
import sys
import bandit
from bandit.cli.main import main
from bandit.core import extension_loader, test_properties

@test_properties.checks("Call")
@test_properties.test_id("B950")
def owned_issue(context):
    if context.call_function_name == "owned_crash":
        raise RuntimeError("owned plugin failure")
    if context.call_function_name == "owned_issue":
        severity, confidence = context.call_args
        return bandit.Issue(severity=severity, confidence=confidence,
                            text="Owned severity/confidence control")

plugin = SimpleNamespace(name="owned_issue", plugin=owned_issue)
manager = extension_loader.MANAGER
manager.plugins.append(plugin)
manager.plugin_names.append(plugin.name)
manager.plugins_by_id["B950"] = plugin
manager.plugins_by_name[plugin.name] = plugin
sys.argv = ["bandit", *sys.argv[1:]]
main()
'''


def run_case(directory: Path, source: str, *, threshold: bool) -> dict:
    directory.mkdir(parents=True)
    (directory / "source").mkdir()
    (directory / "source/control.py").write_text(source, encoding="utf-8")
    command = [sys.executable, "-I", "-c", CONTROL_PLUGIN,
               "-r", "source", "-t", "B950", "-f", "json", "-o", "report.json"]
    if threshold:
        command += ["-lll", "-iii"]
    started = datetime.now(timezone.utc).isoformat()
    before = time.perf_counter_ns()
    result = subprocess.run(command, cwd=directory, stdin=subprocess.DEVNULL,
                            capture_output=True, timeout=30)
    duration = time.perf_counter_ns() - before
    finished = datetime.now(timezone.utc).isoformat()
    (directory / "scanner.log").write_bytes(result.stdout + result.stderr)
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    observation = {"returncode": result.returncode, "elapsed_ns": duration,
                   "started_at": started, "finished_at": finished,
                   "errors": report["errors"], "results": len(report["results"]),
                   "threshold": threshold}
    (directory / "observation.json").write_text(json.dumps(observation, indent=2) + "\n")
    return observation


def probe(output: Path) -> dict:
    if version("bandit") != PINNED_BANDIT:
        raise ValueError("contract controls require the pinned Bandit version")
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for severity, confidence in itertools.product(RANKS, repeat=2):
        label = severity + "-" + confidence
        source = f'owned_issue("{severity}", "{confidence}")\n'
        full = run_case(output / label / "full", source, threshold=False)
        blocking = run_case(output / label / "threshold", source, threshold=True)
        expected = int((severity, confidence) == ("HIGH", "HIGH"))
        assert full["returncode"] == 1 and full["results"] == 1 and not full["errors"]
        assert blocking["returncode"] == expected and blocking["results"] == expected
        rows.append({"severity": severity, "confidence": confidence, "full": full, "blocking": blocking})
    failures = {}
    for name, source in (("clean", "value = 1\n"), ("syntax-error", "def broken(:\n"),
                         ("plugin-error", "owned_crash()\n")):
        failures[name] = {"full": run_case(output / name / "full", source, threshold=False),
                          "blocking": run_case(output / name / "threshold", source, threshold=True)}
    assert failures["clean"]["full"]["returncode"] == 0
    assert failures["syntax-error"]["full"]["errors"]
    assert not failures["plugin-error"]["full"]["errors"]
    assert "Bandit internal error running:" in (output / "plugin-error/full/scanner.log").read_text()
    result = {"schema_version": "agent-wiki-bandit-contract/v1", "bandit_version": PINNED_BANDIT,
              "rankings": list(RANKS), "cases": rows, "failure_controls": failures,
              "threshold": {"severity": "HIGH", "confidence": "HIGH", "operator": "and"}}
    (output / "contract.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.output.absolute())
    print(json.dumps({"bandit": result["bandit_version"], "rank_pairs": len(result["cases"]), "passed": True}))


if __name__ == "__main__":
    main()
