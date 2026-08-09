"""Tests for extractor helper preparation and cache lookup."""

from __future__ import annotations

import json
import os
import subprocess
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import prepare_extractors_cmd
from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.services import extractor_helpers
from llm_wiki_cli.services.extractor_helpers import (
    DEFAULT_EXTRACTOR_TIMEOUT_SECONDS,
    ENV_EXTRACTOR_TIMEOUT,
    HELPER_CACHE_DIRNAME,
    HELPER_MANIFEST_VERSION,
    HelperPrepareResult,
    get_prepared_binary,
    get_prepared_typescript_root,
    helper_artifact_fingerprint,
    helper_cache_key,
    prepare_go,
    prepare_haskell,
    prepare_rust,
    prepare_typescript,
    resolve_helper_cache_root,
)
from llm_wiki_cli.services.source_selection import SourceSelectionError


def _write_fixture(root: Path, rel_path: str, content: str = "fixture\n") -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_self_like_helpers(root: Path) -> None:
    package_prefix = "src/llm_wiki_cli"
    for rel_path in (
        "__init__.py",
        "cli.py",
        "extractors/__init__.py",
        "extractors/common.py",
        "extractors/ts_scripts/extract.js",
        "extractors/go_scripts/main.go",
        "extractors/rust_scripts/src/main.rs",
        "extractors/haskell_scripts/Inventory.hs",
        "extractors/haskell_scripts/Json.hs",
        "extractors/haskell_scripts/Main.hs",
        "extractors/haskell_scripts/Parser.hs",
        "extractors/haskell_scripts/Paths.hs",
    ):
        _write_fixture(root, f"{package_prefix}/{rel_path}")


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        (None, DEFAULT_EXTRACTOR_TIMEOUT_SECONDS),
        ("275", 275),
        ("1", 1),
        ("0", 1),
        ("-40", 1),
        ("not-an-integer", DEFAULT_EXTRACTOR_TIMEOUT_SECONDS),
    ],
)
def test_extractor_timeout_uses_environment_default_and_floor(
    configured, expected, monkeypatch
):
    if configured is None:
        monkeypatch.delenv(ENV_EXTRACTOR_TIMEOUT, raising=False)
    else:
        monkeypatch.setenv(ENV_EXTRACTOR_TIMEOUT, configured)

    assert extractor_helpers.extractor_timeout_seconds() == expected


def test_helper_cache_key_changes_for_sources_platform_and_toolchain(
    tmp_path, monkeypatch
):
    script = tmp_path / "main.go"
    script.write_text("package main\n", encoding="utf-8")
    monkeypatch.setattr(
        extractor_helpers,
        "helper_source_files",
        lambda language: [("main.go", script)],
    )

    base = helper_cache_key(
        "go", toolchain_version="go1", platform_value="linux-x86_64"
    )
    script.write_text("package main\nfunc main(){}\n", encoding="utf-8")
    changed_source = helper_cache_key(
        "go", toolchain_version="go1", platform_value="linux-x86_64"
    )
    changed_platform = helper_cache_key(
        "go", toolchain_version="go1", platform_value="darwin-arm64"
    )
    changed_toolchain = helper_cache_key(
        "go", toolchain_version="go2", platform_value="linux-x86_64"
    )

    assert changed_source != base
    assert changed_platform != base
    assert changed_toolchain != base


def test_haskell_helper_cache_key_changes_for_sources_platform_and_toolchain(
    tmp_path, monkeypatch
):
    script = tmp_path / "Main.hs"
    script.write_text("module Main where\nmain = pure ()\n", encoding="utf-8")
    monkeypatch.setattr(
        extractor_helpers,
        "helper_source_files",
        lambda language: [("Main.hs", script)],
    )

    base = helper_cache_key(
        "haskell", toolchain_version="ghc 9.8.2", platform_value="linux-x86_64"
    )
    script.write_text('module Main where\nmain = putStrLn "ok"\n', encoding="utf-8")
    changed_source = helper_cache_key(
        "haskell", toolchain_version="ghc 9.8.2", platform_value="linux-x86_64"
    )
    changed_platform = helper_cache_key(
        "haskell", toolchain_version="ghc 9.8.2", platform_value="darwin-arm64"
    )
    changed_toolchain = helper_cache_key(
        "haskell", toolchain_version="ghc 9.10.1", platform_value="linux-x86_64"
    )

    assert changed_source != base
    assert changed_platform != base
    assert changed_toolchain != base


def test_helper_cache_root_resolves_git_env_explicit_and_worktree(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    assert resolve_helper_cache_root(repo) == repo / ".git" / HELPER_CACHE_DIRNAME

    env_root = tmp_path / "env"
    assert (
        resolve_helper_cache_root(tmp_path, env={"LLM_WIKI_CACHE_DIR": str(env_root)})
        == env_root / HELPER_CACHE_DIRNAME
    )

    explicit = tmp_path / "explicit"
    assert (
        resolve_helper_cache_root(
            tmp_path,
            str(explicit),
            env={"LLM_WIKI_CACHE_DIR": str(env_root)},
        )
        == explicit / HELPER_CACHE_DIRNAME
    )

    worktree = tmp_path / "worktree"
    worktree.mkdir()
    gitdir = tmp_path / "actual-git"
    gitdir.mkdir()
    (worktree / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
    assert resolve_helper_cache_root(worktree) == gitdir / HELPER_CACHE_DIRNAME


def test_prepared_binary_uses_manifest_and_exe_suffix(tmp_path, monkeypatch):
    cache_root = tmp_path / "cache" / HELPER_CACHE_DIRNAME
    binary = cache_root / "go" / "key" / "llm-wiki-go-extractor.exe"
    binary.parent.mkdir(parents=True)
    binary.write_text("binary", encoding="utf-8")
    (cache_root / "go").mkdir(exist_ok=True)
    monkeypatch.setattr(extractor_helpers, "platform_id", lambda: "windows-amd64")
    monkeypatch.setattr(
        extractor_helpers, "helper_source_fingerprint", lambda language: "src"
    )
    (cache_root / "go" / "current.json").write_text(
        json.dumps(
            {
                "version": HELPER_MANIFEST_VERSION,
                "language": "go",
                "platform": "windows-amd64",
                "source_fingerprint": "src",
                "artifact_fingerprint": helper_artifact_fingerprint(binary),
                "path": str(binary),
            }
        ),
        encoding="utf-8",
    )

    assert get_prepared_binary("go", tmp_path, str(tmp_path / "cache")) == binary
    assert binary.name.endswith(".exe")


def test_haskell_prepared_binary_uses_manifest_and_exe_suffix(tmp_path, monkeypatch):
    cache_root = tmp_path / "cache" / HELPER_CACHE_DIRNAME
    binary = cache_root / "haskell" / "key" / "llm-wiki-haskell-extractor.exe"
    binary.parent.mkdir(parents=True)
    binary.write_text("binary", encoding="utf-8")
    (cache_root / "haskell").mkdir(exist_ok=True)
    monkeypatch.setattr(extractor_helpers, "platform_id", lambda: "windows-amd64")
    monkeypatch.setattr(
        extractor_helpers, "helper_source_fingerprint", lambda language: "src"
    )
    (cache_root / "haskell" / "current.json").write_text(
        json.dumps(
            {
                "version": HELPER_MANIFEST_VERSION,
                "language": "haskell",
                "platform": "windows-amd64",
                "source_fingerprint": "src",
                "artifact_fingerprint": helper_artifact_fingerprint(binary),
                "path": str(binary),
            }
        ),
        encoding="utf-8",
    )

    assert get_prepared_binary("haskell", tmp_path, str(tmp_path / "cache")) == binary
    assert binary.name.endswith(".exe")


def test_haskell_manifest_path_must_point_to_file(tmp_path, monkeypatch):
    cache_root = tmp_path / "cache" / HELPER_CACHE_DIRNAME
    directory_path = cache_root / "haskell" / "key" / "not-a-binary"
    directory_path.mkdir(parents=True)
    monkeypatch.setattr(extractor_helpers, "platform_id", lambda: "linux-x86_64")
    monkeypatch.setattr(
        extractor_helpers, "helper_source_fingerprint", lambda language: "src"
    )
    (cache_root / "haskell" / "current.json").write_text(
        json.dumps(
            {
                "version": HELPER_MANIFEST_VERSION,
                "language": "haskell",
                "platform": "linux-x86_64",
                "source_fingerprint": "src",
                "artifact_fingerprint": helper_artifact_fingerprint(directory_path),
                "path": str(directory_path),
            }
        ),
        encoding="utf-8",
    )

    assert get_prepared_binary("haskell", tmp_path, str(tmp_path / "cache")) is None


def test_typescript_manifest_v1_is_invalidated_instead_of_reused(
    tmp_path, monkeypatch
):
    configured_cache = tmp_path / "cache"
    cache_root = configured_cache / HELPER_CACHE_DIRNAME
    helper_root = cache_root / "typescript" / "legacy"
    dependency = helper_root / "node_modules" / "ts-morph"
    dependency.mkdir(parents=True)
    (helper_root / "extract.js").write_text("// legacy\n", encoding="utf-8")
    (dependency / "package.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(extractor_helpers, "platform_id", lambda: "linux-x86_64")
    monkeypatch.setattr(
        extractor_helpers, "helper_source_fingerprint", lambda _language: "src"
    )
    (cache_root / "typescript" / "current.json").write_text(
        json.dumps(
            {
                "version": 1,
                "language": "typescript",
                "platform": "linux-x86_64",
                "source_fingerprint": "src",
                "path": str(dependency),
                "root": str(helper_root),
            }
        ),
        encoding="utf-8",
    )

    assert get_prepared_typescript_root(
        tmp_path, str(configured_cache)
    ) is None


def test_prepare_extractors_detects_languages_from_snapshot(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "app.ts").write_text("export class App {}\n", encoding="utf-8")
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "lib.rs").write_text("pub fn run() {}\n", encoding="utf-8")
    (tmp_path / "Main.hs").write_text("module Main where\n", encoding="utf-8")
    calls = []

    def fake_prepare(language, cache_root):
        calls.append((language, cache_root))
        return HelperPrepareResult(language, "prepared", "ok")

    monkeypatch.setattr(prepare_extractors_cmd, "prepare_helper", fake_prepare)

    prepare_extractors_cmd.run(
        types.SimpleNamespace(src_dir=".", cache_dir=None, language=None)
    )

    assert [language for language, _cache_root in calls] == [
        "typescript",
        "go",
        "rust",
        "haskell",
    ]
    assert "typescript: prepared" in capsys.readouterr().out


def test_prepare_extractors_json_plan_is_profile_aware_canonical_and_no_write(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    _write_fixture(tmp_path, "selected/Main.hs", "module Main where\n")
    _write_fixture(tmp_path, "selected/lib.rs", "pub fn run() {}\n")
    _write_fixture(tmp_path, "selected/main.go", "package main\n")
    _write_fixture(tmp_path, "selected/client.js", "export const client = {};\n")
    _write_fixture(tmp_path, "outside/ignored.go", "package ignored\n")
    _write_fixture(
        tmp_path,
        ".llm-wiki/source-selection.json",
        json.dumps(
            {
                "schema_version": "llm-wiki-source-selection/v1",
                "include": ["selected"],
                "exclude": [],
            }
        )
        + "\n",
    )
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    monkeypatch.setattr(
        prepare_extractors_cmd,
        "resolve_helper_cache_root",
        lambda *_args, **_kwargs: pytest.fail("plan must not resolve a cache"),
    )
    monkeypatch.setattr(
        prepare_extractors_cmd,
        "prepare_helper",
        lambda *_args, **_kwargs: pytest.fail("plan must not prepare helpers"),
    )

    prepare_extractors_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            cache_dir=None,
            language=None,
            source_selection=None,
            plan=True,
            format="json",
        )
    )

    output = capsys.readouterr().out
    assert output == (
        '{"schema":"llm-wiki-prepare-extractors-plan/v1",'
        '"languages":["typescript","go","rust","haskell"]}\n'
    )
    assert len(output.splitlines()) == 1
    assert json.loads(output) == {
        "schema": prepare_extractors_cmd.PREPARE_EXTRACTORS_PLAN_SCHEMA,
        "languages": prepare_extractors_cmd._languages_from_snapshot("."),
    }
    after = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_prepare_extractors_text_plan_canonicalizes_explicit_languages(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        prepare_extractors_cmd,
        "resolve_helper_cache_root",
        lambda *_args, **_kwargs: pytest.fail("plan must not resolve a cache"),
    )
    monkeypatch.setattr(
        prepare_extractors_cmd,
        "prepare_helper",
        lambda *_args, **_kwargs: pytest.fail("plan must not prepare helpers"),
    )

    prepare_extractors_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            cache_dir=None,
            language=["rust", "typescript", "rust"],
            plan=True,
            format="text",
        )
    )

    assert capsys.readouterr().out == (
        "Extractor helper plan (llm-wiki-prepare-extractors-plan/v1)\n"
        "languages: typescript, rust\n"
    )


def test_prepare_extractors_json_format_requires_plan(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exc:
        prepare_extractors_cmd.run(
            types.SimpleNamespace(
                src_dir=".",
                cache_dir=None,
                language=["go"],
                plan=False,
                format="json",
            )
        )

    assert exc.value.code == 2
    assert "--format is only available with --plan" in capsys.readouterr().err


def test_prepare_extractors_rejects_external_source_without_opt_in(
    tmp_path, monkeypatch
):
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    monkeypatch.chdir(project)

    with pytest.raises(PathValidationError, match="--src-dir"):
        prepare_extractors_cmd.run(
            types.SimpleNamespace(
                src_dir=str(outside),
                cache_dir=str(tmp_path / "helpers"),
                language=["go"],
                allow_external_src=False,
            )
        )


def test_prepare_extractors_accepts_external_source_with_opt_in(
    tmp_path, monkeypatch, capsys
):
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    monkeypatch.chdir(project)
    calls = []

    def fake_prepare(language, cache_root):
        calls.append((language, cache_root))
        return HelperPrepareResult(language, "prepared", "ok")

    monkeypatch.setattr(prepare_extractors_cmd, "prepare_helper", fake_prepare)

    prepare_extractors_cmd.run(
        types.SimpleNamespace(
            src_dir=str(outside),
            cache_dir=str(tmp_path / "helpers"),
            language=["go"],
            allow_external_src=True,
        )
    )

    assert [language for language, _cache_root in calls] == ["go"]
    assert "go: prepared" in capsys.readouterr().out


def test_prepare_extractors_detects_javascript_as_typescript_helper(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "script.js").write_text("export function run() {}\n", encoding="utf-8")
    calls = []

    def fake_prepare(language, cache_root):
        calls.append((language, cache_root))
        return HelperPrepareResult(language, "prepared", "ok")

    monkeypatch.setattr(prepare_extractors_cmd, "prepare_helper", fake_prepare)

    prepare_extractors_cmd.run(
        types.SimpleNamespace(src_dir=".", cache_dir=None, language=None)
    )

    assert [language for language, _cache_root in calls] == ["typescript"]
    assert "typescript: prepared" in capsys.readouterr().out


def test_prepare_extractors_automatic_selection_ignores_self_helpers(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    _write_self_like_helpers(tmp_path)
    _write_fixture(
        tmp_path,
        "integrations/obsidian/llm-wiki/main.js",
        "export function activate() {}\n",
    )
    _write_fixture(
        tmp_path,
        "integrations/obsidian/llm-wiki/src/main.ts",
        "export const plugin = true;\n",
    )
    calls = []

    def fake_prepare(language, cache_root):
        calls.append((language, cache_root))
        return HelperPrepareResult(language, "prepared", "ok")

    monkeypatch.setattr(prepare_extractors_cmd, "prepare_helper", fake_prepare)

    prepare_extractors_cmd.run(
        types.SimpleNamespace(src_dir=".", cache_dir=None, language=None)
    )

    assert [language for language, _cache_root in calls] == ["typescript"]
    output = capsys.readouterr().out
    assert "typescript: prepared" in output
    assert "go: prepared" not in output
    assert "rust: prepared" not in output
    assert "haskell: prepared" not in output


def test_prepare_extractors_repeated_language_forces_selection(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    calls = []
    monkeypatch.setattr(
        prepare_extractors_cmd,
        "prepare_helper",
        lambda language, cache_root: (
            calls.append(language)
            or HelperPrepareResult(language, "already_current", "ok")
        ),
    )

    prepare_extractors_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            cache_dir=None,
            language=[
                "typescript",
                "go",
                "rust",
                "haskell",
                "typescript",
                "go",
                "rust",
                "haskell",
            ],
        )
    )

    assert calls == ["typescript", "go", "rust", "haskell"]
    assert "already_current" in capsys.readouterr().out


@pytest.mark.parametrize(
    "profile_text, expected",
    [
        ("{not-json}\n", "valid bounded JSON"),
        (
            json.dumps(
                {
                    "schema_version": "llm-wiki-source-selection/v1",
                    "include": ["missing"],
                    "exclude": [],
                }
            )
            + "\n",
            "select at least one readable regular file",
        ),
    ],
)
def test_prepare_extractors_explicit_language_still_validates_default_selection(
    tmp_path,
    monkeypatch,
    profile_text,
    expected,
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    profile = tmp_path / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir()
    profile.write_text(profile_text, encoding="utf-8")
    monkeypatch.setattr(
        prepare_extractors_cmd,
        "prepare_helper",
        lambda *_args, **_kwargs: pytest.fail(
            "helpers must not be prepared before selection validation"
        ),
    )

    with pytest.raises(SourceSelectionError, match=expected):
        prepare_extractors_cmd.run(
            types.SimpleNamespace(src_dir=".", cache_dir=None, language=["go"])
        )


def test_prepare_extractors_missing_cache_location_exits(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        prepare_extractors_cmd, "resolve_helper_cache_root", lambda *a, **k: None
    )

    with pytest.raises(SystemExit) as exc:
        prepare_extractors_cmd.run(
            types.SimpleNamespace(src_dir=".", cache_dir=None, language=["go"])
        )

    assert exc.value.code == 1
    assert "helper cache directory unavailable" in capsys.readouterr().err


def test_prepare_extractors_failed_helper_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(
        prepare_extractors_cmd,
        "prepare_helper",
        lambda language, cache_root: HelperPrepareResult(
            language, "failed", "go not found"
        ),
    )

    with pytest.raises(SystemExit) as exc:
        prepare_extractors_cmd.run(
            types.SimpleNamespace(src_dir=".", cache_dir=None, language=["go"])
        )

    assert exc.value.code == 1


def test_prepare_go_builds_cached_binary_and_manifest(tmp_path, monkeypatch):
    cache_root = tmp_path / "helpers"
    calls = []

    for key in list(os.environ):
        if key.upper() == "GOCACHE":
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(
        extractor_helpers, "_resolve_go_executable", lambda: "/usr/bin/go"
    )
    monkeypatch.setattr(
        extractor_helpers, "_go_version", lambda go: ("go version test", "")
    )

    def fake_run(cmd, **kwargs):
        if len(cmd) >= 2 and cmd[1] == "version":
            return subprocess.CompletedProcess(
                cmd, 0, stdout="go version test", stderr=""
            )
        calls.append((cmd, kwargs.get("env", {})))
        output = Path(cmd[cmd.index("-o") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("binary", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(extractor_helpers.subprocess, "run", fake_run)

    result = prepare_go(cache_root)

    assert result.status == "prepared"
    build_cmd, build_env = next(
        (cmd, env) for cmd, env in calls if len(cmd) >= 2 and cmd[1] == "build"
    )
    assert build_cmd[:4] == ["/usr/bin/go", "build", "-o", result.path]
    assert build_env["GOCACHE"] == str(cache_root / "go-build-cache")
    manifest = json.loads(
        (cache_root / "go" / "current.json").read_text(encoding="utf-8")
    )
    assert manifest["path"] == result.path
    assert manifest["go_executable"] == "/usr/bin/go"
    assert manifest["artifact_fingerprint"] == helper_artifact_fingerprint(
        Path(result.path)
    )


def test_prepare_typescript_uses_locked_cache_and_detects_artifact_tampering(
    tmp_path, monkeypatch
):
    configured_cache = tmp_path / "cache"
    cache_root = configured_cache / HELPER_CACHE_DIRNAME
    commands = []

    monkeypatch.setattr(
        extractor_helpers.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"node", "npm"} else None,
    )
    monkeypatch.setattr(
        extractor_helpers,
        "command_output",
        lambda cmd, **_kwargs: "v24.18.0" if cmd[0].endswith("node") else "11.16.0",
    )

    def fake_run(cmd, **kwargs):
        commands.append((cmd, kwargs))
        dependency = Path(kwargs["cwd"]) / "node_modules" / "ts-morph"
        dependency.mkdir(parents=True, exist_ok=True)
        (dependency / "package.json").write_text(
            '{"name":"ts-morph","version":"28.0.0"}\n',
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(extractor_helpers.subprocess, "run", fake_run)

    first = prepare_typescript(cache_root)
    second = prepare_typescript(cache_root)

    assert first.status == "prepared"
    assert second.status == "already_current"
    assert len(commands) == 1
    command, kwargs = commands[0]
    assert command == [
        "/usr/bin/npm",
        "ci",
        "--ignore-scripts",
        "--no-audit",
        "--no-fund",
    ]
    helper_root = Path(kwargs["cwd"])
    assert helper_root != extractor_helpers.TS_SCRIPTS_DIR
    assert (helper_root / "extract.js").read_bytes() == (
        extractor_helpers.TS_SCRIPTS_DIR / "extract.js"
    ).read_bytes()
    assert (helper_root / "package-lock.json").is_file()
    assert not (extractor_helpers.TS_SCRIPTS_DIR / "node_modules").exists()
    assert get_prepared_typescript_root(
        tmp_path, str(configured_cache)
    ) == helper_root

    dependency_file = Path(first.path) / "package.json"
    dependency_file.write_text('{"tampered":true}\n', encoding="utf-8")
    third = prepare_typescript(cache_root)

    assert third.status == "prepared"
    assert len(commands) == 2


def test_prepare_go_reports_missing_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(extractor_helpers, "_resolve_go_executable", lambda: None)

    result = prepare_go(tmp_path / "helpers")

    assert result.status == "failed"
    assert result.message == "go not found"


def test_prepare_go_reports_failing_found_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(
        extractor_helpers, "_resolve_go_executable", lambda: "/snap/bin/go"
    )
    monkeypatch.setattr(
        extractor_helpers,
        "_go_version",
        lambda go: (None, "snap-confine failed"),
    )

    result = prepare_go(tmp_path / "helpers")

    assert result.status == "failed"
    assert (
        "go found at /snap/bin/go but failed to run: snap-confine failed"
        in result.message
    )
    assert "LLM_WIKI_GO=/path/to/go" in result.message


def test_prepare_go_uses_llm_wiki_go_override(tmp_path, monkeypatch):
    cache_root = tmp_path / "helpers"
    fake_go = tmp_path / extractor_helpers._binary_name("custom-go")
    fake_go.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_go.chmod(fake_go.stat().st_mode | 0o111)
    version_calls = []
    commands = []

    monkeypatch.setenv("LLM_WIKI_GO", str(fake_go))
    monkeypatch.setenv("GOCACHE", str(tmp_path / "existing-go-cache"))

    def fake_version(go):
        version_calls.append(go)
        return "go version custom", ""

    def fake_run(cmd, **kwargs):
        if len(cmd) >= 2 and cmd[1] == "version":
            return subprocess.CompletedProcess(
                cmd, 0, stdout="go version custom", stderr=""
            )
        commands.append((cmd, kwargs.get("env", {})))
        output = Path(cmd[cmd.index("-o") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("binary", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(extractor_helpers, "_go_version", fake_version)
    monkeypatch.setattr(extractor_helpers.subprocess, "run", fake_run)

    result = prepare_go(cache_root)

    assert result.status == "prepared"
    assert version_calls == [str(fake_go)]
    assert commands[0][0][0] == str(fake_go)
    assert commands[0][1]["GOCACHE"] == str(tmp_path / "existing-go-cache")


def test_resolve_go_executable_uses_path_when_no_override(tmp_path, monkeypatch):
    fake_go = tmp_path / extractor_helpers._binary_name("go")
    fake_go.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_go.chmod(fake_go.stat().st_mode | 0o111)

    resolved = extractor_helpers._resolve_go_executable(
        {
            "PATH": str(tmp_path),
        }
    )

    assert os.path.normcase(os.path.normpath(str(resolved))) == os.path.normcase(
        os.path.normpath(str(fake_go))
    )


def test_resolve_ghc_executable_uses_override_and_path(tmp_path):
    override_ghc = tmp_path / extractor_helpers._binary_name("custom-ghc")
    override_ghc.write_text("#!/bin/sh\n", encoding="utf-8")
    override_ghc.chmod(override_ghc.stat().st_mode | 0o111)
    path_ghc = tmp_path / extractor_helpers._binary_name("ghc")
    path_ghc.write_text("#!/bin/sh\n", encoding="utf-8")
    path_ghc.chmod(path_ghc.stat().st_mode | 0o111)

    resolved_override = extractor_helpers._resolve_ghc_executable(
        {
            "LLM_WIKI_GHC": str(override_ghc),
            "PATH": str(tmp_path),
        }
    )
    resolved_path = extractor_helpers._resolve_ghc_executable({"PATH": str(tmp_path)})

    assert os.path.normcase(
        os.path.normpath(str(resolved_override))
    ) == os.path.normcase(os.path.normpath(str(override_ghc)))
    assert os.path.normcase(os.path.normpath(str(resolved_path))) == os.path.normcase(
        os.path.normpath(str(path_ghc))
    )


def test_prepare_rust_builds_cached_binary_and_manifest(tmp_path, monkeypatch):
    cache_root = tmp_path / "helpers"
    commands = []

    monkeypatch.setattr(
        extractor_helpers, "command_output", lambda *a, **k: "cargo 1.0"
    )

    def fake_run(cmd, **kwargs):
        if "--target-dir" not in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="cargo 1.0", stderr="")
        commands.append(cmd)
        target = Path(cmd[cmd.index("--target-dir") + 1])
        output = (
            target
            / "release"
            / extractor_helpers._binary_name("llm-wiki-rust-extractor")
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("binary", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(extractor_helpers.subprocess, "run", fake_run)

    result = prepare_rust(cache_root)

    assert result.status == "prepared"
    build_cmd = next(cmd for cmd in commands if cmd[:2] == ["cargo", "build"])
    assert build_cmd[:4] == ["cargo", "build", "--locked", "--release"]
    manifest = json.loads(
        (cache_root / "rust" / "current.json").read_text(encoding="utf-8")
    )
    assert manifest["path"] == result.path


def test_prepare_haskell_builds_cached_binary_and_manifest(tmp_path, monkeypatch):
    cache_root = tmp_path / "helpers"
    commands = []

    monkeypatch.setattr(
        extractor_helpers, "_resolve_ghc_executable", lambda: "/usr/bin/ghc"
    )
    monkeypatch.setattr(
        extractor_helpers, "_ghc_version", lambda ghc: ("ghc 9.8.2", "")
    )

    def fake_run(cmd, **kwargs):
        assert cmd[0] == "/usr/bin/ghc"
        assert "cabal" not in cmd
        assert "stack" not in cmd
        commands.append((cmd, kwargs))
        output = Path(cmd[cmd.index("-o") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("binary", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(extractor_helpers.subprocess, "run", fake_run)

    result = prepare_haskell(cache_root)

    assert result.status == "prepared"
    build_cmd, build_kwargs = commands[0]
    assert build_cmd[0] == "/usr/bin/ghc"
    assert "-Wall" in build_cmd
    assert "-Werror" not in build_cmd
    assert build_cmd[build_cmd.index("-package") + 1] == "ghc"
    assert build_cmd[build_cmd.index("-o") + 1] == result.path
    assert build_kwargs["cwd"] == str(extractor_helpers.HASKELL_SCRIPTS_DIR)
    manifest = json.loads(
        (cache_root / "haskell" / "current.json").read_text(encoding="utf-8")
    )
    assert manifest["language"] == "haskell"
    assert manifest["toolchain"] == "ghc 9.8.2"
    assert manifest["ghc_executable"] == "/usr/bin/ghc"
    assert manifest["path"] == result.path


def test_prepare_haskell_accepts_supported_ghc_9_6_policy(tmp_path, monkeypatch):
    cache_root = tmp_path / "helper cache with spaces"
    commands = []

    monkeypatch.setattr(
        extractor_helpers, "_resolve_ghc_executable", lambda: "/usr/bin/ghc"
    )
    monkeypatch.setattr(
        extractor_helpers, "_ghc_version", lambda ghc: ("ghc 9.6.7", "")
    )

    def fake_run(cmd, **kwargs):
        commands.append((cmd, kwargs))
        output = Path(cmd[cmd.index("-o") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("binary", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(extractor_helpers.subprocess, "run", fake_run)

    result = prepare_haskell(cache_root)

    assert result.status == "prepared"
    assert "helper cache with spaces" in str(result.path)
    build_cmd, _kwargs = commands[0]
    assert build_cmd[build_cmd.index("-o") + 1] == result.path


def test_prepare_haskell_rejects_malformed_ghc_version(tmp_path, monkeypatch):
    monkeypatch.setattr(
        extractor_helpers, "_resolve_ghc_executable", lambda: "/usr/bin/ghc"
    )
    monkeypatch.setattr(extractor_helpers, "_ghc_version", lambda ghc: ("ghc dev", ""))

    result = prepare_haskell(tmp_path / "helpers")

    assert result.status == "failed"
    assert "unsupported GHC version output" in result.message
    assert "ghc dev" in result.message


def test_prepare_haskell_rejects_too_old_ghc_version(tmp_path, monkeypatch):
    monkeypatch.setattr(
        extractor_helpers, "_resolve_ghc_executable", lambda: "/usr/bin/ghc"
    )
    monkeypatch.setattr(
        extractor_helpers, "_ghc_version", lambda ghc: ("ghc 9.4.8", "")
    )

    result = prepare_haskell(tmp_path / "helpers")

    assert result.status == "failed"
    assert "requires GHC 9.6.x" in result.message
    assert "ghc 9.4.8" in result.message


def test_ghc_version_timeout_message_names_probe_timeout(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(extractor_helpers.subprocess, "run", fake_run)

    toolchain, error = extractor_helpers._ghc_version("/usr/bin/ghc", timeout=3)

    assert toolchain is None
    assert error == "version probe timed out after 3 s"


def test_prepare_haskell_reuses_current_manifest(tmp_path, monkeypatch):
    cache_root = tmp_path / "helpers"
    commands = []

    monkeypatch.setattr(
        extractor_helpers, "_resolve_ghc_executable", lambda: "/usr/bin/ghc"
    )
    monkeypatch.setattr(
        extractor_helpers, "_ghc_version", lambda ghc: ("ghc 9.8.2", "")
    )

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        output = Path(cmd[cmd.index("-o") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("binary", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(extractor_helpers.subprocess, "run", fake_run)

    first = prepare_haskell(cache_root)
    second = prepare_haskell(cache_root)

    assert first.status == "prepared"
    assert second.status == "already_current"
    assert second.path == first.path
    assert len(commands) == 1


def test_prepare_haskell_reports_missing_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(extractor_helpers, "_resolve_ghc_executable", lambda: None)

    result = prepare_haskell(tmp_path / "helpers")

    assert result.status == "failed"
    assert "ghc not found" in result.message
    assert "LLM_WIKI_GHC=/path/to/ghc" in result.message


def test_prepare_haskell_reports_failing_found_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(
        extractor_helpers, "_resolve_ghc_executable", lambda: "/usr/bin/ghc"
    )
    monkeypatch.setattr(
        extractor_helpers,
        "_ghc_version",
        lambda ghc: (None, "missing libgmp"),
    )

    result = prepare_haskell(tmp_path / "helpers")

    assert result.status == "failed"
    assert (
        "ghc found at /usr/bin/ghc but failed to run: missing libgmp" in result.message
    )
    assert "LLM_WIKI_GHC=/path/to/ghc" in result.message


def test_prepare_haskell_reports_build_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr(
        extractor_helpers, "_resolve_ghc_executable", lambda: "/usr/bin/ghc"
    )
    monkeypatch.setattr(
        extractor_helpers, "_ghc_version", lambda ghc: ("ghc 9.6.7", "")
    )

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(extractor_helpers.subprocess, "run", fake_run)

    result = prepare_haskell(tmp_path / "helpers")

    assert result.status == "failed"
    assert result.message == "ghc build timed out after 180 s"
