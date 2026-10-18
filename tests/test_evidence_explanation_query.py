"""Explanation transport preserves evidence authority and independent identities."""

from copy import deepcopy
from dataclasses import replace
import json
from typing import Any, cast

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.commands import query_cmd
from llm_wiki_cli.services import evidence_explanation, extractor_helpers as helpers
from llm_wiki_cli.services.documentation_queries import DocumentationGraphQueryService
from llm_wiki_cli.services.normalization_diagnostics import DIAGNOSTIC_PREFIX
from tests.test_captured_evidence_diagnostics import _view
from tests.test_knowledge_evidence import _inventory, _module_basis
from tests.test_knowledge_freshness import MODULE_LOCATOR


@pytest.fixture
def services(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    view, _ = _view(tmp_path)
    snapshot_view, _ = _view(tmp_path, "untested")
    live = DocumentationGraphQueryService({}, knowledge_view=view, limit=2)
    snapshot = DocumentationGraphQueryService({}, knowledge_view=snapshot_view, limit=2)
    calls = []
    def build(*args, **kwargs):
        calls.append(kwargs)
        return live
    monkeypatch.setattr(api, "_snapshot_query_service", lambda *a, **kw: snapshot)
    monkeypatch.setattr(api, "build_documentation_query_service", build)
    monkeypatch.setattr(evidence_explanation.knowledge_reuse, "implementation_hash", lambda: "sha256:" + "a" * 64)
    return snapshot, live, calls


@pytest.mark.parametrize("value", [MODULE_LOCATOR, "modules/accounts.md"])
def test_exact_snapshot_reuses_explanation_without_live_work(services, value):
    snapshot, _, calls = services
    before = deepcopy(snapshot.explain_evidence(value))
    result = cast(dict[str, Any], api.query_documentation({"operation": "explain", "value": value}))
    assert result["found"] and not result["ambiguous"]
    for key, expected in before.items():
        assert result[key] == expected
    assert result["cost"] == {"scope": "snapshot-index-only", "full_inventory_performed": False, "supplied_paths": 0}
    assert calls == []
    assert result["provenance"]["stored_producer"] is not None
    assert result["provenance"]["live_producer"] is None
    assert result["provenance"]["captured_source_basis"]["source_path"] == "src/accounts.py"
    assert result["provenance"]["captured_source_basis"]["unknown_reason"] == "invalid-inventory-shape"
    assert result["provenance"]["inventory_contract"] == "structural-observations/v1"
    assert result["provenance"]["package"]["distribution_archive_digest"] is None
    assert result["evidence"]["freshness"]["live_basis"] is None


def test_source_returns_explicit_bounded_choices(services):
    snapshot, _, _ = services
    result = cast(dict[str, Any], api.query_documentation({"operation": "explain", "source": "src/accounts.py", "limit": 2}))
    assert not result["found"] and result["ambiguous"]
    assert result["evidence"] is None
    assert result["bounds"]["matches"] == {"total": 3, "returned": 2, "truncated": True}
    assert all(row["source_path"] == "src/accounts.py" for row in result["matches"])
    chosen = result["matches"][0]["locator"]
    selected = cast(dict[str, Any], api.query_documentation({"operation": "explain", "value": chosen}))
    assert selected["found"] and selected["concept"]["locator"] == chosen
    # A source with one concept can use the same exact resolution.
    snapshot.concepts_by_source_path["one.py"] = snapshot.concepts_by_source_path["src/accounts.py"][:1]
    assert api.query_documentation({"operation": "explain", "source": "one.py"})["found"]
    absent = cast(dict[str, Any], api.query_documentation({"operation": "explain", "source": "absent.py"}))
    assert not absent["found"] and not absent["ambiguous"] and absent["total"] == 0


@pytest.mark.parametrize("fields", [
    {}, {"value": MODULE_LOCATOR, "source": "a.py"},
    {"value": MODULE_LOCATOR, "live": True},
    {"value": MODULE_LOCATOR, "live": "yes"},
    {"value": MODULE_LOCATOR, "allow_full_inventory": 1},
    {"value": MODULE_LOCATOR, "allow_full_inventory": True},
    {"source": "../secret"}, {"source": "src\\accounts.py"},
])
def test_invalid_requests_fail_before_workspace_reads(monkeypatch, fields):
    monkeypatch.setattr(api, "validate_source_root", lambda *a, **k: pytest.fail("unexpected read"))
    with pytest.raises(api.InvalidRequestError):
        api.query_documentation({"operation": "explain", **fields})


def test_live_retains_fresh_diagnostic_and_cache_binding(services):
    _, service, calls = services
    view = service.knowledge_view
    bad = _inventory("python")
    bad["imports"] = [{"module": ""}]
    diagnostic = _module_basis(bad).normalization_diagnostic
    assert diagnostic is not None and view is not None and view.freshness is not None
    old = view.freshness.by_locator[MODULE_LOCATOR]
    assert old.live_basis is not None
    new = replace(old, live_basis=replace(old.live_basis, concept_observation_hash=None,
                    unknown_reason="invalid-inventory-shape", normalization_diagnostic=diagnostic))
    service.knowledge_view = replace(view, freshness=replace(view.freshness,
                    by_locator={**view.freshness.by_locator, MODULE_LOCATOR: new}))
    # The service caches freshness at construction; rebuild from the updated view.
    service = DocumentationGraphQueryService({}, knowledge_view=service.knowledge_view)
    def build(*a, **kw):
        calls.append(kw)
        return service
    from unittest.mock import patch
    with patch.object(api, "build_documentation_query_service", build):
        result = cast(dict[str, Any], api.query_documentation({"operation": "explain", "value": MODULE_LOCATOR,
                  "live": True, "allow_full_inventory": True}, helper_cache_dir="chosen-cache"))
    assert result["cost"]["full_inventory_performed"]
    assert calls[-1]["helper_cache_dir"] == "chosen-cache" and calls[-1]["read_only"] is True
    assert result["provenance"]["live_producer"] is not None
    detail = result["evidence"]["freshness"]["description"]
    assert DIAGNOSTIC_PREFIX in detail and '"pointer":"/imports/0/module"' in detail
    assert result["evidence"]["freshness"]["state"] == "unknown"


def test_cli_and_mcp_share_dispatch_without_altering_legacy_explanation(services, monkeypatch, capsys):
    snapshot, live, _ = services
    from llm_wiki_cli.services import mcp_server
    monkeypatch.setattr(mcp_server, "build_documentation_query_service", lambda *a, **kw: live)
    mcp = mcp_server.McpWikiService(src_dir=".", wiki_dir=".")
    old = api.explain_evidence(MODULE_LOCATOR, service=live)
    assert mcp.explain_evidence(MODULE_LOCATOR) == old
    assert "provenance" not in old and "cost" not in old
    request = {"operation": "explain", "value": MODULE_LOCATOR}
    monkeypatch.setattr(query_cmd, "load_request", lambda _: request)
    args = cli._build_parser().parse_args(["query", "--request", "-", "--helper-cache-dir", "cache"])
    query_cmd.run(args)
    result = json.loads(capsys.readouterr().out)
    assert result["evidence"] == snapshot.explain_evidence(MODULE_LOCATOR)["evidence"]
    assert mcp.query_documentation(request)["evidence"] == result["evidence"]


def _prepared(tmp_path, language):
    cache = tmp_path / "helper cache"
    root = cache / helpers.HELPER_CACHE_DIRNAME
    artifact = tmp_path / ("artifact" if language != "typescript" else "ts/node_modules/ts-morph")
    if language == "typescript":
        artifact.mkdir(parents=True)
        (artifact / "package.json").write_text("{}")
        for name, path in helpers.helper_source_files("typescript"):
            (artifact.parents[1] / name).write_bytes(path.read_bytes())
    else:
        artifact.write_bytes(b"native binary")
    receipt = {"version": helpers.HELPER_MANIFEST_VERSION, "language": language,
        "platform": helpers.platform_id(), "source_fingerprint": helpers.helper_source_fingerprint(language),
        "artifact_fingerprint": helpers.helper_artifact_fingerprint(artifact),
        "path": str(artifact), "root": str(artifact.parents[1]),
        "toolchain": "node v24.18.0; npm 11.16.0" if language == "typescript" else "test compiler"}
    helpers._write_manifest(root, language, receipt)
    return cache, root, artifact, receipt


@pytest.mark.parametrize("language", helpers.SUPPORTED_HELPERS)
def test_receipt_identity_uses_actual_bytes_and_does_not_prepare(tmp_path, monkeypatch, language):
    cache, root, artifact, receipt = _prepared(tmp_path, language)
    probes = []
    def probe(*a, **kw):
        probes.append(a)
        return "v24.18.0"
    monkeypatch.setattr(helpers, "command_output", probe)
    monkeypatch.setattr(helpers.shutil, "which", lambda *a, **kw: "/active/node")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = helpers.helper_identity(language, tmp_path, str(cache))
    assert result["status"] == "ready" and result["issues"] == []
    assert result["prepared"]["artifact_fingerprint"] == result["current_artifact_fingerprint"]
    assert result["prepared"]["source_fingerprint"] == result["current_source_fingerprint"]
    assert result["cache_root"] == str(root)
    if language == "typescript":
        assert len(probes) == 1
        assert result["prepared"]["toolchain"] == receipt["toolchain"]
        assert result["active_runtime"] == {"kind": "node", "path": "/active/node", "version": "v24.18.0"}
        assert result["execution_source_fingerprint"] == result["current_source_fingerprint"]
    else:
        assert not probes  # No compiler is needed to inspect a native binary.
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


@pytest.mark.parametrize(("mutation", "issue"), [
    ("source_fingerprint", "source-fingerprint-mismatch"), ("platform", "platform-mismatch"),
    ("artifact", "artifact-unavailable-or-mismatch"), ("runtime", "active-runtime-mismatch"),
    ("execution-source", "execution-source-mismatch"),
    ("missing", "receipt-unavailable"),
])
def test_mismatch_and_missing_are_explicit_with_same_cache_recovery(tmp_path, monkeypatch, mutation, issue):
    cache, root, artifact, receipt = _prepared(tmp_path, "typescript")
    if mutation in {"source_fingerprint", "platform"}:
        receipt[mutation] = "different"
        helpers._write_manifest(root, "typescript", receipt)
    elif mutation == "artifact":
        (artifact / "package.json").write_text("changed")
    elif mutation == "execution-source":
        (artifact.parents[1] / "extract.js").write_text("// changed execution copy")
    elif mutation == "missing":
        (root / "typescript/current.json").unlink()
    monkeypatch.setattr(helpers, "command_output", lambda *a, **kw: "v26.0.0" if mutation == "runtime" else "v24.18.0")
    monkeypatch.setattr(helpers.shutil, "which", lambda *a, **kw: "/active/node")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = helpers.helper_identity("typescript", tmp_path, str(cache))
    assert result["status"] == "unavailable-or-mismatched" and issue in result["issues"]
    assert result["preparation_argv"] == helpers.helper_preparation_argv("typescript", tmp_path, str(cache))
    assert str(cache) in result["recovery"] and "same source selection" in result["recovery"]
    if mutation == "runtime":
        assert "prepared helper is current" in result["recovery"]
        assert "does not change active PATH" in result["recovery"]
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


def test_unknown_captured_typescript_basis_still_selects_its_helper(services, monkeypatch):
    snapshot, _, _ = services
    view = snapshot.knowledge_view
    assert view is not None and view.manifest_basis is not None
    concept = snapshot.concept_by_locator[MODULE_LOCATOR]
    path = concept["document"]["canonical_path"]
    baseline = view.manifest_basis.evidence_baselines[path]
    assert baseline.basis is not None
    snapshot.knowledge_view = replace(view, manifest_basis=replace(view.manifest_basis,
        evidence_baselines={**view.manifest_basis.evidence_baselines,
            path: replace(baseline, basis=replace(baseline.basis, extractor_ref="llm-wiki/extractor/javascript"))}))
    seen = []
    def inspect(language, source_root, cache):
        seen.append((language, cache))
        return {"status": "unavailable-or-mismatched", "issues": ["receipt-unavailable"]}
    monkeypatch.setattr(helpers, "helper_identity", inspect)
    result = cast(dict[str, Any], api.query_documentation({"operation": "explain", "value": MODULE_LOCATOR}, helper_cache_dir="same-cache"))
    assert result["evidence"]["structure"].get("basis") is None
    assert seen == [("typescript", "same-cache")]
    assert result["provenance"]["helper"]["issues"] == ["receipt-unavailable"]


def test_combined_provenance_and_evidence_keep_shared_byte_ceiling(services, monkeypatch):
    monkeypatch.setattr(evidence_explanation, "explanation_provenance",
        lambda *a, **kw: {"untrusted_receipt": "x" * (1024 * 1024)})
    result = cast(dict[str, Any], api.query_documentation({"operation": "explain", "value": MODULE_LOCATOR}))
    rendered = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    assert result["truncated"] and len(rendered) <= 65536
    assert result["bounds"]["result_bytes"]["returned"] == len(rendered)
    assert result["bounds"]["result_bytes"]["truncated"]
    assert result["cost"]["full_inventory_performed"] is False
