"""Independent receiving controls for explicit static-source discovery."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import sys
from typing import Any, Literal

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import search_service, search_source
from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError
from llm_wiki_cli.services.knowledge_storage_io import StorageReadSession
from llm_wiki_cli.services.mcp_server import McpWikiError, McpWikiService
from llm_wiki_cli.services.search_lexical import rank_pages as rank_candidate
from llm_wiki_cli.services.search_rank import rank_pages as rank_legacy
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME, SyncManifest


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _tree(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file() and not path.is_symlink()}


@pytest.fixture
def owned_wiki(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.chdir(tmp_path)
    source = root / "selected" / "owner.py"
    source.parent.mkdir()
    source.write_text(
        "from pathlib import Path\n"
        f"Path({str(root / 'target-execution-tripwire')!r}).write_text('executed')\n"
        "class OwnedBoundary:\n"
        "    def inspect(self):\n"
        "        raise ValueError('cobalt retention sentinel')\n",
        encoding="utf-8",
    )
    (root / "outside.py").write_text("# unselected hidden sentinel\n", encoding="utf-8")
    (source.parent / "ignored.py").write_text("# ignored hidden sentinel\n", encoding="utf-8")
    (root / ".gitignore").write_text("selected/ignored.py\n", encoding="utf-8")
    profile = root / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir()
    profile.write_text(json.dumps({"schema_version": "llm-wiki-source-selection/v1",
                                   "include": ["selected"], "exclude": []}) + "\n", encoding="utf-8")
    wiki = tmp_path / "wiki"
    api.bootstrap_wiki(str(root), str(wiki), skip_workflows=True, skip_flows=True,
                       skip_data_flow=True, skip_dependencies=True)
    manifest = SyncManifest.load(wiki)
    module = next(path for path, owner in manifest.page_source_mappings.items()
                  if owner.scope == "module" and owner.source_path == "selected/owner.py")
    entity = next(path for path, owner in manifest.page_source_mappings.items()
                  if owner.scope == "entity" and owner.source_path == "selected/owner.py")
    assert not (root / "target-execution-tripwire").exists()
    return root, wiki, source, profile, module, entity


def _search(fixture, **options):
    root, wiki, *_ = fixture
    return search_service.search_wiki("cobalt retention sentinel", src_dir=str(root),
                                    wiki_dir=str(wiki), mode="ranked-v2",
                                    include_source=True, **options)


@pytest.mark.parametrize("mode,include_source", [("ranked", False), ("ranked-v1", False), ("substring", False),
                                                  ("ranked-v2", False), ("ranked-v2", True)])
def test_owned_public_cli_mcp_service_byte_parity(
    owned_wiki, monkeypatch, capsys,
    mode: Literal["ranked", "ranked-v1", "substring", "ranked-v2"], include_source: bool,
):
    root, wiki, *_ = owned_wiki
    kwargs: dict[str, Any] = dict(src_dir=str(root), wiki_dir=str(wiki), mode=mode,
                                 include_source=include_source, kinds=["modules"], limit=1)
    expected = api.search_wiki("owner", **kwargs)
    assert expected == search_service.search_wiki("owner", **kwargs)
    service = McpWikiService(src_dir=str(root), wiki_dir=str(wiki))
    assert service.search_wiki("owner", kinds=["modules"], limit=1, mode=mode,
                               include_source=include_source) == expected
    capsys.readouterr()
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "search", "owner", "--src-dir", str(root),
                                      "--wiki-dir", str(wiki), "--kind", "modules", "--limit", "1",
                                      "--mode", mode] + (["--include-source"] if include_source else []))
    cli.main()
    assert json.loads(capsys.readouterr().out) == expected
    assert expected["mode"] == mode
    assert ("source_indexing" in expected) is include_source
    if mode in {"ranked", "ranked-v2"}:
        assert expected.get("experimental") is False
        assert expected.get("definitive_answer") is False
        assert expected.get("ranking") == "llm-wiki-search/lexical-v2"
    elif mode == "ranked-v1":
        assert expected.get("ranking") == "llm-wiki-search/lexical-v1"
        assert "experimental" not in expected and "definitive_answer" not in expected
    if mode == "substring":
        assert "ranking" not in expected
        assert all("score" not in item and "provenance" not in item for item in expected["results"])


@pytest.mark.parametrize("mode,include_source", [("ranked", False), ("ranked-v1", False), ("substring", False),
                                                  ("ranked-v2", False), ("ranked-v2", True)])
def test_mcp_external_wiki_root_and_exactly_one_capture(
    owned_wiki, monkeypatch,
    mode: Literal["ranked", "ranked-v1", "substring", "ranked-v2"], include_source: bool,
):
    root, wiki, *_ = owned_wiki
    expected = search_service.search_prevalidated_roots(
        "owner", source_root=root, wiki_root=wiki, kinds=["modules"],
        mode=mode, include_source=include_source,
    )
    monkeypatch.chdir(root)
    assert not wiki.is_relative_to(root)
    service = McpWikiService(src_dir=str(root), wiki_dir=str(wiki))
    original = search_service.build_source_snapshot
    captures = []

    def capture(*args, **kwargs):
        captures.append(kwargs.copy())
        return original(*args, **kwargs)

    monkeypatch.setattr(search_service, "build_source_snapshot", capture)
    actual = service.search_wiki("owner", kinds=["modules"], mode=mode, include_source=include_source)
    assert actual == expected
    assert len(captures) == 1
    if include_source:
        assert captures[0]["coherent"] is True and captures[0]["respect_ignores"] is True
        assert captures[0]["max_bytes"] == 16_777_216
        accounting = actual["source_indexing"]
        assert accounting["source_read_bytes_including_rechecks"] >= accounting["source_bytes"]
        assert accounting["wiki_read_bytes_including_rechecks"] >= accounting["indexed_bytes"] - accounting["source_bytes"]
        assert accounting["source_snapshot_captured_input_bytes"] >= accounting["source_bytes"]
        assert accounting["final_source_validation"]


def test_real_source_only_term_preserves_physical_wiki_identity_without_writes(owned_wiki):
    root, wiki, source, _, module, _ = owned_wiki
    before = _tree(root), _tree(wiki)
    physical = (wiki / module).read_bytes()
    assert b"cobalt retention sentinel" not in physical
    result = _search(owned_wiki, kinds=["modules"])
    match = next(item for item in result["results"] if item["path"] == module)
    indexing = match["indexing"]
    assert indexing["original_wiki_content_sha256"] == _sha(physical)
    assert indexing["source_sha256"] == _sha(source.read_bytes())
    assert indexing["source_bytes"] == len(source.read_bytes())
    assert indexing["source_path"] == "selected/owner.py"
    assert match["provenance"]["content_sha256"] == _sha(physical)
    assert match["provenance"]["indexed_content_sha256"] == indexing["indexed_content_sha256"]
    assert indexing["indexed_content_sha256"] != _sha(physical)
    assert indexing["runtime_behavior_evaluated"] is False
    assert result["source_indexing"]["source_files"] == 1
    assert result["source_indexing"]["runtime_behavior_evaluated"] is False
    assert (_tree(root), _tree(wiki)) == before
    assert not (root / "target-execution-tripwire").exists()


def test_frozen_owned_source_arm_is_byte_equal_for_both_engines(owned_wiki, monkeypatch):
    frozen = []
    original = search_service.search_records

    def capture(records, query, **options):
        values = list(records)
        frozen.extend(json.loads(json.dumps(values)))
        return original(values, query, **options)

    monkeypatch.setattr(search_service, "search_records", capture)
    actual = _search(owned_wiki, kinds=["modules"])
    before = json.dumps(frozen, ensure_ascii=False, sort_keys=True).encode("utf-8")
    legacy = rank_legacy(frozen, "cobalt retention sentinel")
    candidate = rank_candidate(frozen, "cobalt retention sentinel")
    assert json.dumps(frozen, ensure_ascii=False, sort_keys=True).encode("utf-8") == before
    assert legacy["corpus_id"] == candidate["corpus_id"] == actual["corpus_id"]
    assert legacy["scanned"] == candidate["scanned"] == actual["scanned"]
    assert candidate["results"] == actual["results"]


def test_unselected_and_unmapped_pages_filtered_before_reads(owned_wiki, monkeypatch):
    root, wiki, _, _, module, entity = owned_wiki
    from llm_wiki_cli.services.sync_manifest import (
        EVIDENCE_NOT_RECORDED, ManifestEvidenceBaseline, ManifestPageSource,
    )
    manifest = SyncManifest.load(wiki)
    manifest.sources["outside.py"] = {"hash": "sha256:" + _sha((root / "outside.py").read_bytes())}
    for directory in ("modules", "entities"):
        path = f"{directory}/private.md"
        (wiki / path).write_text("# cobalt retention sentinel hidden payload\n", encoding="utf-8")
        manifest.page_source_mappings[path] = (ManifestPageSource("module", "outside.py")
            if directory == "modules" else ManifestPageSource("entity", "outside.py", "Private", 1))
        manifest.evidence_baselines[path] = ManifestEvidenceBaseline(unknown_reason=EVIDENCE_NOT_RECORDED)
        (wiki / directory / "unmapped.md").write_text("# hidden payload\n", encoding="utf-8")
    manifest.save(wiki)
    original = StorageReadSession.read
    reads = []

    def guard(self, relative, *args, **kwargs):
        if self.root == wiki:
            assert relative not in {"modules/private.md", "entities/private.md",
                                    "modules/unmapped.md", "entities/unmapped.md"}
            reads.append(relative)
        return original(self, relative, *args, **kwargs)

    monkeypatch.setattr(StorageReadSession, "read", guard)
    result = _search(owned_wiki)
    assert module in reads and entity in reads
    assert all("private" not in match["path"] and "unmapped" not in match["path"] for match in result["results"])
    assert all("hidden payload" not in match["snippet"] for match in result["results"])


@pytest.mark.parametrize("bad", [True, 1, "yes", None])
def test_source_option_requires_explicit_boolean_and_candidate_before_capture(monkeypatch, bad):
    monkeypatch.setattr(search_service, "build_source_snapshot", lambda *a, **kw: pytest.fail("captured invalid request"))
    with pytest.raises(ValueError):
        search_service.search_wiki("owner", mode="ranked", include_source=bad)


@pytest.mark.parametrize("bad", [1, "yes", None])
def test_candidate_source_option_rejects_nonboolean_before_capture(monkeypatch, bad):
    monkeypatch.setattr(search_service, "build_source_snapshot", lambda *a, **kw: pytest.fail("captured invalid request"))
    with pytest.raises(ValueError):
        search_service.search_wiki("owner", mode="ranked-v2", include_source=bad)


@pytest.mark.parametrize("state", ["missing", "corrupt", "traversal"])
def test_manifest_failures_never_admit_outside_source(owned_wiki, state):
    _, wiki, *_ = owned_wiki
    path = wiki / MANIFEST_FILENAME
    if state == "missing":
        path.unlink()
    elif state == "corrupt":
        path.write_text("{broken", encoding="utf-8")
    else:
        value = json.loads(path.read_text(encoding="utf-8"))
        value["page_source_mappings"][owned_wiki[4]]["source_path"] = "../outside.py"
        path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises((ValueError, OSError, KnowledgeStorageError)):
        _search(owned_wiki)


@pytest.mark.parametrize("target", ["source", "wiki", "profile", "manifest", "new-source", "new-wiki"])
def test_mutation_during_ranking_refuses_mixed_publication(owned_wiki, monkeypatch, target):
    root, wiki, source, profile, module, _ = owned_wiki
    original = search_service.search_records

    def race(records, query, **options):
        result = original(records, query, **options)
        path = {"source": source, "wiki": wiki / module, "profile": profile,
                "manifest": wiki / MANIFEST_FILENAME, "new-source": root / "selected/new.py",
                "new-wiki": wiki / "modules/new.md"}[target]
        path.write_bytes((path.read_bytes() if path.exists() else b"") + b"\n# raced\n")
        return result

    monkeypatch.setattr(search_service, "search_records", race)
    with pytest.raises((ValueError, OSError, KnowledgeStorageError)):
        _search(owned_wiki)


def test_source_file_replaced_after_guarded_read_refuses(owned_wiki, monkeypatch):
    root, wiki, source, *_ = owned_wiki
    before = _tree(root), _tree(wiki)
    original = StorageReadSession.read
    attempted = False

    def race(self, relative, *args, **kwargs):
        nonlocal attempted
        raw = original(self, relative, *args, **kwargs)
        if self.root == root and relative == "selected/owner.py":
            attempted = True
            source.write_bytes(raw + b"\n# later source\n")
        return raw

    monkeypatch.setattr(StorageReadSession, "read", race)
    if os.name == "nt":
        with pytest.raises(PermissionError) as denied:
            _search(owned_wiki)
        assert denied.value.errno == errno.EACCES
        assert denied.value.filename == str(source)
        assert (_tree(root), _tree(wiki)) == before
    else:
        with pytest.raises((ValueError, KnowledgeStorageError)):
            _search(owned_wiki)
        assert source.read_bytes().endswith(b"\n# later source\n")
    assert attempted


def test_symlinked_selected_source_never_indexes_outside_bytes(owned_wiki, tmp_path):
    root, _, source, *_ = owned_wiki
    outside = tmp_path.parent / (tmp_path.name + "-outside.py")
    outside.write_text("# outside cobalt retention sentinel secret\n", encoding="utf-8")
    try:
        source.unlink()
        source.symlink_to(outside)
        with pytest.raises((ValueError, OSError, KnowledgeStorageError)):
            _search(owned_wiki)
        assert not (root / "target-execution-tripwire").exists()
    finally:
        outside.unlink()


def test_ignored_source_never_enters_source_index(owned_wiki, monkeypatch):
    root, _, _, *_ = owned_wiki
    snapshot = build_source_snapshot(root, coherent=True, respect_ignores=True)
    assert "selected/ignored.py" not in snapshot.all_source_paths
    assert "selected/ignored.py" not in snapshot.captured_content_hashes
    original = StorageReadSession.read

    def guard(self, relative, *args, **kwargs):
        assert not (self.root == root and relative == "selected/ignored.py")
        return original(self, relative, *args, **kwargs)

    monkeypatch.setattr(StorageReadSession, "read", guard)
    result = _search(owned_wiki)
    assert result["source_indexing"]["source_files"] == 1
    assert all("ignored hidden" not in item["snippet"] for item in result["results"])


def test_source_per_file_and_unique_caps_fail_closed(owned_wiki, monkeypatch):
    _, _, source, *_ = owned_wiki
    monkeypatch.setattr(search_source, "MAX_SOURCE_FILE_BYTES", len(source.read_bytes()) - 1)
    with pytest.raises((ValueError, KnowledgeStorageError)):
        _search(owned_wiki)


def test_unique_source_cap_fail_closed(owned_wiki, monkeypatch):
    _, _, source, *_ = owned_wiki
    monkeypatch.setattr(search_source, "MAX_SOURCE_INDEX_BYTES", len(source.read_bytes()) - 1)
    with pytest.raises((ValueError, KnowledgeStorageError)):
        _search(owned_wiki)


def test_combined_source_wiki_cap_fail_closed(owned_wiki, monkeypatch):
    monkeypatch.setattr(search_source, "MAX_SEARCH_BYTES", 1)
    with pytest.raises((ValueError, KnowledgeStorageError)):
        _search(owned_wiki)


def test_public_and_mcp_invalid_explicit_mode_have_no_output(owned_wiki):
    root, wiki, *_ = owned_wiki
    with pytest.raises(api.LlmWikiApiError):
        api.search_wiki("owner", src_dir=str(root), wiki_dir=str(wiki), include_source=True)
    with pytest.raises(McpWikiError):
        McpWikiService(src_dir=str(root), wiki_dir=str(wiki)).search_wiki("owner", include_source=True)


def test_bundled_helper_owned_sentinels_are_excluded_without_execution(owned_wiki):
    root, _, source, *_ = owned_wiki
    package = source.parent / "llm_wiki_cli"
    for relative in ("__init__.py", "cli.py", "extractors/__init__.py", "extractors/common.py",
                     "extractors/ts_scripts/extract.js"):
        path = package / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("// helper cobalt secret\n" if relative.endswith(".js") else "# package marker\n",
                        encoding="utf-8")
    snapshot = build_source_snapshot(root, coherent=True, respect_ignores=True)
    helper = "selected/llm_wiki_cli/extractors/ts_scripts/extract.js"
    assert helper not in snapshot.all_source_paths
    assert helper not in snapshot.captured_content_hashes


def test_pure_augmentation_keeps_source_fences_and_unicode_inside_code():
    from llm_wiki_cli.services.markdown_sections import parse_markdown_document

    page = {"kind": "modules", "id": "owner", "uri": "llm-wiki://modules/owner",
            "path": "modules/owner.md", "title": "owner", "content": "# Owner\n"}
    raw = "# café\n# ```\n## injected heading\n# ```````\n".encode("utf-8")
    augmented = search_source.augment_module_page(page, "selected/owner.py", raw)
    assert page["content"] == "# Owner\n"
    headings = [section.title for section in parse_markdown_document(augmented["content"], page["uri"]).sections]
    assert headings == ["Owner", "Selected source indexing evidence"]
    assert augmented["indexing"]["source_bytes"] == len(raw)
    assert augmented["indexing"]["source_sha256"] == _sha(raw)


def test_pure_augmentation_real_one_megabyte_ceiling():
    page = {"content": "# Owner\n"}
    at_limit = b"#" * 1_048_576
    assert search_source.augment_module_page(page, "selected/owner.py", at_limit)["indexing"]["source_bytes"] == 1_048_576
    with pytest.raises(ValueError, match="byte limit"):
        search_source.augment_module_page(page, "selected/owner.py", at_limit + b"x")


@pytest.mark.parametrize("limit,expected", [(1, 1), (101, 100)])
def test_source_candidate_preserves_limit_and_zero_result_bounds(owned_wiki, limit, expected):
    root, wiki, *_ = owned_wiki
    result = api.search_wiki("nonexistent-candidate-4829", src_dir=str(root), wiki_dir=str(wiki),
                             mode="ranked-v2", include_source=True, limit=limit)
    assert result["results"] == []
    assert result["count"] == result["returned"] == result["total"] == 0
    assert result["truncated"] is False
    assert result["bounds"]["results"] == {"total": 0, "returned": 0, "truncated": False}
    assert search_service.normalize_search("owner", None, limit, "ranked-v2")[2] == expected
