"""Repair absent managed source pages without inventing source changes."""

from __future__ import annotations

import os
import json
from pathlib import Path

import pytest

from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services.io import read_md
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.test_sync_page_transitions import (
    _assert_consistent,
    _assert_entity_page,
    _assert_module_page,
    _assert_page_mapping,
    _author_description,
    _bootstrap_project,
    _draft_source,
    _require_page,
    _sync,
)


@pytest.mark.parametrize("page_kind", ["entity", "module"])
@pytest.mark.parametrize("mode", ["ordinary", "no-cache", "rebuild-cache", "force-rebuild-cache", "mtime-only"])
def test_sync_restores_missing_page_without_source_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, page_kind: str, mode: str
) -> None:
    original_doc = "A mail draft."
    keeper_doc = "An unrelated keeper."
    keeper_authored = "HAND-WRITTEN: preserve this unrelated keeper."
    project, wiki_dir = _bootstrap_project(
        tmp_path,
        monkeypatch,
        {
            "model.py": _draft_source(original_doc),
            "keeper.py": _draft_source(keeper_doc, name="Keeper"),
        },
    )
    _author_description(wiki_dir / "entities/Keeper.md", keeper_doc, keeper_authored)
    # Establish a healthy warm sync before deletion, independent of either rename.
    _sync(wiki_dir)
    _assert_consistent(wiki_dir)
    source_path = project / "pkg/model.py"
    source_bytes = {
        path: path.read_bytes() for path in (project / "pkg").glob("*.py")
    }
    source_hash = SyncManifest.load(wiki_dir).sources["pkg/model.py"]["hash"]
    relative_path = "entities/Draft.md" if page_kind == "entity" else "modules/model.md"
    _assert_page_mapping(
        wiki_dir,
        relative_path,
        "pkg/model.py",
        entity_name="Draft" if page_kind == "entity" else None,
    )
    target = wiki_dir / relative_path
    assert target.is_file()
    expected_content = read_md(target)
    target.unlink()
    surviving_pages = {
        path: path.read_bytes()
        for directory in ("entities", "modules")
        for path in (wiki_dir / directory).glob("*.md")
    }
    if mode == "mtime-only":
        before = source_path.stat()
        os.utime(
            source_path,
            ns=(before.st_atime_ns, before.st_mtime_ns + 2_000_000_000),
        )
        assert source_path.stat().st_mtime_ns != before.st_mtime_ns

    options = {
        "ordinary": {}, "mtime-only": {}, "no-cache": {"no_cache": True},
        "rebuild-cache": {"rebuild_cache": True},
        "force-rebuild-cache": {"force": True, "rebuild_cache": True},
    }[mode]
    _sync(wiki_dir, **options)

    for path, content in source_bytes.items():
        assert path.read_bytes() == content, f"Source changed: {path.name}"
    assert SyncManifest.load(wiki_dir).sources["pkg/model.py"]["hash"] == source_hash
    for path, content in surviving_pages.items():
        assert path.read_bytes() == content, f"Surviving page changed: {path.name}"
    _assert_entity_page(
        wiki_dir, "Keeper", "pkg/keeper.py", keeper_authored, entity_name="Keeper"
    )
    assert _require_page(wiki_dir, relative_path) == expected_content
    _assert_entity_page(wiki_dir, "Draft", "pkg/model.py", original_doc)
    _assert_module_page(wiki_dir, "model", "pkg/model.py")
    _assert_consistent(wiki_dir)
    stable = {
        path.relative_to(wiki_dir): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in wiki_dir.rglob("*") if path.is_file()
    }
    _sync(wiki_dir)
    assert {
        path.relative_to(wiki_dir): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in wiki_dir.rglob("*") if path.is_file()
    } == stable


def _snapshot(root):
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()
    }


@pytest.mark.parametrize("page_kind", ["entity", "module"])
def test_repairs_are_output_work_and_only_the_missing_page_is_rendered(tmp_path, monkeypatch, capsys, page_kind):
    source = _draft_source("Draft generated.") + "\n\n" + _draft_source("Keeper generated.", name="Keeper")
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": source})
    _author_description(wiki / "entities/Keeper.md", "Keeper generated.", "AUTHORED: keep this exactly.")
    _sync(wiki)
    relative = "entities/Draft.md" if page_kind == "entity" else "modules/model.md"
    (wiki / relative).unlink()
    before = _snapshot(wiki)
    receipts = []
    rendered = []
    real_entity = sync_cmd._apply_entity_page
    real_module = sync_cmd._apply_module_page
    real_finalize = sync_cmd.finalize_runtime_knowledge
    real_apply = sync_cmd._apply_prepared_sync

    def entity(ctx, diff, result, filepath, cls, mod_page, entity_page):
        rendered.append(f"entities/{entity_page}.md")
        return real_entity(ctx, diff, result, filepath, cls, mod_page, entity_page)

    def module(ctx, diff, result, filepath, data, page, *args):
        rendered.append(f"modules/{page}.md")
        return real_module(ctx, diff, result, filepath, data, page, *args)

    def finalize(inputs, **kwargs):
        receipts.append(inputs.regenerated_evidence_page_paths)
        return real_finalize(inputs, **kwargs)

    def apply(options, prepared):
        assert not prepared.diff.has_changes
        assert prepared.diff.unchanged_files == ["pkg/model.py"]
        assert prepared.application_diff.unchanged_files == prepared.diff.unchanged_files
        assert prepared.application_diff.changed_files == []
        assert set(prepared.application_diff.missing_pages) == {relative}
        return real_apply(options, prepared)

    def forbid_reuse(*args, **kwargs):
        pytest.fail("Repair was allowed to reach the unchanged reuse path")

    monkeypatch.setattr(sync_cmd, "_apply_entity_page", entity)
    monkeypatch.setattr(sync_cmd, "_apply_module_page", module)
    monkeypatch.setattr(sync_cmd, "_apply_prepared_sync", apply)
    monkeypatch.setattr(sync_cmd, "finalize_runtime_knowledge", finalize)
    monkeypatch.setattr(sync_cmd, "_try_sync_knowledge_reuse", forbid_reuse)
    capsys.readouterr()
    _sync(wiki)
    assert rendered == [relative]
    assert receipts == [frozenset({relative})]
    assert "Sync complete: 1 created" in capsys.readouterr().out
    for path, value in before.items():
        if path.startswith(("entities/", "modules/")):
            assert ((wiki / path).read_bytes(), (wiki / path).stat().st_mtime_ns) == value
    assert (project / "pkg/model.py").read_text() == source
    _assert_consistent(wiki)


def test_dry_run_describes_repairs_without_modifying_the_wiki(tmp_path, monkeypatch, capsys):
    _, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": _draft_source("Generated.")})
    (wiki / "entities/Draft.md").unlink()
    before = _snapshot(wiki)
    capsys.readouterr()
    _sync(wiki, dry_run=True)
    output = capsys.readouterr().out
    assert "source files: 0 new, 0 changed" in output
    assert "missing source pages: 1 repair" in output
    assert "REPAIR entities/Draft.md" in output
    assert _snapshot(wiki) == before
    _sync(wiki)
    _assert_consistent(wiki)


def test_all_missing_modules_retain_the_enabled_dependency_sections(tmp_path, monkeypatch):
    _, wiki = _bootstrap_project(
        tmp_path, monkeypatch,
        {"model.py": _draft_source("Generated."), "consumer.py": "from .model import Draft\n\nclass Consumer:\n    draft: Draft\n"},
        skip_dependencies=False,
    )
    _sync(wiki)
    expected = {path.name: path.read_bytes() for path in (wiki / "modules").glob("*.md")}
    assert expected and all(b"## Local dependency map" in data for data in expected.values())
    entities = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in (wiki / "entities").glob("*.md")}
    for path in (wiki / "modules").glob("*.md"):
        path.unlink()
    _sync(wiki)
    assert {path.name: path.read_bytes() for path in (wiki / "modules").glob("*.md")} == expected
    assert {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in (wiki / "entities").glob("*.md")} == entities
    _assert_consistent(wiki)


def test_repair_of_three_way_collision_state_uses_the_private_owner(tmp_path, monkeypatch):
    _, wiki = _bootstrap_project(tmp_path, monkeypatch, {
        "model.py": _draft_source("Original model."),
        "composer.py": _draft_source("Composer."),
        "fakes.py": _draft_source("Private twin.", name="_Draft"),
    })
    _sync(wiki)
    (wiki / "entities/Draft.md").unlink()
    _sync(wiki)
    _assert_entity_page(wiki, "Draft", "pkg/fakes.py", "Private twin.", entity_name="_Draft")
    _assert_entity_page(wiki, "model_Draft", "pkg/model.py", "Original model.")
    _assert_entity_page(wiki, "composer_Draft", "pkg/composer.py", "Composer.")
    _assert_consistent(wiki)


@pytest.mark.parametrize("state", ["missing-manifest", "invalid-source-hash"])
def test_manifest_seed_and_repair_remain_nonmutating_first_pass(tmp_path, monkeypatch, state):
    _, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": _draft_source("Generated.")})
    (wiki / "entities/Draft.md").unlink()
    if state == "missing-manifest":
        (wiki / ".llm-wiki-manifest.json").unlink()
    else:
        manifest = SyncManifest.load(wiki)
        manifest.sources["pkg/model.py"]["hash"] = ""
        manifest.save(wiki)
    before = {path.name: path.read_bytes() for path in (wiki / "modules").glob("*.md")}
    _sync(wiki)
    assert not (wiki / "entities/Draft.md").exists()
    assert {path.name: path.read_bytes() for path in (wiki / "modules").glob("*.md")} == before
    _sync(wiki)
    _assert_entity_page(wiki, "Draft", "pkg/model.py", "Generated.")


def test_source_selection_repairs_only_selected_live_pages(tmp_path, monkeypatch):
    from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION

    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {
        "model.py": _draft_source("Selected."),
        "excluded.py": _draft_source("Excluded.", name="Excluded"),
    })
    profile = project / ".llm-wiki/source-selection.json"
    profile.parent.mkdir(exist_ok=True)
    profile.write_text(json.dumps({
        "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
        "include": ["pkg/model.py"], "exclude": [],
    }), encoding="utf-8")
    (wiki / "entities/Draft.md").unlink()
    (wiki / "entities/Excluded.md").unlink()
    _sync(wiki, source_selection=profile.relative_to(project))
    _assert_entity_page(wiki, "Draft", "pkg/model.py", "Selected.")
    assert not (wiki / "entities/Excluded.md").exists()
    assert not (wiki / "modules/excluded.md").exists()
    assert set(SyncManifest.load(wiki).sources) == {"pkg/model.py"}
    stable = _snapshot(wiki)
    _sync(wiki, source_selection=profile.relative_to(project))
    assert _snapshot(wiki) == stable


def test_retired_and_unmanaged_pages_are_not_recreated(tmp_path, monkeypatch):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {
        "model.py": _draft_source("Live."),
        "retired.py": _draft_source("Old.", name="Retired"),
        "unsupported.custom": "class Unsupported: pass\n",
    })
    (project / "pkg/retired.py").unlink()
    _sync(wiki)
    assert "entities/Retired.md" in SyncManifest.load(wiki).tombstones
    for relative in ["entities/Retired.md", "modules/retired.md", "entities/Draft.md"]:
        (wiki / relative).unlink()
    guide = wiki / "guides/manual.md"
    guide.parent.mkdir(exist_ok=True)
    guide.write_text("# Manual notes\n", encoding="utf-8")
    _sync(wiki)
    guide.unlink()
    (wiki / "entities/Draft.md").unlink()
    _sync(wiki)
    _assert_entity_page(wiki, "Draft", "pkg/model.py", "Live.")
    for relative in ["entities/Retired.md", "modules/retired.md", "entities/Unsupported.md", "modules/unsupported.md", "guides/manual.md"]:
        assert not (wiki / relative).exists()
    _sync(wiki)
    assert not (wiki / "entities/Retired.md").exists()


def test_surface_initialization_defers_core_page_repairs(tmp_path, monkeypatch):
    _, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": _draft_source("Generated.")})
    (wiki / "entities/Draft.md").unlink()
    _sync(wiki, initialize_surfaces=[("dependencies",)])
    assert not (wiki / "entities/Draft.md").exists()
    _sync(wiki)
    _assert_entity_page(wiki, "Draft", "pkg/model.py", "Generated.")


@pytest.mark.parametrize("sharded", [False, True], ids=["inline", "sharded"])
def test_repair_preserves_governance_identity_and_storage_layout(tmp_path, monkeypatch, sharded):
    from llm_wiki_cli import cli
    from llm_wiki_cli.commands import knowledge_cmd
    from llm_wiki_cli.services.knowledge_governance import load_governance
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState

    _, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": _draft_source("Generated.")})
    if sharded:
        _sync(wiki, knowledge_format="sharded-v2")
    knowledge_cmd.run(cli._build_parser().parse_args([
        "knowledge", "init", "--wiki-dir", str(wiki), "--bundle-id", "kb_missing_page_repair",
    ]))
    _sync(wiki)
    ledger_before = load_governance(wiki).content
    version_before = SyncManifest.load(wiki).storage_version
    (wiki / "entities/Draft.md").unlink()
    _sync(wiki)
    assert load_governance(wiki).content == ledger_before
    assert SyncManifest.load(wiki).storage_version == version_before
    assert load_knowledge_state(wiki).status is KnowledgeLoadState.VALID
    _assert_entity_page(wiki, "Draft", "pkg/model.py", "Generated.")
    _assert_consistent(wiki)


@pytest.mark.parametrize("page_kind", ["entity", "module"])
def test_missing_page_directory_can_be_recreated(tmp_path, monkeypatch, page_kind):
    _, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": _draft_source("Generated.")})
    parent = wiki / ("entities" if page_kind == "entity" else "modules")
    for path in parent.iterdir():
        path.unlink()
    parent.rmdir()
    _sync(wiki)
    _assert_consistent(wiki)


def test_a_nonregular_expected_page_is_not_treated_as_absent(tmp_path, monkeypatch, capsys):
    _, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": _draft_source("Generated.")})
    target = wiki / "entities/Draft.md"
    target.unlink()
    target.mkdir()
    (target / "keep.txt").write_text("Unrelated content.\n", encoding="utf-8")
    before = _snapshot(wiki)
    capsys.readouterr()
    with pytest.raises(SystemExit) as exc:
        _sync(wiki)
    assert exc.value.code == 2
    assert "not a regular file" in capsys.readouterr().err
    assert _snapshot(wiki) == before
