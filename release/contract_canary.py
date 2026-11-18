"""Check bounded release fixtures and real coverage output before full producers."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release import core_shard_runner as runner
from release import core_shards
from release import measurement_canary as canary
from release import pr_ci_pytest

SCHEMA = "agent-wiki-release-contract-canary/v1"
PUBLICATION_CASE = "tests/test_publication_portability_adoption.py::test_managed_native_wiki_custom_paths_stale_evidence_and_recovery[retired]"
FIXTURES = (
    PUBLICATION_CASE,
    "tests/test_preflight_runner.py::test_prepare_only_has_locked_setup_and_readiness_without_wiki_write",
    "tests/test_preflight_runner.py::test_full_driver_keeps_maintained_owners_and_strict_full_suite",
    "tests/test_preflight_runner.py::test_shared_driver_environment_skip_stays_blocked",
    "tests/test_preflight_runner.py::test_archive_block_does_not_hide_independent_wiki_health_checks",
    "tests/test_preflight_contracts.py::test_rebound_registry_cannot_remove_admission_dependency",
    "tests/test_helper_cache.py::test_legacy_receipt_cannot_read_an_artifact_outside_cache",
    "tests/test_helper_cache.py::test_npm_shebang_uses_pinned_node_when_selection_alias_changes",
    "tests/test_helper_cache.py::test_rust_profile_forces_the_compiler_it_validated",
    "tests/test_evidence_explanation_query.py::test_receipt_identity_uses_actual_bytes_and_does_not_prepare[typescript]",
    "tests/test_manual_release.py::test_interrupted_notes_materialization_resumes_without_accepting_changed_notes",
    "tests/test_wiki_candidate_checkout.py::test_source_and_separate_target_have_independent_verified_revisions",
    "tests/test_wiki_candidate_checkout.py::test_pinned_target_rejects_materialized_git_symlink",
    "tests/test_wiki_integrity_action.py::test_full_integrity_action_has_bounded_portable_inputs",
    "tests/test_wiki_integrity_action.py::test_full_integrity_action_is_pinned_caller_checkout_owned_and_read_only",
    "tests/test_wiki_integrity_action.py::test_full_integrity_action_isolates_python_modules_from_candidate_source",
    "tests/test_wiki_integrity_action.py::test_full_integrity_action_reserves_and_always_uploads_allowlisted_evidence",
)
COVERAGE = (
    "tests/test_core_shard_runner.py::test_pure_coverage_reader_preserves_raw_union_for_multiline_statement_hits",
    "tests/test_core_shard_runner.py::test_multiline_coverage_reader_rejects_rehashed_xml_hits",
    "tests/test_core_shard_runner.py::test_pure_promotion_reader_replays_raw_coverage_union_without_third_party_reader",
    "tests/test_core_shard_runner.py::test_unexecuted_source_files_cannot_disappear_from_coverage_denominator",
    "tests/test_core_shard_runner.py::test_coverage_statement_map_rejects_rehashed_omitted_uncovered_xml_line",
    "tests/test_core_shard_runner.py::test_coverage_report_probe_preserves_active_configured_outputs",
)


def profile_selectors(profile: str):
    if profile == "fixtures":
        if sys.platform != "win32":
            return (*FIXTURES, "tests/test_ci_toolchain_setup.py::test_routine_local_setup_uses_lock_and_writes_sourceable_environment")
        return FIXTURES
    return COVERAGE


def verify_candidate(args) -> dict:
    root = canary.safe(args.root)
    canary.require(not (root / ".git").exists() and not (root / ".git").is_symlink(),
                   "Contract canary requires the frozen Git-free candidate")
    identity = runner.q._validate_identity(runner.q.load_json(canary.safe(args.identity)))
    canary.require(identity["source"]["sha"] == args.source_sha, "Contract canary source differs")
    canary.require(canary.safe(Path(sys.prefix)).samefile(canary.safe(args.expected_prefix)),
                   "Contract canary interpreter prefix differs")
    runner.verify_source(root, canary.safe(args.archive), identity)
    expected = canary.provider_files(root)
    canary.verify_provider(expected)
    return dict(expected)


def validate_results(selectors, collection, started, cases) -> dict:
    nodes = core_shards.inventory(collection["collected"])
    canary.require(collection["deselected"] == [] and Counter(collection["selected"]) == Counter(nodes),
                   "Contract canary selection was reduced")
    canary.require(all(any(runner.q._selector_matches(s, n) for n in nodes) for s in selectors),
                   "Contract canary omitted a required selector")
    canary.require(all(any(runner.q._selector_matches(s, n) for s in selectors) for n in nodes),
                   "Contract canary collected an unexpected selector")
    if selectors == COVERAGE:
        required = {COVERAGE[0] + "[" + mode + "]" for mode in ("continuation-events", "native-tracer")}
        required.update(COVERAGE[1] + f"[{mode}-{line}-{hits}]"
                        for mode in ("continuation-events", "native-tracer") for line, hits in ((10, 0), (15, 1)))
        canary.require(required <= set(nodes), "Contract canary omitted a real tracer or tampered multiline output")
    canary.require(Counter(started) == Counter(nodes) and set(cases) == set(nodes),
                   "Contract canary collection, started nodes and JUnit differ")
    canary.require(all(not any(c.find(t) is not None for t in ("failure", "error", "skipped")) for c in cases.values()),
                   "Contract canary failed or skipped a required case")
    return {"collected": len(nodes), "passed": len(nodes), "skipped": 0}


def verify_profile(output: Path, profile: str, source_sha: str) -> dict:
    selectors = profile_selectors(profile)
    path = canary.safe(output / "started.jsonl")
    canary.require(path.stat().st_size <= 4 * 1024 * 1024, "Contract started inventory exceeds bound")
    started = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    counts = validate_results(selectors, runner.q.load_json(output / "collection.json"), started,
                              core_shards.junit(output / "junit.xml"))
    expected = {"schema_version": SCHEMA, "profile": profile, "source_sha": source_sha, "status": "passed", **counts}
    canary.require(runner.q.load_json(output / "result.json") == expected, "Contract profile result differs from evidence")
    return counts


def execute_tests(root: Path, selectors, out: Path, *, collect_only=False, installed_only=False) -> int:
    """Run once in a fresh worker, retaining collection, starts, status and raw JUnit."""
    import pytest

    os.environ["PR_CI_COLLECTION"] = str(out / "collection.json")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    class Started:
        @pytest.hookimpl
        def pytest_runtest_logstart(self, nodeid, location):
            with (out / "started.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(nodeid) + "\n")

    command = [*selectors, "-q", "-o", "addopts=", "-p", "no:cacheprovider", "--strict-config", "--strict-markers",
               "-W", "error", "-o", "xfail_strict=true",
               "--junitxml=" + str(out / "junit.xml")]
    if collect_only:
        command.append("--collect-only")
    if installed_only:
        canary.save(out, "installed-provider.json", canary._observe_installed_provider(canary.provider_files(root)))
        command.extend(["-o", "pythonpath="])
    temporary_parent = os.environ.get("RELEASE_CONTRACT_TEMP")
    previous = Path.cwd()
    os.chdir(root)
    start = time.monotonic()
    try:
        # Consumers may discover Git governance locks by walking their parents.
        # Keep mutable inputs outside any checkout even when reports live under it.
        with tempfile.TemporaryDirectory(prefix="release-contract-", dir=temporary_parent) as scratch:
            base = Path(scratch).resolve()
            canary.require(not any((p / ".git").exists() for p in (base, *base.parents)),
                           "Provide an OS temporary directory outside Git for contract inputs")
            code = int(pytest.main([*command, "--basetemp=" + str(base / "tests")],
                                   plugins=[pr_ci_pytest, Started()]))
    finally:
        os.chdir(previous)
    canary.save(out, "execution.json", {"exit_code": code, "seconds": time.monotonic() - start})
    return code


def worker(args) -> int:
    expected = verify_candidate(args)
    selectors = profile_selectors(args.profile)
    canary.require(args.profile != "coverage" or sys.platform != "win32", "Coverage producer requires a POSIX owner")
    out = canary.safe(args.output)
    canary.require(not out.is_relative_to(args.root.absolute()), "Contract evidence must be outside candidate source")
    out.mkdir(parents=True, exist_ok=False)
    code = execute_tests(args.root, selectors, out)
    canary.require(code == 0, "Contract canary cases failed")
    starts = [json.loads(line) for line in (out / "started.jsonl").read_text().splitlines()]
    counts = validate_results(selectors, runner.q.load_json(out / "collection.json"), starts,
                              core_shards.junit(out / "junit.xml"))
    canary.require(verify_candidate(args) == expected, "Contract canary provider changed")
    canary.save(out, "result.json", {"schema_version": SCHEMA, "profile": args.profile,
                                    "source_sha": args.source_sha, "status": "passed", **counts})
    return 0


def run(args) -> int:
    verify_candidate(args)
    out = canary.safe(args.output)
    canary.require(not out.is_relative_to(args.root.absolute()), "Contract evidence must be outside candidate source")
    out.mkdir(parents=True, exist_ok=False)
    profiles = [("fixtures", "inherited"), ("fixtures", "unset")]
    if sys.platform != "win32":
        profiles.append(("coverage", "unset"))
    results: list[dict[str, Any]] = []
    report: dict[str, Any] = {"schema_version": SCHEMA, "source_sha": args.source_sha, "publication_authority": False,
              "runtime": {"python": sys.version, "platform": sys.platform, "prefix": str(sys.prefix)},
              "status": "running", "profiles": results}
    runner.q.write_json(out / "result.json", report)
    try:
        for profile, mode in profiles:
            target = out / (profile + "-" + mode)
            env = runner.child_environment(out / (target.name + "-state"), out / (target.name + "-temp"), args.archive)
            env.pop("LLM_WIKI_GO", None)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["RELEASE_CONTRACT_TEMP"] = tempfile.gettempdir()
            if mode == "inherited":
                cache = canary.safe(args.helper_cache_dir or out / "helper-cache")
                canary.require(not cache.is_relative_to(args.root.absolute()), "Helper cache must be outside candidate source")
                env["LLM_WIKI_CACHE_DIR"] = str(cache)
            command = [sys.executable, "-I", str(Path(__file__).resolve()), "worker", "--root", str(args.root),
                       "--archive", str(args.archive), "--identity", str(args.identity), "--source-sha", args.source_sha,
                       "--expected-prefix", str(args.expected_prefix), "--output", str(target), "--profile", profile]
            started = time.monotonic()
            with tempfile.TemporaryDirectory(prefix="contract-worker-") as temporary:
                env.update(TMPDIR=temporary, TEMP=temporary, TMP=temporary, RELEASE_CONTRACT_TEMP=temporary)
                execution = runner.invoke(command, args.root, env, out / (target.name + ".log"), timeout=180)
            code = execution["exit_code"]
            result: dict[str, Any] = {"profile": profile, "cache_mode": mode, "exit_code": code, "seconds": time.monotonic() - started}
            if execution["error"]:
                result["error"] = execution["error"]
            if code == 0:
                try:
                    result["counts"] = verify_profile(target, profile, args.source_sha)
                except (OSError, ValueError, RuntimeError) as error:
                    code = 1
                    result.update(exit_code=code, error=str(error))
            results.append(result)
            report["status"] = "failed" if code else "running"
            runner.q.write_json(out / "result.json", report)
            if code:
                return 1
        verify_candidate(args)
        ownership = out / "typescript-ownership"
        command = [sys.executable, "-I", str(Path(__file__).with_name("helper_ownership.py")), "probe",
                   "--all-families", "--root", str(args.root), "--archive", str(args.archive),
                   "--identity", str(args.identity), "--source-sha", args.source_sha, "--output", str(ownership)]
        if args.helper_cache_dir:
            command.extend(["--helper-cache-dir", str(args.helper_cache_dir)])
        else:
            command.append("--cold-only")
        result = runner.invoke(command, args.root, os.environ.copy(), out / "typescript-ownership.log", timeout=600)
        report["typescript_ownership"] = result
        canary.require(result["exit_code"] == 0 and runner.q.load_json(ownership / "result.json")["status"] == "passed",
                       "TypeScript ownership failed; see typescript-ownership/result.json")
        verify_candidate(args)
        report["status"] = "passed"
        runner.q.write_json(out / "result.json", report)
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        report.update(status="failed", error=str(error))
        runner.q.write_json(out / "result.json", report)
        return 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    for name in ("run", "worker"):
        p = commands.add_parser(name)
        for argument in ("root", "archive", "identity", "expected-prefix", "output"):
            p.add_argument("--" + argument, type=Path, required=True)
        p.add_argument("--source-sha", required=True)
        if name == "worker":
            p.add_argument("--profile", choices=("fixtures", "coverage"), required=True)
        else:
            p.add_argument("--helper-cache-dir", type=Path)
    args = parser.parse_args(argv)
    for name in ("root", "archive", "identity", "expected_prefix", "output"):
        setattr(args, name, Path(os.path.abspath(getattr(args, name))))
    try:
        return run(args) if args.operation == "run" else worker(args)
    except (OSError, ValueError, RuntimeError) as error:
        print("Release contract canary failed: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
