"""Tests for the provider-free eval-lite inspection planner."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli.eval_lite import (
    EVAL_LITE_PLAN_SCHEMA_VERSION,
    EVAL_LITE_TASK_SCHEMA_VERSION,
    EvaluationPlanError,
    build_evaluation_plan,
    materialize_evaluation_plan,
    normalize_task_manifest,
)
from llm_wiki_cli.eval_lite import planner
from llm_wiki_cli.services import context_packet, extraction_service


def _manifest(**overrides):
    value = {
        "schema_version": EVAL_LITE_TASK_SCHEMA_VERSION,
        "base_revision": "sha256:" + "2" * 64,
        "prompt": "Add deterministic validation for the declared surface.",
        "allowed_surface": ["tests/test_widget.py", "src/widget.py"],
        "oracle": {
            "command": [".venv/bin/pytest", "-q", "tests/test_widget.py"],
            "timeout_seconds": 120,
        },
        "environment": {
            "model": "declared-model",
            "toolchain": ["pytest", "python-3.12"],
            "budget": {"tokens": 4096},
            "required_capabilities": ["oracle-runner", "model-provider"],
        },
        "limitations": [
            "single-paired-inspection",
            "stochastic-runtime-not-observed",
        ],
    }
    value.update(overrides)
    return value


def _packet_payload(
    packet_id: str,
    *,
    filters=None,
    response_files=None,
    source_identity: str = "sha256:" + "2" * 64,
    budget_tokens: int = 4096,
):
    return {
        "schema_version": context_packet.CONTEXT_PACKET_SCHEMA_VERSION,
        "packet_id": packet_id,
        "assurance": {
            "level": "content-integrity",
            "scope": "canonical-packet-content",
        },
        "request": {
            "protocol": "llm-wiki-context/v1",
            "budget_tokens": budget_tokens,
            "focus": ["all"],
            "format": "json",
            "filters": filters or {},
            "prefer_fresh": False,
        },
        "response": {
            "protocol": "llm-wiki-context/v1",
            "ok": True,
            "files": response_files or {},
        },
        "basis": {
            "source_snapshot": {
                "identity": source_identity,
                "input_count": 2,
            },
            "repository": {
                "state": "recorded",
                "identity": "example/project",
            },
            "knowledge": {
                "state": "unavailable",
                "availability": "absent",
                "reason": "not-initialized",
            },
            "generator": {
                "component": "agent-wiki-cli",
                "version": "1.4.0",
                "context_protocol": "llm-wiki-context/v1",
                "policy_digest": "sha256:" + "3" * 64,
            },
            "freshness": {
                "state": "unevaluated",
                "evaluated": False,
                "reason": "snapshot-only-read",
            },
        },
        "delivery": {
            "bounds": {},
            "truncated": False,
            "warnings": [],
            "limitations": ["freshness-not-evaluated"],
        },
        "path_policy": {
            "policy_version": "qualified-context-path-policy-v1",
            "policy_digest": "sha256:" + "4" * 64,
            "field_counts": {"opaque_values": 1},
        },
    }


def _install_packet_validator(
    monkeypatch,
    baseline_payload,
    treatment_payload,
):
    payloads = {
        b"baseline\n": baseline_payload,
        b"treatment\n": treatment_payload,
    }

    class Packet:
        def __init__(self, payload):
            self._payload = payload

        def to_payload(self):
            return json.loads(json.dumps(self._payload))

    def fake_validate(raw):
        payload = payloads[bytes(raw)]
        packet = Packet(payload)
        return SimpleNamespace(
            packet_id=payload["packet_id"],
            packet=packet,
            to_payload=lambda: {
                "valid": True,
                "packet_id": payload["packet_id"],
                "schema": {"state": "valid"},
                "canonical": {"state": "valid"},
                "digest": {"state": "valid"},
                "path_policy": {"state": "valid"},
                "lineage": {"state": "valid"},
                "availability": {"state": "declared", "value": "absent"},
                "freshness": {
                    "state": "unevaluated",
                    "evaluated": False,
                },
            },
        )

    monkeypatch.setattr(context_packet, "validate_context_packet", fake_validate)


def _reconciliation(packet_id, *, state="current"):
    facets = {
        name: {
            "matches_expected": True,
            "current": True,
            "state": "current",
            "reason": "live-facet-matches-packet",
        }
        for name in context_packet._RECONCILIATION_FACETS
    }
    current = True
    if state == "stale":
        facets["freshness"] = {
            "matches_expected": False,
            "current": False,
            "state": "stale",
            "reason": "freshness-evaluation-changed",
        }
        current = False
    elif state == "unevaluated":
        facets["freshness"] = {
            "matches_expected": True,
            "current": None,
            "state": "unevaluated",
            "reason": "freshness-currentness-not-evaluated",
        }
        current = None
    return context_packet.ContextPacketReconciliation._from_official_read(
        packet_id=packet_id,
        policy=context_packet.CONTEXT_PACKET_RECONCILIATION_POLICY,
        state=state,
        current=current,
        facets=facets,
        limitations=(),
    )


def _current_reconciliation(packet_id):
    return _reconciliation(packet_id)


def test_fixed_inputs_produce_identical_canonical_exploratory_plan(monkeypatch):
    baseline = _packet_payload("sha256:" + "a" * 64)
    treatment = _packet_payload(
        "sha256:" + "b" * 64,
        filters={"surface": "entities"},
        response_files={"src/widget.py": {"summary": "treatment context"}},
    )
    _install_packet_validator(monkeypatch, baseline, treatment)

    first = build_evaluation_plan(
        _manifest(),
        b"baseline\n",
        b"treatment\n",
    )
    reordered = _manifest(
        allowed_surface=["src/widget.py", "tests/test_widget.py"],
        limitations=[
            "stochastic-runtime-not-observed",
            "single-paired-inspection",
        ],
        environment={
            "required_capabilities": ["model-provider", "oracle-runner"],
            "budget": {"tokens": 4096},
            "toolchain": ["python-3.12", "pytest"],
            "model": "declared-model",
        },
    )
    second = build_evaluation_plan(
        reordered,
        b"baseline\n",
        b"treatment\n",
    )

    assert first.to_bytes() == second.to_bytes()
    assert first.to_bytes().endswith(b"\n")
    assert first.to_bytes().count(b"\n") == 1
    payload = first.to_payload()
    assert payload["schema_version"] == EVAL_LITE_PLAN_SCHEMA_VERSION
    assert payload["label"] == "exploratory"
    assert payload["exploratory"] is True
    assert payload["disposition"] == "conditionally-runnable"
    assert payload["reason_codes"] == [
        "evidence-currentness-unevaluated",
        "execution-capabilities-unavailable",
    ]
    assert payload["confound_report"]["count"] == 0
    assert {
        item["classification"] for item in payload["arm_differences"]
    } <= {"intended-context", "derived-context"}
    assert all(
        "value" not in receipt
        for difference in payload["arm_differences"]
        for receipt in (
            difference["baseline"],
            difference["treatment"],
        )
    )
    assert payload["operation_manifest"]["oracle"]["handling"] == (
        "inert-data-not-executed"
    )
    assert payload["operation_manifest"]["prohibited_operations"] == [
        "task-execution",
        "provider-call",
        "repository-write",
        "plugin-load",
    ]
    assert first.plan_digest == payload["plan_digest"]


def test_complete_caller_capability_declarations_make_design_valid(monkeypatch):
    baseline = _packet_payload("sha256:" + "a" * 64)
    treatment = _packet_payload(
        "sha256:" + "b" * 64,
        filters={"surface": "modules"},
        response_files={"src/widget.py": {"summary": "context"}},
    )
    _install_packet_validator(monkeypatch, baseline, treatment)

    plan = build_evaluation_plan(
        _manifest(),
        b"baseline\n",
        b"treatment\n",
        available_capabilities={"model-provider", "oracle-runner"},
        baseline_reconciliation=_current_reconciliation(
            baseline["packet_id"]
        ),
        treatment_reconciliation=_current_reconciliation(
            treatment["packet_id"]
        ),
    )

    assert plan.disposition == "design-valid"
    assert plan.to_payload()["capabilities"] == {
        "basis": "caller-declared-not-live-probed",
        "required": ["model-provider", "oracle-runner"],
        "declared_available": ["model-provider", "oracle-runner"],
        "missing": [],
        "current": None,
    }


def test_planted_source_confound_flips_disposition_to_design_invalid(monkeypatch):
    baseline = _packet_payload("sha256:" + "a" * 64)
    treatment = _packet_payload(
        "sha256:" + "b" * 64,
        filters={"surface": "entities"},
        source_identity="sha256:" + "9" * 64,
    )
    _install_packet_validator(monkeypatch, baseline, treatment)

    payload = build_evaluation_plan(
        _manifest(),
        b"baseline\n",
        b"treatment\n",
        available_capabilities=["model-provider", "oracle-runner"],
    ).to_payload()

    assert payload["disposition"] == "design-invalid"
    assert payload["reason_codes"] == [
        "task-base-mismatch",
        "non-context-arm-difference",
    ]
    assert payload["confound_report"]["state"] == "different"
    source_findings = [
        item
        for item in payload["confound_report"]["findings"]
        if item["category"] == "source"
    ]
    assert [item["path"] for item in source_findings] == [
        "/basis/source_snapshot/identity"
    ]
    assert all(
        item["classification"] == "non-context-confound"
        for item in source_findings
    )


def test_matching_wrong_task_base_is_design_invalid(monkeypatch):
    wrong_identity = "sha256:" + "8" * 64
    baseline = _packet_payload(
        "sha256:" + "a" * 64,
        source_identity=wrong_identity,
    )
    treatment = _packet_payload(
        "sha256:" + "b" * 64,
        filters={"surface": "entities"},
        source_identity=wrong_identity,
    )
    _install_packet_validator(monkeypatch, baseline, treatment)

    payload = build_evaluation_plan(
        _manifest(),
        b"baseline\n",
        b"treatment\n",
    ).to_payload()

    assert payload["disposition"] == "design-invalid"
    assert payload["reason_codes"] == ["task-base-mismatch"]
    assert payload["source_binding"]["matches"] is False
    assert {
        name: arm["matches_expected"]
        for name, arm in payload["source_binding"]["arms"].items()
    } == {"baseline": False, "treatment": False}


def test_budget_difference_is_a_non_context_confound(monkeypatch):
    baseline = _packet_payload("sha256:" + "a" * 64, budget_tokens=2048)
    treatment = _packet_payload("sha256:" + "b" * 64, budget_tokens=4096)
    _install_packet_validator(monkeypatch, baseline, treatment)

    payload = build_evaluation_plan(
        _manifest(),
        b"baseline\n",
        b"treatment\n",
    ).to_payload()

    assert payload["disposition"] == "design-invalid"
    assert {
        (item["path"], item["category"])
        for item in payload["confound_report"]["findings"]
    } >= {("/request/budget_tokens", "budget")}


def test_stale_live_reconciliation_blocks_design(monkeypatch):
    baseline = _packet_payload("sha256:" + "a" * 64)
    treatment = _packet_payload(
        "sha256:" + "b" * 64,
        filters={"surface": "entities"},
    )
    _install_packet_validator(monkeypatch, baseline, treatment)
    stale = _reconciliation(treatment["packet_id"], state="stale")

    payload = build_evaluation_plan(
        _manifest(),
        b"baseline\n",
        b"treatment\n",
        available_capabilities=["model-provider", "oracle-runner"],
        baseline_reconciliation=_current_reconciliation(
            baseline["packet_id"]
        ),
        treatment_reconciliation=stale,
    ).to_payload()

    assert payload["disposition"] == "design-invalid"
    assert payload["reason_codes"] == ["stale-context-evidence"]
    assert payload["evidence"]["state"] == "stale"
    assert payload["evidence"]["current"] is False


def test_serialized_or_fabricated_reconciliation_cannot_assert_currentness(
    monkeypatch,
):
    baseline = _packet_payload("sha256:" + "a" * 64)
    treatment = _packet_payload("sha256:" + "b" * 64)
    _install_packet_validator(monkeypatch, baseline, treatment)
    forged = {
        "packet_id": baseline["packet_id"],
        "policy": context_packet.CONTEXT_PACKET_RECONCILIATION_POLICY,
        "state": "current",
        "current": True,
        "facets": {},
        "limitations": [],
    }

    with pytest.raises(EvaluationPlanError) as caught:
        build_evaluation_plan(
            _manifest(),
            b"baseline\n",
            b"treatment\n",
            available_capabilities=["model-provider", "oracle-runner"],
            baseline_reconciliation=forged,
            treatment_reconciliation=_current_reconciliation(
                treatment["packet_id"]
            ),
        )

    assert caught.value.field == "baseline_reconciliation"


def test_complete_unevaluated_reconciliation_stays_conditional(monkeypatch):
    baseline = _packet_payload("sha256:" + "a" * 64)
    treatment = _packet_payload("sha256:" + "b" * 64)
    _install_packet_validator(monkeypatch, baseline, treatment)

    payload = build_evaluation_plan(
        _manifest(),
        b"baseline\n",
        b"treatment\n",
        available_capabilities=["model-provider", "oracle-runner"],
        baseline_reconciliation=_current_reconciliation(
            baseline["packet_id"]
        ),
        treatment_reconciliation=_reconciliation(
            treatment["packet_id"],
            state="unevaluated",
        ),
    ).to_payload()

    assert payload["disposition"] == "conditionally-runnable"
    assert payload["evidence"]["state"] == "unevaluated"
    assert payload["evidence"]["current"] is None


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"base_revision": "main"}, "manifest.base_revision"),
        ({"allowed_surface": ["/tmp/escape.py"]}, "manifest.allowed_surface[0]"),
        ({"allowed_surface": ["src/../escape.py"]}, "manifest.allowed_surface[0]"),
        ({"oracle": {"command": [], "timeout_seconds": 10}}, "manifest.oracle.command"),
        (
            {
                "environment": {
                    "required_capabilities": [],
                }
            },
            "manifest.environment.model",
        ),
        (
            {
                "environment": {
                    "model": "declared-model",
                    "toolchain": ["pytest"],
                    "required_capabilities": [],
                }
            },
            "manifest.environment.budget",
        ),
        (
            {"allowed_surface": ["src/Foo.py", "src/foo.py"]},
            "manifest.allowed_surface[1]",
        ),
        (
            {"allowed_surface": ["src", "src/widget.py"]},
            "manifest.allowed_surface",
        ),
    ],
)
def test_manifest_admission_is_strict(overrides, field):
    with pytest.raises(EvaluationPlanError) as caught:
        normalize_task_manifest(_manifest(**overrides))

    assert caught.value.field == field


def test_equivalent_manifest_collections_normalize_identically():
    first = normalize_task_manifest(_manifest())
    second = normalize_task_manifest(
        _manifest(
            allowed_surface=["src/widget.py", "tests/test_widget.py"],
            environment={
                "model": "declared-model",
                "toolchain": ["python-3.12", "pytest"],
                "budget": {"tokens": 4096},
                "required_capabilities": ["model-provider", "oracle-runner"],
            },
            limitations=[
                "stochastic-runtime-not-observed",
                "single-paired-inspection",
            ],
        )
    )

    assert first == second


def test_materializer_uses_read_only_qcp_builder_and_never_runs_an_arm(monkeypatch):
    calls = []
    baseline = object()
    treatment = object()
    baseline_live = object()
    treatment_live = object()
    expected = object()

    def fake_packet_builder(src_dir, wiki_dir, request, *, read_only):
        calls.append((src_dir, wiki_dir, request, read_only))
        return baseline if len(calls) == 1 else treatment

    def fake_planner(manifest, baseline_packet, treatment_packet, **kwargs):
        assert manifest == normalize_task_manifest(_manifest())
        assert baseline_packet is baseline
        assert treatment_packet is treatment
        assert kwargs == {
            "available_capabilities": ("oracle-runner",),
            "baseline_reconciliation": baseline_live,
            "treatment_reconciliation": treatment_live,
        }
        return expected

    def fake_reconcile(raw, src_dir, wiki_dir, *, read_only):
        expected_raw = (
            b"baseline\n" if len(reconcile_calls) == 0 else b"treatment\n"
        )
        assert raw == expected_raw
        reconcile_calls.append((src_dir, wiki_dir, read_only))
        return baseline_live if len(reconcile_calls) == 1 else treatment_live

    class MaterializedPacket:
        def __init__(self, raw):
            self.raw = raw

        def to_bytes(self):
            return self.raw

    baseline = MaterializedPacket(b"baseline\n")
    treatment = MaterializedPacket(b"treatment\n")
    reconcile_calls = []

    monkeypatch.setattr(
        context_packet,
        "build_qualified_context",
        fake_packet_builder,
    )
    monkeypatch.setattr(
        context_packet,
        "reconcile_context_packet",
        fake_reconcile,
    )
    monkeypatch.setattr(planner, "build_evaluation_plan", fake_planner)

    result = materialize_evaluation_plan(
        _manifest(),
        src_dir="src",
        wiki_dir="docs/llm_wiki",
        baseline_request={"filters": {}},
        treatment_request={"filters": {"surface": "entities"}},
        available_capabilities=("oracle-runner",),
    )

    assert result is expected
    assert calls == [
        ("src", "docs/llm_wiki", {"filters": {}}, True),
        (
            "src",
            "docs/llm_wiki",
            {"filters": {"surface": "entities"}},
            True,
        ),
    ]
    assert reconcile_calls == [
        ("src", "docs/llm_wiki", True),
        ("src", "docs/llm_wiki", True),
    ]


def test_materializer_rejects_manifest_before_any_source_read(monkeypatch):
    calls = []

    def unexpected(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("invalid manifests must fail before source reads")

    monkeypatch.setattr(context_packet, "build_qualified_context", unexpected)
    monkeypatch.setattr(context_packet, "reconcile_context_packet", unexpected)

    with pytest.raises(EvaluationPlanError) as caught:
        materialize_evaluation_plan(
            _manifest(base_revision="main"),
            src_dir="src",
            wiki_dir="docs/llm_wiki",
            baseline_request={"filters": {}},
            treatment_request={"filters": {"surface": "entities"}},
        )

    assert caught.value.field == "manifest.base_revision"
    assert calls == []


def test_real_packet_materialization_is_plugin_free_and_write_free(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "project"
    root.mkdir()
    (root / "widget.py").write_text(
        "def render(value: str) -> str:\n    return value\n",
        encoding="utf-8",
    )
    wiki = root / "docs" / "llm_wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_text("# Project\n", encoding="utf-8")
    monkeypatch.chdir(root)

    def unexpected_plugin_registry():
        raise AssertionError("eval-lite materialization loaded source plugins")

    monkeypatch.setattr(
        extraction_service,
        "get_extractor_registry",
        unexpected_plugin_registry,
    )
    request = {
        "budget_tokens": 4096,
        "focus": ["all"],
        "format": "json",
        "filters": {},
    }
    seed_packet = context_packet.build_qualified_context(
        ".",
        "docs/llm_wiki",
        request,
    )
    source_identity = seed_packet.to_payload()["basis"]["source_snapshot"][
        "identity"
    ]
    manifest = _manifest(base_revision=source_identity)
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }

    plan = materialize_evaluation_plan(
        manifest,
        src_dir=".",
        wiki_dir="docs/llm_wiki",
        baseline_request=request,
        treatment_request={
            **request,
            "filters": {"language": "python"},
        },
    )

    after = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert before == after
    assert plan.to_payload()["source_binding"]["matches"] is True
    assert plan.to_payload()["disposition"] == "conditionally-runnable"
    assert "evidence-currentness-unevaluated" in plan.to_payload()["reason_codes"]


def test_module_imports_no_execution_or_network_runtime():
    source = Path(planner.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )

    assert imported_roots.isdisjoint(
        {"http", "requests", "socket", "urllib", "subprocess"}
    )
    assert "llm_wiki_cli.services.documentation_calibration" not in source
    assert "llm_wiki_cli.services.calibration" not in source
