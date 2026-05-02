"""Python AST extractor for llm-wiki-cli."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from ..config import build_gitignore_matcher
from .common import discover_source_files


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
    def __init__(self, deep: bool = False):
        self.classes = []
        self.functions = []  # top-level functions only
        self.imports = []
        self.constants = []  # UPPER_CASE module-level assignments
        self.has_all = False  # whether __all__ is defined
        self._class_depth = 0
        self._function_depth = 0
        self._deep = deep

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                "module": alias.name,
                "name": alias.asname or alias.name,
                "type": "import",
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = "." * node.level + (node.module or "")
        for alias in node.names:
            self.imports.append({
                "module": module,
                "name": alias.name,
                "alias": alias.asname,
                "type": "from",
            })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if self._class_depth > 0 or self._function_depth > 0:
            return

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
        if self._class_depth == 0 and self._function_depth == 0:
            if not node.name.startswith("_"):
                self.functions.append(_extract_function_info(node))
            elif self._deep:
                info = _extract_function_info(node)
                info["private"] = True
                self.functions.append(info)
        self._function_depth += 1
        try:
            self.generic_visit(node)
        finally:
            self._function_depth -= 1

    def visit_AsyncFunctionDef(self, node):
        if self._class_depth == 0 and self._function_depth == 0:
            if not node.name.startswith("_"):
                self.functions.append(_extract_function_info(node))
            elif self._deep:
                info = _extract_function_info(node)
                info["private"] = True
                self.functions.append(info)
        self._function_depth += 1
        try:
            self.generic_visit(node)
        finally:
            self._function_depth -= 1

    def visit_Assign(self, node):
        """Detect module-level UPPER_CASE constants and ``__all__``."""
        if self._class_depth == 0 and self._function_depth == 0:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "__all__":
                        self.has_all = True
                    elif target.id == target.id.upper() and target.id.replace("_", "").isalnum() and not target.id[0].isdigit():
                        self.constants.append({
                            "name": target.id,
                            "line": node.lineno,
                        })
        self.generic_visit(node)


# ── Core scan logic ──────────────────────────────────────────────────


def _scan_python_files(
    src_dir: str,
    deep: bool = False,
    only_files: list[str] | None = None,
    include_empty: bool = False,
) -> dict:
    """Scan Python files under *src_dir* and return a raw inventory dict.

    The returned dict maps *relative* filepath strings (relative to
    *src_dir*) to file entry dicts.  The ``"language"`` key is
    intentionally absent here — callers (e.g. :class:`PythonExtractor`)
    are responsible for stamping it.
    """
    src_path = Path(src_dir).resolve()
    inventory = {}
    matcher = build_gitignore_matcher(src_path)
    py_files = [
        src_path / rel
        for rel in discover_source_files(
            str(src_path), (".py",), only_files=only_files, language="python", matcher=matcher,
        )
    ]

    for py_file in py_files:
        rel = py_file.relative_to(src_path)
        try:
            data = py_file.read_bytes()
            try:
                source = data.decode("utf-8")
            except UnicodeDecodeError:
                source = data.decode("cp1252")
            tree = ast.parse(source, filename=str(py_file))
        except UnicodeDecodeError:
            print(f"llm-wiki Python extractor: skipped undecodable file {rel.as_posix()}", file=sys.stderr)
            continue
        except OSError as exc:
            print(f"llm-wiki Python extractor: failed to read {rel.as_posix()}: {exc}", file=sys.stderr)
            continue
        except SyntaxError:
            continue

        visitor = ComponentVisitor(deep=deep)
        visitor.visit(tree)

        # Include the file if it has classes, public functions, constants,
        # __all__, or (in deep mode) private functions.
        has_content = (
            visitor.classes
            or visitor.functions
            or visitor.constants
            or visitor.has_all
            or include_empty
        )
        if has_content:
            file_entry = {
                "classes": visitor.classes,
                "functions": visitor.functions,
            }

            if visitor.constants:
                file_entry["constants"] = visitor.constants
            if visitor.has_all:
                file_entry["has_all"] = True

            if deep:
                file_entry["imports"] = visitor.imports
                file_entry["module_docstring"] = ast.get_docstring(tree) or ""
            else:
                # Slim format: strip rich fields for backward compat
                file_entry["classes"] = [
                    {"name": c["name"], "bases": c["bases"], "line": c["line"]}
                    for c in visitor.classes
                ]
                fns = []
                for f in visitor.functions:
                    fn = {"name": f["name"], "line": f["line"]}
                    if f.get("is_async"):
                        fn["async"] = True
                    if f.get("private"):
                        fn["private"] = True
                    fns.append(fn)
                file_entry["functions"] = fns

            inventory[rel.as_posix()] = file_entry

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
        include_empty: bool = False,
    ) -> dict:
        """Scan *src_dir* for Python files and return an inventory dict.

        Each file entry includes ``"language": "python"``.
        """
        inventory = _scan_python_files(
            src_dir, deep=deep, only_files=only_files,
            include_empty=include_empty,
        )
        for entry in inventory.values():
            entry["language"] = "python"
        return inventory
