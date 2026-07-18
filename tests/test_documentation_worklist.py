"""Focused tests for deterministic standalone-documentation worklists."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_wiki_cli.services.documentation_worklist import (
    DOCUMENTATION_WORKLIST_SCHEMA_VERSION,
    IMPORTED_PAGE_CLASSIFICATIONS,
    DocumentationWorklistError,
    build_documentation_worklist,
    classify_imported_semantic_page,
)


FLOW_PLACEHOLDER = (
    "_Describe what this flow does, when it is triggered, and its key side "
    "effects or outputs. Replace this placeholder._"
)
NOTES_PLACEHOLDER = (
    "_Document dynamic or conditional imports and architectural rationale. "
    "Replace this placeholder._"
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _base_wiki(root: Path) -> Path:
    wiki = root / "wiki"
    _write(
        wiki / "index.md",
        "# LLM Wiki Index\n\nUse this landing page to choose the right wiki surface.\n",
    )
    _write(
        wiki / "flows" / "serve.md",
        f"# Serve\n\n**Path:** `src/server.py`\n\n## Behavior\n\n{FLOW_PLACEHOLDER}\n",
    )
    _write(
        wiki / "dependencies.md",
        f"# Dependencies\n\n## Notes\n\n{NOTES_PLACEHOLDER}\n",
    )
    _write(
        wiki / "load-order.md",
        f"# Load order\n\n## Notes\n\n{NOTES_PLACEHOLDER}\n",
    )
    _write(
        wiki / "api-contracts.md",
        "# API contracts\n\n## Operations\n\nGenerated.\n",
    )
    _write(
        wiki / "modules" / "core.md",
        "# core Module\n\n**Path:** `src/core.py`\n\n"
        "## Description\n\n_Auto-generated from `src/core.py`._\n",
    )
    _write(
        wiki / "modules" / "leaf.md",
        "# leaf Module\n\n**Path:** `src/leaf.py`\n\n"
        "## Description\n\n_Auto-generated from `src/leaf.py`._\n",
    )
    _write(
        wiki / ".llm-wiki-surface.json",
        json.dumps(
            {
                "schema_version": "llm-wiki-surface-index/v1",
                "pages": [
                    {
                        "canonical_path": "flows/serve.md",
                        "source_path": "src/server.py",
                    },
                    {
                        "canonical_path": "modules/core.md",
                        "source_path": "src/core.py",
                    },
                    {
                        "canonical_path": "modules/leaf.md",
                        "source_path": "src/leaf.py",
                    },
                ],
                "flows": [
                    {
                        "id": "serve",
                        "category": "http",
                        "entry_point": {"source_path": "src/server.py"},
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
    )
    return wiki


def _by_path(worklist):
    return {item.canonical_path: item for item in worklist.items if item.canonical_path}


def test_worklist_has_stable_ids_order_and_explicit_p2_deferral(tmp_path):
    wiki = _base_wiki(tmp_path)
    metrics = {
        "metrics": {
            "src/leaf.py": {"fan_in": 0, "fan_out": 0},
            "src/core.py": {"fan_in": 5, "fan_out": 1},
        },
        "most_depended_on": ["src/core.py", "src/leaf.py"],
    }
    findings = [
        {"category": "missing_user_guides", "path": "/derived/site/guides"},
        {
            "category": "user_docs_missing_examples",
            "path": "/derived/site/guides",
        },
    ]
    unsupported = {"mystery": {"count": 1, "paths": ["vendor/opaque.mystery"]}}

    first = build_documentation_worklist(
        wiki,
        dependency_metrics=metrics,
        user_profile_findings=findings,
        unsupported_sources=unsupported,
        p1_budget=1,
    )
    second = build_documentation_worklist(
        wiki,
        dependency_metrics={
            "most_depended_on": list(reversed(metrics["most_depended_on"])),
            "metrics": dict(reversed(list(metrics["metrics"].items()))),
        },
        user_profile_findings=reversed(findings),
        unsupported_sources=unsupported,
        p1_budget=1,
    )

    # Metric ranking, not mapping/list insertion order, determines the result.
    assert [
        (item.work_id, item.priority, item.canonical_path) for item in first.items
    ] == [(item.work_id, item.priority, item.canonical_path) for item in second.items]
    assert [item.priority for item in first.items] == sorted(
        [item.priority for item in first.items], key={"P0": 0, "P1": 1, "P2": 2}.get
    )
    pages = _by_path(first)
    assert pages["modules/core.md"].priority == "P1"
    assert pages["modules/leaf.md"].priority == "P2"
    assert pages["modules/leaf.md"].status == "deferred"
    assert pages["modules/leaf.md"].deferred is True
    assert (
        "configured central semantic P1 budget"
        in pages["modules/leaf.md"].deferral_reason
    )
    unsupported_item = next(
        item for item in first.items if item.category == "unsupported_source"
    )
    assert unsupported_item.priority == "P2"
    assert unsupported_item.status == "deferred"
    assert "completeness remain unknown" in unsupported_item.deferral_reason
    assert first.to_dict()["schema_version"] == DOCUMENTATION_WORKLIST_SCHEMA_VERSION


def test_detects_landing_flow_architecture_and_user_profile_signals(tmp_path):
    wiki = _base_wiki(tmp_path)
    worklist = build_documentation_worklist(
        wiki,
        user_profile_findings=[
            {
                "category": "published_placeholder",
                "path": "/derived/site/guides/start.md",
            }
        ],
    )
    pages = _by_path(worklist)

    assert "generic_landing_context" in pages["index.md"].signals
    assert "missing_or_placeholder_flow_behavior" in pages["flows/serve.md"].signals
    assert (
        "missing_or_placeholder_architecture_notes" in pages["dependencies.md"].signals
    )
    assert "missing_or_placeholder_architecture_notes" in pages["load-order.md"].signals
    assert (
        "missing_or_placeholder_architecture_notes" in pages["api-contracts.md"].signals
    )
    user_finding = next(
        item
        for item in worklist.items
        if "user_profile:published_placeholder" in item.signals
    )
    assert user_finding.priority == "P0"
    assert user_finding.canonical_path == "guides/start.md"
    assert all(
        not value.startswith("/derived") for value in user_finding.suggested_context
    )


def test_detects_copied_docstring_only_prose(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Product\n\nA useful product overview.\n")
    _write(
        wiki / "modules" / "service.md",
        "# service Module\n\n**Path:** `src/service.py`\n\n"
        "## Description\n\nHandle user requests through the service boundary.\n",
    )

    worklist = build_documentation_worklist(
        wiki,
        source_inventory={
            "src/service.py": {
                "module_docstring": "Handle user requests through the service boundary."
            }
        },
    )

    item = _by_path(worklist)["modules/service.md"]
    assert item.priority == "P1"
    assert item.signals == ("copied_docstring_only_prose",)
    assert any("dependency_neighborhood" in value for value in item.suggested_context)


def test_imported_classifications_are_exact_and_grounding_is_separate(tmp_path):
    wiki = tmp_path / "wiki"
    _write(
        wiki / "guides" / "grounded.md",
        "# Grounded guide\n\nThis guide explains a verified user workflow with enough detail "
        "to remain useful after import.\n",
    )
    _write(
        wiki / "guides" / "unknown.md",
        "# Existing guide\n\nThis is substantial imported semantic prose whose claims still "
        "need to be checked against authoritative evidence.\n",
    )
    _write(
        wiki / "modules" / "weak.md",
        "# weak Module\n\n## Description\n\n_Auto-generated from `src/weak.py`._\n",
    )

    records = [
        {"canonical_path": "guides/grounded.md", "grounded": True},
        {"canonical_path": "guides/unknown.md"},
        {"canonical_path": "modules/weak.md", "grounded": True},
        {
            "canonical_path": "guides/missing.md",
            "compatible": False,
            "grounded": True,
        },
    ]
    worklist = build_documentation_worklist(wiki, imported_pages=records)
    pages = _by_path(worklist)

    assert set(IMPORTED_PAGE_CLASSIFICATIONS) == {
        "candidate_reuse",
        "needs_grounding",
        "needs_enhancement",
        "incompatible",
    }
    grounded = pages["guides/grounded.md"]
    assert grounded.imported_classification == "candidate_reuse"
    assert grounded.reuse_eligible is True
    assert grounded.grounding_status == "grounded"
    assert grounded.status == "reused"
    unknown = pages["guides/unknown.md"]
    assert unknown.imported_classification == "needs_grounding"
    assert unknown.reuse_eligible is True
    assert unknown.grounding_status == "unknown"
    assert unknown.status == "open"
    weak = pages["modules/weak.md"]
    assert weak.imported_classification == "needs_enhancement"
    assert weak.reuse_eligible is False
    assert weak.grounding_status == "grounded"
    missing = pages["guides/missing.md"]
    assert missing.imported_classification == "incompatible"
    assert missing.reuse_eligible is False
    assert missing.grounding_status == "grounded"
    assert missing.status == "deferred"

    assert classify_imported_semantic_page(wiki, records[1]) == (
        "needs_grounding",
        True,
        "unknown",
    )


def test_entrypoint_evidence_creates_missing_flow_and_boosts_central_page(tmp_path):
    wiki = tmp_path / "wiki"
    _write(
        wiki / "index.md", "# Product\n\nPurposeful project context and navigation.\n"
    )
    _write(
        wiki / "modules" / "api.md",
        "# api Module\n\n**Path:** `src/api.py`\n\n"
        "## Description\n\n_Auto-generated from `src/api.py`._\n",
    )
    _write(
        wiki / "modules" / "leaf.md",
        "# leaf Module\n\n**Path:** `src/leaf.py`\n\n"
        "## Description\n\n_Auto-generated from `src/leaf.py`._\n",
    )

    worklist = build_documentation_worklist(
        wiki,
        entrypoint_evidence=[
            {
                "id": "serve-api",
                "category": "http",
                "source_path": "src/api.py",
                "boundary_effect_count": 3,
            }
        ],
        p1_budget=1,
    )
    pages = _by_path(worklist)

    assert pages["flows/serve-api.md"].priority == "P0"
    assert "missing_flow_page" in pages["flows/serve-api.md"].signals
    assert pages["modules/api.md"].priority == "P1"
    assert pages["modules/api.md"].rank_score > pages["modules/leaf.md"].rank_score
    assert pages["modules/leaf.md"].priority == "P2"


def test_only_boundary_workflows_are_p0_and_api_symbols_remain_explicit_p2(
    tmp_path,
):
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Product\n\nPurposeful project context.\n")
    _write(
        wiki / "flows" / "api-helper.md",
        f"# API helper\n\n## Behavior\n\n{FLOW_PLACEHOLDER}\n",
    )

    worklist = build_documentation_worklist(
        wiki,
        entrypoint_evidence=[
            {
                "id": "api-helper",
                "category": "api",
                "source_path": "src/helpers.py",
                "boundary_effect_count": 0,
            },
            {
                "id": "api-boundary-call",
                "category": "api",
                "source_path": "src/client.py",
                "boundary_effect_count": 1,
            },
            {
                "id": "cli-run",
                "category": "cli",
                "source_path": "src/cli.py",
                "boundary_effect_count": 0,
            },
        ],
    )
    pages = _by_path(worklist)

    ordinary_api = pages["flows/api-helper.md"]
    assert ordinary_api.priority == "P2"
    assert ordinary_api.status == "deferred"
    assert "ordinary reference/API symbol" in ordinary_api.deferral_reason
    assert pages["flows/api-boundary-call.md"].priority == "P0"
    assert pages["flows/cli-run.md"].priority == "P0"


def test_context_and_acceptance_are_bounded(tmp_path):
    wiki = _base_wiki(tmp_path)
    worklist = build_documentation_worklist(
        wiki,
        imported_pages=[{"canonical_path": "flows/serve.md", "grounded": False}],
        max_context_entries=2,
        max_acceptance_checks=2,
    )

    for item in worklist.items:
        assert len(item.suggested_context) <= 2
        assert len(item.acceptance_checks) <= 2
    assert worklist.to_dict()["policy"] == {
        "p1_budget": 30,
        "max_context_entries": 2,
        "max_acceptance_checks": 2,
    }


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("p1_budget", -1, "non-negative integer"),
        ("max_context_entries", 0, "positive integer"),
        ("max_acceptance_checks", True, "positive integer"),
    ],
)
def test_rejects_invalid_budgets(tmp_path, field, value, message):
    wiki = _base_wiki(tmp_path)
    kwargs = {field: value}
    with pytest.raises(DocumentationWorklistError, match=message):
        build_documentation_worklist(wiki, **kwargs)


def test_unsafe_imported_path_is_incompatible_without_reading_outside_wiki(tmp_path):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    outside = tmp_path / "secret.md"
    outside.write_text(
        "# Secret\n\nDo not read this as wiki evidence.\n", encoding="utf-8"
    )

    result = classify_imported_semantic_page(
        wiki,
        {"canonical_path": "../secret.md", "grounded": True},
    )

    assert result == ("incompatible", False, "grounded")


def test_conflicting_import_evidence_fails_closed_and_dot_path_is_preserved(tmp_path):
    wiki = tmp_path / "wiki"
    _write(
        wiki / "modules" / "config.md",
        "# config Module\n\n**Path:** `.config/service.py`\n\n"
        "## Description\n\nThis module owns validated configuration loading and "
        "documents the runtime defaults used by the service.\n",
    )

    worklist = build_documentation_worklist(
        wiki,
        imported_pages=[
            {"canonical_path": "modules/config.md", "grounded": True},
            {
                "canonical_path": "modules/config.md",
                "compatibility": "unsupported",
                "grounded": True,
            },
        ],
    )

    item = _by_path(worklist)["modules/config.md"]
    assert item.source_path == ".config/service.py"
    assert item.imported_classification == "incompatible"
    assert item.reuse_eligible is False
    assert item.status == "deferred"


def test_noncanonical_import_and_unsafe_entrypoint_never_become_output_paths(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "notes.md", "# Notes\n\nSubstantial but noncanonical prose.\n")

    worklist = build_documentation_worklist(
        wiki,
        imported_pages=[{"canonical_path": "notes.md", "grounded": True}],
        entrypoint_evidence=[{"id": "../../escape", "source_path": "src/server.py"}],
    )

    imported = next(
        item for item in worklist.items if item.imported_classification is not None
    )
    unsafe_flow = next(
        item for item in worklist.items if "incompatible_entrypoint_id" in item.signals
    )
    assert imported.imported_classification == "incompatible"
    assert imported.status == "deferred"
    assert unsafe_flow.canonical_path is None
    assert unsafe_flow.priority == "P2"
    assert unsafe_flow.status == "deferred"
