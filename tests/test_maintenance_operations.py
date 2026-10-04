"""Current ordinary review is explicit, scoped, and read-only until acknowledged."""
from pathlib import Path
from unittest.mock import patch
import sys

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.maintenance_service import (
    adopt_maintenance_authority, get_maintenance_status_authority,
    acknowledge_maintenance_authority,
)
from llm_wiki_cli.services.maintenance_protocol import snapshot_wiki, MaintenanceProtocolError
from llm_wiki_cli.services.maintenance_shapes import MaintenanceError
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.developer_value.fixtures import POLICY_SOURCE


@pytest.fixture
def adopted(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(POLICY_SOURCE)
    api.bootstrap_wiki("src", "wiki")
    adopt_maintenance_authority("src", "wiki", recovery_dir="recovery")
    capsys.readouterr()
    return Path("wiki")


def _status():
    return get_maintenance_status_authority("src", "wiki")


def _ack(status, row, **changes):
    options = dict(record_id=row["record_id"], expected_state_hash=status["state_hash"],
                   expected_basis=row["expected_basis"], actor_kind="agent", actor_id="fixture-agent")
    options.update(changes)
    return acknowledge_maintenance_authority("src", "wiki", **options)


def _sync():
    with patch.object(sys, "argv", ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"]):
        cli.main()


def test_status_read_only_initial_unreviewed_and_snapshot_is_historical(adopted):
    before = snapshot_wiki(adopted)
    live = _status()
    assert live["availability"] == "ready" and live["live_evaluation_performed"]
    assert live["records"]
    assert all(row["effective_status"] == "pending" and "unreviewed" in row["reasons"] for row in live["records"])
    assert all(row["basis_available"] for row in live["records"])
    stored = get_maintenance_status_authority("missing-source", "wiki", live=False)
    assert not stored["live_evaluation_performed"]
    assert all(row["effective_status"] is None and row["expected_basis"] is None for row in stored["records"])
    assert snapshot_wiki(adopted) == before


def test_agent_ack_is_scoped_and_exact_retry_is_idempotent(adopted):
    status = _status()
    row = next(r for r in status["records"] if r["coordinate"]["qualified_owner"] == "Batch")
    result = _ack(status, row)
    assert result["changed"] and result["governance_effect"] == "none"
    assert result["actor"] == {"kind": "agent", "actor_id": "fixture-agent", "authority": "ordinary-maintenance"}
    state = SyncManifest.load(adopted).maintenance_state
    assert state is not None
    assert state["records"][row["record_id"]]["status"] == "acknowledged"
    assert any(value["status"] == "pending" for key, value in state["records"].items() if key != row["record_id"])
    assert not (adopted / ".llm-wiki-governance.json").exists()
    before = snapshot_wiki(adopted)
    retry = _ack(status, row)
    assert not retry["changed"] and retry["acknowledgment_id"] == result["acknowledgment_id"]
    assert snapshot_wiki(adopted) == before
    _sync()
    assert SyncManifest.load(adopted).maintenance_state == state


def test_source_edit_reopens_live_status_and_stale_ack_cannot_publish(adopted):
    status = _status()
    row = next(r for r in status["records"] if r["coordinate"]["qualified_owner"] == "Batch")
    _ack(status, row)
    Path("src/policy.py").write_text(POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    before = snapshot_wiki(adopted)
    live = _status()
    current = next(r for r in live["records"] if r["record_id"] == row["record_id"])
    assert current["recorded_status"] == "acknowledged" and current["effective_status"] == "pending"
    assert "executable-syntax-changed" in current["reasons"]
    with pytest.raises((MaintenanceProtocolError, MaintenanceError)):
        _ack(status, row)
    assert snapshot_wiki(adopted) == before
    _sync()
    state = SyncManifest.load(adopted).maintenance_state
    assert state is not None and state["records"][row["record_id"]]["status"] == "pending"


def test_prose_edit_is_visible_without_read_mutation_then_sync_ack(adopted):
    from tests.test_knowledge_commands import _write_reviewed_description
    status = _status()
    row = next(r for r in status["records"] if r["coordinate"]["qualified_owner"] == "Batch")
    _ack(status, row)
    page = adopted / row["target"]["canonical_path"]
    _write_reviewed_description(page, "The reviewed prose changed independently.")
    before = snapshot_wiki(adopted)
    live = _status()
    current = next(r for r in live["records"] if r["record_id"] == row["record_id"])
    assert current["effective_status"] == "pending" and "prose-changed" in current["reasons"]
    assert live["requires_sync"] and not live["native_prose_coherent"]
    with pytest.raises(MaintenanceProtocolError):
        _ack(live, current)
    assert snapshot_wiki(adopted) == before
    _sync()
    ready = _status()
    current = next(r for r in ready["records"] if r["record_id"] == row["record_id"])
    result = _ack(ready, current)
    assert result["changed"]
    assert "The reviewed prose changed independently." in page.read_text()


def test_python_and_read_only_mcp_status_agree_without_mutation(adopted):
    from llm_wiki_cli.services.mcp_server import McpWikiService, _register_mcp_tools
    from tests.test_mcp import RecordingMcpServer
    before = snapshot_wiki(adopted)
    expected = api.get_maintenance_status("src", "wiki")
    service = McpWikiService(src_dir="src", wiki_dir="wiki")
    assert service.get_maintenance_status() == expected
    registrar = RecordingMcpServer()
    _register_mcp_tools(registrar, service)
    assert "get_maintenance_status" in registrar.tool_names
    assert not {"adopt_maintenance", "acknowledge_maintenance", "recover_maintenance"} & set(registrar.tool_names)
    assert snapshot_wiki(adopted) == before


@pytest.mark.parametrize("changed", ["source", "prose"])
def test_input_race_during_ack_leaves_previous_authority_pending(adopted, monkeypatch, changed):
    from llm_wiki_cli.services import maintenance_service
    from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts, CommitStage
    status = _status()
    row = next(r for r in status["records"] if r["coordinate"]["qualified_owner"] == "Batch")
    manifest = (adopted / ".llm-wiki-manifest.json").read_bytes()
    def race(stage):
        if stage == CommitStage.KNOWLEDGE_INDEX_WRITTEN:
            if changed == "source":
                Path("src/policy.py").write_text(POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"))
            else:
                page = adopted / "entities/Batch.md"
                page.write_bytes(page.read_bytes() + b"\nExternal prose edit during publication.\n")
    def publish(plan):
        return commit_knowledge_artifacts(plan, fault_injector=race)
    monkeypatch.setattr(maintenance_service, "commit_knowledge_artifacts", publish)
    with pytest.raises(MaintenanceProtocolError, match="Source changed|Wiki changed"):
        _ack(status, row)
    assert (adopted / ".llm-wiki-manifest.json").read_bytes() == manifest
    state = SyncManifest.load(adopted).maintenance_state
    assert state is not None and state["records"][row["record_id"]]["status"] == "pending"


def test_newer_owner_rejects_old_cas_without_wiki_publication(adopted):
    status = _status()
    first, second = status["records"][:2]
    _ack(status, first)
    before = snapshot_wiki(adopted)
    with pytest.raises(MaintenanceProtocolError, match="authority changed"):
        _ack(status, second)
    assert snapshot_wiki(adopted) == before


def test_common_project_root_can_ack_wiki_inside_source_tree(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("policy.py").write_text(POLICY_SOURCE)
    with patch.object(sys, "argv", ["llm-wiki", "bootstrap", "--src-dir", ".", "--wiki-dir", "wiki"]):
        cli.main()
    adopt_maintenance_authority(".", "wiki", recovery_dir=tmp_path.parent / (tmp_path.name + "-recovery"))
    capsys.readouterr()
    status = get_maintenance_status_authority(".", "wiki")
    row = next(r for r in status["records"] if r["coordinate"]["qualified_owner"] == "Batch")
    result = acknowledge_maintenance_authority(".", "wiki", record_id=row["record_id"],
        expected_state_hash=status["state_hash"], expected_basis=row["expected_basis"],
        actor_kind="agent", actor_id="fixture-agent")
    assert result["changed"]


def test_successful_adoption_supplies_documented_committed_recovery(adopted):
    from llm_wiki_cli.services.maintenance_service import load_recovery_snapshot
    state = SyncManifest.load(adopted).maintenance_state
    assert state is not None
    load_recovery_snapshot("recovery/committed")
    (adopted / ".llm-wiki-manifest.json").unlink()
    restored = api.recover_maintenance("wiki", recovery_dir="recovery/committed",
                                     expected_adoption_id=state["adoption_id"])
    assert restored["restored"] and not restored["requires_sync"]
    assert SyncManifest.load(adopted).maintenance_state == state


def test_agent_ack_never_reactivates_expired_human_governance(adopted):
    from tests.test_knowledge_cmd import _run
    from llm_wiki_cli.services.knowledge_governance import load_governance, evaluate_review_event
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    from llm_wiki_cli.services.contracts import SECTION_OWNERSHIP_EXTENSION_KEY

    _run(["init", "--wiki-dir", "wiki", "--bundle-id", "kb_separate_authorities"])
    knowledge = load_knowledge_state(adopted).knowledge
    assert knowledge is not None
    page = next(p for p in knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]["pages"]
                if p["page_locator"] == "llm-wiki://entities/Batch")
    section = next(s for s in page["sections"] if s.get("semantic_hash") is not None)
    ledger = load_governance(adopted).ledger
    uid = next(key for key, value in ledger.concepts.items() if value.locator == page["page_locator"])
    _run(["review", "--wiki-dir", "wiki", "--uid", uid, "--section", section["locator"],
          "--reviewer-kind", "human", "--reviewer-id", "fixture-human", "--method", "manual-review",
          "--method-version", "1", "--authored-at", "2026-10-04T10:00:00Z"])
    Path("src/policy.py").write_text(POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    _sync()
    ledger = load_governance(adopted).ledger
    event = next(iter(ledger.review_events.values()))
    knowledge = load_knowledge_state(adopted).knowledge
    assert knowledge is not None and not evaluate_review_event(event, ledger, knowledge).valid
    before = (adopted / ".llm-wiki-governance.json").read_bytes()
    status = _status()
    row = next(r for r in status["records"] if r["coordinate"]["qualified_owner"] == "Batch")
    _ack(status, row)
    assert (adopted / ".llm-wiki-governance.json").read_bytes() == before
    knowledge = load_knowledge_state(adopted).knowledge
    assert knowledge is not None and not evaluate_review_event(event, ledger, knowledge).valid


@pytest.mark.parametrize("changed", ["source", "prose"])
def test_read_status_refuses_input_race_without_authority_write(adopted, monkeypatch, changed):
    from llm_wiki_cli.services import maintenance_service
    original = maintenance_service._capture
    manifest = (adopted / ".llm-wiki-manifest.json").read_bytes()
    def capture_then_edit(*args, **options):
        captured = original(*args, **options)
        path = Path("src/policy.py") if changed == "source" else adopted / "entities/Batch.md"
        path.write_bytes(path.read_bytes() + b"\nchanged after capture\n")
        return captured
    monkeypatch.setattr(maintenance_service, "_capture", capture_then_edit)
    with pytest.raises(MaintenanceProtocolError, match="changed"):
        _status()
    assert (adopted / ".llm-wiki-manifest.json").read_bytes() == manifest
