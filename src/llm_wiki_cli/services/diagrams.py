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
