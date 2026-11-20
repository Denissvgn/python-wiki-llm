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

import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from pathlib import PurePath
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from .reference_providers import (
    BUILTIN_REFERENCE_PROVIDERS,
    ReferenceProvider,
    check_reference_providers,
)
from llm_wiki_engine.integrations import DEFAULT_INTEGRATIONS, IntegrationSet
from llm_wiki_engine.pack_interfaces import (
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
from llm_wiki_engine.validation import portable_page_component, portable_path_key

if TYPE_CHECKING:
    from .helper_runtime import PreparedHelperHandle
    from .source_snapshot import SourceSnapshot


class BuiltInPageRenderer:
    """Today's code-documentation pages; subclass it to adjust them."""

    def render_module(self, request: ModulePageRequest) -> str:
        return request.builtin_markdown()

    def render_entity(self, request: EntityPageRequest) -> str:
        return request.builtin_markdown()

    def render_page(self, request: PageRequest) -> str:
        return request.builtin_markdown()


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


# ── Stem page names ────────────────────────────────────────────────────


def _safe_page_component(value: object, *, fallback: str = "page") -> str:
    return portable_page_component(value, fallback=fallback)


def _path_parts(path: str) -> tuple[str, ...]:
    return PurePath(path).parts


def _page_name_with_extension(filepath: str) -> str:
    """A page-safe path stem that includes the source extension."""
    path = PurePath(filepath)
    base = path.with_suffix("").as_posix()
    base = base.replace("/", "_").replace("\\", "_").replace(".", "_")
    extension = path.suffix.lower().lstrip(".") or "file"
    return f"{base}_{extension.replace('.', '_')}"


def _page_name_from_source_path(filepath: str) -> str:
    """A page-safe stem from the full source path without extension."""
    path = PurePath(filepath)
    base = path.with_suffix("").as_posix()
    base = base.replace("/", "_").replace("\\", "_").replace(".", "_")
    return _safe_page_component(base, fallback=path.stem)


def _disambiguate_paths(filepaths: list[str], stem: str) -> dict[str, str]:
    """Add parent directories until every path sharing ``stem`` is unique."""
    max_depth = max(len(_path_parts(filepath)) for filepath in filepaths)
    for depth in range(1, max_depth):
        candidates: dict[str, str] = {}
        for filepath in filepaths:
            directory_parts = _path_parts(filepath)[:-1]
            prefix_parts = (
                directory_parts[-depth:]
                if len(directory_parts) >= depth
                else directory_parts
            )
            candidates[filepath] = "_".join(prefix_parts) + "_" + stem
        if len(set(candidates.values())) == len(filepaths):
            return candidates

    candidates = {filepath: _page_name_with_extension(filepath) for filepath in filepaths}
    if len(set(candidates.values())) == len(filepaths):
        return candidates

    seen: defaultdict[str, int] = defaultdict(int)
    unique: dict[str, str] = {}
    for filepath in sorted(filepaths):
        name = candidates[filepath]
        seen[name] += 1
        unique[filepath] = name if seen[name] == 1 else f"{name}_{seen[name]}"
    return unique


def _globally_disambiguate_module_pages(page_map: dict[str, str]) -> dict[str, str]:
    """Resolve portable filesystem collisions after stem-group disambiguation."""
    page_counts = Counter(portable_path_key(page) for page in page_map.values())
    colliding_pages = {page for page, count in page_counts.items() if count > 1}
    if not colliding_pages:
        return page_map

    resolved = dict(page_map)
    used = {
        portable_path_key(page) for page in page_map.values()
        if portable_path_key(page) not in colliding_pages
    }
    for filepath in sorted(page_map):
        if portable_path_key(page_map[filepath]) not in colliding_pages:
            continue
        base = _page_name_from_source_path(filepath)
        candidates = [base, _page_name_with_extension(filepath)]
        candidate = next(
            (item for item in candidates if portable_path_key(item) not in used), base
        )
        suffix = 2
        while portable_path_key(candidate) in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        resolved[filepath] = candidate
        used.add(portable_path_key(candidate))
    return resolved


def _entity_occurrences(
    inventory: Mapping[str, Mapping[str, Any]],
) -> list[tuple[EntityOccurrenceKey, Mapping[str, Any]]]:
    occurrences: list[tuple[EntityOccurrenceKey, Mapping[str, Any]]] = []
    for filepath, file_data in inventory.items():
        seen_names: defaultdict[str, int] = defaultdict(int)
        for entity in file_data.get("classes", []):
            name = entity.get("name")
            if not name:
                continue
            name_text = str(name)
            seen_names[name_text] += 1
            occurrences.append(((name_text, filepath, seen_names[name_text]), entity))
    return occurrences


class StemPageNamer:
    """Module pages take the source file stem, entity pages the entity name.

    Colliding names are qualified with parent directories (modules) or the
    module page (entities), and names that collide on a case-insensitive or
    Windows filesystem are made distinct.
    """

    def module_pages(self, inventory: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
        stem_groups: defaultdict[str, list[str]] = defaultdict(list)
        for filepath in inventory:
            stem_groups[PurePath(filepath).stem].append(filepath)

        page_map: dict[str, str] = {}
        for stem, filepaths in stem_groups.items():
            if len(filepaths) == 1:
                page_map[filepaths[0]] = stem
            else:
                page_map.update(_disambiguate_paths(filepaths, stem))
        return _globally_disambiguate_module_pages(page_map)

    def entity_pages(
        self,
        inventory: Mapping[str, Mapping[str, Any]],
        module_pages: Mapping[str, str],
    ) -> dict[EntityOccurrenceKey, str]:
        occurrences = _entity_occurrences(inventory)
        name_counts = Counter(key[0] for key, _entity in occurrences)
        files_by_name: defaultdict[str, set[str]] = defaultdict(set)
        for (name, filepath, _occurrence), _entity in occurrences:
            files_by_name[name].add(filepath)

        proposed_pages: list[tuple[EntityOccurrenceKey, str, str]] = []
        for key, _entity in occurrences:
            name, filepath, occurrence = key
            safe_name = _safe_page_component(name, fallback="entity")
            if name_counts[name] > 1 and len(files_by_name[name]) > 1:
                page_name = _safe_page_component(f"{module_pages[filepath]}_{safe_name}")
            else:
                page_name = safe_name
            if occurrence > 1:
                page_name = _safe_page_component(f"{page_name}_{occurrence}")
            proposed_pages.append((key, page_name, module_pages[filepath]))

        page_counts = Counter(portable_path_key(page) for _, page, _ in proposed_pages)
        used: set[str] = set()
        page_map: dict[EntityOccurrenceKey, str] = {}
        for key, page_name, module_page in proposed_pages:
            candidate = page_name
            if page_counts[portable_path_key(page_name)] > 1:
                candidate = _safe_page_component(f"{module_page}_{page_name}")
            suffix = 2
            while portable_path_key(candidate) in used:
                candidate = f"{page_name}_{suffix}"
                suffix += 1
            page_map[key] = candidate
            used.add(portable_path_key(candidate))
        return page_map

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


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


_ENTRY_POINT = re.compile(r"[A-Za-z_][\w.]*:[A-Za-z_][\w.]*")


def _check_extractors(extractors: object, classifier: SourceClassifier) -> Mapping[str, str]:
    if not isinstance(extractors, Mapping):
        raise TypeError("extractors must map source kinds to entry points")
    checked: dict[str, str] = {}
    if not extractors:
        # Declared kinds are only needed to check entries; asking a code
        # classifier for them would load the extractors.
        return MappingProxyType(checked)
    declared = classifier.source_kinds()
    for kind, entry_point in sorted(extractors.items()):
        if kind not in declared:
            raise ValueError(f"extractor source kind {kind!r} is not declared by the classifier")
        if not isinstance(entry_point, str) or not _ENTRY_POINT.fullmatch(entry_point):
            raise ValueError(f"extractor for {kind!r} must be a 'module:attribute' entry point")
        checked[kind] = entry_point
    return MappingProxyType(checked)


def pack_extractor(source_kind: str, entry_point: str) -> bool:
    """Whether the active pack extracts ``source_kind`` with ``entry_point``."""
    return current_pack().extractors.get(source_kind) == entry_point


def _qualified_type_name(value: object) -> str:
    kind = type(value)
    return f"{kind.__module__}.{kind.__qualname__}"


@dataclass(frozen=True)
class DomainPack:
    """A named set of domain decisions: classification, naming, rendering, context,
    references and analysis helpers."""

    name: str
    classifier: SourceClassifier
    page_namer: PageNamer = field(default_factory=StemPageNamer)
    page_renderer: PageRenderer = field(default_factory=BuiltInPageRenderer)
    context_source: ContextSource = field(default_factory=CodeContextSource)
    reference_providers: tuple[ReferenceProvider, ...] = BUILTIN_REFERENCE_PROVIDERS
    helper_toolchain: HelperToolchain = field(default_factory=BundledHelperToolchain)
    extractors: Mapping[str, str] = field(default_factory=dict, hash=False)
    #: Knowledge-core providers this pack's domain needs; see
    #: :mod:`llm_wiki_engine.integrations`. The default names none and keeps
    #: the process-wide providers.
    integrations: IntegrationSet = DEFAULT_INTEGRATIONS

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("pack name must be a non-empty string")
        if not isinstance(self.classifier, SourceClassifier):
            raise TypeError("classifier must implement SourceClassifier")
        if not isinstance(self.page_namer, PageNamer):
            raise TypeError("page_namer must implement PageNamer")
        if not isinstance(self.page_renderer, PageRenderer):
            raise TypeError("page_renderer must implement PageRenderer")
        if not isinstance(self.context_source, ContextSource):
            raise TypeError("context_source must implement ContextSource")
        if not isinstance(self.helper_toolchain, HelperToolchain):
            raise TypeError("helper_toolchain must be a HelperToolchain")
        if not isinstance(self.integrations, IntegrationSet):
            raise TypeError("integrations must be an IntegrationSet")
        object.__setattr__(self, "extractors", _check_extractors(self.extractors, self.classifier))
        object.__setattr__(
            self, "reference_providers", check_reference_providers(self.reference_providers)
        )

    def with_classifier(self, classifier: SourceClassifier) -> DomainPack:
        """A copy of this pack that classifies sources with ``classifier``."""
        return replace(self, classifier=classifier)

    def with_page_namer(self, page_namer: PageNamer) -> DomainPack:
        """A copy of this pack that names pages with ``page_namer``."""
        return replace(self, page_namer=page_namer)

    def with_page_renderer(self, page_renderer: PageRenderer) -> DomainPack:
        """A copy of this pack that writes pages with ``page_renderer``."""
        return replace(self, page_renderer=page_renderer)

    def with_context_source(self, context_source: ContextSource) -> DomainPack:
        """A copy of this pack that builds budgeted context with ``context_source``."""
        return replace(self, context_source=context_source)

    def with_reference_provider(self, provider: ReferenceProvider) -> DomainPack:
        """A copy of this pack that also serves ``provider``, replacing one of the same kind."""
        kept = tuple(item for item in self.reference_providers if item.kind != provider.kind)
        return replace(self, reference_providers=(*kept, provider))

    def with_extractor(self, source_kind: str, entry_point: str) -> DomainPack:
        """A copy of this pack that extracts ``source_kind`` with ``entry_point``."""
        return replace(self, extractors={**self.extractors, source_kind: entry_point})

    def with_helper_toolchain(self, helper_toolchain: HelperToolchain) -> DomainPack:
        """A copy of this pack that prepares analysis helpers with ``helper_toolchain``."""
        return replace(self, helper_toolchain=helper_toolchain)

    def with_integrations(self, integrations: IntegrationSet) -> DomainPack:
        """A copy of this pack whose knowledge core uses ``integrations``."""
        return replace(self, integrations=integrations)

    def describe(self) -> dict[str, Any]:
        """A JSON-ready summary of the pack."""
        return {
            "name": self.name,
            "source_kinds": {
                kind: list(extensions)
                for kind, extensions in self.classifier.source_kinds().items()
            },
            "classifier": _qualified_type_name(self.classifier),
            "page_namer": _qualified_type_name(self.page_namer),
            "page_renderer": _qualified_type_name(self.page_renderer),
            "context_source": _qualified_type_name(self.context_source),
            "reference_providers": [provider.kind for provider in self.reference_providers],
            "helper_toolchain": _qualified_type_name(self.helper_toolchain),
            "extractors": dict(self.extractors),
        }


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

_ACTIVE_PACK: ContextVar[DomainPack | None] = ContextVar("llm_wiki_domain_pack", default=None)


def current_pack() -> DomainPack:
    """The pack chosen for this context, or :data:`CODE_DOCS_PACK`."""
    return _ACTIVE_PACK.get() or CODE_DOCS_PACK


def uses_default_pack() -> bool:
    """Whether this context uses :data:`CODE_DOCS_PACK`.

    Caches keyed by the package implementation are only valid for it.
    """
    return current_pack() is CODE_DOCS_PACK


@contextmanager
def using_pack(pack: DomainPack) -> Iterator[DomainPack]:
    """Classify, name, render and build context inside the block with ``pack``."""
    if not isinstance(pack, DomainPack):
        raise TypeError("pack must be a DomainPack")
    token = _ACTIVE_PACK.set(pack)
    try:
        yield pack
    finally:
        _ACTIVE_PACK.reset(token)


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
