"""One bounded concept inspection over one captured native read view."""

import json
from pathlib import Path
from typing import Any

from . import context_packet
from .documentation_queries import (
    DocumentationQueryError,
    QUERY_RESULT_SERIALIZED_BYTE_LIMIT,
)
from .documentation_query_builder import (
    build_documentation_query_service_from_view,
    build_snapshot_documentation_query_service,
)
from .knowledge_coverage import MAX_COVERAGE_BYTES, build_knowledge_coverage


NATIVE_INSPECTION_SCHEMA_VERSION = "llm-wiki-native-inspection/v1"
MAX_INSPECTION_BYTES = 256 * 1024


def inspect_native_concept(
    coordinate: str,
    *,
    src_dir: str,
    wiki_root: Path,
    live: bool,
    limit: int,
    include_evidence: bool,
    allow_external_src: bool,
    source_selection: str | Path | None,
    helper_cache_dir: str | Path | None,
) -> dict[str, Any]:
    """Compose existing queries, then check that their common inputs still hold."""
    captured = None
    if live:
        captured = context_packet.capture_context_read(
            src_dir,
            str(wiki_root),
            read_only=True,
            allow_external_src=allow_external_src,
            source_selection=source_selection,
            helper_cache_dir=None
            if helper_cache_dir is None
            else str(helper_cache_dir),
        )
        service = build_documentation_query_service_from_view(
            wiki_root=wiki_root,
            knowledge_view=captured.knowledge_view,
            limit=limit,
            inventory=captured.inventory,
            call_edges=captured.call_edges,
            flows=captured.flows,
            data_flows=captured.data_flows,
            dependency_analysis=captured.dependency_analysis,
            surface_index=captured.surface_evaluation.payload,
        )
        wiki_anchor = captured.wiki_anchor
    else:
        wiki_anchor = context_packet._wiki_anchor(wiki_root)
        service = build_snapshot_documentation_query_service(
            wiki_root=wiki_root, limit=limit
        )

    concept = service.get_concept(coordinate)
    graph = service.traverse_typed_graph(coordinate, include_evidence=include_evidence)
    sections = service.list_concept_sections(coordinate)
    assert service.knowledge_view is not None
    coverage = build_knowledge_coverage(service.knowledge_view)
    result = {
        "schema_version": NATIVE_INSPECTION_SCHEMA_VERSION,
        "read_scope": coverage["read_scope"],
        "cost": {
            "scope": "full-inventory" if live else "snapshot-only",
            "full_inventory_performed": live,
            "supplied_paths": [],
        },
        "concept": concept,
        "graph": graph,
        "sections": sections,
        "coverage": coverage,
        "limits": {
            "per_collection": limit,
            "per_query_bytes": QUERY_RESULT_SERIALIZED_BYTE_LIMIT,
            "coverage_bytes": MAX_COVERAGE_BYTES,
            "result_bytes": MAX_INSPECTION_BYTES,
        },
        "truncated": any(item["truncated"] for item in (concept, graph, sections)),
    }
    # Each component retains its original response bounds and qualifications.
    # The final cap also covers the combined envelope and aggregate diagnostics.
    if (
        len(
            json.dumps(
                result,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        )
        > MAX_INSPECTION_BYTES
    ):
        raise DocumentationQueryError("inspection exceeds its serialized byte bound")
    if captured is not None:
        context_packet._assert_source_unchanged(
            captured.source_snapshot, captured.source_anchor
        )
    context_packet._assert_wiki_unchanged(wiki_root, wiki_anchor)
    return result
