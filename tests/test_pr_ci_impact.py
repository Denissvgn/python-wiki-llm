"""Impact can add independently owned checks, never retract the trusted floor."""

from __future__ import annotations

import copy
from fnmatch import fnmatchcase
from pathlib import Path
from types import SimpleNamespace

import pytest

from release import pr_ci as ci
from release import pr_ci_impact as adapter
from tests.test_pr_ci import (
    policy as policy,
    sources as sources,
    changed,
    selection,
    fixture_repository,
)


ROOT = Path(__file__).parents[1]


def envelope(operation, **fields):
    return {
        "schema_version": "llm-wiki-documentation-query/v1",
        "operation": operation,
        "cost": {
            "scope": "targeted-extraction"
            if operation == "impact"
            else "snapshot-index-only",
            "full_inventory_performed": False,
        },
        "knowledge": {"availability": "ready", "freshness_evaluated": False},
        "bounds": {},
        "truncated": False,
        **fields,
    }


def responses(
    calls, *, source="src/pkg/query.py", resolution="resolved", truncated=False
):
    def query(request):
        calls.append(request)
        if request["operation"] == "impact":
            return envelope(
                "impact",
                concepts=[{"locator": "llm-wiki://modules/changed"}],
                matches=[{"path": "src/pkg/api.py", "inventory_present": True}],
            )
        return envelope(
            "typed",
            typed_graph={"availability": "ready"},
            truncated=truncated,
            edges=[
                {
                    "kind": "calls",
                    "origin": "extracted",
                    "resolution": resolution,
                    "related_concept": {
                        "locator": "llm-wiki://modules/caller",
                        "source_path": source,
                        "freshness": {
                            "state": "unknown",
                            "live_comparison_performed": False,
                        },
                    },
                    "coverage": {"omitted": 2},
                }
            ],
        )

    return query


def test_supported_queries_are_read_only_bounded_and_keep_snapshot_qualifications():
    calls = []
    result = adapter.observe(
        responses(calls), ["src/pkg/api.py"], {"candidate_sha": "a" * 40}
    )
    assert result["affected_sources"] == ["src/pkg/query.py"]
    assert calls[0] == {
        "operation": "impact",
        "paths": ["src/pkg/api.py"],
        "source_policy": "discovery",
        "limit": 100,
    }
    assert calls[1]["operation"] == "typed" and calls[1]["direction"] == "incoming"
    assert all("allow_full_inventory" not in request for request in calls)
    assert result["can_reduce_selection"] is False and result["complete"] is False
    assert result["citations"][0]["freshness"]["state"] == "unknown"
    assert result["citations"][0]["coverage"]["omitted"] == 2
    assert result["citations"][0]["basis"] == "recorded-snapshot-relationship"


@pytest.mark.parametrize("resolution", ["unresolved", "ambiguous", "external"])
def test_unresolved_edges_are_gaps_not_guessed_test_owners(resolution):
    result = adapter.observe(
        responses([], resolution=resolution), ["src/pkg/api.py"], {}
    )
    assert result["affected_sources"] == [] and result["status"] == "partial"
    assert any(gap.get("resolution") == resolution for gap in result["gaps"])


def test_unavailable_native_knowledge_is_not_an_empty_impact_verdict():
    result = adapter.observe(
        lambda request: envelope(
            "impact",
            knowledge={"availability": "degraded", "reason": "mixed-snapshot"},
            matches=[],
        ),
        ["src/pkg/api.py"],
        {},
    )
    assert result["status"] == "partial" and result["complete"] is False
    assert result["gaps"][0]["reason"] == "native-knowledge-unavailable"


def test_query_truncation_survives_in_the_result():
    result = adapter.observe(responses([], truncated=True), ["src/pkg/api.py"], {})
    assert result["status"] == "partial"
    assert any(g["reason"] == "query-truncated" for g in result["gaps"])
    assert result["queries"][1]["truncated"] is True


def test_full_inventory_or_unknown_query_scope_cannot_produce_admitted_hints():
    result = adapter.observe(
        lambda request: envelope(
            "impact", cost={"scope": "full-inventory", "full_inventory_performed": True}
        ),
        ["src/pkg/api.py"],
        {},
    )
    assert result["status"] == "unavailable" and result["affected_sources"] == []


def test_errors_and_zero_paths_preserve_the_advisory_boundary():
    def fail(request):
        raise OSError("helper unavailable")

    assert adapter.observe(fail, ["src/pkg/api.py"], {})["status"] == "unavailable"
    assert adapter.observe(fail, [], {})["status"] == "not-applicable"


def test_path_and_concept_limits_have_exact_omission_accounting(monkeypatch):
    monkeypatch.setattr(adapter, "MAX_PATHS", 1)
    monkeypatch.setattr(adapter, "MAX_CONCEPTS", 1)
    calls = []

    def query(request):
        calls.append(request)
        if request["operation"] == "impact":
            return envelope(
                "impact",
                concepts=[
                    {"locator": "llm-wiki://modules/a"},
                    {"locator": "llm-wiki://modules/b"},
                ],
            )
        return envelope("typed", typed_graph={"availability": "ready"}, edges=[])

    result = adapter.observe(query, ["a.py", "b.py"], {})
    assert result["path_bounds"] == {"total": 2, "returned": 1, "truncated": True}
    assert result["concept_bounds"] == {"total": 2, "returned": 1, "truncated": True}
    assert len(calls) == 2


def test_module_owner_is_queried_before_lexically_earlier_entities(monkeypatch):
    monkeypatch.setattr(adapter, "MAX_CONCEPTS", 1)
    calls = []

    def query(request):
        calls.append(request)
        if request["operation"] == "impact":
            return envelope(
                "impact",
                concepts=[
                    {
                        "locator": "llm-wiki://entities/AAA",
                        "concept_kind": "code-entity",
                    },
                    {"locator": "llm-wiki://modules/zzz", "page_kind": "module"},
                ],
            )
        return envelope("typed", typed_graph={"availability": "ready"}, edges=[])

    result = adapter.observe(query, ["zzz.py"], {})
    assert calls[1]["value"] == "llm-wiki://modules/zzz"
    assert result["concept_bounds"] == {"total": 2, "returned": 1, "truncated": True}


def test_slow_impact_retains_evidence_and_exact_unqueried_concept_count(monkeypatch):
    ticks = iter([0, adapter.QUERY_SECONDS + 1])
    monkeypatch.setattr(adapter.time, "monotonic", lambda: next(ticks))
    calls = []
    result = adapter.observe(responses(calls), ["src/pkg/api.py"], {})
    assert len(calls) == 1 and result["status"] == "partial"
    assert result["source_outcomes"][0]["path"] == "src/pkg/api.py"
    assert result["concept_bounds"] == {"total": 1, "returned": 0, "truncated": True}
    assert {"reason": "query-time-budget", "omitted": 1} in result["gaps"]


def test_api_runtime_error_preserves_the_unavailable_fallback():
    def query(request):
        raise RuntimeError("API boundary refused the request")

    result = adapter.observe(query, ["src/pkg/api.py"], {})
    assert result["status"] == "unavailable" and result["affected_sources"] == []
    assert result["gaps"][0]["error"] == "RuntimeError"


def plan_for(policy, sources):
    floor = selection(policy, sources, [changed("README.md")])
    return {
        "schema": ci.SCHEMA,
        "mode": "pull-request",
        "base_sha": "a" * 40,
        "head_sha": "b" * 40,
        "candidate_sha": "c" * 40,
        "candidate_tree": "d" * 40,
        "policy_sha256": "e" * 64,
        "repository": "owner/repo",
        "run_id": 100,
        "run_attempt": 2,
        "changes": [changed("README.md")],
        **floor,
    }


def install_fake_adapter(monkeypatch, hints, *, status="observed", wrong_binding=False):
    def collect(ci_driver, root, directory, binding, rows, work, provider_python):
        result = adapter.report(binding, status, "fixture")
        result["affected_sources"] = hints
        if wrong_binding:
            result["binding"] = {**binding, "candidate_sha": "f" * 40}
        return result

    monkeypatch.setattr(
        ci,
        "impact_module",
        lambda directory: SimpleNamespace(
            collect=collect, SCHEMA=adapter.SCHEMA, MAX_HINTS=adapter.MAX_HINTS
        ),
    )


def test_admitted_impact_is_an_additive_union_with_existing_changed_tests(
    tmp_path, monkeypatch, policy, sources
):
    install_fake_adapter(monkeypatch, ["src/pkg/query.py"])
    directory = tmp_path / "driver"
    directory.mkdir()
    (directory / "skip-allowlist.json").write_text('{"entries":[]}')
    original = plan_for(policy, sources)
    result = ci.enrich_impact(
        Path("."),
        directory,
        policy,
        sources,
        sources,
        copy.deepcopy(original),
        tmp_path / "work",
    )
    assert result["lanes"]["ubuntu"]["selectors"] == [
        "tests/test_api.py",
        "tests/test_docs.py",
        "tests/test_query.py",
    ]
    assert set(original["jobs"]) <= set(result["jobs"])
    assert result["impact"]["admissions"][0]["status"] == "admitted"
    ci.additive_floor(result["selection_floor"], result)


@pytest.mark.parametrize(
    "hint", ["/tmp/escape.py", "../escape.py", "src/pkg/no-owner.py"]
)
def test_invalid_or_unowned_hints_cannot_shrink_or_replace_the_floor(
    tmp_path, monkeypatch, policy, sources, hint
):
    install_fake_adapter(monkeypatch, [hint])
    original = plan_for(policy, sources)
    result = ci.enrich_impact(
        Path("."),
        tmp_path,
        policy,
        sources,
        sources,
        copy.deepcopy(original),
        tmp_path / "work",
    )
    assert result["lanes"] == original["lanes"] and result["jobs"] == original["jobs"]
    assert result["impact"]["admissions"][0]["status"] == "rejected"


def test_missing_impact_keeps_the_trusted_floor_and_a_visible_reason(
    tmp_path, monkeypatch, policy, sources
):
    install_fake_adapter(monkeypatch, [], status="unavailable")
    original = plan_for(policy, sources)
    result = ci.enrich_impact(
        Path("."),
        tmp_path,
        policy,
        sources,
        sources,
        copy.deepcopy(original),
        tmp_path / "work",
    )
    assert result["lanes"] == original["lanes"]
    assert result["impact"]["status"] == "unavailable"


def test_cross_candidate_impact_evidence_is_rejected(
    tmp_path, monkeypatch, policy, sources
):
    install_fake_adapter(monkeypatch, [], wrong_binding=True)
    with pytest.raises(ci.SelectionError, match="authority"):
        ci.enrich_impact(
            Path("."),
            tmp_path,
            policy,
            sources,
            sources,
            plan_for(policy, sources),
            tmp_path / "work",
        )


@pytest.mark.parametrize("damage", ["job", "test", "lane", "helper", "profile", "skip"])
def test_additive_invariant_rejects_every_kind_of_retraction(policy, sources, damage):
    floor = selection(policy, sources, [changed("src/pkg/query.py")])
    floor["lanes"]["ubuntu"]["helpers"] = ["typescript"]
    floor["skip_edges"] = [
        {
            "lane": "ubuntu",
            "node_id": "tests/test_query.py::test_query",
            "reason": "fixture",
            "producer": "windows",
        }
    ]
    changed_plan = copy.deepcopy(floor)
    if damage == "job":
        changed_plan["jobs"] = []
    elif damage == "test":
        changed_plan["lanes"]["ubuntu"]["selectors"] = [
            "tests/test_query.py::test_query"
        ]
    elif damage == "lane":
        changed_plan["lanes"] = {}
    elif damage == "helper":
        changed_plan["lanes"]["ubuntu"]["helpers"] = []
    elif damage == "profile":
        changed_plan["lanes"]["ubuntu"]["profile"] = "dev"
    elif damage == "skip":
        changed_plan["skip_edges"] = []
    with pytest.raises(ci.SelectionError):
        ci.additive_floor(floor, changed_plan)


def test_minimal_provider_profile_reuses_maintained_hash_pins():
    profile = (ROOT / "release/pr-ci-impact-requirements.txt").read_text()
    original = (ROOT / "release/requirements.txt").read_text()
    assert "pyyaml==6.0.3" in profile and "setuptools==84.1.0" in profile
    for line in profile.splitlines():
        if "--hash=" in line:
            assert line in original


def test_adapter_and_setup_inputs_have_mandatory_ci_safety_owners():
    registry = ci.policy_load(ROOT / "release")
    assert "tests/test_pr_ci_impact.py" in registry["groups"]["ci-policy"]["tests"]
    for path in ("release/pr_ci_impact.py", "release/pr-ci-impact-requirements.txt"):
        groups = {
            group
            for rule in registry["rules"]
            if any(fnmatchcase(path, pattern) for pattern in rule["paths"])
            for group in rule["groups"]
        }
        assert "ci-policy" in groups


def test_worker_refuses_a_provider_outside_its_interpreter(monkeypatch, tmp_path):
    monkeypatch.setattr(
        adapter.importlib.util,
        "find_spec",
        lambda name: SimpleNamespace(origin=str(tmp_path / "foreign/__init__.py")),
    )
    with pytest.raises(ci.SelectionError, match="noneditably"):
        adapter.worker(ci, {"schema": adapter.SCHEMA})


def test_frozen_provider_comes_from_base_objects_without_executing_package(
    tmp_path, policy, sources
):
    original = b'raise RuntimeError("provider freeze must not import code")\n'
    sources = {
        **sources,
        "src/llm_wiki_cli/__init__.py": original,
        "src/llm_wiki_cli/services/analysis_contracts.json": b"{}",
        ".llm-wiki/source-selection.json": b'{"include":["src/llm_wiki_cli"]}',
    }
    root, _, event, _ = fixture_repository(tmp_path, policy, sources)
    (root / "src/llm_wiki_cli/__init__.py").write_text(
        'raise RuntimeError("candidate must not be copied")\n'
    )
    destination = tmp_path / "provider"
    frozen = adapter.freeze_provider(
        ci, root, event["pull_request"]["base"]["sha"], destination
    )
    assert (destination / "src/llm_wiki_cli/__init__.py").read_bytes() == original
    assert frozen["python_files"] == {"__init__.py": ci.digest(original)}
    assert not (destination / "tests").exists()
    assert frozen["base_sha"] == event["pull_request"]["base"]["sha"]


def test_same_version_but_different_provider_bytes_cannot_analyze(
    monkeypatch, tmp_path
):
    environment = tmp_path / "venv"
    package = environment / "lib/llm_wiki_cli"
    package.mkdir(parents=True)
    (package / "__init__.py").write_bytes(b"OLD")
    monkeypatch.setattr(adapter.sys, "prefix", str(environment))
    monkeypatch.setattr(
        adapter.importlib.util,
        "find_spec",
        lambda name: SimpleNamespace(origin=str(package / "__init__.py")),
    )
    with pytest.raises(ci.SelectionError, match="Python bytes"):
        adapter.worker(
            ci,
            {
                "schema": adapter.SCHEMA,
                "provider": {"python_files": {"__init__.py": ci.digest(b"NEW")}},
            },
        )


@pytest.mark.parametrize("data", [None, b"OLD"])
def test_missing_or_changed_provider_data_cannot_analyze(monkeypatch, tmp_path, data):
    environment = tmp_path / "venv"
    package = environment / "lib/llm_wiki_cli"
    package.mkdir(parents=True)
    (package / "__init__.py").write_bytes(b"")
    if data is not None:
        (package / "schema.json").write_bytes(data)
    monkeypatch.setattr(adapter.sys, "prefix", str(environment))
    monkeypatch.setattr(
        adapter.importlib.util,
        "find_spec",
        lambda name: SimpleNamespace(origin=str(package / "__init__.py")),
    )
    with pytest.raises(ci.SelectionError, match="package bytes"):
        adapter.worker(
            ci,
            {
                "schema": adapter.SCHEMA,
                "provider": {
                    "python_files": {"__init__.py": ci.digest(b"")},
                    "package_files": {"schema.json": ci.digest(b"NEW")},
                },
            },
        )


def test_revision_two_plan_runs_adapter_automatically_and_keeps_real_git_bindings(
    tmp_path, monkeypatch, policy, sources
):
    policy["revision"] = 2
    root, trusted, event, candidate = fixture_repository(tmp_path, policy, sources)
    install_fake_adapter(monkeypatch, ["tests/test_docs.py"])
    plan = ci.make_plan(root, trusted, event, candidate, "owner/repo", 123, 2)
    assert plan["impact"]["binding"]["base_sha"] == event["pull_request"]["base"]["sha"]
    assert plan["impact"]["binding"]["candidate_sha"] == candidate
    assert (
        plan["impact"]["binding"]["run_id"] == 123
        and plan["impact"]["binding"]["run_attempt"] == 2
    )
    assert plan["lanes"]["ubuntu"]["selectors"] == [
        "tests/test_api.py",
        "tests/test_docs.py",
        "tests/test_query.py",
    ]
    assert plan["qualification"] is False
