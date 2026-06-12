from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from llm_wiki_cli.services import metrics


def test_metrics_path_resolves_inside_git_dir():
    assert metrics.metrics_path(".git") == Path(".git") / "llm-wiki-metrics.jsonl"
    assert metrics.metrics_path(Path("repo") / ".git") == Path("repo") / ".git" / "llm-wiki-metrics.jsonl"


def test_record_event_appends_jsonl_and_load_events_reads_it(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    metrics.record_event("trigger_start", {"mode": "CLI", "agent": "claude"}, git_dir=git_dir)

    path = metrics.metrics_path(git_dir)
    assert path.exists()
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    assert len(raw_lines) == 1

    raw_event = json.loads(raw_lines[0])
    assert raw_event["event"] == "trigger_start"
    assert raw_event["agent"] == "claude"
    assert raw_event["mode"] == "CLI"
    assert raw_event["ts"].endswith("Z")

    assert metrics.load_events(git_dir=git_dir) == [raw_event]


def test_record_event_ignores_missing_git_dir(tmp_path):
    missing_git_dir = tmp_path / ".git"

    metrics.record_event("trigger_start", {"agent": "claude"}, git_dir=missing_git_dir)

    assert not metrics.metrics_path(missing_git_dir).exists()


def test_load_events_returns_empty_when_metrics_file_is_missing(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    assert metrics.load_events(git_dir=git_dir) == []


def test_load_events_skips_blank_invalid_and_out_of_window_events(tmp_path, monkeypatch):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    now = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(metrics, "_utc_now", lambda: now)

    path = metrics.metrics_path(git_dir)
    path.write_text(
        "\n".join(
            [
                "",
                "{not-json}",
                json.dumps({"event": "old", "ts": "2026-06-10T08:59:00Z"}),
                json.dumps({"event": "recent", "ts": "2026-06-12T08:30:00Z"}),
                json.dumps({"event": "missing_ts"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert metrics.load_events(last="1h", git_dir=git_dir) == [
        {"event": "recent", "ts": "2026-06-12T08:30:00Z"},
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        (3, timedelta(days=3)),
        ("7", timedelta(days=7)),
        ("2d", timedelta(days=2)),
        ("6h", timedelta(hours=6)),
        ("15m", timedelta(minutes=15)),
    ],
)
def test_parse_window_accepts_supported_values(value, expected):
    assert metrics.parse_window(value) == expected


@pytest.mark.parametrize("value", ["0", "0d", "-1", "abc"])
def test_parse_window_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        metrics.parse_window(value)


def test_resolve_agent_classifies_cli_ide_and_custom_agents(monkeypatch):
    monkeypatch.setattr(metrics, "read_config", lambda wiki_dir: {"agent": "cursor"})

    assert metrics.resolve_agent("claude") == ("claude", "CLI")
    assert metrics.resolve_agent(None, wiki_dir="wiki") == ("cursor", "IDE")
    assert metrics.resolve_agent("local-agent") == ("local-agent", "CLI")


def test_record_validation_event_writes_structured_validation_payload(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    metrics.record_validation_event(
        command="ci-check",
        passed=False,
        issue_count=2,
        strict=True,
        duration_ms=15,
        wiki_dir="docs/llm_wiki",
        src_dir=".",
        git_dir=git_dir,
    )

    events = metrics.load_events(git_dir=git_dir)
    assert events == [
        {
            "command": "ci-check",
            "duration_ms": 15,
            "event": "validation",
            "issue_count": 2,
            "passed": False,
            "src_dir": ".",
            "strict": True,
            "ts": events[0]["ts"],
            "wiki_dir": "docs/llm_wiki",
        }
    ]


def test_summarize_events_aggregates_validation_sync_and_recent_failures(monkeypatch):
    coverage = {
        "percent": 87.5,
        "entities": {"documented": 7, "total": 8},
        "modules": {"documented": 7, "total": 8},
    }
    monkeypatch.setattr(metrics, "current_coverage", lambda src_dir, wiki_dir: coverage)
    events = [
        {"event": "trigger_start"},
        {"event": "trigger_start"},
        {"event": "trigger_finish", "exit_code": 0, "duration_ms": 100},
        {"event": "trigger_finish", "exit_code": 1, "duration_ms": 200},
        {"event": "validation", "strict": True, "passed": True},
        {"event": "validation", "strict": True, "passed": False},
        {"event": "validation", "strict": False, "passed": False},
    ]

    summary = metrics.summarize_events(events, src_dir="src", wiki_dir="wiki")

    assert summary["accuracy"] == {
        "strict_validation_pass_percent": 50.0,
        "validations": 2,
        "failures": 1,
    }
    assert summary["coverage"] == coverage
    assert summary["speed"] == {
        "average_successful_sync_ms": 100.0,
        "successful_syncs": 1,
    }
    assert summary["totals"] == {
        "sync_attempts": 2,
        "validations": 2,
        "failures": 2,
        "events": 7,
    }
    assert summary["recent_failures"] == [
        {"event": "validation", "strict": False, "passed": False},
        {"event": "validation", "strict": True, "passed": False},
        {"event": "trigger_finish", "exit_code": 1, "duration_ms": 200},
    ]
