"""Read-only prerequisite diagnosis across provider states and clean setups."""

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli.services import capability_diagnostics as capabilities


@pytest.mark.parametrize(
    "language,suffix",
    [("typescript", ".ts"), ("go", ".go"), ("rust", ".rs"), ("haskell", ".hs")],
)
@pytest.mark.parametrize(
    "state", ["ready", "unprepared", "stale-or-invalid", "missing-toolchain"]
)
def test_provider_matrix(tmp_path, monkeypatch, language, suffix, state):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ("app" + suffix)).write_text("// selected source")
    cache = tmp_path / "helpers"
    if state == "stale-or-invalid":
        cache_root = capabilities.helpers.resolve_helper_cache_root(
            tmp_path, str(cache)
        )
        assert cache_root is not None
        manifest = capabilities.helpers._manifest_path(cache_root, language)
        manifest.parent.mkdir(parents=True)
        manifest.write_text("{}")
    monkeypatch.setattr(
        capabilities.shutil,
        "which",
        lambda name, **kwargs: (
            None if state == "missing-toolchain" else "/tools/" + name
        ),
    )
    monkeypatch.setattr(
        capabilities.helpers,
        "get_prepared_binary",
        lambda *a: tmp_path / "helper" if state == "ready" else None,
    )
    monkeypatch.setattr(
        capabilities.helpers,
        "get_prepared_typescript_root",
        lambda *a: tmp_path / "helper" if state == "ready" else None,
    )
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("doctor executed a process")
    )
    report = capabilities.build_capability_diagnostics(".", helper_cache_dir=str(cache))
    provider = next(p for p in report["providers"] if p["language"] == language)
    assert provider["selected_files"] == 1
    assert provider["status"] == (
        "unprepared" if state == "stale-or-invalid" else state
    )
    if state == "stale-or-invalid":
        assert provider["helper"]["status"] == state
    if state != "ready":
        assert provider["remedy"]["argv"][3] == "prepare-extractors"
        assert language in provider["remedy"]["argv"]
        assert capabilities.helpers.resolve_helper_cache_root(
            tmp_path, provider["remedy"]["argv"][-1]
        ) == Path(report["helper_cache"])
        assert (provider["remedy"]["prerequisite"] is not None) == (
            state == "missing-toolchain"
        )
    else:
        assert provider["remedy"] is None


def test_python_unsupported_plugin_and_unchanged_tree(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("raise AssertionError('must not execute')")
    (tmp_path / "run.sh").write_text("exit 99")
    lock = capabilities.plugins.lock_path(tmp_path)
    lock.parent.mkdir(parents=True)
    lock.write_text("invalid")
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    report = capabilities.build_capability_diagnostics(".")
    assert report["providers"][0]["status"] == "ready"
    assert report["unsupported_inputs"][0]["status"] == "unsupported"
    assert report["plugins"][0]["status"] == "unknown"
    assert before == {
        str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    }


@pytest.mark.parametrize("selected", [False, True])
def test_unsupported_languages_respect_discovery_without_requiring_a_profile(
    tmp_path, monkeypatch, selected
):
    monkeypatch.chdir(tmp_path)
    languages = {
        "java": ".java",
        "csharp": ".cs",
        "cpp": ".cpp",
        "c": ".c",
        "ruby": ".rb",
        "php": ".php",
        "kotlin": ".kt",
    }
    for directory in ("src", "excluded", "ignored", "src/ignored", ".venv"):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
        for suffix in languages.values():
            (tmp_path / directory / ("app" + suffix)).write_text("source\n")
    (tmp_path / ".gitignore").write_text("ignored/\nexcluded/\n")
    if selected:
        config = tmp_path / ".llm-wiki/source-selection.json"
        config.parent.mkdir()
        config.write_text(
            json.dumps(
                {
                    "schema_version": "llm-wiki-source-selection/v1",
                    "include": ["src"],
                    "exclude": [],
                }
            )
        )
    report = capabilities.build_capability_diagnostics(".")
    assert {
        item["language"]: item["paths"] for item in report["unsupported_inputs"]
    } == {language: ["src/app" + suffix] for language, suffix in languages.items()}
    assert all(
        item["status"] == "unsupported" and item["remedy"] is None
        for item in report["unsupported_inputs"]
    )
    assert not report["blocked_languages"]


@pytest.mark.parametrize(
    "language,suffix,tool,variable",
    [
        ("go", ".go", "go", "LLM_WIKI_GO"),
        ("haskell", ".hs", "ghc", "LLM_WIKI_GHC"),
    ],
)
def test_tool_override_uses_the_same_resolution_as_preparation(
    tmp_path, monkeypatch, language, suffix, tool, variable
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ("app" + suffix)).write_text("source\n")
    executable = tmp_path / (tool + (".exe" if os.name == "nt" else ""))
    executable.write_text("must not execute")
    executable.chmod(0o700)
    override = "~/" + os.path.relpath(executable, Path.home())
    monkeypatch.setenv(variable, override)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("tool executed"))
    report = capabilities.build_capability_diagnostics(
        ".", helper_cache_dir=str(tmp_path / "cache")
    )
    provider = next(p for p in report["providers"] if p["language"] == language)
    assert provider["status"] == "unprepared"
    assert Path(provider["tools"][tool]).resolve() == executable
    assert provider["missing_tools"] == []
    assert provider["remedy"]["prerequisite"] is None


@pytest.mark.parametrize(
    "language,suffix",
    [
        ("typescript", ".ts"),
        ("go", ".go"),
        ("rust", ".rs"),
        ("haskell", ".hs"),
    ],
)
def test_unreadable_helper_manifest_still_produces_a_remedy(
    tmp_path, monkeypatch, language, suffix
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ("app" + suffix)).write_text("source\n")
    cache = tmp_path / "cache"
    cache_root = capabilities.helpers.resolve_helper_cache_root(tmp_path, str(cache))
    assert cache_root is not None
    manifest = capabilities.helpers._manifest_path(cache_root, language)
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(b"\xff\xfe")
    report = capabilities.build_capability_doctor(helper_cache_dir=str(cache))
    provider = next(
        p for p in report["capabilities"]["providers"] if p["language"] == language
    )
    assert provider["helper"]["status"] == "stale-or-invalid"
    assert provider["remedy"]["argv"][3] == "prepare-extractors"
    assert report["exit_code"] == 2
    assert manifest.read_bytes() == b"\xff\xfe"


@pytest.mark.parametrize(
    "language,suffix", [("typescript", ".ts"), ("go", ".go"), ("rust", ".rs")]
)
def test_clean_setup_cli_and_executable_remedy_plan(tmp_path, language, suffix):
    (tmp_path / ("app" + suffix)).write_text("// source")
    command = [
        sys.executable,
        "-m",
        "llm_wiki_cli.cli",
        "doctor",
        "--capabilities",
        "--format",
        "json",
        "--helper-cache-dir",
        str(tmp_path / "helpers"),
    ]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    report = json.loads(result.stdout)
    assert result.returncode == 2
    assert report["schema_version"] == "llm-wiki-doctor/v2"
    assert report["health"] is None
    provider = next(
        p for p in report["capabilities"]["providers"] if p["language"] == language
    )
    assert provider["helper"]["status"] == "missing"
    assert "has not been prepared" in provider["status_reason"]
    assert "preparation command" in provider["remedy"]["next_step"]
    remedy = subprocess.run(
        provider["remedy"]["argv"] + ["--plan", "--format", "json"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert remedy.returncode == 0, remedy.stderr
    assert json.loads(remedy.stdout)["languages"] == [language]
    recheck = subprocess.run(
        report["recheck"]["argv"] + ["--format", "json"],
        cwd=report["recheck"]["cwd"],
        capture_output=True,
        text=True,
    )
    assert recheck.returncode == 2
    assert json.loads(recheck.stdout) == report
    rendered = capabilities.render_capability_doctor(report)
    assert provider["status_reason"] in rendered
    assert provider["remedy"]["next_step"] in rendered
    assert "Commands:" in rendered and "Recheck command" in rendered
    assert not (tmp_path / "helpers").exists()


def test_prepared_typescript_needs_node_without_rebuilding_the_helper(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.ts").write_text("export const answer = 42;\n")
    monkeypatch.setattr(
        capabilities.helpers,
        "get_prepared_typescript_root",
        lambda *a: tmp_path / "prepared",
    )
    monkeypatch.setattr(
        capabilities.shutil,
        "which",
        lambda name, **kw: None if name == "node" else "/tools/" + name,
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("tool executed"))
    report = capabilities.build_capability_doctor()
    provider = next(
        p for p in report["capabilities"]["providers"] if p["language"] == "typescript"
    )
    assert provider["status"] == "missing-toolchain"
    assert provider["helper"]["status"] == "current"
    assert provider["remedy"]["argv"] is None
    assert (
        provider["remedy"]["prerequisite"]
        == "Install Node.js or make node available on PATH"
    )
    text = capabilities.render_capability_doctor(report)
    assert "helper is already prepared" in text
    assert "node missing, npm found" in text
    assert "Preparation command" not in text
    assert "Recheck command" in text


def test_recheck_preserves_source_profile_health_options_and_cache(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app_test.go").write_text("package app\n")
    profile = tmp_path / "src/profile.json"
    profile.write_text(
        json.dumps(
            {
                "schema_version": "llm-wiki-source-selection/v1",
                "include": ["app_test.go"],
                "exclude": [],
            }
        )
    )
    report = capabilities.build_capability_doctor(
        "custom-wiki",
        "src",
        helper_cache_dir=str(tmp_path / "helpers"),
        source_selection="profile.json",
        include_tests=["go"],
        strict=True,
    )
    recheck = subprocess.run(
        report["recheck"]["argv"] + ["--format", "json"],
        cwd=report["recheck"]["cwd"],
        capture_output=True,
        text=True,
    )
    assert recheck.returncode == 2, recheck.stderr
    assert json.loads(recheck.stdout) == report


def test_text_preserves_health_details(tmp_path, monkeypatch):
    from llm_wiki_cli.services.doctor_service import (
        build_doctor_report,
        render_doctor_text,
    )

    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("pass\n")
    report = capabilities.build_capability_doctor()
    text = capabilities.render_capability_doctor(report)
    assert render_doctor_text(build_doctor_report()).strip() in text
    assert "Availability:" in text


@pytest.mark.parametrize("platform", ["posix", "nt"])
def test_text_remedy_quoting_and_plugin_failure_details(
    tmp_path, monkeypatch, platform
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.ts").write_text("export const answer = 42;\n")
    cache = tmp_path / "cache with spaces"
    report = capabilities.build_capability_doctor(helper_cache_dir=str(cache))
    argv = next(
        p["remedy"]["argv"]
        for p in report["capabilities"]["providers"]
        if p["selected_files"]
    )
    report["capabilities"]["plugins"] = [
        {
            "id": "broken",
            "status": "invalid",
            "reason": "Missing plugin manifest",
            "remedy": {"argv": argv},
        }
    ]
    argv[-1] = "C:\\cache&' $HOME %TEMP% ! ` ‘left’ ‚low‛"
    monkeypatch.setattr(capabilities, "os", SimpleNamespace(name=platform))
    text = capabilities.render_capability_doctor(report)
    command = next(
        line.split(": ", 1)[1]
        for line in text.splitlines()
        if "Preparation command" in line
    )
    if platform == "nt":
        assert "Preparation command (PowerShell): & '" in text
        assert command.endswith(
            "'--cache-dir' 'C:\\cache&'' $HOME %TEMP% ! ` ‘‘left’’ ‚‚low‛‛'"
        )
    else:
        assert shlex.split(command) == argv
    assert "Missing plugin manifest" in text
    assert "Validation command" in text


@pytest.mark.skipif(os.name != "nt", reason="requires a native Windows PowerShell host")
def test_windows_text_command_preserves_literal_arguments():
    powershell = shutil.which("powershell.exe") or shutil.which("pwsh")
    if powershell is None:
        pytest.skip("PowerShell is unavailable")
    arguments = [
        r"C:\source&cache",
        r"C:\source's workspace",
        r"C:\literal$HOME%TEMP%!`name",
        r"C:\left‘right’low‚high‛",
    ]
    report = {
        "status": "unknown",
        "health": None,
        "health_reason": "Prerequisite inspection only",
        "capabilities": {
            "providers": [],
            "unsupported_inputs": [],
            "plugins": [
                {
                    "id": "echo-arguments",
                    "status": "invalid",
                    "remedy": {
                        "argv": [
                            sys.executable,
                            "-I",
                            "-c",
                            "import json, sys; print(json.dumps(sys.argv[1:]))",
                            *arguments,
                        ]
                    },
                }
            ],
        },
    }
    text = capabilities.render_capability_doctor(report)
    command = next(
        line.split(": ", 1)[1]
        for line in text.splitlines()
        if "Validation command" in line
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert json.loads(result.stdout) == arguments
