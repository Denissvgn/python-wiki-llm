"""Structured context budgeting — return priority-ranked, token-budgeted
codebase context for LLM agents.

Priority tiers:

- **high**: files changed in the last commit → full deep inventory detail
- **medium**: 1-hop import neighbors of changed files → slim detail
- **low**: everything else → names only

Usage::

    llm-wiki context --budget 32000
    llm-wiki context --budget 8000 --format markdown
    llm-wiki context --budget 32000 --focus all
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .extract_cmd import _git_changed_files, get_inventory_result, print_inventory_failures
from ..config import validate_path


# ── Token estimation ──────────────────────────────────────────────────


def _estimate_tokens(text: str) -> int:
    """Approximate token count using the ~4 chars/token heuristic.

    No external dependency — good enough for budgeting (within ~10-20%).
    """
    return len(text) // 4


# ── Import graph ──────────────────────────────────────────────────────


def _build_import_graph(inventory: dict) -> dict[str, set[str]]:
    """Build a bidirectional import adjacency map from a deep inventory.

    For each file A that imports a symbol from file B (both present in *inventory*),
    adds edges A→B and B→A.  External / stdlib imports are silently skipped.

    Returns ``{filepath: {neighbor_filepaths}}`` with every key appearing
    even if it has no neighbors.
    """
    # Build a lookup: dotted module path → inventory filepath
    # e.g.  "llm_wiki_cli.config" → "src/llm_wiki_cli/config.py"
    module_to_file: dict[str, str] = {}
    for filepath in inventory:
        # Convert filepath to dotted module path
        mod = _filepath_to_module(filepath)
        if mod:
            module_to_file[mod] = filepath

    graph: dict[str, set[str]] = {fp: set() for fp in inventory}

    for filepath, file_data in inventory.items():
        for imp in file_data.get("imports", []):
            imp_module = imp.get("module", "")
            if not imp_module:
                continue

            # Try exact match, then parent module (for ``from pkg.mod import X``)
            target = module_to_file.get(imp_module)
            if target is None:
                # Try progressively shorter prefixes
                parts = imp_module.split(".")
                for i in range(len(parts) - 1, 0, -1):
                    candidate = ".".join(parts[:i])
                    target = module_to_file.get(candidate)
                    if target is not None:
                        break

            if target is not None and target != filepath:
                graph[filepath].add(target)
                graph[target].add(filepath)

    return graph


def _filepath_to_module(filepath: str) -> str | None:
    """Convert ``"src/llm_wiki_cli/config.py"`` → ``"llm_wiki_cli.config"``.

    Strips a leading ``src/`` directory and the ``.py`` suffix, then
    converts path separators to dots.  Returns None for non-Python files.
    """
    p = Path(filepath)
    if p.suffix != ".py":
        return None

    parts = list(p.with_suffix("").parts)

    # Strip leading "src" directory (common in Python projects)
    if parts and parts[0] == "src":
        parts = parts[1:]

    # Strip __init__ (package init files map to the package itself)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts) if parts else None


# ── Classification ────────────────────────────────────────────────────


def _classify_files(
    all_files: list[str],
    changed: list[str] | None,
    import_graph: dict[str, set[str]],
    focus: str,
) -> dict[str, str]:
    """Assign a priority tier to every file in the inventory.

    Returns ``{filepath: "high"|"medium"|"low"}``.
    """
    if focus == "all":
        return {fp: "high" for fp in all_files}

    classification: dict[str, str] = {}
    changed_set = set(changed) if changed else set()

    # High: changed files
    for fp in all_files:
        if fp in changed_set:
            classification[fp] = "high"

    # Medium: 1-hop neighbors of changed files
    for fp in changed_set:
        for neighbor in import_graph.get(fp, set()):
            if neighbor not in classification:
                classification[neighbor] = "medium"

    # Low: everything else
    for fp in all_files:
        if fp not in classification:
            classification[fp] = "low"

    return classification


# ── Detail-level serializers ──────────────────────────────────────────


def _deep_entry(file_data: dict) -> dict:
    """Full detail: classes with methods, params, docstrings, imports."""
    return {k: v for k, v in file_data.items() if k != "language"}


def _slim_entry(file_data: dict) -> dict:
    """Slim detail: class names/bases/line, function names/lines."""
    return {
        "classes": [
            {"name": c["name"], "bases": c.get("bases", []), "line": c.get("line")}
            for c in file_data.get("classes", [])
        ],
        "functions": [
            {"name": f["name"], "line": f.get("line")}
            for f in file_data.get("functions", [])
        ],
    }


def _summary_entry(file_data: dict) -> dict:
    """Names only: lists of class names and function names."""
    entry: dict[str, list[str]] = {}
    cls_names = [c["name"] for c in file_data.get("classes", [])]
    fn_names = [f["name"] for f in file_data.get("functions", [])]
    if cls_names:
        entry["classes"] = cls_names
    if fn_names:
        entry["functions"] = fn_names
    return entry


_DETAIL_SERIALIZERS = {
    "deep": _deep_entry,
    "slim": _slim_entry,
    "summary": _summary_entry,
}

_PREFERRED_DETAILS = {
    "high": "deep",
    "medium": "slim",
    "low": "summary",
}

_DETAIL_FALLBACKS = {
    "high": ("deep", "slim", "summary"),
    "medium": ("slim", "summary"),
    "low": ("summary",),
}


# ── Budgeting ─────────────────────────────────────────────────────────


def _build_context_payload(
    inventory: dict,
    classification: dict[str, str],
    budget: int,
) -> dict:
    """Build a token-budgeted context payload.

    Greedy allocation: high-priority files first, then medium, then low.
    Files are downgraded to smaller detail levels before they are omitted.

    Returns::

        {
            "budget": <requested>,
            "used": <estimated tokens>,
            "truncated": <whether files were downgraded or omitted>,
            "omitted_files": ["path/too_large.py"],
            "downgraded_files": {"path/file.py": "summary"},
            "files": {
                "path/file.py": {"priority": "high", "detail": "deep", ...detail...},
                ...
            }
        }
    """
    files_out: dict[str, dict] = {}
    omitted_files: list[str] = []
    downgraded_files: dict[str, str] = {}
    used = 0

    # Process tiers in priority order
    for tier in ("high", "medium", "low"):
        tier_files = sorted(
            fp for fp, pri in classification.items() if pri == tier
        )
        for fp in tier_files:
            file_data = inventory.get(fp, {})
            selected_entry: dict | None = None
            selected_tokens = 0
            selected_detail = ""

            for detail in _DETAIL_FALLBACKS[tier]:
                entry = _build_entry(file_data, tier, detail)
                entry_tokens = _entry_tokens(fp, entry)
                if used + entry_tokens <= budget:
                    selected_entry = entry
                    selected_tokens = entry_tokens
                    selected_detail = detail
                    break

            if selected_entry is None:
                omitted_files.append(fp)
                continue

            files_out[fp] = selected_entry
            used += selected_tokens
            if selected_detail != _PREFERRED_DETAILS[tier]:
                downgraded_files[fp] = selected_detail

    return {
        "budget": budget,
        "used": used,
        "truncated": bool(omitted_files or downgraded_files),
        "omitted_files": omitted_files,
        "downgraded_files": downgraded_files,
        "files": files_out,
    }


def _build_entry(file_data: dict, priority: str, detail: str) -> dict:
    """Serialize one file at a specific detail level."""
    entry = _DETAIL_SERIALIZERS[detail](file_data)
    entry["priority"] = priority
    entry["detail"] = detail
    return entry


def _entry_tokens(filepath: str, entry: dict) -> int:
    return _estimate_tokens(json.dumps({filepath: entry}))


# ── Markdown renderer ─────────────────────────────────────────────────


def _render_markdown(payload: dict) -> str:
    """Render the context payload as agent-friendly markdown."""
    lines: list[str] = []
    lines.append(f"# Context Budget: {payload['used']} / {payload['budget']} tokens")
    lines.append("")

    tier_labels = {
        "high": "Changed Files (High Priority)",
        "medium": "Neighbor Files (Medium Priority)",
        "low": "Index (Low Priority)",
    }

    for tier in ("high", "medium", "low"):
        tier_files = {
            fp: data for fp, data in payload["files"].items()
            if data.get("priority") == tier
        }
        if not tier_files:
            continue

        lines.append(f"## {tier_labels[tier]}")
        lines.append("")

        for fp, data in sorted(tier_files.items()):
            lines.append(f"### `{fp}`")
            lines.append("")

            for cls in data.get("classes", []):
                if isinstance(cls, str):
                    lines.append(f"- class **{cls}**")
                else:
                    bases = ", ".join(cls.get("bases", []))
                    base_str = f"({bases})" if bases else ""
                    lines.append(f"- class **{cls['name']}**{base_str}")
                    if cls.get("docstring"):
                        lines.append(f"  > {cls['docstring'].splitlines()[0]}")
                    for method in cls.get("methods", []):
                        params = ", ".join(
                            p.get("name", "") for p in method.get("params", [])
                        )
                        ret = f" → {method['return_type']}" if method.get("return_type") else ""
                        async_prefix = "async " if method.get("is_async") else ""
                        lines.append(f"  - {async_prefix}`{method['name']}({params})`{ret}")

            for fn in data.get("functions", []):
                if isinstance(fn, str):
                    lines.append(f"- def **{fn}**()")
                else:
                    params = ", ".join(
                        p.get("name", "") for p in fn.get("params", [])
                    )
                    ret = f" → {fn['return_type']}" if fn.get("return_type") else ""
                    async_prefix = "async " if fn.get("is_async") else ""
                    lines.append(f"- {async_prefix}def **{fn['name']}**({params}){ret}")
                    if fn.get("docstring"):
                        lines.append(f"  > {fn['docstring'].splitlines()[0]}")

            lines.append("")

    omitted = payload.get("omitted_files", [])
    if omitted:
        lines.append("## Omitted Files")
        lines.append("")
        for fp in omitted:
            lines.append(f"- `{fp}`")
        lines.append("")

    return "\n".join(lines)


# ── CLI entry point ───────────────────────────────────────────────────


def run(args) -> None:
    src_dir: str = getattr(args, "src_dir", ".")
    budget: int = getattr(args, "budget", 32000)
    fmt: str = getattr(args, "format", "json")
    focus: str = getattr(args, "focus", "changed")

    validate_path(src_dir, "--src-dir")

    # 1. Get full deep inventory (imports needed for graph building)
    inventory_result = get_inventory_result(src_dir, deep=True)
    if inventory_result.failed:
        print_inventory_failures(inventory_result)
        sys.exit(1)
    inventory = inventory_result.inventory

    if not inventory:
        print("{}" if fmt == "json" else "No source files found.")
        return

    # 2. Determine changed files
    changed: list[str] | None = None
    if focus == "changed":
        changed = _git_changed_files(src_dir)
        if changed is None:
            print("Warning: Could not get changed files from git. Treating all files as high priority.",
                  file=sys.stderr, flush=True)
            focus = "all"
        elif not changed:
            print("Warning: No files changed in the last commit. Treating all files as high priority.",
                  file=sys.stderr, flush=True)
            focus = "all"
        else:
            # Normalise changed paths to match inventory keys
            changed = _normalise_changed_paths(changed, inventory)

    # 3. Build import graph and classify files
    import_graph = _build_import_graph(inventory)
    classification = _classify_files(list(inventory.keys()), changed, import_graph, focus)

    # 4. Build budgeted payload
    payload = _build_context_payload(inventory, classification, budget)

    # 5. Output
    if fmt == "markdown":
        print(_render_markdown(payload))
    else:
        print(json.dumps(payload, indent=2))


def _normalise_changed_paths(
    changed: list[str], inventory: dict
) -> list[str]:
    """Match git-reported changed paths to inventory keys.

    Git paths are relative to the repo root; inventory keys may include
    a leading ``src/`` or similar prefix.  This function tries exact
    match first, then suffix match against inventory keys.
    """
    inv_keys = list(inventory.keys())
    normalised: list[str] = []
    for ch in changed:
        if ch in inventory:
            normalised.append(ch)
            continue
        # Try suffix matching
        for key in inv_keys:
            if key.endswith(ch) or ch.endswith(key):
                normalised.append(key)
                break
    return normalised
