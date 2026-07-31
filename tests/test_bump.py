"""Tests for commands/bump_cmd.py"""

import shutil
import subprocess
import types
from pathlib import Path

import pytest
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
        content = Path("pyproject.toml").read_text(encoding="utf-8")
        assert "0.1.1" in content


class TestBumpMinorCmd:
    def test_bumps_minor(self, tmp_project, capsys):
        args = _make_args(bump_type="minor")
        bump_cmd.run(args)
        out = capsys.readouterr().out
        assert "0.1.0 -> 0.2.0" in out


class TestBumpStageFlag:
    @pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
    def test_stage_git_adds(self, tmp_project, capsys):
        # Initial commit so git is ready
        subprocess.run(["git", "add", "."], capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], capture_output=True)

        args = _make_args(bump_type="patch", stage=True)
        bump_cmd.run(args)

        # Check that pyproject.toml is staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
        )
        assert "pyproject.toml" in result.stdout

    def test_stage_git_add_failure_exits_nonzero(self, tmp_project, monkeypatch):
        def fake_run(*args, **kwargs):
            raise subprocess.CalledProcessError(128, args[0], stderr="not a git repo")

        monkeypatch.setattr(bump_cmd.subprocess, "run", fake_run)

        with pytest.raises(SystemExit) as exc_info:
            bump_cmd.run(_make_args(bump_type="patch", stage=True))

        assert exc_info.value.code == 1

    def test_stage_reports_missing_git(self, tmp_project, monkeypatch, capsys):
        def missing_git(*args, **kwargs):
            raise FileNotFoundError

        monkeypatch.setattr(bump_cmd.subprocess, "run", missing_git)

        with pytest.raises(SystemExit) as exc_info:
            bump_cmd.run(_make_args(bump_type="patch", stage=True))

        assert exc_info.value.code == 1
        assert "git not found" in capsys.readouterr().err


class TestBumpValidation:
    def test_missing_version_file_is_actionable(self, monkeypatch, capsys):
        monkeypatch.setattr(bump_cmd, "find_version_file", lambda root: None)

        with pytest.raises(SystemExit) as exc_info:
            bump_cmd.run(_make_args())

        assert exc_info.value.code == 1
        assert "No version file found" in capsys.readouterr().out

    def test_unparseable_version_is_actionable(self, monkeypatch, capsys):
        version_file = Path("VERSION")
        monkeypatch.setattr(
            bump_cmd, "find_version_file", lambda root: version_file
        )
        monkeypatch.setattr(bump_cmd, "read_version", lambda path: None)

        with pytest.raises(SystemExit) as exc_info:
            bump_cmd.run(_make_args())

        assert exc_info.value.code == 1
        assert "Could not parse version from VERSION" in capsys.readouterr().out

    def test_unknown_bump_type_is_rejected(self, tmp_project, capsys):
        with pytest.raises(SystemExit) as exc_info:
            bump_cmd.run(_make_args(bump_type="major"))

        assert exc_info.value.code == 1
        assert "Unknown bump type 'major'" in capsys.readouterr().out
