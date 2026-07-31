"""Deterministic commit protocol for generated knowledge artifacts.

The surface index and knowledge index are independently atomic files.  The
sync manifest is replaced last and commits the exact bytes of both projections
plus the complete evaluated-envelope hash.  Until that final replacement, a
validated reader must reject any orphan or mixed projection set.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .contracts import (
    KNOWLEDGE_SCHEMA_VERSION,
    SECTION_OWNERSHIP_EXTENSION_KEY,
    TYPED_GRAPH_EXTENSION_KEY,
)
from .io import write_bytes_atomic
from .infrastructure_sync import (
    INFRASTRUCTURE_GENERATION_INPUT_KEY,
    INFRASTRUCTURE_SYNC_SCHEMA_VERSION,
    InfrastructureSyncError,
    infrastructure_evidence_by_page,
)
from .knowledge_envelope import EvaluatedEnvelope, INVENTORY_HASH_EXTENSION
from .knowledge_evidence import formatted_json_bytes, is_valid_sha256, sha256_bytes
from .knowledge_graph import KnowledgeGraphError, typed_graph_from_knowledge_extensions
from .knowledge_index import serialize_knowledge_index, validate_knowledge_index
from .knowledge_model import (
    ConceptKind,
    EvidenceBasis,
    EvidenceState,
    KnowledgeIndex,
    Origin,
)
from .section_ownership import SectionOwnershipError, validate_section_ownership
from .sync_manifest import MANIFEST_FILENAME, SyncManifest, SyncManifestError
from .validation import (
    is_portable_relative_path,
    require_exact_fields as require_shared_exact_fields,
    require_nonnegative_int,
)
from .wiki_surface import (
    PageKind,
    WikiSurfaceError,
    canonical_path,
    iter_page_kinds,
    mcp_uri,
)
from .wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
)

KNOWLEDGE_INDEX_FILENAME = ".llm-wiki-knowledge.json"
_KNOWLEDGE_SCHEMA_VERSION_RE = re.compile(
    r"^llm-wiki-knowledge/v([1-9][0-9]*)$"
)
_SURFACE_SCHEMA_VERSION_RE = re.compile(
    r"^llm-wiki-surface-index/v([1-9][0-9]*)$"
)


class KnowledgeArtifactError(ValueError):
    """Field-specific failure while planning a generated artifact commit."""

    def __init__(self, field: str, message: str, *, code: str | None = None):
        self.field = field
        self.message = message
        self.code = code
        super().__init__(f"{field}: {message}")


class ArtifactWriteState(str, Enum):
    """User-facing state for one planned artifact replacement."""

    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


class CommitStage(str, Enum):
    """Fault-injection points reached after each successful atomic replacement."""

    SURFACE_INDEX_WRITTEN = "surface-index-written"
    KNOWLEDGE_INDEX_WRITTEN = "knowledge-index-written"
    MANIFEST_WRITTEN = "manifest-written"


@dataclass(frozen=True)
class PlannedArtifactWrite:
    """One exact-byte action in a knowledge artifact commit."""

    path: Path
    relative_path: str
    state: ArtifactWriteState
    content_hash: str
    content: bytes
    needs_write: bool


@dataclass(frozen=True)
class ValidatedKnowledgeArtifacts:
    """Validated canonical projections and their exact-byte commitments."""

    surface_payload: Mapping[str, Any]
    knowledge: KnowledgeIndex
    surface_index_hash: str
    knowledge_index_hash: str
    evaluated_envelope_hash: str
    governance_hash: str | None = None


@dataclass(frozen=True)
class KnowledgeCommitPlan:
    """A fully validated, immutable three-artifact commit plan."""

    surface_index: PlannedArtifactWrite
    knowledge_index: PlannedArtifactWrite
    manifest: PlannedArtifactWrite
    committed_manifest: SyncManifest
    evaluated_envelope_hash: str

    @property
    def changed(self) -> bool:
        return any(
            artifact.needs_write
            for artifact in (
                self.surface_index,
                self.knowledge_index,
                self.manifest,
            )
        )


@dataclass(frozen=True)
class KnowledgeCommitResult:
    """Outcome of a real or dry-run commit."""

    surface_index: PlannedArtifactWrite
    knowledge_index: PlannedArtifactWrite
    manifest: PlannedArtifactWrite
    committed_manifest: SyncManifest
    evaluated_envelope_hash: str
    dry_run: bool

    @property
    def changed(self) -> bool:
        return any(
            artifact.needs_write
            for artifact in (
                self.surface_index,
                self.knowledge_index,
                self.manifest,
            )
        )


FaultInjector = Callable[[CommitStage], None]


def validate_surface_index_bytes(
    surface_index_bytes: bytes,
) -> Mapping[str, Any]:
    """Parse and strictly validate canonical surface-index v1 bytes."""

    surface_payload = _decode_json_object(
        surface_index_bytes,
        "surface_index_bytes",
    )
    _validate_surface_payload(surface_payload)
    _surface_page_index(surface_payload)
    expected_surface_bytes = (
        json.dumps(
            surface_payload,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if surface_index_bytes != expected_surface_bytes:
        raise KnowledgeArtifactError(
            "surface_index_bytes",
            "must use the deterministic surface-index v1 wire encoding",
        )
    return surface_payload


def validate_knowledge_artifacts(
    *,
    surface_index_bytes: bytes,
    knowledge_index_bytes: bytes,
    manifest: SyncManifest,
) -> ValidatedKnowledgeArtifacts:
    """Validate canonical projections, cross-artifact parity, and manifest basis."""

    surface_payload = validate_surface_index_bytes(surface_index_bytes)

    knowledge_payload = _decode_json_object(
        knowledge_index_bytes,
        "knowledge_index_bytes",
    )
    schema_version = knowledge_payload.get("schema_version")
    if _is_future_schema_version(
        schema_version,
        KNOWLEDGE_SCHEMA_VERSION,
        _KNOWLEDGE_SCHEMA_VERSION_RE,
    ):
        raise KnowledgeArtifactError(
            "knowledge_index_bytes.schema_version",
            "uses a recognized future knowledge schema version",
            code="unsupported-schema-version",
        )
    try:
        knowledge = validate_knowledge_index(knowledge_payload)
        expected_knowledge_bytes = serialize_knowledge_index(knowledge).encode("utf-8")
    except (TypeError, ValueError) as exc:
        nested_field = getattr(exc, "field", None)
        nested_code = getattr(exc, "code", None)
        artifact_field = (
            f"knowledge_index_bytes.{nested_field}"
            if isinstance(nested_field, str) and nested_field
            else "knowledge_index_bytes"
        )
        raise KnowledgeArtifactError(
            artifact_field,
            f"does not contain a valid knowledge index: {exc}",
            code=(
                str(nested_code)
                if isinstance(nested_code, str)
                else None
            ),
        ) from exc
    if knowledge_index_bytes != expected_knowledge_bytes:
        raise KnowledgeArtifactError(
            "knowledge_index_bytes",
            "must use the canonical knowledge-index v1 wire encoding",
        )

    surface_hash = sha256_bytes(surface_index_bytes)
    if knowledge.bundle.snapshot.surface_index_hash != surface_hash:
        raise KnowledgeArtifactError(
            "knowledge_index.bundle.snapshot.surface_index_hash",
            "does not match the exact surface-index bytes",
        )
    try:
        graph = typed_graph_from_knowledge_extensions(
            knowledge.extensions,
            concept_kinds={
                concept.locator: (
                    concept.concept_kind.value
                    if isinstance(concept.concept_kind, ConceptKind)
                    else concept.concept_kind
                )
                for concept in knowledge.concepts
            },
        )
    except KnowledgeGraphError as exc:
        field = exc.field
        if field.startswith("typed_graph"):
            field = (
                "knowledge_index.extensions."
                f"{TYPED_GRAPH_EXTENSION_KEY}"
                + field[len("typed_graph") :]
            )
        raise KnowledgeArtifactError(
            field,
            exc.message,
        ) from exc
    if graph is not None:
        inventory_hash = knowledge.bundle.snapshot.extensions.get(
            INVENTORY_HASH_EXTENSION
        )
        if graph["input_hashes"]["inventory"] != inventory_hash:
            raise KnowledgeArtifactError(
                "knowledge_index.extensions."
                f"{TYPED_GRAPH_EXTENSION_KEY}.input_hashes.inventory",
                "does not match the evaluated envelope inventory hash",
            )
    section_ownership = knowledge.extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY)
    if section_ownership is not None:
        try:
            validate_section_ownership(
                section_ownership,
                concepts={
                    concept.locator: (
                        concept.document.page_kind,
                        concept.facets.semantics.page_hash,
                    )
                    for concept in knowledge.concepts
                },
            )
        except SectionOwnershipError as exc:
            field = exc.field
            if field.startswith("section_ownership"):
                field = (
                    "knowledge_index.extensions."
                    f"{SECTION_OWNERSHIP_EXTENSION_KEY}"
                    + field[len("section_ownership") :]
                )
            raise KnowledgeArtifactError(
                field,
                exc.message,
            ) from exc
    _validate_surface_knowledge_parity(surface_payload, knowledge)
    _validate_manifest_knowledge_parity(manifest, surface_payload, knowledge)
    from .knowledge_governance import governance_hash_from_knowledge

    governance_hash = governance_hash_from_knowledge(knowledge)
    return ValidatedKnowledgeArtifacts(
        surface_payload=surface_payload,
        knowledge=knowledge,
        surface_index_hash=surface_hash,
        knowledge_index_hash=sha256_bytes(knowledge_index_bytes),
        evaluated_envelope_hash=EvaluatedEnvelope(
            bundle=knowledge.bundle
        ).content_hash(),
        governance_hash=governance_hash,
    )


def build_knowledge_commit_plan(
    wiki_dir: str | Path,
    *,
    surface_index_bytes: bytes,
    knowledge_index_bytes: bytes,
    manifest: SyncManifest,
) -> KnowledgeCommitPlan:
    """Validate and plan one manifest-last knowledge artifact commit.

    The supplied projection bytes must already use their canonical wire
    encodings.  The evaluated-envelope hash is derived from the validated
    knowledge bundle, rather than accepted as an independent caller claim.
    """

    root = Path(wiki_dir)
    validated = validate_knowledge_artifacts(
        surface_index_bytes=surface_index_bytes,
        knowledge_index_bytes=knowledge_index_bytes,
        manifest=manifest,
    )

    if not isinstance(manifest, SyncManifest):
        raise TypeError("manifest must be a SyncManifest")
    committed_manifest = manifest.with_artifact_hashes(
        surface_index_hash=validated.surface_index_hash,
        knowledge_index_hash=validated.knowledge_index_hash,
        evaluated_envelope_hash=validated.evaluated_envelope_hash,
        governance_hash=validated.governance_hash,
    )
    try:
        manifest_bytes = formatted_json_bytes(committed_manifest.to_payload())
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise KnowledgeArtifactError(
            "manifest",
            f"cannot be serialized as deterministic JSON: {exc}",
        ) from exc

    surface = _planned_write(
        root / SURFACE_INDEX_FILENAME,
        SURFACE_INDEX_FILENAME,
        surface_index_bytes,
    )
    knowledge_write = _planned_write(
        root / KNOWLEDGE_INDEX_FILENAME,
        KNOWLEDGE_INDEX_FILENAME,
        knowledge_index_bytes,
    )
    projections_change = surface.needs_write or knowledge_write.needs_write
    manifest_write = _planned_write(
        root / MANIFEST_FILENAME,
        MANIFEST_FILENAME,
        manifest_bytes,
        force_replace=projections_change,
    )
    return KnowledgeCommitPlan(
        surface_index=surface,
        knowledge_index=knowledge_write,
        manifest=manifest_write,
        committed_manifest=committed_manifest,
        evaluated_envelope_hash=validated.evaluated_envelope_hash,
    )


def commit_knowledge_artifacts(
    plan: KnowledgeCommitPlan,
    *,
    dry_run: bool = False,
    fault_injector: FaultInjector | None = None,
) -> KnowledgeCommitResult:
    """Apply *plan* in projection/projection/manifest order.

    Dry-run returns the complete plan without touching the filesystem or
    invoking fault-injection callbacks.
    """

    if not isinstance(plan, KnowledgeCommitPlan):
        raise TypeError("plan must be a KnowledgeCommitPlan")
    if not isinstance(dry_run, bool):
        raise TypeError("dry_run must be a bool")
    if fault_injector is not None and not callable(fault_injector):
        raise TypeError("fault_injector must be callable")

    if not dry_run:
        _apply_write(
            plan.surface_index,
            CommitStage.SURFACE_INDEX_WRITTEN,
            fault_injector,
        )
        _apply_write(
            plan.knowledge_index,
            CommitStage.KNOWLEDGE_INDEX_WRITTEN,
            fault_injector,
        )
        _verify_persisted(plan.surface_index)
        _verify_persisted(plan.knowledge_index)
        _apply_write(
            plan.manifest,
            CommitStage.MANIFEST_WRITTEN,
            fault_injector,
        )
        _verify_persisted(plan.surface_index)
        _verify_persisted(plan.knowledge_index)
        _verify_persisted(plan.manifest)

    return KnowledgeCommitResult(
        surface_index=plan.surface_index,
        knowledge_index=plan.knowledge_index,
        manifest=plan.manifest,
        committed_manifest=plan.committed_manifest,
        evaluated_envelope_hash=plan.evaluated_envelope_hash,
        dry_run=dry_run,
    )


def _planned_write(
    path: Path,
    relative_path: str,
    content: bytes,
    *,
    force_replace: bool = False,
) -> PlannedArtifactWrite:
    exists = path.is_file()
    current = path.read_bytes() if exists else None
    differs = current != content
    needs_write = differs or (force_replace and exists)
    if not exists:
        state = ArtifactWriteState.CREATED
    elif differs or force_replace:
        state = ArtifactWriteState.UPDATED
    else:
        state = ArtifactWriteState.UNCHANGED
    return PlannedArtifactWrite(
        path=path,
        relative_path=relative_path,
        state=state,
        content_hash=sha256_bytes(content),
        content=content,
        needs_write=needs_write,
    )


def _apply_write(
    artifact: PlannedArtifactWrite,
    stage: CommitStage,
    fault_injector: FaultInjector | None,
) -> None:
    if not artifact.needs_write:
        return
    write_bytes_atomic(artifact.path, artifact.content)
    if fault_injector is not None:
        fault_injector(stage)


def _verify_persisted(artifact: PlannedArtifactWrite) -> None:
    try:
        persisted = artifact.path.read_bytes()
    except OSError as exc:
        raise KnowledgeArtifactError(
            artifact.relative_path,
            "could not verify the persisted artifact",
        ) from exc
    if (
        sha256_bytes(persisted) != artifact.content_hash
        or persisted != artifact.content
    ):
        raise KnowledgeArtifactError(
            artifact.relative_path,
            "persisted bytes changed before the manifest commit completed",
        )


def _decode_json_object(content: bytes, field: str) -> Mapping[str, Any]:
    if not isinstance(content, bytes):
        raise KnowledgeArtifactError(field, "must be bytes")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise KnowledgeArtifactError(field, "must be valid UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=lambda pairs: _unique_json_object(pairs, field),
            parse_constant=lambda value: _reject_json_constant(value, field),
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, KnowledgeArtifactError):
            raise
        raise KnowledgeArtifactError(field, f"must contain valid JSON: {exc}") from exc
    if not isinstance(value, Mapping):
        raise KnowledgeArtifactError(field, "must contain a JSON object")
    return value


def _unique_json_object(
    pairs: list[tuple[str, Any]],
    field: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KnowledgeArtifactError(field, f"contains duplicate key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str, field: str) -> None:
    raise KnowledgeArtifactError(field, f"contains non-finite number {value!r}")


def _is_future_schema_version(
    value: object,
    current: str,
    pattern: re.Pattern[str],
) -> bool:
    if not isinstance(value, str):
        return False
    candidate_match = pattern.fullmatch(value)
    current_match = pattern.fullmatch(current)
    if candidate_match is None or current_match is None:
        return False
    candidate_number = candidate_match.group(1)
    current_number = current_match.group(1)
    return (
        len(candidate_number) > len(current_number)
        or (
            len(candidate_number) == len(current_number)
            and candidate_number > current_number
        )
    )


def _validate_surface_payload(payload: Mapping[str, Any]) -> None:
    _validate_utf8_json(payload, "surface_index")
    schema_version = payload.get("schema_version")
    if schema_version != WIKI_SURFACE_INDEX_SCHEMA_VERSION:
        raise KnowledgeArtifactError(
            "surface_index.schema_version",
            f"must be {WIKI_SURFACE_INDEX_SCHEMA_VERSION!r}",
            code=(
                "unsupported-schema-version"
                if _is_future_schema_version(
                    schema_version,
                    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
                    _SURFACE_SCHEMA_VERSION_RE,
                )
                else None
            ),
        )
    required = {
        "schema_version",
        "counts",
        "dependency_pages",
        "assets",
        "flows",
        "pages",
        "source_hash",
    }
    missing = required - set(payload)
    if missing:
        name = min(missing)
        raise KnowledgeArtifactError(f"surface_index.{name}", "is required")
    pages = payload.get("pages")
    if not isinstance(pages, list):
        raise KnowledgeArtifactError("surface_index.pages", "must be an array")
    if not isinstance(payload.get("counts"), Mapping):
        raise KnowledgeArtifactError("surface_index.counts", "must be an object")
    if not isinstance(payload.get("dependency_pages"), Mapping):
        raise KnowledgeArtifactError(
            "surface_index.dependency_pages",
            "must be an object",
        )
    if not is_valid_sha256(payload.get("source_hash")):
        raise KnowledgeArtifactError(
            "surface_index.source_hash",
            "must be a canonical lowercase SHA-256 value",
        )


def _validate_utf8_json(value: object, field: str) -> None:
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise KnowledgeArtifactError(
                field,
                "contains a string that cannot be encoded as strict UTF-8",
            ) from exc
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise KnowledgeArtifactError(field, "must use string object keys")
            _validate_utf8_json(key, f"{field}.<key>")
            _validate_utf8_json(child, f"{field}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _validate_utf8_json(child, f"{field}[{index}]")


def _validate_surface_knowledge_parity(
    surface: Mapping[str, Any],
    knowledge: KnowledgeIndex,
) -> None:
    surface_by_path = _surface_page_index(surface)

    concepts_by_path = {
        concept.document.canonical_path: concept for concept in knowledge.concepts
    }
    if set(surface_by_path) != set(concepts_by_path):
        missing = set(concepts_by_path) - set(surface_by_path)
        if missing:
            path = min(missing)
            raise KnowledgeArtifactError(
                "surface_index.pages",
                f"is missing active knowledge document {path!r}",
            )
        path = min(set(surface_by_path) - set(concepts_by_path))
        index, _ = surface_by_path[path]
        raise KnowledgeArtifactError(
            f"surface_index.pages[{index}].canonical_path",
            f"{path!r} is not an active knowledge document",
        )

    for path, (index, page) in surface_by_path.items():
        concept = concepts_by_path[path]
        field = f"surface_index.pages[{index}]"
        expected = {
            "kind": concept.document.page_kind.value,
            "id": concept.document.page_id,
            "title": concept.title,
            "role": concept.document.role.value,
            "mcp_uri": concept.locator,
        }
        for key, expected_value in expected.items():
            if page[key] != expected_value:
                raise KnowledgeArtifactError(
                    f"{field}.{key}",
                    f"must match the knowledge document value {expected_value!r}",
                )


def _surface_page_index(
    surface: Mapping[str, Any],
) -> dict[str, tuple[int, Mapping[str, Any]]]:
    raw_pages = surface["pages"]
    assert isinstance(raw_pages, list)
    registry = {entry.kind: entry for entry in iter_page_kinds()}
    surface_by_path: dict[str, tuple[int, Mapping[str, Any]]] = {}
    required = {
        "kind",
        "id",
        "title",
        "canonical_path",
        "source_path",
        "role",
        "mcp_uri",
        "outgoing_internal_links",
    }
    for index, value in enumerate(raw_pages):
        field = f"surface_index.pages[{index}]"
        if not isinstance(value, Mapping):
            raise KnowledgeArtifactError(field, "must be an object")
        missing = required - set(value)
        if missing:
            key = min(missing)
            raise KnowledgeArtifactError(f"{field}.{key}", "is required")
        try:
            kind = PageKind(value["kind"])
        except (TypeError, ValueError) as exc:
            raise KnowledgeArtifactError(
                f"{field}.kind",
                "must be a registered page kind",
            ) from exc
        page_id = value["id"]
        if not isinstance(page_id, str) or not page_id:
            raise KnowledgeArtifactError(f"{field}.id", "must be a non-empty string")
        entry = registry[kind]
        if not entry.requires_page_id and page_id != kind.value:
            raise KnowledgeArtifactError(
                f"{field}.id",
                f"must be {kind.value!r} for the root surface",
            )
        try:
            expected_path = canonical_path(
                kind,
                page_id if entry.requires_page_id else None,
            )
            expected_locator = mcp_uri(
                kind,
                page_id if entry.requires_page_id else None,
            )
        except WikiSurfaceError as exc:
            raise KnowledgeArtifactError(f"{field}.id", str(exc)) from exc
        canonical = value["canonical_path"]
        if canonical != expected_path:
            raise KnowledgeArtifactError(
                f"{field}.canonical_path",
                f"must be the registered canonical path {expected_path!r}",
            )
        if value["role"] != entry.role.value:
            raise KnowledgeArtifactError(
                f"{field}.role",
                f"must be the registered role {entry.role.value!r}",
            )
        if value["mcp_uri"] != expected_locator:
            raise KnowledgeArtifactError(
                f"{field}.mcp_uri",
                f"must be the registered locator {expected_locator!r}",
            )
        title = value["title"]
        if not isinstance(title, str) or not title.strip():
            raise KnowledgeArtifactError(
                f"{field}.title",
                "must be a non-empty string",
            )
        source_path = value["source_path"]
        if source_path is not None and not _is_safe_relative_path(source_path):
            raise KnowledgeArtifactError(
                f"{field}.source_path",
                "must be null or a normalized repository-relative POSIX path",
            )
        outgoing = value["outgoing_internal_links"]
        if not isinstance(outgoing, list) or any(
            not isinstance(target, str) for target in outgoing
        ):
            raise KnowledgeArtifactError(
                f"{field}.outgoing_internal_links",
                "must be an array of canonical path strings",
            )
        if len(set(outgoing)) != len(outgoing):
            raise KnowledgeArtifactError(
                f"{field}.outgoing_internal_links",
                "must not contain duplicates",
            )
        if canonical in surface_by_path:
            raise KnowledgeArtifactError(
                f"{field}.canonical_path",
                f"duplicates {canonical!r}",
            )
        surface_by_path[canonical] = (index, value)

    valid_paths = set(surface_by_path)
    for index, page in surface_by_path.values():
        for target in page["outgoing_internal_links"]:
            if target not in valid_paths:
                raise KnowledgeArtifactError(
                    f"surface_index.pages[{index}].outgoing_internal_links",
                    f"contains unknown canonical document {target!r}",
                )
    _validate_surface_counts(surface, surface_by_path)
    _validate_surface_dependency_pages(surface)
    _validate_surface_assets(surface, valid_paths)
    _validate_surface_flows(surface, surface_by_path)
    return surface_by_path


def _validate_manifest_knowledge_parity(
    manifest: SyncManifest,
    surface: Mapping[str, Any],
    knowledge: KnowledgeIndex,
) -> None:
    if not isinstance(manifest, SyncManifest):
        raise TypeError("manifest must be a SyncManifest")
    # Validate the caller's complete next-state manifest before deriving its
    # commit marker.
    try:
        manifest.to_payload()
    except SyncManifestError as exc:
        raise KnowledgeArtifactError(
            f"manifest.{exc.field}",
            exc.message,
        ) from exc
    structural = {
        concept.document.canonical_path: concept
        for concept in knowledge.concepts
        if concept.concept_kind in {ConceptKind.SOURCE_MODULE, ConceptKind.CODE_ENTITY}
    }
    expected_paths = set(structural)
    mapped_paths = set(manifest.page_source_mappings)
    extra_mappings = mapped_paths - expected_paths
    if extra_mappings:
        path = min(extra_mappings)
        raise KnowledgeArtifactError(
            "manifest.page_source_mappings",
            f"contains non-active structural document {path!r}",
        )
    evidence_paths = set(manifest.evidence_baselines) | set(manifest.tombstones)
    if evidence_paths != expected_paths:
        missing = expected_paths - evidence_paths
        if missing:
            path = min(missing)
            raise KnowledgeArtifactError(
                "manifest.evidence_state",
                f"is missing active structural document {path!r}",
            )
        path = min(evidence_paths - expected_paths)
        raise KnowledgeArtifactError(
            "manifest.evidence_state",
            f"contains non-active structural document {path!r}",
        )

    surface_by_path = {
        page["canonical_path"]: page
        for page in surface["pages"]
        if isinstance(page, Mapping)
    }
    for path, concept in structural.items():
        mapping = manifest.page_source_mappings.get(path)
        surface_source = surface_by_path[path]["source_path"]
        state = manifest.evidence_baselines.get(path)
        tombstone = manifest.tombstones.get(path)
        if (
            mapping is not None
            and surface_source != mapping.source_path
            and not (tombstone is not None and surface_source is None)
        ):
            raise KnowledgeArtifactError(
                f"surface_index.pages.{path}.source_path",
                "must match the manifest page source mapping",
            )
        if state is not None and mapping is None:
            raise KnowledgeArtifactError(
                f"manifest.evidence_baselines.{path}",
                "requires a page source mapping",
            )
        if state is not None:
            assert mapping is not None
            source = manifest.sources[mapping.source_path]
            if not is_valid_sha256(source.get("hash")):
                raise KnowledgeArtifactError(
                    f"manifest.sources.{mapping.source_path}.hash",
                    "must be a canonical lowercase SHA-256 value for an active source",
                )
        expected_basis = (
            state.basis
            if state is not None
            else tombstone.last_valid_basis
            if tombstone is not None
            else None
        )
        actual_basis = concept.facets.structure.basis
        if _basis_payload(actual_basis) != (
            expected_basis.to_evidence_payload() if expected_basis is not None else None
        ):
            raise KnowledgeArtifactError(
                f"knowledge_index.concepts.{path}.facets.structure.basis",
                "must match the manifest evidence state",
            )
        if expected_basis is None:
            expected_origin = Origin.UNKNOWN
            expected_evidence = EvidenceState.UNKNOWN
        else:
            expected_origin = Origin.EXTRACTED
            expected_evidence = (
                EvidenceState.PRESENT
                if expected_basis.is_known
                else EvidenceState.UNKNOWN
            )
        structure = concept.facets.structure
        if structure.origin is not expected_origin:
            raise KnowledgeArtifactError(
                f"knowledge_index.concepts.{path}.facets.structure.origin",
                "must match the manifest evidence state",
            )
        if structure.evidence is not expected_evidence:
            raise KnowledgeArtifactError(
                f"knowledge_index.concepts.{path}.facets.structure.evidence",
                "must match the manifest evidence state",
            )

    infrastructure = {
        concept.document.canonical_path: concept
        for concept in knowledge.concepts
        if concept.document.page_kind is PageKind.INFRASTRUCTURE
    }
    try:
        infrastructure_bases = infrastructure_evidence_by_page(
            manifest.generation_inputs
        )
    except InfrastructureSyncError as exc:
        raise KnowledgeArtifactError(
            "manifest.generation_inputs.infrastructure",
            str(exc),
        ) from exc
    raw_infrastructure_state = manifest.generation_inputs.get(
        INFRASTRUCTURE_GENERATION_INPUT_KEY
    )
    infrastructure_state_present = (
        isinstance(raw_infrastructure_state, Mapping)
        and raw_infrastructure_state.get("schema_version")
        == INFRASTRUCTURE_SYNC_SCHEMA_VERSION
    )
    if infrastructure_state_present and not set(infrastructure_bases).issubset(
        infrastructure
    ):
        missing = set(infrastructure_bases) - set(infrastructure)
        path = min(missing)
        raise KnowledgeArtifactError(
            "manifest.generation_inputs.infrastructure",
            f"maps missing active infrastructure page {path!r}",
        )
    for path, concept in infrastructure.items():
        expected_basis = infrastructure_bases.get(path)
        actual_basis = concept.facets.structure.basis
        expected_payload = (
            None
            if expected_basis is None
            else expected_basis.to_evidence_payload()
        )
        if _basis_payload(actual_basis) != expected_payload:
            raise KnowledgeArtifactError(
                f"knowledge_index.concepts.{path}.facets.structure.basis",
                "must match the persisted infrastructure evidence state",
            )
        surface_source = surface_by_path[path]["source_path"]
        if (
            expected_basis is not None
            and surface_source != expected_basis.source_path
        ):
            raise KnowledgeArtifactError(
                f"surface_index.pages.{path}.source_path",
                "must match the persisted infrastructure source mapping",
            )
        structure = concept.facets.structure
        expected_origin = (
            Origin.UNKNOWN if expected_basis is None else Origin.EXTRACTED
        )
        expected_evidence = (
            EvidenceState.UNKNOWN
            if expected_basis is None
            else EvidenceState.PRESENT
        )
        if structure.origin is not expected_origin:
            raise KnowledgeArtifactError(
                f"knowledge_index.concepts.{path}.facets.structure.origin",
                "must match the persisted infrastructure evidence state",
            )
        if structure.evidence is not expected_evidence:
            raise KnowledgeArtifactError(
                f"knowledge_index.concepts.{path}.facets.structure.evidence",
                "must match the persisted infrastructure evidence state",
            )


def _basis_payload(value: EvidenceBasis | None) -> dict[str, Any] | None:
    if value is None:
        return None
    payload: dict[str, Any] = {
        "scope": value.scope.value,
        "source_path": value.source_path,
        "extractor_ref": value.extractor_ref,
        "source_content_hash": value.source_content_hash,
    }
    if value.concept_observation_hash is not None:
        payload["concept_observation_hash"] = value.concept_observation_hash
    return payload


def _validate_surface_assets(
    surface: Mapping[str, Any],
    valid_page_paths: set[str],
) -> None:
    assets = surface.get("assets")
    if not isinstance(assets, Mapping):
        raise KnowledgeArtifactError("surface_index.assets", "must be an object")
    for name in ("by_page", "referenced", "unreferenced"):
        if name not in assets:
            raise KnowledgeArtifactError(f"surface_index.assets.{name}", "is required")
    by_page = assets["by_page"]
    if not isinstance(by_page, Mapping):
        raise KnowledgeArtifactError(
            "surface_index.assets.by_page",
            "must be an object",
        )
    referenced_by_page: set[str] = set()
    for page_path, asset_paths in by_page.items():
        if page_path not in valid_page_paths:
            raise KnowledgeArtifactError(
                "surface_index.assets.by_page",
                f"contains unknown canonical document {page_path!r}",
            )
        _validate_asset_path_list(
            asset_paths,
            f"surface_index.assets.by_page.{page_path}",
        )
        referenced_by_page.update(asset_paths)
    for name in ("referenced", "unreferenced"):
        _validate_asset_path_list(
            assets[name],
            f"surface_index.assets.{name}",
        )
    referenced = set(assets["referenced"])
    unreferenced = set(assets["unreferenced"])
    if referenced_by_page != referenced:
        raise KnowledgeArtifactError(
            "surface_index.assets.referenced",
            "must equal the unique asset paths recorded by page",
        )
    overlap = referenced & unreferenced
    if overlap:
        raise KnowledgeArtifactError(
            "surface_index.assets.unreferenced",
            f"must not also contain referenced asset {min(overlap)!r}",
        )


def _validate_surface_counts(
    surface: Mapping[str, Any],
    surface_by_path: Mapping[str, tuple[int, Mapping[str, Any]]],
) -> None:
    counts = surface["counts"]
    assert isinstance(counts, Mapping)
    _validate_exact_surface_keys(
        counts,
        "surface_index.counts",
        {"total", "by_kind", "dependency_architecture", "assets"},
    )
    actual_by_kind = Counter(page["kind"] for _index, page in surface_by_path.values())
    by_kind = counts["by_kind"]
    if not isinstance(by_kind, Mapping):
        raise KnowledgeArtifactError(
            "surface_index.counts.by_kind",
            "must be an object",
        )
    expected_kinds = {entry.kind.value for entry in iter_page_kinds()}
    _validate_exact_surface_keys(
        by_kind,
        "surface_index.counts.by_kind",
        expected_kinds,
    )
    for kind in sorted(expected_kinds):
        count = _nonnegative_integer(
            by_kind[kind],
            f"surface_index.counts.by_kind.{kind}",
        )
        if count != actual_by_kind[kind]:
            raise KnowledgeArtifactError(
                f"surface_index.counts.by_kind.{kind}",
                f"must equal the {actual_by_kind[kind]} active {kind!r} pages",
            )
    total = _nonnegative_integer(
        counts["total"],
        "surface_index.counts.total",
    )
    if total != len(surface_by_path):
        raise KnowledgeArtifactError(
            "surface_index.counts.total",
            f"must equal the {len(surface_by_path)} active pages",
        )
    expected_dependency_count = (
        actual_by_kind[PageKind.DEPENDENCIES.value]
        + actual_by_kind[PageKind.LOAD_ORDER.value]
    )
    dependency_count = _nonnegative_integer(
        counts["dependency_architecture"],
        "surface_index.counts.dependency_architecture",
    )
    if dependency_count != expected_dependency_count:
        raise KnowledgeArtifactError(
            "surface_index.counts.dependency_architecture",
            "must equal the dependencies and load-order page count",
        )
    _validate_surface_asset_counts(counts["assets"], surface["assets"])


def _validate_surface_asset_counts(
    value: object,
    assets_value: object,
) -> None:
    if not isinstance(value, Mapping):
        raise KnowledgeArtifactError(
            "surface_index.counts.assets",
            "must be an object",
        )
    if not isinstance(assets_value, Mapping):
        # The independently field-specific assets error is raised later.
        return
    _validate_exact_surface_keys(
        value,
        "surface_index.counts.assets",
        {"total", "referenced", "unreferenced", "by_media_type"},
    )
    count_values = {
        name: _nonnegative_integer(
            value[name],
            f"surface_index.counts.assets.{name}",
        )
        for name in ("total", "referenced", "unreferenced")
    }
    media = value["by_media_type"]
    if not isinstance(media, Mapping):
        raise KnowledgeArtifactError(
            "surface_index.counts.assets.by_media_type",
            "must be an object",
        )
    _validate_exact_surface_keys(
        media,
        "surface_index.counts.assets.by_media_type",
        {"image", "video", "other"},
    )
    media_counts = {
        name: _nonnegative_integer(
            media[name],
            f"surface_index.counts.assets.by_media_type.{name}",
        )
        for name in ("image", "video", "other")
    }
    if count_values["total"] != sum(media_counts.values()):
        raise KnowledgeArtifactError(
            "surface_index.counts.assets.total",
            "must equal the sum of the media-type counts",
        )
    if count_values["total"] != (
        count_values["referenced"] + count_values["unreferenced"]
    ):
        raise KnowledgeArtifactError(
            "surface_index.counts.assets.total",
            "must equal the referenced and unreferenced asset counts",
        )
    referenced = assets_value.get("referenced")
    unreferenced = assets_value.get("unreferenced")
    if isinstance(referenced, list) and count_values["referenced"] > len(referenced):
        raise KnowledgeArtifactError(
            "surface_index.counts.assets.referenced",
            "cannot exceed the number of recorded referenced asset paths",
        )
    if isinstance(unreferenced, list) and count_values["unreferenced"] != len(
        unreferenced
    ):
        raise KnowledgeArtifactError(
            "surface_index.counts.assets.unreferenced",
            "must equal the number of recorded unreferenced asset paths",
        )


def _validate_surface_dependency_pages(surface: Mapping[str, Any]) -> None:
    dependency_pages = surface["dependency_pages"]
    assert isinstance(dependency_pages, Mapping)
    _validate_exact_surface_keys(
        dependency_pages,
        "surface_index.dependency_pages",
        {"dependencies", "load_order", "count"},
    )
    by_kind = surface["counts"]["by_kind"]
    assert isinstance(by_kind, Mapping)
    for key, kind in (
        ("dependencies", PageKind.DEPENDENCIES),
        ("load_order", PageKind.LOAD_ORDER),
    ):
        value = dependency_pages[key]
        if not isinstance(value, bool):
            raise KnowledgeArtifactError(
                f"surface_index.dependency_pages.{key}",
                "must be a boolean",
            )
        expected = by_kind[kind.value] > 0
        if value is not expected:
            raise KnowledgeArtifactError(
                f"surface_index.dependency_pages.{key}",
                f"must be {expected!r} for the active page set",
            )
    count = _nonnegative_integer(
        dependency_pages["count"],
        "surface_index.dependency_pages.count",
    )
    if count != surface["counts"]["dependency_architecture"]:
        raise KnowledgeArtifactError(
            "surface_index.dependency_pages.count",
            "must equal counts.dependency_architecture",
        )


def _validate_asset_path_list(
    value: object,
    field: str,
) -> None:
    if not isinstance(value, list):
        raise KnowledgeArtifactError(field, "must be an array")
    for index, path in enumerate(value):
        if not _is_safe_relative_path(path) or not path.startswith("assets/"):
            raise KnowledgeArtifactError(
                f"{field}[{index}]",
                "must be a normalized assets/ path",
            )
    if len(value) != len(set(value)):
        raise KnowledgeArtifactError(field, "must not contain duplicates")


def _validate_surface_flows(
    surface: Mapping[str, Any],
    surface_by_path: Mapping[str, tuple[int, Mapping[str, Any]]],
) -> None:
    flows = surface.get("flows")
    if not isinstance(flows, list):
        raise KnowledgeArtifactError("surface_index.flows", "must be an array")
    flow_pages = {
        page["id"]: page
        for _page_index, page in surface_by_path.values()
        if page["kind"] == PageKind.FLOWS.value
    }
    seen_ids: set[str] = set()
    for index, flow in enumerate(flows):
        field = f"surface_index.flows[{index}]"
        if not isinstance(flow, Mapping):
            raise KnowledgeArtifactError(field, "must be an object")
        _validate_surface_keys(
            flow,
            field,
            {"id", "category", "entry_point"},
            {"detector", "language", "routes", "evidence"},
        )
        flow_id = flow["id"]
        if not isinstance(flow_id, str) or not flow_id:
            raise KnowledgeArtifactError(
                f"{field}.id",
                "must be a non-empty string",
            )
        if flow_id in seen_ids:
            raise KnowledgeArtifactError(
                f"{field}.id",
                f"duplicates flow {flow_id!r}",
            )
        seen_ids.add(flow_id)
        page = flow_pages.get(flow_id)
        if page is None:
            raise KnowledgeArtifactError(
                f"{field}.id",
                f"does not identify an active {PageKind.FLOWS.value!r} page",
            )
        category = flow["category"]
        if not isinstance(category, str) or not category:
            raise KnowledgeArtifactError(
                f"{field}.category",
                "must be a non-empty string",
            )
        entry_point = flow.get("entry_point")
        if not isinstance(entry_point, Mapping):
            raise KnowledgeArtifactError(f"{field}.entry_point", "must be an object")
        _validate_exact_surface_keys(
            entry_point,
            f"{field}.entry_point",
            {"symbol", "source_path", "label"},
        )
        for key in ("symbol", "label"):
            entry_value = entry_point[key]
            if entry_value is not None and not isinstance(entry_value, str):
                raise KnowledgeArtifactError(
                    f"{field}.entry_point.{key}",
                    "must be null or a string",
                )
        source_path = entry_point.get("source_path")
        if source_path is not None and not _is_safe_relative_path(source_path):
            raise KnowledgeArtifactError(
                f"{field}.entry_point.source_path",
                "must be null or a normalized repository-relative POSIX path",
            )
        if source_path != page["source_path"]:
            raise KnowledgeArtifactError(
                f"{field}.entry_point.source_path",
                "must match the corresponding flow page source path",
            )
        _validate_optional_surface_flow_fields(flow, field)
    missing = set(flow_pages) - seen_ids
    if missing:
        raise KnowledgeArtifactError(
            "surface_index.flows",
            f"is missing active flow page {min(missing)!r}",
        )


def _validate_optional_surface_flow_fields(
    flow: Mapping[str, Any],
    field: str,
) -> None:
    for key in ("detector", "language"):
        if key not in flow:
            continue
        value = flow[key]
        if not isinstance(value, str) or not value:
            raise KnowledgeArtifactError(
                f"{field}.{key}",
                "must be a non-empty string",
            )
    if "routes" in flow:
        _validate_surface_flow_routes(flow["routes"], f"{field}.routes")
    if "evidence" in flow:
        _validate_surface_flow_evidence(flow["evidence"], f"{field}.evidence")


def _validate_surface_flow_routes(value: object, field: str) -> None:
    if not isinstance(value, list):
        raise KnowledgeArtifactError(field, "must be an array")
    for index, route in enumerate(value):
        route_field = f"{field}[{index}]"
        if not isinstance(route, Mapping):
            raise KnowledgeArtifactError(route_field, "must be an object")
        _validate_exact_surface_keys(
            route,
            route_field,
            {"method", "path", "operation_id"},
        )
        for key in ("method", "path"):
            if not isinstance(route[key], str) or not route[key]:
                raise KnowledgeArtifactError(
                    f"{route_field}.{key}",
                    "must be a non-empty string",
                )
        operation_id = route["operation_id"]
        if operation_id is not None and (
            not isinstance(operation_id, str) or not operation_id
        ):
            raise KnowledgeArtifactError(
                f"{route_field}.operation_id",
                "must be null or a non-empty string",
            )


def _validate_surface_flow_evidence(value: object, field: str) -> None:
    if not isinstance(value, Mapping):
        raise KnowledgeArtifactError(field, "must be an object")
    _validate_exact_surface_keys(value, field, {"flow", "data_flow"})
    flow = value["flow"]
    if not isinstance(flow, Mapping):
        raise KnowledgeArtifactError(f"{field}.flow", "must be an object")
    _validate_exact_surface_keys(
        flow,
        f"{field}.flow",
        {"step_count", "truncated", "modules_touched"},
    )
    _nonnegative_integer(flow["step_count"], f"{field}.flow.step_count")
    if not isinstance(flow["truncated"], bool):
        raise KnowledgeArtifactError(
            f"{field}.flow.truncated",
            "must be a boolean",
        )
    modules = flow["modules_touched"]
    if not isinstance(modules, list):
        raise KnowledgeArtifactError(
            f"{field}.flow.modules_touched",
            "must be an array",
        )
    for index, source_path in enumerate(modules):
        if not _is_safe_relative_path(source_path):
            raise KnowledgeArtifactError(
                f"{field}.flow.modules_touched[{index}]",
                "must be a normalized repository-relative POSIX path",
            )
    if len(modules) != len(set(modules)):
        raise KnowledgeArtifactError(
            f"{field}.flow.modules_touched",
            "must not contain duplicates",
        )

    data_flow = value["data_flow"]
    if data_flow is None:
        return
    if not isinstance(data_flow, Mapping):
        raise KnowledgeArtifactError(
            f"{field}.data_flow",
            "must be null or an object",
        )
    _validate_exact_surface_keys(
        data_flow,
        f"{field}.data_flow",
        {
            "generated",
            "step_count",
            "transfer_count",
            "truncated",
            "boundary_effects",
            "gaps",
        },
    )
    if not isinstance(data_flow["generated"], bool):
        raise KnowledgeArtifactError(
            f"{field}.data_flow.generated",
            "must be a boolean",
        )
    for key in ("step_count", "transfer_count"):
        _nonnegative_integer(data_flow[key], f"{field}.data_flow.{key}")
    if not isinstance(data_flow["truncated"], bool):
        raise KnowledgeArtifactError(
            f"{field}.data_flow.truncated",
            "must be a boolean",
        )
    _validate_surface_flow_records(
        data_flow["boundary_effects"],
        f"{field}.data_flow.boundary_effects",
        {
            "step": str,
            "step_index": int,
            "kind": str,
            "target": str,
            "line": int,
            "confidence": str,
        },
    )
    _validate_surface_flow_records(
        data_flow["gaps"],
        f"{field}.data_flow.gaps",
        {
            "kind": str,
            "step": str,
            "target": str,
            "line": int,
        },
    )


def _validate_surface_flow_records(
    value: object,
    field: str,
    schema: Mapping[str, type],
) -> None:
    if not isinstance(value, list):
        raise KnowledgeArtifactError(field, "must be an array")
    for index, record in enumerate(value):
        record_field = f"{field}[{index}]"
        if not isinstance(record, Mapping):
            raise KnowledgeArtifactError(record_field, "must be an object")
        _validate_exact_surface_keys(record, record_field, set(schema))
        for key, expected_type in schema.items():
            item = record[key]
            item_field = f"{record_field}.{key}"
            if expected_type is int:
                _nonnegative_integer(item, item_field)
            elif not isinstance(item, expected_type) or not item:
                raise KnowledgeArtifactError(
                    item_field,
                    "must be a non-empty string",
                )


def _validate_surface_keys(
    value: Mapping[str, Any],
    field: str,
    required: set[str],
    optional: set[str],
) -> None:
    return require_shared_exact_fields(
        value,
        allowed=required | optional,
        required=required,
        mapping_error=KnowledgeArtifactError(field, "must be an object"),
        missing_error=lambda fields: KnowledgeArtifactError(
            f"{field}.{fields[0]}", "is required"
        ),
        unknown_error=lambda fields: KnowledgeArtifactError(
            f"{field}.{fields[0]}", "is not supported by surface-index v1"
        ),
    )


def _validate_exact_surface_keys(
    value: Mapping[str, Any],
    field: str,
    expected: set[str],
) -> None:
    _validate_surface_keys(value, field, expected, set())


def _nonnegative_integer(value: object, field: str) -> int:
    return require_nonnegative_int(
        value,
        error=KnowledgeArtifactError(field, "must be a non-negative integer"),
    )


def _is_safe_relative_path(value: object) -> bool:
    return is_portable_relative_path(value)


__all__ = [
    "KNOWLEDGE_INDEX_FILENAME",
    "ArtifactWriteState",
    "CommitStage",
    "KnowledgeArtifactError",
    "KnowledgeCommitPlan",
    "KnowledgeCommitResult",
    "PlannedArtifactWrite",
    "ValidatedKnowledgeArtifacts",
    "build_knowledge_commit_plan",
    "commit_knowledge_artifacts",
    "validate_knowledge_artifacts",
    "validate_surface_index_bytes",
]
