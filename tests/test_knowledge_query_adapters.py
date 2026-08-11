from __future__ import annotations

import json
import os
from pathlib import Path
from time import perf_counter, perf_counter_ns
import tracemalloc
from types import SimpleNamespace

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import (
    context_packet,
    context_service,
    documentation_query_builder,
    knowledge_consumption,
)
from llm_wiki_cli.services import mcp_server


class _SnapshotService:
    knowledge_status = {
        "availability": "ready",
        "reason": "knowledge-ready",
        "freshness": "snapshot-only",
        "freshness_evaluated": False,
    }
    pages: list[dict] = []

    @staticmethod
    def _base(value):
        return {
            "query": value,
            "found": True,
            "ambiguous": False,
            "matches": [{"value": value}],
            "bounds": {"matches": {"total": 1, "returned": 1, "truncated": False}},
            "truncated": False,
        }

    def get_concept(self, value):
        concept = {"locator": value}
        return {
            **self._base(value),
            "matches": [concept],
            "knowledge": dict(self.knowledge_status),
            "concept": concept,
        }

    def related_concepts(self, value, **kwargs):
        del kwargs
        return {
            **self._base(value),
            "knowledge": dict(self.knowledge_status),
            "relationships": [],
            "related_concepts": [],
        }

    def traverse_typed_graph(self, value, **kwargs):
        del kwargs
        return {
            **self._base(value),
            "knowledge": dict(self.knowledge_status),
            "edges": [],
        }

    def pages_for_symbol(self, value):
        return {
            **self._base(value),
            "symbol": {"name": value},
            "pages": [],
            "bounds": {
                **self._base(value)["bounds"],
                "pages": {"total": 0, "returned": 0, "truncated": False},
            },
        }

    def callers(self, value):
        return {
            **self._base(value),
            "callers": [],
            "bounds": {
                **self._base(value)["bounds"],
                "callers": {"total": 0, "returned": 0, "truncated": False},
            },
        }

    def callees(self, value):
        return {
            **self._base(value),
            "callees": [],
            "bounds": {
                **self._base(value)["bounds"],
                "callees": {"total": 0, "returned": 0, "truncated": False},
            },
        }

    def flow_for_entrypoint(self, value):
        return {**self._base(value), "flow": None}

    def data_flow_for_entrypoint(self, value):
        return {**self._base(value), "data_flow": None}

    def dependency_neighborhood(self, value):
        return {**self._base(value), "path": value}


class _ImpactService(_SnapshotService):
    def __init__(self, path: str):
        self.inventory = {
            path: {
                "language": "python",
                "classes": [],
                "functions": [{"name": "run"}],
                "imports": [],
            }
        }
        self.concepts_by_source_path = {}
        self.relationships_by_source_path = {}
        self._knowledge_relationship_order = ()
        self.pages = []


def test_snapshot_dispatch_is_executable_without_source_extraction(monkeypatch):
    monkeypatch.setattr(
        api,
        "_snapshot_query_service",
        lambda wiki_dir, *, limit: _SnapshotService(),
    )
    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        lambda *args, **kwargs: pytest.fail("narrow query extracted source"),
    )

    result = api.query_documentation(
        {"operation": "concept", "value": "llm-wiki://entities/User"}
    )

    assert result.get("concept") == {"locator": "llm-wiki://entities/User"}
    assert result["cost"] == {
        "scope": "snapshot-index-only",
        "full_inventory_performed": False,
        "supplied_paths": 0,
    }


@pytest.mark.parametrize(
    "query_request",
    [
        {"operation": "concept", "value": "llm-wiki://entities/User"},
        {"operation": "related", "value": "llm-wiki://entities/User"},
        {"operation": "surface", "value": "api-contracts.md"},
        {"operation": "typed", "value": "llm-wiki://entities/User"},
        {"operation": "symbol", "value": "run", "allow_full_inventory": True},
        {
            "operation": "entrypoint",
            "value": "cli",
            "allow_full_inventory": True,
        },
        {
            "operation": "dependency",
            "value": "app.py",
            "allow_full_inventory": True,
        },
        {"operation": "impact", "paths": ["app.py"]},
    ],
    ids=lambda query_request: query_request["operation"],
)
def test_every_documentation_query_operation_has_the_common_envelope(
    query_request,
    tmp_path,
    monkeypatch,
):
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "app.py").write_text("value = 1\n", encoding="utf-8")
    service = _ImpactService("app.py")
    service.pages = [
        {
            "canonical_path": "api-contracts.md",
            "mcp_uri": "llm-wiki://api-contracts",
        }
    ]
    monkeypatch.setattr(
        api,
        "_snapshot_query_service",
        lambda wiki_dir, *, limit: service,
    )
    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        lambda *args, **kwargs: service,
    )
    monkeypatch.setattr(
        api,
        "build_live_documentation_query_service",
        lambda **kwargs: service,
    )
    monkeypatch.setattr(api, "_validate_wiki_dir", lambda value: Path(value))

    result = api.query_documentation(
        query_request,
        src_dir=source_root.as_posix(),
        wiki_dir=(tmp_path / "wiki").as_posix(),
        allow_external_src=True,
    )

    required = {
        "schema_version",
        "operation",
        "query",
        "found",
        "ambiguous",
        "matches",
        "bounds",
        "truncated",
        "cost",
    }
    assert required.issubset(result)
    assert result["schema_version"] == api.DOCUMENTATION_QUERY_SCHEMA_VERSION
    assert result["operation"] == query_request["operation"]
    assert isinstance(result["matches"], list)
    assert isinstance(result["bounds"], dict)
    assert isinstance(result["truncated"], bool)


def test_full_inventory_requires_explicit_cost_authorization(monkeypatch):
    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        lambda *args, **kwargs: pytest.fail("query extracted before authorization"),
    )

    with pytest.raises(api.InvalidRequestError) as exc_info:
        api.query_documentation({"operation": "symbol", "value": "run"})

    assert exc_info.value.code == "full-inventory-required"
    assert exc_info.value.details == {"field": "allow_full_inventory"}


@pytest.mark.parametrize(
    ("query_request", "field"),
    [
        ({"operation": "impact", "paths": "app.py"}, "paths"),
        ({"operation": "impact", "paths": [1]}, "paths"),
        ({"operation": "impact", "diff": 1}, "diff"),
    ],
)
def test_impact_input_errors_have_equivalent_api_and_mcp_structure(
    query_request,
    field,
):
    with pytest.raises(api.InvalidRequestError) as python_error:
        api.query_documentation(query_request)
    with pytest.raises(mcp_server.McpWikiError) as mcp_error:
        mcp_server.McpWikiService().query_documentation(query_request)

    assert python_error.value.code == "invalid-request"
    assert python_error.value.details == {"field": field}
    assert mcp_error.value.code == python_error.value.code
    assert mcp_error.value.data == python_error.value.details


@pytest.mark.parametrize("operation", ["symbol", "entrypoint"])
def test_combined_full_inventory_matches_obey_caller_limit(
    monkeypatch,
    operation,
):
    def result(value, marker, **extra):
        return {
            "query": value,
            "found": True,
            "ambiguous": False,
            "matches": [{"marker": marker}],
            "bounds": {"matches": {"total": 1, "returned": 1, "truncated": False}},
            "truncated": False,
            **extra,
        }

    class FullInventoryService:
        def pages_for_symbol(self, value):
            payload = result(value, "pages", symbol={"name": value}, pages=[])
            payload["bounds"]["pages"] = {
                "total": 0,
                "returned": 0,
                "truncated": False,
            }
            return payload

        def callers(self, value):
            payload = result(value, "callers", callers=[])
            payload["bounds"]["callers"] = {
                "total": 0,
                "returned": 0,
                "truncated": False,
            }
            return payload

        def callees(self, value):
            payload = result(value, "callees", callees=[])
            payload["bounds"]["callees"] = {
                "total": 0,
                "returned": 0,
                "truncated": False,
            }
            return payload

        def flow_for_entrypoint(self, value):
            return result(value, "flow", flow={"steps": []})

        def data_flow_for_entrypoint(self, value):
            return result(value, "data-flow", data_flow={"steps": []})

    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        lambda *args, **kwargs: FullInventoryService(),
    )

    response = api.query_documentation(
        {
            "operation": operation,
            "value": "run",
            "limit": 1,
            "allow_full_inventory": True,
        }
    )

    expected_total = 3 if operation == "symbol" else 2
    assert len(response["matches"]) == 1
    assert response["bounds"]["matches"] == {
        "total": expected_total,
        "returned": 1,
        "truncated": True,
    }
    assert response["truncated"] is True


def test_invalid_exact_coordinate_is_rejected_before_snapshot_load(monkeypatch):
    monkeypatch.setattr(
        api,
        "_snapshot_query_service",
        lambda *args, **kwargs: pytest.fail("invalid query loaded the snapshot"),
    )

    with pytest.raises(api.InvalidRequestError):
        api.query_documentation({"operation": "concept", "value": "User"})


def test_impact_uses_only_supplied_paths_and_inert_targeted_extraction(
    tmp_path,
    monkeypatch,
):
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    seen = {}

    def fake_live_builder(**kwargs):
        seen.update(kwargs)
        return _ImpactService("app.py")

    monkeypatch.setattr(
        api, "build_live_documentation_query_service", fake_live_builder
    )
    monkeypatch.setattr(api, "_validate_wiki_dir", lambda value: Path(value))

    result = api.query_documentation(
        {"operation": "impact", "paths": ["app.py"]},
        src_dir=source_root.as_posix(),
        wiki_dir=(tmp_path / "wiki").as_posix(),
        allow_external_src=True,
    )

    assert seen["paths"] == ("app.py",)
    assert seen["include_plugins"] is False
    assert seen["read_only"] is True
    assert result["matches"] == [
        {
            "path": "app.py",
            "present": True,
            "language": "python",
            "counts": {
                "classes": 0,
                "functions": 1,
                "imports": 0,
            },
        }
    ]
    assert result["cost"] == {
        "scope": "targeted-extraction",
        "full_inventory_performed": False,
        "supplied_paths": 1,
    }
    assert "raw_evidence" not in result
    assert "elapsed" not in result
    assert "memory" not in result


def test_impact_result_paths_obey_limit_without_truncating_input_echo_or_cost(
    tmp_path,
    monkeypatch,
):
    source_root = tmp_path / "source"
    source_root.mkdir()
    for path in ("a.py", "b.py"):
        (source_root / path).write_text("value = 1\n", encoding="utf-8")
    service = _ImpactService("a.py")
    service.inventory["b.py"] = dict(service.inventory["a.py"])
    monkeypatch.setattr(
        api,
        "build_live_documentation_query_service",
        lambda **kwargs: service,
    )
    monkeypatch.setattr(api, "_validate_wiki_dir", lambda value: Path(value))

    result = api.query_documentation(
        {
            "operation": "impact",
            "paths": ["b.py", "a.py"],
            "limit": 1,
        },
        src_dir=source_root.as_posix(),
        wiki_dir=(tmp_path / "wiki").as_posix(),
        allow_external_src=True,
    )

    assert result["query"]["paths"] == ["a.py", "b.py"]
    assert result["cost"]["supplied_paths"] == 2
    assert [match["path"] for match in result["matches"]] == ["a.py"]
    assert result["impacted_paths"] == ["a.py"]
    assert result["bounds"]["matches"] == {
        "total": 2,
        "returned": 1,
        "truncated": True,
    }
    assert result["bounds"]["paths"] == result["bounds"]["matches"]
    assert result["truncated"] is True


def test_supplied_path_normalization_consumes_at_most_limit_plus_one():
    pulled = 0

    def paths():
        nonlocal pulled
        while True:
            pulled += 1
            yield f"src/generated-{pulled}.py"

    with pytest.raises(
        documentation_query_builder.DocumentationQueryError,
        match=f"at most {documentation_query_builder.MAX_SUPPLIED_PATHS}",
    ):
        documentation_query_builder.normalize_supplied_paths(paths())

    assert pulled == documentation_query_builder.MAX_SUPPLIED_PATHS + 1


def test_supplied_path_normalization_maps_broken_iterator_to_stable_error():
    class BrokenPaths:
        def __iter__(self):
            return self

        def __next__(self):
            raise RuntimeError("iteration failed")

    with pytest.raises(
        documentation_query_builder.DocumentationQueryError,
        match="paths must be an array of source paths",
    ):
        documentation_query_builder.normalize_supplied_paths(BrokenPaths())


def test_final_documentation_query_envelope_caps_combined_component_bytes():
    result = api._with_query_envelope(
        "symbol",
        {
            "query": "run",
            "found": True,
            "ambiguous": False,
            "matches": [],
            "pages": [{"canonical_path": "modules/run.md", "title": "p" * 40_000}],
            "callers": [{"source_path": "src/caller.py", "label": "c" * 40_000}],
            "callees": [],
            "bounds": {
                "matches": {"total": 0, "returned": 0, "truncated": False},
                "pages": {"total": 1, "returned": 1, "truncated": False},
                "callers": {"total": 1, "returned": 1, "truncated": False},
                "callees": {"total": 0, "returned": 0, "truncated": False},
            },
            "truncated": False,
        },
        scope="snapshot-index-only",
    )
    encoded = json.dumps(
        result,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    assert len(encoded) <= 64 * 1024
    assert result["schema_version"] == api.DOCUMENTATION_QUERY_SCHEMA_VERSION
    assert result["operation"] == "symbol"
    assert result["cost"]["scope"] == "snapshot-index-only"
    assert result["pages"][0]["canonical_path"] == "modules/run.md"
    assert result["callers"][0]["source_path"] == "src/caller.py"
    assert result["bounds"]["result_bytes"]["returned"] == len(encoded)


def test_oversized_query_identity_is_rejected_before_full_inventory(monkeypatch):
    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        lambda *_args, **_kwargs: pytest.fail("oversized query reached extraction"),
    )

    with pytest.raises(api.InvalidRequestError, match="UTF-8 bytes") as caught:
        api.query_documentation(
            {
                "operation": "symbol",
                "value": "x" * 5000,
                "allow_full_inventory": True,
            }
        )

    assert caught.value.code == "invalid-request"
    assert caught.value.details == {"field": "value"}


def test_impact_rejects_a_symlink_escape_before_builder(
    tmp_path,
    monkeypatch,
):
    source_root = tmp_path / "source"
    source_root.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("secret = True\n", encoding="utf-8")
    os.symlink(outside, source_root / "escape.py")
    monkeypatch.setattr(
        api,
        "build_live_documentation_query_service",
        lambda **kwargs: pytest.fail("symlink reached targeted extraction"),
    )
    monkeypatch.setattr(api, "_validate_wiki_dir", lambda value: Path(value))

    with pytest.raises(api.PathPolicyError):
        api.query_documentation(
            {"operation": "impact", "paths": ["escape.py"]},
            src_dir=source_root.as_posix(),
            wiki_dir=(tmp_path / "wiki").as_posix(),
            allow_external_src=True,
        )


def test_raw_impact_evidence_has_an_independent_serialized_byte_cap(
    tmp_path,
    monkeypatch,
):
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "app.py").write_text("value = 1\n", encoding="utf-8")
    service = _ImpactService("app.py")
    service.inventory["app.py"]["diagnostic"] = "x" * (
        api.MAX_RAW_QUERY_EVIDENCE_BYTES * 2
    )
    monkeypatch.setattr(
        api,
        "build_live_documentation_query_service",
        lambda **kwargs: service,
    )
    monkeypatch.setattr(api, "_validate_wiki_dir", lambda value: Path(value))

    result = api.query_documentation(
        {
            "operation": "impact",
            "paths": ["app.py"],
            "include_raw_evidence": True,
        },
        src_dir=source_root.as_posix(),
        wiki_dir=(tmp_path / "wiki").as_posix(),
        allow_external_src=True,
    )

    assert result.get("raw_evidence") == []
    assert result["bounds"]["raw_evidence"] == {
        "total": 1,
        "returned": 0,
        "truncated": True,
    }
    byte_bound = result["bounds"]["raw_evidence_bytes"]
    byte_limit = byte_bound.get("limit")
    assert byte_limit == api.MAX_RAW_QUERY_EVIDENCE_BYTES
    raw_wire = json.dumps(
        result.get("raw_evidence"), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert byte_bound["returned"] == len(raw_wire)
    assert len(raw_wire) <= byte_limit
    assert byte_bound["total"] > byte_limit
    assert byte_bound["truncated"] is True
    assert len(json.dumps(result).encode("utf-8")) < 8 * 1024


def test_raw_evidence_byte_cap_includes_array_framing_and_separators():
    cap = api.MAX_RAW_QUERY_EVIDENCE_BYTES
    first = {"id": 1, "payload": ""}
    second = {"id": 2, "payload": ""}
    first_overhead = len(
        json.dumps(first, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    second_overhead = len(
        json.dumps(second, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    first["payload"] = "a" * (cap // 2 - first_overhead)
    first_wire = json.dumps(first, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    second["payload"] = "b" * (cap - 1 - len(first_wire) - second_overhead)
    full_wire = json.dumps(
        [first, second], sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert (
        sum(
            len(json.dumps(item, sort_keys=True, separators=(",", ":")).encode("utf-8"))
            for item in (first, second)
        )
        == cap - 1
    )
    assert len(full_wire) > cap

    selected, record_bound, byte_bound = api._bounded_raw_query_evidence(
        (first, second),
        limit=2,
    )
    selected_wire = json.dumps(selected, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )

    assert record_bound == {"total": 2, "returned": 1, "truncated": True}
    assert byte_bound == {
        "total": len(full_wire),
        "returned": len(selected_wire),
        "limit": cap,
        "truncated": True,
    }
    assert len(selected_wire) <= cap


def test_unified_diff_paths_are_bounded_exact_metadata_only():
    paths = documentation_query_builder.supplied_paths_from_unified_diff(
        "diff --git a/app.py b/app.py\n"
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    assert paths == ("app.py",)
    with pytest.raises(
        documentation_query_builder.DocumentationQueryError,
        match="canonical unified-diff",
    ):
        documentation_query_builder.supplied_paths_from_unified_diff(
            "ordinary text naming app.py"
        )


def test_unified_diff_ignores_header_looking_hunk_content():
    paths = documentation_query_builder.supplied_paths_from_unified_diff(
        "diff --git a/app.py b/app.py\n"
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -1 +1,3 @@\n"
        "-old\n"
        "+new\n"
        "--- a/secret.py\n"
        "+++ b/secret.py\n"
    )

    assert paths == ("app.py",)


@pytest.mark.parametrize(
    "diff",
    [
        "diff --git a/app.py b/app.py\n--- a/app.py\n",
        "diff --git a/app.py b/app.py\n+++ b/app.py\n",
        ("diff --git a/app.py b/app.py\n--- a/other.py\n+++ b/app.py\n"),
    ],
)
def test_unified_diff_rejects_unpaired_or_mismatched_file_headers(diff):
    with pytest.raises(documentation_query_builder.DocumentationQueryError):
        documentation_query_builder.supplied_paths_from_unified_diff(diff)


def test_targeted_builder_uses_snapshot_view_and_reports_stages(
    tmp_path,
    monkeypatch,
):
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "app.py").write_text("value = 1\n", encoding="utf-8")
    snapshot = SimpleNamespace(
        root=source_root,
        source_selection_identity=None,
        source_selection_inputs=None,
        captured_content_hashes={"app.py": "sha256:fixture"},
    )
    inventory_result = SimpleNamespace(source_snapshot=snapshot)
    extraction = SimpleNamespace(
        payload={"inventory": {"app.py": {}}, "entrypoints": [], "data_flows": []},
        inventory_result=inventory_result,
        dependency_analysis={"graph": {"nodes": [], "edges": []}},
    )
    snapshot_view = object()
    metrics = []

    monkeypatch.setattr(
        documentation_query_builder,
        "validate_live_query_source_selection",
        lambda **kwargs: None,
    )

    service = documentation_query_builder.build_live_documentation_query_service(
        source_root=source_root,
        wiki_root=tmp_path / "wiki",
        limit=4,
        read_only=True,
        include_plugins=False,
        paths=("app.py",),
        source_snapshot_builder=lambda root, **kwargs: snapshot,
        extract_payload_builder=lambda src, **kwargs: extraction,
        call_edge_resolver=lambda inventory: [],
        flow_builder=lambda entrypoint, call_edges: {},
        surface_evaluator=lambda *args, **kwargs: pytest.fail(
            "partial inventory evaluated a global live surface"
        ),
        knowledge_view_builder=lambda *args, **kwargs: pytest.fail(
            "partial inventory evaluated live knowledge freshness"
        ),
        snapshot_view_loader=lambda *args, **kwargs: snapshot_view,
        dependency_analyzer=lambda *args, **kwargs: {},
        service_factory=lambda inventory, **kwargs: {
            "surface": kwargs["surface_index"]
        },
        metrics_observer=metrics.append,
    )

    assert service == {"surface": None}
    assert set(metrics[0]["stages_ns"]) == {
        "source_selection",
        "source_snapshot",
        "extraction",
        "graph_construction",
        "knowledge_surface",
        "service_assembly",
    }
    assert metrics[0]["counts"]["requested_paths"] == 1
    assert metrics[0]["counts"]["inventory_files"] == 1


@pytest.mark.parametrize("knowledge_mode", ["off", "auto", "required"])
def test_python_and_mcp_context_modes_preserve_adapter_plugin_authority(
    tmp_path,
    monkeypatch,
    knowledge_mode,
):
    source_root = tmp_path / "source"
    source_root.mkdir()
    sentinel = source_root / "sentinel.txt"
    sentinel.write_text("unchanged\n", encoding="utf-8")
    seen = []

    def fake_build_context(*args, **kwargs):
        seen.append(dict(kwargs))
        return {
            "budget": args[1],
            "used": 0,
            "truncated": False,
            "omitted_files": [],
            "downgraded_files": {},
            "bounds": {},
            "files": {},
            "knowledge": {"mode": knowledge_mode},
        }, []

    monkeypatch.setattr(context_service, "_build_context", fake_build_context)

    python_result = api.build_context(
        source_root.as_posix(),
        wiki_dir=(tmp_path / "wiki").as_posix(),
        allow_external_src=True,
        knowledge_mode=knowledge_mode,
    )
    mcp_result = mcp_server.McpWikiService(
        src_dir=source_root.as_posix(),
        wiki_dir=(tmp_path / "wiki").as_posix(),
        allow_external_src=True,
    ).get_context(format="json", knowledge_mode=knowledge_mode)

    assert "knowledge" in python_result
    assert python_result["knowledge"] == mcp_result["knowledge"]
    assert [call["include_plugins"] for call in seen] == [True, False]
    assert all(call["knowledge_mode"] == knowledge_mode for call in seen)
    assert sentinel.read_text(encoding="utf-8") == "unchanged\n"


def test_required_mode_has_structured_python_and_mcp_errors(tmp_path, monkeypatch):
    source_root = tmp_path / "source"
    source_root.mkdir()

    def unavailable(*args, **kwargs):
        raise context_service.KnowledgeRequiredUnavailableError(
            availability="absent",
            reason="knowledge-artifact-absent",
            fallback_evidence=["repository-evidence"],
            recovery_command="llm-wiki sync",
        )

    monkeypatch.setattr(context_service, "_build_context", unavailable)
    with pytest.raises(api.WorkspaceStateError) as python_error:
        api.build_context(
            source_root.as_posix(),
            wiki_dir=(tmp_path / "wiki").as_posix(),
            allow_external_src=True,
            knowledge_mode="required",
        )
    with pytest.raises(mcp_server.McpWikiError) as mcp_error:
        mcp_server.McpWikiService(
            src_dir=source_root.as_posix(),
            wiki_dir=(tmp_path / "wiki").as_posix(),
            allow_external_src=True,
        ).get_context(format="json", knowledge_mode="required")

    assert python_error.value.code == "knowledge-required-unavailable"
    assert python_error.value.details is not None
    assert python_error.value.details["mutation_permitted"] is False
    assert mcp_error.value.code == "knowledge-required-unavailable"
    assert mcp_error.value.data is not None
    assert mcp_error.value.data == python_error.value.details


@pytest.mark.parametrize("operation", ["context", "packet"])
def test_python_and_mcp_path_policy_errors_have_equivalent_structure(operation):
    outside_source = "../outside-source"
    service = mcp_server.McpWikiService(src_dir=outside_source)

    with pytest.raises(api.PathPolicyError) as python_error:
        if operation == "context":
            api.build_context(outside_source, knowledge_mode="off")
        else:
            api.build_qualified_context(outside_source, knowledge_mode="off")
    with pytest.raises(mcp_server.McpWikiError) as mcp_error:
        if operation == "context":
            service.get_context(format="json", knowledge_mode="off")
        else:
            service.get_context_packet(knowledge_mode="off")

    assert python_error.value.code == "path-policy-error"
    assert python_error.value.details == {"field": "src_dir"}
    assert mcp_error.value.code == python_error.value.code
    assert mcp_error.value.data == python_error.value.details


def test_mcp_dispatcher_uses_the_supported_python_route(monkeypatch, tmp_path):
    expected = {"schema_version": "llm-wiki-documentation-query/v1"}
    seen = {}

    def fake_dispatch(request, **kwargs):
        seen["request"] = request
        seen["kwargs"] = kwargs
        return expected

    monkeypatch.setattr(mcp_server, "run_documentation_query", fake_dispatch)
    service = mcp_server.McpWikiService(
        src_dir=tmp_path.as_posix(),
        wiki_dir=(tmp_path / "wiki").as_posix(),
        allow_external_src=True,
    )

    assert service.query_documentation({"operation": "concept"}) == expected
    assert seen["request"] == {"operation": "concept"}
    assert seen["kwargs"]["allow_external_src"] is True


def test_snapshot_surface_query_has_representative_scale_bounds(monkeypatch):
    service = _SnapshotService()
    service.pages = [
        {
            "canonical_path": f"entities/generated-{index}.md",
            "mcp_uri": f"llm-wiki://entities/generated-{index}",
        }
        for index in range(10_000)
    ]
    service.pages.append(
        {"canonical_path": "api-contracts.md", "mcp_uri": "llm-wiki://api-contracts"}
    )
    monkeypatch.setattr(
        api,
        "_snapshot_query_service",
        lambda wiki_dir, *, limit: service,
    )

    tracemalloc.start()
    started = perf_counter()
    result = api.query_documentation(
        {"operation": "surface", "value": "api-contracts.md"}
    )
    elapsed = perf_counter() - started
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert result["bounds"]["pages"] == {
        "total": 1,
        "returned": 1,
        "truncated": False,
    }
    assert elapsed < 2.0
    assert peak_bytes < 32 * 1024 * 1024
    assert set(result["cost"]) == {
        "scope",
        "full_inventory_performed",
        "supplied_paths",
    }


_CONTEXT_PERFORMANCE_RECORD_PATH = (
    Path(__file__).parent / "records" / "knowledge" / "context-performance-gate.json"
)
_CONTEXT_PERFORMANCE_RECORD = json.loads(
    _CONTEXT_PERFORMANCE_RECORD_PATH.read_text(encoding="utf-8")
)
_CONTEXT_PERFORMANCE_BUDGETS = _CONTEXT_PERFORMANCE_RECORD["thresholds"]


def test_context_performance_threshold_record_is_explicit_and_portable():
    record = _CONTEXT_PERFORMANCE_RECORD

    assert record["schema_version"] == "llm-wiki-context-performance-gate/v1"
    assert record["record_kind"] == "context-performance-thresholds"
    assert record["fixtures"] == {
        "representative": {
            "knowledge": "ready one-module two-entity projection",
            "requests": [
                "auto context response",
                "auto qualified context packet",
            ],
        },
        "scale": {
            "concepts": 2_000,
            "relationships": 3_998,
            "source_files": 1,
        },
    }
    assert record["environment"] == {
        "capacity": "single worker; host CPU and memory capacity unspecified",
        "execution": "serialized in one pytest process",
        "filesystem": "temporary local fixture directory",
        "memory_measurement": "tracemalloc Python allocations",
        "network": "not used",
        "python": "project-supported Python >=3.10",
        "time_measurement": "time.perf_counter wall clock",
    }
    assert record["reproduce"] == (
        ".venv/bin/pytest -q tests/test_knowledge_query_adapters.py"
    )
    assert record["thresholds"] == {
        "representative_elapsed_seconds": 15.0,
        "representative_peak_bytes": 128 * 1024 * 1024,
        "representative_context_bytes": 512 * 1024,
        "representative_packet_bytes": 2 * 1024 * 1024,
        "scale_elapsed_seconds": 15.0,
        "scale_peak_bytes": 256 * 1024 * 1024,
        "scale_context_bytes": 512 * 1024,
        "scale_packet_bytes": 2 * 1024 * 1024,
        "named_stage_nanoseconds": 10_000_000_000,
    }


def _instrumented_stage(counters, durations, name, callback):
    started = perf_counter_ns()
    counters[name] = counters.get(name, 0) + 1
    result = callback()
    durations[name] = durations.get(name, 0) + perf_counter_ns() - started
    return result


def _materialize_ready_packet_project(tmp_path, monkeypatch):
    from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts
    from tests.knowledge_fixtures import (
        materialize_fixture_tree,
        one_module_two_entities_fixture,
    )
    from tests.test_context_packet_knowledge import _knowledge_commit_plan

    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(fixture, tmp_path / "checkout")
    commit_knowledge_artifacts(_knowledge_commit_plan(tree["wiki_root"], fixture))
    monkeypatch.chdir(tree["root"])
    return tree


def test_api_query_and_mcp_discovery_reject_external_wiki_page_symlink(
    tmp_path,
    monkeypatch,
    capsys,
):
    tree = _materialize_ready_packet_project(tmp_path, monkeypatch)
    outside = tmp_path / "external-secret.md"
    outside.write_text("# External secret\n\nnever expose this\n", encoding="utf-8")
    page = tree["page_paths"]["entities/User.md"]
    page.unlink()
    page.symlink_to(outside)

    cli_args = SimpleNamespace(
        request=None,
        src_dir=".",
        budget=32_000,
        format="json",
        focus="all",
        output=None,
        allow_external_src=False,
        read_only=True,
        wiki_dir="docs/llm_wiki",
        prefer_fresh=False,
        source_selection=None,
        knowledge_mode="auto",
    )
    with pytest.raises(SystemExit) as cli_error:
        context_service.run(cli_args)
    captured = capsys.readouterr()

    with pytest.raises(api.PathPolicyError) as list_error:
        api.list_wiki_pages("docs/llm_wiki")
    with pytest.raises(api.PathPolicyError) as context_error:
        api.build_context(".", knowledge_mode="auto")
    with pytest.raises(api.PathPolicyError) as query_error:
        api.query_documentation(
            {"operation": "concept", "value": "llm-wiki://entities/User"}
        )

    service = mcp_server.McpWikiService(wiki_dir="docs/llm_wiki")
    with pytest.raises(mcp_server.McpWikiError) as discovery_error:
        service.list_resources()
    with pytest.raises(mcp_server.McpWikiError) as direct_read_error:
        service.get_entity("User")
    with pytest.raises(mcp_server.McpWikiError) as mcp_context_error:
        service.get_context(format="json", knowledge_mode="auto")
    with pytest.raises(mcp_server.McpWikiError) as mcp_query_error:
        service.query_documentation(
            {"operation": "concept", "value": "llm-wiki://entities/User"}
        )

    expected_data = {"field": "wiki_dir", "path": "entities/User.md"}
    assert cli_error.value.code == 1
    assert captured.out == ""
    assert "entities/User.md" in captured.err
    assert "never expose this" not in captured.err
    assert list_error.value.code == "path-policy-error"
    assert list_error.value.details == expected_data
    assert context_error.value.code == "path-policy-error"
    assert context_error.value.details == expected_data
    assert query_error.value.code == "path-policy-error"
    assert query_error.value.details == expected_data
    assert discovery_error.value.code == "path-policy-error"
    assert discovery_error.value.data == expected_data
    assert direct_read_error.value.code == "path-policy-error"
    assert direct_read_error.value.data == expected_data
    assert mcp_context_error.value.code == "path-policy-error"
    assert mcp_context_error.value.data == expected_data
    assert mcp_query_error.value.code == "path-policy-error"
    assert mcp_query_error.value.data == expected_data


def test_real_representative_context_and_packet_have_attributable_budgets(
    tmp_path,
    monkeypatch,
):
    _materialize_ready_packet_project(tmp_path, monkeypatch)
    counters = {}
    durations = {}
    real_context_snapshot = context_service.build_source_snapshot
    real_packet_snapshot = context_packet.build_source_snapshot
    real_packet_input_integrity = (
        context_packet.source_snapshot_inputs_match_current_files
    )
    real_packet_integrity = context_packet.source_snapshot_matches_current_files
    real_inventory = context_service.get_inventory
    real_context_surface = context_service.evaluate_surface_index
    real_packet_surface = context_packet.evaluate_surface_index
    real_knowledge = context_service._build_context_knowledge_view
    real_freshness = knowledge_consumption.evaluate_knowledge_freshness
    real_service = context_service.DocumentationGraphQueryService
    real_selection = real_service.broad_context_selection
    inventory_plugin_modes = []

    def wrap(name, callback):
        def measured(*args, **kwargs):
            return _instrumented_stage(
                counters,
                durations,
                name,
                lambda: callback(*args, **kwargs),
            )

        return measured

    def measured_inventory(*args, **kwargs):
        inventory_plugin_modes.append(kwargs["include_plugins"])
        return _instrumented_stage(
            counters,
            durations,
            "deep_extraction",
            lambda: real_inventory(*args, **kwargs),
        )

    monkeypatch.setattr(
        context_service,
        "build_source_snapshot",
        wrap("source_snapshot", real_context_snapshot),
    )
    monkeypatch.setattr(
        context_packet,
        "build_source_snapshot",
        wrap("source_snapshot", real_packet_snapshot),
    )
    monkeypatch.setattr(
        context_packet,
        "source_snapshot_inputs_match_current_files",
        wrap("source_input_integrity_check", real_packet_input_integrity),
    )
    monkeypatch.setattr(
        context_packet,
        "source_snapshot_matches_current_files",
        wrap("source_structural_verification", real_packet_integrity),
    )
    monkeypatch.setattr(context_service, "get_inventory", measured_inventory)
    monkeypatch.setattr(
        context_service,
        "evaluate_surface_index",
        wrap("surface_evaluation", real_context_surface),
    )
    monkeypatch.setattr(
        context_packet,
        "evaluate_surface_index",
        wrap("surface_evaluation", real_packet_surface),
    )
    monkeypatch.setattr(
        context_service,
        "_build_context_knowledge_view",
        wrap("knowledge_read", real_knowledge),
    )
    monkeypatch.setattr(
        knowledge_consumption,
        "evaluate_knowledge_freshness",
        wrap("freshness_evaluation", real_freshness),
    )
    monkeypatch.setattr(
        context_service,
        "DocumentationGraphQueryService",
        wrap("graph_construction", real_service),
    )
    monkeypatch.setattr(
        context_packet,
        "DocumentationGraphQueryService",
        wrap("graph_construction", real_service),
    )
    monkeypatch.setattr(
        real_service,
        "broad_context_selection",
        wrap("knowledge_selection", real_selection),
    )

    tracemalloc.start()
    started = perf_counter()
    context_result = api.build_context(
        ".",
        wiki_dir="docs/llm_wiki",
        focus="all",
        knowledge_mode="auto",
    )
    assert counters == {
        "source_snapshot": 1,
        "deep_extraction": 1,
        "surface_evaluation": 1,
        "knowledge_read": 1,
        "freshness_evaluation": 1,
        "graph_construction": 1,
        "knowledge_selection": 1,
    }
    packet = api.build_qualified_context(
        ".",
        "docs/llm_wiki",
        {
            "budget_tokens": 32_000,
            "focus": ["all"],
            "format": "json",
            "filters": {},
            "prefer_fresh": False,
        },
        knowledge_mode="auto",
    )
    elapsed = perf_counter() - started
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    packet_payload = packet.to_payload()
    assert "knowledge" in context_result
    for knowledge in (
        context_result["knowledge"],
        packet_payload["response"]["knowledge"],
    ):
        assert isinstance(knowledge, dict)
        selection = knowledge.get("selection")
        assert isinstance(selection, dict)
        for name in ("concepts", "pages", "relationships"):
            assert len(selection[name]) == knowledge["bounds"][name]["returned"]
        assert knowledge["bounds"]["concepts"]["returned"] <= 20
        assert knowledge["bounds"]["pages"]["returned"] <= 20
        assert knowledge["bounds"]["relationships"]["returned"] <= 40

    assert counters == {
        "source_snapshot": 2,
        "source_input_integrity_check": 2,
        "source_structural_verification": 1,
        "deep_extraction": 2,
        "surface_evaluation": 2,
        "knowledge_read": 2,
        "freshness_evaluation": 2,
        "graph_construction": 2,
        "knowledge_selection": 2,
    }
    assert inventory_plugin_modes == [True, False]
    assert elapsed < _CONTEXT_PERFORMANCE_BUDGETS["representative_elapsed_seconds"]
    assert peak_bytes < _CONTEXT_PERFORMANCE_BUDGETS["representative_peak_bytes"]
    assert (
        len(json.dumps(context_result, sort_keys=True).encode("utf-8"))
        < (_CONTEXT_PERFORMANCE_BUDGETS["representative_context_bytes"])
    )
    assert (
        len(packet.to_bytes())
        < _CONTEXT_PERFORMANCE_BUDGETS["representative_packet_bytes"]
    )
    assert all(
        duration < _CONTEXT_PERFORMANCE_BUDGETS["named_stage_nanoseconds"]
        for duration in durations.values()
    )


@pytest.fixture(scope="module")
def scale_knowledge_view(tmp_path_factory):
    from dataclasses import replace

    from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
    from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
    from tests.test_knowledge_loader import _committed_state
    from tests.test_knowledge_freshness import _live_evaluation
    from tests.test_knowledge_performance import _stress_knowledge

    root = tmp_path_factory.mktemp("context-packet-scale")
    fixture, _plan, _result = _committed_state(root)
    loaded = load_knowledge_state(root)
    knowledge = _stress_knowledge(dict(fixture.knowledge_payload))
    return build_knowledge_read_view(
        replace(loaded, knowledge=knowledge),
        live_evaluation=_live_evaluation(knowledge),
    )


def _scale_surface(view):
    assert view.knowledge is not None
    pages = []
    for concept in view.knowledge.concepts:
        basis = concept.facets.structure.basis
        pages.append(
            {
                "kind": concept.document.page_kind.value,
                "id": concept.document.page_id,
                "title": concept.title,
                "canonical_path": concept.document.canonical_path,
                "source_path": None if basis is None else basis.source_path,
                "role": concept.document.role.value,
                "mcp_uri": concept.locator,
            }
        )
    return {"pages": pages}


def test_real_scale_selection_and_packet_validation_stay_bounded(
    scale_knowledge_view,
    tmp_path,
    monkeypatch,
):
    from llm_wiki_cli.services.documentation_queries import (
        DocumentationGraphQueryService,
    )

    _materialize_ready_packet_project(tmp_path, monkeypatch)
    stress_source = Path("src/stress.py")
    stress_source.parent.mkdir(parents=True, exist_ok=True)
    stress_source.write_text("STRESS = True\n", encoding="utf-8")
    monkeypatch.setattr(
        context_packet.context_service,
        "_build_context_knowledge_view",
        lambda *_args, **_kwargs: scale_knowledge_view,
    )
    monkeypatch.setattr(
        context_packet.context_service,
        "_context_query_surface",
        lambda *_args, **_kwargs: _scale_surface(scale_knowledge_view),
    )
    counters = {}
    durations = {}

    tracemalloc.start()
    started = perf_counter()
    service = _instrumented_stage(
        counters,
        durations,
        "graph_construction",
        lambda: DocumentationGraphQueryService(
            {},
            surface_index=_scale_surface(scale_knowledge_view),
            knowledge_view=scale_knowledge_view,
        ),
    )
    knowledge = _instrumented_stage(
        counters,
        durations,
        "knowledge_selection",
        lambda: context_service._build_explicit_knowledge_response(
            "auto",
            scale_knowledge_view,
            service,
            {"src/stress.py": "high"},
        ),
    )
    request = context_service._validate_protocol_request(
        {
            "protocol": context_service.KNOWLEDGE_PROTOCOL_VERSION,
            "budget_tokens": 32_000,
            "focus": ["all"],
            "format": "json",
            "filters": {},
            "prefer_fresh": False,
            "knowledge_mode": "auto",
        }
    )
    _instrumented_stage(
        counters,
        durations,
        "packet_response_validation",
        lambda: context_packet._validate_explicit_knowledge_response(
            knowledge,
            request,
        ),
    )
    context_wire = _instrumented_stage(
        counters,
        durations,
        "context_serialization",
        lambda: json.dumps(
            {"knowledge": knowledge},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    )
    scale_packet = api.build_qualified_context(
        ".",
        "docs/llm_wiki",
        request={
            "budget_tokens": 32_000,
            "focus": ["all"],
            "format": "json",
            "filters": {},
            "prefer_fresh": False,
        },
        knowledge_mode="auto",
    )
    validated = _instrumented_stage(
        counters,
        durations,
        "packet_validation",
        lambda: context_packet.validate_context_packet(scale_packet.to_bytes()),
    )
    elapsed = perf_counter() - started
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    bounds = knowledge["bounds"]
    assert bounds["concepts"] == {
        "total": 2_000,
        "returned": 20,
        "truncated": True,
    }
    assert bounds["pages"] == {
        "total": 2_000,
        "returned": 20,
        "truncated": True,
    }
    assert bounds["relationships"] == {
        "total": 3_998,
        "returned": 40,
        "truncated": True,
    }
    relationship_wire = [
        json.dumps(item, sort_keys=True, separators=(",", ":"))
        for item in knowledge["selection"]["relationships"]
    ]
    assert len(relationship_wire) == len(set(relationship_wire))
    packet_knowledge = scale_packet.to_payload()["response"]["knowledge"]
    assert packet_knowledge["bounds"] == bounds
    assert packet_knowledge["selection"] == knowledge["selection"]
    assert validated.valid is True
    assert counters == {
        "graph_construction": 1,
        "knowledge_selection": 1,
        "packet_response_validation": 1,
        "context_serialization": 1,
        "packet_validation": 1,
    }
    assert elapsed < _CONTEXT_PERFORMANCE_BUDGETS["scale_elapsed_seconds"]
    assert peak_bytes < _CONTEXT_PERFORMANCE_BUDGETS["scale_peak_bytes"]
    assert len(context_wire) < _CONTEXT_PERFORMANCE_BUDGETS["scale_context_bytes"]
    assert (
        len(scale_packet.to_bytes())
        < _CONTEXT_PERFORMANCE_BUDGETS["scale_packet_bytes"]
    )
    assert all(
        duration < _CONTEXT_PERFORMANCE_BUDGETS["named_stage_nanoseconds"]
        for duration in durations.values()
    )
    serialized = context_wire.decode("utf-8")
    assert "source_content_hash" not in serialized
    assert "concept_observation_hash" not in serialized
    assert '"diagnostics"' not in serialized
