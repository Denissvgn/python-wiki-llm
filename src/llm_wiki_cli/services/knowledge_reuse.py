"""Versioned input commitments for conservative, validated sync no-ops."""

from __future__ import annotations

import os
import sys
import hashlib
from collections.abc import Mapping, Sequence
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
    return KnowledgeCommitResult(
        surface_index=writes[0],
        knowledge_index=writes[1],
        manifest=writes[2],
        committed_manifest=manifest,
        evaluated_envelope_hash=state.artifacts.evaluated_envelope_hash,
        dry_run=dry_run,
    )
