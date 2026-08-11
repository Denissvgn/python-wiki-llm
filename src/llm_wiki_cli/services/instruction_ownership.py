"""Machine-checkable ownership and routing for generated agent instructions.

This inventory is a fail-closed removal gate.  Detailed generated prose may be
moved only after its canonical destination is both present in the distribution
payload and explicitly reachable in the rendered target/profile being changed.
"""

from __future__ import annotations

import fnmatch
import posixpath
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath

from .schema import SCHEMA_FILENAMES, SchemaRenderProfile
from .skills import skills_install_dir

try:  # Python 3.11+
    import tomllib  # type: ignore[reportMissingImports]
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    try:
        import tomli as tomllib  # type: ignore[reportMissingImports]
    except ModuleNotFoundError:  # pragma: no cover - incomplete ad-hoc install
        tomllib = None  # type: ignore[assignment]


class InstructionOwner(str, Enum):
    """Canonical owner classes for generated instruction content."""

    KERNEL = "kernel"
    KNOWLEDGE_CONSUMER = "knowledge_consumer"
    MANAGED_REFERENCE_TOPIC = "managed_reference_topic"
    WORKFLOW_SKILL = "workflow_skill"
    DETERMINISTIC_CLI_LINT = "deterministic_cli_lint"
    REMOVED_DUPLICATE = "removed_duplicate"


class SectionCondition(str, Enum):
    """Configuration switch controlling a current generated section."""

    ALWAYS = "always"
    QUALITY_HINTS = "quality_hints"
    ISSUE_REPORTING = "issue_reporting"


class InstructionOrigin(str, Enum):
    """Renderer fragment that currently carries a correctness rule."""

    GENERATED_BODY = "generated_body"
    SYNC_INSTRUCTIONS = "sync_instructions"


class InstructionRouteKind(str, Enum):
    """How a rendered instruction reaches one packaged destination."""

    INSTALLED_PATH = "installed_path"
    WORKFLOW_SKILL = "workflow_skill"
    LITERAL = "literal"


class InboundRouteKind(str, Enum):
    """Supported source-level route shapes into managed references."""

    MARKDOWN_LINK = "markdown_link"
    HEADING_REFERENCE = "heading_reference"
    INSTALLED_FILE_ROUTE = "installed_file_route"
    REFERENCE_ROOT = "reference_root"


_ALL_PROFILES = tuple(SchemaRenderProfile)
_COMPACT_ONLY = (SchemaRenderProfile.COMPACT,)
_EXPANDED_ONLY = (SchemaRenderProfile.EXPANDED_INLINE,)


@dataclass(frozen=True)
class InstructionDestination:
    """Package-relative destination for content leaving generated prose."""

    path: str
    heading: str | None = None
    anchor: str | None = None


@dataclass(frozen=True)
class InstructionRoute:
    """Route that must occur in a particular rendered section."""

    destination_path: str
    source_heading: str
    kind: InstructionRouteKind
    literal: str | None = None
    profiles: tuple[SchemaRenderProfile, ...] = tuple(SchemaRenderProfile)
    agent_targets: tuple[str, ...] = tuple(SCHEMA_FILENAMES)


@dataclass(frozen=True)
class GeneratedSectionCoverage:
    """Single-owner record for one current generated section."""

    section: str
    source_heading: str | None
    owner: InstructionOwner
    destinations: tuple[InstructionDestination, ...] = ()
    routes: tuple[InstructionRoute, ...] = ()
    retained_kernel: bool = False
    condition: SectionCondition = SectionCondition.ALWAYS
    profiles: tuple[SchemaRenderProfile, ...] = _ALL_PROFILES


@dataclass(frozen=True)
class CorrectnessClauseCoverage:
    """Current correctness rule protected by a canonical ownership decision."""

    name: str
    source_section: str
    source_text: str
    owner: InstructionOwner
    destination: InstructionDestination
    route: InstructionRoute
    origin: InstructionOrigin = InstructionOrigin.GENERATED_BODY
    destination_text: str | None = None
    always_inline: bool = False
    profiles: tuple[SchemaRenderProfile, ...] = tuple(SchemaRenderProfile)
    agent_targets: tuple[str, ...] = tuple(SCHEMA_FILENAMES)


@dataclass(frozen=True)
class RepositoryHygieneCoverage:
    """Always-inline ownership reservation for repository safeguards."""

    name: str
    contract: str
    owner: InstructionOwner = InstructionOwner.KERNEL
    always_inline: bool = True
    profiles: tuple[SchemaRenderProfile, ...] = tuple(SchemaRenderProfile)
    agent_targets: tuple[str, ...] = tuple(SCHEMA_FILENAMES)


@dataclass(frozen=True)
class ManagedReferenceInboundRoute:
    """One active source route into a managed reference topic."""

    source_path: str
    source_text: str
    kind: InboundRouteKind
    destination_path: str
    destination_heading: str
    destination_anchor: str
    markdown_target: str | None = None


@dataclass(frozen=True)
class MarkdownLink:
    """One parsed local Markdown link."""

    label: str
    target_path: str
    anchor: str | None


@dataclass(frozen=True)
class MarkdownHeading:
    """One parsed Markdown heading and its actual local anchor."""

    title: str
    anchor: str


@dataclass(frozen=True)
class DiscoveredInboundRoute:
    """Source-derived route identity used to audit the declared inventory."""

    source_path: str
    kind: InboundRouteKind
    destination_path: str
    destination_heading: str
    destination_anchor: str


_REFERENCE_SKILL = "skills/wiki-reference/SKILL.md"
_REFERENCE_COMPATIBILITY = "skills/wiki-reference/reference.md"
_REFERENCE_TOPICS = "skills/wiki-reference/references"
_SCHEMA_SOURCE = "services/schema.py"


_TOPIC_HEADINGS: dict[str, tuple[str, str]] = {
    "maintenance": ("Maintenance and validation", "maintenance-and-validation"),
    "surfaces-naming": (
        "Canonical surfaces and naming",
        "canonical-surfaces-and-naming",
    ),
    "repository-handoff": ("Repository handoff", "repository-handoff"),
    "knowledge-consumption": (
        "Qualified knowledge consumption",
        "qualified-knowledge-consumption",
    ),
    "context-query": ("Context and query selection", "context-and-query-selection"),
    "governance": ("Durable knowledge governance", "durable-knowledge-governance"),
    "extractors-dependencies": (
        "Extractors and dependencies",
        "extractors-and-dependencies",
    ),
    "publishing": ("Publishing projections", "publishing-projections"),
    "resources-context": (
        "Resource-aware execution",
        "resource-aware-execution",
    ),
}


def _topic(name: str) -> InstructionDestination:
    heading, anchor = _TOPIC_HEADINGS[name]
    return InstructionDestination(
        f"{_REFERENCE_TOPICS}/{name}.md",
        heading,
        anchor,
    )


def _skill(skill_id: str) -> InstructionDestination:
    return InstructionDestination(f"skills/{skill_id}/SKILL.md", skill_id)


def _installed_route(
    source_heading: str,
    destination: InstructionDestination,
    *,
    profiles: tuple[SchemaRenderProfile, ...] = _ALL_PROFILES,
) -> InstructionRoute:
    return InstructionRoute(
        destination.path,
        source_heading,
        InstructionRouteKind.INSTALLED_PATH,
        profiles=profiles,
    )


def _workflow_route(
    source_heading: str,
    skill_id: str,
    *,
    profiles: tuple[SchemaRenderProfile, ...] = _ALL_PROFILES,
) -> InstructionRoute:
    return InstructionRoute(
        f"skills/{skill_id}/SKILL.md",
        source_heading,
        InstructionRouteKind.WORKFLOW_SKILL,
        profiles=profiles,
    )


def _topic_route(
    source_heading: str,
    topic: str,
    *,
    profiles: tuple[SchemaRenderProfile, ...] = _ALL_PROFILES,
) -> InstructionRoute:
    return _installed_route(source_heading, _topic(topic), profiles=profiles)


_BEFORE = "## Before you start"
_HANDOFF = "## Repository delivery preflight"
_KNOWLEDGE = "## Native knowledge preflight"
_DEEP_REFERENCE = "## Deep reference (read on demand)"
_RESOURCES = "## Resource-aware execution"
_SURFACES = "## Canonical wiki surfaces"
_USER_DOCS = "## User docs and usage examples"
_CHANGE_CODE = "## When you change code"
_NAMING = "## Wiki file naming rules"
_QUALITY = "## Quality checks"
_ISSUES = "## Report llm-wiki tool issues"
_FORMATTING = "## Formatting rules"
_AGENT_QUALITY = "## Agent quality guidelines"
_SYNC = "## How to sync the wiki in this agent session"
_INCREMENTAL = "## Using `llm-wiki sync` for incremental updates"
_LARGE_CODEBASES = "## Large codebases"
_COMPACT_EVIDENCE = "## Select evidence first"
_COMPACT_AUTHORITY = "## Authority and handoff"
_REPOSITORY_HYGIENE = "## Repository content hygiene"
_COMPACT_ROUTES = "## Managed routes and completion"


_USER_DOCS_SKILLS = (
    "wiki-bootstrap",
    "wiki-sync",
    "user-docs-author",
    "usage-examples",
    "publish-docs",
)


def _profiled_topic_routes(
    expanded_heading: str,
    compact_heading: str,
    topic: str,
) -> tuple[InstructionRoute, ...]:
    return (
        _topic_route(expanded_heading, topic, profiles=_EXPANDED_ONLY),
        _topic_route(compact_heading, topic, profiles=_COMPACT_ONLY),
    )


def _profiled_workflow_routes(
    expanded_heading: str,
    compact_heading: str,
    skill_id: str,
) -> tuple[InstructionRoute, ...]:
    return (
        _workflow_route(expanded_heading, skill_id, profiles=_EXPANDED_ONLY),
        _workflow_route(compact_heading, skill_id, profiles=_COMPACT_ONLY),
    )


GENERATED_SECTION_COVERAGE: tuple[GeneratedSectionCoverage, ...] = (
    GeneratedSectionCoverage(
        "Preamble/markers",
        None,
        InstructionOwner.KERNEL,
        retained_kernel=True,
    ),
    GeneratedSectionCoverage(
        "Compact evidence selection",
        _COMPACT_EVIDENCE,
        InstructionOwner.KNOWLEDGE_CONSUMER,
        retained_kernel=True,
        profiles=_COMPACT_ONLY,
    ),
    GeneratedSectionCoverage(
        "Compact authority and handoff",
        _COMPACT_AUTHORITY,
        InstructionOwner.KERNEL,
        (_topic("repository-handoff"),),
        (
            _topic_route(
                _COMPACT_AUTHORITY,
                "repository-handoff",
                profiles=_COMPACT_ONLY,
            ),
        ),
        retained_kernel=True,
        profiles=_COMPACT_ONLY,
    ),
    GeneratedSectionCoverage(
        "Compact repository content hygiene",
        _REPOSITORY_HYGIENE,
        InstructionOwner.KERNEL,
        retained_kernel=True,
        profiles=_COMPACT_ONLY,
    ),
    GeneratedSectionCoverage(
        "Compact managed routes and completion",
        _COMPACT_ROUTES,
        InstructionOwner.KERNEL,
        tuple(_topic(topic) for topic in _TOPIC_HEADINGS if topic != "repository-handoff")
        + tuple(_skill(skill_id) for skill_id in _USER_DOCS_SKILLS),
        tuple(
            _topic_route(_COMPACT_ROUTES, topic, profiles=_COMPACT_ONLY)
            for topic in _TOPIC_HEADINGS
            if topic != "repository-handoff"
        )
        + tuple(
            _workflow_route(
                _COMPACT_ROUTES,
                skill_id,
                profiles=_COMPACT_ONLY,
            )
            for skill_id in _USER_DOCS_SKILLS
        ),
        retained_kernel=True,
        profiles=_COMPACT_ONLY,
    ),
    GeneratedSectionCoverage(
        "Before you start",
        _BEFORE,
        InstructionOwner.KNOWLEDGE_CONSUMER,
        (_topic("context-query"),),
        _profiled_topic_routes(_BEFORE, _COMPACT_ROUTES, "context-query"),
        retained_kernel=True,
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Repository delivery preflight",
        _HANDOFF,
        InstructionOwner.KERNEL,
        (_topic("repository-handoff"),),
        _profiled_topic_routes(
            _HANDOFF,
            _COMPACT_AUTHORITY,
            "repository-handoff",
        ),
        retained_kernel=True,
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Native knowledge preflight",
        _KNOWLEDGE,
        InstructionOwner.KNOWLEDGE_CONSUMER,
        (_topic("knowledge-consumption"),),
        _profiled_topic_routes(
            _KNOWLEDGE,
            _COMPACT_ROUTES,
            "knowledge-consumption",
        ),
        retained_kernel=True,
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Expanded repository content hygiene",
        _REPOSITORY_HYGIENE,
        InstructionOwner.KERNEL,
        retained_kernel=True,
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Deep reference",
        _DEEP_REFERENCE,
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        (
            _topic("extractors-dependencies"),
            _topic("publishing"),
            _topic("context-query"),
        ),
        (
            *_profiled_topic_routes(
                _DEEP_REFERENCE,
                _COMPACT_ROUTES,
                "extractors-dependencies",
            ),
            *_profiled_topic_routes(
                _DEEP_REFERENCE,
                _COMPACT_ROUTES,
                "publishing",
            ),
            *_profiled_topic_routes(
                _DEEP_REFERENCE,
                _COMPACT_ROUTES,
                "context-query",
            ),
        ),
        retained_kernel=True,
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Resource-aware execution",
        _RESOURCES,
        InstructionOwner.KERNEL,
        (_topic("resources-context"),),
        _profiled_topic_routes(
            _RESOURCES,
            _COMPACT_ROUTES,
            "resources-context",
        ),
        retained_kernel=True,
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Canonical wiki surfaces",
        _SURFACES,
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        (_topic("surfaces-naming"), _topic("publishing")),
        (
            *_profiled_topic_routes(
                _SURFACES,
                _COMPACT_ROUTES,
                "surfaces-naming",
            ),
            *_profiled_topic_routes(
                _SURFACES,
                _COMPACT_ROUTES,
                "publishing",
            ),
        ),
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "User docs and usage examples",
        _USER_DOCS,
        InstructionOwner.WORKFLOW_SKILL,
        tuple(_skill(skill_id) for skill_id in _USER_DOCS_SKILLS),
        tuple(
            route
            for skill_id in _USER_DOCS_SKILLS
            for route in _profiled_workflow_routes(
                _USER_DOCS,
                _COMPACT_ROUTES,
                skill_id,
            )
        ),
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "When you change code",
        _CHANGE_CODE,
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        (_topic("maintenance"),),
        _profiled_topic_routes(
            _CHANGE_CODE,
            _COMPACT_ROUTES,
            "maintenance",
        ),
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Wiki file naming rules",
        _NAMING,
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        (_topic("surfaces-naming"),),
        _profiled_topic_routes(
            _NAMING,
            _COMPACT_ROUTES,
            "surfaces-naming",
        ),
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Quality checks",
        _QUALITY,
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        (_topic("maintenance"), _topic("extractors-dependencies")),
        (
            *_profiled_topic_routes(
                _QUALITY,
                _COMPACT_ROUTES,
                "maintenance",
            ),
            *_profiled_topic_routes(
                _QUALITY,
                _COMPACT_ROUTES,
                "extractors-dependencies",
            ),
        ),
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Tool issue reporting",
        _ISSUES,
        InstructionOwner.KERNEL,
        retained_kernel=True,
        condition=SectionCondition.ISSUE_REPORTING,
    ),
    GeneratedSectionCoverage(
        "Formatting rules",
        _FORMATTING,
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        (_topic("surfaces-naming"),),
        _profiled_topic_routes(
            _FORMATTING,
            _COMPACT_ROUTES,
            "surfaces-naming",
        ),
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Agent quality guidelines",
        _AGENT_QUALITY,
        InstructionOwner.KERNEL,
        retained_kernel=True,
        condition=SectionCondition.QUALITY_HINTS,
    ),
    GeneratedSectionCoverage(
        "How to sync in this session",
        _SYNC,
        InstructionOwner.REMOVED_DUPLICATE,
        (_topic("maintenance"),),
        _profiled_topic_routes(_SYNC, _COMPACT_ROUTES, "maintenance"),
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Incremental sync details",
        _INCREMENTAL,
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        (_topic("maintenance"),),
        _profiled_topic_routes(
            _INCREMENTAL,
            _COMPACT_ROUTES,
            "maintenance",
        ),
        profiles=_EXPANDED_ONLY,
    ),
    GeneratedSectionCoverage(
        "Large codebases",
        _LARGE_CODEBASES,
        InstructionOwner.REMOVED_DUPLICATE,
        (_topic("context-query"),),
        _profiled_topic_routes(
            _LARGE_CODEBASES,
            _COMPACT_ROUTES,
            "context-query",
        ),
        profiles=_EXPANDED_ONLY,
    ),
)


REPOSITORY_HYGIENE_COVERAGE: tuple[RepositoryHygieneCoverage, ...] = (
    RepositoryHygieneCoverage(
        "internal_document_publication",
        "Internal documentation, including ADRs, plans, backlogs, reports, and "
        "implementation notes, must never be published in the repository. Create "
        "it only at an exact path proven ignored, and never stage or force-add it.",
    ),
    RepositoryHygieneCoverage(
        "public_document_content",
        "Public documentation, including README files and published documentation, "
        "wiki, and site surfaces, must never mention internal development phases "
        "or tests.",
    ),
    RepositoryHygieneCoverage(
        "code_and_test_provenance",
        "Source code, comments, docstrings, identifiers, checked-in fixtures, and "
        "test files must never contain actual epic, milestone, or phase names, "
        "backlog or task identifiers, or internal planning provenance.",
    ),
)


_MAINTENANCE = _topic("maintenance")
_SURFACES_NAMING = _topic("surfaces-naming")
_PUBLISHING = _topic("publishing")
_EXTRACTORS = _topic("extractors-dependencies")


def _correctness_route(
    _source_heading: str,
    destination: InstructionDestination,
) -> InstructionRoute:
    return _installed_route(
        _COMPACT_ROUTES,
        destination,
        profiles=_COMPACT_ONLY,
    )


CORRECTNESS_CLAUSE_COVERAGE: tuple[CorrectnessClauseCoverage, ...] = (
    CorrectnessClauseCoverage(
        "relevant_code_change_activation",
        "How to sync in this session",
        "adds, removes, or modifies a class, function, module, or cross-module flow, run the full sync-then-lint workflow",
        InstructionOwner.KERNEL,
        _MAINTENANCE,
        _correctness_route(_SYNC, _MAINTENANCE),
        InstructionOrigin.SYNC_INSTRUCTIONS,
        always_inline=True,
    ),
    CorrectnessClauseCoverage(
        "stale_update_guard",
        "How to sync in this session",
        "**Never skip the update** — a stale wiki defeats the purpose of the system.",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _MAINTENANCE,
        _correctness_route(_SYNC, _MAINTENANCE),
        InstructionOrigin.SYNC_INSTRUCTIONS,
    ),
    CorrectnessClauseCoverage(
        "manifestless_sync_seeding",
        "Incremental sync details",
        "**seed a baseline manifest** from the current source state without modifying pages",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _MAINTENANCE,
        _correctness_route(_INCREMENTAL, _MAINTENANCE),
        InstructionOrigin.SYNC_INSTRUCTIONS,
    ),
    CorrectnessClauseCoverage(
        "final_owning_sync_condition",
        "Incremental sync details",
        "Skip the second sync only when no canonical Markdown changed.",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _MAINTENANCE,
        _correctness_route(_INCREMENTAL, _MAINTENANCE),
        InstructionOrigin.SYNC_INSTRUCTIONS,
    ),
    CorrectnessClauseCoverage(
        "generated_semantic_ownership",
        "User docs and usage examples",
        "Edit semantic prose only; generated blocks are CLI-owned.",
        InstructionOwner.KERNEL,
        _SURFACES_NAMING,
        _correctness_route(_USER_DOCS, _SURFACES_NAMING),
        always_inline=True,
    ),
    CorrectnessClauseCoverage(
        "source_read_only",
        "User docs and usage examples",
        "Keep source targets read-only unless the user explicitly asks for source edits.",
        InstructionOwner.KERNEL,
        _MAINTENANCE,
        _correctness_route(_USER_DOCS, _MAINTENANCE),
        always_inline=True,
    ),
    CorrectnessClauseCoverage(
        "manifest_repair_recheck",
        "When you change code",
        "If sync repairs only the manifest (its stored hashes were invalid, and no pages were modified), run the same sync command again before linting.",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _MAINTENANCE,
        _correctness_route(_CHANGE_CODE, _MAINTENANCE),
    ),
    CorrectnessClauseCoverage(
        "external_source_argument_continuity",
        "When you change code",
        "pass the same external `--src-dir` with `--allow-external-src` to `sync`, `lint`, and `ci-check`",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _MAINTENANCE,
        _correctness_route(_CHANGE_CODE, _MAINTENANCE),
    ),
    CorrectnessClauseCoverage(
        "semantic_reanchor_order",
        "When you change code",
        "After the last canonical Markdown edit, run `llm-wiki sync",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _MAINTENANCE,
        _correctness_route(_CHANGE_CODE, _MAINTENANCE),
    ),
    CorrectnessClauseCoverage(
        "review_receipt_integrity",
        "When you change code",
        "Do not fabricate replacement human reviews or receipts.",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _MAINTENANCE,
        _correctness_route(_CHANGE_CODE, _MAINTENANCE),
    ),
    CorrectnessClauseCoverage(
        "guide_prose_ownership",
        "Canonical wiki surfaces",
        "`sync` does not generate or overwrite guide prose.",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _SURFACES_NAMING,
        _correctness_route(_SURFACES, _SURFACES_NAMING),
    ),
    CorrectnessClauseCoverage(
        "derived_site_ownership",
        "Canonical wiki surfaces",
        "not as an editable source of truth",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _PUBLISHING,
        _correctness_route(_SURFACES, _PUBLISHING),
        destination_text="Derived Site output is never the editable source of truth.",
    ),
    CorrectnessClauseCoverage(
        "infrastructure_semantic_surface",
        "When you change code",
        "Infrastructure `## Notes` is the only supported semantic section",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _SURFACES_NAMING,
        _correctness_route(_CHANGE_CODE, _SURFACES_NAMING),
        destination_text=(
            "Infrastructure `## Notes` is the only supported semantic section"
        ),
    ),
    CorrectnessClauseCoverage(
        "generated_diagram_ownership",
        "User docs and usage examples",
        "Do not edit generated Mermaid diagrams by hand.",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _SURFACES_NAMING,
        _correctness_route(_USER_DOCS, _SURFACES_NAMING),
        destination_text="Do not edit generated Mermaid diagrams by hand.",
    ),
    CorrectnessClauseCoverage(
        "diagram_plugin_boundary",
        "User docs and usage examples",
        "cannot inject arbitrary Markdown, labels, hrefs, or raw Mermaid content",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _SURFACES_NAMING,
        _correctness_route(_USER_DOCS, _SURFACES_NAMING),
        destination_text=(
            "cannot inject arbitrary Markdown, labels, hrefs, or raw Mermaid content"
        ),
    ),
    CorrectnessClauseCoverage(
        "entity_collision_naming",
        "Wiki file naming rules",
        "prefix with the disambiguated module page stem",
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        _SURFACES_NAMING,
        _correctness_route(_NAMING, _SURFACES_NAMING),
    ),
    CorrectnessClauseCoverage(
        "module_collision_naming",
        "Wiki file naming rules",
        "parent directory components are prepended with underscores until unique",
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        _SURFACES_NAMING,
        _correctness_route(_NAMING, _SURFACES_NAMING),
    ),
    CorrectnessClauseCoverage(
        "infrastructure_page_naming",
        "Wiki file naming rules",
        "replace `/` and `.` with `_`",
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        _SURFACES_NAMING,
        _correctness_route(_NAMING, _SURFACES_NAMING),
    ),
    CorrectnessClauseCoverage(
        "guide_discoverability",
        "Wiki file naming rules",
        "Keep guide pages linked from `index.md` or another canonical page",
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        _SURFACES_NAMING,
        _correctness_route(_NAMING, _SURFACES_NAMING),
    ),
    CorrectnessClauseCoverage(
        "generated_flow_names",
        "Wiki file naming rules",
        "Do not rename them.",
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        _SURFACES_NAMING,
        _correctness_route(_NAMING, _SURFACES_NAMING),
    ),
    CorrectnessClauseCoverage(
        "strict_validation_after_reanchor",
        "Quality checks",
        "Strict validation follows the final owning sync after any semantic Markdown edit.",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _MAINTENANCE,
        _correctness_route(_QUALITY, _MAINTENANCE),
    ),
    CorrectnessClauseCoverage(
        "unknown_contract_values",
        "When you change code",
        "never treat an unknown contract field as a confirmed value",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _MAINTENANCE,
        _correctness_route(_CHANGE_CODE, _MAINTENANCE),
    ),
    CorrectnessClauseCoverage(
        "unsupported_source_disclosure",
        "Quality checks",
        "do not claim those files were documented",
        InstructionOwner.MANAGED_REFERENCE_TOPIC,
        _EXTRACTORS,
        _correctness_route(_QUALITY, _EXTRACTORS),
        destination_text=(
            "Analyzer absence, truncation, or unsupported syntax is an unknown surface"
        ),
    ),
    CorrectnessClauseCoverage(
        "lint_clean_handoff",
        "Quality checks",
        "Never leave the wiki in a state where lint reports errors.",
        InstructionOwner.KERNEL,
        _MAINTENANCE,
        _correctness_route(_QUALITY, _MAINTENANCE),
        always_inline=True,
    ),
    CorrectnessClauseCoverage(
        "entity_required_structure",
        "Formatting rules",
        "Entity pages must have: Location, Bases, Module link, Attributes table, Methods table, Relationships.",
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        _SURFACES_NAMING,
        _correctness_route(_FORMATTING, _SURFACES_NAMING),
    ),
    CorrectnessClauseCoverage(
        "module_required_structure",
        "Formatting rules",
        "Module pages must have: Path, Imports table, Classes summary, Functions table.",
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        _SURFACES_NAMING,
        _correctness_route(_FORMATTING, _SURFACES_NAMING),
    ),
    CorrectnessClauseCoverage(
        "flow_semantic_surface",
        "Formatting rules",
        "fill in the `## Behavior` section",
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        _SURFACES_NAMING,
        _correctness_route(_FORMATTING, _SURFACES_NAMING),
    ),
    CorrectnessClauseCoverage(
        "dependency_notes_ownership",
        "Formatting rules",
        "Dependency architecture pages must keep any human-authored `## Notes` section aligned",
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        _SURFACES_NAMING,
        _correctness_route(_FORMATTING, _SURFACES_NAMING),
    ),
    CorrectnessClauseCoverage(
        "relative_internal_links",
        "Formatting rules",
        "Use relative markdown links between pages",
        InstructionOwner.DETERMINISTIC_CLI_LINT,
        _SURFACES_NAMING,
        _correctness_route(_FORMATTING, _SURFACES_NAMING),
    ),
)


def _managed_topic_route(
    source_path: str,
    source_text: str,
    topic: str,
    *,
    kind: InboundRouteKind = InboundRouteKind.INSTALLED_FILE_ROUTE,
    markdown_target: str | None = None,
) -> ManagedReferenceInboundRoute:
    destination = _topic(topic)
    assert destination.heading is not None
    assert destination.anchor is not None
    return ManagedReferenceInboundRoute(
        source_path,
        source_text,
        kind,
        destination.path,
        destination.heading,
        destination.anchor,
        markdown_target,
    )


_ROUTER_TOPICS = tuple(_TOPIC_HEADINGS)
_HANDOFF_SKILLS = (
    "usage-examples",
    "onboarding-guide",
    "wiki-sync",
    "infra-review",
    "dep-audit",
    "wiki-bootstrap",
    "user-docs-author",
    "doc-review",
)
_KNOWLEDGE_CONSUMERS = (
    "agent-docs",
    "dep-audit",
    "doc-hub",
    "doc-review",
    "impact-analysis",
    "infra-review",
    "onboarding-guide",
    "publish-docs",
    "usage-examples",
    "user-docs-author",
    "wiki-bootstrap",
    "wiki-semantic-enhance",
    "wiki-sync",
)
_INSTALLED_HANDOFF_SPAN = (
    "Read the separately managed topic at "
    "`.claude/skills/wiki-reference/references/repository-handoff.md` for Claude "
    "or `.llm-wiki/skills/wiki-reference/references/repository-handoff.md` for "
    "other configured agents."
)
_INSTALLED_KNOWLEDGE_SPAN = (
    "Read the full separately managed contract at "
    "`.claude/skills/wiki-reference/references/knowledge-consumption.md` for "
    "Claude or "
    "`.llm-wiki/skills/wiki-reference/references/knowledge-consumption.md` for "
    "other configured agents."
)


MANAGED_REFERENCE_INBOUND_ROUTES: tuple[ManagedReferenceInboundRoute, ...] = (
    *(
        _managed_topic_route(
            _REFERENCE_SKILL,
            f"](references/{topic}.md)",
            topic,
            kind=InboundRouteKind.MARKDOWN_LINK,
            markdown_target=f"references/{topic}.md",
        )
        for topic in _ROUTER_TOPICS
    ),
    _managed_topic_route(
        _SCHEMA_SOURCE,
        "`{reference_root}/context-query.md`",
        "context-query",
    ),
    _managed_topic_route(
        _SCHEMA_SOURCE,
        "`{reference_root}/extractors-dependencies.md`",
        "extractors-dependencies",
    ),
    _managed_topic_route(
        _SCHEMA_SOURCE,
        "`{reference_root}/maintenance.md`",
        "maintenance",
    ),
    _managed_topic_route(
        _SCHEMA_SOURCE,
        "`{reference_root}/repository-handoff.md`",
        "repository-handoff",
    ),
    _managed_topic_route(
        _SCHEMA_SOURCE,
        "`{reference_root}/knowledge-consumption.md`",
        "knowledge-consumption",
    ),
    _managed_topic_route(
        _SCHEMA_SOURCE,
        "`{reference_root}/governance.md`",
        "governance",
    ),
    _managed_topic_route(
        _SCHEMA_SOURCE,
        "`{reference_root}/publishing.md`",
        "publishing",
    ),
    _managed_topic_route(
        _SCHEMA_SOURCE,
        "`{reference_root}/resources-context.md`",
        "resources-context",
    ),
    _managed_topic_route(
        _SCHEMA_SOURCE,
        "`{reference_root}/surfaces-naming.md`",
        "surfaces-naming",
    ),
    *(
        _managed_topic_route(
            f"skills/{skill_id}/SKILL.md",
            _INSTALLED_HANDOFF_SPAN,
            "repository-handoff",
        )
        for skill_id in _HANDOFF_SKILLS
    ),
    *(
        _managed_topic_route(
            f"skills/{skill_id}/SKILL.md",
            _INSTALLED_KNOWLEDGE_SPAN,
            "knowledge-consumption",
        )
        for skill_id in _KNOWLEDGE_CONSUMERS
    ),
)


def normalize_instruction_text(value: str) -> str:
    """Collapse formatting whitespace for stable sentence-level checks."""

    return " ".join(value.split())


def markdown_anchor(heading: str) -> str:
    """Return the GitHub-style base anchor for a Markdown heading."""

    normalized = re.sub(r"[^\w\- ]", "", heading.lower(), flags=re.UNICODE)
    return re.sub(r" +", "-", normalized.strip())


def markdown_headings(content: str) -> tuple[MarkdownHeading, ...]:
    """Parse headings and their duplicate-aware local anchors."""

    headings: list[MarkdownHeading] = []
    seen: dict[str, int] = {}
    for line in content.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match is None:
            continue
        title = match.group(1).strip()
        base = markdown_anchor(title)
        duplicate = seen.get(base, 0)
        seen[base] = duplicate + 1
        anchor = base if duplicate == 0 else f"{base}-{duplicate}"
        headings.append(MarkdownHeading(title, anchor))
    return tuple(headings)


def markdown_links(content: str) -> tuple[MarkdownLink, ...]:
    """Parse ordinary local Markdown links without treating images as routes."""

    links: list[MarkdownLink] = []
    for match in re.finditer(r"(?<!!)\[([^]\n]+)\]\(([^)\s]+)\)", content):
        raw_target = match.group(2)
        target_path, separator, anchor = raw_target.partition("#")
        links.append(
            MarkdownLink(
                match.group(1),
                target_path,
                anchor if separator else None,
            )
        )
    return tuple(links)


def _destination_heading_lookup(
    package_root: Path,
    destination_path: str,
) -> tuple[MarkdownHeading | None, dict[str, str]]:
    path = package_root / destination_path
    if not path.is_file():
        return None, {}
    headings = markdown_headings(path.read_text(encoding="utf-8"))
    if not headings:
        return None, {}
    return headings[0], {heading.anchor: heading.title for heading in headings}


def _resolved_package_link(source_path: str, target_path: str) -> str:
    source_parent = PurePosixPath(source_path).parent.as_posix()
    return posixpath.normpath(posixpath.join(source_parent, target_path))


_INSTALLED_REFERENCE_PATH = re.compile(
    r"(?:\{skills_dir\}|\.claude/skills|\.llm-wiki/skills)/"
    r"(?P<relative>wiki-reference/(?:reference\.md|references/[a-z0-9-]+\.md))"
)
_REFERENCE_ROOT_TOPIC_PATH = re.compile(
    r"\{reference_root\}/(?P<topic>[a-z0-9-]+\.md)"
)


def _active_reference_sources(package_root: Path) -> tuple[Path, ...]:
    source_paths = [package_root / _SCHEMA_SOURCE]
    source_paths.extend(sorted((package_root / "skills").rglob("*.md")))
    return tuple(
        path
        for path in source_paths
        if path.is_file()
        and not (
            path.relative_to(package_root)
            .as_posix()
            .startswith(f"{_REFERENCE_TOPICS}/")
            or path.relative_to(package_root).as_posix() == _REFERENCE_COMPATIBILITY
        )
    )


def discover_managed_reference_inbound_routes(
    package_root: Path,
) -> tuple[DiscoveredInboundRoute, ...]:
    """Discover direct topic and forbidden compatibility routes from syntax.

    Topic-internal and compatibility-index links are excluded. Active schema,
    workflow, and router routes remain in scope. Alternative Claude and generic
    installed paths collapse to one source/destination route.
    """

    managed_destinations = {_topic(topic).path for topic in _TOPIC_HEADINGS} | {
        _REFERENCE_COMPATIBILITY
    }
    discovered: set[DiscoveredInboundRoute] = set()
    for path in _active_reference_sources(package_root):
        relative = path.relative_to(package_root).as_posix()
        content = path.read_text(encoding="utf-8")
        for link in markdown_links(content):
            destination_path = _resolved_package_link(relative, link.target_path)
            if destination_path not in managed_destinations:
                continue
            root_heading, titles_by_anchor = _destination_heading_lookup(
                package_root,
                destination_path,
            )
            if root_heading is None:
                heading = ""
                anchor = link.anchor or ""
            elif link.anchor is None:
                heading = root_heading.title
                anchor = root_heading.anchor
            else:
                heading = titles_by_anchor.get(link.anchor, "")
                anchor = link.anchor
            discovered.add(
                DiscoveredInboundRoute(
                    relative,
                    InboundRouteKind.MARKDOWN_LINK,
                    destination_path,
                    heading,
                    anchor,
                )
            )

        for match in _INSTALLED_REFERENCE_PATH.finditer(content):
            destination_path = f"skills/{match.group('relative')}"
            root_heading, _ = _destination_heading_lookup(
                package_root,
                destination_path,
            )
            discovered.add(
                DiscoveredInboundRoute(
                    relative,
                    InboundRouteKind.INSTALLED_FILE_ROUTE,
                    destination_path,
                    root_heading.title if root_heading is not None else "",
                    root_heading.anchor if root_heading is not None else "",
                )
            )

        for match in _REFERENCE_ROOT_TOPIC_PATH.finditer(content):
            destination_path = (
                f"{_REFERENCE_TOPICS}/{match.group('topic')}"
            )
            root_heading, _ = _destination_heading_lookup(
                package_root,
                destination_path,
            )
            discovered.add(
                DiscoveredInboundRoute(
                    relative,
                    InboundRouteKind.INSTALLED_FILE_ROUTE,
                    destination_path,
                    root_heading.title if root_heading is not None else "",
                    root_heading.anchor if root_heading is not None else "",
                )
            )

    return tuple(
        sorted(
            discovered,
            key=lambda item: (
                item.source_path,
                item.destination_path,
                item.kind.value,
                item.destination_anchor,
            ),
        )
    )


def _package_data_patterns(project_root: Path) -> tuple[str, ...]:
    if tomllib is None:
        return ()
    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        return ()
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        values = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    except (KeyError, OSError, TypeError, ValueError):
        return ()
    if not isinstance(values, list) or not all(
        isinstance(item, str) for item in values
    ):
        return ()
    return tuple(values)


def destination_is_packaged(
    project_root: Path,
    destination: InstructionDestination,
) -> bool:
    """Return whether package metadata includes the instruction destination."""

    return any(
        fnmatch.fnmatchcase(destination.path, pattern)
        for pattern in _package_data_patterns(project_root)
    )


def destination_exists(
    project_root: Path,
    package_root: Path,
    destination: InstructionDestination,
) -> bool:
    """Require an included package-data file and its declared heading/anchor."""

    path = package_root / destination.path
    if not path.is_file() or not destination_is_packaged(project_root, destination):
        return False
    if destination.heading is None:
        return True
    headings = markdown_headings(path.read_text(encoding="utf-8"))
    return any(
        heading.title == destination.heading
        and (destination.anchor is None or heading.anchor == destination.anchor)
        for heading in headings
    )


def _section_text(content: str, heading: str) -> str | None:
    marker = f"\n{heading}\n"
    start = content.find(marker)
    if start < 0:
        return None
    start += 1
    following = re.search(r"(?m)^## ", content[start + len(heading) :])
    if following is None:
        return content[start:]
    end = start + len(heading) + following.start()
    return content[start:end]


def route_exists(
    rendered_content: str | None,
    route: InstructionRoute,
    *,
    agent: str,
    profile: SchemaRenderProfile,
) -> bool:
    """Require the route in the relevant rendered target/profile section."""

    if (
        rendered_content is None
        or profile not in route.profiles
        or agent not in route.agent_targets
    ):
        return False
    section = _section_text(rendered_content, route.source_heading)
    if section is None:
        return False
    if route.kind is InstructionRouteKind.INSTALLED_PATH:
        relative = PurePosixPath(route.destination_path)
        try:
            skill_relative = relative.relative_to("skills")
        except ValueError:
            return False
        expected = (skills_install_dir(agent) / skill_relative).as_posix()
        return expected in section
    if route.kind is InstructionRouteKind.WORKFLOW_SKILL:
        parts = PurePosixPath(route.destination_path).parts
        if len(parts) < 3 or parts[0] != "skills":
            return False
        skill_id = parts[1]
        return (
            re.search(rf"(?<![\w-]){re.escape(skill_id)}(?![\w-])", section) is not None
        )
    if route.literal is None:
        return False
    return normalize_instruction_text(route.literal) in normalize_instruction_text(
        section
    )


def removal_prerequisites_ready(
    project_root: Path,
    package_root: Path,
    coverage: GeneratedSectionCoverage,
    *,
    agent: str,
    profile: SchemaRenderProfile,
    rendered_content: str | None,
) -> bool:
    """Fail closed until every destination is packaged and rendered-routable."""

    inline_clauses = tuple(
        clause.always_inline and clause.source_section == coverage.section
        for clause in CORRECTNESS_CLAUSE_COVERAGE
    )
    if (
        profile in coverage.profiles
        or coverage.retained_kernel
        or not coverage.destinations
        or not coverage.routes
        or rendered_content is None
    ):
        return False
    if any(inline_clauses):
        normalized = normalize_instruction_text(rendered_content)
        for clause in CORRECTNESS_CLAUSE_COVERAGE:
            if clause.always_inline and clause.source_section == coverage.section:
                if normalize_instruction_text(clause.source_text) not in normalized:
                    return False
    destination_paths = {item.path for item in coverage.destinations}
    relevant_routes = tuple(
        route for route in coverage.routes if profile in route.profiles
    )
    route_paths = {item.destination_path for item in relevant_routes}
    if destination_paths != route_paths:
        return False
    return all(
        destination_exists(project_root, package_root, destination)
        for destination in coverage.destinations
    ) and all(
        route_exists(
            rendered_content,
            route,
            agent=agent,
            profile=profile,
        )
        for route in relevant_routes
    )


def correctness_destination_ready(
    project_root: Path,
    package_root: Path,
    clause: CorrectnessClauseCoverage,
    *,
    agent: str,
    profile: SchemaRenderProfile,
    rendered_content: str | None,
) -> bool:
    """Require packaged detail and a rendered route; inline rules never retire."""

    if clause.always_inline:
        return False
    if not destination_exists(project_root, package_root, clause.destination):
        return False
    if not route_exists(
        rendered_content,
        clause.route,
        agent=agent,
        profile=profile,
    ):
        return False
    expected = clause.destination_text or clause.source_text
    content = (package_root / clause.destination.path).read_text(encoding="utf-8")
    return normalize_instruction_text(expected) in normalize_instruction_text(content)


def inbound_route_resolves(
    project_root: Path,
    package_root: Path,
    route: ManagedReferenceInboundRoute,
) -> bool:
    """Validate one exact source route and its real destination heading anchor."""

    source_path = package_root / route.source_path
    destination = InstructionDestination(
        route.destination_path,
        route.destination_heading,
        route.destination_anchor,
    )
    if not source_path.is_file() or not destination_exists(
        project_root,
        package_root,
        destination,
    ):
        return False
    source = source_path.read_text(encoding="utf-8")
    normalized_source = normalize_instruction_text(source)
    normalized_span = normalize_instruction_text(route.source_text)
    if normalized_source.count(normalized_span) != 1:
        return False
    if route.kind is InboundRouteKind.MARKDOWN_LINK:
        if route.markdown_target is None:
            return False
        matches = [
            link
            for link in markdown_links(source)
            if link.target_path == route.markdown_target
        ]
        if len(matches) != 1:
            return False
        resolved = (
            PurePosixPath(route.source_path).parent / matches[0].target_path
        ).as_posix()
        return resolved == route.destination_path and matches[0].anchor is None
    if route.kind is InboundRouteKind.HEADING_REFERENCE:
        return f'"{route.destination_heading}"' in normalized_span
    if route.kind is InboundRouteKind.INSTALLED_FILE_ROUTE:
        relative = route.destination_path.removeprefix("skills/")
        topic_name = PurePosixPath(route.destination_path).name
        return relative in normalized_span or (
            "{reference_root}" in normalized_span and topic_name in normalized_span
        )
    return "wiki-reference" in normalized_span
