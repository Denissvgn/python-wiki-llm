"""Typed request/result contract for deterministic wiki bootstrap."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


class BootstrapServiceError(RuntimeError):
    """Base error raised by the library bootstrap boundary."""


class BootstrapExtractionError(BootstrapServiceError):
    """Raised when one or more required extractors fail."""


class BootstrapContractError(BootstrapServiceError):
    """Raised when bootstrap input or generated contracts are invalid."""


class BootstrapRequestError(BootstrapContractError):
    """Raised when caller-supplied bootstrap options violate the contract."""


@dataclass(frozen=True)
class BootstrapRequest:
    """Runner-neutral deterministic bootstrap inputs.

    ``source_adapter`` defaults to true because library callers should not
    mutate agent integration files.  The existing CLI explicitly supplies its
    historical value when translating argparse options.

    ``overwrite`` is retained only as a compatibility tombstone.  Public
    bootstrap is first-use only and rejects ``overwrite=True`` before source
    extraction or target writes.
    """

    source_root: str | Path
    wiki_root: str | Path
    depth: str = "full"
    skip_workflows: bool = False
    skip_flows: bool = False
    skip_data_flow: bool = False
    skip_dependencies: bool = False
    api_contracts: bool = False
    openapi_file: str | None = None
    dependency_graph_detail: str = "auto"
    overwrite: bool = False
    source_adapter: bool = True
    helper_cache_dir: str | None = None
    include_tests: Iterable[str] | None = None
    trust_source_plugins: bool = False
    source_selection: str | Path | None = None


@dataclass(frozen=True)
class BootstrapResult:
    """Typed bootstrap result shared by the CLI and Python API."""

    summary: dict[str, Any]
    created_files: tuple[str, ...] = field(default_factory=tuple)
    updated_files: tuple[str, ...] = field(default_factory=tuple)
    skipped_files: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def schema_version(self) -> str:
        return str(self.summary.get("schema_version", ""))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.summary)


__all__ = [
    "BootstrapContractError",
    "BootstrapExtractionError",
    "BootstrapRequestError",
    "BootstrapRequest",
    "BootstrapResult",
    "BootstrapServiceError",
]
