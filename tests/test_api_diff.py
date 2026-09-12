"""Versioned exported-contract cases; no application imports or builds."""

import json
import sys
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services.api_contracts import ApiContractError
from llm_wiki_cli.services.api_diff import compare_openapi, render_markdown

CORPUS = json.loads(
    (Path(__file__).parent / "fixtures/api_diff/corpus-v1.json").read_text()
)


@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda case: case["id"])
def test_declared_compatibility_corpus(case, tmp_path):
    for name in ("baseline", "candidate"):
        (tmp_path / f"{name}.json").write_text(json.dumps(case[name]))
    report = compare_openapi("baseline.json", "candidate.json", source_root=tmp_path)
    assert report["breaking_count"] == case["expected_breaking"]
    assert report == compare_openapi(
        "baseline.json", "candidate.json", source_root=tmp_path
    )
    assert report["baseline"]["document_id"].startswith("sha256:")
    assert render_markdown(report) == render_markdown(report)
    if case["id"] in {
        "enum-narrowing",
        "composition",
        "cycle",
        "unresolved-path",
        "unresolved-response",
    }:
        assert report["status"] == "advisory"


def test_gate_exit_and_source_containment(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    case = CORPUS["cases"][1]
    for name in ("baseline", "candidate"):
        (tmp_path / f"{name}.json").write_text(json.dumps(case[name]))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "llm-wiki",
            "api-diff",
            "--baseline",
            "baseline.json",
            "--candidate",
            "candidate.json",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert json.loads(capsys.readouterr().out)["status"] == "breaking"
    with pytest.raises(ApiContractError):
        compare_openapi("../outside.json", "candidate.json", source_root=tmp_path)


@pytest.mark.parametrize("path_item", [None, {"get": None}])
def test_malformed_candidate_is_unknown_instead_of_a_confirmed_removal(
    tmp_path, path_item
):
    baseline = {
        "openapi": "3.1.0",
        "paths": {"/items": {"get": {"responses": {"200": {"description": "OK"}}}}},
    }
    candidate = {"openapi": "3.1.0", "paths": {"/items": path_item}}
    for name, document in (("baseline", baseline), ("candidate", candidate)):
        (tmp_path / f"{name}.json").write_text(json.dumps(document))
    report = compare_openapi("baseline.json", "candidate.json", source_root=tmp_path)
    assert report["status"] == "advisory"
    assert report["breaking_count"] == 0
