"""Tests for commands/sync_cmd.py — incremental wiki sync."""

import ast
import inspect
import json
import os
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import (
    bootstrap_cmd,
    knowledge_cmd,
    lint_cmd,
    sync_cmd,
)
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.commands.sync_cmd import (
    MANIFEST_FILENAME,
    SyncManifest,
    _compute_diff,
    _hash_file,
)
from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.services import knowledge_orchestration, plugins
from llm_wiki_cli.services.contracts import SECTION_OWNERSHIP_EXTENSION_KEY
from llm_wiki_cli.services.extraction_jobs import ExtractionJobPlan
from llm_wiki_cli.services.inventory_cache import CACHE_FILENAME, InventoryCacheStats
from llm_wiki_cli.services.knowledge_governance import (
    current_review_evidence,
    evaluate_review_event,
    load_governance,
    review_scope_hash,
)
from llm_wiki_cli.services.knowledge_evidence import (
    is_valid_sha256,
    semantic_hash_for_file,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.sync_manifest import (
    MANIFEST_FILENAME as SERVICE_MANIFEST_FILENAME,
)
from llm_wiki_cli.services.sync_manifest import (
    PRODUCER_BASIS_INCOMPATIBLE,
    TOMBSTONE_UNKNOWN_PROVENANCE,
    ManifestEvidenceBaseline,
)
from llm_wiki_cli.services.sync_manifest import (
    SyncManifest as ServiceSyncManifest,
)
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_bootstrap_args(**kwargs):
    defaults = {
        "src_dir": ".",
        "wiki_dir": "docs/llm_wiki",
        "overwrite": False,
        "depth": "full",
        "skip_workflows": True,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _make_sync_args(**kwargs):
    defaults = {"src_dir": ".", "wiki_dir": "docs/llm_wiki"}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    assert isinstance(function_node, ast.FunctionDef)
    body = [
        stmt
        for stmt in function_node.body
        if not (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        )
    ]
    first_body_line = min(stmt.lineno for stmt in body)
    last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
    return last_body_line - first_body_line + 1


def _write_entrypoint_detector_plugin(root: Path, *, body: str) -> None:
    plugin_dir = root / "vendor" / "detector-plugin"
    plugin_dir.mkdir(parents=True)
    module_name = "detectors_" + "_".join(root.parts[-3:])
    module_name = "".join(
        ch if ch.isalnum() or ch == "_" else "_" for ch in module_name
    )
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        textwrap.dedent(f"""\
        {{
          "id": "detector-plugin",
          "version": "0.1.0",
          "llm_wiki_version": "*",
          "components": [
            {{
              "type": "entrypoint_detector",
              "id": "worker",
              "entry_point": "{module_name}:detect"
            }}
          ]
        }}
        """),
        encoding="utf-8",
    )
    (plugin_dir / f"{module_name}.py").write_text(
        textwrap.dedent(body), encoding="utf-8"
    )
    plugins.install_plugin(str(plugin_dir), root=root, yes=True)


def _write_diagram_style_plugin(root: Path, *, body: str) -> None:
    plugin_dir = root / "vendor" / "diagram-style-plugin"
    plugin_dir.mkdir(parents=True)
    module_name = "styles_" + "_".join(root.parts[-3:])
    module_name = "".join(
        ch if ch.isalnum() or ch == "_" else "_" for ch in module_name
    )
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        textwrap.dedent(f"""\
        {{
          "id": "diagram-style-plugin",
          "version": "0.1.0",
          "llm_wiki_version": "*",
          "components": [
            {{
              "type": "diagram_style",
              "id": "brand",
              "entry_point": "{module_name}:style"
            }}
          ]
        }}
        """),
        encoding="utf-8",
    )
    (plugin_dir / f"{module_name}.py").write_text(
        textwrap.dedent(body), encoding="utf-8"
    )
    plugins.install_plugin(str(plugin_dir), root=root, yes=True)


def _write_toy_extractor_plugin(root: Path) -> None:
    plugin_dir = root / "vendor" / "toy-extractor-plugin"
    plugin_dir.mkdir(parents=True)
    module_name = "toy_extractor_" + "_".join(root.parts[-3:])
    module_name = "".join(
        ch if ch.isalnum() or ch == "_" else "_" for ch in module_name
    )
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        textwrap.dedent(f"""\
        {{
          "id": "toy-extractor",
          "version": "0.1.0",
          "llm_wiki_version": "*",
          "components": [
            {{
              "type": "extractor",
              "id": "toy",
              "language": "javascript",
              "entry_point": "{module_name}:ToyExtractor",
              "parallel_safe": false
            }}
          ]
        }}
        """),
        encoding="utf-8",
    )
    (plugin_dir / f"{module_name}.py").write_text(
        textwrap.dedent("""\
        from pathlib import Path


        class ToyExtractor:
            def extract(self, src_dir, only_files=None, deep=False):
                files = sorted(Path(src_dir).glob("*.jscustom"))
                if only_files is not None:
                    selected = set(only_files)
                    files = [path for path in files if path.name in selected]
                return {
                    path.name: {
                        "language": "javascript",
                        "classes": [],
                        "functions": [{"name": path.stem, "line": 1}],
                        "imports": [],
                    }
                    for path in files
                }
        """),
        encoding="utf-8",
    )
    plugins.install_plugin(str(plugin_dir), root=root, yes=True)


class TestSyncRunStructure:
    def test_run_stays_a_small_coordinator(self):
        assert _body_line_count(sync_cmd.run) <= 40

    def test_apply_diff_stays_decomposed(self):
        assert _body_line_count(sync_cmd._apply_diff) <= 40


@pytest.fixture
def bootstrapped_project(tmp_path):
    """A project that has been fully bootstrapped with a manifest."""
    import subprocess

    proj = tmp_path / "project"
    proj.mkdir()

    subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(proj), "config", "user.email", "t@t.com"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(proj), "config", "user.name", "T"],
        capture_output=True,
        check=True,
    )

    (proj / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "0.1.0"\n'
    )
    (proj / "models.py").write_text(
        textwrap.dedent("""\
            class User:
                \"\"\"A system user.\"\"\"
                name: str = ""
                email: str = ""
        """)
    )

    wiki_dir = proj / "docs" / "llm_wiki"
    old_cwd = os.getcwd()
    os.chdir(proj)

    bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))
    # Write manifest so sync can run
    _write_manifest_from_bootstrap(proj, wiki_dir)

    yield proj, wiki_dir
    os.chdir(old_cwd)


def _write_manifest_from_bootstrap(proj: Path, wiki_dir: Path) -> None:
    """Write a .llm-wiki-manifest.json for the current state of proj."""
    from llm_wiki_cli.commands.extract_cmd import get_inventory
    from llm_wiki_cli.commands.sync_cmd import (
        SyncManifest,
        _collision_maps,
        _page_name_for_module,
    )

    inventory = get_inventory(str(proj), deep=True)
    colliding_stems, colliding_cls, entity_page_cache = _collision_maps(
        inventory, str(proj)
    )
    module_page_map = {fp: _page_name_for_module(fp) for fp in inventory}
    manifest = SyncManifest.build_from_inventory(
        inventory, str(proj), entity_page_cache, module_page_map
    )
    manifest.save(wiki_dir)


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_sync_manifest_command_import_is_a_compatibility_reexport():
    assert SyncManifest is ServiceSyncManifest
    assert MANIFEST_FILENAME == SERVICE_MANIFEST_FILENAME
    assert sync_cmd.SyncManifest is ServiceSyncManifest
    assert sync_cmd.MANIFEST_VERSION == 5


def test_shared_evidence_preserves_manifest_v4_semantic_hash_bytes():
    expected = "sha256:0162de6dd06ce9b209c525ce4b845a54c2463f32bc327739343ea2cf551e401c"

    assert semantic_hash_for_file({"docstring": "café", "line": 1}) == expected
    assert semantic_hash_for_file({"line": 99, "docstring": "café"}) == expected
    assert is_valid_sha256(expected)
    assert not is_valid_sha256(expected.upper())
    assert not is_valid_sha256("sha256:abc")
    assert not is_valid_sha256(None)


def test_service_manifest_preserves_occurrence_map_fallback(tmp_path):
    inventory = {
        "pkg_a/models.py": {
            "language": "python",
            "classes": [{"name": "User"}, {"name": "User"}],
        },
        "pkg_b/models.py": {
            "language": "python",
            "classes": [{"name": "User"}],
        },
    }
    module_page_map = bootstrap_cmd.build_module_page_map(inventory)
    entity_page_map = bootstrap_cmd.build_entity_page_map(inventory)
    expected = bootstrap_cmd.build_entity_occurrence_page_map(
        inventory, module_page_map
    )

    manifest = ServiceSyncManifest.build_from_inventory(
        inventory,
        str(tmp_path),
        entity_page_map,
        module_page_map,
    )

    actual = {
        (entry["name"], filepath, entry["occurrence"]): entry["page"]
        for filepath, source in manifest.sources.items()
        for entry in source["entity_page_occurrences"]
    }
    assert actual == expected

    empty_module_map_manifest = ServiceSyncManifest.build_from_inventory(
        inventory,
        str(tmp_path),
        entity_page_map,
        {},
    )
    empty_module_map_actual = {
        (entry["name"], filepath, entry["occurrence"]): entry["page"]
        for filepath, source in empty_module_map_manifest.sources.items()
        for entry in source["entity_page_occurrences"]
    }
    assert empty_module_map_actual == expected


def test_service_manifest_load_preserves_missing_and_malformed_behavior(tmp_path):
    wiki_dir = tmp_path / "wiki"

    with pytest.raises(FileNotFoundError):
        ServiceSyncManifest.load(wiki_dir)

    wiki_dir.mkdir()
    manifest_path = wiki_dir / SERVICE_MANIFEST_FILENAME
    manifest_path.write_text("{", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        ServiceSyncManifest.load(wiki_dir)

    manifest_path.write_bytes(b"\xff")
    with pytest.raises(UnicodeDecodeError):
        ServiceSyncManifest.load(wiki_dir)


def test_service_manifest_load_keeps_legacy_optional_mapping_defaults(tmp_path):
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    (wiki_dir / SERVICE_MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "version": 3,
                "sources": {},
                "surfaces": [],
                "generation_inputs": None,
            }
        ),
        encoding="utf-8",
    )

    manifest = ServiceSyncManifest.load(wiki_dir)

    assert manifest.sources == {}
    assert manifest.surfaces == {}
    assert manifest.generation_inputs == {}


class TestNoManifest:
    """sync exits 1 with a clear message when no manifest exists."""

    def test_exits_one_and_prints_error(self, tmp_path, capsys):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        wiki_dir.mkdir(parents=True)
        args = _make_sync_args(src_dir=str(tmp_path), wiki_dir=str(wiki_dir))

        old_cwd = os.getcwd()
        os.chdir(tmp_path)  # validate_path checks relative to cwd
        try:
            with pytest.raises(SystemExit) as exc_info:
                sync_cmd.run(args)
        finally:
            os.chdir(old_cwd)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "bootstrap" in captured.err.lower()
        assert MANIFEST_FILENAME in captured.err


class TestSyncSurfaceIndex:
    def test_noop_sync_preserves_canonical_markdown_with_knowledge_sidecars(
        self, bootstrapped_project, capsys
    ):
        proj, wiki_dir = bootstrapped_project
        before = {
            path.relative_to(wiki_dir).as_posix(): path.read_bytes()
            for path in sorted(wiki_dir.rglob("*.md"))
        }
        capsys.readouterr()

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        after = {
            path.relative_to(wiki_dir).as_posix(): path.read_bytes()
            for path in sorted(wiki_dir.rglob("*.md"))
        }
        assert after == before
        assert (wiki_dir / ".llm-wiki-knowledge.json").is_file()
        surface = json.loads(
            (wiki_dir / SURFACE_INDEX_FILENAME).read_text(encoding="utf-8")
        )
        assert surface["schema_version"] == "llm-wiki-surface-index/v1"

    def test_sync_regenerates_missing_surface_index_without_source_changes(
        self, bootstrapped_project, capsys
    ):
        proj, wiki_dir = bootstrapped_project
        surface_path = wiki_dir / SURFACE_INDEX_FILENAME
        surface_path.unlink()

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        assert surface_path.exists()
        data = json.loads(surface_path.read_text(encoding="utf-8"))
        assert data["schema_version"] == "llm-wiki-surface-index/v1"
        assert data["counts"]["by_kind"]["entities"] == 1
        assert "Wiki is up to date." in capsys.readouterr().out

    def test_sync_links_new_guide_page_without_source_changes(
        self, bootstrapped_project, capsys
    ):
        """Regression (2026-07-04): found while dogfooding the
        ``onboarding-guide`` skill. Adding a guide page touches no source
        file, so ``_compute_sync_diff`` sees no changes and
        ``_finish_if_no_changes`` used to return before index.md's
        ``## Guides`` section was ever regenerated — the new guide stayed
        permanently unlinked (and permanently flagged ``orphan_pages`` by
        lint) until some unrelated source change next triggered a real sync.
        The guides surface contract promises sync always keeps guide links
        current; this must hold on the no-op path too.
        """
        proj, wiki_dir = bootstrapped_project
        capsys.readouterr()

        guides_dir = wiki_dir / "guides"
        guides_dir.mkdir(parents=True, exist_ok=True)
        (guides_dir / "operator-onboarding.md").write_text(
            "# Operator onboarding\n", encoding="utf-8"
        )

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        out = capsys.readouterr().out
        assert "Wiki is up to date." in out
        index = (wiki_dir / "index.md").read_text(encoding="utf-8")
        assert "| Guides | 1 | [Open section](#guides) |" in index
        assert "[Operator onboarding](guides/operator-onboarding.md)" in index
        assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID

    def test_sync_leaves_agent_owned_assets_untouched(
        self, bootstrapped_project, capsys
    ):
        proj, wiki_dir = bootstrapped_project
        assets_dir = wiki_dir / "assets" / "guides" / "operator-onboarding"
        assets_dir.mkdir(parents=True)
        asset = assets_dir / "terminal.png"
        asset.write_bytes(b"agent-owned-media")
        before = asset.read_bytes()
        capsys.readouterr()

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        assert asset.exists()
        assert asset.read_bytes() == before
        assert "Wiki is up to date." in capsys.readouterr().out


class TestSeedManifest:
    """When no manifest exists but a wiki does, sync seeds a baseline manifest."""

    @pytest.mark.parametrize(
        "retained_page",
        ("modules/Retired.md", "entities/Retired.md"),
    )
    def test_deleted_manifest_reseed_records_unmapped_retained_page_tombstone(
        self,
        bootstrapped_project,
        retained_page,
        monkeypatch,
        capsys,
    ):
        proj, wiki_dir = bootstrapped_project
        retained_path = wiki_dir / retained_page
        retained_path.write_text(
            "# Retired\n\nHuman-maintained history.\n",
            encoding="utf-8",
        )
        before = retained_path.read_bytes()
        (wiki_dir / MANIFEST_FILENAME).unlink()
        capsys.readouterr()
        monkeypatch.setattr(
            sync_cmd,
            "write_md",
            lambda *args, **kwargs: pytest.fail(
                "manifest reseed must not rewrite retained wiki pages"
            ),
        )

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        assert retained_path.read_bytes() == before
        seeded = SyncManifest.load(wiki_dir)
        assert retained_page not in seeded.page_source_mappings
        assert retained_page not in seeded.evidence_baselines
        assert seeded.tombstones[retained_page].to_payload() == {
            "reason": "unknown-provenance",
            "unknown_reason": "manifest-state-unavailable",
        }
        output = capsys.readouterr().out.lower()
        assert "seeding" in output
        assert "unknown provenance: 1" in output

    def test_seeds_manifest_when_wiki_exists(self, tmp_path, capsys):
        """sync creates a manifest without modifying any wiki pages."""
        import subprocess

        proj = tmp_path / "project"
        proj.mkdir()
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.email", "t@t.com"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.name", "T"],
            capture_output=True,
            check=True,
        )
        (proj / "models.py").write_text("class User:\n    name: str = ''\n")

        wiki_dir = proj / "docs" / "llm_wiki"
        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            # Bootstrap without manifest (simulate old version)
            bootstrap_cmd.run(
                _make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
            )
            # Remove the manifest that new bootstrap creates
            (wiki_dir / MANIFEST_FILENAME).unlink(missing_ok=True)
            assert not (wiki_dir / MANIFEST_FILENAME).exists()

            # Record existing page content
            entity_before = (wiki_dir / "entities" / "User.md").read_text(
                encoding="utf-8"
            )

            # Run sync — should seed, not fail
            args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
            sync_cmd.run(args)

            # Manifest now exists
            assert (wiki_dir / MANIFEST_FILENAME).exists()

            # Pages were NOT modified
            entity_after = (wiki_dir / "entities" / "User.md").read_text(
                encoding="utf-8"
            )
            assert entity_after == entity_before

            captured = capsys.readouterr()
            assert "seeding" in captured.out.lower()
        finally:
            os.chdir(old_cwd)

    def test_seed_then_sync_detects_changes(self, tmp_path, capsys):
        """After seeding, a source change is detected by the next sync."""
        import subprocess

        proj = tmp_path / "project"
        proj.mkdir()
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.email", "t@t.com"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.name", "T"],
            capture_output=True,
            check=True,
        )
        (proj / "models.py").write_text("class User:\n    name: str = ''\n")

        wiki_dir = proj / "docs" / "llm_wiki"
        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            bootstrap_cmd.run(
                _make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
            )
            (wiki_dir / MANIFEST_FILENAME).unlink(missing_ok=True)

            # Seed manifest
            sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))
            capsys.readouterr()  # clear output

            # Modify source
            (proj / "models.py").write_text(
                "class User:\n    name: str = ''\n    email: str = ''\n"
            )

            # Next sync should detect the change
            sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))
            captured = capsys.readouterr()
            assert (
                "1 updated" in captured.out.lower()
                or "1 created" in captured.out.lower()
                or "sync complete" in captured.out.lower()
            )
        finally:
            os.chdir(old_cwd)

    def test_still_errors_without_wiki(self, tmp_path, capsys):
        """If neither manifest nor wiki index exists, still exit 1."""
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        wiki_dir.mkdir(parents=True)
        # No index.md → should still fail
        args = _make_sync_args(src_dir=str(tmp_path), wiki_dir=str(wiki_dir))

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(SystemExit) as exc_info:
                sync_cmd.run(args)
            assert exc_info.value.code == 1
        finally:
            os.chdir(old_cwd)

    def test_empty_inventory_reseed_records_retained_pages_as_unknown(
        self, tmp_path, monkeypatch, capsys
    ):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        (wiki_dir / "modules").mkdir(parents=True)
        (wiki_dir / "entities").mkdir()
        (wiki_dir / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki_dir / "modules" / "Retired.md").write_text(
            "# Retired module\n", encoding="utf-8"
        )
        (wiki_dir / "entities" / "Former.md").write_text(
            "# Former entity\n", encoding="utf-8"
        )
        monkeypatch.setattr(
            sync_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
            ),
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            sync_cmd.run(_make_sync_args(src_dir=str(tmp_path), wiki_dir=str(wiki_dir)))
        finally:
            os.chdir(old_cwd)

        seeded = SyncManifest.load(wiki_dir)
        assert seeded.sources == {}
        assert set(seeded.tombstones) == {
            "modules/Retired.md",
            "entities/Former.md",
        }
        assert all(
            tombstone.to_payload()
            == {
                "reason": "unknown-provenance",
                "unknown_reason": "manifest-state-unavailable",
            }
            for tombstone in seeded.tombstones.values()
        )
        assert load_knowledge_state(wiki_dir).status is KnowledgeLoadState.VALID
        output = capsys.readouterr().out.lower()
        assert "manifest written" in output
        assert "unknown provenance: 2" in output


class TestManifestLanguage:
    def test_old_manifest_load_infers_language(self, tmp_path):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        wiki_dir.mkdir(parents=True)
        (wiki_dir / MANIFEST_FILENAME).write_text(
            json.dumps(
                {
                    "version": 1,
                    "sources": {
                        "models.py": {
                            "hash": "sha256:x",
                            "entities": [],
                            "module_page": "models",
                        },
                        "web/app.tsx": {
                            "hash": "sha256:y",
                            "entities": [],
                            "module_page": "app",
                        },
                    },
                }
            )
        )

        manifest = SyncManifest.load(wiki_dir)

        assert manifest.sources["models.py"]["language"] == "python"
        assert manifest.sources["web/app.tsx"]["language"] == "typescript"


class TestSyncInventoryRuntime:
    def _write_empty_manifest(self, wiki_dir: Path) -> None:
        wiki_dir.mkdir(parents=True, exist_ok=True)
        SyncManifest().save(wiki_dir)

    def test_passes_cache_options_and_jobs(self, tmp_path, monkeypatch, capsys):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        self._write_empty_manifest(wiki_dir)
        seen = {}
        events = []
        real_reporter = sync_cmd.print_extraction_job_plan

        def recording_reporter(plan):
            events.append("report")
            real_reporter(plan)

        monkeypatch.setattr(sync_cmd, "print_extraction_job_plan", recording_reporter)

        def fake_inventory(*args, **kwargs):
            seen["cache_options"] = kwargs["cache_options"]
            seen["helper_cache_dir"] = kwargs["helper_cache_dir"]
            seen["include_tests"] = kwargs["include_tests"]
            seen["parallel_jobs"] = kwargs["parallel_jobs"]
            seen["job_request"] = kwargs["job_request"]
            kwargs["plan_reporter"](ExtractionJobPlan(requested_jobs=2))
            events.append("work")
            return InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
                InventoryCacheStats(enabled=False, status="disabled"),
            )

        monkeypatch.setattr(sync_cmd, "get_inventory_result", fake_inventory)
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            sync_cmd.run(
                _make_sync_args(
                    src_dir=str(tmp_path),
                    wiki_dir=str(wiki_dir),
                    no_cache=True,
                    rebuild_cache=True,
                    cache_stats=True,
                    cache_dir=str(tmp_path / "cache"),
                    helper_cache_dir=str(tmp_path / "helper-cache"),
                    include_tests=["go"],
                    jobs=2,
                )
            )
        finally:
            os.chdir(old_cwd)

        assert seen["parallel_jobs"] == 2
        assert seen["job_request"].requested_jobs == 2
        assert seen["job_request"].resolved_jobs == 2
        assert events == ["report", "work"]
        assert seen["cache_options"].enabled is False
        assert seen["cache_options"].rebuild is True
        assert seen["cache_options"].stats_enabled is True
        assert seen["cache_options"].cache_dir == str(tmp_path / "cache")
        assert seen["helper_cache_dir"] == str(tmp_path / "helper-cache")
        assert seen["include_tests"] == ["go"]
        assert capsys.readouterr().err.count("Extractor plan:") == 1

    def test_include_tests_go_creates_go_test_module_and_manifest_entry(
        self, tmp_path, monkeypatch, capsys
    ):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        self._write_empty_manifest(wiki_dir)
        (tmp_path / "main_test.go").write_text(
            "package main\n\nfunc TestMain() {}\n", encoding="utf-8"
        )
        seen = {}
        real_build_source_snapshot = sync_cmd.build_source_snapshot

        def fake_snapshot(src_dir, **kwargs):
            seen["snapshot_include_tests"] = kwargs.get("include_tests")
            return real_build_source_snapshot(src_dir, **kwargs)

        def fake_inventory(src_dir, *args, **kwargs):
            seen["inventory_include_tests"] = kwargs["include_tests"]
            return InventoryResult(
                {
                    "main_test.go": {
                        "classes": [],
                        "functions": [{"name": "TestMain", "line": 3}],
                        "language": "go",
                    }
                },
                {"go": ExtractorStatus("go", "ok", 1)},
                InventoryCacheStats(enabled=False, status="disabled"),
            )

        monkeypatch.setattr(sync_cmd, "build_source_snapshot", fake_snapshot)
        monkeypatch.setattr(sync_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.chdir(tmp_path)

        sync_cmd.run(
            _make_sync_args(
                src_dir=str(tmp_path),
                wiki_dir=str(wiki_dir),
                include_tests=["go"],
            )
        )

        assert set(seen["snapshot_include_tests"]) == {"go"}
        assert set(seen["inventory_include_tests"]) == {"go"}
        assert (wiki_dir / "modules" / "main_test.md").exists()
        manifest = SyncManifest.load(wiki_dir)
        assert "main_test.go" in manifest.sources
        assert manifest.sources["main_test.go"]["module_page"] == "main_test"

    def test_haskell_inventory_creates_module_page_and_manifest_entry(
        self, tmp_path, monkeypatch, capsys
    ):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        self._write_empty_manifest(wiki_dir)
        (tmp_path / "Main.hs").write_text("module Main where\n", encoding="utf-8")
        seen = {}
        real_build_source_snapshot = sync_cmd.build_source_snapshot

        def fake_snapshot(src_dir, **kwargs):
            seen["snapshot_paths"] = real_build_source_snapshot(
                src_dir, **kwargs
            ).language_paths("haskell")
            return real_build_source_snapshot(src_dir, **kwargs)

        def fake_inventory(src_dir, *args, **kwargs):
            seen["helper_cache_dir"] = kwargs["helper_cache_dir"]
            return InventoryResult(
                {
                    "Main.hs": {
                        "classes": [],
                        "functions": [{"name": "main", "line": 1}],
                        "language": "haskell",
                    }
                },
                {"haskell": ExtractorStatus("haskell", "ok", 1)},
                InventoryCacheStats(enabled=False, status="disabled"),
            )

        monkeypatch.setattr(sync_cmd, "build_source_snapshot", fake_snapshot)
        monkeypatch.setattr(sync_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.chdir(tmp_path)

        sync_cmd.run(
            _make_sync_args(
                src_dir=str(tmp_path),
                wiki_dir=str(wiki_dir),
                helper_cache_dir=str(tmp_path / "helper-cache"),
            )
        )

        assert seen["snapshot_paths"] == ["Main.hs"]
        assert seen["helper_cache_dir"] == str(tmp_path / "helper-cache")
        assert (wiki_dir / "modules" / "Main.md").exists()
        manifest = SyncManifest.load(wiki_dir)
        assert manifest.sources["Main.hs"]["language"] == "haskell"
        assert manifest.sources["Main.hs"]["module_page"] == "Main"

    def test_changed_haskell_inventory_regenerates_module_page(
        self, tmp_path, monkeypatch, capsys
    ):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        (tmp_path / "API.hs").write_text(
            "module API where\napiName :: Text\n", encoding="utf-8"
        )
        state = {"signature": "Text"}

        def fake_inventory(src_dir, *args, **kwargs):
            return InventoryResult(
                {
                    "API.hs": {
                        "language": "haskell",
                        "module": "API",
                        "imports": [],
                        "classes": [],
                        "functions": [
                            {
                                "name": "apiName",
                                "kind": "signature",
                                "signature": state["signature"],
                                "line": 2,
                            }
                        ],
                    }
                },
                {"haskell": ExtractorStatus("haskell", "ok", 1)},
                InventoryCacheStats(enabled=False, status="disabled"),
            )

        monkeypatch.setattr(bootstrap_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(sync_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(bootstrap_cmd, "get_docker_inventory", lambda *a, **k: {})
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(
            _make_bootstrap_args(
                src_dir=str(tmp_path),
                wiki_dir=str(wiki_dir),
                skip_dependencies=True,
                skip_flows=True,
            )
        )
        module_path = wiki_dir / "modules" / "API.md"
        assert "| `apiName` | Signature | `Text` | 2 | — |" in module_path.read_text(
            encoding="utf-8"
        )

        state["signature"] = "String"
        (tmp_path / "API.hs").write_text(
            "module API where\napiName :: String\n", encoding="utf-8"
        )
        sync_cmd.run(_make_sync_args(src_dir=str(tmp_path), wiki_dir=str(wiki_dir)))

        assert "| `apiName` | Signature | `String` | 2 | — |" in (
            module_path.read_text(encoding="utf-8")
        )

    def test_haskell_import_graph_change_refreshes_unchanged_module_local_map(
        self, tmp_path, monkeypatch, capsys
    ):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        (tmp_path / "hls-analysis" / "app").mkdir(parents=True)
        (tmp_path / "hls-analysis" / "src" / "HLSAnalysis").mkdir(parents=True)
        (tmp_path / "hls-analysis" / "app" / "Main.hs").write_text(
            "module Main where\nimport HLSAnalysis.API\n", encoding="utf-8"
        )
        (tmp_path / "hls-analysis" / "src" / "HLSAnalysis" / "API.hs").write_text(
            "module HLSAnalysis.API where\n", encoding="utf-8"
        )
        state = {"imports_api": True}

        def fake_inventory(src_dir, *args, **kwargs):
            imports = []
            if state["imports_api"]:
                imports.append(
                    {
                        "module": "HLSAnalysis.API",
                        "qualified": False,
                        "alias": None,
                        "line": 2,
                    }
                )
            return InventoryResult(
                {
                    "hls-analysis/app/Main.hs": {
                        "language": "haskell",
                        "module": "Main",
                        "imports": imports,
                        "classes": [],
                        "functions": [{"name": "main", "kind": "value", "line": 3}],
                    },
                    "hls-analysis/src/HLSAnalysis/API.hs": {
                        "language": "haskell",
                        "module": "HLSAnalysis.API",
                        "imports": [],
                        "classes": [{"name": "User", "kind": "data", "line": 3}],
                        "functions": [],
                    },
                },
                {"haskell": ExtractorStatus("haskell", "ok", 2)},
                InventoryCacheStats(enabled=False, status="disabled"),
            )

        monkeypatch.setattr(bootstrap_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(sync_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(bootstrap_cmd, "get_docker_inventory", lambda *a, **k: {})
        monkeypatch.chdir(tmp_path)

        bootstrap_cmd.run(
            _make_bootstrap_args(
                src_dir=str(tmp_path),
                wiki_dir=str(wiki_dir),
                skip_flows=True,
            )
        )
        api_module = wiki_dir / "modules" / "API.md"
        assert "[Main](../modules/Main.md)" in api_module.read_text(encoding="utf-8")

        state["imports_api"] = False
        (tmp_path / "hls-analysis" / "app" / "Main.hs").write_text(
            "module Main where\n", encoding="utf-8"
        )
        sync_cmd.run(_make_sync_args(src_dir=str(tmp_path), wiki_dir=str(wiki_dir)))

        captured = capsys.readouterr()
        updated = api_module.read_text(encoding="utf-8")
        local_map = updated.split("## Local dependency map", 1)[1]
        assert "[Main](../modules/Main.md)" not in local_map
        assert "No internal module dependencies detected" in local_map
        assert "UPDATE module local dependency map: API" in captured.out

    def test_allow_external_src_reaches_inventory_for_external_source(
        self, tmp_path, monkeypatch, capsys
    ):
        runner = tmp_path / "runner"
        external = tmp_path / "external"
        wiki_dir = runner / "wiki"
        runner.mkdir()
        external.mkdir()
        wiki_dir.mkdir()
        (wiki_dir / "index.md").write_text("# Wiki\n", encoding="utf-8")
        seen = {}

        def fake_inventory(src_dir, *args, **kwargs):
            seen["src_dir"] = src_dir
            return InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
                InventoryCacheStats(enabled=False, status="disabled"),
            )

        monkeypatch.setattr(sync_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.chdir(runner)

        sync_cmd.run(
            _make_sync_args(
                src_dir=os.path.relpath(external, runner),
                wiki_dir="wiki",
                allow_external_src=True,
            )
        )

        assert Path(seen["src_dir"]) == external.resolve()

    def test_external_source_without_opt_in_still_fails_closed(
        self, tmp_path, monkeypatch
    ):
        runner = tmp_path / "runner"
        external = tmp_path / "external"
        runner.mkdir()
        external.mkdir()
        monkeypatch.chdir(runner)

        with pytest.raises(PathValidationError) as exc_info:
            sync_cmd.run(
                _make_sync_args(
                    src_dir=os.path.relpath(external, runner),
                    wiki_dir="wiki",
                )
            )

        message = str(exc_info.value)
        assert "--src-dir" in message
        assert "outside the project root" in message

    def test_cli_sync_jobs_auto_resolves_positive_count(self, monkeypatch):
        seen = {}
        monkeypatch.setattr(cli.os, "cpu_count", lambda: 4)
        monkeypatch.setattr(
            cli.sync_cmd,
            "run",
            lambda args: seen.update(
                jobs=args.jobs, requested_jobs=args.requested_jobs
            ),
        )
        monkeypatch.setattr("sys.argv", ["llm-wiki", "sync", "--jobs", "auto"])

        cli.main()

        assert seen == {"jobs": 4, "requested_jobs": "auto"}

    def test_cli_sync_allow_external_src_parses_with_jobs_auto(self, monkeypatch):
        seen = {}
        monkeypatch.setattr(cli.os, "cpu_count", lambda: 4)
        monkeypatch.setattr(
            cli.sync_cmd,
            "run",
            lambda args: seen.update(
                allow_external_src=args.allow_external_src,
                jobs=args.jobs,
            ),
        )
        monkeypatch.setattr(
            "sys.argv",
            ["llm-wiki", "sync", "--allow-external-src", "--jobs", "auto"],
        )

        cli.main()

        assert seen == {"allow_external_src": True, "jobs": 4}

    def test_cli_sync_force_parses(self, monkeypatch):
        seen = {}
        monkeypatch.setattr(
            cli.sync_cmd, "run", lambda args: seen.setdefault("force", args.force)
        )
        monkeypatch.setattr("sys.argv", ["llm-wiki", "sync", "--force"])

        cli.main()

        assert seen["force"] is True

    def test_cli_sync_no_preserve_semantic_parses(self, monkeypatch):
        seen = {}
        monkeypatch.setattr(
            cli.sync_cmd,
            "run",
            lambda args: seen.setdefault(
                "no_preserve_semantic", args.no_preserve_semantic
            ),
        )
        monkeypatch.setattr("sys.argv", ["llm-wiki", "sync", "--no-preserve-semantic"])

        cli.main()

        assert seen["no_preserve_semantic"] is True

    @pytest.mark.parametrize("value", ["0", "-1", "many"])
    def test_cli_sync_rejects_invalid_jobs(self, value, monkeypatch):
        monkeypatch.setattr(
            cli.sync_cmd, "run", lambda _args: pytest.fail("command should not run")
        )
        monkeypatch.setattr("sys.argv", ["llm-wiki", "sync", "--jobs", value])

        with pytest.raises(SystemExit) as exc:
            cli.main()

        assert exc.value.code == 2

    def test_default_sync_creates_git_cache(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        assert (proj / ".git" / CACHE_FILENAME).exists()

    def test_no_cache_does_not_create_git_cache(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project

        sync_cmd.run(
            _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir), no_cache=True)
        )

        assert not (proj / ".git" / CACHE_FILENAME).exists()

    def test_cache_dir_routes_cache_file(self, bootstrapped_project, tmp_path, capsys):
        proj, wiki_dir = bootstrapped_project
        cache_dir = tmp_path / "sync-cache"

        sync_cmd.run(
            _make_sync_args(
                src_dir=str(proj),
                wiki_dir=str(wiki_dir),
                cache_dir=str(cache_dir),
            )
        )

        assert (cache_dir / CACHE_FILENAME).exists()
        assert not (proj / ".git" / CACHE_FILENAME).exists()

    def test_cache_stats_prints_for_empty_inventory_manifest_seed(
        self, tmp_path, monkeypatch, capsys
    ):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        wiki_dir.mkdir(parents=True)
        (wiki_dir / "index.md").write_text("# Index\n", encoding="utf-8")
        monkeypatch.setattr(
            sync_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
                InventoryCacheStats(
                    enabled=True, path="cache.json", status="miss", misses=1
                ),
            ),
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            sync_cmd.run(
                _make_sync_args(
                    src_dir=str(tmp_path), wiki_dir=str(wiki_dir), cache_stats=True
                )
            )
        finally:
            os.chdir(old_cwd)

        out = capsys.readouterr().out
        assert "manifest written" in out.lower()
        assert "Cache:" in out
        assert "status: miss" in out

    def test_cache_stats_prints_for_up_to_date_sync(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project

        sync_cmd.run(
            _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir), cache_stats=True)
        )

        out = capsys.readouterr().out
        assert "Wiki is up to date." in out
        assert "Cache:" in out

    def test_cache_stats_prints_for_changed_sync(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").write_text(
            "class User:\n    changed: str = ''\n", encoding="utf-8"
        )

        sync_cmd.run(
            _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir), cache_stats=True)
        )

        out = capsys.readouterr().out
        assert "Sync complete:" in out
        assert "Cache:" in out


class TestSyncSafetyGuards:
    def _poison_manifest_hashes(self, wiki_dir: Path, value=None) -> None:
        manifest_path = wiki_dir / MANIFEST_FILENAME
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        for info in payload["sources"].values():
            if value is None:
                info.pop("hash", None)
            else:
                info["hash"] = value
        manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def test_missing_manifest_hash_repairs_without_touching_pages(
        self,
        bootstrapped_project,
        monkeypatch,
        capsys,
    ):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").write_text(
            "class User:\n    changed: str = ''\n", encoding="utf-8"
        )
        entity_path = wiki_dir / "entities" / "User.md"
        before = entity_path.read_text(encoding="utf-8")
        self._poison_manifest_hashes(wiki_dir)
        writes = []

        def fail_page_write(path, text):
            writes.append(Path(path))
            raise AssertionError("manifest repair must not rewrite wiki pages")

        monkeypatch.setattr(sync_cmd, "write_md", fail_page_write)

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        out = capsys.readouterr().out
        assert "manifest repaired" in out.lower()
        assert "wiki pages were not modified" in out.lower()
        assert writes == []
        assert entity_path.read_text(encoding="utf-8") == before
        repaired = SyncManifest.load(wiki_dir)
        info = next(iter(repaired.sources.values()))
        assert info["hash"].startswith("sha256:")
        assert len(info["hash"]) == len("sha256:") + 64
        assert info["language"] == "python"
        assert info["entity_pages"]["User"] == "User"
        assert info["module_page"] == "models"

    def test_malformed_manifest_hash_repairs_without_touching_pages(
        self,
        bootstrapped_project,
        monkeypatch,
        capsys,
    ):
        proj, wiki_dir = bootstrapped_project
        self._poison_manifest_hashes(wiki_dir, "sha256:not-valid")
        monkeypatch.setattr(
            sync_cmd,
            "write_md",
            lambda *args, **kwargs: pytest.fail(
                "manifest repair must not rewrite wiki pages"
            ),
        )

        sync_cmd.run(
            _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir), cache_stats=True)
        )

        out = capsys.readouterr().out
        assert "manifest repaired" in out.lower()
        assert "Cache:" in out
        repaired = SyncManifest.load(wiki_dir)
        assert all(
            info["hash"].startswith("sha256:") for info in repaired.sources.values()
        )

    def test_manifest_repair_preserves_unknown_generation_state_and_clears_commit(
        self,
        bootstrapped_project,
        monkeypatch,
        capsys,
    ):
        proj, wiki_dir = bootstrapped_project
        manifest = SyncManifest.load(wiki_dir)
        unknown_reason = "evidence-intentionally-unavailable"
        baseline_paths = set(manifest.evidence_baselines)
        manifest.evidence_baselines = {
            page_path: ManifestEvidenceBaseline.unknown(unknown_reason)
            for page_path in baseline_paths
        }
        surfaces = {
            "flows": {
                "enabled": True,
                "categories": ["startup", "background"],
                "exclude_tests": True,
            },
            "future_surface": {
                "enabled": False,
                "settings": {"order": [2, 1]},
            },
        }
        generation_inputs = {
            "fixture": {
                "path": "inputs/fixture.json",
                "flags": ["alpha", "beta"],
            }
        }
        manifest = manifest.with_generation_state(
            surfaces=surfaces,
            generation_inputs=generation_inputs,
        ).with_artifact_hashes(
            surface_index_hash="sha256:" + "1" * 64,
            knowledge_index_hash="sha256:" + "2" * 64,
            evaluated_envelope_hash="sha256:" + "3" * 64,
        )
        manifest.save(wiki_dir)
        assert SyncManifest.load(wiki_dir).artifact_hashes is not None

        (proj / "models.py").write_text(
            "class User:\n    changed: str = ''\n",
            encoding="utf-8",
        )
        self._poison_manifest_hashes(wiki_dir)
        monkeypatch.setattr(
            sync_cmd,
            "write_md",
            lambda *args, **kwargs: pytest.fail(
                "manifest repair must not rewrite wiki pages"
            ),
        )

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        assert "manifest repaired" in capsys.readouterr().out.lower()
        repaired = SyncManifest.load(wiki_dir)
        assert repaired.surfaces == surfaces
        assert repaired.generation_inputs == generation_inputs
        assert repaired.artifact_hashes is not None
        assert "artifact_hashes" in repaired.to_payload()
        assert set(repaired.evidence_baselines) == baseline_paths
        assert all(
            not baseline.is_known
            and baseline.basis is None
            and baseline.unknown_reason == unknown_reason
            for baseline in repaired.evidence_baselines.values()
        )

    def test_dry_run_rejects_external_symlink_without_touching_target(
        self,
        bootstrapped_project,
        capsys,
    ):
        proj, wiki_dir = bootstrapped_project
        external_modules = proj.parent / "external-modules"
        modules_dir = wiki_dir / "modules"
        modules_dir.rename(external_modules)
        try:
            modules_dir.symlink_to(external_modules, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"directory symlinks are unavailable: {exc}")
        before = {
            path.relative_to(external_modules).as_posix(): path.read_bytes()
            for path in external_modules.rglob("*")
            if path.is_file()
        }
        (proj / "models.py").write_text(
            "class User:\n    changed: str = ''\n",
            encoding="utf-8",
        )
        capsys.readouterr()

        with pytest.raises(SystemExit) as exc_info:
            sync_cmd.run(
                _make_sync_args(
                    src_dir=str(proj),
                    wiki_dir=str(wiki_dir),
                    dry_run=True,
                )
            )

        assert exc_info.value.code == 2
        assert {
            path.relative_to(external_modules).as_posix(): path.read_bytes()
            for path in external_modules.rglob("*")
            if path.is_file()
        } == before
        captured = capsys.readouterr()
        assert "cannot safely stage" in captured.err
        assert "modules" in captured.err

    def test_large_manifest_diff_dry_run_reports_force_requirement(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        wiki_dir.mkdir(parents=True)
        inventory = {}
        sources = {}
        for index in range(10):
            path = f"f{index}.py"
            source_path = tmp_path / path
            source_path.write_text(
                f"class C{index}: pass\n",
                encoding="utf-8",
            )
            sources[path] = {
                "hash": (
                    "sha256:" + "0" * 64 if index < 4 else _hash_file(source_path)
                ),
                "language": "python",
                "entities": [f"C{index}"],
                "module_page": f"f{index}",
            }
            inventory[path] = {
                "language": "python",
                "classes": [{"name": f"C{index}", "line": 1, "bases": []}],
                "functions": [],
            }
        SyncManifest(sources=sources).save(wiki_dir)
        monkeypatch.setattr(
            sync_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                inventory,
                {"python": ExtractorStatus("python", "ok", 10)},
            ),
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            sync_cmd.run(
                _make_sync_args(
                    src_dir=str(tmp_path),
                    wiki_dir=str(wiki_dir),
                    dry_run=True,
                )
            )
        finally:
            os.chdir(old_cwd)

        output = capsys.readouterr().out
        assert "requires --force: yes" in output

    def test_large_diff_count_guard_aborts_before_page_writes(
        self, tmp_path, monkeypatch, capsys
    ):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        wiki_dir.mkdir(parents=True)
        sources = {
            f"f{i}.py": {
                "hash": "sha256:" + "0" * 64,
                "language": "python",
                "entities": [],
                "module_page": f"f{i}",
            }
            for i in range(51)
        }
        SyncManifest(sources=sources).save(wiki_dir)
        inventory = {
            path: {"language": "python", "classes": [], "functions": []}
            for path in sources
        }
        for path in sources:
            (tmp_path / path).write_text("# changed\n", encoding="utf-8")
        monkeypatch.setattr(
            sync_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                inventory, {"python": ExtractorStatus("python", "ok", 51)}
            ),
        )
        monkeypatch.setattr(
            sync_cmd,
            "write_md",
            lambda *args, **kwargs: pytest.fail(
                "large diff guard should abort before page writes"
            ),
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(SystemExit) as exc:
                sync_cmd.run(
                    _make_sync_args(src_dir=str(tmp_path), wiki_dir=str(wiki_dir))
                )
        finally:
            os.chdir(old_cwd)

        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "exceeds the safety limit" in err
        assert "--force" in err

    def test_large_diff_percent_guard_aborts_before_page_writes(
        self, tmp_path, monkeypatch, capsys
    ):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        wiki_dir.mkdir(parents=True)
        inventory = {}
        sources = {}
        for i in range(10):
            path = f"f{i}.py"
            source_path = tmp_path / path
            source_path.write_text(f"class C{i}: pass\n", encoding="utf-8")
            current_hash = _hash_file(source_path)
            sources[path] = {
                "hash": "sha256:" + "0" * 64 if i < 4 else current_hash,
                "language": "python",
                "entities": [f"C{i}"],
                "module_page": f"f{i}",
            }
            inventory[path] = {
                "language": "python",
                "classes": [{"name": f"C{i}", "line": 1, "bases": []}],
                "functions": [],
            }
        SyncManifest(sources=sources).save(wiki_dir)
        monkeypatch.setattr(
            sync_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                inventory, {"python": ExtractorStatus("python", "ok", 10)}
            ),
        )
        monkeypatch.setattr(
            sync_cmd,
            "write_md",
            lambda *args, **kwargs: pytest.fail(
                "large diff guard should abort before page writes"
            ),
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(SystemExit) as exc:
                sync_cmd.run(
                    _make_sync_args(src_dir=str(tmp_path), wiki_dir=str(wiki_dir))
                )
        finally:
            os.chdir(old_cwd)

        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "30% safety limit" in err

    def test_force_allows_large_diff(self, tmp_path, monkeypatch, capsys):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        wiki_dir.mkdir(parents=True)
        sources = {
            f"f{i}.py": {
                "hash": "sha256:" + "0" * 64,
                "language": "python",
                "entities": [],
                "module_page": f"f{i}",
            }
            for i in range(51)
        }
        inventory = {
            path: {"language": "python", "classes": [], "functions": []}
            for path in sources
        }
        for path in sources:
            (tmp_path / path).write_text("# changed\n", encoding="utf-8")
        SyncManifest(sources=sources).save(wiki_dir)
        monkeypatch.setattr(
            sync_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                inventory, {"python": ExtractorStatus("python", "ok", 51)}
            ),
        )
        calls = {"apply": 0}

        def fake_apply(*args, **kwargs):
            calls["apply"] += 1
            return sync_cmd.SyncResult()

        monkeypatch.setattr(sync_cmd, "_apply_diff", fake_apply)
        monkeypatch.setattr(sync_cmd, "_rebuild_index", lambda *args, **kwargs: None)
        monkeypatch.setattr(sync_cmd, "_append_log", lambda *args, **kwargs: None)
        monkeypatch.setattr(
            sync_cmd,
            "_finalize_prepared_sync",
            lambda _options, prepared, result, **kwargs: sync_cmd._print_sync_summary(
                result, prepared.diff
            ),
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            sync_cmd.run(
                _make_sync_args(
                    src_dir=str(tmp_path), wiki_dir=str(wiki_dir), force=True
                )
            )
        finally:
            os.chdir(old_cwd)

        assert calls["apply"] == 1
        assert "Sync complete:" in capsys.readouterr().out

    def test_content_equal_pages_are_not_rewritten(
        self, bootstrapped_project, monkeypatch, capsys
    ):
        proj, wiki_dir = bootstrapped_project
        manifest_path = wiki_dir / MANIFEST_FILENAME
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        for info in payload["sources"].values():
            info["hash"] = "sha256:" + "0" * 64
        manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        entity_path = wiki_dir / "entities" / "User.md"
        module_path = wiki_dir / "modules" / "models.md"
        index_path = wiki_dir / "index.md"
        writes = []
        real_write_md = sync_cmd.write_md

        def recording_write(path, text):
            writes.append(Path(path))
            real_write_md(path, text)

        monkeypatch.setattr(sync_cmd, "write_md", recording_write)

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        out = capsys.readouterr().out
        assert "SKIP entity (unchanged): User" in out
        assert "SKIP module (unchanged): models" in out
        assert "SKIP index.md (unchanged)" in out
        assert "0 updated" in out
        assert entity_path not in writes
        assert module_path not in writes
        assert index_path not in writes
        assert wiki_dir / "log.md" in writes

    def test_small_diff_relationships_are_target_scoped(
        self, bootstrapped_project, monkeypatch
    ):
        proj, wiki_dir = bootstrapped_project
        (proj / "extra.py").write_text("class Extra:\n    pass\n", encoding="utf-8")
        seen = {}

        def fake_build_relationships(
            inventory, module_page_map=None, *, target_entities=None, **kwargs
        ):
            seen["target_entities"] = target_entities
            return {}

        monkeypatch.setattr(sync_cmd, "_build_relationships", fake_build_relationships)

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        assert seen["target_entities"] == {("Extra", "extra.py")}

    def test_changed_sync_summarizes_unchanged_files(
        self, bootstrapped_project, capsys
    ):
        proj, wiki_dir = bootstrapped_project
        (proj / "extra.py").write_text("class Extra:\n    pass\n", encoding="utf-8")

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        out = capsys.readouterr().out
        assert "SKIP unchanged source files:" in out
        assert "SKIP (unchanged):" not in out

    def test_already_deprecated_pages_are_not_rewritten(
        self, bootstrapped_project, monkeypatch
    ):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").unlink()
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))
        _write_manifest_from_bootstrap_from_disk(wiki_dir, proj)
        writes = []
        real_write_md = sync_cmd.write_md

        def recording_write(path, text):
            writes.append(Path(path))
            real_write_md(path, text)

        monkeypatch.setattr(sync_cmd, "write_md", recording_write)

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        assert wiki_dir / "entities" / "User.md" not in writes
        assert wiki_dir / "modules" / "models.md" not in writes


class TestPartialExtractionSafety:
    def _write_ts_manifest_and_pages(self, wiki_dir: Path) -> None:
        (wiki_dir / "entities").mkdir(parents=True)
        (wiki_dir / "modules").mkdir(parents=True)
        (wiki_dir / "workflows").mkdir(parents=True)
        (wiki_dir / "infrastructure").mkdir(parents=True)
        (wiki_dir / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki_dir / "entities" / "Widget.md").write_text("# Widget\n", encoding="utf-8")
        (wiki_dir / "modules" / "app.md").write_text("# app Module\n", encoding="utf-8")
        SyncManifest(
            sources={
                "app.ts": {
                    "hash": "sha256:" + "0" * 64,
                    "language": "typescript",
                    "entities": ["Widget"],
                    "module_page": "app",
                }
            }
        ).save(wiki_dir)

    def test_extractor_failure_aborts_without_deprecation(self, tmp_path, monkeypatch):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        self._write_ts_manifest_and_pages(wiki_dir)
        monkeypatch.setattr(
            sync_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {},
                {
                    "typescript": ExtractorStatus(
                        "typescript", "failed", 1, "node not found"
                    )
                },
            ),
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            with pytest.raises(SystemExit) as exc_info:
                sync_cmd.run(
                    _make_sync_args(src_dir=str(tmp_path), wiki_dir=str(wiki_dir))
                )
        finally:
            os.chdir(old_cwd)

        assert exc_info.value.code == 1
        assert "Stale" not in (wiki_dir / "entities" / "Widget.md").read_text(
            encoding="utf-8"
        )
        assert "Stale" not in (wiki_dir / "modules" / "app.md").read_text(
            encoding="utf-8"
        )

    def test_skipped_language_allows_real_deletion(self, tmp_path, monkeypatch):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        self._write_ts_manifest_and_pages(wiki_dir)
        monkeypatch.setattr(
            sync_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {},
                {"typescript": ExtractorStatus("typescript", "skipped", 0)},
            ),
        )

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            sync_cmd.run(_make_sync_args(src_dir=str(tmp_path), wiki_dir=str(wiki_dir)))
        finally:
            os.chdir(old_cwd)

        assert "Stale" in (wiki_dir / "entities" / "Widget.md").read_text(
            encoding="utf-8"
        )


class TestUnchangedFile:
    """When nothing changed, sync prints 'up to date' and skips all pages."""

    def test_wiki_is_up_to_date(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))

        # Run sync immediately after bootstrap — nothing should change
        sync_cmd.run(args)

        captured = capsys.readouterr()
        assert "Extracting current source inventory..." in captured.out
        assert "Extracted current source inventory:" in captured.out
        assert "up to date" in captured.out.lower()

    def test_entity_page_not_rewritten(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        entity_path = wiki_dir / "entities" / "User.md"
        original_mtime = entity_path.stat().st_mtime

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        # File should not have been touched
        assert entity_path.stat().st_mtime == original_mtime


class TestChangedFile:
    """When a source file is modified, affected pages are updated."""

    def test_entity_page_updated(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        models_py = proj / "models.py"

        # Modify source
        models_py.write_text(
            textwrap.dedent("""\
                class User:
                    \"\"\"An updated user with role.\"\"\"
                    name: str = ""
                    email: str = ""
                    role: str = "viewer"
            """)
        )

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        captured = capsys.readouterr()
        assert "UPDATE entity: User" in captured.out

        # Entity page should contain the new attribute
        entity_content = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")
        assert "role" in entity_content

    def test_module_page_updated(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").write_text(
            textwrap.dedent("""\
                class User:
                    \"\"\"An updated user.\"\"\"
                    name: str = ""
            """)
        )

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        captured = capsys.readouterr()
        assert "UPDATE module: models" in captured.out

    def test_manifest_updated_after_sync(self, bootstrapped_project):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").write_text(
            textwrap.dedent("""\
                class User:
                    \"\"\"Changed.\"\"\"
            """)
        )

        old_manifest = SyncManifest.load(wiki_dir)
        old_hash = next(
            (
                v.get("hash", "")
                for k, v in old_manifest.sources.items()
                if k.endswith("models.py")
            ),
            "",
        )
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))
        new_manifest = SyncManifest.load(wiki_dir)
        new_hash = next(
            (
                v.get("hash", "")
                for k, v in new_manifest.sources.items()
                if k.endswith("models.py")
            ),
            "",
        )

        assert old_hash != new_hash

    def test_relationship_links_keep_qualified_module_pages(self, tmp_path, capsys):
        """sync must use the same collision-aware module links as bootstrap."""
        import subprocess

        proj = tmp_path / "project"
        proj.mkdir()
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.email", "t@t.com"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.name", "T"],
            capture_output=True,
            check=True,
        )

        (proj / "models.py").write_text("class User:\n    pass\n")
        (proj / "pkg_a").mkdir()
        (proj / "pkg_b").mkdir()
        (proj / "pkg_a" / "service.py").write_text(
            "from models import User\n\n"
            "def make_user(user: User) -> User:\n"
            "    return user\n"
        )
        (proj / "pkg_b" / "service.py").write_text("class Other:\n    pass\n")

        wiki_dir = proj / "docs" / "llm_wiki"
        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            bootstrap_cmd.run(_make_bootstrap_args(src_dir=".", wiki_dir=str(wiki_dir)))
            (proj / "models.py").write_text(
                'class User:\n    """Changed."""\n    pass\n'
            )
            sync_cmd.run(_make_sync_args(src_dir=".", wiki_dir=str(wiki_dir)))

            entity_content = (wiki_dir / "entities" / "User.md").read_text(
                encoding="utf-8"
            )
            assert "../modules/pkg_a_service.md" in entity_content
            assert "../modules/service.md" not in entity_content

            from llm_wiki_cli.commands import lint_cmd

            lint_cmd.run(types.SimpleNamespace(src_dir=".", wiki_dir=str(wiki_dir)))
        finally:
            os.chdir(old_cwd)


class TestSemanticPreservation:
    """sync preserves manually enriched descriptions while refreshing metadata."""

    @staticmethod
    def _replace_section_body(content: str, heading: str, body: str) -> str:
        lines = content.splitlines()
        target = f"## {heading}"
        for i, line in enumerate(lines):
            if line.strip() != target:
                continue
            start = i + 1
            while start < len(lines) and lines[start] == "":
                start += 1
            end = start
            while end < len(lines) and not lines[end].startswith("## "):
                end += 1
            return "\n".join(lines[: i + 1] + ["", body, ""] + lines[end:])
        raise AssertionError(f"missing section: {heading}")

    @staticmethod
    def _replace_table_description(content: str, row_key: str, description: str) -> str:
        updated = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|") or row_key not in stripped:
                updated.append(line)
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) >= 4:
                cells[-1] = description
                updated.append("| " + " | ".join(cells) + " |")
            else:
                updated.append(line)
        return "\n".join(updated)

    def test_table_parser_keeps_pipes_inside_code_spans_and_escaped_cells(self):
        assert sync_cmd._split_table_row(
            "| Name | `str | None` | Human description |"
        ) == ["Name", "`str | None`", "Human description"]
        assert sync_cmd._split_table_row(
            r"| Name | `str \| None` | Human \| description |"
        ) == ["Name", r"`str \| None`", r"Human \| description"]

    def test_generated_field_description_updates_unedited_text_and_preserves_edits(
        self,
    ):
        old_generated = textwrap.dedent("""\
            # Request

            ## Description

            Request payload.

            ## Attributes

            | Name | Type | Default | Description |
            |------|------|---------|-------------|
            | `name` | `str` | *required* | Old source description. |
            """)
        new_generated = old_generated.replace(
            "Old source description.", "New source description."
        )
        old_semantics = {
            "description": "Request payload.",
            "attributes": {"name": "Old source description."},
            "methods": {},
        }

        unchanged = sync_cmd._merge_entity_semantics(
            old_generated, new_generated, old_semantics
        )
        human_edited = sync_cmd._merge_entity_semantics(
            old_generated.replace(
                "Old source description.", "Human-curated description."
            ),
            new_generated,
            old_semantics,
        )

        assert "New source description." in unchanged.text
        assert "Old source description." not in unchanged.text
        assert "Human-curated description." in human_edited.text
        assert "New source description." not in human_edited.text

    def test_line_number_shift_preserves_entity_semantics(
        self, bootstrapped_project, capsys
    ):
        proj, wiki_dir = bootstrapped_project
        entity_path = wiki_dir / "entities" / "User.md"
        content = entity_path.read_text(encoding="utf-8")
        content = self._replace_section_body(
            content,
            "Description",
            "Human-written semantic description.",
        )
        content = self._replace_table_description(
            content,
            "`name`",
            "Human-curated display name.",
        )
        entity_path.write_text(content, encoding="utf-8")

        (proj / "models.py").write_text(
            textwrap.dedent("""\
                # inserted comment shifts class line numbers
                class User:
                    \"\"\"A system user.\"\"\"
                    name: str = ""
                    email: str = ""
            """),
            encoding="utf-8",
        )

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        out = capsys.readouterr().out
        entity_content = entity_path.read_text(encoding="utf-8")
        assert "METADATA entity: User" in out
        assert "**Location:** `models.py:2`" in entity_content
        assert "Human-written semantic description." in entity_content
        assert "Human-curated display name." in entity_content

    def test_line_number_shift_preserves_module_semantics(
        self, bootstrapped_project, capsys
    ):
        proj, wiki_dir = bootstrapped_project
        module_path = wiki_dir / "modules" / "models.md"
        content = module_path.read_text(encoding="utf-8")
        content = self._replace_section_body(
            content,
            "Description",
            "Human-written module overview.",
        )
        content = self._replace_table_description(
            content,
            "[User](../entities/User.md)",
            "Human-curated user summary.",
        )
        module_path.write_text(content, encoding="utf-8")

        (proj / "models.py").write_text(
            textwrap.dedent("""\
                # inserted comment shifts class line numbers
                class User:
                    \"\"\"A system user.\"\"\"
                    name: str = ""
                    email: str = ""
            """),
            encoding="utf-8",
        )

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        out = capsys.readouterr().out
        module_content = module_path.read_text(encoding="utf-8")
        assert "METADATA module: models" in out
        assert "| [User](../entities/User.md) | 2 |" in module_content
        assert "Human-written module overview." in module_content
        assert "Human-curated user summary." in module_content

    def test_structural_change_preserves_existing_table_descriptions(
        self,
        bootstrapped_project,
        capsys,
    ):
        proj, wiki_dir = bootstrapped_project
        entity_path = wiki_dir / "entities" / "User.md"
        content = entity_path.read_text(encoding="utf-8")
        content = self._replace_table_description(
            content,
            "`name`",
            "Human-curated display name.",
        )
        entity_path.write_text(content, encoding="utf-8")

        (proj / "models.py").write_text(
            textwrap.dedent("""\
                class User:
                    \"\"\"A system user.\"\"\"
                    name: str = ""
                    email: str = ""
                    role: str = "viewer"
            """),
            encoding="utf-8",
        )

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        entity_content = entity_path.read_text(encoding="utf-8")
        assert "UPDATE entity: User" in capsys.readouterr().out
        assert "Human-curated display name." in entity_content
        assert "| `role` | `str` | `'viewer'` |" in entity_content

    def test_no_preserve_semantic_disables_entity_merge(
        self, bootstrapped_project, capsys
    ):
        proj, wiki_dir = bootstrapped_project
        entity_path = wiki_dir / "entities" / "User.md"
        content = entity_path.read_text(encoding="utf-8")
        content = self._replace_section_body(
            content,
            "Description",
            "Human-written semantic description.",
        )
        content = self._replace_table_description(
            content,
            "`name`",
            "Human-curated display name.",
        )
        entity_path.write_text(content, encoding="utf-8")

        (proj / "models.py").write_text(
            textwrap.dedent("""\
                # inserted comment shifts class line numbers
                class User:
                    \"\"\"A system user.\"\"\"
                    name: str = ""
                    email: str = ""
            """),
            encoding="utf-8",
        )

        sync_cmd.run(
            _make_sync_args(
                src_dir=str(proj),
                wiki_dir=str(wiki_dir),
                no_preserve_semantic=True,
            )
        )

        out = capsys.readouterr().out
        entity_content = entity_path.read_text(encoding="utf-8")
        assert "METADATA entity: User" in out
        assert "**Location:** `models.py:2`" in entity_content
        assert "A system user." in entity_content
        assert "| `name` | `str` | `''` | — |" in entity_content
        assert "Human-written semantic description." not in entity_content
        assert "Human-curated display name." not in entity_content


class TestNewFile:
    """When a new source file is added, new pages are created and manifest updated."""

    def test_new_pages_created(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        (proj / "auth.py").write_text(
            textwrap.dedent("""\
                class AuthService:
                    \"\"\"Handles authentication.\"\"\"
                    secret: str = ""
            """)
        )

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        captured = capsys.readouterr()
        assert "CREATE entity: AuthService" in captured.out
        assert "CREATE module: auth" in captured.out
        assert (wiki_dir / "entities" / "AuthService.md").exists()
        assert (wiki_dir / "modules" / "auth.md").exists()

    def test_new_file_in_manifest(self, bootstrapped_project):
        proj, wiki_dir = bootstrapped_project
        (proj / "auth.py").write_text("class AuthService:\n    pass\n")

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        manifest = SyncManifest.load(wiki_dir)
        assert any(k.endswith("auth.py") for k in manifest.sources)

    def test_new_entity_name_collision_renames_existing_pages(self, tmp_path, capsys):
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "backend" / "app" / "schemas").mkdir(parents=True)
        (proj / "backend" / "app" / "schemas" / "gantt.py").write_text(
            "class GanttResponse:\n    pass\n",
            encoding="utf-8",
        )
        (proj / "backend" / "app" / "schemas" / "task.py").write_text(
            "class SuggestedSubtask:\n    pass\n",
            encoding="utf-8",
        )

        wiki_dir = proj / "docs" / "llm_wiki"
        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            bootstrap_cmd.run(_make_bootstrap_args(src_dir=".", wiki_dir=str(wiki_dir)))

            assert (wiki_dir / "entities" / "GanttResponse.md").exists()
            assert (wiki_dir / "entities" / "SuggestedSubtask.md").exists()
            assert (wiki_dir / "modules" / "gantt.md").exists()
            assert (wiki_dir / "modules" / "task.md").exists()

            (proj / "frontend" / "src" / "types").mkdir(parents=True)
            (proj / "frontend" / "src" / "types" / "gantt.py").write_text(
                "class GanttResponse:\n    pass\n",
                encoding="utf-8",
            )
            (proj / "frontend" / "src" / "types" / "task.py").write_text(
                "class SuggestedSubtask:\n    pass\n",
                encoding="utf-8",
            )

            sync_cmd.run(_make_sync_args(src_dir=".", wiki_dir=str(wiki_dir)))
            out = capsys.readouterr().out

            assert "Moved entities detected" not in out
            assert (wiki_dir / "entities" / "schemas_gantt_GanttResponse.md").exists()
            assert (wiki_dir / "entities" / "types_gantt_GanttResponse.md").exists()
            assert (wiki_dir / "entities" / "schemas_task_SuggestedSubtask.md").exists()
            assert (wiki_dir / "entities" / "types_task_SuggestedSubtask.md").exists()
            assert not (wiki_dir / "entities" / "GanttResponse.md").exists()
            assert not (wiki_dir / "entities" / "SuggestedSubtask.md").exists()

            assert (wiki_dir / "modules" / "schemas_gantt.md").exists()
            assert (wiki_dir / "modules" / "types_gantt.md").exists()
            assert (wiki_dir / "modules" / "schemas_task.md").exists()
            assert (wiki_dir / "modules" / "types_task.md").exists()
            assert not (wiki_dir / "modules" / "gantt.md").exists()
            assert not (wiki_dir / "modules" / "task.md").exists()

            backend_module = (wiki_dir / "modules" / "schemas_gantt.md").read_text(
                encoding="utf-8"
            )
            assert "../entities/schemas_gantt_GanttResponse.md" in backend_module
            index = (wiki_dir / "index.md").read_text(encoding="utf-8")
            assert "entities/schemas_gantt_GanttResponse.md" in index
            assert "entities/types_gantt_GanttResponse.md" in index
            assert "modules/schemas_gantt.md" in index
            assert "modules/types_gantt.md" in index

            report = lint_cmd.build_report(wiki_dir, ".", strict=True)
            assert report.passed, report.by_category()
        finally:
            os.chdir(old_cwd)


class TestMovedClass:
    """When a class moves to a different file, its entity page is updated in-place."""

    def test_moved_entity_page_updated(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project

        # Remove User from models.py, add it to users.py
        (proj / "models.py").write_text("# empty\n")
        (proj / "users.py").write_text(
            textwrap.dedent("""\
                class User:
                    \"\"\"A moved user.\"\"\"
                    name: str = ""
            """)
        )

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        captured = capsys.readouterr()
        # The entity page should be updated (now points at users.py)
        entity_content = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")
        assert "users.py" in entity_content
        assert not entity_content.startswith("> ⚠️ **Stale:**")

        # Moved entities should be mentioned in summary
        assert "User" in captured.out

    def test_move_detected_in_diff(self, bootstrapped_project):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").write_text("# empty\n")
        (proj / "users.py").write_text("class User:\n    pass\n")

        from llm_wiki_cli.commands.extract_cmd import get_inventory

        manifest = SyncManifest.load(wiki_dir)
        inventory = get_inventory(str(proj), deep=True)
        diff = _compute_diff(manifest, inventory, str(proj))

        assert "User" in diff.moved_entities


class TestDeletedClass:
    """When a source file is removed, existing pages get a deprecation warning."""

    def test_removed_source_retains_known_basis_in_source_missing_tombstones(
        self,
        bootstrapped_project,
    ):
        proj, wiki_dir = bootstrapped_project
        bootstrap_cmd.run(
            _make_bootstrap_args(
                src_dir=str(proj),
                wiki_dir=str(wiki_dir),
                overwrite=True,
            )
        )
        manifest = SyncManifest.load(wiki_dir)
        expected_bases = {
            page_path: manifest.evidence_baselines[page_path].basis
            for page_path in ("modules/models.md", "entities/User.md")
        }
        assert all(
            basis is not None and basis.is_known for basis in expected_bases.values()
        )
        (proj / "models.py").unlink()

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        reconciled = SyncManifest.load(wiki_dir)
        for page_path, expected_basis in expected_bases.items():
            assert page_path not in reconciled.evidence_baselines
            tombstone = reconciled.tombstones[page_path]
            assert tombstone.reason == "source-missing"
            assert tombstone.last_valid_basis == expected_basis
            assert tombstone.unknown_reason is None

    def test_deprecation_header_added_to_entity(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project

        # Delete models.py
        (proj / "models.py").unlink()

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        captured = capsys.readouterr()
        assert "DEPRECATE" in captured.out

        entity_content = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")
        assert "⚠️" in entity_content
        assert "Stale" in entity_content

    def test_deprecation_header_is_idempotent(self, bootstrapped_project):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").unlink()

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        # Reset manifest to old state to allow running sync again
        _write_manifest_from_bootstrap_from_disk(wiki_dir, proj)
        sync_cmd.run(args)

        content = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")
        # Header must appear exactly once
        assert content.count("⚠️") == 1

    def test_deprecation_header_added_to_module(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").unlink()

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        module_content = (wiki_dir / "modules" / "models.md").read_text(
            encoding="utf-8"
        )
        assert "⚠️" in module_content

    def test_deprecation_header_added_to_qualified_entity_from_legacy_manifest(
        self,
        tmp_path,
        capsys,
    ):
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "pkg_a").mkdir()
        (proj / "pkg_b").mkdir()
        (proj / "pkg_a" / "models.py").write_text("class User:\n    pass\n")
        (proj / "pkg_b" / "models.py").write_text("class User:\n    pass\n")

        wiki_dir = proj / "docs" / "llm_wiki"
        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            bootstrap_cmd.run(_make_bootstrap_args(src_dir=".", wiki_dir=str(wiki_dir)))
            manifest_path = wiki_dir / MANIFEST_FILENAME
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            for info in manifest_data["sources"].values():
                info.pop("entity_pages", None)
            manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

            (proj / "pkg_a" / "models.py").unlink()
            sync_cmd.run(_make_sync_args(src_dir=".", wiki_dir=str(wiki_dir)))
        finally:
            os.chdir(old_cwd)

        content = (wiki_dir / "entities" / "pkg_a_models_User.md").read_text(
            encoding="utf-8"
        )
        assert "⚠️" in content
        assert "Stale" in content


def _write_manifest_from_bootstrap_from_disk(wiki_dir: Path, proj: Path) -> None:
    """Re-seed manifest from whatever pages are on disk (for idempotency test)."""
    # Rebuild manifest pointing to the old state by loading the existing one
    # and clearing the files that were deleted so sync runs the removal path again.
    manifest = SyncManifest.load(wiki_dir)
    manifest.save(wiki_dir)


class TestDiffOutput:
    """sync prints a concise per-page summary to stdout."""

    def test_sync_reports_missing_haskell_helper_failure(
        self, bootstrapped_project, capsys
    ):
        proj, wiki_dir = bootstrapped_project
        hls_app = proj / "hls-analysis" / "app"
        hls_app.mkdir(parents=True)
        (hls_app / "Main.hs").write_text("module Main where\n", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        captured = capsys.readouterr()
        assert exc_info.value.code == 1
        assert "Error: haskell extraction failed" in captured.err
        assert "prepare-extractors --language haskell" in captured.err
        assert "Unsupported sources detected" not in captured.out
        assert "Wiki is up to date." not in captured.out

    def test_summary_line_on_completion(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        # Trigger a real change
        (proj / "models.py").write_text("class User:\n    updated: str = ''\n")

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        out = capsys.readouterr().out
        assert "Sync complete:" in out
        assert "created" in out
        assert "updated" in out
        assert "skipped" in out

    def test_log_entry_appended(self, bootstrapped_project):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").write_text("class User:\n    changed: str = ''\n")

        log_before = (
            (wiki_dir / "log.md").read_text(encoding="utf-8")
            if (wiki_dir / "log.md").exists()
            else ""
        )

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        log_after = (wiki_dir / "log.md").read_text(encoding="utf-8")
        assert len(log_after) > len(log_before)
        assert "incremental sync" in log_after


class TestSyncFlowReindex:
    def _inventory(self):
        return {
            "api.py": {
                "language": "python",
                "classes": [],
                "functions": [{"name": "run", "line": 1}],
            }
        }

    def test_rebuild_index_includes_existing_flow_pages(self, tmp_path):
        wiki = tmp_path / "wiki"
        (wiki / "flows").mkdir(parents=True)
        (wiki / "flows" / "api-run.md").write_text("# run\n")
        (wiki / "flows" / "process-cli.md").write_text("# cli\n")
        (wiki / "log.md").write_text("# Architectural Log\n")

        sync_cmd._rebuild_index(wiki, self._inventory(), str(tmp_path))

        index = (wiki / "index.md").read_text(encoding="utf-8")
        assert "## Surface Overview" in index
        assert "| User flows | 2 |" in index
        assert "| Dependency architecture | 0 |" in index
        assert "| Log | 1 | [Open log](log.md) |" in index
        assert "## User Flows" in index
        assert "**api**" in index
        assert "**process**" in index
        assert "[api-run](flows/api-run.md)" in index
        assert "[process-cli](flows/process-cli.md)" in index
        assert "## Dependency Architecture" not in index

    def test_rebuild_index_includes_existing_guide_pages(self, tmp_path):
        wiki = tmp_path / "wiki"
        (wiki / "guides").mkdir(parents=True)
        (wiki / "guides" / "operator-onboarding.md").write_text(
            "# Operator onboarding\n",
            encoding="utf-8",
        )
        (wiki / "log.md").write_text("# Architectural Log\n", encoding="utf-8")

        sync_cmd._rebuild_index(wiki, self._inventory(), str(tmp_path))

        index = (wiki / "index.md").read_text(encoding="utf-8")
        assert "| Guides | 1 | [Open section](#guides) |" in index
        assert "## Guides" in index
        assert "[Operator onboarding](guides/operator-onboarding.md)" in index

    def test_rebuild_index_links_existing_architecture_pages(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "dependencies.md").write_text("# Dependencies\n")
        (wiki / "load-order.md").write_text("# Load order\n")

        sync_cmd._rebuild_index(wiki, self._inventory(), str(tmp_path))

        index = (wiki / "index.md").read_text(encoding="utf-8")
        assert "| Dependency architecture | 2 |" in index
        assert "## Dependency Architecture" in index
        assert "[Dependencies](dependencies.md)" in index
        assert "[Load order](load-order.md)" in index

    def test_rebuild_index_leaves_flow_pages_untouched(self, tmp_path):
        wiki = tmp_path / "wiki"
        (wiki / "flows").mkdir(parents=True)
        page = wiki / "flows" / "api-run.md"
        original = "# run\n\nHand-written semantic behavior notes.\n"
        page.write_text(original)

        sync_cmd._rebuild_index(wiki, self._inventory(), str(tmp_path))

        assert page.read_text(encoding="utf-8") == original

    def test_rebuild_index_preserves_custom_index_sections(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text(
            textwrap.dedent("""\
                # Old Index

                Remember the deployment checklist.

                ## Custom Notes

                Keep the payment flow review link here.
            """),
            encoding="utf-8",
        )

        sync_cmd._rebuild_index(
            wiki, self._inventory(), str(tmp_path), preserve_semantic=True
        )

        index = (wiki / "index.md").read_text(encoding="utf-8")
        assert "## Notes" in index
        assert "Remember the deployment checklist." in index
        assert "## Custom Notes" in index
        assert "Keep the payment flow review link here." in index

    def test_rebuild_index_no_preserve_semantic_drops_custom_index_sections(
        self, tmp_path
    ):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text(
            textwrap.dedent("""\
                # Old Index

                Remember the deployment checklist.

                ## Custom Notes

                Keep the payment flow review link here.
            """),
            encoding="utf-8",
        )

        sync_cmd._rebuild_index(
            wiki, self._inventory(), str(tmp_path), preserve_semantic=False
        )

        index = (wiki / "index.md").read_text(encoding="utf-8")
        assert "Remember the deployment checklist." not in index
        assert "## Custom Notes" not in index
        assert "Keep the payment flow review link here." not in index


class TestSyncIndexCustomSections:
    def _inventory(self):
        return {
            "api.py": {
                "language": "python",
                "classes": [],
                "functions": [{"name": "run", "line": 1}],
            }
        }

    def test_rebuild_index_preserves_custom_section_links_for_strict_lint(
        self, tmp_path
    ):
        wiki = tmp_path / "wiki"
        config_docs = wiki / "config_docs"
        config_docs.mkdir(parents=True)
        (config_docs / "recording_rules_yml.md").write_text(
            "# Recording rules\n", encoding="utf-8"
        )
        (config_docs / "grafana_dashboards.md").write_text(
            "# Grafana dashboards\n", encoding="utf-8"
        )
        (wiki / "index.md").write_text(
            textwrap.dedent("""\
                # Old Index

                ## Configuration Docs

                - [Recording rules](config_docs/recording_rules_yml.md)
                - [Grafana dashboards](config_docs/grafana_dashboards.md)
            """),
            encoding="utf-8",
        )

        sync_cmd._rebuild_index(
            wiki, self._inventory(), str(tmp_path), preserve_semantic=True
        )

        index = (wiki / "index.md").read_text(encoding="utf-8")
        assert "## Configuration Docs" in index
        assert "config_docs/recording_rules_yml.md" in index
        assert "config_docs/grafana_dashboards.md" in index

        page_index = lint_cmd._build_page_index(wiki)
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))
        lint_cmd._check_orphan_pages(report, wiki, page_index)
        assert report.count("orphan_pages") == 0

    def test_rebuild_index_no_preserve_semantic_drops_custom_section_links(
        self, tmp_path
    ):
        wiki = tmp_path / "wiki"
        config_docs = wiki / "config_docs"
        config_docs.mkdir(parents=True)
        (config_docs / "recording_rules_yml.md").write_text(
            "# Recording rules\n", encoding="utf-8"
        )
        (wiki / "index.md").write_text(
            textwrap.dedent("""\
                # Old Index

                ## Configuration Docs

                - [Recording rules](config_docs/recording_rules_yml.md)
            """),
            encoding="utf-8",
        )

        sync_cmd._rebuild_index(
            wiki, self._inventory(), str(tmp_path), preserve_semantic=False
        )

        index = (wiki / "index.md").read_text(encoding="utf-8")
        assert "## Configuration Docs" not in index
        assert "config_docs/recording_rules_yml.md" not in index


class TestSyncFlowRegeneration:
    def _write_svc(self, proj, callee):
        (proj / "svc.py").write_text(
            textwrap.dedent(f"""\
            __all__ = ["run"]


            def run():
                return {callee}()


            def helper_a():
                return 1


            def helper_b():
                return 2
        """)
        )

    def _new_project(self, tmp_path, callee):
        import subprocess

        proj = tmp_path / "proj"
        proj.mkdir()
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        (proj / "pyproject.toml").write_text(
            '[project]\nname = "p"\nversion = "0.1.0"\n'
        )
        self._write_svc(proj, callee)
        return proj, proj / "docs" / "llm_wiki"

    def _write_svc_with_arg(self, proj, value):
        (proj / "svc.py").write_text(
            textwrap.dedent(f"""\
            __all__ = ["run"]


            def run(path):
                result = helper("{value}")
                path.write_text(result)
                return result


            def helper(value):
                return value
        """)
        )

    def test_regenerates_changed_flow_and_preserves_behavior(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))

        flow_page = wiki / "flows" / "api-run.md"
        original = flow_page.read_text(encoding="utf-8")
        assert "helper_a" in original
        # Human edits the Behavior section.
        flow_page.write_text(
            sync_cmd._replace_section_body(
                original, "Behavior", "Runs the primary path."
            ),
            encoding="utf-8",
        )

        # Change the code so the diagram changes, then sync.
        self._write_svc(proj, "helper_b")
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        updated = flow_page.read_text(encoding="utf-8")
        assert "helper_b" in updated  # diagram regenerated
        assert "helper_a" not in updated  # old call removed
        assert "Runs the primary path." in updated  # human Behavior preserved

    def test_regenerates_data_flow_for_changed_call_argument(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        self._write_svc_with_arg(proj, "alpha")
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))

        flow_page = wiki / "flows" / "api-run.md"
        original = flow_page.read_text(encoding="utf-8")
        assert "helper('alpha')" in original
        flow_page.write_text(
            sync_cmd._replace_section_body(
                original, "Behavior", "Keeps the reviewed behavior notes."
            ),
            encoding="utf-8",
        )

        self._write_svc_with_arg(proj, "beta")
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        updated = flow_page.read_text(encoding="utf-8")
        assert "helper('beta')" in updated
        assert "helper('alpha')" not in updated
        assert "| filesystem_write | `path.write_text` | `run` |" in updated
        assert "Keeps the reviewed behavior notes." in updated

    def test_sync_preserves_bounded_plugin_style_on_regenerated_data_flow(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        self._write_svc_with_arg(proj, "alpha")
        _write_diagram_style_plugin(
            proj,
            body="""
            def style(context):
                assert context["surface"] == "data_flow"
                return {
                    "direction": "RL",
                    "node_classes": {
                        "1. run": "entry",
                        "2. helper": "worker",
                    },
                    "category_colors": {
                        "entry": "#abc",
                        "worker": "#123456",
                    },
                    "markdown": "```markdown\\n# injected",
                }
            """,
        )
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))

        flow_page = wiki / "flows" / "api-run.md"
        original = flow_page.read_text(encoding="utf-8")
        assert "```mermaid\nflowchart RL" in original
        assert "    class s1 entry" in original
        assert "# injected" not in original
        bootstrap_knowledge = load_knowledge_state(wiki).knowledge
        assert bootstrap_knowledge is not None
        assert [
            component.component_id
            for component in bootstrap_knowledge.bundle.producer.plugins
        ] == ["diagram-style-plugin"]
        assert bootstrap_knowledge.bundle.producer.plugins[0].version == "0.1.0"
        assert str(proj) not in (wiki / ".llm-wiki-knowledge.json").read_text(
            encoding="utf-8"
        )

        self._write_svc_with_arg(proj, "beta")
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        updated = flow_page.read_text(encoding="utf-8")
        assert "helper('beta')" in updated
        assert "```mermaid\nflowchart RL" in updated
        assert "    class s1 entry" in updated
        assert "    classDef worker fill:#123456,stroke:#123456" in updated
        assert "# injected" not in updated
        sync_knowledge = load_knowledge_state(wiki).knowledge
        assert sync_knowledge is not None
        assert sync_knowledge.bundle.producer == (bootstrap_knowledge.bundle.producer)

    def test_plugin_lock_change_updates_producer_basis_without_source_change(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        _write_diagram_style_plugin(
            proj,
            body="""
            def style(context):
                return {"direction": "RL"}
            """,
        )
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))
        before = load_knowledge_state(wiki).knowledge
        assert before is not None
        lock = plugins.lock_path(proj)
        lock_payload = json.loads(lock.read_text(encoding="utf-8"))
        lock_payload["plugins"]["diagram-style-plugin"]["version"] = "0.2.0"
        lock.write_text(
            json.dumps(lock_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        capsys.readouterr()

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        after = load_knowledge_state(wiki).knowledge
        assert after is not None
        assert after.bundle.producer.plugins[0].version == "0.2.0"
        assert after.bundle.producer != before.bundle.producer
        assert after.bundle.snapshot.source_snapshot_hash != (
            before.bundle.snapshot.source_snapshot_hash
        )
        assert after.bundle.snapshot.generation_options_hash == (
            before.bundle.snapshot.generation_options_hash
        )

    def test_removed_source_does_not_bind_tombstone_to_upgraded_same_id_extractor(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        (proj / "alpha.jscustom").write_text("function alpha() { return 1; }\n")
        (proj / "beta.jscustom").write_text("function beta() { return 2; }\n")
        _write_toy_extractor_plugin(proj)
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))
        before = load_knowledge_state(wiki)
        assert before.status is KnowledgeLoadState.VALID
        assert before.manifest_basis is not None
        assert before.knowledge is not None
        prior_extractor = {
            component.component_id: component
            for component in before.knowledge.bundle.producer.extractors
        }["toy-extractor/toy"]
        prior = before.manifest_basis.evidence_baselines["modules/alpha.md"]
        assert prior.is_known
        assert prior.basis is not None
        assert prior.basis.extractor_ref == "toy-extractor/toy"

        (proj / "alpha.jscustom").unlink()
        lock = plugins.lock_path(proj)
        lock_payload = json.loads(lock.read_text(encoding="utf-8"))
        plugin = lock_payload["plugins"]["toy-extractor"]
        plugin["version"] = "0.2.0"
        plugin["components"][0]["parallel_safe"] = True
        lock.write_text(
            json.dumps(lock_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        capsys.readouterr()

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        after = load_knowledge_state(wiki)
        assert after.status is KnowledgeLoadState.VALID
        assert after.manifest_basis is not None
        assert after.knowledge is not None
        tombstone = after.manifest_basis.tombstones["modules/alpha.md"]
        assert tombstone.reason == TOMBSTONE_UNKNOWN_PROVENANCE
        assert tombstone.last_valid_basis is None
        assert tombstone.unknown_reason == PRODUCER_BASIS_INCOMPATIBLE
        alpha = next(
            concept
            for concept in after.knowledge.concepts
            if concept.document.canonical_path == "modules/alpha.md"
        )
        assert alpha.facets.structure.basis is None
        current = {
            component.component_id: component
            for component in after.knowledge.bundle.producer.extractors
        }["toy-extractor/toy"]
        assert current.version == "0.2.0"
        assert current.configuration_hash != prior_extractor.configuration_hash

    def test_removed_source_does_not_bind_tombstone_to_upgraded_tool(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        (proj / "alpha.jscustom").write_text("function alpha() { return 1; }\n")
        (proj / "beta.jscustom").write_text("function beta() { return 2; }\n")
        _write_toy_extractor_plugin(proj)
        monkeypatch.chdir(proj)
        monkeypatch.setattr(knowledge_orchestration, "__version__", "1.0.0")
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))
        before = load_knowledge_state(wiki)
        assert before.status is KnowledgeLoadState.VALID
        assert before.knowledge is not None
        prior_producer = before.knowledge.bundle.producer
        assert prior_producer.tool.version == "1.0.0"

        (proj / "alpha.jscustom").unlink()
        monkeypatch.setattr(knowledge_orchestration, "__version__", "2.0.0")
        capsys.readouterr()

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        after = load_knowledge_state(wiki)
        assert after.status is KnowledgeLoadState.VALID
        assert after.manifest_basis is not None
        assert after.knowledge is not None
        current_producer = after.knowledge.bundle.producer
        assert current_producer.tool.version == "2.0.0"
        prior_toy = {
            component.component_id: component for component in prior_producer.extractors
        }["toy-extractor/toy"]
        current_toy = {
            component.component_id: component
            for component in current_producer.extractors
        }["toy-extractor/toy"]
        assert current_toy == prior_toy
        tombstone = after.manifest_basis.tombstones["modules/alpha.md"]
        assert tombstone.reason == TOMBSTONE_UNKNOWN_PROVENANCE
        assert tombstone.last_valid_basis is None
        assert tombstone.unknown_reason == PRODUCER_BASIS_INCOMPATIBLE

    def test_sync_uses_source_root_plugin_style_when_cwd_differs(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        self._write_svc_with_arg(proj, "alpha")
        _write_diagram_style_plugin(
            proj,
            body="""
            def style(context):
                if context["surface"] == "data_flow":
                    return {"direction": "RL"}
                return {}
            """,
        )
        _write_diagram_style_plugin(
            tmp_path,
            body="""
            def style(context):
                if context["surface"] == "data_flow":
                    return {"direction": "TD"}
                return {}
            """,
        )
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(
            _make_bootstrap_args(src_dir="proj", wiki_dir="proj/docs/llm_wiki")
        )

        flow_page = wiki / "flows" / "api-run.md"
        original = flow_page.read_text(encoding="utf-8")
        assert "```mermaid\nflowchart RL" in original
        source_root_knowledge = load_knowledge_state(wiki).knowledge
        assert source_root_knowledge is not None
        assert [
            component.component_id
            for component in source_root_knowledge.bundle.producer.plugins
        ] == ["diagram-style-plugin"]

        self._write_svc_with_arg(proj, "beta")
        sync_cmd.run(_make_sync_args(src_dir="proj", wiki_dir="proj/docs/llm_wiki"))

        updated = flow_page.read_text(encoding="utf-8")
        assert "helper('beta')" in updated
        assert "```mermaid\nflowchart RL" in updated

    def test_flow_regeneration_reuses_single_data_flow_context(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))
        calls = 0
        real_build_context = sync_cmd.build_data_flow_context

        def counted_build_context(*args, **kwargs):
            nonlocal calls
            calls += 1
            return real_build_context(*args, **kwargs)

        monkeypatch.setattr(sync_cmd, "build_data_flow_context", counted_build_context)

        self._write_svc(proj, "helper_b")
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        assert calls == 1
        assert "helper_b" in (wiki / "flows" / "api-run.md").read_text(encoding="utf-8")

    def test_runtime_plan_receives_reused_graph_analyzer_observations(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))
        capsys.readouterr()
        (proj / "pyproject.toml").write_text(
            '[project]\nname = "p"\nversion = "0.1.0"\n'
            'dependencies = ["requests"]\n',
            encoding="utf-8",
        )
        constants = "\n".join(f"CONFIG_{index} = {index}" for index in range(20))
        reads = ", ".join(f"CONFIG_{index}" for index in range(20))
        (proj / "svc.py").write_text(
            "import requests\n\n"
            f"{constants}\n\n"
            '__all__ = ["run"]\n\n'
            "def run():\n"
            f"    values = ({reads})\n"
            '    requests.get("https://example.invalid")\n'
            "    return helper_b()\n\n"
            "def helper_b():\n"
            "    return 2\n",
            encoding="utf-8",
        )
        captured = []
        detailed_results = []
        real_build_plan = knowledge_orchestration.build_runtime_knowledge_plan
        real_analyze = sync_cmd.analyze_data_flow_detailed

        def capture_plan(inputs):
            captured.append(inputs)
            return real_build_plan(inputs)

        def capture_data_flow(*args, **kwargs):
            result = real_analyze(*args, **kwargs)
            detailed_results.append(result)
            return result

        monkeypatch.setattr(
            knowledge_orchestration,
            "build_runtime_knowledge_plan",
            capture_plan,
        )
        monkeypatch.setattr(
            sync_cmd,
            "analyze_data_flow_detailed",
            capture_data_flow,
        )

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        assert len(captured) == 1
        runtime = captured[0]
        assert runtime.call_edges["schema_version"] == "llm-wiki-call-observations/v1"
        assert runtime.call_edges["observations"]
        assert any(
            observation["module"] == "requests"
            for observation in runtime.dependency_observations["observations"]
        )
        assert next(
            observation
            for observation in runtime.dependency_observations["observations"]
            if observation["module"] == "requests"
        )["line"] == 1
        assert runtime.entrypoint_observations["observations"][0]["detector"][
            "id"
        ].startswith("builtin.")
        assert runtime.flows[0]["entry"]["id"] == "api-run"
        assert runtime.flows[0]["schema_version"] == "llm-wiki-flow-observations/v1"
        assert runtime.data_flows[0] is detailed_results[0]
        assert runtime.data_flows[0]["coverage"]["steps"]["observed"] >= 1
        reads_coverage = runtime.data_flows[0]["coverage"]["effects"]["by_kind"][
            "reads"
        ]
        assert reads_coverage["observed"] == 20
        assert reads_coverage["emitted"] == 8
        assert reads_coverage["omitted"] == 12
        assert any(
            dependency["package"] == "requests" and dependency["explicit"]
            for dependency in runtime.external_dependencies
        )

    def test_regenerates_plugin_detector_flow_and_surface_index(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        _write_entrypoint_detector_plugin(
            proj,
            body="""
            def detect(inventory):
                return [{
                    "category": "task",
                    "file": "svc.py",
                    "symbol": "run",
                    "label": "task-handler",
                }]
            """,
        )
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))
        capsys.readouterr()

        self._write_svc(proj, "helper_b")
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        flow_page = wiki / "flows" / "task-task-handler.md"
        assert "helper_b" in flow_page.read_text(encoding="utf-8")
        surface = json.loads(
            (wiki / SURFACE_INDEX_FILENAME).read_text(encoding="utf-8")
        )
        assert {
            "id": "task-task-handler",
            "category": "task",
            "entry_point": {
                "symbol": "run",
                "source_path": "svc.py",
                "label": "task-handler",
            },
        } in surface["flows"]

    def test_plugin_detector_failure_warns_once_during_sync(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        _write_entrypoint_detector_plugin(
            proj,
            body="""
            def detect(inventory):
                raise RuntimeError("sync detector failed")
            """,
        )
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))
        capsys.readouterr()

        self._write_svc(proj, "helper_b")
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        assert out.count("sync detector failed") == 1
        assert "Warning:" in out
        assert "helper_b" in (wiki / "flows" / "api-run.md").read_text(encoding="utf-8")

    def test_does_not_create_flows_when_opted_out(self, tmp_path, monkeypatch, capsys):
        proj, wiki = self._new_project(tmp_path, "helper_a")
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(
            _make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki), skip_flows=True)
        )
        assert not list((wiki / "flows").glob("*.md"))

        self._write_svc(proj, "helper_b")
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        assert not list((wiki / "flows").glob("*.md"))


class TestSyncDependencyRegeneration:
    def _write_modules(self, proj, app_body):
        (proj / "core.py").write_text("def core():\n    return 1\n")
        (proj / "app.py").write_text(app_body)

    def _new_project(self, tmp_path):
        import subprocess

        proj = tmp_path / "proj"
        proj.mkdir()
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        (proj / "pyproject.toml").write_text(
            '[project]\nname = "p"\nversion = "0.1.0"\n'
        )
        return proj, proj / "docs" / "llm_wiki"

    def test_regenerates_graph_and_preserves_notes(self, tmp_path, monkeypatch, capsys):
        proj, wiki = self._new_project(tmp_path)
        self._write_modules(proj, "def go():\n    return 1\n")  # no internal import yet
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))

        deps_page = wiki / "dependencies.md"
        load_page = wiki / "load-order.md"
        original_deps = deps_page.read_text(encoding="utf-8")
        original_load = load_page.read_text(encoding="utf-8")
        deps_page.write_text(
            sync_cmd._replace_section_body(
                original_deps, "Notes", "Reviewed; no dependency concerns."
            ),
            encoding="utf-8",
        )
        load_page.write_text(
            sync_cmd._replace_section_body(
                original_load, "Notes", "Core must load before app."
            ),
            encoding="utf-8",
        )

        # app.py now imports core → a new internal edge appears.
        self._write_modules(
            proj, "import core\n\n\ndef go():\n    return core.core()\n"
        )
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        updated_deps = deps_page.read_text(encoding="utf-8")
        assert "| [core](modules/core.md) | 1 | 0 |" in updated_deps
        assert "Reviewed; no dependency concerns." in updated_deps

        updated_load = load_page.read_text(encoding="utf-8")
        assert "1. [core](modules/core.md)" in updated_load
        assert "2. [app](modules/app.md)" in updated_load
        assert "Core must load before app." in updated_load

        # Architecture pages stay linked from the index (not orphaned).
        index = (wiki / "index.md").read_text(encoding="utf-8")
        assert "## Dependency Architecture" in index
        assert "[Dependencies](dependencies.md)" in index

    def test_unrelated_source_edit_does_not_rewrite_architecture_pages(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path)
        self._write_modules(
            proj, "import core\n\n\ndef go():\n    return core.core()\n"
        )
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))

        architecture_writes = []
        original_write_md = sync_cmd.write_md

        def record_architecture_writes(path, text):
            if path.name in {"dependencies.md", "load-order.md"}:
                architecture_writes.append(path.name)
            original_write_md(path, text)

        monkeypatch.setattr(sync_cmd, "write_md", record_architecture_writes)

        self._write_modules(
            proj, "import core\n\n\ndef go():\n    return core.core() + 1\n"
        )
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        assert architecture_writes == []

    def test_opted_out_project_stays_untouched(self, tmp_path, monkeypatch, capsys):
        proj, wiki = self._new_project(tmp_path)
        self._write_modules(proj, "def go():\n    return 1\n")
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(
            _make_bootstrap_args(
                src_dir=str(proj), wiki_dir=str(wiki), skip_dependencies=True
            )
        )
        assert not (wiki / "dependencies.md").exists()

        self._write_modules(
            proj, "import core\n\n\ndef go():\n    return core.core()\n"
        )
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))
        assert not (wiki / "dependencies.md").exists()
        assert not (wiki / "load-order.md").exists()

    def test_dependency_regeneration_reuses_single_sync_inventory_extraction(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path)
        self._write_modules(proj, "def go():\n    return 1\n")
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))

        calls = 0
        real_get_inventory_result = sync_cmd.get_inventory_result

        def counted_get_inventory_result(*args, **kwargs):
            nonlocal calls
            calls += 1
            return real_get_inventory_result(*args, **kwargs)

        monkeypatch.setattr(
            sync_cmd, "get_inventory_result", counted_get_inventory_result
        )

        self._write_modules(
            proj, "import core\n\n\ndef go():\n    return core.core()\n"
        )
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        assert calls == 1
        assert "| [core](modules/core.md) | 1 | 0 |" in (
            wiki / "dependencies.md"
        ).read_text(encoding="utf-8")


class TestSyncGeneratedRelationshipSections:
    def _new_project(self, tmp_path):
        import subprocess

        proj = tmp_path / "proj"
        proj.mkdir()
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        (proj / "pyproject.toml").write_text(
            '[project]\nname = "p"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        return proj, proj / "docs" / "llm_wiki"

    def _write_relationship_project(self, proj: Path, service_body: str) -> None:
        (proj / "models.py").write_text(
            textwrap.dedent("""\
                class User:
                    \"\"\"A system user.\"\"\"
                    name: str = ""
            """),
            encoding="utf-8",
        )
        (proj / "service.py").write_text(service_body, encoding="utf-8")

    def test_changed_reference_updates_unchanged_entity_relationship_section(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path)
        self._write_relationship_project(
            proj,
            textwrap.dedent("""\
                from models import User

                def make_user(user: User) -> User:
                    return user
            """),
        )
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))

        entity_path = wiki / "entities" / "User.md"
        original = entity_path.read_text(encoding="utf-8")
        entity_path.write_text(
            sync_cmd._replace_section_body(
                original, "Description", "Human-reviewed user entity."
            ),
            encoding="utf-8",
        )

        self._write_relationship_project(
            proj,
            textwrap.dedent("""\
                def make_value() -> int:
                    return 1
            """),
        )
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        updated = entity_path.read_text(encoding="utf-8")
        relationships = updated.split("## Relationships", 1)[1]
        assert "Human-reviewed user entity." in updated
        assert "service.py" not in relationships
        assert "No generated relationships detected" in relationships
        assert "UPDATE entity relationships: User" in out

    def test_generated_relationship_churn_preserves_matching_human_review(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path)
        self._write_relationship_project(
            proj,
            textwrap.dedent("""\
                from models import User

                def make_user(user: User) -> User:
                    return user
            """),
        )
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(
            _make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki))
        )

        entity_path = wiki / "entities" / "User.md"
        original = entity_path.read_text(encoding="utf-8")
        entity_path.write_text(
            sync_cmd._replace_section_body(
                original,
                "Description",
                "Human-reviewed user entity.",
            ),
            encoding="utf-8",
        )
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        init_args = cli._build_parser().parse_args(
            [
                "knowledge",
                "init",
                "--wiki-dir",
                str(wiki),
                "--bundle-id",
                "kb_sync_review_churn",
            ]
        )
        knowledge_cmd.run(init_args)
        state_before = load_knowledge_state(wiki)
        assert state_before.knowledge is not None
        knowledge_before = state_before.knowledge
        pages = knowledge_before.extensions[
            SECTION_OWNERSHIP_EXTENSION_KEY
        ]["pages"]
        user_sections = next(
            page["sections"]
            for page in pages
            if page["page_locator"] == "llm-wiki://entities/User"
        )
        description = next(
            section
            for section in user_sections
            if section["title"] == "Description"
        )
        ledger_before = load_governance(wiki).ledger
        uid = next(
            uid
            for uid, allocation in ledger_before.concepts.items()
            if allocation.locator == "llm-wiki://entities/User"
        )
        concept_before = next(
            concept
            for concept in knowledge_before.concepts
            if concept.locator == "llm-wiki://entities/User"
        )
        scope_hash_before = review_scope_hash(
            knowledge_before,
            description["locator"],
        )
        evidence_before = current_review_evidence(concept_before)
        assert evidence_before is not None

        review_args = cli._build_parser().parse_args(
            [
                "knowledge",
                "review",
                "--wiki-dir",
                str(wiki),
                "--uid",
                uid,
                "--section",
                description["locator"],
                "--reviewer-kind",
                "human",
                "--reviewer-id",
                "alice",
                "--method",
                "manual-review",
                "--method-version",
                "1",
                "--authored-at",
                "2026-07-27T12:00:00Z",
            ]
        )
        knowledge_cmd.run(review_args)
        reviewed = load_governance(wiki).ledger
        event = next(iter(reviewed.review_events.values()))
        before_relationships = entity_path.read_text(encoding="utf-8").split(
            "## Relationships",
            1,
        )[1]
        assert "service.py" in before_relationships

        (proj / "service.py").write_text(
            "def make_value() -> int:\n    return 1\n",
            encoding="utf-8",
        )
        capsys.readouterr()
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        state_after = load_knowledge_state(wiki)
        assert state_after.knowledge is not None
        knowledge_after = state_after.knowledge
        concept_after = next(
            concept
            for concept in knowledge_after.concepts
            if concept.locator == "llm-wiki://entities/User"
        )
        after_relationships = entity_path.read_text(encoding="utf-8").split(
            "## Relationships",
            1,
        )[1]
        assert before_relationships != after_relationships
        assert "No generated relationships detected" in after_relationships
        assert review_scope_hash(
            knowledge_after,
            description["locator"],
        ) == scope_hash_before
        assert current_review_evidence(concept_after) == evidence_before
        current_ledger = load_governance(wiki).ledger
        assert current_ledger.review_events[event.event_id] == event
        assert evaluate_review_event(
            event,
            current_ledger,
            knowledge_after,
        ).reasons == ()

    def test_changed_import_graph_updates_unchanged_module_local_maps(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path)
        (proj / "core.py").write_text("def core():\n    return 1\n", encoding="utf-8")
        (proj / "app.py").write_text(
            "import core\n\n\ndef go():\n    return core.core()\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))

        core_module = wiki / "modules" / "core.md"
        assert "[app](../modules/app.md)" in core_module.read_text(encoding="utf-8")

        (proj / "app.py").write_text("def go():\n    return 1\n", encoding="utf-8")
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        updated_core = core_module.read_text(encoding="utf-8")
        local_map = updated_core.split("## Local dependency map", 1)[1]
        assert "[app](app.md)" not in local_map
        assert "No internal module dependencies detected" in local_map
        assert "UPDATE module local dependency map: core" in out

    def test_no_preserve_semantic_keeps_generated_relationships_current(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path)
        self._write_relationship_project(
            proj,
            textwrap.dedent("""\
                from models import User

                def make_user(user: User) -> User:
                    return user
            """),
        )
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(_make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki)))

        entity_path = wiki / "entities" / "User.md"
        original = entity_path.read_text(encoding="utf-8")
        entity_path.write_text(
            sync_cmd._replace_section_body(
                original, "Description", "Human-reviewed user entity."
            ),
            encoding="utf-8",
        )
        (proj / "models.py").write_text(
            textwrap.dedent("""\
                class User:
                    \"\"\"Current generated user entity.\"\"\"
                    name: str = ""
            """),
            encoding="utf-8",
        )

        sync_cmd.run(
            _make_sync_args(
                src_dir=str(proj),
                wiki_dir=str(wiki),
                no_preserve_semantic=True,
            )
        )

        updated = entity_path.read_text(encoding="utf-8")
        assert "Human-reviewed user entity." not in updated
        assert "Current generated user entity." in updated
        assert "service.py" in updated

    def test_module_maps_are_not_added_to_old_pages_without_existing_section(
        self, tmp_path, monkeypatch, capsys
    ):
        proj, wiki = self._new_project(tmp_path)
        (proj / "core.py").write_text("def core():\n    return 1\n", encoding="utf-8")
        (proj / "app.py").write_text(
            "import core\n\n\ndef go():\n    return core.core()\n",
            encoding="utf-8",
        )
        monkeypatch.chdir(proj)
        bootstrap_cmd.run(
            _make_bootstrap_args(
                src_dir=str(proj), wiki_dir=str(wiki), skip_dependencies=True
            )
        )
        module_path = wiki / "modules" / "app.md"
        assert "## Local dependency map" not in module_path.read_text(encoding="utf-8")

        (proj / "app.py").write_text(
            "import core\n\n\ndef go():\n    return core.core() + 1\n",
            encoding="utf-8",
        )
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki)))

        updated = module_path.read_text(encoding="utf-8")
        assert "## Local dependency map" not in updated
