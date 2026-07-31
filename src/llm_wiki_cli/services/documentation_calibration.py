"""Deterministic evidence contracts for standalone documentation calibration.

This module deliberately does not classify, label, rank, or promote flows.  Its
v1 preflight, shadow, and verdict records are diagnostic-only: they cannot admit
or qualify a calibration cohort.  The module preserves bounded source-backed
evidence in a portable census, emits an evidence-only shadow record beside the
frozen v1 worklist, and applies the calibration plan's terminal decision
precedence to already-produced gate records.  Agent inference, holdout custody,
admission authority, enforced isolation, and provider execution remain runner
responsibilities outside the core package.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Optional, Sequence

from .contracts import (
    P0_CALIBRATION_PREFLIGHT_SCHEMA_VERSION,
    P0_CALIBRATION_SHADOW_SCHEMA_VERSION,
    P0_CALIBRATION_VERDICT_SCHEMA_VERSION,
    P0_FLOW_CENSUS_SCHEMA_VERSION,
)
from .validation import (
    bool_or_none,
    filtered_trimmed_text_list,
    nonnegative_int_or_none,
    normalize_optional_portable_relative_path,
    trimmed_text_or_none,
)
from .wiki_surface import is_safe_page_id
from .wiki_surface_index import SURFACE_INDEX_FILENAME


CALIBRATION_TERMINAL_OUTCOMES = (
    "ADOPT_DEFAULT",
    "OPT_IN_ONLY",
    "REVISE_NEW_COHORT",
    "REJECT",
    "BLOCKED_NO_SHIP",
)
_CALIBRATION_PRIORITIES = frozenset({"P0", "P1", "P2"})
_SOURCE_PROVENANCE = frozenset(
    {"production", "test", "fixture", "generated", "unknown"}
)
_CONFIDENCE_VALUES = frozenset({"high", "medium", "low", "unknown", "static"})
_LANGUAGE_BY_SUFFIX = {
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".hs": "haskell",
    ".java": "java",
    ".js": "javascript",
    ".jsx": "javascript",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".mjs": "javascript",
    ".php": "php",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".swift": "swift",
    ".ts": "typescript",
    ".tsx": "typescript",
}
_MUTATION_HTTP_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_DEFINITION_PATTERNS = {
    "python": r"^\s*(?:async\s+def|def|class)\s+{symbol}\b",
    "javascript": (
        r"^\s*(?:export\s+)?(?:async\s+)?(?:function\s+{symbol}\b|"
        r"(?:const|let|var)\s+{symbol}\b|{symbol}\s*[:=])"
    ),
    "typescript": (
        r"^\s*(?:export\s+)?(?:async\s+)?(?:function\s+{symbol}\b|"
        r"(?:const|let|var)\s+{symbol}\b|{symbol}\s*[:=])"
    ),
    "go": r"^\s*func\s+(?:\([^)]*\)\s*)?{symbol}\b",
    "haskell": r"^\s*{symbol}\s*(?:::\s*|=)",
    "rust": r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+{symbol}\b",
}


class DocumentationCalibrationError(ValueError):
    """Raised when a calibration evidence contract is malformed."""


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    """Return a stable prefixed digest for a JSON-compatible mapping."""

    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def build_flow_evidence_census(
    wiki_dir: str,
    *,
    source_root: Optional[str] = None,
    source_revision: str = "unknown",
    source_fingerprint: str = "unknown",
    dependency_evidence: Optional[Mapping[str, Any]] = None,
    tool_revision: str = "unknown",
    allow_surface_fallback: bool = False,
) -> dict[str, Any]:
    """Build a deterministic, priority-blind flow evidence census.

    Missing and truncated evidence remains explicit.  Preliminary operation
    families are partitioning hints based only on exact normalized operation
    identity; they are never semantic-equivalence or priority decisions.
    """

    wiki = Path(wiki_dir).expanduser()
    if not wiki.is_dir():
        raise DocumentationCalibrationError(f"Wiki directory does not exist: {wiki}")
    surface_path = wiki / SURFACE_INDEX_FILENAME
    population_source = "surface_index"
    population_complete = True
    if allow_surface_fallback and not surface_path.exists():
        surface = {"flows": _fallback_flow_records(wiki)}
        population_source = "flow_pages_fallback"
        population_complete = False
    else:
        surface = _read_json_mapping(surface_path, "surface index")
    raw_flows = surface.get("flows")
    if raw_flows is None and allow_surface_fallback:
        raw_flows = _fallback_flow_records(wiki)
        population_source = "flow_pages_fallback"
        population_complete = False
    if not isinstance(raw_flows, list):
        raise DocumentationCalibrationError("Surface index flows must be a list.")

    source = Path(source_root).expanduser().resolve() if source_root else None
    dependency_metrics = _dependency_metric_map(dependency_evidence or {})
    capsules = []
    seen_flow_ids: set[str] = set()
    for raw in raw_flows:
        if not isinstance(raw, Mapping):
            raise DocumentationCalibrationError("Surface flow records must be objects.")
        flow_id = _required_flow_id(raw)
        if flow_id in seen_flow_ids:
            raise DocumentationCalibrationError(f"Duplicate surface flow id: {flow_id}")
        seen_flow_ids.add(flow_id)
        capsules.append(
            _flow_capsule(
                raw,
                wiki=wiki,
                source_root=source,
                source_revision=source_revision,
                dependency_metrics=dependency_metrics,
            )
        )
    capsules.sort(key=lambda item: (item["flow_id"].casefold(), item["flow_id"]))

    families_by_id: dict[str, list[str]] = defaultdict(list)
    family_basis: dict[str, str] = {}
    for capsule in capsules:
        family_id = str(capsule["preliminary_family"]["id"])
        families_by_id[family_id].append(str(capsule["flow_id"]))
        family_basis[family_id] = str(capsule["preliminary_family"]["basis"])
    families = [
        {
            "id": family_id,
            "basis": family_basis[family_id],
            "members": sorted(members, key=lambda value: (value.casefold(), value)),
            "semantic_equivalence": "unadjudicated",
        }
        for family_id, members in sorted(families_by_id.items())
    ]

    by_category = Counter(str(item["category"]) for item in capsules)
    by_provenance = Counter(str(item["source_provenance"]) for item in capsules)
    unknown_count = sum(bool(item["unknown_fields"]) for item in capsules)
    critical_review_inventory = [
        {
            "case_id": item["case_id"],
            "flow_id": item["flow_id"],
            "review_reasons": _critical_review_reasons(item),
            "classification": "unlabeled",
        }
        for item in capsules
    ]
    payload = {
        "schema_version": P0_FLOW_CENSUS_SCHEMA_VERSION,
        "source": {
            "revision": source_revision,
            "content_fingerprint": source_fingerprint,
        },
        "tool_revision": tool_revision,
        "priority_blind": True,
        "population": {
            "source": population_source,
            "complete": population_complete,
        },
        "counts": {
            "total": len(capsules),
            "by_category": dict(sorted(by_category.items())),
            "by_source_provenance": dict(sorted(by_provenance.items())),
            "with_unknowns": unknown_count,
            "preliminary_families": len(families),
        },
        "capsules": capsules,
        "preliminary_families": families,
        "critical_review_inventory": critical_review_inventory,
        "limitations": [
            "Preliminary families are partitioning hints, not alias equivalence.",
            "Critical review inventory is exhaustive and unlabelled; no item is promoted or demoted.",
            "Static absence is not runtime proof, especially when gaps or truncation are present.",
        ]
        + (
            [
                "The surface index was unavailable; flow-page fallback inventory may be incomplete."
            ]
            if not population_complete
            else []
        ),
    }
    validate_flow_evidence_census(payload)
    return payload


def validate_flow_evidence_census(payload: Mapping[str, Any]) -> None:
    """Validate the deterministic census invariants used by later runners."""

    if payload.get("schema_version") != P0_FLOW_CENSUS_SCHEMA_VERSION:
        raise DocumentationCalibrationError("Unsupported flow-census schema_version.")
    if payload.get("priority_blind") is not True:
        raise DocumentationCalibrationError("Flow census must remain priority_blind.")
    population = payload.get("population")
    if not isinstance(population, Mapping) or not isinstance(
        population.get("complete"), bool
    ):
        raise DocumentationCalibrationError("Flow census population is malformed.")
    population_source = population.get("source")
    expected_complete = population_source == "surface_index"
    if (
        population_source not in {"surface_index", "flow_pages_fallback"}
        or population.get("complete") is not expected_complete
    ):
        raise DocumentationCalibrationError(
            "Flow census population source/completeness is inconsistent."
        )
    capsules = payload.get("capsules")
    families = payload.get("preliminary_families")
    inventory = payload.get("critical_review_inventory")
    if not isinstance(capsules, list) or not isinstance(families, list):
        raise DocumentationCalibrationError("Flow census lists are malformed.")
    if not isinstance(inventory, list):
        raise DocumentationCalibrationError("Critical review inventory is malformed.")
    for item in capsules:
        if not isinstance(item, Mapping):
            raise DocumentationCalibrationError("Flow census capsules must be objects.")
        if "priority" in item or "classification" in item:
            raise DocumentationCalibrationError(
                "Priority-blind census capsules cannot contain labels or priorities."
            )
        if item.get("source_provenance") not in _SOURCE_PROVENANCE:
            raise DocumentationCalibrationError(
                "Flow census source provenance is unsupported."
            )
        if not isinstance(item.get("case_id"), str) or not item.get("case_id"):
            raise DocumentationCalibrationError("Every census capsule needs a case_id.")
        preliminary = item.get("preliminary_family")
        if (
            not isinstance(preliminary, Mapping)
            or not isinstance(preliminary.get("id"), str)
            or preliminary.get("semantic_equivalence") != "unadjudicated"
        ):
            raise DocumentationCalibrationError(
                "Every census capsule needs an unadjudicated preliminary family."
            )
        completeness = item.get("evidence_completeness")
        if not isinstance(completeness, Mapping) or any(
            value not in {"observed", "partial", "unknown"}
            for value in completeness.values()
        ):
            raise DocumentationCalibrationError(
                "Flow census evidence completeness is malformed."
            )
    flow_ids = [item.get("flow_id") for item in capsules if isinstance(item, Mapping)]
    if len(flow_ids) != len(capsules) or any(
        not isinstance(value, str) for value in flow_ids
    ):
        raise DocumentationCalibrationError("Every census capsule needs a flow_id.")
    if len(flow_ids) != len(set(flow_ids)):
        raise DocumentationCalibrationError("Flow census ids must be unique.")
    if flow_ids != sorted(flow_ids, key=lambda value: (value.casefold(), value)):
        raise DocumentationCalibrationError(
            "Flow census ordering is not deterministic."
        )
    counts = payload.get("counts")
    if not isinstance(counts, Mapping) or counts.get("total") != len(capsules):
        raise DocumentationCalibrationError(
            "Flow census total does not match capsules."
        )
    inventory_flow_ids = [
        item.get("flow_id") for item in inventory if isinstance(item, Mapping)
    ]
    if (
        len(inventory_flow_ids) != len(inventory)
        or any(not isinstance(value, str) for value in inventory_flow_ids)
        or len(inventory_flow_ids) != len(set(inventory_flow_ids))
        or set(inventory_flow_ids) != set(flow_ids)
    ):
        raise DocumentationCalibrationError(
            "Critical review inventory must cover every flow exactly by id."
        )
    case_by_flow = {item["flow_id"]: item["case_id"] for item in capsules}
    if any(
        item.get("classification") != "unlabeled"
        or item.get("case_id") != case_by_flow.get(item.get("flow_id"))
        for item in inventory
    ):
        raise DocumentationCalibrationError(
            "Critical review inventory cannot contain labels or mismatched case ids."
        )
    family_members = []
    family_ids = set()
    family_by_member = {}
    for family in families:
        if not isinstance(family, Mapping) or not isinstance(
            family.get("members"), list
        ):
            raise DocumentationCalibrationError("Preliminary family is malformed.")
        family_id = family.get("id")
        if (
            not isinstance(family_id, str)
            or not family_id
            or family_id in family_ids
            or any(not isinstance(member, str) for member in family["members"])
        ):
            raise DocumentationCalibrationError(
                "Preliminary family ids and members are malformed."
            )
        family_ids.add(family_id)
        family_members.extend(family["members"])
        family_by_member.update({member: family_id for member in family["members"]})
        if family.get("semantic_equivalence") != "unadjudicated":
            raise DocumentationCalibrationError(
                "Preliminary families cannot claim semantic equivalence."
            )
    if sorted(family_members) != sorted(flow_ids):
        raise DocumentationCalibrationError(
            "Preliminary families must preserve every flow id exactly once."
        )
    if any(
        family_by_member.get(item["flow_id"]) != item["preliminary_family"]["id"]
        for item in capsules
    ):
        raise DocumentationCalibrationError(
            "Capsule and family-map assignments do not match."
        )


def build_p0_calibration_shadow(
    worklist: Mapping[str, Any],
    census: Mapping[str, Any],
    *,
    candidate_records: Optional[Iterable[Mapping[str, Any]]] = None,
    policy_version: str = "unscored-shadow/v1",
) -> dict[str, Any]:
    """Emit current semantics beside optional, explicitly separate candidates."""

    validate_flow_evidence_census(census)
    items = worklist.get("items")
    if not isinstance(items, list):
        raise DocumentationCalibrationError("Worklist items must be a list.")
    current_by_flow: dict[str, Mapping[str, Any]] = {}
    structural_controls = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        canonical_path = item.get("canonical_path")
        if isinstance(canonical_path, str) and canonical_path.startswith("flows/"):
            flow_id = PurePosixPath(canonical_path).stem
            current_by_flow[flow_id] = item
        elif item.get("priority") == "P0" and item.get("category") in {
            "landing_context",
            "architecture_notes",
        }:
            structural_controls.append(
                {
                    "work_id": item.get("id"),
                    "category": item.get("category"),
                    "priority": "P0",
                    "candidate_change_allowed": False,
                }
            )

    candidates: dict[str, Mapping[str, Any]] = {}
    for record in candidate_records or ():
        if not isinstance(record, Mapping):
            raise DocumentationCalibrationError(
                "Candidate shadow records must be objects."
            )
        flow_id = record.get("flow_id")
        priority = record.get("candidate_priority")
        if not isinstance(flow_id, str) or priority not in _CALIBRATION_PRIORITIES:
            raise DocumentationCalibrationError(
                "Candidate shadow records require flow_id and candidate_priority."
            )
        if flow_id in candidates:
            raise DocumentationCalibrationError(
                f"Duplicate candidate flow id: {flow_id}"
            )
        candidates[flow_id] = record

    shadow_items = []
    for capsule in census["capsules"]:
        flow_id = str(capsule["flow_id"])
        current = current_by_flow.get(flow_id)
        candidate = candidates.get(flow_id)
        shadow_items.append(
            {
                "case_id": capsule["case_id"],
                "flow_id": flow_id,
                "work_id": current.get("id") if current else None,
                "visibility": "worklist" if current else "inventory_only",
                "current": {
                    "priority": current.get("priority") if current else None,
                    "reason_codes": list(current.get("signals") or [])
                    if current
                    else [],
                },
                "candidate": _candidate_shadow(candidate),
                "preliminary_family_id": capsule["preliminary_family"]["id"],
                "evidence_completeness": dict(capsule["evidence_completeness"]),
                "unknown_fields": list(capsule["unknown_fields"]),
                "ordering_key": [flow_id.casefold(), flow_id],
            }
        )

    evaluated = bool(candidates)
    if evaluated and set(candidates) != {item["flow_id"] for item in shadow_items}:
        raise DocumentationCalibrationError(
            "A candidate shadow must account for every census flow id."
        )
    return {
        "schema_version": P0_CALIBRATION_SHADOW_SCHEMA_VERSION,
        "mode": "candidate_shadow" if evaluated else "evidence_only",
        "policy_version": policy_version,
        "candidate_evaluated": evaluated,
        "current_worklist_schema": worklist.get("schema_version"),
        "census_schema": census.get("schema_version"),
        "counts": {
            "flows": len(shadow_items),
            "candidate_records": len(candidates),
            "inventory_visible": len(shadow_items),
            "structural_controls": len(structural_controls),
        },
        "structural_controls": sorted(
            structural_controls, key=lambda item: str(item.get("work_id") or "")
        ),
        "items": shadow_items,
        "limitations": (
            []
            if evaluated
            else [
                "No sealed reference cohort or candidate policy was supplied; candidate fields are intentionally not evaluated.",
                "This artifact does not change or recommend v1 priority semantics.",
            ]
        ),
    }


def evaluate_calibration_preflight(checks: Mapping[str, bool]) -> dict[str, Any]:
    """Evaluate diagnostic-only P0C-000 v1 checks without discretionary waivers.

    This legacy boolean contract reproduces baseline diagnostics but cannot
    authorize admission.  A qualifying cohort requires separate, evidence-backed
    authority and isolation contracts.
    """

    required = (
        "source_revision_matches",
        "source_fingerprint_matches",
        "source_read_only",
        "control_repetitions_match",
        "role_isolation_enforced",
        "holdout_access_enforced",
        "agent_runtime_available",
        "budget_enforced",
    )
    normalized = {}
    for name in required:
        value = checks.get(name)
        if not isinstance(value, bool):
            raise DocumentationCalibrationError(
                f"Preflight check {name!r} must be an explicit boolean."
            )
        normalized[name] = value
    failed = [name for name in required if not normalized[name]]
    return {
        "schema_version": P0_CALIBRATION_PREFLIGHT_SCHEMA_VERSION,
        "checks": normalized,
        "gate_result": "pass" if not failed else "fail_closed",
        "failed_checks": failed,
        "next_state": "BASELINE_FROZEN" if not failed else "BLOCKED_NO_SHIP",
    }


def mechanical_calibration_verdict(
    *,
    reject_reasons: Sequence[str] = (),
    blocked_reasons: Sequence[str] = (),
    revision_reasons: Sequence[str] = (),
    mandatory_gates_complete: bool,
    diversity_complete: bool,
) -> dict[str, Any]:
    """Apply diagnostic v1 precedence to already-audited gate reasons.

    ``OPT_IN_ONLY`` is reachable only after every mandatory gate is complete;
    missing authority or enforced isolation must therefore be represented as an
    incomplete mandatory gate and remains ``BLOCKED_NO_SHIP``.
    """

    for value, label in (
        (mandatory_gates_complete, "mandatory_gates_complete"),
        (diversity_complete, "diversity_complete"),
    ):
        if not isinstance(value, bool):
            raise DocumentationCalibrationError(f"{label} must be boolean.")
    reject = _reason_tuple(reject_reasons, "reject_reasons")
    blocked = _reason_tuple(blocked_reasons, "blocked_reasons")
    revise = _reason_tuple(revision_reasons, "revision_reasons")
    if reject:
        outcome = "REJECT"
        decisive = reject
    elif blocked or not mandatory_gates_complete:
        outcome = "BLOCKED_NO_SHIP"
        decisive = blocked or ("mandatory_gates_incomplete",)
    elif revise:
        outcome = "REVISE_NEW_COHORT"
        decisive = revise
    elif not diversity_complete:
        outcome = "OPT_IN_ONLY"
        decisive = ("required_model_or_runtime_diversity_incomplete",)
    else:
        outcome = "ADOPT_DEFAULT"
        decisive = ("all_mandatory_gates_and_diversity_complete",)
    return {
        "schema_version": P0_CALIBRATION_VERDICT_SCHEMA_VERSION,
        "outcome": outcome,
        "decisive_reasons": list(decisive),
        "mandatory_gates_complete": mandatory_gates_complete,
        "diversity_complete": diversity_complete,
        "precedence": [
            "REJECT",
            "BLOCKED_NO_SHIP",
            "REVISE_NEW_COHORT",
            "OPT_IN_ONLY",
            "ADOPT_DEFAULT",
        ],
    }


def validate_source_citation(citation: Mapping[str, Any], source_root: str) -> bool:
    """Recompute a census citation against a frozen source snapshot."""

    path = _portable_relative_path(citation.get("path"))
    if path is None:
        return False
    root = Path(source_root).expanduser().resolve()
    target = _safe_source_file(root, path)
    if target is None:
        return False
    start = citation.get("start_line")
    end = citation.get("end_line")
    if (
        isinstance(start, bool)
        or not isinstance(start, int)
        or isinstance(end, bool)
        or not isinstance(end, int)
        or start < 1
        or end < start
    ):
        return False
    try:
        raw = target.read_bytes()
        lines = raw.decode("utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return False
    if end > len(lines):
        return False
    excerpt = "\n".join(lines[start - 1 : end]).encode("utf-8")
    return (
        citation.get("source_sha256") == "sha256:" + hashlib.sha256(raw).hexdigest()
        and citation.get("excerpt_sha256")
        == "sha256:" + hashlib.sha256(excerpt).hexdigest()
    )


def _flow_capsule(
    raw: Mapping[str, Any],
    *,
    wiki: Path,
    source_root: Optional[Path],
    source_revision: str,
    dependency_metrics: Mapping[str, Mapping[str, int]],
) -> dict[str, Any]:
    flow_id = _required_flow_id(raw)
    entry = raw.get("entry_point")
    entry_mapping = entry if isinstance(entry, Mapping) else {}
    source_path = _portable_relative_path(
        entry_mapping.get("source_path") or raw.get("source_path")
    )
    symbol = _optional_text(entry_mapping.get("symbol") or raw.get("symbol"))
    label = _optional_text(entry_mapping.get("label") or raw.get("label"))
    category = _optional_text(raw.get("category")) or flow_id.split("-", 1)[0]
    evidence = raw.get("evidence")
    evidence_mapping = evidence if isinstance(evidence, Mapping) else {}
    flow_evidence = evidence_mapping.get("flow")
    flow_mapping = flow_evidence if isinstance(flow_evidence, Mapping) else {}
    data_flow_evidence = evidence_mapping.get("data_flow")
    data_flow = data_flow_evidence if isinstance(data_flow_evidence, Mapping) else None
    boundary_effects = _bounded_mapping_list(
        data_flow.get("boundary_effects") if data_flow else None,
        limit=256,
    )
    gaps = _bounded_mapping_list(
        data_flow.get("gaps") if data_flow else None, limit=256
    )
    routes = _bounded_mapping_list(raw.get("routes"), limit=64)
    language = _optional_text(raw.get("language")) or _language_for_path(source_path)
    if not language:
        language = "unknown"
    language = language.casefold()
    detector = _optional_text(raw.get("detector")) or "unknown"
    provenance = _source_provenance(source_path)
    source_citation = _source_citation(
        source_root,
        source_path,
        symbol,
        language,
    )
    page_path = wiki / "flows" / f"{flow_id}.md"
    page_sha256 = _file_sha256(page_path) if page_path.is_file() else None
    metrics = dependency_metrics.get(source_path or "")
    completeness = _evidence_completeness(
        source_path=source_path,
        source_citation=source_citation,
        flow=flow_mapping,
        data_flow=data_flow,
        dependency=metrics,
    )
    unknown_fields = [
        name
        for name, status in completeness.items()
        if status in {"unknown", "partial"}
    ]
    if data_flow and data_flow.get("truncated") and not boundary_effects:
        unknown_fields.append("boundary_effect_absence_under_truncation")
    family_key = _operation_family_key(label or symbol or flow_id, category)
    return {
        "case_id": _case_id(source_revision, flow_id),
        "flow_id": flow_id,
        "category": category.casefold(),
        "detector": detector,
        "language": language,
        "source_provenance": provenance,
        "entry_point": {
            "source_path": source_path,
            "symbol": symbol,
            "label": label,
        },
        "routes": routes,
        "flow": {
            "step_count": _non_negative_int_or_none(flow_mapping.get("step_count")),
            "truncated": _bool_or_none(flow_mapping.get("truncated")),
            "modules_touched": _portable_path_list(
                flow_mapping.get("modules_touched"), limit=128
            ),
        },
        "data_flow": {
            "generated": _bool_or_none(data_flow.get("generated"))
            if data_flow
            else None,
            "step_count": _non_negative_int_or_none(data_flow.get("step_count"))
            if data_flow
            else None,
            "transfer_count": _non_negative_int_or_none(data_flow.get("transfer_count"))
            if data_flow
            else None,
            "truncated": _bool_or_none(data_flow.get("truncated"))
            if data_flow
            else None,
            "boundary_effects": boundary_effects,
            "gaps": gaps,
        },
        "dependency": dict(metrics) if metrics else None,
        "source_citation": source_citation,
        "flow_page_sha256": page_sha256,
        "preliminary_family": {
            "id": "family-" + _digest(family_key)[:20],
            "basis": "exact_normalized_operation_identity",
            "key_sha256": "sha256:" + _digest(family_key),
            "semantic_equivalence": "unadjudicated",
        },
        "evidence_completeness": completeness,
        "unknown_fields": sorted(set(unknown_fields)),
    }


def _candidate_shadow(candidate: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    if candidate is None:
        return {
            "status": "not_evaluated",
            "priority": None,
            "score": None,
            "score_components": {},
            "hard_overrides": [],
            "reason_codes": [],
            "representative_id": None,
        }
    score = candidate.get("score")
    if score is not None and (isinstance(score, bool) or not isinstance(score, int)):
        raise DocumentationCalibrationError(
            "Candidate score must be an integer or null."
        )
    components = candidate.get("score_components") or {}
    if not isinstance(components, Mapping):
        raise DocumentationCalibrationError(
            "Candidate score_components must be an object."
        )
    normalized_components = _json_mapping(components)
    if any(
        not isinstance(key, str)
        or not key
        or isinstance(value, bool)
        or not isinstance(value, int)
        for key, value in normalized_components.items()
    ):
        raise DocumentationCalibrationError(
            "Candidate score_components must map names to integer values."
        )
    return {
        "status": "evaluated",
        "priority": candidate["candidate_priority"],
        "score": score,
        "score_components": dict(sorted(normalized_components.items())),
        "hard_overrides": _text_list(candidate.get("hard_overrides"), limit=32),
        "reason_codes": _text_list(candidate.get("reason_codes"), limit=32),
        "representative_id": _optional_text(candidate.get("representative_id")),
    }


def _critical_review_reasons(capsule: Mapping[str, Any]) -> list[str]:
    reasons = ["complete_population_review"]
    if capsule.get("category") == "process":
        reasons.append("process_boundary")
    data_flow = capsule.get("data_flow")
    if isinstance(data_flow, Mapping) and data_flow.get("boundary_effects"):
        reasons.append("observed_boundary_effect")
    routes = capsule.get("routes") or []
    if any(
        str(route.get("method") or "").upper() in _MUTATION_HTTP_METHODS
        for route in routes
        if isinstance(route, Mapping)
    ):
        reasons.append("mutation_transport_review")
    if capsule.get("unknown_fields"):
        reasons.append("incomplete_or_truncated_evidence")
    return reasons


def _source_citation(
    source_root: Optional[Path],
    source_path: Optional[str],
    symbol: Optional[str],
    language: str,
) -> Optional[dict[str, Any]]:
    if source_root is None or source_path is None or symbol is None:
        return None
    target = _safe_source_file(source_root, source_path)
    if target is None:
        return None
    try:
        raw = target.read_bytes()
        lines = raw.decode("utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    line_number = _definition_line(lines, symbol, language)
    if line_number is None:
        return None
    start = max(1, line_number - 3)
    end = min(len(lines), line_number + 20)
    excerpt = "\n".join(lines[start - 1 : end]).encode("utf-8")
    return {
        "path": source_path,
        "symbol": symbol,
        "start_line": start,
        "end_line": end,
        "definition_line": line_number,
        "source_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "excerpt_sha256": "sha256:" + hashlib.sha256(excerpt).hexdigest(),
    }


def _definition_line(lines: Sequence[str], symbol: str, language: str) -> Optional[int]:
    leaf = symbol.rsplit(".", 1)[-1]
    pattern = _DEFINITION_PATTERNS.get(language)
    if pattern:
        matcher = re.compile(pattern.format(symbol=re.escape(leaf)))
        for index, line in enumerate(lines, start=1):
            if matcher.search(line):
                return index
    fallback = re.compile(rf"\b{re.escape(leaf)}\b")
    for index, line in enumerate(lines, start=1):
        if fallback.search(line):
            return index
    return None


def _evidence_completeness(
    *,
    source_path: Optional[str],
    source_citation: Optional[Mapping[str, Any]],
    flow: Mapping[str, Any],
    data_flow: Optional[Mapping[str, Any]],
    dependency: Optional[Mapping[str, int]],
) -> dict[str, str]:
    call_status = "unknown"
    if flow:
        call_status = "partial" if flow.get("truncated") is True else "observed"
    data_status = "unknown"
    if data_flow:
        has_uncertainty = data_flow.get("truncated") is True or bool(
            data_flow.get("gaps")
        )
        data_status = "partial" if has_uncertainty else "observed"
    return {
        "source_path": "observed" if source_path else "unknown",
        "source_citation": "observed" if source_citation else "unknown",
        "call_graph": call_status,
        "data_flow": data_status,
        "dependency": "observed" if dependency else "unknown",
    }


def _dependency_metric_map(
    evidence: Mapping[str, Any],
) -> dict[str, dict[str, int]]:
    payload: Mapping[str, Any] = evidence
    nested = payload.get("metrics")
    if isinstance(nested, Mapping) and isinstance(nested.get("metrics"), Mapping):
        payload = nested
    raw_metrics = payload.get("metrics")
    if not isinstance(raw_metrics, Mapping):
        return {}
    result = {}
    for raw_path, counts in raw_metrics.items():
        path = _portable_relative_path(raw_path)
        if path is None or not isinstance(counts, Mapping):
            continue
        result[path] = {
            "fan_in": _safe_non_negative_int(counts.get("fan_in")),
            "fan_out": _safe_non_negative_int(counts.get("fan_out")),
            "cycle": int(counts.get("cycle") is True),
        }
    return result


def _operation_family_key(value: str, category: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    prefix = category.casefold() + "-"
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix) :]
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_") or "unknown"


def _source_provenance(source_path: Optional[str]) -> str:
    if source_path is None:
        return "unknown"
    parts = tuple(part.casefold() for part in PurePosixPath(source_path).parts)
    name = parts[-1] if parts else ""
    if "fixtures" in parts or "fixture" in parts:
        return "fixture"
    if "tests" in parts or "test" in parts or name.startswith("test_"):
        return "test"
    if any(part in {"build", "dist", "generated", "vendor"} for part in parts):
        return "generated"
    return "production"


def _language_for_path(source_path: Optional[str]) -> Optional[str]:
    if source_path is None:
        return None
    return _LANGUAGE_BY_SUFFIX.get(PurePosixPath(source_path).suffix.casefold())


def _safe_source_file(root: Path, relative: str) -> Optional[Path]:
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts:
        return None
    target = root.joinpath(*path.parts)
    if target.is_symlink() or not target.is_file():
        return None
    try:
        target.resolve().relative_to(root)
    except (OSError, ValueError):
        return None
    return target


def _read_json_mapping(path: Path, label: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DocumentationCalibrationError(f"Missing {label}: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise DocumentationCalibrationError(f"Invalid {label}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise DocumentationCalibrationError(f"{label.title()} must be an object.")
    return payload


def _fallback_flow_records(wiki: Path) -> list[dict[str, str]]:
    flows_dir = wiki / "flows"
    if flows_dir.is_symlink() or not flows_dir.is_dir():
        return []
    records = []
    for path in flows_dir.glob("*.md"):
        flow_id = path.stem
        if path.is_file() and not path.is_symlink() and is_safe_page_id(flow_id):
            records.append({"id": flow_id, "category": flow_id.split("-", 1)[0]})
    return sorted(records, key=lambda item: (item["id"].casefold(), item["id"]))


def _required_flow_id(raw: Mapping[str, Any]) -> str:
    flow_id = raw.get("id")
    if not isinstance(flow_id, str) or not flow_id or not is_safe_page_id(flow_id):
        raise DocumentationCalibrationError("Surface flow id is missing or unsafe.")
    return flow_id


def _portable_relative_path(value: object) -> Optional[str]:
    """Normalize legacy observation spelling without admitting unsafe paths."""

    return normalize_optional_portable_relative_path(value)


def _portable_path_list(value: object, *, limit: int) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    paths = {path for path in (_portable_relative_path(item) for item in value) if path}
    return sorted(paths, key=lambda item: (item.casefold(), item))[:limit]


def _bounded_mapping_list(value: object, *, limit: int) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    records = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        normalized = _json_mapping(item)
        confidence = normalized.get("confidence")
        if confidence is not None and confidence not in _CONFIDENCE_VALUES:
            normalized["confidence"] = "unknown"
        records.append(normalized)
    return sorted(
        records,
        key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")),
    )[:limit]


def _json_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(json.dumps(value, allow_nan=False, sort_keys=True))
    except (TypeError, ValueError) as exc:
        raise DocumentationCalibrationError(
            "Flow evidence must be JSON-compatible."
        ) from exc
    if not isinstance(payload, dict):
        raise DocumentationCalibrationError("Flow evidence must be an object.")
    return payload


def _text_list(value: object, *, limit: int) -> list[str]:
    """Normalize loose diagnostic text while discarding malformed observations."""

    return filtered_trimmed_text_list(value, limit=limit)


def _optional_text(value: object) -> Optional[str]:
    return trimmed_text_or_none(value)


def _safe_non_negative_int(value: object) -> int:
    parsed = nonnegative_int_or_none(value)
    return 0 if parsed is None else parsed


def _non_negative_int_or_none(value: object) -> Optional[int]:
    return nonnegative_int_or_none(value)


def _bool_or_none(value: object) -> Optional[bool]:
    return bool_or_none(value)


def _file_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _case_id(source_revision: str, flow_id: str) -> str:
    return "case-" + _digest(f"{source_revision}\0{flow_id}")[:20]


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _reason_tuple(values: Sequence[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or any(
        not isinstance(value, str) or not value.strip() for value in values
    ):
        raise DocumentationCalibrationError(
            f"{field_name} must contain non-empty strings."
        )
    return tuple(sorted({value.strip() for value in values}))
