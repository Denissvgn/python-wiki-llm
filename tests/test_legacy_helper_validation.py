"""Legacy pointers obey the same validation as immutable helper slots."""

from __future__ import annotations

import json

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.extractors.go_extractor import GoExtractor
from llm_wiki_cli.extractors.haskell_extractor import HaskellExtractor
from llm_wiki_cli.extractors.rust_extractor import RustExtractor
from llm_wiki_cli.services import analysis_capture
from llm_wiki_cli.services import extractor_helpers as helpers
from llm_wiki_cli.services import helper_cache

from tests.test_helper_cache import _native_header
from tests.test_helper_preparation import _prepare_fixture


def legacy_native(tmp_path, language, *, native=True, redirect=False):
    base = tmp_path / "helper-cache"
    cache_root = base / helpers.HELPER_CACHE_DIRNAME
    toolchain = "test compiler profile"
    key = helpers.helper_cache_key(language, toolchain_version=toolchain)
    root = cache_root / language / key
    root.mkdir(parents=True)
    artifact = (tmp_path / "outside-cache") if redirect else root / helpers._binary_name("extractor")
    # An executable with an incompatible target is rejected without executing
    # it. The accepted fixture only supplies the native header needed to inspect
    # the pointer; no synthetic executable is ever dispatched by these tests.
    artifact.write_bytes(_native_header() if native else b"foreign-target\n")
    artifact.chmod(0o755)
    helpers._write_manifest(cache_root, language, {
        "version": helpers.HELPER_MANIFEST_VERSION,
        "language": language, "platform": helpers.platform_id(),
        "source_fingerprint": helpers.helper_source_fingerprint(language),
        "artifact_fingerprint": helpers.helper_artifact_fingerprint(artifact),
        "key": key, "toolchain": toolchain,
        "root": str(root), "path": str(artifact),
    })
    return base, artifact


@pytest.mark.parametrize("language", ["go", "rust", "haskell"])
@pytest.mark.parametrize("invalid", ["foreign-target", "outside-cache"])
def test_unbound_getter_and_capture_reject_invalid_legacy_native(
    tmp_path, monkeypatch, language, invalid,
):
    base, _artifact = legacy_native(
        tmp_path, language, native=invalid != "foreign-target", redirect=invalid == "outside-cache",
    )
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: pytest.fail("inspection prepared a helper"))
    monkeypatch.setattr(helper_cache, "_profile", lambda *a, **k: pytest.fail("inspection probed a toolchain"))
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in tmp_path.rglob("*") if path.is_file()}
    assert helper_cache.lookup_helper(language, tmp_path, str(base)) is None
    assert helpers.get_prepared_binary(language, tmp_path, str(base)) is None
    captured = analysis_capture.capture_analysis(
        EXTRACTOR_REGISTRY, source_root=tmp_path, helper_cache_dir=str(base), languages={language},
    )
    assert "llm-wiki/extractor/" + language not in captured
    assert before == {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in tmp_path.rglob("*") if path.is_file()}


@pytest.mark.parametrize("language,suffix,extractor", [
    ("go", "go", GoExtractor), ("rust", "rs", RustExtractor), ("haskell", "hs", HaskellExtractor),
])
def test_strict_public_read_never_dispatches_a_rejected_legacy_helper(
    tmp_path, monkeypatch, language, suffix, extractor,
):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source"
    source.mkdir()
    (source / ("main." + suffix)).write_text("syntax-only source\n")
    base, _artifact = legacy_native(tmp_path, language, native=False)
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: pytest.fail("strict read prepared a helper"))
    monkeypatch.setattr(extractor, "_run_helper", lambda *a, **k: pytest.fail("rejected helper reached native dispatch"))
    with api.helper_preparation("never", cache_dir=str(base)):
        with pytest.raises(api.WorkspaceStateError, match="helper"):
            api.extract_source(str(source), deep=True, read_only=True)


@pytest.mark.parametrize("language", ["go", "rust", "haskell"])
def test_valid_legacy_native_remains_available_without_preparation(tmp_path, monkeypatch, language):
    base, artifact = legacy_native(tmp_path, language)
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: pytest.fail("inspection prepared a helper"))
    monkeypatch.setattr(helper_cache, "_profile", lambda *a, **k: pytest.fail("inspection probed a toolchain"))
    handle = helper_cache.lookup_helper(language, tmp_path, str(base))
    assert handle is not None and handle.path == artifact
    assert helpers.get_prepared_binary(language, tmp_path, str(base)) == artifact
    captured = analysis_capture.capture_analysis(
        EXTRACTOR_REGISTRY, source_root=tmp_path, helper_cache_dir=str(base), languages={language},
    )
    assert "llm-wiki/extractor/" + language in captured


def test_typescript_getter_and_capture_reject_redirected_legacy_pointer(tmp_path, monkeypatch):
    base = tmp_path / "helper-cache"
    cache_root = base / helpers.HELPER_CACHE_DIRNAME
    _prepare_fixture("typescript", cache_root)
    pointer = cache_root / "typescript" / helpers.HELPER_MANIFEST
    receipt = json.loads(pointer.read_text())
    root = tmp_path / "outside-cache"
    from shutil import copytree
    copytree(receipt["root"], root)
    receipt.update(root=str(root), path=str(root / "node_modules/ts-morph"))
    pointer.write_text(json.dumps(receipt))
    monkeypatch.setattr(helper_cache, "ensure_helper", lambda *a, **k: pytest.fail("inspection prepared a helper"))
    monkeypatch.setattr(helpers, "command_output", lambda *a, **k: pytest.fail("rejected helper probed Node"))
    assert helpers.get_prepared_typescript_root(tmp_path, str(base)) is None
    captured = analysis_capture.capture_analysis(
        EXTRACTOR_REGISTRY, source_root=tmp_path, helper_cache_dir=str(base), languages={"typescript"},
    )
    assert "llm-wiki/extractor/typescript" not in captured
