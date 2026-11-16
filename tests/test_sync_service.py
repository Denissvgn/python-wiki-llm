"""Sync runs without argparse or exits for the API and embedding engines."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import io
import os
import subprocess
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.engine import Engine, NoProcessHost, SyncError, SyncRequest, SyncRequestError

BILLING = "class Invoice:\n    total: int\n\n\ndef bill(invoice: Invoice) -> int:\n    return invoice.total\n"


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "billing.py").write_text(BILLING, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))
    api.bootstrap_wiki("src", "wiki")
    return tmp_path


def _wiki_digest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((root / "wiki").rglob("*")) if path.is_file()
    }


def _add_refund(root: Path) -> None:
    (root / "src" / "billing.py").write_text(
        BILLING + "\n\nclass Refund:\n    amount: int\n", encoding="utf-8",
    )


def test_api_sync_returns_page_counts_without_console_output(project: Path, capsys) -> None:
    _add_refund(project)
    capsys.readouterr()

    outcome = api.sync_wiki("src", "wiki")
    again = api.sync_wiki("src", "wiki")

    assert outcome.status == "synced" and not outcome.dry_run
    assert outcome.pages["created"] >= 1
    assert again.status == "up-to-date" and again.pages == {}
    assert capsys.readouterr() == ("", "")
    assert outcome.to_dict()["pages"] == dict(outcome.pages)


def test_api_dry_run_reports_the_plan_and_leaves_the_wiki_unchanged(project: Path) -> None:
    _add_refund(project)
    before = _wiki_digest(project)

    outcome = api.sync_wiki("src", "wiki", dry_run=True)

    assert outcome.status == "synced" and outcome.dry_run
    assert outcome.pages["created"] >= 1
    assert _wiki_digest(project) == before


def test_api_maps_unmanaged_wikis_to_workspace_state(project: Path) -> None:
    with pytest.raises(api.WorkspaceStateError, match="no sync manifest"):
        api.sync_wiki("src", "other-wiki")


def test_engine_sync_streams_to_its_host_and_starts_no_process(project: Path, monkeypatch) -> None:
    started: list[object] = []

    def forbidden(args, *rest, **kwargs):
        started.append(args)
        raise AssertionError("no process may start")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    out, err = io.StringIO(), io.StringIO()
    engine = Engine(host=NoProcessHost(stdout=out, stderr=err))
    _add_refund(project)

    outcome = engine.sync(SyncRequest(source_root="src", wiki_root="wiki", plugins=False))

    assert outcome.status == "synced" and started == []
    assert "Sync complete" in out.getvalue() or "CREATE" in out.getvalue()


def test_engine_sync_raises_typed_errors_with_the_reported_reason(project: Path) -> None:
    err = io.StringIO()
    engine = Engine(host=NoProcessHost(stdout=io.StringIO(), stderr=err))

    with pytest.raises(SyncRequestError) as invalid:
        engine.sync(SyncRequest(source_root="src", wiki_root="wiki", openapi_file="a.yaml", clear_openapi_file=True))
    with pytest.raises(SyncError) as unmanaged:
        engine.sync(SyncRequest(source_root="src", wiki_root="other-wiki", plugins=False))

    assert invalid.value.exit_code == 2 and "mutually exclusive" in str(invalid.value)
    assert unmanaged.value.exit_code == 1 and str(unmanaged.value).startswith("Error: no sync manifest")
    assert "mutually exclusive" in err.getvalue() and "no sync manifest" in err.getvalue()
    with pytest.raises(TypeError):
        engine.sync({"wiki_root": "wiki"})  # type: ignore[arg-type]


@pytest.mark.parametrize("source_root", ["missing", "src/billing.py"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_engine_sync_rejects_a_source_root_that_is_not_a_directory(
    project: Path, source_root: str, dry_run: bool,
) -> None:
    before = _wiki_digest(project)
    engine = Engine(host=NoProcessHost(stdout=io.StringIO(), stderr=io.StringIO()))

    with pytest.raises(SyncRequestError) as rejected:
        engine.sync(SyncRequest(source_root=source_root, wiki_root="wiki", dry_run=dry_run))

    assert rejected.value.exit_code == 1
    assert f"--src-dir '{source_root}'" in str(rejected.value)
    assert "not an existing directory" in str(rejected.value)
    assert _wiki_digest(project) == before


def test_cli_sync_rejects_a_missing_source_root_before_touching_pages(
    project: Path, monkeypatch, capsys,
) -> None:
    from llm_wiki_cli import cli

    before = _wiki_digest(project)
    monkeypatch.setattr("sys.argv", ["llm-wiki", "sync", "--src-dir", "missing", "--wiki-dir", "wiki"])
    capsys.readouterr()

    with pytest.raises(SystemExit) as stopped:
        cli.main()

    err = capsys.readouterr().err
    assert stopped.value.code == 1
    assert "--src-dir 'missing'" in err and "not an existing directory" in err
    assert "missing-source confirmation" not in err
    assert _wiki_digest(project) == before


def test_cli_entry_point_still_exits_with_the_command_status(project: Path, capsys) -> None:
    args = argparse.Namespace(src_dir="src", wiki_dir="other-wiki", no_plugins=True)

    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(args)

    assert stopped.value.code == 1 and isinstance(stopped.value, sync_cmd.SyncAborted)
    assert "no sync manifest" in capsys.readouterr().err


def test_request_translation_keeps_cli_defaults() -> None:
    args = argparse.Namespace(src_dir="src", wiki_dir="wiki", no_cache=True, jobs=4, requested_jobs="auto")

    request = sync_cmd.sync_request_from_args(args)

    assert (request.plugins, request.cache, request.preserve_semantic) == (True, False, True)
    assert (request.jobs, request.requested_jobs) == (4, "auto")
    assert sync_cmd.sync_request_from_args(argparse.Namespace()) == SyncRequest()


@pytest.mark.parametrize("extra", [{}, {"helper_cache_dir": "cache", "source_selection": "profile.json"}])
def test_upgrade_seeds_with_the_request_its_parser_call_used_to_build(extra) -> None:
    from llm_wiki_cli.cli_declarations import _build_parser
    from llm_wiki_cli.commands.upgrade_cmd import _legacy_seed_sync_request
    from llm_wiki_cli.services.current_contracts import CURRENT_KNOWLEDGE_FORMAT

    arguments = ["sync", "--src-dir", "src", "--wiki-dir", "wiki", "--force", "--no-plugins",
                 "--knowledge-format", CURRENT_KNOWLEDGE_FORMAT]
    if "source_selection" in extra:
        arguments.extend(["--source-selection", extra["source_selection"]])
    if "helper_cache_dir" in extra:
        arguments.extend(["--helper-cache-dir", extra["helper_cache_dir"]])

    parsed = sync_cmd.sync_request_from_args(_build_parser().parse_args(arguments))
    seeded = _legacy_seed_sync_request("src", "wiki", **extra)

    # The parser spells the default job request out; the request leaves it implied.
    assert sync_cmd._job_request(seeded) == sync_cmd._job_request(parsed)
    assert seeded == dataclasses.replace(parsed, requested_jobs=None)
