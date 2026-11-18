"""Persisted infrastructure state: its format and the evidence it projects.

The state records repository-relative source/page mappings and binds each
rendered observation to the exact source bytes and the normalized parser
result. It contains no timestamps, absolute paths, or source literals.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import PurePosixPath
from typing import Mapping

from llm_wiki_engine.knowledge_evidence import (
    ConceptObservationBasis,
    build_infrastructure_observation_basis,
    is_valid_sha256,
)
from llm_wiki_engine.validation import is_portable_relative_path

INFRASTRUCTURE_SYNC_SCHEMA_VERSION = "llm-wiki-infrastructure-sync/v1"
INFRASTRUCTURE_GENERATION_INPUT_KEY = "infrastructure"
INFRASTRUCTURE_DISCOVERY_ROOT = "."
INFRASTRUCTURE_EXTRACTOR_REF = "llm-wiki/extractor/infrastructure"


class InfrastructureSyncError(ValueError):
    """Persisted infrastructure state is unsafe or internally inconsistent."""


def _prior_infrastructure_state(
    generation_inputs: Mapping[str, object] | None,
) -> dict[str, object]:
    if not isinstance(generation_inputs, Mapping):
        return {}
    if INFRASTRUCTURE_GENERATION_INPUT_KEY not in generation_inputs:
        return {}
    value = generation_inputs[INFRASTRUCTURE_GENERATION_INPUT_KEY]
    if not isinstance(value, Mapping):
        raise InfrastructureSyncError(
            "generation_inputs.infrastructure must be an object."
        )
    if value.get("schema_version") != INFRASTRUCTURE_SYNC_SCHEMA_VERSION:
        raise InfrastructureSyncError(
            "generation_inputs.infrastructure.schema_version is unsupported: "
            f"{value.get('schema_version')!r}"
        )
    return deepcopy(dict(value))


def _valid_repository_path(value: str) -> bool:
    PurePosixPath(value)  # Preserve the legacy type-error boundary.
    return is_portable_relative_path(value)


def _valid_page_path(value: object) -> bool:
    if not isinstance(value, str):
        return False
    path = PurePosixPath(value)
    return (
        len(path.parts) == 2
        and path.parts[0] == "infrastructure"
        and path.suffix == ".md"
        and path.name != ".md"
        and path.as_posix() == value
    )


def _record_mapping(
    value: object,
    *,
    field_name: str,
) -> dict[str, dict[str, object]]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise InfrastructureSyncError(
            f"generation_inputs.infrastructure.{field_name} must be an object"
        )
    result: dict[str, dict[str, object]] = {}
    for key, raw_record in value.items():
        if not isinstance(key, str) or not isinstance(raw_record, Mapping):
            raise InfrastructureSyncError(
                f"generation_inputs.infrastructure.{field_name} must contain objects"
            )
        if not _valid_repository_path(key):
            raise InfrastructureSyncError(
                f"generation_inputs.infrastructure.{field_name} has unsafe source path"
            )
        if raw_record.get("source_path") != key:
            raise InfrastructureSyncError(
                f"generation_inputs.infrastructure.{field_name}.{key}.source_path "
                "must match its repository-relative key"
            )
        if not _valid_page_path(raw_record.get("page_path")):
            raise InfrastructureSyncError(
                f"generation_inputs.infrastructure.{field_name}.{key}.page_path "
                "must be a direct infrastructure Markdown path"
            )
        for hash_field in ("source_content_hash", "observation_hash"):
            if not is_valid_sha256(raw_record.get(hash_field)):
                raise InfrastructureSyncError(
                    "generation_inputs.infrastructure."
                    f"{field_name}.{key}.{hash_field} must be a SHA-256 value"
                )
        adapter = raw_record.get("adapter")
        if not isinstance(adapter, str) or not adapter:
            raise InfrastructureSyncError(
                "generation_inputs.infrastructure."
                f"{field_name}.{key}.adapter must be a non-empty string"
            )
        evidence_basis = raw_record.get("evidence_basis")
        if not isinstance(evidence_basis, Mapping):
            raise InfrastructureSyncError(
                "generation_inputs.infrastructure."
                f"{field_name}.{key}.evidence_basis must be an object"
            )
        expected_basis = {
            "discovery_root": INFRASTRUCTURE_DISCOVERY_ROOT,
            "source_content_hash": raw_record["source_content_hash"],
            "observation_hash": raw_record["observation_hash"],
            "adapter": adapter,
        }
        if dict(evidence_basis) != expected_basis:
            raise InfrastructureSyncError(
                "generation_inputs.infrastructure."
                f"{field_name}.{key}.evidence_basis must match its source record"
            )
        state = raw_record.get("state")
        if field_name == "sources":
            if state != "current":
                raise InfrastructureSyncError(
                    "generation_inputs.infrastructure."
                    f"{field_name}.{key}.state must be 'current'"
                )
        else:
            if state != "removed":
                raise InfrastructureSyncError(
                    "generation_inputs.infrastructure."
                    f"{field_name}.{key}.state must be 'removed'"
                )
            reason = raw_record.get("reason")
            if reason not in {"source-moved", "source-removed"}:
                raise InfrastructureSyncError(
                    "generation_inputs.infrastructure."
                    f"{field_name}.{key}.reason is not supported"
                )
            moved_to = raw_record.get("moved_to")
            if reason == "source-moved":
                if not isinstance(moved_to, str) or not _valid_repository_path(
                    moved_to
                ):
                    raise InfrastructureSyncError(
                        "generation_inputs.infrastructure."
                        f"{field_name}.{key}.moved_to must be repository-relative"
                    )
            elif moved_to is not None:
                raise InfrastructureSyncError(
                    "generation_inputs.infrastructure."
                    f"{field_name}.{key}.moved_to is only valid for source moves"
                )
        result[key] = deepcopy(dict(raw_record))
    return result


def validate_infrastructure_generation_input(
    generation_inputs: Mapping[str, object] | None,
) -> None:
    """Reject an unsafe persisted v1 infrastructure mapping."""

    state = _prior_infrastructure_state(generation_inputs)
    if not state:
        return
    _record_mapping(state.get("sources"), field_name="sources")
    _record_mapping(state.get("tombstones"), field_name="tombstones")


def infrastructure_evidence_by_page(
    generation_inputs: Mapping[str, object] | None,
) -> dict[str, ConceptObservationBasis]:
    """Project persisted current/removal records into native concept evidence.

    Move tombstones intentionally have no page: the current destination record
    owns the observation. Source-removal tombstones retain the last valid basis
    so live freshness can report ``source-missing`` without presenting the page
    as current.
    """

    state = _prior_infrastructure_state(generation_inputs)
    if not state:
        return {}
    sources = _record_mapping(state.get("sources"), field_name="sources")
    tombstones = _record_mapping(state.get("tombstones"), field_name="tombstones")
    records = list(sources.items())
    records.extend(
        (source_path, record)
        for source_path, record in tombstones.items()
        if record.get("reason") == "source-removed"
    )
    result: dict[str, ConceptObservationBasis] = {}
    for source_path, record in sorted(records):
        page_path = str(record["page_path"])
        if page_path in result:
            raise InfrastructureSyncError(
                "generation_inputs.infrastructure maps multiple source records "
                f"to {page_path!r}"
            )
        result[page_path] = build_infrastructure_observation_basis(
            source_path=source_path,
            source_content_hash=str(record["source_content_hash"]),
            observation_hash=str(record["observation_hash"]),
            extractor_ref=INFRASTRUCTURE_EXTRACTOR_REF,
        )
    return result
