"""Pure Markdown rewriting and checks for portable GitHub wiki candidates."""

from __future__ import annotations

from collections.abc import Mapping
from html import unescape
from html.parser import HTMLParser
import posixpath
import re
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from typing import Any

from .validation import portable_path_key, require_portable_relative_path


MAX_WIKI_FILES = 5_000
MAX_WIKI_FILE_BYTES = 8 * 1024 * 1024
MAX_WIKI_TOTAL_BYTES = 64 * 1024 * 1024
_MAX_TOKENS = 100_000
_WIKI_LINK = re.compile(r"\[\[([^\]\r\n]+)\]\]")
_REFERENCE = re.compile(r"(?m)^[ \t]*(?:>[ \t]*)*\[(?:\\.|[^\]\\\r\n])+\]:[ \t]*")
_ESCAPE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])")
_FORMAT_TAGS = frozenset(
    {
        "a",
        "b",
        "br",
        "blockquote",
        "code",
        "dd",
        "del",
        "details",
        "div",
        "dl",
        "dt",
        "em",
        "hr",
        "i",
        "ins",
        "kbd",
        "li",
        "ol",
        "p",
        "pre",
        "s",
        "span",
        "strong",
        "sub",
        "summary",
        "sup",
        "ul",
    }
)


def _bounded_path(path: str) -> str:
    if len(path.encode("utf-8")) > 1024 or any(
        len(part.encode("utf-8")) > 255 for part in path.split("/")
    ):
        raise ValueError("Wiki path exceeds portable filename bounds")
    return path


def _path(value: object) -> str:
    error = ValueError("Wiki paths must be canonical portable relative paths")
    return _bounded_path(
        require_portable_relative_path(
            value,
            text_error=error,
            relative_error=error,
            escape_error=error,
            traversal_error=error,
            separator_error=error,
            utf8_error=error,
            control_error=error,
            non_nfc_error=error,
            nonportable_error=error,
            reserved_error=error,
        )
    )


def _page_path(value: object) -> str:
    path = _path(value)
    if "/" in path or not path.endswith(".md") or not path[:-3]:
        raise ValueError("Wiki pages require flat, nonempty .md filenames")
    return path


def _route(path: str) -> str:
    return path[:-3].replace(" ", "-")


def _parse(text: str):
    try:
        from markdown_it import MarkdownIt
    except ImportError as exc:
        raise ValueError(
            "GitHub wiki content requires the publication extra (markdown-it-py>=4,<5)"
        ) from exc
    parser = MarkdownIt("commonmark", {"html": True, "maxNesting": 64}).enable(
        ["table", "strikethrough"]
    )
    # Attach exact inline-source spans using MarkdownIt's own rule decisions;
    # unmatched backticks must never hide live links in another paragraph/cell.
    for name in ("backticks", "html_inline"):
        rule = parser.inline.ruler.getRules("")[
            parser.inline.ruler.get_active_rules().index(name)
        ]
        parser.inline.ruler.at(name, _record_span(rule))
    environment: dict[str, Any] = {}
    tokens = parser.parse(text, environment)
    if sum(1 + len(token.children or []) for token in tokens) > _MAX_TOKENS:
        raise ValueError("Markdown exceeds the supported token bound")
    return tokens, environment


def _record_span(rule):
    def record(state, silent):
        start, count = state.pos, len(state.tokens)
        matched = rule(state, silent)
        if matched and not silent and len(state.tokens) > count:
            token = state.tokens[-1]
            if token.type in {"code_inline", "html_inline"}:
                token.meta["publication_source_span"] = (start, state.pos)
        return matched

    return record


def _blank(text: str) -> str:
    return "".join(char if char in "\r\n" else " " for char in text)


def _line_match(text, part, start, end):
    found = text.find(part, start, end)
    if found >= 0:
        return list(range(found, found + len(part)))
    # MarkdownIt's table rule removes the escape before a literal pipe prior
    # to inline parsing. Keep its original source coordinate when matching.
    cleaned, positions = [], []
    cursor = start
    while cursor < end:
        if text[cursor : cursor + 2] == "\\|" and _escaped(text, cursor + 1):
            cursor += 1
        cleaned.append(text[cursor])
        positions.append(cursor)
        cursor += 1
    found = "".join(cleaned).find(part)
    if found < 0:
        raise ValueError("Inline markup source layout is unsupported")
    return positions[found : found + len(part)]


def _inline_offsets(text, token, offsets, cursors):
    positions = []
    parts = token.content.split("\n")
    for index, part in enumerate(parts):
        line = token.map[0] + index
        if line >= token.map[1]:
            raise ValueError("Inline markup source layout is unsupported")
        start, end = offsets[line], offsets[line + 1]
        body_end = end
        while body_end > start and text[body_end - 1] in "\r\n":
            body_end -= 1
        observed = _line_match(
            text, part, max(start, cursors.get(line, start)), body_end
        )
        positions.extend(observed)
        cursors[line] = (
            observed[-1] + 1 if observed else max(start, cursors.get(line, start))
        )
        if index < len(parts) - 1:
            positions.append(body_end)
    return positions


def _visible(text: str, tokens) -> str:
    value = list(text)
    # CommonMark normalizes CRLF/CR, but does not treat Unicode line separators
    # as source lines. Token.map coordinates must use precisely those rules.
    offsets = [0, *(match.end() for match in re.finditer(r"\r\n|\r|\n", text))]
    if offsets[-1] < len(text):
        offsets.append(len(text))
    cursors = {}
    for token in tokens:
        if token.map is None:
            continue
        start, end = offsets[token.map[0]], offsets[token.map[1]]
        if token.type in {"fence", "code_block", "html_block"}:
            value[start:end] = _blank(text[start:end])
        elif token.children:
            spans = [
                child.meta["publication_source_span"]
                for child in token.children
                if "publication_source_span" in child.meta
            ]
            if spans:
                positions = _inline_offsets(text, token, offsets, cursors)
                for first, last in spans:
                    for position in positions[first:last]:
                        if text[position] not in "\r\n":
                            value[position] = " "
            elif token.type == "inline":
                # Reserve an earlier table cell's source range even when it
                # contains no code/HTML, so identical later cells map correctly.
                _inline_offsets(text, token, offsets, cursors)
    return "".join(value)


def _escaped(text: str, position: int) -> bool:
    count = 0
    while position > 0 and text[position - 1] == "\\":
        position -= 1
        count += 1
    return bool(count % 2)


def _destination(text: str, start: int) -> tuple[int, int] | None:
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text):
        return None
    if text[start] == "<":
        end = start + 1
        while end < len(text) and text[end] not in "\r\n":
            if text[end] == ">" and not _escaped(text, end):
                return start + 1, end
            end += 1
        return None
    end, depth = start, 0
    while end < len(text):
        char = text[end]
        if char == "\\" and end + 1 < len(text):
            end += 2
            continue
        if char.isspace() or (char == ")" and depth == 0):
            break
        if char == "(":
            depth += 1
            if depth > 32:
                return None
        elif char == ")":
            depth -= 1
        end += 1
    return (start, end) if end > start else None


def _resources(visible: str):
    stack = []
    for index, char in enumerate(visible):
        if _escaped(visible, index):
            continue
        if char == "[":
            stack.append(index)
        elif char == "]" and stack:
            stack.pop()
            if visible[index : index + 2] == "](":
                span = _destination(visible, index + 2)
                if span:
                    yield (*span, visible[slice(*span)], "markdown")
    for match in _REFERENCE.finditer(visible):
        span = _destination(visible, match.end())
        if span:
            yield (*span, visible[slice(*span)], "reference")
    for match in _WIKI_LINK.finditer(visible):
        if _escaped(visible, match.start()):
            continue
        content = match.group(1)
        if content.count("|") > 1 or re.match(
            r"^(?:alt|width|height|align|float|class|style)=",
            content.rsplit("|", 1)[-1],
        ):
            yield match.start(), match.end(), content, "unsupported-wiki"
            continue
        target = content.rsplit("|", 1)[-1]
        if not target.strip():
            yield match.start(), match.end(), content, "unsupported-wiki"
            continue
        offset = match.start(1) + len(content) - len(target)
        yield offset, offset + len(target), target, "wiki"


def _url(value: str):
    value = _ESCAPE.sub(r"\1", unescape(value.strip()))
    if any(ord(char) < 32 or ord(char) == 127 for char in value) or "\\" in value:
        raise ValueError("Link contains a control character or non-POSIX separator")
    if value.startswith("//"):
        raise ValueError("Protocol-relative and host paths are not portable wiki links")
    parsed = urlsplit(value)
    if parsed.scheme:
        if parsed.scheme.lower() not in {"http", "https", "mailto"}:
            raise ValueError("Executable, local-file or unsupported link scheme")
        if parsed.scheme.lower() in {"http", "https"} and (
            not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError(
                "External links require a host without embedded credentials"
            )
        return parsed, None
    path = unquote(parsed.path, errors="strict")
    fragment = unquote(parsed.fragment, errors="strict")
    if (
        any(ord(char) < 32 or ord(char) == 127 for char in path + fragment)
        or "\\" in path
    ):
        raise ValueError("Decoded link contains an unsafe path or fragment")
    if re.search(r"%[0-9a-fA-F]{2}", path):
        raise ValueError("Multiply encoded paths are ambiguous")
    if re.match(r"^[A-Za-z]:", path):
        raise ValueError("Host drive paths are not wiki links")
    return parsed, path


def _relative(path: str, parent: str = "") -> str:
    normalized = posixpath.normpath(posixpath.join(parent, path))
    if normalized == ".." or normalized.startswith("../") or normalized.startswith("/"):
        raise ValueError("Link escapes its configured root")
    return _path(normalized)


def _append_url(path: str, parsed) -> str:
    return urlunsplit(
        ("", "", quote(path, safe="/-._~"), parsed.query, parsed.fragment)
    )


def _repository_link(
    path: str, parsed, repository_url: str | None, source_revision: str | None
) -> str:
    if not repository_url or not source_revision:
        raise ValueError(
            "Repository links require both repository_url and an immutable source_revision"
        )
    if (
        repository_url != repository_url.strip()
        or "\\" in repository_url
        or any(ord(char) < 32 or ord(char) == 127 for char in repository_url)
    ):
        raise ValueError("repository_url must be a canonical HTTPS repository URL")
    repository = urlsplit(repository_url)
    _path(unquote(repository.path.strip("/"), errors="strict"))
    if (
        repository.scheme != "https"
        or not repository.netloc
        or repository.username is not None
        or repository.password is not None
        or repository.query
        or repository.fragment
        or not repository.path.strip("/")
    ):
        raise ValueError(
            "repository_url must be an HTTPS repository URL without credentials, query or fragment"
        )
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", source_revision):
        raise ValueError("source_revision must be a full immutable Git object ID")
    return (
        repository_url.rstrip("/")
        + "/blob/"
        + source_revision
        + "/"
        + _append_url(path, parsed)
    )


def _resource_identity(value: str):
    parsed, path = _url(value)
    return (
        parsed.scheme,
        parsed.netloc,
        path,
        unquote(parsed.query),
        unquote(parsed.fragment),
    )


def prepare_wiki_markdown(
    text: str,
    *,
    source_path: str,
    source_pages: Mapping[str, str],
    source_assets: Mapping[str, str],
    repository_url: str | None = None,
    source_revision: str | None = None,
) -> str:
    """Rewrite declared source links without loading application code or files."""
    _path(source_path)
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_WIKI_FILE_BYTES:
        raise ValueError("Markdown input must be text within the per-file byte bound")
    pages = {_path(path): _page_path(target) for path, target in source_pages.items()}
    assets = {_path(path): _path(target) for path, target in source_assets.items()}
    if len(pages) + len(assets) > MAX_WIKI_FILES:
        raise ValueError("Content mappings exceed the wiki file bound")
    if pages.keys() & assets.keys():
        raise ValueError("A source cannot be mapped as both page and asset")
    page_destinations = {value: _route(value) for value in pages.values()}
    routes = set(page_destinations.values())
    tokens, environment = _parse(text)
    recognized = {
        _resource_identity(str(child.attrGet("href") or child.attrGet("src") or ""))
        for token in tokens
        for child in token.children or []
        if child.type in {"link_open", "image"}
    }
    recognized.update(
        _resource_identity(record["href"])
        for record in environment.get("references", {}).values()
    )
    visible = _visible(text, tokens)
    replacements = []
    for start, end, raw, kind in _resources(visible):
        if kind == "unsupported-wiki":
            raise ValueError("Wiki links with additional attributes are unsupported")
        parsed, path = _url(raw)
        if kind != "wiki" and _resource_identity(raw) not in recognized:
            continue
        if path is None or not path:
            continue
        rooted = path.startswith("/")
        source = _relative(
            path.lstrip("/") if rooted else path,
            "" if rooted else posixpath.dirname(source_path),
        )
        if source in pages:
            target = _append_url(_route(pages[source]), parsed)
        elif source in assets:
            target = _append_url(assets[source], parsed)
        elif not rooted and path in page_destinations:
            target = _append_url(page_destinations[path], parsed)
        elif not rooted and (path in routes or path in assets.values()):
            target = _append_url(path, parsed)
        elif kind == "wiki":
            target = _append_url(path.lstrip("/"), parsed) if rooted else raw
        elif rooted or repository_url is not None or source_revision is not None:
            target = _repository_link(source, parsed, repository_url, source_revision)
        else:
            # The complete candidate checker can resolve native wiki links,
            # including paths to preserved manual pages, after composition.
            target = raw
        if target != raw:
            replacements.append((start, end, target))
    for start, end, value in sorted(set(replacements), reverse=True):
        text = text[:start] + value + text[end:]
    return text


class _HTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors: list[str] = []
        self.unsupported = False

    def handle_starttag(self, tag, attrs):
        if tag not in _FORMAT_TAGS or any(
            name not in {"id", "name", "title", "open"} for name, _value in attrs
        ):
            self.unsupported = True
        for value in {
            value
            for name, value in attrs
            if name in {"id", "name"} and value is not None
        }:
            if not value or any(ord(char) < 32 or ord(char) == 127 for char in value):
                self.unsupported = True
            else:
                self.anchors.append(value)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def unknown_decl(self, data):
        self.unsupported = True


def _plain(children) -> str:
    return "".join(
        _plain(token.children)
        if token.type == "image"
        else token.content
        if token.type in {"text", "code_inline"}
        else " "
        if token.type in {"softbreak", "hardbreak"}
        else ""
        for token in children or []
    )


def _slug(text: str) -> str:
    return re.sub(r"[^\w\- ]", "", text.strip().lower(), flags=re.UNICODE).replace(
        " ", "-"
    )


def check_github_wiki(files: Mapping[str, bytes]) -> dict[str, Any]:
    """Check a complete candidate without filesystem or network access."""
    findings: set[tuple[str, str, str]] = set()

    def issue(path, kind, message):
        findings.add((str(path), kind, message))

    if not isinstance(files, Mapping) or any(type(path) is not str for path in files):
        raise ValueError("Wiki candidates require a mapping of string paths to bytes")
    if len(files) > MAX_WIKI_FILES:
        issue("", "file-limit", "Candidate exceeds the wiki file bound")
        return {
            "ok": False,
            "findings": [
                {"path": p, "kind": k, "message": m} for p, k, m in sorted(findings)
            ],
        }
    valid = {}
    spellings = {}
    total = 0
    for path, raw in sorted(files.items(), key=lambda item: str(item[0])):
        try:
            _path(path)
        except (ValueError, TypeError, UnicodeError) as exc:
            issue(path, "invalid-path", str(exc))
            continue
        if type(raw) is not bytes:
            issue(path, "invalid-content", "Candidate files must contain bytes")
            continue
        total += len(raw)
        if len(raw) > MAX_WIKI_FILE_BYTES:
            issue(path, "file-limit", "File exceeds the per-file byte bound")
            continue
        parts = path.split("/")
        for count in range(1, len(parts) + 1):
            exact = "/".join(parts[:count])
            key = portable_path_key(exact)
            if key in spellings and spellings[key] != exact:
                issue(
                    path,
                    "path-collision",
                    "Path spelling collides across supported filesystems",
                )
            spellings[key] = exact
        valid[path] = raw
    if total > MAX_WIKI_TOTAL_BYTES:
        issue("", "total-limit", "Candidate exceeds the total byte bound")
    full_keys = {portable_path_key(path) for path in valid}
    for path in valid:
        if any(
            portable_path_key("/".join(path.split("/")[:count])) in full_keys
            for count in range(1, len(path.split("/")))
        ):
            issue(
                path,
                "tree-collision",
                "A file also occupies a parent directory coordinate",
            )
    if "Home.md" not in valid:
        issue("Home.md", "missing-home", "A GitHub wiki candidate requires Home.md")
    if total > MAX_WIKI_TOTAL_BYTES:
        return {
            "ok": False,
            "findings": [
                {"path": p, "kind": k, "message": m} for p, k, m in sorted(findings)
            ],
        }
    pages, routes, anchors = {}, {}, {}
    for path, raw in sorted(valid.items()):
        if path.lower().endswith(
            (
                ".markdown",
                ".textile",
                ".rst",
                ".rdoc",
                ".org",
                ".mediawiki",
                ".asciidoc",
            )
        ):
            issue(path, "unsupported-page", "Only Markdown .md wiki pages are checked")
        if not path.lower().endswith(".md"):
            continue
        try:
            _page_path(path)
            text = raw.decode("utf-8")
            if "\x00" in text:
                raise ValueError("Markdown contains a NUL")
            tokens, _environment = _parse(text)
            if re.match(r"\A---[ \t]*\r?\n", text):
                issue(
                    path,
                    "unsupported-frontmatter",
                    "YAML front matter requires an explicit supported content conversion",
                )
        except (ValueError, UnicodeError) as exc:
            issue(path, "invalid-markdown", str(exc))
            continue
        route = _route(path)
        folded = portable_path_key(route)
        if folded in routes:
            issue(path, "page-collision", "Wiki page routes collide")
        routes[folded] = path
        pages[path] = (text, tokens)
        used = set()
        html = _HTML()
        for index, token in enumerate(tokens):
            if (
                token.type == "fence"
                and token.info.strip().casefold() == "mermaid"
                and re.search(r"(?m)^\s*(?:click|link)\b", token.content)
            ):
                issue(
                    path,
                    "unsupported-diagram-link",
                    "Interactive diagram links require explicit supported Markdown navigation",
                )
            if token.type == "heading_open":
                base = _slug(_plain(tokens[index + 1].children))
                anchor, number = base, 0
                while anchor in used:
                    number += 1
                    anchor = f"{base}-{number}"
                used.add(anchor)
            if token.type == "html_block":
                html.feed(token.content)
            for child in token.children or []:
                if child.type == "html_inline":
                    html.feed(child.content)
        html.close()
        for anchor in html.anchors:
            if anchor in used:
                issue(
                    path,
                    "anchor-collision",
                    "Custom and generated anchors must be unique",
                )
            used.add(anchor)
        if html.unsupported:
            issue(
                path,
                "unsupported-html",
                "HTML URLs, media or unsupported attributes require explicit supported Markdown",
            )
        anchors[path] = used
    for path, (text, tokens) in pages.items():
        targets = []
        for token in tokens:
            for child in token.children or []:
                if child.type == "link_open":
                    targets.append((child.attrGet("href") or "", False, False))
                elif child.type == "image":
                    targets.append((child.attrGet("src") or "", True, False))
        try:
            visible = _visible(text, tokens)
        except ValueError as exc:
            issue(path, "unsupported-markdown-layout", str(exc))
            visible = ""
        for _start, _end, raw, kind in _resources(visible):
            if kind == "unsupported-wiki":
                issue(
                    path,
                    "unsupported-wiki",
                    "Wiki links with additional attributes are unsupported",
                )
            elif kind == "wiki":
                targets.append((raw, False, True))
            else:
                try:
                    _url(raw)
                except (ValueError, UnicodeError) as exc:
                    issue(path, "unsafe-link", str(exc))
        for target, image, wiki in targets:
            try:
                parsed, local = _url(target)
                if local is None:
                    continue
                if local.startswith("/") and wiki:
                    local = local.lstrip("/")
                elif local.startswith("/"):
                    raise ValueError(
                        "Root-relative links must be rewritten to a pinned repository URL"
                    )
                selected = path if not local else _relative(local)
                if selected not in valid:
                    page_path = local[:-3] if local.endswith(".md") else local
                    selected = routes.get(
                        portable_path_key(page_path.replace(" ", "-")), ""
                    )
                    if selected and _route(selected) != page_path.replace(" ", "-"):
                        raise ValueError("Link spelling differs from its target page")
                if not selected or selected not in valid:
                    issue(
                        path, "missing-link", "Local link target is absent: " + target
                    )
                    continue
                fragment = unquote(parsed.fragment, errors="strict")
                if image and selected in pages:
                    issue(path, "image-page", "Image link points to a Markdown page")
                elif image and posixpath.splitext(selected)[1].lower() not in {
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".svg",
                    ".webp",
                    ".avif",
                    ".apng",
                    ".bmp",
                    ".ico",
                }:
                    issue(
                        path,
                        "image-format",
                        "Local image requires a supported image filename",
                    )
                if fragment and (
                    selected not in anchors or fragment not in anchors[selected]
                ):
                    issue(
                        path,
                        "missing-anchor",
                        "Link fragment is absent or unsupported: " + target,
                    )
            except (ValueError, UnicodeError) as exc:
                issue(path, "unsafe-link", str(exc))
    return {
        "ok": not findings,
        "findings": [
            {"path": path, "kind": kind, "message": message}
            for path, kind, message in sorted(findings)
        ],
    }
