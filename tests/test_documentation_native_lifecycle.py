"""Native projection ownership across the standalone documentation lifecycle."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.commands import knowledge_cmd
import llm_wiki_cli.services.documentation_run as documentation_run_service
from llm_wiki_cli.services.contracts import (
    DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
)
from llm_wiki_cli.services.documentation_native import DocumentationNativeError
from llm_wiki_cli.services.documentation_claim_evidence import (
    qualify_claim_evidence,
)
from llm_wiki_cli.services.documentation_queries import DocumentationGraphQueryService
from llm_wiki_cli.services.documentation_run import (
    DocumentationIntegrityError,
    DocumentationSchemaError,
    build_documentation_agent_packet,
    capture_generated_ownership,
    export_documentation_run,
    load_documentation_run,
    prepare_documentation_run,
    record_documentation_agent_result,
)
from llm_wiki_cli.services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_consumption import load_knowledge_read_view
from llm_wiki_cli.services.knowledge_governance import GOVERNANCE_FILENAME
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME
from llm_wiki_cli.services.verification_contracts import (
    ARTIFACT_INTEGRITY_CHECKER_ID,
    VERIFICATION_RECEIPT_FILENAME,
    VerificationDiagnostic,
    build_artifact_verification_context,
    verify_and_write_receipt,
    write_verification_receipt,
)


NATIVE_ARTIFACTS = {
    MANIFEST_FILENAME,
    SURFACE_INDEX_FILENAME,
    KNOWLEDGE_INDEX_FILENAME,
}
PROTECTED_NATIVE_ARTIFACTS = NATIVE_ARTIFACTS | {
    GOVERNANCE_FILENAME,
    VERIFICATION_RECEIPT_FILENAME,
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
    claim_evidence: list[dict[str, Any]] | None = None,
    runtime_captures: list[dict[str, Any]] | None = None,
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
        "claim_evidence": claim_evidence or [],
        "runtime_captures": runtime_captures or [],
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


def _run_knowledge_command(argv: list[str]) -> None:
    args = cli._build_parser().parse_args(["knowledge", *argv])
    knowledge_cmd.run(args)


def _prepare_governed_source_run(
    tmp_path: Path,
    *,
    failed_receipt: bool = False,
    checker_version: str | None = None,
    knowledge_mode: str = "off",
    include_receipt: bool = True,
):
    source, seed_workspace, _seed_run = _prepare_source_run(tmp_path)
    seed_wiki = seed_workspace / "wiki"
    _run_knowledge_command(
        [
            "init",
            "--wiki-dir",
            str(seed_wiki),
            "--bundle-id",
            "docs_native_lifecycle",
        ]
    )
    view = load_knowledge_read_view(seed_wiki, snapshot_only=True)
    assert view.knowledge is not None
    assert view.manifest_basis is not None
    assert view.manifest_basis.artifact_hashes is not None
    hashes = view.manifest_basis.artifact_hashes
    receipt_bytes = b""
    if include_receipt:
        diagnostics = (
            (
                VerificationDiagnostic(
                    code="artifact-integrity-failed",
                    subject="artifact_hashes.knowledge_index_hash",
                ),
            )
            if failed_receipt
            else ()
        )
        context = build_artifact_verification_context(
            view.knowledge,
            knowledge_hash=hashes.knowledge_index_hash,
            surface_index_hash=hashes.surface_index_hash,
            evaluated_envelope_hash=hashes.evaluated_envelope_hash,
            governance_hash=hashes.governance_hash,
            artifact_integrity=not failed_receipt,
            artifact_diagnostics=diagnostics,
        )
        receipt = verify_and_write_receipt(
            seed_wiki,
            context,
            [ARTIFACT_INTEGRITY_CHECKER_ID],
        )
        if checker_version is not None:
            receipt = replace(
                receipt,
                checks=(
                    replace(
                        receipt.checks[0],
                        checker_version=checker_version,
                    ),
                ),
            )
            write_verification_receipt(seed_wiki, receipt)
        receipt_bytes = (seed_wiki / VERIFICATION_RECEIPT_FILENAME).read_bytes()
    workspace = tmp_path / "governed-workspace"
    run = prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        source_root=source,
        input_wiki_root=seed_wiki,
        freshness_policy="require-current",
        site_name="Governed Native Lifecycle Docs",
        project_purpose="Exercise governed documentation refresh.",
        audiences=["operator"],
        audience_intent={"operator": "run one governed operation"},
        knowledge_mode=knowledge_mode,
    )
    for required_dir in ("entities", "infrastructure", "workflows"):
        (workspace / "wiki" / required_dir).mkdir(exist_ok=True)
    return source, workspace, run, receipt_bytes


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
    imported_edits = []
    if any(
        item.get("canonical_path") == "index.md"
        and item.get("imported_classification") is not None
        for item in worklist["items"]
    ):
        _imported_work_id, imported_edit = _imported_index_edit(workspace, run)
        imported_edits.append(imported_edit)
    updated = record_documentation_agent_result(
        workspace,
        _agent_result(
            run.run_id,
            "wiki-enrichment",
            changed=["index.md"],
            completed=work_ids,
            claims=evidence_pages,
            imported_page_edits=imported_edits,
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


def _imported_index_edit(
    workspace: Path,
    run,
    *,
    stage: str = "wiki-enrichment",
) -> tuple[str, dict[str, Any]]:
    run = load_documentation_run(workspace)
    before = _read_json(workspace / run.evidence[f"{stage}_before"])
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
    assert refresh["schema_version"] == (
        "llm-wiki-documentation-native-refresh/v2"
    )
    assert refresh["phase"] == "baseline"
    assert refresh["status"] == "complete"
    assert set(refresh["artifacts"]) == {"surface", "knowledge", "manifest"}
    assert refresh["ownership_after"] == ownership["fingerprints"]
    assert set(refresh["artifact_ownership"]) == PROTECTED_NATIVE_ARTIFACTS
    assert refresh["governance_reconciliation"]["status"] == "not-adopted"
    assert refresh["verification_receipt"]["status"] == "absent"
    assert refresh["verification_receipt"]["policy"] == "retain-and-limit"
    assert refresh["verification_receipt"]["checker_execution"] == (
        "not-authorized"
    )
    assert refresh["review_authority"] == {
        "external_agent_result": "not-native-human-review",
        "human_review_mutation": "not-authorized",
    }


def test_governed_prepare_records_unchanged_ledger_and_current_receipt(
    tmp_path: Path,
    capsys,
) -> None:
    _source, workspace, run, receipt_bytes = _prepare_governed_source_run(
        tmp_path
    )
    capsys.readouterr()
    wiki = workspace / "wiki"
    refresh = _read_json(workspace / run.evidence["native_refresh"])

    assert (wiki / VERIFICATION_RECEIPT_FILENAME).read_bytes() == receipt_bytes
    assert {
        GOVERNANCE_FILENAME,
        VERIFICATION_RECEIPT_FILENAME,
    } <= set(capture_generated_ownership(wiki))
    assert refresh["governance_reconciliation"]["status"] == "unchanged"
    assert refresh["verification_receipt"]["status"] == "unchanged"
    assert refresh["verification_receipt"]["evaluation"]["status"] == (
        "current-passed"
    )
    assert refresh["verification_receipt"]["evaluation"]["valid"] is True
    assert refresh["verification_receipt"]["evaluation"]["passed"] is True


def test_refresh_retains_and_limits_a_receipt_made_stale(
    tmp_path: Path,
    capsys,
) -> None:
    _source, workspace, run, receipt_bytes = _prepare_governed_source_run(
        tmp_path
    )
    capsys.readouterr()
    wiki = workspace / "wiki"
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    index = wiki / "index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\nA governed semantic clarification changes the native snapshot.\n",
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

    refresh = _read_json(workspace / updated.evidence["native_refresh"])
    verification = refresh["verification_receipt"]
    assert (wiki / VERIFICATION_RECEIPT_FILENAME).read_bytes() == receipt_bytes
    assert verification["status"] == "unchanged"
    assert verification["evaluation"]["status"] == "retained-stale"
    assert verification["evaluation"]["valid"] is False
    assert verification["evaluation"]["invalidation_reasons"]
    assert "native_verification_receipt_stale" in updated.verdict_limitations
    assert refresh["governance_reconciliation"]["status"] == "unchanged"


def test_supervisor_refresh_exposes_governance_reconciliation_change(
    tmp_path: Path,
    capsys,
) -> None:
    _source, workspace, run, receipt_bytes = _prepare_governed_source_run(
        tmp_path
    )
    capsys.readouterr()
    wiki = workspace / "wiki"
    governance_before = (wiki / GOVERNANCE_FILENAME).read_bytes()
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
    run = record_documentation_agent_result(
        workspace,
        _agent_result(
            run.run_id,
            "wiki-enrichment",
            completed=work_ids,
            claims=evidence_pages,
        ),
    )
    assert run.state == "user_docs"
    build_documentation_agent_packet(workspace, stage="user-docs")
    guide = wiki / "guides" / "governed-operation.md"
    guide.parent.mkdir(parents=True, exist_ok=True)
    guide.write_text(
        "# Governed operation\n\n"
        "Use the current [application module](../modules/app.md).\n",
        encoding="utf-8",
    )

    updated = record_documentation_agent_result(
        workspace,
        _agent_result(
            run.run_id,
            "user-docs",
            status="partial",
            changed=["guides/governed-operation.md"],
        ),
    )

    refresh = _read_json(workspace / updated.evidence["native_refresh"])
    governance = refresh["governance_reconciliation"]
    assert governance["status"] == "reconciled-changed"
    assert governance["before_sha256"] != governance["after_sha256"]
    assert (wiki / GOVERNANCE_FILENAME).read_bytes() != governance_before
    assert (wiki / VERIFICATION_RECEIPT_FILENAME).read_bytes() == receipt_bytes
    assert refresh["verification_receipt"]["evaluation"]["status"] == (
        "retained-stale"
    )


def test_valid_failed_receipt_remains_visible_and_limits_the_run(
    tmp_path: Path,
    capsys,
) -> None:
    _source, workspace, run, receipt_bytes = _prepare_governed_source_run(
        tmp_path,
        failed_receipt=True,
    )
    capsys.readouterr()
    wiki = workspace / "wiki"
    refresh = _read_json(workspace / run.evidence["native_refresh"])
    evaluation = refresh["verification_receipt"]["evaluation"]

    assert (wiki / VERIFICATION_RECEIPT_FILENAME).read_bytes() == receipt_bytes
    assert evaluation["status"] == "current-failed"
    assert evaluation["valid"] is True
    assert evaluation["recorded_result"] == "failed"
    assert evaluation["passed"] is False
    assert "native_verification_receipt_failed" in run.verdict_limitations


def test_unknown_checker_version_is_retained_as_stale_evidence(
    tmp_path: Path,
    capsys,
) -> None:
    _source, workspace, run, receipt_bytes = _prepare_governed_source_run(
        tmp_path,
        checker_version="2",
    )
    capsys.readouterr()
    wiki = workspace / "wiki"
    evaluation = _read_json(workspace / run.evidence["native_refresh"])[
        "verification_receipt"
    ]["evaluation"]

    assert (wiki / VERIFICATION_RECEIPT_FILENAME).read_bytes() == receipt_bytes
    assert evaluation["status"] == "retained-stale"
    assert evaluation["valid"] is False
    assert evaluation["invalidation_reasons"] == ["checker-version-changed"]
    assert "native_verification_receipt_stale" in run.verdict_limitations


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


@pytest.mark.parametrize(
    "artifact",
    [GOVERNANCE_FILENAME, VERIFICATION_RECEIPT_FILENAME],
)
def test_worker_cannot_add_governance_or_verification_artifact(
    tmp_path: Path,
    artifact: str,
) -> None:
    _source, workspace, run = _prepare_source_run(tmp_path)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    (workspace / "wiki" / artifact).write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        DocumentationIntegrityError,
        match="generated ownership changed",
    ):
        record_documentation_agent_result(
            workspace,
            _agent_result(
                run.run_id,
                "wiki-enrichment",
                changed=[artifact],
            ),
        )

    assert load_documentation_run(workspace).state == "blocked"


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


def test_interrupted_post_commit_refresh_restores_all_protected_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    _source, workspace, run, receipt_bytes = _prepare_governed_source_run(
        tmp_path
    )
    capsys.readouterr()
    wiki = workspace / "wiki"
    protected_before = {
        name: (wiki / name).read_bytes()
        for name in PROTECTED_NATIVE_ARTIFACTS
    }
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    index = wiki / "index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\nThis change reaches the interrupted refresh boundary.\n",
        encoding="utf-8",
    )
    work_id, imported_edit = _imported_index_edit(workspace, run)
    real_refresh = (
        documentation_run_service.refresh_documentation_native_projection
    )

    def interrupt_after_commit(**kwargs):
        real_refresh(**kwargs)
        raise DocumentationNativeError("injected interruption after commit")

    monkeypatch.setattr(
        documentation_run_service,
        "refresh_documentation_native_projection",
        interrupt_after_commit,
    )

    with pytest.raises(
        DocumentationIntegrityError,
        match="injected interruption after commit",
    ):
        record_documentation_agent_result(
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

    assert {
        name: (wiki / name).read_bytes()
        for name in PROTECTED_NATIVE_ARTIFACTS
    } == protected_before
    assert (wiki / VERIFICATION_RECEIPT_FILENAME).read_bytes() == receipt_bytes
    assert load_documentation_run(workspace).state == "blocked"


def test_interrupted_refresh_finalization_restores_artifacts_and_controller_anchors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    _source, workspace, run, _receipt_bytes = _prepare_governed_source_run(
        tmp_path
    )
    capsys.readouterr()
    wiki = workspace / "wiki"
    protected_before = {
        name: (wiki / name).read_bytes()
        for name in PROTECTED_NATIVE_ARTIFACTS
    }
    ownership_path = workspace / run.evidence["generated_ownership"]
    refresh_path = workspace / run.evidence["native_refresh"]
    ownership_before = ownership_path.read_bytes()
    refresh_before = refresh_path.read_bytes()
    phase_path = (
        workspace
        / ".llm-wiki-docs"
        / "evidence"
        / "native-refresh-wiki-enrichment-01.json"
    )
    assert not phase_path.exists()

    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    index = wiki / "index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\nThis change reaches refresh finalization.\n",
        encoding="utf-8",
    )
    work_id, imported_edit = _imported_index_edit(workspace, run)
    real_write_json = documentation_run_service._write_json
    injected = {"raised": False}

    def interrupt_ownership_write(path, payload):
        if Path(path) == ownership_path and not injected["raised"]:
            injected["raised"] = True
            raise OSError("injected ownership finalization interruption")
        return real_write_json(path, payload)

    monkeypatch.setattr(
        documentation_run_service,
        "_write_json",
        interrupt_ownership_write,
    )

    with pytest.raises(
        DocumentationIntegrityError,
        match="finalization failed",
    ):
        record_documentation_agent_result(
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

    assert injected["raised"] is True
    assert {
        name: (wiki / name).read_bytes()
        for name in PROTECTED_NATIVE_ARTIFACTS
    } == protected_before
    assert ownership_path.read_bytes() == ownership_before
    assert refresh_path.read_bytes() == refresh_before
    assert not phase_path.exists()
    assert load_documentation_run(workspace).state == "blocked"


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


def test_agent_claim_evidence_is_recomputed_after_native_reanchor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, run = _prepare_source_run(tmp_path)
    wiki = workspace / "wiki"
    monkeypatch.chdir(tmp_path)
    service = api.build_documentation_query_service(
        str(source),
        wiki_dir=str(wiki),
    )
    claim = qualify_claim_evidence(
        service,
        claim_id="work:module-app",
        canonical_page="modules/app.md",
        concept_query="llm-wiki://modules/app",
    )
    monkeypatch.setattr(
        documentation_run_service,
        "build_live_documentation_query_service",
        lambda **_kwargs: pytest.fail(
            "post-refresh reconciliation rebuilt the live extraction"
        ),
    )
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    worklist = _read_json(workspace / run.evidence["semantic_worklist"])
    work_ids = [str(item["id"]) for item in worklist["items"]]
    evidence_pages = sorted(
        {
            "modules/app.md",
            *(
                str(item["canonical_path"])
                for item in worklist["items"]
                if item.get("canonical_path")
            ),
        }
    )
    (wiki / "index.md").write_text(
        "# Native Lifecycle Docs\n\n"
        "The application module is the supported implementation entry. See "
        "[its evidence](modules/app.md).\n",
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
            claim_evidence=[claim],
        ),
    )

    result = _read_json(workspace / updated.evidence["wiki-enrichment_result"])
    assert result["claim_evidence"] == [claim]
    assert result["reconciliation"]["claim_evidence"] == [claim]
    assert claim["freshness"]["evaluated"] is True
    assert claim["freshness"]["state"] == "current"
    readiness = _read_json(workspace / updated.evidence["semantic_readiness"])
    assert readiness["claim_evidence"] == [claim]


def test_tampered_agent_claim_coordinate_blocks_result_acceptance(
    tmp_path: Path,
) -> None:
    _source, workspace, run = _prepare_source_run(tmp_path)
    wiki = workspace / "wiki"
    service = DocumentationGraphQueryService(
        {},
        knowledge_view=load_knowledge_read_view(wiki, snapshot_only=True),
    )
    claim = qualify_claim_evidence(
        service,
        claim_id="finding:module-app",
        canonical_page="modules/app.md",
        concept_query="llm-wiki://modules/app",
    )
    claim["concept_locator"] = "llm-wiki://modules/forged"
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    worklist = _read_json(workspace / run.evidence["semantic_worklist"])
    work_ids = [str(item["id"]) for item in worklist["items"]]
    evidence_pages = sorted(
        {
            "modules/app.md",
            *(
                str(item["canonical_path"])
                for item in worklist["items"]
                if item.get("canonical_path")
            ),
        }
    )
    (wiki / "index.md").write_text(
        "# Native Lifecycle Docs\n\n"
        "The changed overview still links to "
        "[module evidence](modules/app.md).\n",
        encoding="utf-8",
    )
    protected_before = {
        name: (wiki / name).read_bytes()
        for name in NATIVE_ARTIFACTS
    }
    ownership_path = workspace / run.evidence["generated_ownership"]
    refresh_path = workspace / run.evidence["native_refresh"]
    ownership_before = ownership_path.read_bytes()
    refresh_before = refresh_path.read_bytes()

    with pytest.raises(
        DocumentationIntegrityError,
        match="current committed native view",
    ):
        record_documentation_agent_result(
            workspace,
            _agent_result(
                run.run_id,
                "wiki-enrichment",
                changed=["index.md"],
                completed=work_ids,
                claims=evidence_pages,
                claim_evidence=[claim],
            ),
        )

    blocked = load_documentation_run(workspace)
    assert blocked.state == "blocked"
    assert {
        name: (wiki / name).read_bytes()
        for name in NATIVE_ARTIFACTS
    } == protected_before
    assert ownership_path.read_bytes() == ownership_before
    assert refresh_path.read_bytes() == refresh_before
    assert not (
        workspace
        / ".llm-wiki-docs"
        / "evidence"
        / "native-refresh-wiki-enrichment-01.json"
    ).exists()


def test_missing_claim_internal_reference_fails_before_refresh_without_blocking(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, run = _prepare_source_run(tmp_path)
    wiki = workspace / "wiki"
    monkeypatch.chdir(tmp_path)
    service = api.build_documentation_query_service(
        str(source),
        wiki_dir=str(wiki),
    )
    claim = qualify_claim_evidence(
        service,
        claim_id="finding:missing-internal-reference",
        canonical_page="modules/app.md",
        concept_query="llm-wiki://modules/app",
        internal_evidence_ref=(
            ".llm-wiki-docs/evidence/missing-claim-source.json"
        ),
    )
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    run = load_documentation_run(workspace)
    worklist = _read_json(workspace / run.evidence["semantic_worklist"])
    work_ids = [str(item["id"]) for item in worklist["items"]]
    evidence_pages = sorted(
        {
            "modules/app.md",
            *(
                str(item["canonical_path"])
                for item in worklist["items"]
                if item.get("canonical_path")
            ),
        }
    )
    index = wiki / "index.md"
    index.write_text(
        "# Native Lifecycle Docs\n\n"
        "This semantic edit must survive a reusable malformed attempt. See "
        "[module evidence](modules/app.md).\n",
        encoding="utf-8",
    )
    protected_before = {
        name: (wiki / name).read_bytes()
        for name in NATIVE_ARTIFACTS
    }
    ownership_path = workspace / run.evidence["generated_ownership"]
    refresh_path = workspace / run.evidence["native_refresh"]
    ownership_before = ownership_path.read_bytes()
    refresh_before = refresh_path.read_bytes()
    run_before = (
        workspace / ".llm-wiki-docs" / "run.json"
    ).read_bytes()

    with pytest.raises(
        DocumentationSchemaError,
        match="internal reference is missing",
    ):
        record_documentation_agent_result(
            workspace,
            _agent_result(
                run.run_id,
                "wiki-enrichment",
                changed=["index.md"],
                completed=work_ids,
                claims=evidence_pages,
                claim_evidence=[claim],
            ),
        )

    assert {
        name: (wiki / name).read_bytes()
        for name in NATIVE_ARTIFACTS
    } == protected_before
    assert ownership_path.read_bytes() == ownership_before
    assert refresh_path.read_bytes() == refresh_before
    assert (
        workspace / ".llm-wiki-docs" / "run.json"
    ).read_bytes() == run_before
    assert index.read_text(encoding="utf-8").startswith(
        "# Native Lifecycle Docs"
    )
    reusable = load_documentation_run(workspace)
    assert reusable.state == "wiki_enrichment"
    assert reusable.stage_attempts["wiki-enrichment"] == 1
    assert not (
        workspace
        / ".llm-wiki-docs"
        / "results"
        / "wiki-enrichment-01.json"
    ).exists()
    assert not (
        workspace
        / ".llm-wiki-docs"
        / "evidence"
        / "native-refresh-wiki-enrichment-01.json"
    ).exists()


def test_unverified_adopted_run_reconciles_snapshot_only_claim_evidence(
    tmp_path: Path,
) -> None:
    _source, seed_workspace, _seed_run = _prepare_source_run(tmp_path)
    workspace = tmp_path / "snapshot-only-workspace"
    run = prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        input_wiki_root=seed_workspace / "wiki",
        freshness_policy="allow-unverified",
        site_name="Snapshot-only Native Docs",
        project_purpose="Preserve snapshot-qualified native claims.",
        audiences=["operator"],
        audience_intent={"operator": "review snapshot-qualified evidence"},
    )
    wiki = workspace / "wiki"
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    index = wiki / "index.md"
    index.write_text(
        "# Imported Wiki\n\n"
        "The imported claim remains explicitly snapshot-only.\n",
        encoding="utf-8",
    )
    service = DocumentationGraphQueryService(
        {},
        knowledge_view=load_knowledge_read_view(wiki, snapshot_only=True),
    )
    claim = qualify_claim_evidence(
        service,
        claim_id="claim:imported-snapshot",
        canonical_page="index.md",
        concept_query="llm-wiki://modules/imported",
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
            claim_evidence=[claim],
            imported_page_edits=[imported_edit],
        ),
    )

    result = _read_json(workspace / updated.evidence["wiki-enrichment_result"])
    assert claim["freshness"]["evaluated"] is False
    assert claim["freshness"]["state"] is None
    assert result["reconciliation"]["claim_evidence"] == [claim]
    assert result["reconciliation"]["native_projection_refresh"] is None


def test_bound_source_becoming_unavailable_reconciles_snapshot_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, run = _prepare_source_run(tmp_path)
    wiki = workspace / "wiki"
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    worklist = _read_json(workspace / run.evidence["semantic_worklist"])
    work_ids = [str(item["id"]) for item in worklist["items"]]
    evidence_pages = sorted(
        {
            "modules/app.md",
            *(
                str(item["canonical_path"])
                for item in worklist["items"]
                if item.get("canonical_path")
            ),
        }
    )
    (wiki / "index.md").write_text(
        "# Native Lifecycle Docs\n\n"
        "The source is temporarily unavailable, so this result remains "
        "snapshot-qualified. See [module evidence](modules/app.md).\n",
        encoding="utf-8",
    )
    source.rename(tmp_path / "source-offline")
    snapshot_service = DocumentationGraphQueryService(
        {},
        knowledge_view=load_knowledge_read_view(wiki, snapshot_only=True),
    )
    claim = qualify_claim_evidence(
        snapshot_service,
        claim_id="claim:source-unavailable-snapshot",
        canonical_page="modules/app.md",
        concept_query="llm-wiki://modules/app",
    )
    monkeypatch.setattr(
        documentation_run_service,
        "build_live_documentation_query_service",
        lambda **_kwargs: pytest.fail(
            "source-unavailable reconciliation must not extract live"
        ),
    )

    updated = record_documentation_agent_result(
        workspace,
        _agent_result(
            run.run_id,
            "wiki-enrichment",
            changed=["index.md"],
            completed=work_ids,
            claims=evidence_pages,
            claim_evidence=[claim],
        ),
    )

    result = _read_json(workspace / updated.evidence["wiki-enrichment_result"])
    assert result["reconciliation"]["claim_evidence"] == [claim]
    assert result["reconciliation"]["native_projection_refresh"] is None
    assert result["reconciliation"]["source_and_input_integrity"] == [
        {
            "check": "source_integrity",
            "ok": True,
            "limited": True,
            "availability": "source_unavailable",
        }
    ]
    assert "native_knowledge_snapshot_only" in updated.verdict_limitations


def test_raw_service_failure_after_refresh_rolls_back_authority_then_blocks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, run = _prepare_source_run(tmp_path)
    wiki = workspace / "wiki"
    monkeypatch.chdir(tmp_path)
    service = api.build_documentation_query_service(
        str(source),
        wiki_dir=str(wiki),
    )
    claim = qualify_claim_evidence(
        service,
        claim_id="finding:query-failure",
        canonical_page="modules/app.md",
        concept_query="llm-wiki://modules/app",
    )
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    run = load_documentation_run(workspace)
    worklist = _read_json(workspace / run.evidence["semantic_worklist"])
    work_ids = [str(item["id"]) for item in worklist["items"]]
    evidence_pages = sorted(
        {
            "modules/app.md",
            *(
                str(item["canonical_path"])
                for item in worklist["items"]
                if item.get("canonical_path")
            ),
        }
    )
    index = wiki / "index.md"
    index.write_text(
        "# Native Lifecycle Docs\n\n"
        "This semantic edit remains after a failed native reconciliation. See "
        "[module evidence](modules/app.md).\n",
        encoding="utf-8",
    )
    protected_before = {
        name: (wiki / name).read_bytes()
        for name in NATIVE_ARTIFACTS
    }
    ownership_path = workspace / run.evidence["generated_ownership"]
    refresh_path = workspace / run.evidence["native_refresh"]
    ownership_before = ownership_path.read_bytes()
    refresh_before = refresh_path.read_bytes()
    evidence_before = dict(run.evidence)
    anchors_before = dict(run.integrity_anchors)
    limitations_before = list(run.verdict_limitations)

    def fail_reconciliation(*_args, **_kwargs):
        raise RuntimeError("injected raw query-service failure")

    monkeypatch.setattr(
        documentation_run_service,
        "reconcile_claim_evidence_records",
        fail_reconciliation,
    )

    with pytest.raises(
        DocumentationIntegrityError,
        match="injected raw query-service failure",
    ):
        record_documentation_agent_result(
            workspace,
            _agent_result(
                run.run_id,
                "wiki-enrichment",
                changed=["index.md"],
                completed=work_ids,
                claims=evidence_pages,
                claim_evidence=[claim],
            ),
        )

    assert {
        name: (wiki / name).read_bytes()
        for name in NATIVE_ARTIFACTS
    } == protected_before
    assert ownership_path.read_bytes() == ownership_before
    assert refresh_path.read_bytes() == refresh_before
    assert index.read_text(encoding="utf-8").startswith(
        "# Native Lifecycle Docs"
    )
    blocked = load_documentation_run(workspace)
    assert blocked.state == "blocked"
    assert blocked.evidence == evidence_before
    assert blocked.integrity_anchors == anchors_before
    assert blocked.verdict_limitations == limitations_before
    assert not (
        workspace
        / ".llm-wiki-docs"
        / "results"
        / "wiki-enrichment-01.json"
    ).exists()
    assert not (
        workspace
        / ".llm-wiki-docs"
        / "evidence"
        / "native-refresh-wiki-enrichment-01.json"
    ).exists()


def test_post_refresh_reconciliation_failure_restores_governance_and_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    source, workspace, run, _receipt_bytes = _prepare_governed_source_run(
        tmp_path
    )
    capsys.readouterr()
    wiki = workspace / "wiki"
    monkeypatch.chdir(tmp_path)
    service = api.build_documentation_query_service(
        str(source),
        wiki_dir=str(wiki),
    )
    claim = qualify_claim_evidence(
        service,
        claim_id="finding:governed-query-failure",
        canonical_page="modules/app.md",
        concept_query="llm-wiki://modules/app",
    )
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    index = wiki / "index.md"
    index.write_text(
        "# Governed Native Lifecycle Docs\n\n"
        "This semantic edit remains after reconciliation fails. See "
        "[module evidence](modules/app.md).\n",
        encoding="utf-8",
    )
    work_id, imported_edit = _imported_index_edit(workspace, run)
    protected_before = {
        name: (wiki / name).read_bytes()
        for name in PROTECTED_NATIVE_ARTIFACTS
    }

    def fail_reconciliation(*_args, **_kwargs):
        raise RuntimeError("injected governed reconciliation failure")

    monkeypatch.setattr(
        documentation_run_service,
        "reconcile_claim_evidence_records",
        fail_reconciliation,
    )

    with pytest.raises(
        DocumentationIntegrityError,
        match="injected governed reconciliation failure",
    ):
        record_documentation_agent_result(
            workspace,
            _agent_result(
                run.run_id,
                "wiki-enrichment",
                status="partial",
                changed=["index.md"],
                completed=[work_id],
                claims=["index.md", "modules/app.md"],
                claim_evidence=[claim],
                imported_page_edits=[imported_edit],
            ),
        )

    assert {
        name: (wiki / name).read_bytes()
        for name in PROTECTED_NATIVE_ARTIFACTS
    } == protected_before
    assert index.read_text(encoding="utf-8").startswith(
        "# Governed Native Lifecycle Docs"
    )
    assert load_documentation_run(workspace).state == "blocked"
    assert not (
        workspace
        / ".llm-wiki-docs"
        / "results"
        / "wiki-enrichment-01.json"
    ).exists()


def test_runtime_capture_is_out_of_band_and_digest_reconciled(
    tmp_path: Path,
) -> None:
    _source, workspace, prepared, _receipt = _prepare_governed_source_run(
        tmp_path,
        knowledge_mode="public-portable",
        include_receipt=False,
    )
    run, _result, _refresh = _complete_wiki_enrichment(workspace, prepared)
    build_documentation_agent_packet(workspace, stage="user-docs")
    wiki = workspace / "wiki"
    view = load_knowledge_read_view(wiki, snapshot_only=True)
    service = DocumentationGraphQueryService({}, knowledge_view=view)
    concept_uid = service.get_concept("llm-wiki://modules/app")["concept"]["uid"]
    native_authority_before = {
        name: (wiki / name).read_bytes()
        for name in NATIVE_ARTIFACTS | {GOVERNANCE_FILENAME}
    }
    asset = wiki / "assets" / "guides" / "run-fixture" / "result.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"\x89PNG\r\n\x1a\nredacted-fixture")
    text_asset = asset.with_name("result.txt")
    text_asset.write_text("redacted command output\n", encoding="utf-8")
    guide = wiki / "guides" / "run-fixture.md"
    guide.parent.mkdir(parents=True, exist_ok=True)
    guide.write_text(
        "# Run the fixture\n\n"
        "Use the supported operation described by the "
        "[application module](../modules/app.md).\n\n"
        "![Redacted successful fixture result]"
        "(../assets/guides/run-fixture/result.png)\n\n"
        "[Redacted text output]"
        "(../assets/guides/run-fixture/result.txt)\n",
        encoding="utf-8",
    )
    index = wiki / "index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\nContinue with the [run fixture guide](guides/run-fixture.md).\n",
        encoding="utf-8",
    )
    assert {
        name: (wiki / name).read_bytes()
        for name in NATIVE_ARTIFACTS | {GOVERNANCE_FILENAME}
    } == native_authority_before
    _imported_work_id, imported_edit = _imported_index_edit(
        workspace,
        run,
        stage="user-docs",
    )
    digest = _sha256(asset.read_bytes())
    capture = {
        "schema_version": "llm-wiki-documentation-runtime-capture/v1",
        "capture_id": "capture:run-fixture",
        "capture_digest": digest,
        "capture_path": "assets/guides/run-fixture/result.png",
        "command_or_flow_id": "flow:run-fixture",
        "result": {"state": "captured", "exit_code": 0},
        "concept_uid": concept_uid,
        "concept_locator": "llm-wiki://modules/app",
        "section_locator": None,
        "native_observation": {
            "availability": "ready",
            "reason": "knowledge-ready",
            "structural_evidence_state": "present",
            "freshness_evaluated": False,
            "freshness_state": None,
            "freshness_reason": "freshness-not-evaluated",
        },
        "redaction": {"outcome": "redacted", "limitations": []},
        "environment": {"mode": "disposable", "limitations": []},
        "limitations": [
            "binary-media-content-not-machine-inspected",
            "canonical-body-media-review-required",
            "runtime-evidence-is-not-native-authority",
        ],
    }
    text_capture = {
        **capture,
        "capture_id": "capture:run-fixture-text",
        "capture_digest": _sha256(text_asset.read_bytes()),
        "capture_path": "assets/guides/run-fixture/result.txt",
    }

    updated = record_documentation_agent_result(
        workspace,
        _agent_result(
            run.run_id,
            "user-docs",
            changed=[
                "assets/guides/run-fixture/result.png",
                "assets/guides/run-fixture/result.txt",
                "guides/run-fixture.md",
                "index.md",
            ],
            claims=["modules/app.md"],
            runtime_captures=[capture, text_capture],
            imported_page_edits=[imported_edit],
        ),
    )

    result = _read_json(workspace / updated.evidence["user-docs_result"])
    assert result["runtime_captures"] == [capture, text_capture]
    assert result["reconciliation"]["runtime_captures"] == [
        {
            **capture,
            "reconciliation": {
                "resolution": "exact",
                "uid": concept_uid,
                "locator": "llm-wiki://modules/app",
                "section_state": "not-requested",
            },
        },
        {
            **text_capture,
            "reconciliation": {
                "resolution": "exact",
                "uid": concept_uid,
                "locator": "llm-wiki://modules/app",
                "section_state": "not-requested",
            },
        },
    ]
    assert asset.read_bytes() == b"\x89PNG\r\n\x1a\nredacted-fixture"
    assert text_asset.read_text(encoding="utf-8") == "redacted command output\n"
    export_report = export_documentation_run(workspace)
    assert export_report["validation"]["knowledge_projection"]["mode"] == (
        "public-portable"
    )
