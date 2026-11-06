"""Generated helper caches never become source or selection inputs."""

from __future__ import annotations

import json

import pytest

from llm_wiki_cli.extractors.common import discover_source_files
from llm_wiki_cli.services import extractor_helpers as helpers
from llm_wiki_cli.services import helper_cache as cache
from llm_wiki_cli.services.helper_runtime import EXTRACTOR_REGISTRY, required_helper_languages
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION
from llm_wiki_cli.services.source_snapshot import (
    build_source_snapshot,
    source_snapshot_matches_current_files,
)
from tests.test_helper_cache import _profile, _typescript_build


@pytest.mark.parametrize("source_name,expected_helpers", [("main.ts", ("typescript",)), ("main.py", ())])
def test_in_project_helper_publication_preserves_source_census(
    tmp_path, monkeypatch, source_name, expected_helpers,
):
    monkeypatch.delenv(helpers.ENV_CACHE_DIR, raising=False)
    monkeypatch.setattr(cache, "_profile", _profile)
    monkeypatch.setattr(cache, "_build", _typescript_build)
    project = tmp_path / "project"
    project.mkdir()
    (project / source_name).write_text("source input\n")
    before = build_source_snapshot(project)
    handle = cache.ensure_helper("typescript", project, str(project / "custom-helper-base"))
    after = build_source_snapshot(project)

    assert cache.validate_handle(handle)
    assert before.all_source_paths == after.all_source_paths == (source_name,)
    assert before.captured_content_hashes == after.captured_content_hashes
    assert before.captured_input_kinds == after.captured_input_kinds
    assert before.selected_regular_paths == after.selected_regular_paths
    assert before.package_markers == after.package_markers == ()
    assert source_snapshot_matches_current_files(before)
    assert required_helper_languages(after, EXTRACTOR_REGISTRY) == expected_helpers
    assert discover_source_files(str(project), [".js", ".ts"], language="typescript") == (
        [source_name] if source_name.endswith(".ts") else []
    )
    generated = str((handle.root / "extract.js").relative_to(project))
    assert build_source_snapshot(project, only_files=[generated]).all_source_paths == ()
    assert discover_source_files(str(project), [".js"], only_files=[generated], language="typescript") == []


def test_selection_cannot_readmit_managed_helper_cache(tmp_path, monkeypatch):
    monkeypatch.delenv(helpers.ENV_CACHE_DIR, raising=False)
    monkeypatch.setattr(cache, "_profile", _profile)
    monkeypatch.setattr(cache, "_build", _typescript_build)
    (tmp_path / "main.py").write_text("source input\n")
    policy = tmp_path / "sources.json"
    policy.write_text(json.dumps({"schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                                  "include": ["main.py", "tool-state"], "exclude": []}))
    handle = cache.ensure_helper("typescript", tmp_path, str(tmp_path / "tool-state"))
    generated = (handle.root / "extract.js").relative_to(tmp_path).as_posix()
    (handle.root / ".gitignore").write_text("*\n")
    snapshot = build_source_snapshot(tmp_path, source_selection="sources.json", coherent=True)
    assert snapshot.all_source_paths == ("main.py",)
    assert not snapshot.path_is_effectively_selected(generated)
    assert not snapshot.path_may_contain_effective_selection(str(handle.root.relative_to(tmp_path)))
    assert snapshot.captured_gitignore_paths == frozenset()
    assert source_snapshot_matches_current_files(snapshot)


def test_helper_cache_exclusion_does_not_match_user_source_prefixes(tmp_path):
    similar = tmp_path / "llm-wiki-extractors-examples"
    similar.mkdir()
    (similar / "main.ts").write_text("export const example = 1;\n")
    (tmp_path / "llm-wiki-extractors.ts").write_text("export const source = 1;\n")
    assert build_source_snapshot(tmp_path).all_source_paths == (
        "llm-wiki-extractors-examples/main.ts", "llm-wiki-extractors.ts",
    )
