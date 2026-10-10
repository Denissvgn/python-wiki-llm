"""Operational mutation locks remain safe inputs without content reads."""

from pathlib import Path

import pytest

from llm_wiki_cli.services import context_packet
from llm_wiki_cli.services.knowledge_governance import governance_lock


@pytest.mark.parametrize("git_inside", [False, True])
def test_owned_mutation_locks_are_not_read_and_other_files_remain_anchored(
    tmp_path, monkeypatch, git_inside
):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    lock_root = wiki
    if git_inside:
        lock_root = wiki / ".git"
        lock_root.mkdir()
    nested = wiki / "nested"
    nested.mkdir()
    ordinary = nested / "llm-wiki-storage.lock"
    ordinary.write_bytes(b"ordinary wiki content\n")
    page = wiki / "guide.md"
    page.write_bytes(b"# Guide\n")
    locks = {lock_root / "llm-wiki-storage.lock", lock_root / "llm-wiki-governance.lock"}
    original = Path.open

    def no_lock_read(path, mode="r", *args, **kwargs):
        if path in locks and "r" in mode:
            pytest.fail("held Windows mutation lock cannot be read as wiki content")
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", no_lock_read)
    with governance_lock(wiki), governance_lock(wiki, _lock_filename="llm-wiki-storage.lock"):
        integrity = {}
        anchor = context_packet._wiki_anchor(wiki, reject_all_symlinks=True, integrity_out=integrity)
        assert all(str(path) in integrity for path in locks)
        context_packet._assert_wiki_unchanged(wiki, anchor, expected_integrity=integrity)
        ordinary.write_bytes(b"changed nested content\n")
        with pytest.raises(context_packet.ContextPacketSourceMutationError):
            context_packet._assert_wiki_unchanged(wiki, anchor)
        ordinary.write_bytes(b"ordinary wiki content\n")
        page.write_bytes(b"# Changed guide\n")
        with pytest.raises(context_packet.ContextPacketSourceMutationError):
            context_packet._assert_wiki_unchanged(wiki, anchor)


@pytest.mark.parametrize("unsafe", ["directory", "symlink", "hardlink"])
def test_operational_lock_exemption_rejects_unsafe_entries(tmp_path, unsafe):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    lock = wiki / "llm-wiki-storage.lock"
    target = tmp_path / "target"
    target.write_bytes(b"outside content")
    if unsafe == "directory":
        lock.mkdir()
    elif unsafe == "symlink":
        try:
            lock.symlink_to(target)
        except OSError as error:
            pytest.skip(f"symlink creation unavailable: {error}")
    else:
        lock.hardlink_to(target)
    with pytest.raises(context_packet.ContextPacketPathPolicyError):
        context_packet._wiki_anchor(wiki)


def test_lock_name_is_not_exempt_when_actual_locks_live_in_ancestor_git(tmp_path):
    (tmp_path / ".git").mkdir()
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    ordinary = wiki / "llm-wiki-storage.lock"
    ordinary.write_bytes(b"wiki owned content")
    anchor = context_packet._wiki_anchor(wiki)
    ordinary.write_bytes(b"changed wiki owned content")
    with pytest.raises(context_packet.ContextPacketSourceMutationError):
        context_packet._assert_wiki_unchanged(wiki, anchor)


@pytest.mark.parametrize("change", ["remove", "same-bytes-replacement"])
def test_operational_lock_presence_and_private_identity_remain_guarded(tmp_path, change):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    lock = wiki / "llm-wiki-storage.lock"
    lock.write_bytes(b"\0")
    integrity = {}
    anchor = context_packet._wiki_anchor(wiki, integrity_out=integrity)
    if change == "remove":
        lock.unlink()
    else:
        replacement = wiki / "replacement"
        replacement.write_bytes(lock.read_bytes())
        replacement.replace(lock)
    with pytest.raises(context_packet.ContextPacketSourceMutationError):
        context_packet._assert_wiki_unchanged(wiki, anchor, expected_integrity=integrity)
