"""Pure evidence selection from a single existing captured read."""

from __future__ import annotations

from collections import Counter
from typing import Any

from . import context_packet as packets
from .documentation_query_builder import build_documentation_query_service_from_view
from .markdown_sections import parse_markdown_document
from .workflow_profile import content_id


def declaration_records(inventory):
    """Index extractor-owned contracts without re-parsing source code."""
    result = []
    for path, module in sorted(inventory.items()):
        occurrences = Counter()

        def add(contract, owner, kind):
            name = contract.get("name")
            if not isinstance(name, str):
                return
            symbol = f"{owner}.{name}" if owner else name
            occurrences[symbol] += 1
            ordinal = occurrences[symbol]
            result.append({"path": path, "symbol": symbol, "name": name, "owner": owner,
                           "occurrence": ordinal, "kind": contract.get("kind", kind),
                           "line": contract.get("line"), "language": module.get("language"),
                           "selector": f"{path}:{symbol}#{ordinal}",
                           "contract": packets._thaw_json(contract)})
        for function in module.get("functions", ()):
            add(function, "", "function")
        for cls in module.get("classes", ()):
            add(cls, "", "class")
            for method in cls.get("methods", ()):
                add(method, cls["name"], "method")
    return result


def match_declarations(records, selector):
    file, separator, symbol = selector.partition(":")
    if not separator:
        file, symbol = None, selector
    raw, mark, ordinal = symbol.rpartition("#")
    occurrence = int(ordinal) if mark and ordinal.isdigit() else None
    if occurrence is not None:
        symbol = raw
    return [record for record in records
            if (file is None or record["path"] == file)
            and (record["symbol"] == symbol or (file is None and record["name"] == symbol))
            and (occurrence is None or record["occurrence"] == occurrence)]


def query_service(captured, limit):
    return build_documentation_query_service_from_view(
        wiki_root=captured.wiki_root, knowledge_view=captured.knowledge_view,
        limit=limit, inventory=captured.inventory, call_edges=captured.call_edges,
        flows=captured.flows, data_flows=captured.data_flows,
        dependency_analysis=captured.dependency_analysis,
        surface_index=captured.surface_evaluation.payload,
    )


def observe_requirement(captured, service, records, requirement, *, scope, limit):
    facet, selector = requirement["facet"], requirement["selector"]
    qualification = {"analysis_scope": scope, "freshness": "captured-live",
                     "semantic_review": "not-evaluated", "behavior": "not-evaluated",
                     "negative_claim_supported": False}
    citations: list[dict[str, Any]] = []
    if facet == "behavior":
        return "unsupported", None, "host-behavioral-verification-required"
    if facet == "source-contract":
        matches = match_declarations(records, selector)
        if not matches:
            return "missing", None, "declaration-not-in-captured-scope"
        if len(matches) != 1:
            return "ambiguous", None, "select-an-exact-owner-and-occurrence"
        observed = matches[0]
        citations = [{"path": observed["path"], "line": observed["line"],
                      "source_identity": captured.source_snapshot.captured_content_hashes.get(observed["path"])}]
        if type(observed["line"]) is not int or observed["line"] < 1:
            return "unsupported", None, "exact-source-location-unavailable"
        state, reason = "present", "exact-declaration-observed"
    else:
        methods = {"callers": service.callers, "callees": service.callees,
                   "concept": service.get_concept, "semantic-section": service.list_concept_sections,
                   "typed-relationships": service.traverse_typed_graph,
                   "entrypoint": service.flow_for_entrypoint, "dependency": service.dependency_neighborhood}
        if facet == "semantic-section":
            observed = methods[facet](selector, ownership="semantic")
        else:
            observed = methods[facet](selector)
        if observed.get("ambiguous"):
            return "ambiguous", None, "select-an-exact-owner-and-occurrence"
        native = observed.get("knowledge")
        native_stale = False
        if native is not None:
            qualification["native"] = native
            qualification["freshness"] = "snapshot"
            if native.get("availability") not in {"ready", None}:
                return "unavailable", None, str(native.get("reason", "native-unavailable"))
            freshness = (observed.get("concept") or {}).get("freshness") or {}
            native_stale = freshness.get("state") in {"source-changed", "source-missing", "stale"}
            if native_stale:
                qualification["freshness"] = "stale"
        if not observed.get("found"):
            return "missing", None, "no-exact-observation-in-captured-scope"
        key = {"callers": "callers", "callees": "callees", "concept": "concept",
               "semantic-section": "sections", "typed-relationships": "edges",
               "entrypoint": "flow", "dependency": "dependencies"}[facet]
        if facet in {"callers", "callees", "semantic-section", "typed-relationships"} and not observed.get(key):
            return "unknown", None, "empty-static-result-does-not-prove-absence"
        if facet == "dependency" and not observed.get("inbound") and not observed.get("outbound"):
            return "unknown", None, "empty-static-result-does-not-prove-absence"
        state, reason = "present", "qualified-observation-emitted"
        if observed.get("truncated"):
            state, reason = "partial", "query-limit-omits-observations"
        if facet in {"callers", "callees", "dependency", "typed-relationships"}:
            qualification["graph_completeness"] = "static-observations-only"
            if requirement["criterion"] == "complete":
                state, reason = "partial", "complete-runtime-graph-not-established"
        if native_stale:
            state, reason = "stale", "native-observation-is-stale"
        concept = observed.get("concept") or {}
        if concept.get("canonical_path"):
            citations = [{"path": concept["canonical_path"], "wiki_identity": captured.wiki_anchor}]
        if facet == "semantic-section":
            concept = observed.get("concept") or {}
            path = (concept.get("document") or {}).get("canonical_path") or concept.get("canonical_path")
            if path is None:
                path = next((p["canonical_path"] for p in captured.surface_evaluation.payload["pages"]
                             if p["canonical_path"] == selector), None)
            text = captured.surface_evaluation.content_by_path.get(path) if path else None
            if text is None:
                return "unavailable", None, "authored-section-content-unavailable"
            parsed = parse_markdown_document(text, str(concept.get("locator") or selector))
            exact = {(s.title, s.sibling_occurrence): s for s in parsed.sections}
            sections = []
            for section in observed["sections"][:limit]:
                selected = exact.get((section.get("title"), section.get("occurrence", 1)))
                if selected is not None:
                    sections.append({**section, "content": selected.exact_text,
                                     "content_identity": selected.exact_hash})
            if not sections:
                return "unavailable", None, "exact-semantic-sections-unavailable"
            observed["sections"] = sections
            citations = [{"path": path, "wiki_identity": captured.wiki_anchor}]
        if not citations:
            selected = observed.get("callable") or observed.get("symbol") or {}
            if selected.get("file"):
                citations = [{"path": selected["file"], "source_identity":
                    captured.source_snapshot.captured_content_hashes.get(selected["file"])}]
            elif facet == "dependency":
                citations = [{"path": selector, "source_identity":
                    captured.source_snapshot.captured_content_hashes.get(selector)}]
    fact = {"facet": facet, "selector": observed["selector"] if facet == "source-contract" else selector, "state": state,
            "observation": packets._thaw_json(observed), "citations": citations,
            "qualification": qualification}
    fact["fact_id"] = content_id("llm-wiki-task-fact/v1", fact)
    return state, fact, reason


def coverage(requirements, observations, facts):
    emitted = {fact["fact_id"] for fact in facts}
    result = []
    for requirement in requirements:
        state, fact, reason = observations[requirement["id"]]
        ids = [fact["fact_id"]] if fact is not None and fact["fact_id"] in emitted else []
        if fact is not None and not ids:
            state, reason = "omitted", "output-budget-omits-required-evidence"
        result.append({"requirement_id": requirement["id"], "state": state,
                       "satisfied": state == "present" and bool(ids),
                       "fact_ids": ids, "reason": reason})
    return result
