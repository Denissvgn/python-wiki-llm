"""Pure per-module dependency mini-map summaries.

This module projects the existing dependency-analysis bundle into bounded local
views for module pages. It performs no I/O and does not render Markdown; page
generators can turn the returned plain dict/list data into diagrams later.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

from .dependencies import top_level_package

_DEFAULT_NODE_LIMIT = 12


def _sort_key(value: object) -> tuple[str, str]:
    text = "" if value is None else str(value)
    return text.casefold(), text


def _edge_tuple(edge: Iterable[object]) -> tuple[str, str]:
    source, target = list(edge)[:2]
    return str(source), str(target)


def _graph_edges(graph: Mapping) -> list[tuple[str, str]]:
    edges = []
    for edge in graph.get("edges", []) or []:
        try:
            edges.append(_edge_tuple(edge))
        except (TypeError, ValueError):
            continue
    return sorted(set(edges), key=lambda item: (_sort_key(item[0]), _sort_key(item[1])))


def _graph_nodes(graph: Mapping, edges: Iterable[tuple[str, str]]) -> list[str]:
    nodes = {str(node) for node in graph.get("nodes", []) or []}
    for source, target in edges:
        nodes.add(source)
        nodes.add(target)
    return sorted(nodes, key=_sort_key)


def _safe_node_limit(node_limit: int) -> int:
    try:
        return max(1, int(node_limit))
    except (TypeError, ValueError):
        return _DEFAULT_NODE_LIMIT


def _cycle_groups(cycles: Iterable[Iterable[object]]) -> list[set[str]]:
    groups = []
    for cycle in cycles or []:
        members = {str(member) for member in cycle}
        if members:
            groups.append(members)
    return groups


def _cycle_edges_for_module(
    module: str, edges: Iterable[tuple[str, str]], groups: Iterable[set[str]]
) -> list[tuple[str, str]]:
    for group in groups:
        if module not in group:
            continue
        return [
            (source, target)
            for source, target in edges
            if source in group and target in group
        ]
    return []


def _external_summary(module: str, reconciliation: Mapping) -> dict:
    external = {}
    for language in sorted((reconciliation.get("languages", {}) or {}), key=_sort_key):
        data = reconciliation.get("languages", {}).get(language) or {}
        used = data.get("used", {}) or {}
        undeclared = set(data.get("undeclared", []) or [])
        used_packages = [
            str(package)
            for package, files in used.items()
            if module in {str(file) for file in files or []}
        ]
        if not used_packages:
            continue
        external[str(language)] = {
            "used_count": len(set(used_packages)),
            "undeclared_count": len(set(used_packages) & undeclared),
        }
    return external


def _package_buckets(files: Iterable[str]) -> list[dict]:
    buckets: defaultdict[str, set[str]] = defaultdict(set)
    for filepath in files:
        buckets[top_level_package(filepath)].add(filepath)
    return [
        {"package": package, "count": len(buckets[package])}
        for package in sorted(buckets, key=_sort_key)
    ]


def _package_nodes_and_edges(
    module: str, inbound: Iterable[str], outbound: Iterable[str]
) -> tuple[list[str], list[tuple[str, str]]]:
    nodes = {module}
    edges = set()
    for package in {top_level_package(filepath) for filepath in inbound}:
        nodes.add(package)
        edges.add((package, module))
    for package in {top_level_package(filepath) for filepath in outbound}:
        nodes.add(package)
        edges.add((module, package))
    return (
        sorted(nodes, key=_sort_key),
        sorted(edges, key=lambda item: (_sort_key(item[0]), _sort_key(item[1]))),
    )


def _module_summary(
    module: str,
    edges: list[tuple[str, str]],
    cycle_groups: list[set[str]],
    reconciliation: Mapping,
    node_limit: int,
) -> dict:
    inbound = sorted(
        {source for source, target in edges if target == module}, key=_sort_key
    )
    outbound = sorted(
        {target for source, target in edges if source == module}, key=_sort_key
    )
    neighbors = sorted(set(inbound) | set(outbound), key=_sort_key)
    total_neighbor_count = len(neighbors)
    visible_neighbor_limit = max(node_limit - 1, 0)
    omitted_count = max(0, total_neighbor_count - visible_neighbor_limit)
    cycle_edges = _cycle_edges_for_module(module, edges, cycle_groups)

    overflow = {
        "node_limit": node_limit,
        "total_neighbor_count": total_neighbor_count,
        "omitted_count": omitted_count,
    }

    if total_neighbor_count + 1 > node_limit:
        nodes, local_edges = _package_nodes_and_edges(module, inbound, outbound)
        return {
            "file": module,
            "detail": "package",
            "inbound": _package_buckets(inbound),
            "outbound": _package_buckets(outbound),
            "nodes": nodes,
            "edges": local_edges,
            "cycle_participation": bool(cycle_edges),
            "cycle_edges": cycle_edges,
            "external": _external_summary(module, reconciliation),
            "overflow": overflow,
        }

    local_nodes = set(neighbors)
    local_nodes.add(module)
    local_edges = [
        (source, target)
        for source, target in edges
        if source in local_nodes and target in local_nodes
    ]
    return {
        "file": module,
        "detail": "module",
        "inbound": inbound,
        "outbound": outbound,
        "nodes": sorted(local_nodes, key=_sort_key),
        "edges": local_edges,
        "cycle_participation": bool(cycle_edges),
        "cycle_edges": cycle_edges,
        "external": _external_summary(module, reconciliation),
        "overflow": overflow,
    }


def build_module_dependency_maps(
    analysis: Mapping, *, node_limit: int = _DEFAULT_NODE_LIMIT
) -> dict[str, dict]:
    """Build bounded local dependency summaries for each internal module.

    ``analysis`` should be the existing :func:`dependencies.analyze_dependencies`
    bundle. The function consumes only the already-computed graph, cycles, and
    external reconciliation, preserving dependency-analysis reuse for bootstrap,
    sync, extract, and future module-page rendering.
    """
    graph = analysis.get("graph", {}) or {}
    edges = _graph_edges(graph)
    nodes = _graph_nodes(graph, edges)
    cycles = _cycle_groups(analysis.get("cycles", []) or [])
    reconciliation = analysis.get("reconciliation", {}) or {}
    limit = _safe_node_limit(node_limit)

    return {
        module: _module_summary(module, edges, cycles, reconciliation, limit)
        for module in nodes
    }
