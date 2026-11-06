"""Cross-boundary helper bindings use one artifact/profile for an operation."""
from __future__ import annotations

import pytest

from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.extractors.ts_extractor import TypeScriptExtractor
from llm_wiki_cli.services import analysis_capture
from llm_wiki_cli.services import extraction_service
from llm_wiki_cli.services import extractor_helpers as helpers
from llm_wiki_cli.services import helper_cache as cache
from llm_wiki_cli.services.helper_preparation import prepare_operation_helpers
from llm_wiki_cli.services.helper_runtime import bind_helper, helper_operation, pinned_helper
from llm_wiki_cli.services.source_snapshot import build_source_snapshot

from tests.test_helper_cache import _profile, _typescript_build


@pytest.fixture
def independent_cache_profiles(tmp_path, monkeypatch):
    source = tmp_path / "project"
    source.mkdir()
    (source / "main.ts").write_text("export const value = 1;\n")
    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    monkeypatch.setattr(cache, "_profile", _profile)
    monkeypatch.setattr(cache, "_build", _typescript_build)
    one, two = tmp_path / "cache-one", tmp_path / "cache-two"
    first = cache.ensure_helper("typescript", source, str(one))
    second = cache.ensure_helper("typescript", source, str(two))
    assert first.root != second.root
    assert cache.validate_handle(first) and cache.validate_handle(second)
    return source, one, two, first, second


def test_pinned_getter_refuses_an_explicit_different_cache_scope(independent_cache_profiles):
    source, one, two, first, second = independent_cache_profiles
    observed = cache.lookup_helper("typescript", source, str(two))
    assert observed is not None and observed.root == second.root
    with helper_operation("auto"):
        bind_helper(first, source_root=source)
        assert helpers.get_prepared_typescript_root(str(source), str(one)) == first.root
        assert helpers.get_prepared_typescript_root(str(source), str(two)) is None
        assert pinned_helper("typescript", source_root=source) is first


def test_direct_extractor_cannot_pair_other_cache_code_with_pinned_runtime(
    independent_cache_profiles,
):
    source, _one, two, first, _second = independent_cache_profiles
    extractor = TypeScriptExtractor()
    with helper_operation("auto"):
        bind_helper(first, source_root=source)
        assert extractor._toolchain_root(str(source), str(two)) is None
        assert extractor.last_error
        assert "cache" in extractor.last_error.casefold()
        assert pinned_helper("typescript", source_root=source) is first


def test_capture_cannot_label_an_explicit_other_cache_as_the_pinned_profile(
    independent_cache_profiles, monkeypatch,
):
    source, one, two, first, _second = independent_cache_profiles
    commands = []
    monkeypatch.setattr(helpers, "command_output", lambda argv, **kwargs: commands.append(argv) or "v24.18.0")
    with helper_operation("auto"):
        bind_helper(first, source_root=source)
        matching = analysis_capture.capture_analysis(
            EXTRACTOR_REGISTRY, source_root=source, helper_cache_dir=str(one), languages={"typescript"},
        )
        assert "llm-wiki/extractor/typescript" in matching
        mismatching = analysis_capture.capture_analysis(
            EXTRACTOR_REGISTRY, source_root=source, helper_cache_dir=str(two), languages={"typescript"},
        )
        assert "llm-wiki/extractor/typescript" not in mismatching
    assert commands == [["selected-node", "--version"]]


def test_strict_configured_empty_cache_never_falls_back_to_project_or_shared_helper(
    tmp_path, monkeypatch,
):
    from tests.test_helper_preparation import _prepare_fixture

    source = tmp_path / "project"
    (source / ".git").mkdir(parents=True)
    (source / "main.ts").write_text("export const value = 1;\n")
    legacy = source / ".git" / helpers.HELPER_CACHE_DIRNAME
    result = _prepare_fixture("typescript", legacy)
    assert result.path is not None
    available = helpers.get_prepared_typescript_root(source)
    assert available is not None
    selected = tmp_path / "explicitly selected empty cache"
    monkeypatch.setattr(cache, "ensure_helper", lambda *args, **kwargs: pytest.fail("strict mode must not prepare"))
    # Make the global cache equally tempting; neither project nor user scope
    # may override this operation's explicit cache selection.
    monkeypatch.setattr(cache, "user_helper_cache_root", lambda: legacy)
    snapshot = build_source_snapshot(source)
    with helper_operation("never", cache_dir=str(selected)):
        assert prepare_operation_helpers(snapshot, EXTRACTOR_REGISTRY) == ()
        assert pinned_helper("typescript", source_root=source) is None
        assert helpers.resolve_helper_cache_root(source) == selected / helpers.HELPER_CACHE_DIRNAME
        assert cache.cache_roots(source) == (selected / helpers.HELPER_CACHE_DIRNAME,)
        assert helpers.get_prepared_typescript_root(source) is None
        assert cache.lookup_helper("typescript", source) is None
        request = extraction_service.InventoryRequest(source, source_snapshot=snapshot)
        assert extraction_service._inventory_helper_cache_dir(request) == str(selected)
    assert helpers.get_prepared_typescript_root(source) == available
    assert not selected.exists()


def test_unbound_capture_obeys_strict_configured_cache_without_project_fallback(tmp_path, monkeypatch):
    from tests.test_helper_preparation import _prepare_fixture

    source = tmp_path / "project"
    (source / ".git").mkdir(parents=True)
    (source / "main.ts").write_text("export const value = 1;\n")
    legacy = source / ".git" / helpers.HELPER_CACHE_DIRNAME
    _prepare_fixture("typescript", legacy)
    selected = tmp_path / "never selected project default"
    monkeypatch.setattr(helpers, "command_output", lambda *args, **kwargs: "v24.18.0")
    before = analysis_capture.capture_analysis(EXTRACTOR_REGISTRY, source_root=source, languages={"typescript"})
    assert "llm-wiki/extractor/typescript" in before
    with helper_operation("never", cache_dir=str(selected)):
        observed = analysis_capture.capture_analysis(EXTRACTOR_REGISTRY, source_root=source, languages={"typescript"})
        assert "llm-wiki/extractor/typescript" not in observed
    assert not selected.exists()


def test_unbound_shared_helper_observation_is_available_without_preparation(tmp_path, monkeypatch):
    from tests.test_helper_cache import _profile, _typescript_build
    from llm_wiki_cli.services.helper_runtime import current_helper_operation

    source = tmp_path / "project without git"
    source.mkdir()
    (source / "main.ts").write_text("export const value=1;\n")
    shared = tmp_path / "user-cache"
    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    monkeypatch.setattr(cache, "user_helper_cache_root", lambda: shared)
    monkeypatch.setattr(cache, "_profile", _profile)
    monkeypatch.setattr(cache, "_build", _typescript_build)
    prepared = cache.ensure_helper("typescript", source)
    monkeypatch.setattr(cache, "ensure_helper", lambda *args, **kwargs: pytest.fail("observation must not prepare"))
    monkeypatch.setattr(helpers, "command_output", lambda *args, **kwargs: "v24.18.0")
    before = {p.relative_to(shared).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
              for p in shared.rglob("*") if p.is_file()}
    observed = analysis_capture.capture_analysis(
        EXTRACTOR_REGISTRY, source_root=source, languages={"typescript"},
    )
    assert "llm-wiki/extractor/typescript" in observed
    assert helpers.get_prepared_typescript_root(source) == prepared.root
    assert current_helper_operation() is None
    assert before == {p.relative_to(shared).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
                      for p in shared.rglob("*") if p.is_file()}


def test_unbound_shared_observation_respects_explicit_empty_scope(tmp_path, monkeypatch):
    from tests.test_helper_cache import _profile, _typescript_build

    source = tmp_path / "project"
    source.mkdir()
    (source / "main.ts").write_text("export const value=1;\n")
    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    monkeypatch.setattr(cache, "user_helper_cache_root", lambda: tmp_path / "shared")
    monkeypatch.setattr(cache, "_profile", _profile)
    monkeypatch.setattr(cache, "_build", _typescript_build)
    cache.ensure_helper("typescript", source)
    monkeypatch.setattr(cache, "ensure_helper", lambda *args, **kwargs: pytest.fail("observation must not prepare"))
    monkeypatch.setattr(helpers, "command_output", lambda *args, **kwargs: "v24.18.0")
    empty = tmp_path / "empty cache"
    observed = analysis_capture.capture_analysis(
        EXTRACTOR_REGISTRY, source_root=source, helper_cache_dir=str(empty), languages={"typescript"},
    )
    assert "llm-wiki/extractor/typescript" not in observed
    assert not empty.exists()


@pytest.mark.parametrize("node_available", [True, False])
def test_strict_shared_typescript_reuse_pins_available_node_without_setup(tmp_path, monkeypatch, node_available):
    source = tmp_path / "project"
    source.mkdir()
    (source / "main.ts").write_text("export const value=1;\n")
    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    monkeypatch.setattr(cache, "user_helper_cache_root", lambda: tmp_path / "shared")
    monkeypatch.setattr(cache, "_profile", _profile)
    monkeypatch.setattr(cache, "_build", _typescript_build)
    prepared = cache.ensure_helper("typescript", source)
    node = tmp_path / "selected node"
    node.write_text("#!/bin/sh\nexit 0\n")
    node.chmod(0o755)
    monkeypatch.setattr(cache.shutil, "which", lambda name: str(node) if name == "node" and node_available else None)
    monkeypatch.setattr(cache, "ensure_helper", lambda *args, **kwargs: pytest.fail("strict must not prepare"))
    monkeypatch.setattr(cache, "_profile", lambda *args, **kwargs: pytest.fail("strict must not probe build tools"))
    extractor = TypeScriptExtractor()
    with helper_operation("never"):
        selected = prepare_operation_helpers(build_source_snapshot(source), EXTRACTOR_REGISTRY)
        assert len(selected) == 1
        assert selected[0].root == prepared.root
        actual = extractor._toolchain_root(str(source))
        if node_available:
            assert actual is not None
            assert actual == prepared.root
            assert selected[0].runtime_executables["node"] == str(node.resolve())
            assert extractor._build_command(str(source), ["main.ts"], False, actual)[0] == str(node.resolve())
        else:
            assert actual is None
            assert extractor.last_error is not None
            assert "node not found" in extractor.last_error
            assert selected[0].runtime_executables == {}
