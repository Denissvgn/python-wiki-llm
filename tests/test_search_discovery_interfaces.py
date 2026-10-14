"""Public receiving checks for opt-in qualified discovery."""

import json
import sys
from typing import Any

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import search_service
from llm_wiki_cli.services.mcp_server import McpWikiError, McpWikiService
from llm_wiki_cli.services.search_discovery import DiscoveryError
from tests.test_search_source_interfaces import owned_wiki as owned_wiki


@pytest.mark.parametrize("mode,include_source", [
    ("ranked", False), ("ranked-v1", False), ("ranked-v2", False),
    ("ranked-v2", True), ("ranked", True), ("substring", False),
])
def test_qualified_api_cli_mcp_byte_parity(owned_wiki, monkeypatch, capsys, mode, include_source):
    root, wiki, *_ = owned_wiki
    options: dict[str, Any] = {"src_dir": str(root), "wiki_dir": str(wiki), "kinds": ["modules"],
                              "limit": 1, "mode": mode, "include_source": include_source}
    plain = api.search_wiki("owner", **options)
    expected = api.search_wiki("owner", discovery="qualified-v1", **options)
    assert {key: value for key, value in expected.items() if key not in {"discovery", "source_indexing"}} == {
        key: value for key, value in plain.items() if key != "source_indexing"}
    if include_source:
        original = plain.get("source_indexing")
        enriched = expected.get("source_indexing")
        assert original is not None and enriched is not None
        for key in ("wiki_read_bytes_including_rechecks", "source_read_bytes_including_rechecks"):
            assert enriched[key] >= original[key]
        work = {"wiki_read_bytes_including_rechecks", "source_read_bytes_including_rechecks", "final_source_validation"}
        assert {key: value for key, value in enriched.items() if key not in work} == {
            key: value for key, value in original.items() if key not in work}
    assert expected == search_service.search_wiki("owner", discovery="qualified-v1", **options)
    service = McpWikiService(src_dir=str(root), wiki_dir=str(wiki))
    assert service.search_wiki("owner", kinds=["modules"], limit=1, mode=mode,
                              include_source=include_source, discovery="qualified-v1") == expected
    capsys.readouterr()
    args = ["llm-wiki", "search", "owner", "--src-dir", str(root), "--wiki-dir", str(wiki),
            "--kind", "modules", "--limit", "1", "--mode", mode, "--discovery", "qualified-v1"]
    monkeypatch.setattr(sys, "argv", args + (["--include-source"] if include_source else []))
    cli.main()
    assert json.loads(capsys.readouterr().out) == expected
    discovery = expected.get("discovery")
    assert discovery is not None
    assert discovery["identity_state"] == "candidate"
    assert discovery["live_comparison_performed"] is False
    assert discovery["members"][0]["next_read"]["resolution_performed"] is False


def test_qualified_text_preserves_complete_metadata(owned_wiki, monkeypatch, capsys):
    root, wiki, *_ = owned_wiki
    expected = api.search_wiki("owner", src_dir=str(root), wiki_dir=str(wiki), discovery="qualified-v1")
    capsys.readouterr()
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "search", "owner", "--src-dir", str(root),
                                     "--wiki-dir", str(wiki), "--discovery", "qualified-v1", "--format", "text"])
    cli.main()
    output = capsys.readouterr().out
    assert json.loads(output[output.index("{"):]) == expected.get("discovery")


@pytest.mark.parametrize("discovery", [True, {}, "qualified-v2", ""])
def test_invalid_discovery_rejected_before_capture(tmp_path, monkeypatch, discovery):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(search_service, "build_source_snapshot",
                        lambda *args, **kwargs: pytest.fail("invalid option performed capture"))
    with pytest.raises(ValueError, match="discovery"):
        search_service.search_wiki("owner", discovery=discovery)


def test_output_limit_reason_survives_public_api_and_mcp(owned_wiki, monkeypatch):
    from llm_wiki_cli.services import search_discovery

    root, wiki, *_ = owned_wiki
    def exceed(*args, **kwargs):
        raise DiscoveryError("discovery-output-limit", "discovery", required_bytes=262145)
    monkeypatch.setattr(search_discovery, "enrich_search", exceed)
    with pytest.raises(api.InvalidRequestError) as api_error:
        api.search_wiki("owner", src_dir=str(root), wiki_dir=str(wiki), discovery="qualified-v1")
    service = McpWikiService(src_dir=str(root), wiki_dir=str(wiki))
    with pytest.raises(McpWikiError) as mcp_error:
        service.search_wiki("owner", discovery="qualified-v1")
    assert api_error.value.code == mcp_error.value.code == "discovery-output-limit"
    assert api_error.value.details == mcp_error.value.data == {
        "reason": "discovery-output-limit", "field": "discovery", "max_bytes": 262144, "required_bytes": 262145}


def test_invalid_mcp_discovery_precedes_selection_pin_read(owned_wiki, monkeypatch):
    root, wiki, *_ = owned_wiki
    service = McpWikiService(src_dir=str(root), wiki_dir=str(wiki))
    monkeypatch.setattr(service, "_assert_source_selection_pin_current",
                        lambda: pytest.fail("invalid option read source selection"))
    with pytest.raises(McpWikiError, match="discovery"):
        service.search_wiki("owner", discovery="unknown")
