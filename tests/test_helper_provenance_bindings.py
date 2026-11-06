"""Inspection describes the exact shared or operation-pinned helper inputs."""

from __future__ import annotations

from dataclasses import replace

import pytest

from llm_wiki_cli.services import extractor_helpers as helpers
from llm_wiki_cli.services import helper_cache as cache
from llm_wiki_cli.services.helper_runtime import bind_helper, helper_operation
from llm_wiki_cli.services.helper_preparation import prepare_operation_helpers
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.config import EXTRACTOR_REGISTRY

from tests.test_helper_cache import _native_header, _profile, _typescript_build
from tests.test_legacy_helper_validation import legacy_native
from tests.test_helper_preparation import _prepare_fixture


@pytest.fixture
def prepared_shared(tmp_path, monkeypatch):
    source = tmp_path / "project"
    source.mkdir()
    shared = tmp_path / "user-cache" / helpers.HELPER_CACHE_DIRNAME
    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    monkeypatch.setattr(cache, "user_helper_cache_root", lambda: shared)

    def profile(language, root, cwd):
        return _profile(language, root, cwd, toolchain=(
            "node v24.18.0; npm 11.16.0" if language == "typescript" else "test compiler"
        ))

    def build(language, stage, active, cwd):
        if language == "typescript":
            return _typescript_build(language, stage, active, cwd)
        artifact = stage / "artifact"
        artifact.mkdir()
        binary = artifact / helpers._binary_name("llm-wiki-" + language + "-extractor")
        binary.write_bytes(_native_header())
        binary.chmod(0o755)
        return {"version": helpers.HELPER_MANIFEST_VERSION,
                "language": language, "platform": helpers.platform_id(),
                "source_fingerprint": helpers.helper_source_fingerprint(language),
                "artifact_fingerprint": cache._native_fingerprint(binary),
                "toolchain": active.identity["toolchain"], "preparation_profile": active.identity}

    monkeypatch.setattr(cache, "_profile", profile)
    monkeypatch.setattr(cache, "_build", build)
    return source, shared


@pytest.mark.parametrize("language", ["go", "rust", "haskell", "typescript"])
@pytest.mark.parametrize("pinned", [False, True], ids=["unbound", "pinned"])
def test_shared_helper_identity_uses_actual_receipt_and_cache_without_setup(
    prepared_shared, monkeypatch, language, pinned,
):
    source, shared = prepared_shared
    handle = cache.ensure_helper(language, source)
    monkeypatch.setattr(cache, "ensure_helper", lambda *a, **k: pytest.fail("inspection prepared a helper"))
    monkeypatch.setattr(cache, "_profile", lambda *a, **k: pytest.fail("inspection probed a compiler"))
    monkeypatch.setattr(helpers, "command_output", lambda *a, **k: "v24.18.0" if language == "typescript" else pytest.fail("native helper needs no compiler"))
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in shared.rglob("*") if path.is_file()}
    with helper_operation("never"):
        if pinned:
            bind_helper(handle, source_root=source)
        observed = helpers.helper_identity(language, source)
    assert observed["status"] == "ready" and observed["issues"] == []
    assert observed["cache_root"] == str(shared)
    assert observed["current_artifact_fingerprint"] == handle.receipt["artifact_fingerprint"]
    assert observed["prepared"]["path"] == str(handle.path)
    assert observed["preparation_argv"][-2:] == ["--cache-dir", str(shared.parent)]
    assert before == {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in shared.rglob("*") if path.is_file()}
    assert list(source.iterdir()) == []


def test_typescript_identity_uses_pinned_physical_node_and_same_cache_recovery(
    prepared_shared, tmp_path, monkeypatch,
):
    source, shared = prepared_shared
    handle = cache.ensure_helper("typescript", source)
    node, other = tmp_path / "physical-node", tmp_path / "other-node"
    for path in (node, other):
        path.write_text("test runtime path\n")
    handle = replace(handle, runtime_executables={"node": str(node.resolve())})
    monkeypatch.setattr(helpers.shutil, "which", lambda *a, **k: str(other))
    commands = []

    def probe(argv):
        commands.append(argv)
        assert argv == [str(node.resolve()), "--version"]
        return "v99.0.0"

    monkeypatch.setattr(helpers, "command_output", probe)
    with helper_operation("never"):
        bind_helper(handle, source_root=source)
        observed = helpers.helper_identity("typescript", source)
    assert commands == [[str(node.resolve()), "--version"]]
    assert observed["active_runtime"] == {"kind": "node", "path": str(node.resolve()), "version": "v99.0.0"}
    assert observed["issues"] == ["active-runtime-mismatch"]
    assert str(shared) in observed["recovery"]
    assert observed["preparation_argv"][-2:] == ["--cache-dir", str(shared.parent)]


@pytest.mark.parametrize("language", ["go", "typescript"])
@pytest.mark.parametrize("invalid", ["scope", "artifact"])
def test_pinned_provenance_never_falls_back_to_another_ready_artifact(
    prepared_shared, tmp_path, monkeypatch, language, invalid,
):
    source, shared = prepared_shared
    selected = cache.ensure_helper(language, source)
    other_base = tmp_path / "other-cache"
    alternate = cache.ensure_helper(language, source, str(other_base))
    assert alternate.root != selected.root
    argument = None
    if invalid == "artifact":
        target = selected.root / "node_modules/ts-morph/index.js" if language == "typescript" else selected.path
        target.write_bytes(b"changed artifact")
    else:
        argument = str(other_base)
    monkeypatch.setattr(cache, "lookup_helper", lambda *a, **k: pytest.fail("pinned inspection selected another artifact"))
    monkeypatch.setattr(helpers, "command_output", lambda *a, **k: "v24.18.0")
    with helper_operation("never"):
        bind_helper(selected, source_root=source)
        observed = helpers.helper_identity(language, source, argument)
    assert observed["status"] == "unavailable-or-mismatched"
    assert ("helper-cache-scope-mismatch" if invalid == "scope" else "artifact-unavailable-or-mismatch") in observed["issues"]
    expected_base = other_base if invalid == "scope" else shared.parent
    assert observed["preparation_argv"][-2:] == ["--cache-dir", str(expected_base)]


@pytest.mark.parametrize("invalid", ["foreign-target", "outside-cache", "traversal"])
def test_invalid_native_legacy_diagnostics_do_not_hash_redirected_bytes(tmp_path, monkeypatch, invalid):
    import json

    base, artifact = legacy_native(tmp_path, "go", native=invalid != "foreign-target", redirect=invalid != "foreign-target")
    if invalid == "traversal":
        pointer = base / helpers.HELPER_CACHE_DIRNAME / "go" / helpers.HELPER_MANIFEST
        receipt = json.loads(pointer.read_text())
        receipt["path"] = str(base / helpers.HELPER_CACHE_DIRNAME / "go" / receipt["key"] / "../../../.." / artifact.name)
        pointer.write_text(json.dumps(receipt))
    monkeypatch.setattr(cache, "_native_fingerprint", lambda *a: pytest.fail("invalid native bytes were hashed"))
    observed = helpers.helper_identity("go", tmp_path, str(base))
    assert observed["status"] == "unavailable-or-mismatched"
    assert observed["current_artifact_fingerprint"] is None


@pytest.mark.parametrize("language", ["go", "typescript"])
def test_environment_cache_change_invalidates_pinned_getters_and_provenance(
    prepared_shared, tmp_path, monkeypatch, language,
):
    source, _shared = prepared_shared
    selected = cache.ensure_helper(language, source)
    other_base = tmp_path / "new-environment-cache"
    getter = helpers.get_prepared_typescript_root if language == "typescript" else (
        lambda src: helpers.get_prepared_binary(language, src)
    )
    with helper_operation("never"):
        bind_helper(selected, source_root=source)
        monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(other_base))
        assert getter(source) is None
        observed = helpers.helper_identity(language, source)
        assert observed["status"] == "unavailable-or-mismatched"
        assert "helper-cache-scope-mismatch" in observed["issues"]
        assert observed["preparation_argv"][-2:] == ["--cache-dir", str(other_base)]
    assert not other_base.exists()


@pytest.mark.parametrize("language,suffix", [("go", "go"), ("typescript", "ts")])
def test_no_git_recovery_prewarms_the_original_strict_lookup_scope(
    prepared_shared, monkeypatch, language, suffix,
):
    from llm_wiki_cli import cli
    from llm_wiki_cli.commands import prepare_extractors_cmd

    source, shared = prepared_shared
    monkeypatch.chdir(source)
    (source / ("main." + suffix)).write_text("selected source\n")
    argv = helpers.helper_preparation_argv(language, source)
    assert argv[-2:] == ["--cache-dir", str(shared.parent)]
    assert cache.cache_roots(source) == (shared,)
    monkeypatch.setattr(prepare_extractors_cmd, "prepare_helper", _prepare_fixture)
    prepare_extractors_cmd.run(cli._build_parser().parse_args(argv[1:]))
    with helper_operation("never"):
        selected = prepare_operation_helpers(build_source_snapshot(source), EXTRACTOR_REGISTRY)
    assert len(selected) == 1 and selected[0].cache_root == shared
    assert not (source / ".git").exists()
    assert not (source / ".llm-wiki").exists()
