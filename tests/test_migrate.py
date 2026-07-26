"""Tests for llm-wiki migrate."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import lint_cmd, migrate_cmd
from llm_wiki_cli.commands.migrate_cmd import (
    ExistingPage,
    TargetPage,
    _build_chunks,
    _build_match_lookups,
    _match_existing_page,
    _read_existing_page,
    _rewrite_links_in_content,
    _split_location,
)
from llm_wiki_cli.commands.sync_cmd import MANIFEST_FILENAME
from llm_wiki_cli.services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from llm_wiki_cli.services.knowledge_evidence import (
    MODULE_OBSERVATION_SCOPE,
    ConceptObservationBasis,
    hash_file,
    sha256_bytes,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState, WorkingTreeState
from llm_wiki_cli.services.knowledge_orchestration import (
    build_runtime_knowledge_plan,
)
from llm_wiki_cli.services.sync_manifest import (
    ManifestEvidenceBaseline,
    ManifestPageSource,
    SyncManifest,
)
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME

NODE_AVAILABLE = shutil.which("node") is not None
TS_NODE_MODULES = (
    Path(__file__).parents[1]
    / "src"
    / "llm_wiki_cli"
    / "extractors"
    / "ts_scripts"
    / "node_modules"
).exists()
skip_no_ts = pytest.mark.skipif(
    not (NODE_AVAILABLE and TS_NODE_MODULES),
    reason="Node.js/ts-morph dependencies not available",
)


def _make_args(**kwargs):
    defaults = {"src_dir": ".", "wiki_dir": "docs/llm_wiki", "dry_run": False}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def _make_wiki(proj: Path) -> Path:
    wiki = proj / "docs" / "llm_wiki"
    for subdir in ["entities", "modules", "workflows", "infrastructure"]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    _write(wiki / "index.md", "# Old Index\n")
    _write(wiki / "log.md", "# Log\n")
    return wiki


def _has_legacy_archive(wiki: Path, *parts: str) -> bool:
    legacy_root = wiki / "legacy"
    return any(
        (archive / Path(*parts)).exists() for archive in legacy_root.glob("migrate-*")
    )


def _legacy_archive_names(wiki: Path) -> list[str]:
    legacy_root = wiki / "legacy"
    if not legacy_root.exists():
        return []
    return sorted(path.name for path in legacy_root.glob("migrate-*") if path.is_dir())


class TestMigrateHelpers:
    def test_canonical_saved_manifest_is_not_planned_for_rewrite(self, tmp_path):
        wiki = tmp_path / "wiki"
        manifest = SyncManifest(
            surfaces={"flows": {"enabled": True}},
            generation_inputs={"openapi_file": "openapi.json"},
        )
        manifest.save(wiki)

        assert migrate_cmd._manifest_payload(manifest) == (
            wiki / MANIFEST_FILENAME
        ).read_text(encoding="utf-8")
        assert migrate_cmd._manifest_needs_write(wiki, manifest) is False

    def test_command_migrates_v4_generation_state_and_commits_current_evidence(
        self, tmp_path, monkeypatch
    ):
        project = tmp_path / "project"
        project.mkdir()
        _write(project / "alpha.py", "def alpha():\n    return 1\n")
        wiki = _make_wiki(project)
        legacy_state = {
            "version": 4,
            "sources": {},
            "surfaces": {"flows": {"enabled": True}},
            "generation_inputs": {"openapi_file": "openapi.json"},
        }
        (wiki / MANIFEST_FILENAME).write_text(
            json.dumps(legacy_state), encoding="utf-8"
        )
        monkeypatch.chdir(project)

        migrate_cmd.run(_make_args())

        payload = json.loads((wiki / MANIFEST_FILENAME).read_text(encoding="utf-8"))
        assert payload["version"] == 5
        assert payload["surfaces"] == legacy_state["surfaces"]
        assert payload["generation_inputs"] == legacy_state["generation_inputs"]
        assert "artifact_hashes" in payload
        assert payload["tombstones"] == {}
        assert {
            baseline["state"] for baseline in payload["evidence_baselines"].values()
        } == {"known"}
        assert load_knowledge_state(wiki).status is KnowledgeLoadState.VALID

    def test_v4_same_path_regeneration_promotes_unknown_evidence(
        self, tmp_path, monkeypatch
    ):
        project = tmp_path / "project"
        project.mkdir()
        source = project / "alpha.py"
        _write(source, "def alpha():\n    return 1\n")
        wiki = _make_wiki(project)
        _write(
            wiki / "modules" / "alpha.md",
            "# Legacy Alpha\n\n**Path:** `alpha.py`\n\nRetained migration notes.\n",
        )
        source_hash = hash_file(source)
        legacy_state = {
            "version": 4,
            "sources": {
                "alpha.py": {
                    "hash": source_hash,
                    "semantic_hash": sha256_bytes(b"legacy semantics"),
                    "generated_semantics": {},
                    "language": "python",
                    "entities": [],
                    "entity_pages": {},
                    "entity_page_occurrences": [],
                    "module_page": "alpha",
                }
            },
            "surfaces": {},
            "generation_inputs": {},
        }
        (wiki / MANIFEST_FILENAME).write_text(
            json.dumps(legacy_state), encoding="utf-8"
        )
        prior = SyncManifest.load(wiki)
        assert not prior.evidence_baselines["modules/alpha.md"].is_known
        monkeypatch.chdir(project)

        migrate_cmd.run(_make_args())

        migrated = SyncManifest.load(wiki)
        assert migrated.evidence_baselines["modules/alpha.md"].is_known
        assert load_knowledge_state(wiki).status is KnowledgeLoadState.VALID

    def test_chunked_v4_regeneration_promotes_every_rewritten_page(
        self,
        tmp_path,
        monkeypatch,
    ):
        project = tmp_path / "project"
        project.mkdir()
        sources = {}
        wiki = _make_wiki(project)
        for name in ("alpha", "beta"):
            source = project / f"{name}.py"
            _write(source, f"def {name}():\n    return 1\n")
            _write(
                wiki / "modules" / f"{name}.md",
                f"# Legacy {name.title()}\n\n**Path:** `{name}.py`\n",
            )
            sources[f"{name}.py"] = {
                "hash": hash_file(source),
                "semantic_hash": sha256_bytes(f"{name} semantics".encode()),
                "generated_semantics": {},
                "language": "python",
                "entities": [],
                "entity_pages": {},
                "entity_page_occurrences": [],
                "module_page": name,
            }
        (wiki / MANIFEST_FILENAME).write_text(
            json.dumps(
                {
                    "version": 4,
                    "sources": sources,
                    "surfaces": {},
                    "generation_inputs": {},
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.chdir(project)

        migrate_cmd.run(_make_args(chunk_size=1))
        assert (wiki / migrate_cmd.MIGRATION_PROGRESS_FILENAME).is_file()
        migrate_cmd.run(_make_args(chunk_size=1))

        migrated = SyncManifest.load(wiki)
        assert {
            page_path: baseline.is_known
            for page_path, baseline in migrated.evidence_baselines.items()
            if page_path in {"modules/alpha.md", "modules/beta.md"}
        } == {
            "modules/alpha.md": True,
            "modules/beta.md": True,
        }
        assert not (wiki / migrate_cmd.MIGRATION_PROGRESS_FILENAME).exists()
        assert load_knowledge_state(wiki).status is KnowledgeLoadState.VALID

        (wiki / migrate_cmd.MIGRATION_PROGRESS_FILENAME).write_text(
            "{}\n",
            encoding="utf-8",
        )
        migrate_cmd.run(_make_args(chunk_size=1))
        assert not (wiki / migrate_cmd.MIGRATION_PROGRESS_FILENAME).exists()

    def test_canonical_page_rename_does_not_invent_source_missing_tombstone(
        self, tmp_path, monkeypatch
    ):
        project = tmp_path / "project"
        project.mkdir()
        source = project / "current.py"
        _write(source, "def current():\n    return 1\n")
        wiki = _make_wiki(project)
        _write(
            wiki / "modules" / "legacy.md",
            "# Legacy\n\n**Path:** `current.py`\n",
        )
        source_hash = hash_file(source)
        mapping = ManifestPageSource(
            scope=MODULE_OBSERVATION_SCOPE,
            source_path="current.py",
        )
        basis = ConceptObservationBasis(
            scope=MODULE_OBSERVATION_SCOPE,
            source_path="current.py",
            extractor_ref="python-ast",
            source_content_hash=source_hash,
            concept_observation_hash=sha256_bytes(b"legacy observation"),
        )
        SyncManifest(
            sources={
                "current.py": {
                    "hash": source_hash,
                    "semantic_hash": sha256_bytes(b"legacy semantics"),
                    "generated_semantics": {},
                    "language": "python",
                    "entities": [],
                    "entity_pages": {},
                    "entity_page_occurrences": [],
                    "module_page": "legacy",
                }
            },
            page_source_mappings={"modules/legacy.md": mapping},
            evidence_baselines={
                "modules/legacy.md": ManifestEvidenceBaseline.from_basis(basis)
            },
        ).save(wiki)
        monkeypatch.chdir(project)

        migrate_cmd.run(_make_args())

        migrated = SyncManifest.load(wiki)
        assert "modules/legacy.md" not in migrated.page_source_mappings
        assert "modules/legacy.md" not in migrated.tombstones
        assert migrated.page_source_mappings["modules/current.md"] == mapping
        assert migrated.evidence_baselines["modules/current.md"].is_known

    def test_chunk_plan_splits_pending_page_operations(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        plan = migrate_cmd.MigrationPlan(
            archive_name="migrate-test",
            targets=[
                TargetPage("modules", "a", "modules/a.md", "# a\n", "a.py"),
                TargetPage("modules", "b", "modules/b.md", "# b\n", "b.py"),
                TargetPage("modules", "c", "modules/c.md", "# c\n", "c.py"),
            ],
            index_content="# Index\n",
            manifest=None,
        )

        chunks = _build_chunks(wiki, plan, 2)

        assert [chunk.page_operations for chunk in chunks] == [2, 1]
        assert chunks[-1].include_finalizers

    def test_metadata_normalizes_absolute_paths(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        src_file = proj / "web" / "src" / "api" / "client.ts"
        src_file.parent.mkdir(parents=True)
        src_file.write_text("export interface Project {}\n", encoding="utf-8")
        wiki = _make_wiki(proj)
        page = wiki / "modules" / "old_client.md"
        _write(page, f"# old client\n\n**Path:** `{src_file}`\n")

        parsed = _read_existing_page(page, wiki, str(proj))

        assert parsed.source_path == "web/src/api/client.ts"

    def test_metadata_accepts_location_without_line(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "pkg" / "session_client.py", "class SessionClient:\n    pass\n")
        wiki = _make_wiki(proj)
        page = wiki / "entities" / "SessionClient.md"
        _write(page, "# SessionClient\n\n**Location:** `pkg/session_client.py`\n")

        parsed = _read_existing_page(page, wiki, str(proj))

        assert parsed.location_path == "pkg/session_client.py"
        assert parsed.location_line is None

    def test_location_split_preserves_windows_drive_letters(self):
        assert _split_location(r"C:\repo\pkg\client.py") == (
            r"C:\repo\pkg\client.py",
            None,
        )
        assert _split_location(r"C:\repo\pkg\client.py:42") == (
            r"C:\repo\pkg\client.py",
            42,
        )

    def test_ambiguous_stem_match_returns_none(self):
        targets = [
            TargetPage(
                "modules",
                "pkg_a_server",
                "modules/pkg_a_server.md",
                "",
                "pkg_a/server.py",
            ),
            TargetPage(
                "modules",
                "pkg_b_server",
                "modules/pkg_b_server.md",
                "",
                "pkg_b/server.py",
            ),
        ]
        page = ExistingPage(
            kind="modules",
            path=Path("server.md"),
            rel="modules/server.md",
            stem="server",
            content="# server\n",
        )

        assert _match_existing_page(page, _build_match_lookups(targets)) is None

    def test_link_rewrite_uses_relative_path_from_page(self, tmp_path):
        wiki = tmp_path / "wiki"
        page = wiki / "workflows" / "flow.md"
        page.parent.mkdir(parents=True)
        content = "- [old server](../modules/server.md)\n"

        updated = _rewrite_links_in_content(
            content,
            page,
            wiki,
            {"modules/server.md": "modules/pkg_a_server.md"},
        )

        assert "../modules/pkg_a_server.md" in updated
        assert "../modules/server.md" not in updated


class TestMigrateIntegration:
    def test_collision_aware_pages_archive_old_pages_and_lint_passes(
        self, tmp_path, capsys
    ):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "api" / "server.py", "class Server:\n    pass\n")
        _write(proj / "worker" / "server.py", "class WorkerServer:\n    pass\n")
        _write(
            proj / "sidecars" / "workspace_server.py",
            "class WorkspaceServer:\n    pass\n",
        )
        _write(
            proj / "other" / "workspace_server.py",
            "class OtherWorkspaceServer:\n    pass\n",
        )
        wiki = _make_wiki(proj)
        _write(
            wiki / "modules" / "server.md",
            "# server\n\n**Path:** `api/server.py`\n\nManual server notes.\n",
        )
        _write(
            wiki / "modules" / "workspace_server.md",
            "# workspace_server\n\n**Path:** `sidecars/workspace_server.py`\n\nManual workspace notes.\n",
        )
        _write(wiki / "modules" / "orphan.md", "# orphan\n\nUnmatched notes.\n")
        _write(
            wiki / "workflows" / "flow.md",
            "# flow\n\n- [server](../modules/server.md)\n",
        )

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        assert not (wiki / "modules" / "workspace_server.md").exists()
        assert (wiki / "modules" / "api_server.md").exists()
        assert (wiki / "modules" / "sidecars_workspace_server.md").exists()
        assert "Manual workspace notes" in (
            wiki / "modules" / "sidecars_workspace_server.md"
        ).read_text(encoding="utf-8")
        assert "../modules/api_server.md" in (wiki / "workflows" / "flow.md").read_text(
            encoding="utf-8"
        )
        assert _has_legacy_archive(wiki, "modules", "server.md")
        assert _has_legacy_archive(wiki, "modules", "workspace_server.md")
        assert _has_legacy_archive(wiki, "modules", "orphan.md")
        assert (wiki / MANIFEST_FILENAME).exists()

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    def test_workflow_raw_stem_links_rewrite_per_workflow_from_call_graph(
        self, tmp_path, capsys
    ):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "models" / "task.py", "class Task:\n    pass\n")
        _write(proj / "models" / "iteration.py", "class Iteration:\n    pass\n")
        _write(proj / "schemas" / "task.py", "class TaskCreate:\n    pass\n")
        _write(proj / "schemas" / "iteration.py", "class IterationSummary:\n    pass\n")
        _write(proj / "schemas" / "common.py", "class MessageResponse:\n    pass\n")
        _write(proj / "schemas" / "gantt.py", "class SchedulingDecision:\n    pass\n")
        _write(proj / "types" / "gantt.py", "class GanttTask:\n    pass\n")
        _write(proj / "services" / "task_service.py", "class TaskService:\n    pass\n")
        _write(
            proj / "routers" / "tasks.py",
            """
            from schemas.task import TaskCreate as CreateSchema
            from schemas.common import MessageResponse
            from services.task_service import TaskService

            def create_task(data: CreateSchema, service: TaskService) -> MessageResponse:
                return MessageResponse()
            """,
        )
        _write(
            proj / "services" / "scheduler_service.py",
            """
            from models.task import Task
            from models.iteration import Iteration
            from schemas.gantt import SchedulingDecision

            def _schedule_leaf_task(task: Task, iteration: Iteration) -> SchedulingDecision:
                return SchedulingDecision()
            """,
        )
        wiki = _make_wiki(proj)
        _write(
            wiki / "workflows" / "create_task.md",
            """
            # create_task

            **Modules involved:** [task](../modules/task.md)

            ## Touches

            - [task](../modules/task.md)
            """,
        )
        _write(
            wiki / "workflows" / "schedule_leaf_task.md",
            """
            # schedule_leaf_task

            ## Touches

            - [task](../modules/task.md)
            - [iteration](../modules/iteration.md)
            - [gantt](../modules/gantt.md)
            """,
        )

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        create_task = (wiki / "workflows" / "create_task.md").read_text(
            encoding="utf-8"
        )
        schedule_leaf = (wiki / "workflows" / "schedule_leaf_task.md").read_text(
            encoding="utf-8"
        )
        assert "../modules/schemas_task.md" in create_task
        assert "../modules/models_task.md" not in create_task
        assert "../modules/models_task.md" in schedule_leaf
        assert "../modules/models_iteration.md" in schedule_leaf
        assert "../modules/schemas_gantt.md" in schedule_leaf
        assert "../modules/task.md" not in create_task
        assert "../modules/task.md" not in schedule_leaf

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    def test_infrastructure_page_regenerated_and_legacy_content_preserved(
        self, tmp_path, capsys
    ):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(
            proj / "app" / "workspace_server.py", "class WorkspaceServer:\n    pass\n"
        )
        _write(
            proj / "other" / "workspace_server.py",
            "class OtherWorkspaceServer:\n    pass\n",
        )
        _write(
            proj / "docker" / "Dockerfile.workspace",
            "FROM alpine\nCOPY app/workspace_server.py /app/\n",
        )
        wiki = _make_wiki(proj)
        _write(
            wiki / "modules" / "workspace_server.md",
            "# workspace\n\n**Path:** `app/workspace_server.py`\n",
        )
        _write(
            wiki / "infrastructure" / "docker_Dockerfile_workspace.md",
            """
            # docker/Dockerfile.workspace

            **Path:** `docker/Dockerfile.workspace`

            | `COPY` | [`app/workspace_server.py`](../modules/workspace_server.md) | `/app/` | — |
            """,
        )

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        infra = (wiki / "infrastructure" / "docker_Dockerfile_workspace.md").read_text(
            encoding="utf-8"
        )
        assert "../modules/app_workspace_server.md" in infra
        assert "../modules/workspace_server.md" not in infra
        assert "Legacy Notes" in infra
        assert _has_legacy_archive(
            wiki, "infrastructure", "docker_Dockerfile_workspace.md"
        )

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    def test_second_migrate_does_not_create_new_archive_batch(self, tmp_path, capsys):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "api" / "server.py", "class Server:\n    pass\n")
        _write(proj / "worker" / "server.py", "class WorkerServer:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(
            wiki / "modules" / "server.md",
            "# server\n\n**Path:** `api/server.py`\n\nManual server notes.\n",
        )
        _write(
            wiki / "workflows" / "flow.md",
            "# flow\n\n- [server](../modules/server.md)\n",
        )

        os.chdir(proj)
        migrate_cmd.run(_make_args())
        first_archives = _legacy_archive_names(wiki)
        first_content = (wiki / "modules" / "api_server.md").read_text(encoding="utf-8")

        migrate_cmd.run(_make_args())
        second_archives = _legacy_archive_names(wiki)
        second_content = (wiki / "modules" / "api_server.md").read_text(
            encoding="utf-8"
        )

        assert first_archives
        assert second_archives == first_archives
        assert second_content == first_content
        assert second_content.count("### From `modules/server.md`") == 1

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    def test_migrate_adds_legacy_archive_to_gitignore_once(self, tmp_path, capsys):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "models.py", "class User:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(proj / ".gitignore", "# user rules\n*.pyc\n")
        _write(
            wiki / "modules" / "models.md",
            "# models\n\n**Path:** `models.py`\n\nManual.\n",
        )

        os.chdir(proj)
        migrate_cmd.run(_make_args())
        migrate_cmd.run(_make_args())

        content = (proj / ".gitignore").read_text(encoding="utf-8")
        assert "# user rules" in content
        assert "*.pyc" in content
        assert content.count("docs/llm_wiki/legacy/") == 1
        assert _has_legacy_archive(wiki, "modules", "models.md")

        output = capsys.readouterr().out
        assert "GITIGNORE add docs/llm_wiki/legacy/" in output

    def test_path_only_location_maps_ambiguous_entity_and_rewrites_legacy_links(
        self, tmp_path, capsys
    ):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "pkg" / "session_client.py", "class SessionClient:\n    pass\n")
        _write(proj / "other" / "target.py", "class SessionClient:\n    pass\n")
        _write(proj / "app_state.py", "class AppState:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(
            wiki / "entities" / "SessionClient.md",
            """
            # SessionClient

            **Location:** `pkg/session_client.py`

            Manual session details.
            """,
        )
        _write(
            wiki / "entities" / "AppState.md",
            """
            # AppState

            **Location:** `app_state.py`

            - **uses**: [`SessionClient`](SessionClient.md)
            """,
        )
        _write(
            wiki / "modules" / "session_client.md",
            """
            # session_client Module

            **Path:** `pkg/session_client.py`

            | [`SessionClient`](../entities/SessionClient.md) | struct |
            """,
        )

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        canonical = wiki / "entities" / "session_client_SessionClient.md"
        assert canonical.exists()
        assert not (wiki / "entities" / "SessionClient.md").exists()
        assert "Manual session details" in canonical.read_text(encoding="utf-8")
        module_content = (wiki / "modules" / "session_client.md").read_text(
            encoding="utf-8"
        )
        app_state_content = (wiki / "entities" / "AppState.md").read_text(
            encoding="utf-8"
        )
        assert "../entities/session_client_SessionClient.md" in module_content
        assert "../entities/SessionClient.md" not in module_content
        assert "(session_client_SessionClient.md)" in app_state_content
        assert "(SessionClient.md)" not in app_state_content

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    def test_unmatched_legacy_page_links_rewrite_to_archive(self, tmp_path, capsys):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "models.py", "class User:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(
            wiki / "modules" / "models.md",
            """
            # models Module

            **Path:** `models.py`

            See [removed](../entities/Removed.md).
            """,
        )
        _write(
            wiki / "entities" / "Removed.md",
            """
            # Removed

            **Location:** `deleted.py`

            Historical notes.
            """,
        )

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        content = (wiki / "modules" / "models.md").read_text(encoding="utf-8")
        assert "../legacy/migrate-" in content
        assert "../entities/Removed.md" not in content
        assert _has_legacy_archive(wiki, "entities", "Removed.md")

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    def test_additional_docs_are_indexed(self, tmp_path, capsys):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "models.py", "class User:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(wiki / "config_docs" / "prometheus_yml.md", "# Prometheus\n")

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        index = (wiki / "index.md").read_text(encoding="utf-8")
        assert "## Additional Docs" in index
        assert "- [config_docs/prometheus_yml](config_docs/prometheus_yml.md)" in index

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    def test_existing_m4_surfaces_are_indexed_as_canonical_sections(self, tmp_path):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "models.py", "class User:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(wiki / "flows" / "api-run.md", "# api-run\n\nExisting flow.\n")
        _write(
            wiki / "api-contracts.md",
            "# API contracts\n\n## Notes\n\nExisting contract note.\n",
        )
        _write(wiki / "dependencies.md", "# Dependencies\n\nExisting graph.\n")
        _write(wiki / "load-order.md", "# Load order\n\nExisting order.\n")

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        index = (wiki / "index.md").read_text(encoding="utf-8")
        assert "## User Flows" in index
        assert "- [api-run](flows/api-run.md)" in index
        assert "## Dependency Architecture" in index
        assert "## API contracts" in index
        assert "[Production HTTP API inventory](api-contracts.md)" in index
        assert "- [Dependencies](dependencies.md)" in index
        assert "- [Load order](load-order.md)" in index
        additional_docs = index.partition("## Additional Docs")[2]
        assert "flows/api-run.md" not in additional_docs
        assert "api-contracts.md" not in additional_docs
        assert "dependencies.md" not in additional_docs
        assert "load-order.md" not in additional_docs
        assert (wiki / "flows" / "api-run.md").read_text(
            encoding="utf-8"
        ) == "# api-run\n\nExisting flow.\n"
        assert (wiki / "api-contracts.md").read_text(
            encoding="utf-8"
        ) == "# API contracts\n\n## Notes\n\nExisting contract note.\n"

    def test_empty_upgraded_flows_directory_does_not_add_user_flows_section(
        self, tmp_path
    ):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "models.py", "class User:\n    pass\n")
        wiki = _make_wiki(proj)
        (wiki / "flows").mkdir(parents=True)
        (wiki / "flows" / ".gitkeep").write_text("", encoding="utf-8")

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        index = (wiki / "index.md").read_text(encoding="utf-8")
        assert "## User Flows" not in index
        assert "flows/.gitkeep" not in index

    def test_rerun_uses_archived_pages_to_repair_legacy_links(self, tmp_path, capsys):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "pkg" / "session_client.py", "class SessionClient:\n    pass\n")
        _write(proj / "other" / "target.py", "class SessionClient:\n    pass\n")
        _write(proj / "app_state.py", "class AppState:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(
            wiki / "modules" / "session_client.md",
            """
            # session_client Module

            **Path:** `pkg/session_client.py`

            ## Legacy Notes

            <!-- llm-wiki-migrate:legacy-notes -->

            ### From `modules/session_client.md`

            | [`SessionClient`](../entities/SessionClient.md) | struct |
            """,
        )
        _write(
            wiki / "entities" / "session_client_SessionClient.md",
            "# SessionClient\n\n**Location:** `pkg/session_client.py:1`\n",
        )
        _write(
            wiki / "entities" / "target_SessionClient.md",
            "# SessionClient\n\n**Location:** `other/target.py:1`\n",
        )
        _write(
            wiki / "entities" / "AppState.md",
            """
            # AppState

            **Location:** `app_state.py:1`

            ## Legacy Notes

            <!-- llm-wiki-migrate:legacy-notes -->

            ### From `entities/AppState.md`

            - **uses**: [`SessionClient`](SessionClient.md)
            """,
        )
        _write(
            wiki
            / "legacy"
            / "migrate-20240101000000"
            / "entities"
            / "SessionClient.md",
            """
            # SessionClient

            **Location:** `pkg/session_client.py`

            Archived session details.
            """,
        )

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        canonical = (wiki / "entities" / "session_client_SessionClient.md").read_text(
            encoding="utf-8"
        )
        module_content = (wiki / "modules" / "session_client.md").read_text(
            encoding="utf-8"
        )
        app_state_content = (wiki / "entities" / "AppState.md").read_text(
            encoding="utf-8"
        )
        assert "Archived session details" in canonical
        assert "../entities/session_client_SessionClient.md" in module_content
        assert "../entities/SessionClient.md" not in module_content
        assert "(session_client_SessionClient.md)" in app_state_content
        assert "(SessionClient.md)" not in app_state_content

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    @skip_no_ts
    def test_typescript_absolute_page_names_migrate_to_relative_names(
        self, tmp_path, capsys
    ):
        proj = tmp_path / "proj"
        proj.mkdir()
        src_file = proj / "web" / "src" / "api" / "client.ts"
        _write(src_file, "export interface Project { id: string }\n")
        wiki = _make_wiki(proj)
        old_module = "proj_web_src_api_client"
        old_entity = "proj_web_src_api_client_Project"
        _write(
            wiki / "modules" / f"{old_module}.md",
            f"# client\n\n**Path:** `{src_file}`\n",
        )
        _write(
            wiki / "entities" / f"{old_entity}.md",
            f"# Project\n\n**Location:** `{src_file}:1`\n",
        )

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        assert (wiki / "modules" / "client.md").exists()
        assert (wiki / "entities" / "Project.md").exists()
        assert not (wiki / "modules" / f"{old_module}.md").exists()
        assert _has_legacy_archive(wiki, "modules", f"{old_module}.md")

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    def test_cli_dry_run_does_not_modify_wiki(self, tmp_path, monkeypatch, capsys):
        from llm_wiki_cli import cli

        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "models.py", "class User:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(
            wiki / "modules" / "models.md",
            "# models\n\n**Path:** `models.py`\n\nManual.\n",
        )
        before = {
            path.relative_to(wiki).as_posix(): path.read_text(encoding="utf-8")
            for path in wiki.rglob("*")
            if path.is_file()
        }

        os.chdir(proj)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "llm-wiki",
                "migrate",
                "--src-dir",
                ".",
                "--wiki-dir",
                "docs/llm_wiki",
                "--dry-run",
            ],
        )
        cli.main()

        after = {
            path.relative_to(wiki).as_posix(): path.read_text(encoding="utf-8")
            for path in wiki.rglob("*")
            if path.is_file()
        }
        output = capsys.readouterr().out
        assert "DRY-RUN" in output
        assert "DRY-RUN: surface index created" in output
        assert "DRY-RUN: knowledge index created" in output
        assert "DRY-RUN: manifest created" in output
        assert after == before
        assert not (wiki / "legacy").exists()
        assert not Path(".gitignore").exists()

    def test_dry_run_reports_exact_unchanged_artifact_actions(
        self,
        tmp_path,
        capsys,
    ):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "models.py", "class User:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(
            wiki / "modules" / "models.md",
            "# models\n\n**Path:** `models.py`\n",
        )
        os.chdir(proj)
        migrate_cmd.run(_make_args())
        capsys.readouterr()
        migrate_cmd.run(_make_args())
        capsys.readouterr()
        before = {
            filename: (wiki / filename).read_bytes()
            for filename in (
                SURFACE_INDEX_FILENAME,
                KNOWLEDGE_INDEX_FILENAME,
                MANIFEST_FILENAME,
            )
        }

        migrate_cmd.run(_make_args(dry_run=True))

        output = capsys.readouterr().out
        assert "DRY-RUN: surface index unchanged" in output
        assert "DRY-RUN: knowledge index unchanged" in output
        assert "DRY-RUN: manifest unchanged" in output
        assert {
            filename: (wiki / filename).read_bytes() for filename in before
        } == before

    def test_clean_git_sibling_wiki_dry_run_matches_apply_artifact_bytes(
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        proj = tmp_path / "proj"
        source = proj / "src"
        source.mkdir(parents=True)
        _write(source / "models.py", "class User:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(
            wiki / "modules" / "models.md",
            "# models\n\n**Path:** `models.py`\n\nManual.\n",
        )
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.email", "test@example.com"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.name", "Test"],
            check=True,
        )
        subprocess.run(["git", "-C", str(proj), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(proj), "commit", "-m", "initial"],
            capture_output=True,
            check=True,
        )
        monkeypatch.chdir(proj)

        captured = []
        real_build = migrate_cmd.build_runtime_knowledge_plan
        real_finalize = migrate_cmd.finalize_runtime_knowledge

        def capture_build(inputs):
            plan = real_build(inputs)
            captured.append(
                (
                    "preview",
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
            return plan

        def capture_finalize(inputs, *, dry_run=False, fault_injector=None):
            plan = build_runtime_knowledge_plan(inputs)
            captured.append(
                (
                    "apply",
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

        monkeypatch.setattr(
            migrate_cmd,
            "build_runtime_knowledge_plan",
            capture_build,
        )
        monkeypatch.setattr(
            migrate_cmd,
            "finalize_runtime_knowledge",
            capture_finalize,
        )

        migrate_cmd.run(
            _make_args(
                src_dir="src",
                wiki_dir="docs/llm_wiki",
                dry_run=True,
            )
        )
        assert len(captured) == 1
        assert captured[0][0] == "preview"
        assert captured[0][1] is WorkingTreeState.CLEAN
        capsys.readouterr()

        migrate_cmd.run(
            _make_args(
                src_dir="src",
                wiki_dir="docs/llm_wiki",
            )
        )

        assert len(captured) == 2
        assert captured[1][0] == "apply"
        assert captured[1][1] is WorkingTreeState.CLEAN
        assert captured[1][2] == captured[0][2]
        assert load_knowledge_state(wiki).status is KnowledgeLoadState.VALID

    def test_cli_plan_chunks_does_not_modify_wiki(self, tmp_path, monkeypatch, capsys):
        from llm_wiki_cli import cli

        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "models.py", "class User:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(
            wiki / "modules" / "models.md",
            "# models\n\n**Path:** `models.py`\n\nManual.\n",
        )
        before = {
            path.relative_to(wiki).as_posix(): path.read_text(encoding="utf-8")
            for path in wiki.rglob("*")
            if path.is_file()
        }

        os.chdir(proj)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "llm-wiki",
                "migrate",
                "--src-dir",
                ".",
                "--wiki-dir",
                "docs/llm_wiki",
                "--chunk-size",
                "1",
                "--plan-chunks",
            ],
        )
        cli.main()

        after = {
            path.relative_to(wiki).as_posix(): path.read_text(encoding="utf-8")
            for path in wiki.rglob("*")
            if path.is_file()
        }
        output = capsys.readouterr().out
        assert "Migration chunk plan" in output
        assert "DRY-RUN: surface index created" in output
        assert "DRY-RUN: knowledge index created" in output
        assert "DRY-RUN: manifest created" in output
        assert "PLAN: no files modified" in output
        assert after == before
        assert not (wiki / "legacy").exists()
        assert not Path(".gitignore").exists()

    def test_chunked_migrate_applies_next_pending_chunk_until_finalizers(
        self, tmp_path, capsys
    ):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "alpha.py", "def alpha():\n    pass\n")
        _write(proj / "beta.py", "def beta():\n    pass\n")
        wiki = _make_wiki(proj)
        _write(
            wiki / "modules" / "alpha.md",
            "# alpha\n\n**Path:** `alpha.py`\n\nManual alpha.\n",
        )
        _write(
            wiki / "modules" / "beta.md",
            "# beta\n\n**Path:** `beta.py`\n\nManual beta.\n",
        )

        os.chdir(proj)
        migrate_cmd.run(_make_args(chunk_size=1))

        assert not (wiki / MANIFEST_FILENAME).exists()
        assert (wiki / "index.md").read_text(encoding="utf-8") == "# Old Index\n"
        assert "docs/llm_wiki/legacy/" in Path(".gitignore").read_text(encoding="utf-8")
        first_output = capsys.readouterr().out
        assert "DEFER index/manifest refresh" in first_output

        migrate_cmd.run(_make_args(chunk_size=1))

        assert (wiki / MANIFEST_FILENAME).exists()
        assert (wiki / "index.md").read_text(encoding="utf-8") != "# Old Index\n"
        second_output = capsys.readouterr().out
        assert "final index/link/manifest refresh" in second_output
