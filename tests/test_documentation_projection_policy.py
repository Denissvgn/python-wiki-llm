"""Native projection policy coverage for standalone documentation exports."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

import llm_wiki_cli.services.documentation_run as documentation_run
from llm_wiki_cli.services.documentation_run import (
    DocumentationIntegrityError,
    DocumentationRunError,
    DocumentationSchemaError,
    export_documentation_run,
    load_documentation_run,
    save_documentation_run,
)
from llm_wiki_cli.services.knowledge_artifacts import build_knowledge_commit_plan
from llm_wiki_cli.services.knowledge_consumption import (
    build_knowledge_read_view,
    load_knowledge_read_view,
)
from llm_wiki_cli.services.knowledge_governance import (
    GovernanceLedger,
    apply_governance_projection,
    concept_references_from_knowledge,
    reconcile_concepts,
)
from llm_wiki_cli.services.knowledge_loader import KnowledgeLoadResult
from llm_wiki_cli.services.knowledge_model import (
    KnowledgeLoadState,
    serialize_knowledge_index,
)
from llm_wiki_cli.services.knowledge_projection import project_knowledge
from tests.knowledge_fixtures import FIXTURE_REPOSITORY_IDENTITY
from tests.test_documentation_protocol import _prepare_source_run_at_review
from tests.test_knowledge_projection import _base_view


def _governed_snapshot_view(wiki_root):
    current = load_knowledge_read_view(wiki_root, snapshot_only=True)
    assert current.knowledge is not None
    assert current.surface is not None
    assert current.manifest_basis is not None
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_documentation_publication"),
        concept_references_from_knowledge(current.knowledge),
    )
    governed = apply_governance_projection(current.knowledge, ledger)
    surface_bytes = (
        json.dumps(dict(current.surface), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    plan = build_knowledge_commit_plan(
        wiki_root,
        surface_index_bytes=surface_bytes,
        knowledge_index_bytes=serialize_knowledge_index(governed).encode("utf-8"),
        manifest=replace(current.manifest_basis, artifact_hashes=None),
    )
    return build_knowledge_read_view(
        KnowledgeLoadResult(
            status=KnowledgeLoadState.VALID,
            surface=dict(current.surface),
            knowledge=governed,
            manifest_basis=plan.committed_manifest,
            issues=(),
        ),
        snapshot_only=True,
    )


@pytest.mark.parametrize(
    ("mode", "identity"),
    [
        ("off", "example.invalid/private"),
        ("internal", "example.invalid/private"),
        ("future-profile", None),
    ],
)
def test_projection_policy_rejects_unsafe_mode_identity_pairs(mode, identity):
    with pytest.raises(DocumentationSchemaError):
        documentation_run._validate_documentation_projection_policy(
            mode,
            identity,
        )


@pytest.mark.parametrize("mode", ["public-portable", "internal"])
def test_standalone_projection_loader_is_snapshot_only_and_preserves_missing_governance(
    tmp_path,
    monkeypatch,
    mode,
):
    view = _base_view(tmp_path)
    observed = {}

    def fake_load(wiki_root, **kwargs):
        observed.update(wiki_root=wiki_root, kwargs=kwargs)
        return view

    monkeypatch.setattr(
        "llm_wiki_cli.services.knowledge_consumption.load_knowledge_read_view",
        fake_load,
    )
    public_identity = (
        FIXTURE_REPOSITORY_IDENTITY if mode == "public-portable" else None
    )

    projection = documentation_run._load_documentation_knowledge_projection(
        tmp_path / "wiki",
        knowledge_mode=mode,
        knowledge_public_repository_identity=public_identity,
    )

    assert projection is not None
    assert projection.profile.value == mode
    assert projection.bundle["repository_identity"] == FIXTURE_REPOSITORY_IDENTITY
    assert "governance-not-available" in projection.warnings
    assert observed == {
        "wiki_root": tmp_path / "wiki",
        "kwargs": {
            "snapshot_only": True,
            "include_machine_verification": True,
        },
    }
    assert {
        (
            concept["freshness"]["state"],
            concept["freshness"]["evaluated"],
            concept["freshness"]["live_comparison_performed"],
        )
        for concept in projection.concepts.values()
    } == {("not-evaluated", False, False)}


def test_off_projection_mode_performs_no_native_read(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "llm_wiki_cli.services.knowledge_consumption.load_knowledge_read_view",
        lambda *_args, **_kwargs: pytest.fail("off mode loaded native knowledge"),
    )

    assert (
        documentation_run._load_documentation_knowledge_projection(
            tmp_path / "wiki",
            knowledge_mode="off",
            knowledge_public_repository_identity=None,
        )
        is None
    )


def test_standalone_export_reuses_persisted_projection_policy_and_hash(
    tmp_path,
    monkeypatch,
):
    workspace, prepared = _prepare_source_run_at_review(tmp_path)
    assert prepared.publication["knowledge_mode"] == "off"
    assert prepared.publication["knowledge_public_repository_identity"] is None
    governed_view = _governed_snapshot_view(workspace / "wiki")
    monkeypatch.setattr(
        "llm_wiki_cli.services.knowledge_consumption.load_knowledge_read_view",
        lambda *_args, **_kwargs: governed_view,
    )

    for mode in ("off", "public-portable", "internal"):
        run = load_documentation_run(workspace)
        run.publication["knowledge_mode"] = mode
        run.publication["knowledge_public_repository_identity"] = None
        save_documentation_run(workspace, run)

        report = export_documentation_run(workspace, knowledge_mode=mode)
        persisted = load_documentation_run(workspace)
        export_payload = json.loads(
            (workspace / persisted.evidence["site_export"]).read_text(
                encoding="utf-8"
            )
        )
        check_payload = json.loads(
            (workspace / persisted.evidence["site_check"]).read_text(
                encoding="utf-8"
            )
        )
        exported = export_payload["knowledge_projection"]
        checked = check_payload["knowledge_projection"]

        assert exported["mode"] == checked["mode"] == mode
        assert exported["source_knowledge_hash"] == checked[
            "source_knowledge_hash"
        ]
        assert exported["freshness_scope"] == "snapshot-only"
        assert exported["freshness_evaluated"] is False
        assert exported["canonical_body_media_review"] == "separate-required"
        assert exported["derived_output"] == "disposable-rebuildable"
        final_projection = report["validation"]["knowledge_projection"]
        assert final_projection["mode"] == mode
        assert final_projection["export_source_knowledge_hash"] == exported[
            "source_knowledge_hash"
        ]
        assert final_projection["check_source_knowledge_hash"] == checked[
            "source_knowledge_hash"
        ]
        assert final_projection["source_knowledge_hashes_match"] is True
        if mode == "off":
            assert exported["knowledge_metadata"] == "off"
            assert exported["source_knowledge_hash"] is None
        else:
            assert exported["knowledge_metadata"] == "summary"
            assert exported["profile"] == mode
            assert exported["source_knowledge_hash"].startswith("sha256:")


def test_standalone_export_rejects_policy_mismatch_before_writing(tmp_path):
    workspace, _ = _prepare_source_run_at_review(tmp_path)

    with pytest.raises(DocumentationRunError, match="differs from the prepared"):
        export_documentation_run(workspace, knowledge_mode="internal")

    assert list((workspace / "site").iterdir()) == []


def test_selected_projection_failure_blocks_without_implicit_fallback(
    tmp_path,
    monkeypatch,
):
    workspace, run = _prepare_source_run_at_review(tmp_path)
    run.publication["knowledge_mode"] = "public-portable"
    run.publication["knowledge_public_repository_identity"] = None
    save_documentation_run(workspace, run)
    monkeypatch.setattr(
        "llm_wiki_cli.services.knowledge_consumption.load_knowledge_read_view",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("invalid committed projection")
        ),
    )

    with pytest.raises(
        DocumentationIntegrityError,
        match="No un-enriched fallback was performed",
    ):
        export_documentation_run(workspace)

    assert load_documentation_run(workspace).state == "blocked"
    assert list((workspace / "site").iterdir()) == []


def test_selected_projection_without_governance_fails_closed(tmp_path):
    workspace, run = _prepare_source_run_at_review(tmp_path)
    run.publication["knowledge_mode"] = "public-portable"
    run.publication["knowledge_public_repository_identity"] = None
    save_documentation_run(workspace, run)

    with pytest.raises(
        DocumentationIntegrityError,
        match="bundle.bundle_id",
    ):
        export_documentation_run(workspace)

    assert load_documentation_run(workspace).state == "blocked"
    assert list((workspace / "site").iterdir()) == []


def test_changed_projection_hash_blocks_stale_enriched_output(
    tmp_path,
    monkeypatch,
):
    workspace, run = _prepare_source_run_at_review(tmp_path)
    run.publication["knowledge_mode"] = "public-portable"
    run.publication["knowledge_public_repository_identity"] = None
    save_documentation_run(workspace, run)
    projection = project_knowledge(
        _governed_snapshot_view(workspace / "wiki"),
        profile="public-portable",
    )
    stale_projection = replace(
        projection,
        source_knowledge_hash="sha256:" + "f" * 64,
    )
    projections = iter((projection, stale_projection))
    monkeypatch.setattr(
        documentation_run,
        "_load_documentation_knowledge_projection",
        lambda *_args, **_kwargs: next(projections),
    )

    with pytest.raises(
        DocumentationIntegrityError,
        match="snapshot changed between export and check",
    ):
        export_documentation_run(workspace)

    assert load_documentation_run(workspace).state == "blocked"
