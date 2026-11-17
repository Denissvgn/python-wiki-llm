"""The concept, relationship and graph-edge kinds a knowledge index may use.

The ``llm-wiki-knowledge/v1`` format fixes its built-in kinds and lets any
other concept, relationship or typed-graph edge kind appear as a qualified
``namespace/name`` value. A :class:`KindRegistry` lets a host declare those
custom kinds as part of its domain:

* a :class:`ConceptKindSpec` names the page kinds a custom concept kind may
  appear on and whether it is document-only (no structural evidence);
* a :class:`RelationshipKindSpec` declares a custom relationship or typed-graph
  edge kind;
* ``undeclared="reject"`` refuses custom kinds the registry does not declare,
  while the default ``"accept"`` keeps the format's open behavior.

Page kinds are fixed by the v1 format and cannot be added; the registry lists
them for discovery. Built-in kinds keep the rules the format defines.

The checks run when a knowledge index is parsed, and the registry is part of
the validation identity, so a model validated under one registry is not
trusted under another. Context packets do not consult the registry: they
validate the same way for every consumer.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Literal

from llm_wiki_engine.knowledge_graph import CORE_RELATIONSHIP_KINDS
from .knowledge_model import (
    PAGE_KIND_TO_CONCEPT_KIND,
    QUALIFIED_NAME_PATTERN,
    ConceptKind,
    EvidenceState,
    KnowledgeModelError,
    Origin,
    RelationshipKind,
)
from llm_wiki_engine.wiki_surface import PageKind

if TYPE_CHECKING:
    from .knowledge_model import ConceptRecord, KnowledgeIndex

UndeclaredPolicy = Literal["accept", "reject"]

_QUALIFIED_NAME_RE = re.compile(QUALIFIED_NAME_PATTERN)
_TYPED_GRAPH_EXTENSION = "llm-wiki/typed-graph-v1"


def _require_name(name: object, *, builtin: frozenset[str]) -> str:
    if not isinstance(name, str) or not name:
        raise ValueError("kind name must be a non-empty string")
    if name not in builtin and _QUALIFIED_NAME_RE.fullmatch(name) is None:
        raise ValueError(f"custom kind {name!r} must be a qualified namespace/name value")
    return name


_BUILTIN_CONCEPT_KINDS = frozenset(kind.value for kind in ConceptKind)
_BUILTIN_RELATIONSHIP_KINDS = frozenset(kind.value for kind in RelationshipKind)
_BUILTIN_GRAPH_KINDS = frozenset(CORE_RELATIONSHIP_KINDS)


@dataclass(frozen=True)
class ConceptKindSpec:
    """One concept kind and the page kinds its concepts may appear on."""

    name: str
    page_kinds: tuple[PageKind, ...]
    document_only: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        _require_name(self.name, builtin=_BUILTIN_CONCEPT_KINDS)
        try:
            page_kinds = tuple(PageKind(value) for value in self.page_kinds)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"concept kind {self.name!r} names an unknown page kind") from exc
        if not page_kinds or len(set(page_kinds)) != len(page_kinds):
            raise ValueError(f"concept kind {self.name!r} needs distinct page kinds")
        if not isinstance(self.document_only, bool):
            raise TypeError("document_only must be a boolean")
        if not isinstance(self.description, str):
            raise TypeError("description must be a string")
        object.__setattr__(self, "page_kinds", page_kinds)


@dataclass(frozen=True)
class RelationshipKindSpec:
    """One relationship or typed-graph edge kind."""

    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("kind name must be a non-empty string")
        if not isinstance(self.description, str):
            raise TypeError("description must be a string")


def _builtin_concept_specs() -> tuple[ConceptKindSpec, ...]:
    return tuple(
        ConceptKindSpec(
            kind.value,
            tuple(page for page, concept in PAGE_KIND_TO_CONCEPT_KIND.items() if concept is kind),
            document_only=kind.is_document_only,
        )
        for kind in ConceptKind
    )


_BUILTIN_CONCEPT_SPECS = _builtin_concept_specs()
_BUILTIN_RELATIONSHIP_SPECS = tuple(RelationshipKindSpec(kind.value) for kind in RelationshipKind)
_BUILTIN_GRAPH_SPECS = tuple(RelationshipKindSpec(kind) for kind in CORE_RELATIONSHIP_KINDS)


def _unique(specs: tuple, family: str) -> dict:
    by_name = {}
    for spec in specs:
        if spec.name in by_name:
            raise ValueError(f"{family} kind names must be unique: {spec.name!r}")
        by_name[spec.name] = spec
    return by_name


def _require_family(specs: object, spec_type: type, builtin: tuple, family: str) -> tuple:
    values = tuple(specs)  # type: ignore[arg-type]
    if not all(isinstance(spec, spec_type) for spec in values):
        raise TypeError(f"{family} kinds must be {spec_type.__name__} values")
    by_name = _unique(values, family)
    builtin_names = {spec.name for spec in builtin}
    if any(by_name.get(spec.name) != spec for spec in builtin):
        raise ValueError(f"{family} kinds must keep every built-in kind unchanged")
    for name in by_name:
        _require_name(name, builtin=frozenset(builtin_names))
    return values


@dataclass(frozen=True)
class KindRegistry:
    """Declared concept, relationship and typed-graph edge kinds."""

    concept_kinds: tuple[ConceptKindSpec, ...] = _BUILTIN_CONCEPT_SPECS
    relationship_kinds: tuple[RelationshipKindSpec, ...] = _BUILTIN_RELATIONSHIP_SPECS
    graph_relationship_kinds: tuple[RelationshipKindSpec, ...] = _BUILTIN_GRAPH_SPECS
    undeclared: UndeclaredPolicy = "accept"

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_kinds", _require_family(
            self.concept_kinds, ConceptKindSpec, _BUILTIN_CONCEPT_SPECS, "concept"))
        object.__setattr__(self, "relationship_kinds", _require_family(
            self.relationship_kinds, RelationshipKindSpec, _BUILTIN_RELATIONSHIP_SPECS, "relationship"))
        object.__setattr__(self, "graph_relationship_kinds", _require_family(
            self.graph_relationship_kinds, RelationshipKindSpec, _BUILTIN_GRAPH_SPECS, "graph relationship"))
        if self.undeclared not in ("accept", "reject"):
            raise ValueError("undeclared must be 'accept' or 'reject'")

    @property
    def page_kinds(self) -> tuple[PageKind, ...]:
        """The page kinds the v1 format defines; they cannot be extended."""
        return tuple(PageKind)

    def with_concept_kind(self, spec: ConceptKindSpec) -> KindRegistry:
        """A copy of this registry that also declares ``spec``."""
        return replace(self, concept_kinds=(*self.concept_kinds, spec))

    def with_relationship_kind(self, spec: RelationshipKindSpec) -> KindRegistry:
        """A copy of this registry that also declares relationship kind ``spec``."""
        return replace(self, relationship_kinds=(*self.relationship_kinds, spec))

    def with_graph_relationship_kind(self, spec: RelationshipKindSpec) -> KindRegistry:
        """A copy of this registry that also declares typed-graph edge kind ``spec``."""
        return replace(self, graph_relationship_kinds=(*self.graph_relationship_kinds, spec))

    def rejecting_undeclared(self) -> KindRegistry:
        """A copy of this registry that refuses custom kinds it does not declare."""
        return replace(self, undeclared="reject")

    def describe(self) -> dict[str, Any]:
        """A JSON-ready summary of the declared kinds."""
        return {
            "concept": [spec.name for spec in self.concept_kinds],
            "relationship": [spec.name for spec in self.relationship_kinds],
            "graph_relationship": [spec.name for spec in self.graph_relationship_kinds],
            "page": [kind.value for kind in self.page_kinds],
            "undeclared": self.undeclared,
        }

    def identity(self) -> tuple:
        """A value that changes whenever what this registry accepts may change."""
        return (
            tuple((spec.name, tuple(kind.value for kind in spec.page_kinds), spec.document_only)
                  for spec in self.concept_kinds),
            tuple(spec.name for spec in self.relationship_kinds),
            tuple(spec.name for spec in self.graph_relationship_kinds),
            self.undeclared,
        )

    def check(self, model: KnowledgeIndex) -> None:
        """Refuse custom kinds in ``model`` that break this registry's rules."""
        concepts = {spec.name: spec for spec in self.concept_kinds}
        for index, concept in enumerate(model.concepts):
            if not isinstance(concept.concept_kind, ConceptKind):
                self._check_concept(concept, concepts.get(concept.concept_kind), f"concepts[{index}]")

        relationships = {spec.name for spec in self.relationship_kinds}
        for index, relationship in enumerate(model.relationships):
            kind = relationship.kind
            if not isinstance(kind, RelationshipKind):
                self._require_declared(kind, relationships, f"relationships[{index}].kind", "relationship")

        graph = model.extensions.get(_TYPED_GRAPH_EXTENSION)
        edges = graph.get("edges") if isinstance(graph, Mapping) else None
        if isinstance(edges, (list, tuple)):
            graph_kinds = {spec.name for spec in self.graph_relationship_kinds}
            for index, edge in enumerate(edges):
                kind = edge.get("kind") if isinstance(edge, Mapping) else None
                if isinstance(kind, str):
                    self._require_declared(
                        kind, graph_kinds,
                        f"extensions.{_TYPED_GRAPH_EXTENSION}.edges[{index}].kind",
                        "typed-graph relationship",
                    )

    def _require_declared(self, kind: str, declared: set[str], path: str, family: str) -> None:
        if kind not in declared and self.undeclared == "reject":
            raise KnowledgeModelError(path, f"{kind!r} is not a declared {family} kind")

    def _check_concept(self, concept: ConceptRecord, spec: ConceptKindSpec | None, path: str) -> None:
        kind = str(concept.concept_kind)
        if spec is None:
            self._require_declared(kind, set(), f"{path}.concept_kind", "concept")
            return
        page_kind = concept.document.page_kind
        if page_kind not in spec.page_kinds:
            allowed = ", ".join(repr(value.value) for value in spec.page_kinds)
            raise KnowledgeModelError(
                f"{path}.concept_kind",
                f"{kind!r} is not allowed on page_kind {page_kind.value!r}; allowed: {allowed}",
            )
        structure = concept.facets.structure
        if spec.document_only and (
            structure.origin is not Origin.UNKNOWN
            or structure.evidence not in {EvidenceState.UNKNOWN, EvidenceState.NOT_APPLICABLE}
            or structure.basis is not None
        ):
            raise KnowledgeModelError(
                f"{path}.facets.structure",
                "document-only concepts must use unknown origin, "
                "unknown/not-applicable evidence, and no structural basis",
            )


#: Today's kinds, accepting any qualified custom kind.
DEFAULT_KINDS = KindRegistry()

_ACTIVE_KINDS: ContextVar[KindRegistry | None] = ContextVar("llm_wiki_kinds", default=None)


def current_kinds() -> KindRegistry:
    """The registry chosen for this context, or :data:`DEFAULT_KINDS`."""
    return _ACTIVE_KINDS.get() or DEFAULT_KINDS


@contextmanager
def using_kinds(registry: KindRegistry) -> Iterator[KindRegistry]:
    """Check knowledge index kinds inside the block with ``registry``."""
    if not isinstance(registry, KindRegistry):
        raise TypeError("registry must be a KindRegistry")
    token = _ACTIVE_KINDS.set(registry)
    try:
        yield registry
    finally:
        _ACTIVE_KINDS.reset(token)


__all__ = [
    "DEFAULT_KINDS",
    "ConceptKindSpec",
    "KindRegistry",
    "RelationshipKindSpec",
    "current_kinds",
    "using_kinds",
]
