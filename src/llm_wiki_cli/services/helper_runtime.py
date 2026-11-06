"""Operation-owned helper policy and immutable prepared-artifact bindings.

Configuration scopes carry defaults only. Each top-level analysis opens an
operation; nested implementation calls may share it, but a later top-level
call gets fresh bindings. These primitives never inspect or prepare a helper.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
import os
from pathlib import Path
from types import MappingProxyType
from typing import Literal, TYPE_CHECKING, cast

from ..config import EXTRACTOR_REGISTRY
from .immutable import freeze

if TYPE_CHECKING:
    from .source_snapshot import SourceSnapshot


HelperPolicy = Literal["auto", "never"]
HelperProgress = Callable[[str], None]


def resolve_helper_policy(
    requested: str | None = None,
    *,
    strict_read_only: bool = False,
    preview: bool = False,
    offline: bool = False,
) -> HelperPolicy:
    """Resolve preparation authority without changing workspace mutability."""
    for name, value in (("strict_read_only", strict_read_only),
                        ("preview", preview), ("offline", offline)):
        if type(value) is not bool:
            raise ValueError(f"{name} must be a boolean")
    if requested is not None and (not isinstance(requested, str) or requested not in {"auto", "never"}):
        raise ValueError("helper preparation must be 'auto' or 'never'")
    strict = strict_read_only or preview or offline
    if strict and requested == "auto":
        raise ValueError("automatic helper preparation conflicts with strict read-only, preview or offline mode")
    return "never" if strict else cast(HelperPolicy, requested or "auto")


def _absolute(path: str | Path) -> Path:
    # No resolve()/stat(): scope construction and pinned lookup must remain I/O
    # free. The cache owner checks path safety before issuing a handle.
    return Path(os.path.abspath(path))


@dataclass(frozen=True)
class PreparedHelperHandle:
    """Detached artifact and receipt selected once by the preparation owner."""

    language: str
    cache_root: Path
    key: str
    root: Path
    path: Path
    receipt: Mapping[str, object]
    runtime_executables: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.language not in EXTRACTOR_REGISTRY or self.language == "python":
            raise ValueError("unsupported bundled helper language")
        if not isinstance(self.key, str) or not self.key:
            raise ValueError("prepared helper key must be nonempty")
        for name in ("cache_root", "root", "path"):
            object.__setattr__(self, name, _absolute(getattr(self, name)))
        if not self.root.is_relative_to(self.cache_root) or not self.path.is_relative_to(self.root):
            raise ValueError("prepared helper paths must remain inside its cache root")
        if not isinstance(self.receipt, Mapping):
            raise ValueError("prepared helper receipt must be a mapping")
        if not isinstance(self.runtime_executables, Mapping) or not all(
            isinstance(name, str) and isinstance(path, str) and bool(path)
            for name, path in self.runtime_executables.items()
        ):
            raise ValueError("helper runtime executables must be named nonempty paths")
        object.__setattr__(self, "receipt", freeze(dict(self.receipt)))
        object.__setattr__(self, "runtime_executables", freeze(dict(self.runtime_executables)))


@dataclass(frozen=True)
class HelperConfiguration:
    policy: HelperPolicy
    cache_dir: str | None = None
    progress: HelperProgress | None = field(default=None, repr=False, compare=False)


@dataclass(frozen=True)
class HelperOperation:
    policy: HelperPolicy
    cache_dir: str | None = None
    progress: HelperProgress | None = field(default=None, repr=False, compare=False)
    _configuration: HelperConfiguration | None = field(default=None, repr=False, compare=False)
    _handles: dict[str, PreparedHelperHandle] = field(default_factory=dict, repr=False, compare=False)
    _source_roots: dict[tuple[Path, str], Path] = field(default_factory=dict, repr=False, compare=False)

    @property
    def handles(self) -> Mapping[str, PreparedHelperHandle]:
        return MappingProxyType(self._handles)

    def bind(self, handle: PreparedHelperHandle, *, source_root: str | Path | None = None) -> None:
        previous = self._handles.get(handle.language)
        if previous is not None and previous != handle:
            raise ValueError("a helper cannot be rebound during one analysis operation")
        if source_root is not None:
            source = (_absolute(source_root), handle.language)
            bound_root = self._source_roots.get(source)
            if bound_root is not None and bound_root != handle.cache_root:
                raise ValueError("helper cache scope changed during analysis")
            self._source_roots[source] = handle.cache_root
        self._handles[handle.language] = handle


_CONFIGURATION: ContextVar[HelperConfiguration | None] = ContextVar("helper_configuration", default=None)
_OPERATION: ContextVar[HelperOperation | None] = ContextVar("helper_operation", default=None)


def current_helper_configuration() -> HelperConfiguration | None:
    return _CONFIGURATION.get()


def current_helper_policy() -> HelperConfiguration | None:
    """Return configured defaults, never an artifact/operation binding."""
    return current_helper_configuration()


def current_helper_operation() -> HelperOperation | None:
    return _OPERATION.get()


current_operation = current_helper_operation


def _cache_value(cache_dir: str | Path | None) -> str | None:
    if cache_dir is None:
        return None
    value = os.fspath(cache_dir)
    if not isinstance(value, str) or not value or "\0" in value:
        raise ValueError("helper cache directory must be a nonempty path")
    return value


def _check_progress(progress: HelperProgress | None) -> None:
    if progress is not None and not callable(progress):
        raise ValueError("helper progress must be callable")


@contextmanager
def helper_policy(
    policy: str,
    *,
    cache_dir: str | Path | None = None,
    progress: HelperProgress | None = None,
) -> Iterator[HelperConfiguration]:
    """Configure independent calls without retaining their prepared handles."""
    _check_progress(progress)
    selected = resolve_helper_policy(policy)
    parent, active = _CONFIGURATION.get(), _OPERATION.get()
    if selected == "auto" and (
        parent is not None and parent.policy == "never"
        or active is not None and active.policy == "never"
    ):
        raise ValueError("a strict helper scope cannot enable automatic preparation")
    inherited_cache = active.cache_dir if active is not None else parent.cache_dir if parent is not None else None
    inherited_progress = active.progress if active is not None else parent.progress if parent is not None else None
    configured = HelperConfiguration(
        selected, _cache_value(cache_dir) if cache_dir is not None else inherited_cache,
        progress if progress is not None else inherited_progress,
    )
    token = _CONFIGURATION.set(configured)
    try:
        yield configured
    finally:
        _CONFIGURATION.reset(token)


@contextmanager
def helper_operation(
    policy: str | None = None,
    *,
    fresh: bool = False,
    cache_dir: str | Path | None = None,
    progress: HelperProgress | None = None,
) -> Iterator[HelperOperation]:
    """Own one capture/extraction binding; nested calls inherit compatible state."""
    _check_progress(progress)
    if type(fresh) is not bool:
        raise ValueError("fresh must be a boolean")
    parent, configured = _OPERATION.get(), _CONFIGURATION.get()
    same_configuration = parent is not None and configured is parent._configuration
    defaults = parent if same_configuration else configured if configured is not None else parent
    selected = resolve_helper_policy(policy if policy is not None else defaults.policy if defaults is not None else None)
    if selected == "auto" and (
        parent is not None and parent.policy == "never"
        or configured is not None and configured.policy == "never"
    ):
        raise ValueError("a strict helper scope cannot enable automatic preparation")
    inherited_cache = defaults.cache_dir if defaults is not None else None
    inherited_progress = defaults.progress if defaults is not None else None
    cache = _cache_value(cache_dir) if cache_dir is not None else inherited_cache
    reporter = progress if progress is not None else inherited_progress
    if (not fresh and parent is not None and parent.policy == selected
            and parent.cache_dir == cache and parent.progress is reporter):
        yield parent
        return
    operation = HelperOperation(selected, cache, reporter, configured)
    if not fresh and parent is not None and parent.cache_dir == cache:
        operation._handles.update(parent._handles)
        operation._source_roots.update(parent._source_roots)
    token = _OPERATION.set(operation)
    try:
        yield operation
    finally:
        _OPERATION.reset(token)


def bind_helper(handle: PreparedHelperHandle, *, source_root: str | Path | None = None) -> None:
    operation = _OPERATION.get()
    if operation is None:
        raise ValueError("prepared helpers must be bound inside an analysis operation")
    operation.bind(handle, source_root=source_root)


def pinned_helper(
    language: str, cache_root: str | Path | None = None,
    *, source_root: str | Path | None = None,
) -> PreparedHelperHandle | None:
    operation = _OPERATION.get()
    if operation is None:
        return None
    handle = operation.handles.get(language)
    if handle is None or cache_root is not None and handle.cache_root != _absolute(cache_root):
        return None
    if source_root is not None and operation._source_roots.get((_absolute(source_root), language)) != handle.cache_root:
        return None
    return handle


def operation_cache_root(source_root: str | Path, language: str | None = None) -> Path | None:
    operation = _OPERATION.get()
    if operation is None:
        return None
    source = _absolute(source_root)
    if language is not None:
        return operation._source_roots.get((source, language))
    roots = {root for (bound_source, _), root in operation._source_roots.items() if bound_source == source}
    return next(iter(roots)) if len(roots) == 1 else None


def required_helper_languages(
    snapshot: SourceSnapshot,
    registry: Mapping[str, str],
    *, only_files: Iterable[str] | None = None,
) -> tuple[str, ...]:
    """Plan only bundled extraction within the already validated source boundary."""
    from .extractor_helpers import SUPPORTED_HELPERS

    selected = None if only_files is None else set(only_files)
    return tuple(
        language for language in SUPPORTED_HELPERS
        if registry.get(language) == EXTRACTOR_REGISTRY.get(language)
        and any(selected is None or path in selected for path in snapshot.language_paths(language))
    )
