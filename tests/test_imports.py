"""Tests for import-module resolution helpers."""

from __future__ import annotations

import json

from llm_wiki_cli.commands.bootstrap_cmd import _build_relationships
from llm_wiki_cli.services import imports as imports_service
from llm_wiki_cli.services.imports import build_module_path_resolver
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


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


def test_import_resolver_prefers_python_from_import_child_modules():
    inventory = {
        "src/pkg/cli.py": {"language": "python"},
        "src/pkg/commands/__init__.py": {"language": "python"},
        "src/pkg/commands/build.py": {"language": "python"},
        "src/pkg/config.py": {"language": "python"},
    }
    resolver = build_module_path_resolver(inventory)

    assert resolver.import_candidates(
        ".commands",
        "build",
        "src/pkg/cli.py",
        import_type="from",
    ) == {"src/pkg/commands/build.py"}
    assert resolver.import_candidates(
        ".config",
        "SETTING",
        "src/pkg/cli.py",
        import_type="from",
    ) == {"src/pkg/config.py"}


def test_import_resolver_does_not_treat_plain_import_alias_as_submodule():
    inventory = {
        "src/pkg/cli.py": {"language": "python"},
        "src/pkg/runtime.py": {"language": "python"},
        "src/pkg/runtime/alias.py": {"language": "python"},
    }
    resolver = build_module_path_resolver(inventory)

    assert resolver.import_candidates(
        ".runtime",
        "alias",
        "src/pkg/cli.py",
        import_type="import",
    ) == {"src/pkg/runtime.py"}


def test_generic_resolver_scopes_python_imports_to_python_modules():
    inventory = {
        "rlm/gateway.py": {"language": "python"},
        "rlm/openai.py": {"language": "python"},
        "internal/llm/openai.go": {"language": "go"},
        "internal/llm/anthropic.go": {"language": "go"},
    }
    resolver = build_module_path_resolver(inventory)

    assert resolver.candidates("openai", "rlm/gateway.py") == {"rlm/openai.py"}
    assert resolver.candidates("anthropic", "rlm/gateway.py") == set()


def test_generic_resolver_groups_typescript_and_javascript_without_other_languages():
    inventory = {
        "frontend/src/App.tsx": {"language": "typescript"},
        "frontend/src/api.js": {"language": "javascript"},
        "server/api.py": {"language": "python"},
        "internal/api.go": {"language": "go"},
    }
    resolver = build_module_path_resolver(inventory)

    assert resolver.candidates("api", "frontend/src/App.tsx") == {"frontend/src/api.js"}


def test_go_resolver_uses_module_root_without_stdlib_stem_collision(tmp_path):
    (tmp_path / "go.mod").write_text(
        "module github.com/charmbracelet/teamcrush\n\ngo 1.23\n",
        encoding="utf-8",
    )
    inventory = {
        "cmd/teamcrush/main.go": {"language": "go"},
        "internal/agents/agent.go": {"language": "go"},
        "internal/orchestrator/context.go": {"language": "go"},
    }
    resolver = build_module_path_resolver(inventory, project_root=str(tmp_path))

    assert resolver.candidates(
        "github.com/charmbracelet/teamcrush/internal/agents",
        "cmd/teamcrush/main.go",
    ) == {"internal/agents/agent.go"}
    assert resolver.candidates("context", "cmd/teamcrush/main.go") == set()


def test_go_resolver_uses_nearest_nested_module_root(tmp_path):
    nested = tmp_path / "libs" / "identity_client_go"
    nested.mkdir(parents=True)
    (nested / "go.mod").write_text(
        "module github.com/traid-platform/identityclient\n\ngo 1.21\n",
        encoding="utf-8",
    )
    inventory = {
        "libs/identity_client_go/example/main.go": {"language": "go"},
        "libs/identity_client_go/identity_client.go": {"language": "go"},
        "libs/identity_client_go/example/context.go": {"language": "go"},
    }
    resolver = build_module_path_resolver(inventory, project_root=str(tmp_path))

    assert resolver.candidates(
        "github.com/traid-platform/identityclient",
        "libs/identity_client_go/example/main.go",
    ) == {"libs/identity_client_go/identity_client.go"}
    assert (
        resolver.candidates(
            "context",
            "libs/identity_client_go/example/main.go",
        )
        == set()
    )


def test_haskell_resolver_uses_declared_module_under_nested_root():
    inventory = {
        "hls-analysis/app/Main.hs": {
            "language": "haskell",
            "module": "Main",
        },
        "hls-analysis/src/HLSAnalysis/API.hs": {
            "language": "haskell",
            "module": "HLSAnalysis.API",
        },
    }
    resolver = build_module_path_resolver(inventory)

    assert resolver.candidates("HLSAnalysis.API", "hls-analysis/app/Main.hs") == {
        "hls-analysis/src/HLSAnalysis/API.hs"
    }


def test_haskell_resolver_declared_module_matches_alternate_roots():
    inventory = {
        "app/Main.hs": {
            "language": "haskell",
            "module": "Main",
        },
        "src/HLSAnalysis/API.hs": {
            "language": "haskell",
            "module": "HLSAnalysis.API",
        },
        "lib/HLSAnalysis/API.hs": {
            "language": "haskell",
            "module": "HLSAnalysis.API",
        },
    }
    resolver = build_module_path_resolver(inventory)

    assert resolver.candidates("HLSAnalysis.API", "app/Main.hs") == {
        "src/HLSAnalysis/API.hs",
        "lib/HLSAnalysis/API.hs",
    }


def test_haskell_resolver_normalizes_declared_modules_without_changing_case():
    inventory = {
        "app/Main.hs": {
            "language": "haskell",
            "module": "Main",
        },
        "src/HLSAnalysis/API.hs": {
            "language": "haskell",
            "module": '  "HLSAnalysis.API"  ',
        },
    }
    resolver = build_module_path_resolver(inventory)

    assert resolver.candidates("  'HLSAnalysis.API'  ", "app/Main.hs") == {
        "src/HLSAnalysis/API.hs"
    }
    assert resolver.candidates("hlsanalysis.api", "app/Main.hs") == set()


def test_haskell_resolver_does_not_fallback_to_filepath_for_external_imports():
    inventory = {
        "app/Main.hs": {
            "language": "haskell",
            "module": "Main",
        },
        "Data/Text.hs": {
            "language": "haskell",
        },
        "Control/Monad.hs": {
            "language": "haskell",
        },
        "Test/Hspec.hs": {
            "language": "haskell",
        },
    }
    resolver = build_module_path_resolver(inventory)

    assert resolver.candidates("Data.Text", "app/Main.hs") == set()
    assert resolver.candidates("Control.Monad", "app/Main.hs") == set()
    assert resolver.candidates("Test.Hspec", "app/Main.hs") == set()


def test_haskell_resolver_ignores_entries_without_declared_module_for_bare_import():
    inventory = {
        "app/Main.hs": {
            "language": "haskell",
            "module": "Main",
        },
        "lib/Settings.hs": {
            "language": "haskell",
        },
    }
    resolver = build_module_path_resolver(inventory)

    assert resolver.candidates("Settings", "app/Main.hs") == set()


def test_typescript_resolver_uses_nearest_tsconfig_paths(tmp_path):
    frontend = tmp_path / "frontend"
    (frontend / "src" / "hooks").mkdir(parents=True)
    (frontend / "src" / "components" / "projects").mkdir(parents=True)
    (frontend / "tsconfig.json").write_text(
        """
        {
          "compilerOptions": {
            "baseUrl": ".",
            "paths": {
              "@/*": ["./src/*"],
              "@/components/*": ["./src/components/*"],
              "@/hooks/*": ["./src/hooks/*"]
            }
          }
        }
        """,
        encoding="utf-8",
    )
    inventory = {
        "frontend/src/App.tsx": {"language": "typescript"},
        "frontend/src/hooks/useAuth.ts": {"language": "typescript"},
        "frontend/src/components/projects/index.ts": {"language": "typescript"},
        "other/src/hooks/useAuth.ts": {"language": "typescript"},
    }
    resolver = build_module_path_resolver(inventory, project_root=tmp_path)

    assert resolver.candidates("@/hooks/useAuth", "frontend/src/App.tsx") == {
        "frontend/src/hooks/useAuth.ts"
    }
    assert resolver.candidates("@/components/projects", "frontend/src/App.tsx") == {
        "frontend/src/components/projects/index.ts"
    }
    assert resolver.candidates("@/hooks/useAuth", "other/src/page.tsx") == set()
    assert (
        resolver.typescript_path_alias_matched(
            "@tanstack/react-query", "frontend/src/App.tsx"
        )
        is False
    )


def test_resolver_reuses_snapshot_for_go_and_typescript_scopes(
    tmp_path,
    monkeypatch,
):
    frontend = tmp_path / "frontend"
    (frontend / "src").mkdir(parents=True)
    (tmp_path / "go.mod").write_text(
        "module example.com/project\n",
        encoding="utf-8",
    )
    (tmp_path / "cmd").mkdir()
    (frontend / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "baseUrl": ".",
                    "paths": {"@/*": ["./src/*"]},
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "cmd" / "main.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "internal.go").write_text("package project\n", encoding="utf-8")
    (frontend / "src" / "app.ts").write_text("", encoding="utf-8")
    (frontend / "src" / "client.ts").write_text("", encoding="utf-8")
    snapshot = build_source_snapshot(tmp_path)
    inventory = {
        "cmd/main.go": {"language": "go"},
        "internal.go": {"language": "go"},
        "frontend/src/app.ts": {"language": "typescript"},
        "frontend/src/client.ts": {"language": "typescript"},
    }

    def fail_if_walked(*_args, **_kwargs):
        raise AssertionError("module resolver must reuse the source snapshot")

    monkeypatch.setattr(imports_service.os, "walk", fail_if_walked)

    resolver = build_module_path_resolver(
        inventory,
        project_root=tmp_path,
        source_snapshot=snapshot,
    )

    assert resolver.candidates("example.com/project", "cmd/main.go") == {"internal.go"}
    assert resolver.candidates("@/client", "frontend/src/app.ts") == {
        "frontend/src/client.ts"
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
