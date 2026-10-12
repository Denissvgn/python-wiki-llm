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


@pytest.mark.parametrize("base,query", [
    ("rename", "renaming"), ("delete", "deleted"), ("verify", "verifying"),
    ("verify", "verified"), ("expire", "expiry"), ("stop", "stopping"),
    ("process", "processes"), ("status", "statuses"), ("retry", "retrying"),
])
def test_word_forms_retrieve_captured_section_without_rewriting_evidence(base, query):
    content = f"# Payload\n\n## Notes\n{base.capitalize()} payload envelope safely.\n"
    owner = page("worker", content)
    original = deepcopy(owner)
    result = rank_pages([page("other", "## Notes\nDiagnostic clock samples.\n"), owner], query + " payload envelope")
    match = result["results"][0]
    assert match["path"] == owner["path"]
    assert match["provenance"]["content_sha256"] == hashlib.sha256(content.encode()).hexdigest()
    assert match["provenance"]["configuration"] == "idf-sections-prose-families-links/v2"
    assert "live comparison not performed" in match["provenance"]["qualification"]
    assert match["matched_section_locations"][0]["heading_path"] == ["Payload", "Notes"]
    assert owner == original


def test_word_family_discovery_does_not_replace_exact_symbol_or_page_identity():
    exact = page("object", "## Functions\n| Function | Signature | Description |\n|---|---|---|\n| `rename` | `rename()` | Renames payloads. |\n")
    related = page("renaming", "## Notes\nRename rename rename payload envelopes.\n")
    assert rank_pages([related, exact], "rename")["results"][0]["id"] == "object"
    assert rank_pages([related, exact], "renaming")["results"][0]["id"] == "renaming"
    assert not any("defined-symbol" in row["reasons"] for row in rank_pages([exact], "renamed")["results"])


@pytest.mark.parametrize("noun,query", [
    ("serialization", "serialized"), ("serialisation", "serialised"),
    ("serializations", "serializing"), ("normalization", "normalizing"),
    ("classification", "classifies"), ("verification", "verifying"),
    ("identification", "identified"), ("modification", "modified"),
    ("simplification", "simplifies"), ("notification", "notified"),
])
def test_nominal_prose_family_retains_original_text_and_source_qualification(noun, query):
    content = f"# Engine\n\n## Description\n{noun.capitalize()} preserves the record boundary.\n"
    owner = page("engine", content)
    original = deepcopy(owner)
    result = rank_pages([owner], query)
    match = result["results"][0]
    assert match["path"] == owner["path"]
    assert match["provenance"]["content_sha256"] == hashlib.sha256(content.encode()).hexdigest()
    assert "defined-symbol" not in match["reasons"]
    assert match["matched_section_locations"][0]["heading_path"] == ["Engine", "Description"]
    assert "live comparison not performed" in match["provenance"]["qualification"]
    assert owner == original


@pytest.mark.parametrize("body", [
    "## Imports\nSerialization helpers.",
    "## Functions\n| Function | Signature | Description |\n|---|---|---|\n| `serialization` | `serialization(value)` | Boundary operation. |",
    "## Description\n`serialization` is an identifier.",
    "## Description\n```text\nSerialization\n```",
    "## Description\nSérialization is an unrelated Unicode word.",
])
def test_nominal_expansion_does_not_promote_inventory_identifiers_or_code(body):
    assert rank_pages([page("engine", body)], "serialized")["results"] == []


def test_definition_description_prose_expands_without_aliasing_the_defined_symbol():
    owner = page("engine", "## Functions\n| Function | Signature | Description |\n|---|---|---|\n| `snapshot` | `snapshot(value)` | Canonical serialization. |\n")
    exact = page("serialized", "## Description\nUnrelated operation.\n")
    result = rank_pages([owner, exact], "serialized")
    assert result["results"][0]["path"] == exact["path"]
    derived = next(row for row in result["results"] if row["path"] == owner["path"])
    assert "defined-symbol" not in derived["reasons"]
    assert derived["matched_sections"] == [["Functions"]]
    assert rank_pages([owner], "snapshot")["results"][0]["reasons"][0] == "defined-symbol"


def test_word_form_matching_is_approximate_navigation_not_a_semantic_answer():
    owner = page("retention", "## Notes\nDeletion retains referenced payloads.\n")
    assert rank_pages([owner], "radiation dosage orbital navigation")["results"] == []
    result = rank_pages([owner], "deleted referenced payloads")
    assert result["results"] and not {"answer", "correct", "verified"} & result.keys()
    assert "lexical-discovery-candidate" in result["results"][0]["provenance"]["qualification"]


def test_strong_diagnostic_prose_links_retrieve_only_captured_implementation_targets():
    guide = page("diagnosis", "# Diagnosis\n\n## Troubleshooting\nAmber checkpoint fingerprint differs. Inspect [owner](../modules/opaque.md).\n", kind="guides")
    owner = page("opaque", "# Opaque\n\n## Description\nValidate boundary admission.\n")
    original = deepcopy([guide, owner])
    result = rank_pages([guide, owner], "amber checkpoint fingerprint")
    linked = next(row for row in result["results"] if row["path"] == owner["path"])
    assert linked["matched_sections"] == [] and linked["matched_section_locations"] == []
    assert linked["linked_evidence"] == [{
        "path": guide["path"], "content_sha256": hashlib.sha256(guide["content"].encode()).hexdigest(),
        "section_locator": "llm-wiki://guides/diagnosis#section/Diagnosis~1/Troubleshooting~1", "target_path": owner["path"],
    }]
    assert linked["provenance"]["qualification"] == "linked-discovery-candidate; live comparison not performed"
    assert [guide, owner] == original
    assert rank_pages([guide], "amber checkpoint fingerprint")["total"] == 1


@pytest.mark.parametrize("body", [
    "## Imports\nAmber checkpoint fingerprint [owner](../modules/opaque.md).",
    "## Troubleshooting\nAmber checkpoint fingerprint.\n```md\n[owner](../modules/opaque.md)\n```",
    "## Troubleshooting\nAmber checkpoint fingerprint [owner](https://remote.invalid/modules/opaque.md).",
    "## Troubleshooting\nAmber checkpoint fingerprint [owner](../../../modules/opaque.md).",
])
def test_inventory_fenced_external_or_escaping_links_do_not_invent_candidates(body):
    guide = page("diagnosis", body, kind="guides")
    owner = page("opaque", "# Opaque\nValidate admission boundary.")
    assert not any(row["path"] == owner["path"] for row in rank_pages([owner, guide], "amber checkpoint fingerprint")["results"])


def test_linked_candidates_keep_exact_identity_precedence_and_indexing_hash_custody():
    guide = page("guide", "## Troubleshooting\nAmber checkpoint fingerprint [owner](../modules/opaque.md).", kind="guides")
    raw = "# Opaque\nAdmission boundary.\n"
    indexed = raw + "\n## Selected source indexing evidence\nStatic declaration.\n"
    owner = page("opaque", indexed, indexing={"original_wiki_content_sha256":hashlib.sha256(raw.encode()).hexdigest()})
    linked = next(row for row in rank_pages([guide, owner], "amber checkpoint fingerprint")["results"] if row["id"]=="opaque")
    assert linked["provenance"]["content_sha256"] == hashlib.sha256(raw.encode()).hexdigest()
    assert linked["provenance"]["indexed_content_sha256"] == hashlib.sha256(indexed.encode()).hexdigest()
    exact = page("amber checkpoint fingerprint", "Nothing here.")
    assert rank_pages([guide,owner,exact], "amber checkpoint fingerprint")["results"][0]["id"]==exact["id"]
