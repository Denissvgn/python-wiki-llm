"""Formats are versioned by their own identifiers, not by the package version.

The CLI and the engine are released in lockstep, so the package version
changes with every release. A format identifier that followed it would change
canonical bytes and break consumers without any change to the format itself.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re

import llm_wiki_cli
import llm_wiki_engine

ENGINE_ROOT = Path(llm_wiki_engine.__file__).resolve().parent
SCHEMA_ROOT = Path(llm_wiki_cli.__file__).resolve().parent / "schemas"
FORMAT_ID = re.compile(r"[a-z][a-z0-9-]*(?:/[a-z][a-z0-9-]*)*/v[0-9]+\Z")
SEMVER = re.compile(r"\d+\.\d+\.\d+")


def test_engine_modules_never_read_the_package_version():
    found = []
    for path in sorted(ENGINE_ROOT.rglob("*.py")):
        if path.name == "__init__.py" and path.parent == ENGINE_ROOT:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and any(alias.name == "__version__" for alias in node.names):
                found.append(f"{path.name}: imports __version__")
            if isinstance(node, ast.Attribute) and node.attr == "__version__":
                found.append(f"{path.name}: reads __version__")
            names = [alias.name for alias in node.names] if isinstance(node, (ast.Import, ast.ImportFrom)) else []
            module = node.module if isinstance(node, ast.ImportFrom) else None
            if module == "importlib.metadata" or "importlib.metadata" in names:
                found.append(f"{path.name}: inspects installed distributions")
    assert found == []


def test_published_format_identifiers_carry_no_package_version():
    identifiers = {}
    for path in sorted(SCHEMA_ROOT.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        identifiers[path.name] = schema["$id"]
        version = schema.get("properties", {}).get("schema_version", {})
        if "const" in version:
            identifiers[path.name + "#schema_version"] = version["const"]
            assert FORMAT_ID.fullmatch(version["const"]), (path.name, version["const"])
    assert identifiers
    assert [name for name, value in identifiers.items() if SEMVER.search(value)] == []
    assert llm_wiki_engine.__version__ not in json.dumps(identifiers)
