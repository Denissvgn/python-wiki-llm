"""Real SDK receiving and advisory CI boundaries on owned combined inputs."""

from __future__ import annotations

import asyncio
from hashlib import sha256
import importlib.util
import io
import json
import os
import sys
from unittest.mock import patch

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import mcp_server
from tests.developer_value.combined_workflows import (
    input_packet, prepare_combined, request_for, source_after,
)
from tests.developer_value.workflow_fixtures import (
    VIEW, mutate_source, prepare_workflow, record_workflow_trace, sync_workflow,
)
from tests.developer_value.workflow_oracles import (
    REQUIRED_GAP_STATES, assert_coverage_gap, assert_coverage_preserved,
)


def _protected(project):
    return {name: (raw, (project.root / name).stat().st_mtime_ns)
            for name, raw in project.tree().items() if name.startswith(("src/", "wiki/"))}


def _receipt_inventory(snapshot):
    return {name: {"sha256": sha256(raw).hexdigest(), "bytes": len(raw), "mtime_ns": mtime}
            for name, (raw, mtime) in snapshot.items()}


@pytest.mark.parametrize("variant", ["source-only", "sharded", "packed"])
def test_actual_sdk_combined_callers_compact_and_stale_custody(tmp_path, monkeypatch, capsys, variant):
    if importlib.util.find_spec("mcp") is None:
        if os.environ.get("LLM_WIKI_REQUIRE_MCP_SDK") == "1":
            pytest.fail("MCP SDK required by this environment")
        pytest.skip("Optional MCP SDK is not installed")
    from mcp import types as mcp_types

    monkeypatch.chdir(tmp_path)
    project = prepare_combined(tmp_path, variant)
    capsys.readouterr()
    request = request_for(variant)
    server = mcp_server.create_mcp_server(mcp_server.McpServerConfig(
        **project.options, workflow_policy=project.context_options["policy"], enable_sessions=True))
    observations = {"transport": "Actual installed SDK CallToolRequest handler; network unobserved", "calls": [],
                    "mutation_scope": "policy.py body only; client.py remains before, distinct auxiliary receiving scope"}

    async def exercise():
        async def call(name, arguments):
            before = _protected(project)
            handler = server._mcp_server.request_handlers[mcp_types.CallToolRequest]
            reply = await handler(mcp_types.CallToolRequest(method="tools/call",
                params=mcp_types.CallToolRequestParams(name=name, arguments=arguments)))
            result = reply.root
            after = _protected(project)
            observations["calls"].append({"tool": name, "arguments": arguments,
                "response": result.model_dump(mode="json"),
                "inventory_before": _receipt_inventory(before), "inventory_after": _receipt_inventory(after)})
            record_workflow_trace(project, "combined-sdk-progress", observations)
            assert isinstance(result, mcp_types.CallToolResult)
            assert after == before
            assert not (project.root / "source-execution-tripwire").exists()
            return result

        def body(result):
            return next(block.text for block in result.content if block.type == "text")

        for target, expected in input_packet()["caller_expectations"].items():
            result = await call("query_graph", {"query": {"type": "callers", "value": target, "limit": 100}})
            assert not result.isError
            payload = result.structuredContent or json.loads(body(result))
            assert {row["file"] + ":" + row["symbol"] for row in payload["callers"]} == set(expected)
            assert payload["coverage"]["runtime_completeness"] is False
        opened = await call("open_context_session", {})
        assert not opened.isError
        session_id = (opened.structuredContent or json.loads(body(opened)))["session_id"]
        first = await call("read_compact_context_session", {"session_id": session_id, "request": request, "view_options": VIEW})
        assert not first.isError
        view = body(first)
        compact = json.loads(view)
        assert compact["schema_version"] == "llm-wiki-task-compact/v1"
        identity = compact["canonical"]
        arguments = {"session_id": session_id, "request_id": identity["request_id"], "result_id": identity["result_id"]}
        receipt = await call("get_task_context_receipt", arguments)
        assert not receipt.isError
        canonical_text = body(receipt)
        canonical = api.validate_task_context(canonical_text, request, policy=project.context_options["policy"])
        expanded = api.expand_compact_task_context(view, canonical_text, request, view_options=VIEW, policy=project.context_options["policy"])
        assert_coverage_preserved(canonical, expanded)
        for name, states in REQUIRED_GAP_STATES.items():
            assert_coverage_gap(expanded, name, states=states)
        current = await call("get_task_context_receipt", {**arguments, "current": True})
        assert not current.isError and body(current) == canonical_text
        (project.source / "policy.py").write_text(source_after())
        historical = await call("get_task_context_receipt", arguments)
        assert not historical.isError and body(historical) == canonical_text
        stale = await call("get_task_context_receipt", {**arguments, "current": True})
        assert stale.isError
        assert stale.structuredContent and stale.structuredContent["error"]["code"] == "context-read-mutated"
        if variant != "source-only":
            sync_workflow(project)
        fresh = await call("read_compact_context_session", {"session_id": session_id, "request": request, "view_options": VIEW})
        assert not fresh.isError
        fresh_view = body(fresh)
        fresh_ids = json.loads(fresh_view)["canonical"]
        fresh_receipt = await call("get_task_context_receipt", {"session_id": session_id,
            "request_id": fresh_ids["request_id"], "result_id": fresh_ids["result_id"]})
        assert not fresh_receipt.isError
        new = api.validate_task_context(body(fresh_receipt), request, policy=project.context_options["policy"])
        api.expand_compact_task_context(fresh_view, body(fresh_receipt), request, view_options=VIEW, policy=project.context_options["policy"])
        assert new["result_id"] != canonical["result_id"] and new["task_id"] == canonical["task_id"]
        assert not (await call("close_context_session", {"session_id": session_id})).isError
        observations.update({"request": request, "canonical_text": canonical_text, "compact_text": view,
                             "fresh_canonical_text": body(fresh_receipt), "fresh_compact_text": fresh_view})

    asyncio.run(exercise())
    record_workflow_trace(project, "combined-sdk", observations)


@pytest.mark.parametrize("variant", ["adopted-flat", "sharded", "packed"])
def test_real_ci_drift_report_preserves_integrity_exit_and_is_advisory(tmp_path, monkeypatch, capsys, variant):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, variant)
    capsys.readouterr()
    calls = []

    def ci_check(advisory):
        before = _protected(project)
        arguments = ["llm-wiki", "ci-check", "--src-dir", str(project.source), "--wiki-dir", str(project.wiki),
            "--no-report", "--no-cache", "--no-plugins", "--jobs", "1", "--progress", "never", "--format", "json", "--report-schema", "v4"]
        if advisory:
            arguments.append("--knowledge-drift-report")
        stdout, stderr = io.StringIO(), io.StringIO()
        from contextlib import redirect_stdout, redirect_stderr
        with patch.object(sys, "argv", arguments), redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                cli.main()
            except SystemExit as stopped:
                code = stopped.code
            else:
                code = 0
        after = _protected(project)
        raw = {"exit_code": code, "stdout": stdout.getvalue(), "stderr": stderr.getvalue(),
               "arguments": arguments, "inventory_before": _receipt_inventory(before),
               "inventory_after": _receipt_inventory(after)}
        calls.append(raw)
        record_workflow_trace(project, "combined-ci-advisory-progress", {"calls": calls})
        assert after == before
        payload = json.loads(stdout.getvalue())
        assert payload["knowledge_drift_gate"] is False
        assert payload["command_exit_code"] == code
        return {**raw, "payload": payload}

    before = ci_check(False)
    assert before["exit_code"] == 0
    mutate_source(project, "default")
    plain = ci_check(False)
    advisory = ci_check(True)
    assert plain["exit_code"] == advisory["exit_code"] == 1
    assert plain["payload"]["issues"] == advisory["payload"]["issues"]
    assert not plain["payload"]["diagnostics"] and advisory["payload"]["diagnostics"]
    assert all(row["severity"] == "warning" for row in advisory["payload"]["diagnostics"])
    sync_workflow(project)
    current = ci_check(True)
    assert current["exit_code"] == 0
    assert not (project.root / "source-execution-tripwire").exists()
    record_workflow_trace(project, "combined-ci-advisory", {"initial": before, "changed_plain": plain,
        "changed_advisory": advisory, "after_sync": current, "advisory_does_not_change_integrity_exit": True,
        "schema_choice": "Explicit compatible v4 for flat/sharded/packed; no default schema change"})
