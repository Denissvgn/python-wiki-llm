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
