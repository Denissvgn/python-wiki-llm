"""Bounded inspection projections of the separately owned maintenance ledger."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from .knowledge_storage import canonical_bytes
from .maintenance_state import (
    LIMITS,
    MaintenanceError,
    canonical_hash,
    maintenance_core,
    validate_maintenance_adoption,
    validate_maintenance_state,
)

BINDING_KEY = "llm-wiki/maintenance-binding"
RECORD_KEY = "llm-wiki/maintenance-record"
BINDING_SCHEMA = "llm-wiki-maintenance-binding/v1"
RECORD_SCHEMA = "llm-wiki-maintenance-record-binding/v1"
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _fields(value, fields, label):
    if not isinstance(value, Mapping) or set(value) != set(fields):
        raise MaintenanceError(
            "projection-invalid", label + " fields do not match contract"
        )
    return deepcopy(dict(value))


def validate_maintenance_binding(value) -> dict:
    result = _fields(
        value, {"schema_version", "adoption_id", "state_hash"}, "maintenance binding"
    )
    if (
        result["schema_version"] != BINDING_SCHEMA
        or not isinstance(result["state_hash"], str)
        or not _HASH.fullmatch(result["state_hash"])
    ):
        raise MaintenanceError("projection-invalid", "unsupported maintenance binding")
    maintenance_core().validate_schema(
        "maintenance-adoption-v1",
        {
            "schema_version": "llm-wiki-maintenance-adoption/v1",
            "adoption_id": result["adoption_id"],
            "min_manifest_version": 7,
            "features": {
                "implementation_evidence": 1,
                "maintenance_state": 1,
                "ordinary_acknowledgment": 1,
            },
        },
    )
    return result


def _parts(concept):
    if isinstance(concept, Mapping):
        return concept["document"]["canonical_path"], concept.get("extensions", {})
    return concept.document.canonical_path, concept.extensions


def validate_maintenance_concept_projection(concept, *, binding, state=None) -> dict:
    root = validate_maintenance_binding(binding)
    path, extensions = _parts(concept)
    if RECORD_KEY not in extensions:
        return {}
    record = _fields(
        extensions[RECORD_KEY],
        {"schema_version", "adoption_id", "records", "bounds"},
        "maintenance records",
    )
    if (
        record["schema_version"] != RECORD_SCHEMA
        or record["adoption_id"] != root["adoption_id"]
    ):
        raise MaintenanceError(
            "projection-state-mismatch",
            "concept belongs to another maintenance adoption",
        )
    bounds = _fields(
        record["bounds"],
        {"observations_total", "observations_returned", "truncated"},
        "maintenance bounds",
    )
    total, returned = bounds["observations_total"], bounds["observations_returned"]
    if (
        type(total) is not int
        or not 0 <= total <= LIMITS["pending_records"]
        or type(returned) is not int
        or not 0 <= returned <= LIMITS["observations_per_object"]
        or type(bounds["truncated"]) is not bool
        or returned > total
        or bounds["truncated"] != (returned < total)
    ):
        raise MaintenanceError(
            "projection-invalid", "invalid maintenance projection bounds"
        )
    if (
        not isinstance(record["records"], (list, tuple))
        or len(record["records"]) != returned
    ):
        raise MaintenanceError("projection-invalid", "maintenance record count differs")
    seen = set()
    for value in record["records"]:
        row = _fields(
            value, {"record_id", "target", "target_presence"}, "maintenance record"
        )
        # Reuse the core's opaque-id and exact semantic-target grammar.
        from .maintenance_state import _identity

        _identity(row["record_id"])
        maintenance_core()._target(row["target"])
        if (
            row["record_id"] in seen
            or row["target"]["canonical_path"] != path
            or row["target_presence"] not in {"present", "deleted"}
        ):
            raise MaintenanceError(
                "projection-record-mismatch",
                "duplicate, foreign or invalid semantic target",
            )
        seen.add(row["record_id"])
        if state is not None:
            current = state["observations"].get(row["record_id"])
            if (
                current is None
                or row["target"] != current["target"]
                or row["target_presence"] != current["target_presence"]
            ):
                raise MaintenanceError(
                    "projection-record-mismatch",
                    "record differs from durable authority",
                )
    if len(canonical_bytes(record)) > LIMITS["object_bytes"]:
        raise MaintenanceError(
            "object-limit", "maintenance concept projection exceeds 64 KiB"
        )
    return record


def project_maintenance_knowledge(knowledge, state, marker):
    """Derive root/concept projections; history remains exclusively in the owner."""
    owner = validate_maintenance_state(state)
    guard = validate_maintenance_adoption(marker)
    if owner["adoption_id"] != guard["adoption_id"] or owner[
        "guard_hash"
    ] != canonical_hash(guard):
        raise MaintenanceError("guard-mismatch", "maintenance owner and marker differ")
    binding = {
        "schema_version": BINDING_SCHEMA,
        "adoption_id": owner["adoption_id"],
        "state_hash": canonical_hash(owner),
    }
    by_page = {}
    for record_id, observation in owner["observations"].items():
        path = observation["target"]["canonical_path"]
        by_page.setdefault(path, []).append(
            {
                "record_id": record_id,
                "target": deepcopy(observation["target"]),
                "target_presence": observation["target_presence"],
            }
        )
    concepts = []
    for concept in knowledge.concepts:
        rows = sorted(
            by_page.get(concept.document.canonical_path, []),
            key=lambda row: row["record_id"],
        )
        selected = rows[: LIMITS["observations_per_object"]]
        projection = {
            "schema_version": RECORD_SCHEMA,
            "adoption_id": owner["adoption_id"],
            "records": selected,
            "bounds": {
                "observations_total": len(rows),
                "observations_returned": len(selected),
                "truncated": len(selected) < len(rows),
            },
        }
        while len(canonical_bytes(projection)) > LIMITS["object_bytes"] and selected:
            selected.pop()
            projection["bounds"].update(
                observations_returned=len(selected), truncated=True
            )
        concepts.append(
            replace(concept, extensions={**concept.extensions, RECORD_KEY: projection})
        )
    result = replace(
        knowledge,
        concepts=tuple(concepts),
        extensions={**knowledge.extensions, BINDING_KEY: binding},
    )
    validate_maintenance_projection(result, state=owner, marker=guard)
    return result


def validate_maintenance_projection(
    knowledge, state=None, marker=None, *, complete=True, raw_content_by_page=None
) -> None:
    extensions = (
        knowledge.get("extensions", {})
        if isinstance(knowledge, Mapping)
        else knowledge.extensions
    )
    concepts = (
        knowledge["concepts"] if isinstance(knowledge, Mapping) else knowledge.concepts
    )
    reserved = any(RECORD_KEY in _parts(concept)[1] for concept in concepts)
    if BINDING_KEY not in extensions:
        if reserved or state is not None or marker is not None:
            raise MaintenanceError(
                "owner-missing", "maintenance concept projection lacks its root binding"
            )
        return
    binding = validate_maintenance_binding(extensions[BINDING_KEY])
    owner = validate_maintenance_state(state) if state is not None else None
    if owner is not None and (
        binding["adoption_id"] != owner["adoption_id"]
        or binding["state_hash"] != canonical_hash(owner)
    ):
        raise MaintenanceError(
            "projection-state-mismatch", "maintenance projection binds another ledger"
        )
    if marker is not None:
        guard = validate_maintenance_adoption(marker)
        if binding["adoption_id"] != guard["adoption_id"] or (
            owner is not None and owner["guard_hash"] != canonical_hash(guard)
        ):
            raise MaintenanceError(
                "guard-mismatch", "maintenance projection has another immutable marker"
            )
    for concept in concepts:
        path, values = _parts(concept)
        if RECORD_KEY not in values:
            if complete:
                raise MaintenanceError(
                    "owner-missing",
                    "adopted concept lacks its bounded maintenance projection",
                )
            continue
        record = validate_maintenance_concept_projection(
            concept, binding=binding, state=owner
        )
        if owner is not None:
            expected = [
                record_id
                for record_id, value in owner["observations"].items()
                if value["target"]["canonical_path"] == path
            ]
            if record["bounds"]["observations_total"] != len(expected):
                raise MaintenanceError(
                    "projection-record-mismatch",
                    "concept cardinality differs from durable owner",
                )

    if owner is not None and raw_content_by_page is not None:
        validate_maintenance_prose(
            owner,
            knowledge,
            raw_content_by_page,
            selected_paths=None
            if complete
            else {_parts(concept)[0] for concept in concepts},
        )


def validate_maintenance_prose(
    state, knowledge, raw_content_by_page, *, selected_paths=None
) -> None:
    """Validate supplied exact pages; unavailable prose makes no byte claim."""
    from .maintenance_evidence import captured_semantic_sections

    owner = validate_maintenance_state(state)
    concepts = (
        knowledge["concepts"] if isinstance(knowledge, Mapping) else knowledge.concepts
    )
    observed_pages = {}
    for concept in concepts:
        path, _ = _parts(concept)
        if path not in raw_content_by_page:
            continue
        raw = raw_content_by_page[path]
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = raw.decode("cp1252")
            except UnicodeDecodeError as exc:
                raise MaintenanceError(
                    "prose-encoding-unavailable", "page encoding cannot be qualified"
                ) from exc
        locator = (
            concept["locator"] if isinstance(concept, Mapping) else concept.locator
        )
        kind = (
            concept["document"]["page_kind"]
            if isinstance(concept, Mapping)
            else concept.document.page_kind.value
        )
        observed_pages[path] = captured_semantic_sections(
            text, locator, kind, raw_content=raw
        )
    for observation in owner["observations"].values():
        path = observation["target"]["canonical_path"]
        if selected_paths is not None and path not in selected_paths:
            continue
        prose = observation["basis"]["prose_hash"]
        if path not in observed_pages:
            if prose is not None and observation["target_presence"] == "present":
                raise MaintenanceError(
                    "prose-binding",
                    "claimed prose page is outside the supplied capture",
                )
            continue
        section = observed_pages[path].get(observation["target"]["section_locator"])
        if observation["target_presence"] == "deleted":
            if section is not None:
                raise MaintenanceError(
                    "prose-binding", "deleted semantic target is still present"
                )
        elif prose is not None and (section is None or section["prose_hash"] != prose):
            raise MaintenanceError(
                "prose-binding",
                "current semantic byte basis differs from the captured page",
            )
