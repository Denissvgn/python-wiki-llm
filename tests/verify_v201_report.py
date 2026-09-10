"""Bounded observations for the 2026-09-10 report review; no product mutations.

Run from the repository with .venv/bin/python. This records current behavior,
including defects, and is not a regression suite whose success means bug-free.
Temporary source fixtures are deleted on exit. No helper preparation or network
access is needed. The knowledge comparison deliberately replays recorded bases;
it is not a claim to have run a fresh bootstrap or live doctor command.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import platform
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory


from llm_wiki_cli.api_types import ContextKnowledgeResult
from llm_wiki_cli.cli import _build_parser
from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services import bootstrap_runtime as render
from llm_wiki_cli.services.dependencies import analyze_dependencies
from llm_wiki_cli.services.diagrams import sequence_diagram
from llm_wiki_cli.services.doctor_service import DOCTOR_EXIT_CODES, _classify
from llm_wiki_cli.services.entrypoints import build_flow
from llm_wiki_cli.services.extraction_service import get_call_graph, resolve_call_edges
from llm_wiki_cli.services.extractor_helpers import resolve_helper_cache_root
from llm_wiki_cli.services.knowledge_envelope import (
    ProducerComponentInput,
    build_producer_record,
)
from llm_wiki_cli.services.knowledge_evidence import ConceptObservationBasis
from llm_wiki_cli.services.knowledge_freshness import (
    LiveKnowledgeEvaluation,
    evaluate_knowledge_freshness,
)
from llm_wiki_cli.services.knowledge_model import parse_knowledge_index
from llm_wiki_cli.services.knowledge_orchestration import _producer_evidence
from llm_wiki_cli.services.module_maps import build_module_dependency_maps

ROOT = Path(__file__).resolve().parents[1]


def inventory_from_sources(sources):
    with TemporaryDirectory(prefix="wiki-report-probe-") as directory:
        root = Path(directory)
        for name, source in sources.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding="utf-8")
        return PythonExtractor().extract(
            str(root), deep=True, include_empty=True, source_files=sorted(sources)
        )


def flow_for(symbol, edges, filepath="handler.py"):
    return build_flow(
        {"id": "api-" + symbol, "category": "api", "file": filepath,
         "symbol": symbol, "label": symbol},
        edges,
    )


def finding_01():
    inventory = inventory_from_sources({
        "handler.py": (
            "def check_wiki(service):\n    return service.check_wiki()\n\n"
            "def recursive():\n    return recursive()\n"
        )
    })
    edges = resolve_call_edges(inventory)
    delegated = next(edge for edge in edges if edge["name"] == "service.check_wiki")
    flow = flow_for("check_wiki", edges)
    interactions = render._flow_interactions(flow)
    recursive = next(edge for edge in edges if edge["name"] == "recursive")
    assert delegated["kind"] == "unresolved" and delegated["to"]["file"] is None
    assert recursive["kind"] == "internal"
    return {
        "delegated_edge": delegated,
        "rendered_diagram": sequence_diagram(interactions),
        "distinct_targets_collapsed": interactions[0]["from"] == interactions[0]["to"],
        "real_recursion_control_is_internal": recursive["from"] == recursive["to"],
    }


def finding_02():
    inventory = inventory_from_sources({
        "types_a.py": "class A: pass\n",
        "types_b.py": "class B: pass\n",
        "types_c.py": "class C: pass\n",
        "handler.py": (
            "from types_a import A\nfrom types_b import B\nfrom types_c import C\n\n"
            "def annotations_only(a: A, b: B, c: C) -> A:\n    return a\n\n"
            "def calls_only():\n    return C(B(A()))\n"
        ),
    })
    workflows = get_call_graph(inventory)
    functions = {fn["name"]: fn for fn in inventory["handler.py"]["functions"]}
    return {
        "annotations_only_body_calls": functions["annotations_only"].get("calls", []),
        "annotations_only_workflow_chain": workflows.get("annotations_only", {}).get("chain", []),
        "calls_only_body_calls": [call["name"] for call in functions["calls_only"]["calls"]],
        "calls_only_has_workflow": "calls_only" in workflows,
    }


def producer_for(inventory, registry):
    _, _, extractors, plugins = _producer_evidence(
        inventory, inventory_complete=True, extractor_registry=registry
    )
    return build_producer_record(
        tool=ProducerComponentInput("agent-wiki-cli", "2.0.1", configuration={}),
        extractors=extractors, plugins=plugins,
    )


def replay_module_basis(knowledge, locator):
    concept = next(c for c in knowledge.concepts if c.locator == locator)
    basis = concept.facets.structure.basis
    assert basis is not None and basis.source_path and basis.extractor_ref
    assert basis.source_content_hash and basis.concept_observation_hash
    live = LiveKnowledgeEvaluation(
        schema_version=knowledge.schema_version,
        producer=knowledge.bundle.producer,
        generation_options_hash=knowledge.bundle.snapshot.generation_options_hash,
        source_content_hashes={basis.source_path: basis.source_content_hash},
        concept_bases={locator: ConceptObservationBasis(
            scope=basis.scope.value,
            source_path=basis.source_path,
            extractor_ref=basis.extractor_ref,
            source_content_hash=basis.source_content_hash,
            concept_observation_hash=basis.concept_observation_hash,
        )},
    )
    result = evaluate_knowledge_freshness(knowledge, live).by_locator[locator]
    return {"state": result.state.value, "reason": result.reason_code}


def finding_03():
    inventory = {"demo.js": {"language": "javascript"},
                 "demo.ts": {"language": "typescript"}}
    producer = producer_for(inventory, EXTRACTOR_REGISTRY)
    by_id = {item.component_id: item for item in producer.extractors}
    javascript = by_id["llm-wiki/extractor/javascript"]
    typescript = by_id["llm-wiki/extractor/typescript"]
    # Counterfactual evidence input only: this does not edit the registry.
    alias_registry = dict(EXTRACTOR_REGISTRY)
    alias_registry["javascript"] = EXTRACTOR_REGISTRY["typescript"]
    alias_producer = producer_for(inventory, alias_registry)
    alias_javascript = next(item for item in alias_producer.extractors
                            if item.component_id == javascript.component_id)
    payload = json.loads(
        (ROOT / "docs/llm_wiki/.llm-wiki-knowledge.json").read_text(encoding="utf-8")
    )
    locator = "llm-wiki://modules/llm-wiki_main"
    # Validate only the reported module and its producer/basis. The full file
    # includes large unrelated graph extensions, unnecessary for this probe.
    module = next(c for c in payload["concepts"] if c["locator"] == locator)
    knowledge = parse_knowledge_index({
        "schema_version": payload["schema_version"],
        "bundle": payload["bundle"],
        "concepts": [module],
        "relationships": [],
    })
    del payload
    baseline = replay_module_basis(knowledge, locator)
    recorded_producer = knowledge.bundle.producer
    counterfactual = replace(knowledge, bundle=replace(
        knowledge.bundle,
        producer=replace(recorded_producer, extractors=tuple(
            alias_javascript if item.component_id == javascript.component_id else item
            for item in recorded_producer.extractors
        )),
    ))
    recovered = replay_module_basis(counterfactual, locator)
    classified = _classify(
        strict=True, source_selection_mismatch=False,
        availability={"state": "ready"}, freshness={"evaluated": True},
        snapshot={"state": "consistent"},
        governance={"state": "valid", "expired_reviews": 0},
        drift={"state": "indeterminate"}, verification={"state": "absent"},
    )
    return {
        "registry_has_typescript": "typescript" in EXTRACTOR_REGISTRY,
        "registry_has_javascript": "javascript" in EXTRACTOR_REGISTRY,
        "javascript_configuration_hash": javascript.configuration_hash,
        "javascript_limitations": list(javascript.limitations),
        "typescript_control_has_hash": typescript.configuration_hash is not None,
        "counterfactual_alias_has_hash": alias_javascript.configuration_hash is not None,
        "recorded_module_matching_basis_replay": baseline,
        "counterfactual_matching_basis_replay": recovered,
        "strict_indeterminate_classifier_exit": DOCTOR_EXIT_CODES[classified[0]],
        "strict_indeterminate_classifier_reasons": list(classified[2]),
    }


def finding_04():
    inventory = inventory_from_sources({
        "a.py": "from typing import TYPE_CHECKING as TC\nif TC:\n    import b\n",
        "b.py": "import a\n",
    })
    with TemporaryDirectory(prefix="wiki-dependency-probe-") as directory:
        analysis = analyze_dependencies(inventory, directory)
    summary = build_module_dependency_maps(analysis)["a.py"]
    rendered = "\n".join(render._generate_module_dependency_section(summary))
    return {
        "type_checking_import": next(item for item in inventory["a.py"]["imports"]
                                     if item["module"] == "b"),
        "coupling_edges": analysis["graph"]["edges"],
        "import_time_edges": analysis["graph"]["import_time_edges"],
        "runtime_cycles": analysis["cycles"],
        "local_cycle_participation": summary["cycle_participation"],
        "local_cycle_edges": summary["cycle_edges"],
        "rendered_cycle_warning": "inside an import cycle" in rendered,
    }


def finding_05():
    filepath = "src/llm_wiki_cli/api_types.py"
    inventory = PythonExtractor().extract(str(ROOT), deep=True, source_files=[filepath])
    cls = next(item for item in inventory[filepath]["classes"]
               if item["name"] == "ContextKnowledgeResult")
    markdown = render._generate_entity_md(cls, filepath, {})
    return {
        "runtime_optional_keys": sorted(ContextKnowledgeResult.__optional_keys__),
        "runtime_required_keys": sorted(ContextKnowledgeResult.__required_keys__),
        "extracted_selection": next(item for item in cls["attributes"]
                                    if item["name"] == "selection"),
        "rendered_selection_row": next(line for line in markdown.splitlines()
                                       if line.startswith("| `selection`")),
    }


def finding_06():
    edges = [{"from": {"file": "handler.py", "symbol": "run"},
              "to": {"file": None, "symbol": "utility_" + str(index)},
              "name": "utility_" + str(index), "kind": "unresolved", "line": index}
             for index in range(1, 41)]
    markdown = render._generate_flow_md(flow_for("run", edges))
    return {
        "rendered_interactions": markdown.count("-->>"),
        "omission_disclosure": next(line for line in markdown.splitlines()
                                    if line.startswith("> Call sequence diagram shows")),
        "last_ten_calls_omitted_as_documented": "utility_31" not in markdown,
    }


def finding_07():
    inventory = inventory_from_sources({
        "pkg/app.py": "from . import helper\n",
        "pkg/helper.py": "VALUE = 1\n",
    })
    inventory.update({"client/main.js": {"language": "javascript"},
                      "helper/main.rs": {"language": "rust"}})
    with TemporaryDirectory(prefix="wiki-polyglot-probe-") as directory:
        analysis = analyze_dependencies(inventory, directory)
    order = analysis["load_order"]["order"]
    return {
        "import_time_edges": analysis["graph"]["import_time_edges"],
        "order": order,
        "all_dependency_constraints_satisfied": all(
            order.index(target) < order.index(source)
            for source, target in analysis["graph"]["import_time_edges"]
        ),
        "cross_runtime_edges": [edge for edge in analysis["graph"]["edges"]
                                if inventory[edge[0]]["language"] !=
                                inventory[edge[1]]["language"]],
    }


def finding_08():
    filepath = "src/llm_wiki_cli/commands/ci_check_cmd.py"
    source = (ROOT / filepath).read_text(encoding="utf-8")
    tree = ast.parse(source)
    data = PythonExtractor().extract(str(ROOT), deep=True, source_files=[filepath])[filepath]
    markdown = render._generate_module_md(filepath, data)
    return {
        "source_module_docstring": ast.get_docstring(tree),
        "source_function_docstrings": {
            node.name: ast.get_docstring(node) for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        },
        "rendered_source_fallback": "_Auto-generated from `" + filepath + "`._" in markdown,
    }


def finding_09():
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        try:
            _build_parser().parse_args([
                "context", "--budget", "8000", "--helper-cache-dir", "custom-cache"
            ])
        except SystemExit as exc:
            exit_code = exc.code
        else:
            exit_code = 0
    with TemporaryDirectory(prefix="wiki-cache-probe-") as directory:
        cache = Path(directory) / "chosen"
        resolved = resolve_helper_cache_root(
            directory, env={"LLM_WIKI_CACHE_DIR": str(cache)}
        )
        env_works = resolved == cache.resolve() / "llm-wiki-extractors"
    return {
        "context_flag_parser_exit": exit_code,
        "parser_error": stderr.getvalue().splitlines()[-1],
        "documented_environment_cache_selection_works": env_works,
    }


def main():
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(ROOT), check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    results = {
        "source_revision": revision,
        "python": platform.python_version(),
        "platform": sys.platform,
        "comparison_scope": "targeted source fixtures and recorded-basis replay; no live doctor",
        "findings": {
            "FINDING-01": finding_01(), "FINDING-02": finding_02(),
            "FINDING-03": finding_03(), "FINDING-04": finding_04(),
            "FINDING-05": finding_05(), "FINDING-06": finding_06(),
            "FINDING-07": finding_07(), "FINDING-08": finding_08(),
            "FINDING-09": finding_09(),
        },
    }
    print(json.dumps(results, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
