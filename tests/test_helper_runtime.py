"""Preparation authority and bindings are scoped before automatic setup exists."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
from typing import Any, cast

import pytest

from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.services import helper_runtime as runtime
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


def handle(tmp_path, language="typescript", key="first", *, cache=None):
    cache = cache or tmp_path / "cache"
    root = cache / language / key
    return runtime.PreparedHelperHandle(
        language, cache, key, root, root / "artifact",
        {"key": key, "nested": {"dependencies": ["frozen"]}},
        {"node": "/runtime/node"} if language == "typescript" else {},
    )


@pytest.mark.parametrize("requested,flags,expected", [
    (None, {}, "auto"), ("auto", {}, "auto"), ("never", {}, "never"),
    (None, {"strict_read_only": True}, "never"),
    (None, {"preview": True}, "never"), (None, {"offline": True}, "never"),
    ("never", {"strict_read_only": True, "preview": True, "offline": True}, "never"),
])
def test_policy_resolution_keeps_strict_modes_inert(requested, flags, expected):
    assert runtime.resolve_helper_policy(requested, **flags) == expected


@pytest.mark.parametrize("flag", ["strict_read_only", "preview", "offline"])
def test_explicit_automatic_request_cannot_override_strict_intent(flag):
    with pytest.raises(ValueError, match="conflicts"):
        runtime.resolve_helper_policy("auto", **{flag: True})
    with pytest.raises(ValueError, match="boolean"):
        runtime.resolve_helper_policy(None, **cast(Any, {flag: "true"}))


@pytest.mark.parametrize("bad", ["AUTO", "", "sometimes", True])
def test_invalid_policy_refused_before_context_exists(bad):
    with pytest.raises(ValueError, match="preparation"):
        with runtime.helper_policy(bad):
            pytest.fail("invalid scope entered")
    assert runtime.current_helper_operation() is None
    assert runtime.current_helper_configuration() is None


def test_invalid_configuration_does_not_enter_an_operation():
    with pytest.raises(ValueError, match="preparation"):
        runtime.resolve_helper_policy(cast(Any, {}))
    with pytest.raises(ValueError, match="progress must be callable"):
        with runtime.helper_policy("auto", progress=cast(Any, "bad")):
            pytest.fail("invalid progress entered scope")
    with pytest.raises(ValueError, match="progress must be callable"):
        with runtime.helper_operation(progress=cast(Any, "bad")):
            pytest.fail("invalid progress entered operation")
    assert runtime.current_helper_operation() is None


def test_handle_is_detached_deeply_immutable_and_requires_no_filesystem(tmp_path, monkeypatch):
    receipt = {"nested": {"dependencies": ["original"]}}
    executables = {"node": "/runtime/selected-node"}
    cache = tmp_path / "not-created"
    monkeypatch.setattr(Path, "stat", lambda *a, **k: pytest.fail("handle must not stat paths"))
    selected = runtime.PreparedHelperHandle(
        "typescript", cache, "first", cache / "typescript/first",
        cache / "typescript/first/node_modules/ts-morph", receipt, executables,
    )
    receipt["nested"]["dependencies"][0] = "changed"
    executables["node"] = "/wrong/node"
    receipt_view = cast(Any, selected.receipt)
    assert receipt_view["nested"]["dependencies"] == ["original"]
    assert selected.runtime_executables["node"] == "/runtime/selected-node"
    with pytest.raises(TypeError):
        receipt_view["nested"]["dependencies"].append("changed")
    with pytest.raises(TypeError):
        cast(Any, selected.runtime_executables)["node"] = "/wrong/node"
    with pytest.raises(FrozenInstanceError):
        setattr(selected, "path", tmp_path / "wrong")


def test_handle_path_cannot_point_outside_issued_cache(tmp_path):
    with pytest.raises(ValueError, match="inside"):
        runtime.PreparedHelperHandle("go", tmp_path / "cache", "key", tmp_path / "elsewhere",
                                     tmp_path / "elsewhere/helper", {})


def test_configuration_does_not_hold_artifacts_across_independent_calls(tmp_path):
    selected = handle(tmp_path)
    with runtime.helper_policy("auto", cache_dir="shared cache") as configured:
        assert configured.cache_dir == "shared cache"
        assert runtime.current_helper_operation() is None
        with runtime.helper_operation() as first:
            runtime.bind_helper(selected, source_root=tmp_path)
            assert runtime.pinned_helper("typescript", source_root=tmp_path) is selected
        assert runtime.current_helper_operation() is None
        with runtime.helper_operation() as second:
            assert second is not first and second.handles == {}
            assert runtime.pinned_helper("typescript") is None
        assert runtime.current_helper_configuration() is configured
    assert runtime.current_helper_configuration() is None


def test_internal_calls_keep_explicit_request_cache_over_config_default(tmp_path):
    selected = handle(tmp_path)
    messages = []
    callback = messages.append
    with runtime.helper_policy("auto", cache_dir="configured", progress=callback):
        with runtime.helper_operation(cache_dir="request") as outer:
            runtime.bind_helper(selected, source_root=tmp_path)
            with runtime.helper_operation() as nested:
                assert nested is outer and nested.cache_dir == "request"
                assert nested.progress is callback
                assert runtime.pinned_helper("typescript") is selected
            with runtime.helper_policy("never"):
                with runtime.helper_operation() as strict:
                    assert strict is not outer and strict.policy == "never"
                    assert strict.cache_dir == "request"
                    assert runtime.pinned_helper("typescript") is selected
            with runtime.helper_operation() as nested_again:
                assert nested_again is outer
    assert messages == []


def test_new_configuration_can_change_cache_without_mutating_outer_bindings(tmp_path):
    selected = handle(tmp_path)
    with runtime.helper_operation("auto", cache_dir="first") as outer:
        runtime.bind_helper(selected, source_root=tmp_path)
        with runtime.helper_policy("auto", cache_dir="second"):
            with runtime.helper_operation() as nested:
                assert nested is not outer and nested.cache_dir == "second"
                assert runtime.pinned_helper("typescript") is None
        assert runtime.current_helper_operation() is outer
        assert runtime.pinned_helper("typescript") is selected


@pytest.mark.parametrize("configured", [False, True])
def test_strict_parent_cannot_enable_setup_even_in_fresh_child(configured):
    scope = runtime.helper_policy("never") if configured else runtime.helper_operation("never")
    with scope:
        with pytest.raises(ValueError, match="strict helper scope"):
            with runtime.helper_operation("auto", fresh=True):
                pytest.fail("strict scope escaped")
        with pytest.raises(ValueError, match="strict helper scope"):
            with runtime.helper_policy("auto"):
                pytest.fail("strict configuration escaped")


def test_nested_failure_and_fresh_request_restore_current_operation(tmp_path):
    selected = handle(tmp_path)
    with runtime.helper_operation("auto") as outer:
        runtime.bind_helper(selected, source_root=tmp_path)
        with pytest.raises(RuntimeError, match="request failed"):
            with runtime.helper_operation(fresh=True) as separate:
                assert separate is not outer and separate.handles == {}
                raise RuntimeError("request failed")
        assert runtime.current_helper_operation() is outer
        assert runtime.pinned_helper("typescript") is selected
    assert runtime.current_helper_operation() is None


def test_binding_is_stable_and_source_language_specific(tmp_path):
    ts = handle(tmp_path, cache=tmp_path / "legacy")
    go = handle(tmp_path, "go", cache=tmp_path / "shared")
    with pytest.raises(ValueError, match="inside an analysis operation"):
        runtime.bind_helper(ts)
    with runtime.helper_operation():
        runtime.bind_helper(ts, source_root=tmp_path / "project")
        runtime.bind_helper(go, source_root=tmp_path / "project")
        assert runtime.operation_cache_root(tmp_path / "project", "typescript") == ts.cache_root
        assert runtime.operation_cache_root(tmp_path / "project", "go") == go.cache_root
        assert runtime.operation_cache_root(tmp_path / "project") is None
        assert runtime.pinned_helper("typescript", source_root=tmp_path / "other") is None
        assert runtime.pinned_helper("typescript", cache_root=go.cache_root) is None
        with pytest.raises(TypeError):
            cast(Any, runtime.current_helper_operation()).handles["go"] = ts
        with pytest.raises(ValueError, match="cannot be rebound"):
            runtime.bind_helper(handle(tmp_path, key="second"))
        assert runtime.pinned_helper("typescript") is ts


def write(root, name, text="fixture"):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_planning_reuses_selected_snapshot_and_requested_paths(tmp_path):
    for name in ("main.py", "app.ts", "view.jsx", "server.go", "lib.rs", "Main.hs"):
        write(tmp_path, name)
    snapshot = build_source_snapshot(tmp_path)
    assert runtime.required_helper_languages(snapshot, EXTRACTOR_REGISTRY) == (
        "typescript", "go", "rust", "haskell",
    )
    assert runtime.required_helper_languages(snapshot, EXTRACTOR_REGISTRY,
                                            only_files=["main.py"]) == ()
    assert runtime.required_helper_languages(snapshot, EXTRACTOR_REGISTRY,
                                            only_files=["view.jsx"]) == ("typescript",)
    assert runtime.required_helper_languages(snapshot, EXTRACTOR_REGISTRY,
                                            only_files=[]) == ()
    assert runtime.required_helper_languages(snapshot, EXTRACTOR_REGISTRY,
                                            only_files=["../outside.go"]) == ()


def test_plugin_replacement_never_prepares_unneeded_bundled_helper(tmp_path):
    write(tmp_path, "app.ts")
    write(tmp_path, "main.go")
    snapshot = build_source_snapshot(tmp_path)
    registry = {**EXTRACTOR_REGISTRY, "typescript": "custom.extractor:Owned", "go": "custom.go:Owned"}
    assert runtime.required_helper_languages(snapshot, registry) == ()


def test_planning_keeps_snapshot_exclusions_and_go_test_policy(tmp_path):
    write(tmp_path, ".gitignore", "ignored/\n")
    write(tmp_path, "main.py")
    write(tmp_path, "ignored/app.ts")
    write(tmp_path, "node_modules/dependency.ts")
    write(tmp_path, "public/assets/app.min.js")
    write(tmp_path, "only_test.go")
    ordinary = build_source_snapshot(tmp_path)
    assert runtime.required_helper_languages(ordinary, EXTRACTOR_REGISTRY) == ()
    with_tests = build_source_snapshot(tmp_path, include_tests=["go"])
    assert runtime.required_helper_languages(with_tests, EXTRACTOR_REGISTRY) == ("go",)


def test_planning_does_not_widen_persisted_source_selection(tmp_path):
    from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION

    write(tmp_path, "selected/main.py")
    write(tmp_path, "outside/app.ts")
    write(tmp_path, "outside/main.go")
    write(tmp_path, ".llm-wiki/source-selection.json", json.dumps({
        "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
        "include": ["selected"], "exclude": [],
    }))
    snapshot = build_source_snapshot(tmp_path)
    assert snapshot.source_selection_policy is not None
    assert runtime.required_helper_languages(snapshot, EXTRACTOR_REGISTRY) == ()
