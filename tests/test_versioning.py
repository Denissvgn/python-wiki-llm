"""Tests for services/versioning.py"""

import pytest

from llm_wiki_cli.services.versioning import (
    bump_patch,
    bump_minor,
    find_version_file,
    read_version,
    write_version,
)


# ── bump_patch / bump_minor ──────────────────────────────────────────


class TestBumpPatch:
    def test_normal(self):
        assert bump_patch("1.2.3") == "1.2.4"

    def test_zero(self):
        assert bump_patch("0.0.0") == "0.0.1"

    def test_large(self):
        assert bump_patch("1.2.99") == "1.2.100"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            bump_patch("not-a-version")


class TestBumpMinor:
    def test_normal(self):
        assert bump_minor("1.2.3") == "1.3.0"

    def test_zero(self):
        assert bump_minor("0.0.0") == "0.1.0"

    def test_resets_patch(self):
        assert bump_minor("1.2.99") == "1.3.0"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            bump_minor("bad")


# ── find_version_file ────────────────────────────────────────────────


class TestFindVersionFile:
    def test_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.0.0"\n')
        assert find_version_file(str(tmp_path)).name == "pyproject.toml"

    def test_setup_cfg(self, tmp_path):
        (tmp_path / "setup.cfg").write_text("[metadata]\nversion = 1.0.0\n")
        assert find_version_file(str(tmp_path)).name == "setup.cfg"

    def test_package_json(self, tmp_path):
        (tmp_path / "package.json").write_text('{"version": "1.0.0"}')
        assert find_version_file(str(tmp_path)).name == "package.json"

    def test_version_file(self, tmp_path):
        (tmp_path / "VERSION").write_text("1.0.0\n")
        assert find_version_file(str(tmp_path)).name == "VERSION"

    def test_none(self, tmp_path):
        assert find_version_file(str(tmp_path)) is None

    def test_priority_pyproject_over_setup_cfg(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.0.0"\n')
        (tmp_path / "setup.cfg").write_text("[metadata]\nversion = 2.0.0\n")
        assert find_version_file(str(tmp_path)).name == "pyproject.toml"


# ── read_version / write_version ─────────────────────────────────────


class TestReadWriteVersion:
    def test_read_pyproject(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text('[project]\nname = "foo"\nversion = "1.2.3"\n')
        assert read_version(p) == "1.2.3"

    def test_read_pyproject_prefers_project_over_poetry(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text(
            '[project]\nname = "foo"\nversion = "1.2.3"\n'
            '\n[tool.poetry]\nname = "foo"\nversion = "9.9.9"\n'
        )
        assert read_version(p) == "1.2.3"

    def test_read_pyproject_poetry_fallback(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text('[tool.poetry]\nname = "foo"\nversion = "1.2.3"\n')
        assert read_version(p) == "1.2.3"

    def test_read_pyproject_dynamic_project_version(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text('[project]\nname = "foo"\ndynamic = ["version"]\n')
        assert read_version(p) is None

    def test_read_setup_cfg(self, tmp_path):
        p = tmp_path / "setup.cfg"
        p.write_text("[metadata]\nname = foo\nversion = 1.2.3\n")
        assert read_version(p) == "1.2.3"

    def test_read_package_json(self, tmp_path):
        p = tmp_path / "package.json"
        p.write_text('{\n  "name": "foo",\n  "version": "1.2.3"\n}')
        assert read_version(p) == "1.2.3"

    def test_read_version_file(self, tmp_path):
        p = tmp_path / "VERSION"
        p.write_text("1.2.3\n")
        assert read_version(p) == "1.2.3"

    def test_write_pyproject(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text(
            '[project]\nname = "foo"\nversion = "1.2.3"\ndescription = "bar"\n'
        )
        write_version(p, "2.0.0")
        assert read_version(p) == "2.0.0"
        # preserve other content
        assert 'name = "foo"' in p.read_text(encoding="utf-8")
        assert 'description = "bar"' in p.read_text(encoding="utf-8")

    def test_write_pyproject_updates_project_not_poetry(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text(
            '[project]\nname = "foo"\nversion = "1.2.3"\n'
            '\n[tool.poetry]\nname = "foo"\nversion = "9.9.9"\n'
        )
        write_version(p, "2.0.0")
        text = p.read_text(encoding="utf-8")
        assert '[project]\nname = "foo"\nversion = "2.0.0"' in text
        assert '[tool.poetry]\nname = "foo"\nversion = "9.9.9"' in text

    def test_write_pyproject_rejects_dynamic_version(self, tmp_path):
        p = tmp_path / "pyproject.toml"
        p.write_text('[project]\nname = "foo"\ndynamic = ["version"]\n')
        with pytest.raises(ValueError):
            write_version(p, "2.0.0")

    def test_write_setup_cfg(self, tmp_path):
        p = tmp_path / "setup.cfg"
        p.write_text("[metadata]\nname = foo\nversion = 1.2.3\n")
        write_version(p, "2.0.0")
        assert read_version(p) == "2.0.0"

    def test_write_package_json(self, tmp_path):
        p = tmp_path / "package.json"
        p.write_text('{\n  "name": "foo",\n  "version": "1.2.3"\n}')
        write_version(p, "2.0.0")
        assert read_version(p) == "2.0.0"

    def test_write_version_file(self, tmp_path):
        p = tmp_path / "VERSION"
        p.write_text("1.2.3\n")
        write_version(p, "2.0.0")
        assert read_version(p) == "2.0.0"

    def test_roundtrip_all_formats(self, tmp_path):
        cases = [
            ("pyproject.toml", '[project]\nversion = "0.1.0"\n'),
            ("setup.cfg", "[metadata]\nversion = 0.1.0\n"),
            ("package.json", '{"version": "0.1.0"}'),
            ("VERSION", "0.1.0\n"),
        ]
        for filename, content in cases:
            p = tmp_path / filename
            p.write_text(content)
            assert read_version(p) == "0.1.0", f"read failed for {filename}"
            write_version(p, "1.0.0")
            assert read_version(p) == "1.0.0", f"roundtrip failed for {filename}"
            p.unlink()
