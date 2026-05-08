"""Tests for extractor helper preparation and cache lookup."""
from __future__ import annotations

import json
import subprocess
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import prepare_extractors_cmd
from llm_wiki_cli.services import extractor_helpers
from llm_wiki_cli.services.extractor_helpers import (
    HELPER_CACHE_DIRNAME,
    HELPER_MANIFEST_VERSION,
    HelperPrepareResult,
    get_prepared_binary,
    helper_cache_key,
    prepare_go,
    prepare_rust,
    resolve_helper_cache_root,
)


def test_helper_cache_key_changes_for_sources_platform_and_toolchain(tmp_path, monkeypatch):
    script = tmp_path / "main.go"
    script.write_text("package main\n", encoding="utf-8")
    monkeypatch.setattr(
        extractor_helpers,
        "helper_source_files",
        lambda language: [("main.go", script)],
    )

    base = helper_cache_key("go", toolchain_version="go1", platform_value="linux-x86_64")
    script.write_text("package main\nfunc main(){}\n", encoding="utf-8")
    changed_source = helper_cache_key("go", toolchain_version="go1", platform_value="linux-x86_64")
    changed_platform = helper_cache_key("go", toolchain_version="go1", platform_value="darwin-arm64")
    changed_toolchain = helper_cache_key("go", toolchain_version="go2", platform_value="linux-x86_64")

    assert changed_source != base
    assert changed_platform != base
    assert changed_toolchain != base


def test_helper_cache_root_resolves_git_env_explicit_and_worktree(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    assert resolve_helper_cache_root(repo) == repo / ".git" / HELPER_CACHE_DIRNAME

    env_root = tmp_path / "env"
    assert resolve_helper_cache_root(tmp_path, env={"LLM_WIKI_CACHE_DIR": str(env_root)}) == env_root / HELPER_CACHE_DIRNAME

    explicit = tmp_path / "explicit"
    assert resolve_helper_cache_root(
        tmp_path,
        str(explicit),
        env={"LLM_WIKI_CACHE_DIR": str(env_root)},
    ) == explicit / HELPER_CACHE_DIRNAME

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
    monkeypatch.setattr(extractor_helpers, "helper_source_fingerprint", lambda language: "src")
    (cache_root / "go" / "current.json").write_text(
        json.dumps({
            "version": HELPER_MANIFEST_VERSION,
            "language": "go",
            "platform": "windows-amd64",
            "source_fingerprint": "src",
            "path": str(binary),
        }),
        encoding="utf-8",
    )

    assert get_prepared_binary("go", tmp_path, str(tmp_path / "cache")) == binary
    assert binary.name.endswith(".exe")


def test_prepare_extractors_detects_languages_from_snapshot(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "app.ts").write_text("export class App {}\n", encoding="utf-8")
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    calls = []

    def fake_prepare(language, cache_root):
        calls.append((language, cache_root))
        return HelperPrepareResult(language, "prepared", "ok")

    monkeypatch.setattr(prepare_extractors_cmd, "prepare_helper", fake_prepare)

    prepare_extractors_cmd.run(types.SimpleNamespace(src_dir=".", cache_dir=None, language=None))

    assert [language for language, _cache_root in calls] == ["typescript", "go"]
    assert "typescript: prepared" in capsys.readouterr().out


def test_prepare_extractors_repeated_language_forces_selection(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    calls = []
    monkeypatch.setattr(
        prepare_extractors_cmd,
        "prepare_helper",
        lambda language, cache_root: calls.append(language) or HelperPrepareResult(language, "already_current", "ok"),
    )

    prepare_extractors_cmd.run(types.SimpleNamespace(
        src_dir=".",
        cache_dir=None,
        language=["go", "go", "rust"],
    ))

    assert calls == ["go", "rust"]
    assert "already_current" in capsys.readouterr().out


def test_prepare_extractors_missing_cache_location_exits(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(prepare_extractors_cmd, "resolve_helper_cache_root", lambda *a, **k: None)

    with pytest.raises(SystemExit) as exc:
        prepare_extractors_cmd.run(types.SimpleNamespace(src_dir=".", cache_dir=None, language=["go"]))

    assert exc.value.code == 1
    assert "helper cache directory unavailable" in capsys.readouterr().err


def test_prepare_extractors_failed_helper_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(
        prepare_extractors_cmd,
        "prepare_helper",
        lambda language, cache_root: HelperPrepareResult(language, "failed", "go not found"),
    )

    with pytest.raises(SystemExit) as exc:
        prepare_extractors_cmd.run(types.SimpleNamespace(src_dir=".", cache_dir=None, language=["go"]))

    assert exc.value.code == 1


def test_prepare_go_builds_cached_binary_and_manifest(tmp_path, monkeypatch):
    cache_root = tmp_path / "helpers"
    commands = []
    envs = []

    monkeypatch.delenv("GOCACHE", raising=False)
    monkeypatch.setattr(extractor_helpers, "_resolve_go_executable", lambda: "/usr/bin/go")
    monkeypatch.setattr(extractor_helpers, "_go_version", lambda go: ("go version test", ""))

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        envs.append(kwargs["env"])
        output = Path(cmd[cmd.index("-o") + 1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("binary", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(extractor_helpers.subprocess, "run", fake_run)

    result = prepare_go(cache_root)

    assert result.status == "prepared"
    assert commands[0][:4] == ["/usr/bin/go", "build", "-o", result.path]
    assert envs[0]["GOCACHE"] == str(cache_root / "go-build-cache")
    manifest = json.loads((cache_root / "go" / "current.json").read_text(encoding="utf-8"))
    assert manifest["path"] == result.path
    assert manifest["go_executable"] == "/usr/bin/go"


def test_prepare_go_reports_missing_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(extractor_helpers, "_resolve_go_executable", lambda: None)

    result = prepare_go(tmp_path / "helpers")

    assert result.status == "failed"
    assert result.message == "go not found"


def test_prepare_go_reports_failing_found_executable(tmp_path, monkeypatch):
    monkeypatch.setattr(extractor_helpers, "_resolve_go_executable", lambda: "/snap/bin/go")
    monkeypatch.setattr(
        extractor_helpers,
        "_go_version",
        lambda go: (None, "snap-confine failed"),
    )

    result = prepare_go(tmp_path / "helpers")

    assert result.status == "failed"
    assert "go found at /snap/bin/go but failed to run: snap-confine failed" in result.message
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
        commands.append((cmd, kwargs["env"]))
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

    resolved = extractor_helpers._resolve_go_executable({
        "PATH": str(tmp_path),
    })

    assert resolved == str(fake_go)


def test_prepare_rust_builds_cached_binary_and_manifest(tmp_path, monkeypatch):
    cache_root = tmp_path / "helpers"
    commands = []

    monkeypatch.setattr(extractor_helpers, "command_output", lambda *a, **k: "cargo 1.0")

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        target = Path(cmd[cmd.index("--target-dir") + 1])
        output = target / "release" / extractor_helpers._binary_name("llm-wiki-rust-extractor")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("binary", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(extractor_helpers.subprocess, "run", fake_run)

    result = prepare_rust(cache_root)

    assert result.status == "prepared"
    assert commands[0][:3] == ["cargo", "build", "--release"]
    manifest = json.loads((cache_root / "rust" / "current.json").read_text(encoding="utf-8"))
    assert manifest["path"] == result.path
