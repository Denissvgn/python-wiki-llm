"""Automatic helper storage, independent profiles and publication boundaries."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from llm_wiki_cli.services import extractor_helpers as helpers
from llm_wiki_cli.services import helper_cache as cache

_REAL_PROFILE = cache._profile


def _typescript_build(language, stage, profile, cwd):
    assert language == "typescript"
    artifact = stage / "artifact"
    artifact.mkdir()
    dependency = artifact / "node_modules/ts-morph"
    dependency.mkdir(parents=True)
    (dependency / "index.js").write_text("module.exports={};\n")
    for name in helpers._TS_FILES:
        (artifact / name).write_bytes((helpers.TS_SCRIPTS_DIR / name).read_bytes())
    return {
        "version": helpers.TYPESCRIPT_HELPER_MANIFEST_VERSION,
        "language": language,
        "platform": helpers.platform_id(),
        "source_fingerprint": helpers.helper_source_fingerprint(language),
        "artifact_fingerprint": helpers.ts_identity.dependency_fingerprint(artifact / "node_modules"),
        "artifact_scope": helpers.ts_identity.ARTIFACT_SCOPE,
        "toolchain": profile.identity["toolchain"],
        "preparation_profile": profile.identity,
    }


def _profile(language, root, cwd, toolchain="node v24.18.0; npm 11.16.0"):
    return cache._Profile({"recipe": cache.RECIPE, "host": helpers.platform_id(),
                           "source": helpers.helper_source_fingerprint(language),
                           "toolchain": toolchain},
                          {"node": "selected-node", "npm": "selected-npm"}, {})


def _native_header():
    machine, system = cache._machine(), cache._system()
    if system == "darwin":
        cpu = {"arm64": 0x100000C, "x86_64": 0x1000007}[machine]
        return b"\xcf\xfa\xed\xfe" + cpu.to_bytes(4, "little")
    if system == "windows":
        header = bytearray(70)
        header[:2] = b"MZ"
        header[60:64] = (64).to_bytes(4, "little")
        header[64:68] = b"PE\0\0"
        header[68:70] = {"arm64": 0xAA64, "x86_64": 0x8664, "i386": 0x14C}[machine].to_bytes(2, "little")
        return bytes(header)
    cpu = {"arm64": 183, "x86_64": 62, "i386": 3, "riscv64": 243}[machine]
    return b"\x7fELF\x02\x01" + bytes(12) + cpu.to_bytes(2, "little")


def _native_build(language, stage, profile, cwd):
    artifact = stage / "artifact"
    artifact.mkdir()
    path = artifact / helpers._binary_name("llm-wiki-" + language + "-extractor")
    path.write_bytes(_native_header())
    path.chmod(0o755)
    return {"version": helpers.HELPER_MANIFEST_VERSION, "language": language,
            "platform": helpers.platform_id(), "toolchain": profile.identity["toolchain"],
            "preparation_profile": profile.identity,
            "source_fingerprint": helpers.helper_source_fingerprint(language),
            "artifact_fingerprint": cache._native_fingerprint(path)}


@pytest.fixture
def prepared_environment(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    user = tmp_path / "user helper cache"
    monkeypatch.setattr(cache, "user_helper_cache_root", lambda: user)
    monkeypatch.setattr(cache, "_profile", _profile)
    monkeypatch.setattr(cache, "_build", _typescript_build)
    return user


def test_shared_cold_warm_and_other_project_reuse(prepared_environment, tmp_path, monkeypatch):
    first, second = tmp_path / "one", tmp_path / "two"
    first.mkdir()
    second.mkdir()
    builds = []

    def build(*args):
        builds.append(args[0])
        return _typescript_build(*args)

    monkeypatch.setattr(cache, "_build", build)
    handle = cache.ensure_helper("typescript", first)
    assert cache.ensure_helper("typescript", first) == handle
    assert cache.ensure_helper("typescript", second) == handle
    assert builds == ["typescript"]
    assert handle.cache_root == prepared_environment
    assert cache.validate_handle(handle)
    assert not (first / ".git").exists() and not (second / ".git").exists()
    assert (handle.root / cache.RECEIPT).is_file()
    assert not (handle.cache_root / "typescript/current.json").exists()


def test_inspection_is_pure_and_cache_overrides_are_authoritative(prepared_environment, tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    assert cache.lookup_helper("typescript", project) is None
    assert not prepared_environment.exists()
    handle = cache.ensure_helper("typescript", project)
    selected = tmp_path / "configured"
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(selected))
    assert cache.lookup_helper("typescript", project) is None
    explicit = tmp_path / "explicit"
    assert cache.preparation_cache_root(project, str(explicit)) == explicit / helpers.HELPER_CACHE_DIRNAME
    assert cache.preparation_cache_root(project) == selected / helpers.HELPER_CACHE_DIRNAME
    assert cache.validate_handle(handle)
    assert not selected.exists() and not explicit.exists()


def test_valid_legacy_project_helper_is_reused_without_build(prepared_environment, tmp_path, monkeypatch):
    from tests.test_helper_preparation import _prepare_fixture

    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    legacy = project / ".git" / helpers.HELPER_CACHE_DIRNAME
    result = _prepare_fixture("typescript", legacy)
    handle = cache.lookup_helper("typescript", project)
    assert handle is not None and str(handle.path) == result.path
    monkeypatch.setattr(cache, "_build", lambda *args: pytest.fail("legacy helper remains valid"))
    selected = cache.ensure_helper("typescript", project)
    assert selected.root == handle.root and selected.receipt == handle.receipt
    assert selected.runtime_executables == {"node": "selected-node"}
    assert not prepared_environment.exists()


def test_valid_cache_needs_no_package_manager(prepared_environment, tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    expected = cache.ensure_helper("typescript", project)

    def unavailable(*args):
        error = cache.HelperPreparationError("typescript", "npm missing")
        error.runtime_executables = {"node": "selected-node"}
        raise error

    monkeypatch.setattr(cache, "_profile", unavailable)
    monkeypatch.setattr(cache, "_build", lambda *args: pytest.fail("no build tools needed"))
    assert cache.ensure_helper("typescript", project) == expected


@pytest.mark.parametrize("language", ["typescript", "go"])
@pytest.mark.parametrize("invalid", [None, 0, True, "2", 2.0])
def test_shared_receipt_requires_exact_typed_helper_version(
    prepared_environment, tmp_path, monkeypatch, language, invalid,
):
    if language != "typescript":
        monkeypatch.setattr(cache, "_build", _native_build)
    handle = cache.ensure_helper(language, tmp_path)
    value = json.loads((handle.root / cache.RECEIPT).read_text())
    value["manifest"]["version"] = invalid
    (handle.root / cache.RECEIPT).write_text(json.dumps(value))
    assert cache.lookup_helper(language, tmp_path) is None
    assert not cache.validate_handle(replace(handle, receipt=value["manifest"]))


@pytest.mark.parametrize("invalid", [None, "", True, 2, "different compiler"])
def test_shared_receipt_toolchain_must_match_keyed_profile(
    prepared_environment, tmp_path, invalid,
):
    handle = cache.ensure_helper("typescript", tmp_path)
    value = json.loads((handle.root / cache.RECEIPT).read_text())
    value["manifest"]["toolchain"] = invalid
    (handle.root / cache.RECEIPT).write_text(json.dumps(value))
    assert cache.lookup_helper("typescript", tmp_path) is None
    assert not cache.validate_handle(replace(handle, receipt=value["manifest"]))


@pytest.mark.parametrize("language", ["typescript", "go"])
def test_helper_abi_bump_uses_new_slot_and_preserves_prior_artifact_on_failure(
    prepared_environment, tmp_path, monkeypatch, language,
):
    build = _typescript_build if language == "typescript" else _native_build
    monkeypatch.setattr(cache, "_build", build)
    first = cache.ensure_helper(language, tmp_path)
    original = {path.relative_to(first.root): path.read_bytes()
                for path in first.root.rglob("*") if path.is_file()}
    version_name = "TYPESCRIPT_HELPER_MANIFEST_VERSION" if language == "typescript" else "HELPER_MANIFEST_VERSION"
    prior_version = getattr(helpers, version_name)
    monkeypatch.setattr(helpers, version_name, prior_version + 1)
    assert cache.lookup_helper(language, tmp_path) is None
    assert not cache.validate_handle(first)
    monkeypatch.setattr(cache, "_build", lambda *args: (_ for _ in ()).throw(RuntimeError("build unavailable")))
    with pytest.raises(cache.HelperPreparationError, match="build unavailable"):
        cache.ensure_helper(language, tmp_path)
    assert original == {path.relative_to(first.root): path.read_bytes()
                        for path in first.root.rglob("*") if path.is_file()}
    monkeypatch.setattr(cache, "_build", build)
    second = cache.ensure_helper(language, tmp_path)
    assert first.key != second.key and first.root != second.root
    assert second.receipt["version"] == prior_version + 1 and cache.validate_handle(second)
    assert original == {path.relative_to(first.root): path.read_bytes()
                        for path in first.root.rglob("*") if path.is_file()}
    monkeypatch.setattr(helpers, version_name, prior_version)
    assert cache.validate_handle(first)
    assert not list(prepared_environment.glob(".prepare-*"))


def test_foreign_typescript_execution_runtime_does_not_reuse_cached_dependencies(
    prepared_environment, tmp_path, monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()
    handle = cache.ensure_helper("typescript", project)

    def unavailable(*args):
        raise cache.HelperPreparationError("typescript", "Node is not native for the active platform")

    monkeypatch.setattr(cache, "_profile", unavailable)
    with pytest.raises(cache.HelperPreparationError, match="not native"):
        cache.ensure_helper("typescript", project)
    assert cache.validate_handle(handle)


def test_prepared_native_helper_is_reused_without_its_compiler(prepared_environment, tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()

    def build(language, stage, profile, cwd):
        artifact = stage / "artifact"
        artifact.mkdir()
        path = artifact / helpers._binary_name("llm-wiki-go-extractor")
        path.write_bytes(_native_header())
        path.chmod(0o755)
        return {"version": helpers.HELPER_MANIFEST_VERSION, "language": language,
                "platform": helpers.platform_id(), "toolchain": profile.identity["toolchain"],
                "preparation_profile": profile.identity,
                "source_fingerprint": helpers.helper_source_fingerprint(language),
                "artifact_fingerprint": cache._native_fingerprint(path)}

    monkeypatch.setattr(cache, "_build", build)
    first = cache.ensure_helper("go", project)
    monkeypatch.setattr(cache, "_profile", lambda *args: (_ for _ in ()).throw(
        cache.HelperPreparationError("go", "Go compiler not found")))
    assert cache.ensure_helper("go", project) == first
    assert cache.validate_handle(first)


def test_profile_change_creates_an_independent_immutable_slot(prepared_environment, tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    first = cache.ensure_helper("typescript", project)
    before = {p.relative_to(first.root): p.read_bytes() for p in first.root.rglob("*") if p.is_file()}
    monkeypatch.setattr(cache, "_profile", lambda *args: _profile(*args, toolchain="node v25.0.0; npm 12.0.0"))
    second = cache.ensure_helper("typescript", project)
    assert second.key != first.key and second.root != first.root
    assert before == {p.relative_to(first.root): p.read_bytes() for p in first.root.rglob("*") if p.is_file()}
    assert cache.validate_handle(first) and cache.validate_handle(second)


def test_strict_lookup_prefers_selected_node_among_multiple_ready_profiles(
    prepared_environment, tmp_path, monkeypatch,
):
    from llm_wiki_cli.services.helper_preparation import prepare_operation_helpers
    from llm_wiki_cli.services.helper_runtime import helper_operation
    from llm_wiki_cli.services.source_snapshot import build_source_snapshot
    from llm_wiki_cli.config import EXTRACTOR_REGISTRY

    project = tmp_path / "project"
    project.mkdir()
    (project / "main.ts").write_text("export const value = 1;\n")
    node = tmp_path / "node"
    monkeypatch.setattr(cache.shutil, "which", lambda name: str(node) if name == "node" else None)

    def profile(language, root, cwd):
        selected = _profile(language, root, cwd)
        selected.identity["executables"] = cache._executable_identity({"node": str(node)})
        selected.executables["node"] = str(node)
        return selected

    monkeypatch.setattr(cache, "_profile", profile)
    versions = {}
    for content in (b"first Node binary", b"replaced Node binary"):
        node.write_bytes(content)
        handle = cache.ensure_helper("typescript", project)
        versions[handle.key] = content
    assert len(versions) == 2
    # Filename ordering cannot tell which binary is currently installed.
    selected_key = max(versions)
    node.write_bytes(versions[selected_key])
    monkeypatch.setattr(cache, "_run", lambda *a, **k: pytest.fail("lookup ran a tool"))
    monkeypatch.setattr(cache, "ensure_helper", lambda *a, **k: pytest.fail("strict read prepared"))
    with helper_operation("never"):
        selected, = prepare_operation_helpers(build_source_snapshot(project), EXTRACTOR_REGISTRY)
    assert selected.key == selected_key


def test_failed_verbose_build_reports_the_final_tool_error(tmp_path):
    command = [sys.executable, "-c", "print('x' * 1100000); print('missing dependency at end'); raise SystemExit(3)"]
    with pytest.raises(RuntimeError, match="missing dependency at end") as captured:
        cache._run(command, cwd=tmp_path, env=dict(os.environ), timeout=10)
    assert len(str(captured.value)) < 5000


def test_toolchain_error_includes_cache_selected_by_ensure(prepared_environment, tmp_path, monkeypatch):
    def missing(*args):
        raise cache.HelperPreparationError("typescript", "Node missing")

    monkeypatch.setattr(cache, "_profile", missing)
    with pytest.raises(cache.HelperPreparationError) as error:
        cache.ensure_helper("typescript", tmp_path)
    assert error.value.reason == "Node missing"
    assert str(prepared_environment) in str(error.value)


def test_optional_shared_lookup_failure_preserves_verified_legacy_helper(prepared_environment, tmp_path):
    from tests.test_helper_preparation import _prepare_fixture

    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    result = _prepare_fixture("typescript", project / ".git" / helpers.HELPER_CACHE_DIRNAME)
    prepared_environment.symlink_to(tmp_path / "outside")
    found = cache.lookup_helper("typescript", project)
    assert found is not None and str(found.path) == result.path


def test_warm_second_profile_does_not_require_a_writable_cache(prepared_environment, tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    versions = {}
    for npm in ("11.0.0", "12.0.0"):
        version = f"node v24.18.0; npm {npm}"
        monkeypatch.setattr(cache, "_profile", lambda *args, v=version: _profile(*args, toolchain=v))
        selected = cache.ensure_helper("typescript", project)
        versions[selected.key] = version
    wanted = max(versions)
    monkeypatch.setattr(cache, "_profile", lambda *args: _profile(*args, toolchain=versions[wanted]))
    monkeypatch.setattr(cache, "_lock", lambda *args: pytest.fail("warm read opened a writer lock"))
    assert cache.ensure_helper("typescript", project).key == wanted


def test_racing_profiles_cannot_make_existing_cache_unreadable(prepared_environment, tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "MAX_HELPER_PROFILES", 1)
    monkeypatch.setattr(cache, "_profile", lambda *args: _profile(*args, toolchain=threading.current_thread().name))
    started = threading.Barrier(2)

    def build(*args):
        started.wait(timeout=10)
        return _typescript_build(*args)

    monkeypatch.setattr(cache, "_build", build)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(cache.ensure_helper, "typescript", tmp_path) for _ in range(2)]
        failures = [future.exception() for future in futures if future.exception() is not None]
        assert len(failures) == 1 and isinstance(failures[0], cache.HelperPreparationError)
        assert "profile limit" in str(failures[0])
        published, = [future.result() for future in futures if future.exception() is None]
    found = cache.lookup_helper("typescript", tmp_path)
    assert found is not None and found.key == published.key
    monkeypatch.setattr(cache, "_build", lambda *a: pytest.fail("full cache built another profile"))
    with pytest.raises(cache.HelperPreparationError, match="profile limit"):
        cache.ensure_helper("typescript", tmp_path)
    assert cache.validate_handle(published)


def test_malformed_deep_receipt_is_repaired(prepared_environment, tmp_path):
    original = cache.ensure_helper("typescript", tmp_path)
    (original.root / cache.RECEIPT).write_bytes(b"[" * 5000 + b"]" * 5000)
    assert cache.lookup_helper("typescript", tmp_path) is None
    repaired = cache.ensure_helper("typescript", tmp_path)
    assert repaired.key == original.key and cache.validate_handle(repaired)


def test_malformed_deep_legacy_receipt_reports_unavailable(tmp_path):
    pointer = tmp_path / helpers.HELPER_CACHE_DIRNAME / "typescript" / helpers.HELPER_MANIFEST
    pointer.parent.mkdir(parents=True)
    pointer.write_bytes(b"[" * 5000 + b"]" * 5000)
    identity = helpers.helper_identity("typescript", tmp_path, str(tmp_path))
    assert identity["status"] == "unavailable-or-mismatched" and identity["prepared"] is None


def test_same_version_changed_toolchain_bytes_change_profile_key(prepared_environment, tmp_path, monkeypatch):
    compiler = tmp_path / "compiler"
    compiler.write_bytes(b"first compiler build")
    base = {"recipe": cache.RECIPE, "host": helpers.platform_id(), "toolchain": "same version",
            "source": helpers.helper_source_fingerprint("typescript")}
    first = {**base, "executables": cache._executable_identity({"go": str(compiler)})}
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr(cache, "_profile", lambda *args: cache._Profile(
        {**base, "executables": cache._executable_identity({"go": str(compiler)})},
        {"node": "selected-node", "npm": "selected-npm"}, {}))
    one = cache.ensure_helper("typescript", project)
    compiler.write_bytes(b"other compiler build")
    second = {**base, "executables": cache._executable_identity({"go": str(compiler)})}
    two = cache.ensure_helper("typescript", project)
    assert first["toolchain"] == second["toolchain"]
    assert cache._profile_key("go", first) != cache._profile_key("go", second)
    assert one.key != two.key and cache.validate_handle(one) and cache.validate_handle(two)


def test_operator_toolchain_symlinks_and_hardlinks_are_not_cache_redirects(tmp_path):
    executable = tmp_path / "compiler"
    executable.write_bytes(b"selected executable")
    alias = tmp_path / "compiler-proxy"
    alias.symlink_to(executable)
    hardlink = tmp_path / "compiler-hardlink"
    os.link(executable, hardlink)
    observed = cache._executable_identity({"proxy": str(alias), "hardlink": str(hardlink)})
    assert observed["proxy"]["path"] == str(executable)
    assert observed["proxy"]["sha256"] == observed["hardlink"]["sha256"]


def test_typescript_runtime_pins_physical_node_when_selection_alias_changes(
    prepared_environment, tmp_path, monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()
    one, two, npm = (tmp_path / name for name in ("node-one", "node-two", "npm"))
    one.write_bytes(b"selected Node runtime")
    two.write_bytes(b"different Node runtime")
    npm.write_bytes(b"selected package manager")
    alias = tmp_path / "current-node"
    alias.symlink_to(one)
    monkeypatch.setattr(cache, "_profile", _REAL_PROFILE)
    monkeypatch.setattr(cache.shutil, "which", lambda name, path=None: str(alias if name == "node" else npm))

    def output(command, *, cwd, env):
        if command[0] == str(npm):
            return "11.16.0"
        assert command[0] == str(one)
        if command[1] == "--version":
            return "v24.18.0"
        return {"windows": "win32"}.get(cache._system(), cache._system()) + " " + {
            "x86_64": "x64", "i386": "ia32",
        }.get(cache._machine(), cache._machine())

    monkeypatch.setattr(cache, "_output", output)
    handle = cache.ensure_helper("typescript", project)
    alias.unlink()
    alias.symlink_to(two)
    assert handle.runtime_executables["node"] == str(one)
    recorded = handle.receipt["preparation_profile"]
    assert isinstance(recorded, dict)
    assert recorded["executables"]["node"]["path"] == str(one)
    assert cache.validate_handle(handle)


def test_npm_shebang_uses_pinned_node_when_selection_alias_changes(tmp_path, monkeypatch):
    first, second, aliases = (tmp_path / name for name in ("first", "second", "aliases"))
    for directory in (first, second, aliases):
        directory.mkdir()
    node_name = "node.exe" if os.name == "nt" else "node"
    one, two = first / node_name, second / node_name
    for path in (one, two):
        path.write_bytes(b"owned Node executable " + str(path.parent).encode())
        path.chmod(0o755)
    alias = aliases / node_name
    alias.symlink_to(one)
    npm = aliases / ("npm.cmd" if os.name == "nt" else "npm")
    npm.write_bytes(b"owned npm launcher")
    npm.chmod(0o755)
    monkeypatch.setenv("PATH", str(aliases))

    def output(command, *, cwd, env):
        if command[0] == str(npm):
            alias.unlink()
            alias.symlink_to(two)
            selected = cache.shutil.which("node", path=env["PATH"])
            assert selected is not None and Path(selected).resolve() == one
            return "11.16.0"
        assert command[0] == str(one)
        if command[1] == "--version":
            return "v24.18.0"
        return {"windows": "win32"}.get(cache._system(), cache._system()) + " " + {
            "x86_64": "x64", "i386": "ia32",
        }.get(cache._machine(), cache._machine())

    monkeypatch.setattr(cache, "_output", output)
    profile = cache._profile("typescript", tmp_path / "cache", tmp_path)
    assert profile.executables["node"] == str(one)
    assert profile.identity["executables"]["node"]["path"] == str(one)


def test_failed_build_and_cancellation_preserve_prior_valid_slot(prepared_environment, tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    first = cache.ensure_helper("typescript", project)
    monkeypatch.setattr(cache, "_profile", lambda *args: _profile(*args, toolchain="changed profile"))

    def fail(*args):
        (args[1] / "partial").write_bytes(b"partial")
        raise RuntimeError("network unavailable")

    monkeypatch.setattr(cache, "_build", fail)
    with pytest.raises(cache.HelperPreparationError, match="network unavailable") as error:
        cache.ensure_helper("typescript", project)
    assert error.value.language == "typescript" and error.value.cache_root == prepared_environment
    assert cache.validate_handle(first)
    assert not list(prepared_environment.glob(".prepare-*"))

    def cancel(*args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(cache, "_build", cancel)
    with pytest.raises(KeyboardInterrupt):
        cache.ensure_helper("typescript", project)
    assert cache.validate_handle(first)
    assert not list(prepared_environment.glob(".prepare-*"))


@pytest.mark.parametrize("language", ["typescript", "go", "rust", "haskell"])
def test_explicit_cache_build_stays_outside_target_project_workspace(
    prepared_environment, tmp_path, monkeypatch, language,
):
    project = tmp_path / "workspace"
    dependencies = project / "node_modules"
    dependencies.mkdir(parents=True)
    sentinel = dependencies / "user-dependency"
    sentinel.write_text("keep target dependencies")
    (project / "package.json").write_text(json.dumps({"name": "user-workspace", "private": True,
        "workspaces": ["cache/llm-wiki-extractors/.prepare-typescript-*/artifact"]}))
    selected = project / "cache"
    stages = []

    def build(language, stage, profile, cwd):
        # npm can discover a matching ancestor workspace through its own
        # package.json; Go and Rust also search ancestors for configuration.
        assert not stage.resolve().is_relative_to(project.resolve())
        assert not cwd.resolve().is_relative_to(project.resolve())
        stages.append(stage)
        if language == "typescript":
            return _typescript_build(language, stage, profile, cwd)
        artifact = stage / "artifact"
        artifact.mkdir()
        path = artifact / helpers._binary_name("llm-wiki-" + language + "-extractor")
        path.write_bytes(_native_header())
        path.chmod(0o755)
        return {"version": helpers.HELPER_MANIFEST_VERSION, "language": language,
                "platform": helpers.platform_id(), "toolchain": profile.identity["toolchain"],
                "preparation_profile": profile.identity,
                "source_fingerprint": helpers.helper_source_fingerprint(language),
                "artifact_fingerprint": cache._native_fingerprint(path)}

    monkeypatch.setattr(cache, "_build", build)
    handle = cache.ensure_helper(language, project, str(selected))
    assert handle.root.is_relative_to(selected) and cache.validate_handle(handle)
    assert sentinel.read_text() == "keep target dependencies"
    assert stages and not any(path.exists() for path in stages)
    assert not list(handle.cache_root.glob(".prepare-*"))


@pytest.mark.parametrize("failure", [OSError, KeyboardInterrupt])
def test_failed_or_cancelled_artifact_copy_preserves_prior_slot(
    prepared_environment, tmp_path, monkeypatch, failure,
):
    project = tmp_path / "project"
    project.mkdir()
    first = cache.ensure_helper("typescript", project)
    monkeypatch.setattr(cache, "_profile", lambda *args: _profile(*args, toolchain="changed profile"))
    build_stages = []

    def build(*args):
        build_stages.append(args[1])
        return _typescript_build(*args)

    def copy(language, source, destination):
        destination.mkdir()
        (destination / "partial").write_bytes(b"partial copy")
        raise failure("interrupted artifact copy")

    monkeypatch.setattr(cache, "_build", build)
    monkeypatch.setattr(cache, "_copy_artifact", copy)
    expected = KeyboardInterrupt if failure is KeyboardInterrupt else cache.HelperPreparationError
    with pytest.raises(expected, match="interrupted artifact copy"):
        cache.ensure_helper("typescript", project)
    assert cache.validate_handle(first)
    assert list((prepared_environment / "typescript").iterdir()) == [first.root]
    assert not list(prepared_environment.glob(".prepare-*"))
    assert build_stages and not any(path.exists() for path in build_stages)


def test_artifact_copy_is_verified_before_publication(prepared_environment, tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    first = cache.ensure_helper("typescript", project)
    monkeypatch.setattr(cache, "_profile", lambda *args: _profile(*args, toolchain="changed profile"))
    original = cache._copy_artifact

    def copy(language, source, destination):
        original(language, source, destination)
        (destination / "node_modules/ts-morph/index.js").write_bytes(b"changed during copy")

    monkeypatch.setattr(cache, "_copy_artifact", copy)
    with pytest.raises(cache.HelperPreparationError, match="artifact changed"):
        cache.ensure_helper("typescript", project)
    assert cache.validate_handle(first)
    assert list((prepared_environment / "typescript").iterdir()) == [first.root]
    assert not list(prepared_environment.glob(".prepare-*"))


def test_failed_atomic_publication_preserves_prior_slot(prepared_environment, tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    first = cache.ensure_helper("typescript", project)
    monkeypatch.setattr(cache, "_profile", lambda *args: _profile(*args, toolchain="changed profile"))
    original = cache.os.rename

    def rename(source, destination):
        if Path(source).name == "artifact":
            raise OSError("publication unavailable")
        return original(source, destination)

    monkeypatch.setattr(cache.os, "rename", rename)
    with pytest.raises(cache.HelperPreparationError, match="publication unavailable"):
        cache.ensure_helper("typescript", project)
    assert cache.validate_handle(first)
    assert list((prepared_environment / "typescript").iterdir()) == [first.root]
    assert not list(prepared_environment.glob(".prepare-*"))


def test_corrupt_pinned_artifact_is_not_rebound_during_validation(prepared_environment, tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    handle = cache.ensure_helper("typescript", project)
    (handle.path / "index.js").write_bytes(b"changed")
    assert not cache.validate_handle(handle)
    repaired = cache.ensure_helper("typescript", project)
    assert repaired.root == handle.root and cache.validate_handle(repaired)
    assert list(handle.root.parent.glob(".rejected-*"))


def test_two_threads_publish_once_and_no_reader_sees_staging(prepared_environment, tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    started, finish = threading.Event(), threading.Event()
    builds = []

    def build(*args):
        builds.append(args[0])
        started.set()
        assert finish.wait(5)
        return _typescript_build(*args)

    monkeypatch.setattr(cache, "_build", build)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(cache.ensure_helper, "typescript", project)
        assert started.wait(5)
        second = pool.submit(cache.ensure_helper, "typescript", project)
        assert cache.lookup_helper("typescript", project) is None
        finish.set()
        one, two = first.result(), second.result()
    assert one == two and builds == ["typescript"]


def test_separate_processes_serialize_one_profile(tmp_path):
    project, user, journal = tmp_path / "project", tmp_path / "shared", tmp_path / "builds"
    project.mkdir()
    script = """import json,pathlib,sys,time
sys.path.insert(0,sys.argv[4])
from llm_wiki_cli.services import helper_cache as cache
from tests.test_helper_cache import _profile,_typescript_build
root,project,journal=map(pathlib.Path,sys.argv[1:4])
cache.user_helper_cache_root=lambda:root
cache._profile=_profile
def build(*args):
 with journal.open('a') as stream:stream.write('build\\n')
 time.sleep(0.2)
 return _typescript_build(*args)
cache._build=build
handle=cache.ensure_helper('typescript',project)
print(json.dumps({'key':handle.key,'root':str(handle.root),'valid':cache.validate_handle(handle)}))
"""
    env = dict(os.environ)
    env.pop("LLM_WIKI_CACHE_DIR", None)
    root = Path(__file__).resolve().parents[1]
    children = [subprocess.Popen([sys.executable, "-c", script, str(user), str(project), str(journal), str(root / "src")],
                                cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True) for _ in range(2)]
    observed = []
    try:
        for child in children:
            output, error = child.communicate(timeout=15)
            assert child.returncode == 0, error
            observed.append(json.loads(output))
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
            if child.stdout is not None:
                child.stdout.close()
            if child.stderr is not None:
                child.stderr.close()
    assert observed[0] == observed[1] and observed[0]["valid"] is True
    assert journal.read_text().splitlines() == ["build"]


@pytest.mark.parametrize("machine,system,header,valid", [
    ("aarch64", "Linux", b"\x7fELF\x02\x01" + bytes(12) + (183).to_bytes(2, "little"), True),
    ("aarch64", "Linux", b"\x7fELF\x02\x01" + bytes(12) + (62).to_bytes(2, "little"), False),
    ("arm64", "Darwin", b"\xcf\xfa\xed\xfe" + (0x100000C).to_bytes(4, "little"), True),
    ("arm64", "Darwin", b"\xcf\xfa\xed\xfe" + (0x1000007).to_bytes(4, "little"), False),
])
def test_native_output_is_bound_to_active_platform(tmp_path, monkeypatch, machine, system, header, valid):
    path = tmp_path / "helper"
    path.write_bytes(header)
    path.chmod(0o755)
    monkeypatch.setattr(cache.platform, "machine", lambda: machine)
    monkeypatch.setattr(cache.platform, "system", lambda: system)
    if valid:
        cache._native_binary(path)
    else:
        with pytest.raises(ValueError, match="not native"):
            cache._native_binary(path)


def test_project_build_targets_are_removed_without_mutating_environment(tmp_path, monkeypatch):
    supplied = {"GOOS": "windows", "GOARCH": "386", "GOFLAGS": "-mod=mod", "GOWORK": "project.work",
                "GOROOT": "project SDK", "GOEXPERIMENT": "project experiment",
                "CARGO_BUILD_TARGET": "foreign", "CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_RUSTFLAGS": "bad",
                "RUSTC": "project rustc", "RUSTC_WRAPPER": "project wrapper",
                "RUSTC_WORKSPACE_WRAPPER": "project workspace", "CARGO_BUILD_RUSTC": "other rustc",
                "CARGO_BUILD_RUSTFLAGS": "foreign flags", "CARGO_PROFILE_RELEASE_OVERFLOW_CHECKS": "false",
                "RUSTC_BOOTSTRAP": "1",
                "RUSTFLAGS": "bad", "CARGO_ENCODED_RUSTFLAGS": "bad", "GHC_PACKAGE_PATH": "project",
                "NODE_OPTIONS": "--require=project.js", "NODE_PATH": "project-node"}
    for name, value in supplied.items():
        monkeypatch.setenv(name, value)
    env = cache._build_environment(tmp_path)
    assert env["GOENV"] == "off" and env["GOWORK"] == "off" and env["GOTOOLCHAIN"] == "local"
    assert env["CGO_ENABLED"] == "0" and env["RUSTUP_AUTO_INSTALL"] == "0"
    assert env["GHC_ENVIRONMENT"] == "-"
    assert not any(key in env for key in supplied if key not in {"GOOS", "GOARCH", "GOFLAGS", "GOWORK"})
    assert all(os.environ[name] == value for name, value in supplied.items())


def test_go_compiler_host_must_match_actual_platform_before_build(tmp_path, monkeypatch):
    monkeypatch.setattr(cache.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(cache.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(helpers, "_resolve_go_executable", lambda env: "selected-go")
    observed = []

    def output(command, *, cwd, env):
        observed.append((command, env))
        return "go version go1.26.5 darwin/amd64"

    monkeypatch.setattr(cache, "_output", output)
    with pytest.raises(cache.HelperPreparationError, match="host differs"):
        cache._profile("go", tmp_path / "cache", tmp_path)
    assert observed[0][1]["GOTOOLCHAIN"] == "local"
    assert not (tmp_path / "cache").exists()


def test_rust_uses_copied_manifest_and_external_build_cwd(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "Cargo.toml").write_text("user project must not build")
    stage = project / "explicit cache/staging"
    stage.mkdir(parents=True)
    with cache._sandbox(project) as sandbox:
        cwd = Path(sandbox)
        assert not cwd.is_relative_to(project)
        profile = cache._Profile({"toolchain": "cargo owned", "target": "host-triple"},
                                 {"cargo": "selected-cargo"}, cache._build_environment(stage))
        commands = []

        def run(command, *, cwd, env, timeout):
            commands.append((command, cwd, env))
            source = Path(command[command.index("--manifest-path") + 1])
            assert source == stage / "source/Cargo.toml"
            assert source.read_bytes() == (helpers.RUST_SCRIPTS_DIR / "Cargo.toml").read_bytes()
            target = Path(command[command.index("--target-dir") + 1]) / "host-triple/release"
            target.mkdir(parents=True)
            path = target / helpers._binary_name("llm-wiki-rust-extractor")
            path.write_bytes(_native_header())
            path.chmod(0o755)
            return ""

        monkeypatch.setattr(cache, "_run", run)
        monkeypatch.setattr(cache, "_executable_identity", lambda paths: {})
        profile.identity["executables"] = {}
        receipt = cache._build("rust", stage, profile, cwd)
    assert commands[0][1] == cwd and commands[0][2]["RUSTUP_AUTO_INSTALL"] == "0"
    assert receipt["language"] == "rust"
    assert (project / "Cargo.toml").read_text() == "user project must not build"


def test_rust_profile_forces_the_compiler_it_validated(tmp_path, monkeypatch):
    monkeypatch.setenv("RUSTC", "project-compiler")
    monkeypatch.setenv("RUSTC_WRAPPER", "project-wrapper")
    monkeypatch.setenv("CARGO_BUILD_RUSTC", "other-compiler")
    monkeypatch.setattr(cache.platform, "system", lambda: "Linux")
    monkeypatch.setattr(cache.platform, "machine", lambda: "aarch64")
    monkeypatch.setattr(cache.shutil, "which", lambda name, path=None: "/selected/" + name)
    monkeypatch.setattr(cache, "_executable_identity", lambda paths: {name: path for name, path in paths.items()})

    def output(command, *, cwd, env):
        assert "RUSTC" not in env and "RUSTC_WRAPPER" not in env
        return "cargo 1.94.0" if command[0].endswith("cargo") else "rustc 1.94.0\nhost: aarch64-unknown-linux-gnu"

    monkeypatch.setattr(cache, "_output", output)
    profile = cache._profile("rust", tmp_path / "cache", tmp_path)
    assert profile.environment["RUSTC"] == "/selected/rustc"
    assert profile.environment["RUSTC_WRAPPER"] == profile.environment["RUSTC_WORKSPACE_WRAPPER"] == ""
    assert "CARGO_BUILD_RUSTC" not in profile.environment


@pytest.mark.parametrize("proxy_kind", ["symlink", "hardlink"])
def test_rustup_profiles_pin_actual_same_version_cargo_and_rustc(
    prepared_environment, tmp_path, monkeypatch, proxy_kind,
):
    binaries = tmp_path / "bin"
    binaries.mkdir()
    suffix = ".exe" if os.name == "nt" else ""
    launcher = binaries / ("rustup" + suffix)
    launcher.write_bytes(b"stable rustup dispatcher")
    launcher.chmod(0o755)
    for name in ("cargo", "rustc"):
        proxy = binaries / (name + suffix)
        if proxy_kind == "symlink":
            proxy.symlink_to(launcher)
        else:
            os.link(launcher, proxy)
        for label in ("A", "B"):
            target = tmp_path / "toolchains" / label / "bin" / (name + suffix)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((name + " actual build " + label).encode())
            target.chmod(0o755)
    monkeypatch.setenv("PATH", str(binaries))
    monkeypatch.setenv("RUSTUP_TOOLCHAIN", "A")
    monkeypatch.setattr(cache.platform, "system", lambda: "Linux")
    monkeypatch.setattr(cache.platform, "machine", lambda: "aarch64")
    monkeypatch.setattr(cache, "_profile", _REAL_PROFILE)
    probes = []

    def output(command, *, cwd, env):
        probes.append(command)
        if command[:2] == [str(launcher), "which"]:
            return str(tmp_path / "toolchains" / env["RUSTUP_TOOLCHAIN"] / "bin" / (command[2] + suffix))
        name = Path(command[0]).stem
        assert "toolchains" in Path(command[0]).parts
        return "cargo 1.94.0" if name == "cargo" else "rustc 1.94.0\nhost: aarch64-unknown-linux-gnu"

    builds = []

    def build(language, stage, profile, cwd):
        builds.append(profile.environment["RUSTUP_TOOLCHAIN"])
        assert profile.environment["RUSTC"] == profile.executables["rustc"]
        assert all("toolchains" in Path(path).parts for path in profile.executables.values())
        artifact = stage / "artifact"
        artifact.mkdir()
        path = artifact / helpers._binary_name("llm-wiki-rust-extractor")
        path.write_bytes(_native_header() + profile.environment["RUSTUP_TOOLCHAIN"].encode())
        path.chmod(0o755)
        return {"version": helpers.HELPER_MANIFEST_VERSION, "language": language,
                "platform": helpers.platform_id(), "source_fingerprint": helpers.helper_source_fingerprint(language),
                "artifact_fingerprint": cache._native_fingerprint(path),
                "toolchain": profile.identity["toolchain"], "preparation_profile": profile.identity}

    monkeypatch.setattr(cache, "_output", output)
    monkeypatch.setattr(cache, "_build", build)
    project = tmp_path / "project"
    project.mkdir()
    first = cache.ensure_helper("rust", project)
    monkeypatch.setenv("RUSTUP_TOOLCHAIN", "B")
    second = cache.ensure_helper("rust", project)
    assert first.key != second.key and builds == ["A", "B"]
    assert first.path.read_bytes().endswith(b"A") and second.path.read_bytes().endswith(b"B")
    assert first.receipt["toolchain"] == second.receipt["toolchain"]
    assert {row[2] for row in probes if row[1] == "which"} == {"cargo", "rustc"}
    recorded = second.receipt["preparation_profile"]
    assert isinstance(recorded, dict)
    for row in recorded["executables"].values():
        assert isinstance(row, dict) and "toolchains" in row["path"]
    # Replacing either actual tool at the same selected path must also change
    # identity even if every printed version and the rustup proxy stay fixed.
    previous = second
    for name in ("cargo", "rustc"):
        target = tmp_path / "toolchains/B/bin" / (name + suffix)
        target.write_bytes(target.read_bytes() + b" same-version replacement")
        changed = cache.ensure_helper("rust", project)
        assert changed.key != previous.key and changed.receipt["toolchain"] == previous.receipt["toolchain"]
        previous = changed
    assert builds == ["A", "B", "B", "B"]


def test_rustup_unresolved_or_recursive_tool_selection_fails_closed(tmp_path, monkeypatch):
    binaries = tmp_path / "bin"
    binaries.mkdir()
    launcher = binaries / ("rustup.exe" if os.name == "nt" else "rustup")
    launcher.write_bytes(b"owned dispatcher")
    launcher.chmod(0o755)
    proxy = binaries / ("cargo.exe" if os.name == "nt" else "cargo")
    proxy.symlink_to(launcher)
    monkeypatch.setattr(cache.shutil, "which", lambda name, path=None: str(proxy))
    monkeypatch.setattr(cache, "_output", lambda *args, **kwargs: "relative-cargo")
    with pytest.raises(cache.HelperPreparationError, match="absolute cargo"):
        cache._selected_rust_executable("cargo", {}, tmp_path)
    monkeypatch.setattr(cache, "_output", lambda *args, **kwargs: str(launcher))
    with pytest.raises(cache.HelperPreparationError, match="dispatcher instead of cargo"):
        cache._selected_rust_executable("cargo", {}, tmp_path)


def test_build_sandbox_does_not_follow_alias_back_into_project(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / "build-temp").mkdir(parents=True)
    alias = tmp_path / "outside-looking-temp"
    alias.symlink_to(project / "build-temp", target_is_directory=True)
    monkeypatch.setattr(cache.tempfile, "gettempdir", lambda: str(alias))
    with cache._sandbox(project) as name:
        assert not Path(name).resolve().is_relative_to(project)
    assert list((project / "build-temp").iterdir()) == []


def test_subprocess_timeout_stops_process_tree(tmp_path):
    marker = tmp_path / "late-write"
    command = [sys.executable, "-c", "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c',"
               + repr("import pathlib,time;time.sleep(0.5);pathlib.Path(" + repr(str(marker)) + ").write_text('orphan')")
               + "]);time.sleep(30)"]
    with pytest.raises(subprocess.TimeoutExpired):
        cache._run(command, cwd=tmp_path, env=dict(os.environ), timeout=0.1)
    time.sleep(0.7)
    assert not marker.exists()


def test_native_cache_fingerprint_matches_existing_receipt_format(tmp_path):
    path = tmp_path / "helper"
    path.write_bytes(b"owned bytes")
    assert cache._native_fingerprint(path) == helpers.helper_artifact_fingerprint(path)


def test_internal_language_redirect_is_refused_before_build(prepared_environment, tmp_path, monkeypatch):
    outside = tmp_path / "unrelated"
    outside.mkdir()
    sentinel = outside / "keep"
    sentinel.write_bytes(b"unrelated bytes")
    prepared_environment.mkdir()
    (prepared_environment / "typescript").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(cache, "_build", lambda *args: pytest.fail("unsafe cache must not build"))
    with pytest.raises(cache.HelperPreparationError, match="link or reparse"):
        cache.ensure_helper("typescript", tmp_path)
    assert list(outside.iterdir()) == [sentinel] and sentinel.read_bytes() == b"unrelated bytes"


def test_build_dependency_redirect_cannot_receive_writes(tmp_path):
    root, outside = tmp_path / "cache", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / ".dependencies").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="link or reparse"):
        cache._build_environment(root)
    assert list(outside.iterdir()) == []


def test_legacy_receipt_cannot_read_an_artifact_outside_cache(tmp_path, monkeypatch):
    source = tmp_path / "source"
    (source / ".git").mkdir(parents=True)
    root = source / ".git" / helpers.HELPER_CACHE_DIRNAME
    (root / "go").mkdir(parents=True)
    outside = tmp_path / "private"
    outside.write_bytes(b"do not inspect")
    key = helpers.helper_cache_key("go", toolchain_version="go selected")
    (root / "go/current.json").write_text(json.dumps({
        "version": helpers.HELPER_MANIFEST_VERSION, "language": "go", "platform": helpers.platform_id(),
        "source_fingerprint": helpers.helper_source_fingerprint("go"), "toolchain": "go selected",
        "key": key, "path": str(outside), "artifact_fingerprint": "irrelevant",
    }))
    monkeypatch.setattr(helpers, "_manifest_current", lambda *args: pytest.fail("legacy reader must not dereference first"))
    monkeypatch.setattr(cache, "user_helper_cache_root", lambda: tmp_path / "shared")
    monkeypatch.setattr(cache, "_native_fingerprint", lambda path: pytest.fail("outside artifact must remain unread"))
    assert cache.lookup_helper("go", source) is None
    assert outside.read_bytes() == b"do not inspect"
