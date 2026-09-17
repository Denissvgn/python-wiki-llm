"""Host-boundary instrumentation cannot turn missing/replayed evidence into success."""

import json

import pytest

from tests.native_workflow.run_trace import AttemptTrace, TraceError, identity, inspect_attempt, inspect_campaign


def manifest(attempt="attempt-1", *, external=False):
    pin = identity(b"frozen")
    return {"schema_version": "native-workflow-run-trace/v1", "attempt_id": attempt,
            "task_id": "T01", "arm": "B", "repetition": 0,
            "execution_kind": "external-host" if external else "replay", "host": "fixture-host.v1",
            "model": "configured-model" if external else None,
            "settings": pin if external else None, "admission": pin if external else None,
            "bindings": {key: pin for key in ("task", "protocol", "source", "wiki", "oracle", "provider", "profile", "original_roots")}}


def cleanup(trace, *, removed=True, changed=False):
    before = trace.manifest["bindings"]["original_roots"]
    trace.record("cleanup", {"original_before": before, "original_after": identity(b"different") if changed else before,
                            "workspace_removed": removed, "receipt": trace.blob(b"cleanup observation")})


def complete_run(directory, *, external=False):
    with AttemptTrace(directory, manifest(external=external)) as trace:
        if external:
            trace.blob(b"frozen")
        context = trace.blob(b"qualified context")
        trace.record("context", {"context_id": "c1", "blob": context, "counter_id": "counter.v1",
            "counter_mode": "estimated", "canonical_tokens": 5, "host_framing_tokens": None})
        source = trace.blob(b"value = 3\n")
        trace.record("source-read", {"path": "source.py", "blob": source})
        trace.record("source-read", {"path": "source.py", "blob": source})
        trace.record("model-start", {"call_id": "m1", "request": trace.blob(b"submitted request body"), "context_ids": ["c1"]})
        trace.record("model-end", {"call_id": "m1", "response": trace.blob(b"response body"),
            "receipt": trace.blob(b"external host receipt") if external else None,
            "outcome": "passed", "input_tokens": 17, "output_tokens": 8})
        trace.record("tool-start", {"call_id": "t1", "name": "edit", "arguments": trace.blob(b'{"path":"source.py"}')})
        trace.record("edit", {"path": "source.py", "before": source, "after": trace.blob(b"value = 4\n")})
        trace.record("tool-end", {"call_id": "t1", "result": trace.blob(b'{"changed":true}'), "outcome": "passed"})
        trace.record("check-start", {"call_id": "check1", "argv": [".venv/bin/python", "oracle.py"], "cwd": "."})
        trace.record("check-end", {"call_id": "check1", "stdout": trace.blob(b"compiles, wrong result"),
            "stderr": trace.blob(b""), "exit_code": 0, "compilation": "passed", "oracle": "failed"})
        trace.record("resources", {"preparation_ns": 100, "validation_bytes": 20, "peak_memory_bytes": 4096})
        cleanup(trace)
        trace.finish("passed")


@pytest.mark.parametrize("external", [False, True])
def test_complete_trace_preserves_inclusion_work_and_distinct_oracle_verdict(tmp_path, external):
    directory = tmp_path / "attempt"
    complete_run(directory, external=external)
    result = inspect_attempt(directory)
    assert result["outcome"] == "passed" and result["pending_calls"] == []
    assert result["oracle_outcomes"] == {"failed": 1}
    assert result["work"]["unique_source_paths"] == 1
    assert result["work"]["source_read_bytes"] == 20
    assert result["work"]["contexts"][0] == {"counter_id": "counter.v1", "mode": "estimated",
        "emitted_bytes": 17, "canonical_tokens": 5, "host_framing_tokens": None, "inclusions": 1}
    assert result["work"]["model_usage"] == {"input_tokens": 17, "output_tokens": 8}
    assert result["work"]["checks"][0]["oracle"] == "failed"
    assert result["model_execution_established"] is False
    assert result["admission_independently_verified"] is False


def test_failed_and_interrupted_attempts_survive_and_cannot_be_overwritten(tmp_path):
    directory = tmp_path / "failed"
    with pytest.raises(RuntimeError):
        with AttemptTrace(directory, manifest("failed")) as trace:
            trace.record("model-start", {"call_id": "m1", "request": trace.blob(b"request"), "context_ids": []})
            raise RuntimeError("private credential must not be copied")
    result = inspect_attempt(directory)
    assert result["outcome"] == "failed" and result["pending_calls"] == ["m1"]
    assert b"private credential" not in (directory / "events.jsonl").read_bytes()
    with pytest.raises(FileExistsError):
        AttemptTrace(directory, manifest("failed"))
    interrupted = tmp_path / "interrupted"
    trace = AttemptTrace(interrupted, manifest("interrupted"))
    trace._stream.close()  # simulate host termination before terminal receipt
    assert inspect_attempt(interrupted)["outcome"] == "interrupted"
    damaged = tmp_path / "damaged"
    damaged.mkdir()
    report = inspect_campaign(tmp_path)
    assert report["denominator"] == 3
    assert report["outcomes"] == {"failed": 1, "interrupted": 1, "invalid-evidence": 1}


@pytest.mark.parametrize("mutation", ["drop", "reorder", "event", "artifact", "tail"])
def test_independent_reader_rejects_tampered_or_incomplete_evidence(tmp_path, mutation):
    directory = tmp_path / "attempt"
    complete_run(directory)
    path = directory / "events.jsonl"
    lines = path.read_bytes().splitlines(keepends=True)
    if mutation == "drop":
        del lines[1]
    elif mutation == "reorder":
        lines[1], lines[2] = lines[2], lines[1]
    elif mutation == "event":
        lines[0] = lines[0].replace(b'"canonical_tokens":5', b'"canonical_tokens":0')
    elif mutation == "tail":
        lines[-1] = lines[-1][:-3]
    else:
        blob = next((directory / "blobs").iterdir())
        blob.write_bytes(b"replaced")
    path.write_bytes(b"".join(lines))
    with pytest.raises(ValueError):
        inspect_attempt(directory)


def test_missing_context_and_duplicate_outcomes_fail_at_their_boundaries(tmp_path):
    with AttemptTrace(tmp_path / "attempt", manifest()) as trace:
        request = trace.blob(b"request")
        with pytest.raises(TraceError, match="unrecorded context"):
            trace.record("model-start", {"call_id": "m1", "request": request, "context_ids": ["missing"]})
        trace.record("model-start", {"call_id": "m1", "request": request, "context_ids": []})
        with pytest.raises(TraceError, match="call outcomes"):
            trace.finish("passed")
        end = {"call_id": "m1", "response": trace.blob(b"failure"), "receipt": None,
               "outcome": "failed", "input_tokens": None, "output_tokens": None}
        trace.record("model-end", end)
        with pytest.raises(TraceError, match="call start"):
            trace.record("model-end", end)
        trace.finish("failed")


@pytest.mark.parametrize("removed,changed", [(False, False), (True, True)])
def test_cleanup_failure_cannot_become_a_completed_attempt(tmp_path, removed, changed):
    with AttemptTrace(tmp_path / "attempt", manifest()) as trace:
        cleanup(trace, removed=removed, changed=changed)
        with pytest.raises(TraceError, match="original-root integrity"):
            trace.finish("passed")
        with pytest.raises(TraceError, match="follows cleanup"):
            trace.record("source-read", {"path": "x.py", "blob": trace.blob(b"x")})


@pytest.mark.parametrize("patch", [{"repetition": True}, {"arm": "D"}, {"extra": "field"},
    {"execution_kind": "replay", "model": "claimed-live-model"}, {"admission": None, "execution_kind": "external-host"}])
def test_bad_manifest_is_rejected_before_creating_evidence(tmp_path, patch):
    path = tmp_path / "attempt"
    with pytest.raises(TraceError):
        AttemptTrace(path, {**manifest(), **patch})
    assert not path.exists()


def test_capture_is_detached_and_rejects_unknown_counts_and_outside_paths(tmp_path):
    path = tmp_path / "attempt"
    spec = manifest()
    with AttemptTrace(path, spec) as trace:
        spec["task_id"] = "changed"
        blob = trace.blob(b"source")
        for bad in ("../private", "/absolute", "C:\\secret", "a/../b"):
            with pytest.raises(TraceError):
                trace.record("source-read", {"path": bad, "blob": blob})
        with pytest.raises(TraceError):
            trace.record("resources", {"preparation_ns": True, "validation_bytes": 0, "peak_memory_bytes": 0})
        cleanup(trace)
        trace.finish("passed")
    assert json.loads((path / "manifest.json").read_text())["task_id"] == "T01"


def test_blob_budget_preserves_room_for_a_failure_receipt(tmp_path, monkeypatch):
    from tests.native_workflow import run_trace

    monkeypatch.setattr(run_trace, "MAX_TRACE_BYTES", 3000)
    monkeypatch.setattr(run_trace, "MAX_EVENT_BYTES", 1024)
    with AttemptTrace(tmp_path / "attempt", manifest()) as trace:
        with pytest.raises(TraceError, match="evidence budget"):
            trace.blob(b"x" * 2500)
    assert inspect_attempt(tmp_path / "attempt")["outcome"] == "integration-failed"


def test_failed_model_response_keeps_unknown_usage_unknown(tmp_path):
    with AttemptTrace(tmp_path / "attempt", manifest()) as trace:
        trace.record("model-start", {"call_id": "m1", "request": trace.blob(b"request"), "context_ids": []})
        trace.record("model-end", {"call_id": "m1", "response": None, "receipt": None,
                                    "outcome": "timed-out", "input_tokens": None, "output_tokens": None})
        trace.finish("timed-out")
    assert inspect_attempt(tmp_path / "attempt")["work"]["model_usage"] == {"input_tokens": None, "output_tokens": None}


def test_unreferenced_corrupt_bytes_are_not_hidden_by_a_successful_event_log(tmp_path):
    complete_run(tmp_path / "attempt")
    (tmp_path / "attempt/blobs" / ("0" * 64)).write_bytes(b"unreferenced corrupt artifact")
    with pytest.raises(TraceError, match="artifact changed"):
        inspect_attempt(tmp_path / "attempt")


def test_frozen_schedule_exposes_missing_attempts_and_changed_bindings(tmp_path):
    complete_run(tmp_path / "first")
    expected = {"first": manifest(), "second": manifest("attempt-2")}
    result = inspect_campaign(tmp_path, expected_attempts=expected)
    assert result["denominator"] == 2 and result["schedule_supplied"]
    assert result["schedule_complete"] is False
    assert result["outcomes"] == {"passed": 1, "missing-evidence": 1}
    assert result["analysis_outcomes"]["integration-failed"] == 1
    altered = {**manifest(), "arm": "C"}
    with pytest.raises(TraceError, match="frozen scheduled"):
        inspect_attempt(tmp_path / "first", expected_manifest=altered)


def test_extra_attempts_cannot_hide_outside_the_declared_schedule(tmp_path):
    complete_run(tmp_path / "unexpected")
    result = inspect_campaign(tmp_path, expected_attempts={})
    assert result["denominator"] == 1 and result["outcomes"] == {"invalid-evidence": 1}
