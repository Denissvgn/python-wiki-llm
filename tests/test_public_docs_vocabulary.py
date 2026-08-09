"""Executable policy for public documentation vocabulary and local links."""

from __future__ import annotations

import ast
import io
import json
import os
import posixpath
import re
import subprocess
import tarfile
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Iterable, Iterator, Mapping
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
_QUALIFICATION_SOURCE_ARCHIVE_ENV = (
    "LLM_WIKI_QUALIFICATION_SOURCE_ARCHIVE"
)
MARKDOWN = MarkdownIt("commonmark").enable(("strikethrough", "table"))
_PROSE_GAP = r"(?:[^\S\r\n]+|[^\S\r\n]*(?:\r\n?|\n)[^\S\r\n]*)"
_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_HTML_NUMBER = re.compile(
    r"-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
)
_DEFAULT_IGNORABLE_RANGES = (
    (0x034F, 0x034F),
    (0x115F, 0x1160),
    (0x17B4, 0x17B5),
    (0x180B, 0x180F),
    (0x2060, 0x206F),
    (0x3164, 0x3164),
    (0xFE00, 0xFE0F),
    (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8),
    (0x1BCA0, 0x1BCA3),
    (0x1D173, 0x1D17A),
    (0xE0000, 0xE0FFF),
)


@dataclass(frozen=True)
class ForbiddenProse:
    """One narrowly scoped internal-planning marker."""

    pattern: re.Pattern[str]
    rationale: str


FORBIDDEN_INTERNAL_PROSE: Mapping[str, ForbiddenProse] = {
    "delivery-stage-label": ForbiddenProse(
        re.compile(r"(?<!\w)M[0-9]+(?!\w)"),
        "Standalone M-number labels identify internal delivery stages.",
    ),
    "internal-task-id": ForbiddenProse(
        re.compile(
            r"(?<![\w-])"
            r"(?:KNOW|DL|NKC|PUB|SKL|SEC|ARC|KUX|VEC|HYG|DEC|QCP|CLX|M2MAIN)"
            r"-[0-9]+(?![\w-])"
        ),
        "These prefixes identify internal remediation or delivery tasks.",
    ),
    "priority-calibration-name": ForbiddenProse(
        re.compile(rf"\bP0{_PROSE_GAP}calibration\b"),
        "The public feature name is documentation calibration.",
    ),
    "shadow-pilot-claim": ForbiddenProse(
        re.compile(rf"\b[Ss]hadow{_PROSE_GAP}pilot\b"),
        "This phrase implies an internal evaluation that did not run.",
    ),
    "numbered-delivery-milestone": ForbiddenProse(
        re.compile(
            rf"\b(?:[Dd]elivery{_PROSE_GAP})?"
            rf"[Mm]ilestone{_PROSE_GAP}"
            rf"(?:\#(?:{_PROSE_GAP})?)?(?:[0-9]+|[IVX]+)\b"
        ),
        "Numbered milestone labels expose internal delivery sequencing.",
    ),
    "numbered-delivery-epic": ForbiddenProse(
        re.compile(
            rf"\b[Ee]pic{_PROSE_GAP}"
            rf"(?:\#(?:{_PROSE_GAP})?)?[0-9]+(?:\.[0-9]+)*\b"
        ),
        "Numbered epic labels expose internal delivery sequencing.",
    ),
    "closure-review": ForbiddenProse(
        re.compile(rf"\b[Cc]losure{_PROSE_GAP}review\b"),
        "This phrase identifies an internal completion checkpoint.",
    ),
}


# Add an entry only for an externally observable compatibility literal that
# cannot be removed. Keys must be exact literals and values must explain the
# public compatibility obligation; path, line, and whole-file exceptions are
# deliberately unsupported.
PUBLIC_LEGACY_IDENTIFIERS: Mapping[str, str] = {}
_SOURCE_IDENTITY_RULES = frozenset(
    {"delivery-stage-label", "internal-task-id"}
)
_SELECTED_SOURCE_INTERNAL_IDENTIFIER = re.compile(
    r"\b(?:KNOW|DL|NKC)-\d+\b|\bM\d+\b|"
    r"(?i:\bEpic\s+\d+(?:\.\d+)*\b)"
)
_RUNTIME_DOC_INTERNAL_PROSE = re.compile(
    r"\btests?\s*/\s*runners?\b",
    re.IGNORECASE,
)
_SOURCE_SELECTION_PAYLOAD = json.loads(
    (REPO_ROOT / ".llm-wiki/source-selection.json").read_text(
        encoding="utf-8"
    )
)
_SELECTED_SOURCE_INCLUDES = tuple(_SOURCE_SELECTION_PAYLOAD["include"])
_SELECTED_SOURCE_EXCLUDES = tuple(_SOURCE_SELECTION_PAYLOAD["exclude"])


def _is_selected_source_path(path: str) -> bool:
    """Return whether the committed profile selects a repository path."""

    def matches(root: str) -> bool:
        return path == root or path.startswith(f"{root}/")

    return any(matches(root) for root in _SELECTED_SOURCE_INCLUDES) and not any(
        matches(root) for root in _SELECTED_SOURCE_EXCLUDES
    )


@dataclass(frozen=True)
class PublicDocsFinding:
    path: str
    line: int
    rule: str
    detail: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.rule}: {self.detail}"


def _canonical_archive_member_name(member: tarfile.TarInfo) -> str:
    name = member.name
    parts = name.split("/")
    if (
        not name
        or "\0" in name
        or "\\" in name
        or re.match(r"^[A-Za-z]:", name)
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise AssertionError(
            f"unsafe source archive member path: {name!r}"
        )
    pure = PurePosixPath(name)
    if pure.is_absolute() or pure.as_posix() != name:
        raise AssertionError(
            f"non-canonical source archive member path: {name!r}"
        )
    return name


def _tracked_files_from_archive(archive_path: Path) -> tuple[str, ...]:
    tracked: list[str] = []
    seen: set[str] = set()
    with tarfile.open(archive_path, mode="r:") as archive:
        for member in archive:
            name = _canonical_archive_member_name(member)
            if name in seen:
                raise AssertionError(
                    f"duplicate source archive member path: {name!r}"
                )
            seen.add(name)
            if member.isdir():
                continue
            if not (member.isreg() or member.issym()):
                raise AssertionError(
                    "unsupported source archive member type for "
                    f"{name!r}"
                )
            tracked.append(name)
    return tuple(sorted(tracked))


def _tracked_files() -> tuple[str, ...]:
    archive_path = os.environ.get(_QUALIFICATION_SOURCE_ARCHIVE_ENV)
    if archive_path is not None:
        if not archive_path:
            raise AssertionError(
                f"{_QUALIFICATION_SOURCE_ARCHIVE_ENV} must not be empty"
            )
        return _tracked_files_from_archive(Path(archive_path))

    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    return tuple(
        path for path in result.stdout.decode("utf-8").split("\0") if path
    )


def _is_public_documentation_path(path: str) -> bool:
    pure = PurePosixPath(path)
    if path in {"README.md", "CHANGELOG.md", "SECURITY.md"}:
        return True
    if path.startswith("docs/") and pure.suffix == ".md":
        return True
    if (
        path.startswith("src/llm_wiki_cli/skills/")
        and pure.suffix == ".md"
    ):
        return True
    return path.startswith("examples/")


def public_documentation_files(
    tracked_files: Iterable[str] | None = None,
) -> tuple[str, ...]:
    """Return the deterministic tracked public-documentation scan set."""

    tracked = _tracked_files() if tracked_files is None else tuple(tracked_files)
    return tuple(
        sorted(path for path in tracked if _is_public_documentation_path(path))
    )


def _decode_public_text(path: str, raw: bytes) -> str | None:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        if path.startswith("examples/"):
            return None
        raise AssertionError(
            f"{path} is required public Markdown and must be UTF-8."
        ) from exc


def _mask_public_legacy_identifiers(text: str) -> str:
    chars = list(text)
    for literal in PUBLIC_LEGACY_IDENTIFIERS:
        start = 0
        while (index := text.find(literal, start)) != -1:
            for cursor in range(index, index + len(literal)):
                if chars[cursor] not in "\r\n":
                    chars[cursor] = " "
            start = index + len(literal)
    return "".join(chars)


def _srcset_destinations(value: str) -> Iterator[str]:
    """Yield URL tokens from an HTML srcset candidate list."""

    cursor = 0
    while cursor < len(value):
        while cursor < len(value) and (
            value[cursor].isspace() or value[cursor] == ","
        ):
            cursor += 1
        start = cursor
        while cursor < len(value) and not value[cursor].isspace():
            cursor += 1
        candidate = value[start:cursor].rstrip(",")
        if candidate:
            yield candidate
        if value[start:cursor].endswith(","):
            continue
        while cursor < len(value) and value[cursor] != ",":
            cursor += 1


class _HTMLText(HTMLParser):
    """Collect rendered text while discarding HTML tags and comments."""

    _BLOCK_BOUNDARIES = frozenset(
        {
            "address",
            "article",
            "aside",
            "base",
            "basefont",
            "blockquote",
            "body",
            "caption",
            "center",
            "col",
            "colgroup",
            "dd",
            "details",
            "dialog",
            "dir",
            "div",
            "dl",
            "dt",
            "fieldset",
            "figcaption",
            "figure",
            "footer",
            "form",
            "frame",
            "frameset",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "head",
            "header",
            "hr",
            "html",
            "iframe",
            "legend",
            "li",
            "link",
            "main",
            "menu",
            "menuitem",
            "nav",
            "noframes",
            "ol",
            "optgroup",
            "option",
            "p",
            "param",
            "pre",
            "search",
            "section",
            "script",
            "style",
            "summary",
            "table",
            "tbody",
            "td",
            "tfoot",
            "th",
            "thead",
            "title",
            "tr",
            "track",
            "ul",
        }
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.visible_attributes: list[str] = []
        self.comments: list[str] = []
        self.destinations: list[tuple[int, str]] = []
        self._textarea_placeholders: list[int | None] = []
        self._textarea_at_start: list[bool] = []
        self._preformatted_depth = 0
        self._suppress_break_whitespace = False

    def handle_data(self, data: str) -> None:
        if self._suppress_break_whitespace:
            data = re.sub(r"^[\t\n\f\r ]+", "", data)
            self._suppress_break_whitespace = False
        if self._textarea_at_start and self._textarea_at_start[-1]:
            if data.startswith("\r\n"):
                data = data[2:]
            elif data.startswith(("\r", "\n")):
                data = data[1:]
            self._textarea_at_start[-1] = False
        if self._textarea_placeholders and data:
            placeholder_index = self._textarea_placeholders[-1]
            if placeholder_index is not None:
                self.parts[placeholder_index] = ""
                self._textarea_placeholders[-1] = None
        self.parts.append(data)

    def handle_comment(self, data: str) -> None:
        self.comments.append(data)

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        normalized_tag = tag.casefold()
        if self._textarea_placeholders:
            self.handle_data(self.get_starttag_text() or f"<{tag}>")
            return
        attribute_values: dict[str, str] = {}
        for name, value in attrs:
            if value is not None:
                attribute_values.setdefault(name.casefold(), value)
        inline_attributes: set[str] = set()
        if normalized_tag == "img" and "alt" in attribute_values:
            self._suppress_break_whitespace = False
            self.parts.append(attribute_values["alt"])
            inline_attributes.add("alt")
        elif normalized_tag == "input":
            input_type = attribute_values.get("type", "text").casefold()
            known_input_types = {
                "button",
                "checkbox",
                "color",
                "date",
                "datetime-local",
                "email",
                "file",
                "hidden",
                "image",
                "month",
                "number",
                "password",
                "radio",
                "range",
                "reset",
                "search",
                "submit",
                "tel",
                "text",
                "time",
                "url",
                "week",
            }
            if input_type not in known_input_types:
                input_type = "text"
            raw_value = attribute_values.get("value", "")
            value_is_empty = not raw_value or (
                input_type == "number"
                and _HTML_NUMBER.fullmatch(raw_value) is None
            )
            if input_type == "image" and "alt" in attribute_values:
                self._suppress_break_whitespace = False
                self.parts.append(attribute_values["alt"])
                inline_attributes.add("alt")
            elif input_type not in {
                "checkbox",
                "color",
                "date",
                "datetime-local",
                "file",
                "hidden",
                "image",
                "month",
                "number",
                "password",
                "radio",
                "range",
                "time",
                "week",
            } and attribute_values.get("value"):
                self._suppress_break_whitespace = False
                self.parts.append(attribute_values["value"])
                inline_attributes.add("value")
            elif input_type in {
                "email",
                "number",
                "password",
                "search",
                "tel",
                "text",
                "url",
            } and value_is_empty and attribute_values.get("placeholder"):
                self._suppress_break_whitespace = False
                self.parts.append(attribute_values["placeholder"])
                inline_attributes.add("placeholder")
        elif normalized_tag == "textarea":
            self._suppress_break_whitespace = False
            placeholder = attribute_values.get("placeholder")
            self.parts.append(placeholder or "")
            self._textarea_placeholders.append(len(self.parts) - 1)
            self._textarea_at_start.append(True)
            inline_attributes.add("placeholder")
        if normalized_tag in {"listing", "pre", "xmp"}:
            self._preformatted_depth += 1
        if normalized_tag in self._BLOCK_BOUNDARIES:
            self.parts.append("\0")
        elif normalized_tag == "br":
            self.parts.append("\n")
            self._suppress_break_whitespace = self._preformatted_depth == 0
        seen_attributes: set[str] = set()
        for name, value in attrs:
            attribute = name.casefold()
            if attribute in seen_attributes:
                continue
            seen_attributes.add(attribute)
            is_visible_attribute = (
                attribute in {"aria-description", "aria-label", "title"}
                or (
                    attribute == "alt"
                    and normalized_tag == "area"
                )
                or (
                    attribute == "label"
                    and normalized_tag
                    in {"menuitem", "optgroup", "option", "track"}
                )
                or (
                    attribute == "placeholder"
                    and normalized_tag == "textarea"
                )
            )
            if (
                value is not None
                and is_visible_attribute
                and attribute not in inline_attributes
            ):
                self.visible_attributes.append(value)
            is_url_attribute = attribute in {
                "href",
                "src",
                "xlink:href",
            } or (
                (normalized_tag == "object" and attribute == "data")
                or (normalized_tag == "video" and attribute == "poster")
            )
            if value is not None and is_url_attribute:
                self.destinations.append((self.getpos()[0], value))
            elif (
                value is not None
                and normalized_tag in {"img", "source"}
                and attribute == "srcset"
            ):
                self.destinations.extend(
                    (self.getpos()[0], destination)
                    for destination in _srcset_destinations(value)
                )

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.casefold()
        if self._textarea_placeholders and normalized_tag != "textarea":
            self.handle_data(f"</{tag}>")
            return
        if normalized_tag == "textarea" and self._textarea_placeholders:
            self._textarea_placeholders.pop()
            self._textarea_at_start.pop()
        if normalized_tag in self._BLOCK_BOUNDARIES:
            self.parts.append("\0")
        if (
            normalized_tag in {"listing", "pre", "xmp"}
            and self._preformatted_depth
        ):
            self._preformatted_depth -= 1

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if self._textarea_placeholders:
            self.handle_data(self.get_starttag_text() or f"<{tag}/>")
            return
        super().handle_startendtag(tag, attrs)

    def discard_unclosed_textarea_placeholders(self) -> None:
        for placeholder_index in self._textarea_placeholders:
            if placeholder_index is not None:
                self.parts[placeholder_index] = ""


def _parse_html(
    source: str,
    *,
    rendered_fragment: bool = False,
) -> _HTMLText:
    parser = _HTMLText()
    parser.feed(source)
    parser.close()
    if rendered_fragment:
        parser.discard_unclosed_textarea_placeholders()
    return parser


def _html_semantics(
    source: str,
    *,
    rendered_fragment: bool = False,
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    parser = _parse_html(source, rendered_fragment=rendered_fragment)
    return (
        "".join(parser.parts),
        tuple(parser.visible_attributes),
        tuple(parser.comments),
    )


def _html_destinations(source: str) -> tuple[tuple[int, str], ...]:
    return tuple(_parse_html(source).destinations)


def _render_inline(
    children: Iterable[object],
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    rendered_html = MARKDOWN.renderer.renderInline(
        tuple(children),
        MARKDOWN.options,
        {},
    )
    return _html_semantics(rendered_html, rendered_fragment=True)


def _semantic_markdown_segments(text: str) -> Iterator[tuple[int, str]]:
    """Yield rendered prose/code segments without presentation-only markup."""

    environment: dict[str, object] = {}
    for token in MARKDOWN.parse(text, environment):
        if token.type == "inline":
            rendered, attributes, comments = _render_inline(
                token.children or ()
            )
            line = (token.map or [0])[0] + 1
            if rendered:
                yield line, rendered
            for attribute in attributes:
                yield line, attribute
            for comment in comments:
                yield line, comment
        elif token.type in {"code_block", "fence"}:
            line = (token.map or [0])[0] + (2 if token.type == "fence" else 1)
            yield line, token.content
        elif token.type == "html_block":
            line = (token.map or [0])[0] + 1
            rendered, attributes, comments = _html_semantics(token.content)
            if rendered:
                yield line, rendered
            for attribute in attributes:
                yield line, attribute
            for comment in comments:
                yield line, comment

    references = environment.get("references", {})
    if isinstance(references, dict):
        for reference in references.values():
            if not isinstance(reference, dict) or not reference.get("title"):
                continue
            source_map = reference.get("map", [0])
            yield int(source_map[0]) + 1, str(reference["title"])


def _without_invisible_formatting(text: str) -> str:
    return "".join(
        character
        for character in text
        if unicodedata.category(character) != "Cf"
        and not any(
            start <= ord(character) <= end
            for start, end in _DEFAULT_IGNORABLE_RANGES
        )
    )


def _identity_is_embedded_in_unicode_word(
    text: str,
    match: re.Match[str],
) -> bool:
    adjacent = (
        text[match.start() - 1] if match.start() else "",
        text[match.end()] if match.end() < len(text) else "",
    )
    return any(
        character and unicodedata.category(character).startswith("M")
        for character in adjacent
    )


def scan_internal_prose(
    text: str,
    *,
    path: str = "snippet.md",
) -> list[PublicDocsFinding]:
    """Find unambiguous internal-planning prose in one public text."""

    candidate = _mask_public_legacy_identifiers(text)
    findings: dict[tuple[int, str, str], PublicDocsFinding] = {}

    def record(line: int, rule: str, match: re.Match[str]) -> None:
        forbidden = FORBIDDEN_INTERNAL_PROSE[rule]
        finding = PublicDocsFinding(
            path=path,
            line=line,
            rule=rule,
            detail=(
                f"{match.group(0)!r} is internal prose. "
                f"{forbidden.rationale}"
            ),
        )
        findings.setdefault((line, rule, match.group(0)), finding)

    source_candidate = unicodedata.normalize(
        "NFC",
        _without_invisible_formatting(candidate),
    )
    for rule in _SOURCE_IDENTITY_RULES:
        forbidden = FORBIDDEN_INTERNAL_PROSE[rule]
        for match in forbidden.pattern.finditer(source_candidate):
            if _identity_is_embedded_in_unicode_word(source_candidate, match):
                continue
            record(
                source_candidate.count("\n", 0, match.start()) + 1,
                rule,
                match,
            )

    for base_line, rendered_segment in _semantic_markdown_segments(candidate):
        segment = unicodedata.normalize(
            "NFC",
            _without_invisible_formatting(rendered_segment),
        )
        for rule, forbidden in FORBIDDEN_INTERNAL_PROSE.items():
            for match in forbidden.pattern.finditer(segment):
                if (
                    rule in _SOURCE_IDENTITY_RULES
                    and _identity_is_embedded_in_unicode_word(segment, match)
                ):
                    continue
                record(
                    base_line + segment.count("\n", 0, match.start()),
                    rule,
                    match,
                )
    return sorted(
        findings.values(),
        key=lambda finding: (finding.line, finding.rule, finding.detail),
    )


def _markdown_link_destinations(text: str) -> Iterator[tuple[int, str]]:
    """Yield destinations recognized by the CommonMark parser."""

    environment: dict[str, object] = {}
    tokens = MARKDOWN.parse(text, environment)
    destinations: dict[str, int] = {}

    references = environment.get("references", {})
    if isinstance(references, dict):
        for reference in references.values():
            if not isinstance(reference, dict):
                continue
            destination = reference.get("href")
            source_map = reference.get("map", [0])
            if isinstance(destination, str):
                destinations.setdefault(destination, int(source_map[0]) + 1)

    for token in tokens:
        if token.type == "html_block":
            line = (token.map or [0])[0] + 1
            for relative_line, destination in _html_destinations(token.content):
                destinations.setdefault(
                    destination,
                    line + relative_line - 1,
                )
            continue
        if token.type != "inline":
            continue
        line = (token.map or [0])[0] + 1
        for child in token.children or ():
            attribute = (
                "href"
                if child.type == "link_open"
                else "src"
                if child.type == "image"
                else None
            )
            if attribute and (destination := child.attrGet(attribute)):
                destinations.setdefault(destination, line)
            elif child.type == "html_inline":
                for _, destination in _html_destinations(child.content):
                    destinations.setdefault(destination, line)

    yield from sorted(
        ((line, destination) for destination, line in destinations.items()),
        key=lambda item: (item[0], item[1]),
    )


def _fully_unquote(value: str) -> str:
    while True:
        decoded = unquote(value)
        if decoded == value:
            return value
        value = decoded


@dataclass(frozen=True)
class _LocalDestination:
    path: str
    requires_directory: bool


def _normalize_local_destination(
    source_path: str,
    destination: str,
) -> _LocalDestination | None:
    value = destination.strip()
    if not value or value.startswith("#"):
        return None
    if value.startswith("//") or _URI_SCHEME.match(value):
        return None

    parsed = urlsplit(value)
    path = _fully_unquote(parsed.path).replace("\\", "/")
    if not path:
        return None
    absolute = path.startswith("/")
    if absolute:
        combined = path.lstrip("/")
        normalized = posixpath.normpath(path).lstrip("/") or "."
    else:
        combined = posixpath.join(posixpath.dirname(source_path), path)
        normalized = posixpath.normpath(combined).removeprefix("./")
    final_component = path.rstrip("/").rsplit("/", 1)[-1]
    requires_directory = path.endswith("/") or final_component in {".", ".."}

    return _LocalDestination(normalized, requires_directory)


def scan_markdown_links(
    text: str,
    *,
    path: str,
    tracked_files: Iterable[str],
    root: Path | None = None,
) -> list[PublicDocsFinding]:
    """Reject ignored-report, repository-escape, and untracked local links."""

    tracked = set(tracked_files)
    findings: list[PublicDocsFinding] = []
    for line, destination in _markdown_link_destinations(text):
        local = _normalize_local_destination(path, destination)
        if local is None:
            continue
        normalized = local.path
        if normalized == ".." or normalized.startswith("../"):
            findings.append(
                PublicDocsFinding(
                    path,
                    line,
                    "local-link-outside-repository",
                    f"{destination!r} resolves outside the repository.",
                )
            )
            continue
        if normalized == "reports" or normalized.startswith("reports/"):
            findings.append(
                PublicDocsFinding(
                    path,
                    line,
                    "ignored-internal-report-link",
                    f"{destination!r} resolves into the ignored reports tree.",
                )
            )
            continue
        tracked_directory = normalized == "." or any(
            candidate.startswith(normalized.rstrip("/") + "/")
            for candidate in tracked
        )
        target_is_tracked = normalized in tracked or tracked_directory
        target_exists = root is None or (
            (root / normalized).is_dir()
            if local.requires_directory
            else (root / normalized).exists()
        )
        if (
            not target_is_tracked
            or not target_exists
            or (local.requires_directory and not tracked_directory)
        ):
            findings.append(
                PublicDocsFinding(
                    path,
                    line,
                    "missing-or-untracked-local-link",
                    f"{destination!r} resolves to untracked target {normalized!r}.",
                )
            )
    return findings


def scan_public_document(
    text: str,
    *,
    path: str,
    tracked_files: Iterable[str],
    root: Path | None = None,
) -> list[PublicDocsFinding]:
    findings = scan_internal_prose(text, path=path)
    if path.endswith(".md"):
        findings.extend(
            scan_markdown_links(
                text,
                path=path,
                tracked_files=tracked_files,
                root=root,
            )
        )
    return sorted(findings, key=lambda finding: (finding.line, finding.rule))


def _write_inventory_test_archive(
    path: Path,
    members: Iterable[tuple[str, str]],
) -> None:
    with tarfile.open(path, mode="w") as archive:
        for name, kind in members:
            member = tarfile.TarInfo(name)
            if kind == "directory":
                member.type = tarfile.DIRTYPE
                archive.addfile(member)
            elif kind == "file":
                payload = b"tracked\n"
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
            elif kind == "symlink":
                member.type = tarfile.SYMTYPE
                member.linkname = "guide.md"
                archive.addfile(member)
            elif kind == "hardlink":
                member.type = tarfile.LNKTYPE
                member.linkname = "README.md"
                archive.addfile(member)
            else:
                raise AssertionError(f"unsupported test member kind: {kind}")


def test_archive_inventory_matches_git_file_semantics_and_posix_spelling(
    tmp_path,
):
    archive_path = tmp_path / "candidate-source.tar"
    _write_inventory_test_archive(
        archive_path,
        (
            ("docs", "directory"),
            ("docs/guide.md", "file"),
            ("README.md", "file"),
            ("docs/current.md", "symlink"),
        ),
    )

    tracked = _tracked_files_from_archive(archive_path)

    assert tracked == (
        "README.md",
        "docs/current.md",
        "docs/guide.md",
    )
    assert all("\\" not in path for path in tracked)


def test_qualification_archive_inventory_never_invokes_git(
    tmp_path,
    monkeypatch,
):
    archive_path = tmp_path / "candidate-source.tar"
    _write_inventory_test_archive(
        archive_path,
        (
            ("docs", "directory"),
            ("README.md", "file"),
            ("docs/guide.md", "file"),
        ),
    )
    monkeypatch.setenv(
        _QUALIFICATION_SOURCE_ARCHIVE_ENV,
        str(archive_path),
    )

    def fail_if_git_runs(*_args, **_kwargs):
        pytest.fail("archive inventory must not invoke Git")

    monkeypatch.setattr(subprocess, "run", fail_if_git_runs)

    assert _tracked_files() == ("README.md", "docs/guide.md")


def test_tracked_inventory_preserves_git_ls_files_fallback(monkeypatch):
    monkeypatch.delenv(_QUALIFICATION_SOURCE_ARCHIVE_ENV, raising=False)
    calls = []

    def fake_run(command, *, cwd, check, capture_output):
        calls.append((command, cwd, check, capture_output))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=b"README.md\0docs/guide.md\0",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert _tracked_files() == ("README.md", "docs/guide.md")
    assert calls == [
        (["git", "ls-files", "-z"], REPO_ROOT, True, True)
    ]


@pytest.mark.parametrize(
    "member_name",
    [
        "/README.md",
        "../README.md",
        "docs/../README.md",
        r"docs\guide.md",
        "docs//guide.md",
        "docs/./guide.md",
        "C:/README.md",
    ],
)
def test_archive_inventory_rejects_unsafe_or_noncanonical_names(
    tmp_path,
    member_name,
):
    archive_path = tmp_path / "candidate-source.tar"
    _write_inventory_test_archive(
        archive_path,
        ((member_name, "file"),),
    )

    with pytest.raises(AssertionError, match="archive member path"):
        _tracked_files_from_archive(archive_path)


def test_archive_inventory_rejects_duplicate_names(tmp_path):
    archive_path = tmp_path / "candidate-source.tar"
    _write_inventory_test_archive(
        archive_path,
        (
            ("README.md", "file"),
            ("README.md", "file"),
        ),
    )

    with pytest.raises(AssertionError, match="duplicate source archive"):
        _tracked_files_from_archive(archive_path)


def test_archive_inventory_rejects_non_file_member_types(tmp_path):
    archive_path = tmp_path / "candidate-source.tar"
    _write_inventory_test_archive(
        archive_path,
        (("README-hardlink.md", "hardlink"),),
    )

    with pytest.raises(AssertionError, match="unsupported source archive"):
        _tracked_files_from_archive(archive_path)


@pytest.mark.parametrize(
    ("snippet", "rule"),
    [
        ("The M4 stage expanded the graph.", "delivery-stage-label"),
        ("Complete PUB-008 before release.", "internal-task-id"),
        ("Complete PUB&#45;008 before release.", "internal-task-id"),
        ("P0 calibration is now complete.", "priority-calibration-name"),
        ("P0 cali&#98;ration is now complete.", "priority-calibration-name"),
        ("Run a shadow pilot first.", "shadow-pilot-claim"),
        ("Milestone 4 adds governance.", "numbered-delivery-milestone"),
        ("Milestone #4 adds governance.", "numbered-delivery-milestone"),
        ("Delivery milestone #\nIV is next.", "numbered-delivery-milestone"),
        ("Epic 2 adds dependency analysis.", "numbered-delivery-epic"),
        ("Epic 2.4 adds aggregation.", "numbered-delivery-epic"),
        ("Epic\n2.4 adds aggregation.", "numbered-delivery-epic"),
        ("Start the closure review.", "closure-review"),
        ("P0\ncalibration is now complete.", "priority-calibration-name"),
        ("P0  \ncalibration is now complete.", "priority-calibration-name"),
        ("P0\\\ncalibration is now complete.", "priority-calibration-name"),
        ("Run a shadow\n  pilot first.", "shadow-pilot-claim"),
        ("Delivery\nmilestone IV is next.", "numbered-delivery-milestone"),
        ("Start the closure\treview.", "closure-review"),
        ("P0 *calibration* is now complete.", "priority-calibration-name"),
        ("P0 ~~calibration~~ is now complete.", "priority-calibration-name"),
        ("![P0 *calibration*](image.png)", "priority-calibration-name"),
        ("P0<br>calibration is now complete.", "priority-calibration-name"),
        (
            "<div>P0<br>\ncalibration</div>",
            "priority-calibration-name",
        ),
        ("Run a shadow<br/>pilot first.", "shadow-pilot-claim"),
        (
            '<span title="P0 calibration">public</span>',
            "priority-calibration-name",
        ),
        ('<img alt="P0 calibration">', "priority-calibration-name"),
        (
            '<button aria-label="shadow pilot">x</button>',
            "shadow-pilot-claim",
        ),
        (
            'P0 <span title="tooltip">calibration</span>',
            "priority-calibration-name",
        ),
        (
            'Run a shadow <span aria-label="note">pilot</span> first.',
            "shadow-pilot-claim",
        ),
        (
            'P0 <img alt="calibration" src="https://example.com/image.png">',
            "priority-calibration-name",
        ),
        (
            'Run a shadow <img alt="pilot" src="https://example.com/image.png">',
            "shadow-pilot-claim",
        ),
        (
            'P0 <input type="image" alt="calibration" src="image.png">',
            "priority-calibration-name",
        ),
        (
            'P0 <input type="submit" value="calibration">',
            "priority-calibration-name",
        ),
        (
            'P0 <textarea placeholder="calibration"></textarea>',
            "priority-calibration-name",
        ),
        (
            'P0 <textarea placeholder="calibration">\n</textarea>',
            "priority-calibration-name",
        ),
        (
            'P0 <input type="unknown" placeholder="calibration">',
            "priority-calibration-name",
        ),
        (
            'P0 <input type=" text " placeholder="calibration">',
            "priority-calibration-name",
        ),
        (
            'P0 <input type=" hidden " value="calibration">',
            "priority-calibration-name",
        ),
        (
            'P0 <input type="number" value="invalid" '
            'placeholder="calibration">',
            "priority-calibration-name",
        ),
        ("Run a shadow **pilot** first.", "shadow-pilot-claim"),
        ("> P0\n> calibration is complete.", "priority-calibration-name"),
        ("`Complete PUB-008 before release.`", "internal-task-id"),
        ("```\nM4\n```", "delivery-stage-label"),
        ("<!-- Complete PUB-008 before release. -->", "internal-task-id"),
        ("<!-- P0 calibration -->", "priority-calibration-name"),
        ("M&#x200B;4", "delivery-stage-label"),
        ("PUB&ZeroWidthSpace;-008", "internal-task-id"),
        ("P0 cali&shy;bration", "priority-calibration-name"),
        ("shadow pi&#x200B;lot", "shadow-pilot-claim"),
        ("closure re&#xfeff;view", "closure-review"),
        ("M\u034f4", "delivery-stage-label"),
        ("M\ufe0f4", "delivery-stage-label"),
        ("M\u180b4", "delivery-stage-label"),
        ("M\U000e01004", "delivery-stage-label"),
        ("M\u20654", "delivery-stage-label"),
        ("M\ufff04", "delivery-stage-label"),
        (
            '<span aria-description="P0 calibration">x</span>',
            "priority-calibration-name",
        ),
        ('<option label="P0 calibration">Public</option>', "priority-calibration-name"),
        ('<track label="shadow pilot">', "shadow-pilot-claim"),
        (
            '<img alt="P0 calibration" alt="safe" '
            'src="https://example.com/image.png">',
            "priority-calibration-name",
        ),
        (
            '<input type="submit" value="P0 calibration" value="safe">',
            "priority-calibration-name",
        ),
        ("M4\0", "delivery-stage-label"),
    ],
)
def test_internal_prose_scanner_rejects_delivery_vocabulary(snippet, rule):
    findings = scan_internal_prose(snippet)

    assert [finding.rule for finding in findings] == [rule]


@pytest.mark.parametrize(
    "snippet",
    [
        "Keep the remainder backlog in `bootstrap-remainder.md`.",
        "Use P0, P1, and P2 as public content priorities.",
        "A pilot can establish a milestone before ordinary project closure.",
        "Write the generated report to reports/dep_vuln_triage_<date>.md.",
        "The protocol remains `llm-wiki-p0-calibration-run/v1`.",
        "- P0\n- calibration\n",
        "| left | right |\n|---|---|\n| P0 | calibration |\n",
        "xPUB-008y is an external identifier.",
        "x\u200bPUB-008 is an embedded identifier.",
        "x\u00adM4 is an embedded identifier.",
        "`some_PUB-008_name` is an embedded identifier.",
        "éPUB-008é is an embedded identifier.",
        "e\u0301PUB-008 is an embedded identifier.",
        "αM4β is an embedded identifier.",
        "α\u0301M4 is an embedded identifier.",
        "<p>P0</p><p>calibration</p>",
        "<center>P0</center>\n<center>calibration</center>",
        "<div>PUB&amp;#45;008</div>",
        "<div>P0&amp;#32;calibration</div>",
        "<pre>P0\n\ncalibration</pre>",
        "<pre>P0<br>\ncalibration</pre>",
        "<textarea>P0\n\ncalibration</textarea>",
        "<textarea>P0<br>\ncalibration</textarea>",
        "![P0<br>calibration](image.png)",
        '![<span title="P0 calibration">x</span>](image.png)',
        '<div value="P0 calibration" label="shadow pilot">public</div>',
        '<button value="P0 calibration">Public</button>',
        '<input type="hidden" value="P0 calibration">',
        '<input type="number" value="P0 calibration">',
        '<input type="date" value="P0 calibration">',
        '<img alt="safe" alt="P0 calibration" src="image.png">',
        (
            'P0 <textarea placeholder="calibration">'
            "visible value</textarea>"
        ),
        'P0 <textarea placeholder="calibration">\n\n</textarea>',
        'P0 <input value="visible" placeholder="calibration">',
        'P0 cali<img alt="icon" src="https://example.com/image.png">bration',
        'Start closure <input value="x">review.',
    ],
)
def test_internal_prose_scanner_preserves_public_product_language(snippet):
    assert scan_internal_prose(snippet) == []


def test_full_scanner_preserves_plain_text_generated_report_path():
    findings = scan_public_document(
        "Write the generated artifact to reports/dep_vuln_triage_<date>.md.",
        path="docs/guide.md",
        tracked_files={"docs/guide.md"},
    )

    assert findings == []


@pytest.mark.parametrize(
    "destination",
    [
        "../reports/private.md",
        "../%72eports/private.md",
        "../%2572eports/private.md",
        "../%2525252572eports/private.md",
        r"..\reports\private.md",
        "../&#x72;eports/private.md",
        "..&#47;reports/private.md",
        "../reports/`private`.md",
        "../reports/foo<!--x-->bar.md",
    ],
)
def test_link_scanner_rejects_normalized_internal_report_targets(destination):
    findings = scan_markdown_links(
        f"[internal review]({destination})",
        path="docs/guide.md",
        tracked_files={"docs/guide.md"},
    )

    assert [finding.rule for finding in findings] == [
        "ignored-internal-report-link"
    ]


@pytest.mark.parametrize(
    "text",
    [
        "> > [internal](../reports/private.md)\n",
        "- - [internal](../reports/private.md)\n",
        "- > [internal](../reports/private.md)\n",
        "> - [internal](../reports/private.md)\n",
        "Paragraph\n+ \n    [internal](../reports/private.md)\n",
        "Paragraph\n1. \n    [internal](../reports/private.md)\n",
        "See the internal review\n    [internal](../reports/private.md)\n",
        "[read\nmore](../reports/private.md)",
        "[internal](\n  ../reports/private.md\n)",
    ],
)
def test_link_scanner_validates_live_commonmark_links(text):
    findings = scan_markdown_links(
        text,
        path="docs/guide.md",
        tracked_files={"docs/guide.md"},
    )

    assert [finding.rule for finding in findings] == [
        "ignored-internal-report-link"
    ]


def test_link_scanner_rejects_missing_target_and_accepts_tracked_links():
    tracked = {
        "README.md",
        "docs/guide.md",
        "docs/reference.md",
        "docs/reference(v1).md",
    }
    text = "\n".join(
        [
            "[reference](reference.md#details)",
            '[parenthesized](reference(v1).md "Reference")',
            "[root](../README.md)",
            "[external](https://example.com/docs)",
            "[missing](missing.md)",
            "`[example](not-real.md)`",
            "```markdown",
            "[placeholder](also-not-real.md)",
            "```",
        ]
    )

    findings = scan_markdown_links(
        text,
        path="docs/guide.md",
        tracked_files=tracked,
    )

    assert len(findings) == 1
    assert findings[0].rule == "missing-or-untracked-local-link"
    assert "'missing.md'" in findings[0].detail


@pytest.mark.parametrize(
    ("text", "rule"),
    [
        (
            '<a href="../reports/private.md">internal</a>',
            "ignored-internal-report-link",
        ),
        ('<img src="missing.png" alt="missing">', "missing-or-untracked-local-link"),
        (
            "<div>\n<a href=\"../reports/private.md\">internal</a>\n</div>",
            "ignored-internal-report-link",
        ),
        (
            '<img srcset="../reports/private.png 2x" alt="private">',
            "ignored-internal-report-link",
        ),
        (
            '<video poster="../reports/private.png"></video>',
            "ignored-internal-report-link",
        ),
        (
            '<object data="../reports/private.pdf"></object>',
            "ignored-internal-report-link",
        ),
        (
            '<svg><a xlink:href="../reports/private.md">private</a></svg>',
            "ignored-internal-report-link",
        ),
    ],
)
def test_link_scanner_validates_raw_html_destinations(text, rule):
    findings = scan_markdown_links(
        text,
        path="docs/guide.md",
        tracked_files={"docs/guide.md"},
    )

    assert [finding.rule for finding in findings] == [rule]


@pytest.mark.parametrize(
    "destination",
    [
        "missing%3Athing.md",
        "reference.md%23details",
        "reference.md%3Fmode=missing",
    ],
)
def test_encoded_reserved_characters_remain_part_of_the_local_path(destination):
    findings = scan_markdown_links(
        f"[missing]({destination})",
        path="docs/guide.md",
        tracked_files={"docs/guide.md", "docs/reference.md"},
    )

    assert [finding.rule for finding in findings] == [
        "missing-or-untracked-local-link"
    ]


@pytest.mark.parametrize(
    "text",
    [
        "    [placeholder](missing.md)\n",
        "-     [placeholder](missing.md)\n",
        "1.     [placeholder](missing.md)\n",
        "Heading\n-\n    [placeholder](missing.md)\n",
        "```markdown\n[placeholder](missing.md)\n```\n",
        "<!-- [placeholder](missing.md) -->",
        '<span title="[placeholder](missing.md)">text</span>',
        "<script>\n[placeholder](missing.md)\n</script>\n",
        "<div>\n[placeholder](missing.md)\n</div>\n",
    ],
)
def test_link_scanner_ignores_non_link_commonmark_contexts(text):
    assert (
        scan_markdown_links(
            text,
            path="docs/guide.md",
            tracked_files={"docs/guide.md"},
        )
        == []
    )


@pytest.mark.parametrize(
    "text",
    [
        "[private]: ../reports/private.md\n",
        "[private]:\n  ../reports/private.md\n",
        "> [private]: ../reports/private.md\n",
        "- [private]: ../reports/private.md\n",
        "# Heading\n[private]: ../reports/private.md\n",
        "<!-- comment -->\n[private]: ../reports/private.md\n",
    ],
)
def test_link_scanner_validates_reference_definitions(text):
    findings = scan_markdown_links(
        text,
        path="docs/guide.md",
        tracked_files={"docs/guide.md"},
    )

    assert [finding.rule for finding in findings] == [
        "ignored-internal-report-link"
    ]


@pytest.mark.parametrize(
    "text",
    [
        r"[not closed\](missing.md)",
        "[invalid](missing.md extra garbage)",
        "[notref]: ../reports/private.md extra garbage\n",
        "Ordinary prose\n[notref]: ../reports/private.md\n",
        "[   ]: ../reports/private.md\n",
    ],
)
def test_link_scanner_ignores_invalid_link_forms(text):
    assert (
        scan_markdown_links(
            text,
            path="docs/guide.md",
            tracked_files={"docs/guide.md"},
        )
        == []
    )


def test_link_scanner_rejects_tracked_but_missing_target(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("", encoding="utf-8")

    findings = scan_markdown_links(
        "[missing](reference.md)",
        path="docs/guide.md",
        tracked_files={"docs/guide.md", "docs/reference.md"},
        root=tmp_path,
    )

    assert [finding.rule for finding in findings] == [
        "missing-or-untracked-local-link"
    ]


@pytest.mark.parametrize(
    "destination",
    [
        "../README.md/",
        "native-knowledge.md/",
        "native-knowledge.md/.",
    ],
)
def test_link_scanner_rejects_file_as_directory_paths(destination):
    findings = scan_markdown_links(
        f"[invalid]({destination})",
        path="docs/guide.md",
        tracked_files={
            "README.md",
            "docs/guide.md",
            "docs/native-knowledge.md",
        },
        root=REPO_ROOT,
    )

    assert [finding.rule for finding in findings] == [
        "missing-or-untracked-local-link"
    ]


@pytest.mark.parametrize(
    ("text", "path"),
    [
        ("[repository root](..)", "docs/guide.md"),
        ("[repository root](.)", "README.md"),
        ("[repository root](/)", "docs/guide.md"),
    ],
)
def test_link_scanner_accepts_repository_root_directory(text, path):
    assert (
        scan_markdown_links(
            text,
            path=path,
            tracked_files={"README.md", "docs/guide.md"},
            root=REPO_ROOT,
        )
        == []
    )


@pytest.mark.parametrize(
    "text",
    [
        "[absolute clamped path](/../README.md)",
        "[normalized directory](../README.md/../docs)",
        "[normalized file](native-knowledge.md/../standalone-documentation.md)",
    ],
)
def test_link_scanner_accepts_url_dot_segment_normalization(text):
    assert (
        scan_markdown_links(
            text,
            path="docs/guide.md",
            tracked_files={
                "README.md",
                "docs/guide.md",
                "docs/native-knowledge.md",
                "docs/standalone-documentation.md",
            },
            root=REPO_ROOT,
        )
        == []
    )


def test_public_text_decoding_fails_closed_for_required_markdown():
    with pytest.raises(AssertionError, match="must be UTF-8"):
        _decode_public_text("docs/guide.md", b"\xff")

    assert _decode_public_text("examples/image.bin", b"\xff") is None
    assert _decode_public_text("README.md", b"M4\0") == "M4\0"


def test_scan_set_is_tracked_and_excludes_internal_reports():
    tracked = _tracked_files()
    scanned = public_documentation_files(tracked)

    assert "README.md" in scanned
    assert "CHANGELOG.md" in scanned
    assert "SECURITY.md" in scanned
    assert "docs/native-knowledge.md" in scanned
    assert "src/llm_wiki_cli/skills/agent-docs/SKILL.md" in scanned
    assert any(path.startswith("examples/") for path in scanned)
    assert all(path in tracked for path in scanned)
    assert not any(path.startswith("reports/") for path in scanned)


def test_tracked_public_documentation_has_no_internal_vocabulary_or_dead_links():
    tracked = _tracked_files()
    findings: list[PublicDocsFinding] = []
    for path in public_documentation_files(tracked):
        raw = (REPO_ROOT / path).read_bytes()
        text = _decode_public_text(path, raw)
        if text is None:
            continue
        findings.extend(
            scan_public_document(
                text,
                path=path,
                tracked_files=tracked,
                root=REPO_ROOT,
            )
        )

    assert not findings, "\n" + "\n".join(
        finding.render() for finding in findings
    )


def test_selected_source_has_no_internal_delivery_identifiers():
    """Keep source-derived public pages free of development identifiers."""

    findings: list[str] = []
    for path in _tracked_files():
        if not _is_selected_source_path(path):
            continue
        text = (REPO_ROOT / path).read_text(encoding="utf-8")
        for match in _SELECTED_SOURCE_INTERNAL_IDENTIFIER.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{path}:{line}: {match.group(0)!r}")

    assert not findings, "\n" + "\n".join(findings)


def test_selected_python_docstrings_have_no_test_runner_prose():
    """Reject development-harness language from extracted descriptions."""

    findings: list[str] = []
    for path in _tracked_files():
        if not (_is_selected_source_path(path) and path.endswith(".py")):
            continue
        source = (REPO_ROOT / path).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=path)
        for node in ast.walk(tree):
            if not isinstance(
                node,
                (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                continue
            docstring = ast.get_docstring(node, clean=False)
            if docstring is None:
                continue
            for match in _RUNTIME_DOC_INTERNAL_PROSE.finditer(docstring):
                line = getattr(node, "lineno", 1) + docstring.count(
                    "\n", 0, match.start()
                )
                findings.append(f"{path}:{line}: {match.group(0)!r}")

    assert not findings, "\n" + "\n".join(findings)
