"""Opt-in deterministic observations over the frozen owned Python corpus.

Every provider value is retained. Missing implementation or ordinary review
capabilities remain unavailable; an independent oracle is never substituted for
missing provider evidence. This driver does not launch a model or field trial.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from typing import Any

from tests.developer_value import runtime
from tests.developer_value.oracles import (
    apply_prose_mutation, apply_source_mutation, corpus_identity, owned_behavior,
    score_retrieval, source_observations, verify_corpus,
)

SCHEMA = "developer-value-evaluation/v1"


@contextmanager
def _cwd(path: Path):
    previous = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(previous)


def _error(error: Exception) -> dict[str, Any]:
    return {"type": type(error).__name__, "message": str(error),
            "code": getattr(error, "code", None), "details": getattr(error, "details", None)}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _task(api: Any, request: Mapping[str, Any], policy: Any = None) -> dict[str, Any]:
    kwargs = {"src_dir": "src", "wiki_dir": "wiki"}
    if policy is not None:
        kwargs["policy"] = policy
    result = api.build_task_context(request, **kwargs)
    payload = result.to_payload()
    validation = "not-applicable-error-result"
    if result.ok:
        validation_kwargs = {} if policy is None else {"policy": policy}
        checked = api.validate_task_context(result.rendered, request, **validation_kwargs)
        if checked != payload:
            raise ValueError("canonical validation changed the observed task result")
        validation = "passed"
    return {"ok": result.ok, "payload": payload, "rendered": result.rendered,
            "rendered_sha256": _sha(result.rendered.encode("utf-8")),
            "canonical_validation": validation}


def _session_reply(api: Any, reply: Any, request: Mapping[str, Any]) -> dict[str, Any]:
    context = None
    if reply.context is not None:
        payload = reply.context.to_payload()
        if reply.context.ok:
            api.validate_task_context(reply.context.rendered, request)
        context = {"payload": payload, "rendered": reply.context.rendered, "ok": reply.context.ok}
    return {"state": reply.state, "result_id": reply.result_id, "context": context,
            "delta": None if reply.delta is None else dict(reply.delta), "metadata": reply.metadata()}


def _inspection_concept(result: Mapping[str, Any] | None) -> dict[str, Any]:
    if not result:
        return {}
    selection = result.get("concept", {})
    selected = selection.get("concept") if isinstance(selection, Mapping) else None
    return dict(selected) if isinstance(selected, Mapping) else {}


def _selected_integrity_ready(result: Mapping[str, Any] | None, coordinate: str) -> bool | None:
    """A diagnostic object is not evidence of valid selected commitments."""
    if result is None:
        return None
    selection = result.get("concept", {})
    concept = _inspection_concept(result)
    if (not isinstance(selection, Mapping) or selection.get("found") is not True
            or selection.get("ambiguous") is True or concept.get("canonical_path") != coordinate):
        return False
    if (result.get("ok") is False or result.get("error") is not None
            or result.get("status") in {"unavailable", "unsupported", "degraded", "error", "rejected"}):
        return False
    coverage = result.get("coverage", {})
    if not isinstance(coverage, Mapping) or coverage.get("availability") != "ready":
        return False
    for component in ("concept", "graph", "sections"):
        payload = result.get(component)
        if not isinstance(payload, Mapping):
            return False
        knowledge = payload.get("knowledge", {})
        if not isinstance(knowledge, Mapping) or knowledge.get("availability") != "ready":
            return False
    return True


@dataclass
class _Case:
    api: Any
    spec: Mapping[str, Any]
    root: Path
    events: list[dict[str, Any]] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)

    def observe(self, step: Mapping[str, Any]) -> None:
        source_before = runtime.tree_hashes(self.root / "src")
        wiki_before = runtime.tree_hashes(self.root / "wiki")
        self.state["wiki_before_last_read"] = wiki_before
        stdout, stderr = io.StringIO(), io.StringIO()
        started = time.perf_counter()
        event: dict[str, Any] = {"step": dict(step), "outcome": "ok"}
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result, outcome = self.perform(step)
            event.update(result=result, outcome=outcome)
        except Exception as error:
            event.update(outcome="error", error=_error(error))
        event.update(seconds=time.perf_counter() - started, stdout=stdout.getvalue(), stderr=stderr.getvalue())
        read_action = step.get("action") in {
            "validate-protected-artifacts", "compare-protected-and-authored-bytes",
            "compare-all-wiki-bytes-with-before-read", "capture-source-and-semantic-prose-hashes",
            "inspect-generated-flow-overview", "compare-session-with-cold-result",
        }
        if "api" in step or "session" in step or "oracle" in step or read_action:
            event["read_integrity"] = {
                "source_before": source_before, "source_after": runtime.tree_hashes(self.root / "src"),
                "wiki_before": wiki_before, "wiki_after": runtime.tree_hashes(self.root / "wiki"),
            }
        self.events.append(event)

    def perform(self, step: Mapping[str, Any]) -> tuple[Any, str]:
        if "api" in step:
            name = step["api"]
            if name == "build_maintenance_queue" and step.get("fresh_process"):
                script = ('import json, os\nos.chdir(sys.argv[1])\n'
                          'print(json.dumps(api.build_maintenance_queue("src", "wiki", limit=100), sort_keys=True))\n')
                argv = runtime.provider_command(script, str(self.root))
                completed = subprocess.run(argv, cwd=self.root, capture_output=True, text=True, timeout=30)
                raw = {"argv": argv, "exit_code": completed.returncode,
                       "stdout": completed.stdout, "stderr": completed.stderr}
                if completed.returncode != 0:
                    return raw, "error"
                return {"fresh_process": raw, "payload": json.loads(completed.stdout)}, "ok"
            if name == "build_task_context":
                policy = self.api.WorkflowPolicy(**step["host_policy"]) if "host_policy" in step else None
                return _task(self.api, step["request"], policy), "ok"
            if name == "open_context_session":
                self.state["session"] = self.api.open_context_session(src_dir="src", wiki_dir="wiki")
                return {"opened": True, "request": step["request"]}, "ok"
            if name == "search_wiki":
                manifest = verify_corpus()
                requested = set(step["query_ids"])
                rows, observations = _queries(self.api, manifest, requested)
                self.state["query_observations"] = observations
                return {"queries": rows, "observed_query_ids": sorted(observations)}, "ok"
            function = getattr(self.api, name)
            result = function(*step.get("args", []), src_dir="src", wiki_dir="wiki", **step.get("kwargs", {}))
            return result, "ok"
        if "session" in step:
            kwargs = {}
            if "if_result_id" in step:
                kwargs["if_result_id"] = self.state.get("before_result_id")
                if kwargs["if_result_id"] is None:
                    raise ValueError("resumed read lacks its observed base result")
            reply = self.state["session"].read(step["request"], **kwargs)
            if step["stage"] == "before":
                self.state["before_result_id"] = reply.result_id
            value = _session_reply(self.api, reply, step["request"])
            self.state["session_after"] = value
            return value, "ok"
        if "oracle" in step:
            name = step["oracle"]
            if name == "owned_behavior":
                return owned_behavior(self.root / "src", step["control"]), "ok"
            if name == "source_observations":
                paths = step.get("source_paths", [step.get("source_path")])
                return {p: {"sha256": _sha((self.root / "src" / p).read_bytes()),
                            "observations": source_observations((self.root / "src" / p).read_text())}
                        for p in paths}, "ok"
            if name == "score_retrieval":
                return score_retrieval(verify_corpus(), self.state.get("query_observations", {})), "ok"
        action = step.get("action")
        if action == "apply-declared-source-mutation":
            path = self.root / "src" / self.spec["mutation"]["path"]
            before = path.read_bytes()
            apply_source_mutation(self.spec, self.root / "src")
            return {"path": path.relative_to(self.root).as_posix(), "before_sha256": _sha(before),
                    "after_sha256": _sha(path.read_bytes()), "before_text": before.decode("utf-8"),
                    "after_text": path.read_text()}, "ok"
        if action == "apply-declared-prose-mutation":
            path = apply_prose_mutation(self.spec, self.root / "wiki")
            value: dict[str, Any] = {"path": path.relative_to(self.root).as_posix(), "sha256": _sha(path.read_bytes()),
                                     "text": path.read_text()}
            if self.spec.get("prose_mutation", {}).get("refresh_before_read"):
                refresh = runtime.run_cli(list(verify_corpus()["preparation"]["sync_cli"]))
                value["declared_owning_refresh"] = refresh
                if refresh["exit_code"] != 0:
                    return value, "error"
            return value, "ok"
        if action == "apply-declared-artifact-mutation":
            mutation = self.spec["mutation"]
            path = self.root / "wiki" / mutation["path"]
            before = path.read_bytes()
            path.write_bytes((mutation["after"]).encode("utf-8"))
            return {"path": path.relative_to(self.root).as_posix(), "before_sha256": _sha(before),
                    "after_sha256": _sha(path.read_bytes()), "after_text": path.read_text()}, "ok"
        if action == "sync":
            previous = self.state.get("last_sync_tree")
            before = runtime.tree_hashes(self.root / "wiki")
            result = runtime.run_cli(list(step["argv"]))
            after = runtime.tree_hashes(self.root / "wiki")
            if result["exit_code"] == 0:
                self.state["last_sync_tree"] = after
            return {"cli": result, "wiki_hashes": after, "wiki_unchanged": before == after,
                    "same_as_previous_sync": None if previous is None else previous == after}, (
                        "ok" if result["exit_code"] == 0 else "error")
        if action == "validate-protected-artifacts":
            return self.api.inspect_concept(self.spec["selector"], src_dir="src", wiki_dir="wiki"), "ok"
        if action == "compare-protected-and-authored-bytes":
            return {"wiki_hashes": runtime.tree_hashes(self.root / "wiki")}, "ok"
        if action == "compare-all-wiki-bytes-with-before-read":
            after = runtime.tree_hashes(self.root / "wiki")
            return {"unchanged": self.state["wiki_before_last_read"] == after,
                    "before": self.state["wiki_before_last_read"], "after": after}, "ok"
        if action == "capture-source-and-semantic-prose-hashes":
            page = self.root / "wiki/entities/Batch.md"
            return {"source": runtime.tree_hashes(self.root / "src"), "page_sha256": _sha(page.read_bytes()),
                    "page_text": page.read_text(), "prose_binding_scope": "entire-page-bytes",
                    "actor": step["actor"]}, "ok"
        if action in {"probe-ordinary-review-acknowledgment", "repeat-fresh-acknowledgment"}:
            candidates = sorted(name for name in dir(self.api) if "acknowledg" in name.casefold())
            return {"state": "unavailable", "reason": self.spec["baseline_missing_capability"],
                    "provider_acknowledgment_names": candidates, "attempted_mutation": False,
                    "human_approval": "not-observed"}, "unavailable"
        if action == "compare-session-with-cold-result":
            cold = self.last("after", "build_task_context")
            reply = self.state.get("session_after", {})
            context = reply.get("context") or {}
            return {"cold_result_equivalent": cold is not None and context.get("rendered") == cold.get("rendered"),
                    "before_result_id": self.state.get("before_result_id"),
                    "after_result_id": reply.get("result_id")}, "ok"
        if action == "inspect-generated-flow-overview":
            return _overview(self.root, step), "ok"
        return {"state": "unavailable", "reason": "no-baseline-adapter-for-declared-step"}, "unavailable"

    def last(self, stage: str, api: str | None = None, *, action: str | None = None,
             argument: str | None = None, oracle: str | None = None) -> dict[str, Any] | None:
        for event in reversed(self.events):
            step = event["step"]
            if event["outcome"] != "ok" or step.get("stage") != stage:
                continue
            if api is not None and step.get("api") != api:
                continue
            if action is not None and step.get("action") != action:
                continue
            if oracle is not None and step.get("oracle") != oracle:
                continue
            if argument is not None and step.get("args") != [argument]:
                continue
            result = event.get("result")
            return result if isinstance(result, dict) else None
        return None


def _overview(root: Path, step: Mapping[str, Any]) -> dict[str, Any]:
    entry = step["entrypoint"]
    candidates = []
    for path in sorted((root / "wiki/flows").glob("*.md")):
        text = path.read_text()
        if f'**Entry point:** `{entry["symbol"]}`' in text and "../modules/cli.md" in text:
            candidates.append((path, text))
    if len(candidates) != 1:
        return {"state": "unavailable", "reason": "no-unique-generated-entrypoint-page",
                "candidates": [p.relative_to(root / "wiki").as_posix() for p, _ in candidates]}
    path, text = candidates[0]
    sequence = re.search(r"```mermaid\n(sequenceDiagram\n.*?)```", text, re.DOTALL)
    return {"path": path.relative_to(root / "wiki").as_posix(), "text": text,
            "sha256": _sha(text.encode("utf-8")), "sequence": None if sequence is None else sequence[1],
            "interaction_limit": step["display_interaction_limit"], "analysis_kind": "static"}


def _prepare_case(case: _Case) -> list[dict[str, Any]]:
    records = []
    preparation = case.spec["preparation"]
    if preparation.get("wiki_required") is False:
        original = runtime.tree_hashes(case.root / "wiki")
        (case.root / "wiki").rename(case.root / "retained-unused-wiki")
        records.append({"source_only_route": True, "requested_wiki_absent": True,
                        "retained_unused_wiki_hashes": original})
    for edit in preparation["semantic_edits"]:
        path = case.root / "wiki" / edit["wiki_path"]
        before = path.read_text()
        needle = "## " + edit["heading"] + "\n"
        if before.count(needle) != 1:
            raise ValueError("semantic preparation lacks its unique declared heading")
        path.write_bytes((before.replace(needle, needle + "\n" + edit["text"] + "\n", 1)).encode("utf-8"))
        records.append({"semantic_edit": dict(edit), "path": edit["wiki_path"],
                        "before_sha256": _sha(before.encode("utf-8")), "after_sha256": _sha(path.read_bytes())})
    if preparation["refresh_before_first_read"]:
        result = runtime.run_cli(list(verify_corpus()["preparation"]["sync_cli"]))
        records.append({"owning_refresh": result})
        if result["exit_code"] != 0:
            raise ValueError("declared semantic preparation refresh failed")
    if "adopt_storage" in preparation:
        argv = ["knowledge", "migrate", "--wiki-dir", "wiki", "--to", preparation["adopt_storage"],
                "--recovery-dir", "storage-recovery"]
        result = runtime.run_cli(argv)
        records.append({"explicit_adoption": {"argv": argv, **result}})
        if result["exit_code"] != 0:
            raise ValueError("explicit native storage adoption failed")
    return records


def _assess(case: _Case) -> list[dict[str, Any]]:
    spec, rows = case.spec, []

    def check(name: str, expected: Any, observed: Any, *, available: bool = True, reason: str | None = None):
        rows.append({"id": name, "expected": expected, "observed": observed,
                     "state": "unavailable" if not available else "passed" if observed == expected else "failed",
                     "reason": reason})

    reads = [event["read_integrity"] for event in case.events if "read_integrity" in event]
    check("read-only-integrity", True, bool(reads) and all(
        r["source_before"] == r["source_after"] and r["wiki_before"] == r["wiki_after"] for r in reads))
    operation = spec["operation"]
    if operation in {"implementation-change", "default-change", "formatting-change", "sibling-isolation", "docstring-change", "module-change"}:
        check("provider-implementation-comparison", spec["expected"]["after"].get("implementation", spec["expected"]["after"].get("selected_implementation")),
              None, available=False, reason="retained baseline has no supported versioned implementation-comparison adapter")
        if operation == "module-change":
            check("module-implementation-comparison", "changed", None, available=False,
                  reason="module executable evidence is absent from the retained provider contract")
        for stage in ("before", "after"):
            behavior = case.last(stage, oracle="owned_behavior")
            if behavior is not None:
                expected = spec["expected"][stage].get("owned_behavior", "").endswith("-passed")
                check(f"owned-behavior-{stage}", expected, behavior.get("oracle_passed"))
        if operation == "default-change":
            for stage, expected in (("before", "3"), ("after", "4")):
                task = case.last(stage, "build_task_context") or {}
                facts = task.get("payload", {}).get("facts", [])
                params = facts[0]["observation"]["contract"].get("params", []) if facts else []
                default = next((p.get("default") for p in params if p.get("name") == "limit"), None)
                check(f"source-default-{stage}", expected, default)
    if operation in {"callers", "uncertain-callers"}:
        result = case.last("before", "callers") or {}
        actual = {f'{row.get("file")}:{row.get("symbol")}' for row in result.get("callers", [])}
        for edge in spec["expected"]["before"].get("required_edges", []):
            check("required-caller:" + edge["from"], True, edge["from"] in actual)
        forbidden = [edge["from"] for edge in spec["expected"]["before"].get("forbidden_edges", []) if edge["from"] in actual]
        check("no-invented-negative-control-edge", [], forbidden)
        if operation == "uncertain-callers":
            check("located-receiver-uncertainty", spec["expected"]["before"]["uncertain_sites"], None,
                  available=False, reason="caller query does not expose per-site uncertain receivers")
    if operation == "source-only-context":
        before, after = case.last("before", "build_task_context") or {}, case.last("after", "build_task_context") or {}
        payload = before.get("payload", {})
        contract = next((r for r in payload.get("coverage", []) if r["requirement_id"] == "contract"), {})
        check("source-contract-present", True, contract.get("satisfied"))
        check("native-mode-off", "off", payload.get("storage", {}).get("status"))
        check("tiny-budget-rejected", False, after.get("ok"))
        check("tiny-budget-explicit-gap", "cannot-fit", after.get("payload", {}).get("error"))
        check("tiny-budget-no-context", "", after.get("rendered"))
    if operation in {"review-persistence", "stale-acknowledgment"}:
        check("ordinary-durable-review", "pending" if operation == "review-persistence" else "acknowledged", None,
              available=False, reason="ordinary durable pending/acknowledgment state is not supplied by the retained baseline")
        page = case.root / "wiki/entities/Batch.md"
        sentinel = spec["preparation"]["semantic_edits"][0]["text"].strip()
        check("authored-prose-preserved", True, sentinel in page.read_text())
        if operation == "review-persistence":
            restart = case.last("after-restart", "build_maintenance_queue")
            check("fresh-process-observed", True, bool(restart and restart.get("fresh_process", {}).get("exit_code") == 0))
            sync = case.last("second-sync", action="sync") or {}
            check("second-sync-idempotent", True, sync.get("same_as_previous_sync"))
    if operation == "corrupt-native":
        before = case.last("before", "build_task_context") or {}
        error = next((event for event in case.events if event["step"].get("api") == "build_task_context"
                      and event["step"]["stage"] == "after"), {})
        check("native-before-corruption", True, before.get("ok"))
        check("corrupt-required-read-rejected", "error", error.get("outcome"))
        unchanged = case.last("after", action="compare-all-wiki-bytes-with-before-read") or {}
        check("corrupt-read-no-repair", True, unchanged.get("unchanged"))
    if operation == "selected-context":
        before = (case.last("before", "build_task_context") or {}).get("payload", {})
        after = (case.last("after", "build_task_context") or {}).get("payload", {})
        check("selected-one-file", 1, before.get("work", {}).get("source_files"))
        check("selected-path", ["parts/part_005.py"], before.get("basis", {}).get("paths"))
        check("full-inventory-explicit-scope", "full-inventory", after.get("work", {}).get("scope"))
        check("full-inventory-file-count", 102, after.get("work", {}).get("source_files"))
        coverage = after.get("coverage", [])
        check("bounded-complete-graph-unsatisfied", False, coverage[0].get("satisfied") if coverage else None)
        check("bounded-graph-partial", "partial", coverage[0].get("state") if coverage else None)
    if operation == "resume-mutation":
        comparison = case.last("after", action="compare-session-with-cold-result") or {}
        before, after = comparison.get("before_result_id"), comparison.get("after_result_id")
        check("source-mutation-invalidates-identity", True, before is not None and after is not None and before != after)
        check("cold-session-equivalence", True, comparison.get("cold_result_equivalent"))
        reuse = case.state.get("session_after", {}).get("metadata", {}).get("reuse", {})
        check("stale-render-not-reused", False, reuse.get("rendering"))
    if operation == "maintenance-noop":
        before = case.last("before", action="sync") or {}
        after = case.last("second-sync", action="sync") or {}
        check("unchanged-sync-stable", True, before.get("wiki_unchanged"))
        check("second-sync-idempotent", True, after.get("same_as_previous_sync"))
        text = (case.root / "wiki" / spec["mutation"]["path"]).read_text()
        check("description-prose-preserved", True, spec["mutation"]["after"].strip() in text)
        integrity = _selected_integrity_ready(case.last("after", action="validate-protected-artifacts"), spec["selector"])
        check("protected-artifacts-validated", True, integrity, available=integrity is not None,
              reason="requires the selected concept and ready committed knowledge; diagnostics alone do not validate integrity")
    if operation == "flow-overview":
        overview = case.last("before", action="inspect-generated-flow-overview") or {}
        sequence = overview.get("sequence") or ""
        for stage in spec["expected"]["before"]["required_stages"]:
            check("overview-stage:" + stage, True, stage in sequence, available=bool(sequence))
        interactions = sum("->>" in line for line in sequence.splitlines())
        check("diagram-interaction-limit", True, interactions <= 30, available=bool(sequence))
        check("visible-failure-boundary-label", True, spec["expected"]["before"]["security_boundary"] in sequence,
              available=bool(sequence))
    if operation == "retrieval":
        scores = case.last("before", oracle="score_retrieval") or {}
        queried = set(spec["expected"]["before"]["query_ids"])
        for row in scores.get("queries", []):
            if row["query_id"] in queried:
                check("relevant-target:" + row["query_id"], len(row["expected_targets"]), row["recovered"])
    return rows


def observe_case(api: Any, spec: Mapping[str, Any], root: Path) -> dict[str, Any]:
    """Observe one already prepared owned workspace; restore cwd and close sessions."""
    case = _Case(api, spec, root)
    preparation, error = [], None
    with _cwd(root):
        try:
            preparation = _prepare_case(case)
            for step in spec["observation_steps"]:
                case.observe(step)
            checks = _assess(case)
        except Exception as failure:
            error = _error(failure)
            checks = []
        finally:
            if "session" in case.state:
                case.state["session"].close()
    states = Counter(check["state"] for check in checks)
    status = "error" if error else "failed" if states["failed"] else "unavailable" if states["unavailable"] else "passed"
    return {"id": spec["id"], "project": spec["project"], "operation": spec["operation"],
            "expected": spec["expected"], "disconfirming_outcomes": spec["disconfirming_outcomes"],
            "status": status, "preparation": preparation, "preparation_or_assessment_error": error,
            "events": case.events, "checks": checks, "check_counts": dict(states),
            "source_after": runtime.tree_hashes(root / "src"), "wiki_after": runtime.tree_hashes(root / "wiki"),
            "model_execution_established": False, "field_evidence_established": False}


def _queries(api: Any, manifest: Mapping[str, Any], ids: set[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows, observations = [], {}
    for query in manifest["retrieval"]["queries"]:
        if query["id"] not in ids:
            continue
        row = {"id": query["id"], "project": query["project"], "split": query["split"],
               "category": query["category"], "query": query["query"], "requested_limit": 100}
        try:
            result = api.search_wiki(query["query"], src_dir="src", wiki_dir="wiki", limit=100, mode="ranked")
            row.update(outcome="ok", result=result)
            if not isinstance(result.get("results"), list):
                raise ValueError("provider search response lacks a result list")
            # Reject malformed rows before treating this as an observed query.
            # The complete corpus denominator is still retained by final scoring.
            score_retrieval(manifest, {query["id"]: result["results"]})
            observations[query["id"]] = result["results"]
        except Exception as error:
            row.update(outcome="error", error=_error(error))
        rows.append(row)
    return rows, observations


def run(provider_root: Path, output: Path) -> dict[str, Any]:
    """Collect all twenty cases and forty questions using one verified provider."""
    manifest = verify_corpus()
    api = runtime.load_provider(provider_root)
    before_identity = runtime.provider_identity()
    output = output.absolute()
    if output.is_symlink() or output.resolve().is_relative_to(provider_root.resolve() / "src"):
        raise ValueError("evaluation output must not redirect writes or replace provider source")
    cases, query_rows, observations = [], [], {}
    retrieval_preparation: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="developer-value-evaluation-", dir=runtime.temporary_parent()) as temporary:
        work = Path(temporary).resolve()
        for spec in manifest["cases"]:
            root = work / spec["id"]
            stdout, stderr = io.StringIO(), io.StringIO()
            try:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    runtime.prepare_workspace(spec["project"], root)
                result = observe_case(api, spec, root)
            except Exception as error:
                result = {"id": spec["id"], "project": spec["project"], "status": "error",
                          "workspace_preparation_error": _error(error), "events": [], "checks": []}
            result["workspace_preparation_output"] = {"stdout": stdout.getvalue(), "stderr": stderr.getvalue()}
            cases.append(result)
        for project in manifest["projects"]:
            root = work / ("queries-" + project)
            ids = {q["id"] for q in manifest["retrieval"]["queries"] if q["project"] == project}
            stdout, stderr = io.StringIO(), io.StringIO()
            try:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    runtime.prepare_workspace(project, root)
                with _cwd(root):
                    rows, observed = _queries(api, manifest, ids)
                query_rows.extend(rows)
                observations.update(observed)
                retrieval_preparation[project] = {"outcome": "ok", "source_hashes": runtime.tree_hashes(root / "src"),
                                                  "wiki_hashes": runtime.tree_hashes(root / "wiki")}
            except Exception as error:
                query_rows.extend({"id": identity, "project": project, "outcome": "error",
                                   "workspace_preparation_error": _error(error)} for identity in sorted(ids))
                retrieval_preparation[project] = {"outcome": "error", "error": _error(error)}
            retrieval_preparation[project].update(stdout=stdout.getvalue(), stderr=stderr.getvalue())
    after_identity = runtime.provider_identity()
    scores = {str(split or "all"): score_retrieval(manifest, {identity: value for identity, value in observations.items()
              if split is None or identity in manifest["retrieval"]["development_ids" if split == "development" else "heldout_ids"]}, split=split)
              for split in (None, "development", "held-out")}
    report = {"schema_version": SCHEMA, "evidence_kind": "owned-synthetic-deterministic-provider-observations",
              "corpus_identity": corpus_identity(), "provider_before": before_identity, "provider_after": after_identity,
              "provider_unchanged": before_identity == after_identity, "cases": cases,
              "case_counts": dict(Counter(case["status"] for case in cases)), "queries": query_rows,
              "retrieval_preparation": retrieval_preparation,
              "query_counts": dict(Counter(query["outcome"] for query in query_rows)), "retrieval": scores,
              "frozen_target_aliases": manifest["retrieval"]["target_aliases"],
              "model_execution_established": False, "field_evidence_established": False,
              "answer_generation": "not-performed", "definitive_answer_claims": "unmeasured",
              "limitations": ["Deterministic owned observations establish no model productivity or field acceptance.",
                              "Unavailable future evidence is not replaced by independent oracle output.",
                              "Raw search is bounded to 100 pages; scoring uses the first five distinct frozen source owners.",
                              "Unmapped source aliases remain noise; unavailable answer claims remain unmeasured."]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes((json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run(args.provider_root, args.output)
    print(json.dumps({"output": str(args.output.absolute()), "case_counts": result["case_counts"],
                      "query_counts": result["query_counts"], "provider_unchanged": result["provider_unchanged"],
                      "model_execution_established": False, "field_evidence_established": False}, sort_keys=True))


if __name__ == "__main__":
    main()
