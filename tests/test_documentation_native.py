"""Focused tests for controller-owned native evaluation and refresh."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.commands.bootstrap_cmd import execute_bootstrap
from llm_wiki_cli.services import (
    documentation_native,
    source_snapshot as source_snapshot_module,
)
from llm_wiki_cli.services.bootstrap_service import BootstrapRequest
from llm_wiki_cli.services.documentation_native import (
    DocumentationNativeError,
    evaluate_documentation_native_freshness,
    refresh_documentation_native_projection,
)
from llm_wiki_cli.services.knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    CommitStage,
)
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeMismatchPolicy,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.services.sync_manifest import (
    MANIFEST_FILENAME,
    SyncManifest,
)
from llm_wiki_cli.services.wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
)


def _bootstrap_native(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text(
        (
            '"""Example application."""\n\n'
            '__all__ = ["run"]\n\n'
            "def run(value: str) -> str:\n"
            "    return normalize(value)\n\n"
            "def normalize(value: str) -> str:\n"
            "    return value.strip()\n"
        ),
        encoding="utf-8",
    )
    wiki = tmp_path / "wiki"
    execute_bootstrap(
        BootstrapRequest(
            source_root=source,
            wiki_root=wiki,
            source_adapter=True,
        )
    )
    return source, wiki


def _bootstrap_native_with_openapi(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text(
        (
            "from fastapi import FastAPI\n\n"
            "app = FastAPI()\n\n"
            '@app.get("/items", operation_id="list_items")\n'
            "def list_items():\n"
            "    return []\n"
        ),
        encoding="utf-8",
    )
    (source / "openapi.json").write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Example", "version": "1.0.0"},
                "paths": {
                    "/items": {
                        "get": {
                            "operationId": "list_items",
                            "responses": {"200": {"description": "OK"}},
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    wiki = tmp_path / "wiki"
    execute_bootstrap(
        BootstrapRequest(
            source_root=source,
            wiki_root=wiki,
            source_adapter=True,
            api_contracts=True,
            openapi_file="openapi.json",
        )
    )
    return source, wiki


def _loaded_native(wiki: Path):
    loaded = load_knowledge_state(wiki)
    assert loaded.status is KnowledgeLoadState.VALID
    assert loaded.knowledge is not None
    assert loaded.manifest_basis is not None
    return loaded.knowledge, loaded.manifest_basis


def _markdown_bytes(wiki: Path) -> dict[str, bytes]:
    return {
        path.relative_to(wiki).as_posix(): path.read_bytes()
        for path in sorted(wiki.rglob("*.md"))
    }


def test_freshness_uses_one_deep_plugin_filtered_inventory(
    tmp_path, monkeypatch
):
    source, wiki = _bootstrap_native(tmp_path)
    knowledge, manifest = _loaded_native(wiki)
    calls = {"snapshot": 0, "inventory": 0}
    requests = []
    real_snapshot = documentation_native.build_source_snapshot
    real_inventory = extract_cmd.get_inventory_result

    def counted_snapshot(*args, **kwargs):
        calls["snapshot"] += 1
        return real_snapshot(*args, **kwargs)

    def counted_inventory(request):
        calls["inventory"] += 1
        requests.append(request)
        return real_inventory(request)

    monkeypatch.setattr(
        documentation_native,
        "build_source_snapshot",
        counted_snapshot,
    )
    monkeypatch.setattr(extract_cmd, "get_inventory_result", counted_inventory)

    freshness = evaluate_documentation_native_freshness(
        knowledge=knowledge,
        manifest=manifest,
        source_root=source,
    )

    assert freshness.current
    assert freshness.reasons == ()
    assert freshness.source_mismatches == ()
    assert calls == {"snapshot": 1, "inventory": 1}
    assert len(requests) == 1
    assert requests[0].deep is True
    assert requests[0].include_plugins is False
    assert requests[0].include_tests == frozenset()


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("added", "added:added.py"),
        ("removed", "removed:app.py"),
        ("changed", "changed:app.py"),
    ],
)
def test_freshness_reports_exact_source_inventory_mismatches(
    tmp_path,
    mutation,
    expected,
):
    source, wiki = _bootstrap_native(tmp_path)
    knowledge, manifest = _loaded_native(wiki)
    if mutation == "added":
        (source / "added.py").write_text("VALUE = 1\n", encoding="utf-8")
    elif mutation == "removed":
        (source / "app.py").unlink()
    else:
        (source / "app.py").write_text(
            (source / "app.py").read_text(encoding="utf-8") + "\n# changed\n",
            encoding="utf-8",
        )

    freshness = evaluate_documentation_native_freshness(
        knowledge=knowledge,
        manifest=manifest,
        source_root=source,
    )

    assert not freshness.current
    assert expected in freshness.source_mismatches
    assert expected in freshness.reasons


def test_freshness_independently_detects_generation_and_producer_drift(tmp_path):
    source, wiki = _bootstrap_native(tmp_path)
    knowledge, manifest = _loaded_native(wiki)
    changed_surfaces = {
        **manifest.surfaces,
        "flows": {
            **manifest.surfaces["flows"],
            "enabled": not manifest.surfaces["flows"]["enabled"],
        },
    }
    changed_manifest = manifest.with_generation_state(
        surfaces=changed_surfaces,
        generation_inputs=manifest.generation_inputs,
    )

    generation = evaluate_documentation_native_freshness(
        knowledge=knowledge,
        manifest=changed_manifest,
        source_root=source,
    )

    changed_tool = replace(
        knowledge.bundle.producer.tool,
        version="different-version",
    )
    changed_knowledge = replace(
        knowledge,
        bundle=replace(
            knowledge.bundle,
            producer=replace(
                knowledge.bundle.producer,
                tool=changed_tool,
            ),
        ),
    )
    producer = evaluate_documentation_native_freshness(
        knowledge=changed_knowledge,
        manifest=manifest,
        source_root=source,
    )

    assert not generation.current
    assert "generation-options-changed" in generation.reasons
    assert not producer.current
    assert "producer-basis-changed" in producer.reasons


def test_freshness_reports_exact_openapi_generation_input_drift(tmp_path):
    source, wiki = _bootstrap_native_with_openapi(tmp_path)
    knowledge, manifest = _loaded_native(wiki)
    openapi_path = source / "openapi.json"
    payload = json.loads(openapi_path.read_text(encoding="utf-8"))
    payload["info"]["version"] = "2.0.0"
    openapi_path.write_text(json.dumps(payload), encoding="utf-8")

    freshness = evaluate_documentation_native_freshness(
        knowledge=knowledge,
        manifest=manifest,
        source_root=source,
    )

    mismatch = "generation_input_changed:openapi:openapi.json"
    assert not freshness.current
    assert mismatch in freshness.source_mismatches
    assert mismatch in freshness.reasons


def test_selection_mismatch_is_explicit_and_refresh_updates_identity(
    tmp_path,
    monkeypatch,
):
    source, wiki = _bootstrap_native(tmp_path)
    knowledge, manifest = _loaded_native(wiki)
    (source / "pyproject.toml").write_text(
        '[project.scripts]\nexcluded-command = "app:run"\n',
        encoding="utf-8",
    )
    profile = source / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["app.py"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    observed_console_scripts = []
    real_read_console_scripts = documentation_native.read_console_scripts

    def selected_console_scripts(project_root, *, source_snapshot=None):
        scripts = real_read_console_scripts(
            project_root,
            source_snapshot=source_snapshot,
        )
        observed_console_scripts.append((source_snapshot, scripts))
        return scripts

    monkeypatch.setattr(
        documentation_native,
        "read_console_scripts",
        selected_console_scripts,
    )

    with pytest.raises(DocumentationNativeError, match="source-selection"):
        evaluate_documentation_native_freshness(
            knowledge=knowledge,
            manifest=manifest,
            source_root=source,
        )

    refresh_documentation_native_projection(
        source_root=source,
        wiki_root=wiki,
    )
    refreshed_knowledge, refreshed_manifest = _loaded_native(wiki)
    assert refreshed_manifest.generation_inputs["source_selection"] == (
        build_source_snapshot(source).source_selection_identity
    )
    current = evaluate_documentation_native_freshness(
        knowledge=refreshed_knowledge,
        manifest=refreshed_manifest,
        source_root=source,
    )
    assert current.current
    assert observed_console_scripts
    assert all(snapshot is not None for snapshot, _ in observed_console_scripts)
    assert all(scripts == [] for _, scripts in observed_console_scripts)


def test_selection_control_change_is_explicit_native_freshness_mismatch(
    tmp_path,
):
    source, wiki = _bootstrap_native(tmp_path)
    profile = source / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["app.py"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    refresh_documentation_native_projection(source_root=source, wiki_root=wiki)
    knowledge, manifest = _loaded_native(wiki)
    (source / ".gitignore").write_text("not-present.py\n", encoding="utf-8")

    with pytest.raises(DocumentationNativeError, match="source-selection inputs"):
        evaluate_documentation_native_freshness(
            knowledge=knowledge,
            manifest=manifest,
            source_root=source,
        )


@pytest.mark.parametrize("operation", ["evaluate", "refresh"])
def test_native_control_broadening_rejects_before_new_source_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    source, wiki = _bootstrap_native(tmp_path)
    secret = source / "secret.py"
    secret.write_text("MUST_NOT_READ = True\n", encoding="utf-8")
    ignore = source / ".gitignore"
    ignore.write_text("secret.py\n", encoding="utf-8")
    profile = source / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["app.py", "secret.py"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    refresh_documentation_native_projection(source_root=source, wiki_root=wiki)
    knowledge, manifest = _loaded_native(wiki)
    ignore.write_text("", encoding="utf-8")
    real_hash = source_snapshot_module._sha256_file

    def guarded_hash(path: Path) -> str:
        if path == secret:
            pytest.fail("newly admitted source must not be hashed before rejection")
        return real_hash(path)

    monkeypatch.setattr(source_snapshot_module, "_sha256_file", guarded_hash)

    with pytest.raises(DocumentationNativeError, match="source-selection inputs"):
        if operation == "evaluate":
            evaluate_documentation_native_freshness(
                knowledge=knowledge,
                manifest=manifest,
                source_root=source,
            )
        else:
            refresh_documentation_native_projection(
                source_root=source,
                wiki_root=wiki,
            )


def test_refresh_does_not_read_persisted_openapi_after_selection_excludes_it(
    tmp_path,
) -> None:
    source, wiki = _bootstrap_native_with_openapi(tmp_path)
    profile = source / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["app.py"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        DocumentationNativeError,
        match="OpenAPI file is outside the selected source set",
    ):
        refresh_documentation_native_projection(
            source_root=source,
            wiki_root=wiki,
        )


def test_refresh_preserves_markdown_and_is_current_and_idempotent(tmp_path):
    source, wiki = _bootstrap_native(tmp_path)
    index = wiki / "index.md"
    index.write_text(
        index.read_text(encoding="utf-8") + "\nSemantic owner note.\n",
        encoding="utf-8",
    )
    markdown = _markdown_bytes(wiki)

    first = refresh_documentation_native_projection(
        source_root=source,
        wiki_root=wiki,
    )

    assert first.changed
    assert first.markdown_before == first.markdown_after
    assert _markdown_bytes(wiki) == markdown
    assert set(first.artifact_hashes_before) == {
        SURFACE_INDEX_FILENAME,
        KNOWLEDGE_INDEX_FILENAME,
        MANIFEST_FILENAME,
    }
    assert first.artifact_hashes == first.artifact_hashes_after
    knowledge, manifest = _loaded_native(wiki)
    freshness = evaluate_documentation_native_freshness(
        knowledge=knowledge,
        manifest=manifest,
        source_root=source,
    )
    assert freshness.current

    second = refresh_documentation_native_projection(
        source_root=source,
        wiki_root=wiki,
    )

    assert not second.changed
    assert second.artifact_hashes_before == second.artifact_hashes_after
    assert _markdown_bytes(wiki) == markdown


def test_refresh_fault_after_knowledge_write_leaves_old_manifest_fail_closed(
    tmp_path,
):
    source, wiki = _bootstrap_native(tmp_path)
    index = wiki / "index.md"
    index.write_text(
        index.read_text(encoding="utf-8") + "\nSemantic owner note.\n",
        encoding="utf-8",
    )
    manifest_before = (wiki / MANIFEST_FILENAME).read_bytes()

    def fail_after_knowledge(stage):
        if stage is CommitStage.KNOWLEDGE_INDEX_WRITTEN:
            raise RuntimeError("injected interruption")

    with pytest.raises(DocumentationNativeError, match="injected interruption"):
        refresh_documentation_native_projection(
            source_root=source,
            wiki_root=wiki,
            fault_injector=fail_after_knowledge,
        )

    assert (wiki / MANIFEST_FILENAME).read_bytes() == manifest_before
    degraded = load_knowledge_state(
        wiki,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )
    assert degraded.status is not KnowledgeLoadState.VALID


@pytest.mark.parametrize(
    "surface_schema",
    ["llm-wiki-surface/v1", WIKI_SURFACE_INDEX_SCHEMA_VERSION],
)
def test_refresh_upgrades_a_coherent_v4_pair_without_touching_markdown(
    tmp_path,
    surface_schema,
):
    source, wiki = _bootstrap_native(tmp_path)
    manifest = SyncManifest.load(wiki)
    v4_payload = {
        "version": 4,
        "sources": manifest.sources,
        "surfaces": manifest.surfaces,
        "generation_inputs": manifest.generation_inputs,
    }
    (wiki / MANIFEST_FILENAME).write_text(
        json.dumps(v4_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (wiki / SURFACE_INDEX_FILENAME).write_text(
        json.dumps(
            {
                "schema_version": surface_schema,
                "pages": [
                    {
                        "canonical_path": "modules/app.md",
                        "source_path": "app.py",
                    }
                ],
                "flows": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (wiki / KNOWLEDGE_INDEX_FILENAME).unlink()
    markdown = _markdown_bytes(wiki)

    refresh = refresh_documentation_native_projection(
        source_root=source,
        wiki_root=wiki,
    )

    assert refresh.changed
    assert KNOWLEDGE_INDEX_FILENAME not in refresh.artifact_hashes_before
    assert set(refresh.artifact_hashes_after) == {
        SURFACE_INDEX_FILENAME,
        KNOWLEDGE_INDEX_FILENAME,
        MANIFEST_FILENAME,
    }
    assert _markdown_bytes(wiki) == markdown
    knowledge, current_manifest = _loaded_native(wiki)
    assert evaluate_documentation_native_freshness(
        knowledge=knowledge,
        manifest=current_manifest,
        source_root=source,
    ).current


def test_refresh_upgrades_a_markerless_v5_surface_without_touching_markdown(
    tmp_path,
):
    source, wiki = _bootstrap_native(tmp_path)
    manifest = SyncManifest.load(wiki)
    (wiki / MANIFEST_FILENAME).write_text(
        manifest.without_artifact_hashes().to_json(),
        encoding="utf-8",
    )
    (wiki / KNOWLEDGE_INDEX_FILENAME).unlink()
    markdown = _markdown_bytes(wiki)

    refresh = refresh_documentation_native_projection(
        source_root=source,
        wiki_root=wiki,
    )

    assert refresh.changed
    assert KNOWLEDGE_INDEX_FILENAME not in refresh.artifact_hashes_before
    assert set(refresh.artifact_hashes_after) == {
        SURFACE_INDEX_FILENAME,
        KNOWLEDGE_INDEX_FILENAME,
        MANIFEST_FILENAME,
    }
    assert _markdown_bytes(wiki) == markdown
    knowledge, current_manifest = _loaded_native(wiki)
    assert evaluate_documentation_native_freshness(
        knowledge=knowledge,
        manifest=current_manifest,
        source_root=source,
    ).current


def test_refresh_rejects_a_corrupt_markerless_v5_surface(tmp_path):
    source, wiki = _bootstrap_native(tmp_path)
    manifest = SyncManifest.load(wiki)
    (wiki / MANIFEST_FILENAME).write_text(
        manifest.without_artifact_hashes().to_json(),
        encoding="utf-8",
    )
    (wiki / KNOWLEDGE_INDEX_FILENAME).unlink()
    (wiki / SURFACE_INDEX_FILENAME).write_text(
        '{"schema_version":"llm-wiki-surface-index/v1","pages":[]}\n',
        encoding="utf-8",
    )
    manifest_before = (wiki / MANIFEST_FILENAME).read_bytes()
    markdown = _markdown_bytes(wiki)

    with pytest.raises(
        DocumentationNativeError,
        match="unmarked surface index is invalid",
    ):
        refresh_documentation_native_projection(
            source_root=source,
            wiki_root=wiki,
        )

    assert not (wiki / KNOWLEDGE_INDEX_FILENAME).exists()
    assert (wiki / MANIFEST_FILENAME).read_bytes() == manifest_before
    assert _markdown_bytes(wiki) == markdown


def test_refresh_rejects_a_partial_marked_native_set(tmp_path):
    source, wiki = _bootstrap_native(tmp_path)
    (wiki / KNOWLEDGE_INDEX_FILENAME).unlink()

    with pytest.raises(
        DocumentationNativeError,
        match="incomplete before refresh",
    ):
        refresh_documentation_native_projection(
            source_root=source,
            wiki_root=wiki,
        )
