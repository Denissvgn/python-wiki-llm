"""Complete storage/routing audit without constructing a complete native model.

This is an explicit narrower boundary than full artifact validation: surface,
Markdown, governance authority and native projection parity still require the
full snapshot operation. No full-artifact validation token is issued here.
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import ExitStack
from pathlib import Path

from .canonical_json import CanonicalArray
from .contracts import SECTION_OWNERSHIP_EXTENSION_KEY, TYPED_GRAPH_EXTENSION_KEY
from .knowledge_audit import audit_spilled_records
from .knowledge_envelope import EvaluatedEnvelope
from .knowledge_model import (
    _parse_bundle, _parse_concept, _parse_relationship, _concept_to_payload,
    _relationship_to_payload, _validate_index_references, Resolution,
)
from .knowledge_packs import PackedKnowledgeStoreReader, open_knowledge_store
from .knowledge_storage import (
    MAX_EXPANDED_BYTES, MAX_ROOT_BYTES, ROOT_FILENAME, LOGICAL_SCHEMA,
    KnowledgeStorageError, canonical_bytes, digest, logical_digest, _validate_selected_record,
)
from .knowledge_storage_io import read_guarded, _absolute_path, _require_relative_name
from .manifest_storage import read_manifest_header
from .storage_spool import ByteSpool, DecodeCache, JsonSpool
from .storage_sort import SortedRuns
from .sync_manifest import MANIFEST_FILENAME


class _DigestSession:
    def __init__(self, root):
        self.root = _absolute_path(Path(root))
        self.observations = {}
        self.bytes_read = self.reads = 0

    def read(self, name, maximum):
        _require_relative_name(name)
        observed = read_guarded(self.root / name, min(maximum, MAX_EXPANDED_BYTES - self.bytes_read))
        self.bytes_read += len(observed.content)
        self.reads += 1
        receipt = digest(observed.content), len(observed.content), observed.identity, observed.directories
        if name in self.observations and self.observations[name] != receipt:
            raise KnowledgeStorageError(name, "input changed during streaming audit", code="storage-mutation")
        self.observations[name] = receipt
        return observed.content

    def recheck(self):
        for name, (_, size, _, _) in tuple(self.observations.items()):
            self.read(name, size)


class _Extensions(Mapping):
    def __init__(self, stored, extra):
        self.stored, self.extra = stored, extra

    def __iter__(self):
        yield from self.stored
        yield from self.extra

    def __len__(self):
        return len(self.stored) + len(self.extra)

    def __getitem__(self, name):
        return self.extra[name] if name in self.extra else self.stored[name]


def audit_knowledge_stream(wiki_dir, *, record_bytes=1_048_576):
    """Validate all storage bytes, logical hash, record shapes and exact routing.

    Expanded records are capped at 1 MiB by default (8 MiB maximum), merge runs
    use 1 MiB batches/32 handles, each spill index is capped at 16 MiB encoded
    key weight, and each private spill has a 2 GiB write quota. These are explicit
    streaming limits; the existing full-model API keeps its original limits.
    """
    if type(record_bytes) is not int or not 1024 <= record_bytes <= 8_388_608:
        raise KnowledgeStorageError("record_bytes", "must be 1024..8388608")
    session = _DigestSession(wiki_dir)
    raw = session.read(ROOT_FILENAME, MAX_ROOT_BYTES)
    with ExitStack() as stack:
        def spool():
            return stack.enter_context(ByteSpool())
        reader = open_knowledge_store(raw, session.read)
        reader.objects = spool()
        reader._nodes, reader._validated_nodes, reader._values = DecodeCache(), DecodeCache(), DecodeCache()
        if isinstance(reader, PackedKnowledgeStoreReader):
            reader.physical_objects = spool()
            reader._indexes = DecodeCache()
        manifest = read_manifest_header(session.read(MANIFEST_FILENAME, MAX_EXPANDED_BYTES), session.read)
        bundle = _parse_bundle(reader.root["bundle"], "bundle")
        marker = manifest.artifact_hashes
        if (marker is None or marker.knowledge_index_hash != digest(raw)
                or marker.surface_index_hash != bundle.snapshot.surface_index_hash
                or marker.evaluated_envelope_hash != EvaluatedEnvelope(bundle=bundle).content_hash()):
            raise KnowledgeStorageError("manifest", "does not commit the audited generation")
        keys = {"concepts": lambda v: v["locator"], "relationships": canonical_bytes,
                "edges": lambda v: v["key"], "sections": lambda v: (v["page_locator"].casefold(), v["page_locator"])}
        records = {name: stack.enter_context(SortedRuns(key, record_bytes=record_bytes)) for name, key in keys.items()}
        extensions, concepts, pages = JsonSpool(spool()), JsonSpool(spool()), JsonSpool(spool())

        def expand(row):
            reader.max_expanded_bytes = min(MAX_EXPANDED_BYTES, reader.expanded_bytes + record_bytes)
            return reader.expand_record(row)

        for kind in ("concepts", "relationships", "edges", "sections", "extensions"):
            for row in reader.records(kind):
                value = expand(row)
                _validate_selected_record(kind, row, value)
                if kind == "concepts":
                    concept = _parse_concept(value, "concept")
                    _validate_index_references(bundle, (concept,), ())
                    if concept.locator in concepts or concept.document.canonical_path in pages:
                        raise KnowledgeStorageError("concept", "duplicate locator or canonical page")
                    concepts[concept.locator] = getattr(concept.concept_kind, "value", concept.concept_kind)
                    pages[concept.document.canonical_path] = concept.locator
                    if canonical_bytes(_concept_to_payload(concept)) != canonical_bytes(value):
                        raise KnowledgeStorageError(kind, "noncanonical native record")
                elif kind == "relationships":
                    relation = _parse_relationship(value, "relationship")
                    target = relation.target
                    if (relation.source_locator not in concepts or relation.resolution is Resolution.RESOLVED and
                            (target.locator is not None and target.locator not in concepts or
                             target.canonical_path is not None and target.canonical_path not in pages)):
                        raise KnowledgeStorageError(kind, "does not reference a concept or page")
                    if canonical_bytes(_relationship_to_payload(relation)) != canonical_bytes(value):
                        raise KnowledgeStorageError(kind, "noncanonical native record")
                elif kind == "edges":
                    from .knowledge_graph import _normalise_edge
                    if canonical_bytes(_normalise_edge(value, "edge", concepts)) != canonical_bytes(value):
                        raise KnowledgeStorageError(kind, "noncanonical native edge")
                if kind == "extensions":
                    if row["id"] in extensions or row["id"] in {TYPED_GRAPH_EXTENSION_KEY, SECTION_OWNERSHIP_EXTENSION_KEY}:
                        raise KnowledgeStorageError(kind, "duplicate or misplaced extension")
                    extensions[row["id"]] = value
                else:
                    records[kind].add(value)
        extra = {}
        for kind, key, metadata, field in (("edges", TYPED_GRAPH_EXTENSION_KEY, "graph", "edges"),
                                            ("sections", SECTION_OWNERSHIP_EXTENSION_KEY, "sections", "pages")):
            if reader.root["metadata"][metadata] is not None:
                extra[key] = {**reader.root["metadata"][metadata], field: CanonicalArray(records[kind])}
            elif records[kind].count:
                raise KnowledgeStorageError(kind, "missing extension metadata")
        payload = {"schema_version": LOGICAL_SCHEMA, "bundle": reader.root["bundle"],
                   "concepts": CanonicalArray(records["concepts"]),
                   "relationships": CanonicalArray(records["relationships"])}
        if reader.root["metadata"]["has_extensions"]:
            payload["extensions"] = _Extensions(extensions, extra)
        elif extensions or extra:
            raise KnowledgeStorageError("extensions", "extension metadata mismatch")
        if logical_digest(payload) != reader.root["logical_hash"]:
            raise KnowledgeStorageError("knowledge", "logical commitment mismatch")
        for row in reader.records("values"):
            if row["owner"] != "shared" or digest(canonical_bytes(row["value"])) != row["id"]:
                raise KnowledgeStorageError("values", "descriptor identity mismatch")
            expand(row)
        audit_spilled_records(reader, payload, stack)
        if isinstance(reader, PackedKnowledgeStoreReader):
            reader.audit_containers()
        session.recheck()
        return {"schema_version": "llm-wiki-storage-audit/v1", "ok": True,
                "validation_scope": "complete-storage-and-routing", "whole_snapshot_validated": False,
                "logical_hash": reader.root["logical_hash"], "records": {k: r.count for k, r in records.items()},
                "objects": len(reader.objects), "bytes_read": session.bytes_read, "reads": session.reads,
                "expanded_bytes": reader.expanded_bytes, "streaming_record_limit": record_bytes}
