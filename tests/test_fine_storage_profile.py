"""The fine storage profile keeps a sync's writes close to what really changed."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli import cli
from llm_wiki_engine import knowledge_packs as packs
from llm_wiki_engine.knowledge_storage import KnowledgeStorageError
from llm_wiki_engine.knowledge_storage_lifecycle import migrate_knowledge_storage

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not available")

WIKI = "docs/llm_wiki"
MODULE = '''class {name}Service:
    """Serve {name} requests."""

    def run(self, value: int) -> int:
        return value + 1
'''


@pytest.fixture(autouse=True)
def git_environment(monkeypatch, tmp_path):
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(tmp_path / "cache"))


def _run(monkeypatch, root: Path, *arguments: str) -> int:
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["llm-wiki", *arguments])
    try:
        cli.main()
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    return 0


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(root), *arguments], check=True, capture_output=True)


def _commit(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "--quiet", "-m", message)


def _add_module(root: Path, name: str) -> None:
    (root / "app" / f"{name.lower()}.py").write_text(
        MODULE.format(name=name), encoding="utf-8", newline="\n"
    )


def _repository(monkeypatch, tmp_path: Path, knowledge_format: str) -> Path:
    root = tmp_path / knowledge_format
    (root / "app").mkdir(parents=True)
    _git(root, "init", "--quiet", "-b", "main")
    _git(root, "config", "user.email", "fine-profile@example.invalid")
    _git(root, "config", "user.name", "Fine Profile Tests")
    _git(root, "config", "core.longpaths", "true")
    (root / "app" / "__init__.py").write_text("", encoding="utf-8")
    for name in ("Alpha", "Beta", "Gamma", "Delta", "Omega"):
        _add_module(root, name)
    _commit(root, "source")
    assert _run(monkeypatch, root, "init", "--agent", "generic", "--no-skills", "--no-quality-hints") == 0
    assert _run(
        monkeypatch, root, "bootstrap", "--src-dir", ".", "--wiki-dir", WIKI,
        "--knowledge-format", knowledge_format,
    ) == 0
    _commit(root, "wiki")
    return root


def _root(root: Path) -> dict:
    return json.loads((root / WIKI / ".llm-wiki-knowledge.json").read_text(encoding="utf-8"))


def _link_records(root: Path) -> list[dict]:
    """Return every stored link target, read straight from the packs."""
    found = []
    for pack in (root / WIKI / ".llm-wiki-knowledge" / "packs").rglob("*.zip"):
        with zipfile.ZipFile(pack) as archive:
            for name in archive.namelist():
                if not name.startswith("values/"):
                    continue
                node = json.loads(archive.read(name))
                for record in node.get("records", ()):
                    value = record.get("value")
                    if isinstance(value, dict) and "normalized_target" in value:
                        found.append(record)
    return found


def test_fine_profile_is_recorded_and_reported_as_the_packed_v4_family(monkeypatch, tmp_path):
    root = _repository(monkeypatch, tmp_path, "packed-v4-fine-deflate")

    stored = _root(root)

    assert stored["schema_version"] == packs.LOCAL_PACKED_SCHEMA
    assert stored["packing"]["profile"] == packs.FINE_PACK_PROFILE
    assert packs.packed_format(stored) == "packed-v4-fine-deflate"
    assert packs.packed_family(stored) == "packed-v4"


def test_fine_links_are_located_within_their_line(monkeypatch, tmp_path):
    root = _repository(monkeypatch, tmp_path, "packed-v4-fine-deflate")

    links = _link_records(root)

    assert links
    for record in links:
        location = record["value"]["location"]
        assert location["extensions"] == {"llm-wiki/location-basis": "line"}
        assert location["end"] - location["start"] < 400


def test_standard_profile_keeps_page_offsets(monkeypatch, tmp_path):
    root = _repository(monkeypatch, tmp_path, "packed-v4-deflate")

    assert _root(root)["packing"]["profile"] == packs.LOCAL_PACK_PROFILE
    assert all("extensions" not in record["value"]["location"] for record in _link_records(root))


def test_a_new_page_leaves_other_fine_link_records_unchanged(monkeypatch, tmp_path):
    results = {}
    for knowledge_format in ("packed-v4-deflate", "packed-v4-fine-deflate"):
        root = _repository(monkeypatch, tmp_path, knowledge_format)
        before = {record["id"]: record["value"] for record in _link_records(root)}
        # "Aardvark" sorts first, so its index entry moves every later link.
        _add_module(root, "Aardvark")
        _commit(root, "new module")
        assert _run(
            monkeypatch, root, "sync", "--prune-storage", "--verify",
            "--src-dir", ".", "--wiki-dir", WIKI,
        ) == 0
        after = {record["id"] for record in _link_records(root)}
        results[knowledge_format] = [value for identity, value in before.items() if identity not in after]

    # Diagram nodes are numbered in order, so their labels really change.
    renumbered = re.compile(r"n\d+")
    assert all(renumbered.fullmatch(value["label"]) for value in results["packed-v4-fine-deflate"])
    moved = [value for value in results["packed-v4-deflate"] if not renumbered.fullmatch(value["label"])]
    assert moved


def test_fine_profile_survives_later_syncs_and_strict_checks(monkeypatch, capsys, tmp_path):
    root = _repository(monkeypatch, tmp_path, "packed-v4-fine-deflate")
    _add_module(root, "Sigma")
    _commit(root, "new module")

    assert _run(monkeypatch, root, "sync", "--verify", "--src-dir", ".", "--wiki-dir", WIKI) == 0
    _commit(root, "refresh")
    capsys.readouterr()
    assert _run(monkeypatch, root, "sync", "--dry-run", "--src-dir", ".", "--wiki-dir", WIKI) == 0
    preview = capsys.readouterr().out

    assert _root(root)["packing"]["profile"] == packs.FINE_PACK_PROFILE
    assert "Knowledge index: unchanged" in preview
    assert _run(monkeypatch, root, "ci-check", "--no-report", "--src-dir", ".", "--wiki-dir", WIKI) == 0
    assert _run(monkeypatch, root, "knowledge", "storage-check", "--wiki-dir", WIKI, "--full") == 0


def test_a_sync_adopts_and_leaves_the_fine_profile(monkeypatch, tmp_path):
    root = _repository(monkeypatch, tmp_path, "packed-v4-deflate")

    assert _run(
        monkeypatch, root, "sync", "--prune-storage", "--verify", "--src-dir", ".", "--wiki-dir", WIKI,
        "--knowledge-format", "packed-v4-fine-deflate",
    ) == 0
    assert _root(root)["packing"]["profile"] == packs.FINE_PACK_PROFILE
    assert all("extensions" in record["value"]["location"] for record in _link_records(root))

    assert _run(
        monkeypatch, root, "sync", "--prune-storage", "--verify", "--src-dir", ".", "--wiki-dir", WIKI,
        "--knowledge-format", "packed-v4-deflate",
    ) == 0
    assert _root(root)["packing"]["profile"] == packs.LOCAL_PACK_PROFILE
    assert all("extensions" not in record["value"]["location"] for record in _link_records(root))


def test_storage_migration_refuses_the_fine_profile_in_both_directions(monkeypatch, tmp_path):
    standard = _repository(monkeypatch, tmp_path, "packed-v4-deflate")
    with pytest.raises(KnowledgeStorageError, match="writing sync"):
        migrate_knowledge_storage(standard / WIKI, dry_run=True, to="packed-v4-fine-deflate")

    fine = _repository(monkeypatch, tmp_path, "packed-v4-fine-deflate")
    with pytest.raises(KnowledgeStorageError, match="writing sync"):
        migrate_knowledge_storage(fine / WIKI, dry_run=True, to="packed-v4-deflate")


def test_a_reader_without_the_fine_profile_refuses_the_root(monkeypatch, tmp_path):
    root = _repository(monkeypatch, tmp_path, "packed-v4-fine-deflate")
    raw = (root / WIKI / ".llm-wiki-knowledge.json").read_bytes()
    monkeypatch.setattr(packs, "LOCAL_PACK_PROFILES", frozenset({packs.LOCAL_PACK_PROFILE}))

    with pytest.raises(KnowledgeStorageError) as refused:
        packs.parse_packed_root(raw)

    assert refused.value.code == "unsupported-schema-version"


def _fine_plan(payload):
    # Small logical objects give the locator several pages and packs to route.
    logical = packs.build_knowledge_store(payload, target_bytes=512)
    return packs._pack_logical(logical, "deflate", None, None, packs.FINE_PACK_PROFILE)


def _fixture_payload() -> dict:
    from tests.knowledge_fixtures import one_module_two_entities_fixture

    return json.loads(one_module_two_entities_fixture().knowledge_bytes)


def _locator_rows(plan) -> dict:
    reader = packs.open_knowledge_store(plan.root_bytes, lambda path, _: plan.objects[path])
    assert isinstance(reader, packs.PackedKnowledgeStoreReader)
    reader.materialize()
    rows = {}
    for node in reader._indexes.values():
        rows.update(node.get("slots", {}))
    return rows


def test_fine_locator_names_members_and_reads_ranges_from_the_pack(monkeypatch):
    monkeypatch.setattr(packs, "FINE_PACK_TARGET_BYTES", 2_048)
    payload = _fixture_payload()
    plan = _fine_plan(payload)

    reader = packs.open_knowledge_store(plan.root_bytes, lambda path, _: plan.objects[path])
    assert reader.materialize() == payload
    rows = _locator_rows(plan)
    assert len(rows) == json.loads(plan.root_bytes)["packing"]["objects"]
    assert all(len(value) == 2 and packs._MEMBER.fullmatch(value[1]) for value in rows.values())

    whole_files = []

    def read_file(path, _size):
        whole_files.append(path)
        return plan.objects[path]

    ranged = packs.open_knowledge_store(
        plan.root_bytes, read_file,
        read_range=lambda path, offset, count, _size: plan.objects[path][offset:offset + count],
    )
    assert ranged.select(["source:src/accounts.py"]).to_payload()["records"]
    assert not any(packs.PACK_NAME.fullmatch(path) for path in whole_files)


def test_fine_locator_is_untouched_by_a_content_change(monkeypatch):
    monkeypatch.setattr(packs, "FINE_PACK_TARGET_BYTES", 2_048)
    payload = _fixture_payload()
    before = _fine_plan(payload)
    changed = json.loads(json.dumps(payload))
    # Same record identity and size, different stored bytes.
    changed["concepts"][0]["facets"]["semantics"]["page_hash"] = "sha256:" + "5" * 64
    after = _fine_plan(changed)

    first, second = json.loads(before.root_bytes)["packing"], json.loads(after.root_bytes)["packing"]

    assert first["pack_catalog"] != second["pack_catalog"]
    assert first["catalog"] == second["catalog"]
    assert _locator_rows(before) == _locator_rows(after)


def test_each_fine_locator_leaf_has_its_own_container(monkeypatch):
    monkeypatch.setattr(packs, "FINE_INDEX_ROWS", 4)
    plan = _fine_plan(_fixture_payload())

    leaves = 0
    for path, raw in plan.objects.items():
        if not packs.INDEX_PAGE_NAME.fullmatch(path):
            continue
        assert packs.inspect_index_pages(raw, path)["pages"] >= 1
        kinds = [json.loads(line)["kind"] for line in raw.splitlines()]
        if "slots" in kinds:
            assert kinds == ["slots"]
            leaves += 1
    assert leaves > 1


def test_a_fine_locator_that_names_the_wrong_member_is_rejected():
    plan = _fine_plan(_fixture_payload())
    objects = dict(plan.objects)
    root = json.loads(plan.root_bytes)
    descriptor = root["packing"]["catalog"]
    path = packs.index_page_path(descriptor["extent"]["container"])
    node = json.loads(objects[path])
    assert node["kind"] == "slots"
    first, second = sorted(node["slots"])[:2]
    node["slots"][first], node["slots"][second] = node["slots"][second], node["slots"][first]
    raw = packs.canonical_bytes(node)
    del objects[path]
    container = packs.digest(raw)
    objects[packs.index_page_path(container)] = raw
    root["packing"]["catalog"] = {**descriptor, "hash": container, "bytes": len(raw),
                                  "extent": {"container": container, "offset": 0, "file_bytes": len(raw)}}

    reader = packs.open_knowledge_store(packs.canonical_bytes(root), lambda name, _: objects[name])
    with pytest.raises(KnowledgeStorageError):
        reader.materialize()


def test_selected_impact_read_works_on_a_fine_wiki(monkeypatch, tmp_path, capsys):
    from llm_wiki_cli import api

    root = _repository(monkeypatch, tmp_path, "packed-v4-fine-deflate")
    monkeypatch.chdir(root)
    (root / "empty").mkdir()
    capsys.readouterr()

    def impact(**options) -> Any:
        return api.query_documentation(
            {"operation": "impact", "paths": ["app/alpha.py", "app/missing.py"], "limit": 100, **options},
            src_dir="empty", wiki_dir=WIKI,
        )

    selected, full = impact(read="selected"), impact()

    assert selected["query"]["read"] == "selected"
    assert selected["concepts"]
    assert [c["locator"] for c in selected["concepts"]] == [c["locator"] for c in full["concepts"]]
    for name in ("pages", "relationships", "impacted_paths", "found"):
        assert selected[name] == full[name], name
