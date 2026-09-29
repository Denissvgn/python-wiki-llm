"""Explicit acceptance cases for known sync defects, pending their fixes.

Run with .venv/bin/pytest tests/sync_page_transition_acceptance.py --runxfail.
The filename keeps known failures out of default collection and the release
skip contract. Promote each case to default collection when fixing its defect.
Strict xfail markers accept only the specific missing-page or prose mismatch;
other assertions, setup failures, and unexpected passes must remain failures.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from llm_wiki_cli.services.io import read_md
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.test_sync_page_transitions import (
    _MissingManagedPage,
    _UnexpectedEntityDescription,
    _assert_consistent,
    _assert_entity_page,
    _assert_module_page,
    _assert_page_mapping,
    _author_description,
    _bootstrap_project,
    _check_added_twin,
    _check_private_twin,
    _draft_source,
    _require_page,
    _sync,
)


@pytest.mark.xfail(
    strict=True,
    raises=_UnexpectedEntityDescription,
    reason="Existing-module addition gives the original owner's prose to its new twin",
)
def test_existing_module_twin_preserves_original_page_owner(tmp_path, monkeypatch):
    _check_added_twin(tmp_path, monkeypatch, existing_module=True)


@pytest.mark.xfail(
    strict=True,
    raises=_MissingManagedPage,
    reason="A public rename consumes the private twin's newly written page",
)
def test_three_way_private_twin_preserves_all_page_owners(tmp_path, monkeypatch):
    _check_private_twin(tmp_path, monkeypatch, second_public=True)


@pytest.mark.xfail(
    strict=True,
    raises=_MissingManagedPage,
    reason="Sync does not recreate missing managed pages when source content is unchanged",
)
@pytest.mark.parametrize("page_kind", ["entity", "module"])
@pytest.mark.parametrize("mode", ["ordinary", "force-rebuild-cache", "mtime-only"])
def test_sync_restores_missing_page_without_source_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, page_kind: str, mode: str
) -> None:
    original_doc = "A mail draft."
    keeper_doc = "An unrelated keeper."
    keeper_authored = "HAND-WRITTEN: preserve this unrelated keeper."
    project, wiki_dir = _bootstrap_project(
        tmp_path,
        monkeypatch,
        {
            "model.py": _draft_source(original_doc),
            "keeper.py": _draft_source(keeper_doc, name="Keeper"),
        },
    )
    _author_description(wiki_dir / "entities/Keeper.md", keeper_doc, keeper_authored)
    # Establish a healthy warm sync before deletion, independent of either rename.
    _sync(wiki_dir)
    _assert_consistent(wiki_dir)
    source_path = project / "pkg/model.py"
    source_bytes = {
        path: path.read_bytes() for path in (project / "pkg").glob("*.py")
    }
    source_hash = SyncManifest.load(wiki_dir).sources["pkg/model.py"]["hash"]
    relative_path = "entities/Draft.md" if page_kind == "entity" else "modules/model.md"
    _assert_page_mapping(
        wiki_dir,
        relative_path,
        "pkg/model.py",
        entity_name="Draft" if page_kind == "entity" else None,
    )
    target = wiki_dir / relative_path
    assert target.is_file()
    expected_content = read_md(target)
    target.unlink()
    surviving_pages = {
        path: path.read_bytes()
        for directory in ("entities", "modules")
        for path in (wiki_dir / directory).glob("*.md")
    }
    if mode == "mtime-only":
        before = source_path.stat()
        os.utime(
            source_path,
            ns=(before.st_atime_ns, before.st_mtime_ns + 2_000_000_000),
        )
        assert source_path.stat().st_mtime_ns != before.st_mtime_ns

    options = (
        {"force": True, "rebuild_cache": True}
        if mode == "force-rebuild-cache"
        else {}
    )
    _sync(wiki_dir, **options)

    # These ordinary assertions must not be masked by the missing-page marker.
    for path, content in source_bytes.items():
        assert path.read_bytes() == content, f"Source changed: {path.name}"
    assert SyncManifest.load(wiki_dir).sources["pkg/model.py"]["hash"] == source_hash
    for path, content in surviving_pages.items():
        assert path.read_bytes() == content, f"Surviving page changed: {path.name}"
    _assert_entity_page(
        wiki_dir, "Keeper", "pkg/keeper.py", keeper_authored, entity_name="Keeper"
    )
    assert _require_page(wiki_dir, relative_path) == expected_content
    _assert_entity_page(wiki_dir, "Draft", "pkg/model.py", original_doc)
    _assert_module_page(wiki_dir, "model", "pkg/model.py")
    _assert_consistent(wiki_dir)
