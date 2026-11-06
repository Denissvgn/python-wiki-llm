"""Conflict resolution observes source only for repairs that need it."""
import json
import sys

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services import extraction_service, helper_cache, team


@pytest.fixture
def conflict_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source"
    source.mkdir()
    (source / "example.go").write_text("package example\nfunc Answer() int { return 42 }\n")
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    cache = tmp_path / "empty-cache"
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(cache))
    attempts = []

    def unexpected_preparation(language, *args, **kwargs):
        attempts.append(language)
        raise helper_cache.HelperPreparationError(language, "unexpected automatic preparation")

    monkeypatch.setattr(helper_cache, "ensure_helper", unexpected_preparation)

    def run(*options):
        monkeypatch.setattr(sys, "argv", [
            "llm-wiki", "team", "resolve-conflicts", "--src-dir", "source",
            "--wiki-dir", "wiki", "--format", "json", *options,
        ])
        cli.main()

    return wiki, cache, attempts, run


@pytest.mark.parametrize("options", [(), ("--write", "--helper-preparation", "never")],
                         ids=["default-preview", "existing-only-write"])
def test_missing_helper_cannot_resolve_from_incomplete_inventory(conflict_project, capsys, options):
    wiki, cache, attempts, run = conflict_project
    original = "<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> other\n"
    page = wiki / "index.md"
    page.write_text(original)
    with pytest.raises(SystemExit) as error:
        run(*options)
    assert error.value.code == 1
    assert attempts == []
    assert "go extraction failed" in capsys.readouterr().err
    assert page.read_text() == original
    assert not cache.exists()


@pytest.mark.parametrize("log_conflict", [False, True], ids=["clean", "log-only"])
def test_no_source_derived_conflict_requires_no_preparation(conflict_project, capsys, log_conflict):
    wiki, cache, attempts, run = conflict_project
    if log_conflict:
        (wiki / "log.md").write_text("<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> other\n")
    run("--write")
    response = json.loads(capsys.readouterr().out)
    assert response["ok"]
    assert response["conflict_count"] == int(log_conflict)
    assert not attempts and not cache.exists()


@pytest.mark.parametrize("during_resolution", [False, True], ids=["during-extraction", "before-publication"])
def test_conflict_resolver_preserves_concurrent_page_edits(conflict_project, monkeypatch, capsys, during_resolution):
    wiki, _cache, _attempts, run = conflict_project
    source = wiki.parent / "source"
    (source / "example.go").unlink()
    (source / "example.py").write_text("def answer(): return 42\n")
    page = wiki / "index.md"
    page.write_text("<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> other\n")
    module, name = (team, "_index_content") if during_resolution else (extraction_service, "get_inventory_result")
    original = getattr(module, name)

    def capture(*args, **kwargs):
        page.write_text("Author resolved this page.\n")
        return original(*args, **kwargs)

    monkeypatch.setattr(module, name, capture)
    with pytest.raises(SystemExit) as error:
        run("--write")
    assert error.value.code == 1
    if not during_resolution:
        response = json.loads(capsys.readouterr().out)
        assert response["resolved"] == []
        assert response["unresolved"][0]["path"] == "index.md"
    assert page.read_text() == "Author resolved this page.\n"


@pytest.mark.parametrize("write", [False, True], ids=["preview", "write"])
def test_explicit_auto_only_attempts_setup_for_writable_source_repairs(conflict_project, capsys, write):
    wiki, _cache, attempts, run = conflict_project
    original = "<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> other\n"
    page = wiki / "index.md"
    page.write_text(original)
    with pytest.raises(SystemExit) as error:
        run("--helper-preparation", "auto", *(["--write"] if write else []))
    assert error.value.code == 1
    assert attempts == (["go"] if write else [])
    message = capsys.readouterr().err
    assert ("go helper preparation failed" if write else "conflicts") in message
    assert page.read_text() == original
