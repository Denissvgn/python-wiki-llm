"""Joint selection uses one immutable capture and preserves qualified groups."""

from __future__ import annotations

import copy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import context_budget as budget
from llm_wiki_cli.services import context_packet as packets
from llm_wiki_cli.services import context_service as context
from llm_wiki_cli.services.token_counting import EstimatedCounter
from tests.test_context_budget import ByteCounter

CORPUS = json.loads(
    (Path(__file__).parent / "fixtures/context-budget-corpus.json").read_text()
)


@pytest.fixture
def native_heavy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    spec = CORPUS["native_heavy"]
    for index in range(spec["source_files"]):
        name = (
            spec["changed_source"]
            if index == spec["source_files"] - 1
            else f"file_{index:02}.py"
        )
        content = ['raise RuntimeError("synthetic source must never execute")\n']
        for number in range(spec["classes_per_file"]):
            content.append(
                f"class Component{index:02}_{number:02}_{spec['identifier_suffix']}:\n"
                "    def execute(self, value: str) -> str:\n        return value\n\n"
            )
        (source / name).write_text("".join(content))
    api.bootstrap_wiki(
        "src",
        "wiki",
        skip_workflows=True,
        skip_flows=True,
        skip_dependencies=True,
        skip_data_flow=True,
    )
    captured = packets.capture_context_read(
        "src",
        "wiki",
        read_only=True,
        allow_selection_mismatch=True,
        strict_wiki_symlinks=True,
    )
    captured = replace(
        captured, changed_files=(spec["changed_source"],), explicit_changes=True
    )
    request = budget.validate_request(
        {
            "budget_tokens": spec["budget_tokens"],
            "budget_mode": "estimated",
            "format": "packet",
            "focus": ["changed"],
            "knowledge_mode": "auto",
            "changes": {"mode": "paths", "paths": [spec["changed_source"]]},
        }
    )
    changes = budget.select_changes(
        captured.source_root, request["changes"], snapshot=captured.source_snapshot
    )
    captured = replace(captured, change_selection=changes)
    legacy = {k: v for k, v in request.items() if k in context._V2_REQUEST_KEYS}
    legacy.update(
        protocol=context.KNOWLEDGE_PROTOCOL_VERSION,
        format="json",
        budget_tokens=2**63 - 1,
    )
    ranks = {}
    payload, warnings = packets.build_context_from_captured_read(
        captured, legacy, freshness_ranking_out=ranks
    )
    return captured, request, payload, warnings, ranks


def renderer(captured):
    def render(request, response):
        contract = packets._packet_contract_for_request(request)
        body = {
            "schema_version": contract.schema_version,
            **packets._packet_body(captured, request, response, contract),
        }
        return {**body, "packet_id": packets._packet_id(body)}

    return render


def fit(captured, request, payload, warnings, ranks, **options):
    return budget.fit_payload(
        payload,
        request,
        warnings,
        EstimatedCounter(),
        packet_renderer=renderer(captured) if request["format"] == "packet" else None,
        freshness_rank_by_source=ranks,
        changes=captured.change_selection,
        **options,
    )


def test_source_only_baseline_preserves_correct_refusal_and_larger_request(
    native_heavy,
):
    captured, request, payload, warnings, ranks = native_heavy
    native_bytes = len(
        json.dumps(
            payload["knowledge"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    )
    assert native_bytes > request["budget_tokens"] * 4
    rejected = fit(captured, request, payload, warnings, ranks)
    assert (
        not rejected.ok and rejected.rendered == "" and rejected.error == "cannot-fit"
    )
    larger_request = {**request, "budget_tokens": 32000}
    larger = fit(captured, larger_request, payload, warnings, ranks)
    assert larger.ok
    counted = EstimatedCounter().count(larger.rendered)
    assert counted <= larger.accounting["used_tokens"] <= 32000
    assert budget.request_identity(request) != budget.request_identity(larger_request)
    budget.validate_budgeted_context(
        larger.rendered, larger_request, counter=EstimatedCounter()
    )
    packets._assert_source_unchanged(captured.source_snapshot, captured.source_anchor)
    packets._assert_wiki_unchanged(
        captured.wiki_root,
        captured.wiki_anchor,
        reject_all_symlinks=True,
        expected_integrity=captured.wiki_integrity,
    )


@pytest.mark.parametrize("fmt", ["json", "markdown", "packet"])
def test_joint_native_heavy_selection_keeps_useful_changed_evidence(native_heavy, fmt):
    captured, request, payload, warnings, ranks = native_heavy
    original = copy.deepcopy(payload)
    request = {**request, "format": fmt}
    result = fit(captured, request, payload, warnings, ranks, joint_native_source=True)
    assert result.ok
    envelope = budget.validate_budgeted_context(
        result.rendered, request, counter=EstimatedCounter()
    )
    response = (
        envelope["packet"]["response"]
        if fmt == "packet"
        else envelope.get("context", envelope.get("metadata"))
    )
    assert response is not None
    knowledge = response["knowledge"]
    expected = CORPUS["native_heavy"]["expected"]
    files = response.get("files", {})
    if fmt != "markdown":
        assert len(files) >= expected["minimum_source_rows"]
        assert expected["retained_source"] in files
    assert (
        len(knowledge["selection"]["concepts"]) >= expected["minimum_native_concepts"]
    )
    assert len(knowledge["selection"]["pages"]) >= expected["minimum_native_pages"]
    assert any(
        c["source_path"] == expected["retained_native_source"]
        for c in knowledge["selection"]["concepts"]
    )
    assert knowledge["reason"] == "knowledge-results-truncated"
    assert knowledge["bounds"]["concepts"]["truncated"]
    for concept in knowledge["selection"]["concepts"]:
        assert concept in original["knowledge"]["selection"]["concepts"]
    assert payload == original
    assert (
        EstimatedCounter().count(result.rendered)
        <= result.accounting["used_tokens"]
        <= request["budget_tokens"]
    )


def test_joint_policy_does_not_assume_monotonic_native_counter(native_heavy):
    captured, request, payload, warnings, ranks = native_heavy

    class NonMonotonicCounter:
        identity = "native-three-row-counter/v1"
        exact = True

        def count(self, text):
            native = json.loads(text)["context"]["knowledge"]
            return 1 if len(native["selection"]["concepts"]) == 3 else 100_000

    request = {**request, "format": "json", "budget_mode": "exact"}
    counter = NonMonotonicCounter()
    result = budget.fit_payload(
        payload,
        request,
        warnings,
        counter,
        changes=captured.change_selection,
        joint_native_source=True,
        source_json_lower_bound=True,
    )
    assert result.ok and result.accounting["exact_compliance"]
    validated = budget.validate_budgeted_context(
        result.rendered, request, counter=counter
    )
    assert len(validated["context"]["knowledge"]["selection"]["concepts"]) == 3


def test_joint_native_exact_counter_counts_complete_unicode_output(native_heavy):
    captured, request, payload, warnings, ranks = native_heavy
    request = {**request, "budget_tokens": 32000, "budget_mode": "exact"}
    counter = ByteCounter()
    result = budget.fit_payload(
        payload,
        request,
        warnings,
        counter,
        packet_renderer=renderer(captured),
        changes=captured.change_selection,
        joint_native_source=True,
        freshness_rank_by_source=ranks,
    )
    assert result.ok and result.accounting["exact_compliance"]
    budget.validate_budgeted_context(result.rendered, request, counter=counter)
    assert (
        len(result.rendered.encode("utf-8"))
        <= result.accounting["used_tokens"]
        <= 32000
    )


def test_explicit_target_evidence_is_not_discarded_to_obtain_a_fit(native_heavy):
    captured, request, _payload, _warnings, _ranks = native_heavy
    target = "Component07_03_" + CORPUS["native_heavy"]["identifier_suffix"]
    request = {**request, "filters": {"symbol": target}, "knowledge_mode": "required"}
    normalized = budget.validate_request(request)
    legacy = {
        key: value
        for key, value in normalized.items()
        if key in context._V2_REQUEST_KEYS
    }
    legacy.update(
        protocol=context.KNOWLEDGE_PROTOCOL_VERSION,
        format="json",
        budget_tokens=2**63 - 1,
    )
    payload, warnings = packets.build_context_from_captured_read(captured, legacy)
    graph_before = copy.deepcopy(payload["graphs"])
    full = fit(
        captured,
        {**normalized, "budget_tokens": 100000},
        payload,
        warnings,
        {},
        joint_native_source=True,
    )
    assert full.ok
    response = budget.validate_budgeted_context(
        full.rendered,
        {**normalized, "budget_tokens": 100000},
        counter=EstimatedCounter(),
    )["packet"]["response"]
    assert response["graphs"] == graph_before
    assert any(
        row["title"] == target for row in response["knowledge"]["selection"]["concepts"]
    )
    tiny = fit(
        captured,
        {**normalized, "budget_tokens": 1},
        payload,
        warnings,
        {},
        joint_native_source=True,
        broad_refusal_diagnostics=True,
    )
    assert not tiny.ok and tiny.rendered == ""
    assert tiny.diagnostics is not None
    assert tiny.diagnostics["native"]["mode"] == "required"


def test_joint_currentness_stays_inside_changed_source_relevance(native_heavy):
    captured, request, _payload, _warnings, _ranks = native_heavy
    for name in ("file_00.py", "z_changed.py"):
        path = captured.source_root / name
        path.write_text(path.read_text().replace("value: str", "value: int"))
    fresh_capture = packets.capture_context_read(
        "src",
        "wiki",
        read_only=True,
        allow_selection_mismatch=True,
        strict_wiki_symlinks=True,
    )
    fresh_capture = replace(
        fresh_capture,
        changed_files=("z_changed.py",),
        explicit_changes=True,
        change_selection=captured.change_selection,
    )
    request = {**request, "prefer_fresh": True, "budget_tokens": 12000}
    legacy = {k: v for k, v in request.items() if k in context._V2_REQUEST_KEYS}
    legacy.update(
        protocol=context.KNOWLEDGE_PROTOCOL_VERSION,
        format="json",
        budget_tokens=2**63 - 1,
    )
    ranks = {}
    payload, warnings = packets.build_context_from_captured_read(
        fresh_capture, legacy, freshness_ranking_out=ranks
    )
    assert ranks["file_00.py"] > ranks["file_01.py"]
    result = fit(
        fresh_capture, request, payload, warnings, ranks, joint_native_source=True
    )
    assert result.ok
    response = budget.validate_budgeted_context(
        result.rendered, request, counter=EstimatedCounter()
    )["packet"]["response"]
    concepts = response["knowledge"]["selection"]["concepts"]
    assert any(row["source_path"] == "z_changed.py" for row in concepts)
    low = [row for row in concepts if row["source_path"] != "z_changed.py"]
    assert low and all(row["source_path"] != "file_00.py" for row in low)
    assert response["knowledge"]["freshness_evaluated"]
    assert any(row["freshness"]["state"] == "source-changed" for row in concepts)


@pytest.mark.parametrize("facet", ["source", "wiki", "selection"])
def test_joint_fitting_keeps_mutation_guards_after_reductions(
    native_heavy, monkeypatch, facet
):
    captured, request, _payload, _warnings, _ranks = native_heavy
    monkeypatch.setattr(packets, "capture_context_read", lambda *a, **k: captured)
    mutated = []

    class MutatingCounter(EstimatedCounter):
        def count(self, text):
            envelope = json.loads(text)
            concepts = envelope["packet"]["response"]["knowledge"]["selection"][
                "concepts"
            ]
            if len(concepts) < 20 and not mutated:
                if facet == "source":
                    path = captured.source_root / "z_changed.py"
                    path.write_bytes(path.read_bytes() + b"\n# concurrent change\n")
                elif facet == "wiki":
                    path = captured.wiki_root / "index.md"
                    path.write_bytes(
                        path.read_bytes() + b"\nConcurrent authored change.\n"
                    )
                else:
                    path = captured.source_root / ".llm-wiki/source-selection.json"
                    path.parent.mkdir(exist_ok=True)
                    path.write_text(
                        json.dumps(
                            {
                                "schema_version": "llm-wiki-source-selection/v1",
                                "include": ["z_changed.py"],
                                "exclude": [],
                            }
                        )
                    )
                mutated.append(path)
            return super().count(text)

    with pytest.raises(packets.ContextPacketSourceMutationError):
        budget.build_budgeted_context("src", "wiki", request, counter=MutatingCounter())
    assert len(mutated) == 1


def test_joint_required_native_does_not_disappear_at_tiny_budget(native_heavy):
    captured, request, payload, warnings, ranks = native_heavy
    request = {**request, "budget_tokens": 1, "knowledge_mode": "required"}
    payload = copy.deepcopy(payload)
    payload["knowledge"]["mode"] = "required"
    result = fit(
        captured,
        request,
        payload,
        warnings,
        ranks,
        joint_native_source=True,
        broad_refusal_diagnostics=True,
        source_json_lower_bound=True,
    )
    assert not result.ok and result.rendered == ""
    assert result.accounting["used_tokens"] > 1
    assert result.diagnostics is not None
    native = result.diagnostics["native"]
    assert native["mode"] == "required" and native["status"] == "selected"
    assert native["bounds"]["concepts"]["returned"] >= 1
    assert result.diagnostics["source"]["returned"] >= 1


def test_broad_fitting_captures_and_builds_selection_once(native_heavy, monkeypatch):
    captured, request, _payload, _warnings, _ranks = native_heavy
    captures = []
    builds = []
    original = packets.build_context_from_captured_read

    def capture(*args, **kwargs):
        captures.append(1)
        return captured

    def build(*args, **kwargs):
        builds.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(packets, "capture_context_read", capture)
    monkeypatch.setattr(packets, "build_context_from_captured_read", build)
    result = budget.build_budgeted_context("src", "wiki", request)
    assert result.ok
    assert captures == builds == [1]
    budget.validate_budgeted_context(
        result.rendered, request, counter=EstimatedCounter()
    )


@pytest.mark.parametrize("case", ["source_heavy", "metadata_heavy"])
def test_source_and_metadata_corpus_preserve_budget_meaning(
    tmp_path, monkeypatch, case
):
    monkeypatch.chdir(tmp_path)
    spec = CORPUS[case]
    source = tmp_path / "src"
    source.mkdir()
    for index in range(spec["source_files"]):
        name = (
            "z_changed.py"
            if index == spec["source_files"] - 1
            else f"module_{index:03}_" + "x" * spec.get("filename_padding", 0) + ".py"
        )
        methods = "".join(
            f"    def execute_{method}(self, value):\n        return value\n\n"
            for method in range(spec.get("methods_per_class", 1))
        )
        content = "".join(
            f"class Component{number}:\n{methods}"
            for number in range(spec.get("classes_per_file", 1))
        )
        if name == "z_changed.py" and spec.get("changed_source_calls"):
            content += (
                "\ndef dense():\n"
                + "    record('雪', 2, 3, 4)\n" * spec["changed_source_calls"]
            )
        (source / name).write_text(content)
    request = {
        "budget_tokens": spec["budget_tokens"],
        "budget_mode": "estimated",
        "format": "packet",
        "knowledge_mode": "auto",
        "focus": ["changed"],
        "changes": {"mode": "paths", "paths": ["z_changed.py"]},
    }
    result = budget.build_budgeted_context("src", "absent-wiki", request)
    if case == "metadata_heavy":
        assert not result.ok and result.error == "cannot-fit" and result.rendered == ""
        assert result.diagnostics is not None
        assert (
            result.diagnostics["component_bytes"]["source_priorities"]
            > spec["budget_tokens"] * 4
        )
        assert result.diagnostics["native"]["availability"] == "absent"
        return
    assert result.ok
    packet = budget.validate_budgeted_context(
        result.rendered, request, counter=EstimatedCounter()
    )["packet"]
    assert "z_changed.py" in packet["response"]["files"]
    assert packet["response"]["truncated"]
    assert packet["response"]["knowledge"]["status"] == "fallback"
    assert packet["response"]["knowledge"]["availability"] == "absent"
