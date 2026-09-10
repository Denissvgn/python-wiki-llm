"""Bounded observations for the second forensic report; not a bug-free gate.

Run with the project virtual environment. Only generated temporary fixtures
are written or executed. Application sources from the report are not imported,
and no external services or language helpers are required.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services.api_contracts import (
    attach_routes_to_entry_points,
    build_static_api_contracts,
)
from llm_wiki_cli.services.bootstrap_runtime import _generate_load_order_md
from llm_wiki_cli.services.dependencies import (
    build_dependency_graph,
    build_dependency_observations,
    detect_cycles,
    topological_order,
)
from llm_wiki_cli.services.entrypoints import build_flow, get_entry_points
from llm_wiki_cli.services.extraction_service import (
    resolve_call_edges,
    resolve_call_observations,
)
from llm_wiki_cli.services.imports import build_module_path_resolver, _suffix_candidates
from llm_wiki_cli.services.knowledge_artifacts import (
    KnowledgeArtifactError,
    _validate_surface_flow_routes,
)

ROOT = Path(__file__).resolve().parents[1]


def write_sources(root, sources):
    for name, source in sources.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")


def inventory(sources):
    with TemporaryDirectory(prefix="wiki-report-source-") as directory:
        root = Path(directory)
        write_sources(root, sources)
        return PythonExtractor().extract(
            str(root), source_files=sorted(sources), deep=True, include_empty=True
        )


def cli(root, args):
    completed = subprocess.run(
        [sys.executable, "-c", "from llm_wiki_cli.cli import main; main()", *args],
        cwd=str(root),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=90,
    )
    return {
        "exit_code": completed.returncode,
        "stderr": completed.stderr.strip().replace(str(root), "<fixture>"),
    }


def route_source(dynamic):
    route = 'f"{PREFIX}/items"' if dynamic else '"/v1/items"'
    return (
        'from fastapi import FastAPI\napp = FastAPI()\nPREFIX = "/v1"\n'
        "@app.get(" + route + ")\n"
        '@app.get("/items", include_in_schema=False)\n'
        "def items():\n    return []\n"
    )


def artifact_hashes(wiki):
    names = (
        ".llm-wiki-surface.json",
        ".llm-wiki-knowledge.json",
        ".llm-wiki-manifest.json",
    )
    return {
        name: hashlib.sha256((wiki / name).read_bytes()).hexdigest()
        for name in names
        if (wiki / name).is_file()
    }


def wiki_hashes(wiki):
    return {
        path.relative_to(wiki).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in wiki.rglob("*")
        if path.is_file()
    }


def probe_routes():
    inv = inventory({"app.py": route_source(True)})
    contracts = build_static_api_contracts(inv)
    entries = attach_routes_to_entry_points(get_entry_points(inv), contracts)
    routes = next((entry["routes"] for entry in entries if entry.get("routes")), [])
    try:
        _validate_surface_flow_routes(routes, "surface_index.flows[0].routes")
    except KnowledgeArtifactError as exc:
        validation = {"field": exc.field, "message": exc.message}
    else:
        validation = None

    boot = [
        "bootstrap",
        "--src-dir",
        "src",
        "--wiki-dir",
        "wiki",
        "--source-adapter",
        "--skip-workflows",
        "--skip-data-flow",
        "--skip-dependencies",
    ]
    with TemporaryDirectory(prefix="wiki-report-route-") as directory:
        root = Path(directory)
        subprocess.run(
            ["git", "init", "-q", str(root)], check=True, capture_output=True
        )
        cases = {}
        for name, dynamic, api_contracts in (
            ("literal", False, True),
            ("dynamic", True, True),
            ("dynamic_without_api_page", True, False),
        ):
            case = root / name
            write_sources(case, {"src/app.py": route_source(dynamic)})
            result = cli(case, boot + (["--api-contracts"] if api_contracts else []))
            result["committed_artifacts"] = sorted(artifact_hashes(case / "wiki"))
            result["generated_markdown_count"] = len(
                list((case / "wiki").rglob("*.md"))
            )
            cases[name] = result
        case = root / "literal"
        before = artifact_hashes(case / "wiki")
        before_wiki = wiki_hashes(case / "wiki")
        assert cases["literal"]["exit_code"] == 0, cases["literal"]
        assert len(before) == 3, before
        write_sources(case, {"src/app.py": route_source(True)})
        sync = cli(
            case,
            [
                "sync",
                "--src-dir",
                "src",
                "--wiki-dir",
                "wiki",
                "--rebuild-knowledge",
                "--no-cache",
                "--force",
                "--jobs",
                "1",
            ],
        )
        after_wiki = wiki_hashes(case / "wiki")
        sync["prior_trio_bytes_preserved"] = artifact_hashes(case / "wiki") == before
        sync["prior_wiki_bytes_preserved"] = after_wiki == before_wiki
        sync["changed_wiki_paths"] = sorted(
            path
            for path in set(before_wiki) | set(after_wiki)
            if before_wiki.get(path) != after_wiki.get(path)
        )

    return {
        "operation_paths": [operation["path"] for operation in contracts["operations"]],
        "operation_unknowns": [
            operation["unknowns"] for operation in contracts["operations"]
        ],
        "attached_routes": routes,
        "surface_validation_error": validation,
        "bootstrap_cases": cases,
        "sync_from_valid_baseline": sync,
    }


def call_outcomes(
    sources, caller="service_a/permissions.py", symbol="permissions", name="set"
):
    inv = inventory(sources)
    edges = resolve_call_edges(inv)
    observations = resolve_call_observations(inv)["observations"]
    def pick(items):
        return next(
            item
            for item in items
            if item["from"] == {"file": caller, "symbol": symbol}
            and item["name"] == name
        )

    flow = build_flow(
        {
            "id": "api-" + symbol,
            "category": "api",
            "file": caller,
            "symbol": symbol,
            "label": symbol,
        },
        edges,
    )
    return {
        "legacy_edge": pick(edges),
        "detailed_observation": pick(observations),
        "modules_touched": flow["modules_touched"],
    }


def probe_calls():
    definitions = {
        "service_a/permissions.py": "def permissions():\n    return set()\n",
        "service_b/cache.py": "def set(key, value):\n    return len(key)\n",
    }
    baseline = call_outcomes(
        {"service_a/permissions.py": definitions["service_a/permissions.py"]}
    )
    collided = call_outcomes(definitions)
    local = call_outcomes(
        {
            **definitions,
            "service_a/permissions.py": "def set():\n    return 1\ndef permissions():\n    return set()\n",
        }
    )
    imported = call_outcomes(
        {
            "app.py": "from cache import set\ndef run():\n    return set('key', 1)\n",
            "cache.py": definitions["service_b/cache.py"],
        },
        "app.py",
        "run",
    )
    unknown = call_outcomes(
        {
            "app.py": "def run():\n    return helper()\n",
            "unrelated/helper.py": "def helper():\n    return 1\n",
        },
        "app.py",
        "run",
        "helper",
    )
    external = call_outcomes(
        {
            "app.py": "from external_sdk import Client\ndef run():\n    return Client()\n",
            "unrelated/models.py": "class Client: pass\n",
        },
        "app.py",
        "run",
        "Client",
    )
    return {
        "no_collision_control": baseline,
        "builtin_collision": collided,
        "local_shadow_control": local,
        "imported_shadow_control": imported,
        "unbound_nonbuiltin_variant": unknown,
        "external_import_variant": external,
    }


def probe_imports():
    sources = {
        "service_a/utils/logging.py": "import logging\ndef a(): return logging.getLogger(__name__)\n",
        "service_b/utils/logging.py": "import logging\ndef b(): return logging.getLogger(__name__)\n",
        "service_a/api.py": "import logging\ndef ready(): return True\n",
    }
    inv = inventory(sources)
    resolver = build_module_path_resolver(inv)
    graph = build_dependency_graph(inv)
    cycles = detect_cycles(graph, import_time_only=True)
    observations = build_dependency_observations(inv)["observations"]
    order = topological_order(graph, import_time_only=True)
    markdown = _generate_load_order_md(
        {"load_order": order, "side_effects": {"side_effects": [], "factories": []}}
    )
    shadow_inv = inventory(
        {"logging.py": "MARKER = 'local'\n", "app.py": "import logging\n"}
    )
    with TemporaryDirectory(prefix="wiki-report-shadow-") as directory:
        root = Path(directory)
        write_sources(root, {"logging.py": "MARKER = 'local'\n"})
        shadow = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                "import sys; sys.path.insert(0, sys.argv[1]); import logging; print(logging.MARKER)",
                str(root),
            ],
            check=True,
            text=True,
            capture_output=True,
            timeout=10,
        ).stdout.strip()
    return {
        "stdlib_import_candidates": sorted(
            resolver.candidates("logging", "service_a/api.py")
        ),
        "absolute_suffix_candidates": sorted(
            resolver.candidates("utils.logging", "service_a/api.py")
        ),
        "relative_import_control": sorted(
            resolver.candidates(".logging", "service_a/utils/consumer.py")
        ),
        "suffix_expansion": sorted(_suffix_candidates("service_b/utils/logging")),
        "import_time_edges": graph["import_time_edges"],
        "runtime_cycles": cycles,
        "api_logging_observation": next(
            item for item in observations if item["source_path"] == "service_a/api.py"
        ),
        "indeterminate_cycle_group_rendered": "## Indeterminate (cyclic) groups"
        in markdown,
        "top_level_shadow_control": sorted(
            build_module_path_resolver(shadow_inv).candidates("logging", "app.py")
        ),
        "top_level_shadow_runtime_marker": shadow,
    }


def main():
    report = ROOT / "reports/agent_verification_findings_report_20260910_120000.md"
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(ROOT),
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    results = {
        "source_revision": revision,
        "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest()
        if report.is_file()
        else None,
        "python": platform.python_version(),
        "platform": sys.platform,
        "scope": "synthetic bounded fixtures; no external application execution",
        "findings": {
            "FINDING-01": probe_routes(),
            "FINDING-02": probe_calls(),
            "FINDING-03": probe_imports(),
        },
        "report_table_check": {
            "row_sample_sum": 6 * 4 + 3 + 7 * 5 + 3 + 1 + 1 + 2 + 2,
            "reported_sample_total": 64,
            "row_clean_sum": 6 * 4 + 3 + 5 + 7 + 5 + 7 + 7 + 1 + 1 + 1 + 2 + 2,
            "reported_clean_total": 58,
        },
    }
    print(json.dumps(results, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
