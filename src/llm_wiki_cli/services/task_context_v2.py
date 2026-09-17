"""Explicit task v2: selected native storage plus independently captured source.

No legacy whole-wiki packet is constructed for a scoped store read. Source
extraction, graph queries, requirements, coverage and accounting keep their
existing owners; this module composes their selected observations.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any

from ..config import DEFAULT_WIKI_DIR, validate_path, validate_source_root
from . import context_packet as packets, context_service as context
from .change_selection import select_changes
from .context_budget import _accounted_render
from .dependencies import analyze_dependencies
from .documentation_query_builder import assemble_documentation_query_service
from .extraction_service import InventoryResult
from .knowledge_envelope import ConsumedInput, hash_source_snapshot
from .knowledge_storage import KnowledgeStorageError, _concept_aliases, digest
from .knowledge_storage_access import ScopedKnowledgeRead, capture_knowledge_slice
from .knowledge_storage_io import ReadObservation, StorageReadSession, range_batches
from .markdown_sections import parse_markdown_document
from .section_ownership import observe_page_sections
from .source_selection import validate_persisted_source_selection_identity
from .source_snapshot import SourceSnapshot, build_source_snapshot
from .task_contract import TASK_RESULT_SCHEMA_V2, TaskContext, normalize_task_request
from .task_context import (
    TaskRead, _LIVE_FACETS, _NATIVE_FACETS, _cancel, _counter, _result_body, plan_source_read,
)
from .task_evidence import declaration_records, observe_requirement
from .workflow_profile import WorkflowRequestError, canonical_json, content_id

SOURCE_RECEIPT_SCHEMA = "llm-wiki-task-source/v1"
STORAGE_RECEIPT_SCHEMA = "llm-wiki-task-storage/v1"
PACKED_RECEIPT_SCHEMA = "llm-wiki-task-storage/v2"
PROJECTED_RECEIPT_SCHEMA = "llm-wiki-task-storage/v3"


def _source_receipt(snapshot: SourceSnapshot | None) -> dict[str, Any] | None:
    if snapshot is None:
        return None
    return {"schema_version": SOURCE_RECEIPT_SCHEMA,
            "inputs": [{"path": i.path, "content_hash": i.content_hash, "kind": i.kind_value}
                       for i in snapshot.to_consumed_inputs()],
            "file_bytes": {p: info.size for p, info in sorted(snapshot.captured_file_integrity.items())},
            "source_selection": packets._thaw_json(snapshot.source_selection_identity),
            "selection_inputs": packets._thaw_json(snapshot.source_selection_inputs)}


def _source_capture(root, paths, scope, settings, source_selection, helper_cache_dir):
    snapshot = build_source_snapshot(root, only_files=None if scope == "full-inventory" else sorted(paths),
        source_selection=source_selection, max_files=settings["max_files"], max_bytes=settings["max_source_bytes"],
        respect_ignores=True, coherent=True)
    packets._guard_windows_inputs(root, snapshot.captured_content_hashes)
    collected = context.get_inventory(str(root), deep=True, return_result=True, include_plugins=False,
        source_selection=source_selection, source_snapshot=snapshot,
        **({"helper_cache_dir": helper_cache_dir} if helper_cache_dir is not None else {}))
    if not isinstance(collected, InventoryResult) or collected.failed or not isinstance(collected.source_snapshot, SourceSnapshot):
        raise packets.ContextPacketUnavailableError("selected source extraction is unavailable", field="src_dir")
    snapshot = collected.source_snapshot
    anchor = packets._source_anchor(snapshot)
    packets._assert_source_inputs_unchanged(snapshot, anchor)
    inventory = collected.inventory
    edges = context.resolve_call_edges(inventory)
    entrypoints = context.get_entry_points(inventory,
        console_scripts=context.read_console_scripts(str(root), source_snapshot=snapshot), root=root,
        include_plugins=False)
    flows = [context.build_flow(entry, list(edges)) for entry in entrypoints]
    dependency_analysis = analyze_dependencies(inventory)
    service = assemble_documentation_query_service(inventory=inventory, call_edges=edges, flows=flows,
        data_flows=(), dependency_analysis=dependency_analysis, surface_index=None,
        limit=settings["max_graph_items"], knowledge_view=None, machine_verification={})
    return snapshot, anchor, inventory, service


def _native_key(selector: str) -> str:
    return "page:" + selector if selector.endswith(".md") and ":" not in selector else "concept:" + selector


def _native_selectors(request) -> list[str]:
    keys = set()
    for anchor in request["anchors"]:
        if anchor["kind"] == "source":
            keys.add("source:" + anchor["value"])
        elif anchor["kind"] in {"concept", "wiki"}:
            keys.add(_native_key(anchor["value"]))
    for requirement in request["requirements"]:
        if requirement["facet"] in _NATIVE_FACETS:
            keys.add(_native_key(requirement["selector"]))
    if not keys and not request["requirements"]:
        keys.update("term:" + token for token in re.findall(r"\w+", request["text"].casefold())[:16])
    if len(keys) > 100:
        raise WorkflowRequestError("anchors", "native selectors exceed the bounded routing limit")
    return sorted(keys)


def _native_collections(request):
    if request.get("storage_options", {}).get("selection") != "required-facets-v1":
        return None
    collections = {"concepts"}
    for requirement in request["requirements"]:
        if requirement["facet"] == "typed-relationships":
            collections.add("edges")
        elif requirement["facet"] == "semantic-section":
            collections.add("sections")
    return sorted(collections)


def _storage_receipt(native: ScopedKnowledgeRead | None, *, status: str, reason: str | None,
                     request=None) -> dict[str, Any]:
    result: dict[str, Any] = {"schema_version": STORAGE_RECEIPT_SCHEMA, "status": status, "reason": reason,
        "validation_scope": "selected-committed-records", "whole_store_validated": False,
        "root_hash": None, "lookup_complete": False, "unverified_records": {}, "inputs": [],
        "read_bytes": 0, "read_operations": 0, "expanded_bytes": 0}
    collections = _native_collections(request) if request is not None else None
    if ((request is not None and "storage_options" in request)
            or (native is not None and native.slice.to_payload().get("storage_format") == "packed-v4")):
        from .knowledge_storage import COLLECTIONS
        result.update(schema_version=PROJECTED_RECEIPT_SCHEMA, layout="expanded-v1", storage_format=None,
                      collections=collections or sorted(COLLECTIONS[:5]),
                      validation_scope="selected-committed-collections" if collections is not None else "selected-committed-records")
    if native is None:
        if request is not None and request.get("storage_options", {}).get("receipt") == "compact-v1":
            from .storage_receipts import compact_storage_receipt
            return compact_storage_receipt(result)
        return result
    selected = native.slice.to_payload()
    inputs = [{"path": path, "hash": digest(observed.content), "bytes": len(observed.content)}
              for path, observed in sorted(native.session.observations.items())]
    ranges = [{"path": key[0], "offset": key[1], "bytes": key[2], "file_bytes": key[3],
               "hash": digest(observed.content)}
              for key, observed in sorted(native.session.range_observations.items())]
    if selected.get("storage_format") in {"packed-v3", "packed-v4"}:
        result.update(schema_version=PROJECTED_RECEIPT_SCHEMA if "layout" in result else PACKED_RECEIPT_SCHEMA, ranges=ranges,
                      archive_validation_scope="selected-members")
    if "layout" in result:
        result["storage_format"] = selected.get("storage_format", "sharded-v2")
    # One final reread is reserved in the emitted work receipt. Publication
    # checks that it actually completed with exactly this counted work.
    recheck = native.session.recheck_work()
    result.update(root_hash=selected["root_hash"], lookup_complete=selected["lookup_complete"],
        unverified_records=selected["unverified_records"], inputs=inputs,
        read_bytes=native.session.bytes_read + recheck["bytes"],
        read_operations=native.session.reads + recheck["operations"],
        expanded_bytes=selected["work"]["expanded_bytes"])
    if request is not None and request.get("storage_options", {}).get("receipt") == "compact-v1":
        from .storage_receipts import compact_storage_receipt
        return compact_storage_receipt(result)
    return result


def _native_observation(native, requirement, snapshot, paths, scope, limit):
    selector, facet = requirement["selector"], requirement["facet"]
    selected = native.slice.to_payload()
    key = _native_key(selector)
    concepts = [c for c in native.reader.consumed_concepts.values() if key in _concept_aliases(c)]
    if not concepts:
        return "missing", None, "no-exact-concept-in-selected-committed-scope"
    if len(concepts) != 1:
        return "ambiguous", None, "select-an-exact-concept-coordinate"
    concept = concepts[0]
    structure = concept["facets"]["structure"]
    source_basis = structure.get("basis") or {}
    source_path = source_basis.get("source_path")
    freshness = "unknown"
    if snapshot is not None and source_path in snapshot.captured_content_hashes:
        freshness = ("source-unchanged" if snapshot.captured_content_hashes[source_path] == source_basis.get("source_content_hash")
                     else "source-changed")
    elif snapshot is not None and source_path in paths:
        freshness = "source-missing"
    qualified = {**concept, "canonical_path": concept["document"]["canonical_path"],
        "freshness": {"state": freshness}, "evidence": structure["evidence"],
        "verification": "not-evaluated"}
    native_qualification = {"availability": "scoped", "root_hash": selected["root_hash"],
                            "whole_store_validated": False, "validation_scope": selected["validation_scope"]}
    observation: dict[str, Any] = {"found": True, "concept": qualified, "knowledge": native_qualification}
    values = []
    field = "concepts"
    if facet == "concept":
        values = [qualified]
    elif facet == "typed-relationships":
        field = "edges"
        locator = concept["locator"]
        values = [row["value"] for row in selected["records"]["edges"]
                  if row["value"]["from"].get("locator") == locator or row["value"]["target"].get("locator") == locator]
    elif facet == "semantic-section":
        field = "sections"
        path = concept["document"]["canonical_path"]
        text = native.markdown[path]
        ownership = observe_page_sections(text, concept["locator"], concept["document"]["page_kind"])
        parsed = parse_markdown_document(text, concept["locator"])
        sections = {s.locator: s for s in parsed.sections}
        for section in ownership.sections:
            if section.ownership.value == "semantic" and section.locator in sections:
                exact = sections[section.locator]
                values.append({**section.to_payload(), "content": exact.exact_text, "content_identity": exact.exact_hash})
    if not values:
        return "unknown", None, "empty-selected-result-does-not-prove-absence"
    returned = values[:limit]
    total = len(values)
    if not selected["lookup_complete"]:
        total = max(total, len(returned) + 1)
    truncated = len(returned) < total
    observation.update(bounds={field: {"total": total, "returned": len(returned), "truncated": truncated}},
                       truncated=truncated)
    if facet != "concept":
        observation[field] = returned
    state, reason = ("partial", "selected-query-limit") if truncated else ("present", "qualified-committed-observation")
    if facet == "typed-relationships" and requirement["criterion"] == "complete":
        state, reason = "partial", "complete-runtime-graph-not-established"
    if freshness in {"source-changed", "source-missing"}:
        state, reason = "stale", "native-observation-is-stale"
    qualification = {"analysis_scope": scope, "freshness": "stale" if state == "stale" else "snapshot",
        "semantic_review": "not-evaluated", "behavior": "not-evaluated", "negative_claim_supported": False,
        "native": native_qualification}
    if facet == "typed-relationships":
        qualification["graph_completeness"] = "static-observations-only"
    fact = {"facet": facet, "selector": selector, "state": state, "observation": observation,
            "citations": [{"path": concept["document"]["canonical_path"], "wiki_identity": selected["root_hash"]}],
            "qualification": qualification}
    fact["fact_id"] = content_id("llm-wiki-task-fact/v1", fact)
    return state, fact, reason


@dataclass(frozen=True)
class ScopedTaskState:
    source_root: Path
    wiki_root: Path
    snapshot: SourceSnapshot | None
    source_anchor: str | None
    wiki_inputs: Mapping[str, ReadObservation]
    cacheable: bool
    changes: Any
    change_request: Any
    native_absent: bool = False
    original_work: Mapping[str, Any] | None = None
    wiki_ranges: Mapping[tuple[str, int, int, int], ReadObservation] = field(default_factory=dict)
    batched: bool = False

    def revalidate(self, settings, *, source_metrics=None, wiki_metrics=None):
        if self.snapshot is not None:
            if self.source_anchor is None:
                raise WorkflowRequestError("source", "source anchor is missing")
            packets._assert_source_unchanged(self.snapshot, self.source_anchor, metrics=source_metrics)
        if self.change_request is not None:
            if select_changes(self.source_root, self.change_request) != self.changes:
                raise packets.ContextPacketSourceMutationError("changes")
        session = StorageReadSession(self.wiki_root, max_bytes=settings["max_wiki_bytes"])
        if self.native_absent and (self.wiki_root / ".llm-wiki-knowledge.json").exists():
            raise KnowledgeStorageError("root", "native state appeared during the request", code="storage-mutation")
        try:
            with session.phase():
                for relative, expected in self.wiki_inputs.items():
                    raw = session.read(relative, len(expected.content))
                    if raw != expected.content or session.observations[relative] != expected:
                        raise KnowledgeStorageError(relative, "scoped input changed", code="storage-mutation")
                if self.batched:
                    session.read_ranges(list(self.wiki_ranges))
                for key, expected in self.wiki_ranges.items():
                    if not self.batched:
                        session.read_range(*key)
                    if session.range_observations[key] != expected:
                        raise KnowledgeStorageError(key[0], "scoped pack changed", code="storage-mutation")
        finally:
            if wiki_metrics is not None:
                wiki_metrics.update(files=session.reads, bytes=session.bytes_read)


@packets._guarded_capture
def build_scoped_task_read(request, *, src_dir=".", wiki_dir=DEFAULT_WIKI_DIR,
    profile=None, policy=None, counter=None, allow_external_src=False, source_selection=None,
    helper_cache_dir=None, cancelled=None, _defer_validation=False, _wiki_byte_budget=None):
    normalized, effective = normalize_task_request(request, profile=profile, policy=policy)
    settings = effective.settings
    wiki_budget = settings["max_wiki_bytes"] if _wiki_byte_budget is None else min(settings["max_wiki_bytes"], _wiki_byte_budget)
    if wiki_budget <= 0:
        raise packets.ContextPacketUnavailableError("scoped validation byte budget exhausted", field="max_wiki_bytes")
    counter = _counter(settings, counter)
    if cancelled is not None and not callable(cancelled):
        raise WorkflowRequestError("cancelled", "must be a trusted callback")
    _cancel(cancelled)
    source_root = validate_source_root(src_dir, "--src-dir", allow_external=allow_external_src)
    wiki_root = validate_path(wiki_dir, "--wiki-dir")
    paths, changes, live, scope = plan_source_read(normalized, settings, source_root)
    snapshot, source_anchor, inventory, service = None, None, {}, None
    source_error = None
    if live:
        snapshot, source_anchor, inventory, service = _source_capture(source_root, paths, scope, settings,
                                                                    source_selection, helper_cache_dir)
    _cancel(cancelled)
    native, native_reason = None, None
    native_status = "off" if settings["knowledge_mode"] == "off" else "unavailable"
    compatible = True
    if native_status != "off":
        try:
            native = capture_knowledge_slice(wiki_root, _native_selectors(normalized),
                max_bytes=wiki_budget, max_records=min(1000, max(100, settings["max_graph_items"] * 4)),
                include_graph=any(r["facet"] == "typed-relationships" for r in normalized["requirements"]),
                collections=_native_collections(normalized),
                coalesce_rechecks="storage_options" in normalized, cancelled=cancelled)
            if snapshot is not None:
                validate_persisted_source_selection_identity(native.manifest.generation_inputs,
                    snapshot.source_selection_identity, operation="scoped task context",
                    live_selection_inputs=snapshot.source_selection_inputs)
            native_status = "scoped"
        except KnowledgeStorageError as exc:
            if exc.code == "storage-cancelled":
                _cancel(lambda: True)
            if exc.code != "storage-missing" or exc.field != ".llm-wiki-knowledge.json":
                raise
            native_reason = getattr(exc, "code", "native-input-unavailable")
            compatible = False
            native = None
    if settings["knowledge_mode"] == "required" and native is None:
        raise packets.ContextPacketUnavailableError("required scoped native inputs are unavailable: " + str(native_reason), field="knowledge_mode")
    storage = _storage_receipt(native, status=native_status, reason=native_reason, request=normalized)
    if storage["read_bytes"] > wiki_budget:
        raise packets.ContextPacketUnavailableError("scoped wiki validation exceeds its byte budget", field="max_wiki_bytes")
    source_capture = _source_receipt(snapshot)
    source_id = None if source_capture is None else content_id(SOURCE_RECEIPT_SCHEMA, source_capture)
    wiki_id = storage["root_hash"] or content_id("llm-wiki-unread-storage/v1", {"status": native_status})
    source_context = SimpleNamespace(source_snapshot=snapshot, wiki_anchor=wiki_id)
    records = declaration_records(inventory)
    observations, queried, plan = {}, {}, []
    anchors = [{**a, "reason": "explicit-caller-selection"} for a in normalized["anchors"]]
    requirements = normalized["requirements"]
    for requirement in requirements:
        facet, selector = requirement["facet"], requirement["selector"]
        key = (facet, selector, requirement["criterion"])
        operation = {"facet": facet, "selector": selector, "scope": scope, "reason": "explicit-requirement", "executed": False}
        if key in queried:
            observation = queried[key]
        elif len(queried) >= settings["max_read_rounds"]:
            observation = ("omitted", None, "read-round-limit")
        elif facet == "behavior":
            observation = ("unsupported", None, "host-behavioral-verification-required")
        elif facet in _LIVE_FACETS and snapshot is None:
            observation = ("unavailable" if source_error else "omitted", None, source_error or "broader-scope-required")
        elif facet in _NATIVE_FACETS and native is None:
            observation = ("unavailable", None, native_reason or "native-mode-is-off")
        else:
            _cancel(cancelled)
            observation = (_native_observation(native, requirement, snapshot, paths, scope, settings["max_graph_items"])
                if facet in _NATIVE_FACETS else observe_requirement(source_context, service, records, requirement,
                                                                  scope=scope, limit=settings["max_graph_items"]))
            queried[key] = observation
            operation["executed"] = True
        observations[requirement["id"]] = observation
        plan.append(operation)
    facts = {fact["fact_id"]: fact for _, fact, _ in observations.values() if fact is not None}
    if not requirements:
        for record in records[:settings["max_read_rounds"]]:
            requirement = {"facet": "source-contract", "selector": record["selector"], "criterion": "present"}
            _, fact, _ = observe_requirement(source_context, service, records, requirement,
                                            scope=scope, limit=settings["max_graph_items"])
            if fact is not None:
                facts[fact["fact_id"]] = fact
                queried[("source-contract", record["selector"], "present")] = ("present", fact, "discovery")
        if native is not None:
            for row in native.slice.to_payload()["records"]["concepts"][:settings["max_graph_items"]]:
                anchors.append({"kind": "concept", "value": row["value"]["locator"], "reason": "committed-candidate"})
    work = {"captures": int(snapshot is not None), "source_files": len(snapshot.captured_content_hashes) if snapshot else 0,
            "source_bytes": sum(i.size for i in snapshot.captured_file_integrity.values()) if snapshot else 0,
            "queries": len(queried), "capture_retries": 0, "scope": scope,
            "source_byte_measure": "unique-captured-inputs; excludes parser and validation rereads"}
    basis = {"source": source_id, "wiki": wiki_id,
             "consumed_source": hash_source_snapshot(snapshot.to_consumed_inputs()) if snapshot else None,
             "scope": scope, "paths": sorted(paths), "changes": changes,
             "source_selection_compatible": compatible if snapshot else None,
             "native_availability_required": settings["knowledge_mode"] == "required"}
    basis["capture_id"] = content_id("llm-wiki-task-basis/v2", basis)
    accounting = {"budget_tokens": settings["budget_tokens"], "used_tokens": 0, "counter_id": counter.identity,
                  "mode": settings["budget_mode"], "exact_compliance": settings["budget_mode"] == "exact" and bool(counter.exact),
                  "usage_kind": "upper-bound-including-accounting", "scope": "emitted-text-without-host-chat-framing"}
    selected_facts = sorted(facts.values(), key=lambda f: f["fact_id"])
    while True:
        def render(value):
            body = _result_body(normalized, effective, basis, plan, anchors, work, observations, selected_facts, None, value)
            body.update(schema_version=TASK_RESULT_SCHEMA_V2, storage=storage, source_capture=source_capture)
            body.pop("result_id")
            body["result_id"] = content_id(TASK_RESULT_SCHEMA_V2, body)
            return canonical_json(body).decode("utf-8")
        rendered = _accounted_render(render, accounting, counter)
        if accounting["used_tokens"] <= settings["budget_tokens"]:
            result = TaskContext(True, rendered, accounting, schema_version=TASK_RESULT_SCHEMA_V2)
            break
        if not selected_facts:
            result = TaskContext(False, "", {**accounting, "exact_compliance": False}, "cannot-fit", TASK_RESULT_SCHEMA_V2)
            break
        selected_facts.pop()
    _cancel(cancelled)
    if snapshot is not None:
        if source_anchor is None:
            raise WorkflowRequestError("source", "source anchor is missing")
        packets._assert_source_unchanged(snapshot, source_anchor)
    if changes is not None and select_changes(source_root, normalized["changes"]) != changes:
        raise packets.ContextPacketSourceMutationError("changes")
    if native is not None and not _defer_validation:
        actual = native.finish()
        if actual["bytes_read"] != storage["read_bytes"] or actual["read_operations"] != storage["read_operations"]:
            raise WorkflowRequestError("storage", "storage work accounting changed before publication")
    state = ScopedTaskState(source_root, wiki_root, snapshot, source_anchor,
        {} if native is None else dict(native.session.observations),
        native_status != "unavailable" and all(module.get("language") == "python" for module in inventory.values()),
        changes, normalized["changes"], native_status == "unavailable", dict(work),
        {} if native is None else dict(native.session.range_observations), "storage_options" in normalized)
    if state.native_absent and (wiki_root / ".llm-wiki-knowledge.json").exists():
        raise packets.ContextPacketSourceMutationError("wiki")
    return TaskRead(normalized, effective, None, wiki_root, wiki_id, result,
                    scoped_state=state, source_root=source_root)


def validate_scoped_bindings(payload, normalized, profile):
    """Validate portable scope and consumed-input bindings, without claiming authenticity."""
    from .task_context import _result_fields
    from .validation import is_portable_relative_path
    settings = profile.settings
    if payload["packet"] is not None:
        raise ValueError("scoped task context cannot carry a legacy full-validity packet")
    storage = payload["storage"]
    compact = normalized.get("storage_options", {}).get("receipt") == "compact-v1"
    if compact:
        from .storage_receipts import expand_storage_receipt
        storage = expand_storage_receipt(storage)
    projected = isinstance(storage, dict) and storage.get("schema_version") == PROJECTED_RECEIPT_SCHEMA
    packed = isinstance(storage, dict) and (storage.get("schema_version") == PACKED_RECEIPT_SCHEMA
        or (projected and storage.get("storage_format") in {"packed-v3", "packed-v4"}))
    _result_fields(storage, {"schema_version", "status", "reason", "validation_scope", "whole_store_validated",
                            "root_hash", "lookup_complete", "unverified_records", "inputs", "read_bytes",
                            "read_operations", "expanded_bytes"} |
                   ({"ranges", "archive_validation_scope"} if packed else set()) |
                   ({"collections", "layout", "storage_format"} if projected else set()), "storage")
    selected_collections = _native_collections(normalized)
    expected_scope = "selected-committed-collections" if selected_collections is not None else "selected-committed-records"
    if projected != ("storage_options" in normalized or storage.get("storage_format") == "packed-v4"):
        raise ValueError("storage receipt version differs from the request")
    if projected:
        from .knowledge_storage import COLLECTIONS
        if (storage["layout"] != "expanded-v1" or storage["collections"] != (selected_collections or sorted(COLLECTIONS[:5]))
                or storage["storage_format"] not in {None, "sharded-v2", "packed-v3", "packed-v4"}
                or (storage["storage_format"] is None) != (storage["status"] != "scoped")):
            raise ValueError("storage selection or layout differs from the request")
    if (storage["schema_version"] not in {STORAGE_RECEIPT_SCHEMA, PACKED_RECEIPT_SCHEMA, PROJECTED_RECEIPT_SCHEMA} or storage["whole_store_validated"] is not False
            or storage["validation_scope"] != expected_scope
            or storage["status"] not in {"off", "unavailable", "scoped"} or type(storage["lookup_complete"]) is not bool):
        raise ValueError("invalid scoped storage qualification")
    if settings["knowledge_mode"] == "required" and storage["status"] != "scoped":
        raise ValueError("required scoped native inputs are unavailable")
    if settings["knowledge_mode"] == "off" and storage["status"] != "off":
        raise ValueError("native mode was widened")
    inputs = storage["inputs"]
    if not isinstance(inputs, list) or len(inputs) > 100_000:
        raise ValueError("invalid storage input list")
    names = set()
    for item in inputs:
        _result_fields(item, {"path", "hash", "bytes"}, "storage input")
        if (not is_portable_relative_path(item["path"]) or item["path"] in names or not packets.is_valid_sha256(item["hash"])
                or type(item["bytes"]) is not int or item["bytes"] < 0):
            raise ValueError("invalid consumed storage input")
        names.add(item["path"])
    ranges = storage.get("ranges", [])
    if packed:
        from .knowledge_packs import PACK_NAME, INDEX_PAGE_NAME, INDEX_PAGE_BYTES, MAX_INDEX_BYTES, MAX_PACK_BYTES
        if (storage["archive_validation_scope"] != "selected-members" or storage["status"] != "scoped"
                or not isinstance(ranges, list) or len(ranges) > 100_000):
            raise ValueError("invalid packed storage scope")
        previous = None
        pack_ends = {}
        for item in ranges:
            _result_fields(item, {"path", "offset", "bytes", "file_bytes", "hash"}, "storage range")
            if (not isinstance(item["path"], str) or not (PACK_NAME.fullmatch(item["path"])
                    or (projected and storage["storage_format"] == "packed-v4" and INDEX_PAGE_NAME.fullmatch(item["path"]))) or item["path"] in names
                    or not packets.is_valid_sha256(item["hash"])
                    or any(type(item[k]) is not int for k in ("offset", "bytes", "file_bytes"))
                    or item["offset"] < 0 or not 0 < item["bytes"] <= item["file_bytes"] <= MAX_PACK_BYTES
                    or item["offset"] + item["bytes"] > item["file_bytes"]):
                raise ValueError("invalid consumed pack range")
            if INDEX_PAGE_NAME.fullmatch(item["path"]) and (item["file_bytes"] > INDEX_PAGE_BYTES or item["bytes"] > MAX_INDEX_BYTES):
                raise ValueError("metadata page range exceeds its bound")
            key = (item["path"], item["offset"])
            if previous is not None and key <= previous:
                raise ValueError("pack ranges must be sorted and unique")
            previous = key
            prior = pack_ends.get(item["path"])
            if prior is not None and (item["offset"] < prior[0] or item["file_bytes"] != prior[1]):
                raise ValueError("pack ranges overlap or disagree on file size")
            pack_ends[item["path"]] = (item["offset"] + item["bytes"], item["file_bytes"])
    range_rechecks = len(range_batches([(r["path"], r["offset"], r["bytes"], r["file_bytes"]) for r in ranges])) if "storage_options" in normalized else len(ranges)
    if (type(storage["read_bytes"]) is not int or storage["read_bytes"] != 2 * sum(i["bytes"] for i in [*inputs, *ranges])
            or storage["read_bytes"] > settings["max_wiki_bytes"]
            or type(storage["read_operations"]) is not int or storage["read_operations"] != 2 * len(inputs) + len(ranges) + range_rechecks
            or type(storage["expanded_bytes"]) is not int or not 0 <= storage["expanded_bytes"] <= 16_777_216):
        raise ValueError("storage work is inconsistent or exceeds policy")
    if storage["status"] == "scoped":
        roots = [i for i in inputs if i["path"] == ".llm-wiki-knowledge.json"]
        if (len(roots) != 1 or roots[0]["hash"] != storage["root_hash"]
                or payload["basis"]["wiki"] != storage["root_hash"] or ".llm-wiki-manifest.json" not in names):
            raise ValueError("scoped generation commitment was lost")
    elif inputs or storage["root_hash"] is not None:
        raise ValueError("unavailable native state cannot claim consumed storage")
    source = payload["source_capture"]
    if source is None:
        if payload["basis"]["source"] is not None:
            raise ValueError("missing source receipt")
        source_hashes = {}
    else:
        _result_fields(source, {"schema_version", "inputs", "file_bytes", "source_selection", "selection_inputs"}, "source receipt")
        if source["schema_version"] != SOURCE_RECEIPT_SCHEMA or not isinstance(source["inputs"], list):
            raise ValueError("unsupported source receipt")
        consumed = []
        for item in source["inputs"]:
            _result_fields(item, {"path", "content_hash", "kind"}, "source input")
            consumed.append(ConsumedInput(**item))
        if (hash_source_snapshot(consumed) != payload["basis"]["consumed_source"]
                or content_id(SOURCE_RECEIPT_SCHEMA, source) != payload["basis"]["source"]):
            raise ValueError("source receipt commitment mismatch")
        source_hashes = {i.path: i.content_hash for i in consumed}
        if (set(source_hashes) != set(source["file_bytes"])
                or any(type(n) is not int or n < 0 for n in source["file_bytes"].values())
                or len(source_hashes) != payload["work"]["source_files"]
                or sum(source["file_bytes"].values()) != payload["work"]["source_bytes"]):
            raise ValueError("source work receipt mismatch")
    for fact in payload["facts"]:
        if fact["facet"] in _NATIVE_FACETS:
            native = fact["qualification"]["native"]
            if (storage["status"] != "scoped" or native.get("availability") != "scoped"
                    or native.get("whole_store_validated") is not False
                    or native.get("root_hash") != storage["root_hash"]
                    or native.get("validation_scope") != storage["validation_scope"]):
                raise ValueError("native fact widened its validation scope")
            concept = fact["observation"]["concept"]
            if _native_key(fact["selector"]) not in _concept_aliases(concept):
                raise ValueError("native observation does not match its exact selector")
            path = concept["document"]["canonical_path"]
            page_inputs = [item for item in inputs if item["path"] == path]
            if len(page_inputs) != 1 or page_inputs[0]["hash"] != concept["facets"]["semantics"]["page_hash"]:
                raise ValueError("native observation is not bound to its consumed page")
            if fact["facet"] == "typed-relationships":
                locator = concept["locator"]
                if any(edge["from"].get("locator") != locator and edge["target"].get("locator") != locator
                       for edge in fact["observation"]["edges"]):
                    raise ValueError("typed relationship belongs to a different concept")
        elif fact["facet"] == "source-contract":
            observed = fact["observation"]
            if fact["selector"] != observed["selector"] or type(observed["line"]) is not int or observed["line"] < 1:
                raise ValueError("invalid source declaration coordinate")
            if payload["basis"]["scope"] == "selected" and observed["path"] not in payload["basis"]["paths"]:
                raise ValueError("source declaration exceeds selected paths")
        for citation in fact["citations"]:
            if "source_identity" in citation and (citation.get("path") not in source_hashes
                    or source_hashes[citation["path"]] != citation["source_identity"]):
                raise ValueError("source citation is outside the consumed inputs")
            if "wiki_identity" in citation and (citation["path"] not in names or citation["wiki_identity"] != storage["root_hash"]):
                raise ValueError("wiki citation is outside the validated scope")
