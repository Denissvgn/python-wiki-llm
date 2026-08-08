"""Lossless, deterministic observations of links in canonical Markdown.

The collector is pure over already discovered wiki pages, their supplied
Markdown content, and an already evaluated set of asset paths.  It performs no
filesystem reads or source scans.  Mapping observations to persisted
``links_to`` relationships, including page hashes, belongs to the knowledge
index builder.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from enum import Enum
from urllib.parse import SplitResult, unquote, urlsplit

from .knowledge_model import (
    RelationshipLocation,
    Resolution,
    TargetClass,
)
from .validation import (
    contains_control_character as shared_contains_control_character,
    require_repository_relative_path,
)
from .wiki_media import (
    MarkdownLinkTarget,
    contains_uri_authority_userinfo,
    is_assets_path,
    iter_markdown_link_targets,
    iter_mermaid_click_targets,
    local_link_path,
    mask_fenced_code_blocks,
    media_type_for_path,
)
from .wiki_surface import (
    PageKind,
    WikiSurfaceError,
    WikiSurfacePage,
)
from .wiki_surface import canonical_path as wiki_canonical_path
from .wiki_surface import mcp_uri as wiki_mcp_uri

_MALFORMED_PERCENT_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_URI_CHARS_RE = re.compile(r"[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*")
_MAX_LOCATION_OFFSET = (2**63) - 1


class KnowledgeLinkError(ValueError):
    """Field-specific invalid input at the pure link-collection boundary."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class LinkSyntax(str, Enum):
    """Source syntax that produced one Markdown-owned observation."""

    MARKDOWN = "markdown"
    MARKDOWN_IMAGE = "markdown-image"
    MERMAID_CLICK = "mermaid-click"


@dataclass(frozen=True)
class LinkObservation:
    """One lossless link occurrence and its deterministic resolution outcome."""

    source_locator: str
    source_canonical_path: str
    raw_target: str
    normalized_target: str
    label: str
    location: RelationshipLocation
    target_class: TargetClass
    resolution: Resolution
    resolved_canonical_path: str | None = None
    external_uri: str | None = None
    syntax: LinkSyntax = LinkSyntax.MARKDOWN

    @property
    def source_page(self) -> str:
        """Compatibility shorthand for the source canonical path."""

        return self.source_canonical_path

    @property
    def canonical_path(self) -> str | None:
        """Return the resolved canonical route, when one exists."""

        return self.resolved_canonical_path

    @property
    def resolved_canonical_route(self) -> str | None:
        """Compatibility alias for the resolved canonical page path."""

        return self.resolved_canonical_path

    @property
    def start(self) -> int:
        return self.location.start

    @property
    def end(self) -> int:
        return self.location.end


# The longer name is retained as a discoverable compatibility alias.
KnowledgeLinkObservation = LinkObservation


@dataclass(frozen=True)
class _TargetOutcome:
    target_class: TargetClass
    resolution: Resolution
    canonical_path: str | None = None
    external_uri: str | None = None


@dataclass(frozen=True)
class _PageRegistry:
    routes: Mapping[str, tuple[WikiSurfacePage, ...]]
    locators: Mapping[str, tuple[WikiSurfacePage, ...]]


def collect_link_observations(
    pages: Sequence[WikiSurfacePage],
    content_by_page: Mapping[str, str],
    *,
    existing_asset_paths: AbstractSet[str] = frozenset(),
) -> tuple[LinkObservation, ...]:
    """Collect every supported link occurrence without deduplication or limits.

    ``content_by_page`` must have exact canonical-path parity with ``pages``.
    ``existing_asset_paths`` must come from the caller's already evaluated
    wiki/asset input; this function never rescans the filesystem.
    """

    registry, ordered_pages = _build_page_registry(pages)
    content = _validate_page_content(content_by_page, registry)
    assets = _validate_asset_paths(existing_asset_paths, registry)

    observations: list[LinkObservation] = []
    for page in ordered_pages:
        page_content = content[page.relative_path]
        parsed: list[tuple[MarkdownLinkTarget, LinkSyntax]] = [
            (link, LinkSyntax.MARKDOWN_IMAGE if link.is_image else LinkSyntax.MARKDOWN)
            for link in iter_markdown_link_targets(
                mask_fenced_code_blocks(page_content)
            )
        ]
        parsed.extend(
            (link, LinkSyntax.MERMAID_CLICK)
            for link in iter_mermaid_click_targets(page_content)
        )
        parsed.sort(
            key=lambda item: (
                item[0].start,
                item[0].end,
                item[1].value,
                item[0].raw_target,
                item[0].label,
            )
        )
        for link, syntax in parsed:
            observation = _build_observation(
                page,
                link,
                syntax,
                registry,
                assets,
            )
            if observation is not None:
                observations.append(observation)

    observations.sort(
        key=lambda observation: (
            observation.source_canonical_path.casefold(),
            observation.source_canonical_path,
            observation.location.start,
            observation.location.end,
            observation.syntax.value,
            observation.raw_target,
            observation.label,
            observation.source_locator,
        )
    )
    return tuple(observations)


def _build_page_registry(
    pages: Sequence[WikiSurfacePage],
) -> tuple[_PageRegistry, tuple[WikiSurfacePage, ...]]:
    if isinstance(pages, (str, bytes)) or not isinstance(pages, Sequence):
        raise KnowledgeLinkError("pages", "must be a sequence of wiki surface pages")

    route_lists: dict[str, list[WikiSurfacePage]] = {}
    locator_lists: dict[str, list[WikiSurfacePage]] = {}
    validated: list[WikiSurfacePage] = []
    for index, page in enumerate(pages):
        field = f"pages[{index}]"
        if not isinstance(page, WikiSurfacePage):
            raise KnowledgeLinkError(field, "must be a WikiSurfacePage")
        if not isinstance(page.kind, PageKind):
            raise KnowledgeLinkError(f"{field}.kind", "must be a PageKind")
        if not isinstance(page.page_id, str) or not page.page_id:
            raise KnowledgeLinkError(f"{field}.page_id", "must be a non-empty string")
        _canonical_relative_path(page.relative_path, f"{field}.relative_path")
        _page_locator(page.mcp_uri, f"{field}.mcp_uri")
        expected_path, expected_locator = _expected_page_coordinates(page, field)
        if page.relative_path != expected_path:
            raise KnowledgeLinkError(
                f"{field}.relative_path",
                f"must match page kind and id ({expected_path!r})",
            )
        if page.mcp_uri != expected_locator:
            raise KnowledgeLinkError(
                f"{field}.mcp_uri",
                "must match page kind and id",
            )
        route_lists.setdefault(page.relative_path, []).append(page)
        locator_lists.setdefault(page.mcp_uri, []).append(page)
        validated.append(page)

    ordered = tuple(
        sorted(
            validated,
            key=lambda page: (
                page.relative_path.casefold(),
                page.relative_path,
                page.mcp_uri,
            ),
        )
    )
    return (
        _PageRegistry(
            routes={
                route: tuple(candidates)
                for route, candidates in sorted(route_lists.items())
            },
            locators={
                locator: tuple(candidates)
                for locator, candidates in sorted(locator_lists.items())
            },
        ),
        ordered,
    )


def _validate_page_content(
    content_by_page: Mapping[str, str],
    registry: _PageRegistry,
) -> dict[str, str]:
    if not isinstance(content_by_page, Mapping):
        raise KnowledgeLinkError("content_by_page", "must be a mapping")
    for key in content_by_page:
        if not isinstance(key, str):
            raise KnowledgeLinkError(
                "content_by_page", "must use string canonical page paths"
            )

    expected = set(registry.routes)
    actual = set(content_by_page)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        raise KnowledgeLinkError(
            "content_by_page",
            f"is missing canonical page content for {missing[0]!r}",
        )
    if extra:
        raise KnowledgeLinkError(
            "content_by_page",
            f"contains content for unknown canonical page {extra[0]!r}",
        )

    result: dict[str, str] = {}
    for path in sorted(actual):
        value = content_by_page[path]
        if not isinstance(value, str):
            raise KnowledgeLinkError(
                f"content_by_page.{path}", "must be a Markdown string"
            )
        result[path] = value
    return result


def _validate_asset_paths(
    paths: AbstractSet[str],
    registry: _PageRegistry,
) -> frozenset[str]:
    if isinstance(paths, (str, bytes)) or not isinstance(paths, AbstractSet):
        raise KnowledgeLinkError(
            "existing_asset_paths", "must be a set of canonical asset paths"
        )
    validated = set()
    for path in paths:
        if not isinstance(path, str):
            raise KnowledgeLinkError(
                "existing_asset_paths", "must contain only string paths"
            )
        _canonical_relative_path(path, "existing_asset_paths")
        if path in registry.routes:
            raise KnowledgeLinkError(
                "existing_asset_paths",
                f"must not collide with canonical page route {path!r}",
            )
        if posixpath.splitext(path)[1].casefold() == ".md" and not is_assets_path(path):
            raise KnowledgeLinkError(
                "existing_asset_paths",
                "Markdown paths outside the assets namespace are concept routes",
            )
        validated.add(path)
    return frozenset(validated)


def _build_observation(
    page: WikiSurfacePage,
    link: MarkdownLinkTarget,
    syntax: LinkSyntax,
    registry: _PageRegistry,
    existing_assets: frozenset[str],
) -> LinkObservation | None:
    if link.start < 0 or link.end <= link.start or link.end > _MAX_LOCATION_OFFSET:
        raise KnowledgeLinkError(
            f"content_by_page.{page.relative_path}",
            "contains a link outside the supported character-offset range",
        )
    if contains_uri_authority_userinfo(link.raw_target) or (
        contains_uri_authority_userinfo(link.target)
    ):
        # Authority userinfo is credential-bearing. The complete observation is
        # omitted instead of emitting a redacted pseudo-record.
        return None

    outcome = _classify_target(
        source_path=page.relative_path,
        normalized_target=link.target,
        is_image=link.is_image,
        registry=registry,
        existing_assets=existing_assets,
    )
    if outcome.external_uri is not None and contains_uri_authority_userinfo(
        outcome.external_uri
    ):
        return None

    return LinkObservation(
        source_locator=page.mcp_uri,
        source_canonical_path=page.relative_path,
        raw_target=link.raw_target,
        normalized_target=link.target,
        label=link.label,
        location=RelationshipLocation(start=link.start, end=link.end),
        target_class=outcome.target_class,
        resolution=outcome.resolution,
        resolved_canonical_path=outcome.canonical_path,
        external_uri=outcome.external_uri,
        syntax=syntax,
    )


def _classify_target(
    *,
    source_path: str,
    normalized_target: str,
    is_image: bool,
    registry: _PageRegistry,
    existing_assets: frozenset[str],
) -> _TargetOutcome:
    if (
        not normalized_target
        or _contains_control_character(normalized_target)
        or _MALFORMED_PERCENT_RE.search(normalized_target)
    ):
        return _malformed()
    if normalized_target.startswith("#"):
        return _TargetOutcome(TargetClass.ANCHOR, Resolution.RESOLVED)
    if _WINDOWS_ABSOLUTE_RE.match(normalized_target):
        return _malformed()

    try:
        parsed = urlsplit(normalized_target)
        port = parsed.port
    except ValueError:
        return _malformed()

    scheme = parsed.scheme.casefold()
    if scheme == "llm-wiki":
        if not _valid_link_locator(normalized_target, parsed, port):
            return _malformed()
        locator = normalized_target.partition("#")[0]
        candidates = registry.locators.get(locator, ())
        return _concept_candidates(candidates)

    if parsed.scheme:
        if not _valid_external_uri(normalized_target, parsed, port):
            return _malformed()
        target_class = TargetClass.MAIL if scheme == "mailto" else TargetClass.EXTERNAL
        return _TargetOutcome(
            target_class,
            Resolution.EXTERNAL,
            external_uri=normalized_target,
        )

    if parsed.netloc:
        # Protocol-relative values cannot populate v1's absolute external_uri
        # coordinate.  Do not invent a scheme.
        return _TargetOutcome(TargetClass.UNKNOWN, Resolution.UNRESOLVED)
    if normalized_target.startswith(("/", "\\")):
        return _malformed()

    local_path = local_link_path(normalized_target)
    if (
        local_path is None
        or posixpath.isabs(local_path)
        or _WINDOWS_ABSOLUTE_RE.match(local_path)
        or _contains_control_character(local_path)
    ):
        return _malformed()
    candidate = posixpath.normpath(
        posixpath.join(posixpath.dirname(source_path), local_path)
    )
    if candidate == ".." or candidate.startswith("../") or posixpath.isabs(candidate):
        return _malformed()

    is_asset = (
        is_image
        or candidate in existing_assets
        or is_assets_path(candidate)
        or media_type_for_path(local_path) is not None
    )
    if is_asset:
        resolution = (
            Resolution.RESOLVED
            if candidate in existing_assets
            else Resolution.UNRESOLVED
        )
        return _TargetOutcome(TargetClass.ASSET, resolution)

    candidates = registry.routes.get(candidate, ())
    if candidates:
        return _concept_candidates(candidates)
    if posixpath.splitext(candidate)[1].casefold() == ".md":
        return _TargetOutcome(TargetClass.CONCEPT, Resolution.UNRESOLVED)
    return _TargetOutcome(TargetClass.UNKNOWN, Resolution.UNRESOLVED)


def _concept_candidates(
    candidates: Sequence[WikiSurfacePage],
) -> _TargetOutcome:
    if len(candidates) == 1:
        return _TargetOutcome(
            TargetClass.CONCEPT,
            Resolution.RESOLVED,
            canonical_path=candidates[0].relative_path,
        )
    if len(candidates) > 1:
        return _TargetOutcome(TargetClass.CONCEPT, Resolution.AMBIGUOUS)
    return _TargetOutcome(TargetClass.CONCEPT, Resolution.UNRESOLVED)


def _malformed() -> _TargetOutcome:
    return _TargetOutcome(TargetClass.MALFORMED, Resolution.UNRESOLVED)


def _expected_page_coordinates(
    page: WikiSurfacePage,
    field: str,
) -> tuple[str, str]:
    try:
        return (
            wiki_canonical_path(page.kind, page.page_id),
            wiki_mcp_uri(page.kind, page.page_id),
        )
    except WikiSurfaceError:
        try:
            expected_path = wiki_canonical_path(page.kind)
            expected_locator = wiki_mcp_uri(page.kind)
        except WikiSurfaceError as exc:
            raise KnowledgeLinkError(
                field, "contains an invalid page kind or id"
            ) from exc
        if page.page_id != page.kind.value:
            raise KnowledgeLinkError(
                f"{field}.page_id",
                f"must be {page.kind.value!r} for a singleton page kind",
            )
        return expected_path, expected_locator


def _valid_external_uri(
    value: str,
    parsed: SplitResult,
    port: int | None,
) -> bool:
    if (
        not parsed.scheme
        or parsed.scheme.casefold() == "llm-wiki"
        or "\\" in value
        or any(char.isspace() or ord(char) >= 128 for char in value)
        or _URI_CHARS_RE.fullmatch(value) is None
    ):
        return False
    uses_authority = value[len(parsed.scheme) :].startswith("://")
    requires_authority = parsed.scheme.casefold() in {"http", "https", "ftp", "ftps"}
    if (uses_authority or requires_authority) and (
        not parsed.netloc or parsed.hostname is None
    ):
        return False
    # Accessing parsed.port above already rejects malformed/non-numeric ports.
    _ = port
    return True


def is_valid_external_link_uri(value: str) -> bool:
    """Return whether *value* is a supported absolute external link URI."""

    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    return _valid_external_uri(value, parsed, port)


def _valid_link_locator(
    value: str,
    parsed: SplitResult,
    port: int | None,
) -> bool:
    if (
        not parsed.netloc
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.query
        or "\\" in value
        or any(char.isspace() for char in value)
        or _contains_control_character(value)
        or _MALFORMED_PERCENT_RE.search(value)
    ):
        return False
    for segment in parsed.path.split("/")[1:] if parsed.path else ():
        decoded = unquote(segment)
        if (
            not segment
            or decoded in {".", ".."}
            or "/" in decoded
            or "\\" in decoded
            or any(char.isspace() for char in decoded)
            or _contains_control_character(decoded)
        ):
            return False
    return True


def is_valid_link_locator_target(value: str) -> bool:
    """Return whether *value* is a supported ``llm-wiki:`` link target."""

    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    return parsed.scheme == "llm-wiki" and _valid_link_locator(
        value,
        parsed,
        port,
    )


def _canonical_relative_path(value: str, field: str) -> str:
    return require_repository_relative_path(
        value,
        text_error=KnowledgeLinkError(field, "must be a non-empty string"),
        posix_error=KnowledgeLinkError(
            field, "must be a repository-relative POSIX path"
        ),
        normalized_error=KnowledgeLinkError(
            field, "must be normalized without empty or dot segments"
        ),
        control_error=KnowledgeLinkError(
            field, "must be a repository-relative POSIX path"
        ),
        reject_delete_character=True,
    )


def _contains_control_character(value: str) -> bool:
    return shared_contains_control_character(
        value,
        reject_delete_character=True,
    )


def _page_locator(value: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise KnowledgeLinkError(field, "must be a non-empty llm-wiki locator")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise KnowledgeLinkError(field, "must be a valid llm-wiki locator") from exc
    if (
        parsed.scheme != "llm-wiki"
        or not _valid_link_locator(value, parsed, port)
        or parsed.fragment
    ):
        raise KnowledgeLinkError(field, "must be a normalized llm-wiki locator")
    return value
