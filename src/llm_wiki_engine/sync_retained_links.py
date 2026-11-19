"""Pure, ownership-scoped link repairs for retained source pages."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator, Mapping
import posixpath
from urllib.parse import quote, unquote, urlsplit

from .markdown_sections import description_table_cells, parse_markdown_document
from .section_ownership import SectionOwnership, classify_section_ownership
from .validation import portable_path_key
from .wiki_media import (
    iter_markdown_link_targets,
    iter_mermaid_click_targets,
    mask_markdown_code,
)
from .wiki_surface import PageKind


def _structural_cells(text: str) -> Iterator[tuple[int, int]]:
    """Locate structural cells without reformatting mixed table rows."""
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    for row in description_table_cells(text):
        line = lines[row.row_index]
        cursor = 0
        for index, cell in enumerate(row.cells):
            start = line.find(cell, cursor)
            if start < 0:
                break
            cursor = start + len(cell)
            if index != row.description_index and cell:
                yield offsets[row.row_index] + start, offsets[row.row_index] + cursor


def _new_destination(target: str, relative: str, moves: Mapping[str, str]) -> str | None:
    url = urlsplit(target)
    if url.scheme or url.netloc or not url.path or url.path.startswith("/") or "\\" in url.path:
        return None
    old = posixpath.normpath(posixpath.join(posixpath.dirname(relative), unquote(url.path)))
    new = moves.get(portable_path_key(old))
    if new is None:
        return None
    # Generated links use explicit sibling directories even for same-kind
    # pages. Preserve that style while canonicalizing the destination casing.
    path = "../" + new if url.path.startswith("../") else posixpath.relpath(new, posixpath.dirname(relative))
    destination = quote(path, safe="/._-~")
    # Preserve the original query/fragment spelling, including empty suffixes.
    return destination + target[len(url.path):]


def _rewrite_region(text: str, relative: str, moves: Mapping[str, str], *, mermaid: bool) -> str:
    replacements = []
    masked = mask_markdown_code(text)
    masked = "".join(
        "".join("\n" if character == "\n" else " " for character in line)
        if line.startswith(("    ", "\t")) else line
        for line in masked.splitlines(keepends=True)
    )
    links = [(link, False) for link in iter_markdown_link_targets(masked)]
    if mermaid:
        links.extend((link, True) for link in iter_mermaid_click_targets(text))
    for link, diagram in links:
        if link.is_image:
            continue
        if not diagram:
            prefix = text[:link.start]
            if (len(prefix) - len(prefix.rstrip("\\"))) % 2:
                continue
        try:
            destination = _new_destination(link.target, relative, moves)
        except ValueError:
            # Malformed authored URLs are not authority to change a page.
            continue
        if destination is None or destination == link.target:
            continue
        original = text[link.start:link.end]
        # Parser offsets span the whole link/directive. Only replace its URL,
        # never a matching string in the label, tooltip, or optional title.
        target_start = original.index('"') + 1 if diagram else original.index("](") + 2
        raw = original[target_start:]
        offset = target_start + raw.index(link.target)
        start = link.start + offset
        replacements.append((start, start + len(link.target), destination))
    for start, end, destination in sorted(replacements, reverse=True):
        text = text[:start] + destination + text[end:]
    return text


def repair_retained_page_links(
    text: str, relative: str, kind: PageKind, moves: Mapping[str, str]
) -> str:
    """Apply each old-to-final mapping once, only to generated structure."""
    document = parse_markdown_document(text, relative)
    text = document.normalized_markdown
    ownership: dict[str, SectionOwnership] = {}
    occurrences: defaultdict[tuple[str | None, str], int] = defaultdict(int)
    replacements = []
    for index, section in enumerate(document.sections):
        key = (section.parent_locator, section.title.casefold())
        occurrences[key] += 1
        policy = classify_section_ownership(
            kind, section,
            parent_ownership=ownership.get(section.parent_locator or ""),
            canonical_occurrence=occurrences[key],
        )
        ownership[section.locator] = policy
        # Visit each character once; descendants inherit their section policy.
        end = section.end
        if index + 1 < len(document.sections):
            end = min(end, document.sections[index + 1].start)
        body = text[section.body_start:end]
        if policy is SectionOwnership.GENERATED:
            regions = [(0, len(body))]
        elif policy is SectionOwnership.MIXED:
            regions = list(_structural_cells(body))
        else:
            continue
        for start, stop in regions:
            old = body[start:stop]
            new = _rewrite_region(old, relative, moves, mermaid=policy is SectionOwnership.GENERATED)
            if old != new:
                replacements.append((section.body_start + start, section.body_start + stop, new))
    for start, end, new in sorted(replacements, reverse=True):
        text = text[:start] + new + text[end:]
    return text
