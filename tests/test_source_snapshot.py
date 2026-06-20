"""Tests for shared source-tree discovery snapshots."""

from __future__ import annotations

import inspect

from llm_wiki_cli.services.source_snapshot import build_source_snapshot


def _paths(snapshot, language: str) -> list[str]:
    return snapshot.language_paths(language)


def test_build_source_snapshot_stays_decomposed():
    assert len(inspect.getsource(build_source_snapshot).splitlines()) <= 60


def test_groups_builtin_language_files(tmp_path):
    (tmp_path / "app.py").write_text("class App: pass\n")
    (tmp_path / "ui.ts").write_text("export const x = 1;\n")
    (tmp_path / "view.tsx").write_text("export const View = () => null;\n")
    (tmp_path / "main.go").write_text("package main\n")
    (tmp_path / "lib.rs").write_text("pub fn run() {}\n")

    snapshot = build_source_snapshot(tmp_path)

    assert _paths(snapshot, "python") == ["app.py"]
    assert _paths(snapshot, "typescript") == ["ui.ts", "view.tsx"]
    assert _paths(snapshot, "go") == ["main.go"]
    assert _paths(snapshot, "rust") == ["lib.rs"]
    assert snapshot.all_source_paths == (
        "app.py",
        "lib.rs",
        "main.go",
        "ui.ts",
        "view.tsx",
    )


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
        assert _paths(snapshot, "typescript") == []
        assert _paths(snapshot, "go") == []
    finally:
        outside.unlink(missing_ok=True)


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
    (tmp_path / "setup.py").write_text(
        'from setuptools import setup\nsetup(name="root")\n'
    )

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
    ]
    assert [item.rel_path for item in snapshot.package_markers] == [
        "pkg/pyproject.toml",
        "setup.py",
    ]


def test_package_markers_keep_existing_gitignore_semantics(tmp_path):
    (tmp_path / ".gitignore").write_text("pyproject.toml\nignored.py\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "ignored-marker"\n')
    (tmp_path / "ignored.py").write_text("class Ignored: pass\n")

    snapshot = build_source_snapshot(tmp_path)

    assert _paths(snapshot, "python") == []
    assert [item.rel_path for item in snapshot.package_markers] == ["pyproject.toml"]


def test_root_parent_named_excluded_dir_is_allowed(tmp_path):
    env_root = tmp_path / "env" / "project"
    env_root.mkdir(parents=True)
    (env_root / "app.py").write_text("class App: pass\n")

    snapshot = build_source_snapshot(env_root)

    assert _paths(snapshot, "python") == ["app.py"]
