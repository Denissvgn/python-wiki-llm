"""Source observations from stdlib AST; target modules are never imported."""

from __future__ import annotations

import ast
from collections import Counter


def expression(node) -> str:
    return ast.unparse(node) if node is not None else ""


def normalize(mode: str, text: str):
    return ast.dump(ast.parse(text, mode="eval"), include_attributes=False)


def parameters(args: ast.arguments) -> list[dict]:
    positional = [*args.posonlyargs, *args.args]
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    result = []
    for index, (arg, default) in enumerate(zip(positional, defaults)):
        item = {
            "name": arg.arg,
            "type": expression(arg.annotation),
            "kind": "positional_only"
            if index < len(args.posonlyargs)
            else "positional_or_keyword",
        }
        if default is not None:
            item["default"] = expression(default)
        result.append(item)
    if args.vararg:
        result.append(
            {
                "name": args.vararg.arg,
                "type": expression(args.vararg.annotation),
                "kind": "var_positional",
            }
        )
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        item = {
            "name": arg.arg,
            "type": expression(arg.annotation),
            "kind": "keyword_only",
        }
        if default is not None:
            item["default"] = expression(default)
        result.append(item)
    if args.kwarg:
        result.append(
            {
                "name": args.kwarg.arg,
                "type": expression(args.kwarg.annotation),
                "kind": "var_keyword",
            }
        )
    return result


def observe(text: str) -> dict:
    tree = ast.parse(text)
    records, imports = [], []
    class_occurrences = Counter()

    def declarations(body, owner="", owner_occurrence=1):
        for node in body:
            if isinstance(node, ast.ClassDef):
                class_occurrences[owner, node.name] += 1
                records.append(
                    {
                        "kind": "class",
                        "name": node.name,
                        "owner": owner,
                        "owner_occurrence": owner_occurrence,
                        "line": node.lineno,
                        "bases": [expression(base) for base in node.bases],
                    }
                )
                declarations(
                    node.body,
                    f"{owner}.{node.name}".strip("."),
                    class_occurrences[owner, node.name],
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                records.append(
                    {
                        "kind": "method" if owner else "function",
                        "name": node.name,
                        "owner": owner,
                        "owner_occurrence": owner_occurrence,
                        "line": node.lineno,
                        "params": parameters(node.args),
                        "return_type": expression(node.returns),
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "decorators": [
                            expression(item) for item in node.decorator_list
                        ],
                    }
                )
            elif (
                isinstance(node, ast.AnnAssign)
                and owner
                and isinstance(node.target, ast.Name)
            ):
                item = {
                    "kind": "attribute",
                    "name": node.target.id,
                    "owner": owner,
                    "owner_occurrence": owner_occurrence,
                    "line": node.lineno,
                    "type": expression(node.annotation),
                }
                if node.value is not None:
                    item["default"] = expression(node.value)
                records.append(item)
            elif isinstance(node, ast.ImportFrom) and not owner:
                imports.append(
                    {
                        "module": "." * node.level + (node.module or ""),
                        "names": [item.name for item in node.names],
                        "line": node.lineno,
                    }
                )
            elif isinstance(node, ast.Import) and not owner:
                imports.extend(
                    {"module": item.name, "names": [], "line": node.lineno}
                    for item in node.names
                )
            elif not owner and isinstance(node, (ast.If, ast.Try, ast.With)):
                declarations(node.body)
                declarations(getattr(node, "orelse", []))
                declarations(getattr(node, "finalbody", []))
                for handler in getattr(node, "handlers", []):
                    declarations(handler.body)

    declarations(tree.body)
    return {"declarations": records, "imports": imports}


def calls(text: str) -> list[dict]:
    """Keep lexical callers distinct and conservatively resolve local calls."""
    tree = ast.parse(text)
    module_functions = {
        n.name
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    result = []
    occurrences: Counter = Counter()

    def visit_function(node, parent=""):
        scope = f"{parent}.{node.name}".strip(".")
        occurrences[scope] += 1
        ordinal = occurrences[scope]
        shadowed = {p["name"] for p in parameters(node.args)}
        local_nodes = []

        def walk(item):
            if isinstance(
                item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
            ):
                if isinstance(
                    item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    shadowed.add(item.name)
                return
            local_nodes.append(item)
            for child in ast.iter_child_nodes(item):
                walk(child)

        for statement in node.body:
            walk(statement)
        for item in local_nodes:
            if isinstance(item, ast.Name) and isinstance(
                item.ctx, (ast.Store, ast.Del)
            ):
                shadowed.add(item.id)
            if isinstance(item, (ast.Import, ast.ImportFrom)):
                shadowed.update(
                    alias.asname or alias.name.split(".")[0] for alias in item.names
                )
        for item in local_nodes:
            if isinstance(item, ast.Call):
                target = expression(item.func)
                local = (
                    isinstance(item.func, ast.Name)
                    and target in module_functions
                    and target not in shadowed
                )
                result.append(
                    {
                        "caller": scope,
                        "occurrence": ordinal,
                        "caller_line": node.lineno,
                        "callee": target,
                        "line": item.lineno,
                        "resolution": "local" if local else "external-or-unresolved",
                    }
                )
        for child in node.body:
            descend(child, scope)

    def descend(node, parent=""):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visit_function(node, parent)
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                descend(child, f"{parent}.{node.name}".strip("."))
        else:
            for child in ast.iter_child_nodes(node):
                descend(child, parent)

    for node in tree.body:
        descend(node)
    return result
