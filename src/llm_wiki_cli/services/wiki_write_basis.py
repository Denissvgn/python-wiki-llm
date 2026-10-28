"""Operation-local compare-and-swap hooks for adopted wiki writes."""

from __future__ import annotations

from contextvars import ContextVar
from pathlib import Path
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .source_snapshot import SourceSnapshot


class WriteBasis(Protocol):
    root: Path
    preimages: dict[str, bytes]
    expected: dict[str, bytes]
    source_snapshot: SourceSnapshot | None
    def assert_current(self) -> None: ...
    def before_write(self, path: Path, content: bytes | None) -> None: ...
    def after_write(self, path: Path, content: bytes | None) -> None: ...

class PageWriteObserver(Protocol):
    def before_write(self, path: Path, content: bytes | None) -> None: ...
    def after_write(self, path: Path, content: bytes | None) -> None: ...


ACTIVE_WRITE_BASIS: ContextVar[WriteBasis | None] = ContextVar("llm_wiki_write_basis", default=None)
ACTIVE_SYNC_JOURNAL: ContextVar[PageWriteObserver | None] = ContextVar("llm_wiki_sync_journal", default=None)
ACTIVE_BOOTSTRAP_JOURNAL: ContextVar[WriteBasis | None] = ContextVar("llm_wiki_bootstrap_journal", default=None)


def before_wiki_write(path: str | Path, content: bytes | None) -> None:
    basis = ACTIVE_WRITE_BASIS.get()
    if basis is not None:
        basis.before_write(Path(path), content)
    journal = ACTIVE_SYNC_JOURNAL.get()
    if journal is not None:
        journal.before_write(Path(path), content)
    bootstrap = ACTIVE_BOOTSTRAP_JOURNAL.get()
    if bootstrap is not None:
        bootstrap.before_write(Path(path), content)


def after_wiki_write(path: str | Path, content: bytes | None) -> None:
    basis = ACTIVE_WRITE_BASIS.get()
    if basis is not None:
        basis.after_write(Path(path), content)
    journal = ACTIVE_SYNC_JOURNAL.get()
    if journal is not None:
        journal.after_write(Path(path), content)
    bootstrap = ACTIVE_BOOTSTRAP_JOURNAL.get()
    if bootstrap is not None:
        bootstrap.after_write(Path(path), content)
