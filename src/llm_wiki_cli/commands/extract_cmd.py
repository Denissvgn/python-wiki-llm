import ast
import json
from pathlib import Path


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


def get_inventory(src_dir, deep=False):
    """Scan Python files and return inventory.
    
    If deep=True, returns enriched data (docstrings, attributes, methods, imports).
    If deep=False, returns the slim format for backward compatibility.
    """
    src_path = Path(src_dir)
    inventory = {}

    for py_file in src_path.rglob("*.py"):
        if "venv" in py_file.parts or ".venv" in py_file.parts:
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
    print(f"Extracted {len(inventory)} files with tracked components. (You can redirect this to JSON).")


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

    for fp, data in inventory.items():
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
                # For the entry-point function name heuristic: if it's in the
                # same module as the import, it likely calls it
                if referenced or sym_name in imported_symbols:
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
