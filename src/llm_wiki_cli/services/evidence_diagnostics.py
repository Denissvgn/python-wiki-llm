"""Explain captured versus fresh evidence without repairing or accepting it."""

from __future__ import annotations

import json

from .knowledge_consumption import KnowledgeReadView
from .knowledge_model import ComputedFreshness, ConceptRecord, EvidenceState


def _label(value: str | None) -> str:
    if value is None:
        return "unavailable"
    return json.dumps(value[:128], ensure_ascii=True) + (" [truncated]" if len(value) > 128 else "")


def captured_evidence_diagnostic(
    view: KnowledgeReadView,
    concept: ConceptRecord,
) -> tuple[str, str] | None:
    """Return bounded interpretation/guidance over this read's existing inputs.

    Fresh normalization is distinct from committed evidence and compatible
    structural comparison. Neither versions nor matching metadata identify
    historical package bytes. This consumer never extracts, writes or changes
    evidence/freshness states.
    """

    manifest = view.manifest_basis
    if view.knowledge is None or manifest is None:
        return None
    baseline = manifest.evidence_baselines.get(concept.document.canonical_path)
    stored = None if baseline is None else baseline.basis
    freshness = None if view.freshness is None else view.freshness.by_locator.get(concept.locator)
    live = None if freshness is None else freshness.live_basis
    captured_bad = concept.facets.structure.evidence is not EvidenceState.PRESENT
    if not captured_bad and (live is None or live.unknown_reason is None):
        return None

    cause = None if baseline is None else baseline.unknown_reason
    description = (
        f"Captured evidence is unavailable [captured cause={_label(cause)}]."
        if captured_bad else "Captured evidence was present."
    )
    read_hint = (
        "Inspect fresh raw output with llm-wiki extract --deep --read-only "
        "--paths <source-path>, preserving --src-dir, source selection and "
        "prepared helper cache. This read does not commit a repair."
    )
    if live is None:
        return (
            description + " Fresh result is untested or unavailable in this read; "
            "a captured failure alone does not establish a current extractor defect.",
            read_hint + " Resolve unavailable extraction prerequisites before owning sync.",
        )

    mapping = manifest.page_source_mappings.get(concept.document.canonical_path)
    same_coordinate = (
        mapping is not None and mapping.source_path == live.source_path
        and mapping.scope == live.scope.value
        and (stored is None or (stored.source_path == live.source_path and stored.scope == live.scope.value))
    )
    if not same_coordinate:
        source_status = "not comparable (source mapping or scope differs)"
    elif stored is None:
        source_status = "unavailable (historical source basis not captured)"
    else:
        source_status = "unchanged" if stored.source_content_hash == live.source_content_hash else "changed"
    description += f" Captured source bytes: {source_status}."

    prior = view.knowledge.bundle.producer
    current = None if view.freshness is None else view.freshness.live_producer
    metadata = "unavailable" if current is None else "matching" if prior == current else "different"
    description += (
        f" Captured/current producer metadata: {metadata}; versions "
        f"{_label(prior.tool.version)}/{_label(None if current is None else current.tool.version)}. "
        "Version labels and metadata do not establish historical artifact identity."
    )
    if live.unknown_reason == "invalid-inventory-shape":
        return (
            description + " Fresh normalization still rejects the current observation "
            "[fresh cause=invalid-inventory-shape]; this is a current producer/consumer failure.",
            read_hint + " Repair the current producer/normalization cause before owning sync; "
            "do not bypass an invalid-evidence gate with --force.",
        )
    if live.unknown_reason is not None or live.concept_observation_hash is None or live.analysis_basis_hash is None:
        return (
            description + f" Fresh evidence remains unavailable [fresh cause={_label(live.unknown_reason)}].",
            read_hint + " Resolve the current coverage, helper or producer-basis gap before owning sync.",
        )
    if current is not None:
        components = [current.tool, *current.plugins, *(
            component for component in current.extractors if component.component_id == live.extractor_ref
        )]
        if any(c.configuration_hash is None or c.version.casefold() in {"unknown", "unavailable"} for c in components):
            return (
                description + " Fresh producer-basis metadata is incomplete; normalization alone cannot establish compatible evidence.",
                read_hint + " Resolve the current producer-basis gap before owning sync.",
            )
    if (
        not same_coordinate
        or (stored is not None and stored.extractor_ref != live.extractor_ref)
        or (freshness is not None and freshness.state is ComputedFreshness.BASIS_INCOMPATIBLE)
    ):
        return (
            description + " Fresh normalization is valid, but its basis is not compatible with the recorded coordinate/basis.",
            read_hint + " Resolve the mapping or producer-basis incompatibility through the owning workflow.",
        )
    return (
        description + " Fresh normalization is valid; captured evidence is not repaired "
        "or proven current by this read. Historical rejected-record details are unavailable in this diagnosis.",
        read_hint + " Run owning sync to regenerate and commit coherent evidence, then repeat strict validation. "
        "If the broad-update guard refuses sync, inspect its same-binding --dry-run plan and "
        "review it before explicitly authorizing --force; never force automatically on upgrade.",
    )
