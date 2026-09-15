"""Shared retained packet acceptance: parity, live authority and local limits."""

import builtins
from contextlib import contextmanager
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import urllib.request

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import context_packet as packets, plugins
from llm_wiki_cli.services.mcp_server import McpWikiService
from tests.test_context_integration import canonical, cli_context, tree_state
from tests.test_context_integration import packet_project as packet_project
from tests.test_context_packet_knowledge import _canonical_repack, _materialize_ready_project


FACETS = {
    "request", "source_snapshot", "repository", "availability", "knowledge",
    "generator", "freshness", "context_response", "delivery", "path_policy",
}


def test_acceptance_manifest_declares_three_replayable_synthetic_corpora():
    from tests.qualified_context_acceptance import load_manifest

    manifest = load_manifest()
    assert len(manifest["corpora"]) == 3
    assert sum(len(group["cases"]) for group in manifest["corpora"]) == 24


@pytest.fixture
def managed_packet_project(tmp_path, monkeypatch):
    tree, _ = _materialize_ready_project(tmp_path, monkeypatch)
    return tree


def _managed_packet():
    return api.build_qualified_context(request={
        "protocol": "llm-wiki-context/v2", "budget_tokens": 32000,
        "focus": ["all"], "format": "json", "filters": {}, "knowledge_mode": "auto",
    })


@pytest.mark.parametrize("mode", [None, "off", "auto", "required"])
@pytest.mark.parametrize("prefer_fresh", [False, True])
@pytest.mark.parametrize("format,budget,filters", [
    ("json", 32000, {}), ("json", 80, {}),
    ("json", 32000, {"symbol": "User"}),
    ("json", 32000, {"surface": "entities"}),
    ("markdown", 32000, {}),
    ("json", 32000, {"language": "python", "module": "src/accounts.py"}),
])
def test_managed_cross_surface_acceptance(managed_packet_project, mode, prefer_fresh, format, budget, filters):
    root = managed_packet_project["root"]
    request = {
        "protocol": "llm-wiki-context/v1" if mode is None else "llm-wiki-context/v2",
        "budget_tokens": budget, "format": format, "focus": ["all"], "filters": filters,
        "prefer_fresh": prefer_fresh,
    }
    if mode is not None:
        request["knowledge_mode"] = mode
    request_path = root / "context-request.json"
    request_path.write_bytes(canonical(request))
    before = tree_state(root)
    packet = api.build_qualified_context(request=request)
    result = cli_context(root, "--request", str(request_path), "--format", "packet")
    assert result.returncode == 0, result.stderr.decode()
    mcp = McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki").get_context_packet(
        budget_tokens=budget, focus=["all"], format=format, filters=filters,
        knowledge_mode=mode, prefer_fresh=prefer_fresh,
    )
    assert packet.to_bytes() == result.stdout == canonical(mcp["packet"])
    assert api.validate_context_packet(result.stdout).valid
    legacy = api.build_context(budget=budget, format=format, focus="all", filters=filters, knowledge_mode=mode, prefer_fresh=prefer_fresh)
    payload = legacy["payload"] if format == "markdown" else legacy
    response = packet.to_payload()["response"]
    assert response["used_tokens"] == payload["used"]
    for name in ("truncated", "omitted_files", "downgraded_files", "bounds"):
        assert response[name] == payload[name]
    if format == "json":
        assert response["files"] == payload["files"]
    else:
        assert response["content"] == legacy["content"]
    assert tree_state(root) == before


@pytest.mark.parametrize("facet", [
    "source_snapshot", "repository", "knowledge", "generator", "freshness",
    "context_response", "delivery", "path_policy",
])
def test_self_consistent_substitutions_reconcile_against_each_live_facet(managed_packet_project, facet):
    original = _managed_packet()
    current = api.reconcile_context_packet(original.to_bytes())
    assert current.current is True
    assert set(current.facets) == FACETS
    payload = original.to_payload()
    if facet == "source_snapshot":
        payload["basis"][facet]["identity"] = "sha256:" + "0" * 64
    elif facet == "repository":
        payload["basis"][facet]["identity"] = "example.invalid/different/project"
    elif facet == "knowledge":
        payload["basis"][facet]["knowledge_index_hash"] = "sha256:" + "0" * 64
    elif facet == "generator":
        payload["basis"][facet]["version"] = "fixture-other-generator"
    elif facet == "freshness":
        payload["basis"][facet]["evaluation_digest"] = "sha256:" + "0" * 64
    elif facet == "context_response":
        payload["response"]["used_tokens"] += 1
    else:
        warnings = [*payload["response"].get("warnings", []), "Synthetic additional warning."]
        payload["response"]["warnings"] = warnings
        payload["delivery"]["warnings"] = warnings
    changed = _canonical_repack(payload)
    assert api.validate_context_packet(changed).valid
    before = tree_state(managed_packet_project["root"])
    reconciled = api.reconcile_context_packet(changed)
    assert reconciled.state == "stale" and reconciled.current is False
    assert reconciled.facets[facet]["current"] is False
    assert tree_state(managed_packet_project["root"]) == before


def test_availability_loss_is_stale_not_an_unchanged_success(managed_packet_project):
    packet = _managed_packet()
    wiki = managed_packet_project["wiki_root"]
    for name in (".llm-wiki-manifest.json", ".llm-wiki-surface.json", ".llm-wiki-knowledge.json"):
        (wiki / name).unlink()
    before = tree_state(managed_packet_project["root"])
    result = api.reconcile_context_packet(packet.to_bytes())
    assert result.current is False and result.state == "stale"
    assert result.facets["availability"]["current"] is False
    assert result.facets["knowledge"]["current"] is None
    assert tree_state(managed_packet_project["root"]) == before


@pytest.mark.parametrize("name", [
    ".llm-wiki-manifest.json", ".llm-wiki-surface.json", ".llm-wiki-knowledge.json",
    ".llm-wiki-governance.json", ".llm-wiki-verification.json", "index.md",
    "modules/accounts.md",
])
def test_each_wiki_anchor_mutation_aborts_packet_return(managed_packet_project, monkeypatch, name):
    original = packets.build_context_from_captured_read
    def mutate_after_read(captured, request, *args, **kwargs):
        result = original(captured, request, *args, **kwargs)
        target = captured.wiki_root / name
        target.write_bytes((target.read_bytes() if target.exists() else b"{}") + b"\n")
        return result
    monkeypatch.setattr(packets, "build_context_from_captured_read", mutate_after_read)
    with pytest.raises(api.WorkspaceStateError) as raised:
        _managed_packet()
    assert raised.value.code == "context-read-mutated"
    assert raised.value.details == {"field": "wiki_dir"}


def test_consumer_request_intent_is_separate_from_live_currentness(managed_packet_project):
    packet = _managed_packet()
    expected_request = {**packet.to_payload()["request"], "focus": ["changed", "neighbors"]}
    comparison = api.compare_context_packet_basis(packet.to_bytes(), packet.to_payload()["basis"])
    assert comparison.matches_expected and comparison.current is None
    result = api.reconcile_context_packet(packet.to_bytes())
    assert result.current is True and result.facets["request"]["current"] is True
    assert packet.to_payload()["request"] != expected_request


def test_snapshot_equality_never_becomes_currentness(packet_project):
    packet = api.build_qualified_context()
    validation = api.validate_context_packet(packet.to_bytes())
    assert validation.valid and validation.freshness == "unevaluated"
    comparison = api.compare_context_packet_basis(packet.to_bytes(), packet.to_payload()["basis"])
    assert comparison.matches_expected and comparison.current is None
    reconciliation = api.reconcile_context_packet(packet.to_bytes())
    assert reconciliation.current is None and reconciliation.state == "unevaluated"


def test_offline_consumers_have_no_file_or_network_io(packet_project, monkeypatch):
    packet = api.build_qualified_context()
    basis = packet.to_payload()["basis"]
    def forbidden(*args, **kwargs):
        raise AssertionError("offline packet operation performed I/O")
    with monkeypatch.context() as guard:
        for owner, name in ((builtins, "open"), (io, "open"), (os, "open"),
                            (socket, "socket"), (socket, "create_connection"),
                            (urllib.request, "urlopen"), (packets, "capture_context_read")):
            guard.setattr(owner, name, forbidden)
        assert api.validate_context_packet(packet.to_bytes()).valid
        assert api.compare_context_packet_basis(packet.to_bytes(), basis).current is None
        with pytest.raises(api.InvalidRequestError):
            api.validate_context_packet(b"invalid")


@contextmanager
def _read_only_guard(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("packet reconciliation attempted a write/provider/plugin call")
    with monkeypatch.context() as guard:
        for owner, name in ((socket, "socket"), (socket, "create_connection"),
                            (urllib.request, "urlopen"), (plugins, "load_entry_point")):
            guard.setattr(owner, name, forbidden)
        for name in ("write_text", "write_bytes", "mkdir", "unlink", "rename", "replace", "rmdir"):
            guard.setattr(Path, name, forbidden)
        def wrap_open(original):
            def checked(file, mode="r", *args, **kwargs):
                writing = any(flag in mode for flag in "wax+")
                pipe = isinstance(file, int) and not stat.S_ISREG(os.fstat(file).st_mode)
                if writing and not pipe:
                    forbidden()
                return original(file, mode, *args, **kwargs)
            return checked
        guard.setattr(builtins, "open", wrap_open(builtins.open))
        guard.setattr(io, "open", wrap_open(io.open))
        original_os_open = os.open
        def checked_os_open(path, flags, *args, **kwargs):
            if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                forbidden()
            return original_os_open(path, flags, *args, **kwargs)
        guard.setattr(os, "open", checked_os_open)
        yield


def test_official_reconciliation_is_read_only_and_provider_free(managed_packet_project, monkeypatch):
    packet = _managed_packet()
    root = managed_packet_project["root"]
    before = tree_state(root)
    with _read_only_guard(monkeypatch):
        result = api.reconcile_context_packet(packet.to_bytes())
    assert result.current is True
    assert tree_state(root) == before


def test_owner_can_replace_consistent_local_history_but_not_external_expectation(packet_project):
    original = api.build_qualified_context(request={"budget_tokens": 32000, "focus": ["all"]})
    (packet_project / "app.py").write_text("def replacement():\n    return 99\n")
    replacement = api.build_qualified_context(request={"budget_tokens": 32000, "focus": ["all"]})
    assert api.validate_context_packet(original.to_bytes()).valid
    assert api.validate_context_packet(replacement.to_bytes()).valid
    assert original.packet_id != replacement.packet_id
    result = api.compare_context_packet_basis(replacement.to_bytes(), original.to_payload()["basis"])
    assert not result.matches_expected and result.current is None
    assert api.reconcile_context_packet(original.to_bytes()).state == "stale"


def test_consistent_whole_root_recreation_does_not_claim_owner_resistance(packet_project, tmp_path, monkeypatch):
    original = api.build_qualified_context(request={"budget_tokens": 32000, "focus": ["all"]})
    snapshot = {name: content for name, (content, _mtime) in tree_state(packet_project).items()}
    monkeypatch.chdir(tmp_path)
    shutil.rmtree(packet_project)
    packet_project.mkdir()
    for name, content in snapshot.items():
        path = packet_project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    monkeypatch.chdir(packet_project)
    rebuilt = api.build_qualified_context(request={"budget_tokens": 32000, "focus": ["all"]})
    assert rebuilt.to_bytes() == original.to_bytes()
    assert rebuilt.to_payload()["assurance"]["level"] == "content-integrity"
    assert api.reconcile_context_packet(rebuilt.to_bytes()).current is None


def test_local_signing_does_not_admit_stronger_packet_assurance(packet_project):
    packet = api.build_qualified_context()
    key = b"synthetic-fixture-key-not-a-credential"
    signature = hmac.new(key, packet.to_bytes(), hashlib.sha256).digest()
    assert hmac.compare_digest(signature, hmac.new(key, packet.to_bytes(), hashlib.sha256).digest())
    for assurance in ("owner-resistant", "authenticated", "externally-witnessed"):
        payload = packet.to_payload()
        payload["assurance"]["level"] = assurance
        with pytest.raises(api.InvalidRequestError):
            api.validate_context_packet(_canonical_repack(payload))


def test_v3_outer_accounting_is_not_bound_by_nested_packet_id(packet_project):
    result = api.build_budgeted_context(request={
        "budget_tokens": 32000, "budget_mode": "estimated", "format": "packet",
        "focus": ["all"], "knowledge_mode": "off",
    })
    assert result.ok
    outer = json.loads(result.rendered)
    inner = canonical(outer["packet"])
    identity = api.validate_context_packet(inner).packet_id
    outer["accounting"]["used_tokens"] += 1
    assert api.validate_context_packet(canonical(outer["packet"])).packet_id == identity
    with pytest.raises(api.InvalidRequestError):
        api.validate_context_packet(canonical(outer))


def test_explicit_source_selection_has_real_adapter_parity(packet_project):
    policy = packet_project / "profiles" / "public.json"
    policy.parent.mkdir()
    policy.write_bytes(canonical({
        "schema_version": "llm-wiki-source-selection/v1",
        "include": ["app.py"], "exclude": [],
    }))
    request = {"protocol": "llm-wiki-context/v2", "budget_tokens": 32000,
               "focus": ["all"], "knowledge_mode": "auto"}
    request_path = packet_project / "request.json"
    request_path.write_bytes(canonical(request))
    before = tree_state(packet_project)
    packet = api.build_qualified_context(request=request, source_selection="profiles/public.json")
    result = cli_context(packet_project, "--request", str(request_path), "--format", "packet",
                         "--source-selection", "profiles/public.json")
    assert result.returncode == 0, result.stderr.decode()
    mcp = McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki", source_selection="profiles/public.json").get_context_packet(focus=["all"], knowledge_mode="auto")
    assert packet.to_bytes() == result.stdout == canonical(mcp["packet"])
    assert set(packet.to_payload()["response"]["files"]) == {"app.py"}
    assert tree_state(packet_project) == before


def test_legacy_plugin_execution_stays_separate_from_packet_construction(packet_project):
    from tests.test_context_packet import _install_entrypoint_detector_plugin

    marker = packet_project / "plugin-executed.txt"
    _install_entrypoint_detector_plugin(packet_project, marker=marker)
    assert not marker.exists()
    api.build_qualified_context(request={
        "budget_tokens": 32000, "focus": ["all"], "filters": {"entrypoint": "api-greet"},
    })
    assert not marker.exists()
    api.build_context(budget=32000, focus="all", filters={"entrypoint": "api-greet"})
    assert marker.read_text() == "executed"
