"""On-disk names are defined once, in llm_wiki_engine.layout."""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from llm_wiki_engine.layout import DEFAULT_LAYOUT, Layout

SRC = Path(__file__).resolve().parents[1] / "src"
NAMES = {getattr(DEFAULT_LAYOUT, field.name): field.name for field in dataclasses.fields(Layout)}


def _code_literals(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    skipped: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                skipped.add(id(first.value))
        if isinstance(node, ast.JoinedStr):
            skipped.update(id(child) for child in ast.walk(node))
    return [
        f"{path.relative_to(SRC)}:{node.lineno}: {node.value!r}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and node.value in NAMES and id(node) not in skipped
    ]


def test_layout_names_are_not_repeated_in_code():
    found = []
    for package in ("llm_wiki_engine", "llm_wiki_cli"):
        for path in sorted((SRC / package).rglob("*.py")):
            if path == SRC / "llm_wiki_engine" / "layout.py":
                continue
            found += _code_literals(path)
    assert found == [], "use llm_wiki_engine.layout.DEFAULT_LAYOUT instead"


def test_existing_names_come_from_the_layout():
    from llm_wiki_engine import (
        circuit_breaker,
        knowledge_artifacts,
        knowledge_governance,
        knowledge_storage,
        maintenance_protocol,
        path_policy,
        sync_manifest,
        sync_transition_execution,
        verification_contracts,
        wiki_surface_index,
    )

    assert sync_manifest.MANIFEST_FILENAME == DEFAULT_LAYOUT.manifest == ".llm-wiki-manifest.json"
    assert knowledge_artifacts.KNOWLEDGE_INDEX_FILENAME == DEFAULT_LAYOUT.knowledge_index
    assert knowledge_storage.ROOT_FILENAME == DEFAULT_LAYOUT.knowledge_index
    assert knowledge_governance.GOVERNANCE_FILENAME == DEFAULT_LAYOUT.governance
    assert knowledge_governance.GOVERNANCE_LOCK_FILENAME == DEFAULT_LAYOUT.governance_lock
    assert maintenance_protocol.ADOPTION_FILENAME == DEFAULT_LAYOUT.maintenance_adoption
    assert maintenance_protocol.STORAGE_LOCK_FILENAME == DEFAULT_LAYOUT.storage_lock
    assert wiki_surface_index.SURFACE_INDEX_FILENAME == DEFAULT_LAYOUT.surface_index
    assert verification_contracts.VERIFICATION_RECEIPT_FILENAME == DEFAULT_LAYOUT.verification_receipt
    assert sync_transition_execution.RECOVERY_PREFIX == DEFAULT_LAYOUT.page_move_recovery_prefix
    assert circuit_breaker._STATE_FILE == DEFAULT_LAYOUT.breaker_state
    assert path_policy.DEFAULT_WIKI_DIR == DEFAULT_LAYOUT.wiki_dir == "docs/llm_wiki"
    assert {DEFAULT_LAYOUT.knowledge_store, DEFAULT_LAYOUT.manifest_objects} <= path_policy.EXCLUDED_DIRS


def test_the_layout_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        DEFAULT_LAYOUT.manifest = "other.json"  # type: ignore[misc]
