"""Real packet adapter parity, error identity and safe diagnostic boundaries."""

import json
import subprocess
import sys
from typing import Any

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import context_packet as packets, context_service
from llm_wiki_cli.services.mcp_server import McpWikiError, McpWikiService


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


@pytest.fixture
def packet_project(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    (root / "app.py").write_text('def greet(name: str):\n    return "hello " + name\n')
    (root / "other.py").write_text('def unrelated():\n    return 2\n')
    wiki = root / "docs/llm_wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_text("# Project\n")
    monkeypatch.chdir(root)
    return root


def cli_context(root, *args):
    return subprocess.run(
        [sys.executable, "-m", "llm_wiki_cli.cli", "context", *args],
        cwd=root, capture_output=True, timeout=30,
    )


def tree_state(root):
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*") if path.is_file()
    }


@pytest.mark.parametrize("mode", [None, "off", "auto"])
@pytest.mark.parametrize("format", ["json", "markdown"])
def test_request_packet_real_api_cli_mcp_parity(packet_project, mode, format):
    request = {
        "protocol": "llm-wiki-context/v1" if mode is None else "llm-wiki-context/v2",
        "budget_tokens": 32000, "focus": ["all"], "format": format,
        "filters": {"module": "app"}, "prefer_fresh": False,
    }
    if mode is not None:
        request["knowledge_mode"] = mode
    request_path = packet_project / "request.json"
    request_path.write_bytes(canonical(request))
    before = tree_state(packet_project)
    packet = api.build_qualified_context(request=request)
    result = cli_context(packet_project, "--request", str(request_path), "--format", "packet")
    assert result.returncode == 0, result.stderr.decode()
    service = McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")
    response = service.get_context_packet(
        budget_tokens=32000, focus=["all"], format=format,
        filters=request["filters"], knowledge_mode=mode,
    )
    assert packet.to_bytes() == result.stdout == canonical(response["packet"])
    assert api.validate_context_packet(result.stdout).valid
    assert packet.to_payload()["request"]["filters"] == request["filters"]
    if format == "json":
        assert set(packet.to_payload()["response"]["files"]) == {"app.py"}
    assert tree_state(packet_project) == before


@pytest.mark.parametrize("options,field", [
    (["--budget", "4000"], "budget_tokens"),
    (["--focus", "all"], "focus"),
    (["--prefer-fresh"], "prefer_fresh"),
    (["--knowledge-mode", "off"], "knowledge_mode"),
])
def test_request_conflicts_fail_before_capture(packet_project, monkeypatch, capsys, options, field):
    request = packet_project / "request.json"
    request.write_bytes(canonical({"protocol": "llm-wiki-context/v1", "budget_tokens": 32000}))
    def forbidden(*args, **kwargs):
        raise AssertionError("conflicting requests must not read source/wiki")
    monkeypatch.setattr(packets, "capture_context_read", forbidden)
    monkeypatch.setattr(context_service, "_build_context", forbidden)
    args = cli._build_parser().parse_args(["context", "--request", str(request), "--format", "packet", *options])
    with pytest.raises(SystemExit) as error:
        context_service.run(args)
    assert error.value.code == 1
    output = capsys.readouterr()
    assert not output.out
    assert json.loads(output.err)["error"]["field"] == field


def test_v3_request_does_not_silently_change_delivery(packet_project, monkeypatch, capsys):
    request = packet_project / "request.json"
    request.write_bytes(canonical({"protocol": "llm-wiki-context/v3", "budget_tokens": 32000, "budget_mode": "estimated", "format": "json"}))
    monkeypatch.setattr(packets, "capture_context_read", lambda *a, **k: pytest.fail("unexpected capture"))
    args = cli._build_parser().parse_args(["context", "--request", str(request), "--format", "packet"])
    with pytest.raises(SystemExit):
        context_service.run(args)
    output = capsys.readouterr()
    assert not output.out
    assert json.loads(output.err)["error"]["field"] == "format"


@pytest.mark.parametrize("operation", ["validate", "compare", "reconcile"])
@pytest.mark.parametrize("raw,code,field", [
    (b"not-json", "malformed-context-packet", "packet"),
    (canonical({"schema_version": "/Users/synthetic-private/secret"}), "unsupported-context-packet", "schema_version"),
])
def test_public_packet_consumption_errors_retain_safe_structure(packet_project, operation, raw, code, field):
    calls = {
        "validate": lambda: api.validate_context_packet(raw),
        "compare": lambda: api.compare_context_packet_basis(raw, {}),
        "reconcile": lambda: api.reconcile_context_packet(raw),
    }
    with pytest.raises(api.InvalidRequestError) as raised:
        calls[operation]()
    assert raised.value.code == code
    assert raised.value.details == {"field": field}
    assert raised.value.__cause__ is not None
    assert "/Users/synthetic-private" not in str(raised.value)
    assert "/Users/synthetic-private" not in json.dumps(raised.value.details)


@pytest.mark.parametrize("kind", ["missing", "file"])
def test_missing_source_is_unavailable_across_adapters(packet_project, kind):
    path = packet_project / kind
    if kind == "file":
        path.write_text("not a directory")
    with pytest.raises(api.WorkspaceStateError) as raised:
        api.build_qualified_context(src_dir=str(path), request={"budget_tokens": 32000})
    assert raised.value.code == "context-packet-unavailable"
    assert raised.value.details == {"field": "src_dir"}
    with pytest.raises(McpWikiError) as mcp:
        McpWikiService(src_dir=str(path), wiki_dir="docs/llm_wiki").get_context_packet()
    assert mcp.value.code == raised.value.code
    result = cli_context(packet_project, "--budget", "32000", "--format", "packet", "--src-dir", str(path))
    assert result.returncode == 1 and not result.stdout
    assert json.loads(result.stderr)["error"]["code"] == raised.value.code
    assert str(packet_project).encode() not in result.stderr


def test_existing_empty_source_remains_a_valid_packet(packet_project):
    empty = packet_project / "empty"
    empty.mkdir()
    packet = api.build_qualified_context(src_dir=str(empty), request={"budget_tokens": 32000})
    assert packet.to_payload()["response"]["files"] == {}
    assert api.validate_context_packet(packet.to_bytes()).valid


@pytest.mark.parametrize("option", ["read_only", "allow_external_src"])
@pytest.mark.parametrize("operation", ["build", "reconcile"])
def test_packet_option_types_fail_before_source_reads(packet_project, monkeypatch, option, operation):
    packet = api.build_qualified_context().to_bytes()
    monkeypatch.setattr(context_service, "validate_source_root", lambda *a, **k: pytest.fail("unexpected source read"))
    invalid_options: dict[str, Any] = {option: "yes"}
    with pytest.raises(api.InvalidRequestError) as raised:
        if operation == "build":
            api.build_qualified_context(**invalid_options)
        else:
            api.reconcile_context_packet(packet, **invalid_options)
    assert raised.value.code == "invalid-request"
    assert raised.value.details == {"field": option}


def test_mutation_is_distinct_and_never_returns_cached_success(packet_project, monkeypatch, capsys):
    service = McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")
    old = service.get_context_packet()
    def mutated(*args, **kwargs):
        raise packets.ContextPacketSourceMutationError("source")
    monkeypatch.setattr(packets, "_assert_source_unchanged", mutated)
    with pytest.raises(api.WorkspaceStateError) as raised:
        api.build_qualified_context()
    assert raised.value.code == "context-read-mutated"
    with pytest.raises(McpWikiError) as mcp:
        service.get_context_packet(if_packet_id=old["packet_id"])
    assert mcp.value.code == raised.value.code
    args = cli._build_parser().parse_args(["context", "--budget", "32000", "--format", "packet"])
    with pytest.raises(SystemExit):
        context_service.run(args)
    output = capsys.readouterr()
    assert not output.out
    assert json.loads(output.err)["error"]["code"] == raised.value.code


def test_path_failure_diagnostics_do_not_expose_resolved_roots(packet_project):
    with pytest.raises(api.PathPolicyError) as raised:
        api.build_qualified_context(wiki_dir="../outside-wiki")
    assert raised.value.code == "path-policy-error"
    with pytest.raises(McpWikiError) as mcp:
        McpWikiService(src_dir=".", wiki_dir="../outside-wiki").get_context_packet()
    assert mcp.value.code == "path-policy-error"
    for error in (raised.value, mcp.value):
        assert str(packet_project) not in str(error)
        assert "Error: Error:" not in str(error)
    result = cli_context(packet_project, "--budget", "32000", "--format", "packet", "--wiki-dir", "../outside-wiki")
    assert result.returncode == 1 and not result.stdout
    assert json.loads(result.stderr)["error"]["code"] == "path-policy-error"
    assert str(packet_project).encode() not in result.stderr
