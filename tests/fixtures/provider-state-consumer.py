"""Supplemental installed consumer for legacy inputs and native state boundaries."""

from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager
import hashlib
from importlib.metadata import distribution
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from typing import Any, Iterator, TypedDict

from llm_wiki_cli import api


STATES = {
    "valid": "ready", "empty-selection": "ready", "absent": "workspace-state-error",
    "surface-only": "absent", "declared-missing": "degraded",
    "malformed": "degraded", "unsupported": "unsupported", "mixed": "degraded",
    "corrupt-surface": "artifact-integrity-error",
    **{f"legacy-manifest-v{v}": "absent" for v in (1, 2, 3, 4)},
}
TARGET = "llm-wiki://entities/Item"


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def tree(root):
    return {p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mode)
            for p in root.rglob("*") if p.is_file()}


def run(arguments, *, data=None, expected=0):
    result = subprocess.run([sys.executable, "-X", "utf8", "-I", "-m", "llm_wiki_cli.cli", *arguments],
                            input=data, capture_output=True, timeout=180, check=False,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"})
    assert result.returncode == expected, result.stderr.decode(errors="replace")
    return result.stderr if expected else result.stdout


class Roots(TypedDict):
    src_dir: str
    wiki_dir: str


def options(root) -> Roots:
    return {"src_dir": str(root / "src"), "wiki_dir": str(root / "wiki")}


def build_cases(root):
    original = root / "template"
    (original / "src").mkdir(parents=True)
    (original / "src/item.py").write_text(
        "raise RuntimeError('target application must never execute')\n\n"
        "class Item:\n    value: int\n    label: str\n\n"
        "    def render(self, prefix: str = '') -> str:\n        return prefix + self.label\n",
        encoding="utf-8")
    api.bootstrap_wiki(str(original / "src"), str(original / "wiki"))
    foreign = root / "foreign"
    (foreign / "src").mkdir(parents=True)
    (foreign / "src/other.py").write_text("class Other:\n    pass\n", encoding="utf-8")
    api.bootstrap_wiki(str(foreign / "src"), str(foreign / "wiki"))
    cases = {}
    for name in STATES:
        case = root / name
        shutil.copytree(original, case)
        wiki = case / "wiki"
        knowledge = wiki / ".llm-wiki-knowledge.json"
        manifest = wiki / ".llm-wiki-manifest.json"
        if name == "absent":
            shutil.rmtree(wiki)
            wiki.mkdir()
            (wiki / "index.md").write_text("# Plain documentation\n", encoding="utf-8")
        elif name == "surface-only" or name.startswith("legacy-manifest"):
            knowledge.unlink()
            manifest.unlink()
            if name.startswith("legacy-manifest"):
                manifest.write_bytes(canonical({"version": int(name[-1]), "sources": {}}))
        elif name == "declared-missing":
            knowledge.unlink()
        elif name == "malformed":
            knowledge.write_bytes(b"{broken")
        elif name == "unsupported":
            payload = json.loads(knowledge.read_bytes())
            payload["schema_version"] = "llm-wiki-knowledge/v999"
            knowledge.write_bytes(canonical(payload))
        elif name == "mixed":
            shutil.copyfile(foreign / "wiki/.llm-wiki-knowledge.json", knowledge)
        elif name == "corrupt-surface":
            (wiki / ".llm-wiki-surface.json").write_bytes(b"{broken")
        cases[name] = case
    return cases


def bounds(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if {"returned", "total", "truncated"} <= value.keys():
            yield value
        for item in value.values():
            yield from bounds(item)
    elif isinstance(value, list):
        for item in value:
            yield from bounds(item)


@asynccontextmanager
async def sdk(root, transport):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.streamable_http import streamable_http_client
    from datetime import timedelta

    arguments = ["-X", "utf8", "-I", "-m", "llm_wiki_cli.cli", "mcp",
                 "--src-dir", str(root / "src"), "--wiki-dir", str(root / "wiki"), "--transport", transport]
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "NO_PROXY": "*"}
    if transport == "stdio":
        async with stdio_client(StdioServerParameters(command=sys.executable, args=arguments, env=environment)) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=45)) as session:
                await session.initialize()
                yield session
    else:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        with (root / "http-server.log").open("wb") as log:
            server = subprocess.Popen([sys.executable, *arguments, "--host", "127.0.0.1", "--port", str(port)],
                                      stdout=log, stderr=log, env=environment)
            try:
                deadline = time.monotonic() + 30
                while True:
                    assert server.poll() is None, "HTTP server exited before readiness"
                    try:
                        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                            break
                    except OSError:
                        assert time.monotonic() < deadline, "HTTP readiness timeout"
                        await asyncio.sleep(0.1)
                async with streamable_http_client(f"http://127.0.0.1:{port}/mcp") as (read, write, _):
                    async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=45)) as session:
                        await session.initialize()
                        yield session
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=10)


async def check_transport(root, target, expected, transport):
    async with sdk(root, transport) as session:
        result = await session.call_tool("inspect_concept", {"locator_or_exact_route": target, "limit": 1})
        if "error" in expected:
            assert result.isError is True and result.structuredContent is not None
            actual = result.structuredContent["error"]
            assert actual["code"] == expected["error"]["code"]
            assert actual["details"] == expected["error"]["details"]
            assert str(Path.cwd()) not in json.dumps(actual)
        else:
            assert result.isError is False and result.structuredContent == expected
        invalid = await session.call_tool("inspect_concept", {"locator_or_exact_route": target, "limit": 0})
        assert invalid.isError is True
        assert invalid.structuredContent is not None
        error = invalid.structuredContent["error"]
        assert error["code"] == "invalid-request" and error["details"] == {"field": "limit"}
        assert str(Path.cwd()) not in json.dumps(error)
    return {"transport": transport, "parity": True, "safe_error": True,
            "sha256": hashlib.sha256(canonical(expected)).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goldens", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--mode", choices=("base", "mcp"), required=True)
    args = parser.parse_args()
    origin = Path(api.__file__).resolve()
    assert origin.is_relative_to(Path(sys.prefix).resolve())
    dist = distribution("agent-wiki-cli")
    direct_text = dist.read_text("direct_url.json")
    assert direct_text is not None
    direct = json.loads(direct_text)
    assert dist.version == args.version
    assert direct["archive_info"]["hashes"]["sha256"] == args.archive_sha256
    cwd = Path.cwd()
    root = cwd / "state-consumer"
    root.mkdir()
    cases = build_cases(root)
    results = []
    for name, case in cases.items():
        target = "llm-wiki://entities/DoesNotExist" if name == "empty-selection" else TARGET
        frozen = (tree(case / "src"), tree(case / "wiki"))
        try:
            inspection = api.inspect_concept(target, limit=1, **options(case))
        except (api.WorkspaceStateError, api.ArtifactIntegrityError) as error:
            assert name in {"absent", "corrupt-surface"} and error.code == STATES[name]
            assert error.details == {"field": "wiki_dir"} and str(cwd) not in str(error)
            # A native snapshot needs its committed surface. Context auto has
            # a different contract: absent native knowledge permits fallback.
            inspection = {"error": {"code": error.code, "details": error.details}}
            if name == "absent":
                packet = api.build_qualified_context(str(case / "src"), wiki_dir=str(case / "wiki"),
                    request={"budget_tokens": 4000, "focus": ["all"], "format": "json", "filters": {}, "knowledge_mode": "auto"})
                assert packet.to_payload()["response"]["knowledge"]["availability"] == "absent"
            coverage = {"availability": error.code, "freshness_evaluated": False, "counts": None, "reason": "surface-required"}
        else:
            coverage = inspection["coverage"]
        assert coverage["availability"] == STATES[name]
        assert coverage["freshness_evaluated"] is False
        if STATES[name] == "ready":
            assert coverage["counts"] is not None and coverage["counts"]["modeled"] > 0
            assert inspection["concept"]["found"] is (name == "valid")
            if name == "valid":
                limits = list(bounds(inspection))
                assert limits and all(b["returned"] <= 1 <= max(1, b["total"]) for b in limits)
                assert any(b["truncated"] and b["total"] > b["returned"] for b in limits)
        else:
            assert coverage["counts"] is None
            if "concept" in inspection:
                assert inspection["concept"]["found"] is False
        request = {"operation": "concept", "value": target, "limit": 1}
        try:
            expected: dict[str, Any] = dict(api.query_documentation(request, **options(case)))
        except (api.WorkspaceStateError, api.ArtifactIntegrityError) as error:
            assert name in {"absent", "corrupt-surface"} and error.code == STATES[name]
            expected = {"error": {"code": error.code, "details": error.details}}
        raw = run(["query", "--request", "-", "--src-dir", str(case / "src"), "--wiki-dir", str(case / "wiki")],
                  data=canonical(request), expected=1 if name in {"absent", "corrupt-surface"} else 0)
        actual = json.loads(raw)
        if name in {"absent", "corrupt-surface"}:
            assert actual["error"]["code"] == expected["error"]["code"]
            assert actual["error"]["details"] == expected["error"]["details"]
            assert str(cwd) not in json.dumps(actual)
        else:
            assert actual == expected
        transports = []
        if args.mode == "mcp":
            for transport in ("stdio", "http"):
                transports.append(asyncio.run(check_transport(case, target, inspection, transport)))
        assert (tree(case / "src"), tree(case / "wiki")) == frozen and Path.cwd() == cwd
        results.append({"state": name, "availability": coverage["availability"], "reason": coverage["reason"],
                        "counts": coverage["counts"], "found": inspection.get("concept", {}).get("found", False),
                        "api_cli_parity": True, "read_only": True, "sdk": transports})
    goldens = []
    for name in ("context-packet-v1.json", "context-packet-v2.json",
                 "context-packet-v1-pre-bindings.json", "context-packet-v2-pre-bindings.json"):
        raw = (args.goldens / name).read_bytes()
        result = api.validate_context_packet(raw)
        assert result.valid and result.packet.to_bytes() == raw and result.freshness_evaluated is False
        goldens.append({"name": name, "sha256": hashlib.sha256(raw).hexdigest(), "schema": result.packet.to_payload()["schema_version"]})
    future = json.loads((args.goldens / "context-packet-v2.json").read_bytes())
    future["schema_version"] = "llm-wiki-qualified-context-packet/v999"
    try:
        api.validate_context_packet(canonical(future))
    except api.InvalidRequestError as error:
        assert error.code == "unsupported-context-packet" and error.details == {"field": "schema_version"}
        assert "v999" not in str(error) and str(cwd) not in str(error)
    else:
        raise AssertionError("future packet schema accepted")
    legacy = root / "legacy-upgrade"
    shutil.copytree(args.goldens / "knowledge-bootstrap/legacy-bootstrap", legacy)
    assert api.get_knowledge_coverage(src_dir=str(legacy / "source"), wiki_dir=str(legacy / "wiki"))["availability"] == "absent"
    page = legacy / "wiki/entities/User.md"
    prose = "Consumer-owned upgrade note: preserve this paragraph."
    page.write_text(page.read_text(encoding="utf-8").replace("## Description", "## Description\n\n" + prose), encoding="utf-8")
    source_before = tree(legacy / "source")
    run(["sync", "--src-dir", str(legacy / "source"), "--wiki-dir", str(legacy / "wiki"), "--force", "--no-plugins"])
    assert api.get_knowledge_coverage(src_dir=str(legacy / "source"), wiki_dir=str(legacy / "wiki"))["availability"] == "ready"
    assert prose in page.read_text(encoding="utf-8") and tree(legacy / "source") == source_before
    print(json.dumps({"status": "pass", "version": dist.version, "archive_sha256": args.archive_sha256,
        "origin": str(origin), "prefix": sys.prefix, "mode": args.mode, "states": results, "goldens": goldens,
        "future_packet_rejected": True,
        "legacy_upgrade": {"before": "absent", "after": "ready", "source_unchanged": True, "authored_preserved": True}}, indent=2))


if __name__ == "__main__":
    main()
