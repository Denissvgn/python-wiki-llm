"""Typed contract and stdlib validation for ``llm-wiki-knowledge/v1``.

The persisted knowledge index is a generated observation read model. It stores
the basis needed for a later freshness comparison, but never stores a timeless
freshness verdict. :class:`ComputedFreshness` is therefore a consumer-side
vocabulary only and is not a field on any persisted dataclass.

Core record objects reject unknown fields. Forward-compatible data belongs in
an explicit ``extensions`` object whose keys use ``namespace/name`` syntax.
Unknown concept and relationship kinds are accepted only when similarly
qualified; unqualified unknown values are treated as likely typos.

This module is deliberately pure over supplied Python values. It does not read
or write knowledge artifacts, scan source, invoke helpers, or evaluate live
freshness. Loading the packaged JSON Schema is the sole resource read.
"""

from __future__ import annotations

import json
import math
import posixpath
import re
from dataclasses import dataclass, field
from enum import Enum
from importlib import resources
from types import MappingProxyType
from typing import AbstractSet, Any, Mapping, Optional, Type, TypeVar, Union
from urllib.parse import unquote, urlsplit

from . import wiki_surface
from .contracts import KNOWLEDGE_SCHEMA_FILENAME, KNOWLEDGE_SCHEMA_VERSION
from .knowledge_evidence import SHA256_PATTERN, is_valid_sha256
from .wiki_media import contains_uri_authority_userinfo
from .wiki_surface import (
    PageKind,
    SurfaceRole,
    is_safe_page_id,
    iter_page_kinds,
)

QUALIFIED_NAME_PATTERN = r"^[A-Za-z][A-Za-z0-9._-]*/[A-Za-z][A-Za-z0-9._-]*$"
REPOSITORY_IDENTITY_PATTERN = (
    r"^(?!.*[\u0000-\u001F])(?:unknown|[a-z0-9][a-z0-9._-]*"
    r"(?:/[A-Za-z0-9][A-Za-z0-9._-]*)+)$"
)
EVALUATED_REVISION_PATTERN = (
    r"^(?!.*[\u0000-\u001F])"
    r"(?:unknown|git:(?:[0-9a-f]{40}|[0-9a-f]{64}))$"
)
LIMITATION_CODE_PATTERN = (
    r"^(?!.*[\u0000-\u001F])"
    r"[a-z][a-z0-9.-]*(?:/[a-z][a-z0-9.-]*)?$"
)
REPOSITORY_IDENTITY_SOURCE_EXTENSION = "llm-wiki/identity-source"

_QUALIFIED_NAME_RE = re.compile(QUALIFIED_NAME_PATTERN)
_REPOSITORY_IDENTITY_RE = re.compile(REPOSITORY_IDENTITY_PATTERN)
_EVALUATED_REVISION_RE = re.compile(EVALUATED_REVISION_PATTERN)
_LIMITATION_CODE_RE = re.compile(LIMITATION_CODE_PATTERN)
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:/")
_PERCENT_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_COMPONENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_URI_CHAR_RE = re.compile(r"^[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+$")
_MISSING = object()
_MAX_LOCATION_OFFSET = (2**63) - 1


class KnowledgeModelError(ValueError):
    """Raised when a knowledge payload violates the v1 contract."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.reason = message
        super().__init__(f"{field}: {message}")


class ConceptKind(str, Enum):
    """Versioned domain taxonomy independent of the current page layout."""

    SOURCE_MODULE = "source-module"
    CODE_ENTITY = "code-entity"
    WORKFLOW = "workflow"
    GUIDE = "guide"
    USER_FLOW = "user-flow"
    INFRASTRUCTURE_RESOURCE = "infrastructure-resource"
    API_CONTRACT = "api-contract"
    DEPENDENCY_VIEW = "dependency-view"
    NAVIGATION_DOCUMENT = "navigation-document"
    CHANGE_LOG_DOCUMENT = "change-log-document"

    @property
    def is_document_only(self) -> bool:
        return self in {
            ConceptKind.NAVIGATION_DOCUMENT,
            ConceptKind.CHANGE_LOG_DOCUMENT,
        }


class Origin(str, Enum):
    UNKNOWN = "unknown"
    EXTRACTED = "extracted"
    AUTHORED = "authored"
    INFERRED = "inferred"
    IMPORTED = "imported"
    MARKDOWN = "markdown"
    GOVERNANCE = "governance"


class EvidenceState(str, Enum):
    UNKNOWN = "unknown"
    PRESENT = "present"
    MISSING = "missing"
    INVALID = "invalid"
    NOT_APPLICABLE = "not-applicable"


class Resolution(str, Enum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    EXTERNAL = "external"
    UNRESOLVED = "unresolved"


class TargetClass(str, Enum):
    """Classification of a relationship target, separate from resolution."""

    UNKNOWN = "unknown"
    CONCEPT = "concept"
    SOURCE = "source"
    EXTERNAL = "external"
    MAIL = "mail"
    ANCHOR = "anchor"
    ASSET = "asset"
    MALFORMED = "malformed"


class Verification(str, Enum):
    UNTRACKED = "untracked"
    UNVERIFIED = "unverified"
    MACHINE_CHECKED = "machine-checked"
    HUMAN_REVIEWED = "human-reviewed"
    FAILED = "failed"
    EXPIRED = "expired"


class Lifecycle(str, Enum):
    UNKNOWN = "unknown"
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class ComputedFreshness(str, Enum):
    """Live comparison outcomes; never serialized in the knowledge index."""

    UNKNOWN = "unknown"
    CURRENT = "current"
    NONSEMANTIC_SOURCE_CHANGE = "nonsemantic-source-change"
    SOURCE_CHANGED = "source-changed"
    BASIS_INCOMPATIBLE = "basis-incompatible"
    SOURCE_MISSING = "source-missing"


class KnowledgeLoadState(str, Enum):
    """Validated artifact-load outcomes; never persisted in the knowledge index."""

    VALID = "valid"
    ABSENT = "absent"
    INVALID = "invalid"
    MIXED_SNAPSHOT = "mixed-snapshot"
    DEGRADED = "degraded"


class KnowledgeProjectionProfile(str, Enum):
    """Out-of-band projection policies; never selected by artifact metadata."""

    INTERNAL = "internal"
    PUBLIC_PORTABLE = "public-portable"


class ActorKind(str, Enum):
    UNKNOWN = "unknown"
    TOOL = "tool"
    AGENT = "agent"
    HUMAN = "human"
    PROCESS = "process"


class WorkingTreeState(str, Enum):
    UNKNOWN = "unknown"
    CLEAN = "clean"
    DIRTY = "dirty"


class RepositoryIdentitySource(str, Enum):
    """How a repository identity was selected by an application-owned writer."""

    CONFIGURED_PUBLIC = "configured-public"
    NORMALIZED_VCS = "normalized-vcs"
    UNKNOWN = "unknown"


class ObservationScope(str, Enum):
    UNKNOWN = "unknown"
    MODULE = "module"
    ENTITY = "entity"
    INFRASTRUCTURE = "infrastructure"
    AGGREGATE = "aggregate"


class RelationshipKind(str, Enum):
    DERIVED_FROM = "derived_from"
    LINKS_TO = "links_to"


ConceptKindValue = Union[ConceptKind, str]
RelationshipKindValue = Union[RelationshipKind, str]
Extensions = Mapping[str, Any]


PAGE_KIND_TO_CONCEPT_KIND: Mapping[PageKind, ConceptKind] = MappingProxyType(
    {
        PageKind.INDEX: ConceptKind.NAVIGATION_DOCUMENT,
        PageKind.LOG: ConceptKind.CHANGE_LOG_DOCUMENT,
        PageKind.ENTITIES: ConceptKind.CODE_ENTITY,
        PageKind.MODULES: ConceptKind.SOURCE_MODULE,
        PageKind.WORKFLOWS: ConceptKind.WORKFLOW,
        PageKind.GUIDES: ConceptKind.GUIDE,
        PageKind.FLOWS: ConceptKind.USER_FLOW,
        PageKind.INFRASTRUCTURE: ConceptKind.INFRASTRUCTURE_RESOURCE,
        PageKind.API_CONTRACTS: ConceptKind.API_CONTRACT,
        PageKind.DEPENDENCIES: ConceptKind.DEPENDENCY_VIEW,
        PageKind.LOAD_ORDER: ConceptKind.DEPENDENCY_VIEW,
    }
)
_SURFACE_KIND_BY_PAGE_KIND = MappingProxyType(
    {entry.kind: entry for entry in iter_page_kinds()}
)


@dataclass(frozen=True)
class Actor:
    kind: ActorKind = ActorKind.UNKNOWN
    actor_id: Optional[str] = None
    version: Optional[str] = None
    model: Optional[str] = None
    organization: Optional[str] = None
    extensions: Extensions = field(default_factory=dict)

    @property
    def id(self) -> Optional[str]:
        """Return the wire-format actor identifier."""

        return self.actor_id


@dataclass(frozen=True)
class RepositoryRecord:
    identity: str
    evaluated_revision: str = "unknown"
    working_tree: WorkingTreeState = WorkingTreeState.UNKNOWN
    extensions: Extensions = field(default_factory=dict)

    @property
    def identity_source(self) -> RepositoryIdentitySource:
        """Return the redaction-relevant source of the selected identity."""

        value = self.extensions.get(
            REPOSITORY_IDENTITY_SOURCE_EXTENSION,
            RepositoryIdentitySource.UNKNOWN.value,
        )
        return RepositoryIdentitySource(value)


@dataclass(frozen=True)
class SnapshotRecord:
    source_snapshot_hash: str
    markdown_snapshot_hash: str
    surface_index_hash: str
    generation_options_hash: str
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class ProducerComponent:
    component_id: str
    version: str
    configuration_hash: Optional[str] = None
    limitations: tuple[str, ...] = ()
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class ProducerRecord:
    tool: ProducerComponent
    extractors: tuple[ProducerComponent, ...] = ()
    plugins: tuple[ProducerComponent, ...] = ()
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class BundleRecord:
    repository: RepositoryRecord
    snapshot: SnapshotRecord
    producer: ProducerRecord
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentRecord:
    page_kind: PageKind
    page_id: str
    canonical_path: str
    role: SurfaceRole
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceBasis:
    scope: ObservationScope
    source_path: Optional[str] = None
    extractor_ref: Optional[str] = None
    source_content_hash: Optional[str] = None
    concept_observation_hash: Optional[str] = None
    aggregate_input_hash: Optional[str] = None
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class StructuralFacet:
    origin: Origin = Origin.UNKNOWN
    evidence: EvidenceState = EvidenceState.UNKNOWN
    basis: Optional[EvidenceBasis] = None
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class SemanticFacet:
    ownership: SurfaceRole
    page_hash: str
    authorship: Actor = field(default_factory=Actor)
    verification: Verification = Verification.UNTRACKED
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class ConceptFacets:
    structure: StructuralFacet
    semantics: SemanticFacet
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class ConceptRecord:
    locator: str
    concept_kind: ConceptKindValue
    title: str
    document: DocumentRecord
    facets: ConceptFacets
    lifecycle: Lifecycle = Lifecycle.UNKNOWN
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class RelationshipLocation:
    """Half-open character offsets for a relationship observation."""

    start: int
    end: int
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class RelationshipTarget:
    target_class: TargetClass = TargetClass.UNKNOWN
    locator: Optional[str] = None
    canonical_path: Optional[str] = None
    source_path: Optional[str] = None
    external_uri: Optional[str] = None
    raw_target: Optional[str] = None
    normalized_target: Optional[str] = None
    label: Optional[str] = None
    location: Optional[RelationshipLocation] = None
    extensions: Extensions = field(default_factory=dict)

    @property
    def endpoint_kind(self) -> str:
        for name in (
            "locator",
            "canonical_path",
            "source_path",
            "external_uri",
        ):
            if getattr(self, name) is not None:
                return name
        return "none"

    @property
    def kind(self) -> str:
        """Compatibility view of the endpoint or unresolved raw observation."""

        if self.endpoint_kind != "none":
            return self.endpoint_kind
        return "raw_target" if self.raw_target is not None else "unknown"

    @property
    def value(self) -> Optional[str]:
        return getattr(self, self.kind, None)


@dataclass(frozen=True)
class RelationshipEvidence:
    state: EvidenceState = EvidenceState.UNKNOWN
    source_content_hash: Optional[str] = None
    concept_observation_hash: Optional[str] = None
    page_hash: Optional[str] = None
    aggregate_input_hash: Optional[str] = None
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class RelationshipRecord:
    kind: RelationshipKindValue
    source_locator: str
    target: RelationshipTarget
    origin: Origin
    evidence: RelationshipEvidence
    resolution: Resolution
    extensions: Extensions = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeIndex:
    schema_version: str
    bundle: BundleRecord
    concepts: tuple[ConceptRecord, ...]
    relationships: tuple[RelationshipRecord, ...]
    extensions: Extensions = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: object) -> "KnowledgeIndex":
        return parse_knowledge_index(payload)

    def to_payload(self) -> dict[str, Any]:
        return knowledge_index_to_payload(self)

    def to_json(self) -> str:
        return serialize_knowledge_index(self)


# Compatibility-oriented names make the status semantics obvious at call sites
# without creating duplicate enum classes.
KnowledgeOrigin = Origin
RelationshipResolution = Resolution
RelationshipTargetClass = TargetClass
LinkTargetClass = TargetClass
VerificationState = Verification
LifecycleState = Lifecycle


_EnumT = TypeVar("_EnumT", bound=Enum)


def concept_kind_for_page_kind(value: Union[PageKind, str]) -> ConceptKind:
    """Map a presentation page kind to the v1 domain/document taxonomy."""

    try:
        page_kind = value if isinstance(value, PageKind) else PageKind(value)
    except (TypeError, ValueError) as exc:
        raise KnowledgeModelError(
            "page_kind", f"unsupported page kind {value!r}"
        ) from exc
    return PAGE_KIND_TO_CONCEPT_KIND[page_kind]


def repository_identities_match(
    left: RepositoryRecord,
    right: RepositoryRecord,
) -> bool:
    """Return whether two explicit, non-unknown repository identities match.

    Snapshot equality is intentionally irrelevant here. ``unknown`` is a
    non-identity sentinel, so it never matches another ``unknown`` value.
    """

    if not isinstance(left, RepositoryRecord) or not isinstance(
        right, RepositoryRecord
    ):
        raise TypeError("left and right must be RepositoryRecord values")
    left_identity = _repository_identity(left.identity, "left.identity")
    right_identity = _repository_identity(right.identity, "right.identity")
    try:
        left_source = left.identity_source
        right_source = right.identity_source
    except (AttributeError, TypeError, ValueError):
        return False
    return (
        left_identity != "unknown"
        and right_identity != "unknown"
        and left_source is not RepositoryIdentitySource.UNKNOWN
        and right_source is not RepositoryIdentitySource.UNKNOWN
        and left_identity == right_identity
    )


def parse_knowledge_index(payload: object) -> KnowledgeIndex:
    """Validate and deserialize one v1 payload without performing I/O."""

    data, extensions = _record(
        payload,
        "",
        {"schema_version", "bundle", "concepts", "relationships"},
        required={"schema_version", "bundle", "concepts", "relationships"},
    )
    schema_version = _string(data["schema_version"], "schema_version")
    if schema_version != KNOWLEDGE_SCHEMA_VERSION:
        raise KnowledgeModelError(
            "schema_version", f"must be {KNOWLEDGE_SCHEMA_VERSION!r}"
        )

    bundle = _parse_bundle(data["bundle"], "bundle")
    concepts_value = _array(data["concepts"], "concepts")
    concepts = tuple(
        _parse_concept(item, f"concepts[{index}]")
        for index, item in enumerate(concepts_value)
    )
    relationships_value = _array(data["relationships"], "relationships")
    relationships = tuple(
        _parse_relationship(item, f"relationships[{index}]")
        for index, item in enumerate(relationships_value)
    )

    extensions = _validated_reserved_extensions(extensions, concepts)
    _validate_index_references(bundle, concepts, relationships)
    model = KnowledgeIndex(
        schema_version=schema_version,
        bundle=bundle,
        concepts=concepts,
        relationships=relationships,
        extensions=extensions,
    )
    # Governance is an independently versioned projection whose authority is
    # the separate ledger.  Validate its core lifecycle/UID/alias/event parity
    # only after the enclosing model and the other reserved extensions exist.
    from .knowledge_governance import validate_governance_projection

    try:
        validate_governance_projection(model)
    except ValueError as exc:
        field = getattr(exc, "field", "extensions")
        message = getattr(exc, "message", str(exc))
        raise KnowledgeModelError(str(field), str(message)) from exc
    return model


def _validated_reserved_extensions(
    extensions: Mapping[str, Any],
    concepts: tuple[ConceptRecord, ...],
) -> dict[str, Any]:
    """Validate application-owned, independently versioned v1 extensions."""

    # Local imports avoid making the independent extension contracts depend on
    # the legacy relationship dataclasses in this module.
    from .contracts import (
        SECTION_OWNERSHIP_EXTENSION_KEY,
        TYPED_GRAPH_EXTENSION_KEY,
    )
    from .knowledge_graph import (
        KnowledgeGraphError,
        typed_graph_from_knowledge_extensions,
    )
    from .section_ownership import (
        SectionOwnershipError,
        validate_section_ownership,
    )

    normalized = dict(extensions)
    try:
        typed_graph = typed_graph_from_knowledge_extensions(
            normalized,
        )
    except KnowledgeGraphError as exc:
        field = exc.field
        if field.startswith("typed_graph"):
            field = (
                f"extensions.{TYPED_GRAPH_EXTENSION_KEY}"
                + field[len("typed_graph") :]
            )
        raise KnowledgeModelError(field, exc.message) from exc
    if typed_graph is not None:
        normalized[TYPED_GRAPH_EXTENSION_KEY] = typed_graph
    section_value = normalized.get(SECTION_OWNERSHIP_EXTENSION_KEY)
    if section_value is not None:
        try:
            section_ownership = validate_section_ownership(
                section_value,
            )
        except SectionOwnershipError as exc:
            field = exc.field
            if field.startswith("section_ownership"):
                field = (
                    f"extensions.{SECTION_OWNERSHIP_EXTENSION_KEY}"
                    + field[len("section_ownership") :]
                )
            raise KnowledgeModelError(field, exc.message) from exc
        normalized[SECTION_OWNERSHIP_EXTENSION_KEY] = section_ownership
    return normalized


def validate_knowledge_payload(payload: object) -> KnowledgeIndex:
    """Alias for :func:`parse_knowledge_index` used by future builders/loaders."""

    return parse_knowledge_index(payload)


def knowledge_index_to_payload(model: KnowledgeIndex) -> dict[str, Any]:
    """Return the normalized JSON-compatible representation of ``model``."""

    if not isinstance(model, KnowledgeIndex):
        raise TypeError("model must be a KnowledgeIndex")

    try:
        payload = _emit_extensions(
            {
                "schema_version": model.schema_version,
                "bundle": _bundle_to_payload(model.bundle),
                "concepts": [
                    _concept_to_payload(concept) for concept in model.concepts
                ],
                "relationships": [
                    _relationship_to_payload(relationship)
                    for relationship in model.relationships
                ],
            },
            model.extensions,
            "extensions",
        )
    except KnowledgeModelError:
        raise
    except (AttributeError, TypeError) as exc:
        raise KnowledgeModelError(
            "model", "must contain the declared knowledge model dataclass shapes"
        ) from exc
    # Validate manually constructed dataclasses too, while returning the
    # normalized copy produced by the validated model.
    validated = parse_knowledge_index(payload)
    return _knowledge_index_to_payload_unchecked(validated)


def serialize_knowledge_index(model: KnowledgeIndex) -> str:
    """Serialize deterministically with exactly one trailing newline."""

    try:
        return (
            json.dumps(
                knowledge_index_to_payload(model),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        )
    except (RecursionError, TypeError, ValueError) as exc:
        raise KnowledgeModelError(
            "model", "cannot be serialized as finite JSON"
        ) from exc


def load_knowledge_schema() -> dict[str, Any]:
    """Load the packaged JSON Schema through a zip-safe resource handle."""

    try:
        resource = resources.files("llm_wiki_cli.schemas").joinpath(
            KNOWLEDGE_SCHEMA_FILENAME
        )
        payload = json.loads(resource.read_text(encoding="utf-8"))
    except (
        ModuleNotFoundError,
        OSError,
        TypeError,
        UnicodeError,
        json.JSONDecodeError,
    ) as exc:
        raise KnowledgeModelError(
            "schema", f"packaged schema {KNOWLEDGE_SCHEMA_FILENAME!r} is unavailable"
        ) from exc
    if not isinstance(payload, dict):
        raise KnowledgeModelError("schema", "packaged schema must be a JSON object")
    return payload


def _parse_bundle(value: object, path: str) -> BundleRecord:
    data, extensions = _record(
        value,
        path,
        {"repository", "snapshot", "producer"},
        required={"repository", "snapshot", "producer"},
    )
    return BundleRecord(
        repository=_parse_repository(data["repository"], _child(path, "repository")),
        snapshot=_parse_snapshot(data["snapshot"], _child(path, "snapshot")),
        producer=_parse_producer(data["producer"], _child(path, "producer")),
        extensions=extensions,
    )


def _parse_repository(value: object, path: str) -> RepositoryRecord:
    data, extensions = _record(
        value,
        path,
        {"identity", "evaluated_revision", "working_tree"},
        required={"identity"},
    )
    identity = _repository_identity(data["identity"], _child(path, "identity"))
    revision = _evaluated_revision(
        data.get("evaluated_revision", "unknown"),
        _child(path, "evaluated_revision"),
    )
    working_tree = _enum_value(
        data.get("working_tree", WorkingTreeState.UNKNOWN.value),
        WorkingTreeState,
        _child(path, "working_tree"),
    )
    identity_source_path = _child(
        path,
        f"extensions.{REPOSITORY_IDENTITY_SOURCE_EXTENSION}",
    )
    identity_source_value = extensions.get(
        REPOSITORY_IDENTITY_SOURCE_EXTENSION,
        _MISSING,
    )
    if identity_source_value is _MISSING:
        if identity != "unknown":
            raise KnowledgeModelError(
                identity_source_path,
                "is required for a non-unknown repository identity",
            )
        identity_source = RepositoryIdentitySource.UNKNOWN
    else:
        identity_source = _enum_value(
            identity_source_value,
            RepositoryIdentitySource,
            identity_source_path,
        )
    if (identity == "unknown") != (identity_source is RepositoryIdentitySource.UNKNOWN):
        raise KnowledgeModelError(
            identity_source_path,
            "must be 'unknown' exactly when repository identity is 'unknown'",
        )
    if identity_source is RepositoryIdentitySource.UNKNOWN:
        extensions.pop(REPOSITORY_IDENTITY_SOURCE_EXTENSION, None)
    return RepositoryRecord(
        identity=identity,
        evaluated_revision=revision,
        working_tree=working_tree,
        extensions=extensions,
    )


def _parse_snapshot(value: object, path: str) -> SnapshotRecord:
    fields = {
        "source_snapshot_hash",
        "markdown_snapshot_hash",
        "surface_index_hash",
        "generation_options_hash",
    }
    data, extensions = _record(value, path, fields, required=fields)
    return SnapshotRecord(
        source_snapshot_hash=_hash(
            data["source_snapshot_hash"], _child(path, "source_snapshot_hash")
        ),
        markdown_snapshot_hash=_hash(
            data["markdown_snapshot_hash"],
            _child(path, "markdown_snapshot_hash"),
        ),
        surface_index_hash=_hash(
            data["surface_index_hash"], _child(path, "surface_index_hash")
        ),
        generation_options_hash=_hash(
            data["generation_options_hash"],
            _child(path, "generation_options_hash"),
        ),
        extensions=extensions,
    )


def _parse_producer(value: object, path: str) -> ProducerRecord:
    data, extensions = _record(
        value,
        path,
        {"tool", "extractors", "plugins"},
        required={"tool"},
    )
    extractors = _component_array(
        data.get("extractors", []), _child(path, "extractors")
    )
    plugins = _component_array(data.get("plugins", []), _child(path, "plugins"))
    tool = _parse_component(data["tool"], _child(path, "tool"))
    _reject_duplicate_components((tool,), extractors, plugins, path)
    return ProducerRecord(
        tool=tool,
        extractors=extractors,
        plugins=plugins,
        extensions=extensions,
    )


def _component_array(value: object, path: str) -> tuple[ProducerComponent, ...]:
    items = _array(value, path)
    components = tuple(
        _parse_component(item, f"{path}[{index}]") for index, item in enumerate(items)
    )
    for index, component in enumerate(components):
        _validate_analyzer_component(component, f"{path}[{index}]")
    return components


def _parse_component(value: object, path: str) -> ProducerComponent:
    data, extensions = _record(
        value,
        path,
        {"id", "version", "configuration_hash", "limitations"},
        required={"id", "version"},
    )
    component_id = _nonempty_string(data["id"], _child(path, "id"))
    if not _COMPONENT_ID_RE.fullmatch(component_id):
        raise KnowledgeModelError(
            _child(path, "id"),
            "must contain only letters, digits, '.', '_', '/', or '-'",
        )
    configuration_hash = _optional_hash(
        data.get("configuration_hash", _MISSING),
        _child(path, "configuration_hash"),
    )
    limitations_value = _array(data.get("limitations", []), _child(path, "limitations"))
    limitations = tuple(
        _nonempty_string(item, f"{path}.limitations[{index}]")
        for index, item in enumerate(limitations_value)
    )
    invalid_limitation = next(
        (
            (index, limitation)
            for index, limitation in enumerate(limitations)
            if not _LIMITATION_CODE_RE.fullmatch(limitation)
        ),
        None,
    )
    if invalid_limitation is not None:
        index, _ = invalid_limitation
        raise KnowledgeModelError(
            f"{path}.limitations[{index}]",
            "must be a lowercase stable machine code",
        )
    if len(set(limitations)) != len(limitations):
        raise KnowledgeModelError(
            _child(path, "limitations"),
            "must not contain duplicate codes",
        )
    if limitations != tuple(sorted(limitations)):
        raise KnowledgeModelError(
            _child(path, "limitations"),
            "must be sorted in ascending code order",
        )
    return ProducerComponent(
        component_id=component_id,
        version=_nonempty_string(data["version"], _child(path, "version")),
        configuration_hash=configuration_hash,
        limitations=limitations,
        extensions=extensions,
    )


def _validate_analyzer_component(
    component: ProducerComponent,
    path: str,
) -> None:
    unknown_basis = "configuration-basis-unknown" in component.limitations
    if component.configuration_hash is None and not unknown_basis:
        raise KnowledgeModelError(
            _child(path, "configuration_hash"),
            "is required unless limitations contains 'configuration-basis-unknown'",
        )
    if component.configuration_hash is not None and unknown_basis:
        raise KnowledgeModelError(
            _child(path, "limitations"),
            "must omit 'configuration-basis-unknown' when configuration_hash "
            "is present",
        )


def _parse_concept(value: object, path: str) -> ConceptRecord:
    data, extensions = _record(
        value,
        path,
        {"locator", "concept_kind", "title", "document", "facets", "lifecycle"},
        required={"locator", "concept_kind", "title", "document", "facets"},
    )
    document = _parse_document(data["document"], _child(path, "document"))
    locator = _locator(data["locator"], _child(path, "locator"))
    surface_kind = _SURFACE_KIND_BY_PAGE_KIND[document.page_kind]
    expected_locator = wiki_surface.mcp_uri(
        document.page_kind,
        document.page_id if surface_kind.requires_page_id else None,
    )
    if locator != expected_locator:
        raise KnowledgeModelError(
            _child(path, "locator"),
            f"must match the canonical surface locator {expected_locator!r}",
        )
    concept_kind = _open_enum_value(
        data["concept_kind"], ConceptKind, _child(path, "concept_kind")
    )
    if isinstance(concept_kind, ConceptKind):
        expected = concept_kind_for_page_kind(document.page_kind)
        if concept_kind is not expected:
            raise KnowledgeModelError(
                _child(path, "concept_kind"),
                f"{concept_kind.value!r} does not match page_kind "
                f"{document.page_kind.value!r}; expected {expected.value!r}",
            )

    facets = _parse_facets(data["facets"], _child(path, "facets"))
    if facets.semantics.ownership is not document.role:
        raise KnowledgeModelError(
            _child(path, "facets.semantics.ownership"),
            f"must match document.role {document.role.value!r}",
        )
    if (
        isinstance(concept_kind, ConceptKind)
        and concept_kind.is_document_only
        and (
            facets.structure.origin is not Origin.UNKNOWN
            or facets.structure.evidence
            not in {EvidenceState.UNKNOWN, EvidenceState.NOT_APPLICABLE}
            or facets.structure.basis is not None
        )
    ):
        raise KnowledgeModelError(
            _child(path, "facets.structure"),
            "document-only concepts must use unknown origin, "
            "unknown/not-applicable evidence, and no structural basis",
        )

    return ConceptRecord(
        locator=locator,
        concept_kind=concept_kind,
        title=_nonempty_string(data["title"], _child(path, "title")),
        document=document,
        facets=facets,
        lifecycle=_enum_value(
            data.get("lifecycle", Lifecycle.UNKNOWN.value),
            Lifecycle,
            _child(path, "lifecycle"),
        ),
        extensions=extensions,
    )


def _parse_document(value: object, path: str) -> DocumentRecord:
    fields = {"page_kind", "page_id", "canonical_path", "role"}
    data, extensions = _record(value, path, fields, required=fields)
    page_kind = _enum_value(data["page_kind"], PageKind, _child(path, "page_kind"))
    page_id = _nonempty_string(data["page_id"], _child(path, "page_id"))
    if not is_safe_page_id(page_id):
        raise KnowledgeModelError(
            _child(path, "page_id"), "must be a safe canonical page identifier"
        )
    surface_kind = _SURFACE_KIND_BY_PAGE_KIND[page_kind]
    if not surface_kind.requires_page_id and page_id != page_kind.value:
        raise KnowledgeModelError(
            _child(path, "page_id"),
            f"must be {page_kind.value!r} for the root surface",
        )
    canonical_path = _relative_path(
        data["canonical_path"], _child(path, "canonical_path")
    )
    if not canonical_path.endswith(".md"):
        raise KnowledgeModelError(
            _child(path, "canonical_path"), "must identify a Markdown file"
        )
    expected_path = wiki_surface.canonical_path(
        page_kind, page_id if surface_kind.requires_page_id else None
    )
    if canonical_path != expected_path:
        raise KnowledgeModelError(
            _child(path, "canonical_path"),
            f"must match the canonical surface path {expected_path!r}",
        )
    role = _enum_value(data["role"], SurfaceRole, _child(path, "role"))
    if role is not surface_kind.role:
        raise KnowledgeModelError(
            _child(path, "role"),
            f"must match the canonical surface role {surface_kind.role.value!r}",
        )
    return DocumentRecord(
        page_kind=page_kind,
        page_id=page_id,
        canonical_path=canonical_path,
        role=role,
        extensions=extensions,
    )


def _parse_facets(value: object, path: str) -> ConceptFacets:
    data, extensions = _record(
        value,
        path,
        {"structure", "semantics"},
        required={"structure", "semantics"},
    )
    return ConceptFacets(
        structure=_parse_structural_facet(data["structure"], _child(path, "structure")),
        semantics=_parse_semantic_facet(data["semantics"], _child(path, "semantics")),
        extensions=extensions,
    )


def _parse_structural_facet(value: object, path: str) -> StructuralFacet:
    data, extensions = _record(value, path, {"origin", "evidence", "basis"})
    evidence = _enum_value(
        data.get("evidence", EvidenceState.UNKNOWN.value),
        EvidenceState,
        _child(path, "evidence"),
    )
    basis = (
        _parse_evidence_basis(data["basis"], _child(path, "basis"))
        if "basis" in data
        else None
    )
    if evidence is EvidenceState.PRESENT and basis is None:
        raise KnowledgeModelError(
            _child(path, "basis"), "is required when evidence is 'present'"
        )
    return StructuralFacet(
        origin=_enum_value(
            data.get("origin", Origin.UNKNOWN.value),
            Origin,
            _child(path, "origin"),
        ),
        evidence=evidence,
        basis=basis,
        extensions=extensions,
    )


def _parse_evidence_basis(value: object, path: str) -> EvidenceBasis:
    data, extensions = _record(
        value,
        path,
        {
            "scope",
            "source_path",
            "extractor_ref",
            "source_content_hash",
            "concept_observation_hash",
            "aggregate_input_hash",
        },
        required={"scope"},
    )
    return EvidenceBasis(
        scope=_enum_value(data["scope"], ObservationScope, _child(path, "scope")),
        source_path=_optional_relative_path(
            data.get("source_path", _MISSING), _child(path, "source_path")
        ),
        extractor_ref=_optional_nonempty_string(
            data.get("extractor_ref", _MISSING), _child(path, "extractor_ref")
        ),
        source_content_hash=_optional_hash(
            data.get("source_content_hash", _MISSING),
            _child(path, "source_content_hash"),
        ),
        concept_observation_hash=_optional_hash(
            data.get("concept_observation_hash", _MISSING),
            _child(path, "concept_observation_hash"),
        ),
        aggregate_input_hash=_optional_hash(
            data.get("aggregate_input_hash", _MISSING),
            _child(path, "aggregate_input_hash"),
        ),
        extensions=extensions,
    )


def _parse_semantic_facet(value: object, path: str) -> SemanticFacet:
    data, extensions = _record(
        value,
        path,
        {"ownership", "page_hash", "authorship", "verification"},
        required={"ownership", "page_hash"},
    )
    return SemanticFacet(
        ownership=_enum_value(
            data["ownership"], SurfaceRole, _child(path, "ownership")
        ),
        page_hash=_hash(data["page_hash"], _child(path, "page_hash")),
        authorship=(
            _parse_actor(data["authorship"], _child(path, "authorship"))
            if "authorship" in data
            else Actor()
        ),
        verification=_enum_value(
            data.get("verification", Verification.UNTRACKED.value),
            Verification,
            _child(path, "verification"),
        ),
        extensions=extensions,
    )


def _parse_actor(value: object, path: str) -> Actor:
    data, extensions = _record(
        value,
        path,
        {"kind", "id", "version", "model", "organization"},
        required={"kind"},
    )
    kind = _enum_value(data["kind"], ActorKind, _child(path, "kind"))
    actor_id = _optional_nonempty_string(data.get("id", _MISSING), _child(path, "id"))
    if kind is not ActorKind.UNKNOWN and actor_id is None:
        raise KnowledgeModelError(
            _child(path, "id"), f"is required for actor kind {kind.value!r}"
        )
    if kind is ActorKind.UNKNOWN and any(
        data.get(name) is not None
        for name in ("id", "version", "model", "organization")
    ):
        raise KnowledgeModelError(
            path, "unknown actor must not claim identity or producer metadata"
        )
    return Actor(
        kind=kind,
        actor_id=actor_id,
        version=_optional_nonempty_string(
            data.get("version", _MISSING), _child(path, "version")
        ),
        model=_optional_nonempty_string(
            data.get("model", _MISSING), _child(path, "model")
        ),
        organization=_optional_nonempty_string(
            data.get("organization", _MISSING), _child(path, "organization")
        ),
        extensions=extensions,
    )


def _parse_relationship(value: object, path: str) -> RelationshipRecord:
    fields = {"kind", "from", "target", "origin", "evidence", "resolution"}
    data, extensions = _record(value, path, fields, required=fields)
    relationship = RelationshipRecord(
        kind=_open_enum_value(data["kind"], RelationshipKind, _child(path, "kind")),
        source_locator=_locator(data["from"], _child(path, "from")),
        target=_parse_relationship_target(data["target"], _child(path, "target")),
        origin=_enum_value(data["origin"], Origin, _child(path, "origin")),
        evidence=_parse_relationship_evidence(
            data["evidence"], _child(path, "evidence")
        ),
        resolution=_enum_value(
            data["resolution"], Resolution, _child(path, "resolution")
        ),
        extensions=extensions,
    )
    _validate_relationship_shape(relationship, path)
    return relationship


def _parse_relationship_target(value: object, path: str) -> RelationshipTarget:
    coordinate_fields = {
        "locator",
        "canonical_path",
        "source_path",
        "external_uri",
    }
    observation_fields = {
        "raw_target",
        "normalized_target",
        "label",
        "location",
    }
    data, extensions = _record(
        value,
        path,
        coordinate_fields | observation_fields | {"target_class"},
    )
    present = [name for name in coordinate_fields if name in data]
    if len(present) > 1:
        raise KnowledgeModelError(
            path,
            "must contain at most one endpoint coordinate: locator, "
            "canonical_path, source_path, or external_uri",
        )
    if not present and "raw_target" not in data:
        raise KnowledgeModelError(
            path, "must contain an endpoint coordinate or raw_target observation"
        )
    observed = [name for name in observation_fields if name in data]
    if observed and len(observed) != len(observation_fields):
        missing = sorted(observation_fields - set(observed))[0]
        raise KnowledgeModelError(
            _child(path, missing),
            "is required when any link-observation field is present",
        )

    parsed: dict[str, Optional[str]] = {
        "locator": None,
        "canonical_path": None,
        "source_path": None,
        "external_uri": None,
    }
    if present:
        name = present[0]
        if name == "locator":
            parsed[name] = _locator(data[name], _child(path, name))
        elif name in {"canonical_path", "source_path"}:
            parsed[name] = _relative_path(data[name], _child(path, name))
        else:
            parsed[name] = _external_uri(data[name], _child(path, name))

    return RelationshipTarget(
        target_class=_enum_value(
            data.get("target_class", TargetClass.UNKNOWN.value),
            TargetClass,
            _child(path, "target_class"),
        ),
        raw_target=(
            _link_observation_string(data["raw_target"], _child(path, "raw_target"))
            if "raw_target" in data
            else None
        ),
        normalized_target=(
            _link_observation_string(
                data["normalized_target"], _child(path, "normalized_target")
            )
            if "normalized_target" in data
            else None
        ),
        label=(
            _string(data["label"], _child(path, "label")) if "label" in data else None
        ),
        location=(
            _parse_relationship_location(data["location"], _child(path, "location"))
            if "location" in data
            else None
        ),
        extensions=extensions,
        **parsed,
    )


def _parse_relationship_location(value: object, path: str) -> RelationshipLocation:
    data, extensions = _record(
        value,
        path,
        {"start", "end"},
        required={"start", "end"},
    )
    start = _nonnegative_integer(data["start"], _child(path, "start"))
    end = _positive_integer(data["end"], _child(path, "end"))
    if end <= start:
        raise KnowledgeModelError(
            _child(path, "end"), "must be greater than location.start"
        )
    return RelationshipLocation(start=start, end=end, extensions=extensions)


def _parse_relationship_evidence(value: object, path: str) -> RelationshipEvidence:
    data, extensions = _record(
        value,
        path,
        {
            "state",
            "source_content_hash",
            "concept_observation_hash",
            "page_hash",
            "aggregate_input_hash",
        },
    )
    evidence = RelationshipEvidence(
        state=_enum_value(
            data.get("state", EvidenceState.UNKNOWN.value),
            EvidenceState,
            _child(path, "state"),
        ),
        source_content_hash=_optional_hash(
            data.get("source_content_hash", _MISSING),
            _child(path, "source_content_hash"),
        ),
        concept_observation_hash=_optional_hash(
            data.get("concept_observation_hash", _MISSING),
            _child(path, "concept_observation_hash"),
        ),
        page_hash=_optional_hash(
            data.get("page_hash", _MISSING), _child(path, "page_hash")
        ),
        aggregate_input_hash=_optional_hash(
            data.get("aggregate_input_hash", _MISSING),
            _child(path, "aggregate_input_hash"),
        ),
        extensions=extensions,
    )
    if evidence.state is EvidenceState.PRESENT and not any(
        (
            evidence.source_content_hash,
            evidence.concept_observation_hash,
            evidence.page_hash,
            evidence.aggregate_input_hash,
        )
    ):
        raise KnowledgeModelError(
            path, "present relationship evidence requires at least one hash"
        )
    return evidence


def _validate_relationship_shape(relationship: RelationshipRecord, path: str) -> None:
    target_kind = relationship.target.endpoint_kind
    target_class = relationship.target.target_class

    allowed_by_class = {
        TargetClass.CONCEPT: {"locator", "canonical_path", "none"},
        TargetClass.SOURCE: {"source_path"},
        TargetClass.EXTERNAL: {"external_uri"},
        TargetClass.MAIL: {"external_uri"},
        TargetClass.ANCHOR: {"none"},
        TargetClass.ASSET: {"none"},
        TargetClass.MALFORMED: {"none"},
    }
    if (
        target_class is not TargetClass.UNKNOWN
        and target_kind not in allowed_by_class[target_class]
    ):
        raise KnowledgeModelError(
            _child(path, "target.target_class"),
            f"target class {target_class.value!r} is incompatible with {target_kind!r}",
        )
    if target_class is TargetClass.MAIL and not (
        relationship.target.external_uri or ""
    ).casefold().startswith("mailto:"):
        raise KnowledgeModelError(
            _child(path, "target.external_uri"),
            "mail targets require a mailto: URI",
        )
    if target_class is TargetClass.EXTERNAL and (
        relationship.target.external_uri or ""
    ).casefold().startswith("mailto:"):
        raise KnowledgeModelError(
            _child(path, "target.target_class"),
            "mailto: URIs require target class 'mail'",
        )

    if relationship.resolution is Resolution.RESOLVED:
        resolved_target_kinds = {"locator", "canonical_path", "source_path"}
        if target_class in {TargetClass.ANCHOR, TargetClass.ASSET}:
            resolved_target_kinds.add("none")
        if target_kind not in resolved_target_kinds:
            raise KnowledgeModelError(
                _child(path, "target"),
                "resolved relationships require a locator, canonical_path, "
                "source_path, or a classified anchor/asset observation",
            )
    elif (
        relationship.resolution is Resolution.EXTERNAL and target_kind != "external_uri"
    ):
        raise KnowledgeModelError(
            _child(path, "target"),
            "external relationships require an external_uri target",
        )
    elif (
        relationship.resolution in {Resolution.AMBIGUOUS, Resolution.UNRESOLVED}
        and target_kind != "none"
    ):
        raise KnowledgeModelError(
            _child(path, "target"),
            f"{relationship.resolution.value} relationships must not claim "
            "a resolved endpoint",
        )

    if relationship.kind is RelationshipKind.DERIVED_FROM:
        if (
            target_kind != "source_path"
            or relationship.resolution is not Resolution.RESOLVED
        ):
            raise KnowledgeModelError(
                _child(path, "target"),
                "derived_from requires a resolved source_path target",
            )
        if target_class not in {TargetClass.UNKNOWN, TargetClass.SOURCE}:
            raise KnowledgeModelError(
                _child(path, "target.target_class"),
                "derived_from target class must be 'source' or 'unknown'",
            )
        if relationship.origin not in {Origin.EXTRACTED, Origin.INFERRED}:
            raise KnowledgeModelError(
                _child(path, "origin"),
                "derived_from origin must be 'extracted' or 'inferred'",
            )
        if (
            relationship.evidence.state is EvidenceState.PRESENT
            and relationship.evidence.concept_observation_hash is None
        ):
            raise KnowledgeModelError(
                _child(path, "evidence.concept_observation_hash"),
                "is required for present derived_from evidence",
            )
    elif relationship.kind is RelationshipKind.LINKS_TO:
        if relationship.origin is not Origin.MARKDOWN:
            raise KnowledgeModelError(
                _child(path, "origin"), "links_to origin must be 'markdown'"
            )
        if relationship.target.raw_target is None:
            raise KnowledgeModelError(
                _child(path, "target.raw_target"),
                "is required for links_to observations",
            )
        allowed_target_kinds = {
            Resolution.RESOLVED: {"locator", "canonical_path"},
            Resolution.EXTERNAL: {"external_uri"},
            Resolution.AMBIGUOUS: {"none"},
            Resolution.UNRESOLVED: {"none"},
        }[relationship.resolution]
        if relationship.resolution is Resolution.RESOLVED and target_class in {
            TargetClass.ANCHOR,
            TargetClass.ASSET,
        }:
            allowed_target_kinds.add("none")
        if target_kind not in allowed_target_kinds:
            raise KnowledgeModelError(
                _child(path, "target"),
                f"links_to target does not match resolution "
                f"{relationship.resolution.value!r}",
            )
        if (
            relationship.evidence.state is EvidenceState.PRESENT
            and relationship.evidence.page_hash is None
        ):
            raise KnowledgeModelError(
                _child(path, "evidence.page_hash"),
                "is required for present links_to evidence",
            )


def _validate_index_references(
    bundle: BundleRecord,
    concepts: tuple[ConceptRecord, ...],
    relationships: tuple[RelationshipRecord, ...],
) -> None:
    locators: dict[str, int] = {}
    canonical_paths: dict[str, int] = {}
    for index, concept in enumerate(concepts):
        if concept.locator in locators:
            raise KnowledgeModelError(
                f"concepts[{index}].locator",
                f"duplicates concepts[{locators[concept.locator]}].locator",
            )
        locators[concept.locator] = index
        path = concept.document.canonical_path
        if path in canonical_paths:
            raise KnowledgeModelError(
                f"concepts[{index}].document.canonical_path",
                f"duplicates concepts[{canonical_paths[path]}].document.canonical_path",
            )
        canonical_paths[path] = index

    producer_ids = {
        bundle.producer.tool.component_id,
        *(component.component_id for component in bundle.producer.extractors),
        *(component.component_id for component in bundle.producer.plugins),
    }
    for index, concept in enumerate(concepts):
        basis = concept.facets.structure.basis
        if basis is None:
            continue
        basis_path = f"concepts[{index}].facets.structure.basis"
        if concept.facets.structure.evidence is EvidenceState.PRESENT:
            if basis.scope is ObservationScope.UNKNOWN:
                raise KnowledgeModelError(
                    _child(basis_path, "scope"),
                    "must identify module, entity, infrastructure, or aggregate "
                    "evidence "
                    "when evidence is present",
                )
            if basis.scope in {
                ObservationScope.MODULE,
                ObservationScope.ENTITY,
                ObservationScope.INFRASTRUCTURE,
            }:
                required = {
                    "source_path": basis.source_path,
                    "extractor_ref": basis.extractor_ref,
                    "source_content_hash": basis.source_content_hash,
                    "concept_observation_hash": basis.concept_observation_hash,
                }
                missing = next(
                    (name for name, value in required.items() if value is None),
                    None,
                )
                if missing is not None:
                    raise KnowledgeModelError(
                        _child(basis_path, missing),
                        "is required for present source-backed evidence",
                    )
            if basis.scope is ObservationScope.AGGREGATE and (
                basis.aggregate_input_hash is None
            ):
                raise KnowledgeModelError(
                    _child(basis_path, "aggregate_input_hash"),
                    "is required for present aggregate evidence",
                )
        if basis.extractor_ref is not None and basis.extractor_ref not in producer_ids:
            raise KnowledgeModelError(
                _child(basis_path, "extractor_ref"),
                f"does not reference a declared producer component: "
                f"{basis.extractor_ref!r}",
            )

    for index, relationship in enumerate(relationships):
        path = f"relationships[{index}]"
        if relationship.source_locator not in locators:
            raise KnowledgeModelError(
                _child(path, "from"), "does not reference a concept locator"
            )
        if (
            relationship.resolution is Resolution.RESOLVED
            and relationship.target.locator is not None
            and relationship.target.locator not in locators
        ):
            raise KnowledgeModelError(
                _child(path, "target.locator"),
                "does not reference a concept locator",
            )
        if (
            relationship.resolution is Resolution.RESOLVED
            and relationship.target.canonical_path is not None
            and relationship.target.canonical_path not in canonical_paths
        ):
            raise KnowledgeModelError(
                _child(path, "target.canonical_path"),
                "does not reference a concept document",
            )


def _record(
    value: object,
    path: str,
    fields: AbstractSet[str],
    *,
    required: AbstractSet[str] = frozenset(),
) -> tuple[dict[str, Any], dict[str, Any]]:
    data = _object(value, path or "payload")
    allowed = fields | {"extensions"}
    unknown = sorted(set(data) - allowed)
    if unknown:
        key = unknown[0]
        raise KnowledgeModelError(
            _child(path, key),
            "unknown field; custom data must be placed in extensions",
        )
    missing = sorted(required - set(data))
    if missing:
        raise KnowledgeModelError(_child(path, missing[0]), "is required")
    extensions = _parse_extensions(
        data.get("extensions", {}), _child(path, "extensions")
    )
    return data, extensions


def _parse_extensions(value: object, path: str) -> dict[str, Any]:
    data = _object(value, path)
    result: dict[str, Any] = {}
    for key in sorted(data):
        if not _QUALIFIED_NAME_RE.fullmatch(key):
            raise KnowledgeModelError(
                _child(path, key),
                "extension key must use namespace/name syntax",
            )
        try:
            result[key] = _normalize_json_value(data[key], _child(path, key))
        except RecursionError as exc:
            raise KnowledgeModelError(
                _child(path, key), "extension nesting is too deep"
            ) from exc
    return result


def _normalize_json_value(value: object, path: str) -> Any:
    return _normalize_json_value_inner(value, path, set())


def _normalize_json_value_inner(
    value: object, path: str, active_containers: set[int]
) -> Any:
    if isinstance(value, str):
        return _string(value, path)
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise KnowledgeModelError(path, "extension number must be finite")
        return value
    if isinstance(value, list):
        identity = id(value)
        if identity in active_containers:
            raise KnowledgeModelError(path, "extension value must not be cyclic")
        active_containers.add(identity)
        try:
            return [
                _normalize_json_value_inner(item, f"{path}[{index}]", active_containers)
                for index, item in enumerate(value)
            ]
        finally:
            active_containers.remove(identity)
    if isinstance(value, Mapping):
        keys = list(value)
        for key in keys:
            if not isinstance(key, str):
                raise KnowledgeModelError(path, "extension object keys must be strings")
            _string(key, path)
        identity = id(value)
        if identity in active_containers:
            raise KnowledgeModelError(path, "extension value must not be cyclic")
        active_containers.add(identity)
        try:
            return {
                key: _normalize_json_value_inner(
                    value[key], _child(path, key), active_containers
                )
                for key in sorted(keys)
            }
        finally:
            active_containers.remove(identity)
    raise KnowledgeModelError(path, "extension value must be JSON-compatible")


def _object(value: object, path: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeModelError(path, "must be an object")
    result: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise KnowledgeModelError(path, "object keys must be strings")
        _string(key, path)
        result[key] = item
    return result


def _array(value: object, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise KnowledgeModelError(path, "must be an array")
    return value


def _string(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise KnowledgeModelError(path, "must be a string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise KnowledgeModelError(
            path,
            "must contain only Unicode scalar values encodable as UTF-8",
        ) from exc
    return value


def _nonempty_string(value: object, path: str) -> str:
    text = _string(value, path)
    if not text or text.strip() != text or any(ord(char) < 32 for char in text):
        raise KnowledgeModelError(
            path, "must be a non-empty string without surrounding/control whitespace"
        )
    return text


def _nonnegative_integer(value: object, path: str) -> int:
    if isinstance(value, bool):
        raise KnowledgeModelError(path, "must be a non-negative integer")
    if isinstance(value, int):
        integer = value
    elif isinstance(value, float) and math.isfinite(value) and value.is_integer():
        integer = int(value)
    else:
        raise KnowledgeModelError(path, "must be a non-negative integer")
    if integer < 0 or integer > _MAX_LOCATION_OFFSET:
        raise KnowledgeModelError(
            path,
            f"must be between 0 and {_MAX_LOCATION_OFFSET}",
        )
    return integer


def _positive_integer(value: object, path: str) -> int:
    integer = _nonnegative_integer(value, path)
    if integer < 1:
        raise KnowledgeModelError(path, "must be a positive integer")
    return integer


def _optional_nonempty_string(value: object, path: str) -> Optional[str]:
    if value is _MISSING:
        return None
    return _nonempty_string(value, path)


def _hash(value: object, path: str) -> str:
    text = _string(value, path)
    if not is_valid_sha256(text):
        raise KnowledgeModelError(
            path, "must be 'sha256:' followed by 64 lowercase hexadecimal digits"
        )
    return text


def _optional_hash(value: object, path: str) -> Optional[str]:
    if value is _MISSING:
        return None
    return _hash(value, path)


def _relative_path(value: object, path: str) -> str:
    text = _nonempty_string(value, path)
    if _looks_absolute(text):
        raise KnowledgeModelError(path, "must be repository-relative")
    if "\\" in text:
        raise KnowledgeModelError(path, "must use POSIX '/' separators")
    parts = text.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise KnowledgeModelError(
            path, "must be normalized without empty or dot segments"
        )
    if posixpath.normpath(text) != text:
        raise KnowledgeModelError(path, "must be a normalized POSIX path")
    return text


def _optional_relative_path(value: object, path: str) -> Optional[str]:
    if value is _MISSING:
        return None
    return _relative_path(value, path)


def _repository_identity(value: object, path: str) -> str:
    text = _nonempty_string(value, path)
    if not _REPOSITORY_IDENTITY_RE.fullmatch(text):
        raise KnowledgeModelError(
            path,
            "must be 'unknown' or a normalized namespace/path identity "
            "with a lowercase leading namespace and without a scheme, "
            "credentials, query, fragment, or checkout path",
        )
    if text != "unknown" and text.lower().endswith(".git"):
        raise KnowledgeModelError(path, "must omit a trailing '.git' suffix")
    return text


def _evaluated_revision(value: object, path: str) -> str:
    text = _nonempty_string(value, path)
    if not _EVALUATED_REVISION_RE.fullmatch(text):
        raise KnowledgeModelError(
            path,
            "must be 'unknown' or 'git:' followed by a full lowercase "
            "40- or 64-hex object ID",
        )
    return text


def _looks_absolute(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return (
        normalized.startswith("/")
        or normalized.startswith("//")
        or bool(_WINDOWS_ABSOLUTE_RE.match(normalized))
    )


def _locator(value: object, path: str) -> str:
    text = _nonempty_string(value, path)
    if not text.startswith("llm-wiki://") or any(char.isspace() for char in text):
        raise KnowledgeModelError(path, "must be a normalized llm-wiki:// locator")
    if _PERCENT_ESCAPE_RE.search(text):
        raise KnowledgeModelError(path, "contains an invalid percent escape")
    try:
        parsed = urlsplit(text)
        port = parsed.port
    except ValueError as exc:
        raise KnowledgeModelError(path, "contains an invalid authority") from exc
    if (
        parsed.scheme != "llm-wiki"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.query
        or parsed.fragment
    ):
        raise KnowledgeModelError(
            path, "must be a normalized llm-wiki:// locator without query or fragment"
        )
    if "\\" in text:
        raise KnowledgeModelError(path, "must not contain a backslash")
    segments = parsed.path.split("/")[1:] if parsed.path else []
    if any(not segment for segment in segments):
        raise KnowledgeModelError(path, "contains an empty path segment")
    for segment in segments:
        decoded = unquote(segment)
        if (
            decoded in {".", ".."}
            or "/" in decoded
            or "\\" in decoded
            or any(char.isspace() or ord(char) < 32 for char in decoded)
        ):
            raise KnowledgeModelError(path, "contains an unsafe path segment")
    return text


def _external_uri(value: object, path: str) -> str:
    text = _nonempty_string(value, path)
    if contains_uri_authority_userinfo(text):
        raise KnowledgeModelError(
            path, "must not contain credential-bearing URI authority userinfo"
        )
    if (
        any(char.isspace() for char in text)
        or "\\" in text
        or not _URI_CHAR_RE.fullmatch(text)
    ):
        raise KnowledgeModelError(
            path,
            "must be an ASCII RFC 3986 URI without whitespace, backslashes, "
            "or raw invalid characters",
        )
    if _PERCENT_ESCAPE_RE.search(text):
        raise KnowledgeModelError(path, "contains an invalid percent escape")
    try:
        parsed = urlsplit(text)
        _ = parsed.port
        hostname = parsed.hostname
    except ValueError as exc:
        raise KnowledgeModelError(path, "must be a valid external URI") from exc
    if parsed.netloc and (parsed.username is not None or parsed.password is not None):
        raise KnowledgeModelError(
            path, "must not contain credential-bearing URI authority userinfo"
        )
    uses_authority = text[len(parsed.scheme) :].startswith("://")
    requires_authority = parsed.scheme in {"http", "https", "ftp", "ftps"}
    if (
        not parsed.scheme
        or parsed.scheme == "llm-wiki"
        or ((uses_authority or requires_authority) and not parsed.netloc)
        or ((uses_authority or requires_authority) and hostname is None)
    ):
        raise KnowledgeModelError(path, "must be an absolute non-llm-wiki external URI")
    return text


def _link_observation_string(value: object, path: str) -> str:
    text = _string(value, path)
    if contains_uri_authority_userinfo(text):
        raise KnowledgeModelError(
            path, "must not contain credential-bearing URI authority userinfo"
        )
    return text


def _enum_value(value: object, enum_type: Type[_EnumT], path: str) -> _EnumT:
    if not isinstance(value, str):
        raise KnowledgeModelError(path, "must be a string")
    try:
        return enum_type(value)
    except ValueError as exc:
        allowed = ", ".join(repr(item.value) for item in enum_type)
        raise KnowledgeModelError(path, f"must be one of {allowed}") from exc


def _open_enum_value(
    value: object, enum_type: Type[_EnumT], path: str
) -> Union[_EnumT, str]:
    if not isinstance(value, str):
        raise KnowledgeModelError(path, "must be a string")
    try:
        return enum_type(value)
    except ValueError as exc:
        if _QUALIFIED_NAME_RE.fullmatch(value):
            return value
        allowed = ", ".join(repr(item.value) for item in enum_type)
        raise KnowledgeModelError(
            path,
            f"must be one of {allowed} or a qualified namespace/name value",
        ) from exc


def _reject_duplicate_components(
    tools: tuple[ProducerComponent, ...],
    extractors: tuple[ProducerComponent, ...],
    plugins: tuple[ProducerComponent, ...],
    path: str,
) -> None:
    seen: set[str] = set()
    for group_name, components in (
        ("tool", tools),
        ("extractors", extractors),
        ("plugins", plugins),
    ):
        for index, component in enumerate(components):
            if component.component_id in seen:
                suffix = "" if group_name == "tool" else f"[{index}]"
                raise KnowledgeModelError(
                    f"{path}.{group_name}{suffix}.id",
                    f"duplicates producer component {component.component_id!r}",
                )
            seen.add(component.component_id)


def _child(path: str, name: str) -> str:
    return f"{path}.{name}" if path else name


def _emit_extensions(
    payload: dict[str, Any],
    extensions: Extensions,
    path: str,
) -> dict[str, Any]:
    parsed = _parse_extensions(extensions, path)
    if parsed:
        payload["extensions"] = parsed
    return payload


def _wire_enum(value: object) -> object:
    """Return an enum's wire value while leaving invalid manual input parseable."""

    return value.value if isinstance(value, Enum) else value


def _actor_to_payload(actor: Actor) -> dict[str, Any]:
    payload: dict[str, Any] = {"kind": _wire_enum(actor.kind)}
    for key, value in (
        ("id", actor.actor_id),
        ("version", actor.version),
        ("model", actor.model),
        ("organization", actor.organization),
    ):
        if value is not None:
            payload[key] = value
    return _emit_extensions(payload, actor.extensions, "actor.extensions")


def _component_to_payload(component: ProducerComponent) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": component.component_id,
        "version": component.version,
    }
    if component.configuration_hash is not None:
        payload["configuration_hash"] = component.configuration_hash
    if component.limitations:
        payload["limitations"] = list(component.limitations)
    return _emit_extensions(payload, component.extensions, "component.extensions")


def _bundle_to_payload(bundle: BundleRecord) -> dict[str, Any]:
    repository = _emit_extensions(
        {
            "identity": bundle.repository.identity,
            "evaluated_revision": bundle.repository.evaluated_revision,
            "working_tree": _wire_enum(bundle.repository.working_tree),
        },
        bundle.repository.extensions,
        "bundle.repository.extensions",
    )
    snapshot = _emit_extensions(
        {
            "source_snapshot_hash": bundle.snapshot.source_snapshot_hash,
            "markdown_snapshot_hash": bundle.snapshot.markdown_snapshot_hash,
            "surface_index_hash": bundle.snapshot.surface_index_hash,
            "generation_options_hash": bundle.snapshot.generation_options_hash,
        },
        bundle.snapshot.extensions,
        "bundle.snapshot.extensions",
    )
    producer = _emit_extensions(
        {
            "tool": _component_to_payload(bundle.producer.tool),
            "extractors": [
                _component_to_payload(component)
                for component in bundle.producer.extractors
            ],
            "plugins": [
                _component_to_payload(component)
                for component in bundle.producer.plugins
            ],
        },
        bundle.producer.extensions,
        "bundle.producer.extensions",
    )
    return _emit_extensions(
        {
            "repository": repository,
            "snapshot": snapshot,
            "producer": producer,
        },
        bundle.extensions,
        "bundle.extensions",
    )


def _document_to_payload(document: DocumentRecord) -> dict[str, Any]:
    return _emit_extensions(
        {
            "page_kind": _wire_enum(document.page_kind),
            "page_id": document.page_id,
            "canonical_path": document.canonical_path,
            "role": _wire_enum(document.role),
        },
        document.extensions,
        "document.extensions",
    )


def _basis_to_payload(basis: EvidenceBasis) -> dict[str, Any]:
    payload: dict[str, Any] = {"scope": _wire_enum(basis.scope)}
    for key, value in (
        ("source_path", basis.source_path),
        ("extractor_ref", basis.extractor_ref),
        ("source_content_hash", basis.source_content_hash),
        ("concept_observation_hash", basis.concept_observation_hash),
        ("aggregate_input_hash", basis.aggregate_input_hash),
    ):
        if value is not None:
            payload[key] = value
    return _emit_extensions(payload, basis.extensions, "basis.extensions")


def _concept_to_payload(concept: ConceptRecord) -> dict[str, Any]:
    structure: dict[str, Any] = {
        "origin": _wire_enum(concept.facets.structure.origin),
        "evidence": _wire_enum(concept.facets.structure.evidence),
    }
    if concept.facets.structure.basis is not None:
        structure["basis"] = _basis_to_payload(concept.facets.structure.basis)
    structure = _emit_extensions(
        structure,
        concept.facets.structure.extensions,
        "facets.structure.extensions",
    )
    semantics = _emit_extensions(
        {
            "ownership": _wire_enum(concept.facets.semantics.ownership),
            "page_hash": concept.facets.semantics.page_hash,
            "authorship": _actor_to_payload(concept.facets.semantics.authorship),
            "verification": _wire_enum(concept.facets.semantics.verification),
        },
        concept.facets.semantics.extensions,
        "facets.semantics.extensions",
    )
    facets = _emit_extensions(
        {"structure": structure, "semantics": semantics},
        concept.facets.extensions,
        "facets.extensions",
    )
    kind = _wire_enum(concept.concept_kind)
    return _emit_extensions(
        {
            "locator": concept.locator,
            "concept_kind": kind,
            "title": concept.title,
            "document": _document_to_payload(concept.document),
            "facets": facets,
            "lifecycle": _wire_enum(concept.lifecycle),
        },
        concept.extensions,
        "concept.extensions",
    )


def _relationship_target_to_payload(
    target: RelationshipTarget,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "target_class": _wire_enum(target.target_class),
        **{
            name: value
            for name, value in (
                ("locator", target.locator),
                ("canonical_path", target.canonical_path),
                ("source_path", target.source_path),
                ("external_uri", target.external_uri),
                ("raw_target", target.raw_target),
                ("normalized_target", target.normalized_target),
                ("label", target.label),
            )
            if value is not None
        },
    }
    if target.location is not None:
        payload["location"] = _emit_extensions(
            {
                "start": target.location.start,
                "end": target.location.end,
            },
            target.location.extensions,
            "target.location.extensions",
        )
    return _emit_extensions(payload, target.extensions, "target.extensions")


def _relationship_evidence_to_payload(
    evidence: RelationshipEvidence,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"state": _wire_enum(evidence.state)}
    for key, value in (
        ("source_content_hash", evidence.source_content_hash),
        ("concept_observation_hash", evidence.concept_observation_hash),
        ("page_hash", evidence.page_hash),
        ("aggregate_input_hash", evidence.aggregate_input_hash),
    ):
        if value is not None:
            payload[key] = value
    return _emit_extensions(payload, evidence.extensions, "evidence.extensions")


def _relationship_to_payload(
    relationship: RelationshipRecord,
) -> dict[str, Any]:
    kind = _wire_enum(relationship.kind)
    return _emit_extensions(
        {
            "kind": kind,
            "from": relationship.source_locator,
            "target": _relationship_target_to_payload(relationship.target),
            "origin": _wire_enum(relationship.origin),
            "evidence": _relationship_evidence_to_payload(relationship.evidence),
            "resolution": _wire_enum(relationship.resolution),
        },
        relationship.extensions,
        "relationship.extensions",
    )


def _knowledge_index_to_payload_unchecked(
    model: KnowledgeIndex,
) -> dict[str, Any]:
    bundle = _bundle_to_payload(model.bundle)
    producer = bundle["producer"]
    producer["extractors"] = sorted(
        producer["extractors"], key=lambda component: component["id"]
    )
    producer["plugins"] = sorted(
        producer["plugins"], key=lambda component: component["id"]
    )
    concepts = sorted(
        (_concept_to_payload(concept) for concept in model.concepts),
        key=lambda concept: concept["locator"],
    )
    relationships = sorted(
        (
            _relationship_to_payload(relationship)
            for relationship in model.relationships
        ),
        key=_canonical_relationship_key,
    )
    return _emit_extensions(
        {
            "schema_version": model.schema_version,
            "bundle": bundle,
            "concepts": concepts,
            "relationships": relationships,
        },
        model.extensions,
        "extensions",
    )


def _canonical_relationship_key(relationship: dict[str, Any]) -> str:
    return json.dumps(
        relationship,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


__all__ = [
    "EVALUATED_REVISION_PATTERN",
    "LIMITATION_CODE_PATTERN",
    "PAGE_KIND_TO_CONCEPT_KIND",
    "QUALIFIED_NAME_PATTERN",
    "REPOSITORY_IDENTITY_PATTERN",
    "REPOSITORY_IDENTITY_SOURCE_EXTENSION",
    "SHA256_PATTERN",
    "Actor",
    "ActorKind",
    "BundleRecord",
    "ComputedFreshness",
    "ConceptFacets",
    "ConceptKind",
    "ConceptKindValue",
    "ConceptRecord",
    "DocumentRecord",
    "EvidenceBasis",
    "EvidenceState",
    "KnowledgeIndex",
    "KnowledgeLoadState",
    "KnowledgeModelError",
    "KnowledgeOrigin",
    "KnowledgeProjectionProfile",
    "Lifecycle",
    "LifecycleState",
    "LinkTargetClass",
    "ObservationScope",
    "Origin",
    "ProducerComponent",
    "ProducerRecord",
    "RelationshipEvidence",
    "RelationshipKind",
    "RelationshipKindValue",
    "RelationshipLocation",
    "RelationshipRecord",
    "RelationshipResolution",
    "RelationshipTarget",
    "RelationshipTargetClass",
    "RepositoryIdentitySource",
    "RepositoryRecord",
    "Resolution",
    "SemanticFacet",
    "SnapshotRecord",
    "StructuralFacet",
    "TargetClass",
    "Verification",
    "VerificationState",
    "WorkingTreeState",
    "concept_kind_for_page_kind",
    "knowledge_index_to_payload",
    "load_knowledge_schema",
    "parse_knowledge_index",
    "repository_identities_match",
    "serialize_knowledge_index",
    "validate_knowledge_payload",
]
