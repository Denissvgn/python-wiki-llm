"""Coherent selected access to a committed sharded knowledge generation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from .knowledge_envelope import EvaluatedEnvelope
from .knowledge_governance import (
    GOVERNANCE_FILENAME, parse_governance_ledger, lifecycle_state_by_uid, natural_key_for,
)
from .contracts import GOVERNANCE_EXTENSION_KEY
from .knowledge_model import _parse_bundle
from .knowledge_storage import (
    MAX_EXPANDED_BYTES, MAX_OBJECT_BYTES, MAX_ROOT_BYTES, ROOT_FILENAME, STORE_SCHEMA,
    KnowledgeSlice, KnowledgeStorageError, KnowledgeStoreReader, digest,
)
from .knowledge_storage_io import StorageReadSession
from .knowledge_packs import PACKED_SCHEMAS, open_knowledge_store
from .sync_manifest import MANIFEST_FILENAME
from .manifest_storage import ValidatedManifestHeader, read_manifest_header


@dataclass
class ScopedKnowledgeRead:
    """Request-owned observations that require a final authoritative recheck."""

    slice: KnowledgeSlice
    manifest: ValidatedManifestHeader
    markdown: dict[str, str]
    reader: KnowledgeStoreReader = field(repr=False)
    session: StorageReadSession = field(repr=False)

    def finish(self) -> dict[str, Any]:
        self.session.recheck()
        return self.session.receipt()


def capture_knowledge_slice(
    wiki_dir: str | Path, selectors: Iterable[str], *, max_bytes: int = 8_388_608,
    max_records: int = 1000, max_expanded_bytes: int = 16_777_216,
    include_graph: bool = False, collections: Iterable[str] | None = None,
    coalesce_rechecks: bool = False, cancelled=None,
) -> ScopedKnowledgeRead:
    """Capture selected stored observations without enumerating the wiki tree.

    The v6 commit header and policy are read completely. Unread catalogs remain
    unverified; the receipt never represents a full artifact or a live source
    evaluation. The owning request calls ``finish`` before publishing its result.
    """
    if type(include_graph) is not bool or isinstance(selectors, (str, bytes)):
        raise KnowledgeStorageError("selectors", "must be a collection of selectors")
    keys = list(selectors)
    if len(keys) > 100 or any(not isinstance(key, str) or not key or len(key) > 16_384 for key in keys):
        raise KnowledgeStorageError("selectors", "requires at most 100 bounded strings")
    session = StorageReadSession(wiki_dir, max_bytes=max_bytes, coalesce_rechecks=coalesce_rechecks, cancelled=cancelled)
    with session.phase():
        return _capture_slice(session, keys, max_bytes, max_records, max_expanded_bytes, include_graph, collections)


def _capture_slice(session, keys, max_bytes, max_records, max_expanded_bytes, include_graph, collections):
    raw = session.read(ROOT_FILENAME, MAX_ROOT_BYTES)
    try:
        schema = json.loads(raw).get("schema_version")
    except (ValueError, AttributeError, UnicodeError) as exc:
        raise KnowledgeStorageError("root", "invalid knowledge root") from exc
    if schema not in (STORE_SCHEMA, *PACKED_SCHEMAS):
        raise KnowledgeStorageError("schema_version", "selected native reads require explicit sharded or packed storage adoption",
                                    code="unsupported-schema-version")
    reader = open_knowledge_store(raw, session.read, read_range=session.read_range, max_bytes=max_bytes,
                                  max_expanded_bytes=max_expanded_bytes)
    manifest_bytes = session.read(MANIFEST_FILENAME, MAX_EXPANDED_BYTES)
    from .knowledge_artifacts import _decode_json_object
    try:
        manifest = read_manifest_header(manifest_bytes, session.read)
        bundle = _parse_bundle(reader.root["bundle"], "bundle")
    except ValueError as exc:
        raise KnowledgeStorageError("manifest", str(exc)) from exc
    marker = manifest.artifact_hashes
    if (marker is None or marker.knowledge_index_hash != digest(raw)
            or marker.surface_index_hash != bundle.snapshot.surface_index_hash
            or marker.evaluated_envelope_hash != EvaluatedEnvelope(bundle=bundle).content_hash()):
        raise KnowledgeStorageError("manifest", "does not commit the selected generation", code="storage-mixed-generation")
    if collections is not None:
        if isinstance(collections, (str, bytes)):
            raise KnowledgeStorageError("collections", "requires a collection of record collection names")
        collections = tuple(collections)
    selected = reader.select(keys, max_records=max_records, collections=collections)
    if include_graph:
        locators = [row["value"]["locator"] for row in selected.to_payload()["records"]["concepts"]]
        expanded = set(keys)
        for locator in locators:
            expanded.update({"concept:" + locator, "out:concept:" + locator, "in:concept:" + locator})
        if len(expanded) > 100:
            raise KnowledgeStorageError("selectors", "graph expansion exceeds the selector limit", code="storage-budget-exhausted")
        selected = reader.select(expanded, max_records=max_records, collections=collections)
    markdown: dict[str, str] = {}
    for concept in reader.consumed_concepts.values():
        relative = concept["document"]["canonical_path"]
        if relative not in markdown:
            content = session.read(relative, MAX_OBJECT_BYTES)
            if digest(content) != concept["facets"]["semantics"]["page_hash"]:
                raise KnowledgeStorageError(relative, "selected Markdown differs from its observation",
                                            code="storage-markdown-mismatch")
            try:
                markdown[relative] = content.decode("utf-8")
            except UnicodeError as exc:
                raise KnowledgeStorageError(relative, "selected Markdown is not UTF-8") from exc
    if marker.governance_hash is not None:
        ledger_bytes = session.read(GOVERNANCE_FILENAME, MAX_OBJECT_BYTES)
        if digest(ledger_bytes) != marker.governance_hash:
            raise KnowledgeStorageError("governance", "authoritative ledger differs from its commitment")
        try:
            ledger = parse_governance_ledger(_decode_json_object(ledger_bytes, "governance"))
            states = lifecycle_state_by_uid(ledger)
            for concept in reader.consumed_concepts.values():
                summary = concept.get("extensions", {}).get(GOVERNANCE_EXTENSION_KEY)
                if not isinstance(summary, dict):
                    raise KnowledgeStorageError("governance", "selected concept lacks its identity projection")
                uid = summary.get("uid")
                if not isinstance(uid, str):
                    raise KnowledgeStorageError("governance", "selected concept UID is invalid")
                allocation = ledger.concepts.get(uid)
                if (allocation is None or allocation.locator != concept["locator"]
                        or allocation.concept_kind != concept["concept_kind"]
                        or allocation.natural_key != natural_key_for(concept["concept_kind"], concept["document"]["canonical_path"])):
                    raise KnowledgeStorageError("governance", "selected UID does not belong to this concept")
                expected_aliases = [{"type": item.alias_type, "value": item.value}
                    for item in sorted((a for a in ledger.aliases.values() if a.uid == allocation.uid),
                                       key=lambda a: (a.alias_type, a.value))]
                state, successor, _ = states[allocation.uid]
                if (summary.get("aliases") != expected_aliases or summary.get("lifecycle") != state.value
                        or concept["lifecycle"] != state.value or summary.get("successor_uid") != successor):
                    raise KnowledgeStorageError("governance", "selected identity/lifecycle differs from its authority")
        except ValueError as exc:
            raise KnowledgeStorageError("governance", str(exc)) from exc
    elif any(GOVERNANCE_EXTENSION_KEY in c.get("extensions", {}) for c in reader.consumed_concepts.values()):
        raise KnowledgeStorageError("governance", "selected governance has no committed authority")
    return ScopedKnowledgeRead(selected, manifest, markdown, reader, session)
