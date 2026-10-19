"""Read-only CLI explanation adapters over the existing knowledge service."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import platform
import sys
from typing import Any

from .. import __version__
from . import analysis_capture, extractor_helpers, knowledge_reuse
from .documentation_queries import DocumentationGraphQueryService


def explain_source(service: DocumentationGraphQueryService, source: str) -> dict[str, Any]:
    """Select only when an exact source has one concept, otherwise offer choices."""
    candidates = service.concepts_by_source_path.get(source, ())
    if len(candidates) == 1:
        return service.explain_evidence(candidates[0]["locator"])
    matches = [service._compact_knowledge_concept(row["locator"])
               for row in candidates[:service.limit]]
    return {
        "query": {"source": source}, "knowledge": dict(service.knowledge_status),
        "found": False, "ambiguous": len(candidates) > 1,
        "matches": matches, "concept": None, "evidence": None,
        "total": len(candidates), "returned": len(matches),
        "truncated": len(matches) < len(candidates),
        "bounds": {"matches": {"total": len(candidates), "returned": len(matches),
                                "truncated": len(matches) < len(candidates)}},
    }


def explanation_provenance(
    service: DocumentationGraphQueryService, payload: dict[str, Any], *,
    source_root: Path, helper_cache_dir: str | Path | None,
) -> dict[str, Any]:
    """Keep observed installation, stored/live producers and runtime distinct."""
    view = service.knowledge_view
    stored = None if view is None or view.knowledge is None else view.knowledge.bundle.producer
    live = None if view is None or view.freshness is None else view.freshness.live_producer
    evidence = payload.get("evidence") or {}
    freshness = evidence.get("freshness") or {}
    concept = payload.get("concept") or {}
    canonical_path = concept.get("canonical_path")
    baseline = (None if view is None or view.manifest_basis is None or not isinstance(canonical_path, str) else
                view.manifest_basis.evidence_baselines.get(canonical_path))
    captured_basis = None if baseline is None else baseline.basis
    captured = (None if captured_basis is None else
                {**captured_basis.to_evidence_payload(), "unknown_reason": captured_basis.unknown_reason})
    basis = (freshness.get("live_basis") or evidence.get("structure", {}).get("basis")
             or freshness.get("recorded_basis") or captured or {})
    extractor = basis.get("extractor_ref")
    language = extractor.removeprefix("llm-wiki/extractor/") if isinstance(extractor, str) else None
    owner = "typescript" if language == "javascript" else language
    helper = None
    if owner in extractor_helpers.SUPPORTED_HELPERS:
        helper = extractor_helpers.helper_identity(owner, source_root,
                    None if helper_cache_dir is None else str(helper_cache_dir))
    try:
        contract = analysis_capture.registry()["contract"]
    except (OSError, ValueError, KeyError):
        contract = None
    return {
        "package": {"name": "agent-wiki-cli", "version": __version__,
                    "installed_implementation_fingerprint": knowledge_reuse.implementation_hash(),
                    "fingerprint_basis": "installed package files, Python version and tool version",
                    "distribution_archive_digest": None,
                    "qualification": "Installed implementation identity; original wheel/archive identity unavailable."},
        "inventory_contract": contract,
        "captured_source_basis": captured,
        "live_source_basis": freshness.get("live_basis"),
        "stored_producer": None if stored is None else asdict(stored),
        "live_producer": None if live is None else asdict(live),
        "active_runtime": {"implementation": platform.python_implementation(),
                           "version": platform.python_version(), "executable": sys.executable,
                           "platform": sys.platform, "machine": platform.machine()},
        "helper": helper,
        "helper_qualification": ("Selected concept's external helper" if helper is not None else
            "No external helper selected; choose an exact supported concept for helper identity."),
    }
