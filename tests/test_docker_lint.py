"""Tests for Docker infrastructure lint checks in lint_cmd."""
from __future__ import annotations

import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from llm_wiki_cli.commands.lint_cmd import (
    _collect_docker_files,
    _collect_documented_infrastructure,
)


class TestCollectDockerFiles:
    def test_finds_dockerfile(self, tmp_path):
        (tmp_path / "Dockerfile").write_text("FROM alpine\n")
        result = _collect_docker_files(str(tmp_path))
        assert "Dockerfile" in result

    def test_finds_compose(self, tmp_path):
        (tmp_path / "docker-compose.yml").write_text("services:\n  web:\n    image: nginx\n")
        result = _collect_docker_files(str(tmp_path))
        assert "docker-compose_yml" in result

    def test_empty_dir(self, tmp_path):
        result = _collect_docker_files(str(tmp_path))
        assert result == set()


class TestCollectDocumentedInfrastructure:
    def test_finds_pages(self, tmp_path):
        infra = tmp_path / "infrastructure"
        infra.mkdir()
        (infra / "Dockerfile.md").write_text("# Dockerfile\n")
        (infra / "docker-compose_yml.md").write_text("# compose\n")
        result = _collect_documented_infrastructure(tmp_path)
        assert result == {"Dockerfile", "docker-compose_yml"}

    def test_empty_dir(self, tmp_path):
        result = _collect_documented_infrastructure(tmp_path)
        assert result == set()

    def test_no_infra_dir(self, tmp_path):
        result = _collect_documented_infrastructure(tmp_path)
        assert result == set()


class TestLintInfrastructureIntegration:
    """Integration: lint detects undocumented Docker files and stale infra pages."""

    def test_undocumented_docker_file(self, tmp_path, capsys):
        """Dockerfile in source but no wiki page → lint warns."""
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "Dockerfile").write_text("FROM alpine\n")
        (proj / "dummy.py").write_text("")  # needed so src_dir is valid

        wiki = proj / "docs" / "llm_wiki"
        for d in ["entities", "modules", "workflows", "infrastructure"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "index.md").write_text("# Index\n")
        (wiki / "log.md").write_text("# Log\n")

        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            import argparse
            from llm_wiki_cli.commands import lint_cmd
            args = argparse.Namespace(wiki_dir=str(wiki), src_dir=".")
            with pytest.raises(SystemExit, match="1"):
                lint_cmd.run(args)
            output = capsys.readouterr().out
            assert "Undocumented Docker file" in output
        finally:
            os.chdir(old_cwd)

    def test_stale_infrastructure_page(self, tmp_path, capsys):
        """Wiki page exists but Docker source removed → lint warns."""
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "dummy.py").write_text("")

        wiki = proj / "docs" / "llm_wiki"
        for d in ["entities", "modules", "workflows", "infrastructure"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "index.md").write_text("# Index\n")
        (wiki / "log.md").write_text("# Log\n")
        # Create a stale page for a Dockerfile that doesn't exist
        (wiki / "infrastructure" / "Dockerfile.md").write_text("# Dockerfile\n")

        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            import argparse
            from llm_wiki_cli.commands import lint_cmd
            args = argparse.Namespace(wiki_dir=str(wiki), src_dir=".")
            with pytest.raises(SystemExit, match="1"):
                lint_cmd.run(args)
            output = capsys.readouterr().out
            assert "Stale infrastructure page" in output
        finally:
            os.chdir(old_cwd)

    def test_documented_docker_file_passes(self, tmp_path, capsys):
        """Dockerfile in source + wiki page → lint passes (for infra check)."""
        proj = tmp_path / "proj"
        proj.mkdir()
        (proj / "Dockerfile").write_text("FROM alpine\n")
        (proj / "dummy.py").write_text("")

        wiki = proj / "docs" / "llm_wiki"
        for d in ["entities", "modules", "workflows", "infrastructure"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "index.md").write_text("# Index\n\n- [Dockerfile](infrastructure/Dockerfile.md)\n")
        (wiki / "log.md").write_text("# Log\n")
        (wiki / "infrastructure" / "Dockerfile.md").write_text("# Dockerfile\n")

        old_cwd = os.getcwd()
        os.chdir(proj)
        try:
            import argparse
            from llm_wiki_cli.commands import lint_cmd
            args = argparse.Namespace(wiki_dir=str(wiki), src_dir=".")
            # May still exit(1) due to other checks (undocumented modules, etc.)
            # but the Docker checks specifically should pass
            try:
                lint_cmd.run(args)
            except SystemExit:
                pass
            output = capsys.readouterr().out
            assert "All Docker/Compose files documented" in output
            assert "No stale infrastructure pages" in output
        finally:
            os.chdir(old_cwd)
