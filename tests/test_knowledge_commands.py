"""Command integration coverage for managed knowledge artifacts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import textwrap
import types
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services.knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    CommitStage,
)
from llm_wiki_cli.services.knowledge_envelope import (
    collect_git_repository_evidence,
)
from llm_wiki_cli.services.contracts import (
    SECTION_OWNERSHIP_EXTENSION_KEY,
    TYPED_GRAPH_EXTENSION_KEY,
)
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeMismatchPolicy,
    KnowledgeStateLoadError,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_governance import GOVERNANCE_FILENAME
from llm_wiki_cli.services.knowledge_model import (
    KnowledgeLoadState,
    RelationshipRecord,
    WorkingTreeState,
)
from llm_wiki_cli.services.knowledge_orchestration import (
    RUNTIME_GENERATION_INPUT_KEY,
    build_runtime_knowledge_plan,
)
from llm_wiki_cli.services.sync_manifest import (
    MANIFEST_FILENAME,
    MANIFEST_REPAIR_UNAVAILABLE,
    MANIFEST_STATE_UNAVAILABLE,
    SyncManifest,
)
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME


# Golden bytes were captured from the v1.4.0 release:
# 76bfc0b35cbca12317f9a5c0182488d9cddbf72b.
_LEGACY_BOOTSTRAP_FIXTURE = (
    Path(__file__).parent / "fixtures" / "knowledge-bootstrap" / "legacy-bootstrap"
)
_LEGACY_BOOTSTRAP_DATE = date(2025, 1, 2)
_PROJECT_ROOT_TOKEN = b"<PROJECT_ROOT>"


def _write_canonical_utf8_lf(path: Path, text: str) -> None:
    payload = text.encode("utf-8")
    assert b"\r" not in payload
    path.write_bytes(payload)


def _bootstrap_args(project, wiki_dir):
    return types.SimpleNamespace(
        src_dir=str(project),
        wiki_dir=str(wiki_dir),
        overwrite=False,
        depth="full",
        skip_workflows=True,
    )


def _sync_args(project, wiki_dir, **kwargs):
    defaults = {
        "src_dir": str(project),
        "wiki_dir": str(wiki_dir),
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


@pytest.fixture
def knowledge_command_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(
        ["git", "init", str(project)],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(project),
            "config",
            "--local",
            "core.autocrlf",
            "false",
        ],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(project),
            "config",
            "--local",
            "core.eol",
            "lf",
        ],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(project), "config", "user.email", "test@example.com"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(project), "config", "user.name", "Test"],
        capture_output=True,
        check=True,
    )
    _write_canonical_utf8_lf(
        project / "pyproject.toml",
        '[project]\nname = "sample"\nversion = "0.1.0"\n',
    )
    _write_canonical_utf8_lf(
        project / "models.py",
        textwrap.dedent(
            """\
            class User:
                \"\"\"A system user.\"\"\"
                name: str = ""
                email: str = ""
            """
        ),
    )
    wiki_dir = project / "docs" / "llm_wiki"
    previous_cwd = os.getcwd()
    os.chdir(project)
    try:
        bootstrap_cmd.run(_bootstrap_args(project, wiki_dir))
        yield project, wiki_dir
    finally:
        os.chdir(previous_cwd)


def _artifact_bytes(wiki_dir):
    return {
        filename: (wiki_dir / filename).read_bytes()
        for filename in (
            SURFACE_INDEX_FILENAME,
            KNOWLEDGE_INDEX_FILENAME,
            MANIFEST_FILENAME,
        )
    }


def _markdown_tree_bytes(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*.md"))
    }


def _concepts_by_path(knowledge):
    return {concept.document.canonical_path: concept for concept in knowledge.concepts}


def _relationships_by_source(
    relationships: tuple[RelationshipRecord, ...],
):
    grouped = defaultdict(list)
    for relationship in relationships:
        grouped[relationship.source_locator].append(relationship)
    return {source: tuple(records) for source, records in grouped.items()}


def _relationship_topology(relationships):
    return Counter(
        (
            relationship.kind,
            relationship.source_locator,
            relationship.target.kind,
            relationship.target.value,
            relationship.target.target_class,
            relationship.resolution,
        )
        for relationship in relationships
    )


def _write_changed_source(project):
    _write_canonical_utf8_lf(
        project / "models.py",
        textwrap.dedent(
            """\
            class User:
                \"\"\"An updated user with a role.\"\"\"
                name: str = ""
                email: str = ""
                role: str = "viewer"
            """
        ),
    )


def _remove_manifest_source_hashes(wiki_dir):
    path = wiki_dir / MANIFEST_FILENAME
    payload = json.loads(path.read_text(encoding="utf-8"))
    for source in payload["sources"].values():
        source.pop("hash", None)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_bootstrap_commits_a_loader_valid_knowledge_state(
    knowledge_command_project,
    capsys,
):
    _project, wiki_dir = knowledge_command_project
    capsys.readouterr()

    loaded = load_knowledge_state(wiki_dir)

    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.surface is not None
    assert loaded.knowledge is not None
    assert loaded.manifest_basis is not None
    assert loaded.manifest_basis.artifact_hashes is not None
    assert loaded.issues == ()


def test_bootstrap_matches_v1_4_0_markdown_and_surface_v1_goldens(
    tmp_path,
    monkeypatch,
):
    """Lock bootstrap bytes from the v1.4.0 revision 76bfc0b."""

    project = tmp_path / "project"
    shutil.copytree(_LEGACY_BOOTSTRAP_FIXTURE / "source", project)
    wiki_dir = project / "wiki"
    expected_wiki = _LEGACY_BOOTSTRAP_FIXTURE / "wiki"

    class FrozenDate(date):
        @classmethod
        def today(cls):
            return _LEGACY_BOOTSTRAP_DATE

    monkeypatch.chdir(project)
    monkeypatch.setattr(bootstrap_cmd, "date", FrozenDate)
    source_snapshot = bootstrap_cmd.build_source_snapshot(project)
    bootstrap_cmd.run(_bootstrap_args(project, wiki_dir))

    expected_markdown = _markdown_tree_bytes(expected_wiki)
    assert set(expected_markdown) == {
        "dependencies.md",
        "entities/User.md",
        "index.md",
        "load-order.md",
        "log.md",
        "modules/models.md",
    }
    # Current bootstrap renders the same-root source with its portable label.
    assert expected_markdown["log.md"].count(_PROJECT_ROOT_TOKEN) == 1
    expected_markdown["log.md"] = expected_markdown["log.md"].replace(
        _PROJECT_ROOT_TOKEN,
        b".",
    )
    historical_log_header = (
        b"### feat: bootstrap wiki from existing codebase\n"
        b"- Source: `.`\n"
    )
    current_log_header = (
        "### Wiki bootstrap\n"
        "- Source: `.`\n"
        f"{bootstrap_cmd._source_snapshot_log_lines(source_snapshot)}"
    ).encode("utf-8")
    assert expected_markdown["log.md"].count(historical_log_header) == 1
    expected_markdown["log.md"] = expected_markdown["log.md"].replace(
        historical_log_header,
        current_log_header,
    )
    expected_markdown["log.md"] = expected_markdown["log.md"].replace(
        b"- User flows created:",
        b"- Entry-point flows created:",
    )
    expected_markdown["log.md"] = expected_markdown["log.md"].replace(
        b"- API contract pages created:",
        b"- HTTP API contract pages created:",
    )
    expected_markdown["index.md"] = expected_markdown["index.md"].replace(
        b"Use this landing page to choose the right wiki surface.",
        b"This page is an exhaustive reference inventory of the selected source. "
        b"Task-oriented guides are not yet available.",
    )
    expected_markdown["index.md"] = expected_markdown["index.md"].replace(
        b"| User flows |",
        b"| Entry-point flows |",
    )
    expected_markdown["index.md"] = expected_markdown["index.md"].replace(
        b"| API contracts |",
        b"| HTTP API contracts |",
    )
    semantic_starter_updates = {
        "dependencies.md": (
            b"_Document dynamic or conditional imports, intentional cycles, and "
            b"the rationale behind notable dependencies. Replace this placeholder._",
            b"This page reflects statically observed imports and declared "
            b"dependencies. Dynamic or conditional imports and runtime-loaded "
            b"integrations may not appear in the generated sections.",
        ),
        "load-order.md": (
            b"_Document required initialization order, lazy imports, and side "
            b"effects that must run before others. Replace this placeholder._",
            b"This page presents a static dependency projection. Lazy imports, "
            b"conditional initialization, and runtime side effects can change the "
            b"effective order.",
        ),
    }
    for path, (historical, current) in semantic_starter_updates.items():
        assert expected_markdown[path].count(historical) == 1
        expected_markdown[path] = expected_markdown[path].replace(
            historical,
            current,
        )
    assert all(b"\r" not in content for content in expected_markdown.values())
    assert _markdown_tree_bytes(wiki_dir) == expected_markdown

    expected_surface = (expected_wiki / SURFACE_INDEX_FILENAME).read_bytes()
    actual_surface = (wiki_dir / SURFACE_INDEX_FILENAME).read_bytes()
    assert b"\r" not in expected_surface
    assert json.loads(actual_surface)["schema_version"] == (
        "llm-wiki-surface-index/v1"
    )
    assert actual_surface == expected_surface
    assert {
        path.name
        for path in wiki_dir.iterdir()
        if path.is_file() and path.name.startswith(".")
    } == {
        SURFACE_INDEX_FILENAME,
        KNOWLEDGE_INDEX_FILENAME,
        MANIFEST_FILENAME,
    }
    assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID


def test_bootstrap_and_changed_source_sync_keep_governance_opt_in(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    governance = wiki_dir / GOVERNANCE_FILENAME
    assert not governance.exists()

    _write_changed_source(project)
    sync_cmd.run(_sync_args(project, wiki_dir))

    assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID
    assert not governance.exists()


def test_immediate_noop_sync_preserves_all_committed_artifact_bytes(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    before = _artifact_bytes(wiki_dir)
    before_manifest = SyncManifest.load(wiki_dir)
    assert before_manifest.generation_inputs[RUNTIME_GENERATION_INPUT_KEY] == {
        "data_flow_enabled": True,
        "dependency_graph_detail": "auto",
        "workflows_enabled": False,
    }

    sync_cmd.run(_sync_args(project, wiki_dir))

    assert _artifact_bytes(wiki_dir) == before
    assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID
    output = capsys.readouterr().out
    assert "Surface index: unchanged" in output
    assert "Knowledge index: unchanged" in output
    assert "Manifest: unchanged" in output


def test_bootstrap_rejection_preserves_evidence_and_sync_regenerates(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    module_path = wiki_dir / "modules" / "models.md"
    entity_path = wiki_dir / "entities" / "User.md"
    before_pages = (module_path.read_bytes(), entity_path.read_bytes())
    before_artifacts = _artifact_bytes(wiki_dir)
    before_manifest = SyncManifest.load(wiki_dir)
    _write_changed_source(project)

    with pytest.raises(SystemExit) as exc_info:
        bootstrap_cmd.run(_bootstrap_args(project, wiki_dir))

    assert exc_info.value.code == 2
    assert (module_path.read_bytes(), entity_path.read_bytes()) == before_pages
    assert _artifact_bytes(wiki_dir) == before_artifacts
    assert SyncManifest.load(wiki_dir) == before_manifest
    assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID
    output = capsys.readouterr().out
    assert "Bootstrap is first-use only" in output
    assert "llm-wiki sync" in output
    assert "llm-wiki migrate --dry-run" not in output

    sync_cmd.run(_sync_args(project, wiki_dir))

    assert (module_path.read_bytes(), entity_path.read_bytes()) != before_pages
    regenerated = SyncManifest.load(wiki_dir)
    assert "models.py" in regenerated.sources
    assert regenerated.evidence_baselines["modules/models.md"].is_known
    assert regenerated.evidence_baselines["entities/User.md"].is_known
    assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID


def test_bootstrap_and_sync_each_reuse_one_snapshot_and_inventory_extraction(
    knowledge_command_project,
    monkeypatch,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    fresh_wiki_dir = project / "docs" / "fresh_wiki"
    counts = Counter()
    real_bootstrap_snapshot = bootstrap_cmd.build_source_snapshot
    real_bootstrap_inventory = bootstrap_cmd.get_inventory_result

    def bootstrap_snapshot(*args, **kwargs):
        counts["bootstrap_snapshot"] += 1
        return real_bootstrap_snapshot(*args, **kwargs)

    def bootstrap_inventory(*args, **kwargs):
        counts["bootstrap_inventory"] += 1
        return real_bootstrap_inventory(*args, **kwargs)

    monkeypatch.setattr(
        bootstrap_cmd,
        "build_source_snapshot",
        bootstrap_snapshot,
    )
    monkeypatch.setattr(
        bootstrap_cmd,
        "get_inventory_result",
        bootstrap_inventory,
    )
    bootstrap_cmd.run(_bootstrap_args(project, fresh_wiki_dir))

    assert counts == Counter({"bootstrap_snapshot": 1, "bootstrap_inventory": 1})

    real_sync_snapshot = sync_cmd.build_source_snapshot
    real_sync_inventory = sync_cmd.get_inventory_result

    def sync_snapshot(*args, **kwargs):
        counts["sync_snapshot"] += 1
        return real_sync_snapshot(*args, **kwargs)

    def sync_inventory(*args, **kwargs):
        counts["sync_inventory"] += 1
        return real_sync_inventory(*args, **kwargs)

    monkeypatch.setattr(sync_cmd, "build_source_snapshot", sync_snapshot)
    monkeypatch.setattr(sync_cmd, "get_inventory_result", sync_inventory)
    sync_cmd.run(_sync_args(project, fresh_wiki_dir))

    assert counts == Counter(
        {
            "bootstrap_snapshot": 1,
            "bootstrap_inventory": 1,
            "sync_snapshot": 1,
            "sync_inventory": 1,
        }
    )


def test_noop_sync_is_stable_after_generated_artifacts_are_committed(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    subprocess.run(["git", "-C", str(project), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(project), "commit", "-m", "commit generated wiki"],
        capture_output=True,
        check=True,
    )

    sync_cmd.run(_sync_args(project, wiki_dir))
    after_first = _artifact_bytes(wiki_dir)
    capsys.readouterr()
    sync_cmd.run(_sync_args(project, wiki_dir))

    assert _artifact_bytes(wiki_dir) == after_first
    output = capsys.readouterr().out
    assert "Surface index: unchanged" in output
    assert "Knowledge index: unchanged" in output
    assert "Manifest: unchanged" in output


def test_changed_source_sync_commits_only_expected_modeled_changes(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    before = load_knowledge_state(wiki_dir)
    assert before.knowledge is not None
    _write_changed_source(project)

    sync_cmd.run(_sync_args(project, wiki_dir))

    after = load_knowledge_state(wiki_dir)
    assert after.status is KnowledgeLoadState.VALID
    assert after.knowledge is not None
    assert after.knowledge.schema_version == before.knowledge.schema_version
    modeled_extension_keys = {
        TYPED_GRAPH_EXTENSION_KEY,
        SECTION_OWNERSHIP_EXTENSION_KEY,
    }
    assert {
        key: value
        for key, value in after.knowledge.extensions.items()
        if key not in modeled_extension_keys
    } == {
        key: value
        for key, value in before.knowledge.extensions.items()
        if key not in modeled_extension_keys
    }
    assert modeled_extension_keys <= set(before.knowledge.extensions)
    assert modeled_extension_keys <= set(after.knowledge.extensions)
    assert all(
        after.knowledge.extensions[key] != before.knowledge.extensions[key]
        for key in modeled_extension_keys
    )
    assert after.knowledge.bundle.repository == before.knowledge.bundle.repository
    assert after.knowledge.bundle.producer == before.knowledge.bundle.producer
    assert after.knowledge.bundle.extensions == before.knowledge.bundle.extensions
    before_snapshot = before.knowledge.bundle.snapshot
    after_snapshot = after.knowledge.bundle.snapshot
    assert after_snapshot.source_snapshot_hash != before_snapshot.source_snapshot_hash
    assert after_snapshot.markdown_snapshot_hash != (
        before_snapshot.markdown_snapshot_hash
    )
    assert after_snapshot.surface_index_hash == before_snapshot.surface_index_hash
    assert after_snapshot.generation_options_hash == (
        before_snapshot.generation_options_hash
    )
    assert after_snapshot.extensions != before_snapshot.extensions
    before_concepts = _concepts_by_path(before.knowledge)
    after_concepts = _concepts_by_path(after.knowledge)
    assert set(after_concepts) == set(before_concepts)
    changed_concepts = {
        path
        for path in before_concepts
        if before_concepts[path] != after_concepts[path]
    }
    assert {"modules/models.md", "entities/User.md"} <= changed_concepts
    assert changed_concepts <= {
        "log.md",
        "modules/models.md",
        "entities/User.md",
    }

    assert _relationship_topology(after.knowledge.relationships) == (
        _relationship_topology(before.knowledge.relationships)
    )
    before_by_source = _relationships_by_source(before.knowledge.relationships)
    after_by_source = _relationships_by_source(after.knowledge.relationships)
    changed_relationship_sources = {
        source
        for source in before_by_source
        if before_by_source[source] != after_by_source[source]
    }
    assert changed_relationship_sources <= {
        "llm-wiki://modules/models",
        "llm-wiki://entities/User",
    }


def test_removed_source_sync_commits_valid_tombstones(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    previous = SyncManifest.load(wiki_dir)
    expected_basis = {
        page_path: baseline.basis
        for page_path, baseline in previous.evidence_baselines.items()
        if page_path in {"modules/models.md", "entities/User.md"}
    }
    assert set(expected_basis) == {"modules/models.md", "entities/User.md"}
    assert all(
        basis is not None and basis.is_known for basis in expected_basis.values()
    )
    (project / "models.py").unlink()

    sync_cmd.run(_sync_args(project, wiki_dir))

    loaded = load_knowledge_state(wiki_dir)
    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.knowledge is not None
    assert loaded.manifest_basis is not None
    for page_path, basis in expected_basis.items():
        assert basis is not None
        assert page_path not in loaded.manifest_basis.evidence_baselines
        tombstone = loaded.manifest_basis.tombstones[page_path]
        assert tombstone.reason == "source-missing"
        assert tombstone.last_valid_basis == basis
        concept = _concepts_by_path(loaded.knowledge)[page_path]
        assert concept.facets.structure.basis is not None
        assert concept.facets.structure.basis.source_content_hash == (
            basis.source_content_hash
        )


def test_manifest_repair_then_sync_regenerates_pages_and_known_evidence(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    entity_path = wiki_dir / "entities" / "User.md"
    before_entity = entity_path.read_bytes()
    _write_changed_source(project)
    _remove_manifest_source_hashes(wiki_dir)

    sync_cmd.run(_sync_args(project, wiki_dir))

    assert entity_path.read_bytes() == before_entity
    repaired = load_knowledge_state(wiki_dir)
    assert repaired.status is KnowledgeLoadState.VALID
    assert repaired.manifest_basis is not None
    assert all(
        not baseline.is_known and baseline.unknown_reason == MANIFEST_REPAIR_UNAVAILABLE
        for baseline in repaired.manifest_basis.evidence_baselines.values()
    )

    capsys.readouterr()
    sync_cmd.run(_sync_args(project, wiki_dir))

    assert entity_path.read_bytes() != before_entity
    loaded = load_knowledge_state(wiki_dir)
    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.manifest_basis is not None
    assert all(
        baseline.is_known
        for baseline in loaded.manifest_basis.evidence_baselines.values()
    )


def test_manifest_reseed_unknown_survives_following_noop_sync(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    before_pages = {
        path.relative_to(wiki_dir).as_posix(): path.read_bytes()
        for directory in ("modules", "entities")
        for path in (wiki_dir / directory).glob("*.md")
    }
    (wiki_dir / MANIFEST_FILENAME).unlink()

    sync_cmd.run(_sync_args(project, wiki_dir))

    seeded = load_knowledge_state(wiki_dir)
    assert seeded.status is KnowledgeLoadState.VALID
    assert seeded.manifest_basis is not None
    assert all(
        not baseline.is_known and baseline.unknown_reason == MANIFEST_STATE_UNAVAILABLE
        for baseline in seeded.manifest_basis.evidence_baselines.values()
    )
    first_artifacts = _artifact_bytes(wiki_dir)
    capsys.readouterr()

    sync_cmd.run(_sync_args(project, wiki_dir))

    loaded = load_knowledge_state(wiki_dir)
    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.manifest_basis is not None
    assert all(
        not baseline.is_known and baseline.unknown_reason == MANIFEST_STATE_UNAVAILABLE
        for baseline in loaded.manifest_basis.evidence_baselines.values()
    )
    assert _artifact_bytes(wiki_dir) == first_artifacts
    assert {
        path.relative_to(wiki_dir).as_posix(): path.read_bytes()
        for directory in ("modules", "entities")
        for path in (wiki_dir / directory).glob("*.md")
    } == before_pages


def test_bootstrap_overwrite_rejection_preserves_reseeded_unknown_evidence(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    (wiki_dir / MANIFEST_FILENAME).unlink()

    sync_cmd.run(_sync_args(project, wiki_dir))

    seeded = SyncManifest.load(wiki_dir)
    assert seeded.evidence_baselines
    assert all(not baseline.is_known for baseline in seeded.evidence_baselines.values())
    before = _artifact_bytes(wiki_dir)

    capsys.readouterr()
    args = _bootstrap_args(project, wiki_dir)
    args.overwrite = True
    with pytest.raises(SystemExit) as exc_info:
        bootstrap_cmd.run(args)

    assert exc_info.value.code == 2
    assert _artifact_bytes(wiki_dir) == before
    preserved = SyncManifest.load(wiki_dir)
    assert preserved.evidence_baselines
    assert all(
        not baseline.is_known for baseline in preserved.evidence_baselines.values()
    )
    assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID


def test_repair_with_new_concept_keeps_partial_wiki_valid_until_next_sync(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    (project / "models.py").write_text(
        "class User:\n    name: str = ''\n\nclass Admin:\n    role: str = 'admin'\n",
        encoding="utf-8",
    )
    _remove_manifest_source_hashes(wiki_dir)

    sync_cmd.run(_sync_args(project, wiki_dir))

    assert not (wiki_dir / "entities" / "Admin.md").exists()
    assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID
    capsys.readouterr()

    sync_cmd.run(_sync_args(project, wiki_dir))

    assert (wiki_dir / "entities" / "Admin.md").is_file()
    assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID


def test_repair_with_new_source_keeps_it_pending_until_next_sync(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    (project / "admin.py").write_text(
        "class Admin:\n    role: str = 'admin'\n",
        encoding="utf-8",
    )
    _remove_manifest_source_hashes(wiki_dir)

    sync_cmd.run(_sync_args(project, wiki_dir))

    assert not (wiki_dir / "modules" / "admin.md").exists()
    assert not (wiki_dir / "entities" / "Admin.md").exists()
    repaired = load_knowledge_state(wiki_dir)
    assert repaired.status is KnowledgeLoadState.VALID
    assert repaired.manifest_basis is not None
    assert "admin.py" not in repaired.manifest_basis.sources
    capsys.readouterr()

    sync_cmd.run(_sync_args(project, wiki_dir))

    assert (wiki_dir / "modules" / "admin.md").is_file()
    assert (wiki_dir / "entities" / "Admin.md").is_file()
    loaded = load_knowledge_state(wiki_dir)
    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.manifest_basis is not None
    assert "admin.py" in loaded.manifest_basis.sources


def test_normal_sync_dry_run_writes_nothing_and_reports_three_artifacts(
    knowledge_command_project,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    before = _artifact_bytes(wiki_dir)
    _write_changed_source(project)

    sync_cmd.run(_sync_args(project, wiki_dir, dry_run=True))

    assert _artifact_bytes(wiki_dir) == before
    output = capsys.readouterr().out
    assert "DRY-RUN: Surface index:" in output
    assert "DRY-RUN: Knowledge index:" in output
    assert "DRY-RUN: Manifest:" in output
    assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID


def test_clean_git_sync_dry_run_matches_apply_artifact_bytes(
    knowledge_command_project,
    monkeypatch,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    subprocess.run(["git", "-C", str(project), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(project), "commit", "-m", "commit generated wiki"],
        capture_output=True,
        check=True,
    )
    _write_changed_source(project)
    subprocess.run(["git", "-C", str(project), "add", "models.py"], check=True)
    subprocess.run(
        ["git", "-C", str(project), "commit", "-m", "change source"],
        capture_output=True,
        check=True,
    )
    assert (
        subprocess.run(
            ["git", "-C", str(project), "status", "--porcelain"],
            capture_output=True,
            check=True,
            text=True,
        ).stdout
        == ""
    )
    assert (
        collect_git_repository_evidence(project).working_tree
        is WorkingTreeState.CLEAN
    )

    captured = []
    real_finalize = sync_cmd.finalize_runtime_knowledge

    def capture_plan(inputs, *, dry_run=False, fault_injector=None):
        plan = build_runtime_knowledge_plan(inputs)
        captured.append(
            (
                dry_run,
                inputs.repository_evidence.working_tree,
                tuple(
                    (artifact.state, artifact.content)
                    for artifact in (
                        plan.surface_index,
                        plan.knowledge_index,
                        plan.manifest,
                    )
                ),
            )
        )
        return real_finalize(
            inputs,
            dry_run=dry_run,
            fault_injector=fault_injector,
        )

    monkeypatch.setattr(sync_cmd, "finalize_runtime_knowledge", capture_plan)

    sync_cmd.run(_sync_args(project, wiki_dir, dry_run=True))
    assert len(captured) == 1
    assert captured[0][0] is True
    assert captured[0][1] is WorkingTreeState.CLEAN
    capsys.readouterr()

    sync_cmd.run(_sync_args(project, wiki_dir))

    assert len(captured) == 2
    assert captured[1][0] is False
    assert captured[1][1] is WorkingTreeState.CLEAN
    assert captured[1][2] == captured[0][2]
    assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID


def test_command_commit_interruption_never_serves_mixed_knowledge(
    knowledge_command_project,
    monkeypatch,
    capsys,
):
    project, wiki_dir = knowledge_command_project
    capsys.readouterr()
    previous_manifest_bytes = (wiki_dir / MANIFEST_FILENAME).read_bytes()
    _write_changed_source(project)
    real_finalize = sync_cmd.finalize_runtime_knowledge

    def interrupt_after_knowledge(inputs, *, dry_run=False):
        def inject(stage):
            if stage is CommitStage.KNOWLEDGE_INDEX_WRITTEN:
                raise RuntimeError("injected command interruption")

        return real_finalize(
            inputs,
            dry_run=dry_run,
            fault_injector=inject,
        )

    monkeypatch.setattr(
        sync_cmd,
        "finalize_runtime_knowledge",
        interrupt_after_knowledge,
    )

    with pytest.raises(RuntimeError, match="injected command interruption"):
        sync_cmd.run(_sync_args(project, wiki_dir))

    assert (wiki_dir / MANIFEST_FILENAME).read_bytes() == previous_manifest_bytes
    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(wiki_dir)
    assert exc_info.value.status in {
        KnowledgeLoadState.INVALID,
        KnowledgeLoadState.MIXED_SNAPSHOT,
    }

    degraded = load_knowledge_state(
        wiki_dir,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )
    assert degraded.status is KnowledgeLoadState.DEGRADED
    assert degraded.underlying_status is exc_info.value.status
    assert degraded.surface is not None
    assert degraded.knowledge is None


def test_bootstrap_commit_interruption_never_serves_mixed_knowledge(
    knowledge_command_project,
    monkeypatch,
    capsys,
):
    project, _existing_wiki_dir = knowledge_command_project
    wiki_dir = project / "docs" / "interrupted_first_bootstrap"
    capsys.readouterr()
    real_finalize = bootstrap_cmd.finalize_runtime_knowledge

    def interrupt_after_knowledge(inputs, *, dry_run=False):
        def inject(stage):
            if stage is CommitStage.KNOWLEDGE_INDEX_WRITTEN:
                raise RuntimeError("injected bootstrap interruption")

        return real_finalize(
            inputs,
            dry_run=dry_run,
            fault_injector=inject,
        )

    monkeypatch.setattr(
        bootstrap_cmd,
        "finalize_runtime_knowledge",
        interrupt_after_knowledge,
    )

    with pytest.raises(RuntimeError, match="injected bootstrap interruption"):
        bootstrap_cmd.run(_bootstrap_args(project, wiki_dir))

    assert not (wiki_dir / MANIFEST_FILENAME).exists()
    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        load_knowledge_state(wiki_dir)
    assert exc_info.value.status in {
        KnowledgeLoadState.INVALID,
        KnowledgeLoadState.MIXED_SNAPSHOT,
    }

    degraded = load_knowledge_state(
        wiki_dir,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )
    assert degraded.status is KnowledgeLoadState.DEGRADED
    assert degraded.underlying_status is exc_info.value.status
    assert degraded.surface is not None
    assert degraded.knowledge is None
