"""Pure Mermaid diagram renderers.

These functions turn plain Python structures into fenced ``mermaid`` code
blocks. They perform no I/O, are deterministic (stable participant/node
ordering), and sanitize labels so generated diagrams render on GitHub and in
common Mermaid viewers.
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping

_FENCE = "```mermaid"
_LABEL_SAFE = re.compile(r"[^A-Za-z0-9 _.\-/]+")
_HREF_SAFE = re.compile(r'[\s"`]+')


def _sanitize(text: str) -> str:
    """Reduce *text* to characters that are safe inside a Mermaid label."""
    cleaned = _LABEL_SAFE.sub(" ", str(text)).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "unknown"


def _sanitize_href(href: str) -> str:
    """Strip whitespace/quotes that would break a Mermaid ``click`` directive."""
    return _HREF_SAFE.sub("", str(href))


def _ordered_participants(interactions: list[Mapping]) -> dict[str, str]:
    """Map each actor to a stable ``pN`` alias in first-seen order."""
    aliases: dict[str, str] = {}
    for interaction in interactions:
        for actor in (interaction["from"], interaction["to"]):
            if actor not in aliases:
                aliases[actor] = f"p{len(aliases)}"
    return aliases


def sequence_diagram(interactions: Iterable[Mapping]) -> str:
    """Render a Mermaid ``sequenceDiagram`` from caller→callee interactions.

    Each interaction is a mapping with ``from``, ``to``, and ``label`` keys and
    an optional ``dashed`` flag (rendered with a dashed arrow, e.g. for external
    or unresolved calls). Participants are declared explicitly in first-seen
    order so the output is deterministic.
    """
    interactions = list(interactions)
    aliases = _ordered_participants(interactions)
    lines = [_FENCE, "sequenceDiagram"]
    for actor, alias in aliases.items():
        lines.append(f"    participant {alias} as {_sanitize(actor)}")
    for interaction in interactions:
        arrow = "-->>" if interaction.get("dashed") else "->>"
        src = aliases[interaction["from"]]
        dst = aliases[interaction["to"]]
        lines.append(f"    {src}{arrow}{dst}: {_sanitize(interaction['label'])}")
    lines.append("```")
    return "\n".join(lines)


def flowchart(
    nodes: Iterable[str],
    edges: Iterable[tuple[str, str]],
    *,
    direction: str = "TD",
    links: Mapping[str, str] | None = None,
    highlight_edges: Iterable[tuple[str, str]] | None = None,
) -> str:
    """Render a Mermaid ``flowchart`` from *nodes* and directed *edges*.

    Nodes are de-duplicated preserving order; edges referencing unknown nodes
    are dropped. *links* maps a node to a relative href; each gets a Mermaid
    ``click`` directive so the node hyperlinks to its page (links to unknown
    nodes are ignored, emitted in node order for determinism). *highlight_edges*
    are drawn with a thick ``==>`` arrow instead of ``-->`` — used to mark the
    edges inside an import cycle. Used for dependency / load-order diagrams.
    """
    link_map = dict(links or {})
    highlight = set(highlight_edges or ())
    alias: dict[str, str] = {}
    lines = [_FENCE, f"flowchart {direction}"]
    for node in dict.fromkeys(nodes):
        alias[node] = f"n{len(alias)}"
        lines.append(f'    {alias[node]}["{_sanitize(node)}"]')
    for src, dst in edges:
        if src in alias and dst in alias:
            arrow = "==>" if (src, dst) in highlight else "-->"
            lines.append(f"    {alias[src]} {arrow} {alias[dst]}")
    for node in alias:
        href = link_map.get(node)
        if href:
            lines.append(f'    click {alias[node]} "{_sanitize_href(href)}"')
    lines.append("```")
    return "\n".join(lines)


def _step_number(step: Mapping, fallback: int) -> int:
    try:
        return int(step.get("index") or fallback)
    except (TypeError, ValueError):
        return fallback


def _transfer_endpoint(
    transfer: Mapping,
    key: str,
    symbol_key: str,
    aliases_by_index: Mapping[int, str],
    aliases_by_symbol: Mapping[str, str],
) -> str | None:
    try:
        step_index = int(transfer.get(key))
    except (TypeError, ValueError):
        step_index = 0
    if step_index in aliases_by_index:
        return aliases_by_index[step_index]
    symbol = str(transfer.get(symbol_key) or "")
    return aliases_by_symbol.get(symbol)


def _link_for_step(step: Mapping, module_page_map: Mapping[str, str]) -> str:
    filepath = step.get("file")
    if not filepath:
        return ""
    page = module_page_map.get(str(filepath))
    return f"../modules/{page}.md" if page else ""


def data_flow_diagram(
    data_flow: Mapping, module_page_map: Mapping[str, str] | None = None
) -> str:
    """Render a labeled Mermaid diagram for one static data-flow summary."""
    page_map = dict(module_page_map or {})
    steps = list(data_flow.get("steps", []))
    aliases_by_index: dict[int, str] = {}
    aliases_by_symbol: dict[str, str] = {}
    lines = [_FENCE, "flowchart LR"]

    for fallback, step in enumerate(steps, start=1):
        number = _step_number(step, fallback)
        alias = f"s{number}"
        aliases_by_index[number] = alias
        symbol = str(step.get("symbol") or "?")
        aliases_by_symbol.setdefault(symbol, alias)
        lines.append(f'    {alias}["{_sanitize(f"{number}. {symbol}")}"]')

    for transfer in data_flow.get("transfers", []):
        src = _transfer_endpoint(
            transfer, "from_step", "from", aliases_by_index, aliases_by_symbol
        )
        dst = _transfer_endpoint(
            transfer, "to_step", "to", aliases_by_index, aliases_by_symbol
        )
        if not src or not dst:
            continue
        label = _sanitize(transfer.get("call") or transfer.get("kind") or "data")
        if transfer.get("kind") in {"external", "unresolved"}:
            lines.append(f"    {src} -. {label} .-> {dst}")
        else:
            lines.append(f"    {src} -->|{label}| {dst}")

    boundary_aliases = []
    for offset, boundary in enumerate(data_flow.get("boundaries", [])):
        src = None
        try:
            step_index = int(boundary.get("step_index"))
        except (TypeError, ValueError):
            step_index = 0
        if step_index:
            src = aliases_by_index.get(step_index)
        if src is None:
            src = aliases_by_symbol.get(str(boundary.get("step") or ""))
        if src is None:
            continue
        alias = f"b{offset}"
        label = _sanitize(
            f"{boundary.get('kind', 'boundary')} {boundary.get('target', '?')}"
        )
        lines.append(f'    {alias}["{label}"]')
        lines.append(f"    {src} -. {label} .-> {alias}")
        boundary_aliases.append(alias)

    for fallback, step in enumerate(steps, start=1):
        number = _step_number(step, fallback)
        href = _link_for_step(step, page_map)
        if href:
            lines.append(f'    click s{number} "{_sanitize_href(href)}"')

    if boundary_aliases:
        lines.append("    classDef boundary stroke:#b45309,stroke-dasharray: 4 2")
        for alias in boundary_aliases:
            lines.append(f"    class {alias} boundary")

    lines.append("```")
    return "\n".join(lines)
