"""Native projection ownership across the standalone documentation lifecycle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

import llm_wiki_cli.services.documentation_run as documentation_run_service
from llm_wiki_cli.services.contracts import (
    DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
)
from llm_wiki_cli.services.documentation_native import DocumentationNativeError
from llm_wiki_cli.services.documentation_run import (
    DocumentationIntegrityError,
    build_documentation_agent_packet,
    capture_generated_ownership,
    load_documentation_run,
    prepare_documentation_run,
    record_documentation_agent_result,
)
from llm_wiki_cli.services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME


NATIVE_ARTIFACTS = {
    MANIFEST_FILENAME,
    SURFACE_INDEX_FILENAME,
    KNOWLEDGE_INDEX_FILENAME,
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _agent_result(
    run_id: str,
    stage: str,
    *,
    status: str = "complete",
    changed: list[str] | None = None,
    completed: list[str] | None = None,
    claims: list[str] | None = None,
    imported_page_edits: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": stage,
        "status": status,
        "changed_wiki_paths": changed or [],
        "reused_work_ids": [],
        "completed_work_ids": completed or [],
        "deferred_work_ids": [],
        "claims_evidence_pages": claims or [],
        "unresolved_unknowns": [],
        "unsupported_source_notices": [],
        "requested_follow_up_checks": [],
        "reported_source_writes": [],
        "reported_input_wiki_writes": [],
        "reported_generated_block_edits": [],
        "imported_page_edits": imported_page_edits or [],
        "deferral_rationales": {},
        "findings": [],
    }


def _prepare_source_run(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text(
        '"""Small lifecycle fixture."""\n\n'
        "def run() -> str:\n"
        '    """Return one deterministic result."""\n'
        '    return "ok"\n',
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"
    run = prepare_documentation_run(
        workspace,
        baseline_strategy="bootstrap_source",
        source_root=source,
        site_name="Native Lifecycle Docs",
        project_purpose="Help operators run the lifecycle fixture.",
        audiences=["operator"],
        audience_intent={"operator": "run one supported operation"},
    )
    assert run.state == "baseline_ready"
    return source, workspace, run


def _complete_wiki_enrichment(workspace: Path, run):
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    worklist = _read_json(workspace / run.evidence["semantic_worklist"])
    work_ids = [str(item["id"]) for item in worklist["items"]]
    evidence_pages = sorted(
        {
            str(item["canonical_path"])
            for item in worklist["items"]
            if item.get("canonical_path")
        }
    )
    (workspace / "wiki" / "index.md").write_text(
        "# Native Lifecycle Docs\n\n"
        "The fixture exposes one supported operation. See the "
        "[application evidence](modules/app.md), "
        "[dependencies](dependencies.md), and "
        "[load order](load-order.md).\n",
        encoding="utf-8",
    )
    updated = record_documentation_agent_result(
        workspace,
        _agent_result(
            run.run_id,
            "wiki-enrichment",
            changed=["index.md"],
            completed=work_ids,
            claims=evidence_pages,
        ),
    )
    assert updated.state == "user_docs"
    result_payload = _read_json(
        workspace / updated.evidence["wiki-enrichment_result"]
    )
    refresh_payload = _read_json(workspace / updated.evidence["native_refresh"])
    return updated, result_payload, refresh_payload


def _prepare_legacy_wiki_only_run(tmp_path: Path):
    input_wiki = tmp_path / "input-wiki"
    input_wiki.mkdir()
    (input_wiki / "index.md").write_text(
        "# Imported Wiki\n\nPrior semantic context.\n",
        encoding="utf-8",
    )
    input_bytes = (input_wiki / "index.md").read_bytes()
    workspace = tmp_path / "wiki-only-workspace"
    run = prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        input_wiki_root=input_wiki,
        freshness_policy="allow-unverified",
        site_name="Imported Wiki Docs",
        project_purpose="Preserve the imported documentation snapshot.",
        audiences=["operator"],
        audience_intent={"operator": "review the imported operation"},
    )
    assert run.state == "baseline_ready"
    return input_wiki, input_bytes, workspace, run


def _imported_index_edit(workspace: Path, run) -> tuple[str, dict[str, Any]]:
    run = load_documentation_run(workspace)
    before = _read_json(workspace / run.evidence["wiki-enrichment_before"])
    worklist = _read_json(workspace / run.evidence["semantic_worklist"])
    item = next(
        item
        for item in worklist["items"]
        if item.get("canonical_path") == "index.md"
        and item.get("imported_classification") is not None
    )
    index = workspace / "wiki" / "index.md"
    return str(item["id"]), {
        "work_id": str(item["id"]),
        "canonical_path": "index.md",
        "before_hash": before["tree"]["file_hashes"]["index.md"],
        "after_hash": _sha256(index.read_bytes()),
        "evidence": ["index.md"],
        "rationale": "Preserved the imported context while clarifying its limitation.",
    }


def _ownership_payload(workspace: Path, run) -> dict[str, Any]:
    return _read_json(workspace / run.evidence["generated_ownership"])


def test_source_backed_prepare_owns_a_valid_native_trio(tmp_path: Path) -> None:
    _source, workspace, run = _prepare_source_run(tmp_path)
    wiki = workspace / "wiki"

    assert {name for name in NATIVE_ARTIFACTS if (wiki / name).is_file()} == (
        NATIVE_ARTIFACTS
    )
    loaded = load_knowledge_state(wiki)
    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.knowledge is not None
    assert loaded.manifest_basis is not None
    assert _read_json(wiki / MANIFEST_FILENAME)["version"] == 5

    ownership = _ownership_payload(workspace, run)
    assert NATIVE_ARTIFACTS <= set(ownership["fingerprints"])
    assert ownership["fingerprints"] == capture_generated_ownership(wiki)
    refresh = _read_json(workspace / run.evidence["native_refresh"])
    assert refresh["phase"] == "baseline"
    assert refresh["status"] == "complete"
    assert set(refresh["artifacts"]) == {"surface", "knowledge", "manifest"}
    assert refresh["ownership_after"] == ownership["fingerprints"]


def test_wiki_enrichment_refreshes_and_reanchors_native_ownership(
    tmp_path: Path,
) -> None:
    _source, workspace, run = _prepare_source_run(tmp_path)
    baseline_refresh = _read_json(workspace / run.evidence["native_refresh"])
    baseline_ownership = _ownership_payload(workspace, run)["fingerprints"]

    updated, result, refresh = _complete_wiki_enrichment(workspace, run)

    assert result["changed_wiki_paths"] == ["index.md"]
    assert NATIVE_ARTIFACTS.isdisjoint(result["changed_wiki_paths"])
    assert result["reconciliation"]["actual_changed_wiki_paths"] == ["index.md"]
    assert result["reconciliation"]["native_projection_refresh"] == {
        "status": "complete",
        "phase": "wiki-enrichment-01",
        "evidence": (
            ".llm-wiki-docs/evidence/native-refresh-wiki-enrichment-01.json"
        ),
    }
    assert refresh["phase"] == "wiki-enrichment-01"
    assert refresh["changed_wiki_paths"] == ["index.md"]
    assert refresh["ownership_before"] == baseline_ownership
    assert refresh["ownership_before"] == baseline_refresh["ownership_after"]

    ownership_path = workspace / updated.evidence["generated_ownership"]
    ownership_after = _read_json(ownership_path)["fingerprints"]
    assert refresh["ownership_after"] == ownership_after
    assert ownership_after == capture_generated_ownership(workspace / "wiki")
    assert updated.integrity_anchors["generated_ownership"] == _sha256(
        ownership_path.read_bytes()
    )
    assert load_knowledge_state(workspace / "wiki").status is KnowledgeLoadState.VALID


def test_user_docs_change_gets_a_second_refresh_and_validation_phase(
    tmp_path: Path,
) -> None:
    _source, workspace, run = _prepare_source_run(tmp_path)
    run, _enrichment_result, first_refresh = _complete_wiki_enrichment(
        workspace, run
    )
    build_documentation_agent_packet(workspace, stage="user-docs")
    guide = workspace / "wiki" / "guides" / "run-fixture.md"
    guide.parent.mkdir(parents=True, exist_ok=True)
    guide.write_text(
        "# Run the fixture\n\n"
        "Follow the supported operation in the "
        "[application evidence](../modules/app.md).\n",
        encoding="utf-8",
    )
    index = workspace / "wiki" / "index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\nContinue with the [run fixture guide](guides/run-fixture.md).\n",
        encoding="utf-8",
    )

    updated = record_documentation_agent_result(
        workspace,
        _agent_result(
            run.run_id,
            "user-docs",
            changed=["guides/run-fixture.md", "index.md"],
            claims=["modules/app.md"],
        ),
    )

    assert updated.state == "review"
    result = _read_json(workspace / updated.evidence["user-docs_result"])
    second_refresh = _read_json(workspace / updated.evidence["native_refresh"])
    assert result["changed_wiki_paths"] == ["guides/run-fixture.md", "index.md"]
    assert NATIVE_ARTIFACTS.isdisjoint(result["changed_wiki_paths"])
    assert result["reconciliation"]["native_projection_refresh"]["phase"] == (
        "user-docs-01"
    )
    assert second_refresh["phase"] == "user-docs-01"
    assert second_refresh["changed_wiki_paths"] == [
        "guides/run-fixture.md",
        "index.md",
    ]
    assert second_refresh["ownership_before"] == first_refresh["ownership_after"]
    assert second_refresh["ownership_after"] == _ownership_payload(
        workspace, updated
    )["fingerprints"]

    validation = {
        item["check"]: item
        for item in updated.validation_results
        if item.get("phase") == "user-docs-01"
    }
    assert set(validation) == {"lint", "ci-check"}
    assert all(item["ok"] is True for item in validation.values())
    for item in validation.values():
        assert _read_json(workspace / item["evidence"])["phase"] == "user-docs-01"
    assert load_knowledge_state(workspace / "wiki").status is KnowledgeLoadState.VALID


def test_wiki_only_markdown_change_remains_snapshot_only(
    tmp_path: Path,
) -> None:
    input_wiki, input_bytes, workspace, run = _prepare_legacy_wiki_only_run(tmp_path)
    assert run.evidence["native_refresh"] == ""
    assert "native_knowledge_snapshot_only" in run.verdict_limitations
    assert not (workspace / "wiki" / KNOWLEDGE_INDEX_FILENAME).exists()

    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    (workspace / "wiki" / "index.md").write_text(
        "# Imported Wiki\n\n"
        "The imported claim remains useful snapshot evidence but is not "
        "source-verified.\n",
        encoding="utf-8",
    )
    work_id, imported_edit = _imported_index_edit(workspace, run)
    updated = record_documentation_agent_result(
        workspace,
        _agent_result(
            run.run_id,
            "wiki-enrichment",
            status="partial",
            changed=["index.md"],
            completed=[work_id],
            claims=["index.md"],
            imported_page_edits=[imported_edit],
        ),
    )

    assert updated.state == "wiki_enrichment"
    assert "native_knowledge_snapshot_only" in updated.verdict_limitations
    assert updated.evidence["native_refresh"] == ""
    result = _read_json(workspace / updated.evidence["wiki-enrichment_result"])
    assert result["reconciliation"]["native_projection_refresh"] is None
    assert not (workspace / "wiki" / KNOWLEDGE_INDEX_FILENAME).exists()
    assert KNOWLEDGE_INDEX_FILENAME not in capture_generated_ownership(
        workspace / "wiki"
    )
    assert (input_wiki / "index.md").read_bytes() == input_bytes


@pytest.mark.parametrize("mutation", ["add", "change", "remove"])
def test_knowledge_sidecar_tampering_is_rejected_before_result_acceptance(
    tmp_path: Path,
    mutation: str,
) -> None:
    if mutation == "add":
        _input, _input_bytes, workspace, run = _prepare_legacy_wiki_only_run(
            tmp_path
        )
    else:
        _source, workspace, run = _prepare_source_run(tmp_path)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    knowledge = workspace / "wiki" / KNOWLEDGE_INDEX_FILENAME
    if mutation == "add":
        knowledge.write_text("{}\n", encoding="utf-8")
    elif mutation == "change":
        knowledge.write_text("{}\n", encoding="utf-8")
    else:
        knowledge.unlink()

    with pytest.raises(
        DocumentationIntegrityError,
        match="generated ownership changed",
    ):
        record_documentation_agent_result(
            workspace,
            _agent_result(
                run.run_id,
                "wiki-enrichment",
                changed=[KNOWLEDGE_INDEX_FILENAME],
            ),
        )

    blocked = load_documentation_run(workspace)
    assert blocked.state == "blocked"
    assert not (
        workspace
        / ".llm-wiki-docs"
        / "results"
        / "wiki-enrichment-01.json"
    ).exists()


def test_native_refresh_failure_blocks_result_before_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _source, workspace, run = _prepare_source_run(tmp_path)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    worklist = _read_json(workspace / run.evidence["semantic_worklist"])
    work_ids = [str(item["id"]) for item in worklist["items"]]
    evidence_pages = [
        str(item["canonical_path"])
        for item in worklist["items"]
        if item.get("canonical_path")
    ]
    index = workspace / "wiki" / "index.md"
    index.write_text(
        "# Native Lifecycle Docs\n\n"
        "The semantic change requires a controller refresh. See "
        "[application evidence](modules/app.md).\n",
        encoding="utf-8",
    )

    def fail_refresh(**_kwargs):
        raise DocumentationNativeError("injected refresh failure")

    monkeypatch.setattr(
        documentation_run_service,
        "refresh_documentation_native_projection",
        fail_refresh,
    )

    with pytest.raises(
        DocumentationIntegrityError,
        match="Controller native projection refresh failed",
    ):
        record_documentation_agent_result(
            workspace,
            _agent_result(
                run.run_id,
                "wiki-enrichment",
                changed=["index.md"],
                completed=work_ids,
                claims=evidence_pages,
            ),
        )

    blocked = load_documentation_run(workspace)
    assert blocked.state == "blocked"
    assert _read_json(workspace / blocked.evidence["native_refresh"])["phase"] == (
        "baseline"
    )
    assert not (
        workspace
        / ".llm-wiki-docs"
        / "results"
        / "wiki-enrichment-01.json"
    ).exists()


def test_inconsistent_native_reanchor_blocks_result_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _source, workspace, run = _prepare_source_run(tmp_path)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    worklist = _read_json(workspace / run.evidence["semantic_worklist"])
    work_ids = [str(item["id"]) for item in worklist["items"]]
    evidence_pages = [
        str(item["canonical_path"])
        for item in worklist["items"]
        if item.get("canonical_path")
    ]
    (workspace / "wiki" / "index.md").write_text(
        "# Native Lifecycle Docs\n\n"
        "The semantic change requires a consistent ownership re-anchor. See "
        "[application evidence](modules/app.md).\n",
        encoding="utf-8",
    )
    real_refresh = (
        documentation_run_service.refresh_documentation_native_projection
    )

    def inject_non_native_owner(**kwargs):
        refreshed = real_refresh(**kwargs)
        module = Path(kwargs["wiki_root"]) / "modules" / "app.md"
        module.write_text(
            module.read_text(encoding="utf-8")
            + "\n## Injected generated section\n\n"
            + "<!-- Auto-generated test section. Do not edit by hand. -->\n",
            encoding="utf-8",
        )
        return refreshed

    monkeypatch.setattr(
        documentation_run_service,
        "refresh_documentation_native_projection",
        inject_non_native_owner,
    )

    with pytest.raises(
        DocumentationIntegrityError,
        match="non-native generated ownership",
    ):
        record_documentation_agent_result(
            workspace,
            _agent_result(
                run.run_id,
                "wiki-enrichment",
                changed=["index.md"],
                completed=work_ids,
                claims=evidence_pages,
            ),
        )

    blocked = load_documentation_run(workspace)
    assert blocked.state == "blocked"
    assert not (
        workspace
        / ".llm-wiki-docs"
        / "results"
        / "wiki-enrichment-01.json"
    ).exists()
