"""Versioned input commitments for conservative, validated sync no-ops."""

from __future__ import annotations

import os
import sys
import hashlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, replace
from pathlib import Path

from .. import __version__
from .contracts import KNOWLEDGE_REUSE_SCHEMA_VERSION
from .knowledge_evidence import hash_json, is_valid_sha256, sha256_bytes

REUSE_INPUT_KEY = "knowledge_reuse"
REUSE_EXTENSION_KEY = "llm-wiki/knowledge-reuse-v1"
_HASH_FIELDS = frozenset(
    {
        "source_snapshot_hash",
        "inventory_hash",
        "generation_options_hash",
        "implementation_hash",
        "markdown_snapshot_hash",
        "assets_hash",
        "repository_hash",
        "lifecycle_hash",
        "observation_inputs_hash",
    }
)
_STABLE_IMPLEMENTATION_GAPS = frozenset(
    {
        "observation-limit",
        "object-limit",
        "unsupported-syntax",
        "unsupported-producer",
        "unsupported-language",
        "ambiguous-owner",
    }
)


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def validate_reuse_commitment(value: object) -> dict:
    if not isinstance(value, Mapping) or set(value) != _HASH_FIELDS | {
        "schema_version"
    }:
        raise ValueError(
            "knowledge reuse must contain the exact versioned input commitments"
        )
    if value["schema_version"] != KNOWLEDGE_REUSE_SCHEMA_VERSION:
        raise ValueError("unsupported knowledge reuse schema")
    if any(not is_valid_sha256(value[field]) for field in _HASH_FIELDS):
        raise ValueError("knowledge reuse inputs must be SHA-256 commitments")
    return dict(value)


def manifest_lifecycle_hash(manifest) -> str:
    payload = manifest.to_payload()
    payload.pop("artifact_hashes", None)
    generation_inputs = dict(payload["generation_inputs"])
    generation_inputs.pop(REUSE_INPUT_KEY, None)
    payload["generation_inputs"] = generation_inputs
    return hash_json(payload)


def repository_input_hash(record) -> str:
    # Hash the normalized public record, never raw remotes or credentials.
    return hash_json(asdict(replace(record, evaluated_revision="unknown")))


def implementation_hash() -> str | None:
    """Fingerprint installed implementation inputs, without a process-global cache."""
    root = Path(__file__).resolve().parents[1]
    hashes = {}
    try:
        for directory, names, files in os.walk(root):
            names[:] = sorted(
                name
                for name in names
                if name not in {"__pycache__", "node_modules", "target", ".git"}
            )
            for filename in sorted(files):
                path = Path(directory) / filename
                if path.suffix == ".pyc":
                    continue
                hashes[path.relative_to(root).as_posix()] = _file_hash(path)
    except OSError:
        return None
    if not hashes:
        return None
    return hash_json(
        {"files": hashes, "python": list(sys.version_info[:3]), "tool": __version__}
    )


def wiki_input_hashes(wiki_dir: str | Path) -> tuple[str, str]:
    from .io import read_md
    from .knowledge_envelope import hash_markdown_snapshot
    from .validation import resolve_portable_workspace_path
    from .wiki_media import build_asset_index
    from .wiki_surface import collect_wiki_pages

    root = Path(wiki_dir)
    content = {
        page.relative_path: read_md(page.path) for page in collect_wiki_pages(root)
    }
    assets = build_asset_index(root, content)
    asset_hashes = {}
    for relative in sorted(assets.existing_paths):
        path = resolve_portable_workspace_path(
            root,
            relative,
            path_error=ValueError("invalid reuse asset path"),
            escape_error=ValueError("reuse asset escapes the wiki"),
        )
        asset_hashes[relative] = _file_hash(path)
    return hash_markdown_snapshot(content), hash_json(asset_hashes)


def bind_reuse_commitment(basis: Mapping[str, object], manifest) -> dict:
    value = {
        **basis,
        "schema_version": KNOWLEDGE_REUSE_SCHEMA_VERSION,
        "lifecycle_hash": manifest_lifecycle_hash(manifest),
    }
    return validate_reuse_commitment(value)


def rebind_maintenance_reuse(knowledge, manifest):
    """Retain validated input commitments while rebinding a projected owner update."""
    previous = knowledge.extensions.get(REUSE_EXTENSION_KEY)
    if previous is None:
        return knowledge, manifest
    previous = validate_reuse_commitment(previous)
    basis = {key: value for key, value in previous.items()
             if key not in {"schema_version", "lifecycle_hash"}}
    commitment = bind_reuse_commitment(basis, manifest)
    manifest = manifest.with_generation_state(
        surfaces=manifest.surfaces,
        generation_inputs={**manifest.generation_inputs, REUSE_INPUT_KEY: commitment},
    )
    return replace(knowledge, extensions={**knowledge.extensions, REUSE_EXTENSION_KEY: commitment}), manifest


def validate_reuse_artifact_parity(knowledge, manifest) -> None:
    """A manifest hint alone never authorizes reuse of a projection."""
    value = knowledge.extensions.get(REUSE_EXTENSION_KEY)
    if value is None:
        # Older writers/readers can preserve unknown manifest metadata; it is
        # unusable as a shortcut without the matching committed extension.
        return
    value = validate_reuse_commitment(value)
    if manifest.generation_inputs.get(REUSE_INPUT_KEY) != value:
        raise ValueError("manifest and knowledge reuse commitments differ")
    from .knowledge_envelope import INVENTORY_HASH_EXTENSION

    snapshot = knowledge.bundle.snapshot
    expected = {
        "source_snapshot_hash": snapshot.source_snapshot_hash,
        "inventory_hash": snapshot.extensions[INVENTORY_HASH_EXTENSION],
        "generation_options_hash": snapshot.generation_options_hash,
        "markdown_snapshot_hash": snapshot.markdown_snapshot_hash,
        "repository_hash": repository_input_hash(knowledge.bundle.repository),
        "lifecycle_hash": manifest_lifecycle_hash(manifest),
    }
    if any(value[field] != commitment for field, commitment in expected.items()):
        raise ValueError("knowledge reuse does not match its committed artifact inputs")


def observation_inputs_hash(
    *,
    entrypoint_observations: Mapping,
    entry_points: Sequence[Mapping],
    api_contracts: Mapping,
    dependency_analysis: Mapping | None,
) -> str:
    """Commit the same raw detector inputs for bootstrap and sync."""
    return hash_json(
        {
            "entrypoints": entrypoint_observations,
            "entries": entry_points,
            "api_contracts": api_contracts,
            "dependencies": dependency_analysis,
        }
    )


def build_reuse_input_basis(
    wiki_dir,
    inventory_result,
    source_snapshot,
    generation_inputs,
    generation_options,
    repository_evidence,
    *,
    include_plugins=True,
    manifest=None,
    inventory_complete=True,
    observation_inputs_hash=None,
) -> dict[str, object] | None:
    """Capture the inputs of the deterministic built-in sync pipeline."""
    from .knowledge_envelope import build_repository_record, hash_inventory
    from .knowledge_governance import GOVERNANCE_FILENAME
    from .knowledge_orchestration import (
        runtime_generation_options_hash,
        runtime_source_snapshot_hash,
    )

    if not inventory_complete or not is_valid_sha256(observation_inputs_hash):
        return None
    from .extraction_service import EXTRACTOR_REGISTRY

    if (
        (Path(wiki_dir) / GOVERNANCE_FILENAME).exists()
        or getattr(getattr(manifest, "artifact_hashes", None), "governance_hash", None)
        is not None
        or inventory_result.plugin_components
        or inventory_result.producer_plugin_components
        or any(
            entry != EXTRACTOR_REGISTRY.get(language)
            for language, entry in inventory_result.extractor_registry.items()
        )
        or any(
            status.state != "ok" and status.files_found
            for status in inventory_result.statuses.values()
        )
    ):
        return None
    if include_plugins and any(
        (root / ".llm-wiki/plugins.lock.json").exists()
        for root in (Path.cwd(), source_snapshot.root)
    ):
        return None
    implementation = implementation_hash()
    if implementation is None:
        return None
    markdown, assets = wiki_input_hashes(Path(wiki_dir))
    return {
        "observation_inputs_hash": observation_inputs_hash,
        "source_snapshot_hash": runtime_source_snapshot_hash(
            source_snapshot,
            generation_inputs=generation_inputs,
            plugin_lock_path=inventory_result.plugin_lock_path,
            plugin_lock_hash=inventory_result.plugin_lock_hash,
        ),
        "inventory_hash": hash_inventory(inventory_result.inventory),
        "generation_options_hash": runtime_generation_options_hash(generation_options),
        "implementation_hash": implementation,
        "markdown_snapshot_hash": markdown,
        "assets_hash": assets,
        "repository_hash": repository_input_hash(
            build_repository_record(evidence=repository_evidence)
        ),
    }


def maintenance_reuse_check(wiki_dir, manifest, knowledge, inventory_result, source_snapshot) -> Callable[[], None] | None:
    """Reconcile exact live maintenance inputs before reusing a committed graph.

    Success retains a guarded raw-page recheck for the caller's final boundary.
    It never allocates an identity, changes review history or publishes evidence.
    """
    from .io import decode_markdown_bytes
    from .knowledge_storage import KnowledgeStorageError, MAX_EXPANDED_BYTES
    from .knowledge_storage_io import StorageReadSession
    from .maintenance_evidence import captured_observations_from_knowledge, reconcile_pending_maintenance
    from .maintenance_protocol import guard_maintenance_owner
    from .maintenance_state import MaintenanceError
    from .python_implementation import analysis_identity
    from .source_snapshot import confirmed_missing_source_paths
    from .wiki_surface import collect_wiki_pages

    owner = manifest.maintenance_state
    if owner is None:
        return None
    marker = guard_maintenance_owner(wiki_dir, manifest)
    captures = inventory_result.implementation_observations
    analysis_hash = analysis_identity(inventory_result.analysis_components)
    if not isinstance(captures, Mapping) or analysis_hash is None:
        return None
    captured_files = captures.get("files", {})
    if not isinstance(captured_files, Mapping) or any(
        source not in captured_files
        for source, info in inventory_result.inventory.items()
        if info.get("language") == "python"
    ):
        return None
    root = Path(wiki_dir)
    reader = StorageReadSession(root)
    pages = collect_wiki_pages(root)
    try:
        with reader.phase():
            raw = {page.relative_path: reader.read(page.relative_path, MAX_EXPANDED_BYTES) for page in pages}
    except KnowledgeStorageError as exc:
        if exc.code == "storage-budget-exhausted":
            return None
        raise
    # The final raw-byte recheck is charged to the same bounded session. Reserve
    # its exact work before accepting this advisory shortcut; larger wikis still
    # use the ordinary guarded planner without relaxing the inspection budget.
    if reader.recheck_work()["bytes"] > reader.maximum - reader.bytes_read:
        return None
    content = {name: decode_markdown_bytes(value) for name, value in raw.items()}
    prior_paths = {row["coordinate"]["source_path"] for row in owner["observations"].values()}
    missing = confirmed_missing_source_paths(source_snapshot, prior_paths)
    old_targets = {row["target"]["canonical_path"] for row in owner["observations"].values()}
    absent = {path for path in old_targets if not (root / path).exists() and not (root / path).is_symlink()}
    hashes = source_snapshot.captured_content_hashes
    capture = captured_observations_from_knowledge(
        knowledge, content_by_page=content, raw_content_by_page=raw,
        page_source_mappings=manifest.page_source_mappings, captures=captures,
        source_content_hashes=hashes, captured_paths=set(hashes) | set(missing),
        missing_source_paths=missing, analysis_compatibility_hash=analysis_hash,
        previous_state=owner, known_absent_pages=absent,
    )
    from .source_retirement import retired_entity_mappings
    retired = retired_entity_mappings(manifest)

    def has_selected_owner(row):
        if row["coordinate"]["source_path"] not in hashes:
            return False
        previous = retired.get(row["target"]["canonical_path"])
        return previous is None or row["coordinate"] != {
            "source_path": previous.source_path, "qualified_owner": previous.entity_name,
            "occurrence": previous.occurrence,
        }

    for issue in capture.issues:
        if issue.get("reason") in _STABLE_IMPLEMENTATION_GAPS:
            # Exact source/page/analysis commitments may preserve a known gap;
            # they never make its implementation evidence available. The full
            # reconciliation below must still preserve every owner byte without
            # registering an identity, including untracked unsupported scopes.
            continue
        # Retired/deselected owners may deliberately retain unavailable history.
        # Such an issue cannot authorize any selected source, and every affected
        # recorded observation must already equal this exact current capture.
        if issue.get("reason") not in {"source-not-captured", "current-owner-not-qualified"}:
            return None
        recorded = [row for record_id, row in owner["observations"].items()
                    if (issue.get("record_id") is None or issue["record_id"] == record_id)
                    and (issue.get("coordinate") is None or issue["coordinate"] == row["coordinate"])
                    and issue.get("canonical_path") == row["target"]["canonical_path"]]
        from .maintenance_evidence import owner_key

        if not recorded or any(has_selected_owner(row)
                               or capture.by_owner.get(owner_key(row["coordinate"], row["target"])) != row
                               for row in recorded):
            return None

    def refuse_registration():
        raise MaintenanceError("reuse-registration", "Current maintenance capture requires a new durable identity")

    try:
        reconciled = reconcile_pending_maintenance(owner, marker, capture, allocate_id=refuse_registration)
    except MaintenanceError as exc:
        if exc.code == "reuse-registration":
            return None
        raise
    if reconciled != owner:
        return None
    return reader.recheck


def unchanged_commit_result(state, manifest, *, dry_run: bool = False):
    """Return the ordinary result shape using already captured, validated bytes."""
    from .knowledge_artifacts import (
        ArtifactWriteState,
        KnowledgeCommitResult,
        PlannedArtifactWrite,
    )

    state.require_for(state.wiki_root)
    assert state.artifacts is not None
    writes = []
    for name in (
        ".llm-wiki-surface.json",
        ".llm-wiki-knowledge.json",
        ".llm-wiki-manifest.json",
    ):
        content = state.captured_bytes[name]
        assert isinstance(content, bytes)
        writes.append(
            PlannedArtifactWrite(
                path=state.wiki_root / name,
                relative_path=name,
                state=ArtifactWriteState.UNCHANGED,
                content_hash=sha256_bytes(content),
                content=content,
                needs_write=False,
            )
        )
    from .knowledge_packs import PACKED_SCHEMAS, packed_format
    import json
    storage_root = json.loads(writes[1].content)
    storage_format = "sharded-v2" if state.artifacts.storage_objects else "v1"
    if storage_root.get("schema_version") in PACKED_SCHEMAS:
        storage_format = packed_format(storage_root)
    return KnowledgeCommitResult(
        surface_index=writes[0],
        knowledge_index=writes[1],
        manifest=writes[2],
        committed_manifest=manifest,
        evaluated_envelope_hash=state.artifacts.evaluated_envelope_hash,
        dry_run=dry_run,
        storage_format=storage_format,
        storage_objects=tuple(PlannedArtifactWrite(
            path=state.wiki_root / name, relative_path=name, state=ArtifactWriteState.UNCHANGED,
            content_hash=sha256_bytes(content), content=content, needs_write=False, previous_content=content,
        ) for name, content in sorted(state.artifacts.storage_objects.items())),
    )
