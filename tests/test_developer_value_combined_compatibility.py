"""Compatible receiving and unavailable states compose without hidden authority."""

from __future__ import annotations

from hashlib import sha256
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import knowledge_orchestration, task_context_v2
from llm_wiki_cli.services.context_packet import ContextPacketUnavailableError
from llm_wiki_cli.services.knowledge_artifacts import CommitStage, commit_knowledge_artifacts
from llm_wiki_cli.services.knowledge_governance import load_governance
from llm_wiki_cli.services.knowledge_storage import canonical_bytes
from llm_wiki_cli.services.maintenance_service import load_recovery_snapshot
from llm_wiki_cli.services.mcp_server import McpWikiError, McpWikiService
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.developer_value.workflow_fixtures import (
    BODY_PROSE, VIEW, compact_payload, mutate_source, prepare_workflow,
    record_workflow_trace, sync_workflow, task_request, write_description,
)
from tests.developer_value.workflow_oracles import (
    REQUIRED_GAP_STATES, assert_coverage_gap, assert_coverage_preserved,
)


def _inventory(project):
    # Observe only the source/wiki surfaces. Explicit receipt/recovery writes
    # outside these roots remain separate writer operations.
    return {name: {"sha256": sha256(raw).hexdigest(), "bytes": len(raw),
                   "mtime_ns": (project.root / name).stat().st_mtime_ns}
            for name, raw in project.tree().items()
            if name.startswith(("src/", "wiki/"))}


def _cli(monkeypatch, capsys, *arguments, request=None, failure=False):
    with monkeypatch.context() as patch:
        patch.setattr(sys, "argv", ["llm-wiki", *arguments])
        if request is not None:
            patch.setattr(sys, "stdin", io.StringIO(json.dumps(request)))
        if failure:
            with pytest.raises(SystemExit) as stopped:
                cli.main()
            assert stopped.value.code != 0
        else:
            cli.main()
    return capsys.readouterr()


def _arguments(project):
    return ["--src-dir", str(project.source), "--wiki-dir", str(project.wiki)]


def _status(project):
    return api.get_maintenance_status(**project.options, limit=100)


def _window(status):
    return next(row for row in status["records"]
                if row["coordinate"]["qualified_owner"] == "Window"
                and row["target"]["canonical_path"] == "entities/Window.md"
                and row["basis_available"])


def _ack(project, status, row):
    assert status["state_hash"] is not None and row["expected_basis"] is not None
    return api.acknowledge_maintenance(**project.options, record_id=row["record_id"],
        expected_state_hash=status["state_hash"], expected_basis=row["expected_basis"],
        actor_kind="agent", actor_id="owned-compatibility-agent")


def _trace(project, scenario, before, **observations):
    after = _inventory(project)
    assert after == before
    assert not (project.root / "source-execution-tripwire").exists()
    record_workflow_trace(project, scenario, {"inventory_before": before,
        "inventory_after": after, "read_only_checked": True,
        "inventory_scope": "aggregate source/wiki read interval; bytes, presence and mtime_ns",
        "target_execution_observed": False, **observations})


@pytest.mark.parametrize("variant", ["source-only", "native-absent", "legacy", "adopted-flat", "sharded", "packed"])
def test_compatible_default_and_compact_receiving_share_canonical_gaps_without_adoption(
    tmp_path, monkeypatch, capsys, variant
):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, variant)
    capsys.readouterr()
    # Explicit off is a separate source-only request, even when native storage
    # exists. It does not quietly downgrade a required native request.
    request = task_request(native=False)
    before = _inventory(project)
    compact, canonical, expanded = compact_payload(project, request)
    assert_coverage_preserved(canonical, expanded)
    for identity, states in REQUIRED_GAP_STATES.items():
        assert_coverage_gap(expanded, identity, states=states)
    assert json.loads(compact.rendered)["schema_version"] == "llm-wiki-task-compact/v1"
    plain = _cli(monkeypatch, capsys, "task-context", "--request", "-",
                 *_arguments(project), "--allow-full-inventory", request=request)
    assert plain.err == "" and plain.out == compact.canonical_text
    # Canonical publication is explicitly requested and outside observed roots.
    receipt = tmp_path / "canonical-receipt.json"
    emitted = _cli(monkeypatch, capsys, "task-context", "--request", "-",
        *_arguments(project), "--allow-full-inventory", "--view", "compact-v1",
        "--view-budget-tokens", "32000", "--canonical-output", str(receipt), request=request)
    assert emitted.err == "" and emitted.out == compact.rendered
    assert receipt.read_text() == plain.out
    service = McpWikiService(str(project.source), str(project.wiki),
                            workflow_policy=project.context_options["policy"])
    service_text = service.build_task_context(request)
    assert service_text == plain.out
    status = _status(project)
    if variant in {"source-only", "native-absent", "legacy"}:
        assert status["availability"] in {"unavailable", "unadopted"}
        assert status["records"] == []
        assert not (project.wiki / ".llm-wiki-maintenance-adoption.json").exists()
    else:
        assert status["records"] and all(row["recorded_status"] == "pending" for row in status["records"])
    _trace(project, "compatible-receiving", before, request=request, canonical=canonical,
        compact=compact.rendered, cli_default=plain.out, cli_compact=emitted.out,
        service_canonical=service_text, maintenance_status=status,
        service_transport="McpWikiService direct local service call", native_request=False,
        canonical_receipt_writer="explicit CLI output outside source/wiki")


@pytest.mark.parametrize("variant", ["legacy", "adopted-flat"])
def test_flat_native_legacy_contract_remains_distinct_from_selected_v2_refusal(
    tmp_path, monkeypatch, capsys, variant
):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, variant)
    capsys.readouterr()
    before = _inventory(project)
    request = task_request(native=True, schema="v1")
    canonical = api.build_task_context(request, **project.context_options)
    assert canonical.ok
    payload = api.validate_task_context(canonical.rendered, request, policy=project.context_options["policy"])
    assert next(row for row in payload["coverage"] if row["requirement_id"] == "concept")["satisfied"]
    with pytest.raises(api.InvalidRequestError, match="task v2") as old_compact:
        api.build_compact_task_context(request, view_options=VIEW, **project.context_options)
    selected = task_request(native=True)
    with pytest.raises(api.InvalidRequestError, match="selected native reads require explicit") as unsupported:
        api.build_task_context(selected, **project.context_options)
    _trace(project, "flat-native-compatibility", before, request=request,
        legacy_canonical=canonical.rendered, v1_compact_refusal=str(old_compact.value),
        v2_selected_request=selected, v2_selected_refusal=str(unsupported.value),
        implicit_migration=False, native_v2_solved=False)


@pytest.mark.parametrize("variant", ["native-absent", "sharded"])
def test_required_native_absent_or_corrupt_is_refused_across_receiving_routes(
    tmp_path, monkeypatch, capsys, variant
):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, variant)
    capsys.readouterr()
    if variant == "sharded":
        # Damage the active locator, not an unused flat artifact.
        (project.wiki / ".llm-wiki-knowledge.json").write_text("{ invalid owned native locator\n")
    request = task_request(native=True)
    before = _inventory(project)
    with pytest.raises(api.LlmWikiApiError) as refused:
        api.build_task_context(request, **project.context_options)
    service = McpWikiService(str(project.source), str(project.wiki),
                            workflow_policy=project.context_options["policy"])
    with pytest.raises(McpWikiError) as service_refused:
        service.build_task_context(request)
    output = _cli(monkeypatch, capsys, "task-context", "--request", "-",
        *_arguments(project), "--allow-full-inventory", request=request, failure=True)
    assert output.out == ""
    diagnostic = json.loads(output.err)
    assert diagnostic["ok"] is False and diagnostic["error"]["code"]
    separate = task_request(native=False)
    fallback = api.build_task_context(separate, **project.context_options)
    assert fallback.ok
    api.validate_task_context(fallback.rendered, separate, policy=project.context_options["policy"])
    _trace(project, "required-native-refusal", before, native_request=request,
        api_error=str(refused.value), service_error=str(service_refused.value), cli_error=diagnostic,
        separate_source_only_request=separate, separate_source_only_canonical=fallback.rendered,
        native_solved=False, unavailable_or_corrupt=True, implicit_source_only_fallback=False)


def test_named_helper_unavailability_clears_current_custody_without_old_context_fallback(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, "source-only")
    capsys.readouterr()
    request = task_request()
    with api.open_context_session(**project.context_options) as owner:
        first = owner.read_compact(request, view_options=VIEW)
        assert first.canonical is not None and first.result_id is not None
        identity = first.canonical.to_payload()["request_id"], first.result_id
        captured = owner.canonical_receipt(*identity)
        assert captured.validation_scope == "historical-captured"
        mutate_source(project, "default")
        before = _inventory(project)

        def unavailable(*args, **kwargs):
            raise ContextPacketUnavailableError("owned selected-source helper is unavailable", field="src_dir")

        with monkeypatch.context() as fault:
            fault.setattr(task_context_v2.context, "get_inventory", unavailable)
            with pytest.raises(api.LlmWikiApiError) as refused:
                owner.read_compact(request, view_options=VIEW, if_result_id=first.result_id,
                                   if_view_id=first.view_id, delta=True)
        with pytest.raises(api.InvalidRequestError, match="not retained") as custody:
            owner.canonical_receipt(*identity)
        _trace(project, "synthetic-helper-unavailability", before, request=request,
            historical_canonical=captured.canonical.rendered, historical_scope=captured.validation_scope,
            current_error=str(refused.value), custody_error=str(custody.value),
            fault_is_synthetic=True, actual_host_helper_absent=False, current_context_emitted=False,
            unavailable_solved=False)


def test_optional_governance_preserves_human_review_boundary_during_agent_ack_and_sync(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, "adopted-flat")
    capsys.readouterr()
    output = _cli(monkeypatch, capsys, "knowledge", "init", "--wiki-dir", str(project.wiki),
                  "--bundle-id", "kb_owned_compatibility")
    assert json.loads(output.out)["bundle_id"] == "kb_owned_compatibility"
    ledger = load_governance(project.wiki).ledger
    uid = next(uid for uid, concept in ledger.concepts.items()
               if concept.locator == "llm-wiki://entities/Window")
    assert ledger.review_events == {}
    governance_path = project.wiki / ".llm-wiki-governance.json"
    governance_before = governance_path.read_bytes()
    before = _inventory(project)
    output = _cli(monkeypatch, capsys, "knowledge", "review", "--wiki-dir", str(project.wiki),
        "--uid", uid, "--section", "llm-wiki://entities/Window#section/Description",
        "--reviewer-kind", "agent", "--reviewer-id", "owned-compatibility-agent",
        "--method", "source-reading", "--method-version", "1", failure=True)
    assert output.out == "" and "invalid choice: 'agent'" in output.err
    assert "choose from 'human'" in output.err
    _trace(project, "governance-agent-refusal", before, error=output.err,
        governance_review_available_to_agent=False, human_approval_supplied=False)
    ready = _status(project)
    row = _window(ready)
    acknowledged = _ack(project, ready, row)
    assert acknowledged["actor"]["kind"] == "agent" and acknowledged["governance_effect"] == "none"
    assert governance_path.read_bytes() == governance_before
    stale = _status(project)
    stale_row = _window(stale)
    mutate_source(project, "body")
    before = _inventory(project)
    with pytest.raises(api.WorkspaceStateError) as refused:
        _ack(project, stale, stale_row)
    assert refused.value.code == "maintenance-conflict"
    _trace(project, "governed-stale-agent-ack", before, stale_error=str(refused.value),
        ordinary_ack=acknowledged, human_approval_supplied=False)
    sync_workflow(project)
    capsys.readouterr()
    before = _inventory(project)
    pending = _status(project)
    assert _window(pending)["recorded_status"] == "pending"
    assert governance_path.read_bytes() == governance_before
    assert load_governance(project.wiki).ledger.review_events == {}
    _trace(project, "governed-pending-after-sync", before, maintenance_status=pending,
        ordinary_ack_is_human_review=False, governance_review_events=0)


def test_interrupted_sync_recovery_preserves_source_prose_and_durable_pending(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, "adopted-flat")
    capsys.readouterr()
    initial = _status(project)
    row = _window(initial)
    _ack(project, initial, row)
    acknowledged_state = canonical_bytes(SyncManifest.load(project.wiki).maintenance_state)
    mutate_source(project, "body")
    write_description(project, BODY_PROSE)
    exact_source = (project.source / "policy.py").read_bytes()
    exact_prose = (project.wiki / "entities/Window.md").read_bytes()
    previous_recoveries = set((project.root / ".llm-wiki-maintenance-recovery/maintenance-preimages").glob("*"))

    def interrupt(plan, **options):
        def after_write(stage):
            if stage == CommitStage.KNOWLEDGE_INDEX_WRITTEN:
                raise RuntimeError("owned interrupted sync publication")
        return commit_knowledge_artifacts(plan, fault_injector=after_write)

    with monkeypatch.context() as fault:
        fault.setenv("LLM_WIKI_DEBUG", "1")
        fault.setattr(knowledge_orchestration, "commit_knowledge_artifacts", interrupt)
        with pytest.raises(RuntimeError, match="owned interrupted sync") as failure:
            sync_workflow(project)
    capsys.readouterr()
    failed_inventory = _inventory(project)
    recovery_roots = set((project.root / ".llm-wiki-maintenance-recovery/maintenance-preimages").glob("*"))
    created_recoveries = recovery_roots - previous_recoveries
    assert len(created_recoveries) == 1
    recovery = created_recoveries.pop()
    _, files, _ = load_recovery_snapshot(recovery, allow_captured_preimage=True)
    assert files["entities/Window.md"] == exact_prose
    marker = json.loads((project.wiki / ".llm-wiki-maintenance-adoption.json").read_text())
    restored = api.recover_maintenance(str(project.wiki), recovery_dir=recovery,
        expected_adoption_id=marker["adoption_id"], allow_captured_preimage=True)
    assert restored["restored"] and restored["requires_sync"] and not restored["prose_basis_validated"]
    assert (project.source / "policy.py").read_bytes() == exact_source
    assert (project.wiki / "entities/Window.md").read_bytes() == exact_prose
    assert canonical_bytes(SyncManifest.load(project.wiki).maintenance_state) == acknowledged_state
    # The durable record is old, but live evaluation cannot treat it current.
    overlay = _status(project)
    assert _window(overlay)["effective_status"] == "pending"
    sync_workflow(project)
    capsys.readouterr()
    before = _inventory(project)
    pending = _status(project)
    selected = _window(pending)
    assert selected["record_id"] == row["record_id"] and selected["recorded_status"] == "pending"
    assert (project.source / "policy.py").read_bytes() == exact_source
    assert (project.wiki / "entities/Window.md").read_bytes() == exact_prose
    interpreter = Path(sys.executable)
    assert interpreter.is_file()
    restarted = subprocess.run([str(interpreter), "-I", "-c",
        "from llm_wiki_cli import cli; cli.main()", "maintenance", "status",
        *_arguments(project), "--record-id", row["record_id"], "--format", "json"],
        cwd=project.root, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, check=True, timeout=30)
    assert restarted.stderr == ""
    actual_restart = json.loads(restarted.stdout)
    assert actual_restart["records"][0]["recorded_status"] == "pending"
    _trace(project, "interrupted-sync-recovery", before, interrupted_error=str(failure.value),
        inventory_after_interruption=failed_inventory, explicit_recovery=restored,
        maintenance_status=pending, fresh_cli_status=actual_restart,
        fresh_cli_process={"exit_code": restarted.returncode, "stdout": restarted.stdout,
                           "stderr": restarted.stderr},
        source_sha256=sha256(exact_source).hexdigest(), prose_sha256=sha256(exact_prose).hexdigest(),
        pending_acknowledged=False, recovery_is_explicit=True)
