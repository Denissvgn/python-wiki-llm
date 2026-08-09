"""Deterministic Markdown section parsing and legacy sync splice helpers.

The hierarchy parser in this module is deliberately small.  It recognizes ATX
headings and the code/frontmatter constructs that can make heading-looking
lines non-structural, but it is not intended to be a complete CommonMark
parser.  All parsing and hashing is pure over the supplied strings.

The legacy helpers at the end of the module preserve the historical sync
command contract.  In particular, they intentionally keep first-match and
duplicate-table-row behavior that predates the hierarchy parser.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Callable, Iterable
from urllib.parse import quote

from .knowledge_evidence import hash_json, sha256_bytes

SECTION_ORDER_DOMAIN = "llm-wiki-markdown-section-order/v1"
MIXED_TABLE_DOMAIN = "llm-wiki-mixed-table-projection/v1"
LEGACY_GENERATED_INDEX_INTRO = (
    "Use this landing page to choose the right wiki surface."
)
GENERATED_INDEX_INTRO_WITH_GUIDES = (
    "Guides lead supported tasks. The generated indexes are exhaustive reference "
    "inventories of the selected source."
)
GENERATED_INDEX_INTRO_WITHOUT_GUIDES = (
    "This page is an exhaustive reference inventory of the selected source. "
    "Task-oriented guides are not yet available."
)
GENERATED_INDEX_INTROS = frozenset(
    {
        LEGACY_GENERATED_INDEX_INTRO,
        GENERATED_INDEX_INTRO_WITH_GUIDES,
        GENERATED_INDEX_INTRO_WITHOUT_GUIDES,
    }
)
GENERATED_INDEX_ENTRY_POINT_FLOWS_HEADING = (
    "Entry-point flows <!-- llm-wiki-generated:index:entry-point-flows -->"
)
GENERATED_INDEX_HTTP_API_CONTRACTS_HEADING = (
    "HTTP API contracts <!-- llm-wiki-generated:index:http-api-contracts -->"
)

_ATX_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
_FENCE_OPEN_RE = re.compile(r"^ {0,3}((?:`{3,})|(?:~{3,}))(.*)$")
_LEGACY_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_AUTO_GENERATED_RE = re.compile(r"^_Auto-generated from `.+`(?: in `.+`)?\._$")
_INDEX_GENERATED_HEADINGS = frozenset(
    heading.casefold()
    for heading in (
        "Surface Overview",
        "Entities",
        "Modules",
        "Workflows",
        "Guides",
        "User Flows",
        GENERATED_INDEX_ENTRY_POINT_FLOWS_HEADING,
        "Infrastructure",
        "Architecture",
        "Dependency Architecture",
        "API Contracts",
        GENERATED_INDEX_HTTP_API_CONTRACTS_HEADING,
        "Log",
    )
)
_INDEX_GENERATED_INTROS = {
    ("Catalog of project modules and entities.",),
    *((intro,) for intro in GENERATED_INDEX_INTROS),
}


def normalize_markdown(text: str) -> str:
    """Return *text* with CRLF and lone CR normalized to LF."""

    return text.replace("\r\n", "\n").replace("\r", "\n")


@dataclass(frozen=True)
class MarkdownSection:
    """One ATX heading and its exact normalized section extent.

    ``exact_text`` begins at the opening heading and ends immediately before
    the next heading of the same or shallower level (or at EOF).  It therefore
    includes nested sections and every blank line in that extent.
    """

    page_locator: str
    locator: str
    ordinal: int
    level: int
    title: str
    heading_path: tuple[str, ...]
    occurrence_path: tuple[int, ...]
    sibling_occurrence: int
    parent_locator: str | None
    child_locators: tuple[str, ...]
    start: int
    body_start: int
    end: int
    start_byte: int
    body_start_byte: int
    end_byte: int
    heading_text: str
    body: str
    exact_text: str
    exact_bytes: bytes
    exact_hash: str

    @property
    def section_hash(self) -> str:
        """Compatibility alias for the exact normalized section hash."""

        return self.exact_hash

    @property
    def occurrence(self) -> int:
        """Compatibility alias for :attr:`sibling_occurrence`."""

        return self.sibling_occurrence

    @property
    def path(self) -> tuple[str, ...]:
        """Compatibility alias for :attr:`heading_path`."""

        return self.heading_path

    def to_payload(self) -> dict[str, object]:
        """Return a deterministic, JSON-friendly section commitment."""

        return {
            "locator": self.locator,
            "page_locator": self.page_locator,
            "ordinal": self.ordinal,
            "level": self.level,
            "title": self.title,
            "heading_path": list(self.heading_path),
            "occurrence_path": list(self.occurrence_path),
            "sibling_occurrence": self.sibling_occurrence,
            "parent_locator": self.parent_locator,
            "child_locators": list(self.child_locators),
            "start": self.start_byte,
            "body_start": self.body_start_byte,
            "end": self.end_byte,
            "exact_hash": self.exact_hash,
        }


@dataclass(frozen=True)
class MarkdownSectionDocument:
    """Normalized Markdown plus its ordered hierarchy commitment."""

    page_locator: str
    normalized_markdown: str
    normalized_bytes: bytes
    exact_hash: str
    sections: tuple[MarkdownSection, ...]
    ordering_hash: str

    def __iter__(self):
        return iter(self.sections)

    def __len__(self) -> int:
        return len(self.sections)

    def __getitem__(self, index):
        return self.sections[index]


@dataclass(frozen=True)
class TableDescriptionCell:
    """One table Description cell without lossy duplicate-key collapse."""

    key: str
    occurrence: int
    description: str
    row_index: int
    cells: tuple[str, ...]
    description_index: int


@dataclass(frozen=True)
class MixedTableProjection:
    """Separate structural and semantic commitments for one mixed section."""

    structural_projection: dict[str, object]
    semantic_projection: dict[str, object]
    structural_hash: str
    semantic_hash: str
    description_cells: tuple[TableDescriptionCell, ...]


@dataclass(frozen=True)
class _HeadingCandidate:
    level: int
    title: str
    start: int
    body_start: int
    parent_index: int | None
    heading_path: tuple[str, ...]
    occurrence_path: tuple[int, ...]
    occurrence: int


def _line_content(line: str) -> str:
    return line[:-1] if line.endswith("\n") else line


def _frontmatter_extent(lines: list[str]) -> int:
    """Return the number of leading frontmatter lines to mask.

    An unclosed leading frontmatter block conservatively masks the complete
    document.  A UTF-8 BOM before the first delimiter is tolerated.
    """

    if not lines:
        return 0
    first = _line_content(lines[0]).removeprefix("\ufeff").strip(" \t")
    if first != "---":
        return 0
    for index, line in enumerate(lines[1:], start=1):
        if _line_content(line).strip(" \t") in {"---", "..."}:
            return index + 1
    return len(lines)


def _atx_heading(line: str) -> tuple[int, str] | None:
    match = _ATX_HEADING_RE.fullmatch(line)
    if match is None:
        return None
    marks, raw_title = match.groups()
    title = raw_title or ""
    # A trailing run is a closing sequence only when separated from content.
    # When the whole title is hashes, the separator after the opening run is
    # sufficient and the resulting ATX title is empty.
    if title and set(title) == {"#"}:
        title = ""
    else:
        title = re.sub(r"[ \t]+#+[ \t]*$", "", title)
    return len(marks), title.strip(" \t")


def _iter_structural_headings(markdown: str) -> Iterable[tuple[int, str, int, int]]:
    """Yield ``(level, title, start, body_start)`` outside masked constructs."""

    lines = markdown.splitlines(keepends=True)
    frontmatter_lines = _frontmatter_extent(lines)
    offset = 0
    fence_character: str | None = None
    fence_length = 0

    for line_index, line_with_ending in enumerate(lines):
        line = _line_content(line_with_ending)
        body_start = offset + len(line_with_ending)
        if line_index < frontmatter_lines:
            offset = body_start
            continue

        if fence_character is not None:
            closing = re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
                line,
            )
            if closing is not None:
                fence_character = None
                fence_length = 0
            offset = body_start
            continue

        opening = _FENCE_OPEN_RE.fullmatch(line)
        if opening is not None:
            run, info = opening.groups()
            # CommonMark does not allow a backtick in a backtick-fence info
            # string.  Treating that line as ordinary text is conservative.
            if not (run[0] == "`" and "`" in info):
                fence_character = run[0]
                fence_length = len(run)
                offset = body_start
                continue

        heading = _atx_heading(line)
        if heading is not None:
            level, title = heading
            yield level, title, offset, body_start
        offset = body_start


def section_locator(
    page_locator: str,
    heading_path: Iterable[str],
    occurrence_path: Iterable[int],
) -> str:
    """Build a deterministic locator from a page and full sibling path."""

    if not isinstance(page_locator, str) or not page_locator:
        raise ValueError("page_locator must be a non-empty string")
    if "#" in page_locator:
        raise ValueError("page_locator must not already contain a fragment")
    headings = tuple(heading_path)
    occurrences = tuple(occurrence_path)
    if not headings or len(headings) != len(occurrences):
        raise ValueError("heading_path and occurrence_path must be non-empty peers")
    if any(not isinstance(value, str) for value in headings):
        raise ValueError("heading_path entries must be strings")
    if any(not isinstance(value, int) or value < 1 for value in occurrences):
        raise ValueError("occurrence_path entries must be positive integers")
    components = [
        f"{quote(title, safe='-._~')}~{occurrence}"
        for title, occurrence in zip(headings, occurrences)
    ]
    return f"{page_locator}#section/" + "/".join(components)


def parse_markdown_document(
    markdown: str,
    page_locator: str,
) -> MarkdownSectionDocument:
    """Parse and commit one normalized Markdown document."""

    if not isinstance(markdown, str):
        raise TypeError("markdown must be a string")
    if not isinstance(page_locator, str) or not page_locator:
        raise ValueError("page_locator must be a non-empty string")

    normalized = normalize_markdown(markdown)
    headings = list(_iter_structural_headings(normalized))
    candidates: list[_HeadingCandidate] = []
    stack: list[int] = []
    occurrences: defaultdict[tuple[int | None, str], int] = defaultdict(int)

    for level, title, start, body_start in headings:
        while stack and candidates[stack[-1]].level >= level:
            stack.pop()
        parent_index = stack[-1] if stack else None
        key = (parent_index, title)
        occurrences[key] += 1
        occurrence = occurrences[key]
        if parent_index is None:
            heading_path = (title,)
            occurrence_path = (occurrence,)
        else:
            parent = candidates[parent_index]
            heading_path = parent.heading_path + (title,)
            occurrence_path = parent.occurrence_path + (occurrence,)
        candidates.append(
            _HeadingCandidate(
                level=level,
                title=title,
                start=start,
                body_start=body_start,
                parent_index=parent_index,
                heading_path=heading_path,
                occurrence_path=occurrence_path,
                occurrence=occurrence,
            )
        )
        stack.append(len(candidates) - 1)

    utf8_prefix_lengths = [0]
    for character in normalized:
        utf8_prefix_lengths.append(
            utf8_prefix_lengths[-1] + len(character.encode("utf-8"))
        )

    sections: list[MarkdownSection] = []
    for index, candidate in enumerate(candidates):
        end = len(normalized)
        for following in candidates[index + 1 :]:
            if following.level <= candidate.level:
                end = following.start
                break
        parent_locator = (
            section_locator(
                page_locator,
                candidates[candidate.parent_index].heading_path,
                candidates[candidate.parent_index].occurrence_path,
            )
            if candidate.parent_index is not None
            else None
        )
        locator = section_locator(
            page_locator,
            candidate.heading_path,
            candidate.occurrence_path,
        )
        exact_text = normalized[candidate.start : end]
        exact_bytes = exact_text.encode("utf-8")
        sections.append(
            MarkdownSection(
                page_locator=page_locator,
                locator=locator,
                ordinal=index,
                level=candidate.level,
                title=candidate.title,
                heading_path=candidate.heading_path,
                occurrence_path=candidate.occurrence_path,
                sibling_occurrence=candidate.occurrence,
                parent_locator=parent_locator,
                child_locators=(),
                start=candidate.start,
                body_start=candidate.body_start,
                end=end,
                start_byte=utf8_prefix_lengths[candidate.start],
                body_start_byte=utf8_prefix_lengths[candidate.body_start],
                end_byte=utf8_prefix_lengths[end],
                heading_text=normalized[candidate.start : candidate.body_start],
                body=normalized[candidate.body_start : end],
                exact_text=exact_text,
                exact_bytes=exact_bytes,
                exact_hash=sha256_bytes(exact_bytes),
            )
        )

    children: defaultdict[str, list[str]] = defaultdict(list)
    for section in sections:
        if section.parent_locator is not None:
            children[section.parent_locator].append(section.locator)
    sections = [
        replace(section, child_locators=tuple(children[section.locator]))
        for section in sections
    ]
    ordering_payload = {
        "domain": SECTION_ORDER_DOMAIN,
        "page_locator": page_locator,
        "sections": [
            {
                "locator": section.locator,
                "ordinal": section.ordinal,
                "parent_locator": section.parent_locator,
                "child_locators": list(section.child_locators),
            }
            for section in sections
        ],
    }
    normalized_bytes = normalized.encode("utf-8")
    return MarkdownSectionDocument(
        page_locator=page_locator,
        normalized_markdown=normalized,
        normalized_bytes=normalized_bytes,
        exact_hash=sha256_bytes(normalized_bytes),
        sections=tuple(sections),
        ordering_hash=hash_json(ordering_payload),
    )


def parse_markdown_sections(
    markdown: str,
    page_locator: str,
) -> tuple[MarkdownSection, ...]:
    """Return parsed sections in exact document order."""

    return parse_markdown_document(markdown, page_locator).sections


# A discoverable verb used by the knowledge builder.
collect_markdown_sections = parse_markdown_sections


def split_table_row(line: str) -> list[str]:
    """Split a pipe table row, respecting escapes and inline-code pipe runs."""

    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    body = stripped[1:-1]
    cells: list[str] = []
    current: list[str] = []
    code_fence = 0
    index = 0
    while index < len(body):
        character = body[index]
        if character == "\\" and index + 1 < len(body):
            current.extend((character, body[index + 1]))
            index += 2
            continue
        if character == "`":
            end = index + 1
            while end < len(body) and body[end] == "`":
                end += 1
            run = end - index
            current.append(body[index:end])
            if code_fence == 0:
                code_fence = run
            elif run == code_fence:
                code_fence = 0
            index = end
            continue
        if character == "|" and code_fence == 0:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(character)
        index += 1
    cells.append("".join(current).strip())
    return cells


def format_table_row(cells: Iterable[str]) -> str:
    """Render already escaped Markdown table cells canonically."""

    return "| " + " | ".join(cells) + " |"


def is_table_separator(cells: list[str]) -> bool:
    """Return whether every supplied cell is a Markdown separator cell."""

    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def semantic_table_key(cell: str) -> str:
    """Normalize the first cell exactly as the historical sync merger does."""

    key = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cell)
    key = key.replace("`", "").replace("*", "").replace("\\|", "|")
    return key.strip()


def is_placeholder_description(value: str | None) -> bool:
    """Return whether a Description cell/body is not human semantic content."""

    if value is None:
        return True
    stripped = value.strip()
    if not stripped or stripped in {"—", "-"}:
        return True
    return _AUTO_GENERATED_RE.match(stripped) is not None


def should_preserve_semantic_value(
    existing: str | None,
    generated: str | None,
    old_generated: str | None,
) -> bool:
    """Apply the historical three-way semantic preservation decision."""

    if is_placeholder_description(existing):
        return False
    existing_stripped = (existing or "").strip()
    generated_stripped = (generated or "").strip()
    if old_generated is None:
        return existing_stripped != generated_stripped
    old_stripped = old_generated.strip()
    if existing_stripped == old_stripped:
        return False
    return existing_stripped != generated_stripped


def description_table_cells(markdown: str) -> tuple[TableDescriptionCell, ...]:
    """Return first-table Description cells with duplicate occurrences intact."""

    lines = normalize_markdown(markdown).splitlines()
    for index, line in enumerate(lines):
        headers = split_table_row(line)
        if not headers or "Description" not in headers:
            continue
        description_index = headers.index("Description")
        row_start = index + 1
        if row_start < len(lines) and is_table_separator(
            split_table_row(lines[row_start])
        ):
            row_start += 1
        occurrences: defaultdict[str, int] = defaultdict(int)
        cells: list[TableDescriptionCell] = []
        for row_index in range(row_start, len(lines)):
            row = split_table_row(lines[row_index])
            if not row:
                break
            if len(row) <= description_index:
                continue
            key = semantic_table_key(row[0])
            if not key:
                continue
            occurrences[key] += 1
            cells.append(
                TableDescriptionCell(
                    key=key,
                    occurrence=occurrences[key],
                    description=row[description_index].strip(),
                    row_index=row_index,
                    cells=tuple(row),
                    description_index=description_index,
                )
            )
        return tuple(cells)
    return ()


def mixed_table_projection(section_markdown: str) -> MixedTableProjection:
    """Build structural/semantic projections for the first Description table.

    The structural projection replaces each Description cell with a stable
    marker and retains row order/multiplicity.  The semantic projection keeps
    only the historical last-non-placeholder Description value for each
    semantic row key. This matches sync's preserved description mapping, so
    generated row reordering or duplicate multiplicity is not semantic.
    """

    normalized = normalize_markdown(section_markdown)
    lines = normalized.splitlines()
    trailing_newline = normalized.endswith("\n")
    cells = description_table_cells(normalized)
    structural_lines = list(lines)
    if cells:
        for cell in cells:
            row = list(cell.cells)
            row[cell.description_index] = "<semantic-description>"
            structural_lines[cell.row_index] = format_table_row(row)
    structural_projection: dict[str, object] = {
        "domain": MIXED_TABLE_DOMAIN,
        "lines": structural_lines,
        "trailing_newline": trailing_newline,
    }
    semantic_by_key: dict[str, str] = {}
    for cell in cells:
        if not is_placeholder_description(cell.description):
            # Historical sync behavior is intentionally last-duplicate-wins.
            semantic_by_key[cell.key] = cell.description
    semantic_cells = [
        {"key": key, "description": description}
        for key, description in semantic_by_key.items()
    ]
    semantic_cells.sort(
        key=lambda item: (
            str(item["key"]).casefold(),
            str(item["key"]),
            str(item["description"]),
        )
    )
    semantic_projection: dict[str, object] = {
        "domain": MIXED_TABLE_DOMAIN,
        "description_cells": semantic_cells,
    }
    return MixedTableProjection(
        structural_projection=structural_projection,
        semantic_projection=semantic_projection,
        structural_hash=hash_json(structural_projection),
        semantic_hash=hash_json(semantic_projection),
        description_cells=cells,
    )


# ── Byte-compatible sync/bootstrap helpers ──────────────────────────────────


def section_bounds(
    lines: list[str], heading: str
) -> tuple[int, int, int] | None:
    """Return historical level-two ``(heading, body_start, body_end)`` bounds.

    This helper intentionally does not use :func:`parse_markdown_sections`;
    changing its permissive matching would change existing sync output.
    """

    target = heading.casefold()
    for index, line in enumerate(lines):
        match = _LEGACY_HEADING_RE.match(line.strip())
        if match is None:
            continue
        level = len(match.group(1))
        title = match.group(2).strip().casefold()
        if level != 2 or title != target:
            continue
        end = len(lines)
        for following in range(index + 1, len(lines)):
            next_match = _LEGACY_HEADING_RE.match(lines[following].strip())
            if next_match is not None and len(next_match.group(1)) <= level:
                end = following
                break
        return index, index + 1, end
    return None


def trim_blank_lines(lines: list[str]) -> list[str]:
    """Trim blank lines exactly as the historical sync helper does."""

    start = 0
    end = len(lines)
    while start < end and lines[start].strip() == "":
        start += 1
    while end > start and lines[end - 1].strip() == "":
        end -= 1
    return lines[start:end]


def section_body(markdown: str, heading: str) -> str | None:
    """Return the trimmed body of the first historical level-two section."""

    lines = normalize_markdown(markdown).splitlines()
    bounds = section_bounds(lines, heading)
    if bounds is None:
        return None
    _, start, end = bounds
    return "\n".join(trim_blank_lines(lines[start:end])).strip()


def replace_section_body(markdown: str, heading: str, body: str) -> str:
    """Replace the first historical level-two body byte-compatibly."""

    lines = normalize_markdown(markdown).splitlines()
    bounds = section_bounds(lines, heading)
    if bounds is None:
        return markdown
    heading_index, _, end = bounds
    replacement = [""] + body.splitlines() + [""]
    return "\n".join(lines[: heading_index + 1] + replacement + lines[end:])


def preserve_level_two_section_exact(
    existing: str, generated: str, heading: str
) -> str:
    """Splice the first matching human-owned level-two section verbatim."""

    pattern = re.compile(
        rf"(?ms)^##[ \t]+{re.escape(heading)}[ \t]*\r?\n.*?"
        rf"(?=^##[ \t]+|\Z)"
    )
    old_match = pattern.search(existing)
    new_match = pattern.search(generated)
    if old_match is None or new_match is None:
        return generated
    old_section = old_match.group(0)
    if old_section == new_match.group(0):
        return generated
    return (
        generated[: new_match.start()]
        + old_section
        + generated[new_match.end() :]
    )


def _legacy_heading_title(line: str) -> str | None:
    match = _LEGACY_HEADING_RE.match(line.strip())
    if match is None:
        return None
    return match.group(2).strip()


def _legacy_level_two_sections(
    lines: list[str],
) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    for index, line in enumerate(lines):
        match = _LEGACY_HEADING_RE.match(line.strip())
        if match is None or len(match.group(1)) != 2:
            continue
        end = len(lines)
        for following in range(index + 1, len(lines)):
            next_match = _LEGACY_HEADING_RE.match(lines[following].strip())
            if next_match is not None and len(next_match.group(1)) <= 2:
                end = following
                break
        sections.append(
            (line.strip(), trim_blank_lines(lines[index + 1 : end]))
        )
    return sections


def _index_intro_lines(lines: list[str]) -> list[str]:
    start = 1 if lines and lines[0].startswith("# ") else 0
    first_section = len(lines)
    for index, line in enumerate(lines[start:], start=start):
        match = _LEGACY_HEADING_RE.match(line.strip())
        if match is not None and len(match.group(1)) == 2:
            first_section = index
            break
    return trim_blank_lines(lines[start:first_section])


def _merge_index_intro_into_notes(
    sections: list[tuple[str, list[str]]],
    intro: list[str],
) -> list[tuple[str, list[str]]]:
    if not intro:
        return sections
    merged: list[tuple[str, list[str]]] = []
    inserted = False
    for heading, body in sections:
        title = _legacy_heading_title(heading)
        if title and title.casefold() == "notes" and not inserted:
            merged.append((heading, intro + ([""] if body else []) + body))
            inserted = True
        else:
            merged.append((heading, body))
    if not inserted:
        merged.insert(0, ("## Notes", intro))
    return merged


def preserve_index_custom_sections(old_markdown: str, new_markdown: str) -> str:
    """Preserve historical custom index prose and level-two sections.

    This is the service-layer form of the sync compatibility splice. Its
    deliberately permissive legacy parsing keeps existing output bytes stable.
    """

    old_lines = normalize_markdown(old_markdown).splitlines()
    custom_sections = [
        (heading, body)
        for heading, body in _legacy_level_two_sections(old_lines)
        if (_legacy_heading_title(heading) or "").casefold()
        not in _INDEX_GENERATED_HEADINGS
    ]
    intro = _index_intro_lines(old_lines)
    if tuple(intro) in _INDEX_GENERATED_INTROS:
        intro = []
    preserved = _merge_index_intro_into_notes(custom_sections, intro)
    if not preserved:
        return new_markdown

    lines = normalize_markdown(new_markdown).splitlines()
    while lines and lines[-1].strip() == "":
        lines.pop()
    lines.append("")
    for heading, body in preserved:
        lines.append(heading)
        lines.append("")
        lines.extend(body)
        lines.append("")
    return "\n".join(lines)


def table_description_cells(markdown: str, heading: str) -> dict[str, str]:
    """Return the historical duplicate-collapsing Description mapping."""

    lines = normalize_markdown(markdown).splitlines()
    bounds = section_bounds(lines, heading)
    if bounds is None:
        return {}
    _, start, end = bounds

    for index in range(start, end):
        headers = split_table_row(lines[index])
        if not headers or "Description" not in headers:
            continue
        description_index = headers.index("Description")
        row_start = index + 1
        if row_start < end and is_table_separator(split_table_row(lines[row_start])):
            row_start += 1

        descriptions: dict[str, str] = {}
        for row_index in range(row_start, end):
            row = split_table_row(lines[row_index])
            if not row:
                break
            if len(row) <= description_index:
                continue
            key = semantic_table_key(row[0])
            description = row[description_index].strip()
            if key and not is_placeholder_description(description):
                # Historical behavior is intentionally last-duplicate-wins.
                descriptions[key] = description
        return descriptions
    return {}


def preserve_table_description_cells(
    markdown: str,
    heading: str,
    descriptions: dict[str, str],
    old_descriptions: dict[str, str] | None = None,
    *,
    should_preserve: Callable[[str | None, str | None, str | None], bool]
    | None = None,
) -> tuple[str, int]:
    """Restore historical semantic cells without changing duplicate handling."""

    if not descriptions:
        return markdown, 0
    predicate = should_preserve or should_preserve_semantic_value
    lines = normalize_markdown(markdown).splitlines()
    bounds = section_bounds(lines, heading)
    if bounds is None:
        return markdown, 0
    _, start, end = bounds

    preserved = 0
    for index in range(start, end):
        headers = split_table_row(lines[index])
        if not headers or "Description" not in headers:
            continue
        description_index = headers.index("Description")
        row_start = index + 1
        if row_start < end and is_table_separator(split_table_row(lines[row_start])):
            row_start += 1

        for row_index in range(row_start, end):
            row = split_table_row(lines[row_index])
            if not row:
                break
            if len(row) <= description_index:
                continue
            key = semantic_table_key(row[0])
            existing_description = descriptions.get(key)
            old_description = (old_descriptions or {}).get(key)
            if existing_description is None:
                continue
            if not predicate(
                existing_description,
                row[description_index],
                old_description,
            ):
                continue
            row[description_index] = existing_description
            lines[row_index] = format_table_row(row)
            preserved += 1
        break

    if preserved == 0:
        return markdown, 0
    updated = "\n".join(lines)
    if markdown.endswith("\n"):
        updated += "\n"
    return updated, preserved


__all__ = [
    "MarkdownSection",
    "MarkdownSectionDocument",
    "MixedTableProjection",
    "TableDescriptionCell",
    "collect_markdown_sections",
    "description_table_cells",
    "format_table_row",
    "is_placeholder_description",
    "is_table_separator",
    "mixed_table_projection",
    "normalize_markdown",
    "parse_markdown_document",
    "parse_markdown_sections",
    "preserve_level_two_section_exact",
    "preserve_table_description_cells",
    "replace_section_body",
    "section_body",
    "section_bounds",
    "section_locator",
    "semantic_table_key",
    "should_preserve_semantic_value",
    "split_table_row",
    "table_description_cells",
    "trim_blank_lines",
]
