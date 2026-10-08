"""Prospective accounting controls with fixed clocks and independent expectations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING or os.name == "posix":
    from tests.developer_value import cost_recorder
else:
    cost_recorder = None


pytestmark = pytest.mark.skipif(
    os.name != "posix",
    reason="Local cost recorder requires native POSIX locking, Unix sockets and process groups",
)


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable)
SOURCE_HASH = hashlib.sha256(b"frozen source").hexdigest()
PROSE_HASH = hashlib.sha256(b"neutral prose").hexdigest()


class Clock:
    """A controller clock whose readings are chosen by the test, not slept."""

    def __init__(self, seconds=0, wall_seconds=None):
        self.set(seconds, wall_seconds)

    def set(self, seconds, wall_seconds=None):
        self.ns = int(seconds * 1_000_000_000)
        self.wall = datetime(2026, 10, 8, tzinfo=timezone.utc) + timedelta(
            seconds=seconds if wall_seconds is None else wall_seconds)

    def __call__(self):
        return self.ns, self.wall.isoformat()


def recorder(tmp_path, clock, **kwargs):
    return cost_recorder.CostRecorder(tmp_path / "cost.sqlite3", clock=clock, **kwargs)


def begin(rec, *, phases=None, categories=None, required_pairs=None):
    rec.start_run("run", actor_id="controller", task_id="four-guide-treatment",
                  phases=phases or ["author"],
                  categories=categories or ["drafting", "tool-wait"],
                  required_pairs=required_pairs or (
                      None if categories else [{"phase": "author", "category": "drafting"}]),
                  source_manifest_sha256=SOURCE_HASH,
                  prose_manifest_sha256=PROSE_HASH)
    rec.start_attempt("run", "attempt", actor_id="author", task_id="four-guides")


def span(rec, identity, *, actor="author", category="drafting", phase="author",
         parent=None, attempt="attempt"):
    return rec.start_span("run", identity, actor_id=actor, task_id="four-guides",
                          attempt_id=attempt, phase=phase, category=category,
                          parent_span_id=parent)


def finish(rec, outcome="completed"):
    rec.end_attempt("run", "attempt", outcome=outcome)
    rec.end_run("run", outcome=outcome)


def tool(rec, identity, *, actor="author", parent=None):
    return rec.start_tool("run", identity, actor_id=actor, task_id="four-guides",
                          attempt_id="attempt", phase="author", category="tool-wait",
                          parent_span_id=parent, command_label="local verification",
                          command_sha256=hashlib.sha256(b"verify").hexdigest())


def end_tool(rec, identity, *, outcome="completed", exit_code: int | None = 0,
             stdout=b"", stderr=b""):
    return rec.end_tool("run", identity, outcome=outcome, exit_code=exit_code,
                        stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                        stderr_sha256=hashlib.sha256(stderr).hexdigest(),
                        stdout_bytes=len(stdout), stderr_bytes=len(stderr))


def events(tmp_path):
    return cost_recorder.read_events(tmp_path / "cost.sqlite3")


def rewrite(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_parallel_workers_are_union_wall_time_and_separate_consumption(tmp_path):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec)
        span(rec, "author-span")
        clock.set(2)
        rec.start_attempt("run", "review", actor_id="reviewer", task_id="four-guides")
        span(rec, "review-span", actor="reviewer", attempt="review")
        clock.set(8)
        rec.end_span("run", "author-span")
        clock.set(10)
        rec.end_span("run", "review-span")
        rec.end_attempt("run", "review", outcome="completed")
        finish(rec)
        summary = rec.summary("run")
    assert summary["complete"] is True
    assert summary["elapsed_wall_seconds"] == 10
    assert summary["critical_path_seconds"] == 10
    assert summary["worker_seconds"] == 16
    assert summary["per_actor_seconds"] == {"author": 8, "reviewer": 8}
    assert summary["tool_seconds"] == 0


def test_contained_other_worker_interval_cannot_shorten_elapsed_union(tmp_path):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec)
        span(rec, "outer")
        clock.set(2)
        rec.start_attempt("run", "review", actor_id="reviewer", task_id="four-guides")
        span(rec, "contained", actor="reviewer", attempt="review")
        clock.set(5)
        rec.end_span("run", "contained")
        rec.end_attempt("run", "review", outcome="completed")
        clock.set(10)
        rec.end_span("run", "outer")
        finish(rec)
        summary = rec.summary("run")
    assert summary["complete"] is True
    assert summary["elapsed_wall_seconds"] == 10
    assert summary["critical_path_seconds"] == summary["active_window_seconds"] == 10
    assert summary["worker_seconds"] == 13
    assert summary["per_actor_seconds"] == {"author": 10, "reviewer": 3}


def test_nested_and_same_worker_overlap_count_once_but_raw_tools_keep_consumption(tmp_path):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec)
        span(rec, "outer")
        clock.set(1)
        span(rec, "nested", parent="outer")
        tool(rec, "tool-one", parent="nested")
        clock.set(2)
        span(rec, "parallel-same-worker")
        tool(rec, "tool-two", parent="outer")
        clock.set(5)
        end_tool(rec, "tool-one")
        rec.end_span("run", "nested")
        clock.set(7)
        end_tool(rec, "tool-two")
        rec.end_span("run", "parallel-same-worker")
        clock.set(10)
        rec.end_span("run", "outer")
        finish(rec)
        summary = rec.summary("run")
    assert summary["complete"] is True
    assert summary["elapsed_wall_seconds"] == summary["critical_path_seconds"] == 10
    assert summary["worker_seconds"] == 10
    assert summary["per_actor_seconds"] == {"author": 10}
    assert summary["tool_seconds"] == 9


@pytest.mark.parametrize("concurrent_review", [False, True])
def test_nested_pause_subtracts_only_its_actors_active_window(tmp_path, concurrent_review):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec, categories=["drafting", "pause"])
        span(rec, "outer")
        clock.set(2)
        span(rec, "nested-pause", category="pause", parent="outer")
        if concurrent_review:
            clock.set(3)
            rec.start_attempt("run", "review", actor_id="reviewer", task_id="four-guides")
            span(rec, "review-work", actor="reviewer", attempt="review")
            clock.set(6)
            rec.end_span("run", "review-work")
            rec.end_attempt("run", "review", outcome="completed")
        clock.set(7)
        rec.end_span("run", "nested-pause")
        clock.set(10)
        rec.end_span("run", "outer")
        finish(rec)
        summary = rec.summary("run")
    assert summary["accounting_complete"] is True
    assert summary["critical_path_seconds"] == summary["elapsed_wall_seconds"] == 10
    assert summary["active_window_seconds"] == (8 if concurrent_review else 5)
    assert summary["worker_seconds"] == (13 if concurrent_review else 10)


def test_phase_category_denominator_preserves_unperformed_work(tmp_path):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec, phases=["author", "update"], categories=["drafting", "review"])
        span(rec, "draft")
        clock.set(4)
        rec.end_span("run", "draft")
        finish(rec)
        summary = rec.summary("run")
    assert summary["complete"] is False
    assert {(row["phase"], row["category"]) for row in summary["denominator"]} == {
        ("author", "drafting"), ("author", "review"),
        ("update", "drafting"), ("update", "review")}
    assert {(row["phase"], row["category"]) for row in summary["missing_denominator"]} == {
        ("author", "review"), ("update", "drafting"), ("update", "review")}
    draft = next(row for row in summary["denominator"] if row["phase"] == "author"
                 and row["category"] == "drafting")
    assert draft["worker_seconds"] == 4


def test_declared_sparse_phase_costs_keep_preparation_and_update_separate(tmp_path):
    clock = Clock()
    pairs = [{"phase": "preparation", "category": "preparation"},
             {"phase": "author", "category": "drafting"},
             {"phase": "update", "category": "revision"}]
    with recorder(tmp_path, clock) as rec:
        rec.start_run("run", actor_id="controller", task_id="four-guide-treatment",
                      phases=["preparation", "author", "update"],
                      categories=["preparation", "drafting", "revision"], required_pairs=pairs,
                      source_manifest_sha256=SOURCE_HASH, prose_manifest_sha256=PROSE_HASH)
        rec.start_attempt("run", "attempt", actor_id="author", task_id="four-guides")
        span(rec, "setup", phase="preparation", category="preparation")
        clock.set(2)
        rec.end_span("run", "setup")
        span(rec, "draft")
        clock.set(7)
        rec.end_span("run", "draft")
        span(rec, "repair", phase="update", category="revision")
        clock.set(10)
        rec.end_span("run", "repair")
        finish(rec)
        summary = rec.summary("run")
    assert summary["complete"] is True
    assert summary["elapsed_wall_seconds"] == 10
    assert {(row["phase"], row["category"]): row["worker_seconds"]
            for row in summary["denominator"]} == {
                ("preparation", "preparation"): 2,
                ("author", "drafting"): 5,
                ("update", "revision"): 3}


def begin_controller(rec, **changes):
    arguments = {"actor_id": "author", "task_id": "four-guides", "phases": ["author"],
                 "categories": ["drafting", "source-reading", "validation"],
                 "source_manifest_sha256": SOURCE_HASH, "prose_manifest_sha256": PROSE_HASH,
                 "controller_attempt_id": "attempt", "controller_span_id": "controller-scope",
                 "controller_phase": "author", "controller_category": "drafting"}
    arguments.update(changes)
    return rec.start_run("run", **arguments)


def test_explicit_controller_scope_observes_setup_and_closure_latency_without_backfill(tmp_path):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin_controller(rec)
        clock.set(2)
        span(rec, "read", category="source-reading", parent="controller-scope")
        clock.set(4)
        rec.end_span("run", "read")
        clock.set(8)
        span(rec, "check", category="validation", parent="controller-scope")
        clock.set(9)
        rec.end_span("run", "check")
        clock.set(10)
        rec.end_run("run", outcome="completed")
        summary = rec.summary("run")
        rows = rec.events()
    assert summary["accounting_complete"] is True
    assert summary["elapsed_wall_seconds"] == summary["critical_path_seconds"] == 10
    assert summary["worker_seconds"] == 10
    assert summary["missing_intervals"] == []
    assert summary["unattributed_controller_overhead_seconds"] == 0
    assert {(row["phase"], row["category"]) for row in summary["denominator"]} == {
        ("author", "drafting"), ("author", "source-reading"), ("author", "validation")}
    closed = [row for row in rows if row["event_kind"] in {"span_end", "attempt_end", "run_end"}
              and (row.get("span_id") == "controller-scope" or row["event_kind"] != "span_end")]
    assert len(closed) == 3
    assert {row["monotonic_ns"] for row in closed} == {10_000_000_000}


@pytest.mark.parametrize("missing", ["controller_attempt_id", "controller_span_id",
                                      "controller_phase", "controller_category"])
def test_partial_controller_scope_cannot_leave_a_started_run(tmp_path, missing):
    with recorder(tmp_path, Clock()) as rec:
        before = rec.events()
        with pytest.raises(ValueError):
            begin_controller(rec, **{missing: None})
        assert rec.events() == before


def test_controller_terminal_cannot_silently_close_an_open_child(tmp_path):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin_controller(rec)
        clock.set(2)
        span(rec, "unclosed-read", category="source-reading", parent="controller-scope")
        clock.set(10)
        before = rec.events()
        with pytest.raises(ValueError):
            rec.end_run("run", outcome="completed")
        assert rec.events() == before
        assert rec.summary("run")["accounting_complete"] is False


def test_failures_timeouts_and_pauses_remain_in_elapsed_and_outcomes(tmp_path):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec, categories=["drafting", "pause", "tool-wait"])
        span(rec, "failed")
        tool(rec, "failed-tool", parent="failed")
        clock.set(3)
        end_tool(rec, "failed-tool", outcome="failed", exit_code=7, stderr=b"failure")
        rec.end_span("run", "failed", outcome="failed")
        span(rec, "pause", category="pause")
        clock.set(8)
        rec.end_span("run", "pause")
        span(rec, "timeout")
        tool(rec, "timeout-tool", parent="timeout")
        clock.set(10)
        end_tool(rec, "timeout-tool", outcome="timed-out", exit_code=None)
        rec.end_span("run", "timeout", outcome="timed-out")
        finish(rec, "timed-out")
        summary = rec.summary("run")
    assert summary["elapsed_wall_seconds"] == 10
    assert summary["critical_path_seconds"] == 10
    assert summary["tool_seconds"] == 5
    assert summary["outcome"] == "timed-out"
    assert {row["outcome"] for row in summary["invocation_outcomes"]} == {"failed", "timed-out"}
    assert len(summary["invocation_outcomes"]) == 2


def test_fully_observed_failed_delivery_has_complete_accounting(tmp_path):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec)
        span(rec, "failed-work")
        clock.set(3)
        rec.end_span("run", "failed-work", outcome="failed")
        finish(rec, "failed")
        summary = rec.summary("run")
    assert summary["complete"] is False
    assert summary["accounting_complete"] is True
    assert summary["outcome"] == "failed"
    assert summary["worker_seconds"] == summary["elapsed_wall_seconds"] == 3


def test_unparented_overlapping_phase_category_attribution_is_incomplete(tmp_path):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec, phases=["author", "update"], categories=["drafting", "revision"],
              required_pairs=[{"phase": "author", "category": "drafting"},
                              {"phase": "update", "category": "revision"}])
        span(rec, "draft")
        clock.set(1)
        try:
            span(rec, "ambiguous-update", phase="update", category="revision")
        except ValueError:
            pass
        else:
            clock.set(4)
            rec.end_span("run", "ambiguous-update")
        clock.set(5)
        rec.end_span("run", "draft")
        finish(rec)
        summary = rec.summary("run")
    assert summary["complete"] is False
    assert summary["accounting_complete"] is False
    assert summary["errors"]


@pytest.mark.parametrize("damage", ["open-span", "missing-run-end", "uncovered-interval", "explicit-gap"])
def test_unobserved_or_unfinished_intervals_never_receive_complete_credit(tmp_path, damage):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec)
        if damage == "uncovered-interval":
            clock.set(2)
        span(rec, "work")
        clock.set(5)
        if damage != "open-span":
            rec.end_span("run", "work")
        if damage == "explicit-gap":
            rec.record_gap("run", reason="author boundary was not retained")
        if damage == "open-span":
            with pytest.raises(ValueError):
                finish(rec)
        elif damage != "missing-run-end":
            finish(rec)
        summary = rec.summary("run")
    assert summary["complete"] is False
    if damage == "uncovered-interval":
        assert sum(row["seconds"] for row in summary["missing_intervals"]) == 2
        assert summary["worker_seconds"] == 3
    elif damage == "explicit-gap":
        assert summary["gaps"] and "not retained" in summary["gaps"][0]["gap_or_redaction_reason"]
    else:
        assert summary["errors"]


def test_artifact_bytes_and_content_estimates_are_not_actual_model_usage(tmp_path):
    clock = Clock()
    content = "π: guide\n".encode()
    with recorder(tmp_path, clock) as rec:
        begin(rec)
        span(rec, "work")
        rec.record_artifact("run", actor_id="author", task_id="four-guides",
                            attempt_id="attempt", path="guide.md", content=content,
                            estimate_tokens=True)
        clock.set(2)
        rec.end_span("run", "work")
        finish(rec)
        summary = rec.summary("run")
    artifact_event = summary["artifacts"][0]
    artifact = artifact_event["artifact"]
    assert artifact["sha256"] == hashlib.sha256(content).hexdigest()
    assert artifact["bytes"] == len(content)
    assert artifact_event["estimated_content_tokens"]["value"] == (len(content) + 3) // 4
    assert summary["actual_usage"]["status"] == "unavailable"
    assert summary["actual_usage"]["receipts"] == []
    start = next(row for row in events(tmp_path) if row["event_kind"] == "run_start")
    assert start["source_manifest_sha256"] == SOURCE_HASH
    assert start["prose_manifest_sha256"] == PROSE_HASH


def test_restart_retains_interrupted_attempt_without_inventing_span_end(tmp_path):
    first = Clock()
    with recorder(tmp_path, first) as rec:
        begin(rec)
        span(rec, "interrupted")
        first.set(3)
        rec.record_artifact("run", actor_id="author", task_id="four-guides",
                            attempt_id="attempt", path="partial.md", content=b"partial")
    second = Clock(0, 10)
    with recorder(tmp_path, second) as rec:
        rec.start_attempt("run", "resumed", actor_id="author", task_id="four-guides",
                          resumed_from="attempt")
        span(rec, "new-work", attempt="resumed")
        second.set(2, 12)
        rec.end_span("run", "new-work")
        rec.end_attempt("run", "resumed", outcome="completed")
        rec.end_run("run", outcome="completed")
        summary = rec.summary("run")
    assert summary["complete"] is False
    assert summary["elapsed_wall_seconds"] == 12
    assert summary["worker_seconds"] == 2
    assert summary["critical_path_seconds"] == 2
    assert len(summary["clock_segments"]) == 2
    assert summary["interrupted_intervals"][0]["known_lower_bound_seconds"] == 3
    assert summary["interrupted_intervals"][0]["unobserved_tail_seconds"] is None
    assert summary["worker_lower_bound_seconds"] == 5
    assert not any(row["event_kind"] == "span_end" and row.get("span_id") == "interrupted"
                   for row in events(tmp_path))
    assert summary["errors"] or summary["gaps"]


def test_monotonic_restart_cannot_be_used_as_one_continuous_interval(tmp_path):
    first = Clock(100, 0)
    with recorder(tmp_path, first) as rec:
        begin(rec)
        span(rec, "before-restart")
        first.set(104, 4)
        rec.end_span("run", "before-restart")
        rec.end_attempt("run", "attempt", outcome="interrupted")
    second = Clock(0, 10)
    with recorder(tmp_path, second) as rec:
        rec.start_attempt("run", "resumed", actor_id="author", task_id="four-guides",
                          resumed_from="attempt")
        span(rec, "after-restart", attempt="resumed")
        second.set(3, 13)
        rec.end_span("run", "after-restart")
        rec.end_attempt("run", "resumed", outcome="completed")
        rec.end_run("run", outcome="completed")
        summary = rec.summary("run")
    assert summary["elapsed_wall_seconds"] == 13
    assert summary["critical_path_seconds"] == summary["worker_seconds"] == 7
    assert summary["complete"] is False
    assert summary["gaps"] or summary["missing_intervals"] or summary["errors"]


@pytest.mark.parametrize("clock_damage", ["monotonic-backwards", "wall-backwards", "wall-jump"])
def test_clock_reversal_or_discontinuity_prevents_complete_time_claim(tmp_path, clock_damage):
    clock = Clock(5, 5)
    with recorder(tmp_path, clock) as rec:
        begin(rec)
        span(rec, "work")
        if clock_damage == "monotonic-backwards":
            clock.set(4, 6)
        elif clock_damage == "wall-backwards":
            clock.set(6, 4)
        else:
            clock.set(6, 1006)
        try:
            rec.end_span("run", "work")
            finish(rec)
        except ValueError:
            pass
        summary = rec.summary("run")
        clock.set(7, 1007)
    assert summary["complete"] is False
    assert summary["errors"] or summary["gaps"]


@pytest.mark.parametrize("operation", ["duplicate-span", "duplicate-attempt", "double-span-end",
                                        "double-run-end", "unknown-parent", "unknown-attempt"])
def test_invalid_lifecycle_cannot_append_plausible_terminal_records(tmp_path, operation):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec)
        span(rec, "work")
        clock.set(2)
        if operation == "double-span-end":
            rec.end_span("run", "work")
        elif operation == "double-run-end":
            rec.end_span("run", "work")
            finish(rec)

        def action():
            if operation == "duplicate-span":
                return span(rec, "work")
            if operation == "duplicate-attempt":
                return rec.start_attempt("run", "attempt", actor_id="author", task_id="four-guides")
            if operation == "double-span-end":
                return rec.end_span("run", "work")
            if operation == "double-run-end":
                return rec.end_run("run", outcome="completed")
            if operation == "unknown-parent":
                return span(rec, "child", parent="does-not-exist")
            return span(rec, "child", attempt="does-not-exist")

        before = (tmp_path / "cost.sqlite3").read_bytes()
        with pytest.raises(ValueError):
            action()
        assert (tmp_path / "cost.sqlite3").read_bytes() == before


@pytest.mark.parametrize("damage", ["edit", "truncate", "drop", "duplicate", "reorder"])
def test_corrupt_ledger_cannot_be_reopened_or_credited_complete(tmp_path, damage):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec)
        span(rec, "work")
        clock.set(2)
        rec.end_span("run", "work")
        finish(rec)
        path = tmp_path / "ledger-export.jsonl"
        rec.export_jsonl(path)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    terminal_hash = rows[-1]["event_hash"]
    if damage == "edit":
        rows[2]["actor_id"] = "forged-actor"
    elif damage == "truncate":
        path.write_bytes(path.read_bytes()[:-13])
    elif damage == "drop":
        rows.pop(2)
    elif damage == "duplicate":
        rows.insert(3, dict(rows[2]))
    else:
        rows[2], rows[3] = rows[3], rows[2]
    if damage != "truncate":
        rewrite(path, rows)
    corrupt = path.read_bytes()
    with pytest.raises(ValueError):
        cost_recorder.validate_export(path, expected_terminal_hash=terminal_hash)
    assert path.read_bytes() == corrupt


def test_export_roundtrip_preserves_authenticated_events_and_never_overwrites(tmp_path):
    clock = Clock()
    destination = tmp_path / "export.jsonl"
    with recorder(tmp_path, clock) as rec:
        begin(rec)
        span(rec, "work")
        clock.set(2)
        rec.end_span("run", "work")
        finish(rec)
        original = rec.events()
        export = rec.export_jsonl(destination)
        assert export["events"] == len(original)
        assert export["bytes"] == len(destination.read_bytes())
        assert export["sha256"] == hashlib.sha256(destination.read_bytes()).hexdigest()
        parsed = [json.loads(line) for line in destination.read_text().splitlines()]
        assert parsed == original
        cost_recorder.validate_export(destination, expected_terminal_hash=original[-1]["event_hash"])
        with pytest.raises(FileExistsError):
            rec.export_jsonl(destination)
        assert [json.loads(line) for line in destination.read_text().splitlines()] == original


def test_single_writer_lock_prevents_a_second_controller_segment(tmp_path):
    with recorder(tmp_path, Clock()) as first:
        begin(first)
        before = first.events()
        with pytest.raises(ValueError, match="writer|broker"):
            recorder(tmp_path, Clock(5))
        assert first.events() == before


def test_zero_work_category_needs_an_explicit_retained_reason(tmp_path):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec, categories=["drafting", "review"])
        span(rec, "work")
        clock.set(3)
        rec.end_span("run", "work")
        rec.category_not_applicable("run", phase="author", category="review",
                                    reason="separate review treatment is outside this declared attempt")
        finish(rec)
        summary = rec.summary("run")
    assert summary["complete"] is True
    review = next(row for row in summary["denominator"] if row["category"] == "review")
    assert review["span_count"] == 0
    assert review["worker_seconds"] == 0
    assert review["not_applicable_reason"] == "separate review treatment is outside this declared attempt"
    assert summary["prior_work"] == "unavailable"


def test_work_cannot_contradict_a_zero_work_denominator_exclusion(tmp_path):
    clock = Clock()
    with recorder(tmp_path, clock) as rec:
        begin(rec, categories=["drafting", "review"])
        rec.category_not_applicable("run", phase="author", category="review",
                                    reason="no review in this treatment")
        span(rec, "draft")
        clock.set(2)
        rec.end_span("run", "draft")
        try:
            span(rec, "contradictory-review", category="review")
        except ValueError:
            pass
        else:
            clock.set(3)
            rec.end_span("run", "contradictory-review")
            finish(rec)
            assert rec.summary("run")["accounting_complete"] is False


def receipt(tmp_path, **changes):
    row = {"schema_version": "developer-value-host-usage/v1", "status": "actual",
           "attribution": {"run_id": "run", "actor_id": "author", "task_id": "four-guides",
                           "attempt_id": "attempt"},
           "input_tokens": 103, "output_tokens": 19, "cached_tokens": 7,
           "reasoning_tokens": None, "monetary_cost": None, "currency": None,
           "host_receipt_id": "retained-host-request-1", "provider": "owned-test-host"}
    row.update(changes)
    path = tmp_path / "host-receipt.json"
    path.write_text(json.dumps(row))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_actual_usage_requires_pinned_receipt_bytes_and_retains_partial_coverage(tmp_path):
    path, digest = receipt(tmp_path)
    clock = Clock()
    with recorder(tmp_path, clock, trusted_receipt_sha256=[digest]) as rec:
        begin(rec)
        span(rec, "first")
        clock.set(2)
        rec.end_span("run", "first")
        rec.record_usage("run", receipt_path=path)
        rec.end_attempt("run", "attempt", outcome="completed")
        rec.start_attempt("run", "unreceipted", actor_id="reviewer", task_id="four-guides")
        span(rec, "second", actor="reviewer", attempt="unreceipted")
        clock.set(4)
        rec.end_span("run", "second")
        rec.end_attempt("run", "unreceipted", outcome="completed")
        rec.end_run("run", outcome="completed")
        summary = rec.summary("run")
    assert summary["complete"] is True
    usage = summary["actual_usage"]
    assert usage["status"] == "partial"
    assert usage["coverage"]["attempts"] == 2
    assert usage["coverage"]["receipted_attempts"] == 1
    assert usage["receipts"][0]["receipt_sha256"] == digest
    assert usage["receipts"][0]["input_tokens"] == 103
    assert usage["receipts"][0]["monetary_cost"] is None


@pytest.mark.parametrize("damage", ["untrusted", "mutated-after-pin", "estimate", "wrong-run",
                                    "wrong-attempt", "negative-tokens", "money-no-currency"])
def test_estimates_untrusted_or_unattributable_usage_never_enter_actual_totals(tmp_path, damage):
    changes = {}
    if damage == "estimate":
        changes = {"estimated_content_tokens": 103}
    elif damage == "wrong-run":
        changes = {"attribution": {"run_id": "another-run", "actor_id": "author",
                                   "task_id": "four-guides", "attempt_id": "attempt"}}
    elif damage == "wrong-attempt":
        changes = {"attribution": {"run_id": "run", "actor_id": "author",
                                   "task_id": "four-guides", "attempt_id": "unknown"}}
    elif damage == "negative-tokens":
        changes = {"input_tokens": -1}
    elif damage == "money-no-currency":
        changes = {"monetary_cost": 0.2, "currency": None}
    path, digest = receipt(tmp_path, **changes)
    if damage == "mutated-after-pin":
        path.write_text(path.read_text() + "\n")
    clock = Clock()
    trusted = [] if damage == "untrusted" else [digest]
    with recorder(tmp_path, clock, trusted_receipt_sha256=trusted) as rec:
        begin(rec)
        before = (tmp_path / "cost.sqlite3").read_bytes()
        with pytest.raises(ValueError):
            rec.record_usage("run", receipt_path=path)
        assert (tmp_path / "cost.sqlite3").read_bytes() == before
        assert rec.summary("run")["actual_usage"]["status"] == "unavailable"


def test_reusing_same_usage_receipt_does_not_double_bill(tmp_path):
    path, digest = receipt(tmp_path)
    with recorder(tmp_path, Clock(), trusted_receipt_sha256=[digest]) as rec:
        begin(rec)
        rec.record_usage("run", receipt_path=path)
        before = (tmp_path / "cost.sqlite3").read_bytes()
        with pytest.raises(ValueError):
            rec.record_usage("run", receipt_path=path)
        assert (tmp_path / "cost.sqlite3").read_bytes() == before


def test_same_host_request_cannot_be_rebilled_by_changing_run_and_receipt_bytes(tmp_path):
    first_path, first_digest = receipt(tmp_path)
    retained_first = tmp_path / "first-host-receipt.json"
    first_path.rename(retained_first)
    second_path, second_digest = receipt(
        tmp_path, attribution={"run_id": "run-two", "actor_id": "author",
                               "task_id": "four-guides", "attempt_id": "second-attempt"})
    assert first_digest != second_digest
    clock = Clock()
    with recorder(tmp_path, clock, trusted_receipt_sha256=[first_digest, second_digest]) as rec:
        begin(rec)
        span(rec, "first-work")
        rec.record_usage("run", receipt_path=retained_first)
        clock.set(2)
        rec.end_span("run", "first-work")
        finish(rec)
        rec.start_run("run-two", actor_id="controller", task_id="four-guide-treatment",
                      phases=["author"], categories=["drafting"],
                      source_manifest_sha256=SOURCE_HASH, prose_manifest_sha256=PROSE_HASH)
        rec.start_attempt("run-two", "second-attempt", actor_id="author", task_id="four-guides")
        before = rec.events()
        with pytest.raises(ValueError):
            rec.record_usage("run-two", receipt_path=second_path)
        assert rec.events() == before
        assert rec.summary("run-two")["actual_usage"]["receipts"] == []


def test_receipted_attempts_do_not_prove_complete_model_request_or_money_coverage(tmp_path):
    path, digest = receipt(tmp_path)
    clock = Clock()
    with recorder(tmp_path, clock, trusted_receipt_sha256=[digest]) as rec:
        begin(rec)
        span(rec, "work")
        clock.set(2)
        rec.end_span("run", "work")
        rec.record_usage("run", receipt_path=path)
        finish(rec)
        summary = rec.summary("run")
    assert summary["actual_usage"]["status"] == "partial"
    assert summary["actual_usage"]["coverage"] == {"attempts": 1, "receipted_attempts": 1}
    assert summary["actual_usage"]["receipts"][0]["monetary_cost"] is None
    assert summary["actual_usage"]["request_scope_coverage"]["status"] == "unavailable"
    assert summary["actual_usage"]["request_scope_coverage"]["reason"]
    assert summary["actual_usage"]["monetary_coverage"] == "unavailable"


@contextmanager
def broker(tmp_path):
    socket_dir = tempfile.TemporaryDirectory(
        prefix="af11-socket-",
        dir="/private/tmp" if sys.platform == "darwin" else tempfile.gettempdir(),
    )
    socket_path = Path(socket_dir.name) / "broker.sock"
    db_path = tmp_path / "cost.sqlite3"
    with (tmp_path / "broker.stderr").open("ab") as stderr:
        process = subprocess.Popen(
            [str(PYTHON), "-m", "tests.developer_value.cost_recorder", "serve",
             "--db", str(db_path), "--socket", str(socket_path)],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=stderr)
        deadline = time.monotonic() + 5
        while not socket_path.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        try:
            assert process.poll() is None, (tmp_path / "broker.stderr").read_text()
            assert socket_path.exists(), "recorder broker did not bind its local socket"
            yield socket_path
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)
            socket_dir.cleanup()


def request_in_fresh_process(socket_path, operation, **arguments):
    result = subprocess.run(
        [str(PYTHON), "-m", "tests.developer_value.cost_recorder", "request",
         "--socket", str(socket_path), "--json",
         json.dumps({"operation": operation, "arguments": arguments})],
        cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def begin_broker(socket_path):
    request_in_fresh_process(socket_path, "start_run", run_id="run", actor_id="controller",
                             task_id="four-guide-treatment", phases=["author"],
                             categories=["drafting", "tool-wait"],
                             required_pairs=[{"phase": "author", "category": "drafting"}],
                             source_manifest_sha256=SOURCE_HASH, prose_manifest_sha256=PROSE_HASH)
    request_in_fresh_process(socket_path, "start_attempt", run_id="run", attempt_id="attempt",
                             actor_id="author", task_id="four-guides")
    request_in_fresh_process(socket_path, "start_span", run_id="run", span_id="work",
                             actor_id="author", task_id="four-guides", attempt_id="attempt",
                             phase="author", category="drafting")


def test_fresh_process_broker_resume_keeps_durable_history_and_segment_boundary(tmp_path):
    with broker(tmp_path) as socket_path:
        begin_broker(socket_path)
        request_in_fresh_process(socket_path, "end_span", run_id="run", span_id="work")
        request_in_fresh_process(socket_path, "end_attempt", run_id="run", attempt_id="attempt",
                                 outcome="interrupted")
    before = events(tmp_path)
    with broker(tmp_path) as socket_path:
        request_in_fresh_process(socket_path, "start_attempt", run_id="run", attempt_id="resumed",
                                 actor_id="author", task_id="four-guides", resumed_from="attempt")
        request_in_fresh_process(socket_path, "start_span", run_id="run", span_id="resumed-work",
                                 actor_id="author", task_id="four-guides", attempt_id="resumed",
                                 phase="author", category="drafting")
        request_in_fresh_process(socket_path, "end_span", run_id="run", span_id="resumed-work")
        request_in_fresh_process(socket_path, "end_attempt", run_id="run", attempt_id="resumed",
                                 outcome="completed")
        request_in_fresh_process(socket_path, "end_run", run_id="run", outcome="completed")
        summary = cost_recorder.request(socket_path, "summary", run_id="run")
    assert events(tmp_path)[:len(before)] == before
    assert len(summary["clock_segments"]) == 2
    assert summary["complete"] is False
    assert summary["worker_seconds"] > 0
    assert summary["elapsed_wall_seconds"] > summary["critical_path_seconds"]


def test_broker_serializes_concurrent_append_requests_without_lost_records(tmp_path):
    with broker(tmp_path) as socket_path:
        begin_broker(socket_path)

        def write(index):
            return cost_recorder.request(socket_path, "record_gap", run_id="run",
                                         reason=f"retained concurrent observation {index}")

        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(write, range(12)))
        summary = cost_recorder.request(socket_path, "summary", run_id="run")
    assert {row["gap_or_redaction_reason"] for row in summary["gaps"]} == {
        f"retained concurrent observation {index}" for index in range(12)}
    rows = events(tmp_path)
    assert len({row["event_id"] for row in rows}) == len(rows)
    assert len({row["sequence"] for row in rows}) == len(rows)
    with recorder(tmp_path, Clock(0, 100)) as rec:
        assert len(rec.summary("run")["gaps"]) >= 12


@pytest.mark.parametrize("outcome", ["failed", "timed-out"])
def test_real_tool_wrapper_records_boundaries_failure_hashes_and_redaction(tmp_path, outcome):
    marker = "synthetic-secret-not-a-real-credential"
    child = (
        "import sys,time; from tests.developer_value.cost_recorder import read_events; "
        f"rows=read_events({str(tmp_path / 'cost.sqlite3')!r}); "
        "assert any(x['event_kind']=='tool_start' and x.get('span_id')=='tool' for x in rows); "
        f"print({marker!r},flush=True); print('failure details',file=sys.stderr,flush=True); "
        + ("sys.exit(7)" if outcome == "failed" else "time.sleep(1)")
    )
    with broker(tmp_path) as socket_path:
        begin_broker(socket_path)
        command = [str(PYTHON), "-m", "tests.developer_value.cost_recorder", "tool",
                   "--socket", str(socket_path), "--run-id", "run", "--span-id", "tool",
                   "--actor-id", "author", "--task-id", "four-guides", "--attempt-id", "attempt",
                   "--phase", "author", "--category", "tool-wait", "--label", "local failure probe",
                   "--redaction-reason", "command/output may contain sensitive fixture text"]
        if outcome == "timed-out":
            command.extend(["--timeout", "0.5"])
        command.extend(["--", str(PYTHON), "-c", child])
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=10)
        assert result.returncode != 0
        summary = cost_recorder.request(socket_path, "summary", run_id="run")
    assert len(summary["invocation_outcomes"]) == 1
    end = summary["invocation_outcomes"][0]
    assert end["outcome"] == outcome
    assert end["tool"]["stdout_sha256"] == hashlib.sha256((marker + "\n").encode()).hexdigest()
    assert end["tool"]["stderr_sha256"] == hashlib.sha256(b"failure details\n").hexdigest()
    assert end["tool"]["stdout_bytes"] == len((marker + "\n").encode())
    assert summary["tool_seconds"] > 0
    ledger = json.dumps(events(tmp_path))
    assert marker not in ledger
    assert child not in ledger


def test_timed_out_tool_cannot_leave_its_owned_grandchild_running(tmp_path):
    marker = tmp_path / "orphan-wrote-after-timeout"
    ready = tmp_path / "grandchild-ready"
    grandchild = (
        "import os,pathlib,time; "
        f"pathlib.Path({str(ready)!r}).write_text(str(os.getpid())); "
        "time.sleep(1.5); "
        f"pathlib.Path({str(marker)!r}).write_text('orphan survived'); "
        "time.sleep(5)"
    )
    parent = (
        "import subprocess,time; "
        f"subprocess.Popen([{str(PYTHON)!r},'-c',{grandchild!r}],"
        "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(5)"
    )
    try:
        with broker(tmp_path) as socket_path:
            begin_broker(socket_path)
            result = cost_recorder.request(
                socket_path, "run_tool", run_id="run", span_id="tree-timeout",
                actor_id="author", task_id="four-guides", attempt_id="attempt",
                phase="author", category="tool-wait", command_label="owned descendant timeout probe",
                timeout=0.5, argv=[str(PYTHON), "-c", parent])
            assert result["outcome"] == "timed-out"
            assert ready.exists(), "probe grandchild must start before its cancellation is tested"
            time.sleep(1.2)
            assert not marker.exists(), "tool timeout left its owned grandchild executing"
            summary = cost_recorder.request(socket_path, "summary", run_id="run")
            assert summary["invocation_outcomes"][0]["outcome"] == "timed-out"
    finally:
        if ready.exists():
            try:
                os.kill(int(ready.read_text()), signal.SIGTERM)
            except ProcessLookupError:
                pass
