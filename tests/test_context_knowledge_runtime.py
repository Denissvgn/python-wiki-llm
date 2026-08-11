"""Focused executable tests for explicit context knowledge selection."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import context_service
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
)
from llm_wiki_cli.services.knowledge_consumption import KnowledgeAvailability
from llm_wiki_cli.services.knowledge_governance import GOVERNANCE_FILENAME
from llm_wiki_cli.services.knowledge_loader import KnowledgeLoadIssue
from llm_wiki_cli.services.knowledge_model import ComputedFreshness
from llm_wiki_cli.services.mcp_server import McpWikiService
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME
from tests.test_knowledge_cmd import _committed_wiki, _run as _run_knowledge
from tests.test_knowledge_queries import _ready_view


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        (
            {
                "protocol": [],
                "budget_tokens": 1,
            },
            "protocol",
        ),
        (
            {
                "protocol": context_service.PROTOCOL_VERSION,
                "budget_tokens": 1,
                "format": [],
            },
            "format",
        ),
        (
            {
                "protocol": context_service.PROTOCOL_VERSION,
                "budget_tokens": 1,
                1: "not-a-field",
            },
            "request",
        ),
        (
            {
                "protocol": context_service.PROTOCOL_VERSION,
                "budget_tokens": 1,
                "filters": {1: "not-a-field"},
            },
            "filters",
        ),
    ],
)
def test_protocol_request_maps_unhashable_and_nonstring_shapes_to_field_errors(
    payload,
    field,
):
    with pytest.raises(context_service.ProtocolRequestError) as caught:
        context_service._validate_protocol_request(payload)

    assert caught.value.field == field


def _broad_result(
    *,
    concepts: list[dict],
    truncated: bool = False,
) -> dict:
    total = len(concepts) + int(truncated)
    return {
        "concepts": concepts,
        "pages": [],
        "relationships": [],
        "relationship_coverage": {
            "availability": "absent",
            "reason": "typed-graph-extension-not-present",
            "schema_version": None,
            "coverage": [],
        },
        "bounds": {
            "concepts": {
                "total": total,
                "returned": len(concepts),
                "truncated": truncated,
            },
            "pages": {"total": 0, "returned": 0, "truncated": False},
            "relationships": {
                "total": 0,
                "returned": 0,
                "truncated": False,
            },
        },
        "truncated": truncated,
    }


def _tree_snapshot(root: Path) -> tuple[list[str], dict[str, bytes]]:
    entries = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    return entries, files


def _context_args(**overrides):
    values = {
        "request": None,
        "src_dir": ".",
        "budget": 32_000,
        "format": "json",
        "focus": "all",
        "output": None,
        "allow_external_src": False,
        "read_only": True,
        "wiki_dir": "docs/llm_wiki",
        "prefer_fresh": False,
        "source_selection": None,
        "knowledge_mode": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class _BroadService:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.calls: list[tuple[dict[str, str], dict[str, int]]] = []

    def broad_context_selection(self, priorities, **limits):
        self.calls.append((dict(priorities), dict(limits)))
        return self.result


def _fake_ready_view(
    freshness_by_locator: dict[str, object] | None = None,
    *,
    snapshot_only: bool = False,
):
    return SimpleNamespace(
        projection_findings=(),
        availability=KnowledgeAvailability.READY,
        reason_code="all-projection-commitments-match",
        freshness_evaluated=freshness_by_locator is not None,
        freshness=(
            None
            if freshness_by_locator is None
            else SimpleNamespace(by_locator=freshness_by_locator)
        ),
        mode=SimpleNamespace(
            value="snapshot-only" if snapshot_only else "evaluate-freshness"
        ),
        surface={"pages": []},
    )


def _fake_unavailable_view(
    availability: KnowledgeAvailability,
    reason: str,
    *,
    issue_code: str | None = None,
    surface: object = None,
):
    findings = (
        ()
        if issue_code is None
        else (
            KnowledgeLoadIssue(
                code=issue_code,
                artifact_path="projection.json",
                message="projection unavailable",
            ),
        )
    )
    return SimpleNamespace(
        projection_findings=findings,
        availability=availability,
        reason_code=reason,
        freshness_evaluated=False,
        freshness=None,
        mode=SimpleNamespace(value="snapshot-only"),
        surface=surface,
    )


def test_off_without_query_constructs_no_surface_or_knowledge_session(
    monkeypatch,
) -> None:
    def unexpected(*_args, **_kwargs):
        pytest.fail("off mode must not construct an enrichment session")

    monkeypatch.setattr(
        context_service,
        "_capture_protocol_enrichment_session",
        unexpected,
    )

    enrichment = context_service._build_protocol_enrichment(
        {},
        {},
        src_root=Path("."),
        wiki_dir="docs/llm_wiki",
        knowledge_mode="off",
        prefer_fresh=True,
    )

    assert enrichment["knowledge"]["status"] == "disabled"
    assert enrichment["knowledge"]["bounds"] == {
        name: {"total": 0, "returned": 0, "truncated": False}
        for name in ("concepts", "pages", "relationships")
    }
    assert enrichment["ranking_policy"]["reason"] == ("knowledge-selection-disabled")


def test_broad_selection_has_independent_bounds_and_strict_wire_projection(
    tmp_path,
) -> None:
    view = _ready_view(tmp_path)
    service = DocumentationGraphQueryService(
        {},
        knowledge_view=view,
        surface_index=view.surface,
    )

    selected = service.broad_context_selection(
        {"src/accounts.py": "high"},
        concept_limit=1,
        page_limit=2,
        relationship_limit=3,
    )

    assert selected["bounds"] == {
        "concepts": {"total": 3, "returned": 1, "truncated": True},
        "pages": {"total": 3, "returned": 2, "truncated": True},
        "relationships": {"total": 10, "returned": 3, "truncated": True},
    }
    assert all(
        set(page)
        == {
            "kind",
            "id",
            "title",
            "canonical_path",
            "source_path",
            "role",
            "mcp_uri",
        }
        for page in selected["pages"]
    )
    encoded = json.dumps(selected, sort_keys=True)
    for forbidden in (
        "raw_target",
        "normalized_target",
        "lifecycle_events",
        "reviews",
        "machine_verification",
        "samples",
        "source_content_hash",
        "limitations",
    ):
        assert f'"{forbidden}"' not in encoded


def test_ready_without_relevant_selection_is_qualified_fallback_for_required() -> None:
    service = _BroadService(_broad_result(concepts=[]))

    knowledge = context_service._build_explicit_knowledge_response(
        "required",
        _fake_ready_view(),
        service,
        {"src/unmapped.py": "high"},
    )

    assert knowledge["status"] == "fallback"
    assert knowledge["availability"] == "ready"
    assert knowledge["reason"] == "no-relevant-native-selection"
    assert knowledge["fallback"]["used"] is True


def test_explicit_freshness_policy_requires_an_actual_current_rank() -> None:
    knowledge = {"mode": "auto", "status": "selected"}

    unavailable = context_service._explicit_freshness_ranking_policy(
        knowledge,
        {"src/stale.py": 1},
        True,
    )
    applied = context_service._explicit_freshness_ranking_policy(
        knowledge,
        {"src/current.py": 0, "src/stale.py": 1},
        True,
    )

    assert unavailable["applied"] is False
    assert unavailable["reason"] == "qualified-freshness-ranks-unavailable"
    assert applied["applied"] is True
    assert applied["reason"] == "same-tier-budget-pressure"


def test_markdown_renders_every_explicit_selection_collection() -> None:
    payload = {
        "budget": 100,
        "used": 0,
        "files": {},
        "knowledge": {
            "mode": "auto",
            "status": "selected",
            "availability": "ready",
            "reason": "knowledge-ready",
            "selected": True,
            "freshness_evaluated": True,
            "bounds": {
                name: {"total": 1, "returned": 1, "truncated": False}
                for name in ("concepts", "pages", "relationships")
            },
            "fallback": {
                "used": False,
                "evidence": [],
                "reason": "knowledge-selected",
            },
            "selection": {
                "concepts": [
                    {
                        "locator": "llm-wiki://entities/User",
                        "freshness": {"state": "current"},
                    }
                ],
                "pages": [
                    {
                        "canonical_path": "entities/User.md",
                        "source_path": "src/accounts.py",
                    }
                ],
                "relationships": [
                    {
                        "graph": "knowledge",
                        "from": "llm-wiki://entities/User",
                        "kind": "derived_from",
                        "target": {
                            "target_class": "source",
                            "source_path": "src/accounts.py",
                        },
                        "resolution": "resolved",
                    }
                ],
                "relationship_coverage": {
                    "availability": "absent",
                    "reason": "typed-graph-extension-not-present",
                },
            },
        },
    }

    rendered = context_service._render_markdown(payload)

    assert "### Selected Concepts" in rendered
    assert "### Selected Pages" in rendered
    assert "### Selected Relationships" in rendered
    assert "entities/User.md" in rendered
    assert "derived_from" in rendered


def test_qualifier_precedence_and_source_change_use_only_returned_concepts() -> None:
    selected_locator = "llm-wiki://entities/Selected"
    unrelated_locator = "llm-wiki://entities/Unrelated"
    current = SimpleNamespace(state=ComputedFreshness.CURRENT)
    changed = SimpleNamespace(state=ComputedFreshness.SOURCE_CHANGED)
    view = _fake_ready_view(
        {
            selected_locator: current,
            unrelated_locator: changed,
        }
    )
    selected_concept = {
        "locator": selected_locator,
        "freshness": {"state": ComputedFreshness.CURRENT.value},
    }
    service = _BroadService(_broad_result(concepts=[selected_concept]))

    knowledge = context_service._build_explicit_knowledge_response(
        "auto",
        view,
        service,
        {"src/selected.py": "high"},
    )

    assert knowledge["reason"] == "knowledge-ready"

    selected_concept["freshness"]["state"] = ComputedFreshness.SOURCE_CHANGED.value
    assert (
        context_service._build_explicit_knowledge_response(
            "auto",
            view,
            service,
            {"src/selected.py": "high"},
        )["reason"]
        == "knowledge-source-changed"
    )

    truncated = _BroadService(
        _broad_result(
            concepts=[selected_concept],
            truncated=True,
        )
    )
    assert (
        context_service._build_explicit_knowledge_response(
            "auto",
            view,
            truncated,
            {"src/selected.py": "high"},
        )["reason"]
        == "knowledge-results-truncated"
    )


def test_snapshot_only_ready_selection_is_explicitly_qualified() -> None:
    concept = {
        "locator": "llm-wiki://entities/Selected",
        "freshness": {
            "state": "not-evaluated",
            "reason": "live-evaluation-not-performed",
            "live_comparison_performed": False,
        },
    }

    knowledge = context_service._build_explicit_knowledge_response(
        "required",
        _fake_ready_view(snapshot_only=True),
        _BroadService(_broad_result(concepts=[concept])),
        {"src/selected.py": "high"},
    )

    assert knowledge["status"] == "selected"
    assert knowledge["availability"] == "ready"
    assert knowledge["reason"] == "knowledge-snapshot-only"
    assert knowledge["freshness_evaluated"] is False


def test_incompatible_basis_rejects_projection_without_querying_it() -> None:
    service = _BroadService(
        _broad_result(concepts=[{"locator": "llm-wiki://entities/User"}])
    )

    auto = context_service._build_explicit_knowledge_response(
        "auto",
        _fake_ready_view(),
        service,
        {"src/accounts.py": "high"},
        basis_incompatible=True,
    )

    assert service.calls == []
    assert auto["status"] == "fallback"
    assert auto["availability"] == "degraded"
    assert auto["reason"] == "knowledge-basis-incompatible"

    with pytest.raises(context_service.KnowledgeRequiredUnavailableError) as required:
        context_service._build_explicit_knowledge_response(
            "required",
            _fake_ready_view(),
            service,
            {"src/accounts.py": "high"},
            basis_incompatible=True,
        )
    assert service.calls == []
    assert required.value.reason == "knowledge-basis-incompatible"


def test_required_governance_restore_error_is_stable_and_shell_quoted() -> None:
    view = _fake_ready_view()
    view.projection_findings = (
        KnowledgeLoadIssue(
            code="governance-missing",
            artifact_path=".llm-wiki-governance.json",
            message="governance projection is missing",
        ),
    )

    with pytest.raises(context_service.KnowledgeRequiredUnavailableError) as caught:
        context_service._build_explicit_knowledge_response(
            "required",
            view,
            _BroadService(_broad_result(concepts=[])),
            {},
            src_dir="source tree",
            wiki_dir="wiki tree",
        )

    error = caught.value
    assert error.code == "knowledge-required-unavailable"
    assert error.reason == "governance-missing"
    assert error.details["error"]["mutation_permitted"] is False
    assert error.details["error"]["recovery_command"] == (
        "restore 'wiki tree/.llm-wiki-governance.json' from version control "
        "or an owner-approved backup"
    )


@pytest.mark.parametrize(
    ("view", "expected_availability", "expected_reason", "expected_evidence"),
    [
        (
            _fake_unavailable_view(
                KnowledgeAvailability.ABSENT,
                "knowledge-projection-not-present",
                surface={"pages": []},
            ),
            "absent",
            "knowledge-projection-not-present",
            [
                "independently-validated-surface",
                "markdown",
                "targeted-source-or-runtime",
            ],
        ),
        (
            _fake_unavailable_view(
                KnowledgeAvailability.DEGRADED,
                "policy-selected-surface-only-fallback-after-mixed-snapshot",
                surface={"pages": []},
            ),
            "degraded",
            "policy-selected-surface-only-fallback-after-mixed-snapshot",
            [
                "independently-validated-surface",
                "markdown",
                "targeted-source-or-runtime",
            ],
        ),
        (
            _fake_unavailable_view(
                KnowledgeAvailability.DEGRADED,
                "policy-selected-surface-only-fallback-after-invalid",
                surface={"pages": []},
            ),
            "degraded",
            "policy-selected-surface-only-fallback-after-invalid",
            [
                "independently-validated-surface",
                "markdown",
                "targeted-source-or-runtime",
            ],
        ),
        (
            _fake_unavailable_view(
                KnowledgeAvailability.UNSUPPORTED,
                "knowledge-schema-version-unsupported",
            ),
            "unsupported",
            "knowledge-schema-version-unsupported",
            ["markdown", "targeted-source-or-runtime"],
        ),
        (
            _fake_unavailable_view(
                KnowledgeAvailability.DEGRADED,
                "policy-selected-surface-only-fallback-after-invalid",
                issue_code="surface-invalid",
                surface={"pages": []},
            ),
            "degraded",
            "surface-validation-failed",
            ["markdown", "targeted-source-or-runtime"],
        ),
    ],
)
def test_auto_and_required_unavailable_states_share_stable_fallback_error_shape(
    view,
    expected_availability: str,
    expected_reason: str,
    expected_evidence: list[str],
) -> None:
    auto_service = _BroadService(_broad_result(concepts=[]))
    auto = context_service._build_explicit_knowledge_response(
        "auto",
        view,
        auto_service,
        {},
        src_dir="source tree",
        wiki_dir="wiki tree",
    )

    assert auto["status"] == "fallback"
    assert auto["availability"] == expected_availability
    assert auto["reason"] == expected_reason
    assert auto["selected"] is False
    assert "selection" not in auto
    assert auto["fallback"] == {
        "used": True,
        "evidence": expected_evidence,
        "reason": expected_reason,
    }
    assert auto_service.calls == []

    required_service = _BroadService(_broad_result(concepts=[]))
    with pytest.raises(context_service.KnowledgeRequiredUnavailableError) as required:
        context_service._build_explicit_knowledge_response(
            "required",
            view,
            required_service,
            {},
            src_dir="source tree",
            wiki_dir="wiki tree",
        )
    assert required.value.availability == expected_availability
    assert required.value.reason == expected_reason
    assert required.value.details["error"]["fallback_evidence"] == (expected_evidence)
    recovery_command = required.value.details["error"]["recovery_command"]
    sync_command = "llm-wiki sync --src-dir 'source tree' --wiki-dir 'wiki tree'"
    if expected_reason == "knowledge-schema-version-unsupported":
        assert "environment's package manager" in recovery_command
        assert "llm-wiki --version" in recovery_command
        assert recovery_command.endswith(f"then run {sync_command}")
        assert recovery_command != sync_command
        assert "llm-wiki upgrade" not in recovery_command
    else:
        assert recovery_command == sync_command
    assert required_service.calls == []


def test_invalid_projection_surface_has_consistent_read_only_fallbacks(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    from tests.test_context_packet_knowledge import (
        _materialize_ready_project,
        _request,
    )
    from llm_wiki_cli.services.context_packet import build_qualified_context

    tree, _fixture = _materialize_ready_project(tmp_path, monkeypatch)
    rejected_payload_sentinel = "projection-only-untrusted-detail"
    (tree["wiki_root"] / SURFACE_INDEX_FILENAME).write_text(
        json.dumps(
            {
                "schema_version": 999,
                "untrusted_detail": rejected_payload_sentinel,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    before = _tree_snapshot(tree["root"])

    context_service.run(_context_args(knowledge_mode="auto"))
    cli_payload = json.loads(capsys.readouterr().out)
    api_payload = api.build_context(
        ".",
        focus="all",
        wiki_dir="docs/llm_wiki",
        knowledge_mode="auto",
    )
    mcp_payload = McpWikiService(
        src_dir=".",
        wiki_dir="docs/llm_wiki",
    ).get_context(format="json", focus=["all"], knowledge_mode="auto")
    packet_payload = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    ).to_payload()

    results = (
        cli_payload["knowledge"],
        api_payload["knowledge"],
        mcp_payload["knowledge"],
        packet_payload["response"]["knowledge"],
    )
    for knowledge in results:
        assert knowledge["status"] == "fallback"
        assert knowledge["availability"] == "degraded"
        assert knowledge["reason"] == "surface-validation-failed"
        assert knowledge["selected"] is False
        assert "selection" not in knowledge
        assert knowledge["fallback"] == {
            "used": True,
            "evidence": ["markdown", "targeted-source-or-runtime"],
            "reason": "surface-validation-failed",
        }

    assert "knowledge-degraded" in packet_payload["delivery"]["limitations"]
    assert rejected_payload_sentinel not in json.dumps(
        [cli_payload, api_payload, mcp_payload, packet_payload],
        sort_keys=True,
    )
    assert _tree_snapshot(tree["root"]) == before
    assert not (tree["wiki_root"] / GOVERNANCE_FILENAME).exists()


def test_prefer_fresh_never_crosses_tiers_or_filters_stale_sources() -> None:
    inventory = {
        "high-stale.py": {"classes": [], "functions": [{"name": "high"}]},
        "low-current.py": {"classes": [], "functions": [{"name": "low"}]},
    }
    classification = {
        "high-stale.py": "high",
        "low-current.py": "low",
    }
    high_entry = context_service._build_entry(
        inventory["high-stale.py"],
        "high",
        "deep",
    )
    constrained_budget = context_service._entry_tokens(
        "high-stale.py",
        high_entry,
    )

    constrained, pressure = (
        context_service._build_context_payload_with_freshness_preference(
            inventory,
            classification,
            constrained_budget,
            freshness_rank_by_source={
                "high-stale.py": 1,
                "low-current.py": 0,
            },
        )
    )
    complete, _ = context_service._build_context_payload_with_freshness_preference(
        inventory,
        classification,
        100_000,
        freshness_rank_by_source={
            "high-stale.py": 1,
            "low-current.py": 0,
        },
    )

    assert pressure is True
    assert list(constrained["files"]) == ["high-stale.py"]
    assert constrained["omitted_files"] == ["low-current.py"]
    assert list(complete["files"]) == ["high-stale.py", "low-current.py"]


@pytest.mark.parametrize("mode", ["off", "auto", "required"])
def test_direct_modes_are_read_only_on_real_filesystem(
    tmp_path,
    monkeypatch,
    capsys,
    mode: str,
) -> None:
    (tmp_path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "docs" / "llm_wiki").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    before = _tree_snapshot(tmp_path)

    if mode == "required":
        with pytest.raises(SystemExit) as exited:
            context_service.run(_context_args(knowledge_mode=mode))
        assert exited.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "knowledge-required-unavailable" in captured.err
        assert "knowledge-projection-not-present" in captured.err
    else:
        context_service.run(_context_args(knowledge_mode=mode))
        payload = json.loads(capsys.readouterr().out)
        assert payload["knowledge"]["mode"] == mode
        assert payload["knowledge"]["status"] == (
            "disabled" if mode == "off" else "fallback"
        )

    assert _tree_snapshot(tmp_path) == before
    assert not (tmp_path / "docs" / "llm_wiki" / ".llm-wiki-governance.json").exists()
    assert not (tmp_path / "docs" / "llm_wiki" / ".llm-wiki-agent").exists()


@pytest.mark.parametrize("mode", ["off", "auto", "required"])
def test_raw_protocol_modes_are_read_only_on_real_filesystem(
    tmp_path,
    monkeypatch,
    capsys,
    mode: str,
) -> None:
    (tmp_path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "docs" / "llm_wiki").mkdir(parents=True)
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "protocol": context_service.KNOWLEDGE_PROTOCOL_VERSION,
                "budget_tokens": 32_000,
                "focus": ["all"],
                "format": "json",
                "knowledge_mode": mode,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    before = _tree_snapshot(tmp_path)

    output_path = tmp_path / "required-output.json"
    args = _context_args(
        request=request_path.as_posix(),
        budget=None,
        output=(output_path.as_posix() if mode == "required" else None),
    )
    if mode == "required":
        with pytest.raises(SystemExit) as exited:
            context_service.run(args)
        assert exited.value.code == 1
        captured = capsys.readouterr()
        assert captured.err == ""
        response = json.loads(captured.out)
        assert response["protocol"] == context_service.KNOWLEDGE_PROTOCOL_VERSION
        assert response["ok"] is False
        assert response["error"]["code"] == "knowledge-required-unavailable"
        assert not output_path.exists()
    else:
        context_service.run(args)
        response = json.loads(capsys.readouterr().out)
        assert response["ok"] is True
        assert response["knowledge"]["mode"] == mode

    assert _tree_snapshot(tmp_path) == before
    assert not (tmp_path / "docs" / "llm_wiki" / ".llm-wiki-governance.json").exists()
    assert not (tmp_path / "docs" / "llm_wiki" / ".llm-wiki-agent").exists()


def test_governance_missing_required_mode_is_restore_only_and_read_only(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    root = tmp_path / "checkout"
    wiki = root / "docs" / "llm_wiki"
    _committed_wiki(wiki)
    _run_knowledge(
        [
            "init",
            "--wiki-dir",
            wiki.as_posix(),
            "--bundle-id",
            "kb_context_restore_fixture",
        ]
    )
    capsys.readouterr()
    (wiki / GOVERNANCE_FILENAME).unlink()
    request_path = root / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "protocol": context_service.KNOWLEDGE_PROTOCOL_VERSION,
                "budget_tokens": 32_000,
                "focus": ["all"],
                "format": "json",
                "knowledge_mode": "required",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(root)
    before = _tree_snapshot(root)

    with pytest.raises(SystemExit) as exited:
        context_service.run(_context_args(request=request_path.as_posix(), budget=None))

    assert exited.value.code == 1
    captured = capsys.readouterr()
    assert captured.err == ""
    response = json.loads(captured.out)
    assert response["error"]["reason"] == "governance-missing"
    recovery = response["error"]["recovery_command"]
    assert recovery == (
        f"restore {wiki.as_posix()}/.llm-wiki-governance.json from version control "
        "or an owner-approved backup"
    )
    assert "init" not in recovery
    assert "sync" not in recovery
    assert _tree_snapshot(root) == before
    assert not (wiki / GOVERNANCE_FILENAME).exists()


def test_direct_v2_low_source_budget_preserves_full_native_selection(
    tmp_path,
    monkeypatch,
) -> None:
    from tests.test_context_packet_knowledge import _materialize_ready_project

    _materialize_ready_project(tmp_path, monkeypatch)

    payload, warnings = context_service._build_context(
        ".",
        1,
        "json",
        ["all"],
        {},
        emit_warnings=False,
        wiki_dir="docs/llm_wiki",
        knowledge_mode="auto",
    )

    assert warnings == []
    assert payload["files"] == {}
    knowledge = payload["knowledge"]
    assert knowledge["status"] == "selected"
    assert all(
        knowledge["bounds"][name]["total"] > 0
        and knowledge["bounds"][name]["returned"] > 0
        for name in ("concepts", "pages", "relationships")
    )


def test_v2_markdown_renders_equivalent_bounded_knowledge_disclosures() -> None:
    content = context_service._render_markdown(
        {
            "used": 10,
            "budget": 100,
            "files": {},
            "omitted_files": [],
            "ranking_policy": {
                "requested": True,
                "policy": "current-first",
                "scope": "within-existing-relevance-tier-under-budget-pressure",
                "budget_pressure": True,
                "applied": True,
                "reason": "same-tier-budget-pressure",
            },
            "knowledge": {
                "mode": "auto",
                "status": "selected",
                "availability": "ready",
                "reason": "knowledge-results-truncated",
                "selected": True,
                "freshness_evaluated": True,
                "bounds": {
                    "concepts": {"total": 1, "returned": 1, "truncated": False},
                    "pages": {"total": 0, "returned": 0, "truncated": False},
                    "relationships": {
                        "total": 2,
                        "returned": 1,
                        "truncated": True,
                    },
                },
                "fallback": {
                    "used": True,
                    "evidence": ["markdown"],
                    "reason": "knowledge-results-truncated",
                },
                "selection": {
                    "concepts": [
                        {
                            "locator": "llm-wiki://modules/accounts",
                            "freshness": {
                                "state": "current",
                                "reason": "recorded-basis-matches-live-evaluation",
                                "live_comparison_performed": True,
                            },
                        }
                    ],
                    "pages": [],
                    "relationships": [
                        {
                            "graph": "knowledge",
                            "from": "llm-wiki://modules/accounts",
                            "kind": "links_to",
                            "resolution": "unresolved",
                            "target": {
                                "target_class": "concept",
                                "normalized_target": "../entities/Missing.md",
                            },
                        }
                    ],
                    "relationship_coverage": {
                        "availability": "ready",
                        "reason": "typed-graph-extension-ready",
                        "schema_version": "llm-wiki-typed-graph/v1",
                        "coverage": [
                            {
                                "analyzer": "calls",
                                "observed": 3,
                                "emitted": 2,
                                "omitted": 1,
                                "limit": 2,
                                "truncated": True,
                                "limitations": ["graph/unowned-call"],
                                "limitation_bounds": {
                                    "total": 1,
                                    "returned": 1,
                                    "truncated": False,
                                },
                            }
                        ],
                    },
                },
            },
        }
    )

    for disclosure in (
        "- ranking policy: current-first",
        "- ranking budget pressure: yes",
        "- ranking applied: yes",
        "- ranking reason: same-tier-budget-pressure",
        "- fallback reason: knowledge-results-truncated",
        "freshness reason: `recorded-basis-matches-live-evaluation`",
        "live comparison performed: yes",
        "coordinate=../entities/Missing.md",
        "observed=3, emitted=2, omitted=1, limit=2, truncated=yes",
        "limitations: graph/unowned-call",
        "limitation codes: 1 / 1",
    ):
        assert disclosure in content
    assert "raw_target" not in content
