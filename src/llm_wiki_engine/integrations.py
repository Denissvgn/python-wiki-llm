"""Providers the knowledge core borrows from the application that embeds it.

The knowledge core stores, validates and maintains knowledge without knowing
how sources are analyzed. A few of its checks need that knowledge: concept
implementation evidence comes from a language analysis, source snapshots come
from the application's view of the source tree, and some operations accept
only objects the application issued. The application names a module for each
capability below; the engine imports it on first use and reads its attributes
at call time, so a replaced attribute takes effect immediately.

A capability nobody provided fails closed with :class:`IntegrationUnavailable`.
"""

from __future__ import annotations

import importlib
import re
from collections.abc import Mapping
from types import MappingProxyType, ModuleType

# Each capability, and what the knowledge core uses from its provider module.
CAPABILITIES: Mapping[str, str] = MappingProxyType({
    "implementation_evidence": (
        "validators and comparisons for concept implementation evidence "
        "(IMPLEMENTATION_KEY, DECLARATIONS_KEY, validate_concept_implementation, "
        "validate_implementation_collection, validate_implementation_evidence, "
        "compare_knowledge_implementation, compare_implementation_observations, "
        "ImplementationReport)"
    ),
    "implementation_analysis": (
        "the analysis that produces implementation evidence (comparison_id, "
        "analysis_identity and its format constants)"
    ),
    "source_snapshots": (
        "the application's captured view of the source tree (SourceSnapshot, "
        "build_source_snapshot, capture_source_selection_inputs, "
        "source_snapshot_matches_current_files, confirmed_missing_source_paths)"
    ),
    "bootstrap_recovery": "guard_incomplete_bootstrap for an interrupted first bootstrap",
    "committed_knowledge": "CommittedKnowledgeState, the issued prior knowledge closure of one sync",
    "page_transitions": "PageTransitionPlan, the verified page-owner plan of one sync",
    "entity_ownership": "_recorded_entity_pages, recorded entity page owners of a manifest",
    "maintenance_reports": "maintenance_report_from_captured for captured maintenance status",
    "inventory_results": "InventoryResult, one captured source inventory",
    "domain_packs": "current_pack, the active domain pack (classifier and page namer)",
})

_MODULE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
_PROVIDED: dict[str, str] = {}


class IntegrationUnavailable(LookupError):
    """The application did not provide a capability the knowledge core needs."""


def provide(modules: Mapping[str, str]) -> None:
    """Name the provider module of each capability; a capability is provided once."""
    for capability, module in modules.items():
        if capability not in CAPABILITIES:
            raise ValueError(f"unknown knowledge-core capability: {capability!r}")
        if not isinstance(module, str) or not _MODULE.fullmatch(module):
            raise ValueError(f"capability {capability!r} needs a module name, got {module!r}")
        current = _PROVIDED.get(capability)
        if current is not None and current != module:
            raise ValueError(f"capability {capability!r} is already provided by {current}")
    _PROVIDED.update(modules)


def provider(capability: str) -> ModuleType:
    """Return the module providing *capability*, importing it on first use."""
    if capability not in CAPABILITIES:
        raise ValueError(f"unknown knowledge-core capability: {capability!r}")
    module = _PROVIDED.get(capability)
    if module is None:
        raise IntegrationUnavailable(
            f"the knowledge core needs a {capability} provider: {CAPABILITIES[capability]}"
        )
    return importlib.import_module(module)


def attributes(capability: str, *names: str) -> tuple:
    """Read *names* from the provider of *capability* now, as a lazy import would."""
    module = provider(capability)
    return tuple(getattr(module, name) for name in names)


def provided() -> Mapping[str, str]:
    """The provider module named for each capability so far."""
    return MappingProxyType(dict(_PROVIDED))
