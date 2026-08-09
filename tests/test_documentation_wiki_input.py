from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import cast

import pytest

from llm_wiki_cli.services import documentation_wiki_input as wiki_input_module
from llm_wiki_cli.services import filesystem_guard as filesystem_guard_module
from llm_wiki_cli.services import source_snapshot as source_snapshot_module
from llm_wiki_cli.services.documentation_wiki_input import (
    DocumentationWikiInputError,
    DocumentationWikiSnapshot,
    adopt_documentation_wiki_snapshot,
    fingerprint_documentation_wiki_input,
)
from llm_wiki_cli.services.knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.knowledge_freshness import (
    REASON_GENERATION_OPTIONS_CHANGED,
)
from llm_wiki_cli.services.knowledge_index import serialize_knowledge_index
from llm_wiki_cli.services.knowledge_model import ComputedFreshness
from llm_wiki_cli.services.knowledge_observability import knowledge_freshness_hint
from llm_wiki_cli.services.source_selection import (
    SOURCE_SELECTION_IDENTITY_SCHEMA_VERSION,
    SOURCE_SELECTION_SCHEMA_VERSION,
    with_source_selection_generation_input,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME, SyncManifest
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_artifacts import _plan as _knowledge_commit_plan


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _write(path: Path, data: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")


def _materialize_evaluated_fixture_source(
    root: Path,
    source_files: Mapping[str, str],
) -> None:
    """Write evaluated fixture inputs as their exact UTF-8 evidence bytes."""

    expected = {
        relative_path: content.encode("utf-8")
        for relative_path, content in source_files.items()
    }
    for relative_path, content in expected.items():
        _write(root / relative_path, content)
    assert _tree_bytes(root) == expected


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def _stat_with(result: os.stat_result, **changes: int) -> os.stat_result:
    values = {
        "st_mode": result.st_mode,
        "st_size": result.st_size,
        "st_mtime": result.st_mtime,
        "st_mtime_ns": result.st_mtime_ns,
        "st_ctime_ns": result.st_ctime_ns,
        "st_dev": result.st_dev,
        "st_ino": result.st_ino,
        "st_file_attributes": getattr(result, "st_file_attributes", 0),
    }
    values.update(changes)
    return cast(os.stat_result, SimpleNamespace(**values))


def _write_current_metadata(
    wiki: Path,
    source_hashes: dict[str, str],
    *,
    manifest_version: int = 4,
    surface_schema: str = "llm-wiki-surface-index/v1",
    surface_pages: list[str] | None = None,
    generation_inputs: dict[str, object] | None = None,
) -> None:
    manifest = {
        "version": manifest_version,
        "sources": {
            path: {
                "hash": digest,
                "semantic_hash": "sha256:" + "0" * 64,
                "generated_semantics": {},
                "language": "python",
                "entities": [],
                "entity_pages": {},
                "module_page": Path(path).stem,
            }
            for path, digest in source_hashes.items()
        },
        "surfaces": {},
        "generation_inputs": generation_inputs or {},
    }
    pages = surface_pages if surface_pages is not None else ["index.md"]
    surface = {
        "schema_version": surface_schema,
        "source_hash": "sha256:" + "1" * 64,
        "pages": [
            {
                "kind": "index" if page == "index.md" else "guides",
                "id": Path(page).stem,
                "canonical_path": page,
                "source_path": None,
                "role": "mixed",
            }
            for page in pages
        ],
    }
    _write(wiki / ".llm-wiki-manifest.json", json.dumps(manifest))
    _write(wiki / ".llm-wiki-surface.json", json.dumps(surface))


def _write_v5_metadata(
    wiki: Path,
    *,
    marked: bool,
):
    fixture = one_module_two_entities_fixture()
    for page in fixture.pages:
        _write(wiki / page.canonical_path, page.content)
    for relative_path, content in fixture.assets.items():
        _write(wiki / relative_path, content)

    plan = _knowledge_commit_plan(wiki, fixture)
    if marked:
        commit_knowledge_artifacts(plan)
    else:
        _write(wiki / SURFACE_INDEX_FILENAME, plan.surface_index.content)
        _write(
            wiki / MANIFEST_FILENAME,
            plan.committed_manifest.without_artifact_hashes().to_json(),
        )
    return fixture, plan


def test_legacy_import_preserves_semantic_and_unknown_files_byte_for_byte(
    tmp_path: Path,
) -> None:
    wiki = tmp_path / "Existing Wiki"
    workspace = tmp_path / "Documentation Workspace" / "wiki"
    marker = "<!-- Auto-generated relationship summary. Do not edit by hand. -->"
    _write(wiki / "index.md", "# Enriched overview\r\n\r\nPrior LLM prose.\r\n")
    _write(wiki / "guides" / "Начало работы.md", "# Начало работы\n\nGuide prose.\n")
    _write(
        wiki / "modules" / "core.md",
        f"# core\n\nHuman explanation.\n\n{marker}\n```mermaid\ngraph LR\n```\n",
    )
    _write(wiki / "custom" / "agent-notes.md", "# Preserved custom page\n")
    _write(wiki / "custom" / "evidence.bin", b"\x00\xff\x10wiki")
    before = _tree_bytes(wiki)

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        workspace,
        freshness_policy="allow-unverified",
    )

    assert isinstance(snapshot, DocumentationWikiSnapshot)
    assert snapshot.legacy_index_only is True
    assert snapshot.freshness == "unverified"
    assert snapshot.source_verified_publish_ready is False
    assert snapshot.input_tree_hash == snapshot.initial_snapshot_hash
    assert snapshot.unknown_entries == (
        "custom/agent-notes.md",
        "custom/evidence.bin",
        "guides/Начало работы.md",
    )
    assert snapshot.semantic_markdown_paths == (
        "custom/agent-notes.md",
        "guides/Начало работы.md",
        "index.md",
        "modules/core.md",
    )
    marker_evidence = snapshot.generated_markers
    assert marker_evidence["schema_version"] == (
        wiki_input_module.GENERATED_MARKER_EVIDENCE_SCHEMA_VERSION
    )
    assert marker_evidence["total_count"] == 1
    assert marker_evidence["captured_count"] == 1
    assert marker_evidence["truncated"] is False
    assert marker_evidence["pages"]["modules/core.md"] == {
        "count": 1,
        "captured_count": 1,
        "truncated": False,
        "markers": [
            {
                "type": "html_comment",
                "sha256": _sha256(marker.encode("utf-8")),
                "byte_length": len(marker.encode("utf-8")),
            }
        ],
    }
    records = {record["canonical_path"]: record for record in snapshot.semantic_pages}
    assert (
        records["guides/Начало работы.md"]["imported_classification"] == "incompatible"
    )
    assert records["custom/agent-notes.md"]["imported_classification"] == (
        "incompatible"
    )
    assert records["modules/core.md"]["generated_marker_count"] == 1
    assert _tree_bytes(wiki) == before
    assert _tree_bytes(workspace) == before
    payload = snapshot.to_dict()
    assert payload["source"]["source_verified_publish_ready"] is False
    assert payload["compatibility"] == "legacy_index_only"
    assert payload["refresh_decision"] == "allow_unverified"
    assert payload["semantic_pages"] == [dict(page) for page in snapshot.semantic_pages]
    assert payload["resource_usage"] == {
        "entry_count": 8,
        "file_count": 5,
        "directory_count": 3,
        "total_bytes": sum(len(value) for value in before.values()),
        "maximum_depth": 2,
        "semantic_file_count": 4,
        "semantic_total_bytes": sum(
            len(value) for path, value in before.items() if path.endswith(".md")
        ),
    }
    assert payload["resource_limits"] == (
        wiki_input_module.documentation_wiki_input_resource_limits()
    )


def _assert_resource_limit_rejected_by_adoption_and_fingerprint(
    wiki: Path,
    workspace: Path,
    *,
    category: str,
) -> None:
    with pytest.raises(DocumentationWikiInputError) as fallback_error:
        wiki_input_module._collect_input_tree(
            wiki.resolve(),
            enforce_content_policy=True,
        )
    assert fallback_error.value.category == category
    assert fallback_error.value.diagnostics

    with pytest.raises(DocumentationWikiInputError) as fingerprint_error:
        fingerprint_documentation_wiki_input(wiki)
    assert fingerprint_error.value.category == category
    assert fingerprint_error.value.diagnostics

    with pytest.raises(DocumentationWikiInputError) as adoption_error:
        adopt_documentation_wiki_snapshot(
            wiki,
            workspace,
            freshness_policy="allow-unverified",
        )
    assert adoption_error.value.category == category
    assert adoption_error.value.diagnostics
    assert not workspace.exists()


def test_input_file_count_limit_applies_before_snapshot_or_fingerprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "#\n")
    _write(wiki / "guides" / "one.md", "1\n")
    _write(wiki / "guides" / "two.md", "2\n")
    monkeypatch.setattr(wiki_input_module, "MAX_INPUT_WIKI_FILES", 2)

    _assert_resource_limit_rejected_by_adoption_and_fingerprint(
        wiki,
        tmp_path / "workspace",
        category="input_file_count_limit_exceeded",
    )


def test_input_per_file_size_limit_applies_before_full_reads_or_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "#\n")
    _write(wiki / "assets" / "oversized.bin", b"123456789")
    monkeypatch.setattr(wiki_input_module, "MAX_INPUT_WIKI_FILE_BYTES", 8)

    _assert_resource_limit_rejected_by_adoption_and_fingerprint(
        wiki,
        tmp_path / "workspace",
        category="input_file_size_limit_exceeded",
    )


def test_input_aggregate_size_limit_applies_before_snapshot_or_fingerprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "#\n")
    _write(wiki / "assets" / "one.bin", b"1234")
    _write(wiki / "assets" / "two.bin", b"5678")
    monkeypatch.setattr(wiki_input_module, "MAX_INPUT_WIKI_TOTAL_BYTES", 8)

    _assert_resource_limit_rejected_by_adoption_and_fingerprint(
        wiki,
        tmp_path / "workspace",
        category="input_total_size_limit_exceeded",
    )


def test_input_entry_limit_bounds_directory_only_trees(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "#\n")
    (wiki / "empty-a").mkdir(parents=True)
    (wiki / "empty-b").mkdir()
    monkeypatch.setattr(wiki_input_module, "MAX_INPUT_WIKI_ENTRIES", 2)

    _assert_resource_limit_rejected_by_adoption_and_fingerprint(
        wiki,
        tmp_path / "workspace",
        category="input_entry_count_limit_exceeded",
    )


def test_input_depth_limit_bounds_deep_directory_trees(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "#\n")
    (wiki / "one" / "two" / "three").mkdir(parents=True)
    monkeypatch.setattr(wiki_input_module, "MAX_INPUT_WIKI_DEPTH", 2)

    _assert_resource_limit_rejected_by_adoption_and_fingerprint(
        wiki,
        tmp_path / "workspace",
        category="input_depth_limit_exceeded",
    )


def test_semantic_file_budget_accepts_boundary_and_rejects_before_full_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exact_wiki = tmp_path / "exact-wiki"
    exact_content = b"# Index\n"
    _write(exact_wiki / "index.md", exact_content)
    monkeypatch.setattr(
        wiki_input_module,
        "MAX_INPUT_WIKI_SEMANTIC_FILE_BYTES",
        len(exact_content),
    )

    snapshot = adopt_documentation_wiki_snapshot(
        exact_wiki,
        tmp_path / "exact-workspace",
        freshness_policy="allow-unverified",
    )
    assert snapshot.resource_usage["semantic_total_bytes"] == len(exact_content)

    oversized_wiki = tmp_path / "oversized-wiki"
    _write(oversized_wiki / "index.md", exact_content + b"x")
    reads: list[str] = []
    original_read = wiki_input_module._read_verified_bytes

    def record_read(entry):
        reads.append(entry.relative_path)
        return original_read(entry)

    monkeypatch.setattr(wiki_input_module, "_read_verified_bytes", record_read)
    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            oversized_wiki,
            tmp_path / "oversized-workspace",
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == "input_semantic_file_size_limit_exceeded"
    assert exc_info.value.diagnostics
    assert reads == []
    assert not (tmp_path / "oversized-workspace").exists()


def test_semantic_aggregate_budget_accepts_boundary_and_rejects_one_byte_lower(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    index_content = b"#\n"
    guide_content = b"1\n"
    _write(wiki / "index.md", index_content)
    _write(wiki / "guides" / "one.md", guide_content)
    total_bytes = len(index_content) + len(guide_content)
    monkeypatch.setattr(
        wiki_input_module,
        "MAX_INPUT_WIKI_SEMANTIC_TOTAL_BYTES",
        total_bytes,
    )

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "exact-workspace",
        freshness_policy="allow-unverified",
    )
    assert snapshot.resource_usage["semantic_total_bytes"] == total_bytes

    monkeypatch.setattr(
        wiki_input_module,
        "MAX_INPUT_WIKI_SEMANTIC_TOTAL_BYTES",
        total_bytes - 1,
    )
    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "rejected-workspace",
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == "input_semantic_total_size_limit_exceeded"
    assert exc_info.value.diagnostics
    assert not (tmp_path / "rejected-workspace").exists()


def test_generated_marker_evidence_caps_records_and_never_retains_marker_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    secret = "SENSITIVE-MARKER-PAYLOAD-DO-NOT-PERSIST"
    marker = f"<!-- Auto-generated {secret * 64} -->"
    page = "# Generated\n\n" + "\n".join(marker for _ in range(4)) + "\n"
    _write(wiki / "index.md", page)
    _write(wiki / "guides" / "many.md", page)
    monkeypatch.setattr(
        wiki_input_module,
        "MAX_GENERATED_MARKER_RECORDS_PER_PAGE",
        2,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "MAX_GENERATED_MARKER_RECORDS_TOTAL",
        3,
    )

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "workspace",
        freshness_policy="allow-unverified",
    )

    evidence = snapshot.generated_markers
    assert evidence["total_count"] == 8
    assert evidence["captured_count"] == 3
    assert evidence["truncated"] is True
    assert all(
        page_evidence["captured_count"] <= 2
        for page_evidence in evidence["pages"].values()
    )
    serialized = json.dumps(evidence, sort_keys=True)
    assert secret not in serialized
    assert "excerpt" not in serialized
    assert all(
        set(record) == {"type", "sha256", "byte_length"}
        for page_evidence in evidence["pages"].values()
        for record in page_evidence["markers"]
    )
    records = {record["canonical_path"]: record for record in snapshot.semantic_pages}
    assert records["index.md"]["generated_marker_count"] == 4
    assert records["guides/many.md"]["generated_marker_count"] == 4


def test_generated_marker_evidence_serialized_byte_cap_trims_detail_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    marker = "<!-- Auto-generated bounded marker -->"
    _write(wiki / "index.md", "# Index\n" + (marker + "\n") * 8)
    monkeypatch.setattr(
        wiki_input_module,
        "MAX_GENERATED_MARKER_EVIDENCE_BYTES",
        1_024,
    )

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "workspace",
        freshness_policy="allow-unverified",
    )

    evidence = snapshot.generated_markers
    canonical = json.dumps(
        evidence,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert len(canonical) <= 1_024
    assert evidence["total_count"] == 8
    assert evidence["captured_count"] < evidence["total_count"]
    assert evidence["truncated"] is True
    assert snapshot.semantic_pages[0]["generated_marker_count"] == 8


def test_require_current_fails_before_copy_without_source(tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    workspace = tmp_path / "workspace" / "wiki"
    _write(wiki / "index.md", "# Index\n")
    before = _tree_bytes(wiki)

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(wiki, workspace)

    assert exc_info.value.category == "freshness_not_current"
    assert "allow-unverified" in str(exc_info.value)
    assert not workspace.exists()
    assert _tree_bytes(wiki) == before


def test_source_backed_current_metadata_reaches_verified_current(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    workspace = tmp_path / "workspace" / "wiki"
    source_bytes = b"def run():\n    return 1\n"
    _write(source / "pkg" / "app.py", source_bytes)
    _write(wiki / "index.md", "# Index\n")
    _write(wiki / "guides" / "user.md", "# User guide\n")
    _write_current_metadata(
        wiki,
        {"pkg/app.py": _sha256(source_bytes)},
        surface_pages=["index.md", "guides/user.md"],
    )
    before = _tree_bytes(wiki)

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        workspace,
        source_root=source,
    )

    assert snapshot.recognized_schemas == {
        "manifest": 4,
        "surface": "llm-wiki-surface-index/v1",
    }
    assert snapshot.freshness == "verified_current"
    assert snapshot.source_mismatches == ()
    assert snapshot.workspace_refresh_required is False
    assert snapshot.source_verified_publish_ready is True
    assert snapshot.to_dict()["manifest_version"] == 4
    assert snapshot.to_dict()["surface_schema_version"] == ("llm-wiki-surface-index/v1")
    assert _tree_bytes(wiki) == before
    assert _tree_bytes(workspace) == before


def test_changed_source_fails_closed_or_remains_visibly_limited(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    source_file = source / "app.py"
    _write(source_file, b"old\n")
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(wiki, {"app.py": _sha256(b"old\n")})
    _write(source_file, b"new\n")
    before = _tree_bytes(wiki)

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "refused" / "wiki",
            source_root=source,
        )
    assert exc_info.value.category == "freshness_not_current"
    assert not (tmp_path / "refused").exists()

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "limited" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )
    assert snapshot.freshness == "verified_stale"
    assert snapshot.source_mismatches == ("changed:app.py",)
    assert snapshot.workspace_refresh_required is False
    assert snapshot.source_verified_publish_ready is False
    assert any("publish_ready_limited" in item for item in snapshot.diagnostics)
    assert _tree_bytes(wiki) == before


@pytest.mark.parametrize(
    "added_relative_path",
    [
        "pkg/new_feature.py",
        "pkg with spaces/naïve_feature.py",
    ],
)
def test_added_supported_source_file_is_detected_by_current_inventory(
    tmp_path: Path,
    added_relative_path: str,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    original_bytes = b"def original():\n    return 1\n"
    _write(source / "pkg" / "app.py", original_bytes)
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(wiki, {"pkg/app.py": _sha256(original_bytes)})
    _write(
        source.joinpath(*PurePosixPath(added_relative_path).parts),
        b"def added():\n    return 2\n",
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "refused" / "wiki",
            source_root=source,
        )

    assert exc_info.value.category == "freshness_not_current"
    assert not (tmp_path / "refused").exists()

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "limited" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )

    assert snapshot.freshness == "verified_stale"
    assert snapshot.source_mismatches == (f"added:{added_relative_path}",)
    assert any(
        "source inventory item(s) differ" in item for item in snapshot.diagnostics
    )


def test_removed_manifest_source_file_is_detected_by_current_inventory(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    current_bytes = b"def current():\n    return 1\n"
    _write(source / "pkg" / "current.py", current_bytes)
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(
        wiki,
        {
            "pkg/current.py": _sha256(current_bytes),
            "pkg/removed.py": _sha256(b"def removed():\n    return 0\n"),
        },
    )

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "limited" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )

    assert snapshot.freshness == "verified_stale"
    assert snapshot.source_mismatches == ("removed:pkg/removed.py",)


def test_source_removed_from_supported_inventory_is_stale_even_if_file_exists(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    current_bytes = b"def current():\n    return 1\n"
    ignored_bytes = b"def ignored():\n    return 2\n"
    _write(source / "pkg" / "current.py", current_bytes)
    _write(source / "pkg" / "ignored.py", ignored_bytes)
    _write(source / ".gitignore", "pkg/ignored.py\n")
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(
        wiki,
        {
            "pkg/current.py": _sha256(current_bytes),
            "pkg/ignored.py": _sha256(ignored_bytes),
        },
    )

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "limited" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )

    assert snapshot.freshness == "verified_stale"
    assert snapshot.source_mismatches == ("removed:pkg/ignored.py",)
    assert (source / "pkg" / "ignored.py").is_file()


def test_empty_manifest_with_supported_source_addition_is_verified_stale(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    _write(source / "app.py", b"def added():\n    return 1\n")
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(wiki, {})

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "limited" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )

    assert snapshot.freshness == "verified_stale"
    assert snapshot.source_mismatches == ("added:app.py",)


def test_changed_selection_identity_is_stale_when_source_bytes_match(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    source_bytes = b"def current():\n    return 1\n"
    _write(source / "selected" / "app.py", source_bytes)
    _write(
        source / ".llm-wiki" / "source-selection.json",
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["selected"],
                "exclude": [],
            }
        ),
    )
    _write(wiki / "index.md", "# Index\n")
    source_snapshot = build_source_snapshot(source)
    _write_current_metadata(
        wiki,
        {"selected/app.py": _sha256(source_bytes)},
        generation_inputs=with_source_selection_generation_input(
            {},
            {
                "schema_version": SOURCE_SELECTION_IDENTITY_SCHEMA_VERSION,
                "path": ".llm-wiki/source-selection.json",
                "fingerprint": _sha256(b"different semantic policy"),
            },
            source_snapshot.source_selection_inputs,
        ),
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "refused" / "wiki",
            source_root=source,
        )
    assert exc_info.value.category == "freshness_not_current"

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "limited" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )
    assert snapshot.freshness == "verified_stale"
    assert snapshot.source_mismatches == ("generation_input_changed:source_selection",)


def test_selection_control_broadening_is_stale_before_new_source_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    keep_bytes = b"KEEP = True\n"
    _write(source / "selected" / "keep.py", keep_bytes)
    secret = source / "selected" / "secret.py"
    _write(secret, b"MUST_NOT_READ = True\n")
    ignore = source / "selected" / ".gitignore"
    _write(ignore, "secret.py\n")
    _write(
        source / ".llm-wiki" / "source-selection.json",
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["selected"],
                "exclude": [],
            }
        ),
    )
    _write(wiki / "index.md", "# Index\n")
    initial = build_source_snapshot(source)
    _write_current_metadata(
        wiki,
        {"selected/keep.py": _sha256(keep_bytes)},
        generation_inputs=with_source_selection_generation_input(
            {},
            initial.source_selection_identity,
            initial.source_selection_inputs,
        ),
    )
    ignore.write_text("", encoding="utf-8")
    real_hash = source_snapshot_module._sha256_file

    def guarded_hash(path: Path) -> str:
        if path == secret:
            pytest.fail("newly admitted source must not be hashed before rejection")
        return real_hash(path)

    monkeypatch.setattr(source_snapshot_module, "_sha256_file", guarded_hash)

    adopted = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "limited" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )

    assert adopted.freshness == "verified_stale"
    assert adopted.source_mismatches == (
        "generation_input_changed:source_selection_inputs",
    )


def test_current_openapi_generation_input_can_verify_without_language_sources(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    openapi_bytes = b"openapi: 3.1.0\ninfo: {title: Demo, version: '1'}\npaths: {}\n"
    _write(source / "contracts" / "openapi.yaml", openapi_bytes)
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(
        wiki,
        {},
        generation_inputs={
            "openapi": {
                "path": "contracts/openapi.yaml",
                "sha256": _sha256(openapi_bytes),
                "format": "yaml",
            }
        },
    )

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "workspace" / "wiki",
        source_root=source,
    )

    assert snapshot.freshness == "verified_current"
    assert snapshot.source_mismatches == ()


@pytest.mark.parametrize("boundary", ("policy", "gitignore", "global"))
def test_deselected_openapi_generation_input_is_never_read(
    tmp_path: Path,
    monkeypatch,
    boundary: str,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    selected_bytes = b"VALUE = 1\n"
    openapi_bytes = b"openapi: 3.1.0\ninfo: {title: Secret, version: '1'}\npaths: {}\n"
    _write(source / "selected" / "app.py", selected_bytes)
    relative_openapi = {
        "policy": "outside/openapi.yaml",
        "gitignore": "selected/contracts/openapi.yaml",
        "global": "selected/build/openapi.yaml",
    }[boundary]
    _write(source / relative_openapi, openapi_bytes)
    if boundary == "gitignore":
        _write(source / "selected" / ".gitignore", "contracts/openapi.yaml\n")
    _write(
        source / ".llm-wiki" / "source-selection.json",
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["selected"],
                "exclude": [],
            }
        ),
    )
    source_snapshot = build_source_snapshot(source)
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(
        wiki,
        {"selected/app.py": _sha256(selected_bytes)},
        generation_inputs=with_source_selection_generation_input(
            {
                "openapi": {
                    "path": relative_openapi,
                    "sha256": _sha256(openapi_bytes),
                    "format": "yaml",
                },
            },
            source_snapshot.source_selection_identity,
            source_snapshot.source_selection_inputs,
        ),
    )
    real_compare = wiki_input_module._compare_source_file

    def reject_deselected_read(root, relative_path, expected_hash):
        if relative_path == relative_openapi:
            pytest.fail("deselected OpenAPI input must not be opened")
        return real_compare(root, relative_path, expected_hash)

    monkeypatch.setattr(
        wiki_input_module,
        "_compare_source_file",
        reject_deselected_read,
    )

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "limited" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )

    assert snapshot.freshness == "verified_stale"
    assert snapshot.source_mismatches == (
        f"generation_input_deselected:openapi:{relative_openapi}",
    )


def test_changed_openapi_generation_input_makes_unchanged_sources_stale(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    source_bytes = b"def unchanged():\n    return 1\n"
    original_openapi = b"openapi: 3.1.0\ninfo: {title: Demo, version: '1'}\npaths: {}\n"
    changed_openapi = b"openapi: 3.1.0\ninfo: {title: Demo, version: '2'}\npaths: {}\n"
    _write(source / "app.py", source_bytes)
    _write(source / "contracts" / "openapi.yaml", original_openapi)
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(
        wiki,
        {"app.py": _sha256(source_bytes)},
        generation_inputs={
            "openapi": {
                "path": "contracts/openapi.yaml",
                "sha256": _sha256(original_openapi),
                "format": "yaml",
            }
        },
    )
    _write(source / "contracts" / "openapi.yaml", changed_openapi)

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "refused" / "wiki",
            source_root=source,
        )

    assert exc_info.value.category == "freshness_not_current"
    assert not (tmp_path / "refused").exists()

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "limited" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )

    assert snapshot.freshness == "verified_stale"
    assert snapshot.source_mismatches == (
        "generation_input_changed:openapi:contracts/openapi.yaml",
    )


def test_missing_openapi_generation_input_is_reported_as_removed(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    source_bytes = b"def unchanged():\n    return 1\n"
    _write(source / "app.py", source_bytes)
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(
        wiki,
        {"app.py": _sha256(source_bytes)},
        generation_inputs={
            "openapi": {
                "path": "contracts/openapi.yaml",
                "sha256": "sha256:" + "0" * 64,
                "format": "yaml",
            }
        },
    )

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "limited" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )

    assert snapshot.freshness == "verified_stale"
    assert snapshot.source_mismatches == (
        "generation_input_removed:openapi:contracts/openapi.yaml",
    )


@pytest.mark.parametrize(
    "openapi_metadata",
    [
        [],
        {
            "sha256": "sha256:" + "0" * 64,
            "format": "yaml",
        },
        {
            "path": "../outside.yaml",
            "sha256": "sha256:" + "0" * 64,
            "format": "yaml",
        },
        {
            "path": "C:/outside.yaml",
            "sha256": "sha256:" + "0" * 64,
            "format": "yaml",
        },
        {
            "path": "contracts/./openapi.yaml",
            "sha256": "sha256:" + "0" * 64,
            "format": "yaml",
        },
        {
            "path": "contracts/openapi.yaml",
            "sha256": "not-a-hash",
            "format": "yaml",
        },
        {
            "path": "contracts/openapi.yaml",
            "sha256": "sha256:" + "0" * 64,
            "format": "toml",
        },
        {
            "path": "contracts/openapi.yaml",
            "sha256": "sha256:" + "0" * 64,
            "format": "yaml",
            "endpoint": "https://example.invalid/openapi.yaml",
        },
    ],
)
def test_malformed_openapi_generation_input_metadata_fails_closed(
    tmp_path: Path,
    openapi_metadata: object,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(
        wiki,
        {},
        generation_inputs={"openapi": openapi_metadata},
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace" / "wiki",
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == "manifest_schema_invalid"
    assert "generation_inputs.openapi" in str(exc_info.value)
    assert not (tmp_path / "workspace").exists()


def test_unknown_generation_input_metadata_fails_closed(tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(
        wiki,
        {},
        generation_inputs={"remote_schema": {"path": "schema.json"}},
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace" / "wiki",
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == "manifest_schema_invalid"
    assert "unsupported key 'remote_schema'" in str(exc_info.value)


def test_refresh_snapshot_records_workspace_only_follow_up(tmp_path: Path) -> None:
    source = tmp_path / "source"
    wiki = tmp_path / "wiki"
    workspace = tmp_path / "workspace" / "wiki"
    _write(source / "app.py", b"new\n")
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(wiki, {"app.py": _sha256(b"old\n")})
    before = _tree_bytes(wiki)

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        workspace,
        source_root=source,
        freshness_policy="refresh-snapshot",
    )

    assert snapshot.freshness == "verified_stale"
    assert snapshot.workspace_refresh_required is True
    assert snapshot.refresh_decision == "workspace_only_required"
    assert any("workspace_refresh_required" in item for item in snapshot.diagnostics)
    assert _tree_bytes(wiki) == before
    assert _tree_bytes(workspace) == before


def test_legacy_refresh_requires_source_and_never_seeds_input(tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    workspace = tmp_path / "workspace" / "wiki"
    _write(wiki / "index.md", "# Legacy\n")

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            workspace,
            freshness_policy="refresh-snapshot",
        )

    assert exc_info.value.category == "refresh_source_required"
    assert set(_tree_bytes(wiki)) == {"index.md"}
    assert not workspace.exists()


@pytest.mark.parametrize(
    ("manifest", "surface", "category"),
    [
        (True, False, "metadata_pair_incomplete"),
        (False, True, "metadata_pair_incomplete"),
    ],
)
def test_metadata_must_be_present_as_a_pair(
    tmp_path: Path,
    manifest: bool,
    surface: bool,
    category: str,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n")
    if manifest:
        _write(
            wiki / ".llm-wiki-manifest.json",
            json.dumps(
                {"version": 4, "sources": {}, "surfaces": {}, "generation_inputs": {}}
            ),
        )
    if surface:
        _write(
            wiki / ".llm-wiki-surface.json",
            json.dumps({"schema_version": "llm-wiki-surface-index/v1", "pages": []}),
        )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace" / "wiki",
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == category
    assert not (tmp_path / "workspace").exists()


def test_markerless_v5_surface_form_is_validated_and_adopted_without_knowledge(
    tmp_path: Path,
) -> None:
    wiki = tmp_path / "wiki"
    workspace = tmp_path / "workspace" / "wiki"
    _fixture, plan = _write_v5_metadata(wiki, marked=False)

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        workspace,
        freshness_policy="allow-unverified",
    )

    assert snapshot.artifact_form == "manifest_v5_surface"
    assert snapshot.recognized_schemas == {
        "manifest": 5,
        "surface": "llm-wiki-surface-index/v1",
    }
    assert snapshot.knowledge_schema_version is None
    assert snapshot.freshness == "unverified"
    assert KNOWLEDGE_INDEX_FILENAME not in snapshot.copied_paths
    assert (workspace / SURFACE_INDEX_FILENAME).read_bytes() == (
        plan.surface_index.content
    )


def test_marked_v5_trio_uses_guarded_bytes_and_exposes_validated_schema_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    source = tmp_path / "source"
    workspace = tmp_path / "workspace" / "wiki"
    fixture, plan = _write_v5_metadata(wiki, marked=True)
    _materialize_evaluated_fixture_source(source, fixture.source_files)

    monkeypatch.setattr(
        SyncManifest,
        "load",
        lambda *_args, **_kwargs: pytest.fail(
            "input validation must not reopen the manifest by path"
        ),
    )

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        workspace,
        source_root=source,
        freshness_policy="allow-unverified",
    )

    assert snapshot.artifact_form == "manifest_v5_native"
    assert snapshot.recognized_schemas == {
        "manifest": 5,
        "surface": "llm-wiki-surface-index/v1",
        "knowledge": "llm-wiki-knowledge/v1",
    }
    assert snapshot.knowledge_schema_version == "llm-wiki-knowledge/v1"
    assert snapshot.freshness == "verified_current"
    assert snapshot.source_mismatches == ()
    assert any("native_verified_current" in item for item in snapshot.diagnostics)
    assert KNOWLEDGE_INDEX_FILENAME in snapshot.copied_paths
    assert KNOWLEDGE_INDEX_FILENAME not in snapshot.unknown_entries
    assert (workspace / KNOWLEDGE_INDEX_FILENAME).read_bytes() == (
        plan.knowledge_index.content
    )


def test_marked_v5_trio_rejects_changed_source_through_shared_live_evaluation(
    tmp_path: Path,
) -> None:
    wiki = tmp_path / "wiki"
    source = tmp_path / "source"
    fixture, _plan = _write_v5_metadata(wiki, marked=True)
    for relative_path, content in fixture.source_files.items():
        _write(
            source / relative_path,
            (content + "\n# changed after generation\n").encode("utf-8"),
        )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace" / "wiki",
            source_root=source,
        )

    assert exc_info.value.category == "freshness_not_current"
    assert any(
        "native_freshness_not_current:changed:src/accounts.py" in item
        for item in exc_info.value.diagnostics
    )
    assert not (tmp_path / "workspace").exists()


def test_native_basis_incompatibility_exposes_structured_actionable_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    source = tmp_path / "source"
    fixture, _plan = _write_v5_metadata(wiki, marked=True)
    _materialize_evaluated_fixture_source(source, fixture.source_files)

    locator = "llm-wiki://entities/User"
    reason = REASON_GENERATION_OPTIONS_CHANGED
    hint = knowledge_freshness_hint(ComputedFreshness.BASIS_INCOMPATIBLE, reason)
    assert hint is not None

    from llm_wiki_cli.services import documentation_native

    monkeypatch.setattr(
        documentation_native,
        "evaluate_documentation_native_freshness",
        lambda **_kwargs: SimpleNamespace(
            current=False,
            reasons=(f"{locator}:{reason}",),
            source_mismatches=(),
            report=SimpleNamespace(
                by_locator={
                    locator: SimpleNamespace(
                        state=ComputedFreshness.BASIS_INCOMPATIBLE,
                        reason_code=reason,
                    )
                }
            ),
        ),
    )

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "allow-unverified" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )

    expected = {
        "locator": locator,
        "state": ComputedFreshness.BASIS_INCOMPATIBLE.value,
        "reason_code": reason,
        "hint": hint,
    }
    assert snapshot.freshness == "verified_stale"
    assert snapshot.freshness_diagnostics == (expected,)
    assert snapshot.to_dict()["freshness_diagnostics"] == [expected]
    assert any(
        item == f"native_basis_incompatible:{locator}:{reason}; hint={hint}"
        for item in snapshot.diagnostics
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "require-current" / "wiki",
            source_root=source,
            freshness_policy="require-current",
        )

    assert exc_info.value.category == "freshness_not_current"
    assert reason in str(exc_info.value)
    assert hint in str(exc_info.value)


def test_native_unknown_basis_incompatibility_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    source = tmp_path / "source"
    fixture, _plan = _write_v5_metadata(wiki, marked=True)
    _materialize_evaluated_fixture_source(source, fixture.source_files)

    unknown_reason = "future-basis-reason"
    locator = "llm-wiki://entities/User"
    from llm_wiki_cli.services import documentation_native

    monkeypatch.setattr(
        documentation_native,
        "evaluate_documentation_native_freshness",
        lambda **_kwargs: SimpleNamespace(
            current=False,
            reasons=(f"{locator}:{unknown_reason}",),
            source_mismatches=(),
            report=SimpleNamespace(
                by_locator={
                    locator: SimpleNamespace(
                        state=ComputedFreshness.BASIS_INCOMPATIBLE,
                        reason_code=unknown_reason,
                    )
                }
            ),
        ),
    )

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "workspace" / "wiki",
        source_root=source,
        freshness_policy="allow-unverified",
    )

    assert snapshot.freshness == "unverified"
    assert snapshot.freshness_diagnostics == ()
    assert "freshness_diagnostics" not in snapshot.to_dict()
    assert any(
        item.startswith("native_freshness_invalid:") for item in snapshot.diagnostics
    )
    assert all(unknown_reason not in item for item in snapshot.diagnostics)


@pytest.mark.parametrize(
    ("artifact_form", "category"),
    [
        ("orphan-knowledge", "knowledge_artifact_orphan"),
        ("v4-with-knowledge", "native_artifact_form_invalid"),
        ("markerless-v5-with-knowledge", "native_artifact_marker_missing"),
        ("marked-v5-without-knowledge", "native_artifact_set_incomplete"),
        ("marked-v5-without-surface", "metadata_pair_incomplete"),
    ],
)
def test_partial_or_orphan_native_artifact_forms_fail_closed(
    tmp_path: Path,
    artifact_form: str,
    category: str,
) -> None:
    wiki = tmp_path / artifact_form
    _write(wiki / "index.md", "# Index\n")
    fixture = one_module_two_entities_fixture()
    if artifact_form == "orphan-knowledge":
        _write(wiki / KNOWLEDGE_INDEX_FILENAME, fixture.knowledge_bytes)
    elif artifact_form == "v4-with-knowledge":
        _write_current_metadata(wiki, {})
        _write(wiki / KNOWLEDGE_INDEX_FILENAME, fixture.knowledge_bytes)
    elif artifact_form == "markerless-v5-with-knowledge":
        fixture, plan = _write_v5_metadata(wiki, marked=False)
        _write(wiki / KNOWLEDGE_INDEX_FILENAME, plan.knowledge_index.content)
    else:
        _fixture, _plan = _write_v5_metadata(wiki, marked=True)
        if artifact_form == "marked-v5-without-knowledge":
            (wiki / KNOWLEDGE_INDEX_FILENAME).unlink()
        else:
            (wiki / SURFACE_INDEX_FILENAME).unlink()

    workspace = tmp_path / f"{artifact_form}-workspace"
    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            workspace,
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == category
    assert not workspace.exists()


@pytest.mark.parametrize(
    ("mutation", "category"),
    [
        ("corrupt-surface", "surface_schema_invalid"),
        ("future-surface", "surface_schema_unsupported"),
        ("corrupt-knowledge", "native_artifact_invalid"),
        ("future-knowledge", "knowledge_schema_unsupported"),
        ("surface-knowledge-parity", "native_artifact_invalid"),
        ("marker-mismatch", "native_artifact_marker_mismatch"),
        ("markdown-mismatch", "native_markdown_snapshot_mismatch"),
        ("page-parity-mismatch", "native_page_parity_mismatch"),
    ],
)
def test_invalid_v5_native_artifact_state_fails_closed_before_copy(
    tmp_path: Path,
    mutation: str,
    category: str,
) -> None:
    wiki = tmp_path / mutation
    _fixture, plan = _write_v5_metadata(wiki, marked=True)
    if mutation == "corrupt-surface":
        _write(wiki / SURFACE_INDEX_FILENAME, "{")
    elif mutation == "future-surface":
        surface = json.loads(plan.surface_index.content)
        surface["schema_version"] = "llm-wiki-surface-index/v2"
        _write(
            wiki / SURFACE_INDEX_FILENAME,
            (json.dumps(surface, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
    elif mutation == "corrupt-knowledge":
        _write(wiki / KNOWLEDGE_INDEX_FILENAME, "{")
    elif mutation == "future-knowledge":
        knowledge = json.loads(plan.knowledge_index.content)
        knowledge["schema_version"] = "llm-wiki-knowledge/v2"
        _write(
            wiki / KNOWLEDGE_INDEX_FILENAME,
            (json.dumps(knowledge, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
    elif mutation == "surface-knowledge-parity":
        surface = json.loads(plan.surface_index.content)
        surface["pages"][0]["title"] += " changed"
        surface_bytes = (json.dumps(surface, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        knowledge = json.loads(plan.knowledge_index.content)
        knowledge["bundle"]["snapshot"]["surface_index_hash"] = sha256_bytes(
            surface_bytes
        )
        _write(wiki / SURFACE_INDEX_FILENAME, surface_bytes)
        _write(
            wiki / KNOWLEDGE_INDEX_FILENAME,
            serialize_knowledge_index(knowledge).encode("utf-8"),
        )
    elif mutation == "marker-mismatch":
        manifest = json.loads((wiki / MANIFEST_FILENAME).read_bytes())
        manifest["artifact_hashes"]["surface_index_hash"] = "sha256:" + "0" * 64
        _write(
            wiki / MANIFEST_FILENAME,
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
    elif mutation == "markdown-mismatch":
        with (wiki / "index.md").open("ab") as handle:
            handle.write(b"\nChanged after commit.\n")
    else:
        _write(wiki / "guides" / "extra.md", "# Extra\n")

    workspace = tmp_path / f"{mutation}-workspace"
    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            workspace,
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == category
    assert not workspace.exists()


@pytest.mark.parametrize(
    ("manifest_version", "surface_schema", "category"),
    [
        (6, "llm-wiki-surface-index/v1", "manifest_schema_unsupported"),
        (3, "llm-wiki-surface-index/v1", "manifest_schema_unsupported"),
        (4, "llm-wiki-surface-index/v2", "surface_schema_unsupported"),
    ],
)
def test_future_or_unsupported_metadata_is_rejected(
    tmp_path: Path,
    manifest_version: int,
    surface_schema: str,
    category: str,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(
        wiki,
        {},
        manifest_version=manifest_version,
        surface_schema=surface_schema,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace" / "wiki",
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == category


def test_corrupt_metadata_and_missing_surface_page_are_rejected(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt"
    _write(corrupt / "index.md", "# Index\n")
    _write(corrupt / ".llm-wiki-manifest.json", "{")
    _write(
        corrupt / ".llm-wiki-surface.json",
        json.dumps({"schema_version": "llm-wiki-surface-index/v1", "pages": []}),
    )
    with pytest.raises(DocumentationWikiInputError) as corrupt_error:
        adopt_documentation_wiki_snapshot(
            corrupt,
            tmp_path / "corrupt-workspace",
            freshness_policy="allow-unverified",
        )
    assert corrupt_error.value.category == "metadata_corrupt"

    missing_page = tmp_path / "missing-page"
    _write(missing_page / "index.md", "# Index\n")
    _write_current_metadata(missing_page, {}, surface_pages=["guides/missing.md"])
    with pytest.raises(DocumentationWikiInputError) as surface_error:
        adopt_documentation_wiki_snapshot(
            missing_page,
            tmp_path / "surface-workspace",
            freshness_policy="allow-unverified",
        )
    assert surface_error.value.category == "surface_schema_invalid"
    assert "missing wiki page" in str(surface_error.value)


@pytest.mark.parametrize(
    "relative_path",
    [
        "AGENTS.md",
        ".claude/skills/wiki/SKILL.md",
        ".llm-wiki/skills/wiki/SKILL.md",
        ".github/copilot-instructions.md",
        ".github/instructions/docs.instructions.md",
        "llm-wiki-inventory-cache.json",
        "__pycache__/cache.pyc",
        "_site/index.html",
    ],
)
def test_agent_policy_and_cache_content_is_rejected(
    tmp_path: Path, relative_path: str
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n")
    _write(wiki / Path(relative_path), "untrusted\n")

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace" / "wiki",
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == "rejected_input_entries"
    expected = relative_path.replace("\\", "/")
    assert any(
        expected == rejected or expected.startswith(f"{rejected}/")
        for rejected in exc_info.value.rejected_entries
    )
    assert not (tmp_path / "workspace").exists()


def test_every_symlink_is_rejected_even_when_it_stays_inside_input(
    tmp_path: Path,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n")
    _write(wiki / "guides" / "real.md", "# Real\n")
    link = wiki / "guides" / "alias.md"
    try:
        link.symlink_to("real.md")
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace" / "wiki",
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == "rejected_input_entries"
    assert exc_info.value.rejected_entries == ("guides/alias.md",)


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_copy_rejects_target_parent_redirected_after_input_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    _write(wiki / "index.md", "# Index\n")
    _write(wiki / "guides" / "page.md", "# Page\n")
    outside.mkdir()

    real_copy = wiki_input_module._copy_regular_file
    redirected = False

    def redirect_parent_after_inventory(
        entry,
        workspace_root,
        *,
        root_descriptor,
        root_identity,
    ):
        nonlocal redirected
        if entry.relative_path == "guides/page.md" and not redirected:
            redirected = True
            try:
                (workspace_root / "guides").symlink_to(
                    outside,
                    target_is_directory=True,
                )
            except (OSError, NotImplementedError) as exc:
                pytest.skip(f"directory symlinks unavailable: {exc}")
        return real_copy(
            entry,
            workspace_root,
            root_descriptor=root_descriptor,
            root_identity=root_identity,
        )

    monkeypatch.setattr(
        wiki_input_module,
        "_copy_regular_file",
        redirect_parent_after_inventory,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            workspace,
            freshness_policy="allow-unverified",
        )

    assert redirected is True
    assert exc_info.value.category == "workspace_redirection_rejected"
    assert not (outside / "page.md").exists()


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_descriptor_input_read_rejects_parent_swap_between_inspection_and_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not wiki_input_module._supports_secure_input_fd_traversal():
        pytest.skip("descriptor-rooted no-follow input traversal unavailable")

    wiki = tmp_path / "wiki"
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    held_parent = tmp_path / "guides-before-swap"
    _write(wiki / "index.md", "# Index\n")
    _write(wiki / "guides" / "page.md", "# Trusted page\n")
    _write(outside / "page.md", "# Redirected page\n")
    workspace.mkdir()

    input_identity = (wiki.stat().st_dev, wiki.stat().st_ino)
    real_copy_tree = wiki_input_module._copy_input_tree
    real_open = os.open
    copying = False
    swapped = False

    def mark_copy_phase(input_tree, workspace_root):
        nonlocal copying
        copying = True
        try:
            return real_copy_tree(input_tree, workspace_root)
        finally:
            copying = False

    def swap_input_parent_before_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if (
            path == "guides"
            and dir_fd is not None
            and copying
            and not swapped
            and (os.fstat(dir_fd).st_dev, os.fstat(dir_fd).st_ino) == input_identity
        ):
            swapped = True
            (wiki / "guides").replace(held_parent)
            try:
                (wiki / "guides").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                pytest.skip(f"directory symlinks unavailable: {exc}")
        if dir_fd is None:
            return real_open(path, flags, mode)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(wiki_input_module, "_copy_input_tree", mark_copy_phase)
    monkeypatch.setattr(os, "open", swap_input_parent_before_open)

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            workspace,
            freshness_policy="allow-unverified",
        )

    assert swapped is True
    assert exc_info.value.category == "input_changed_during_snapshot"
    assert list(workspace.iterdir()) == []
    assert (outside / "page.md").read_text(encoding="utf-8") == ("# Redirected page\n")


def test_mocked_windows_input_fallback_pins_root_parents_and_leaves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n")
    _write(wiki / "guides" / "page.md", "# Page\n")
    events: list[tuple[str, tuple[str, ...] | str]] = []
    active_guards = 0
    cached_stat_calls: list[Path] = []
    real_scandir = os.scandir

    class _ZeroIdentityEntry:
        def __init__(self, entry):
            self._entry = entry
            self.name = entry.name
            self.path = entry.path

        def stat(self, *, follow_symlinks=True):
            cached_stat_calls.append(Path(self.path))
            values = list(self._entry.stat(follow_symlinks=follow_symlinks))
            values[1] = 0
            values[2] = 0
            values[3] = 0
            return os.stat_result(values)

    class _ZeroIdentityScandir:
        def __init__(self, path):
            self._iterator = real_scandir(path)

        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _traceback):
            self._iterator.close()

        def __iter__(self):
            return (_ZeroIdentityEntry(entry) for entry in self._iterator)

    @contextmanager
    def fake_directory_guard(root, components, *, create_missing=False):
        nonlocal active_guards
        assert root == wiki
        assert create_missing is False
        key = tuple(components)
        active_guards += 1
        events.append(("directory-enter", key))
        try:
            yield root.joinpath(*key)
        finally:
            events.append(("directory-exit", key))
            active_guards -= 1

    @contextmanager
    def fake_file_guard(path):
        relative = path.relative_to(wiki).as_posix()
        events.append(("file-enter", relative))
        with path.open("rb") as handle:
            yield handle, os.fstat(handle.fileno())
        events.append(("file-exit", relative))

    monkeypatch.setattr(
        wiki_input_module,
        "_supports_secure_input_fd_traversal",
        lambda: False,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "_uses_windows_guarded_input_fallback",
        lambda: True,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "guard_windows_directory_chain",
        fake_directory_guard,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "open_windows_readonly_file",
        fake_file_guard,
    )
    monkeypatch.setattr(
        wiki_input_module.os,
        "scandir",
        _ZeroIdentityScandir,
    )

    with wiki_input_module._open_input_root_descriptor(
        wiki,
        expected_identity=wiki.lstat(),
    ) as root_descriptor:
        assert root_descriptor is None
        tree = wiki_input_module._collect_input_tree(
            wiki,
            enforce_content_policy=True,
        )
        assert {entry.relative_path for entry in tree.files} == {
            "guides/page.md",
            "index.md",
        }
        assert events[0] == ("directory-enter", ())
        assert active_guards == 1

    assert active_guards == 0
    assert events[-1] == ("directory-exit", ())
    assert ("directory-enter", ("guides",)) in events
    assert ("file-enter", "guides/page.md") in events
    assert cached_stat_calls == []


def test_mocked_windows_inventory_accepts_path_ctime_difference_and_uses_handle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    source_path = wiki / "index.md"
    _write(source_path, b"# Index\n")
    with source_path.open("rb") as baseline_handle:
        baseline_handle_stat = os.fstat(baseline_handle.fileno())
    path_stat = _stat_with(
        baseline_handle_stat,
        st_ctime_ns=baseline_handle_stat.st_ctime_ns + 1,
    )
    guarded_handle_stats: list[os.stat_result] = []
    real_fresh_stat = wiki_input_module.fresh_no_follow_stat

    @contextmanager
    def fake_directory_guard(root, components, *, create_missing=False):
        assert root == wiki
        assert create_missing is False
        yield root.joinpath(*components)

    @contextmanager
    def fake_file_guard(path):
        with path.open("rb") as handle:
            handle_stat = os.fstat(handle.fileno())
            guarded_handle_stats.append(handle_stat)
            yield handle, handle_stat

    def fake_fresh_stat(path):
        if Path(path) == source_path:
            return path_stat
        return real_fresh_stat(path)

    monkeypatch.setattr(
        wiki_input_module,
        "_uses_windows_guarded_input_fallback",
        lambda: True,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "guard_windows_directory_chain",
        fake_directory_guard,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "open_windows_readonly_file",
        fake_file_guard,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "fresh_no_follow_stat",
        fake_fresh_stat,
    )

    tree = wiki_input_module._collect_input_tree(
        wiki,
        enforce_content_policy=True,
    )

    assert len(tree.files) == 1
    assert guarded_handle_stats
    handle_stat = guarded_handle_stats[0]
    entry = tree.files[0]
    assert entry.ctime_ns == handle_stat.st_ctime_ns
    assert entry.ctime_ns != path_stat.st_ctime_ns
    assert (entry.device, entry.inode) == (handle_stat.st_dev, handle_stat.st_ino)
    assert wiki_input_module._read_verified_bytes(entry) == b"# Index\n"


@pytest.mark.parametrize("changed_field", ("st_size", "st_mtime_ns"))
def test_mocked_windows_leaf_guard_rejects_path_handle_metadata_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    changed_field: str,
) -> None:
    source_path = tmp_path / "wiki" / "index.md"
    _write(source_path, b"# Index\n")
    expected = source_path.stat()
    opened = _stat_with(
        expected,
        **{changed_field: getattr(expected, changed_field) + 1},
    )

    @contextmanager
    def fake_file_guard(path):
        with path.open("rb") as handle:
            yield handle, opened

    monkeypatch.setattr(
        wiki_input_module,
        "open_windows_readonly_file",
        fake_file_guard,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        with wiki_input_module._open_windows_input_leaf(
            source_path,
            "index.md",
            expected_stat=expected,
        ):
            pass

    assert exc_info.value.category == "input_changed_during_snapshot"


def test_mocked_windows_leaf_guard_rejects_same_handle_ctime_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "wiki" / "index.md"
    _write(source_path, b"# Index\n")
    opened = source_path.stat()
    changed = _stat_with(opened, st_ctime_ns=opened.st_ctime_ns + 1)

    class _OsProxy:
        def __getattr__(self, name):
            return getattr(os, name)

        def fstat(self, _descriptor):
            return changed

    @contextmanager
    def fake_file_guard(path):
        with path.open("rb") as handle:
            yield handle, opened

    monkeypatch.setattr(wiki_input_module, "os", _OsProxy())
    monkeypatch.setattr(
        wiki_input_module,
        "open_windows_readonly_file",
        fake_file_guard,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        with wiki_input_module._open_windows_input_leaf(
            source_path,
            "index.md",
            expected_stat=opened,
        ):
            pass

    assert exc_info.value.category == "input_changed_during_snapshot"


def test_mocked_windows_reopen_rejects_handle_ctime_change_with_same_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "wiki" / "index.md"
    contents = b"# Index\n"
    _write(source_path, contents)
    inventoried = source_path.stat()
    reopened = _stat_with(
        inventoried,
        st_ctime_ns=inventoried.st_ctime_ns + 1,
    )
    entry = wiki_input_module._InputFile(
        path=source_path,
        relative_path="index.md",
        sha256=_sha256(contents),
        size=inventoried.st_size,
        mtime_ns=inventoried.st_mtime_ns,
        ctime_ns=inventoried.st_ctime_ns,
        device=inventoried.st_dev,
        inode=inventoried.st_ino,
    )

    @contextmanager
    def fake_directory_guard(root, components, *, create_missing=False):
        assert root == source_path.parent
        assert components == ()
        assert create_missing is False
        yield root

    @contextmanager
    def fake_file_guard(path):
        with path.open("rb") as handle:
            yield handle, reopened

    monkeypatch.setattr(
        wiki_input_module,
        "_uses_windows_guarded_input_fallback",
        lambda: True,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "guard_windows_directory_chain",
        fake_directory_guard,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "open_windows_readonly_file",
        fake_file_guard,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        wiki_input_module._read_verified_bytes(entry)

    assert exc_info.value.category == "input_changed_during_snapshot"


def test_mocked_windows_leaf_guard_rejects_post_read_path_rebind(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "wiki" / "index.md"
    _write(source_path, b"# Index\n")
    opened = source_path.stat()
    rebound = _stat_with(opened, st_ino=opened.st_ino + 1)
    body_entered = False

    @contextmanager
    def fake_file_guard(path):
        with path.open("rb") as handle:
            yield handle, opened

    monkeypatch.setattr(
        wiki_input_module,
        "open_windows_readonly_file",
        fake_file_guard,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "fresh_no_follow_stat",
        lambda _path: rebound,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        with wiki_input_module._open_windows_input_leaf(
            source_path,
            "index.md",
            expected_stat=opened,
        ):
            body_entered = True

    assert body_entered is True
    assert exc_info.value.category == "input_changed_during_snapshot"


def test_mocked_windows_leaf_guard_maps_post_read_path_disappearance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "wiki" / "index.md"
    _write(source_path, b"# Index\n")
    opened = source_path.stat()

    @contextmanager
    def fake_file_guard(path):
        with path.open("rb") as handle:
            yield handle, opened

    def missing_path(_path):
        raise FileNotFoundError("injected post-read disappearance")

    monkeypatch.setattr(
        wiki_input_module,
        "open_windows_readonly_file",
        fake_file_guard,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "fresh_no_follow_stat",
        missing_path,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        with wiki_input_module._open_windows_input_leaf(
            source_path,
            "index.md",
            expected_stat=opened,
        ):
            pass

    assert exc_info.value.category == "input_changed_during_snapshot"


def test_mocked_windows_file_guard_preserves_body_oserror(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "page.md"
    _write(source_path, "# Page\n")

    class _WindowsOsProxy:
        name = "nt"

        def __getattr__(self, name):
            return getattr(os, name)

    monkeypatch.setattr(filesystem_guard_module, "os", _WindowsOsProxy())
    monkeypatch.setattr(
        filesystem_guard_module,
        "_open_windows_readonly_file_handle",
        lambda path: os.open(path, os.O_RDONLY),
    )
    monkeypatch.setitem(
        sys.modules,
        "msvcrt",
        SimpleNamespace(open_osfhandle=lambda handle, _flags: handle),
    )

    body_error = OSError("destination write failed")
    with pytest.raises(OSError) as exc_info:
        with filesystem_guard_module.open_windows_readonly_file(source_path):
            raise body_error

    assert exc_info.value is body_error


@pytest.mark.parametrize("zero_component", ("device", "file_id"))
def test_mocked_windows_file_guard_rejects_zero_handle_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    zero_component: str,
) -> None:
    source_path = tmp_path / "page.md"
    _write(source_path, "# Page\n")

    class _WindowsOsProxy:
        name = "nt"

        def __getattr__(self, name):
            return getattr(os, name)

        def fstat(self, descriptor):
            values = list(os.fstat(descriptor))
            values[1 if zero_component == "file_id" else 2] = 0
            return os.stat_result(values)

    monkeypatch.setattr(filesystem_guard_module, "os", _WindowsOsProxy())
    monkeypatch.setattr(
        filesystem_guard_module,
        "_open_windows_readonly_file_handle",
        lambda path: os.open(path, os.O_RDONLY),
    )
    monkeypatch.setitem(
        sys.modules,
        "msvcrt",
        SimpleNamespace(open_osfhandle=lambda handle, _flags: handle),
    )

    with pytest.raises(
        filesystem_guard_module.WindowsFileGuardError,
        match="identity is unavailable",
    ):
        with filesystem_guard_module.open_windows_readonly_file(source_path):
            pass


def test_mocked_windows_root_guard_preserves_body_oserror(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "trusted\n")

    @contextmanager
    def fake_directory_guard(root, components, *, create_missing=False):
        assert root == wiki
        assert components == ()
        assert create_missing is False
        yield root

    monkeypatch.setattr(
        wiki_input_module,
        "_supports_secure_input_fd_traversal",
        lambda: False,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "_uses_windows_guarded_input_fallback",
        lambda: True,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "guard_windows_directory_chain",
        fake_directory_guard,
    )

    body_error = OSError("workspace creation failed")
    with pytest.raises(OSError) as exc_info:
        with wiki_input_module._open_input_root_descriptor(
            wiki,
            expected_identity=wiki.lstat(),
        ):
            raise body_error

    assert exc_info.value is body_error


def test_mocked_windows_leaf_guard_rejects_same_size_identity_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_path = tmp_path / "wiki" / "index.md"
    replacement = tmp_path / "outside" / "index.md"
    _write(expected_path, "trusted\n")
    _write(replacement, "outside\n")
    assert expected_path.stat().st_size == replacement.stat().st_size

    @contextmanager
    def open_replacement(_path):
        with replacement.open("rb") as handle:
            yield handle, os.fstat(handle.fileno())

    monkeypatch.setattr(
        wiki_input_module,
        "open_windows_readonly_file",
        open_replacement,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        with wiki_input_module._open_windows_input_leaf(
            expected_path,
            "index.md",
            expected_stat=expected_path.stat(),
        ):
            pass

    assert exc_info.value.category == "input_changed_during_snapshot"


def test_mocked_windows_root_guard_rejects_replacement_before_pin_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    held = tmp_path / "held"
    _write(wiki / "index.md", "trusted\n")
    expected = wiki.lstat()

    @contextmanager
    def replacing_guard(root, components, *, create_missing=False):
        assert components == ()
        assert create_missing is False
        root.replace(held)
        _write(root / "index.md", "outside\n")
        yield root

    monkeypatch.setattr(
        wiki_input_module,
        "_supports_secure_input_fd_traversal",
        lambda: False,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "_uses_windows_guarded_input_fallback",
        lambda: True,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "guard_windows_directory_chain",
        replacing_guard,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        with wiki_input_module._open_input_root_descriptor(
            wiki,
            expected_identity=expected,
        ):
            pass

    assert exc_info.value.category == "input_changed_during_snapshot"


def test_mocked_windows_root_guard_unavailable_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "trusted\n")

    @contextmanager
    def unavailable_guard(_root, _components, *, create_missing=False):
        assert create_missing is False
        raise filesystem_guard_module._WindowsDirectoryGuardUnavailableError(
            "list-directory access denied"
        )
        yield  # pragma: no cover

    monkeypatch.setattr(
        wiki_input_module,
        "_supports_secure_input_fd_traversal",
        lambda: False,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "_uses_windows_guarded_input_fallback",
        lambda: True,
    )
    monkeypatch.setattr(
        wiki_input_module,
        "guard_windows_directory_chain",
        unavailable_guard,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        with wiki_input_module._open_input_root_descriptor(
            wiki,
            expected_identity=wiki.lstat(),
        ):
            pass

    assert exc_info.value.category == "secure_input_traversal_unavailable"


@pytest.mark.skipif(os.name != "nt", reason="Windows guard semantics only")
def test_windows_input_root_guard_blocks_replacement(tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    held = tmp_path / "held"
    _write(wiki / "index.md", "trusted\n")

    with wiki_input_module._open_input_root_descriptor(
        wiki,
        expected_identity=wiki.lstat(),
    ):
        with pytest.raises(OSError):
            wiki.replace(held)

    wiki.replace(held)
    assert held.is_dir()
    assert not wiki.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction semantics only")
def test_windows_input_inventory_rejects_junction(tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    outside = tmp_path / "outside"
    _write(wiki / "index.md", "# Index\n")
    _write(outside / "page.md", "# Outside\n")
    junction = wiki / "guides"
    completed = subprocess.run(
        [
            "cmd.exe",
            "/d",
            "/c",
            "mklink",
            "/J",
            str(junction),
            str(outside),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        pytest.skip(f"junction creation is unavailable: {completed.stderr.strip()}")

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        fingerprint_documentation_wiki_input(wiki)

    assert exc_info.value.category == "rejected_input_entries"
    assert exc_info.value.rejected_entries == ("guides",)


def test_input_root_replacement_before_descriptor_open_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    held_wiki = tmp_path / "wiki-before-swap"
    workspace = tmp_path / "workspace"
    _write(wiki / "index.md", "# Trusted index\n")

    real_validate_workspace = wiki_input_module._validate_workspace_root
    swapped = False

    def swap_after_input_validation(path):
        nonlocal swapped
        swapped = True
        wiki.replace(held_wiki)
        _write(wiki / "index.md", "# Redirected index\n")
        return real_validate_workspace(path)

    monkeypatch.setattr(
        wiki_input_module,
        "_validate_workspace_root",
        swap_after_input_validation,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            workspace,
            freshness_policy="allow-unverified",
        )

    assert swapped is True
    assert exc_info.value.category == "input_changed_during_snapshot"
    assert not workspace.exists()
    assert (held_wiki / "index.md").read_text(encoding="utf-8") == ("# Trusted index\n")


@pytest.mark.parametrize("workspace_preexisted", [False, True])
def test_failed_initial_adoption_rolls_back_partial_workspace_and_can_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    workspace_preexisted: bool,
) -> None:
    wiki = tmp_path / "wiki"
    workspace = tmp_path / "workspace" / "wiki"
    _write(wiki / "index.md", "# Index\n")
    _write(wiki / "guides" / "page.md", "# Page\n")
    if workspace_preexisted:
        workspace.mkdir(parents=True)

    real_copy = wiki_input_module._copy_regular_file
    failed = False

    def fail_after_partial_copy(
        entry,
        workspace_root,
        *,
        root_descriptor,
        root_identity,
    ):
        nonlocal failed
        if entry.relative_path == "index.md" and not failed:
            failed = True
            raise DocumentationWikiInputError(
                "Injected copy failure after a prior file was copied.",
                category="injected_copy_failure",
                path=entry.relative_path,
            )
        return real_copy(
            entry,
            workspace_root,
            root_descriptor=root_descriptor,
            root_identity=root_identity,
        )

    monkeypatch.setattr(
        wiki_input_module,
        "_copy_regular_file",
        fail_after_partial_copy,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            workspace,
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == "injected_copy_failure"
    assert workspace.exists() is workspace_preexisted
    if workspace_preexisted:
        assert list(workspace.iterdir()) == []

    monkeypatch.setattr(wiki_input_module, "_copy_regular_file", real_copy)
    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        workspace,
        freshness_policy="allow-unverified",
    )

    assert snapshot.input_tree_hash == snapshot.initial_snapshot_hash
    assert _tree_bytes(workspace) == _tree_bytes(wiki)


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_descriptor_copy_rejects_parent_swap_between_inspection_and_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not wiki_input_module._supports_secure_directory_fd_copy():
        pytest.skip("descriptor-relative no-follow directory opens unavailable")

    wiki = tmp_path / "wiki"
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    held_parent = workspace / "guides-before-swap"
    _write(wiki / "index.md", "# Index\n")
    _write(wiki / "guides" / "page.md", "# Page\n")
    outside.mkdir()

    real_open = os.open
    swapped = False

    def swap_parent_before_directory_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if (
            path == "guides"
            and dir_fd is not None
            and not swapped
            and (workspace / "guides").exists()
        ):
            swapped = True
            (workspace / "guides").replace(held_parent)
            try:
                (workspace / "guides").symlink_to(
                    outside,
                    target_is_directory=True,
                )
            except (OSError, NotImplementedError) as exc:
                pytest.skip(f"directory symlinks unavailable: {exc}")
        if dir_fd is None:
            return real_open(path, flags, mode)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", swap_parent_before_directory_open)

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            workspace,
            freshness_policy="allow-unverified",
        )

    assert swapped is True
    assert exc_info.value.category == "workspace_redirection_rejected"
    assert not (outside / "page.md").exists()
    assert not (held_parent / "page.md").exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction semantics only")
def test_copy_rejects_target_parent_replaced_with_windows_junction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki = tmp_path / "wiki"
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    _write(wiki / "index.md", "# Index\n")
    _write(wiki / "guides" / "page.md", "# Page\n")
    outside.mkdir()

    real_copy = wiki_input_module._copy_regular_file
    redirected = False

    def redirect_parent_after_inventory(
        entry,
        workspace_root,
        *,
        root_descriptor,
        root_identity,
    ):
        nonlocal redirected
        if entry.relative_path == "guides/page.md" and not redirected:
            redirected = True
            junction = workspace_root / "guides"
            completed = subprocess.run(
                [
                    "cmd.exe",
                    "/d",
                    "/c",
                    "mklink",
                    "/J",
                    str(junction),
                    str(outside),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode:
                pytest.skip(
                    f"junction creation is unavailable: {completed.stderr.strip()}"
                )
        return real_copy(
            entry,
            workspace_root,
            root_descriptor=root_descriptor,
            root_identity=root_identity,
        )

    monkeypatch.setattr(
        wiki_input_module,
        "_copy_regular_file",
        redirect_parent_after_inventory,
    )

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            workspace,
            freshness_policy="allow-unverified",
        )

    assert redirected is True
    assert exc_info.value.category == "workspace_redirection_rejected"
    assert not (outside / "page.md").exists()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs unavailable")
def test_non_regular_input_is_rejected(tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n")
    fifo = wiki / "stream"
    os.mkfifo(fifo)

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace" / "wiki",
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == "rejected_input_entries"
    assert exc_info.value.rejected_entries == ("stream",)


def test_workspace_must_not_overlap_input_or_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    wiki = source / "docs" / "wiki"
    _write(source / "app.py", b"pass\n")
    _write(wiki / "index.md", "# Index\n")

    with pytest.raises(DocumentationWikiInputError) as input_overlap:
        adopt_documentation_wiki_snapshot(
            wiki,
            wiki / "snapshot",
            freshness_policy="allow-unverified",
        )
    assert input_overlap.value.category == "workspace_input_overlap"

    with pytest.raises(DocumentationWikiInputError) as source_overlap:
        adopt_documentation_wiki_snapshot(
            wiki,
            source / "workspace" / "wiki",
            source_root=source,
            freshness_policy="allow-unverified",
        )
    assert source_overlap.value.category == "workspace_source_overlap"


def test_nonempty_workspace_is_not_overwritten(tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    workspace = tmp_path / "workspace"
    _write(wiki / "index.md", "# Index\n")
    _write(workspace / "keep.txt", "user content\n")

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            workspace,
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == "workspace_not_empty"
    assert (workspace / "keep.txt").read_text(encoding="utf-8") == "user content\n"


@pytest.mark.parametrize(
    "target",
    [
        "../../outside.md",
        "/etc/passwd",
        "C:/Windows/System32/drivers/etc/hosts",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "guides/CON.md",
        "guides/page.:1",
    ],
)
def test_import_rejects_unsafe_markdown_link_targets(
    tmp_path: Path,
    target: str,
) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "guides" / "start.md", f"# Start\n\n[unsafe]({target})\n")
    _write(wiki / "index.md", "# Index\n")

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace" / "wiki",
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == "unsafe_markdown_link"
    assert exc_info.value.path == "guides/start.md"
    assert not (tmp_path / "workspace").exists()


def test_import_allows_root_bounded_relative_and_safe_external_links(
    tmp_path: Path,
) -> None:
    wiki = tmp_path / "wiki"
    _write(
        wiki / "guides" / "start.md",
        "# Start\n\n[Index](../index.md) [web](https://example.com/docs) "
        "[mail](mailto:docs@example.com)\n",
    )
    _write(wiki / "index.md", "# Index\n")

    snapshot = adopt_documentation_wiki_snapshot(
        wiki,
        tmp_path / "workspace" / "wiki",
        freshness_policy="allow-unverified",
    )

    assert snapshot.semantic_markdown_paths == ("guides/start.md", "index.md")


def test_manifest_source_paths_are_path_safe(tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    _write(wiki / "index.md", "# Index\n")
    _write_current_metadata(wiki, {"../outside.py": "sha256:" + "0" * 64})

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace",
            freshness_policy="allow-unverified",
        )

    assert exc_info.value.category == "manifest_schema_invalid"
    assert "unsafe source path" in str(exc_info.value)


def test_missing_index_and_invalid_policy_fail_actionably(tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    wiki.mkdir()

    with pytest.raises(DocumentationWikiInputError) as missing:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace",
            freshness_policy="allow-unverified",
        )
    assert missing.value.category == "missing_index"

    _write(wiki / "index.md", "# Index\n")
    with pytest.raises(DocumentationWikiInputError) as policy:
        adopt_documentation_wiki_snapshot(
            wiki,
            tmp_path / "workspace",
            freshness_policy="guess",
        )
    assert policy.value.category == "invalid_freshness_policy"
