"""Bounded observations for the 17:45 forensic report, not a bug-free gate.

Run with .venv/bin/python. Only temporary fixtures are written; optional
reported source is parsed, never imported or executed. Commands run serially.
The optional helper cache must already be prepared; no downloads are made.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from llm_wiki_cli.cli import main as cli_main
from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services import bootstrap_runtime
from llm_wiki_cli.services.data_flow import analyze_data_flow
from llm_wiki_cli.services.entrypoints import build_flow
from llm_wiki_cli.services.extraction_service import (
    resolve_call_edges,
    resolve_call_observations,
)
from llm_wiki_cli.services.extractor_helpers import resolve_helper_cache_root


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(source):
    with TemporaryDirectory(prefix="wiki-label-source-") as directory:
        root = Path(directory)
        (root / "builder.py").write_bytes(source)
        return PythonExtractor().extract(
            str(root), source_files=["builder.py"], deep=True, include_empty=True
        )


def observe_flow(inventory, symbol):
    entry = {
        "id": "api-" + symbol,
        "category": "api",
        "file": "builder.py",
        "symbol": symbol,
        "label": symbol,
    }
    edges = resolve_call_edges(inventory)
    flow = build_flow(entry, edges)
    data = analyze_data_flow(inventory, flow, edges)
    markdown = bootstrap_runtime._generate_flow_md(flow, data_flow=data)
    function = next(
        item for item in inventory["builder.py"]["functions"] if item["name"] == symbol
    )
    diagrams = re.findall(r"```mermaid\n(.*?)\n```", markdown, flags=re.DOTALL)
    return {
        "raw_calls": function["calls"],
        "call_bindings": function.get("call_bindings"),
        "edges": [edge for edge in edges if edge["from"]["symbol"] == symbol],
        "observations": [
            item
            for item in resolve_call_observations(inventory)["observations"]
            if item["from"]["symbol"] == symbol
        ],
        "diagrams": diagrams,
        "diagrams_show_build_method": any(".build" in item for item in diagrams),
        "evidence_table_retains_build_method": ").build"
        in markdown.split("### Call data", 1)[-1],
        "participant_count": sum(
            "participant p" in line for line in diagrams[0].splitlines()
        ),
    }


def label_cases():
    arguments = ", ".join(f"configuration_option_{n}=value_{n}" for n in range(9))
    source = (
        "class Builder:\n"
        "    def build(self):\n        return None\n"
        "    def finish(self):\n        return None\n\n"
        f"def long_chain():\n    return Builder({arguments}).build()\n\n"
        "def short_chain():\n    return Builder().build()\n\n"
        f"def factory_chain(factory):\n    return factory({arguments}).build()\n\n"
        f"def distinct_methods():\n    Builder({arguments}).build()\n"
        f"    Builder({arguments}).finish()\n"
    )
    inventory = extract(source.encode("utf-8"))
    return {
        name: observe_flow(inventory, name)
        for name in ("long_chain", "short_chain", "factory_chain", "distinct_methods")
    }


def cli(cwd, arguments):
    stdout, stderr = io.StringIO(), io.StringIO()
    previous = Path.cwd()
    try:
        os.chdir(cwd)
        with (
            patch.object(sys, "argv", ["llm-wiki", *arguments]),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            try:
                cli_main()
            except SystemExit as exc:
                code = exc.code
            else:
                code = 0
    finally:
        os.chdir(previous)
    return {"exit_code": code, "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}


def doctor(cwd, source):
    result = cli(
        cwd,
        [
            "doctor",
            "--src-dir",
            str(source),
            "--wiki-dir",
            "wiki",
            "--allow-external-src",
            "--jobs",
            "1",
            "--format",
            "json",
        ],
    )
    payload = json.loads(result["stdout"])
    return {
        key: payload[key]
        for key in (
            "exit_code",
            "status",
            "availability",
            "freshness",
            "snapshot_parity",
            "drift",
            "degraded_reasons",
            "unhealthy_reasons",
        )
    }


def command_cases(root, helper_cache):
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    caller, output, source = (root / name for name in ("caller", "output", "source"))
    for path in (caller, output, source):
        path.mkdir()
    app = source / "app.py"
    app.write_text("class Session:\n    pass\n", encoding="utf-8")
    initial_source_hash = digest(app)
    boot = [
        "bootstrap",
        "--src-dir",
        str(source),
        "--wiki-dir",
        str(output / "wiki"),
        "--source-adapter",
        "--allow-external-src",
        "--skip-workflows",
    ]
    rejected = cli(caller, boot)
    rejected["output_created"] = (output / "wiki").exists()
    accepted = cli(output, boot)
    assert accepted["exit_code"] == 0, accepted
    health = doctor(output, source)
    path_case = {
        "from_unrelated_cwd": rejected,
        "from_output_workspace": accepted,
        "doctor_from_output_workspace": health,
        "source_bytes_unchanged": digest(app) == initial_source_hash,
    }

    cache = root / "isolated-helper-cache"
    cache_case = {
        "unsupported_flag": cli(
            caller,
            [
                "context",
                "--budget",
                "8000",
                "--helper-cache-dir",
                str(cache),
            ],
        ),
        "environment_selection": str(
            resolve_helper_cache_root(
                source,
                env={"LLM_WIKI_CACHE_DIR": str(cache)},
            )
        ),
    }
    if helper_cache is not None:
        polyglot = root / "polyglot"
        polyglot.mkdir()
        (polyglot / "example.ts").write_text(
            "export function hello(name: string) { return name; }\n", encoding="utf-8"
        )
        with patch.dict(os.environ, {"LLM_WIKI_CACHE_DIR": str(helper_cache)}):
            cache_case["prepared_environment_context"] = cli(
                polyglot,
                [
                    "context",
                    "--src-dir",
                    ".",
                    "--budget",
                    "8000",
                    "--focus",
                    "all",
                    "--format",
                    "json",
                    "--read-only",
                ],
            )

    # Deterministic mutation after inventory capture and before publication.
    # No timing race or background writer is required for this observation.
    race = root / "drift"
    race.mkdir()
    boot[boot.index("--wiki-dir") + 1] = str(race / "wiki")
    real_inventory = bootstrap_runtime.get_inventory_result
    mutations = []

    def mutate_after_inventory(*args, **kwargs):
        result = real_inventory(*args, **kwargs)
        app.write_text(
            "class Session:\n    pass\n\n# formatting note\n", encoding="utf-8"
        )
        mutations.append({"before": initial_source_hash, "after": digest(app)})
        return result

    with patch.object(
        bootstrap_runtime, "get_inventory_result", mutate_after_inventory
    ):
        drift_bootstrap = cli(race, boot)
    assert drift_bootstrap["exit_code"] == 0, drift_bootstrap
    drift_health = doctor(race, source)
    pages = {
        str(path.relative_to(race / "wiki")): (digest(path), path.stat().st_mtime_ns)
        for surface in ("modules", "entities", "flows", "workflows")
        for path in (race / "wiki" / surface).glob("*.md")
    }
    sync = cli(
        race,
        [
            "sync",
            "--src-dir",
            str(source),
            "--wiki-dir",
            "wiki",
            "--allow-external-src",
            "--jobs",
            "1",
            "--no-plugins",
        ],
    )
    recovered = doctor(race, source)
    return {
        "output_path_policy": path_case,
        "context_cache": cache_case,
        "in_flight_drift": {
            "mutation_after_inventory": mutations,
            "bootstrap": drift_bootstrap,
            "doctor_before_sync": drift_health,
            "sync": sync,
            "doctor_after_sync": recovered,
            "content_page_bytes_and_mtimes_preserved": all(
                before
                == (
                    digest(race / "wiki" / name),
                    (race / "wiki" / name).stat().st_mtime_ns,
                )
                for name, before in pages.items()
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reported-source", type=Path)
    parser.add_argument("--reported-flow", type=Path)
    parser.add_argument("--helper-cache-dir", type=Path)
    args = parser.parse_args()
    result = {"python": platform.python_version(), "labels": label_cases()}
    with TemporaryDirectory(prefix="wiki-report-174500-") as directory:
        root = Path(directory)
        with patch.dict(os.environ, {"LLM_WIKI_CACHE_DIR": str(root / "cache")}):
            result.update(command_cases(root, args.helper_cache_dir))
        normalized = json.dumps(result, ensure_ascii=False).replace(
            str(root), "<fixture>"
        )
        result = json.loads(normalized)
    if args.reported_source is not None:
        before = digest(args.reported_source)
        result["reported_source"] = {
            "path": str(args.reported_source),
            "sha256": before,
            "flow": observe_flow(
                extract(args.reported_source.read_bytes()), "build_recovery_report"
            ),
            "source_bytes_unchanged": digest(args.reported_source) == before,
        }
    if args.reported_flow is not None:
        result["reported_flow"] = {
            "path": str(args.reported_flow),
            "sha256": digest(args.reported_flow),
            "diagrams": re.findall(
                r"```mermaid\n(.*?)\n```",
                args.reported_flow.read_text(encoding="utf-8"),
                flags=re.DOTALL,
            ),
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
