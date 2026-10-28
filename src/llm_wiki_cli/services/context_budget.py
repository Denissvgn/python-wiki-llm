"""Opt-in full-render context budgets over the existing captured-read contract."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from dataclasses import dataclass, replace
from typing import Any, Mapping

from ..config import DEFAULT_WIKI_DIR
from . import context_packet as packets, context_service as context
from .contracts import CONTEXT_BUDGET_PROTOCOL_VERSION
from .io import write_text_output, write_utf8_stdout
from .token_counting import EstimatedCounter, LocalTokenizerCounter, TokenCounter
from .change_selection import (
    affected_page_map,
    changes_from_args,
    select_changes,
    validate_changes,
)


@dataclass(frozen=True)
class BudgetedContext:
    ok: bool
    rendered: str
    accounting: Mapping[str, Any]
    error: str | None = None
    diagnostics: Mapping[str, Any] | None = None


def refusal_diagnostics(payload, request, counter, accounting, *, policy):
    """Describe a rejected candidate without emitting source or native rows."""
    knowledge = payload.get("knowledge", {})
    files = payload["files"]

    def json_bytes(value):
        return len(json.dumps(value, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":"), allow_nan=False).encode("utf-8"))

    return {
        "schema_version": "llm-wiki-context-budget-refusal/v1",
        "request_id": request_identity(request),
        "selection_policy": policy,
        "reason": "permitted-selection-reductions-exhausted",
        "accounting_meaning": "rejected-candidate-not-emitted-context-or-global-minimum",
        "counter_id": counter.identity,
        "budget_mode": request["budget_mode"],
        "emitted_context_bytes": 0,
        "source": {"total": len(files) + len(payload["omitted_files"]),
                   "returned": len(files), "omitted": len(payload["omitted_files"])},
        "native": {"mode": knowledge.get("mode", request.get("knowledge_mode", "off")),
                   "status": knowledge.get("status", "disabled"),
                   "availability": knowledge.get("availability", "not-evaluated"),
                   "bounds": copy.deepcopy(knowledge.get("bounds", {}))},
        "component_bytes": {
            "measurement": "canonical-json-fragments-not-additive-token-costs",
            "source_entries": json_bytes(files),
            "native_knowledge": json_bytes(knowledge),
            "omitted_files": json_bytes(payload["omitted_files"]),
            "source_priorities": json_bytes(payload.get("source_priorities", {})),
        },
        "recovery": [
            {"id": "scoped-evidence", "automatic": False,
             "new_request_binding_required": True,
             "description": "Choose a task-scoped context/session or bounded documentation query matching the actual requirements; preserve native requirements and all evidence qualifications."},
            {"id": "explicit-larger-budget", "automatic": False,
             "new_request_binding_required": True,
             "description": "Explicitly authorize a larger complete-output budget, then independently fit and recount it with the pinned counter. The failed request remains unsatisfied."},
        ],
    }


def validate_request(data: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(data, Mapping) or any(not isinstance(key, str) for key in data):
        raise context.ProtocolRequestError("Request must be an object with string keys", "request")
    if data.get("protocol", CONTEXT_BUDGET_PROTOCOL_VERSION) != CONTEXT_BUDGET_PROTOCOL_VERSION:
        raise context.ProtocolRequestError("Unsupported context budget protocol", "protocol")
    allowed = context._V2_REQUEST_KEYS | {"budget_mode", "counter_id", "changes"}
    unknown = set(data) - allowed
    if unknown:
        raise context.ProtocolRequestError(
            f"Unknown request field: {sorted(unknown)[0]}", sorted(unknown)[0]
        )
    legacy = dict(data)
    legacy["protocol"] = context.KNOWLEDGE_PROTOCOL_VERSION
    legacy["knowledge_mode"] = data.get("knowledge_mode", "off")
    legacy["format"] = (
        "json" if data.get("format") == "packet" else data.get("format", "json")
    )
    legacy.pop("budget_mode", None)
    legacy.pop("counter_id", None)
    legacy.pop("changes", None)
    normalized = context._validate_protocol_request(legacy)
    mode = data.get("budget_mode", "exact")
    if not isinstance(mode, str) or mode not in {"exact", "estimated"}:
        raise context.ProtocolRequestError(
            "budget_mode must be exact or estimated", "budget_mode"
        )
    identity = data.get("counter_id")
    if identity is not None and (not isinstance(identity, str) or not identity):
        raise context.ProtocolRequestError(
            "counter_id must be a nonempty string", "counter_id"
        )
    changes = None
    if "changes" in data:
        try:
            changes = validate_changes(data["changes"])
        except ValueError as exc:
            raise context.ProtocolRequestError(str(exc), "changes") from exc
    return {
        **normalized,
        **({"changes": changes} if changes is not None else {}),
        "protocol": CONTEXT_BUDGET_PROTOCOL_VERSION,
        "format": data.get("format", "json"),
        "budget_mode": mode,
        "counter_id": identity,
    }


def _accounted_render(render, accounting, counter):
    # Monotone upper-bound accounting avoids tokenizer-dependent digit cycles.
    accounting["used_tokens"] = 0
    for _ in range(32):
        text = render(accounting)
        used = counter.count(text)
        if isinstance(used, bool) or not isinstance(used, int) or used < 0:
            raise ValueError("Token counter returned an invalid count")
        if used <= accounting["used_tokens"]:
            return text
        accounting["used_tokens"] = used
    raise ValueError("Token accounting did not converge")


class _JointSelection:
    """Spend one budget across whole native groups and source detail.

    Relevance wins before currentness. Within the same rank, optional native
    relationships and source detail yield before concepts and whole sources.
    A useful source and native group remain when available; explicit target
    enrichment and its selected coordinates are never reduced.
    """

    def __init__(self, payload, request, freshness):
        self.payload, self.request = payload, request
        self.freshness = freshness if request.get("prefer_fresh") else {}
        self.priorities = payload.get("source_priorities", {})
        files = payload["files"]
        self.required_sources = {min(files, key=self.rank)} if files else set()
        knowledge = payload.get("knowledge", {})
        self.required_native = set()
        if knowledge.get("status") == "selected":
            concepts = knowledge["selection"]["concepts"]
            best = min(concepts, key=lambda row: (*self.rank(row["source_path"]), row["locator"]))
            self.required_native.add(best["locator"])
            self.required_sources.add(best["source_path"])
            # An explicit query's complete target evidence stays in enrichment.
            # Retain matching broad groups too, rather than treating a requested
            # coordinate as an optional row merely to satisfy the budget.
            references = set()

            def visit(value):
                if isinstance(value, Mapping):
                    for child in value.values():
                        visit(child)
                elif isinstance(value, (list, tuple)):
                    for child in value:
                        visit(child)
                elif isinstance(value, str):
                    references.add(value)

            visit(payload.get("graphs", {}))
            visit(payload.get("surface", {}))
            for row in concepts:
                if row["locator"] in references or row["canonical_path"] in references:
                    self.required_native.add(row["locator"])
                    self.required_sources.add(row["source_path"])

    def rank(self, path):
        priority = self.priorities.get(path, self.payload["files"].get(path, {}).get("priority", "low"))
        return ({"high": 0, "medium": 1, "low": 2}.get(priority, 2),
                self.freshness.get(path, 1))

    def reduce(self):
        choices = []
        files = self.payload["files"]
        for order, (path, row) in enumerate(files.items()):
            if row["detail"] != "summary":
                choices.append(((*self.rank(path), 4, order), "source", path))
            elif path not in self.required_sources:
                choices.append(((*self.rank(path), 2, order), "source", path))
        knowledge = self.payload.get("knowledge", {})
        if knowledge.get("status") == "selected":
            selection = knowledge["selection"]
            concepts = selection["concepts"]
            by_locator = {row["locator"]: row for row in concepts}
            by_path = {row["canonical_path"]: row["locator"] for row in concepts}

            def endpoint(value):
                if isinstance(value, str):
                    return value if value in by_locator else None
                if isinstance(value, Mapping):
                    locator = value.get("locator")
                    return locator if locator in by_locator else by_path.get(value.get("canonical_path"))
                return None

            for order, row in enumerate(concepts):
                if row["locator"] not in self.required_native:
                    choices.append(((*self.rank(row["source_path"]), 3, order), "native", row["locator"]))
            for order, row in enumerate(selection["relationships"]):
                incident = (endpoint(row.get("from")), endpoint(row.get("target")))
                rank = min((self.rank(by_locator[locator]["source_path"])
                            for locator in incident if locator is not None), default=(3, 1))
                choices.append(((*rank, 5, order), "relationship", order))
        if not choices:
            return None
        _rank, kind, selected = max(choices, key=lambda row: row[0])
        if kind == "source":
            return selected
        retained = {row["locator"] for row in knowledge["selection"]["concepts"]}
        if kind == "native":
            retained.remove(selected)
        else:
            knowledge["selection"]["relationships"].pop(selected)
        self.payload["knowledge"] = context._select_native_context_groups(
            knowledge, retained, self.priorities,
        )
        return False


def fit_payload(
    payload, request, warnings, counter, *, packet_renderer=None, changes=None,
    envelope_renderer=None,
    freshness_rank_by_source=None,
    source_json_lower_bound=False,
    broad_refusal_diagnostics=False,
    joint_native_source=False,
):
    """Select whole source entries; keep all enrichment and omission evidence."""
    payload = copy.deepcopy(payload)
    freshness_rank_by_source = freshness_rank_by_source or {}
    budget = request["budget_tokens"]
    accounting = {
        "budget_tokens": budget,
        "used_tokens": 0,
        "counter_id": counter.identity,
        "mode": request["budget_mode"],
        "exact_compliance": request["budget_mode"] == "exact" and bool(counter.exact),
        "usage_kind": "upper-bound-including-accounting",
        "scope": "emitted-text-without-host-chat-framing",
    }
    envelope = {
        "protocol": CONTEXT_BUDGET_PROTOCOL_VERSION,
        "ok": True,
        "format": request["format"],
        "accounting": accounting,
        "request_id": request_identity(request),
    }
    envelope["changes"] = changes or {"request": {"mode": "legacy-last-commit"}}
    # The inner legacy budget is an allocation bound, not a compliance claim.
    legacy_request = {k: v for k, v in request.items() if k in context._V2_REQUEST_KEYS}
    legacy_request.update(
        protocol=context.KNOWLEDGE_PROTOCOL_VERSION,
        budget_tokens=payload["budget"],
        format="json",
    )

    def render(accounting):
        if "ranking_policy" in payload:
            payload["ranking_policy"] = context._explicit_freshness_ranking_policy(
                payload.get("knowledge", {}), freshness_rank_by_source,
                budget_pressure=bool(payload["truncated"]),
            )
        payload["used"] = sum(
            context._entry_tokens(p, e) for p, e in payload["files"].items()
        )
        payload["bounds"]["files"] = context._bounds_metadata(
            total=len(payload["files"]) + len(payload["omitted_files"]),
            returned=len(payload["files"]),
        )
        if request["format"] == "markdown":
            # The full JSON metadata is present even when the legacy renderer
            # omits a field; evidence is never lost in a display conversion.
            metadata = {k: v for k, v in payload.items() if k != "files"}
            return (
                "# Budgeted context\n\n```json\n"
                + json.dumps(
                    {**envelope, "metadata": metadata, "warnings": warnings},
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n```\n\n"
                + context._render_markdown(payload)
                + "\n"
            )
        response = context._protocol_success_payload(legacy_request, payload, warnings)
        if joint_native_source or packet_renderer is not None:
            response["source_priorities"] = payload.get("source_priorities", {})
        if packet_renderer is not None:
            value = {**envelope, "packet": packet_renderer(legacy_request, response)}
        else:
            value = {**envelope, "context": response}
        if envelope_renderer is not None:
            return envelope_renderer(value)
        return (
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        )

    def entry_bytes(path, entry):
        return len(json.dumps(
            {path: entry}, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")) - 2

    sizes = None
    if (source_json_lower_bound and type(counter) is EstimatedCounter
            and request["format"] in {"json", "packet"} and envelope_renderer is None):
        # The files object is an unchanged fragment of the full JSON output.
        # Its UTF-8 bytes are a lower bound only for this built-in counter;
        # arbitrary tokenizers/counters need complete rendering on every step.
        sizes = {path: entry_bytes(path, entry) for path, entry in payload["files"].items()}
    size_total = sum(sizes.values()) if sizes is not None else 0
    joint = _JointSelection(payload, request, freshness_rank_by_source) if joint_native_source else None

    while True:
        counted_candidate = sizes is None or size_total + max(0, len(sizes) - 1) + 2 <= budget * 4
        if counted_candidate:
            rendered = _accounted_render(render, accounting, counter)
            if accounting["used_tokens"] <= budget:
                return BudgetedContext(True, rendered, dict(accounting))
        files = payload["files"]
        selected = joint.reduce() if joint is not None else None
        if selected is False:
            continue
        if not files or joint is not None and selected is None:
            # Even an estimator lower-bound shortcut must report the complete
            # last rejected candidate, not an uncounted or stale estimate.
            if not counted_candidate:
                _accounted_render(render, accounting, counter)
            return BudgetedContext(
                False, "", {**accounting, "exact_compliance": False}, "cannot-fit",
                refusal_diagnostics(payload, request, counter, accounting,
                                    policy="joint-native-source/v1" if joint is not None else "source-tail-reduction/v1")
                if broad_refusal_diagnostics else None,
            )
        if joint is None and freshness_rank_by_source and request.get("prefer_fresh"):
            order = {path: index for index, path in enumerate(files)}
            priorities = {"high": 0, "medium": 1, "low": 2}
            files = payload["files"] = dict(sorted(files.items(), key=lambda item: (
                priorities.get(item[1]["priority"], 2),
                freshness_rank_by_source.get(item[0], 1), order[item[0]],
            )))
        path = selected if joint is not None else next(reversed(files))
        entry = files[path]
        detail = entry["detail"]
        if detail == "summary":
            del files[path]
            payload["omitted_files"].append(path)
            payload["downgraded_files"].pop(path, None)
        else:
            detail = "slim" if detail == "deep" else "summary"
            files[path] = context._build_entry(entry, entry["priority"], detail)
            payload["downgraded_files"][path] = detail
        if sizes is not None:
            size_total -= sizes.pop(path)
            if path in files:
                sizes[path] = entry_bytes(path, files[path])
                size_total += sizes[path]
        payload["truncated"] = True


def build_budgeted_context(
    src_dir=".",
    wiki_dir=DEFAULT_WIKI_DIR,
    request=None,
    *,
    counter: TokenCounter | None = None,
    allow_external_src=False,
    source_selection=None,
) -> BudgetedContext:
    request = validate_request({"budget_tokens": 32000} if request is None else request)
    if counter is None:
        if request["budget_mode"] == "exact":
            raise ValueError(
                "Exact mode requires an explicit trusted counter or --tokenizer FILE"
            )
        counter = EstimatedCounter()
    if not isinstance(counter.identity, str) or not counter.identity:
        raise ValueError("Token counter must have a pinned identity")
    if request["budget_mode"] == "exact" and not counter.exact:
        raise ValueError("An estimated counter cannot satisfy exact mode")
    if request.get("counter_id") not in (None, counter.identity):
        raise ValueError("Requested counter_id does not match the trusted counter")
    captured = packets.capture_context_read(
        src_dir,
        wiki_dir,
        allow_external_src=allow_external_src,
        read_only=True,
        source_selection=source_selection,
        allow_selection_mismatch=True,
        strict_wiki_symlinks=True,
    )
    changes = None
    if "changes" in request:
        changes = select_changes(
            captured.source_root, request["changes"], snapshot=captured.source_snapshot
        )
        captured = replace(
            captured,
            changed_files=tuple(changes["paths"]),
            explicit_changes=True,
            change_selection=changes,
        )
        changes = dict(changes)
        changes["affected_pages"] = affected_page_map(
            changes["paths"],
            captured.inventory,
            captured.surface_evaluation.payload.get("pages", ()),
            page_contents=captured.surface_evaluation.content_by_path,
        )
    legacy = {k: v for k, v in request.items() if k in context._V2_REQUEST_KEYS}
    legacy.update(
        protocol=context.KNOWLEDGE_PROTOCOL_VERSION,
        format="json",
        budget_tokens=2**63 - 1,
    )
    freshness_ranks: dict[str, int] = {}
    payload, warnings = packets.build_context_from_captured_read(captured, legacy,
                                                               freshness_ranking_out=freshness_ranks)

    def packet_renderer(legacy, response):
        # Fitting starts with an unbounded internal candidate. Apply wire limits
        # only to the selected output, rather than rejecting before reduction.
        contract = packets._packet_contract_for_request(legacy)
        body = {
            "schema_version": contract.schema_version,
            **packets._packet_body(captured, legacy, response, contract),
        }
        return {**body, "packet_id": packets._packet_id(body)}

    result = fit_payload(
        payload,
        request,
        warnings,
        counter,
        packet_renderer=packet_renderer if request["format"] == "packet" else None,
        changes=changes,
        freshness_rank_by_source=freshness_ranks,
        source_json_lower_bound=True,
        broad_refusal_diagnostics=True,
        joint_native_source=True,
    )
    if result.ok:
        validate_budgeted_context(result.rendered, request, counter=counter)
    packets._assert_source_unchanged(captured.source_snapshot, captured.source_anchor)
    packets._assert_wiki_unchanged(
        captured.wiki_root, captured.wiki_anchor, reject_all_symlinks=True,
        expected_integrity=captured.wiki_integrity,
    )
    packets._assert_selection_unchanged(captured)
    return result


def request_identity(request: Mapping[str, Any]) -> str:
    normalized = validate_request(request)
    raw = json.dumps(normalized, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(b"llm-wiki-context-request/v3\0" + raw).hexdigest()


def validate_budgeted_context(
    rendered: str, request: Mapping[str, Any], *, counter: TokenCounter,
) -> dict[str, Any]:
    """Independently validate the outer v3 binding, packet and emitted count."""
    normalized = validate_request(request)
    if not isinstance(rendered, str) or not rendered.endswith("\n"):
        raise ValueError("Budgeted output must be canonical UTF-8 text ending in LF")
    if normalized["format"] == "markdown":
        prefix = "# Budgeted context\n\n```json\n"
        if not rendered.startswith(prefix) or "\n```\n\n" not in rendered[len(prefix):]:
            raise ValueError("Invalid budgeted markdown envelope")
        raw = rendered[len(prefix):].split("\n```\n\n", 1)[0]
    else:
        raw = rendered
    from .request_json import _pairs, _constant

    try:
        payload = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, RecursionError) as exc:
        raise ValueError("Invalid budgeted context JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Budgeted context must contain an object")
    common = {"protocol", "ok", "format", "request_id", "changes", "accounting"}
    fields = {"markdown": {"metadata", "warnings"}, "json": {"context"}, "packet": {"packet"}}
    if set(payload) != common | fields[normalized["format"]]:
        raise ValueError("Invalid budgeted context envelope fields")
    if (payload["protocol"] != CONTEXT_BUDGET_PROTOCOL_VERSION or payload["ok"] is not True
            or payload["format"] != normalized["format"]
            or payload["request_id"] != request_identity(normalized)):
        raise ValueError("Budgeted context request binding mismatch")
    accounting = payload["accounting"]
    if not isinstance(accounting, dict) or set(accounting) != {
        "budget_tokens", "used_tokens", "counter_id", "mode", "exact_compliance", "usage_kind", "scope"
    }:
        raise ValueError("Invalid accounting fields")
    for field in ("budget_tokens", "used_tokens"):
        if type(accounting[field]) is not int or accounting[field] < 0:
            raise ValueError("Invalid token count")
    count = counter.count(rendered)
    if type(count) is not int or count < 0:
        raise ValueError("Invalid trusted counter")
    if (accounting["budget_tokens"] != normalized["budget_tokens"]
            or not count <= accounting["used_tokens"] <= accounting["budget_tokens"]
            or accounting["counter_id"] != counter.identity
            or normalized["counter_id"] not in (None, counter.identity)
            or accounting["mode"] != normalized["budget_mode"]
            or accounting["exact_compliance"] is not (normalized["budget_mode"] == "exact" and bool(counter.exact))
            or (normalized["budget_mode"] == "exact" and not counter.exact)
            or accounting["scope"] != "emitted-text-without-host-chat-framing"
            or accounting["usage_kind"] != "upper-bound-including-accounting"):
        raise ValueError("Budgeted context accounting mismatch")
    if normalized["format"] != "markdown":
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False) + "\n"
        if canonical != rendered:
            raise ValueError("Budgeted context was reserialized")
    if normalized["format"] == "packet":
        packets.validate_context_packet(packets._encode_packet_payload(payload["packet"]))
        inner = payload["packet"]["request"]
    elif normalized["format"] == "json":
        inner = payload["context"]
        if not isinstance(inner, dict) or inner.get("protocol") != context.KNOWLEDGE_PROTOCOL_VERSION or inner.get("ok") is not True:
            raise ValueError("Invalid embedded context")
    else:
        inner = None
    if normalized["format"] in {"json", "markdown"}:
        response = payload["context"] if normalized["format"] == "json" else payload["metadata"]
        if not isinstance(response, Mapping):
            raise ValueError("Invalid context metadata")
        packets._validate_explicit_knowledge_response(
            response["knowledge"], normalized,
            source_priorities=response.get("source_priorities"),
        )
    if inner is not None:
        fields = ("focus", "filters", "prefer_fresh", "knowledge_mode") if normalized["format"] == "packet" else ("focus", "filters", "prefer_fresh")
        for field in fields:
            if inner.get(field, False if field == "prefer_fresh" else None) != normalized.get(field):
                raise ValueError("Embedded context request mismatch")
    changes = payload["changes"]
    if not isinstance(changes, dict) or not isinstance(changes.get("request"), dict):
        raise ValueError("Invalid change selection binding")
    expected_changes = normalized.get("changes", {"mode": "legacy-last-commit"})
    if any(changes["request"].get(key) != value for key, value in expected_changes.items()):
        raise ValueError("Change selection request mismatch")
    return payload


def run(args, request=None):
    if request is None:
        request = {
            "budget_tokens": args.budget,
            "format": args.format,
            "focus": ["all"] if args.focus == "all" else ["changed", "neighbors"],
            "knowledge_mode": args.knowledge_mode or "off",
            "prefer_fresh": args.prefer_fresh,
            "budget_mode": args.budget_mode or "estimated",
        }
        changes = changes_from_args(args)
        if changes is not None:
            request["changes"] = changes
    elif getattr(args, "budget_mode", None) is not None:
        raise ValueError("With --request, place budget_mode in the request")
    elif changes_from_args(args) is not None:
        raise ValueError("With --request, place changes in the request")
    counter = (
        LocalTokenizerCounter(args.tokenizer)
        if getattr(args, "tokenizer", None)
        else None
    )
    try:
        result = build_budgeted_context(
            args.src_dir,
            args.wiki_dir,
            request,
            counter=counter,
            allow_external_src=args.allow_external_src,
            source_selection=args.source_selection,
        )
    except packets.ContextPacketAuthorityError as exc:
        context._emit_packet_error(exc, protocol=CONTEXT_BUDGET_PROTOCOL_VERSION)
        raise
    if not result.ok:
        print(
            json.dumps(
                {
                    "protocol": CONTEXT_BUDGET_PROTOCOL_VERSION,
                    "ok": False,
                    "error": result.error,
                    "accounting": result.accounting,
                    "diagnostics": result.diagnostics,
                }
            ),
            file=sys.stderr,
        )
        raise SystemExit(3)
    if getattr(args, "output", None):
        write_text_output(args.output, result.rendered)
    else:
        write_utf8_stdout(result.rendered)
