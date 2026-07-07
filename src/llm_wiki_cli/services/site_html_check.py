"""Built static-site HTML link validation."""

from __future__ import annotations

import posixpath
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Iterable, Optional, Union
from urllib.parse import unquote, urlsplit

from .wiki_media import split_srcset_candidates


SUPPORTED_LINK_MODES = frozenset({"http", "file"})
_IGNORED_SCHEMES = frozenset({"http", "https", "mailto", "tel", "data", "javascript"})
_HREF_TAGS = frozenset({"a", "area", "link"})
_MEDIA_SRC_TAGS = frozenset({"img", "video", "source"})


class _HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.media_srcs: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, Optional[str]]],
    ) -> None:
        if tag.casefold() not in _HREF_TAGS:
            if tag.casefold() not in _MEDIA_SRC_TAGS:
                return
            for name, value in attrs:
                if name.casefold() == "src" and value is not None:
                    self.media_srcs.append(value.strip())
                if name.casefold() == "srcset" and value is not None:
                    self.media_srcs.extend(split_srcset_candidates(value))
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
        for src in parser.media_srcs:
            issue = _check_media_src(html_path, src, root=root_resolved)
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
    return _resolve_local_html_target(
        html_path,
        href,
        root=root,
        subject="link",
        missing_category="missing_built_html_target",
        candidate_paths=lambda path: _candidate_targets(
            html_path, path, root=root, link_mode=link_mode
        ),
        precheck=(
            lambda path: (
                _issue(
                    "file_directory_url",
                    html_path,
                    href,
                    "Directory-style URL is not direct-file-safe.",
                )
                if link_mode == "file" and _is_file_directory_url(path)
                else None
            )
        ),
    )


def _check_media_src(
    html_path: Path,
    src: str,
    *,
    root: Path,
) -> Optional[dict[str, str]]:
    return _resolve_local_html_target(
        html_path,
        src,
        root=root,
        subject="media source",
        missing_category="missing_built_media_target",
        candidate_paths=lambda path: [_media_candidate(html_path, path, root=root)],
    )


def _resolve_local_html_target(
    html_path: Path,
    raw_target: str,
    *,
    root: Path,
    subject: str,
    missing_category: str,
    candidate_paths: Callable[[str], Iterable[Path]],
    precheck: Optional[Callable[[str], Optional[dict[str, str]]]] = None,
) -> Optional[dict[str, str]]:
    if not raw_target or raw_target.startswith("#"):
        return None
    if "\x00" in raw_target:
        return _issue(
            "malformed_built_html_link",
            html_path,
            raw_target,
            f"Built HTML {subject} contains a NUL byte.",
        )
    try:
        parsed = urlsplit(raw_target)
    except ValueError as exc:
        return _issue(
            "malformed_built_html_link",
            html_path,
            raw_target,
            f"Cannot parse built HTML {subject}: {exc}",
        )
    scheme = parsed.scheme.casefold()
    if scheme in _IGNORED_SCHEMES or parsed.netloc:
        return None
    if scheme:
        return _issue(
            "malformed_built_html_link",
            html_path,
            raw_target,
            f"Unsupported built HTML {subject} scheme: {scheme}",
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
            raw_target,
            f"Cannot decode built HTML {subject}: {exc}",
        )
    if precheck is not None:
        issue = precheck(path)
        if issue is not None:
            return issue
    for candidate in candidate_paths(path):
        try:
            candidate.relative_to(root)
        except ValueError:
            return _issue(
                "unsafe_built_html_link",
                html_path,
                raw_target,
                f"Built HTML {subject} escapes built site directory: {raw_target}",
            )
        if candidate.is_file():
            return None
    return _issue(
        missing_category,
        html_path,
        raw_target,
        f"Built HTML {subject} target does not exist: {raw_target}",
    )


def _media_candidate(html_path: Path, path: str, *, root: Path) -> Path:
    base_dir = root if path.startswith("/") else html_path.parent
    return (base_dir / path.lstrip("/")).resolve()


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
