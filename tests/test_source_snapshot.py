"""Tests for shared source-tree discovery snapshots."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from llm_wiki_cli.extractors.common import discover_source_files
from llm_wiki_cli.services.knowledge_envelope import ConsumedInputKind
from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.source_snapshot import (
    SourceSnapshotError,
    build_source_snapshot,
    unsupported_source_summary,
)


def _paths(snapshot, language: str) -> list[str]:
    return snapshot.language_paths(language)


def test_build_source_snapshot_stays_decomposed():
    assert len(inspect.getsource(build_source_snapshot).splitlines()) <= 60


def test_groups_builtin_language_files(tmp_path):
    (tmp_path / "app.py").write_text("class App: pass\n")
    (tmp_path / "ui.ts").write_text("export const x = 1;\n")
    (tmp_path / "view.tsx").write_text("export const View = () => null;\n")
    (tmp_path / "script.js").write_text("export function run() {}\n")
    (tmp_path / "widget.jsx").write_text("export function Widget() { return null; }\n")
    (tmp_path / "main.go").write_text("package main\n")
    (tmp_path / "lib.rs").write_text("pub fn run() {}\n")
    (tmp_path / "API.hs").write_text("module API where\n")
    (tmp_path / "Guide.lhs").write_text("> module Guide where\n")

    snapshot = build_source_snapshot(tmp_path)

    assert _paths(snapshot, "python") == ["app.py"]
    assert _paths(snapshot, "typescript") == [
        "script.js",
        "ui.ts",
        "view.tsx",
        "widget.jsx",
    ]
    assert _paths(snapshot, "go") == ["main.go"]
    assert _paths(snapshot, "rust") == ["lib.rs"]
    assert _paths(snapshot, "haskell") == ["API.hs", "Guide.lhs"]
    assert snapshot.all_source_paths == (
        "API.hs",
        "Guide.lhs",
        "app.py",
        "lib.rs",
        "main.go",
        "script.js",
        "ui.ts",
        "view.tsx",
        "widget.jsx",
    )


def test_javascript_sources_keep_default_exclusions(tmp_path):
    (tmp_path / "app.js").write_text("export function app() {}\n", encoding="utf-8")
    (tmp_path / "view.jsx").write_text(
        "export function View() { return null; }\n", encoding="utf-8"
    )
    for dirname, filename in (
        ("dist", "bundle.js"),
        ("node_modules/pkg", "index.js"),
        ("venv/lib", "dep.js"),
        (".claude/worktrees/agent/web", "copy.jsx"),
    ):
        target_dir = tmp_path / dirname
        target_dir.mkdir(parents=True)
        (target_dir / filename).write_text(
            "export function ignored() {}\n", encoding="utf-8"
        )

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.language_paths("typescript") == ["app.js", "view.jsx"]
    assert snapshot.all_source_paths == ("app.js", "view.jsx")
    assert unsupported_source_summary(snapshot) == {}


def test_generated_javascript_bundles_are_advisory_unsupported_only(tmp_path):
    first_party_files = (
        "services/dashboard/frontend/src/main.js",
        "host/app/src/main.js",
        "host/extension/shared/transport.js",
        "services/dashboard/static/app.js",
    )
    generated_files = (
        "services/dashboard/static/assets/index-D0zaI3XT.js",
        "services/dashboard/static/assets/ProjectList--B600j8c.js",
        "services/dashboard/static/assets/MeetingList-NYNwTJXX.js",
        "services/dashboard/static/assets/meetings-DwH1QO_9.js",
        "services/dashboard/static/assets/vendor.min.js",
    )
    for rel_path in first_party_files:
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("export function visible() {}\n", encoding="utf-8")
    for rel_path in generated_files:
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("function a(){};export{a as Ko};\n", encoding="utf-8")

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.language_paths("typescript") == [
        "host/app/src/main.js",
        "host/extension/shared/transport.js",
        "services/dashboard/frontend/src/main.js",
        "services/dashboard/static/app.js",
    ]
    assert unsupported_source_summary(snapshot) == {
        "generated_javascript_bundle": {
            "count": 5,
            "paths": sorted(generated_files),
        }
    }


def test_only_files_can_opt_into_exact_generated_javascript_bundle(tmp_path):
    generated = "services/dashboard/static/assets/index-D0zaI3XT.js"
    path = tmp_path / generated
    path.parent.mkdir(parents=True)
    path.write_text("function a(){};export{a as Ko};\n", encoding="utf-8")

    snapshot = build_source_snapshot(tmp_path, only_files=[generated])

    assert snapshot.language_paths("typescript") == [generated]
    assert unsupported_source_summary(snapshot) == {}


def test_shell_sources_are_advisory_unsupported_only(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "deploy.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (tmp_path / "ignored.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("ignored.sh\n", encoding="utf-8")
    excluded = tmp_path / ".venv" / "bin"
    excluded.mkdir(parents=True)
    (excluded / "activate.sh").write_text("#!/bin/sh\n", encoding="utf-8")

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.unsupported_language_paths("shell") == ["scripts/deploy.sh"]
    assert unsupported_source_summary(snapshot) == {
        "shell": {"count": 1, "paths": ["scripts/deploy.sh"]}
    }
    assert snapshot.all_source_paths == ()


def test_records_supported_haskell_sources_with_filtering(tmp_path):
    (tmp_path / ".gitignore").write_text("ignored.hs\n", encoding="utf-8")
    hls_app = tmp_path / "hls-analysis" / "app"
    hls_src = tmp_path / "hls-analysis" / "src" / "HLSAnalysis"
    hls_lhs = tmp_path / "hls-analysis" / "literate"
    hls_app.mkdir(parents=True)
    hls_src.mkdir(parents=True)
    hls_lhs.mkdir(parents=True)
    (hls_app / "Main.hs").write_text("module Main where\n", encoding="utf-8")
    (hls_src / "API.hs").write_text("module HLSAnalysis.API where\n", encoding="utf-8")
    (hls_lhs / "Guide.lhs").write_text("> module Guide where\n", encoding="utf-8")
    (tmp_path / "ignored.hs").write_text("module Ignored where\n", encoding="utf-8")
    excluded = tmp_path / ".venv"
    excluded.mkdir()
    (excluded / "Hidden.hs").write_text("module Hidden where\n", encoding="utf-8")

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.language_paths("haskell") == [
        "hls-analysis/app/Main.hs",
        "hls-analysis/literate/Guide.lhs",
        "hls-analysis/src/HLSAnalysis/API.hs",
    ]
    assert snapshot.unsupported_language_paths("haskell") == []
    assert snapshot.all_source_paths == (
        "hls-analysis/app/Main.hs",
        "hls-analysis/literate/Guide.lhs",
        "hls-analysis/src/HLSAnalysis/API.hs",
    )
    assert unsupported_source_summary(snapshot) == {}
    assert unsupported_source_summary(snapshot, supported_languages={"haskell"}) == {}


def test_haskell_sources_respect_only_files(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "Main.hs").write_text("module Main where\n", encoding="utf-8")
    (tmp_path / "app" / "Other.hs").write_text("module Other where\n", encoding="utf-8")

    snapshot = build_source_snapshot(tmp_path, only_files=["app/Main.hs"])

    assert snapshot.language_paths("haskell") == ["app/Main.hs"]
    assert snapshot.unsupported_language_paths("haskell") == []


def test_only_files_and_filtering_rules(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}_outside.py"
    outside.write_text("class Outside: pass\n")
    try:
        (tmp_path / "app.py").write_text("class App: pass\n")
        (tmp_path / "types.d.ts").write_text("declare const x: string;\n")
        (tmp_path / "main_test.go").write_text("package main\n")
        (tmp_path / "README.md").write_text("# docs\n")
        hidden = tmp_path / ".venv"
        hidden.mkdir()
        (hidden / "dep.py").write_text("class Hidden: pass\n")

        snapshot = build_source_snapshot(
            tmp_path,
            only_files=[
                "app.py",
                "missing.py",
                f"../{tmp_path.name}_outside.py",
                "types.d.ts",
                "main_test.go",
                ".venv/dep.py",
                "README.md",
            ],
        )

        assert _paths(snapshot, "python") == ["app.py"]
        assert _paths(snapshot, "typescript") == ["types.d.ts"]
        assert _paths(snapshot, "go") == []
    finally:
        outside.unlink(missing_ok=True)


def test_only_files_bypass_gitignore_for_explicit_source_paths(tmp_path):
    (tmp_path / ".gitignore").write_text("lib/\n", encoding="utf-8")
    lib_dir = tmp_path / "frontend" / "src" / "lib"
    lib_dir.mkdir(parents=True)
    (lib_dir / "api.ts").write_text("export const api = 1;\n", encoding="utf-8")

    snapshot = build_source_snapshot(
        tmp_path,
        only_files=["frontend/src/lib/api.ts"],
    )

    assert snapshot.language_paths("typescript") == ["frontend/src/lib/api.ts"]


def test_gitignore_directory_rules_ignore_unescaped_trailing_spaces(tmp_path):
    (tmp_path / ".gitignore").write_text(".shared/ \n.agent/   \n", encoding="utf-8")
    for dirname in (".shared", ".agent"):
        ignored_dir = tmp_path / dirname
        ignored_dir.mkdir()
        (ignored_dir / "example.py").write_text(
            "class Ignored: pass\n", encoding="utf-8"
        )
    (tmp_path / "visible.py").write_text("class Visible: pass\n", encoding="utf-8")

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.language_paths("python") == ["visible.py"]
    assert snapshot.all_source_paths == ("visible.py",)


def test_root_lib_gitignore_keeps_typescript_src_lib_modules(tmp_path):
    (tmp_path / ".gitignore").write_text("lib/\n", encoding="utf-8")
    source_lib = tmp_path / "frontend" / "src" / "lib"
    source_lib.mkdir(parents=True)
    for name in (
        "api.ts",
        "api.tsx",
        "queryClient.ts",
        "queryClient.tsx",
        "utils.ts",
        "utils.tsx",
        "websocket.ts",
        "websocket.tsx",
    ):
        (source_lib / name).write_text("export const value = 1;\n", encoding="utf-8")
    root_lib = tmp_path / "lib"
    root_lib.mkdir()
    (root_lib / "generated.ts").write_text(
        "export const generated = 1;\n", encoding="utf-8"
    )

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.language_paths("typescript") == [
        "frontend/src/lib/api.ts",
        "frontend/src/lib/api.tsx",
        "frontend/src/lib/queryClient.ts",
        "frontend/src/lib/queryClient.tsx",
        "frontend/src/lib/utils.ts",
        "frontend/src/lib/utils.tsx",
        "frontend/src/lib/websocket.ts",
        "frontend/src/lib/websocket.tsx",
    ]


def test_agent_worktree_sources_are_excluded_by_default(tmp_path):
    (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  app:\n    build: .\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "real"\n', encoding="utf-8"
    )
    claude_source = tmp_path / ".claude" / "source"
    claude_source.mkdir(parents=True)
    (claude_source / "notes.py").write_text("class Notes: pass\n", encoding="utf-8")

    worktree = tmp_path / ".claude" / "worktrees" / "agent-strict-instructions"
    worktree.mkdir(parents=True)
    (worktree / "app.py").write_text("class WorktreeApp: pass\n", encoding="utf-8")
    (worktree / "Dockerfile").write_text("FROM alpine\n", encoding="utf-8")
    (worktree / "docker-compose.yml").write_text(
        "services:\n  agent:\n    image: alpine\n", encoding="utf-8"
    )
    (worktree / "pyproject.toml").write_text(
        '[project]\nname = "generated"\n', encoding="utf-8"
    )

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.language_paths("python") == [".claude/source/notes.py", "app.py"]
    assert [item.rel_path for item in snapshot.dockerfile_candidates] == ["Dockerfile"]
    assert [item.rel_path for item in snapshot.compose_candidates] == [
        "docker-compose.yml"
    ]
    assert [item.rel_path for item in snapshot.package_markers] == ["pyproject.toml"]
    assert not any(
        path.startswith(".claude/worktrees/")
        for path in (
            list(snapshot.all_source_paths)
            + [item.rel_path for item in snapshot.dockerfile_candidates]
            + [item.rel_path for item in snapshot.compose_candidates]
            + [item.rel_path for item in snapshot.yaml_candidates]
            + [item.rel_path for item in snapshot.package_markers]
        )
    )


def test_only_files_can_opt_into_exact_agent_worktree_source(tmp_path):
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    worktree = tmp_path / ".claude" / "worktrees" / "agent-strict-instructions"
    worktree.mkdir(parents=True)
    (worktree / "app.py").write_text("class WorktreeApp: pass\n", encoding="utf-8")
    (worktree / "sibling.py").write_text("class Sibling: pass\n", encoding="utf-8")
    (worktree / "Dockerfile").write_text("FROM alpine\n", encoding="utf-8")
    (worktree / "pyproject.toml").write_text(
        '[project]\nname = "generated"\n', encoding="utf-8"
    )

    snapshot = build_source_snapshot(
        tmp_path,
        only_files=[".claude/worktrees/agent-strict-instructions/app.py"],
    )

    assert snapshot.language_paths("python") == [
        ".claude/worktrees/agent-strict-instructions/app.py"
    ]
    assert [item.rel_path for item in snapshot.dockerfile_candidates] == ["Dockerfile"]
    assert [item.rel_path for item in snapshot.package_markers] == []


def test_nested_lib_gitignore_still_excludes_typescript_src_lib_modules(tmp_path):
    nested_src = tmp_path / "frontend" / "src"
    nested_src.mkdir(parents=True)
    (nested_src / ".gitignore").write_text("lib/\n", encoding="utf-8")
    source_lib = nested_src / "lib"
    source_lib.mkdir()
    (source_lib / "api.ts").write_text("export const api = 1;\n", encoding="utf-8")
    (tmp_path / "frontend" / "src" / "main.tsx").write_text(
        "export const main = 1;\n", encoding="utf-8"
    )

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.language_paths("typescript") == ["frontend/src/main.tsx"]


def test_go_test_files_are_excluded_by_default_and_included_when_opted_in(tmp_path):
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "main_test.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "integration_test.go").write_text(
        "package pkg\n", encoding="utf-8"
    )

    default_snapshot = build_source_snapshot(tmp_path)
    opted_in_snapshot = build_source_snapshot(tmp_path, include_tests={"go"})

    assert _paths(default_snapshot, "go") == ["main.go"]
    assert _paths(opted_in_snapshot, "go") == [
        "main.go",
        "main_test.go",
        "pkg/integration_test.go",
    ]
    assert opted_in_snapshot.all_source_paths == (
        "main.go",
        "main_test.go",
        "pkg/integration_test.go",
    )


def test_go_test_only_files_require_include_tests_opt_in(tmp_path):
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "main_test.go").write_text("package main\n", encoding="utf-8")

    default_snapshot = build_source_snapshot(
        tmp_path,
        only_files=["main.go", "main_test.go"],
    )
    opted_in_snapshot = build_source_snapshot(
        tmp_path,
        only_files=["main.go", "main_test.go"],
        include_tests={"go"},
    )

    assert _paths(default_snapshot, "go") == ["main.go"]
    assert _paths(opted_in_snapshot, "go") == ["main.go", "main_test.go"]


def test_go_test_opt_in_still_respects_gitignore_and_excluded_dirs(tmp_path):
    (tmp_path / ".gitignore").write_text("ignored_test.go\n", encoding="utf-8")
    (tmp_path / "visible_test.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "ignored_test.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "target" / "dep").mkdir(parents=True)
    (tmp_path / "target" / "dep" / "dep_test.go").write_text(
        "package dep\n", encoding="utf-8"
    )

    snapshot = build_source_snapshot(tmp_path, include_tests={"go"})

    assert _paths(snapshot, "go") == ["visible_test.go"]


def test_discover_source_files_includes_go_tests_only_when_opted_in(tmp_path):
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "main_test.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "app_test.py").write_text("def test_app(): pass\n", encoding="utf-8")

    default_go = discover_source_files(str(tmp_path), (".go",), language="go")
    opted_in_go = discover_source_files(
        str(tmp_path),
        (".go",),
        language="go",
        include_tests={"go"},
    )
    python_files = discover_source_files(str(tmp_path), (".py",), language="python")

    assert default_go == ["main.go"]
    assert opted_in_go == ["main.go", "main_test.go"]
    assert python_files == ["app_test.py"]


def test_respects_root_and_nested_gitignore(tmp_path):
    (tmp_path / ".gitignore").write_text("ignored.py\nroot_ignored/\n")
    (tmp_path / "ignored.py").write_text("class Ignored: pass\n")
    root_ignored = tmp_path / "root_ignored"
    root_ignored.mkdir()
    (root_ignored / "hidden.py").write_text("class Hidden: pass\n")

    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / ".gitignore").write_text("nested_ignored.py\n")
    (pkg / "nested_ignored.py").write_text("class NestedIgnored: pass\n")
    (pkg / "visible.py").write_text("class Visible: pass\n")

    snapshot = build_source_snapshot(tmp_path)

    assert _paths(snapshot, "python") == ["pkg/visible.py"]
    assert snapshot.gitignore_fingerprint.startswith("sha256:")


def test_gitignore_fingerprint_changes_with_discovered_gitignore(tmp_path):
    (tmp_path / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
    first = build_source_snapshot(tmp_path)

    (tmp_path / ".gitignore").write_text("ignored.py\nother.py\n", encoding="utf-8")
    second = build_source_snapshot(tmp_path)

    assert second.gitignore_fingerprint != first.gitignore_fingerprint


def test_captures_exact_consumed_input_hashes_and_overlap_kinds(tmp_path):
    files = {
        ".gitignore": b"ignored.py\n",
        "app.py": b"class App: pass\n",
        "compose.yaml": b"services:\n  web:\n    image: nginx\n",
        "pyproject.toml": b'[project]\nname = "demo"\n',
    }
    for rel_path in reversed(tuple(files)):
        (tmp_path / rel_path).write_bytes(files[rel_path])

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.captured_content_hashes == {
        path: sha256_bytes(content) for path, content in sorted(files.items())
    }
    assert snapshot.captured_input_kinds == {
        ".gitignore": ("selection",),
        "app.py": ("source",),
        "compose.yaml": ("compose", "yaml"),
        "pyproject.toml": ("package",),
    }
    assert [(item.path, item.kind_value) for item in snapshot.to_consumed_inputs()] == [
        (".gitignore", ConsumedInputKind.SELECTION.value),
        ("app.py", ConsumedInputKind.SOURCE.value),
        ("compose.yaml", ConsumedInputKind.COMPOSE.value),
        ("pyproject.toml", ConsumedInputKind.PACKAGE.value),
    ]


def test_snapshot_reads_each_captured_input_once(tmp_path, monkeypatch):
    (tmp_path / ".gitignore").write_text("ignored.py\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
    (tmp_path / "compose.yaml").write_text("services: {}\n", encoding="utf-8")
    real_open = Path.open
    binary_reads: dict[str, int] = {}

    def tracking_open(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if mode == "rb":
            try:
                rel_path = path.resolve().relative_to(tmp_path).as_posix()
            except ValueError:
                pass
            else:
                binary_reads[rel_path] = binary_reads.get(rel_path, 0) + 1
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", tracking_open)

    snapshot = build_source_snapshot(tmp_path)

    assert sorted(snapshot.captured_content_hashes) == [
        ".gitignore",
        "app.py",
        "compose.yaml",
    ]
    assert binary_reads == {
        ".gitignore": 1,
        "app.py": 1,
        "compose.yaml": 1,
    }


@pytest.mark.parametrize(
    ("paths", "field"),
    [
        (["../app.py"], "captured_paths[0]"),
        ([r"src\\app.py"], "captured_paths[0]"),
        (["/tmp/app.py"], "captured_paths[0]"),
        (["app.py", "app.py"], "captured_paths[1]"),
        (["missing.py"], "captured_paths[0]"),
    ],
)
def test_snapshot_hash_selection_rejects_unsafe_duplicate_or_missing_paths(
    tmp_path, paths, field
):
    (tmp_path / "app.py").write_text("pass\n", encoding="utf-8")
    snapshot = build_source_snapshot(tmp_path)

    with pytest.raises(SourceSnapshotError) as exc_info:
        snapshot.hashes_for(paths)

    assert exc_info.value.field == field


def test_snapshot_captures_exact_plugin_inventory_path_without_rescanning(
    tmp_path,
):
    plugin_source = tmp_path / "flow.toy"
    plugin_source.write_bytes(b"run\r\n")
    snapshot = build_source_snapshot(tmp_path)
    assert "flow.toy" not in snapshot.captured_content_hashes

    extended = snapshot.with_captured_inventory_paths(["flow.toy"])

    assert extended.hashes_for(["flow.toy"]) == {"flow.toy": sha256_bytes(b"run\r\n")}
    assert extended.captured_input_kinds["flow.toy"] == ("source",)
    assert "flow.toy" in extended.all_source_paths
    assert snapshot.captured_content_hashes == {}


@pytest.mark.parametrize("path", ["../outside.toy", "missing.toy"])
def test_snapshot_rejects_unsafe_or_missing_plugin_inventory_path(
    tmp_path,
    path,
):
    snapshot = build_source_snapshot(tmp_path)

    with pytest.raises(SourceSnapshotError) as exc_info:
        snapshot.with_captured_inventory_paths([path])

    assert exc_info.value.field == "inventory_paths[0]"


def test_records_docker_yaml_and_package_candidates_deterministically(tmp_path):
    (tmp_path / "z.py").write_text("class Z: pass\n")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")
    (tmp_path / "Dockerfile.dev").write_text("FROM alpine\n")
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  web:\n    image: nginx\n"
    )
    (tmp_path / "compose.dev.yaml").write_text(
        "services:\n  worker:\n    image: alpine\n"
    )
    (tmp_path / "infra.yaml").write_text("services:\n  api:\n    image: nginx\n")
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "pyproject.toml").write_text('[project]\nname = "pkg"\n')
    (pkg / "pkg.cabal").write_text("name: pkg\n")
    (tmp_path / "setup.py").write_text(
        'from setuptools import setup\nsetup(name="root")\n'
    )
    (tmp_path / "go.mod").write_text("module example.com/app\n")
    (tmp_path / "package.json").write_text('{"dependencies": {}}\n')
    (tmp_path / "requirements.txt").write_text("requests\n")
    (tmp_path / "requirements-dev.txt").write_text("pytest\n")
    (tmp_path / "cabal.project").write_text("packages: pkg\n")
    (tmp_path / "flake.nix").write_text("{ outputs = _: {}; }\n")
    (tmp_path / "stack.yaml").write_text("packages:\n- .\n")

    snapshot = build_source_snapshot(tmp_path)

    assert [item.rel_path for item in snapshot.dockerfile_candidates] == [
        "Dockerfile",
        "Dockerfile.dev",
    ]
    assert [item.rel_path for item in snapshot.compose_candidates] == [
        "compose.dev.yaml",
        "docker-compose.yml",
    ]
    assert [item.rel_path for item in snapshot.yaml_candidates] == [
        "compose.dev.yaml",
        "docker-compose.yml",
        "infra.yaml",
        "stack.yaml",
    ]
    assert [item.rel_path for item in snapshot.package_markers] == [
        "cabal.project",
        "flake.nix",
        "go.mod",
        "package.json",
        "pkg/pkg.cabal",
        "pkg/pyproject.toml",
        "requirements-dev.txt",
        "requirements.txt",
        "setup.py",
        "stack.yaml",
    ]


def test_package_markers_keep_existing_gitignore_semantics(tmp_path):
    (tmp_path / ".gitignore").write_text(
        "pyproject.toml\nignored.py\nignored.cabal\ngo.mod\n"
    )
    (tmp_path / "go.mod").write_text("module example.com/ignored\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ignored-marker"\n')
    (tmp_path / "ignored.cabal").write_text("name: ignored\n")
    (tmp_path / "ignored.py").write_text("class Ignored: pass\n")

    snapshot = build_source_snapshot(tmp_path)

    assert _paths(snapshot, "python") == []
    assert [item.rel_path for item in snapshot.package_markers] == [
        "go.mod",
        "ignored.cabal",
        "pyproject.toml",
    ]


def test_haskell_package_markers_skip_excluded_and_generated_worktree_dirs(tmp_path):
    (tmp_path / "app.cabal").write_text("name: app\n")
    for dirname, filename in (
        ("dist", "dist.cabal"),
        ("dist", "go.mod"),
        ("node_modules/pkg", "go.mod"),
        ("node_modules/pkg", "package.json"),
        ("node_modules/pkg", "pkg.cabal"),
        ("projects/sample", "go.mod"),
        ("projects/sample", "package.json"),
        ("projects/sample", "requirements.txt"),
        (".claude/worktrees/agent/go", "go.mod"),
        (".claude/worktrees/agent/hls", "agent.cabal"),
        (".claude/worktrees/agent/web", "package.json"),
    ):
        target_dir = tmp_path / dirname
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / filename).write_text("name: ignored\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("projects/\n!projects/.gitkeep\n")

    snapshot = build_source_snapshot(tmp_path)

    assert [item.rel_path for item in snapshot.package_markers] == ["app.cabal"]


def test_root_parent_named_excluded_dir_is_allowed(tmp_path):
    env_root = tmp_path / "env" / "project"
    env_root.mkdir(parents=True)
    (env_root / "app.py").write_text("class App: pass\n")

    snapshot = build_source_snapshot(env_root)

    assert _paths(snapshot, "python") == ["app.py"]
