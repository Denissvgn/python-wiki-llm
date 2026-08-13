"""Executable compatibility baselines for generated schemas and context output."""

from __future__ import annotations

import hashlib
import json
import types
from pathlib import Path

import pytest

from llm_wiki_cli.services import context_packet, context_service
from llm_wiki_cli.services.contracts import CONTEXT_PROTOCOL_VERSION
from llm_wiki_cli.services.schema import (
    SCHEMA_FILENAMES,
    SchemaRenderProfile,
    build_schema_content,
)
from tests.baseline_measurements import assert_text_baseline, measure_text


REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = REPO_ROOT / "tests" / "fixtures" / "schema-context-baselines-v3.json"
PACKET_ID_DOMAIN = b"llm-wiki-qualified-context-packet/v1\x00"


def _baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _ranking_inputs() -> tuple[dict[str, dict], dict[str, str], int]:
    file_data = {
        "language": "python",
        "classes": [],
        "functions": [{"name": "run", "line": 1}],
    }
    inventory = {
        "a_stale.py": file_data,
        "z_fresh.py": file_data,
    }
    classification = {
        "a_stale.py": "high",
        "z_fresh.py": "high",
    }
    budget = context_service._entry_tokens(
        "a_stale.py",
        context_service._build_entry(file_data, "high", "deep"),
    )
    return inventory, classification, budget


def _plain_context_bytes(prefer_fresh: bool | None) -> bytes:
    inventory, classification, budget = _ranking_inputs()
    if prefer_fresh:
        ranks = {"a_stale.py": 1, "z_fresh.py": 0}
        payload, budget_pressure = (
            context_service._build_context_payload_with_freshness_preference(
                inventory,
                classification,
                budget,
                freshness_rank_by_source=ranks,
            )
        )
        payload["ranking_policy"] = context_service._freshness_ranking_policy(
            {"freshness_evaluated": True},
            ranks,
            budget_pressure=budget_pressure,
        )
    else:
        payload = context_service._build_context_payload(
            inventory,
            classification,
            budget,
        )

    request = {
        "protocol": CONTEXT_PROTOCOL_VERSION,
        "budget_tokens": budget,
        "focus": ["all"],
        "format": "json",
    }
    if prefer_fresh is not None:
        request["prefer_fresh"] = prefer_fresh
    normalized = context_service._validate_protocol_request(request)
    response = context_service._protocol_success_payload(normalized, payload, [])
    return (json.dumps(response, indent=2) + "\n").encode("utf-8")


def _assert_file_baseline(record: dict) -> bytes:
    path = REPO_ROOT / record["path"]
    content = path.read_bytes()
    assert len(content) == record["bytes"]
    assert hashlib.sha256(content).hexdigest() == record["sha256"]
    assert b"\r" not in content
    return content


def _assert_at_most(label: str, metric: str, actual: int, limit: int) -> None:
    assert actual <= limit, f"{label}: measured {metric}={actual}; limit={limit}"


def test_text_baseline_failure_reports_measured_words_and_characters() -> None:
    with pytest.raises(
        AssertionError,
        match=r"measured words=2, characters=10, lines=1",
    ):
        assert_text_baseline(
            "diagnostic example",
            "alpha beta",
            {"words": 1, "characters": 1, "lines": 1, "sha256": "different"},
        )


def test_generated_schema_targets_and_configuration_matrix_match_baseline() -> None:
    baseline = _baseline()
    assert baseline["schema_version"] == "schema-context-executable-baselines/v3"
    generated = baseline["generated_schema"]
    assert generated["measurement"] == {
        "words": "unicode-whitespace-delimited",
        "characters": "unicode-code-points",
        "lines": "splitlines",
        "sha256": "utf-8-bytes",
    }
    assert SCHEMA_FILENAMES == {
        agent: record["path"] for agent, record in generated["agents"].items()
    }
    expected_variants = {
        "default",
        "without_quality_hints",
        "with_issue_reporting",
        "without_quality_hints_with_issue_reporting",
    }
    assert set(generated["variants"]) == expected_variants
    assert generated["profiles"] == [
        SchemaRenderProfile.COMPACT.value,
        SchemaRenderProfile.EXPANDED_INLINE.value,
    ]

    for agent, agent_record in generated["agents"].items():
        assert set(agent_record["profiles"]) == set(generated["profiles"])
        for profile_name, profile_record in agent_record["profiles"].items():
            render_profile = SchemaRenderProfile(profile_name)
            assert set(profile_record["variants"]) == expected_variants
            for variant_name, expected in profile_record["variants"].items():
                settings = generated["variants"][variant_name]
                content = build_schema_content(
                    agent,
                    generated["wiki_dir"],
                    render_profile=render_profile,
                    quality_hints=settings["quality_hints"],
                    issue_reporting=settings["issue_reporting"],
                )
                assert_text_baseline(
                    f"{agent}/{profile_name}/{variant_name}", content, expected
                )
                assert ("## Agent quality guidelines" in content) is settings[
                    "quality_hints"
                ]
                assert ("## Report llm-wiki tool issues" in content) is settings[
                    "issue_reporting"
                ]
                assert content.count("--knowledge-mode auto") == 1
                assert "query_documentation" in content
                assert "`impact` with `paths`" in content
                assert "`allow_full_inventory=true`" in content


def test_expanded_observation_and_compact_target_are_separate_profiles() -> None:
    generated = _baseline()["generated_schema"]
    assert generated["compact_target"] == {
        "words": {"minimum": 400, "maximum": 650},
        "characters": {"preferred_maximum": 5000},
        "other_agent_character_delta": {"maximum": 50},
        "conditional_additions": {
            "quality_hints": {
                "words_maximum": 15,
                "characters_maximum": 100,
                "lines_maximum": 4,
            },
            "issue_reporting": {
                "words_maximum": 60,
                "characters_maximum": 480,
                "lines_maximum": 8,
            },
        },
        "all_options": {"words_maximum": 650, "characters_maximum": 5520},
        "reduction_percent": {"minimum": 75, "maximum": 85},
    }

    target = generated["compact_target"]
    records = generated["agents"]
    generic = records["generic"]["profiles"]
    generic_compact = generic[SchemaRenderProfile.COMPACT.value]["variants"]
    generic_expanded = generic[SchemaRenderProfile.EXPANDED_INLINE.value]["variants"]
    compact_default = generic_compact["default"]
    expanded_default = generic_expanded["default"]

    _assert_at_most(
        "generic/compact/default",
        "words",
        compact_default["words"],
        target["words"]["maximum"],
    )
    _assert_at_most(
        "generic/compact/default",
        "characters",
        compact_default["characters"],
        target["characters"]["preferred_maximum"],
    )
    assert compact_default["words"] >= target["words"]["minimum"]

    reduction = 100 * (1 - compact_default["words"] / expanded_default["words"])
    assert target["reduction_percent"]["minimum"] <= reduction <= target[
        "reduction_percent"
    ]["maximum"], f"generic/compact/default: measured reduction={reduction:.2f}%"

    generic_characters = compact_default["characters"]
    for agent, record in records.items():
        variants = record["profiles"][SchemaRenderProfile.COMPACT.value]["variants"]
        default = variants["default"]
        _assert_at_most(
            f"{agent}/compact/default",
            "words",
            default["words"],
            target["words"]["maximum"],
        )
        _assert_at_most(
            f"{agent}/compact/default-preamble-delta",
            "characters",
            default["characters"] - generic_characters,
            target["other_agent_character_delta"]["maximum"],
        )

        without_quality = variants["without_quality_hints"]
        quality_limits = target["conditional_additions"]["quality_hints"]
        for metric in ("words", "characters", "lines"):
            _assert_at_most(
                f"{agent}/compact/quality-hints",
                metric,
                default[metric] - without_quality[metric],
                quality_limits[f"{metric}_maximum"],
            )

        with_issue = variants["with_issue_reporting"]
        issue_limits = target["conditional_additions"]["issue_reporting"]
        for metric in ("words", "characters", "lines"):
            _assert_at_most(
                f"{agent}/compact/issue-reporting",
                metric,
                with_issue[metric] - default[metric],
                issue_limits[f"{metric}_maximum"],
            )
        _assert_at_most(
            f"{agent}/compact/with-issue-reporting",
            "words",
            with_issue["words"],
            target["all_options"]["words_maximum"],
        )
        _assert_at_most(
            f"{agent}/compact/with-issue-reporting",
            "characters",
            with_issue["characters"],
            target["all_options"]["characters_maximum"],
        )

    current_compact = build_schema_content(
        "generic",
        generated["wiki_dir"],
        render_profile=SchemaRenderProfile.COMPACT,
    )
    assert measure_text(current_compact) == compact_default


def test_plain_context_default_and_explicit_false_remain_byte_compatible() -> None:
    record = _baseline()["plain_context"]
    golden = _assert_file_baseline(record["default_golden"])
    omitted = _plain_context_bytes(None)
    explicit_false = _plain_context_bytes(False)

    assert record["protocol_version"] == CONTEXT_PROTOCOL_VERSION
    assert record["protocol_version"] == context_service.PROTOCOL_VERSION
    assert record["default_prefer_fresh"] is False
    assert omitted == explicit_false == golden
    assert b'"prefer_fresh"' not in golden
    assert b'"ranking_policy"' not in golden


@pytest.mark.parametrize(
    "include_explicit_false",
    [False, True],
    ids=["prefer-fresh-omitted", "prefer-fresh-explicit-false"],
)
def test_plain_context_request_file_stdout_route_matches_legacy_golden(
    include_explicit_false: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    record = _baseline()["plain_context"]
    golden = _assert_file_baseline(record["default_golden"])
    inventory, _classification, budget = _ranking_inputs()
    inventory_calls: list[dict] = []

    def deterministic_inventory(*_args, **kwargs):
        inventory_calls.append(kwargs)
        return inventory

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(context_service, "get_inventory", deterministic_inventory)

    request = {
        "protocol": CONTEXT_PROTOCOL_VERSION,
        "budget_tokens": budget,
        "focus": ["all"],
        "format": "json",
    }
    if include_explicit_false:
        request["prefer_fresh"] = False
    request_path = tmp_path / "context-request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")

    context_service.run(
        types.SimpleNamespace(
            request=str(request_path),
            output=None,
            src_dir=".",
        )
    )

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.encode("utf-8") == golden
    assert len(inventory_calls) == 1
    assert inventory_calls[0]["return_result"] is True


def test_plain_context_freshness_preference_golden_remains_deterministic() -> None:
    record = _baseline()["plain_context"]
    golden = _assert_file_baseline(record["preferred_golden"])

    assert _plain_context_bytes(True) == golden
    assert b'"prefer_fresh": true' in golden
    assert b'"ranking_policy"' in golden


def test_packet_versions_and_fixture_hash_semantics_match_baseline() -> None:
    record = _baseline()["qualified_context_packet"]
    fixture = _assert_file_baseline(record["golden"])
    payload = json.loads(fixture)

    assert record["schema_version"] == context_packet.CONTEXT_PACKET_SCHEMA_VERSION
    assert record["policy_version"] == context_packet.CONTEXT_PACKET_POLICY_VERSION
    assert record["path_policy_version"] == (
        context_packet.CONTEXT_PACKET_PATH_POLICY_VERSION
    )
    assert record["reconciliation_policy"] == (
        context_packet.CONTEXT_PACKET_RECONCILIATION_POLICY
    )
    assert record["context_protocol_version"] == CONTEXT_PROTOCOL_VERSION
    assert record["context_protocol_version"] == context_service.PROTOCOL_VERSION
    assert record["assurance_level"] == context_packet.CONTEXT_PACKET_ASSURANCE_LEVEL

    assert payload["schema_version"] == record["schema_version"]
    assert payload["request"]["prefer_fresh"] is False
    assert (
        payload["basis"]["generator"]["policy_digest"]
        == record["generator_policy_digest"]
    )
    assert payload["path_policy"]["policy_version"] == record["path_policy_version"]
    assert payload["path_policy"]["policy_digest"] == record["path_policy_digest"]
    assert payload["packet_id"] == record["golden"]["packet_id"]
    assert context_packet._context_policy_digest() == record["generator_policy_digest"]
    assert context_packet._path_policy_digest() == record["path_policy_digest"]

    semantic_body = {key: value for key, value in payload.items() if key != "packet_id"}
    canonical_body = json.dumps(
        semantic_body,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    expected_packet_id = (
        "sha256:" + hashlib.sha256(PACKET_ID_DOMAIN + canonical_body).hexdigest()
    )

    assert payload["packet_id"] == expected_packet_id
    assert context_packet._packet_id(semantic_body) == expected_packet_id
    assert payload["packet_id"].removeprefix("sha256:") != record["golden"]["sha256"]
