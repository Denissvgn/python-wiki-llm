from __future__ import annotations

from copy import deepcopy

import pytest

from llm_wiki_cli.services.contracts import (
    SECTION_OWNERSHIP_EXTENSION_KEY,
    SECTION_OWNERSHIP_SCHEMA_VERSION,
)
from llm_wiki_cli.services.markdown_sections import table_description_cells
from llm_wiki_cli.services.section_ownership import (
    SectionOwnership,
    SectionOwnershipError,
    merge_entity_semantics,
    observe_page_sections,
    replace_generated_section,
    section_ownership_extension,
    validate_section_ownership,
)
from llm_wiki_cli.services.markdown_sections import (
    GENERATED_INDEX_ENTRY_POINT_FLOWS_HEADING,
    GENERATED_INDEX_HTTP_API_CONTRACTS_HEADING,
)
from llm_wiki_cli.services.wiki_surface import PageKind


def _by_title(markdown: str, kind: PageKind):
    page = observe_page_sections(
        markdown,
        f"llm-wiki://{kind.value}/example",
        kind,
    )
    return page, [(section.title, section.ownership) for section in page.sections]


def test_section_ownership_has_all_four_conservative_states():
    assert {ownership.value for ownership in SectionOwnership} == {
        "generated",
        "semantic",
        "mixed",
        "unknown",
    }


def test_entity_policy_limits_canonical_sections_and_inherits_nested_ownership():
    markdown = """# Entity
## Description
Human prose.
### Details
More prose.
## Description
Duplicate prose.
## Attributes
| Name | Type | Description |
|---|---|---|
| `value` | `str` | Human meaning |
### Attribute caveat
Nested.
## Relationships
generated
### Incoming
generated nested
## Custom
unknown
"""
    page, pairs = _by_title(markdown, PageKind.ENTITIES)
    assert pairs == [
        ("Entity", SectionOwnership.UNKNOWN),
        ("Description", SectionOwnership.SEMANTIC),
        ("Details", SectionOwnership.SEMANTIC),
        ("Description", SectionOwnership.UNKNOWN),
        ("Attributes", SectionOwnership.MIXED),
        ("Attribute caveat", SectionOwnership.MIXED),
        ("Relationships", SectionOwnership.GENERATED),
        ("Incoming", SectionOwnership.GENERATED),
        ("Custom", SectionOwnership.UNKNOWN),
    ]
    observations = page.sections
    assert observations[1].semantic_hash == observations[1].exact_hash
    assert observations[1].structural_hash is None
    assert observations[4].structural_hash is not None
    assert observations[4].semantic_hash is not None
    assert observations[6].structural_hash == observations[6].exact_hash
    assert observations[6].semantic_hash is None
    assert observations[-1].structural_hash is None
    assert observations[-1].semantic_hash is None


def test_module_mixed_tables_and_generated_local_dependencies():
    markdown = """# Module
## Description
Semantic.
## Classes
| Class | Line | Description |
|---|---:|---|
| A | 1 | Meaning |
## Functions
| Function | Signature | Description |
|---|---|---|
| f | `f()` | Meaning |
## Local dependency map
generated
## Imports
generated
## Custom
unknown
"""
    _, pairs = _by_title(markdown, PageKind.MODULES)
    assert pairs == [
        ("Module", SectionOwnership.UNKNOWN),
        ("Description", SectionOwnership.SEMANTIC),
        ("Classes", SectionOwnership.MIXED),
        ("Functions", SectionOwnership.MIXED),
        ("Local dependency map", SectionOwnership.GENERATED),
        ("Imports", SectionOwnership.GENERATED),
        ("Custom", SectionOwnership.UNKNOWN),
    ]


def test_guides_are_semantic_and_index_custom_is_semantic_only_when_preserved():
    guide, guide_pairs = _by_title(
        "# Guide\n## Anything\n### Nested\n",
        PageKind.GUIDES,
    )
    assert all(
        ownership is SectionOwnership.SEMANTIC for _, ownership in guide_pairs
    )
    assert all(
        section.semantic_hash == section.exact_hash for section in guide.sections
    )

    markdown = (
        "# Index\n"
        "## Modules\ngenerated\n"
        f"## {GENERATED_INDEX_ENTRY_POINT_FLOWS_HEADING}\ngenerated\n"
        f"## {GENERATED_INDEX_HTTP_API_CONTRACTS_HEADING}\ngenerated\n"
        "## Entry-point flows\nhuman routing\n"
        "## HTTP API contracts\nhuman contract notes\n"
        "## Team notes\nhuman\n"
    )
    preserved = observe_page_sections(
        markdown,
        "llm-wiki://index",
        PageKind.INDEX,
    )
    unpreserved = observe_page_sections(
        markdown,
        "llm-wiki://index",
        PageKind.INDEX,
        index_preserved=False,
    )
    assert [section.ownership for section in preserved.sections] == [
        SectionOwnership.UNKNOWN,
        SectionOwnership.GENERATED,
        SectionOwnership.GENERATED,
        SectionOwnership.GENERATED,
        SectionOwnership.SEMANTIC,
        SectionOwnership.SEMANTIC,
        SectionOwnership.SEMANTIC,
    ]
    assert all(
        section.ownership is SectionOwnership.UNKNOWN
        for section in unpreserved.sections[-3:]
    )


def test_only_first_behavior_and_notes_sections_are_semantic():
    fixtures = (
        (PageKind.WORKFLOWS, "Behavior", "Sequence"),
        (PageKind.FLOWS, "Behavior", "Call sequence"),
        (PageKind.API_CONTRACTS, "Notes", "Applications"),
        (PageKind.DEPENDENCIES, "Notes", "Module graph"),
        (PageKind.LOAD_ORDER, "Notes", "Load order"),
    )
    for kind, semantic_heading, generated_heading in fixtures:
        markdown = (
            f"# Page\n"
            f"## {generated_heading}\n"
            "generated\n"
            f"## {semantic_heading}\n"
            "first\n"
            f"## {semantic_heading}\n"
            "second\n"
        )
        page = observe_page_sections(
            markdown,
            f"llm-wiki://{kind.value}",
            kind,
        )
        matching = [
            section
            for section in page.sections
            if section.title == semantic_heading
        ]
        assert [section.ownership for section in matching] == [
            SectionOwnership.SEMANTIC,
            SectionOwnership.UNKNOWN,
        ]
        assert page.sections[1].ownership is SectionOwnership.GENERATED


def test_workflow_behavior_semantics_are_stable_across_generated_churn():
    before = """# Workflow
## Sequence
1. `start`
## Touches
- [service](../modules/service.md)
## Behavior
Runs the reviewed primary path.
"""
    after = before.replace("1. `start`", "1. `start`\n2. `finish`")

    first = observe_page_sections(
        before,
        "llm-wiki://workflows/example",
        PageKind.WORKFLOWS,
    )
    changed = observe_page_sections(
        after,
        "llm-wiki://workflows/example",
        PageKind.WORKFLOWS,
    )
    first_sequence, first_touches, first_behavior = first.sections[1:]
    changed_sequence, changed_touches, changed_behavior = changed.sections[1:]

    assert first_sequence.structural_hash != changed_sequence.structural_hash
    assert first_sequence.semantic_hash is None
    assert first_touches.structural_hash == changed_touches.structural_hash
    assert first_touches.semantic_hash is None
    assert first_behavior.semantic_hash == changed_behavior.semantic_hash
    assert first_behavior.structural_hash is None


def test_policy_is_explicit_for_every_page_kind_and_custom_never_optimistic():
    canonical = {
        PageKind.INDEX: "Modules",
        PageKind.LOG: "2026-07-27",
        PageKind.ENTITIES: "Relationships",
        PageKind.MODULES: "Imports",
        PageKind.WORKFLOWS: "Sequence",
        PageKind.GUIDES: "Overview",
        PageKind.FLOWS: "Call sequence",
        PageKind.INFRASTRUCTURE: "Services",
        PageKind.API_CONTRACTS: "Applications",
        PageKind.DEPENDENCIES: "Module graph",
        PageKind.LOAD_ORDER: "Load order",
    }
    for kind in PageKind:
        markdown = f"# Page\n## {canonical[kind]}\nbody\n## Bespoke\ncustom\n"
        page = observe_page_sections(
            markdown,
            f"llm-wiki://{kind.value}",
            kind,
            index_preserved=False,
        )
        assert page.sections[1].ownership is not SectionOwnership.UNKNOWN
        expected_custom = (
            SectionOwnership.SEMANTIC
            if kind is PageKind.GUIDES
            else SectionOwnership.UNKNOWN
        )
        assert page.sections[-1].ownership is expected_custom


def test_mixed_hashes_change_only_for_their_modeled_scope():
    before = """# Entity
## Attributes
| Name | Type | Description |
|---|---|---|
| `value` | `str` | Human meaning |
"""
    structure = before.replace("`str`", "`int`")
    semantics = before.replace("Human meaning", "Reviewed meaning")

    first = observe_page_sections(
        before,
        "llm-wiki://entities/Entity",
        PageKind.ENTITIES,
    ).sections[1]
    structural_change = observe_page_sections(
        structure,
        "llm-wiki://entities/Entity",
        PageKind.ENTITIES,
    ).sections[1]
    semantic_change = observe_page_sections(
        semantics,
        "llm-wiki://entities/Entity",
        PageKind.ENTITIES,
    ).sections[1]

    assert first.exact_hash != structural_change.exact_hash
    assert first.structural_hash != structural_change.structural_hash
    assert first.semantic_hash == structural_change.semantic_hash
    assert first.structural_hash == semantic_change.structural_hash
    assert first.semantic_hash != semantic_change.semantic_hash


def test_mixed_semantic_hash_ignores_generated_duplicate_row_churn():
    before = """# Entity
## Methods
| Method | Signature | Description |
|---|---|---|
| `same` | `same(a)` | Human meaning |
| `other` | `other()` | Other meaning |
"""
    generated_churn = """# Entity
## Methods
| Method | Signature | Description |
|---|---|---|
| `other` | `other()` | Other meaning |
| `same` | `same(b)` | Human meaning |
| `same` | `same(a)` | Human meaning |
"""

    assert table_description_cells(before, "Methods") == (
        table_description_cells(generated_churn, "Methods")
    )
    first = observe_page_sections(
        before,
        "llm-wiki://entities/Entity",
        PageKind.ENTITIES,
    ).sections[1]
    changed = observe_page_sections(
        generated_churn,
        "llm-wiki://entities/Entity",
        PageKind.ENTITIES,
    ).sections[1]

    assert first.semantic_hash == changed.semantic_hash
    assert first.structural_hash != changed.structural_hash


def test_generated_and_semantic_hashes_do_not_cross_domains():
    markdown = """# Flow
## Call sequence
generated
## Behavior
human
## Custom
unknown
"""
    page = observe_page_sections(
        markdown,
        "llm-wiki://flows/example",
        PageKind.FLOWS,
    )
    generated, semantic, unknown = page.sections[1:]
    assert (generated.structural_hash, generated.semantic_hash) == (
        generated.exact_hash,
        None,
    )
    assert (semantic.structural_hash, semantic.semantic_hash) == (
        None,
        semantic.exact_hash,
    )
    assert (unknown.structural_hash, unknown.semantic_hash) == (None, None)


def test_section_extension_sorts_pages_and_preserves_section_order():
    second = observe_page_sections(
        "# B\n## Description\nB\n",
        "llm-wiki://modules/b",
        PageKind.MODULES,
    )
    first = observe_page_sections(
        "# A\n## Description\nA\n",
        "llm-wiki://modules/a",
        PageKind.MODULES,
    )
    extension = section_ownership_extension([second, first])
    payload = extension[SECTION_OWNERSHIP_EXTENSION_KEY]

    assert payload["schema_version"] == SECTION_OWNERSHIP_SCHEMA_VERSION
    assert [page["page_locator"] for page in payload["pages"]] == [
        "llm-wiki://modules/a",
        "llm-wiki://modules/b",
    ]
    assert [section["ordinal"] for section in payload["pages"][0]["sections"]] == [
        0,
        1,
    ]
    assert payload["pages"][0]["sections"][1]["parent_locator"] == (
        payload["pages"][0]["sections"][0]["locator"]
    )


def test_sectionless_page_gets_a_preamble_observation():
    page = observe_page_sections(
        "Semantic guide without headings.\r\n",
        "llm-wiki://guides/plain",
        PageKind.GUIDES,
    )
    assert len(page.sections) == 1
    assert page.sections[0].title is None
    assert page.sections[0].level == 0
    assert page.sections[0].ownership is SectionOwnership.SEMANTIC
    assert page.sections[0].semantic_hash == page.sections[0].exact_hash


def test_persisted_section_contract_rejects_reorder_scope_and_snapshot_mismatch():
    observed = observe_page_sections(
        "# Module\n## Description\nHuman\n## Imports\nGenerated\n",
        "llm-wiki://modules/a",
        PageKind.MODULES,
    )
    payload = section_ownership_extension([observed])[
        SECTION_OWNERSHIP_EXTENSION_KEY
    ]
    concepts = {
        observed.page_locator: (
            PageKind.MODULES,
            observed.source_hash,
        )
    }
    assert validate_section_ownership(payload, concepts=concepts) == payload

    reordered = deepcopy(payload)
    reordered["pages"][0]["sections"][1:] = reversed(
        reordered["pages"][0]["sections"][1:]
    )
    for index, section in enumerate(reordered["pages"][0]["sections"]):
        section["ordinal"] = index
    with pytest.raises(SectionOwnershipError, match="ordering_hash"):
        validate_section_ownership(reordered, concepts=concepts)

    wrong_scope = deepcopy(payload)
    semantic = wrong_scope["pages"][0]["sections"][1]
    semantic["structural_hash"] = semantic["exact_hash"]
    with pytest.raises(SectionOwnershipError, match="hash scopes"):
        validate_section_ownership(wrong_scope, concepts=concepts)

    with pytest.raises(SectionOwnershipError, match="concept page hash"):
        validate_section_ownership(
            payload,
            concepts={
                observed.page_locator: (
                    PageKind.MODULES,
                    "sha256:" + ("f" * 64),
                )
            },
        )


def test_persisted_section_contract_enforces_conservative_page_policy():
    observed = observe_page_sections(
        "# Module\n## Custom\nHuman text\n",
        "llm-wiki://modules/a",
        PageKind.MODULES,
    )
    payload = section_ownership_extension([observed])[
        SECTION_OWNERSHIP_EXTENSION_KEY
    ]
    custom = payload["pages"][0]["sections"][1]
    assert custom["ownership"] == "unknown"

    custom["ownership"] = "semantic"
    custom["semantic_hash"] = custom["exact_hash"]

    with pytest.raises(SectionOwnershipError, match="conservative section policy"):
        validate_section_ownership(
            payload,
            concepts={
                observed.page_locator: (
                    PageKind.MODULES,
                    observed.source_hash,
                )
            },
        )


def test_service_merge_preserves_current_duplicate_row_behavior():
    existing = """# Entity
## Description
Human description.
## Methods
| Method | Signature | Description |
|---|---|---|
| `same` | `same(a)` | First human |
| `same` | `same(b)` | Second human |
"""
    generated = """# Entity
## Description
Generated description.
## Methods
| Method | Signature | Description |
|---|---|---|
| `same` | `same(x)` | Generated first |
| `same` | `same(y)` | Generated second |
"""
    merged = merge_entity_semantics(existing, generated)

    assert merged.preserved == 3
    assert merged.text.count("Second human") == 2
    assert "First human" not in merged.text
    assert "Human description." in merged.text


def test_generated_section_replacement_is_surgical_and_newline_compatible():
    existing = "# Entity\n\n## Relationships\n\nOld.\n\n## Custom\n\nKeep.\n"
    generated = "# Entity\n\n## Relationships\n\nNew.\n"
    assert replace_generated_section(existing, generated, "Relationships") == (
        "# Entity\n\n## Relationships\n\nNew.\n\n## Custom\n\nKeep.\n"
    )
