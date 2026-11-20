"""The replaceable parts of a domain pack, as the engine sees them.

A domain pack decides how sources become wiki pages: which files are sources
(:class:`SourceClassifier`), how generated pages are named
(:class:`PageNamer`) and written (:class:`PageRenderer`), how sources relate
in budgeted context (:class:`ContextSource`) and which analysis helpers a
source tree needs (:class:`HelperToolchain`). This module holds those
interfaces, the requests a renderer receives and the implementations that
need no source analysis. Applications assemble packs from them; the
code-documentation pack lives in the application that analyzes code.

``snapshot`` arguments are the application's source snapshot (see the
``source_snapshots`` integration), and prepared helpers are the application's
handles; the engine passes both through without inspecting them.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import PurePath
from types import MappingProxyType
from typing import Any, Literal, Protocol, runtime_checkable

from .wiki_surface import PageKind

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


#: The page kinds a :class:`PageRequest` describes.
PAGE_REQUEST_KINDS = frozenset(
    {
        PageKind.INDEX,
        PageKind.WORKFLOWS,
        PageKind.FLOWS,
        PageKind.INFRASTRUCTURE,
        PageKind.API_CONTRACTS,
        PageKind.DEPENDENCIES,
        PageKind.LOAD_ORDER,
    }
)


@dataclass(frozen=True)
class PageRequest:
    """Everything a renderer gets for one page that is not a module or entity.

    ``inputs`` holds what the built-in page is generated from, by name:

    * ``index``: ``entity_names``, ``module_entries``, ``workflow_entries``,
      ``guide_entries``, ``infra_entries``, ``flow_entries``,
      ``architecture_entries``, ``retired_entity_pages``,
      ``api_contracts_present``, ``log_present``;
    * ``workflows``: ``name``, ``workflow``, ``module_pages``;
    * ``flows``: ``flow``, ``module_pages``, ``data_flow``,
      ``diagram_style``, ``api_contract_operations``;
    * ``infrastructure``: ``source_path``, ``info``, ``module_links``,
      ``unsupported_sources``;
    * ``api-contracts``: ``contracts``, ``module_pages``, ``entity_pages``;
    * ``dependencies``: ``analysis``, ``module_pages``, ``detail``,
      ``diagram_style``;
    * ``load-order``: ``analysis``, ``module_pages``.

    Absent optional inputs are ``None``.
    """

    page_kind: PageKind
    inputs: Mapping[str, Any]
    _builtin: Callable[[], str] = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        page_kind = PageKind(self.page_kind)
        if page_kind not in PAGE_REQUEST_KINDS:
            raise ValueError(f"page kind {page_kind.value!r} has its own request type")
        object.__setattr__(self, "page_kind", page_kind)
        object.__setattr__(self, "inputs", MappingProxyType(dict(self.inputs)))

    def builtin_markdown(self) -> str:
        """The Markdown the built-in renderer writes for this page."""
        return self._builtin()


@runtime_checkable
class PageRenderer(Protocol):
    """Writes the Markdown of generated pages."""

    def render_module(self, request: ModulePageRequest) -> str:
        """Return the Markdown of one module page."""
        ...

    def render_entity(self, request: EntityPageRequest) -> str:
        """Return the Markdown of one entity page."""
        ...

    def render_page(self, request: PageRequest) -> str:
        """Return the Markdown of one other generated page."""
        ...


ContextDetail = Literal["deep", "slim", "summary"]


@runtime_checkable
class ContextSource(Protocol):
    """How sources relate and appear in budgeted context."""

    def related_sources(
        self, inventory: Mapping[str, Mapping[str, Any]]
    ) -> Mapping[str, Iterable[str]]:
        """Return ``{source path: related source paths}``.

        Sources related to a changed source get medium priority.
        """
        ...

    def entry(self, data: Mapping[str, Any], detail: ContextDetail) -> Mapping[str, Any]:
        """Return the context entry of one source at ``detail``.

        ``data`` is the source's inventory record, or an entry this method
        returned at a higher detail level when budgeting shrinks it.
        """
        ...


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


class HelperToolchain:
    """Which analysis helpers a source tree needs, and how they are prepared.

    :meth:`languages` lists the source kinds whose extraction needs a
    prepared helper. :meth:`prepare` runs before extraction inside a helper
    operation: it resolves each needed helper under the operation's policy
    (``"never"`` only reuses prepared artifacts, ``"auto"`` may build them),
    binds what it found to the operation and returns those handles.
    """

    def languages(
        self, snapshot: Any, registry: Mapping[str, str],
        *, only_files: Iterable[str] | None = None,
    ) -> tuple[str, ...]:
        raise NotImplementedError

    def prepare(
        self, snapshot: Any, registry: Mapping[str, str],
        *, only_files: Iterable[str] | None = None, cache_dir: str | None = None,
    ) -> tuple[Any, ...]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class NoHelperToolchain(HelperToolchain):
    """Needs and prepares no helpers.

    A pack using it should classify only sources that in-process extractors
    handle; a source kind whose extractor needs a helper still fails without one.
    """

    def languages(
        self, snapshot: Any, registry: Mapping[str, str],
        *, only_files: Iterable[str] | None = None,
    ) -> tuple[str, ...]:
        return ()

    def prepare(
        self, snapshot: Any, registry: Mapping[str, str],
        *, only_files: Iterable[str] | None = None, cache_dir: str | None = None,
    ) -> tuple[Any, ...]:
        return ()


__all__ = [
    "ContextDetail",
    "ContextSource",
    "EntityOccurrenceKey",
    "EntityPageRequest",
    "ExtensionSourceClassifier",
    "HelperToolchain",
    "ModulePageRequest",
    "NoHelperToolchain",
    "PAGE_REQUEST_KINDS",
    "PageNamer",
    "PageRenderer",
    "PageRequest",
    "SourceClassifier",
]
