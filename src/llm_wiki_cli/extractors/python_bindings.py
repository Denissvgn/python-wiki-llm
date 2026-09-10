"""Conservative syntax-only binding facts for captured Python calls."""

from __future__ import annotations

import ast
import builtins
from dataclasses import dataclass

UNKNOWN = {"kind": "unresolved"}
BUILTIN_NAMES = frozenset(dir(builtins))
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def _lookup(env: dict, name: str) -> dict:
    if name in env:
        return env[name]
    if "*" not in env and name in BUILTIN_NAMES:
        return {"kind": "builtin", "symbol": name}
    return UNKNOWN


def _target_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Name):
        return {node.id}
    if isinstance(node, (ast.Tuple, ast.List)):
        return set().union(*(_target_names(item) for item in node.elts))
    if isinstance(node, ast.Starred):
        return _target_names(node.value)
    return set()


class _ScopeNames(ast.NodeVisitor):
    def __init__(self):
        self.bound: set[str] = set()
        self.globals: set[str] = set()
        self.nonlocals: set[str] = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.bound.add(node.id)

    def visit_FunctionDef(self, node):
        self.bound.add(node.name)

    def visit_AsyncFunctionDef(self, node):
        self.bound.add(node.name)

    def visit_ClassDef(self, node):
        self.bound.add(node.name)

    def visit_Lambda(self, node):
        pass

    def visit_Import(self, node):
        self.bound.update(
            alias.asname or alias.name.split(".")[0] for alias in node.names
        )

    def visit_ImportFrom(self, node):
        self.bound.update(alias.asname or alias.name for alias in node.names)

    def visit_Global(self, node):
        self.globals.update(node.names)

    def visit_Nonlocal(self, node):
        self.nonlocals.update(node.names)

    def visit_MatchAs(self, node):
        if node.name:
            self.bound.add(node.name)
        self.generic_visit(node)

    def visit_MatchStar(self, node):
        if node.name:
            self.bound.add(node.name)

    def visit_MatchMapping(self, node):
        if node.rest:
            self.bound.add(node.rest)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.name:
            self.bound.add(node.name)
        self.generic_visit(node)

    def _comprehension(self, node: ast.AST):
        # Iteration targets belong to the comprehension; walrus targets bind
        # in its containing scope. No inspected expression is evaluated.
        for child in ast.walk(node):
            if isinstance(child, ast.NamedExpr):
                self.bound.update(_target_names(child.target))

    def visit_ListComp(self, node):
        self._comprehension(node)

    def visit_SetComp(self, node):
        self._comprehension(node)

    def visit_DictComp(self, node):
        self._comprehension(node)

    def visit_GeneratorExp(self, node):
        self._comprehension(node)


def _scope_names(body: list[ast.stmt]) -> _ScopeNames:
    scope = _ScopeNames()
    for statement in body:
        scope.visit(statement)
    return scope


def _parameters(args: ast.arguments) -> set[str]:
    return {arg.arg for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs)} | {
        arg.arg for arg in (args.vararg, args.kwarg) if arg is not None
    }


def import_bindings(node: ast.Import | ast.ImportFrom) -> dict[str, dict]:
    if isinstance(node, ast.ImportFrom):
        module = "." * node.level + (node.module or "")
        return {
            alias.asname or alias.name: {
                "kind": "import",
                "module": module,
                "name": alias.name,
            }
            for alias in node.names
        }
    return {
        alias.asname or alias.name.split(".")[0]: {
            "kind": "import",
            "module": alias.name if alias.asname else alias.name.split(".")[0],
            "name": "",
            "modules": [alias.name],
        }
        for alias in node.names
    }


@dataclass(frozen=True)
class PythonBindings:
    module: dict[str, dict]
    calls: dict[int, dict]


class _BindingAnalyzer:
    def __init__(self):
        self.calls: dict[int, dict] = {}
        self.module: dict[str, dict] = {}

    def function(self, node, closure: set[str], class_name: str | None = None):
        scope = _scope_names(node.body)
        local = (scope.bound | _parameters(node.args)) - scope.globals
        env = dict(self.module)
        env.update({name: UNKNOWN for name in closure | local | scope.nonlocals})
        positional = [*node.args.posonlyargs, *node.args.args]
        if class_name and positional and positional[0].arg in {"self", "cls"}:
            if not self.static_method(node):
                env[positional[0].arg] = {"kind": "receiver", "symbol": class_name}
        self.block(node.body, env, closure | local, capture=True)

    def static_method(self, node) -> bool:
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                binding = _lookup(self.module, decorator.id)
                if (
                    binding.get("symbol") == "staticmethod"
                    and binding.get("kind") == "builtin"
                ):
                    return True
                if (
                    binding.get("module") == "builtins"
                    and binding.get("name") == "staticmethod"
                ):
                    return True
            elif isinstance(decorator, ast.Attribute) and isinstance(
                decorator.value, ast.Name
            ):
                binding = _lookup(self.module, decorator.value.id)
                if (
                    decorator.attr == "staticmethod"
                    and binding.get("module") == "builtins"
                ):
                    return True
        return False

    def expression(self, node, env: dict, closure: set[str]):
        if isinstance(node, ast.Lambda):
            nested = dict(env)
            nested.update({name: UNKNOWN for name in closure | _parameters(node.args)})
            self.expression(node.body, nested, closure | _parameters(node.args))
            return
        if isinstance(node, COMPREHENSIONS):
            nested = dict(env)
            bound = set(closure)
            for generator in node.generators:
                self.expression(generator.iter, nested, bound)
                names = _target_names(generator.target)
                bound.update(names)
                nested.update({name: UNKNOWN for name in names})
                for condition in generator.ifs:
                    self.expression(condition, nested, bound)
            for value in (
                [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
            ):
                self.expression(value, nested, bound)
            return
        if isinstance(node, ast.Call):
            root = node.func
            while isinstance(root, ast.Attribute):
                root = root.value
            self.calls[id(node)] = (
                dict(_lookup(env, root.id))
                if isinstance(root, ast.Name)
                else dict(UNKNOWN)
            )
        if isinstance(node, ast.NamedExpr):
            self.expression(node.value, env, closure)
            for name in _target_names(node.target):
                env[name] = (
                    _lookup(env, node.value.id)
                    if isinstance(node.value, ast.Name)
                    else UNKNOWN
                )
            return
        for child in ast.iter_child_nodes(node):
            self.expression(child, env, closure)

    def block(
        self, body, env: dict, closure: set[str], *, capture: bool, module: bool = False
    ):
        for statement in body:
            if isinstance(statement, FUNCTIONS):
                if capture:
                    self.function(statement, set() if module else closure)
                env[statement.name] = (
                    {"kind": "local", "symbol": statement.name} if module else UNKNOWN
                )
            elif isinstance(statement, ast.ClassDef):
                if capture:
                    for child in statement.body:
                        if isinstance(child, FUNCTIONS):
                            self.function(
                                child, set() if module else closure, statement.name
                            )
                env[statement.name] = (
                    {"kind": "local", "symbol": statement.name} if module else UNKNOWN
                )
            elif isinstance(statement, (ast.Import, ast.ImportFrom)):
                for name, binding in import_bindings(statement).items():
                    if name == "*":
                        env.update({key: UNKNOWN for key in env})
                    prior = env.get(name, {})
                    if (
                        binding.get("modules")
                        and prior.get("module") == binding["module"]
                        and not prior.get("name")
                    ):
                        binding["modules"] = sorted(
                            set(prior.get("modules", [])) | set(binding["modules"])
                        )
                    env[name] = binding
            elif isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                value = statement.value
                if capture and value is not None:
                    self.expression(value, env, closure)
                targets = (
                    statement.targets
                    if isinstance(statement, ast.Assign)
                    else [statement.target]
                )
                binding = (
                    _lookup(env, value.id) if isinstance(value, ast.Name) else UNKNOWN
                )
                for target in targets:
                    for name in _target_names(target):
                        if value is not None or not module:
                            env[name] = (
                                binding if isinstance(target, ast.Name) else UNKNOWN
                            )
            elif isinstance(statement, ast.Delete):
                if capture:
                    self.expression(statement, env, closure)
                for target in statement.targets:
                    env.update({name: UNKNOWN for name in _target_names(target)})
            elif isinstance(
                statement,
                (
                    ast.If,
                    ast.For,
                    ast.AsyncFor,
                    ast.While,
                    ast.Try,
                    getattr(ast, "TryStar", ast.Try),
                ),
            ):
                if capture:
                    for field in ("test", "iter"):
                        value = getattr(statement, field, None)
                        if value is not None:
                            self.expression(value, env, closure)
                branches = [(statement.body, None), (statement.orelse, None)]
                if isinstance(statement, (ast.Try, getattr(ast, "TryStar", ast.Try))):
                    branches.extend(
                        (handler.body, handler.name) for handler in statement.handlers
                    )
                    branches.append((statement.finalbody, None))
                for branch, exception_name in branches:
                    branch_env = dict(env)
                    if exception_name:
                        branch_env[exception_name] = UNKNOWN
                    if isinstance(statement, (ast.For, ast.AsyncFor)):
                        branch_env.update(
                            {name: UNKNOWN for name in _target_names(statement.target)}
                        )
                    self.block(
                        branch, branch_env, closure, capture=capture, module=module
                    )
                names = _scope_names([statement]).bound
                if "*" in names:
                    env.update({name: UNKNOWN for name in env})
                env.update({name: UNKNOWN for name in names})
            elif isinstance(statement, getattr(ast, "Match", ())):
                if capture:
                    self.expression(statement.subject, env, closure)
                for case in statement.cases:
                    names = _ScopeNames()
                    names.visit(case.pattern)
                    branch_env = {**env, **{name: UNKNOWN for name in names.bound}}
                    if capture and case.guard is not None:
                        self.expression(case.guard, branch_env, closure)
                    self.block(
                        case.body, branch_env, closure, capture=capture, module=module
                    )
                env.update({name: UNKNOWN for name in _scope_names([statement]).bound})
            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                for item in statement.items:
                    if capture:
                        self.expression(item.context_expr, env, closure)
                    if item.optional_vars:
                        env.update(
                            {
                                name: UNKNOWN
                                for name in _target_names(item.optional_vars)
                            }
                        )
                self.block(statement.body, env, closure, capture=capture, module=module)
            elif capture:
                self.expression(statement, env, closure)


def analyze_python_bindings(tree: ast.Module) -> PythonBindings:
    analyzer = _BindingAnalyzer()
    analyzer.block(tree.body, analyzer.module, set(), capture=False, module=True)
    for name in _scope_names(tree.body).bound:
        analyzer.module.setdefault(name, UNKNOWN)
    for node in ast.walk(tree):
        if isinstance(node, FUNCTIONS):
            scope = _scope_names(node.body)
            for name in scope.bound & scope.globals:
                analyzer.module[name] = UNKNOWN
    analyzer.block(tree.body, {}, set(), capture=True, module=True)
    return PythonBindings(analyzer.module, analyzer.calls)
