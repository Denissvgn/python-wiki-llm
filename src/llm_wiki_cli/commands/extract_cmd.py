from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ..config import EXTRACTOR_REGISTRY, validate_path
from ..extractors.common import LANGUAGE_EXTENSIONS
from ..services.inventory_cache import (
    InventoryCache,
    InventoryCacheOptions,
    InventoryCacheStats,
    build_inventory_cache_key,
    hash_source_file,
    is_valid_cache_entry,
    make_cache_entry,
)
from ..services.imports import module_path_candidates
from ..services.packages import discover_packages, stamp_inventory_packages
from ..services.plugins import get_extractor_registry
from ..services.source_snapshot import SourceSnapshot, build_source_snapshot

# Re-export ComponentVisitor so existing callers that import it from here
# continue to work without modification.
from ..extractors.python_extractor import ComponentVisitor  # noqa: F401


# ── Extractor loader ─────────────────────────────────────────────────


@lru_cache(maxsize=None)
def _load_extractor(entry_point: str):
    """Instantiate an extractor from a ``"module.path:ClassName"`` string."""
    module_path, class_name = entry_point.rsplit(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()


@dataclass(frozen=True)
class ExtractorStatus:
    language: str
    state: str  # ok | skipped | failed
    files_found: int
    message: str = ""


@dataclass(frozen=True)
class InventoryResult:
    inventory: dict
    statuses: dict[str, ExtractorStatus]
    cache_stats: InventoryCacheStats | None = None

    @property
    def failed(self) -> list[ExtractorStatus]:
        return [s for s in self.statuses.values() if s.state == "failed"]


def print_inventory_failures(result: InventoryResult, *, file=None) -> None:
    """Print extractor failures in a consistent form."""
    stream = file or sys.stderr
    for status in result.failed:
        detail = f": {status.message}" if status.message else ""
        print(f"Error: {status.language} extraction failed{detail}", file=stream)


# ── Backward-compatible public API ───────────────────────────────────


def get_inventory_result(
    src_dir,
    deep=False,
    only_files=None,
    include_empty=False,
    source_snapshot: SourceSnapshot | None = None,
    cache_options: InventoryCacheOptions | None = None,
) -> InventoryResult:
    """Scan source files across all registered languages and return inventory.

    Runs every built-in and installed extractor and merges the
    results into a single dict keyed by file path.

    If deep=True, returns enriched data (docstrings, attributes, methods, imports).
    If deep=False, returns the slim format for backward compatibility.
    If only_files is given, restrict to those relative paths.
    If include_empty=True, include all .py files even without extractable components.

    Each entry is stamped with a ``"package"`` key (package name or
    ``None``) derived from ``pyproject.toml`` / ``setup.py`` markers.
    """
    source_snapshot = source_snapshot or build_source_snapshot(src_dir, only_files=only_files)
    registry = get_extractor_registry()
    cache = InventoryCache(src_dir, cache_options) if cache_options is not None else None
    cache_files: dict[str, dict] = {}
    updated_cache_files: dict[str, dict] = {}
    cache_key: dict | None = None

    source_file_by_path = {
        source_file.rel_path: source_file
        for source_files in source_snapshot.files_by_language.values()
        for source_file in source_files
    }
    current_source_paths = set(source_file_by_path)
    source_hashes: dict[str, str] = {}

    if cache is not None and cache.enabled and only_files is None:
        cache_key = build_inventory_cache_key(
            src_dir,
            source_snapshot,
            deep=deep,
            include_empty=include_empty,
            extractor_registry=registry,
        )
        cache_files = cache.load(cache_key)
        cache.stats.deleted = len(set(cache_files) - current_source_paths)
        for rel_path, source_file in source_file_by_path.items():
            file_hash = hash_source_file(source_file)
            if file_hash is not None:
                source_hashes[rel_path] = file_hash

    inventory: dict = {}
    statuses: dict[str, ExtractorStatus] = {}
    for language, entry_point in registry.items():
        extensions = LANGUAGE_EXTENSIONS.get(language)
        source_files: list[str] | None = None
        if extensions is not None:
            source_files = source_snapshot.language_paths(language)
            if not source_files:
                statuses[language] = ExtractorStatus(language, "skipped", 0)
                continue

        files_found = len(source_files or [])
        if extensions is None and only_files:
            files_found = len(only_files)

        if extensions is not None and not source_files:
            statuses[language] = ExtractorStatus(language, "skipped", 0)
            continue

        is_builtin = extensions is not None and entry_point == EXTRACTOR_REGISTRY.get(language)
        fresh_source_files = list(source_files or [])
        if is_builtin and cache is not None and cache.enabled and cache_key is not None:
            fresh_source_files = []
            for rel_path in source_files or []:
                source_file = source_file_by_path[rel_path]
                file_hash = source_hashes.get(rel_path)
                cached_entry = cache_files.get(rel_path)
                if file_hash is None:
                    cache.stats.misses += 1
                    fresh_source_files.append(rel_path)
                    continue
                if cached_entry is None:
                    cache.stats.misses += 1
                    fresh_source_files.append(rel_path)
                    continue
                if is_valid_cache_entry(cached_entry, source_file, file_hash):
                    cache.stats.hits += 1
                    raw_inventory = deepcopy(cached_entry.get("inventory", {}))
                    if raw_inventory:
                        inventory[rel_path] = raw_inventory
                    updated_cache_files[rel_path] = make_cache_entry(
                        source_file,
                        file_hash,
                        deepcopy(cached_entry.get("inventory", {})),
                    )
                    continue
                cached_hash = cached_entry.get("hash") if isinstance(cached_entry, dict) else None
                if cached_hash != file_hash:
                    cache.stats.changed += 1
                else:
                    cache.stats.stale += 1
                fresh_source_files.append(rel_path)

            if not fresh_source_files:
                statuses[language] = ExtractorStatus(language, "ok", files_found)
                continue

        extractor = _load_extractor(entry_point)
        # Reset cached extractor state from any previous invocation.
        if hasattr(extractor, "last_error"):
            extractor.last_error = None
        kwargs = {"src_dir": src_dir, "only_files": only_files, "deep": deep}
        if is_builtin:
            kwargs["source_files"] = fresh_source_files
            if language in {"go", "rust"}:
                kwargs["helper_cache_dir"] = (
                    cache_options.cache_dir if cache_options is not None else None
                )
        if language == "python":
            kwargs["include_empty"] = include_empty
        try:
            extracted = extractor.extract(**kwargs)
        except Exception as exc:
            statuses[language] = ExtractorStatus(language, "failed", files_found, str(exc))
            continue
        error = getattr(extractor, "last_error", None)
        if error:
            statuses[language] = ExtractorStatus(language, "failed", files_found, str(error))
            continue
        inventory.update(extracted)
        if is_builtin and cache is not None and cache.enabled and cache_key is not None:
            cache.stats.fresh_extracted += len(fresh_source_files)
            for rel_path in fresh_source_files:
                source_file = source_file_by_path[rel_path]
                file_hash = source_hashes.get(rel_path)
                if file_hash is None:
                    continue
                raw_entry = deepcopy(extracted.get(rel_path, {}))
                if raw_entry:
                    raw_entry.pop("package", None)
                updated_cache_files[rel_path] = make_cache_entry(source_file, file_hash, raw_entry)
        if extensions is None:
            files_found = len(extracted)
        statuses[language] = ExtractorStatus(language, "ok", files_found)

    # Stamp package ownership
    packages = discover_packages(src_dir, source_snapshot=source_snapshot)
    stamp_inventory_packages(inventory, packages)
    if cache is not None and cache.enabled:
        cache.finalize_lookup_status()
        if cache_key is not None and not any(status.state == "failed" for status in statuses.values()):
            cache.save(cache_key, updated_cache_files)

    return InventoryResult(
        inventory=inventory,
        statuses=statuses,
        cache_stats=cache.stats if cache is not None else None,
    )


def get_inventory(src_dir, deep=False, only_files=None, include_empty=False):
    """Backward-compatible inventory API returning only the inventory dict."""
    return get_inventory_result(
        src_dir, deep=deep, only_files=only_files, include_empty=include_empty,
    ).inventory


def ensure_complete_inventory(result: InventoryResult) -> bool:
    """Return True when all extractors that had matching source files succeeded."""
    return not result.failed


def infer_language_from_path(filepath: str) -> str | None:
    suffix = Path(filepath).suffix
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if suffix in extensions:
            return language
    return None


def languages_with_source(src_dir: str, only_files: list[str] | None = None) -> set[str]:
    snapshot = build_source_snapshot(src_dir, only_files=only_files)
    return {
        language for language, source_files in snapshot.files_by_language.items()
        if source_files
    }


def _inventory_or_exit(src_dir: str, *, deep: bool = False, only_files=None, include_empty: bool = False) -> dict:
    result = get_inventory_result(src_dir, deep=deep, only_files=only_files, include_empty=include_empty)
    if result.failed:
        print_inventory_failures(result)
        sys.exit(1)
    return result.inventory


def _git_changed_files(src_dir: str) -> list[str] | None:
    """Return list of files changed in the last commit, relative to *src_dir*.

    Returns None if git is unavailable or there are no commits.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1..HEAD"],
            capture_output=True, text=True, check=True, timeout=15,
            cwd=src_dir,
        )
        return [line for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _summarize_inventory(inventory: dict) -> dict:
    """Produce a compact one-line-per-symbol summary from a shallow inventory."""
    summary: dict[str, dict] = {}
    for fp, data in inventory.items():
        entry: dict[str, list] = {}
        cls_names = [c["name"] for c in data.get("classes", [])]
        fn_names = [f["name"] for f in data.get("functions", [])]
        if cls_names:
            entry["classes"] = cls_names
        if fn_names:
            entry["functions"] = fn_names
        if entry:
            summary[fp] = entry
    return summary


def run(args):
    src_dir: str = getattr(args, "src_dir", ".")
    validate_path(src_dir, "--src-dir")
    changed: bool = getattr(args, "changed", False)
    summary: bool = getattr(args, "summary", False)
    deep: bool = getattr(args, "deep", False)
    paths: list[str] | None = getattr(args, "paths", None)
    package_filter: str | None = getattr(args, "package", None)
    include_empty: bool = getattr(args, "include_empty", False)

    only_files = None

    if changed and paths:
        print("Error: --changed and --paths are mutually exclusive.", file=sys.stderr)
        sys.exit(2)

    if changed:
        only_files = _git_changed_files(src_dir)
        if only_files is None:
            print("Warning: Could not get changed files from git. Falling back to full scan.", file=sys.stderr)
        elif not only_files:
            print("No files changed in the last commit.", file=sys.stderr)
            return
        else:
            print(f"Extracting {len(only_files)} changed file(s)...", file=sys.stderr)
    elif paths:
        only_files = paths
        print(f"Extracting {len(only_files)} specified path(s)...", file=sys.stderr)
    else:
        print(f"Extracting inventory from {src_dir}...", file=sys.stderr)

    source_snapshot = build_source_snapshot(src_dir, only_files=only_files)
    result = get_inventory_result(
        src_dir,
        deep=deep,
        only_files=only_files,
        include_empty=include_empty,
        source_snapshot=source_snapshot,
    )
    if result.failed:
        print_inventory_failures(result)
        sys.exit(1)
    inventory = result.inventory

    if package_filter:
        inventory = {
            fp: data for fp, data in inventory.items()
            if data.get("package") == package_filter
        }
        if not inventory:
            print(f"No files found for package '{package_filter}'.", file=sys.stderr)
            sys.exit(1)

    if summary:
        inventory = _summarize_inventory(inventory)

    docker_inv = get_docker_inventory(src_dir, source_snapshot=source_snapshot)

    output: dict = {"inventory": inventory}
    if docker_inv:
        output["docker"] = docker_inv

    print(json.dumps(output, indent=2))
    print(f"Extracted {len(inventory)} files with tracked components.", file=sys.stderr)
    if docker_inv:
        print(f"Docker inventory: {len(docker_inv)} file(s).", file=sys.stderr)
    else:
        print("No Docker/Compose files found.", file=sys.stderr)


# ── Call-graph extraction for workflow detection ──────────────────────

def _module_name(filepath: str) -> str:
    return Path(filepath).stem


def get_call_graph(inventory: dict) -> dict:
    """Build cross-module call chains from a deep inventory.

    Detects functions that import and reference symbols from 3+ other
    project-internal modules — these are workflow candidates.

    Returns a dict of workflow_name -> {entry, chain, modules_touched}.
    """
    # Map of symbol name -> defining source files.
    symbol_to_files: dict[str, set[str]] = {}
    for fp, data in inventory.items():
        for cls in data.get("classes", []):
            symbol_to_files.setdefault(cls["name"], set()).add(fp)
        for fn in data.get("functions", []):
            symbol_to_files.setdefault(fn["name"], set()).add(fp)

    workflows: dict[str, dict] = {}

    # Determine which paths are test files — skip them for workflow detection
    _TEST_STEMS = {"conftest"}
    _TEST_DIRS = {"tests", "test", "__tests__"}

    for fp, data in inventory.items():
        fp_path = Path(fp)
        # Skip test files: file stem starts with 'test_' or lives under a tests dir
        if fp_path.stem.startswith("test_") or fp_path.stem in _TEST_STEMS:
            continue
        if _TEST_DIRS & set(fp_path.parts):
            continue

        mod = _module_name(fp)
        imports = data.get("imports", [])

        # Resolve visible imported names to exact internal source files.
        imported_symbols: dict[str, tuple[str, str]] = {}  # visible_name -> (source_path, source_symbol)
        for imp in imports:
            source_name = imp["name"]
            visible_name = imp.get("alias") or source_name
            candidates = set(symbol_to_files.get(source_name, set()))
            module_candidates = module_path_candidates(
                imp.get("module", ""), fp, inventory
            )

            if candidates and module_candidates:
                candidates &= module_candidates
            elif not candidates and module_candidates:
                candidates = set(module_candidates)

            candidates.discard(fp)
            if len(candidates) == 1:
                imported_symbols[visible_name] = (next(iter(candidates)), source_name)

        if not imported_symbols:
            continue

        # For each function in this module, find which imported symbols it references
        all_functions = list(data.get("functions", []))
        for cls in data.get("classes", []):
            for method in cls.get("methods", []):
                all_functions.append(method)

        for fn in all_functions:
            touched_module_paths: set[str] = set()
            chain: list[str] = []

            # Check params, return types, decorators for references to imported symbols
            for visible_name, (src_path, source_name) in imported_symbols.items():
                referenced = False
                for p in fn.get("params", []):
                    if visible_name in p.get("type", ""):
                        referenced = True
                if visible_name in fn.get("return_type", ""):
                    referenced = True
                for dec in fn.get("decorators", []):
                    if visible_name in dec:
                        referenced = True
                # Check docstring for symbol mentions
                if visible_name in fn.get("docstring", ""):
                    referenced = True

                if referenced:
                    touched_module_paths.add(src_path)
                    chain.append(f"{_module_name(src_path)}.{source_name}")

            # Workflow threshold: function touches 3+ other internal modules
            if len(touched_module_paths) >= 3:
                fn_name = fn["name"]
                # Clean up workflow name
                wf_name = fn_name.lstrip("_")
                if wf_name == "run":
                    wf_name = f"{mod}_flow"

                all_touched_paths = touched_module_paths | {fp}
                workflows[wf_name] = {
                    "entry": f"{mod}.{fn_name}",
                    "entry_module": mod,
                    "entry_module_path": fp,
                    "chain": chain,
                    "modules_touched": sorted({_module_name(path) for path in all_touched_paths}),
                    "modules_touched_paths": sorted(all_touched_paths),
                    "docstring": fn.get("docstring", ""),
                }

    return workflows


# ── Docker / Compose extraction ──────────────────────────────────────

def _parse_dockerfile(text: str) -> dict:
    """Parse a Dockerfile into a structured dict (line-based, no external deps)."""
    stages: list[dict] = []
    current_stage: str | None = None
    ports: list[str] = []
    env_vars: list[dict] = []
    volumes: list[str] = []
    copies: list[dict] = []
    build_args: list[dict] = []
    labels: dict[str, str] = {}
    entrypoint: str = ""
    cmd: str = ""
    workdir: str = ""
    healthcheck: str = ""

    # Join continuation lines (trailing backslash)
    logical_lines: list[str] = []
    buf = ""
    for raw in text.splitlines():
        stripped = raw.rstrip()
        if stripped.endswith("\\"):
            buf += stripped[:-1] + " "
        else:
            buf += stripped
            logical_lines.append(buf)
            buf = ""
    if buf:
        logical_lines.append(buf)

    for line in logical_lines:
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue

        upper = trimmed.split()[0].upper() if trimmed.split() else ""

        if upper == "FROM":
            parts = trimmed.split()
            image = parts[1] if len(parts) >= 2 else "unknown"
            alias = ""
            if len(parts) >= 4 and parts[2].upper() == "AS":
                alias = parts[3]
            stage = {"image": image, "alias": alias}
            stages.append(stage)
            current_stage = alias or image

        elif upper == "EXPOSE":
            for token in trimmed.split()[1:]:
                ports.append(token)

        elif upper == "ENV":
            rest = trimmed[4:].strip()
            if "=" in rest:
                for pair in re.findall(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)', rest):
                    env_vars.append({"name": pair[0], "default": pair[1].strip('"')})
            else:
                parts = rest.split(None, 1)
                if len(parts) == 2:
                    env_vars.append({"name": parts[0], "default": parts[1]})
                elif parts:
                    env_vars.append({"name": parts[0], "default": ""})

        elif upper == "VOLUME":
            rest = trimmed[7:].strip()
            if rest.startswith("["):
                for v in re.findall(r'"([^"]+)"', rest):
                    volumes.append(v)
            else:
                volumes.extend(rest.split())

        elif upper in ("COPY", "ADD"):
            parts = trimmed.split()
            flags = [p for p in parts[1:] if p.startswith("--")]
            non_flag = [p for p in parts[1:] if not p.startswith("--")]
            src = " ".join(non_flag[:-1]) if len(non_flag) >= 2 else ""
            dest = non_flag[-1] if non_flag else ""
            from_stage = ""
            for f in flags:
                if f.startswith("--from="):
                    from_stage = f.split("=", 1)[1]
            copies.append({"src": src, "dest": dest, "from_stage": from_stage, "instruction": upper})

        elif upper == "WORKDIR":
            workdir = trimmed.split(None, 1)[1] if len(trimmed.split()) > 1 else ""

        elif upper == "ARG":
            rest = trimmed[4:].strip()
            if "=" in rest:
                name, default = rest.split("=", 1)
                build_args.append({"name": name.strip(), "default": default.strip()})
            else:
                build_args.append({"name": rest, "default": ""})

        elif upper == "LABEL":
            for pair in re.findall(r'(\S+)=("(?:[^"\\]|\\.)*"|\S+)', trimmed[6:]):
                labels[pair[0]] = pair[1].strip('"')

        elif upper == "ENTRYPOINT":
            entrypoint = trimmed.split(None, 1)[1] if len(trimmed.split()) > 1 else ""

        elif upper == "CMD":
            cmd = trimmed.split(None, 1)[1] if len(trimmed.split()) > 1 else ""

        elif upper == "HEALTHCHECK":
            rest = trimmed.split(None, 1)[1] if len(trimmed.split()) > 1 else ""
            if rest.upper() != "NONE":
                healthcheck = rest

    return {
        "type": "dockerfile",
        "stages": stages,
        "ports": ports,
        "env_vars": env_vars,
        "volumes": volumes,
        "copies": copies,
        "build_args": build_args,
        "labels": labels,
        "entrypoint": entrypoint,
        "cmd": cmd,
        "workdir": workdir,
        "healthcheck": healthcheck,
    }


def _parse_inline_yaml_list(value: str) -> list[str] | None:
    """Parse an inline YAML list like ``["CMD", "curl", "-f", "http://..."]``.

    Returns a list of strings if the value is an inline list, otherwise None.
    """
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1]
        items: list[str] = []
        for item in re.split(r",\s*", inner):
            item = item.strip().strip('"').strip("'")
            if item:
                items.append(item)
        return items
    return None


def _parse_compose(text: str) -> dict:
    """Parse a docker-compose YAML file using line-based parsing (no PyYAML).

    Handles the most common patterns: top-level keys (services, networks,
    volumes) and nested mappings under each service (environment, build,
    deploy, healthcheck, depends_on) at arbitrary depth.  Complex YAML
    features (anchors, merge keys, multi-line block scalars) are best-effort.
    """
    services: dict[str, dict] = {}
    networks: list[str] = []
    named_volumes: list[str] = []

    current_top: str = ""       # "services" | "networks" | "volumes" | ""
    current_service: str = ""
    # Stack of keys at each nesting depth (relative to service, depth 0 = indent 4)
    key_stack: list[str] = []

    def _strip_yaml_quotes(value: str) -> str:
        """Remove surrounding YAML quotes from a value."""
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            return value[1:-1]
        return value

    def _navigate(path: list[str], create: bool = False):
        """Navigate to the parent for path, returning (parent_dict, final_key).

        When *create* is True, intermediate dicts are created.  If an
        intermediate value is an empty list it is promoted to a dict (the
        initial ``[]`` was a provisional guess — now we know it's a mapping).
        """
        if not current_service or not path:
            return None, None
        target = services[current_service]
        for part in path[:-1]:
            if part not in target:
                if create:
                    target[part] = {}
                else:
                    return None, None
            child = target[part]
            # Promote empty list to dict — we guessed list, but it's a mapping
            if isinstance(child, list) and not child:
                target[part] = {}
                child = target[part]
            if not isinstance(child, dict):
                return None, None
            target = child
        return target, path[-1]

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip())

        # ── top-level key (indent 0) ──
        if indent == 0 and ":" in stripped:
            key = stripped.split(":")[0].strip()
            current_top = key
            current_service = ""
            key_stack = []
            continue

        # ── under "services" ──
        if current_top == "services":
            # service name (indent 2)
            if indent == 2 and ":" in stripped and not stripped.startswith("-"):
                current_service = stripped.split(":")[0].strip()
                services.setdefault(current_service, {})
                key_stack = []
                continue

            if not current_service:
                continue

            # depth relative to service body (indent 4 → depth 0)
            depth = (indent - 4) // 2
            if depth < 0:
                continue

            # Trim key_stack to current depth
            key_stack = key_stack[:depth]

            # ── list item (- ...) ──
            if stripped.startswith("- "):
                item_value = _strip_yaml_quotes(stripped[2:].strip())
                if key_stack:
                    parent, final_key = _navigate(key_stack)
                    if parent is not None and final_key is not None:
                        existing = parent.get(final_key)
                        if isinstance(existing, list):
                            existing.append(item_value)
                continue

            # ── key:value or key: (mapping start) ──
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip()

                key_stack = key_stack[:depth] + [key]
                path = list(key_stack)

                parent, final_key = _navigate(path, create=True)
                if parent is None or final_key is None:
                    continue

                if value:
                    # Check for inline YAML list: [item1, item2, ...]
                    inline = _parse_inline_yaml_list(value)
                    if inline is not None:
                        parent[final_key] = inline
                    else:
                        parent[final_key] = _strip_yaml_quotes(value)
                else:
                    # Start of a sub-block — initialise as empty list.
                    # If nested key:value lines follow, _navigate will
                    # promote it to a dict automatically.
                    if final_key not in parent:
                        parent[final_key] = []
                continue

        # ── under "networks" — collect names at indent 2 ──
        if current_top == "networks":
            if indent == 2 and ":" in stripped:
                networks.append(stripped.split(":")[0].strip())
            continue

        # ── under "volumes" — collect names at indent 2 ──
        if current_top == "volumes":
            if indent == 2 and ":" in stripped:
                named_volumes.append(stripped.split(":")[0].strip())
            continue

    return {
        "type": "compose",
        "services": services,
        "networks": networks,
        "volumes": named_volumes,
    }


def _looks_like_compose(text: str) -> bool:
    """Return True if the file content appears to be a docker-compose file.

    Checks for a ``services:`` top-level key at indent 0 AND at least one
    service containing a compose-specific key (``image``, ``build``,
    ``ports``, ``depends_on``, ``container_name``, ``environment``,
    ``volumes``, ``command``, ``healthcheck``).  This avoids false positives
    from non-compose YAML files that happen to have a ``services:`` key.
    """
    _COMPOSE_SERVICE_KEYS = {
        "image:", "build:", "ports:", "depends_on:", "container_name:",
        "environment:", "volumes:", "command:", "healthcheck:", "restart:",
        "networks:", "deploy:", "profiles:",
    }
    has_services = False
    in_services = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith("services:") or line.startswith("services :"):
            has_services = True
            in_services = True
            continue
        # Another top-level key ends the services block
        if in_services and not line[0].isspace():
            in_services = False
        if in_services:
            for ck in _COMPOSE_SERVICE_KEYS:
                if ck in stripped:
                    return True
    return False


def get_docker_inventory(src_dir: str, *, source_snapshot: SourceSnapshot | None = None) -> dict:
    """Discover and parse Dockerfiles and Compose files in the source tree.

    Uses two strategies:
    1. **Name-based**: glob patterns from config (Dockerfile*, *.dockerfile,
       docker-compose*.yml, compose*.yml) — searched recursively.
    2. **Content-based**: any ``.yml`` / ``.yaml`` file containing a
       ``services:`` top-level key is treated as a Compose file.  This
       catches non-standard names like ``infra.yml`` or ``core.yml`` that
       are common in split-compose layouts.

    Respects .gitignore rules to skip ignored files.

    Returns a dict of relative-path -> parsed data.  Keys always use
    forward slashes regardless of the host OS.
    """
    source_snapshot = source_snapshot or build_source_snapshot(src_dir)
    inventory: dict[str, dict] = {}

    for source_file in source_snapshot.dockerfile_candidates:
        rel = source_file.rel_path
        if rel not in inventory:
            inventory[rel] = _parse_dockerfile(source_file.abs_path.read_text(errors="replace"))

    for source_file in source_snapshot.compose_candidates:
        rel = source_file.rel_path
        if rel not in inventory:
            inventory[rel] = _parse_compose(source_file.abs_path.read_text(errors="replace"))

    for source_file in source_snapshot.yaml_candidates:
        rel = source_file.rel_path
        if rel in inventory:
            continue
        text = source_file.abs_path.read_text(errors="replace")
        if _looks_like_compose(text):
            inventory[rel] = _parse_compose(text)

    return inventory
