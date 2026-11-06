"""Selected helper readiness precedes capture and stays pinned through execution."""
from __future__ import annotations

import pytest

from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.services import analysis_capture, extraction_service, helper_cache
from llm_wiki_cli.services import extractor_helpers as helpers
from llm_wiki_cli.services.helper_preparation import prepare_operation_helpers
from llm_wiki_cli.services.helper_runtime import (
    PreparedHelperHandle, bind_helper, helper_operation, pinned_helper,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


def handle(tmp_path, language="typescript", *, key="a" * 64, cache=None):
    cache = cache or tmp_path / "cache" / "llm-wiki-extractors"
    root = cache / language / key
    path = root / "node_modules/ts-morph" if language == "typescript" else root / "extractor"
    receipt = {"toolchain": "node v24.18.0; npm 11.16.0" if language == "typescript" else "go version go1.26.5",
               "artifact_scope": helpers.ts_identity.ARTIFACT_SCOPE,
               "artifact_fingerprint": "sha256:" + "b" * 64}
    return PreparedHelperHandle(language, cache, key, root, path, receipt,
                                {"node": "/pinned/node"} if language == "typescript" else {})


def source(tmp_path, *names):
    for name in names:
        (tmp_path / name).write_text("export const value = 1;\n")
    return build_source_snapshot(tmp_path)


def test_selected_helpers_are_ready_before_inventory_cache_identity(tmp_path, monkeypatch):
    snapshot = source(tmp_path, "main.ts")
    events = []
    prepared = handle(tmp_path)
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: events.append("prepare") or prepared)

    def identity(*args):
        assert pinned_helper("typescript", source_root=tmp_path) is prepared
        events.append("capture")
        raise RuntimeError("stop before identity computation")

    monkeypatch.setattr(extraction_service, "_load_inventory_cache_state", identity)
    request = extraction_service.InventoryRequest(tmp_path, source_snapshot=snapshot, include_plugins=False)
    with helper_operation("auto"), pytest.raises(RuntimeError, match="stop before identity"):
        extraction_service.get_inventory_result(request)
    assert events == ["prepare", "capture"]


def test_python_or_python_only_subset_never_resolves_helpers(tmp_path, monkeypatch):
    snapshot = source(tmp_path, "main.ts", "main.py")
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: pytest.fail("unselected helper"))
    monkeypatch.setattr(helper_cache, "lookup_helper", lambda *a, **k: pytest.fail("unselected helper"))
    with helper_operation("auto"):
        assert prepare_operation_helpers(snapshot, EXTRACTOR_REGISTRY, only_files=["main.py"]) == ()
    assert not (tmp_path / "cache").exists()


def test_strict_operation_reuses_only_existing_artifacts(tmp_path, monkeypatch):
    snapshot = source(tmp_path, "main.ts")
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: pytest.fail("strict must not prepare"))
    monkeypatch.setattr(helper_cache, "lookup_helper", lambda *a, **k: None)
    with helper_operation("never"):
        assert prepare_operation_helpers(snapshot, EXTRACTOR_REGISTRY) == ()
    assert not (tmp_path / "cache").exists()


def test_failed_preparation_is_attempted_once_and_keeps_cause(tmp_path, monkeypatch):
    snapshot = source(tmp_path, "main.ts")
    attempts = []

    def failed(*args, **kwargs):
        attempts.append(args[0])
        raise helper_cache.HelperPreparationError("typescript", "npm is unavailable")

    monkeypatch.setattr(helper_cache, "ensure_helper", failed)
    with helper_operation("auto"), pytest.raises(helper_cache.HelperPreparationError, match="npm is unavailable"):
        prepare_operation_helpers(snapshot, EXTRACTOR_REGISTRY)
    assert attempts == ["typescript"]


def test_operation_reuses_handle_but_refuses_mid_operation_mutation(tmp_path, monkeypatch):
    snapshot = source(tmp_path, "main.ts")
    prepared = handle(tmp_path)
    attempts = []
    valid = [True]
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: attempts.append(a[0]) or prepared)
    monkeypatch.setattr(helper_cache, "validate_handle", lambda h: valid[0])
    with helper_operation("auto"):
        assert prepare_operation_helpers(snapshot, EXTRACTOR_REGISTRY) == (prepared,)
        assert prepare_operation_helpers(snapshot, EXTRACTOR_REGISTRY) == (prepared,)
        valid[0] = False
        with pytest.raises(helper_cache.HelperPreparationError, match="changed during analysis"):
            prepare_operation_helpers(snapshot, EXTRACTOR_REGISTRY)
    assert attempts == ["typescript"]


def test_parallel_workers_receive_same_operation_owned_handle(tmp_path, monkeypatch):
    prepared = handle(tmp_path)

    def extract(plan, **kwargs):
        assert pinned_helper("typescript", source_root=tmp_path) is prepared
        return extraction_service._ExtractionOutcome(plan.language, "ok", 1, {})

    monkeypatch.setattr(extraction_service, "_run_extraction_plan", extract)
    results = {}
    with helper_operation("auto"):
        bind_helper(prepared, source_root=tmp_path)
        extraction_service._run_parallel_safe_inventory_plans(
            [extraction_service._ExtractionPlan(
                language, "unused:test", True, True, None, [], 1, {},
            ) for language in ("typescript", "go")], 2, results,
        )
    assert set(results) == {"typescript", "go"}


def test_capture_uses_pinned_node_and_new_binding_invalidates_earlier_capture(tmp_path, monkeypatch):
    prepared = handle(tmp_path)
    monkeypatch.setattr(helper_cache, "validate_handle", lambda h: True)
    monkeypatch.setattr(helpers, "_manifest_current", lambda *a: None)
    commands = []
    monkeypatch.setattr(helpers, "command_output", lambda argv, **k: commands.append(argv) or "v24.18.0")

    @analysis_capture.capture_operation
    def observe():
        before = analysis_capture.capture_analysis(EXTRACTOR_REGISTRY, source_root=tmp_path, languages={"typescript"})
        assert "llm-wiki/extractor/typescript" not in before
        bind_helper(prepared, source_root=tmp_path)
        after = analysis_capture.capture_analysis(EXTRACTOR_REGISTRY, source_root=tmp_path, languages={"typescript"})
        assert "llm-wiki/extractor/typescript" in after

    with helper_operation("auto"):
        observe()
    assert commands == [["/pinned/node", "--version"]]


def test_fresh_reobservation_detects_pinned_artifact_mutation(tmp_path, monkeypatch):
    from llm_wiki_cli.services.scoped_sync_repair import _recapture
    prepared = handle(tmp_path)
    valid = [True]
    monkeypatch.setattr(helper_cache, "validate_handle", lambda h: valid[0])
    monkeypatch.setattr(helpers, "command_output", lambda *a, **k: "v24.18.0")
    with helper_operation("auto"):
        bind_helper(prepared, source_root=tmp_path)
        assert "llm-wiki/extractor/typescript" in _recapture(EXTRACTOR_REGISTRY, tmp_path, None, {"typescript"})
        valid[0] = False
        assert "llm-wiki/extractor/typescript" not in _recapture(EXTRACTOR_REGISTRY, tmp_path, None, {"typescript"})
