"""Protocol registry coverage and migration-policy contracts."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from llm_wiki_cli.services.contracts import (
    CONTEXT_PROTOCOL_VERSION,
    PROTOCOL_VERSIONS,
)


_PROTOCOL_RE = re.compile(r"^llm-wiki-.+/v[1-9][0-9]*$")
_CONTRACTS_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "llm_wiki_cli"
    / "services"
    / "contracts.py"
)
_DOCUMENTATION_PATH = (
    Path(__file__).parents[1] / "docs" / "standalone-documentation.md"
)


def _protocol_literals(source: str) -> set[str]:
    tree = ast.parse(source)
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and _PROTOCOL_RE.fullmatch(node.value)
    }


def _unregistered_protocols(source: str) -> set[str]:
    return _protocol_literals(source) - set(PROTOCOL_VERSIONS)


def test_every_contract_protocol_is_registered_once():
    source = _CONTRACTS_PATH.read_text(encoding="utf-8")

    assert _unregistered_protocols(source) == set()
    assert len(PROTOCOL_VERSIONS) == len(set(PROTOCOL_VERSIONS))
    assert CONTEXT_PROTOCOL_VERSION in PROTOCOL_VERSIONS


def test_registry_guard_detects_an_unregistered_protocol_literal():
    source = _CONTRACTS_PATH.read_text(encoding="utf-8")
    candidate = "llm-wiki-registry-guard-probe/v1"
    mutated_source = (
        source + f'\nREGISTRY_GUARD_PROBE_SCHEMA_VERSION = "{candidate}"\n'
    )

    assert _unregistered_protocols(mutated_source) == {candidate}


def test_protocol_migration_policy_defines_compatibility_and_deprecation():
    documentation = _DOCUMENTATION_PATH.read_text(encoding="utf-8")
    section = documentation.split("## Protocol versioning", 1)[1].split(
        "\n## ",
        1,
    )[0]
    policy = " ".join(section.split())

    assert "optional fields" in policy
    assert "never bumps the protocol version" in policy
    assert "ignore unknown fields from the same major version" in policy
    assert "Renaming or removing a field" in policy
    assert "new major protocol version" in policy
    assert "at least one minor package release" in policy
    assert "emit both representations" in policy
