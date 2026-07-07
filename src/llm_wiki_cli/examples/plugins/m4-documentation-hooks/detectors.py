"""Sample M4 entry-point detector hooks for LLM Wiki plugins."""

from __future__ import annotations


def detect_worker_tasks(inventory):
    """Return task entry points from a plain extracted inventory mapping."""
    records = []
    for file_path, data in sorted(inventory.items()):
        if not isinstance(data, dict):
            continue
        for function in sorted(data.get("functions", []), key=_function_name):
            name = _function_name(function)
            if not _is_worker_task(file_path, name):
                continue
            records.append(
                {
                    "category": "task",
                    "file": file_path,
                    "symbol": name,
                    "label": "task-handler",
                }
            )
    return records


def _function_name(function):
    if isinstance(function, dict) and isinstance(function.get("name"), str):
        return function["name"]
    return ""


def _is_worker_task(file_path, function_name):
    normalized_file = str(file_path).replace("\\", "/").lower()
    normalized_name = function_name.lower()
    return normalized_file.endswith("tasks.py") and normalized_name in {
        "handle_task",
        "task_handler",
    }
