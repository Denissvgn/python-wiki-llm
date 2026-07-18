"""Filesystem policy tests for external documentation workspaces."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from llm_wiki_cli.services.documentation_policy import (
    DocumentationPolicyError,
    compare_tree_baseline,
    resolve_documentation_policy,
    source_tree_baseline,
)


def _write_source(root: Path) -> None:
    root.mkdir(parents=True)
    (root / "module.py").write_text("def value():\n    return 1\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("untrusted instructions\n", encoding="utf-8")
    plugin = root / ".llm-wiki" / "plugins" / "hostile"
    plugin.mkdir(parents=True)
    (plugin / "llm-wiki-plugin.json").write_text("{}\n", encoding="utf-8")
    (plugin / "plugin.py").write_text(
        "raise RuntimeError('must never execute')\n", encoding="utf-8"
    )


def test_policy_supports_no_git_source_and_unicode_paths(tmp_path):
    source = tmp_path / "source with spaces Ω"
    workspace = tmp_path / "documentation output Ω"
    _write_source(source)

    policy = resolve_documentation_policy(workspace, source_root=source)
    baseline = source_tree_baseline(source)

    assert policy.source_root == source.resolve()
    assert baseline.file_count == 4
    assert baseline.tree_hash.startswith("sha256:")
    assert ".git" in baseline.excluded_directories
    assert compare_tree_baseline(baseline, source).ok


@pytest.mark.parametrize("workspace_rel", [".", "docs", "nested/workspace"])
def test_policy_rejects_workspace_inside_source(tmp_path, workspace_rel):
    source = tmp_path / "source"
    _write_source(source)
    workspace = source / workspace_rel

    with pytest.raises(DocumentationPolicyError, match="must not overlap"):
        resolve_documentation_policy(workspace, source_root=source)


def test_policy_rejects_source_inside_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    source = workspace / "source"
    _write_source(source)

    with pytest.raises(DocumentationPolicyError, match="must not overlap"):
        resolve_documentation_policy(workspace, source_root=source)


def test_policy_forbidden_roots_override_write_allowlist(tmp_path):
    source = tmp_path / "source"
    workspace = tmp_path / "workspace"
    cache = tmp_path / "cache"
    _write_source(source)
    policy = resolve_documentation_policy(
        workspace,
        source_root=source,
        helper_cache_root=cache,
    )

    assert policy.assert_write_allowed(workspace / "wiki" / "index.md")
    assert policy.assert_write_allowed(cache / "helper")
    with pytest.raises(DocumentationPolicyError, match="read-only evidence root"):
        policy.assert_write_allowed(source / "module.py")
    with pytest.raises(DocumentationPolicyError, match="outside"):
        policy.assert_write_allowed(tmp_path / "other" / "file.txt")


def test_tree_comparison_reports_added_removed_and_changed(tmp_path):
    source = tmp_path / "source"
    _write_source(source)
    (source / "removed.txt").write_text("remove\n", encoding="utf-8")
    baseline = source_tree_baseline(source)

    (source / "module.py").write_text("changed\n", encoding="utf-8")
    (source / "removed.txt").unlink()
    (source / "added.txt").write_text("added\n", encoding="utf-8")
    difference = compare_tree_baseline(baseline, source)

    assert difference.ok is False
    assert difference.added == ("added.txt",)
    assert difference.removed == ("removed.txt",)
    assert difference.changed == ("module.py",)


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_tree_baseline_rejects_symlinked_source_content(tmp_path):
    source = tmp_path / "source"
    outside = tmp_path / "outside.txt"
    _write_source(source)
    outside.write_text("outside\n", encoding="utf-8")
    try:
        (source / "escape.txt").symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable for this account")

    with pytest.raises(DocumentationPolicyError, match="Symlinked content"):
        source_tree_baseline(source)


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_tree_baseline_rejects_symlinked_source_root(tmp_path):
    real_source = tmp_path / "real-source"
    source_link = tmp_path / "source-link"
    _write_source(real_source)
    try:
        source_link.symlink_to(real_source, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlink creation is unavailable for this account")

    with pytest.raises(DocumentationPolicyError, match="Symlinked source"):
        source_tree_baseline(source_link)


def test_tree_baseline_rejects_file_replaced_between_inspection_and_open(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    _write_source(source)
    target = source / "module.py"
    replacement = source / "replacement.tmp"
    replacement.write_text("replacement\n", encoding="utf-8")
    real_open = os.open
    swapped = False

    def swap_before_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if Path(path) == target and not swapped:
            swapped = True
            target.replace(source / "module.original")
            replacement.replace(target)
        if dir_fd is None:
            return real_open(path, flags, mode)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", swap_before_open)

    with pytest.raises(DocumentationPolicyError, match="changed identity"):
        source_tree_baseline(source)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction semantics only")
def test_tree_baseline_rejects_windows_junction(tmp_path):
    source = tmp_path / "source"
    junction_target = tmp_path / "junction-target"
    _write_source(source)
    junction_target.mkdir()
    (junction_target / "outside.txt").write_text("outside\n", encoding="utf-8")
    junction = source / "junction"
    completed = subprocess.run(
        [
            "cmd.exe",
            "/d",
            "/c",
            "mklink",
            "/J",
            str(junction),
            str(junction_target),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        pytest.skip(f"junction creation is unavailable: {completed.stderr.strip()}")

    with pytest.raises(DocumentationPolicyError, match="reparse-point"):
        source_tree_baseline(source)


def test_live_service_requires_explicit_safe_observation_policy(tmp_path):
    workspace = tmp_path / "workspace"
    capture = tmp_path / "capture"

    with pytest.raises(DocumentationPolicyError, match="must not contain"):
        resolve_documentation_policy(
            workspace,
            live_service_url="https://user:secret@example.test/?token=secret",
        )
    with pytest.raises(DocumentationPolicyError, match="capture root"):
        resolve_documentation_policy(
            workspace,
            live_service_url="https://example.test/demo",
            live_service_access_mode="anonymous",
            live_service_observation_allowed=True,
        )

    policy = resolve_documentation_policy(
        workspace,
        capture_root=capture,
        live_service_url="https://example.test/demo",
        live_service_access_mode="anonymous",
        live_service_observation_allowed=True,
    )
    portable = policy.to_portable_dict()
    assert portable["live_service"]["observation_allowed"] is True
    assert portable["live_service"]["secret_material_persisted"] is False
    assert "https://" not in str(portable)
