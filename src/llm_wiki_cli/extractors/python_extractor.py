"""Python AST extractor for llm-wiki-cli."""

from __future__ import annotations

import ast
from pathlib import Path

from ..config import EXCLUDED_DIRS


# ── AST helper utilities ──────────────────────────────────────────────


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


# ── AST visitor ───────────────────────────────────────────────────────


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


# ── Core scan logic ──────────────────────────────────────────────────


def _scan_python_files(
    src_dir: str,
    deep: bool = False,
    only_files: list[str] | None = None,
) -> dict:
    """Scan Python files under *src_dir* and return a raw inventory dict.

    The returned dict maps absolute filepath strings to file entry dicts.
    The ``"language"`` key is intentionally absent here — callers (e.g.
    :class:`PythonExtractor`) are responsible for stamping it.
    """
    src_path = Path(src_dir)
    inventory = {}

    if only_files is not None:
        # Resolve each relative path against src_dir
        py_files = []
        for f in only_files:
            p = src_path / f
            if p.suffix == ".py" and p.exists():
                py_files.append(p)
    else:
        py_files = list(src_path.rglob("*.py"))

    for py_file in py_files:
        if EXCLUDED_DIRS & set(py_file.parts):
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


# ── Public extractor class ────────────────────────────────────────────


class PythonExtractor:
    """Extractor for Python source files using the built-in :mod:`ast` module.

    Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.
    """

    def extract(
        self,
        src_dir: str,
        only_files: list[str] | None = None,
        deep: bool = False,
    ) -> dict:
        """Scan *src_dir* for Python files and return an inventory dict.

        Each file entry includes ``"language": "python"``.
        """
        inventory = _scan_python_files(src_dir, deep=deep, only_files=only_files)
        for entry in inventory.values():
            entry["language"] = "python"
        return inventory
