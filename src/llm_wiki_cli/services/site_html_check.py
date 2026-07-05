"""Built static-site HTML link validation."""

from __future__ import annotations

import posixpath
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Optional, Union
from urllib.parse import unquote, urlsplit


SUPPORTED_LINK_MODES = frozenset({"http", "file"})
_IGNORED_SCHEMES = frozenset({"http", "https", "mailto", "tel", "data", "javascript"})
_HREF_TAGS = frozenset({"a", "area", "link"})


class _HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, Optional[str]]],
    ) -> None:
        if tag.casefold() not in _HREF_TAGS:
            return
        for name, value in attrs:
            if name.casefold() == "href" and value is not None:
                self.hrefs.append(value.strip())


def check_built_site_links(
    *,
    built_site_dir: Union[str, Path],
    link_mode: str = "http",
) -> list[dict[str, str]]:
    """Return link issues found in built ``*.html`` files."""
    _validate_link_mode(link_mode)
    root = Path(built_site_dir).expanduser()
    if not root.exists() or not root.is_dir():
        return [
            {
                "category": "missing_built_html_target",
                "path": str(root),
                "message": f"Built site directory does not exist: {root}",
            }
        ]

    root_resolved = root.resolve()
    issues: list[dict[str, str]] = []
    for html_path in sorted(root.rglob("*.html")):
        if not html_path.is_file():
            continue
        try:
            content = html_path.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(
                {
                    "category": "malformed_built_html_link",
                    "path": str(html_path),
                    "message": f"Cannot read built HTML page: {exc}",
                }
            )
            continue
        parser = _HrefParser()
        parser.feed(content)
        for href in parser.hrefs:
            issue = _check_href(
                html_path,
                href,
                root=root_resolved,
                link_mode=link_mode,
            )
            if issue is not None:
                issues.append(issue)
    return issues


def _validate_link_mode(link_mode: str) -> None:
    if link_mode not in SUPPORTED_LINK_MODES:
        supported = ", ".join(sorted(SUPPORTED_LINK_MODES))
        raise ValueError(f"Unsupported built-site link mode: {link_mode} ({supported})")


def _check_href(
    html_path: Path,
    href: str,
    *,
    root: Path,
    link_mode: str,
) -> Optional[dict[str, str]]:
    if not href or href.startswith("#"):
        return None
    if "\x00" in href:
        return _issue(
            "malformed_built_html_link",
            html_path,
            href,
            "Built HTML link contains a NUL byte.",
        )

    try:
        parsed = urlsplit(href)
    except ValueError as exc:
        return _issue(
            "malformed_built_html_link",
            html_path,
            href,
            f"Cannot parse built HTML link: {exc}",
        )

    scheme = parsed.scheme.casefold()
    if scheme in _IGNORED_SCHEMES or parsed.netloc:
        return None
    if scheme:
        return _issue(
            "malformed_built_html_link",
            html_path,
            href,
            f"Unsupported built HTML link scheme: {scheme}",
        )

    raw_path = parsed.path
    if not raw_path:
        return None
    try:
        path = unquote(raw_path, errors="strict").replace("\\", "/")
    except UnicodeDecodeError as exc:
        return _issue(
            "malformed_built_html_link",
            html_path,
            href,
            f"Cannot decode built HTML link: {exc}",
        )
    if link_mode == "file" and _is_file_directory_url(path):
        return _issue(
            "file_directory_url",
            html_path,
            href,
            "Directory-style URL is not direct-file-safe.",
        )

    for candidate in _candidate_targets(
        html_path, path, root=root, link_mode=link_mode
    ):
        try:
            candidate.relative_to(root)
        except ValueError:
            return _issue(
                "unsafe_built_html_link",
                html_path,
                href,
                f"Built HTML link escapes built site directory: {href}",
            )
        if candidate.is_file():
            return None

    return _issue(
        "missing_built_html_target",
        html_path,
        href,
        f"Built HTML link target does not exist: {href}",
    )


def _candidate_targets(
    html_path: Path,
    path: str,
    *,
    root: Path,
    link_mode: str,
) -> Iterable[Path]:
    base_dir = root if path.startswith("/") else html_path.parent
    rel_path = path.lstrip("/")
    if link_mode == "file":
        yield (base_dir / rel_path).resolve()
        return

    if path.endswith("/"):
        yield (base_dir / rel_path / "index.html").resolve()
        return

    exact = (base_dir / rel_path).resolve()
    yield exact
    suffix = posixpath.splitext(rel_path)[1]
    if not suffix:
        yield (base_dir / rel_path / "index.html").resolve()
        yield (base_dir / f"{rel_path}.html").resolve()


def _is_file_directory_url(path: str) -> bool:
    return path.endswith("/") or path in {".", ".."}


def _issue(
    category: str,
    html_path: Path,
    href: str,
    message: str,
) -> dict[str, str]:
    return {
        "category": category,
        "path": str(html_path),
        "target": href,
        "message": message,
    }
