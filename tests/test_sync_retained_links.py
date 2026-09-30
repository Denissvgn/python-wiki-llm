"""Generated links in retained pages follow verified page owners."""

import pytest

from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import sync_transition_execution as execution
from llm_wiki_cli.services import sync_transitions
from llm_wiki_cli.services.io import read_md
from llm_wiki_cli.services.sync_manifest import SyncManifest
from llm_wiki_cli.services.sync_retained_links import repair_retained_page_links
from llm_wiki_cli.services.validation import portable_path_key
from llm_wiki_cli.services.wiki_surface import PageKind
from tests.test_sync_analysis import _inventory, _manifest
from tests.test_sync_page_transitions import _bootstrap_project, _draft_source, _sync
from tests.test_sync_transition_execution import _assert_originals
from tests.test_sync_transitions import _plan, _snapshot, _wiki


def _moves(**names):
    return {portable_path_key(f"entities/{old}.md"): f"entities/{new}.md" for old, new in names.items()}


def test_mixed_table_repair_preserves_authored_cells_and_exact_spacing():
    original = (
        "# Retired\n\n**Path:** `pkg/retired.py`\n\n"
        "## Description\nAuthored [A](../entities/A.md).\n\n"
        "## Classes\n"
        "| Class | Line | Description |\n|---|---|---|\n"
        "|  [A](<../entities/A.md#anchor> \"title ../entities/A.md\")  |  1  | Authored [A](../entities/A.md) \\| café |\n"
        "| [A](../entities/A.md) | 2 | Second distinct description. |\n\n"
        "Custom prose [A](../entities/A.md).\n\n"
        "## classes\n| Class | Description |\n|---|---|\n| [A](../entities/A.md) | Duplicate section. |\n\n"
        "## Custom\nAuthored [A](../entities/A.md).\n"
    )
    expected = original.replace(
        "[A](<../entities/A.md#anchor>", "[A](<../entities/NewA.md#anchor>"
    ).replace("| [A](../entities/A.md) | 2", "| [A](../entities/NewA.md) | 2")
    assert repair_retained_page_links(original, "modules/retired.md", PageKind.MODULES, _moves(A="NewA")) == expected


def test_generated_sections_repair_mermaid_and_links_but_leave_examples_and_external_urls():
    original = (
        "# Retired\n\n## Local dependency map\n"
        "[A ../entities/A.md](../entities/A.md#details 'keep this title')\n"
        "[A](https://example.com/entities/A.md) ![A](../entities/A.md) [local](#details)\n"
        "`[A](../entities/A.md)`\n"
        "    [A](../entities/A.md)\n"
        "\\[A](../entities/A.md)\n"
        "```python\n[A](../entities/A.md)\n```\n"
        "```mermaid\ngraph TD\n  click a \"../entities/A.md#details\" \"tip ../entities/A.md\"\n```\n"
        "### Nested generated structure\n[A](../entities/A.md)\n"
        "## Custom\n```mermaid\nclick a \"../entities/A.md\"\n```\n"
    )
    expected = original.replace(
        "](../entities/A.md#details 'keep", "](../entities/NewA.md#details 'keep"
    ).replace('click a "../entities/A.md#details"', 'click a "../entities/NewA.md#details"').replace(
        "### Nested generated structure\n[A](../entities/A.md)",
        "### Nested generated structure\n[A](../entities/NewA.md)",
    )
    assert repair_retained_page_links(original, "modules/retired.md", PageKind.MODULES, _moves(A="NewA")) == expected


@pytest.mark.parametrize("final_b", ["A", "C"])
def test_swaps_and_chains_are_applied_once_to_original_links(final_b):
    text = "# Retired\n\n## Relationships\n[A](../entities/A.md) [B](../entities/B.md)\n"
    expected = f"# Retired\n\n## Relationships\n[A](../entities/B.md) [B](../entities/{final_b}.md)\n"
    assert repair_retained_page_links(text, "entities/Retired.md", PageKind.ENTITIES, _moves(A="B", B=final_b)) == expected


def test_lexical_resolution_and_casing_do_not_require_the_old_path_to_exist():
    text = "# Retired\n\n## Relationships\n[A](../entities/./a.md#part) [module](../modules/old.md)\n"
    moves = {**_moves(A="NewA"), "modules/old.md": "modules/new.md"}
    assert repair_retained_page_links(text, "entities/Retired.md", PageKind.ENTITIES, moves) == (
        "# Retired\n\n## Relationships\n[A](../entities/NewA.md#part) [module](../modules/new.md)\n"
    )


def test_mixed_entity_tables_preserve_description_links():
    text = "# Retired\n\n## Attributes\n| Name | Type | Description |\n|---|---|---|\n| a | [A](../entities/A.md) | See [A](../entities/A.md). |\n"
    assert repair_retained_page_links(text, "entities/Retired.md", PageKind.ENTITIES, _moves(A="NewA")) == text.replace(
        "| a | [A](../entities/A.md)", "| a | [A](../entities/NewA.md)"
    )


def _repair_case(tmp_path, scope="entity", cycle=False):
    old = _inventory(alpha=["A"], beta=["B"], retired=["Retired"])
    manifest = _manifest(old)
    wiki = _wiki(tmp_path, manifest)
    target = "../entities/A.md" if scope == "entity" else "../modules/alpha.md"
    (wiki / "modules/retired.md").write_text(
        f"# Retired\n\n## Classes\n| Class | Description |\n|---|---|\n| [A]({target}) | Authored café. |\n",
        encoding="utf-8",
    )
    (wiki / "entities/Retired.md").write_text(
        f"# Retired\n\n## Relationships\n[A]({target})\n", encoding="utf-8"
    )
    inventory = {path: data for path, data in old.items() if path != "pkg/retired.py"}
    kwargs = (
        {"entities": {("A", "pkg/alpha.py", 1): "B", ("B", "pkg/beta.py", 1): "A" if cycle else "C"}}
        if scope == "entity" else {"modules": {"pkg/alpha.py": "beta", "pkg/beta.py": "alpha" if cycle else "gamma"}}
    )
    return wiki, manifest, inventory, _plan(wiki, manifest, inventory, **kwargs)


@pytest.mark.parametrize("scope", ["entity", "module"])
@pytest.mark.parametrize("cycle", [False, True])
def test_retained_repairs_are_backed_up_before_any_move(tmp_path, monkeypatch, scope, cycle):
    wiki, _, _, plan = _repair_case(tmp_path, scope, cycle)
    before = _snapshot(wiki)
    assert {repair.path for repair in plan.retained_page_repairs} == {"modules/retired.md", "entities/Retired.md"}
    real_unlink = execution.unlink_guarded_bytes

    def unlink(path, **kwargs):
        _assert_originals(wiki, before)
        return real_unlink(path, **kwargs)

    monkeypatch.setattr(execution, "unlink_guarded_bytes", unlink)
    with execution.PageTransitionExecution(wiki, plan) as session:
        session.apply(plan)
        for repair in plan.retained_page_repairs:
            assert session.write(repair.path, repair.text) == "updated"
        _assert_originals(wiki, before)
    assert not list(wiki.glob(f"{execution.RECOVERY_PREFIX}*"))
    expected = "../entities/B.md" if scope == "entity" else "../modules/beta.md"
    assert expected in read_md(wiki / "modules/retired.md")
    assert "Authored café." in read_md(wiki / "modules/retired.md")


def test_changed_retained_page_aborts_before_staging(tmp_path):
    wiki, _, _, plan = _repair_case(tmp_path)
    (wiki / "modules/retired.md").write_text("Concurrent author edit.\n", encoding="utf-8")
    before = _snapshot(wiki)
    with pytest.raises(sync_transitions.PageTransitionError, match="changed before application"):
        with execution.PageTransitionExecution(wiki, plan) as session:
            session.apply(plan)
    assert _snapshot(wiki) == before
    assert not list(wiki.glob(f"{execution.RECOVERY_PREFIX}*"))


def test_retained_repairs_have_recovery_even_when_the_rename_source_is_missing(tmp_path):
    wiki, manifest, inventory, _ = _repair_case(tmp_path)
    (wiki / "entities/A.md").unlink()
    plan = _plan(wiki, manifest, inventory, entities={
        ("A", "pkg/alpha.py", 1): "NewA", ("B", "pkg/beta.py", 1): "B",
    })
    assert not plan.staged_moves and plan.retained_page_repairs
    before = _snapshot(wiki)
    with execution.PageTransitionExecution(wiki, plan) as session:
        session.apply(plan)
        _assert_originals(wiki, before)
        for repair in plan.retained_page_repairs:
            session.write(repair.path, repair.text)
    assert not list(wiki.glob(f"{execution.RECOVERY_PREFIX}*"))


def test_recorded_and_actual_casing_aliases_share_the_verified_destination(tmp_path):
    wiki, manifest, inventory, _ = _repair_case(tmp_path)
    page = wiki / "entities/A.md"
    page.rename(wiki / "entities/staging.md")
    (wiki / "entities/staging.md").rename(wiki / "entities/a.md")
    plan = _plan(wiki, manifest, inventory, entities={
        ("A", "pkg/alpha.py", 1): "NewA", ("B", "pkg/beta.py", 1): "B",
    })
    assert plan.staged_moves[0].source_path == "entities/a.md"
    assert all("../entities/NewA.md" in repair.text for repair in plan.retained_page_repairs)


def test_deprecation_cannot_overwrite_an_author_edit_after_link_repair(tmp_path):
    wiki, _, _, plan = _repair_case(tmp_path)
    before = _snapshot(wiki)
    with pytest.raises(sync_transitions.PageTransitionError, match="changed during application"):
        with execution.PageTransitionExecution(wiki, plan) as session:
            session.apply(plan)
            for repair in plan.retained_page_repairs:
                session.write(repair.path, repair.text)
            page = wiki / "modules/retired.md"
            page.write_text("Concurrent author edit.\n", encoding="utf-8")
            sync_cmd._deprecate_existing_page(page, sync_cmd.SyncResult(), "module", "retired", execution=session)
    assert read_md(wiki / "modules/retired.md") == "Concurrent author edit.\n"
    _assert_originals(wiki, before)


@pytest.mark.parametrize("failure", ["repair-write", "concurrent-edit", "metadata"])
def test_retained_originals_survive_application_failures(tmp_path, monkeypatch, failure):
    wiki, _, _, plan = _repair_case(tmp_path)
    before = _snapshot(wiki)
    real_write = execution.atomic_write_guarded_bytes

    def write(path, data, **kwargs):
        if failure == "repair-write" and path.name == "retired.md":
            raise OSError("Injected retained repair failure")
        return real_write(path, data, **kwargs)

    monkeypatch.setattr(execution, "atomic_write_guarded_bytes", write)
    with pytest.raises((sync_transitions.PageTransitionError, OSError)):
        with execution.PageTransitionExecution(wiki, plan) as session:
            session.apply(plan)
            if failure == "concurrent-edit":
                (wiki / "modules/retired.md").write_text("Concurrent author edit.\n", encoding="utf-8")
            for repair in plan.retained_page_repairs:
                session.write(repair.path, repair.text)
            if failure == "metadata":
                raise OSError("Injected metadata failure")
    _assert_originals(wiki, before)
    if failure == "concurrent-edit":
        assert read_md(wiki / "modules/retired.md") == "Concurrent author edit.\n"
    with pytest.raises(sync_transitions.PageTransitionError, match="Unresolved"):
        execution.assert_no_pending_page_moves(wiki)


@pytest.mark.parametrize("kind", ["directory", "symlink"])
def test_nonregular_retained_page_is_rejected_before_any_write(tmp_path, kind):
    wiki, manifest, inventory, _ = _repair_case(tmp_path)
    page = wiki / "modules/retired.md"
    page.unlink()
    if kind == "directory":
        page.mkdir()
    else:
        external = tmp_path / "external.md"
        external.write_text("External notes.\n", encoding="utf-8")
        page.symlink_to(external)
    before = _snapshot(wiki)
    with pytest.raises(sync_transitions.PageTransitionError, match="not a regular file"):
        _plan(wiki, manifest, inventory, entities={("A", "pkg/alpha.py", 1): "NewA", ("B", "pkg/beta.py", 1): "B"})
    assert _snapshot(wiki) == before
    assert not list(wiki.glob(f"{execution.RECOVERY_PREFIX}*"))


def test_deleted_and_unmanaged_pages_are_excluded_from_repairs(tmp_path):
    wiki, manifest, inventory, _ = _repair_case(tmp_path)
    (wiki / "modules/manual.md").write_text("## Imports\n[A](../entities/A.md)\n", encoding="utf-8")
    plan = _plan(
        wiki, manifest, inventory,
        entities={("A", "pkg/alpha.py", 1): "NewA", ("B", "pkg/beta.py", 1): "B"},
        deleted_source_paths=frozenset({"pkg/retired.py"}),
    )
    assert plan.retained_page_repairs == ()


def test_plan_without_path_changes_does_not_read_retained_content(tmp_path, monkeypatch):
    wiki, manifest, inventory, _ = _repair_case(tmp_path)

    def forbid_reader(*args, **kwargs):
        pytest.fail("No-op page plan read retained content")

    monkeypatch.setattr(sync_transitions, "StorageReadSession", forbid_reader)
    assert _plan(wiki, manifest, inventory).retained_page_repairs == ()


def test_previously_retired_page_follows_a_later_collision_and_sync_converges(tmp_path, monkeypatch):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"alpha.py": _draft_source("Original.")})
    (project / "pkg/alpha.py").rename(project / "pkg/beta.py")
    _sync(wiki, force=True)
    old_manifest = SyncManifest.load(wiki)
    old_tombstone = old_manifest.tombstones["modules/alpha.md"]
    retired = wiki / "modules/alpha.md"
    retired.write_text(read_md(retired).replace("Original. |", "Authored retired description. |"), encoding="utf-8")
    retired.write_text(read_md(retired) + "\n## Custom\nKeep this prose.\n", encoding="utf-8")
    (project / "pkg/composer.py").write_text(_draft_source("Added."), encoding="utf-8")
    before = _snapshot(wiki)
    _sync(wiki, force=True, dry_run=True)
    assert _snapshot(wiki) == before
    _sync(wiki, force=True)
    text = read_md(retired)
    assert "../entities/beta_Draft.md" in text
    assert "../entities/Draft.md" not in text
    assert sync_cmd._DEPRECATION_HEADER in text
    assert "**Path:** `pkg/alpha.py`" in text
    assert "Authored retired description." in text and "Keep this prose." in text
    current = SyncManifest.load(wiki)
    assert current.tombstones["modules/alpha.md"].last_valid_basis == old_tombstone.last_valid_basis
    assert current.page_source_mappings["modules/alpha.md"].source_path == "pkg/alpha.py"
    stable = _snapshot(wiki)
    _sync(wiki)
    assert _snapshot(wiki) == stable


def test_command_metadata_failure_retains_historical_page_originals(tmp_path, monkeypatch):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"alpha.py": _draft_source("Original.")})
    (project / "pkg/alpha.py").rename(project / "pkg/beta.py")
    _sync(wiki, force=True)
    (project / "pkg/composer.py").write_text(_draft_source("Added."), encoding="utf-8")
    before = _snapshot(wiki)

    def fail_metadata(*args, **kwargs):
        raise OSError("Injected metadata failure")

    monkeypatch.setattr(sync_cmd, "finalize_runtime_knowledge", fail_metadata)
    with pytest.raises(OSError, match="metadata failure"):
        _sync(wiki, force=True)
    _, journal = _assert_originals(wiki, before)
    assert {page["source"] for page in journal["retained_pages"]} == {"modules/alpha.md"}
    assert (wiki / ".llm-wiki-manifest.json").read_bytes() == before[".llm-wiki-manifest.json"][0]
    with pytest.raises(SystemExit) as exc:
        _sync(wiki, force=True)
    assert exc.value.code == 2
