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
from llm_wiki_cli.services import team
from llm_wiki_cli.services.inventory_cache import CACHE_FILENAME
from llm_wiki_cli.services.knowledge_evidence import (
    ConceptObservationBasis,
    sha256_bytes,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.paths import is_test_source_path
from llm_wiki_cli.services.sync_manifest import (
    ManifestEvidenceBaseline,
    ManifestTombstone,
    TOMBSTONE_UNKNOWN_PROVENANCE,
)


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


def test_bootstrap_records_page_mappings_with_concept_evidence(
    optional_surface_project,
):
    _project, wiki = optional_surface_project

    manifest = SyncManifest.load(wiki)

    assert set(manifest.page_source_mappings) == {
        "modules/app.md",
        "modules/core.md",
        "modules/test_api.md",
    }
    assert set(manifest.evidence_baselines) == set(manifest.page_source_mappings)
    assert all(
        baseline.is_known and baseline.basis is not None
        for baseline in manifest.evidence_baselines.values()
    )
    assert manifest.tombstones == {}
    assert manifest.artifact_hashes is not None


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
    log = (wiki / "log.md").read_text(encoding="utf-8")
    assert "### Wiki surface initialization" in log
    assert "### feat:" not in log
    manifest = json.loads((wiki / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert manifest["version"] == 5
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


def test_surface_only_sync_repairs_invalid_evidence_state_and_commits_artifact_hashes(
    optional_surface_project,
):
    project, wiki = optional_surface_project
    before = SyncManifest.load(wiki)
    page_path = "modules/app.md"
    mapping = before.page_source_mappings[page_path]
    basis = ConceptObservationBasis(
        scope=mapping.scope,
        source_path=mapping.source_path,
        extractor_ref="python-ast",
        source_content_hash=before.sources[mapping.source_path]["hash"],
        concept_observation_hash=sha256_bytes(b"app module observation"),
    )
    before.evidence_baselines[page_path] = ManifestEvidenceBaseline.from_basis(basis)
    before.tombstones["modules/Retired.md"] = ManifestTombstone(
        reason=TOMBSTONE_UNKNOWN_PROVENANCE,
        unknown_reason="manifest-state-unavailable",
    )
    (wiki / "modules" / "Retired.md").write_text(
        "# Retired\n\nRetained history.\n",
        encoding="utf-8",
    )
    before = before.with_artifact_hashes(
        surface_index_hash=sha256_bytes(b"surface index"),
        knowledge_index_hash=sha256_bytes(b"knowledge index"),
        evaluated_envelope_hash=sha256_bytes(b"evaluated envelope"),
    )
    before.save(wiki)

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("dependencies",)],
        )
    )

    after = SyncManifest.load(wiki)
    assert after.page_source_mappings == before.page_source_mappings
    assert set(after.evidence_baselines) == set(before.evidence_baselines)
    assert all(
        baseline.is_known and baseline.basis is not None
        for baseline in after.evidence_baselines.values()
    )
    repaired_basis = after.evidence_baselines[page_path].basis
    assert repaired_basis is not None
    assert repaired_basis.source_path == mapping.source_path
    assert repaired_basis.source_content_hash == after.sources[mapping.source_path][
        "hash"
    ]
    assert repaired_basis.concept_observation_hash != basis.concept_observation_hash
    assert after.tombstones == before.tombstones
    assert after.artifact_hashes is not None


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


def test_initialization_defers_removed_source_with_valid_preserved_mappings(
    optional_surface_project,
):
    project, wiki = optional_surface_project
    before_manifest = SyncManifest.load(wiki)
    before_module = (wiki / "modules" / "app.md").read_bytes()
    (project / "app.py").unlink()

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("dependencies",)],
        )
    )

    after_manifest = SyncManifest.load(wiki)
    assert after_manifest.sources == before_manifest.sources
    assert after_manifest.page_source_mappings == before_manifest.page_source_mappings
    assert after_manifest.evidence_baselines == before_manifest.evidence_baselines
    assert (wiki / "modules" / "app.md").read_bytes() == before_module
    loaded = load_knowledge_state(wiki)
    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.surface is not None
    app_page = next(
        page
        for page in loaded.surface["pages"]
        if page["canonical_path"] == "modules/app.md"
    )
    assert app_page["source_path"] == "app.py"


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
        "import core\n\n\ndef use_core():\n    return core.helper()\n",
        encoding="utf-8",
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
    assert "new_dependency" not in (wiki / "index.md").read_text(encoding="utf-8")


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


def test_manifest_v3_loads_in_legacy_mode_and_v5_round_trips(tmp_path):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / MANIFEST_FILENAME).write_text(
        json.dumps({"version": 3, "sources": {}}), encoding="utf-8"
    )
    assert SyncManifest.load(wiki).surfaces == {}

    manifest = SyncManifest(
        sources={
            "src/example.py": {
                "hash": "sha256:" + ("1" * 64),
                "semantic_hash": "sha256:" + ("2" * 64),
                "generated_semantics": {
                    "module": {
                        "description": "café",
                        "classes": {"Example": "Example class."},
                        "functions": {},
                    },
                    "entities": {
                        "Example": {
                            "description": "Example class.",
                            "attributes": {},
                            "methods": {},
                        }
                    },
                },
                "language": "python",
                "entities": ["Example"],
                "entity_pages": {"Example": "Example"},
                "entity_page_occurrences": [
                    {"name": "Example", "page": "Example", "occurrence": 1}
                ],
                "module_page": "example",
            }
        },
        surfaces={"flows": {"enabled": True, "categories": None}},
        generation_inputs={"openapi_file": "openapi.json"},
    )
    manifest.save(wiki)

    manifest_bytes = (wiki / MANIFEST_FILENAME).read_bytes()
    payload = json.loads(manifest_bytes)
    loaded = SyncManifest.load(wiki)

    assert payload == manifest.to_payload()
    assert payload["version"] == 5
    assert loaded.to_payload() == manifest.to_payload()
    assert manifest_bytes == manifest.to_json().encode("utf-8")
    assert b"caf\xc3\xa9" in manifest_bytes
    assert manifest_bytes.endswith(b"\n")
    assert not manifest_bytes.endswith(b"\n\n")


def test_team_manifest_conflict_preserves_matching_generation_state():
    state = {
        "surfaces": {"api_contracts": {"enabled": True}},
        "generation_inputs": {"openapi_file": "openapi.json"},
    }
    payload = json.dumps({"version": 4, "sources": {}, **state}, indent=2)
    conflicted = f"<<<<<<< ours\n{payload}\n=======\n{payload}\n>>>>>>> theirs\n"

    surfaces, generation_inputs, error = team._manifest_state_from_conflict(conflicted)

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

    surfaces, generation_inputs, error = team._manifest_state_from_conflict(conflicted)

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
    page_path = "modules/app.md"
    mapping = manifest.page_source_mappings[page_path]
    basis = ConceptObservationBasis(
        scope=mapping.scope,
        source_path=mapping.source_path,
        extractor_ref="python-ast",
        source_content_hash=manifest.sources[mapping.source_path]["hash"],
        concept_observation_hash=sha256_bytes(b"app module observation"),
    )
    manifest.evidence_baselines[page_path] = ManifestEvidenceBaseline.from_basis(basis)
    manifest = manifest.with_artifact_hashes(
        surface_index_hash=sha256_bytes(b"surface index"),
        knowledge_index_hash=sha256_bytes(b"knowledge index"),
        evaluated_envelope_hash=sha256_bytes(b"evaluated envelope"),
    )
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
    assert migrated.page_source_mappings[page_path] == mapping
    migrated_baseline = migrated.evidence_baselines[page_path]
    assert migrated_baseline.is_known
    assert migrated_baseline.basis is not None
    assert migrated_baseline.basis.source_content_hash == basis.source_content_hash
    assert migrated.artifact_hashes is not None


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


def test_dry_run_is_available_for_normal_sync(tmp_path, capsys):
    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        options = sync_cmd._sync_run_options_from_args(
            types.SimpleNamespace(
                src_dir=".",
                wiki_dir="wiki",
                dry_run=True,
            )
        )
    finally:
        os.chdir(old_cwd)

    assert options.dry_run is True
    assert options.initialize_surfaces == frozenset()
    assert capsys.readouterr().err == ""
