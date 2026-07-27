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
from collections.abc import Iterable, Mapping
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .imports import build_module_path_resolver
from .plugins import PluginError, entrypoint_detector_components, load_entry_point

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
_PLUGIN_CATEGORY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")

_DEFAULT_FLOW_DEPTH = 6


@dataclass(frozen=True)
class EntryPointDetectionResult:
    entries: list[dict]
    warnings: list[str]


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


def _constant_dict_items(data: Mapping[str, Any], name: str) -> list[Mapping[str, Any]]:
    for constant in data.get("constants", []):
        if constant.get("name") != name:
            continue
        value = constant.get("value")
        if isinstance(value, Mapping) and value.get("kind") == "dict":
            items = value.get("items")
            if isinstance(items, list):
                return [item for item in items if isinstance(item, Mapping)]
    return []


def _import_targets(data: Mapping[str, Any]) -> dict[str, str]:
    targets: dict[str, str] = {}
    for record in data.get("imports", []):
        if record.get("type") == "from":
            module = str(record.get("module") or "")
            name = str(record.get("name") or "")
            if not name:
                continue
            binding = str(record.get("alias") or name)
            targets[binding] = f"{module}.{name}" if module else name
        elif record.get("type") == "import":
            module = str(record.get("module") or "")
            binding = str(record.get("name") or module)
            if module and binding:
                targets[binding] = module
    return targets


def _module_ref_candidates(ref: str, imports: Mapping[str, str]) -> list[str]:
    candidates = [ref]
    root, _, rest = ref.partition(".")
    target = imports.get(root)
    if target:
        candidates.append(f"{target}.{rest}" if rest else target)
    return list(dict.fromkeys(candidates))


def _resolve_command_module(
    ref: str, filepath: str, data: Mapping[str, Any], resolver
) -> str | None:
    for candidate in _module_ref_candidates(ref, _import_targets(data)):
        matches = resolver.candidates(candidate, filepath)
        if len(matches) == 1:
            return next(iter(matches))
    return None


def _has_run_function(data: Mapping[str, Any]) -> bool:
    return any(fn.get("name") == "run" for fn in data.get("functions", []))


def _dedup_paths(paths: Iterable[str | None]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not path or path in seen:
            continue
        seen.add(path)
        values.append(path)
    return values


def _related_internal_import_modules(
    filepath: str | None, data: Mapping[str, Any] | None, resolver
) -> list[str]:
    if not filepath or data is None:
        return []
    paths: list[str] = []
    for record in data.get("imports", []):
        module = str(record.get("module") or "")
        if not module:
            continue
        matches = sorted(resolver.candidates(module, filepath))
        paths.extend(match for match in matches if match != filepath)
    return _dedup_paths(paths)


def _entry_with_related_modules(entry: dict, related_modules: list[str]) -> dict:
    if related_modules:
        entry["related_modules"] = related_modules
    return entry


def _detect_argparse_dispatch_commands(inventory: dict) -> list[dict]:
    """Detect top-level CLI commands declared in a module dispatch table.

    ``llm-wiki`` command modules are registered as ``_COMMAND_MODULES`` in the
    top-level CLI.  Each dispatch table entry is one user-flow root; nested
    argparse subcommands remain part of that parent command flow.
    """
    resolver = build_module_path_resolver(inventory)
    entries: list[dict] = []
    for filepath, data in inventory.items():
        for item in _constant_dict_items(data, "_COMMAND_MODULES"):
            label = item.get("key")
            value = item.get("value")
            if not isinstance(label, str) or not isinstance(value, Mapping):
                continue
            if value.get("kind") not in {"name", "attribute"}:
                continue
            ref = value.get("value")
            if not isinstance(ref, str) or not ref:
                continue
            command_file = _resolve_command_module(ref, filepath, data, resolver)
            if command_file is None:
                continue
            command_data = inventory.get(command_file)
            if not isinstance(command_data, Mapping) or not _has_run_function(
                command_data
            ):
                continue
            entries.append(_entry(CATEGORY_CLI, command_file, "run", label=label))
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


_NODE_HTTP_MODULES = frozenset({"http", "node:http", "https", "node:https"})
_GO_HTTP_MODULES = frozenset({"net/http"})
_HASKELL_WEB_MODULE_PREFIXES = (
    "Network.Wai",
    "Network.Wai.Handler.Warp",
    "Servant",
)
_GO_HANDLE_FUNC_RE = re.compile(
    r"\bhttp\.HandleFunc\s*\([^,]+,\s*([A-Za-z_][A-Za-z0-9_]*)"
)
_GO_LISTEN_AND_SERVE_RE = re.compile(
    r"\bhttp\.ListenAndServe(?:TLS)?\s*\([^,]+,\s*([A-Za-z_][A-Za-z0-9_]*)"
)
_GO_HTTP_SERVER_RE = re.compile(r"\bhttp\.Server\b")
_HASKELL_SERVE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_']*)\s*=\s*serve\b", re.M)
_HASKELL_WARP_RUN_RE = re.compile(r"\brun\s+\S+\s+([A-Za-z_][A-Za-z0-9_']*)")


def _javascript_has_node_http_signal(data: Mapping[str, Any]) -> bool:
    for record in data.get("imports", []):
        module = str(record.get("module") or "")
        if module in _NODE_HTTP_MODULES:
            return True
    for call in data.get("module_calls", []):
        if call.get("name") == "require" and call.get("target") in {"http", "https"}:
            return True
    return False


def _module_call_args(call: Mapping[str, Any]) -> list[str]:
    args = call.get("args")
    if not isinstance(args, list):
        return []
    return [arg for arg in args if isinstance(arg, str) and arg]


def _javascript_server_symbol(data: Mapping[str, Any], call: Mapping[str, Any]) -> str:
    local = _local_symbols(dict(data))
    for arg in _module_call_args(call):
        if arg in local:
            return arg
    target = call.get("target")
    if isinstance(target, str) and target:
        return target
    return "createServer"


def _detect_javascript_http_servers(inventory: dict) -> list[dict]:
    entries: list[dict] = []
    for filepath, data in inventory.items():
        if not isinstance(data, Mapping) or data.get("language") != "javascript":
            continue
        if not _javascript_has_node_http_signal(data):
            continue
        for call in data.get("module_calls", []):
            if not isinstance(call, Mapping) or call.get("name") != "createServer":
                continue
            symbol = _javascript_server_symbol(data, call)
            entries.append(_entry(CATEGORY_HTTP, filepath, symbol))
    return entries


def _import_modules(data: Mapping[str, Any]) -> set[str]:
    return {
        str(record.get("module") or "")
        for record in data.get("imports", [])
        if isinstance(record, Mapping) and record.get("module")
    }


def _source_text(root: str | Path, filepath: str) -> str:
    path = PurePosixPath(filepath)
    if path.is_absolute() or ".." in path.parts:
        return ""
    root_path = Path(root).resolve()
    candidate = root_path.joinpath(*path.parts).resolve()
    try:
        candidate.relative_to(root_path)
    except ValueError:
        return ""
    try:
        return candidate.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _detect_go_http_servers(inventory: dict, *, root: str | Path) -> list[dict]:
    entries: list[dict] = []
    for filepath, data in inventory.items():
        if not isinstance(data, Mapping) or data.get("language") != "go":
            continue
        if not (_import_modules(data) & _GO_HTTP_MODULES):
            continue
        text = _source_text(root, filepath)
        if not text:
            continue
        local = _local_symbols(dict(data))
        for pattern in (_GO_HANDLE_FUNC_RE, _GO_LISTEN_AND_SERVE_RE):
            for match in pattern.finditer(text):
                symbol = match.group(1)
                if symbol in local:
                    entries.append(_entry(CATEGORY_HTTP, filepath, symbol))
        if _GO_HTTP_SERVER_RE.search(text):
            entries.append(_entry(CATEGORY_HTTP, filepath, "http.Server"))
    return entries


def _has_haskell_web_import(data: Mapping[str, Any]) -> bool:
    modules = _import_modules(data)
    return any(
        module == prefix or module.startswith(f"{prefix}.")
        for module in modules
        for prefix in _HASKELL_WEB_MODULE_PREFIXES
    )


def _haskell_application_symbols(data: Mapping[str, Any], source: str) -> list[str]:
    local = _local_symbols(dict(data))
    symbols: list[str] = []
    for fn in data.get("functions", []):
        if not isinstance(fn, Mapping):
            continue
        name = str(fn.get("name") or "")
        signature = str(fn.get("signature") or "")
        if name in local and "Application" in signature:
            symbols.append(name)
    symbols.extend(match.group(1) for match in _HASKELL_SERVE_RE.finditer(source))
    symbols.extend(match.group(1) for match in _HASKELL_WARP_RUN_RE.finditer(source))
    return [symbol for symbol in dict.fromkeys(symbols) if symbol in local]


def _detect_haskell_web_servers(inventory: dict, *, root: str | Path) -> list[dict]:
    entries: list[dict] = []
    for filepath, data in inventory.items():
        if not isinstance(data, Mapping) or data.get("language") != "haskell":
            continue
        if not _has_haskell_web_import(data):
            continue
        text = _source_text(root, filepath)
        if not text:
            continue
        entries.extend(
            _entry(CATEGORY_HTTP, filepath, symbol)
            for symbol in _haskell_application_symbols(data, text)
        )
    return entries


def _detect_process(inventory: dict, console_scripts: list[dict] | None) -> list[dict]:
    """Process entry points: ``__main__`` guards and console-script targets."""
    entries: list[dict] = []
    resolver = build_module_path_resolver(inventory)
    for filepath, data in inventory.items():
        if not data.get("main_block"):
            continue
        symbol = "main" if "main" in _local_symbols(data) else "__main__"
        related_modules = _related_internal_import_modules(filepath, data, resolver)
        entries.append(
            _entry_with_related_modules(
                _entry(CATEGORY_PROCESS, filepath, symbol, label=Path(filepath).stem),
                related_modules,
            )
        )

    for script in console_scripts or []:
        file = _resolve_module_file(script["module"], resolver)
        data = inventory.get(file) if file is not None else None
        related_modules = _related_internal_import_modules(file, data, resolver)
        entries.append(
            _entry_with_related_modules(
                _entry(CATEGORY_PROCESS, file, script["attr"], label=script["name"]),
                related_modules,
            )
        )
    return entries


def _resolve_module_file(module: str, resolver) -> str | None:
    candidates = resolver.candidates(module, "")
    return next(iter(candidates)) if len(candidates) == 1 else None


def _plugin_warning(component: Mapping[str, Any], message: str) -> str:
    ref = component.get("ref") or component.get("id") or component.get("entry_point")
    return f"Plugin entry-point detector {ref}: {message}"


def _plugin_error(message: str) -> PluginError:
    return PluginError(message)


def _iter_plugin_records(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, (str, bytes)) or isinstance(value, Mapping):
        raise _plugin_error("must return an iterable of entry-point records.")
    if not isinstance(value, Iterable):
        raise _plugin_error("must return an iterable of entry-point records.")
    return value


def _safe_plugin_file(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise _plugin_error("file must be a non-empty relative POSIX path or null.")
    if "\\" in value:
        raise _plugin_error("file must use POSIX '/' separators.")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise _plugin_error("file must stay relative to the source inventory.")
    return path.as_posix()


def _safe_plugin_text(record: Mapping[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise _plugin_error(f"{key} must be a non-empty string.")
    return value


def _normalize_plugin_entry(record: Any) -> dict:
    if not isinstance(record, Mapping):
        raise _plugin_error("record must be an object.")
    category = _safe_plugin_text(record, "category")
    if not _PLUGIN_CATEGORY_RE.match(category):
        raise _plugin_error(f"category must be a safe identifier: {category!r}.")
    symbol = _safe_plugin_text(record, "symbol")
    label = record.get("label", symbol)
    if not isinstance(label, str) or not label:
        raise _plugin_error("label must be a non-empty string when provided.")
    return _entry(category, _safe_plugin_file(record.get("file")), symbol, label)


def _load_plugin_detector(component: Mapping[str, Any], root: str | Path):
    return load_entry_point(str(component["entry_point"]), root=root)


def _roots_equal(left: str | Path, right: str | Path) -> bool:
    return Path(left).resolve() == Path(right).resolve()


def _read_detector_components(
    root: str | Path, *, strict_plugin_errors: bool
) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        return entrypoint_detector_components(root=root), []
    except PluginError as exc:
        if strict_plugin_errors:
            raise
        return [], [f"Plugin entry-point detectors unavailable: {exc}"]


def _detector_components(
    root: str | Path,
    *,
    fallback_root: str | Path | None,
    strict_plugin_errors: bool,
) -> tuple[list[tuple[dict[str, Any], str | Path]], list[str]]:
    components, warnings = _read_detector_components(
        root, strict_plugin_errors=strict_plugin_errors
    )
    if components or fallback_root is None or _roots_equal(root, fallback_root):
        return [(component, root) for component in components], warnings

    fallback_components, fallback_warnings = _read_detector_components(
        fallback_root, strict_plugin_errors=strict_plugin_errors
    )
    return (
        [(component, fallback_root) for component in fallback_components],
        warnings + fallback_warnings,
    )


def _detect_plugin_entries(
    inventory: dict,
    *,
    root: str | Path,
    fallback_root: str | Path | None,
    strict_plugin_errors: bool,
    include_provenance: bool,
) -> EntryPointDetectionResult:
    components, warnings = _detector_components(
        root,
        fallback_root=fallback_root,
        strict_plugin_errors=strict_plugin_errors,
    )
    entries: list[dict] = []
    for component, component_root in components:
        try:
            detector = _load_plugin_detector(component, component_root)
            records = list(_iter_plugin_records(detector(inventory)))
        except Exception as exc:
            if strict_plugin_errors:
                raise
            warnings.append(_plugin_warning(component, f"failed: {exc}"))
            continue
        for index, record in enumerate(records, start=1):
            try:
                entry = _normalize_plugin_entry(record)
                if include_provenance:
                    entry["detector"] = (
                        f"plugin:{component.get('ref', 'unknown')}"
                        f"@{component.get('plugin_version', 'unknown')}"
                    )
                entries.append(entry)
            except Exception as exc:
                if strict_plugin_errors:
                    raise
                warnings.append(
                    _plugin_warning(component, f"invalid record {index}: {exc}")
                )
    return EntryPointDetectionResult(entries, warnings)


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


def _builtin_entry_points(
    inventory: dict, console_scripts: list[dict] | None, *, root: str | Path
) -> list[dict]:
    entries: list[dict] = []
    entries += _detect_argparse_dispatch_commands(inventory)
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
    entries += _detect_javascript_http_servers(inventory)
    entries += _detect_go_http_servers(inventory, root=root)
    entries += _detect_haskell_web_servers(inventory, root=root)
    entries += _detect_process(inventory, console_scripts)

    return entries


def _finalize_entries(entries: list[dict]) -> list[dict]:
    entries = _dedup(entries)
    entries.sort(key=lambda e: (e["category"], e.get("file") or "", e["symbol"]))
    return _assign_ids(entries)


def detect_entry_points(
    inventory: dict,
    *,
    console_scripts: list[dict] | None = None,
    root: str | Path = ".",
    fallback_root: str | Path | None = None,
    include_plugins: bool = True,
    strict_plugin_errors: bool = False,
    include_provenance: bool = False,
) -> EntryPointDetectionResult:
    """Detect user-reachable entry points and non-fatal plugin warnings.

    ``include_provenance`` adds a bounded detector identity for downstream
    evidence artifacts. It defaults off so the public v1 entry-point shape is
    unchanged for existing callers.
    """
    entries = _builtin_entry_points(inventory, console_scripts, root=root)
    if include_provenance:
        for entry in entries:
            entry["detector"] = "builtin"
    warnings: list[str] = []
    if include_plugins:
        plugin_result = _detect_plugin_entries(
            inventory,
            root=root,
            fallback_root=fallback_root,
            strict_plugin_errors=strict_plugin_errors,
            include_provenance=include_provenance,
        )
        entries += plugin_result.entries
        warnings += plugin_result.warnings
    return EntryPointDetectionResult(_finalize_entries(entries), warnings)


def get_entry_points(
    inventory: dict,
    *,
    console_scripts: list[dict] | None = None,
    root: str | Path = ".",
    fallback_root: str | Path | None = None,
    include_plugins: bool = True,
) -> list[dict]:
    """Detect user-reachable entry points from a deep inventory.

    Returns a deterministically ordered list of
    ``{"id", "category", "file", "symbol", "label"}`` records. ``console_scripts``
    are the parsed ``[project.scripts]`` entries (see :func:`read_console_scripts`).
    Plugin detectors can be excluded for untrusted source workspaces.
    """
    return detect_entry_points(
        inventory,
        console_scripts=console_scripts,
        root=root,
        fallback_root=fallback_root,
        include_plugins=include_plugins,
    ).entries


def javascript_flow_limitations(
    inventory: dict, entry_points: list[dict]
) -> list[dict]:
    """Return JavaScript HTTP server files that lack flow entry-point coverage."""
    covered_files = {
        entry.get("file") for entry in entry_points if entry.get("file") is not None
    }
    limitations: list[dict] = []
    for filepath, data in inventory.items():
        if data.get("language") != "javascript" or filepath in covered_files:
            continue
        create_server_calls = [
            call
            for call in data.get("module_calls", [])
            if call.get("name") == "createServer"
        ]
        if not create_server_calls:
            continue
        first_call = create_server_calls[0]
        line = first_call.get("line") or 0
        location = f" at line {line}" if line else ""
        limitations.append(
            {
                "file": filepath,
                "line": line,
                "message": (
                    f"JavaScript HTTP flow detection for createServer{location} "
                    "is still advisory for patterns outside raw "
                    "http.createServer/https.createServer; add an entry-point "
                    "detector plugin to generate flow pages for this file."
                ),
            }
        )
    return limitations


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
    return _dedup_paths(
        step["file"]
        for step in steps
        if step["kind"] in ("entry", "internal") and step["file"]
    )


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
        "related_modules": _dedup_paths(entry.get("related_modules", [])),
        "truncated": state["truncated"],
    }
