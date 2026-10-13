"""Owned per-file diagnostics for the bundled Go, Rust and Haskell helpers."""

from __future__ import annotations

import json
import sys
from typing import Any

from .common import chunk_source_files_for_cli

SCHEMA = "llm-wiki-native-diagnostics/v1"


def path_outcome(state: str, reason: str, scope: str | None = None) -> dict:
    result = {"extraction_state": state, "reason": reason}
    if scope is not None:
        result["failure_scope"] = scope
    return result


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate helper output key")
        result[key] = value
    return result


def decode_diagnostics(
    output: str, paths: list[str], language: str
) -> tuple[dict, dict]:
    """Reject unselected, contradictory or unattributable helper observations."""
    raw = json.loads(output, object_pairs_hook=_unique_object)
    if (
        not isinstance(raw, dict)
        or raw.get("schema_version") != SCHEMA
        or raw.get("language") != language
    ):
        raise ValueError("unexpected native diagnostic protocol")
    inventory, outcomes = raw.get("inventory"), raw.get("outcomes")
    if not isinstance(inventory, dict) or not isinstance(outcomes, dict):
        raise ValueError("invalid native diagnostic payload")
    selected = set(paths)
    if (set(inventory) | set(outcomes)) - selected:
        raise ValueError("unselected native diagnostic path")
    accepted = {}
    for path in paths:
        row = outcomes.get(path)
        if row is None and path not in inventory:
            accepted[path] = path_outcome("unavailable", "outcome-not-reported")
            continue
        if not isinstance(row, dict) or row.get("failure_scope") != "file":
            raise ValueError("invalid native per-file outcome")
        state, reason = row.get("extraction_state"), row.get("reason")
        if (
            not isinstance(state, str)
            or not isinstance(reason, str)
            or (state, reason)
            not in {
                ("extracted", "inventory-entry"),
                ("failed", "syntax-error"),
                ("failed", "read-error"),
            }
        ):
            raise ValueError("unsupported native per-file outcome")
        entry = inventory.get(path)
        if state == "extracted":
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("classes"), list)
                or not isinstance(entry.get("functions"), list)
            ):
                raise ValueError("successful outcome lacks parsed module record")
            entry["language"] = language
        elif path in inventory:
            raise ValueError("failed outcome contains inventory authority")
        accepted[path] = path_outcome(state, reason, "file")
    return inventory, accepted


def load_native_chunks(
    extractor: Any,
    request: Any,
    source_files: list[str],
    helper_binary: Any,
    language: str,
) -> dict:
    """Preserve completed file scope separately from failed/aborted batches."""
    inventory: dict = {}
    chunks = chunk_source_files_for_cli(source_files)
    for index, chunk in enumerate(chunks):
        cmd = extractor._build_command(request, chunk, helper_binary)
        result = extractor._run_helper(cmd, helper_binary)
        reason = "extractor-batch-failed"
        if result is not None:
            if request.diagnostics:
                if result.stderr.strip():
                    sys.stderr.write(result.stderr)
                try:
                    records, outcomes = decode_diagnostics(
                        result.stdout, chunk, language
                    )
                    extractor.last_path_outcomes.update(outcomes)
                except (ValueError, TypeError):
                    extractor.last_error = "invalid diagnostic helper output"
                    reason = "invalid-helper-output"
                    records = {}
            else:
                records = extractor._load_inventory(result)
            if not extractor.last_error:
                inventory.update(records)
                continue
        if request.diagnostics:
            extractor.last_path_outcomes.update(
                {
                    path: path_outcome("failed", reason, "extractor-batch")
                    for path in chunk
                }
            )
            for remaining in chunks[index + 1 :]:
                extractor.last_path_outcomes.update(
                    {
                        path: path_outcome("not-attempted", "extractor-batch-aborted")
                        for path in remaining
                    }
                )
            return inventory
        return {}
    return inventory
