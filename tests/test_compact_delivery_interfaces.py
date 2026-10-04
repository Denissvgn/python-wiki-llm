"""Real compact delivery preserves evidence and protects input/publication roots."""

from __future__ import annotations

from copy import deepcopy
import asyncio
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest
from mcp.types import CallToolResult, TextContent

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import task_compact
from llm_wiki_cli.services import context_session
from llm_wiki_cli.services import mcp_server
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from llm_wiki_cli.services.mcp_server import McpWikiService
from llm_wiki_cli.services.token_counting import EstimatedCounter
from tests.developer_value.fixtures import POLICY_SOURCE
from tests.test_task_compact_receiving import tiny_request, view_options


def tree(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_bytes(POLICY_SOURCE.encode())
    Path("request.json").write_text(json.dumps(tiny_request()), encoding="utf-8")
    return tmp_path


def native(project, capsys):
    api.bootstrap_wiki("src", "wiki")
    migrate_knowledge_storage(
        Path("wiki"), to="sharded-v2", recovery_dir=Path("recovery")
    )
    capsys.readouterr()


def execute_cli(
    monkeypatch,
    capsys,
    *,
    compact=True,
    destination: str | None = "receipt.json",
    output=None,
    extra=(),
):
    argv = [
        "llm-wiki",
        "task-context",
        "--request",
        "request.json",
        "--src-dir",
        "src",
        "--wiki-dir",
        "wiki",
    ]
    if compact:
        argv += ["--view", "compact-v1", "--view-budget-tokens", "32000"]
        if destination is not None:
            argv += ["--canonical-output", str(destination)]
    if output is not None:
        argv += ["--output", str(output)]
    argv += list(extra)
    with monkeypatch.context() as patch:
        patch.setattr(sys, "argv", argv)
        cli.main()
    return capsys.readouterr()


def assert_equivalent(view_text, canonical_text, request, *, options=None):
    opts = view_options() if options is None else options
    canonical = api.validate_task_context(canonical_text, request)
    selected = task_compact.expand_compact_task_context(
        view_text, canonical_text, request, view_options=opts
    )
    assert selected["facts"] == canonical["facts"]
    assert selected["coverage"] == canonical["coverage"]
    assert selected["omissions"] == canonical["omissions"]
    assert selected["canonical"]["result_id"] == canonical["result_id"]
    return canonical


@pytest.mark.parametrize("gap", [False, True])
def test_python_cli_compact_and_canonical_receipt_preserve_real_facts_and_gaps(
    project, monkeypatch, capsys, gap
):
    request = tiny_request()
    if gap:
        request["requirements"].append(
            {"id": "behavior", "facet": "behavior", "selector": "policy.py:Batch.cap"}
        )
        Path("request.json").write_text(json.dumps(request), encoding="utf-8")
    before = tree(Path("src")), tree(Path("wiki"))
    python = api.build_compact_task_context(
        request, src_dir="src", wiki_dir="wiki", view_options=view_options()
    )
    assert python.ok
    output = execute_cli(monkeypatch, capsys)
    assert output.err == ""
    assert output.out == python.rendered
    receipt = Path("receipt.json").read_text()
    assert receipt == python.canonical_text
    canonical = assert_equivalent(output.out, receipt, request)
    if gap:
        assert any(not row["satisfied"] for row in canonical["coverage"])
    assert (tree(Path("src")), tree(Path("wiki"))) == before
    counter = EstimatedCounter()
    assert python.accounting["used_tokens"] == counter.count(output.out)
    assert len(receipt.encode()) > len(output.out.encode())
    assert counter.count(output.out + receipt) > counter.count(output.out)
    assert counter.count("MCP framing:\n" + output.out) > counter.count(output.out)


def test_canonical_default_cli_bytes_and_public_builder_stay_unchanged(
    project, monkeypatch, capsys
):
    request = tiny_request()
    canonical = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    output = execute_cli(monkeypatch, capsys, compact=False)
    assert output.out == canonical.rendered and output.err == ""
    assert not Path("receipt.json").exists()
    view = api.build_compact_task_context(
        request, src_dir="src", wiki_dir="wiki", view_options=view_options()
    )
    assert view.canonical_text == canonical.rendered
    assert (
        api.build_task_context(request, src_dir="src", wiki_dir="wiki").rendered
        == canonical.rendered
    )


@pytest.mark.parametrize(
    "target",
    [
        "src/policy.py",
        "wiki/index.md",
        "request.json",
        "profile.json",
        "tokenizer.json",
        "compact.json",
    ],
)
def test_cli_receipt_destination_cannot_overwrite_inputs_or_model_output(
    project, monkeypatch, capsys, target
):
    Path("wiki").mkdir()
    Path("wiki/index.md").write_text("# Unadopted wiki\n")
    Path("profile.json").write_text(
        json.dumps(
            {
                "schema_version": "llm-wiki-workflow-profile/v1",
                "settings": {"knowledge_mode": "off"},
            }
        )
    )
    Path("tokenizer.json").write_text("inert invalid tokenizer input")
    Path("compact.json").write_text("existing model output")
    before = tree(project)
    extra = (
        ("--profile", "profile.json")
        if target == "profile.json"
        else ("--tokenizer", "tokenizer.json")
        if target == "tokenizer.json"
        else ()
    )
    output = "compact.json" if target == "compact.json" else None
    with pytest.raises(SystemExit):
        execute_cli(monkeypatch, capsys, destination=target, output=output, extra=extra)
    failure = capsys.readouterr()
    assert failure.out == ""
    assert tree(project) == before


def test_cli_requires_explicit_receipt_path_and_rejects_redirected_destination(
    project, monkeypatch, capsys
):
    before = tree(project)
    with pytest.raises(SystemExit):
        execute_cli(monkeypatch, capsys, destination=None)
    assert tree(project) == before
    capsys.readouterr()
    Path("receipt-link.json").symlink_to(Path("src/policy.py"))
    source = Path("src/policy.py").read_bytes()
    with pytest.raises(SystemExit):
        execute_cli(monkeypatch, capsys, destination="receipt-link.json")
    failure = capsys.readouterr()
    assert failure.out == ""
    assert Path("src/policy.py").read_bytes() == source


@pytest.mark.parametrize("surface", ["source", "wiki"])
def test_python_compact_publication_rechecks_actual_inputs_after_counter_callback(
    project, capsys, surface
):
    native(project, capsys)
    request = tiny_request()
    request["options"]["knowledge_mode"] = "auto"
    request["requirements"].append(
        {"id": "class", "facet": "concept", "selector": "llm-wiki://entities/Batch"}
    )

    class MutatingCounter(EstimatedCounter):
        changed = False

        def count(self, text):
            if '"schema_version":"llm-wiki-task-compact/v1"' in text:
                self.changed = True
                path = (
                    Path("src/policy.py")
                    if surface == "source"
                    else Path("wiki/entities/Batch.md")
                )
                path.write_bytes(path.read_bytes() + b"\n# concurrent input edit\n")
            return super().count(text)

    counter = MutatingCounter()
    with pytest.raises(api.LlmWikiApiError):
        api.build_compact_task_context(
            request,
            src_dir="src",
            wiki_dir="wiki",
            view_options=view_options(),
            counter=counter,
        )
    assert counter.changed


def test_cli_receipt_hardlink_is_rejected_before_build_and_cannot_destroy_request(
    project, monkeypatch, capsys
):
    import os

    os.link("request.json", "hardlink-receipt.json")
    before = tree(project)
    monkeypatch.setattr(
        api,
        "build_compact_task_context",
        lambda *args, **kwargs: pytest.fail(
            "unsafe destination reached workspace build"
        ),
    )
    with pytest.raises(SystemExit):
        execute_cli(monkeypatch, capsys, destination="hardlink-receipt.json")
    assert capsys.readouterr().out == ""
    assert tree(project) == before


def test_cli_destination_redirected_after_render_is_rejected_without_publishing_model_text(
    project, monkeypatch, capsys
):
    original = api.build_compact_task_context
    source = Path("src/policy.py").read_bytes()

    def redirect(*args, **kwargs):
        result = original(*args, **kwargs)
        Path("receipt.json").symlink_to(Path("src/policy.py"))
        return result

    monkeypatch.setattr(api, "build_compact_task_context", redirect)
    with pytest.raises(SystemExit):
        execute_cli(monkeypatch, capsys)
    assert capsys.readouterr().out == ""
    assert Path("src/policy.py").read_bytes() == source


def test_cli_transports_exact_captured_evidence_after_api_return_without_new_currentness_claim(
    project, monkeypatch, capsys
):
    original = api.build_compact_task_context
    captured = []
    old_source = Path("src/policy.py").read_bytes()

    def after_return(*args, **kwargs):
        result = original(*args, **kwargs)
        captured.append(result)
        Path("src/policy.py").write_text(
            POLICY_SOURCE.replace("limit: int = 3", "limit: int = 4")
        )
        return result

    monkeypatch.setattr(api, "build_compact_task_context", after_return)
    output = execute_cli(monkeypatch, capsys)
    assert output.out == captured[0].rendered
    assert Path("receipt.json").read_text() == captured[0].canonical_text
    assert Path("src/policy.py").read_bytes() != old_source
    receipt = assert_equivalent(output.out, captured[0].canonical_text, tiny_request())
    assert (
        receipt["source_capture"]["inputs"][0]["content_hash"]
        != "sha256:" + sha256(Path("src/policy.py").read_bytes()).hexdigest()
    )
    fresh = original(
        tiny_request(), src_dir="src", wiki_dir="wiki", view_options=view_options()
    )
    assert fresh.canonical_text != captured[0].canonical_text


@pytest.mark.parametrize(
    "axis",
    [
        "wiki",
        "source",
        "request",
        "profile",
        "tokenizer",
        "selection",
        "model-descendant",
        "receipt-descendant",
    ],
)
def test_artifact_ancestor_or_descendant_overlap_is_rejected_before_workspace_build(
    project, monkeypatch, capsys, axis
):
    destination, output, extra = "future", None, ()
    if axis == "wiki":
        extra = ("--wiki-dir", "future/wiki")
    elif axis == "source":
        extra = ("--src-dir", "future/source")
    elif axis == "request":
        extra = ("--request", "future/request.json")
    elif axis == "profile":
        extra = ("--profile", "future/profile.json")
    elif axis == "tokenizer":
        extra = ("--tokenizer", "future/tokenizer.json")
    elif axis == "selection":
        extra = ("--source-selection", "future/selection.json")
    elif axis == "model-descendant":
        output = "future/view.json"
    else:
        destination, output = "future/receipt.json", "future"
    before = tree(project)
    monkeypatch.setattr(
        api,
        "build_compact_task_context",
        lambda *args, **kwargs: pytest.fail(
            "ancestor/descendant artifact reached workspace build"
        ),
    )
    with pytest.raises(SystemExit):
        execute_cli(
            monkeypatch, capsys, destination=destination, output=output, extra=extra
        )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert not Path("future").exists()
    assert tree(project) == before


def test_public_session_exact_receipt_and_conditional_view_require_owned_base(project):
    request = tiny_request()
    session = api.open_context_session(src_dir="src", wiki_dir="wiki")
    first = session.read_compact(request, view_options=view_options())
    assert (
        first.state == "full" and first.view is not None and first.canonical is not None
    )
    canonical = assert_equivalent(
        first.view.rendered, first.canonical.rendered, request
    )
    receipt = session.canonical_receipt(canonical["request_id"], canonical["result_id"])
    assert receipt.canonical.rendered == first.canonical.rendered
    assert receipt.validation_scope == "historical-captured"
    warm = session.read_compact(
        request,
        view_options=view_options(),
        if_result_id=first.result_id,
        if_view_id=first.view_id,
    )
    assert warm.state == "unchanged" and warm.view is None
    missing = session.read_compact(
        request,
        view_options=view_options(),
        if_result_id=first.result_id,
        if_view_id="sha256:" + "0" * 64,
    )
    assert missing.state == "full" and missing.view is not None
    wrong = api.open_context_session(src_dir="src", wiki_dir="wiki")
    with pytest.raises(api.LlmWikiApiError):
        wrong.canonical_receipt(canonical["request_id"], canonical["result_id"])
    fresh = wrong.read_compact(
        request,
        view_options=view_options(),
        if_result_id=first.result_id,
        if_view_id=first.view_id,
    )
    assert fresh.state == "full" and fresh.view is not None
    session.close()
    with pytest.raises(api.LlmWikiApiError):
        session.canonical_receipt(canonical["request_id"], canonical["result_id"])


def test_receipt_historical_bytes_do_not_mask_failed_current_validation(project):
    request = tiny_request()
    session = api.open_context_session(src_dir="src", wiki_dir="wiki")
    first = session.read_compact(request, view_options=view_options())
    assert first.canonical is not None
    payload = first.canonical.to_payload()
    Path("src/policy.py").write_text(
        POLICY_SOURCE.replace("limit: int = 3", "limit: int = 4")
    )
    historical = session.canonical_receipt(payload["request_id"], payload["result_id"])
    assert historical.validation_scope == "historical-captured"
    assert historical.canonical.rendered == first.canonical.rendered
    with pytest.raises(api.LlmWikiApiError):
        session.canonical_receipt(
            payload["request_id"], payload["result_id"], current=True
        )
    current = session.read_compact(
        request,
        view_options=view_options(),
        if_result_id=first.result_id,
        if_view_id=first.view_id,
        delta=True,
    )
    assert (
        current.state != "unchanged"
        and current.view is not None
        and current.canonical is not None
    )
    assert current.result_id != first.result_id
    assert_equivalent(current.view.rendered, current.canonical.rendered, request)


def test_unavailable_environment_allows_bounded_receipt_custody_without_capture_reuse(
    project, monkeypatch
):
    original = context_session.shutil.which
    monkeypatch.setattr(
        context_session.shutil,
        "which",
        lambda value: None if value == "git" else original(value),
    )
    request = tiny_request()
    session = api.open_context_session(src_dir="src", wiki_dir="wiki")
    first = session.read_compact(request, view_options=view_options())
    assert first.canonical is not None
    payload = first.canonical.to_payload()
    receipt = session.canonical_receipt(payload["request_id"], payload["result_id"])
    assert receipt.canonical.rendered == first.canonical.rendered
    assert receipt.validation_scope == "historical-captured"
    second = session.read_compact(
        request,
        view_options=view_options(),
        if_result_id=first.result_id,
        if_view_id=first.view_id,
    )
    assert second.state == "full" and second.view is not None
    assert not second.metadata()["reuse"]["capture"]


def test_ttl_cancellation_unsaved_and_disabled_custody_require_fresh_reads(
    project, monkeypatch
):
    tick = [100.0]
    monkeypatch.setattr(context_session.time, "monotonic", lambda: tick[0])
    request = tiny_request()
    session = api.open_context_session(src_dir="src", wiki_dir="wiki", ttl_seconds=1)
    first = session.read_compact(request, view_options=view_options())
    assert first.canonical is not None
    payload = first.canonical.to_payload()
    tick[0] += 2
    with pytest.raises(api.LlmWikiApiError):
        session.canonical_receipt(payload["request_id"], payload["result_id"])
    fresh = session.read_compact(
        request,
        view_options=view_options(),
        if_result_id=first.result_id,
        if_view_id=first.view_id,
    )
    assert fresh.state == "full" and fresh.view is not None
    session.hint(unsaved_buffers=True)
    with pytest.raises(api.LlmWikiApiError):
        session.read_compact(request, view_options=view_options())
    session.hint(unsaved_buffers=False)
    with pytest.raises(api.LlmWikiApiError):
        session.read_compact(
            request, view_options=view_options(), cancelled=lambda: True
        )
    with pytest.raises(api.LlmWikiApiError):
        session.canonical_receipt(payload["request_id"], payload["result_id"])
    disabled = api.open_context_session(src_dir="src", wiki_dir="wiki", max_entries=0)
    full = disabled.read_compact(request, view_options=view_options())
    assert full.view is not None and full.canonical is not None
    body = full.canonical.to_payload()
    with pytest.raises(api.LlmWikiApiError):
        disabled.canonical_receipt(body["request_id"], body["result_id"])


def test_mcp_configured_session_view_and_explicit_receipt_match_python_without_implicit_duplicate(
    project,
):
    request = tiny_request()
    expected = api.build_compact_task_context(
        request, src_dir="src", wiki_dir="wiki", view_options=view_options()
    )
    service = McpWikiService("src", "wiki", enable_sessions=True)
    handle = service.open_context_session()["session_id"]
    reply = service.read_compact_context_session(handle, request, view_options())
    assert reply.view is not None
    assert reply.view.rendered == expected.rendered
    payload = json.loads(reply.view.rendered)
    receipt = service.get_task_context_receipt(
        handle, payload["canonical"]["request_id"], payload["canonical"]["result_id"]
    )
    assert receipt.canonical.rendered == expected.canonical_text
    assert receipt.validation_scope == "historical-captured"
    assert expected.canonical_text not in json.dumps(reply.metadata())
    with pytest.raises(mcp_server.McpWikiError):
        service.get_task_context_receipt(
            handle, "sha256:" + "0" * 64, payload["canonical"]["result_id"]
        )
    other = service.open_context_session()["session_id"]
    with pytest.raises(mcp_server.McpWikiError):
        service.get_task_context_receipt(
            other, payload["canonical"]["request_id"], payload["canonical"]["result_id"]
        )
    service.close_context_session(handle)
    with pytest.raises(mcp_server.McpWikiError):
        service.read_compact_context_session(handle, request, view_options())
    fresh = service.read_compact_context_session(
        other,
        request,
        view_options(),
        if_result_id=reply.result_id,
        if_view_id=reply.view_id,
    )
    assert fresh.state == "full" and fresh.view is not None


def test_actual_mcp_sdk_content_carries_view_then_receipt_as_separate_transport(
    project,
):
    server = mcp_server.create_mcp_server(
        mcp_server.McpServerConfig(src_dir="src", wiki_dir="wiki", enable_sessions=True)
    )

    async def call(name, arguments):
        return await server.call_tool(name, arguments)

    opened = asyncio.run(call("open_context_session", {}))
    # Ordinary dict tools are text-encoded by the SDK; compact/receipt tools
    # explicitly return CallToolResult with content and separate bounded metadata.
    if isinstance(opened, CallToolResult):
        block = opened.content[0]
        assert isinstance(block, TextContent)
        handle = json.loads(block.text)["session_id"]
    elif isinstance(opened, (list, tuple)):
        block = opened[0]
        if isinstance(block, list):
            block = block[0]
        assert isinstance(block, TextContent)
        handle = json.loads(block.text)["session_id"]
    else:
        assert isinstance(opened, dict)
        handle = opened["session_id"]
    request = tiny_request()
    delivered = asyncio.run(
        call(
            "read_compact_context_session",
            {"session_id": handle, "request": request, "view_options": view_options()},
        )
    )
    assert isinstance(delivered, CallToolResult)
    block = delivered.content[0]
    assert isinstance(block, TextContent)
    text = block.text
    payload = json.loads(text)
    assert payload["schema_version"] == "llm-wiki-task-compact/v1"
    receipt = asyncio.run(
        call(
            "get_task_context_receipt",
            {
                "session_id": handle,
                "request_id": payload["canonical"]["request_id"],
                "result_id": payload["canonical"]["result_id"],
            },
        )
    )
    assert isinstance(receipt, CallToolResult)
    block = receipt.content[0]
    assert isinstance(block, TextContent)
    canonical_text = block.text
    assert_equivalent(text, canonical_text, request)
    model_transport = delivered.model_dump(mode="json")
    assert canonical_text not in json.dumps(model_transport)
    assert "source_capture" not in json.dumps(delivered.structuredContent)
    counter = EstimatedCounter()
    assert counter.count(canonical_text) > counter.count(text)
    assert counter.count(json.dumps(model_transport)) > counter.count(text)
    assert counter.count(text + canonical_text) > counter.count(text)


@pytest.mark.parametrize("change", ["source", "ignore", "selection"])
def test_real_session_source_and_control_edits_never_serve_prior_unchanged_view(
    project, change
):
    request = tiny_request()
    session = api.open_context_session(src_dir="src", wiki_dir="wiki")
    first = session.read_compact(request, view_options=view_options())
    if change == "source":
        Path("src/policy.py").write_text(
            POLICY_SOURCE.replace("limit: int = 3", "limit: int = 4")
        )
    elif change == "ignore":
        Path("src/.gitignore").write_text("# changed selection-control bytes\n")
    else:
        Path("src/.llm-wiki").mkdir()
        Path("src/.llm-wiki/source-selection.json").write_text(
            json.dumps(
                {
                    "schema_version": "llm-wiki-source-selection/v1",
                    "include": ["policy.py"],
                    "exclude": [],
                }
            )
        )
    second = session.read_compact(
        request,
        view_options=view_options(),
        if_result_id=first.result_id,
        if_view_id=first.view_id,
    )
    assert (
        second.state == "full"
        and second.view is not None
        and second.canonical is not None
    )
    assert second.result_id != first.result_id
    assert_equivalent(second.view.rendered, second.canonical.rendered, request)


def test_session_options_change_requires_complete_view_not_missing_base_inference(
    project,
):
    request = tiny_request()
    session = api.open_context_session(src_dir="src", wiki_dir="wiki")
    first = session.read_compact(request, view_options=view_options())
    options = view_options(30000)
    changed = session.read_compact(
        request,
        view_options=options,
        if_result_id=first.result_id,
        if_view_id=first.view_id,
    )
    assert changed.state == "full" and changed.view is not None
    assert changed.view_id != first.view_id
    altered = deepcopy(request)
    altered["text"] = "New task intent with same source input."
    changed_request = session.read_compact(
        altered,
        view_options=options,
        if_result_id=first.result_id,
        if_view_id=first.view_id,
    )
    assert changed_request.state == "full" and changed_request.view is not None


def test_cli_compact_size_failure_retains_exact_host_receipt_without_publishing_view(
    project, monkeypatch, capsys
):
    request = tiny_request()
    expected = api.build_compact_task_context(
        request, src_dir="src", wiki_dir="wiki", view_options=view_options(1000)
    )
    assert not expected.ok and expected.error == "cannot-fit-compact"
    Path("view.json").write_text("old model view")
    with pytest.raises(SystemExit) as error:
        execute_cli(
            monkeypatch,
            capsys,
            output="view.json",
            extra=("--view-budget-tokens", "1000"),
        )
    output = capsys.readouterr()
    assert error.value.code == 3 and output.out == ""
    assert output.err == expected.diagnostic_rendered
    assert Path("receipt.json").read_text() == expected.canonical_text
    assert Path("view.json").read_text() == "old model view"
    assert "facts" not in json.loads(output.err)


def test_canonical_failure_cannot_be_delivered_as_compact_or_written_as_receipt(
    project, monkeypatch, capsys
):
    request = tiny_request()
    request["options"]["budget_tokens"] = 1
    Path("request.json").write_text(json.dumps(request))
    ordinary = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    assert not ordinary.ok and ordinary.error == "cannot-fit"
    with pytest.raises(api.LlmWikiApiError):
        api.build_compact_task_context(
            request, src_dir="src", wiki_dir="wiki", view_options=view_options(1)
        )
    with pytest.raises(SystemExit):
        execute_cli(monkeypatch, capsys, extra=("--view-budget-tokens", "1"))
    assert capsys.readouterr().out == ""
    assert not Path("receipt.json").exists()


def test_native_python_cli_and_session_delivery_preserve_selected_receipt_scope(
    project, monkeypatch, capsys
):
    native(project, capsys)
    request = tiny_request()
    request["options"]["knowledge_mode"] = "required"
    request["requirements"].append(
        {"id": "native", "facet": "concept", "selector": "llm-wiki://entities/Batch"}
    )
    Path("request.json").write_text(json.dumps(request))
    before = tree(Path("src")), tree(Path("wiki"))
    expected = api.build_compact_task_context(
        request, src_dir="src", wiki_dir="wiki", view_options=view_options()
    )
    assert expected.ok
    output = execute_cli(monkeypatch, capsys)
    assert output.out == expected.rendered
    assert Path("receipt.json").read_text() == expected.canonical_text
    session = api.open_context_session(src_dir="src", wiki_dir="wiki")
    reply = session.read_compact(request, view_options=view_options())
    assert reply.view is not None and reply.canonical is not None
    assert (
        reply.view.rendered == expected.rendered
        and reply.canonical.rendered == expected.canonical_text
    )
    result = assert_equivalent(reply.view.rendered, reply.canonical.rendered, request)
    assert (
        result["storage"]["status"] == "scoped"
        and result["storage"]["whole_store_validated"] is False
    )
    assert (tree(Path("src")), tree(Path("wiki"))) == before
