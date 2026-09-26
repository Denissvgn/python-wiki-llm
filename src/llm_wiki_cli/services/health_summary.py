"""Pure presentation helpers for detailed local and CI health reports."""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence


FRESHNESS_ORDER = (
    "current", "basis-incompatible", "unknown", "nonsemantic-source-change",
    "source-changed", "source-missing",
)
FRESHNESS_DISCLOSURE = (
    "Evaluated does not mean current. Unknown may include unmodeled or unavailable "
    "evidence; zero confirmed drift alone does not establish currentness."
)


def summary_cell(value: object, limit: int = 240) -> str:
    """Escape inline-code/table content and explicitly disclose UTF-8 clipping."""
    marker = "... [truncated]"
    if limit < len(marker):
        raise ValueError("summary cell limit is too small")
    pieces = []
    size = 0
    for character in str(value):
        if character in "\r\n\u0085\u2028\u2029":
            piece = " "
        elif unicodedata.category(character) in {"Cc", "Cf", "Cs"}:
            codepoint = ord(character)
            piece = f"\\u{codepoint:04x}" if codepoint <= 0xFFFF else f"\\U{codepoint:08x}"
        else:
            piece = character.replace("`", r"\x60").replace("|", r"\|")
        pieces.append(piece)
        size += len(piece.encode("utf-8"))
        if size > limit:
            prefix = "".join(pieces).encode("utf-8")[:limit - len(marker)]
            return prefix.decode("utf-8", "ignore") + marker
    return "".join(pieces)


def health_policy(strict: bool) -> str:
    """Describe classification independently of an Action's failure threshold."""
    if strict:
        return "strict; indeterminate/nonsemantic drift is unhealthy"
    return "non-strict; indeterminate/nonsemantic drift is degraded"


def optional_status(state: str, *, absent: str) -> str:
    """Disclose optional absence without changing present evidence states."""
    return state + " (optional; absent)" if state == absent else state


def freshness_counts(counts: Mapping[str, int] | None) -> str:
    """Describe existing state counters without inventing model eligibility."""
    if counts is None:
        return "not evaluated"
    return ", ".join(f"{state}={counts[state]}" for state in FRESHNESS_ORDER)


def reason_list(reasons: Sequence[str], limit: int = 5) -> str:
    """List a bounded prefix of reported reasons, without estimating counts."""
    shown = "; ".join(reasons[:limit]) or "none reported"
    if len(reasons) > limit:
        shown += f"; ... [{len(reasons) - limit} more reasons; see full JSON]"
    return shown


def _versions(recorded, live, kind: str, limit: int = 3) -> str:
    if recorded is None or live is None:
        return "comparison basis unavailable"
    left = {row["id"]: row for row in recorded[kind]}
    right = {row["id"]: row for row in live[kind]}
    keys = sorted(set(left) | set(right))
    changed = [key for key in keys if left.get(key) != right.get(key)]
    shown = changed or keys
    values = [
        f"{key}: {left.get(key, {}).get('version', 'absent')} -> {right.get(key, {}).get('version', 'absent')}"
        for key in shown[:limit]
    ]
    text = "; ".join(values) or "none"
    if len(shown) > limit:
        text += f"; [{len(shown) - limit} more; full JSON]"
    return text


def detailed_health_rows(report: Mapping) -> list[tuple[str, str]]:
    """Describe validated evidence; legacy reports cannot gain inferred detail."""
    detail = report.get("health_details")
    if detail is None:
        return [("Coverage detail", "unavailable in this legacy report; select report-schema v3")]
    coverage = detail["coverage"]
    evaluation = detail["evaluation"]["state"]
    basis = detail["basis"]
    recorded, live = basis["recorded"], basis["live"]
    def value(item):
        return "not evaluated" if item is None else str(item)
    outcome = coverage["outcomes"]
    primary = [row for row in detail["reasons"] if row["code"] not in {
        "freshness-not-modeled", "recorded-basis-matches-live-evaluation",
    }]
    primary.sort(key=lambda row: (-row["concepts"], row["code"]))
    causes = "; ".join(f"{row['code']}={row['concepts']}" for row in primary[:3]) or "none reported"
    if len(primary) > 3:
        causes += f"; [{len(primary) - 3} more; full JSON]"
    examples = []
    for row in primary[:3]:
        if row["examples"]:
            examples.append(row["examples"][0])
    tool = "comparison basis unavailable"
    if recorded is not None and live is not None:
        tool = f"{recorded['tool']['id']} {recorded['tool']['version']} -> {live['tool']['id']} {live['tool']['version']}"
    if evaluation != "evaluated":
        remedy = "Complete source/provider preparation and rerun the check; evaluation is incomplete."
    elif outcome and (outcome["source-changed"] or outcome["source-missing"] or outcome["nonsemantic-source-change"]):
        remedy = "Review source changes and run llm-wiki sync with the same selection and generation options."
    elif outcome and outcome["basis-incompatible"]:
        remedy = "Align the installed producer and selected helpers, then refresh with llm-wiki sync."
    elif outcome and outcome["unknown"]:
        remedy = "Inspect missing modeled evidence in the full JSON; prepare providers and reevaluate."
    else:
        remedy = "No modeled drift; unmodeled coverage does not establish source currentness."
    return [
        ("Evaluation", evaluation),
        ("Coverage", ", ".join(f"{key}={value(coverage[key])}" for key in ("total", "modeled", "unmodeled"))),
        ("Comparison", ", ".join(f"{key}={value(coverage[key])}" for key in ("evaluated", "comparison_attempted", "comparable"))),
        ("Modeled outcomes", freshness_counts(outcome)),
        ("Producer", tool),
        ("Components", "extractors: " + _versions(recorded, live, "extractors") + "; plugins: " + _versions(recorded, live, "plugins")),
        ("Primary causes (concepts)", causes),
        ("Affected examples", "; ".join(examples) or "none reported"),
        ("Next action", remedy),
    ]
