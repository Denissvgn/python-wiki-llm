import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MAX_CONSECUTIVE_FAILURES = 3
DEFAULT_BREAKER_TTL_SECONDS = 3600
BREAKER_TTL_ENV = "LLM_WIKI_BREAKER_TTL_SECONDS"
_STATE_FILE = "llm-wiki-breaker.json"

_DEFAULT_STATE = {
    "consecutive_failures": 0,
    "last_failure_ts": None,
    "probe_started_ts": None,
    "state": "closed",
}


def _state_path(git_dir: Path) -> Path:
    return git_dir / _STATE_FILE


def load_state(git_dir: Path) -> dict:
    path = _state_path(git_dir)
    if not path.exists():
        return dict(_DEFAULT_STATE)
    # Readers intentionally remain lock-free: malformed/torn JSON falls back
    # to the safe defaults below, while missing keys in a partial state object
    # are filled by the default-state merge.
    try:
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, UnicodeError, ValueError, RecursionError):
        return dict(_DEFAULT_STATE)
    if not isinstance(state, dict):
        return dict(_DEFAULT_STATE)
    normalized = dict(_DEFAULT_STATE)
    failures = state.get("consecutive_failures")
    if isinstance(failures, int) and not isinstance(failures, bool) and failures >= 0:
        normalized["consecutive_failures"] = failures
    breaker_state = state.get("state")
    if breaker_state in {"closed", "open", "half-open"}:
        normalized["state"] = breaker_state
    for timestamp_key in ("last_failure_ts", "probe_started_ts"):
        timestamp = state.get(timestamp_key)
        if timestamp is None or isinstance(timestamp, str):
            normalized[timestamp_key] = timestamp
    return normalized


def save_state(git_dir: Path, state: dict) -> None:
    """Persist state atomically (write to tmp + rename)."""
    path = _state_path(git_dir)
    fd, tmp = tempfile.mkstemp(dir=git_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def check_breaker(git_dir: Path) -> bool:
    """Return whether an open breaker or active half-open probe blocks execution."""
    state = load_state(git_dir)
    breaker_state = state.get("state")
    if breaker_state not in {"open", "half-open"}:
        return False
    ttl_seconds = breaker_ttl_seconds()
    if ttl_seconds == 0:
        return True
    timestamp_key = (
        "probe_started_ts" if breaker_state == "half-open" else "last_failure_ts"
    )
    if not _timestamp_expired(state.get(timestamp_key), ttl_seconds=ttl_seconds):
        return True

    # Claim one half-open probe without clearing the failure history. A stale
    # claim expires after the same TTL so a killed probe cannot wedge recovery.
    # This advisory save is not compare-and-swap; the trigger workflow's
    # WikiLock normally serializes callers, while the lock-free breaker-state
    # race remains an accepted same-user limitation.
    state["state"] = "half-open"
    state["probe_started_ts"] = datetime.now(timezone.utc).isoformat()
    save_state(git_dir, state)
    return False


def record_success(git_dir: Path) -> None:
    state = load_state(git_dir)
    state["consecutive_failures"] = 0
    state["last_failure_ts"] = None
    state["probe_started_ts"] = None
    state["state"] = "closed"
    save_state(git_dir, state)


def record_failure(git_dir: Path) -> None:
    state = load_state(git_dir)
    failed_probe = state.get("state") == "half-open"
    state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
    state["last_failure_ts"] = datetime.now(timezone.utc).isoformat()
    state["probe_started_ts"] = None
    if failed_probe or state["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
        state["state"] = "open"
        print(
            f"Circuit breaker OPEN after {state['consecutive_failures']} consecutive failures."
        )
        ttl_seconds = breaker_ttl_seconds()
        if ttl_seconds == 0:
            print(
                "Manual trigger-agent sync is disabled; automatic recovery is "
                "configured off."
            )
            print(
                f"Enable auto-recovery with {BREAKER_TTL_ENV}>0, or re-enable now: "
                "llm-wiki trigger-agent --reset-breaker"
            )
        else:
            print(
                "Manual trigger-agent sync is temporarily disabled until "
                "auto-recovery permits a retry."
            )
            print(
                "Auto-recovery permits one retry after "
                f"{ttl_seconds:g} seconds; to re-enable immediately: "
                "llm-wiki trigger-agent --reset-breaker"
            )
    save_state(git_dir, state)


def reset_breaker(git_dir: Path) -> None:
    save_state(git_dir, dict(_DEFAULT_STATE))


def breaker_ttl_seconds() -> float:
    """Return the configured non-negative automatic-recovery TTL."""

    raw = os.environ.get(BREAKER_TTL_ENV)
    if raw is None:
        return float(DEFAULT_BREAKER_TTL_SECONDS)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return float(DEFAULT_BREAKER_TTL_SECONDS)
    if value < 0 or not math.isfinite(value):
        return float(DEFAULT_BREAKER_TTL_SECONDS)
    return value


def _timestamp_expired(value: object, *, ttl_seconds: float) -> bool:
    if not isinstance(value, str):
        return True
    try:
        failed_at = datetime.fromisoformat(value)
        if failed_at.tzinfo is None or failed_at.utcoffset() is None:
            return True
        elapsed = (
            datetime.now(timezone.utc) - failed_at.astimezone(timezone.utc)
        ).total_seconds()
    except (OverflowError, TypeError, ValueError):
        return True
    return elapsed >= ttl_seconds
