"""Standalone installed-distribution packet parity probe (no checkout imports)."""

import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from llm_wiki_cli import api


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode()


def tree_bytes(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


source, wiki = (Path(value) for value in sys.argv[1:3])
with_sdk = sys.argv[3] == "mcp"
before = (tree_bytes(source), tree_bytes(wiki))
async def sdk_parity(expected):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-X", "utf8", "-I", "-m", "llm_wiki_cli.cli", "mcp",
              "--src-dir", str(source), "--wiki-dir", str(wiki), "--transport", "stdio"],
    )
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for arguments, raw, identity in expected:
                response = await session.call_tool("get_context_packet", arguments)
                assert response.isError is False
                content = response.structuredContent or json.loads(next(
                    item.text for item in response.content if item.type == "text"
                ))
                assert canonical(content["packet"]) == raw
                assert content["packet_id"] == identity
            response = await session.call_tool("get_context_packet", {"budget_tokens": 0})
            assert response.isError is True
            assert response.structuredContent is not None
            assert response.structuredContent["error"]["code"] == "invalid-request"
            assert str(Path.cwd()) not in json.dumps(response.structuredContent)


cases = {}
expected_mcp = []
for version in (1, 2):
    for format in ("json", "markdown"):
        label = f"v{version}-{format}"
        request = {"protocol": f"llm-wiki-context/v{version}", "budget_tokens": 2000,
                   "focus": ["all"], "format": format,
                   "filters": {"module": "app/service"}}
        if version == 2:
            request["knowledge_mode"] = "auto"
        request_path = Path.cwd() / f"packet-request-{label}.json"
        request_path.write_bytes(canonical(request))
        packet = api.build_qualified_context(str(source), str(wiki), request)
        if format == "json":
            assert "app/service.py" in packet.to_payload()["response"]["files"]
        else:
            assert "app/service.py" in json.dumps(packet.to_payload()["response"])
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "-I", "-m", "llm_wiki_cli.cli", "context",
             "--src-dir", str(source), "--wiki-dir", str(wiki),
             "--request", str(request_path), "--format", "packet", "--read-only"],
            capture_output=True, check=True, timeout=30,
        )
        assert result.stdout == packet.to_bytes()
        assert api.validate_context_packet(result.stdout).packet_id == packet.packet_id
        if with_sdk:
            arguments = {"budget_tokens": 2000, "focus": ["all"], "format": format,
                         "filters": request["filters"]}
            if version == 2:
                arguments["knowledge_mode"] = "auto"
            expected_mcp.append((arguments, packet.to_bytes(), packet.packet_id))
        cases[label] = hashlib.sha256(packet.to_bytes()).hexdigest()

try:
    api.validate_context_packet(b"invalid")
except api.InvalidRequestError as error:
    assert error.code == "malformed-context-packet" and error.details
else:
    raise AssertionError("Malformed packet was accepted.")
if with_sdk:
    asyncio.run(asyncio.wait_for(sdk_parity(expected_mcp), timeout=45))
assert (tree_bytes(source), tree_bytes(wiki)) == before
print(json.dumps({"cases": cases, "read_only": True, "structured_errors": True,
                  "sdk": "verified" if with_sdk else "not-used"}, sort_keys=True))
