"""Tests for commands/bump_cmd.py"""
import subprocess
import types
from pathlib import Path

from llm_wiki_cli.commands import bump_cmd


def _make_args(**kwargs):
    defaults = {"root": ".", "stage": False, "bump_type": "patch"}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestBumpPatchCmd:
    def test_bumps_patch(self, tmp_project, capsys):
        args = _make_args(bump_type="patch")
        bump_cmd.run(args)
        out = capsys.readouterr().out
        assert "0.1.0 -> 0.1.1" in out

    def test_version_changed_on_disk(self, tmp_project):
        args = _make_args(bump_type="patch")
        bump_cmd.run(args)
        content = Path("pyproject.toml").read_text()
        assert '0.1.1' in content


class TestBumpMinorCmd:
    def test_bumps_minor(self, tmp_project, capsys):
        args = _make_args(bump_type="minor")
        bump_cmd.run(args)
        out = capsys.readouterr().out
        assert "0.1.0 -> 0.2.0" in out


class TestBumpStageFlag:
    def test_stage_git_adds(self, tmp_project, capsys):
        # Initial commit so git is ready
        subprocess.run(["git", "add", "."], capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], capture_output=True)

        args = _make_args(bump_type="patch", stage=True)
        bump_cmd.run(args)

        # Check that pyproject.toml is staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True
        )
        assert "pyproject.toml" in result.stdout
