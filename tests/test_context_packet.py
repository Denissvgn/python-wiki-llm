"""Qualified Context Packet canonicalization and read-only reconciliation."""

from __future__ import annotations

import hashlib
import json
import os
import socket
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli.services import context_packet, extraction_service
from llm_wiki_cli.services.context_packet import (
    CONTEXT_PACKET_ASSURANCE_LEVEL,
    CONTEXT_PACKET_RECONCILIATION_POLICY,
    CONTEXT_PACKET_SCHEMA_VERSION,
    ContextPacketMalformedError,
    ContextPacketPathPolicyError,
    ContextPacketSourceMutationError,
    build_context_from_captured_read,
    build_qualified_context,
    capture_context_read,
    compare_context_packet_basis,
    reconcile_context_packet,
    validate_context_packet,
)
from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts
from tests.knowledge_fixtures import (
    materialize_fixture_tree,
    one_module_two_entities_fixture,
)
from tests.test_knowledge_artifacts import _plan as _knowledge_commit_plan
from tests.test_public_docs_vocabulary import scan_public_document


REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = REPO_ROOT / "tests" / "fixtures" / "context-packet-v1.json"
PUBLIC_DOC_PATH = REPO_ROOT / "docs" / "qualified-context-packets.md"


def _request(**overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "budget_tokens": 32_000,
        "focus": ["all"],
        "format": "json",
        "filters": {},
    }
    value.update(overrides)
    return value


def test_context_packet_golden_is_lf_only() -> None:
    assert b"\r" not in GOLDEN_PATH.read_bytes()


def _write_snapshot_project(root: Path, *, opaque_text: bool = False) -> None:
    root.mkdir(parents=True)
    docstring = (
        '"""Routes such as /api/v1, https://example.invalid/a/b, and 8 / 2 '
        'are opaque source text."""\n\n'
        if opaque_text
        else ""
    )
    app_source = (
        docstring
        + "def greet(name: str) -> str:\n"
        + '    return f"Hello {name}"\n'
    )
    app_bytes = app_source.encode("utf-8")
    assert b"\r" not in app_bytes
    (root / "app.py").write_bytes(app_bytes)
    wiki = root / "docs" / "llm_wiki"
    wiki.mkdir(parents=True)
    index_bytes = b"# Project index\n"
    assert b"\r" not in index_bytes
    (wiki / "index.md").write_bytes(index_bytes)


def _build_snapshot_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    opaque_text: bool = False,
    request: dict[str, Any] | None = None,
):
    root = tmp_path / "private-root-token" / "project"
    _write_snapshot_project(root, opaque_text=opaque_text)
    monkeypatch.chdir(root)
    return build_qualified_context(
        ".",
        "docs/llm_wiki",
        request or _request(),
    )


def _canonical_repack(payload: dict[str, Any]) -> bytes:
    semantic_body = {
        key: value for key, value in payload.items() if key != "packet_id"
    }
    payload["packet_id"] = context_packet._packet_id(semantic_body)
    return context_packet._encode_packet_payload(payload)


def _tree_bytes(root: Path) -> dict[str, tuple[str, bytes | None]]:
    records: dict[str, tuple[str, bytes | None]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            records[relative] = ("symlink", os.readlink(path).encode())
        elif path.is_dir():
            records[relative] = ("directory", None)
        else:
            records[relative] = ("file", path.read_bytes())
    return records


def _make_read_only(root: Path) -> list[tuple[Path, int]]:
    original: list[tuple[Path, int]] = []
    for path in sorted(root.rglob("*"), reverse=True):
        mode = path.stat().st_mode & 0o777
        original.append((path, mode))
        path.chmod(0o555 if path.is_dir() else 0o444)
    mode = root.stat().st_mode & 0o777
    original.append((root, mode))
    root.chmod(0o555)
    return original


def _restore_modes(values: list[tuple[Path, int]]) -> None:
    for path, mode in reversed(values):
        path.chmod(mode)


def test_packet_is_byte_stable_immutable_and_matches_cross_platform_golden(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    first = _build_snapshot_packet(tmp_path, monkeypatch)
    second = build_qualified_context(".", "docs/llm_wiki", _request())

    assert first.to_bytes() == second.to_bytes()
    assert first.to_bytes() == GOLDEN_PATH.read_bytes()
    assert first.to_bytes().endswith(b"\n")
    assert b"\r" not in first.to_bytes()
    assert first.to_bytes() == (
        json.dumps(
            json.loads(first.to_bytes()),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )

    mutable = first.to_payload()
    mutable["response"]["used_tokens"] = -1
    assert first.to_payload()["response"]["used_tokens"] >= 0
    with pytest.raises(TypeError):
        first._payload["packet_id"] = "changed"  # type: ignore[index]

    semantic_body = {
        key: value
        for key, value in first.to_payload().items()
        if key != "packet_id"
    }
    expected_id = "sha256:" + hashlib.sha256(
        b"llm-wiki-qualified-context-packet/v1\x00"
        + json.dumps(
            semantic_body,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    assert first.packet_id == expected_id


def test_packet_binds_snapshot_request_response_generator_and_limitations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    packet = _build_snapshot_packet(tmp_path, monkeypatch)
    payload = packet.to_payload()

    assert payload["schema_version"] == CONTEXT_PACKET_SCHEMA_VERSION
    assert payload["assurance"] == {
        "level": CONTEXT_PACKET_ASSURANCE_LEVEL,
        "scope": "canonical-packet-content",
    }
    assert payload["request"] == {
        "protocol": "llm-wiki-context/v1",
        "budget_tokens": 32_000,
        "focus": ["all"],
        "format": "json",
        "filters": {},
        "prefer_fresh": False,
    }
    assert payload["response"]["protocol"] == payload["request"]["protocol"]
    assert payload["response"]["files"]
    assert payload["basis"]["source_snapshot"]["input_count"] == 1
    assert payload["basis"]["repository"] == {
        "state": "unavailable",
        "reason": "native-knowledge-envelope-unavailable",
    }
    assert payload["basis"]["knowledge"] == {
        "state": "unavailable",
        "availability": "absent",
        "reason": "knowledge-projection-not-present",
    }
    assert payload["basis"]["freshness"] == {
        "state": "unevaluated",
        "evaluated": False,
        "disclosure": "unevaluated (snapshot-only read)",
        "reason": "snapshot-only-read",
    }
    assert payload["delivery"]["limitations"] == [
        "freshness-not-evaluated",
        "knowledge-absent",
    ]
    assert payload["path_policy"]["final_scan"] == "passed"
    assert payload["path_policy"]["finding_counts"]["rejected"] == 0
    assert payload["path_policy"]["limitations"] == [
        "does-not-establish-absence-of-arbitrary-sensitive-content"
    ]


def test_explicit_empty_request_is_rejected_instead_of_defaulted() -> None:
    with pytest.raises(
        context_packet.context_service.ProtocolRequestError
    ) as caught:
        build_qualified_context(".", "docs/llm_wiki", {})

    assert caught.value.field == "budget_tokens"


def test_structural_validation_is_strict_and_never_claims_live_currentness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    packet = _build_snapshot_packet(tmp_path, monkeypatch)
    result = validate_context_packet(packet.to_bytes())

    assert result.valid is True
    assert result.packet_id == packet.packet_id
    assert result.packet.to_bytes() == packet.to_bytes()
    assert result.to_payload()["lineage"] == {"state": "valid"}
    assert result.to_payload()["availability"] == {
        "state": "declared",
        "value": "absent",
    }
    assert result.to_payload()["freshness"] == {
        "state": "unevaluated",
        "evaluated": False,
        "reason": "structural-validation-has-no-live-basis",
    }


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: raw[:-1],
        lambda raw: b" " + raw,
        lambda raw: raw.replace(b"{", b"{\n", 1),
        lambda _raw: b'{"duplicate":1,"duplicate":2}\n',
        lambda _raw: b'{"value":NaN}\n',
        lambda _raw: b'{"value":"\\ud800"}\n',
        lambda _raw: b"\xef\xbb\xbf{}\n",
        lambda _raw: b"\xff\n",
    ],
)
def test_strict_parser_rejects_truncated_noncanonical_duplicate_and_invalid_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation,
):
    packet = _build_snapshot_packet(tmp_path, monkeypatch)

    with pytest.raises(ContextPacketMalformedError):
        validate_context_packet(mutation(packet.to_bytes()))


@pytest.mark.parametrize(
    ("limit_name", "limit_value", "message"),
    [
        ("_MAX_PACKET_BYTES", 1, "must not exceed"),
        ("_MAX_JSON_DEPTH", 1, "depth limit"),
        ("_MAX_JSON_ITEMS", 1, "item limit"),
        ("_MAX_TEXT_LENGTH", 1, "text limit"),
    ],
)
def test_strict_parser_enforces_resource_limits_before_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    limit_name: str,
    limit_value: int,
    message: str,
):
    packet = _build_snapshot_packet(tmp_path, monkeypatch)
    monkeypatch.setattr(context_packet, limit_name, limit_value)

    with pytest.raises(ContextPacketMalformedError, match=message):
        validate_context_packet(packet.to_bytes())


def test_digest_rejects_semantic_mutation_and_transplanted_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    packet = _build_snapshot_packet(tmp_path, monkeypatch)
    payload = packet.to_payload()
    payload["response"]["used_tokens"] += 1
    mutated = context_packet._encode_packet_payload(payload)

    with pytest.raises(ContextPacketMalformedError, match="packet_id"):
        validate_context_packet(mutated)

    other = packet.to_payload()
    other["packet_id"] = "sha256:" + "0" * 64
    with pytest.raises(ContextPacketMalformedError, match="packet_id"):
        validate_context_packet(context_packet._encode_packet_payload(other))


@pytest.mark.parametrize(
    ("mutate", "stale_facet"),
    [
        (
            lambda payload: payload["basis"]["source_snapshot"].__setitem__(
                "identity",
                "sha256:" + "0" * 64,
            ),
            "source_snapshot",
        ),
        (
            lambda payload: payload["basis"]["generator"].__setitem__(
                "version",
                "0.0.0-substituted",
            ),
            "generator",
        ),
        (
            lambda payload: payload["response"].__setitem__(
                "used_tokens",
                payload["response"]["used_tokens"] + 1,
            ),
            "context_response",
        ),
    ],
)
def test_self_consistent_substitution_is_structurally_valid_but_live_stale(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate,
    stale_facet: str,
):
    packet = _build_snapshot_packet(tmp_path, monkeypatch)
    substituted = packet.to_payload()
    mutate(substituted)
    raw = _canonical_repack(substituted)

    assert validate_context_packet(raw).valid is True
    reconciled = reconcile_context_packet(raw, ".", "docs/llm_wiki")
    assert reconciled.state == "stale"
    assert reconciled.current is False
    assert reconciled.facets[stale_facet]["current"] is False


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("schema_version", "llm-wiki-qualified-context-packet/v2", "schema_version"),
        ("assurance", {"level": "owner-resistant", "scope": "canonical-packet-content"}, "assurance.level"),
    ],
)
def test_unknown_schema_and_unsupported_assurance_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: Any,
    match: str,
):
    packet = _build_snapshot_packet(tmp_path, monkeypatch)
    payload = packet.to_payload()
    payload[field] = value

    with pytest.raises(ContextPacketMalformedError, match=match):
        validate_context_packet(_canonical_repack(payload))


def test_path_policy_rejects_structural_absolute_path_and_forged_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    packet = _build_snapshot_packet(tmp_path, monkeypatch)
    absolute = packet.to_payload()
    file_value = absolute["response"]["files"].pop("app.py")
    absolute["response"]["files"]["/private/source/app.py"] = file_value
    with pytest.raises(ContextPacketPathPolicyError, match="repository-relative"):
        validate_context_packet(_canonical_repack(absolute))

    forged = packet.to_payload()
    forged["path_policy"]["field_counts"]["opaque_values"] += 1
    with pytest.raises(ContextPacketPathPolicyError, match="classified"):
        validate_context_packet(_canonical_repack(forged))


def test_typed_path_policy_preserves_opaque_slash_like_source_text_and_hides_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    packet = _build_snapshot_packet(tmp_path, monkeypatch, opaque_text=True)
    raw = packet.to_bytes()

    assert b"/api/v1" in raw
    assert b"https://example.invalid/a/b" in raw
    assert b"8 / 2" in raw
    assert str(tmp_path).encode() not in raw
    assert str(Path.cwd()).encode() not in raw
    assert validate_context_packet(raw).path_policy == "valid"


def test_prefer_fresh_policy_and_order_match_the_existing_context_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    packet = _build_snapshot_packet(
        tmp_path,
        monkeypatch,
        request=_request(prefer_fresh=True),
    )
    payload = packet.to_payload()

    assert payload["request"]["prefer_fresh"] is True
    assert payload["response"]["prefer_fresh"] is True
    assert payload["response"]["ranking_policy"] == {
        "name": "relevance-then-current-freshness",
        "prefer_fresh": True,
        "scope": "within-relevance-tiers",
        "freshness_evaluated": False,
        "budget_pressure": False,
        "applied": False,
        "filters_stale_content": False,
    }


def test_builder_uses_one_inventory_surface_and_knowledge_view(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    root = tmp_path / "project"
    _write_snapshot_project(root)
    monkeypatch.chdir(root)
    calls = {"inventory": 0, "surface": 0, "knowledge": 0}
    real_inventory = context_packet.context_service.get_inventory
    real_surface = context_packet.evaluate_surface_index
    real_knowledge = context_packet.context_service._build_context_knowledge_view

    def counted_inventory(*args, **kwargs):
        calls["inventory"] += 1
        return real_inventory(*args, **kwargs)

    def counted_surface(*args, **kwargs):
        calls["surface"] += 1
        return real_surface(*args, **kwargs)

    def counted_knowledge(*args, **kwargs):
        calls["knowledge"] += 1
        return real_knowledge(*args, **kwargs)

    monkeypatch.setattr(
        context_packet.context_service,
        "get_inventory",
        counted_inventory,
    )
    monkeypatch.setattr(context_packet, "evaluate_surface_index", counted_surface)
    monkeypatch.setattr(
        context_packet.context_service,
        "_build_context_knowledge_view",
        counted_knowledge,
    )

    packet = build_qualified_context(".", "docs/llm_wiki", _request())

    assert calls == {"inventory": 1, "surface": 1, "knowledge": 1}
    assert packet.to_payload()["response"]["files"]


def test_packet_construction_does_not_load_project_extractor_plugins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    root = tmp_path / "project"
    _write_snapshot_project(root)
    monkeypatch.chdir(root)

    def unexpected_plugin_registry():
        raise AssertionError("packet construction must not load source plugins")

    monkeypatch.setattr(
        extraction_service,
        "get_extractor_registry",
        unexpected_plugin_registry,
    )

    packet = build_qualified_context(".", "docs/llm_wiki", _request())

    assert validate_context_packet(packet.to_bytes()).valid is True


def test_captured_context_builder_performs_no_second_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    root = tmp_path / "project"
    _write_snapshot_project(root)
    monkeypatch.chdir(root)
    captured = capture_context_read(".", "docs/llm_wiki")

    def unexpected(*_args, **_kwargs):
        raise AssertionError("captured response attempted another semantic read")

    monkeypatch.setattr(context_packet.context_service, "get_inventory", unexpected)
    monkeypatch.setattr(context_packet, "evaluate_surface_index", unexpected)
    monkeypatch.setattr(
        context_packet.context_service,
        "_build_context_knowledge_view",
        unexpected,
    )

    payload, warnings = build_context_from_captured_read(captured, _request())

    assert payload["files"]
    assert warnings == []


@pytest.mark.parametrize("facet", ["source", "wiki"])
def test_mutation_before_final_encoding_aborts_without_returning_a_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    facet: str,
):
    root = tmp_path / "project"
    _write_snapshot_project(root)
    monkeypatch.chdir(root)
    real_build = context_packet.build_context_from_captured_read

    def mutate_after_response(captured, request):
        result = real_build(captured, request)
        target = (
            root / "app.py"
            if facet == "source"
            else root / "docs" / "llm_wiki" / "index.md"
        )
        target.write_text(target.read_text(encoding="utf-8") + "\nchanged\n")
        return result

    monkeypatch.setattr(
        context_packet,
        "build_context_from_captured_read",
        mutate_after_response,
    )

    with pytest.raises(ContextPacketSourceMutationError, match=facet):
        build_qualified_context(".", "docs/llm_wiki", _request())


def test_malformed_packet_fails_before_any_live_read(
    monkeypatch: pytest.MonkeyPatch,
):
    def unexpected(*_args, **_kwargs):
        raise AssertionError("live read ran before structural validation")

    monkeypatch.setattr(context_packet, "build_qualified_context", unexpected)

    with pytest.raises(ContextPacketMalformedError):
        reconcile_context_packet(b'{"not":"a packet"}\n')


def test_reconciliation_result_requires_complete_coherent_official_facets():
    packet_id = "sha256:" + "a" * 64
    facets = {
        name: {
            "matches_expected": True,
            "current": True,
            "state": "current",
            "reason": "live-facet-matches-packet",
        }
        for name in context_packet._RECONCILIATION_FACETS
    }

    with pytest.raises(TypeError, match="returned by reconcile_context_packet"):
        context_packet.ContextPacketReconciliation()
    with pytest.raises(ValueError, match="complete.*policy"):
        context_packet.ContextPacketReconciliation._from_official_read(
            packet_id=packet_id,
            policy="caller-policy",
            state="current",
            current=True,
            facets=facets,
        )
    with pytest.raises(ValueError, match=r"facets\.availability is required"):
        context_packet.ContextPacketReconciliation._from_official_read(
            packet_id=packet_id,
            policy=CONTEXT_PACKET_RECONCILIATION_POLICY,
            state="current",
            current=True,
            facets={
                name: finding
                for name, finding in facets.items()
                if name != "availability"
            },
        )
    with pytest.raises(ValueError, match="aggregate state"):
        context_packet.ContextPacketReconciliation._from_official_read(
            packet_id=packet_id,
            policy=CONTEXT_PACKET_RECONCILIATION_POLICY,
            state="stale",
            current=False,
            facets=facets,
        )


def test_arbitrary_basis_comparison_never_claims_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    packet = _build_snapshot_packet(tmp_path, monkeypatch)
    basis = packet.to_payload()["basis"]

    matching = compare_context_packet_basis(
        packet.to_bytes(),
        {"source_snapshot": basis["source_snapshot"]},
    )
    assert matching.matches_expected is True
    assert matching.current is None
    assert matching.to_payload()["facets"]["source_snapshot"]["current"] is None

    changed = dict(basis["source_snapshot"])
    changed["input_count"] += 1
    mismatching = compare_context_packet_basis(
        packet.to_bytes(),
        {"source_snapshot": changed},
    )
    assert mismatching.matches_expected is False
    assert mismatching.current is None


def test_snapshot_reconciliation_remains_unevaluated_and_detects_source_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    packet = _build_snapshot_packet(tmp_path, monkeypatch)

    unchanged = reconcile_context_packet(
        packet.to_bytes(),
        ".",
        "docs/llm_wiki",
    )
    assert unchanged.policy == CONTEXT_PACKET_RECONCILIATION_POLICY
    assert unchanged.state == "unevaluated"
    assert unchanged.current is None
    assert unchanged.limitations == (
        "freshness-not-evaluated",
        "knowledge-absent",
    )
    assert unchanged.facets["source_snapshot"]["current"] is True
    assert unchanged.facets["freshness"] == {
        "matches_expected": True,
        "current": None,
        "state": "unevaluated",
        "reason": "freshness-currentness-not-evaluated",
    }

    Path("app.py").write_text("def changed():\n    return 2\n", encoding="utf-8")
    changed = reconcile_context_packet(
        packet.to_bytes(),
        ".",
        "docs/llm_wiki",
    )
    assert changed.state == "stale"
    assert changed.current is False
    assert changed.facets["source_snapshot"]["current"] is False
    assert changed.facets["source_snapshot"]["reason"] == "source-snapshot-changed"


def test_managed_live_packet_binds_envelope_and_reconciles_current(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(fixture, tmp_path / "checkout")
    commit_knowledge_artifacts(
        _knowledge_commit_plan(tree["wiki_root"], fixture)
    )
    monkeypatch.chdir(tree["root"])

    packet = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request(filters={"surface": "entities"}),
    )
    payload = packet.to_payload()
    assert payload["basis"]["repository"]["state"] == "recorded"
    assert payload["basis"]["repository"]["identity"] == (
        "example.invalid/acme/knowledge-fixture"
    )
    assert payload["basis"]["knowledge"]["state"] == "recorded"
    assert payload["basis"]["freshness"]["evaluated"] is True
    assert payload["basis"]["freshness"]["concept_count"] == 6
    assert payload["basis"]["freshness"]["disclosure"] == "evaluated (6 concepts)"
    assert payload["response"]["knowledge"]["freshness_evaluated"] is True

    structural = validate_context_packet(packet.to_bytes())
    assert structural.freshness_evaluated is False
    live = reconcile_context_packet(packet.to_bytes())
    assert live.state == "current"
    assert live.current is True
    assert all(
        live.facets[name]["current"] is True
        for name in {
            "source_snapshot",
            "repository",
            "knowledge",
            "generator",
            "freshness",
            "context_response",
            "path_policy",
        }
    )

    source = Path("src/accounts.py")
    source.write_text(
        source.read_text(encoding="utf-8") + "\n# nonsemantic change\n",
        encoding="utf-8",
    )
    stale = reconcile_context_packet(packet.to_bytes())
    assert stale.state == "stale"
    assert stale.current is False
    assert stale.facets["source_snapshot"] == {
        "matches_expected": False,
        "current": False,
        "state": "stale",
        "reason": "source-snapshot-changed",
    }
    assert stale.facets["freshness"]["current"] is False
    assert stale.facets["freshness"]["reason"] == "freshness-evaluation-changed"


def test_degraded_packet_exposes_no_failed_native_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(fixture, tmp_path / "checkout")
    commit_knowledge_artifacts(
        _knowledge_commit_plan(tree["wiki_root"], fixture)
    )
    tree["knowledge_path"].write_bytes(b"{not valid JSON}\n")
    monkeypatch.chdir(tree["root"])

    packet = build_qualified_context(
        ".",
        "docs/llm_wiki",
        _request(filters={"surface": "entities"}),
    )
    payload = packet.to_payload()

    assert payload["basis"]["knowledge"] == {
        "state": "unavailable",
        "availability": "degraded",
        "reason": "policy-selected-surface-only-fallback-after-invalid",
    }
    assert payload["basis"]["repository"] == {
        "state": "unavailable",
        "reason": "native-knowledge-envelope-unavailable",
    }
    assert payload["basis"]["freshness"]["evaluated"] is False
    assert payload["delivery"]["limitations"] == [
        "freshness-not-evaluated",
        "knowledge-degraded",
    ]
    assert payload["response"]["knowledge"]["availability"] == "degraded"
    assert b"example.invalid/acme/knowledge-fixture" not in packet.to_bytes()
    assert fixture.knowledge_payload["bundle"]["snapshot"][
        "source_snapshot_hash"
    ].encode() not in packet.to_bytes()


def test_construction_makes_no_network_call_and_no_native_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    root = tmp_path / "project"
    _write_snapshot_project(root)
    wiki = root / "docs" / "llm_wiki"
    before = _tree_bytes(root)
    modes = _make_read_only(wiki)
    monkeypatch.chdir(root)

    def no_network(*_args, **_kwargs):
        raise AssertionError("qualified context construction attempted network I/O")

    monkeypatch.setattr(socket, "create_connection", no_network)
    try:
        packet = build_qualified_context(
            ".",
            "docs/llm_wiki",
            _request(),
            read_only=True,
        )
    finally:
        _restore_modes(modes)

    assert packet.to_bytes()
    assert _tree_bytes(root) == before


def test_public_contract_contains_exact_non_claims_and_passes_vocabulary_guard():
    text = PUBLIC_DOC_PATH.read_text(encoding="utf-8")
    required = (
        "that the source or packet author is authenticated",
        "that repository transfer is authorized",
        "that the packet is owner-resistant or tamperproof",
        "that runtime state remains current after packet construction",
        "that static evidence proves live production behavior",
        "that no arbitrary secret or unregistered identity exists in source text",
        "that the context improves an agent",
    )
    assert all(item in text for item in required)
    assert "content-integrity" in text
    assert "unevaluated (snapshot-only read)" in text
    assert "matches_expected" in text
    assert "current" in text

    tracked = tuple(
        path.relative_to(REPO_ROOT).as_posix()
        for path in REPO_ROOT.rglob("*")
        if path.is_file()
    )
    assert scan_public_document(
        text,
        path="docs/qualified-context-packets.md",
        tracked_files=tracked,
        root=REPO_ROOT,
    ) == []
