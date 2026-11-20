"""Providers the knowledge core borrows from the application that embeds it.

The knowledge core stores, validates and maintains knowledge without knowing
how sources are analyzed. A few of its checks need that knowledge: concept
implementation evidence comes from a language analysis, source snapshots come
from the application's view of the source tree, and some operations accept
only objects the application issued. The application names a module for each
capability below; the engine imports it on first use and reads its attributes
at call time, so a replaced attribute takes effect immediately.

A capability nobody provided fails closed with :class:`IntegrationUnavailable`.

Providers are resolved per context. :func:`provide` names process-wide
defaults. An :class:`IntegrationSet` names providers for one scope, entered with
:func:`using_integrations`; inside it the set's providers win, and a set built
with ``inherit=False`` hides the process-wide defaults entirely. Two engines in
one process can therefore use different providers without seeing each other's.
"""

from __future__ import annotations

import importlib
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
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


def _check(capability: object, module: object) -> None:
    if capability not in CAPABILITIES:
        raise ValueError(f"unknown knowledge-core capability: {capability!r}")
    if not isinstance(module, str) or not _MODULE.fullmatch(module):
        raise ValueError(f"capability {capability!r} needs a module name, got {module!r}")


class IntegrationSet:
    """Provider modules for some capabilities, used inside one scope.

    ``inherit`` decides what an unnamed capability resolves to inside the
    scope: the process-wide default (``True``) or nothing (``False``).
    """

    __slots__ = ("_modules", "_inherit")

    def __init__(self, modules: Mapping[str, str] | None = None, *, inherit: bool = True) -> None:
        if not isinstance(inherit, bool):
            raise TypeError("inherit must be a bool")
        checked: dict[str, str] = {}
        for capability, module in dict(modules or {}).items():
            _check(capability, module)
            checked[capability] = module
        self._modules: Mapping[str, str] = MappingProxyType(dict(sorted(checked.items())))
        self._inherit = inherit

    @property
    def modules(self) -> Mapping[str, str]:
        """The provider module named for each capability in this set."""
        return self._modules

    @property
    def inherit(self) -> bool:
        """Whether unnamed capabilities fall back to the process-wide defaults."""
        return self._inherit

    def merged(self, override: IntegrationSet) -> IntegrationSet:
        """This set with ``override``'s providers on top.

        The result inherits the defaults only when both sets do, so an
        isolated set stays isolated whichever side it is on.
        """
        if not isinstance(override, IntegrationSet):
            raise TypeError("override must be an IntegrationSet")
        return IntegrationSet(
            {**self._modules, **override._modules},
            inherit=self._inherit and override._inherit,
        )

    def describe(self) -> dict[str, object]:
        """A JSON-ready summary of the set."""
        return {"modules": dict(self._modules), "inherit": self._inherit}

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IntegrationSet):
            return NotImplemented
        return self._modules == other._modules and self._inherit == other._inherit

    def __hash__(self) -> int:
        return hash((tuple(self._modules.items()), self._inherit))

    def __repr__(self) -> str:
        return f"IntegrationSet({dict(self._modules)!r}, inherit={self._inherit!r})"


#: A set that names nothing and inherits every process-wide default.
DEFAULT_INTEGRATIONS = IntegrationSet()

_SCOPE: ContextVar[IntegrationSet | None] = ContextVar("llm_wiki_integrations", default=None)


@contextmanager
def using_integrations(integrations: IntegrationSet) -> Iterator[IntegrationSet]:
    """Resolve capabilities inside the block with ``integrations`` first."""
    if not isinstance(integrations, IntegrationSet):
        raise TypeError("integrations must be an IntegrationSet")
    token = _SCOPE.set(integrations)
    try:
        yield integrations
    finally:
        _SCOPE.reset(token)


def provide(modules: Mapping[str, str]) -> None:
    """Name the process-wide default provider of each capability, once each."""
    for capability, module in modules.items():
        _check(capability, module)
        current = _PROVIDED.get(capability)
        if current is not None and current != module:
            raise ValueError(f"capability {capability!r} is already provided by {current}")
    _PROVIDED.update(modules)


def _resolve(capability: str) -> str | None:
    scope = _SCOPE.get()
    if scope is not None:
        module = scope.modules.get(capability)
        if module is not None or not scope.inherit:
            return module
    return _PROVIDED.get(capability)


def provider(capability: str) -> ModuleType:
    """Return the module providing *capability* here, importing it on first use."""
    if capability not in CAPABILITIES:
        raise ValueError(f"unknown knowledge-core capability: {capability!r}")
    module = _resolve(capability)
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
    """The provider module each capability resolves to in this context."""
    resolved = {name: _resolve(name) for name in CAPABILITIES}
    return MappingProxyType({name: module for name, module in resolved.items() if module is not None})


def defaults() -> Mapping[str, str]:
    """The process-wide default provider named for each capability so far."""
    return MappingProxyType(dict(_PROVIDED))
