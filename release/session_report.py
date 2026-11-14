"""Read-only release-session timelines and identity-bound diagnostic packets.

Reports are observations, never controller transitions or release authority.
Reading a session does not claim its lease, dispatch, poll through advance(),
write cached observations into its work directory, or re-run local stages.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release import hosted_evidence as hosted
from release import manual_release as manual
from release import preflight
from release import qualification_automation as automation

SCHEMA = "agent-wiki-session-timeline/v1"
PACKET_SCHEMA = "agent-wiki-release-diagnostic-packet/v1"
MAX_EVENTS = 20_000
MAX_EVENT_BYTES = 32 * 1024 * 1024
MAX_OBSERVATIONS = 128
RESULTS = {"qualify": "qualification", "dry-run": "dry_run", "tag": "tag", "publish": "publication", "github-release": "github_release"}
AGGREGATORS = {"owner-lanes", "bundle", "decision", "core-windows", "core-ubuntu", "discovery-allowlist"}
require = manual.require


def _bytes(path: Path, limit: int = MAX_EVENT_BYTES) -> bytes:
    return preflight._read(manual.safe(path), limit)


def _stamp(value: str) -> str:
    return hosted.timestamp(value).isoformat()


def snapshot(store: manual.Store) -> dict:
    """Observe stable state bytes without creating a lock or changing history."""
    for _ in range(3):
        before = _bytes(store.work / "state.json", 4 * 1024 * 1024)
        state = store.load()
        events = _bytes(store.work / "events.jsonl")
        after = _bytes(store.work / "state.json", 4 * 1024 * 1024)
        if before == after:
            break
    else:
        raise manual.SessionError("Session changed during read-only observation; retry this report")
    require(manual.git(store.root, "rev-parse", state["candidate_sha"] + "^{tree}").stdout.strip() == state["candidate_tree"],
            "Recorded session source/tree differs from original Git")
    rows, warnings = [], []
    lines = events.splitlines(keepends=True)
    require(len(lines) <= MAX_EVENTS, "Session event inventory exceeds bound")
    revisions = set()
    for index, line in enumerate(lines):
        if not line.endswith(b"\n"):
            require(index == len(lines) - 1, "Incomplete event occurs before journal tail")
            warnings.append({"kind": "incomplete-journal-tail", "bytes": len(line), "sha256": hosted.sha256(line)})
            continue
        row = hosted._json(line)
        require(isinstance(row, dict) and type(row.get("revision")) is int and row["revision"] > 0
                and isinstance(row.get("event"), str) and isinstance(row.get("phase"), str), "Invalid session event")
        _stamp(row["time"])
        for name in ("session_id", "candidate_sha", "candidate_tree", "repository"):
            require(name not in row or row[name] == state[name], "Journal event belongs to another session/source")
        if row["revision"] in revisions:
            warnings.append({"kind": "duplicate-journal-revision", "revision": row["revision"]})
        revisions.add(row["revision"])
        rows.append({**row, "line": index + 1, "sha256": hosted.sha256(line),
                     "binding": "event-bound" if "session_id" in row else "legacy-adjacent-state",
                     "ahead_of_state": row["revision"] > state["revision"]})
    require(manual.digest(before) == manual.digest(_bytes(store.work / "state.json", 4 * 1024 * 1024)),
            "Session changed while parsing its journal")
    return {"state": state, "events": rows, "warnings": warnings,
            "inputs": {"state_sha256": hosted.sha256(before), "events_sha256": hosted.sha256(events)}}


def operations(state: dict, events: list[dict]) -> list[dict]:
    """Never join two dispatches merely because their candidate SHA agrees."""
    found: dict[str, dict] = {}
    for event in events:
        if event.get("ahead_of_state"):
            continue
        pending = event.get("pending")
        if pending:
            identifier = pending.get("operation_id")
            require(isinstance(identifier, str) and re.fullmatch(r"[0-9a-f]{32}", identifier) is not None
                    and pending.get("action") in manual.ACTIONS, "Invalid journal operation identity")
            row = found.setdefault(identifier, {"operation_id": identifier, "action": pending["action"], "events": []})
            require(row["action"] == pending["action"], "Operation action changed in journal")
            row["pending"] = pending
            row["events"].append({"time": event["time"], "event": event["event"], "revision": event["revision"]})
            row["local_status"] = "outcome-unknown" if pending.get("outcome_unknown") else "submitted" if pending.get("response") is not None else "intent-recorded"
            if pending.get("failure"):
                row["local_status"] = "remote-failed"
        for action, result in event.get("results", {}).items():
            require(action in RESULTS and isinstance(result, dict), "Invalid accepted-result journal record")
            candidates = [r for r in found.values() if r["action"] == action]
            if candidates:
                latest = candidates[-1]
                latest["accepted_result"] = result
                latest["local_status"] = "accepted-verified" if result.get("verified") is True else "recorded-result"
    for action, field in RESULTS.items():
        result = state.get(field)
        candidates = [r for r in found.values() if r["action"] == action]
        if result and candidates:
            row = candidates[-1]
            row["accepted_result"] = result
            row["local_status"] = "accepted-verified" if result.get("verified") is True else "recorded-result"
    pending = state.get("pending")
    if pending:
        identifier = pending["operation_id"]
        row = found.setdefault(identifier, {"operation_id": identifier, "action": pending["action"], "events": []})
        row.update(pending=pending, current=True)
        row.setdefault("local_status", "outcome-unknown" if pending.get("outcome_unknown") else "intent-recorded")
    for recovery in state.get("recoveries", []):
        row = found.get(recovery.get("operation_id"))
        if row:
            row.update(disposition=recovery, local_status="startup-failure-disposed")
    for row in found.values():
        result = row.get("accepted_result", {})
        pending = row["pending"]
        response = pending.get("response") or {}
        failure = pending.get("failure") or {}
        run_id = result.get("run_id") or response.get("workflow_run_id") or response.get("run_id") or failure.get("run_id")
        if run_id is not None:
            require(type(run_id) is int and run_id > 0, "Invalid recorded workflow run ID")
        row.update(run_id=run_id, attempt=(result.get("attempt") or failure.get("attempt") or 1) if row["action"] in manual.WORKFLOWS else None,
                   started_at=pending["started_at"], candidate_sha=state["candidate_sha"], session_id=state["session_id"])
    return sorted(found.values(), key=lambda r: (hosted.timestamp(r["started_at"]), r["operation_id"]))


def local_preparation(state: dict, *, verify: bool = False) -> dict:
    """Separate host execution from the target declarations it cannot establish."""
    path = state.get("preflight_receipt") or state.get("preparation", {}).get("receipt")
    if not path:
        return {"host_stages": {"complete": False, "status": state.get("preparation", {}).get("status", "not-recorded")},
                "target_proof": {"status": "not-recorded", "rows": [], "fresh_native_proof_required": True}}
    try:
        path = manual.safe(Path(path))
        receipt = preflight.read_document(path)
        require(set(receipt) == preflight.RECEIPT_KEYS and receipt.get("schema_version") == preflight.RECEIPT_SCHEMA,
                "Unknown preflight receipt schema or fields")
        preflight._check_seal(receipt, "receipt_hash")
        require(receipt["plan"]["candidate_sha"] == state["candidate_sha"] and receipt["plan"]["root"] == state["root"],
                "Preflight receipt belongs to another session source/root")
        preflight._check_seal(receipt["plan"], "plan_hash")
        attempts = receipt["attempts"]
        completed = {r["stage"] for r in attempts if r.get("status") == "passed"}
        target = receipt["plan"]["binding"].get("maintenance", {}).get("target_runtime", {})
        complete = (receipt["operation"] == "run" and receipt["requested_stages"] == list(preflight.STAGES)
                    and [r["stage"] for r in attempts] == list(preflight.STAGES)
                    and all(s in completed for s in preflight.STAGES))
        result = {"receipt": str(path), "sha256": hosted.sha256(_bytes(path)), "receipt_status": receipt["status"],
                  "integrity": "sealed-record-only", "host_stages": {"complete": complete,
                  "stages": [{"stage": r["stage"], "status": r.get("status"), "started": r.get("started"), "seconds": r.get("seconds")} for r in attempts]},
                  "target_proof": {"status": target.get("status", "unknown"), "rows": target.get("rows", []),
                                   "target_execution_verified": target.get("target_execution_verified", False),
                                   "fresh_native_proof_required": True}, "pending": receipt.get("pending", [])}
        if verify:
            checked = preflight.verify_receipt(path)
            result.update(integrity="verified-current" if checked["ok"] else "failed", verification=checked)
        return result
    except (OSError, ValueError, KeyError) as exc:
        return {"host_stages": {"complete": False, "status": "receipt-unavailable"},
                "target_proof": {"status": "unknown", "fresh_native_proof_required": True}, "reason": str(exc)[:1000]}


def declaration(root: Path, source: str, action: str) -> dict:
    import yaml

    if action not in manual.WORKFLOWS:
        return {"path": None, "jobs": {}, "sha256": None}
    path = ".github/workflows/" + manual.WORKFLOWS[action][0]
    raw = subprocess.check_output(["git", "--no-replace-objects", "-C", str(root), "show", source + ":" + path], timeout=60)
    require(len(raw) <= 1024 * 1024, "Workflow declaration exceeds bound")
    value = yaml.safe_load(raw)
    require(isinstance(value, dict) and isinstance(value.get("jobs"), dict), "Original workflow jobs unavailable")
    require(len(value["jobs"]) <= 200, "Workflow job declaration exceeds bound")
    return {"path": path, "sha256": hosted.sha256(raw), "jobs": value["jobs"]}


def producer_failures(jobs: list[dict], definitions: dict) -> dict:
    from release.optimization_evidence import matrix_rows, resolve

    names: dict[str, list[str]] = {}
    for identifier, value in definitions.items():
        try:
            rows = matrix_rows(value)
        except (ValueError, TypeError, AttributeError):
            rows = [{}]
        for row in rows:
            name = resolve(value.get("name", identifier), row)
            if isinstance(name, str) and "${{" not in name:
                names.setdefault(name, []).append(identifier)
    mapped = {}
    for job in jobs:
        matches = set(names.get(job["name"], []))
        if len(matches) == 1:
            mapped[job["id"]] = next(iter(matches))
    def ancestors(identifier, active=frozenset()):
        require(identifier not in active, "Workflow dependency cycle")
        dependencies = definitions[identifier].get("needs", [])
        if isinstance(dependencies, str):
            dependencies = [dependencies]
        require(isinstance(dependencies, list) and all(d in definitions for d in dependencies), "Unknown workflow dependency")
        return set(dependencies) | {parent for d in dependencies for parent in ancestors(d, active | {identifier})}
    failed = [j for j in jobs if j.get("conclusion") in {"failure", "timed_out", "startup_failure", "action_required"}]
    failures = []
    for job in failed:
        identifier = mapped.get(job["id"])
        roots = ancestors(identifier) if identifier else set()
        causes = [j["id"] for j in failed if j["id"] != job["id"] and mapped.get(j["id"]) in roots]
        category = "unclassified" if identifier is None else "downstream-aggregate" if identifier in AGGREGATORS and causes else "independent-producer"
        failures.append({"job_id": job["id"], "name": job["name"], "declaration_id": identifier,
                         "conclusion": job["conclusion"], "observed_failed_at": job.get("completed_at"),
                         "failure_time_scope": "producer completion; actual first error time unobserved",
                         "category": category, "upstream_failed_jobs": causes,
                         "causality": "declared dependency linkage; inspect retained producer evidence" if causes else None})
    failures.sort(key=lambda r: (hosted.timestamp(r["observed_failed_at"]) if r["observed_failed_at"] else datetime.max.replace(tzinfo=timezone.utc), r["job_id"]))
    independent = [r for r in failures if r["category"] == "independent-producer"]
    return {"first_independent_failure": independent[0] if independent else None,
            "additional_independent_failures": independent[1:], "all_failures": failures,
            "cancelled_jobs": [j["id"] for j in jobs if j.get("conclusion") == "cancelled"],
            "pending_jobs": [{"job_id": j["id"], "name": j["name"], "status": j["status"]} for j in jobs if j.get("status") != "completed"]}


def bind_observation(state: dict, operation: dict, run: dict, jobs: list[dict]) -> dict:
    workflow, name = manual.WORKFLOWS[operation["action"]]
    require(run.get("id") == operation["run_id"] and run.get("run_attempt") == operation["attempt"]
            and run.get("head_sha") == state["candidate_sha"] and run.get("head_branch") == "main"
            and run.get("name") == name and run.get("path", "").partition("@")[0] == ".github/workflows/" + workflow
            and run.get("event") == "workflow_dispatch" and run.get("repository", {}).get("full_name") == state["repository"]
            and run.get("head_repository", {}).get("full_name") == state["repository"]
            and type(run.get("repository", {}).get("id")) is int
            and run["repository"]["id"] == run.get("head_repository", {}).get("id"), "Run observation belongs to another operation/source/attempt")
    require(hosted.timestamp(run["created_at"]) >= hosted.timestamp(operation["started_at"]).replace(microsecond=0),
            "Observed run predates the operation")
    require(isinstance(jobs, list) and len(jobs) <= 1000 and len({j["id"] for j in jobs}) == len(jobs), "Incomplete or duplicate job inventory")
    for job in jobs:
        require(job.get("run_id") == run["id"] and job.get("run_attempt") == operation["attempt"]
                and job.get("head_sha") == state["candidate_sha"], "Job belongs to another source/attempt")
    return {"run": run, "jobs": jobs}


def observe(state: dict, operation: dict, client) -> dict:
    require(operation["action"] in manual.WORKFLOWS, "Operation has no workflow producer")
    row = dict(operation)
    pending = row["pending"]
    if row["run_id"] is None:
        workflow = manual.WORKFLOWS[row["action"]][0]
        before = pending.get("before", {}).get("run_ids", [])
        runs = client.list(f"/actions/workflows/{workflow}/runs?event=workflow_dispatch", "workflow_runs")
        matches = [r for r in runs if r["id"] not in before and r.get("head_sha") == state["candidate_sha"]
                   and r.get("head_branch") == "main" and hosted.timestamp(r["created_at"]) >= hosted.timestamp(row["started_at"]).replace(microsecond=0)]
        if len(matches) != 1:
            return {"status": "unresolved-dispatch" if not matches else "ambiguous-dispatch", "matches": len(matches), "retry_authority": False}
        row["run_id"] = matches[0]["id"]
    latest = client.get(f"/actions/runs/{row['run_id']}")
    run = latest if latest.get("run_attempt") == row["attempt"] else client.get(f"/actions/runs/{row['run_id']}/attempts/{row['attempt']}")
    jobs = client.list(f"/actions/runs/{row['run_id']}/attempts/{row['attempt']}/jobs", "jobs")
    bound = bind_observation(state, row, run, jobs)
    return {"status": "observed", **bound, "run_id": row["run_id"], "attempt": row["attempt"],
            "latest_attempt": latest.get("run_attempt"), "historical_attempt": latest.get("run_attempt") != row["attempt"]}


def _public_run(run: dict) -> dict:
    fields = ("id", "name", "head_sha", "head_branch", "path", "event", "status", "conclusion", "run_attempt",
              "check_suite_id", "created_at", "run_started_at", "updated_at", "html_url")
    return {k: run.get(k) for k in fields}


def _public_job(job: dict) -> dict:
    fields = ("id", "name", "run_id", "run_attempt", "head_sha", "status", "conclusion", "created_at", "started_at", "completed_at")
    row = {k: job.get(k) for k in fields}
    row["steps"] = [{k: s.get(k) for k in ("name", "status", "conclusion", "number", "started_at", "completed_at")} for s in job.get("steps", [])]
    return row


def timeline(store: manual.Store, *, client=None, retained: dict | None = None, verify_local: bool = False) -> dict:
    captured = snapshot(store)
    state = captured["state"]
    rows = operations(state, captured["events"])
    require(len(rows) <= MAX_OBSERVATIONS, "Session operation inventory exceeds reporting bound")
    for row in rows:
        evidence = None
        try:
            if retained is not None and row["operation_id"] in retained:
                evidence = bind_observation(state, row, **retained[row["operation_id"]])
                evidence.update(status="observed", observation_scope="retained-offline-records", run_id=row["run_id"], attempt=row["attempt"])
            elif client is not None and row["action"] in manual.WORKFLOWS:
                evidence = observe(state, row, client)
                evidence["observation_scope"] = "current-read-only-api"
            if evidence and evidence.get("status") == "observed":
                source = declaration(store.root, state["candidate_sha"], row["action"])
                row.update(run_id=evidence["run"]["id"], attempt=evidence["run"]["run_attempt"],
                           workflow={k: v for k, v in source.items() if k != "jobs"},
                           producers=producer_failures(evidence["jobs"], source["jobs"]))
                evidence["run"] = _public_run(evidence["run"])
                evidence["jobs"] = [_public_job(j) for j in evidence["jobs"]]
            row["observation"] = evidence or {"status": "not-observed", "retry_authority": False}
        except automation.APIError as exc:
            if exc.status not in {404, 502, 503, 504}:
                raise
            row["observation"] = {"status": "remote-observation-unavailable", "http_status": exc.status, "retry_authority": False}
        row["key"] = {"session_id": state["session_id"], "candidate_sha": state["candidate_sha"],
                      "operation_id": row["operation_id"], "action": row["action"], "run_id": row["run_id"], "attempt": row["attempt"]}
        # Keep only the fields needed to diagnose a recorded write. Environment,
        # arbitrary server payloads and command logs are not copied into packets.
        row["intent"] = {"started_at": row["started_at"], "outcome_unknown": bool(row["pending"].get("outcome_unknown")),
                         "response_recorded": row["pending"].get("response") is not None}
        if row.get("accepted_result"):
            result = row["accepted_result"]
            row["recorded_result"] = {k: result[k] for k in ("verified", "candidate_sha", "run_id", "attempt", "technical_decision", "upload", "refs", "url") if k in result}
        row.pop("pending", None)
        row.pop("accepted_result", None)
    public = state.get("phase") == "complete" and state.get("public_verification", {}).get("verified") is True
    return {"schema_version": SCHEMA, "session": {k: state[k] for k in ("session_id", "repository", "candidate_sha", "candidate_tree", "version", "phase", "revision", "created_at")},
            "snapshot": captured["inputs"], "warnings": captured["warnings"], "operations": rows,
            "events": [{k: r.get(k) for k in ("revision", "time", "event", "phase", "line", "sha256", "binding", "ahead_of_state")} for r in captured["events"]],
            "local_preparation": local_preparation(state, verify=verify_local),
            "completion": {"state_authority": "maintained-controller", "recorded_public_verification": public,
                           "superseded": state["phase"] == "superseded", "fresh_public_observation_performed": False},
            "publication_authority": False}


def packet(root: Path, output: Path, report: dict, operation_id: str) -> dict:
    rows = [r for r in report["operations"] if r["operation_id"] == operation_id]
    require(len(rows) == 1, "Choose one recorded operation for the diagnostic packet")
    row = rows[0]
    key = row["key"]
    identifier = hosted.sha256(manual.canonical(key))
    output = preflight._destination(root, output)
    require(not output.exists(), "Diagnostic output is occupied; retain previous packets")
    payload = {"schema_version": PACKET_SCHEMA, "key": key, "packet_id": identifier,
               "session": report["session"], "snapshot": report["snapshot"], "operation": row,
               "local_preparation": report["local_preparation"], "completion": report["completion"],
               "warnings": report["warnings"], "publication_authority": False}
    output.mkdir(parents=True)
    try:
        for name, value in (("diagnostic.json", payload), ("timeline.json", report)):
            with (output / name).open("x") as stream:
                json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
                stream.write("\n")
        manifest = {name: {"sha256": hosted.sha256(_bytes(output / name)), "bytes": (output / name).stat().st_size} for name in ("diagnostic.json", "timeline.json")}
        with (output / "manifest.json").open("x") as stream:
            json.dump({"schema_version": PACKET_SCHEMA, "key": key, "packet_id": identifier, "files": manifest}, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except BaseException:
        # Retain incomplete diagnostic output as a failed attempt; never clobber
        # a packet or copy command text out of it as executable recovery steps.
        raise
    return {"key": key, "packet_id": identifier, "path": str(output), "publication_authority": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("timeline", "packet"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--operation-id")
    parser.add_argument("--observe", action="store_true", help="Use only GET/list metadata reads; never advance or reconcile the controller")
    parser.add_argument("--verify-local", action="store_true", help="Verify retained receipt evidence without running stages")
    args = parser.parse_args(argv)
    try:
        root = manual.safe(args.root)
        store = manual.Store(root, root / args.work)
        client = None
        if args.observe:
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            if not token:
                token = subprocess.check_output(["gh", "auth", "token", "--hostname", "github.com"], text=True).strip()
            client = automation.GitHubClient(store.load()["repository"], token, write=False)
        report = timeline(store, client=client, verify_local=args.verify_local)
        if args.operation == "timeline":
            preflight.write_document(args.output, report, root=root)
            result = {"session": report["session"], "operations": len(report["operations"]), "output": str(args.output)}
        else:
            require(args.operation_id is not None, "An operation ID is required for a diagnostic packet")
            result = packet(root, args.output, report, args.operation_id)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
        print("Session reporting failed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
