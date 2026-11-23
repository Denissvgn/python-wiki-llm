"""The parts of a Markdown notes pack, built from engine interfaces only.

Each note becomes a module page titled by its first heading, each ``##``
section an entity page, and links between notes relate them in budgeted
context. Nothing here imports ``llm_wiki_cli``.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from llm_wiki_engine.pack_interfaces import (
    BuiltInPageRenderer,
    DomainPack,
    ExtensionSourceClassifier,
    ModulePageRequest,
)

_TITLE = re.compile(r"^#\s+(.+?)\s*#*\s*$")
_SECTION = re.compile(r"^##\s+(.+?)\s*#*\s*$")
_LINK = re.compile(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)")


def _identifier(text: str) -> str:
    return re.sub(r"\W+", "_", text).strip("_") or "Section"


class NotesExtractor:
    """Reads the title, sections and note links of each classified note."""

    def extract(self, src_dir: str, only_files: list[str] | None = None, deep: bool = False) -> dict:
        root = Path(src_dir)
        inventory: dict[str, Any] = {}
        for relative in only_files or []:
            lines = (root / relative).read_text(encoding="utf-8").splitlines()
            title = next(
                (match.group(1) for line in lines if (match := _TITLE.match(line))),
                Path(relative).stem,
            )
            sections = [
                {"name": _identifier(match.group(1)), "line": number, "kind": "class", "bases": []}
                for number, line in enumerate(lines, 1)
                if (match := _SECTION.match(line))
            ]
            folder = posixpath.dirname(relative)
            links = sorted({
                posixpath.normpath(posixpath.join(folder, target))
                for line in lines
                for target in _LINK.findall(line)
            })
            inventory[relative] = {
                "classes": sections,
                "functions": [],
                "language": "notes",
                "package": None,
                "title": title,
                "links": links,
            }
        return inventory


class NotesRenderer(BuiltInPageRenderer):
    """Titles each note page by the note's own heading."""

    def render_module(self, request: ModulePageRequest) -> str:
        markdown = request.builtin_markdown()
        title = request.file_data.get("title")
        if not isinstance(title, str):
            return markdown
        lines = markdown.split("\n")
        for index, line in enumerate(lines):
            if line.startswith("# "):
                lines[index] = f"# {title}"
                break
        return "\n".join(lines)


class NotesContextSource:
    """Linked notes are related; detail levels keep title, sections, links."""

    def related_sources(
        self, inventory: Mapping[str, Mapping[str, Any]]
    ) -> Mapping[str, Iterable[str]]:
        related: dict[str, set[str]] = {path: set() for path in inventory}
        for path, data in inventory.items():
            for target in data.get("links", ()):
                if target in related and target != path:
                    related[path].add(target)
                    related[target].add(path)
        return {path: sorted(targets) for path, targets in related.items()}

    def entry(self, data: Mapping[str, Any], detail: str) -> Mapping[str, Any]:
        entry: dict[str, Any] = {"title": data.get("title")}
        if detail in ("deep", "slim"):
            entry["sections"] = [
                section["name"] if isinstance(section, Mapping) else section
                for section in data.get("classes", data.get("sections", ()))
            ]
        if detail == "deep":
            entry["links"] = list(data.get("links", ()))
        return entry


#: The notes pack assembled from engine parts, for ``llm_wiki_engine.Engine``.
ENGINE_NOTES_PACK = DomainPack(
    "example/notes",
    ExtensionSourceClassifier({"notes": (".md",)}),
    page_renderer=NotesRenderer(),
    context_source=NotesContextSource(),
    extractors={"notes": "tests.notes_parts:NotesExtractor"},
)
