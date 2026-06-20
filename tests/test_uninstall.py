"""Tests for commands/uninstall_cmd.py"""

import types
from pathlib import Path

import pytest

from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.commands import uninstall_cmd


def _make_args(**kwargs):
    defaults = {
        "wiki_dir": "docs/llm_wiki",
        "remove_wiki": False,
        "dry_run": False,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _setup_wiki_project(project_dir: Path):
    """Set up a project with wiki artifacts for uninstall testing."""
    # Wiki dir
    wiki = project_dir / "docs" / "llm_wiki"
    for d in ["entities", "modules", "workflows"]:
        (wiki / d).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text("# Index\n")
    (wiki / "log.md").write_text("# Log\n")

    # Agent schema
    Path("CLAUDE.md").write_text(
        uninstall_cmd.CONSTRAINT_START
        + "\nstuff\n"
        + uninstall_cmd.CONSTRAINT_END
        + "\n"
    )

    # Git hooks
    hooks_dir = project_dir / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    (hooks_dir / "post-commit").write_text(
        "#!/bin/sh\n# LLM Wiki sync\nnohup llm-wiki trigger-agent &\n"
    )
    (hooks_dir / "post-commit").chmod(0o755)

    # Temp files
    (project_dir / ".git" / ".llm-wiki-agent").write_text("claude")
    (project_dir / ".git" / "llm-wiki-prompt.txt").write_text("prompt")
    (project_dir / ".git" / "llm-wiki.lock").write_text("")
    (project_dir / ".git" / "llm-wiki-breaker.json").write_text("{}")
    (project_dir / ".git" / "llm-wiki-sync.log").write_text("log")

    return wiki


class TestUninstallRemovesHooks:
    def test_removes_hook(self, tmp_project, capsys, monkeypatch):
        _setup_wiki_project(tmp_project)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = _make_args()
        uninstall_cmd.run(args)
        capsys.readouterr()

        hook = tmp_project / ".git" / "hooks" / "post-commit"
        assert not hook.exists()

    def test_preserves_non_wiki_hook(self, tmp_project, capsys, monkeypatch):
        hooks_dir = tmp_project / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        (hooks_dir / "post-commit").write_text("#!/bin/sh\necho custom\n")

        monkeypatch.setattr("builtins.input", lambda _: "y")
        args = _make_args()
        uninstall_cmd.run(args)

        assert (hooks_dir / "post-commit").exists()


class TestUninstallStripsConstraints:
    def test_strips_wiki_block(self, tmp_project, capsys, monkeypatch):
        _setup_wiki_project(tmp_project)
        Path("CLAUDE.md").write_text(
            "# My Rules\n\n"
            + uninstall_cmd.CONSTRAINT_START
            + "\nwiki stuff\n"
            + uninstall_cmd.CONSTRAINT_END
            + "\n"
        )
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = _make_args()
        uninstall_cmd.run(args)

        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        assert "My Rules" in content
        assert "LLM Wiki Maintainer Constraints" not in content

    def test_deletes_wiki_only_schema(self, tmp_project, capsys, monkeypatch):
        _setup_wiki_project(tmp_project)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = _make_args()
        uninstall_cmd.run(args)

        # CLAUDE.md contained only wiki block, should be deleted
        assert not Path("CLAUDE.md").exists()

    def test_strips_legacy_agents_md_wiki_block(self, tmp_project, capsys, monkeypatch):
        Path(".agents.md").write_text(
            "# Legacy Agent Rules\n\n"
            + uninstall_cmd.CONSTRAINT_START
            + "\nlegacy wiki stuff\n"
            + uninstall_cmd.CONSTRAINT_END
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args())

        content = Path(".agents.md").read_text(encoding="utf-8")
        assert "Legacy Agent Rules" in content
        assert "LLM Wiki Maintainer Constraints" not in content


class TestUninstallKeepsWiki:
    def test_wiki_preserved_by_default(self, tmp_project, capsys, monkeypatch):
        wiki = _setup_wiki_project(tmp_project)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = _make_args(remove_wiki=False)
        uninstall_cmd.run(args)

        assert wiki.exists()
        assert (wiki / "index.md").exists()

    def test_remove_wiki_flag(self, tmp_project, capsys, monkeypatch):
        wiki = _setup_wiki_project(tmp_project)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = _make_args(remove_wiki=True)
        uninstall_cmd.run(args)

        assert not wiki.exists()


class TestUninstallRuntimeArtifacts:
    def test_removes_all_runtime_artifacts(self, tmp_project, capsys, monkeypatch):
        _setup_wiki_project(tmp_project)
        monkeypatch.setattr("builtins.input", lambda _: "y")

        uninstall_cmd.run(_make_args())

        for name in [
            ".llm-wiki-agent",
            "llm-wiki-prompt.txt",
            "llm-wiki.lock",
            "llm-wiki-breaker.json",
            "llm-wiki-sync.log",
        ]:
            assert not (tmp_project / ".git" / name).exists()

    def test_dry_run_lists_runtime_artifacts(self, tmp_project, capsys):
        _setup_wiki_project(tmp_project)

        uninstall_cmd.run(_make_args(dry_run=True))

        out = capsys.readouterr().out
        assert "Runtime Artifacts" in out
        assert ".git/.llm-wiki-agent" in out
        assert ".git/llm-wiki.lock" in out
        assert ".git/llm-wiki-breaker.json" in out

    def test_rejects_absolute_wiki_dir_outside_project(
        self, tmp_project, tmp_path, monkeypatch
    ):
        outside = tmp_path / "outside_wiki"
        outside.mkdir()
        monkeypatch.setattr("builtins.input", lambda _: "y")

        with pytest.raises(PathValidationError):
            uninstall_cmd.run(_make_args(wiki_dir=str(outside), remove_wiki=True))

        assert outside.exists()

    def test_rejects_traversal_wiki_dir_outside_project(self, tmp_project, monkeypatch):
        outside = tmp_project.parent / "outside_wiki"
        outside.mkdir()
        monkeypatch.setattr("builtins.input", lambda _: "y")

        with pytest.raises(PathValidationError):
            uninstall_cmd.run(_make_args(wiki_dir="../outside_wiki", remove_wiki=True))

        assert outside.exists()


class TestUninstallDryRun:
    def test_dry_run_no_changes(self, tmp_project, capsys):
        wiki = _setup_wiki_project(tmp_project)
        hook = tmp_project / ".git" / "hooks" / "post-commit"

        args = _make_args(dry_run=True)
        uninstall_cmd.run(args)

        # Everything should still exist
        assert wiki.exists()
        assert hook.exists()
        assert Path("CLAUDE.md").exists()
