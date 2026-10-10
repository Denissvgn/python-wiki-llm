"""Deterministic case comparison; deliberately excludes held-out retrieval runs.

Use a fresh process per provider. The direct read transcript exhaustively reads
source and the identical authored input. It is an information/cost reference,
not a model task solver or an oracle substitute for native provider guarantees.
"""
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import re
from pathlib import Path
import tempfile
import time
from typing import Any

from tests.developer_value import evaluate, runtime
from tests.developer_value.fixtures import baseline_guides
from tests.developer_value.measure import harness_identity, save
from tests.developer_value.oracles import corpus_identity, verify_corpus

SCHEMA = "developer-value-case-comparison/v1"


def check(identity: str, expected: Any, observed: Any, *, available: bool = True) -> dict[str, Any]:
    return {"id": identity, "expected": expected, "observed": observed,
            "state": "unavailable" if not available else "passed" if observed == expected else "failed"}


def summarize(rows: list[dict[str, Any]], expected_ids: list[str]) -> dict[str, Any]:
    """Missing cases remain in the denominator; duplicate or unknown IDs fail."""
    if not expected_ids or len(set(expected_ids)) != len(expected_ids):
        raise ValueError("comparison schedule must have unique nonempty identities")
    if any(row["status"] not in {"passed", "failed", "error", "unavailable", "not-run"} for row in rows):
        raise ValueError("invalid comparison outcome")
    indexed = {row["id"]: row for row in rows}
    if len(indexed) != len(rows) or set(indexed) - set(expected_ids):
        raise ValueError("duplicate or unexpected comparison case")
    states = Counter(indexed[key]["status"] if key in indexed else "not-run" for key in expected_ids)
    return {"planned": len(expected_ids), "observed": len(rows), "states": dict(states),
            "passed_fraction": states["passed"] / len(expected_ids)}


def authored_input(spec: Mapping[str, Any]) -> dict[str, str]:
    content = {"guides/" + name: text for name, text in baseline_guides(spec["project"]).items()}
    for edit in spec["preparation"]["semantic_edits"]:
        content[edit["wiki_path"] + "#" + edit["heading"]] = edit["text"]
    return content


def direct_read(root: Path, authored: Mapping[str, str], stage: str) -> dict[str, Any]:
    """Read all owned source bytes and authored input, without executing source."""
    started = time.perf_counter_ns()
    source = {name: (root / "src" / name).read_text(encoding="utf-8")
              for name in runtime.tree_hashes(root / "src")}
    total = sum(len(text.encode()) for text in [*source.values(), *authored.values()])
    return {"stage": stage, "source": source, "authored": dict(authored),
            "source_hashes": runtime.tree_hashes(root / "src"),
            "authored_hashes": {name: evaluate._sha(text.encode()) for name, text in authored.items()},
            "bytes_read": total, "estimated_tokens": (total + 3) // 4,
            "wall_ns": time.perf_counter_ns() - started,
            "strategy": "predeclared-exhaustive-source-and-authored-read",
            "source_executed": False, "task_solved": "unmeasured",
            "native_guarantees": "unavailable", "model_usage": "unmeasured"}


class ComparisonCase(evaluate._Case):
    """Explicit current API adapter, leaving the original baseline driver intact."""

    def status(self) -> dict[str, Any]:
        return self.api.get_maintenance_status(src_dir="src", wiki_dir="wiki", limit=100)

    def target(self, status: Mapping[str, Any]) -> dict[str, Any]:
        return next(row for row in status["records"] if row["target"]["canonical_path"] == "entities/Batch.md")

    def perform(self, step: Mapping[str, Any]) -> tuple[Any, str]:
        action = step.get("action")
        if action == "capture-source-and-semantic-prose-hashes" and hasattr(self.api, "get_maintenance_status"):
            result, outcome = super().perform(step)
            status = self.status()
            self.state["ack_before"] = (status, self.target(status))
            result["maintenance_status"] = status
            return result, outcome
        if action in {"probe-ordinary-review-acknowledgment", "repeat-fresh-acknowledgment"} and hasattr(self.api, "acknowledge_maintenance"):
            basis = step.get("basis")
            current = self.status()
            row = self.target(current)
            if basis == "before-source-and-prose":
                status, row = self.state["ack_before"]
            elif basis == "current-source-and-old-prose":
                status, row = self.state["ack_after_source"]
            elif action == "repeat-fresh-acknowledgment":
                status, row = self.state["ack_fresh"]
            else:
                status = current
            try:
                result = self.api.acknowledge_maintenance(src_dir="src", wiki_dir="wiki",
                    record_id=row["record_id"], expected_state_hash=status["state_hash"],
                    expected_basis=row["expected_basis"], actor_kind="agent", actor_id="developer-value-evaluator",
                    recovery_dir="ack-recovery-" + step["stage"])
                value = {"state": "acknowledged", "response": result, "human_approval": False}
            except self.api.LlmWikiApiError as error:
                value = {"state": "rejected", "error": evaluate._error(error), "human_approval": False}
            if basis == "before-source-and-prose":
                # Capture a coherent current-source basis before the declared prose edit.
                synced = runtime.run_cli(list(verify_corpus()["preparation"]["sync_cli"]))
                if synced["exit_code"] != 0:
                    raise ValueError("acknowledgment preparation sync failed")
                refreshed = self.status()
                self.state["ack_after_source"] = (refreshed, self.target(refreshed))
                value["owning_refresh"] = synced
            if basis == "current-source-and-current-prose":
                self.state["ack_fresh"] = (status, row)
            return value, "ok"
        result, outcome = super().perform(step)
        if step.get("api") == "build_maintenance_queue" and hasattr(self.api, "get_maintenance_status"):
            if step.get("fresh_process"):
                script = ('import json,os\nos.chdir(sys.argv[1])\n'
                          'print(json.dumps(api.get_maintenance_status(src_dir="src",wiki_dir="wiki",limit=100)))\n')
                import subprocess
                argv = runtime.provider_command(script, str(self.root))
                completed = subprocess.run(argv, capture_output=True, text=True, timeout=30)
                result["maintenance_restart"] = {"exit_code": completed.returncode,
                    "stdout": completed.stdout, "stderr": completed.stderr,
                    "payload": json.loads(completed.stdout) if completed.returncode == 0 else None}
            else:
                result["maintenance_status"] = self.status()
        return result, outcome


def assess(case: ComparisonCase) -> list[dict[str, Any]]:
    rows = evaluate._assess(case)
    scheduled = case.events[:len(case.spec["observation_steps"])]
    complete = [event["step"] for event in scheduled] == list(case.spec["observation_steps"])
    unexpected = [event for event in scheduled if event["outcome"] == "error" and not (
        case.spec["operation"] == "corrupt-native" and event["step"].get("api") == "build_task_context"
        and event["step"]["stage"] == "after" and event.get("error", {}).get("type") == "InvalidRequestError"
        and event.get("error", {}).get("message") == "root: invalid knowledge root")]
    rows.append(check("scheduled-observations-complete", True, complete and not unexpected))
    unavailable = [event for event in scheduled if event["outcome"] == "unavailable"]
    rows.append(check("scheduled-capabilities-available", True, not unavailable, available=not unavailable))
    operation = case.spec["operation"]
    replacements: dict[str, dict[str, Any]] = {}
    if operation in {"implementation-change", "default-change", "formatting-change", "docstring-change", "module-change", "sibling-isolation"}:
        argument = "entities/Store.md" if operation == "module-change" else None
        if operation == "sibling-isolation":
            first = case.state.get("sibling_after", {}).get("first", {})
            second = case.state.get("sibling_after", {}).get("second", {})
            implementation = first.get("implementation", {})
            rows.append(check("second-occurrence-changed", "changed", second.get("implementation", {}).get("state"),
                              available=bool(second.get("implementation"))))
        else:
            concept = evaluate._inspection_concept(case.last("after", "inspect_concept", argument=argument))
            implementation = concept.get("implementation", {})
        expected = case.spec["expected"]["after"].get("implementation", case.spec["expected"]["after"].get("selected_implementation"))
        replacements["provider-implementation-comparison"] = check("provider-implementation-comparison", expected,
            implementation.get("state"), available=bool(implementation))
        if operation == "module-change":
            module = evaluate._inspection_concept(case.last("after", "inspect_concept", argument="modules/store.md"))
            replacements["module-implementation-comparison"] = check("module-implementation-comparison", "changed",
                module.get("implementation", {}).get("state"), available=bool(module.get("implementation")))
        if implementation:
            rows.append(check("runtime-behavior-not-inferred", True,
                "dependencies-and-runtime-behavior-not-evaluated" in implementation.get("limitations", [])))
        if operation == "implementation-change":
            rows.append(check("legacy-structural-meaning-preserved", "nonsemantic-source-change", concept.get("freshness", {}).get("state")))
        if operation == "docstring-change":
            rows.append(check("documentation-change-reported", True, implementation.get("documentation_changed"), available=bool(implementation)))
    if operation == "uncertain-callers":
        values = case.state.get("uncertain_callees")
        expected = case.spec["expected"]["before"]["uncertain_sites"]
        observed = None if values is None else [owner for owner, value in values.items() if any(
            row.get("symbol") == "cap" and row.get("kind") == "unresolved" and row.get("file") is None
            and row.get("line") is not None for row in value.get("callees", []))]
        replacements["located-receiver-uncertainty"] = check("located-receiver-uncertainty", sorted(expected),
            None if observed is None else sorted(observed), available=values is not None)
    if operation == "review-persistence" and hasattr(case.api, "get_maintenance_status"):
        for stage in ("after-edit", "after-sync", "after-restart"):
            result = case.last(stage, "build_maintenance_queue") or {}
            status = result.get("maintenance_status", result.get("maintenance_restart", {}).get("payload"))
            target = case.target(status) if status else {}
            rows.append(check("pending-review:" + stage, "pending", target.get("effective_status") or target.get("recorded_status")))
        replacements["ordinary-durable-review"] = check("ordinary-durable-review", True,
            all(row["state"] == "passed" for row in rows if row["id"].startswith("pending-review:")))
    if operation == "stale-acknowledgment" and hasattr(case.api, "acknowledge_maintenance"):
        for stage, expected in (("after", "rejected"), ("after-prose", "rejected"), ("fresh", "acknowledged"), ("repeat", "acknowledged")):
            action = "repeat-fresh-acknowledgment" if stage == "repeat" else "probe-ordinary-review-acknowledgment"
            result = case.last(stage, action=action) or {}
            rows.append(check("acknowledgment:" + stage, expected, result.get("state")))
            if expected == "rejected":
                rows.append(check("stale-basis-refusal:" + stage, "basis-changed", result.get("error", {}).get("details", {}).get("reason")))
            if expected == "acknowledged":
                response = result.get("response", {})
                rows.append(check("agent-authority:" + stage, {"kind": "agent", "actor_id": "developer-value-evaluator", "authority": "ordinary-maintenance"}, response.get("actor")))
                rows.append(check("no-governance-effect:" + stage, "none", response.get("governance_effect")))
                if stage == "repeat":
                    rows.append(check("repeat-idempotent", False, response.get("changed")))
        replacements["ordinary-durable-review"] = check("ordinary-durable-review", "acknowledged",
            (case.last("fresh", action="probe-ordinary-review-acknowledgment") or {}).get("state"))
    if operation in {"implementation-change", "module-change"}:
        queue = case.last("after", "build_maintenance_queue") or {}
        path = "entities/Batch.md" if operation == "implementation-change" else "modules/store.md"
        status = queue.get("maintenance_status", {})
        target = next((row for row in status.get("records", []) if row["target"]["canonical_path"] == path), {})
        rows.append(check("changed-prose-review-pending", "pending", target.get("effective_status"), available=bool(target)))
        rows.append(check("required-changed-owner-surfaced", True, any(row["path"] == path for row in queue.get("items", []))))
    if operation == "sibling-isolation":
        for name, occurrence in (("first", 1), ("second", 2)):
            value = case.state.get("sibling_after", {}).get(name, {}).get("implementation", {})
            rows.append(check("class-occurrence:" + name, {"source_path": "scope.py", "qualified_owner": "Repeated", "occurrence": occurrence},
                              value.get("coordinate"), available=bool(value)))
        # Independently check both requested method identities; executable
        # isolation is supplied by their containing exact class observations.
        for stage in ("before", "after"):
            facts = (case.last(stage, "build_task_context") or {}).get("payload", {}).get("facts", [])
            actual = sorted((row.get("observation", {}).get("symbol"), row.get("observation", {}).get("occurrence")) for row in facts)
            rows.append(check("method-occurrences:" + stage, [("Repeated.touch", 1), ("Repeated.touch", 2)], actual))
    if operation == "flow-overview":
        overview = case.last("before", action="inspect-generated-flow-overview") or {}
        text = overview.get("text", "")
        rows.append(check("flow-static-order-qualified", True, "not runtime execution order" in text))
        counts = re.search(r"shows (\d+) of (\d+) interactions; (\d+) omitted", text)
        rows.append(check("flow-omissions-counted", True, bool(counts and int(counts[1]) + int(counts[3]) == int(counts[2]))))
        rows.append(check("flow-source-links", True, all("../modules/" + module + ".md" in text for module in ("cli", "guards", "catalog", "rank", "search"))))
    supplemental = case.events[len(case.spec["observation_steps"]):]
    rows.append(check("supplemental-observations-complete", True, all(event["outcome"] == "ok" for event in supplemental)))
    return [replacements.get(row["id"], row) for row in rows]


def observe(api: Any, spec: Mapping[str, Any], root: Path) -> dict[str, Any]:
    case = ComparisonCase(api, spec, root)
    authored = authored_input(spec)
    reads, preparation, error, rows = [], [], None, []
    with evaluate._cwd(root):
        try:
            preparation = evaluate._prepare_case(case)
            reads.append(direct_read(root, authored, "before"))
            if spec["operation"] in {"review-persistence", "stale-acknowledgment"} and hasattr(api, "adopt_maintenance"):
                preparation.append({"explicit_maintenance_adoption": api.adopt_maintenance(src_dir="src", wiki_dir="wiki", recovery_dir="adopt-recovery")})
            for step in spec["observation_steps"]:
                case.observe(step)
                if step.get("action") in {"apply-declared-source-mutation", "apply-declared-prose-mutation"}:
                    if step["action"] == "apply-declared-prose-mutation":
                        mutation = spec.get("prose_mutation", spec.get("mutation", {}))
                        authored = {**authored, mutation["path"] + "#Description-insertion": mutation["after"]}
                    reads.append(direct_read(root, authored, step["stage"]))
            if spec["operation"] == "sibling-isolation":
                case.state["sibling_after"] = {}
                for name, path in (("first", "entities/Repeated.md"), ("second", "entities/Repeated_2.md")):
                    case.observe({"stage": "supplemental", "api": "inspect_concept", "args": [path], "kwargs": {"live": True}})
                    case.state["sibling_after"][name] = evaluate._inspection_concept(case.last("supplemental", "inspect_concept", argument=path))
            if spec["operation"] == "uncertain-callers" and hasattr(api, "callees"):
                case.state["uncertain_callees"] = {}
                for owner in spec["expected"]["before"]["uncertain_sites"]:
                    case.observe({"stage": "supplemental", "api": "callees", "args": [owner], "kwargs": {"limit": 100, "read_only": True}})
                    case.state["uncertain_callees"][owner] = case.last("supplemental", "callees", argument=owner) or {}
            rows = assess(case)
        except Exception as failure:
            error = evaluate._error(failure)
        finally:
            if "session" in case.state:
                case.state["session"].close()
    counts = Counter(row["state"] for row in rows)
    status = "error" if error else "failed" if counts["failed"] else "unavailable" if counts["unavailable"] else "passed"
    return {"id": spec["id"], "operation": spec["operation"], "status": status,
            "preparation": preparation, "error": error, "checks": rows, "events": case.events,
            "supplemental_provider_observations": {key: value for key, value in case.state.items() if key in {"sibling_after", "uncertain_callees"}},
            "direct_source": {"status": "observed" if reads else "not-run", "reads": reads,
                "required_provider_behavior": "unavailable", "accepted_task_quality": "unmeasured"}}


def run(provider_root: Path, output: Path) -> dict[str, Any]:
    if output.is_symlink() or any(parent.is_symlink() for parent in output.parents) or output.resolve().is_relative_to(provider_root.resolve() / "src"):
        raise ValueError("comparison output must not redirect writes or replace provider source")
    manifest = verify_corpus()
    # Only G05 development questions are admitted here. Never call evaluate.run.
    requested = {identity for spec in manifest["cases"] for step in spec["observation_steps"] for identity in step.get("query_ids", [])}
    if requested - set(manifest["retrieval"]["development_ids"]):
        raise ValueError("comparison case would replay held-out retrieval")
    harness_before = {**harness_identity(), "compare_cases.py": evaluate._sha(Path(__file__).read_bytes()), "evaluate.py": evaluate._sha(Path(evaluate.__file__).read_bytes())}
    api = runtime.load_provider(provider_root)
    before = runtime.provider_identity()
    rows = []
    with tempfile.TemporaryDirectory(prefix="developer-value-comparison-", dir=runtime.temporary_parent()) as temporary:
        for spec in manifest["cases"]:
            root = Path(temporary) / spec["id"]
            stdout, stderr = io.StringIO(), io.StringIO()
            try:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    runtime.prepare_workspace(spec["project"], root)
                row = observe(api, spec, root)
            except Exception as error:
                row = {"id": spec["id"], "status": "error", "error": evaluate._error(error), "checks": [], "events": [],
                       "direct_source": {"status": "not-run", "reads": []}}
            row["workspace_output"] = {"stdout": stdout.getvalue(), "stderr": stderr.getvalue()}
            rows.append(row)
            save(output.parent / (output.stem + "-cases") / (spec["id"] + ".json"), row)
    after = runtime.provider_identity()
    harness_after = {**harness_identity(), "compare_cases.py": evaluate._sha(Path(__file__).read_bytes()), "evaluate.py": evaluate._sha(Path(evaluate.__file__).read_bytes())}
    result = {"schema_version": SCHEMA, "corpus_identity": corpus_identity(), "provider_before": before,
              "provider_after": after, "provider_unchanged": before == after, "cases": rows,
              "harness_before": harness_before, "harness_after": harness_after, "harness_unchanged": harness_before == harness_after,
              "summary": summarize(rows, [spec["id"] for spec in manifest["cases"]]),
              "guide_content_treatment": "excluded-identical-frozen-authored-input",
              "heldout_retrieval_replayed": False, "development_query_ids": sorted(requested),
              "model_productivity": "unmeasured", "field_acceptance": "unmeasured",
              "direct_source_scope": "raw-exhaustive-information-read; no provider-specific capabilities or task-quality inference"}
    save(output, result)
    return result


def compare_reports(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Join complete case schedules and verify actual source/authored parity."""
    expected = [case["id"] for case in verify_corpus()["cases"]]
    for report in (baseline, candidate):
        if (report.get("schema_version") != SCHEMA or report.get("corpus_identity") != corpus_identity()
                or report.get("provider_unchanged") is not True or report.get("harness_unchanged") is not True
                or report.get("heldout_retrieval_replayed") is not False):
            raise ValueError("comparison basis changed or replayed held-out retrieval")
    if baseline["harness_before"] != candidate["harness_before"]:
        raise ValueError("comparison harnesses differ")
    arms = [{row["id"]: row for row in report["cases"]} for report in (baseline, candidate)]
    summaries = {name: summarize(report["cases"], expected) for name, report in (("baseline", baseline), ("candidate", candidate))}
    rows = []
    for identity in expected:
        pair = [arm.get(identity) for arm in arms]
        reads = [None if value is None else value.get("direct_source", {}).get("reads", []) for value in pair]
        available = all(value for value in reads)
        if available:
            first, second = reads
            assert first is not None and second is not None
            # Compare every recorded source/prose stage, not provider-generated pages.
            signatures = [[(value["stage"], value["source_hashes"], value["authored_hashes"]) for value in arm] for arm in (first, second)]
            if signatures[0] != signatures[1]:
                raise ValueError("source/authored information differs for " + identity)
        rows.append({"id": identity, "baseline": "not-run" if pair[0] is None else pair[0]["status"],
                     "candidate": "not-run" if pair[1] is None else pair[1]["status"],
                     "information_parity": "verified" if available else "unavailable",
                     "direct_source": "read-reference-only" if available else "not-run"})
    return {"schema_version": "developer-value-comparative-summary/v1", "summaries": summaries, "cases": rows,
            "information_parity_verified": sum(row["information_parity"] == "verified" for row in rows),
            "direct_source_provider_success_fraction": "unavailable",
            "guide_content_treatment": "separate", "model_productivity": "unmeasured", "field_acceptance": "unmeasured"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.provider_root.resolve(), args.output.absolute())
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
