from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..config import CLI_AGENTS, DEFAULT_WIKI_DIR, IDE_AGENTS, read_config

METRICS_FILENAME = "llm-wiki-metrics.jsonl"


def metrics_path(git_dir: str | Path = ".git") -> Path:
    return Path(git_dir) / METRICS_FILENAME


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat().replace("+00:00", "Z")


def _parse_ts(value: str) -> datetime | None:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_window(value: str | int | None) -> timedelta | None:
    if value is None:
        return None
    if isinstance(value, int):
        return timedelta(days=value)
    text = str(value).strip().lower()
    if not text:
        return None
    unit = text[-1]
    amount_text = text[:-1] if unit in {"d", "h", "m"} else text
    try:
        amount = int(amount_text)
    except ValueError:
        raise ValueError("--last must be an integer number of days or a value like 30d")
    if amount < 1:
        raise ValueError("--last must be greater than zero")
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "m":
        return timedelta(minutes=amount)
    return timedelta(days=amount)


def resolve_agent(agent: str | None = None, wiki_dir: str | Path = DEFAULT_WIKI_DIR) -> tuple[str, str]:
    resolved = agent or read_config(wiki_dir).get("agent") or "generic"
    if resolved in CLI_AGENTS:
        return str(resolved), "CLI"
    if resolved in IDE_AGENTS:
        return str(resolved), "IDE"
    return str(resolved), "CLI"


def record_event(event: str, payload: dict[str, Any] | None = None, *, git_dir: str | Path = ".git") -> None:
    git_path = Path(git_dir)
    if not git_path.exists():
        return
    path = metrics_path(git_path)
    data = {"ts": _iso_now(), "event": event}
    if payload:
        data.update(payload)
    line = json.dumps(data, sort_keys=True) + "\n"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        return


def record_validation_event(
    *,
    command: str,
    passed: bool,
    issue_count: int,
    strict: bool,
    duration_ms: int | None,
    wiki_dir: str,
    src_dir: str,
    git_dir: str | Path = ".git",
) -> None:
    record_event(
        "validation",
        {
            "command": command,
            "passed": passed,
            "issue_count": issue_count,
            "strict": strict,
            "duration_ms": duration_ms,
            "wiki_dir": wiki_dir,
            "src_dir": src_dir,
        },
        git_dir=git_dir,
    )


def load_events(*, last: str | int | None = None, git_dir: str | Path = ".git") -> list[dict[str, Any]]:
    path = metrics_path(git_dir)
    if not path.exists():
        return []
    window = parse_window(last)
    cutoff = _utc_now() - window if window else None
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if cutoff:
                ts = _parse_ts(str(event.get("ts", "")))
                if ts is None or ts < cutoff:
                    continue
            events.append(event)
    return events


def current_coverage(src_dir: str = ".", wiki_dir: str | Path = DEFAULT_WIKI_DIR) -> dict[str, Any]:
    from ..commands.bootstrap_cmd import build_entity_page_map, build_module_page_map
    from ..commands.extract_cmd import get_inventory
    from ..commands.lint_cmd import _collect_documented_entities, _collect_documented_modules

    wiki_path = Path(wiki_dir)
    inventory = get_inventory(src_dir)
    code_entities = set(build_entity_page_map(inventory).values())
    code_modules = set(build_module_page_map(inventory).values())
    documented_entities = _collect_documented_entities(wiki_path)
    documented_modules = _collect_documented_modules(wiki_path)

    entity_hits = len(code_entities & documented_entities)
    module_hits = len(code_modules & documented_modules)
    total = len(code_entities) + len(code_modules)
    hits = entity_hits + module_hits
    percent = round((hits / total) * 100, 1) if total else 100.0

    return {
        "percent": percent,
        "entities": {"documented": entity_hits, "total": len(code_entities)},
        "modules": {"documented": module_hits, "total": len(code_modules)},
    }


def summarize_events(
    events: list[dict[str, Any]],
    *,
    src_dir: str = ".",
    wiki_dir: str | Path = DEFAULT_WIKI_DIR,
) -> dict[str, Any]:
    validations = [event for event in events if event.get("event") == "validation" and event.get("strict")]
    validation_failures = [event for event in validations if not event.get("passed")]
    validation_passes = len(validations) - len(validation_failures)
    accuracy = round((validation_passes / len(validations)) * 100, 1) if validations else None

    sync_finishes = [event for event in events if event.get("event") == "trigger_finish"]
    successful_syncs = [
        event for event in sync_finishes
        if event.get("exit_code") == 0 and isinstance(event.get("duration_ms"), (int, float))
    ]
    avg_sync_ms = (
        round(sum(float(event["duration_ms"]) for event in successful_syncs) / len(successful_syncs), 1)
        if successful_syncs
        else None
    )

    recent_failures = []
    for event in reversed(events):
        failed_validation = event.get("event") == "validation" and not event.get("passed")
        failed_trigger = event.get("event") == "trigger_finish" and event.get("exit_code") not in (0, None)
        if failed_validation or failed_trigger:
            recent_failures.append(event)
        if len(recent_failures) >= 5:
            break

    return {
        "accuracy": {
            "strict_validation_pass_percent": accuracy,
            "validations": len(validations),
            "failures": len(validation_failures),
        },
        "coverage": current_coverage(src_dir=src_dir, wiki_dir=wiki_dir),
        "speed": {
            "average_successful_sync_ms": avg_sync_ms,
            "successful_syncs": len(successful_syncs),
        },
        "totals": {
            "sync_attempts": len([event for event in events if event.get("event") == "trigger_start"]),
            "validations": len(validations),
            "failures": len(validation_failures) + len([
                event for event in sync_finishes if event.get("exit_code") not in (0, None)
            ]),
            "events": len(events),
        },
        "recent_failures": recent_failures,
    }
