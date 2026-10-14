"""Maintenance read surfaces share one capture and never mutate the wiki."""

from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import context_service, lint_service
from llm_wiki_cli.services.context_packet import capture_context_read
from llm_wiki_cli.services.maintenance_queue import build_maintenance_queue
from llm_wiki_cli.services.maintenance_service import adopt_maintenance_authority
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from tests.developer_value.fixtures import POLICY_SOURCE


def files():
    return {
        p.relative_to("wiki").as_posix(): p.read_bytes()
        for p in Path("wiki").rglob("*")
        if p.is_file()
    }


@pytest.fixture
def owned(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(POLICY_SOURCE)
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    adopt_maintenance_authority("src", "wiki", recovery_dir="recovery")
    capsys.readouterr()
    return tmp_path


def test_queue_and_inspection_share_confirmed_executable_drift_without_writes(owned):
    before = files()
    Path("src/policy.py").write_text(
        POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]")
    )
    queue = build_maintenance_queue("src", "wiki")
    item = next(row for row in queue["items"] if row["path"] == "entities/Batch.md")
    reason = next(
        r
        for r in item["reasons"]
        if r["code"] == "maintenance:executable-syntax-changed"
    )
    assert reason["weight"] == 90
    assert item["maintenance"]["pending"] >= 1
    native = api.inspect_concept(
        "llm-wiki://entities/Batch", src_dir="src", wiki_dir="wiki", live=True
    )
    component = native["concept"]
    assert component is not None
    concept = component["concept"]
    assert concept is not None
    summary = concept["maintenance"]["summary"]
    assert summary == item["maintenance"]
    assert files() == before


def test_queue_reuses_inventory_in_lint_and_captures_source_once(owned, monkeypatch):
    original = context_service.get_inventory_result
    calls = []

    def collect(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)

    def no_second(*args, **kwargs):
        pytest.fail("lint must reuse the captured inventory rather than extract again")

    monkeypatch.setattr(context_service, "get_inventory_result", collect)
    monkeypatch.setattr(lint_service, "get_inventory_result", no_second)
    build_maintenance_queue("src", "wiki")
    assert len(calls) == 1
    assert calls[0]["capture_implementation_observations"] is True


def test_capture_option_disabled_attaches_no_maintenance_read_overlay(owned):
    captured = capture_context_read(
        "src", "wiki", capture_implementation_observations=False
    )
    assert captured.capture_implementation_requested is False
    assert captured.knowledge_view.maintenance_report is None


def test_snapshot_inspection_never_claims_current_acknowledgment(owned):
    result = api.inspect_concept(
        "llm-wiki://entities/Batch", src_dir="src", wiki_dir="wiki", live=False
    )
    component = result["concept"]
    assert component is not None
    concept = component["concept"]
    assert concept is not None
    maintenance = concept["maintenance"]
    assert (
        maintenance["analysis_scope"] == "snapshot"
        and not maintenance["live_evaluation_performed"]
    )
    assert all(
        row["effective_status"] is None and row["expected_basis"] is None
        for row in maintenance["records"]
    )


@pytest.mark.parametrize("live", [False, True])
def test_uid_and_alias_inspection_preserve_resolved_maintenance_status(owned, live):
    from tests.test_knowledge_cmd import _run
    from llm_wiki_cli.services.knowledge_governance import load_governance

    route = "llm-wiki://entities/Batch"
    alias = "llm-wiki://entities/FormerBatch"
    _run(["init", "--wiki-dir", "wiki", "--bundle-id", "kb_inspection_identity"])
    ledger = load_governance(Path("wiki")).ledger
    uid = next(key for key, value in ledger.concepts.items() if value.locator == route)
    _run(["alias", "--wiki-dir", "wiki", "--uid", uid,
          "--type", "locator", "--value", alias])
    Path("src/policy.py").write_text(
        POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]")
    )
    before = files()
    expected = api.inspect_concept(route, src_dir="src", wiki_dir="wiki", live=live)
    assert "maintenance" in expected and "maintenance" in expected["concept"]
    for coordinate in (uid, alias):
        result = api.inspect_concept(coordinate, src_dir="src", wiki_dir="wiki", live=live)
        selected = result["concept"]["concept"]
        assert selected is not None and selected["locator"] == route
        assert "maintenance" in result and "maintenance" in result["concept"]
        assert result["maintenance"] == expected["maintenance"]
        assert result["concept"]["maintenance"] == expected["concept"]["maintenance"]
        assert result["maintenance"] == selected["maintenance"]
    assert files() == before


def test_selected_v8_task_discloses_partial_ledger_and_no_ack_inference(owned):
    migrate_knowledge_storage(
        Path("wiki"), to="sharded-v2", recovery_dir=Path("storage-recovery")
    )
    migrate_knowledge_storage(
        Path("wiki"), to="indexed-v8", recovery_dir=Path("manifest-recovery")
    )
    request = {
        "schema_version": "llm-wiki-task-request/v2",
        "requirements": [
            {"id": "class", "facet": "concept", "selector": "llm-wiki://entities/Batch"}
        ],
    }
    result = api.build_task_context(
        request, src_dir="src", wiki_dir="wiki"
    ).to_payload()
    summary = result["facts"][0]["observation"]["concept"]["maintenance"]
    assert (
        summary["availability"] == "partial"
        and summary["analysis_scope"] == "selected-header"
    )
    assert summary["pending"] == summary["acknowledged"] == 0
    assert not summary["live_evaluation_performed"]


def _context(captured):
    from llm_wiki_cli.services.context_packet import (
        build_context_from_captured_read,
        _normalized_request,
        packet_from_captured_response,
    )

    request = _normalized_request(
        {
            "budget_tokens": 32000,
            "focus": ["all"],
            "format": "json",
            "filters": {},
            "knowledge_mode": "auto",
        }
    )
    payload, warnings = build_context_from_captured_read(captured, request)
    response = context_service._protocol_success_payload(request, payload, warnings)
    response["source_priorities"] = payload.get("source_priorities", {})
    packet = packet_from_captured_response(captured, request, response)
    return response, packet


def test_actual_prose_drift_status_queue_context_and_inspection_are_consistent(owned):
    from llm_wiki_cli.services.maintenance_service import (
        get_maintenance_status_authority,
    )
    from llm_wiki_cli.services.maintenance_status import compact_maintenance_summary

    path = Path("wiki/entities/Batch.md")
    path.write_text(
        path.read_text().replace(
            "## Description\n", "## Description\n\nAuthored correction.\n"
        )
    )
    before = files()
    status = get_maintenance_status_authority("src", "wiki")
    assert status["requires_sync"]
    captured = capture_context_read("src", "wiki")
    report = captured.knowledge_view.maintenance_report
    assert report is not None and not captured.knowledge_view.ready
    assert compact_maintenance_summary(status) == compact_maintenance_summary(report)
    response, _ = _context(captured)
    assert response["knowledge"]["maintenance"] == compact_maintenance_summary(report)
    queue = build_maintenance_queue("src", "wiki")
    item = next(row for row in queue["items"] if row["path"] == "entities/Batch.md")
    native = api.inspect_concept(
        "llm-wiki://entities/Batch", src_dir="src", wiki_dir="wiki", live=True
    )
    assert "maintenance" in native
    assert native["maintenance"]["summary"] == item["maintenance"]
    assert item["maintenance"]["pending"] >= 1 and item["maintenance"]["requires_sync"]
    assert files() == before


def test_ambiguous_candidate_targets_remain_pending_across_all_read_surfaces(
    owned, monkeypatch
):
    from llm_wiki_cli import cli
    from llm_wiki_cli.services.maintenance_status import compact_maintenance_summary
    from llm_wiki_cli.services.maintenance_service import (
        get_maintenance_status_authority,
    )
    import sys

    Path("src/policy.py").unlink()
    Path("src/one.py").write_text(POLICY_SOURCE)
    Path("src/two.py").write_text(POLICY_SOURCE)
    monkeypatch.setattr(
        sys,
        "argv",
        ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"],
    )
    cli.main()
    before = files()
    status = get_maintenance_status_authority("src", "wiki")
    assert compact_maintenance_summary(status)["ambiguous"] >= 1
    captured = capture_context_read("src", "wiki")
    response, _ = _context(captured)
    assert response["knowledge"]["maintenance"]["ambiguous"] >= 1
    queue = build_maintenance_queue("src", "wiki")
    ambiguous = next(
        row for row in status["records"] if row["mapping"]["state"] == "ambiguous"
    )
    targets = [
        ambiguous["target"],
        *(c["target"] for c in ambiguous["mapping"]["candidates"]),
    ]
    for target in targets:
        path = target["canonical_path"]
        item = next(row for row in queue["items"] if row["path"] == path)
        assert item["maintenance"]["ambiguous"] >= 1
        assert any(t["target"] == target for t in item["semantic_targets"])
        native = api.inspect_concept(
            "llm-wiki://" + path[:-3], src_dir="src", wiki_dir="wiki", live=True
        )
        assert "maintenance" in native
        assert native["maintenance"]["summary"] == item["maintenance"]
    assert files() == before


def test_source_deletion_retains_exact_old_targets_in_all_read_views(
    owned, monkeypatch
):
    from llm_wiki_cli import cli
    from llm_wiki_cli.services.maintenance_status import compact_maintenance_summary
    from llm_wiki_cli.services.maintenance_service import (
        get_maintenance_status_authority,
    )
    import sys

    Path("src/policy.py").unlink()
    monkeypatch.setattr(
        sys,
        "argv",
        ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"],
    )
    cli.main()
    before = files()
    status = get_maintenance_status_authority("src", "wiki")
    assert compact_maintenance_summary(status)["deleted"] >= 1
    captured = capture_context_read("src", "wiki")
    response, _ = _context(captured)
    assert response["knowledge"]["maintenance"]["deleted"] >= 1
    queue = build_maintenance_queue("src", "wiki")
    item = next(row for row in queue["items"] if row["path"] == "entities/Batch.md")
    assert item["maintenance"]["deleted"] >= 1
    native = api.inspect_concept(
        "llm-wiki://entities/Batch", src_dir="src", wiki_dir="wiki", live=True
    )
    assert "maintenance" in native
    assert native["maintenance"]["summary"] == item["maintenance"]
    assert files() == before


@pytest.mark.parametrize("change", ["snapshot-ack", "header-ack", "impossible-count"])
def test_rehashed_context_packet_refuses_false_maintenance_qualification(owned, change):
    from copy import deepcopy
    from llm_wiki_cli.services.context_packet import (
        ContextPacketMalformedError,
        validate_context_packet,
    )
    from tests.test_context_packet_knowledge import _canonical_repack

    captured = capture_context_read("src", "wiki")
    _, packet = _context(captured)
    payload = deepcopy(packet.to_payload())
    summary = payload["response"]["knowledge"]["maintenance"]
    if change == "impossible-count":
        summary["pending"] = summary["total"] + 1
    else:
        summary.update(
            analysis_scope="snapshot"
            if change == "snapshot-ack"
            else "selected-header",
            live_evaluation_performed=True,
            acknowledged=1,
        )
    with pytest.raises(ContextPacketMalformedError, match="maintenance"):
        validate_context_packet(_canonical_repack(payload))
