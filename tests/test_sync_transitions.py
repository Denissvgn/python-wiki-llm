"""Read-only page transition plans and conservative legacy application gates."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from llm_wiki_cli.services.bootstrap_runtime import (
    build_entity_occurrence_page_map,
    build_module_page_map,
)
from llm_wiki_cli.services.sync_analysis import SyncDiff
from llm_wiki_cli.services.sync_transitions import (
    PageTransitionError,
    StagedRenamesRequired,
    plan_page_transitions,
)
from tests.test_sync_analysis import _inventory, _manifest


def _wiki(tmp_path, manifest):
    wiki = tmp_path / "wiki"
    for path, owner in manifest.page_source_mappings.items():
        target = wiki / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(repr(owner), encoding="utf-8")
    return wiki


def _snapshot(wiki):
    return {
        path.relative_to(wiki).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in wiki.rglob("*") if path.is_file()
    }


def _plan(wiki, manifest, inventory, *, modules=None, entities=None, **kwargs):
    module_pages = build_module_page_map(inventory) if modules is None else modules
    entity_pages = (
        build_entity_occurrence_page_map(inventory, module_pages)
        if entities is None else entities
    )
    return plan_page_transitions(
        wiki, manifest, inventory,
        module_page_map=module_pages,
        entity_occurrence_page_map=entity_pages,
        **kwargs,
    )


def test_plan_describes_every_live_page_without_writing_or_mutating_inputs(tmp_path):
    old = _inventory(alpha=["Draft"], beta=["Other"])
    manifest = _manifest(old)
    wiki = _wiki(tmp_path, manifest)
    current = _inventory(alpha=["Draft"], beta=["Other", "Added"], gamma=[])
    before = _snapshot(wiki)
    original = deepcopy((manifest, current))

    plan = _plan(wiki, manifest, current, refresh_sources=frozenset({"pkg/beta.py"}))

    assert {item.final_path: item.action for item in plan.transitions} == {
        "entities/Draft.md": "retain",
        "entities/Other.md": "refresh",
        "entities/Added.md": "create",
        "modules/alpha.md": "retain",
        "modules/beta.md": "refresh",
        "modules/gamma.md": "create",
    }
    assert plan.staged_moves == ()
    assert (manifest, current) == original
    assert _snapshot(wiki) == before
    with pytest.raises(FrozenInstanceError):
        setattr(plan, "transitions", ())


def test_three_way_collision_reserves_old_content_before_reusing_its_path(tmp_path):
    manifest = _manifest(_inventory(model=["Draft"]))
    wiki = _wiki(tmp_path, manifest)
    current = _inventory(composer=["Draft"], fakes=["_Draft"], model=["Draft"])
    plan = _plan(wiki, manifest, current)
    private = next(item for item in plan.transitions if item.owner.entity_name == "_Draft")
    original = next(item for item in plan.transitions if item.final_path == "entities/model_Draft.md")

    assert private.action == "create"
    assert private.previous_owner is None and private.source_path is None
    assert private.final_path == original.old_path == "entities/Draft.md"
    assert original.source_path == "entities/Draft.md"
    assert len(plan.staged_moves) == 1
    with pytest.raises(StagedRenamesRequired, match="Staged page renames required"):
        plan.require_legacy_compatible(SyncDiff())


@pytest.mark.parametrize("scope", ["entity", "module"])
@pytest.mark.parametrize("cycle", [False, True])
def test_chains_and_cycles_use_two_phase_staging_independent_of_order(tmp_path, scope, cycle):
    inventory = _inventory(alpha=["A"], beta=["B"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    modules = build_module_page_map(inventory)
    entities = build_entity_occurrence_page_map(inventory, modules)
    if scope == "entity":
        entities["A", "pkg/alpha.py", 1] = "B"
        entities["B", "pkg/beta.py", 1] = "A" if cycle else "C"
        first, second, target = "entities/A.md", "entities/B.md", "entities/A.md" if cycle else "entities/C.md"
    else:
        modules["pkg/alpha.py"] = "beta"
        modules["pkg/beta.py"] = "alpha" if cycle else "gamma"
        first, second, target = "modules/alpha.md", "modules/beta.md", "modules/alpha.md" if cycle else "modules/gamma.md"
    before = _snapshot(wiki)
    original_maps = deepcopy((modules, entities))
    plan = _plan(wiki, manifest, inventory, modules=modules, entities=entities)
    reordered = _plan(
        wiki, manifest, dict(reversed(list(inventory.items()))),
        modules=dict(reversed(list(modules.items()))),
        entities=dict(reversed(list(entities.items()))),
    )
    assert reordered == plan
    assert len(plan.staged_moves) == 2
    assert len({move.staging_slot for move in plan.staged_moves}) == 2
    # Model the two phases in memory: planning itself never moves these files.
    contents = {name: value[0] for name, value in before.items()}
    staged = {move.staging_slot: contents.pop(move.source_path) for move in plan.staged_moves}
    for move in plan.staged_moves:
        contents[move.final_path] = staged[move.staging_slot]
    assert contents[second] == before[first][0]
    assert contents[target] == before[second][0]
    assert _snapshot(wiki) == before
    assert (modules, entities) == original_maps
    with pytest.raises(StagedRenamesRequired):
        plan.require_legacy_compatible(SyncDiff())


@pytest.mark.parametrize("scope", ["entity", "module"])
def test_occupied_unowned_destination_is_preserved(tmp_path, scope):
    inventory = _inventory(alpha=["A"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    modules = build_module_page_map(inventory)
    entities = build_entity_occurrence_page_map(inventory, modules)
    if scope == "entity":
        entities["A", "pkg/alpha.py", 1] = "Manual"
        target = wiki / "entities/Manual.md"
    else:
        modules["pkg/alpha.py"] = "Manual"
        target = wiki / "modules/Manual.md"
    target.write_text("Authored unrelated content.", encoding="utf-8")
    before = _snapshot(wiki)
    with pytest.raises(PageTransitionError, match="no verified outgoing owner"):
        _plan(wiki, manifest, inventory, modules=modules, entities=entities)
    assert _snapshot(wiki) == before


@pytest.mark.parametrize("scope", ["entity", "module"])
def test_duplicate_portable_destinations_are_rejected(tmp_path, scope):
    inventory = _inventory(alpha=["A"], beta=["B"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    modules = build_module_page_map(inventory)
    entities = build_entity_occurrence_page_map(inventory, modules)
    if scope == "entity":
        entities = {("A", "pkg/alpha.py", 1): "Same", ("B", "pkg/beta.py", 1): "same"}
    else:
        modules = {"pkg/alpha.py": "Same", "pkg/beta.py": "same"}
    with pytest.raises(PageTransitionError, match="Multiple current owners target"):
        _plan(wiki, manifest, inventory, modules=modules, entities=entities)


def test_module_old_page_cannot_have_multiple_claimants(tmp_path):
    inventory = _inventory(alpha=["A"], beta=["B"])
    manifest = _manifest(inventory)
    manifest.sources["pkg/beta.py"]["module_page"] = "alpha"
    manifest.page_source_mappings.pop("modules/beta.md")
    wiki = _wiki(tmp_path, manifest)
    before = _snapshot(wiki)
    with pytest.raises(PageTransitionError, match="Multiple recorded owners"):
        _plan(wiki, manifest, inventory)
    assert _snapshot(wiki) == before


def test_missing_rename_source_is_creation_and_never_borrows_new_owners_content(tmp_path):
    manifest = _manifest(_inventory(model=["Draft"]))
    wiki = _wiki(tmp_path, manifest)
    (wiki / "entities/Draft.md").unlink()
    current = _inventory(composer=["Draft"], fakes=["_Draft"], model=["Draft"])
    plan = _plan(wiki, manifest, current)
    original = next(item for item in plan.transitions if item.final_path == "entities/model_Draft.md")
    assert original.old_path == "entities/Draft.md"
    assert original.source_missing and original.action == "create"
    assert plan.staged_moves == ()
    with pytest.raises(StagedRenamesRequired):
        plan.require_legacy_compatible(SyncDiff())


def test_repeated_declarations_have_separate_moves_but_still_require_safe_application(tmp_path):
    inventory = _inventory(alpha=["Draft", "Draft"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    entities = {("Draft", "pkg/alpha.py", 1): "First", ("Draft", "pkg/alpha.py", 2): "Second"}
    plan = _plan(wiki, manifest, inventory, entities=entities)
    assert {(item.owner.occurrence, item.old_path, item.final_path) for item in plan.transitions if item.owner.scope == "entity"} == {
        (1, "entities/Draft.md", "entities/First.md"),
        (2, "entities/Draft_2.md", "entities/Second.md"),
    }
    assert len(plan.staged_moves) == 2
    with pytest.raises(StagedRenamesRequired):
        plan.require_legacy_compatible(SyncDiff(renamed_entity_pages={("Draft", "pkg/alpha.py"): ("Draft", "First")}))


def test_same_path_is_noop_and_simple_rename_remains_legacy_compatible(tmp_path):
    inventory = _inventory(alpha=["A"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    unchanged = _plan(wiki, manifest, inventory)
    assert all(item.action == "retain" for item in unchanged.transitions)
    assert unchanged.staged_moves == ()
    unchanged.require_legacy_compatible(SyncDiff())
    rename = _plan(wiki, manifest, inventory, entities={("A", "pkg/alpha.py", 1): "NewA"})
    rename.require_legacy_compatible(SyncDiff(renamed_entity_pages={("A", "pkg/alpha.py"): ("A", "NewA")}))


@pytest.mark.parametrize("extra", [False, True])
def test_supplied_page_maps_must_cover_exactly_the_live_inventory(tmp_path, extra):
    inventory = _inventory(alpha=["A"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    entities = build_entity_occurrence_page_map(inventory)
    if extra:
        entities["Ghost", "pkg/alpha.py", 1] = "Ghost"
    else:
        entities.clear()
    with pytest.raises(PageTransitionError, match="absent from|Missing entity"):
        _plan(wiki, manifest, inventory, entities=entities)


def test_uninspectable_page_directory_is_a_controlled_preflight_error(tmp_path, monkeypatch):
    inventory = _inventory(alpha=["A"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    before = _snapshot(wiki)
    lstat = Path.lstat

    def refuse(path, *args, **kwargs):
        if path == wiki / "entities":
            raise PermissionError("cannot inspect entity directory")
        return lstat(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", refuse)
        with pytest.raises(PageTransitionError, match="Cannot inspect"):
            _plan(wiki, manifest, inventory)
    assert _snapshot(wiki) == before


@pytest.mark.parametrize("source", [False, True])
def test_nonregular_source_or_target_is_never_overwritten(tmp_path, source):
    inventory = _inventory(alpha=["A"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    path = wiki / ("entities/A.md" if source else "entities/New.md")
    if source:
        path.unlink()
    path.mkdir()
    (path / "keep.txt").write_text("Preserve directory content.", encoding="utf-8")
    before = _snapshot(wiki)
    with pytest.raises(PageTransitionError, match="not a regular file"):
        _plan(wiki, manifest, inventory, entities={("A", "pkg/alpha.py", 1): "New"})
    assert _snapshot(wiki) == before


def test_case_variant_of_unowned_target_is_also_protected(tmp_path):
    inventory = _inventory(alpha=["A"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    (wiki / "entities/new.md").write_text("Unrelated notes.", encoding="utf-8")
    before = _snapshot(wiki)
    with pytest.raises(PageTransitionError, match="no verified outgoing owner"):
        _plan(wiki, manifest, inventory, entities={("A", "pkg/alpha.py", 1): "New"})
    assert _snapshot(wiki) == before


@pytest.mark.parametrize("bad_path", ["../../A.md", "modules/A.md"])
def test_recorded_entity_paths_cannot_be_reinterpreted_by_their_basename(tmp_path, bad_path):
    inventory = _inventory(alpha=["A"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    owner = manifest.page_source_mappings.pop("entities/A.md")
    manifest.page_source_mappings[bad_path] = owner
    before = _snapshot(wiki)
    with pytest.raises(PageTransitionError, match="Invalid recorded page path"):
        _plan(wiki, manifest, inventory)
    assert _snapshot(wiki) == before


def test_nonpage_entries_are_not_inspected_as_transition_targets(tmp_path, monkeypatch):
    inventory = _inventory(alpha=["A"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    asset = wiki / "entities/diagram.png"
    asset.write_bytes(b"unrelated asset")
    lstat = Path.lstat

    def forbid_asset_probe(path, *args, **kwargs):
        assert path != asset, "An unrelated non-page entry was inspected"
        return lstat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", forbid_asset_probe)
    plan = _plan(wiki, manifest, inventory)
    assert all(item.action == "retain" for item in plan.transitions)
    assert asset.read_bytes() == b"unrelated asset"
