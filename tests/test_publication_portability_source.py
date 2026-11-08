"""Publication in a fresh foreign consumer with a custom source selection and policy."""

import json
from pathlib import Path, PureWindowsPath
import runpy
import subprocess
import sys

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import publication_cmd


VERIFIER = Path(__file__).parent / "fixtures/sibling-wiki/verify_typescript_consumer.py"
fixture = runpy.run_path(str(VERIFIER))


def test_installed_python_consumer_rollout_without_git_or_helper_cache(tmp_path):
    workspace = tmp_path / "Python verification"
    cache = tmp_path / "unused cache"
    evidence = tmp_path / "verification.json"
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            str(VERIFIER),
            "--language",
            "python",
            "--workspace",
            str(workspace),
            "--helper-cache",
            str(cache),
            "--output",
            str(evidence),
        ],
        cwd=tmp_path,
        check=True,
        timeout=120,
    )
    result = json.loads(evidence.read_bytes())
    assert result["helpers"] == [] and result["relocated_receipt_matches"]
    assert not cache.exists()


def test_unprepared_selected_typescript_preserves_consumer_and_requests_only_its_helper(
    tmp_path,
):
    root = tmp_path / "Consumer"
    fixture["create_consumer"](root, "typescript")
    before = fixture["tree"](root)
    cache = tmp_path / "cold cache"
    receipt = tmp_path / "candidate.json"
    destination = tmp_path / "candidate"
    result = fixture["cli"](
        tmp_path,
        cache,
        "docs",
        "wiki",
        "export",
        "--consumer-root",
        root,
        "--config",
        fixture["CONFIG"],
        "--receipt",
        receipt,
        "--output-dir",
        destination,
        expected=2,
    )
    diagnostic = result.stderr.decode("utf-8")
    assert "typescript helper is not prepared" in diagnostic
    assert "prepare-extractors" in diagnostic and "typescript" in diagnostic
    assert "go helper" not in diagnostic
    assert before == fixture["tree"](root)
    assert not any(p.exists() for p in (cache, receipt, destination))


def test_native_windows_cli_coordinates_preserve_portable_policy_checks(
    tmp_path, monkeypatch, capsys
):
    # Exercise the Windows argument spelling on every platform; JSON remains POSIX.
    root = tmp_path / "Consumer"
    fixture["create_consumer"](root, "python")
    target = root / "Pinned copies/Manual"
    target.mkdir(parents=True)
    (target / "Notes.md").write_bytes(b"# Manual notes\r\n")
    monkeypatch.setattr(publication_cmd, "sep", "\\")
    monkeypatch.chdir(root)
    config = str(PureWindowsPath(fixture["CONFIG"]))
    common = [
        "--config",
        config,
        "--target-dir",
        str(PureWindowsPath("Pinned copies/Manual")),
    ]
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "docs", "impact", *common])
    cli.main()
    assert json.loads(capsys.readouterr().out)["complete"]
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "llm-wiki",
            "docs",
            "wiki",
            "export",
            *common,
            "--output-dir",
            "candidate",
            "--receipt",
            "receipt.json",
        ],
    )
    cli.main()
    assert (root / "candidate/Notes.md").read_bytes() == (
        target / "Notes.md"
    ).read_bytes()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "llm-wiki",
            "docs",
            "wiki",
            "export",
            "--config",
            "..\\" + config,
            "--output-dir",
            "rejected",
            "--receipt",
            "invalid.json",
        ],
    )
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    assert not (root / "rejected").exists()
