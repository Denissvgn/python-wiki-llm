"""Synthetic scorer checks; never read historical or held-out provider evidence."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import json
from typing import Any

import pytest

from tests.developer_value.retrieval_experiment import (
    CATEGORIES,
    CaptureBinding,
    Ratio,
    adoption_gate,
    corpus_digest,
    frozen_results_digest,
    score_split,
    validate_corpus,
)


def corpus() -> dict[str, Any]:
    owners = [f"{letter}.py" for letter in "abcdef"]
    fixtures = {f"fixture-{index}": {
        "id": f"fixture-{index}", "type": kind, "source_root": "src",
        "files": {owner: f"def {owner[:-3]}(): pass\n" for owner in owners},
        "authored_content": {owner: {"Behavior": f"{owner} accepts only current input."}
                             for owner in owners},
    } for index, kind in enumerate(("library", "command", "service"))}
    queries = []
    for split in ("development", "confirmation"):
        for category in CATEGORIES:
            for index in range(4):
                answerable = category != "unanswerable"
                queries.append({
                    "id": f"{split}-{category}-{index}", "fixture": f"fixture-{index % 3}",
                    "category": category, "split": split,
                    "query": f"Independent {split} {category} question {index}",
                    "expected_owners": ["a.py"] if answerable else [],
                    "expected_sections": [{"owner": "a.py", "heading": "Behavior",
                                           "quote": "accepts only current input"}] if answerable else [],
                    "expected_top_one_owner": "a.py" if category == "exact-symbol" else None,
                    "relevancecite": "Synthetic authored fixture behavior",
                })
    return {"corpus_id": "scorer-synthetic-40", "version": 1, "categories": list(CATEGORIES),
            "fixture_types": ["library", "command", "service"], "fixtures": fixtures,
            "queries": queries}


def aliases() -> dict[str, dict[str, str]]:
    pages = {f"entities/{letter}.md": f"{letter}.py" for letter in "abcdef"}
    pages["modules/a.md"] = "a.py"
    pages["modules/b.md"] = "b.py"
    return {f"fixture-{index}": dict(pages) for index in range(3)}


def capture(spec: dict[str, Any], split: str = "development", *,
            capture_id: str = "baseline-capture") -> dict[str, Any]:
    return {
        "corpus_id": spec["corpus_id"], "corpus_sha256": corpus_digest(spec),
        "provider": "synthetic-provider", "selected_source": "source-plan-sha256",
        "capture_id": capture_id, "arm": "no-source-augmentation", "split": split,
        "rows": [{"query_id": query["id"], "limit": 100, "error": None,
                  "results": ([] if query["category"] == "unanswerable" else
                              [{"path": "entities/a.md", "section": "Behavior", "snippet": "candidate"}]),
                  "definitive_claim": False, "wall_ns": 40, "response_bytes": 50,
                  "truncated": False}
                 for query in spec["queries"] if query["split"] == split],
    }


def binding(spec: dict[str, Any], observations: dict[str, Any],
            mapping: dict[str, dict[str, str]]) -> CaptureBinding:
    return CaptureBinding(corpus_id=spec["corpus_id"], corpus_sha256=corpus_digest(spec),
                          provider=observations["provider"], selected_source=observations["selected_source"],
                          capture_id=observations["capture_id"], arm=observations["arm"],
                          results_sha256=frozen_results_digest(observations),
                          aliases_sha256=frozen_results_digest(mapping))


def score(spec: dict[str, Any], observations: dict[str, Any],
          mapping: dict[str, dict[str, str]] | None = None):
    mapping = aliases() if mapping is None else mapping
    return score_split(spec, observations, mapping, observations["split"],
                       expected=binding(spec, observations, mapping))


def test_balanced_corpus_and_query_section_denominators() -> None:
    spec = corpus()
    validate_corpus(spec)
    results = score(spec, capture(spec))
    assert len(results.query_ids) == 20
    assert results.owner_recall == Ratio(16, 16)
    assert results.owner_precision == Ratio(16, 16)
    assert results.emitted_precision == Ratio(16, 16)
    assert results.exact_correct == results.exact_total == 4
    assert results.unanswerable_claims_observed == results.unanswerable_total == 4
    assert all(row.expected_sections == row.emitted_section_hits == 1
               for row in results.queries if row.category != "unanswerable")
    assert results.to_dict()["owner_recall"]["value"] == 1.0


@pytest.mark.parametrize("change", ["balance", "id", "query", "owner", "section", "quote", "top_one", "unanswerable"])
def test_invalid_predeclared_corpus_is_rejected(change: str) -> None:
    spec = corpus()
    query = spec["queries"][0]
    if change == "balance":
        query["split"] = "confirmation"
    elif change == "id":
        query["id"] = spec["queries"][1]["id"]
    elif change == "query":
        query["query"] = " " + spec["queries"][1]["query"].upper() + " "
    elif change == "owner":
        query["expected_owners"] = ["outside.py"]
    elif change == "section":
        query["expected_sections"][0]["heading"] = "Missing"
    elif change == "quote":
        query["expected_sections"][0]["quote"] = "invented excerpt"
    elif change == "top_one":
        query["expected_top_one_owner"] = "b.py"
    else:
        spec["queries"][16]["expected_owners"] = ["a.py"]
    with pytest.raises(ValueError):
        validate_corpus(spec)


def test_list_fixture_schema_is_supported() -> None:
    spec = corpus()
    spec["fixtures"] = list(spec["fixtures"].values())
    validate_corpus(spec)
    assert score(spec, capture(spec)).owner_recall.value == 1


def test_deduplicate_all_results_recovers_rank_six_but_safeguard_keeps_first_five() -> None:
    spec = corpus()
    observations = capture(spec)
    raw = [{"path": "entities/b.md"}, {"path": "modules/b.md"},
           {"path": "entities/b.md"}, {"path": "modules/b.md"},
           {"path": "entities/b.md"}, {"path": "entities/a.md", "section": "Behavior"}]
    observations["rows"][4]["results"] = raw
    results = score(spec, observations)
    row = results.queries[4]
    assert row.owner_top5 == ("b.py", "a.py")
    assert row.owner_hits == 1
    assert row.emitted_owner_hits == row.emitted_page_hits == row.emitted_section_hits == 0
    assert [page.path for page in row.emitted_top5] == [page["path"] for page in raw[:5]]
    assert [page.rank for page in row.emitted_top5] == [1, 2, 3, 4, 5]
    assert len(row.all_pages) == 6
    assert results.owner_recall == Ratio(16, 16)
    assert results.owner_precision == Ratio(16, 17)
    assert results.emitted_recall == Ratio(15, 16)
    assert results.emitted_precision == Ratio(15, 20)
    raw[0]["path"] = "entities/a.md"
    assert row.emitted_top5[0].path == "entities/b.md"
    assert json.loads(row.emitted_top5[0].raw_json) == {"path": "entities/b.md"}


def test_duplicate_relevant_pages_affect_page_precision_without_double_recall() -> None:
    spec = corpus()
    observations = capture(spec)
    observations["rows"][4]["results"] = [{"path": "entities/a.md"}, {"path": "modules/a.md"},
                                            {"path": "entities/b.md"}]
    result = score(spec, observations)
    assert result.owner_recall == result.emitted_recall == Ratio(16, 16)
    assert result.owner_precision == Ratio(16, 17)
    assert result.emitted_precision == Ratio(17, 18)


def test_unmapped_pages_are_distinct_precision_negatives_and_fixture_scoped() -> None:
    spec = corpus()
    observations = capture(spec)
    observations["rows"][4]["results"] = [{"path": "other/a.md"}, {"path": "other/b.md"},
                                            {"path": "entities/a.md"}]
    mapping = aliases()
    mapping["fixture-0"]["entities/a.md"] = "b.py"
    result = score(spec, observations, mapping)
    assert result.queries[4].owner_top5 == ("unmapped:other/a.md", "unmapped:other/b.md", "b.py")
    assert result.queries[4].owner_hits == 0
    assert result.owner_precision.denominator == 18
    assert result.exact_correct == 2  # Only fixture-0's exact cases lose top-one correctness.


def test_missing_errors_and_empty_output_stay_in_recall_denominator() -> None:
    spec = corpus()
    observations = capture(spec)
    del observations["rows"][0]
    observations["rows"][0]["error"] = "provider failure"
    observations["rows"][1]["results"] = []
    result = score(spec, observations)
    assert result.owner_recall == Ratio(13, 16)
    assert result.owner_precision == Ratio(13, 14)
    assert result.exact_correct == 1
    assert result.missing == result.errors == 1
    assert result.queries[0].status == "missing"
    assert result.queries[1].status == "error"
    assert result.queries[1].all_pages[0].path == "entities/a.md"


def test_unknown_claims_are_preserved_separately_from_lexical_candidates() -> None:
    spec = corpus()
    observations = capture(spec)
    rows = observations["rows"]
    rows[16]["results"] = [{"path": "entities/b.md", "snippet": "qualified lexical candidate"}]
    del rows[16]["definitive_claim"]
    rows[17]["error"] = "capture failed"
    rows[18]["definitive_claim"] = True
    del rows[19]
    result = score(spec, observations)
    assert result.unanswerable_total == 4
    assert result.unanswerable_claims_observed == 1
    assert result.unanswerable_definitive_claims == 1
    assert result.unanswerable_candidates == result.unanswerable_candidate_pages == 1
    assert result.queries[16].definitive_claim is None
    assert result.queries[17].definitive_claim is None
    assert result.queries[19].definitive_claim is None


def test_null_precision_is_explicit_for_wholly_empty_answerable_output() -> None:
    spec = corpus()
    observations = capture(spec, "confirmation")
    for row in observations["rows"]:
        row["results"] = []
    result = score(spec, observations)
    assert result.owner_recall == Ratio(0, 16)
    assert result.owner_precision.value is None
    assert result.emitted_precision.to_dict()["value"] is None
    decision = adoption_gate(result, replace(result, binding=replace(result.binding, capture_id="candidate")),
                             controls={"correctness": True, "selection": True, "exact_development": True})
    assert not decision.eligible
    assert "owner_precision_noninferiority" in decision.reasons
    assert "emitted_precision_noninferiority" in decision.reasons


@pytest.mark.parametrize("field", ["corpus_id", "corpus_sha256", "provider", "selected_source", "capture_id", "arm"])
def test_all_capture_identity_fields_are_externally_pinned(field: str) -> None:
    spec = corpus()
    observations = capture(spec)
    mapping = aliases()
    pin = binding(spec, observations, mapping)
    observations[field] = "substituted"
    # Even if a caller re-hashes substituted bytes, independent identity remains pinned.
    pin = replace(pin, results_sha256=frozen_results_digest(observations))
    with pytest.raises(ValueError, match="identity mismatch"):
        score_split(spec, observations, mapping, "development", expected=pin)


def test_raw_results_aliases_and_whole_corpus_hash_are_pinned() -> None:
    spec = corpus()
    observations = capture(spec)
    mapping = aliases()
    pin = binding(spec, observations, mapping)
    altered = deepcopy(observations)
    altered["rows"][0]["results"][0]["snippet"] = "changed raw provider output"
    with pytest.raises(ValueError, match="pinned capture"):
        score_split(spec, altered, mapping, "development", expected=pin)
    mapping["fixture-0"]["entities/a.md"] = "b.py"
    with pytest.raises(ValueError, match="manifest projection"):
        score_split(spec, observations, mapping, "development", expected=pin)
    spec["queries"][20]["query"] = "Changed confirmation query without scoring it"
    with pytest.raises(ValueError, match="corpus differs"):
        score_split(spec, observations, aliases(), "development", expected=pin)


@pytest.mark.parametrize("bad", ["/absolute.md", "../escape.md", "entities/../../escape.md", "entities//a.md", "entities\\a.md"])
def test_emitted_paths_are_not_guessed_or_normalized(bad: str) -> None:
    spec = corpus()
    observations = capture(spec)
    observations["rows"][0]["results"][0]["path"] = bad
    with pytest.raises(ValueError, match="path"):
        score(spec, observations)


def test_alias_ambiguity_and_owner_outside_fixture_are_rejected() -> None:
    spec = corpus()
    observations = capture(spec)
    mapping: Any = aliases()
    mapping["fixture-0"]["entities/a.md"] = ["a.py", "b.py"]
    with pytest.raises(ValueError, match="path"):
        score(spec, observations, mapping)
    mapping = aliases()
    mapping["fixture-0"]["entities/a.md"] = "other.py"
    with pytest.raises(ValueError, match="outside selected"):
        score(spec, observations, mapping)


def test_split_is_explicit_and_duplicate_foreign_query_ids_reject() -> None:
    spec = corpus()
    observations = capture(spec)
    with pytest.raises(ValueError, match="split must be explicit"):
        score_split(spec, observations, aliases(), "all", expected=binding(spec, observations, aliases()))
    observations["rows"].append(deepcopy(observations["rows"][0]))
    with pytest.raises(ValueError, match="duplicate or out-of-split"):
        score(spec, observations)
    observations["rows"][-1]["query_id"] = spec["queries"][20]["id"]
    with pytest.raises(ValueError, match="duplicate or out-of-split"):
        score(spec, observations)


def test_limits_truncation_and_resource_metadata_remain_visible() -> None:
    spec = corpus()
    observations = capture(spec)
    observations["rows"][4].update(limit=1, truncated=True, response_bytes=111, wall_ns=222)
    result = score(spec, observations)
    assert json.loads(result.queries[4].metadata_json)["truncated"] is True
    assert json.loads(result.queries[4].metadata_json)["response_bytes"] == 111
    assert result.owner_recall.denominator == 16
    observations["rows"][4]["results"].append({"path": "entities/b.md"})
    with pytest.raises(ValueError, match="limit"):
        score(spec, observations)
    observations["rows"][4]["limit"] = 101
    with pytest.raises(ValueError, match="limit"):
        score(spec, observations)


def gate_pair():
    spec = corpus()
    # Twenty predeclared owner targets, with captured hits of 14 and 16.
    # Threshold cases must come from actual rows rather than edited summaries.
    for query in spec["queries"]:
        if query["split"] == "confirmation" and query["category"] == "symptom":
            query["expected_owners"].append("b.py")
            query["expected_sections"].append({"owner": "b.py", "heading": "Behavior",
                                               "quote": "accepts only current input"})
    baseline_capture = capture(spec, "confirmation")
    candidate_capture = capture(spec, "confirmation", capture_id="candidate-capture")
    for observations in (baseline_capture, candidate_capture):
        for row in observations["rows"][4:8]:
            row["results"].append({"path": "entities/c.md"})
    for row in baseline_capture["rows"][12:14]:
        row["results"] = [{"path": "entities/c.md"}]
    baseline = score(spec, baseline_capture)
    candidate = score(spec, candidate_capture)
    controls = {"correctness": True, "selection": True, "exact_development": True}
    return baseline, candidate, controls


def test_fraction_thresholds_accept_exact_boundary_without_float_rounding() -> None:
    baseline, candidate, controls = gate_pair()
    assert baseline.owner_recall == Ratio(14, 20)
    assert candidate.owner_recall == Ratio(16, 20)
    baseline_recall, candidate_recall = baseline.owner_recall.value, candidate.owner_recall.value
    assert baseline_recall is not None and candidate_recall is not None
    assert candidate_recall - baseline_recall == Fraction(1, 10)
    assert adoption_gate(baseline, candidate, controls=controls).eligible
    assert isinstance(candidate.corpus_json, str) and isinstance(candidate.capture_json, str)
    spec = json.loads(candidate.corpus_json)
    observations = json.loads(candidate.capture_json)
    observations["rows"][14]["results"] = [{"path": "entities/c.md"}]
    below = score(spec, observations)
    rejected = adoption_gate(baseline, below, controls=controls)
    assert not rejected.eligible and "owner_recall_gain" in rejected.reasons
    assert rejected.checks["candidate_score_custody"]


def test_authentic_precision_noninferiority_boundary_and_below_threshold() -> None:
    spec = corpus()
    selected = [query for query in spec["queries"] if query["split"] == "confirmation"]
    for query in selected[:14]:
        query["expected_owners"].append("b.py")
        query["expected_sections"].append({"owner": "b.py", "heading": "Behavior",
                                           "quote": "accepts only current input"})
    baseline_capture = capture(spec, "confirmation")
    candidate_capture = capture(spec, "confirmation", capture_id="candidate-capture")
    for row in baseline_capture["rows"][12:15]:
        row["results"] = [{"path": "entities/c.md"}]
    baseline_capture["rows"][15]["results"] = []
    candidate_capture["rows"][15]["results"] = [{"path": "entities/c.md"}]
    for row in candidate_capture["rows"][4:8]:
        row["results"].append({"path": "entities/c.md"})
    baseline, candidate = score(spec, baseline_capture), score(spec, candidate_capture)
    assert baseline.owner_recall == Ratio(12, 30) and candidate.owner_recall == Ratio(15, 30)
    assert baseline.owner_precision == baseline.emitted_precision == Ratio(12, 15)
    assert candidate.owner_precision == candidate.emitted_precision == Ratio(15, 20)
    controls = {"correctness": True, "selection": True, "exact_development": True}
    assert adoption_gate(baseline, candidate, controls=controls).eligible
    candidate_capture["rows"][8]["results"].append({"path": "entities/c.md"})
    below = score(spec, candidate_capture)
    rejected = adoption_gate(baseline, below, controls=controls)
    assert not rejected.eligible
    assert {"owner_precision_noninferiority", "emitted_precision_noninferiority"} <= set(rejected.reasons)
    assert rejected.checks["candidate_score_custody"]


@pytest.mark.parametrize("control", ["correctness", "selection", "exact_development"])
def test_correctness_and_selection_controls_are_mandatory(control: str) -> None:
    baseline, candidate, controls = gate_pair()
    del controls[control]
    assert control in adoption_gate(baseline, candidate, controls=controls).reasons


def test_every_exact_case_and_all_unknown_unanswerable_claims_are_gate_failures() -> None:
    baseline, candidate, controls = gate_pair()
    assert "exact_confirmation" in adoption_gate(baseline, replace(candidate, exact_correct=3), controls=controls).reasons
    assert "unanswerable_claims_observed" in adoption_gate(
        baseline, replace(candidate, unanswerable_claims_observed=3), controls=controls).reasons
    assert "no_unanswerable_definitive_claims" in adoption_gate(
        baseline, replace(candidate, unanswerable_definitive_claims=1), controls=controls).reasons


def test_zero_baseline_precision_is_valid_but_null_is_not() -> None:
    baseline, candidate, controls = gate_pair()
    assert isinstance(baseline.corpus_json, str) and isinstance(baseline.capture_json, str)
    spec = json.loads(baseline.corpus_json)
    observations = json.loads(baseline.capture_json)
    for row in observations["rows"][:16]:
        row["results"] = [{"path": "entities/c.md"}]
    zero = score(spec, observations)
    assert zero.owner_precision == zero.emitted_precision == Ratio(0, 16)
    assert adoption_gate(zero, candidate, controls=controls).eligible
    for row in observations["rows"][:16]:
        row["results"] = []
    null = score(spec, observations)
    assert "owner_precision_noninferiority" in adoption_gate(null, candidate, controls=controls).reasons


def test_independent_source_arms_and_development_are_not_confirmation_adoption() -> None:
    baseline, candidate, controls = gate_pair()
    augmented = replace(candidate, binding=replace(candidate.binding, arm="source-augmentation"))
    assert "same_arm" in adoption_gate(baseline, augmented, controls=controls).reasons
    other_source = replace(candidate, binding=replace(candidate.binding, selected_source="other-source"))
    assert "same_selected_source" in adoption_gate(baseline, other_source, controls=controls).reasons
    development = replace(candidate, split="development")
    assert "confirmation_split" in adoption_gate(baseline, development, controls=controls).reasons


def test_relabeling_identical_pages_cannot_establish_retrieval_improvement() -> None:
    spec = corpus()
    baseline_capture = capture(spec, "confirmation")
    candidate_capture = capture(spec, "confirmation", capture_id="candidate-capture")
    baseline_aliases = aliases()
    for fixture_aliases in baseline_aliases.values():
        fixture_aliases["entities/a.md"] = "b.py"
    baseline = score(spec, baseline_capture, baseline_aliases)
    candidate = score(spec, candidate_capture, aliases())
    assert baseline_capture["rows"] == candidate_capture["rows"]
    assert baseline.owner_recall.value == 0
    assert candidate.owner_recall.value == 1
    assert baseline.binding.corpus_sha256 == candidate.binding.corpus_sha256
    assert baseline.binding.selected_source == candidate.binding.selected_source
    assert baseline.binding.arm == candidate.binding.arm
    decision = adoption_gate(baseline, candidate, controls={
        "correctness": True, "selection": True, "exact_development": True})
    assert not decision.eligible
    assert decision.reasons == ("same_aliases",)
    assert decision.checks["same_aliases"] is False


@pytest.mark.parametrize("field", ["owner_recall", "owner_precision", "emitted_recall", "emitted_precision"])
@pytest.mark.parametrize("mutation", ["within-range", "impossible", "denominator", "noninteger"])
def test_gate_rejects_aggregate_forgery_with_unchanged_pinned_query_rows(field: str, mutation: str) -> None:
    baseline, candidate, controls = gate_pair()
    assert adoption_gate(baseline, candidate, controls=controls).eligible
    original = getattr(candidate, field)
    edited = {"within-range": Ratio(original.numerator - 1, original.denominator),
              "impossible": Ratio(original.denominator + 1, original.denominator),
              "denominator": Ratio(original.numerator, original.denominator + 1),
              "noninteger": Ratio(True, original.denominator)}[mutation]
    forged = replace(candidate, **{field: edited})
    assert forged.binding == candidate.binding and forged.queries == candidate.queries
    result = adoption_gate(baseline, forged, controls=controls)
    assert not result.eligible and "candidate_score_custody" in result.reasons


@pytest.mark.parametrize("field", ["exact_correct", "exact_total", "unanswerable_total",
                                   "unanswerable_claims_observed", "unanswerable_definitive_claims",
                                   "unanswerable_candidates", "unanswerable_candidate_pages", "missing", "errors"])
def test_gate_rederives_every_aggregate_from_original_capture(field: str) -> None:
    baseline, candidate, controls = gate_pair()
    original = getattr(candidate, field)
    forged = replace(candidate, **{field: original + 1})
    assert not adoption_gate(baseline, forged, controls=controls).eligible
    assert "candidate_score_custody" in adoption_gate(baseline, forged, controls=controls).reasons


@pytest.mark.parametrize("field", ["expected_owners", "owner_top5", "owner_hits", "emitted_top5",
                                   "all_pages", "metadata_json", "query_ids", "capture_json", "corpus_json", "aliases_json"])
def test_gate_authenticates_query_and_source_alias_foundations(field: str) -> None:
    baseline, candidate, controls = gate_pair()
    first = candidate.queries[0]
    if field in ("query_ids", "capture_json", "corpus_json", "aliases_json"):
        if field == "query_ids":
            changed: Any = tuple(reversed(candidate.query_ids))
        else:
            raw = json.loads(getattr(candidate, field))
            if field == "capture_json":
                raw["rows"][0]["results"][0]["snippet"] = "substituted capture"
            elif field == "corpus_json":
                raw["queries"][0]["relevancecite"] = "substituted relevance"
            else:
                raw["fixture-0"]["entities/a.md"] = "b.py"
            changed = json.dumps(raw)
        forged = replace(candidate, **{field: changed})
    else:
        changes: dict[str, Any] = {"expected_owners": ("b.py",), "owner_top5": ("b.py",),
                                  "owner_hits": 0, "emitted_top5": (), "all_pages": (),
                                  "metadata_json": "{}"}
        forged = replace(candidate, queries=(replace(first, **{field: changes[field]}), *candidate.queries[1:]))
    assert forged.binding == candidate.binding
    assert not adoption_gate(baseline, forged, controls=controls).eligible


def test_legacy_summary_without_raw_custody_cannot_earn_adoption() -> None:
    baseline, candidate, controls = gate_pair()
    naked = replace(candidate, corpus_json=None, capture_json=None, aliases_json=None)
    assert not adoption_gate(baseline, naked, controls=controls).eligible
    assert "capture_json" not in candidate.to_dict()
    assert "corpus_json" not in candidate.to_dict()
    assert "aliases_json" not in candidate.to_dict()


def test_capture_snapshot_remains_independent_of_later_mutable_input_edits() -> None:
    spec = corpus()
    observations = capture(spec)
    mapping = aliases()
    original = score(spec, observations, mapping)
    observations["rows"][0]["results"].clear()
    spec["queries"][0]["expected_owners"].clear()
    mapping["fixture-0"].clear()
    # The replay foundation still contains the initially pinned owner and page.
    assert isinstance(original.capture_json, str)
    assert json.loads(original.capture_json)["rows"][0]["results"][0]["path"] == "entities/a.md"
    assert original.queries[0].owner_hits == 1
