"""Opt-in full-render context budgets over the existing captured-read contract."""

from __future__ import annotations

import copy
import json
import sys
from dataclasses import dataclass, replace
from typing import Any, Mapping

from ..config import DEFAULT_WIKI_DIR
from . import context_packet as packets, context_service as context
from .contracts import CONTEXT_BUDGET_PROTOCOL_VERSION
from .io import write_text_output
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
    allowed = context._V2_REQUEST_KEYS | {"budget_mode", "counter_id", "changes"}
    unknown = set(data) - allowed
    if unknown:
        raise context.ProtocolRequestError(
            f"Unknown request field: {sorted(unknown)[0]}"
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
    payload, request, warnings, counter, *, packet_renderer=None, changes=None
):
    """Select whole source entries; keep all enrichment and omission evidence."""
    payload = copy.deepcopy(payload)
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
        # Existing insertion order already carries relevance and freshness ties.
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
    request = validate_request(request or {"budget_tokens": 32000})
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
            captured, changed_files=tuple(changes["paths"]), explicit_changes=True
        )
        changes["affected_pages"] = affected_page_map(
            changes["paths"],
            captured.inventory,
            captured.surface_evaluation.payload.get("pages", ()),
        )
    legacy = {k: v for k, v in request.items() if k in context._V2_REQUEST_KEYS}
    legacy.update(
        protocol=context.KNOWLEDGE_PROTOCOL_VERSION,
        format="json",
        budget_tokens=2**63 - 1,
    )
    payload, warnings = packets.build_context_from_captured_read(captured, legacy)

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
    )
    packets._assert_source_unchanged(captured.source_snapshot, captured.source_anchor)
    packets._assert_wiki_unchanged(
        captured.wiki_root, captured.wiki_anchor, reject_all_symlinks=True
    )
    packets._assert_selection_unchanged(captured)
    return result


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
        sys.stdout.write(result.rendered)
