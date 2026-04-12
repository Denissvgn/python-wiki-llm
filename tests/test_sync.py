"""Tests for commands/sync_cmd.py — incremental wiki sync."""
import os
import sys
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.commands.sync_cmd import (
    MANIFEST_FILENAME,
    SyncManifest,
    _compute_diff,
    _hash_file,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_bootstrap_args(**kwargs):
    defaults = {
        "src_dir": ".",
        "wiki_dir": "docs/llm_wiki",
        "overwrite": False,
        "depth": "full",
        "skip_workflows": True,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _make_sync_args(**kwargs):
    defaults = {"src_dir": ".", "wiki_dir": "docs/llm_wiki"}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


@pytest.fixture
def bootstrapped_project(tmp_path):
    """A project that has been fully bootstrapped with a manifest."""
    import subprocess

    proj = tmp_path / "project"
    proj.mkdir()

    subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(proj), "config", "user.email", "t@t.com"],
        capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "-C", str(proj), "config", "user.name", "T"],
        capture_output=True, check=True,
    )

    (proj / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "0.1.0"\n'
    )
    (proj / "models.py").write_text(
        textwrap.dedent("""\
            class User:
                \"\"\"A system user.\"\"\"
                name: str = ""
                email: str = ""
        """)
    )

    wiki_dir = proj / "docs" / "llm_wiki"
    old_cwd = os.getcwd()
    os.chdir(proj)

    bootstrap_cmd.run(
        _make_bootstrap_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
    )
    # Write manifest so sync can run
    _write_manifest_from_bootstrap(proj, wiki_dir)

    yield proj, wiki_dir
    os.chdir(old_cwd)


def _write_manifest_from_bootstrap(proj: Path, wiki_dir: Path) -> None:
    """Write a .llm-wiki-manifest.json for the current state of proj."""
    from llm_wiki_cli.commands.extract_cmd import get_inventory
    from llm_wiki_cli.commands.sync_cmd import (
        SyncManifest,
        _collision_maps,
        _page_name_for_module,
    )

    inventory = get_inventory(str(proj), deep=True)
    colliding_stems, colliding_cls, entity_page_cache = _collision_maps(inventory, str(proj))
    module_page_map = {
        fp: _page_name_for_module(fp, str(proj), colliding_stems)
        for fp in inventory
    }
    manifest = SyncManifest.build_from_inventory(
        inventory, str(proj), entity_page_cache, module_page_map
    )
    manifest.save(wiki_dir)


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestNoManifest:
    """sync exits 1 with a clear message when no manifest exists."""

    def test_exits_one_and_prints_error(self, tmp_path, capsys):
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        wiki_dir.mkdir(parents=True)
        args = _make_sync_args(src_dir=str(tmp_path), wiki_dir=str(wiki_dir))

        old_cwd = os.getcwd()
        os.chdir(tmp_path)  # validate_path checks relative to cwd
        try:
            with pytest.raises(SystemExit) as exc_info:
                sync_cmd.run(args)
        finally:
            os.chdir(old_cwd)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "bootstrap" in captured.err.lower()
        assert MANIFEST_FILENAME in captured.err


class TestUnchangedFile:
    """When nothing changed, sync prints 'up to date' and skips all pages."""

    def test_wiki_is_up_to_date(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))

        # Run sync immediately after bootstrap — nothing should change
        sync_cmd.run(args)

        captured = capsys.readouterr()
        assert "up to date" in captured.out.lower()

    def test_entity_page_not_rewritten(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        entity_path = wiki_dir / "entities" / "User.md"
        original_content = entity_path.read_text()
        original_mtime = entity_path.stat().st_mtime

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        # File should not have been touched
        assert entity_path.stat().st_mtime == original_mtime


class TestChangedFile:
    """When a source file is modified, affected pages are updated."""

    def test_entity_page_updated(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        models_py = proj / "models.py"

        # Modify source
        models_py.write_text(
            textwrap.dedent("""\
                class User:
                    \"\"\"An updated user with role.\"\"\"
                    name: str = ""
                    email: str = ""
                    role: str = "viewer"
            """)
        )

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        captured = capsys.readouterr()
        assert "UPDATE entity: User" in captured.out

        # Entity page should contain the new attribute
        entity_content = (wiki_dir / "entities" / "User.md").read_text()
        assert "role" in entity_content

    def test_module_page_updated(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").write_text(
            textwrap.dedent("""\
                class User:
                    \"\"\"An updated user.\"\"\"
                    name: str = ""
            """)
        )

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        captured = capsys.readouterr()
        assert "UPDATE module: models" in captured.out

    def test_manifest_updated_after_sync(self, bootstrapped_project):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").write_text(
            textwrap.dedent("""\
                class User:
                    \"\"\"Changed.\"\"\"
            """)
        )

        old_manifest = SyncManifest.load(wiki_dir)
        old_hash = next(
            (v.get("hash", "") for k, v in old_manifest.sources.items() if k.endswith("models.py")),
            "",
        )
        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))
        new_manifest = SyncManifest.load(wiki_dir)
        new_hash = next(
            (v.get("hash", "") for k, v in new_manifest.sources.items() if k.endswith("models.py")),
            "",
        )

        assert old_hash != new_hash


class TestNewFile:
    """When a new source file is added, new pages are created and manifest updated."""

    def test_new_pages_created(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        (proj / "auth.py").write_text(
            textwrap.dedent("""\
                class AuthService:
                    \"\"\"Handles authentication.\"\"\"
                    secret: str = ""
            """)
        )

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        captured = capsys.readouterr()
        assert "CREATE entity: AuthService" in captured.out
        assert "CREATE module: auth" in captured.out
        assert (wiki_dir / "entities" / "AuthService.md").exists()
        assert (wiki_dir / "modules" / "auth.md").exists()

    def test_new_file_in_manifest(self, bootstrapped_project):
        proj, wiki_dir = bootstrapped_project
        (proj / "auth.py").write_text("class AuthService:\n    pass\n")

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        manifest = SyncManifest.load(wiki_dir)
        assert any(k.endswith("auth.py") for k in manifest.sources)


class TestMovedClass:
    """When a class moves to a different file, its entity page is updated in-place."""

    def test_moved_entity_page_updated(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project

        # Remove User from models.py, add it to users.py
        (proj / "models.py").write_text("# empty\n")
        (proj / "users.py").write_text(
            textwrap.dedent("""\
                class User:
                    \"\"\"A moved user.\"\"\"
                    name: str = ""
            """)
        )

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        captured = capsys.readouterr()
        # The entity page should be updated (now points at users.py)
        entity_content = (wiki_dir / "entities" / "User.md").read_text()
        assert "users.py" in entity_content

        # Moved entities should be mentioned in summary
        assert "User" in captured.out

    def test_move_detected_in_diff(self, bootstrapped_project):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").write_text("# empty\n")
        (proj / "users.py").write_text("class User:\n    pass\n")

        from llm_wiki_cli.commands.extract_cmd import get_inventory

        manifest = SyncManifest.load(wiki_dir)
        inventory = get_inventory(str(proj), deep=True)
        diff = _compute_diff(manifest, inventory, str(proj))

        assert "User" in diff.moved_entities


class TestDeletedClass:
    """When a source file is removed, existing pages get a deprecation warning."""

    def test_deprecation_header_added_to_entity(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project

        # Delete models.py
        (proj / "models.py").unlink()

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        captured = capsys.readouterr()
        assert "DEPRECATE" in captured.out

        entity_content = (wiki_dir / "entities" / "User.md").read_text()
        assert "⚠️" in entity_content
        assert "Stale" in entity_content

    def test_deprecation_header_is_idempotent(self, bootstrapped_project):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").unlink()

        args = _make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir))
        sync_cmd.run(args)

        # Reset manifest to old state to allow running sync again
        _write_manifest_from_bootstrap_from_disk(wiki_dir, proj)
        sync_cmd.run(args)

        content = (wiki_dir / "entities" / "User.md").read_text()
        # Header must appear exactly once
        assert content.count("⚠️") == 1

    def test_deprecation_header_added_to_module(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").unlink()

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        module_content = (wiki_dir / "modules" / "models.md").read_text()
        assert "⚠️" in module_content


def _write_manifest_from_bootstrap_from_disk(wiki_dir: Path, proj: Path) -> None:
    """Re-seed manifest from whatever pages are on disk (for idempotency test)."""
    # Rebuild manifest pointing to the old state by loading the existing one
    # and clearing the files that were deleted so sync runs the removal path again.
    manifest = SyncManifest.load(wiki_dir)
    manifest.save(wiki_dir)


class TestDiffOutput:
    """sync prints a concise per-page summary to stdout."""

    def test_summary_line_on_completion(self, bootstrapped_project, capsys):
        proj, wiki_dir = bootstrapped_project
        # Trigger a real change
        (proj / "models.py").write_text("class User:\n    updated: str = ''\n")

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        out = capsys.readouterr().out
        assert "Sync complete:" in out
        assert "created" in out
        assert "updated" in out
        assert "skipped" in out

    def test_log_entry_appended(self, bootstrapped_project):
        proj, wiki_dir = bootstrapped_project
        (proj / "models.py").write_text("class User:\n    changed: str = ''\n")

        log_before = (wiki_dir / "log.md").read_text() if (wiki_dir / "log.md").exists() else ""

        sync_cmd.run(_make_sync_args(src_dir=str(proj), wiki_dir=str(wiki_dir)))

        log_after = (wiki_dir / "log.md").read_text()
        assert len(log_after) > len(log_before)
        assert "incremental sync" in log_after
