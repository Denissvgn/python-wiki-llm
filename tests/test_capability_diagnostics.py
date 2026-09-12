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
        lambda name: None if state == "missing-toolchain" else "/tools/" + name,
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
    remedy = subprocess.run(
        provider["remedy"]["argv"] + ["--plan", "--format", "json"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert remedy.returncode == 0, remedy.stderr
    assert json.loads(remedy.stdout)["languages"] == [language]
    assert not (tmp_path / "helpers").exists()


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
