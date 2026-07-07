"""Media reference parsing for wiki pages and agent-owned assets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Mapping, Optional, Union
from urllib.parse import unquote, urlsplit


IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"})
VIDEO_EXTENSIONS = frozenset({".mp4", ".webm"})
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
DEFAULT_MEDIA_SIZE_WARN_BYTES = 2 * 1024 * 1024

_MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((.+?)\)")
_MARKDOWN_PLAIN_LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\((.+?)\)")
_MARKDOWN_TITLE_RE = re.compile(
    r"^(?P<target><[^>]+>|[^\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*$"
)
_IGNORED_SCHEMES = frozenset({"http", "https", "mailto", "tel", "data", "javascript"})


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
class AssetIndex:
    counts: dict[str, object]
    by_page: dict[str, list[str]]
    referenced: list[str]
    unreferenced: list[str]
    expected_pages: dict[str, Optional[str]]


class _HtmlMediaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str, Optional[str], bool]] = []

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
        if src is None:
            return
        alt = values.get("alt")
        self.references.append((tag_name, src.strip(), alt, tag_name == "img"))


def normalize_markdown_link_target(raw_target: str) -> str:
    """Return a markdown link target without optional title text."""
    target = raw_target.strip()
    match = _MARKDOWN_TITLE_RE.match(target)
    if match:
        target = match.group("target").strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    return target


def local_link_path(raw_target: str) -> Optional[str]:
    """Return the path component for a local link target, or None if ignored."""
    target = normalize_markdown_link_target(raw_target)
    if not target or target.startswith("#") or "\x00" in target:
        return None
    try:
        parsed = urlsplit(target)
    except ValueError:
        return target.partition("#")[0] or None
    if parsed.scheme.casefold() in _IGNORED_SCHEMES or parsed.netloc:
        return None
    if parsed.scheme:
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
    references: list[MediaReference] = []
    for regex, source, image_embed in (
        (_MARKDOWN_IMAGE_RE, "markdown", True),
        (_MARKDOWN_PLAIN_LINK_RE, "markdown_link", False),
    ):
        for match in regex.finditer(content):
            raw_target = match.group(2)
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
                    alt_text=match.group(1).strip() if image_embed else None,
                    requires_alt=image_embed and media_type == "image",
                )
            )

    parser = _HtmlMediaParser()
    parser.feed(content)
    for _tag, raw_target, alt, requires_alt in parser.references:
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
                source="html",
                alt_text=alt.strip() if alt is not None else None,
                requires_alt=requires_alt,
            )
        )
    return references


def build_asset_index(
    wiki_dir: Union[str, Path],
    content_by_page: Optional[Mapping[str, str]] = None,
) -> AssetIndex:
    wiki = Path(wiki_dir)
    content = (
        dict(content_by_page) if content_by_page is not None else _read_pages(wiki)
    )
    by_page: dict[str, set[str]] = {}
    referenced_assets: set[str] = set()
    for page_rel, page_content in content.items():
        page = wiki / Path(page_rel)
        assets = set()
        for reference in collect_media_references(page, page_rel, page_content):
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
    by_media_type = {"image": 0, "video": 0}
    for asset in asset_paths:
        media_type = media_type_for_path(asset)
        if media_type is not None:
            by_media_type[media_type] += 1

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
    rel_posix = rel.as_posix()
    if rel_posix.split("/", 1)[0] != "assets":
        return None
    return rel_posix


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
        if media_type_for_path(rel) is not None:
            paths.append(rel)
    return sorted(paths, key=lambda value: (value.casefold(), value))
