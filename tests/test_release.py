"""Tests for commands/release_cmd.py"""
import subprocess
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands.release_cmd import stamp_changelog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_CHANGELOG = textwrap.dedent("""\
    # Changelog

    All notable changes to this project will be documented in this file.

    ## [Unreleased]

    ### Added
    - New feature A
    - New feature B

    ## [0.1.4] - 2026-04-10

    ### Added
    - Old feature

    [Unreleased]: https://github.com/example/repo/compare/v0.1.4...HEAD
    [0.1.4]: https://github.com/example/repo/releases/tag/v0.1.4
""")

_EMPTY_UNRELEASED = textwrap.dedent("""\
    # Changelog

    ## [Unreleased]

    ## [0.1.4] - 2026-04-10

    ### Added
    - Old feature

    [Unreleased]: https://github.com/example/repo/compare/v0.1.4...HEAD
    [0.1.4]: https://github.com/example/repo/releases/tag/v0.1.4
""")


def _make_args(**kwargs):
    defaults = {"root": ".", "stage": False, "changelog": "CHANGELOG.md"}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Unit tests for stamp_changelog()
# ---------------------------------------------------------------------------

class TestStampChangelog:
    def test_replaces_unreleased_heading(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(_BASE_CHANGELOG)
        text, stamped = stamp_changelog(cl, "0.1.5", today="2026-04-11")
        assert stamped is True
        assert "## [0.1.5] - 2026-04-11" in text

    def test_prepends_fresh_unreleased(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(_BASE_CHANGELOG)
        text, stamped = stamp_changelog(cl, "0.1.5", today="2026-04-11")
        assert stamped is True
        unreleased_pos = text.index("## [Unreleased]")
        version_pos = text.index("## [0.1.5]")
        assert unreleased_pos < version_pos

    def test_only_one_unreleased_after_stamp(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(_BASE_CHANGELOG)
        text, _ = stamp_changelog(cl, "0.1.5", today="2026-04-11")
        assert text.count("## [Unreleased]") == 1

    def test_old_content_preserved(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(_BASE_CHANGELOG)
        text, _ = stamp_changelog(cl, "0.1.5", today="2026-04-11")
        assert "New feature A" in text
        assert "New feature B" in text

    def test_no_unreleased_raises(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text("# Changelog\n\n## [0.1.4] - 2026-04-10\n")
        with pytest.raises(ValueError, match="[Uu]nreleased"):
            stamp_changelog(cl, "0.1.5")


class TestStampChangelogEmptyGuard:
    """stamp_changelog must skip stamping when [Unreleased] has no content."""

    def test_returns_false_when_empty(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(_EMPTY_UNRELEASED)
        _text, stamped = stamp_changelog(cl, "0.1.5", today="2026-04-11")
        assert stamped is False

    def test_file_unchanged_when_empty(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(_EMPTY_UNRELEASED)
        text, stamped = stamp_changelog(cl, "0.1.5", today="2026-04-11")
        assert stamped is False
        assert text == _EMPTY_UNRELEASED

    def test_returns_true_when_has_content(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(_BASE_CHANGELOG)
        _text, stamped = stamp_changelog(cl, "0.1.5", today="2026-04-11")
        assert stamped is True

    def test_whitespace_only_body_is_empty(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text("# Changelog\n\n## [Unreleased]\n\n\n\n## [0.1.4]\n\n[Unreleased]: https://github.com/x/y/compare/v0.1.4...HEAD\n[0.1.4]: https://github.com/x/y/releases/tag/v0.1.4\n")
        _text, stamped = stamp_changelog(cl, "0.1.5")
        assert stamped is False


class TestStampChangelogReferenceLinks:
    def test_unreleased_link_points_to_new_version(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(_BASE_CHANGELOG)
        text, _ = stamp_changelog(cl, "0.1.5", today="2026-04-11")
        assert "[Unreleased]: https://github.com/example/repo/compare/v0.1.5...HEAD" in text

    def test_new_version_compare_link(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(_BASE_CHANGELOG)
        text, _ = stamp_changelog(cl, "0.1.5", today="2026-04-11")
        assert "[0.1.5]: https://github.com/example/repo/compare/v0.1.4...v0.1.5" in text

    def test_oldest_version_gets_releases_tag(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(_BASE_CHANGELOG)
        text, _ = stamp_changelog(cl, "0.1.5", today="2026-04-11")
        assert "[0.1.4]: https://github.com/example/repo/releases/tag/v0.1.4" in text

    def test_no_duplicate_links(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(_BASE_CHANGELOG)
        text, _ = stamp_changelog(cl, "0.1.5", today="2026-04-11")
        assert text.count("[0.1.4]:") == 1
        assert text.count("[Unreleased]:") == 1

    def test_duplicate_version_headings_get_one_reference_link(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ### Added
            - New feature

            ## [0.1.4] - 2026-04-10
            - Existing release

            ## [0.1.4] - 2026-04-10
            - Duplicate heading from a previous bad stamp

            [Unreleased]: https://github.com/example/repo/compare/v0.1.4...HEAD
            [0.1.4]: https://github.com/example/repo/releases/tag/v0.1.4
        """))

        text, _ = stamp_changelog(cl, "0.1.5", today="2026-04-11")

        assert text.count("[0.1.5]:") == 1
        assert text.count("[0.1.4]:") == 1


class TestStampChangelogMultipleVersions:
    """Stamping with 3 existing versions rebuilds all compare links."""

    _MULTI = textwrap.dedent("""\
        # Changelog

        ## [Unreleased]

        ### Added
        - Stuff

        ## [0.1.2] - 2026-04-09

        ### Added
        - More stuff

        ## [0.1.1] - 2026-04-08

        ## [0.1.0] - 2026-04-07

        [Unreleased]: https://github.com/example/repo/compare/v0.1.2...HEAD
        [0.1.2]: https://github.com/example/repo/compare/v0.1.1...v0.1.2
        [0.1.1]: https://github.com/example/repo/compare/v0.1.0...v0.1.1
        [0.1.0]: https://github.com/example/repo/releases/tag/v0.1.0
    """)

    def test_all_compare_links_rebuilt(self, tmp_path):
        cl = tmp_path / "CHANGELOG.md"
        cl.write_text(self._MULTI)
        text, _ = stamp_changelog(cl, "0.1.3", today="2026-04-10")
        assert "[0.1.3]: https://github.com/example/repo/compare/v0.1.2...v0.1.3" in text
        assert "[0.1.2]: https://github.com/example/repo/compare/v0.1.1...v0.1.2" in text
        assert "[0.1.1]: https://github.com/example/repo/compare/v0.1.0...v0.1.1" in text
        assert "[0.1.0]: https://github.com/example/repo/releases/tag/v0.1.0" in text


# ---------------------------------------------------------------------------
# Integration tests for release_cmd.run()
# ---------------------------------------------------------------------------

class TestReleaseCmdRun:
    def _write_changelog(self, content: str):
        Path("CHANGELOG.md").write_text(content)

    def test_stamps_changelog_file(self, tmp_project, capsys):
        from llm_wiki_cli.commands import release_cmd
        self._write_changelog(_BASE_CHANGELOG)
        args = _make_args()
        release_cmd.run(args)
        result = Path("CHANGELOG.md").read_text(encoding="utf-8")
        assert "## [0.1.0]" in result  # tmp_project uses version 0.1.0
        assert "## [Unreleased]" in result

    def test_prints_confirmation(self, tmp_project, capsys):
        from llm_wiki_cli.commands import release_cmd
        self._write_changelog(_BASE_CHANGELOG)
        args = _make_args()
        release_cmd.run(args)
        out = capsys.readouterr().out
        assert "CHANGELOG.md" in out
        assert "0.1.0" in out

    def test_stage_flag_stages_changelog(self, tmp_project, capsys):
        from llm_wiki_cli.commands import release_cmd
        subprocess.run(["git", "add", "."], capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], capture_output=True)
        self._write_changelog(_BASE_CHANGELOG)
        args = _make_args(stage=True)
        release_cmd.run(args)
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True,
        )
        assert "CHANGELOG.md" in result.stdout

    def test_stage_git_add_uses_explicit_no_shell(self, tmp_project, monkeypatch):
        from llm_wiki_cli.commands import release_cmd
        self._write_changelog(_BASE_CHANGELOG)
        seen = {}

        def fake_run(cmd, **kwargs):
            seen["cmd"] = cmd
            seen["kwargs"] = kwargs
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr(release_cmd.subprocess, "run", fake_run)

        release_cmd.run(_make_args(stage=True))

        assert seen["cmd"] == ["git", "add", "CHANGELOG.md"]
        assert seen["kwargs"]["shell"] is False

    def test_stage_git_add_failure_exits_nonzero(self, tmp_project, monkeypatch):
        from llm_wiki_cli.commands import release_cmd
        self._write_changelog(_BASE_CHANGELOG)

        def fake_run(*args, **kwargs):
            raise subprocess.CalledProcessError(128, args[0], stderr="not a git repo")

        monkeypatch.setattr(release_cmd.subprocess, "run", fake_run)

        with pytest.raises(SystemExit) as exc_info:
            release_cmd.run(_make_args(stage=True))

        assert exc_info.value.code == 1

    def test_missing_changelog_exits_1(self, tmp_project):
        from llm_wiki_cli.commands import release_cmd
        args = _make_args(changelog="NONEXISTENT.md")
        with pytest.raises(SystemExit) as exc_info:
            release_cmd.run(args)
        assert exc_info.value.code == 1

    def test_no_unreleased_section_exits_1(self, tmp_project):
        from llm_wiki_cli.commands import release_cmd
        Path("CHANGELOG.md").write_text("# Changelog\n\n## [0.1.0]\n")
        args = _make_args()
        with pytest.raises(SystemExit) as exc_info:
            release_cmd.run(args)
        assert exc_info.value.code == 1

    def test_empty_unreleased_skips_stamp_exits_0(self, tmp_project, capsys):
        """When [Unreleased] is empty, run() should print a notice and exit cleanly."""
        from llm_wiki_cli.commands import release_cmd
        self._write_changelog(_EMPTY_UNRELEASED)
        args = _make_args()
        release_cmd.run(args)  # must NOT raise SystemExit
        out = capsys.readouterr().out
        assert "empty" in out.lower() or "nothing" in out.lower()
        # File must be untouched
        assert Path("CHANGELOG.md").read_text(encoding="utf-8") == _EMPTY_UNRELEASED

    def test_empty_unreleased_does_not_stage(self, tmp_project):
        """Empty [Unreleased] should not stage CHANGELOG even with --stage."""
        from llm_wiki_cli.commands import release_cmd
        subprocess.run(["git", "add", "."], capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], capture_output=True)
        self._write_changelog(_EMPTY_UNRELEASED)
        args = _make_args(stage=True)
        release_cmd.run(args)
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True,
        )
        assert "CHANGELOG.md" not in result.stdout
