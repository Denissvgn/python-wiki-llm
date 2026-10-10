"""Bind optional task implementation comparisons to their captured inputs."""

from __future__ import annotations

from collections.abc import Mapping

from .knowledge_envelope import ConsumedInput, hash_source_snapshot
from .python_implementation import analysis_identity

SCHEMA = "llm-wiki-task-implementation-capture/v1"


def native_bindings(concepts):
    """Extract owner bindings from consumed native records, never display names."""
    from .knowledge_storage import canonical_bytes, digest
    from .implementation_evidence import validate_implementation_evidence

    result = {}
    for concept in concepts or ():
        if isinstance(concept, Mapping):
            extensions, locator = concept.get("extensions", {}), concept.get("locator")
        else:
            extensions, locator = concept.extensions, concept.locator
        primary = extensions.get("llm-wiki/implementation")
        if primary is not None:
            primary = validate_implementation_evidence(primary)
        supplemental = extensions.get("llm-wiki/implementation-declarations")
        owner = primary if primary is not None else (supplemental or {}).get("owner")
        if owner is not None:
            result[locator] = {"coordinate": dict(owner["coordinate"]), "scope": owner["scope"],
                               "recorded_hash": digest(canonical_bytes(dict(primary))) if primary is not None else None}
    return result


def attach_bindings(body, bindings):
    locators = {locator for fact in body["facts"]
                for _, observed, declaration in _comparisons(fact)
                if not declaration and isinstance((locator := observed.get("locator")), str)}
    if locators:
        body["implementation_bindings"] = {key: bindings[key] for key in sorted(locators) if key in bindings}
    return body


def capture_receipt(inventory_result):
    if inventory_result is None or inventory_result.implementation_observations is None:
        return None
    snapshot = inventory_result.source_snapshot
    if snapshot is None:
        return None
    return {"schema_version": SCHEMA,
            "inputs": [{"path": row.path, "content_hash": row.content_hash, "kind": row.kind_value}
                       for row in snapshot.to_consumed_inputs()],
            "analysis_compatibility_hash": analysis_identity(inventory_result.analysis_components)}


def _comparisons(fact):
    observed = fact.get("observation")
    if not isinstance(observed, Mapping):
        return
    if "implementation" in observed:
        yield observed["implementation"], observed, True
    concept = observed.get("concept")
    if isinstance(concept, Mapping) and "implementation" in concept:
        yield concept["implementation"], concept, False
    for key in ("matches", "concepts", "related_concepts"):
        for row in observed.get(key, ()):
            if isinstance(row, Mapping) and "implementation" in row:
                yield row["implementation"], row, False


def attach_capture(body, inventory_result):
    if any(list(_comparisons(fact)) for fact in body["facts"]):
        receipt = capture_receipt(inventory_result)
        if receipt is not None:
            body["implementation_capture"] = receipt
    return body


def validate_task_implementations(payload, settings):
    from .implementation_evidence import validate_implementation_comparison
    from .knowledge_evidence import is_valid_sha256

    comparisons = [(item, fact) for fact in payload["facts"] for item in _comparisons(fact)]
    receipt = payload.get("implementation_capture")
    bindings = payload.get("implementation_bindings", {})
    if not isinstance(bindings, dict):
        raise ValueError("invalid implementation native bindings")
    source_hashes = {}
    analysis_hash = None
    if receipt is not None:
        if not isinstance(receipt, dict) or set(receipt) != {"schema_version", "inputs", "analysis_compatibility_hash"} or receipt["schema_version"] != SCHEMA:
            raise ValueError("invalid task implementation capture")
        if not isinstance(receipt["inputs"], list):
            raise ValueError("invalid task implementation input set")
        inputs = []
        for row in receipt["inputs"]:
            if not isinstance(row, dict) or set(row) != {"path", "content_hash", "kind"}:
                raise ValueError("invalid task implementation source input")
            inputs.append(ConsumedInput(**row))
        source_hashes = {row.path: row.content_hash for row in inputs}
        if len(source_hashes) != len(inputs) or hash_source_snapshot(inputs) != payload["basis"]["consumed_source"]:
            raise ValueError("task implementation inputs differ from captured source")
        analysis_hash = receipt["analysis_compatibility_hash"]
        if analysis_hash is not None and not is_valid_sha256(analysis_hash):
            raise ValueError("invalid implementation analysis capture identity")
        if payload["basis"]["source"] is None or not comparisons:
            raise ValueError("uncaptured task cannot claim implementation capture")
        existing = payload.get("source_capture")
        if isinstance(existing, dict) and existing.get("inputs") != receipt["inputs"]:
            raise ValueError("implementation and scoped source receipts disagree")
    expected_scope = {"selected": "selected-source", "full-inventory": "full-inventory", "snapshot": "snapshot"}[payload["basis"]["scope"]]
    for (raw, observed, declaration), fact in comparisons:
        if settings["knowledge_mode"] == "off":
            raise ValueError("native-off task cannot include implementation evidence")
        comparison = validate_implementation_comparison(raw)
        if comparison["analysis_scope"] != expected_scope:
            raise ValueError("implementation comparison exceeds captured task scope")
        coordinate = comparison["coordinate"]
        if declaration and coordinate is not None:
            expected = {"source_path": observed["path"], "qualified_owner": observed["symbol"], "occurrence": observed["occurrence"]}
            if coordinate != expected:
                raise ValueError("implementation declaration differs from exact selector")
            kind = observed.get("kind")
            kind_scope = "class" if kind == "class" else "callable"
            if comparison["scope"] != kind_scope:
                raise ValueError("implementation scope differs from declaration kind")
        elif not declaration:
            source = observed.get("source_path") or (observed.get("facets", {}).get("structure", {}).get("basis") or {}).get("source_path")
            if coordinate is not None and source is not None and coordinate["source_path"] != source:
                raise ValueError("implementation source differs from native concept")
            kind = observed.get("page_kind") or observed.get("document", {}).get("page_kind")
            expected = {"modules": "module", "entities": "class"}.get(kind)
            if expected is not None and comparison["scope"] not in {None, expected}:
                raise ValueError("implementation scope differs from native page")
            persisted = observed.get("extensions", {}).get("llm-wiki/implementation")
            if persisted is not None and comparison["recorded"] != persisted:
                raise ValueError("implementation recorded basis differs from consumed native record")
            if coordinate is not None:
                from .knowledge_storage import canonical_bytes, digest

                binding = bindings.get(observed.get("locator"))
                if not isinstance(binding, dict) or set(binding) != {"coordinate", "scope", "recorded_hash"}:
                    raise ValueError("implementation native owner binding is missing")
                recorded_hash = digest(canonical_bytes(comparison["recorded"])) if comparison["recorded"] is not None else None
                if binding["coordinate"] != coordinate or binding["scope"] != comparison["scope"] or binding["recorded_hash"] != recorded_hash:
                    raise ValueError("implementation owner differs from consumed native binding")
        live = comparison["live"]
        if live is not None:
            path = live["coordinate"]["source_path"]
            if receipt is None or path not in source_hashes or live["source_hash"] != source_hashes[path]:
                raise ValueError("implementation live source is outside captured inputs")
            if live["producer"]["analysis_compatibility_hash"] != analysis_hash:
                raise ValueError("implementation producer differs from captured analysis")
        if comparison["live_comparison_performed"] and receipt is None:
            raise ValueError("implementation verdict has no independent capture receipt")
        if expected_scope == "snapshot" and comparison["state"] != "unavailable":
            raise ValueError("snapshot task cannot claim executable unchanged or changed")
