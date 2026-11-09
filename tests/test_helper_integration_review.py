"""Cross-boundary helper bindings use one artifact/profile for an operation."""
from __future__ import annotations

import pytest

from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli import api
from llm_wiki_cli.extractors.ts_extractor import TypeScriptExtractor
from llm_wiki_cli.services import analysis_capture
from llm_wiki_cli.services import extraction_service
from llm_wiki_cli.services import extractor_helpers as helpers
from llm_wiki_cli.services import helper_cache as cache
from llm_wiki_cli.services.helper_preparation import prepare_operation_helpers
from llm_wiki_cli.services.helper_runtime import bind_helper, helper_operation, pinned_helper
from llm_wiki_cli.services.source_snapshot import build_source_snapshot

from tests.test_helper_cache import _profile, _typescript_build


def test_strict_external_read_does_not_execute_callers_project_helper(tmp_path, monkeypatch):
    from tests.test_helper_preparation import _prepare_fixture

    caller = tmp_path / "caller"
    (caller / ".git").mkdir(parents=True)
    source = tmp_path / "source"
    source.mkdir()
    (source / "main.ts").write_text("export const value = 1;\n")
    monkeypatch.chdir(caller)
    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    monkeypatch.setattr(cache, "user_helper_cache_root", lambda: tmp_path / "empty-shared-cache")
    monkeypatch.setattr(cache.shutil, "which", lambda name: "node" if name == "node" else None)
    _prepare_fixture("typescript", caller / ".git" / helpers.HELPER_CACHE_DIRNAME)
    assert helpers.get_prepared_typescript_root(caller) is not None
    assert helpers.get_prepared_typescript_root(source) is None
    monkeypatch.setattr(TypeScriptExtractor, "_run_node_extractor", lambda *a: pytest.fail("executed helper from caller's cache"))

    with pytest.raises(api.WorkspaceStateError, match="helper is not prepared"):
        api.extract_source(str(source), read_only=True, allow_external_src=True)


def test_capture_does_not_discover_a_new_node_for_a_bound_missing_runtime(tmp_path, monkeypatch):
    from tests.test_helper_preparation import _prepare_fixture

    base = tmp_path / "cache"
    _prepare_fixture("typescript", base / helpers.HELPER_CACHE_DIRNAME)
    monkeypatch.setattr(cache.shutil, "which", lambda name: None)
    with helper_operation("never", cache_dir=base):
        handle = cache.lookup_helper("typescript", tmp_path)
        assert handle is not None and "node" not in handle.runtime_executables
        bind_helper(handle, source_root=tmp_path)
        # A Node subsequently found via PATH cannot execute this operation's
        # bound helper. Its version must not qualify an inventory cache entry.
        monkeypatch.setattr(helpers, "command_output", lambda *a: "v24.18.0")
        captured = analysis_capture.capture_analysis(
            EXTRACTOR_REGISTRY, source_root=tmp_path, languages={"typescript"},
        )
        assert "llm-wiki/extractor/typescript" not in captured


@pytest.mark.parametrize("change_scope", [False, True], ids=["same-cache", "changed-environment-cache"])
def test_strict_missing_binding_survives_publication_after_inventory_key(tmp_path, monkeypatch, change_scope):
    from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions
    from tests.test_helper_preparation import _prepare_fixture

    source = tmp_path / "source"
    source.mkdir()
    (source / "main.ts").write_text("export const value = 1;\n")
    base = tmp_path / "helpers"
    initial = tmp_path / "empty" if change_scope else base
    monkeypatch.setenv(helpers.ENV_CACHE_DIR, str(initial))
    ready = base / helpers.HELPER_CACHE_DIRNAME
    unpublished = tmp_path / "ready-to-publish"
    _prepare_fixture("typescript", ready)
    ready.rename(unpublished)
    monkeypatch.setattr(cache.shutil, "which", lambda name: "node" if name == "node" else None)
    original = extraction_service._run_inventory_plans

    def publish_and_extract(*args, **kwargs):
        unpublished.rename(ready)
        monkeypatch.setenv(helpers.ENV_CACHE_DIR, str(base))
        return original(*args, **kwargs)

    monkeypatch.setattr(extraction_service, "_run_inventory_plans", publish_and_extract)
    monkeypatch.setattr(TypeScriptExtractor, "_run_node_extractor", lambda *a: pytest.fail("executed a helper published after capture"))
    with helper_operation("never"):
        result = extraction_service.get_inventory_result(source, include_plugins=False,
            cache_options=InventoryCacheOptions(enabled=True, cache_dir=str(tmp_path / "inventory")))
        assert [status.language for status in result.failed] == ["typescript"]
        assert "llm-wiki/extractor/typescript" not in (result.analysis_components or {})
        assert helpers.get_prepared_typescript_root(source) is None
        observed = helpers.helper_identity("typescript", source)
        assert observed["prepared"] is None
        if change_scope:
            assert "helper-cache-scope-mismatch" in observed["issues"]
            with pytest.raises(cache.HelperPreparationError, match="cache scope changed"):
                prepare_operation_helpers(build_source_snapshot(source), EXTRACTOR_REGISTRY)
        assert helpers.get_prepared_typescript_root(tmp_path) is not None
        with helper_operation("never", cache_dir=base):
            assert helpers.get_prepared_typescript_root(source) is not None
    with helper_operation("never"):
        assert helpers.get_prepared_typescript_root(source) is not None


def test_selected_miss_invalidates_an_earlier_unbound_capture(tmp_path, monkeypatch):
    from tests.test_helper_preparation import _prepare_fixture

    source = tmp_path / "project"
    source.mkdir()
    (source / "main.ts").write_text("export const value = 1;\n")
    base = tmp_path / "helpers"
    ready = base / helpers.HELPER_CACHE_DIRNAME
    _prepare_fixture("typescript", ready)
    monkeypatch.setattr(cache.shutil, "which", lambda name: "node" if name == "node" else None)
    monkeypatch.setattr(helpers, "command_output", lambda *args: "v24.18.0")

    @analysis_capture.capture_operation
    def observe():
        def capture():
            return analysis_capture.capture_analysis(EXTRACTOR_REGISTRY, source_root=source, languages={"typescript"})

        assert "llm-wiki/extractor/typescript" in capture()
        ready.rename(tmp_path / "removed")
        assert prepare_operation_helpers(build_source_snapshot(source), EXTRACTOR_REGISTRY) == ()
        (tmp_path / "removed").rename(ready)
        assert "llm-wiki/extractor/typescript" not in capture()

    with helper_operation("never", cache_dir=base):
        observe()


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

    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    monkeypatch.setattr(cache, "user_helper_cache_root", lambda: tmp_path / "empty-user-cache")

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

    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    monkeypatch.setattr(cache, "user_helper_cache_root", lambda: tmp_path / "empty-user-cache")

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
