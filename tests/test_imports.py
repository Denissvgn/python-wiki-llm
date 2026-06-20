"""Tests for import-module resolution helpers."""

from __future__ import annotations

from llm_wiki_cli.commands.bootstrap_cmd import _build_relationships
from llm_wiki_cli.services.imports import build_module_path_resolver


def test_indexed_resolver_handles_common_import_shapes():
    inventory = {
        "src/pkg/service.py": {},
        "pkg/feature/local.py": {},
        "pkg/shared.py": {},
        "pkg/a/settings.py": {},
        "pkg/b/settings.py": {},
    }
    resolver = build_module_path_resolver(inventory)

    assert resolver.candidates("pkg.service", "pkg/feature/use.py") == {
        "src/pkg/service.py"
    }
    assert resolver.candidates(".local", "pkg/feature/use.py") == {
        "pkg/feature/local.py"
    }
    assert resolver.candidates("../shared", "pkg/feature/use.py") == {"pkg/shared.py"}
    assert resolver.candidates("settings", "pkg/feature/use.py") == {
        "pkg/a/settings.py",
        "pkg/b/settings.py",
    }


def test_target_scoped_relationships_match_full_relationships_for_targets():
    inventory = {
        "models.py": {
            "classes": [{"name": "Model"}],
            "functions": [],
            "imports": [],
        },
        "api.py": {
            "classes": [],
            "imports": [{"module": "models", "name": "Model"}],
            "functions": [
                {
                    "name": "create",
                    "params": [{"name": "model", "type": "Model"}],
                    "return_type": "",
                    "decorators": [],
                }
            ],
        },
        "other.py": {
            "classes": [{"name": "Other"}],
            "functions": [],
            "imports": [],
        },
    }

    full = _build_relationships(inventory)
    scoped = _build_relationships(inventory, target_entities={("Model", "models.py")})

    assert scoped == {("Model", "models.py"): full[("Model", "models.py")]}
