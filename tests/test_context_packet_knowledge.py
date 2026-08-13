"""Explicit knowledge semantics for canonical Qualified Context Packets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import context_packet
from llm_wiki_cli.services.context_packet import (
    CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION,
    ContextPacketError,
    ContextPacketMalformedError,
    ContextPacketPathPolicyError,
    ContextPacketSourceMutationError,
    ContextPacketUnavailableError,
    build_qualified_context,
    reconcile_context_packet,
    validate_context_packet,
)
from llm_wiki_cli.services.context_service import (
    KnowledgeRequiredUnavailableError,
)
from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts
from llm_wiki_cli.services.knowledge_consumption import load_knowledge_read_view
from llm_wiki_cli.services.mcp_server import McpWikiError, McpWikiService
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION
from tests.knowledge_fixtures import (
    materialize_fixture_tree,
    one_module_two_entities_fixture,
)
from tests.test_knowledge_artifacts import _plan as _knowledge_commit_plan


REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_GOLDEN_PATH = REPO_ROOT / "tests" / "fixtures" / "context-packet-v1.json"
KNOWLEDGE_GOLDEN_PATH = REPO_ROOT / "tests" / "fixtures" / "context-packet-v2.json"


def _request(mode: str, **overrides: Any) -> dict[str, Any]:
    request: dict[str, Any] = {
        "budget_tokens": 32_000,
        "focus": ["all"],
        "format": "json",
        "filters": {},
        "knowledge_mode": mode,
    }
    request.update(overrides)
    return request


def _write_snapshot_project(root: Path) -> None:
    root.mkdir(parents=True)
    (root / "app.py").write_bytes(
        b'def greet(name: str) -> str:\n    return f"Hello {name}"\n'
    )
    wiki = root / "docs" / "llm_wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_bytes(b"# Project index\n")


def _build_absent_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    mode: str = "auto",
    **request_overrides: Any,
):
    root = tmp_path / "project"
    _write_snapshot_project(root)
    monkeypatch.chdir(root)
    return build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request(mode, **request_overrides),
    )


def _materialize_ready_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, Path], Any]:
    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(fixture, tmp_path / "checkout")
    commit_knowledge_artifacts(_knowledge_commit_plan(tree["wiki_root"], fixture))
    monkeypatch.chdir(tree["root"])
    return tree, fixture


def _write_mismatched_source_selection(tree: dict[str, Path]) -> Path:
    profile = tree["root"] / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir(exist_ok=True)
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["src"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    return profile


def _canonical_repack(payload: dict[str, Any]) -> bytes:
    policy_input = {
        key: value
        for key, value in payload.items()
        if key not in {"schema_version", "packet_id", "path_policy"}
    }
    payload["path_policy"] = context_packet._path_policy_receipt(policy_input)
    semantic_body = {key: value for key, value in payload.items() if key != "packet_id"}
    payload["packet_id"] = context_packet._packet_id(semantic_body)
    return context_packet._encode_packet_payload(payload)


def _tree_state(root: Path) -> dict[str, tuple[str, bytes | None]]:
    state: dict[str, tuple[str, bytes | None]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            state[relative] = ("symlink", path.readlink().as_posix().encode())
        elif path.is_dir():
            state[relative] = ("directory", None)
        else:
            state[relative] = ("file", path.read_bytes())
    return state


def test_v2_packet_is_deterministic_and_v1_golden_remains_valid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _build_absent_packet(tmp_path, monkeypatch)
    second = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    )

    assert first.to_bytes() == second.to_bytes()
    assert first.to_bytes() == KNOWLEDGE_GOLDEN_PATH.read_bytes()
    assert first.to_payload()["schema_version"] == (
        CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION
    )
    assert first.to_payload()["request"]["protocol"] == "llm-wiki-context/v2"
    assert validate_context_packet(first.to_bytes()).valid is True

    legacy = validate_context_packet(LEGACY_GOLDEN_PATH.read_bytes()).packet
    assert legacy.to_bytes() == LEGACY_GOLDEN_PATH.read_bytes()
    assert "knowledge_mode" not in legacy.to_payload()["request"]


def test_v2_markdown_packet_retains_structured_knowledge_disclosure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet = _build_absent_packet(
        tmp_path,
        monkeypatch,
        format="markdown",
    )
    response = packet.to_payload()["response"]

    assert "content" in response
    assert "files" not in response
    assert response["knowledge"]["mode"] == "auto"
    assert response["knowledge"]["status"] == "fallback"
    assert validate_context_packet(packet.to_bytes()).packet.to_bytes() == (
        packet.to_bytes()
    )


def test_off_captures_actual_ready_basis_without_native_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)

    def unexpected_selection(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("off mode must not construct a knowledge query service")

    monkeypatch.setattr(
        context_packet,
        "DocumentationGraphQueryService",
        unexpected_selection,
    )
    packet = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("off"),
    )
    payload = packet.to_payload()

    assert payload["response"]["knowledge"] == {
        "mode": "off",
        "status": "disabled",
        "availability": "not-evaluated",
        "reason": "knowledge-selection-disabled",
        "selected": False,
        "freshness_evaluated": False,
        "bounds": {
            name: {"total": 0, "returned": 0, "truncated": False}
            for name in ("concepts", "pages", "relationships")
        },
        "fallback": {
            "used": False,
            "evidence": [],
            "reason": "knowledge-selection-disabled",
        },
    }
    assert payload["basis"]["knowledge"]["state"] == "recorded"
    assert payload["basis"]["knowledge"]["availability"] == "ready"


def test_api_explicit_mode_promotes_supported_protocols_but_rejects_unknown_shapes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    base = _request("auto")
    del base["knowledge_mode"]

    for protocol in (
        context_packet.context_service.PROTOCOL_VERSION,
        context_packet.context_service.KNOWLEDGE_PROTOCOL_VERSION,
    ):
        packet = api.build_qualified_context(
            ".",
            "docs/llm_wiki",
            {**base, "protocol": protocol},
            knowledge_mode="auto",
        )
        assert packet.to_payload()["request"]["protocol"] == (
            context_packet.context_service.KNOWLEDGE_PROTOCOL_VERSION
        )

    for unsupported in ("future/v99", []):
        with pytest.raises(api.InvalidRequestError) as caught:
            api.build_qualified_context(
                ".",
                "docs/llm_wiki",
                {**base, "protocol": unsupported},  # type: ignore[dict-item]
                knowledge_mode="auto",
            )
        assert caught.value.code == "invalid-request"
        assert caught.value.details == {"field": "protocol"}


@pytest.mark.parametrize("mode", ["off", "auto", "required"])
def test_all_packet_modes_are_read_only_on_the_real_filesystem(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    root = tmp_path / "read-only-project"
    _write_snapshot_project(root)
    before = _tree_state(root)
    monkeypatch.chdir(root)

    if mode == "required":
        with pytest.raises(KnowledgeRequiredUnavailableError):
            build_qualified_context(
                ".",
                "docs/llm_wiki",
                _request(mode),
                read_only=True,
            )
    else:
        build_qualified_context(
            ".",
            "docs/llm_wiki",
            _request(mode),
            read_only=True,
        )

    assert _tree_state(root) == before
    wiki = root / "docs" / "llm_wiki"
    assert not (wiki / ".llm-wiki-governance.json").exists()
    assert not (wiki / ".llm-wiki-knowledge.json").exists()
    assert not (wiki / ".llm-wiki-manifest.json").exists()
    assert not (root / ".llm-wiki").exists()


def test_preexisting_wiki_symlink_is_path_policy_rejected_without_target_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "symlink-project"
    _write_snapshot_project(root)
    external = tmp_path / "external-secret.md"
    external.write_bytes(b"# MUST NOT READ\n")
    linked = root / "docs" / "llm_wiki" / "entities" / "Escape.md"
    linked.parent.mkdir()
    linked.symlink_to(external)
    monkeypatch.chdir(root)
    real_read_bytes = Path.read_bytes
    real_read_text = Path.read_text

    def guarded_read_bytes(path: Path) -> bytes:
        if path.resolve() == external.resolve():
            pytest.fail("external symlink target bytes must not be read")
        return real_read_bytes(path)

    def guarded_read_text(path: Path, *args: Any, **kwargs: Any) -> str:
        if path.resolve() == external.resolve():
            pytest.fail("external symlink target text must not be read")
        return real_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)

    with pytest.raises(ContextPacketPathPolicyError) as direct:
        build_qualified_context(".", "docs/llm_wiki", _request("off"))
    assert direct.value.field == "wiki_dir"
    assert "entities/Escape.md" in str(direct.value)

    with pytest.raises(api.PathPolicyError) as python_error:
        api.build_qualified_context(
            ".",
            wiki_dir="docs/llm_wiki",
            knowledge_mode="off",
        )
    assert python_error.value.code == "path-policy-error"
    assert python_error.value.details == {"field": "wiki_dir"}

    with pytest.raises(McpWikiError) as mcp_error:
        McpWikiService(wiki_dir="docs/llm_wiki").get_context_packet(
            knowledge_mode="off"
        )
    assert mcp_error.value.code == "path-policy-error"
    assert mcp_error.value.data == {"field": "wiki_dir"}


def test_unread_noncanonical_wiki_symlink_remains_v1_compatible_but_v2_rejects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "noncanonical-symlink-project"
    _write_snapshot_project(root)
    outside = tmp_path / "outside.svg"
    outside.write_bytes(b"<svg><!-- outside --></svg>\n")
    asset = root / "docs" / "llm_wiki" / "assets" / "link.svg"
    asset.parent.mkdir()
    asset.symlink_to(outside)
    monkeypatch.chdir(root)
    legacy_request = _request("off")
    del legacy_request["knowledge_mode"]

    legacy = build_qualified_context(".", "docs/llm_wiki", legacy_request)
    assert (
        legacy.to_payload()["schema_version"] != CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION
    )

    with pytest.raises(ContextPacketPathPolicyError, match="assets/link.svg"):
        build_qualified_context(".", "docs/llm_wiki", _request("off"))


def test_wiki_symlink_introduced_after_anchor_is_a_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "mutating-wiki-project"
    _write_snapshot_project(root)
    page = root / "docs" / "llm_wiki" / "index.md"
    external = tmp_path / "late-external.md"
    external.write_bytes(b"# external\n")
    monkeypatch.chdir(root)
    real_evaluate = context_packet.evaluate_surface_index

    def mutate_after_surface(*args: Any, **kwargs: Any):
        result = real_evaluate(*args, **kwargs)
        page.unlink()
        page.symlink_to(external)
        return result

    monkeypatch.setattr(
        context_packet,
        "evaluate_surface_index",
        mutate_after_surface,
    )

    with pytest.raises(ContextPacketSourceMutationError) as caught:
        build_qualified_context(".", "docs/llm_wiki", _request("off"))
    assert caught.value.facet == "wiki"


def test_auto_ready_uses_one_captured_view_and_one_bounded_native_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    calls = {"knowledge": 0, "selection": 0}
    real_knowledge = context_packet.context_service._build_context_knowledge_view
    real_selection = (
        context_packet.DocumentationGraphQueryService.broad_context_selection
    )

    def counted_knowledge(*args: Any, **kwargs: Any):
        calls["knowledge"] += 1
        return real_knowledge(*args, **kwargs)

    def counted_selection(self: Any, *args: Any, **kwargs: Any):
        calls["selection"] += 1
        return real_selection(self, *args, **kwargs)

    monkeypatch.setattr(
        context_packet.context_service,
        "_build_context_knowledge_view",
        counted_knowledge,
    )
    monkeypatch.setattr(
        context_packet.DocumentationGraphQueryService,
        "broad_context_selection",
        counted_selection,
    )

    packet = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    )
    knowledge = packet.to_payload()["response"]["knowledge"]

    assert calls == {"knowledge": 1, "selection": 1}
    assert knowledge["status"] == "selected"
    assert knowledge["selected"] is True
    assert knowledge["availability"] == "ready"
    selection = knowledge["selection"]
    limits = {
        "concepts": context_packet.context_service.CONTEXT_KNOWLEDGE_CONCEPT_LIMIT,
        "pages": context_packet.context_service.CONTEXT_KNOWLEDGE_PAGE_LIMIT,
        "relationships": (
            context_packet.context_service.CONTEXT_KNOWLEDGE_RELATIONSHIP_LIMIT
        ),
    }
    for name, limit in limits.items():
        assert len(selection[name]) == knowledge["bounds"][name]["returned"]
        assert len(selection[name]) <= limit
    serialized_selection = json.dumps(selection, sort_keys=True)
    for forbidden in (
        "source_content_hash",
        "concept_observation_hash",
        "analysis_basis_hash",
        "recorded_basis",
        "live_basis",
        "diagnostics",
        "reviews",
    ):
        assert forbidden not in serialized_selection


def test_required_unavailable_uses_configured_paths_and_emits_no_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "configured-source"
    _write_snapshot_project(root)
    configured_wiki = root / "docs" / "llm_wiki"
    monkeypatch.chdir(tmp_path)

    def unexpected_encoding(*_args: Any, **_kwargs: Any) -> bytes:
        raise AssertionError("required failure must not encode a packet")

    monkeypatch.setattr(context_packet, "_encode_packet_payload", unexpected_encoding)
    with pytest.raises(KnowledgeRequiredUnavailableError) as caught:
        build_qualified_context(
            root.as_posix(),
            configured_wiki.as_posix(),
            _request("required"),
            allow_external_src=True,
        )

    error = caught.value.details["error"]
    assert error["code"] == "knowledge-required-unavailable"
    assert error["availability"] == "absent"
    assert error["mutation_permitted"] is False
    assert root.as_posix() in error["recovery_command"]
    assert configured_wiki.as_posix() in error["recovery_command"]
    assert error["recovery_command"].endswith("--allow-external-src")


def test_required_ready_without_relevant_native_selection_is_qualified_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    packet = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("required", filters={"language": "javascript"}),
    )
    response = packet.to_payload()["response"]

    assert response["files"] == {}
    assert response["knowledge"]["status"] == "fallback"
    assert response["knowledge"]["availability"] == "ready"
    assert response["knowledge"]["reason"] == "no-relevant-native-selection"
    assert response["knowledge"]["selected"] is False
    assert "selection" not in response["knowledge"]


def test_auto_source_selection_incompatibility_is_fallback_not_native_query(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree, _fixture = _materialize_ready_project(tmp_path, monkeypatch)
    profile = _write_mismatched_source_selection(tree)

    def unexpected_selection(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("an incompatible projection must not be queried")

    monkeypatch.setattr(
        context_packet.DocumentationGraphQueryService,
        "broad_context_selection",
        unexpected_selection,
    )
    monkeypatch.setattr(
        context_packet,
        "_captured_query_service",
        lambda *_args, **_kwargs: pytest.fail(
            "a rejected projection must not enter a packet query service"
        ),
    )
    packet = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
        source_selection=profile.relative_to(tree["root"]).as_posix(),
    )
    payload = packet.to_payload()

    assert payload["response"]["knowledge"]["status"] == "fallback"
    assert payload["response"]["knowledge"]["availability"] == "degraded"
    assert payload["response"]["knowledge"]["reason"] == (
        "knowledge-basis-incompatible"
    )
    assert payload["response"]["knowledge"]["selected"] is False
    assert payload["basis"]["knowledge"] == {
        "state": "unavailable",
        "availability": "degraded",
        "reason": "knowledge-basis-incompatible",
    }
    assert payload["basis"]["freshness"] == {
        "state": "unevaluated",
        "evaluated": False,
        "disclosure": "unevaluated (knowledge basis incompatible)",
        "reason": "knowledge-basis-incompatible",
    }


def test_required_source_selection_incompatibility_queries_nothing_and_emits_no_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree, _fixture = _materialize_ready_project(tmp_path, monkeypatch)
    profile = _write_mismatched_source_selection(tree)
    monkeypatch.setattr(
        context_packet,
        "_captured_query_service",
        lambda *_args, **_kwargs: pytest.fail(
            "a rejected projection must not enter a packet query service"
        ),
    )
    monkeypatch.setattr(
        context_packet,
        "_encode_packet_payload",
        lambda *_args, **_kwargs: pytest.fail(
            "required incompatibility must not encode a packet"
        ),
    )

    with pytest.raises(KnowledgeRequiredUnavailableError) as caught:
        build_qualified_context(
            ".",
            "docs/llm_wiki",
            _request("required"),
            source_selection=profile.relative_to(tree["root"]).as_posix(),
        )

    assert caught.value.availability == "degraded"
    assert caught.value.reason == "knowledge-basis-incompatible"
    assert (
        "--source-selection .llm-wiki/source-selection.json"
        in caught.value.details["error"]["recovery_command"]
    )
    assert (
        "--allow-external-src" not in caught.value.details["error"]["recovery_command"]
    )


def test_off_tolerates_projection_selection_mismatch_without_querying_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree, _fixture = _materialize_ready_project(tmp_path, monkeypatch)
    profile = _write_mismatched_source_selection(tree)
    monkeypatch.setattr(
        context_packet,
        "_captured_query_service",
        lambda *_args, **_kwargs: pytest.fail("off must not construct a query service"),
    )

    payload = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("off"),
        source_selection=profile.relative_to(tree["root"]).as_posix(),
    ).to_payload()

    assert payload["response"]["knowledge"]["status"] == "disabled"
    assert payload["basis"]["knowledge"]["state"] == "recorded"
    assert payload["basis"]["knowledge"]["availability"] == "ready"


def test_direct_context_mismatch_never_indexes_or_ranks_rejected_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree, _fixture = _materialize_ready_project(tmp_path, monkeypatch)
    profile = _write_mismatched_source_selection(tree)
    real_service = context_packet.context_service.DocumentationGraphQueryService
    service_calls = 0

    def guarded_service(*args: Any, **kwargs: Any):
        nonlocal service_calls
        service_calls += 1
        assert kwargs.get("knowledge_view") is None
        assert kwargs.get("machine_verification") is None
        return real_service(*args, **kwargs)

    monkeypatch.setattr(
        context_packet.context_service,
        "DocumentationGraphQueryService",
        guarded_service,
    )
    monkeypatch.setattr(
        context_packet.context_service,
        "_context_freshness_rank_by_source",
        lambda *_args, **_kwargs: pytest.fail(
            "an incompatible knowledge basis must not produce freshness ranks"
        ),
    )
    selection = profile.relative_to(tree["root"]).as_posix()

    auto = api.build_context(
        ".",
        wiki_dir="docs/llm_wiki",
        focus="all",
        prefer_fresh=True,
        source_selection=selection,
        knowledge_mode="auto",
    )
    off = api.build_context(
        ".",
        wiki_dir="docs/llm_wiki",
        focus="all",
        source_selection=selection,
        knowledge_mode="off",
    )

    assert service_calls == 1
    assert auto["knowledge"]["status"] == "fallback"
    assert auto["knowledge"]["reason"] == "knowledge-basis-incompatible"
    assert auto["ranking_policy"]["reason"] == "knowledge-unavailable"
    assert off["knowledge"]["status"] == "disabled"


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (
            lambda payload: payload["request"].__setitem__("knowledge_mode", "off"),
            "response.knowledge.mode",
        ),
        (
            lambda payload: payload["response"]["knowledge"]["bounds"][
                "concepts"
            ].update({"total": 2, "returned": 2, "truncated": False}),
            "selection.concepts",
        ),
        (
            lambda payload: payload["response"]["knowledge"]["fallback"].__setitem__(
                "used", True
            ),
            "selected-mode semantics",
        ),
        (
            lambda payload: payload["basis"]["generator"].__setitem__(
                "policy_digest", "sha256:" + "0" * 64
            ),
            "basis.generator",
        ),
        (
            lambda payload: payload["response"]["knowledge"]["selection"]["concepts"][
                0
            ].__setitem__("source_content_hash", "sha256:" + "0" * 64),
            "raw projection evidence",
        ),
    ],
)
def test_v2_canonical_validation_rejects_self_consistent_semantic_mutations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate: Callable[[dict[str, Any]], None],
    match: str,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    payload = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    ).to_payload()
    mutate(payload)

    with pytest.raises(ContextPacketError, match=match):
        validate_context_packet(_canonical_repack(payload))


def test_v2_path_policy_rejects_absolute_selected_source_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    payload = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    ).to_payload()
    payload["response"]["knowledge"]["selection"]["concepts"][0]["source_path"] = (
        "/private/source.py"
    )

    with pytest.raises(ContextPacketPathPolicyError, match="repository-relative"):
        _canonical_repack(payload)


def test_v2_selection_rejects_windows_paths_disguised_as_public_uris(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    payload = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    ).to_payload()
    concept = payload["response"]["knowledge"]["selection"]["concepts"][0]
    concept["locator"] = r"C:\private\source.py"
    concept["mcp_uri"] = r"C:\private\source.py"

    with pytest.raises(ContextPacketMalformedError, match="must match the registry"):
        validate_context_packet(_canonical_repack(payload))


def test_snapshot_only_reconciliation_never_promotes_currentness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree, _fixture = _materialize_ready_project(tmp_path, monkeypatch)
    snapshot_view = load_knowledge_read_view(
        tree["wiki_root"],
        snapshot_only=True,
    )
    monkeypatch.setattr(
        context_packet.context_service,
        "_build_context_knowledge_view",
        lambda *_args, **_kwargs: snapshot_view,
    )
    packet = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    )
    knowledge = packet.to_payload()["response"]["knowledge"]

    assert knowledge["reason"] == "knowledge-snapshot-only"
    assert knowledge["freshness_evaluated"] is False
    assert all(
        concept["freshness"]
        == {
            "state": "not-evaluated",
            "reason": "live-evaluation-not-performed",
            "live_comparison_performed": False,
        }
        for concept in knowledge["selection"]["concepts"]
    )
    forged = packet.to_payload()
    forged["response"]["knowledge"]["reason"] = "knowledge-ready"
    with pytest.raises(ContextPacketMalformedError, match="qualifier precedence"):
        validate_context_packet(_canonical_repack(forged))
    for _ in range(2):
        reconciled = reconcile_context_packet(
            packet.to_bytes(),
            ".",
            "docs/llm_wiki",
        )
        assert reconciled.state == "unevaluated"
        assert reconciled.current is None
        assert reconciled.facets["freshness"]["current"] is None


def test_unselected_aggregate_source_change_does_not_requalify_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    payload = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    ).to_payload()
    freshness_basis = payload["basis"]["freshness"]
    counts = freshness_basis["counts"]
    counts["source-changed"] += 1
    freshness_basis["concept_count"] += 1
    freshness_basis["disclosure"] = (
        f"evaluated ({freshness_basis['concept_count']} concepts)"
    )

    validated = validate_context_packet(_canonical_repack(payload))

    assert validated.packet.to_payload()["response"]["knowledge"]["reason"] == (
        "knowledge-ready"
    )


@pytest.mark.parametrize(
    ("mode", "expected_reason"),
    [
        ("off", "knowledge-selection-disabled"),
        ("auto", "no-budget-pressure"),
    ],
)
def test_v2_prefer_fresh_is_ranking_only_and_always_disclosed_when_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    expected_reason: str,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    response = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request(mode, prefer_fresh=True),
    ).to_payload()["response"]

    assert response["ranking_policy"] == {
        "requested": True,
        "policy": "current-first",
        "scope": "within-existing-relevance-tier-under-budget-pressure",
        "budget_pressure": False,
        "applied": False,
        "reason": expected_reason,
    }
    assert response["knowledge"]["status"] == (
        "disabled" if mode == "off" else "selected"
    )


def test_v2_ranking_policy_cannot_forge_budget_pressure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    payload = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto", prefer_fresh=True),
    ).to_payload()
    payload["response"]["ranking_policy"]["budget_pressure"] = True
    payload["response"]["ranking_policy"]["applied"] = True
    payload["response"]["ranking_policy"]["reason"] = "same-tier-budget-pressure"

    with pytest.raises(ContextPacketMalformedError, match="budget_pressure"):
        validate_context_packet(_canonical_repack(payload))


def test_v2_independent_result_caps_are_deterministic_and_disclosed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    monkeypatch.setattr(
        context_packet.context_service,
        "CONTEXT_KNOWLEDGE_CONCEPT_LIMIT",
        1,
    )
    monkeypatch.setattr(
        context_packet.context_service,
        "CONTEXT_KNOWLEDGE_PAGE_LIMIT",
        1,
    )
    monkeypatch.setattr(
        context_packet.context_service,
        "CONTEXT_KNOWLEDGE_RELATIONSHIP_LIMIT",
        1,
    )
    monkeypatch.setattr(context_packet, "_MAX_KNOWLEDGE_CONCEPTS", 1)
    monkeypatch.setattr(context_packet, "_MAX_KNOWLEDGE_PAGES", 1)
    monkeypatch.setattr(context_packet, "_MAX_KNOWLEDGE_RELATIONSHIPS", 1)

    first = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    )
    second = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    )
    knowledge = first.to_payload()["response"]["knowledge"]

    assert first.to_bytes() == second.to_bytes()
    assert knowledge["reason"] == "knowledge-results-truncated"
    assert all(
        bound["returned"] <= 1 and bound["truncated"] is True
        for bound in knowledge["bounds"].values()
    )
    assert (
        "knowledge-results-truncated" in (first.to_payload()["delivery"]["limitations"])
    )


def test_v2_packet_enforces_the_versioned_serialized_size_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet = _build_absent_packet(tmp_path, monkeypatch)
    payload = packet.to_payload()
    payload["response"]["warnings"] = ["x" * context_packet._MAX_TEXT_LENGTH]
    oversized = context_packet._encode_packet_payload(payload)

    assert len(oversized) > context_packet._MAX_KNOWLEDGE_PACKET_BYTES
    with pytest.raises(ContextPacketMalformedError, match="must not exceed"):
        validate_context_packet(oversized)


def test_oversized_off_packet_fails_without_rewriting_disabled_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_snapshot_project(tmp_path / "project")
    monkeypatch.chdir(tmp_path / "project")
    real_success = context_packet.context_service._protocol_success_payload

    def oversized_success(*args: Any, **kwargs: Any):
        response = real_success(*args, **kwargs)
        response["warnings"] = ["x" * context_packet._MAX_TEXT_LENGTH] * 3
        return response

    monkeypatch.setattr(
        context_packet.context_service,
        "_protocol_success_payload",
        oversized_success,
    )

    with pytest.raises(ContextPacketUnavailableError, match="disabled knowledge mode"):
        build_qualified_context(".", "docs/llm_wiki", _request("off"))


def test_v2_selection_is_tail_reduced_before_the_packet_byte_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    real_selection = (
        context_packet.DocumentationGraphQueryService.broad_context_selection
    )

    def oversized_selection(self: Any, *args: Any, **kwargs: Any):
        selected = json.loads(json.dumps(real_selection(self, *args, **kwargs)))
        for item in [*selected["concepts"], *selected["pages"]]:
            item["title"] = "x" * 400_000
        return selected

    monkeypatch.setattr(
        context_packet.DocumentationGraphQueryService,
        "broad_context_selection",
        oversized_selection,
    )

    packet = build_qualified_context(".", "docs/llm_wiki", _request("auto"))
    knowledge = packet.to_payload()["response"]["knowledge"]

    assert len(packet.to_bytes()) <= context_packet._MAX_KNOWLEDGE_PACKET_BYTES
    assert knowledge["status"] == "selected"
    assert knowledge["reason"] == "knowledge-results-truncated"
    assert any(bound["truncated"] for bound in knowledge["bounds"].values())
    assert (
        "knowledge-results-truncated" in packet.to_payload()["delivery"]["limitations"]
    )
    assert validate_context_packet(packet.to_bytes()).valid is True


def test_v2_minimal_oversized_selection_falls_back_or_errors_before_encoding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    real_selection = (
        context_packet.DocumentationGraphQueryService.broad_context_selection
    )

    def minimally_oversized(self: Any, *args: Any, **kwargs: Any):
        selected = json.loads(json.dumps(real_selection(self, *args, **kwargs)))
        for item in selected["concepts"]:
            item["title"] = "x" * context_packet._MAX_TEXT_LENGTH
        return selected

    monkeypatch.setattr(
        context_packet.DocumentationGraphQueryService,
        "broad_context_selection",
        minimally_oversized,
    )

    packet = build_qualified_context(".", "docs/llm_wiki", _request("auto"))
    knowledge = packet.to_payload()["response"]["knowledge"]
    assert len(packet.to_bytes()) <= context_packet._MAX_KNOWLEDGE_PACKET_BYTES
    assert knowledge["status"] == "fallback"
    assert knowledge["availability"] == "degraded"
    assert knowledge["reason"] == "knowledge-result-exceeds-size-limit"

    with pytest.raises(
        KnowledgeRequiredUnavailableError,
        match="knowledge-result-exceeds-size-limit",
    ):
        build_qualified_context(".", "docs/llm_wiki", _request("required"))


def test_v2_markdown_retains_source_priority_binding_for_canonical_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    payload = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto", format="markdown"),
    ).to_payload()
    assert payload["response"]["source_priorities"] == {"src/accounts.py": "high"}
    concepts = payload["response"]["knowledge"]["selection"]["concepts"]
    concepts[0], concepts[1] = concepts[1], concepts[0]

    with pytest.raises(ContextPacketMalformedError, match="canonical relevance-tier"):
        validate_context_packet(_canonical_repack(payload))


def test_v2_low_source_budget_keeps_full_native_relevance_and_totals(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)

    payload = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto", budget_tokens=1),
    ).to_payload()
    response = payload["response"]
    knowledge = response["knowledge"]

    assert response["files"] == {}
    assert response["source_priorities"] == {"src/accounts.py": "high"}
    assert knowledge["status"] == "selected"
    assert knowledge["bounds"]["concepts"]["total"] > 0
    assert knowledge["bounds"]["pages"]["total"] > 0
    assert knowledge["bounds"]["relationships"]["total"] > 0
    assert all(
        knowledge["bounds"][name]["returned"] > 0
        for name in ("concepts", "pages", "relationships")
    )
    assert validate_context_packet(_canonical_repack(payload)).valid is True


def test_v2_rejects_noncanonical_request_defaults_and_focus_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    packet = _build_absent_packet(
        tmp_path,
        monkeypatch,
        focus=["changed", "neighbors"],
    )
    missing_default = packet.to_payload()
    del missing_default["request"]["format"]
    with pytest.raises(ContextPacketMalformedError, match="canonical normalized"):
        validate_context_packet(_canonical_repack(missing_default))

    swapped = packet.to_payload()
    swapped["request"]["focus"].reverse()
    with pytest.raises(ContextPacketMalformedError, match="canonical normalized"):
        validate_context_packet(_canonical_repack(swapped))


def test_v2_rejects_duplicate_or_noncanonical_selection_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    packet = build_qualified_context(".", "docs/llm_wiki", _request("auto"))
    payload = packet.to_payload()
    selection = payload["response"]["knowledge"]["selection"]
    selection["relationships"].append(dict(selection["relationships"][0]))
    bound = payload["response"]["knowledge"]["bounds"]["relationships"]
    bound["total"] += 1
    bound["returned"] += 1
    with pytest.raises(ContextPacketMalformedError, match="unique canonical"):
        validate_context_packet(_canonical_repack(payload))

    swapped = packet.to_payload()
    relationships = swapped["response"]["knowledge"]["selection"]["relationships"]
    relationships[0], relationships[1] = relationships[1], relationships[0]
    with pytest.raises(ContextPacketMalformedError, match="canonical incident-concept"):
        validate_context_packet(_canonical_repack(swapped))


def test_v2_relationship_direction_is_bound_to_returned_incident_concepts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    packet = build_qualified_context(".", "docs/llm_wiki", _request("auto"))

    both_payload = packet.to_payload()
    both = next(
        item
        for item in both_payload["response"]["knowledge"]["selection"]["relationships"]
        if item["direction"] == "both"
    )
    both["direction"] = "outbound" if both["graph"] == "knowledge" else "outgoing"
    with pytest.raises(ContextPacketMalformedError, match="both incident concepts"):
        validate_context_packet(_canonical_repack(both_payload))

    external_payload = packet.to_payload()
    external = next(
        item
        for item in external_payload["response"]["knowledge"]["selection"][
            "relationships"
        ]
        if item["graph"] == "knowledge"
        and item["target"].get("target_class") != "concept"
        and item["direction"] == "outbound"
    )
    external["direction"] = "inbound"
    with pytest.raises(ContextPacketMalformedError, match="non-concept target"):
        validate_context_packet(_canonical_repack(external_payload))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda relationship: relationship.update(origin="markdown"),
        lambda relationship: relationship.update(resolution="external"),
        lambda relationship: relationship["target"].update(
            external_uri="https://example.invalid/extra"
        ),
    ],
)
def test_v2_rejects_cross_field_invalid_derived_relationships(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    payload = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    ).to_payload()
    relationship = next(
        item
        for item in payload["response"]["knowledge"]["selection"]["relationships"]
        if item["kind"] == "derived_from"
    )
    mutate(relationship)

    with pytest.raises(
        ContextPacketMalformedError,
        match="derived_from|exactly one",
    ):
        validate_context_packet(_canonical_repack(payload))


@pytest.mark.parametrize(
    ("target_class", "uri"),
    [
        ("external", "mailto:support@example.invalid"),
        ("mail", "https://example.invalid/reference"),
    ],
)
def test_v2_external_relationship_scheme_matches_target_class(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target_class: str,
    uri: str,
) -> None:
    _materialize_ready_project(tmp_path, monkeypatch)
    payload = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request("auto"),
    ).to_payload()
    relationship = next(
        item
        for item in payload["response"]["knowledge"]["selection"]["relationships"]
        if item["resolution"] == "external"
    )
    relationship["target"] = {
        "target_class": target_class,
        "external_uri": uri,
    }

    with pytest.raises(ContextPacketMalformedError, match="URI scheme"):
        validate_context_packet(_canonical_repack(payload))


def test_v2_packet_accepts_bounded_real_typed_external_relationships(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.test_typed_graph_queries import SOURCE_PATH, _service

    typed_root = tmp_path / "typed-view"
    typed_root.mkdir()
    typed_service = _service(typed_root)
    assert typed_service.knowledge_view is not None
    _materialize_ready_project(tmp_path / "packet-project", monkeypatch)
    monkeypatch.setattr(
        context_packet.context_service,
        "_build_context_knowledge_view",
        lambda *_args, **_kwargs: typed_service.knowledge_view,
    )

    packet = build_qualified_context(".", "docs/llm_wiki", _request("auto"))
    relationships = packet.to_payload()["response"]["knowledge"]["selection"][
        "relationships"
    ]
    typed_external = [
        item
        for item in relationships
        if item["graph"] == "typed" and item["resolution"] == "external"
    ]

    assert SOURCE_PATH == "src/accounts.py"
    assert {item["kind"] for item in typed_external} == {"imports", "depends_on"}
    assert all(item["target"]["kind"] == "external-resource" for item in typed_external)
    assert all(item["target"]["resource"] for item in typed_external)
    assert all(context_packet.is_valid_sha256(item["key"]) for item in typed_external)
    assert validate_context_packet(packet.to_bytes()).valid is True
