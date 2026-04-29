from __future__ import annotations

import json

from ..config import DEFAULT_WIKI_DIR, validate_path
from ..services.metrics import load_events, summarize_events


def _fmt_percent(value) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}%"


def _fmt_ms(value) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f} ms"


def render_text(summary: dict, last: str) -> str:
    accuracy = summary["accuracy"]
    coverage = summary["coverage"]
    speed = summary["speed"]
    totals = summary["totals"]

    lines = [
        f"LLM Wiki metrics (last {last})",
        "",
        f"Accuracy: {_fmt_percent(accuracy['strict_validation_pass_percent'])} strict validation pass rate "
        f"({accuracy['validations']} run(s), {accuracy['failures']} failure(s))",
        f"Coverage: {_fmt_percent(coverage['percent'])} "
        f"({coverage['entities']['documented']}/{coverage['entities']['total']} entities, "
        f"{coverage['modules']['documented']}/{coverage['modules']['total']} modules)",
        f"Speed: {_fmt_ms(speed['average_successful_sync_ms'])} average successful sync "
        f"({speed['successful_syncs']} run(s))",
        f"Totals: {totals['sync_attempts']} sync attempt(s), {totals['validations']} validation(s), "
        f"{totals['failures']} failure(s), {totals['events']} event(s)",
    ]

    if summary["recent_failures"]:
        lines.extend(["", "Recent failures:"])
        for event in summary["recent_failures"]:
            label = event.get("command") or event.get("agent") or event.get("event")
            detail = event.get("issue_count", event.get("exit_code", "unknown"))
            lines.append(f"- {event.get('ts', '?')} {label}: {detail}")
    return "\n".join(lines) + "\n"


def run(args) -> None:
    src_dir: str = getattr(args, "src_dir", ".")
    wiki_dir: str = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    last: str = getattr(args, "last", "30d")
    output_format: str = getattr(args, "format", "text")

    validate_path(src_dir, "--src-dir")
    validate_path(wiki_dir, "--wiki-dir")

    events = load_events(last=last)
    summary = summarize_events(events, src_dir=src_dir, wiki_dir=wiki_dir)

    if output_format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(render_text(summary, last), end="")
