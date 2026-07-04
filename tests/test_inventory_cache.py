"""Tests for persistent inventory cache helpers."""

from __future__ import annotations

import json

from llm_wiki_cli.services import inventory_cache
from llm_wiki_cli.services.inventory_cache import (
    CACHE_FILENAME,
    InventoryCache,
    InventoryCacheOptions,
    build_inventory_cache_key,
    make_cache_entry,
    resolve_inventory_cache_path,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.commands.extract_cmd import get_inventory_result


def test_resolves_normal_git_dir(tmp_path):
    src = tmp_path / "project"
    src.mkdir()
    (src / ".git").mkdir()

    assert resolve_inventory_cache_path(src) == src / ".git" / CACHE_FILENAME


def test_resolves_git_worktree_file(tmp_path):
    src = tmp_path / "worktree"
    src.mkdir()
    gitdir = tmp_path / "repo" / ".git" / "worktrees" / "worktree"
    gitdir.mkdir(parents=True)
    (src / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")

    assert resolve_inventory_cache_path(src) == gitdir / CACHE_FILENAME


def test_cache_dir_flag_wins_over_env(tmp_path):
    explicit = tmp_path / "explicit"
    env_dir = tmp_path / "env"

    assert (
        resolve_inventory_cache_path(
            tmp_path,
            str(explicit),
            env={"LLM_WIKI_CACHE_DIR": str(env_dir)},
        )
        == explicit / CACHE_FILENAME
    )


def test_env_cache_dir_is_used_without_git(tmp_path):
    env_dir = tmp_path / "env-cache"

    assert (
        resolve_inventory_cache_path(
            tmp_path,
            env={"LLM_WIKI_CACHE_DIR": str(env_dir)},
        )
        == env_dir / CACHE_FILENAME
    )


def test_corrupt_cache_loads_as_empty(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cache_file = cache_dir / CACHE_FILENAME
    cache_file.write_text("{not json", encoding="utf-8")

    cache = InventoryCache(
        tmp_path, InventoryCacheOptions(enabled=True, cache_dir=str(cache_dir))
    )

    assert cache.load({"version": 1}) == {}
    assert cache.stats.status == "corrupt"
    assert cache.stats.load_error


def test_save_writes_schema_and_prunes_to_given_files(tmp_path):
    cache_dir = tmp_path / "cache"
    source = tmp_path / "app.py"
    source.write_text("class App: pass\n", encoding="utf-8")
    snapshot = build_source_snapshot(tmp_path)
    source_file = snapshot.files_by_language["python"][0]
    cache_key = build_inventory_cache_key(
        tmp_path,
        snapshot,
        deep=True,
        include_empty=False,
        extractor_registry={"python": "builtin"},
    )
    cache = InventoryCache(
        tmp_path, InventoryCacheOptions(enabled=True, cache_dir=str(cache_dir))
    )
    cache.save(
        cache_key,
        {
            "app.py": make_cache_entry(
                source_file,
                "sha256:test",
                {"language": "python", "classes": [], "functions": []},
            ),
        },
    )

    payload = json.loads((cache_dir / CACHE_FILENAME).read_text(encoding="utf-8"))
    assert payload["schema"] == "inventory-v1"
    assert sorted(payload["files"]) == ["app.py"]
    assert payload["files"]["app.py"]["hash"] == "sha256:test"


def test_save_handles_atomic_replace_oserror(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cache_file = cache_dir / CACHE_FILENAME
    original_payload = '{"files": {"old.py": {}}}\n'
    cache_file.write_text(original_payload, encoding="utf-8")
    cache = InventoryCache(
        tmp_path, InventoryCacheOptions(enabled=True, cache_dir=str(cache_dir))
    )
    assert cache.path is not None

    def fail_replace(self, target):
        raise OSError("replace denied")

    monkeypatch.setattr(type(cache.path), "replace", fail_replace)

    cache.save({"version": 1}, {"app.py": {"hash": "sha256:new"}})

    assert cache_file.read_text(encoding="utf-8") == original_payload
    assert not list(cache_dir.glob(f".{CACHE_FILENAME}.*.tmp"))
    assert cache.stats.status == "save_failed"
    assert cache.stats.saved_entries == 0
    assert "replace denied" in cache.stats.load_error


def test_cache_key_changes_for_gitignore_plugin_and_filter_inputs(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("class App: pass\n", encoding="utf-8")
    snapshot = build_source_snapshot(src)

    def key():
        return build_inventory_cache_key(
            src,
            snapshot,
            deep=True,
            include_empty=False,
            extractor_registry={"python": "builtin"},
        )

    base = key()
    (src / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
    snapshot = build_source_snapshot(src)
    assert key()["gitignore_fingerprint"] != base["gitignore_fingerprint"]

    plugin_home = tmp_path / ".llm-wiki"
    plugin_home.mkdir()
    (plugin_home / "plugins.lock.json").write_text(
        '{"plugins": {}}\n', encoding="utf-8"
    )
    assert key()["plugin_lock_fingerprint"] != base["plugin_lock_fingerprint"]

    monkeypatch.setattr(
        inventory_cache, "LANGUAGE_EXTENSIONS", {"python": (".py", ".pyw")}
    )
    assert key()["filter_fingerprint"] != base["filter_fingerprint"]

    monkeypatch.setattr(
        inventory_cache,
        "AGENT_WORKTREE_DIR_PATTERNS",
        ((".claude", "worktrees"), (".other-agent", "worktrees")),
    )
    assert key()["filter_fingerprint"] != base["filter_fingerprint"]

    monkeypatch.setattr(
        inventory_cache, "_implementation_fingerprint", lambda: "changed"
    )
    assert key()["extractor_fingerprint"] == "changed"


def test_cache_key_uses_snapshot_gitignore_fingerprint_without_rescan(
    tmp_path, monkeypatch
):
    src = tmp_path / "src"
    src.mkdir()
    (src / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
    (src / "app.py").write_text("class App: pass\n", encoding="utf-8")
    snapshot = build_source_snapshot(src)
    monkeypatch.setattr(
        inventory_cache,
        "_gitignore_fingerprint",
        lambda root: (_ for _ in ()).throw(AssertionError("should not rescan")),
    )

    cache_key = build_inventory_cache_key(
        src,
        snapshot,
        deep=True,
        include_empty=False,
        extractor_registry={"python": "builtin"},
    )

    assert cache_key["gitignore_fingerprint"] == snapshot.gitignore_fingerprint


def test_pure_warm_cache_hit_does_not_rewrite_cache(tmp_path):
    cache_dir = tmp_path / "cache"
    (tmp_path / "app.py").write_text("class App:\n    pass\n", encoding="utf-8")
    options = InventoryCacheOptions(
        enabled=True, cache_dir=str(cache_dir), stats_enabled=True
    )

    first = get_inventory_result(tmp_path, deep=True, cache_options=options)
    assert first.cache_stats is not None
    assert first.cache_stats.saved_entries == 1

    second = get_inventory_result(tmp_path, deep=True, cache_options=options)
    assert second.cache_stats is not None
    assert second.cache_stats.status == "hit"
    assert second.cache_stats.hits == 1
    assert second.cache_stats.saved_entries == 0
