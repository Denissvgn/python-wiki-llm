"""Controlled source/prose review follows owning sync and ordinary agent CAS."""

from copy import deepcopy
import json
from pathlib import Path
import os
import subprocess
import sys

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services.knowledge_artifacts import CommitStage, commit_knowledge_artifacts
from llm_wiki_cli.services.knowledge_governance import load_governance
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.developer_value.workflow_fixtures import (
    BODY_PROSE, DEFAULT_PROSE, INITIAL_PROSE, prepare_workflow, mutate_source, record_workflow_trace,
    run_behavior_oracle, sync_workflow, write_description, task_request, compact_payload,
)
from tests.developer_value.workflow_oracles import (
    assert_clip_behavior, assert_source_change, assert_read_only,
    assert_coverage_preserved, assert_coverage_gap, REQUIRED_GAP_STATES,
)


def _row(status, owner='Window'):
    return next(row for row in status['records'] if row['coordinate']['qualified_owner'] == owner
                and row['target']['canonical_path'] == f'entities/{owner}.md')


def _ack(project, status, row):
    assert row['basis_available'] and row['expected_basis'] is not None
    return api.acknowledge_maintenance(**project.options, record_id=row['record_id'],
        expected_state_hash=status['state_hash'], expected_basis=row['expected_basis'],
        actor_kind='agent', actor_id='owned-after-change-agent')


def _assert_writer_preserves_authority(before, after):
    allowed = tuple(path for path in set(before) | set(after)
                    if path.startswith(".llm-wiki-maintenance-recovery/maintenance-preimages/"))
    assert_read_only(before, after, allowed_changes=allowed)


def _restart_status(project):
    interpreter = Path(sys.executable)
    assert interpreter.is_file()
    code = ('import json,sys; from llm_wiki_cli import api; '
            'print(json.dumps(api.get_maintenance_status(src_dir=sys.argv[1],wiki_dir=sys.argv[2],live=False,limit=100)))')
    child = subprocess.run([str(interpreter), '-I', '-c', code, str(project.source), str(project.wiki)],
        cwd=project.root, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True,
        text=True, check=True, timeout=30)
    return json.loads(child.stdout)


@pytest.mark.parametrize('variant', ['adopted-flat', 'sharded', 'packed'])
@pytest.mark.parametrize('change', ['body', 'default'])
def test_explicit_change_sync_agent_review_ack_and_restart_preserve_unrelated_authority(tmp_path, monkeypatch, variant, change):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, variant)
    source_before = (project.source / 'policy.py').read_bytes()
    before_runtime = run_behavior_oracle(project, 'before')
    assert_clip_behavior(before_runtime, 'before')
    status = api.get_maintenance_status(**project.options, live=True, limit=100)
    target = _row(status)
    _ack(project, status, target)
    stable_status = api.get_maintenance_status(**project.options, live=True, limit=100)
    _ack(project, stable_status, _row(stable_status, 'Stable'))
    captured = api.get_maintenance_status(**project.options, live=True, limit=100)
    stale = _row(captured)
    stable_id = _row(captured, 'Stable')['record_id']
    authority = SyncManifest.load(project.wiki)
    assert authority.maintenance_state is not None
    stable_record = deepcopy(authority.maintenance_state['records'][stable_id])
    manifest_version = authority.storage_version
    mutate_source(project, change)
    assert_source_change(source_before, (project.source / 'policy.py').read_bytes(), change)
    after_runtime = run_behavior_oracle(project, change)
    assert_clip_behavior(after_runtime, change)
    assert after_runtime != before_runtime
    read_before = project.tree()
    overlay = api.get_maintenance_status(**project.options, live=True, limit=100)
    current = _row(overlay)
    assert current['recorded_status'] == 'acknowledged' and current['effective_status'] == 'pending'
    assert 'executable-syntax-changed' in current['reasons'] or 'scope-signature-changed' in current['reasons']
    assert _row(overlay, 'Stable')['effective_status'] == 'acknowledged'
    diagnostic = api.inspect_concept("llm-wiki://entities/Window", live=True, **project.options)
    concept = diagnostic["concept"]["concept"]
    assert concept is not None and concept["implementation"]["state"] == "changed"
    assert concept["freshness"]["state"] == ("nonsemantic-source-change" if change == "body" else "source-changed")
    independent = api.inspect_concept("llm-wiki://entities/Stable", live=True, **project.options)
    peer = independent["concept"]["concept"]
    assert peer is not None and peer["implementation"]["state"] == "unchanged"
    assert peer["freshness"]["state"] == "current"
    assert_read_only(read_before, project.tree())
    with pytest.raises(api.LlmWikiApiError):
        _ack(project, captured, stale)
    # A rejected explicit writer can retain an operational recovery preimage;
    # it cannot change source, canonical prose, marker or durable owner.
    after_rejected = project.tree()
    _assert_writer_preserves_authority(read_before, after_rejected)
    sync_workflow(project)
    owner = SyncManifest.load(project.wiki)
    assert owner.maintenance_state is not None and owner.storage_version == manifest_version
    assert owner.maintenance_state['records'][current['record_id']]['status'] == 'pending'
    assert owner.maintenance_state['records'][stable_id] == stable_record
    sync_workflow(project)
    before_restart = project.tree()
    restarted = _restart_status(project)
    pending = _row(restarted)
    assert pending['recorded_status'] == 'pending' and pending['effective_status'] is None
    assert pending['expected_basis'] is None
    assert_read_only(before_restart, project.tree())
    # Explicit agent review is a separately labeled prose action against the
    # fixed behavioral cases; ordinary acknowledgment is neither runtime proof nor human approval.
    reviewed = BODY_PROSE if change == 'body' else DEFAULT_PROSE
    page = project.wiki / 'entities/Window.md'
    assert INITIAL_PROSE in page.read_text()
    write_description(project, reviewed)
    prose_bytes = page.read_bytes()
    before_prose_read = project.tree()
    dirty = api.get_maintenance_status(**project.options, live=True, limit=100)
    assert dirty['requires_sync'] and not dirty['native_prose_coherent']
    assert_read_only(before_prose_read, project.tree())
    with pytest.raises(api.LlmWikiApiError):
        _ack(project, dirty, _row(dirty))
    rejected = project.tree()
    _assert_writer_preserves_authority(before_prose_read, rejected)
    sync_workflow(project)
    assert page.read_bytes() == prose_bytes
    fresh = api.get_maintenance_status(**project.options, live=True, limit=100)
    acknowledged = _ack(project, fresh, _row(fresh))
    assert acknowledged['actor'] == {'kind': 'agent', 'actor_id': 'owned-after-change-agent', 'authority': 'ordinary-maintenance'}
    assert acknowledged['governance_effect'] == 'none' and acknowledged['changed']
    before_retry = project.tree()
    retry = _ack(project, fresh, _row(fresh))
    assert not retry['changed'] and retry['acknowledgment_id'] == acknowledged['acknowledgment_id']
    _assert_writer_preserves_authority(before_retry, project.tree())
    durable = _restart_status(project)
    assert _row(durable)['recorded_status'] == 'acknowledged'
    assert _row(durable)['effective_status'] is None
    assert not (project.wiki / '.llm-wiki-governance.json').exists()
    assert not (project.root / 'source-execution-tripwire').exists()
    assert load_knowledge_state(project.wiki).status is KnowledgeLoadState.VALID
    record_workflow_trace(project, f"after-{change}", {
        "source_before": source_before.decode(), "source_after": (project.source / "policy.py").read_text(),
        "runtime_before": before_runtime, "runtime_after": after_runtime, "source_overlay": overlay,
        "diagnostic": diagnostic, "independent_diagnostic": independent,
        "pending_restart": restarted, "reviewed_prose": reviewed, "prose_bytes": prose_bytes.decode(),
        "current_status": fresh, "acknowledgment": acknowledged, "retry": retry,
        "acknowledged_restart": durable, "stable_record_preserved": True,
        "review_actor": "agent", "governance_effect": "none", "runtime_scope": "fixed-owned-cases",
    })


@pytest.mark.parametrize('variant', ['source-only', 'native-absent', 'legacy'])
def test_after_change_source_only_context_retains_behavior_and_native_gaps_without_setup(tmp_path, monkeypatch, variant):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, variant)
    original = (project.source / 'policy.py').read_bytes()
    mutate_source(project, 'body')
    assert_source_change(original, (project.source / 'policy.py').read_bytes(), 'body')
    runtime = run_behavior_oracle(project, 'body')
    assert_clip_behavior(runtime, 'body')
    before = project.tree()
    request = task_request(native=False)
    _, canonical, expanded = compact_payload(project, request)
    assert_coverage_preserved(canonical, expanded)
    for requirement in ['missing', 'ambiguous', 'behavior']:
        assert_coverage_gap(canonical, requirement, states=tuple(REQUIRED_GAP_STATES[requirement]))
    assert canonical['state'] != 'covered'
    required = task_request(native=True)
    with pytest.raises(api.LlmWikiApiError):
        api.build_task_context(required, **project.context_options)
    assert_read_only(before, project.tree())
    assert not (project.wiki / '.llm-wiki-maintenance-adoption.json').exists()
    assert not (project.root / 'source-execution-tripwire').exists()
    record_workflow_trace(project, "after-source-only", {"request": request, "canonical": canonical,
        "expanded": expanded, "source_before": original.decode(),
        "source_after": (project.source / "policy.py").read_text(), "runtime_after": runtime,
        "native_required": "refused", "read_only_checked": True})


def test_optional_governance_retains_no_human_review_or_approval_from_agent_ack(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, 'sharded')
    from tests.test_knowledge_cmd import _run
    _run(['init', '--wiki-dir', str(project.wiki), '--bundle-id', 'kb_owned_window'])
    ledger = load_governance(project.wiki).ledger
    assert not ledger.review_events
    mutate_source(project, 'body')
    sync_workflow(project)
    write_description(project, BODY_PROSE)
    sync_workflow(project)
    before = (project.wiki / '.llm-wiki-governance.json').read_bytes()
    status = api.get_maintenance_status(**project.options, live=True, limit=100)
    result = _ack(project, status, _row(status))
    assert result['governance_effect'] == 'none'
    assert (project.wiki / '.llm-wiki-governance.json').read_bytes() == before
    assert not load_governance(project.wiki).ledger.review_events
    record_workflow_trace(project, "after-governance", {"status": status, "acknowledgment": result,
        "ledger_bytes": before.decode(), "human_review_events": [], "reviewed_prose": BODY_PROSE})


def test_interrupted_prose_reanchor_is_rejected_then_explicitly_recovered_before_ack(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, 'sharded')
    mutate_source(project, 'body')
    sync_workflow(project)
    write_description(project, BODY_PROSE)
    page = project.wiki / 'entities/Window.md'
    expected_prose = page.read_bytes()
    owner = SyncManifest.load(project.wiki)
    assert owner.maintenance_state is not None
    previous_state = deepcopy(owner.maintenance_state)
    adoption_id = previous_state['adoption_id']
    preimage_root = project.root / ".llm-wiki-maintenance-recovery/maintenance-preimages"
    existing_preimages = set(preimage_root.glob("*"))
    from llm_wiki_cli.services import knowledge_orchestration
    def stop(stage):
        if stage == CommitStage.KNOWLEDGE_INDEX_WRITTEN:
            raise RuntimeError('owned interrupted publication')
    def interrupted(plan, **options):
        return commit_knowledge_artifacts(plan, **{**options, 'fault_injector': stop})
    with monkeypatch.context() as fault:
        fault.setenv('LLM_WIKI_DEBUG', '1')
        fault.setattr(knowledge_orchestration, 'commit_knowledge_artifacts', interrupted)
        with pytest.raises(RuntimeError, match='owned interrupted'):
            sync_workflow(project)
    before_read = project.tree()
    with pytest.raises(api.LlmWikiApiError):
        api.build_task_context(task_request(native=True), **project.context_options)
    assert_read_only(before_read, project.tree())
    preimages = sorted(set(preimage_root.glob('*')) - existing_preimages)
    assert len(preimages) == 1
    from llm_wiki_cli.services.maintenance_service import load_recovery_snapshot
    metadata, recovered_files, recovered_owner = load_recovery_snapshot(preimages[0], allow_captured_preimage=True)
    assert metadata['kind'] == 'captured-preimage'
    assert recovered_files['entities/Window.md'] == expected_prose
    assert recovered_owner.maintenance_state == previous_state
    with pytest.raises(api.LlmWikiApiError):
        api.recover_maintenance(str(project.wiki), recovery_dir=preimages[0], expected_adoption_id=adoption_id)
    recovered = api.recover_maintenance(str(project.wiki), recovery_dir=preimages[0],
        expected_adoption_id=adoption_id, allow_captured_preimage=True)
    assert recovered['requires_sync'] and not recovered['prose_basis_validated']
    assert page.read_bytes() == expected_prose and SyncManifest.load(project.wiki).maintenance_state == previous_state
    sync_workflow(project)
    assert page.read_bytes() == expected_prose
    status = api.get_maintenance_status(**project.options, live=True, limit=100)
    assert _row(status)['effective_status'] == 'pending'
    acknowledged = _ack(project, status, _row(status))
    assert load_knowledge_state(project.wiki).status is KnowledgeLoadState.VALID
    record_workflow_trace(project, "after-interrupted-recovery", {"recovery": recovered,
        "preimage_kind": metadata["kind"], "prose_bytes": expected_prose.decode(),
        "status_after_reanchor": status, "acknowledgment": acknowledged,
        "read_refusal_preserved_authority": True, "recovery_mode": "explicit-captured-preimage"})
