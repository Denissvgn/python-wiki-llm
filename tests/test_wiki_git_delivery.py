"""Git handoff inspects complete required native artifacts without changing policy."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys

import pytest

from llm_wiki_cli.cli import main
from llm_wiki_cli.services import wiki_git_delivery as delivery
from llm_wiki_cli.services.knowledge_governance import GOVERNANCE_FILENAME
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from llm_wiki_cli.services.wiki_git_policy import (
    classify_wiki_git_policy,
    WikiGitDisposition,
)
from tests.test_snapshot_query_validation import STORAGE_FORMATS, _history_snapshot
from tests.knowledge_fixtures import one_module_two_entities_fixture


def git(root, *args, data=None):
    return subprocess.run(
        ["git", "-C", str(root), *args], input=data, capture_output=True, check=True
    ).stdout


def project(tmp_path, monkeypatch, storage_format="packed-v4-deflate"):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.email", "delivery@example.invalid")
    git(root, "config", "user.name", "Git Delivery")
    wiki = root / "wiki"
    wiki.mkdir()
    _history_snapshot(wiki, storage_format)
    for relative, content in one_module_two_entities_fixture().assets.items():
        target = wiki / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    monkeypatch.chdir(root)
    return root, wiki


def hashes(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.mark.parametrize("storage_format", STORAGE_FORMATS)
def test_every_native_format_is_git_eligible_and_stages_completely(
    tmp_path, monkeypatch, storage_format
):
    root, wiki = project(tmp_path, monkeypatch, storage_format)
    before = hashes(root)
    result = delivery.inspect_wiki_git_delivery(wiki)
    assert result["ok"] and result["delivery_state"] == "git-eligible"
    assert result["required_files"] > 3 and result["ignored_files"] == 0
    assert result["staged"]["status"] == "not-checked"
    assert hashes(root) == before
    missing = delivery.inspect_wiki_git_delivery(wiki, staged=True)
    assert not missing["ok"] and missing["staged"]["status"] == "incomplete"
    assert missing["staged"]["missing"] == result["required_files"]
    assert hashes(root) == before
    git(root, "add", "--", "wiki")
    before = hashes(root)
    staged = delivery.inspect_wiki_git_delivery(wiki, staged=True)
    assert staged["ok"] and staged["staged"]["status"] == "complete"
    assert hashes(root) == before


@pytest.mark.parametrize(
    "rule",
    (
        "*.zip\n",
        "wiki/.llm-wiki-knowledge/index-pages/\n",
        f"wiki/{GOVERNANCE_FILENAME}\n",
    ),
)
def test_mixed_native_descendants_override_the_incomplete_root_probe(
    tmp_path, monkeypatch, rule
):
    root, wiki = project(tmp_path, monkeypatch)
    (root / ".gitignore").write_text(rule)
    assert classify_wiki_git_policy(wiki).disposition is WikiGitDisposition.INCLUDED
    before = hashes(root)
    result = delivery.inspect_wiki_git_delivery(wiki)
    assert result["ok"] and result["delivery_state"] == "mixed"
    assert result["ignored_files"] > 0 and result["eligible_files"] > 0
    assert result["ignored_samples"]
    assert hashes(root) == before
    git(root, "add", "--", "wiki", ".gitignore")
    staged = delivery.inspect_wiki_git_delivery(wiki, staged=True)
    assert not staged["ok"] and staged["staged"]["missing"] > 0


def test_intentionally_local_only_wiki_remains_valid_without_git_handoff(
    tmp_path, monkeypatch
):
    root, wiki = project(tmp_path, monkeypatch)
    (root / ".gitignore").write_text("wiki/\n")
    result = delivery.inspect_wiki_git_delivery(wiki)
    assert result["ok"] and result["delivery_state"] == "local-only"
    assert result["ignored_files"] == result["required_files"]
    assert not delivery.inspect_wiki_git_delivery(wiki, staged=True)["ok"]


def test_manifest_catalog_objects_are_part_of_delivery(tmp_path, monkeypatch):
    root, wiki = project(tmp_path, monkeypatch)
    migrate_knowledge_storage(wiki, to="indexed-v6", recovery_dir=tmp_path / "recovery")
    (root / ".gitignore").write_text("wiki/.llm-wiki-manifest/objects/\n")
    result = delivery.inspect_wiki_git_delivery(wiki)
    assert result["delivery_state"] == "mixed"
    assert any(".llm-wiki-manifest/objects/" in p for p in result["ignored_samples"])


def test_staged_native_bytes_must_match_the_current_commitments(tmp_path, monkeypatch):
    root, wiki = project(tmp_path, monkeypatch)
    git(root, "add", "--", "wiki")
    relative = next(wiki.rglob("*.zip")).relative_to(root).as_posix()
    identity = (
        git(root, "hash-object", "-w", "--stdin", data=b"wrong native bytes\n")
        .decode()
        .strip()
    )
    git(root, "update-index", "--cacheinfo", "100644", identity, relative)
    result = delivery.inspect_wiki_git_delivery(wiki, staged=True)
    assert not result["ok"] and result["staged"]["mismatched"] == 1
    assert relative in result["staged"]["mismatched_samples"]


def test_markdown_git_newline_normalization_preserves_delivery(tmp_path, monkeypatch):
    root, wiki = project(tmp_path, monkeypatch)
    page = wiki / "entities/User.md"
    page.write_bytes(page.read_bytes().replace(b"\n", b"\r\n"))
    (root / ".gitattributes").write_text("*.md text eol=lf\n")
    git(root, "add", "--", "wiki", ".gitattributes")
    assert delivery.inspect_wiki_git_delivery(wiki, staged=True)["ok"]


def test_effective_global_excludes_are_honored_and_git_redirection_is_discarded(
    tmp_path, monkeypatch
):
    root, wiki = project(tmp_path, monkeypatch)
    excludes = tmp_path / "excludes"
    excludes.write_text("*.zip\n")
    config = tmp_path / "globalconfig"
    git(root, "config", "--file", str(config), "core.excludesFile", str(excludes))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "other-index"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.excludesFile")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "/dev/null")
    assert delivery.inspect_wiki_git_delivery(wiki)["delivery_state"] == "mixed"


def test_changed_index_during_delivery_is_indeterminate(tmp_path, monkeypatch):
    root, wiki = project(tmp_path, monkeypatch)
    git(root, "add", "--", "wiki")
    original = delivery._command

    def changed(repo, args, **kwargs):
        result = original(repo, args, **kwargs)
        if args == ["cat-file", "--batch"]:
            git(root, "update-index", "--force-remove", "--", "wiki/index.md")
        return result

    monkeypatch.setattr(delivery, "_command", changed)
    result = delivery.inspect_wiki_git_delivery(wiki, staged=True)
    assert not result["ok"] and result["delivery_state"] == "indeterminate"
    assert result["reason"] == "git-delivery-mutation"


def test_command_exposes_advisory_state_and_explicit_staged_gate(
    tmp_path, monkeypatch, capsys
):
    root, wiki = project(tmp_path, monkeypatch)
    (root / ".gitignore").write_text("*.zip\n")
    monkeypatch.setattr(
        sys, "argv", ["llm-wiki", "knowledge", "git-check", "--wiki-dir", "wiki"]
    )
    main()
    assert json.loads(capsys.readouterr().out)["delivery_state"] == "mixed"
    with pytest.raises(SystemExit) as caught:
        monkeypatch.setattr(
            sys,
            "argv",
            ["llm-wiki", "knowledge", "git-check", "--wiki-dir", "wiki", "--staged"],
        )
        main()
    assert caught.value.code == 1
    assert json.loads(capsys.readouterr().out)["staged"]["status"] == "incomplete"


def test_referenced_asset_is_required_but_unreferenced_cache_is_not(
    tmp_path, monkeypatch
):
    root, wiki = project(tmp_path, monkeypatch, "v1")
    cache = wiki / "unused.zip"
    cache.write_bytes(b"not part of the snapshot")
    (root / ".gitignore").write_text("unused.zip\n")
    assert delivery.inspect_wiki_git_delivery(wiki)["delivery_state"] == "git-eligible"
    asset = next(iter(one_module_two_entities_fixture().assets))
    (root / ".gitignore").write_text(f"unused.zip\nwiki/{asset}\n")
    result = delivery.inspect_wiki_git_delivery(wiki)
    assert result["delivery_state"] == "mixed"
    assert result["ignored_samples"] == [f"wiki/{asset}"]
    git(root, "add", "--", "wiki")
    staged = delivery.inspect_wiki_git_delivery(wiki, staged=True)
    assert not staged["ok"] and staged["staged"]["missing_samples"] == [f"wiki/{asset}"]
    (wiki / asset).unlink()
    assert delivery.inspect_wiki_git_delivery(wiki)["delivery_state"] == "indeterminate"


def test_new_ignore_policy_blocks_even_an_already_tracked_complete_snapshot(
    tmp_path, monkeypatch
):
    root, wiki = project(tmp_path, monkeypatch)
    git(root, "add", "--", "wiki")
    (root / ".gitignore").write_text("*.zip\n")
    result = delivery.inspect_wiki_git_delivery(wiki, staged=True)
    assert result["delivery_state"] == "mixed"
    assert result["staged"]["status"] == "complete" and not result["ok"]


def test_symlink_index_entry_cannot_deliver_a_native_object(tmp_path, monkeypatch):
    root, wiki = project(tmp_path, monkeypatch)
    git(root, "add", "--", "wiki")
    path = next(wiki.rglob("*.zip")).relative_to(root).as_posix()
    identity = (
        git(root, "hash-object", "-w", "--stdin", data=b"elsewhere").decode().strip()
    )
    git(root, "update-index", "--cacheinfo", "120000", identity, path)
    result = delivery.inspect_wiki_git_delivery(wiki, staged=True)
    assert not result["ok"] and result["staged"]["mismatched_samples"] == [path]


def test_promisor_repository_fails_closed_before_requesting_objects(
    tmp_path, monkeypatch
):
    root, wiki = project(tmp_path, monkeypatch)
    git(root, "add", "--", "wiki")
    git(root, "config", "remote.origin.promisor", "true")

    def forbidden(*args, **kwargs):
        pytest.fail("partial repository must never request missing Git objects")

    monkeypatch.setattr(delivery, "_blobs", forbidden)
    before = hashes(root)
    result = delivery.inspect_wiki_git_delivery(wiki, staged=True)
    assert result["delivery_state"] == "indeterminate" and not result["ok"]
    assert hashes(root) == before


def test_included_promisor_configuration_cannot_trigger_a_lazy_fetch(
    tmp_path, monkeypatch
):
    root, wiki = project(tmp_path, monkeypatch)
    git(root, "add", "--", "wiki")
    included = tmp_path / "partial-config"
    included.write_text('[remote "origin"]\n promisor = true\n')
    git(root, "config", "include.path", str(included))

    def forbidden(*args, **kwargs):
        pytest.fail(
            "included partial-clone configuration must be checked before object access"
        )

    monkeypatch.setattr(delivery, "_blobs", forbidden)
    result = delivery.inspect_wiki_git_delivery(wiki, staged=True)
    assert result["delivery_state"] == "indeterminate"
    assert result["staged"]["status"] == "indeterminate" and not result["ok"]


def test_changed_ignore_policy_during_inspection_is_indeterminate(
    tmp_path, monkeypatch
):
    root, wiki = project(tmp_path, monkeypatch)
    original = delivery._ignored

    def changed(*args):
        result = original(*args)
        (root / ".gitignore").write_text("*.zip\n")
        return result

    monkeypatch.setattr(delivery, "_ignored", changed)
    result = delivery.inspect_wiki_git_delivery(wiki)
    assert result["delivery_state"] == "indeterminate" and not result["ok"]
    assert result["reason"] == "git-delivery-mutation"


def test_missing_git_and_inspection_limits_fail_closed(tmp_path, monkeypatch):
    root, wiki = project(tmp_path, monkeypatch)
    monkeypatch.setattr(delivery, "MAX_DELIVERY_FILES", 1)
    assert delivery.inspect_wiki_git_delivery(wiki)["reason"] == "git-delivery-limit"
    (root / ".git").rename(tmp_path / "saved-git")
    result = delivery.inspect_wiki_git_delivery(wiki, staged=True)
    assert result["delivery_state"] == "indeterminate" and not result["ok"]
    assert result["staged"]["status"] == "indeterminate"


def test_linked_worktree_with_spaces_delivers_its_own_index(tmp_path, monkeypatch):
    root, wiki = project(tmp_path, monkeypatch)
    git(root, "add", "--", "wiki")
    git(root, "commit", "-qm", "Native snapshot")
    linked = tmp_path / "linked worktree"
    git(root, "worktree", "add", "--detach", str(linked), "HEAD")
    monkeypatch.chdir(linked)
    assert delivery.inspect_wiki_git_delivery(linked / "wiki", staged=True)["ok"]
