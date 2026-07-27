"""Focused rollback coverage for initial documentation preparation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services import documentation_run as documentation_run_service
from llm_wiki_cli.services.documentation_run import prepare_documentation_run


def _write_legacy_inputs(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    wiki = tmp_path / "existing-wiki"
    wiki.mkdir()
    (wiki / "index.md").write_text("# Existing Wiki\n", encoding="utf-8")
    return source, wiki


def _prepare_cli_argv(
    workspace: Path,
    source: Path,
    wiki: Path,
    *,
    freshness: str,
) -> list[str]:
    return [
        "llm-wiki",
        "docs",
        "prepare",
        "--workspace",
        str(workspace),
        "--baseline",
        "existing-wiki",
        "--src-dir",
        str(source),
        "--input-wiki-dir",
        str(wiki),
        "--wiki-freshness",
        freshness,
        "--site-name",
        "Transaction Pilot",
        "--allow-external-src",
        "--output-format",
        "json",
    ]


@pytest.mark.parametrize("workspace_preexisted", [False, True])
def test_cli_freshness_failure_rolls_back_and_same_root_retry_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    workspace_preexisted: bool,
) -> None:
    source, wiki = _write_legacy_inputs(tmp_path)
    workspace = tmp_path / "standalone-docs"
    initial_workspace_identity: tuple[int, int] | None = None
    if workspace_preexisted:
        workspace.mkdir()
        initial_stat = workspace.stat()
        initial_workspace_identity = (initial_stat.st_dev, initial_stat.st_ino)
    source_before = (source / "app.py").read_bytes()
    wiki_before = (wiki / "index.md").read_bytes()
    monkeypatch.setattr(
        documentation_run_service,
        "_run_wiki_validation_pair",
        lambda *args, **kwargs: True,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        _prepare_cli_argv(
            workspace,
            source,
            wiki,
            freshness="require-current",
        ),
    )
    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 1
    assert "freshness_not_current" in capsys.readouterr().err
    assert workspace.exists() is workspace_preexisted
    if workspace_preexisted:
        assert list(workspace.iterdir()) == []
        after_failure = workspace.stat()
        assert (after_failure.st_dev, after_failure.st_ino) == (
            initial_workspace_identity
        )

    monkeypatch.setattr(
        sys,
        "argv",
        _prepare_cli_argv(
            workspace,
            source,
            wiki,
            freshness="allow-unverified",
        ),
    )
    cli.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["freshness"] == "unverified"
    assert (workspace / ".llm-wiki-docs" / "run.json").is_file()
    assert (source / "app.py").read_bytes() == source_before
    assert (wiki / "index.md").read_bytes() == wiki_before


def test_bootstrap_failure_removes_only_new_lifecycle_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    helper_cache = tmp_path / "helper-cache"
    capture = tmp_path / "capture"
    helper_cache.mkdir()
    capture.mkdir()
    (helper_cache / "keep.txt").write_text("keep helper cache\n", encoding="utf-8")
    (capture / "keep.txt").write_text("keep capture\n", encoding="utf-8")
    workspace = tmp_path / "bootstrap-workspace"

    def fail_after_partial_bootstrap(request):
        wiki = Path(request.wiki_root)
        wiki.mkdir(parents=True, exist_ok=True)
        (wiki / "partial.md").write_text("partial\n", encoding="utf-8")
        raise RuntimeError("injected bootstrap extraction failure")

    monkeypatch.setattr(
        "llm_wiki_cli.commands.bootstrap_cmd.execute_bootstrap",
        fail_after_partial_bootstrap,
    )

    with pytest.raises(RuntimeError, match="injected bootstrap extraction failure"):
        prepare_documentation_run(
            workspace,
            baseline_strategy="bootstrap_source",
            source_root=source,
            helper_cache_root=helper_cache,
            capture_root=capture,
            site_name="Bootstrap Transaction",
        )

    assert not workspace.exists()
    assert (source / "app.py").is_file()
    assert (helper_cache / "keep.txt").read_text(encoding="utf-8") == (
        "keep helper cache\n"
    )
    assert (capture / "keep.txt").read_text(encoding="utf-8") == "keep capture\n"


def test_post_run_gate_exception_rolls_back_and_service_retry_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _source, wiki = _write_legacy_inputs(tmp_path)
    workspace = tmp_path / "gate-workspace"

    def fail_gate(*args, **kwargs):
        assert (workspace / ".llm-wiki-docs" / "run.json").is_file()
        raise RuntimeError("injected baseline gate failure")

    monkeypatch.setattr(
        documentation_run_service,
        "_run_wiki_validation_pair",
        fail_gate,
    )

    with pytest.raises(RuntimeError, match="injected baseline gate failure"):
        prepare_documentation_run(
            workspace,
            baseline_strategy="adopt_existing_wiki",
            input_wiki_root=wiki,
            freshness_policy="allow-unverified",
            site_name="Gate Transaction",
        )

    assert not workspace.exists()

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
        site_name="Gate Transaction",
    )

    assert run.state == "baseline_ready"
    assert (workspace / ".llm-wiki-docs" / "run.json").is_file()


def test_rollback_refuses_unexpected_top_level_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _source, wiki = _write_legacy_inputs(tmp_path)
    workspace = tmp_path / "unexpected-entry-workspace"

    def inject_unexpected_entry(*args, **kwargs):
        (workspace / "operator-note.txt").write_text(
            "must not be deleted\n",
            encoding="utf-8",
        )
        raise RuntimeError("injected gate failure with unexpected entry")

    monkeypatch.setattr(
        documentation_run_service,
        "_run_wiki_validation_pair",
        inject_unexpected_entry,
    )

    with pytest.raises(
        documentation_run_service.DocumentationIntegrityError,
        match="could not be removed safely",
    ):
        prepare_documentation_run(
            workspace,
            baseline_strategy="adopt_existing_wiki",
            input_wiki_root=wiki,
            freshness_policy="allow-unverified",
            site_name="Unexpected Entry Safety",
        )

    assert (workspace / "operator-note.txt").read_text(encoding="utf-8") == (
        "must not be deleted\n"
    )
    assert (workspace / ".llm-wiki-docs" / "run.json").is_file()


def test_rollback_refuses_replaced_workspace_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _source, wiki = _write_legacy_inputs(tmp_path)
    workspace = tmp_path / "replaced-root-workspace"
    held_workspace = tmp_path / "prepared-root-before-swap"

    def replace_workspace_root(*args, **kwargs):
        workspace.replace(held_workspace)
        workspace.mkdir()
        (workspace / "sentinel.txt").write_text(
            "replacement must survive\n",
            encoding="utf-8",
        )
        raise RuntimeError("injected gate failure after root replacement")

    monkeypatch.setattr(
        documentation_run_service,
        "_run_wiki_validation_pair",
        replace_workspace_root,
    )

    with pytest.raises(
        documentation_run_service.DocumentationIntegrityError,
        match="could not be removed safely",
    ):
        prepare_documentation_run(
            workspace,
            baseline_strategy="adopt_existing_wiki",
            input_wiki_root=wiki,
            freshness_policy="allow-unverified",
            site_name="Root Replacement Safety",
        )

    assert (workspace / "sentinel.txt").read_text(encoding="utf-8") == (
        "replacement must survive\n"
    )
    assert (held_workspace / ".llm-wiki-docs" / "run.json").is_file()
