"""Installed workflow acceptance through public APIs and actual MCP transports."""

import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import socket
import subprocess
import sys

from llm_wiki_cli import api


class ByteCounter:
    identity = "utf8-bytes/v1"
    exact = True

    def count(self, text: str) -> int:
        return len(text.encode("utf-8"))


def tree(root):
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts}


def text_of(result):
    assert not result.isError and len(result.content) == 1
    content = result.content[0]
    assert content.type == "text"
    return content.text


def structured(result):
    assert result.structuredContent is not None
    return result.structuredContent


tutorial, mode, probe_path, receipt = sys.argv[1:5]
project = Path.cwd() / ("workflow-" + mode)
shutil.copytree(Path(tutorial) / "project", project)
os.chdir(project)
assert Path(api.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
environment.pop("PYTHONPATH", None)


def run(arguments, *, code=0, input_text=None):
    result = subprocess.run([sys.executable, *arguments], capture_output=True, text=True,
                            input=input_text, env=environment, timeout=60, cwd=project)
    assert result.returncode == code, (arguments, result.stdout, result.stderr)
    return result


def client(command, *options):
    return json.loads(run(["client.py", command, *options]).stdout)


client("prepare")
request = json.loads(Path("request.json").read_text())
source, wiki = "src", "wiki"
before = tree(project)
search = api.search_wiki("cap", src_dir=source, wiki_dir=wiki)
assert search["results"] and search["mode"] == "ranked"
queue = api.build_maintenance_queue(source, wiki, limit=2)
assert queue["advisory"] and queue["returned"] <= 2
context = api.build_task_context(request, src_dir=source, wiki_dir=wiki)
assert context.ok
payload = api.validate_task_context(context.rendered, request)
assert all(item["satisfied"] for item in payload["coverage"])
contract = next(fact for fact in payload["facts"] if fact["selector"] == "policy.py:cap#1")
assert contract["observation"]["contract"]["params"][1]["default"] == "3"
assert len(payload["facts"]) == 2
cli_text = run(["-I", "-m", "llm_wiki_cli.cli", "task-context", "--src-dir", source,
                "--wiki-dir", wiki, "--request", "-"], input_text=json.dumps(request)).stdout
assert cli_text == context.rendered
query = {"operation": "surface", "value": "modules/policy.md"}
cli_query = run(["-I", "-m", "llm_wiki_cli.cli", "query", "--src-dir", source,
                "--wiki-dir", wiki, "--request", "-"], input_text=json.dumps(query)).stdout
assert json.loads(cli_query) == api.query_documentation(query, src_dir=source, wiki_dir=wiki)
assert tree(project) == before
with api.open_context_session(src_dir=source, wiki_dir=wiki) as session:
    first = session.read(request)
    assert first.context is not None
    assert session.read(request, if_result_id=first.result_id).state == "unchanged"
    cold = session.read(request, reuse=False)
    assert cold.context is not None and cold.context.rendered == first.context.rendered
    session.hint(unsaved_buffers=True)
    try:
        session.read(request)
    except api.InvalidRequestError:
        pass
    else:
        raise AssertionError("unsaved buffers accepted")

for invalid in ({**request, "tokenizer": "/outside"}, {**request, "options": {"max_files": True}}):
    try:
        api.build_task_context(invalid, src_dir=source, wiki_dir=wiki)
    except api.InvalidRequestError:
        pass
    else:
        raise AssertionError("invalid task request accepted")
assert tree(project) == before
client("handoff")
assert client("check")["behavior_matches"] is False
client("change")
assert client("check")["behavior_matches"] is True
assert client("resume")["basis_matches"] is False
client("note")
run(["-I", "-m", "llm_wiki_cli.cli", "sync", "--src-dir", source, "--wiki-dir", wiki, "--no-plugins"])
assert "a full permitted batch must retain every item" in Path("wiki/modules/policy.md").read_text()
assert all(item["satisfied"] for item in client("read", "--no-session")["coverage"])
client("handoff", "--no-session")
assert client("resume", "--no-session")["basis_matches"] is True

# Adopt through the installed CLI and keep the legacy workflow usable.
preview = json.loads(run(["-I", "-m", "llm_wiki_cli.cli", "knowledge", "migrate", "--wiki-dir", wiki,
                          "--to", "sharded-v2", "--dry-run", "--recovery-dir", "storage-recovery"]).stdout)
assert preview["changed"]
run(["-I", "-m", "llm_wiki_cli.cli", "knowledge", "migrate", "--wiki-dir", wiki,
     "--to", "sharded-v2", "--recovery-dir", "storage-recovery"])
storage = json.loads(run(["-I", "-m", "llm_wiki_cli.cli", "knowledge", "storage-check", "--wiki-dir", wiki, "--full"]).stdout)
assert storage["ok"] and storage["format"] == "sharded-v2"
# Both packed profiles preserve the installed full and scoped consumers.
for storage_format in ("packed-v3", "packed-v3-deflate"):
    run(["-I", "-m", "llm_wiki_cli.cli", "knowledge", "migrate", "--wiki-dir", wiki,
         "--to", storage_format, "--recovery-dir", "recovery-" + storage_format])
    report = json.loads(run(["-I", "-m", "llm_wiki_cli.cli", "knowledge", "storage-check",
                             "--wiki-dir", wiki, "--full"]).stdout)
    assert report["ok"] and report["format"] == storage_format and report["physical_packs"]
    assert api.validate_task_context(api.build_task_context(request, src_dir=source, wiki_dir=wiki).rendered, request)["state"] == "covered"
    repeat = json.loads(run(["-I", "-m", "llm_wiki_cli.cli", "knowledge", "migrate", "--wiki-dir", wiki,
                             "--to", storage_format, "--dry-run"]).stdout)
    assert not repeat["changed"]
run(["-I", "-m", "llm_wiki_cli.cli", "knowledge", "migrate", "--wiki-dir", wiki,
     "--to", "indexed-v6", "--recovery-dir", "recovery-manifest-v6"])
manifest_root = Path(wiki, ".llm-wiki-manifest.json").read_bytes()
assert json.loads(manifest_root)["version"] == 6 and len(manifest_root) < 16_384
streamed = json.loads(run(["-I", "-m", "llm_wiki_cli.cli", "knowledge", "storage-check",
                          "--wiki-dir", wiki, "--stream"]).stdout)
assert streamed["ok"] and not streamed["whole_snapshot_validated"]
inspection = json.loads(run(["-I", "-m", "llm_wiki_cli.cli", "knowledge", "inspect-storage",
                            "--wiki-dir", wiki, "--selector", "page:modules/policy.md", "--limit", "1"]).stdout)
assert inspection["validation_scope"] == "selected-records-and-policy" and inspection["records"]
scoped_request = {**request, "schema_version": "llm-wiki-task-request/v2"}
scoped = api.build_task_context(scoped_request, src_dir=source, wiki_dir=wiki)
scoped_payload = api.validate_task_context(scoped.rendered, scoped_request)
assert scoped_payload["packet"] is None and scoped_payload["storage"]["whole_store_validated"] is False
assert scoped_payload["storage"]["schema_version"] == "llm-wiki-task-storage/v2"
assert scoped_payload["storage"]["ranges"]
assert all(item["satisfied"] for item in scoped_payload["coverage"])
assert run(["-I", "-m", "llm_wiki_cli.cli", "task-context", "--src-dir", source, "--wiki-dir", wiki,
            "--request", "-"], input_text=json.dumps(scoped_request)).stdout == scoped.rendered


async def transport(transport_name):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.streamable_http import streamable_http_client

    probe_type = runpy.run_path(probe_path)["McpProbe"]
    output = Path(receipt).with_name(Path(receipt).stem + "-" + transport_name + ".json")
    probe = probe_type(output, ["initialize", "v3", "task", "scoped", "invalid", "session", "mutation", "close"])
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server_code = '''from llm_wiki_cli.services.mcp_server import McpServerConfig, run_mcp_server
class Counter:
    identity = "utf8-bytes/v1"
    exact = True
    def count(self, text): return len(text.encode("utf-8"))
run_mcp_server(McpServerConfig(src_dir="src", wiki_dir="wiki", counter=Counter(),
    enable_sessions=True, transport=TRANSPORT, port=PORT))
'''.replace("TRANSPORT", repr(transport_name)).replace("PORT", str(port))
    parameters = StdioServerParameters(command=sys.executable, args=["-I", "-c", server_code],
                                       cwd=str(project), env=environment)

    @asynccontextmanager
    async def connection():
        if transport_name == "stdio":
            async with stdio_client(parameters) as streams:
                yield streams[0], streams[1]
        else:
            with output.with_suffix(".server.log").open("w") as log:
                process = subprocess.Popen([sys.executable, "-I", "-c", server_code], cwd=project,
                                           env=environment, stdout=log, stderr=log)
                try:
                    for _ in range(100):
                        if process.poll() is not None:
                            raise AssertionError("HTTP server exited before connection")
                        try:
                            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                                break
                        except OSError:
                            await asyncio.sleep(0.1)
                    else:
                        raise AssertionError("HTTP server did not start")
                    async with streamable_http_client(f"http://127.0.0.1:{port}/mcp") as streams:
                        yield streams[0], streams[1]
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)

    with probe.session():
        async with connection() as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=45)) as session:
                with probe.step("initialize"):
                    await session.initialize()
                    names = {tool.name for tool in (await session.list_tools()).tools}
                    assert {"build_budgeted_context", "build_task_context", "open_context_session"} <= names
                before_reads = tree(project)
                with probe.step("v3"):
                    req = {"protocol": "llm-wiki-context/v3", "budget_tokens": 200000,
                           "budget_mode": "exact", "format": "packet", "focus": ["all"],
                           "changes": {"mode": "paths", "paths": ["policy.py", "deleted.py"]}}
                    expected = api.build_budgeted_context(source, wiki, req, counter=ByteCounter())
                    result = await session.call_tool("build_budgeted_context", {"request": req})
                    assert not result.isError and result.structuredContent is None and len(result.content) == 1
                    assert text_of(result) == expected.rendered
                    api.validate_budgeted_context(text_of(result), req, counter=ByteCounter())
                with probe.step("task"):
                    expected = api.build_task_context(request, src_dir=source, wiki_dir=wiki, counter=ByteCounter())
                    result = await session.call_tool("build_task_context", {"request": request})
                    assert not result.isError and result.structuredContent is None and len(result.content) == 1
                    assert text_of(result) == expected.rendered
                with probe.step("scoped"):
                    expected_scoped = api.build_task_context(scoped_request, src_dir=source, wiki_dir=wiki, counter=ByteCounter())
                    result = await session.call_tool("build_task_context", {"request": scoped_request})
                    assert result.structuredContent is None and text_of(result) == expected_scoped.rendered
                    api.validate_task_context(text_of(result), scoped_request, counter=ByteCounter())
                    opened_scoped = await session.call_tool("open_context_session", {})
                    scoped_handle = structured(opened_scoped)["session_id"]
                    scoped_first = await session.call_tool("read_context_session", {"session_id": scoped_handle, "request": scoped_request})
                    scoped_id = structured(scoped_first)["result_id"]
                    scoped_warm = await session.call_tool("read_context_session", {"session_id": scoped_handle,
                        "request": scoped_request, "if_result_id": scoped_id})
                    assert structured(scoped_warm)["state"] == "unchanged"
                    await session.call_tool("close_context_session", {"session_id": scoped_handle})
                with probe.step("invalid"):
                    for bad in ({"protocol": "future", "budget_tokens": 10000},
                                {**req, "tokenizer": "/outside"}, {**req, "budget_tokens": True},
                                {**req, "budget_tokens": 1}):
                        failed = await session.call_tool("build_budgeted_context", {"request": bad})
                        assert failed.isError and structured(failed)["state"] == "error"
                    assert tree(project) == before_reads
                with probe.step("session"):
                    opened = await session.call_tool("open_context_session", {})
                    handle = structured(opened)["session_id"]
                    first = await session.call_tool("read_context_session", {"session_id": handle, "request": request})
                    assert not first.isError and structured(first)["state"] == "full"
                    base_text = text_of(first)
                    api.validate_task_context(base_text, request, counter=ByteCounter())
                    base_id = structured(first)["result_id"]
                    warm = await session.call_tool("read_context_session", {"session_id": handle,
                        "request": request, "if_result_id": base_id})
                    assert structured(warm)["state"] == "unchanged"
                with probe.step("mutation"):
                    path = Path("src/policy.py")
                    original = path.read_bytes()
                    try:
                        path.write_bytes(original.replace(b"= 3", b"= 4"))
                        changed = await session.call_tool("read_context_session", {"session_id": handle,
                            "request": request, "if_result_id": base_id, "delta": True})
                        assert structured(changed)["state"] in {"full", "delta"}
                        if structured(changed)["state"] == "delta":
                            actual = api.apply_task_delta(base_text, json.loads(text_of(changed)), request, counter=ByteCounter())
                        else:
                            actual = api.TaskContext(True, text_of(changed), {})
                        expected = api.build_task_context(request, src_dir=source, wiki_dir=wiki, counter=ByteCounter())
                        assert actual.rendered == expected.rendered
                    finally:
                        path.write_bytes(original)
                with probe.step("close"):
                    closed = await session.call_tool("close_context_session", {"session_id": handle})
                    assert structured(closed)["state"] == "closed"
                    failed = await session.call_tool("read_context_session", {"session_id": handle, "request": request})
                    assert failed.isError


if mode == "mcp":
    asyncio.run(transport("stdio"))
    asyncio.run(transport("http"))
print(json.dumps({"sdk": "verified" if mode == "mcp" else "not-used",
    "task_facts": 2, "canonical_cli_parity": True, "read_only": True,
    "edit_and_behavior": True, "semantic_note_preserved": True, "resume_detects_drift": True,
    "cold_resume": True, "sharded_migration": True, "scoped_task_v2": True,
    "real_model_execution": False}, sort_keys=True))
