"""Bounded task-context composition over existing capture, query and v3 owners."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from ..config import DEFAULT_WIKI_DIR, validate_path, validate_source_root
from . import context_packet as packets, context_service as context
from .change_selection import select_changes
from .context_budget import _accounted_render, fit_payload, validate_request as budget_request
from .documentation_query_builder import build_documentation_query_service_from_view, normalize_supplied_paths
from .knowledge_consumption import load_knowledge_read_view
from .knowledge_loader import KnowledgeStateLoadError
from .knowledge_envelope import hash_source_snapshot
from .io import first_unsafe_path_component
from .search_service import SEARCH_KINDS, page_records, search_records
from .source_snapshot import SourceSnapshotError
from .task_contract import TASK_RESULT_SCHEMA, TaskContext, normalize_task_request
from .task_evidence import coverage, declaration_records, match_declarations, observe_requirement, query_service
from .token_counting import EstimatedCounter, TokenCounter
from .wiki_surface_index import evaluate_surface_index
from .workflow_profile import (
    WorkflowPolicy, WorkflowProfile, WorkflowRequestError, canonical_json, content_id,
)

_LIVE_FACETS = frozenset({"source-contract", "callers", "callees", "entrypoint", "dependency"})
_NATIVE_FACETS = frozenset({"concept", "semantic-section", "typed-relationships"})
_LIMITATIONS = [
    "Coverage describes emitted observations under their qualifications; semantic adequacy and task correctness are not evaluated.",
    "Static graph observations do not prove the absence of runtime callers or effects.",
    "Source selection controls and package/infrastructure inputs may be inspected alongside selected language files.",
    "Byte ceilings bound a capture's inputs; validation re-reads and parser work are separate costs.",
    "Unsaved editor buffers are not on-disk evidence. Follow-up requests are inert proposals.",
]


class TaskCancelledError(RuntimeError):
    """The trusted host cancelled before a task result was published."""


@dataclass
class TaskRead:
    """Private ownership retained only by an explicit bounded session."""

    normalized: dict[str, Any]
    profile: WorkflowProfile
    captured: packets.CapturedContextRead | None
    wiki_root: Path
    wiki_anchor: str
    result: TaskContext
    wiki_integrity: Mapping[str, tuple[int, ...]] | None = None


def _counter(settings, supplied):
    if supplied is None:
        if settings["budget_mode"] == "exact":
            raise WorkflowRequestError("counter_id", "exact mode requires a trusted host counter")
        supplied = EstimatedCounter()
    if not isinstance(supplied.identity, str) or not supplied.identity:
        raise WorkflowRequestError("counter_id", "trusted counter identity is missing")
    if settings["budget_mode"] == "exact" and not supplied.exact:
        raise WorkflowRequestError("budget_mode", "an estimated counter cannot satisfy exact mode")
    if settings["counter_id"] not in (None, supplied.identity):
        raise WorkflowRequestError("counter_id", "does not match the trusted counter")
    return supplied


def _cancel(check):
    if check is not None and check():
        raise TaskCancelledError("Task context cancelled before publication")


def _paths(request):
    selected = {anchor["value"] for anchor in request["anchors"] if anchor["kind"] == "source"}
    for anchor in request["anchors"]:
        if anchor["kind"] == "symbol" and ":" in anchor["value"]:
            selected.add(anchor["value"].split(":", 1)[0])
    for requirement in request["requirements"]:
        if requirement["facet"] == "dependency":
            selected.add(requirement["selector"])
        elif requirement["facet"] in _LIVE_FACETS and ":" in requirement["selector"]:
            selected.add(requirement["selector"].split(":", 1)[0])
    return set(normalize_supplied_paths(sorted(selected)))


def plan_source_read(request, settings, source_root):
    paths = _paths(request)
    changes = select_changes(source_root, request["changes"]) if request["changes"] is not None else None
    if changes is not None:
        paths.update(normalize_supplied_paths(changes["paths"]))
    if len(paths) > settings["max_files"]:
        raise WorkflowRequestError("max_files", "selectors exceed the host/profile limit")
    live_required = any(item["facet"] in _LIVE_FACETS for item in request["requirements"])
    needs_broad = live_required and (not paths or any(item["facet"] == "callers" and
                     item["criterion"] == "complete" for item in request["requirements"]))
    full = settings["read_scope"] == "full-inventory" and needs_broad
    live = settings["read_scope"] != "snapshot" and (bool(paths) or full)
    scope = "full-inventory" if full else "selected" if live else "snapshot"
    for path in paths:
        if first_unsafe_path_component(source_root / path) is not None:
            raise WorkflowRequestError("anchors", "source selectors cannot follow symlinks or reparse points")
    return paths, changes, live, scope


def _followups(requirements, observed, settings):
    suggestions, seen = [], set()
    for requirement in requirements:
        state, _, reason = observed[requirement["id"]]
        if state == "present":
            continue
        identity = (requirement["facet"], requirement["selector"], reason)
        if identity in seen or len(suggestions) >= settings["max_followups"]:
            continue
        seen.add(identity)
        suggestions.append({"requirement_id": requirement["id"], "facet": requirement["facet"],
                            "selector": requirement["selector"], "reason": reason,
                            "operation": "host-verification" if requirement["facet"] == "behavior" else "task-context",
                            "needed_scope": "host-execution" if requirement["facet"] == "behavior" else
                                "full-inventory" if reason == "broader-scope-required" else settings["read_scope"],
                            "requires_host_authorization": True, "automatic": False,
                            "remaining_read_rounds": 0})
    return suggestions


def _result_body(request, profile, basis, plan, anchors, work, observations, facts, packet, accounting):
    requirement_coverage = coverage(request["requirements"], observations, facts)
    if not request["requirements"]:
        state = "discovery" if anchors else "empty"
    elif all(item["satisfied"] for item in requirement_coverage):
        state = "covered"
    else:
        state = "incomplete"
    effective_observations = dict(observations)
    for item in requirement_coverage:
        if item["state"] == "omitted":
            effective_observations[item["requirement_id"]] = ("omitted", None, item["reason"])
    body = {"schema_version": TASK_RESULT_SCHEMA, "ok": True, "state": state,
            "task_id": request["task_id"], "task_ref": request["task_ref"],
            "request_id": request["request_id"], "profile_id": profile.profile_id,
            "profile": profile.to_payload(), "basis": basis, "plan": plan, "anchors": anchors,
            "facts": facts, "coverage": requirement_coverage,
            "omissions": [item for item in requirement_coverage if not item["satisfied"]],
            "followups": _followups(request["requirements"], effective_observations, profile.settings),
            "work": work, "packet": packet, "accounting": dict(accounting),
            "limitations": list(_LIMITATIONS)}
    body["result_id"] = content_id(TASK_RESULT_SCHEMA, body)
    return body


def _empty_render(request, profile, counter, basis, plan, anchors, work, observations, facts):
    settings = profile.settings
    accounting = {"budget_tokens": settings["budget_tokens"], "used_tokens": 0,
                  "counter_id": counter.identity, "mode": settings["budget_mode"],
                  "exact_compliance": settings["budget_mode"] == "exact" and bool(counter.exact),
                  "usage_kind": "upper-bound-including-accounting",
                  "scope": "emitted-text-without-host-chat-framing"}
    while True:
        def render(value):
            return canonical_json(_result_body(request, profile, basis, plan, anchors, work,
                                              observations, facts, None, value)).decode("utf-8")
        rendered = _accounted_render(render, accounting, counter)
        if accounting["used_tokens"] <= settings["budget_tokens"]:
            return TaskContext(True, rendered, accounting)
        if not facts:
            return TaskContext(False, "", {**accounting, "exact_compliance": False}, "cannot-fit")
        facts.pop()


def build_task_read(
    request: Mapping[str, Any], *, src_dir: str = ".", wiki_dir: str = DEFAULT_WIKI_DIR,
    profile: WorkflowProfile | Mapping[str, Any] | None = None,
    policy: WorkflowPolicy | None = None, counter: TokenCounter | None = None,
    allow_external_src: bool = False, source_selection: str | Path | None = None,
    helper_cache_dir: str | None = None, cancelled: Callable[[], bool] | None = None,
    _reused_capture: packets.CapturedContextRead | None = None,
) -> TaskRead:
    normalized, effective = normalize_task_request(request, profile=profile, policy=policy)
    settings = effective.settings
    counter = _counter(settings, counter)
    if cancelled is not None and not callable(cancelled):
        raise WorkflowRequestError("cancelled", "must be a trusted host callback")
    _cancel(cancelled)
    source_root = validate_source_root(src_dir, "--src-dir", allow_external=allow_external_src)
    wiki_root = validate_path(wiki_dir, "--wiki-dir")
    last_mutation = None
    for attempt in range(settings["max_retries"] + 1):
        _cancel(cancelled)
        try:
            return _read_once(normalized, effective, counter, source_root, wiki_root,
                              allow_external_src, source_selection, helper_cache_dir, cancelled, attempt,
                              _reused_capture if attempt == 0 else None)
        except packets.ContextPacketSourceMutationError as exc:
            last_mutation = exc
    assert last_mutation is not None
    raise last_mutation


@packets._guarded_capture
def _read_once(request, profile, counter, source_root, wiki_root, allow_external,
               source_selection, helper_cache, cancelled, attempt, reused_capture=None):
    settings = profile.settings
    wiki_integrity = {}
    wiki_anchor = packets._wiki_anchor(wiki_root, reject_all_symlinks=True,
        max_bytes=settings["max_wiki_bytes"], integrity_out=wiki_integrity, guard_windows=True)
    paths, selected_changes, live, scope = plan_source_read(request, settings, source_root)
    anchors = [{**anchor, "reason": "explicit-caller-selection"} for anchor in request["anchors"]]
    # Discovery reads wiki text only, before deciding whether any source read is useful.
    if not anchors and request["changes"] is None and not request["requirements"] and request["text"].strip():
        ranked = search_records(page_records(wiki_root, set(SEARCH_KINDS)), request["text"][:4096],
                                limit=min(20, settings["max_graph_items"]), mode="ranked")
        anchors = [{"kind": "wiki", "value": hit["path"], "reason": "lexical-candidate",
                    "resolved": False, "ranking_reasons": hit["reasons"], "corpus_id": ranked["corpus_id"]}
                   for hit in ranked["results"]]
    captured = None
    service = None
    evidence_capture = None
    records = []
    unavailable = None
    work = {"captures": 0, "source_files": 0, "source_bytes": 0, "queries": 0,
            "capture_retries": attempt, "scope": scope,
            "source_byte_measure": "unique-captured-inputs; excludes parser and validation rereads"}
    try:
        if live:
            captured = reused_capture or packets.capture_context_read(
                str(source_root), str(wiki_root), allow_external_src=allow_external,
                read_only=True, source_selection=source_selection, allow_selection_mismatch=True,
                strict_wiki_symlinks=True, helper_cache_dir=helper_cache,
                only_files=None if scope == "full-inventory" else sorted(paths), respect_ignores=True,
                max_source_files=settings["max_files"], max_source_bytes=settings["max_source_bytes"],
                max_wiki_bytes=settings["max_wiki_bytes"],
            )
            if captured.wiki_anchor != wiki_anchor:
                raise packets.ContextPacketSourceMutationError("wiki")
            if selected_changes is not None:
                bound_changes = select_changes(source_root, request["changes"], snapshot=captured.source_snapshot)
                if bound_changes["request"] != selected_changes["request"]:
                    raise packets.ContextPacketSourceMutationError("changes")
                captured = replace(captured, changed_files=tuple(bound_changes["paths"]),
                                   explicit_changes=True, change_selection=bound_changes)
            service = query_service(captured, settings["max_graph_items"])
            records = declaration_records(captured.inventory)
            evidence_capture = captured
            work.update(captures=1, source_files=len(captured.source_snapshot.captured_content_hashes),
                        source_bytes=sum(item.size for item in captured.source_snapshot.captured_file_integrity.values()))
        elif settings["knowledge_mode"] == "required" or any(item["facet"] in _NATIVE_FACETS for item in request["requirements"]) or any(a["kind"] in {"concept", "wiki"} for a in anchors):
            view = load_knowledge_read_view(wiki_root, snapshot_only=True, include_machine_verification=True)
            if settings["knowledge_mode"] == "required" and view.availability.value != "ready":
                raise context.KnowledgeRequiredUnavailableError(
                    availability=view.availability.value, reason=view.reason_code,
                    fallback_evidence=[], recovery_command="llm-wiki sync")
            surface = evaluate_surface_index(wiki_root, {})
            service = build_documentation_query_service_from_view(wiki_root=wiki_root,
                        knowledge_view=view, limit=settings["max_graph_items"], surface_index=view.surface)
            evidence_capture = SimpleNamespace(surface_evaluation=surface, wiki_anchor=wiki_anchor,
                                               source_snapshot=None)
    except (SourceSnapshotError, packets.ContextPacketUnavailableError) as exc:
        unavailable = "work-limit-exceeded" if getattr(exc, "field", "").startswith("max_") else "source-capability-unavailable"
    except KnowledgeStateLoadError:
        if settings["knowledge_mode"] == "required":
            raise context.KnowledgeRequiredUnavailableError(availability="unavailable",
                reason="native-artifact-unavailable-or-invalid", fallback_evidence=[], recovery_command="llm-wiki sync") from None
        unavailable = "native-artifact-unavailable-or-invalid"
    except context.ProtocolRequestError as exc:
        if exc.field != "src_dir":
            raise
        unavailable = "source-capability-unavailable"
    _cancel(cancelled)
    observations, plan, queried = {}, [], {}
    for requirement in request["requirements"]:
        facet, selector = requirement["facet"], requirement["selector"]
        operation = {"facet": facet, "selector": selector, "scope": scope,
                     "reason": "explicit-evidence-requirement", "executed": False}
        key = (facet, selector, requirement["criterion"])
        if unavailable:
            observation = ("unavailable", None, unavailable)
        elif facet in _LIVE_FACETS and not live:
            observation = ("omitted", None, "broader-scope-required")
        elif facet in _NATIVE_FACETS and settings["knowledge_mode"] == "off":
            observation = ("unsupported", None, "native-mode-is-off")
        elif key in queried:
            observation = queried[key]
        elif len(queried) >= settings["max_read_rounds"]:
            observation = ("omitted", None, "read-round-limit")
        elif facet == "behavior":
            observation = ("unsupported", None, "host-behavioral-verification-required")
        else:
            _cancel(cancelled)
            observation = observe_requirement(evidence_capture, service, records, requirement,
                            scope=scope, limit=settings["max_graph_items"])
            queried[key] = observation
            operation["executed"] = True
        observations[requirement["id"]] = observation
        plan.append(operation)
        if observation[0] == "ambiguous" and facet == "source-contract":
            candidates = match_declarations(records, selector)
            anchors.extend({"kind": "symbol", "value": item["selector"], "reason": "ambiguous-exact-selection",
                            "resolved": True, "path": item["path"], "line": item["line"]}
                           for item in candidates[:settings["max_graph_items"]])
    required_facts = {fact["fact_id"]: fact for _, fact, _ in observations.values() if fact}
    optional_facts = {}
    recipes = {"orientation": ("source-contract",), "bug-diagnosis": ("source-contract", "callees", "callers"),
               "contract-change": ("source-contract", "callers"), "refactor": ("source-contract", "dependency")}
    optional_reads = []
    for anchor in anchors:
        if anchor.get("reason") == "ambiguous-exact-selection":
            continue  # The caller must choose among ambiguous declarations.
        if anchor["kind"] == "symbol":
            optional_reads.extend((facet, anchor["value"].split(":", 1)[0] if facet == "dependency" else anchor["value"])
                                  for facet in recipes[request["kind"]] if facet != "dependency" or ":" in anchor["value"])
        elif anchor["kind"] == "source":
            optional_reads.extend(("source-contract", item["selector"]) for item in records if item["path"] == anchor["value"])
        else:
            optional_reads.append(("concept", anchor["value"]))
    for facet, selector in optional_reads:
        key = (facet, selector, "present")
        if key in queried or unavailable or service is None or len(queried) >= settings["max_read_rounds"]:
            continue
        if (facet in _LIVE_FACETS and not live) or (facet in _NATIVE_FACETS and settings["knowledge_mode"] == "off"):
            continue
        observation = observe_requirement(evidence_capture, service, records,
            {"facet": facet, "selector": selector, "criterion": "present"}, scope=scope, limit=settings["max_graph_items"])
        queried[key] = observation
        plan.append({"facet": facet, "selector": selector, "scope": scope,
                     "reason": "task-kind:" + request["kind"], "executed": True})
        if observation[1] is not None:
            optional_facts[observation[1]["fact_id"]] = observation[1]
    facts = sorted({**optional_facts, **required_facts}.values(),
                   key=lambda item: (item["fact_id"] not in required_facts, item["fact_id"]))
    work["queries"] = len(queried)
    basis = {"source": captured.source_anchor if captured else None, "wiki": wiki_anchor,
             "consumed_source": hash_source_snapshot(captured.source_snapshot.to_consumed_inputs()) if captured else None,
             "scope": scope, "paths": sorted(paths), "changes": selected_changes,
             "source_selection_compatible": not captured.basis_incompatible if captured else None,
             "native_availability_required": settings["knowledge_mode"] == "required"}
    basis["capture_id"] = content_id("llm-wiki-task-basis/v1", basis)
    if captured is not None:
        request_v3 = budget_request({"protocol": "llm-wiki-context/v3", "format": "packet",
            "budget_tokens": settings["budget_tokens"], "budget_mode": settings["budget_mode"],
            "counter_id": settings["counter_id"], "focus": ["all"],
            "knowledge_mode": settings["knowledge_mode"], "prefer_fresh": settings["prefer_fresh"]})
        legacy = {key: value for key, value in request_v3.items() if key in context._V2_REQUEST_KEYS}
        legacy.update(protocol=context.KNOWLEDGE_PROTOCOL_VERSION, format="json", budget_tokens=2**63 - 1)
        freshness_ranks = {}
        payload, warnings = packets.build_context_from_captured_read(captured, legacy,
                                                                   freshness_ranking_out=freshness_ranks)
        packet_cache = {}

        def packet_renderer(selected_request, response):
            key = content_id("task-packet-render/v1", {"request": selected_request, "response": response})
            if key not in packet_cache:
                packet_cache.clear()
                packet_cache[key] = packets.packet_from_captured_response(captured, selected_request, response).to_payload()
            return packet_cache[key]

        def envelope_renderer(value):
            return canonical_json(_result_body(request, profile, basis, plan, anchors, work,
                observations, facts, value["packet"], value["accounting"])).decode("utf-8")

        while True:
            _cancel(cancelled)
            result = fit_payload(payload, request_v3, warnings, counter,
                                 packet_renderer=packet_renderer, envelope_renderer=envelope_renderer,
                                 freshness_rank_by_source=freshness_ranks)
            if result.ok or not facts:
                output = TaskContext(result.ok, result.rendered, result.accounting, result.error)
                break
            facts.pop()
    else:
        output = _empty_render(request, profile, counter, basis, plan, anchors, work, observations, facts)
    _cancel(cancelled)
    if captured is not None:
        packets._assert_source_unchanged(captured.source_snapshot, captured.source_anchor)
        packets._assert_selection_unchanged(captured)
    if selected_changes is not None:
        current = select_changes(source_root, request["changes"])
        if current != selected_changes:
            raise packets.ContextPacketSourceMutationError("changes")
    packets._assert_wiki_unchanged(wiki_root, wiki_anchor, reject_all_symlinks=True,
                                  max_bytes=settings["max_wiki_bytes"], expected_integrity=wiki_integrity)
    return TaskRead(request, profile, captured, wiki_root, wiki_anchor, output, wiki_integrity)


def build_task_context(request: Mapping[str, Any], **kwargs) -> TaskContext:
    return build_task_read(request, **kwargs).result


def reconcile_task_context(rendered: str, request: Mapping[str, Any], **options) -> dict[str, Any]:
    validation_options = {key: options[key] for key in ("profile", "policy", "counter") if key in options}
    previous = validate_task_context(rendered, request, **validation_options)
    current = build_task_read(request, **options).result
    payload = current.to_payload()
    packet_report = None
    if current.ok and previous["packet"] is not None and payload["packet"] is not None:
        packet_report = packets._reconcile_packet_views(previous["packet"], payload["packet"]).to_payload()
    return {"schema_version": "llm-wiki-task-reconciliation/v1",
            "basis_matches": previous["basis"] == payload["basis"] if current.ok else None,
            "previous_result_id": previous["result_id"], "current_result_id": current.result_id,
            "request_id": previous["request_id"], "packet_reconciliation": packet_report,
            "semantic_adequacy": "not-evaluated", "context": current}


def validate_task_context(rendered, request, *, profile=None, policy=None, counter=None):
    """Check the task envelope separately from the unchanged embedded packet."""
    normalized, effective = normalize_task_request(request, profile=profile, policy=policy)
    counter = _counter(effective.settings, counter)
    try:
        from .request_json import _pairs, _constant
        payload = json.loads(rendered, object_pairs_hook=_pairs, parse_constant=_constant)
        if not isinstance(payload, dict) or set(payload) != {
            "schema_version", "ok", "state", "task_id", "task_ref", "request_id", "profile_id",
            "profile", "basis", "plan", "anchors", "facts", "coverage", "omissions", "followups",
            "work", "packet", "accounting", "limitations", "result_id"
        }:
            raise ValueError("invalid task envelope fields")
        if canonical_json(payload).decode("utf-8") != rendered:
            raise ValueError("task response is not canonical")
        if payload["schema_version"] != TASK_RESULT_SCHEMA or payload["ok"] is not True:
            raise ValueError("unsupported task response")
        if (payload["request_id"] != normalized["request_id"] or payload["task_id"] != normalized["task_id"]
                or payload["profile_id"] != effective.profile_id or payload["profile"] != effective.to_payload()
                or payload["task_ref"] != normalized["task_ref"]):
            raise ValueError("task/profile/request binding mismatch")
        if payload["result_id"] != content_id(TASK_RESULT_SCHEMA, {k: v for k, v in payload.items() if k != "result_id"}):
            raise ValueError("task result identity mismatch")
        accounting = payload["accounting"]
        count = counter.count(rendered)
        if type(count) is not int or count < 0:
            raise ValueError("invalid counter value")
        if (type(accounting["used_tokens"]) is not int or type(accounting["budget_tokens"]) is not int
                or not count <= accounting["used_tokens"] <= effective.settings["budget_tokens"]
                or accounting["budget_tokens"] != effective.settings["budget_tokens"]
                or accounting["counter_id"] != counter.identity
                or accounting["scope"] != "emitted-text-without-host-chat-framing"
                or accounting["mode"] != effective.settings["budget_mode"]
                or accounting["exact_compliance"] is not (effective.settings["budget_mode"] == "exact" and bool(counter.exact))):
            raise ValueError("task accounting mismatch")
        facts = {fact["fact_id"]: fact for fact in payload["facts"]}
        if len(facts) != len(payload["facts"]):
            raise ValueError("duplicate task facts")
        for fact_id, fact in facts.items():
            if set(fact) != {"facet", "selector", "state", "observation", "citations", "qualification", "fact_id"}:
                raise ValueError("invalid fact fields")
            if fact_id != content_id("llm-wiki-task-fact/v1", {k: v for k, v in fact.items() if k != "fact_id"}):
                raise ValueError("fact identity mismatch")
            qualifiers = fact["qualification"]
            if qualifiers["semantic_review"] != "not-evaluated" or qualifiers["behavior"] != "not-evaluated" or qualifiers["negative_claim_supported"] is not False:
                raise ValueError("required evidence qualification was lost")
            if fact["facet"] in _NATIVE_FACETS and not isinstance(qualifiers.get("native"), dict):
                raise ValueError("native evidence qualification was lost")
            observed = fact["observation"]
            if fact["facet"] != "source-contract":
                bounds = observed.get("bounds")
                if not isinstance(bounds, dict) or not bounds:
                    raise ValueError("query bounds were lost")
                for bound in bounds.values():
                    if (not isinstance(bound, dict) or type(bound.get("total")) is not int
                            or type(bound.get("returned")) is not int
                            or not 0 <= bound["returned"] <= bound["total"]
                            or bound.get("truncated") is not (bound["returned"] < bound["total"])):
                        raise ValueError("invalid query bounds")
                if observed.get("truncated") is not any(b["truncated"] for b in bounds.values()):
                    raise ValueError("query truncation qualifier was lost")
                if observed["truncated"] and fact["state"] == "present":
                    raise ValueError("truncated observations cannot have complete coverage")
            if fact["facet"] in _NATIVE_FACETS:
                if qualifiers["native"] != observed.get("knowledge"):
                    raise ValueError("native qualification differs from its observation")
                concept = observed.get("concept") or {}
                if not {"freshness", "evidence", "verification", "lifecycle"} <= set(concept):
                    raise ValueError("native concept qualifications were lost")
            if fact["facet"] in {"callers", "callees", "dependency", "typed-relationships"}:
                if qualifiers.get("graph_completeness") != "static-observations-only":
                    raise ValueError("static graph limitation was lost")
            if fact["facet"] == "typed-relationships":
                for edge in observed["edges"]:
                    if edge.get("resolution") not in {"resolved", "unresolved", "ambiguous", "external"} or not isinstance(edge.get("coverage"), dict):
                        raise ValueError("typed edge qualification was lost")
        requirements = {item["id"]: item for item in normalized["requirements"]}
        if [item["requirement_id"] for item in payload["coverage"]] != list(requirements):
            raise ValueError("requirement coverage mismatch")
        for item in payload["coverage"]:
            requirement = requirements[item["requirement_id"]]
            support = [facts[fact_id] for fact_id in item["fact_ids"]]
            if any(fact["facet"] != requirement["facet"] or
                   (not match_declarations([fact["observation"]], requirement["selector"])
                    if requirement["facet"] == "source-contract" else fact["selector"] != requirement["selector"])
                   for fact in support):
                raise ValueError("coverage refers to unrelated evidence")
            satisfied = item["state"] == "present" and bool(support) and all(fact["state"] == "present" for fact in support)
            if item["satisfied"] is not satisfied or (requirement["facet"] == "behavior" and satisfied):
                raise ValueError("unsupported coverage claim")
            if satisfied and requirement["criterion"] == "complete" and requirement["facet"] in {"callers", "callees", "dependency", "typed-relationships"}:
                raise ValueError("static observations cannot establish a complete runtime graph")
        if payload["omissions"] != [item for item in payload["coverage"] if not item["satisfied"]]:
            raise ValueError("missing omission disclosure")
        basis = payload["basis"]
        if basis["capture_id"] != content_id("llm-wiki-task-basis/v1", {k: v for k, v in basis.items() if k != "capture_id"}):
            raise ValueError("capture identity mismatch")
        if (payload["packet"] is None) != (basis["source"] is None):
            raise ValueError("required captured packet is missing")
        if any(fact["qualification"]["analysis_scope"] != basis["scope"] for fact in facts.values()):
            raise ValueError("fact scope differs from the captured basis")
        if payload["packet"] is not None:
            packets.validate_context_packet(packets._encode_packet_payload(payload["packet"]))
            if payload["packet"]["basis"]["source_snapshot"]["identity"] != basis["consumed_source"]:
                raise ValueError("packet/source binding mismatch")
            packet_request = payload["packet"]["request"]
            if (packet_request["knowledge_mode"] != effective.settings["knowledge_mode"]
                    or packet_request["prefer_fresh"] != effective.settings["prefer_fresh"]):
                raise ValueError("packet/profile binding mismatch")
        if len(payload["followups"]) > effective.settings["max_followups"]:
            raise ValueError("too many followups")
        if any(item["automatic"] is not False or item["requires_host_authorization"] is not True for item in payload["followups"]):
            raise ValueError("followups cannot grant authority")
    except (KeyError, TypeError, ValueError, RecursionError) as exc:
        raise WorkflowRequestError("result", str(exc)) from exc
    return payload
