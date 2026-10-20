"""Read-only declared-target prerequisites, separate from live analysis authority."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any
import json
from pathlib import Path
import re

from . import analysis_compatibility as ac

SCHEMA = "llm-wiki-analysis-target-prerequisites/v1"
MAX_TARGET_BYTES = 65536
MAX_ROWS = 32


def normalize_targets(value):
    """Accept project-owned declarations as data, never commands or authority."""
    if not isinstance(value, list) or len(value) > 16:
        raise ValueError("targets must be an array of at most 16 owner declarations")
    result, owners = [], set()
    fields = {
        "owner",
        "platform",
        "machine",
        "python",
        "implementation",
        "helpers",
        "components",
        "capture_route",
    }
    for row in value:
        if not isinstance(row, dict) or set(row) - fields:
            raise ValueError("unknown target declaration fields")
        owner = row.get("owner")
        if (
            not isinstance(owner, str)
            or not owner.strip()
            or len(owner) > 256
            or owner in owners
        ):
            raise ValueError(
                "target owners must be unique nonempty strings of at most 256 characters"
            )
        owners.add(owner)
        normalized: dict[str, Any] = {"owner": owner}
        for key in ("platform", "machine", "python", "implementation", "capture_route"):
            val = row.get(key)
            if val is not None and (
                not isinstance(val, str) or not val or len(val) > 512
            ):
                raise ValueError(
                    "target runtime fields must be bounded strings or null"
                )
            normalized[key] = val
        if normalized["python"] is not None and not re.fullmatch(
            r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", normalized["python"]
        ):
            raise ValueError(
                "target Python must be a declared major.minor or major.minor.patch"
            )
        helpers = row.get("helpers", {})
        if (
            not isinstance(helpers, dict)
            or len(helpers) > 9
            or any(
                not isinstance(k, str)
                or len(k) > 128
                or not isinstance(v, str)
                or len(v) > 512
                for k, v in helpers.items()
            )
        ):
            raise ValueError(
                "target helpers must be bounded component-to-toolchain strings"
            )
        components = row.get("components")
        if components is not None and (
            not isinstance(components, list)
            or not components
            or len(components) > 9
            or any(not isinstance(v, str) or not v or len(v) > 128 for v in components)
            or len(set(components)) != len(components)
        ):
            raise ValueError("target components must be a bounded unique list")
        normalized.update(helpers=dict(helpers), components=components)
        result.append(normalized)
    return result


def _portable(record, target, rules):
    """Recognize only the runtime commitments issued by registered profiles."""
    component = record["component"]
    profile = {"profile": "qualified-python-observations/v1"}
    helper = record["provenance"]["helper"]
    is_python = component in {"agent-wiki-cli", "llm-wiki/extractor/python"}
    is_ts = component in {
        "llm-wiki/extractor/typescript",
        "llm-wiki/extractor/javascript",
    }
    expected = (
        ac.digest(profile)
        if component == "agent-wiki-cli"
        else ac.digest(
            {
                "python": profile,
                "helper": "" if is_python else helper,
                "dependencies": {},
            }
        )
    )
    if not (is_python or is_ts) or record["runtime"] != expected:
        return None
    python = target["python"]
    if (
        not python
        or not target["platform"]
        or not target["machine"]
        or not target["implementation"]
    ):
        return "unknown", ["target-profile-incomplete"]
    major, minor = map(int, python.split(".")[:2])
    candidate = [target["platform"], major, minor, target["machine"].casefold()]
    if (
        target["implementation"] != "CPython"
        or candidate not in rules["portable_python_profiles"]
    ):
        return "unknown", ["target-portability-not-established"]
    if is_ts:
        required = rules.get("portable_helper_toolchains", {}).get("typescript")
        if not required or helper != required + "; active-node " + required.split(
            ";", 1
        )[0].removeprefix("node "):
            return "unknown", ["recorded-helper-portability-not-established"]
        if target["platform"] not in rules.get("portable_helper_platforms", {}).get(
            "typescript", []
        ):
            return "unknown", ["target-helper-platform-not-qualified"]
        declared = target["helpers"].get(component)
        if declared is None:
            return "unknown", ["target-helper-not-declared"]
        if declared != helper:
            return "capture-required", ["target-helper-differs"]
    return "portable", []


def _compare(record, target, rules):
    portable = _portable(record, target, rules)
    if portable is not None:
        return portable
    provenance = record["provenance"]
    recorded = provenance["platform"].split("/")
    if (
        len(recorded) != 2
        or not all(recorded)
        or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", provenance["python"])
    ):
        return "unknown", ["recorded-runtime-provenance-incomplete"]
    differences, unknown = [], []
    for key, actual in (("platform", recorded[0]), ("machine", recorded[1])):
        declared = target[key]
        if declared is None:
            unknown.append("target-" + key + "-not-declared")
        elif declared.casefold() != actual.casefold():
            differences.append("target-" + key + "-differs")
    python = target["python"]
    if python is None:
        unknown.append("target-python-not-declared")
    elif tuple(map(int, python.split("."))) != tuple(
        map(int, provenance["python"].split(".")[: len(python.split("."))])
    ):
        differences.append("target-python-differs")
    elif len(python.split(".")) != 3:
        unknown.append("target-python-patch-not-declared")
    if target["implementation"] is None:
        unknown.append("target-python-implementation-not-declared")
    elif target["implementation"] != "CPython":
        unknown.append("recorded-python-implementation-not-observable")
    if provenance["helper"]:
        helper = target["helpers"].get(record["component"])
        if helper is None:
            unknown.append("target-helper-not-declared")
        elif helper != provenance["helper"]:
            differences.append("target-helper-differs")
    return (
        ("capture-required", differences + unknown)
        if differences
        else (("unknown", unknown) if unknown else ("matching-target", []))
    )


def compare_targets(records, targets, *, rules=None):
    """Compare prerequisite metadata; never create or replace runtime identities."""
    from .analysis_capture import registry

    targets = normalize_targets(targets)
    records_unavailable = not isinstance(records, Mapping) or len(records) > 64
    if records_unavailable:
        records = {}
    if rules is None:
        try:
            rules = registry()
        except (OSError, ValueError):
            rules = {"portable_python_profiles": []}
    rows = []
    for target in targets:
        for component in target["components"] or sorted(records) or [None]:
            raw = records.get(component)
            try:
                if raw is None:
                    raise ValueError("missing record")
                record = ac.validate_record(raw, component)
                state, reasons = _compare(record, target, rules)
            except (ValueError, KeyError, TypeError):
                record, state, reasons = (
                    None,
                    "unknown",
                    ["recorded-analysis-unavailable"],
                )
            rows.append(
                {
                    "owner": target["owner"],
                    "component": component,
                    "state": state,
                    "reasons": reasons,
                    "recorded": None
                    if record is None
                    else {
                        k: record[k]
                        for k in ("implementation", "configuration", "runtime")
                    },
                    "recorded_provenance": None
                    if record is None
                    else {k: v[:512] for k, v in record["provenance"].items()},
                    "target": {
                        k: target[k]
                        for k in ("platform", "machine", "python", "implementation")
                    },
                    "capture_route": target["capture_route"],
                }
            )
    counts = dict(Counter(row["state"] for row in rows))
    status = (
        "capture-required"
        if counts.get("capture-required")
        else "unknown"
        if not rows or counts.get("unknown")
        else "requirements-match"
    )
    result = {
        "schema_version": SCHEMA,
        "status": status,
        "counts": counts,
        "rows": [],
        "bounds": {"total": len(rows), "returned": 0, "truncated": bool(rows)},
        "target_execution_verified": False,
        "source_inventory_performed": False,
        "comparison_scope": "declared-provenance-and-registered-portability; target runtime identity is not evaluated",
        "selection": {
            "recorded_components": len(records),
            "component_limit_exceeded_or_invalid": records_unavailable,
            "unselected_component_pairs": sum(
                len(set(records) - set(t["components"]))
                if t["components"] is not None
                else 0
                for t in targets
            ),
        },
        "qualification": "Declared environment prerequisites only; not target runtime identity, package compatibility, source freshness, snapshot health or hosted proof.",
        "next_action": "Review the project's authorized target-host owning capture, including complete snapshot provenance and removals, then obtain fresh target-native proof."
        if status == "capture-required"
        else "Resolve unknown declarations or records before claiming prerequisite alignment; fresh target-native proof remains required."
        if status == "unknown"
        else "Declared prerequisites align; fresh target-native proof remains required.",
    }
    for row in rows[:MAX_ROWS]:
        if (
            len(
                json.dumps(
                    {**result, "rows": [*result["rows"], row]}, ensure_ascii=True
                ).encode()
            )
            > MAX_TARGET_BYTES - 2048
        ):
            break
        result["rows"].append(row)
    result["bounds"].update(
        returned=len(result["rows"]), truncated=len(result["rows"]) != len(rows)
    )
    return result


def inspect_targets(wiki_dir, targets):
    """Read committed producer headers, without source discovery or extraction."""
    from .health_policy import digest, strict_json
    from .knowledge_model import _parse_bundle, parse_knowledge_index
    from .knowledge_packs import parse_packed_root
    from .knowledge_storage import parse_store_root
    from .knowledge_storage_io import StorageReadSession
    from .sync_manifest import SyncManifest

    records, binding, reason = {}, None, None
    try:
        session = StorageReadSession(Path(wiki_dir))
        raw = session.read(".llm-wiki-knowledge.json", 64 * 1024 * 1024)
        data = strict_json(raw)
        schema = data.get("schema_version")
        if schema in {"llm-wiki-knowledge/v3", "llm-wiki-knowledge/v4"}:
            bundle = _parse_bundle(parse_packed_root(raw)["store"]["bundle"], "bundle")
        elif schema == "llm-wiki-knowledge/v2":
            bundle = _parse_bundle(parse_store_root(raw)["store"]["bundle"], "bundle")
        else:
            bundle = parse_knowledge_index(data).bundle
        session.read(".llm-wiki-manifest.json", 64 * 1024 * 1024)
        manifest = SyncManifest.load(Path(wiki_dir))
        hashes = manifest.artifact_hashes
        surface = session.read(".llm-wiki-surface.json", 64 * 1024 * 1024)
        if (
            hashes is None
            or hashes.knowledge_index_hash != digest(raw)
            or hashes.surface_index_hash != digest(surface)
        ):
            raise ValueError("committed root/surface bindings differ")
        if len(bundle.producer.extractors) + len(bundle.producer.plugins) > 63:
            raise ValueError("producer component limit exceeded")
        records = {
            c.component_id: ac.component_record(c)
            for c in (bundle.producer.tool, *bundle.producer.extractors)
        }
        records.update(
            {"plugin/" + c.component_id: None for c in bundle.producer.plugins}
        )
        binding = {
            "knowledge_index_hash": digest(raw),
            "surface_index_hash": digest(surface),
            "source_snapshot_hash": bundle.snapshot.source_snapshot_hash,
        }
        session.recheck()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        records, binding, reason = (
            {},
            None,
            "committed-producer-metadata-unavailable: " + type(exc).__name__,
        )
    result = compare_targets(records, targets)
    result.update(snapshot_binding=binding, snapshot_limitation=reason)
    return result


def load_targets(path):
    from .health_policy import strict_json
    from .knowledge_storage_io import read_guarded

    value = strict_json(read_guarded(Path(path), MAX_TARGET_BYTES).content)
    if set(value) != {"targets"}:
        raise ValueError("target document must contain only targets")
    return normalize_targets(value["targets"])
