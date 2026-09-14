"""Replay the native tutorial against an installed wheel or sdist, in isolation."""

import asyncio
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from llm_wiki_cli import api


tutorial = Path(sys.argv[1])
with_sdk = sys.argv[2] == "mcp"
assert Path(api.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
consumer = Path.cwd() / ("native-mcp" if with_sdk else "native-base")
shutil.copytree(
    tutorial / "project",
    consumer,
    ignore=shutil.ignore_patterns(
        ".venv",
        "__pycache__",
        "*.pyc",
        "wiki",
        "output",
        ".git",
    ),
)
os.chdir(consumer)
environment = os.environ.copy()
environment.pop("PYTHONPATH", None)
environment.pop("LLM_WIKI_CACHE_DIR", None)
environment["PYTHONUTF8"] = "1"
environment["PYTHONIOENCODING"] = "utf-8"


def run(command, expected_exit=0):
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-I", *command],
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == expected_exit, (command, result.stdout, result.stderr)
    return result


def tree():
    return {
        p.relative_to(consumer).as_posix(): p.read_bytes()
        for p in consumer.rglob("*")
        if p.is_file()
    }


heading = ""
inside = False
outputs = {}
source = Path("src/catalog.py")
page = Path("wiki/entities/Item.md")
assert "price_cents: int" in source.read_text(encoding="utf-8")
assert "currency:" not in source.read_text(encoding="utf-8")
for line in (tutorial / "README.md").read_text(encoding="utf-8").splitlines():
    if line.startswith("## "):
        heading = line[3:]
    if line.startswith("```"):
        inside = line == "```sh"
        continue
    if not inside or not line.strip():
        continue
    command = shlex.split(line)
    if command[0] == "llm-wiki":
        cli = ["-m", "llm_wiki_cli.cli", *command[1:]]
        expected_exit = 1 if heading == "Change and diagnose" else 0
        completed = run(cli, expected_exit)
        if heading == "Change and diagnose":
            plain = run([item for item in cli if item != "--knowledge-drift-report"], 1)
            report, baseline = json.loads(completed.stdout), json.loads(plain.stdout)
            assert report["issues"] == baseline["issues"]
            assert report["issues"][0]["category"] == "sync_manifest"
            assert report["diagnostics"] and not baseline["diagnostics"]
            assert all(item["severity"] == "warning" for item in report["diagnostics"])
            assert report["knowledge_drift_gate"] is False
    else:
        assert command[:2] == [".venv/bin/python", "client.py"]
        before = tree() if heading == "Read with limited knowledge" else None
        completed = run(command[1:])
        if before is not None:
            assert tree() == before
        if command[2] == "change":
            assert 'currency: str = "EUR"' in source.read_text(encoding="utf-8")
            assert "`currency`" not in page.read_text(encoding="utf-8")
    outputs.setdefault(heading, []).append(completed.stdout)

prepared = json.loads(outputs["Prepare and inspect"][1])
assert prepared["freshness"]["state"] == "current"
assert (
    prepared["coverage"]["counts"]["modeled"]
    == prepared["coverage"]["counts"]["compared"]
    == 2
)
assert json.loads(outputs["Prepare and inspect"][3])["ok"] is True
baseline = json.loads(outputs["Capture a handoff"][1])
assert baseline["intent_matches"] is True
assert baseline["offline_validation"]["freshness"]["evaluated"] is False
assert baseline["live_reconciliation"]["current"] is True
changed = json.loads(outputs["Change and diagnose"][1])
assert changed["freshness"]["state"] == "source-changed"
assert changed["coverage"]["counts"]["modeled_freshness"]["source-changed"] == 1
assert (
    changed["coverage"]["counts"]["modeled_freshness"]["nonsemantic-source-change"] == 1
)
stale = json.loads(outputs["Change and diagnose"][3])
assert stale["offline_validation"]["valid"] is True
assert stale["live_reconciliation"]["current"] is False
assert (
    json.loads(outputs["Review and synchronize"][2])["freshness"]["state"] == "current"
)
assert json.loads(outputs["Review and synchronize"][3])["ok"] is True
assert (
    json.loads(outputs["Review and synchronize"][5])["live_reconciliation"]["current"]
    is True
)
assert "`currency`" in page.read_text(encoding="utf-8")
assert (
    "Currency is explicit; price_cents remains an integer count of minor units."
    in page.read_text(encoding="utf-8")
)
assert (
    json.loads(outputs["Read with limited knowledge"][0])["coverage"][
        "freshness_evaluated"
    ]
    is False
)
assert (
    json.loads(outputs["Read with limited knowledge"][1])["knowledge"]["availability"]
    == "absent"
)
assert not Path("missing-wiki").exists() and not Path("AGENTS.md").exists()

expected = json.loads(Path("expected-request.json").read_text(encoding="utf-8"))
wrong = api.build_qualified_context(
    "src", wiki_dir="wiki", request={**expected, "budget_tokens": 2000}
)
assert api.validate_context_packet(wrong.to_bytes()).valid
Path("output/wrong.packet.json").write_bytes(wrong.to_bytes())
rejected = run(["client.py", "check-packet", "output/wrong.packet.json"], 1)
assert "does not match the consumer" in rejected.stderr and not rejected.stdout


async def native_sdk():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            "-X",
            "utf8",
            "-I",
            "-m",
            "llm_wiki_cli.cli",
            "mcp",
            "--src-dir",
            "src",
            "--wiki-dir",
            "wiki",
            "--transport",
            "stdio",
        ],
        env=environment,
    )
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for live in (False, True):
                for name, args in (
                    (
                        "inspect_concept",
                        {
                            "locator_or_exact_route": "llm-wiki://entities/Item",
                            "live": live,
                        },
                    ),
                    ("get_knowledge_coverage", {"live": live}),
                ):
                    response = await session.call_tool(name, args)
                    assert response.isError is False
                    payload = response.structuredContent or json.loads(
                        next(
                            item.text
                            for item in response.content
                            if item.type == "text"
                        )
                    )
                    assert payload == getattr(api, name)(
                        src_dir="src", wiki_dir="wiki", **args
                    )
            for name in (
                "get_concept",
                "related_concepts",
                "list_concept_sections",
                "traverse_typed_graph",
                "explain_evidence",
                "inspect_concept",
            ):
                response = await session.call_tool(
                    name,
                    {"locator_or_exact_route": "llm-wiki://entities/Item", "limit": 0},
                )
                assert (
                    response.isError is True and response.structuredContent is not None
                )
                error = response.structuredContent["error"]
                assert error["code"] == "invalid-request" and error["details"] == {
                    "field": "limit"
                }
                assert str(consumer) not in json.dumps(error)


before = tree()
if with_sdk:
    asyncio.run(asyncio.wait_for(native_sdk(), timeout=45))
assert tree() == before
print(
    json.dumps(
        {
            "source_grounded_tutorial": True,
            "authored_prose_preserved": True,
            "intent_mismatch_rejected": True,
            "advisory_exit_parity": True,
            "coverage_denominators": {"modeled": 2, "compared": 2},
            "packet_sha256": hashlib.sha256(
                Path("output/context.packet.json").read_bytes()
            ).hexdigest(),
            "sdk": "verified" if with_sdk else "not-used",
        },
        sort_keys=True,
    )
)
