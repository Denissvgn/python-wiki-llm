"""Tests for services/circuit_breaker.py"""
from pathlib import Path

from llm_wiki_cli.services.circuit_breaker import (
    MAX_CONSECUTIVE_FAILURES,
    load_state,
    save_state,
    check_breaker,
    record_success,
    record_failure,
    reset_breaker,
)


class TestLoadState:
    def test_default_when_no_file(self, tmp_path):
        state = load_state(tmp_path)
        assert state["consecutive_failures"] == 0
        assert state["state"] == "closed"
        assert state["last_failure_ts"] is None

    def test_loads_existing(self, tmp_path):
        import json
        (tmp_path / "llm-wiki-breaker.json").write_text(
            json.dumps({"consecutive_failures": 2, "state": "closed", "last_failure_ts": None})
        )
        state = load_state(tmp_path)
        assert state["consecutive_failures"] == 2


class TestCheckBreaker:
    def test_closed_returns_false(self, tmp_path):
        assert check_breaker(tmp_path) is False

    def test_open_returns_true(self, tmp_path):
        import json
        (tmp_path / "llm-wiki-breaker.json").write_text(
            json.dumps({"consecutive_failures": 3, "state": "open", "last_failure_ts": None})
        )
        assert check_breaker(tmp_path) is True


class TestRecordFailure:
    def test_single_failure_stays_closed(self, tmp_path):
        record_failure(tmp_path)
        state = load_state(tmp_path)
        assert state["consecutive_failures"] == 1
        assert state["state"] == "closed"

    def test_three_failures_opens(self, tmp_path):
        for _ in range(MAX_CONSECUTIVE_FAILURES):
            record_failure(tmp_path)
        assert check_breaker(tmp_path) is True
        state = load_state(tmp_path)
        assert state["consecutive_failures"] == MAX_CONSECUTIVE_FAILURES
        assert state["state"] == "open"

    def test_failure_sets_timestamp(self, tmp_path):
        record_failure(tmp_path)
        state = load_state(tmp_path)
        assert state["last_failure_ts"] is not None


class TestRecordSuccess:
    def test_resets_count(self, tmp_path):
        record_failure(tmp_path)
        record_failure(tmp_path)
        record_success(tmp_path)
        state = load_state(tmp_path)
        assert state["consecutive_failures"] == 0
        assert state["state"] == "closed"

    def test_resets_open_breaker(self, tmp_path):
        for _ in range(MAX_CONSECUTIVE_FAILURES):
            record_failure(tmp_path)
        assert check_breaker(tmp_path) is True
        record_success(tmp_path)
        assert check_breaker(tmp_path) is False


class TestResetBreaker:
    def test_resets_to_default(self, tmp_path):
        for _ in range(MAX_CONSECUTIVE_FAILURES):
            record_failure(tmp_path)
        reset_breaker(tmp_path)
        state = load_state(tmp_path)
        assert state["consecutive_failures"] == 0
        assert state["state"] == "closed"
        assert state["last_failure_ts"] is None


class TestAtomicWrite:
    def test_state_file_valid_json(self, tmp_path):
        import json
        record_failure(tmp_path)
        path = tmp_path / "llm-wiki-breaker.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert "consecutive_failures" in data
