"""Authenticate native Windows timings and prepare nonqualifying scheduling trials."""

from __future__ import annotations

import argparse
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release import core_shards as shards
from release import hosted_evidence as hosted

LANE = shards.WINDOWS_LANE
HISTORY = "core-shard-windows-trial.json"
WORKFLOW = ".github/workflows/core-shard-shadow.yml"
def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _git(root: Path, *arguments: str, check: bool = True):
    return subprocess.run(["git", "--no-replace-objects", "-C", str(root), *arguments],
                          capture_output=True, text=True, check=check, timeout=60)


def runtime_key(environment: dict) -> dict:
    shards.validate_environment(environment, environment["profile"]["lane"])
    return {k: environment[k] for k in ("profile", "python", "machine")} | {
        "packages": {k: v for k, v in environment["packages"].items() if k != "agent-wiki-cli"}}


def _source_hashes(root: Path, source: str, names: set[str]) -> dict:
    result = {}
    for name in sorted(names):
        shards.q._canonical_junit_selector(name)
        require(name.startswith("tests/") and name.endswith(".py") and "::" not in name, "unsafe timing source")
        size = _git(root, "cat-file", "-s", source + ":" + name).stdout.strip()
        require(size.isdigit() and int(size) <= 2 * 1024 * 1024, "timing source exceeds bound")
        raw = subprocess.check_output(["git", "--no-replace-objects", "-C", str(root), "show", source + ":" + name], timeout=60)
        result[name] = hosted.sha256(raw)
    return result


def file_times(cases: dict) -> dict[str, int]:
    times: dict[str, Decimal] = defaultdict(Decimal)
    for node, case in cases.items():
        try:
            value = Decimal(case.get("time", "NaN"))
        except InvalidOperation as exc:
            raise ValueError("invalid native case duration") from exc
        require(value.is_finite() and value >= 0, "missing or invalid native case duration")
        times[shards.file_name(node)] += value * 1000
    return {name: max(1, int(value.to_integral_value(rounding=ROUND_CEILING))) for name, value in sorted(times.items())}


def capture(root: Path, work: Path, repository: str, run_id: int, attempt: int, *, client) -> dict:
    """Reauthenticate all producers and replay the complete logical Windows lane."""
    from release import manual_release as manual
    shards.positive(run_id, "native timing run")
    shards.positive(attempt, "native timing attempt")
    root = manual.safe(root)
    work = manual.safe(work if work.is_absolute() else root / work)
    manual.Store(root, work)  # Reuse ignored, nonredirected evidence ownership rules.
    manual.ensure_directory(work)
    run = client.get(f"/actions/runs/{run_id}")
    require(run.get("id") == run_id and run.get("run_attempt") == attempt
            and run.get("status") == "completed" and run.get("event") == "workflow_dispatch"
            and run.get("path", "").partition("@")[0] == hosted.WORKFLOW and run.get("head_branch") == "main"
            and run.get("repository", {}).get("full_name") == repository
            and run.get("head_repository", {}).get("full_name") == repository, "native timing run identity differs")
    source = run["head_sha"]
    shards.q._require_sha(source, "timing source")
    backend = manual.GitHubBackend(root, work, repository, getattr(client, "token", "injected-read-only-transport"))
    backend.client = client
    contract = hosted.artifact_contract("union", "platform-sharded")
    evidence = {}
    for role in ("windows-plan", "windows-shard-0", "windows-shard-1", "windows"):
        name, producer, _ = contract["RD-01:" + role]
        evidence[role] = backend._artifact({"candidate_sha": source}, run, name, producer)
    preparation = evidence["windows-plan"]
    plan = shards.read(preparation / "plan.json")
    context = plan["context"]
    require(context["environment"]["profile"]["lane"] == LANE, "timing lane differs")
    raw_shards = [evidence["windows-shard-" + str(i)] for i in range(2)]
    allowlist = manual.git(root, "show", source + ":release/skip-allowlist.json").stdout
    with tempfile.TemporaryDirectory(prefix="native-schedule-") as temporary:
        policy = Path(temporary) / "skip-allowlist.json"
        policy.write_text(allowlist)
        shards.validate_aggregation(evidence["windows"], preparation, raw_shards,
                                                context["identity"], context["harness_sha256"], run_id, attempt, policy)
    require(context["identity"]["source"]["sha"] == source, "timing plan source differs")
    cases = shards.junit(evidence["windows"] / (LANE + ".xml"))
    times = file_times(cases)
    hashes = _source_hashes(root, source, set(times))
    history = {"schema_version": shards.NATIVE_HISTORY_SCHEMA, "source_sha": source,
               "run_id": run_id, "run_attempt": attempt,
               "lanes": {LANE: {"profile": shards.profile(LANE), "environment": context["environment"],
                                "files_ms": times, "files_sha256": hashes}}}
    transports = {role: manual.read(path.parent / "transport.json") for role, path in evidence.items()}
    jobs = client.list(f"/actions/runs/{run_id}/attempts/{attempt}/jobs", "jobs")
    observations = []
    for index, path in enumerate(raw_shards):
        receipt = shards.read(path / "execution.json")
        shard_cases = shards.junit(path / "junit.xml")
        elapsed = sum(Decimal(case.get("time", "0")) for case in shard_cases.values())
        require(float(elapsed) <= receipt["seconds"] + 1, "case durations exceed their actual producer duration")
        producer_id = transports["windows-shard-" + str(index)]["artifact"]["id"]
        files = plan["shards"][index]["files"]
        per_file = {name: {"estimated_ms": plan["weights_ms"][name], "case_ms": times[name]} for name in files}
        fresh = set(plan["fresh_history_files"])
        stale = set(plan["stale_history_files"])
        estimates = {}
        for category, selected in (("fresh", fresh), ("stale", stale),
                                   ("fallback", set(files) - fresh - stale)):
            group = sorted(set(files) & selected)
            estimates[category] = {"files": len(group),
                                   "estimated_ms": sum(plan["weights_ms"][f] for f in group),
                                   "observed_case_ms": sum(times[f] for f in group)}
        observations.append({"index": index, "weight_contributions": estimates, "file_comparison": per_file, "worker_seconds": receipt["seconds"], "case_seconds": float(elapsed),
                             "artifact_id": producer_id, "nodes": sorted(shard_cases)})
    audit = {"schema_version": "agent-wiki-native-timing-capture/v1", "qualifying": False,
             "repository": repository, "run": run, "jobs": jobs, "context": context,
             "inventory_sha256": shards.digest(sorted(cases)), "plan_sha256": shards.digest(plan),
             "artifacts": {role: {"id": row["artifact"]["id"], "digest": row["artifact"]["digest"],
                                   "inventory": row["inventory"]} for role, row in transports.items()},
             "shards": observations, "outcomes": shards.outcomes(cases),
             "readers": {name: shards.q.sha256_file(root / "release" / name) for name in
                         ("core_schedule.py", "core_shards.py", "manual_release.py", "hosted_evidence.py", "qualification.py")}}
    return {"history": history, "audit": audit}


def score(training: dict, holdout: dict, root: Path) -> dict:
    """Held-out case-time projection; never interpret it as elapsed runner savings."""
    previous, observed = training["history"], holdout["history"]
    require(previous["run_id"] != observed["run_id"] and previous["source_sha"] != observed["source_sha"],
            "a training run cannot be its own held-out sample")
    require(runtime_key(previous["lanes"][LANE]["environment"]) == runtime_key(observed["lanes"][LANE]["environment"]),
            "native runtime or resolved dependency profile differs")
    require(_git(root, "merge-base", "--is-ancestor", previous["source_sha"], observed["source_sha"], check=False).returncode == 0,
            "training source is not earlier held-out history")
    latest = max(hosted.timestamp(row["completed_at"]) for row in training["audit"]["jobs"]
                 if row.get("completed_at") and row.get("name", "").startswith("Execute Windows core shard"))
    require(latest < hosted.timestamp(holdout["audit"]["run"]["created_at"]), "training observations include held-out time")
    nodes = sorted(holdout["audit"]["outcomes"])
    results = {}
    costs = observed["lanes"][LANE]["files_ms"]
    for count in (2, 3):
        plan = shards.plan(nodes, holdout["audit"]["context"], count, previous, purpose="shadow",
                           file_hashes=observed["lanes"][LANE]["files_sha256"])
        seconds = [sum(costs[name] for name in row["files"]) / 1000 for row in plan["shards"]]
        results[str(count)] = {"case_seconds": seconds, "longest_case_seconds": max(seconds),
                               "summed_case_seconds": sum(seconds), "imbalance_seconds": max(seconds) - min(seconds),
                               "assignment": [row["files"] for row in plan["shards"]],
                               "fresh_files": len(plan["fresh_history_files"]), "stale_files": plan["stale_history_files"]}
    return {"schema_version": "agent-wiki-native-schedule-score/v1", "qualifying": False,
            "training_run": previous["run_id"], "held_out_run": observed["run_id"], "nodes": len(nodes),
            "actual_shards": [{k: v for k, v in row.items() if k != "nodes"} for row in holdout["audit"]["shards"]],
            "projections": results, "decision": "native-shadow-trial-required",
            "scope": "Held-out case times only. Setup, queue, inter-case effects and paid runner time are excluded."}


def matrices(root: Path, *, scope: str, windows_shards: int, history: str, fixtures: bool) -> dict:
    require(scope in {"windows", "all"} and type(windows_shards) is int and windows_shards in {2, 3}
            and history in {"committed", "windows-trained"} and type(fixtures) is bool, "invalid shadow experiment")
    runtime = shards.read(root / "release/runtime-policy.json")
    windows_python = runtime["profiles"]["windows-core"]["python"]
    require(len(windows_python) == 1, "shadow requires one declared native Windows interpreter")
    lanes = [LANE] if scope == "windows" else list(shards.PROFILES)
    references, workers = [], []
    for lane in lanes:
        row = {"lane": lane, "os": shards.PROFILES[lane]["os"],
               "python": windows_python[0] if lane == LANE else shards.PROFILES[lane]["python"],
               "shards": windows_shards if lane == LANE else 2,
               "history": history if lane == LANE else "committed"}
        references.append(row)
        workers.extend({**row, "shard": i} for i in range(row["shards"]))
    return {"schema_version": "agent-wiki-core-shadow-options/v1", "qualifying": False,
            "prepared_workspaces": fixtures, "reference": {"include": references},
            "shards": {"include": workers}, "compare": {"include": references}}


def job_metrics(jobs: list[dict]) -> dict:
    """Keep queue, makespan, runner time and failure observation as separate clocks."""
    completed, pending, failures = [], [], []
    for job in jobs:
        if job.get("status") != "completed" or not job.get("started_at") or not job.get("completed_at"):
            pending.append(job["name"])
            continue
        start, end = hosted.timestamp(job["started_at"]), hosted.timestamp(job["completed_at"])
        require(end >= start, "negative native job interval")
        queue = None if not job.get("created_at") else (start - hosted.timestamp(job["created_at"])).total_seconds()
        require(queue is None or queue >= 0, "negative native queue interval")
        row = {"name": job["name"], "job_id": job["id"], "seconds": (end - start).total_seconds(),
               "queue_seconds": queue, "started_at": job["started_at"], "completed_at": job["completed_at"],
               "conclusion": job["conclusion"]}
        completed.append(row)
        if row["conclusion"] != "success":
            failures.append(row)
    return {"jobs": completed, "pending": pending,
            "summed_runner_seconds": sum(row["seconds"] for row in completed),
            "elapsed_span_seconds": (max(hosted.timestamp(r["completed_at"]) for r in completed)
                                     - min(hosted.timestamp(r["started_at"]) for r in completed)).total_seconds() if completed else None,
            "execution_imbalance_seconds": max(r["seconds"] for r in completed) - min(r["seconds"] for r in completed) if completed else None,
            "first_failed_producer": min(failures, key=lambda r: hosted.timestamp(r["completed_at"])) if failures else None,
            "first_case_failure_time": "unobserved; job completion bounds the observation, not the testcase failure time"}


def native_clocks(run: dict, jobs: list[dict]) -> dict:
    for job in jobs:
        require(job.get("run_id") == run["id"] and job.get("run_attempt") == run["run_attempt"]
                and job.get("head_sha") == run["head_sha"], "native clock producer belongs to another attempt/source")
    producers = [r for r in jobs if r["name"].startswith(("Core reference (", "Core shard ("))]
    references = [r for r in producers if r["name"].startswith("Core reference (")]
    workers = [r for r in producers if r["name"].startswith("Core shard (")]
    result = job_metrics(producers)
    result.update(schema_version="agent-wiki-native-clocks/v1", qualifying=False, run_id=run["id"],
                  run_attempt=run["run_attempt"], source_sha=run["head_sha"], workers=job_metrics(workers))
    if references and workers and not result["pending"]:
        ready = max(hosted.timestamp(r["completed_at"]) for r in references)
        starts = [hosted.timestamp(r["started_at"]) for r in workers]
        require(min(starts) >= ready, "native workers started before their reference plans completed")
        result["workers"]["elapsed_after_reference_seconds"] = (
            max(hosted.timestamp(r["completed_at"]) for r in workers) - ready).total_seconds()
        result["workers"]["queue_after_reference_seconds"] = {
            r["name"]: (hosted.timestamp(r["started_at"]) - max(ready, hosted.timestamp(r.get("created_at") or r["started_at"])) ).total_seconds()
            if r.get("created_at") else None for r in workers}
    return result


def capture_trial(root: Path, work: Path, repository: str, run_id: int, attempt: int, *, client) -> dict:
    from release import manual_release as manual

    root = manual.safe(root)
    work = manual.safe(work if work.is_absolute() else root / work)
    manual.Store(root, work)
    manual.ensure_directory(work)
    run = client.get(f"/actions/runs/{run_id}")
    require(run.get("id") == run_id and run.get("run_attempt") == attempt and run.get("event") == "workflow_dispatch"
            and run.get("path", "").partition("@")[0] == WORKFLOW and run.get("status") == "completed"
            and run.get("conclusion") == "success" and run.get("repository", {}).get("full_name") == repository
            and run.get("head_repository", {}).get("full_name") == repository, "shadow trial is incomplete or belongs to another producer")
    backend = manual.GitHubBackend(root, work, repository, getattr(client, "token", "injected-read-only-transport"))
    backend.client = client
    state = {"candidate_sha": run["head_sha"]}
    frozen = backend._artifact(state, run, f"core-shard-inputs-{attempt}", "Freeze core shard shadow inputs")
    options = shards.read(frozen / "shadow-options.json")
    require(options.get("schema_version") == "agent-wiki-core-shadow-options/v1" and options.get("qualifying") is False
            and len(options["reference"]["include"]) == 1 and options["reference"]["include"][0]["lane"] == LANE,
            "timing comparison requires an isolated Windows trial")
    identity = shards.q._validate_identity(shards.read(frozen / "identity.json"))
    require(identity["source"]["sha"] == run["head_sha"]
            and identity["source"]["archive_sha256"] == shards.q.sha256_file(frozen / "candidate-source.tar"),
            "shadow source archive differs")
    directory = backend._artifact(state, run, f"core-shard-comparison-{LANE}-{attempt}", f"Core shard parity ({LANE})")
    comparison = shards.read(directory / "comparison.json")
    require(comparison.get("qualifying") is False and comparison.get("purpose") == "shadow"
            and comparison.get("complete") is True and comparison.get("passed") is True, "native shadow parity failed")
    context = comparison["context"]
    shards.validate_context(context)
    require(context["identity"] == identity and context["run_id"] == run_id and context["run_attempt"] == attempt
            and context["harness_sha256"] == shards.q.sha256_file(frozen / "qualification-harnesses.tar")
            and comparison["shard_count"] == options["reference"]["include"][0]["shards"], "shadow comparison source or layout differs")
    profiles = comparison.get("prepared_workspace_profiles", {})
    require(set(profiles) == {"reference", *(f"shard-{i}" for i in range(comparison["shard_count"]))}
            and profiles["reference"]["enabled"] is False
            and all(v["enabled"] is options["prepared_workspaces"] for k, v in profiles.items() if k != "reference"),
            "prepared fixture experiment is missing or differs from its frozen options")
    outcomes = shards.outcomes(shards.junit(directory / (LANE + ".xml")))
    require(len(outcomes) == comparison["collected"], "native trial inventory differs from its comparison")
    jobs = client.list(f"/actions/runs/{run_id}/attempts/{attempt}/jobs", "jobs")
    clocks = native_clocks(run, jobs)
    require(not clocks["pending"] and clocks["first_failed_producer"] is None, "native trial has missing or failed producers")
    require(len(clocks["workers"]["jobs"]) == comparison["shard_count"], "native worker clocks are incomplete")
    return {"schema_version": "agent-wiki-native-trial/v1", "qualifying": False, "run": run,
            "options": options, "comparison": comparison, "clocks": clocks,
            "inventory_sha256": shards.digest(sorted(outcomes)), "outcomes_sha256": shards.digest(outcomes),
            "artifact_transports": {"inputs": manual.read(frozen.parent / "transport.json")["artifact"],
                                    "comparison": manual.read(directory.parent / "transport.json")["artifact"]}}


def compare_trials(pairs: list[dict]) -> dict:
    results, sources, runs = [], set(), set()
    for pair in pairs:
        control, candidate = pair["control"], pair["candidate"]
        for sample in (control, candidate):
            require(sample.get("schema_version") == "agent-wiki-native-trial/v1" and sample.get("qualifying") is False
                    and sample["comparison"].get("passed") is True and sample["comparison"].get("complete") is True,
                    "paired native parity evidence is incomplete")
            key = (sample["run"]["id"], sample["run"]["run_attempt"])
            require(key not in runs, "duplicate native sample")
            runs.add(key)
        source = control["run"]["head_sha"]
        require(source == candidate["run"]["head_sha"] and source not in sources, "each pair needs its own exact held-out candidate")
        sources.add(source)
        require(runtime_key(control["comparison"]["context"]["environment"])
                == runtime_key(candidate["comparison"]["context"]["environment"]), "paired native runtime/dependencies differ")
        require(control["inventory_sha256"] == candidate["inventory_sha256"]
                and control["outcomes_sha256"] == candidate["outcomes_sha256"], "paired native inventories/outcomes differ")
        old_options, new_options = (s["options"]["reference"]["include"][0] for s in (control, candidate))
        require(old_options["shards"] == 2 and new_options["shards"] in {2, 3}
                and all(old_options[k] == new_options[k] for k in ("lane", "python", "history")), "paired native scheduling profiles differ")
        require(set(control["comparison"]["runner_images"]["shards"].values())
                == set(candidate["comparison"]["runner_images"]["shards"].values()), "paired native runner images differ")
        values = []
        for sample in (control, candidate):
            clocks = sample["clocks"]["workers"]
            require(not clocks["pending"] and clocks["first_failed_producer"] is None
                    and all(v is not None for v in clocks["queue_after_reference_seconds"].values()), "native timing/queue evidence is incomplete")
            values.append((clocks["elapsed_after_reference_seconds"], clocks["summed_runner_seconds"]))
        (old_time, old_cost), (new_time, new_cost) = values
        require(old_time > 0 and old_cost > 0 and new_time > 0 and new_cost > 0, "invalid native comparison interval")
        results.append({"source_sha": source, "control_run": control["run"]["id"], "candidate_run": candidate["run"]["id"],
                        "elapsed_ratio": new_time / old_time, "runner_seconds_ratio": new_cost / old_cost,
                        "meets_time_target": new_time <= old_time * .8, "meets_cost_budget": new_cost <= old_cost * 1.1})
    return {"schema_version": "agent-wiki-native-trial-decision/v1", "qualifying": False, "samples": results,
            "decision": "insufficient-held-out-samples" if len(results) < 2 else "ready-for-review"
            if all(r["meets_time_target"] and r["meets_cost_budget"] for r in results) else "keep-current-default",
            "required_held_out_candidates": 2, "longest_path_target_ratio": .8, "runner_time_budget_ratio": 1.1,
            "rollout_authority": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("capture", "score", "matrix", "constraints", "metrics", "trial", "decision"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--repository", default="Denissvgn/python-wiki-llm")
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--training", type=Path)
    parser.add_argument("--holdout", type=Path)
    parser.add_argument("--history", choices=("committed", "windows-trained"), default="committed")
    parser.add_argument("--scope", choices=("windows", "all"), default="windows")
    parser.add_argument("--windows-shards", type=int, default=2)
    parser.add_argument("--prepared-workspaces", action="store_true")
    parser.add_argument("--source-sha")
    parser.add_argument("--pairs", type=Path)
    args = parser.parse_args(argv)
    try:
        root = args.root.absolute()
        require(not args.output.exists(), "output is occupied; retain previous scheduling evidence")
        if args.operation == "capture":
            if args.work is None or args.run_id is None:
                raise ValueError("capture work and run identity required")
            value = capture(root, args.work, args.repository, args.run_id, args.attempt, client=hosted.GitHub(args.repository))
        elif args.operation == "trial":
            if args.work is None or args.run_id is None:
                raise ValueError("trial work and run identity required")
            value = capture_trial(root, args.work, args.repository, args.run_id, args.attempt, client=hosted.GitHub(args.repository))
        elif args.operation == "metrics":
            client = hosted.GitHub(args.repository)
            run = client.get(f"/actions/runs/{args.run_id}")
            require(run.get("id") == args.run_id and run.get("run_attempt") == args.attempt
                    and run.get("head_sha") == (args.source_sha or os.environ.get("GITHUB_SHA"))
                    and run.get("path", "").partition("@")[0] == WORKFLOW
                    and run.get("event") == "workflow_dispatch" and run.get("repository", {}).get("full_name") == args.repository
                    and run.get("head_repository", {}).get("full_name") == args.repository, "native clock run identity differs")
            value = native_clocks(run, client.list(f"/actions/runs/{args.run_id}/attempts/{args.attempt}/jobs", "jobs"))
        elif args.operation == "decision":
            if args.pairs is None:
                raise ValueError("paired trial captures required")
            value = compare_trials(shards.read(args.pairs)["pairs"])
        elif args.operation == "score":
            if args.training is None or args.holdout is None:
                raise ValueError("training and held-out captures required")
            value = score(shards.read(args.training), shards.read(args.holdout), root)
        elif args.operation == "matrix":
            value = matrices(root, scope=args.scope, windows_shards=args.windows_shards, history=args.history, fixtures=args.prepared_workspaces)
            if os.environ.get("GITHUB_OUTPUT"):
                with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
                    for name in ("reference", "shards", "compare"):
                        stream.write(name + "-matrix=" + json.dumps(value[name], separators=(",", ":")) + "\n")
        else:
            history = shards.read(root / "release" / HISTORY)
            row = history["lanes"][LANE]
            shards.validate_environment(row["environment"], LANE)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x") as stream:
                stream.write(shards.constraints(row["environment"]))
            return 0
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as exc:
        print("Native schedule preparation failed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
