"""Service layer map and shrink-only baselines of upward imports.

Engine layers (primitive, kernel) must not depend on analysis, product or
adapter modules, and analysis modules (services and extractors, the future
domain packs) must not depend on product or adapter modules. Existing
exceptions are pinned exactly: fixing one requires deleting its baseline
entry, and a new one fails. Imports inside functions
count because they hide import cycles; TYPE_CHECKING imports do not.
Every service module must be classified, so a new module states its layer.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "llm_wiki_cli"
LAYER_ORDER = ("primitive", "kernel", "analysis", "product", "adapter")
ENGINE_LAYERS = frozenset({"primitive", "kernel"})

# Domain-free helpers: encodings, digests, paths, guarded I/O.
PRIMITIVE_SERVICES = frozenset(
    {
        "canonical_json",
        "circuit_breaker",
        "contracts",
        "filesystem_guard",
        "freshness_wording",
        "gitignore",
        "host",
        "immutable",
        "io",
        "lockfile",
        "normalization_diagnostics",
        "path_policy",
        "paths",
        "progress",
        "redaction",
        "request_json",
        "runtime_output",
        "secure_file",
        "storage_receipts",
        "storage_sort",
        "storage_spool",
        "token_counting",
        "validation",
        "versioning",
    }
)

# Knowledge, wiki surface, maintenance, query, context and storage.
KERNEL_SERVICES = frozenset(
    {
        "canonical_pages",
        "change_selection",
        "concept_identity",
        "context_budget",
        "context_knowledge_contract",
        "context_packet",
        "context_service",
        "context_session",
        "documentation_queries",
        "documentation_query_builder",
        "knowledge_artifacts",
        "knowledge_audit",
        "knowledge_consumption",
        "knowledge_coverage",
        "knowledge_envelope",
        "knowledge_evidence",
        "knowledge_freshness",
        "knowledge_governance",
        "knowledge_graph",
        "knowledge_index",
        "knowledge_links",
        "knowledge_loader",
        "knowledge_maintenance",
        "knowledge_model",
        "knowledge_observability",
        "knowledge_packs",
        "knowledge_reuse",
        "knowledge_storage",
        "knowledge_storage_access",
        "knowledge_storage_diagnostics",
        "knowledge_storage_io",
        "knowledge_storage_lifecycle",
        "knowledge_stream_audit",
        "knowledge_verification",
        "maintenance_evidence",
        "maintenance_projection",
        "maintenance_protocol",
        "maintenance_queue",
        "maintenance_recovery",
        "maintenance_service",
        "maintenance_shapes",
        "maintenance_state",
        "maintenance_status",
        "manifest_storage",
        "markdown_sections",
        "packet_field_policy",
        "protected_artifacts",
        "scoped_sync_repair",
        "search_discovery",
        "search_discovery_capture",
        "search_lexical",
        "search_rank",
        "search_service",
        "search_source",
        "section_ownership",
        "source_retirement",
        "source_selection",
        "source_snapshot",
        "sync_manifest",
        "sync_recovery",
        "sync_retained_links",
        "sync_transition_execution",
        "sync_transitions",
        "task_compact",
        "task_compact_delivery",
        "task_compact_readable",
        "task_context",
        "task_context_v2",
        "task_contract",
        "task_evidence",
        "task_implementation",
        "verification_contracts",
        "wiki_lifecycle",
        "wiki_media",
        "wiki_surface",
        "wiki_surface_index",
        "wiki_write_basis",
        "workflow_profile",
    }
)

# Source analysis for code, infrastructure and API inputs; future packs.
ANALYSIS_SERVICES = frozenset(
    {
        "analysis_capture",
        "analysis_compatibility",
        "analysis_targets",
        "api_contracts",
        "api_diff",
        "capability_diagnostics",
        "current_contracts",
        "data_flow",
        "dependencies",
        "dependency_versions",
        "diagrams",
        "dockerfile_parser",
        "entrypoints",
        "evidence_diagnostics",
        "extraction_jobs",
        "extraction_service",
        "extractor_helpers",
        "extractor_registry",
        "flow_followup",
        "flow_overview",
        "go_calls",
        "helper_cache",
        "helper_preparation",
        "helper_runtime",
        "impact",
        "implementation_evidence",
        "imports",
        "infrastructure_inventory",
        "infrastructure_sync",
        "inventory_cache",
        "module_coverage",
        "module_maps",
        "packages",
        "python_calls",
        "python_implementation",
        "python_imports",
        "python_observations",
        "python_stdlib",
        "relationships",
        "source_path_diagnostics",
        "sync_analysis",
        "sync_analysis_cache",
        "sync_analysis_storage",
        "typescript_helper_identity",
        "yaml_formats",
        "yaml_syntax",
    }
)

# Product workflows and adapters: CLI-facing, MCP, publication, CI, calibration.
PRODUCT_SERVICES = frozenset(
    {
        "behavior_reference",
        "bootstrap_recovery",
        "bootstrap_runtime",
        "bootstrap_service",
        "calibration",
        "calibration.broker",
        "calibration.contracts",
        "calibration.controller",
        "calibration.host_broker",
        "ci_installer",
        "ci_report",
        "cli_reference",
        "doctor_service",
        "documentation_calibration",
        "documentation_calibration_broker",
        "documentation_calibration_controller",
        "documentation_calibration_host_broker",
        "documentation_claim_evidence",
        "documentation_model_policy",
        "documentation_native",
        "documentation_policy",
        "documentation_review",
        "documentation_run",
        "documentation_run.contracts",
        "documentation_run.dependencies",
        "documentation_run.export",
        "documentation_run.integrity",
        "documentation_run.packet",
        "documentation_run.prepare",
        "documentation_run.publication",
        "documentation_run.record",
        "documentation_run.refresh",
        "documentation_run.schema",
        "documentation_run.verify",
        "documentation_run.workspace",
        "documentation_wiki_input",
        "documentation_worklist",
        "evidence_explanation",
        "health_contract",
        "health_details",
        "health_policy",
        "health_summary",
        "instruction_ownership",
        "knowledge_generation",
        "knowledge_orchestration",
        "knowledge_projection",
        "legacy_hooks",
        "lint_service",
        "mcp_server",
        "metrics",
        "native_inspection",
        "obsidian",
        "plugin_samples",
        "plugins",
        "publication_candidate",
        "publication_config",
        "publication_contracts",
        "publication_delivery",
        "publication_impact",
        "publication_links",
        "publication_maintenance",
        "publication_references",
        "publication_snapshot",
        "rendering_lifecycle",
        "resource_diagnostics",
        "review_service",
        "schema",
        "site_export",
        "site_html_check",
        "skills",
        "sync_generated_sections",
        "sync_runtime",
        "sync_service",
        "team",
        "wiki_git_delivery",
        "wiki_git_policy",
        "wiki_scaffold",
    }
)

# Upward imports from engine layers that exist today. Entries may only be removed.
UPWARD_IMPORT_BASELINE: dict[str, frozenset[str]] = {
    "canonical_pages": frozenset(
        {
            "services.bootstrap_runtime",
            "services.infrastructure_sync",
        }
    ),
    "change_selection": frozenset(
        {
            "services.bootstrap_runtime",
            "services.extraction_service",
        }
    ),
    "context_packet": frozenset(
        {
            "llm_wiki_cli",
            "services.dependencies",
            "services.extraction_jobs",
            "services.extraction_service",
            "services.extractor_helpers",
            "services.helper_cache",
            "services.implementation_evidence",
            "services.plugins",
        }
    ),
    "context_service": frozenset(
        {
            "services.dependencies",
            "services.extraction_jobs",
            "services.extraction_service",
            "services.helper_cache",
            "services.implementation_evidence",
            "services.infrastructure_inventory",
            "services.knowledge_orchestration",
            "services.plugins",
        }
    ),
    "context_session": frozenset(
        {
            "llm_wiki_cli",
            "services.analysis_compatibility",
        }
    ),
    "documentation_queries": frozenset(
        {
            "services.dependencies",
            "services.evidence_diagnostics",
            "services.flow_followup",
            "services.implementation_evidence",
            "services.relationships",
        }
    ),
    "documentation_query_builder": frozenset(
        {
            "services.dependencies",
            "services.entrypoints",
            "services.extraction_service",
            "services.python_implementation",
            "services.source_path_diagnostics",
        }
    ),
    "filesystem_guard": frozenset({"services.wiki_write_basis"}),
    "io": frozenset(
        {
            "services.knowledge_evidence",
            "services.wiki_write_basis",
        }
    ),
    "knowledge_artifacts": frozenset(
        {
            "services.implementation_evidence",
            "services.infrastructure_sync",
        }
    ),
    "knowledge_consumption": frozenset({"services.implementation_evidence"}),
    "knowledge_freshness": frozenset({"services.analysis_compatibility"}),
    "knowledge_index": frozenset(
        {
            "services.analysis_compatibility",
            "services.implementation_evidence",
            "services.python_implementation",
        }
    ),
    "knowledge_maintenance": frozenset(
        {
            "extractors.common",
            "llm_wiki_cli",
            "services.analysis_capture",
            "services.analysis_compatibility",
            "services.extractor_helpers",
            "services.extractor_registry",
            "services.health_policy",
            "services.knowledge_orchestration",
        }
    ),
    "knowledge_model": frozenset(
        {
            "services.analysis_compatibility",
            "services.implementation_evidence",
        }
    ),
    "knowledge_reuse": frozenset(
        {
            "llm_wiki_cli",
            "services.extraction_service",
            "services.knowledge_orchestration",
            "services.python_implementation",
        }
    ),
    "knowledge_storage": frozenset({"services.implementation_evidence"}),
    "knowledge_storage_access": frozenset({"services.implementation_evidence"}),
    "maintenance_evidence": frozenset(
        {
            "services.implementation_evidence",
            "services.python_implementation",
        }
    ),
    "maintenance_protocol": frozenset(
        {
            "services.bootstrap_recovery",
            "services.knowledge_orchestration",
        }
    ),
    "maintenance_queue": frozenset(
        {
            "services.documentation_worklist",
            "services.inventory_cache",
            "services.lint_service",
        }
    ),
    "maintenance_service": frozenset(
        {
            "services.knowledge_orchestration",
            "services.python_implementation",
        }
    ),
    "maintenance_state": frozenset(
        {
            "services.implementation_evidence",
            "services.python_implementation",
        }
    ),
    "maintenance_status": frozenset(
        {
            "services.extraction_service",
            "services.implementation_evidence",
            "services.python_implementation",
        }
    ),
    "scoped_sync_repair": frozenset(
        {
            "services.analysis_capture",
            "services.analysis_compatibility",
            "services.implementation_evidence",
            "services.knowledge_orchestration",
        }
    ),
    "source_retirement": frozenset({"services.sync_analysis"}),
    "source_snapshot": frozenset(
        {
            "extractors.common",
            "services.extractor_registry",
        }
    ),
    "storage_receipts": frozenset(
        {
            "services.knowledge_packs",
            "services.knowledge_storage",
        }
    ),
    "storage_sort": frozenset({"services.knowledge_storage"}),
    "storage_spool": frozenset({"services.knowledge_storage"}),
    "sync_manifest": frozenset({"extractors.common"}),
    "sync_transitions": frozenset(
        {
            "services.bootstrap_runtime",
            "services.sync_analysis",
        }
    ),
    "task_compact_delivery": frozenset({"services.analysis_compatibility"}),
    "task_context": frozenset({"services.analysis_capture"}),
    "task_context_v2": frozenset(
        {
            "services.dependencies",
            "services.extraction_service",
            "services.implementation_evidence",
            "services.python_implementation",
        }
    ),
    "task_evidence": frozenset({"services.implementation_evidence"}),
    "task_implementation": frozenset(
        {
            "services.implementation_evidence",
            "services.python_implementation",
        }
    ),
    "wiki_lifecycle": frozenset(
        {
            "config",
            "services.current_contracts",
            "services.rendering_lifecycle",
            "services.schema",
            "services.wiki_scaffold",
        }
    ),
}

# Product and adapter imports from analysis modules that exist today. Packs must
# reach plugins and product services through the engine. Entries may only be removed.
ANALYSIS_UPWARD_IMPORT_BASELINE: dict[str, frozenset[str]] = {
    "analysis_targets": frozenset({"services.health_policy"}),
    "capability_diagnostics": frozenset(
        {
            "services.doctor_service",
            "services.plugins",
        }
    ),
    "diagrams": frozenset({"services.plugins"}),
    "entrypoints": frozenset({"services.plugins"}),
    "extraction_service": frozenset(
        {
            "services.plugins",
            "services.resource_diagnostics",
        }
    ),
    "impact": frozenset({"services.review_service"}),
    "inventory_cache": frozenset(
        {
            "llm_wiki_cli",
            "services.plugins",
        }
    ),
    "sync_analysis": frozenset({"services.bootstrap_runtime"}),
    "sync_analysis_cache": frozenset({"services.knowledge_generation"}),
}

# Ambient side effects in engine layers today. Entries may only be removed;
# output, processes, environment, working directory and clock come from the host.
SIDE_EFFECT_BASELINE: dict[str, frozenset[str]] = {}

# The host module is the one boundary that touches the machine on the engine's
# behalf; everything else asks ``host.current_host()``.
HOST_BOUNDARY: dict[str, frozenset[str]] = {
    "host": frozenset({"subprocess", "environ", "cwd", "clock", "print"}),
}

_SERVICE_LAYERS = {
    **{name: "primitive" for name in PRIMITIVE_SERVICES},
    **{name: "kernel" for name in KERNEL_SERVICES},
    **{name: "analysis" for name in ANALYSIS_SERVICES},
    **{name: "product" for name in PRODUCT_SERVICES},
}
_SERVICES = "llm_wiki_cli.services"


def _source_paths(package_root: Path) -> list[Path]:
    return [
        path
        for path in sorted(package_root.rglob("*.py"))
        if "target" not in path.relative_to(package_root).parts
    ]


def _module_name(path: Path, package_root: Path) -> str:
    relative = path.relative_to(package_root.parent).with_suffix("")
    parts = relative.parts[:-1] if relative.name == "__init__" else relative.parts
    return ".".join(parts)


def _module_layer(module: str, service_layers: dict[str, str]) -> str | None:
    if module in {_SERVICES, "llm_wiki_cli.schemas"}:
        return "primitive"
    if module.startswith(_SERVICES + "."):
        return service_layers.get(module.removeprefix(_SERVICES + "."))
    if module == "llm_wiki_cli.extractors" or module.startswith("llm_wiki_cli.extractors."):
        return "analysis"
    return "adapter"


def _imported_modules(path: Path, package_root: Path, modules: set[str]) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    current = _module_name(path, package_root)
    package = current.split(".") if path.name == "__init__.py" else current.split(".")[:-1]
    type_only = {
        id(node)
        for statement in ast.walk(tree)
        if isinstance(statement, ast.If) and "TYPE_CHECKING" in ast.unparse(statement.test)
        for child in statement.body
        for node in ast.walk(child)
    }
    found: set[str] = set()
    for node in ast.walk(tree):
        if id(node) in type_only:
            continue
        if isinstance(node, ast.Import):
            candidates = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = package[: len(package) - (node.level - 1)] if node.level else []
            target = ".".join([*base, *([node.module] if node.module else [])])
            candidates = [
                f"{target}.{alias.name}" if f"{target}.{alias.name}" in modules else target
                for alias in node.names
            ]
        else:
            continue
        for candidate in candidates:
            while candidate and candidate not in modules:
                candidate = candidate.rpartition(".")[0]
            if candidate and candidate != current:
                found.add(candidate)
    return found


def _baseline_key(module: str) -> str:
    return module.removeprefix("llm_wiki_cli.").removeprefix("services.")


def _upward_imports(
    package_root: Path = PACKAGE_ROOT,
    service_layers: dict[str, str] = _SERVICE_LAYERS,
    source_layers: frozenset[str] = ENGINE_LAYERS,
) -> dict[str, frozenset[str]]:
    """Map each service or extractor module in ``source_layers`` to higher-layer imports.

    Keys drop the ``llm_wiki_cli.services.`` prefix (extractors keep
    ``extractors.``); targets are relative to ``llm_wiki_cli``.
    """
    paths = _source_paths(package_root)
    modules = {_module_name(path, package_root) for path in paths}
    rank: dict[str | None, int] = {layer: index for index, layer in enumerate(LAYER_ORDER)}
    result: dict[str, frozenset[str]] = {}
    for path in paths:
        source = _module_name(path, package_root)
        if not source.startswith((_SERVICES + ".", "llm_wiki_cli.extractors")):
            continue
        layer = _module_layer(source, service_layers)
        if layer not in source_layers:
            continue
        upward = {
            target.removeprefix("llm_wiki_cli.")
            for target in _imported_modules(path, package_root, modules)
            if rank.get(_module_layer(target, service_layers), -1) > rank[layer]
        }
        if upward:
            result[_baseline_key(source)] = frozenset(upward)
    return result


def _baseline_drift(
    actual: dict[str, frozenset[str]], baseline: dict[str, frozenset[str]]
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    added = {
        source: sorted(targets - baseline.get(source, frozenset()))
        for source, targets in actual.items()
        if targets - baseline.get(source, frozenset())
    }
    fixed = {
        source: sorted(targets - actual.get(source, frozenset()))
        for source, targets in baseline.items()
        if targets - actual.get(source, frozenset())
    }
    return added, fixed


_SIDE_EFFECT_CALLS = {
    "subprocess": frozenset(
        {
            "subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_call",
            "subprocess.check_output", "subprocess.getoutput", "subprocess.getstatusoutput",
            "os.system", "os.popen",
        }
    ),
    "print": frozenset({"print", "sys.stdout.write", "sys.stderr.write"}),
    "exit": frozenset({"sys.exit", "exit", "quit", "os._exit"}),
    "environ": frozenset({"os.getenv", "os.putenv"}),
    "cwd": frozenset({"os.getcwd", "os.chdir", "pathlib.Path.cwd"}),
    "sys.path": frozenset(
        {"sys.path.insert", "sys.path.append", "sys.path.extend", "sys.path.remove"}
    ),
    "clock": frozenset(
        {
            "datetime.datetime.now", "datetime.datetime.utcnow", "datetime.date.today",
            "datetime.datetime.today",
        }
    ),
    "network": frozenset(
        {
            "socket.socket", "socket.create_connection", "urllib.request.urlopen",
            "http.client.HTTPConnection", "http.client.HTTPSConnection",
        }
    ),
}


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else ""
    return ""


def _side_effects(path: Path) -> frozenset[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"

    def resolved(node: ast.AST) -> str:
        name = _dotted(node)
        head, _, rest = name.partition(".")
        target = aliases.get(head, head)
        return f"{target}.{rest}" if rest else target

    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = resolved(node.func)
            found.update(kind for kind, names in _SIDE_EFFECT_CALLS.items() if name in names)
        elif isinstance(node, (ast.Attribute, ast.Name)) and resolved(node) == "os.environ":
            found.add("environ")
        elif isinstance(node, ast.Assign) and any(
            resolved(target) == "sys.path" for target in node.targets
        ):
            found.add("sys.path")
    return frozenset(found)


def _engine_side_effects(
    package_root: Path = PACKAGE_ROOT,
    service_layers: dict[str, str] = _SERVICE_LAYERS,
) -> dict[str, frozenset[str]]:
    result: dict[str, frozenset[str]] = {}
    for path in _source_paths(package_root / "services"):
        module = _module_name(path, package_root)
        if _module_layer(module, service_layers) in ENGINE_LAYERS and (
            effects := _side_effects(path)
        ):
            result[module.removeprefix(_SERVICES + ".")] = effects
    return result


def test_engine_layers_add_no_ambient_side_effects() -> None:
    actual = _engine_side_effects()
    assert {name: actual.pop(name, frozenset()) for name in HOST_BOUNDARY} == HOST_BOUNDARY
    added = {
        module: sorted(effects - SIDE_EFFECT_BASELINE.get(module, frozenset()))
        for module, effects in actual.items()
        if effects - SIDE_EFFECT_BASELINE.get(module, frozenset())
    }
    fixed = {
        module: sorted(effects - actual.get(module, frozenset()))
        for module, effects in SIDE_EFFECT_BASELINE.items()
        if effects - actual.get(module, frozenset())
    }

    assert added == {}, "engine layers receive processes, output, environment and paths from the host"
    assert fixed == {}, "delete fixed entries from SIDE_EFFECT_BASELINE"


def test_side_effect_scan_resolves_import_aliases(tmp_path: Path) -> None:
    package_root = tmp_path / "llm_wiki_cli"
    files = {
        "services/__init__.py": "",
        "services/runner.py": (
            "import subprocess as sp\n"
            "from os import environ, getcwd\n"
            "from pathlib import Path\n"
            "import sys\n"
            "def run():\n"
            "    sp.run(['git'])\n"
            "    print(environ.get('HOME'), getcwd(), Path.cwd())\n"
            "    sys.path.insert(0, 'x')\n"
            "    sys.exit(1)\n"
        ),
        "services/pure.py": "def run(value):\n    return value.strip()\n",
        "services/analysis.py": "import subprocess\nsubprocess.run(['go'])\n",
    }
    for relative, source in files.items():
        path = package_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    layers = {"runner": "kernel", "pure": "primitive", "analysis": "analysis"}

    assert _engine_side_effects(package_root, layers) == {
        "runner": frozenset({"subprocess", "environ", "cwd", "print", "sys.path", "exit"}),
    }


def test_every_service_module_has_exactly_one_layer() -> None:
    services_root = PACKAGE_ROOT / "services"
    modules = {
        _module_name(path, PACKAGE_ROOT).removeprefix(_SERVICES + ".")
        for path in _source_paths(services_root)
        if path != services_root / "__init__.py"
    }
    groups = (PRIMITIVE_SERVICES, KERNEL_SERVICES, ANALYSIS_SERVICES, PRODUCT_SERVICES)
    overlapping = {
        name for index, group in enumerate(groups) for name in group
        if any(name in other for other in groups[index + 1:])
    }

    assert overlapping == set()
    assert sorted(modules - _SERVICE_LAYERS.keys()) == [], "classify new service modules"
    assert sorted(_SERVICE_LAYERS.keys() - modules) == [], "remove deleted service modules"


def test_engine_layers_add_no_upward_imports() -> None:
    added, fixed = _baseline_drift(_upward_imports(), UPWARD_IMPORT_BASELINE)

    assert added == {}, "engine layers must not import analysis, product or adapter modules"
    assert fixed == {}, "delete fixed entries from UPWARD_IMPORT_BASELINE"


def test_analysis_layer_adds_no_product_or_adapter_imports() -> None:
    actual = _upward_imports(source_layers=frozenset({"analysis"}))
    added, fixed = _baseline_drift(actual, ANALYSIS_UPWARD_IMPORT_BASELINE)

    assert added == {}, "analysis modules must not import product or adapter modules"
    assert fixed == {}, "delete fixed entries from ANALYSIS_UPWARD_IMPORT_BASELINE"


def _import_closure(start: str, package_root: Path = PACKAGE_ROOT) -> set[str]:
    paths = {_module_name(path, package_root): path for path in _source_paths(package_root)}
    modules = set(paths)
    seen, pending = set(), [start]
    while pending:
        module = pending.pop()
        if module in seen or module not in paths:
            continue
        seen.add(module)
        pending.extend(_imported_modules(paths[module], package_root, modules))
        # Importing a submodule runs its parent packages first.
        parent = module.rpartition(".")[0]
        if parent:
            pending.append(parent)
    return seen


@pytest.mark.parametrize("start", ["llm_wiki_cli.cli_declarations", "llm_wiki_cli.engine"])
def test_entry_points_reach_no_commands_cli_or_public_api(start: str) -> None:
    """The CLI reference and the engine work without loading the CLI or the facade."""
    closure = _import_closure(start)
    forbidden = sorted(
        module for module in closure
        if module in {"llm_wiki_cli.cli", "llm_wiki_cli.api", "llm_wiki_cli.services.mcp_server"}
        or module == "llm_wiki_cli.commands" or module.startswith("llm_wiki_cli.commands.")
    )

    assert forbidden == []


def test_upward_scan_counts_function_imports_but_not_type_checking(tmp_path: Path) -> None:
    package_root = tmp_path / "llm_wiki_cli"
    files = {
        "__init__.py": "",
        "cli.py": "",
        "services/__init__.py": "",
        "services/analyzer.py": "",
        "services/kernel_one.py": (
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from . import analyzer\n"
            "def run():\n"
            "    from .. import cli\n"
        ),
        "services/kernel_two.py": "try:\n    from .analyzer import value\nexcept ImportError:\n    pass\n",
        "services/product.py": "from . import analyzer\n",
        "services/pack.py": "from . import kernel_one\ndef run():\n    from . import product\n",
        "extractors/__init__.py": "",
        "extractors/common.py": "from .. import cli\nfrom ..services import analyzer\n",
    }
    for relative, source in files.items():
        path = package_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    layers = {
        "analyzer": "analysis",
        "kernel_one": "kernel",
        "kernel_two": "kernel",
        "product": "product",
        "pack": "analysis",
    }

    assert _upward_imports(package_root, layers) == {
        "kernel_one": frozenset({"cli"}),
        "kernel_two": frozenset({"services.analyzer"}),
    }
    assert _upward_imports(package_root, layers, frozenset({"analysis"})) == {
        "pack": frozenset({"services.product"}),
        "extractors.common": frozenset({"cli"}),
    }
