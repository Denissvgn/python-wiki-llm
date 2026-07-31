"""Tests for the ``context`` command — structured context budgeting."""

from __future__ import annotations

import io
import json
import sys
import textwrap
import types
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import context_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.services.extraction_jobs import ExtractionJobPlan
from llm_wiki_cli.services.knowledge_artifacts import (
    build_knowledge_commit_plan,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_evidence import (
    build_module_observation_basis,
    sha256_bytes,
)
from llm_wiki_cli.services.knowledge_freshness import (
    REASON_GENERATION_OPTIONS_CHANGED,
)
from llm_wiki_cli.services.knowledge_index import (
    build_knowledge_index,
    serialize_knowledge_index,
)
from llm_wiki_cli.services.knowledge_observability import (
    BASIS_INCOMPATIBLE_HINTS,
)
from llm_wiki_cli.services.sync_manifest import (
    ManifestEvidenceBaseline,
    ManifestPageSource,
    SyncManifest,
)
from tests import knowledge_fixtures as knowledge_fixture_helpers
from tests.knowledge_fixtures import (
    EvaluatedKnowledgeFixture,
    PageFixture,
    materialize_fixture_tree,
    one_module_two_entities_fixture,
)
from tests.test_knowledge_artifacts import _plan as _knowledge_commit_plan
from tests.test_knowledge_index import _builder_case_for
from tests.test_knowledge_compatibility import (
    COMPATIBILITY_CASES,
    _materialize_case,
)

CONTEXT_FIXTURE_DIR = Path(__file__).parent / "fixtures"
PREFER_FRESH_OFF_GOLDEN = (
    CONTEXT_FIXTURE_DIR / "context-prefer-fresh-off-v1.json"
)
PREFER_FRESH_ON_GOLDEN = (
    CONTEXT_FIXTURE_DIR / "context-prefer-fresh-on-v1.json"
)

# ── Helpers ───────────────────────────────────────────────────────────


def _make_args(**kwargs):
    defaults = {
        "src_dir": ".",
        "budget": 32000,
        "format": "json",
        "focus": "all",
        "request": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write_request(tmp_path, data) -> str:
    path = tmp_path / "context-request.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def _protocol_request(**overrides):
    data = {
        "protocol": context_cmd.PROTOCOL_VERSION,
        "budget_tokens": 32000,
        "focus": ["all"],
        "format": "json",
    }
    data.update(overrides)
    return data


def test_context_parser_accepts_packet_and_freshness_preference():
    args = cli._build_parser().parse_args(
        [
            "context",
            "--budget",
            "2048",
            "--format",
            "packet",
            "--prefer-fresh",
        ]
    )

    assert args.format == "packet"
    assert args.prefer_fresh is True


def _write_query_project(root: Path) -> None:
    (root / "api.py").write_text(
        textwrap.dedent(
            """\
            from repo import save

            __all__ = ["run"]

            def run(payload):
                return save(payload)
            """
        ),
        encoding="utf-8",
    )
    (root / "repo.py").write_text(
        textwrap.dedent(
            """\
            def save(payload):
                return payload
            """
        ),
        encoding="utf-8",
    )


def _write_query_wiki(root: Path, rel_path: str = "docs/llm_wiki") -> Path:
    wiki = root / rel_path
    for subdir in ["entities", "modules", "workflows", "flows", "infrastructure"]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text("# Index\n\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Log\n\n", encoding="utf-8")
    (wiki / "modules" / "api.md").write_text(
        "# api Module\n\n**Path:** `api.py`\n", encoding="utf-8"
    )
    (wiki / "modules" / "repo.md").write_text(
        "# repo Module\n\n**Path:** `repo.py`\n", encoding="utf-8"
    )
    (wiki / "flows" / "api-run.md").write_text(
        "# api-run\n\nFlow for run.\n", encoding="utf-8"
    )
    (wiki / "dependencies.md").write_text("# Dependencies\n\n", encoding="utf-8")
    (wiki / "load-order.md").write_text("# Load order\n\n", encoding="utf-8")
    return wiki


def _freshness_ranking_golden_inputs() -> tuple[
    dict[str, dict],
    dict[str, str],
    int,
]:
    file_data = {
        "language": "python",
        "classes": [],
        "functions": [{"name": "run", "line": 1}],
    }
    inventory = {
        "a_stale.py": file_data,
        "z_fresh.py": file_data,
    }
    classification = {
        "a_stale.py": "high",
        "z_fresh.py": "high",
    }
    budget = context_cmd._entry_tokens(
        "a_stale.py",
        context_cmd._build_entry(file_data, "high", "deep"),
    )
    return inventory, classification, budget


def _protocol_output_bytes(request: dict, payload: dict) -> bytes:
    response = context_cmd._protocol_success_payload(request, payload, [])
    return (json.dumps(response, indent=2) + "\n").encode("utf-8")


def _materialize_managed_freshness_ranking_project(tmp_path: Path) -> Path:
    source_files = {
        "src/a_stale.py": (
            '"""Stale module."""\n\n'
            "class StaleService:\n"
            '    """Recorded stale service."""\n'
        ),
        "src/z_fresh.py": (
            '"""Fresh module."""\n\n'
            "class FreshService:\n"
            '    """Current fresh service."""\n'
        ),
    }

    def module_inventory(
        module_docstring: str,
        class_name: str,
        class_docstring: str,
    ) -> dict:
        return {
            "language": "python",
            "module_docstring": module_docstring,
            "classes": [
                {
                    "name": class_name,
                    "kind": "class",
                    "line": 3,
                    "docstring": class_docstring,
                    "bases": [],
                    "decorators": [],
                    "attributes": [],
                    "methods": [],
                }
            ],
            "functions": [],
            "imports": [],
        }

    inventory = {
        "src/a_stale.py": module_inventory(
            "Stale module.",
            "StaleService",
            "Recorded stale service.",
        ),
        "src/z_fresh.py": module_inventory(
            "Fresh module.",
            "FreshService",
            "Current fresh service.",
        ),
    }
    pages = (
        PageFixture(
            "modules",
            "stale",
            "modules/stale.md",
            "semantic",
            "# stale Module\n\nStale module documentation.\n",
        ),
        PageFixture(
            "modules",
            "fresh",
            "modules/fresh.md",
            "semantic",
            "# fresh Module\n\nFresh module documentation.\n",
        ),
    )
    module_page_map = {
        "src/a_stale.py": "stale",
        "src/z_fresh.py": "fresh",
    }
    surface_payload, surface_bytes = (
        knowledge_fixture_helpers._build_surface_projection(
            source_files=source_files,
            assets={},
            inventory=inventory,
            pages=pages,
            module_page_map=module_page_map,
            entity_occurrence_page_map={},
        )
    )
    base_fixture = one_module_two_entities_fixture()
    fixture = EvaluatedKnowledgeFixture(
        name="freshness-ranking",
        source_files=source_files,
        assets={},
        inventory=inventory,
        pages=pages,
        module_page_map=module_page_map,
        entity_occurrence_page_map={},
        surface_payload=surface_payload,
        surface_bytes=surface_bytes,
        knowledge_payload=base_fixture.knowledge_payload,
        knowledge_bytes=base_fixture.knowledge_bytes,
    )
    builder_case = _builder_case_for(fixture)
    page_sources: dict[str, ManifestPageSource] = {}
    evidence_baselines: dict[str, ManifestEvidenceBaseline] = {}
    for source_path, page_id in module_page_map.items():
        page_path = f"modules/{page_id}.md"
        page_sources[page_path] = ManifestPageSource(
            scope="module",
            source_path=source_path,
        )
        evidence_baselines[page_path] = ManifestEvidenceBaseline.from_basis(
            build_module_observation_basis(
                source_path=source_path,
                file_data=inventory[source_path],
                source_content_hash=sha256_bytes(
                    source_files[source_path].encode("utf-8")
                ),
                extractor_ref="llm-wiki/extractor/python",
                inventory_complete=True,
            )
        )
    inputs = replace(
        builder_case.inputs,
        page_source_mappings=page_sources,
        evidence_baselines=evidence_baselines,
    )
    knowledge_bytes = serialize_knowledge_index(
        build_knowledge_index(inputs)
    ).encode("utf-8")
    fixture = replace(fixture, knowledge_bytes=knowledge_bytes)
    tree = materialize_fixture_tree(fixture, tmp_path / "checkout")
    manifest = SyncManifest(
        sources={
            source_path: {
                "hash": sha256_bytes(content.encode("utf-8")),
                "language": inventory[source_path]["language"],
            }
            for source_path, content in source_files.items()
        },
        page_source_mappings=page_sources,
        evidence_baselines=evidence_baselines,
        tombstones={},
    )
    commit_knowledge_artifacts(
        build_knowledge_commit_plan(
            tree["wiki_root"],
            surface_index_bytes=surface_bytes,
            knowledge_index_bytes=knowledge_bytes,
            manifest=manifest,
        )
    )
    (tree["root"] / "src" / "a_stale.py").write_text(
        '"""Stale module changed."""\n\n'
        "class ChangedStaleService:\n"
        '    """Changed stale service."""\n',
        encoding="utf-8",
    )
    return tree["root"]


def _knowledge_page_fixture(
    canonical_path: str,
    *,
    freshness: str,
    evidence: str = "present",
) -> tuple[dict, dict]:
    page_id = Path(canonical_path).stem
    page = {
        "kind": "entities",
        "id": page_id,
        "title": page_id,
        "canonical_path": canonical_path,
        "source_path": f"src/{page_id}.py",
        "role": "semantic",
        "mcp_uri": f"llm-wiki://entities/{page_id}",
    }
    concept = {
        "origin": "extracted",
        "evidence": evidence,
        "verification": "untracked",
        "freshness": {
            "state": freshness,
            "reason": (
                REASON_GENERATION_OPTIONS_CHANGED
                if freshness == "basis-incompatible"
                else f"fixture-{freshness}"
            ),
            "live_comparison_performed": True,
        },
    }
    return page, concept


def test_missing_context_source_probes_are_unique_and_deterministic(
    tmp_path,
    monkeypatch,
):
    def concept(source_path):
        basis = (
            None
            if source_path is None
            else types.SimpleNamespace(source_path=source_path)
        )
        return types.SimpleNamespace(
            facets=types.SimpleNamespace(structure=types.SimpleNamespace(basis=basis))
        )

    knowledge = types.SimpleNamespace(
        concepts=[
            concept("missing.py"),
            concept("present.py"),
            concept("missing.py"),
            concept("captured.py"),
            concept(None),
        ]
    )
    snapshot = types.SimpleNamespace(
        root=tmp_path,
        captured_content_hashes={"captured.py": "sha256:" + ("0" * 64)},
    )
    probed = []

    def fake_lstat(path):
        probed.append(path.relative_to(tmp_path).as_posix())
        if path.name == "missing.py":
            raise FileNotFoundError(path)
        return types.SimpleNamespace()

    monkeypatch.setattr(Path, "lstat", fake_lstat)

    missing = context_cmd._reliably_missing_context_sources(
        knowledge,
        snapshot,
    )

    assert probed == ["missing.py", "present.py"]
    assert missing == frozenset({"missing.py"})


class _KnowledgeQueryStub:
    def __init__(
        self,
        concepts: dict[str, dict] | None = None,
        *,
        availability: str = "ready",
        reason: str = "all-projection-commitments-match",
        freshness_evaluated: bool = True,
    ):
        self.concepts = concepts or {}
        self.knowledge_status = {
            "availability": availability,
            "reason": reason,
            "freshness": (
                f"evaluated ({len(self.concepts)} concepts)"
                if freshness_evaluated
                else "unevaluated (snapshot-only read)"
            ),
            "freshness_evaluated": freshness_evaluated,
        }
        self.lookups: list[str] = []

    def get_concept(self, canonical_path: str) -> dict:
        self.lookups.append(canonical_path)
        return {"concept": self.concepts.get(canonical_path)}


class _TypedGraphQueryStub(_KnowledgeQueryStub):
    def __init__(
        self,
        concepts: dict[str, dict],
        graph_counts: dict[str, tuple[int, int]],
        *,
        availability: str = "ready",
        reason: str = "typed-graph-extension-ready",
    ):
        super().__init__(concepts)
        self.graph_counts = graph_counts
        self.typed_graph_status = {
            "availability": availability,
            "reason": reason,
            "schema_version": "llm-wiki-typed-graph/v1",
            "coverage": [
                {
                    "analyzer": "calls",
                    "observed": 9,
                    "emitted": 8,
                    "omitted": 1,
                    "limit": 8,
                    "truncated": True,
                    "limitations": ["dynamic-dispatch"],
                }
            ],
        }
        self.traversals: list[tuple[str, dict]] = []

    def traverse_typed_graph(self, locator: str, **options) -> dict:
        self.traversals.append((locator, dict(options)))
        all_total, selected_total = self.graph_counts.get(locator, (0, 0))
        has_refinement = (
            options.get("direction", "both") != "both"
            or options.get("kinds") is not None
            or options.get("origins") is not None
            or options.get("resolutions") is not None
        )
        total = selected_total if has_refinement else all_total
        if self.typed_graph_status["availability"] != "ready":
            total = 0
        returned = min(total, 1)
        edges = [
            {
                "evidence": {
                    "aggregate_input_hash": "sha256:" + ("1" * 64),
                    "samples": [{"kind": "call"}],
                },
                "coverage": {
                    "observed": 7,
                    "emitted": 5,
                    "omitted": 2,
                    "limit": 5,
                    "truncated": True,
                    "limitations": ["polymorphism"],
                },
            }
            for _ in range(returned)
        ]
        return {
            "found": True,
            "typed_graph": self.typed_graph_status,
            "total": total,
            "returned": returned,
            "truncated": total > returned,
            "edges": edges,
        }


@pytest.mark.parametrize(
    "case",
    COMPATIBILITY_CASES,
    ids=lambda case: case.id,
)
def test_context_v1_uses_shared_knowledge_compatibility_policy(
    tmp_path,
    monkeypatch,
    case,
):
    root = tmp_path / "checkout"
    wiki = root / "docs" / "llm_wiki"
    wiki.mkdir(parents=True)
    fixture = _materialize_case(wiki, case)
    for relative_path, content in fixture.source_files.items():
        source = root / relative_path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(content, encoding="utf-8")
    monkeypatch.chdir(root)

    payload, warnings = context_cmd._build_context(
        ".",
        32_000,
        "json",
        ["all"],
        {"surface": "entities"},
        emit_warnings=False,
        wiki_dir="docs/llm_wiki",
    )

    expected_status = {
        "availability": case.expected_availability.value,
        "reason": case.expected_reason.value,
        "freshness": (
            "evaluated (6 concepts)"
            if case.serves_knowledge
            else "unevaluated (snapshot-only read)"
        ),
        "freshness_evaluated": case.serves_knowledge,
    }
    assert context_cmd.PROTOCOL_VERSION == "llm-wiki-context/v1"
    assert payload["knowledge"] == expected_status
    assert [
        (page["canonical_path"], page["mcp_uri"])
        for page in payload["surface"]["pages"]
    ] == [
        ("entities/AccountService.md", "llm-wiki://entities/AccountService"),
        ("entities/User.md", "llm-wiki://entities/User"),
    ]
    if case.serves_knowledge:
        assert all(
            page["knowledge"]["availability"] == "ready"
            and "freshness" in page["knowledge"]
            for page in payload["surface"]["pages"]
        )
    else:
        assert all(
            page["knowledge"]
            == {
                "availability": expected_status["availability"],
                "reason": expected_status["reason"],
                "freshness_disclosure": expected_status["freshness"],
                "freshness_evaluated": False,
            }
            for page in payload["surface"]["pages"]
        )
        assert any(
            case.expected_availability.value in warning for warning in warnings
        )


# ── Token estimation ──────────────────────────────────────────────────


class TestEstimateTokens:
    def test_empty_string(self):
        assert context_cmd._estimate_tokens("") == 0

    def test_short_string(self):
        assert context_cmd._estimate_tokens("hello") == 1  # 5 // 4

    def test_typical_string(self):
        text = "x" * 400
        assert context_cmd._estimate_tokens(text) == 100  # 400 // 4


# ── Filepath to module ────────────────────────────────────────────────


class TestFilepathToModule:
    def test_simple(self):
        assert context_cmd._filepath_to_module("config.py") == "config"

    def test_nested(self):
        assert (
            context_cmd._filepath_to_module("llm_wiki_cli/config.py")
            == "llm_wiki_cli.config"
        )

    def test_src_prefix(self):
        assert (
            context_cmd._filepath_to_module("src/llm_wiki_cli/config.py")
            == "llm_wiki_cli.config"
        )

    def test_init(self):
        assert (
            context_cmd._filepath_to_module("src/llm_wiki_cli/__init__.py")
            == "llm_wiki_cli"
        )

    def test_non_python(self):
        assert context_cmd._filepath_to_module("README.md") is None


# ── Import graph ──────────────────────────────────────────────────────


class TestBuildImportGraph:
    def test_no_imports(self):
        inventory = {
            "a.py": {"classes": [], "functions": [], "imports": []},
            "b.py": {"classes": [], "functions": [], "imports": []},
        }
        graph = context_cmd._build_import_graph(inventory)
        assert graph["a.py"] == set()
        assert graph["b.py"] == set()

    def test_one_import(self):
        inventory = {
            "a.py": {
                "classes": [],
                "functions": [],
                "imports": [{"module": "b", "name": "foo", "type": "from"}],
            },
            "b.py": {"classes": [], "functions": [], "imports": []},
        }
        graph = context_cmd._build_import_graph(inventory)
        assert "b.py" in graph["a.py"]
        assert "a.py" in graph["b.py"]  # bidirectional

    def test_external_import_skipped(self):
        inventory = {
            "a.py": {
                "classes": [],
                "functions": [],
                "imports": [{"module": "json", "name": "json", "type": "import"}],
            },
        }
        graph = context_cmd._build_import_graph(inventory)
        assert graph["a.py"] == set()

    def test_nested_module_match(self):
        inventory = {
            "src/pkg/mod.py": {
                "classes": [],
                "functions": [],
                "imports": [{"module": "pkg.utils", "name": "helper", "type": "from"}],
            },
            "src/pkg/utils.py": {"classes": [], "functions": [], "imports": []},
        }
        graph = context_cmd._build_import_graph(inventory)
        assert "src/pkg/utils.py" in graph["src/pkg/mod.py"]


# ── Classification ────────────────────────────────────────────────────


class TestClassifyFiles:
    def test_focus_all(self):
        files = ["a.py", "b.py", "c.py"]
        result = context_cmd._classify_files(files, None, {}, "all")
        assert all(v == "high" for v in result.values())

    def test_changed_high_neighbor_medium_rest_low(self):
        files = ["a.py", "b.py", "c.py"]
        graph = {
            "a.py": {"b.py"},
            "b.py": {"a.py"},
            "c.py": set(),
        }
        result = context_cmd._classify_files(files, ["a.py"], graph, "changed")
        assert result["a.py"] == "high"
        assert result["b.py"] == "medium"
        assert result["c.py"] == "low"

    def test_no_changed_files(self):
        files = ["a.py", "b.py"]
        result = context_cmd._classify_files(files, [], {}, "changed")
        assert result["a.py"] == "low"
        assert result["b.py"] == "low"


# ── Serializers ───────────────────────────────────────────────────────


class TestSerializers:
    def test_deep_entry_strips_language(self):
        data = {"language": "python", "classes": [{"name": "X"}], "functions": []}
        result = context_cmd._deep_entry(data)
        assert "language" not in result
        assert result["classes"] == [{"name": "X"}]

    def test_slim_entry(self):
        data = {
            "classes": [{"name": "X", "bases": ["Y"], "line": 1, "docstring": "doc"}],
            "functions": [{"name": "f", "line": 5, "docstring": "doc"}],
        }
        result = context_cmd._slim_entry(data)
        assert result["classes"] == [{"name": "X", "bases": ["Y"], "line": 1}]
        assert result["functions"] == [{"name": "f", "line": 5}]

    def test_summary_entry(self):
        data = {
            "classes": [{"name": "A"}, {"name": "B"}],
            "functions": [{"name": "f"}],
        }
        result = context_cmd._summary_entry(data)
        assert result == {"classes": ["A", "B"], "functions": ["f"]}


# ── Budget payload ────────────────────────────────────────────────────


class TestBuildContextPayload:
    def test_all_high_within_budget(self):
        inventory = {
            "a.py": {"classes": [{"name": "X"}], "functions": []},
        }
        classification = {"a.py": "high"}
        result = context_cmd._build_context_payload(inventory, classification, 100000)
        assert result["budget"] == 100000
        assert result["used"] > 0
        assert "a.py" in result["files"]
        assert result["files"]["a.py"]["priority"] == "high"
        assert result["files"]["a.py"]["detail"] == "deep"
        assert result["truncated"] is False
        assert result["omitted_files"] == []
        assert result["downgraded_files"] == {}
        assert result["bounds"]["files"] == {
            "total": 1,
            "returned": 1,
            "truncated": False,
        }

    def test_prefer_fresh_is_opt_in_and_breaks_ties_only_within_tier(self):
        file_data = {
            "language": "python",
            "classes": [],
            "functions": [{"name": "run", "line": 1}],
        }
        inventory = {
            "a_old.py": file_data,
            "z_new.py": file_data,
        }
        classification = {
            "a_old.py": "high",
            "z_new.py": "high",
        }
        budget = context_cmd._entry_tokens(
            "a_old.py",
            context_cmd._build_entry(file_data, "high", "deep"),
        )

        baseline = context_cmd._build_context_payload(
            inventory,
            classification,
            budget,
        )
        explicit_off = context_cmd._build_context_payload(
            inventory,
            classification,
            budget,
            freshness_rank_by_source=None,
        )
        preferred = context_cmd._build_context_payload(
            inventory,
            classification,
            budget,
            freshness_rank_by_source={
                "a_old.py": 1,
                "z_new.py": 0,
            },
        )
        regenerated = context_cmd._build_context_payload(
            inventory,
            classification,
            budget,
            freshness_rank_by_source={
                "a_old.py": 1,
                "z_new.py": 0,
            },
        )

        assert json.dumps(explicit_off, sort_keys=False) == json.dumps(
            baseline,
            sort_keys=False,
        )
        assert json.dumps(regenerated, sort_keys=False) == json.dumps(
            preferred,
            sort_keys=False,
        )
        assert list(baseline["files"]) == ["a_old.py"]
        assert list(preferred["files"]) == ["z_new.py"]
        assert preferred["omitted_files"] == ["a_old.py"]
        assert preferred["bounds"]["files"]["total"] == 2

    def test_prefer_fresh_never_reorders_across_relevance_tiers(self):
        file_data = {
            "language": "python",
            "classes": [],
            "functions": [{"name": "run", "line": 1}],
        }
        inventory = {
            "a_old.py": file_data,
            "z_new.py": file_data,
        }
        classification = {
            "a_old.py": "high",
            "z_new.py": "low",
        }
        budget = context_cmd._entry_tokens(
            "a_old.py",
            context_cmd._build_entry(file_data, "high", "deep"),
        )

        preferred = context_cmd._build_context_payload(
            inventory,
            classification,
            budget,
            freshness_rank_by_source={
                "a_old.py": 1,
                "z_new.py": 0,
            },
        )

        assert list(preferred["files"]) == ["a_old.py"]
        assert preferred["files"]["a_old.py"]["priority"] == "high"
        assert preferred["omitted_files"] == ["z_new.py"]

    def test_prefer_fresh_does_not_reorder_without_budget_pressure(self):
        file_data = {
            "language": "python",
            "classes": [],
            "functions": [{"name": "run", "line": 1}],
        }
        inventory = {
            "a_old.py": file_data,
            "z_new.py": file_data,
        }
        classification = {
            "a_old.py": "high",
            "z_new.py": "high",
        }

        baseline = context_cmd._build_context_payload(
            inventory,
            classification,
            100_000,
        )
        preferred, budget_pressure = (
            context_cmd._build_context_payload_with_freshness_preference(
                inventory,
                classification,
                100_000,
                freshness_rank_by_source={
                    "a_old.py": 1,
                    "z_new.py": 0,
                },
            )
        )

        assert budget_pressure is False
        assert json.dumps(preferred, sort_keys=False) == json.dumps(
            baseline,
            sort_keys=False,
        )
        assert list(preferred["files"]) == ["a_old.py", "z_new.py"]

    def test_prefer_fresh_flag_off_matches_protocol_baseline_golden(self):
        inventory, classification, budget = _freshness_ranking_golden_inputs()
        payload = context_cmd._build_context_payload(
            inventory,
            classification,
            budget,
        )
        request_without_flag = context_cmd._validate_protocol_request(
            _protocol_request(budget_tokens=budget)
        )
        request_with_explicit_off = context_cmd._validate_protocol_request(
            _protocol_request(
                budget_tokens=budget,
                prefer_fresh=False,
            )
        )

        without_flag = _protocol_output_bytes(request_without_flag, payload)
        explicit_off = _protocol_output_bytes(
            request_with_explicit_off,
            payload,
        )

        assert without_flag == explicit_off
        assert without_flag == PREFER_FRESH_OFF_GOLDEN.read_bytes()
        assert b'"prefer_fresh"' not in without_flag
        assert b'"ranking_policy"' not in without_flag

    def test_prefer_fresh_flag_on_matches_deterministic_protocol_golden(self):
        inventory, classification, budget = _freshness_ranking_golden_inputs()
        ranks = {
            "a_stale.py": 1,
            "z_fresh.py": 0,
        }

        def render() -> bytes:
            payload, budget_pressure = (
                context_cmd._build_context_payload_with_freshness_preference(
                    inventory,
                    classification,
                    budget,
                    freshness_rank_by_source=ranks,
                )
            )
            payload["ranking_policy"] = context_cmd._freshness_ranking_policy(
                {"freshness_evaluated": True},
                ranks,
                budget_pressure=budget_pressure,
            )
            request = context_cmd._validate_protocol_request(
                _protocol_request(
                    budget_tokens=budget,
                    prefer_fresh=True,
                )
            )
            return _protocol_output_bytes(request, payload)

        first = render()
        second = render()

        assert first == second
        assert first == PREFER_FRESH_ON_GOLDEN.read_bytes()
        payload = json.loads(first)
        assert payload["ranking_policy"]["applied"] is True
        assert list(payload["files"]) == ["z_fresh.py"]
        assert payload["omitted_files"] == ["a_stale.py"]
        assert b"example.invalid" not in first

    def test_high_downgraded_before_omit(self):
        inventory = {
            "a.py": {
                "classes": [
                    {
                        "name": "X",
                        "bases": [],
                        "line": 1,
                        "docstring": "D" * 1000,
                        "methods": [{"name": "run", "params": [], "return_type": None}],
                    }
                ],
                "functions": [],
                "imports": [{"module": "huge", "name": "Huge", "type": "from"}],
            },
        }
        classification = {"a.py": "high"}
        summary = context_cmd._build_entry(inventory["a.py"], "high", "summary")
        budget = context_cmd._entry_tokens("a.py", summary)

        result = context_cmd._build_context_payload(inventory, classification, budget)

        assert "a.py" in result["files"]
        assert result["files"]["a.py"]["detail"] == "summary"
        assert result["downgraded_files"] == {"a.py": "summary"}
        assert result["omitted_files"] == []
        assert result["used"] <= result["budget"]
        assert result["truncated"] is True
        assert result["bounds"]["files"] == {
            "total": 1,
            "returned": 1,
            "truncated": False,
        }

    def test_high_omitted_when_summary_does_not_fit(self):
        inventory = {
            "a.py": {"classes": [{"name": "X" * 100}], "functions": []},
        }
        classification = {"a.py": "high"}

        result = context_cmd._build_context_payload(inventory, classification, 1)

        assert result["files"] == {}
        assert result["omitted_files"] == ["a.py"]
        assert result["downgraded_files"] == {}
        assert result["used"] == 0
        assert result["truncated"] is True
        assert result["bounds"]["files"] == {
            "total": 1,
            "returned": 0,
            "truncated": True,
        }

    def test_medium_and_low_omitted_on_tight_budget(self):
        inventory = {
            "a.py": {"classes": [{"name": "A"}], "functions": []},
            "b.py": {"classes": [{"name": "B"}], "functions": []},
            "c.py": {"classes": [{"name": "C"}], "functions": []},
        }
        classification = {"a.py": "high", "b.py": "medium", "c.py": "low"}
        high_entry = context_cmd._build_entry(inventory["a.py"], "high", "deep")
        budget = context_cmd._entry_tokens("a.py", high_entry)

        result = context_cmd._build_context_payload(inventory, classification, budget)

        assert "a.py" in result["files"]
        assert "b.py" not in result["files"]
        assert "c.py" not in result["files"]
        assert result["omitted_files"] == ["b.py", "c.py"]
        assert result["used"] <= result["budget"]
        assert result["bounds"]["files"] == {
            "total": 3,
            "returned": 1,
            "truncated": True,
        }

    def test_later_smaller_file_included_after_large_omitted_file(self):
        inventory = {
            "a.py": {"classes": [{"name": "X" * 200}], "functions": []},
            "b.py": {"classes": [{"name": "B"}], "functions": []},
        }
        classification = {"a.py": "high", "b.py": "high"}
        small_summary = context_cmd._build_entry(inventory["b.py"], "high", "summary")
        budget = context_cmd._entry_tokens("b.py", small_summary)

        result = context_cmd._build_context_payload(inventory, classification, budget)

        assert "a.py" not in result["files"]
        assert "b.py" in result["files"]
        assert result["files"]["b.py"]["detail"] == "summary"
        assert result["omitted_files"] == ["a.py"]
        assert result["downgraded_files"] == {"b.py": "summary"}
        assert result["used"] <= result["budget"]
        assert result["bounds"]["files"] == {
            "total": 2,
            "returned": 1,
            "truncated": True,
        }

    def test_output_has_priority_field(self):
        inventory = {
            "a.py": {"classes": [], "functions": [{"name": "f"}]},
            "b.py": {"classes": [], "functions": [{"name": "g"}]},
        }
        classification = {"a.py": "high", "b.py": "low"}
        result = context_cmd._build_context_payload(inventory, classification, 100000)
        assert result["files"]["a.py"]["priority"] == "high"
        assert result["files"]["b.py"]["priority"] == "low"
        assert result["files"]["a.py"]["detail"] == "deep"
        assert result["files"]["b.py"]["detail"] == "summary"


# ── Markdown rendering ───────────────────────────────────────────────


class TestRenderMarkdown:
    def test_contains_tier_headers(self):
        payload = {
            "budget": 1000,
            "used": 50,
            "files": {
                "a.py": {
                    "priority": "high",
                    "classes": [{"name": "X", "bases": []}],
                    "functions": [],
                },
                "b.py": {"priority": "low", "classes": [], "functions": ["f"]},
            },
        }
        md = context_cmd._render_markdown(payload)
        assert "Changed Files (High Priority)" in md
        assert "Index (Low Priority)" in md
        assert "50 / 1000 tokens" in md

    def test_contains_omitted_files_section(self):
        payload = {
            "budget": 10,
            "used": 0,
            "files": {},
            "omitted_files": ["too_big.py"],
        }
        md = context_cmd._render_markdown(payload)
        assert "Omitted Files" in md
        assert "`too_big.py`" in md

    def test_contains_graph_and_surface_sections(self):
        payload = {
            "budget": 10,
            "used": 0,
            "files": {},
            "graphs": {
                "symbol": {
                    "callers": {"query": "run", "found": True},
                    "callees": {"query": "run", "found": True},
                    "pages": {"query": "run", "found": True},
                },
                "entrypoint": {
                    "flow": {"query": "api-run", "found": True},
                    "data_flow": {"query": "api-run", "found": True},
                },
            },
            "surface": {
                "kind": "flows",
                "count": 1,
                "truncated": False,
                "pages": [
                    {
                        "id": "api-run",
                        "title": "api-run",
                        "canonical_path": "flows/api-run.md",
                        "mcp_uri": "llm-wiki://flows/api-run",
                    }
                ],
            },
        }

        md = context_cmd._render_markdown(payload)

        assert "Documentation Graphs" in md
        assert "Symbol `run`" in md
        assert "Entry point `api-run`" in md
        assert "Surface `flows`" in md
        assert "`flows/api-run.md`" in md

    def test_basis_incompatibility_renders_machine_reason_and_action_hint(self):
        reason = "generation-options-changed"
        hint = BASIS_INCOMPATIBLE_HINTS[reason]
        payload = {
            "budget": 10,
            "used": 0,
            "files": {},
            "surface": {
                "kind": "entities",
                "count": 1,
                "truncated": False,
                "pages": [
                    {
                        "id": "User",
                        "title": "User",
                        "canonical_path": "entities/User.md",
                        "mcp_uri": "llm-wiki://entities/User",
                        "knowledge": {
                            "availability": "ready",
                            "freshness": {
                                "state": "basis-incompatible",
                                "reason": reason,
                                "hint": hint,
                                "live_comparison_performed": True,
                            },
                        },
                    }
                ],
            },
        }

        markdown = context_cmd._render_markdown(payload)

        assert f"freshness reason: `{reason}`" in markdown
        assert f"freshness hint: {hint}" in markdown

    def test_prefer_fresh_policy_is_disclosed(self):
        payload = {
            "budget": 10,
            "used": 0,
            "files": {},
            "ranking_policy": {
                "name": "relevance-then-current-freshness",
                "prefer_fresh": True,
                "scope": "within-relevance-tiers",
                "freshness_evaluated": True,
                "applied": True,
                "filters_stale_content": False,
            },
        }

        markdown = context_cmd._render_markdown(payload)

        assert (
            "current freshness is preferred only within existing relevance tiers"
            in markdown
        )


# ── Protocol helpers ──────────────────────────────────────────────────


class TestProtocolValidation:
    def test_protocol_version_remains_context_v1(self):
        assert context_cmd.PROTOCOL_VERSION == "llm-wiki-context/v1"

    def test_language_filter(self):
        inventory = {
            "src/api/users.py": {"language": "python"},
            "web/api/client.ts": {"language": "typescript"},
        }
        result = context_cmd._apply_protocol_filters(inventory, {"language": "python"})
        assert set(result) == {"src/api/users.py"}

    def test_module_filter_matches_dotted_python_module(self):
        inventory = {
            "src/api/users.py": {"language": "python"},
            "src/db/models.py": {"language": "python"},
        }
        result = context_cmd._apply_protocol_filters(inventory, {"module": "api/*"})
        assert set(result) == {"src/api/users.py"}

    def test_module_filter_matches_path_glob(self):
        inventory = {
            "src/api/users.py": {"language": "python"},
            "web/api/client.ts": {"language": "typescript"},
        }
        result = context_cmd._apply_protocol_filters(inventory, {"module": "web/api/*"})
        assert set(result) == {"web/api/client.ts"}

    def test_validation_defaults(self):
        result = context_cmd._validate_protocol_request(
            {
                "protocol": context_cmd.PROTOCOL_VERSION,
                "budget_tokens": 1000,
            }
        )
        assert result["focus"] == ["changed", "neighbors"]
        assert result["format"] == "json"
        assert result["filters"] == {}
        assert result["prefer_fresh"] is False

    def test_validation_accepts_boolean_prefer_fresh(self):
        result = context_cmd._validate_protocol_request(
            _protocol_request(prefer_fresh=True)
        )

        assert result["prefer_fresh"] is True

    @pytest.mark.parametrize("value", [1, "true", [], None])
    def test_validation_rejects_non_boolean_prefer_fresh(self, value):
        with pytest.raises(
            context_cmd.ProtocolRequestError,
            match="prefer_fresh must be a boolean",
        ) as exc_info:
            context_cmd._validate_protocol_request(
                _protocol_request(prefer_fresh=value)
            )

        assert exc_info.value.field == "prefer_fresh"

    def test_validation_accepts_graph_and_surface_filters(self):
        result = context_cmd._validate_protocol_request(
            _protocol_request(
                filters={
                    "language": "python",
                    "module": "api/*",
                    "symbol": "api.py:run",
                    "entrypoint": "api-run",
                    "surface": "flows",
                }
            )
        )

        assert result["filters"] == {
            "language": "python",
            "module": "api/*",
            "symbol": "api.py:run",
            "entrypoint": "api-run",
            "surface": "flows",
        }

    @pytest.mark.parametrize(
        "relationship_kind",
        ["calls", "supersedes", "vendor.plugin/invokes"],
    )
    def test_validation_accepts_scalar_typed_relationship_filters(
        self,
        relationship_kind,
    ):
        result = context_cmd._validate_protocol_request(
            _protocol_request(
                filters={
                    "surface": "entities",
                    "relationship_kind": relationship_kind,
                    "relationship_origin": "extracted",
                    "relationship_resolution": "resolved",
                    "relationship_direction": "incoming",
                }
            )
        )

        assert result["filters"] == {
            "surface": "entities",
            "relationship_kind": relationship_kind,
            "relationship_origin": "extracted",
            "relationship_resolution": "resolved",
            "relationship_direction": "incoming",
        }

    @pytest.mark.parametrize(
        ("filters", "field"),
        [
            ({"relationship_kind": "calls"}, "filters.relationship_kind"),
            (
                {"entrypoint": "api-run", "relationship_origin": "extracted"},
                "filters.relationship_origin",
            ),
            (
                {"language": "python", "relationship_resolution": "resolved"},
                "filters.relationship_resolution",
            ),
            (
                {"module": "api/*", "relationship_direction": "both"},
                "filters.relationship_direction",
            ),
        ],
    )
    def test_typed_relationship_filter_requires_concept_producer(
        self,
        filters,
        field,
    ):
        with pytest.raises(context_cmd.ProtocolRequestError) as exc_info:
            context_cmd._validate_protocol_request(
                _protocol_request(filters=filters)
            )

        assert exc_info.value.field == field
        assert "requires filters.surface or filters.symbol" in str(exc_info.value)

    @pytest.mark.parametrize(
        ("filters", "field"),
        [
            (
                {"surface": "entities", "relationship_kind": "unqualified"},
                "filters.relationship_kind",
            ),
            (
                {"symbol": "User", "relationship_origin": "guessed"},
                "filters.relationship_origin",
            ),
            (
                {"symbol": "User", "relationship_resolution": "partial"},
                "filters.relationship_resolution",
            ),
            (
                {"surface": "entities", "relationship_direction": "inbound"},
                "filters.relationship_direction",
            ),
            (
                {"surface": "entities", "relationship_kind": ["calls"]},
                "filters.relationship_kind",
            ),
        ],
    )
    def test_validation_rejects_invalid_typed_relationship_filters(
        self,
        filters,
        field,
    ):
        with pytest.raises(context_cmd.ProtocolRequestError) as exc_info:
            context_cmd._validate_protocol_request(
                _protocol_request(filters=filters)
            )

        assert exc_info.value.field == field

    @pytest.mark.parametrize(
        "freshness",
        [
            "current",
            "nonsemantic-source-change",
            "unknown",
            "source-changed",
            "source-missing",
            "basis-incompatible",
        ],
    )
    def test_validation_accepts_every_freshness_refinement(self, freshness):
        result = context_cmd._validate_protocol_request(
            _protocol_request(
                filters={"surface": "entities", "freshness": freshness}
            )
        )

        assert result["filters"] == {
            "surface": "entities",
            "freshness": freshness,
        }

    @pytest.mark.parametrize(
        "evidence",
        ["unknown", "present", "missing", "invalid", "not-applicable"],
    )
    def test_validation_accepts_every_evidence_refinement(self, evidence):
        result = context_cmd._validate_protocol_request(
            _protocol_request(
                filters={
                    "symbol": "src/accounts.py:User",
                    "evidence": evidence,
                }
            )
        )

        assert result["filters"] == {
            "symbol": "src/accounts.py:User",
            "evidence": evidence,
        }

    @pytest.mark.parametrize(
        ("filters", "field"),
        [
            ({"freshness": "current"}, "filters.freshness"),
            (
                {"entrypoint": "api-run", "freshness": "current"},
                "filters.freshness",
            ),
            ({"language": "python", "evidence": "present"}, "filters.evidence"),
            ({"module": "api/*", "evidence": "present"}, "filters.evidence"),
        ],
    )
    def test_knowledge_refinement_requires_a_concept_producing_filter(
        self, filters, field
    ):
        with pytest.raises(context_cmd.ProtocolRequestError) as exc_info:
            context_cmd._validate_protocol_request(
                _protocol_request(filters=filters)
            )

        assert exc_info.value.field == field
        assert "requires filters.surface or filters.symbol" in str(exc_info.value)

    @pytest.mark.parametrize(
        ("filters", "field"),
        [
            (
                {"surface": "entities", "freshness": "stale"},
                "filters.freshness",
            ),
            (
                {"symbol": "User", "freshness": 1},
                "filters.freshness",
            ),
            (
                {"surface": "entities", "evidence": "trusted"},
                "filters.evidence",
            ),
            (
                {"symbol": "User", "evidence": None},
                "filters.evidence",
            ),
        ],
    )
    def test_validation_rejects_invalid_knowledge_refinements(
        self, filters, field
    ):
        with pytest.raises(context_cmd.ProtocolRequestError) as exc_info:
            context_cmd._validate_protocol_request(
                _protocol_request(filters=filters)
            )

        assert exc_info.value.field == field


class TestKnowledgePageSelection:
    def test_source_freshness_rank_requires_every_mapped_concept_current(self):
        current_page, current = _knowledge_page_fixture(
            "entities/Current.md",
            freshness="current",
        )
        mixed_current_page, mixed_current = _knowledge_page_fixture(
            "entities/MixedCurrent.md",
            freshness="current",
        )
        mixed_stale_page, mixed_stale = _knowledge_page_fixture(
            "entities/MixedStale.md",
            freshness="source-changed",
        )
        mixed_current_page["source_path"] = "src/mixed.py"
        mixed_stale_page["source_path"] = "src/mixed.py"
        service = _KnowledgeQueryStub(
            {
                current_page["canonical_path"]: current,
                mixed_current_page["canonical_path"]: mixed_current,
                mixed_stale_page["canonical_path"]: mixed_stale,
            }
        )

        ranks = context_cmd._context_freshness_rank_by_source(
            {
                "pages": [
                    current_page,
                    mixed_current_page,
                    mixed_stale_page,
                ]
            },
            service,
        )

        assert ranks == {
            "src/Current.py": 0,
            "src/mixed.py": 1,
        }
        policy = context_cmd._freshness_ranking_policy(
            service.knowledge_status,
            ranks,
        )
        assert policy == {
            "name": "relevance-then-current-freshness",
            "prefer_fresh": True,
            "scope": "within-relevance-tiers",
            "freshness_evaluated": True,
            "budget_pressure": False,
            "applied": False,
            "filters_stale_content": False,
        }

    def test_source_freshness_rank_treats_missing_state_as_non_current(self):
        current_page, current = _knowledge_page_fixture(
            "entities/MixedCurrent.md",
            freshness="current",
        )
        unknown_page, _ = _knowledge_page_fixture(
            "entities/MixedUnknown.md",
            freshness="current",
        )
        current_page["source_path"] = "src/mixed.py"
        unknown_page["source_path"] = "src/mixed.py"
        service = _KnowledgeQueryStub(
            {current_page["canonical_path"]: current}
        )

        ranks = context_cmd._context_freshness_rank_by_source(
            {"pages": [current_page, unknown_page]},
            service,
        )

        assert ranks == {"src/mixed.py": 1}

    def test_source_freshness_rank_is_unavailable_without_evaluation(self):
        page, concept = _knowledge_page_fixture(
            "entities/User.md",
            freshness="current",
        )
        service = _KnowledgeQueryStub(
            {page["canonical_path"]: concept},
            freshness_evaluated=False,
        )

        ranks = context_cmd._context_freshness_rank_by_source(
            {"pages": [page]},
            service,
        )

        assert ranks == {}
        assert context_cmd._freshness_ranking_policy(
            service.knowledge_status,
            ranks,
        )["applied"] is False

    def test_governed_summary_is_compact_and_omits_private_event_detail(self):
        page, concept = _knowledge_page_fixture(
            "entities/User.md",
            freshness="source-changed",
        )
        concept.update(
            {
                "lifecycle": "superseded",
                "successor_uid": "lw:entity:successor",
                "reviews": {
                    "items": [
                        {
                            "state": "valid",
                            "reasons": [],
                            "reviewer": {
                                "kind": "human",
                                "id": "private-reviewer@example.invalid",
                            },
                            "authored_at": "2026-07-27T09:30:00Z",
                            "event_id": "rv_private",
                            "method": {"id": "manual-review", "version": "2"},
                        },
                        {
                            "state": "expired",
                            "reasons": ["scope-changed", "not/a-machine-code"],
                            "reviewer": {
                                "kind": "human",
                                "id": "other-private@example.invalid",
                            },
                        },
                    ],
                    "total": 2,
                    "returned": 2,
                    "limit": 20,
                    "truncated": False,
                },
                "machine_verification": {
                    "availability": "recorded",
                    "scope_uid": "bundle:private",
                    "valid": True,
                    "invalidation_reasons": [],
                    "recorded_result": "failed",
                    "passed": False,
                    "checks": {
                        "internal-links": {
                            "result": "failed",
                            "diagnostics": [
                                {
                                    "code": "private-diagnostic",
                                    "subject": "/private/checkout",
                                }
                            ],
                        },
                        "artifact-integrity": {
                            "result": "passed",
                            "diagnostics": [],
                        },
                    },
                },
            }
        )
        service = _KnowledgeQueryStub({page["canonical_path"]: concept})

        enriched = context_cmd._knowledge_enriched_page_ref(page, service)

        assert enriched["knowledge"] == {
            "availability": "ready",
            "reason": "all-projection-commitments-match",
            "freshness_disclosure": "evaluated (1 concepts)",
            "freshness_evaluated": True,
            "origin": "extracted",
            "evidence": "present",
            "verification": "untracked",
            "freshness": {
                "state": "source-changed",
                "reason": "fixture-source-changed",
                "live_comparison_performed": True,
            },
            "lifecycle": "superseded",
            "successor_uid": "lw:entity:successor",
            "review": {
                "scope": "section",
                "state": "mixed",
                "total": 2,
                "returned": 2,
                "valid_returned": 1,
                "expired_returned": 1,
                "truncated": False,
                "reasons": ["scope-changed"],
            },
            "machine_verification": {
                "availability": "recorded",
                "valid": True,
                "recorded_result": "failed",
                "passed": False,
                "checks": {
                    "total": 2,
                    "passed": 1,
                    "failed": 1,
                },
                "invalidation_reasons": [],
            },
        }
        encoded = json.dumps(enriched, sort_keys=True)
        for forbidden in (
            "private-reviewer",
            "other-private",
            "authored_at",
            "event_id",
            "manual-review",
            "scope_uid",
            "diagnostics",
            "/private/checkout",
            "private-diagnostic",
        ):
            assert forbidden not in encoded

    def test_invalid_machine_receipt_stays_unevaluable(self):
        page, concept = _knowledge_page_fixture(
            "entities/User.md",
            freshness="current",
        )
        concept["machine_verification"] = {
            "availability": "invalid",
            "reason": "receipt-invalid",
        }
        service = _KnowledgeQueryStub({page["canonical_path"]: concept})

        enriched = context_cmd._knowledge_enriched_page_ref(page, service)

        assert enriched["knowledge"]["machine_verification"] == {
            "availability": "invalid",
            "reason": "receipt-invalid",
        }
        assert "valid" not in enriched["knowledge"]["machine_verification"]
        assert "passed" not in enriched["knowledge"]["machine_verification"]
        assert (
            "recorded_result"
            not in enriched["knowledge"]["machine_verification"]
        )

    def test_orders_by_freshness_then_evidence_presence_then_path(self):
        specs = [
            ("entities/basis.md", "basis-incompatible", "present"),
            ("entities/missing.md", "source-missing", "present"),
            ("entities/changed.md", "source-changed", "present"),
            ("entities/unknown.md", "unknown", "present"),
            ("entities/nonsemantic.md", "nonsemantic-source-change", "present"),
            ("entities/current-missing.md", "current", "missing"),
            ("entities/current-z.md", "current", "present"),
            ("entities/current-a.md", "current", "present"),
        ]
        fixtures = [
            _knowledge_page_fixture(path, freshness=state, evidence=evidence)
            for path, state, evidence in reversed(specs)
        ]
        pages = [page for page, _concept in fixtures]
        service = _KnowledgeQueryStub(
            {
                page["canonical_path"]: concept
                for page, concept in fixtures
            }
        )

        selected, counts = context_cmd._select_knowledge_page_refs(
            pages,
            {},
            service,
            limit=20,
            observed=[],
        )

        assert [page["canonical_path"] for page in selected] == [
            "entities/current-a.md",
            "entities/current-z.md",
            "entities/current-missing.md",
            "entities/nonsemantic.md",
            "entities/unknown.md",
            "entities/changed.md",
            "entities/missing.md",
            "entities/basis.md",
        ]
        assert counts == {
            "unfiltered_total": 8,
            "filtered_total": 8,
            "returned": 8,
            "truncated": False,
        }

    def test_filters_before_limit_and_reports_both_candidate_totals(self):
        fixtures = [
            _knowledge_page_fixture(
                f"entities/current-{index:02d}.md",
                freshness="current",
            )
            for index in range(21)
        ]
        fixtures.append(
            _knowledge_page_fixture(
                "entities/target.md",
                freshness="source-changed",
                evidence="missing",
            )
        )
        pages = [page for page, _concept in fixtures]
        service = _KnowledgeQueryStub(
            {
                page["canonical_path"]: concept
                for page, concept in fixtures
            }
        )
        observed = []

        selected, counts = context_cmd._select_knowledge_page_refs(
            pages,
            {"freshness": "source-changed", "evidence": "missing"},
            service,
            limit=20,
            observed=observed,
        )

        assert [page["canonical_path"] for page in selected] == [
            "entities/target.md"
        ]
        assert counts == {
            "unfiltered_total": 22,
            "filtered_total": 1,
            "returned": 1,
            "truncated": False,
        }
        assert len(observed) == 22

        current, current_counts = context_cmd._select_knowledge_page_refs(
            pages,
            {"freshness": "current"},
            service,
            limit=20,
            observed=None,
        )
        assert len(current) == 20
        assert current_counts == {
            "unfiltered_total": 22,
            "filtered_total": 21,
            "returned": 20,
            "truncated": True,
        }

    @pytest.mark.parametrize(
        ("availability", "reason"),
        [
            ("absent", "knowledge-projection-not-present"),
            (
                "degraded",
                "policy-selected-surface-only-fallback-after-invalid",
            ),
            ("unsupported", "knowledge-schema-version-unsupported"),
        ],
    )
    def test_unavailable_knowledge_is_explicit_and_never_matches_unknown(
        self, availability, reason
    ):
        pages = [
            _knowledge_page_fixture(
                "entities/Zed.md",
                freshness="unknown",
            )[0],
            _knowledge_page_fixture(
                "entities/Alpha.md",
                freshness="current",
            )[0],
        ]
        service = _KnowledgeQueryStub(
            availability=availability,
            reason=reason,
            freshness_evaluated=False,
        )

        selected, counts = context_cmd._select_knowledge_page_refs(
            pages,
            {},
            service,
            limit=20,
            observed=[],
        )

        assert [page["canonical_path"] for page in selected] == [
            "entities/Alpha.md",
            "entities/Zed.md",
        ]
        assert all(
            page["knowledge"]
            == {
                "availability": availability,
                "reason": reason,
                "freshness_disclosure": "unevaluated (snapshot-only read)",
                "freshness_evaluated": False,
            }
            for page in selected
        )
        assert service.lookups == []
        assert counts["filtered_total"] == 2

        refined, refined_counts = context_cmd._select_knowledge_page_refs(
            pages,
            {"freshness": "unknown"},
            service,
            limit=20,
            observed=None,
        )
        assert refined == []
        assert refined_counts == {
            "unfiltered_total": 2,
            "filtered_total": 0,
            "returned": 0,
            "truncated": False,
        }

    def test_default_selection_warns_once_for_unique_stale_or_unknown_pages(self):
        fixtures = [
            _knowledge_page_fixture(
                "entities/Unknown.md",
                freshness="unknown",
            ),
            _knowledge_page_fixture(
                "entities/Changed.md",
                freshness="source-changed",
            ),
            _knowledge_page_fixture(
                "entities/Current.md",
                freshness="current",
            ),
        ]
        service = _KnowledgeQueryStub(
            {
                page["canonical_path"]: concept
                for page, concept in fixtures
            }
        )
        selected, _counts = context_cmd._select_knowledge_page_refs(
            [page for page, _concept in fixtures],
            {},
            service,
            limit=20,
            observed=[],
        )
        candidates = selected + [selected[-1]]
        warnings = []

        context_cmd._append_knowledge_context_warning(
            service.knowledge_status,
            candidates,
            {},
            warnings,
        )
        context_cmd._append_knowledge_context_warning(
            service.knowledge_status,
            candidates,
            {},
            warnings,
        )

        assert len(warnings) == 1
        assert warnings[0].startswith(
            "Knowledge context includes stale or unknown concept references "
        )
        assert "(unknown=1, source-changed=1)" in warnings[0]
        assert "retained" in warnings[0]

    def test_unavailable_refinement_warns_without_claiming_a_match(self):
        page, _concept = _knowledge_page_fixture(
            "entities/User.md",
            freshness="unknown",
        )
        service = _KnowledgeQueryStub(
            availability="degraded",
            reason="policy-selected-surface-only-fallback-after-invalid",
            freshness_evaluated=False,
        )
        candidates, _counts = context_cmd._select_knowledge_page_refs(
            [page],
            {},
            service,
            limit=20,
            observed=None,
        )
        warnings = []

        context_cmd._append_knowledge_context_warning(
            service.knowledge_status,
            candidates,
            {"freshness": "unknown"},
            warnings,
        )

        assert warnings == [
            (
                "Knowledge context is degraded "
                "(policy-selected-surface-only-fallback-after-invalid); concept "
                "ranking and requested refinements are unavailable."
            )
        ]

    def test_typed_graph_filters_before_page_limit_and_hides_evidence(self):
        fixtures = [
            _knowledge_page_fixture(
                f"entities/{name}.md",
                freshness="current",
            )
            for name in ("Alpha", "Beta", "Gamma")
        ]
        pages = [page for page, _concept in fixtures]
        concepts = {
            page["canonical_path"]: concept for page, concept in fixtures
        }
        service = _TypedGraphQueryStub(
            concepts,
            {
                pages[0]["mcp_uri"]: (5, 2),
                pages[1]["mcp_uri"]: (4, 0),
                pages[2]["mcp_uri"]: (3, 1),
            },
        )
        observed = []

        selected, counts = context_cmd._select_knowledge_page_refs(
            pages,
            {
                "relationship_kind": "calls",
                "relationship_origin": "extracted",
                "relationship_resolution": "resolved",
                "relationship_direction": "incoming",
            },
            service,
            limit=1,
            observed=observed,
        )

        assert [page["canonical_path"] for page in selected] == [
            "entities/Alpha.md"
        ]
        assert counts == {
            "unfiltered_total": 3,
            "filtered_total": 2,
            "returned": 1,
            "truncated": True,
        }
        assert len(observed) == 3
        graph = selected[0]["typed_graph"]
        assert graph == {
            "availability": "ready",
            "reason": "typed-graph-extension-ready",
            "coverage": {
                "scope": "returned-edges",
                "edges": 1,
                "observed": 7,
                "emitted": 5,
                "omitted": 2,
                "truncated": True,
                "limitations": ["polymorphism"],
            },
            "found": True,
            "direction": "incoming",
            "filters": {
                "relationship_kind": "calls",
                "relationship_origin": "extracted",
                "relationship_resolution": "resolved",
                "relationship_direction": "incoming",
            },
            "unfiltered_total": 5,
            "filtered_total": 2,
            "returned": 1,
            "truncated": True,
        }
        encoded = json.dumps(graph, sort_keys=True)
        assert "samples" not in encoded
        assert "aggregate_input_hash" not in encoded
        assert len(service.traversals) == 6
        assert all(
            options["include_evidence"] is False
            for _locator, options in service.traversals
        )

    @pytest.mark.parametrize(
        ("availability", "reason"),
        [
            ("absent", "typed-graph-extension-not-present"),
            (
                "degraded",
                "policy-selected-surface-only-fallback-after-invalid",
            ),
        ],
    )
    def test_unavailable_typed_graph_is_explicit_and_does_not_drop_pages(
        self,
        availability,
        reason,
    ):
        page, concept = _knowledge_page_fixture(
            "entities/User.md",
            freshness="current",
        )
        service = _TypedGraphQueryStub(
            {page["canonical_path"]: concept},
            {page["mcp_uri"]: (0, 0)},
            availability=availability,
            reason=reason,
        )

        selected, counts = context_cmd._select_knowledge_page_refs(
            [page],
            {"relationship_kind": "calls"},
            service,
            limit=20,
            observed=[],
        )
        warnings = []
        context_cmd._append_typed_graph_context_warning(
            service.typed_graph_status,
            selected,
            warnings,
        )

        assert counts["filtered_total"] == 1
        assert selected[0]["typed_graph"]["availability"] == availability
        assert selected[0]["typed_graph"]["filtered_total"] == 0
        assert warnings == [
            (
                f"Typed relationship graph is {availability} ({reason}); "
                "requested relationship refinements could not be evaluated "
                "and no candidates were dropped."
            )
        ]

    def test_default_page_selection_never_traverses_typed_graph(self):
        page, concept = _knowledge_page_fixture(
            "entities/User.md",
            freshness="current",
        )
        service = _TypedGraphQueryStub(
            {page["canonical_path"]: concept},
            {page["mcp_uri"]: (5, 2)},
        )

        selected, counts = context_cmd._select_knowledge_page_refs(
            [page],
            {},
            service,
            limit=20,
            observed=[],
        )

        assert counts["filtered_total"] == 1
        assert "typed_graph" not in selected[0]
        assert service.traversals == []


def test_committed_surface_mapping_preserves_collision_page_symbol_lookup():
    live_surface = {
        "pages": [
            {
                "kind": "modules",
                "id": "web_client",
                "title": "web/client",
                "canonical_path": "modules/web_client.md",
                "source_path": None,
                "role": "semantic",
                "mcp_uri": "llm-wiki://modules/web_client",
            },
            {
                "kind": "modules",
                "id": "admin_client",
                "title": "admin/client",
                "canonical_path": "modules/admin_client.md",
                "source_path": None,
                "role": "semantic",
                "mcp_uri": "llm-wiki://modules/admin_client",
            },
        ]
    }
    committed_surface = {
        "pages": [
            {
                "canonical_path": "modules/web_client.md",
                "source_path": "web/client.ts",
            },
            {
                "canonical_path": "modules/admin_client.md",
                "source_path": "admin/client.ts",
            },
        ]
    }
    query_surface = context_cmd._context_query_surface(
        live_surface,
        types.SimpleNamespace(surface=committed_surface),
    )
    inventory = {
        path: {
            "language": "typescript",
            "module": path.removesuffix(".ts").replace("/", "."),
            "classes": [],
            "functions": [{"name": "run", "line": 1, "params": []}],
        }
        for path in ("web/client.ts", "admin/client.ts")
    }
    service = context_cmd.DocumentationGraphQueryService(
        inventory,
        surface_index=query_surface,
    )

    result = context_cmd._symbol_pages_payload(
        service,
        query_surface,
        "web/client.ts:run",
        {},
        observed=[],
    )

    assert result["found"] is True
    assert [page["canonical_path"] for page in result["pages"]] == [
        "modules/web_client.md"
    ]
    assert result["pages"][0]["source_path"] == "web/client.ts"
    assert result["bounds"]["pages"] == {
        "total": 1,
        "returned": 1,
        "truncated": False,
    }


def test_knowledge_enrichment_reuses_one_live_inventory_and_read_view(
    tmp_path,
    monkeypatch,
):
    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(fixture, tmp_path / "checkout")
    commit_knowledge_artifacts(
        _knowledge_commit_plan(tree["wiki_root"], fixture)
    )
    monkeypatch.chdir(tree["root"])

    calls = {
        "inventory": 0,
        "surface": 0,
        "load": 0,
        "live": 0,
        "query_service": 0,
    }
    real_inventory = context_cmd.get_inventory_result
    real_surface = context_cmd.evaluate_surface_index
    real_load = context_cmd.load_knowledge_state
    real_live = context_cmd.build_runtime_live_evaluation
    real_query_service = context_cmd.DocumentationGraphQueryService

    def counted_inventory(*args, **kwargs):
        calls["inventory"] += 1
        return real_inventory(*args, **kwargs)

    def counted_surface(*args, **kwargs):
        calls["surface"] += 1
        return real_surface(*args, **kwargs)

    def counted_load(*args, **kwargs):
        calls["load"] += 1
        return real_load(*args, **kwargs)

    def counted_live(inputs):
        calls["live"] += 1
        assert set(inputs.inventory) == set(fixture.inventory)
        assert [
            item["name"]
            for item in inputs.inventory["src/accounts.py"]["classes"]
        ] == ["User", "AccountService"]
        return real_live(inputs)

    def counted_query_service(*args, **kwargs):
        calls["query_service"] += 1
        return real_query_service(*args, **kwargs)

    monkeypatch.setattr(context_cmd, "get_inventory_result", counted_inventory)
    monkeypatch.setattr(context_cmd, "evaluate_surface_index", counted_surface)
    monkeypatch.setattr(context_cmd, "load_knowledge_state", counted_load)
    monkeypatch.setattr(
        context_cmd,
        "build_runtime_live_evaluation",
        counted_live,
    )
    monkeypatch.setattr(
        context_cmd,
        "DocumentationGraphQueryService",
        counted_query_service,
    )

    payload, warnings = context_cmd._build_context(
        ".",
        32_000,
        "json",
        ["all"],
        {"surface": "entities", "symbol": "User"},
        emit_warnings=False,
        wiki_dir="docs/llm_wiki",
    )

    assert calls == {
        "inventory": 1,
        "surface": 1,
        "load": 1,
        "live": 1,
        "query_service": 1,
    }
    assert payload["knowledge"] == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness": "evaluated (6 concepts)",
        "freshness_evaluated": True,
    }
    assert payload["surface"]["knowledge_selection"] == {
        "unfiltered_total": 2,
        "filtered_total": 2,
        "returned": 2,
        "truncated": False,
    }
    summaries = [page["knowledge"] for page in payload["surface"]["pages"]]
    assert all(
        set(summary)
        == {
            "availability",
            "reason",
            "freshness_disclosure",
            "freshness_evaluated",
            "origin",
            "evidence",
            "verification",
            "freshness",
            "lifecycle",
        }
        for summary in summaries
    )
    assert all(
        set(summary["freshness"])
        == {"state", "reason", "live_comparison_performed"}
        for summary in summaries
    )
    assert {
        summary["freshness"]["state"] for summary in summaries
    } == {"current"}
    assert not any("retained by default" in warning for warning in warnings)


@pytest.mark.parametrize(
    ("live_policy", "freshness_evaluated", "state", "reason"),
    [
        (
            "mismatch",
            True,
            "basis-incompatible",
            "generation-options-changed",
        ),
        ("invalid", False, None, "not-evaluated"),
    ],
)
def test_context_generation_option_evaluation_fails_closed(
    tmp_path,
    monkeypatch,
    live_policy,
    freshness_evaluated,
    state,
    reason,
):
    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(fixture, tmp_path / "checkout")
    commit_knowledge_artifacts(
        _knowledge_commit_plan(tree["wiki_root"], fixture)
    )
    monkeypatch.chdir(tree["root"])
    real_options = context_cmd.runtime_generation_options

    if live_policy == "mismatch":

        def evaluated_options(**kwargs):
            options = real_options(**kwargs)
            options["preserve_semantic"] = False
            return options

    else:

        def evaluated_options(**_kwargs):
            raise ValueError("invalid runtime generation policy")

    monkeypatch.setattr(
        context_cmd,
        "runtime_generation_options",
        evaluated_options,
    )

    payload, _warnings = context_cmd._build_context(
        ".",
        32_000,
        "json",
        ["all"],
        {"surface": "entities"},
        emit_warnings=False,
        wiki_dir="docs/llm_wiki",
    )

    assert payload["knowledge"] == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness": (
            "evaluated (6 concepts)"
            if freshness_evaluated
            else "unevaluated (snapshot-only read)"
        ),
        "freshness_evaluated": freshness_evaluated,
    }
    freshness = [
        page["knowledge"]["freshness"] for page in payload["surface"]["pages"]
    ]
    assert {item["state"] for item in freshness} == {state}
    assert {item["reason"] for item in freshness} == {reason}
    assert {item["live_comparison_performed"] for item in freshness} == {
        freshness_evaluated
    }
    if live_policy == "mismatch":
        assert {item["hint"] for item in freshness} == {
            BASIS_INCOMPATIBLE_HINTS[reason]
        }
    else:
        assert all("hint" not in item for item in freshness)


class TestProtocolRun:
    def test_packet_format_emits_exact_canonical_bytes(
        self,
        monkeypatch,
        capsys,
    ):
        from llm_wiki_cli.services import context_packet

        canonical = b'{"packet_id":"sha256:' + b"a" * 64 + b'"}\n'
        seen = {}

        class Packet:
            @staticmethod
            def to_bytes():
                return canonical

        def fake_builder(src_dir, wiki_dir, request, **kwargs):
            seen.update(
                {
                    "src_dir": src_dir,
                    "wiki_dir": wiki_dir,
                    "request": request,
                    **kwargs,
                }
            )
            return Packet()

        monkeypatch.setattr(
            context_packet,
            "build_qualified_context",
            fake_builder,
        )

        context_cmd.run(
            _make_args(
                format="packet",
                budget=2048,
                focus="all",
                wiki_dir="agent_wiki",
                prefer_fresh=True,
                read_only=False,
                allow_external_src=False,
            )
        )

        assert capsys.readouterr().out.encode("utf-8") == canonical
        assert seen["src_dir"] == "."
        assert seen["wiki_dir"] == "agent_wiki"
        assert seen["request"] == {
            "protocol": "llm-wiki-context/v1",
            "budget_tokens": 2048,
            "focus": ["all"],
            "format": "json",
            "filters": {},
            "prefer_fresh": True,
        }
        assert seen["read_only"] is True
        assert seen["allow_external_src"] is False

    def test_request_file_json_envelope(self, tmp_project, tmp_path, capsys):
        request = _write_request(tmp_path, _protocol_request(budget_tokens=100000))
        context_cmd.run(_make_args(request=request, budget=None))

        data = json.loads(capsys.readouterr().out)
        assert data["protocol"] == context_cmd.PROTOCOL_VERSION
        assert data["ok"] is True
        assert data["budget_tokens"] == 100000
        assert data["format"] == "json"
        assert data["focus"] == ["all"]
        assert "used_tokens" in data
        assert "files" in data
        assert "content" not in data
        assert "graphs" not in data
        assert "surface" not in data
        assert data["files"]

    def test_request_discloses_opt_in_freshness_ranking(
        self,
        tmp_project,
        tmp_path,
        capsys,
    ):
        _write_query_project(tmp_project)
        _write_query_wiki(tmp_project, "agent_wiki")
        request = _write_request(
            tmp_path,
            _protocol_request(
                budget_tokens=100000,
                prefer_fresh=True,
            ),
        )

        context_cmd.run(
            _make_args(
                request=request,
                budget=None,
                wiki_dir="agent_wiki",
            )
        )

        data = json.loads(capsys.readouterr().out)
        assert data["prefer_fresh"] is True
        assert data["ranking_policy"] == {
            "name": "relevance-then-current-freshness",
            "prefer_fresh": True,
            "scope": "within-relevance-tiers",
            "freshness_evaluated": False,
            "budget_pressure": False,
            "applied": False,
            "filters_stale_content": False,
        }
        assert data["knowledge"]["freshness_evaluated"] is False

    def test_managed_public_context_prefers_current_source_under_pressure(
        self,
        tmp_path,
        monkeypatch,
    ):
        from llm_wiki_cli.api import build_context

        root = _materialize_managed_freshness_ranking_project(tmp_path)
        monkeypatch.chdir(root)
        inventory = context_cmd.get_inventory(".", deep=True)
        fresh_path = "src/z_fresh.py"
        stale_path = "src/a_stale.py"
        budget = context_cmd._entry_tokens(
            fresh_path,
            context_cmd._build_entry(
                inventory[fresh_path],
                "high",
                "slim",
            ),
        )
        options = {
            "budget": budget,
            "focus": "all",
            "filters": {"surface": "modules"},
            "wiki_dir": "docs/llm_wiki",
        }

        baseline = build_context(".", **options)
        preferred = build_context(".", prefer_fresh=True, **options)

        assert list(baseline["files"]) == [stale_path]
        assert baseline["downgraded_files"] == {
            stale_path: "summary",
        }
        assert baseline["omitted_files"] == [fresh_path]
        assert "ranking_policy" not in baseline
        assert list(preferred["files"]) == [fresh_path]
        assert preferred["omitted_files"] == [stale_path]
        assert preferred["downgraded_files"] == {
            fresh_path: "slim",
        }
        assert preferred["files"][fresh_path]["priority"] == "high"
        assert preferred["truncated"] is True
        assert preferred["ranking_policy"] == {
            "name": "relevance-then-current-freshness",
            "prefer_fresh": True,
            "scope": "within-relevance-tiers",
            "freshness_evaluated": True,
            "budget_pressure": True,
            "applied": True,
            "filters_stale_content": False,
        }
        states = {
            page["source_path"]: page["knowledge"]["freshness"]["state"]
            for page in preferred["surface"]["pages"]
        }
        assert states == {
            fresh_path: "current",
            stale_path: "source-changed",
        }

    def test_success_envelope_keeps_old_json_shape_when_enriched(
        self, tmp_project, tmp_path, capsys
    ):
        _write_query_project(tmp_project)
        _write_query_wiki(tmp_project, "agent_wiki")
        request = _write_request(
            tmp_path,
            _protocol_request(
                budget_tokens=100000,
                filters={
                    "symbol": "run",
                    "entrypoint": "api-run",
                    "surface": "flows",
                },
            ),
        )

        context_cmd.run(_make_args(request=request, budget=None, wiki_dir="agent_wiki"))

        data = json.loads(capsys.readouterr().out)
        assert {
            "protocol",
            "ok",
            "budget_tokens",
            "used_tokens",
            "format",
            "focus",
            "filters",
            "files",
        } <= set(data)
        assert data["protocol"] == "llm-wiki-context/v1"
        assert data["ok"] is True
        assert data["graphs"]["symbol"]["callees"]["found"] is True
        assert data["surface"]["kind"] == "flows"

    def test_request_stdin(self, tmp_project, monkeypatch, capsys):
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps(_protocol_request(budget_tokens=100000))),
        )
        context_cmd.run(_make_args(request="-", budget=None))

        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is True
        assert data["files"]

    def test_request_markdown_envelope(self, tmp_project, tmp_path, capsys):
        request = _write_request(
            tmp_path,
            _protocol_request(budget_tokens=100000, format="markdown"),
        )
        context_cmd.run(_make_args(request=request, budget=None))

        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is True
        assert data["format"] == "markdown"
        assert "content" in data
        assert "files" not in data
        assert "Context Budget" in data["content"]

    def test_request_empty_inventory_reports_zero_file_bounds(
        self, tmp_path, capsys, monkeypatch
    ):
        monkeypatch.setattr(context_cmd, "get_inventory", lambda *args, **kwargs: {})
        request = _write_request(tmp_path, _protocol_request())

        context_cmd.run(_make_args(request=request, budget=None))

        data = json.loads(capsys.readouterr().out)
        assert data["files"] == {}
        assert data["bounds"]["files"] == {
            "total": 0,
            "returned": 0,
            "truncated": False,
        }
        assert data["truncated"] is False
        assert data["omitted_files"] == []
        assert data["downgraded_files"] == {}

    def test_request_language_filter_excludes_nonmatching_inventory(
        self, tmp_path, capsys, monkeypatch
    ):
        inventory = {
            "api.py": {
                "language": "python",
                "classes": [{"name": "Api"}],
                "functions": [],
            },
            "web.ts": {
                "language": "typescript",
                "classes": [{"name": "Web"}],
                "functions": [],
            },
        }
        monkeypatch.setattr(
            context_cmd, "get_inventory", lambda *args, **kwargs: inventory
        )
        request = _write_request(
            tmp_path,
            _protocol_request(filters={"language": "python"}),
        )

        context_cmd.run(_make_args(request=request, budget=None))

        data = json.loads(capsys.readouterr().out)
        assert set(data["files"]) == {"api.py"}

    def test_request_module_filter_matches_path_and_module(
        self, tmp_path, capsys, monkeypatch
    ):
        inventory = {
            "src/api/users.py": {
                "language": "python",
                "classes": [{"name": "User"}],
                "functions": [],
            },
            "web/api/client.ts": {
                "language": "typescript",
                "classes": [{"name": "Client"}],
                "functions": [],
            },
            "src/db/models.py": {
                "language": "python",
                "classes": [{"name": "Model"}],
                "functions": [],
            },
        }
        monkeypatch.setattr(
            context_cmd, "get_inventory", lambda *args, **kwargs: inventory
        )

        request = _write_request(
            tmp_path, _protocol_request(filters={"module": "api/*"})
        )
        context_cmd.run(_make_args(request=request, budget=None))
        data = json.loads(capsys.readouterr().out)
        assert set(data["files"]) == {"src/api/users.py"}

        request = _write_request(
            tmp_path, _protocol_request(filters={"module": "web/api/*"})
        )
        context_cmd.run(_make_args(request=request, budget=None))
        data = json.loads(capsys.readouterr().out)
        assert set(data["files"]) == {"web/api/client.ts"}

    def test_request_graph_and_surface_filters_add_sections(
        self, tmp_project, tmp_path, capsys
    ):
        _write_query_project(tmp_project)
        _write_query_wiki(tmp_project, "agent_wiki")
        request = _write_request(
            tmp_path,
            _protocol_request(
                budget_tokens=100000,
                filters={
                    "symbol": "run",
                    "entrypoint": "api-run",
                    "surface": "flows",
                },
            ),
        )

        context_cmd.run(_make_args(request=request, budget=None, wiki_dir="agent_wiki"))

        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is True
        assert "files" in data
        assert data["bounds"]["files"] == {
            "total": 5,
            "returned": 5,
            "truncated": False,
        }
        assert data["truncated"] is False
        assert data["omitted_files"] == []
        assert data["downgraded_files"] == {}
        assert data["graphs"]["symbol"]["callees"]["found"] is True
        assert data["graphs"]["symbol"]["pages"]["pages"]
        assert data["graphs"]["entrypoint"]["flow"]["found"] is True
        assert data["graphs"]["entrypoint"]["data_flow"]["found"] is True
        assert data["surface"]["kind"] == "flows"
        assert data["surface"]["returned"] == 1
        assert data["surface"]["count"] == data["surface"]["returned"]
        assert data["surface"]["bounds"]["pages"] == {
            "total": 1,
            "returned": 1,
            "truncated": False,
        }
        assert [page["canonical_path"] for page in data["surface"]["pages"]] == [
            "flows/api-run.md"
        ]

    def test_graph_and_surface_filters_do_not_compete_with_file_budget(
        self, tmp_project, tmp_path, capsys
    ):
        _write_query_project(tmp_project)
        _write_query_wiki(tmp_project, "agent_wiki")
        request = _write_request(
            tmp_path,
            _protocol_request(
                budget_tokens=1,
                filters={
                    "symbol": "run",
                    "entrypoint": "api-run",
                    "surface": "flows",
                },
            ),
        )

        context_cmd.run(_make_args(request=request, budget=None, wiki_dir="agent_wiki"))

        data = json.loads(capsys.readouterr().out)
        assert data["used_tokens"] == 0
        assert data["files"] == {}
        assert data["bounds"]["files"]["total"] == 5
        assert data["bounds"]["files"]["returned"] == 0
        assert data["bounds"]["files"]["truncated"] is True
        assert data["truncated"] is True
        assert data["omitted_files"]
        assert data["graphs"]["symbol"]["callees"]["found"] is True
        assert data["graphs"]["entrypoint"]["flow"]["found"] is True
        assert data["surface"]["pages"]

    def test_unknown_graph_filters_return_structured_empty_results(
        self, tmp_project, tmp_path, capsys
    ):
        _write_query_project(tmp_project)
        _write_query_wiki(tmp_project, "agent_wiki")
        request = _write_request(
            tmp_path,
            _protocol_request(
                budget_tokens=100000,
                filters={"symbol": "missing", "entrypoint": "missing"},
            ),
        )

        context_cmd.run(_make_args(request=request, budget=None, wiki_dir="agent_wiki"))

        data = json.loads(capsys.readouterr().out)
        assert data["graphs"]["symbol"]["callers"]["found"] is False
        assert data["graphs"]["symbol"]["callees"]["found"] is False
        assert data["graphs"]["symbol"]["pages"]["pages"] == []
        assert data["graphs"]["entrypoint"]["flow"]["flow"] is None
        assert data["graphs"]["entrypoint"]["data_flow"]["data_flow"] is None

    def test_request_markdown_includes_graph_and_surface_sections(
        self, tmp_project, tmp_path, capsys
    ):
        _write_query_project(tmp_project)
        _write_query_wiki(tmp_project, "agent_wiki")
        request = _write_request(
            tmp_path,
            _protocol_request(
                budget_tokens=100000,
                format="markdown",
                filters={
                    "symbol": "run",
                    "entrypoint": "api-run",
                    "surface": "flows",
                },
            ),
        )

        context_cmd.run(_make_args(request=request, budget=None, wiki_dir="agent_wiki"))

        data = json.loads(capsys.readouterr().out)
        assert "Documentation Graphs" in data["content"]
        assert data["bounds"]["files"] == {
            "total": 5,
            "returned": 5,
            "truncated": False,
        }
        assert data["truncated"] is False
        assert data["omitted_files"] == []
        assert data["downgraded_files"] == {}
        assert "Symbol `run`" in data["content"]
        assert "Entry point `api-run`" in data["content"]
        assert "Surface `flows`" in data["content"]

    @pytest.mark.parametrize(
        ("request_data", "field"),
        [
            ({"protocol": "bad", "budget_tokens": 1000}, "protocol"),
            ({"protocol": context_cmd.PROTOCOL_VERSION}, "budget_tokens"),
            (_protocol_request(focus=["neighbors"]), "focus"),
            (_protocol_request(extra=True), "extra"),
            (_protocol_request(filters={"package": "api"}), "filters.package"),
            (_protocol_request(filters={"symbol": ""}), "filters.symbol"),
            (_protocol_request(filters={"entrypoint": ""}), "filters.entrypoint"),
            (_protocol_request(filters={"surface": "bad"}), "filters.surface"),
        ],
    )
    def test_invalid_requests_return_error_envelope(
        self, tmp_path, capsys, request_data, field
    ):
        request = _write_request(tmp_path, request_data)
        with pytest.raises(SystemExit) as exc_info:
            context_cmd.run(_make_args(request=request, budget=None))

        assert exc_info.value.code == 1
        data = json.loads(capsys.readouterr().out)
        assert data["protocol"] == context_cmd.PROTOCOL_VERSION
        assert data["ok"] is False
        assert data["error"]["code"] == "invalid_request"
        assert data["error"]["field"] == field
        assert isinstance(data["error"]["message"], str)

    def test_invalid_json_returns_error_envelope(self, tmp_path, capsys):
        request = tmp_path / "bad-request.json"
        request.write_text("{bad json", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            context_cmd.run(_make_args(request=str(request), budget=None))

        assert exc_info.value.code == 1
        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is False
        assert data["error"]["field"] == "request"

    def test_extractor_failure_returns_error_envelope(
        self, tmp_path, monkeypatch, capsys
    ):
        result = InventoryResult(
            {},
            {"python": ExtractorStatus("python", "failed", 1, "boom")},
        )
        monkeypatch.setattr(
            context_cmd, "get_inventory_result", lambda *args, **kwargs: result
        )
        request = _write_request(tmp_path, _protocol_request())

        with pytest.raises(SystemExit) as exc_info:
            context_cmd.run(_make_args(request=request, budget=None))

        assert exc_info.value.code == 1
        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is False
        assert data["error"]["field"] == "src_dir"
        assert "python extraction failed: boom" in data["error"]["message"]


# ── Integration ───────────────────────────────────────────────────────


class TestContextRun:
    def test_focus_all_json(self, tmp_project, capsys):
        args = _make_args(focus="all", budget=100000)
        context_cmd.run(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "budget" in data
        assert "used" in data
        assert "files" in data
        # tmp_project has models.py, main.py, utils.py — at least some should appear
        assert len(data["files"]) > 0
        # All should be high priority
        for entry in data["files"].values():
            assert entry["priority"] == "high"

    def test_focus_all_markdown(self, tmp_project, capsys):
        args = _make_args(focus="all", budget=100000, format="markdown")
        context_cmd.run(args)
        captured = capsys.readouterr()
        assert "Changed Files (High Priority)" in captured.out
        assert "tokens" in captured.out

    def test_tight_budget_drops_files(self, tmp_project, capsys):
        args = _make_args(focus="all", budget=50)
        context_cmd.run(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["budget"] == 50
        assert data["used"] <= 50
        assert data["truncated"] is True
        assert data["omitted_files"] or data["downgraded_files"]

    def test_json_output_file_suppresses_stdout(self, tmp_project, tmp_path, capsys):
        out_path = tmp_path / "context.json"
        args = _make_args(
            focus="all", budget=100000, output=str(out_path), read_only=True
        )

        context_cmd.run(args)

        captured = capsys.readouterr()
        assert captured.out == ""
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert data["files"]

    def test_markdown_output_file_suppresses_stdout(
        self, tmp_project, tmp_path, capsys
    ):
        out_path = tmp_path / "context.md"
        args = _make_args(
            focus="all", budget=100000, format="markdown", output=str(out_path)
        )

        context_cmd.run(args)

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Context Budget" in out_path.read_text(encoding="utf-8")

    def test_run_allows_external_src_with_explicit_flag(
        self, tmp_project, tmp_path, capsys
    ):
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "external.py").write_text("class External: pass\n", encoding="utf-8")
        args = _make_args(
            src_dir=str(outside),
            focus="all",
            budget=100000,
            allow_external_src=True,
        )

        context_cmd.run(args)

        data = json.loads(capsys.readouterr().out)
        assert set(data["files"]) == {"external.py"}

    def test_read_only_context_does_not_create_wiki_artifacts(
        self, tmp_project, capsys
    ):
        context_cmd.run(_make_args(focus="all", budget=100000, read_only=True))

        assert not Path("docs").exists()

    def test_changed_focus_warning_goes_to_stderr_json_stays_parseable(
        self, tmp_project, capsys
    ):
        args = _make_args(focus="changed", budget=100000)
        context_cmd.run(args)
        captured = capsys.readouterr()

        data = json.loads(captured.out)
        assert "files" in data
        assert "Extractor plan: requested=1 resolved=1" in captured.err
        assert captured.err.count("Extractor plan:") == 1
        assert "Warning:" in captured.err
        assert "Warning:" not in captured.out

    def test_extractor_plan_is_reported_once_before_context_inventory_work(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        events = []
        real_reporter = context_cmd.print_extraction_job_plan

        def recording_reporter(plan):
            events.append("report")
            real_reporter(plan)

        def fake_inventory(*args, **kwargs):
            kwargs["plan_reporter"](ExtractionJobPlan())
            events.append("work")
            return InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
            )

        monkeypatch.setattr(
            context_cmd, "print_extraction_job_plan", recording_reporter
        )
        monkeypatch.setattr(context_cmd, "get_inventory_result", fake_inventory)

        context_cmd.run(_make_args(focus="all", budget=1000))

        captured = capsys.readouterr()
        assert captured.out.strip() == "{}"
        assert captured.err.count("Extractor plan:") == 1
        assert events == ["report", "work"]

    def test_empty_directory(self, tmp_path, capsys, monkeypatch):
        monkeypatch.chdir(tmp_path)
        args = _make_args(focus="all", budget=1000)
        context_cmd.run(args)
        captured = capsys.readouterr()
        assert captured.out.strip() == "{}"

    def test_budget_required_without_request(self, tmp_project, capsys):
        with pytest.raises(SystemExit) as exc_info:
            context_cmd.run(_make_args(budget=None))

        assert exc_info.value.code == 2
        assert "--budget is required" in capsys.readouterr().err

    def test_extractor_failure_exits_at_cli_boundary(
        self, tmp_project, monkeypatch, capsys
    ):
        result = InventoryResult(
            {},
            {"python": ExtractorStatus("python", "failed", 1, "boom")},
        )
        monkeypatch.setattr(
            context_cmd, "get_inventory_result", lambda *args, **kwargs: result
        )

        with pytest.raises(SystemExit) as exc_info:
            context_cmd.run(_make_args(focus="all", budget=1000))

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Error: python extraction failed: boom" in captured.err

    @pytest.mark.parametrize("value", ["0", "-1"])
    def test_cli_rejects_non_positive_budget(self, tmp_project, monkeypatch, value):
        from llm_wiki_cli import cli

        monkeypatch.setattr(sys, "argv", ["llm-wiki", "context", "--budget", value])
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 2


class TestBuildProtocolEnrichmentRootPropagation:
    def test_propagates_src_root_to_get_entry_points(self, tmp_path, monkeypatch):
        """Regression (2026-07-04): ``_build_protocol_enrichment`` must pass
        ``root=src_root``/``fallback_root=Path.cwd()`` to ``get_entry_points``.
        Dropping those kwargs (as this call site once did) makes the Go/
        Haskell web-server detectors silently miss entry points whenever
        ``llm-wiki context`` runs with an external ``--src-dir`` from a
        different cwd — proven end-to-end for the sibling lint check in
        ``TestLintFlowCoverage::test_go_http_entrypoint_not_stale_for_external_src_dir``
        in test_lint.py. This test pins the wiring at the call site directly.
        """
        monkeypatch.chdir(tmp_path)
        (tmp_path / "wiki").mkdir()

        calls = []
        real_get_entry_points = context_cmd.get_entry_points

        def spy(inventory, **kwargs):
            calls.append(kwargs)
            return real_get_entry_points(inventory, **kwargs)

        monkeypatch.setattr(context_cmd, "get_entry_points", spy)

        src_root = Path("/some/external/src")
        context_cmd._build_protocol_enrichment(
            {}, {"surface": True}, src_root=src_root, wiki_dir="wiki"
        )

        assert len(calls) == 1
        assert calls[0]["root"] == src_root
        assert calls[0]["fallback_root"] == Path.cwd()
