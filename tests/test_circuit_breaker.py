"""Tests for services/circuit_breaker.py"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from llm_wiki_cli.services.circuit_breaker import (
    BREAKER_TTL_ENV,
    DEFAULT_BREAKER_TTL_SECONDS,
    MAX_CONSECUTIVE_FAILURES,
    check_breaker,
    load_state,
    record_failure,
    record_success,
    reset_breaker,
)


def _write_open_state(
    tmp_path,
    *,
    last_failure_ts,
    state="open",
    probe_started_ts=None,
):
    (tmp_path / "llm-wiki-breaker.json").write_text(
        json.dumps(
            {
                "consecutive_failures": MAX_CONSECUTIVE_FAILURES,
                "last_failure_ts": last_failure_ts,
                "probe_started_ts": probe_started_ts,
                "state": state,
            }
        ),
        encoding="utf-8",
    )


class TestLoadState:
    def test_default_when_no_file(self, tmp_path):
        state = load_state(tmp_path)
        assert state["consecutive_failures"] == 0
        assert state["state"] == "closed"
        assert state["last_failure_ts"] is None
        assert state["probe_started_ts"] is None

    def test_loads_existing(self, tmp_path):
        (tmp_path / "llm-wiki-breaker.json").write_text(
            json.dumps(
                {"consecutive_failures": 2, "state": "closed", "last_failure_ts": None}
            )
        )
        state = load_state(tmp_path)
        assert state["consecutive_failures"] == 2
        assert state["probe_started_ts"] is None

    def test_corrupt_json_falls_back_to_default(self, tmp_path):
        (tmp_path / "llm-wiki-breaker.json").write_text("{not json")
        state = load_state(tmp_path)
        assert state["consecutive_failures"] == 0
        assert state["state"] == "closed"

    @pytest.mark.parametrize(
        "payload",
        [
            b"\xff",
            b'{"consecutive_failures":'
            + (b"9" * 5000)
            + b',"state":"open"}',
        ],
    )
    def test_malformed_encoding_or_oversized_integer_falls_back_to_default(
        self, tmp_path, payload
    ):
        (tmp_path / "llm-wiki-breaker.json").write_bytes(payload)

        assert load_state(tmp_path) == {
            "consecutive_failures": 0,
            "last_failure_ts": None,
            "probe_started_ts": None,
            "state": "closed",
        }

    def test_non_object_json_falls_back_to_default(self, tmp_path):
        (tmp_path / "llm-wiki-breaker.json").write_text("[]")
        state = load_state(tmp_path)
        assert state["consecutive_failures"] == 0
        assert state["state"] == "closed"

    def test_bad_field_types_are_normalized_before_recovery(self, tmp_path):
        (tmp_path / "llm-wiki-breaker.json").write_text(
            json.dumps(
                {
                    "consecutive_failures": "3",
                    "last_failure_ts": {"invalid": True},
                    "probe_started_ts": 42,
                    "state": "open",
                    "unknown": "discarded",
                }
            ),
            encoding="utf-8",
        )

        assert check_breaker(tmp_path) is False
        record_failure(tmp_path)

        state = load_state(tmp_path)
        assert state["consecutive_failures"] == 1
        assert state["state"] == "open"
        assert state["probe_started_ts"] is None
        assert "unknown" not in state


class TestCheckBreaker:
    def test_closed_returns_false(self, tmp_path):
        assert check_breaker(tmp_path) is False

    def test_open_within_ttl_returns_true(self, tmp_path, monkeypatch):
        monkeypatch.setenv(BREAKER_TTL_ENV, "3600")
        _write_open_state(
            tmp_path,
            last_failure_ts=datetime.now(timezone.utc).isoformat(),
        )

        assert check_breaker(tmp_path) is True

    def test_default_ttl_is_3600_seconds(self, tmp_path, monkeypatch):
        monkeypatch.delenv(BREAKER_TTL_ENV, raising=False)
        assert DEFAULT_BREAKER_TTL_SECONDS == 3600
        now = datetime.now(timezone.utc)
        recent = tmp_path / "recent"
        expired = tmp_path / "expired"
        recent.mkdir()
        expired.mkdir()
        _write_open_state(
            recent,
            last_failure_ts=(now - timedelta(seconds=3599)).isoformat(),
        )
        _write_open_state(
            expired,
            last_failure_ts=(now - timedelta(seconds=3601)).isoformat(),
        )

        assert check_breaker(recent) is True
        assert check_breaker(expired) is False

    def test_expired_open_breaker_allows_failure_retry_without_resetting_count(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv(BREAKER_TTL_ENV, "60")
        _write_open_state(
            tmp_path,
            last_failure_ts=(
                datetime.now(timezone.utc) - timedelta(seconds=61)
            ).isoformat(),
        )

        assert check_breaker(tmp_path) is False
        half_open_state = load_state(tmp_path)
        assert half_open_state["state"] == "half-open"
        assert half_open_state["consecutive_failures"] == MAX_CONSECUTIVE_FAILURES
        assert half_open_state["probe_started_ts"] is not None
        assert check_breaker(tmp_path) is True

        record_failure(tmp_path)
        failed_retry = load_state(tmp_path)
        assert failed_retry["state"] == "open"
        assert failed_retry["probe_started_ts"] is None
        assert (
            failed_retry["consecutive_failures"] == MAX_CONSECUTIVE_FAILURES + 1
        )
        assert check_breaker(tmp_path) is True

    def test_expired_open_breaker_success_closes_fully(self, tmp_path, monkeypatch):
        monkeypatch.setenv(BREAKER_TTL_ENV, "60")
        _write_open_state(
            tmp_path,
            last_failure_ts=(
                datetime.now(timezone.utc) - timedelta(seconds=61)
            ).isoformat(),
        )

        assert check_breaker(tmp_path) is False
        record_success(tmp_path)

        recovered = load_state(tmp_path)
        assert recovered["state"] == "closed"
        assert recovered["consecutive_failures"] == 0
        assert recovered["last_failure_ts"] is None
        assert recovered["probe_started_ts"] is None
        assert check_breaker(tmp_path) is False

    def test_stale_half_open_probe_lease_allows_one_new_retry(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv(BREAKER_TTL_ENV, "60")
        stale_probe = (
            datetime.now(timezone.utc) - timedelta(seconds=61)
        ).isoformat()
        _write_open_state(
            tmp_path,
            last_failure_ts=stale_probe,
            state="half-open",
            probe_started_ts=stale_probe,
        )

        assert check_breaker(tmp_path) is False
        reclaimed = load_state(tmp_path)
        assert reclaimed["state"] == "half-open"
        assert reclaimed["consecutive_failures"] == MAX_CONSECUTIVE_FAILURES
        assert reclaimed["probe_started_ts"] != stale_probe
        assert check_breaker(tmp_path) is True

    @pytest.mark.parametrize("state", ["open", "half-open"])
    def test_zero_ttl_never_auto_recovers(self, tmp_path, monkeypatch, state):
        monkeypatch.setenv(BREAKER_TTL_ENV, "0")
        old_timestamp = (
            datetime.now(timezone.utc) - timedelta(days=365)
        ).isoformat()
        _write_open_state(
            tmp_path,
            last_failure_ts=old_timestamp,
            state=state,
            probe_started_ts=old_timestamp if state == "half-open" else None,
        )

        assert check_breaker(tmp_path) is True

    @pytest.mark.parametrize("timestamp", [None, "not-a-timestamp", "2026-01-01"])
    def test_malformed_timestamp_fails_open_to_recovery(
        self, tmp_path, monkeypatch, timestamp
    ):
        monkeypatch.setenv(BREAKER_TTL_ENV, "3600")
        _write_open_state(tmp_path, last_failure_ts=timestamp)

        assert check_breaker(tmp_path) is False
        assert load_state(tmp_path)["state"] == "half-open"


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

    def test_open_hints_describe_auto_recovery(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv(BREAKER_TTL_ENV, "3600")
        for _ in range(MAX_CONSECUTIVE_FAILURES):
            record_failure(tmp_path)

        output = capsys.readouterr().out.lower()
        assert output.count("auto-recovery") >= 2
        assert "3600 seconds" in output


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
        assert state["probe_started_ts"] is None


class TestAtomicWrite:
    def test_state_file_valid_json(self, tmp_path):
        record_failure(tmp_path)
        path = tmp_path / "llm-wiki-breaker.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "consecutive_failures" in data
