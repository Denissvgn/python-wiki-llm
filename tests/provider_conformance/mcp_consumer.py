"""Actual installed SDK transport comparison against a frozen public capture."""

import asyncio
import hashlib
from importlib.metadata import distribution
import json
import os
from pathlib import Path
import sys

from llm_wiki_cli import api
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    config = json.loads(Path(sys.argv[1]).read_text())
    assert Path(api.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    origin = json.loads(
        distribution("agent-wiki-cli").read_text("direct_url.json") or "{}"
    )
    assert (
        origin.get("archive_info", {}).get("hashes", {}).get("sha256")
        == config["artifact_sha256"]
    ), "wrong installed MCP artifact"
    capture = Path(config["capture"])
    output = Path(config["output"])
    output.mkdir(parents=True, exist_ok=True)
    os.environ["LLM_WIKI_CACHE_DIR"] = config["helper_cache"]
    cases = [
        c for c in json.loads((capture / "cases.json").read_text()) if c["adapter"]
    ]
    assert cases, "empty MCP comparison"
    args = [
        "-X",
        "utf8",
        "-I",
        "-m",
        "llm_wiki_cli.cli",
        "mcp",
        "--src-dir",
        config["source"],
        "--wiki-dir",
        config["wiki"],
        "--transport",
        "stdio",
    ]
    records = []
    async with stdio_client(
        StdioServerParameters(command=sys.executable, args=args, env=dict(os.environ))
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for case in cases:
                args = {k: v for k, v in case["request"].items() if k != "protocol"}
                result = await session.call_tool("get_context_packet", args)
                assert not result.isError and result.structuredContent is not None
                raw = (
                    json.dumps(
                        result.structuredContent["packet"],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    )
                    + "\n"
                ).encode()
                assert raw == (capture / case["packet"]).read_bytes()
                (output / case["packet"]).write_bytes(raw)
                records.append(
                    {
                        "case": case["label"],
                        "sha256": hashlib.sha256(raw).hexdigest(),
                        "status": "pass",
                    }
                )
    (output / "result.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "cases": records,
                "installed_module": api.__file__,
                "archive_origin": origin,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(main(), timeout=1200))
