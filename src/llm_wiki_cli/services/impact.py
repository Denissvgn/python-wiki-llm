"""Deterministic advisory change impact and bounded CI presentations."""

from __future__ import annotations

import hashlib
import html
import json
from dataclasses import asdict

from .api_contracts import build_static_api_contracts
from .change_selection import _git, patch_paths, source_relative_paths
from .dependencies import build_dependency_graph
from .source_snapshot import source_snapshot_matches_current_files
from .review_service import build_analysis, _is_dependency_path

IMPACT_SCHEMA = "llm-wiki-impact/v1"
ANNOTATION_LIMIT = 50
SUMMARY_BYTES = 65536


def build_impact(
    diff_text: str = "",
    *,
    src_dir=".",
    wiki_dir="docs/llm_wiki",
    changes=None,
    source_selection=None,
    helper_cache_dir=None,
) -> dict:
    # Impact depends on the selected paths and captured candidate, not on whether
    # the caller happened to supply patch text alongside equivalent paths.
    selected = changes or {
        "mode": "paths",
        "paths": source_relative_paths(patch_paths(diff_text), src_dir),
    }
    analysis = build_analysis(
        "",
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        changes=selected,
        source_selection=source_selection,
        include_plugins=False,
        helper_cache_dir=helper_cache_dir,
    )
    paths = analysis.changes["paths"]
    graph = build_dependency_graph(
        analysis.inventory,
        project_root=src_dir,
        source_snapshot=analysis.source_snapshot,
    )
    contracts = build_static_api_contracts(analysis.inventory)
    operations = [
        operation
        for operation in contracts.get("operations", [])
        if (operation.get("handler") or {}).get("file") in paths
    ]
    try:
        prefix = _git(src_dir, "rev-parse", "--show-prefix").strip()
    except ValueError:
        prefix = ""
    findings = []
    for finding in analysis.findings:
        value = asdict(finding)
        value["annotation_path"] = prefix + finding.source_path
        value["basis"] = "candidate-source-and-wiki-coverage"
        findings.append(value)
    payload = {
        "schema_version": IMPACT_SCHEMA,
        "advisory": True,
        "changes": {
            key: value for key, value in analysis.changes.items() if key != "request"
        },
        "affected_pages": sorted(
            {page for pages in analysis.page_mapping.values() for page in pages}
        ),
        "page_mapping": analysis.page_mapping,
        "dependencies": {
            "basis": "candidate-static-imports",
            "manifests": sorted(path for path in paths if _is_dependency_path(path)),
            "edges": [
                {"from": source, "to": target}
                for source, target in graph["edges"]
                if source in paths or target in paths
            ],
            "unresolved": [
                item for item in graph["unresolved"] if item["file"] in paths
            ],
        },
        "contracts": {
            "basis": "candidate-static-fastapi",
            "operations": operations,
            "diagnostics": contracts.get("diagnostics", []),
        },
        "findings": findings,
        "limitations": [
            "Affected pages are direct source mappings, including expected pages that may be missing.",
            "Candidate dependencies and contracts are impact hints, not compatibility verdicts.",
            "Deleted sources without retained wiki provenance have unknown page coverage.",
        ],
        "bounds": {
            "annotations": {
                "total": len(findings),
                "returned": min(len(findings), ANNOTATION_LIMIT),
                "omitted": max(0, len(findings) - ANNOTATION_LIMIT),
            }
        },
    }
    if not source_snapshot_matches_current_files(analysis.source_snapshot):
        raise ValueError(
            "Source changed while computing impact; retry with a stable checkout"
        )
    payload["impact_id"] = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
    )
    return payload


def _cell(value, limit=512):
    text = str(value).replace("\r", " ").replace("\n", " ")
    if len(text) > limit:
        text = text[:limit] + "…"
    return html.escape(text).replace("|", "&#124;").replace("`", "&#96;")


def render_summary(impact: dict) -> str:
    findings = impact["findings"]
    lines = [
        "# LLM Wiki change impact",
        "",
        "Advisory review; integrity status is reported separately.",
        "",
        f"Changed paths: {len(impact['changes']['paths'])}. Directly affected pages: {len(impact['affected_pages'])}.",
        f"Dependency edges: {len(impact['dependencies']['edges'])}. Known API operations: {len(impact['contracts']['operations'])}.",
        "",
        "| Severity | Source | Related pages | Follow-up |",
        "|---|---|---|---|",
    ]
    shown = 0
    for finding in findings[:ANNOTATION_LIMIT]:
        row = (
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    finding["severity"],
                    finding["source_path"],
                    ", ".join(finding["wiki_pages"]) or "Unknown / no mapped pages",
                    finding["reason"] + " " + finding["suggested_follow_up"],
                )
            )
            + " |"
        )
        if len(("\n".join(lines + [row])).encode("utf-8")) > SUMMARY_BYTES - 1024:
            break
        lines.append(row)
        shown += 1
    lines += [
        "",
        f"Findings shown: {shown}; omitted: {len(findings) - shown}.",
        f"Annotations omitted: {impact['bounds']['annotations']['omitted']}.",
        "Full details and mapping limitations are recorded in the impact JSON.",
        "",
    ]
    return "\n".join(lines)


def _escape_command(value: str, *, property=False) -> str:
    value = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    if property:
        value = value.replace(":", "%3A").replace(",", "%2C")
    return value


def render_github(impact: dict) -> str:
    lines = []
    for finding in impact["findings"][:ANNOTATION_LIMIT]:
        severity = (
            "warning" if finding["severity"] in {"warning", "error"} else "notice"
        )
        message = finding["reason"] + " " + finding["suggested_follow_up"]
        if len(message) > 2048:
            message = message[:2048] + "… [message shortened; see impact JSON]"
        lines.append(
            f"::{severity} file={_escape_command(finding['annotation_path'], property=True)},"
            f"title=LLM Wiki impact::{_escape_command(message)}"
        )
    omitted = impact["bounds"]["annotations"]["omitted"]
    # A plain log line records the bound without consuming another annotation.
    lines.append(
        f"LLM Wiki impact: {min(len(impact['findings']), ANNOTATION_LIMIT)} annotations; {omitted} omitted."
    )
    return "\n".join(lines) + "\n"
