"""Memoized helper observations cannot cross explicit cache scopes."""

from contextlib import contextmanager

import pytest

from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.services import analysis_capture, helper_cache
from llm_wiki_cli.services import extractor_helpers as helpers
from llm_wiki_cli.services.helper_runtime import bind_helper, helper_operation
from llm_wiki_cli.services.helper_preparation import prepare_operation_helpers
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from tests.test_helper_cache import _profile, _typescript_build


@pytest.mark.parametrize("environment", [False, True], ids=["operation", "environment"])
def test_capture_memo_respects_configured_cache_switch(tmp_path, monkeypatch, environment):
    source = tmp_path / "project"
    source.mkdir()
    (source / "main.ts").write_text("export const value = 1;\n")
    populated, empty = tmp_path / "populated", tmp_path / "empty"
    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    monkeypatch.setattr(helper_cache, "_profile", _profile)
    monkeypatch.setattr(helper_cache, "_build", _typescript_build)
    helper_cache.ensure_helper("typescript", source, str(populated))
    monkeypatch.setattr(helpers, "command_output", lambda *a, **k: "v24.18.0")
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("capture must never prepare")
    ))

    @contextmanager
    def scope(cache):
        with monkeypatch.context() as configured:
            if environment:
                configured.setenv("LLM_WIKI_CACHE_DIR", str(cache))
            with helper_operation("never", cache_dir=None if environment else cache):
                yield

    @analysis_capture.capture_operation
    def observe():
        with scope(populated):
            first = analysis_capture.capture_analysis(
                EXTRACTOR_REGISTRY, source_root=source, languages={"typescript"},
            )
            assert "llm-wiki/extractor/typescript" in first
            with scope(empty):
                second = analysis_capture.capture_analysis(
                    EXTRACTOR_REGISTRY, source_root=source, languages={"typescript"},
                )
                assert "llm-wiki/extractor/typescript" not in second
            third = analysis_capture.capture_analysis(
                EXTRACTOR_REGISTRY, source_root=source, languages={"typescript"},
            )
            assert third == first

    observe()
    assert not empty.exists()


def test_pinned_helper_cannot_escape_changed_environment_cache_scope(tmp_path, monkeypatch):
    source = tmp_path / "project"
    source.mkdir()
    (source / "main.ts").write_text("export const value = 1;\n")
    populated, empty = tmp_path / "populated", tmp_path / "empty"
    monkeypatch.setattr(helper_cache, "_profile", _profile)
    monkeypatch.setattr(helper_cache, "_build", _typescript_build)
    handle = helper_cache.ensure_helper("typescript", source, str(populated))
    monkeypatch.setattr(helpers, "command_output", lambda *a, **k: "v24.18.0")
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: pytest.fail("strict must not prepare"))
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(populated))
    with helper_operation("never"):
        bind_helper(handle, source_root=source)
        assert helpers.get_prepared_typescript_root(source) == handle.root
        monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(empty))
        captured = analysis_capture.capture_analysis(
            EXTRACTOR_REGISTRY, source_root=source, languages={"typescript"},
        )
        assert "llm-wiki/extractor/typescript" not in captured
        assert helpers.get_prepared_typescript_root(source) is None
        with pytest.raises(helper_cache.HelperPreparationError, match="cache scope changed"):
            prepare_operation_helpers(build_source_snapshot(source), EXTRACTOR_REGISTRY)
    assert not empty.exists()
