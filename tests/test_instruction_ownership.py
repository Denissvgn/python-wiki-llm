"""Executable ownership, packaging, and route coverage for agent instructions."""

from __future__ import annotations

from collections import Counter
from itertools import product
from pathlib import Path

from llm_wiki_cli.services.instruction_ownership import (
    CORRECTNESS_CLAUSE_COVERAGE,
    GENERATED_SECTION_COVERAGE,
    MANAGED_REFERENCE_INBOUND_ROUTES,
    REPOSITORY_HYGIENE_COVERAGE,
    InboundRouteKind,
    InstructionDestination,
    InstructionOrigin,
    InstructionOwner,
    InstructionProfile,
    MarkdownLink,
    SectionCondition,
    correctness_destination_ready,
    destination_exists,
    destination_is_packaged,
    discover_managed_reference_inbound_routes,
    inbound_route_resolves,
    markdown_headings,
    markdown_links,
    normalize_instruction_text,
    removal_prerequisites_ready,
    route_exists,
)
from llm_wiki_cli.services.schema import (
    CONSTRAINT_END,
    CONSTRAINT_START,
    SCHEMA_FILENAMES,
    build_schema_content,
)
from llm_wiki_cli.services.skills import skills_install_dir


PROJECT_ROOT = Path(__file__).parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "llm_wiki_cli"


EXPECTED_CURRENT_SECTIONS = (
    ("Preamble/markers", None),
    ("Before you start", "## Before you start"),
    ("Repository delivery preflight", "## Repository delivery preflight"),
    ("Native knowledge preflight", "## Native knowledge preflight"),
    ("Deep reference", "## Deep reference (read on demand)"),
    ("Resource-aware execution", "## Resource-aware execution"),
    ("Canonical wiki surfaces", "## Canonical wiki surfaces"),
    ("User docs and usage examples", "## User docs and usage examples"),
    ("When you change code", "## When you change code"),
    ("Wiki file naming rules", "## Wiki file naming rules"),
    ("Quality checks", "## Quality checks"),
    ("Tool issue reporting", "## Report llm-wiki tool issues"),
    ("Formatting rules", "## Formatting rules"),
    ("Agent quality guidelines", "## Agent quality guidelines"),
    ("How to sync in this session", "## How to sync the wiki in this agent session"),
    (
        "Incremental sync details",
        "## Using `llm-wiki sync` for incremental updates",
    ),
    ("Large codebases", "## Large codebases"),
)


def _level_two_headings(content: str) -> tuple[str, ...]:
    return tuple(line for line in content.splitlines() if line.startswith("## "))


def _section_text(content: str, heading: str) -> str:
    start = content.index(heading)
    tail = content[start + len(heading) :]
    next_heading = tail.find("\n## ")
    if next_heading < 0:
        return content[start:]
    return content[start : start + len(heading) + next_heading]


def _rendered_content(
    agent: str,
    profile: InstructionProfile,
    *,
    quality_hints: bool = True,
    issue_reporting: bool = False,
) -> str | None:
    if profile is InstructionProfile.COMPACT:
        return None
    return build_schema_content(
        agent,
        "docs/llm_wiki",
        quality_hints=quality_hints,
        issue_reporting=issue_reporting,
    )


def test_current_generated_sections_have_one_authoritative_owner():
    actual = tuple(
        (item.section, item.source_heading) for item in GENERATED_SECTION_COVERAGE
    )
    assert actual == EXPECTED_CURRENT_SECTIONS
    assert len({item.section for item in GENERATED_SECTION_COVERAGE}) == len(actual)
    assert all(
        isinstance(item.owner, InstructionOwner) for item in GENERATED_SECTION_COVERAGE
    )

    expected_owner = {
        "When you change code": InstructionOwner.MANAGED_REFERENCE_TOPIC,
        "Incremental sync details": InstructionOwner.MANAGED_REFERENCE_TOPIC,
        "User docs and usage examples": InstructionOwner.WORKFLOW_SKILL,
        "Quality checks": InstructionOwner.DETERMINISTIC_CLI_LINT,
    }
    owner_by_section = {item.section: item.owner for item in GENERATED_SECTION_COVERAGE}
    for section, owner in expected_owner.items():
        assert owner_by_section[section] is owner


def test_current_renderer_matches_section_inventory_for_every_target_and_option():
    for quality_hints, issue_reporting in product((False, True), repeat=2):
        expected_headings = tuple(
            item.source_heading
            for item in GENERATED_SECTION_COVERAGE
            if item.source_heading is not None
            and (
                item.condition is SectionCondition.ALWAYS
                or (item.condition is SectionCondition.QUALITY_HINTS and quality_hints)
                or (
                    item.condition is SectionCondition.ISSUE_REPORTING
                    and issue_reporting
                )
            )
        )
        for agent in SCHEMA_FILENAMES:
            content = build_schema_content(
                agent,
                "docs/llm_wiki",
                quality_hints=quality_hints,
                issue_reporting=issue_reporting,
            )
            assert content.startswith(CONSTRAINT_START)
            assert content.rstrip().endswith(CONSTRAINT_END)
            assert _level_two_headings(content) == expected_headings


def test_owner_inventory_uses_every_supported_owner_class():
    assert {item.owner for item in GENERATED_SECTION_COVERAGE} == set(InstructionOwner)


def test_repository_hygiene_reservations_retain_required_semantics_everywhere():
    required_concepts = {
        "internal_document_publication": (
            "internal documentation",
            "adrs",
            "plans",
            "backlogs",
            "reports",
            "implementation notes",
            "never be published",
            "exact path",
            "proven ignored",
            "stage",
            "force-add",
        ),
        "public_document_content": (
            "public documentation",
            "readme",
            "published documentation",
            "wiki",
            "site",
            "must never mention",
            "development phases",
            "tests",
        ),
        "code_and_test_provenance": (
            "source code",
            "comments",
            "docstrings",
            "identifiers",
            "fixtures",
            "test files",
            "epic",
            "milestone",
            "phase names",
            "backlog",
            "task identifiers",
            "planning provenance",
        ),
    }
    assert {item.name for item in REPOSITORY_HYGIENE_COVERAGE} == set(required_concepts)
    assert len(REPOSITORY_HYGIENE_COVERAGE) == 3
    for item in REPOSITORY_HYGIENE_COVERAGE:
        contract = normalize_instruction_text(item.contract).lower()
        assert item.owner is InstructionOwner.KERNEL
        assert item.always_inline
        assert set(item.profiles) == set(InstructionProfile)
        assert set(item.agent_targets) == set(SCHEMA_FILENAMES)
        for concept in required_concepts[item.name]:
            assert concept in contract, (item.name, concept)


def test_critical_inline_clauses_are_explicit_and_semantically_present():
    required = {
        "relevant_code_change_activation": (
            "after every code change in this session",
            "adds, removes, or modifies",
            "sync-then-lint workflow",
        ),
        "generated_semantic_ownership": (
            "edit semantic prose only",
            "generated blocks are cli-owned",
        ),
        "source_read_only": (
            "source targets read-only",
            "user explicitly asks for source edits",
        ),
        "lint_clean_handoff": (
            "never leave the wiki",
            "lint reports errors",
        ),
    }
    inline = {
        item.name: item for item in CORRECTNESS_CLAUSE_COVERAGE if item.always_inline
    }
    assert set(inline) == set(required)
    for item in inline.values():
        assert item.owner is InstructionOwner.KERNEL
        assert set(item.profiles) == set(InstructionProfile)
        assert set(item.agent_targets) == set(SCHEMA_FILENAMES)
        assert item.destination.path.startswith("skills/wiki-reference/references/")

    for agent in SCHEMA_FILENAMES:
        content = build_schema_content(agent, "docs/llm_wiki")
        normalized = normalize_instruction_text(content).lower()
        for name, concepts in required.items():
            clause = inline[name]
            assert normalize_instruction_text(clause.source_text).lower() in normalized
            for concept in concepts:
                assert concept in normalized, (agent, name, concept)


def test_sync_only_clause_inventory_is_not_self_declared():
    expected_names = {
        "relevant_code_change_activation",
        "stale_update_guard",
        "manifestless_sync_seeding",
        "final_owning_sync_condition",
    }
    actual = {
        item.name
        for item in CORRECTNESS_CLAUSE_COVERAGE
        if item.origin is InstructionOrigin.SYNC_INSTRUCTIONS
    }
    assert actual == expected_names

    content = build_schema_content("generic", "docs/llm_wiki")
    for name in expected_names:
        clause = next(item for item in CORRECTNESS_CLAUSE_COVERAGE if item.name == name)
        section = next(
            item
            for item in GENERATED_SECTION_COVERAGE
            if item.section == clause.source_section
        )
        assert section.source_heading is not None
        assert normalize_instruction_text(
            clause.source_text
        ) in normalize_instruction_text(_section_text(content, section.source_heading))


def test_correctness_owner_and_destination_decisions_are_consistent():
    clauses = {item.name: item for item in CORRECTNESS_CLAUSE_COVERAGE}
    assert len(clauses) == len(CORRECTNESS_CLAUSE_COVERAGE)
    assert clauses["strict_validation_after_reanchor"].destination.path.endswith(
        "/maintenance.md"
    )
    assert clauses["lint_clean_handoff"].destination.path.endswith("/maintenance.md")
    assert clauses["unsupported_source_disclosure"].destination.path.endswith(
        "/extractors-dependencies.md"
    )
    assert clauses["lint_clean_handoff"].owner is InstructionOwner.KERNEL
    assert all(
        item.destination.path != "skills/wiki-sync/SKILL.md"
        for item in CORRECTNESS_CLAUSE_COVERAGE
    )


def test_user_documentation_section_maps_every_selected_workflow_subroute():
    section = next(
        item
        for item in GENERATED_SECTION_COVERAGE
        if item.section == "User docs and usage examples"
    )
    expected_paths = {
        "skills/wiki-bootstrap/SKILL.md",
        "skills/wiki-sync/SKILL.md",
        "skills/user-docs-author/SKILL.md",
        "skills/usage-examples/SKILL.md",
        "skills/publish-docs/SKILL.md",
    }
    assert {item.path for item in section.destinations} == expected_paths
    assert {item.destination_path for item in section.routes} == expected_paths
    for destination in section.destinations:
        assert destination_exists(PROJECT_ROOT, PACKAGE_ROOT, destination)
    for agent, profile in product(SCHEMA_FILENAMES, InstructionProfile):
        content = _rendered_content(agent, profile)
        for route in section.routes:
            assert route_exists(
                content,
                route,
                agent=agent,
                profile=profile,
            ) is (profile is InstructionProfile.EXPANDED)
        assert not removal_prerequisites_ready(
            PROJECT_ROOT,
            PACKAGE_ROOT,
            section,
            agent=agent,
            profile=profile,
            rendered_content=content,
        )


def test_destination_requires_file_heading_and_package_data_inclusion(tmp_path: Path):
    project_root = tmp_path / "project"
    package_root = project_root / "src" / "llm_wiki_cli"
    destination_path = package_root / "skills" / "sample" / "reference.md"
    destination_path.parent.mkdir(parents=True)
    destination_path.write_text("# Sample reference\n", encoding="utf-8")
    (project_root / "pyproject.toml").write_text(
        '[tool.setuptools.package-data]\n"llm_wiki_cli" = []\n',
        encoding="utf-8",
    )
    destination = InstructionDestination(
        "skills/sample/reference.md",
        "Sample reference",
        "sample-reference",
    )
    assert not destination_is_packaged(project_root, destination)
    assert not destination_exists(project_root, package_root, destination)

    (project_root / "pyproject.toml").write_text(
        "[tool.setuptools.package-data]\n"
        '"llm_wiki_cli" = ["skills/sample/reference.md"]\n',
        encoding="utf-8",
    )
    assert destination_is_packaged(project_root, destination)
    assert destination_exists(project_root, package_root, destination)
    assert not destination_exists(
        project_root,
        package_root,
        InstructionDestination(
            destination.path,
            "Missing heading",
            "missing-heading",
        ),
    )


def test_removal_gate_uses_relevant_rendered_profile_for_every_target():
    raw_schema_source = (PACKAGE_ROOT / "services" / "schema.py").read_text(
        encoding="utf-8"
    )
    deep_reference = next(
        item for item in GENERATED_SECTION_COVERAGE if item.section == "Deep reference"
    )
    retained_routes = {
        item.section for item in GENERATED_SECTION_COVERAGE if item.retained_kernel
    }
    assert {
        "Before you start",
        "Native knowledge preflight",
        "Deep reference",
    } <= retained_routes
    assert len(deep_reference.routes) == 1
    assert not route_exists(
        raw_schema_source,
        deep_reference.routes[0],
        agent="generic",
        profile=InstructionProfile.EXPANDED,
    )

    for agent, profile in product(SCHEMA_FILENAMES, InstructionProfile):
        content = _rendered_content(agent, profile)
        deep_ready = removal_prerequisites_ready(
            PROJECT_ROOT,
            PACKAGE_ROOT,
            deep_reference,
            agent=agent,
            profile=profile,
            rendered_content=content,
        )
        assert not deep_ready
        assert route_exists(
            content,
            deep_reference.routes[0],
            agent=agent,
            profile=profile,
        ) is (profile is InstructionProfile.EXPANDED)

        for section in GENERATED_SECTION_COVERAGE:
            ready = removal_prerequisites_ready(
                PROJECT_ROOT,
                PACKAGE_ROOT,
                section,
                agent=agent,
                profile=profile,
                rendered_content=content,
            )
            if profile is InstructionProfile.COMPACT:
                assert not ready
            elif (
                section.source_heading is not None
                and section.condition is not SectionCondition.ISSUE_REPORTING
            ):
                assert content is not None
                assert section.source_heading in content


def test_correctness_text_cannot_retire_in_any_target_or_profile_yet():
    for agent, profile in product(SCHEMA_FILENAMES, InstructionProfile):
        content = _rendered_content(agent, profile)
        for clause in CORRECTNESS_CLAUSE_COVERAGE:
            assert not correctness_destination_ready(
                PROJECT_ROOT,
                PACKAGE_ROOT,
                clause,
                agent=agent,
                profile=profile,
                rendered_content=content,
            )
            if profile is InstructionProfile.EXPANDED:
                assert content is not None
                section = next(
                    item
                    for item in GENERATED_SECTION_COVERAGE
                    if item.section == clause.source_section
                )
                assert section.source_heading is not None
                source = _section_text(content, section.source_heading)
                assert normalize_instruction_text(
                    clause.source_text
                ) in normalize_instruction_text(source), clause.name


def test_managed_reference_inbound_inventory_is_explicit_and_exhaustive():
    expected = {
        (
            "skills/wiki-reference/SKILL.md",
            InboundRouteKind.MARKDOWN_LINK,
            "wiki-reference reference",
        ),
        (
            "services/schema.py",
            InboundRouteKind.HEADING_REFERENCE,
            "Extractor helpers and toolchains",
        ),
        (
            "services/schema.py",
            InboundRouteKind.REFERENCE_ROOT,
            "wiki-reference reference",
        ),
        (
            "services/schema.py",
            InboundRouteKind.HEADING_REFERENCE,
            "Repository-aware Git handoff",
        ),
        (
            "services/schema.py",
            InboundRouteKind.INSTALLED_FILE_ROUTE,
            "wiki-reference reference",
        ),
        (
            "services/schema.py",
            InboundRouteKind.HEADING_REFERENCE,
            "Static-site export",
        ),
        (
            "services/schema.py",
            InboundRouteKind.HEADING_REFERENCE,
            "Dependency reconciliation",
        ),
        *(
            (path, InboundRouteKind.HEADING_REFERENCE, "Repository-aware Git handoff")
            for path in (
                "skills/usage-examples/SKILL.md",
                "skills/onboarding-guide/SKILL.md",
                "skills/wiki-sync/SKILL.md",
                "skills/infra-review/SKILL.md",
                "skills/dep-audit/SKILL.md",
                "skills/wiki-bootstrap/SKILL.md",
                "skills/user-docs-author/SKILL.md",
                "skills/doc-review/SKILL.md",
            )
        ),
    }
    actual = {
        (item.source_path, item.kind, item.destination_heading)
        for item in MANAGED_REFERENCE_INBOUND_ROUTES
    }
    assert actual == expected
    assert len(actual) == 15
    assert len(MANAGED_REFERENCE_INBOUND_ROUTES) == 16
    assert {
        item.source_text
        for item in MANAGED_REFERENCE_INBOUND_ROUTES
        if item.source_path == "services/schema.py"
        and item.kind is InboundRouteKind.REFERENCE_ROOT
    } == {
        "Flag semantics are documented in the `wiki-reference` skill.",
        "per-language extraction contracts (including the Haskell helper and inventory schema) are documented in the `wiki-reference` skill.",
    }
    assert all(
        inbound_route_resolves(PROJECT_ROOT, PACKAGE_ROOT, item)
        for item in MANAGED_REFERENCE_INBOUND_ROUTES
    )

    declared = Counter(
        (
            item.source_path,
            item.kind,
            item.destination_heading,
            item.destination_anchor,
        )
        for item in MANAGED_REFERENCE_INBOUND_ROUTES
    )
    discovered = Counter(
        (
            item.source_path,
            item.kind,
            item.destination_heading,
            item.destination_anchor,
        )
        for item in discover_managed_reference_inbound_routes(PACKAGE_ROOT)
    )
    assert discovered == declared


def test_reference_router_markdown_link_and_real_heading_anchors_resolve():
    skill_path = PACKAGE_ROOT / "skills" / "wiki-reference" / "SKILL.md"
    reference_path = PACKAGE_ROOT / "skills" / "wiki-reference" / "reference.md"
    assert MarkdownLink("reference.md", "reference.md", None) in markdown_links(
        skill_path.read_text(encoding="utf-8")
    )

    headings = {
        (item.title, item.anchor)
        for item in markdown_headings(reference_path.read_text(encoding="utf-8"))
    }
    for route in MANAGED_REFERENCE_INBOUND_ROUTES:
        assert (route.destination_heading, route.destination_anchor) in headings


def test_generated_compatibility_reference_path_resolves_for_every_target():
    destination = InstructionDestination(
        "skills/wiki-reference/reference.md",
        "wiki-reference reference",
        "wiki-reference-reference",
    )
    assert destination_exists(PROJECT_ROOT, PACKAGE_ROOT, destination)
    for agent in SCHEMA_FILENAMES:
        content = build_schema_content(agent, "docs/llm_wiki")
        reference_path = (
            skills_install_dir(agent) / "wiki-reference" / "reference.md"
        ).as_posix()
        assert reference_path in content
