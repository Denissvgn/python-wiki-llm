"""Entry-point detection and user-flow assembly.

An *entry point* is a function/class a user (or another system) can reach
directly: a public API symbol, a framework-decorated handler, or a process
entry. :func:`get_entry_points` finds them from a deep inventory (plus optional
console-script declarations), and :func:`build_flow` traces the resolved call
edges from an entry point into an ordered, bounded, de-cycled call path.

This module is deterministic and consumes only the structural inventory and
pre-computed call edges (see ``extract_cmd.resolve_call_edges``); it performs no
LLM calls and tolerates inventories that omit optional fields.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .imports import build_module_path_resolver

# ── Entry-point categories ────────────────────────────────────────────

CATEGORY_CLI = "cli"
CATEGORY_API = "api"
CATEGORY_MCP = "mcp"
CATEGORY_HTTP = "http"
CATEGORY_PROCESS = "process"

CATEGORIES = (CATEGORY_CLI, CATEGORY_API, CATEGORY_MCP, CATEGORY_HTTP, CATEGORY_PROCESS)

# Decorator leaf names that mark a callable as a framework entry point. CLI
# decorators may appear bare (``from click import command``); HTTP/MCP
# decorators are required to be attribute-form (``app.route``, ``server.tool``)
# to avoid matching unrelated bare decorators.
_CLI_DECORATORS = frozenset({"command", "group"})
_HTTP_DECORATORS = frozenset(
    {"route", "get", "post", "put", "delete", "patch", "head", "options"}
)
_MCP_DECORATORS = frozenset({"tool", "resource", "prompt"})

_DEFAULT_FLOW_DEPTH = 6


def _entry(
    category: str, file: str | None, symbol: str, label: str | None = None
) -> dict:
    return {
        "category": category,
        "file": file,
        "symbol": symbol,
        "label": label or symbol,
    }


def _local_symbols(data: dict) -> set[str]:
    """Names of functions and classes defined in a single file entry."""
    names = {fn["name"] for fn in data.get("functions", [])}
    names |= {cls["name"] for cls in data.get("classes", [])}
    return names


def _iter_callables(inventory: dict):
    """Yield ``(filepath, symbol, fn)`` for every function, method, and decorated
    nested function (e.g. factory-registered ``@app.route``/``@server.tool``)."""
    for filepath, data in inventory.items():
        for fn in data.get("functions", []):
            yield filepath, fn["name"], fn
        for cls in data.get("classes", []):
            for method in cls.get("methods", []):
                yield filepath, f"{cls['name']}.{method['name']}", method
        for fn in data.get("nested_functions", []):
            yield filepath, fn["name"], fn


# ── Detectors ─────────────────────────────────────────────────────────


def _detect_api(inventory: dict) -> list[dict]:
    """Public API entry points: ``__all__`` exports that resolve to a local def."""
    entries: list[dict] = []
    for filepath, data in inventory.items():
        local = _local_symbols(data)
        for name in data.get("all_exports", []):
            if name in local:
                entries.append(_entry(CATEGORY_API, filepath, name))
    return entries


def _decorator_leaf(decorator: str) -> tuple[str, bool]:
    """Return ``(leaf_name, is_dotted)`` for a decorator string.

    ``"app.route('/x')"`` -> ``("route", True)``; ``"command"`` -> ``("command", False)``.
    """
    base = decorator.split("(", 1)[0]
    return base.rsplit(".", 1)[-1], "." in base


def _detect_decorated(
    inventory: dict, leaves: frozenset[str], category: str, *, allow_bare: bool
) -> list[dict]:
    entries: list[dict] = []
    for filepath, symbol, fn in _iter_callables(inventory):
        for decorator in fn.get("decorators", []):
            leaf, dotted = _decorator_leaf(decorator)
            if leaf in leaves and (dotted or allow_bare):
                entries.append(_entry(category, filepath, symbol))
                break
    return entries


def _detect_process(inventory: dict, console_scripts: list[dict] | None) -> list[dict]:
    """Process entry points: ``__main__`` guards and console-script targets."""
    entries: list[dict] = []
    for filepath, data in inventory.items():
        if not data.get("main_block"):
            continue
        symbol = "main" if "main" in _local_symbols(data) else "__main__"
        entries.append(
            _entry(CATEGORY_PROCESS, filepath, symbol, label=Path(filepath).stem)
        )

    resolver = build_module_path_resolver(inventory)
    for script in console_scripts or []:
        file = _resolve_module_file(script["module"], resolver)
        entries.append(
            _entry(CATEGORY_PROCESS, file, script["attr"], label=script["name"])
        )
    return entries


def _resolve_module_file(module: str, resolver) -> str | None:
    candidates = resolver.candidates(module, "")
    return next(iter(candidates)) if len(candidates) == 1 else None


# ── Console-script parsing (pyproject.toml ``[project.scripts]``) ──────


def _parse_scripts_section(text: str) -> list[dict]:
    """Parse ``[project.scripts]`` entries without a TOML dependency.

    Returns ``[{"name", "module", "attr"}]``. ``attr`` is empty when the target
    omits the ``module:attr`` colon form.
    """
    scripts: list[dict] = []
    in_section = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            in_section = line == "[project.scripts]"
            continue
        if not in_section or not line or line.startswith("#") or "=" not in line:
            continue
        name, _, target = line.partition("=")
        target = target.strip().strip('"').strip("'")
        module, _, attr = target.partition(":")
        scripts.append(
            {"name": name.strip().strip('"').strip("'"), "module": module, "attr": attr}
        )
    return scripts


def read_console_scripts(project_root: str = ".") -> list[dict]:
    """Read ``[project.scripts]`` from ``pyproject.toml`` (best-effort)."""
    pyproject = Path(project_root) / "pyproject.toml"
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return []
    return _parse_scripts_section(text)


# ── Aggregation + stable ids ──────────────────────────────────────────


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_") or "entry"


def _label_rank(entry: dict) -> int:
    """Prefer a specific label (script name, symbol) over the bare module stem."""
    stem = Path(entry["file"]).stem if entry.get("file") else ""
    return 0 if entry["label"] == stem else 1


def _dedup(entries: list[dict]) -> list[dict]:
    """Collapse entries sharing ``(category, file, symbol)``, keeping the best label."""
    chosen: dict[tuple, dict] = {}
    for entry in entries:
        key = (entry["category"], entry.get("file"), entry["symbol"])
        current = chosen.get(key)
        if current is None or _label_rank(entry) > _label_rank(current):
            chosen[key] = entry
    return list(chosen.values())


def _assign_ids(entries: list[dict]) -> list[dict]:
    """Assign stable, collision-safe ids of the form ``<category>-<slug>``.

    On a base-id collision the module stem is folded in; a final counter
    guarantees uniqueness deterministically.
    """
    bases = [f"{e['category']}-{_slug(e['label'])}" for e in entries]
    base_counts = Counter(bases)
    used: Counter = Counter()
    for entry, base in zip(entries, bases):
        candidate = base
        if base_counts[base] > 1 and entry.get("file"):
            candidate = f"{base}-{_slug(Path(entry['file']).stem)}"
        seen = used[candidate]
        used[candidate] += 1
        entry["id"] = candidate if seen == 0 else f"{candidate}-{seen + 1}"
    return entries


def get_entry_points(
    inventory: dict, *, console_scripts: list[dict] | None = None
) -> list[dict]:
    """Detect user-reachable entry points from a deep inventory.

    Returns a deterministically ordered list of
    ``{"id", "category", "file", "symbol", "label"}`` records. ``console_scripts``
    are the parsed ``[project.scripts]`` entries (see :func:`read_console_scripts`).
    """
    entries: list[dict] = []
    entries += _detect_decorated(
        inventory, _CLI_DECORATORS, CATEGORY_CLI, allow_bare=True
    )
    entries += _detect_api(inventory)
    entries += _detect_decorated(
        inventory, _MCP_DECORATORS, CATEGORY_MCP, allow_bare=False
    )
    entries += _detect_decorated(
        inventory, _HTTP_DECORATORS, CATEGORY_HTTP, allow_bare=False
    )
    entries += _detect_process(inventory, console_scripts)

    entries = _dedup(entries)
    entries.sort(key=lambda e: (e["category"], e.get("file") or "", e["symbol"]))
    return _assign_ids(entries)


# ── Flow assembly ─────────────────────────────────────────────────────


def _build_adjacency(edges: list[dict]) -> dict[tuple, list[dict]]:
    adjacency: dict[tuple, list[dict]] = {}
    for edge in edges:
        key = (edge["from"]["file"], edge["from"]["symbol"])
        adjacency.setdefault(key, []).append(edge)
    return adjacency


def _edge_metadata(edge: dict) -> dict:
    metadata = {
        "from": dict(edge["from"]),
        "to": dict(edge["to"]),
        "name": edge.get("name", ""),
        "kind": edge.get("kind", "unknown"),
        "line": edge.get("line", 0),
    }
    for key in ("args", "kwargs"):
        if key in edge:
            metadata[key] = edge[key]
    return metadata


def _flow_step_from_edge(edge: dict, depth: int) -> dict:
    return {
        "depth": depth,
        "file": edge["to"]["file"],
        "symbol": edge["to"]["symbol"],
        "kind": edge["kind"],
        "edge": _edge_metadata(edge),
    }


def _expand_flow(node, depth, adjacency, steps, visited, max_depth, state) -> None:
    if depth >= max_depth:
        if adjacency.get(node):
            state["truncated"] = True
        return
    for edge in adjacency.get(node, []):
        target = (edge["to"]["file"], edge["to"]["symbol"])
        steps.append(_flow_step_from_edge(edge, depth + 1))
        if (
            edge["kind"] == "internal"
            and edge["to"]["file"] is not None
            and target not in visited
        ):
            visited.add(target)
            _expand_flow(target, depth + 1, adjacency, steps, visited, max_depth, state)


def _modules_touched(steps: list[dict]) -> list[str]:
    modules: list[str] = []
    seen: set[str] = set()
    for step in steps:
        file = step["file"]
        if step["kind"] in ("entry", "internal") and file and file not in seen:
            seen.add(file)
            modules.append(file)
    return modules


def build_flow(
    entry: dict, edges: list[dict], *, max_depth: int = _DEFAULT_FLOW_DEPTH
) -> dict:
    """Trace an ordered call path from *entry* through resolved *edges*.

    Performs a depth-first preorder walk of internal call edges, bounded by
    *max_depth* and de-cycled by tracking visited ``(file, symbol)`` nodes.
    External and unresolved calls appear as leaf steps (never expanded), so
    boundary crossings remain visible. Returns
    ``{"entry", "steps", "modules_touched", "truncated"}``.
    """
    adjacency = _build_adjacency(edges)
    start = (entry["file"], entry["symbol"])
    steps = [
        {"depth": 0, "file": entry["file"], "symbol": entry["symbol"], "kind": "entry"}
    ]
    state = {"truncated": False}
    _expand_flow(start, 0, adjacency, steps, {start}, max_depth, state)
    return {
        "entry": entry,
        "steps": steps,
        "modules_touched": _modules_touched(steps),
        "truncated": state["truncated"],
    }
