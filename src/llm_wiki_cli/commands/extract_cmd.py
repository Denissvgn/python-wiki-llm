from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ..config import COMPOSE_PATTERNS, DOCKERFILE_PATTERNS, EXCLUDED_DIRS, EXTRACTOR_REGISTRY
from ..extractors.common import LANGUAGE_EXTENSIONS, discover_source_files
from ..services.packages import discover_packages, stamp_inventory_packages

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


def get_inventory_result(src_dir, deep=False, only_files=None, include_empty=False) -> InventoryResult:
    """Scan source files across all registered languages and return inventory.

    Runs every extractor in :data:`EXTRACTOR_REGISTRY` and merges the
    results into a single dict keyed by file path.

    If deep=True, returns enriched data (docstrings, attributes, methods, imports).
    If deep=False, returns the slim format for backward compatibility.
    If only_files is given, restrict to those relative paths.
    If include_empty=True, include all .py files even without extractable components.

    Each entry is stamped with a ``"package"`` key (package name or
    ``None``) derived from ``pyproject.toml`` / ``setup.py`` markers.
    """
    inventory: dict = {}
    statuses: dict[str, ExtractorStatus] = {}
    for language, entry_point in EXTRACTOR_REGISTRY.items():
        source_files = discover_source_files(
            src_dir,
            LANGUAGE_EXTENSIONS.get(language, ()),
            only_files=only_files,
            language=language,
        )
        if not source_files:
            statuses[language] = ExtractorStatus(language, "skipped", 0)
            continue

        extractor = _load_extractor(entry_point)
        # Reset cached extractor state from any previous invocation.
        if hasattr(extractor, "last_error"):
            extractor.last_error = None
        kwargs = {"src_dir": src_dir, "only_files": only_files, "deep": deep}
        if language == "python":
            kwargs["include_empty"] = include_empty
        try:
            extracted = extractor.extract(**kwargs)
        except Exception as exc:
            statuses[language] = ExtractorStatus(language, "failed", len(source_files), str(exc))
            continue
        error = getattr(extractor, "last_error", None)
        if error:
            statuses[language] = ExtractorStatus(language, "failed", len(source_files), str(error))
            continue
        inventory.update(extracted)
        statuses[language] = ExtractorStatus(language, "ok", len(source_files))

    # Stamp package ownership
    packages = discover_packages(src_dir)
    stamp_inventory_packages(inventory, packages)

    return InventoryResult(inventory=inventory, statuses=statuses)


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
    languages: set[str] = set()
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if discover_source_files(src_dir, extensions, only_files=only_files, language=language):
            languages.add(language)
    return languages


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

    result = get_inventory_result(src_dir, deep=deep, only_files=only_files,
                                  include_empty=include_empty)
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

    docker_inv = get_docker_inventory(src_dir)

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
    # Map of known module stems from inventory
    known_modules = {_module_name(fp) for fp in inventory}
    # Map of symbol name -> defining module stem
    symbol_to_module: dict[str, str] = {}
    for fp, data in inventory.items():
        mod = _module_name(fp)
        for cls in data.get("classes", []):
            symbol_to_module[cls["name"]] = mod
        for fn in data.get("functions", []):
            symbol_to_module[fn["name"]] = mod

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

        # Resolve which internal modules this file imports from
        imported_symbols: dict[str, str] = {}  # symbol_name -> source_module
        for imp in imports:
            # Check if the imported name maps to a known symbol
            name = imp["name"]
            if name in symbol_to_module and symbol_to_module[name] != mod:
                imported_symbols[name] = symbol_to_module[name]
            # Also check if the import's module path contains a known module
            imp_mod = imp.get("module", "")
            imp_mod_stem = imp_mod.rsplit(".", 1)[-1] if imp_mod else ""
            if imp_mod_stem in known_modules and imp_mod_stem != mod:
                imported_symbols[name] = imp_mod_stem

        if not imported_symbols:
            continue

        # For each function in this module, find which imported symbols it references
        all_functions = list(data.get("functions", []))
        for cls in data.get("classes", []):
            for method in cls.get("methods", []):
                all_functions.append(method)

        for fn in all_functions:
            touched_modules: set[str] = set()
            chain: list[str] = []

            # Check params, return types, decorators for references to imported symbols
            for sym_name, src_mod in imported_symbols.items():
                referenced = False
                for p in fn.get("params", []):
                    if sym_name in p.get("type", ""):
                        referenced = True
                if sym_name in fn.get("return_type", ""):
                    referenced = True
                for dec in fn.get("decorators", []):
                    if sym_name in dec:
                        referenced = True
                # Check docstring for symbol mentions
                if sym_name in fn.get("docstring", ""):
                    referenced = True

                if referenced:
                    touched_modules.add(src_mod)
                    chain.append(f"{src_mod}.{sym_name}")

            # Workflow threshold: function touches 3+ other internal modules
            if len(touched_modules) >= 3:
                fn_name = fn["name"]
                # Clean up workflow name
                wf_name = fn_name.lstrip("_")
                if wf_name == "run":
                    wf_name = f"{mod}_flow"

                workflows[wf_name] = {
                    "entry": f"{mod}.{fn_name}",
                    "entry_module": mod,
                    "chain": chain,
                    "modules_touched": sorted(touched_modules | {mod}),
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


def get_docker_inventory(src_dir: str) -> dict:
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
    from ..config import build_gitignore_matcher
    
    src_path = Path(src_dir)
    inventory: dict[str, dict] = {}
    matcher = build_gitignore_matcher(src_path)

    def _rel(path: Path) -> str:
        """Return a forward-slash relative path (consistent across OSes)."""
        return str(path.relative_to(src_path)).replace(os.sep, "/")
    
    def _should_skip(path: Path) -> bool:
        """Check if a path should be skipped (excluded_dirs or gitignore)."""
        rel = path.relative_to(src_path)
        # Check hardcoded exclusions
        if not EXCLUDED_DIRS.isdisjoint(rel.parts):
            return True
        rel_str = str(rel).replace("\\", "/")
        if matcher.is_ignored(rel_str):
            return True
        return False

    # Suffixes that should never be treated as Dockerfiles
    _DOC_SUFFIXES = {".md", ".txt", ".rst", ".html", ".json"}

    # Discover Dockerfiles (recursive)
    for pattern in DOCKERFILE_PATTERNS:
        for match in src_path.rglob(pattern):
            if match.suffix.lower() in _DOC_SUFFIXES:
                continue
            if match.is_file() and not _should_skip(match):
                rel = _rel(match)
                if rel not in inventory:
                    inventory[rel] = _parse_dockerfile(match.read_text(errors="replace"))

    # Discover Compose files — name-based (recursive)
    for pattern in COMPOSE_PATTERNS:
        for match in src_path.rglob(pattern):
            if match.is_file() and not _should_skip(match):
                rel = _rel(match)
                if rel not in inventory:
                    inventory[rel] = _parse_compose(match.read_text(errors="replace"))

    # Discover Compose files — content-based (recursive, YAML files only)
    for ext in ("*.yml", "*.yaml"):
        for match in src_path.rglob(ext):
            if not match.is_file():
                continue
            if _should_skip(match):
                continue
            rel = _rel(match)
            if rel in inventory:
                continue
            text = match.read_text(errors="replace")
            if _looks_like_compose(text):
                inventory[rel] = _parse_compose(text)

    return inventory
