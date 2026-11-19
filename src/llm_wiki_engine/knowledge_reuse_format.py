"""Knowledge reuse commitments: their format and their binding to artifacts.

A sync may reuse a committed knowledge projection only when the manifest and
the knowledge bundle carry the same versioned commitment to every input.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, replace

from llm_wiki_engine.contracts import KNOWLEDGE_REUSE_SCHEMA_VERSION
from llm_wiki_engine.knowledge_evidence import hash_json, is_valid_sha256

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
