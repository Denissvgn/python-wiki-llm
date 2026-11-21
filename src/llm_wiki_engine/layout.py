"""The names a wiki and its machine state use on disk.

Every file and directory name the knowledge core reads or writes is defined
once, here, as a field of :class:`Layout`. Modules use :data:`DEFAULT_LAYOUT`
instead of repeating the names. The default layout is the only supported one;
changing a name changes the on-disk format.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Layout:
    """Where a wiki keeps its pages and machine state."""

    #: The wiki directory, relative to the repository root, unless a caller names another.
    wiki_dir: str = "docs/llm_wiki"
    #: The sync manifest and its content-addressed object directory.
    manifest: str = ".llm-wiki-manifest.json"
    manifest_objects: str = ".llm-wiki-manifest"
    #: The knowledge index and its packed store directory.
    knowledge_index: str = ".llm-wiki-knowledge.json"
    knowledge_store: str = ".llm-wiki-knowledge"
    #: The published surface index.
    surface_index: str = ".llm-wiki-surface.json"
    #: The governance record and the locks that serialize writers.
    governance: str = ".llm-wiki-governance.json"
    governance_lock: str = "llm-wiki-governance.lock"
    storage_lock: str = "llm-wiki-storage.lock"
    #: The maintenance adoption record.
    maintenance_adoption: str = ".llm-wiki-maintenance-adoption.json"
    #: The machine verification receipt.
    verification_receipt: str = ".llm-wiki-verification.json"
    #: The prefix of retained page-move recovery directories.
    page_move_recovery_prefix: str = ".llm-wiki-page-moves-"
    #: The circuit breaker state file.
    breaker_state: str = "llm-wiki-breaker.json"


#: The one supported layout.
DEFAULT_LAYOUT = Layout()


__all__ = ["DEFAULT_LAYOUT", "Layout"]
