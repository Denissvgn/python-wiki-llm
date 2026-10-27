"""Optional, additive llm-wiki evidence for the trusted selective CI planner.

The controller stays stdlib-only. Analysis executes in an isolated interpreter
with the actual base provider installed; candidate code is input, never imported.
No result from this module permits dropping a mandatory test or owner.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time
import venv
from typing import Callable


SCHEMA = "agent-wiki-pr-ci-impact/v1"
MAX_PATHS = 32
MAX_CONCEPTS = 3
MAX_HINTS = 32
QUERY_LIMIT = 100
MAX_PROVIDER_BYTES = 64 * 1024 * 1024
MAX_PROVIDER_FILES = 2000
WORKER_SECONDS = 90
QUERY_SECONDS = 15
SETUP_SECONDS = 120


def ci_module():
    spec = importlib.util.spec_from_file_location(
        "impact_ci_driver", Path(__file__).with_name("pr_ci.py")
    )
    if spec is None or spec.loader is None:
        raise ValueError("trusted CI driver is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def report(binding: dict, status: str, reason: str) -> dict:
    return {
        "schema": SCHEMA,
        "binding": dict(binding),
        "status": status,
        "advisory": True,
        "complete": False,
        "can_reduce_selection": False,
        "reason": reason,
        "affected_sources": [],
        "citations": [],
        "queries": [],
        "gaps": [],
        "limits": {
            "paths": MAX_PATHS,
            "concept_queries": MAX_CONCEPTS,
            "hops": 1,
            "affected_sources": MAX_HINTS,
            "query_seconds": QUERY_SECONDS,
            "worker_seconds": WORKER_SECONDS,
        },
        "limitations": [
            "Targeted extraction and recorded incoming edges do not establish global live or transitive completeness.",
            "The trusted base/head import and contract selection remains mandatory, including deleted and renamed sources.",
            "No graph match or unchanged structure establishes that a test can be omitted.",
        ],
    }


def availability(value: dict) -> str | None:
    state = value.get("availability")
    return state.get("state") if isinstance(state, dict) else state


def observe(query: Callable[[dict], dict], paths: list[str], binding: dict) -> dict:
    """Use only bounded supported reads; retain uncertainty with every hint."""
    result = report(binding, "observed", "bounded-impact-hints")
    started = time.monotonic()
    ordered = sorted(set(paths))
    selected = ordered[:MAX_PATHS]
    result["path_bounds"] = {
        "total": len(ordered),
        "returned": len(selected),
        "truncated": len(ordered) > len(selected),
    }
    if len(ordered) > len(selected):
        result["gaps"].append(
            {"reason": "path-budget", "omitted": len(ordered) - len(selected)}
        )
    if not selected:
        result.update(status="not-applicable", reason="no-supplied-python-paths")
        return result

    def read(request):
        response = query(request)
        if (
            not isinstance(response, dict)
            or response.get("operation") != request["operation"]
        ):
            raise ValueError("unexpected impact query envelope")
        cost = response.get("cost", {})
        if cost.get("full_inventory_performed") is not False or cost.get(
            "scope"
        ) not in {"targeted-extraction", "snapshot-index-only"}:
            raise ValueError(
                "impact adapter refuses a full-inventory or unknown query scope"
            )
        result["queries"].append(
            {
                "operation": request["operation"],
                "value": request.get("value"),
                **{
                    k: response[k]
                    for k in (
                        "cost",
                        "knowledge",
                        "bounds",
                        "truncated",
                        "limitations",
                        "typed_graph",
                    )
                    if k in response
                },
            }
        )
        if response.get("truncated"):
            result["gaps"].append(
                {
                    "reason": "query-truncated",
                    "operation": request["operation"],
                    "value": request.get("value"),
                }
            )
        return response

    try:
        impact = read(
            {
                "operation": "impact",
                "paths": selected,
                "source_policy": "discovery",
                "limit": QUERY_LIMIT,
            }
        )
        result["source_outcomes"] = impact.get("matches", [])
        knowledge = impact.get("knowledge", {})
        if availability(knowledge) != "ready":
            result["gaps"].append(
                {"reason": "native-knowledge-unavailable", "knowledge": knowledge}
            )
        else:
            priorities = {
                c["locator"]: (
                    0
                    if c.get("page_kind") == "module"
                    or c.get("concept_kind") == "module"
                    else 1
                )
                for c in impact.get("concepts", [])
                if isinstance(c, dict) and isinstance(c.get("locator"), str)
            }
            concepts = sorted(
                priorities, key=lambda locator: (priorities[locator], locator)
            )
            result["concept_bounds"] = {
                "total": len(concepts),
                "returned": 0,
                "truncated": bool(concepts),
            }
            if len(concepts) > MAX_CONCEPTS:
                result["gaps"].append(
                    {
                        "reason": "concept-query-budget",
                        "omitted": len(concepts) - MAX_CONCEPTS,
                    }
                )
            hints = set()
            pending = concepts[:MAX_CONCEPTS]
            for index, locator in enumerate(pending):
                if time.monotonic() - started >= QUERY_SECONDS:
                    result["gaps"].append(
                        {"reason": "query-time-budget", "omitted": len(pending) - index}
                    )
                    break
                result["concept_bounds"]["returned"] += 1
                try:
                    related = read(
                        {
                            "operation": "typed",
                            "value": locator,
                            "direction": "incoming",
                            "kinds": [
                                "imports",
                                "calls",
                                "depends_on",
                                "reads",
                                "writes",
                            ],
                            "include_evidence": False,
                            "limit": QUERY_LIMIT,
                        }
                    )
                    if (
                        availability(related.get("knowledge", {})) != "ready"
                        or related.get("typed_graph", {}).get("availability") != "ready"
                    ):
                        result["gaps"].append(
                            {"reason": "typed-graph-unavailable", "locator": locator}
                        )
                        continue
                    for edge in related.get("edges", []):
                        if not isinstance(edge, dict):
                            raise ValueError("invalid typed edge")
                        if edge.get("resolution") != "resolved":
                            result["gaps"].append(
                                {
                                    "reason": "nonresolved-edge",
                                    "resolution": edge.get("resolution"),
                                    "locator": locator,
                                }
                            )
                            continue
                        concept = edge.get("related_concept")
                        if not isinstance(concept, dict) or not isinstance(
                            concept.get("source_path"), str
                        ):
                            result["gaps"].append(
                                {
                                    "reason": "edge-without-source-owner",
                                    "locator": locator,
                                }
                            )
                            continue
                        source = concept["source_path"]
                        if source not in selected:
                            hints.add(source)
                            result["citations"].append(
                                {
                                    "source": source,
                                    "via": locator,
                                    "kind": edge.get("kind"),
                                    "related_locator": concept.get("locator"),
                                    "origin": edge.get("origin"),
                                    "coverage": edge.get("coverage"),
                                    "freshness": concept.get("freshness"),
                                    "basis": "recorded-snapshot-relationship",
                                }
                            )
                except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
                    result["gaps"].append(
                        {
                            "reason": "related-query-failed",
                            "locator": locator,
                            "error": type(exc).__name__,
                        }
                    )
            result["concept_bounds"]["truncated"] = result["concept_bounds"][
                "returned"
            ] < len(concepts)
            ordered_hints = sorted(hints)
            result["affected_source_bounds"] = {
                "total": len(hints),
                "returned": min(len(hints), MAX_HINTS),
                "truncated": len(hints) > MAX_HINTS,
            }
            result["affected_sources"] = ordered_hints[:MAX_HINTS]
            if len(hints) > MAX_HINTS:
                result["gaps"].append(
                    {
                        "reason": "affected-source-budget",
                        "omitted": len(hints) - MAX_HINTS,
                    }
                )
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        result.update(status="unavailable", reason="impact-query-failed")
        result["gaps"].append(
            {"reason": "impact-query-failed", "error": type(exc).__name__}
        )
    if result["status"] == "observed" and result["gaps"]:
        result["status"] = "partial"
    return result


def freeze_provider(ci, root: Path, base: str, destination: Path) -> dict:
    """Materialize only base-owned package/build inputs, never candidate Python."""
    ci.require(
        not destination.exists(), "refuse to overwrite an impact provider snapshot"
    )
    catalog = ci.tree(root, base)
    build_files = {
        "pyproject.toml",
        "release_build_backend.py",
        "README.md",
        "LICENSE",
        "MANIFEST.in",
    }
    paths = sorted(
        p for p in catalog if p.startswith("src/llm_wiki_cli/") or p in build_files
    )
    ci.require(
        0 < len(paths) <= MAX_PROVIDER_FILES, "provider file count exceeds limit"
    )
    inputs = {}
    total = 0
    for path in paths:
        raw = ci.git(root, "show", base + ":" + path)
        total += len(raw)
        ci.require(
            total <= MAX_PROVIDER_BYTES and len(raw) <= ci.MAX_JSON,
            "provider snapshot byte limit exceeded",
        )
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        inputs[path] = ci.digest(raw)
    python = {
        p.removeprefix("src/llm_wiki_cli/"): sha
        for p, sha in inputs.items()
        if p.startswith("src/llm_wiki_cli/") and p.endswith(".py")
    }
    ci.require(
        python and "src/llm_wiki_cli/services/analysis_contracts.json" in inputs,
        "base provider is incomplete",
    )
    return {
        "base_sha": base,
        "base_tree": ci.git(root, "rev-parse", base + "^{tree}").decode().strip(),
        "source_inputs_sha256": ci.digest(ci.canonical(inputs)),
        "python_files": python,
        "source_selection_sha256": ci.digest(
            ci.git(root, "show", base + ":.llm-wiki/source-selection.json")
        ),
        "analysis_contracts_sha256": inputs[
            "src/llm_wiki_cli/services/analysis_contracts.json"
        ],
    }


def clean_environment() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key
        not in {"PYTHONPATH", "GITHUB_TOKEN", "GH_TOKEN", "RELEASE_AUTOMATION_TOKEN"}
    }


def collect(
    ci,
    root: Path,
    directory: Path,
    binding: dict,
    rows: list[dict],
    work: Path,
    provider_python: Path | None = None,
) -> dict:
    paths = sorted(
        {p for row in rows for p in (row["old"], row["path"]) if p.endswith(".py")}
    )
    if not paths:
        return report(binding, "not-applicable", "no-supplied-python-paths")
    try:
        ci.require(not work.exists(), "refuse to overwrite impact evidence")
        work.mkdir(parents=True)
        provider_source = work / "provider-source"
        provider = freeze_provider(ci, root, binding["base_sha"], provider_source)
        interpreter = provider_python
        if interpreter is None:
            environment = work / ".venv"
            venv.EnvBuilder(with_pip=True).create(environment)
            interpreter = environment / (
                "Scripts/python.exe" if os.name == "nt" else "bin/python"
            )
            commands = [
                [
                    str(interpreter),
                    "-m",
                    "pip",
                    "install",
                    "--require-hashes",
                    "--only-binary=:all:",
                    "-r",
                    str(directory / "pr-ci-impact-requirements.txt"),
                ],
                [
                    str(interpreter),
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--no-deps",
                    "--no-build-isolation",
                    str(provider_source),
                ],
            ]
            with (work / "provider-setup.log").open("wb") as log:
                for command in commands:
                    done = subprocess.run(
                        command,
                        env=clean_environment(),
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        timeout=SETUP_SECONDS,
                        check=False,
                    )
                    ci.require(
                        done.returncode == 0, "trusted impact provider setup failed"
                    )
        request = {
            "schema": SCHEMA,
            "binding": binding,
            "provider": provider,
            "root": str(root.resolve()),
            "paths": paths,
            "wiki_dir": "docs/llm_wiki",
            "source_selection": ".llm-wiki/source-selection.json",
        }
        request_path, response_path = work / "request.json", work / "response.json"
        ci.write_json(request_path, request)
        with (work / "worker.log").open("wb") as log:
            done = subprocess.run(
                [
                    str(interpreter),
                    "-I",
                    str(directory / "pr_ci_impact.py"),
                    "worker",
                    "--request",
                    str(request_path),
                    "--output",
                    str(response_path),
                ],
                cwd=root,
                env=clean_environment(),
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=WORKER_SECONDS,
                check=False,
            )
        ci.require(done.returncode == 0, "trusted impact worker did not succeed")
        result = ci.read_json(response_path)
        ci.require(
            result.get("schema") == SCHEMA
            and result.get("binding") == binding
            and result.get("advisory") is True
            and result.get("can_reduce_selection") is False,
            "impact result identity or authority differs",
        )
        return result
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as exc:
        result = report(
            binding, "unavailable", "trusted-provider-or-worker-unavailable"
        )
        result["gaps"] = [
            {
                "reason": "trusted-provider-or-worker-unavailable",
                "error": type(exc).__name__,
            }
        ]
        return result


def worker(ci, request: dict) -> dict:
    ci.require(request.get("schema") == SCHEMA, "unknown impact request")
    # -I and an installed package ensure no candidate source is imported.
    spec = importlib.util.find_spec("llm_wiki_cli")
    ci.require(
        spec is not None and spec.origin is not None, "installed base provider missing"
    )
    if spec is None or spec.origin is None:
        raise ValueError("installed base provider missing")
    package = Path(spec.origin).parent
    ci.require(
        package.is_relative_to(Path(sys.prefix)),
        "impact provider must be installed noneditably in its interpreter",
    )
    expected = request["provider"]
    actual = {
        p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in package.rglob("*.py")
    }
    ci.require(
        actual == expected["python_files"],
        "installed provider Python bytes differ from trusted base",
    )
    ci.require(
        ci.digest((package / "services/analysis_contracts.json").read_bytes())
        == expected["analysis_contracts_sha256"],
        "provider analysis registry differs",
    )
    root = Path(request["root"])
    ci.require(
        ci.git(root, "rev-parse", "HEAD").decode().strip()
        == request["binding"]["candidate_sha"]
        and ci.git(root, "rev-parse", "HEAD^{tree}").decode().strip()
        == request["binding"]["candidate_tree"],
        "impact checkout differs",
    )
    if (
        ci.digest(ci.bounded_file(root / request["source_selection"], ci.MAX_JSON))
        != expected["source_selection_sha256"]
    ):
        result = report(request["binding"], "unavailable", "source-selection-changed")
        result["gaps"].append(
            {"reason": "source-selection-changed", "scope_widened": False}
        )
        return result
    from llm_wiki_cli.api import query_documentation

    result = observe(
        lambda query: dict(
            query_documentation(
                query,
                src_dir=str(root),
                wiki_dir=str(root / request["wiki_dir"]),
                source_selection=request["source_selection"],
                allow_external_src=True,
            )
        ),
        request["paths"],
        request["binding"],
    )
    ci.require(
        ci.git(root, "status", "--porcelain", "--untracked-files=no").strip() == b"",
        "impact read modified tracked inputs",
    )
    result["provider"] = {
        k: expected[k] for k in ("base_sha", "base_tree", "source_inputs_sha256")
    }
    result["provider"].update(
        {
            "python_files_verified": len(actual),
            "origin": str(package),
            "python": sys.version.split()[0],
            "editable": False,
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["worker"])
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ci = ci_module()
    try:
        ci.write_json(args.output, worker(ci, ci.read_json(args.request)))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("Impact worker refused: " + type(exc).__name__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
