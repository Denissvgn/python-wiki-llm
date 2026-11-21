"""The knowledge core borrows analysis-specific providers only through integrations."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
import subprocess
import sys

import pytest

import llm_wiki_cli  # noqa: F401 - names this package's providers
from llm_wiki_engine import integrations

ENGINE_ROOT = Path(integrations.__file__).resolve().parent


def _engine_uses() -> dict[str, set[str]]:
    """Every provider attribute the engine reads, found in its source."""
    uses: dict[str, set[str]] = {}
    for path in sorted(ENGINE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            arguments = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if node.func.id == "attributes" and arguments:
                uses.setdefault(arguments[0], set()).update(arguments[1:])
        for node in ast.walk(tree):
            # provider("capability").attribute
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "provider"
                and node.value.args
                and isinstance(node.value.args[0], ast.Constant)
                and isinstance(node.value.args[0].value, str)
            ):
                uses.setdefault(node.value.args[0].value, set()).add(node.attr)
    return uses


def test_cli_provides_every_capability_the_engine_uses():
    uses = _engine_uses()
    assert set(uses) <= set(integrations.CAPABILITIES)
    assert set(integrations.provided()) == set(integrations.CAPABILITIES)
    for capability, names in sorted(uses.items()):
        module = integrations.provider(capability)
        assert module.__name__.startswith("llm_wiki_cli.services.")
        assert sorted(name for name in names if not hasattr(module, name)) == [], capability


def test_cli_import_names_providers_without_importing_them():
    probe = (
        "import sys, llm_wiki_cli; from llm_wiki_engine import integrations; "
        "print(len(integrations.provided())); "
        "print(sorted(m for m in sys.modules if m.startswith('llm_wiki_cli.services')))"
    )
    result = subprocess.run([sys.executable, "-I", "-c", probe], capture_output=True, text=True, check=True)
    count, loaded = result.stdout.splitlines()
    assert int(count) == len(integrations.CAPABILITIES)
    assert loaded == "[]"


def test_missing_capability_fails_closed(monkeypatch):
    monkeypatch.setattr(integrations, "_PROVIDED", {})
    with pytest.raises(integrations.IntegrationUnavailable, match="implementation_evidence provider"):
        integrations.provider("implementation_evidence")
    with pytest.raises(integrations.IntegrationUnavailable):
        integrations.attributes("source_snapshots", "SourceSnapshot")


def test_provision_rejects_unknown_malformed_and_conflicting_names(monkeypatch):
    monkeypatch.setattr(integrations, "_PROVIDED", dict(integrations.provided()))
    with pytest.raises(ValueError, match="unknown"):
        integrations.provide({"telemetry": "example.module"})
    with pytest.raises(ValueError, match="module name"):
        integrations.provide({"domain_packs": "not a module"})
    with pytest.raises(ValueError, match="already provided"):
        integrations.provide({"domain_packs": "example.other_pack"})
    # Naming the same provider again is harmless.
    integrations.provide({"domain_packs": integrations.provided()["domain_packs"]})
    with pytest.raises(ValueError, match="unknown"):
        integrations.provider("telemetry")


def test_attributes_are_read_at_call_time(monkeypatch):
    module = integrations.provider("implementation_evidence")
    marker = object()
    monkeypatch.setattr(module, "validate_concept_implementation", marker)
    assert integrations.attributes("implementation_evidence", "validate_concept_implementation") == (marker,)
    knowledge_model = importlib.import_module("llm_wiki_engine.knowledge_model")
    assert knowledge_model is importlib.import_module("llm_wiki_engine.knowledge_model")


@pytest.fixture
def fake_providers(monkeypatch):
    """Two stand-in source snapshot providers, importable by name."""
    import types

    names = []
    for label in ("alpha", "beta"):
        name = f"tests_fake_snapshots_{label}"
        module = types.ModuleType(name)
        module.LABEL = label  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, name, module)
        names.append(name)
    return names


def test_integration_sets_validate_their_names():
    with pytest.raises(ValueError, match="unknown"):
        integrations.IntegrationSet({"telemetry": "example.module"})
    with pytest.raises(ValueError, match="module name"):
        integrations.IntegrationSet({"source_snapshots": "not a module"})
    with pytest.raises(TypeError, match="inherit"):
        integrations.IntegrationSet(inherit="no")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        with integrations.using_integrations({"source_snapshots": "x"}):  # type: ignore[arg-type]
            pass
    named = integrations.IntegrationSet({"source_snapshots": "example.snapshots"})
    assert named == integrations.IntegrationSet({"source_snapshots": "example.snapshots"})
    assert hash(named) == hash(integrations.IntegrationSet({"source_snapshots": "example.snapshots"}))
    assert named.describe() == {"modules": {"source_snapshots": "example.snapshots"}, "inherit": True}
    with pytest.raises(TypeError):
        named.modules["source_snapshots"] = "other"  # type: ignore[index]


def test_a_scope_wins_over_the_defaults_and_restores_them(fake_providers):
    alpha, beta = fake_providers
    default = integrations.provided()["source_snapshots"]
    with integrations.using_integrations(integrations.IntegrationSet({"source_snapshots": alpha})):
        assert integrations.provider("source_snapshots").LABEL == "alpha"
        # Unnamed capabilities keep the process-wide default.
        assert integrations.provided()["implementation_evidence"] == integrations.defaults()["implementation_evidence"]
        with integrations.using_integrations(integrations.IntegrationSet({"source_snapshots": beta})):
            assert integrations.provider("source_snapshots").LABEL == "beta"
        assert integrations.provider("source_snapshots").LABEL == "alpha"
    assert integrations.provided()["source_snapshots"] == default
    assert integrations.defaults()["source_snapshots"] == default


def test_an_isolated_scope_never_falls_back_to_the_defaults(fake_providers):
    alpha, _ = fake_providers
    isolated = integrations.IntegrationSet({"source_snapshots": alpha}, inherit=False)
    with integrations.using_integrations(isolated):
        assert integrations.provider("source_snapshots").LABEL == "alpha"
        assert set(integrations.provided()) == {"source_snapshots"}
        with pytest.raises(integrations.IntegrationUnavailable, match="implementation_evidence"):
            integrations.provider("implementation_evidence")


def test_merging_keeps_the_override_and_isolation(fake_providers):
    alpha, beta = fake_providers
    base = integrations.IntegrationSet({"source_snapshots": alpha, "inventory_results": alpha})
    merged = base.merged(integrations.IntegrationSet({"source_snapshots": beta}))
    assert dict(merged.modules) == {"inventory_results": alpha, "source_snapshots": beta}
    assert merged.inherit
    assert not base.merged(integrations.IntegrationSet(inherit=False)).inherit
    assert not integrations.IntegrationSet(inherit=False).merged(base).inherit


def test_two_engines_in_one_process_never_share_providers(fake_providers):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from llm_wiki_cli.engine import CODE_DOCS_PACK, Engine, IntegrationSet

    alpha, beta = fake_providers
    # One engine takes its provider from its pack, the other names its own.
    first = Engine(pack=CODE_DOCS_PACK.with_integrations(IntegrationSet({"source_snapshots": alpha})))
    second = Engine(integrations=IntegrationSet({"source_snapshots": beta}))
    both_inside = threading.Barrier(2, timeout=10)

    def observe(engine):
        with engine.operation() as operation:
            before = integrations.provider("source_snapshots").LABEL
            both_inside.wait()  # the other engine's scope is active right now
            after = integrations.provider("source_snapshots").LABEL
            return before, after, operation.integrations

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(observe, (first, second)))
    assert [result[:2] for result in results] == [("alpha", "alpha"), ("beta", "beta")]
    assert results[0][2] == IntegrationSet({"source_snapshots": alpha})
    # Interleaved on one thread, each operation still sees only its own.
    with first.operation():
        with second.operation():
            assert integrations.provider("source_snapshots").LABEL == "beta"
        assert integrations.provider("source_snapshots").LABEL == "alpha"
    assert integrations.provided()["source_snapshots"].startswith("llm_wiki_cli.services.")


def test_an_engine_choice_wins_over_its_pack(fake_providers):
    from llm_wiki_cli.engine import CODE_DOCS_PACK, Engine, IntegrationSet

    alpha, beta = fake_providers
    pack = CODE_DOCS_PACK.with_integrations(IntegrationSet({"source_snapshots": alpha}))
    engine = Engine(pack=pack, integrations=IntegrationSet({"source_snapshots": beta}))
    with engine.operation():
        assert integrations.provider("source_snapshots").LABEL == "beta"
    with pytest.raises(TypeError, match="IntegrationSet"):
        Engine(integrations={"source_snapshots": beta})  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="IntegrationSet"):
        CODE_DOCS_PACK.with_integrations({"source_snapshots": beta})  # type: ignore[arg-type]


def test_packet_builder_names_resolve_through_the_integration():
    from llm_wiki_engine import context_packet

    builders = integrations.provider("packet_builders")
    assert context_packet.capture_context_read is builders.capture_context_read
    with integrations.using_integrations(integrations.IntegrationSet(inherit=False)):
        with pytest.raises(AttributeError, match="packet_builders"):
            context_packet.capture_context_read  # noqa: B018
        assert not hasattr(context_packet, "reconcile_context_packet")
    with pytest.raises(AttributeError):
        context_packet.not_a_builder  # noqa: B018


def test_engine_packet_validation_loads_no_application_code():
    fixture = Path(__file__).resolve().parent / "fixtures" / "context-packet-v1.json"
    probe = (
        "import json, sys; from llm_wiki_engine import context_packet; "
        f"context_packet.validate_context_packet(open({str(fixture)!r}, 'rb').read()); "
        "print(sorted(m for m in sys.modules if m.split('.')[0] == 'llm_wiki_cli'))"
    )
    result = subprocess.run([sys.executable, "-I", "-c", probe], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "[]"


def test_moved_query_and_sync_names_stay_the_same_objects():
    from llm_wiki_cli.services import documentation_queries, documentation_query_builder, sync_analysis, sync_transitions
    from llm_wiki_engine import query_request_format, sync_ownership

    assert documentation_queries.DocumentationQueryError is query_request_format.DocumentationQueryError
    for name in query_request_format.__all__:
        assert getattr(documentation_query_builder, name) is getattr(query_request_format, name), name
    assert sync_analysis.SyncOwnershipError is sync_ownership.SyncOwnershipError
    assert sync_transitions.PageTransitionError is sync_ownership.PageTransitionError
    assert issubclass(sync_ownership.PageTransitionError, sync_ownership.SyncOwnershipError)


def test_engine_search_reads_source_snapshots_through_the_integration(tmp_path):
    from llm_wiki_engine import search_service

    with integrations.using_integrations(integrations.IntegrationSet(inherit=False)):
        with pytest.raises(integrations.IntegrationUnavailable, match="source_snapshots"):
            search_service.capture_source_selection_inputs(tmp_path, source_selection=None, selection_policy=None)
    snapshots = integrations.provider("source_snapshots")
    assert snapshots.__name__ == "llm_wiki_cli.services.source_snapshot"
