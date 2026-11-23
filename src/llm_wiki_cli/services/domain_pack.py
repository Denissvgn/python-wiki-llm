"""Domain packs: the replaceable parts of turning sources into wiki pages.

A :class:`DomainPack` bundles the domain decisions the engine asks about:

* a :class:`SourceClassifier` decides which repository files are sources and
  which source kind (for code: language) each one is;
* ``extractors`` name the extractor of each source kind the pack adds, as
  ``"module:attribute"`` entry points the host can import. Built-in languages
  keep their bundled extractors;
* a :class:`PageNamer` names the module and entity pages generated from an
  inventory. Page kinds themselves are fixed by the knowledge format;
* a :class:`PageRenderer` writes the Markdown of every generated page: module
  and entity pages, and the index, workflow, flow, infrastructure, API
  contract, dependency and load-order pages. Each request carries the
  built-in Markdown, so a renderer can adjust it instead of starting over;
* a :class:`ContextSource` decides which sources are related to a changed
  one and how much of each source budgeted context shows at each detail
  level;
* :class:`~.reference_providers.ReferenceProvider` values serve the
  reference kinds a publication policy may declare, so public documentation
  can depend on the pack's contracts;
* a :class:`HelperToolchain` names the analysis helpers a source tree needs
  and prepares (builds or reuses from its cache) the ones an operation may
  use. Helper builds and runs are subprocesses, so they need a host that
  grants them.

The interfaces, page requests and the implementations that need no source
analysis live in :mod:`llm_wiki_engine.pack_interfaces` and are importable here
too. A pack can also name the knowledge-core providers its domain needs
(``integrations``, an :class:`~llm_wiki_engine.integrations.IntegrationSet`).

:data:`CODE_DOCS_PACK` is today's code-documentation behavior and the default.
A host chooses another pack with :func:`using_pack` or ``Engine(pack=...)``;
every call that classifies sources or names pages inside that block uses it.
Pages named by one pack are not renamed by another, so a wiki should keep
using the pack that generated it.

When sync refreshes a page it keeps what people wrote in that page kind's
reviewed sections and takes everything else from the renderer:

* module and entity pages: ``Description`` and the description cells of the
  ``Attributes``, ``Methods``, ``Classes`` and ``Functions`` tables;
* workflow and flow pages: ``Behavior``;
* infrastructure, API contract, dependency and load-order pages: ``Notes``;
* the index: level-two sections under headings it does not write itself.

A renderer that wants people to write there keeps those headings; any section
it adds stays current with sources.

Qualified context packets (and task context, which seals one) need the
built-in :class:`CodeContextSource`: a packet's policy digest names that
ranking, so packets refuse to seal under a pack that replaces it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import PurePath
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from .reference_providers import (
    BUILTIN_REFERENCE_PROVIDERS,
    ReferenceProvider,
    check_reference_providers,
)
from llm_wiki_engine.pack_interfaces import (
    BuiltInPageRenderer as _EngineBuiltInPageRenderer,
    DomainPack as _EngineDomainPack,
    NoContextSource as NoContextSource,
    StemPageNamer as _EngineStemPageNamer,
    _qualified_type_name,
    active_pack,
    using_pack as using_pack,
    PAGE_REQUEST_KINDS,
    ContextDetail,
    ContextSource,
    EntityOccurrenceKey,
    EntityPageRequest,
    ExtensionSourceClassifier,
    HelperToolchain,
    ModulePageRequest,
    NoHelperToolchain,
    PageNamer,
    PageRenderer,
    PageRequest,
    SourceClassifier,
)

if TYPE_CHECKING:
    from .helper_runtime import PreparedHelperHandle
    from .source_snapshot import SourceSnapshot


class BuiltInPageRenderer(_EngineBuiltInPageRenderer):
    """Today's code-documentation pages; subclass it to adjust them."""


def render_with_pack(request: ModulePageRequest | EntityPageRequest | PageRequest) -> str:
    """Render ``request`` with the current pack's page renderer."""
    renderer = current_pack().page_renderer
    if isinstance(request, ModulePageRequest):
        markdown = renderer.render_module(request)
    elif isinstance(request, EntityPageRequest):
        markdown = renderer.render_entity(request)
    else:
        markdown = renderer.render_page(request)
    if not isinstance(markdown, str):
        raise TypeError(
            f"page renderer {_qualified_type_name(renderer)} must return Markdown text"
        )
    return markdown


class CodeContextSource:
    """Code context: import neighbors, then classes and functions by detail."""

    @staticmethod
    def module_for_path(filepath: str) -> str | None:
        """Convert ``"src/llm_wiki_cli/config.py"`` to ``"llm_wiki_cli.config"``.

        Strips a leading ``src/`` directory and the ``.py`` suffix, then
        converts path separators to dots.  Returns None for non-Python files.
        """
        p = PurePath(filepath)
        if p.suffix != ".py":
            return None
        parts = list(p.with_suffix("").parts)
        # Strip leading "src" directory (common in Python projects)
        if parts and parts[0] == "src":
            parts = parts[1:]
        # Strip __init__ (package init files map to the package itself)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts) if parts else None

    def related_sources(self, inventory: Mapping[str, Mapping[str, Any]]) -> dict[str, set[str]]:
        """A bidirectional import adjacency map of the inventory.

        For each file A that imports a symbol from file B (both present in
        *inventory*), adds edges A→B and B→A.  External / stdlib imports are
        silently skipped.  Every key appears even if it has no neighbors.
        """
        module_to_file: dict[str, str] = {}
        for filepath in inventory:
            mod = self.module_for_path(filepath)
            if mod:
                module_to_file[mod] = filepath

        graph: dict[str, set[str]] = {fp: set() for fp in inventory}
        for filepath, file_data in inventory.items():
            for imp in file_data.get("imports", []):
                imp_module = imp.get("module", "")
                if not imp_module:
                    continue
                # Try exact match, then parent module (for ``from pkg.mod import X``)
                target = module_to_file.get(imp_module)
                if target is None:
                    parts = imp_module.split(".")
                    for i in range(len(parts) - 1, 0, -1):
                        target = module_to_file.get(".".join(parts[:i]))
                        if target is not None:
                            break
                if target is not None and target != filepath:
                    graph[filepath].add(target)
                    graph[target].add(filepath)
        return graph

    @staticmethod
    def deep_entry(file_data: Mapping[str, Any]) -> dict[str, Any]:
        """Full detail: classes with methods, params, docstrings, imports."""
        return {k: v for k, v in file_data.items() if k != "language"}

    @staticmethod
    def slim_entry(file_data: Mapping[str, Any]) -> dict[str, Any]:
        """Slim detail: class names/bases/line, function names/lines."""
        return {
            "classes": [
                {"name": c["name"], "bases": c.get("bases", []), "line": c.get("line")}
                for c in file_data.get("classes", [])
            ],
            "functions": [
                {"name": f["name"], "line": f.get("line")}
                for f in file_data.get("functions", [])
            ],
        }

    @staticmethod
    def summary_entry(file_data: Mapping[str, Any]) -> dict[str, Any]:
        """Names only: lists of class names and function names."""
        entry: dict[str, list[str]] = {}
        cls_names = [c["name"] for c in file_data.get("classes", [])]
        fn_names = [f["name"] for f in file_data.get("functions", [])]
        if cls_names:
            entry["classes"] = cls_names
        if fn_names:
            entry["functions"] = fn_names
        return entry

    def entry(self, data: Mapping[str, Any], detail: ContextDetail) -> dict[str, Any]:
        if detail == "deep":
            return self.deep_entry(data)
        if detail == "slim":
            return self.slim_entry(data)
        return self.summary_entry(data)


def context_related_sources(inventory: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Iterable[str]]:
    """Related sources from the current pack's context source."""
    source = current_pack().context_source
    related = source.related_sources(inventory)
    if not isinstance(related, Mapping):
        raise TypeError(
            f"context source {_qualified_type_name(source)} must return a mapping of related sources"
        )
    return related


def context_entry(data: Mapping[str, Any], detail: ContextDetail) -> dict[str, Any]:
    """One source's context entry from the current pack's context source."""
    source = current_pack().context_source
    entry = source.entry(data, detail)
    if not isinstance(entry, Mapping):
        raise TypeError(f"context source {_qualified_type_name(source)} must return a mapping entry")
    return dict(entry)


def uses_builtin_context_source() -> bool:
    """Whether this context ranks and shows sources with :class:`CodeContextSource`."""
    return type(current_pack().context_source) is CodeContextSource


class CodeSourceClassifier(ExtensionSourceClassifier):
    """The built-in languages; Go ``_test.go`` files are opt-in.

    The language table is read live from the extractors, which are imported
    only when a source is first classified.
    """

    def __init__(self) -> None:
        self._test_suffixes = MappingProxyType({"go": ("_test.go",)})

    def _kind_table(self) -> Mapping[str, tuple[str, ...]]:
        from ..extractors.common import LANGUAGE_EXTENSIONS

        return LANGUAGE_EXTENSIONS

    def inventory_language(self, path: str) -> str | None:
        from ..extractors.common import inventory_language_for_path

        kind = super().inventory_language(path)
        return None if kind is None else inventory_language_for_path(kind, path)


class StemPageNamer(_EngineStemPageNamer):
    """Module pages named by source stem, entity pages by entity name."""


class BundledHelperToolchain(HelperToolchain):
    """The bundled Go, Rust, TypeScript and Haskell helpers and their cache."""

    def languages(
        self, snapshot: SourceSnapshot, registry: Mapping[str, str],
        *, only_files: Iterable[str] | None = None,
    ) -> tuple[str, ...]:
        from .helper_runtime import required_helper_languages

        return required_helper_languages(snapshot, registry, only_files=only_files)

    def prepare(
        self, snapshot: SourceSnapshot, registry: Mapping[str, str],
        *, only_files: Iterable[str] | None = None, cache_dir: str | None = None,
    ) -> tuple[PreparedHelperHandle, ...]:
        from .helper_preparation import prepare_operation_helpers

        return prepare_operation_helpers(
            snapshot, registry, only_files=only_files, cache_dir=cache_dir
        )


def pack_extractor(source_kind: str, entry_point: str) -> bool:
    """Whether the active pack extracts ``source_kind`` with ``entry_point``."""
    return current_pack().extractors.get(source_kind) == entry_point


@dataclass(frozen=True)
class DomainPack(_EngineDomainPack):
    """A named set of domain decisions: classification, naming, rendering, context,
    references and analysis helpers.

    Unless given, a pack uses today's code-documentation parts: stem page
    names, the built-in pages, code context, the built-in reference providers
    and the bundled analysis helpers.
    """

    page_namer: PageNamer = field(default_factory=lambda: StemPageNamer())
    page_renderer: PageRenderer = field(default_factory=lambda: BuiltInPageRenderer())
    context_source: ContextSource = field(default_factory=lambda: CodeContextSource())
    reference_providers: tuple[ReferenceProvider, ...] = BUILTIN_REFERENCE_PROVIDERS
    helper_toolchain: HelperToolchain = field(default_factory=lambda: BundledHelperToolchain())

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(
            self, "reference_providers", check_reference_providers(self.reference_providers)
        )


#: Today's code-documentation behavior: built-in languages, stem page names,
#: built-in page Markdown, code context, the built-in reference providers and
#: the bundled analysis helpers.
CODE_DOCS_PACK = DomainPack(
    "agent-wiki-cli/code-docs",
    CodeSourceClassifier(),
    StemPageNamer(),
    BuiltInPageRenderer(),
    CodeContextSource(),
    helper_toolchain=BundledHelperToolchain(),
)

def current_pack() -> _EngineDomainPack:
    """The pack chosen for this context, or :data:`CODE_DOCS_PACK`."""
    return active_pack() or CODE_DOCS_PACK


def uses_default_pack() -> bool:
    """Whether this context uses :data:`CODE_DOCS_PACK`.

    Caches keyed by the package implementation are only valid for it.
    """
    return current_pack() is CODE_DOCS_PACK


__all__ = [
    "CODE_DOCS_PACK",
    "BuiltInPageRenderer",
    "CodeContextSource",
    "BundledHelperToolchain",
    "CodeSourceClassifier",
    "ContextDetail",
    "ContextSource",
    "DomainPack",
    "EntityOccurrenceKey",
    "EntityPageRequest",
    "ExtensionSourceClassifier",
    "HelperToolchain",
    "ModulePageRequest",
    "NoHelperToolchain",
    "PageNamer",
    "PAGE_REQUEST_KINDS",
    "PageRenderer",
    "PageRequest",
    "SourceClassifier",
    "StemPageNamer",
    "context_entry",
    "context_related_sources",
    "current_pack",
    "pack_extractor",
    "render_with_pack",
    "uses_builtin_context_source",
    "uses_default_pack",
    "using_pack",
]
