"""Isolated performance worker and sequential paired comparison driver.

Gate timing and cProfile attribution are separate lanes. Mutating workloads
require --allow-writes and an explicitly supplied disposable fixture directory.
Large generated artifacts and raw evidence are never part of the test package.
"""
from __future__ import annotations

import argparse
from collections import Counter
import cProfile
import gc
import hashlib
import contextlib
import io
import os
import math
import statistics
import json
from pathlib import Path
import platform
import pstats
import inspect
try:
    import resource
except ImportError:
    resource = None
import subprocess
import sys
import time

from llm_wiki_cli import api
from llm_wiki_cli.services.knowledge_artifacts import build_knowledge_commit_plan
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage import canonical_bytes
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from llm_wiki_cli.services.knowledge_storage_diagnostics import storage_report, review_storage

ROOT = Path.cwd()
WIKI = ROOT / "docs/llm_wiki"
OUT = ROOT / "reports/knowledge-storage-performance"
PAGE = "entities/KnowledgeStorePlan.md"
SELECTORS = {"concept": "page:" + PAGE, "module": "source:src/llm_wiki_cli/services/workflow_profile.py"}


def rss():
    if resource is None:
        return None
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def measure(fn):
    gc.collect()
    before = rss()
    wall, cpu = time.perf_counter_ns(), time.process_time_ns()
    value = fn()
    return value, {"wall_ns": time.perf_counter_ns() - wall, "cpu_ns": time.process_time_ns() - cpu,
                   "process_peak_rss_bytes": rss(), "peak_rss_before_bytes": before}


def slice_details(capture):
    payload = capture.slice.to_payload()
    whole = Counter()
    for name, observation in capture.session.observations.items():
        kind = "indexes" if "/pack-index/" in name else "markdown" if name.endswith(".md") else name
        whole[kind] += len(observation.content)
    member_bytes = sum(key[2] for key in capture.session.range_observations if "/packs/" in key[0])
    index_bytes = sum(key[2] for key in capture.session.range_observations if "/index-pages/" in key[0])
    packs = {key[0]: key[3] for key in capture.session.range_observations if "/packs/" in key[0]}
    logical = Counter()
    for name, raw in capture.reader.objects.items():
        logical[capture.reader._nodes[name]["collection"]] += len(raw)
    indexes = getattr(capture.reader, "_indexes", {})
    return {"selected_counts": {kind: len(rows) for kind, rows in payload["records"].items()},
            "returned_record_bytes": len(canonical_bytes(payload["records"])),
            "physical_bytes_including_rechecks": capture.session.bytes_read,
            "operations_including_rechecks": capture.session.reads,
            "one_pass_file_bytes": dict(whole), "one_pass_member_range_bytes": member_bytes,
            "one_pass_index_page_range_bytes": index_bytes,
            "distinct_pack_files": len(packs), "whole_bytes_of_touched_packs": sum(packs.values()),
            "ranges": len(capture.session.range_observations), "logical_objects": len(capture.reader.objects),
            "decoded_logical_object_bytes_by_kind": dict(logical),
            "index_nodes": len(indexes),
            "manifest_bytes_with_rechecks": 2 * sum(size for name, size in whole.items() if name.startswith(".llm-wiki-manifest")),
            "member_locator_rows_decoded": sum(len(node.get("members", {})) for node in indexes.values()),
            "expanded_bytes": capture.reader.expanded_bytes,
            "lookup_complete": payload["lookup_complete"]}


def profile_summary(profiler, label):
    profiler.dump_stats(str(OUT / (label + ".prof")))
    stats = pstats.Stats(profiler)
    rows = []
    for (filename, line, name), (primitive, calls, own, cumulative, _) in stats.stats.items():
        if filename.startswith(str(ROOT)):
            filename = str(Path(filename).relative_to(ROOT))
        rows.append({"file": filename, "line": line, "function": name, "calls": calls,
                     "primitive_calls": primitive, "own_seconds": own, "cumulative_seconds": cumulative})
    from llm_wiki_cli.services.knowledge_storage import KnowledgeStoreReader
    lines, first_line = inspect.getsourcelines(KnowledgeStoreReader._expand)
    last_line = first_line + len(lines)
    attribution = {"scalar_canonical_calls": 0, "path_component_calls": 0}
    for (filename, line, name), (_, calls, _, _, callers) in stats.stats.items():
        if name == "require_portable_path_component":
            attribution["path_component_calls"] += calls
        if name == "canonical_bytes" and filename.endswith("knowledge_storage.py"):
            for (parent_file, parent_line, _), call_info in callers.items():
                if parent_file.endswith("knowledge_storage.py") and first_line <= parent_line < last_line:
                    attribution["scalar_canonical_calls"] += call_info[0]
    return {"top_self": sorted(rows, key=lambda r: r["own_seconds"], reverse=True)[:35],
            "top_cumulative": sorted(rows, key=lambda r: r["cumulative_seconds"], reverse=True)[:40],
            "selected_functions": [r for r in rows if any(s in r["file"] for s in ["knowledge_storage", "knowledge_packs", "context_session", "canonical_json", "validation.py"])
                                   or any(s in r["function"] for s in ["decompress", "posix.stat", "posix.open", "posix.close", "posix.fstat", "_io.BufferedReader", "encode", "decode", "sha256", "compress"])],
            "total_calls": stats.total_calls, "attribution": attribution}


def worker(workload, profiled):
    request = {"schema_version": "llm-wiki-task-request/v2", "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
               "requirements": [{"id": "concept", "facet": "concept", "selector": PAGE}]}
    session = previous = preloaded = None
    capture_start = time.perf_counter_ns()
    before_tree = artifact_tree(WIKI)
    capture_setup_ns = time.perf_counter_ns() - capture_start
    setup = None
    if workload in {"plan_unchanged", "plan_reuse", "incremental", "incremental_write"}:
        preloaded, setup = measure(lambda: load_knowledge_state(WIKI))
        assert preloaded.knowledge is not None and preloaded.manifest_basis is not None
    if workload == "session_warm":
        session = api.open_context_session(src_dir=str(ROOT), wiki_dir=str(WIKI))
        previous, setup = measure(lambda: session.read(request))
        assert previous.context is not None

    def operation():
        if workload.startswith("slice_"):
            read = capture_knowledge_slice(WIKI, [SELECTORS[workload[6:]]])
            read.finish()
            return read
        if workload == "task_cold":
            return api.build_task_context(request, src_dir=str(ROOT), wiki_dir=str(WIKI))
        if workload == "session_warm":
            return session.read(request, if_result_id=previous.result_id)
        if workload == "full_load":
            return load_knowledge_state(WIKI)
        if workload == "storage_full":
            return storage_report(WIKI, full=True)
        if workload == "inspect_one":
            return review_storage(WIKI, limit=1)
        if workload in {"plan_unchanged", "plan_reuse", "incremental", "incremental_write"}:
            options = {}
            if workload != "plan_unchanged":
                options["prior"] = preloaded.validated_artifacts
            if workload in {"incremental", "incremental_write"}:
                from dataclasses import replace
                model = replace(preloaded.knowledge, extensions={**preloaded.knowledge.extensions, "benchmark/edit": "one edit"})
            else:
                model = preloaded.knowledge
            plan = build_knowledge_commit_plan(WIKI, surface_index_bytes=(WIKI / ".llm-wiki-surface.json").read_bytes(),
                knowledge_index=model, manifest=preloaded.manifest_basis.without_artifact_hashes(), **options)
            if workload == "incremental_write":
                if not ALLOW_WRITES:
                    raise ValueError("--allow-writes is required")
                from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts
                commit_knowledge_artifacts(plan)
            return plan
        if workload == "inspect_scoped":
            return review_storage(WIKI, limit=1, selectors=[SELECTORS["concept"]])
        if workload == "audit_stream":
            from llm_wiki_cli.services.knowledge_stream_audit import audit_knowledge_stream
            return audit_knowledge_stream(WIKI)
        if workload in {"prune_preview", "prune_apply"}:
            from llm_wiki_cli.services.knowledge_storage_lifecycle import prune_knowledge_storage
            if workload == "prune_apply" and not ALLOW_WRITES:
                raise ValueError("--allow-writes is required")
            return prune_knowledge_storage(WIKI, dry_run=workload == "prune_preview")
        if workload in {"sync_default", "sync_no_cache", "sync_dry_run"}:
            if not ALLOW_WRITES:
                raise ValueError("--allow-writes and disposable source/wiki roots are required")
            from llm_wiki_cli.cli import main as cli
            argv = ["llm-wiki", "sync", "--src-dir", str(ROOT), "--wiki-dir", str(WIKI),
                    "--jobs", "1", "--no-plugins", "--progress", "never"]
            if workload == "sync_no_cache":
                argv.append("--no-cache")
            if workload == "sync_dry_run":
                argv.append("--dry-run")
            old_argv = sys.argv
            try:
                sys.argv = argv
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    cli()
                return {"emitted_bytes": len(output.getvalue().encode())}
            finally:
                sys.argv = old_argv
        raise ValueError(workload)

    profiler = cProfile.Profile() if profiled else None
    if profiler:
        profiler.enable()
    value, measurement = measure(operation)
    if profiler:
        profiler.disable()
    details = {}
    if workload.startswith("slice_"):
        details = slice_details(value)
    elif workload == "task_cold":
        payload = value.to_payload()
        assert value.ok
        details = {"rendered_bytes": len(value.rendered.encode()), "storage_receipt_bytes": len(canonical_bytes(payload["storage"])),
                   "fact_bytes": len(canonical_bytes(payload["facts"])), "state": payload["state"],
                   "storage_read_bytes": payload["storage"]["read_bytes"], "storage_operations": payload["storage"]["read_operations"]}
    elif workload == "session_warm":
        details = value.metadata()
        assert value.state == "unchanged" and details["reuse"]["rendering"]
    elif workload == "full_load":
        assert value.knowledge is not None and value.validated_artifacts is not None
        details = {"concepts": len(value.knowledge.concepts), "relationships": len(value.knowledge.relationships),
                   "physical_files": len(value.validated_artifacts.storage_objects)}
    elif workload in {"storage_full", "inspect_one", "inspect_scoped", "audit_stream"}:
        assert value["ok"]
        details = dict(value)
    elif workload in {"plan_unchanged", "plan_reuse", "incremental", "incremental_write"}:
        assert value.changed == (workload in {"incremental", "incremental_write"})
        details = {"changed": value.changed, "planned_files": len(value.storage_objects),
                   "planned_content_bytes": sum(len(row.content) for row in value.storage_objects),
                   "changed_files": sum(row.needs_write for row in value.storage_objects),
                   "bytes_rewritten": sum(len(row.content) for row in value.storage_objects if row.needs_write)}
    elif isinstance(value, dict):
        details = value
    if session:
        session.close()
    after_tree = artifact_tree(WIKI)
    changed = sorted(k for k in after_tree.keys() | before_tree.keys() if before_tree.get(k) != after_tree.get(k))
    details["artifact_changes"] = {"files": len(changed),
                                   "bytes_written": sum(after_tree[k][1] for k in changed if k in after_tree),
                                   "bytes_removed": sum(before_tree[k][1] for k in changed if k not in after_tree)}
    if not ALLOW_WRITES and changed:
        raise RuntimeError("read-only operation changed artifacts")
    details["retained_cache_bytes"] = details.get("work", {}).get("retained_bytes")
    details["capture_setup_ns"] = capture_setup_ns
    details["git_pack_bytes"] = git_pack_bytes(ROOT)
    if ALLOW_WRITES:
        details["recovery_bytes"] = sum(p.stat().st_size for p in ROOT.parent.glob("recovery*/**/*") if p.is_file())
        from llm_wiki_cli.services.knowledge_storage_lifecycle import prune_knowledge_storage
        try:
            details["orphan_bytes"] = prune_knowledge_storage(WIKI)["bytes"]
        except ValueError as exc:
            details["orphan_inspection_error"] = str(exc)
    return {"ok": True, "workload": workload, "profiled": profiled, "measurement": measurement, "setup": setup,
            "details": details, "profile": profile_summary(profiler, workload) if profiler else None}


def artifact_tree(wiki):
    return {p.relative_to(wiki).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size)
            for p in sorted(wiki.rglob("*")) if p.is_file()}


def git_pack_bytes(root):
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "--absolute-git-dir"],
                            capture_output=True, text=True, timeout=10)
    if result.returncode:
        return None
    return sum(p.stat().st_size for p in (Path(result.stdout.strip()) / "objects/pack").glob("*.pack"))


ALLOW_WRITES = False


def identity(root):
    result = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" not in path.parts:
            result.update(path.relative_to(root).as_posix().encode())
            result.update(path.read_bytes())
    return result.hexdigest()


def main():
    global ROOT, WIKI, OUT, PAGE, SELECTORS, ALLOW_WRITES
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--wiki", type=Path, required=True)
    parser.add_argument("--src-root", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--package-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--page", default=PAGE)
    parser.add_argument("--module", default=SELECTORS["module"])
    parser.add_argument("--allow-writes", action="store_true")
    parser.add_argument("--baseline-src", type=Path)
    parser.add_argument("--candidate-src", type=Path)
    parser.add_argument("--baseline-wiki", type=Path)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--workloads", nargs="+", default=["slice_concept", "slice_module", "task_cold", "session_warm"])
    args = parser.parse_args()
    ROOT, WIKI, OUT, PAGE = args.src_root.absolute(), args.wiki.absolute(), args.output.parent.absolute(), args.page
    args.output = args.output.absolute()
    if args.package_root is not None:
        args.package_root = args.package_root.absolute()
    os.chdir(args.project_root)
    SELECTORS = {"concept": "page:" + PAGE, "module": args.module}
    ALLOW_WRITES = args.allow_writes
    OUT.mkdir(parents=True, exist_ok=True)
    import llm_wiki_cli
    package_path = Path(llm_wiki_cli.__file__).resolve()
    if args.package_root is not None and args.package_root.resolve() not in package_path.parents:
        raise RuntimeError(f"wrong imported package: {package_path}")
    if args.worker:
        started = time.perf_counter()
        try:
            result = worker(args.worker, args.profile)
        except Exception as exc:
            result = {"ok": False, "workload": args.worker, "profiled": args.profile,
                      "error": type(exc).__name__ + ": " + str(exc), "failed_after_seconds": time.perf_counter() - started}
        result.update(python=platform.python_version(), platform=platform.platform(), package_path=str(package_path),
                      page_cache="uncontrolled/warm; no disk-cold claim", process="fresh",
                      verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"ok": result["ok"], "workload": args.worker, "output": str(args.output)}))
        return
    if args.baseline_src is None or args.candidate_src is None or args.samples < 1:
        parser.error("paired mode requires --baseline-src, --candidate-src and positive --samples")
    result = {"conditions": "Sequential alternating paired fresh processes; same interpreter; warm/uncontrolled OS cache.",
              "samples": args.samples, "runs": [], "identities": {}, "summary": {}}
    for label, source in (("baseline", args.baseline_src), ("candidate", args.candidate_src)):
        result["identities"][label] = {"source": str(source.absolute()), "source_sha256": identity(source)}
    for workload in args.workloads:
        for number in range(args.samples):
            for label in (["baseline", "candidate"] if number % 2 == 0 else ["candidate", "baseline"]):
                source = args.baseline_src if label == "baseline" else args.candidate_src
                wiki = args.baseline_wiki if label == "baseline" and args.baseline_wiki is not None else WIKI
                output = OUT / f"{args.output.stem}-{workload}-{label}-{number}.json"
                command = [sys.executable, str(Path(__file__).absolute()), "--worker", workload,
                           "--wiki", str(wiki), "--src-root", str(ROOT), "--output", str(output),
                           "--package-root", str(source), "--page", PAGE, "--module", args.module,
                           "--project-root", str(Path.cwd())]
                try:
                    completed = subprocess.run(command, env={**os.environ, "PYTHONPATH": str(source)},
                                               capture_output=True, text=True, timeout=600)
                    row = json.loads(output.read_text()) if completed.returncode == 0 else {
                        "ok": False, "error": completed.stderr[-4000:], "returncode": completed.returncode}
                except subprocess.TimeoutExpired:
                    row = {"ok": False, "error": "timeout after 600 seconds"}
                row.update(label=label, sample=number, workload=workload)
                result["runs"].append(row)
                args.output.write_text(json.dumps(result, indent=2) + "\n")
                print(workload, label, number, row["ok"], flush=True)
    for workload in args.workloads:
        result["summary"][workload] = {}
        for label in ("baseline", "candidate"):
            rows = [r for r in result["runs"] if r["workload"] == workload and r["label"] == label]
            summary = {"samples": len(rows), "failed": sum(not r["ok"] for r in rows)}
            for metric in ("wall_ns", "cpu_ns", "process_peak_rss_bytes"):
                values = sorted(r["measurement"][metric] for r in rows if r["ok"] and r["measurement"][metric] is not None)
                if values:
                    summary[metric] = {"median": statistics.median(values), "p95": values[math.ceil(.95 * len(values)) - 1],
                                       "population_variance": statistics.pvariance(values), "min": min(values), "max": max(values)}
            result["summary"][workload][label] = summary
    for label, source in (("baseline", args.baseline_src), ("candidate", args.candidate_src)):
        if result["identities"][label]["source_sha256"] != identity(source):
            result.setdefault("invalidated", []).append(label + " source changed during campaign")
    result["ok"] = not result.get("invalidated") and all(r["ok"] for r in result["runs"])
    args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
