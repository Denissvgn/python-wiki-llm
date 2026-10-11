"""Source/prose review gaps survive owning sync without durable adoption."""

import json
from unittest.mock import patch

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import maintenance_queue, maintenance_service, mcp_server
from llm_wiki_cli.services.context_packet import ContextPacketSourceMutationError
from llm_wiki_cli.services.knowledge_storage import canonical_bytes
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from llm_wiki_cli.services.maintenance_evidence import MaintenanceCapture
from llm_wiki_cli.services.maintenance_protocol import ADOPTION_FILENAME
from llm_wiki_cli.services.maintenance_status import build_maintenance_status
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.developer_value.combined_workflows import (
    AFTER_PROSE,
    BEFORE_PROSE,
    client_after,
    prepare_combined,
    source_after,
)
from tests.developer_value.workflow_fixtures import sync_workflow, write_description
from tests.test_mcp import RecordingMcpServer


@pytest.mark.parametrize("storage", ["v1", "sharded-v2", "packed-v4-deflate"])
def test_post_sync_unadopted_claim_has_exact_informational_review_target(
    tmp_path, monkeypatch, capsys, storage
):
    monkeypatch.chdir(tmp_path)
    project = prepare_combined(tmp_path, "legacy")
    if storage != "v1":
        migrate_knowledge_storage(
            project.wiki, to=storage, recovery_dir=tmp_path / "storage-recovery"
        )
    (project.source / "policy.py").write_text(source_after())
    (project.source / "client.py").write_text(client_after())
    sync_workflow(project)
    # Literal source/prose contradiction is specified independently of queue labels.
    assert "records[max(0, len(records) - limit):]" in (
        project.source / "policy.py"
    ).read_text()
    assert BEFORE_PROSE in (project.wiki / "entities/Harbor.md").read_text()
    capsys.readouterr()
    captures = []
    original = maintenance_queue.capture_context_read

    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        captures.append(result)
        return result

    monkeypatch.setattr(maintenance_queue, "capture_context_read", capture)

    def read(operation):
        before = {
            path: (raw, (project.root / path).stat().st_mtime_ns)
            for path, raw in project.tree().items()
        }
        result = operation()
        assert before == {
            path: (raw, (project.root / path).stat().st_mtime_ns)
            for path, raw in project.tree().items()
        }
        assert not (tmp_path / "source-execution-tripwire").exists()
        assert not (project.wiki / ADOPTION_FILENAME).exists()
        assert SyncManifest.load(project.wiki).maintenance_state is None
        return result

    result = read(lambda: api.build_maintenance_queue(**project.options, limit=1000))
    assert len(captures) == 1
    assert result == read(
        lambda: api.build_maintenance_queue(**project.options, limit=1000)
    )
    item = next(row for row in result["items"] if row["path"] == "entities/Harbor.md")
    assert item["classification"] == "informational"
    assert item["observed_change_category"] == "ordinary-coverage-gap"
    assert "record_ids" not in item and "maintenance" not in item
    targets = [gap["target"] for gap in item["coverage_gaps"] if "target" in gap]
    assert {
        "canonical_path": "entities/Harbor.md",
        "section_locator": "llm-wiki://entities/Harbor#section/Harbor~1/Description~1",
        "ownership": "semantic",
    } in targets
    custody = result["qualification"]["ordinary_review_custody"]
    assert custody["availability"] == "unadopted"
    assert custody["durable_owner_available"] is False
    assert custody["live_evaluation_performed"] is True
    assert custody["source_prose_correctness"] == "not-established"
    assert result["omitted"] == 0 and result["returned"] == result["total"]
    narrow = read(lambda: api.build_maintenance_queue(**project.options, limit=1))
    assert narrow["items"] == result["items"][:1]
    assert narrow["total"] == result["total"]
    assert narrow["omitted"] == result["total"] - 1
    assert narrow["queue_id"] != result["queue_id"]

    def cli_read():
        with patch("sys.argv", [
            "llm-wiki", "queue", "--src-dir", str(project.source),
            "--wiki-dir", str(project.wiki), "--limit", "1000", "--format", "json",
        ]):
            cli.main()
        return json.loads(capsys.readouterr().out)

    assert read(cli_read) == result
    service = mcp_server.McpWikiService(**project.options)
    server = RecordingMcpServer()
    mcp_server._register_mcp_tools(server, service)
    assert read(lambda: server.tool_functions["get_maintenance_queue"](limit=1000)) == result

    # Correct prose also stays untracked; a read cannot invent review completion.
    write_description(project, AFTER_PROSE, "entities/Harbor.md")
    sync_workflow(project)
    corrected = read(lambda: api.build_maintenance_queue(**project.options, limit=1000))
    assert next(i for i in corrected["items"] if i["path"] == item["path"])[
        "classification"
    ] == "informational"


@pytest.mark.parametrize("scope", ["full-inventory", "selected-source"])
def test_unadopted_capture_exposes_missing_coverage_without_allocating_records(scope):
    target = {
        "canonical_path": "entities/Owned.md",
        "section_locator": "llm-wiki://entities/Owned#section/Owned~1/Description~1",
        "ownership": "semantic",
    }
    capture = MaintenanceCapture(
        {"owned": {"target": target, "target_presence": "present"}},
        issues=({"canonical_path": "entities/Unsupported.md", "reason": "unsupported-producer"},),
        source_backed_semantic_total=2,
        tracked_semantic_total=1,
    )
    report = build_maintenance_status(None, None, capture, analysis_scope=scope)
    payload = report.to_payload()
    assert payload["availability"] == "unadopted"
    assert payload["records"] == [] and payload["state_hash"] is None
    assert report.by_record == {} and report.by_path == {}
    assert payload["coverage"]["tracked_semantic_total"] == 0
    assert payload["coverage"]["untracked_semantic_total"] == 2
    assert payload["coverage"]["untracked_targets"] == [target]
    assert payload["coverage"]["untracked_target_bounds"] == {
        "total": 2, "returned": 1, "truncated": True,
    }
    assert payload["coverage"]["issues"] == list(capture.issues)
    assert not build_maintenance_status(None, None, capture).to_payload()[
        "coverage"
    ]["untracked_targets"]


def test_unadopted_target_details_are_bounded_without_losing_counts():
    capture = MaintenanceCapture(
        {
            str(i): {
                "target": {
                    "canonical_path": "entities/Owned.md",
                    "section_locator": "x" * 4000 + str(i),
                    "ownership": "semantic",
                },
                "target_presence": "present",
            }
            for i in range(150)
        },
        source_backed_semantic_total=150,
    )
    report = build_maintenance_status(None, None, capture, analysis_scope="full-inventory")
    result = maintenance_queue.compose_queue([], [], {}, {}, {}, maintenance_report=report)
    assert result["total"] == result["returned"] == 1
    item = result["items"][0]
    bounds = item["coverage_gap_bounds"]
    assert bounds["total"] == 150 and bounds["truncated"]
    assert bounds["omitted"] == 150 - len(item["coverage_gaps"])
    assert len(item["coverage_gaps"]) <= 128
    assert len(canonical_bytes(item["coverage_gaps"])) <= 65536
    assert len(canonical_bytes(report.to_payload())) <= 65536


@pytest.mark.parametrize("target", ["source", "wiki", "selection"])
def test_unadopted_queue_refuses_mutation_during_semantic_join(tmp_path, monkeypatch, target):
    monkeypatch.chdir(tmp_path)
    project = prepare_combined(tmp_path, "legacy")
    original = maintenance_service.capture_maintenance_observations
    path = {
        "source": project.source / "policy.py",
        "wiki": project.wiki / "entities/Harbor.md",
        "selection": project.source / ".llm-wiki/source-selection.json",
    }[target]

    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        path.write_bytes(path.read_bytes() + b"\n ")
        return result

    monkeypatch.setattr(maintenance_service, "capture_maintenance_observations", mutate)
    with pytest.raises(ContextPacketSourceMutationError):
        maintenance_queue.build_maintenance_queue(**project.options)
