"""Independent dependency-tree, legacy receipt and preparation boundaries."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import stat
from types import SimpleNamespace

import pytest

from llm_wiki_cli.services import extractor_helpers as helpers
from llm_wiki_cli.services import typescript_helper_identity as identity


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    cache_base = tmp_path / "helper cache"
    cache_root = cache_base / helpers.HELPER_CACHE_DIRNAME
    builds = []
    monkeypatch.setattr(helpers.shutil, "which", lambda name: "/tools/" + name)
    monkeypatch.setattr(helpers, "command_output", lambda argv, **kw:
                        "v24.18.0" if argv[0].endswith("node") else "11.16.0")

    def npm(argv, **kwargs):
        assert argv[1:] == ["ci", "--ignore-scripts", "--no-audit", "--no-fund"]
        root = Path(kwargs["cwd"])
        builds.append(root)
        dependencies = root / "node_modules"
        if dependencies.exists():
            shutil.rmtree(dependencies)
        for name, content in {
            "ts-morph/index.js": "module.exports = require('@ts-morph/common');\n",
            "@ts-morph/common/index.js": "exports.fixture = 1;\n",
            "@ts-morph/common/node_modules/nested/index.js": "exports.nested = 1;\n",
        }.items():
            path = dependencies / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(helpers.subprocess, "run", npm)
    result = helpers.prepare_typescript(cache_root)
    assert result.status == "prepared"
    assert result.path is not None
    root = Path(result.path).parents[1]
    return cache_base, cache_root, root, builds


@pytest.mark.parametrize("change", ["sibling", "nested", "added", "removed"])
def test_dependency_changes_refuse_reuse_and_authorized_preparation_repairs(prepared, change):
    cache_base, cache_root, root, builds = prepared
    sibling = root / "node_modules/@ts-morph/common/index.js"
    before = json.loads((cache_root / "typescript/current.json").read_text())
    if change == "sibling":
        sibling.write_text("exports.fixture = 2;\n")
    elif change == "nested":
        (sibling.parent / "node_modules/nested/index.js").write_text("exports.nested = 2;\n")
    elif change == "added":
        (sibling.parent / "extra.js").write_text("exports.extra = true;\n")
    else:
        sibling.unlink()
    captured = {p: p.read_bytes() for p in cache_base.rglob("*") if p.is_file()}
    assert helpers.get_prepared_typescript_root(cache_dir=str(cache_base)) is None
    diagnostic = helpers.helper_identity("typescript", cache_dir=str(cache_base))
    assert diagnostic["status"] == "unavailable-or-mismatched"
    assert len(builds) == 1
    assert captured == {p: p.read_bytes() for p in cache_base.rglob("*") if p.is_file()}
    assert helpers.prepare_typescript(cache_root).status == "prepared"
    assert len(builds) == 2
    assert helpers.get_prepared_typescript_root(cache_dir=str(cache_base)) == root
    after = json.loads((cache_root / "typescript/current.json").read_text())
    assert before["artifact_fingerprint"] == after["artifact_fingerprint"]
    assert after["version"] == 3


def test_legacy_v2_receipt_is_inspectable_but_not_reused(prepared):
    cache_base, cache_root, root, builds = prepared
    path = cache_root / "typescript/current.json"
    old = json.loads(path.read_text())
    old["version"] = 2
    old.pop("artifact_scope", None)
    old["artifact_fingerprint"] = helpers.helper_artifact_fingerprint(root / "node_modules/ts-morph")
    path.write_text(json.dumps(old))
    original = path.read_bytes()
    assert helpers.get_prepared_typescript_root(cache_dir=str(cache_base)) is None
    result = helpers.helper_identity("typescript", cache_dir=str(cache_base))
    assert result["prepared"]["version"] == 2
    assert "typescript-dependency-identity-unavailable" in result["issues"]
    assert set(result) == {
        "language", "status", "issues", "cache_root", "current_source_fingerprint",
        "current_artifact_fingerprint", "execution_source_fingerprint", "prepared",
        "active_runtime", "recovery", "preparation_argv", "qualification",
    }
    assert path.read_bytes() == original and len(builds) == 1
    assert helpers.prepare_typescript(cache_root).status == "prepared"
    assert helpers.get_prepared_typescript_root(cache_dir=str(cache_base)) is not None


def test_complete_tree_identity_is_path_independent_and_deterministic(tmp_path):
    roots = [tmp_path / "one", tmp_path / "other cache's 树"]
    payloads = {"@scope/common/index.js": b"a\0b", "ts-morph/main.js": b"c\0d"}
    for root, entries in zip(roots, [list(payloads), list(reversed(payloads))]):
        for name in entries:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payloads[name])
    assert identity.dependency_fingerprint(roots[0]) == identity.dependency_fingerprint(roots[1])
    (roots[1] / "empty").mkdir()
    assert identity.dependency_fingerprint(roots[0]) != identity.dependency_fingerprint(roots[1])


@pytest.mark.parametrize("budget", ["entries", "bytes", "file-bytes", "depth"])
def test_limits_refuse_before_reading_dependency_bytes(tmp_path, monkeypatch, budget):
    root = tmp_path / "node_modules"
    file = root / "package/deeper/main.js"
    file.parent.mkdir(parents=True)
    file.write_bytes(b"1234")
    (file.parent / "other.js").write_bytes(b"5678")
    name, value = {"entries": ("MAX_ENTRIES", 3), "bytes": ("MAX_BYTES", 7),
                   "file-bytes": ("MAX_FILE_BYTES", 3), "depth": ("MAX_DEPTH", 2)}[budget]
    monkeypatch.setattr(identity, name, value)
    monkeypatch.setattr(identity, "read_guarded", lambda *a, **kw: pytest.fail("over-budget tree was read"))
    with pytest.raises(ValueError):
        identity.dependency_fingerprint(root)


@pytest.mark.parametrize("unsafe", ["symlink", "hardlink", "reparse", "special"])
def test_unsafe_dependency_entries_refuse_without_following(tmp_path, monkeypatch, unsafe):
    root = tmp_path / "node_modules"
    root.mkdir()
    original = tmp_path / "outside"
    original.write_bytes(b"not part of the prepared dependency tree")
    path = root / "bad.js"
    if unsafe == "symlink":
        path.symlink_to(original)
    elif unsafe == "hardlink":
        os.link(original, path)
    else:
        path.write_bytes(b"fixture")
        observe = identity.fresh_no_follow_stat

        def metadata(p):
            value = observe(p)
            if p == path:
                fields = {name: getattr(value, name) for name in (
                    "st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")}
                if unsafe == "reparse":
                    fields["st_file_attributes"] = 0x400
                else:
                    fields["st_mode"] = stat.S_IFIFO | 0o600
                return SimpleNamespace(**fields)
            return value
        monkeypatch.setattr(identity, "fresh_no_follow_stat", metadata)
    monkeypatch.setattr(identity, "read_guarded", lambda *a, **kw: pytest.fail("unsafe entry was read"))
    with pytest.raises(ValueError):
        identity.dependency_fingerprint(root)
    assert original.read_bytes() == b"not part of the prepared dependency tree"


def test_in_read_mutation_refuses_the_mixed_tree(tmp_path, monkeypatch):
    root = tmp_path / "node_modules"
    root.mkdir()
    path = root / "index.js"
    path.write_bytes(b"first")
    read = identity.read_guarded

    def mutate(*a, **kw):
        observed = read(*a, **kw)
        path.write_bytes(b"second")
        return observed

    monkeypatch.setattr(identity, "read_guarded", mutate)
    with pytest.raises(ValueError, match="changed"):
        identity.dependency_fingerprint(root)


def test_foreign_receipt_paths_are_not_scanned(prepared, tmp_path, monkeypatch):
    cache_base, cache_root, _, _ = prepared
    path = cache_root / "typescript/current.json"
    receipt = json.loads(path.read_text())
    receipt["root"] = str(tmp_path / "outside")
    receipt["path"] = str(tmp_path / "outside/node_modules/ts-morph")
    path.write_text(json.dumps(receipt))
    monkeypatch.setattr(identity, "dependency_fingerprint", lambda *a: pytest.fail("foreign tree read"))
    assert helpers.get_prepared_typescript_root(cache_dir=str(cache_base)) is None
    result = helpers.helper_identity("typescript", cache_dir=str(cache_base))
    assert result["status"] == "unavailable-or-mismatched"
    assert "typescript-root-unavailable" in result["issues"]


@pytest.mark.parametrize("mutation", ["oversized", "redirected", "duplicate", "nonfinite"])
def test_unsafe_receipts_stay_unavailable_without_preparation(prepared, tmp_path, monkeypatch, mutation):
    cache_base, cache_root, _, builds = prepared
    path = cache_root / "typescript/current.json"
    if mutation == "oversized":
        monkeypatch.setattr(identity, "MAX_RECEIPT_BYTES", path.stat().st_size - 1)
    elif mutation == "redirected":
        other = tmp_path / "foreign.json"
        other.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(other)
    elif mutation == "duplicate":
        path.write_bytes(b'{"version":2,"version":3}')
    else:
        path.write_bytes(b'{"version":NaN}')
    assert helpers.get_prepared_typescript_root(cache_dir=str(cache_base)) is None
    assert helpers.helper_identity("typescript", cache_dir=str(cache_base))["status"] == "unavailable-or-mismatched"
    assert len(builds) == 1


def test_preparation_does_not_follow_a_redirected_execution_source(prepared, tmp_path):
    _, cache_root, root, builds = prepared
    outside = tmp_path / "outside.js"
    outside.write_bytes(b"outside data")
    script = root / "extract.js"
    script.unlink()
    script.symlink_to(outside)
    before = (cache_root / "typescript/current.json").read_bytes()
    result = helpers.prepare_typescript(cache_root)
    assert result.status == "failed" and "unsafe link" in result.message
    assert len(builds) == 1 and outside.read_bytes() == b"outside data"
    assert (cache_root / "typescript/current.json").read_bytes() == before


def test_validated_dependency_identity_is_bound_to_ts_and_js_producers(prepared):
    from llm_wiki_cli.config import EXTRACTOR_REGISTRY
    from llm_wiki_cli.services import analysis_capture as capture

    cache_base, cache_root, root, _ = prepared
    first = capture.capture_analysis(EXTRACTOR_REGISTRY, helper_cache_dir=str(cache_base),
                                     languages={"typescript", "javascript"})
    name = "llm-wiki/extractor/typescript"
    assert first[name] == first["llm-wiki/extractor/javascript"]
    (root / "node_modules/@ts-morph/common/index.js").write_text("different dependency bytes")
    unavailable = capture.capture_analysis(EXTRACTOR_REGISTRY, helper_cache_dir=str(cache_base),
                                           languages={"typescript", "javascript"})
    assert name not in unavailable and "llm-wiki/extractor/javascript" not in unavailable
    # A fresh preparation identity is a distinct runtime basis, even with the
    # same toolchain, implementation and source selection.
    receipt = json.loads((cache_root / "typescript/current.json").read_text())
    receipt["artifact_fingerprint"] = identity.dependency_fingerprint(root / "node_modules")
    helpers._write_manifest(cache_root, "typescript", receipt)
    changed = capture.capture_analysis(EXTRACTOR_REGISTRY, helper_cache_dir=str(cache_base),
                                       languages={"typescript", "javascript"})
    assert first[name]["implementation"] == changed[name]["implementation"]
    assert first[name]["runtime"] != changed[name]["runtime"]


@pytest.mark.parametrize("mutation", ["missing", "scope", "fingerprint"])
def test_unqualified_helper_cannot_issue_ts_or_js_producer(prepared, monkeypatch, mutation):
    from llm_wiki_cli.config import EXTRACTOR_REGISTRY
    from llm_wiki_cli.services import analysis_capture as capture

    cache_base, cache_root, _, _ = prepared
    manifest = json.loads((cache_root / "typescript/current.json").read_text())
    if mutation == "missing":
        manifest.pop("artifact_fingerprint")
    elif mutation == "scope":
        manifest["artifact_scope"] = "legacy-path-only"
    else:
        manifest["artifact_fingerprint"] = "invalid"
    monkeypatch.setattr(helpers, "_manifest_current", lambda *a: manifest)
    result = capture.capture_analysis(EXTRACTOR_REGISTRY, helper_cache_dir=str(cache_base),
                                     languages={"typescript", "javascript"})
    assert "llm-wiki/extractor/typescript" not in result
    assert "llm-wiki/extractor/javascript" not in result
