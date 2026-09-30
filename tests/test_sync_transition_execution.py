"""Staged page ownership, guarded writes, and recoverable failure boundaries."""

import hashlib
import json
from pathlib import Path

import pytest

from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import sync_transition_execution as execution
from llm_wiki_cli.services.sync_transitions import PageTransitionError
from llm_wiki_cli.services.io import read_md
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.test_sync_analysis import _inventory, _manifest
from tests.test_sync_page_transitions import (
    _assert_consistent, _author_description, _bootstrap_project, _draft_source, _sync,
)
from tests.test_sync_transitions import _plan, _snapshot, _wiki


def _case(tmp_path, scope="entity", cycle=False):
    inventory = _inventory(alpha=["A"], beta=["B"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    if scope == "entity":
        first, second, target = "entities/A.md", "entities/B.md", "entities/A.md" if cycle else "entities/C.md"
        plan = _plan(wiki, manifest, inventory, entities={
            ("A", "pkg/alpha.py", 1): "B", ("B", "pkg/beta.py", 1): "A" if cycle else "C",
        })
    else:
        first, second, target = "modules/alpha.md", "modules/beta.md", "modules/alpha.md" if cycle else "modules/gamma.md"
        plan = _plan(wiki, manifest, inventory, modules={
            "pkg/alpha.py": "beta", "pkg/beta.py": "alpha" if cycle else "gamma",
        })
    return wiki, plan, first, second, target


def _recovery(wiki):
    roots = list(wiki.glob(f"{execution.RECOVERY_PREFIX}*"))
    assert len(roots) == 1
    record = json.loads((roots[0] / "recovery.json").read_text())
    return roots[0], record


def _assert_originals(wiki, originals):
    root, record = _recovery(wiki)
    for move in record["moves"]:
        data = (root / move["backup"]).read_bytes()
        assert data == originals[move["source"]][0]
        assert hashlib.sha256(data).hexdigest() == move["sha256"]
    for repair in record.get("retained_pages", []):
        data = (root / repair["backup"]).read_bytes()
        assert data == originals[repair["source"]][0]
        assert hashlib.sha256(data).hexdigest() == repair["sha256"]
    return root, record


@pytest.mark.parametrize("scope", ["entity", "module"])
@pytest.mark.parametrize("cycle", [False, True])
def test_all_sources_are_backed_up_before_any_destination_is_placed(tmp_path, monkeypatch, scope, cycle):
    wiki, plan, first, second, target = _case(tmp_path, scope, cycle)
    before = _snapshot(wiki)
    unlink = execution.unlink_guarded_bytes
    removed = []

    def check_backups(path, **kwargs):
        _, record = _assert_originals(wiki, before)
        assert record["state"] == "prepared"
        removed.append(path.relative_to(wiki).as_posix())
        return unlink(path, **kwargs)

    monkeypatch.setattr(execution, "unlink_guarded_bytes", check_backups)
    with execution.PageTransitionExecution(wiki, plan) as session:
        session.apply(plan)
        assert set(removed) == {first, second}
        assert (wiki / second).read_bytes() == before[first][0]
        assert (wiki / target).read_bytes() == before[second][0]
        _, record = _assert_originals(wiki, before)
        assert record["state"] == "applied"
    assert not list(wiki.glob(f"{execution.RECOVERY_PREFIX}*"))


def test_missing_original_never_consumes_the_new_page_at_its_old_path(tmp_path):
    manifest = _manifest(_inventory(model=["Draft"]))
    wiki = _wiki(tmp_path, manifest)
    (wiki / "entities/Draft.md").unlink()
    inventory = _inventory(model=["Draft"], composer=["Draft"], fakes=["_Draft"])
    plan = _plan(wiki, manifest, inventory)
    with execution.PageTransitionExecution(wiki, plan) as session:
        session.apply(plan)
        session.write("entities/Draft.md", "Private class description.\n")
        session.write("entities/model_Draft.md", "Original class regenerated.\n")
    assert (wiki / "entities/Draft.md").read_text() == "Private class description.\n"
    assert (wiki / "entities/model_Draft.md").read_text() == "Original class regenerated.\n"


def test_staging_preserves_legacy_encoding_and_does_not_rewrite_equal_content(tmp_path):
    inventory = _inventory(alpha=["A"])
    manifest = _manifest(inventory)
    wiki = _wiki(tmp_path, manifest)
    content = "Authored café.\r\n".encode("cp1252")
    (wiki / "entities/A.md").write_bytes(content)
    plan = _plan(wiki, manifest, inventory, entities={("A", "pkg/alpha.py", 1): "NewA"})
    with execution.PageTransitionExecution(wiki, plan) as session:
        session.apply(plan)
        page = wiki / "entities/NewA.md"
        before = (page.read_bytes(), page.stat().st_mtime_ns)
        assert session.read_text("entities/NewA.md") == "Authored café.\n"
        assert session.write("entities/NewA.md", "Authored café.\n") == "unchanged"
        assert (page.read_bytes(), page.stat().st_mtime_ns) == before
    assert page.read_bytes() == content


@pytest.mark.parametrize("phase", ["capture", "remove", "place"])
def test_injected_stage_failures_retain_originals_and_block_reentry(tmp_path, monkeypatch, phase):
    wiki, plan, _, _, _ = _case(tmp_path)
    before = _snapshot(wiki)
    function = {
        "capture": "atomic_write_private_bytes", "remove": "unlink_guarded_bytes",
        "place": "atomic_write_guarded_bytes",
    }[phase]
    real = getattr(execution, function)
    calls = []

    def fail_second(path, *args, **kwargs):
        if path.name != "recovery.json":
            calls.append(path)
            if len(calls) == 2:
                raise OSError(f"Injected {phase} failure")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(execution, function, fail_second)
    with pytest.raises(PageTransitionError, match=f"Injected {phase} failure"):
        with execution.PageTransitionExecution(wiki, plan) as session:
            session.apply(plan)
    root, record = _recovery(wiki)
    if phase == "capture":
        assert record["state"] == "capturing"
        for name, data in before.items():
            assert (wiki / name).read_bytes() == data[0]
    else:
        _assert_originals(wiki, before)
    after = _snapshot(wiki)
    with pytest.raises(PageTransitionError, match="Unresolved page transition recovery"):
        with execution.PageTransitionExecution(wiki, plan):
            pytest.fail("recovery state was ignored")
    assert _snapshot(wiki) == after
    assert root.is_dir()


def test_concurrent_destination_is_not_overwritten_during_placement(tmp_path, monkeypatch):
    wiki, plan, _, _, target = _case(tmp_path)
    before = _snapshot(wiki)
    real = execution.atomic_write_guarded_bytes

    def occupy(path, *args, **kwargs):
        if path == wiki / target:
            path.write_bytes(b"Concurrent unrelated content")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(execution, "atomic_write_guarded_bytes", occupy)
    with pytest.raises(PageTransitionError):
        with execution.PageTransitionExecution(wiki, plan) as session:
            session.apply(plan)
    assert (wiki / target).read_bytes() == b"Concurrent unrelated content"
    _assert_originals(wiki, before)


def test_concurrent_source_edit_is_preserved_when_guarded_removal_refuses(tmp_path, monkeypatch):
    wiki, plan, first, _, _ = _case(tmp_path)
    before = _snapshot(wiki)
    real = execution.unlink_guarded_bytes

    def change_source(path, **kwargs):
        if path == wiki / first:
            path.write_bytes(b"Later authored source")
        return real(path, **kwargs)

    monkeypatch.setattr(execution, "unlink_guarded_bytes", change_source)
    with pytest.raises(PageTransitionError):
        with execution.PageTransitionExecution(wiki, plan) as session:
            session.apply(plan)
    assert (wiki / first).read_bytes() == b"Later authored source"
    _assert_originals(wiki, before)


def test_generated_write_cannot_overwrite_a_concurrent_author_edit(tmp_path):
    wiki, plan, _, second, _ = _case(tmp_path)
    before = _snapshot(wiki)
    with pytest.raises(PageTransitionError):
        with execution.PageTransitionExecution(wiki, plan) as session:
            session.apply(plan)
            (wiki / second).write_bytes(b"Concurrent authored edit")
            session.write(second, "Generated replacement")
    assert (wiki / second).read_bytes() == b"Concurrent authored edit"
    _assert_originals(wiki, before)


@pytest.mark.parametrize("scope", ["entity", "module"])
@pytest.mark.parametrize("kind", ["symlink", "directory"])
def test_nonregular_retired_page_is_rejected_before_live_renames(tmp_path, monkeypatch, scope, kind):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {
        "model.py": _draft_source("Original model."),
        "retired.py": _draft_source("Retiring class.", name="Retired"),
    })
    external = project / "notes.txt"
    external.write_text("Unrelated external notes.", encoding="utf-8")
    retired = wiki / ("entities/Retired.md" if scope == "entity" else "modules/retired.md")
    retired.unlink()
    if kind == "symlink":
        retired.symlink_to(external)
    else:
        retired.mkdir()
        (retired / "keep.txt").write_text("Preserve directory content.", encoding="utf-8")
    (project / "pkg/retired.py").unlink()
    (project / "pkg/composer.py").write_text(_draft_source("New collision."), encoding="utf-8")
    before = _snapshot(wiki)

    with pytest.raises(SystemExit) as exc:
        _sync(wiki)

    assert exc.value.code == 2
    assert retired.is_symlink() if kind == "symlink" else retired.is_dir()
    assert external.read_text() == "Unrelated external notes."
    assert _snapshot(wiki) == before
    assert not list(wiki.glob(f"{execution.RECOVERY_PREFIX}*"))


@pytest.mark.parametrize("failure", ["generation", "metadata"])
def test_command_failure_retains_backups_without_publishing_success_metadata(tmp_path, monkeypatch, capsys, failure):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": _draft_source("Original.")})
    _author_description(wiki / "entities/Draft.md", "Original.", "AUTHORED: keep this original.")
    before = _snapshot(wiki)
    for module, name in [("composer", "Draft"), ("fakes", "_Draft")]:
        (project / "pkg" / f"{module}.py").write_text(_draft_source(module, name=name), encoding="utf-8")
    if failure == "generation":
        real = sync_cmd._apply_module_page

        def fail_module(ctx, diff, result, filepath, *args):
            if filepath == "pkg/fakes.py":
                raise OSError("Injected generation failure")
            return real(ctx, diff, result, filepath, *args)

        monkeypatch.setattr(sync_cmd, "_apply_module_page", fail_module)
    else:
        def fail_metadata(*args, **kwargs):
            raise OSError("Injected metadata failure")

        monkeypatch.setattr(sync_cmd, "finalize_runtime_knowledge", fail_metadata)
    capsys.readouterr()
    with pytest.raises(OSError, match=f"Injected {failure} failure"):
        _sync(wiki)
    captured = capsys.readouterr()
    assert "Page transition recovery data retained" in captured.err
    assert "Sync complete:" not in captured.out
    _assert_originals(wiki, before)
    for name in [".llm-wiki-manifest.json", ".llm-wiki-knowledge.json", ".llm-wiki-surface.json"]:
        assert (wiki / name).read_bytes() == before[name][0]
    after = _snapshot(wiki)
    with pytest.raises(SystemExit) as exc:
        _sync(wiki)
    assert exc.value.code == 2
    assert _snapshot(wiki) == after


def test_three_way_dry_run_is_isolated_then_real_sync_converges(tmp_path, monkeypatch):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": _draft_source("Original.")})
    _author_description(wiki / "entities/Draft.md", "Original.", "AUTHORED: model's description.")
    for module, name in [("composer", "Draft"), ("fakes", "_Draft")]:
        (project / "pkg" / f"{module}.py").write_text(_draft_source(module, name=name), encoding="utf-8")
    before = _snapshot(wiki)
    _sync(wiki, dry_run=True)
    assert _snapshot(wiki) == before
    assert not list(wiki.glob(f"{execution.RECOVERY_PREFIX}*"))
    _sync(wiki)
    _assert_consistent(wiki)
    stable = _snapshot(wiki)
    _sync(wiki)
    assert _snapshot(wiki) == stable


@pytest.mark.parametrize("authored_first", [False, True])
@pytest.mark.parametrize("sharded", [False, True], ids=["inline", "sharded"])
def test_repeated_declaration_renames_keep_each_occurrences_semantics(tmp_path, monkeypatch, authored_first, sharded):
    source = _draft_source("First generated.") + "\n\n" + _draft_source("Second generated.")
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"alpha.py": source})
    if sharded:
        _sync(wiki, knowledge_format="sharded-v2")
    if authored_first:
        _author_description(wiki / "entities/Draft.md", "First generated.", "AUTHORED FIRST")
    _author_description(wiki / "entities/Draft_2.md", "Second generated.", "AUTHORED SECOND")
    (project / "pkg/alpha.py").write_text(source.replace("First generated.", "First updated."), encoding="utf-8")
    (project / "pkg/beta.py").write_text(_draft_source("Third generated."), encoding="utf-8")
    _sync(wiki)
    manifest = SyncManifest.load(wiki)
    for occurrence, name, expected in [
        (1, "alpha_Draft", "AUTHORED FIRST" if authored_first else "First updated."),
        (2, "alpha_Draft_2", "AUTHORED SECOND"),
    ]:
        content = read_md(wiki / f"entities/{name}.md")
        assert content.split("## Description\n", 1)[1].split("\n## ", 1)[0].strip() == expected
        mapping = manifest.page_source_mappings[f"entities/{name}.md"]
        assert (mapping.source_path, mapping.entity_name, mapping.occurrence) == ("pkg/alpha.py", "Draft", occurrence)
        assert manifest.evidence_baselines[f"entities/{name}.md"].is_known
    assert "AUTHORED" not in read_md(wiki / "entities/beta_Draft.md")
    _assert_consistent(wiki)
    before = _snapshot(wiki)
    _sync(wiki)
    assert _snapshot(wiki) == before


@pytest.mark.parametrize("authored", [False, True])
def test_source_move_uses_original_owners_semantic_baseline(tmp_path, monkeypatch, authored):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"alpha.py": _draft_source("Alpha generated.")})
    if authored:
        _author_description(wiki / "entities/Draft.md", "Alpha generated.", "AUTHORED original")
    (project / "pkg/alpha.py").unlink()
    (project / "pkg/beta.py").write_text(_draft_source("Beta generated."), encoding="utf-8")
    _sync(wiki)
    content = read_md(wiki / "entities/Draft.md")
    assert "pkg/beta.py:1" in content
    assert ("AUTHORED original" if authored else "Beta generated.") in content
    assert "Alpha generated." not in content
    mapping = SyncManifest.load(wiki).page_source_mappings["entities/Draft.md"]
    assert mapping.source_path == "pkg/beta.py"


@pytest.mark.parametrize("baseline", [None, {}, {"entities": None}])
def test_missing_legacy_semantic_baseline_preserves_owned_prose(tmp_path, monkeypatch, baseline):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"alpha.py": _draft_source("Generated.")})
    _author_description(wiki / "entities/Draft.md", "Generated.", "AUTHORED original")
    manifest = SyncManifest.load(wiki)
    manifest.sources["pkg/alpha.py"]["generated_semantics"] = baseline
    manifest.save(wiki)
    (project / "pkg/beta.py").write_text(_draft_source("Beta generated."), encoding="utf-8")
    _sync(wiki)
    assert "AUTHORED original" in read_md(wiki / "entities/alpha_Draft.md")
    assert "AUTHORED original" not in read_md(wiki / "entities/beta_Draft.md")
    _assert_consistent(wiki)


def test_changed_backup_is_detected_before_any_original_is_removed(tmp_path, monkeypatch):
    wiki, plan, _, _, _ = _case(tmp_path)
    before = _snapshot(wiki)
    real = execution.atomic_write_private_bytes

    def corrupt_backup_after_preparation(path, data, **kwargs):
        result = real(path, data, **kwargs)
        if path.name == "recovery.json" and json.loads(data)["state"] == "prepared":
            (path.parent / plan.staged_moves[-1].staging_slot).write_bytes(b"Broken backup")
        return result

    monkeypatch.setattr(execution, "atomic_write_private_bytes", corrupt_backup_after_preparation)
    with pytest.raises(PageTransitionError, match="Recovery files changed"):
        with execution.PageTransitionExecution(wiki, plan) as session:
            session.apply(plan)
    for name, value in before.items():
        assert (wiki / name).read_bytes() == value[0]


def test_cleanup_failure_keeps_recovery_and_reports_completed_transition(tmp_path, monkeypatch, capsys):
    wiki, plan, first, second, target = _case(tmp_path)
    before = _snapshot(wiki)

    def fail_cleanup(*args, **kwargs):
        raise OSError("Injected cleanup failure")

    monkeypatch.setattr(execution, "remove_guarded_tree", fail_cleanup)
    with pytest.raises(PageTransitionError, match="completed.*cleanup"):
        with execution.PageTransitionExecution(wiki, plan) as session:
            session.apply(plan)
    assert (wiki / second).read_bytes() == before[first][0]
    assert (wiki / target).read_bytes() == before[second][0]
    _, record = _assert_originals(wiki, before)
    assert record["state"] == "committed"
    assert "retained" in capsys.readouterr().err


@pytest.mark.parametrize("dry_run", [False, True])
def test_governance_identity_reuse_conflicts_before_any_page_write(tmp_path, monkeypatch, capsys, dry_run):
    from llm_wiki_cli import cli
    from llm_wiki_cli.commands import knowledge_cmd

    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"model.py": _draft_source("Original.")})
    knowledge_cmd.run(cli._build_parser().parse_args([
        "knowledge", "init", "--wiki-dir", str(wiki), "--bundle-id", "kb_transition_reuse",
    ]))
    for module, name in [("composer", "Draft"), ("fakes", "_Draft")]:
        (project / "pkg" / f"{module}.py").write_text(_draft_source(module, name=name), encoding="utf-8")
    before = _snapshot(wiki)
    capsys.readouterr()
    with pytest.raises(SystemExit) as exc:
        _sync(wiki, dry_run=dry_run)
    assert exc.value.code == 2
    assert "UID" in capsys.readouterr().err
    assert _snapshot(wiki) == before
    assert not list(wiki.glob(f"{execution.RECOVERY_PREFIX}*"))


def test_governance_moves_follow_the_plan_not_a_legacy_name_guess(tmp_path):
    from llm_wiki_cli.services.sync_analysis import SyncDiff
    from llm_wiki_cli.services.wiki_surface import PageKind, mcp_uri

    manifest = _manifest(_inventory(alpha=["Draft"], beta=["Other"]))
    wiki = _wiki(tmp_path, manifest)
    current = _inventory(alpha=["Draft"], beta=["Other", "Draft"])
    plan = _plan(wiki, manifest, current)
    incorrect_legacy_diff = SyncDiff(renamed_entity_pages={
        ("Draft", "pkg/beta.py"): ("Draft", "beta_Draft"),
    })
    assert sync_cmd._governance_moves_for_sync(
        incorrect_legacy_diff, manifest, entity_page_cache={}, page_transitions=plan,
    ) == {mcp_uri(PageKind.ENTITIES, "Draft"): mcp_uri(PageKind.ENTITIES, "alpha_Draft")}


@pytest.mark.parametrize("scope", ["entity", "module"])
def test_generation_after_a_cycle_keeps_each_pages_original_owner(tmp_path, scope):
    from llm_wiki_cli.services.bootstrap_runtime import (
        _generate_entity_md, _generate_module_md, build_entity_page_map, build_module_page_map,
    )
    from llm_wiki_cli.services.sync_analysis import compute_sync_diff
    from tests.test_sync_analysis import _hashes

    inventory = _inventory(alpha=["A"], beta=["B"])
    modules = build_module_page_map(inventory)
    entities = {("A", "pkg/alpha.py", 1): "A", ("B", "pkg/beta.py", 1): "B"}
    if scope == "module":
        modules = {"pkg/alpha.py": "beta", "pkg/beta.py": "alpha"}
    else:
        entities = {("A", "pkg/alpha.py", 1): "B", ("B", "pkg/beta.py", 1): "A"}
    manifest = SyncManifest.build_from_inventory(
        inventory, str(tmp_path), build_entity_page_map(inventory), modules,
        entity_occurrence_page_cache=entities, source_content_hashes=_hashes(inventory),
    )
    wiki = tmp_path / "wiki"
    for source, data in inventory.items():
        name = data["classes"][0]["name"]
        entity = wiki / "entities" / f"{entities[name, source, 1]}.md"
        module = wiki / "modules" / f"{modules[source]}.md"
        entity.parent.mkdir(parents=True, exist_ok=True)
        module.parent.mkdir(parents=True, exist_ok=True)
        entity.write_text(_generate_entity_md(data["classes"][0], source, {}, modules[source]), encoding="utf-8")
        module.write_text(_generate_module_md(source, data, {name: entities[name, source, 1]}), encoding="utf-8")
        target = entity if scope == "entity" else module
        generated = f"_Auto-generated from `{name}` in `{source}`._" if scope == "entity" else f"_Auto-generated from `{source}`._"
        _author_description(target, generated, f"AUTHORED for {source}")
    diff = compute_sync_diff(manifest, inventory, str(tmp_path), source_content_hashes=_hashes(inventory))
    result = sync_cmd._apply_diff(diff, wiki, inventory, str(tmp_path), manifest, include_plugins=False)
    for source, data in inventory.items():
        name = data["classes"][0]["name"]
        target = f"entities/{name}.md" if scope == "entity" else f"modules/{Path(source).stem}.md"
        assert f"AUTHORED for {source}" in read_md(wiki / target)
        assert target in result.regenerated_evidence_page_paths
    assert not list(wiki.glob(f"{execution.RECOVERY_PREFIX}*"))


def test_only_the_second_occurrence_rename_still_refreshes_module_links(tmp_path, monkeypatch):
    source = _draft_source("First.") + "\n\n" + _draft_source("Second.")
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"alpha.py": source})
    _author_description(wiki / "entities/Draft_2.md", "Second.", "AUTHORED second")
    (project / "pkg/beta.py").write_text(_draft_source("New distinct class.", name="Draft_2"), encoding="utf-8")
    _sync(wiki)
    assert "AUTHORED second" in read_md(wiki / "entities/alpha_Draft_2.md")
    assert "../entities/alpha_Draft_2.md" in read_md(wiki / "modules/alpha.md")
    mapping = SyncManifest.load(wiki).page_source_mappings["entities/alpha_Draft_2.md"]
    assert mapping.occurrence == 2 and mapping.source_path == "pkg/alpha.py"
    _assert_consistent(wiki)


def test_source_move_with_case_only_page_rename_does_not_deprecate_live_page(tmp_path, monkeypatch):
    from dataclasses import replace
    from llm_wiki_cli.commands import bootstrap_cmd
    from tests.test_sync import _make_bootstrap_args

    project = tmp_path / "project"
    (project / "pkg").mkdir(parents=True)
    (project / "pkg/alpha.py").write_text(_draft_source("Original draft."), encoding="utf-8")
    wiki = project / "docs/llm_wiki"
    monkeypatch.chdir(project)
    real_maps = bootstrap_cmd._prepare_bootstrap_page_maps

    def legacy_maps(inventory):
        return replace(
            real_maps(inventory),
            entity_page_name_cache={("Draft", "pkg/alpha.py"): "draft"},
            entity_occurrence_page_name_cache={("Draft", "pkg/alpha.py", 1): "draft"},
        )

    with monkeypatch.context() as setup:
        setup.setattr(bootstrap_cmd, "_prepare_bootstrap_page_maps", legacy_maps)
        bootstrap_cmd.run(_make_bootstrap_args(wiki_dir=str(wiki), skip_flows=True, skip_dependencies=True, jobs=1))
    _author_description(wiki / "entities/draft.md", "Original draft.", "AUTHORED moved draft.")
    (project / "pkg/alpha.py").rename(project / "pkg/beta.py")

    _sync(wiki, force=True)

    content = read_md(wiki / "entities/Draft.md")
    assert sync_cmd._DEPRECATION_HEADER not in content
    assert "AUTHORED moved draft." in content
    assert "pkg/beta.py:1" in content
    manifest = SyncManifest.load(wiki)
    assert manifest.page_source_mappings["entities/Draft.md"].source_path == "pkg/beta.py"
    assert "entities/Draft.md" not in manifest.tombstones
    retired_module = read_md(wiki / "modules/alpha.md")
    assert "../entities/Draft.md" in retired_module
    assert "../entities/draft.md" not in retired_module
    from llm_wiki_cli.commands import lint_cmd
    report = lint_cmd.build_report(wiki, ".", strict=True, parallel_jobs=1, include_plugins=False)
    # Source removal intentionally retains the old module with a stale marker.
    assert {(issue.category, issue.path, issue.target) for issue in report.issues} == {
        ("orphan_pages", "modules/alpha.md", None),
        ("stale_modules", None, "alpha"),
    }
    stable = _snapshot(wiki)
    _sync(wiki)
    assert _snapshot(wiki) == stable


@pytest.mark.parametrize("scope", ["entity", "module"])
def test_cycle_sync_commits_correct_metadata_and_converges(tmp_path, monkeypatch, scope):
    from dataclasses import replace
    from llm_wiki_cli.commands import bootstrap_cmd
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
    from tests.test_sync import _make_bootstrap_args

    project = tmp_path / "project"
    (project / "pkg").mkdir(parents=True)
    for module, name in [("alpha", "A"), ("beta", "B")]:
        (project / "pkg" / f"{module}.py").write_text(_draft_source(f"{module} generated.", name=name), encoding="utf-8")
    wiki = project / "docs/llm_wiki"
    monkeypatch.chdir(project)
    real_maps = bootstrap_cmd._prepare_bootstrap_page_maps

    def legacy_maps(inventory):
        maps = real_maps(inventory)
        if scope == "module":
            return replace(maps, module_page_map={"pkg/alpha.py": "beta", "pkg/beta.py": "alpha"})
        return replace(
            maps,
            entity_page_name_cache={("A", "pkg/alpha.py"): "B", ("B", "pkg/beta.py"): "A"},
            entity_occurrence_page_name_cache={("A", "pkg/alpha.py", 1): "B", ("B", "pkg/beta.py", 1): "A"},
        )

    with monkeypatch.context() as setup:
        setup.setattr(bootstrap_cmd, "_prepare_bootstrap_page_maps", legacy_maps)
        bootstrap_cmd.run(_make_bootstrap_args(wiki_dir=str(wiki), skip_flows=True, skip_dependencies=True, jobs=1))
    for module, old_page in [("alpha", "B" if scope == "entity" else "beta"), ("beta", "A" if scope == "entity" else "alpha")]:
        relative = f"entities/{old_page}.md" if scope == "entity" else f"modules/{old_page}.md"
        generated = f"{module} generated." if scope == "entity" else f"_Auto-generated from `pkg/{module}.py`._"
        _author_description(wiki / relative, generated, f"AUTHORED for {module}")
    _sync(wiki)
    manifest = SyncManifest.load(wiki)
    for module, name in [("alpha", "A"), ("beta", "B")]:
        relative = f"entities/{name}.md" if scope == "entity" else f"modules/{module}.md"
        assert f"AUTHORED for {module}" in read_md(wiki / relative)
        assert manifest.page_source_mappings[relative].source_path == f"pkg/{module}.py"
        assert manifest.evidence_baselines[relative].is_known
    assert load_knowledge_state(wiki).status is KnowledgeLoadState.VALID
    _assert_consistent(wiki)
    stable = _snapshot(wiki)
    _sync(wiki)
    assert _snapshot(wiki) == stable
