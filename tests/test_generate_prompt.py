"""Tests for commands/generate_prompt_cmd.py"""
from __future__ import annotations

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

    def test_prompt_contains_extract_command(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)

        content = Path(".git/llm-wiki-prompt.txt").read_text()
        assert "llm-wiki extract" in content
        assert "--changed" in content
        assert "--summary" in content

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
    def test_prompt_contains_step_headings(self, tmp_project):
        """Prompt should have the three instructional steps."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text()
        assert "Step 1" in content
        assert "Step 2" in content
        assert "Step 3" in content

    def test_prompt_contains_git_diff_command(self, tmp_project):
        """Prompt should instruct the agent to run git diff."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text()
        assert "git diff HEAD~1..HEAD" in content
