"""A domain pack for a folder of Markdown notes: no code, helpers or processes.

Each note becomes a module page titled by its first heading, each ``##``
section an entity page, and links between notes relate them in budgeted
context. The parts live in :mod:`tests.notes_parts`; this module assembles
them into a ``llm_wiki_cli`` pack.
"""

from __future__ import annotations

from llm_wiki_cli.engine import (
    DomainPack,
    ExtensionSourceClassifier,
    NoHelperToolchain,
)
from tests.notes_parts import NotesContextSource, NotesExtractor, NotesRenderer

__all__ = ["NOTES_PACK", "NotesContextSource", "NotesExtractor", "NotesRenderer"]


NOTES_PACK = DomainPack(
    "example/notes",
    ExtensionSourceClassifier({"notes": (".md",)}),
    page_renderer=NotesRenderer(),
    context_source=NotesContextSource(),
    reference_providers=(),
    helper_toolchain=NoHelperToolchain(),
    extractors={"notes": "tests.notes_pack:NotesExtractor"},
)
