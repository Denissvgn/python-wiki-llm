"""Versioned, out-of-band evidence contracts for documentation agents.

Claim evidence qualifies a documentation assertion against the supported
native query service.  Runtime-capture evidence records an observation made by
an explicitly authorized capture workflow.  Neither record is written into
the native knowledge projection or governance ledger, and neither can upgrade
structural evidence, freshness, review, verification, or lifecycle state.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from .knowledge_evidence import is_valid_sha256

if TYPE_CHECKING:
    from .documentation_queries import DocumentationGraphQueryService


CLAIM_EVIDENCE_SCHEMA_VERSION = "llm-wiki-documentation-claim-evidence/v1"
RUNTIME_CAPTURE_SCHEMA_VERSION = "llm-wiki-documentation-runtime-capture/v1"

_CLAIM_FIELDS = frozenset(
    {
        "schema_version",
        "claim_id",
        "canonical_page",
        "concept_query",
        "resolution",
        "concept_uid",
        "concept_locator",
        "section_locator",
        "structural_evidence",
        "freshness",
        "lifecycle_review",
        "graph_query",
        "bounds",
        "safe_evidence_link",
        "internal_evidence_ref",
    }
)
_CLAIM_REQUIRED = frozenset(
    {
        "schema_version",
        "claim_id",
        "canonical_page",
        "concept_query",
        "resolution",
        "structural_evidence",
        "freshness",
        "bounds",
        "safe_evidence_link",
    }
)
_CAPTURE_FIELDS = frozenset(
    {
        "schema_version",
        "capture_id",
        "capture_digest",
        "capture_path",
        "command_or_flow_id",
        "result",
        "concept_uid",
        "concept_locator",
        "section_locator",
        "native_observation",
        "redaction",
        "environment",
        "limitations",
    }
)
_CAPTURE_REQUIRED = frozenset(
    {
        "schema_version",
        "capture_id",
        "capture_digest",
        "capture_path",
        "command_or_flow_id",
        "result",
        "concept_uid",
        "concept_locator",
        "section_locator",
        "native_observation",
        "redaction",
        "environment",
        "limitations",
    }
)
_RESOLUTIONS = frozenset(
    {
        "exact",
        "ambiguous",
        "missing",
        "native-unavailable",
        "typed-graph-unavailable",
    }
)
_EVIDENCE_STATES = frozenset(
    {"present", "missing", "invalid", "unknown", "not-applicable"}
)
_FRESHNESS_STATES = frozenset(
    {
        "current",
        "nonsemantic-source-change",
        "source-changed",
        "source-missing",
        "basis-incompatible",
        "unknown",
    }
)
_AVAILABILITY_STATES = frozenset(
    {"ready", "absent", "degraded", "unsupported"}
)
_OWNERSHIP_STATES = frozenset({"generated", "semantic", "mixed", "unknown"})
_CAPTURE_STATES = frozenset({"captured", "failed", "deferred"})
_REDACTION_STATES = frozenset({"not-required", "redacted", "rejected"})
_ENVIRONMENT_MODES = frozenset(
    {"disposable", "read-only-service", "unavailable"}
)
_RUNTIME_CAPTURE_SUFFIXES = frozenset(
    {
        ".gif",
        ".jpeg",
        ".jpg",
        ".json",
        ".log",
        ".md",
        ".mp4",
        ".png",
        ".svg",
        ".txt",
        ".webm",
        ".webp",
    }
)
_UNINSPECTED_MEDIA_SUFFIXES = frozenset(
    {".gif", ".jpeg", ".jpg", ".mp4", ".png", ".webm", ".webp"}
)
_UNINSPECTED_MEDIA_LIMITATIONS = frozenset(
    {
        "binary-media-content-not-machine-inspected",
        "canonical-body-media-review-required",
    }
)
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,127}$")
_MACHINE_REASON_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[/\\]")
_CREDENTIAL_VALUE_RE = re.compile(
    r"(?i)(?:bearer\s+[A-Za-z0-9._~+/=-]{8,}|"
    r"sk-(?:proj-)?[A-Za-z0-9_-]{16,}|"
    r"(?:password|passwd|secret|api[-_]?key|access[-_]?token|private[-_]?key)"
    r"\s*[:=]\s*\S+)"
)
_MACHINE_ABSOLUTE_PATH_RE = re.compile(
    r"(?m)(?:^|[\s\"'=(])(?:/[Uu]sers/|/home/|/private/(?:tmp|var)/|"
    r"[A-Za-z]:[/\\](?:Users|Documents and Settings)[/\\])"
)


class DocumentationClaimEvidenceError(ValueError):
    """Raised when an evidence record is malformed or does not reconcile."""


def normalize_claim_evidence_records(value: object) -> tuple[dict[str, Any], ...]:
    """Strictly validate and deterministically order claim-evidence records."""

    records = _object_array(value, "claim_evidence")
    normalized = tuple(
        _normalize_claim_record(record, f"claim_evidence[{index}]")
        for index, record in enumerate(records)
    )
    identifiers = [record["claim_id"] for record in normalized]
    if len(set(identifiers)) != len(identifiers):
        raise DocumentationClaimEvidenceError(
            "claim_evidence contains duplicate claim_id values."
        )
    return tuple(sorted(normalized, key=lambda record: record["claim_id"]))


def normalize_runtime_capture_records(value: object) -> tuple[dict[str, Any], ...]:
    """Strictly validate and deterministically order runtime-capture records."""

    records = _object_array(value, "runtime_captures")
    normalized = tuple(
        _normalize_capture_record(record, f"runtime_captures[{index}]")
        for index, record in enumerate(records)
    )
    identifiers = [record["capture_id"] for record in normalized]
    if len(set(identifiers)) != len(identifiers):
        raise DocumentationClaimEvidenceError(
            "runtime_captures contains duplicate capture_id values."
        )
    return tuple(sorted(normalized, key=lambda record: record["capture_id"]))


def qualify_claim_evidence(
    service: DocumentationGraphQueryService,
    *,
    claim_id: str,
    canonical_page: str,
    concept_query: str,
    section_locator: str | None = None,
    graph_query: Mapping[str, Any] | None = None,
    safe_evidence_link: str | None = None,
    internal_evidence_ref: str | None = None,
) -> dict[str, Any]:
    """Build the current supported qualification for one claim.

    The caller supplies identity and query intent; every native assertion and
    bound in the returned record is recomputed from the already-built service.
    """

    normalized_claim_id = _identifier(claim_id, "claim_id")
    page = _portable_path(canonical_page, "canonical_page", suffix=".md")
    query = _text(concept_query, "concept_query")
    section = (
        _section_locator(section_locator, "section_locator")
        if section_locator is not None
        else None
    )
    graph = _normalize_graph_query(graph_query, "graph_query")
    link = _safe_evidence_link(
        safe_evidence_link or page,
        canonical_page=page,
        field_name="safe_evidence_link",
    )
    internal_ref = (
        _internal_evidence_ref(internal_evidence_ref, "internal_evidence_ref")
        if internal_evidence_ref is not None
        else None
    )

    selection = service.get_concept(query)
    knowledge = _mapping(selection.get("knowledge"), "knowledge")
    availability = str(knowledge.get("availability") or "")
    concept = selection.get("concept")
    if availability != "ready":
        resolution = "native-unavailable"
        selected: Mapping[str, Any] | None = None
    elif bool(selection.get("ambiguous")):
        resolution = "ambiguous"
        selected = None
    elif bool(selection.get("found")) and isinstance(concept, Mapping):
        resolution = "exact"
        selected = concept
    else:
        resolution = "missing"
        selected = None

    freshness_evaluated = bool(knowledge.get("freshness_evaluated", False))
    freshness_value = (
        _mapping(selected.get("freshness"), "concept.freshness")
        if selected is not None
        else {}
    )
    freshness = {
        "evaluated": freshness_evaluated,
        "state": (
            freshness_value.get("state") if freshness_evaluated else None
        ),
        "reason": str(
            freshness_value.get("reason")
            or (
                "freshness-not-evaluated"
                if not freshness_evaluated
                else "freshness-result-unavailable"
            )
        ),
    }
    evidence_state = selected.get("evidence") if selected is not None else None
    structural_evidence = {
        "state": evidence_state,
        "reason": (
            None
            if evidence_state is not None
            else str(knowledge.get("reason") or "native-result-unavailable")
        ),
    }
    lifecycle_review, section_bounds = _current_lifecycle_review(
        service,
        query=query,
        selected=selected,
        section_locator=section,
    )
    bounds: dict[str, Any] = {
        "matches": _bound(selection, "matches"),
        "sections": section_bounds,
        "edges": None,
        "analyzers": [],
    }
    if graph is not None and graph["limit"] != service.limit:
        raise DocumentationClaimEvidenceError(
            f"claim {normalized_claim_id!r} graph_query.limit must match the "
            "operation-scoped native query service limit."
        )
    graph_resolution = resolution
    if graph is not None and resolution == "exact":
        traversal = service.traverse_typed_graph(
            query,
            direction=graph["direction"],
            kinds=graph["kinds"],
            origins=graph["origins"],
            resolutions=graph["resolutions"],
            include_evidence=False,
        )
        typed_status = _mapping(traversal.get("typed_graph"), "typed_graph")
        if typed_status.get("availability") != "ready":
            graph_resolution = "typed-graph-unavailable"
        bounds["edges"] = _bound(traversal, "edges")
        bounds["analyzers"] = _analyzer_bounds(typed_status.get("coverage"))

    record: dict[str, Any] = {
        "schema_version": CLAIM_EVIDENCE_SCHEMA_VERSION,
        "claim_id": normalized_claim_id,
        "canonical_page": page,
        "concept_query": query,
        "resolution": graph_resolution,
        "concept_uid": selected.get("uid") if selected is not None else None,
        "concept_locator": (
            selected.get("locator") if selected is not None else None
        ),
        "section_locator": section,
        "structural_evidence": structural_evidence,
        "freshness": freshness,
        "lifecycle_review": lifecycle_review,
        "graph_query": graph,
        "bounds": bounds,
        "safe_evidence_link": link,
        "internal_evidence_ref": internal_ref,
    }
    if selected is not None and selected.get("canonical_path") != page:
        # Preserve the requested output page in the exception so a worker
        # cannot silently bind a claim to a different canonical document.
        raise DocumentationClaimEvidenceError(
            f"claim {normalized_claim_id!r} canonical_page {page!r} does not "
            f"match the current concept page {selected.get('canonical_path')!r}."
        )
    return record


def reconcile_claim_evidence_records(
    records: Iterable[Mapping[str, Any]],
    service: DocumentationGraphQueryService,
) -> tuple[dict[str, Any], ...]:
    """Recompute every worker assertion and reject any current-view mismatch."""

    reconciled: list[dict[str, Any]] = []
    for raw in records:
        record = _normalize_claim_record(raw, "claim_evidence")
        expected = qualify_claim_evidence(
            service,
            claim_id=record["claim_id"],
            canonical_page=record["canonical_page"],
            concept_query=record["concept_query"],
            section_locator=record.get("section_locator"),
            graph_query=record.get("graph_query"),
            safe_evidence_link=record["safe_evidence_link"],
            internal_evidence_ref=record.get("internal_evidence_ref"),
        )
        if record != expected:
            mismatch = next(
                (
                    field
                    for field in sorted(_CLAIM_FIELDS)
                    if record.get(field) != expected.get(field)
                ),
                "record",
            )
            raise DocumentationClaimEvidenceError(
                f"claim {record['claim_id']!r} does not match the current "
                f"committed native view at {mismatch}."
            )
        reconciled.append(expected)
    return tuple(sorted(reconciled, key=lambda item: item["claim_id"]))


def reconcile_runtime_capture_records(
    records: Iterable[Mapping[str, Any]],
    *,
    wiki_root: str | Path,
    service: DocumentationGraphQueryService | None,
) -> tuple[dict[str, Any], ...]:
    """Verify persisted capture bytes and append current identity reconciliation."""

    root = Path(wiki_root).resolve()
    reconciled: list[dict[str, Any]] = []
    for raw in records:
        record = _normalize_capture_record(raw, "runtime_captures")
        capture_path = record["capture_path"]
        if record["result"]["state"] != "deferred":
            assert isinstance(capture_path, str)
            path = root / PurePosixPath(capture_path)
            if path.is_symlink():
                raise DocumentationClaimEvidenceError(
                    f"runtime capture path must not be a symlink: {capture_path}"
                )
            try:
                resolved = path.resolve(strict=True)
            except OSError as exc:
                raise DocumentationClaimEvidenceError(
                    f"runtime capture {record['capture_id']!r} is missing: "
                    f"{capture_path}"
                ) from exc
            if (
                not resolved.is_relative_to(root)
                or not resolved.is_file()
            ):
                raise DocumentationClaimEvidenceError(
                    f"runtime capture path is not a regular wiki file: {capture_path}"
                )
            digest = "sha256:" + hashlib.sha256(resolved.read_bytes()).hexdigest()
            if digest != record["capture_digest"]:
                raise DocumentationClaimEvidenceError(
                    f"runtime capture {record['capture_id']!r} digest does not "
                    "match the persisted redacted bytes."
                )
            _validate_runtime_capture_content(
                resolved,
                capture_id=record["capture_id"],
            )

        current = {
            "resolution": "native-unavailable",
            "uid": None,
            "locator": None,
            "section_state": "not-evaluated",
        }
        if service is not None:
            concept_uid = record.get("concept_uid")
            concept_locator = record.get("concept_locator")
            if isinstance(concept_uid, str) and isinstance(concept_locator, str):
                uid_selection = service.get_concept(concept_uid)
                locator_selection = service.get_concept(concept_locator)
                selections = (uid_selection, locator_selection)
                if all(
                    isinstance(selection.get("knowledge"), Mapping)
                    and selection["knowledge"].get("availability") == "ready"
                    for selection in selections
                ):
                    resolved = [
                        selection.get("concept")
                        if selection.get("found") is True
                        and selection.get("ambiguous") is False
                        and isinstance(selection.get("concept"), Mapping)
                        else None
                        for selection in selections
                    ]
                    if (
                        any(concept is None for concept in resolved)
                        or resolved[0].get("locator")
                        != resolved[1].get("locator")
                    ):
                        raise DocumentationClaimEvidenceError(
                            f"runtime capture {record['capture_id']!r} concept_uid "
                            "and concept_locator do not resolve to the same "
                            "current concept."
                        )
            query = concept_uid or concept_locator
            if isinstance(query, str):
                selected = service.get_concept(query)
                concept = selected.get("concept")
                if bool(selected.get("ambiguous")):
                    current["resolution"] = "ambiguous"
                elif bool(selected.get("found")) and isinstance(concept, Mapping):
                    current.update(
                        {
                            "resolution": "exact",
                            "uid": concept.get("uid"),
                            "locator": concept.get("locator"),
                            "section_state": _capture_section_state(
                                service,
                                query,
                                record.get("section_locator"),
                            ),
                        }
                    )
                elif (
                    isinstance(selected.get("knowledge"), Mapping)
                    and selected["knowledge"].get("availability") == "ready"
                ):
                    current["resolution"] = "missing"
        reconciled.append({**record, "reconciliation": current})
    return tuple(sorted(reconciled, key=lambda item: item["capture_id"]))


def _normalize_claim_record(value: object, field_name: str) -> dict[str, Any]:
    record = _mapping(value, field_name)
    _exact_fields(record, _CLAIM_FIELDS, _CLAIM_REQUIRED, field_name)
    if record["schema_version"] != CLAIM_EVIDENCE_SCHEMA_VERSION:
        raise DocumentationClaimEvidenceError(
            f"{field_name}.schema_version is unsupported."
        )
    page = _portable_path(record["canonical_page"], f"{field_name}.canonical_page", suffix=".md")
    resolution = _enum(record["resolution"], _RESOLUTIONS, f"{field_name}.resolution")
    concept_uid = _optional_identifier(record.get("concept_uid"), f"{field_name}.concept_uid")
    concept_locator = _optional_locator(
        record.get("concept_locator"), f"{field_name}.concept_locator"
    )
    if resolution == "exact" and concept_uid is None and concept_locator is None:
        raise DocumentationClaimEvidenceError(
            f"{field_name} exact resolution requires concept_uid or concept_locator."
        )
    section = (
        _section_locator(record.get("section_locator"), f"{field_name}.section_locator")
        if record.get("section_locator") is not None
        else None
    )
    return {
        "schema_version": CLAIM_EVIDENCE_SCHEMA_VERSION,
        "claim_id": _identifier(record["claim_id"], f"{field_name}.claim_id"),
        "canonical_page": page,
        "concept_query": _text(record["concept_query"], f"{field_name}.concept_query"),
        "resolution": resolution,
        "concept_uid": concept_uid,
        "concept_locator": concept_locator,
        "section_locator": section,
        "structural_evidence": _structural_evidence(
            record["structural_evidence"], f"{field_name}.structural_evidence"
        ),
        "freshness": _freshness(record["freshness"], f"{field_name}.freshness"),
        "lifecycle_review": _lifecycle_review(
            record.get("lifecycle_review"), f"{field_name}.lifecycle_review"
        ),
        "graph_query": _normalize_graph_query(
            record.get("graph_query"), f"{field_name}.graph_query"
        ),
        "bounds": _bounds(record["bounds"], f"{field_name}.bounds"),
        "safe_evidence_link": _safe_evidence_link(
            record["safe_evidence_link"],
            canonical_page=page,
            field_name=f"{field_name}.safe_evidence_link",
        ),
        "internal_evidence_ref": (
            _internal_evidence_ref(
                record.get("internal_evidence_ref"),
                f"{field_name}.internal_evidence_ref",
            )
            if record.get("internal_evidence_ref") is not None
            else None
        ),
    }


def _normalize_capture_record(value: object, field_name: str) -> dict[str, Any]:
    record = _mapping(value, field_name)
    _exact_fields(record, _CAPTURE_FIELDS, _CAPTURE_REQUIRED, field_name)
    if record["schema_version"] != RUNTIME_CAPTURE_SCHEMA_VERSION:
        raise DocumentationClaimEvidenceError(
            f"{field_name}.schema_version is unsupported."
        )
    result = _capture_result(record["result"], f"{field_name}.result")
    capture_path = (
        _runtime_capture_path(
            record["capture_path"],
            f"{field_name}.capture_path",
        )
        if record["capture_path"] is not None
        else None
    )
    digest = record["capture_digest"]
    if result["state"] == "deferred":
        if capture_path is not None or digest is not None:
            raise DocumentationClaimEvidenceError(
                f"{field_name} deferred capture must not claim persisted bytes."
            )
    elif capture_path is None or not is_valid_sha256(digest):
        raise DocumentationClaimEvidenceError(
            f"{field_name} captured/failed result requires a path and SHA-256 digest."
        )
    native = _native_observation(
        record["native_observation"], f"{field_name}.native_observation"
    )
    redaction = _redaction(record["redaction"], f"{field_name}.redaction")
    environment = _environment(record["environment"], f"{field_name}.environment")
    if (
        redaction["outcome"] == "rejected"
        or environment["mode"] == "unavailable"
    ) and result["state"] != "deferred":
        raise DocumentationClaimEvidenceError(
            f"{field_name} rejected/unavailable capture must be deferred."
        )
    normalized = {
        "schema_version": RUNTIME_CAPTURE_SCHEMA_VERSION,
        "capture_id": _identifier(record["capture_id"], f"{field_name}.capture_id"),
        "capture_digest": digest,
        "capture_path": capture_path,
        "command_or_flow_id": _text(
            record["command_or_flow_id"], f"{field_name}.command_or_flow_id"
        ),
        "result": result,
        "concept_uid": _optional_identifier(
            record["concept_uid"], f"{field_name}.concept_uid"
        ),
        "concept_locator": _optional_locator(
            record["concept_locator"], f"{field_name}.concept_locator"
        ),
        "section_locator": (
            _section_locator(
                record["section_locator"], f"{field_name}.section_locator"
            )
            if record["section_locator"] is not None
            else None
        ),
        "native_observation": native,
        "redaction": redaction,
        "environment": environment,
        "limitations": _string_list(
            record["limitations"], f"{field_name}.limitations"
        ),
    }
    if normalized["concept_uid"] is None and normalized["concept_locator"] is None:
        raise DocumentationClaimEvidenceError(
            f"{field_name} requires concept_uid or concept_locator."
        )
    if (
        capture_path is not None
        and PurePosixPath(capture_path).suffix.casefold()
        in _UNINSPECTED_MEDIA_SUFFIXES
    ):
        if redaction["outcome"] != "redacted":
            raise DocumentationClaimEvidenceError(
                f"{field_name} binary media must record a redacted outcome."
            )
        missing_limitations = _UNINSPECTED_MEDIA_LIMITATIONS - set(
            normalized["limitations"]
        )
        if missing_limitations:
            raise DocumentationClaimEvidenceError(
                f"{field_name} binary media must retain limitation "
                f"{min(missing_limitations)!r}."
            )
    _reject_sensitive_metadata(normalized, field_name)
    return normalized


def _current_lifecycle_review(
    service: DocumentationGraphQueryService,
    *,
    query: str,
    selected: Mapping[str, Any] | None,
    section_locator: str | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if selected is None:
        return None, None
    section_review: dict[str, Any] | None = None
    section_bounds: dict[str, Any] | None = None
    if section_locator is not None:
        list_sections = getattr(service, "list_concept_sections", None)
        if not callable(list_sections):
            raise DocumentationClaimEvidenceError(
                "The native query service does not expose section ownership."
            )
        section_result = list_sections(query)
        section_bounds = _bound(section_result, "sections")
        sections = section_result.get("sections", [])
        matching = [
            item
            for item in sections
            if isinstance(item, Mapping) and item.get("locator") == section_locator
        ]
        if not matching:
            section_review = {
                "state": (
                    "bounded-not-returned"
                    if section_bounds["truncated"]
                    else "missing"
                ),
                "reasons": [
                    (
                        "section-query-truncated"
                        if section_bounds["truncated"]
                        else "section-missing"
                    )
                ],
                "ownership": None,
            }
        else:
            section = matching[0]
            review = section.get("review")
            review_map = review if isinstance(review, Mapping) else {}
            section_review = {
                "state": str(review_map.get("state") or "unreviewed"),
                "reasons": sorted(
                    str(item) for item in review_map.get("reasons", []) or []
                ),
                "ownership": section.get("ownership"),
            }
    return (
        {
            "lifecycle": selected.get("lifecycle"),
            "section_review": section_review,
        },
        section_bounds,
    )


def _capture_section_state(
    service: DocumentationGraphQueryService,
    query: str,
    section_locator: object,
) -> str:
    if section_locator is None:
        return "not-requested"
    list_sections = getattr(service, "list_concept_sections", None)
    if not callable(list_sections):
        return "unsupported"
    result = list_sections(query)
    if any(
        isinstance(item, Mapping) and item.get("locator") == section_locator
        for item in result.get("sections", []) or []
    ):
        return "current"
    bounds = result.get("bounds")
    section_bounds = (
        bounds.get("sections") if isinstance(bounds, Mapping) else None
    )
    if isinstance(section_bounds, Mapping) and section_bounds.get("truncated") is True:
        return "bounded-not-returned"
    return "missing"


def _normalize_graph_query(
    value: object, field_name: str
) -> dict[str, Any] | None:
    if value is None:
        return None
    query = _mapping(value, field_name)
    _exact_fields(
        query,
        frozenset(
            {"direction", "kinds", "origins", "resolutions", "include_evidence", "limit"}
        ),
        frozenset(
            {"direction", "kinds", "origins", "resolutions", "include_evidence", "limit"}
        ),
        field_name,
    )
    direction = _enum(
        query["direction"],
        frozenset({"incoming", "outgoing", "both"}),
        f"{field_name}.direction",
    )
    include_evidence = query["include_evidence"]
    if include_evidence is not False:
        raise DocumentationClaimEvidenceError(
            f"{field_name}.include_evidence must be false; detailed evidence "
            "belongs only in internal run evidence."
        )
    limit = query["limit"]
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise DocumentationClaimEvidenceError(
            f"{field_name}.limit must be an integer from 1 through 100."
        )
    return {
        "direction": direction,
        "kinds": _string_list(query["kinds"], f"{field_name}.kinds"),
        "origins": _string_list(query["origins"], f"{field_name}.origins"),
        "resolutions": _string_list(
            query["resolutions"], f"{field_name}.resolutions"
        ),
        "include_evidence": False,
        "limit": limit,
    }


def _structural_evidence(value: object, field_name: str) -> dict[str, Any]:
    evidence = _mapping(value, field_name)
    _exact_fields(
        evidence,
        frozenset({"state", "reason"}),
        frozenset({"state", "reason"}),
        field_name,
    )
    state = evidence["state"]
    if state is not None:
        state = _enum(state, _EVIDENCE_STATES, f"{field_name}.state")
    reason = evidence["reason"]
    if reason is not None:
        reason = _reason(reason, f"{field_name}.reason")
    return {"state": state, "reason": reason}


def _freshness(value: object, field_name: str) -> dict[str, Any]:
    freshness = _mapping(value, field_name)
    _exact_fields(
        freshness,
        frozenset({"evaluated", "state", "reason"}),
        frozenset({"evaluated", "state", "reason"}),
        field_name,
    )
    evaluated = freshness["evaluated"]
    if not isinstance(evaluated, bool):
        raise DocumentationClaimEvidenceError(
            f"{field_name}.evaluated must be a boolean."
        )
    state = freshness["state"]
    if state is not None:
        state = _enum(state, _FRESHNESS_STATES, f"{field_name}.state")
    if not evaluated and state is not None:
        raise DocumentationClaimEvidenceError(
            f"{field_name}.state must be null when freshness was not evaluated."
        )
    return {
        "evaluated": evaluated,
        "state": state,
        "reason": _reason(freshness["reason"], f"{field_name}.reason"),
    }


def _lifecycle_review(value: object, field_name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    item = _mapping(value, field_name)
    _exact_fields(
        item,
        frozenset({"lifecycle", "section_review"}),
        frozenset({"lifecycle", "section_review"}),
        field_name,
    )
    section = item["section_review"]
    normalized_section = None
    if section is not None:
        section_map = _mapping(section, f"{field_name}.section_review")
        _exact_fields(
            section_map,
            frozenset({"state", "reasons", "ownership"}),
            frozenset({"state", "reasons", "ownership"}),
            f"{field_name}.section_review",
        )
        ownership = section_map["ownership"]
        if ownership is not None:
            ownership = _enum(
                ownership,
                _OWNERSHIP_STATES,
                f"{field_name}.section_review.ownership",
            )
        normalized_section = {
            "state": _reason(
                section_map["state"], f"{field_name}.section_review.state"
            ),
            "reasons": _string_list(
                section_map["reasons"], f"{field_name}.section_review.reasons"
            ),
            "ownership": ownership,
        }
    lifecycle = item["lifecycle"]
    if lifecycle is not None:
        lifecycle = _reason(lifecycle, f"{field_name}.lifecycle")
    return {"lifecycle": lifecycle, "section_review": normalized_section}


def _bounds(value: object, field_name: str) -> dict[str, Any]:
    bounds = _mapping(value, field_name)
    _exact_fields(
        bounds,
        frozenset({"matches", "sections", "edges", "analyzers"}),
        frozenset({"matches", "sections", "edges", "analyzers"}),
        field_name,
    )
    return {
        "matches": _bound_record(bounds["matches"], f"{field_name}.matches"),
        "sections": (
            _bound_record(bounds["sections"], f"{field_name}.sections")
            if bounds["sections"] is not None
            else None
        ),
        "edges": (
            _bound_record(bounds["edges"], f"{field_name}.edges")
            if bounds["edges"] is not None
            else None
        ),
        "analyzers": _analyzer_bounds(bounds["analyzers"]),
    }


def _bound(result: Mapping[str, Any], path: str) -> dict[str, Any]:
    bounds = result.get("bounds")
    selected = bounds.get(path) if isinstance(bounds, Mapping) else None
    return _bound_record(selected, f"bounds.{path}")


def _bound_record(value: object, field_name: str) -> dict[str, Any]:
    bound = _mapping(value, field_name)
    _exact_fields(
        bound,
        frozenset({"total", "returned", "truncated"}),
        frozenset({"total", "returned", "truncated"}),
        field_name,
    )
    total = _nonnegative_int(bound["total"], f"{field_name}.total")
    returned = _nonnegative_int(bound["returned"], f"{field_name}.returned")
    truncated = bound["truncated"]
    if not isinstance(truncated, bool) or returned > total or truncated != (
        returned < total
    ):
        raise DocumentationClaimEvidenceError(
            f"{field_name} contains inconsistent bound values."
        )
    return {"total": total, "returned": returned, "truncated": truncated}


def _analyzer_bounds(value: object) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise DocumentationClaimEvidenceError(
            "analyzer coverage must be an array."
        )
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        item = _mapping(raw, f"analyzers[{index}]")
        required = {
            "analyzer",
            "observed",
            "emitted",
            "omitted",
            "limit",
            "truncated",
            "limitations",
        }
        _exact_fields(item, frozenset(required), frozenset(required), f"analyzers[{index}]")
        observed = _nonnegative_int(item["observed"], "analyzer.observed")
        emitted = _nonnegative_int(item["emitted"], "analyzer.emitted")
        omitted = _nonnegative_int(item["omitted"], "analyzer.omitted")
        limit = item["limit"]
        if limit is not None:
            limit = _nonnegative_int(limit, "analyzer.limit")
        truncated = item["truncated"]
        if (
            not isinstance(truncated, bool)
            or emitted + omitted != observed
            or truncated != (omitted > 0)
        ):
            raise DocumentationClaimEvidenceError(
                "analyzer coverage contains inconsistent counts."
            )
        normalized.append(
            {
                "analyzer": _text(item["analyzer"], "analyzer.analyzer"),
                "observed": observed,
                "emitted": emitted,
                "omitted": omitted,
                "limit": limit,
                "truncated": truncated,
                "limitations": _string_list(
                    item["limitations"], "analyzer.limitations"
                ),
            }
        )
    return sorted(normalized, key=lambda item: item["analyzer"])


def _capture_result(value: object, field_name: str) -> dict[str, Any]:
    result = _mapping(value, field_name)
    _exact_fields(
        result,
        frozenset({"state", "exit_code"}),
        frozenset({"state", "exit_code"}),
        field_name,
    )
    state = _enum(result["state"], _CAPTURE_STATES, f"{field_name}.state")
    exit_code = result["exit_code"]
    if exit_code is not None and (
        isinstance(exit_code, bool) or not isinstance(exit_code, int)
    ):
        raise DocumentationClaimEvidenceError(
            f"{field_name}.exit_code must be an integer or null."
        )
    if state == "deferred" and exit_code is not None:
        raise DocumentationClaimEvidenceError(
            f"{field_name}.exit_code must be null for a deferred capture."
        )
    if state != "deferred" and exit_code is None:
        raise DocumentationClaimEvidenceError(
            f"{field_name}.exit_code must be an integer for a completed capture "
            "attempt."
        )
    return {"state": state, "exit_code": exit_code}


def _native_observation(value: object, field_name: str) -> dict[str, Any]:
    native = _mapping(value, field_name)
    _exact_fields(
        native,
        frozenset(
            {
                "availability",
                "reason",
                "structural_evidence_state",
                "freshness_evaluated",
                "freshness_state",
                "freshness_reason",
            }
        ),
        frozenset(
            {
                "availability",
                "reason",
                "structural_evidence_state",
                "freshness_evaluated",
                "freshness_state",
                "freshness_reason",
            }
        ),
        field_name,
    )
    availability = _enum(
        native["availability"], _AVAILABILITY_STATES, f"{field_name}.availability"
    )
    evaluated = native["freshness_evaluated"]
    if not isinstance(evaluated, bool):
        raise DocumentationClaimEvidenceError(
            f"{field_name}.freshness_evaluated must be a boolean."
        )
    evidence = native["structural_evidence_state"]
    freshness_state = native["freshness_state"]
    if evidence is not None:
        evidence = _enum(evidence, _EVIDENCE_STATES, f"{field_name}.structural_evidence_state")
    if freshness_state is not None:
        freshness_state = _enum(
            freshness_state, _FRESHNESS_STATES, f"{field_name}.freshness_state"
        )
    if availability != "ready" and (evidence is not None or evaluated):
        raise DocumentationClaimEvidenceError(
            f"{field_name} unavailable native state cannot claim evidence or "
            "evaluated freshness."
        )
    if not evaluated and freshness_state is not None:
        raise DocumentationClaimEvidenceError(
            f"{field_name}.freshness_state must be null when not evaluated."
        )
    return {
        "availability": availability,
        "reason": _reason(native["reason"], f"{field_name}.reason"),
        "structural_evidence_state": evidence,
        "freshness_evaluated": evaluated,
        "freshness_state": freshness_state,
        "freshness_reason": _reason(
            native["freshness_reason"], f"{field_name}.freshness_reason"
        ),
    }


def _redaction(value: object, field_name: str) -> dict[str, Any]:
    redaction = _mapping(value, field_name)
    _exact_fields(
        redaction,
        frozenset({"outcome", "limitations"}),
        frozenset({"outcome", "limitations"}),
        field_name,
    )
    return {
        "outcome": _enum(
            redaction["outcome"], _REDACTION_STATES, f"{field_name}.outcome"
        ),
        "limitations": _string_list(
            redaction["limitations"], f"{field_name}.limitations"
        ),
    }


def _environment(value: object, field_name: str) -> dict[str, Any]:
    environment = _mapping(value, field_name)
    _exact_fields(
        environment,
        frozenset({"mode", "limitations"}),
        frozenset({"mode", "limitations"}),
        field_name,
    )
    return {
        "mode": _enum(
            environment["mode"], _ENVIRONMENT_MODES, f"{field_name}.mode"
        ),
        "limitations": _string_list(
            environment["limitations"], f"{field_name}.limitations"
        ),
    }


def _safe_evidence_link(
    value: object, *, canonical_page: str, field_name: str
) -> str:
    link = _text(value, field_name)
    if "?" in link:
        raise DocumentationClaimEvidenceError(
            f"{field_name} must not contain a query string."
        )
    page, separator, fragment = link.partition("#")
    normalized_page = _portable_path(page, field_name, suffix=".md")
    if normalized_page != canonical_page:
        raise DocumentationClaimEvidenceError(
            f"{field_name} must target canonical_page."
        )
    if separator and (not fragment or any(ord(char) < 0x20 for char in fragment)):
        raise DocumentationClaimEvidenceError(
            f"{field_name} contains an invalid fragment."
        )
    return link


def _internal_evidence_ref(value: object, field_name: str) -> str:
    path = _portable_path(value, field_name)
    if not path.startswith(".llm-wiki-docs/evidence/"):
        raise DocumentationClaimEvidenceError(
            f"{field_name} must stay under .llm-wiki-docs/evidence/."
        )
    return path


def _portable_path(
    value: object, field_name: str, *, suffix: str | None = None
) -> str:
    text = _text(value, field_name)
    path = PurePosixPath(text)
    if (
        "\\" in text
        or path.is_absolute()
        or _WINDOWS_DRIVE_RE.match(text)
        or path.as_posix() != text
        or any(part in {"", ".", ".."} for part in path.parts)
        or (suffix is not None and not text.casefold().endswith(suffix))
    ):
        raise DocumentationClaimEvidenceError(
            f"{field_name} must be a portable repository-relative path."
        )
    return text


def _runtime_capture_path(value: object, field_name: str) -> str:
    text = _portable_path(value, field_name)
    path = PurePosixPath(text)
    if (
        len(path.parts) < 3
        or path.parts[0] != "assets"
        or path.suffix.casefold() not in _RUNTIME_CAPTURE_SUFFIXES
    ):
        raise DocumentationClaimEvidenceError(
            f"{field_name} must use a supported file under assets/<surface>/."
        )
    return text


def _section_locator(value: object, field_name: str) -> str:
    locator = _text(value, field_name)
    if "#section/" not in locator or not locator.startswith("llm-wiki://"):
        raise DocumentationClaimEvidenceError(
            f"{field_name} must be an exact native section locator."
        )
    return locator


def _optional_locator(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    locator = _text(value, field_name)
    if not locator.startswith("llm-wiki://"):
        raise DocumentationClaimEvidenceError(
            f"{field_name} must be an exact native locator."
        )
    return locator


def _optional_identifier(value: object, field_name: str) -> str | None:
    return None if value is None else _identifier(value, field_name)


def _identifier(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    if _SAFE_ID_RE.fullmatch(text) is None:
        raise DocumentationClaimEvidenceError(
            f"{field_name} must be a stable portable identifier."
        )
    return text


def _reason(value: object, field_name: str) -> str:
    text = _text(value, field_name)
    if _MACHINE_REASON_RE.fullmatch(text) is None:
        raise DocumentationClaimEvidenceError(
            f"{field_name} must be a lowercase hyphen-separated reason."
        )
    return text


def _enum(value: object, allowed: frozenset[str], field_name: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise DocumentationClaimEvidenceError(
            f"{field_name} must be one of {', '.join(sorted(allowed))}."
        )
    return value


def _text(value: object, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(char) < 0x20 for char in value)
    ):
        raise DocumentationClaimEvidenceError(
            f"{field_name} must be non-empty normalized text."
        )
    return value


def _string_list(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise DocumentationClaimEvidenceError(f"{field_name} must be an array.")
    items = [_text(item, f"{field_name}[]") for item in value]
    if len(set(items)) != len(items):
        raise DocumentationClaimEvidenceError(
            f"{field_name} must not contain duplicates."
        )
    return sorted(items)


def _nonnegative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DocumentationClaimEvidenceError(
            f"{field_name} must be a non-negative integer."
        )
    return value


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) for key in value
    ):
        raise DocumentationClaimEvidenceError(f"{field_name} must be an object.")
    return value


def _object_array(value: object, field_name: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise DocumentationClaimEvidenceError(f"{field_name} must be an array.")
    return [_mapping(item, f"{field_name}[]") for item in value]


def _exact_fields(
    value: Mapping[str, Any],
    allowed: frozenset[str],
    required: frozenset[str],
    field_name: str,
) -> None:
    missing = required - set(value)
    unknown = set(value) - allowed
    if missing:
        raise DocumentationClaimEvidenceError(
            f"{field_name}.{min(missing)} is required."
        )
    if unknown:
        raise DocumentationClaimEvidenceError(
            f"{field_name}.{min(unknown)} is not supported."
        )


def _reject_sensitive_metadata(value: object, field_name: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if re.search(
                r"(?i)(?:password|passwd|secret|api[-_]?key|access[-_]?token|"
                r"private[-_]?key|authorization|cookie|credential)",
                str(key),
            ):
                raise DocumentationClaimEvidenceError(
                    f"{field_name} contains credential-like metadata."
                )
            _reject_sensitive_metadata(item, field_name)
        return
    if isinstance(value, list):
        for item in value:
            _reject_sensitive_metadata(item, field_name)
        return
    if not isinstance(value, str):
        return
    if _CREDENTIAL_VALUE_RE.search(value):
        raise DocumentationClaimEvidenceError(
            f"{field_name} contains credential-like content."
        )
    parsed = urlsplit(value)
    if parsed.username is not None or parsed.password is not None:
        raise DocumentationClaimEvidenceError(
            f"{field_name} contains URI user information."
        )
    if _WINDOWS_DRIVE_RE.match(value) or value.startswith("/"):
        raise DocumentationClaimEvidenceError(
            f"{field_name} contains an absolute path."
        )


def _validate_runtime_capture_content(path: Path, *, capture_id: str) -> None:
    if path.suffix.casefold() not in {".json", ".log", ".md", ".svg", ".txt"}:
        return
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise DocumentationClaimEvidenceError(
            f"runtime capture {capture_id!r} uses a text format but is not UTF-8."
        ) from exc
    if _CREDENTIAL_VALUE_RE.search(text):
        raise DocumentationClaimEvidenceError(
            f"runtime capture {capture_id!r} contains credential-like content."
        )
    if _MACHINE_ABSOLUTE_PATH_RE.search(text):
        raise DocumentationClaimEvidenceError(
            f"runtime capture {capture_id!r} contains a machine-specific "
            "absolute path."
        )
    for match in re.finditer(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s<>'\"]+", text):
        parsed = urlsplit(match.group(0))
        if parsed.username is not None or parsed.password is not None:
            raise DocumentationClaimEvidenceError(
                f"runtime capture {capture_id!r} contains URI user information."
            )


__all__ = [
    "CLAIM_EVIDENCE_SCHEMA_VERSION",
    "RUNTIME_CAPTURE_SCHEMA_VERSION",
    "DocumentationClaimEvidenceError",
    "normalize_claim_evidence_records",
    "normalize_runtime_capture_records",
    "qualify_claim_evidence",
    "reconcile_claim_evidence_records",
    "reconcile_runtime_capture_records",
]
