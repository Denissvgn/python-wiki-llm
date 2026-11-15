"""Domain packs: the replaceable parts of turning sources into wiki pages.

A :class:`DomainPack` bundles the domain decisions the engine asks about:

* a :class:`SourceClassifier` decides which repository files are sources and
  which source kind (for code: language) each one is;
* a :class:`PageNamer` names the module and entity pages generated from an
  inventory. Page kinds themselves are fixed by the knowledge format;
* a :class:`PageRenderer` writes the Markdown of those module and entity
  pages. Each request carries the built-in Markdown, so a renderer can adjust
  it instead of starting over.

:data:`CODE_DOCS_PACK` is today's code-documentation behavior and the default.
A host chooses another pack with :func:`using_pack` or ``Engine(pack=...)``;
every call that classifies sources or names pages inside that block uses it.
Pages named by one pack are not renamed by another, so a wiki should keep
using the pack that generated it.

When sync refreshes a module or entity page it keeps what people wrote in
its ``Description`` section and in the description cells of its
``Attributes``, ``Methods``, ``Classes`` and ``Functions`` tables, and takes
everything else from the renderer. A renderer that wants people to write
there keeps those headings; any section it adds stays current with sources.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from pathlib import PurePath
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

from .validation import portable_page_component, portable_path_key

#: ``(entity name, source path, one-based occurrence in that source)``.
EntityOccurrenceKey = tuple[str, str, int]


@runtime_checkable
class SourceClassifier(Protocol):
    """Decides which files are sources and of which kind."""

    def source_kinds(self) -> Mapping[str, tuple[str, ...]]:
        """Every source kind this classifier can return, with its suffixes."""
        ...

    def classify(
        self, path: PurePath, include_tests: frozenset[str]
    ) -> tuple[str | None, str | None]:
        """Return ``(kind, exclusion)`` for a repository-relative path.

        ``kind`` is ``None`` for a file that is not a source. ``exclusion``
        names why a recognized file is left out (for example a test file whose
        kind is not in ``include_tests``) and is ``None`` for included files.
        """
        ...

    def inventory_language(self, path: str) -> str | None:
        """The ``language`` label an inventory records for ``path``."""
        ...


@runtime_checkable
class PageNamer(Protocol):
    """Names the generated module and entity pages for an inventory."""

    def module_pages(self, inventory: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
        """Return ``{source path: module page name}`` for every inventory source."""
        ...

    def entity_pages(
        self,
        inventory: Mapping[str, Mapping[str, Any]],
        module_pages: Mapping[str, str],
    ) -> dict[EntityOccurrenceKey, str]:
        """Return ``{(name, source path, occurrence): entity page name}``."""
        ...


@dataclass(frozen=True)
class ModulePageRequest:
    """Everything a renderer gets for one module page."""

    source_path: str
    file_data: Mapping[str, Any]
    entity_pages: Mapping[str, str]
    module_pages: Mapping[str, str]
    entity_occurrence_pages: Mapping[EntityOccurrenceKey, str]
    module_dependencies: Mapping[str, Any] | None
    diagram_style: Mapping[str, Any] | None
    _builtin: Callable[[], str] = field(repr=False, compare=False)

    def builtin_markdown(self) -> str:
        """The Markdown the built-in renderer writes for this page."""
        return self._builtin()


@dataclass(frozen=True)
class EntityPageRequest:
    """Everything a renderer gets for one entity page."""

    entity: Mapping[str, Any]
    source_path: str
    module_page: str | None
    relationships: Mapping[str, Any]
    relationship_summary: Mapping[str, Any]
    module_pages: Mapping[str, str]
    diagram_style: Mapping[str, Any] | None
    _builtin: Callable[[], str] = field(repr=False, compare=False)

    def builtin_markdown(self) -> str:
        """The Markdown the built-in renderer writes for this page."""
        return self._builtin()


@runtime_checkable
class PageRenderer(Protocol):
    """Writes the Markdown of generated module and entity pages."""

    def render_module(self, request: ModulePageRequest) -> str:
        """Return the Markdown of one module page."""
        ...

    def render_entity(self, request: EntityPageRequest) -> str:
        """Return the Markdown of one entity page."""
        ...


class BuiltInPageRenderer:
    """Today's code-documentation pages; subclass it to adjust them."""

    def render_module(self, request: ModulePageRequest) -> str:
        return request.builtin_markdown()

    def render_entity(self, request: EntityPageRequest) -> str:
        return request.builtin_markdown()


def render_with_pack(request: ModulePageRequest | EntityPageRequest) -> str:
    """Render ``request`` with the current pack's page renderer."""
    renderer = current_pack().page_renderer
    if isinstance(request, ModulePageRequest):
        markdown = renderer.render_module(request)
    else:
        markdown = renderer.render_entity(request)
    if not isinstance(markdown, str):
        raise TypeError(
            f"page renderer {_qualified_type_name(renderer)} must return Markdown text"
        )
    return markdown


def _suffixes(value: object, field_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(f"{field_name} must be a sequence of strings")
    suffixes = tuple(value)
    if not all(isinstance(item, str) and item for item in suffixes):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return suffixes


class ExtensionSourceClassifier:
    """Classifies sources by file extension, first matching kind wins.

    ``test_suffixes`` lists, per kind, file-name endings that mark test files;
    those are excluded unless the kind is in ``include_tests``.
    """

    def __init__(
        self,
        kinds: Mapping[str, Iterable[str]],
        *,
        test_suffixes: Mapping[str, Iterable[str]] | None = None,
    ) -> None:
        if not isinstance(kinds, Mapping) or not kinds:
            raise ValueError("kinds must be a non-empty mapping of kind to extensions")
        resolved: dict[str, tuple[str, ...]] = {}
        for kind, extensions in kinds.items():
            if not isinstance(kind, str) or not kind:
                raise ValueError("source kind names must be non-empty strings")
            values = _suffixes(extensions, f"kinds[{kind!r}]")
            if not all(value.startswith(".") for value in values):
                raise ValueError(f"kinds[{kind!r}] extensions must start with '.'")
            resolved[kind] = values
        tests: dict[str, tuple[str, ...]] = {}
        for kind, suffixes in (test_suffixes or {}).items():
            if kind not in resolved:
                raise ValueError(f"test_suffixes names unknown source kind {kind!r}")
            tests[kind] = _suffixes(suffixes, f"test_suffixes[{kind!r}]")
        self._kinds: Mapping[str, tuple[str, ...]] = MappingProxyType(resolved)
        self._test_suffixes: Mapping[str, tuple[str, ...]] = MappingProxyType(tests)

    def _kind_table(self) -> Mapping[str, tuple[str, ...]]:
        return self._kinds

    def source_kinds(self) -> Mapping[str, tuple[str, ...]]:
        return self._kind_table()

    def classify(
        self, path: PurePath, include_tests: frozenset[str]
    ) -> tuple[str | None, str | None]:
        suffix = path.suffix
        for kind, extensions in self._kind_table().items():
            if suffix not in extensions:
                continue
            if kind not in include_tests and any(
                path.name.endswith(ending) for ending in self._test_suffixes.get(kind, ())
            ):
                return kind, f"{kind}-tests-excluded"
            return kind, None
        return None, None

    def inventory_language(self, path: str) -> str | None:
        suffix = PurePath(path).suffix
        for kind, extensions in self._kind_table().items():
            if suffix in extensions:
                return kind
        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({dict(self._kind_table())!r})"


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


def _qualified_type_name(value: object) -> str:
    kind = type(value)
    return f"{kind.__module__}.{kind.__qualname__}"


@dataclass(frozen=True)
class DomainPack:
    """A named set of domain decisions: classification, page naming and rendering."""

    name: str
    classifier: SourceClassifier
    page_namer: PageNamer = field(default_factory=StemPageNamer)
    page_renderer: PageRenderer = field(default_factory=BuiltInPageRenderer)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("pack name must be a non-empty string")
        if not isinstance(self.classifier, SourceClassifier):
            raise TypeError("classifier must implement SourceClassifier")
        if not isinstance(self.page_namer, PageNamer):
            raise TypeError("page_namer must implement PageNamer")
        if not isinstance(self.page_renderer, PageRenderer):
            raise TypeError("page_renderer must implement PageRenderer")

    def with_classifier(self, classifier: SourceClassifier) -> DomainPack:
        """A copy of this pack that classifies sources with ``classifier``."""
        return replace(self, classifier=classifier)

    def with_page_namer(self, page_namer: PageNamer) -> DomainPack:
        """A copy of this pack that names pages with ``page_namer``."""
        return replace(self, page_namer=page_namer)

    def with_page_renderer(self, page_renderer: PageRenderer) -> DomainPack:
        """A copy of this pack that writes pages with ``page_renderer``."""
        return replace(self, page_renderer=page_renderer)

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
        }


#: Today's code-documentation behavior: built-in languages, stem page names
#: and built-in page Markdown.
CODE_DOCS_PACK = DomainPack(
    "agent-wiki-cli/code-docs", CodeSourceClassifier(), StemPageNamer(), BuiltInPageRenderer()
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
    """Classify sources, name pages and render them inside the block with ``pack``."""
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
    "CodeSourceClassifier",
    "DomainPack",
    "EntityOccurrenceKey",
    "EntityPageRequest",
    "ExtensionSourceClassifier",
    "ModulePageRequest",
    "PageNamer",
    "PageRenderer",
    "SourceClassifier",
    "StemPageNamer",
    "current_pack",
    "render_with_pack",
    "uses_default_pack",
    "using_pack",
]
