"""Tests for config.py — shared constants and validate_path."""
import json
import os
import types
from pathlib import Path

import pytest

from llm_wiki_cli.config import (
    AGENT_CHOICES,
    CLI_AGENTS,
    DEFAULT_WIKI_DIR,
    IDE_AGENTS,
    build_gitignore_matcher,
    read_config,
    PathValidationError,
    validate_path,
    validate_source_paths,
    validate_source_root,
    write_config,
)


class TestConstants:
    def test_default_wiki_dir(self):
        assert DEFAULT_WIKI_DIR == "docs/llm_wiki"

    def test_agent_choices_has_all(self):
        assert set(AGENT_CHOICES) == set(CLI_AGENTS) | IDE_AGENTS

    def test_cli_and_ide_disjoint(self):
        assert set(CLI_AGENTS) & IDE_AGENTS == set()


class TestValidatePath:
    def test_accepts_relative_subdir(self, tmp_path):
        os.chdir(tmp_path)
        sub = tmp_path / "docs" / "wiki"
        sub.mkdir(parents=True)
        result = validate_path("docs/wiki", "--wiki-dir")
        assert result == sub

    def test_accepts_dot(self, tmp_path):
        os.chdir(tmp_path)
        result = validate_path(".", "--src-dir")
        assert result == tmp_path

    def test_rejects_traversal(self, tmp_path):
        os.chdir(tmp_path)
        with pytest.raises(PathValidationError):
            validate_path("../../etc", "--wiki-dir")

    def test_rejects_absolute_outside(self, tmp_path):
        os.chdir(tmp_path)
        with pytest.raises(PathValidationError):
            validate_path("/tmp/outside", "--wiki-dir")

    def test_accepts_absolute_inside(self, tmp_path):
        os.chdir(tmp_path)
        sub = tmp_path / "inner"
        sub.mkdir()
        result = validate_path(str(sub), "--wiki-dir")
        assert result == sub

    def test_source_root_preserves_default_cwd_guard(self, tmp_path):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        outside.mkdir()
        os.chdir(project)

        with pytest.raises(PathValidationError):
            validate_source_root(str(outside), "--src-dir")

    def test_source_root_allows_external_existing_directory(self, tmp_path):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        outside.mkdir()
        os.chdir(project)

        assert validate_source_root(str(outside), "--src-dir", allow_external=True) == outside

    def test_source_paths_reject_escape_from_source_root(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        with pytest.raises(PathValidationError):
            validate_source_paths(source, ["../outside.py"])

    def test_source_paths_accept_relative_and_absolute_inside_root(self, tmp_path):
        source = tmp_path / "source"
        package = source / "package"
        package.mkdir(parents=True)
        module = package / "module.py"
        module.write_text("VALUE = 1\n", encoding="utf-8")

        assert validate_source_paths(
            source,
            ["package/module.py", str(module)],
        ) is None

    def test_source_paths_accept_nonexistent_relative_inside_root(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()

        assert validate_source_paths(source, ["generated/future.py"]) is None

    def test_source_paths_ignore_empty_inputs(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()

        assert validate_source_paths(source, None) is None
        assert validate_source_paths(source, [""]) is None

    def test_source_paths_reject_absolute_outside_root(self, tmp_path):
        source = tmp_path / "source"
        outside = tmp_path / "outside.py"
        source.mkdir()
        outside.write_text("VALUE = 1\n", encoding="utf-8")

        with pytest.raises(PathValidationError):
            validate_source_paths(source, [str(outside)])


class TestReadWriteConfig:
    """Round-trip JSON config and backward compatibility."""

    def test_write_then_read(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        data = {"agent": "copilot", "quality_hints": False}
        write_config(str(wiki), data)
        result = read_config(str(wiki))
        assert result["agent"] == "copilot"
        assert result["quality_hints"] is False

    def test_defaults_when_no_file(self, tmp_path):
        os.chdir(tmp_path)
        result = read_config(str(tmp_path / "nonexistent"))
        assert result["agent"] == "generic"
        assert result["quality_hints"] is True

    def test_backward_compat_bare_string(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        config_path = wiki / ".llm-wiki-agent"
        config_path.write_text("claude")
        result = read_config(str(wiki))
        assert result["agent"] == "claude"
        assert result["quality_hints"] is True

    def test_missing_key_gets_default(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        config_path = wiki / ".llm-wiki-agent"
        config_path.write_text(json.dumps({"agent": "aider"}))
        result = read_config(str(wiki))
        assert result["agent"] == "aider"
        assert result["quality_hints"] is True

    def test_corrupted_json_returns_defaults(self, tmp_path):
        os.chdir(tmp_path)
        wiki = tmp_path / "docs" / "wiki"
        wiki.mkdir(parents=True)
        config_path = wiki / ".llm-wiki-agent"
        config_path.write_text("{invalid json!!}")
        result = read_config(str(wiki))
        assert result["agent"] == "generic"
        assert result["quality_hints"] is True


class TestGitIgnoreMatcher:
    def test_supports_root_anchored_negation_and_dir_patterns(self, tmp_path):
        (tmp_path / ".gitignore").write_text(
            "/root_only.py\n"
            "build/\n"
            "*.pyc\n"
            "!keep.pyc\n"
            "**/cache/*.json\n",
            encoding="utf-8",
        )
        matcher = build_gitignore_matcher(tmp_path)

        assert matcher.is_ignored("root_only.py")
        assert not matcher.is_ignored("pkg/root_only.py")
        assert matcher.is_ignored("build/out.py")
        assert matcher.is_ignored("pkg/build/out.py")
        assert matcher.is_ignored("x.pyc")
        assert not matcher.is_ignored("keep.pyc")
        assert matcher.is_ignored("pkg/cache/data.json")

    def test_nested_gitignore_applies_to_subtree(self, tmp_path):
        nested = tmp_path / "pkg"
        nested.mkdir()
        (nested / ".gitignore").write_text("generated/\n", encoding="utf-8")
        matcher = build_gitignore_matcher(tmp_path)

        assert matcher.is_ignored("pkg/generated/out.py")
        assert not matcher.is_ignored("generated/out.py")
