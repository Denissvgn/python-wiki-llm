"""Pure construction and validation of the native knowledge index.

This service is the join point for already evaluated inputs.  It never reads a
wiki or source file, rebuilds an inventory, invokes a producer, evaluates live
freshness, or writes an artifact.  Callers are responsible for supplying the
exact canonical Markdown strings, surface-index bytes, manifest evidence, and
link observations from the generation run being committed.
"""

from __future__ import annotations

import json
import posixpath
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

from .contracts import KNOWLEDGE_SCHEMA_VERSION
from .knowledge_envelope import (
    INVENTORY_HASH_EXTENSION,
    EvaluatedEnvelope,
    KnowledgeEnvelopeError,
    evaluated_envelope_to_payload,
    hash_markdown_snapshot,
)
from .knowledge_evidence import (
    ConceptObservationBasis,
    canonical_json_text,
    is_valid_sha256,
    sha256_bytes,
)
from .knowledge_links import (
    LinkObservation,
    LinkSyntax,
    is_valid_external_link_uri,
    is_valid_link_locator_target,
)
from .knowledge_model import (
    Actor,
    ActorKind,
    BundleRecord,
    ConceptFacets,
    ConceptKind,
    ConceptRecord,
    DocumentRecord,
    EvidenceBasis,
    EvidenceState,
    KnowledgeIndex,
    KnowledgeModelError,
    Lifecycle,
    ObservationScope,
    Origin,
    RelationshipEvidence,
    RelationshipKind,
    RelationshipLocation,
    RelationshipRecord,
    RelationshipTarget,
    Resolution,
    SemanticFacet,
    StructuralFacet,
    TargetClass,
    Verification,
    concept_kind_for_page_kind,
    parse_knowledge_index,
)
from .knowledge_model import (
    knowledge_index_to_payload as _model_to_payload,
)
from .knowledge_model import (
    serialize_knowledge_index as _serialize_model,
)
from .sync_manifest import (
    ManifestEvidenceBaseline,
    ManifestPageSource,
    ManifestTombstone,
)
from .validation import (
    contains_control_character as shared_contains_control_character,
    require_exact_fields,
    require_repository_relative_path,
)
from .wiki_media import (
    MarkdownLinkTarget,
    contains_uri_authority_userinfo,
    is_assets_path,
    iter_markdown_link_targets,
    iter_mermaid_click_targets,
    local_link_path,
    mask_fenced_code_blocks,
    media_type_for_path,
    normalize_markdown_link_target,
)
from .wiki_surface import (
    PageKind,
    SurfaceRole,
    WikiSurfaceError,
    WikiSurfacePage,
    iter_page_kinds,
)
from .wiki_surface import (
    canonical_path as wiki_canonical_path,
)
from .wiki_surface import (
    mcp_uri as wiki_mcp_uri,
)
from .wiki_surface_index import WIKI_SURFACE_INDEX_SCHEMA_VERSION

LINK_SYNTAX_EXTENSION = "llm-wiki/link-syntax"

_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_MALFORMED_PERCENT_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_MANIFEST_STRUCTURAL_PAGE_KINDS = frozenset(
    {PageKind.MODULES, PageKind.ENTITIES}
)
_STRUCTURAL_PAGE_KINDS = frozenset(
    {*_MANIFEST_STRUCTURAL_PAGE_KINDS, PageKind.INFRASTRUCTURE}
)
_STRUCTURAL_SCOPE_BY_PAGE_KIND = {
    PageKind.MODULES: ObservationScope.MODULE,
    PageKind.ENTITIES: ObservationScope.ENTITY,
    PageKind.INFRASTRUCTURE: ObservationScope.INFRASTRUCTURE,
}
_LINK_SYNTAX_VALUES = frozenset(member.value for member in LinkSyntax)
_SURFACE_KINDS = {entry.kind: entry for entry in iter_page_kinds()}


class KnowledgeIndexBuildError(ValueError):
    """Field-specific failure at the pure knowledge-index join boundary."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


# Shorter compatibility name for callers that treat build and validation
# failures as one service boundary.
KnowledgeIndexError = KnowledgeIndexBuildError


@dataclass(frozen=True)
class KnowledgeIndexInputs:
    """Already evaluated values required to construct one knowledge index."""

    envelope: EvaluatedEnvelope
    pages: Sequence[WikiSurfacePage]
    content_by_page: Mapping[str, str]
    surface_index_bytes: bytes
    page_source_mappings: Mapping[str, ManifestPageSource]
    evidence_baselines: Mapping[str, ManifestEvidenceBaseline]
    tombstones: Mapping[str, ManifestTombstone]
    link_observations: Sequence[LinkObservation]
    infrastructure_bases: Mapping[str, ConceptObservationBasis] = field(
        default_factory=dict
    )
    extensions: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class _SurfacePage:
    index: int
    canonical_path: str
    page_kind: PageKind
    page_id: str
    role: SurfaceRole
    locator: str
    title: str
    source_path: str | None


@dataclass(frozen=True)
class _JoinedPage:
    page: WikiSurfacePage
    surface: _SurfacePage
    content: str
    page_hash: str
    mapping: ManifestPageSource | None
    baseline: ManifestEvidenceBaseline | None
    tombstone: ManifestTombstone | None
    infrastructure_basis: ConceptObservationBasis | None

    @property
    def basis(self) -> ConceptObservationBasis | None:
        if self.infrastructure_basis is not None:
            return self.infrastructure_basis
        if self.baseline is not None:
            return self.baseline.basis
        if self.tombstone is not None:
            return self.tombstone.last_valid_basis
        return None


@dataclass(frozen=True)
class _BuildContext:
    bundle: BundleRecord
    joined_pages: tuple[_JoinedPage, ...]
    joined_by_path: Mapping[str, _JoinedPage]
    observations: tuple[LinkObservation, ...]


@dataclass(frozen=True)
class _ExpectedLinkOutcome:
    target_class: TargetClass
    resolution: Resolution | None
    canonical_path: str | None = None
    external_uri: str | None = None


class _InvalidSurfaceJson(ValueError):
    pass


def build_knowledge_index(inputs: KnowledgeIndexInputs) -> KnowledgeIndex:
    """Build one deterministic v1 knowledge index without performing I/O."""

    context = _validate_and_join_inputs(inputs)
    concepts = tuple(_concept_for_page(joined) for joined in context.joined_pages)
    relationships = [
        relationship
        for joined in context.joined_pages
        if (relationship := _derived_relationship(joined)) is not None
    ]
    relationships.extend(
        _link_relationship(observation, context.joined_by_path)
        for observation in context.observations
    )
    model = KnowledgeIndex(
        schema_version=KNOWLEDGE_SCHEMA_VERSION,
        bundle=context.bundle,
        concepts=concepts,
        relationships=tuple(relationships),
        extensions=inputs.extensions,
    )
    try:
        return validate_knowledge_index(model)
    except KnowledgeModelError as exc:
        raise KnowledgeIndexBuildError(exc.field, exc.reason) from exc


def validate_knowledge_index(
    value: KnowledgeIndex | object,
    *,
    inputs: KnowledgeIndexInputs | None = None,
) -> KnowledgeIndex:
    """Validate a model or decoded payload against the knowledge-index contract.

    Supplying ``inputs`` additionally proves that the model is exactly the
    projection of those evaluated inputs.
    """

    if isinstance(value, KnowledgeIndex):
        # The model serializer validates manually constructed dataclass graphs.
        model = parse_knowledge_index(_model_to_payload(value))
    else:
        model = parse_knowledge_index(value)
    _validate_builder_model(model)

    if inputs is not None:
        expected = build_knowledge_index(inputs)
        actual_payload = _model_to_payload(model)
        expected_payload = _model_to_payload(expected)
        if canonical_json_text(actual_payload) != canonical_json_text(expected_payload):
            field_name = _first_difference(actual_payload, expected_payload)
            raise KnowledgeIndexBuildError(
                field_name,
                "does not match the supplied evaluated knowledge-index inputs",
            )
    return model


def knowledge_index_to_payload(value: KnowledgeIndex | object) -> dict[str, Any]:
    """Validate and return the canonical JSON-compatible builder payload."""

    return _model_to_payload(validate_knowledge_index(value))


def serialize_knowledge_index(value: KnowledgeIndex | object) -> str:
    """Validate and serialize deterministically with one trailing newline."""

    return _serialize_model(validate_knowledge_index(value))


def _validate_and_join_inputs(inputs: KnowledgeIndexInputs) -> _BuildContext:
    if not isinstance(inputs, KnowledgeIndexInputs):
        raise TypeError("inputs must be a KnowledgeIndexInputs")
    bundle = _validated_bundle(inputs.envelope)
    pages, pages_by_path = _validated_pages(inputs.pages)
    content = _validated_content(inputs.content_by_page, pages_by_path)
    _validate_snapshot_commitments(
        bundle.snapshot.markdown_snapshot_hash,
        bundle.snapshot.surface_index_hash,
        content,
        inputs.surface_index_bytes,
    )
    surface_by_path = _surface_pages(inputs.surface_index_bytes)
    _require_exact_keys("surface_index.pages", pages_by_path, surface_by_path)

    mappings = _typed_mapping(
        inputs.page_source_mappings,
        "page_source_mappings",
        ManifestPageSource,
    )
    baselines = _typed_mapping(
        inputs.evidence_baselines,
        "evidence_baselines",
        ManifestEvidenceBaseline,
    )
    tombstones = _typed_mapping(
        inputs.tombstones,
        "tombstones",
        ManifestTombstone,
    )
    infrastructure_bases = _typed_mapping(
        inputs.infrastructure_bases,
        "infrastructure_bases",
        ConceptObservationBasis,
    )
    overlap = set(baselines) & set(tombstones)
    if overlap:
        path = min(overlap)
        raise KnowledgeIndexBuildError(
            f"evidence_baselines.{path}",
            "cannot also be supplied as a tombstone",
        )

    joined: list[_JoinedPage] = []
    extractor_ids = {component.component_id for component in bundle.producer.extractors}
    for page in pages:
        path = page.relative_path
        surface = surface_by_path[path]
        _validate_surface_page(surface, page)
        joined_page = _JoinedPage(
            page=page,
            surface=surface,
            content=content[path],
            page_hash=sha256_bytes(content[path].encode("utf-8")),
            mapping=mappings.get(path),
            baseline=baselines.get(path),
            tombstone=tombstones.get(path),
            infrastructure_basis=infrastructure_bases.get(path),
        )
        _validate_page_evidence(joined_page, extractor_ids)
        joined.append(joined_page)

    active_structural_paths = {
        page.relative_path
        for page in pages
        if page.kind in _MANIFEST_STRUCTURAL_PAGE_KINDS
    }
    _reject_extra_state("page_source_mappings", mappings, active_structural_paths)
    _reject_extra_state("evidence_baselines", baselines, active_structural_paths)
    _reject_extra_state("tombstones", tombstones, active_structural_paths)
    active_infrastructure_paths = {
        page.relative_path
        for page in pages
        if page.kind is PageKind.INFRASTRUCTURE
    }
    _reject_extra_state(
        "infrastructure_bases",
        infrastructure_bases,
        active_infrastructure_paths,
    )

    joined.sort(
        key=lambda item: (
            item.page.relative_path.casefold(),
            item.page.relative_path,
            item.page.mcp_uri,
        )
    )
    joined_by_path = {item.page.relative_path: item for item in joined}
    observations = _validated_observations(
        inputs.link_observations,
        joined_by_path,
    )
    return _BuildContext(
        bundle=bundle,
        joined_pages=tuple(joined),
        joined_by_path=joined_by_path,
        observations=observations,
    )


def _validated_bundle(envelope: object):
    if not isinstance(envelope, EvaluatedEnvelope):
        raise KnowledgeIndexBuildError(
            "envelope",
            "must be an already evaluated envelope",
        )
    try:
        evaluated_envelope_to_payload(envelope)
    except KnowledgeEnvelopeError as exc:
        raise KnowledgeIndexBuildError(
            f"envelope.{exc.field}",
            exc.message,
        ) from exc
    return envelope.bundle


def _validated_pages(
    value: object,
) -> tuple[tuple[WikiSurfacePage, ...], dict[str, WikiSurfacePage]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KnowledgeIndexBuildError(
            "pages",
            "must be a sequence of canonical wiki surface pages",
        )
    pages: list[WikiSurfacePage] = []
    by_path: dict[str, WikiSurfacePage] = {}
    locators: dict[str, int] = {}
    for index, page in enumerate(value):
        field_name = f"pages[{index}]"
        if not isinstance(page, WikiSurfacePage):
            raise KnowledgeIndexBuildError(field_name, "must be a WikiSurfacePage")
        if not isinstance(page.kind, PageKind):
            raise KnowledgeIndexBuildError(
                f"{field_name}.kind",
                "must be a canonical PageKind",
            )
        if not isinstance(page.role, SurfaceRole):
            raise KnowledgeIndexBuildError(
                f"{field_name}.role",
                "must be a canonical SurfaceRole",
            )
        expected_path, expected_locator = _expected_page_coordinates(page, field_name)
        expected_role = _SURFACE_KINDS[page.kind].role
        if page.relative_path != expected_path:
            raise KnowledgeIndexBuildError(
                f"{field_name}.relative_path",
                f"must match the registry-derived path {expected_path!r}",
            )
        if page.mcp_uri != expected_locator:
            raise KnowledgeIndexBuildError(
                f"{field_name}.mcp_uri",
                f"must match the registry-derived locator {expected_locator!r}",
            )
        if page.role is not expected_role:
            raise KnowledgeIndexBuildError(
                f"{field_name}.role",
                f"must match the registry role {expected_role.value!r}",
            )
        if page.relative_path in by_path:
            raise KnowledgeIndexBuildError(
                f"{field_name}.relative_path",
                "duplicates another active canonical page",
            )
        if page.mcp_uri in locators:
            raise KnowledgeIndexBuildError(
                f"{field_name}.mcp_uri",
                f"duplicates pages[{locators[page.mcp_uri]}].mcp_uri",
            )
        by_path[page.relative_path] = page
        locators[page.mcp_uri] = index
        pages.append(page)
    return tuple(pages), by_path


def _expected_page_coordinates(
    page: WikiSurfacePage,
    field_name: str,
) -> tuple[str, str]:
    try:
        return (
            wiki_canonical_path(page.kind, page.page_id),
            wiki_mcp_uri(page.kind, page.page_id),
        )
    except WikiSurfaceError:
        try:
            path = wiki_canonical_path(page.kind)
            locator = wiki_mcp_uri(page.kind)
        except WikiSurfaceError as exc:
            raise KnowledgeIndexBuildError(
                field_name,
                "contains an invalid page kind or identifier",
            ) from exc
        if page.page_id != page.kind.value:
            raise KnowledgeIndexBuildError(
                f"{field_name}.page_id",
                f"must be {page.kind.value!r} for a singleton page kind",
            )
        return path, locator


def _validated_content(
    value: object,
    pages_by_path: Mapping[str, WikiSurfacePage],
) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise KnowledgeIndexBuildError(
            "content_by_page",
            "must be a mapping of canonical paths to Markdown strings",
        )
    if any(not isinstance(key, str) for key in value):
        raise KnowledgeIndexBuildError(
            "content_by_page",
            "must use string canonical page paths",
        )
    _require_exact_keys("content_by_page", pages_by_path, value)
    result: dict[str, str] = {}
    for path in sorted(value):
        content = value[path]
        if not isinstance(content, str):
            raise KnowledgeIndexBuildError(
                f"content_by_page.{path}",
                "must be an exact Markdown string",
            )
        if _contains_surrogate(content):
            raise KnowledgeIndexBuildError(
                f"content_by_page.{path}",
                "must contain only Unicode scalar values",
            )
        result[path] = content
    return result


def _validate_snapshot_commitments(
    expected_markdown_hash: str,
    expected_surface_hash: str,
    content_by_page: Mapping[str, str],
    surface_index_bytes: object,
) -> None:
    if not isinstance(surface_index_bytes, bytes):
        raise KnowledgeIndexBuildError(
            "surface_index_bytes",
            "must be the exact persisted surface-index bytes",
        )
    try:
        markdown_hash = hash_markdown_snapshot(content_by_page)
    except KnowledgeEnvelopeError as exc:
        raise KnowledgeIndexBuildError(exc.field, exc.message) from exc
    if markdown_hash != expected_markdown_hash:
        raise KnowledgeIndexBuildError(
            "envelope.bundle.snapshot.markdown_snapshot_hash",
            "does not commit the supplied canonical Markdown pages",
        )
    if sha256_bytes(surface_index_bytes) != expected_surface_hash:
        raise KnowledgeIndexBuildError(
            "envelope.bundle.snapshot.surface_index_hash",
            "does not commit the supplied exact surface-index bytes",
        )


def _surface_pages(value: bytes) -> dict[str, _SurfacePage]:
    try:
        decoded = json.loads(
            value.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, _InvalidSurfaceJson) as exc:
        raise KnowledgeIndexBuildError(
            "surface_index_bytes",
            "must contain one finite UTF-8 JSON object without duplicate keys",
        ) from exc
    if not isinstance(decoded, dict):
        raise KnowledgeIndexBuildError(
            "surface_index_bytes",
            "must decode to a surface-index object",
        )
    if decoded.get("schema_version") != WIKI_SURFACE_INDEX_SCHEMA_VERSION:
        raise KnowledgeIndexBuildError(
            "surface_index.schema_version",
            f"must be {WIKI_SURFACE_INDEX_SCHEMA_VERSION!r}",
        )
    raw_pages = decoded.get("pages")
    if not isinstance(raw_pages, list):
        raise KnowledgeIndexBuildError(
            "surface_index.pages",
            "must be an array",
        )

    by_path: dict[str, _SurfacePage] = {}
    locators: dict[str, int] = {}
    for index, raw_page in enumerate(raw_pages):
        field_name = f"surface_index.pages[{index}]"
        if not isinstance(raw_page, dict):
            raise KnowledgeIndexBuildError(field_name, "must be an object")
        required = {"kind", "id", "role", "canonical_path", "mcp_uri", "title"}
        missing = required - set(raw_page)
        if missing:
            name = min(missing)
            raise KnowledgeIndexBuildError(f"{field_name}.{name}", "is required")
        try:
            page_kind = PageKind(raw_page["kind"])
        except (TypeError, ValueError) as exc:
            raise KnowledgeIndexBuildError(
                f"{field_name}.kind",
                "must be a canonical page kind",
            ) from exc
        try:
            role = SurfaceRole(raw_page["role"])
        except (TypeError, ValueError) as exc:
            raise KnowledgeIndexBuildError(
                f"{field_name}.role",
                "must be a canonical surface role",
            ) from exc
        page_id = _nonempty_string(raw_page["id"], f"{field_name}.id")
        path = _relative_path(
            raw_page["canonical_path"],
            f"{field_name}.canonical_path",
        )
        locator = _nonempty_string(raw_page["mcp_uri"], f"{field_name}.mcp_uri")
        title = _nonempty_string(raw_page["title"], f"{field_name}.title")
        source_path_value = raw_page.get("source_path")
        source_path = (
            None
            if source_path_value is None
            else _relative_path(source_path_value, f"{field_name}.source_path")
        )
        if path in by_path:
            raise KnowledgeIndexBuildError(
                f"{field_name}.canonical_path",
                "duplicates another surface-index page",
            )
        if locator in locators:
            raise KnowledgeIndexBuildError(
                f"{field_name}.mcp_uri",
                f"duplicates surface_index.pages[{locators[locator]}].mcp_uri",
            )
        by_path[path] = _SurfacePage(
            index=index,
            canonical_path=path,
            page_kind=page_kind,
            page_id=page_id,
            role=role,
            locator=locator,
            title=title,
            source_path=source_path,
        )
        locators[locator] = index
    return by_path


def _unique_json_object(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise _InvalidSurfaceJson(key)
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise _InvalidSurfaceJson(value)


def _validate_surface_page(
    surface: _SurfacePage,
    page: WikiSurfacePage,
) -> None:
    expected = {
        "kind": page.kind,
        "id": page.page_id,
        "role": page.role,
        "canonical_path": page.relative_path,
        "mcp_uri": page.mcp_uri,
    }
    actual = {
        "kind": surface.page_kind,
        "id": surface.page_id,
        "role": surface.role,
        "canonical_path": surface.canonical_path,
        "mcp_uri": surface.locator,
    }
    for name, expected_value in expected.items():
        if actual[name] != expected_value:
            raise KnowledgeIndexBuildError(
                f"surface_index.pages[{surface.index}].{name}",
                "does not match the active canonical page registry",
            )


def _typed_mapping(
    value: object,
    field_name: str,
    value_type: type,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeIndexBuildError(field_name, "must be a mapping")
    result: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise KnowledgeIndexBuildError(field_name, "must use string page paths")
        _relative_path(key, field_name)
        if not isinstance(item, value_type):
            raise KnowledgeIndexBuildError(
                f"{field_name}.{key}",
                f"must be a {value_type.__name__}",
            )
        result[key] = item
    return result


def _validate_page_evidence(
    joined: _JoinedPage,
    extractor_ids: set[str],
) -> None:
    path = joined.page.relative_path
    if joined.page.kind not in _STRUCTURAL_PAGE_KINDS:
        if any(
            value is not None
            for value in (
                joined.mapping,
                joined.baseline,
                joined.tombstone,
                joined.infrastructure_basis,
            )
        ):
            raise KnowledgeIndexBuildError(
                f"page_source_mappings.{path}",
                "structural evidence is only supported for source-backed pages",
            )
        return

    if joined.page.kind is PageKind.INFRASTRUCTURE:
        if any(
            value is not None
            for value in (joined.mapping, joined.baseline, joined.tombstone)
        ):
            raise KnowledgeIndexBuildError(
                f"page_source_mappings.{path}",
                "infrastructure evidence must use the persisted infrastructure basis",
            )
        basis = joined.infrastructure_basis
        if basis is None:
            # Legacy/snapshot-only infrastructure pages remain valid and
            # explicitly expose unknown structural evidence.
            return
        if basis.scope != ObservationScope.INFRASTRUCTURE.value:
            raise KnowledgeIndexBuildError(
                f"infrastructure_bases.{path}.scope",
                "must be 'infrastructure' for this page kind",
            )
        if joined.surface.source_path != basis.source_path:
            raise KnowledgeIndexBuildError(
                f"surface_index.pages[{joined.surface.index}].source_path",
                "must match the persisted infrastructure source mapping",
            )
        if basis.extractor_ref not in extractor_ids:
            raise KnowledgeIndexBuildError(
                f"infrastructure_bases.{path}.extractor_ref",
                "does not reference a declared producer extractor",
            )
        return

    if joined.infrastructure_basis is not None:
        raise KnowledgeIndexBuildError(
            f"infrastructure_bases.{path}",
            "is only supported for infrastructure pages",
        )
    if joined.baseline is None and joined.tombstone is None:
        raise KnowledgeIndexBuildError(
            f"evidence_baselines.{path}",
            "requires an evidence baseline or explicit tombstone state",
        )
    if joined.baseline is not None and joined.mapping is None:
        raise KnowledgeIndexBuildError(
            f"page_source_mappings.{path}",
            "is required for an active evidence baseline",
        )

    basis = joined.basis
    if basis is not None and joined.mapping is None:
        raise KnowledgeIndexBuildError(
            f"page_source_mappings.{path}",
            "is required when structural evidence carries a basis",
        )
    expected_scope = _STRUCTURAL_SCOPE_BY_PAGE_KIND[joined.page.kind].value
    if joined.mapping is not None:
        if joined.mapping.scope != expected_scope:
            raise KnowledgeIndexBuildError(
                f"page_source_mappings.{path}.scope",
                f"must be {expected_scope!r} for this page kind",
            )
        if (
            joined.surface.source_path is not None
            and joined.surface.source_path != joined.mapping.source_path
        ):
            raise KnowledgeIndexBuildError(
                f"surface_index.pages[{joined.surface.index}].source_path",
                "does not match the manifest page source mapping",
            )
        if joined.baseline is not None and (
            joined.surface.source_path != joined.mapping.source_path
        ):
            raise KnowledgeIndexBuildError(
                f"surface_index.pages[{joined.surface.index}].source_path",
                "must identify the current baseline source",
            )
    elif joined.surface.source_path is not None:
        raise KnowledgeIndexBuildError(
            f"surface_index.pages[{joined.surface.index}].source_path",
            "requires a matching manifest page source mapping",
        )
    if basis is not None:
        evidence_field = (
            "evidence_baselines" if joined.baseline is not None else "tombstones"
        )
        if basis.scope != expected_scope:
            raise KnowledgeIndexBuildError(
                f"{evidence_field}.{path}.basis.scope",
                f"must be {expected_scope!r} for this page kind",
            )
        assert joined.mapping is not None
        if basis.source_path != joined.mapping.source_path:
            raise KnowledgeIndexBuildError(
                f"{evidence_field}.{path}.basis.source_path",
                "does not match the manifest page source mapping",
            )
        if basis.extractor_ref not in extractor_ids:
            raise KnowledgeIndexBuildError(
                f"{evidence_field}.{path}.basis.extractor_ref",
                "does not reference a declared producer extractor",
            )


def _reject_extra_state(
    field_name: str,
    values: Mapping[str, Any],
    active_paths: set[str],
) -> None:
    extra = set(values) - active_paths
    if extra:
        path = min(extra)
        raise KnowledgeIndexBuildError(
            f"{field_name}.{path}",
            "does not identify an active page for this evidence mapping",
        )


def _validated_observations(
    value: object,
    joined_by_path: Mapping[str, _JoinedPage],
) -> tuple[LinkObservation, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KnowledgeIndexBuildError(
            "link_observations",
            "must be a sequence of lossless link observations",
        )
    result: list[LinkObservation] = []
    page_locator_by_path = {
        path: joined.page.mcp_uri for path, joined in joined_by_path.items()
    }
    parsed_by_source: dict[
        str,
        Mapping[
            tuple[LinkSyntax, int, int],
            tuple[MarkdownLinkTarget, ...],
        ],
    ] = {}
    observed_locations: dict[
        tuple[str, LinkSyntax, int, int],
        int,
    ] = {}
    for index, observation in enumerate(value):
        field_name = f"link_observations[{index}]"
        if not isinstance(observation, LinkObservation):
            raise KnowledgeIndexBuildError(
                field_name,
                "must be a LinkObservation",
            )
        for name in (
            "source_locator",
            "source_canonical_path",
            "raw_target",
            "normalized_target",
            "label",
        ):
            if not isinstance(getattr(observation, name), str):
                raise KnowledgeIndexBuildError(
                    f"{field_name}.{name}",
                    "must be a string",
                )
        for name in ("resolved_canonical_path", "external_uri"):
            endpoint = getattr(observation, name)
            if endpoint is not None and not isinstance(endpoint, str):
                raise KnowledgeIndexBuildError(
                    f"{field_name}.{name}",
                    "must be a string when present",
                )
        if not isinstance(observation.target_class, TargetClass):
            raise KnowledgeIndexBuildError(
                f"{field_name}.target_class",
                "must be a TargetClass",
            )
        if not isinstance(observation.resolution, Resolution):
            raise KnowledgeIndexBuildError(
                f"{field_name}.resolution",
                "must be a Resolution",
            )
        if not isinstance(observation.location, RelationshipLocation):
            raise KnowledgeIndexBuildError(
                f"{field_name}.location",
                "must be a RelationshipLocation",
            )
        if not isinstance(observation.syntax, LinkSyntax):
            raise KnowledgeIndexBuildError(
                f"{field_name}.syntax",
                "must identify the observed Markdown syntax",
            )
        if _observation_contains_authority_userinfo(observation):
            # Authority userinfo is credential-bearing under the v1 policy.
            # Omit the complete lossless observation rather than redacting it
            # into a misleading target.
            continue
        source = joined_by_path.get(observation.source_canonical_path)
        if source is None:
            raise KnowledgeIndexBuildError(
                f"{field_name}.source_canonical_path",
                "does not identify an active canonical page",
            )
        if observation.source_locator != source.page.mcp_uri:
            raise KnowledgeIndexBuildError(
                f"{field_name}.source_locator",
                "does not match the source page locator",
            )
        parsed_occurrences = parsed_by_source.get(source.page.relative_path)
        if parsed_occurrences is None:
            parsed_occurrences = _index_source_link_occurrences(source.content)
            parsed_by_source[source.page.relative_path] = parsed_occurrences
        location = observation.location
        if (
            isinstance(location.start, bool)
            or not isinstance(location.start, int)
            or isinstance(location.end, bool)
            or not isinstance(location.end, int)
            or location.start < 0
            or location.end <= location.start
            or location.end > len(source.content)
        ):
            raise KnowledgeIndexBuildError(
                f"{field_name}.location",
                "must be a non-empty half-open range within the exact source Markdown",
            )
        _validate_observation_source_syntax(
            observation,
            parsed_occurrences,
            field_name,
        )
        if observation.resolution is Resolution.AMBIGUOUS:
            raise KnowledgeIndexBuildError(
                f"{field_name}.resolution",
                "ambiguous internal target collision cannot be committed",
            )
        _validate_observation_endpoint(
            observation,
            source,
            joined_by_path,
            page_locator_by_path,
            field_name,
        )
        occurrence_key = (
            observation.source_canonical_path,
            observation.syntax,
            location.start,
            location.end,
        )
        if occurrence_key in observed_locations:
            raise KnowledgeIndexBuildError(
                f"{field_name}.location",
                f"duplicates link_observations"
                f"[{observed_locations[occurrence_key]}].location",
            )
        observed_locations[occurrence_key] = index
        result.append(observation)
    return tuple(result)


def _validate_observation_source_syntax(
    observation: LinkObservation,
    parsed_occurrences: Mapping[
        tuple[LinkSyntax, int, int],
        tuple[MarkdownLinkTarget, ...],
    ],
    field_name: str,
) -> None:
    location = observation.location
    matches = parsed_occurrences.get(
        (observation.syntax, location.start, location.end),
        (),
    )
    if len(matches) != 1:
        raise KnowledgeIndexBuildError(
            f"{field_name}.location",
            "does not identify exactly one supported link occurrence",
        )
    target = matches[0]
    expected = {
        "raw_target": target.raw_target,
        "normalized_target": target.target,
        "label": target.label,
    }
    for name, expected_value in expected.items():
        if getattr(observation, name) != expected_value:
            raise KnowledgeIndexBuildError(
                f"{field_name}.{name}",
                "does not match the link occurrence at the recorded location",
            )


def _index_source_link_occurrences(
    content: str,
) -> Mapping[
    tuple[LinkSyntax, int, int],
    tuple[MarkdownLinkTarget, ...],
]:
    indexed: dict[
        tuple[LinkSyntax, int, int],
        list[MarkdownLinkTarget],
    ] = {}
    for target in iter_markdown_link_targets(mask_fenced_code_blocks(content)):
        syntax = LinkSyntax.MARKDOWN_IMAGE if target.is_image else LinkSyntax.MARKDOWN
        indexed.setdefault((syntax, target.start, target.end), []).append(target)
    for target in iter_mermaid_click_targets(content):
        indexed.setdefault(
            (LinkSyntax.MERMAID_CLICK, target.start, target.end),
            [],
        ).append(target)
    return {key: tuple(targets) for key, targets in indexed.items()}


def _validate_observation_endpoint(
    observation: LinkObservation,
    source: _JoinedPage,
    joined_by_path: Mapping[str, _JoinedPage],
    page_locator_by_path: Mapping[str, str],
    field_name: str,
) -> None:
    expected = _expected_observation_outcome(
        observation,
        source.page.relative_path,
        page_locator_by_path,
    )
    if expected is None:
        if observation.target_class not in {
            TargetClass.UNKNOWN,
            TargetClass.ASSET,
        }:
            raise KnowledgeIndexBuildError(
                f"{field_name}.target_class",
                "must be 'unknown' or 'asset' for an unregistered local target",
            )
        allowed_resolutions = (
            {Resolution.UNRESOLVED}
            if observation.target_class is TargetClass.UNKNOWN
            else {Resolution.RESOLVED, Resolution.UNRESOLVED}
        )
        if observation.resolution not in allowed_resolutions:
            raise KnowledgeIndexBuildError(
                f"{field_name}.resolution",
                "does not match an unregistered local target",
            )
        if (
            observation.resolved_canonical_path is not None
            or observation.external_uri is not None
        ):
            raise KnowledgeIndexBuildError(
                f"{field_name}.resolved_canonical_path",
                "an unregistered local target cannot claim an endpoint",
            )
    else:
        if observation.target_class is not expected.target_class:
            raise KnowledgeIndexBuildError(
                f"{field_name}.target_class",
                f"must be {expected.target_class.value!r} for the normalized target",
            )
        if (
            expected.resolution is not None
            and observation.resolution is not expected.resolution
        ):
            raise KnowledgeIndexBuildError(
                f"{field_name}.resolution",
                f"must be {expected.resolution.value!r} for the normalized target",
            )
        if observation.resolved_canonical_path != expected.canonical_path:
            raise KnowledgeIndexBuildError(
                f"{field_name}.resolved_canonical_path",
                "does not match the normalized observed target",
            )
        if observation.external_uri != expected.external_uri:
            raise KnowledgeIndexBuildError(
                f"{field_name}.external_uri",
                "does not match the normalized observed target",
            )

    if observation.external_uri is not None:
        if (
            observation.target_class
            not in {
                TargetClass.EXTERNAL,
                TargetClass.MAIL,
            }
            or observation.resolution is not Resolution.EXTERNAL
        ):
            raise KnowledgeIndexBuildError(
                f"{field_name}.external_uri",
                "is only valid for an external or mail observation",
            )
        if observation.external_uri != observation.normalized_target:
            raise KnowledgeIndexBuildError(
                f"{field_name}.external_uri",
                "must equal the normalized observed target",
            )
    elif observation.target_class in {TargetClass.EXTERNAL, TargetClass.MAIL}:
        raise KnowledgeIndexBuildError(
            f"{field_name}.external_uri",
            "is required for an external or mail observation",
        )

    if observation.resolved_canonical_path is not None:
        if observation.resolved_canonical_path not in joined_by_path:
            raise KnowledgeIndexBuildError(
                f"{field_name}.resolved_canonical_path",
                "does not identify an active canonical page",
            )
        if (
            observation.target_class is not TargetClass.CONCEPT
            or observation.resolution is not Resolution.RESOLVED
        ):
            raise KnowledgeIndexBuildError(
                f"{field_name}.resolved_canonical_path",
                "is only valid for a resolved concept observation",
            )


def _expected_observation_outcome(
    observation: LinkObservation,
    source_path: str,
    page_locator_by_path: Mapping[str, str],
) -> _ExpectedLinkOutcome | None:
    normalized_target = observation.normalized_target
    if (
        not normalized_target
        or _contains_control_character(normalized_target)
        or _MALFORMED_PERCENT_RE.search(normalized_target)
        or _WINDOWS_ABSOLUTE_RE.match(normalized_target)
    ):
        return _ExpectedLinkOutcome(
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
        )
    if normalized_target.startswith("#"):
        return _ExpectedLinkOutcome(TargetClass.ANCHOR, Resolution.RESOLVED)
    try:
        parsed = urlsplit(normalized_target)
        _ = parsed.port
    except ValueError:
        return _ExpectedLinkOutcome(
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
        )
    if parsed.scheme.casefold() == "llm-wiki":
        if not is_valid_link_locator_target(normalized_target):
            return _ExpectedLinkOutcome(
                TargetClass.MALFORMED,
                Resolution.UNRESOLVED,
            )
        locator = normalized_target.partition("#")[0]
        path = next(
            (
                path
                for path, page_locator in page_locator_by_path.items()
                if page_locator == locator
            ),
            None,
        )
        return _ExpectedLinkOutcome(
            TargetClass.CONCEPT,
            Resolution.RESOLVED if path is not None else Resolution.UNRESOLVED,
            canonical_path=path,
        )
    if parsed.scheme:
        if not is_valid_external_link_uri(normalized_target):
            return _ExpectedLinkOutcome(
                TargetClass.MALFORMED,
                Resolution.UNRESOLVED,
            )
        target_class = (
            TargetClass.MAIL
            if parsed.scheme.casefold() == "mailto"
            else TargetClass.EXTERNAL
        )
        return _ExpectedLinkOutcome(
            target_class,
            Resolution.EXTERNAL,
            external_uri=normalized_target,
        )
    if parsed.netloc:
        return _ExpectedLinkOutcome(TargetClass.UNKNOWN, Resolution.UNRESOLVED)
    if normalized_target.startswith(("/", "\\")):
        return _ExpectedLinkOutcome(
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
        )
    local_path = local_link_path(normalized_target)
    if (
        local_path is None
        or posixpath.isabs(local_path)
        or _WINDOWS_ABSOLUTE_RE.match(local_path)
        or _contains_control_character(local_path)
    ):
        return _ExpectedLinkOutcome(
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
        )
    candidate = posixpath.normpath(
        posixpath.join(posixpath.dirname(source_path), local_path)
    )
    if candidate == ".." or candidate.startswith("../") or posixpath.isabs(candidate):
        return _ExpectedLinkOutcome(
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
        )
    if (
        observation.syntax is LinkSyntax.MARKDOWN_IMAGE
        or is_assets_path(candidate)
        or media_type_for_path(local_path) is not None
    ):
        # Existing asset membership was evaluated during link collection but is
        # intentionally not reintroduced as a knowledge-index input. Its class is
        # deterministic here; resolved versus unresolved remains trusted.
        return _ExpectedLinkOutcome(TargetClass.ASSET, None)
    if candidate in page_locator_by_path:
        return _ExpectedLinkOutcome(
            TargetClass.CONCEPT,
            Resolution.RESOLVED,
            canonical_path=candidate,
        )
    if posixpath.splitext(candidate)[1].casefold() == ".md":
        return _ExpectedLinkOutcome(
            TargetClass.CONCEPT,
            Resolution.UNRESOLVED,
        )
    # A caller-supplied existing asset set can classify any other normalized
    # local path as an asset. No endpoint coordinate can be proven here.
    return None


def _contains_control_character(value: str) -> bool:
    return shared_contains_control_character(
        value,
        reject_delete_character=True,
    )


def _observation_contains_authority_userinfo(
    observation: LinkObservation,
) -> bool:
    return any(
        contains_uri_authority_userinfo(value)
        for value in (
            observation.raw_target,
            observation.normalized_target,
            observation.external_uri,
        )
        if value is not None
    )


def _concept_for_page(joined: _JoinedPage) -> ConceptRecord:
    concept_kind = concept_kind_for_page_kind(joined.page.kind)
    return ConceptRecord(
        locator=joined.page.mcp_uri,
        concept_kind=concept_kind,
        title=joined.surface.title,
        document=DocumentRecord(
            page_kind=joined.page.kind,
            page_id=joined.page.page_id,
            canonical_path=joined.page.relative_path,
            role=joined.page.role,
        ),
        facets=ConceptFacets(
            structure=_structural_facet(joined, concept_kind),
            semantics=SemanticFacet(
                ownership=joined.page.role,
                page_hash=joined.page_hash,
                authorship=Actor(),
                verification=Verification.UNTRACKED,
            ),
        ),
        lifecycle=Lifecycle.UNKNOWN,
    )


def _structural_facet(
    joined: _JoinedPage,
    concept_kind: ConceptKind,
) -> StructuralFacet:
    if concept_kind.is_document_only:
        return StructuralFacet(
            origin=Origin.UNKNOWN,
            evidence=EvidenceState.NOT_APPLICABLE,
        )
    if joined.page.kind not in _STRUCTURAL_PAGE_KINDS:
        return StructuralFacet()
    basis = joined.basis
    if basis is None:
        return StructuralFacet()
    return StructuralFacet(
        origin=Origin.EXTRACTED,
        evidence=(EvidenceState.PRESENT if basis.is_known else EvidenceState.UNKNOWN),
        basis=_evidence_basis(basis),
    )


def _evidence_basis(value: ConceptObservationBasis) -> EvidenceBasis:
    return EvidenceBasis(
        scope=ObservationScope(value.scope),
        source_path=value.source_path,
        extractor_ref=value.extractor_ref,
        source_content_hash=value.source_content_hash,
        concept_observation_hash=value.concept_observation_hash,
    )


def _derived_relationship(joined: _JoinedPage) -> RelationshipRecord | None:
    basis = joined.basis
    if basis is None:
        return None
    state = EvidenceState.PRESENT if basis.is_known else EvidenceState.UNKNOWN
    return RelationshipRecord(
        kind=RelationshipKind.DERIVED_FROM,
        source_locator=joined.page.mcp_uri,
        target=RelationshipTarget(
            target_class=TargetClass.SOURCE,
            source_path=basis.source_path,
        ),
        origin=Origin.EXTRACTED,
        evidence=RelationshipEvidence(
            state=state,
            source_content_hash=basis.source_content_hash,
            concept_observation_hash=basis.concept_observation_hash,
        ),
        resolution=Resolution.RESOLVED,
    )


def _link_relationship(
    observation: LinkObservation,
    joined_by_path: Mapping[str, _JoinedPage],
) -> RelationshipRecord:
    source = joined_by_path[observation.source_canonical_path]
    return RelationshipRecord(
        kind=RelationshipKind.LINKS_TO,
        source_locator=observation.source_locator,
        target=RelationshipTarget(
            target_class=observation.target_class,
            canonical_path=observation.resolved_canonical_path,
            external_uri=observation.external_uri,
            raw_target=observation.raw_target,
            normalized_target=observation.normalized_target,
            label=observation.label,
            location=observation.location,
        ),
        origin=Origin.MARKDOWN,
        evidence=RelationshipEvidence(
            state=EvidenceState.PRESENT,
            page_hash=source.page_hash,
        ),
        resolution=observation.resolution,
        extensions={LINK_SYNTAX_EXTENSION: observation.syntax.value},
    )


def _validate_builder_model(model: KnowledgeIndex) -> None:
    inventory_hash = model.bundle.snapshot.extensions.get(INVENTORY_HASH_EXTENSION)
    if not is_valid_sha256(inventory_hash):
        raise KnowledgeModelError(
            f"bundle.snapshot.extensions.{INVENTORY_HASH_EXTENSION}",
            "must carry the evaluated inventory hash",
        )

    concepts = {concept.locator: concept for concept in model.concepts}
    from .knowledge_governance import GOVERNANCE_EXTENSION_KEY

    governed = GOVERNANCE_EXTENSION_KEY in model.extensions
    page_locator_by_path = {
        concept.document.canonical_path: concept.locator for concept in model.concepts
    }
    extractor_ids = {
        component.component_id for component in model.bundle.producer.extractors
    }
    derived_by_source: dict[str, list[tuple[int, RelationshipRecord]]] = {}
    for index, concept in enumerate(model.concepts):
        concept_path = f"concepts[{index}]"
        expected_kind = concept_kind_for_page_kind(concept.document.page_kind)
        if concept.concept_kind is not expected_kind:
            raise KnowledgeModelError(
                f"{concept_path}.concept_kind",
                f"must be {expected_kind.value!r} for knowledge-index construction",
            )
        if not governed and concept.lifecycle is not Lifecycle.UNKNOWN:
            raise KnowledgeModelError(
                f"{concept_path}.lifecycle",
                "must be 'unknown' for knowledge-index construction without governance",
            )
        semantics = concept.facets.semantics
        if semantics.authorship.kind is not ActorKind.UNKNOWN:
            raise KnowledgeModelError(
                f"{concept_path}.facets.semantics.authorship.kind",
                "must be 'unknown' for knowledge-index construction",
            )
        if semantics.verification is not Verification.UNTRACKED:
            raise KnowledgeModelError(
                f"{concept_path}.facets.semantics.verification",
                "must be 'untracked' for knowledge-index construction",
            )

        structure = concept.facets.structure
        basis = structure.basis
        if expected_kind.is_document_only:
            _require_structure_state(
                structure,
                concept_path,
                origin=Origin.UNKNOWN,
                evidence=EvidenceState.NOT_APPLICABLE,
                allows_basis=False,
            )
        elif concept.document.page_kind not in _STRUCTURAL_PAGE_KINDS or basis is None:
            _require_structure_state(
                structure,
                concept_path,
                origin=Origin.UNKNOWN,
                evidence=EvidenceState.UNKNOWN,
                allows_basis=False,
            )
        else:
            expected_scope = _STRUCTURAL_SCOPE_BY_PAGE_KIND[
                concept.document.page_kind
            ]
            if basis.scope is not expected_scope:
                raise KnowledgeModelError(
                    f"{concept_path}.facets.structure.basis.scope",
                    f"must be {expected_scope.value!r} for this page kind",
                )
            for name in ("source_path", "extractor_ref", "source_content_hash"):
                if getattr(basis, name) is None:
                    raise KnowledgeModelError(
                        f"{concept_path}.facets.structure.basis.{name}",
                        "is required for a source-backed observation basis",
                    )
            if basis.extractor_ref not in extractor_ids:
                raise KnowledgeModelError(
                    f"{concept_path}.facets.structure.basis.extractor_ref",
                    "must reference a declared producer extractor",
                )
            if basis.aggregate_input_hash is not None:
                raise KnowledgeModelError(
                    f"{concept_path}.facets.structure.basis.aggregate_input_hash",
                    "is not emitted for source-backed observation bases",
                )
            expected_evidence = (
                EvidenceState.PRESENT
                if basis.concept_observation_hash is not None
                else EvidenceState.UNKNOWN
            )
            _require_structure_state(
                structure,
                concept_path,
                origin=Origin.EXTRACTED,
                evidence=expected_evidence,
                allows_basis=True,
            )

    for index, relationship in enumerate(model.relationships):
        path = f"relationships[{index}]"
        source = concepts[relationship.source_locator]
        if relationship.kind is RelationshipKind.LINKS_TO:
            _validate_builder_link(
                relationship,
                source,
                page_locator_by_path,
                path,
            )
        elif relationship.kind is RelationshipKind.DERIVED_FROM:
            derived_by_source.setdefault(relationship.source_locator, []).append(
                (index, relationship)
            )
            _validate_builder_derived(relationship, source, path)
        else:
            raise KnowledgeModelError(
                f"{path}.kind",
                "the knowledge index emits only 'derived_from' and 'links_to'",
            )

    for index, concept in enumerate(model.concepts):
        relationships = derived_by_source.get(concept.locator, [])
        expected_count = 1 if concept.facets.structure.basis is not None else 0
        if len(relationships) != expected_count:
            raise KnowledgeModelError(
                f"concepts[{index}].facets.structure.basis",
                "must have exactly one matching derived_from relationship"
                if expected_count
                else "must not have a derived_from relationship without a basis",
            )


def _require_structure_state(
    structure: StructuralFacet,
    concept_path: str,
    *,
    origin: Origin,
    evidence: EvidenceState,
    allows_basis: bool,
) -> None:
    path = f"{concept_path}.facets.structure"
    if structure.origin is not origin:
        raise KnowledgeModelError(
            f"{path}.origin",
            f"must be {origin.value!r} for knowledge-index construction",
        )
    if structure.evidence is not evidence:
        raise KnowledgeModelError(
            f"{path}.evidence",
            f"must be {evidence.value!r} for knowledge-index construction",
        )
    if not allows_basis and structure.basis is not None:
        raise KnowledgeModelError(
            f"{path}.basis",
            "must be absent for this knowledge-index structural state",
        )


def _validate_builder_link(
    relationship: RelationshipRecord,
    source: ConceptRecord,
    page_locator_by_path: Mapping[str, str],
    path: str,
) -> None:
    if relationship.origin is not Origin.MARKDOWN:
        raise KnowledgeModelError(
            f"{path}.origin",
            "must be 'markdown' for a knowledge-index link observation",
        )
    evidence = relationship.evidence
    if evidence.state is not EvidenceState.PRESENT:
        raise KnowledgeModelError(
            f"{path}.evidence.state",
            "must be 'present' for a knowledge-index link observation",
        )
    if evidence.page_hash != source.facets.semantics.page_hash:
        raise KnowledgeModelError(
            f"{path}.evidence.page_hash",
            "must match the source document semantic page hash",
        )
    for name in (
        "source_content_hash",
        "concept_observation_hash",
        "aggregate_input_hash",
    ):
        if getattr(evidence, name) is not None:
            raise KnowledgeModelError(
                f"{path}.evidence.{name}",
                "is not emitted for a knowledge-index link observation",
            )
    syntax = relationship.extensions.get(LINK_SYNTAX_EXTENSION)
    if syntax not in _LINK_SYNTAX_VALUES:
        raise KnowledgeModelError(
            f"{path}.extensions.{LINK_SYNTAX_EXTENSION}",
            "must identify markdown, markdown-image, or mermaid-click syntax",
        )
    target = relationship.target
    assert target.raw_target is not None
    assert target.normalized_target is not None
    for name, value in (
        ("raw_target", target.raw_target),
        ("normalized_target", target.normalized_target),
        ("external_uri", target.external_uri),
    ):
        if value is not None and contains_uri_authority_userinfo(value):
            raise KnowledgeModelError(
                f"{path}.target.{name}",
                "must not contain credential-bearing URI authority userinfo",
            )
    if normalize_markdown_link_target(target.raw_target) != target.normalized_target:
        raise KnowledgeModelError(
            f"{path}.target.normalized_target",
            "must match normalization of the raw target",
        )
    if target.locator is not None or target.source_path is not None:
        raise KnowledgeModelError(
            f"{path}.target",
            "knowledge-index links never emit locator or source_path endpoints",
        )
    observation = LinkObservation(
        source_locator=relationship.source_locator,
        source_canonical_path=source.document.canonical_path,
        raw_target=target.raw_target,
        normalized_target=target.normalized_target,
        label=target.label or "",
        location=target.location or RelationshipLocation(start=0, end=1),
        target_class=target.target_class,
        resolution=relationship.resolution,
        resolved_canonical_path=target.canonical_path,
        external_uri=target.external_uri,
        syntax=LinkSyntax(syntax),
    )
    expected = _expected_observation_outcome(
        observation,
        source.document.canonical_path,
        page_locator_by_path,
    )
    if expected is None:
        if target.target_class not in {TargetClass.UNKNOWN, TargetClass.ASSET}:
            raise KnowledgeModelError(
                f"{path}.target.target_class",
                "must be 'unknown' or 'asset' for an unregistered local target",
            )
        allowed_resolutions = (
            {Resolution.UNRESOLVED}
            if target.target_class is TargetClass.UNKNOWN
            else {Resolution.RESOLVED, Resolution.UNRESOLVED}
        )
        if relationship.resolution not in allowed_resolutions:
            raise KnowledgeModelError(
                f"{path}.resolution",
                "does not match an unregistered local target",
            )
        if target.canonical_path is not None or target.external_uri is not None:
            raise KnowledgeModelError(
                f"{path}.target",
                "an unregistered local target cannot claim an endpoint",
            )
    else:
        if target.target_class is not expected.target_class:
            raise KnowledgeModelError(
                f"{path}.target.target_class",
                f"must be {expected.target_class.value!r} for the normalized target",
            )
        if (
            expected.resolution is not None
            and relationship.resolution is not expected.resolution
        ):
            raise KnowledgeModelError(
                f"{path}.resolution",
                f"must be {expected.resolution.value!r} for the normalized target",
            )
        if target.canonical_path != expected.canonical_path:
            raise KnowledgeModelError(
                f"{path}.target.canonical_path",
                "does not match the normalized target",
            )
        if target.external_uri != expected.external_uri:
            raise KnowledgeModelError(
                f"{path}.target.external_uri",
                "does not match the normalized target",
            )
    if relationship.resolution is Resolution.AMBIGUOUS:
        raise KnowledgeModelError(
            f"{path}.resolution",
            "ambiguous internal target collision cannot be committed",
        )
    if target.external_uri is not None and (
        target.external_uri != target.normalized_target
    ):
        raise KnowledgeModelError(
            f"{path}.target.external_uri",
            "must equal the normalized observed target",
        )


def _validate_builder_derived(
    relationship: RelationshipRecord,
    source: ConceptRecord,
    path: str,
) -> None:
    basis = source.facets.structure.basis
    if basis is None:
        raise KnowledgeModelError(
            f"{path}.from",
            "derived_from requires a structural basis on its source concept",
        )
    if relationship.origin is not Origin.EXTRACTED:
        raise KnowledgeModelError(
            f"{path}.origin",
            "must be 'extracted' for knowledge-index derived evidence",
        )
    if relationship.target.target_class is not TargetClass.SOURCE:
        raise KnowledgeModelError(
            f"{path}.target.target_class",
            "must be 'source' for knowledge-index derived evidence",
        )
    target = relationship.target
    if any(
        value is not None
        for value in (
            target.locator,
            target.canonical_path,
            target.external_uri,
            target.raw_target,
            target.normalized_target,
            target.label,
            target.location,
        )
    ):
        raise KnowledgeModelError(
            f"{path}.target",
            "knowledge-index derived evidence emits only source_path and target_class",
        )
    if relationship.target.source_path != basis.source_path:
        raise KnowledgeModelError(
            f"{path}.target.source_path",
            "must match the source concept structural basis",
        )
    expected_state = (
        EvidenceState.PRESENT
        if basis.concept_observation_hash is not None
        else EvidenceState.UNKNOWN
    )
    if relationship.evidence.state is not expected_state:
        raise KnowledgeModelError(
            f"{path}.evidence.state",
            f"must be {expected_state.value!r} for the source structural basis",
        )
    if relationship.evidence.concept_observation_hash != basis.concept_observation_hash:
        raise KnowledgeModelError(
            f"{path}.evidence.concept_observation_hash",
            "must match the source concept structural basis",
        )
    if relationship.evidence.source_content_hash != basis.source_content_hash:
        raise KnowledgeModelError(
            f"{path}.evidence.source_content_hash",
            "must match the source concept structural basis",
        )
    for name in ("page_hash", "aggregate_input_hash"):
        if getattr(relationship.evidence, name) is not None:
            raise KnowledgeModelError(
                f"{path}.evidence.{name}",
                "is not emitted for knowledge-index derived evidence",
            )


def _require_exact_keys(
    field_name: str,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
) -> None:
    return require_exact_fields(
        actual,
        allowed=expected,
        required=expected,
        mapping_error=KnowledgeIndexBuildError(field_name, "must be a mapping"),
        missing_error=lambda fields: KnowledgeIndexBuildError(
            field_name,
            f"is missing active canonical page {fields[0]!r}",
        ),
        unknown_error=lambda fields: KnowledgeIndexBuildError(
            field_name,
            f"contains unknown canonical page {fields[0]!r}",
        ),
    )


def _relative_path(value: object, field_name: str) -> str:
    text = _nonempty_string(value, field_name)
    return require_repository_relative_path(
        text,
        text_error=KnowledgeIndexBuildError(
            field_name, "must be a non-empty normalized string"
        ),
        posix_error=KnowledgeIndexBuildError(
            field_name, "must be a normalized path without empty or dot segments"
        ),
        normalized_error=KnowledgeIndexBuildError(
            field_name, "must be a normalized path without empty or dot segments"
        ),
        absolute_error=KnowledgeIndexBuildError(
            field_name, "must be repository-relative"
        ),
        separator_error=KnowledgeIndexBuildError(
            field_name, "must use POSIX '/' separators"
        ),
    )


def _nonempty_string(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
        or _contains_surrogate(value)
    ):
        raise KnowledgeIndexBuildError(
            field_name,
            "must be a non-empty normalized string",
        )
    return value


def _contains_surrogate(value: str) -> bool:
    return any(0xD800 <= ord(character) <= 0xDFFF for character in value)


def _first_difference(actual: Any, expected: Any, path: str = "model") -> str:
    if isinstance(actual, dict) and isinstance(expected, dict):
        for key in sorted(set(actual) | set(expected)):
            child = f"{path}.{key}"
            if key not in actual or key not in expected:
                return child
            difference = _first_difference(actual[key], expected[key], child)
            if difference:
                return difference
        return ""
    if isinstance(actual, list) and isinstance(expected, list):
        for index, (left, right) in enumerate(zip(actual, expected)):
            difference = _first_difference(left, right, f"{path}[{index}]")
            if difference:
                return difference
        return f"{path}.length" if len(actual) != len(expected) else ""
    return path if canonical_json_text(actual) != canonical_json_text(expected) else ""


__all__ = [
    "LINK_SYNTAX_EXTENSION",
    "KnowledgeIndexBuildError",
    "KnowledgeIndexError",
    "KnowledgeIndexInputs",
    "build_knowledge_index",
    "knowledge_index_to_payload",
    "serialize_knowledge_index",
    "validate_knowledge_index",
]
