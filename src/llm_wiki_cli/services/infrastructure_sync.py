"""Deterministic infrastructure discovery and incremental sync planning.

Infrastructure observations are intentionally separate from the AST inventory.
The persisted state records repository-relative source/page mappings and binds
each rendered observation to both the exact source bytes and the normalized
parser result.  It contains no timestamps, absolute paths, or source literals.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Mapping

from .infrastructure_inventory import infrastructure_page_name
from .knowledge_evidence import (
    ConceptObservationBasis,
    build_infrastructure_observation_basis,
    hash_json,
    is_valid_sha256,
)
from .source_snapshot import SourceSnapshot


INFRASTRUCTURE_SYNC_SCHEMA_VERSION = "llm-wiki-infrastructure-sync/v1"
INFRASTRUCTURE_GENERATION_INPUT_KEY = "infrastructure"
INFRASTRUCTURE_DISCOVERY_ROOT = "."
INFRASTRUCTURE_EXTRACTOR_REF = "llm-wiki/extractor/infrastructure"


class InfrastructureSyncError(ValueError):
    """Persisted infrastructure state is unsafe or internally inconsistent."""


def build_infrastructure_page_map(
    source_paths: Mapping[str, object] | tuple[str, ...] | list[str] | set[str],
) -> dict[str, str]:
    """Return collision-safe page paths without changing legacy unique names."""

    paths = sorted(source_paths)
    by_stem: dict[str, list[str]] = {}
    for source_path in paths:
        stem = infrastructure_page_name(source_path)
        by_stem.setdefault(stem, []).append(source_path)
    result: dict[str, str] = {}
    for stem, grouped_paths in sorted(by_stem.items()):
        if len(grouped_paths) == 1:
            result[grouped_paths[0]] = f"infrastructure/{stem}.md"
            continue
        for source_path in grouped_paths:
            suffix = hash_json(source_path).removeprefix("sha256:")[:12]
            result[source_path] = f"infrastructure/{stem}__{suffix}.md"
    return result


def _source_hash(snapshot: SourceSnapshot, source_path: str) -> str:
    value = snapshot.captured_content_hashes.get(source_path)
    if value is None or not is_valid_sha256(value):
        raise InfrastructureSyncError(
            "infrastructure source was not captured by the source snapshot: "
            f"{source_path}"
        )
    return value


def _observation_hash(info: Mapping[str, object]) -> str:
    return hash_json(
        {
            "schema_version": INFRASTRUCTURE_SYNC_SCHEMA_VERSION,
            "adapter": str(info.get("type") or "unknown"),
            "observation": dict(info),
        }
    )


def _source_record(
    snapshot: SourceSnapshot,
    source_path: str,
    info: Mapping[str, object],
    *,
    page_path: str,
) -> dict[str, object]:
    source_hash = _source_hash(snapshot, source_path)
    observation_hash = _observation_hash(info)
    adapter = str(info.get("type") or "unknown")
    return {
        "state": "current",
        "source_path": source_path,
        "page_path": page_path,
        "adapter": adapter,
        "source_content_hash": source_hash,
        "observation_hash": observation_hash,
        "evidence_basis": {
            "discovery_root": INFRASTRUCTURE_DISCOVERY_ROOT,
            "source_content_hash": source_hash,
            "observation_hash": observation_hash,
            "adapter": adapter,
        },
    }


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
    path = PurePosixPath(value)
    return bool(
        value
        and not path.is_absolute()
        and "\\" not in value
        and ".." not in path.parts
        and "." not in path.parts
        and path.as_posix() == value
    )


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


def current_infrastructure_bases(
    snapshot: SourceSnapshot,
    inventory: Mapping[str, Mapping[str, object]],
) -> dict[str, ConceptObservationBasis]:
    """Build live bases keyed by source path from an evaluated inventory."""

    page_paths = build_infrastructure_page_map(inventory)
    return {
        source_path: build_infrastructure_observation_basis(
            source_path=source_path,
            source_content_hash=_source_hash(snapshot, source_path),
            observation_hash=_observation_hash(info),
            extractor_ref=INFRASTRUCTURE_EXTRACTOR_REF,
        )
        for source_path, info in sorted(inventory.items())
        if source_path in page_paths
    }


def _yaml_candidates(snapshot: SourceSnapshot) -> tuple[str, ...]:
    return tuple(sorted(item.rel_path for item in snapshot.yaml_candidates))


def _candidate_roots(
    snapshot: SourceSnapshot,
    inventory: Mapping[str, Mapping[str, object]],
) -> tuple[str, ...]:
    paths = set(_yaml_candidates(snapshot))
    paths.update(item.rel_path for item in snapshot.dockerfile_candidates)
    paths.update(item.rel_path for item in snapshot.compose_candidates)
    paths.update(inventory)
    roots = {
        str(PurePosixPath(path).parent)
        if str(PurePosixPath(path).parent) != "."
        else INFRASTRUCTURE_DISCOVERY_ROOT
        for path in paths
    }
    roots.add(INFRASTRUCTURE_DISCOVERY_ROOT)
    return tuple(sorted(roots))


def _unsupported_yaml_records(
    snapshot: SourceSnapshot,
    inventory: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    supported = set(inventory)
    return tuple(
        {
            "path": path,
            "source_content_hash": _source_hash(snapshot, path),
            "reason": "unrecognized-yaml",
        }
        for path in _yaml_candidates(snapshot)
        if path not in supported
    )


def _move_key(record: Mapping[str, object]) -> tuple[object, ...]:
    return (
        record.get("adapter"),
        record.get("source_content_hash"),
        record.get("observation_hash"),
    )


def _detect_moves(
    prior_sources: Mapping[str, Mapping[str, object]],
    current_sources: Mapping[str, Mapping[str, object]],
    removed: set[str],
    added: set[str],
) -> dict[str, str]:
    old_by_key: dict[tuple[object, ...], list[str]] = {}
    new_by_key: dict[tuple[object, ...], list[str]] = {}
    for source_path in sorted(removed):
        old_by_key.setdefault(_move_key(prior_sources[source_path]), []).append(
            source_path
        )
    for source_path in sorted(added):
        new_by_key.setdefault(_move_key(current_sources[source_path]), []).append(
            source_path
        )
    return {
        old_paths[0]: new_by_key[key][0]
        for key, old_paths in sorted(old_by_key.items(), key=lambda item: repr(item[0]))
        if len(old_paths) == 1 and len(new_by_key.get(key, ())) == 1
    }


def _tombstone(
    record: Mapping[str, object],
    *,
    reason: str,
    moved_to: str | None = None,
) -> dict[str, object]:
    result = deepcopy(dict(record))
    result["state"] = "removed"
    result["reason"] = reason
    if moved_to is not None:
        result["moved_to"] = moved_to
    else:
        result.pop("moved_to", None)
    return result


def _discovery_status(
    *,
    current_count: int,
    unsupported_count: int,
    candidate_count: int,
) -> str:
    if current_count:
        return "supported-sources"
    if unsupported_count:
        return "unsupported-only"
    if candidate_count:
        return "no-supported-sources"
    return "nothing-discovered"


@dataclass(frozen=True)
class InfrastructureSyncPlan:
    """One immutable infrastructure regeneration plan."""

    inventory: dict[str, dict]
    prior_sources: dict[str, dict[str, object]]
    current_sources: dict[str, dict[str, object]]
    new_sources: tuple[str, ...]
    changed_sources: tuple[str, ...]
    unchanged_sources: tuple[str, ...]
    removed_sources: tuple[str, ...]
    moved_sources: dict[str, str]
    unsupported_yaml: tuple[dict[str, object], ...]
    discovery_roots: tuple[str, ...]
    next_state: dict[str, object]
    state_changed: bool
    repair_tombstones: tuple[str, ...] = ()
    cleanup_moved_pages: tuple[str, ...] = ()

    @property
    def affected_count(self) -> int:
        return (
            len(self.new_sources)
            + len(self.changed_sources)
            + len(self.removed_sources)
            + len(self.moved_sources)
            + len(self.repair_tombstones)
            + len(self.cleanup_moved_pages)
        )

    @property
    def has_changes(self) -> bool:
        return self.state_changed or bool(
            self.new_sources
            or self.changed_sources
            or self.removed_sources
            or self.moved_sources
            or self.repair_tombstones
            or self.cleanup_moved_pages
        )


def build_infrastructure_sync_plan(
    snapshot: SourceSnapshot,
    inventory: Mapping[str, Mapping[str, object]],
    *,
    generation_inputs: Mapping[str, object] | None = None,
) -> InfrastructureSyncPlan:
    """Compare current infrastructure observations with persisted native state."""

    normalized_inventory = {
        source_path: deepcopy(dict(info))
        for source_path, info in sorted(inventory.items())
    }
    page_paths = build_infrastructure_page_map(normalized_inventory)
    prior_state = _prior_infrastructure_state(generation_inputs)
    prior_sources = _record_mapping(
        prior_state.get("sources"),
        field_name="sources",
    )
    current_sources = {
        source_path: _source_record(
            snapshot,
            source_path,
            info,
            page_path=page_paths[source_path],
        )
        for source_path, info in normalized_inventory.items()
    }
    old_paths = set(prior_sources)
    current_paths = set(current_sources)
    added = current_paths - old_paths
    removed = old_paths - current_paths
    moved = _detect_moves(prior_sources, current_sources, removed, added)
    moved_old = set(moved)
    moved_new = set(moved.values())

    changed = {
        source_path
        for source_path in old_paths & current_paths
        if prior_sources[source_path] != current_sources[source_path]
    }
    unchanged = (old_paths & current_paths) - changed
    unsupported_yaml = _unsupported_yaml_records(snapshot, normalized_inventory)
    discovery_roots = _candidate_roots(snapshot, normalized_inventory)

    tombstones = _record_mapping(
        prior_state.get("tombstones"),
        field_name="tombstones",
    )
    for source_path in current_paths:
        tombstones.pop(source_path, None)
    for source_path in sorted(removed - moved_old):
        tombstones[source_path] = _tombstone(
            prior_sources[source_path],
            reason="source-removed",
        )
    for old_path, new_path in sorted(moved.items()):
        tombstones[old_path] = _tombstone(
            prior_sources[old_path],
            reason="source-moved",
            moved_to=new_path,
        )

    candidate_count = len(
        set(_yaml_candidates(snapshot))
        | {item.rel_path for item in snapshot.dockerfile_candidates}
        | {item.rel_path for item in snapshot.compose_candidates}
    )
    next_state: dict[str, object] = {
        "schema_version": INFRASTRUCTURE_SYNC_SCHEMA_VERSION,
        "status": _discovery_status(
            current_count=len(current_sources),
            unsupported_count=len(unsupported_yaml),
            candidate_count=candidate_count,
        ),
        "discovery": {
            "roots": list(discovery_roots),
            "candidate_count": candidate_count,
            "supported_count": len(current_sources),
            "unsupported_yaml_count": len(unsupported_yaml),
            "unsupported_yaml": list(unsupported_yaml),
        },
        "sources": current_sources,
        "tombstones": tombstones,
    }
    return InfrastructureSyncPlan(
        inventory=normalized_inventory,
        prior_sources=prior_sources,
        current_sources=current_sources,
        new_sources=tuple(sorted(added - moved_new)),
        changed_sources=tuple(sorted(changed)),
        unchanged_sources=tuple(sorted(unchanged)),
        removed_sources=tuple(sorted(removed - moved_old)),
        moved_sources=dict(sorted(moved.items())),
        unsupported_yaml=unsupported_yaml,
        discovery_roots=discovery_roots,
        next_state=next_state,
        state_changed=(
            next_state != prior_state
            and bool(prior_state or candidate_count or current_sources)
        ),
    )


def with_infrastructure_generation_input(
    generation_inputs: Mapping[str, object],
    plan: InfrastructureSyncPlan,
) -> dict[str, object]:
    """Return generation inputs carrying the plan's deterministic next state."""

    result = deepcopy(dict(generation_inputs))
    result[INFRASTRUCTURE_GENERATION_INPUT_KEY] = deepcopy(plan.next_state)
    return result


__all__ = [
    "INFRASTRUCTURE_DISCOVERY_ROOT",
    "INFRASTRUCTURE_EXTRACTOR_REF",
    "INFRASTRUCTURE_GENERATION_INPUT_KEY",
    "INFRASTRUCTURE_SYNC_SCHEMA_VERSION",
    "InfrastructureSyncError",
    "InfrastructureSyncPlan",
    "build_infrastructure_page_map",
    "build_infrastructure_sync_plan",
    "current_infrastructure_bases",
    "infrastructure_evidence_by_page",
    "validate_infrastructure_generation_input",
    "with_infrastructure_generation_input",
]
