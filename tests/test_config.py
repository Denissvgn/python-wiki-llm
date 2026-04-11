"""Tests for config.py — shared constants and validate_path."""
import os
import types
from pathlib import Path

import pytest

from llm_wiki_cli.config import (
    AGENT_CHOICES,
    CLI_AGENTS,
    DEFAULT_WIKI_DIR,
    IDE_AGENTS,
    validate_path,
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
        with pytest.raises(SystemExit):
            validate_path("../../etc", "--wiki-dir")

    def test_rejects_absolute_outside(self, tmp_path):
        os.chdir(tmp_path)
        with pytest.raises(SystemExit):
            validate_path("/tmp/outside", "--wiki-dir")

    def test_accepts_absolute_inside(self, tmp_path):
        os.chdir(tmp_path)
        sub = tmp_path / "inner"
        sub.mkdir()
        result = validate_path(str(sub), "--wiki-dir")
        assert result == sub
