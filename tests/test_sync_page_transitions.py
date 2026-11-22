"""Ownership and page-transition contracts for incremental sync."""

from __future__ import annotations

from pathlib import Path

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, lint_cmd, sync_cmd
from llm_wiki_engine.io import read_md
from llm_wiki_engine.knowledge_governance import GOVERNANCE_LOCK_FILENAME
from llm_wiki_engine.maintenance_protocol import STORAGE_LOCK_FILENAME
from llm_wiki_engine.sync_manifest import SyncManifest
from tests.test_sync import _make_bootstrap_args, _make_sync_args


class _MissingManagedPage(AssertionError):
    """The expected generated page was not written or restored."""


class _UnexpectedEntityDescription(AssertionError):
    """An entity did not retain its own expected description."""


def _draft_source(description: str, *, name: str = "Draft") -> str:
    return f'class {name}:\n    """{description}"""\n\n    subject: str = ""\n'


def _assert_consistent(wiki_dir: Path) -> None:
    report = lint_cmd.build_report(
        wiki_dir, ".", strict=True, parallel_jobs=1, include_plugins=False
    )
    assert report.passed, report.by_category()


def _bootstrap_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sources: dict[str, str],
    *,
    skip_dependencies: bool = True,
) -> tuple[Path, Path]:
    project = tmp_path / "project"
    (project / "pkg").mkdir(parents=True)
    for name, content in sources.items():
        (project / "pkg" / name).write_text(content, encoding="utf-8")
    monkeypatch.chdir(project)
    wiki_dir = project / "docs" / "llm_wiki"
    bootstrap_cmd.run(
        _make_bootstrap_args(
            wiki_dir=str(wiki_dir),
            jobs=1,
            no_plugins=True,
            skip_flows=True,
            skip_dependencies=skip_dependencies,
        )
    )
    _assert_consistent(wiki_dir)
    return project, wiki_dir


def _sync(wiki_dir: Path, **kwargs) -> None:
    sync_cmd.run(
        _make_sync_args(wiki_dir=str(wiki_dir), jobs=1, no_plugins=True, **kwargs)
    )


def _description(content: str) -> str:
    assert "\n## Description\n" in content, "Page has no Description section"
    return content.split("\n## Description\n", 1)[1].split("\n## ", 1)[0].strip()


def _author_description(page: Path, generated: str, authored: str) -> None:
    content = read_md(page)
    assert _description(content) == generated
    old_section = f"\n## Description\n\n{generated}\n"
    assert content.count(old_section) == 1
    page.write_text(
        content.replace(old_section, f"\n## Description\n\n{authored}\n", 1),
        encoding="utf-8",
    )


def _assert_page_mapping(
    wiki_dir: Path,
    relative_path: str,
    source_path: str,
    *,
    entity_name: str | None = None,
) -> None:
    manifest = SyncManifest.load(wiki_dir)
    mapping = manifest.page_source_mappings[relative_path]
    assert mapping.source_path == source_path
    assert mapping.scope == ("entity" if entity_name is not None else "module")
    assert mapping.entity_name == entity_name
    assert mapping.occurrence == (1 if entity_name is not None else None)
    source = manifest.sources[source_path]
    if entity_name is not None:
        assert source["entity_pages"][entity_name] == Path(relative_path).stem
        assert (entity_name, 1, Path(relative_path).stem) in {
            (entry["name"], entry["occurrence"], entry["page"])
            for entry in source["entity_page_occurrences"]
        }
    else:
        assert source["module_page"] == Path(relative_path).stem
    baseline = manifest.evidence_baselines[relative_path]
    assert baseline.is_known
    assert baseline.basis is not None
    assert baseline.basis.source_path == source_path
    assert baseline.basis.source_content_hash == source["hash"]


def _require_page(wiki_dir: Path, relative_path: str) -> str:
    page = wiki_dir / relative_path
    if not page.is_file():
        raise _MissingManagedPage(f"Expected managed page: {relative_path}")
    return read_md(page)


def _assert_entity_page(
    wiki_dir: Path,
    page_name: str,
    source_path: str,
    description: str,
    *,
    entity_name: str = "Draft",
    line: int = 1,
) -> None:
    relative_path = f"entities/{page_name}.md"
    content = _require_page(wiki_dir, relative_path)
    assert content.startswith(f"# {entity_name}\n")
    assert f"**Location:** `{source_path}:{line}`" in content
    _assert_page_mapping(
        wiki_dir, relative_path, source_path, entity_name=entity_name
    )
    module_page = SyncManifest.load(wiki_dir).sources[source_path]["module_page"]
    assert f"../entities/{page_name}.md" in read_md(
        wiki_dir / "modules" / f"{module_page}.md"
    )
    assert f"entities/{page_name}.md" in read_md(wiki_dir / "index.md")
    actual = _description(content)
    if actual != description:
        raise _UnexpectedEntityDescription(
            f"{relative_path} ({source_path}): expected description "
            f"{description!r}, got {actual!r}"
        )


def _assert_module_page(wiki_dir: Path, page_name: str, source_path: str) -> None:
    relative_path = f"modules/{page_name}.md"
    content = _require_page(wiki_dir, relative_path)
    assert f"**Path:** `{source_path}`" in content
    _assert_page_mapping(wiki_dir, relative_path, source_path)


def _check_added_twin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, existing_module: bool,
    governed: bool = False,
) -> None:
    from llm_wiki_cli import cli
    from llm_wiki_cli.commands import knowledge_cmd
    from llm_wiki_engine.knowledge_governance import load_governance
    from llm_wiki_engine.wiki_surface import PageKind, mcp_uri

    original_doc = "A draft in module alpha."
    new_doc = "A draft in module beta."
    authored = "HAND-WRITTEN: alpha alone owns this description."
    sources = {"alpha.py": _draft_source(original_doc)}
    other_source = 'class Other:\n    """Something else."""\n'
    if existing_module:
        sources["beta.py"] = other_source
    project, wiki_dir = _bootstrap_project(tmp_path, monkeypatch, sources)
    original_uid = None
    if governed:
        knowledge_cmd.run(cli._build_parser().parse_args([
            "knowledge", "init", "--wiki-dir", str(wiki_dir),
            "--bundle-id", "kb_added_twin",
        ]))
        original_uid = next(
            uid for uid, allocation in load_governance(wiki_dir).ledger.concepts.items()
            if allocation.locator == mcp_uri(PageKind.ENTITIES, "Draft")
        )
    # Setup uses ordinary assertions, outside the expected defect exception types.
    _assert_page_mapping(
        wiki_dir, "entities/Draft.md", "pkg/alpha.py", entity_name="Draft"
    )
    _author_description(wiki_dir / "entities/Draft.md", original_doc, authored)

    (project / "pkg/beta.py").write_text(
        (other_source + "\n\n" if existing_module else "") + _draft_source(new_doc),
        encoding="utf-8",
    )
    _sync(wiki_dir)

    _assert_entity_page(wiki_dir, "alpha_Draft", "pkg/alpha.py", authored)
    _assert_entity_page(
        wiki_dir,
        "beta_Draft",
        "pkg/beta.py",
        new_doc,
        line=5 if existing_module else 1,
    )
    expected_pages = {"alpha_Draft.md", "beta_Draft.md"}
    if existing_module:
        expected_pages.add("Other.md")
        _assert_entity_page(
            wiki_dir,
            "Other",
            "pkg/beta.py",
            "Something else.",
            entity_name="Other",
        )
    assert {p.name for p in (wiki_dir / "entities").glob("*.md")} == expected_pages
    for module in ("alpha", "beta"):
        _assert_module_page(wiki_dir, module, f"pkg/{module}.py")
    _assert_consistent(wiki_dir)
    if governed:
        assert original_uid is not None
        ledger = load_governance(wiki_dir).ledger
        assert ledger.concepts[original_uid].locator == mcp_uri(PageKind.ENTITIES, "alpha_Draft")
        beta_uid = next(
            uid for uid, allocation in ledger.concepts.items()
            if allocation.locator == mcp_uri(PageKind.ENTITIES, "beta_Draft")
        )
        assert beta_uid != original_uid


def _check_private_twin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, second_public: bool
) -> None:
    original_doc = "A mail draft."
    private_doc = "A private twin of the draft."
    other_doc = "A second public draft, in another module."
    authored = "HAND-WRITTEN: model alone owns this description."
    project, wiki_dir = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source(original_doc)}
    )
    _assert_page_mapping(
        wiki_dir, "entities/Draft.md", "pkg/model.py", entity_name="Draft"
    )
    _author_description(wiki_dir / "entities/Draft.md", original_doc, authored)
    (project / "pkg/fakes.py").write_text(
        _draft_source(private_doc, name="_Draft"), encoding="utf-8"
    )
    if second_public:
        (project / "pkg/composer.py").write_text(
            _draft_source(other_doc), encoding="utf-8"
        )
    _sync(wiki_dir)

    private_page = "Draft" if second_public else "fakes_Draft"
    _assert_entity_page(
        wiki_dir, private_page, "pkg/fakes.py", private_doc, entity_name="_Draft"
    )
    _assert_entity_page(wiki_dir, "model_Draft", "pkg/model.py", authored)
    expected_pages = {f"{private_page}.md", "model_Draft.md"}
    if second_public:
        expected_pages.add("composer_Draft.md")
        _assert_entity_page(wiki_dir, "composer_Draft", "pkg/composer.py", other_doc)
        _assert_module_page(wiki_dir, "composer", "pkg/composer.py")
    assert {p.name for p in (wiki_dir / "entities").glob("*.md")} == expected_pages
    for module in ("model", "fakes"):
        _assert_module_page(wiki_dir, module, f"pkg/{module}.py")
    _assert_consistent(wiki_dir)


@pytest.mark.parametrize("governed", [False, True])
def test_new_module_twin_preserves_original_page_owner(tmp_path, monkeypatch, governed):
    _check_added_twin(tmp_path, monkeypatch, existing_module=False, governed=governed)


@pytest.mark.parametrize("governed", [False, True])
def test_existing_module_twin_preserves_original_page_owner(tmp_path, monkeypatch, governed):
    _check_added_twin(tmp_path, monkeypatch, existing_module=True, governed=governed)
    from llm_wiki_cli.services.doctor_service import build_doctor_report

    report = build_doctor_report(
        src_dir=".", wiki_dir="docs/llm_wiki", strict=True, parallel_jobs=1
    )
    assert report.exit_code == 0, report.to_payload()


def test_two_way_private_twin_preserves_both_page_owners(tmp_path, monkeypatch):
    _check_private_twin(tmp_path, monkeypatch, second_public=False)


def test_three_way_private_twin_preserves_all_page_owners_and_converges(tmp_path, monkeypatch):
    _check_private_twin(tmp_path, monkeypatch, second_public=True)
    wiki = Path.cwd() / "docs/llm_wiki"
    before = {p.relative_to(wiki): (p.read_bytes(), p.stat().st_mtime_ns) for p in wiki.rglob("*") if p.is_file()}
    _sync(wiki)
    assert {p.relative_to(wiki): (p.read_bytes(), p.stat().st_mtime_ns) for p in wiki.rglob("*") if p.is_file()} == before


def test_rename_and_unchanged_page_repairs_share_one_sync(tmp_path, monkeypatch):
    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch,
        {
            "model.py": _draft_source("Original model."),
            "stable.py": _draft_source("Unchanged source.", name="Stable"),
        },
    )
    _author_description(wiki / "entities/Draft.md", "Original model.", "Authored model.")
    (wiki / "modules/model.md").unlink()
    (wiki / "entities/Stable.md").unlink()
    (project / "pkg/composer.py").write_text(_draft_source("New public draft."), encoding="utf-8")
    (project / "pkg/fakes.py").write_text(_draft_source("New private draft.", name="_Draft"), encoding="utf-8")
    before = {p.relative_to(wiki): (p.read_bytes(), p.stat().st_mtime_ns) for p in wiki.rglob("*") if p.is_file()}

    _sync(wiki, dry_run=True)
    assert {p.relative_to(wiki): (p.read_bytes(), p.stat().st_mtime_ns) for p in wiki.rglob("*") if p.is_file()} == before
    _sync(wiki)

    _assert_entity_page(wiki, "model_Draft", "pkg/model.py", "Authored model.")
    _assert_entity_page(wiki, "composer_Draft", "pkg/composer.py", "New public draft.")
    _assert_entity_page(wiki, "Draft", "pkg/fakes.py", "New private draft.", entity_name="_Draft")
    _assert_entity_page(wiki, "Stable", "pkg/stable.py", "Unchanged source.", entity_name="Stable")
    _assert_module_page(wiki, "model", "pkg/model.py")
    _assert_consistent(wiki)
    stable = {p.relative_to(wiki): (p.read_bytes(), p.stat().st_mtime_ns) for p in wiki.rglob("*") if p.is_file()}
    _sync(wiki)
    assert {p.relative_to(wiki): (p.read_bytes(), p.stat().st_mtime_ns) for p in wiki.rglob("*") if p.is_file()} == stable


MODULE_ALIAS = "import sys\n\nfrom engine import model\n\nsys.modules[__name__] = model\n"


@pytest.mark.parametrize("leaves_alias", [False, True])
def test_module_moved_to_another_directory_keeps_its_page(
    tmp_path, monkeypatch, leaves_alias
):
    project, wiki_dir = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original description.")}
    )
    _author_description(
        wiki_dir / "modules/model.md",
        "_Auto-generated from `pkg/model.py`._",
        "AUTHORED: module purpose.",
    )
    _author_description(
        wiki_dir / "entities/Draft.md", "Original description.", "AUTHORED: entity."
    )
    _sync(wiki_dir)
    (project / "engine").mkdir()
    (project / "pkg/model.py").rename(project / "engine/model.py")
    if leaves_alias:
        (project / "pkg/model.py").write_text(MODULE_ALIAS, encoding="utf-8")

    _sync(wiki_dir)

    _assert_module_page(wiki_dir, "model", "engine/model.py")
    module = read_md(wiki_dir / "modules/model.md")
    assert "AUTHORED: module purpose." in module
    assert not module.startswith(sync_cmd._DEPRECATION_HEADER)
    _assert_entity_page(wiki_dir, "Draft", "engine/model.py", "AUTHORED: entity.")
    assert {p.name for p in (wiki_dir / "modules").glob("*.md")} == {"model.md"}
    assert "pkg/model.py" not in SyncManifest.load(wiki_dir).sources
    _assert_consistent(wiki_dir)
    stable = {p.relative_to(wiki_dir): p.read_bytes() for p in wiki_dir.rglob("*") if p.is_file()}
    _sync(wiki_dir)
    assert {p.relative_to(wiki_dir): p.read_bytes() for p in wiki_dir.rglob("*") if p.is_file()} == stable


def _adopted_moved_module(tmp_path, monkeypatch) -> tuple[Path, Path]:
    from llm_wiki_cli import api

    project, wiki_dir = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original description.")}
    )
    _author_description(
        wiki_dir / "modules/model.md",
        "_Auto-generated from `pkg/model.py`._",
        "AUTHORED: module purpose.",
    )
    _sync(wiki_dir)
    api.adopt_maintenance(".", "docs/llm_wiki", recovery_dir=tmp_path / "recovery")
    _sync(wiki_dir)
    (project / "engine").mkdir()
    (project / "pkg/model.py").rename(project / "engine/model.py")
    return project, wiki_dir


def test_dry_run_previews_a_maintained_module_move_without_writing(tmp_path, monkeypatch):
    _, wiki_dir = _adopted_moved_module(tmp_path, monkeypatch)
    before = {p.relative_to(wiki_dir): p.read_bytes() for p in wiki_dir.rglob("*") if p.is_file()}

    _sync(wiki_dir, dry_run=True)

    assert {p.relative_to(wiki_dir): p.read_bytes() for p in wiki_dir.rglob("*") if p.is_file()} == before
    _sync(wiki_dir)
    _assert_module_page(wiki_dir, "model", "engine/model.py")
    assert "AUTHORED: module purpose." in read_md(wiki_dir / "modules/model.md")


def _wiki_bytes(wiki_dir: Path) -> dict[Path, bytes]:
    return {
        path.relative_to(wiki_dir): b"<link>" if path.is_symlink() else path.read_bytes()
        for path in sorted(wiki_dir.rglob("*"))
        if path.is_symlink() or path.is_file()
    }


@pytest.mark.parametrize("dry_run", [True, False])
def test_moved_module_whose_page_was_removed_is_refused(tmp_path, monkeypatch, dry_run):
    from llm_wiki_cli.services.knowledge_generation import KnowledgeGenerationError

    _, wiki_dir = _adopted_moved_module(tmp_path, monkeypatch)
    # The maintained page is gone, so its prose cannot be carried to the new owner.
    (wiki_dir / "modules/model.md").unlink()
    before = _wiki_bytes(wiki_dir)

    with pytest.raises(KnowledgeGenerationError) as raised:
        _sync(wiki_dir, dry_run=dry_run)

    assert "previous-semantic-preimage-unavailable (modules/model.md)" in str(raised.value)
    # A writing sync preflights on a staged copy, so a refusal writes nothing.
    assert _wiki_bytes(wiki_dir) == before


@pytest.mark.parametrize("dry_run", [True, False])
def test_undecodable_maintained_page_is_refused_by_name(tmp_path, monkeypatch, capsys, dry_run):
    from llm_wiki_cli.services.sync_runtime import SyncAborted

    _, wiki_dir = _adopted_moved_module(tmp_path, monkeypatch)
    page = wiki_dir / "modules/model.md"
    # 0x81 is undefined in both UTF-8 (as a lead byte) and Windows-1252.
    page.write_bytes(page.read_bytes().replace(b"AUTHORED: module purpose.", b"AUTHORED \x81 purpose."))
    before = _wiki_bytes(wiki_dir)

    with pytest.raises(SyncAborted):
        _sync(wiki_dir, dry_run=dry_run)

    error = capsys.readouterr().err
    assert "neither UTF-8 nor Windows-1252" in error
    # The page is named where the user can repair it, never in the discarded preview copy.
    assert str(Path("modules", "model.md")) in error
    assert "llm-wiki-sync-preview" not in error
    assert _wiki_bytes(wiki_dir) == before


def test_adopted_writing_sync_preflights_once_and_plain_sync_does_not(tmp_path, monkeypatch):
    from llm_wiki_cli import api
    from llm_wiki_cli.services import sync_runtime

    project, wiki_dir = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original description.")}
    )
    calls = []
    original = sync_runtime._run_sync_dry_run

    def counted(options, prepared):
        calls.append(options.dry_run)
        return original(options, prepared)

    monkeypatch.setattr(sync_runtime, "_run_sync_dry_run", counted)
    (project / "pkg/model.py").write_text(_draft_source("Changed once."), encoding="utf-8")
    _sync(wiki_dir)
    assert calls == []
    api.adopt_maintenance(".", "docs/llm_wiki", recovery_dir=tmp_path / "recovery")
    (project / "pkg/model.py").write_text(_draft_source("Changed twice."), encoding="utf-8")
    _sync(wiki_dir)
    assert calls == [False]
    assert "Changed twice." in read_md(wiki_dir / "entities/Draft.md")


@pytest.mark.parametrize("dry_run", [True, False])
@pytest.mark.parametrize("linked", ["page", "folder"])
def test_moved_module_page_behind_a_link_is_never_read(tmp_path, monkeypatch, linked, dry_run):
    import os

    _, wiki_dir = _adopted_moved_module(tmp_path, monkeypatch)
    page = wiki_dir / "modules/model.md"
    if linked == "page":
        outside = tmp_path / "outside.md"
        outside.write_bytes(page.read_bytes())
        page.unlink()
        os.symlink(outside, page)
    else:
        outside = tmp_path / "outside-modules"
        (wiki_dir / "modules").rename(outside)
        os.symlink(outside, wiki_dir / "modules", target_is_directory=True)
    before = _wiki_bytes(wiki_dir)
    outside_before = outside.read_bytes() if outside.is_file() else _wiki_bytes(outside)

    with pytest.raises(BaseException) as raised:
        _sync(wiki_dir, dry_run=dry_run)

    assert not isinstance(raised.value, (KeyboardInterrupt, AssertionError))
    assert _wiki_bytes(wiki_dir) == before
    assert (outside.read_bytes() if outside.is_file() else _wiki_bytes(outside)) == outside_before


@pytest.mark.parametrize("leaves_alias", [False, True])
def test_shared_class_name_moved_with_its_module_keeps_its_page(
    tmp_path, monkeypatch, leaves_alias
):
    project, wiki_dir = _bootstrap_project(
        tmp_path,
        monkeypatch,
        {
            "model.py": _draft_source("Model draft."),
            "other.py": _draft_source("Other draft."),
        },
    )
    # Both modules declare Draft, so each page carries its module's name.
    _author_description(wiki_dir / "entities/model_Draft.md", "Model draft.", "AUTHORED: model.")
    _sync(wiki_dir)
    (project / "engine").mkdir()
    (project / "pkg/model.py").rename(project / "engine/model.py")
    if leaves_alias:
        (project / "pkg/model.py").write_text(MODULE_ALIAS, encoding="utf-8")

    _sync(wiki_dir)

    _assert_entity_page(wiki_dir, "model_Draft", "engine/model.py", "AUTHORED: model.")
    _assert_entity_page(wiki_dir, "other_Draft", "pkg/other.py", "Other draft.")
    entity = read_md(wiki_dir / "entities/model_Draft.md")
    assert "AUTHORED: model." in entity
    assert not entity.startswith(sync_cmd._DEPRECATION_HEADER)
    assert {p.name for p in (wiki_dir / "entities").glob("*.md")} == {"model_Draft.md", "other_Draft.md"}
    _assert_consistent(wiki_dir)
    stable = {p.relative_to(wiki_dir): p.read_bytes() for p in wiki_dir.rglob("*") if p.is_file()}
    _sync(wiki_dir)
    assert {p.relative_to(wiki_dir): p.read_bytes() for p in wiki_dir.rglob("*") if p.is_file()} == stable


@pytest.mark.parametrize("dry_run", [False, True])
def test_ownership_conflict_stops_sync_before_wiki_mutation(
    tmp_path, monkeypatch, capsys, dry_run
):
    project, wiki_dir = _bootstrap_project(
        tmp_path,
        monkeypatch,
        {
            "alpha.py": _draft_source("Alpha's draft."),
            "beta.py": _draft_source("An unrelated class.", name="Other"),
        },
    )
    _author_description(
        wiki_dir / "entities/Draft.md", "Alpha's draft.", "AUTHORED: keep alpha's text."
    )
    manifest = SyncManifest.load(wiki_dir)
    manifest.sources["pkg/beta.py"]["entity_pages"]["Other"] = "Draft"
    manifest.save(wiki_dir)
    with (project / "pkg/beta.py").open("a", encoding="utf-8") as stream:
        stream.write("\n\n" + _draft_source("Beta's draft."))
    before = {
        path.relative_to(wiki_dir): path.read_bytes()
        for path in wiki_dir.rglob("*") if path.is_file()
    }
    capsys.readouterr()

    with pytest.raises(SystemExit) as exc:
        _sync(wiki_dir, dry_run=dry_run)

    assert exc.value.code == 2
    assert "Entity page ownership conflict" in capsys.readouterr().err
    assert {
        path.relative_to(wiki_dir): path.read_bytes()
        for path in wiki_dir.rglob("*") if path.is_file()
    } == before


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize("scope", ["entity", "module"])
def test_transition_preflight_preserves_all_pages_on_conflict(
    tmp_path, monkeypatch, capsys, dry_run, scope
):
    project, wiki_dir = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original description.")}
    )
    _author_description(
        wiki_dir / "entities/Draft.md", "Original description.", "AUTHORED: original owner."
    )
    if scope == "module":
        (project / "other").mkdir()
        (project / "other/model.py").write_text(
            _draft_source("Another class.", name="Other"), encoding="utf-8"
        )
        target = wiki_dir / "modules/pkg_model.md"
    else:
        (project / "pkg/composer.py").write_text(
            _draft_source("Another draft."), encoding="utf-8"
        )
        target = wiki_dir / "entities/model_Draft.md"
    target.write_text("AUTHORED: unrelated destination.", encoding="utf-8")
    before = {
        path.relative_to(wiki_dir): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in wiki_dir.rglob("*") if path.is_file()
    }
    capsys.readouterr()

    with pytest.raises(SystemExit) as exc:
        _sync(wiki_dir, dry_run=dry_run)

    assert exc.value.code == 2
    stderr = capsys.readouterr().err
    assert "Occupied target" in stderr
    assert {
        path.relative_to(wiki_dir): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in wiki_dir.rglob("*") if path.is_file()
    } == before


def test_transition_preflight_rechecks_occupied_targets_at_application(tmp_path, monkeypatch, capsys):
    project, wiki_dir = _bootstrap_project(
        tmp_path, monkeypatch, {"model.py": _draft_source("Original description.")}
    )
    (project / "pkg/composer.py").write_text(
        _draft_source("Another draft."), encoding="utf-8"
    )
    real_apply = sync_cmd._apply_prepared_sync
    snapshots = []
    locks_before = {
        wiki_dir / name: ((wiki_dir / name).read_bytes(), (wiki_dir / name).stat().st_mtime_ns)
        for name in (GOVERNANCE_LOCK_FILENAME, STORAGE_LOCK_FILENAME)
    }
    original_read = Path.read_bytes

    def locked_read(path):
        if path in locks_before:
            raise PermissionError("held Windows lock cannot be read")
        return original_read(path)

    def occupy_after_preparation(options, prepared):
        assert prepared.page_transitions is not None
        (wiki_dir / "entities/model_Draft.md").write_text("Late authored destination.", encoding="utf-8")
        with monkeypatch.context() as held_lock:
            held_lock.setattr(Path, "read_bytes", locked_read)
            for lock, before in locks_before.items():
                with pytest.raises(PermissionError, match="held Windows lock"):
                    lock.read_bytes()
                assert lock.stat().st_mtime_ns == before[1]
            snapshots.append({
                # Windows prevents reads of the locked byte. Compare that file
                # against its pre-lock bytes again after the lock is released.
                path.relative_to(wiki_dir): locks_before[path][0] if path in locks_before else path.read_bytes()
                for path in wiki_dir.rglob("*") if path.is_file()
            })
            return real_apply(options, prepared)

    monkeypatch.setattr(sync_cmd, "_apply_prepared_sync", occupy_after_preparation)
    capsys.readouterr()
    with pytest.raises(SystemExit) as exc:
        _sync(wiki_dir)
    assert exc.value.code == 2
    assert "Occupied target" in capsys.readouterr().err
    assert len(snapshots) == 1
    assert {
        path.relative_to(wiki_dir): path.read_bytes()
        for path in wiki_dir.rglob("*") if path.is_file()
    } == snapshots[0]
    assert {
        lock: (lock.read_bytes(), lock.stat().st_mtime_ns) for lock in locks_before
    } == locks_before
