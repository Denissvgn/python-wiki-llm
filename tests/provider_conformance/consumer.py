"""Installed-only capture worker. Imports no private provider service modules."""

from __future__ import annotations

import hashlib
from importlib.metadata import distribution
import json
import os
from pathlib import Path
import subprocess
import sys

from llm_wiki_cli import api


def main():
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    source, wiki, output = (
        Path(config[key]).absolute() for key in ("source", "wiki", "output")
    )
    output.mkdir(parents=True, exist_ok=True)
    assert Path(api.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    origin = json.loads(
        distribution("agent-wiki-cli").read_text("direct_url.json") or "{}"
    )
    assert (
        origin.get("archive_info", {}).get("hashes", {}).get("sha256")
        == config["artifact_sha256"]
    ), "wrong installed artifact"
    os.environ["LLM_WIKI_CACHE_DIR"] = config["helper_cache"]
    if not wiki.exists():
        api.bootstrap_wiki(
            str(source),
            str(wiki),
            helper_cache_dir=config["helper_cache"],
            api_contracts=config.get("api_contracts", False),
        )

    def snapshot(root):
        return {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*")
            if p.is_file() and not p.is_symlink() and ".git" not in p.parts
        }

    def save(name, value):
        (output / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    os.environ["LLM_WIKI_CACHE_DIR"] = config["helper_cache"]
    before = (snapshot(source), snapshot(wiki))
    inventory = api.extract_source(str(source), deep=True, read_only=True)
    save("inventory.json", inventory)
    service = api.build_documentation_query_service(
        str(source),
        wiki_dir=str(wiki),
        helper_cache_dir=config["helper_cache"],
        limit=100,
    )
    surface = json.loads((wiki / ".llm-wiki-surface.json").read_text(encoding="utf-8"))
    knowledge = json.loads(
        (wiki / ".llm-wiki-knowledge.json").read_text(encoding="utf-8")
    )
    save("surface.json", surface)
    save("knowledge.json", knowledge)
    native = {}
    for page in surface["pages"]:
        if page.get("source_path") in config["files"] and page["kind"] in {
            "modules",
            "entities",
        }:
            native[page["mcp_uri"]] = api.get_concept(page["mcp_uri"], service=service)
    save("native.json", native)
    cases, commands = [], []
    for number, path in enumerate(config["files"]):
        for representation in ("json", "markdown"):
            label = f"file-{number}-{representation}"
            request = {
                "protocol": "llm-wiki-context/v2",
                "budget_tokens": 128000,
                "focus": ["all"],
                "format": representation,
                "filters": {
                    "module": str(Path(path).with_suffix("")).replace("\\", "/")
                },
                "knowledge_mode": "auto",
            }
            packet = api.build_qualified_context(
                str(source), wiki_dir=str(wiki), request=request
            )
            raw = packet.to_bytes()
            request_path = output / (label + "-request.json")
            save(request_path.name, request)
            (output / (label + ".json")).write_bytes(raw)
            assert api.validate_context_packet(raw).valid
            if path in config.get("adapter_files", config["files"]):
                argv = [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-I",
                    "-m",
                    "llm_wiki_cli.cli",
                    "context",
                    "--src-dir",
                    str(source),
                    "--wiki-dir",
                    str(wiki),
                    "--request",
                    str(request_path),
                    "--format",
                    "packet",
                    "--read-only",
                ]
                checked = subprocess.run(
                    argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=240
                )
                (output / (label + "-cli.stdout")).write_bytes(checked.stdout)
                (output / (label + "-cli.stderr")).write_bytes(checked.stderr)
                commands.append({"argv": argv, "exit_code": checked.returncode})
                save("commands.json", commands)
                assert checked.returncode == 0, checked.stderr
                assert checked.stdout == raw, "API/CLI bytes differ"
            cases.append(
                {
                    "label": label,
                    "source_path": path,
                    "format": representation,
                    "request": request,
                    "packet": label + ".json",
                    "packet_id": packet.packet_id,
                    "adapter": path in config.get("adapter_files", config["files"]),
                }
            )
            save("cases.json", cases)

    assert before == (snapshot(source), snapshot(wiki)), (
        "consumer capture modified source/wiki"
    )
    save(
        "capture.json",
        {
            "status": "pass",
            "installed_module": api.__file__,
            "prefix": sys.prefix,
            "archive_origin": origin,
            "files": config["files"],
            "cases": len(cases),
            "mcp": bool(config.get("mcp")),
            "source": before[0],
            "wiki": before[1],
        },
    )


if __name__ == "__main__":
    main()
