"""Portable GitHub wiki candidates rewrite and validate their complete links."""

from copy import deepcopy
import sys

import pytest

from llm_wiki_cli.services import publication_links as links


PAGES = {"docs/start.md": "Home.md", "docs/accounts.md": "Accounts.md"}
ASSETS = {"docs/assets/account.txt": "assets/account.txt"}


def prepare(text, **kwargs):
    return links.prepare_wiki_markdown(
        text,
        source_path="docs/start.md",
        source_pages=PAGES,
        source_assets=ASSETS,
        **kwargs,
    )


def findings(files):
    return {item["kind"] for item in links.check_github_wiki(files)["findings"]}


def test_authored_pages_assets_and_preserved_manual_page_compose():
    source = "# Home\n\n[Account](accounts.md#display-name)\n\n[Download](assets/account.txt)\n\n[[Wiki tooling|Wiki-Tooling]]\n"
    result = prepare(source)
    assert "(Accounts#display-name)" in result
    assert "(assets/account.txt)" in result
    assert "[[Wiki tooling|Wiki-Tooling]]" in result
    files = {
        "Home.md": result.encode(),
        "Accounts.md": b"# Accounts\n\n## Display name\n",
        "Wiki-Tooling.md": b"# Wiki tooling\n\n[Home](Home)\n",
        "_Sidebar.md": b"[[Home]]\n\n[Accounts](Accounts#display-name)\n",
        "_Footer.md": b"[Home](Home)\n",
        "assets/account.txt": b"A public account example.\n",
    }
    before = deepcopy(files)
    assert links.check_github_wiki(files) == {"ok": True, "findings": []}
    assert files == before
    assert prepare(source) == result


def test_reference_links_nested_labels_and_wiki_links_are_rewritten():
    result = prepare(
        '# Home\n\n[nested [label]](accounts.md#display-name)\n\n[Account][guide]\n\n[guide]: accounts.md "A title"\n\n[[Name|accounts.md#display-name]]\n'
    )
    assert "[nested [label]](Accounts#display-name)" in result
    assert '[guide]: Accounts "A title"' in result
    assert "[[Name|Accounts#display-name]]" in result
    assert links.check_github_wiki(
        {"Home.md": result.encode(), "Accounts.md": b"## Display name\n"}
    )["ok"]


@pytest.mark.parametrize(
    "prefix,continuation", [("> ", ">   "), ("> > ", "> >   "), ("- ", "  ")]
)
def test_multiline_container_reference_definitions_are_rewritten(prefix, continuation):
    source = (
        "# Home\n\n"
        + prefix
        + "[Account][guide]\n\n"
        + prefix
        + "[guide]:\n"
        + continuation
        + 'accounts.md#display-name "Guide"\n'
    )
    result = prepare(source)
    assert continuation + 'Accounts#display-name "Guide"' in result
    assert links.check_github_wiki(
        {"Home.md": result.encode(), "Accounts.md": b"# Accounts\n\n## Display name\n"}
    )["ok"]


@pytest.mark.parametrize(
    "value",
    [
        "[Search](https://example.invalid/[[accounts.md]])",
        "<https://example.invalid/[[accounts.md]]>",
        '[Search](https://example.invalid "[[accounts.md]]")',
        "![Picture](https://example.invalid/[[accounts.md]].png)",
        "[Search][ref]\n\n[ref]: https://example.invalid/[[accounts.md]]",
    ],
)
def test_wiki_like_text_in_markdown_link_attributes_stays_literal(value):
    source = "# Home\n\n" + value + "\n"
    assert prepare(source) == source
    assert links.check_github_wiki({"Home.md": source.encode()})["ok"]


@pytest.mark.parametrize(
    "value",
    [
        '[Search](https://example.invalid "A [literal](accounts.md) title")',
        "[Search](https://example.invalid/?q=[literal](accounts.md))",
        '[Search][ref]\n\n[ref]: https://example.invalid "[literal](accounts.md)"',
    ],
)
def test_parsed_destinations_do_not_rewrite_markdown_shaped_attributes(value):
    source = "# Home\n\n[Account](accounts.md)\n\n" + value + "\n"
    result = prepare(source)
    assert result == source.replace("[Account](accounts.md)", "[Account](Accounts)")
    assert links.check_github_wiki(
        {"Home.md": result.encode(), "Accounts.md": b"# Accounts\n"}
    )["ok"]


@pytest.mark.parametrize(
    "value",
    [
        "[Search](https://example.invalid/?q=[literal](file:///tmp/x))",
        '[Search](https://example.invalid "[literal](file:///tmp/x)")',
        '[Search][ref]\n\n[ref]: https://example.invalid "[literal](file:///tmp/x)"',
    ],
)
def test_markdown_shaped_external_attributes_do_not_create_unsafe_links(value):
    source = "# Home\n\n" + value + "\n"
    assert prepare(source) == source
    assert links.check_github_wiki({"Home.md": source.encode()})["ok"]


def test_linked_image_and_outer_link_destinations_are_both_rewritten():
    source = "# Home\n\n[![Account](assets/account.txt)](accounts.md)\n"
    assert links.prepare_wiki_markdown(
        source,
        source_path="docs/start.md",
        source_pages=PAGES,
        source_assets={"docs/assets/account.txt": "assets/renamed.txt"},
    ) == (
        "# Home\n\n[![Account](assets/renamed.txt)](Accounts)\n"
    )


def test_invalid_reference_container_is_not_rewritten_as_a_definition():
    source = "# Home\n\n[Actual](accounts.md)\n\n[not-a-definition]:\n> accounts.md\n"
    result = prepare(source)
    assert "[Actual](Accounts)" in result
    assert "> accounts.md" in result


def test_code_and_comments_do_not_create_links_or_anchors():
    value = "# Home\n\n`[bad](missing)`\n\n```md\n# Fake\n[bad](missing)\n[[Missing]]\n```\n\n    [also](missing)\n\n<!--\n# Hidden\n[no](missing)\n-->\n"
    assert prepare(value) == value
    assert links.check_github_wiki({"Home.md": value.encode()})["ok"]
    assert "missing-anchor" in findings(
        {"Home.md": (value + "\n[bad](#fake)\n").encode()}
    )


def test_duplicate_heading_anchors_have_globally_unique_suffixes():
    value = "# A\n\n# A\n\n# A-1\n\n[one](#a) [two](#a-1) [three](#a-1-1)\n"
    assert links.check_github_wiki({"Home.md": value.encode()})["ok"]


def test_heading_anchors_follow_rendered_inline_text():
    value = "# Use `code` and *bold* [label](https://example.invalid)\n\n[Here](#use-code-and-bold-label)\n"
    assert links.check_github_wiki({"Home.md": value.encode()})["ok"]


def test_custom_anchors_and_safe_formatting_are_supported():
    value = b'# Home\n\n<details><summary>More</summary>\n\n<a name="custom" id="custom"></a>\n\n[Here](#custom)<br>\n\n</details>\n'
    assert links.check_github_wiki({"Home.md": value})["ok"]
    assert "anchor-collision" in findings(
        {"Home.md": value + b'<a name="custom"></a>\n'}
    )


@pytest.mark.parametrize(
    "value",
    [
        '<img src="assets/a.png">',
        '<a href="Home">Home</a>',
        "<script>alert(1)</script>",
        '<span onclick="x()">x</span>',
        "[[a|Home|alt=x]]",
    ],
)
def test_unsupported_markup_never_claims_readiness(value):
    assert not links.check_github_wiki(
        {"Home.md": ("# Home\n\n" + value).encode(), "assets/a.png": b"png"}
    )["ok"]


@pytest.mark.parametrize(
    "target",
    [
        "javascript:alert(1)",
        "data:text/html,x",
        "file:///tmp/x",
        "C:/private/x",
        "//host/x",
        "../../private.md",
        "%2e%2e/private.md",
        "%252e%252e/private.md",
        "assets/%00.png",
        "bad%5cpath",
    ],
)
def test_unsafe_targets_are_rejected_and_not_rewritten(target):
    text = f"# Home\n\n[x]({target})\n"
    assert "unsafe-link" in findings({"Home.md": text.encode()})
    if target == "%2e%2e/private.md":
        # It remains within the authored repository root, but must not be
        # accepted as a candidate-relative parent traversal.
        assert prepare(text) == text
    else:
        with pytest.raises(ValueError):
            prepare(text)


@pytest.mark.parametrize(
    "target",
    [
        "https://example.invalid/docs#x",
        "http://example.invalid/image.png",
        "mailto:maintainer@example.invalid",
    ],
)
def test_external_links_are_kept_without_network_access(target):
    text = f"# Home\n\n[x]({target})\n"
    assert prepare(text) == text
    assert links.check_github_wiki({"Home.md": text.encode()})["ok"]


def test_repository_links_need_an_immutable_explicit_pin():
    text = "# Home\n\n[Code](/src/app.py#L1)\n"
    with pytest.raises(ValueError, match="both"):
        prepare(text)
    with pytest.raises(ValueError, match="immutable"):
        prepare(
            text, repository_url="https://code.example/org/app", source_revision="main"
        )
    result = prepare(
        text, repository_url="https://code.example/org/app", source_revision="a" * 40
    )
    assert f"https://code.example/org/app/blob/{'a' * 40}/src/app.py#L1" in result
    assert links.check_github_wiki({"Home.md": result.encode()})["ok"]


@pytest.mark.parametrize(
    "repository",
    [
        "http://host/org/app",
        "https://user:token@host/org/app",
        "https://host/org/app?token=x",
        "https://host/org/app#frag",
    ],
)
def test_repository_pin_metadata_cannot_embed_credentials_or_mutable_components(
    repository,
):
    with pytest.raises(ValueError):
        prepare(
            "[code](/src/app.py)", repository_url=repository, source_revision="a" * 40
        )


def test_unmapped_source_links_remain_visible_to_complete_candidate_check():
    value = prepare("# Home\n\n[Missing](other.md)\n")
    assert "other.md" in value
    assert "missing-link" in findings({"Home.md": value.encode()})


def test_missing_anchors_pages_and_assets_are_reported_deterministically():
    files = {
        "Home.md": b"# Home\n[missing](Absent)\n![image](assets/missing.png)\n[heading](#absent)\n"
    }
    first = links.check_github_wiki(files)
    assert not first["ok"]
    assert findings(files) == {"missing-link", "missing-anchor"}
    assert first == links.check_github_wiki(dict(reversed(list(files.items()))))


@pytest.mark.parametrize(
    "extra,kind",
    [
        ({"HOME.md": b"# Alias\n"}, "path-collision"),
        ({"A B.md": b"# A\n", "A-B.md": b"# B\n"}, "page-collision"),
        ({"assets": b"file", "assets/a.png": b"image"}, "tree-collision"),
        ({"Assets/a.png": b"a", "assets/b.png": b"b"}, "path-collision"),
        ({"nested/Guide.md": b"# Nested\n"}, "invalid-markdown"),
        ({"../x.md": b"x"}, "invalid-path"),
        ({"Cafe\u0301.md": b"x"}, "invalid-path"),
        ({"CON.md": b"x"}, "invalid-path"),
        ({"Page.textile": b"x"}, "unsupported-page"),
    ],
)
def test_nonportable_candidates_and_route_collisions_fail(extra, kind):
    assert kind in findings({"Home.md": b"# Home\n", **extra})


def test_page_routes_cannot_alias_asset_or_raw_page_coordinates():
    source = "# Home\n\n[Guide](guide.md) ![Picture](pic.png)\n"
    result = links.prepare_wiki_markdown(
        source,
        source_path="docs/home.md",
        source_pages={"docs/home.md": "Home.md", "docs/guide.md": "Logo.png.md"},
        source_assets={"docs/pic.png": "Logo.png"},
    )
    assert "[Guide](Logo.png) ![Picture](Logo.png)" in result
    assert "route-file-collision" in findings(
        {"Home.md": result.encode(), "Logo.png.md": b"# Guide\n", "Logo.png": b"PNG"}
    )
    assert "route-file-collision" in findings(
        {
            "Home.md": b"# Home\n",
            "Guide.md": b"# Guide\n",
            "Guide.md.md": b"# Another guide\n",
        }
    )


@pytest.mark.parametrize(
    "path",
    [
        ".git/config",
        ".HG/store",
        ".SvN/entries",
        ".venv/a.py",
        "NODE_MODULES/a.js",
        "__PYCACHE__/a.pyc",
        ".LLM-WIKI-knowledge/index.json",
    ],
)
def test_private_namespaces_are_never_public_candidate_content(path):
    assert "invalid-path" in findings({"Home.md": b"# Home\n", path: b"private"})


def test_public_reports_folder_is_not_a_private_namespace():
    assert links.check_github_wiki(
        {
            "Home.md": b"# Home\n[Report](reports/annual.txt)\n",
            "reports/annual.txt": b"Public report\n",
        }
    )["ok"]


def test_missing_home_wrong_case_and_invalid_utf8_do_not_pass():
    assert "missing-home" in findings({"home.md": b"# Home\n"})
    assert "invalid-markdown" in findings({"Home.md": b"\xff"})
    assert "invalid-markdown" in findings({"Home.md": b"# Home\x00"})


def test_link_spelling_is_exact_and_image_links_cannot_point_to_pages():
    assert "unsafe-link" in findings(
        {"Home.md": b"# Home\n[wrong](guide)\n", "Guide.md": b"# Guide\n"}
    )
    assert "image-page" in findings({"Home.md": b"# Home\n![wrong](Home)\n"})


def test_limits_are_checked_before_claiming_readiness(monkeypatch):
    monkeypatch.setattr(links, "MAX_WIKI_FILE_BYTES", 8)
    assert "file-limit" in findings({"Home.md": b"# Home\n", "a": b"123456789"})
    monkeypatch.setattr(links, "MAX_WIKI_TOTAL_BYTES", 10)
    assert "total-limit" in findings({"Home.md": b"# Home\n", "a": b"12345"})
    monkeypatch.setattr(links, "MAX_WIKI_FILES", 1)
    assert "file-limit" in findings({"Home.md": b"# Home\n", "a": b"1"})


def test_optional_parser_dependency_has_an_actionable_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "markdown_it", None)
    result = links.check_github_wiki({"Home.md": b"# Home\n"})
    assert not result["ok"]
    assert any("publication extra" in item["message"] for item in result["findings"])
    with pytest.raises(ValueError, match="publication extra"):
        prepare("# Home\n")


def test_manual_wiki_links_remain_wiki_links_with_repository_metadata():
    text = "# Home\n\n[[Wiki tooling|Wiki-Tooling]] [[/Wiki-Tooling]]\n"
    result = prepare(
        text, repository_url="https://code.example/org/app", source_revision="a" * 40
    )
    assert "blob/" not in result
    assert links.check_github_wiki(
        {"Home.md": result.encode(), "Wiki-Tooling.md": b"# Wiki tooling\n"}
    )["ok"]


def test_source_parent_links_can_stay_within_the_repository_root():
    result = links.prepare_wiki_markdown(
        "[Home](../README.md)",
        source_path="docs/guide.md",
        source_pages={"README.md": "Home.md"},
        source_assets={},
    )
    assert result == "[Home](Home)"


def test_frontmatter_and_non_image_media_do_not_claim_readiness():
    assert "unsupported-frontmatter" in findings(
        {"Home.md": b"---\ntitle: Home\n---\n# Home\n"}
    )
    assert "image-format" in findings(
        {"Home.md": b"# Home\n![data](assets/a.txt)\n", "assets/a.txt": b"data"}
    )


@pytest.mark.parametrize("target", ["[[image.png|alt=x]]", "[[name|]]"])
def test_unknown_wiki_media_attributes_fail_explicitly(target):
    assert "unsupported-wiki" in findings({"Home.md": ("# Home\n" + target).encode()})
    with pytest.raises(ValueError, match="unsupported"):
        prepare(target)


def test_interactive_diagram_links_are_explicitly_unsupported():
    assert "unsupported-diagram-link" in findings(
        {
            "Home.md": b'# Home\n```mermaid\nflowchart LR\nA-->B\nclick A "Missing"\n```\n'
        }
    )
    assert links.check_github_wiki(
        {"Home.md": b"# Home\n```mermaid\nflowchart LR\nA-->B\n```\n"}
    )["ok"]


@pytest.mark.parametrize("separator", ["\u2028", "\x85", "\v", "\f"])
def test_unicode_separators_cannot_hide_live_wiki_links(separator):
    text = (
        "# Home\n\nfirst"
        + separator
        + "second"
        + separator
        + "third\n[[Missing]]\n\n```\ncode\n```\n"
    )
    assert "missing-link" in findings({"Home.md": text.encode()})


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_commonmark_line_endings_preserve_live_and_fenced_link_boundaries(newline):
    text = newline.join(
        ["# Home", "", "[[Missing]]", "", "```", "[[Also missing]]", "```", ""]
    )
    report = links.check_github_wiki({"Home.md": text.encode()})
    assert len(report["findings"]) == 1
    assert "Missing" in report["findings"][0]["message"]
    assert "Also missing" not in report["findings"][0]["message"]


@pytest.mark.parametrize(
    "text",
    [
        "`unclosed\n\n[[Missing]]\n\nclosing`",
        "| A | B | C |\n|---|---|---|\n| `unclosed | [[Missing]] | closing` |",
    ],
)
def test_unmatched_backticks_do_not_hide_links_across_blocks_or_table_cells(text):
    assert "missing-link" in findings({"Home.md": ("# Home\n\n" + text).encode()})


def test_multiline_quoted_code_and_literal_table_code_are_not_links():
    text = "# Home\n\n> A `code\n> [[Missing]]` example.\n\n| A | B |\n|---|---|\n| `[[Missing]]` | [[Home]] |\n"
    assert links.check_github_wiki({"Home.md": text.encode()})["ok"]


def test_escaped_table_pipes_keep_literal_code_and_live_links_separate():
    text = "# Home\n\n| A | B |\n|---|---|\n| `x\\|y [[Missing]]` | [[Home]] |\n"
    assert links.check_github_wiki({"Home.md": text.encode()})["ok"]
