"""Migrate runs from a typed request for the API and embedding engines."""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.cli_declarations import _build_parser
from llm_wiki_cli.commands import migrate_cmd
from llm_wiki_cli.engine import (
    Engine,
    MigrateError,
    MigrateRequest,
    MigrateRequestError,
    NoProcessHost,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def legacy(tmp_path: Path, monkeypatch) -> Path:
    _write(tmp_path / "api" / "server.py", "class Server:\n    pass\n")
    _write(tmp_path / "worker" / "server.py", "class WorkerServer:\n    pass\n")
    wiki = tmp_path / "docs" / "llm_wiki"
    for subdir in ("entities", "modules", "workflows", "infrastructure"):
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    _write(wiki / "index.md", "# Old Index\n")
    _write(wiki / "log.md", "# Log\n")
    _write(wiki / "modules" / "server.md", "# server\n\n**Path:** `api/server.py`\n\nManual server notes.\n")
    _write(wiki / "modules" / "orphan.md", "# orphan\n\nUnmatched notes.\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))
    return wiki


def _digest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def test_api_migrate_returns_page_totals_without_console_output(legacy: Path, capsys) -> None:
    capsys.readouterr()

    outcome = api.migrate_wiki(".", "docs/llm_wiki")

    assert outcome.status == "migrated" and outcome.complete and not outcome.dry_run
    assert outcome.canonical_pages >= 2
    assert (outcome.archived_pages, outcome.unmatched_pages) == (1, 1)
    assert (legacy / "modules" / "api_server.md").is_file()
    assert capsys.readouterr() == ("", "")
    assert outcome.to_dict()["status"] == "migrated"


def test_api_dry_run_and_chunk_plan_leave_the_wiki_unchanged(legacy: Path) -> None:
    before = _digest(legacy)

    dry = api.migrate_wiki(".", "docs/llm_wiki", dry_run=True)
    planned = api.migrate_wiki(".", "docs/llm_wiki", chunk_size=1, plan_chunks=True)

    assert dry.status == "migrated" and dry.dry_run
    assert planned.status == "planned" and planned.chunk_total and planned.chunk_total > 1
    assert _digest(legacy) == before


def test_chunked_migration_reports_each_chunk(legacy: Path) -> None:
    first = api.migrate_wiki(".", "docs/llm_wiki", chunk_size=1)

    assert first.status == "chunk-applied" and first.chunk == 1
    assert first.page_operations >= 1 and first.chunk_total is not None


def test_api_maps_invalid_options_and_missing_wikis(legacy: Path) -> None:
    with pytest.raises(api.InvalidRequestError, match="require --chunk-size"):
        api.migrate_wiki(".", "docs/llm_wiki", plan_chunks=True)
    with pytest.raises(api.WorkspaceStateError, match="does not exist"):
        api.migrate_wiki(".", "missing-wiki")


def test_engine_migrate_uses_the_host_clock_and_starts_no_process(legacy: Path, monkeypatch) -> None:
    def forbidden(args, *rest, **kwargs):
        raise AssertionError("no process may start")

    class FixedClock(NoProcessHost):
        def now(self) -> datetime:
            return datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    out = io.StringIO()
    engine = Engine(host=FixedClock(stdout=out, stderr=io.StringIO()))

    outcome = engine.migrate(MigrateRequest(wiki_root="docs/llm_wiki", plugins=False))

    assert outcome.status == "migrated"
    assert (legacy / "legacy" / "migrate-20260102030405" / "modules" / "server.md").is_file()
    assert "Migration complete" in out.getvalue()


def test_engine_migrate_raises_typed_errors(legacy: Path) -> None:
    engine = Engine(host=NoProcessHost(stdout=io.StringIO(), stderr=io.StringIO()))

    with pytest.raises(MigrateRequestError) as invalid:
        engine.migrate(MigrateRequest(wiki_root="docs/llm_wiki", chunk=2))
    with pytest.raises(MigrateError) as missing:
        engine.migrate(MigrateRequest(wiki_root="missing-wiki"))
    with pytest.raises(MigrateRequestError):
        engine.migrate(MigrateRequest(source_root="../elsewhere"))

    assert invalid.value.exit_code == 1 and "--chunk-size" in str(invalid.value)
    assert missing.value.exit_code == 1 and str(missing.value).startswith("Error: Directory")
    with pytest.raises(TypeError):
        engine.migrate({"wiki_root": "docs/llm_wiki"})  # type: ignore[arg-type]


def test_cli_migrate_still_exits_with_the_command_status(legacy: Path, capsys) -> None:
    args = _build_parser().parse_args(["migrate", "--wiki-dir", "missing-wiki"])

    with pytest.raises(SystemExit) as stopped:
        migrate_cmd.run(args)

    assert stopped.value.code == 1 and isinstance(stopped.value, migrate_cmd.MigrateAborted)
    assert "does not exist" in capsys.readouterr().err


def test_request_translation_keeps_cli_defaults() -> None:
    parsed = _build_parser().parse_args(["migrate", "--chunk-size", "5", "--chunk", "2", "--dry-run"])

    request = migrate_cmd.migrate_request_from_args(parsed)

    assert (request.chunk_size, request.chunk, request.dry_run, request.plugins) == (5, 2, True, True)
    assert migrate_cmd.migrate_request_from_args(argparse.Namespace()) == MigrateRequest()
