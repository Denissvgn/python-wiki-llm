"""Conservative section ownership, scoped hashes, and semantic merge policy.

Ownership in this module is finer-grained than ``wiki_surface.SurfaceRole``.
The latter remains the compatibility summary for a complete page; this module
describes only the canonical sections that current generation and sync
behavior can identify without guessing.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import cast

from .contracts import (
    SECTION_OWNERSHIP_EXTENSION_KEY,
    SECTION_OWNERSHIP_SCHEMA_VERSION,
)
from .knowledge_evidence import hash_json, sha256_bytes
from .markdown_sections import (
    GENERATED_INDEX_ENTRY_POINT_FLOWS_HEADING,
    GENERATED_INDEX_HTTP_API_CONTRACTS_HEADING,
    SECTION_ORDER_DOMAIN,
    MarkdownSection,
    MarkdownSectionDocument,
    mixed_table_projection,
    normalize_markdown,
    parse_markdown_document,
    preserve_table_description_cells,
    replace_section_body,
    section_locator,
    section_body,
    should_preserve_semantic_value,
    table_description_cells,
)
from .validation import (
    require_exact_fields,
    require_int_at_least,
    require_mapping,
    require_nonempty_text,
    require_sequence,
    require_sha256,
)
from .wiki_surface import PageKind


class SectionOwnership(str, Enum):
    """The authority boundary of one parsed Markdown section."""

    GENERATED = "generated"
    SEMANTIC = "semantic"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class SectionOwnershipError(ValueError):
    """Field-specific failure for the persisted section ownership contract."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True)
class SectionObservation:
    """One ordered section plus its exact and ownership-scoped commitments."""

    locator: str
    page_locator: str
    heading_path: tuple[str, ...]
    title: str | None
    level: int
    occurrence: int
    ordinal: int
    parent_locator: str | None
    ownership: SectionOwnership
    exact_hash: str
    structural_hash: str | None = None
    semantic_hash: str | None = None
    occurrence_path: tuple[int, ...] = ()

    def to_payload(self) -> dict[str, object]:
        """Return the stable extension representation."""

        payload: dict[str, object] = {
            "locator": self.locator,
            "page_locator": self.page_locator,
            "heading_path": list(self.heading_path),
            "title": self.title,
            "level": self.level,
            "occurrence": self.occurrence,
            "ordinal": self.ordinal,
            "parent_locator": self.parent_locator,
            "ownership": self.ownership.value,
            "exact_hash": self.exact_hash,
        }
        if self.occurrence_path:
            payload["occurrence_path"] = list(self.occurrence_path)
        if self.structural_hash is not None:
            payload["structural_hash"] = self.structural_hash
        if self.semantic_hash is not None:
            payload["semantic_hash"] = self.semantic_hash
        return payload


@dataclass(frozen=True)
class PageSectionObservations:
    """All ordered section observations for one final Markdown page."""

    page_locator: str
    page_kind: PageKind
    source_hash: str
    exact_hash: str
    ordering_hash: str
    sections: tuple[SectionObservation, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "page_locator": self.page_locator,
            "page_kind": self.page_kind.value,
            "source_hash": self.source_hash,
            "exact_hash": self.exact_hash,
            "ordering_hash": self.ordering_hash,
            "sections": [section.to_payload() for section in self.sections],
        }


@dataclass(frozen=True)
class SemanticMergeResult:
    """Regenerated Markdown and the number of semantic values restored."""

    text: str
    preserved: int = 0


_INDEX_GENERATED_HEADINGS = frozenset(
    heading.casefold()
    for heading in (
        "Surface Overview",
        "Entities",
        "Modules",
        "Workflows",
        "Guides",
        "User Flows",
        GENERATED_INDEX_ENTRY_POINT_FLOWS_HEADING,
        "Infrastructure",
        "Architecture",
        "Dependency Architecture",
        "API Contracts",
        GENERATED_INDEX_HTTP_API_CONTRACTS_HEADING,
        "Log",
    )
)

_ENTITY_GENERATED_HEADINGS = frozenset(
    heading.casefold()
    for heading in (
        "Declaration",
        "Model Configuration",
        "Validators",
        "Relationships",
    )
)
_ENTITY_MIXED_HEADINGS = frozenset(
    heading.casefold() for heading in ("Attributes", "Methods")
)

_MODULE_GENERATED_HEADINGS = frozenset(
    heading.casefold()
    for heading in (
        "Imports",
        "Declarations",
        "Module Signals",
        "Local dependency map",
    )
)
_MODULE_MIXED_HEADINGS = frozenset(
    heading.casefold() for heading in ("Classes", "Functions")
)

_WORKFLOW_GENERATED_HEADINGS = frozenset(
    heading.casefold() for heading in ("Sequence", "Touches")
)
_FLOW_GENERATED_HEADINGS = frozenset(
    heading.casefold()
    for heading in (
        "Call sequence",
        "Data flow",
        "API contract",
    )
)
_API_GENERATED_HEADINGS = frozenset(
    heading.casefold()
    for heading in (
        "Applications",
        "Operations",
        "Diagnostics",
        "Excluded operations",
    )
)
_DEPENDENCIES_GENERATED_HEADINGS = frozenset(
    heading.casefold()
    for heading in (
        "Module graph",
        "Cycles",
        "Fan-in / Fan-out",
        "External dependencies",
    )
)
_LOAD_ORDER_GENERATED_HEADINGS = frozenset(
    heading.casefold()
    for heading in (
        "Load order",
        "Module-level side effects",
        "Factory / wiring",
        "Indeterminate (cyclic) groups",
    )
)
_INFRASTRUCTURE_GENERATED_HEADINGS = frozenset(
    heading.casefold()
    for heading in (
        "Advisories",
        "Triggers",
        "Jobs",
        "Resources",
        "Settings",
        "Rule Groups",
        "Rule Files",
        "Scrape Jobs",
        "Entries",
        "Clients",
        "Schema Stores",
        "Listeners",
        "Clusters",
        "Admin Ports",
        "Build Stages",
        "Exposed Ports",
        "Build Arguments",
        "Environment Variables",
        "Volumes",
        "Entry Point",
        "File Copies",
        "Unsupported Copied Sources",
        "Labels",
        "Services",
        "Networks",
        "Named Volumes",
        "Modules",
        "Dependencies",
        "Plugins",
        "Outputs",
    )
)
_HTTP_OPERATION_HEADING_RE = re.compile(
    r"^(?:CONNECT|DELETE|GET|HEAD|OPTIONS|PATCH|POST|PUT|TRACE)\s+\S+",
    re.IGNORECASE,
)
_LOG_DATE_HEADING_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _coerce_page_kind(page_kind: PageKind | str) -> PageKind:
    if isinstance(page_kind, PageKind):
        return page_kind
    try:
        return PageKind(page_kind)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"unknown page kind: {page_kind!r}") from exc


def _top_level_policy(
    page_kind: PageKind,
    title: str,
    canonical_occurrence: int,
    *,
    index_preserved: bool,
) -> SectionOwnership:
    folded = title.casefold()

    if page_kind is PageKind.GUIDES:
        return SectionOwnership.SEMANTIC
    if page_kind is PageKind.LOG:
        if _LOG_DATE_HEADING_RE.fullmatch(title) is not None:
            return SectionOwnership.GENERATED
        return SectionOwnership.UNKNOWN
    if page_kind is PageKind.INDEX:
        if folded in _INDEX_GENERATED_HEADINGS:
            return (
                SectionOwnership.GENERATED
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        # Sync explicitly carries trailing custom index sections forward.
        return (
            SectionOwnership.SEMANTIC
            if index_preserved
            else SectionOwnership.UNKNOWN
        )
    if page_kind is PageKind.ENTITIES:
        if folded == "description":
            return (
                SectionOwnership.SEMANTIC
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        if folded in _ENTITY_MIXED_HEADINGS:
            return (
                SectionOwnership.MIXED
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        if folded in _ENTITY_GENERATED_HEADINGS:
            return (
                SectionOwnership.GENERATED
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        return SectionOwnership.UNKNOWN
    if page_kind is PageKind.MODULES:
        if folded == "description":
            return (
                SectionOwnership.SEMANTIC
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        if folded in _MODULE_MIXED_HEADINGS:
            return (
                SectionOwnership.MIXED
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        if folded in _MODULE_GENERATED_HEADINGS:
            return (
                SectionOwnership.GENERATED
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        return SectionOwnership.UNKNOWN
    if page_kind is PageKind.WORKFLOWS:
        if folded == "behavior":
            return (
                SectionOwnership.SEMANTIC
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        if folded in _WORKFLOW_GENERATED_HEADINGS and canonical_occurrence == 1:
            return SectionOwnership.GENERATED
        return SectionOwnership.UNKNOWN
    if page_kind is PageKind.FLOWS:
        if folded == "behavior":
            return (
                SectionOwnership.SEMANTIC
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        if folded in _FLOW_GENERATED_HEADINGS and canonical_occurrence == 1:
            return SectionOwnership.GENERATED
        return SectionOwnership.UNKNOWN
    if page_kind is PageKind.INFRASTRUCTURE:
        if folded == "notes":
            return (
                SectionOwnership.SEMANTIC
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        if (
            folded in _INFRASTRUCTURE_GENERATED_HEADINGS
            and canonical_occurrence == 1
        ):
            return SectionOwnership.GENERATED
        return SectionOwnership.UNKNOWN
    if page_kind is PageKind.API_CONTRACTS:
        if folded == "notes":
            return (
                SectionOwnership.SEMANTIC
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        if (
            folded in _API_GENERATED_HEADINGS
            or _HTTP_OPERATION_HEADING_RE.match(title) is not None
        ) and canonical_occurrence == 1:
            return SectionOwnership.GENERATED
        return SectionOwnership.UNKNOWN
    if page_kind is PageKind.DEPENDENCIES:
        if folded == "notes":
            return (
                SectionOwnership.SEMANTIC
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        if (
            folded in _DEPENDENCIES_GENERATED_HEADINGS
            and canonical_occurrence == 1
        ):
            return SectionOwnership.GENERATED
        return SectionOwnership.UNKNOWN
    if page_kind is PageKind.LOAD_ORDER:
        if folded == "notes":
            return (
                SectionOwnership.SEMANTIC
                if canonical_occurrence == 1
                else SectionOwnership.UNKNOWN
            )
        if (
            folded in _LOAD_ORDER_GENERATED_HEADINGS
            and canonical_occurrence == 1
        ):
            return SectionOwnership.GENERATED
        return SectionOwnership.UNKNOWN
    return SectionOwnership.UNKNOWN


def classify_section_ownership(
    page_kind: PageKind | str,
    section: MarkdownSection,
    *,
    parent_ownership: SectionOwnership | None = None,
    canonical_occurrence: int | None = None,
    index_preserved: bool = True,
) -> SectionOwnership:
    """Classify one section without an optimistic fallback.

    Canonical policies apply to level-two sections.  Deeper headings inherit a
    known level-two-or-deeper parent.  A page title does not make otherwise
    unknown custom sections generated merely by containing them.
    """

    kind = _coerce_page_kind(page_kind)
    if kind is PageKind.GUIDES:
        return SectionOwnership.SEMANTIC
    if kind is PageKind.LOG and section.level == 1:
        return SectionOwnership.GENERATED
    if section.level >= 3 and parent_ownership is not None:
        return parent_ownership
    if section.level != 2:
        return SectionOwnership.UNKNOWN
    occurrence = canonical_occurrence or section.sibling_occurrence
    return _top_level_policy(
        kind,
        section.title,
        occurrence,
        index_preserved=index_preserved,
    )


def _scoped_hashes(
    section: MarkdownSection,
    ownership: SectionOwnership,
) -> tuple[str | None, str | None]:
    if ownership is SectionOwnership.GENERATED:
        return section.exact_hash, None
    if ownership is SectionOwnership.SEMANTIC:
        return None, section.exact_hash
    if ownership is SectionOwnership.MIXED:
        projection = mixed_table_projection(section.exact_text)
        return projection.structural_hash, projection.semantic_hash
    return None, None


def _preamble_observation(
    document: MarkdownSectionDocument,
    page_kind: PageKind,
    end: int,
) -> SectionObservation | None:
    preamble = document.normalized_markdown[:end]
    if not preamble:
        return None
    if page_kind is PageKind.GUIDES:
        ownership = SectionOwnership.SEMANTIC
    elif page_kind is PageKind.LOG:
        ownership = SectionOwnership.GENERATED
    else:
        ownership = SectionOwnership.UNKNOWN
    exact_hash = sha256_bytes(preamble.encode("utf-8"))
    structural_hash = (
        exact_hash if ownership is SectionOwnership.GENERATED else None
    )
    semantic_hash = exact_hash if ownership is SectionOwnership.SEMANTIC else None
    return SectionObservation(
        locator=f"{document.page_locator}#section/@preamble",
        page_locator=document.page_locator,
        heading_path=(),
        title=None,
        level=0,
        occurrence=1,
        ordinal=0,
        parent_locator=None,
        ownership=ownership,
        exact_hash=exact_hash,
        structural_hash=structural_hash,
        semantic_hash=semantic_hash,
    )


def _expected_persisted_ownership(
    page_kind: PageKind,
    section: Mapping[str, object],
    *,
    parent_ownership: SectionOwnership | None,
    canonical_occurrence: int,
) -> SectionOwnership:
    title = section["title"]
    level = section["level"]
    if title is None:
        if page_kind is PageKind.GUIDES:
            return SectionOwnership.SEMANTIC
        if page_kind is PageKind.LOG:
            return SectionOwnership.GENERATED
        return SectionOwnership.UNKNOWN
    assert isinstance(title, str)
    assert isinstance(level, int)
    if page_kind is PageKind.GUIDES:
        return SectionOwnership.SEMANTIC
    if page_kind is PageKind.LOG and level == 1:
        return SectionOwnership.GENERATED
    if level >= 3 and parent_ownership is not None:
        return parent_ownership
    if level != 2:
        return SectionOwnership.UNKNOWN
    return _top_level_policy(
        page_kind,
        title,
        canonical_occurrence,
        # Generated knowledge observes the final sync result, where custom
        # index sections are precisely the sections sync preserves.
        index_preserved=True,
    )


def observe_page_sections(
    markdown: str,
    page_locator: str,
    page_kind: PageKind | str,
    *,
    index_preserved: bool = True,
) -> PageSectionObservations:
    """Observe ownership and scoped hashes from final post-merge Markdown."""

    kind = _coerce_page_kind(page_kind)
    document = parse_markdown_document(markdown, page_locator)
    preamble_end = (
        document.sections[0].start
        if document.sections
        else len(document.normalized_markdown)
    )
    preamble = _preamble_observation(document, kind, preamble_end)
    ordinal_offset = 1 if preamble is not None else 0
    observations: list[SectionObservation] = []
    ownership_by_locator: dict[str, SectionOwnership] = {}
    canonical_occurrences: defaultdict[tuple[str | None, str], int] = defaultdict(int)

    for section in document.sections:
        # Only direct level-two policy names share the canonical occurrence
        # domain.  Parser occurrence paths intentionally remain exact-case.
        canonical_key = (section.parent_locator, section.title.casefold())
        canonical_occurrences[canonical_key] += 1
        parent_ownership = (
            ownership_by_locator.get(section.parent_locator)
            if section.parent_locator is not None
            else None
        )
        ownership = classify_section_ownership(
            kind,
            section,
            parent_ownership=parent_ownership,
            canonical_occurrence=canonical_occurrences[canonical_key],
            index_preserved=index_preserved,
        )
        ownership_by_locator[section.locator] = ownership
        structural_hash, semantic_hash = _scoped_hashes(section, ownership)
        observations.append(
            SectionObservation(
                locator=section.locator,
                page_locator=section.page_locator,
                heading_path=section.heading_path,
                title=section.title,
                level=section.level,
                occurrence=section.sibling_occurrence,
                ordinal=section.ordinal + ordinal_offset,
                parent_locator=section.parent_locator,
                ownership=ownership,
                exact_hash=section.exact_hash,
                structural_hash=structural_hash,
                semantic_hash=semantic_hash,
                occurrence_path=section.occurrence_path,
            )
        )

    all_observations = (
        ((preamble,) if preamble is not None else ()) + tuple(observations)
    )
    return PageSectionObservations(
        page_locator=page_locator,
        page_kind=kind,
        source_hash=sha256_bytes(markdown.encode("utf-8")),
        exact_hash=document.exact_hash,
        ordering_hash=document.ordering_hash,
        sections=all_observations,
    )


# Discoverable aliases for callers that use "collect" or "observation" language.
collect_section_observations = observe_page_sections
section_observations = observe_page_sections


def serialize_section_ownership(
    pages: Iterable[PageSectionObservations],
) -> dict[str, object]:
    """Serialize pages deterministically without changing document section order."""

    ordered = sorted(
        pages,
        key=lambda page: (page.page_locator.casefold(), page.page_locator),
    )
    seen: set[str] = set()
    for page in ordered:
        if page.page_locator in seen:
            raise ValueError(f"duplicate page section locator: {page.page_locator}")
        seen.add(page.page_locator)
        ordinals = [section.ordinal for section in page.sections]
        if ordinals != sorted(ordinals) or len(ordinals) != len(set(ordinals)):
            raise ValueError(
                f"section ordinals must be unique and ordered: {page.page_locator}"
            )
    return {
        "schema_version": SECTION_OWNERSHIP_SCHEMA_VERSION,
        "pages": [page.to_payload() for page in ordered],
    }


def validate_section_ownership(
    payload: object,
    *,
    concepts: Mapping[str, tuple[PageKind | str, str]] | None = None,
) -> dict[str, object]:
    """Validate and canonicalize one persisted section ownership extension.

    ``concepts`` maps each expected page locator to its page kind and exact
    Markdown hash. Supplying it enforces full page parity with the enclosing
    knowledge index.
    """

    root = _section_object(payload, "section_ownership")
    _section_fields(
        root,
        "section_ownership",
        {"schema_version", "pages"},
        {"schema_version", "pages"},
    )
    if root["schema_version"] != SECTION_OWNERSHIP_SCHEMA_VERSION:
        raise SectionOwnershipError(
            "section_ownership.schema_version",
            f"must be {SECTION_OWNERSHIP_SCHEMA_VERSION!r}",
        )
    raw_pages = _section_array(root["pages"], "section_ownership.pages")
    pages: list[dict[str, object]] = []
    seen_pages: set[str] = set()
    seen_sections: set[str] = set()
    for page_index, raw_page in enumerate(raw_pages):
        path = f"section_ownership.pages[{page_index}]"
        page = _section_object(raw_page, path)
        _section_fields(
            page,
            path,
            {
                "page_locator",
                "page_kind",
                "source_hash",
                "exact_hash",
                "ordering_hash",
                "sections",
            },
            {
                "page_locator",
                "page_kind",
                "source_hash",
                "exact_hash",
                "ordering_hash",
                "sections",
            },
        )
        locator = _section_string(page["page_locator"], f"{path}.page_locator")
        if locator in seen_pages:
            raise SectionOwnershipError(
                f"{path}.page_locator",
                f"duplicates page locator {locator!r}",
            )
        seen_pages.add(locator)
        try:
            page_kind = PageKind(page["page_kind"])
        except (TypeError, ValueError) as exc:
            raise SectionOwnershipError(
                f"{path}.page_kind",
                f"unsupported page kind {page['page_kind']!r}",
            ) from exc
        source_hash = _section_hash(page["source_hash"], f"{path}.source_hash")
        exact_hash = _section_hash(page["exact_hash"], f"{path}.exact_hash")
        ordering_hash = _section_hash(
            page["ordering_hash"],
            f"{path}.ordering_hash",
        )
        expected = concepts.get(locator) if concepts is not None else None
        if concepts is not None and expected is None:
            raise SectionOwnershipError(
                f"{path}.page_locator",
                "does not identify a concept in the enclosing knowledge index",
            )
        if expected is not None:
            expected_kind = (
                expected[0]
                if isinstance(expected[0], PageKind)
                else PageKind(expected[0])
            )
            if page_kind is not expected_kind:
                raise SectionOwnershipError(
                    f"{path}.page_kind",
                    f"does not match concept page kind {expected_kind.value!r}",
                )
            if source_hash != expected[1]:
                raise SectionOwnershipError(
                    f"{path}.source_hash",
                    "does not match the enclosing concept page hash",
                )

        raw_sections = _section_array(page["sections"], f"{path}.sections")
        sections = [
            _normalise_section_record(
                value,
                f"{path}.sections[{section_index}]",
                page_locator=locator,
                seen_sections=seen_sections,
            )
            for section_index, value in enumerate(raw_sections)
        ]
        ordinals = [section["ordinal"] for section in sections]
        if ordinals != list(range(len(sections))):
            raise SectionOwnershipError(
                f"{path}.sections",
                "must use contiguous document-order ordinals starting at zero",
            )
        prior_sections: dict[str, Mapping[str, object]] = {}
        ownership_by_locator: dict[str, SectionOwnership] = {}
        canonical_occurrences: defaultdict[tuple[str | None, str], int] = (
            defaultdict(int)
        )
        for section_index, section in enumerate(sections):
            parent = section["parent_locator"]
            heading_path = cast(list[str], section["heading_path"])
            if section["title"] is None and section_index != 0:
                raise SectionOwnershipError(
                    f"{path}.sections[{section_index}].title",
                    "the synthetic preamble must be the first section",
                )
            if parent is None:
                if section["title"] is not None and len(heading_path) != 1:
                    raise SectionOwnershipError(
                        f"{path}.sections[{section_index}].heading_path",
                        "a root section must have one heading-path component",
                    )
            else:
                parent_section = prior_sections.get(str(parent))
                if parent_section is None:
                    raise SectionOwnershipError(
                        f"{path}.sections[{section_index}].parent_locator",
                        "must identify an earlier section in the same page",
                    )
                if (
                    parent_section["title"] is None
                    or heading_path[:-1]
                    != cast(list[str], parent_section["heading_path"])
                    or cast(list[int], section.get("occurrence_path", []))[:-1]
                    != cast(
                        list[int],
                        parent_section.get("occurrence_path", []),
                    )
                    or cast(int, section["level"])
                    <= cast(int, parent_section["level"])
                ):
                    raise SectionOwnershipError(
                        f"{path}.sections[{section_index}].parent_locator",
                        "does not match the direct heading parent",
                    )
            title = section["title"]
            canonical_occurrence = 1
            if isinstance(title, str):
                canonical_key = (
                    str(parent) if parent is not None else None,
                    title.casefold(),
                )
                canonical_occurrences[canonical_key] += 1
                canonical_occurrence = canonical_occurrences[canonical_key]
            parent_ownership = (
                ownership_by_locator.get(str(parent))
                if parent is not None
                else None
            )
            expected_ownership = _expected_persisted_ownership(
                page_kind,
                section,
                parent_ownership=parent_ownership,
                canonical_occurrence=canonical_occurrence,
            )
            if section["ownership"] != expected_ownership.value:
                raise SectionOwnershipError(
                    f"{path}.sections[{section_index}].ownership",
                    (
                        "does not match the conservative section policy; "
                        f"expected {expected_ownership.value!r}"
                    ),
                )
            ownership_by_locator[str(section["locator"])] = expected_ownership
            prior_sections[str(section["locator"])] = section
        if _section_ordering_hash(locator, sections) != ordering_hash:
            raise SectionOwnershipError(
                f"{path}.ordering_hash",
                "does not match the canonical section hierarchy and order",
            )
        pages.append(
            {
                "page_locator": locator,
                "page_kind": page_kind.value,
                "source_hash": source_hash,
                "exact_hash": exact_hash,
                "ordering_hash": ordering_hash,
                "sections": sections,
            }
        )

    if concepts is not None and seen_pages != set(concepts):
        missing = min(set(concepts) - seen_pages)
        raise SectionOwnershipError(
            "section_ownership.pages",
            f"is missing concept page {missing!r}",
        )
    pages.sort(key=lambda page: (str(page["page_locator"]).casefold(), page["page_locator"]))
    return {
        "schema_version": SECTION_OWNERSHIP_SCHEMA_VERSION,
        "pages": pages,
    }


def _normalise_section_record(
    value: object,
    path: str,
    *,
    page_locator: str,
    seen_sections: set[str],
) -> dict[str, object]:
    record = _section_object(value, path)
    allowed = {
        "locator",
        "page_locator",
        "heading_path",
        "title",
        "level",
        "occurrence",
        "ordinal",
        "parent_locator",
        "ownership",
        "exact_hash",
        "structural_hash",
        "semantic_hash",
        "occurrence_path",
    }
    required = allowed - {"structural_hash", "semantic_hash", "occurrence_path"}
    _section_fields(record, path, allowed, required)
    locator = _section_string(record["locator"], f"{path}.locator")
    if locator in seen_sections:
        raise SectionOwnershipError(
            f"{path}.locator",
            f"duplicates section locator {locator!r}",
        )
    seen_sections.add(locator)
    record_page = _section_string(
        record["page_locator"],
        f"{path}.page_locator",
    )
    if record_page != page_locator or not locator.startswith(f"{page_locator}#section/"):
        raise SectionOwnershipError(
            f"{path}.page_locator",
            "must match the containing page and section locator",
        )
    title = record["title"]
    if title is not None and not isinstance(title, str):
        raise SectionOwnershipError(f"{path}.title", "must be a string or null")
    level = _section_int(record["level"], f"{path}.level", minimum=0)
    if level > 6 or (title is None) != (level == 0):
        raise SectionOwnershipError(
            f"{path}.level",
            "must be 0 only for the synthetic preamble, otherwise 1 through 6",
        )
    heading_path = _section_string_array(
        record["heading_path"],
        f"{path}.heading_path",
    )
    if title is None and heading_path:
        raise SectionOwnershipError(
            f"{path}.heading_path",
            "must be empty for the synthetic preamble",
        )
    if title is not None and (not heading_path or heading_path[-1] != title):
        raise SectionOwnershipError(
            f"{path}.heading_path",
            "must end with the section title",
        )
    occurrence = _section_int(
        record["occurrence"],
        f"{path}.occurrence",
        minimum=1,
    )
    ordinal = _section_int(record["ordinal"], f"{path}.ordinal", minimum=0)
    parent = record["parent_locator"]
    if parent is not None:
        parent = _section_string(parent, f"{path}.parent_locator")
    try:
        ownership = SectionOwnership(record["ownership"])
    except (TypeError, ValueError) as exc:
        raise SectionOwnershipError(
            f"{path}.ownership",
            f"unsupported ownership {record['ownership']!r}",
        ) from exc
    exact_hash = _section_hash(record["exact_hash"], f"{path}.exact_hash")
    structural_hash = (
        _section_hash(record["structural_hash"], f"{path}.structural_hash")
        if "structural_hash" in record
        else None
    )
    semantic_hash = (
        _section_hash(record["semantic_hash"], f"{path}.semantic_hash")
        if "semantic_hash" in record
        else None
    )
    expected_presence = {
        SectionOwnership.GENERATED: (True, False),
        SectionOwnership.SEMANTIC: (False, True),
        SectionOwnership.MIXED: (True, True),
        SectionOwnership.UNKNOWN: (False, False),
    }[ownership]
    if (structural_hash is not None, semantic_hash is not None) != expected_presence:
        raise SectionOwnershipError(
            path,
            f"hash scopes do not match {ownership.value!r} ownership",
        )
    if ownership is SectionOwnership.GENERATED and structural_hash != exact_hash:
        raise SectionOwnershipError(
            f"{path}.structural_hash",
            "must equal exact_hash for generated ownership",
        )
    if ownership is SectionOwnership.SEMANTIC and semantic_hash != exact_hash:
        raise SectionOwnershipError(
            f"{path}.semantic_hash",
            "must equal exact_hash for semantic ownership",
        )
    result: dict[str, object] = {
        "locator": locator,
        "page_locator": page_locator,
        "heading_path": heading_path,
        "title": title,
        "level": level,
        "occurrence": occurrence,
        "ordinal": ordinal,
        "parent_locator": parent,
        "ownership": ownership.value,
        "exact_hash": exact_hash,
    }
    if "occurrence_path" in record:
        occurrence_path = _section_int_array(
            record["occurrence_path"],
            f"{path}.occurrence_path",
            minimum=1,
        )
        if title is not None and len(occurrence_path) != len(heading_path):
            raise SectionOwnershipError(
                f"{path}.occurrence_path",
                "must align with heading_path",
            )
        result["occurrence_path"] = occurrence_path
    elif title is not None:
        raise SectionOwnershipError(
            f"{path}.occurrence_path",
            "is required for a heading section",
        )
    occurrence_path = result.get("occurrence_path", [])
    if title is None:
        expected_locator = f"{page_locator}#section/@preamble"
        if (
            occurrence != 1
            or parent is not None
            or occurrence_path
            or "occurrence_path" in record
        ):
            raise SectionOwnershipError(
                path,
                "synthetic preamble coordinates are invalid",
            )
    else:
        assert isinstance(occurrence_path, list)
        if occurrence != occurrence_path[-1]:
            raise SectionOwnershipError(
                f"{path}.occurrence",
                "must equal the final occurrence_path component",
            )
        expected_locator = section_locator(
            page_locator,
            tuple(heading_path),
            tuple(occurrence_path),
        )
    if locator != expected_locator:
        raise SectionOwnershipError(
            f"{path}.locator",
            f"does not match canonical section coordinate {expected_locator!r}",
        )
    if structural_hash is not None:
        result["structural_hash"] = structural_hash
    if semantic_hash is not None:
        result["semantic_hash"] = semantic_hash
    return result


def _section_ordering_hash(
    page_locator: str,
    sections: Sequence[Mapping[str, object]],
) -> str:
    actual = [section for section in sections if section["title"] is not None]
    children: defaultdict[str, list[str]] = defaultdict(list)
    for section in actual:
        parent = section["parent_locator"]
        if isinstance(parent, str):
            children[parent].append(str(section["locator"]))
    return hash_json(
        {
            "domain": SECTION_ORDER_DOMAIN,
            "page_locator": page_locator,
            "sections": [
                {
                    "locator": section["locator"],
                    "ordinal": index,
                    "parent_locator": section["parent_locator"],
                    "child_locators": children[str(section["locator"])],
                }
                for index, section in enumerate(actual)
            ],
        }
    )


def _section_object(value: object, path: str) -> Mapping[str, object]:
    return require_mapping(
        value,
        error=SectionOwnershipError(path, "must be an object"),
    )


def _section_array(value: object, path: str) -> list[object]:
    return list(
        require_sequence(
            value,
            error=SectionOwnershipError(path, "must be an array"),
            reject_mapping=True,
        )
    )


def _section_fields(
    value: Mapping[str, object],
    path: str,
    allowed: set[str],
    required: set[str],
) -> None:
    return require_exact_fields(
        value,
        allowed=allowed,
        required=required,
        mapping_error=SectionOwnershipError(path, "must be an object"),
        missing_error=lambda fields: SectionOwnershipError(
            path, f"is missing field {fields[0]!r}"
        ),
        unknown_error=lambda fields: SectionOwnershipError(
            path, f"contains unknown field {fields[0]!r}"
        ),
        unknown_first=True,
    )


def _section_string(value: object, path: str) -> str:
    """Preserve raw persisted strings; callers apply their domain constraints."""

    return require_nonempty_text(
        value,
        error=SectionOwnershipError(path, "must be a non-empty string"),
        reject_control_characters=False,
    )


def _section_hash(value: object, path: str) -> str:
    return require_sha256(
        value,
        digest_error=SectionOwnershipError(path, "must be a sha256 content hash"),
    )


def _section_int(value: object, path: str, *, minimum: int) -> int:
    return require_int_at_least(
        value,
        minimum=minimum,
        error=SectionOwnershipError(path, f"must be an integer >= {minimum}"),
    )


def _section_string_array(value: object, path: str) -> list[str]:
    values = _section_array(value, path)
    if any(not isinstance(item, str) for item in values):
        raise SectionOwnershipError(path, "must contain only strings")
    return values  # type: ignore[return-value]


def _section_int_array(
    value: object,
    path: str,
    *,
    minimum: int,
) -> list[int]:
    values = _section_array(value, path)
    return [
        _section_int(item, f"{path}[{index}]", minimum=minimum)
        for index, item in enumerate(values)
    ]


def section_ownership_extension(
    pages: Iterable[PageSectionObservations],
) -> dict[str, object]:
    """Return the namespaced knowledge-index extension mapping."""

    return {
        SECTION_OWNERSHIP_EXTENSION_KEY: serialize_section_ownership(pages),
    }


def merge_semantic_markdown(
    existing: str,
    generated: str,
    table_headings: tuple[str, ...],
    *,
    old_description: str | None = None,
    old_table_descriptions: dict[str, dict[str, str]] | None = None,
) -> SemanticMergeResult:
    """Preserve historical semantic fields in regenerated wiki Markdown."""

    merged = normalize_markdown(generated)
    preserved = 0
    existing_description = section_body(existing, "Description")
    generated_description = section_body(generated, "Description")
    if existing_description is not None and should_preserve_semantic_value(
        existing_description,
        generated_description,
        old_description,
    ):
        merged = replace_section_body(
            merged,
            "Description",
            existing_description,
        )
        preserved += 1

    for heading in table_headings:
        descriptions = table_description_cells(existing, heading)
        merged, table_preserved = preserve_table_description_cells(
            merged,
            heading,
            descriptions,
            (old_table_descriptions or {}).get(heading),
        )
        preserved += table_preserved
    return SemanticMergeResult(merged, preserved)


def merge_entity_semantics(
    existing: str,
    generated: str,
    old_semantics: Mapping[str, object] | None = None,
) -> SemanticMergeResult:
    """Apply the current entity Description/Attributes/Methods policy."""

    semantics = old_semantics or {}
    attributes = semantics.get("attributes", {})
    methods = semantics.get("methods", {})
    description = semantics.get("description")
    return merge_semantic_markdown(
        existing,
        generated,
        ("Attributes", "Methods"),
        old_description=description if isinstance(description, str) else None,
        old_table_descriptions={
            "Attributes": dict(attributes) if isinstance(attributes, Mapping) else {},
            "Methods": dict(methods) if isinstance(methods, Mapping) else {},
        },
    )


def merge_module_semantics(
    existing: str,
    generated: str,
    old_semantics: Mapping[str, object] | None = None,
) -> SemanticMergeResult:
    """Apply the current module Description/Classes/Functions policy."""

    semantics = old_semantics or {}
    classes = semantics.get("classes", {})
    functions = semantics.get("functions", {})
    description = semantics.get("description")
    return merge_semantic_markdown(
        existing,
        generated,
        ("Classes", "Functions"),
        old_description=description if isinstance(description, str) else None,
        old_table_descriptions={
            "Classes": dict(classes) if isinstance(classes, Mapping) else {},
            "Functions": dict(functions) if isinstance(functions, Mapping) else {},
        },
    )


def replace_generated_section(
    existing: str,
    generated: str,
    heading: str,
) -> str:
    """Replace one current generated section without touching other bytes."""

    if section_body(existing, heading) is None:
        return existing
    generated_body = section_body(generated, heading)
    if generated_body is None:
        return existing
    updated = replace_section_body(existing, heading, generated_body)
    if existing.endswith("\n") and not updated.endswith("\n"):
        updated += "\n"
    return updated


__all__ = [
    "PageSectionObservations",
    "SectionObservation",
    "SectionOwnership",
    "SemanticMergeResult",
    "classify_section_ownership",
    "collect_section_observations",
    "merge_entity_semantics",
    "merge_module_semantics",
    "merge_semantic_markdown",
    "observe_page_sections",
    "replace_generated_section",
    "section_observations",
    "section_ownership_extension",
    "serialize_section_ownership",
]
