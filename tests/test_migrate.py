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
        assert list((wiki / "legacy").glob("migrate-*/modules/server.md"))
        assert list((wiki / "legacy").glob("migrate-*/modules/workspace_server.md"))
        assert list((wiki / "legacy").glob("migrate-*/modules/orphan.md"))
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
        assert list((wiki / "legacy").glob("migrate-*/infrastructure/docker_Dockerfile_workspace.md"))

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
        assert list((wiki / "legacy").glob(f"migrate-*/modules/{old_module}.md"))

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
