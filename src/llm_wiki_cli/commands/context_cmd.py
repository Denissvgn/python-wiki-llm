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

from fnmatch import fnmatch
import json
import sys
from pathlib import Path, PurePosixPath

from .extract_cmd import _git_changed_files, get_inventory_result
from ..config import validate_source_root
from ..services.io import write_text_output


PROTOCOL_VERSION = "llm-wiki-context/v1"

_REQUEST_KEYS = {"protocol", "budget_tokens", "focus", "format", "filters"}
_FILTER_KEYS = {"language", "module"}
_FOCUS_VALUES = {"changed", "neighbors", "all"}
_FORMATS = {"json", "markdown"}


class ProtocolRequestError(ValueError):
    """Validation error for Wiki-as-Context protocol requests."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


def _extractor_failure_message(inventory_result) -> str:
    """Return a compact, structured error message for extractor failures."""
    details = []
    for status in inventory_result.failed:
        detail = f": {status.message}" if status.message else ""
        details.append(f"{status.language} extraction failed{detail}")
    return "; ".join(details) or "Source extraction failed."


def get_inventory(src_dir: str, *, deep: bool = False) -> dict:
    """Context-local inventory helper kept patchable for protocol tests."""
    inventory_result = get_inventory_result(src_dir, deep=deep)
    if inventory_result.failed:
        raise ProtocolRequestError(_extractor_failure_message(inventory_result), "src_dir")
    return inventory_result.inventory


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
    include_neighbors: bool = True,
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
    if include_neighbors:
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


# ── Wiki-as-Context protocol ──────────────────────────────────────────


def _read_protocol_request(source: str) -> dict:
    """Read and validate a Wiki-as-Context protocol request."""
    try:
        raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    except OSError as exc:
        raise ProtocolRequestError(f"Could not read request: {exc}", "request") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProtocolRequestError(f"Invalid JSON: {exc.msg}", "request") from exc

    return _validate_protocol_request(data)


def _validate_protocol_request(data: object) -> dict:
    """Return a normalised protocol request or raise ``ProtocolRequestError``."""
    if not isinstance(data, dict):
        raise ProtocolRequestError("Request must be a JSON object.", "request")

    unknown = sorted(set(data) - _REQUEST_KEYS)
    if unknown:
        raise ProtocolRequestError(f"Unknown request field: {unknown[0]}", unknown[0])

    protocol = data.get("protocol")
    if protocol != PROTOCOL_VERSION:
        raise ProtocolRequestError(
            f"Unsupported protocol: {protocol!r}. Expected {PROTOCOL_VERSION!r}.",
            "protocol",
        )

    if "budget_tokens" not in data:
        raise ProtocolRequestError("Missing required field: budget_tokens", "budget_tokens")
    budget = data["budget_tokens"]
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1:
        raise ProtocolRequestError("budget_tokens must be a positive integer.", "budget_tokens")

    fmt = data.get("format", "json")
    if fmt not in _FORMATS:
        raise ProtocolRequestError("format must be 'json' or 'markdown'.", "format")

    focus = _normalise_protocol_focus(data.get("focus", ["changed", "neighbors"]))
    filters = _normalise_protocol_filters(data.get("filters", {}))

    return {
        "protocol": PROTOCOL_VERSION,
        "budget_tokens": budget,
        "focus": focus,
        "format": fmt,
        "filters": filters,
    }


def _normalise_protocol_focus(raw_focus: object) -> list[str]:
    if not isinstance(raw_focus, list) or not raw_focus:
        raise ProtocolRequestError("focus must be a non-empty list.", "focus")

    if any(not isinstance(item, str) for item in raw_focus):
        raise ProtocolRequestError("focus values must be strings.", "focus")

    unknown = sorted(set(raw_focus) - _FOCUS_VALUES)
    if unknown:
        raise ProtocolRequestError(f"Unknown focus value: {unknown[0]}", "focus")

    if len(set(raw_focus)) != len(raw_focus):
        raise ProtocolRequestError("focus values must not be duplicated.", "focus")

    focus_set = set(raw_focus)
    if "all" in focus_set and len(focus_set) > 1:
        raise ProtocolRequestError("focus 'all' cannot be combined with other values.", "focus")

    if "neighbors" in focus_set and "changed" not in focus_set:
        raise ProtocolRequestError("focus 'neighbors' requires 'changed'.", "focus")

    if "all" in focus_set:
        return ["all"]

    ordered = ["changed"] if "changed" in focus_set else []
    if "neighbors" in focus_set:
        ordered.append("neighbors")
    return ordered


def _normalise_protocol_filters(raw_filters: object) -> dict:
    if raw_filters is None:
        return {}
    if not isinstance(raw_filters, dict):
        raise ProtocolRequestError("filters must be a JSON object.", "filters")

    unknown = sorted(set(raw_filters) - _FILTER_KEYS)
    if unknown:
        raise ProtocolRequestError(f"Unknown filter field: {unknown[0]}", f"filters.{unknown[0]}")

    filters: dict[str, str] = {}
    for key in ("language", "module"):
        if key not in raw_filters:
            continue
        value = raw_filters[key]
        if not isinstance(value, str) or not value:
            raise ProtocolRequestError(f"filters.{key} must be a non-empty string.", f"filters.{key}")
        filters[key] = value
    return filters


def _protocol_error_payload(error: ProtocolRequestError) -> dict:
    payload = {
        "protocol": PROTOCOL_VERSION,
        "ok": False,
        "error": {
            "code": "invalid_request",
            "message": str(error),
        },
    }
    if error.field:
        payload["error"]["field"] = error.field
    return payload


def _emit_protocol_error(error: ProtocolRequestError) -> None:
    print(json.dumps(_protocol_error_payload(error), indent=2))
    raise SystemExit(1)


def _apply_protocol_filters(inventory: dict, filters: dict) -> dict:
    """Filter inventory before prioritisation and budgeting."""
    if not filters:
        return inventory

    result: dict = {}
    for filepath, data in inventory.items():
        if "language" in filters and data.get("language") != filters["language"]:
            continue
        if "module" in filters and not _matches_module_filter(filepath, filters["module"]):
            continue
        result[filepath] = data
    return result


def _matches_module_filter(filepath: str, pattern: str) -> bool:
    posix_path = filepath.replace("\\", "/")
    path_target = PurePosixPath(posix_path).with_suffix("").as_posix()
    module_target = _filepath_to_module(posix_path)
    module_pattern = pattern.replace("/", ".")

    return (
        fnmatch(path_target, pattern)
        or (module_target is not None and fnmatch(module_target, pattern))
        or (module_target is not None and fnmatch(module_target, module_pattern))
    )


def _build_context(
    src_dir: str,
    budget: int,
    fmt: str,
    focus_values: list[str],
    filters: dict | None = None,
    *,
    emit_warnings: bool = True,
    allow_external_src: bool = False,
    read_only: bool = False,
) -> tuple[dict, list[str]]:
    """Build a context payload and return ``(payload, warnings)``."""
    src_root = validate_source_root(
        src_dir, "--src-dir", allow_external=allow_external_src,
    )

    inventory = get_inventory(str(src_root), deep=True)
    inventory = _apply_protocol_filters(inventory, filters or {})
    warnings: list[str] = []

    if not inventory:
        return {"budget": budget, "used": 0, "files": {}}, warnings

    changed: list[str] | None = None
    focus_mode = "all" if "all" in focus_values else "changed"
    include_neighbors = "neighbors" in focus_values

    if focus_mode == "changed":
        changed = _git_changed_files(str(src_root))
        if changed is None:
            warnings.append("Could not get changed files from git. Treating all files as high priority.")
            focus_mode = "all"
        elif not changed:
            warnings.append("No files changed in the last commit. Treating all files as high priority.")
            focus_mode = "all"
        else:
            changed = _normalise_changed_paths(changed, inventory)

    if emit_warnings:
        for warning in warnings:
            print(f"Warning: {warning}", file=sys.stderr, flush=True)

    import_graph = _build_import_graph(inventory)
    classification = _classify_files(
        list(inventory.keys()),
        changed,
        import_graph,
        focus_mode,
        include_neighbors=include_neighbors,
    )

    return _build_context_payload(inventory, classification, budget), warnings


def _protocol_success_payload(request: dict, payload: dict, warnings: list[str]) -> dict:
    response = {
        "protocol": PROTOCOL_VERSION,
        "ok": True,
        "budget_tokens": request["budget_tokens"],
        "used_tokens": payload["used"],
        "format": request["format"],
        "focus": request["focus"],
        "filters": request["filters"],
    }
    if warnings:
        response["warnings"] = warnings

    if request["format"] == "markdown":
        response["content"] = _render_markdown(payload)
    else:
        response["files"] = payload["files"]
    return response


def _run_protocol(args) -> None:
    output_path: str | None = getattr(args, "output", None)
    try:
        request = _read_protocol_request(getattr(args, "request"))
        payload, warnings = _build_context(
            getattr(args, "src_dir", "."),
            request["budget_tokens"],
            request["format"],
            request["focus"],
            request["filters"],
            emit_warnings=False,
            allow_external_src=getattr(args, "allow_external_src", False),
            read_only=getattr(args, "read_only", False),
        )
    except ProtocolRequestError as exc:
        _emit_protocol_error(exc)

    rendered = json.dumps(_protocol_success_payload(request, payload, warnings), indent=2)
    if output_path:
        write_text_output(output_path, rendered + "\n")
        print(f"Context output written to: {output_path}", file=sys.stderr)
    else:
        print(rendered)


# ── CLI entry point ───────────────────────────────────────────────────


def run(args) -> None:
    if getattr(args, "request", None):
        _run_protocol(args)
        return

    src_dir: str = getattr(args, "src_dir", ".")
    budget: int | None = getattr(args, "budget", None)
    fmt: str = getattr(args, "format", "json")
    focus: str = getattr(args, "focus", "changed")
    output_path: str | None = getattr(args, "output", None)
    allow_external_src: bool = getattr(args, "allow_external_src", False)
    read_only: bool = getattr(args, "read_only", False)

    if budget is None:
        print("Error: --budget is required unless --request is used.", file=sys.stderr)
        raise SystemExit(2)
    if budget < 1:
        print("Error: --budget must be greater than zero.", file=sys.stderr)
        raise SystemExit(2)

    focus_values = ["all"] if focus == "all" else ["changed", "neighbors"]
    try:
        payload, _warnings = _build_context(
            src_dir,
            budget,
            fmt,
            focus_values,
            emit_warnings=True,
            allow_external_src=allow_external_src,
            read_only=read_only,
        )
    except ProtocolRequestError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if not payload["files"]:
        rendered = "{}" if fmt == "json" else "No source files found."
        if output_path:
            write_text_output(output_path, rendered + "\n")
            print(f"Context output written to: {output_path}", file=sys.stderr)
        else:
            print(rendered)
        return

    if fmt == "markdown":
        rendered = _render_markdown(payload)
    else:
        rendered = json.dumps(payload, indent=2)
    if output_path:
        write_text_output(output_path, rendered + "\n")
        print(f"Context output written to: {output_path}", file=sys.stderr)
    else:
        print(rendered)


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
