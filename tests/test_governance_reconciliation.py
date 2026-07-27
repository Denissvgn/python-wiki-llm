"""Governance identity evidence carried by bootstrap, sync, and migration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import (
    bootstrap_cmd,
    knowledge_cmd,
    migrate_cmd,
    sync_cmd,
)
from llm_wiki_cli.commands.migrate_cmd import ExistingPage, MigrationPlan, TargetPage
from llm_wiki_cli.services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from llm_wiki_cli.services.knowledge_governance import (
    ALIAS_LOCATOR,
    ALIAS_NATURAL_KEY,
    ConceptGovernanceReference,
    GovernanceError,
    GovernanceLedger,
    load_governance,
    natural_key_for,
    reconcile_concepts,
    save_governance,
    validate_governance_projection,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.knowledge_orchestration import (
    finalize_runtime_knowledge,
)
from llm_wiki_cli.services.sync_manifest import (
    ManifestArtifactHashes,
    SyncManifest,
)
from llm_wiki_cli.services.wiki_surface import PageKind, mcp_uri
from tests.test_knowledge_generation import _runtime_input_case


def test_sync_carries_supported_entity_and_module_renames() -> None:
    manifest = SyncManifest(
        sources={
            "old.py": {
                "hash": "sha256:" + "0" * 64,
                "language": "python",
                "entities": ["Moved"],
                "entity_pages": {"Moved": "OldMoved"},
                "module_page": "old",
            },
            "same.py": {
                "hash": "sha256:" + "1" * 64,
                "language": "python",
                "entities": [],
                "entity_pages": {},
                "module_page": "same",
            },
        }
    )
    diff = sync_cmd.SyncDiff(
        moved_entities={"Moved": ("old.py", "new.py")},
        renamed_entity_pages={
            ("Stable", "same.py"): ("Stable", "pkg_Stable")
        },
        renamed_module_pages={"same.py": ("same", "pkg_same")},
    )

    moves = sync_cmd._governance_moves_for_sync(
        diff,
        manifest,
        entity_page_cache={
            ("Moved", "new.py"): "NewMoved",
            ("Stable", "same.py"): "pkg_Stable",
        },
    )

    assert moves == {
        mcp_uri(PageKind.ENTITIES, "OldMoved"): mcp_uri(
            PageKind.ENTITIES, "NewMoved"
        ),
        mcp_uri(PageKind.ENTITIES, "Stable"): mcp_uri(
            PageKind.ENTITIES, "pkg_Stable"
        ),
        mcp_uri(PageKind.MODULES, "same"): mcp_uri(
            PageKind.MODULES, "pkg_same"
        ),
    }


def test_sync_does_not_guess_when_one_old_route_fans_out() -> None:
    diff = sync_cmd.SyncDiff(
        renamed_entity_pages={
            ("Same", "a.py"): ("Same", "a_Same"),
            ("Same", "b.py"): ("Same", "b_Same"),
        }
    )

    moves = sync_cmd._governance_moves_for_sync(
        diff,
        SyncManifest(),
        entity_page_cache={},
    )

    assert moves == {}


def test_bootstrap_uses_only_unambiguous_prior_manifest_coordinates() -> None:
    manifest = SyncManifest(
        sources={
            "old.py": {
                "hash": "sha256:" + "0" * 64,
                "language": "python",
                "entities": ["Moved"],
                "entity_pages": {"Moved": "Moved"},
                "module_page": "old",
            },
            "same.py": {
                "hash": "sha256:" + "1" * 64,
                "language": "python",
                "entities": [],
                "entity_pages": {},
                "module_page": "same",
            },
        }
    )
    inventory = {
        "new.py": {"classes": [{"name": "Moved"}]},
        "same.py": {"classes": []},
    }
    page_maps = bootstrap_cmd._BootstrapPageMaps(
        module_page_map={"new.py": "new", "same.py": "pkg_same"},
        entity_page_name_cache={("Moved", "new.py"): "Moved"},
        entity_occurrence_page_name_cache={("Moved", "new.py", 1): "Moved"},
    )

    moves = bootstrap_cmd._governance_moves_for_bootstrap(
        manifest,
        inventory,
        page_maps,
    )

    assert moves == {
        mcp_uri(PageKind.MODULES, "same"): mcp_uri(
            PageKind.MODULES, "pkg_same"
        )
    }


def test_migration_match_plan_preserves_uid_and_retains_unmatched_identity(
    tmp_path: Path,
) -> None:
    old_locator = mcp_uri(PageKind.MODULES, "legacy")
    new_locator = mcp_uri(PageKind.MODULES, "canonical")
    unmatched_locator = mcp_uri(PageKind.MODULES, "orphan")
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_migration_test"),
        (
            ConceptGovernanceReference(
                locator=old_locator,
                concept_kind="source-module",
                natural_key=natural_key_for("source-module", "modules/legacy.md"),
            ),
            ConceptGovernanceReference(
                locator=unmatched_locator,
                concept_kind="source-module",
                natural_key=natural_key_for("source-module", "modules/orphan.md"),
            ),
        ),
    )
    save_governance(tmp_path, ledger, expected_hash=None)
    uid_by_locator = {
        allocation.locator: uid for uid, allocation in ledger.concepts.items()
    }
    plan = MigrationPlan(
        archive_name="migrate-20990101000000",
        targets=[
            TargetPage(
                "modules",
                "canonical",
                "modules/canonical.md",
                "# canonical\n",
                "canonical.py",
            )
        ],
        matches={
            "modules/canonical.md": [
                ExistingPage(
                    kind="modules",
                    path=tmp_path / "modules" / "legacy.md",
                    rel="modules/legacy.md",
                    stem="legacy",
                    content="# legacy\n",
                )
            ]
        },
        unmatched=[
            ExistingPage(
                kind="modules",
                path=tmp_path / "modules" / "orphan.md",
                rel="modules/orphan.md",
                stem="orphan",
                content="# orphan\n",
            )
        ],
        link_map={"modules/legacy.md": "modules/canonical.md"},
    )

    migrate_cmd._prepare_migration_governance_plan(tmp_path, plan)

    assert plan.governance_moves == {old_locator: new_locator}
    assert plan.governance_enabled is True
    assert plan.governance_uid_reuses == 1
    assert plan.governance_new_allocations == 0

    reconciled = reconcile_concepts(
        load_governance(tmp_path).ledger,
        (
            ConceptGovernanceReference(
                locator=new_locator,
                concept_kind="source-module",
                natural_key=natural_key_for(
                    "source-module", "modules/canonical.md"
                ),
            ),
        ),
        moves=plan.governance_moves,
    )

    old_uid = uid_by_locator[old_locator]
    assert reconciled.concepts[old_uid].locator == new_locator
    assert any(
        alias.uid == old_uid and alias.value == old_locator
        for alias in reconciled.aliases.values()
    )
    assert uid_by_locator[unmatched_locator] in reconciled.concepts
    assert reconciled.lifecycle_events == {}


def test_migration_matches_path_form_ledger_locators_to_resource_uris(
    tmp_path: Path,
) -> None:
    old_locator = mcp_uri(PageKind.MODULES, "legacy")
    new_locator = mcp_uri(PageKind.MODULES, "canonical")
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_path_form_migration"),
        (
            ConceptGovernanceReference(
                locator=old_locator,
                concept_kind="source-module",
                natural_key=natural_key_for(
                    "source-module",
                    "modules/legacy.md",
                ),
            ),
        ),
    )
    uid = next(iter(ledger.concepts))
    ledger = replace(
        ledger,
        concepts={
            uid: replace(
                ledger.concepts[uid],
                locator="modules/legacy.md",
            )
        },
    )
    save_governance(tmp_path, ledger, expected_hash=None)
    target = TargetPage(
        "modules",
        "canonical",
        "modules/canonical.md",
        "# canonical\n",
        "canonical.py",
    )
    existing = ExistingPage(
        kind="modules",
        path=tmp_path / "modules" / "legacy.md",
        rel="modules/legacy.md",
        stem="legacy",
        content="# legacy\n",
    )
    plan = MigrationPlan(
        archive_name="migrate-path-form",
        targets=[target],
        matches={target.rel: [existing]},
        link_map={existing.rel: target.rel},
    )

    migrate_cmd._prepare_migration_governance_plan(tmp_path, plan)

    assert plan.governance_moves == {old_locator: new_locator}
    assert plan.governance_uid_reuses == 1
    assert plan.governance_new_allocations == 0
    assert plan.governance_ambiguous_moves == 0


def test_migration_defers_equivalent_path_form_target_owner_collision(
    tmp_path: Path,
) -> None:
    old_locator = mcp_uri(PageKind.MODULES, "legacy")
    target_locator = mcp_uri(PageKind.MODULES, "canonical")
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_path_target_collision"),
        (
            ConceptGovernanceReference(
                locator=old_locator,
                concept_kind="source-module",
                natural_key=natural_key_for(
                    "source-module",
                    "modules/legacy.md",
                ),
            ),
            ConceptGovernanceReference(
                locator=target_locator,
                concept_kind="source-module",
                natural_key=natural_key_for(
                    "source-module",
                    "modules/canonical.md",
                ),
            ),
        ),
    )
    path_concepts = {
        uid: replace(
            allocation,
            locator=(
                "modules/legacy.md"
                if allocation.locator == old_locator
                else "modules/canonical.md"
            ),
        )
        for uid, allocation in ledger.concepts.items()
    }
    save_governance(
        tmp_path,
        replace(ledger, concepts=path_concepts),
        expected_hash=None,
    )
    target = TargetPage(
        "modules",
        "canonical",
        "modules/canonical.md",
        "# canonical\n",
        "canonical.py",
    )
    existing = ExistingPage(
        kind="modules",
        path=tmp_path / "modules" / "legacy.md",
        rel="modules/legacy.md",
        stem="legacy",
        content="# legacy\n",
    )
    plan = MigrationPlan(
        archive_name="migrate-path-collision",
        targets=[target],
        matches={target.rel: [existing]},
        link_map={existing.rel: target.rel},
    )

    migrate_cmd._prepare_migration_governance_plan(tmp_path, plan)

    assert plan.governance_moves == {}
    assert plan.governance_uid_reuses == 0
    assert plan.governance_new_allocations == 0
    assert plan.governance_ambiguous_moves == 1


def test_migration_identity_plan_is_independent_of_archive_timestamp(
    tmp_path: Path,
) -> None:
    old_locator = mcp_uri(PageKind.ENTITIES, "Old")
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_archive_time_test"),
        (
            ConceptGovernanceReference(
                locator=old_locator,
                concept_kind="code-entity",
                natural_key=natural_key_for(
                    "code-entity", "entities/Old.md"
                ),
            ),
        ),
    )
    save_governance(tmp_path, ledger, expected_hash=None)
    target = TargetPage(
        "entities",
        "Canonical",
        "entities/Canonical.md",
        "# Canonical\n",
    )
    existing = ExistingPage(
        kind="entities",
        path=tmp_path / "entities" / "Old.md",
        rel="entities/Old.md",
        stem="Old",
        content="# Old\n",
    )

    plans = [
        MigrationPlan(
            archive_name=archive_name,
            targets=[target],
            matches={target.rel: [existing]},
            link_map={existing.rel: target.rel},
        )
        for archive_name in (
            "migrate-20200101000000",
            "migrate-20990101000000",
        )
    ]
    for plan in plans:
        migrate_cmd._prepare_migration_governance_plan(tmp_path, plan)

    assert plans[0].governance_moves == plans[1].governance_moves == {
        old_locator: mcp_uri(PageKind.ENTITIES, "Canonical")
    }


def test_migration_refuses_missing_previously_committed_ledger(
    tmp_path: Path,
) -> None:
    digest = "sha256:" + "a" * 64
    plan = MigrationPlan(
        archive_name="migrate-test",
        targets=[],
        manifest=SyncManifest(
            artifact_hashes=ManifestArtifactHashes(
                surface_index_hash=digest,
                knowledge_index_hash=digest,
                evaluated_envelope_hash=digest,
                governance_hash=digest,
            )
        ),
    )

    with pytest.raises(GovernanceError, match="restore the ledger") as raised:
        migrate_cmd._prepare_migration_governance_plan(tmp_path, plan)
    assert raised.value.code == "governance-missing"


def test_migration_defers_two_governed_sources_claiming_one_target(
    tmp_path: Path,
) -> None:
    old_locators = (
        mcp_uri(PageKind.MODULES, "old_a"),
        mcp_uri(PageKind.MODULES, "old_b"),
    )
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_ambiguous_migration"),
        tuple(
            ConceptGovernanceReference(
                locator=locator,
                concept_kind="source-module",
                natural_key=natural_key_for(
                    "source-module", f"modules/old_{suffix}.md"
                ),
            )
            for locator, suffix in zip(old_locators, ("a", "b"), strict=True)
        ),
    )
    save_governance(tmp_path, ledger, expected_hash=None)
    target = TargetPage(
        "modules",
        "combined",
        "modules/combined.md",
        "# combined\n",
    )
    old_pages = [
        ExistingPage(
            kind="modules",
            path=tmp_path / "modules" / f"old_{suffix}.md",
            rel=f"modules/old_{suffix}.md",
            stem=f"old_{suffix}",
            content=f"# old {suffix}\n",
        )
        for suffix in ("a", "b")
    ]
    plan = MigrationPlan(
        archive_name="migrate-test",
        targets=[target],
        matches={target.rel: old_pages},
        link_map={page.rel: target.rel for page in old_pages},
    )

    migrate_cmd._prepare_migration_governance_plan(tmp_path, plan)

    assert plan.governance_moves == {}
    assert plan.governance_uid_reuses == 0
    assert plan.governance_new_allocations == 1
    assert plan.governance_ambiguous_moves == 2


def test_sync_and_bootstrap_preflight_missing_committed_ledger(
    tmp_path: Path,
) -> None:
    digest = "sha256:" + "b" * 64
    manifest = SyncManifest(
        artifact_hashes=ManifestArtifactHashes(
            surface_index_hash=digest,
            knowledge_index_hash=digest,
            evaluated_envelope_hash=digest,
            governance_hash=digest,
        )
    )
    manifest.save(tmp_path)

    with pytest.raises(GovernanceError, match="restore the ledger"):
        sync_cmd._preflight_sync_governance(tmp_path, manifest)
    with pytest.raises(GovernanceError, match="restore the ledger"):
        bootstrap_cmd._preflight_bootstrap_governance(tmp_path)


def test_governed_runtime_dry_run_does_not_touch_lock_or_tree(
    tmp_path: Path,
) -> None:
    runtime, _snapshot, _fixture = _runtime_input_case(
        tmp_path,
        inventory_complete=True,
    )
    committed = finalize_runtime_knowledge(
        replace(
            runtime,
            governance=GovernanceLedger.empty("kb_dry_run_tree"),
        )
    )

    def snapshot_tree() -> dict[str, tuple[bytes, int]]:
        return {
            path.relative_to(tmp_path).as_posix(): (
                path.read_bytes(),
                path.stat().st_mtime_ns,
            )
            for path in sorted(tmp_path.rglob("*"))
            if path.is_file()
        }

    before = snapshot_tree()
    preview = finalize_runtime_knowledge(
        replace(
            runtime,
            previous_manifest=committed.committed_manifest,
        ),
        dry_run=True,
    )

    assert preview.dry_run is True
    assert snapshot_tree() == before


def test_committed_bundle_identity_rejects_live_ledger_namespace_change(
    tmp_path: Path,
) -> None:
    runtime, _snapshot, _fixture = _runtime_input_case(
        tmp_path,
        inventory_complete=True,
    )
    committed = finalize_runtime_knowledge(
        replace(
            runtime,
            governance=GovernanceLedger.empty("kb_bundle_continuity"),
        )
    )
    loaded = load_governance(tmp_path)
    tampered = replace(loaded.ledger, bundle_id="kb_different_namespace")
    save_governance(
        tmp_path,
        tampered,
        expected_hash=loaded.content_hash,
    )
    tampered_bytes = (tmp_path / ".llm-wiki-governance.json").read_bytes()

    with pytest.raises(GovernanceError) as sync_error:
        sync_cmd._preflight_sync_governance(
            tmp_path,
            committed.committed_manifest,
        )
    assert sync_error.value.code == "governance-bundle-mismatch"

    with pytest.raises(GovernanceError) as runtime_error:
        finalize_runtime_knowledge(
            replace(
                runtime,
                previous_manifest=committed.committed_manifest,
            )
        )
    assert runtime_error.value.code == "governance-bundle-mismatch"
    assert (tmp_path / ".llm-wiki-governance.json").read_bytes() == tampered_bytes


def test_chunked_migration_defers_identity_commit_and_resumes_idempotently(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "alpha.py").write_text(
        "def alpha():\n    return 1\n",
        encoding="utf-8",
    )
    (project / "beta.py").write_text(
        "def beta():\n    return 2\n",
        encoding="utf-8",
    )
    wiki = project / "docs" / "llm_wiki"
    for directory in ("entities", "modules", "workflows", "infrastructure"):
        (wiki / directory).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text("# Old index\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Log\n", encoding="utf-8")
    (wiki / "modules" / "old_alpha.md").write_text(
        "# old alpha\n\n**Path:** `alpha.py`\n",
        encoding="utf-8",
    )
    (wiki / "modules" / "old_beta.md").write_text(
        "# old beta\n\n**Path:** `beta.py`\n",
        encoding="utf-8",
    )

    old_alpha = mcp_uri(PageKind.MODULES, "old_alpha")
    old_beta = mcp_uri(PageKind.MODULES, "old_beta")
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_chunked_migration"),
        (
            ConceptGovernanceReference(
                locator=old_alpha,
                concept_kind="source-module",
                natural_key=natural_key_for(
                    "source-module", "modules/old_alpha.md"
                ),
            ),
            ConceptGovernanceReference(
                locator=old_beta,
                concept_kind="source-module",
                natural_key=natural_key_for(
                    "source-module", "modules/old_beta.md"
                ),
            ),
        ),
    )
    save_governance(wiki, ledger, expected_hash=None)
    initial_bytes = (wiki / ".llm-wiki-governance.json").read_bytes()
    uid_by_locator = {
        allocation.locator: uid for uid, allocation in ledger.concepts.items()
    }
    monkeypatch.chdir(project)
    args = SimpleNamespace(
        src_dir=".",
        wiki_dir=str(wiki),
        dry_run=False,
        chunk_size=1,
        chunk=None,
        plan_chunks=False,
    )
    preview_args = SimpleNamespace(**vars(args))
    preview_args.dry_run = True

    migrate_cmd.run(preview_args)

    assert (wiki / ".llm-wiki-governance.json").read_bytes() == initial_bytes
    assert not (wiki / migrate_cmd.MIGRATION_PROGRESS_FILENAME).exists()

    migrate_cmd.run(args)

    assert (wiki / ".llm-wiki-governance.json").read_bytes() == initial_bytes
    assert (wiki / migrate_cmd.MIGRATION_PROGRESS_FILENAME).is_file()

    migrate_cmd.run(args)

    completed_bytes = (wiki / ".llm-wiki-governance.json").read_bytes()
    completed = load_governance(wiki).ledger
    assert completed.concepts[uid_by_locator[old_alpha]].locator == mcp_uri(
        PageKind.MODULES, "alpha"
    )
    assert completed.concepts[uid_by_locator[old_beta]].locator == mcp_uri(
        PageKind.MODULES, "beta"
    )
    assert not (wiki / migrate_cmd.MIGRATION_PROGRESS_FILENAME).exists()

    migrate_cmd.run(args)

    assert (wiki / ".llm-wiki-governance.json").read_bytes() == completed_bytes
    output = capsys.readouterr().out
    assert "Identity changes commit with the final artifact refresh" in output


def test_governed_collision_sync_preserves_identity_and_recovers_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project = tmp_path / "project"
    original_source = project / "pkg_a" / "models.py"
    original_source.parent.mkdir(parents=True)
    original_source.write_text(
        "class User:\n"
        '    """An existing user."""\n'
        "    pass\n",
        encoding="utf-8",
    )
    wiki = project / "docs" / "llm_wiki"
    monkeypatch.chdir(project)
    parser = cli._build_parser()

    bootstrap_cmd.run(
        parser.parse_args(
            [
                "bootstrap",
                "--src-dir",
                ".",
                "--wiki-dir",
                str(wiki),
                "--skip-workflows",
                "--skip-flows",
                "--skip-dependencies",
            ]
        )
    )
    knowledge_cmd.run(
        parser.parse_args(
            [
                "knowledge",
                "init",
                "--wiki-dir",
                str(wiki),
                "--bundle-id",
                "kb_governed_collision_recovery",
            ]
        )
    )

    old_entity_locator = mcp_uri(PageKind.ENTITIES, "User")
    old_module_locator = mcp_uri(PageKind.MODULES, "models")
    initialized = load_governance(wiki).ledger
    uid_by_old_locator = {
        allocation.locator: uid
        for uid, allocation in initialized.concepts.items()
    }
    old_entity_uid = uid_by_old_locator[old_entity_locator]
    old_module_uid = uid_by_old_locator[old_module_locator]
    old_entity_natural_key = initialized.concepts[
        old_entity_uid
    ].natural_key
    old_module_natural_key = initialized.concepts[
        old_module_uid
    ].natural_key

    colliding_source = project / "pkg_b" / "models.py"
    colliding_source.parent.mkdir()
    colliding_source.write_text(
        "class User:\n"
        '    """A second user with the same display name."""\n'
        "    pass\n",
        encoding="utf-8",
    )
    sync_args = parser.parse_args(
        [
            "sync",
            "--src-dir",
            ".",
            "--wiki-dir",
            str(wiki),
        ]
    )
    sync_cmd.run(sync_args)

    new_entity_locator = mcp_uri(
        PageKind.ENTITIES,
        "pkg_a_models_User",
    )
    new_module_locator = mcp_uri(PageKind.MODULES, "pkg_a_models")
    synchronized = load_governance(wiki).ledger
    assert synchronized.concepts[old_entity_uid].locator == new_entity_locator
    assert synchronized.concepts[old_module_uid].locator == new_module_locator
    assert {
        (alias.uid, alias.alias_type, alias.value)
        for alias in synchronized.aliases.values()
    }.issuperset(
        {
            (old_entity_uid, ALIAS_LOCATOR, old_entity_locator),
            (
                old_entity_uid,
                ALIAS_NATURAL_KEY,
                old_entity_natural_key,
            ),
            (old_module_uid, ALIAS_LOCATOR, old_module_locator),
            (
                old_module_uid,
                ALIAS_NATURAL_KEY,
                old_module_natural_key,
            ),
        }
    )

    synchronized_hash = synchronized.content_hash()
    manifest = SyncManifest.load(wiki)
    assert manifest.artifact_hashes is not None
    assert manifest.artifact_hashes.governance_hash == synchronized_hash
    loaded = load_knowledge_state(wiki)
    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.knowledge is not None
    projection = validate_governance_projection(
        loaded.knowledge,
        ledger=synchronized,
    )
    assert projection is not None
    assert projection["input_hash"] == synchronized_hash

    governance_path = wiki / ".llm-wiki-governance.json"
    exact_ledger_bytes = governance_path.read_bytes()
    governance_path.unlink()
    original_source.write_text(
        "class User:\n"
        '    """An existing user with a repaired field."""\n'
        "    enabled: bool = True\n",
        encoding="utf-8",
    )

    def wiki_files() -> dict[str, bytes]:
        return {
            path.relative_to(wiki).as_posix(): path.read_bytes()
            for path in sorted(wiki.rglob("*"))
            if path.is_file()
        }

    before_failed_sync = wiki_files()
    with pytest.raises(SystemExit) as missing_ledger:
        sync_cmd.run(sync_args)
    assert missing_ledger.value.code == 2
    assert wiki_files() == before_failed_sync

    governance_path.write_bytes(exact_ledger_bytes)
    damaged_artifact = wiki / KNOWLEDGE_INDEX_FILENAME
    damaged_artifact.unlink()
    sync_cmd.run(sync_args)

    repaired = load_governance(wiki).ledger
    assert repaired.concepts == synchronized.concepts
    assert repaired.aliases == synchronized.aliases
    assert repaired.content_hash() == synchronized_hash
    assert governance_path.read_bytes() == exact_ledger_bytes
    assert damaged_artifact.is_file()

    repaired_manifest = SyncManifest.load(wiki)
    assert repaired_manifest.artifact_hashes is not None
    assert repaired_manifest.artifact_hashes.governance_hash == synchronized_hash
    repaired_state = load_knowledge_state(wiki)
    assert repaired_state.status is KnowledgeLoadState.VALID
    assert repaired_state.knowledge is not None
    validate_governance_projection(
        repaired_state.knowledge,
        ledger=repaired,
    )
