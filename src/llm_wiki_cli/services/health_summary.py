"""Pure presentation helpers for detailed local and CI health reports."""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence

from . import analysis_compatibility as ac
from .freshness_wording import SOURCE_CHANGED_STRUCTURE_UNCHANGED


FRESHNESS_ORDER = (
    "current", "basis-incompatible", "unknown", "nonsemantic-source-change",
    "source-changed", "source-missing",
)
FRESHNESS_DISCLOSURE = (
    "Evaluated does not mean current. Unknown may include unmodeled or unavailable "
    "evidence; zero confirmed drift alone does not establish currentness. "
    "nonsemantic-source-change: " + SOURCE_CHANGED_STRUCTURE_UNCHANGED
)
RELEASE_POLICY_UNAVAILABLE = (
    "unavailable (requires separate authenticated, matching release-policy evidence)"
)
ASSURANCE_DISCLOSURE = (
    "Structural integrity and freshness are separate from human review and machine "
    "verification; none alone establishes semantic approval."
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
        return "strict; indeterminate/source-byte drift is unhealthy"
    return "non-strict; indeterminate/source-byte drift is degraded"


def optional_status(state: str, *, absent: str) -> str:
    """Disclose optional absence without changing present evidence states."""
    return state + " (optional; absent)" if state == absent else state


def assurance_rows(report: Mapping) -> list[tuple[str, str]]:
    """Describe captured assurance without inferring adoption or review coverage."""
    governance = report["governance"]
    verification = report["verification_receipt"]
    authority = optional_status(governance["state"], absent="not-present")
    if governance["state"] != "not-present":
        authority += f"; ledger={governance['ledger']}; projection={governance['projection']}"
    if governance["reasons"]:
        authority += "; " + reason_list(governance["reasons"])
    review = (
        f"expired={governance['expired_reviews']}; current review coverage not established "
        "by this aggregate; inspect scoped review records"
    )
    machine = optional_status(verification["state"], absent="absent")
    if verification["state"] != "absent":
        machine += (
            f"; recorded={verification['recorded_result']}; current_passed={verification['passed']}"
            "; recorded scope/checks only"
        )
    return [
        ("Governance authority", authority),
        ("Human review", review),
        ("Machine verification", machine),
    ]


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


def captured_analysis_diagnostic(report: Mapping) -> dict | None:
    """Read validated native commitments, never the current installation."""
    detail = report.get("health_details")
    if detail is None or detail["schema_version"] != "llm-wiki-health-details/v2":
        return None
    basis = detail["basis"]
    if basis["recorded"] is None or basis["live"] is None:
        return None
    return ac.analysis_diagnostic(
        ac.captured_components(basis, "recorded"), ac.captured_components(basis, "live"),
    )


def detailed_health_rows(report: Mapping) -> list[tuple[str, str]]:
    """Describe validated evidence; legacy reports cannot gain inferred detail."""
    detail = report.get("health_details")
    if detail is None:
        return [("Coverage detail", "unavailable in this legacy report; select report-schema v3")]
    coverage = detail["coverage"]
    evaluation = detail["evaluation"]["state"]
    basis = detail["basis"]
    recorded, live = basis["recorded"], basis["live"]
    analysis_diagnosis = None
    analysis_detail = "unavailable in this legacy comparison"
    if detail["schema_version"] == "llm-wiki-health-details/v2":
        analysis_detail = "unavailable (recorded or live producer basis missing)"
        if recorded is not None and live is not None:
            analysis_diagnosis = captured_analysis_diagnostic(report)
            analysis_detail = (analysis_diagnosis["description"] if analysis_diagnosis is not None else
                               "No changed analysis commitments; exact-version and other policy requirements remain separate.")
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
        if analysis_diagnosis is not None and basis.get("comparison", {}).get("reason") == "analysis-configuration-changed":
            remedy = analysis_diagnosis["hint"]
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
        ("Comparison policy", basis["policy"] + ("; " + basis["comparison"]["reason"] if "comparison" in basis else "")),
        ("Analysis dimensions", analysis_detail),
        ("Components", "extractors: " + _versions(recorded, live, "extractors") + "; plugins: " + _versions(recorded, live, "plugins")),
        ("Primary causes (concepts)", causes),
        ("Affected examples", "; ".join(examples) or "none reported"),
        ("Next action", remedy),
    ]
