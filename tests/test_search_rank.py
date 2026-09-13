"""Ranking identity, shared callers, compatibility, and resource boundaries."""

import json
import sys

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services.mcp_server import McpWikiService
from llm_wiki_cli.services.search_rank import rank_pages
from tests.test_mcp import _write_wiki


def _page(name, content):
    return {"id": name, "path": f"modules/{name}.md", "title": name, "content": content}


def test_exact_identity_symbol_graph_and_iteration_independence():
    pages = [
        _page("alpha", "# alpha\n| `do_work` | useful |\n[beta](beta.md)"),
        _page("beta", "# beta\nDo work with alpha.\n[broken](http://[invalid)"),
    ]
    result = rank_pages(pages, "alpha")
    assert result == rank_pages(reversed(pages), "alpha")
    assert result["results"][0]["id"] == "alpha"
    assert "exact-page-id" in result["results"][0]["reasons"]
    assert rank_pages(pages, "do_work")["results"][0]["id"] == "alpha"
    assert "inbound-wiki-links:1" in rank_pages(pages, "beta")["results"][0]["reasons"]
    changed = [dict(pages[0], content=pages[0]["content"] + "!"), pages[1]]
    assert result["corpus_id"] != rank_pages(changed, "alpha")["corpus_id"]


@pytest.mark.parametrize("bounds", [{"max_pages": 1}, {"max_bytes": 2}])
def test_resource_limit_fails_instead_of_returning_partial_ranking(bounds):
    with pytest.raises(ValueError, match="Search exceeds"):
        rank_pages([_page("alpha", "aaa"), _page("beta", "bbb")], "alpha", **bounds)


def test_cli_and_mcp_identical_and_substring_compatibility(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    wiki = _write_wiki(tmp_path)
    service = McpWikiService(src_dir=".", wiki_dir=str(wiki))
    expected = service.search_wiki("User", limit=2)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "llm-wiki",
            "search",
            "User",
            "--wiki-dir",
            str(wiki),
            "--limit",
            "2",
            "--format",
            "json",
        ],
    )
    cli.main()
    assert json.loads(capsys.readouterr().out) == expected
    legacy = service.search_wiki("Primary account", mode="substring")
    assert legacy["total"] == 1
    assert legacy["results"][0]["id"] == "User"
    assert "score" not in legacy["results"][0]
