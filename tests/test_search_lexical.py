"""Bounded lexical candidate invariants independent of development targets."""

from copy import deepcopy
import hashlib
import random

import pytest

from llm_wiki_cli.services.search_lexical import rank_pages


def page(name, content, *, kind="modules", title=None, **metadata):
    return {"kind": kind, "id": name, "path": f"{kind}/{name}.md",
            "uri": f"llm-wiki://{kind}/{name}", "title": title or name,
            "content": content, **metadata}


@pytest.mark.parametrize("identity", ["owner", "modules/owner.md", "llm-wiki://modules/owner"])
def test_identity_precedence_cannot_be_overcome_by_arbitrary_term_repetition(identity):
    exact = page("owner", "# Owner\n\n## Description\nA small relevant declaration.\n")
    noisy = page("noise", (identity + " ") * 20000, title=(identity + " ") * 300)
    result = rank_pages([noisy, exact], identity)
    assert result["results"][0]["path"] == exact["path"]
    assert any(reason.startswith("exact-") for reason in result["results"][0]["reasons"])


def test_definition_table_precedes_fuzzy_reference_but_reference_is_not_a_definition():
    definition = page("owner", "# Owner\n\n## Functions\n\n| Name | Signature | Description |\n|---|---|---|\n| `assemble` | `assemble()` | Build the result. |\n")
    references = page("noise", "# Noise\n\n## Relationships\n\n| Reference | Kind |\n|---|---|\n| `assemble` | call |\n" + "assemble " * 2000)
    result = rank_pages([references, definition], "assemble")
    assert result["results"][0]["id"] == "owner"
    assert "defined-symbol" in result["results"][0]["reasons"]
    assert "defined-symbol" not in next(match for match in result["results"] if match["id"] == "noise")["reasons"]


def test_semantic_section_and_rare_terms_beat_large_common_inventory():
    meaningful = page("owner", "# Owner\n\n## Behavior\nAn amber mismatch invalidates the selected boundary.\n")
    noisy = page("noise", "# Noise\n\n## Imports\n" + "boundary " * 5000)
    other = [page(f"other_{n}", "## Imports\nboundary declarations modules methods") for n in range(10)]
    result = rank_pages([noisy, meaningful, *other], "amber boundary")
    assert result["results"][0]["id"] == "owner"
    assert ["Owner", "Behavior"] in result["results"][0]["matched_sections"]
    assert "amber" in result["results"][0]["snippet"]
    assert "section:Owner / Behavior" in result["results"][0]["reasons"]


def test_same_terms_in_prose_receive_more_weight_than_generated_inventory():
    prose = page("prose", "# Page\n\n## Behavior\nAn amber boundary mismatch.\n", title="Page")
    inventory = page("inventory", "# Page\n\n## Imports\nAn amber boundary mismatch.\n", title="Page")
    result = rank_pages([inventory, prose], "amber boundary")
    assert result["results"][0]["id"] == "prose"


def test_long_query_fallback_is_explicit_and_does_not_answer_unknown_behavior():
    owner = page("owner", "# Page\n\n## Notes\nThe amber boundary has a limit.\n")
    result = rank_pages([owner], "amber boundary vanished output confusing state")
    assert result["results"]
    match = result["results"][0]
    assert "relaxed-long-query-fallback" in match["reasons"]
    assert "lexical-discovery-candidate" in match["provenance"]["qualification"]
    assert "live comparison not performed" in match["provenance"]["qualification"]
    assert not {"answer", "correct", "verified", "definitive_answer"} & match.keys()
    assert rank_pages([owner], "neural similarity vector database")["results"] == []


def test_relaxed_match_does_not_remove_exact_identity():
    exact = page("amber boundary vanished output", "# Nothing\n")
    fallback = page("other", "## Notes\n" + "amber boundary " * 1000)
    result = rank_pages([fallback, exact], "amber boundary vanished output")
    assert result["results"][0]["id"] == exact["id"]


def test_disjoint_section_spans_do_not_duplicate_nested_parent_evidence():
    content = "# Example\n\n## Notes\nOutside narrative.\n\n### Detail\nAmber boundary.\n"
    result = rank_pages([page("owner", content)], "amber boundary")
    assert result["results"][0]["matched_sections"] == [["Example", "Notes", "Detail"]]
    assert "Amber boundary" in result["results"][0]["snippet"]


def test_augmented_index_provenance_does_not_become_the_wiki_file_hash():
    original = "# Owner\n\n## Description\nAn amber boundary.\n"
    augmented = original + "\n## Selected source indexing evidence\n```python\nraise ValueError('amber mismatch')\n```\n"
    wiki_hash = hashlib.sha256(original.encode()).hexdigest()
    indexed_hash = hashlib.sha256(augmented.encode()).hexdigest()
    metadata = {"treatment": "uniform-selected-static-source/v1", "original_wiki_content_sha256": wiki_hash,
                "indexed_content_sha256": indexed_hash, "source_sha256": "a" * 64,
                "source_path": "owner.py", "runtime_behavior_evaluated": False}
    record = page("owner", augmented, indexing=metadata)
    frozen = deepcopy(record)
    match = rank_pages([record], "amber mismatch")["results"][0]
    assert match["provenance"]["content_sha256"] == wiki_hash
    assert match["provenance"]["indexed_content_sha256"] == indexed_hash
    assert match["indexing"] == metadata
    match["indexing"]["source_path"] = "caller-change"
    assert record == frozen


def test_shuffled_inputs_have_identical_ranked_output_and_corpus_identity():
    pages = [page(f"owner_{index}", "## Notes\nAn amber boundary.\n") for index in range(5)]
    expected = rank_pages(pages, "amber boundary")
    shuffled = list(pages)
    random.Random(123).shuffle(shuffled)
    assert rank_pages(shuffled, "amber boundary") == expected


def test_single_pass_unicode_and_truthful_result_bounds():
    class OnePass:
        consumed = False
        def __iter__(self):
            assert not self.consumed
            self.consumed = True
            yield page("unicode", "# Scope\n\n## Notes\nCafé amber boundary.\n")
            yield page("other", "## Notes\nCafé amber boundary.\n")
    result = rank_pages(OnePass(), "Cafe\u0301 amber", limit=1)
    assert result["returned"] == 1 and result["total"] == 2
    assert result["bounds"]["results"] == {"returned": 1, "total": 2, "truncated": True}
    assert result["scanned"]["pages"] == 2
    assert result["scanned"]["bytes"] == sum(len(p["content"].encode()) for p in [page("unicode", "# Scope\n\n## Notes\nCafé amber boundary.\n"), page("other", "## Notes\nCafé amber boundary.\n")])


@pytest.mark.parametrize("option,value", [("limit", True), ("limit", 0), ("limit", 101),
    ("max_pages", True), ("max_pages", 10001), ("max_bytes", 0), ("max_bytes", 67108865)])
def test_resource_options_are_finite_exact_and_cannot_widen_limits(option, value):
    with pytest.raises(ValueError):
        rank_pages([], "amber", **{option: value})


def test_page_and_byte_exhaustion_refuse_instead_of_silently_truncating():
    pages = [page("a", "amber"), page("b", "amber")]
    with pytest.raises(ValueError, match="page limit"):
        rank_pages(iter(pages), "amber", max_pages=1)
    with pytest.raises(ValueError, match="byte limit"):
        rank_pages(pages, "amber", max_bytes=9)
    assert rank_pages([], "amber")["scanned"] == {"pages": 0, "bytes": 0}
    with pytest.raises(ValueError, match="identity"):
        rank_pages([{"content": "amber"}], "amber")


def test_hypothetical_guide_function_table_cannot_manufacture_definition_tier():
    hypothetical = page("guide", "## Functions\n| Name | Signature | Description |\n|---|---|---|\n| `assemble` | `assemble()` | Hypothetical example. |\n", kind="guides")
    actual = page("owner", "## Functions\n| Name | Signature | Description |\n|---|---|---|\n| `assemble` | `assemble()` | Recorded function. |\n")
    results = rank_pages([hypothetical, actual], "assemble")["results"]
    assert results[0]["id"] == "owner"
    assert "defined-symbol" not in results[1]["reasons"]


def test_selected_configuration_does_not_admit_single_term_long_query_noise():
    records = [page(f"other_{index}", "## Imports\ncommon declarations") for index in range(20)]
    records.append(page("owner", "## Notes\nAn amber mismatch."))
    result = rank_pages(records, "amber unknown absent unfamiliar different")
    assert result["results"] == []
    assert rank_pages(records, "common unknown absent unfamiliar different")["results"] == []


def test_repeated_section_citations_retain_exact_occurrence_and_normalized_span():
    content = "# Owner\n\n## Notes\nAmber paragraph.\n\n## Notes\nAmber boundary paragraph.\n"
    result = rank_pages([page("owner", content)], "amber")
    locations = result["results"][0]["matched_section_locations"]
    assert len(locations) == 2
    assert locations[0]["locator"] != locations[1]["locator"]
    assert locations[0]["occurrence_path"] != locations[1]["occurrence_path"]
    for location in locations:
        assert location["text_scope"] == "normalized-indexed-text"
        assert "Amber" in content[location["start"]:location["end"]]


def test_fenced_or_noncanonical_table_cannot_claim_a_defined_symbol():
    fenced = page("sample", "## Functions\n```markdown\n| Function | Signature | Description |\n|---|---|---|\n| `assemble` | `assemble()` | Hypothetical. |\n```\n")
    noncanonical = page("reference", "## Functions\n| Reference | Kind |\n|---|---|\n| `assemble` | call |\n")
    for match in rank_pages([fenced, noncanonical], "assemble")["results"]:
        assert "defined-symbol" not in match["reasons"]
