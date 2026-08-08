"""Pure Mermaid diagram renderers.

Renderer functions turn plain Python structures into fenced ``mermaid`` code
blocks. They perform no I/O, are deterministic (stable participant/node
ordering), and sanitize labels so generated diagrams render on GitHub and in
common Mermaid viewers. Plugin style resolution is the explicit runtime-loading
boundary.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import quote, unquote, urlsplit

from .plugins import PluginError, diagram_style_components, load_entry_point
from .validation import resolved_paths_equal

_FENCE = "```mermaid"
_CLASS_SAFE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
_COLOR_SAFE = re.compile(r"^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$")
_ALLOWED_DIRECTIONS = {"TB", "TD", "BT", "RL", "LR"}
_DISPLAY_LABEL_LIMIT = 160
_HREF_LIMIT = 512
_RESERVED_CLASS_NAMES = {
    "accdescr",
    "acctitle",
    "bt",
    "callback",
    "call",
    "class",
    "classdef",
    "click",
    "default",
    "direction",
    "end",
    "flowchart",
    "graph",
    "href",
    "interpolate",
    "linkstyle",
    "lr",
    "rl",
    "style",
    "subgraph",
    "tb",
    "td",
    "title",
}
_FLOWCHART_ENTITIES = {
    '"': "#34;",
    "#": "#35;",
    "&": "#38;",
    "<": "#60;",
    ">": "#62;",
    "`": "#96;",
}
_HREF_SAFE = "/:@?&=+$,;~-._!()*#"
_STEP_INDEX_DIGIT_LIMIT = 128

GENERATED_DIAGRAM_NODE_LIMIT = 40
GENERATED_DIAGRAM_LINE_LIMIT = 80
GENERATED_DIAGRAM_CHAR_LIMIT = 6000


def _normalize_display_text(value: Any, *, replacements: str = "") -> str:
    """Return bounded NFC text with controls and whitespace collapsed."""
    normalized = unicodedata.normalize("NFC", str(value))
    replacement_chars = set(replacements)
    cleaned = "".join(
        " "
        if char in replacement_chars
        or char.isspace()
        or not char.isprintable()
        else char
        for char in normalized
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip() or "unknown"
    if len(cleaned) > _DISPLAY_LABEL_LIMIT:
        cleaned = cleaned[: _DISPLAY_LABEL_LIMIT - 1].rstrip() + "…"
    return cleaned


def _flowchart_label(value: Any) -> str:
    """Serialize arbitrary display text for a quoted Mermaid flowchart label."""
    return "".join(
        _FLOWCHART_ENTITIES.get(char, char) for char in _normalize_display_text(value)
    )


def _sequence_text(value: Any) -> str:
    """Serialize a participant or message for Mermaid sequence syntax."""
    cleaned = _normalize_display_text(value, replacements="#;%")
    return "(end)" if cleaned == "end" else cleaned


def _sanitize_href(href: str) -> str:
    """Return a safe encoded relative reference, or ``""`` when invalid."""
    raw = unicodedata.normalize("NFC", str(href))
    if (
        not raw
        or "\\" in raw
        or any(
            char.isspace() and char not in {" "}
            or not char.isprintable()
            for char in raw
        )
    ):
        return ""
    decoded = unicodedata.normalize("NFC", unquote(raw))
    if (
        "\\" in decoded
        or any(not char.isprintable() for char in decoded)
        or decoded.startswith("/")
    ):
        return ""
    try:
        parsed = urlsplit(decoded)
    except ValueError:
        return ""
    if parsed.scheme or parsed.netloc:
        return ""
    encoded = quote(decoded, safe=_HREF_SAFE)
    return encoded if len(encoded) <= _HREF_LIMIT else ""


def _class_name_is_safe(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= 64
        and _CLASS_SAFE.fullmatch(value) is not None
        and value.casefold() not in _RESERVED_CLASS_NAMES
    )


def _normalize_direction(value: Any) -> str | None:
    if isinstance(value, str) and value in _ALLOWED_DIRECTIONS:
        return value
    return None


def _normalize_node_classes(value: Any, *, strict: bool = False) -> dict[str, str]:
    if not isinstance(value, Mapping):
        if strict and value is not None:
            raise PluginError("node_classes must be an object.")
        return {}
    classes: dict[str, str] = {}
    for node, class_name in value.items():
        if _class_name_is_safe(class_name):
            classes[str(node)] = class_name
        elif strict:
            raise PluginError(
                f"node class for {node!r} must be a non-reserved safe identifier "
                "of at most 64 characters."
            )
    return classes


def _normalize_category_colors(value: Any, *, strict: bool = False) -> dict[str, str]:
    if not isinstance(value, Mapping):
        if strict and value is not None:
            raise PluginError("category_colors must be an object.")
        return {}
    colors: dict[str, str] = {}
    for class_name, color in value.items():
        if (
            _class_name_is_safe(class_name)
            and isinstance(color, str)
            and _COLOR_SAFE.fullmatch(color)
        ):
            colors[class_name] = color
        elif strict:
            raise PluginError(
                f"category color for {class_name!r} must use a non-reserved safe "
                "class name of at most 64 characters and #RGB or #RRGGBB color."
            )
    return colors


def _normalize_style(
    style: Mapping[str, Any] | None, *, strict: bool = False
) -> dict[str, Any]:
    if style is None:
        return {}
    if not isinstance(style, Mapping):
        if strict:
            raise PluginError("diagram style hook must return an object.")
        return {}
    normalized: dict[str, Any] = {}
    direction = _normalize_direction(style.get("direction"))
    if direction:
        normalized["direction"] = direction
    elif strict and "direction" in style:
        raise PluginError("direction must be one of BT, LR, RL, TB, or TD.")
    node_classes = _normalize_node_classes(style.get("node_classes"), strict=strict)
    if node_classes:
        normalized["node_classes"] = node_classes
    category_colors = _normalize_category_colors(
        style.get("category_colors"), strict=strict
    )
    if category_colors:
        normalized["category_colors"] = category_colors
    return normalized


def _merge_style(target: dict[str, Any], update: Mapping[str, Any]) -> None:
    if "direction" in update:
        target["direction"] = update["direction"]
    if update.get("node_classes"):
        target.setdefault("node_classes", {}).update(update["node_classes"])
    if update.get("category_colors"):
        target.setdefault("category_colors", {}).update(update["category_colors"])


def _load_style_hook(component: Mapping[str, Any], root: str | Path):
    return load_entry_point(str(component["entry_point"]), root=root)


def _roots_equal(left: str | Path, right: str | Path) -> bool:
    return resolved_paths_equal(left, right)


def _read_style_components(
    root: str | Path, *, strict_plugin_errors: bool
) -> list[dict[str, Any]]:
    try:
        return diagram_style_components(root=root)
    except PluginError:
        if strict_plugin_errors:
            raise
        return []


def _style_components(
    root: str | Path,
    *,
    fallback_root: str | Path | None,
    strict_plugin_errors: bool,
) -> list[tuple[dict[str, Any], str | Path]]:
    components = _read_style_components(root, strict_plugin_errors=strict_plugin_errors)
    if components or fallback_root is None or _roots_equal(root, fallback_root):
        return [(component, root) for component in components]

    fallback_components = _read_style_components(
        fallback_root, strict_plugin_errors=strict_plugin_errors
    )
    return [(component, fallback_root) for component in fallback_components]


def resolve_diagram_style(
    context: Mapping[str, Any] | None,
    *,
    root: str | Path = ".",
    fallback_root: str | Path | None = None,
    include_plugins: bool = True,
    strict_plugin_errors: bool = False,
) -> dict[str, Any]:
    """Return normalized style options from installed diagram-style hooks.

    Hooks receive a plain context mapping and may return only data hints:
    ``direction``, ``node_classes``, and ``category_colors``. Invalid hook
    results are ignored unless ``strict_plugin_errors`` is true.
    """
    merged: dict[str, Any] = {}
    if not include_plugins:
        return merged
    style_context = dict(context or {})
    components = sorted(
        _style_components(
            root,
            fallback_root=fallback_root,
            strict_plugin_errors=strict_plugin_errors,
        ),
        key=lambda item: str(item[0].get("ref", "")),
    )
    for component, component_root in components:
        try:
            hook = _load_style_hook(component, component_root)
            normalized = _normalize_style(
                hook(dict(style_context)), strict=strict_plugin_errors
            )
        except Exception:
            if strict_plugin_errors:
                raise
            continue
        _merge_style(merged, normalized)
    return merged


def _append_style_lines(
    lines: list[str],
    aliases_by_node: Mapping[str, str] | Iterable[tuple[str, str]],
    style: Mapping[str, Any] | None,
    *,
    reserved_classes: set[str] | None = None,
) -> None:
    normalized = _normalize_style(style)
    node_classes = normalized.get("node_classes", {})
    category_colors = normalized.get("category_colors", {})
    reserved = reserved_classes or set()
    aliases = (
        list(aliases_by_node.items())
        if isinstance(aliases_by_node, Mapping)
        else list(aliases_by_node)
    )
    assigned = [
        (alias, node_classes[node])
        for node, alias in aliases
        if node in node_classes
        and node_classes[node] not in reserved
    ]
    used_classes = {class_name for _alias, class_name in assigned}
    for class_name in sorted(used_classes & set(category_colors)):
        if class_name in reserved:
            continue
        color = category_colors[class_name]
        lines.append(f"    classDef {class_name} fill:{color},stroke:{color}")
    for alias, class_name in assigned:
        lines.append(f"    class {alias} {class_name}")


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
        lines.append(f"    participant {alias} as {_sequence_text(actor)}")
    for interaction in interactions:
        arrow = "-->>" if interaction.get("dashed") else "->>"
        src = aliases[interaction["from"]]
        dst = aliases[interaction["to"]]
        lines.append(f"    {src}{arrow}{dst}: {_sequence_text(interaction['label'])}")
    lines.append("```")
    return "\n".join(lines)


def flowchart(
    nodes: Iterable[str],
    edges: Iterable[tuple[str, str]],
    *,
    direction: str = "TD",
    links: Mapping[str, str] | None = None,
    highlight_edges: Iterable[tuple[str, str]] | None = None,
    style: Mapping[str, Any] | None = None,
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
    normalized_style = _normalize_style(style)
    direction = normalized_style.get(
        "direction", _normalize_direction(direction) or "TD"
    )
    alias: dict[str, str] = {}
    lines = [_FENCE, f"flowchart {direction}"]
    for node in dict.fromkeys(nodes):
        alias[node] = f"n{len(alias)}"
        lines.append(f'    {alias[node]}["{_flowchart_label(node)}"]')
    seen_edges: set[tuple[str, str]] = set()
    for src, dst in edges:
        edge = (src, dst)
        if edge in seen_edges or src not in alias or dst not in alias:
            continue
        seen_edges.add(edge)
        arrow = "==>" if edge in highlight else "-->"
        lines.append(f"    {alias[src]} {arrow} {alias[dst]}")
    for node in alias:
        href = link_map.get(node)
        if href:
            safe_href = _sanitize_href(href)
            if safe_href:
                lines.append(f'    click {alias[node]} "{safe_href}"')
    _append_style_lines(lines, alias, normalized_style)
    lines.append("```")
    return "\n".join(lines)


def _positive_index(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        digits = value.lstrip("0")
        if not digits or len(digits) > _STEP_INDEX_DIGIT_LIMIT:
            return None
        try:
            parsed = int(digits)
        except (ValueError, OverflowError):
            return None
        return parsed if parsed > 0 else None
    return None


def _transfer_endpoint(
    transfer: Mapping,
    key: str,
    symbol_key: str,
    aliases_by_source_index: Mapping[int, str],
    aliases_by_ordinal: Mapping[int, str],
    aliases_by_symbol: Mapping[str, str],
) -> str | None:
    step_index = _positive_index(transfer.get(key))
    if step_index is not None:
        source_alias = aliases_by_source_index.get(step_index)
        if source_alias is not None:
            return source_alias
        ordinal_alias = aliases_by_ordinal.get(step_index)
        if ordinal_alias is not None:
            return ordinal_alias
    symbol = str(transfer.get(symbol_key) or "")
    return aliases_by_symbol.get(symbol)


def _link_for_step(step: Mapping, module_page_map: Mapping[str, str]) -> str:
    filepath = step.get("file")
    if not filepath:
        return ""
    page = module_page_map.get(str(filepath))
    return f"../modules/{page}.md" if page else ""


def _render_labeled_edge(
    source: str, destination: str, label: Any, *, dashed: bool
) -> str:
    safe_label = _flowchart_label(label)
    if dashed:
        return f'    {source} -. "{safe_label}" .-> {destination}'
    return f'    {source} -->|"{safe_label}"| {destination}'


def data_flow_diagram(
    data_flow: Mapping,
    module_page_map: Mapping[str, str] | None = None,
    *,
    style: Mapping[str, Any] | None = None,
) -> str:
    """Render a labeled Mermaid diagram for one static data-flow summary."""
    page_map = dict(module_page_map or {})
    steps = list(data_flow.get("steps", []))
    aliases_by_source_index: dict[int, str] = {}
    aliases_by_ordinal: dict[int, str] = {}
    aliases_by_symbol: dict[str, str] = {}
    normalized_style = _normalize_style(style)
    direction = normalized_style.get("direction", "LR")
    lines = [_FENCE, f"flowchart {direction}"]
    style_aliases: list[tuple[str, str]] = []
    step_records: list[tuple[Mapping, str]] = []

    for ordinal, step in enumerate(steps, start=1):
        source_index = _positive_index(step.get("index"))
        number = source_index or ordinal
        alias = f"s{ordinal}"
        aliases_by_ordinal[ordinal] = alias
        if source_index is not None:
            aliases_by_source_index.setdefault(source_index, alias)
        symbol = str(step.get("symbol") or "?")
        aliases_by_symbol.setdefault(symbol, alias)
        label = f"{number}. {symbol}"
        style_aliases.append((label, alias))
        step_records.append((step, alias))
        lines.append(f'    {alias}["{_flowchart_label(label)}"]')

    seen_edges: set[tuple[str, str, str, bool]] = set()
    for transfer in data_flow.get("transfers", []):
        src = _transfer_endpoint(
            transfer,
            "from_step",
            "from",
            aliases_by_source_index,
            aliases_by_ordinal,
            aliases_by_symbol,
        )
        dst = _transfer_endpoint(
            transfer,
            "to_step",
            "to",
            aliases_by_source_index,
            aliases_by_ordinal,
            aliases_by_symbol,
        )
        if not src or not dst:
            continue
        label = transfer.get("call") or transfer.get("kind") or "data"
        dashed = transfer.get("kind") in {"external", "unresolved"}
        edge_key = (src, dst, _normalize_display_text(label), dashed)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)
        lines.append(_render_labeled_edge(src, dst, label, dashed=dashed))

    boundary_aliases = []
    for offset, boundary in enumerate(data_flow.get("boundaries", [])):
        src = None
        step_index = _positive_index(boundary.get("step_index"))
        if step_index is not None:
            src = aliases_by_source_index.get(step_index)
            if src is None:
                src = aliases_by_ordinal.get(step_index)
        if src is None:
            src = aliases_by_symbol.get(str(boundary.get("step") or ""))
        if src is None:
            continue
        alias = f"b{offset}"
        label = f"{boundary.get('kind', 'boundary')} {boundary.get('target', '?')}"
        lines.append(f'    {alias}["{_flowchart_label(label)}"]')
        lines.append(_render_labeled_edge(src, alias, label, dashed=True))
        boundary_aliases.append(alias)

    for step, alias in step_records:
        href = _link_for_step(step, page_map)
        safe_href = _sanitize_href(href) if href else ""
        if safe_href:
            lines.append(f'    click {alias} "{safe_href}"')

    if boundary_aliases:
        lines.append("    classDef boundary stroke:#b45309,stroke-dasharray: 4 2")
        for alias in boundary_aliases:
            lines.append(f"    class {alias} boundary")

    _append_style_lines(
        lines, style_aliases, normalized_style, reserved_classes={"boundary"}
    )
    lines.append("```")
    return "\n".join(lines)
