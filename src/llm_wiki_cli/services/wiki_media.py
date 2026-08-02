"""Media reference parsing for wiki pages and agent-owned assets."""

from __future__ import annotations

import os
import re
from bisect import bisect_right
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterator, Mapping, Optional, Union
from urllib.parse import unquote, urlsplit

IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"})
VIDEO_EXTENSIONS = frozenset({".mp4", ".webm"})
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
DEFAULT_MEDIA_SIZE_WARN_BYTES = 2 * 1024 * 1024

_MARKDOWN_TITLE_RE = re.compile(
    r"^(?P<target><[^>]+>|[^\s]+)"
    r"(?:\s+(?:\"(?P<double_title>[^\"]*)\"|'(?P<single_title>[^']*)'))?\s*$"
)
_AUTHORITY_USERINFO_RE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*:)?//[^/?#\s<>'\"]*@")
_URI_AUTHORITY_PREFIX_RE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*:)?//")
_URI_TOKEN_START_RE = re.compile(
    r"(?:^|[^A-Za-z0-9._~/%+-])"
    r"(?P<uri><?(?:[A-Za-z][A-Za-z0-9+.-]*:)?//)"
)
_REFERENCE_DEFINITION_RE = re.compile(r"^[ \t]{0,3}\[([^\]]+)\]:[ \t]*(.+?)\s*$")
_REFERENCE_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\[([^\]]*)\]")
_README_ASSET_RE = re.compile(r"^README(?:\..+)?$", re.IGNORECASE)
_MERMAID_CLICK_RE = re.compile(
    r"^[ \t]*(?P<directive>click[ \t]+(?P<label>\S+)[ \t]+"
    r'"(?P<target>[^"]*)")',
    re.MULTILINE,
)


@dataclass(frozen=True)
class MediaReference:
    page_path: Path
    page_rel: str
    raw_target: str
    target: str
    media_type: str
    source: str
    alt_text: Optional[str] = None
    requires_alt: bool = False


@dataclass(frozen=True)
class MarkdownLinkTarget:
    raw_target: str
    target: str
    label: str
    is_image: bool
    start: int
    end: int


@dataclass(frozen=True)
class AssetIndex:
    counts: dict[str, object]
    by_page: dict[str, list[str]]
    referenced: list[str]
    unreferenced: list[str]
    expected_pages: dict[str, Optional[str]]
    existing_paths: frozenset[str] = frozenset()


class _HtmlMediaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str, Optional[str], bool, str]] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, Optional[str]]],
    ) -> None:
        tag_name = tag.casefold()
        if tag_name not in {"img", "video", "source"}:
            return
        values = {name.casefold(): value for name, value in attrs}
        src = values.get("src")
        alt = values.get("alt")
        if src is not None:
            self.references.append(
                (tag_name, src.strip(), alt, tag_name == "img", "html")
            )
        if tag_name in {"img", "source"}:
            srcset = values.get("srcset")
            if srcset is not None:
                for candidate in split_srcset_candidates(srcset):
                    self.references.append(
                        (tag_name, candidate, alt, False, "html_srcset")
                    )


def strip_fenced_code_blocks(content: str) -> str:
    """Blank fenced code blocks while preserving line count."""
    stripped: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    for line in content.splitlines(keepends=True):
        marker = _fence_marker(line)
        if in_fence:
            stripped.append(_blank_line(line))
            if (
                marker is not None
                and marker[0] == fence_char
                and marker[1] >= fence_len
            ):
                in_fence = False
            continue
        if marker is not None:
            in_fence = True
            fence_char, fence_len = marker
            stripped.append(_blank_line(line))
            continue
        stripped.append(line)
    return "".join(stripped)


def mask_fenced_code_blocks(content: str) -> str:
    """Blank fenced code blocks without changing character offsets.

    Unlike :func:`strip_fenced_code_blocks`, this helper retains the width of
    every fenced line.  Parsers can therefore report half-open offsets against
    the original Markdown string while excluding fenced pseudo-syntax.
    """

    masked: list[str] = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    for line in content.splitlines(keepends=True):
        marker = _fence_marker(line)
        if in_fence:
            masked.append(_mask_line(line))
            if (
                marker is not None
                and marker[0] == fence_char
                and marker[1] >= fence_len
            ):
                in_fence = False
            continue
        if marker is not None:
            in_fence = True
            fence_char, fence_len = marker
            masked.append(_mask_line(line))
            continue
        masked.append(line)
    return "".join(masked)


def _mask_inline_code_spans(content: str) -> str:
    """Blank matched backtick code spans without changing offsets or newlines.

    Backtick runs are considered as maximal delimiters and only an exact-length
    later run closes a span.  Different-length runs remain part of the span.
    An escaped first backtick remains literal, while any remaining run can open
    a span.  Opening runs without a matching closer are left untouched.
    """

    runs: list[tuple[int, int]] = []
    offset = 0
    while offset < len(content):
        run_start = content.find("`", offset)
        if run_start == -1:
            break
        run_end = run_start + 1
        while run_end < len(content) and content[run_end] == "`":
            run_end += 1
        runs.append((run_start, run_end))
        offset = run_end

    runs_by_length: dict[int, list[int]] = {}
    for run_index, (run_start, run_end) in enumerate(runs):
        runs_by_length.setdefault(run_end - run_start, []).append(run_index)

    def matching_closer(run_index: int, delimiter_length: int) -> Optional[int]:
        candidates = runs_by_length.get(delimiter_length, [])
        candidate_offset = bisect_right(candidates, run_index)
        if candidate_offset == len(candidates):
            return None
        return candidates[candidate_offset]

    masked = list(content)
    run_index = 0
    while run_index < len(runs):
        run_start, run_end = runs[run_index]
        delimiter_length = run_end - run_start
        opener_start = run_start
        if _is_escaped_backtick_run(content, run_start):
            opener_start += 1
            delimiter_length -= 1
        if delimiter_length == 0:
            run_index += 1
            continue
        closer_index = matching_closer(run_index, delimiter_length)
        if closer_index is None:
            run_index += 1
            continue
        closer_end = runs[closer_index][1]
        for index in range(opener_start, closer_end):
            if content[index] not in {"\r", "\n"}:
                masked[index] = " "
        run_index = closer_index + 1

    return "".join(masked)


def _is_escaped_backtick_run(content: str, offset: int) -> bool:
    backslashes = 0
    cursor = offset - 1
    while cursor >= 0 and content[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def iter_mermaid_click_targets(content: str) -> Iterator[MarkdownLinkTarget]:
    """Yield URL-bearing ``click`` directives from explicit Mermaid fences.

    The supported form intentionally matches generated wiki diagrams:
    ``click <node> "<target>"``.  Callback, ``href``, and single-quoted forms
    are outside this narrow observation boundary.
    """

    for info, block_start, block_end in _iter_fenced_blocks(content):
        if info.casefold() != "mermaid":
            continue
        block = content[block_start:block_end]
        for match in _MERMAID_CLICK_RE.finditer(block):
            raw_target = match.group("target")
            yield MarkdownLinkTarget(
                raw_target=raw_target,
                target=normalize_markdown_link_target(raw_target),
                label=match.group("label"),
                is_image=False,
                start=block_start + match.start("directive"),
                end=block_start + match.end("directive"),
            )


def _fence_marker(line: str) -> Optional[tuple[str, int]]:
    stripped = line.lstrip()
    if stripped.startswith("```"):
        return "`", len(stripped) - len(stripped.lstrip("`"))
    if stripped.startswith("~~~"):
        return "~", len(stripped) - len(stripped.lstrip("~"))
    return None


def _blank_line(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    return ""


def _mask_line(line: str) -> str:
    if line.endswith("\r\n"):
        return (" " * (len(line) - 2)) + "\r\n"
    if line.endswith(("\n", "\r")):
        return (" " * (len(line) - 1)) + line[-1]
    return " " * len(line)


def _iter_fenced_blocks(content: str) -> Iterator[tuple[str, int, int]]:
    """Yield ``(info, body_start, body_end)`` using the established policy."""

    in_fence = False
    fence_char = ""
    fence_len = 0
    info = ""
    body_start = 0
    offset = 0
    for line in content.splitlines(keepends=True):
        marker = _fence_marker(line)
        if in_fence:
            if (
                marker is not None
                and marker[0] == fence_char
                and marker[1] >= fence_len
            ):
                yield info, body_start, offset
                in_fence = False
            offset += len(line)
            continue
        if marker is not None:
            fence_char, fence_len = marker
            stripped = line.lstrip()
            info = stripped[fence_len:].strip()
            body_start = offset + len(line)
            in_fence = True
        offset += len(line)
    if in_fence:
        yield info, body_start, len(content)


def iter_markdown_link_targets(content: str) -> Iterator[MarkdownLinkTarget]:
    """Yield inline markdown link/image targets with balanced parenthesis support."""
    idx = 0
    length = len(content)
    while idx < length:
        is_image = content.startswith("![", idx)
        label_start = idx + 2 if is_image else idx + 1
        if not is_image:
            if content[idx] != "[" or (idx > 0 and content[idx - 1] == "!"):
                idx += 1
                continue
        label_end = content.find("]", label_start)
        if label_end == -1 or label_end + 1 >= length or content[label_end + 1] != "(":
            idx += 1
            continue
        parsed = _scan_markdown_target(content, label_end + 2)
        if parsed is None:
            idx += 1
            continue
        raw_target, end = parsed
        yield MarkdownLinkTarget(
            raw_target=raw_target,
            target=normalize_markdown_link_target(raw_target),
            label=content[label_start:label_end],
            is_image=is_image,
            start=idx,
            end=end,
        )
        idx = end


def _scan_markdown_target(content: str, start: int) -> Optional[tuple[str, int]]:
    idx = start
    depth = 0
    quote: Optional[str] = None
    while idx < len(content):
        char = content[idx]
        if quote is not None:
            if char == quote:
                quote = None
            idx += 1
            continue
        if char in {"'", '"'}:
            quote = char
            idx += 1
            continue
        if char == "(":
            depth += 1
            idx += 1
            continue
        if char == ")":
            if depth == 0:
                return content[start:idx], idx + 1
            depth -= 1
            idx += 1
            continue
        idx += 1
    return None


def split_srcset_candidates(value: str) -> list[str]:
    candidates = []
    idx = 0
    length = len(value)
    while idx < length:
        while idx < length and (value[idx].isspace() or value[idx] == ","):
            idx += 1
        start = idx
        if value[idx:].casefold().startswith("data:"):
            while idx < length and not value[idx].isspace():
                idx += 1
        else:
            while idx < length and not value[idx].isspace() and value[idx] != ",":
                idx += 1
        candidate = value[start:idx].strip()
        if candidate:
            candidates.append(candidate)
        while idx < length and value[idx] != ",":
            idx += 1
    return candidates


def normalize_markdown_link_target(raw_target: str) -> str:
    """Return a markdown link target without optional title text."""
    target = raw_target.strip()
    match = _MARKDOWN_TITLE_RE.match(target)
    if match:
        target = match.group("target").strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    return target


def contains_uri_authority_userinfo(value: str) -> bool:
    """Detect authority userinfo without scanning URI query/fragment values.

    The first Markdown destination token is inspected as one URI. Any
    whitespace-delimited trailing text is inspected as separate URI tokens,
    covering supported titles and malformed scanner tails without interpreting
    nested URI-looking query or fragment data as another authority.
    """

    text = value.strip()
    if text.startswith("<") and ">" in text:
        destination_end = text.index(">") + 1
        destination = text[:destination_end]
        tail = text[destination_end:].strip()
    else:
        parts = text.split(maxsplit=1)
        destination = parts[0] if parts else ""
        tail = parts[1] if len(parts) == 2 else ""
    if destination.startswith("<"):
        destination = destination[1:]
    if destination.endswith(">"):
        destination = destination[:-1]
    destination = destination.strip()
    if _uri_candidate_contains_authority_userinfo(destination):
        return True

    for token in tail.split():
        candidate = token.lstrip("\"'(<[")
        if _URI_AUTHORITY_PREFIX_RE.match(candidate):
            if _uri_candidate_contains_authority_userinfo(candidate):
                return True
            continue
        match = _URI_TOKEN_START_RE.search(candidate)
        if match is not None:
            uri_candidate = candidate[match.start("uri") :].lstrip("<")
            if _uri_candidate_contains_authority_userinfo(uri_candidate):
                return True
    return False


def _uri_candidate_contains_authority_userinfo(candidate: str) -> bool:
    if _AUTHORITY_USERINFO_RE.match(candidate):
        return True
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return False
    return bool(
        parsed.netloc and (parsed.username is not None or parsed.password is not None)
    )


def local_link_path(raw_target: str) -> Optional[str]:
    """Return the path component for a local link target, or None if ignored."""
    target = normalize_markdown_link_target(raw_target)
    if not target or target.startswith("#") or "\x00" in target:
        return None
    try:
        parsed = urlsplit(target)
    except ValueError:
        return target.partition("#")[0] or None
    if parsed.netloc or parsed.scheme:
        return None
    path = parsed.path
    if not path:
        return None
    return unquote(path).replace("\\", "/")


def media_type_for_path(path: str) -> Optional[str]:
    suffix = Path(path).suffix.casefold()
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    return None


def is_media_target(raw_target: str) -> bool:
    local_path = local_link_path(raw_target)
    return local_path is not None and media_type_for_path(local_path) is not None


def collect_media_references(
    page_path: Union[str, Path],
    page_rel: str,
    content: str,
) -> list[MediaReference]:
    page = Path(page_path)
    content = _mask_inline_code_spans(mask_fenced_code_blocks(content))
    references: list[MediaReference] = []
    for link in iter_markdown_link_targets(content):
        target = local_link_path(link.raw_target)
        if target is None:
            continue
        media_type = media_type_for_path(target)
        if media_type is None:
            continue
        references.append(
            MediaReference(
                page_path=page,
                page_rel=page_rel,
                raw_target=link.raw_target,
                target=target,
                media_type=media_type,
                source="markdown" if link.is_image else "markdown_link",
                alt_text=link.label.strip() if link.is_image else None,
                requires_alt=link.is_image and media_type == "image",
            )
        )

    definitions = _reference_definitions(content)
    for match in _REFERENCE_IMAGE_RE.finditer(content):
        alt_text = match.group(1).strip()
        label = match.group(2).strip() or alt_text
        raw_target = definitions.get(_reference_label(label))
        if raw_target is None:
            continue
        target = local_link_path(raw_target)
        if target is None:
            continue
        media_type = media_type_for_path(target)
        if media_type is None:
            continue
        references.append(
            MediaReference(
                page_path=page,
                page_rel=page_rel,
                raw_target=raw_target,
                target=target,
                media_type=media_type,
                source="markdown_reference",
                alt_text=alt_text,
                requires_alt=media_type == "image",
            )
        )

    parser = _HtmlMediaParser()
    parser.feed(content)
    for _tag, raw_target, alt, requires_alt, source in parser.references:
        target = local_link_path(raw_target)
        if target is None:
            continue
        media_type = media_type_for_path(target)
        if media_type is None:
            continue
        references.append(
            MediaReference(
                page_path=page,
                page_rel=page_rel,
                raw_target=raw_target,
                target=target,
                media_type=media_type,
                source=source,
                alt_text=alt.strip() if alt is not None else None,
                requires_alt=requires_alt,
            )
        )
    return references


def _reference_definitions(content: str) -> dict[str, str]:
    definitions: dict[str, str] = {}
    for line in content.splitlines():
        match = _REFERENCE_DEFINITION_RE.match(line)
        if not match:
            continue
        definitions[_reference_label(match.group(1))] = match.group(2).strip()
    return definitions


def _reference_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def collect_media_references_by_page(
    wiki_dir: Union[str, Path],
    content_by_page: Mapping[str, str],
) -> dict[str, list[MediaReference]]:
    wiki = Path(wiki_dir)
    return {
        page_rel: collect_media_references(wiki / Path(page_rel), page_rel, content)
        for page_rel, content in sorted(content_by_page.items())
    }


def build_asset_index(
    wiki_dir: Union[str, Path],
    content_by_page: Optional[Mapping[str, str]] = None,
    references_by_page: Optional[Mapping[str, list[MediaReference]]] = None,
) -> AssetIndex:
    wiki = Path(wiki_dir)
    if references_by_page is None:
        content = content_by_page if content_by_page is not None else _read_pages(wiki)
        references_by_page = collect_media_references_by_page(wiki, content)
    by_page: dict[str, set[str]] = {}
    referenced_assets: set[str] = set()
    for page_rel, references in sorted(references_by_page.items()):
        assets = set()
        for reference in references:
            asset_rel = asset_relative_path(wiki, reference)
            if asset_rel is None:
                continue
            assets.add(asset_rel)
            referenced_assets.add(asset_rel)
        if assets:
            by_page[page_rel] = assets

    asset_paths = _asset_files(wiki)
    all_assets = set(asset_paths)
    unreferenced = all_assets - referenced_assets
    by_media_type = {"image": 0, "video": 0, "other": 0}
    for asset in asset_paths:
        media_type = media_type_for_path(asset)
        if media_type is not None:
            by_media_type[media_type] += 1
        else:
            by_media_type["other"] += 1

    return AssetIndex(
        counts={
            "total": len(asset_paths),
            "referenced": len(referenced_assets & all_assets),
            "unreferenced": len(unreferenced),
            "by_media_type": by_media_type,
        },
        by_page={
            page: sorted(paths, key=lambda value: (value.casefold(), value))
            for page, paths in sorted(by_page.items())
        },
        referenced=sorted(
            referenced_assets, key=lambda value: (value.casefold(), value)
        ),
        unreferenced=sorted(unreferenced, key=lambda value: (value.casefold(), value)),
        expected_pages={
            asset: expected_page_for_asset(wiki, asset)
            for asset in sorted(
                unreferenced, key=lambda value: (value.casefold(), value)
            )
        },
        existing_paths=frozenset(asset_paths),
    )


def asset_relative_path(
    wiki_dir: Union[str, Path],
    reference: MediaReference,
) -> Optional[str]:
    target = (reference.page_path.parent / reference.target).resolve()
    wiki = Path(wiki_dir).resolve()
    try:
        rel = target.relative_to(wiki)
    except ValueError:
        return None
    return rel.as_posix()


def is_assets_path(path: str) -> bool:
    return Path(path).as_posix().split("/", 1)[0] == "assets"


def is_unrecognized_asset_warning_path(path: str) -> bool:
    rel = Path(path).as_posix()
    parts = rel.split("/")
    if any(part.startswith(".") for part in parts):
        return False
    if not is_assets_path(rel):
        return False
    if media_type_for_path(rel) is not None:
        return False
    return not _README_ASSET_RE.match(parts[-1])


def is_symlink_escape(
    wiki_dir: Union[str, Path],
    reference: MediaReference,
) -> bool:
    wiki_lexical = _absolute_normalized(Path(wiki_dir))
    target_lexical = _absolute_normalized(reference.page_path.parent / reference.target)
    try:
        target_lexical.relative_to(wiki_lexical)
    except ValueError:
        return False
    wiki_resolved = Path(wiki_dir).resolve()
    target_resolved = (reference.page_path.parent / reference.target).resolve()
    try:
        target_resolved.relative_to(wiki_resolved)
    except ValueError:
        return True
    return False


def _absolute_normalized(path: Path) -> Path:
    return Path(os.path.abspath(os.path.normpath(str(path))))


def expected_page_for_asset(
    wiki_dir: Union[str, Path],
    asset_rel: str,
) -> Optional[str]:
    parts = Path(asset_rel).as_posix().split("/")
    if len(parts) < 4 or parts[0] != "assets":
        return None
    page_rel = "/".join(parts[1:-1]) + ".md"
    if (Path(wiki_dir) / Path(page_rel)).is_file():
        return page_rel
    return None


def _read_pages(wiki: Path) -> dict[str, str]:
    pages: dict[str, str] = {}
    for page in sorted(wiki.rglob("*.md")):
        try:
            rel = page.relative_to(wiki).as_posix()
        except ValueError:
            continue
        pages[rel] = page.read_text(encoding="utf-8")
    return pages


def _asset_files(wiki: Path) -> list[str]:
    root = wiki / "assets"
    if not root.is_dir():
        return []
    paths = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(wiki).as_posix()
        if any(part.startswith(".") for part in rel.split("/")):
            continue
        paths.append(rel)
    return sorted(paths, key=lambda value: (value.casefold(), value))
