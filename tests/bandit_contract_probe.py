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

from release import static_checks

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


def run_case(directory: Path, source: str, *, threshold: bool, pipeline: bool = False) -> dict:
    directory.mkdir(parents=True)
    (directory / "source").mkdir()
    (directory / "source/control.py").write_text(source, encoding="utf-8")
    command = [sys.executable, "-I", "-c", CONTROL_PLUGIN,
               "-r", "source", "-t", "B950", "-f", "json", "-o", "report.json"]
    if threshold:
        command += ["-lll", "-iii"]
    started = datetime.now(timezone.utc).isoformat()
    before = time.perf_counter_ns()
    pipeline_result = None
    if pipeline and not threshold:
        evidence = directory / "evidence"
        producer = static_checks.Check("bandit-full", tuple(command), accepted_codes=(0, 1),
            report=directory / "report.json", report_kind="bandit", source_paths=("source",))
        derived = static_checks.Check("bandit-blocking", (), report=evidence / "bandit-blocking.json",
            report_kind="bandit-decision", derived_from="bandit-full")
        later = static_checks.Check("continuation", (sys.executable, "-I", "-c", "print('continued')"))
        pipeline_result = static_checks.run_checks([producer, derived, later], directory, evidence)
        returncode = pipeline_result["checks"][0]["returncode"]
        log = (evidence / "bandit-full.log").read_bytes()
    else:
        result = subprocess.run(command, cwd=directory, stdin=subprocess.DEVNULL,
                                capture_output=True, timeout=30)
        returncode = result.returncode
        log = result.stdout + result.stderr
    duration = time.perf_counter_ns() - before
    finished = datetime.now(timezone.utc).isoformat()
    (directory / "scanner.log").write_bytes(log)
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    observation = {"returncode": returncode, "elapsed_ns": duration,
                   "started_at": started, "finished_at": finished,
                   "errors": report["errors"], "results": len(report["results"]),
                   "threshold": threshold}
    if pipeline_result is not None:
        observation["pipeline"] = {"passed": pipeline_result["passed"],
            "derived_passed": pipeline_result["checks"][1]["passed"],
            "derived_elapsed_ns": pipeline_result["checks"][1]["elapsed_ns"],
            "continuation_passed": pipeline_result["checks"][2]["passed"],
            "run_id": pipeline_result["run_id"]}
    (directory / "observation.json").write_text(json.dumps(observation, indent=2) + "\n")
    return observation


def probe(output: Path, *, pipeline: bool = False) -> dict:
    if version("bandit") != PINNED_BANDIT:
        raise ValueError("contract controls require the pinned Bandit version")
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for severity, confidence in itertools.product(RANKS, repeat=2):
        label = severity + "-" + confidence
        source = f'owned_issue("{severity}", "{confidence}")\n'
        full = run_case(output / label / "full", source, threshold=False, pipeline=pipeline)
        blocking = run_case(output / label / "threshold", source, threshold=True)
        expected = int((severity, confidence) == ("HIGH", "HIGH"))
        assert full["returncode"] == 1 and full["results"] == 1 and not full["errors"]
        assert blocking["returncode"] == expected and blocking["results"] == expected
        if pipeline:
            assert full["pipeline"]["passed"] is (not expected)
            assert full["pipeline"]["derived_passed"] is (not expected)
            assert full["pipeline"]["continuation_passed"]
        rows.append({"severity": severity, "confidence": confidence, "full": full, "blocking": blocking})
    failures = {}
    for name, source in (("clean", "value = 1\n"), ("syntax-error", "def broken(:\n"),
                         ("plugin-error", "owned_crash()\n")):
        failures[name] = {"full": run_case(output / name / "full", source, threshold=False, pipeline=pipeline),
                          "blocking": run_case(output / name / "threshold", source, threshold=True)}
        if pipeline:
            assert failures[name]["full"]["pipeline"]["passed"] is (name == "clean")
            assert failures[name]["full"]["pipeline"]["continuation_passed"]
    assert failures["clean"]["full"]["returncode"] == 0
    assert failures["syntax-error"]["full"]["errors"]
    assert not failures["plugin-error"]["full"]["errors"]
    assert "Bandit internal error running:" in (output / "plugin-error/full/scanner.log").read_text()
    result = {"schema_version": "agent-wiki-bandit-contract/v1", "bandit_version": PINNED_BANDIT,
              "rankings": list(RANKS), "cases": rows, "failure_controls": failures,
              "threshold": {"severity": "HIGH", "confidence": "HIGH", "operator": "and"},
              "pipeline_exercised": pipeline, "verification_only_legacy_scans": True}
    (output / "contract.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def compare_project(root: Path, evidence: Path, output: Path) -> dict:
    """One local timing sample; the legacy scan is verification-only."""
    checks = json.loads((evidence / "checks.json").read_text())
    assert checks["complete"] and checks["passed"] and len(checks["checks"]) == 7
    execution = json.loads((evidence / "bandit-full-execution.json").read_text())
    producer = next(check for check in static_checks.default_checks(root, evidence) if check.name == "bandit-full")
    scope = static_checks.source_manifest(root, producer.source_paths)
    decision = static_checks.evaluate_bandit((evidence / "bandit-full.json").read_bytes(),
        (evidence / "bandit-full.log").read_bytes(), execution, run_id=checks["run_id"],
        command=producer.command, source=scope)
    retained = json.loads((evidence / "bandit-blocking.json").read_text())
    assert decision == retained
    command = [sys.executable, "-I", "-m", "bandit", "-r", "src/llm_wiki_cli", "-lll", "-iii"]
    started = time.perf_counter_ns()
    result = subprocess.run(command, cwd=root, stdin=subprocess.DEVNULL, capture_output=True, timeout=600)
    legacy_ns = time.perf_counter_ns() - started
    (output / "legacy-project.log").write_bytes(result.stdout + result.stderr)
    assert static_checks.source_manifest(root, producer.source_paths) == scope
    assert result.returncode == (0 if decision["decision"]["passed"] else 1)
    derived = next(row for row in checks["checks"] if row["name"] == "bandit-blocking")
    summary = {"equal": True, "source_sha256": scope["sha256"], "run_id": checks["run_id"],
        "bandit_version": PINNED_BANDIT, "findings": decision["decision"]["findings"],
        "blocking_findings": decision["decision"]["blocking_findings"],
        "full_scan_ns": execution["elapsed_ns"], "derived_check_ns": derived["elapsed_ns"],
        "legacy_blocking_scan_ns": legacy_ns, "removed_work_estimate_ns": legacy_ns - derived["elapsed_ns"],
        "evidence_bytes": {p.name: p.stat().st_size for p in evidence.glob("bandit-*") if p.is_file()},
        "sample_count": 1, "timing_scope": "local sequential warm/uncontrolled sample; not hosted or workflow wall-clock savings"}
    (output / "project-parity.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pipeline", action="store_true")
    parser.add_argument("--project-evidence", type=Path)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = probe(args.output.absolute(), pipeline=args.pipeline)
    if args.project_evidence is not None:
        compare_project(args.project_root.absolute(), args.project_evidence.absolute(), args.output.absolute())
    print(json.dumps({"bandit": result["bandit_version"], "rank_pairs": len(result["cases"]), "passed": True}))


if __name__ == "__main__":
    main()
