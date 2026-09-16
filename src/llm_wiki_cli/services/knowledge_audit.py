"""Independent logical membership checks, without rebuilding physical storage."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
from itertools import groupby, zip_longest
from typing import Any

from .knowledge_storage import (
    COLLECTIONS, KnowledgeStorageError, _Encoder, _concept_aliases, _node_aliases, _owner,
    canonical_bytes, digest, _text, _LOOKUP_GROUP_TARGET,
)
from .contracts import SECTION_OWNERSHIP_EXTENSION_KEY, TYPED_GRAPH_EXTENSION_KEY


def expected_records(payload, basis, *, spills=None):
    """Derive record identities, owners and aliases from logical facts.

    Partitioning, tree construction, pack writing and supplied lookup rows are
    deliberately absent. Only the shared reversible value codec is reused.
    """
    encoder = _Encoder(basis)
    aliases: Any
    if spills is None:
        owners, pages = {}, {}
        aliases = defaultdict(set)
        seen = Counter()
    else:
        from .storage_spool import ByteSpool, JsonSpool
        from .storage_sort import SortedRuns
        def mapping():
            return JsonSpool(spills.enter_context(ByteSpool()))
        owners, pages, seen = mapping(), mapping(), mapping()
        encoder.values = mapping()
        aliases = spills.enter_context(SortedRuns())
    for concept in payload["concepts"]:
        owners[concept["locator"]] = _owner(concept)
        pages[concept["document"]["canonical_path"]] = _owner(concept)

    def record(kind, rid, owner, value, keys):
        _text(owner, kind + ".owner")
        _text(rid, kind + ".id")
        for key in set(keys):
            _text(key, "lookup.owner")
            if spills is None:
                aliases[(key, kind, owner)].add(rid)
            else:
                aliases.add([key, kind, owner, rid])
        return kind, owner, rid, encoder.encode(value)

    for concept in payload["concepts"]:
        yield record("concepts", concept["locator"], owners[concept["locator"]], concept, _concept_aliases(concept))
    for relation in payload["relationships"]:
        encoded = encoder.encode(relation)
        key = digest(canonical_bytes(encoded))
        seen[key] = seen.get(key, 0) + 1
        source = _text(relation["from"], "relationship.from")
        owner = owners.get(source, "concept:" + source)
        keys = {owner, "out:concept:" + source, *("in:" + k for k in _node_aliases(relation["target"]))}
        yield record("relationships", f"{key}:{seen[key]}", owner, relation, keys)
    extensions = payload.get("extensions", {})
    graph = extensions.get(TYPED_GRAPH_EXTENSION_KEY)
    if graph is not None:
        for edge in graph["edges"]:
            node = edge["from"]
            keys = _node_aliases(node)
            source_keys = sorted(k for k in keys if k.startswith("source:"))
            if source_keys:
                owner = source_keys[0]
            else:
                locator = _text(node.get("locator") if isinstance(node, dict) else node, "edge.from")
                owner = owners.get(locator, min(keys) if keys else "edge:" + edge["key"])
            aliases_for_edge = {owner, *("out:" + k for k in keys), *("in:" + k for k in _node_aliases(edge["target"]))}
            yield record("edges", edge["key"], owner, edge, aliases_for_edge)
    sections = extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY)
    if sections is not None:
        for section in sections["pages"]:
            locator = section["page_locator"]
            owner = owners.get(locator, pages.get(locator, "page:" + locator))
            yield record("sections", locator, owner, section, {owner, "concept:" + locator, "page:" + locator})
    for name, value in extensions.items():
        if name not in {TYPED_GRAPH_EXTENSION_KEY, SECTION_OWNERSHIP_EXTENSION_KEY}:
            yield record("extensions", name, name, value, {"extension:" + name})
    for key, value in encoder.values.items():
        yield "values", "shared", key, value

    def groups(alias, kind, owner, ids, prefix=""):
        identity = {"collection": kind, "owner": owner, "prefix": prefix}
        rid = digest(canonical_bytes(identity))
        value = {**identity, "ids": ids}
        row = {"owner": alias, "id": rid, "value": value}
        if len(ids) == 1 or len(canonical_bytes(row)) <= _LOOKUP_GROUP_TARGET:
            yield "lookup", alias, rid, value
            return
        if len(prefix) >= 64:
            raise KnowledgeStorageError("lookup", "unsplittable reference group")
        partitions: dict[str, list[str]] = defaultdict(list)
        for item in ids:
            partitions[hashlib.sha256(item.encode()).hexdigest()[len(prefix)]].append(item)
        for nibble, items in sorted(partitions.items()):
            yield from groups(alias, kind, owner, items, prefix + nibble)

    if spills is None:
        for (alias, kind, owner), ids in aliases.items():
            yield from groups(alias, kind, owner, sorted(ids))
    else:
        for (alias, kind, owner), items in groupby(aliases, key=lambda row: tuple(row[:3])):
            ids = []
            size = 0
            for item in items:
                rid = item[3]
                if ids and ids[-1] == rid:
                    continue
                size += len(rid.encode("utf-8")) + 64
                if size > 8_388_608:
                    raise KnowledgeStorageError("lookup", "alias group exceeds streaming spill bound", code="storage-limit")
                ids.append(rid)
            yield from groups(alias, kind, owner, ids)


def audit_logical_records(reader, payload: dict[str, Any]) -> None:
    """Compare complete independent record sets without encoding a second store."""
    actual = {}
    for collection in COLLECTIONS:
        for row in reader.records(collection):
            key = collection, row["owner"], row["id"]
            if key in actual:
                raise KnowledgeStorageError(collection, "duplicate logical record")
            actual[key] = hashlib.sha256(canonical_bytes(row["value"])).digest()
    for kind, owner, rid, value in expected_records(payload, reader.root["basis"]):
        if actual.pop((kind, owner, rid), None) != hashlib.sha256(canonical_bytes(value)).digest():
            raise KnowledgeStorageError(kind, "does not exactly index the logical knowledge")
    if actual:
        raise KnowledgeStorageError(next(iter(actual))[0], "contains records outside the logical knowledge")


def audit_spilled_records(reader, payload, stack) -> None:
    """Complete exact membership comparison with bounded private merge runs."""
    from .storage_sort import SortedRuns
    actual = stack.enter_context(SortedRuns())
    expected = stack.enter_context(SortedRuns())
    for collection in COLLECTIONS:
        for row in reader.records(collection):
            actual.add([collection, row["owner"], row["id"], digest(canonical_bytes(row["value"]))])
    for kind, owner, rid, value in expected_records(payload, reader.root["basis"], spills=stack):
        expected.add([kind, owner, rid, digest(canonical_bytes(value))])
    previous = None
    for left, right in zip_longest(actual, expected):
        if left != right or left is None:
            raise KnowledgeStorageError("routing", "does not exactly index the logical knowledge")
        if previous == left[:3]:
            raise KnowledgeStorageError("routing", "duplicate logical record")
        previous = left[:3]
