"""Serial owned baseline measurements with retained provider and raw observations.

The first timed call runs in a fresh process over a separately prepared wiki.
Five subsequent calls share that worker. Mutation workloads restore equivalent
owned input copies. OS filesystem caches remain uncontrolled.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any

from tests.developer_value.oracles import corpus_identity, verify_corpus
from tests.developer_value import runtime

try:
    import resource
except ImportError:  # Native Windows does not expose resource.getrusage.
    resource = None  # type: ignore[assignment]

SCHEMA = "developer-value-measurements/v1"
READ_LANES = ("context-v1", "context-v2", "context-v2-compact", "context-source-only", "search", "session-read")
MUTATING_LANES = ("changed-sync", "unchanged-sync", "prose-reanchor", "strict-validation")
LANES = (*READ_LANES, *MUTATING_LANES)
TARGETS = {"tiny": ("policy.py", "Batch.cap"), "library": ("policy.py", "Batch.cap"),
           "service": ("policy.py", "Batch.cap"), "large": ("search.py", "search_records")}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode()


def identity(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_bytes(canonical(value))
    os.replace(pending, path)


def harness_identity() -> dict[str, str]:
    folder = Path(__file__).parent
    return {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
            for name in ("fixtures.py", "oracles.py", "runtime.py", "measure.py", "corpus.json")}


def validate_retained_workload(path: Path, report: dict[str, Any], plan: dict[str, Any],
                               project: str, lane: str) -> None:
    """Recheck retained sample bytes and recompute success before resuming."""
    count = plan["warm_repetitions"] + 1
    if report["project"] != project or report["lane"] != lane or report["samples"] != count:
        raise ValueError("retained workload differs from its frozen schedule")
    if report["provider"]["source_tree_sha256"] != plan["provider"]["source_tree_sha256"]:
        raise ValueError("retained workload used a different provider")
    preparation_path = path / "preparation.json"
    if (not preparation_path.is_file() or preparation_path.is_symlink()
            or hashlib.sha256(preparation_path.read_bytes()).hexdigest() != report.get("preparation_sha256")):
        raise ValueError("retained preparation changed or is missing")
    preparation = json.loads(preparation_path.read_bytes())
    if preparation["plan_identity"] != plan["plan_identity"] or preparation["input_tree"] != runtime.tree_hashes(path / "inputs"):
        raise ValueError("retained preparation inputs differ from their frozen plan")
    expected_names = {f"sample-{index}.json" for index in range(count)}
    if set(report.get("sample_hashes", {})) != expected_names:
        raise ValueError("retained workload lacks exact sample commitments")
    samples = []
    for index in range(count):
        name = f"sample-{index}.json"
        sample_path = path / name
        if not sample_path.is_file() or sample_path.is_symlink():
            raise ValueError("retained sample is missing or redirected")
        raw = sample_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != report["sample_hashes"][name]:
            raise ValueError("retained sample bytes changed")
        sample = json.loads(raw)
        if canonical(sample) != raw or sample["index"] != index:
            raise ValueError("retained sample identity changed")
        observed = logical_signature(lane, sample["result"], sample["wiki_changed_paths"]) if sample["error"] is None else None
        if observed != sample["logical_signature"]:
            raise ValueError("retained logical evidence differs from the actual output")
        if sample["input_tree_identity"] != identity(preparation["input_tree"]):
            raise ValueError("retained sample input basis changed")
        samples.append(sample)
    completed = [s for s in samples if s["error"] is None]
    signatures = {identity(s["logical_signature"]) for s in completed}
    if (report["completed_calls"] != len(completed)
            or report["canonical_contexts_validated"] != sum(s["result"].get("canonical_validated") is True for s in samples)
            or report["cli_successes"] != sum(s["result"].get("exit_code") == 0 for s in samples)
            or report["logical_signature_hashes"] != sorted(signatures)
            or report["logical_outputs_repeatable"] != (len(signatures) == 1 and len(completed) == count)
            or report["first_wall_ns"] != samples[0]["wall_ns"]
            or report["errors_retained"] != [s["error"] for s in samples if s["error"] is not None]):
        raise ValueError("retained summary differs from its sample evidence")
    if plan["warm_repetitions"]:
        for field, function, measurement in (("warm_median_wall_ns", statistics.median, "wall_ns"),
                                            ("warm_min_wall_ns", min, "wall_ns"),
                                            ("warm_max_wall_ns", max, "wall_ns"),
                                            ("warm_median_cpu_ns", statistics.median, "cpu_ns")):
            if report[field] != function(s[measurement] for s in samples[1:]):
                raise ValueError("retained timing summary differs from its samples")


def request(project: str, lane: str) -> dict[str, Any]:
    path, symbol = TARGETS[project]
    selector = f"{path}:{symbol}"
    value: dict[str, Any] = {"schema_version": "llm-wiki-task-request/v1" if lane == "context-v1" else "llm-wiki-task-request/v2",
        "kind": "bug-diagnosis", "text": "Inspect the contract and its callers.", "requirements": [
            {"id": "contract", "facet": "source-contract", "selector": selector},
            {"id": "callers", "facet": "callers", "selector": selector},
            {"id": "behavior", "facet": "behavior", "selector": selector}]}
    if lane in {"context-source-only", "session-read"}:
        value["options"] = {"knowledge_mode": "off"}
    if lane == "context-v2-compact":
        value["storage_options"] = {"selection": "required-facets-v1", "receipt": "compact-v1"}
    return value


def prepare(project: str, lane: str, workspace: Path) -> dict[str, Any]:
    start = time.perf_counter_ns()
    runtime.prepare_workspace("library" if project == "tiny" else project, workspace, tiny=project == "tiny")
    previous = Path.cwd()
    try:
        os.chdir(workspace)
        if lane in {"context-v2", "context-v2-compact"}:
            result = runtime.run_cli(["knowledge", "migrate", "--wiki-dir", "wiki", "--to", "sharded-v2",
                                      "--recovery-dir", "recovery"])
            if result["exit_code"] != 0:
                raise ValueError("explicit baseline storage adoption failed: " + result["stderr"])
    finally:
        os.chdir(previous)
    return {"wall_ns": time.perf_counter_ns() - start, "source": runtime.tree_hashes(workspace / "src"),
            "wiki": runtime.tree_hashes(workspace / "wiki"),
            "storage": "sharded-v2" if lane in {"context-v2", "context-v2-compact"} else "flat-v1",
            "guide_policy": "none-tiny-policy-only" if project == "tiny" else "identical-authored-baseline-guides"}


def _context(api: Any, project: str, lane: str) -> dict[str, Any]:
    req = request(project, lane)
    context = api.build_task_context(req, src_dir="src", wiki_dir="wiki")
    payload = context.to_payload()
    if context.ok:
        api.validate_task_context(context.rendered, req)
    return {"ok": context.ok, "state": payload["state"], "request": req,
            "rendered": context.rendered, "rendered_bytes": len(context.rendered.encode()),
            "coverage": payload["coverage"], "facts": payload["facts"],
            "accounting": payload["accounting"], "work": payload.get("work"),
            "storage": payload.get("storage"), "canonical_validated": context.ok}


def operation(api: Any, project: str, lane: str) -> dict[str, Any]:
    if lane.startswith("context-"):
        return _context(api, project, lane)
    if lane == "search":
        result = api.search_wiki(TARGETS[project][1].split(".")[-1], src_dir="src", wiki_dir="wiki", limit=5)
        return {"response": result, "rendered_bytes": len(canonical(result))}
    if lane == "session-read":
        req = request(project, lane)
        with api.open_context_session(src_dir="src", wiki_dir="wiki") as session:
            first = session.read(req)
            if first.context is None:
                raise ValueError("first session read lacks a complete context")
            second = session.read(req, if_result_id=first.result_id)
            return {"initial": first.context.to_payload(), "initial_rendered": first.context.rendered,
                    "reuse": second.metadata(), "same_result": first.result_id == second.result_id,
                    "rendered_bytes": len(first.context.rendered.encode())}
    if lane in {"changed-sync", "unchanged-sync", "prose-reanchor"}:
        return runtime.run_cli(["sync", "--src-dir", "src", "--wiki-dir", "wiki",
                                "--jobs", "1", "--no-plugins", "--progress", "never"])
    if lane == "strict-validation":
        return runtime.run_cli(["lint", "--strict", "--src-dir", "src", "--wiki-dir", "wiki",
                                "--jobs", "1", "--progress", "never"])
    raise ValueError("unknown measurement lane")


def logical_signature(lane: str, output: dict[str, Any], changes: list[str]) -> dict[str, Any]:
    """Compare stable task evidence; omit transport/root-dependent identities."""
    if lane.startswith("context-"):
        return {"ok": output["ok"], "state": output["state"],
                "coverage": [{k: row[k] for k in ("requirement_id", "state", "satisfied", "reason")}
                             for row in output["coverage"]],
                "facts": [{k: row[k] for k in ("facet", "selector", "state", "observation", "qualification")}
                          for row in output["facts"]]}
    if lane == "search":
        response = output["response"]
        return {"paths": [row["path"] for row in response["results"]], "total": response["total"],
                "bounds": response["bounds"], "ranking": response.get("ranking")}
    if lane == "session-read":
        return {"same_result": output["same_result"], "state": output["reuse"]["state"],
                "coverage": [{k: row[k] for k in ("requirement_id", "state", "satisfied", "reason")}
                             for row in output["initial"]["coverage"]]}
    return {"exit_code": output["exit_code"], "changed_paths": changes,
            "integrity": output["integrity"]["status"],
            "expected_change": output["expected_change"],
            "content_commitments": output["content_commitments"]}


def worker(provider_root: Path, project: str, lane: str, prepared: Path, output: Path, warm: int) -> dict[str, Any]:
    load_started = time.perf_counter_ns()
    api = runtime.load_provider(provider_root)
    import_ns = time.perf_counter_ns() - load_started
    before_template = runtime.tree_hashes(prepared)
    samples = []
    original = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="dv-measured-", dir=runtime.temporary_parent()) as directory:
        for index in range(warm + 1):
            clone_ns = 0
            workspace = prepared
            if lane in MUTATING_LANES:
                workspace = Path(directory) / f"sample-{index}"
                started = time.perf_counter_ns()
                shutil.copytree(prepared, workspace, ignore=shutil.ignore_patterns("__pycache__"))
                clone_ns = time.perf_counter_ns() - started
                path, _ = TARGETS[project]
                if lane == "changed-sync":
                    source = workspace / "src" / path
                    source.write_text(source.read_text() + "\n\ndef baseline_added_marker() -> int:\n    return 1\n")
                if lane == "prose-reanchor":
                    page = workspace / "wiki/modules" / (Path(path).stem + ".md")
                    text = page.read_text()
                    marker = "The owned baseline retains this authored operational explanation."
                    if text.count("## Description\n") != 1:
                        raise ValueError("baseline prose owner is missing or ambiguous")
                    page.write_text(text.replace("## Description\n", "## Description\n\n" + marker + "\n", 1))
            before = runtime.tree_hashes(workspace / "wiki")
            os.chdir(workspace)
            start, cpu = time.perf_counter_ns(), time.process_time_ns()
            try:
                result = operation(api, project, lane)
                error = None
            except Exception as exc:
                result = {}
                error = {"type": type(exc).__name__, "message": str(exc)}
            elapsed, cpu_elapsed = time.perf_counter_ns() - start, time.process_time_ns() - cpu
            os.chdir(original)
            after = runtime.tree_hashes(workspace / "wiki")
            changes = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
            if lane in READ_LANES and changes:
                raise ValueError("a measured read changed wiki artifacts")
            if lane in MUTATING_LANES and error is None:
                path, _ = TARGETS[project]
                with_cwd = Path.cwd()
                try:
                    os.chdir(workspace)
                    inspected = api.inspect_concept("modules/" + Path(path).stem + ".md",
                        src_dir="src", wiki_dir="wiki", live=True, include_evidence=True)
                finally:
                    os.chdir(with_cwd)
                selected = inspected["concept"]
                current = (selected.get("concept") or {}).get("freshness", {})
                valid = (selected.get("found") is True
                         and selected.get("knowledge", {}).get("availability") == "ready"
                         and current.get("state") == "current" and current.get("live_comparison_performed") is True)
                result["integrity"] = {"status": "validated" if valid else "unavailable", "inspection": inspected,
                                       "timed": False}
                result["content_commitments"] = after
                if lane == "changed-sync":
                    generated = (workspace / "wiki/modules" / (Path(path).stem + ".md")).read_text()
                    expected_change = ("def baseline_added_marker() -> int:" in (workspace / "src" / path).read_text()
                                       and "baseline_added_marker" in generated)
                elif lane == "prose-reanchor":
                    expected_change = "The owned baseline retains this authored operational explanation." in (
                        workspace / "wiki/modules" / (Path(path).stem + ".md")).read_text()
                else:
                    expected_change = not changes
                result["expected_change"] = expected_change
                if result["exit_code"] != 0 or not valid or not expected_change:
                    error = {"type": "ObservedWorkflowFailure", "message": "CLI exit, artifact integrity, or expected change failed"}
            peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss if resource is not None else None
            sample = {"index": index, "condition": "first-call-fresh-worker" if index == 0 else "warm-worker",
                      "wall_ns": elapsed, "cpu_ns": cpu_elapsed, "workspace_copy_ns": clone_ns,
                      "process_peak_memory_bytes": None if peak is None else (peak if sys.platform == "darwin" else peak * 1024),
                      "wiki_changed_paths": changes, "error": error, "result": result,
                      "input_tree_identity": identity(before_template),
                      "logical_signature": logical_signature(lane, result, changes) if error is None else None}
            samples.append(sample)
            save(output / f"sample-{index}.json", sample)
    if runtime.tree_hashes(prepared) != before_template:
        raise ValueError("prepared measurement input was changed")
    successful = [s for s in samples if s["error"] is None]
    signatures = {identity(s["logical_signature"]) for s in successful}
    report = {"project": project, "lane": lane, "provider": runtime.provider_identity(),
              "provider_import_ns": import_ns, "samples": len(samples), "completed_calls": len(successful),
              "canonical_contexts_validated": sum(s["result"].get("canonical_validated") is True for s in samples),
              "cli_successes": sum(s["result"].get("exit_code") == 0 for s in samples),
              "logical_outputs_repeatable": len(signatures) == 1 and len(successful) == len(samples),
              "logical_signature_hashes": sorted(signatures), "first_wall_ns": samples[0]["wall_ns"],
              "sample_hashes": {f"sample-{s['index']}.json": hashlib.sha256(canonical(s)).hexdigest() for s in samples},
              "warm_median_wall_ns": statistics.median(s["wall_ns"] for s in samples[1:]) if warm else None,
              "warm_min_wall_ns": min(s["wall_ns"] for s in samples[1:]) if warm else None,
              "warm_max_wall_ns": max(s["wall_ns"] for s in samples[1:]) if warm else None,
              "warm_median_cpu_ns": statistics.median(s["cpu_ns"] for s in samples[1:]) if warm else None,
              "errors_retained": [s["error"] for s in samples if s["error"] is not None],
              "model_execution_established": False}
    save(output / "summary.json", report)
    return report


def _child(provider_root: Path, script: str, arguments: list[str], *, timeout: int = 1800,
           preload: bool = True) -> dict[str, Any]:
    argv = runtime.provider_command(script, *arguments, preload=preload)
    start = time.perf_counter_ns()
    completed = subprocess.run(argv, capture_output=True, text=True,
                               timeout=timeout, cwd=runtime.HARNESS_ROOT)
    elapsed = time.perf_counter_ns() - start
    if completed.returncode:
        raise ValueError("measurement child failed: " + completed.stderr[-5000:])
    return {"payload": json.loads(completed.stdout), "process_observation": {"argv": argv,
            "wall_ns": elapsed, "exit_code": completed.returncode,
            "stdout_bytes": len(completed.stdout.encode()), "stderr": completed.stderr}}


def run(provider_root: Path, output: Path, *, selected_projects: list[str] | None = None,
        selected_lanes: list[str] | None = None, warm: int = 5, resume: bool = False) -> dict[str, Any]:
    runtime.load_provider(provider_root)
    manifest = verify_corpus()
    projects = selected_projects or list(TARGETS)
    lanes = selected_lanes or list(LANES)
    if not set(projects) <= TARGETS.keys() or not set(lanes) <= set(LANES) or not 0 <= warm <= 10:
        raise ValueError("unsupported project, lane, or repetition count")
    output = output.absolute()
    if output.is_symlink() or any(p.is_symlink() for p in output.parents):
        raise ValueError("measurement output must not redirect writes")
    plan = {"schema_version": SCHEMA, "provider": runtime.provider_identity(),
            "corpus_identity": corpus_identity(), "harness_identity": harness_identity(),
            "projects": projects, "lanes": lanes, "cold_repetitions": 1, "warm_repetitions": warm,
            "environment": {"python": platform.python_version(), "platform": platform.platform(),
                            "machine": platform.machine()}, "gates": manifest["gates"],
            "timing_definition": "First call in a fresh worker after a separate preparation process, then warm calls; import/preparation/copy costs are separate",
            "memory_definition": "Cumulative worker-process high-water mark, not operation-exclusive allocation",
            "disk_cache": "uncontrolled", "model_execution_established": False, "field_evidence_established": False}
    plan["plan_identity"] = identity(plan)
    if (output / "plan.json").exists():
        if not resume or json.loads((output / "plan.json").read_text()) != plan:
            raise ValueError("existing measurements require explicit resume with identical retained inputs")
    elif output.exists() and any(output.iterdir()):
        raise ValueError("refusing unrelated nonempty measurement output")
    save(output / "plan.json", plan)
    reports = []
    with tempfile.TemporaryDirectory(prefix="dv-prepared-", dir=runtime.temporary_parent()) as directory:
        for project in projects:
            for lane in lanes:
                destination = output / f"{project}-{lane}"
                if resume and (destination / "summary.json").exists():
                    retained = json.loads((destination / "summary.json").read_text())
                    validate_retained_workload(destination, retained, plan, project, lane)
                    reports.append(retained)
                    continue
                prepared = Path(directory) / f"{project}-{lane}"
                script = ("from tests.developer_value.measure import prepare\n"
                          "import json\nprint(json.dumps(prepare(sys.argv[1],sys.argv[2],Path(sys.argv[3]))))\n")
                prepared_call = _child(provider_root, script, [project, lane, str(prepared)])
                preparation = prepared_call["payload"]
                preparation["process_observation"] = prepared_call["process_observation"]
                preparation["plan_identity"] = plan["plan_identity"]
                preparation["input_tree"] = runtime.tree_hashes(prepared)
                if (destination / "inputs").exists():
                    raise ValueError("partial retained inputs require reconciliation; refusing overwrite")
                shutil.copytree(prepared, destination / "inputs", ignore=shutil.ignore_patterns("__pycache__"))
                save(destination / "preparation.json", preparation)
                script = ("from tests.developer_value.measure import worker\nimport json\n"
                          "print(json.dumps(worker(Path(sys.argv[1]),sys.argv[2],sys.argv[3],"
                          "Path(sys.argv[4]),Path(sys.argv[5]),int(sys.argv[6]))))\n")
                measured_call = _child(provider_root, script, [str(provider_root), project, lane, str(prepared), str(destination), str(warm)], preload=False)
                report = measured_call["payload"]
                report["process_observation"] = measured_call["process_observation"]
                report["preparation_sha256"] = hashlib.sha256((destination / "preparation.json").read_bytes()).hexdigest()
                save(destination / "summary.json", report)
                validate_retained_workload(destination, report, plan, project, lane)
                reports.append(report)
                print(f"{project}/{lane}: {report['completed_calls']}/{report['samples']} calls captured", file=sys.stderr, flush=True)
    result = {"schema_version": SCHEMA, "plan_identity": plan["plan_identity"], "workloads": reports,
              "total_samples": sum(r["samples"] for r in reports),
              "completed_calls": sum(r["completed_calls"] for r in reports),
              "all_logical_outputs_repeatable": all(r["logical_outputs_repeatable"] for r in reports),
              "model_execution_established": False, "field_evidence_established": False}
    save(output / "results.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project", choices=tuple(TARGETS), action="append")
    parser.add_argument("--lane", choices=LANES, action="append")
    parser.add_argument("--warm", type=int, default=5)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    result = run(args.provider_root, args.output, selected_projects=args.project,
                 selected_lanes=args.lane, warm=args.warm, resume=args.resume)
    print(json.dumps({"samples": result["total_samples"], "completed_calls": result["completed_calls"],
                      "logical_outputs_repeatable": result["all_logical_outputs_repeatable"]}, sort_keys=True))


if __name__ == "__main__":
    main()
