"""Tests for commands/generate_prompt_cmd.py"""
from __future__ import annotations

import subprocess
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import generate_prompt_cmd


def _make_args(**kwargs):
    defaults = {
        "wiki_dir": "docs/llm_wiki",
        "src_dir": ".",
        "output": ".git/llm-wiki-prompt.txt",
        "print_prompt": False,
        "no_diff": True,  # avoid needing real git commits in tests
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestGeneratePromptWritesFile:
    def test_creates_output_file(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)

        out = Path(".git/llm-wiki-prompt.txt")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_prompt_contains_wiki_dir(self, tmp_project):
        args = _make_args(wiki_dir="my_docs/wiki")
        generate_prompt_cmd.run(args)

        content = Path(".git/llm-wiki-prompt.txt").read_text()
        assert "my_docs/wiki" in content

    def test_prompt_contains_ast_structure(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)

        content = Path(".git/llm-wiki-prompt.txt").read_text()
        # The AST JSON block should be present
        assert "AST structure" in content

    def test_custom_output_path(self, tmp_project, tmp_path):
        out_file = str(tmp_path / "my_prompt.txt")
        args = _make_args(output=out_file)
        generate_prompt_cmd.run(args)

        assert Path(out_file).exists()


class TestGeneratePromptPrintMode:
    def test_print_goes_to_stdout(self, tmp_project, capsys):
        args = _make_args(print_prompt=True)
        generate_prompt_cmd.run(args)

        out = capsys.readouterr().out
        assert "Wiki synchronizer" in out
        # No file should be written
        assert not Path(".git/llm-wiki-prompt.txt").exists()


class TestGeneratePromptBuildPrompt:
    def test_no_diff_skips_git(self, tmp_project):
        """With --no-diff, function should not call git and succeed."""
        args = _make_args(no_diff=True)
        generate_prompt_cmd.run(args)  # must not raise

    def test_diff_included_when_available(self, tmp_project):
        """When no_diff=False and git works, diff text is included in the prompt."""
        # Create a commit so HEAD~1 exists
        subprocess.run(["git", "add", "."], cwd=".", capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=".", capture_output=True)
        subprocess.run(["git", "add", "."], cwd=".", capture_output=True)
        subprocess.run(["git", "commit", "-m", "second"], cwd=".", capture_output=True)

        args = _make_args(no_diff=False)
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text()
        assert "Git Diff" in content
