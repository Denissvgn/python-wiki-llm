"""Python AST extractor for agent-wiki-cli."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from ..config import build_gitignore_matcher
from ..services.imports import build_module_path_resolver
from .common import (
    IMPORT_SCOPE_DEFERRED,
    IMPORT_SCOPE_TYPE_CHECKING,
    discover_source_files,
)
from .fastapi_contracts import extract_fastapi_declarations
from .python_contracts import (
    class_kind,
    explicit_type_alias,
    expression_to_str,
    extract_class_attributes as extract_contract_attributes,
    extract_enum_attributes,
    extract_model_config,
    extract_parameters,
    extract_validator,
    finalize_inventory_model_kinds,
    finalize_model_kinds,
    inferred_type_alias,
    is_pydantic_model,
    type_alias_record,
)


# ── AST helper utilities ──────────────────────────────────────────────


def _annotation_to_str(node) -> str:
    """Convert an AST annotation node to a readable string."""
    return expression_to_str(node)


def _default_to_str(node) -> str:
    """Convert a default-value AST node to a readable string."""
    return expression_to_str(node)


def _simple_reference_to_str(node) -> str:
    """Return a dotted reference for simple name/attribute expressions."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        value = _simple_reference_to_str(node.value)
        if value:
            return f"{value}.{node.attr}"
    return ""


def _is_simple_subscript_slice(node) -> bool:
    return isinstance(node, ast.Constant) or bool(_simple_reference_to_str(node))


def _summarize_expression(node) -> dict[str, str]:
    """Summarize an AST expression without retaining arbitrary source text."""
    if isinstance(node, ast.Name):
        return {"kind": "name", "value": node.id}
    if isinstance(node, ast.Attribute):
        value = _simple_reference_to_str(node)
        if value:
            return {"kind": "attribute", "value": value}
    if isinstance(node, ast.Constant):
        return {"kind": "literal", "value": repr(node.value)}
    if isinstance(node, ast.Subscript):
        value = _simple_reference_to_str(node.value)
        if value and _is_simple_subscript_slice(node.slice):
            return {"kind": "subscript", "value": f"{value}[...]"}
    if isinstance(node, ast.Call):
        value = _simple_reference_to_str(node.func)
        if value:
            return {"kind": "call", "value": f"{value}(...)"}
    if isinstance(node, ast.List):
        return {"kind": "literal", "value": "[...]"}
    if isinstance(node, ast.Tuple):
        return {"kind": "literal", "value": "(...)"}
    if isinstance(node, (ast.Set, ast.Dict)):
        return {"kind": "literal", "value": "{...}"}
    return {"kind": "expression", "value": "..."}


def _extract_decorators(node) -> list[str]:
    """Extract decorator names from a node."""
    return [expression_to_str(dec) for dec in node.decorator_list]


# Nodes that open a new scope; calls inside them belong to that inner scope,
# not the enclosing function, so the walk does not descend into them.
_SCOPE_BOUNDARIES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_DATA_EFFECT_LIMIT = 8
DATA_EFFECT_OBSERVATIONS_SCHEMA = "llm-wiki-data-effect-observations/v1"
IMPORT_LOCATION_OBSERVATIONS_SCHEMA = (
    "llm-wiki-import-location-observations/v1"
)
_DATA_EFFECT_KEYS = (
    "inputs",
    "reads",
    "writes",
    "returns",
    "boundary_effects",
)
_ATTRIBUTE_READ_ROOTS = {"self", "cls", "options"}
_FILESYSTEM_READ_CALLS = {"json.load"}
_FILESYSTEM_READ_METHODS = {"read_text", "read_bytes"}
_FILESYSTEM_WRITE_CALLS = {
    "shutil.copy",
    "shutil.copy2",
    "shutil.copyfile",
    "shutil.copytree",
    "shutil.move",
    "shutil.rmtree",
    "os.remove",
    "os.unlink",
    "os.rmdir",
}
_FILESYSTEM_WRITE_METHODS = {"write_text", "write_bytes", "unlink", "rmdir"}
_PROCESS_CALLS = {
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
}
_MUTATION_METHODS = {
    "append",
    "extend",
    "insert",
    "update",
    "add",
    "remove",
    "discard",
    "pop",
    "clear",
    "sort",
    "reverse",
}


def _call_arguments(node: ast.Call) -> dict:
    details: dict[str, list[dict[str, str]]] = {}
    args = [_summarize_expression(arg) for arg in node.args]
    if args:
        details["args"] = args

    kwargs = []
    for keyword in node.keywords:
        kwargs.append(
            {
                "name": keyword.arg if keyword.arg is not None else "**",
                **_summarize_expression(keyword.value),
            }
        )
    if kwargs:
        details["kwargs"] = kwargs
    return details


def _call_record(node: ast.Call, *, include_arguments: bool = False) -> dict | None:
    """Build a call record from an ``ast.Call`` node.

    Returns ``None`` for call targets we cannot name simply (e.g. calls on a
    subscript or on the result of another call). Callers still descend into the
    arguments so nested calls are not lost.
    """
    func = node.func
    if isinstance(func, ast.Name):
        record = {"name": func.id, "line": node.lineno}
    elif isinstance(func, ast.Attribute):
        record = {
            "name": func.attr,
            "attr": _annotation_to_str(func),
            "line": node.lineno,
        }
    else:
        return None
    if include_arguments:
        record.update(_call_arguments(node))
    return record


def _extract_calls(node) -> list[dict]:
    """Collect direct call targets within a function/method body.

    Walks the body but does not descend into nested function or class
    definitions, so their calls are attributed to the inner scope. Calls inside
    comprehensions and lambdas are kept (same scope). Every nameable occurrence
    is returned in source order so data-flow analysis can preserve call-site
    argument metadata for repeated calls to the same target.
    """
    calls: list[dict] = []

    def _walk(current) -> None:
        for child in ast.iter_child_nodes(current):
            if isinstance(child, _SCOPE_BOUNDARIES):
                continue
            if isinstance(child, ast.Call):
                record = _call_record(child, include_arguments=True)
                if record is not None:
                    calls.append(record)
            _walk(child)

    for statement in node.body:
        if isinstance(statement, _SCOPE_BOUNDARIES):
            continue
        _walk(statement)
    return calls


def _bound_import_name(alias: ast.alias, *, from_import: bool = False) -> str:
    if alias.asname:
        return alias.asname
    if from_import:
        return alias.name
    return alias.name.split(".", 1)[0]


def _iter_binding_targets(target) -> list[ast.AST]:
    if isinstance(target, (ast.Tuple, ast.List)):
        targets = []
        for elt in target.elts:
            targets.extend(_iter_binding_targets(elt))
        return targets
    if isinstance(target, ast.Starred):
        return _iter_binding_targets(target.value)
    return [target]


def _target_bound_names(target) -> set[str]:
    names = set()
    for item in _iter_binding_targets(target):
        if isinstance(item, ast.Name):
            names.add(item.id)
    return names


def _argument_bound_names(args: ast.arguments) -> set[str]:
    names = {arg.arg for arg in args.posonlyargs}
    names.update(arg.arg for arg in args.args)
    names.update(arg.arg for arg in args.kwonlyargs)
    if args.vararg is not None:
        names.add(args.vararg.arg)
    if args.kwarg is not None:
        names.add(args.kwarg.arg)
    return names


def _extract_module_globals(tree: ast.Module) -> set[str]:
    globals_: set[str] = set()
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            globals_.update(_bound_import_name(alias) for alias in statement.names)
        elif isinstance(statement, ast.ImportFrom):
            globals_.update(
                _bound_import_name(alias, from_import=True) for alias in statement.names
            )
        elif isinstance(statement, _SCOPE_BOUNDARIES):
            globals_.add(statement.name)
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                globals_.update(_target_bound_names(target))
        elif isinstance(statement, ast.AnnAssign):
            globals_.update(_target_bound_names(statement.target))
        elif isinstance(statement, ast.AugAssign):
            globals_.update(_target_bound_names(statement.target))
        elif isinstance(statement, (ast.For, ast.AsyncFor)):
            globals_.update(_target_bound_names(statement.target))
        elif isinstance(statement, ast.With):
            for item in statement.items:
                if item.optional_vars is not None:
                    globals_.update(_target_bound_names(item.optional_vars))
    return globals_


def _import_alias_target(
    alias: ast.alias, *, module: str = ""
) -> tuple[str, str] | None:
    if alias.name == "*":
        return None
    if module:
        return _bound_import_name(alias, from_import=True), f"{module}.{alias.name}"
    bound = _bound_import_name(alias)
    if alias.asname:
        return bound, alias.name
    return bound, bound


def _import_aliases_from_statement(statement) -> dict[str, str]:
    aliases: dict[str, str] = {}
    if isinstance(statement, ast.Import):
        for alias in statement.names:
            target = _import_alias_target(alias)
            if target is not None:
                aliases[target[0]] = target[1]
    elif isinstance(statement, ast.ImportFrom) and statement.module:
        module = "." * statement.level + statement.module
        for alias in statement.names:
            target = _import_alias_target(alias, module=module)
            if target is not None:
                aliases[target[0]] = target[1]
    return aliases


def _extract_import_aliases(tree: ast.Module) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for statement in tree.body:
        aliases.update(_import_aliases_from_statement(statement))
    return aliases


def _normalize_reference(name: str, import_aliases: dict[str, str]) -> str:
    if not name:
        return ""
    root, _, rest = name.partition(".")
    mapped = import_aliases.get(root)
    if not mapped:
        return name
    if not rest:
        return mapped
    return f"{mapped}.{rest}"


def _open_mode(node: ast.Call) -> str | None:
    mode_node = node.args[1] if len(node.args) > 1 else None
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode_node = keyword.value
            break
    if mode_node is None:
        return "r"
    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        return mode_node.value
    return None


def _classify_open_call(node: ast.Call) -> str | None:
    mode = _open_mode(node)
    if mode is None:
        return None
    if any(flag in mode for flag in ("w", "a", "x")):
        return "filesystem_write"
    return "filesystem_read"


def _classify_boundary_call(normalized: str, node: ast.Call) -> str | None:
    if normalized in {"open", "io.open", "pathlib.Path.open"}:
        return _classify_open_call(node)
    if normalized in _FILESYSTEM_READ_CALLS:
        return "filesystem_read"
    if normalized in _FILESYSTEM_WRITE_CALLS:
        return "filesystem_write"

    method = normalized.rsplit(".", 1)[-1]
    if method in _FILESYSTEM_READ_METHODS:
        return "filesystem_read"
    if method in _FILESYSTEM_WRITE_METHODS:
        return "filesystem_write"

    if normalized in {"os.getenv", "pathlib.Path.home"}:
        return "environment_read"
    if normalized in {"os.environ.get", "os.environ.__getitem__"}:
        return "environment_read"
    if normalized in {
        "os.environ.update",
        "os.environ.clear",
        "os.environ.pop",
        "os.environ.popitem",
        "os.environ.setdefault",
        "os.putenv",
        "os.unsetenv",
    }:
        return "environment_write"

    if normalized in _PROCESS_CALLS:
        return "process"
    if (
        normalized.startswith("requests.")
        or normalized.startswith("httpx.")
        or normalized.startswith("urllib.request.")
        or normalized.startswith("socket.")
    ):
        return "network"
    if normalized in {"print", "sys.stdout.write", "sys.stderr.write"}:
        return "output"
    if normalized.startswith("logging."):
        return "logging"
    if "." in normalized and method in _MUTATION_METHODS:
        return "mutation"
    return None


def _boundary_call_record(
    node: ast.Call,
    import_aliases: dict[str, str],
) -> dict | None:
    target = _simple_reference_to_str(node.func)
    if not target:
        return None
    kind = _classify_boundary_call(_normalize_reference(target, import_aliases), node)
    if kind is None:
        return None
    return {"kind": kind, "target": target, "line": node.lineno}


def _environment_subscript_record(
    node: ast.Subscript,
    import_aliases: dict[str, str],
    kind: str,
) -> dict | None:
    target = _simple_reference_to_str(node.value)
    if _normalize_reference(target, import_aliases) != "os.environ":
        return None
    return {"kind": kind, "target": f"{target}[...]", "line": node.lineno}


def _collect_function_scope(node) -> tuple[set[str], set[str], dict[str, str]]:
    local_bindings = _argument_bound_names(node.args)
    global_declarations: set[str] = set()
    import_aliases: dict[str, str] = {}

    def _walk(current) -> None:
        if isinstance(current, ast.Global):
            global_declarations.update(current.names)
            return
        if isinstance(current, _SCOPE_BOUNDARIES):
            local_bindings.add(current.name)
            return
        if isinstance(current, ast.Import):
            import_aliases.update(_import_aliases_from_statement(current))
            local_bindings.update(_bound_import_name(alias) for alias in current.names)
        elif isinstance(current, ast.ImportFrom):
            import_aliases.update(_import_aliases_from_statement(current))
            local_bindings.update(
                _bound_import_name(alias, from_import=True) for alias in current.names
            )
        elif isinstance(current, ast.Assign):
            for target in current.targets:
                local_bindings.update(_target_bound_names(target))
        elif isinstance(current, ast.AnnAssign):
            local_bindings.update(_target_bound_names(current.target))
        elif isinstance(current, ast.AugAssign):
            local_bindings.update(_target_bound_names(current.target))
        elif isinstance(current, (ast.For, ast.AsyncFor)):
            local_bindings.update(_target_bound_names(current.target))
        elif isinstance(current, (ast.With, ast.AsyncWith)):
            for item in current.items:
                if item.optional_vars is not None:
                    local_bindings.update(_target_bound_names(item.optional_vars))
        elif isinstance(current, ast.ExceptHandler) and current.name:
            local_bindings.add(current.name)
        elif isinstance(current, ast.NamedExpr):
            local_bindings.update(_target_bound_names(current.target))

        for child in ast.iter_child_nodes(current):
            _walk(child)

    for statement in node.body:
        _walk(statement)
    local_bindings.difference_update(global_declarations)
    return local_bindings, global_declarations, import_aliases


def _attribute_read_name(node: ast.Attribute) -> str:
    name = _simple_reference_to_str(node)
    if not name:
        return ""
    root = name.split(".", 1)[0]
    if root in _ATTRIBUTE_READ_ROOTS:
        return name
    return ""


def _write_record(target, global_declarations: set[str]) -> dict | None:
    if isinstance(target, ast.Attribute):
        name = _simple_reference_to_str(target)
        if name:
            return {"kind": "attribute", "name": name, "line": target.lineno}
    if isinstance(target, ast.Subscript):
        summary = _summarize_expression(target)
        if summary["kind"] == "subscript":
            return {
                "kind": "subscript",
                "name": summary["value"],
                "line": target.lineno,
            }
    if isinstance(target, ast.Name) and target.id in global_declarations:
        return {"kind": "global", "name": target.id, "line": target.lineno}
    return None


class _DataEffectVisitor(ast.NodeVisitor):
    def __init__(
        self,
        module_globals: set[str],
        local_bindings: set[str],
        global_declarations: set[str],
        import_aliases: dict[str, str],
        return_annotation: str,
    ):
        self.module_globals = module_globals
        self.local_bindings = local_bindings
        self.global_declarations = global_declarations
        self.import_aliases = import_aliases
        self.return_annotation = return_annotation
        self.reads: list[dict] = []
        self.writes: list[dict] = []
        self.returns: list[dict] = []
        self.boundary_effects: list[dict] = []
        self.observed: dict[str, int] = {
            "reads": 0,
            "writes": 0,
            "returns": 0,
            "boundary_effects": 0,
        }
        self._seen: dict[str, set[tuple]] = {
            "reads": set(),
            "writes": set(),
            "returns": set(),
            "boundary_effects": set(),
        }

    def _add(self, category: str, record: dict) -> None:
        key = tuple(record.items())
        if key in self._seen[category]:
            return
        self._seen[category].add(key)
        self.observed[category] += 1
        bucket = getattr(self, category)
        if len(bucket) >= _DATA_EFFECT_LIMIT:
            return
        bucket.append(record)

    def _add_write_targets(self, target) -> None:
        for item in _iter_binding_targets(target):
            boundary_record = None
            if isinstance(item, ast.Subscript):
                boundary_record = _environment_subscript_record(
                    item,
                    self.import_aliases,
                    "environment_write",
                )
            if boundary_record is not None:
                self._add("boundary_effects", boundary_record)
            record = _write_record(item, self.global_declarations)
            if record is not None:
                self._add("writes", record)

    def visit_FunctionDef(self, node) -> None:
        return

    def visit_AsyncFunctionDef(self, node) -> None:
        return

    def visit_ClassDef(self, node) -> None:
        return

    def visit_Global(self, node) -> None:
        return

    def visit_Call(self, node) -> None:
        record = _boundary_call_record(node, self.import_aliases)
        if record is not None:
            self._add("boundary_effects", record)
        for arg in node.args:
            self.visit(arg)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Subscript(self, node) -> None:
        if isinstance(node.ctx, ast.Load):
            record = _environment_subscript_record(
                node,
                self.import_aliases,
                "environment_read",
            )
            if record is not None:
                self._add("boundary_effects", record)
        self.generic_visit(node)

    def visit_Attribute(self, node) -> None:
        if isinstance(node.ctx, ast.Load):
            name = _attribute_read_name(node)
            if name:
                self._add(
                    "reads",
                    {"kind": "attribute", "name": name, "line": node.lineno},
                )
                return
        self.generic_visit(node)

    def visit_Name(self, node) -> None:
        if (
            isinstance(node.ctx, ast.Load)
            and node.id in self.module_globals
            and node.id not in self.local_bindings
        ):
            self._add("reads", {"kind": "global", "name": node.id, "line": node.lineno})

    def visit_Assign(self, node) -> None:
        self.visit(node.value)
        for target in node.targets:
            self._add_write_targets(target)

    def visit_AnnAssign(self, node) -> None:
        if node.value is not None:
            self.visit(node.value)
        self._add_write_targets(node.target)

    def visit_AugAssign(self, node) -> None:
        self.visit(node.value)
        self._add_write_targets(node.target)

    def visit_For(self, node: ast.For | ast.AsyncFor) -> None:
        self.visit(node.iter)
        self._add_write_targets(node.target)
        for statement in node.body:
            self.visit(statement)
        for statement in node.orelse:
            self.visit(statement)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit_For(node)

    def visit_With(self, node: ast.With | ast.AsyncWith) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars is not None:
                self._add_write_targets(item.optional_vars)
        for statement in node.body:
            self.visit(statement)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self.visit_With(node)

    def visit_Delete(self, node) -> None:
        for target in node.targets:
            self._add_write_targets(target)

    def visit_NamedExpr(self, node) -> None:
        self.visit(node.value)
        self._add_write_targets(node.target)

    def visit_Return(self, node) -> None:
        if node.value is None:
            self._add("returns", {"kind": "none", "line": node.lineno})
            return
        record = {**_summarize_expression(node.value), "line": node.lineno}
        if self.return_annotation:
            record["annotation"] = self.return_annotation
        self._add("returns", record)
        self.visit(node.value)


def _extract_data_effects(
    node,
    params: list[dict],
    module_globals: set[str],
    module_import_aliases: dict[str, str],
    return_annotation: str,
    *,
    coverage: dict[str, dict] | None = None,
) -> dict:
    local_bindings, global_declarations, local_import_aliases = _collect_function_scope(
        node
    )
    import_aliases = {**module_import_aliases, **local_import_aliases}
    visitor = _DataEffectVisitor(
        module_globals=module_globals,
        local_bindings=local_bindings,
        global_declarations=global_declarations,
        import_aliases=import_aliases,
        return_annotation=return_annotation,
    )
    for statement in node.body:
        visitor.visit(statement)

    effects: dict[str, list[dict]] = {}
    if params:
        inputs = []
        for param in params[:_DATA_EFFECT_LIMIT]:
            record = {key: value for key, value in param.items() if key != "kind"}
            record["kind"] = "param"
            if param.get("kind"):
                record["parameter_kind"] = param["kind"]
            inputs.append(record)
        effects["inputs"] = inputs
    if visitor.reads:
        effects["reads"] = visitor.reads
    if visitor.writes:
        effects["writes"] = visitor.writes
    if visitor.returns:
        effects["returns"] = visitor.returns
    if visitor.boundary_effects:
        effects["boundary_effects"] = visitor.boundary_effects
    if coverage is not None:
        observed_by_kind = {
            "inputs": len(params),
            **visitor.observed,
        }
        for kind in _DATA_EFFECT_KEYS:
            observed = observed_by_kind[kind]
            emitted = len(effects.get(kind, []))
            coverage[kind] = {
                "observed": observed,
                "emitted": emitted,
                "omitted": observed - emitted,
                "limit": _DATA_EFFECT_LIMIT,
                "truncated": observed > emitted,
            }
    return effects


def _assign_target_name(targets) -> str:
    """Name an assignment's target: ``app`` in ``app = Flask(...)``.

    Falls back to the rendered attribute or subscript (``registry["default"]``)
    so a call assigned to external state is labeled the same way a bare
    assignment to it is. Tuple targets stay empty — no single name describes them.
    """
    for target in targets:
        if isinstance(target, ast.Name):
            return target.id
    for target in targets:
        if isinstance(target, (ast.Attribute, ast.Subscript)):
            return _annotation_to_str(target)
    return ""


def _module_call_record(call: ast.Call, target: str = "") -> dict | None:
    """Build a module-level side-effect record, optionally with its bound name.

    Returns ``None`` for call targets we cannot name simply (same rule as
    :func:`_call_record`). ``target`` is the assigned variable, kept before
    ``line`` for a tidy ``{name, attr?, target?, line}`` shape.
    """
    record = _call_record(call)
    if record is None:
        return None
    if not target:
        return record
    ordered = {"name": record["name"]}
    if "attr" in record:
        ordered["attr"] = record["attr"]
    ordered["target"] = target
    ordered["line"] = record["line"]
    return ordered


def _module_mutation_record(statement: ast.Assign) -> dict | None:
    """Record an import-time assignment that mutates state outside the module.

    ``sys.modules[__name__] = impl`` (the module-alias shim) and
    ``logging.root.level = DEBUG`` change objects other modules can observe, so
    they belong in load-order analysis even though no call is made. Assignments
    to a plain ``Name`` bind module-local state instead and are covered by
    ``constants``/``__all__``, so they are not side effects.
    """
    targets = [
        target
        for target in statement.targets
        if isinstance(target, (ast.Subscript, ast.Attribute))
    ]
    if not targets:
        return None
    return {
        "name": _annotation_to_str(statement.value),
        "target": _annotation_to_str(targets[0]),
        "line": statement.lineno,
    }


def _is_self_module_alias(statement) -> bool:
    """Detect ``sys.modules[__name__] = other`` — a module replacing itself."""
    if not isinstance(statement, ast.Assign):
        return False
    for target in statement.targets:
        if (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Attribute)
            and target.value.attr == "modules"
            and isinstance(target.slice, ast.Name)
            and target.slice.id == "__name__"
        ):
            return True
    return False


def module_alias_target(tree: ast.Module) -> str:
    """Return the module a self-aliasing file redirects to, else ``""``.

    ``sys.modules[__name__] = impl`` makes importing this path yield *impl*
    itself, so the file is a redirect rather than a module: it has no symbols of
    its own and its name is another module's name. Callers use this to avoid
    describing a redirect as though it were a separate unit.
    """
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and _is_self_module_alias(statement):
            return _annotation_to_str(statement.value)
    return ""


def _import_time_body(statement, type_checking_names: set[str]) -> list:
    """Return the nested statements of *statement* that run at import time.

    ``try``/``with``/``if`` blocks at module scope execute while the module
    loads — an optional-dependency fallback or a platform branch is import-time
    work. The two guards that do *not* run are ``if __name__ == "__main__":``
    (handled as an entry point) and ``if TYPE_CHECKING:`` (never executed),
    whose ``else:`` branch is still the runtime one.
    """
    if isinstance(statement, ast.Try):
        nested = list(statement.body) + list(statement.orelse)
        for handler in statement.handlers:
            nested.extend(handler.body)
        nested.extend(statement.finalbody)
        return nested
    if isinstance(statement, (ast.With, ast.AsyncWith)):
        return list(statement.body)
    if isinstance(statement, ast.If):
        if _is_main_guard(statement.test):
            return []
        if _is_type_checking_test(statement.test, type_checking_names):
            return list(statement.orelse)
        return list(statement.body) + list(statement.orelse)
    return []


def _collect_module_calls(
    body, calls: list[dict], type_checking_names: set[str]
) -> None:
    for statement in body:
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            record = _module_call_record(statement.value)
        elif isinstance(statement, ast.Assign) and isinstance(
            statement.value, ast.Call
        ):
            record = _module_call_record(
                statement.value, _assign_target_name(statement.targets)
            )
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.target, ast.Name)
        ):
            record = _module_call_record(statement.value, statement.target.id)
        elif isinstance(statement, ast.Assign):
            record = _module_mutation_record(statement)
        elif isinstance(statement, (ast.Try, ast.With, ast.AsyncWith, ast.If)):
            _collect_module_calls(
                _import_time_body(statement, type_checking_names),
                calls,
                type_checking_names,
            )
            continue
        else:
            continue
        if record is not None:
            calls.append(record)


def _extract_module_calls(tree: ast.Module) -> list[dict]:
    """Collect module-scope executable side effects (import-time work).

    Covers ``Expr`` calls (``logging.basicConfig(...)``, ``register()``),
    ``Assign``/``AnnAssign`` whose value is a call (``app = Flask(__name__)``),
    and assignments that mutate an external object (``sys.modules[__name__] =
    impl``). Descends into module-scope ``try``/``with``/``if`` blocks, which do
    run while the module loads, but not into ``def``/``class`` bodies (covered
    by per-function ``calls``) nor into the ``if __name__ == "__main__":`` and
    ``if TYPE_CHECKING:`` guards, which do not.
    """
    calls: list[dict] = []
    _collect_module_calls(tree.body, calls, _collect_type_checking_names(tree))
    return calls


def _extract_function_info(
    node,
    deep: bool = False,
    module_globals: set[str] | None = None,
    module_import_aliases: dict[str, str] | None = None,
    *,
    omit_method_receiver: bool = False,
    data_effect_observations: list[dict] | None = None,
    observation_symbol: str | None = None,
) -> dict:
    """Extract full function/method info from a FunctionDef or AsyncFunctionDef.

    When *deep* is true, a ``"calls"`` list of in-body call targets is added
    (omitted when the body makes no nameable calls).
    """
    info = {
        "name": node.name,
        "line": node.lineno,
        "docstring": ast.get_docstring(node) or "",
        "decorators": _extract_decorators(node),
        "is_async": isinstance(node, ast.AsyncFunctionDef),
    }

    params = extract_parameters(
        node.args, omit_method_receiver=omit_method_receiver
    )

    return_type = _annotation_to_str(node.returns)
    info["params"] = params
    info["return_type"] = return_type

    if deep:
        calls = _extract_calls(node)
        if calls:
            info["calls"] = calls
        effect_coverage: dict[str, dict] | None = (
            {} if data_effect_observations is not None else None
        )
        data_effects = _extract_data_effects(
            node,
            params,
            module_globals or set(),
            module_import_aliases or {},
            return_type,
            coverage=effect_coverage,
        )
        if data_effects:
            info["data_effects"] = data_effects
        if data_effect_observations is not None:
            data_effect_observations.append(
                {
                    "symbol": observation_symbol or node.name,
                    "line": node.lineno,
                    "coverage": effect_coverage,
                }
            )

    return info


def _extract_class_attributes(
    node, module_import_aliases: dict[str, str] | None = None
) -> list[dict]:
    """Extract annotated attributes from a class body (Pydantic fields, dataclass fields, etc.)."""
    return extract_contract_attributes(node, module_import_aliases or {})


def _string_list(node) -> list[str]:
    """Return the string constants of a ``List``/``Tuple`` literal (else empty)."""
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    return [
        elt.value
        for elt in node.elts
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
    ]


def _safe_name_or_attribute(node) -> dict | None:
    if isinstance(node, ast.Name):
        return {"kind": "name", "value": node.id}
    if isinstance(node, ast.Attribute):
        parent = _safe_name_or_attribute(node.value)
        if parent is None:
            return None
        return {"kind": "attribute", "value": f"{parent['value']}.{node.attr}"}
    return None


def _safe_constant_value(node) -> dict | None:
    """Summarize small static constant values without executing user code."""
    if not isinstance(node, ast.Dict):
        return None
    items = []
    for key_node, value_node in zip(node.keys, node.values):
        if not isinstance(key_node, ast.Constant) or not isinstance(
            key_node.value, str
        ):
            return None
        value = _safe_name_or_attribute(value_node)
        if value is None:
            return None
        items.append({"key": key_node.value, "value": value})
    return {"kind": "dict", "items": items}


def _is_main_guard(test) -> bool:
    """Detect an ``if __name__ == "__main__"`` test node."""
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


_TYPE_CHECKING_MODULES = frozenset({"typing", "typing_extensions"})


def _collect_type_checking_names(tree: ast.Module) -> set[str]:
    """Names bound to ``typing.TYPE_CHECKING`` anywhere in *tree*.

    ``from typing import TYPE_CHECKING as _TYPE_CHECKING`` is common in modules
    that keep their public namespace clean, so the alias — not just the bare
    name — has to be recognized. A name that cannot be traced back to an import
    is not treated as the guard, which keeps an unknown spelling on the
    conservative side: its imports stay classified as running at import time.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in _TYPE_CHECKING_MODULES:
            for alias in node.names:
                if alias.name == "TYPE_CHECKING":
                    names.add(alias.asname or alias.name)
    return names


def _is_type_checking_test(test, names: set[str]) -> bool:
    """Detect an ``if TYPE_CHECKING:`` / ``if typing.TYPE_CHECKING:`` test."""
    if isinstance(test, ast.Name):
        return test.id in names
    if isinstance(test, ast.Attribute):
        return test.attr == "TYPE_CHECKING"
    return False


# ── AST visitor ───────────────────────────────────────────────────────


class ComponentVisitor(ast.NodeVisitor):
    def __init__(
        self,
        deep: bool = False,
        module_globals: set[str] | None = None,
        module_import_aliases: dict[str, str] | None = None,
        data_effect_observations: list[dict] | None = None,
        import_location_observations: list[dict] | None = None,
    ):
        self.classes = []
        self.functions = []  # top-level functions only
        self.imports = []
        self.constants = []  # UPPER_CASE module-level assignments
        self.has_all = False  # whether __all__ is defined
        self.all_exports = []  # names listed in __all__ (when statically known)
        self.has_main = False  # whether an `if __name__ == "__main__"` guard exists
        self.main_block_calls = []  # deep-mode calls inside the __main__ guard
        self.nested_functions = []  # decorated functions defined inside other defs
        self._class_depth = 0
        self._function_depth = 0
        self._type_checking_depth = 0
        self._type_checking_names: set[str] = set()
        self._deep = deep
        self._module_globals = module_globals or set()
        self._module_import_aliases = module_import_aliases or {}
        self._data_effect_observations = data_effect_observations
        self._import_location_observations = import_location_observations

    def _import_scope(self) -> str:
        """Classify where an import sits, or ``""`` when it runs at import time.

        A ``TYPE_CHECKING`` guard never executes, and a function body executes
        only when called; neither participates in module load order. A class
        body *does* run at import time, so ``_class_depth`` is not consulted.
        """
        if self._type_checking_depth > 0:
            return IMPORT_SCOPE_TYPE_CHECKING
        if self._function_depth > 0:
            return IMPORT_SCOPE_DEFERRED
        return ""

    def _record_import(
        self, record: dict, node: ast.Import | ast.ImportFrom
    ) -> None:
        """Retain the legacy import shape and optional source-location sidecar."""
        scope = self._import_scope()
        if scope:
            # Omitted at module scope so unclassified records keep the legacy
            # contract: "no scope key" means "executes at import time".
            record["scope"] = scope
        import_index = len(self.imports)
        self.imports.append(record)
        if self._import_location_observations is not None:
            self._import_location_observations.append(
                {
                    "import_index": import_index,
                    "module": record["module"],
                    "name": record["name"],
                    "line": node.lineno,
                }
            )

    def visit_Import(self, node):
        for alias in node.names:
            self._record_import(
                {
                    "module": alias.name,
                    "name": alias.asname or alias.name,
                    "type": "import",
                },
                node,
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = "." * node.level + (node.module or "")
        for alias in node.names:
            self._record_import(
                {
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname,
                    "type": "from",
                },
                node,
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if self._class_depth > 0 or self._function_depth > 0:
            return

        bases = [_annotation_to_str(b) for b in node.bases]
        docstring = ast.get_docstring(node) or ""
        decorators = _extract_decorators(node)
        kind = class_kind(node, self._module_import_aliases)
        attributes = (
            extract_enum_attributes(node)
            if kind == "enum"
            else _extract_class_attributes(node, self._module_import_aliases)
        )

        # Extract methods (including private for completeness)
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_static_method = any(
                    _annotation_to_str(decorator).split("(", 1)[0] == "staticmethod"
                    for decorator in child.decorator_list
                )
                methods.append(
                    _extract_function_info(
                        child,
                        deep=self._deep,
                        module_globals=self._module_globals,
                        module_import_aliases=self._module_import_aliases,
                        omit_method_receiver=not is_static_method,
                        data_effect_observations=self._data_effect_observations,
                        observation_symbol=f"{node.name}.{child.name}",
                    )
                )
                validator = extract_validator(child, self._module_import_aliases)
                if validator is not None:
                    methods[-1]["validator"] = validator

        class_info = {
            "name": node.name,
            "kind": kind,
            "bases": bases,
            "line": node.lineno,
            "docstring": docstring,
            "decorators": decorators,
            "attributes": attributes,
            "methods": methods,
        }
        if is_pydantic_model(node, self._module_import_aliases):
            class_info["model_kind"] = "pydantic"
        model_config = extract_model_config(node, self._module_import_aliases)
        if model_config:
            class_info["model_config"] = model_config
        self.classes.append(class_info)
        # Don't generic_visit — we already walked class body for methods/attrs

    def visit_FunctionDef(self, node):
        # Only capture top-level functions (not methods inside classes)
        if self._class_depth == 0 and self._function_depth == 0:
            if not node.name.startswith("_"):
                self.functions.append(
                    _extract_function_info(
                        node,
                        deep=self._deep,
                        module_globals=self._module_globals,
                        module_import_aliases=self._module_import_aliases,
                        data_effect_observations=self._data_effect_observations,
                    )
                )
            elif self._deep:
                info = _extract_function_info(
                    node,
                    deep=self._deep,
                    module_globals=self._module_globals,
                    module_import_aliases=self._module_import_aliases,
                    data_effect_observations=self._data_effect_observations,
                )
                info["private"] = True
                self.functions.append(info)
        elif self._deep and node.decorator_list:
            # Decorated functions nested inside a factory (e.g. @app.route,
            # @server.tool) are framework entry points even though they are not
            # module-level. Capture them separately from regular functions.
            self.nested_functions.append(
                _extract_function_info(
                    node,
                    deep=True,
                    module_globals=self._module_globals,
                    module_import_aliases=self._module_import_aliases,
                    data_effect_observations=self._data_effect_observations,
                )
            )
        self._function_depth += 1
        try:
            self.generic_visit(node)
        finally:
            self._function_depth -= 1

    def visit_AsyncFunctionDef(self, node):
        if self._class_depth == 0 and self._function_depth == 0:
            if not node.name.startswith("_"):
                self.functions.append(
                    _extract_function_info(
                        node,
                        deep=self._deep,
                        module_globals=self._module_globals,
                        module_import_aliases=self._module_import_aliases,
                        data_effect_observations=self._data_effect_observations,
                    )
                )
            elif self._deep:
                info = _extract_function_info(
                    node,
                    deep=self._deep,
                    module_globals=self._module_globals,
                    module_import_aliases=self._module_import_aliases,
                    data_effect_observations=self._data_effect_observations,
                )
                info["private"] = True
                self.functions.append(info)
        elif self._deep and node.decorator_list:
            # Decorated functions nested inside a factory (e.g. @app.route,
            # @server.tool) are framework entry points even though they are not
            # module-level. Capture them separately from regular functions.
            self.nested_functions.append(
                _extract_function_info(
                    node,
                    deep=True,
                    module_globals=self._module_globals,
                    module_import_aliases=self._module_import_aliases,
                    data_effect_observations=self._data_effect_observations,
                )
            )
        self._function_depth += 1
        try:
            self.generic_visit(node)
        finally:
            self._function_depth -= 1

    def visit_Assign(self, node):
        """Detect module-level UPPER_CASE constants and ``__all__``."""
        if self._class_depth == 0 and self._function_depth == 0:
            alias = inferred_type_alias(
                node, self._module_import_aliases, deep=self._deep
            )
            if alias is not None:
                self.classes.append(alias)
                return
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "__all__":
                        self.has_all = True
                        self.all_exports = _string_list(node.value)
                    elif (
                        target.id == target.id.upper()
                        and target.id.replace("_", "").isalnum()
                        and not target.id[0].isdigit()
                    ):
                        constant = {
                            "name": target.id,
                            "line": node.lineno,
                        }
                        if self._deep:
                            value = _safe_constant_value(node.value)
                            if value is not None:
                                constant["value"] = value
                        self.constants.append(constant)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        """Detect explicit PEP 613 module-level type aliases."""
        if self._class_depth == 0 and self._function_depth == 0:
            alias = explicit_type_alias(
                node, self._module_import_aliases, deep=self._deep
            )
            if alias is not None:
                self.classes.append(alias)
                return
        self.generic_visit(node)

    def visit_TypeAlias(self, node):
        """Detect PEP 695 aliases when the running Python parser supports them."""
        if self._class_depth > 0 or self._function_depth > 0:
            return
        name = getattr(getattr(node, "name", None), "id", "")
        value = getattr(node, "value", None)
        if not name or value is None:
            return
        type_params = [
            expression_to_str(param) for param in getattr(node, "type_params", [])
        ]
        self.classes.append(
            type_alias_record(
                name,
                value,
                node.lineno,
                self._module_import_aliases,
                deep=self._deep,
                type_params=type_params,
            )
        )

    def visit_Module(self, node):
        """Seed the ``TYPE_CHECKING`` aliases before walking the module body."""
        self._type_checking_names = _collect_type_checking_names(node)
        self.generic_visit(node)

    def visit_If(self, node):
        """Detect the ``__main__`` entry guard and the ``TYPE_CHECKING`` guard."""
        if (
            self._class_depth == 0
            and self._function_depth == 0
            and _is_main_guard(node.test)
        ):
            self.has_main = True
            if self._deep:
                self.main_block_calls.extend(_extract_calls(node))
        if _is_type_checking_test(node.test, self._type_checking_names):
            # Only the body is type-only; an ``else:`` branch is the runtime one.
            self.visit(node.test)
            self._type_checking_depth += 1
            try:
                for child in node.body:
                    self.visit(child)
            finally:
                self._type_checking_depth -= 1
            for child in node.orelse:
                self.visit(child)
            return
        self.generic_visit(node)


# ── Core scan logic ──────────────────────────────────────────────────


def _scan_python_files(
    src_dir: str,
    deep: bool = False,
    only_files: list[str] | None = None,
    include_empty: bool = False,
    source_files: list[str] | None = None,
    data_effect_observations: list[dict] | None = None,
    import_location_observations: list[dict] | None = None,
) -> dict:
    """Scan Python files under *src_dir* and return a raw inventory dict.

    The returned dict maps *relative* filepath strings (relative to
    *src_dir*) to file entry dicts.  The ``"language"`` key is
    intentionally absent here — callers (e.g. :class:`PythonExtractor`)
    are responsible for stamping it.
    """
    src_path = Path(src_dir).resolve()
    inventory = {}
    if source_files is None:
        matcher = build_gitignore_matcher(src_path)
        source_files = discover_source_files(
            str(src_path),
            (".py",),
            only_files=only_files,
            language="python",
            matcher=matcher,
        )
    py_files = [src_path / rel for rel in source_files]

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
            print(
                f"llm-wiki Python extractor: skipped undecodable file {rel.as_posix()}",
                file=sys.stderr,
            )
            continue
        except OSError as exc:
            print(
                f"llm-wiki Python extractor: failed to read {rel.as_posix()}: {exc}",
                file=sys.stderr,
            )
            continue
        except SyntaxError:
            continue

        file_effect_observations: list[dict] | None = (
            [] if data_effect_observations is not None else None
        )
        file_import_observations: list[dict] | None = (
            [] if import_location_observations is not None else None
        )
        visitor = ComponentVisitor(
            deep=deep,
            module_globals=_extract_module_globals(tree),
            module_import_aliases=_extract_import_aliases(tree),
            data_effect_observations=file_effect_observations,
            import_location_observations=file_import_observations,
        )
        visitor.visit(tree)
        if data_effect_observations is not None:
            data_effect_observations.extend(
                {"file": rel.as_posix(), **observation}
                for observation in file_effect_observations or []
            )
        finalize_model_kinds(visitor.classes)

        # Module-level side effects (deep only) make an otherwise-defless module
        # (e.g. a config module that only calls ``logging.basicConfig(...)``)
        # meaningful content for load-order analysis.
        module_calls = _extract_module_calls(tree) if deep else []
        fastapi_declarations = (
            extract_fastapi_declarations(source, filepath=rel.as_posix())
            if deep
            else {}
        )

        # Include the file if it has classes, public functions, constants,
        # __all__, (in deep mode) private functions or module-level side effects.
        declares_symbols = (
            visitor.classes
            or visitor.functions
            or visitor.constants
            or visitor.has_all
            or fastapi_declarations
        )
        # A file whose whole body redirects itself with
        # ``sys.modules[__name__] = impl`` is an alias, not a module: at runtime
        # its name resolves to *impl*. Describing it as a unit of its own would
        # invent an empty module and, worse, shadow the real one when a symbol
        # is resolved through the alias path.
        is_module_alias = bool(module_alias_target(tree)) and not declares_symbols
        has_content = (
            declares_symbols or (module_calls and not is_module_alias) or include_empty
        )
        if has_content:
            file_entry: dict[str, object] = {
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
                if visitor.all_exports:
                    file_entry["all_exports"] = visitor.all_exports
                if visitor.has_main:
                    file_entry["main_block"] = True
                if visitor.main_block_calls:
                    file_entry["main_block_calls"] = visitor.main_block_calls
                if visitor.nested_functions:
                    file_entry["nested_functions"] = visitor.nested_functions
                if module_calls:
                    file_entry["module_calls"] = module_calls
                if fastapi_declarations:
                    file_entry["frameworks"] = {"fastapi": fastapi_declarations}
            else:
                # Slim format: strip rich fields for backward compat
                slim_classes = []
                for class_info in visitor.classes:
                    slim = {
                        "name": class_info["name"],
                        "bases": class_info["bases"],
                        "line": class_info["line"],
                    }
                    if class_info.get("kind"):
                        slim["kind"] = class_info["kind"]
                    if class_info.get("model_kind"):
                        slim["model_kind"] = class_info["model_kind"]
                    if class_info.get("inferred"):
                        slim["inferred"] = True
                    slim_classes.append(slim)
                file_entry["classes"] = slim_classes
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
            if import_location_observations is not None:
                import_location_observations.extend(
                    {"source_path": rel.as_posix(), **observation}
                    for observation in file_import_observations or []
                )

    resolver = build_module_path_resolver(inventory)
    finalize_inventory_model_kinds(
        inventory, module_candidates=resolver.candidates
    )
    return inventory


# ── Public extractor class ────────────────────────────────────────────


class PythonExtractor:
    """Extractor for Python source files using the built-in :mod:`ast` module.

    Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.
    """

    def __init__(self) -> None:
        self.last_data_effect_observations: dict | None = None
        self.last_import_observations: dict | None = None

    def extract(
        self,
        src_dir: str,
        only_files: list[str] | None = None,
        deep: bool = False,
        include_empty: bool = False,
        source_files: list[str] | None = None,
        capture_data_effect_observations: bool = False,
        capture_import_observations: bool = False,
    ) -> dict:
        """Scan *src_dir* for Python files and return an inventory dict.

        Each file entry includes ``"language": "python"``.
        """
        if capture_data_effect_observations and not deep:
            raise ValueError("data-effect observations require deep extraction")
        if capture_import_observations and not deep:
            raise ValueError("import observations require deep extraction")
        observations: list[dict] | None = (
            [] if capture_data_effect_observations else None
        )
        import_observations: list[dict] | None = (
            [] if capture_import_observations else None
        )
        self.last_data_effect_observations = None
        self.last_import_observations = None
        inventory = _scan_python_files(
            src_dir,
            deep=deep,
            only_files=only_files,
            include_empty=include_empty,
            source_files=source_files,
            data_effect_observations=observations,
            import_location_observations=import_observations,
        )
        for entry in inventory.values():
            entry["language"] = "python"
        if observations is not None:
            self.last_data_effect_observations = {
                "schema_version": DATA_EFFECT_OBSERVATIONS_SCHEMA,
                "callables": sorted(
                    observations,
                    key=lambda item: (
                        item["file"],
                        item["symbol"],
                        item["line"],
                    ),
                ),
            }
        if import_observations is not None:
            self.last_import_observations = {
                "schema_version": IMPORT_LOCATION_OBSERVATIONS_SCHEMA,
                "observations": sorted(
                    import_observations,
                    key=lambda item: (
                        item["source_path"],
                        item["import_index"],
                        item["module"],
                        item["name"],
                        item["line"],
                    ),
                ),
                "coverage": {
                    "observed": len(import_observations),
                    "emitted": len(import_observations),
                    "omitted": 0,
                    "limit": None,
                    "truncated": False,
                    "limitations": [
                        "static-import-observation-does-not-claim-runtime-completeness"
                    ],
                },
            }
        return inventory
