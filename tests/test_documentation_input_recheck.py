"""Regression coverage for adopted-input fingerprint rechecks."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from llm_wiki_cli.services import documentation_run as documentation_run_service
from llm_wiki_cli.services.documentation_run import (
    DocumentationRunError,
    prepare_documentation_run,
    verify_documentation_run,
)
from llm_wiki_cli.services.documentation_wiki_input import (
    DocumentationWikiInputError,
    fingerprint_documentation_wiki_input,
)


def _write_nontrivial_input(tmp_path: Path) -> Path:
    wiki = tmp_path / "existing wiki"
    files: dict[str, str | bytes] = {
        "index.md": "# Existing Wiki\n\n[Guide](guides/start.md)\n",
        "guides/start.md": "# Start\n\nOperator guidance.\n",
        "modules/core.md": "# core Module\n\n**Path:** `core.py`\n",
        "custom/notes.md": "# Enriched notes\n\nPrior model context.\n",
        "custom/evidence.bin": b"\x00\xffwiki-evidence\n",
    }
    for relative, content in files.items():
        target = wiki / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
    return wiki


def _prepare(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, object]:
    wiki = _write_nontrivial_input(tmp_path)
    workspace = tmp_path / "documentation workspace"
    monkeypatch.setattr(
        documentation_run_service,
        "_run_wiki_validation_pair",
        lambda *args, **kwargs: True,
    )
    run = prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        input_wiki_root=wiki,
        freshness_policy="allow-unverified",
        site_name="Fingerprint Contract",
    )
    return wiki, workspace, run


def _resume(wiki: Path, workspace: Path):
    return prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        input_wiki_root=wiki,
        freshness_policy="allow-unverified",
        site_name="Fingerprint Contract",
    )


def test_unchanged_multifile_input_passes_verification_and_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki, workspace, run = _prepare(tmp_path, monkeypatch)
    expected = run.baseline["input_wiki"]["input_tree_hash"]

    assert fingerprint_documentation_wiki_input(wiki) == expected
    resumed = _resume(wiki, workspace)
    assert resumed.run_id == run.run_id

    report = verify_documentation_run(workspace, advance=False)
    input_check = next(
        check for check in report.checks if check["check"] == "input_wiki_integrity"
    )
    assert input_check == {
        "check": "input_wiki_integrity",
        "ok": True,
        "expected_tree_hash": expected,
        "actual_tree_hash": expected,
    }


@pytest.mark.parametrize("mutation", ["add", "change", "remove"])
def test_multifile_input_mutations_fail_verification_and_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    wiki, workspace, _run = _prepare(tmp_path, monkeypatch)
    if mutation == "add":
        (wiki / "guides" / "added.md").write_text("# Added\n", encoding="utf-8")
    elif mutation == "change":
        (wiki / "modules" / "core.md").write_text(
            "# core Module\n\nChanged after adoption.\n",
            encoding="utf-8",
        )
    else:
        (wiki / "custom" / "evidence.bin").unlink()

    with pytest.raises(DocumentationRunError, match="Input wiki changed"):
        _resume(wiki, workspace)

    report = verify_documentation_run(workspace, advance=False)
    failed = next(
        check for check in report.checks if check["check"] == "read_only_inputs"
    )
    assert failed["ok"] is False
    assert "adopted input wiki changed" in failed["message"]


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_input_symlink_fails_secure_verification_and_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wiki, workspace, _run = _prepare(tmp_path, monkeypatch)
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")
    link = wiki / "guides" / "redirect.md"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    with pytest.raises(DocumentationRunError, match="safely rechecked"):
        _resume(wiki, workspace)

    report = verify_documentation_run(workspace, advance=False)
    failed = next(
        check for check in report.checks if check["check"] == "read_only_inputs"
    )
    assert failed["ok"] is False
    assert "failed secure inventory" in failed["message"]


@pytest.mark.skipif(os.name != "nt", reason="Windows junction semantics only")
def test_fingerprint_rejects_windows_input_junction(tmp_path: Path) -> None:
    wiki = _write_nontrivial_input(tmp_path)
    outside = tmp_path / "junction-target"
    outside.mkdir()
    junction = wiki / "redirected-directory"
    completed = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(outside)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        pytest.skip(f"junction creation unavailable: {completed.stderr.strip()}")

    with pytest.raises(DocumentationWikiInputError) as exc_info:
        fingerprint_documentation_wiki_input(wiki)

    assert exc_info.value.category == "rejected_input_entries"
