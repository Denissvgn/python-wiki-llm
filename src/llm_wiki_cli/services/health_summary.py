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
