import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MAX_CONSECUTIVE_FAILURES = 3
_STATE_FILE = "llm-wiki-breaker.json"

_DEFAULT_STATE = {
    "consecutive_failures": 0,
    "last_failure_ts": None,
    "state": "closed",
}


def _state_path(git_dir: Path) -> Path:
    return git_dir / _STATE_FILE


def load_state(git_dir: Path) -> dict:
    path = _state_path(git_dir)
    if not path.exists():
        return dict(_DEFAULT_STATE)
    with open(path) as f:
        return json.load(f)


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
    """Return True if the circuit is open (should block execution)."""
    state = load_state(git_dir)
    return state.get("state") == "open"


def record_success(git_dir: Path) -> None:
    state = load_state(git_dir)
    state["consecutive_failures"] = 0
    state["state"] = "closed"
    save_state(git_dir, state)


def record_failure(git_dir: Path) -> None:
    state = load_state(git_dir)
    state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
    state["last_failure_ts"] = datetime.now(timezone.utc).isoformat()
    if state["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
        state["state"] = "open"
        print(
            f"Circuit breaker OPEN after {state['consecutive_failures']} consecutive failures."
        )
        print("Wiki auto-sync is now disabled.")
        print("To re-enable: llm-wiki trigger-agent --reset-breaker")
    save_state(git_dir, state)


def reset_breaker(git_dir: Path) -> None:
    save_state(git_dir, dict(_DEFAULT_STATE))
