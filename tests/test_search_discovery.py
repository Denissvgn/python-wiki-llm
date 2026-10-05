"""Pure discovery preserves candidate identity, narrative and captured review."""

from copy import deepcopy
import hashlib
import json

import pytest

from llm_wiki_cli.services import search_discovery as discovery
from llm_wiki_cli.services.search_discovery import DiscoveryError, enrich_search


def _page(name="owner", kind="modules", content=None):
    return {"kind": kind, "id": name, "path": f"{kind}/{name}.md", "uri": f"llm-wiki://{kind}/{name}",
            "title": name, "content": content or "# Owner\n\n## Description\nCaptured prose.\n"}


def _native(concepts=None, *, complete=True):
    return {"availability": "scoped", "reason": None, "root_hash": "sha256:" + "a" * 64,
            "lookup_complete": complete, "validation_scope": "selected-committed-collections",
            "whole_store_validated": False, "concepts": concepts or []}


def _concept(page, source=None, locator=None):
    basis = {"source_path": source, "source_content_hash": "sha256:" + "b" * 64} if source else None
    return {"locator": locator or page["uri"], "document": {"canonical_path": page["path"]},
            "facets": {"structure": {"basis": basis}, "semantics": {"verification": "not-evaluated"}},
            "lifecycle": "active"}


def _reviews(by_path=None):
    if by_path is None:
        return {"availability": "unadopted", "reason": None, "adoption_id": None,
                "state_hash": None, "by_path": {}}
    return {"availability": "ready", "reason": None, "adoption_id": "owned-adoption",
            "state_hash": "sha256:" + "c" * 64, "by_path": by_path}


def _row(path, **extra):
    return {"record_id": "owned-record", "target": {"canonical_path": path, "section_locator": "exact-section"},
            "recorded_status": "pending", "mapping": {"state": "resolved", "candidates": []},
            "reasons": ["source-basis-changed"], "effective_status": None,
            "coordinate": {"source_path": "selected/owner.py", "owner": "Owner", "occurrence": 1},
            "recorded_basis": {"source_hash": "sha256:" + "d" * 64},
            "qualification": "snapshot", "governance_effect": "none", "expected_basis": None,
            "basis_available": False, "acknowledgment": {"actor": {"kind": "agent", "actor_id": "recorded-agent"}},
            "acknowledgment_history": [{"actor": {"kind": "agent", "actor_id": "recorded-agent"}}],
            "history_bounds": {"total": 3, "returned": 1, "omitted": 2, "truncated": True}, **extra}


def _inputs(pages=None, *, mappings=None, native=None, reviews=None, truncated=False):
    pages = pages or [_page()]
    matches = [{key: value for key, value in page.items() if key != "content"} for page in pages]
    for page, match in zip(pages, matches):
        match.update(snippet="flat snippet", reasons=["lexical-candidate"],
                     provenance={"content_sha256": hashlib.sha256(page["content"].encode()).hexdigest()})
    total = len(matches) + int(truncated)
    bound = {"total": total, "returned": len(matches), "truncated": truncated}
    result = {"query": "a fuzzy symptom", "mode": "ranked", "ranking": "lexical-v2",
              "corpus_id": "sha256:" + "e" * 64, "results": matches, "total": total,
              "count": len(matches), "returned": len(matches), "truncated": truncated,
              "bounds": {"results": bound}, "resource_limits": {"pages": 10_000, "bytes": 67_108_864}}
    return result, {"pages_by_path": {page["path"]: page for page in pages},
                    "owner_mappings": mappings or {}, "native_payload": native or _native(),
                    "recorded_reviews": reviews or _reviews()}


def test_same_owned_source_groups_every_member_without_changing_flat_result_or_inputs():
    module, entity = _page(), _page("Owner", "entities")
    pages = [module, entity]
    mappings = {page["path"]: {"scope": "module" if page is module else "entity",
                              "source_path": "selected/owner.py"} for page in pages}
    result, kwargs = _inputs(pages, mappings=mappings, truncated=True)
    before = deepcopy((result, kwargs))
    enriched = enrich_search(result, **kwargs)
    metadata = enriched.pop("discovery")
    assert enriched == result
    assert (result, kwargs) == before
    assert metadata["groups"] == [{"key": {"kind": "source", "value": "selected/owner.py"}, "members": [0, 1]}]
    assert metadata["bounds"]["members"] == result["bounds"]["results"]
    assert metadata["bounds"]["groups"] == {"total": 1, "returned": 1, "truncated": False}
    assert [member["result_index"] for member in metadata["members"]] == [0, 1]
    enriched["results"][0]["provenance"]["content_sha256"] = "caller mutation"
    assert (result, kwargs) == before


def test_contradictory_repeated_and_unknown_sections_keep_exact_occurrences_and_ownership():
    page = _page(content="# Owner\n\n## Description\nAlways permit.\n\n## Description\nAlways reject.\n"
                         "\n## Behavior\nNever discard pending prose.\n\n## Imports\nGENERATED_IMPORT_SENTINEL\n")
    result, kwargs = _inputs([page])
    member = enrich_search(result, **kwargs)["discovery"]["members"][0]
    sections = member["sections"]
    assert [section["ownership"] for section in sections] == ["semantic", "unknown", "unknown"]
    assert sections[0]["occurrence_path"] == [1, 1]
    assert sections[1]["occurrence_path"] == [1, 2]
    assert sections[0]["locator"] != sections[1]["locator"]
    assert "Always permit" in sections[0]["snippet"] and "Always reject" in sections[1]["snippet"]
    assert all("GENERATED_IMPORT_SENTINEL" not in section["snippet"] for section in sections)
    assert member["section_scope"] == "useful-non-generated-narrative"


def test_mixed_table_descriptions_remain_narrative_with_original_owner_classification():
    page = _page(content="# Owner\n\n## Functions\n\n| Name | Description |\n|---|---|\n| f | Reject stale prose. |\n")
    result, kwargs = _inputs([page])
    section = enrich_search(result, **kwargs)["discovery"]["members"][0]["sections"][0]
    assert section["ownership"] == "mixed"
    assert "Reject stale prose" in section["snippet"]


def test_eight_section_and_240_character_bounds_preserve_truthful_omissions():
    page = _page(content="# Owner\n" + "".join(f"\n## Claim {index}\n" + "café " * 200 for index in range(10)))
    result, kwargs = _inputs([page])
    member = enrich_search(result, **kwargs)["discovery"]["members"][0]
    assert member["section_bounds"] == {"total": 10, "returned": 8, "truncated": True}
    assert len(member["sections"]) == 8
    assert all(len(section["snippet"]) == 240 for section in member["sections"])
    assert all(section["snippet_bounds"]["total"] > 240 and section["snippet_bounds"]["returned"] == 240
               and section["snippet_bounds"]["truncated"] for section in member["sections"])
    assert len({section["locator"] for section in member["sections"]}) == 8


def test_guide_preamble_keeps_machine_locator_and_separate_physical_hash_and_uri():
    page = _page("guide", "guides", "Historical intro.\n\n# Guide\n\n## Café / limit\nA qualified claim.\n")
    result, kwargs = _inputs([page])
    member = enrich_search(result, **kwargs)["discovery"]["members"][0]
    assert member["content_sha256"] == hashlib.sha256(page["content"].encode()).hexdigest()
    assert member["uri"] == page["uri"]
    assert member["sections"][0]["locator"].endswith("#section/@preamble")
    assert member["sections"][-1]["locator"].endswith("Caf%C3%A9%20%2F%20limit~1")
    assert member["sections"][-1]["page_locator"] == page["uri"]


@pytest.mark.parametrize("state", ["unique", "missing", "ambiguous", "unavailable"])
def test_native_exact_outcomes_never_resolve_fuzzy_candidate_or_execute_next_read(state):
    page = _page()
    concepts = [] if state in {"missing", "unavailable"} else [_concept(page)]
    if state == "ambiguous":
        concepts.append(_concept(page, locator="llm-wiki://modules/other"))
    native = _native(concepts)
    if state == "unavailable":
        native = {**native, "availability": "unavailable", "reason": "unsupported-native-layout",
                  "root_hash": None, "lookup_complete": False, "validation_scope": None}
    result, kwargs = _inputs([page], native=native)
    member = enrich_search(result, **kwargs)["discovery"]["members"][0]
    assert member["identity_state"] == "candidate" and member["native"]["state"] == state
    assert member["next_read"] == {"operation": "inspect_concept", "locator_or_exact_route": page["path"],
                                   "live": False, "selection_required": True, "resolution_performed": False}
    assert member["qualification"]["source_comparison"] == "not-performed"
    assert member["qualification"]["runtime_behavior"] == "not-evaluated"


def test_incomplete_native_lookup_never_claims_unique_or_absence():
    page = _page()
    result, kwargs = _inputs([page], native=_native([_concept(page)], complete=False))
    native = enrich_search(result, **kwargs)["discovery"]["members"][0]["native"]
    assert native["state"] == "unavailable" and native["locator"] is None
    assert native["reason"] == "native-lookup-incomplete" and native["bounds"]["truncated"]
    assert native["bounds"] == {"total": None, "returned": 1, "truncated": True, "total_known": False}


def test_source_conflict_falls_back_to_exact_page_and_retains_mapping_and_matches():
    page = _page()
    mapping = {page["path"]: {"scope": "module", "source_path": "selected/a.py"}}
    result, kwargs = _inputs([page], mappings=mapping, native=_native([_concept(page, "selected/b.py")]))
    metadata = enrich_search(result, **kwargs)["discovery"]
    assert metadata["groups"][0]["key"] == {"kind": "page", "value": page["path"]}
    assert metadata["members"][0]["owner"] == {"state": "conflicting", "source_path": None,
                                               "mapping": mapping[page["path"]],
                                               "conflicting_sources": ["selected/a.py", "selected/b.py"]}
    assert metadata["members"][0]["native"]["matches"] == [page["uri"]]


def test_source_free_unique_concept_group_and_page_fallback_are_separate():
    page, other = _page(), _page("unowned")
    result, kwargs = _inputs([page, other], native=_native([_concept(page)]))
    groups = enrich_search(result, **kwargs)["discovery"]["groups"]
    assert groups == [{"key": {"kind": "concept", "value": page["uri"]}, "members": [0]},
                      {"key": {"kind": "page", "value": other["path"]}, "members": [1]}]


def test_titles_symbols_and_source_links_never_confer_source_ownership():
    pages = [_page("a", content="# Same\n[Source](selected/owner.py)\n## Description\nSame symbol.\n"),
             _page("b", content="# Same\n## Description\nSame symbol.\n")]
    result, kwargs = _inputs(pages)
    metadata = enrich_search(result, **kwargs)["discovery"]
    assert len(metadata["groups"]) == 2
    assert all(member["owner"]["state"] == "page-only" for member in metadata["members"])


def test_recorded_pending_actor_basis_reasons_history_and_truncation_are_preserved():
    page = _page()
    report = {"records": [_row(page["path"])], "bounds": {"total": 2, "returned": 1, "omitted": 1, "truncated": True}}
    result, kwargs = _inputs([page], reviews=_reviews({page["path"]: report}))
    metadata = enrich_search(result, **kwargs)["discovery"]
    recorded = metadata["members"][0]["recorded_review"]
    assert recorded["records"] == report["records"] and recorded["bounds"] == report["bounds"]
    assert recorded["basis"] == "snapshot" and recorded["live_evaluation_performed"] is False
    assert metadata["recorded_review"]["current_acknowledgment"] == "not-compared"
    assert "native_prose_coherent" not in recorded and "requires_sync" not in recorded


def test_ambiguous_review_original_target_and_all_candidate_targets_stay_visible():
    page = _page()
    row = _row("modules/old.md", mapping={"state": "ambiguous", "candidates": [
        {"target": {"canonical_path": page["path"], "section_locator": "candidate-one"}},
        {"target": {"canonical_path": "modules/other.md", "section_locator": "candidate-two"}}]})
    report = {"records": [row], "bounds": {"total": 1, "returned": 1, "truncated": False}}
    result, kwargs = _inputs([page], reviews=_reviews({page["path"]: report}))
    assert enrich_search(result, **kwargs)["discovery"]["members"][0]["recorded_review"]["records"] == [row]


@pytest.mark.parametrize("extra", [{"native_prose_coherent": True}, {"requires_sync": False},
                                   {"effective_status": "acknowledged"}, {"basis_available": True},
                                   {"qualification": "current-capture"}, {"governance_effect": "accepted"}])
def test_review_cannot_import_unproven_current_readiness_or_upgrade_recorded_authority(extra):
    page = _page()
    report = {"records": [_row(page["path"], **extra)], "bounds": {"total": 1, "returned": 1, "truncated": False}}
    result, kwargs = _inputs([page], reviews=_reviews({page["path"]: report}))
    with pytest.raises(DiscoveryError) as failure:
        enrich_search(result, **kwargs)
    assert failure.value.code == "discovery-invalid-input"


@pytest.mark.parametrize("corruption", ["missing-page", "hash", "duplicate", "foreign-review", "already-enriched", "unsafe-source", "bounds", "uri"])
def test_malformed_exact_capture_fails_closed_with_safe_diagnostic(corruption):
    page = _page()
    result, kwargs = _inputs([page])
    if corruption == "missing-page":
        kwargs["pages_by_path"] = {}
    elif corruption == "hash":
        result["results"][0]["provenance"]["content_sha256"] = "stale"
    elif corruption == "duplicate":
        result["results"].append(deepcopy(result["results"][0]))
    elif corruption == "foreign-review":
        kwargs["recorded_reviews"] = _reviews({page["path"]: {"records": [_row("modules/other.md")],
            "bounds": {"total": 1, "returned": 1, "truncated": False}}})
    elif corruption == "already-enriched":
        result["discovery"] = {}
    elif corruption == "unsafe-source":
        kwargs["owner_mappings"] = {page["path"]: {"scope": "module", "source_path": "../SECRET-CONTENT.py"}}
    elif corruption == "bounds":
        result["bounds"]["results"]["returned"] = True
    elif corruption == "uri":
        result["results"][0]["uri"] = page["uri"] = "https://outside.example/SECRET-CONTENT"
    with pytest.raises(DiscoveryError) as failure:
        enrich_search(result, **kwargs)
    assert failure.value.code == "discovery-invalid-input"
    assert "SECRET-CONTENT" not in str(failure.value)


def test_entire_metadata_cap_rejects_without_dropping_recorded_qualifiers():
    page = _page()
    row = _row(page["path"], reasons=["stale-qualification" * 20_000])
    report = {"records": [row], "bounds": {"total": 1, "returned": 1, "truncated": False}}
    result, kwargs = _inputs([page], reviews=_reviews({page["path"]: report}))
    before = deepcopy((result, kwargs))
    with pytest.raises(DiscoveryError) as failure:
        enrich_search(result, **kwargs)
    assert failure.value.code == "discovery-output-limit"
    assert failure.value.required_bytes is not None and failure.value.required_bytes > 262_144
    assert "stale-qualification" not in str(failure.value)
    assert (result, kwargs) == before


def test_exact_complete_canonical_enrichment_bytes_enforce_admission_boundary(monkeypatch):
    result, kwargs = _inputs()
    metadata = enrich_search(result, **kwargs)["discovery"]
    size = len(json.dumps(metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode())
    # The serialized ceiling itself has fewer digits when lowered; derive the
    # complete new envelope size with that actual declared cap included.
    metadata["limits"]["serialized_bytes"] = size
    minimum = len(json.dumps(metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
    monkeypatch.setattr(discovery, "MAX_DISCOVERY_BYTES", minimum)
    assert enrich_search(result, **kwargs)["discovery"]
    monkeypatch.setattr(discovery, "MAX_DISCOVERY_BYTES", minimum - 1)
    with pytest.raises(DiscoveryError, match="serialized byte limit"):
        enrich_search(result, **kwargs)


def test_recorded_source_location_unknown_qualification_remains_captured_and_inert():
    page = _page()
    location = {"path": "selected/owner.py", "line": None, "end_line": None, "qualification": "not-observed"}
    report = {"records": [_row(page["path"], source_location=location)],
              "bounds": {"total": 1, "returned": 1, "truncated": False}}
    result, kwargs = _inputs([page], reviews=_reviews({page["path"]: report}))
    recorded = enrich_search(result, **kwargs)["discovery"]["members"][0]["recorded_review"]
    assert recorded["records"][0]["source_location"] == location
    assert recorded["live_evaluation_performed"] is False


def test_recorded_manifest_source_hash_and_tombstone_remain_historical_with_native_missing():
    page = _page()
    source = {"basis": "manifest-snapshot", "source_content_hash": "sha256:" + "f" * 64,
              "availability": "recorded", "live_comparison_performed": False,
              "tombstone": {"reason": "source-missing", "unknown_reason": None}}
    result, kwargs = _inputs([page], mappings={page["path"]: {"scope": "module", "source_path": "selected/deleted.py",
                                                           "recorded_source": source}})
    member = enrich_search(result, **kwargs)["discovery"]["members"][0]
    assert member["qualification"]["recorded_source"] == source
    assert member["qualification"]["source_comparison"] == "not-performed"
    assert member["native"]["state"] == "missing"


@pytest.mark.parametrize("recorded", [True, False])
def test_recorded_source_never_permits_live_comparison_flag(recorded):
    page = _page()
    source = {"basis": "manifest-snapshot", "source_content_hash": "sha256:" + "f" * 64 if recorded else None,
              "availability": "recorded" if recorded else "unrecorded", "live_comparison_performed": True}
    result, kwargs = _inputs([page], mappings={page["path"]: {"scope": "module", "source_path": "selected/owner.py",
                                                           "recorded_source": source}})
    with pytest.raises(DiscoveryError) as failure:
        enrich_search(result, **kwargs)
    assert failure.value.code == "discovery-invalid-input"


@pytest.mark.parametrize("malformed", ["counts", "provenance", "mapping", "native-availability", "native-semantics", "native-source-hash",
                                      "review-availability", "surrogate-content", "history"])
def test_malformed_type_shapes_refuse_with_fixed_errors(malformed):
    page = _page()
    result, kwargs = _inputs([page])
    if malformed == "counts":
        result["returned"] = True
    elif malformed == "provenance":
        result["results"][0]["provenance"] = False
    elif malformed == "mapping":
        kwargs["owner_mappings"] = {page["path"]: {"scope": "module", "source_path": []}}
    elif malformed == "native-availability":
        kwargs["native_payload"]["availability"] = []
    elif malformed == "native-semantics":
        concept = _concept(page)
        concept["facets"]["semantics"] = False
        kwargs["native_payload"] = _native([concept])
    elif malformed == "native-source-hash":
        concept = _concept(page, "selected/owner.py")
        concept["facets"]["structure"]["basis"]["source_content_hash"] = {"invalid": "identity"}
        kwargs["native_payload"] = _native([concept])
    elif malformed == "review-availability":
        kwargs["recorded_reviews"]["availability"] = []
    elif malformed == "surrogate-content":
        kwargs["pages_by_path"][page["path"]]["content"] = "\ud800"
    elif malformed == "history":
        row = _row(page["path"])
        row["history_bounds"]["omitted"] = -1
        kwargs["recorded_reviews"] = _reviews({page["path"]: {"records": [row], "bounds": {
            "total": 1, "returned": 1, "truncated": False}}})
    with pytest.raises(DiscoveryError) as failure:
        enrich_search(result, **kwargs)
    assert failure.value.code == "discovery-invalid-input"
