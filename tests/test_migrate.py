"""Tests for llm-wiki migrate."""

from __future__ import annotations

import os
import shutil
import sys
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import lint_cmd, migrate_cmd
from llm_wiki_cli.commands.migrate_cmd import (
    ExistingPage,
    TargetPage,
    _build_match_lookups,
    _match_existing_page,
    _read_existing_page,
    _rewrite_links_in_content,
    _split_location,
)
from llm_wiki_cli.commands.sync_cmd import MANIFEST_FILENAME


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
    return any((archive / Path(*parts)).exists() for archive in legacy_root.glob("migrate-*"))


def _legacy_archive_names(wiki: Path) -> list[str]:
    legacy_root = wiki / "legacy"
    if not legacy_root.exists():
        return []
    return sorted(path.name for path in legacy_root.glob("migrate-*") if path.is_dir())


class TestMigrateHelpers:
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
        assert _split_location(r"C:\repo\pkg\client.py") == (r"C:\repo\pkg\client.py", None)
        assert _split_location(r"C:\repo\pkg\client.py:42") == (r"C:\repo\pkg\client.py", 42)

    def test_ambiguous_stem_match_returns_none(self):
        targets = [
            TargetPage("modules", "pkg_a_server", "modules/pkg_a_server.md", "", "pkg_a/server.py"),
            TargetPage("modules", "pkg_b_server", "modules/pkg_b_server.md", "", "pkg_b/server.py"),
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
    def test_collision_aware_pages_archive_old_pages_and_lint_passes(self, tmp_path, capsys):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "api" / "server.py", "class Server:\n    pass\n")
        _write(proj / "worker" / "server.py", "class WorkerServer:\n    pass\n")
        _write(proj / "sidecars" / "workspace_server.py", "class WorkspaceServer:\n    pass\n")
        _write(proj / "other" / "workspace_server.py", "class OtherWorkspaceServer:\n    pass\n")
        wiki = _make_wiki(proj)
        _write(wiki / "modules" / "server.md", "# server\n\n**Path:** `api/server.py`\n\nManual server notes.\n")
        _write(
            wiki / "modules" / "workspace_server.md",
            "# workspace_server\n\n**Path:** `sidecars/workspace_server.py`\n\nManual workspace notes.\n",
        )
        _write(wiki / "modules" / "orphan.md", "# orphan\n\nUnmatched notes.\n")
        _write(wiki / "workflows" / "flow.md", "# flow\n\n- [server](../modules/server.md)\n")

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        assert not (wiki / "modules" / "workspace_server.md").exists()
        assert (wiki / "modules" / "api_server.md").exists()
        assert (wiki / "modules" / "sidecars_workspace_server.md").exists()
        assert "Manual workspace notes" in (wiki / "modules" / "sidecars_workspace_server.md").read_text(encoding="utf-8")
        assert "../modules/api_server.md" in (wiki / "workflows" / "flow.md").read_text(encoding="utf-8")
        assert _has_legacy_archive(wiki, "modules", "server.md")
        assert _has_legacy_archive(wiki, "modules", "workspace_server.md")
        assert _has_legacy_archive(wiki, "modules", "orphan.md")
        assert (wiki / MANIFEST_FILENAME).exists()

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    def test_infrastructure_page_regenerated_and_legacy_content_preserved(self, tmp_path, capsys):
        proj = tmp_path / "proj"
        proj.mkdir()
        _write(proj / "app" / "workspace_server.py", "class WorkspaceServer:\n    pass\n")
        _write(proj / "other" / "workspace_server.py", "class OtherWorkspaceServer:\n    pass\n")
        _write(proj / "docker" / "Dockerfile.workspace", "FROM alpine\nCOPY app/workspace_server.py /app/\n")
        wiki = _make_wiki(proj)
        _write(wiki / "modules" / "workspace_server.md", "# workspace\n\n**Path:** `app/workspace_server.py`\n")
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

        infra = (wiki / "infrastructure" / "docker_Dockerfile_workspace.md").read_text(encoding="utf-8")
        assert "../modules/app_workspace_server.md" in infra
        assert "../modules/workspace_server.md" not in infra
        assert "Legacy Notes" in infra
        assert _has_legacy_archive(wiki, "infrastructure", "docker_Dockerfile_workspace.md")

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
        second_content = (wiki / "modules" / "api_server.md").read_text(encoding="utf-8")

        assert first_archives
        assert second_archives == first_archives
        assert second_content == first_content
        assert second_content.count("### From `modules/server.md`") == 1

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    def test_path_only_location_maps_ambiguous_entity_and_rewrites_legacy_links(self, tmp_path, capsys):
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
        module_content = (wiki / "modules" / "session_client.md").read_text(encoding="utf-8")
        app_state_content = (wiki / "entities" / "AppState.md").read_text(encoding="utf-8")
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
            wiki / "legacy" / "migrate-20240101000000" / "entities" / "SessionClient.md",
            """
            # SessionClient

            **Location:** `pkg/session_client.py`

            Archived session details.
            """,
        )

        os.chdir(proj)
        migrate_cmd.run(_make_args())

        canonical = (wiki / "entities" / "session_client_SessionClient.md").read_text(encoding="utf-8")
        module_content = (wiki / "modules" / "session_client.md").read_text(encoding="utf-8")
        app_state_content = (wiki / "entities" / "AppState.md").read_text(encoding="utf-8")
        assert "Archived session details" in canonical
        assert "../entities/session_client_SessionClient.md" in module_content
        assert "../entities/SessionClient.md" not in module_content
        assert "(session_client_SessionClient.md)" in app_state_content
        assert "(SessionClient.md)" not in app_state_content

        lint_cmd.run(_make_args())
        output = capsys.readouterr().out
        assert "Lint passed" in output

    @skip_no_ts
    def test_typescript_absolute_page_names_migrate_to_relative_names(self, tmp_path, capsys):
        proj = tmp_path / "proj"
        proj.mkdir()
        src_file = proj / "web" / "src" / "api" / "client.ts"
        _write(src_file, "export interface Project { id: string }\n")
        wiki = _make_wiki(proj)
        old_module = "proj_web_src_api_client"
        old_entity = "proj_web_src_api_client_Project"
        _write(wiki / "modules" / f"{old_module}.md", f"# client\n\n**Path:** `{src_file}`\n")
        _write(wiki / "entities" / f"{old_entity}.md", f"# Project\n\n**Location:** `{src_file}:1`\n")

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
        _write(wiki / "modules" / "models.md", "# models\n\n**Path:** `models.py`\n\nManual.\n")
        before = {
            path.relative_to(wiki).as_posix(): path.read_text(encoding="utf-8")
            for path in wiki.rglob("*")
            if path.is_file()
        }

        os.chdir(proj)
        monkeypatch.setattr(
            sys,
            "argv",
            ["llm-wiki", "migrate", "--src-dir", ".", "--wiki-dir", "docs/llm_wiki", "--dry-run"],
        )
        cli.main()

        after = {
            path.relative_to(wiki).as_posix(): path.read_text(encoding="utf-8")
            for path in wiki.rglob("*")
            if path.is_file()
        }
        output = capsys.readouterr().out
        assert "DRY-RUN" in output
        assert after == before
        assert not (wiki / "legacy").exists()
