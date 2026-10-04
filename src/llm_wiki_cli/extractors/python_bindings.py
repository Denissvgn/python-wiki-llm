"""Conservative syntax-only binding facts for captured Python calls."""

from __future__ import annotations

import ast
import builtins
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass

UNKNOWN = {"kind": "unresolved"}
BUILTIN_NAMES = frozenset(dir(builtins))
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
CONSTRUCTOR_FACTS_VERSION = 1
CONSTRUCTOR_DISPATCH_VERSION = "llm-wiki-python-constructor-dispatch/v1"


def _unresolved(node, reason):
    return {
        "kind": "unresolved",
        "reason": reason,
        "line": node.lineno,
        "column": node.col_offset,
    }


def _callee_path(node):
    members = []
    while isinstance(node, ast.Attribute):
        members.append(node.attr)
        node = node.value
    return (node.id, list(reversed(members))) if isinstance(node, ast.Name) else None


def _module_declarations(tree):
    found = []

    def walk(node):
        if isinstance(node, (ast.ClassDef, *FUNCTIONS)):
            found.append(node)
        elif not isinstance(node, (*FUNCTIONS, ast.Lambda)):
            for child in ast.iter_child_nodes(node):
                walk(child)

    walk(tree)
    return found


def _module_classes(tree):
    return [
        node for node in _module_declarations(tree) if isinstance(node, ast.ClassDef)
    ]


def _namespace_statements(body):
    """Walk namespace statements without interpreting nested callable bodies."""
    for node in body:
        yield node
        if not isinstance(node, (ast.ClassDef, *FUNCTIONS, ast.Lambda)):
            yield from _namespace_statements(list(ast.iter_child_nodes(node)))


def _dispatch_facts(tree, module):
    """Qualify only allocation/dispatch syntax actually present in this AST."""
    classes = _module_classes(tree)
    counts = Counter(node.name for node in _module_declarations(tree))
    facts = {}
    for node in classes:
        reasons = set()
        blocked = set()
        if counts[node.name] != 1:
            reasons.add("duplicate-class")
        if node.decorator_list:
            reasons.add("decorated-class")
        if node.keywords:
            reasons.add("custom-class-keywords")
        for base in node.bases:
            if not (
                isinstance(base, ast.Name)
                and _lookup(module, base.id) == {"kind": "builtin", "symbol": "object"}
            ):
                reasons.add("unsupported-inheritance")
        namespace = ast.Module(body=node.body, type_ignores=[])
        methods = [
            child
            for child in _module_declarations(namespace)
            if isinstance(child, FUNCTIONS)
        ]
        for name, count in Counter(
            child.name for child in _module_declarations(namespace)
        ).items():
            if count > 1:
                blocked.add(name)
        for method in methods:
            if method.name in {
                "__new__",
                "__getattribute__",
                "__getattr__",
                "__setattr__",
                "__delattr__",
            }:
                reasons.add("custom-construction-or-dispatch")
            if method.decorator_list:
                blocked.add(method.name)
                if method.name == "__init__":
                    reasons.add("decorated-constructor")
        for child in _namespace_statements(node.body):
            if isinstance(
                child, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete)
            ):
                targets = (
                    child.targets
                    if isinstance(child, (ast.Assign, ast.Delete))
                    else [child.target]
                )
                for target in targets:
                    blocked.update(_target_names(target))
                    if not isinstance(target, (ast.Name, ast.Tuple, ast.List)):
                        reasons.add("dynamic-class-namespace")
        if blocked & {
            "__new__",
            "__init__",
            "__class__",
            "__dict__",
            "__bases__",
            "__getattribute__",
            "__getattr__",
            "__setattr__",
            "__delattr__",
        }:
            reasons.add("custom-construction-or-dispatch")
        if any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id in {"exec", "eval"}
            for child in ast.walk(node)
        ):
            reasons.add("dynamic-class-namespace")
        facts[id(node)] = {
            "schema_version": CONSTRUCTOR_DISPATCH_VERSION,
            "eligible": not reasons,
            "reasons": sorted(reasons),
            "blocked_members": sorted(blocked),
        }
    return facts


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
    classes: dict[int, dict]


class _BindingAnalyzer:
    def __init__(self, tree):
        self.calls: dict[int, dict] = {}
        self.module: dict[str, dict] = {}
        self.class_names = {node.name for node in _module_classes(tree)}
        self.class_mutations: dict[str, set[str]] = {}
        self.import_mutations: list[dict] = []
        self.constructor_barriers: set[str] = set()
        self.module_namespace_invalidations: set[str] = set()
        self.module_scope = False

    def function(self, node, closure: set[str], class_name: str | None = None):
        scope = _scope_names(node.body)
        local = (scope.bound | _parameters(node.args)) - scope.globals
        env = dict(self.module)
        env.update(
            {
                name: {"kind": "unresolved", "reason": "receiver-outside-lexical-scope"}
                for name in closure | local | scope.nonlocals
            }
        )
        for name in scope.globals:
            if (
                name in self.class_names
                or self.module.get(name, {}).get("kind") == "constructed-instance"
            ):
                env[name] = {
                    "kind": "unresolved",
                    "reason": "receiver-outside-lexical-scope",
                }
        positional = [*node.args.posonlyargs, *node.args.args]
        if class_name and positional:
            if not self.static_method(node):
                env[positional[0].arg] = {"kind": "receiver", "symbol": class_name}
        prior_barriers = self.constructor_barriers
        self.constructor_barriers = scope.globals | scope.nonlocals
        self.block(node.body, env, closure | local, capture=True)
        self.constructor_barriers = prior_barriers

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

    def constructor(self, node, env):
        path = _callee_path(node.func)
        if path is None:
            return _unresolved(node, "dynamic-constructor")
        root, members = path
        if root in self.constructor_barriers:
            return _unresolved(node, "receiver-outside-lexical-scope")
        binding = _lookup(env, root)
        if binding.get("kind") not in {"local", "import"}:
            return _unresolved(
                node, binding.get("reason", "constructor-binding-unresolved")
            )
        if binding["kind"] == "local" and (
            members or binding["symbol"] not in self.class_names
        ):
            return _unresolved(node, "constructor-not-class")
        return {
            "kind": "constructed-instance",
            "constructor": {
                "root_binding": dict(binding),
                "members": members,
                "line": node.lineno,
                "column": node.col_offset,
            },
            "blocked_members": [],
        }

    def call_binding(self, node, env):
        func = node.func
        path = _callee_path(func)
        if (
            path
            and path[0] in self.constructor_barriers
            and isinstance(func, ast.Attribute)
        ):
            return _unresolved(node, "receiver-outside-lexical-scope")
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Call):
                instance = self.constructor(func.value, env)
                origin = "direct-construction"
            elif isinstance(func.value, ast.Name):
                instance = _lookup(env, func.value.id)
                origin = "assigned-construction"
            else:
                instance = {}
                origin = "assigned-construction"
            if instance.get("kind") == "constructed-instance":
                if (
                    func.attr in instance["blocked_members"]
                    or "*" in instance["blocked_members"]
                ):
                    return _unresolved(node, "receiver-member-replaced")
                return {
                    "kind": "constructed-receiver",
                    "constructor": deepcopy(instance["constructor"]),
                    "member": func.attr,
                    "receiver_origin": origin,
                }
            if isinstance(func.value, ast.Call):
                return {**instance, "line": node.lineno, "column": node.col_offset}
        path = _callee_path(func)
        if path is None:
            return _unresolved(node, "unsupported-call-target")
        binding = _lookup(env, path[0])
        if binding.get("kind") in {
            "constructed-instance",
            "receiver-namespace",
            "attribute-mutator",
            "module-namespace",
        }:
            return _unresolved(node, "unsupported-instance-call")
        if binding.get("kind") == "unresolved":
            return _unresolved(
                node, binding.get("reason", "receiver-binding-unresolved")
            )
        return dict(binding)

    def helper_path(self, node, env):
        path = _callee_path(node)
        if path is None:
            return None
        root, members = path
        binding = _lookup(env, root)
        if binding.get("kind") == "builtin":
            return [binding["symbol"], *members]
        if binding.get("kind") == "import" and binding.get("module") == "builtins":
            return ([binding["name"]] if binding.get("name") else []) + members
        return None

    def namespace_value(self, node, env):
        if isinstance(node, ast.Call) and not node.args and not node.keywords:
            helper = self.helper_path(node.func, env)
            if helper == ["globals"] or helper == ["locals"] and self.module_scope:
                return {"kind": "module-namespace"}
        target = None
        qualified = False
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "__dict__"
            and isinstance(node.value, ast.Name)
        ):
            target = _lookup(env, node.value.id)
            qualified = True
        elif (
            isinstance(node, ast.Call)
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Name)
        ):
            target = _lookup(env, node.args[0].id)
            qualified = self.helper_path(node.func, env) == ["vars"]
            path = _callee_path(node.func)
            named_vars = path is not None and (
                path[0] == "vars"
                or path[1][-1:] == ["vars"]
                or _lookup(env, path[0]).get("name") == "vars"
            )
            if (
                not qualified
                and not named_vars
                and self.constructor(node, env).get("kind") == "constructed-instance"
            ):
                return None
        if target is not None and (
            target.get("kind") in {"receiver", "constructed-instance", "import"}
            or target.get("kind") == "local"
            and target.get("symbol") in self.class_names
        ):
            return {
                "kind": "receiver-namespace",
                "target": target,
                "qualified": qualified,
            }
        return None

    def mutator_value(self, node, env):
        path = self.helper_path(node, env)
        if path in (
            ["setattr"],
            ["delattr"],
            ["object", "__setattr__"],
            ["object", "__delattr__"],
        ):
            return {"kind": "attribute-mutator", "qualified": True}
        if (
            isinstance(node, ast.Attribute)
            and node.attr in {"__setattr__", "__delattr__"}
            or isinstance(node, ast.Name)
            and node.id in {"setattr", "delattr"}
        ):
            return {"kind": "attribute-mutator", "qualified": False}
        return None

    def invalidate_target(self, binding, env, member="*"):
        if binding.get("kind") == "constructed-instance":
            binding["blocked_members"].append(member)
            if member in {"__class__", "__dict__"}:
                binding["blocked_members"].append("*")
        elif (
            binding.get("kind") in {"local", "receiver"}
            and binding.get("symbol") in self.class_names
        ):
            self.class_mutations.setdefault(binding["symbol"], set()).add(member)
        elif binding.get("kind") == "import":
            self.import_mutations.append(dict(binding))
            for name, value in list(env.items()):
                if value == binding:
                    env[name] = {
                        "kind": "unresolved",
                        "reason": "receiver-member-replaced",
                    }

    def invalidate_members(self, node, env):
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr
                in {
                    "update",
                    "clear",
                    "pop",
                    "popitem",
                    "setdefault",
                    "__setitem__",
                    "__delitem__",
                    "__ior__",
                }
            ):
                namespace = (
                    _lookup(env, child.func.value.id)
                    if isinstance(child.func.value, ast.Name)
                    else self.namespace_value(child.func.value, env)
                )
                if namespace and namespace.get("kind") == "receiver-namespace":
                    self.invalidate_target(namespace["target"], env)
                elif namespace and namespace.get("kind") == "module-namespace":
                    self.module_namespace_invalidations.add("*")
            if isinstance(child, ast.Subscript) and isinstance(
                child.ctx, (ast.Store, ast.Del)
            ):
                namespace = (
                    _lookup(env, child.value.id)
                    if isinstance(child.value, ast.Name)
                    else self.namespace_value(child.value, env)
                )
                if namespace and namespace.get("kind") == "receiver-namespace":
                    member = (
                        child.slice.value
                        if namespace["qualified"]
                        and isinstance(child.slice, ast.Constant)
                        and isinstance(child.slice.value, str)
                        and child.slice.value.isidentifier()
                        else "*"
                    )
                    self.invalidate_target(namespace["target"], env, member)
                elif namespace and namespace.get("kind") == "module-namespace":
                    member = (
                        child.slice.value
                        if isinstance(child.slice, ast.Constant)
                        and isinstance(child.slice.value, str)
                        and child.slice.value.isidentifier()
                        else "*"
                    )
                    self.module_namespace_invalidations.add(member)
            if isinstance(child, ast.Attribute) and isinstance(
                child.ctx, (ast.Store, ast.Del)
            ):
                if isinstance(child.value, ast.Name):
                    self.invalidate_target(
                        _lookup(env, child.value.id), env, child.attr
                    )
                else:
                    path = _callee_path(child)
                    if (
                        path is not None
                        and _lookup(env, path[0]).get("kind") == "import"
                    ):
                        self.invalidate_target(_lookup(env, path[0]), env)
            if (
                isinstance(child, ast.Call)
                and child.args
                and isinstance(child.args[0], ast.Name)
            ):
                mutator = (
                    _lookup(env, child.func.id)
                    if isinstance(child.func, ast.Name)
                    else None
                )
                if not mutator or mutator.get("kind") != "attribute-mutator":
                    mutator = self.mutator_value(child.func, env)
                if mutator:
                    member = (
                        child.args[1].value
                        if mutator["qualified"]
                        and len(child.args) >= 2
                        and isinstance(child.args[1], ast.Constant)
                        and isinstance(child.args[1].value, str)
                        and child.args[1].value.isidentifier()
                        else "*"
                    )
                    self.invalidate_target(_lookup(env, child.args[0].id), env, member)

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
            self.calls[id(node)] = self.call_binding(node, env)
            self.invalidate_members(node, env)
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
        prior_scope = self.module_scope
        self.module_scope = module
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
                if isinstance(value, ast.Call) and not isinstance(
                    statement, ast.AugAssign
                ):
                    binding = self.constructor(value, env)
                if not isinstance(statement, ast.AugAssign):
                    private = self.namespace_value(value, env)
                    if private is None and not (
                        isinstance(value, ast.Name)
                        and binding.get("kind") in {"builtin", "import"}
                    ):
                        private = self.mutator_value(value, env)
                    if private is not None:
                        binding = private
                if isinstance(statement, ast.AugAssign):
                    binding = {"kind": "unresolved", "reason": "receiver-rebound"}
                self.invalidate_members(statement, env)
                for target in targets:
                    for name in _target_names(target):
                        if value is not None or not module:
                            env[name] = (
                                binding if isinstance(target, ast.Name) else UNKNOWN
                            )
            elif isinstance(statement, getattr(ast, "TypeAlias", ())):
                for name in _target_names(statement.name):
                    env[name] = {"kind": "unresolved", "reason": "receiver-rebound"}
            elif isinstance(statement, ast.Delete):
                if capture:
                    self.expression(statement, env, closure)
                for target in statement.targets:
                    env.update(
                        {
                            name: {"kind": "unresolved", "reason": "receiver-rebound"}
                            for name in _target_names(target)
                        }
                    )
                self.invalidate_members(statement, env)
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
                env.update(
                    {
                        name: {"kind": "unresolved", "reason": "receiver-path-conflict"}
                        for name in names
                    }
                )
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

        self.module_scope = prior_scope


def analyze_python_bindings(tree: ast.Module) -> PythonBindings:
    analyzer = _BindingAnalyzer(tree)
    analyzer.block(tree.body, analyzer.module, set(), capture=False, module=True)
    for name in _scope_names(tree.body).bound:
        analyzer.module.setdefault(name, UNKNOWN)
    for node in ast.walk(tree):
        if isinstance(node, FUNCTIONS):
            scope = _scope_names(node.body)
            for name in scope.bound & scope.globals:
                analyzer.module[name] = UNKNOWN
    analyzer.block(tree.body, {}, set(), capture=True, module=True)
    invalidated = analyzer.module_namespace_invalidations
    for name in analyzer.module:
        if "*" in invalidated or name in invalidated:
            analyzer.module[name] = {
                "kind": "unresolved",
                "reason": "module-namespace-rebound",
            }
    constructor_paths = {
        (node.lineno, node.col_offset): _callee_path(node.func)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fact = analyzer.calls.get(id(node), {})
            if fact.get("kind") == "constructed-receiver":
                constructor = fact["constructor"]
                path = constructor_paths.get(
                    (constructor["line"], constructor["column"])
                )
                if "*" in invalidated or path is not None and path[0] in invalidated:
                    analyzer.calls[id(node)] = _unresolved(
                        node, "constructor-binding-rebound"
                    )
                elif any(
                    constructor["root_binding"].get("module") == mutation.get("module")
                    for mutation in analyzer.import_mutations
                ):
                    analyzer.calls[id(node)] = _unresolved(
                        node, "constructor-member-replaced"
                    )
    module = {
        name: dict(value)
        if value.get("kind")
        not in {
            "constructed-instance",
            "receiver-namespace",
            "attribute-mutator",
            "module-namespace",
        }
        else dict(UNKNOWN)
        for name, value in analyzer.module.items()
    }
    classes = _dispatch_facts(tree, analyzer.module)
    for node in _module_classes(tree):
        mutations = analyzer.class_mutations.get(node.name, set())
        classes[id(node)]["blocked_members"] = sorted(
            set(classes[id(node)]["blocked_members"]) | (mutations - {"*"})
        )
        if "*" in mutations:
            classes[id(node)]["eligible"] = False
            classes[id(node)]["reasons"] = sorted(
                set(classes[id(node)]["reasons"]) | {"dynamic-member-mutation"}
            )
        if mutations & {
            "__new__",
            "__init__",
            "__class__",
            "__dict__",
            "__bases__",
            "__getattribute__",
            "__getattr__",
            "__setattr__",
            "__delattr__",
        }:
            classes[id(node)]["eligible"] = False
            classes[id(node)]["reasons"] = sorted(
                set(classes[id(node)]["reasons"]) | {"custom-construction-or-dispatch"}
            )
    return PythonBindings(module, analyzer.calls, classes)


def valid_python_constructor_facts(inventory, *, require_capability=True):
    """Validate published syntax facts without reading or parsing source."""

    def identifier(value):
        return isinstance(value, str) and value.isidentifier()

    def location(value):
        return (
            type(value.get("line")) is int
            and value["line"] > 0
            and type(value.get("column")) is int
            and value["column"] >= 0
        )

    def binding(value, *, root=False):
        if not isinstance(value, dict):
            return False
        kind = value.get("kind")
        if not isinstance(kind, str):
            return False
        if kind in {"local", "builtin", "receiver"}:
            return (
                (not root or kind == "local")
                and set(value) == {"kind", "symbol"}
                and identifier(value["symbol"])
            )
        if kind == "import":
            return (
                set(value)
                in ({"kind", "module", "name"}, {"kind", "module", "name", "modules"})
                and isinstance(value["module"], str)
                and bool(value["module"])
                and isinstance(value["name"], str)
                and (
                    "modules" not in value
                    or isinstance(value["modules"], list)
                    and all(isinstance(item, str) and item for item in value["modules"])
                )
            )
        if kind == "unresolved" and not root:
            return (
                set(value) <= {"kind", "reason", "line", "column"}
                and (
                    "reason" not in value
                    or isinstance(value["reason"], str)
                    and bool(value["reason"])
                )
                and (not ({"line", "column"} & set(value)) or location(value))
            )
        if kind != "constructed-receiver" or root:
            return False
        constructor = value.get("constructor")
        return (
            set(value) == {"kind", "constructor", "member", "receiver_origin"}
            and identifier(value["member"])
            and isinstance(value["receiver_origin"], str)
            and value["receiver_origin"]
            in {"direct-construction", "assigned-construction"}
            and isinstance(constructor, dict)
            and set(constructor) == {"root_binding", "members", "line", "column"}
            and binding(constructor["root_binding"], root=True)
            and isinstance(constructor["members"], list)
            and all(identifier(item) for item in constructor["members"])
            and location(constructor)
        )

    def aligned(value, calls_key="calls", facts_key="call_bindings"):
        if not isinstance(value, dict):
            return False
        calls = value.get(calls_key, [])
        facts = value.get(facts_key, [])
        return (
            isinstance(calls, list)
            and isinstance(facts, list)
            and len(calls) == len(facts)
            and all(binding(item) for item in facts)
            and all(
                isinstance(call, dict)
                and isinstance(call.get("name"), str)
                and type(call.get("line")) is int
                and call["line"] > 0
                and ("column" not in call or type(call["column"]) is int and call["column"] >= 0)
                and (
                    fact["kind"] != "constructed-receiver"
                    or fact["member"] == call["name"]
                )
                for call, fact in zip(calls, facts)
            )
        )

    if not isinstance(inventory, dict):
        return False
    if not inventory:
        return True
    marker = inventory.get("python_constructor_facts_version")
    if marker is None and not require_capability:
        return True
    if type(marker) is not int or marker != CONSTRUCTOR_FACTS_VERSION:
        return False
    module = inventory.get("python_bindings")
    if not isinstance(module, dict) or not all(
        (identifier(name) or name == "*")
        and binding(value)
        and value["kind"] != "constructed-receiver"
        for name, value in module.items()
    ):
        return False
    if not aligned(inventory, "main_block_calls", "main_block_call_bindings"):
        return False
    for field in ("functions", "nested_functions"):
        values = inventory.get(field, [])
        if not isinstance(values, list) or not all(aligned(value) for value in values):
            return False
    classes = inventory.get("classes", [])
    if not isinstance(classes, list):
        return False
    for cls in classes:
        if not isinstance(cls, dict):
            return False
        if cls.get("kind") == "type_alias":
            if (
                "python_constructor_dispatch" in cls
                or cls.get("methods")
                or not identifier(cls.get("name"))
                or not isinstance(cls.get("target"), str)
                or not cls["target"]
                or type(cls.get("line")) is not int
                or cls["line"] < 1
                or any(
                    cls.get(field) for field in ("bases", "decorators", "attributes")
                )
            ):
                return False
            continue
        dispatch = cls.get("python_constructor_dispatch")
        if not isinstance(dispatch, dict) or set(dispatch) != {
            "schema_version",
            "eligible",
            "reasons",
            "blocked_members",
        }:
            return False
        if (
            dispatch["schema_version"] != CONSTRUCTOR_DISPATCH_VERSION
            or type(dispatch["eligible"]) is not bool
        ):
            return False
        if (
            not isinstance(dispatch["reasons"], list)
            or not all(
                isinstance(reason, str) and reason for reason in dispatch["reasons"]
            )
            or dispatch["eligible"] != (not dispatch["reasons"])
        ):
            return False
        if not isinstance(dispatch["blocked_members"], list) or not all(
            identifier(member) for member in dispatch["blocked_members"]
        ):
            return False
        methods = cls.get("methods", [])
        if not isinstance(methods, list) or not all(
            aligned(value) for value in methods
        ):
            return False
    return True
