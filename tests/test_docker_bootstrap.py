"""Tests for Docker infrastructure page generation in bootstrap_cmd."""

from __future__ import annotations

import ast
import inspect
import os
import textwrap


from llm_wiki_cli.commands.bootstrap_cmd import (
    _generate_docker_md,
    _generate_dockerfile_md,
)
from llm_wiki_cli.commands.extract_cmd import _parse_dockerfile, _parse_compose


class TestGenerateDockerfileMd:
    def test_dockerfile_renderer_stays_decomposed(self):
        source = textwrap.dedent(inspect.getsource(_generate_dockerfile_md))
        function_node = ast.parse(source).body[0]
        body = list(function_node.body)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body = body[1:]

        first_body_line = min(stmt.lineno for stmt in body)
        last_body_line = max(stmt.end_lineno for stmt in body)
        body_lines = last_body_line - first_body_line + 1

        assert body_lines <= 25

    def test_single_stage(self):
        info = _parse_dockerfile(
            "FROM python:3.12-slim\nEXPOSE 8000\nCMD python main.py\n"
        )
        md = _generate_docker_md("Dockerfile", info)
        assert "# Dockerfile" in md
        assert "`python:3.12-slim`" in md
        assert "`8000`" in md
        assert "python main.py" in md

    def test_multi_stage_has_table(self):
        text = "FROM python:3.12 AS builder\nFROM python:3.12-slim AS runtime\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info)
        assert "## Build Stages" in md
        assert "`builder`" in md
        assert "`runtime`" in md

    def test_env_vars_section(self):
        text = "FROM alpine\nENV APP_ENV=production\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info)
        assert "## Environment Variables" in md
        assert "`APP_ENV`" in md
        assert "`production`" in md

    def test_volumes_section(self):
        text = 'FROM alpine\nVOLUME ["/data"]\n'
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info)
        assert "## Volumes" in md
        assert "`/data`" in md

    def test_build_args_section(self):
        text = "FROM alpine\nARG VERSION=1.0\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info)
        assert "## Build Arguments" in md
        assert "`VERSION`" in md

    def test_copy_cross_reference(self):
        text = "FROM alpine\nCOPY main.py /app/\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info, module_stems={"main"})
        assert "[`main.py`](../modules/main.md)" in md

    def test_copy_cross_reference_uses_module_page_map(self):
        """COPY links must use collision-aware module page names, not file stems."""
        text = "FROM alpine\nCOPY sidecars/workspace_server.py /app/\n"
        info = _parse_dockerfile(text)
        module_links = {
            "sidecars/workspace_server.py": "sidecars_workspace_server",
            "sidecars/typescript/src/server.ts": "sidecars_typescript_src_server",
        }

        md = _generate_docker_md(
            "docker/Dockerfile.workspace", info, module_links=module_links
        )

        assert (
            "[`sidecars/workspace_server.py`](../modules/sidecars_workspace_server.md)"
            in md
        )
        assert "../modules/server.md" not in md

    def test_copy_cross_reference_prefers_nested_docker_context(self):
        """A Dockerfile under a nested docker/ dir should link within that worktree."""
        text = "FROM alpine\nCOPY sidecars/workspace_server.py /app/\n"
        info = _parse_dockerfile(text)
        module_links = {
            "sidecars/workspace_server.py": "sidecars_workspace_server",
            ".claude/worktrees/agent-strict-instructions/sidecars/workspace_server.py": "agent-strict-instructions_sidecars_workspace_server",
        }

        md = _generate_docker_md(
            ".claude/worktrees/agent-strict-instructions/docker/Dockerfile.workspace",
            info,
            module_links=module_links,
        )

        assert (
            "[`sidecars/workspace_server.py`]"
            "(../modules/agent-strict-instructions_sidecars_workspace_server.md)"
        ) in md

    def test_copy_cross_reference_leaves_ambiguous_suffix_unlinked(self):
        """Suffix-only matches should not create a link when multiple pages match."""
        text = "FROM alpine\nCOPY workspace_server.py /app/\n"
        info = _parse_dockerfile(text)
        module_links = {
            "sidecars/workspace_server.py": "sidecars_workspace_server",
            "other/workspace_server.py": "other_workspace_server",
        }

        md = _generate_docker_md("Dockerfile", info, module_links=module_links)

        assert "`workspace_server.py`" in md
        assert "../modules/" not in md

    def test_copy_no_cross_reference(self):
        text = "FROM alpine\nCOPY config.txt /app/\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info, module_stems={"main"})
        assert "`config.txt`" in md
        assert "../modules/" not in md

    def test_healthcheck_section(self):
        text = "FROM alpine\nHEALTHCHECK CMD curl -f http://localhost/\n"
        info = _parse_dockerfile(text)
        md = _generate_docker_md("Dockerfile", info)
        assert "Healthcheck" in md


class TestGenerateComposeMd:
    def test_basic_services(self):
        text = textwrap.dedent("""\
            services:
              web:
                build: .
                ports:
                  - "8000:8000"
              db:
                image: postgres:16
        """)
        info = _parse_compose(text)
        md = _generate_docker_md("docker-compose.yml", info)
        assert "# docker-compose.yml" in md
        assert "## Services" in md
        assert "`web`" in md
        assert "`db`" in md

    def test_per_service_detail(self):
        text = textwrap.dedent("""\
            services:
              app:
                image: myapp:latest
                command: python run.py
        """)
        info = _parse_compose(text)
        md = _generate_docker_md("docker-compose.yml", info)
        assert "### app" in md
        assert "`myapp:latest`" in md
        assert "python run.py" in md

    def test_networks_and_volumes(self):
        text = textwrap.dedent("""\
            services:
              web:
                image: nginx
            networks:
              frontend:
            volumes:
              pgdata:
        """)
        info = _parse_compose(text)
        md = _generate_docker_md("docker-compose.yml", info)
        assert "## Networks" in md
        assert "`frontend`" in md
        assert "## Named Volumes" in md
        assert "`pgdata`" in md


class TestBootstrapInfrastructureIntegration:
    """Integration test: bootstrap generates infrastructure pages from Docker files."""

    def test_bootstrap_creates_infra_pages(self, tmp_path):
        """Run bootstrap on a project with Docker files and verify pages."""
        proj = tmp_path / "proj"
        proj.mkdir()

        # Create a Python file so bootstrap has something
        (proj / "app.py").write_text("class App:\n    pass\n")

        # Create Docker files
        (proj / "Dockerfile").write_text("FROM python:3.12\nEXPOSE 8000\n")
        (proj / "docker-compose.yml").write_text(
            'services:\n  web:\n    build: .\n    ports:\n      - "8000:8000"\n'
        )

        # Set up wiki dir inside the project (validate_path needs it inside cwd)
        wiki = proj / "docs" / "llm_wiki"
        for subdir in ["entities", "modules", "workflows", "infrastructure"]:
            (wiki / subdir).mkdir(parents=True)
        (wiki / "log.md").write_text("# Log\n")

        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            from llm_wiki_cli.commands import bootstrap_cmd
            import argparse

            args = argparse.Namespace(
                src_dir=".",
                wiki_dir=str(wiki),
                overwrite=True,
                depth="full",
                skip_workflows=True,
            )
            bootstrap_cmd.run(args)

            # Check infrastructure pages created
            infra_dir = wiki / "infrastructure"
            infra_pages = list(infra_dir.glob("*.md"))
            page_names = {p.stem for p in infra_pages}
            assert "Dockerfile" in page_names
            assert "docker-compose_yml" in page_names

            # Check index.md has Infrastructure section
            index_content = (wiki / "index.md").read_text(encoding="utf-8")
            assert "## Infrastructure" in index_content
            assert "Dockerfile" in index_content
            assert "docker-compose_yml" in index_content
        finally:
            os.chdir(old_cwd)

    def test_bootstrap_lint_passes_with_collision_aware_copy_links(
        self, tmp_path, capsys
    ):
        """A freshly bootstrapped wiki must not emit broken Docker COPY links."""
        proj = tmp_path / "proj"
        proj.mkdir()

        (proj / "sidecars").mkdir()
        (proj / "other").mkdir()
        (proj / "docker").mkdir()
        (proj / "sidecars" / "workspace_server.py").write_text(
            "class WorkspaceServer:\n    pass\n"
        )
        (proj / "sidecars" / "server.py").write_text("class Server:\n    pass\n")
        (proj / "other" / "workspace_server.py").write_text(
            "class OtherWorkspaceServer:\n    pass\n"
        )
        (proj / "docker" / "Dockerfile.workspace").write_text(
            "FROM alpine\nCOPY sidecars/workspace_server.py /app/workspace_server.py\n"
        )

        wiki = proj / "docs" / "llm_wiki"

        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            from llm_wiki_cli.commands import bootstrap_cmd, lint_cmd
            import argparse

            args = argparse.Namespace(
                src_dir=".",
                wiki_dir=str(wiki),
                overwrite=True,
                depth="shallow",
                skip_workflows=True,
            )
            bootstrap_cmd.run(args)

            infra = (
                wiki / "infrastructure" / "docker_Dockerfile_workspace.md"
            ).read_text(encoding="utf-8")
            assert "../modules/sidecars_workspace_server.md" in infra
            assert "../modules/server.md" not in infra

            lint_cmd.run(argparse.Namespace(wiki_dir=str(wiki), src_dir="."))
            output = capsys.readouterr().out
            assert "Lint passed" in output
        finally:
            os.chdir(old_cwd)
