"""Tests for commands/generate_prompt_cmd.py"""

from __future__ import annotations

import ast
import inspect
import os
import stat
import textwrap
import types
from pathlib import Path


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


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    assert isinstance(function_node, ast.FunctionDef)
    body = list(function_node.body)
    first_body_line = min(stmt.lineno for stmt in body)
    last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
    return last_body_line - first_body_line + 1


class TestGeneratePromptWritesFile:
    def test_creates_output_file(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)

        out = Path(".git/llm-wiki-prompt.txt")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_output_file_is_owner_only(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)

        mode = stat.S_IMODE(Path(".git/llm-wiki-prompt.txt").stat().st_mode)
        if os.name == "nt":
            assert Path(".git/llm-wiki-prompt.txt").is_file()
        else:
            assert mode == 0o600

    def test_prompt_contains_wiki_dir(self, tmp_project):
        args = _make_args(wiki_dir="my_docs/wiki")
        generate_prompt_cmd.run(args)

        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "my_docs/wiki" in content

    def test_prompt_contains_extract_command(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)

        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "llm-wiki extract" in content
        assert "--changed" in content
        assert "--summary" in content

    def test_custom_output_path(self, tmp_project, tmp_path):
        out_file = str(tmp_path / "my_prompt.txt")
        args = _make_args(output=out_file)
        generate_prompt_cmd.run(args)

        assert Path(out_file).exists()

    def test_prompt_quotes_paths_with_spaces(self, tmp_project):
        args = _make_args(wiki_dir="my docs/wiki", src_dir="src dir")
        generate_prompt_cmd.run(args)

        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "llm-wiki extract --src-dir 'src dir' --changed --summary" in content
        assert "llm-wiki lint --wiki-dir 'my docs/wiki' --src-dir 'src dir'" in content
        assert "git add 'my docs/wiki/' CHANGELOG.md" in content

    def test_output_message_quotes_output_path_with_spaces(self, tmp_project, capsys):
        args = _make_args(output=".git/wiki prompt.txt")
        generate_prompt_cmd.run(args)

        out = capsys.readouterr().out
        assert "cat '.git/wiki prompt.txt'" in out


class TestGeneratePromptPrintMode:
    def test_print_goes_to_stdout(self, tmp_project, capsys):
        args = _make_args(print_prompt=True)
        generate_prompt_cmd.run(args)

        out = capsys.readouterr().out
        assert "Wiki synchronizer" in out
        # No file should be written
        assert not Path(".git/llm-wiki-prompt.txt").exists()


class TestGeneratePromptBuildPrompt:
    def test_build_prompt_stays_decomposed(self):
        assert _body_line_count(generate_prompt_cmd._build_prompt) <= 40

    def test_prompt_contains_section_headings(self, tmp_project):
        """Prompt should have the goal-driven section headings."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "## Context" in content
        assert "## Success Criteria" in content
        assert "## Verify & Commit" in content

    def test_prompt_contains_lint_success_criterion(self, tmp_project):
        """Prompt should frame lint exit 0 as a success criterion."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "llm-wiki lint" in content
        assert "exits 0" in content

    def test_prompt_contains_log_criterion(self, tmp_project):
        """Prompt should require a log.md entry as a success criterion."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "log.md" in content
        assert "new entry" in content

    def test_prompt_contains_only_affected_criterion(self, tmp_project):
        """Prompt should instruct agents to only modify affected pages."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "Only affected pages" in content

    def test_prompt_runs_sync_before_semantic_pass(self, tmp_project):
        """Prompt should run deterministic sync, then require semantic enrichment."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert (
            "llm-wiki sync --jobs auto --wiki-dir docs/llm_wiki --src-dir ." in content
        )
        assert "## Semantic Pass" in content
        assert "Semantic pass complete" in content
        assert "_Auto-generated from ..._" in content
        assert "generated AST/docstring skeletons" in content

    def test_prompt_contains_git_diff_command(self, tmp_project):
        """Prompt should instruct the agent to run git diff."""
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "git diff HEAD~1..HEAD" in content

    def test_prompt_commit_uses_auto_commit_guard(self, tmp_project):
        args = _make_args()
        generate_prompt_cmd.run(args)
        content = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert (
            'LLM_WIKI_AUTO_COMMIT=1 git commit -m "docs(wiki): auto-update [bot]"'
            in content
        )
