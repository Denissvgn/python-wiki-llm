"""Engines report structured events to hosts that ask for them."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.engine import (
    EVENT_KINDS,
    BootstrapRequest,
    Engine,
    EngineEvent,
    LintRequest,
    NoProcessHost,
    SyncError,
    SyncRequest,
)
from llm_wiki_engine.engine_events import current_operation, operation_identity
from llm_wiki_engine.host import MessageStream, discarding_stdout, emit, using_host

BILLING = "class Invoice:\n    total: int\n\n\ndef bill(invoice: Invoice) -> int:\n    return invoice.total\n"


class Recorder:
    def __init__(self) -> None:
        self.events: list[EngineEvent] = []

    def __call__(self, event: EngineEvent) -> None:
        self.events.append(event)

    def kinds(self) -> list[str]:
        return [event.kind for event in self.events]

    def lines(self, stream: str) -> list[str]:
        return [
            event.data["text"] for event in self.events
            if event.kind == "message" and event.data["stream"] == stream
        ]


@pytest.fixture
def source(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "billing.py").write_text(BILLING, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))
    return tmp_path


def _engine(recorder: Recorder) -> tuple[Engine, io.StringIO, io.StringIO]:
    out, err = io.StringIO(), io.StringIO()
    return Engine(host=NoProcessHost(stdout=out, stderr=err, events=recorder)), out, err


def _assert_one_operation(recorder: Recorder, name: str) -> None:
    assert recorder.events, "the operation reported nothing"
    assert {event.operation for event in recorder.events} == {name}
    assert len({event.operation_id for event in recorder.events}) == 1
    assert set(recorder.kinds()) <= EVENT_KINDS
    for event in recorder.events:
        json.dumps(event.to_dict())


def test_sync_reports_its_lifecycle_and_every_line_it_writes(source: Path) -> None:
    api.bootstrap_wiki("src", "wiki")
    (source / "src" / "billing.py").write_text(BILLING + "\n\nclass Refund:\n    amount: int\n", encoding="utf-8")
    recorder = Recorder()
    engine, out, err = _engine(recorder)

    outcome = engine.sync(SyncRequest(source_root="src", wiki_root="wiki", plugins=False))

    _assert_one_operation(recorder, "sync")
    started, *messages, finished = recorder.events
    assert started.kind == "operation.started"
    assert dict(started.data) == {"source_root": "src", "wiki_root": "wiki"}
    assert {event.kind for event in messages} == {"message"}
    assert finished.kind == "operation.finished"
    assert finished.data["result"] == outcome.to_dict()
    assert recorder.lines("stdout") == out.getvalue().splitlines()
    assert recorder.lines("stderr") == err.getvalue().splitlines()
    assert any(line.startswith("  CREATE") for line in recorder.lines("stdout"))


def test_a_stopped_sync_reports_the_failure_and_still_raises(source: Path) -> None:
    api.bootstrap_wiki("src", "wiki")
    recorder = Recorder()
    engine, _, _ = _engine(recorder)

    with pytest.raises(SyncError):
        engine.sync(SyncRequest(source_root="src", wiki_root="other-wiki", plugins=False))

    _assert_one_operation(recorder, "sync")
    failed = recorder.events[-1]
    assert failed.kind == "operation.failed"
    assert failed.data["error"] == "SyncError" and failed.data["exit_code"] == 1
    assert "no sync manifest" in failed.data["message"]
    assert any("no sync manifest" in line for line in recorder.lines("stderr"))
    assert "operation.finished" not in recorder.kinds()


def test_bootstrap_reports_progress_written_to_its_stream(source: Path) -> None:
    recorder = Recorder()
    engine, out, _ = _engine(recorder)

    result = engine.bootstrap(BootstrapRequest(source_root="src", wiki_root="wiki"))

    _assert_one_operation(recorder, "bootstrap")
    assert recorder.kinds()[0] == "operation.started" and recorder.kinds()[-1] == "operation.finished"
    assert recorder.events[-1].data["result"] == result.to_dict()
    assert recorder.lines("stdout") and recorder.lines("stdout") == out.getvalue().splitlines()


def test_lint_reports_its_verdict(source: Path) -> None:
    api.bootstrap_wiki("src", "wiki")
    recorder = Recorder()
    engine, _, _ = _engine(recorder)

    report = engine.lint(LintRequest(source_root="src", wiki_root="wiki", plugins=False))

    _assert_one_operation(recorder, "lint")
    assert recorder.events[-1].data["result"] == {"passed": report.passed, "issue_count": report.issue_count}


def test_engines_keep_their_events_apart(source: Path) -> None:
    api.bootstrap_wiki("src", "wiki")
    first, second = Recorder(), Recorder()

    _engine(first)[0].sync(SyncRequest(source_root="src", wiki_root="wiki", plugins=False))
    _engine(second)[0].sync(SyncRequest(source_root="src", wiki_root="wiki", plugins=False))

    _assert_one_operation(first, "sync")
    _assert_one_operation(second, "sync")
    assert first.events[0].operation_id != second.events[0].operation_id


def test_hosts_without_a_sink_and_calls_report_nothing(source: Path) -> None:
    api.bootstrap_wiki("src", "wiki")
    recorder = Recorder()
    engine, _, _ = _engine(recorder)

    engine.call(api.lint_wiki, "src", "wiki")
    Engine(host=NoProcessHost(stdout=io.StringIO())).sync(SyncRequest(source_root="src", wiki_root="wiki"))

    assert recorder.events == []


def test_lines_outside_an_operation_or_discarded_are_not_reported() -> None:
    recorder = Recorder()
    host = NoProcessHost(stdout=io.StringIO(), stderr=io.StringIO(), events=recorder)

    with using_host(host):
        emit("before any operation")
        with operation_identity("sync", "abc"):
            assert current_operation() is not None
            with discarding_stdout():
                emit("hidden")
            emit("first\nsecond", stream="stderr")
            emit()

    assert [(event.data["stream"], event.data["text"]) for event in recorder.events] == [
        ("stderr", "first"), ("stderr", "second"), ("stdout", ""),
    ]
    assert host.stdout.getvalue() == "before any operation\n\n"  # type: ignore[attr-defined]


def test_message_stream_reports_whole_lines_and_the_rest_on_close() -> None:
    recorder = Recorder()
    out = io.StringIO()

    with using_host(NoProcessHost(stdout=out, events=recorder)), operation_identity("bootstrap", "id"):
        stream = MessageStream()
        stream.write("Scanning")
        stream.write(" src\r\nWriting")
        assert recorder.lines("stdout") == ["Scanning src"]
        stream.close()

    assert recorder.lines("stdout") == ["Scanning src", "Writing"]
    assert out.getvalue() == "Scanning src\r\nWriting"


def test_event_values_are_checked_and_read_only() -> None:
    event = EngineEvent("message", "sync", "id", {"stream": "stdout", "text": "x"})

    with pytest.raises(TypeError):
        event.data["text"] = "y"  # type: ignore[index]
    with pytest.raises(ValueError, match="unknown engine event kind"):
        EngineEvent("progress", "sync", "id")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="events must be a callable"):
        NoProcessHost(events="log.txt")  # type: ignore[arg-type]
    assert event.to_dict() == {
        "schema_version": "llm-wiki-engine-event/v1",
        "kind": "message", "operation": "sync", "operation_id": "id",
        "data": {"stream": "stdout", "text": "x"},
    }
