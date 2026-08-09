from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from ..config import CLI_AGENTS, DEFAULT_WIKI_DIR, IDE_AGENTS, read_config
from .knowledge_consumption import KnowledgeReadReason
from .knowledge_observability import KnowledgeAggregateSummary

METRICS_FILENAME = "llm-wiki-metrics.jsonl"
REDACTED_ABSOLUTE_PATH = "<redacted-absolute-path>"

_KNOWLEDGE_AVAILABILITY = {"ready", "absent", "degraded", "unsupported"}
_KNOWLEDGE_REASONS_BY_AVAILABILITY = {
    "ready": {KnowledgeReadReason.READY.value},
    "absent": {KnowledgeReadReason.ABSENT.value},
    "degraded": {
        KnowledgeReadReason.DEGRADED_INVALID.value,
        KnowledgeReadReason.DEGRADED_MIXED_SNAPSHOT.value,
    },
    "unsupported": {
        KnowledgeReadReason.KNOWLEDGE_SCHEMA_VERSION_UNSUPPORTED.value,
        KnowledgeReadReason.MANIFEST_VERSION_UNSUPPORTED.value,
        KnowledgeReadReason.SURFACE_SCHEMA_VERSION_UNSUPPORTED.value,
    },
}
_DEGRADED_REASONS = (
    _KNOWLEDGE_REASONS_BY_AVAILABILITY["degraded"]
    | _KNOWLEDGE_REASONS_BY_AVAILABILITY["unsupported"]
)
_FRESHNESS_COUNT_KEYS = {
    "basis-incompatible",
    "current",
    "nonsemantic-source-change",
    "source-changed",
    "source-missing",
    "unknown",
}
_EVIDENCE_ISSUE_COUNT_KEYS = {"missing", "invalid", "unknown"}
_PHASE_DURATION_KEYS = ("load", "evaluate", "check")


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


def resolve_agent(
    agent: str | None = None, wiki_dir: str | Path = DEFAULT_WIKI_DIR
) -> tuple[str, str]:
    resolved = agent or read_config(wiki_dir).get("agent") or "generic"
    if resolved in CLI_AGENTS:
        return str(resolved), "CLI"
    if resolved in IDE_AGENTS:
        return str(resolved), "IDE"
    return str(resolved), "CLI"


def record_event(
    event: str, payload: dict[str, Any] | None = None, *, git_dir: str | Path = ".git"
) -> None:
    try:
        git_path = Path(git_dir)
        if not git_path.exists():
            return
        path = metrics_path(git_path)
        data = {"ts": _iso_now(), "event": event}
        if payload:
            try:
                safe_payload = _sanitize_metrics_value(payload)
            except Exception:  # noqa: BLE001 - local metrics are best-effort
                safe_payload = None
            if isinstance(safe_payload, Mapping):
                data.update(safe_payload)
        line = json.dumps(data, sort_keys=True, allow_nan=False) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:  # noqa: BLE001 - metrics must not affect command success
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
    knowledge_summary: KnowledgeAggregateSummary | Mapping[str, Any] | None = None,
    git_dir: str | Path = ".git",
) -> None:
    payload: dict[str, Any] = {
        "command": command,
        "passed": passed,
        "issue_count": issue_count,
        "strict": strict,
        "duration_ms": duration_ms,
        "wiki_dir": wiki_dir,
        "src_dir": src_dir,
    }
    safe_summary = _safe_knowledge_summary(knowledge_summary)
    if safe_summary is not None:
        payload["knowledge_summary"] = safe_summary
    record_event(
        "validation",
        payload,
        git_dir=git_dir,
    )


def load_events(
    *, last: str | int | None = None, git_dir: str | Path = ".git"
) -> list[dict[str, Any]]:
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
            try:
                event = _sanitize_metrics_value(event)
            except Exception:  # noqa: BLE001, S112 - ignore unsafe legacy events
                continue
            if not isinstance(event, dict):
                continue
            if cutoff:
                ts = _parse_ts(str(event.get("ts", "")))
                if ts is None or ts < cutoff:
                    continue
            events.append(event)
    return events


def current_coverage(
    src_dir: str = ".",
    wiki_dir: str | Path = DEFAULT_WIKI_DIR,
    *,
    source_selection: str | Path | None = None,
) -> dict[str, Any]:
    from .bootstrap_runtime import (
        build_entity_occurrence_page_map,
        build_module_page_map,
    )
    from .documentation_query_builder import validate_live_query_source_selection
    from .extraction_service import (
        InventoryRequest,
        InventoryResult,
        get_inventory_result,
    )
    from .lint_service import (
        _collect_documented_entities,
        _collect_documented_modules,
    )
    from .source_selection import resolve_source_selection
    from .source_snapshot import (
        build_source_snapshot,
        capture_source_selection_inputs,
    )

    wiki_path = Path(wiki_dir)
    selection_policy = resolve_source_selection(src_dir, source_selection)
    selection_inputs = capture_source_selection_inputs(
        src_dir,
        source_selection=source_selection,
        selection_policy=selection_policy,
    )
    validate_live_query_source_selection(
        source_root=Path(src_dir),
        wiki_root=wiki_path,
        live_identity=(
            selection_policy.identity if selection_policy is not None else None
        ),
        live_selection_inputs=selection_inputs,
        operation="Current coverage",
    )
    source_snapshot = build_source_snapshot(
        src_dir,
        source_selection=source_selection,
        selection_policy=selection_policy,
        expected_selection_inputs=selection_inputs,
    )
    collected = get_inventory_result(
        InventoryRequest(
            src_dir=src_dir,
            source_selection=source_selection,
            source_snapshot=source_snapshot,
        )
    )
    if not isinstance(collected, InventoryResult) or collected.source_snapshot is None:
        raise ValueError("coverage requires a captured source snapshot")
    snapshot = collected.source_snapshot
    validate_live_query_source_selection(
        source_root=snapshot.root,
        wiki_root=wiki_path,
        live_identity=snapshot.source_selection_identity,
        live_selection_inputs=snapshot.source_selection_inputs,
        operation="Current coverage",
    )
    inventory = collected.inventory
    code_entities = set(build_entity_occurrence_page_map(inventory).values())
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
    source_selection: str | Path | None = None,
) -> dict[str, Any]:
    validations = [
        event
        for event in events
        if event.get("event") == "validation" and event.get("strict")
    ]
    validation_failures = [event for event in validations if not event.get("passed")]
    validation_passes = len(validations) - len(validation_failures)
    accuracy = (
        round((validation_passes / len(validations)) * 100, 1) if validations else None
    )

    sync_finishes = [
        event for event in events if event.get("event") == "trigger_finish"
    ]
    successful_syncs = [
        event
        for event in sync_finishes
        if event.get("exit_code") == 0
        and isinstance(event.get("duration_ms"), (int, float))
    ]
    avg_sync_ms = (
        round(
            sum(float(event["duration_ms"]) for event in successful_syncs)
            / len(successful_syncs),
            1,
        )
        if successful_syncs
        else None
    )

    recent_failures = []
    for event in reversed(events):
        failed_validation = event.get("event") == "validation" and not event.get(
            "passed"
        )
        failed_trigger = event.get("event") == "trigger_finish" and event.get(
            "exit_code"
        ) not in (0, None)
        if failed_validation or failed_trigger:
            safe_event = _sanitize_metrics_value(event)
            if isinstance(safe_event, dict):
                recent_failures.append(safe_event)
        if len(recent_failures) >= 5:
            break

    coverage = (
        current_coverage(src_dir, wiki_dir)
        if source_selection is None
        else current_coverage(
            src_dir,
            wiki_dir,
            source_selection=source_selection,
        )
    )

    summary = {
        "accuracy": {
            "strict_validation_pass_percent": accuracy,
            "validations": len(validations),
            "failures": len(validation_failures),
        },
        "coverage": coverage,
        "speed": {
            "average_successful_sync_ms": avg_sync_ms,
            "successful_syncs": len(successful_syncs),
        },
        "totals": {
            "sync_attempts": len(
                [event for event in events if event.get("event") == "trigger_start"]
            ),
            "validations": len(validations),
            "failures": len(validation_failures)
            + len(
                [
                    event
                    for event in sync_finishes
                    if event.get("exit_code") not in (0, None)
                ]
            ),
            "events": len(events),
        },
        "recent_failures": recent_failures,
    }
    for event in reversed(events):
        safe_summary = _safe_knowledge_summary(event.get("knowledge_summary"))
        if safe_summary is not None:
            summary["knowledge_summary"] = safe_summary
            break
    return summary


def _safe_knowledge_summary(
    value: KnowledgeAggregateSummary | Mapping[str, Any] | object | None,
) -> dict[str, object] | None:
    if value is None:
        return None
    try:
        raw = (
            value.to_payload()
            if isinstance(value, KnowledgeAggregateSummary)
            else value
        )
        if not isinstance(raw, Mapping):
            return None
        sanitized = _sanitize_metrics_value(raw)
        if not isinstance(sanitized, Mapping):
            return None

        availability = sanitized.get("availability")
        reason = sanitized.get("reason")
        concepts_evaluated = sanitized.get("concepts_evaluated")
        freshness_counts = _safe_count_mapping(
            sanitized.get("freshness_counts"),
            allowed_keys=_FRESHNESS_COUNT_KEYS,
        )
        evidence_issue_counts = _safe_count_mapping(
            sanitized.get("evidence_issue_counts"),
            allowed_keys=_EVIDENCE_ISSUE_COUNT_KEYS,
        )
        degraded_reason = sanitized.get("degraded_reason")
        phase_durations = _safe_phase_durations(sanitized.get("phase_durations_ms"))
        freshness_evaluated = sanitized.get("freshness_evaluated")
        if (
            availability not in _KNOWLEDGE_AVAILABILITY
            or not isinstance(reason, str)
            or reason
            not in _KNOWLEDGE_REASONS_BY_AVAILABILITY.get(
                str(availability),
                set(),
            )
            or isinstance(concepts_evaluated, bool)
            or not isinstance(concepts_evaluated, int)
            or concepts_evaluated < 0
            or (
                degraded_reason is not None
                and (
                    not isinstance(degraded_reason, str)
                    or degraded_reason not in _DEGRADED_REASONS
                )
            )
            or (
                availability in {"degraded", "unsupported"}
                and degraded_reason != reason
            )
            or (availability in {"ready", "absent"} and degraded_reason is not None)
            or not isinstance(freshness_evaluated, bool)
            or phase_durations is None
        ):
            return None
        if sanitized.get("freshness_counts") is not None and freshness_counts is None:
            return None
        if (
            sanitized.get("evidence_issue_counts") is not None
            and evidence_issue_counts is None
        ):
            return None

        validated = KnowledgeAggregateSummary(
            availability=availability,
            reason=reason,
            concepts_evaluated=concepts_evaluated,
            freshness_counts=freshness_counts,
            evidence_issue_counts=evidence_issue_counts,
            degraded_reason=degraded_reason,
            phase_durations_ms=phase_durations,
            freshness_evaluated=freshness_evaluated,
        )
        return validated.to_payload()
    except Exception:  # noqa: BLE001 - reject unsafe aggregate input
        return None


def _safe_count_mapping(
    value: object,
    *,
    allowed_keys: set[str],
) -> dict[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        return None
    if not allowed_keys.issubset(value):
        return None
    counts: dict[str, int] = {}
    for key in sorted(allowed_keys):
        if key not in value:
            continue
        count = value[key]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            return None
        counts[key] = count
    return counts


def _safe_phase_durations(value: object) -> dict[str, int | None] | None:
    if not isinstance(value, Mapping):
        return None
    if not set(_PHASE_DURATION_KEYS).issubset(value):
        return None
    durations: dict[str, int | None] = {}
    for key in _PHASE_DURATION_KEYS:
        duration = value.get(key)
        if duration is not None and (
            isinstance(duration, bool) or not isinstance(duration, int) or duration < 0
        ):
            return None
        durations[key] = duration
    return durations


def _sanitize_metrics_value(
    value: object,
    *,
    path_value: bool = False,
) -> object:
    if isinstance(value, Mapping):
        sanitized: dict[str, object] = {}
        for raw_key, child in value.items():
            if not isinstance(raw_key, str) or _forbidden_metrics_key(raw_key):
                continue
            if raw_key == "knowledge_summary":
                safe_summary = _safe_knowledge_summary(child)
                if safe_summary is not None:
                    sanitized[raw_key] = safe_summary
                continue
            sanitized[raw_key] = _sanitize_metrics_value(
                child,
                path_value=_path_field(raw_key),
            )
        return sanitized
    if isinstance(value, (list, tuple)):
        return [
            _sanitize_metrics_value(child, path_value=path_value) for child in value
        ]
    if path_value and isinstance(value, str) and _is_absolute_path(value):
        return REDACTED_ABSOLUTE_PATH
    return value


def _forbidden_metrics_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", key.casefold()).strip("_")
    return (
        "locator" in normalized
        or normalized.endswith(("hash", "hashes"))
        or "actor" in normalized
        or "author" in normalized
        or "remote" in normalized
    )


def _path_field(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", key.casefold()).strip("_")
    tokens = normalized.split("_")
    return any(
        token in {"path", "paths", "dir", "dirs", "directory", "directories", "output"}
        for token in tokens
    )


def _is_absolute_path(value: str) -> bool:
    windows_path = PureWindowsPath(value)
    return (
        PurePosixPath(value).is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.root)
    )
