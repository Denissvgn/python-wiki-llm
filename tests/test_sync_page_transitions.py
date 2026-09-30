"""Ownership and page-transition contracts for incremental sync."""

from __future__ import annotations

from pathlib import Path

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, lint_cmd, sync_cmd
from llm_wiki_cli.services.io import read_md
from llm_wiki_cli.services.sync_manifest import SyncManifest
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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, existing_module: bool
) -> None:
    original_doc = "A draft in module alpha."
    new_doc = "A draft in module beta."
    authored = "HAND-WRITTEN: alpha alone owns this description."
    sources = {"alpha.py": _draft_source(original_doc)}
    other_source = 'class Other:\n    """Something else."""\n'
    if existing_module:
        sources["beta.py"] = other_source
    project, wiki_dir = _bootstrap_project(tmp_path, monkeypatch, sources)
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


def test_new_module_twin_preserves_original_page_owner(tmp_path, monkeypatch):
    _check_added_twin(tmp_path, monkeypatch, existing_module=False)


def test_existing_module_twin_preserves_original_page_owner(tmp_path, monkeypatch):
    _check_added_twin(tmp_path, monkeypatch, existing_module=True)
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

    def occupy_after_preparation(options, prepared):
        assert prepared.page_transitions is not None
        (wiki_dir / "entities/model_Draft.md").write_text("Late authored destination.", encoding="utf-8")
        snapshots.append({
            path.relative_to(wiki_dir): path.read_bytes()
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
