from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from llm_wiki_cli.commands import metrics_cmd
from llm_wiki_cli.services import metrics
from llm_wiki_cli.services.knowledge_observability import (
    KnowledgeAggregateSummary,
)


def _knowledge_summary(**overrides) -> KnowledgeAggregateSummary:
    values = {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "concepts_evaluated": 6,
        "freshness_counts": {
            "basis-incompatible": 0,
            "current": 3,
            "nonsemantic-source-change": 0,
            "source-changed": 0,
            "source-missing": 0,
            "unknown": 3,
        },
        "evidence_issue_counts": {
            "missing": 0,
            "invalid": 0,
            "unknown": 1,
        },
        "degraded_reason": None,
        "phase_durations_ms": {
            "load": 2,
            "evaluate": 3,
            "check": 1,
        },
        "freshness_evaluated": True,
    }
    values.update(overrides)
    return KnowledgeAggregateSummary(**values)


def test_metrics_path_resolves_inside_git_dir():
    assert metrics.metrics_path(".git") == Path(".git") / "llm-wiki-metrics.jsonl"
    assert (
        metrics.metrics_path(Path("repo") / ".git")
        == Path("repo") / ".git" / "llm-wiki-metrics.jsonl"
    )


def test_record_event_appends_jsonl_and_load_events_reads_it(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    metrics.record_event(
        "trigger_start", {"mode": "CLI", "agent": "claude"}, git_dir=git_dir
    )

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


def test_load_events_skips_blank_invalid_and_out_of_window_events(
    tmp_path, monkeypatch
):
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
    assert "knowledge_summary" not in events[0]


def test_record_validation_event_adds_safe_knowledge_summary_from_model(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    summary = _knowledge_summary()

    metrics.record_validation_event(
        command="lint",
        passed=True,
        issue_count=0,
        strict=True,
        duration_ms=9,
        wiki_dir="docs/llm_wiki",
        src_dir=".",
        knowledge_summary=summary,
        git_dir=git_dir,
    )

    event = metrics.load_events(git_dir=git_dir)[0]
    assert event["knowledge_summary"] == summary.to_payload()


def test_validation_summary_mapping_is_allowlisted_and_sanitized(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    payload = _knowledge_summary().to_payload()
    payload.update(
        {
            "locator": "llm-wiki://entities/Secret",
            "source_hash": "sha256:secret",
            "actor": "private@example.test",
            "author_name": "Private User",
            "repository_remote": "ssh://private.example/repo",
            "source_path": "/private/checkout/secret.py",
            "unexpected": {"remote": "private", "kept": "not-allowlisted"},
        }
    )
    payload["freshness_counts"] = {
        **payload["freshness_counts"],
        "locator": 1,
        "source_hash": 1,
    }
    payload["phase_durations_ms"] = {
        **payload["phase_durations_ms"],
        "output_path": "/private/report.json",
    }

    metrics.record_validation_event(
        command="ci-check",
        passed=False,
        issue_count=1,
        strict=True,
        duration_ms=12,
        wiki_dir="docs/llm_wiki",
        src_dir=".",
        knowledge_summary=payload,
        git_dir=git_dir,
    )

    event = metrics.load_events(git_dir=git_dir)[0]
    assert event["knowledge_summary"] == _knowledge_summary().to_payload()
    serialized = json.dumps(event, sort_keys=True)
    for secret in (
        "llm-wiki://entities/Secret",
        "sha256:secret",
        "private@example.test",
        "Private User",
        "ssh://private.example/repo",
        "/private/checkout/secret.py",
        "/private/report.json",
    ):
        assert secret not in serialized


def test_record_event_sanitizes_evidence_and_absolute_path_fields(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    metrics.record_event(
        "validation",
        {
            "src_dir": "/private/checkout",
            "wiki_dir": "docs/llm_wiki",
            "details": {
                "concept_locator": "llm-wiki://entities/Secret",
                "observation_hash": "sha256:secret",
                "actor_id": "private@example.test",
                "author": "Private User",
                "git_remote": "ssh://private.example/repo",
                "output_path": r"C:\private\report.json",
                "relative_path": "docs/llm_wiki/index.md",
            },
        },
        git_dir=git_dir,
    )

    event = metrics.load_events(git_dir=git_dir)[0]
    assert event["src_dir"] == metrics.REDACTED_ABSOLUTE_PATH
    assert event["wiki_dir"] == "docs/llm_wiki"
    assert event["details"] == {
        "output_path": metrics.REDACTED_ABSOLUTE_PATH,
        "relative_path": "docs/llm_wiki/index.md",
    }


def test_metrics_recording_is_best_effort_for_type_and_serialization_failures(
    tmp_path,
):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    metrics.record_event(
        "bad-payload",
        {"not_json": object()},
        git_dir=git_dir,
    )
    metrics.record_validation_event(
        command="lint",
        passed=True,
        issue_count=0,
        strict=True,
        duration_ms=None,
        wiki_dir="wiki",
        src_dir=".",
        knowledge_summary=object(),
        git_dir=git_dir,
    )

    events = metrics.load_events(git_dir=git_dir)
    assert [event["event"] for event in events] == ["validation"]
    assert "knowledge_summary" not in events[0]


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
    assert "knowledge_summary" not in summary


def test_summarize_events_uses_latest_safe_knowledge_summary(monkeypatch):
    monkeypatch.setattr(
        metrics,
        "current_coverage",
        lambda src_dir, wiki_dir: {
            "percent": 100.0,
            "entities": {"documented": 0, "total": 0},
            "modules": {"documented": 0, "total": 0},
        },
    )
    old = _knowledge_summary(
        availability="degraded",
        reason="policy-selected-surface-only-fallback-after-invalid",
        concepts_evaluated=0,
        freshness_counts=None,
        evidence_issue_counts=None,
        degraded_reason="policy-selected-surface-only-fallback-after-invalid",
        freshness_evaluated=False,
    ).to_payload()
    latest = _knowledge_summary().to_payload()

    summary = metrics.summarize_events(
        [
            {
                "event": "validation",
                "strict": True,
                "passed": False,
                "knowledge_summary": old,
            },
            {
                "event": "validation",
                "strict": True,
                "passed": True,
                "knowledge_summary": latest,
            },
            {
                "event": "validation",
                "strict": False,
                "passed": True,
                "knowledge_summary": {"availability": object()},
            },
        ],
        src_dir="src",
        wiki_dir="wiki",
    )

    assert summary["knowledge_summary"] == latest


def test_summarize_events_rejects_unclosed_knowledge_reason_values(monkeypatch):
    monkeypatch.setattr(
        metrics,
        "current_coverage",
        lambda src_dir, wiki_dir: {
            "percent": 100.0,
            "entities": {"documented": 0, "total": 0},
            "modules": {"documented": 0, "total": 0},
        },
    )
    safe = _knowledge_summary().to_payload()
    unsafe_reason = {
        **safe,
        "reason": "ssh://private.example/repository",
    }
    unsafe_degraded_reason = {
        **safe,
        "availability": "degraded",
        "reason": "policy-selected-surface-only-fallback-after-invalid",
        "degraded_reason": "actor:private@example.test",
    }

    summary = metrics.summarize_events(
        [
            {"event": "validation", "knowledge_summary": safe},
            {"event": "validation", "knowledge_summary": unsafe_reason},
            {"event": "validation", "knowledge_summary": unsafe_degraded_reason},
        ],
        src_dir="src",
        wiki_dir="wiki",
    )

    assert summary["knowledge_summary"] == safe
    serialized = json.dumps(summary, sort_keys=True)
    assert "ssh://private.example/repository" not in serialized
    assert "private@example.test" not in serialized


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "freshness_evaluated": True,
            "freshness_counts": None,
        },
        {
            "freshness_counts": {"current": 6},
        },
        {
            "concepts_evaluated": 5,
        },
        {
            "availability": "degraded",
            "reason": "policy-selected-surface-only-fallback-after-invalid",
            "degraded_reason": "policy-selected-surface-only-fallback-after-invalid",
            "evidence_issue_counts": None,
        },
        {
            "availability": "unsupported",
            "reason": "knowledge-schema-version-unsupported",
            "degraded_reason": "knowledge-schema-version-unsupported",
            "concepts_evaluated": 0,
            "freshness_counts": None,
            "freshness_evaluated": False,
        },
        {
            "freshness_evaluated": 1,
        },
    ],
)
def test_summarize_events_rejects_semantically_invalid_legacy_summary(
    monkeypatch,
    overrides,
):
    monkeypatch.setattr(
        metrics,
        "current_coverage",
        lambda src_dir, wiki_dir: {
            "percent": 100.0,
            "entities": {"documented": 0, "total": 0},
            "modules": {"documented": 0, "total": 0},
        },
    )
    safe = _knowledge_summary().to_payload()
    malformed = {**safe, **overrides}

    summary = metrics.summarize_events(
        [
            {"event": "validation", "knowledge_summary": safe},
            {"event": "validation", "knowledge_summary": malformed},
        ],
        src_dir="src",
        wiki_dir="wiki",
    )

    assert summary["knowledge_summary"] == safe


def test_metrics_text_adds_optional_knowledge_summary(monkeypatch):
    monkeypatch.setattr(
        metrics,
        "current_coverage",
        lambda src_dir, wiki_dir: {
            "percent": 100.0,
            "entities": {"documented": 0, "total": 0},
            "modules": {"documented": 0, "total": 0},
        },
    )
    base = metrics.summarize_events([], src_dir="src", wiki_dir="wiki")
    without_knowledge = metrics_cmd.render_text(base, "30d")
    assert "Knowledge:" not in without_knowledge

    base["knowledge_summary"] = _knowledge_summary().to_payload()
    rendered = metrics_cmd.render_text(base, "30d")

    assert "Knowledge:" in rendered
    assert "Availability: ready (all-projection-commitments-match)" in rendered
    assert "Concepts evaluated: 6" in rendered
    assert "Freshness: evaluated (6 concepts)" in rendered
    assert "current=3" in rendered
    assert "load=2.0 ms, evaluate=3.0 ms, check=1.0 ms" in rendered


def test_record_event_discards_payload_when_sanitization_fails(
    tmp_path, monkeypatch
):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    def fail_sanitization(*args, **kwargs):
        raise RuntimeError("sanitizer failed")

    monkeypatch.setattr(metrics, "_sanitize_metrics_value", fail_sanitization)
    metrics.record_event("safe-fallback", {"secret": "value"}, git_dir=git_dir)

    event = json.loads(
        metrics.metrics_path(git_dir).read_text(encoding="utf-8")
    )
    assert event["event"] == "safe-fallback"
    assert "secret" not in event


def test_load_events_skips_unsanitizable_and_non_object_values(
    tmp_path, monkeypatch
):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    path = metrics.metrics_path(git_dir)
    path.write_text('{"event": "legacy"}\n', encoding="utf-8")

    def fail_sanitization(*args, **kwargs):
        raise RuntimeError("unsafe legacy value")

    monkeypatch.setattr(metrics, "_sanitize_metrics_value", fail_sanitization)
    assert metrics.load_events(git_dir=git_dir) == []

    monkeypatch.undo()
    path.write_text("[]\n", encoding="utf-8")
    assert metrics.load_events(git_dir=git_dir) == []


def test_metrics_sanitizer_handles_nested_path_lists():
    assert metrics._sanitize_metrics_value(
        {"source_paths": ["/private/source.py", "src/public.py"]}
    ) == {
        "source_paths": [
            metrics.REDACTED_ABSOLUTE_PATH,
            "src/public.py",
        ]
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("/private/source.py", True),
        (r"C:\private\source.py", True),
        ("C:/private/source.py", True),
        (r"\\server\share\source.py", True),
        (r"\private\source.py", True),
        ("src/public.py", False),
        (r"C:relative\source.py", False),
    ],
)
def test_metrics_absolute_path_detection_is_host_independent(value, expected):
    assert metrics._is_absolute_path(value) is expected


def test_metrics_sanitizer_redacts_portable_absolute_paths_in_nested_values():
    assert metrics._sanitize_metrics_value(
        {
            "source_paths": [
                "/private/source.py",
                r"C:\private\source.py",
                r"\\server\share\source.py",
                r"\private\source.py",
                "src/public.py",
            ],
            "nested": {
                "output_dir": "C:/private/output",
                "relative_path": "docs/llm_wiki/index.md",
            },
        }
    ) == {
        "source_paths": [
            metrics.REDACTED_ABSOLUTE_PATH,
            metrics.REDACTED_ABSOLUTE_PATH,
            metrics.REDACTED_ABSOLUTE_PATH,
            metrics.REDACTED_ABSOLUTE_PATH,
            "src/public.py",
        ],
        "nested": {
            "output_dir": metrics.REDACTED_ABSOLUTE_PATH,
            "relative_path": "docs/llm_wiki/index.md",
        },
    }


@pytest.mark.parametrize(
    ("value", "allowed", "expected"),
    [
        ("invalid", {"current"}, None),
        ({}, {"current"}, None),
        ({"current": -1}, {"current"}, None),
        ({"current": 2}, {"current"}, {"current": 2}),
    ],
)
def test_safe_count_mapping_rejects_invalid_shapes(value, allowed, expected):
    assert metrics._safe_count_mapping(value, allowed_keys=allowed) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("invalid", None),
        ({"load": 1}, None),
        ({"load": 1, "evaluate": -1, "check": None}, None),
        ({"load": 1, "evaluate": None, "check": 2}, {
            "load": 1,
            "evaluate": None,
            "check": 2,
        }),
    ],
)
def test_safe_phase_durations_rejects_invalid_shapes(value, expected):
    assert metrics._safe_phase_durations(value) == expected


def test_recent_failures_are_capped_at_five(monkeypatch):
    monkeypatch.setattr(
        metrics,
        "current_coverage",
        lambda src_dir, wiki_dir: {
            "percent": 100.0,
            "entities": {"documented": 0, "total": 0},
            "modules": {"documented": 0, "total": 0},
        },
    )
    events = [
        {
            "event": "validation",
            "strict": True,
            "passed": False,
            "sequence": sequence,
        }
        for sequence in range(7)
    ]

    summary = metrics.summarize_events(events)

    assert [event["sequence"] for event in summary["recent_failures"]] == [
        6,
        5,
        4,
        3,
        2,
    ]
