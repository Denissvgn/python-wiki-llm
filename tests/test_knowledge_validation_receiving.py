"""Independent receiving controls for the invocation-bound final-model handoff."""

from __future__ import annotations

from copy import deepcopy
from contextlib import contextmanager, nullcontext
from contextvars import copy_context
from dataclasses import FrozenInstanceError, replace
import io
import json
import shutil
import sys
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import (
    contracts, knowledge_artifacts, knowledge_generation, knowledge_index, knowledge_model, knowledge_orchestration,
)
from llm_wiki_cli.services.knowledge_loader import KnowledgeStateLoadError, load_knowledge_state
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_artifacts import _plan
from tests.test_knowledge_generation import _planner_inputs


def _raw(root):
    fixture = one_module_two_entities_fixture()
    plan = _plan(root, fixture)
    return json.loads(plan.knowledge_index.content), plan


def _artifact_kwargs(plan, content):
    return {"surface_index_bytes": plan.surface_index.content, "knowledge_index_bytes": content,
            "manifest": plan.committed_manifest}


def _tree(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts}


def _cli(argv):
    stdout, stderr = io.StringIO(), io.StringIO()
    with patch.object(sys, "argv", ["llm-wiki", *argv]), patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
        try:
            cli.main()
            code = 0
        except SystemExit as exc:
            code = exc.code
    return code, stdout.getvalue(), stderr.getvalue()


def test_issued_final_receipt_is_frozen_exact_and_expires_at_invocation_end(tmp_path):
    raw, _ = _raw(tmp_path)
    with knowledge_index._knowledge_validation_operation(tmp_path):
        receipt = knowledge_index._validated_index_receipt(raw, tmp_path)
        assert knowledge_index._require_validation_receipt(receipt, tmp_path, receipt.content) is receipt.model
        assert deepcopy(receipt) is receipt
        assert receipt._proof is not None
        for obj, field, value in ((receipt, "content", b"changed"), (receipt._proof, "content", b"changed"),
                                  (receipt._proof, "model", replace(receipt.model)),
                                  (receipt._proof, "validator_identity", ())):
            with pytest.raises(FrozenInstanceError):
                setattr(obj, field, value)
        with pytest.raises(TypeError):
            cast(Any, receipt.model.extensions)["untrusted.receiving/changed"] = True
    with pytest.raises(TypeError, match="operation"):
        knowledge_index._require_validation_receipt(receipt, tmp_path, receipt.content)


@pytest.mark.parametrize("bad", ["manual", "replace", "model", "bytes", "root"])
def test_nominal_or_copied_proof_cannot_authorize_substituted_value(tmp_path, bad):
    raw, _ = _raw(tmp_path)
    with knowledge_index._knowledge_validation_operation(tmp_path):
        receipt = knowledge_index._validated_index_receipt(raw, tmp_path)
        if bad == "manual":
            forged = knowledge_index._ValidatedIndexReceipt(receipt.model, receipt.content, tmp_path)
        elif bad == "replace":
            forged = replace(receipt)
        else:
            forged = knowledge_index._ValidatedIndexReceipt(
                replace(receipt.model) if bad == "model" else receipt.model,
                memoryview(receipt.content).tobytes() if bad == "bytes" else receipt.content,
                tmp_path / "different" if bad == "root" else tmp_path)
            object.__setattr__(forged, "_proof", receipt._proof)
        with pytest.raises(TypeError):
            knowledge_index._require_validation_receipt(forged, tmp_path, forged.content)


def test_nested_same_root_and_cross_root_invocations_do_not_borrow_receipts(tmp_path):
    raw, _ = _raw(tmp_path)
    with knowledge_index._knowledge_validation_operation(tmp_path):
        outer = knowledge_index._validated_index_receipt(raw, tmp_path)
        for root in (tmp_path, tmp_path / "other"):
            with knowledge_index._knowledge_validation_operation(root):
                with pytest.raises(TypeError):
                    knowledge_index._require_validation_receipt(outer, root, outer.content)
        assert knowledge_index._require_validation_receipt(outer, tmp_path, outer.content) is outer.model
        with pytest.raises(TypeError):
            knowledge_index._require_validation_receipt(outer, tmp_path / "other", outer.content)
    with knowledge_index._knowledge_validation_operation(tmp_path):
        with pytest.raises(TypeError):
            knowledge_index._require_validation_receipt(outer, tmp_path, outer.content)


def test_copied_context_cannot_extend_expired_operation_for_issue_or_consumption(tmp_path):
    raw, _ = _raw(tmp_path)
    with knowledge_index._knowledge_validation_operation(tmp_path):
        receipt = knowledge_index._validated_index_receipt(raw, tmp_path)
        copied = copy_context()
        assert copied.run(knowledge_index._require_validation_receipt, receipt, tmp_path, receipt.content) is receipt.model
    with pytest.raises(TypeError):
        copied.run(knowledge_index._require_validation_receipt, receipt, tmp_path, receipt.content)
    with pytest.raises(TypeError):
        copied.run(knowledge_index._validated_index_receipt, raw, tmp_path)


@pytest.mark.parametrize("module,name", [(knowledge_index, "parse_knowledge_index"),
    (knowledge_model, "parse_knowledge_index"), (knowledge_index, "_validate_builder_model"),
    (knowledge_index, "_serialize_payload"), (knowledge_index, "_validated_index_serialization"),
    (knowledge_index, "_model_to_payload"), (knowledge_index, "_knowledge_index_to_payload_unchecked")])
def test_validator_function_identity_changes_refuse_handoff(tmp_path, monkeypatch, module, name):
    raw, _ = _raw(tmp_path)
    with knowledge_index._knowledge_validation_operation(tmp_path):
        receipt = knowledge_index._validated_index_receipt(raw, tmp_path)
        original = getattr(module, name)
        def same_output(*args, **kwargs):
            return original(*args, **kwargs)
        monkeypatch.setattr(module, name, same_output)
        with pytest.raises(TypeError, match="validators"):
            knowledge_index._require_validation_receipt(receipt, tmp_path, receipt.content)


@pytest.mark.parametrize("module", [knowledge_index, knowledge_model, contracts])
def test_schema_identity_changes_refuse_handoff(tmp_path, monkeypatch, module):
    raw, _ = _raw(tmp_path)
    with knowledge_index._knowledge_validation_operation(tmp_path):
        receipt = knowledge_index._validated_index_receipt(raw, tmp_path)
        monkeypatch.setattr(module, "KNOWLEDGE_SCHEMA_VERSION", "llm-wiki-knowledge/receiving-incompatible")
        with pytest.raises(TypeError, match="validators"):
            knowledge_index._require_validation_receipt(receipt, tmp_path, receipt.content)


def test_same_function_object_with_changed_code_is_not_same_validator(tmp_path):
    raw, _ = _raw(tmp_path)
    function = knowledge_index._serialize_payload
    original = function.__code__
    def changed(payload):
        return "untrusted receiving output"
    with knowledge_index._knowledge_validation_operation(tmp_path):
        receipt = knowledge_index._validated_index_receipt(raw, tmp_path)
        try:
            function.__code__ = changed.__code__
            with pytest.raises(TypeError, match="validators"):
                knowledge_index._require_validation_receipt(receipt, tmp_path, receipt.content)
        finally:
            function.__code__ = original


def test_illicit_frozen_model_mutation_is_detected_by_exact_emission(tmp_path):
    raw, _ = _raw(tmp_path)
    with knowledge_index._knowledge_validation_operation(tmp_path):
        receipt = knowledge_index._validated_index_receipt(raw, tmp_path)
        object.__setattr__(receipt.model, "schema_version", "llm-wiki-knowledge/receiving-invalid")
        with pytest.raises(TypeError, match="canonical bytes"):
            knowledge_index._require_validation_receipt(receipt, tmp_path, receipt.content)


def test_artifact_handoff_equals_full_validation_and_preserves_all_parity_checks(tmp_path):
    raw, plan = _raw(tmp_path)
    full = knowledge_artifacts.validate_knowledge_artifacts(**_artifact_kwargs(plan, plan.knowledge_index.content))
    with knowledge_index._knowledge_validation_operation(tmp_path):
        receipt = knowledge_index._validated_index_receipt(raw, tmp_path)
        reused = knowledge_artifacts.validate_knowledge_artifacts(**_artifact_kwargs(plan, receipt.content),
            _validation_receipt=receipt, _receipt_wiki_root=tmp_path)
        assert reused.knowledge == full.knowledge
        assert reused.surface_payload == full.surface_payload
        assert reused.knowledge_index_hash == full.knowledge_index_hash
        assert knowledge_artifacts.validated_artifact_bytes(reused) == knowledge_artifacts.validated_artifact_bytes(full)
        wrong = deepcopy(plan.committed_manifest)
        source = next(iter(wrong.sources))
        wrong.sources[source]["hash"] = "sha256:" + "f" * 64
        with pytest.raises(knowledge_artifacts.KnowledgeArtifactError):
            knowledge_artifacts.validate_knowledge_artifacts(
                surface_index_bytes=plan.surface_index.content, knowledge_index_bytes=receipt.content,
                manifest=wrong, _validation_receipt=receipt, _receipt_wiki_root=tmp_path)


@pytest.mark.parametrize("mutation", ["model", "validator", "scope"])
def test_late_parity_callback_cannot_publish_a_changed_receipt(tmp_path, monkeypatch, mutation):
    raw, plan = _raw(tmp_path)
    original = knowledge_artifacts._validate_manifest_knowledge_parity
    with knowledge_index._knowledge_validation_operation(tmp_path):
        receipt = knowledge_index._validated_index_receipt(raw, tmp_path)
        def raced(*args, **kwargs):
            result = original(*args, **kwargs)
            if mutation == "model":
                object.__setattr__(receipt.model, "schema_version", "llm-wiki-knowledge/receiving-invalid")
            elif mutation == "validator":
                monkeypatch.setattr(knowledge_index, "_serialize_payload", lambda *a, **k: "changed")
            else:
                knowledge_index._INDEX_VALIDATION_OPERATION.set(None)
            return result
        monkeypatch.setattr(knowledge_artifacts, "_validate_manifest_knowledge_parity", raced)
        with pytest.raises(TypeError):
            knowledge_artifacts.validate_knowledge_artifacts(**_artifact_kwargs(plan, receipt.content),
                _validation_receipt=receipt, _receipt_wiki_root=tmp_path)


def test_public_generation_and_standalone_planner_produce_exact_same_final_bytes(tmp_path):
    inputs = _planner_inputs(tmp_path)
    optimized = knowledge_generation.build_knowledge_generation_plan(inputs)
    # The ordinary public planner call outside the generation invocation must
    # validate its manual model fully; its bytes remain the independent oracle.
    raw = json.loads(optimized.knowledge_index.content)
    model = knowledge_index.validate_knowledge_index(raw)
    full = knowledge_artifacts.build_knowledge_commit_plan(tmp_path,
        surface_index_bytes=optimized.surface_index.content, knowledge_index=model,
        manifest=optimized.committed_manifest)
    assert full.knowledge_index.content == optimized.knowledge_index.content
    assert full.surface_index.content == optimized.surface_index.content
    assert full.manifest.content == optimized.manifest.content
    invalid = replace(model, schema_version="llm-wiki-knowledge/receiving-invalid")
    with pytest.raises((ValueError, TypeError)):
        knowledge_artifacts.build_knowledge_commit_plan(tmp_path,
            surface_index_bytes=optimized.surface_index.content, knowledge_index=invalid,
            manifest=optimized.committed_manifest)


@pytest.fixture
def real_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source, wiki = tmp_path / "src", tmp_path / "wiki"
    source.mkdir()
    (source / "policy.py").write_text("def clip(values, limit=3):\n    return values[:limit]\n", encoding="utf-8")
    profile = source / ".llm-wiki/source-selection.json"
    profile.parent.mkdir()
    profile.write_text(json.dumps({"schema_version": "llm-wiki-source-selection/v1",
                                  "include": ["policy.py"], "exclude": []}) + "\n", encoding="utf-8")
    api.bootstrap_wiki(str(source), str(wiki), skip_workflows=True, skip_flows=True,
                       skip_data_flow=True, skip_dependencies=True, knowledge_format="v1")
    return source, wiki, profile


@pytest.mark.parametrize("change", ["source", "configuration", "prose"])
def test_changed_inputs_b1_sync_equals_full_rebuild_from_same_history(real_project, change):
    source, wiki, profile = real_project
    oracle = wiki.parent / "oracle"
    shutil.copytree(wiki, oracle)
    if change == "source":
        path = source / "policy.py"
        path.write_text(path.read_text().replace("limit=3", "limit=2"), encoding="utf-8")
    elif change == "configuration":
        profile.write_text(json.dumps(json.loads(profile.read_text()), indent=4, sort_keys=True) + "\n", encoding="utf-8")
    else:
        for target in (wiki, oracle):
            page = target / "modules/policy.md"
            page.write_text(page.read_text() + "\n## Operator notes\nKeep the qualified prose.\n", encoding="utf-8")
    options = dict(src_dir=str(source), no_plugins=True, no_cache=True, jobs=1, force=True)
    sync_cmd.run(SimpleNamespace(**options, wiki_dir=str(wiki)))
    sync_cmd.run(SimpleNamespace(**options, wiki_dir=str(oracle), rebuild_knowledge=True))
    assert _tree(wiki) == _tree(oracle)
    assert load_knowledge_state(wiki).knowledge is not None


@pytest.mark.parametrize("failure", ["missing", "corrupt"])
@pytest.mark.parametrize("command", ["lint", "ci-check"])
def test_standalone_strict_checks_validate_actual_state_after_generation(real_project, failure, command):
    source, wiki, _ = real_project
    target = wiki / ".llm-wiki-knowledge.json"
    if failure == "missing":
        target.unlink()
    else:
        target.write_bytes(b"{corrupt receiving control\n")
    before = _tree(wiki)
    args = [command, "--src-dir", str(source), "--wiki-dir", str(wiki), "--no-cache"]
    args.extend(["--strict"] if command == "lint" else ["--no-report", "--format", "json"])
    code, stdout, stderr = _cli(args)
    assert code != 0
    assert _tree(wiki) == before
    assert "knowledge" in (stdout + stderr).casefold()


@pytest.mark.parametrize("handoff", [True, False], ids=["b1", "full-validation"])
def test_source_mutation_during_b1_parity_aborts_owning_sync(real_project, monkeypatch, handoff):
    source, wiki, _ = real_project
    path = source / "policy.py"
    path.write_text(path.read_text().replace("limit=3", "limit=2"), encoding="utf-8")
    original = knowledge_artifacts._validate_manifest_knowledge_parity
    original_operation = knowledge_generation._knowledge_validation_operation
    original_commit = knowledge_orchestration.commit_knowledge_artifacts
    artifacts = {name: (wiki / name).read_bytes() for name in (
        ".llm-wiki-surface.json", ".llm-wiki-knowledge.json", ".llm-wiki-manifest.json")}
    timeline = []
    raced = active_generation = False
    @contextmanager
    def operation(root):
        nonlocal active_generation
        active_generation = True
        try:
            with original_operation(root) if handoff else nullcontext():
                yield
        finally:
            active_generation = False
    monkeypatch.setattr(knowledge_generation, "_knowledge_validation_operation", operation)
    def mutate(*args, **kwargs):
        nonlocal raced
        result = original(*args, **kwargs)
        if not raced and active_generation:
            raced = True
            timeline.append("final-manifest-parity-complete")
            path.write_text(path.read_text() + "\n# concurrent source edit\n", encoding="utf-8")
            timeline.append("external-source-edit")
        return result
    def committed(*args, **kwargs):
        timeline.append("native-artifact-commit")
        return original_commit(*args, **kwargs)
    monkeypatch.setattr(knowledge_artifacts, "_validate_manifest_knowledge_parity", mutate)
    monkeypatch.setattr(knowledge_orchestration, "commit_knowledge_artifacts", committed)
    code, _, _ = _cli(["sync", "--src-dir", str(source), "--wiki-dir", str(wiki), "--no-cache", "--jobs", "1"])
    assert raced and code != 0
    assert timeline == ["final-manifest-parity-complete", "external-source-edit"]
    assert {name: (wiki / name).read_bytes() for name in artifacts} == artifacts


def test_commit_stage_source_edit_keeps_manifest_old_and_partial_state_unreadable_until_explicit_recovery(real_project, monkeypatch):
    source, wiki, _ = real_project
    before = _tree(wiki)
    path = source / "policy.py"
    path.write_text(path.read_text().replace("limit=3", "limit=2"), encoding="utf-8")
    original_finalize = sync_cmd.finalize_runtime_knowledge
    stages = []
    def finalize(inputs, *, dry_run=False):
        def inject(stage):
            stages.append(stage)
            if stage is knowledge_artifacts.CommitStage.KNOWLEDGE_INDEX_WRITTEN:
                path.write_text(path.read_text() + "\n# concurrent commit-stage source edit\n", encoding="utf-8")
        return original_finalize(inputs, dry_run=dry_run, fault_injector=inject)
    monkeypatch.setattr(sync_cmd, "finalize_runtime_knowledge", finalize)
    args = ["sync", "--src-dir", str(source), "--wiki-dir", str(wiki), "--no-cache", "--jobs", "1"]
    code, _, stderr = _cli(args)
    assert code != 0 and "Source changed" in stderr
    assert knowledge_artifacts.CommitStage.KNOWLEDGE_INDEX_WRITTEN in stages
    assert knowledge_artifacts.CommitStage.MANIFEST_WRITTEN not in stages
    assert (wiki / ".llm-wiki-manifest.json").read_bytes() == before[".llm-wiki-manifest.json"]
    assert (wiki / ".llm-wiki-knowledge.json").read_bytes() != before[".llm-wiki-knowledge.json"]
    partial = _tree(wiki)
    for _ in range(2):
        with pytest.raises(KnowledgeStateLoadError):
            load_knowledge_state(wiki)
        assert _tree(wiki) == partial

    # Explicit test-owned recovery restores the complete admitted Markdown
    # preimage, then uses the existing full planner/manifest-last commit owner.
    # It establishes captured integrity; it does not acknowledge current prose.
    native_paths = {".llm-wiki-surface.json", ".llm-wiki-knowledge.json", ".llm-wiki-manifest.json"}
    for relative, content in before.items():
        if relative not in native_paths:
            (wiki / relative).write_bytes(content)
    old_manifest = SyncManifest.from_payload(json.loads(before[".llm-wiki-manifest.json"]))
    recovery = knowledge_artifacts.build_knowledge_commit_plan(wiki,
        surface_index_bytes=before[".llm-wiki-surface.json"],
        knowledge_index_bytes=before[".llm-wiki-knowledge.json"], manifest=old_manifest)
    knowledge_artifacts.commit_knowledge_artifacts(recovery)
    assert load_knowledge_state(wiki).knowledge is not None
    monkeypatch.setattr(sync_cmd, "finalize_runtime_knowledge", original_finalize)
    code, _, _ = _cli([*args, "--rebuild-knowledge"])
    assert code == 0
    current = load_knowledge_state(wiki)
    assert current.knowledge is not None and current.manifest_basis is not None
    assert "concurrent commit-stage source edit" in path.read_text()
