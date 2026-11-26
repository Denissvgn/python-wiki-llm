"""The storage usage report lists tool-owned space and reclaims only what is asked."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from llm_wiki_engine.knowledge_storage import KnowledgeStorageError
from llm_wiki_cli.services import storage_usage as usage

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not available")


@pytest.fixture
def wiki(monkeypatch, tmp_path) -> Path:
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path / "tmp"))
    (tmp_path / "tmp").mkdir()
    root = tmp_path / "repo"
    wiki_dir = root / "docs" / "llm_wiki"
    (wiki_dir / ".llm-wiki-knowledge" / "packs").mkdir(parents=True)
    (wiki_dir / ".llm-wiki-knowledge" / "packs" / "a.zip").write_bytes(b"x" * 10)
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    git_dir = root / ".git"
    (git_dir / "llm-wiki-inventory-cache.json").write_bytes(b"c" * 7)
    (git_dir / "llm-wiki-sync-analysis.json.objects").mkdir()
    (git_dir / "llm-wiki-sync-analysis.json.objects" / "o").write_bytes(b"o" * 5)
    (git_dir / "llm-wiki-extractors").mkdir()
    (git_dir / "llm-wiki-extractors" / "helper.js").write_bytes(b"h" * 3)
    (git_dir / "maintenance-preimages" / ".objects").mkdir(parents=True)
    (git_dir / "maintenance-preimages" / ".objects" / "b.blob").write_bytes(b"m" * 11)
    for name, age_days in (("old", 30), ("new", 0)):
        run = git_dir / "llm-wiki-storage-recovery" / "prune" / name
        run.mkdir(parents=True)
        (run / "copy.bin").write_bytes(b"r" * 4)
        stamp = run.stat().st_mtime - age_days * 86_400
        os.utime(run, (stamp, stamp))
    return wiki_dir


def _upgrade_run(wiki: Path, suffix: str, age_days: int) -> Path:
    identity = hashlib.sha256(str(wiki.resolve()).encode()).hexdigest()[:20]
    run = Path(tempfile.gettempdir()).resolve() / "llm-wiki-upgrade-recovery" / f"{identity}-{suffix}"
    run.mkdir(parents=True)
    (run / "root.json").write_bytes(b"u" * 6)
    stamp = run.stat().st_mtime - age_days * 86_400
    os.utime(run, (stamp, stamp))
    return run


def test_report_lists_each_class_and_changes_nothing(wiki):
    _upgrade_run(wiki, "aaa", 30)

    report = usage.storage_usage(wiki)

    assert report["schema_version"] == usage.SCHEMA
    assert {name: row["bytes"] for name, row in report["totals"].items()} == {
        "caches": 12, "helpers": 3, "maintenance-recovery": 11,
        "storage-recovery": 8, "upgrade-recovery": 6, "wiki-store": 10,
    }
    assert report["total_bytes"] == 50
    assert report["reclaim"]["applied"] is False
    assert report["reclaim"]["candidates"] == []
    assert usage.storage_usage(wiki)["total_bytes"] == 50


def test_reclaim_is_a_preview_until_applied(wiki):
    preview = usage.storage_usage(wiki, reclaim=["caches"])

    assert preview["reclaim"]["candidate_bytes"] == 12
    assert preview["reclaim"]["removed"] == []
    assert usage.storage_usage(wiki)["totals"]["caches"]["bytes"] == 12


def test_applied_reclaim_removes_only_the_requested_class(wiki):
    applied = usage.storage_usage(wiki, reclaim=["caches"], apply=True)

    assert applied["reclaim"]["removed_bytes"] == 12
    after = usage.storage_usage(wiki)["totals"]
    assert "caches" not in after
    assert after["helpers"]["bytes"] == 3
    assert after["maintenance-recovery"]["bytes"] == 11
    assert after["wiki-store"]["bytes"] == 10


def test_recovery_classes_keep_recent_entries(wiki):
    old_run = _upgrade_run(wiki, "old", 30)
    new_run = _upgrade_run(wiki, "new", 0)

    applied = usage.storage_usage(
        wiki, reclaim=["storage-recovery", "upgrade-recovery"], apply=True
    )

    assert applied["reclaim"]["removed_bytes"] == 10
    git_dir = wiki.parents[1] / ".git"
    assert not (git_dir / "llm-wiki-storage-recovery" / "prune" / "old").exists()
    assert (git_dir / "llm-wiki-storage-recovery" / "prune" / "new" / "copy.bin").exists()
    assert not old_run.exists()
    assert new_run.exists()


def test_upgrade_copies_of_another_wiki_are_not_listed(wiki, tmp_path):
    other = Path(tempfile.gettempdir()).resolve() / "llm-wiki-upgrade-recovery" / "0123456789abcdef0123-x"
    other.mkdir(parents=True)
    (other / "root.json").write_bytes(b"z" * 9)

    report = usage.storage_usage(wiki, reclaim=["upgrade-recovery"], older_than_days=0, apply=True)

    assert "upgrade-recovery" not in report["totals"]
    assert (other / "root.json").exists()


@pytest.mark.parametrize(
    "options",
    [
        {"reclaim": ["wiki-store"]},
        {"reclaim": ["maintenance-recovery"]},
        {"apply": True},
        {"older_than_days": -1},
    ],
)
def test_protected_classes_and_bad_options_are_refused(wiki, options):
    with pytest.raises(KnowledgeStorageError):
        usage.storage_usage(wiki, **options)
    assert usage.storage_usage(wiki)["totals"]["wiki-store"]["bytes"] == 10
