"""Selective optional-surface initialization and persistence regressions."""

from __future__ import annotations

import json
import os
import subprocess
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import bootstrap_cmd, migrate_cmd, sync_cmd
from llm_wiki_cli.commands.sync_cmd import MANIFEST_FILENAME, SyncManifest
from llm_wiki_cli.services.inventory_cache import CACHE_FILENAME
from llm_wiki_cli.services.paths import is_test_source_path
from llm_wiki_cli.services import team


def _bootstrap_args(project: Path, wiki: Path, **kwargs):
    defaults = {
        "src_dir": str(project),
        "wiki_dir": str(wiki),
        "overwrite": False,
        "depth": "full",
        "skip_workflows": True,
        "skip_flows": True,
        "skip_data_flow": False,
        "skip_dependencies": True,
        "dependency_graph_detail": "auto",
        "format": "text",
        "source_adapter": True,
        "allow_external_src": False,
        "helper_cache_dir": None,
        "include_tests": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _sync_args(project: Path, wiki: Path, **kwargs):
    defaults = {
        "src_dir": str(project),
        "wiki_dir": str(wiki),
        "initialize_surfaces": None,
        "flow_category": None,
        "exclude_tests": False,
        "dry_run": False,
        "force": False,
        "no_cache": True,
        "no_preserve_semantic": False,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write_project(project: Path) -> None:
    (project / "tests").mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        '[project]\nname = "surface-project"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (project / "core.py").write_text(
        "def helper():\n    return 'ok'\n",
        encoding="utf-8",
    )
    (project / "app.py").write_text(
        textwrap.dedent(
            """\
            import core

            __all__ = ["public_api"]


            @app.get("/prod")
            def production_endpoint():
                return core.helper()


            def public_api():
                return core.helper()
            """
        ),
        encoding="utf-8",
    )
    (project / "tests" / "test_api.py").write_text(
        textwrap.dedent(
            """\
            @app.get("/test-only")
            def test_endpoint():
                return {"test": True}
            """
        ),
        encoding="utf-8",
    )


@pytest.fixture
def optional_surface_project(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(["git", "init", str(project)], check=True, capture_output=True)
    _write_project(project)
    wiki = project / "docs" / "llm_wiki"
    monkeypatch.chdir(project)
    bootstrap_cmd.run(_bootstrap_args(project, wiki))
    capsys.readouterr()
    return project, wiki


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_cli_accepts_surface_selection_and_preview_flags(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.sync_cmd,
        "run",
        lambda args: seen.update(
            surfaces=args.initialize_surfaces,
            categories=args.flow_category,
            exclude_tests=args.exclude_tests,
            dry_run=args.dry_run,
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "sync",
            "--initialize-surfaces",
            "flows,dependencies,api-contracts",
            "--flow-category",
            "http",
            "--exclude-tests",
            "--dry-run",
        ],
    )

    cli.main()

    assert seen == {
        "surfaces": [("flows", "dependencies", "api-contracts")],
        "categories": ["http"],
        "exclude_tests": True,
        "dry_run": True,
    }


def test_dry_run_reports_exact_plan_without_modifying_wiki(
    optional_surface_project, capsys
):
    project, wiki = optional_surface_project
    before = _tree_bytes(wiki)
    cache_path = project / ".git" / CACHE_FILENAME
    assert not cache_path.exists()

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("flows", "dependencies", "api-contracts")],
            flow_category=["http"],
            exclude_tests=True,
            dry_run=True,
            no_cache=False,
        )
    )

    output = capsys.readouterr().out
    assert "flows: 1 create (http: 1)" in output
    assert "dependency architecture: 2 create" in output
    assert "ancillary files considered: index.md, log.md" in output
    assert "DRY-RUN: no files modified." in output
    assert _tree_bytes(wiki) == before
    assert not cache_path.exists()


def test_flow_policy_persists_and_later_sync_does_not_expand_scope(
    optional_surface_project, capsys
):
    project, wiki = optional_surface_project
    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("flows",)],
            flow_category=["http"],
            exclude_tests=True,
        )
    )

    assert (wiki / "flows" / "http-production_endpoint.md").is_file()
    assert not (wiki / "flows" / "http-test_endpoint.md").exists()
    assert not (wiki / "flows" / "api-public_api.md").exists()
    manifest = json.loads((wiki / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest["version"] == 4
    assert manifest["surfaces"]["flows"] == {
        "enabled": True,
        "categories": ["http"],
        "exclude_tests": True,
    }

    with (project / "app.py").open("a", encoding="utf-8") as handle:
        handle.write(
            textwrap.dedent(
                """

                @app.get("/second")
                def second_endpoint():
                    return core.helper()
                """
            )
        )
    capsys.readouterr()
    sync_cmd.run(_sync_args(project, wiki))

    assert (wiki / "flows" / "http-second_endpoint.md").is_file()
    assert not (wiki / "flows" / "http-test_endpoint.md").exists()
    assert not (wiki / "flows" / "api-public_api.md").exists()


def test_persisted_policy_recreates_missing_surface_without_source_diff(
    optional_surface_project,
):
    project, wiki = optional_surface_project
    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("flows",)],
            flow_category=["http"],
            exclude_tests=True,
        )
    )
    flow = wiki / "flows" / "http-production_endpoint.md"
    flow.unlink()

    sync_cmd.run(_sync_args(project, wiki))

    assert flow.is_file()


def test_dependency_initialization_is_selective_and_preserves_semantic_pages(
    optional_surface_project,
):
    project, wiki = optional_surface_project
    module_path = wiki / "modules" / "app.md"
    entity_snapshot = _tree_bytes(wiki / "entities")
    module_snapshot = _tree_bytes(wiki / "modules")
    original = module_path.read_text(encoding="utf-8")
    module_path.write_text(original + "\nHuman module note.\n", encoding="utf-8")
    module_snapshot["app.md"] = module_path.read_bytes()

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("dependencies",)],
            exclude_tests=True,
        )
    )

    assert (wiki / "dependencies.md").is_file()
    assert (wiki / "load-order.md").is_file()
    assert "test_api" not in (wiki / "dependencies.md").read_text(encoding="utf-8")
    assert _tree_bytes(wiki / "entities") == entity_snapshot
    assert _tree_bytes(wiki / "modules") == module_snapshot
    manifest = SyncManifest.load(wiki)
    assert manifest.surfaces["dependencies"] == {
        "enabled": True,
        "exclude_tests": True,
    }


def test_explicit_initialization_seeds_old_wiki_and_applies_in_one_run(
    optional_surface_project, capsys
):
    project, wiki = optional_surface_project
    (wiki / MANIFEST_FILENAME).unlink()

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("dependencies", "api-contracts")],
            dry_run=True,
        )
    )
    assert not (wiki / MANIFEST_FILENAME).exists()
    assert not (wiki / "dependencies.md").exists()
    assert "manifest: seed" in capsys.readouterr().out

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("dependencies", "api-contracts")],
        )
    )

    assert (wiki / "dependencies.md").is_file()
    assert (wiki / "load-order.md").is_file()
    manifest = SyncManifest.load(wiki)
    assert manifest.surfaces["dependencies"]["enabled"] is True
    assert manifest.surfaces["api_contracts"] == {"enabled": True}


def test_initialization_defers_source_diff_and_keeps_manifest_hashes(
    optional_surface_project, capsys
):
    project, wiki = optional_surface_project
    before_manifest = SyncManifest.load(wiki)
    before_modules = _tree_bytes(wiki / "modules")
    with (project / "app.py").open("a", encoding="utf-8") as handle:
        handle.write("\n\ndef newly_changed_source():\n    return 1\n")

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("dependencies",)],
        )
    )

    after_manifest = SyncManifest.load(wiki)
    assert after_manifest.sources == before_manifest.sources
    assert _tree_bytes(wiki / "modules") == before_modules
    assert (wiki / "dependencies.md").is_file()
    assert "Deferred source changes: 1 file(s)." in capsys.readouterr().out


def test_initialization_creates_only_missing_flows_and_indexes_existing_pages(
    optional_surface_project,
):
    project, wiki = optional_surface_project
    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("flows",)],
            flow_category=["http"],
            exclude_tests=True,
        )
    )
    existing_flow = wiki / "flows" / "http-production_endpoint.md"
    before_flow = existing_flow.read_bytes()

    (project / "new_module.py").write_text(
        "def helper():\n    return 'new'\n", encoding="utf-8"
    )
    app_path = project / "app.py"
    source = app_path.read_text(encoding="utf-8")
    source = source.replace("import core", "import core\nimport new_module")
    source = source.replace(
        "def production_endpoint():\n    return core.helper()",
        "def production_endpoint():\n    return new_module.helper()",
    )
    source += "\n\n@app.get('/new')\ndef new_endpoint():\n    return core.helper()\n"
    app_path.write_text(source, encoding="utf-8")

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("flows",)],
            flow_category=["http"],
            exclude_tests=True,
        )
    )

    assert (wiki / "flows" / "http-new_endpoint.md").is_file()
    assert existing_flow.read_bytes() == before_flow
    assert not (wiki / "modules" / "new_module.md").exists()
    assert "new_module" not in (wiki / "index.md").read_text(encoding="utf-8")


def test_dependency_policy_change_does_not_regenerate_existing_pages_from_deferred_source(
    optional_surface_project,
):
    project, wiki = optional_surface_project
    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("dependencies",)],
            exclude_tests=False,
        )
    )
    dependencies = wiki / "dependencies.md"
    load_order = wiki / "load-order.md"
    before = (dependencies.read_bytes(), load_order.read_bytes())
    (project / "new_dependency.py").write_text(
        "import core\n", encoding="utf-8"
    )

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("dependencies",)],
            exclude_tests=True,
        )
    )

    assert (dependencies.read_bytes(), load_order.read_bytes()) == before
    assert "new_dependency" not in (wiki / "index.md").read_text(
        encoding="utf-8"
    )


def test_initialization_does_not_apply_other_persisted_surface_policies(
    optional_surface_project,
):
    project, wiki = optional_surface_project
    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("flows",)],
            flow_category=["http"],
            exclude_tests=True,
        )
    )
    with (project / "app.py").open("a", encoding="utf-8") as handle:
        handle.write(
            "\n\n@app.get('/deferred')\ndef deferred_endpoint():\n    return 1\n"
        )

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("dependencies",)],
        )
    )

    assert not (wiki / "flows" / "http-deferred_endpoint.md").exists()
    assert (wiki / "dependencies.md").is_file()


def test_manifest_v3_loads_in_legacy_mode_and_v4_round_trips(tmp_path):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / MANIFEST_FILENAME).write_text(
        json.dumps({"version": 3, "sources": {}}), encoding="utf-8"
    )
    assert SyncManifest.load(wiki).surfaces == {}

    manifest = SyncManifest(
        surfaces={"flows": {"enabled": True, "categories": None}},
        generation_inputs={"openapi_file": "openapi.json"},
    )
    manifest.save(wiki)

    payload = json.loads((wiki / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert payload["version"] == 4
    assert SyncManifest.load(wiki).surfaces == manifest.surfaces
    assert SyncManifest.load(wiki).generation_inputs == manifest.generation_inputs


def test_team_manifest_conflict_preserves_matching_generation_state():
    state = {
        "surfaces": {"api_contracts": {"enabled": True}},
        "generation_inputs": {"openapi_file": "openapi.json"},
    }
    payload = json.dumps({"version": 4, "sources": {}, **state}, indent=2)
    conflicted = f"<<<<<<< ours\n{payload}\n=======\n{payload}\n>>>>>>> theirs\n"

    surfaces, generation_inputs, error = team._manifest_state_from_conflict(
        conflicted
    )

    assert error == ""
    assert surfaces == state["surfaces"]
    assert generation_inputs == state["generation_inputs"]


def test_manifest_repair_preserves_surface_and_generation_state(
    optional_surface_project,
):
    project, wiki = optional_surface_project
    manifest = SyncManifest.load(wiki)
    manifest.surfaces = {"api_contracts": {"enabled": True}}
    manifest.generation_inputs = {"openapi_file": "openapi.json"}
    next(iter(manifest.sources.values()))["hash"] = "invalid"
    manifest.save(wiki)

    sync_cmd.run(_sync_args(project, wiki))

    repaired = SyncManifest.load(wiki)
    assert repaired.surfaces == manifest.surfaces
    assert repaired.generation_inputs == manifest.generation_inputs


def test_manifest_conflict_does_not_silently_undo_explicit_openapi_clear():
    conflicted = "\n".join(
        [
            "{",
            '  "version": 4,',
            '  "sources": {},',
            "<" * 7 + " HEAD",
            '  "generation_inputs": {}',
            "=" * 7,
            '  "generation_inputs": {"openapi": {"path": "openapi.yaml"}}',
            ">" * 7 + " feature",
            "}",
        ]
    )

    surfaces, generation_inputs, error = team._manifest_state_from_conflict(
        conflicted
    )

    assert surfaces is None
    assert generation_inputs is None
    assert error == "manifest generation inputs differ and require manual resolution"


def test_migrate_preserves_surface_and_generation_state(
    optional_surface_project,
):
    project, wiki = optional_surface_project
    manifest = SyncManifest.load(wiki)
    manifest.surfaces = {"api_contracts": {"enabled": True}}
    manifest.generation_inputs = {"openapi_file": "openapi.json"}
    manifest.save(wiki)

    migrate_cmd.run(
        types.SimpleNamespace(
            src_dir=str(project),
            wiki_dir=str(wiki),
            dry_run=False,
            chunk_size=None,
            chunk=None,
            plan_chunks=False,
        )
    )

    migrated = SyncManifest.load(wiki)
    assert migrated.surfaces == manifest.surfaces
    assert migrated.generation_inputs == manifest.generation_inputs


def test_surface_guard_uses_page_count_and_ratio(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "modules").mkdir(parents=True)
    for index in range(10):
        (wiki / "modules" / f"module-{index}.md").write_text(
            "# Page\n", encoding="utf-8"
        )
    plan = sync_cmd._SurfaceInitializationPlan(
        surfaces={},
        policy_changed=False,
        flow_entries=tuple({"id": f"http-{index}"} for index in range(4)),
        new_flow_entries=tuple({"id": f"http-{index}"} for index in range(4)),
        excluded_flow_tests=0,
        dependency_inventory={},
        dependency_analysis=None,
        dependency_target_pages=(),
        new_dependency_pages=(),
        requested_surfaces=frozenset({"flows"}),
    )

    assert "30% safety limit" in sync_cmd._large_surface_message(plan, wiki)


@pytest.mark.parametrize(
    "path",
    [
        "tests/test_api.py",
        r"tests\integration\handler.py",
        "src/widget.spec.ts",
        "pkg/main_test.go",
        "conftest.py",
    ],
)
def test_cross_platform_test_path_classification(path):
    assert is_test_source_path(path)


def test_flow_category_requires_explicit_flow_initialization(tmp_path, capsys):
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        with pytest.raises(SystemExit) as exc:
            sync_cmd._sync_run_options_from_args(
                types.SimpleNamespace(
                    src_dir=".",
                    wiki_dir="wiki",
                    initialize_surfaces=[("dependencies",)],
                    flow_category=["http"],
                )
            )
    finally:
        os.chdir(old_cwd)

    assert exc.value.code == 2
    assert "requires --initialize-surfaces flows" in capsys.readouterr().err


def test_dry_run_requires_surface_initialization(tmp_path, capsys):
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        with pytest.raises(SystemExit) as exc:
            sync_cmd._sync_run_options_from_args(
                types.SimpleNamespace(
                    src_dir=".",
                    wiki_dir="wiki",
                    dry_run=True,
                )
            )
    finally:
        os.chdir(old_cwd)

    assert exc.value.code == 2
    assert "--dry-run requires --initialize-surfaces" in capsys.readouterr().err
