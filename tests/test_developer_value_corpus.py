"""Frozen owned inputs and independently falsifiable evaluation controls.

These tests establish the evaluation harness, not whether current product
defects have been repaired. Product outcomes are retained by opt-in drivers.
"""

from __future__ import annotations

import ast
from collections import Counter
from copy import deepcopy
import json
from typing import Any

import pytest

from tests.developer_value.fixtures import (
    LARGE_MODULES, POLICY_SOURCE, baseline_guides, materialize, projects, source_hashes,
)
from tests.developer_value.oracles import (
    DEVELOPMENT_IDS, MANIFEST, apply_prose_mutation, apply_source_mutation, corpus_identity, owned_behavior,
    score_retrieval, source_observations, verify_corpus,
)


def test_frozen_corpus_has_three_owned_projects_twenty_cases_and_balanced_queries():
    manifest = verify_corpus()
    assert len(manifest["cases"]) == 20
    assert Counter(c["project"] for c in manifest["cases"]) == {"library": 8, "service": 7, "large": 5}
    assert len(manifest["retrieval"]["queries"]) == 40
    assert manifest["retrieval"]["development_ids"] == DEVELOPMENT_IDS
    assert len(manifest["retrieval"]["heldout_ids"]) == 20
    assert manifest["model_execution_established"] is manifest["field_evidence_established"] is False
    assert all(c["execution"] == "opt-in-deterministic-evaluation" for c in manifest["cases"])
    assert corpus_identity() == corpus_identity()


def test_fixture_generation_is_detached_repeatable_and_source_only():
    first, second = projects(), projects()
    assert first == second
    assert len(POLICY_SOURCE.encode("utf-8")) == 238
    assert first["library"]["policy.py"] == POLICY_SOURCE
    assert sum(path.startswith("parts/part_") for path in first["large"]) == LARGE_MODULES
    first["library"]["policy.py"] = "changed"
    assert projects() == second
    assert all(path.endswith(".py") for files in second.values() for path in files)
    assert baseline_guides("library") == baseline_guides("library")
    assert len(source_hashes(second["large"])) == len(second["large"])


@pytest.mark.parametrize("name", ["library", "service", "large"])
def test_materialization_exposes_only_owned_source_bytes(tmp_path, name):
    root = tmp_path / name
    source = materialize(name, root)
    assert source == root / "src"
    assert sorted(p.name for p in root.iterdir()) == ["src"]
    observed = {path.relative_to(source).as_posix(): path.read_text(encoding="utf-8")
                for path in source.rglob("*.py")}
    assert observed == projects()[name]
    assert not any(p.name in {"corpus.json", "oracles.py", "expectations.json"} for p in root.rglob("*"))
    with pytest.raises(ValueError, match="new or empty"):
        materialize(name, root)
    assert observed == {path.relative_to(source).as_posix(): path.read_text(encoding="utf-8")
                        for path in source.rglob("*.py")}


def test_unknown_project_and_redirected_workspace_cannot_write(tmp_path):
    with pytest.raises(ValueError, match="unknown"):
        materialize("external", tmp_path / "unknown")
    assert not (tmp_path / "unknown").exists()
    target = tmp_path / "target"
    target.mkdir()
    (tmp_path / "alias").symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="redirected"):
        materialize("library", tmp_path / "alias")
    assert not list(target.iterdir())


@pytest.mark.parametrize("mutation", ["source-hash", "guide-hash", "split", "count", "gate", "visibility", "alias", "mutation-basis", "origin"])
def test_changed_frozen_contract_is_rejected(tmp_path, mutation):
    data = json.loads(MANIFEST.read_bytes())
    if mutation == "source-hash":
        data["projects"]["library"]["source_sha256"]["policy.py"] = "0" * 64
    elif mutation == "guide-hash":
        data["projects"]["library"]["guides_sha256"]["index.md"] = "0" * 64
    elif mutation == "split":
        data["retrieval"]["queries"][0]["split"] = "held-out"
    elif mutation == "count":
        data["cases"].pop()
    elif mutation == "gate":
        data["gates"]["retrieval"]["min_heldout_answerable_recall_at_five_improvement"] = 0
    elif mutation == "visibility":
        data["visibility"]["solver_allow"].append("oracles.py")
    elif mutation == "alias":
        data["retrieval"]["target_aliases"]["library"]["source:retry.py"].append("entities/Batch.md")
    elif mutation == "mutation-basis":
        data["cases"][0]["mutation"]["before"] = "not present"
    else:
        data["projects"]["large"]["origin"] = "external maintainer repository"
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        verify_corpus(path)


def test_duplicate_json_fields_are_not_silently_replaced(tmp_path):
    path = tmp_path / "corpus.json"
    path.write_text('{"schema_version": "first", "schema_version": "second"}')
    with pytest.raises(ValueError, match="duplicate"):
        verify_corpus(path)


def test_exact_queries_and_error_messages_have_independent_source_evidence():
    sources = projects()
    for query in verify_corpus()["retrieval"]["queries"]:
        if query["category"] not in {"exact-symbol", "error-message"}:
            continue
        text = sources[query["project"]][query["expected_targets"][0][7:]]
        if query["category"] == "error-message":
            assert query["query"] in {node.value for node in ast.walk(ast.parse(text))
                                     if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        else:
            records = source_observations(text)["declarations"]
            assert any(query["query"] == ".".join(filter(None, (r["owner"], r["name"])))
                       or query["query"] == r["name"] for r in records)


def test_source_oracle_preserves_occurrence_and_never_imports_target():
    source = 'raise RuntimeError("source must not execute")\n' + projects()["library"]["scope.py"]
    observed = source_observations(source)
    repeated = [row for row in observed["declarations"] if row["name"] == "touch"]
    assert [row["owner_occurrence"] for row in repeated] == [1, 2]
    assert len({row["line"] for row in repeated}) == 2


def test_review_cases_freeze_semantic_preparation_refresh_and_acknowledgment_gaps():
    manifest = verify_corpus()
    selected = {case["id"]: case for case in manifest["cases"] if case["id"] in {"S05", "S06"}}
    for case in selected.values():
        preparation = case["preparation"]
        sentinel = preparation["semantic_edits"][0]
        assert preparation["refresh_before_first_read"] is True
        assert sentinel["wiki_path"] == "entities/Batch.md"
        assert sentinel["section_ownership"] == "semantic" and sentinel["heading"] == "Description"
        assert case["mutation"]["before"] == "return values[:limit]"
        assert case["mutation"]["after"] == "return values[:limit - 1]"
        assert sentinel["refresh_cli"] == manifest["preparation"]["sync_cli"]
    assert any(step.get("fresh_process") is True for step in selected["S05"]["observation_steps"])
    probes = [step for step in selected["S06"]["observation_steps"]
              if "acknowledgment" in step.get("action", "")]
    assert all(step["missing_capability_outcome"] == "unavailable" for step in probes)
    assert "human approval" in selected["S06"]["baseline_missing_capability"]


def test_same_file_occurrence_case_and_trusted_bounded_scope_are_explicit():
    cases = {case["id"]: case for case in verify_corpus()["cases"]}
    occurrence = cases["L04"]
    assert occurrence["selector"] == "scope.py:Repeated.touch#1"
    assert occurrence["mutation"]["path"] == "scope.py"
    assert occurrence["expected"]["after"]["unchanged_declaration"]["occurrence"] == 1
    assert occurrence["expected"]["after"]["changed_declaration"]["occurrence"] == 2
    bounded = cases["G01"]
    assert bounded["host_policy"] == {"read_scope": "full-inventory", "max_files": 128}
    assert "host_policy" not in bounded["bounded_request"]
    assert bounded["bounded_request"]["options"]["max_files"] >= len(projects()["large"])
    assert bounded["bounded_request"]["requirements"][0]["selector"] == "search_records"


def test_module_global_case_keeps_module_and_class_inspections_separately_scoped():
    case = next(c for c in verify_corpus()["cases"] if c["id"] == "S04")
    for stage in ("before", "after"):
        pages = {step["args"][0] for step in case["observation_steps"]
                 if step.get("stage") == stage and step.get("api") == "inspect_concept"
                 and step.get("kwargs", {}).get("live") is True}
        assert pages == {"modules/store.md", "entities/Store.md"}
    assert case["expected"]["after"]["module_implementation"] == "changed"
    assert case["expected"]["after"]["selected_implementation"] == "unchanged"
    assert case["expected"]["after"]["owned_behavior"] == "service-failed"


@pytest.mark.parametrize("change", ["unknown-heading", "heading-insertion", "forced-sync", "missing-module-inspection"])
def test_preservation_and_module_observation_recipes_cannot_regress(tmp_path, change):
    manifest = verify_corpus()
    if change == "missing-module-inspection":
        case = next(c for c in manifest["cases"] if c["id"] == "S04")
        case["observation_steps"] = [step for step in case["observation_steps"]
                                     if step.get("args") != ["modules/store.md"]]
    else:
        case = next(c for c in manifest["cases"] if c["id"] == "G03")
        if change == "unknown-heading":
            case["mutation"]["heading"] = "Operator notes"
        elif change == "heading-insertion":
            case["mutation"]["after"] = "## Operator notes\nUnsupported custom tail.\n"
        else:
            manifest["preparation"]["sync_cli"].append("--force")
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError):
        verify_corpus(path)


def test_supported_prose_insertion_preserves_following_generated_sections(tmp_path):
    case = next(c for c in verify_corpus()["cases"] if c["id"] == "G03")
    assert case["mutation"]["heading"] == "Description"
    assert case["mutation"]["section_ownership"] == "semantic"
    assert "--force" not in verify_corpus()["preparation"]["sync_cli"]
    wiki = tmp_path / "wiki"
    page = wiki / "modules/search.md"
    page.parent.mkdir(parents=True)
    following = "## Classes\nGenerated class table.\n\n## Functions\nGenerated function table.\n"
    page.write_text("# Search\n\n## Description\nExisting authored explanation.\n\n" + following)
    assert apply_prose_mutation(case, wiki) == page
    updated = page.read_text()
    assert updated.endswith(following)
    assert updated.count("## Description") == 1
    assert "Existing authored explanation." in updated
    assert case["mutation"]["after"].strip() in updated.split("## Classes")[0]
    assert "## Operator notes" not in updated


@pytest.mark.parametrize("body", [
    "# Search\n\n## Functions\nOnly generated code.\n",
    "# Search\n\n## Description\nFirst.\n\n## Description\nDuplicate.\n",
    "# Search\n\n## Description\n```example\nUnclosed code.\n",
])
def test_prose_insertion_rejects_missing_ambiguous_or_malformed_owner_without_write(tmp_path, body):
    case = next(c for c in verify_corpus()["cases"] if c["id"] == "G03")
    wiki = tmp_path / "wiki"
    page = wiki / "modules/search.md"
    page.parent.mkdir(parents=True)
    page.write_text(body)
    before = page.read_bytes()
    with pytest.raises(ValueError):
        apply_prose_mutation(case, wiki)
    assert page.read_bytes() == before


def test_prose_insertion_ignores_fenced_example_headings_and_enforces_bounds(tmp_path):
    case = next(c for c in verify_corpus()["cases"] if c["id"] == "G03")
    wiki = tmp_path / "wiki"
    page = wiki / "modules/search.md"
    page.parent.mkdir(parents=True)
    body = "# Search\n\n## Description\n```markdown\n## Description\n```\n\n## Functions\nGenerated.\n"
    page.write_text(body)
    apply_prose_mutation(case, wiki)
    assert case["mutation"]["after"].strip() in page.read_text().split("## Functions")[0]
    before = page.read_bytes()
    case["mutation"]["after"] = "x" * 4097
    with pytest.raises(ValueError, match="bound"):
        apply_prose_mutation(case, wiki)
    assert page.read_bytes() == before


@pytest.mark.parametrize("prior_edit", ["comment", "default", "line-endings"])
def test_source_mutation_requires_full_frozen_file_even_when_substring_remains(tmp_path, prior_edit):
    source = materialize("library", tmp_path / "library")
    case = verify_corpus()["cases"][0]
    page = source / "policy.py"
    raw = page.read_bytes()
    if prior_edit == "comment":
        changed = raw + b"\n# Unrelated earlier edit.\n"
    elif prior_edit == "default":
        changed = raw.replace(b"limit: int = 3", b"limit: int = 4")
    else:
        changed = raw.replace(b"\n", b"\r\n")
    page.write_bytes(changed)
    assert case["mutation"]["before"].encode("utf-8") in changed
    with pytest.raises(ValueError, match="frozen bytes"):
        apply_source_mutation(case, source)
    assert page.read_bytes() == changed


def test_owned_cap_oracle_falsifies_body_edit_and_wrong_default_workaround(tmp_path):
    source = materialize("library", tmp_path / "library")
    manifest = verify_corpus()
    assert owned_behavior(source, "cap")["oracle_passed"]
    apply_source_mutation(manifest["cases"][0], source)
    result = owned_behavior(source, "cap")
    assert result["compiled"] and result["process_exit"] == 0 and not result["oracle_passed"]
    path = source / "policy.py"
    path.write_text(path.read_text().replace("limit: int = 3", "limit: int = 4"))
    assert not owned_behavior(source, "cap")["oracle_passed"]
    with pytest.raises(ValueError, match="basis changed"):
        apply_source_mutation(manifest["cases"][0], source)


def test_retry_oracle_requires_each_permitted_attempt_instead_of_a_default_patch(tmp_path):
    source = materialize("library", tmp_path / "library")
    path = source / "retry.py"
    original = path.read_text()
    assert not owned_behavior(source, "retry")["oracle_passed"]
    path.write_text(original.replace("attempts: int = 3", "attempts: int = 4"))
    assert not owned_behavior(source, "retry")["oracle_passed"]
    path.write_text(original.replace("range(attempts - 1)", "range(attempts)")
                    .replace("attempt == attempts - 2", "attempt == attempts - 1"))
    assert owned_behavior(source, "retry")["oracle_passed"]


@pytest.mark.parametrize("name,control,path,before,after", [
    ("library", "text", "text.py", ".lower()", ".upper()"),
    ("service", "service", "store.py", "ALLOW_WRITES = True", "ALLOW_WRITES = False"),
    ("large", "large", "rank.py", "-len(terms & set(record.lower().split()))", "len(terms & set(record.lower().split()))"),
])
def test_owned_runtime_controls_falsify_wrong_variants_without_changing_sources_on_read(
    tmp_path, name, control, path, before, after
):
    source = materialize(name, tmp_path / name)
    previous = {p: p.read_bytes() for p in source.rglob("*") if p.is_file()}
    assert owned_behavior(source, control)["oracle_passed"]
    assert previous == {p: p.read_bytes() for p in source.rglob("*") if p.is_file()}
    changed = source / path
    changed.write_text(changed.read_text().replace(before, after))
    observed = owned_behavior(source, control)
    assert observed["compiled"] and not observed["oracle_passed"]
    assert observed["model_execution_established"] is False


def test_behavior_control_distinguishes_syntax_failure_and_unknown_control(tmp_path):
    source = materialize("library", tmp_path / "library")
    with pytest.raises(ValueError, match="unknown"):
        owned_behavior(source, "arbitrary-command")
    (source / "policy.py").write_text("class:\n")
    result = owned_behavior(source, "cap")
    assert not result["compiled"] and result["process_exit"] is None and not result["oracle_passed"]


def perfect_observations(manifest) -> dict[str, Any]:
    return {query["id"]: {"results": list(query["expected_targets"]), "definitive_answer": False}
            for query in manifest["retrieval"]["queries"]}


def test_retrieval_perfect_control_and_missing_results_have_truthful_denominators():
    manifest = verify_corpus()
    observed = score_retrieval(manifest, perfect_observations(manifest))
    assert observed["answerable"]["recall_at_five"] == observed["answerable"]["precision_at_five"] == 1
    assert observed["exact"]["fraction"] == 1
    assert observed["unanswerable"]["queries"] == 8
    assert observed["unanswerable"]["definitive_claims"] == 0
    empty = score_retrieval(manifest, {})
    assert empty["answerable"]["recall_at_five"] == 0
    assert empty["answerable"]["precision_at_five"] is None
    assert empty["answerable"]["expected_targets"] == observed["answerable"]["expected_targets"]
    assert len(empty["missing_observations"]) == 40
    assert empty["unanswerable"]["definitive_claims"] is None


def test_retrieval_deduplicates_owner_aliases_before_cutoff_and_retains_noise():
    manifest = verify_corpus()
    observations = perfect_observations(manifest)
    observations["E1"]["results"] = [
        {"path": "modules/policy.md"}, {"path": "entities/Batch.md#description"},
        "source:policy.py", {"path": "modules/retry.md"}, {"path": "modules/text.md"},
        {"path": "modules/validation.md"}, {"path": "unknown-page.md"},
        {"path": "another-page.md"},
    ]
    observed = score_retrieval(manifest, observations)
    first = observed["queries"][0]
    assert first["targets_at_five"] == ["source:policy.py", "source:retry.py", "source:text.py",
                                        "source:validation.py", "unmapped:unknown-page.md"]
    assert observed["answerable"]["recall_at_five"] == 1
    assert observed["answerable"]["precision_at_five"] < 1
    assert observed["exact"]["fraction"] == 1


def test_distinct_cutoff_cannot_recover_a_sixth_owner_or_inflate_duplicate_relevance():
    manifest = verify_corpus()
    observations = perfect_observations(manifest)
    observations["E1"]["results"] = [f"noise-{i}.md" for i in range(5)] + ["source:policy.py"] * 10
    observed = score_retrieval(manifest, observations)
    assert observed["queries"][0]["recovered"] == 0
    assert not observed["queries"][0]["top_one_correct"]
    assert observed["answerable"]["recall_at_five"] < 1
    assert observed["exact"]["fraction"] == 7 / 8


def test_unanswerable_candidates_are_separate_from_definitive_claims():
    manifest = verify_corpus()
    observations = perfect_observations(manifest)
    observations["U1"] = {"results": ["source:policy.py"], "definitive_answer": True}
    observed = score_retrieval(manifest, observations)
    assert observed["unanswerable"]["returned_candidate_queries"] == 1
    assert observed["unanswerable"]["definitive_claims"] == 1
    assert observed["answerable"]["precision_at_five"] == 1
    observations["U1"] = ["source:policy.py"]
    assert score_retrieval(manifest, observations)["unanswerable"]["definitive_claims"] is None


def test_split_scoring_does_not_silently_accept_treatment_or_unknown_query_ids():
    manifest = verify_corpus()
    observations = perfect_observations(manifest)
    development = {key: value for key, value in observations.items() if key in DEVELOPMENT_IDS}
    assert score_retrieval(manifest, development, split="development")["exact"]["queries"] == 4
    with pytest.raises(ValueError, match="unselected"):
        score_retrieval(manifest, observations, split="development")
    unknown = deepcopy(observations)
    unknown["unknown"] = []
    with pytest.raises(ValueError, match="unknown"):
        score_retrieval(manifest, unknown)
    with pytest.raises(ValueError, match="split"):
        score_retrieval(manifest, {}, split="confirmation")


@pytest.mark.parametrize("invalid", ["not-a-list", {"results": [], "definitive_answer": "yes"}, [None], [{}]])
def test_malformed_retrieval_observation_is_not_counted_as_success(invalid):
    with pytest.raises(ValueError):
        score_retrieval(verify_corpus(), {"E1": invalid})
