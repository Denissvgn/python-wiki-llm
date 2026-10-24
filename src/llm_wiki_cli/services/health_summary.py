"""Pure presentation helpers for detailed local and CI health reports."""

from __future__ import annotations

import unicodedata
import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

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


def ci_health_rows(report: Mapping, health: Mapping) -> list[tuple[str, str]]:
    """Reuse the captured classification without inferring release admission."""
    rows = [
        ("Structural integrity", f"{'passed' if report['ok'] else 'failed'} (strict; blocking)"),
        ("Knowledge health", f"{health['status']} (exit {health['exit_code']}; non-strict; advisory)"),
        ("Native drift", "report-only (advisory)" if report["knowledge_drift_report"] else "disabled"),
        ("Release policy", RELEASE_POLICY_UNAVAILABLE),
        *assurance_rows(health),
    ]
    rows.extend((label, value) for label, value in detailed_health_rows(health)
                if label in {"Analysis dimensions", "Primary causes (concepts)", "Next action"})
    return rows


def _diagnostic_kind(record: Mapping) -> str:
    if record["category"] != "data_flow_gaps":
        return "finding"
    target = record.get("target")
    prefix = f"Data-flow gap in {target}: "
    message = record["message"]
    if isinstance(target, str) and message.startswith(prefix):
        token = message[len(prefix):].split(" ", 1)[0]
        if re.fullmatch(r"[a-z][a-z_]*", token):
            return token
    return "unclassified"


def _diagnostic_priority(category: str, kind: str) -> int:
    if category.startswith("knowledge_") or category in {"extractor_failure", "source-selection-mismatch"}:
        return 0
    if category == "data_flow_gaps":
        return 3 if kind == "external_call" else 2
    return 1


def _record_order(record: Mapping) -> tuple[str, ...]:
    return tuple(str(record.get(key) or "") for key in
                 ("path", "target", "message", "severity", "reason_code", "hint"))


def diagnostic_groups(records: Sequence[Mapping]) -> list[dict[str, Any]]:
    """Partition emitted records; external grouping needs an exact producer prefix."""
    groups: dict[tuple[str, str], list[Mapping]] = defaultdict(list)
    for record in records:
        groups[(record["category"], _diagnostic_kind(record))].append(record)
    return [
        {"category": category, "kind": kind, "records": sorted(groups[(category, kind)], key=_record_order)}
        for category, kind in sorted(groups, key=lambda key: (_diagnostic_priority(*key), *key))
    ]


def diagnostic_preview(records: Sequence[Mapping]) -> dict[str, Any]:
    """Bound examples, keeping duplicate occurrences and exact omitted totals."""
    groups = diagnostic_groups(records)
    shown = [{**group, "records": group["records"][:1], "total": len(group["records"])}
             for group in groups[:8]]
    returned = sum(len(group["records"]) for group in shown)
    return {"total": len(records), "returned": returned, "omitted": len(records) - returned,
            "groups": shown, "group_total": len(groups)}


def _diagnostic_anchor(group: Mapping) -> str:
    identity = json.dumps([group["category"], group["kind"]], ensure_ascii=True).encode()
    return "diagnostic-group-" + hashlib.sha256(identity).hexdigest()[:16]


def _display_hint(record: Mapping, health: Mapping | None) -> str | None:
    hint = record.get("hint")
    if health is not None and record["category"] == "knowledge_freshness":
        from .knowledge_observability import knowledge_freshness_hint

        reasons = {record.get("reason_code")}
        for match in re.findall(r"\[reason=([a-z0-9-]+(?:,[a-z0-9-]+)*)\]", record["message"]):
            reasons.update(match.split(","))
        for reason in ("producer-tool-configuration-changed", "extractor-configuration-changed", "plugin-configuration-changed"):
            if reason in reasons and hint == knowledge_freshness_hint("basis-incompatible", reason):
                diagnosis = captured_analysis_diagnostic(health)
                return (diagnosis["hint"] if diagnosis else
                        "Inspect the recorded and live analysis basis before selecting a repair.")
    return hint


def _legacy_scope_disclosure(record: Mapping) -> str | None:
    if (record["category"] == "unscanned_manifest_scopes"
            and not record.get("path") and not record.get("reason_code")):
        return ("Exact manifest and ownership/cause were not recorded; this read does not infer them. "
                "Skipping is not proof of unused packages or unprepared helpers.")
    return None


def render_validation_markdown(report: Mapping, *, health: Mapping | None = None) -> str:
    """Present a bounded prefix and complete deterministic rows; never scan source."""
    issues, records = report["issues"], report["diagnostics"]
    lines = [
        "# LLM Wiki Validation Report", "",
        f"- Wiki: `{summary_cell(report['wiki_dir'])}`",
        f"- Source: `{summary_cell(report['src_dir'])}`",
        f"- Mode: `{'strict' if report['strict'] else 'normal'}`",
        f"- Native drift: `{'report-only' if report['knowledge_drift_report'] else 'disabled'}`",
        f"- Result: **{'passed' if report['ok'] else 'failed'}**",
        f"- Issues: {report['issue_count']}", f"- Diagnostics: {len(records)}",
    ]
    if report.get("knowledge_summary"):
        lines.append("- Freshness: " + str(report["knowledge_summary"]["freshness"]))
    if health is not None:
        lines.extend("- " + label + ": " + summary_cell(value) for label, value in ci_health_rows(report, health))
        lines.extend(["", ASSURANCE_DISCLOSURE])
    if issues:
        first = sorted(issues, key=lambda row: (_diagnostic_priority(row["category"], "finding"), _record_order(row)))[0]
        lines.append("- Blocking finding: " + summary_cell(first["message"]))
    groups = diagnostic_groups(records)
    preview = diagnostic_preview(records)
    lines.extend(["", "## Diagnostic summary", "",
                  f"Preview: {preview['returned']} of {preview['total']} emitted diagnostic records; "
                  f"{preview['omitted']} omitted from this preview. "
                  f"Groups shown: {len(preview['groups'])} of {preview['group_total']}.",
                  "Counts describe emitted records, not scan coverage or resolved findings. "
                  "[Complete diagnostic index](#complete-diagnostic-index) and complete rows follow; "
                  "canonical lint/CI JSON retains every original field.", ""])
    for group in preview["groups"]:
        lines.append(f"- `{summary_cell(group['category'])}` / `{summary_cell(group['kind'])}`: "
                     f"{group['total']} records; 1 shown, {group['total'] - 1} omitted; "
                     f"[complete rows](#{_diagnostic_anchor(group)}).")
        row = group["records"][0]
        lines.append("  - " + summary_cell(row["message"]))
        disclosure = _legacy_scope_disclosure(row)
        if disclosure:
            lines.append("  - " + disclosure)
        hint = _display_hint(row, health)
        if hint:
            lines.append("  - Next action (reported hint): " + summary_cell(hint))
    lines.extend(["", "## Issues", ""])
    for row in sorted(issues, key=lambda row: (_diagnostic_priority(row["category"], "finding"), _record_order(row))):
        location = f" (`{row['path']}`)" if row.get("path") else ""
        lines.append(f"- **{row['category']}**{location}: {row['message']}")
    if not issues:
        lines.append("No issues found.")
    lines.extend(["", "## Complete diagnostic index", "",
                  "| Category | Kind | Records | Complete rows |", "|---|---|---:|---|"])
    for group in groups:
        lines.append(f"| `{summary_cell(group['category'])}` | `{summary_cell(group['kind'])}` | "
                     f"{len(group['records'])} | [rows](#{_diagnostic_anchor(group)}) |")
    lines.extend(["", "## Diagnostics", ""])
    for group in groups:
        lines.extend([f'<a id="{_diagnostic_anchor(group)}"></a>', "",
                      f"### `{summary_cell(group['category'])}` / `{summary_cell(group['kind'])}`", ""])
        for row in group["records"]:
            location = f" (`{row['path']}`)" if row.get("path") else ""
            lines.append(f"- **{row['category']}**{location} [{row.get('severity') or 'warning'}]: {row['message']}")
            disclosure = _legacy_scope_disclosure(row)
            if disclosure:
                lines.append("  - " + disclosure)
            hint = _display_hint(row, health)
            if hint is not None:
                lines.append("  - Hint: " + hint)
        lines.append("")
    return "\n".join(lines) + "\n"


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
