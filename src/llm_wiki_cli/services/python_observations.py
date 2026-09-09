"""Canonical Python observation envelopes and per-source cache validation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy

DATA_EFFECT_OBSERVATIONS_SCHEMA = "llm-wiki-data-effect-observations/v1"
IMPORT_LOCATION_OBSERVATIONS_SCHEMA = "llm-wiki-import-location-observations/v1"


def data_effect_sidecar(records: Iterable[dict]) -> dict:
    return {
        "schema_version": DATA_EFFECT_OBSERVATIONS_SCHEMA,
        "callables": sorted(
            records, key=lambda item: (item["file"], item["symbol"], item["line"])
        ),
    }


def import_sidecar(records: Iterable[dict]) -> dict:
    observations = sorted(
        records,
        key=lambda item: (
            item["source_path"],
            item["import_index"],
            item["module"],
            item["name"],
            item["line"],
        ),
    )
    return {
        "schema_version": IMPORT_LOCATION_OBSERVATIONS_SCHEMA,
        "observations": observations,
        "coverage": {
            "observed": len(observations),
            "emitted": len(observations),
            "omitted": 0,
            "limit": None,
            "truncated": False,
            "limitations": [
                "static-import-observation-does-not-claim-runtime-completeness"
            ],
        },
    }


def partition_sidecars(
    effects: dict | None, imports: dict | None, paths: Iterable[str]
) -> dict[str, dict]:
    """Store explicit empty observations separately from unavailable capabilities."""
    result = {path: {} for path in paths}
    # Do not turn missing, incompatible, or truncated producer metadata into a
    # canonical empty/complete capability by reconstructing its envelope.
    try:
        if effects is not None:
            from .data_flow import _data_effect_coverage_index

            _data_effect_coverage_index(effects)
            if effects != data_effect_sidecar(effects["callables"]):
                effects = None
    except (KeyError, TypeError, ValueError, AttributeError):
        effects = None
    try:
        if imports is not None and imports != import_sidecar(imports["observations"]):
            imports = None
    except (KeyError, TypeError, ValueError):
        imports = None
    if effects is not None:
        by_file = {path: [] for path in result}
        for record in effects["callables"]:
            if record["file"] in by_file:
                by_file[record["file"]].append(deepcopy(record))
        for path, records in by_file.items():
            result[path]["data_effects"] = data_effect_sidecar(records)
    if imports is not None:
        by_file = {path: [] for path in result}
        for record in imports["observations"]:
            if record["source_path"] in by_file:
                by_file[record["source_path"]].append(deepcopy(record))
        for path, records in by_file.items():
            result[path]["imports"] = import_sidecar(records)
    return result


def valid_cached_sidecars(
    value: object,
    path: str,
    inventory: dict,
    *,
    effects: bool,
    imports: bool,
) -> bool:
    """Validate requested schemas, source ownership, coverage, and import identity."""
    if not effects and not imports:
        return True
    if not isinstance(value, Mapping):
        return False
    try:
        if effects:
            from .data_flow import _data_effect_coverage_index

            sidecar = value.get("data_effects")
            if not isinstance(sidecar, dict) or set(sidecar) != {
                "schema_version",
                "callables",
            }:
                return False
            _data_effect_coverage_index(sidecar)
            for record in sidecar["callables"]:
                if (
                    set(record) != {"file", "symbol", "line", "coverage"}
                    or record["file"] != path
                    or type(record["line"]) is not int
                    or record["line"] <= 0
                ):
                    return False
            if sidecar != data_effect_sidecar(sidecar["callables"]):
                return False
        if imports:
            from .dependencies import _import_location_index

            sidecar = value.get("imports")
            if not isinstance(sidecar, dict) or set(sidecar) != {
                "schema_version",
                "observations",
                "coverage",
            }:
                return False
            index, invalid = _import_location_index(sidecar)
            if invalid or any(
                record["source_path"] != path for record in index.values()
            ):
                return False
            declared = inventory.get("imports", [])
            if not isinstance(declared, list) or len(index) != len(declared):
                return False
            for offset, declaration in enumerate(declared):
                record = index.get((path, offset))
                if (
                    not isinstance(declaration, Mapping)
                    or record is None
                    or record["module"] != declaration.get("module")
                    or record["name"] != declaration.get("name")
                    or set(record)
                    != {"source_path", "import_index", "module", "name", "line"}
                ):
                    return False
            if sidecar != import_sidecar(sidecar["observations"]):
                return False
    except (KeyError, TypeError, ValueError):
        return False
    return True
