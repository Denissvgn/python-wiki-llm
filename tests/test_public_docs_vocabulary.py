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


_INTERNAL_TASK_PREFIXES = (
    "FND",
    "DEC",
    "REF",
    "PRV",
    "KNW",
    "SCH",
    "POL",
    "VER",
    "REL",
    "CLN",
    "KNOW",
    "DL",
    "NKC",
    "PUB",
    "SKL",
    "SEC",
    "ARC",
    "KUX",
    "VEC",
    "HYG",
    "QCP",
    "CLX",
    "M2MAIN",
)
_INTERNAL_TASK_PREFIX_PATTERN = "(?:" + "|".join(
    re.escape(prefix) for prefix in _INTERNAL_TASK_PREFIXES
) + ")"
_INTERNAL_TASK_ID_PATTERN = re.compile(
    rf"(?<![\w-]){_INTERNAL_TASK_PREFIX_PATTERN}-[0-9]+(?![\w-])",
    re.IGNORECASE,
)
_NUMBERED_LABEL_GAP = rf"(?:{_PROSE_GAP}|[-_]+)"


FORBIDDEN_INTERNAL_PROSE: Mapping[str, ForbiddenProse] = {
    "delivery-stage-label": ForbiddenProse(
        re.compile(r"(?<!\w)M[0-9]+(?!\w)"),
        "Standalone M-number labels identify internal delivery stages.",
    ),
    "internal-task-id": ForbiddenProse(
        _INTERNAL_TASK_ID_PATTERN,
        "These prefixes identify internal remediation or delivery tasks.",
    ),
    "priority-calibration-name": ForbiddenProse(
        re.compile(rf"\bP0{_PROSE_GAP}calibration\b", re.IGNORECASE),
        "The public feature name is documentation calibration.",
    ),
    "shadow-pilot-claim": ForbiddenProse(
        re.compile(rf"\bshadow{_PROSE_GAP}pilot\b", re.IGNORECASE),
        "This phrase implies an internal evaluation that did not run.",
    ),
    "numbered-delivery-milestone": ForbiddenProse(
        re.compile(
            rf"\b(?:delivery{_PROSE_GAP})?"
            rf"milestone{_NUMBERED_LABEL_GAP}"
            rf"(?:\#(?:{_NUMBERED_LABEL_GAP})?)?(?:[0-9]+|[IVX]+)\b",
            re.IGNORECASE,
        ),
        "Numbered milestone labels expose internal delivery sequencing.",
    ),
    "numbered-delivery-epic": ForbiddenProse(
        re.compile(
            rf"\bepic{_NUMBERED_LABEL_GAP}"
            rf"(?:\#(?:{_NUMBERED_LABEL_GAP})?)?[0-9]+(?:\.[0-9]+)*\b",
            re.IGNORECASE,
        ),
        "Numbered epic labels expose internal delivery sequencing.",
    ),
    "closure-review": ForbiddenProse(
        re.compile(rf"\bclosure{_PROSE_GAP}review\b", re.IGNORECASE),
        "This phrase identifies an internal completion checkpoint.",
    ),
}


# Add an entry only for an externally observable compatibility literal that
# cannot be removed. Keys must be exact literals and values must explain the
# public compatibility obligation; path, line, and whole-file exceptions are
# deliberately unsupported.
PUBLIC_LEGACY_IDENTIFIERS: Mapping[str, str] = {
    "m4-documentation-hooks": (
        "Deprecated public plugin-sample identifier retained for CLI compatibility."
    ),
}
_SOURCE_IDENTITY_RULES = frozenset(
    {"delivery-stage-label", "internal-task-id"}
)
_SELECTED_SOURCE_INTERNAL_IDENTIFIER = re.compile(
    rf"(?i:\b{_INTERNAL_TASK_PREFIX_PATTERN}-\d+\b)|\bM\d+\b|"
    rf"(?i:\bEpic{_NUMBERED_LABEL_GAP}\d+(?:\.\d+)*\b)"
)
_RUNTIME_DOC_INTERNAL_PROSE = re.compile(
    r"\btests?\s*/\s*runners?\b",
    re.IGNORECASE,
)
_IMPLEMENTATION_PATH_PATTERN = re.compile(
    r"(?:^|[/_.-])(?:"
    r"(?:m|p)[0-9]+|phase[-_ ]*[0-9]+|"
    r"milestone[-_ ]+#?[-_ ]*(?:[0-9]+|[ivx]+)|"
    r"epic[-_ ]+#?[-_ ]*[0-9]+(?:\.[0-9]+)*|"
    rf"{_INTERNAL_TASK_PREFIX_PATTERN}-[0-9]+"
    r")(?=[/_.-]|$)",
    re.IGNORECASE,
)
_PROVENANCE_ARTIFACT_ROOTS = (
    ".github/",
    ".llm-wiki/",
    "examples/plugins/",
    "integrations/",
    "release/",
    "src/",
    "tests/",
)
_PROVENANCE_ARTIFACT_FILES = frozenset(
    {
        ".gitattributes",
        ".gitignore",
        "MANIFEST.in",
        "pyproject.toml",
        "pyrightconfig.json",
        "release_build_backend.py",
        "ruff.toml",
    }
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


def _provenance_artifacts(
    tracked_files: Iterable[str] | None = None,
) -> tuple[str, ...]:
    """Return tracked implementation and verification artifacts."""

    tracked = _tracked_files() if tracked_files is None else tuple(tracked_files)
    return tuple(
        sorted(
            path
            for path in tracked
            if path in _PROVENANCE_ARTIFACT_FILES
            or path.startswith(_PROVENANCE_ARTIFACT_ROOTS)
        )
    )


def _decode_provenance_artifact(path: str, raw: bytes) -> str:
    """Decode tracked text and reject binary or malformed content."""

    if b"\0" in raw:
        raise AssertionError(f"{path} must not contain NUL bytes")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AssertionError(
            f"tracked provenance artifact {path} must be UTF-8 text"
        ) from exc


def _is_public_documentation_path(path: str) -> bool:
    pure = PurePosixPath(path)
    if pure.name.casefold() == "readme.md":
        return True
    if path in {"CHANGELOG.md", "CODE_OF_CONDUCT.md", "SECURITY.md"}:
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


def _synthetic_marker(*parts: str) -> str:
    """Assemble a synthetic forbidden marker without tripping the self-scan."""

    return "".join(parts)


_STAGE_PREFIX = "M"
_STAGE_NUMBER = "987654"
_STAGE_MARKER = _synthetic_marker(_STAGE_PREFIX, _STAGE_NUMBER)
_TASK_PREFIX = "PUB"
_TASK_NUMBER = "987654"
_TASK_MARKER = _synthetic_marker(_TASK_PREFIX, "-", _TASK_NUMBER)
_PRIORITY_MARKER = _synthetic_marker("P", "0")
_CALIBRATION_WORD = _synthetic_marker("calibra", "tion")
_SHADOW_WORD = _synthetic_marker("sha", "dow")
_PILOT_WORD = _synthetic_marker("pi", "lot")
_MILESTONE_WORD = "Milestone"
_MILESTONE_NUMBER = "987654"
_MILESTONE_ROMAN = "XXVII"
_EPIC_WORD = "Epic"
_EPIC_NUMBER = "987654"
_EPIC_SUBNUMBER = "987654.321"
_CLOSURE_WORD = _synthetic_marker("clo", "sure")
_REVIEW_WORD = _synthetic_marker("re", "view")


@pytest.mark.parametrize(
    ("snippet", "rule"),
    [
        (f"The {_STAGE_MARKER} stage expanded the graph.", "delivery-stage-label"),
        (f"Complete {_TASK_MARKER} before release.", "internal-task-id"),
        (
            f"Complete {_TASK_PREFIX}&#45;{_TASK_NUMBER} before release.",
            "internal-task-id",
        ),
        (
            f"{_PRIORITY_MARKER} {_CALIBRATION_WORD} is now complete.",
            "priority-calibration-name",
        ),
        (
            f"{_PRIORITY_MARKER} cali&#98;ration is now complete.",
            "priority-calibration-name",
        ),
        (f"Run a {_SHADOW_WORD} {_PILOT_WORD} first.", "shadow-pilot-claim"),
        (
            f"{_MILESTONE_WORD} {_MILESTONE_NUMBER} adds governance.",
            "numbered-delivery-milestone",
        ),
        (
            f"{_MILESTONE_WORD} #{_MILESTONE_NUMBER} adds governance.",
            "numbered-delivery-milestone",
        ),
        (
            f"{_MILESTONE_WORD}-{_MILESTONE_NUMBER} adds governance.",
            "numbered-delivery-milestone",
        ),
        (
            f"Delivery {_MILESTONE_WORD.lower()} #\n{_MILESTONE_ROMAN} is next.",
            "numbered-delivery-milestone",
        ),
        (
            f"{_EPIC_WORD} {_EPIC_NUMBER} adds dependency analysis.",
            "numbered-delivery-epic",
        ),
        (
            f"{_EPIC_WORD} {_EPIC_SUBNUMBER} adds aggregation.",
            "numbered-delivery-epic",
        ),
        (
            f"{_EPIC_WORD}_{_EPIC_SUBNUMBER} adds aggregation.",
            "numbered-delivery-epic",
        ),
        (
            f"{_EPIC_WORD}\n{_EPIC_SUBNUMBER} adds aggregation.",
            "numbered-delivery-epic",
        ),
        (f"Start the {_CLOSURE_WORD} {_REVIEW_WORD}.", "closure-review"),
        (
            f"{_PRIORITY_MARKER}\n{_CALIBRATION_WORD} is now complete.",
            "priority-calibration-name",
        ),
        (
            f"{_PRIORITY_MARKER}  \n{_CALIBRATION_WORD} is now complete.",
            "priority-calibration-name",
        ),
        (
            f"{_PRIORITY_MARKER}\\\n{_CALIBRATION_WORD} is now complete.",
            "priority-calibration-name",
        ),
        (
            f"Run a {_SHADOW_WORD}\n  {_PILOT_WORD} first.",
            "shadow-pilot-claim",
        ),
        (
            f"Delivery\n{_MILESTONE_WORD.lower()} {_MILESTONE_ROMAN} is next.",
            "numbered-delivery-milestone",
        ),
        (
            f"Start the {_CLOSURE_WORD}\t{_REVIEW_WORD}.",
            "closure-review",
        ),
        (
            f"{_PRIORITY_MARKER} *{_CALIBRATION_WORD}* is now complete.",
            "priority-calibration-name",
        ),
        (
            f"{_PRIORITY_MARKER} ~~{_CALIBRATION_WORD}~~ is now complete.",
            "priority-calibration-name",
        ),
        (
            f"![{_PRIORITY_MARKER} *{_CALIBRATION_WORD}*](image.png)",
            "priority-calibration-name",
        ),
        (
            f"{_PRIORITY_MARKER}<br>{_CALIBRATION_WORD} is now complete.",
            "priority-calibration-name",
        ),
        (
            f"<div>{_PRIORITY_MARKER}<br>\n{_CALIBRATION_WORD}</div>",
            "priority-calibration-name",
        ),
        (
            f"Run a {_SHADOW_WORD}<br/>{_PILOT_WORD} first.",
            "shadow-pilot-claim",
        ),
        (
            f'<span title="{_PRIORITY_MARKER} {_CALIBRATION_WORD}">public</span>',
            "priority-calibration-name",
        ),
        (
            f'<img alt="{_PRIORITY_MARKER} {_CALIBRATION_WORD}">',
            "priority-calibration-name",
        ),
        (
            f'<button aria-label="{_SHADOW_WORD} {_PILOT_WORD}">x</button>',
            "shadow-pilot-claim",
        ),
        (
            f'{_PRIORITY_MARKER} <span title="tooltip">{_CALIBRATION_WORD}</span>',
            "priority-calibration-name",
        ),
        (
            f'Run a {_SHADOW_WORD} <span aria-label="note">{_PILOT_WORD}</span> first.',
            "shadow-pilot-claim",
        ),
        (
            f'{_PRIORITY_MARKER} <img alt="{_CALIBRATION_WORD}" '
            'src="https://example.com/image.png">',
            "priority-calibration-name",
        ),
        (
            f'Run a {_SHADOW_WORD} <img alt="{_PILOT_WORD}" '
            'src="https://example.com/image.png">',
            "shadow-pilot-claim",
        ),
        (
            f'{_PRIORITY_MARKER} <input type="image" '
            f'alt="{_CALIBRATION_WORD}" src="image.png">',
            "priority-calibration-name",
        ),
        (
            f'{_PRIORITY_MARKER} <input type="submit" '
            f'value="{_CALIBRATION_WORD}">',
            "priority-calibration-name",
        ),
        (
            f'{_PRIORITY_MARKER} <textarea '
            f'placeholder="{_CALIBRATION_WORD}"></textarea>',
            "priority-calibration-name",
        ),
        (
            f'{_PRIORITY_MARKER} <textarea '
            f'placeholder="{_CALIBRATION_WORD}">\n</textarea>',
            "priority-calibration-name",
        ),
        (
            f'{_PRIORITY_MARKER} <input type="unknown" '
            f'placeholder="{_CALIBRATION_WORD}">',
            "priority-calibration-name",
        ),
        (
            f'{_PRIORITY_MARKER} <input type=" text " '
            f'placeholder="{_CALIBRATION_WORD}">',
            "priority-calibration-name",
        ),
        (
            f'{_PRIORITY_MARKER} <input type=" hidden " '
            f'value="{_CALIBRATION_WORD}">',
            "priority-calibration-name",
        ),
        (
            f'{_PRIORITY_MARKER} <input type="number" value="invalid" '
            f'placeholder="{_CALIBRATION_WORD}">',
            "priority-calibration-name",
        ),
        (
            f"Run a {_SHADOW_WORD} **{_PILOT_WORD}** first.",
            "shadow-pilot-claim",
        ),
        (
            f"> {_PRIORITY_MARKER}\n> {_CALIBRATION_WORD} is complete.",
            "priority-calibration-name",
        ),
        (f"`Complete {_TASK_MARKER} before release.`", "internal-task-id"),
        (f"```\n{_STAGE_MARKER}\n```", "delivery-stage-label"),
        (
            f"<!-- Complete {_TASK_MARKER} before release. -->",
            "internal-task-id",
        ),
        (
            f"<!-- {_PRIORITY_MARKER} {_CALIBRATION_WORD} -->",
            "priority-calibration-name",
        ),
        (
            f"{_STAGE_PREFIX}&#x200B;{_STAGE_NUMBER}",
            "delivery-stage-label",
        ),
        (
            f"{_TASK_PREFIX}&ZeroWidthSpace;-{_TASK_NUMBER}",
            "internal-task-id",
        ),
        (
            f"{_PRIORITY_MARKER} cali&shy;bration",
            "priority-calibration-name",
        ),
        (f"{_SHADOW_WORD} pi&#x200B;lot", "shadow-pilot-claim"),
        (f"{_CLOSURE_WORD} re&#xfeff;view", "closure-review"),
        (f"{_STAGE_PREFIX}\u034f{_STAGE_NUMBER}", "delivery-stage-label"),
        (f"{_STAGE_PREFIX}\ufe0f{_STAGE_NUMBER}", "delivery-stage-label"),
        (f"{_STAGE_PREFIX}\u180b{_STAGE_NUMBER}", "delivery-stage-label"),
        (
            f"{_STAGE_PREFIX}\U000e0100{_STAGE_NUMBER}",
            "delivery-stage-label",
        ),
        (f"{_STAGE_PREFIX}\u2065{_STAGE_NUMBER}", "delivery-stage-label"),
        (f"{_STAGE_PREFIX}\ufff0{_STAGE_NUMBER}", "delivery-stage-label"),
        (
            f'<span aria-description="{_PRIORITY_MARKER} '
            f'{_CALIBRATION_WORD}">x</span>',
            "priority-calibration-name",
        ),
        (
            f'<option label="{_PRIORITY_MARKER} '
            f'{_CALIBRATION_WORD}">Public</option>',
            "priority-calibration-name",
        ),
        (
            f'<track label="{_SHADOW_WORD} {_PILOT_WORD}">',
            "shadow-pilot-claim",
        ),
        (
            f'<img alt="{_PRIORITY_MARKER} {_CALIBRATION_WORD}" alt="safe" '
            'src="https://example.com/image.png">',
            "priority-calibration-name",
        ),
        (
            f'<input type="submit" value="{_PRIORITY_MARKER} '
            f'{_CALIBRATION_WORD}" value="safe">',
            "priority-calibration-name",
        ),
        (f"{_STAGE_MARKER}\0", "delivery-stage-label"),
    ],
)
def test_internal_prose_scanner_rejects_delivery_vocabulary(snippet, rule):
    findings = scan_internal_prose(snippet)

    assert [finding.rule for finding in findings] == [rule]


@pytest.mark.parametrize(
    ("snippet", "rule"),
    [
        (
            f"{_PRIORITY_MARKER} {_CALIBRATION_WORD.title()}",
            "priority-calibration-name",
        ),
        (
            f"{_SHADOW_WORD.title()} {_PILOT_WORD.title()}",
            "shadow-pilot-claim",
        ),
        (
            f"{_MILESTONE_WORD.upper()} {_MILESTONE_NUMBER}",
            "numbered-delivery-milestone",
        ),
        (
            f"{_MILESTONE_WORD.lower()} {_MILESTONE_ROMAN.lower()}",
            "numbered-delivery-milestone",
        ),
        (
            f"{_EPIC_WORD.upper()} {_EPIC_NUMBER}",
            "numbered-delivery-epic",
        ),
        (
            f"{_CLOSURE_WORD.title()} {_REVIEW_WORD.title()}",
            "closure-review",
        ),
    ],
)
def test_internal_prose_scanner_rejects_phrase_case_variants(snippet, rule):
    assert [finding.rule for finding in scan_internal_prose(snippet)] == [rule]


@pytest.mark.parametrize(
    "snippet",
    [
        "Keep the remainder backlog in `bootstrap-remainder.md`.",
        f"Use {_PRIORITY_MARKER}, P1, and P2 as public content priorities.",
        "A pilot can establish a milestone before ordinary project closure.",
        "Write the generated report to reports/dep_vuln_triage_<date>.md.",
        f"The protocol remains `llm-wiki-{_PRIORITY_MARKER.lower()}-"
        f"{_CALIBRATION_WORD}-run/v1`.",
        f"- {_PRIORITY_MARKER}\n- {_CALIBRATION_WORD}\n",
        f"| left | right |\n|---|---|\n| {_PRIORITY_MARKER} | "
        f"{_CALIBRATION_WORD} |\n",
        f"x{_TASK_MARKER}y is an external identifier.",
        f"x\u200b{_TASK_MARKER} is an embedded identifier.",
        f"x\u00ad{_STAGE_MARKER} is an embedded identifier.",
        f"`some_{_TASK_MARKER}_name` is an embedded identifier.",
        f"é{_TASK_MARKER}é is an embedded identifier.",
        f"e\u0301{_TASK_MARKER} is an embedded identifier.",
        f"α{_STAGE_MARKER}β is an embedded identifier.",
        f"α\u0301{_STAGE_MARKER} is an embedded identifier.",
        f"<p>{_PRIORITY_MARKER}</p><p>{_CALIBRATION_WORD}</p>",
        f"<center>{_PRIORITY_MARKER}</center>\n"
        f"<center>{_CALIBRATION_WORD}</center>",
        f"<div>{_TASK_PREFIX}&amp;#45;{_TASK_NUMBER}</div>",
        f"<div>{_PRIORITY_MARKER}&amp;#32;{_CALIBRATION_WORD}</div>",
        f"<pre>{_PRIORITY_MARKER}\n\n{_CALIBRATION_WORD}</pre>",
        f"<pre>{_PRIORITY_MARKER}<br>\n{_CALIBRATION_WORD}</pre>",
        f"<textarea>{_PRIORITY_MARKER}\n\n{_CALIBRATION_WORD}</textarea>",
        f"<textarea>{_PRIORITY_MARKER}<br>\n{_CALIBRATION_WORD}</textarea>",
        f"![{_PRIORITY_MARKER}<br>{_CALIBRATION_WORD}](image.png)",
        f'![<span title="{_PRIORITY_MARKER} '
        f'{_CALIBRATION_WORD}">x</span>](image.png)',
        f'<div value="{_PRIORITY_MARKER} {_CALIBRATION_WORD}" '
        f'label="{_SHADOW_WORD} {_PILOT_WORD}">public</div>',
        f'<button value="{_PRIORITY_MARKER} '
        f'{_CALIBRATION_WORD}">Public</button>',
        f'<input type="hidden" value="{_PRIORITY_MARKER} '
        f'{_CALIBRATION_WORD}">',
        f'<input type="number" value="{_PRIORITY_MARKER} '
        f'{_CALIBRATION_WORD}">',
        f'<input type="date" value="{_PRIORITY_MARKER} '
        f'{_CALIBRATION_WORD}">',
        f'<img alt="safe" alt="{_PRIORITY_MARKER} {_CALIBRATION_WORD}" '
        'src="image.png">',
        (
            f'{_PRIORITY_MARKER} <textarea placeholder="{_CALIBRATION_WORD}">'
            "visible value</textarea>"
        ),
        f'{_PRIORITY_MARKER} <textarea '
        f'placeholder="{_CALIBRATION_WORD}">\n\n</textarea>',
        f'{_PRIORITY_MARKER} <input value="visible" '
        f'placeholder="{_CALIBRATION_WORD}">',
        f'{_PRIORITY_MARKER} cali<img alt="icon" '
        'src="https://example.com/image.png">bration',
        f'Start {_CLOSURE_WORD} <input value="x">{_REVIEW_WORD}.',
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
    stage_with_nul = f"{_STAGE_MARKER}\0"
    assert (
        _decode_public_text("README.md", stage_with_nul.encode())
        == stage_with_nul
    )


def test_scan_set_is_tracked_and_excludes_internal_reports():
    tracked = _tracked_files()
    scanned = public_documentation_files(tracked)

    assert "README.md" in scanned
    assert "CHANGELOG.md" in scanned
    assert "CODE_OF_CONDUCT.md" in scanned
    assert "SECURITY.md" in scanned
    assert "docs/native-knowledge.md" in scanned
    assert "integrations/obsidian/llm-wiki/README.md" in scanned
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


def test_provenance_scan_includes_tracked_non_python_text_surfaces():
    artifacts = set(_provenance_artifacts())
    representatives = {
        ".github/scripts/run-llm-wiki-ci-check.sh",
        ".github/workflows/ci.yml",
        "examples/plugins/documentation-hooks/detectors.py",
        "integrations/github-action/render_summary.py",
        "integrations/obsidian/llm-wiki/esbuild.config.mjs",
        "integrations/obsidian/llm-wiki/main.js",
        "integrations/obsidian/llm-wiki/src/main.ts",
        "release/qualification.py",
        "src/llm_wiki_cli/extractors/go_scripts/go.mod",
        "src/llm_wiki_cli/extractors/go_scripts/main.go",
        "src/llm_wiki_cli/extractors/haskell_scripts/Main.hs",
        "src/llm_wiki_cli/extractors/rust_scripts/.gitignore",
        "src/llm_wiki_cli/extractors/rust_scripts/Cargo.lock",
        "src/llm_wiki_cli/extractors/rust_scripts/src/main.rs",
        "src/llm_wiki_cli/extractors/ts_scripts/extract.js",
        "tests/fixtures/oci_calibration/Dockerfile",
    }

    assert representatives <= artifacts
    assert all(
        _decode_provenance_artifact(
            path,
            (REPO_ROOT / path).read_bytes(),
        )
        is not None
        for path in representatives
    )


def test_provenance_text_decoder_fails_closed():
    with pytest.raises(AssertionError, match="must not contain NUL"):
        _decode_provenance_artifact("fixture.txt", b"text\0payload")
    with pytest.raises(AssertionError, match="must be UTF-8"):
        _decode_provenance_artifact("fixture.txt", b"\xff")


@pytest.mark.parametrize(
    "path",
    [
        f"tests/{_MILESTONE_WORD.lower()}-{_MILESTONE_NUMBER}.py",
        f"tests/{_MILESTONE_WORD.lower()}-{_MILESTONE_ROMAN}/case.js",
        f"tests/{_EPIC_WORD.lower()}-{_EPIC_SUBNUMBER}/case.rs",
        f"tests/{_TASK_MARKER}.json",
    ],
)
def test_provenance_path_pattern_rejects_planning_families(path):
    assert _IMPLEMENTATION_PATH_PATTERN.search(path)


@pytest.mark.parametrize(
    "path",
    [
        f"tests/{_MILESTONE_WORD.lower()}{_MILESTONE_NUMBER}.py",
        f"tests/{_EPIC_WORD.lower()}{_EPIC_NUMBER}/case.rs",
        f"tests/{_TASK_MARKER}x.json",
    ],
)
def test_provenance_path_pattern_requires_family_boundaries(path):
    assert _IMPLEMENTATION_PATH_PATTERN.search(path) is None


@pytest.mark.parametrize("prefix", _INTERNAL_TASK_PREFIXES)
def test_internal_task_prefix_inventory_is_shared(prefix):
    marker = _synthetic_marker(prefix, "-", _TASK_NUMBER)

    assert [finding.rule for finding in scan_internal_prose(marker)] == [
        "internal-task-id"
    ]
    assert _INTERNAL_TASK_ID_PATTERN.search(marker)
    assert _IMPLEMENTATION_PATH_PATTERN.search(f"tests/{marker}.json")


def test_internal_task_prefix_matching_is_case_insensitive():
    marker = _synthetic_marker("cLn", "-", _TASK_NUMBER)

    assert [finding.rule for finding in scan_internal_prose(marker)] == [
        "internal-task-id"
    ]
    assert _INTERNAL_TASK_ID_PATTERN.search(marker)
    assert _IMPLEMENTATION_PATH_PATTERN.search(f"tests/{marker}.json")


def test_documentation_defect_ids_remain_public_product_language():
    marker = _synthetic_marker("DOC", "-", _TASK_NUMBER)

    assert scan_internal_prose(marker) == []
    assert _INTERNAL_TASK_ID_PATTERN.search(marker) is None
    assert _IMPLEMENTATION_PATH_PATTERN.search(f"tests/{marker}.json") is None


def test_lowercase_stage_compatibility_literal_remains_public():
    literal = next(iter(PUBLIC_LEGACY_IDENTIFIERS))

    assert scan_internal_prose(literal) == []


def test_source_and_test_artifacts_have_no_implementation_plan_provenance():
    """Keep implementation planning labels out of source and verification assets."""

    content_patterns = {
        "delivery-stage-label": FORBIDDEN_INTERNAL_PROSE[
            "delivery-stage-label"
        ].pattern,
        "numbered-milestone": FORBIDDEN_INTERNAL_PROSE[
            "numbered-delivery-milestone"
        ].pattern,
        "numbered-epic": FORBIDDEN_INTERNAL_PROSE[
            "numbered-delivery-epic"
        ].pattern,
        "backlog-task-id": _INTERNAL_TASK_ID_PATTERN,
    }
    findings: list[str] = []

    for relative in _provenance_artifacts():
        if _IMPLEMENTATION_PATH_PATTERN.search(relative):
            findings.append(f"{relative}: implementation-shaped path")
        text = _decode_provenance_artifact(
            relative,
            (REPO_ROOT / relative).read_bytes(),
        )
        for rule, pattern in content_patterns.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(
                    f"{relative}:{line}: {rule}: {match.group(0)!r}"
                )

    assert not findings, "\n" + "\n".join(findings)
