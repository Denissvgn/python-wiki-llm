"""Focused contract tests for KNOW-105 lossless Markdown link collection."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

import pytest

from llm_wiki_cli.services.knowledge_links import (
    KnowledgeLinkError,
    KnowledgeLinkObservation,
    LinkObservation,
    LinkSyntax,
    collect_link_observations,
)
from llm_wiki_cli.services.knowledge_model import Resolution, TargetClass
from llm_wiki_cli.services.wiki_media import mask_fenced_code_blocks
from llm_wiki_cli.services.wiki_surface import (
    PageKind,
    SurfaceRole,
    WikiSurfacePage,
)
from llm_wiki_cli.services.wiki_surface import mcp_uri as wiki_mcp_uri

_VIRTUAL_WIKI = Path("/virtual/wiki-that-must-not-be-read")


def _page(
    relative_path: str,
    *,
    locator: str | None = None,
    physical_path: Path | None = None,
) -> WikiSurfacePage:
    directory = relative_path.partition("/")[0]
    kind = {
        "entities": PageKind.ENTITIES,
        "guides": PageKind.GUIDES,
        "modules": PageKind.MODULES,
    }.get(directory, PageKind.GUIDES)
    page_id = Path(relative_path).stem
    return WikiSurfacePage(
        kind=kind,
        page_id=page_id,
        label="Fixture page",
        path=physical_path or (_VIRTUAL_WIKI / relative_path),
        relative_path=relative_path,
        mcp_uri=locator or wiki_mcp_uri(kind, page_id),
        obsidian_mirror_dir="Guides",
        role=SurfaceRole.SEMANTIC,
    )


def _collect(
    markdown: str,
    *,
    source: WikiSurfacePage | None = None,
    targets: tuple[WikiSurfacePage, ...] = (),
    assets: frozenset[str] = frozenset(),
) -> tuple[WikiSurfacePage, tuple[LinkObservation, ...]]:
    source_page = source or _page("guides/source.md")
    pages = (source_page, *targets)
    content_by_page = {page.relative_path: "" for page in pages}
    content_by_page[source_page.relative_path] = markdown
    return source_page, collect_link_observations(
        pages,
        content_by_page,
        existing_asset_paths=assets,
    )


def _by_label(
    observations: tuple[LinkObservation, ...],
) -> dict[str, LinkObservation]:
    return {observation.label: observation for observation in observations}


def _assert_exact_source_slice(
    markdown: str,
    observation: LinkObservation,
    expected_syntax: str,
) -> None:
    start = markdown.index(expected_syntax)
    assert observation.location.start == start
    assert observation.location.end == start + len(expected_syntax)
    assert markdown[observation.start : observation.end] == expected_syntax
    assert observation.location.extensions == {}


def test_link_observation_public_alias_and_syntax_values_are_stable() -> None:
    assert KnowledgeLinkObservation is LinkObservation
    assert LinkSyntax.MARKDOWN.value == "markdown"
    assert LinkSyntax.MARKDOWN_IMAGE.value == "markdown-image"
    assert LinkSyntax.MERMAID_CLICK.value == "mermaid-click"


def test_collects_the_lossless_outcome_matrix_with_exact_coordinates() -> None:
    target = _page(
        "entities/User.md",
        locator="llm-wiki://entities/User",
    )
    markdown_by_label = {
        "User": "[User](../entities/User.md)",
        "Missing": "[Missing](../entities/Missing.md)",
        "Web": "[Web](https://example.invalid/reference?q=1#details)",
        "FTP": "[FTP](ftp://downloads.example.invalid/archive.tar)",
        "Mail": "[Mail](mailto:user@example.invalid)",
        "Anchor": "[Anchor](#details)",
        "Asset": "[Asset](../assets/manual.pdf)",
        "Screen": "![Screen](../assets/screen.png)",
        "Missing image": "[Missing image](../assets/missing.webp)",
        "Empty": "[Empty]()",
        "Bad HTTP": "[Bad HTTP](https:///missing-host)",
        "Unknown": "[Unknown](notes.txt)",
        "Protocol relative": "[Protocol relative](//cdn.example.invalid/file.js)",
    }
    markdown = "\n".join(markdown_by_label.values())
    source, observations = _collect(
        markdown,
        targets=(target,),
        assets=frozenset(
            {
                "assets/manual.pdf",
                "assets/screen.png",
            }
        ),
    )

    assert len(observations) == len(markdown_by_label)
    by_label = _by_label(observations)
    expected = {
        "User": (
            "../entities/User.md",
            "../entities/User.md",
            TargetClass.CONCEPT,
            Resolution.RESOLVED,
            "entities/User.md",
            None,
            LinkSyntax.MARKDOWN,
        ),
        "Missing": (
            "../entities/Missing.md",
            "../entities/Missing.md",
            TargetClass.CONCEPT,
            Resolution.UNRESOLVED,
            None,
            None,
            LinkSyntax.MARKDOWN,
        ),
        "Web": (
            "https://example.invalid/reference?q=1#details",
            "https://example.invalid/reference?q=1#details",
            TargetClass.EXTERNAL,
            Resolution.EXTERNAL,
            None,
            "https://example.invalid/reference?q=1#details",
            LinkSyntax.MARKDOWN,
        ),
        "FTP": (
            "ftp://downloads.example.invalid/archive.tar",
            "ftp://downloads.example.invalid/archive.tar",
            TargetClass.EXTERNAL,
            Resolution.EXTERNAL,
            None,
            "ftp://downloads.example.invalid/archive.tar",
            LinkSyntax.MARKDOWN,
        ),
        "Mail": (
            "mailto:user@example.invalid",
            "mailto:user@example.invalid",
            TargetClass.MAIL,
            Resolution.EXTERNAL,
            None,
            "mailto:user@example.invalid",
            LinkSyntax.MARKDOWN,
        ),
        "Anchor": (
            "#details",
            "#details",
            TargetClass.ANCHOR,
            Resolution.RESOLVED,
            None,
            None,
            LinkSyntax.MARKDOWN,
        ),
        "Asset": (
            "../assets/manual.pdf",
            "../assets/manual.pdf",
            TargetClass.ASSET,
            Resolution.RESOLVED,
            None,
            None,
            LinkSyntax.MARKDOWN,
        ),
        "Screen": (
            "../assets/screen.png",
            "../assets/screen.png",
            TargetClass.ASSET,
            Resolution.RESOLVED,
            None,
            None,
            LinkSyntax.MARKDOWN_IMAGE,
        ),
        "Missing image": (
            "../assets/missing.webp",
            "../assets/missing.webp",
            TargetClass.ASSET,
            Resolution.UNRESOLVED,
            None,
            None,
            LinkSyntax.MARKDOWN,
        ),
        "Empty": (
            "",
            "",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
            None,
            LinkSyntax.MARKDOWN,
        ),
        "Bad HTTP": (
            "https:///missing-host",
            "https:///missing-host",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
            None,
            LinkSyntax.MARKDOWN,
        ),
        "Unknown": (
            "notes.txt",
            "notes.txt",
            TargetClass.UNKNOWN,
            Resolution.UNRESOLVED,
            None,
            None,
            LinkSyntax.MARKDOWN,
        ),
        "Protocol relative": (
            "//cdn.example.invalid/file.js",
            "//cdn.example.invalid/file.js",
            TargetClass.UNKNOWN,
            Resolution.UNRESOLVED,
            None,
            None,
            LinkSyntax.MARKDOWN,
        ),
    }

    for label, fields in expected.items():
        observation = by_label[label]
        (
            raw_target,
            normalized_target,
            target_class,
            resolution,
            canonical_path,
            external_uri,
            syntax,
        ) = fields
        assert observation.source_locator == source.mcp_uri
        assert observation.source_canonical_path == "guides/source.md"
        assert observation.source_page == "guides/source.md"
        assert observation.raw_target == raw_target
        assert observation.normalized_target == normalized_target
        assert observation.target_class is target_class
        assert observation.resolution is resolution
        assert observation.resolved_canonical_path == canonical_path
        assert observation.canonical_path == canonical_path
        assert observation.resolved_canonical_route == canonical_path
        assert observation.external_uri == external_uri
        assert observation.syntax is syntax
        _assert_exact_source_slice(
            markdown,
            observation,
            markdown_by_label[label],
        )


def test_normalization_is_lossless_while_route_lookup_is_portable() -> None:
    targets = (
        _page("guides/setup(1).md"),
        _page(
            "entities/User.md",
            locator="llm-wiki://entities/User",
        ),
    )
    markdown_by_label = {
        "Angle": "[Angle](<My Guide.md>)",
        "Percent space": "[Percent space](My%20Guide.md)",
        "Fragment": "[Fragment](../entities/User.md#usage)",
        "Query and fragment": (
            "[Query and fragment](../entities/User.md?view=full#usage)"
        ),
        "Backslash": r"[Backslash](..\entities\User.md)",
        "Title": '[Title](setup(1).md "Setup guide")',
        "Encoded parentheses": "[Encoded parentheses](setup%281%29.md)",
        "Local at": "[Local at](user@example.invalid.md)",
        "Invalid percent": "[Invalid percent](missing%2.md)",
        "Encoded NUL": "[Encoded NUL](missing%00.md)",
        "Encoded newline": "[Encoded newline](missing%0Aname.md)",
        "Encoded tab": "[Encoded tab](missing%09name.md)",
        "Encoded DEL": "[Encoded DEL](missing%7Fname.md)",
        "Escaped space": r"[Escaped space](My\ Guide.md)",
        "Traversal": "[Traversal](../../outside.md)",
        "Encoded traversal": ("[Encoded traversal](%2e%2e/%2e%2e/outside.md)"),
        "Absolute": "[Absolute](/outside.md)",
        "Windows absolute": r"[Windows absolute](C:\outside.md)",
        "Encoded Windows absolute": ("[Encoded Windows absolute](C%3A%5Coutside.md)"),
    }
    markdown = "\n".join(markdown_by_label.values())
    _, observations = _collect(markdown, targets=targets)
    by_label = _by_label(observations)

    expected = {
        "Angle": (
            "<My Guide.md>",
            "My Guide.md",
            TargetClass.CONCEPT,
            Resolution.UNRESOLVED,
            None,
        ),
        "Percent space": (
            "My%20Guide.md",
            "My%20Guide.md",
            TargetClass.CONCEPT,
            Resolution.UNRESOLVED,
            None,
        ),
        "Fragment": (
            "../entities/User.md#usage",
            "../entities/User.md#usage",
            TargetClass.CONCEPT,
            Resolution.RESOLVED,
            "entities/User.md",
        ),
        "Query and fragment": (
            "../entities/User.md?view=full#usage",
            "../entities/User.md?view=full#usage",
            TargetClass.CONCEPT,
            Resolution.RESOLVED,
            "entities/User.md",
        ),
        "Backslash": (
            r"..\entities\User.md",
            r"..\entities\User.md",
            TargetClass.CONCEPT,
            Resolution.RESOLVED,
            "entities/User.md",
        ),
        "Title": (
            'setup(1).md "Setup guide"',
            "setup(1).md",
            TargetClass.CONCEPT,
            Resolution.RESOLVED,
            "guides/setup(1).md",
        ),
        "Encoded parentheses": (
            "setup%281%29.md",
            "setup%281%29.md",
            TargetClass.CONCEPT,
            Resolution.RESOLVED,
            "guides/setup(1).md",
        ),
        "Local at": (
            "user@example.invalid.md",
            "user@example.invalid.md",
            TargetClass.CONCEPT,
            Resolution.UNRESOLVED,
            None,
        ),
        "Invalid percent": (
            "missing%2.md",
            "missing%2.md",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
        ),
        "Encoded NUL": (
            "missing%00.md",
            "missing%00.md",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
        ),
        "Encoded newline": (
            "missing%0Aname.md",
            "missing%0Aname.md",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
        ),
        "Encoded tab": (
            "missing%09name.md",
            "missing%09name.md",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
        ),
        "Encoded DEL": (
            "missing%7Fname.md",
            "missing%7Fname.md",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
        ),
        "Escaped space": (
            r"My\ Guide.md",
            r"My\ Guide.md",
            TargetClass.CONCEPT,
            Resolution.UNRESOLVED,
            None,
        ),
        "Traversal": (
            "../../outside.md",
            "../../outside.md",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
        ),
        "Encoded traversal": (
            "%2e%2e/%2e%2e/outside.md",
            "%2e%2e/%2e%2e/outside.md",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
        ),
        "Absolute": (
            "/outside.md",
            "/outside.md",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
        ),
        "Encoded Windows absolute": (
            "C%3A%5Coutside.md",
            "C%3A%5Coutside.md",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
        ),
        "Windows absolute": (
            r"C:\outside.md",
            r"C:\outside.md",
            TargetClass.MALFORMED,
            Resolution.UNRESOLVED,
            None,
        ),
    }

    assert set(by_label) == set(expected)
    for label, (
        raw_target,
        normalized_target,
        target_class,
        resolution,
        canonical_path,
    ) in expected.items():
        observation = by_label[label]
        assert observation.raw_target == raw_target
        assert observation.normalized_target == normalized_target
        assert observation.target_class is target_class
        assert observation.resolution is resolution
        assert observation.resolved_canonical_path == canonical_path
        _assert_exact_source_slice(
            markdown,
            observation,
            markdown_by_label[label],
        )


def test_exact_page_locators_resolve_without_losing_fragments() -> None:
    target = _page(
        "entities/User.md",
        locator="llm-wiki://entities/User",
    )
    markdown_by_label = {
        "Direct": "[Direct](llm-wiki://entities/User)",
        "Fragment": "[Fragment](llm-wiki://entities/User#usage)",
        "Missing": "[Missing](llm-wiki://entities/Missing)",
        "Query": "[Query](llm-wiki://entities/User?view=full)",
    }
    markdown = "\n".join(markdown_by_label.values())
    _, observations = _collect(markdown, targets=(target,))
    by_label = _by_label(observations)

    assert by_label["Direct"].target_class is TargetClass.CONCEPT
    assert by_label["Direct"].resolution is Resolution.RESOLVED
    assert by_label["Direct"].resolved_canonical_path == "entities/User.md"
    assert by_label["Fragment"].normalized_target == ("llm-wiki://entities/User#usage")
    assert by_label["Fragment"].resolution is Resolution.RESOLVED
    assert by_label["Fragment"].resolved_canonical_path == "entities/User.md"
    assert by_label["Missing"].target_class is TargetClass.CONCEPT
    assert by_label["Missing"].resolution is Resolution.UNRESOLVED
    assert by_label["Query"].target_class is TargetClass.MALFORMED
    assert by_label["Query"].resolution is Resolution.UNRESOLVED

    for label, source_syntax in markdown_by_label.items():
        _assert_exact_source_slice(markdown, by_label[label], source_syntax)


def test_fenced_code_mask_preserves_offsets_and_excludes_pseudo_links() -> None:
    target = _page(
        "entities/User.md",
        locator="llm-wiki://entities/User",
    )
    before = "[Before](../entities/User.md)"
    after = "[After](../entities/User.md#after)"
    markdown = (
        f"Ω {before}\r\n"
        "```python\r\n"
        "[Hidden](../entities/Hidden.md)\r\n"
        "```\r\n"
        "~~~text\n"
        "![Also hidden](../assets/hidden.png)\n"
        "~~~\n"
        f"終 {after}\n"
    )

    masked = mask_fenced_code_blocks(markdown)
    assert len(masked) == len(markdown)
    assert [index for index, character in enumerate(masked) if character in "\r\n"] == [
        index for index, character in enumerate(markdown) if character in "\r\n"
    ]
    assert masked.startswith(f"Ω {before}\r\n")
    assert masked.endswith(f"終 {after}\n")
    assert "Hidden" not in masked
    assert "Also hidden" not in masked

    _, observations = _collect(markdown, targets=(target,))
    assert [observation.label for observation in observations] == [
        "Before",
        "After",
    ]
    _assert_exact_source_slice(markdown, observations[0], before)
    _assert_exact_source_slice(markdown, observations[1], after)


def test_unterminated_non_mermaid_fence_excludes_the_remainder() -> None:
    target = _page(
        "entities/User.md",
        locator="llm-wiki://entities/User",
    )
    visible = "[Visible](../entities/User.md)"
    markdown = (
        f"{visible}\n"
        "```text\n"
        "[Hidden](../entities/User.md)\n"
        'click hidden "../entities/User.md"\n'
    )

    _, observations = _collect(markdown, targets=(target,))

    assert len(observations) == 1
    assert observations[0].label == "Visible"
    _assert_exact_source_slice(markdown, observations[0], visible)


def test_mermaid_clicks_have_separate_origin_and_original_coordinates() -> None:
    target = _page(
        "entities/User.md",
        locator="llm-wiki://entities/User",
    )
    markdown_link = "[Inline](../entities/User.md)"
    user_click = 'click user "../entities/User.md"'
    docs_click = 'click docs "https://docs.example.invalid/reference?q=1#top"'
    missing_click = 'click missing "../entities/Missing.md"'
    asset_click = 'click diagram "../assets/diagram.svg"'
    markdown = (
        f"{markdown_link}\r\n"
        'click outside "../entities/Outside.md"\r\n'
        "```python\r\n"
        'click python "../entities/Python.md"\r\n'
        "```\r\n"
        "~~~MeRmAiD\r\n"
        "flowchart LR\r\n"
        "[Pseudo](../entities/Pseudo.md)\r\n"
        f"  {user_click}\r\n"
        f"{docs_click}\r\n"
        f"{missing_click}\r\n"
        f"{asset_click}\r\n"
        "click callback doSomething\r\n"
        "click single '../entities/Single.md'\r\n"
        "~~~\r\n"
    )
    _, observations = _collect(
        markdown,
        targets=(target,),
        assets=frozenset({"assets/diagram.svg"}),
    )
    by_label = _by_label(observations)

    assert set(by_label) == {
        "Inline",
        "user",
        "docs",
        "missing",
        "diagram",
    }
    assert by_label["Inline"].syntax is LinkSyntax.MARKDOWN

    assert by_label["user"].syntax is LinkSyntax.MERMAID_CLICK
    assert by_label["user"].target_class is TargetClass.CONCEPT
    assert by_label["user"].resolution is Resolution.RESOLVED
    assert by_label["user"].resolved_canonical_path == "entities/User.md"

    assert by_label["docs"].syntax is LinkSyntax.MERMAID_CLICK
    assert by_label["docs"].target_class is TargetClass.EXTERNAL
    assert by_label["docs"].resolution is Resolution.EXTERNAL
    assert by_label["docs"].external_uri == (
        "https://docs.example.invalid/reference?q=1#top"
    )

    assert by_label["missing"].syntax is LinkSyntax.MERMAID_CLICK
    assert by_label["missing"].target_class is TargetClass.CONCEPT
    assert by_label["missing"].resolution is Resolution.UNRESOLVED

    assert by_label["diagram"].syntax is LinkSyntax.MERMAID_CLICK
    assert by_label["diagram"].target_class is TargetClass.ASSET
    assert by_label["diagram"].resolution is Resolution.RESOLVED

    for label, source_syntax in {
        "Inline": markdown_link,
        "user": user_click,
        "docs": docs_click,
        "missing": missing_click,
        "diagram": asset_click,
    }.items():
        _assert_exact_source_slice(markdown, by_label[label], source_syntax)


def test_unsupported_markdown_link_forms_remain_outside_the_slice() -> None:
    inline = "[Inline](../entities/User.md)"
    markdown = (
        f"{inline}\n"
        "[Reference][user]\n"
        "[user]: ../entities/User.md\n"
        "<https://example.invalid/autolink>\n"
        '<a href="../entities/User.md">HTML</a>\n'
        "[[entities/User]]\n"
    )
    target = _page(
        "entities/User.md",
        locator="llm-wiki://entities/User",
    )

    _, observations = _collect(markdown, targets=(target,))

    assert len(observations) == 1
    assert observations[0].label == "Inline"
    _assert_exact_source_slice(markdown, observations[0], inline)


def test_authority_userinfo_omits_the_complete_observation() -> None:
    credential_links = {
        "HTTP user": "[HTTP user](http://user@example.invalid/path)",
        "HTTPS password": ("[HTTPS password](https://user:pass@example.invalid/path)"),
        "FTP user": "[FTP user](ftp://user@example.invalid/archive)",
        "FTPS password": ("[FTPS password](ftps://user:pass@example.invalid/archive)"),
        "Protocol user": "[Protocol user](//user@example.invalid/path)",
        "Encoded user": ("[Encoded user](https://user%40name@example.invalid/path)"),
        "Malformed HTTPS user": ("[Malformed HTTPS user](https://user@[bad)"),
        "Malformed protocol user": ("[Malformed protocol user](//user@[bad)"),
        "Locator user": (
            "[Locator user](llm-wiki://user@example.invalid/entities/User)"
        ),
        "Credential title": (
            '[Credential title](docs.md "https://user:pass@example.invalid/path")'
        ),
        "Credential title text": (
            "[Credential title text]"
            '(docs.md "see https://user:pass@example.invalid/path")'
        ),
        "Credential parenthesized tail": (
            "[Credential parenthesized tail]"
            "(docs.md (https://user:pass@example.invalid/path))"
        ),
        "Credential malformed tail": (
            "[Credential malformed tail]"
            "(docs.md see https://user:pass@example.invalid/path)"
        ),
    }
    safe_links = {
        "Mail": "[Mail](mailto:user@example.invalid)",
        "Local at": "[Local at](user@example.invalid.md)",
        "Query at": ("[Query at](https://example.invalid/path?token=user:pass@host)"),
        "Path at": "[Path at](https://example.invalid/user@host)",
        "Fragment at": "[Fragment at](https://example.invalid/#user@host)",
        "Protocol safe": "[Protocol safe](//cdn.example.invalid/path)",
        "Safe title at": '[Safe title at](docs.md "user@example.invalid")',
        "Local double slash at": (
            "[Local double slash at](docs//user@example.invalid.md)"
        ),
        "Nested query URI": (
            "[Nested query URI]"
            "(https://example.invalid/?next=https://user@example.invalid/path)"
        ),
        "Nested query title URI": (
            "[Nested query title URI]"
            '(docs.md "see https://example.invalid/'
            '?next=https://user@example.invalid/path")'
        ),
    }
    credential_click = 'click secret "https://user:pass@example.invalid/path"'
    safe_click = 'click public "mailto:user@example.invalid"'
    markdown = (
        "\n".join((*credential_links.values(), *safe_links.values()))
        + "\n```mermaid\n"
        + credential_click
        + "\n"
        + safe_click
        + "\n```\n"
    )

    _, observations = _collect(markdown)
    by_label = _by_label(observations)

    assert set(by_label) == {*safe_links, "public"}
    assert not set(credential_links) & set(by_label)
    assert "secret" not in by_label
    assert all(
        "user:pass@example.invalid" not in observation.raw_target
        for observation in observations
    )

    assert by_label["Mail"].target_class is TargetClass.MAIL
    assert by_label["Local at"].target_class is TargetClass.CONCEPT
    assert by_label["Local at"].resolution is Resolution.UNRESOLVED
    assert by_label["Local at"].resolved_canonical_path is None
    assert by_label["Query at"].external_uri == (
        "https://example.invalid/path?token=user:pass@host"
    )
    assert by_label["Path at"].resolution is Resolution.EXTERNAL
    assert by_label["Fragment at"].resolution is Resolution.EXTERNAL
    assert by_label["Protocol safe"].target_class is TargetClass.UNKNOWN
    assert by_label["Protocol safe"].resolution is Resolution.UNRESOLVED
    assert by_label["public"].syntax is LinkSyntax.MERMAID_CLICK
    assert by_label["public"].target_class is TargetClass.MAIL

    for label, source_syntax in safe_links.items():
        _assert_exact_source_slice(markdown, by_label[label], source_syntax)
    _assert_exact_source_slice(markdown, by_label["public"], safe_click)


def test_input_order_does_not_change_results_and_duplicates_are_retained() -> None:
    alpha = _page("guides/alpha.md")
    zeta = _page("guides/Zeta.md")
    target = _page(
        "entities/User.md",
        locator="llm-wiki://entities/User",
    )
    duplicate = "[Same](../entities/User.md)"
    alpha_content = f"{duplicate}\n{duplicate}\n"
    zeta_content = "[Zed](../entities/User.md)\n"
    pages = [zeta, target, alpha]
    content_forward = {
        zeta.relative_path: zeta_content,
        target.relative_path: "",
        alpha.relative_path: alpha_content,
    }
    content_reverse = {
        alpha.relative_path: alpha_content,
        target.relative_path: "",
        zeta.relative_path: zeta_content,
    }

    forward = collect_link_observations(pages, content_forward)
    reverse = collect_link_observations(
        list(reversed(pages)),
        content_reverse,
    )

    assert forward == reverse
    assert [observation.source_canonical_path for observation in forward] == [
        "guides/alpha.md",
        "guides/alpha.md",
        "guides/Zeta.md",
    ]
    duplicate_observations = [
        observation for observation in forward if observation.label == "Same"
    ]
    assert len(duplicate_observations) == 2
    assert [observation.start for observation in duplicate_observations] == [
        0,
        len(duplicate) + 1,
    ]
    assert duplicate_observations[0].raw_target == (
        duplicate_observations[1].raw_target
    )


def test_duplicate_routes_and_locators_are_ambiguous_not_input_ordered() -> None:
    source = _page("guides/source.md")
    duplicate_first = _page(
        "entities/Parser.md",
    )
    duplicate_second = _page(
        "entities/Parser.md",
    )
    markdown = "[Route](../entities/Parser.md)\n[Locator](llm-wiki://entities/Parser)\n"
    pages = (
        source,
        duplicate_first,
        duplicate_second,
    )
    content_by_page = {page.relative_path: "" for page in pages}
    content_by_page[source.relative_path] = markdown

    forward = collect_link_observations(pages, content_by_page)
    reverse = collect_link_observations(
        tuple(reversed(pages)),
        dict(reversed(tuple(content_by_page.items()))),
    )

    assert forward == reverse
    assert [observation.label for observation in forward] == [
        "Route",
        "Locator",
    ]
    for observation in forward:
        assert observation.target_class is TargetClass.CONCEPT
        assert observation.resolution is Resolution.AMBIGUOUS
        assert observation.resolved_canonical_path is None


def test_collection_has_no_result_cap_or_deduplication() -> None:
    target = _page(
        "entities/User.md",
        locator="llm-wiki://entities/User",
    )
    link = "[User](../entities/User.md)"
    count = 2_049
    markdown = "\n".join(link for _ in range(count))

    _, observations = _collect(markdown, targets=(target,))

    assert len(observations) == count
    assert all(observation.label == "User" for observation in observations)
    assert all(
        observation.resolution is Resolution.RESOLVED for observation in observations
    )
    assert observations[0].start == 0
    assert observations[0].end == len(link)
    expected_last_start = (len(link) + 1) * (count - 1)
    assert observations[-1].start == expected_last_start
    assert observations[-1].end == len(markdown)
    assert len({observation.start for observation in observations}) == count


def test_collector_is_pure_over_supplied_pages_content_and_assets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _page(
        "guides/source.md",
        physical_path=Path("/absent/source.md"),
    )
    target = _page(
        "entities/User.md",
        locator="llm-wiki://entities/User",
        physical_path=Path("/absent/User.md"),
    )
    pages = [source, target]
    content_by_page = {
        source.relative_path: (
            "[User](../entities/User.md)\n![Diagram](../assets/diagram.svg)\n"
        ),
        target.relative_path: "",
    }
    assets = {"assets/diagram.svg"}
    pages_before = list(pages)
    content_before = dict(content_by_page)
    assets_before = set(assets)

    def forbidden_io(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("knowledge link collection performed filesystem I/O")

    # Scope global pathlib/os guards tightly so pytest can still inspect files
    # and report a useful failure if the collector violates this boundary.
    with monkeypatch.context() as io_guard:
        for method_name in (
            "read_text",
            "read_bytes",
            "open",
            "exists",
            "is_file",
            "is_dir",
            "iterdir",
            "glob",
            "rglob",
            "resolve",
        ):
            io_guard.setattr(Path, method_name, forbidden_io)
        io_guard.setattr(os, "walk", forbidden_io)
        io_guard.setattr(os, "scandir", forbidden_io)

        observations = collect_link_observations(
            pages,
            content_by_page,
            existing_asset_paths=assets,
        )

    assert len(observations) == 2
    assert observations[0].resolution is Resolution.RESOLVED
    assert observations[1].target_class is TargetClass.ASSET
    assert observations[1].resolution is Resolution.RESOLVED
    assert pages == pages_before
    assert content_by_page == content_before
    assert assets == assets_before


def test_empty_supplied_registry_is_a_valid_pure_input() -> None:
    assert collect_link_observations((), {}) == ()


def test_rejects_invalid_page_registry_inputs_with_field_specific_errors() -> None:
    invalid_route = _page("../outside.md")
    invalid_locator = _page(
        "guides/source.md",
        locator="https://example.invalid/not-a-locator",
    )
    credential_locator = _page(
        "guides/source.md",
        locator="llm-wiki://user@example.invalid/source",
    )
    cases: tuple[
        tuple[
            Callable[[], tuple[LinkObservation, ...]],
            str,
        ],
        ...,
    ] = (
        (
            lambda: collect_link_observations("not-pages", {}),
            "pages",
        ),
        (
            lambda: collect_link_observations([object()], {}),
            "pages[0]",
        ),
        (
            lambda: collect_link_observations(
                (invalid_route,),
                {invalid_route.relative_path: ""},
            ),
            "pages[0].relative_path",
        ),
        (
            lambda: collect_link_observations(
                (invalid_locator,),
                {invalid_locator.relative_path: ""},
            ),
            "pages[0].mcp_uri",
        ),
        (
            lambda: collect_link_observations(
                (credential_locator,),
                {credential_locator.relative_path: ""},
            ),
            "pages[0].mcp_uri",
        ),
    )

    for invoke, field in cases:
        with pytest.raises(KnowledgeLinkError) as exc_info:
            invoke()
        assert exc_info.value.field == field
        assert str(exc_info.value).startswith(f"{field}: ")


def test_requires_exact_page_content_parity_and_markdown_strings() -> None:
    source = _page("guides/source.md")

    cases: tuple[
        tuple[
            Callable[[], tuple[LinkObservation, ...]],
            str,
        ],
        ...,
    ] = (
        (
            lambda: collect_link_observations((source,), {}),
            "content_by_page",
        ),
        (
            lambda: collect_link_observations(
                (source,),
                {
                    source.relative_path: "",
                    "guides/extra.md": "",
                },
            ),
            "content_by_page",
        ),
        (
            lambda: collect_link_observations(
                (source,),
                {source.relative_path: b"not Markdown"},
            ),
            f"content_by_page.{source.relative_path}",
        ),
        (
            lambda: collect_link_observations(
                (source,),
                {
                    source.relative_path: "",
                    7: "",
                },
            ),
            "content_by_page",
        ),
        (
            lambda: collect_link_observations((source,), []),
            "content_by_page",
        ),
    )

    for invoke, field in cases:
        with pytest.raises(KnowledgeLinkError) as exc_info:
            invoke()
        assert exc_info.value.field == field
        assert str(exc_info.value).startswith(f"{field}: ")


def test_requires_an_evaluated_set_of_safe_canonical_asset_paths() -> None:
    source = _page("guides/source.md")
    content = {source.relative_path: ""}
    cases: tuple[
        tuple[
            Callable[[], tuple[LinkObservation, ...]],
            str,
        ],
        ...,
    ] = (
        (
            lambda: collect_link_observations(
                (source,),
                content,
                existing_asset_paths=["assets/diagram.svg"],
            ),
            "existing_asset_paths",
        ),
        (
            lambda: collect_link_observations(
                (source,),
                content,
                existing_asset_paths={7},
            ),
            "existing_asset_paths",
        ),
        (
            lambda: collect_link_observations(
                (source,),
                content,
                existing_asset_paths={"../outside.svg"},
            ),
            "existing_asset_paths",
        ),
        (
            lambda: collect_link_observations(
                (source,),
                content,
                existing_asset_paths={"assets\\diagram.svg"},
            ),
            "existing_asset_paths",
        ),
        (
            lambda: collect_link_observations(
                (source,),
                content,
                existing_asset_paths={source.relative_path},
            ),
            "existing_asset_paths",
        ),
        (
            lambda: collect_link_observations(
                (source,),
                content,
                existing_asset_paths={"guides/missing.md"},
            ),
            "existing_asset_paths",
        ),
    )

    for invoke, field in cases:
        with pytest.raises(KnowledgeLinkError) as exc_info:
            invoke()
        assert exc_info.value.field == field
        assert str(exc_info.value).startswith(f"{field}: ")
