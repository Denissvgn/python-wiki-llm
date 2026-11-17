"""Pure bounded discovery presentation over captured exact page observations."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
import re
from typing import Any, NoReturn

from .concept_identity import validate_locator
from .markdown_sections import parse_markdown_document
from .section_ownership import observe_page_sections
from .validation import is_portable_relative_path
from .wiki_surface import canonical_path, iter_page_kinds, mcp_uri, validate_exact_page_coordinate

DISCOVERY_SCHEMA_VERSION = "llm-wiki-discovery/v1"
MAX_DISCOVERY_BYTES = 262_144
MAX_NARRATIVE_SECTIONS = 8
MAX_SECTION_SNIPPET_CHARACTERS = 240
_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
_REVIEW_FIELDS = frozenset({
    "record_id", "target", "recorded_status", "mapping", "reasons", "acknowledgment",
    "history_bounds", "acknowledgment_history", "recorded_target_presence", "effective_status",
    "coordinate", "recorded_basis", "qualification", "governance_effect", "expected_basis", "basis_available",
    "source_location",
})
_REVIEW_REQUIRED = frozenset({"record_id", "target", "recorded_status", "mapping", "reasons"})
_BOUND_FIELDS = frozenset({"total", "returned", "truncated", "omitted", "limit", "max_records", "max_bytes"})


class DiscoveryError(ValueError):
    """Safe fixed diagnostics without reflecting captured content."""

    def __init__(self, code: str, field: str, *, required_bytes: int | None = None):
        self.code = code
        self.field = field
        self.required_bytes = required_bytes
        message = ("Discovery exceeds its serialized byte limit" if required_bytes is not None
                   else "Invalid captured discovery input: " + field)
        super().__init__(message)


def _invalid(field: str) -> NoReturn:
    raise DiscoveryError("discovery-invalid-input", field)


def _object(value, field) -> dict[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        _invalid(field)
    return dict(value)


def _hash(value, field, *, optional=False):
    if optional and value is None:
        return
    if not isinstance(value, str) or _SHA.fullmatch(value) is None:
        _invalid(field)


def _portable_source(value, field):
    if not isinstance(value, str) or not is_portable_relative_path(value):
        _invalid(field)
    return value


def _bounds(value, field) -> dict[str, Any]:
    bound = _object(value, field)
    if not {"total", "returned", "truncated"} <= set(bound) or set(bound) - _BOUND_FIELDS:
        _invalid(field)
    if (type(bound["total"]) is not int or type(bound["returned"]) is not int
            or not 0 <= bound["returned"] <= bound["total"]
            or type(bound["truncated"]) is not bool
            or bound["truncated"] != (bound["returned"] < bound["total"])):
        _invalid(field)
    for key in set(bound) - {"total", "returned", "truncated"}:
        if type(bound[key]) is not int or bound[key] < 0:
            _invalid(field)
    if "omitted" in bound and bound["omitted"] != bound["total"] - bound["returned"]:
        _invalid(field)
    return deepcopy(bound)


def _native(value) -> dict[str, Any]:
    native = _object(value, "native")
    fields = {"availability", "reason", "root_hash", "lookup_complete", "validation_scope",
              "whole_store_validated", "concepts"}
    if set(native) != fields or native["whole_store_validated"] is not False:
        _invalid("native")
    if (not isinstance(native["availability"], str)
            or (native["reason"] is not None and not isinstance(native["reason"], str))):
        _invalid("native")
    if type(native["lookup_complete"]) is not bool or not isinstance(native["concepts"], list):
        _invalid("native")
    if len(native["concepts"]) > 1000:
        _invalid("native.concepts")
    if native["availability"] == "scoped":
        _hash(native["root_hash"], "native.root_hash")
        if native["reason"] is not None or not isinstance(native["validation_scope"], str) or native["validation_scope"] not in {
            "selected-committed-records", "selected-committed-collections",
        }:
            _invalid("native.scope")
    elif native["availability"] == "unavailable":
        if (native["concepts"] or native["root_hash"] is not None or native["lookup_complete"]
                or not isinstance(native["reason"], str) or not native["reason"]):
            _invalid("native.unavailable")
    else:
        _invalid("native.availability")
    return native


def _reviews(value) -> dict[str, Any]:
    reviews = _object(value, "recorded_reviews")
    if set(reviews) != {"availability", "reason", "adoption_id", "state_hash", "by_path"}:
        _invalid("recorded_reviews")
    if (not isinstance(reviews["availability"], str)
            or (reviews["reason"] is not None and not isinstance(reviews["reason"], str))):
        _invalid("recorded_reviews")
    reviews["by_path"] = _object(reviews["by_path"], "recorded_reviews.by_path")
    if reviews["availability"] == "ready":
        _hash(reviews["state_hash"], "recorded_reviews.state_hash")
        if not isinstance(reviews["adoption_id"], str) or not reviews["adoption_id"] or reviews["reason"] is not None:
            _invalid("recorded_reviews.binding")
    elif reviews["availability"] in {"unadopted", "unavailable"}:
        if reviews["by_path"] or reviews["state_hash"] is not None or reviews["adoption_id"] is not None:
            _invalid("recorded_reviews.unavailable")
        if reviews["availability"] == "unavailable" and not reviews["reason"]:
            _invalid("recorded_reviews.reason")
    else:
        _invalid("recorded_reviews.availability")
    return reviews


def _recorded_review(path: str, reviews) -> dict[str, Any]:
    if path not in reviews["by_path"]:
        return {"availability": "unavailable" if reviews["availability"] == "ready" else reviews["availability"],
                "reason": "no-recorded-review-for-exact-page" if reviews["availability"] == "ready" else reviews["reason"],
                "basis": "snapshot", "live_evaluation_performed": False}
    report = _object(reviews["by_path"][path], "recorded_review")
    if set(report) != {"records", "bounds"} or not isinstance(report["records"], list):
        _invalid("recorded_review")
    bound = _bounds(report["bounds"], "recorded_review.bounds")
    if bound["returned"] != len(report["records"]):
        _invalid("recorded_review.bounds")
    ids = set()
    for value in report["records"]:
        row = _object(value, "recorded_review.record")
        if not _REVIEW_REQUIRED <= set(row) or set(row) - _REVIEW_FIELDS or row.get("effective_status") is not None:
            _invalid("recorded_review.record")
        if (row.get("qualification", "snapshot") != "snapshot" or row.get("governance_effect", "none") != "none"
                or row.get("expected_basis") is not None or row.get("basis_available", False) is not False):
            _invalid("recorded_review.current_claim")
        if not isinstance(row["record_id"], str) or not row["record_id"] or row["record_id"] in ids:
            _invalid("recorded_review.record_id")
        ids.add(row["record_id"])
        target = _object(row["target"], "recorded_review.target")
        mapping = _object(row["mapping"], "recorded_review.mapping")
        candidates = mapping.get("candidates", [])
        if not isinstance(candidates, list):
            _invalid("recorded_review.mapping")
        associated = target.get("canonical_path") == path
        for candidate in candidates:
            item = _object(candidate, "recorded_review.mapping_candidate")
            selected = _object(item.get("target"), "recorded_review.mapping_target")
            associated |= selected.get("canonical_path") == path
        if not associated:
            _invalid("recorded_review.target")
        if "history_bounds" in row:
            history_bound = _bounds(row["history_bounds"], "recorded_review.history_bounds")
            history = row.get("acknowledgment_history", [])
            if not isinstance(history, list) or history_bound["returned"] != len(history):
                _invalid("recorded_review.history_bounds")
        if "source_location" in row:
            location = _object(row["source_location"], "recorded_review.source_location")
            if location.get("qualification") not in {"captured", "not-observed"}:
                _invalid("recorded_review.source_location")
    return {"availability": "recorded", "basis": "snapshot", "live_evaluation_performed": False,
            "records": deepcopy(report["records"]), "bounds": bound}


def _native_member(path, native):
    concepts = []
    seen = set()
    for value in native["concepts"]:
        concept = _object(value, "native.concept")
        document = _object(concept.get("document"), "native.document")
        if document.get("canonical_path") != path:
            continue
        locator = concept.get("locator")
        try:
            validate_locator(locator)
        except (TypeError, ValueError):
            _invalid("native.locator")
        if locator in seen:
            _invalid("native.duplicate_locator")
        seen.add(locator)
        concepts.append(concept)
    concepts.sort(key=lambda item: item["locator"])
    complete = native["lookup_complete"]
    total = len(concepts) if complete else None
    state = ("unavailable" if native["availability"] == "unavailable" or not complete
             else "unique" if len(concepts) == 1 else "ambiguous" if concepts else "missing")
    concept = concepts[0] if state == "unique" else None
    basis = _basis(concept) if concept else {}
    _hash(basis.get("source_content_hash"), "native.source_content_hash", optional=True)
    semantics = _object(concept["facets"].get("semantics"), "native.semantics") if concept else {}
    descriptor = {"state": state, "reason": native["reason"] if native["availability"] == "unavailable"
                  else "native-lookup-incomplete" if not complete else None,
                  "locator": concept["locator"] if concept else None,
                  "matches": [item["locator"] for item in concepts],
                  "bounds": {"total": total, "returned": len(concepts), "truncated": not complete,
                             "total_known": complete},
                  "source_content_hash": basis.get("source_content_hash"),
                  "recorded_verification": deepcopy(semantics.get("verification")),
                  "recorded_lifecycle": deepcopy(concept.get("lifecycle")) if concept else None}
    return descriptor, concepts


def _basis(concept):
    facets = _object(concept.get("facets"), "native.facets")
    structure = _object(facets.get("structure"), "native.structure")
    return _object(structure.get("basis") or {}, "native.basis")


def _owner(path, mappings, native, concepts):
    mapping = None if path not in mappings else _object(mappings[path], "owner_mapping")
    sources = set()
    if mapping is not None:
        if mapping.get("scope") not in {"module", "entity"}:
            _invalid("owner_mapping.scope")
        sources.add(_portable_source(mapping.get("source_path"), "owner_mapping.source_path"))
    for concept in concepts:
        source = _basis(concept)
        if source.get("source_path") is not None:
            sources.add(_portable_source(source["source_path"], "native.source_path"))
    if len(sources) > 1:
        return {"state": "conflicting", "source_path": None, "mapping": deepcopy(mapping),
                "conflicting_sources": sorted(sources)}, ("page", path)
    if sources and (mapping is not None or native["state"] == "unique"):
        source = next(iter(sources))
        return {"state": "owned-source", "source_path": source, "mapping": deepcopy(mapping)}, ("source", source)
    state = "concept-only" if native["state"] == "unique" else "page-only"
    return {"state": state, "source_path": None, "mapping": None}, ("concept", native["locator"]) if state == "concept-only" else ("page", path)


def _recorded_source(mapping):
    if mapping is None or "recorded_source" not in mapping:
        return None
    source = _object(mapping["recorded_source"], "recorded_source")
    fields = {"basis", "source_content_hash", "availability", "live_comparison_performed"}
    if not fields <= set(source) or set(source) - fields - {"tombstone"}:
        _invalid("recorded_source")
    if (source["basis"] != "manifest-snapshot" or source["live_comparison_performed"] is not False
            or source["availability"] not in {"recorded", "unrecorded"}):
        _invalid("recorded_source")
    _hash(source["source_content_hash"], "recorded_source.hash", optional=source["availability"] == "unrecorded")
    if source["availability"] == "unrecorded" and source["source_content_hash"] is not None:
        _invalid("recorded_source.hash")
    if "tombstone" in source:
        tombstone = _object(source["tombstone"], "recorded_source.tombstone")
        if set(tombstone) != {"reason", "unknown_reason"}:
            _invalid("recorded_source.tombstone")
    return deepcopy(source)


def _sections(page, locator):
    parsed = parse_markdown_document(page["content"], locator)
    observations = observe_page_sections(page["content"], locator, page["kind"])
    exact = {section.locator: section.exact_text for section in parsed.sections}
    first = parsed.sections[0].start if parsed.sections else len(parsed.normalized_markdown)
    sections = []
    for observation in observations.sections:
        if observation.ownership.value == "generated" or (observation.level == 1 and page["kind"] != "guides"):
            continue
        text = exact.get(observation.locator, parsed.normalized_markdown[:first])
        normalized = re.sub(r"\s+", " ", text).strip()
        snippet = normalized[:MAX_SECTION_SNIPPET_CHARACTERS]
        sections.append({"locator": observation.locator, "page_locator": locator,
            "heading_path": list(observation.heading_path), "occurrence_path": list(observation.occurrence_path),
            "ordinal": observation.ordinal, "ownership": observation.ownership.value,
            "content_sha256": observation.exact_hash,
            "snippet": snippet,
            "snippet_bounds": {"total": len(normalized), "returned": len(snippet),
                               "truncated": len(snippet) < len(normalized)}})
    total = len(sections)
    return sections[:MAX_NARRATIVE_SECTIONS], {"total": total, "returned": min(total, MAX_NARRATIVE_SECTIONS),
                                                "truncated": total > MAX_NARRATIVE_SECTIONS}


def enrich_search(result, *, pages_by_path, owner_mappings, native_payload, recorded_reviews) -> dict[str, Any]:
    """Preserve flat candidates; group only exact captured ownership, without I/O."""
    result = _object(result, "result")
    if "discovery" in result:
        _invalid("result.discovery")
    matches = result.get("results")
    if not isinstance(matches, list) or len(matches) > 100:
        _invalid("result.results")
    bounds = _bounds(_object(result.get("bounds"), "result.bounds").get("results"), "result.bounds.results")
    if (type(result.get("returned")) is not int or type(result.get("count")) is not int
            or type(result.get("total")) is not int
            or result.get("returned") != len(matches) or result.get("count") != len(matches)
            or bounds["returned"] != len(matches) or result.get("total") != bounds["total"]
            or result.get("truncated") is not bounds["truncated"]):
        _invalid("result.bounds")
    pages = _object(pages_by_path, "pages_by_path")
    mappings = _object(owner_mappings, "owner_mappings")
    native = _native(native_payload)
    reviews = _reviews(recorded_reviews)
    members, groups, group_by_key = [], [], {}
    seen = set()
    kinds = {entry.mcp_uri_kind: entry for entry in iter_page_kinds()}
    for index, value in enumerate(matches):
        match = _object(value, "result.match")
        path = match.get("path")
        if not isinstance(path, str):
            _invalid("result.match.path")
        try:
            validate_exact_page_coordinate(path)
        except (TypeError, ValueError):
            _invalid("result.match.path")
        if path in seen or path not in pages:
            _invalid("pages_by_path.membership")
        seen.add(path)
        page = _object(pages[path], "page")
        if (any(not isinstance(page.get(key), str) for key in ("kind", "id", "uri", "path", "title", "content"))
                or page["kind"] not in kinds or page["path"] != path or page["uri"] != match.get("uri")):
            _invalid("page.coordinate")
        entry = kinds[page["kind"]]
        try:
            page_id = page["id"] if entry.requires_page_id else None
            if canonical_path(entry.kind, page_id) != path or mcp_uri(entry.kind, page_id) != page["uri"]:
                _invalid("page.coordinate")
        except (TypeError, ValueError):
            _invalid("page.coordinate")
        try:
            digest = hashlib.sha256(page["content"].encode("utf-8")).hexdigest()
        except UnicodeError:
            _invalid("page.content")
        provenance = _object(match["provenance"], "result.match.provenance") if "provenance" in match else {}
        recorded_digest = provenance.get("content_sha256")
        if recorded_digest is not None and recorded_digest != digest:
            _invalid("page.content_sha256")
        exact_native, concepts = _native_member(path, native)
        owner, key = _owner(path, mappings, exact_native, concepts)
        recorded_source = _recorded_source(owner["mapping"])
        sections, section_bound = _sections(page, exact_native["locator"] or page["uri"])
        members.append({"result_index": index, "path": path, "uri": page["uri"], "content_sha256": digest,
            "identity_state": "candidate", "owner": owner, "native": exact_native,
            "qualification": {"basis": "captured", "source_comparison": "not-performed",
                "implementation_comparison": "not-performed", "semantic_correctness": "not-evaluated",
                "runtime_behavior": "not-evaluated", "recorded_source": recorded_source},
            "section_scope": "useful-non-generated-narrative", "sections": sections, "section_bounds": section_bound,
            "recorded_review": _recorded_review(path, reviews),
            "next_read": {"operation": "inspect_concept", "locator_or_exact_route": path,
                "live": False, "selection_required": True, "resolution_performed": False}})
        if key not in group_by_key:
            group_by_key[key] = len(groups)
            groups.append({"key": {"kind": key[0], "value": key[1]}, "members": []})
        groups[group_by_key[key]]["members"].append(index)
    discovery = {"schema_version": DISCOVERY_SCHEMA_VERSION, "scope": "returned-search-candidates",
        "identity_state": "candidate", "live_comparison_performed": False,
        "native": deepcopy({key: value for key, value in native.items() if key != "concepts"}),
        "recorded_review": {**deepcopy({key: value for key, value in reviews.items() if key != "by_path"}),
            "basis": "snapshot", "live_evaluation_performed": False, "current_acknowledgment": "not-compared"},
        "bounds": {"members": bounds, "groups": {"total": len(groups), "returned": len(groups), "truncated": False}},
        "limits": {"narrative_sections_per_member": MAX_NARRATIVE_SECTIONS,
            "section_snippet_characters": MAX_SECTION_SNIPPET_CHARACTERS, "serialized_bytes": MAX_DISCOVERY_BYTES},
        "members": members, "groups": groups}
    try:
        size = len(json.dumps(discovery, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=False, allow_nan=False).encode("utf-8"))
    except (TypeError, ValueError, UnicodeError):
        _invalid("discovery.json")
    if size > MAX_DISCOVERY_BYTES:
        raise DiscoveryError("discovery-output-limit", "discovery", required_bytes=size)
    return {**deepcopy(result), "discovery": discovery}
