"""Embeddable engine: run wiki operations on behalf of a host application.

An :class:`Engine` holds what the caller grants: a :class:`Host` (processes,
environment, working directory, clock), whether bundled analysis helpers may
be prepared automatically, and the analysis comparison policy. Every call runs
inside one :class:`Operation` that applies those choices to all work beneath
it, including calls into :mod:`llm_wiki_cli.api`.

Unlike the CLI and the public API, an engine never prepares helpers unless the
caller grants ``helper_preparation="auto"``. Importing this module loads
neither the CLI, command modules nor the public API.

Use cases run directly on the engine and write progress to the host's
streams: :meth:`Engine.bootstrap`, :meth:`Engine.sync`, :meth:`Engine.lint`,
:meth:`Engine.migrate` and :meth:`Engine.upgrade`.
They take a typed request, return a typed result and never exit the process.

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
from typing import TYPE_CHECKING, Literal, ParamSpec, TypeVar

from ..services.host import (
    ALL_CAPABILITIES,
    Host,
    HostCapabilityError,
    NoProcessHost,
    current_host,
    using_host,
)
from ..services.bootstrap_service import (
    BootstrapContractError,
    BootstrapRequest,
    BootstrapRequestError,
    BootstrapResult,
    BootstrapServiceError,
)
from ..services.lint_request import LintRequest, LintRequestError
from ..services.migrate_service import MigrateError, MigrateOutcome, MigrateRequest, MigrateRequestError
from ..services.sync_service import SyncError, SyncOutcome, SyncRequest, SyncRequestError
from ..services.upgrade_service import UpgradeError, UpgradeOutcome, UpgradeRequest, UpgradeRequestError

if TYPE_CHECKING:
    from ..services.lint_service import LintReport

__all__ = [
    "ALL_CAPABILITIES",
    "BootstrapContractError",
    "BootstrapRequest",
    "BootstrapRequestError",
    "BootstrapResult",
    "BootstrapServiceError",
    "Engine",
    "Host",
    "HostCapabilityError",
    "LintRequest",
    "LintRequestError",
    "MigrateError",
    "MigrateOutcome",
    "MigrateRequest",
    "MigrateRequestError",
    "NoProcessHost",
    "Operation",
    "SyncError",
    "SyncOutcome",
    "SyncRequest",
    "SyncRequestError",
    "UpgradeError",
    "UpgradeOutcome",
    "UpgradeRequest",
    "UpgradeRequestError",
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

    def sync(self, request: SyncRequest) -> SyncOutcome:
        """Incrementally update a managed wiki; progress goes to the host's streams.

        Raises :class:`SyncError` (or :class:`SyncRequestError`) when sync stops.
        """
        from ..services.sync_runtime import execute_sync

        with self.operation():
            return execute_sync(request)

    def bootstrap(self, request: BootstrapRequest) -> BootstrapResult:
        """Create a first-use wiki; progress goes to the host's streams.

        Raises :class:`BootstrapRequestError` for invalid options and
        :class:`BootstrapServiceError` when bootstrap cannot complete.
        """
        from ..services.bootstrap_runtime import execute_bootstrap

        with self.operation():
            return execute_bootstrap(request)

    def lint(self, request: LintRequest) -> LintReport:
        """Check a wiki against its source; ``report.passed`` is the verdict.

        Extractor failures are report issues. Raises :class:`LintRequestError`
        when a path breaks the workspace policy.
        """
        from ..services.lint_service import execute_lint

        with self.operation():
            return execute_lint(request)

    def migrate(self, request: MigrateRequest) -> MigrateOutcome:
        """Bring an older wiki to current page naming; progress goes to the host.

        Raises :class:`MigrateError` (or :class:`MigrateRequestError`) when the
        migration stops.
        """
        from ..services.migrate_runtime import execute_migrate

        with self.operation():
            return execute_migrate(request)

    def upgrade(self, request: UpgradeRequest) -> UpgradeOutcome:
        """Refresh the managed agent schema, skills and wiki layout in place.

        Unlike the other use cases this changes the repository's agent setup:
        it rewrites the agent instruction file, refreshes managed skills and
        removes retired git hooks. Raises :class:`UpgradeError` when the
        upgrade stops.
        """
        from ..services.upgrade_runtime import execute_upgrade

        with self.operation():
            return execute_upgrade(request)
