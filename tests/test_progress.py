"""Shared phase progress uses bounded stderr events and optional heartbeats."""

from __future__ import annotations

import io
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import bootstrap_cmd
from llm_wiki_cli.services.progress import (
    Progress,
    current_progress,
    observed_phase,
    phase,
    record_counts,
    with_progress,
)


class Clock:
    now = 0.0

    def __call__(self):
        return self.now


class Stream(io.StringIO):
    def __init__(self, tty=False):
        super().__init__()
        self.tty = tty
        self.flushes = 0

    def isatty(self):
        return self.tty

    def flush(self):
        self.flushes += 1


def events(stream):
    return [json.loads(line) for line in stream.getvalue().splitlines()]


@pytest.mark.parametrize(
    "mode,tty,immediate",
    [
        ("always", False, True),
        ("auto", True, True),
        ("auto", False, False),
        ("never", True, False),
    ],
)
def test_modes_phase_order_and_flush(mode, tty, immediate):
    stream = Stream(tty)
    clock = Clock()
    progress = Progress(
        "lint",
        mode=mode,
        output_format="json",
        stream=stream,
        clock=clock,
        start_thread=False,
    )
    with progress.run():
        with phase("knowledge_load"):
            # The same phase in a nested service is not emitted a second time.
            with phase("knowledge_load"):
                clock.now = 0.5
    emitted = events(stream)
    assert [event["event"] for event in emitted] == (
        ["run_started", "phase_started", "phase_finished", "run_finished"]
        if immediate
        else []
    )
    assert stream.flushes == len(emitted)
    assert all(event["elapsed_ms"] >= 0 for event in emitted)
    assert current_progress() is None
    assert progress.durations["knowledge_load"] == 0.5


def test_non_tty_auto_announces_long_phase_and_heartbeats_without_sleep():
    stream, clock = Stream(), Clock()
    progress = Progress(
        "ci-check", output_format="json", stream=stream, clock=clock, start_thread=False
    )
    with progress.run():
        with phase("knowledge_load"):
            clock.now = 9
            progress.tick()
            assert stream.getvalue() == ""
            clock.now = 10
            progress.tick()
            clock.now = 20
            progress.tick()
    emitted = events(stream)
    beats = [event for event in emitted if event["event"] == "heartbeat"]
    assert [event["elapsed_ms"] for event in beats] == [10000, 20000]
    assert all(event["phase"] == "knowledge_load" for event in beats)
    assert emitted[-1]["event"] == "run_finished"
    assert len({event["run_id"] for event in emitted}) == 1


def test_never_has_no_worker_or_events_even_on_failure():
    stream = Stream()
    progress = Progress("sync", mode="never", stream=stream)
    with pytest.raises(ValueError, match="primary failure"):
        with progress.run(), phase("artifact_commit"):
            raise ValueError("primary failure")
    assert progress._thread is None
    assert stream.getvalue() == ""


def test_exception_emits_one_terminal_failure_with_innermost_phase():
    stream = Stream()
    with pytest.raises(ValueError, match="secret must not be copied"):
        with Progress(
            "sync", output_format="json", stream=stream, start_thread=False
        ).run():
            with phase("outer"), phase("typed_graph"):
                raise ValueError("secret must not be copied")
    emitted = events(stream)
    assert [event["event"] for event in emitted] == ["run_started", "run_failed"]
    assert emitted[-1]["phase"] == "typed_graph"
    assert "secret" not in stream.getvalue()


def test_broken_sink_does_not_fail_the_operation():
    class Broken(Stream):
        def write(self, value):
            raise OSError("closed stream")

    with Progress("lint", mode="always", stream=Broken()).run():
        with phase("inventory"):
            result = 42
    assert result == 42


def test_worker_stops_and_worker_start_failure_is_nonfatal(monkeypatch):
    progress = Progress("lint", mode="always", stream=Stream())
    with progress.run():
        assert progress._thread.is_alive()
    assert not progress._thread.is_alive()
    monkeypatch.setattr(
        threading.Thread,
        "start",
        lambda *_: (_ for _ in ()).throw(RuntimeError("thread unavailable")),
    )
    with Progress("lint", mode="always", stream=Stream()).run():
        assert current_progress() is not None


def test_worker_context_and_bounded_counter_payloads():
    stream = Stream()
    progress = Progress(
        "lint", mode="always", output_format="json", stream=stream, start_thread=False
    )
    with progress.run():

        def worker():
            with phase("extractor"):
                assert current_progress() is progress
                record_counts(
                    inventory_files=10, secret_path=123, cache_hits=-1, concepts=2**100
                )

        thread = threading.Thread(target=lambda: with_progress(progress, worker))
        thread.start()
        thread.join()
    assert events(stream)[-1]["counts"] == {"inventory_files": 10}
    assert all(
        len(line.encode("utf-8")) <= 1024
        for line in stream.getvalue().splitlines(keepends=True)
    )
    assert "secret_path" not in stream.getvalue()


@pytest.mark.parametrize("command", ["sync", "lint", "ci-check"])
def test_cli_commands_share_progress_and_keep_result_stdout(
    tmp_path, monkeypatch, capsys, command
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/app.py").write_text("class App:\n    pass\n", encoding="utf-8")
    bootstrap_cmd.run(
        SimpleNamespace(
            src_dir="src",
            wiki_dir="wiki",
            overwrite=False,
            depth="full",
            source_adapter=True,
            skip_workflows=True,
        )
    )
    capsys.readouterr()
    args = [
        "llm-wiki",
        command,
        "--src-dir",
        "src",
        "--wiki-dir",
        "wiki",
        "--no-cache",
        "--progress",
        "always",
        "--progress-format",
        "json",
    ]
    if command == "lint":
        args += ["--strict", "--profile"]
    elif command == "ci-check":
        args += ["--no-report", "--format", "json", "--report-schema", "v2"]
    monkeypatch.setattr("sys.argv", args)
    cli.main()
    captured = capsys.readouterr()
    emitted = [
        json.loads(line) for line in captured.err.splitlines() if line.startswith("{")
    ]
    assert emitted[0]["event"] == "run_started"
    assert emitted[-1]["event"] == "run_finished"
    assert all(event["command"] == command for event in emitted)
    assert "source_snapshot" in {event["phase"] for event in emitted}
    if command == "sync":
        assert "Wiki is up to date" in captured.out
    else:
        assert json.loads(captured.out)["ok"] is True
    assert current_progress() is None


def test_decorated_service_without_command_scope_is_silent(capsys):
    @observed_phase("inventory")
    def operation():
        return 17

    assert operation() == 17
    assert capsys.readouterr().err == ""
