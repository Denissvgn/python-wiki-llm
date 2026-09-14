"""Ranking identity, shared callers, compatibility, and resource boundaries."""

import json
import sys

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services.mcp_server import McpWikiError, McpWikiService
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


@pytest.mark.parametrize("mode", [None, "ranked", "substring"])
def test_cli_and_mcp_identical_and_substring_compatibility(
    tmp_path, monkeypatch, capsys, mode
):
    monkeypatch.chdir(tmp_path)
    wiki = _write_wiki(tmp_path)
    service = McpWikiService(src_dir=".", wiki_dir=str(wiki))
    expected = service.search_wiki("User", limit=2, mode=mode or "ranked")
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
        ]
        + (["--mode", mode] if mode else []),
    )
    cli.main()
    assert json.loads(capsys.readouterr().out) == expected
    assert expected["mode"] == (mode or "ranked")
    legacy = service.search_wiki("Primary account", mode="substring")
    assert legacy["total"] == 1
    assert legacy["results"][0]["id"] == "User"
    assert "score" not in legacy["results"][0]


@pytest.mark.parametrize("mode", ["ranked", "substring"])
@pytest.mark.parametrize(
    "query,options,argument",
    [("User", ["--limit", value], "--limit") for value in ("0", "-1", "-5", "invalid")]
    + [(query, [], "query") for query in ("", "   ", "\t\n", " \u2003\t")],
)
def test_search_invalid_arguments_fail_before_dispatch(
    monkeypatch, capsys, mode, query, options, argument
):
    monkeypatch.setattr(
        cli,
        "_dispatch_command",
        lambda args: pytest.fail("invalid input was dispatched"),
    )
    monkeypatch.setattr(
        "sys.argv", ["llm-wiki", "search", query, "--mode", mode, *options]
    )
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert argument in output.err and "Traceback" not in output.err


@pytest.mark.parametrize("mode", ["ranked", "substring"])
@pytest.mark.parametrize(
    "limit,returned", [(None, 20), (1, 1), (100, 100), (101, 100), (150, 100)]
)
def test_search_cli_preserves_cap_and_exact_bounds(
    tmp_path, monkeypatch, capsys, mode, limit, returned
):
    monkeypatch.chdir(tmp_path)
    wiki = _write_wiki(tmp_path)
    for index in range(101):
        (wiki / "entities" / f"Match{index:03}.md").write_text(
            "# Bounded fixture\n\nUnique search probe.\n", encoding="utf-8"
        )
    argv = ["llm-wiki", "search", "Unique search probe", "--mode", mode]
    if limit is not None:
        argv += ["--limit", str(limit)]
    monkeypatch.setattr("sys.argv", argv)
    cli.main()
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == mode
    assert result["total"] == 101
    assert result["returned"] == result["count"] == len(result["results"]) == returned
    assert result["truncated"] is True
    assert result["bounds"]["results"] == {
        "total": 101,
        "returned": returned,
        "truncated": True,
    }
    if mode == "substring":
        assert [match["id"] for match in result["results"]] == [
            f"Match{i:03}" for i in range(returned)
        ]
        assert all(
            "score" not in match and "provenance" not in match
            for match in result["results"]
        )


@pytest.mark.parametrize("mode", ["ranked", "substring"])
def test_search_cli_empty_result_includes_mode_and_zero_bounds(
    tmp_path, monkeypatch, capsys, mode
):
    monkeypatch.chdir(tmp_path)
    _write_wiki(tmp_path)
    monkeypatch.setattr(
        "sys.argv", ["llm-wiki", "search", "absent-query-xyz", "--mode", mode]
    )
    cli.main()
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == mode
    assert result["results"] == []
    assert result["total"] == result["returned"] == result["count"] == 0
    assert result["truncated"] is False
    assert result["bounds"]["results"] == {
        "total": 0,
        "returned": 0,
        "truncated": False,
    }


def test_cli_preserves_significant_whitespace_in_substring_query(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    wiki = _write_wiki(tmp_path)
    (wiki / "entities" / "Padded.md").write_text(
        "# Padded\n\nleft résumé right\n", encoding="utf-8"
    )
    (wiki / "entities" / "Bare.md").write_text("# Bare\n\nrésumé\n", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv", ["llm-wiki", "search", " résumé ", "--mode", "substring"]
    )
    cli.main()
    result = json.loads(capsys.readouterr().out)
    assert result["query"] == " résumé "
    assert [match["id"] for match in result["results"]] == ["Padded"]
    assert McpWikiService().search_wiki("résumé", mode="substring")["total"] == 2


@pytest.mark.parametrize("mode", ["ranked", "substring"])
@pytest.mark.parametrize("query", [None, False, 0, [], {}, "", " \t\u2003"])
def test_search_service_keeps_rejecting_invalid_queries(
    tmp_path, monkeypatch, mode, query
):
    monkeypatch.chdir(tmp_path)
    _write_wiki(tmp_path)
    with pytest.raises(McpWikiError, match="non-empty string"):
        McpWikiService().search_wiki(query, mode=mode)


@pytest.mark.parametrize("limit", [True, False, "1", 1.5, 0, -1])
def test_search_service_keeps_rejecting_invalid_limits(tmp_path, monkeypatch, limit):
    monkeypatch.chdir(tmp_path)
    _write_wiki(tmp_path)
    with pytest.raises(McpWikiError, match="positive integer"):
        McpWikiService().search_wiki("User", limit=limit)


@pytest.mark.parametrize(
    "error", [McpWikiError("Page exceeds search byte limit"), OSError("read failed")]
)
def test_search_runtime_failures_keep_exit_one(tmp_path, monkeypatch, capsys, error):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_WIKI_DEBUG", raising=False)
    _write_wiki(tmp_path)

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(McpWikiService, "search_wiki", fail)
    monkeypatch.setattr("sys.argv", ["llm-wiki", "search", "User"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert capsys.readouterr() == ("", f"Error: {error}\n")
