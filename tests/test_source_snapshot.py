"""Tests for shared source-tree discovery snapshots."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from llm_wiki_cli.extractors.common import (
    discover_source_files,
    filter_bundled_inventory,
    filter_bundled_source_inventory,
    is_bundled_helper_implementation_path,
)
from llm_wiki_cli.services.knowledge_envelope import ConsumedInputKind
from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.source_snapshot import (
    SourceSnapshotError,
    build_source_snapshot,
    unsupported_source_summary,
)


def _paths(snapshot, language: str) -> list[str]:
    return snapshot.language_paths(language)


_BUNDLED_HELPER_IMPLEMENTATIONS = (
    "extractors/ts_scripts/extract.js",
    "extractors/go_scripts/main.go",
    "extractors/rust_scripts/src/main.rs",
    "extractors/haskell_scripts/Inventory.hs",
    "extractors/haskell_scripts/Json.hs",
    "extractors/haskell_scripts/Main.hs",
    "extractors/haskell_scripts/Parser.hs",
    "extractors/haskell_scripts/Paths.hs",
)
_BUNDLED_HELPER_MARKERS = (
    "extractors/go_scripts/go.mod",
    "extractors/rust_scripts/Cargo.lock",
    "extractors/rust_scripts/Cargo.toml",
    "extractors/ts_scripts/package-lock.json",
    "extractors/ts_scripts/package.json",
)
_BUNDLED_HELPER_SELECTION_INPUTS = (
    "extractors/rust_scripts/.gitignore",
    "extractors/ts_scripts/.gitignore",
)


def _write_file(root: Path, rel_path: str, content: str = "fixture\n") -> Path:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_owned_llm_wiki_package(root: Path, prefix: str = "src") -> Path:
    package_root = root / prefix / "llm_wiki_cli"
    for rel_path in (
        "__init__.py",
        "cli.py",
        "extractors/__init__.py",
        "extractors/common.py",
        "extractors/go_extractor.py",
        "extractors/haskell_extractor.py",
        "extractors/rust_extractor.py",
        "extractors/ts_extractor.py",
    ):
        _write_file(package_root, rel_path, "# package source\n")
    for rel_path in _BUNDLED_HELPER_IMPLEMENTATIONS:
        _write_file(package_root, rel_path)
    for rel_path in _BUNDLED_HELPER_MARKERS:
        _write_file(package_root, rel_path)
    _write_file(
        package_root,
        "extractors/ts_scripts/.gitignore",
        "node_modules/\n",
    )
    _write_file(
        package_root,
        "extractors/rust_scripts/.gitignore",
        "target/\n",
    )
    return package_root


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


@pytest.mark.parametrize(
    "layout",
    (
        "editable/src",
        "copied/package",
        "noneditable/lib/python3.13/site-packages",
    ),
)
def test_bundled_helper_classifier_uses_owned_package_identity_across_layouts(
    tmp_path, layout
):
    package_root = _write_owned_llm_wiki_package(tmp_path, layout)

    for rel_path in _BUNDLED_HELPER_IMPLEMENTATIONS:
        assert is_bundled_helper_implementation_path(package_root / rel_path)

    assert not is_bundled_helper_implementation_path(
        package_root / "extractors/go_extractor.py"
    )
    assert not is_bundled_helper_implementation_path(
        package_root / "tools/go_scripts/main.go"
    )


def test_bundled_helper_classifier_normalizes_windows_paths_with_explicit_root():
    package_root = r"C:\wheel\site-packages\llm_wiki_cli"

    for rel_path in _BUNDLED_HELPER_IMPLEMENTATIONS:
        windows_rel_path = rel_path.replace("/", "\\")
        assert is_bundled_helper_implementation_path(
            rf"{package_root}\{windows_rel_path}",
            package_root=package_root,
        )

    assert not is_bundled_helper_implementation_path(
        rf"{package_root}\extractors\go_extractor.py",
        package_root=package_root,
    )
    assert not is_bundled_helper_implementation_path(
        rf"{package_root}\tools\go_scripts\main.go",
        package_root=package_root,
    )


@pytest.mark.parametrize(
    ("package_root", "candidate"),
    (
        (
            r"C:\Wheel\Site-Packages\LLM_WIKI_CLI",
            r"c:/wheel/site-packages/llm_wiki_cli/EXTRACTORS/GO_SCRIPTS/MAIN.GO",
        ),
        (
            r"\\Server\Share\Site-Packages\LLM_WIKI_CLI",
            r"//server/share/site-packages/llm_wiki_cli/extractors/go_scripts/main.go",
        ),
    ),
)
def test_bundled_helper_classifier_casefolds_windows_drive_and_unc_identity(
    package_root, candidate
):
    assert is_bundled_helper_implementation_path(
        candidate,
        package_root=package_root,
    )


def test_bundled_helper_classifier_keeps_posix_identity_case_sensitive():
    package_root = "/opt/site-packages/llm_wiki_cli"

    assert not is_bundled_helper_implementation_path(
        "/opt/site-packages/LLM_WIKI_CLI/extractors/go_scripts/main.go",
        package_root=package_root,
    )


def test_posix_path_literal_backslashes_are_not_reinterpreted_as_separators(
    tmp_path,
):
    literal_component = r"extractors\go_scripts\main.go"
    if len(Path(literal_component).parts) != 1:
        pytest.skip("literal backslash filename is a POSIX-only contract")
    package_root = _write_owned_llm_wiki_package(tmp_path)
    literal_path = _write_file(
        package_root,
        literal_component,
        "package consumer\n",
    )

    assert not is_bundled_helper_implementation_path(literal_path)
    assert is_bundled_helper_implementation_path(
        str(literal_path),
        package_root=package_root,
    )
    assert build_source_snapshot(tmp_path).language_paths("go") == [
        rf"src/llm_wiki_cli/{literal_component}"
    ]


def test_exact_helper_suffix_without_owned_package_sentinels_is_not_bundled(
    tmp_path,
):
    consumer_source = _write_file(
        tmp_path,
        "vendor/llm_wiki_cli/extractors/go_scripts/main.go",
        "package main\n",
    )

    assert not is_bundled_helper_implementation_path(consumer_source)
    snapshot = build_source_snapshot(tmp_path)
    assert snapshot.language_paths("go") == [
        "vendor/llm_wiki_cli/extractors/go_scripts/main.go"
    ]
    assert discover_source_files(str(tmp_path), (".go",), language="go") == [
        "vendor/llm_wiki_cli/extractors/go_scripts/main.go"
    ]


def test_relative_classifier_input_never_uses_ambient_cwd_for_ownership(
    tmp_path, monkeypatch
):
    relative_path = "src/llm_wiki_cli/extractors/go_scripts/main.go"
    owned_root = tmp_path / "owned"
    package_root = _write_owned_llm_wiki_package(owned_root)
    unrelated_root = tmp_path / "unrelated"
    _write_file(unrelated_root, relative_path, "package consumer\n")

    monkeypatch.chdir(owned_root)
    assert not is_bundled_helper_implementation_path(relative_path)
    monkeypatch.chdir(unrelated_root)
    assert not is_bundled_helper_implementation_path(relative_path)

    absolute_helper = package_root / "extractors/go_scripts/main.go"
    assert is_bundled_helper_implementation_path(
        absolute_helper.as_posix(),
        package_root=package_root,
    )


def test_self_like_helper_tree_excludes_only_implementations_from_snapshot(
    tmp_path,
):
    package_root = _write_owned_llm_wiki_package(tmp_path)
    _write_file(
        package_root,
        "extractors/ts_scripts/node_modules/dependency/index.js",
        "export const ignored = true;\n",
    )
    _write_file(
        package_root,
        "extractors/rust_scripts/target/debug/generated.rs",
        "pub fn ignored() {}\n",
    )

    snapshot = build_source_snapshot(tmp_path)
    helper_prefix = "src/llm_wiki_cli/"
    helper_implementations = {
        helper_prefix + path for path in _BUNDLED_HELPER_IMPLEMENTATIONS
    }
    helper_markers = [helper_prefix + path for path in _BUNDLED_HELPER_MARKERS]
    helper_selection = {
        helper_prefix + path for path in _BUNDLED_HELPER_SELECTION_INPUTS
    }

    for language in ("typescript", "go", "rust", "haskell"):
        assert snapshot.language_paths(language) == []
    assert helper_implementations.isdisjoint(snapshot.all_source_paths)
    assert helper_implementations.isdisjoint(snapshot.captured_content_hashes)
    assert [
        marker.rel_path
        for marker in snapshot.package_markers
        if marker.rel_path.startswith(helper_prefix + "extractors/")
    ] == helper_markers
    assert {
        path
        for path, kinds in snapshot.captured_input_kinds.items()
        if kinds == ("selection",)
    } == helper_selection
    assert all(
        snapshot.captured_input_kinds[path] == ("package",)
        for path in helper_markers
    )
    assert "src/llm_wiki_cli/extractors/go_extractor.py" in snapshot.all_source_paths
    assert not any("node_modules" in path for path in snapshot.captured_content_hashes)
    assert not any("/target/" in path for path in snapshot.captured_content_hashes)


def test_self_like_helpers_do_not_hide_obsidian_or_ordinary_language_sources(
    tmp_path,
):
    _write_owned_llm_wiki_package(tmp_path)
    _write_file(
        tmp_path,
        "integrations/obsidian/llm-wiki/main.js",
        "export function activate() {}\n",
    )
    _write_file(
        tmp_path,
        "integrations/obsidian/llm-wiki/src/main.ts",
        "export const plugin = true;\n",
    )
    _write_file(tmp_path, "services/worker/main.go", "package worker\n")
    _write_file(tmp_path, "crates/domain/src/lib.rs", "pub fn domain() {}\n")
    _write_file(tmp_path, "hls-analysis/app/Main.hs", "module Main where\n")

    snapshot = build_source_snapshot(tmp_path)

    assert snapshot.language_paths("typescript") == [
        "integrations/obsidian/llm-wiki/main.js",
        "integrations/obsidian/llm-wiki/src/main.ts",
    ]
    assert snapshot.language_paths("go") == ["services/worker/main.go"]
    assert snapshot.language_paths("rust") == ["crates/domain/src/lib.rs"]
    assert snapshot.language_paths("haskell") == ["hls-analysis/app/Main.hs"]


def test_only_files_cannot_re_admit_bundled_helper_implementations(tmp_path):
    package_root = _write_owned_llm_wiki_package(tmp_path)
    selected = [
        f"src/llm_wiki_cli/{rel_path}"
        for rel_path in _BUNDLED_HELPER_IMPLEMENTATIONS
    ]
    selected.append("integrations/obsidian/llm-wiki/main.js")
    _write_file(
        tmp_path,
        "integrations/obsidian/llm-wiki/main.js",
        "export function activate() {}\n",
    )

    snapshot = build_source_snapshot(tmp_path, only_files=selected)

    assert snapshot.language_paths("typescript") == [
        "integrations/obsidian/llm-wiki/main.js"
    ]
    for language in ("go", "rust", "haskell"):
        assert snapshot.language_paths(language) == []
    assert not any(
        is_bundled_helper_implementation_path(
            tmp_path / path,
            package_root=package_root,
        )
        for path in snapshot.all_source_paths
    )
    assert [
        marker.rel_path
        for marker in snapshot.package_markers
        if "/extractors/" in marker.rel_path
    ] == [f"src/llm_wiki_cli/{path}" for path in _BUNDLED_HELPER_MARKERS]
    assert {
        path
        for path, kinds in snapshot.captured_input_kinds.items()
        if kinds == ("selection",)
    } == {
        f"src/llm_wiki_cli/{path}"
        for path in _BUNDLED_HELPER_SELECTION_INPUTS
    }

    extended = snapshot.with_captured_inventory_paths(selected[:-1])
    assert extended.all_source_paths == snapshot.all_source_paths
    assert extended.captured_content_hashes == snapshot.captured_content_hashes


def test_protected_helper_symlink_to_ordinary_source_never_uses_helper_spelling(
    tmp_path,
):
    _write_owned_llm_wiki_package(tmp_path)
    helper_rel_path = "src/llm_wiki_cli/extractors/go_scripts/main.go"
    helper = tmp_path / helper_rel_path
    ordinary_rel_path = "services/worker/main.go"
    ordinary = _write_file(tmp_path, ordinary_rel_path, "package worker\n")
    helper.unlink()
    try:
        helper.symlink_to(ordinary)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    snapshot = build_source_snapshot(tmp_path)
    helper_only = build_source_snapshot(tmp_path, only_files=[helper_rel_path])
    discovered = discover_source_files(str(tmp_path), (".go",), language="go")
    discovered_helper_only = discover_source_files(
        str(tmp_path),
        (".go",),
        language="go",
        only_files=[helper_rel_path],
    )
    extended = snapshot.with_captured_inventory_paths([helper_rel_path])

    assert snapshot.language_paths("go") == [ordinary_rel_path]
    assert discovered == [ordinary_rel_path]
    assert helper_only.language_paths("go") == []
    assert discovered_helper_only == []
    assert helper_rel_path not in extended.all_source_paths
    assert helper_rel_path not in extended.captured_content_hashes


def test_ordinary_symlink_to_bundled_helper_remains_excluded_everywhere(tmp_path):
    package_root = _write_owned_llm_wiki_package(tmp_path)
    helper = package_root / "extractors/go_scripts/main.go"
    alias_rel_path = "services/worker/main.go"
    alias = tmp_path / alias_rel_path
    alias.parent.mkdir(parents=True)
    try:
        alias.symlink_to(helper)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    snapshot = build_source_snapshot(tmp_path)
    alias_only = build_source_snapshot(tmp_path, only_files=[alias_rel_path])
    discovered = discover_source_files(str(tmp_path), (".go",), language="go")
    discovered_alias_only = discover_source_files(
        str(tmp_path),
        (".go",),
        language="go",
        only_files=[alias_rel_path],
    )
    extended = snapshot.with_captured_inventory_paths([alias_rel_path])

    assert snapshot.language_paths("go") == []
    assert alias_only.language_paths("go") == []
    assert discovered == []
    assert discovered_alias_only == []
    assert alias_rel_path not in extended.all_source_paths
    assert alias_rel_path not in extended.captured_content_hashes


@pytest.mark.parametrize(
    ("language", "extensions", "rel_path"),
    (
        ("typescript", (".js", ".ts"), "extractors/ts_scripts/extract.js"),
        ("go", (".go",), "extractors/go_scripts/main.go"),
        ("rust", (".rs",), "extractors/rust_scripts/src/main.rs"),
        ("haskell", (".hs",), "extractors/haskell_scripts/Main.hs"),
    ),
)
def test_lower_level_discovery_excludes_owned_helpers_even_with_only_files(
    tmp_path, language, extensions, rel_path
):
    _write_owned_llm_wiki_package(tmp_path)
    full_rel_path = f"src/llm_wiki_cli/{rel_path}"

    assert discover_source_files(
        str(tmp_path), extensions, language=language
    ) == []
    assert discover_source_files(
        str(tmp_path),
        extensions,
        language=language,
        only_files=[full_rel_path],
    ) == []


def test_nested_helper_gitignore_content_remains_selection_fingerprint_input(
    tmp_path,
):
    package_root = _write_owned_llm_wiki_package(tmp_path)
    first = build_source_snapshot(tmp_path)
    nested_gitignore = package_root / "extractors/ts_scripts/.gitignore"
    nested_gitignore.write_text("node_modules/\ncoverage/\n", encoding="utf-8")

    second = build_source_snapshot(tmp_path)
    rel_path = "src/llm_wiki_cli/extractors/ts_scripts/.gitignore"

    assert first.captured_input_kinds[rel_path] == ("selection",)
    assert second.captured_input_kinds[rel_path] == ("selection",)
    assert second.gitignore_fingerprint != first.gitignore_fingerprint
    assert (
        second.captured_content_hashes[rel_path]
        != first.captured_content_hashes[rel_path]
    )


def test_helper_implementation_and_package_marker_have_distinct_freshness(
    tmp_path,
):
    package_root = _write_owned_llm_wiki_package(tmp_path)
    implementation = package_root / "extractors/go_scripts/main.go"
    marker = package_root / "extractors/go_scripts/go.mod"
    marker_rel_path = "src/llm_wiki_cli/extractors/go_scripts/go.mod"
    first = build_source_snapshot(tmp_path)

    implementation.write_text("package main\nfunc main() {}\n", encoding="utf-8")
    after_implementation = build_source_snapshot(tmp_path)
    marker.write_text("module example.com/changed\n", encoding="utf-8")
    after_marker = build_source_snapshot(tmp_path)

    assert (
        after_implementation.captured_content_hashes
        == first.captured_content_hashes
    )
    assert after_implementation.gitignore_fingerprint == first.gitignore_fingerprint
    assert after_marker.captured_input_kinds[marker_rel_path] == ("package",)
    assert (
        after_marker.captured_content_hashes[marker_rel_path]
        != after_implementation.captured_content_hashes[marker_rel_path]
    )
    assert after_marker.gitignore_fingerprint == first.gitignore_fingerprint


def test_post_extraction_filter_handles_distinct_package_and_checkout_roots(
    tmp_path,
):
    installed_package = _write_owned_llm_wiki_package(
        tmp_path / "installed", "lib/python3.13/site-packages"
    )
    checkout_package = _write_owned_llm_wiki_package(tmp_path / "checkout")
    running_scripts = installed_package / "extractors/go_scripts"
    scanned_helper = checkout_package / "extractors/go_scripts/main.go"
    running_helper = running_scripts / "main.go"
    ordinary = _write_file(
        tmp_path / "checkout", "services/worker/main.go", "package worker\n"
    )
    unrelated_suffix = _write_file(
        tmp_path / "checkout",
        "vendor/llm_wiki_cli/extractors/go_scripts/main.go",
        "package consumer\n",
    )
    checkout_root = tmp_path / "checkout"
    scanned_relative = scanned_helper.relative_to(checkout_root).as_posix()
    scanned_windows_relative = scanned_relative.replace("/", "\\")
    ordinary_relative = ordinary.relative_to(checkout_root).as_posix()
    unrelated_relative = unrelated_suffix.relative_to(checkout_root).as_posix()
    inventory = {
        scanned_helper.as_posix(): {"classes": [], "functions": []},
        scanned_relative: {"classes": [], "functions": []},
        scanned_windows_relative: {"classes": [], "functions": []},
        running_helper.as_posix(): {"classes": [], "functions": []},
        ordinary_relative: {"classes": [], "functions": []},
        unrelated_relative: {"classes": [], "functions": []},
    }

    filtered = filter_bundled_inventory(
        inventory,
        running_scripts,
        source_root=checkout_root,
    )

    assert scanned_helper.as_posix() not in filtered
    assert scanned_relative not in filtered
    assert scanned_windows_relative not in filtered
    assert running_helper.as_posix() not in filtered
    assert ordinary_relative in filtered
    assert unrelated_relative in filtered


def test_post_filter_explicit_installed_root_is_additive_to_scanned_ownership(
    tmp_path,
):
    installed_package = _write_owned_llm_wiki_package(
        tmp_path / "installed", "lib/python3.13/site-packages"
    )
    checkout_root = tmp_path / "checkout"
    _write_owned_llm_wiki_package(checkout_root)
    bundled = "src/llm_wiki_cli/extractors/go_scripts/main.go"
    unrelated = "vendor/llm_wiki_cli/extractors/go_scripts/main.go"
    _write_file(checkout_root, unrelated, "package consumer\n")
    inventory = {
        bundled: {"classes": [], "functions": []},
        unrelated: {"classes": [], "functions": []},
    }

    filtered = filter_bundled_inventory(
        inventory,
        installed_package / "extractors/go_scripts",
        source_root=checkout_root,
        package_root=installed_package,
    )

    assert list(filtered) == [unrelated]


def test_post_filter_trusts_absolute_scripts_path_with_literal_backslash(
    tmp_path, monkeypatch
):
    literal_backslash = len(Path(r"cache\go_scripts").parts) == 1
    scripts_component = (
        r"cache\go_scripts" if literal_backslash else "cache/go_scripts"
    )
    ordinary_component = (
        r"services\worker" if literal_backslash else "services/worker"
    )
    scripts_dir = tmp_path / scripts_component
    scripts_dir.mkdir(parents=True)
    absolute_helper = _write_file(scripts_dir, "main.go", "package main\n")
    ordinary_dir = tmp_path / ordinary_component
    ordinary_dir.mkdir(parents=True)
    absolute_ordinary = _write_file(
        ordinary_dir,
        "main.go",
        "package worker\n",
    )
    relative_helper = r"cache\go_scripts/main.go"
    monkeypatch.chdir(tmp_path)
    inventory = {
        absolute_helper.as_posix(): {"identity": "absolute"},
        absolute_ordinary.as_posix(): {"identity": "ordinary"},
        relative_helper: {"identity": "relative"},
    }

    filtered = filter_bundled_inventory(inventory, scripts_dir)

    assert filtered == {
        absolute_ordinary.as_posix(): {"identity": "ordinary"},
        "cache/go_scripts/main.go": {"identity": "relative"},
    }
    assert ordinary_component in next(
        key for key, value in filtered.items() if value["identity"] == "ordinary"
    )


def test_final_source_filter_preserves_virtual_nul_key(tmp_path):
    key = "virtual\0record"
    payload = {"language": "custom", "classes": [], "functions": []}
    inventory = {key: payload}

    filtered = filter_bundled_source_inventory(
        inventory,
        source_root=tmp_path,
    )

    assert filtered == inventory
    assert filtered[key] is payload


def test_post_extraction_filter_handles_windows_drive_keys_on_posix(tmp_path):
    running_package = _write_owned_llm_wiki_package(
        tmp_path / "installed", "lib/python3.13/site-packages"
    )
    running_scripts = running_package / "extractors/go_scripts"
    source_root = r"C:\checkout"
    package_root = rf"{source_root}\src\llm_wiki_cli"
    bundled_absolute = rf"{package_root}\extractors\go_scripts\main.go"
    bundled_relative = r"src\llm_wiki_cli\extractors\go_scripts\main.go"
    bundled_with_dot_segments = (
        rf"{package_root}\extractors\go_scripts\..\go_scripts\main.go"
    )
    ordinary = rf"{source_root}\services\worker\main.go"
    unrelated_suffix = (
        rf"{source_root}\vendor\llm_wiki_cli\extractors\go_scripts\main.go"
    )
    inventory = {
        path: {"classes": [], "functions": []}
        for path in (
            bundled_absolute,
            bundled_relative,
            bundled_with_dot_segments,
            ordinary,
            unrelated_suffix,
        )
    }

    filtered = filter_bundled_inventory(
        inventory,
        running_scripts,
        source_root=source_root,
        package_root=package_root,
    )

    assert sorted(filtered) == [
        "C:/checkout/services/worker/main.go",
        "C:/checkout/vendor/llm_wiki_cli/extractors/go_scripts/main.go",
    ]


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
