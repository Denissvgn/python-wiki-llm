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


def fit_payload(
    payload, request, warnings, counter, *, packet_renderer=None, changes=None,
    envelope_renderer=None,
    freshness_rank_by_source=None,
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
        if packet_renderer is not None:
            response["source_priorities"] = payload.get("source_priorities", {})
            value = {**envelope, "packet": packet_renderer(legacy_request, response)}
        else:
            value = {**envelope, "context": response}
        if envelope_renderer is not None:
            return envelope_renderer(value)
        return (
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        )

    while True:
        rendered = _accounted_render(render, accounting, counter)
        if accounting["used_tokens"] <= budget:
            return BudgetedContext(True, rendered, dict(accounting))
        files = payload["files"]
        if not files:
            return BudgetedContext(
                False, "", {**accounting, "exact_compliance": False}, "cannot-fit"
            )
        if freshness_rank_by_source and request.get("prefer_fresh"):
            order = {path: index for index, path in enumerate(files)}
            priorities = {"high": 0, "medium": 1, "low": 2}
            files = payload["files"] = dict(sorted(files.items(), key=lambda item: (
                priorities.get(item[1]["priority"], 2),
                freshness_rank_by_source.get(item[0], 1), order[item[0]],
            )))
        path = next(reversed(files))
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
        return packets.packet_from_captured_response(
            captured, legacy, response
        ).to_payload()

    result = fit_payload(
        payload,
        request,
        warnings,
        counter,
        packet_renderer=packet_renderer if request["format"] == "packet" else None,
        changes=changes,
        freshness_rank_by_source=freshness_ranks,
    )
    packets._assert_source_unchanged(captured.source_snapshot, captured.source_anchor)
    packets._assert_wiki_unchanged(
        captured.wiki_root, captured.wiki_anchor, reject_all_symlinks=True
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
    result = build_budgeted_context(
        args.src_dir,
        args.wiki_dir,
        request,
        counter=counter,
        allow_external_src=args.allow_external_src,
        source_selection=args.source_selection,
    )
    if not result.ok:
        print(
            json.dumps(
                {
                    "protocol": CONTEXT_BUDGET_PROTOCOL_VERSION,
                    "ok": False,
                    "error": result.error,
                    "accounting": result.accounting,
                }
            ),
            file=sys.stderr,
        )
        raise SystemExit(3)
    if getattr(args, "output", None):
        write_text_output(args.output, result.rendered)
    else:
        write_utf8_stdout(result.rendered)
