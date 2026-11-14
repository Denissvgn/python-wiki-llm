"""Embeddable engine: run wiki operations on behalf of a host application.

An :class:`Engine` holds what the caller grants: a :class:`Host` (processes,
environment, working directory, clock), whether bundled analysis helpers may
be prepared automatically, and the analysis comparison policy. Every call runs
inside one :class:`Operation` that applies those choices to all work beneath
it, including calls into :mod:`llm_wiki_cli.api`.

Unlike the CLI and the public API, an engine never prepares helpers unless the
caller grants ``helper_preparation="auto"``. Importing this module loads
neither the CLI, command modules nor the public API.

    from llm_wiki_cli import api
    from llm_wiki_cli.engine import Engine, NoProcessHost

    engine = Engine(host=NoProcessHost())
    result = engine.call(api.search_wiki, "billing", wiki_dir="docs/llm_wiki")
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, ParamSpec, TypeVar

from ..services.host import (
    ALL_CAPABILITIES,
    Host,
    HostCapabilityError,
    NoProcessHost,
    current_host,
    using_host,
)

__all__ = [
    "ALL_CAPABILITIES",
    "Engine",
    "Host",
    "HostCapabilityError",
    "NoProcessHost",
    "Operation",
    "current_host",
]

HelperPreparation = Literal["auto", "never"]
_P = ParamSpec("_P")
_R = TypeVar("_R")


@dataclass(frozen=True)
class Operation:
    """The settings in force for one engine call and everything beneath it."""

    host: Host
    helper_preparation: HelperPreparation
    helper_cache_dir: str | None
    comparison_policy: str


class Engine:
    """One configured engine; independent engines may run side by side."""

    def __init__(
        self,
        *,
        host: Host | None = None,
        helper_preparation: HelperPreparation = "never",
        helper_cache_dir: str | Path | None = None,
        comparison_policy: str = "auto",
    ) -> None:
        from ..services.analysis_compatibility import selected_policy

        host = Host() if host is None else host
        if not isinstance(host, Host):
            raise TypeError("host must be a Host instance")
        if helper_preparation not in ("auto", "never"):
            raise ValueError("helper_preparation must be 'auto' or 'never'")
        if helper_preparation == "auto" and "subprocess" not in host.capabilities:
            raise ValueError("automatic helper preparation requires a host that grants subprocess")
        if helper_cache_dir is not None and not isinstance(helper_cache_dir, (str, Path)):
            raise TypeError("helper_cache_dir must be a path")
        self._host = host
        self._helper_preparation: HelperPreparation = helper_preparation
        self._helper_cache_dir = None if helper_cache_dir is None else str(helper_cache_dir)
        self._comparison_policy = selected_policy(comparison_policy)

    @property
    def host(self) -> Host:
        return self._host

    def capabilities(self) -> dict[str, object]:
        """What this engine may do, so a caller can explain a refused operation."""
        return {
            "granted": sorted(self._host.capabilities),
            "missing": sorted(ALL_CAPABILITIES - self._host.capabilities),
            "helper_preparation": self._helper_preparation,
            "comparison_policy": self._comparison_policy,
        }

    @contextmanager
    def operation(self) -> Iterator[Operation]:
        """Apply this engine's grants to all work inside the block."""
        from ..services.analysis_compatibility import comparison_scope
        from ..services.helper_runtime import helper_operation, helper_policy

        with ExitStack() as stack:
            stack.enter_context(using_host(self._host))
            stack.enter_context(comparison_scope(self._comparison_policy))
            stack.enter_context(helper_policy(self._helper_preparation, cache_dir=self._helper_cache_dir))
            stack.enter_context(helper_operation(fresh=True))
            yield Operation(
                self._host, self._helper_preparation, self._helper_cache_dir, self._comparison_policy,
            )

    def call(self, function: Callable[_P, _R], /, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        """Run ``function`` (typically from :mod:`llm_wiki_cli.api`) in one operation."""
        with self.operation():
            return function(*args, **kwargs)
