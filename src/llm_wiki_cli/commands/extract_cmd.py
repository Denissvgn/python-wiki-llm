from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path

from ..config import COMPOSE_PATTERNS, DOCKERFILE_PATTERNS


def _annotation_to_str(node) -> str:
    """Convert an AST annotation node to a readable string."""
    if node is None:
        return ""
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_annotation_to_str(node.value)}.{node.attr}"
    if isinstance(node, ast.Subscript):
        return f"{_annotation_to_str(node.value)}[{_annotation_to_str(node.slice)}]"
    if isinstance(node, ast.Tuple):
        return ", ".join(_annotation_to_str(e) for e in node.elts)
    if isinstance(node, ast.List):
        return "[" + ", ".join(_annotation_to_str(e) for e in node.elts) + "]"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return f"{_annotation_to_str(node.left)} | {_annotation_to_str(node.right)}"
    return ast.dump(node)


def _default_to_str(node) -> str:
    """Convert a default-value AST node to a readable string."""
    if node is None:
        return ""
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.List):
        return "[" + ", ".join(_default_to_str(e) for e in node.elts) + "]"
    if isinstance(node, ast.Dict):
        return "{...}"
    if isinstance(node, ast.Call):
        func = _annotation_to_str(node.func)
        return f"{func}(...)"
    return "..."


def _extract_decorators(node) -> list[str]:
    """Extract decorator names from a node."""
    decorators = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            decorators.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            decorators.append(_annotation_to_str(dec))
        elif isinstance(dec, ast.Call):
            func_str = _annotation_to_str(dec.func)
            args_parts = []
            for a in dec.args:
                args_parts.append(_annotation_to_str(a))
            for kw in dec.keywords:
                args_parts.append(f"{kw.arg}={_annotation_to_str(kw.value)}")
            decorators.append(f"{func_str}({', '.join(args_parts)})")
    return decorators


def _extract_function_info(node) -> dict:
    """Extract full function/method info from a FunctionDef or AsyncFunctionDef."""
    info = {
        "name": node.name,
        "line": node.lineno,
        "docstring": ast.get_docstring(node) or "",
        "decorators": _extract_decorators(node),
        "is_async": isinstance(node, ast.AsyncFunctionDef),
    }

    # Parameters (skip 'self'/'cls' for methods)
    params = []
    args_node = node.args

    # Pair defaults with args (defaults align to the end of the args list)
    num_args = len(args_node.args)
    num_defaults = len(args_node.defaults)
    default_offset = num_args - num_defaults

    for i, arg in enumerate(args_node.args):
        if arg.arg in ("self", "cls"):
            continue
        param = {
            "name": arg.arg,
            "type": _annotation_to_str(arg.annotation),
        }
        default_idx = i - default_offset
        if default_idx >= 0:
            param["default"] = _default_to_str(args_node.defaults[default_idx])
        params.append(param)

    info["params"] = params
    info["return_type"] = _annotation_to_str(node.returns)

    return info


def _extract_class_attributes(node) -> list[dict]:
    """Extract annotated attributes from a class body (Pydantic fields, dataclass fields, etc.)."""
    attrs = []
    for child in node.body:
        if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            attr = {
                "name": child.target.id,
                "type": _annotation_to_str(child.annotation),
                "default": _default_to_str(child.value) if child.value else "",
            }
            attrs.append(attr)
    return attrs


class ComponentVisitor(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.functions = []  # top-level functions only
        self.imports = []
        self._class_depth = 0

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                "module": alias.name,
                "name": alias.asname or alias.name,
                "type": "import",
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            self.imports.append({
                "module": module,
                "name": alias.name,
                "alias": alias.asname,
                "type": "from",
            })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        bases = [_annotation_to_str(b) for b in node.bases]
        docstring = ast.get_docstring(node) or ""
        decorators = _extract_decorators(node)
        attributes = _extract_class_attributes(node)

        # Extract methods (including private for completeness)
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(_extract_function_info(child))

        self.classes.append({
            "name": node.name,
            "bases": bases,
            "line": node.lineno,
            "docstring": docstring,
            "decorators": decorators,
            "attributes": attributes,
            "methods": methods,
        })
        # Don't generic_visit — we already walked class body for methods/attrs

    def visit_FunctionDef(self, node):
        # Only capture top-level functions (not methods inside classes)
        if self._class_depth == 0 and not node.name.startswith("_"):
            self.functions.append(_extract_function_info(node))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if self._class_depth == 0 and not node.name.startswith("_"):
            self.functions.append(_extract_function_info(node))
        self.generic_visit(node)


_EXCLUDED_DIRS = {
    "venv", ".venv", "env", ".env",
    ".tox", "node_modules", "__pycache__",
    ".eggs", "build", "dist", ".git",
}


def get_inventory(src_dir, deep=False):
    """Scan Python files and return inventory.
    
    If deep=True, returns enriched data (docstrings, attributes, methods, imports).
    If deep=False, returns the slim format for backward compatibility.
    """
    src_path = Path(src_dir)
    inventory = {}

    for py_file in src_path.rglob("*.py"):
        if _EXCLUDED_DIRS & set(py_file.parts):
            continue

        with open(py_file, "r") as f:
            try:
                source = f.read()
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

        visitor = ComponentVisitor()
        visitor.visit(tree)

        if visitor.classes or visitor.functions:
            file_entry = {
                "classes": visitor.classes,
                "functions": visitor.functions,
            }

            if deep:
                file_entry["imports"] = visitor.imports
                file_entry["module_docstring"] = ast.get_docstring(tree) or ""
            else:
                # Slim format: strip rich fields for backward compat
                file_entry["classes"] = [
                    {"name": c["name"], "bases": c["bases"], "line": c["line"]}
                    for c in visitor.classes
                ]
                file_entry["functions"] = [
                    {"name": f["name"], "line": f["line"],
                     **({"async": True} if f.get("is_async") else {})}
                    for f in visitor.functions
                ]

            inventory[str(py_file)] = file_entry

    return inventory


def run(args):
    print(f"Extracting inventory from {args.src_dir}...")
    inventory = get_inventory(args.src_dir)
    print(json.dumps(inventory, indent=2))
    print(f"Extracted {len(inventory)} files with tracked components.")

    docker_inv = get_docker_inventory(args.src_dir)
    if docker_inv:
        print(f"\nDocker inventory ({len(docker_inv)} file(s)):")
        print(json.dumps(docker_inv, indent=2))
    else:
        print("\nNo Docker/Compose files found.")


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

    Returns a dict of relative-path -> parsed data.  Keys always use
    forward slashes regardless of the host OS.
    """
    src_path = Path(src_dir)
    inventory: dict[str, dict] = {}

    def _rel(path: Path) -> str:
        """Return a forward-slash relative path (consistent across OSes)."""
        return str(path.relative_to(src_path)).replace(os.sep, "/")

    # Suffixes that should never be treated as Dockerfiles
    _DOC_SUFFIXES = {".md", ".txt", ".rst", ".html", ".json"}

    # Discover Dockerfiles (recursive)
    for pattern in DOCKERFILE_PATTERNS:
        for match in src_path.rglob(pattern):
            if match.suffix.lower() in _DOC_SUFFIXES:
                continue
            if match.is_file() and _EXCLUDED_DIRS.isdisjoint(match.relative_to(src_path).parts):
                rel = _rel(match)
                if rel not in inventory:
                    inventory[rel] = _parse_dockerfile(match.read_text(errors="replace"))

    # Discover Compose files — name-based (recursive)
    for pattern in COMPOSE_PATTERNS:
        for match in src_path.rglob(pattern):
            if match.is_file() and _EXCLUDED_DIRS.isdisjoint(match.relative_to(src_path).parts):
                rel = _rel(match)
                if rel not in inventory:
                    inventory[rel] = _parse_compose(match.read_text(errors="replace"))

    # Discover Compose files — content-based (recursive, YAML files only)
    for ext in ("*.yml", "*.yaml"):
        for match in src_path.rglob(ext):
            if not match.is_file():
                continue
            if not _EXCLUDED_DIRS.isdisjoint(match.relative_to(src_path).parts):
                continue
            rel = _rel(match)
            if rel in inventory:
                continue
            text = match.read_text(errors="replace")
            if _looks_like_compose(text):
                inventory[rel] = _parse_compose(text)

    return inventory
