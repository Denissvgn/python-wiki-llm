"""Internal dependency-graph analysis and external reconciliation.

Builds a module-file → module-file dependency graph from a structural
inventory's ``imports`` records, detects import cycles via strongly-connected
components, computes fan-in/fan-out metrics (Epic 2.1), and reconciles each
file's external imports against its language's declared dependency manifest —
Python (``pyproject.toml``), TypeScript/JS (``package.json``), Go (``go.mod``),
Rust (``Cargo.toml``), and Haskell (``*.cabal``/``stack.yaml``/``flake.nix``) —
to surface undeclared and unused packages (Epic 2.2). Analogous to
:mod:`llm_wiki_cli.services.entrypoints`: deterministic, performs no LLM calls,
imports only stdlib (plus the bundled ``tomli`` backport) and
:mod:`llm_wiki_cli.services.imports`, and takes the inventory as plain data
(returning plain dicts/lists). It tolerates slim or non-Python inventory entries
that omit optional fields — absence never raises.

The same module-path resolver that backs call-edge resolution
(:func:`extract_cmd.resolve_call_edges`) is reused here, so import→file
resolution stays consistent across the codebase. Imports that resolve to no
internal file (stdlib, third-party, unresolvable relatives) are collected in an
``unresolved`` bucket; the Epic 2.2 classifiers consume that bucket so an import
already resolved to an internal file is never double-counted as external.

Reconciliation is *language-partitioned*: each language pairs a manifest parser
with an import→package classifier behind a shared dispatcher. A language with
imports but no manifest (everything → undeclared) or a manifest but no imports
(everything → unused) degrades to warnings, never an exception; import→package
name mapping is best-effort per ecosystem, so undeclared/unused are advisory.
"""

from __future__ import annotations

import heapq
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Optional

from ..config import is_agent_worktree_path
from .dependency_versions import build_dependency_version_details
from .imports import build_module_path_resolver
from .source_snapshot import SourceSnapshot, build_source_snapshot
from .validation import (
    path_is_under as shared_path_is_under,
    path_is_under_scope as shared_path_is_under_scope,
    positive_int_or_none,
)

try:  # Python 3.11+
    import tomllib  # type: ignore[reportMissingImports]
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.9/3.10
    try:
        import tomli as tomllib  # type: ignore[reportMissingImports]
    except ModuleNotFoundError:  # pragma: no cover - dependency missing in ad-hoc envs
        tomllib = None  # type: ignore[assignment]


# ── Internal dependency graph (DL-101) ────────────────────────────────


def _build_symbol_file_index(inventory: dict) -> dict[str, set[str]]:
    """Map each top-level symbol name to the files that define it.

    Used only to disambiguate an import whose *module* resolves to more than
    one internal file (e.g. two packages each exposing a ``settings`` module).
    """
    index: defaultdict[str, set[str]] = defaultdict(set)
    for filepath, data in inventory.items():
        if not isinstance(data, dict):
            continue
        for cls in data.get("classes", []):
            index[cls["name"]].add(filepath)
        for fn in data.get("functions", []):
            index[fn["name"]].add(filepath)
    return index


def _resolve_target_module(module: str, name: str) -> str:
    """Return the module string to resolve for an import record.

    A purely-dotted module (``from . import local`` / ``from .. import shared``)
    carries the real target in *name*; fold it in so the resolver lands on the
    submodule file rather than the package ``__init__``.
    """
    if module and set(module) == {"."}:
        return module + name
    return module


def _resolve_internal_targets(
    imp: dict, filepath: str, resolver, symbol_index
) -> set[str]:
    """Return the internal files *imp* (from *filepath*) resolves to.

    Empty only when the import is stdlib/third-party/unresolvable; a module that
    resolves solely to its own file stays non-empty (so it is treated as an
    internal self-reference, not an undeclared external dependency — the caller
    drops the self-edge). When the module alone resolves ambiguously, narrow by
    the imported symbol's defining files.
    """
    module = imp.get("module", "") or ""
    name = imp.get("name", "") or ""
    targets = resolver.candidates(_resolve_target_module(module, name), filepath)
    if len(targets) > 1:
        narrowed = targets & symbol_index.get(name, set())
        if narrowed:
            targets = narrowed
    return targets


def build_dependency_graph(
    inventory: dict,
    project_root: str | Path | None = None,
    *,
    source_snapshot: SourceSnapshot | None = None,
) -> dict:
    """Resolve each file's imports into an internal module-dependency graph.

    For every file, each ``imports`` record is resolved to an internal target
    file with the shared module-path resolver. Resolved targets become directed
    ``(from_file, to_file)`` edges (self-edges excluded, de-duplicated); imports
    that resolve to no internal file land in ``unresolved``.

    Returns ``{"edges": [(from_file, to_file), ...], "nodes": [...],
    "unresolved": [{"file", "module", "name"}, ...]}`` with every list stably
    ordered. A file that imports nothing internal still appears as an isolated
    node. Slim/non-Python entries (no ``imports``) contribute no edges and never
    raise.
    """
    resolver = build_module_path_resolver(
        inventory,
        project_root=project_root,
        source_snapshot=source_snapshot,
    )
    symbol_index = _build_symbol_file_index(inventory)

    edges: set[tuple[str, str]] = set()
    unresolved: list[dict] = []
    nodes: set[str] = set()

    for filepath, data in inventory.items():
        if not isinstance(data, dict) or "imports" not in data:
            continue
        nodes.add(filepath)
        for imp in data.get("imports", []):
            targets = _resolve_internal_targets(imp, filepath, resolver, symbol_index)
            if not targets:
                module = imp.get("module", "") or ""
                entry = {
                    "file": filepath,
                    "module": module,
                    "name": imp.get("name", "") or "",
                }
                if resolver.typescript_path_alias_matched(
                    _resolve_target_module(module, entry["name"]), filepath
                ):
                    entry["kind"] = "path_alias"
                unresolved.append(entry)
                continue
            for target in targets:
                if target != filepath:
                    edges.add((filepath, target))

    for source, target in edges:
        nodes.add(source)
        nodes.add(target)

    return {
        "edges": sorted(edges),
        "nodes": sorted(nodes),
        "unresolved": sorted(
            unresolved, key=lambda u: (u["file"], u["module"], u["name"])
        ),
    }


_DEPENDENCY_OBSERVATIONS_SCHEMA = "llm-wiki-dependency-observations/v1"
_IMPORT_LOCATION_OBSERVATIONS_SCHEMA = (
    "llm-wiki-import-location-observations/v1"
)


def _positive_line(value: object) -> int | None:
    """Return a source line only when the extractor supplied a real line."""
    return positive_int_or_none(value)


def _unresolved_import_resolution(
    module: str, name: str, filepath: str, resolver
) -> str:
    """Classify a no-candidate import without claiming missing code is external."""
    target_module = _resolve_target_module(module, name)
    if (
        not target_module
        or target_module.startswith((".", "/"))
        or resolver.typescript_path_alias_matched(target_module, filepath)
    ):
        return "unresolved"
    return "external"


def _dependency_observation_sort_key(observation: Mapping) -> tuple:
    return (
        str(observation.get("source_path") or ""),
        str(observation.get("module") or ""),
        str(observation.get("name") or ""),
        observation.get("line") or -1,
        str(observation.get("resolution") or ""),
        tuple(observation.get("candidates") or ()),
        str(observation.get("target_path") or ""),
    )


def _import_location_index(
    import_observations: Mapping | None,
) -> tuple[dict[tuple[str, int], Mapping], bool]:
    """Validate an extractor sidecar without turning bad metadata into evidence."""
    if import_observations is None:
        return {}, False
    if (
        not isinstance(import_observations, Mapping)
        or import_observations.get("schema_version")
        != _IMPORT_LOCATION_OBSERVATIONS_SCHEMA
        or not isinstance(import_observations.get("observations"), list)
    ):
        return {}, True

    index: dict[tuple[str, int], Mapping] = {}
    duplicate_keys: set[tuple[str, int]] = set()
    invalid = False
    for observation in import_observations["observations"]:
        if not isinstance(observation, Mapping):
            invalid = True
            continue
        source_path = observation.get("source_path")
        import_index = observation.get("import_index")
        module = observation.get("module")
        name = observation.get("name")
        line = _positive_line(observation.get("line"))
        if (
            not isinstance(source_path, str)
            or not source_path
            or isinstance(import_index, bool)
            or not isinstance(import_index, int)
            or import_index < 0
            or not isinstance(module, str)
            or not isinstance(name, str)
            or line is None
        ):
            invalid = True
            continue
        key = (source_path, import_index)
        if key in index or key in duplicate_keys:
            index.pop(key, None)
            duplicate_keys.add(key)
            invalid = True
            continue
        index[key] = observation
    return index, invalid


def build_dependency_observations(
    inventory: dict,
    project_root: str | Path | None = None,
    *,
    source_snapshot: SourceSnapshot | None = None,
    import_observations: Mapping | None = None,
) -> dict:
    """Return lossless, versioned import-resolution observations.

    Unlike :func:`build_dependency_graph`, this collector emits one observation
    per well-formed inventory import and does not collapse imports into
    ``(from_file, to_file)`` tuples.  A unique internal candidate is
    ``resolved`` (including self-imports), multiple candidates are
    ``ambiguous``, absolute imports outside the selected inventory are
    ``external``, and relative/path-alias misses remain ``unresolved``.

    Source lines are positive integers or ``None``.  An extractor may supply
    the additive ``llm-wiki-import-location-observations/v1`` sidecar to retain
    locations without changing its legacy inventory records. Sidecar records
    are matched by source path and import ordinal, then checked against the
    legacy module/name before use. Absence is explicit rather than encoded as
    line zero.
    """
    resolver = build_module_path_resolver(
        inventory,
        project_root=project_root,
        source_snapshot=source_snapshot,
    )
    symbol_index = _build_symbol_file_index(inventory)
    location_index, invalid_location_observations = _import_location_index(
        import_observations
    )
    observations: list[dict] = []
    malformed = 0
    mismatched_locations = 0
    consumed_location_keys: set[tuple[str, int]] = set()

    for filepath in sorted(inventory):
        data = inventory[filepath]
        if not isinstance(data, Mapping) or "imports" not in data:
            continue
        imports = data.get("imports", [])
        if not isinstance(imports, list):
            malformed += 1
            continue
        for import_index, raw_import in enumerate(imports):
            if not isinstance(raw_import, Mapping):
                malformed += 1
                continue
            module = str(raw_import.get("module") or "")
            name = str(raw_import.get("name") or "")
            line = _positive_line(raw_import.get("line"))
            location_key = (filepath, import_index)
            location_observation = location_index.get(location_key)
            if location_observation is not None:
                consumed_location_keys.add(location_key)
                location_line = _positive_line(location_observation.get("line"))
                if (
                    location_observation.get("module") == module
                    and location_observation.get("name") == name
                    and (line is None or location_line == line)
                ):
                    line = location_line
                else:
                    mismatched_locations += 1
            candidates = sorted(
                _resolve_internal_targets(
                    dict(raw_import), filepath, resolver, symbol_index
                )
            )
            if len(candidates) == 1:
                resolution = "resolved"
                target_path = candidates[0]
            elif candidates:
                resolution = "ambiguous"
                target_path = None
            else:
                resolution = _unresolved_import_resolution(
                    module, name, filepath, resolver
                )
                target_path = None
            observations.append(
                {
                    "source_path": filepath,
                    "module": module,
                    "name": name,
                    "line": line,
                    "candidates": candidates,
                    "target_path": target_path,
                    "resolution": resolution,
                }
            )

    mismatched_locations += len(set(location_index) - consumed_location_keys)
    observations.sort(key=_dependency_observation_sort_key)
    limitations = [
        "external-resolution-is-relative-to-the-selected-inventory",
        "import-locations-depend-on-extractor-support",
        "static-import-resolution-does-not-claim-runtime-completeness",
    ]
    if malformed:
        limitations.append("malformed-import-records")
    if invalid_location_observations:
        limitations.append("invalid-import-location-observations")
    if mismatched_locations:
        limitations.append("mismatched-import-location-observations")
    limitations.sort()
    emitted = len(observations)
    return {
        "schema_version": _DEPENDENCY_OBSERVATIONS_SCHEMA,
        "observations": observations,
        "coverage": {
            "observed": emitted + malformed,
            "emitted": emitted,
            "limit": None,
            "truncated": malformed > 0,
            "omitted": malformed,
            "limitations": limitations,
        },
    }


def build_external_dependency_observations(analysis: Mapping) -> list[dict]:
    """Lift an existing reconciliation report into source/package observations.

    This is deliberately a projection over an already-computed dependency
    analysis: it performs no manifest reads or import resolution.  Both
    declared and undeclared packages are retained so the typed graph can
    distinguish explicit ``depends_on`` evidence without turning every
    external import into such an edge.
    """
    reconciliation = analysis.get("reconciliation", {})
    if not isinstance(reconciliation, Mapping):
        return []
    languages = reconciliation.get("languages", {})
    if not isinstance(languages, Mapping):
        return []

    observations: list[dict] = []
    for language, raw_report in sorted(
        languages.items(),
        key=lambda item: str(item[0]),
    ):
        if not isinstance(raw_report, Mapping):
            continue
        used = raw_report.get("used", {})
        if not isinstance(used, Mapping):
            continue
        required = {
            str(package) for package in raw_report.get("required", []) or []
        }
        optional = {
            str(package) for package in raw_report.get("optional", []) or []
        }
        for package, raw_paths in sorted(used.items(), key=lambda item: str(item[0])):
            package_name = str(package)
            declaration = (
                "required"
                if package_name in required
                else "optional"
                if package_name in optional
                else None
            )
            paths = raw_paths if isinstance(raw_paths, (list, tuple, set)) else ()
            for source_path in sorted(
                {str(path) for path in paths if isinstance(path, str) and path}
            ):
                observation = {
                    "source_path": source_path,
                    "package": package_name,
                    "language": str(language),
                    "explicit": declaration is not None,
                }
                if declaration is not None:
                    observation["declaration"] = declaration
                    observation["reason"] = (
                        f"declared as a {declaration} {language} dependency"
                    )
                observations.append(observation)
    return observations


# ── Cycle detection (DL-102) ──────────────────────────────────────────


def _build_adjacency(graph: dict) -> tuple[dict[str, list[str]], set[str], set[str]]:
    """Return ``(adjacency, nodes, self_loops)`` from a dependency graph."""
    nodes: set[str] = set(graph.get("nodes", []))
    adjacency: defaultdict[str, set[str]] = defaultdict(set)
    self_loops: set[str] = set()
    for source, target in graph.get("edges", []):
        nodes.add(source)
        nodes.add(target)
        if source == target:
            self_loops.add(source)
        else:
            adjacency[source].add(target)
    return ({k: sorted(v) for k, v in adjacency.items()}, nodes, self_loops)


def detect_cycles(graph: dict) -> list[list[str]]:
    """Return the import cycles in *graph* as sorted node lists.

    Computes strongly-connected components (iterative Tarjan, so deep graphs
    never blow the recursion limit) and reports every SCC of size > 1, plus any
    explicit self-loop, as a cycle. Each cycle is a sorted node list and the
    list of cycles is itself deterministically ordered; an acyclic graph returns
    ``[]``.
    """
    adjacency, nodes, self_loops = _build_adjacency(graph)

    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    stack: list[str] = []
    counter = 0
    cycles: list[list[str]] = []

    for root in sorted(nodes):
        if root in indices:
            continue
        work: list[tuple[str, int]] = [(root, 0)]
        while work:
            node, next_child = work[-1]
            if next_child == 0:
                indices[node] = lowlink[node] = counter
                counter += 1
                stack.append(node)
                on_stack[node] = True

            neighbors = adjacency.get(node, ())
            descended = False
            for index in range(next_child, len(neighbors)):
                neighbor = neighbors[index]
                if neighbor not in indices:
                    work[-1] = (node, index + 1)
                    work.append((neighbor, 0))
                    descended = True
                    break
                if on_stack.get(neighbor):
                    lowlink[node] = min(lowlink[node], indices[neighbor])
            if descended:
                continue

            if lowlink[node] == indices[node]:
                component: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack[member] = False
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1:
                    cycles.append(sorted(component))

            work.pop()
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[node])

    cycles.extend([node] for node in self_loops)
    cycles.sort()
    return cycles


# ── Fan-in / fan-out metrics (DL-103) ─────────────────────────────────


def dependency_metrics(graph: dict) -> dict:
    """Compute per-module fan-in/fan-out counts and a most-depended ranking.

    ``fan_out`` is the number of internal modules a file depends on; ``fan_in``
    is the number of internal modules that depend on it. Returns
    ``{"metrics": {file: {"fan_in", "fan_out"}}, "most_depended_on": [file, ...]}``
    where the ranking is by descending fan-in with an alphabetical tie-break.
    Counts match the edge list and the output is deterministic.
    """
    fan_in: defaultdict[str, int] = defaultdict(int)
    fan_out: defaultdict[str, int] = defaultdict(int)
    modules: set[str] = set(graph.get("nodes", []))

    for source, target in graph.get("edges", []):
        modules.add(source)
        modules.add(target)
        fan_out[source] += 1
        fan_in[target] += 1

    metrics = {
        module: {"fan_in": fan_in[module], "fan_out": fan_out[module]}
        for module in sorted(modules)
    }
    most_depended_on = sorted(modules, key=lambda m: (-fan_in[m], m))
    return {"metrics": metrics, "most_depended_on": most_depended_on}


# ══ Load / startup order (Epic 2.3) ═══════════════════════════════════════


def _condense(
    graph: dict,
) -> tuple[dict[str, str], dict[str, list[str]], list[list[str]]]:
    """Condense the graph's strongly-connected components into super-nodes.

    Returns ``(node_to_component, components, cycle_groups)`` where every node
    maps to a component representative (the smallest member), ``components``
    lists each representative's sorted members, and ``cycle_groups`` are the
    multi-module SCCs whose internal load order is indeterminate.
    """
    nodes: set[str] = set(graph.get("nodes", []))
    for source, target in graph.get("edges", []):
        nodes.add(source)
        nodes.add(target)

    node_to_component: dict[str, str] = {}
    components: dict[str, list[str]] = {}
    for cycle in detect_cycles(graph):  # SCCs (size > 1) and explicit self-loops
        representative = cycle[0]  # cycles are sorted, so this is the smallest
        components[representative] = list(cycle)
        for node in cycle:
            node_to_component[node] = representative
    for node in nodes:
        if node not in node_to_component:
            node_to_component[node] = node
            components[node] = [node]

    cycle_groups = [members for members in components.values() if len(members) > 1]
    cycle_groups.sort()
    return node_to_component, components, cycle_groups


def topological_order(graph: dict) -> dict:
    """Order modules so each loads after the internal modules it imports.

    Strongly-connected components (import cycles) are condensed into single
    nodes, the resulting DAG is Kahn-sorted with an alphabetical tie-break for
    determinism, then each component is expanded in sorted order. An edge
    ``(importer, imported)`` places ``imported`` before ``importer`` — the
    dependency loads first. Returns ``{"order": [files...], "cycle_groups":
    [[files...]]}`` where each cyclic group is surfaced (its members listed
    sorted and adjacent) rather than silently dropped, since their relative load
    order is indeterminate. Deterministic; isolated modules still appear.
    """
    node_to_component, components, cycle_groups = _condense(graph)

    # Condensed dependency edges: for importer→imported, the imported
    # component must load before the importer component.
    adjacency: defaultdict[str, set[str]] = defaultdict(set)
    for importer, imported in graph.get("edges", []):
        src, dst = node_to_component[imported], node_to_component[importer]
        if src != dst:
            adjacency[src].add(dst)

    indegree: dict[str, int] = {component: 0 for component in components}
    for dependents in adjacency.values():
        for dependent in dependents:
            indegree[dependent] += 1

    ready = [component for component in components if indegree[component] == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        component = heapq.heappop(ready)
        order.extend(sorted(components[component]))
        for dependent in sorted(adjacency.get(component, ())):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)

    return {"order": order, "cycle_groups": cycle_groups}


# Heuristic factory / dependency-wiring function names. ``create_*`` builds an
# app/server object; the rest configure or register wiring at import or setup
# time. Matching is best-effort (names only), tagged as such by the caller.
_FACTORY_PREFIXES: tuple[str, ...] = ("create_",)
_WIRING_NAMES: frozenset[str] = frozenset({"configure", "setup", "wire"})
_WIRING_PREFIXES: tuple[str, ...] = ("register_", "configure_", "setup_", "wire_")


def _factory_kind(name: str) -> str:
    """Classify a function name as a ``"factory"``, ``"wiring"`` helper, or ``""``."""
    if name.startswith(_FACTORY_PREFIXES):
        return "factory"
    if name in _WIRING_NAMES or name.startswith(_WIRING_PREFIXES):
        return "wiring"
    return ""


def detect_side_effects(inventory: dict) -> dict:
    """List import-time side effects and factory/wiring functions per module.

    Reads the deep extractor's ``module_calls`` (DL-301) to report each module's
    top-level side effects, and flags top-level functions whose names match the
    app-factory / dependency-wiring heuristics (``create_app``, ``configure``,
    ``setup``, ``wire``, ``register_*``, …). Returns ``{"side_effects":
    [{file, calls}], "factories": [{file, symbol, kind}], "best_effort": True}``,
    both lists deterministically ordered. The detection is name-based and
    therefore advisory, hence ``best_effort``. A module with no module-level
    calls contributes no side-effect entry; absence of optional fields never
    raises.
    """
    side_effects: list[dict] = []
    factories: list[dict] = []
    for filepath in sorted(inventory):
        data = inventory[filepath]
        if not isinstance(data, dict):
            continue
        calls = data.get("module_calls") or []
        if calls:
            side_effects.append({"file": filepath, "calls": calls})
        for fn in data.get("functions", []):
            kind = _factory_kind(fn.get("name", ""))
            if kind:
                factories.append({"file": filepath, "symbol": fn["name"], "kind": kind})

    factories.sort(key=lambda f: (f["file"], f["symbol"]))
    return {"side_effects": side_effects, "factories": factories, "best_effort": True}


# ══ External dependency reconciliation (Epic 2.2) ═════════════════════════
#
# Each language pairs a *manifest parser* (declared dependencies) with an
# *import classifier* (import string → external package name, or ``None`` to
# exclude an internal/relative/stdlib import) behind the shared dispatcher
# below. A parsed manifest is carried as a :class:`_Manifest`; the classifier
# receives it so language-specific exclusions (Go's own-module prefix, the
# Python alias override) stay accurate, and degrades when it is absent.


@dataclass(frozen=True)
class _ManifestScope:
    """A scoped dependency manifest rooted at a project-relative directory."""

    root: str
    required: frozenset[str]
    optional: frozenset[str]
    aliases: Optional[dict[str, str]] = None
    distribution: str = ""
    import_roots: frozenset[str] = frozenset()
    own_module: str = ""
    internal_modules: frozenset[str] = frozenset()


@dataclass(frozen=True)
class _Manifest:
    """A language's declared dependencies, parsed from its manifest.

    ``required`` are runtime dependencies; ``optional`` are extras/dev/build
    dependencies (never counted "unused"). The remaining fields are
    language-specific context for classification and default to inert values:
    ``own_module``/``internal_modules`` exclude Go intra-module imports, and
    ``aliases`` is the Python import→distribution map for project-local
    distributions. Python ``[tool.llm-wiki] dependency-aliases`` overrides live
    on matching scopes so nearest manifests can win. ``scopes`` is used by
    languages where nested manifests apply only to files below their directory.
    """

    required: frozenset[str]
    optional: frozenset[str]
    own_module: str = ""
    internal_modules: frozenset[str] = frozenset()
    aliases: Optional[dict[str, str]] = None
    scopes: tuple[_ManifestScope, ...] = ()


@dataclass(frozen=True)
class _LanguagePlugin:
    """A manifest parser + import classifier for one language family."""

    key: str  # canonical language label used in the reconciliation output
    languages: tuple[str, ...]  # inventory ``language`` values this handles
    parse: Callable[[Path, SourceSnapshot], "Optional[_Manifest]"]
    classify: Callable[[str, str, str, "Optional[_Manifest]"], "Optional[str]"]


# ── Python (DL-201) ───────────────────────────────────────────────────


# Import top-level name → distribution name where they differ. Keys are the
# (case-sensitive) import names; values are normalized to PEP 503 form on use.
_PYTHON_ALIASES: dict[str, str] = {
    "yaml": "pyyaml",
    "PIL": "pillow",
    "cv2": "opencv-python",
    "bs4": "beautifulsoup4",
    "sklearn": "scikit-learn",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "OpenSSL": "pyopenssl",
    "Crypto": "pycryptodome",
    "git": "gitpython",
    "jose": "python-jose",
    "jwt": "pyjwt",
    "serial": "pyserial",
    "usb": "pyusb",
    "attr": "attrs",
    "MySQLdb": "mysqlclient",
    "psycopg2": "psycopg2-binary",
    "win32com": "pywin32",
    "grpc": "grpcio",
    "grpc_health": "grpcio-health-checking",
    "riva": "nvidia-riva-client",
    "pyannote": "pyannote.audio",
    "prometheus_client": "prometheus-client",
    "pydantic_settings": "pydantic-settings",
}

# Bundled fallback for ``sys.stdlib_module_names`` (added in 3.10). Top-level
# standard-library module names for Python 3.9; used only on 3.9 so a stdlib
# import is never misreported as an undeclared external dependency.
_PYTHON_STDLIB_FALLBACK: frozenset[str] = frozenset(
    {
        "__future__",
        "_thread",
        "abc",
        "aifc",
        "argparse",
        "array",
        "ast",
        "asynchat",
        "asyncio",
        "asyncore",
        "atexit",
        "audioop",
        "base64",
        "bdb",
        "binascii",
        "bisect",
        "builtins",
        "bz2",
        "cProfile",
        "calendar",
        "cgi",
        "cgitb",
        "chunk",
        "cmath",
        "cmd",
        "code",
        "codecs",
        "codeop",
        "collections",
        "colorsys",
        "compileall",
        "concurrent",
        "configparser",
        "contextlib",
        "contextvars",
        "copy",
        "copyreg",
        "crypt",
        "csv",
        "ctypes",
        "curses",
        "dataclasses",
        "datetime",
        "dbm",
        "decimal",
        "difflib",
        "dis",
        "distutils",
        "doctest",
        "email",
        "encodings",
        "ensurepip",
        "enum",
        "errno",
        "faulthandler",
        "fcntl",
        "filecmp",
        "fileinput",
        "fnmatch",
        "fractions",
        "ftplib",
        "functools",
        "gc",
        "genericpath",
        "getopt",
        "getpass",
        "gettext",
        "glob",
        "graphlib",
        "grp",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "idlelib",
        "imaplib",
        "imghdr",
        "imp",
        "importlib",
        "inspect",
        "io",
        "ipaddress",
        "itertools",
        "json",
        "keyword",
        "lib2to3",
        "linecache",
        "locale",
        "logging",
        "lzma",
        "mailbox",
        "mailcap",
        "marshal",
        "math",
        "mimetypes",
        "mmap",
        "modulefinder",
        "msilib",
        "msvcrt",
        "multiprocessing",
        "netrc",
        "nis",
        "nntplib",
        "nt",
        "ntpath",
        "nturl2path",
        "numbers",
        "opcode",
        "operator",
        "optparse",
        "os",
        "ossaudiodev",
        "pathlib",
        "pdb",
        "pickle",
        "pickletools",
        "pipes",
        "pkgutil",
        "platform",
        "plistlib",
        "poplib",
        "posix",
        "posixpath",
        "pprint",
        "profile",
        "pstats",
        "pty",
        "pwd",
        "py_compile",
        "pyclbr",
        "pydoc",
        "pyexpat",
        "queue",
        "quopri",
        "random",
        "re",
        "readline",
        "reprlib",
        "resource",
        "rlcompleter",
        "runpy",
        "sched",
        "secrets",
        "select",
        "selectors",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "smtpd",
        "smtplib",
        "sndhdr",
        "socket",
        "socketserver",
        "spwd",
        "sqlite3",
        "ssl",
        "stat",
        "statistics",
        "string",
        "stringprep",
        "struct",
        "subprocess",
        "sunau",
        "symtable",
        "sys",
        "sysconfig",
        "syslog",
        "tabnanny",
        "tarfile",
        "telnetlib",
        "tempfile",
        "termios",
        "test",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "tkinter",
        "token",
        "tokenize",
        "trace",
        "traceback",
        "tracemalloc",
        "tty",
        "turtle",
        "turtledemo",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uu",
        "uuid",
        "venv",
        "warnings",
        "wave",
        "weakref",
        "webbrowser",
        "winreg",
        "winsound",
        "wsgiref",
        "xdrlib",
        "xml",
        "xmlrpc",
        "zipapp",
        "zipfile",
        "zipimport",
        "zlib",
        "zoneinfo",
    }
)


def _python_stdlib() -> frozenset[str]:
    names = getattr(sys, "stdlib_module_names", None)
    return frozenset(names) if names else _PYTHON_STDLIB_FALLBACK


def _normalize_python(name: str) -> str:
    """PEP 503 normalization: lowercase, runs of ``-``/``_``/``.`` → ``-``."""
    return re.sub(r"[-_.]+", "-", name.strip().lower()).strip("-")


def _pep508_name(spec: str) -> str:
    """Distribution name from a PEP 508 requirement (drops version/markers/extras)."""
    head = spec.split(";", 1)[0].strip()
    match = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", head)
    return match.group(0) if match else ""


def _snapshot_package_marker_paths(
    project_root: Path,
    source_snapshot: SourceSnapshot,
    predicate: Callable[[str], bool],
) -> list[Path]:
    paths: list[Path] = []
    for marker in source_snapshot.package_markers:
        if not predicate(marker.abs_path.name):
            continue
        try:
            marker.abs_path.relative_to(project_root)
        except ValueError:
            continue
        paths.append(marker.abs_path)
    return sorted(paths, key=lambda path: path.relative_to(project_root).as_posix())


_PYTHON_MANIFEST_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".cache",
        ".eggs",
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "env",
        "node_modules",
        "site-packages",
        "venv",
        "vendor",
    }
)


def _is_python_requirements_manifest_name(name: str) -> bool:
    return name.startswith("requirements") and name.endswith(".txt")


def _is_python_manifest_name(name: str) -> bool:
    return name == "pyproject.toml" or _is_python_requirements_manifest_name(name)


def _walk_python_manifest_files(
    project_root: Path, source_snapshot: SourceSnapshot | None = None
) -> list[Path]:
    if source_snapshot is not None:
        return _snapshot_package_marker_paths(
            project_root, source_snapshot, _is_python_manifest_name
        )

    paths: list[Path] = []
    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        dirs[:] = [
            d
            for d in dirs
            if d not in _PYTHON_MANIFEST_EXCLUDED_DIRS
            and not d.endswith((".egg-info", ".dist-info"))
            and not _manifest_dir_is_agent_worktree(project_root, root_path, d)
        ]
        if "pyproject.toml" in files:
            paths.append(root_path / "pyproject.toml")
        paths.extend(
            root_path / name
            for name in files
            if _is_python_requirements_manifest_name(name)
        )
    return sorted(paths, key=lambda p: p.relative_to(project_root).as_posix())


def _manifest_dir_is_agent_worktree(
    project_root: Path, root_path: Path, dirname: str
) -> bool:
    try:
        rel = (root_path / dirname).relative_to(project_root).as_posix()
    except ValueError:
        return False
    return is_agent_worktree_path(rel)


def _python_scope_root(project_root: Path, path: Path) -> str:
    rel = path.parent.relative_to(project_root)
    return "" if rel.as_posix() == "." else rel.as_posix()


def _discover_python_local_modules(
    project_root: Path,
    source_snapshot: SourceSnapshot,
) -> frozenset[str]:
    if source_snapshot.source_selection_policy is not None:
        modules: set[str] = set()
        for source_file in source_snapshot.files_by_language.get("python", ()):
            parts = Path(source_file.rel_path).parts
            if len(parts) == 1 and source_file.suffix == ".py":
                modules.add(Path(parts[0]).stem)
            elif len(parts) == 2 and parts[1] == "__init__.py":
                modules.add(parts[0])
        return frozenset(sorted(modules))

    modules: set[str] = set()
    try:
        children = list(project_root.iterdir())
    except OSError:
        return frozenset()
    for child in children:
        if child.name.startswith("."):
            continue
        if child.is_file() and child.suffix == ".py":
            modules.add(child.stem)
        elif child.is_dir() and (child / "__init__.py").is_file():
            modules.add(child.name)
    return frozenset(modules)


def _requirements_optional(path: Path) -> bool:
    name = path.name.lower()
    return name != "requirements.txt" and any(
        marker in name for marker in ("dev", "test", "tests")
    )


def _requirement_name(spec: str) -> str:
    if "#egg=" in spec:
        egg = spec.split("#egg=", 1)[1].split("&", 1)[0]
        return egg.strip()
    return _pep508_name(spec)


def _parse_requirements_file(path: Path) -> tuple[set[str], set[str]]:
    required: set[str] = set()
    optional: set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return required, optional

    target = optional if _requirements_optional(path) else required
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith(("-r", "--requirement", "-c", "--constraint", "-e")):
            continue
        if line.startswith(("git+", "http://", "https://")) and "#egg=" not in raw:
            continue
        name = _normalize_python(_requirement_name(line))
        if name:
            target.add(name)
    return required, optional


def _python_package_import_roots(
    path: Path,
    data: dict,
    project_root: Path,
    source_snapshot: SourceSnapshot,
) -> frozenset[str]:
    roots: set[str] = set()
    tool = data.get("tool", {})
    setuptools = tool.get("setuptools", {}) if isinstance(tool, dict) else {}
    packages = setuptools.get("packages", {}) if isinstance(setuptools, dict) else {}
    find = packages.get("find", {}) if isinstance(packages, dict) else {}
    raw_wheres = find.get("where", [""]) if isinstance(find, dict) else [""]
    if isinstance(raw_wheres, str):
        wheres = [raw_wheres]
    elif isinstance(raw_wheres, list):
        wheres = [str(where) for where in raw_wheres if isinstance(where, str)]
    else:
        wheres = [""]

    selected_python_paths = {
        source_file.rel_path
        for source_file in source_snapshot.files_by_language.get("python", ())
    }
    configured = source_snapshot.source_selection_policy is not None
    for where in wheres or [""]:
        base = (path.parent / where).resolve()
        if configured:
            try:
                base_rel_path = base.relative_to(project_root)
            except ValueError:
                continue
            base_rel = (
                "" if base_rel_path.as_posix() == "." else base_rel_path.as_posix()
            )
            base_init = f"{base_rel}/__init__.py" if base_rel else "__init__.py"
            if base_init in selected_python_paths:
                roots.add(base.name)
            prefix = f"{base_rel}/" if base_rel else ""
            for selected_path in selected_python_paths:
                if not selected_path.startswith(prefix):
                    continue
                remainder = selected_path[len(prefix) :]
                parts = remainder.split("/")
                if len(parts) == 2 and parts[1] == "__init__.py":
                    roots.add(parts[0])
            continue
        if not base.is_dir():
            continue
        if (base / "__init__.py").is_file():
            roots.add(base.name)
        try:
            children = list(base.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_dir() and (child / "__init__.py").is_file():
                roots.add(child.name)
    return frozenset(sorted(roots))


def _python_import_name_from_distribution(name: str) -> str:
    return re.sub(r"[-.]+", "_", name.strip()).strip("_")


def _parse_python_pyproject(
    path: Path,
    project_root: Path,
    source_snapshot: SourceSnapshot,
) -> tuple[set[str], set[str], dict[str, str], str, frozenset[str]]:
    data = _load_toml(path)
    if data is None:
        return set(), set(), {}, "", frozenset()
    project = data.get("project", {})
    project = project if isinstance(project, dict) else {}
    project_name = str(project.get("name", "") or "")

    required = {
        n
        for dep in project.get("dependencies", []) or []
        if isinstance(dep, str) and (n := _normalize_python(_pep508_name(dep)))
    }
    optional: set[str] = set()
    extras = project.get("optional-dependencies", {})
    if isinstance(extras, dict):
        for group in extras.values():
            optional |= {
                n
                for dep in group or []
                if isinstance(dep, str) and (n := _normalize_python(_pep508_name(dep)))
            }

    tool = data.get("tool", {})
    override = (
        tool.get("llm-wiki", {}).get("dependency-aliases", {})
        if isinstance(tool, dict)
        else {}
    )
    aliases = (
        {str(k): str(v) for k, v in override.items()}
        if isinstance(override, dict)
        else {}
    )
    import_roots = _python_package_import_roots(
        path,
        data,
        project_root,
        source_snapshot,
    )
    if project_name and not import_roots:
        fallback = _python_import_name_from_distribution(project_name)
        import_roots = frozenset({fallback}) if fallback else frozenset()
    return required, optional, aliases, project_name, import_roots


def _parse_python_manifest(
    project_root: Path, source_snapshot: SourceSnapshot
) -> Optional[_Manifest]:
    scoped_required: defaultdict[str, set[str]] = defaultdict(set)
    scoped_optional: defaultdict[str, set[str]] = defaultdict(set)
    scoped_aliases: defaultdict[str, dict[str, str]] = defaultdict(dict)
    scoped_import_roots: defaultdict[str, set[str]] = defaultdict(set)
    scoped_distributions: dict[str, str] = {}
    local_aliases: dict[str, str] = {}

    for path in _walk_python_manifest_files(project_root, source_snapshot):
        root = _python_scope_root(project_root, path)
        if path.name == "pyproject.toml":
            (
                required,
                optional,
                manifest_aliases,
                project_name,
                import_roots,
            ) = _parse_python_pyproject(path, project_root, source_snapshot)
            scoped_aliases[root].update(manifest_aliases)
            distribution = _normalize_python(project_name)
            if distribution:
                scoped_distributions[root] = distribution
                scoped_import_roots[root].update(import_roots)
                for import_root in import_roots:
                    local_aliases.setdefault(import_root, distribution)
        else:
            required, optional = _parse_requirements_file(path)
        scoped_required[root].update(required)
        scoped_optional[root].update(optional)

    if not scoped_required and not scoped_optional:
        return None

    scopes = tuple(
        _ManifestScope(
            root=root,
            required=frozenset(scoped_required[root]),
            optional=frozenset(scoped_optional[root]),
            aliases=dict(scoped_aliases[root]) or None,
            distribution=scoped_distributions.get(root, ""),
            import_roots=frozenset(scoped_import_roots[root]),
        )
        for root in sorted(set(scoped_required) | set(scoped_optional))
    )
    required = frozenset().union(*(scope.required for scope in scopes))
    optional = frozenset().union(*(scope.optional for scope in scopes))
    return _Manifest(
        required,
        optional,
        aliases=local_aliases,
        scopes=scopes,
        internal_modules=_discover_python_local_modules(
            project_root,
            source_snapshot,
        ),
    )


def _python_aliases_for_file(
    manifest: Optional[_Manifest], filepath: str
) -> dict[str, str]:
    aliases = dict(_PYTHON_ALIASES)
    if manifest and manifest.aliases:
        aliases.update(manifest.aliases)
    if manifest:
        scopes = [
            scope
            for scope in manifest.scopes
            if _path_under_scope(filepath, scope.root) and scope.aliases
        ]
        for scope in sorted(
            scopes, key=lambda item: (item.root.count("/"), len(item.root))
        ):
            aliases.update(scope.aliases or {})
    return aliases


def _classify_python(
    module: str, name: str, filepath: str, manifest: Optional[_Manifest]
) -> Optional[str]:
    module = module or ""
    if not module or module.startswith("."):
        return None  # relative / unresolved-relative import
    top = module.split(".", 1)[0]
    if not top or top in _python_stdlib():
        return None
    if manifest and top in manifest.internal_modules:
        return None
    aliases = _python_aliases_for_file(manifest, filepath)
    return _normalize_python(aliases.get(top, top))


# ── TypeScript / JavaScript (DL-202) ──────────────────────────────────


_NODE_BUILTINS: frozenset[str] = frozenset(
    {
        "assert",
        "async_hooks",
        "buffer",
        "child_process",
        "cluster",
        "console",
        "constants",
        "crypto",
        "dgram",
        "diagnostics_channel",
        "dns",
        "domain",
        "events",
        "fs",
        "http",
        "http2",
        "https",
        "inspector",
        "module",
        "net",
        "os",
        "path",
        "perf_hooks",
        "process",
        "punycode",
        "querystring",
        "readline",
        "repl",
        "stream",
        "string_decoder",
        "sys",
        "timers",
        "tls",
        "trace_events",
        "tty",
        "url",
        "util",
        "v8",
        "vm",
        "wasi",
        "worker_threads",
        "zlib",
    }
)


_TS_MANIFEST_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".cache",
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "env",
        "node_modules",
        "venv",
    }
)


def _walk_ts_manifest_files(
    project_root: Path, source_snapshot: SourceSnapshot | None = None
) -> list[Path]:
    if source_snapshot is not None:
        return _snapshot_package_marker_paths(
            project_root, source_snapshot, lambda name: name == "package.json"
        )

    paths: list[Path] = []
    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        dirs[:] = [
            d
            for d in dirs
            if d not in _TS_MANIFEST_EXCLUDED_DIRS
            and not _manifest_dir_is_agent_worktree(project_root, root_path, d)
        ]
        if "package.json" in files:
            paths.append(root_path / "package.json")
    return sorted(paths, key=lambda path: path.relative_to(project_root).as_posix())


def _ts_scope_root(project_root: Path, path: Path) -> str:
    rel = path.parent.relative_to(project_root)
    return "" if rel.as_posix() == "." else rel.as_posix()


def _parse_ts_package_json(path: Path) -> Optional[tuple[set[str], set[str]]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None

    def _keys(section: str) -> set[str]:
        block = data.get(section, {})
        return {k.lower() for k in block} if isinstance(block, dict) else set()

    required = _keys("dependencies") | _keys("peerDependencies")
    optional = _keys("devDependencies") | _keys("optionalDependencies")
    return required, optional


def _parse_ts_manifest(
    project_root: Path, source_snapshot: SourceSnapshot
) -> Optional[_Manifest]:
    scoped_required: defaultdict[str, set[str]] = defaultdict(set)
    scoped_optional: defaultdict[str, set[str]] = defaultdict(set)

    for path in _walk_ts_manifest_files(project_root, source_snapshot):
        root = _ts_scope_root(project_root, path)
        parsed = _parse_ts_package_json(path)
        if parsed is None:
            continue
        required, optional = parsed
        scoped_required[root].update(required)
        scoped_optional[root].update(optional)

    if not scoped_required and not scoped_optional:
        return None

    scopes = tuple(
        _ManifestScope(
            root=root,
            required=frozenset(scoped_required[root]),
            optional=frozenset(scoped_optional[root]),
        )
        for root in sorted(set(scoped_required) | set(scoped_optional))
    )
    required = frozenset().union(*(scope.required for scope in scopes))
    optional = frozenset().union(*(scope.optional for scope in scopes))
    return _Manifest(required, optional, scopes=scopes)


def _classify_ts(
    module: str, name: str, filepath: str, manifest: Optional[_Manifest]
) -> Optional[str]:
    spec = (module or "").strip()
    if not spec or spec.startswith((".", "/")):
        return None  # relative
    if spec.startswith("node:"):
        return None  # explicit Node builtin
    if spec.startswith("@"):
        parts = spec.split("/")
        pkg = "/".join(parts[:2]) if len(parts) >= 2 else spec
    else:
        pkg = spec.split("/", 1)[0]
    if pkg in _NODE_BUILTINS:
        return None
    return pkg.lower()


# ── Go (DL-203) ───────────────────────────────────────────────────────


_GO_MANIFEST_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".cache",
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "env",
        "node_modules",
        "site-packages",
        "target",
        "venv",
        "vendor",
    }
)


def _walk_go_manifest_files(
    project_root: Path, source_snapshot: SourceSnapshot | None = None
) -> list[Path]:
    if source_snapshot is not None:
        return _snapshot_package_marker_paths(
            project_root, source_snapshot, lambda name: name == "go.mod"
        )

    paths: list[Path] = []
    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        dirs[:] = [
            d
            for d in dirs
            if d not in _GO_MANIFEST_EXCLUDED_DIRS
            and not _manifest_dir_is_agent_worktree(project_root, root_path, d)
        ]
        if "go.mod" in files:
            paths.append(root_path / "go.mod")
    return sorted(paths, key=lambda path: path.relative_to(project_root).as_posix())


def _go_scope_root(project_root: Path, path: Path) -> str:
    rel = path.parent.relative_to(project_root)
    return "" if rel.as_posix() == "." else rel.as_posix()


def _parse_go_mod_file(path: Path) -> tuple[str, set[str], set[str], set[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "", set(), set(), set()

    own_module = ""
    required: set[str] = set()
    optional: set[str] = set()
    replaced_to_local: set[str] = set()
    in_require_block = False

    for raw in text.splitlines():
        line, _, comment = raw.partition("//")
        line = line.strip()
        if not line:
            continue
        if in_require_block:
            if line.startswith(")"):
                in_require_block = False
            else:
                module_path, indirect = _go_require_entry(line, comment)
                if module_path:
                    (optional if indirect else required).add(module_path)
            continue
        if line.startswith("module "):
            own_module = line.split(None, 1)[1].strip().strip('"')
        elif line.startswith("replace"):
            old, target = _parse_go_replace(line)
            if old and _is_local_path(target):
                replaced_to_local.add(old)
        elif line.startswith("require"):
            rest = line[len("require") :].strip()
            if rest.startswith("("):
                in_require_block = True
            else:
                module_path, indirect = _go_require_entry(rest, comment)
                if module_path:
                    (optional if indirect else required).add(module_path)

    internal = replaced_to_local & (required | optional)
    required -= internal
    optional -= internal
    return own_module, required, optional, internal


def _parse_go_manifest(
    project_root: Path, source_snapshot: SourceSnapshot
) -> Optional[_Manifest]:
    scopes: list[_ManifestScope] = []
    for path in _walk_go_manifest_files(project_root, source_snapshot):
        own_module, required, optional, internal = _parse_go_mod_file(path)
        if not own_module and not required and not optional and not internal:
            continue
        scopes.append(
            _ManifestScope(
                root=_go_scope_root(project_root, path),
                required=frozenset(required),
                optional=frozenset(optional),
                own_module=own_module,
                internal_modules=frozenset(internal),
            )
        )

    if not scopes:
        return None

    scopes = sorted(scopes, key=lambda item: (item.root.count("/"), len(item.root)))
    required = frozenset().union(*(scope.required for scope in scopes))
    optional = frozenset().union(*(scope.optional for scope in scopes))
    internal = frozenset().union(*(scope.internal_modules for scope in scopes))
    root_scope = next((scope for scope in scopes if scope.root == ""), None)
    return _Manifest(
        required,
        optional,
        own_module=root_scope.own_module if root_scope else "",
        internal_modules=internal,
        scopes=tuple(scopes),
    )


def _go_require_path(line: str) -> str:
    """First whitespace-delimited token of a ``require`` line: the module path."""
    return _go_require_entry(line, "")[0]


def _go_require_entry(line: str, comment: str) -> tuple[str, bool]:
    """Return ``(module_path, is_indirect)`` for a ``require`` entry."""
    tokens = line.split()
    path = tokens[0] if tokens else ""
    return path, "indirect" in comment.split()


def _parse_go_replace(line: str) -> tuple[str, str]:
    body = line[len("replace") :].strip().lstrip("(").strip()
    if "=>" not in body:
        return "", ""
    left, _, right = body.partition("=>")
    return left.split()[0] if left.split() else "", right.strip().split()[
        0
    ] if right.strip().split() else ""


def _is_local_path(target: str) -> bool:
    return target.startswith((".", "/")) or "." not in target.split("/", 1)[0]


def _go_default_module(path: str) -> str:
    """Heuristic module key when no ``go.mod`` is available: ``host/org/repo``."""
    segments = path.split("/")
    return "/".join(segments[:3]) if len(segments) >= 3 else path


def _classify_go(
    module: str, name: str, filepath: str, manifest: Optional[_Manifest]
) -> Optional[str]:
    path = (module or "").strip().strip('"')
    if not path:
        return None
    if "." not in path.split("/", 1)[0]:
        return None  # stdlib (e.g. ``fmt``, ``net/http``)
    if manifest is not None:
        scope = _nearest_manifest_scope(manifest, filepath)
        own_module = scope.own_module if scope else manifest.own_module
        internal_modules = (
            scope.internal_modules if scope else manifest.internal_modules
        )
        required = scope.required if scope else manifest.required
        optional = scope.optional if scope else manifest.optional
        if own_module and _path_under(path, own_module):
            return None  # intra-module import
        if any(_path_under(path, m) for m in internal_modules):
            return None  # replaced to a local path
        best = ""
        for dep in required | optional:
            if _path_under(path, dep) and len(dep) > len(best):
                best = dep
        if best:
            return best
    return _go_default_module(path)


def _path_under(path: str, prefix: str) -> bool:
    return shared_path_is_under(path, prefix)


# ── Rust (DL-204) ─────────────────────────────────────────────────────


_RUST_INTERNAL_ROOTS: frozenset[str] = frozenset(
    {"crate", "self", "super", "std", "core", "alloc"}
)


def _normalize_rust(name: str) -> str:
    """Rust crate names are interchangeable across ``-``/``_``; canonicalize."""
    return name.strip().lower().replace("-", "_")


def _parse_rust_manifest(
    project_root: Path, source_snapshot: SourceSnapshot
) -> Optional[_Manifest]:
    def _keys(data: dict, section: str) -> set[str]:
        block = data.get(section, {})
        # The dependency-table *key* is the name used in ``use`` (``package =``
        # only renames the published crate), so reconcile against the key.
        return {_normalize_rust(k) for k in block} if isinstance(block, dict) else set()

    paths = (
        _snapshot_package_marker_paths(
            project_root,
            source_snapshot,
            lambda name: name == "Cargo.toml",
        )
        if source_snapshot.source_selection_policy is not None
        else [project_root / "Cargo.toml"]
    )
    required: set[str] = set()
    optional: set[str] = set()
    for path in paths:
        current_data = _load_toml(path)
        if current_data is None:
            continue
        required.update(_keys(current_data, "dependencies"))
        optional.update(_keys(current_data, "dev-dependencies"))
        optional.update(_keys(current_data, "build-dependencies"))
    if not required and not optional:
        return None
    return _Manifest(frozenset(required), frozenset(optional))


def _classify_rust(
    module: str, name: str, filepath: str, manifest: Optional[_Manifest]
) -> Optional[str]:
    path = (module or "").strip()
    if not path:
        return None
    crate = path.split("::", 1)[0]
    if not crate or crate in _RUST_INTERNAL_ROOTS:
        return None
    return _normalize_rust(crate)


# ── Haskell (DL-205) ──────────────────────────────────────────────────


_HASKELL_MANIFEST_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".cache",
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".stack-work",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "dist-newstyle",
        "env",
        "node_modules",
        "site-packages",
        "target",
        "venv",
        "vendor",
    }
)
_HASKELL_MANIFEST_NAMES = {"cabal.project", "flake.nix", "stack.yaml"}
_CABAL_FIELD_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9-]*)\s*:\s*(.*)$")
_CABAL_STANZA_RE = re.compile(
    r"^\s*(benchmark|common|custom-setup|executable|foreign-library|library|"
    r"test-suite)\b",
    re.IGNORECASE,
)
_CABAL_OPTIONAL_STANZAS = {"benchmark", "custom-setup", "test-suite"}
_STACK_FIELD_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*)$")
_NIX_HASKELL_PACKAGE_SKIP_NAMES = frozenset(
    {
        "callCabal2nix",
        "callHackage",
        "developPackage",
        "ghcWithPackages",
        "override",
        "shellFor",
    }
)


def _is_haskell_manifest_file_name(name: str) -> bool:
    return name in _HASKELL_MANIFEST_NAMES or name.endswith(".cabal")


def _walk_haskell_manifest_files(
    project_root: Path, source_snapshot: SourceSnapshot | None = None
) -> list[Path]:
    if source_snapshot is not None:
        return _snapshot_package_marker_paths(
            project_root, source_snapshot, _is_haskell_manifest_file_name
        )

    paths: list[Path] = []
    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        dirs[:] = [
            d
            for d in dirs
            if d not in _HASKELL_MANIFEST_EXCLUDED_DIRS
            and not _manifest_dir_is_agent_worktree(project_root, root_path, d)
        ]
        paths.extend(
            root_path / name for name in files if _is_haskell_manifest_file_name(name)
        )
    return sorted(paths, key=lambda path: path.relative_to(project_root).as_posix())


def _haskell_scope_root(project_root: Path, path: Path) -> str:
    rel = path.parent.relative_to(project_root)
    return "" if rel.as_posix() == "." else rel.as_posix()


def _strip_haskell_line_comment(raw: str) -> str:
    return raw.split("--", 1)[0].rstrip()


def _normalize_haskell_package(name: str) -> str:
    match = re.match(r"[A-Za-z0-9][A-Za-z0-9_-]*", name.strip().strip("'\"`"))
    if not match:
        return ""
    return match.group(0).lower().replace("_", "-")


def _haskell_package_name_from_spec(spec: str) -> str:
    clean = spec.strip().strip(",").strip().strip("'\"`")
    if not clean or clean.startswith((".", "/", "\\")):
        return ""
    if re.match(r"^[A-Za-z0-9_-]+\s*:", clean):
        return ""

    head = clean.split(None, 1)[0].strip(",")
    versioned = re.match(r"^([A-Za-z0-9][A-Za-z0-9_-]*?)-\d+(?:[.\-]|$)", head)
    if versioned:
        return _normalize_haskell_package(versioned.group(1))
    return _normalize_haskell_package(head)


def _haskell_packages_from_specs(specs: list[str]) -> set[str]:
    packages: set[str] = set()
    for chunk in " ".join(specs).split(","):
        package = _haskell_package_name_from_spec(chunk)
        if package:
            packages.add(package)
    return packages


def _cabal_stanza(clean_line: str) -> str:
    match = _CABAL_STANZA_RE.match(clean_line)
    return match.group(1).lower() if match else ""


def _cabal_package_name(lines: list[str]) -> str:
    for raw in lines:
        clean = _strip_haskell_line_comment(raw)
        if not clean.strip():
            continue
        if _cabal_stanza(clean):
            return ""
        field = _CABAL_FIELD_RE.match(clean)
        if field and field.group(1).lower() == "name":
            return _haskell_package_name_from_spec(field.group(2))
    return ""


def _collect_cabal_field(lines: list[str], index: int) -> tuple[list[str], int]:
    field = _CABAL_FIELD_RE.match(_strip_haskell_line_comment(lines[index]))
    if field is None:
        return [], index + 1

    values = [field.group(2).strip()]
    base_indent = len(lines[index]) - len(lines[index].lstrip())
    cursor = index + 1
    while cursor < len(lines):
        clean = _strip_haskell_line_comment(lines[cursor])
        stripped = clean.strip()
        if not stripped:
            cursor += 1
            continue
        indent = len(clean) - len(clean.lstrip())
        if (
            (indent <= base_indent and _CABAL_FIELD_RE.match(clean))
            or _cabal_stanza(clean)
            or (_CABAL_FIELD_RE.match(clean) and not stripped.startswith(","))
        ):
            break
        values.append(stripped)
        cursor += 1
    return values, cursor


def _parse_cabal_file(path: Path) -> tuple[set[str], set[str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return set(), set()

    own_package = _cabal_package_name(lines)
    required: set[str] = set()
    optional: set[str] = set()
    stanza = ""
    index = 0
    while index < len(lines):
        clean = _strip_haskell_line_comment(lines[index])
        stripped = clean.strip()
        if not stripped:
            index += 1
            continue

        next_stanza = _cabal_stanza(clean)
        if next_stanza:
            stanza = next_stanza
            index += 1
            continue

        field = _CABAL_FIELD_RE.match(clean)
        if field is None:
            index += 1
            continue

        key = field.group(1).lower()
        if key not in {"build-depends", "setup-depends"}:
            index += 1
            continue

        values, index = _collect_cabal_field(lines, index)
        target = (
            optional
            if key == "setup-depends" or stanza in _CABAL_OPTIONAL_STANZAS
            else required
        )
        target.update(_haskell_packages_from_specs(values))

    if own_package:
        required.discard(own_package)
        optional.discard(own_package)
    return required, optional


def _parse_stack_extra_deps(path: Path) -> set[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return set()

    optional: set[str] = set()
    in_extra_deps = False
    extra_indent = 0
    for raw in lines:
        clean = raw.split("#", 1)[0].rstrip()
        stripped = clean.strip()
        if not stripped:
            continue
        indent = len(clean) - len(clean.lstrip())

        if not in_extra_deps:
            field = _STACK_FIELD_RE.match(clean)
            if not field or field.group(1) != "extra-deps":
                continue
            extra_indent = indent
            rest = field.group(2).strip()
            if rest.startswith("[") and rest.endswith("]"):
                for spec in rest.strip("[]").split(","):
                    if package := _haskell_package_name_from_spec(spec):
                        optional.add(package)
                continue
            if rest and (package := _haskell_package_name_from_spec(rest)):
                optional.add(package)
            in_extra_deps = True
            continue

        if indent <= extra_indent and _STACK_FIELD_RE.match(clean):
            in_extra_deps = False
            continue
        if stripped.startswith("-"):
            spec = stripped[1:].strip()
            if package := _haskell_package_name_from_spec(spec):
                optional.add(package)

    return optional


def _parse_haskell_nix_hints(path: Path) -> set[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return set()

    packages: set[str] = set()
    for pattern in (
        r"\bhaskellPackages\.([A-Za-z0-9_-]+)\b",
        r"\bhaskell\.packages\.[A-Za-z0-9_-]+\.([A-Za-z0-9_-]+)\b",
    ):
        for match in re.finditer(pattern, text):
            raw_name = match.group(1)
            if raw_name in _NIX_HASKELL_PACKAGE_SKIP_NAMES:
                continue
            if package := _normalize_haskell_package(raw_name):
                packages.add(package)
    return packages


def _parse_haskell_manifest(
    project_root: Path, source_snapshot: SourceSnapshot
) -> Optional[_Manifest]:
    scoped_required: defaultdict[str, set[str]] = defaultdict(set)
    scoped_optional: defaultdict[str, set[str]] = defaultdict(set)

    for path in _walk_haskell_manifest_files(project_root, source_snapshot):
        root = _haskell_scope_root(project_root, path)
        if path.suffix == ".cabal":
            required, optional = _parse_cabal_file(path)
        elif path.name == "stack.yaml":
            required, optional = set(), _parse_stack_extra_deps(path)
        elif path.name == "flake.nix":
            required, optional = set(), _parse_haskell_nix_hints(path)
        else:
            continue
        scoped_required[root].update(required)
        scoped_optional[root].update(optional)

    if not scoped_required and not scoped_optional:
        return None

    scopes = tuple(
        _ManifestScope(
            root=root,
            required=frozenset(scoped_required[root]),
            optional=frozenset(scoped_optional[root]),
        )
        for root in sorted(set(scoped_required) | set(scoped_optional))
    )
    required = frozenset().union(*(scope.required for scope in scopes))
    optional = frozenset().union(*(scope.optional for scope in scopes))
    return _Manifest(required, optional, scopes=scopes)


_HASKELL_IMPORT_PACKAGE_PREFIXES: tuple[tuple[str, str], ...] = (
    ("Language.Haskell.GhclibParserEx", "ghc-lib-parser-ex"),
    ("GHC.Driver", "ghc-lib-parser"),
    ("GHC.Data", "ghc-lib-parser"),
    ("GHC.Hs", "ghc-lib-parser"),
    ("GHC.Parser", "ghc-lib-parser"),
    ("GHC.Types", "ghc-lib-parser"),
    ("GHC.Unit", "ghc-lib-parser"),
    ("Network.Wai.Handler.Warp", "warp"),
    ("Network.Wai", "wai"),
    ("Servant.Server", "servant-server"),
    ("Servant", "servant"),
    ("Test.Hspec", "hspec"),
    ("Data.Aeson", "aeson"),
    ("Data.ByteString", "bytestring"),
    ("Data.Map", "containers"),
    ("Data.Set", "containers"),
    ("Data.Text", "text"),
    ("Data.Time", "time"),
    ("System.Directory", "directory"),
    ("System.FilePath", "filepath"),
    ("Control.Monad.IO.Class", "transformers"),
    ("Control.", "base"),
    ("Data.Bool", "base"),
    ("Data.Char", "base"),
    ("Data.Either", "base"),
    ("Data.Eq", "base"),
    ("Data.Foldable", "base"),
    ("Data.Function", "base"),
    ("Data.Functor", "base"),
    ("Data.Int", "base"),
    ("Data.List", "base"),
    ("Data.Maybe", "base"),
    ("Data.Monoid", "base"),
    ("Data.Ord", "base"),
    ("Data.Semigroup", "base"),
    ("Data.String", "base"),
    ("Data.Traversable", "base"),
    ("Data.Tuple", "base"),
    ("Data.Word", "base"),
    ("Debug.", "base"),
    ("Foreign.", "base"),
    ("GHC.", "base"),
    ("Numeric.", "base"),
    ("Prelude", "base"),
    ("System.Environment", "base"),
    ("System.IO", "base"),
    ("Text.Read", "base"),
)


def _haskell_module_matches_prefix(module: str, prefix: str) -> bool:
    if prefix.endswith("."):
        return module.startswith(prefix)
    return module == prefix or module.startswith(prefix + ".")


def _classify_haskell(
    module: str, name: str, filepath: str, manifest: Optional[_Manifest]
) -> Optional[str]:
    spec = (module or "").strip().strip('"')
    if not spec or spec.startswith("."):
        return None
    for prefix, package in _HASKELL_IMPORT_PACKAGE_PREFIXES:
        if _haskell_module_matches_prefix(spec, prefix):
            return package
    return None


# ── Shared TOML loader ────────────────────────────────────────────────


def _load_toml(path: Path) -> Optional[dict]:
    """Parse a TOML file; ``None`` when missing, unreadable, or unparseable."""
    if tomllib is None:  # pragma: no cover - tomli always present as a dependency
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        data = tomllib.loads(text)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


# ── Dispatcher + reconciliation (DL-201, DL-205) ──────────────────────


_PLUGINS: tuple[_LanguagePlugin, ...] = (
    _LanguagePlugin("python", ("python",), _parse_python_manifest, _classify_python),
    _LanguagePlugin(
        "typescript", ("typescript", "javascript"), _parse_ts_manifest, _classify_ts
    ),
    _LanguagePlugin("go", ("go",), _parse_go_manifest, _classify_go),
    _LanguagePlugin("rust", ("rust",), _parse_rust_manifest, _classify_rust),
    _LanguagePlugin(
        "haskell", ("haskell",), _parse_haskell_manifest, _classify_haskell
    ),
)

_PLUGIN_BY_LANGUAGE: dict[str, _LanguagePlugin] = {
    lang: plugin for plugin in _PLUGINS for lang in plugin.languages
}


def parse_declared_dependencies(
    project_root: str = ".",
    *,
    source_snapshot: SourceSnapshot | None = None,
) -> dict:
    """Parse every available manifest under *project_root*.

    Returns ``{language: {"required": [...], "optional": [...]}}`` for each
    language whose manifest exists and parses; languages with no manifest are
    omitted. ``required`` is runtime dependencies, ``optional`` is extras/dev/
    build dependencies (never flagged "unused"). Both lists are sorted and
    normalized to their language's canonical form; a missing or malformed
    manifest is skipped rather than raised.
    """
    return {
        key: {
            "required": sorted(manifest.required),
            "optional": sorted(manifest.optional),
        }
        for key, manifest in _parse_manifests(
            Path(project_root), source_snapshot=source_snapshot
        ).items()
    }


def _parse_manifests(
    project_root: Path, *, source_snapshot: SourceSnapshot | None = None
) -> dict[str, _Manifest]:
    project_root = project_root.resolve()
    source_snapshot = source_snapshot or build_source_snapshot(project_root)
    manifests: dict[str, _Manifest] = {}
    for plugin in _PLUGINS:
        manifest = plugin.parse(project_root, source_snapshot)
        if manifest is not None:
            manifests[plugin.key] = manifest
    return manifests


def classify_imports(
    inventory: dict,
    *,
    graph: Optional[dict] = None,
    manifests: Optional[dict[str, _Manifest]] = None,
) -> dict:
    """Group each file's external imports by language and package.

    Routes the graph's ``unresolved`` imports (those that resolve to no internal
    file — DL-101) through their file's per-language classifier, dropping
    relative, stdlib/builtin, and intra-module imports. Returns
    ``{language: {package: [importing_files]}}`` with every collection sorted.

    *graph* and *manifests* are accepted so a caller that already computed them
    (e.g. :func:`reconcile_dependencies`) avoids redundant work; both default to
    being derived on demand (manifests stay empty here — Go classification then
    degrades to a ``host/org/repo`` heuristic).
    """
    if graph is None:
        graph = build_dependency_graph(inventory)
    manifests = manifests or {}

    grouped: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    for item in graph.get("unresolved", []):
        if item.get("kind") == "path_alias":
            continue
        data = inventory.get(item["file"])
        language = data.get("language") if isinstance(data, dict) else None
        if not isinstance(language, str):
            continue
        plugin = _PLUGIN_BY_LANGUAGE.get(language)
        if plugin is None:
            continue
        package = plugin.classify(
            item["module"], item["name"], item["file"], manifests.get(plugin.key)
        )
        if package:
            grouped[plugin.key][package].add(item["file"])

    return {
        language: {pkg: sorted(files) for pkg, files in sorted(packages.items())}
        for language, packages in sorted(grouped.items())
    }


def _path_under_scope(filepath: str, scope_root: str) -> bool:
    return shared_path_is_under_scope(filepath, scope_root)


def _nearest_manifest_scope(
    manifest: Optional[_Manifest], filepath: str
) -> Optional[_ManifestScope]:
    if manifest is None:
        return None
    matches = [
        scope for scope in manifest.scopes if _path_under_scope(filepath, scope.root)
    ]
    if not matches:
        return None
    return max(matches, key=lambda scope: (scope.root.count("/"), len(scope.root)))


def _scope_label(scope: Optional[_ManifestScope]) -> str | None:
    if scope is None:
        return None
    return scope.root


def _reconcile_scoped_language(
    used_packages: dict[str, list[str]],
    manifest: Optional[_Manifest],
) -> dict:
    if manifest is None:
        return {
            "used": used_packages,
            "required": [],
            "optional": [],
            "undeclared": sorted(used_packages),
            "unused": [],
            "undeclared_details": [
                {"package": package, "files": list(files), "scope": None}
                for package, files in sorted(used_packages.items())
            ],
            "unused_details": [],
        }

    nearest_cache: dict[str, Optional[_ManifestScope]] = {}

    def nearest(filepath: str) -> Optional[_ManifestScope]:
        if filepath not in nearest_cache:
            nearest_cache[filepath] = _nearest_manifest_scope(manifest, filepath)
        return nearest_cache[filepath]

    undeclared: set[str] = set()
    undeclared_files: defaultdict[str, list[str]] = defaultdict(list)
    undeclared_scopes: defaultdict[str, set[str | None]] = defaultdict(set)
    for package, files in used_packages.items():
        for filepath in files:
            scope = nearest(filepath)
            declared = bool(scope and package in (scope.required | scope.optional))
            if not declared:
                undeclared.add(package)
                undeclared_files[package].append(filepath)
                undeclared_scopes[package].add(_scope_label(scope))

    unused: set[str] = set()
    unused_scopes: defaultdict[str, set[str | None]] = defaultdict(set)
    for scope in manifest.scopes:
        for package in scope.required:
            files = used_packages.get(package, [])
            if not any(nearest(filepath) == scope for filepath in files):
                unused.add(package)
                unused_scopes[package].add(_scope_label(scope))

    def detail_scope(scopes: set[str | None]) -> str | None:
        non_null = {scope for scope in scopes if scope is not None}
        if len(non_null) == 1 and len(scopes) == 1:
            return next(iter(non_null))
        if len(non_null) == 1 and None not in scopes:
            return next(iter(non_null))
        if not non_null:
            return None
        return "multiple"

    return {
        "used": used_packages,
        "required": sorted(manifest.required),
        "optional": sorted(manifest.optional),
        "undeclared": sorted(undeclared),
        "unused": sorted(unused),
        "undeclared_details": [
            {
                "package": package,
                "files": sorted(undeclared_files[package]),
                "scope": detail_scope(undeclared_scopes[package]),
            }
            for package in sorted(undeclared)
        ],
        "unused_details": [
            {
                "package": package,
                "files": [],
                "scope": detail_scope(unused_scopes[package]),
            }
            for package in sorted(unused)
        ],
    }


def _python_internal_distribution_uses(
    inventory: dict,
    _graph: dict,
    manifest: Optional[_Manifest],
) -> dict[str, list[str]]:
    if manifest is None:
        return {}

    resolver = build_module_path_resolver(inventory)
    symbol_index = _build_symbol_file_index(inventory)
    grouped: defaultdict[str, set[str]] = defaultdict(set)
    for importer, importer_data in inventory.items():
        if not (
            isinstance(importer_data, dict)
            and importer_data.get("language") == "python"
        ):
            continue
        importer_scope = _nearest_manifest_scope(manifest, importer)
        for imp in importer_data.get("imports", []):
            module = _resolve_target_module(
                imp.get("module", "") or "", imp.get("name", "") or ""
            )
            if not module or module.startswith("."):
                continue
            import_root = module.split(".", 1)[0]
            targets = _resolve_internal_targets(imp, importer, resolver, symbol_index)
            for target in targets:
                target_data = inventory.get(target)
                if not (
                    isinstance(target_data, dict)
                    and target_data.get("language") == "python"
                ):
                    continue
                target_scope = _nearest_manifest_scope(manifest, target)
                if (
                    target_scope is None
                    or not target_scope.distribution
                    or importer_scope == target_scope
                    or import_root not in target_scope.import_roots
                ):
                    continue
                grouped[target_scope.distribution].add(importer)

    return {package: sorted(files) for package, files in sorted(grouped.items())}


def _merge_used_packages(
    used: dict[str, dict[str, list[str]]],
    language: str,
    additions: dict[str, list[str]],
) -> None:
    if not additions:
        return
    language_used = used.setdefault(language, {})
    for package, files in additions.items():
        merged = set(language_used.get(package, []))
        merged.update(files)
        language_used[package] = sorted(merged)


def _version_record(version: str, resolved_from: str) -> dict[str, str]:
    return {"version": version, "resolved_from": resolved_from}


def _version_sort_key(version: str) -> tuple:
    clean = version.strip()
    if clean.startswith("v") and len(clean) > 1 and clean[1].isdigit():
        clean = clean[1:]
    pieces = re.split(r"([0-9]+)", clean)
    return tuple(
        (0, int(piece)) if piece.isdigit() else (1, piece.lower())
        for piece in pieces
        if piece
    )


def _keep_highest_version(
    versions: dict[str, dict[str, str]], package: str, version: str, source: str
) -> None:
    if not package or not version:
        return
    current = versions.get(package)
    if current is None or _version_sort_key(version) > _version_sort_key(
        current["version"]
    ):
        versions[package] = _version_record(version, source)


def _lockfile_dirs(root: Path, excluded_dirs: frozenset[str]) -> list[Path]:
    dirs: list[Path] = []
    for current, dirnames, _files in os.walk(root):
        current_path = Path(current)
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in excluded_dirs
            and not _manifest_dir_is_agent_worktree(root, current_path, dirname)
        ]
        dirs.append(current_path)
    return dirs


def _go_sum_versions(
    project_root: Path,
    source_snapshot: SourceSnapshot | None = None,
) -> dict[str, dict[str, str]]:
    versions: dict[str, dict[str, str]] = {}
    if (
        source_snapshot is not None
        and source_snapshot.source_selection_policy is not None
    ):
        go_sums = _snapshot_package_marker_paths(
            project_root,
            source_snapshot,
            lambda name: name == "go.sum",
        )
    else:
        go_sums = [
            go_mod.parent / "go.sum"
            for go_mod in _walk_go_manifest_files(project_root, source_snapshot)
        ]
    for go_sum in go_sums:
        try:
            lines = go_sum.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for raw in lines:
            parts = raw.split()
            if len(parts) < 2:
                continue
            module, version = parts[0], parts[1]
            if version.endswith("/go.mod"):
                version = version[: -len("/go.mod")]
            _keep_highest_version(versions, module, version, "go.sum")
    return versions


def _cargo_lock_versions(
    project_root: Path,
    source_snapshot: SourceSnapshot | None = None,
) -> dict[str, dict[str, str]]:
    if (
        source_snapshot is not None
        and source_snapshot.source_selection_policy is not None
    ):
        paths = _snapshot_package_marker_paths(
            project_root,
            source_snapshot,
            lambda name: name == "Cargo.lock",
        )
    else:
        paths = [project_root / "Cargo.lock"]
    versions: dict[str, dict[str, str]] = {}
    for path in paths:
        data = _load_toml(path)
        if data is None:
            continue
        packages = data.get("package")
        if not isinstance(packages, list):
            continue
        for package in packages:
            if not isinstance(package, dict):
                continue
            name = package.get("name")
            version = package.get("version")
            if isinstance(name, str) and isinstance(version, str):
                _keep_highest_version(
                    versions, _normalize_rust(name), version, "Cargo.lock"
                )
    return versions


_REQUIREMENTS_PIN_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*==\s*([^;\s]+)")


def _requirements_pin_versions(
    project_root: Path,
    source_snapshot: SourceSnapshot | None = None,
) -> dict[str, dict[str, str]]:
    versions: dict[str, dict[str, str]] = {}
    for path in _walk_python_manifest_files(project_root, source_snapshot):
        if not _is_python_requirements_manifest_name(path.name):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for raw in lines:
            line = raw.split("#", 1)[0].strip()
            if not line or line.startswith(("-e", "--editable")):
                continue
            match = _REQUIREMENTS_PIN_RE.match(line)
            if match:
                _keep_highest_version(
                    versions,
                    _normalize_python(match.group(1)),
                    match.group(2),
                    path.name,
                )
    return versions


def _poetry_lock_versions(
    project_root: Path,
    source_snapshot: SourceSnapshot | None = None,
) -> dict[str, dict[str, str]]:
    versions: dict[str, dict[str, str]] = {}
    if (
        source_snapshot is not None
        and source_snapshot.source_selection_policy is not None
    ):
        paths = _snapshot_package_marker_paths(
            project_root,
            source_snapshot,
            lambda name: name == "poetry.lock",
        )
    else:
        paths = []
    if source_snapshot is None:
        directories = _lockfile_dirs(project_root, _PYTHON_MANIFEST_EXCLUDED_DIRS)
    elif source_snapshot.source_selection_policy is None:
        directories = sorted(
            {
                path.parent
                for path in _walk_python_manifest_files(
                    project_root,
                    source_snapshot,
                )
            },
            key=lambda path: path.relative_to(project_root).as_posix(),
        )
    else:
        directories = []
    paths.extend(directory / "poetry.lock" for directory in directories)
    for path in paths:
        data = _load_toml(path)
        if data is None:
            continue
        packages = data.get("package")
        if not isinstance(packages, list):
            continue
        for package in packages:
            if not isinstance(package, dict):
                continue
            name = package.get("name")
            version = package.get("version")
            if isinstance(name, str) and isinstance(version, str):
                versions[_normalize_python(name)] = _version_record(
                    version, "poetry.lock"
                )
    return versions


def _python_lock_versions(
    project_root: Path,
    source_snapshot: SourceSnapshot | None = None,
) -> dict[str, dict[str, str]]:
    versions = _requirements_pin_versions(project_root, source_snapshot)
    versions.update(_poetry_lock_versions(project_root, source_snapshot))
    return versions


def _package_lock_name(package_path: str) -> str:
    if "node_modules/" not in package_path:
        return ""
    return package_path.rsplit("node_modules/", 1)[1].strip("/").lower()


def _package_lock_versions(
    project_root: Path,
    source_snapshot: SourceSnapshot | None = None,
) -> dict[str, dict[str, str]]:
    versions: dict[str, dict[str, str]] = {}
    if (
        source_snapshot is not None
        and source_snapshot.source_selection_policy is not None
    ):
        lockfiles = _snapshot_package_marker_paths(
            project_root,
            source_snapshot,
            lambda name: name == "package-lock.json",
        )
    else:
        lockfiles = [
            package_json.parent / "package-lock.json"
            for package_json in _walk_ts_manifest_files(project_root, source_snapshot)
        ]
    for lockfile in lockfiles:
        try:
            data = json.loads(lockfile.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        packages = data.get("packages")
        if not isinstance(packages, dict):
            continue
        for package_path, metadata in packages.items():
            if not isinstance(package_path, str) or not isinstance(metadata, dict):
                continue
            name = _package_lock_name(package_path)
            version = metadata.get("version")
            if name and isinstance(version, str):
                _keep_highest_version(versions, name, version, "package-lock.json")
    return versions


def _pnpm_package_key(line: str) -> tuple[str, str]:
    key = line.strip().strip("'\"")
    if not key.endswith(":"):
        return "", ""
    key = key[:-1].strip().strip("'\"").lstrip("/")
    if "@" not in key:
        return "", ""
    name, version = key.rsplit("@", 1)
    version = version.split("(", 1)[0]
    if not name or not version:
        return "", ""
    return name.lower(), version


def _pnpm_lock_versions(
    project_root: Path,
    source_snapshot: SourceSnapshot | None = None,
) -> dict[str, dict[str, str]]:
    versions: dict[str, dict[str, str]] = {}
    if (
        source_snapshot is not None
        and source_snapshot.source_selection_policy is not None
    ):
        lockfiles = _snapshot_package_marker_paths(
            project_root,
            source_snapshot,
            lambda name: name == "pnpm-lock.yaml",
        )
    else:
        lockfiles = [
            package_json.parent / "pnpm-lock.yaml"
            for package_json in _walk_ts_manifest_files(project_root, source_snapshot)
        ]
    for lockfile in lockfiles:
        try:
            lines = lockfile.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        in_packages = False
        for raw in lines:
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped == "packages:":
                in_packages = True
                continue
            if not in_packages:
                continue
            name, version = _pnpm_package_key(stripped)
            if name and version:
                _keep_highest_version(versions, name, version, "pnpm-lock.yaml")
    return versions


def _typescript_lock_versions(
    project_root: Path,
    source_snapshot: SourceSnapshot | None = None,
) -> dict[str, dict[str, str]]:
    versions = _package_lock_versions(project_root, source_snapshot)
    for package, record in _pnpm_lock_versions(
        project_root,
        source_snapshot,
    ).items():
        versions.setdefault(package, record)
    return versions


def _lockfile_versions(
    project_root: Path,
    source_snapshot: SourceSnapshot | None = None,
) -> dict[str, dict[str, dict[str, str]]]:
    return {
        "go": _go_sum_versions(project_root, source_snapshot),
        "rust": _cargo_lock_versions(project_root, source_snapshot),
        "python": _python_lock_versions(project_root, source_snapshot),
        "typescript": _typescript_lock_versions(project_root, source_snapshot),
    }


def _attach_versions(report: dict, versions: dict[str, dict[str, str]]) -> None:
    relevant = (
        set(report.get("used", {}))
        | set(report.get("required", []))
        | set(report.get("optional", []))
        | set(report.get("undeclared", []))
        | set(report.get("unused", []))
    )
    report["versions"] = {
        package: versions[package]
        for package in sorted(versions)
        if package in relevant
    }


def _unresolved_path_aliases_by_language(
    inventory: dict, graph: dict
) -> dict[str, dict]:
    grouped: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    for item in graph.get("unresolved", []):
        if item.get("kind") != "path_alias":
            continue
        data = inventory.get(item["file"])
        language = data.get("language") if isinstance(data, dict) else None
        if not isinstance(language, str):
            continue
        plugin = _PLUGIN_BY_LANGUAGE.get(language)
        if plugin is None:
            continue
        grouped[plugin.key][item["module"]].add(item["file"])
    return {
        language: {module: sorted(files) for module, files in sorted(modules.items())}
        for language, modules in sorted(grouped.items())
    }


def reconcile_dependencies(
    inventory: dict,
    project_root: str = ".",
    *,
    graph: Optional[dict] = None,
    source_snapshot: SourceSnapshot | None = None,
) -> dict:
    """Reconcile used external imports against declared dependencies per language.

    For every language with either imports or a manifest, computes
    ``undeclared = used − (required ∪ optional)`` and ``unused = required −
    used`` (extras/dev/build dependencies are never "unused"). Returns
    ``{"languages": {language: {"used", "required", "optional", "undeclared",
    "unused"}}, "summary": {...}}``; ``used`` maps each package to its importing
    files. Tolerant of a missing manifest (all used → undeclared) or missing
    imports (all required → unused); never raises.
    """
    if graph is None:
        graph = build_dependency_graph(
            inventory,
            project_root,
            source_snapshot=source_snapshot,
        )
    manifests = _parse_manifests(Path(project_root), source_snapshot=source_snapshot)
    used = classify_imports(inventory, graph=graph, manifests=manifests)
    _merge_used_packages(
        used,
        "python",
        _python_internal_distribution_uses(inventory, graph, manifests.get("python")),
    )
    path_aliases = _unresolved_path_aliases_by_language(inventory, graph)
    versions_by_language = _lockfile_versions(
        Path(project_root).resolve(),
        source_snapshot,
    )

    languages: dict[str, dict] = {}
    for key in sorted(set(used) | set(manifests) | set(path_aliases)):
        used_packages = used.get(key, {})
        if key in {"go", "haskell", "python", "typescript"}:
            languages[key] = _reconcile_scoped_language(
                used_packages, manifests.get(key)
            )
            languages[key]["path_aliases"] = path_aliases.get(key, {})
            _attach_versions(languages[key], versions_by_language.get(key, {}))
            continue
        used_names = set(used_packages)
        manifest = manifests.get(key)
        required = manifest.required if manifest else frozenset()
        optional = manifest.optional if manifest else frozenset()
        languages[key] = {
            "used": used_packages,
            "required": sorted(required),
            "optional": sorted(optional),
            "undeclared": sorted(used_names - required - optional),
            "unused": sorted(required - used_names),
            "path_aliases": path_aliases.get(key, {}),
        }
        _attach_versions(languages[key], versions_by_language.get(key, {}))

    summary = {
        "languages": sorted(languages),
        "external_count": sum(len(lang["used"]) for lang in languages.values()),
        "undeclared_count": sum(len(lang["undeclared"]) for lang in languages.values()),
        "unused_count": sum(len(lang["unused"]) for lang in languages.values()),
    }
    return {
        "languages": languages,
        "summary": summary,
        "version_details": build_dependency_version_details(
            project_root,
            source_snapshot=source_snapshot,
        ),
    }


# ══ Aggregation + scale guard (Epic 2.4) ══════════════════════════════════


def analyze_dependencies(
    inventory: dict,
    project_root: str = ".",
    *,
    source_snapshot: SourceSnapshot | None = None,
) -> dict:
    """Run the full dependency analysis once, sharing the internal graph.

    Builds the internal module-dependency graph a single time and threads it
    through cycle detection, fan-in/fan-out metrics, topological load order, and
    external reconciliation, then pairs it with module-level side effects. The
    page generators, ``sync`` regeneration, and the ``extract`` block all consume
    this one bundle so the graph is never rebuilt per consumer. Returns
    ``{"graph", "cycles", "metrics", "load_order", "side_effects",
    "reconciliation"}``; deterministic and never raises on slim inventories.
    """
    graph = build_dependency_graph(
        inventory,
        project_root,
        source_snapshot=source_snapshot,
    )
    return {
        "graph": graph,
        "cycles": detect_cycles(graph),
        "metrics": dependency_metrics(graph),
        "load_order": topological_order(graph),
        "side_effects": detect_side_effects(inventory),
        "reconciliation": reconcile_dependencies(
            inventory,
            project_root,
            graph=graph,
            source_snapshot=source_snapshot,
        ),
    }


def top_level_package(filepath: str) -> str:
    """Return the top-level package of *filepath* (its first path component).

    A file at the project root (no directory) is its own package, keyed by stem,
    so the collapsed graph never invents an empty bucket.
    """
    path = Path(filepath)
    parts = path.parts
    return parts[0] if len(parts) > 1 else path.stem


def package_dependency_graph(graph: dict) -> dict:
    """Collapse a module graph to a top-level-package graph.

    Every module node maps to its :func:`top_level_package`; intra-package edges
    are dropped and parallel inter-package edges de-duplicated, bounding the
    diagram for large repositories (DL-404). Returns the same
    ``{"nodes", "edges"}`` shape as :func:`build_dependency_graph` (minus
    ``unresolved``), stably sorted.
    """
    nodes = {top_level_package(node) for node in graph.get("nodes", [])}
    edges: set[tuple[str, str]] = set()
    for source, target in graph.get("edges", []):
        src, dst = top_level_package(source), top_level_package(target)
        nodes.add(src)
        nodes.add(dst)
        if src != dst:
            edges.add((src, dst))
    return {"nodes": sorted(nodes), "edges": sorted(edges)}
