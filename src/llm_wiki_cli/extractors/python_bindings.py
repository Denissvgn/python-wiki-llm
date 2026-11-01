"""Conservative syntax-only binding facts for captured Python calls."""

from __future__ import annotations

import ast
import builtins
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field as dataclass_field
import sys
from typing import Any

UNKNOWN = {"kind": "unresolved"}
BUILTIN_NAMES = frozenset(dir(builtins))
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
_NAMESPACE_MUTATORS = frozenset(
    {
        "update",
        "clear",
        "pop",
        "popitem",
        "setdefault",
        "__setitem__",
        "__delitem__",
        "__ior__",
    }
)
CONSTRUCTOR_FACTS_VERSION = 1
CONSTRUCTOR_DISPATCH_VERSION = "llm-wiki-python-constructor-dispatch/v1"
_DISPATCH_SLOTS = frozenset(
    {
        "__new__",
        "__init__",
        "__class__",
        "__dict__",
        "__bases__",
        "__getattribute__",
        "__getattr__",
        "__setattr__",
        "__delattr__",
    }
)


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


def _builtin_getter(binding):
    return (
        binding.get("kind") == "builtin"
        and binding.get("symbol") == "getattr"
        or binding.get("kind") == "import"
        and binding.get("module") == "builtins"
        and binding.get("name") == "getattr"
    )


def _builtin_dict(binding):
    return (
        binding.get("kind") == "builtin"
        and binding.get("symbol") == "dict"
        or binding.get("kind") == "import"
        and binding.get("module") == "builtins"
        and binding.get("name") == "dict"
    )


def _builtin_namespace_factory(binding):
    symbol = (
        binding.get("symbol")
        if binding.get("kind") == "builtin"
        else binding.get("name")
        if binding.get("kind") == "import" and binding.get("module") == "builtins"
        else None
    )
    return symbol if symbol in {"vars", "locals", "globals"} else None


def _builtin_attribute_mutator(binding):
    symbol = (
        binding.get("symbol")
        if binding.get("kind") == "builtin"
        else binding.get("name")
        if binding.get("kind") == "import" and binding.get("module") == "builtins"
        else None
    )
    return (
        {"kind": "attribute-mutator", "qualified": True}
        if symbol in {"setattr", "delattr"}
        else None
    )


def _known_callable(binding):
    if binding.get("kind") in {
        "namespace-mutator",
        "attribute-mutator",
        "namespace-factory",
        "namespace-getter",
        "non-namespace-factory",
    }:
        return True
    if (
        _builtin_getter(binding)
        or _builtin_namespace_factory(binding)
        or _builtin_attribute_mutator(binding)
    ):
        return True
    return any(
        _known_callable(value)
        for value in binding.get("_possible_targets", [])
        + binding.get("possible_namespace_mutators", [])
        + binding.get("possible_namespace_getters", [])
    )


def _dict_namespace(target, *, qualified=True):
    if target.get("kind") in {
        "constructed-instance",
        "receiver",
        "import",
        "local",
    } or target.get("_possible_targets"):
        return {"kind": "receiver-namespace", "target": target, "qualified": qualified}
    return None


def _namespace_lookup(target, member):
    if isinstance(member, ast.Constant):
        return _dict_namespace(target) if member.value == "__dict__" else None
    return _dict_namespace(target, qualified=False)


def _getter_method(node):
    # Unknown namespace attributes may be mutators. Retrieval is harmless;
    # only invoking the captured result applies this possible-owner effect.
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if node.value in _NAMESPACE_MUTATORS:
            return node.value
        if node.value in {
            "get",
            "copy",
            "keys",
            "values",
            "items",
            "__getitem__",
            "__len__",
            "__iter__",
            "__contains__",
            "__reversed__",
        }:
            return None
    return "*"


def _namespace_mutated_names(method, args, keywords, qualified):
    names: set[str] | None = None
    if qualified:
        if (
            method in {"pop", "setdefault", "__setitem__", "__delitem__"}
            and args
            and isinstance(args[0], ast.Constant)
            and isinstance(args[0].value, str)
        ):
            names = {args[0].value}
        elif method == "update" and len(args) <= 1:
            if not args:
                names = set()
            elif isinstance(args[0], ast.Dict) and all(
                isinstance(key, ast.Constant) and isinstance(key.value, str)
                for key in args[0].keys
            ):
                names = {
                    key.value
                    for key in args[0].keys
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)
                }
            if names is not None and all(
                keyword.arg is not None for keyword in keywords
            ):
                names.update(
                    keyword.arg for keyword in keywords if keyword.arg is not None
                )
            else:
                names = None
    return names


class _ClassNamespaceEffects(ast.NodeVisitor):
    """Collect executed namespace effects, retaining explicit scope boundaries."""

    def __init__(self, node, module, *, annotations_eager, side_effects=None):
        scope = _scope_names(node.body)
        self.redirected = scope.globals | scope.nonlocals
        self.global_names = scope.globals
        self.writes: set[str] = set()
        self.missing: set[str] = set()
        self.global_writes: set[str] = set()
        self.outer_writes: set[str] = set()
        self.dynamic = False
        self.direct_mapping_writes: set[str] = set()
        self.env = dict(module)
        self.module = module
        self.side_effects = side_effects
        self.namespace_aliases: set[str] = set()
        self.namespace_factories: set[str] = set()
        self.binding_history: dict[str, list[dict]] = {}
        self.annotations_eager = annotations_eager
        self.conditional = False
        self.in_comprehension = False
        for statement in node.body:
            self.visit(statement)

    def _store(self, name, binding=None):
        if name in self.redirected:
            self.outer_writes.add(name)
            if name in self.global_names:
                self.global_writes.add(name)
        else:
            self.writes.add(name)
        if binding and binding.get("kind") == "class-namespace":
            self.namespace_aliases.add(name)
        if binding == {"kind": "builtin", "symbol": "locals"}:
            self.namespace_factories.add(name)
        self.env[name] = binding if binding is not None else UNKNOWN
        self.binding_history.setdefault(name, []).append(self.env[name])

    def _helper(self, node):
        path = _callee_path(node)
        if path is None:
            return None
        root, members = path
        binding = _lookup(self.env, root)
        if binding.get("kind") == "builtin":
            return [binding["symbol"], *members]
        if binding.get("kind") == "import" and binding.get("module") == "builtins":
            return ([binding["name"]] if binding.get("name") else []) + members
        return None

    def _namespace(self, node):
        if isinstance(node, ast.Name):
            value = _lookup(self.env, node.id)
            return (
                value
                if value.get("kind")
                in {
                    "class-namespace",
                    "module-namespace",
                    "uncertain-namespace",
                    "comprehension-namespace",
                    "receiver-namespace",
                }
                else None
            )
        if isinstance(node, ast.Call) and not node.args and not node.keywords:
            if isinstance(node.func, ast.Name):
                binding = _lookup(self.env, node.func.id)
                if binding.get("kind") == "namespace-factory":
                    return {
                        "kind": "uncertain-namespace",
                        "qualified": binding.get("qualified", False),
                        "scopes": binding["scopes"],
                    }
            if self._helper(node.func) == ["globals"]:
                return {"kind": "module-namespace", "qualified": True}
            if self._helper(node.func) in (["locals"], ["vars"]):
                return {
                    "kind": "comprehension-namespace"
                    if self.in_comprehension
                    else "class-namespace",
                    "qualified": True,
                }
            path = _callee_path(node.func)
            if path and (
                path[0] in self.namespace_factories
                or path[0] == "locals"
                or path[1][-1:] == ["locals"]
            ):
                return {"kind": "class-namespace", "qualified": False}
        return None

    def _value(self, node):
        namespace = self._namespace(node)
        if namespace is not None:
            return namespace
        if isinstance(node, ast.Name):
            return _lookup(self.env, node.id)
        if isinstance(node, ast.Attribute) and node.attr in _NAMESPACE_MUTATORS:
            owner = self._namespace(node.value)
            if owner is not None:
                return {
                    "kind": "namespace-mutator",
                    "namespace": owner,
                    "method": node.attr,
                }
        if isinstance(node, (ast.IfExp, ast.BoolOp)):
            values = [
                self._value(value)
                for value in (
                    [node.body, node.orelse]
                    if isinstance(node, ast.IfExp)
                    else node.values
                )
            ]
            if any(
                value.get("kind") in {"namespace-mutator", "namespace-getter"}
                or value.get("possible_namespace_mutators")
                or value.get("possible_namespace_getters")
                or _builtin_getter(value)
                or "getattr" in value.get("possible_helpers", [])
                for value in values
            ):
                return self._join_binding(values)
            # Conditional expression transfer is handled by the next binding
            # stage. Namespace factories here must not gain unique authority.
            return {
                "kind": "namespace-factory",
                "scopes": ["class", "module"],
                "qualified": False,
            }
        if (
            isinstance(node, ast.Lambda)
            and isinstance(node.body, ast.Dict)
            and not node.body.keys
        ):
            return {"kind": "non-namespace-factory"}
        if isinstance(node, ast.Dict) and not node.keys:
            return {"kind": "non-namespace"}
        helper = self._helper(node)
        if helper == ["object", "__getattribute__"]:
            return {"kind": "namespace-getter"}
        if isinstance(node, ast.Attribute) and node.attr == "__getattribute__":
            target = self._value(node.value)
            if _dict_namespace(target):
                return {"kind": "namespace-getter", "target": target}
        if (
            helper
            and len(helper) == 2
            and helper[0] == "dict"
            and helper[1] in _NAMESPACE_MUTATORS
        ):
            return {"kind": "namespace-mutator", "method": helper[1]}
        return (
            {"kind": "builtin", "symbol": helper[0]}
            if helper and len(helper) == 1
            else UNKNOWN
        )

    def _target(self, node, binding=None, *, captured_namespace=None, evaluated=False):
        if isinstance(node, ast.Name):
            self._store(node.id, binding)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for child in node.elts:
                self._target(child)
        elif isinstance(node, ast.Starred):
            self._target(node.value)
        elif isinstance(node, ast.Subscript):
            namespace = (
                captured_namespace[0]
                if captured_namespace is not None
                else self._namespace(node.value)
            )
            if namespace and namespace["kind"] == "receiver-namespace":
                if not evaluated:
                    self.visit(node.value)
                    self.visit(node.slice)
                if self.side_effects:
                    self.side_effects(node, self.env, store_owner=namespace)
                return
            if namespace and namespace["kind"] == "comprehension-namespace":
                if not evaluated:
                    self.visit(node.value)
                    self.visit(node.slice)
                return
            if namespace and namespace["kind"] == "uncertain-namespace":
                if (
                    namespace["qualified"]
                    and isinstance(node.slice, ast.Constant)
                    and isinstance(node.slice.value, str)
                ):
                    if "class" in namespace["scopes"]:
                        self.writes.add(node.slice.value)
                        self.direct_mapping_writes.add(node.slice.value)
                    if "module" in namespace["scopes"]:
                        self.global_writes.add(node.slice.value)
                else:
                    self.dynamic |= "class" in namespace["scopes"]
                    if "module" in namespace["scopes"]:
                        self.global_writes.add("*")
                if not evaluated:
                    self.visit(node.value)
                    self.visit(node.slice)
                return
            if namespace is None and self.side_effects:
                self.side_effects(node, self.env)
            if namespace and namespace["kind"] == "module-namespace":
                if (
                    namespace["qualified"]
                    and isinstance(node.slice, ast.Constant)
                    and isinstance(node.slice.value, str)
                ):
                    self.global_writes.add(node.slice.value)
                else:
                    self.global_writes.add("*")
                if not evaluated:
                    self.visit(node.value)
                    self.visit(node.slice)
                return
            if (
                namespace
                and namespace["qualified"]
                and isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, str)
            ):
                self.writes.add(node.slice.value)
                if isinstance(node.value, ast.Call):
                    self.direct_mapping_writes.add(node.slice.value)
            else:
                self.dynamic = True
            if not evaluated:
                self.visit(node.value)
                self.visit(node.slice)
        else:
            path = _callee_path(node)
            if path and _lookup(self.env, path[0]).get("kind") in {
                "local",
                "import",
                "builtin",
                "receiver",
                "constructed-instance",
            }:
                if self.side_effects:
                    self.side_effects(node, self.env)
            else:
                self.dynamic = True
            self.visit(node)

    def visit_Assign(self, node):
        evaluated = self.visit(node.value)
        value = evaluated if isinstance(evaluated, dict) else self._value(node.value)
        for target in node.targets:
            self._target(target, value)

    def visit_AnnAssign(self, node):
        if node.value is not None:
            evaluated = self.visit(node.value)
            self._target(
                node.target,
                evaluated if isinstance(evaluated, dict) else self._value(node.value),
            )
        if self.annotations_eager:
            self.visit(node.annotation)

    def visit_AugAssign(self, node):
        if isinstance(node.target, ast.Subscript):
            self.visit(node.target.value)
            captured = (self._namespace(node.target.value),)
            self.visit(node.target.slice)
            self.visit(node.value)
            self._target(node.target, captured_namespace=captured, evaluated=True)
        else:
            self.visit(node.value)
            self._target(node.target)

    def visit_Delete(self, node):
        for target in node.targets:
            self._target(target)
            for name in _target_names(target):
                if name in self.redirected:
                    self.env.pop(name, None)
                else:
                    self.env[name] = _lookup(self.module, name)

    def visit_NamedExpr(self, node):
        evaluated = self.visit(node.value)
        value = evaluated if isinstance(evaluated, dict) else self._value(node.value)
        self._target(node.target, value)
        return value

    def _header(self, node):
        for value in node.decorator_list:
            self.visit(value)
        if isinstance(node, ast.ClassDef):
            for value in [*node.bases, *(keyword.value for keyword in node.keywords)]:
                self.visit(value)
        else:
            for value in [
                *node.args.defaults,
                *(value for value in node.args.kw_defaults if value is not None),
            ]:
                self.visit(value)
            if self.annotations_eager:
                for value in _definition_expressions(node)[
                    len(node.decorator_list)
                    + len(node.args.defaults)
                    + sum(value is not None for value in node.args.kw_defaults) :
                ]:
                    self.visit(value)

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        self._header(node)
        if node.name in self.redirected:
            self.missing.add(node.name)
            self._store(node.name)
        else:
            if self.conditional:
                self.writes.add(node.name)
            self.env[node.name] = UNKNOWN

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        self._header(node)
        self._store(node.name)
        inner = _ClassNamespaceEffects(
            node,
            self.module,
            annotations_eager=self.annotations_eager,
            side_effects=self.side_effects,
        )
        # Inner local stores do not leak; explicit global writes do execute.
        self.global_writes.update(inner.global_writes)
        self.outer_writes.update(inner.outer_writes)

    def visit_Lambda(self, node):
        for value in [
            *node.args.defaults,
            *(value for value in node.args.kw_defaults if value is not None),
        ]:
            self.visit(value)

    def visit_Import(self, node: ast.Import | ast.ImportFrom):
        for name, binding in import_bindings(node).items():
            self._store(name, binding)

    def visit_ImportFrom(self, node):
        self.visit_Import(node)

    def visit_For(self, node: ast.For | ast.AsyncFor):
        self.visit(node.iter)
        self._target(node.target)
        self._branches([node.body, node.orelse])

    def visit_AsyncFor(self, node):
        self.visit_For(node)

    def visit_With(self, node: ast.With | ast.AsyncWith):
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars:
                self._target(item.optional_vars)
        for statement in node.body:
            self.visit(statement)

    def visit_AsyncWith(self, node):
        self.visit_With(node)

    def visit_ExceptHandler(self, node):
        if node.type:
            self.visit(node.type)
        if node.name:
            self._store(node.name)
        self._branches([node.body])
        if node.name:
            self._store(node.name)  # Python implicitly deletes the alias.
            if node.name in self.redirected:
                self.env.pop(node.name, None)
            else:
                self.env[node.name] = _lookup(self.module, node.name)

    def visit_MatchAs(self, node):
        if node.name:
            self._store(node.name)
        if node.pattern:
            self.visit(node.pattern)

    def visit_MatchStar(self, node):
        if node.name:
            self._store(node.name)

    def visit_MatchMapping(self, node):
        if node.rest:
            self._store(node.rest)
        self.generic_visit(node)

    def _branches(self, branches):
        previous = self.conditional
        base = dict(self.env)
        exits = []
        self.conditional = True
        for body in branches:
            self.env = dict(base)
            for statement in body:
                self.visit(statement)
            exits.append(dict(self.env))
        self.env = dict(base)
        for name in set().union(*(set(exit) for exit in exits)):
            values = [_lookup(exit, name) for exit in exits]
            self.env[name] = self._join_binding(values)
        self.conditional = previous

    @staticmethod
    def _join_binding(values):
        if all(value == values[0] for value in values):
            return values[0]
        receivers = [
            value for value in values if value.get("kind") == "receiver-namespace"
        ]
        if receivers:
            return {
                "kind": "receiver-namespace",
                "target": {
                    "kind": "unresolved",
                    "_possible_targets": [value["target"] for value in receivers],
                },
                "qualified": all(value.get("qualified", False) for value in receivers),
            }
        getters = [
            effect
            for value in values
            for effect in (
                [value]
                if value.get("kind") == "namespace-getter"
                else value.get("possible_namespace_getters", [])
            )
        ]
        if getters:
            return {"kind": "unresolved", "possible_namespace_getters": getters}
        mutators = [
            effect
            for value in values
            for effect in (
                [value]
                if value.get("kind") == "namespace-mutator"
                else value.get("possible_namespace_mutators", [])
            )
        ]
        if mutators:
            return {"kind": "unresolved", "possible_namespace_mutators": mutators}
        factories = set()
        namespaces = set()
        helpers = set()
        for value in values:
            kind = value.get("kind")
            helper = (
                value.get("symbol")
                if kind == "builtin"
                else value.get("name")
                if kind == "import" and value.get("module") == "builtins"
                else None
            )
            if helper:
                helpers.add(helper)
            helpers.update(value.get("possible_helpers", []))
            if helper in {"locals", "vars", "globals"}:
                factories.add("module" if helper == "globals" else "class")
            if kind == "namespace-factory":
                factories.update(value["scopes"])
            if kind in {"class-namespace", "module-namespace"}:
                namespaces.add("class" if kind == "class-namespace" else "module")
            if kind == "uncertain-namespace":
                namespaces.update(value["scopes"])
        if factories:
            qualified = all(
                (
                    value.get("kind") == "builtin"
                    and value.get("symbol") in {"locals", "vars", "globals"}
                )
                or (
                    value.get("kind") == "import"
                    and value.get("module") == "builtins"
                    and value.get("name") in {"locals", "vars", "globals"}
                )
                or (
                    value.get("kind") == "namespace-factory"
                    and value.get("qualified", False)
                )
                for value in values
            )
            if any(
                value.get("kind")
                not in {"builtin", "namespace-factory", "non-namespace-factory"}
                and not (
                    value.get("kind") == "import" and value.get("module") == "builtins"
                )
                for value in values
            ):
                factories.update({"class", "module"})
            return {
                "kind": "namespace-factory",
                "scopes": sorted(factories),
                "qualified": qualified,
            }
        if namespaces:
            return {
                "kind": "uncertain-namespace",
                "qualified": False,
                "scopes": sorted(namespaces),
            }
        if helpers & {"setattr", "delattr"}:
            return {"kind": "attribute-mutator", "qualified": False}
        return {"kind": "unresolved", "possible_helpers": sorted(helpers)}

    def visit_If(self, node: ast.If | ast.While):
        self.visit(node.test)
        self._branches([node.body, node.orelse])

    def visit_While(self, node):
        self.visit_If(node)

    def visit_Try(self, node: ast.Try | ast.TryStar) -> None:
        base = dict(self.env)
        start = {name: len(values) for name, values in self.binding_history.items()}
        self._branches([node.body, node.orelse, node.finalbody])
        self._retain_prefix_bindings(base, start)
        handler_base = dict(self.env)
        exits = [dict(self.env)]
        for handler in node.handlers:
            self.env = dict(handler_base)
            self.visit(handler)
            exits.append(dict(self.env))
        self.env = {
            name: self._join_binding([_lookup(exit, name) for exit in exits])
            for name in set().union(*(set(exit) for exit in exits))
        }

    def _retain_prefix_bindings(self, base, start):
        for name, values in self.binding_history.items():
            changed = values[start.get(name, 0) :]
            if changed:
                self.env[name] = self._join_binding(
                    [_lookup(base, name), _lookup(self.env, name), *changed]
                )

    def visit_TryStar(self, node: ast.TryStar) -> None:
        self.visit_Try(node)

    def visit_Match(self, node):
        self.visit(node.subject)
        base = dict(self.env)
        exits = [dict(base)]
        for case in node.cases:
            self.env = dict(base)
            self.visit(case.pattern)
            if case.guard:
                self.visit(case.guard)
            self._branches([case.body])
            exits.append(dict(self.env))
        self.env = {
            name: self._join_binding([_lookup(exit, name) for exit in exits])
            for name in set().union(*(set(exit) for exit in exits))
        }

    def visit_TypeAlias(self, node):
        self._target(node.name)  # The RHS/annotation scope is lazy.

    def _comprehension(self, node):
        if not node.generators:
            return
        self.visit(node.generators[0].iter)
        if isinstance(node, ast.GeneratorExp):
            return  # Only the outer iterable executes at generator creation.
        parent = self.env
        previous_comprehension = self.in_comprehension
        self.in_comprehension = True
        # Comprehension bodies skip class lexical bindings. Explicit global
        # aliases already stored in the class body remain visible there.
        self.env = dict(self.module)
        self.env.update(
            {name: parent[name] for name in self.global_names if name in parent}
        )
        try:
            for index, generator in enumerate(node.generators):
                if index:
                    self.visit(generator.iter)
                self.env.update(
                    {name: UNKNOWN for name in _target_names(generator.target)}
                )
                for condition in generator.ifs:
                    self.visit(condition)
            for value in (
                [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
            ):
                self.visit(value)
        finally:
            self.env = parent
            self.in_comprehension = previous_comprehension

    visit_ListComp = _comprehension
    visit_SetComp = _comprehension
    visit_DictComp = _comprehension
    visit_GeneratorExp = _comprehension

    def visit_Attribute(self, node):
        evaluated = self.visit(node.value)
        owner = evaluated if isinstance(evaluated, dict) else self._value(node.value)
        if node.attr == "__call__" and _known_callable(owner):
            return owner
        return self._value(node)

    def visit_Call(self, node):
        helper = self._helper(node.func)
        path = _callee_path(node.func)
        evaluated = self.visit(node.func)
        callee = evaluated if isinstance(evaluated, dict) else self._value(node.func)
        if helper in (["exec"], ["eval"]) or path and path[0] in {"exec", "eval"}:
            self.dynamic = True
        if set(callee.get("possible_helpers", [])) & {"exec", "eval"}:
            self.dynamic = True
        namespace = (
            self._namespace(node.func.value)
            if isinstance(node.func, ast.Attribute)
            else None
        )
        attribute_effect = _builtin_attribute_mutator(callee)
        if callee.get("kind") == "attribute-mutator":
            attribute_effect = callee
        if namespace is None and self.side_effects and attribute_effect is None:
            self.side_effects(node, self.env)
        method = node.func.attr if isinstance(node.func, ast.Attribute) else None
        effects = []
        if namespace is not None and method in _NAMESPACE_MUTATORS:
            effects.append({"namespace": namespace, "method": method})
        if callee.get("kind") == "namespace-mutator":
            effects.append(callee)
        effects.extend(callee.get("possible_namespace_mutators", []))
        getter = (
            helper == ["getattr"]
            or _builtin_getter(callee)
            or "getattr" in callee.get("possible_helpers", [])
        )
        arguments = []
        for argument in node.args:
            value = self.visit(argument)
            arguments.append(
                value if isinstance(value, dict) else self._value(argument)
            )
        for keyword in node.keywords:
            self.visit(keyword.value)
        if attribute_effect is not None and self.side_effects:
            self.side_effects(node, self.env, attribute_effect, arguments)
        for effect in effects:
            namespace = effect.get("namespace")
            offset = 0
            if namespace is None and arguments:
                namespace = arguments[0]
                offset = 1
            if namespace and namespace.get("kind") == "receiver-namespace":
                if self.side_effects:
                    self.side_effects(node, self.env, effect, arguments)
                continue
            if namespace and namespace.get("kind") in {
                "class-namespace",
                "module-namespace",
                "uncertain-namespace",
                "comprehension-namespace",
            }:
                self._mutate_namespace(
                    namespace, effect["method"], node.args[offset:], node.keywords
                )
        namespace_getters = (
            [callee]
            if callee.get("kind") == "namespace-getter"
            else callee.get("possible_namespace_getters", [])
        )
        namespaces = []
        for namespace_getter in namespace_getters:
            offset = 0 if "target" in namespace_getter else 1
            target = namespace_getter.get("target") or (
                arguments[0] if arguments else None
            )
            if target is not None and len(node.args) > offset:
                namespace = _namespace_lookup(target, node.args[offset])
                if namespace:
                    namespaces.append(namespace)
        if namespaces:
            return (
                namespaces[0]
                if callee.get("kind") == "namespace-getter"
                else self._join_binding(namespaces)
            )
        if getter and len(arguments) >= 2:
            namespace = arguments[0]
            if (
                isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "__dict__"
            ):
                return _dict_namespace(namespace)
            if (
                isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "__getattribute__"
                and _dict_namespace(namespace)
            ):
                return {"kind": "namespace-getter", "target": namespace}
            method = _getter_method(node.args[1])
            if method is not None and _builtin_dict(namespace):
                return {"kind": "namespace-mutator", "method": method}
            if method is not None and namespace.get("kind") in {
                "class-namespace",
                "module-namespace",
                "uncertain-namespace",
                "comprehension-namespace",
            }:
                return {
                    "kind": "namespace-mutator",
                    "namespace": namespace,
                    "method": method,
                }
        factory = _builtin_namespace_factory(callee)
        if not arguments and not node.keywords:
            if factory == "globals":
                return {"kind": "module-namespace", "qualified": True}
            if factory in {"vars", "locals"}:
                return {
                    "kind": "comprehension-namespace"
                    if self.in_comprehension
                    else "class-namespace",
                    "qualified": True,
                }
            if callee.get("kind") == "namespace-factory":
                return {
                    "kind": "uncertain-namespace",
                    "qualified": callee.get("qualified", False),
                    "scopes": callee["scopes"],
                }
        if callee.get("kind") == "non-namespace-factory":
            return {"kind": "non-namespace"}
        return self._namespace(node)

    def _mutate_namespace(self, namespace, method, args, keywords):
        if namespace["kind"] == "comprehension-namespace":
            return
        names = _namespace_mutated_names(method, args, keywords, namespace["qualified"])
        if names is None:
            if namespace["kind"] == "module-namespace":
                self.global_writes.add("*")
            elif namespace["kind"] == "uncertain-namespace":
                self.dynamic |= "class" in namespace["scopes"]
                if "module" in namespace["scopes"]:
                    self.global_writes.add("*")
            else:
                self.dynamic = True
        else:
            if namespace["kind"] == "module-namespace":
                self.global_writes.update(names)
            elif namespace["kind"] == "uncertain-namespace":
                if "module" in namespace["scopes"]:
                    self.global_writes.update(names)
                if "class" in namespace["scopes"]:
                    self.writes.update(names)
            else:
                self.writes.update(names)


def _dispatch_facts(tree, module):
    """Qualify only allocation/dispatch syntax actually present in this AST."""
    classes = _module_classes(tree)
    counts = Counter(node.name for node in _module_declarations(tree))
    facts = {}
    annotations_eager = sys.version_info < (3, 14) and not any(
        isinstance(statement, ast.ImportFrom)
        and statement.module == "__future__"
        and any(alias.name == "annotations" for alias in statement.names)
        for statement in tree.body
    )
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
        effects = _ClassNamespaceEffects(
            node, module, annotations_eager=annotations_eager
        )
        blocked.update(
            name for name in effects.writes | effects.missing if name.isidentifier()
        )
        if effects.dynamic:
            reasons.add("dynamic-class-namespace")
        methods = [
            child
            for child in _module_declarations(namespace)
            if isinstance(child, FUNCTIONS)
        ]
        if effects.direct_mapping_writes & (
            {method.name for method in methods} | _DISPATCH_SLOTS
        ):
            # Preserve existing qualification for direct mapping replacement of
            # declaration/dispatch authority, without blocking unrelated keys.
            reasons.add("dynamic-class-namespace")
        for name, count in Counter(
            child.name for child in _module_declarations(namespace)
        ).items():
            if count > 1:
                blocked.add(name)
        for method in methods:
            if method.name in effects.redirected:
                continue
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
        if effects.writes & _DISPATCH_SLOTS:
            reasons.add("custom-construction-or-dispatch")
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


def _definition_expressions(node, *, annotations_eager=True):
    expressions = list(getattr(node, "decorator_list", ()))
    if isinstance(node, ast.ClassDef):
        return [
            *expressions,
            *node.bases,
            *(keyword.value for keyword in node.keywords),
        ]
    args = node.args
    expressions.extend(args.defaults)
    expressions.extend(value for value in args.kw_defaults if value is not None)
    if annotations_eager:
        expressions.extend(
            arg.annotation
            for arg in (
                *args.posonlyargs,
                *args.args,
                *args.kwonlyargs,
                args.vararg,
                args.kwarg,
            )
            if arg is not None and arg.annotation is not None
        )
        if getattr(node, "returns", None) is not None:
            expressions.append(node.returns)
    return expressions


def _walrus_names(node: ast.AST) -> set[str]:
    """Find containing-scope writes without entering deferred callable bodies."""
    if isinstance(node, (*FUNCTIONS, ast.ClassDef, ast.Lambda)):
        return set().union(
            *(_walrus_names(value) for value in _definition_expressions(node))
        )
    names = _target_names(node.target) if isinstance(node, ast.NamedExpr) else set()
    for child in ast.iter_child_nodes(node):
        names.update(_walrus_names(child))
    return names


class _ScopeNames(ast.NodeVisitor):
    def __init__(self):
        self.bound: set[str] = set()
        self.globals: set[str] = set()
        self.nonlocals: set[str] = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.bound.add(node.id)

    def visit_FunctionDef(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    ):
        self.bound.add(node.name)
        for value in _definition_expressions(node):
            self.visit(value)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Lambda(self, node):
        for value in _definition_expressions(node):
            self.visit(value)

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
        self.bound.update(_walrus_names(node))

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


def _import_path(binding, members=()):
    parts = [binding["module"]]
    if binding.get("name"):
        parts.append(binding["name"])
    parts.extend(binding.get("target_members", members))
    return ".".join(parts)


def _import_contains(prefix, owner):
    return owner == prefix or owner.startswith(prefix + ".")


def _import_mutation_affects(constructor, member, mutation):
    if constructor["root_binding"].get("kind") != "import":
        return False
    owner = _import_path(constructor["root_binding"], constructor["members"])
    target = _import_path(mutation)
    changed = mutation.get("blocked_member", "*")
    if owner == target:
        return changed in {"*", member, *_DISPATCH_SLOTS}
    if owner.startswith(target + "."):
        return (
            changed == "*"
            or owner == target + "." + changed
            or owner.startswith(target + "." + changed + ".")
        )
    return False


@dataclass(frozen=True)
class PythonBindings:
    module: dict[str, dict]
    calls: dict[int, dict]
    classes: dict[int, dict]


@dataclass
class _BindingState:
    """Private related graph; one deepcopy preserves receiver/mutator aliases."""

    module: dict[str, dict] = dataclass_field(default_factory=dict)
    env: dict[str, dict] = dataclass_field(default_factory=dict)
    class_mutations: dict[str, set[str]] = dataclass_field(default_factory=dict)
    import_mutations: list[dict] = dataclass_field(default_factory=list)
    constructor_barriers: set[str] = dataclass_field(default_factory=set)
    module_namespace_invalidations: set[str] = dataclass_field(default_factory=set)
    possible_targets: dict[str, list[dict]] = dataclass_field(default_factory=dict)
    export_invalidations: set[str] = dataclass_field(default_factory=set)
    module_scope: bool = False

    def snapshot(self):
        return deepcopy(self)


class _BindingAnalyzer:
    def __init__(self, tree):
        self.state = _BindingState()
        self.calls: dict[int, dict] = {}
        self.allocation = 0
        self.call_scopes: dict[int, int | None] = {}
        self.current_scope: int | None = None
        self.deferred_effects: dict[int, _BindingState] = {}
        self.class_names = {node.name for node in _module_classes(tree)}
        self.annotations_eager = sys.version_info < (3, 14) and not any(
            isinstance(statement, ast.ImportFrom)
            and statement.module == "__future__"
            and any(alias.name == "annotations" for alias in statement.names)
            for statement in tree.body
        )

    @property
    def module(self):
        return self.state.module

    @property
    def class_mutations(self):
        return self.state.class_mutations

    @property
    def import_mutations(self):
        return self.state.import_mutations

    @property
    def constructor_barriers(self):
        return self.state.constructor_barriers

    @constructor_barriers.setter
    def constructor_barriers(self, value):
        self.state.constructor_barriers = value

    @property
    def module_namespace_invalidations(self):
        return self.state.module_namespace_invalidations

    @property
    def module_scope(self):
        return self.state.module_scope

    @module_scope.setter
    def module_scope(self, value):
        self.state.module_scope = value

    def function(self, node, closure: set[str], class_name: str | None = None):
        parent = self.state
        parent_scope = self.current_scope
        self.current_scope = id(node)
        self.state = parent.snapshot()
        scope = _scope_names(node.body)
        local = (scope.bound | _parameters(node.args)) - scope.globals
        # Module helper/namespace provenance remains available internally;
        # lexical local names must never inherit an outer possible owner.
        self.state.possible_targets = {
            name: [
                value
                for value in targets
                if _known_callable(value)
                or value.get("kind") in {"receiver-namespace", "module-namespace"}
            ]
            for name, targets in self.state.possible_targets.items()
            if name in self.module and name not in closure | local | scope.nonlocals
        }
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
        self.deferred_effects[id(node)] = self.state.snapshot()
        has_constructor_calls = any(
            self.call_scopes.get(key) == id(node)
            and value.get("kind") == "constructed-receiver"
            for key, value in self.calls.items()
        )
        if class_name and node.name == "__init__" or not has_constructor_calls:
            # Constructor effects qualify future instances. Other deferred
            # bodies are analyzed for their own calls, not executed here.
            for name, members in self.class_mutations.items():
                parent.class_mutations.setdefault(name, set()).update(members)
            for mutation in self.import_mutations:
                if mutation not in parent.import_mutations:
                    parent.import_mutations.append(deepcopy(mutation))
        self.state = parent
        self.current_scope = parent_scope

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
        self.allocation += 1
        return {
            "kind": "constructed-instance",
            "_allocation": self.allocation,
            "constructor": {
                "root_binding": dict(binding),
                "members": members,
                "line": node.lineno,
                "column": node.col_offset,
            },
            "blocked_members": [],
        }

    def call_binding(self, node, env, receiver=None):
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
                instance = (
                    receiver
                    if receiver is not None
                    else self.constructor(func.value, env)
                )
                origin = "direct-construction"
            elif isinstance(func.value, ast.Name):
                instance = (
                    receiver if receiver is not None else _lookup(env, func.value.id)
                )
                origin = "assigned-construction"
            else:
                instance = {}
                origin = "assigned-construction"
            if instance.get("kind") == "constructed-instance":
                constructor = instance["constructor"]
                root = constructor["root_binding"]
                local_mutations = (
                    self.class_mutations.get(root.get("symbol"), set())
                    if root.get("kind") == "local"
                    else set()
                )
                if (
                    func.attr in instance["blocked_members"]
                    or "*" in instance["blocked_members"]
                ):
                    return _unresolved(node, "receiver-member-replaced")
                if (
                    "*" in local_mutations
                    or func.attr in local_mutations
                    or local_mutations & _DISPATCH_SLOTS
                    or any(
                        _import_mutation_affects(constructor, func.attr, mutation)
                        for mutation in self.import_mutations
                    )
                ):
                    return _unresolved(node, "constructor-member-replaced")
                return {
                    "kind": "constructed-receiver",
                    "constructor": deepcopy(instance["constructor"]),
                    "member": func.attr,
                    "receiver_origin": origin,
                }
            if isinstance(func.value, ast.Call):
                if instance.get("kind") in {
                    "receiver-namespace",
                    "module-namespace",
                    "attribute-mutator",
                    "namespace-mutator",
                }:
                    return _unresolved(node, "unsupported-instance-call")
                return {**instance, "line": node.lineno, "column": node.col_offset}
        path = _callee_path(func)
        if path is None:
            return _unresolved(node, "unsupported-call-target")
        binding = _lookup(env, path[0])
        if binding.get("kind") in {
            "constructed-instance",
            "receiver-namespace",
            "attribute-mutator",
            "namespace-mutator",
            "non-namespace-factory",
            "module-namespace",
        }:
            return _unresolved(node, "unsupported-instance-call")
        if binding.get("kind") == "unresolved":
            return _unresolved(
                node, binding.get("reason", "receiver-binding-unresolved")
            )
        return {key: value for key, value in binding.items() if not key.startswith("_")}

    @staticmethod
    def _targets(binding):
        if (
            _builtin_getter(binding)
            or _builtin_dict(binding)
            or _builtin_namespace_factory(binding)
        ):
            return [binding]
        if (
            binding.get("kind") == "import"
            and binding.get("module") == "builtins"
            and binding.get("name") in {"setattr", "delattr"}
        ):
            return [{"kind": "attribute-mutator", "qualified": False}]
        if binding.get("kind") in {
            "constructed-instance",
            "receiver",
            "local",
            "import",
        }:
            return [binding]
        if binding.get("kind") in {
            "attribute-mutator",
            "receiver-namespace",
            "namespace-mutator",
            "namespace-getter",
        }:
            return [binding]
        if binding.get("kind") == "builtin" and binding.get("symbol") in {
            "setattr",
            "delattr",
        }:
            return [{"kind": "attribute-mutator", "qualified": False}]
        return binding.get("_possible_targets", [])

    @staticmethod
    def _unique_targets(targets):
        result = []
        for target in targets:
            if target not in result:
                result.append(target)
        return result

    def bind_value(self, name, value, env, source=None):
        candidates = value.get("_possible_targets", [])
        if source is not None and isinstance(source, ast.Name):
            candidates = [*candidates, *self.state.possible_targets.get(source.id, [])]
        if candidates:
            self.state.possible_targets[name] = self._unique_targets(candidates)
        else:
            self.state.possible_targets.pop(name, None)
        env[name] = (
            {key: item for key, item in value.items() if not key.startswith("_")}
            if value.get("kind") == "unresolved"
            else value
        )

    def join_states(self, states, env, values=()):
        """Join a whole related graph without erasing aliases or possible owners."""
        objects = {}
        visited = set()

        def collect(value):
            if isinstance(value, (dict, list, tuple)):
                identity = id(value)
                if identity in visited:
                    return
                visited.add(identity)
            if isinstance(value, dict):
                if "_allocation" in value:
                    token = value["_allocation"]
                    if token not in objects:
                        objects[token] = deepcopy(value)
                    else:
                        objects[token]["blocked_members"] = sorted(
                            set(objects[token]["blocked_members"])
                            | set(value["blocked_members"])
                        )
                for item in value.values():
                    collect(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    collect(item)

        for state in states:
            collect(vars(state))
        for value in values:
            collect(value)
        memo = {}

        def canonical(value: Any) -> Any:
            if isinstance(value, dict):
                if "_allocation" in value:
                    return objects[value["_allocation"]]
                if id(value) not in memo:
                    memo[id(value)] = {
                        key: canonical(item) for key, item in value.items()
                    }
                return memo[id(value)]
            if isinstance(value, list):
                return [canonical(item) for item in value]
            return deepcopy(value)

        merged = _BindingState(**canonical(vars(states[0])))
        canonical_envs = [canonical(state.env) for state in states]
        merged.possible_targets = {}
        for state in states:
            for name, targets in state.possible_targets.items():
                merged.possible_targets.setdefault(name, []).extend(canonical(targets))
        result = {}
        for name in set().union(*(set(values) for values in canonical_envs)):
            bindings = [_lookup(values, name) for values in canonical_envs]
            if all(binding == bindings[0] for binding in bindings):
                result[name] = bindings[0]
            else:
                result[name] = {
                    "kind": "unresolved",
                    "reason": "receiver-path-conflict",
                }
                merged.possible_targets.setdefault(name, []).extend(
                    target for binding in bindings for target in self._targets(binding)
                )
        merged.possible_targets = {
            name: self._unique_targets(targets)
            for name, targets in merged.possible_targets.items()
        }
        merged.class_mutations = {}
        merged.import_mutations = []
        for state in states:
            for name, members in state.class_mutations.items():
                merged.class_mutations.setdefault(name, set()).update(members)
            for mutation in state.import_mutations:
                if mutation not in merged.import_mutations:
                    merged.import_mutations.append(deepcopy(mutation))
        merged.constructor_barriers = set().union(
            *(state.constructor_barriers for state in states)
        )
        merged.module_namespace_invalidations = set().union(
            *(state.module_namespace_invalidations for state in states)
        )
        merged.export_invalidations = set().union(
            *(state.export_invalidations for state in states)
        )
        env.clear()
        env.update(result)
        merged.env = env
        if states[0].module is states[0].env:
            merged.module = env
        self.state = merged
        returns = [canonical(value) for value in values]
        if returns and all(value == returns[0] for value in returns):
            return returns[0]
        return {
            "kind": "unresolved",
            "reason": "receiver-path-conflict",
            "_possible_targets": self._unique_targets(
                target for value in returns for target in self._targets(value)
            ),
        }

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

    def imported_target(self, node, env):
        path = _callee_path(node)
        if path is None:
            return None
        root, members = path
        binding = _lookup(env, root)
        if binding.get("kind") != "import":
            return None
        if not members:
            return binding
        # Qualify an attribute of a captured imported namespace without loading
        # or executing the referenced module. These descriptors stay private.
        return {
            "kind": "import",
            "module": binding["module"],
            "name": binding.get("name", ""),
            "target_members": members,
        }

    def namespace_value(self, node, env):
        if isinstance(node, ast.Call):
            path = _callee_path(node.func)
            if path and _lookup(env, path[0]).get("kind") == "non-namespace-factory":
                return None
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

    @staticmethod
    def namespace_mutator(receiver, method):
        """Capture every known mapping owner before later argument effects."""
        if not receiver or method not in _NAMESPACE_MUTATORS | {"*"}:
            return None
        if _builtin_dict(receiver):
            return {"kind": "namespace-mutator", "method": method}
        if receiver.get("kind") in {"receiver-namespace", "module-namespace"}:
            return {
                "kind": "namespace-mutator",
                "namespace": receiver,
                "method": method,
            }
        effects = []
        for namespace in receiver.get("_possible_targets", []):
            if _builtin_dict(namespace):
                effects.append({"kind": "namespace-mutator", "method": method})
            elif namespace.get("kind") in {"receiver-namespace", "module-namespace"}:
                effects.append(
                    {
                        "kind": "namespace-mutator",
                        "namespace": namespace,
                        "method": method,
                    }
                )
        return {"kind": "unresolved", "_possible_targets": effects} if effects else None

    def mutator_value(self, node, env):
        if isinstance(node, ast.Attribute) and node.attr in _NAMESPACE_MUTATORS:
            receiver = (
                _lookup(env, node.value.id)
                if isinstance(node.value, ast.Name)
                else self.namespace_value(node.value, env)
            )
            effect = self.namespace_mutator(receiver, node.attr)
            if effect:
                return effect
        path = self.helper_path(node, env)
        if path == ["object", "__getattribute__"]:
            return {"kind": "namespace-getter"}
        if isinstance(node, ast.Attribute) and node.attr == "__getattribute__":
            target = (
                _lookup(env, node.value.id)
                if isinstance(node.value, ast.Name)
                else None
            )
            if target is not None and _dict_namespace(target):
                return {"kind": "namespace-getter", "target": target}
        if path in (["getattr"], ["dict"], ["vars"], ["locals"], ["globals"]):
            return {"kind": "builtin", "symbol": path[0]}
        if (
            path
            and len(path) == 2
            and path[0] == "dict"
            and path[1] in _NAMESPACE_MUTATORS
        ):
            return {"kind": "namespace-mutator", "method": path[1]}
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
            and isinstance(node.value, ast.Name)
        ):
            target = _lookup(env, node.value.id)
            if target.get("kind") in {"constructed-instance", "receiver"}:
                return {
                    "kind": "attribute-mutator",
                    "qualified": True,
                    "target": target,
                }
        if isinstance(node, ast.Call):
            target = None
            member = None
            if (
                self.helper_path(node.func, env) == ["getattr"]
                and len(node.args) >= 2
                and isinstance(node.args[0], ast.Name)
            ):
                target = _lookup(env, node.args[0].id)
                member = node.args[1]
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "__getattribute__"
                and isinstance(node.func.value, ast.Name)
                and node.args
            ):
                target = _lookup(env, node.func.value.id)
                member = node.args[0]
            if (
                target is not None
                and target.get("kind") in {"constructed-instance", "receiver"}
                and isinstance(member, ast.Constant)
                and member.value in {"__setattr__", "__delattr__"}
            ):
                return {
                    "kind": "attribute-mutator",
                    "qualified": True,
                    "target": target,
                }
        if (
            isinstance(node, ast.Attribute)
            and node.attr in {"__setattr__", "__delattr__"}
            or isinstance(node, ast.Name)
            and node.id in {"setattr", "delattr"}
        ):
            return {"kind": "attribute-mutator", "qualified": False}
        return None

    def invalidate_target(self, binding, env, member="*"):
        if binding.get("kind") == "module-namespace":
            self.module_namespace_invalidations.add(member)
            return
        if binding.get("kind") == "unresolved":
            for possible in binding.get("_possible_targets", []):
                self.invalidate_target(possible.get("target", possible), env, member)
            return
        if binding.get("kind") == "constructed-instance":
            token = binding.get("_allocation")

            matches = {}
            visited = set()

            def live(value):
                if not isinstance(value, (dict, list, tuple)) or id(value) in visited:
                    return
                visited.add(id(value))
                if isinstance(value, dict):
                    if token is not None and value.get("_allocation") == token:
                        matches[id(value)] = value
                        return
                    for item in value.values():
                        live(item)
                else:
                    for item in value:
                        live(item)

            # Captured call owners can predate a join. Mutate every live alias
            # of this allocation, including the captured descriptor itself.
            matches[id(binding)] = binding
            for value in [binding, *env.values(), *self.state.possible_targets.values()]:
                live(value)
            blocked = {member}
            if member in {"__class__", "__dict__"}:
                blocked.add("*")
            for value in matches.values():
                blocked.update(value["blocked_members"])
            for value in matches.values():
                value["blocked_members"] = sorted(blocked)
        elif (
            binding.get("kind") in {"local", "receiver"}
            and binding.get("symbol") in self.class_names
        ):
            self.class_mutations.setdefault(binding["symbol"], set()).add(member)
        elif binding.get("kind") == "import":
            self.import_mutations.append({**binding, "blocked_member": member})
            if self.module_scope:
                owner = _import_path(binding)
                for name, value in self.module.items():
                    if value.get("kind") == "import" and _import_contains(
                        _import_path(value), owner
                    ):
                        self.state.export_invalidations.add(name)

    def invalidate_names(self, names, env):
        if "*" in names:
            names = set(env) | names
        for name in names:
            binding = env.get(name, {})
            if binding.get("kind") in {"constructed-instance", "namespace-mutator"}:
                self.state.possible_targets.setdefault(name, []).append(binding)
            if binding.get("kind") in {
                "attribute-mutator",
                "receiver-namespace",
                "namespace-mutator",
            }:
                target = binding.get("target")
                if target is not None:
                    targets = self.state.possible_targets.setdefault(name, [])
                    if not any(value is target for value in targets):
                        targets.append(target)
                    # Losing an alias cannot erase the receiver it may mutate.
                    self.invalidate_target(target, env)
            elif binding.get("kind") == "module-namespace":
                self.module_namespace_invalidations.add("*")
        env.update(
            {
                name: {"kind": "unresolved", "reason": "receiver-path-conflict"}
                for name in names
            }
        )

    def invalidate_members(
        self,
        node,
        env,
        *,
        recursive=True,
        mutator=None,
        arguments=None,
        store_owner=None,
    ):
        def eager(current):
            yield current
            if isinstance(current, (*FUNCTIONS, ast.ClassDef, ast.Lambda)):
                for value in _definition_expressions(
                    current, annotations_eager=self.annotations_eager
                ):
                    yield from eager(value)
            elif isinstance(current, ast.GeneratorExp):
                if current.generators:
                    yield from eager(current.generators[0].iter)
            else:
                for child in ast.iter_child_nodes(current):
                    yield from eager(child)

        for child in eager(node) if recursive else [node]:
            if (
                isinstance(child, ast.Call)
                and not (child is node and mutator is not None)
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
                if (
                    child is node
                    and mutator
                    and mutator.get("kind") == "namespace-mutator"
                ):
                    namespace = mutator["namespace"]
                if namespace and namespace.get("kind") == "receiver-namespace":
                    self.invalidate_target(namespace["target"], env)
                elif namespace and namespace.get("kind") == "module-namespace":
                    self.module_namespace_invalidations.add("*")
                elif isinstance(child.func.value, ast.Name):
                    for possible in self.state.possible_targets.get(
                        child.func.value.id, []
                    ):
                        if possible.get("kind") == "receiver-namespace":
                            self.invalidate_target(possible["target"], env)
            if isinstance(child, ast.Subscript) and isinstance(
                child.ctx, (ast.Store, ast.Del)
            ):
                namespace = (
                    _lookup(env, child.value.id)
                    if isinstance(child.value, ast.Name)
                    else self.namespace_value(child.value, env)
                )
                if child is node and store_owner is not None:
                    namespace = store_owner
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
                else:
                    candidates = (
                        store_owner.get("_possible_targets", [])
                        if child is node and store_owner is not None
                        else self.state.possible_targets.get(child.value.id, [])
                        if isinstance(child.value, ast.Name)
                        else []
                    )
                    for possible in candidates:
                        target = possible.get("target", possible)
                        member = (
                            child.slice.value
                            if possible.get(
                                "qualified", possible.get("kind") == "module-namespace"
                            )
                            and isinstance(child.slice, ast.Constant)
                            and isinstance(child.slice.value, str)
                            and child.slice.value.isidentifier()
                            else "*"
                        )
                        self.invalidate_target(target, env, member)
            if isinstance(child, ast.Attribute) and isinstance(
                child.ctx, (ast.Store, ast.Del)
            ):
                if child is node and store_owner is not None:
                    self.invalidate_target(
                        store_owner.get("_effect_target", store_owner), env, child.attr
                    )
                elif isinstance(child.value, ast.Name):
                    self.invalidate_target(
                        _lookup(env, child.value.id), env, child.attr
                    )
                    for possible in self.state.possible_targets.get(child.value.id, []):
                        self.invalidate_target(
                            possible.get("target", possible), env, child.attr
                        )
                else:
                    path = _callee_path(child)
                    if (
                        path is not None
                        and _lookup(env, path[0]).get("kind") == "import"
                    ):
                        self.invalidate_target(_lookup(env, path[0]), env)
            if isinstance(child, ast.Call):
                captured = (
                    mutator
                    if child is node and mutator is not None
                    else _lookup(env, child.func.id)
                    if isinstance(child.func, ast.Name)
                    else self.mutator_value(child.func, env)
                )
                namespace_effects = (
                    [captured]
                    if captured and captured.get("kind") == "namespace-mutator"
                    else [
                        value
                        for value in (captured or {}).get("_possible_targets", [])
                        if value.get("kind") == "namespace-mutator"
                    ]
                )
                if isinstance(child.func, ast.Name) and not (
                    child is node and mutator is not None
                ):
                    namespace_effects.extend(
                        value
                        for value in self.state.possible_targets.get(child.func.id, [])
                        if value.get("kind") == "namespace-mutator"
                    )
                for effect in namespace_effects:
                    namespace = effect.get("namespace")
                    offset = 0
                    if namespace is None and child.args:
                        offset = 1
                        if child is node and arguments is not None and arguments:
                            namespace = arguments[0]
                        elif isinstance(child.args[0], ast.Name):
                            namespace = _lookup(env, child.args[0].id)
                            if namespace.get("kind") == "unresolved":
                                namespace = {
                                    **namespace,
                                    "_possible_targets": self.state.possible_targets.get(
                                        child.args[0].id, []
                                    ),
                                }
                        else:
                            namespace = self.namespace_value(child.args[0], env)
                    bound = self.namespace_mutator(namespace, effect["method"])
                    owners = (
                        [bound]
                        if bound and "namespace" in bound
                        else [
                            value
                            for value in (bound or {}).get("_possible_targets", [])
                            if "namespace" in value
                        ]
                    )
                    for owner in owners:
                        namespace = owner["namespace"]
                        names = _namespace_mutated_names(
                            effect.get("method"),
                            child.args[offset:],
                            child.keywords,
                            namespace.get("qualified", True),
                        )
                        if namespace.get("target", {}).get("kind") == "receiver":
                            # A constructor receiver has no captured allocation;
                            # retain its existing class-wide dispatch qualification.
                            names = None
                        for member in names if names is not None else ["*"]:
                            if namespace.get("kind") == "receiver-namespace":
                                self.invalidate_target(namespace["target"], env, member)
                            elif namespace.get("kind") == "module-namespace":
                                self.module_namespace_invalidations.add(member)
                frozen = child is node and mutator is not None
                effect = (
                    mutator
                    if frozen
                    else (
                        _lookup(env, child.func.id)
                        if isinstance(child.func, ast.Name)
                        else None
                    )
                )
                if not frozen and (
                    not effect or effect.get("kind") != "attribute-mutator"
                ):
                    effect = self.mutator_value(child.func, env)
                effects = (
                    [effect]
                    if effect and effect.get("kind") == "attribute-mutator"
                    else [
                        value
                        for value in (effect or {}).get("_possible_targets", [])
                        if value.get("kind") == "attribute-mutator"
                    ]
                )
                if isinstance(child.func, ast.Name) and not frozen:
                    effects.extend(
                        value
                        for value in self.state.possible_targets.get(child.func.id, [])
                        if value.get("kind") == "attribute-mutator"
                    )
                for effect in effects:
                    offset = 0 if "target" in effect else 1
                    target = effect.get("target")
                    if (
                        target is None
                        and arguments is not None
                        and child is node
                        and arguments
                    ):
                        target = arguments[0].get("_effect_target", arguments[0])
                    if target is None and child.args:
                        target = (
                            _lookup(env, child.args[0].id)
                            if isinstance(child.args[0], ast.Name)
                            else self.imported_target(child.args[0], env)
                        )
                    if target is None:
                        continue
                    argument = child.args[offset] if len(child.args) > offset else None
                    member = (
                        argument.value
                        if effect["qualified"]
                        and isinstance(argument, ast.Constant)
                        and isinstance(argument.value, str)
                        and argument.value.isidentifier()
                        else "*"
                    )
                    self.invalidate_target(target, env, member)

    def shadow_names(self, names, env):
        """Enter a lexical binding without borrowing its outer possible owners."""
        for name in names:
            env[name] = UNKNOWN
            self.state.possible_targets.pop(name, None)

    def expression(self, node, env: dict, closure: set[str], *, capture=True):
        self.state.env = env
        if isinstance(node, ast.Name):
            value = _lookup(env, node.id)
            if (
                value.get("kind") == "unresolved"
                and node.id in self.state.possible_targets
            ):
                return {
                    **value,
                    "_possible_targets": self.state.possible_targets[node.id],
                }
            return value
        if isinstance(node, ast.NamedExpr):
            value = self.expression(node.value, env, closure, capture=capture)
            for name in _target_names(node.target):
                self.bind_value(name, value, env, node.value)
            return value
        if isinstance(node, ast.BoolOp):
            value = self.expression(node.values[0], env, closure, capture=capture)
            states, values = [self.state.snapshot()], [value]
            for operand in node.values[1:]:
                self.state = self.state.snapshot()
                value = self.expression(
                    operand, self.state.env, closure, capture=capture
                )
                states.append(self.state.snapshot())
                values.append(value)
            return self.join_states(states, env, values)
        if isinstance(node, ast.IfExp):
            self.expression(node.test, env, closure, capture=capture)
            base = self.state.snapshot()
            states, values = [], []
            for branch in (node.body, node.orelse):
                self.state = base.snapshot()
                value = self.expression(
                    branch, self.state.env, closure, capture=capture
                )
                states.append(self.state.snapshot())
                values.append(value)
            return self.join_states(states, env, values)
        if isinstance(node, ast.Compare):
            self.expression(node.left, env, closure, capture=capture)
            self.expression(node.comparators[0], env, closure, capture=capture)
            states = [self.state.snapshot()]
            for comparator in node.comparators[1:]:
                self.state = self.state.snapshot()
                self.expression(comparator, self.state.env, closure, capture=capture)
                states.append(self.state.snapshot())
            self.join_states(states, env)
            return UNKNOWN
        if isinstance(node, ast.Lambda):
            for value in _definition_expressions(node):
                self.expression(value, env, closure, capture=capture)
            parent = self.state
            self.state = parent.snapshot()
            local = _parameters(node.args) | _walrus_names(node.body)
            nested = self.state.env
            self.shadow_names(closure | local, nested)
            self.expression(node.body, nested, closure | local, capture=capture)
            self.state = parent
            return (
                {"kind": "non-namespace-factory"}
                if isinstance(node.body, ast.Dict) and not node.body.keys
                else UNKNOWN
            )
        if isinstance(node, COMPREHENSIONS):
            self.expression(node.generators[0].iter, env, closure, capture=capture)
            writes = _walrus_names(node)
            self.invalidate_names(writes, env)
            skipped = self.state.snapshot()
            self.state = skipped.snapshot()
            nested = self.state.env
            bound = set(closure)
            iteration_names = set()
            for index, generator in enumerate(node.generators):
                if index:
                    self.expression(generator.iter, nested, bound, capture=capture)
                names = _target_names(generator.target)
                bound.update(names)
                iteration_names.update(names)
                self.shadow_names(names, nested)
                for condition in generator.ifs:
                    self.expression(condition, nested, bound, capture=capture)
            for value in (
                [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
            ):
                self.expression(value, nested, bound, capture=capture)
            if isinstance(node, ast.GeneratorExp):
                self.join_states([skipped], env)
            else:
                executed = self.state.snapshot()
                # Iteration bindings belong only to this comprehension. Restore
                # their outer lexical facts before joining executed mutations.
                for name in iteration_names:
                    if name in skipped.env:
                        executed.env[name] = skipped.env[name]
                    else:
                        executed.env.pop(name, None)
                    if name in skipped.possible_targets:
                        executed.possible_targets[name] = skipped.possible_targets[name]
                    else:
                        executed.possible_targets.pop(name, None)
                self.join_states([skipped, executed], env)
            return UNKNOWN
        if isinstance(node, ast.Call):
            receiver = None
            callee = None
            if isinstance(node.func, ast.Attribute):
                receiver = self.expression(
                    node.func.value, env, closure, capture=capture
                )
            else:
                callee = self.expression(node.func, env, closure, capture=capture)
            binding = deepcopy(self.call_binding(node, env, receiver))
            instance = self.constructor(node, env)
            helper = self.helper_path(node.func, env)
            getter = (
                helper == ["getattr"]
                or _builtin_getter(callee or {})
                or any(
                    _builtin_getter(value)
                    for value in (callee or {}).get("_possible_targets", [])
                )
            )
            effect = _builtin_attribute_mutator(callee or {}) or callee
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "__call__"
                and _known_callable(receiver or {})
            ):
                callee = receiver
                effect = _builtin_attribute_mutator(callee or {}) or callee
                getter = _builtin_getter(callee or {}) or any(
                    _builtin_getter(value)
                    for value in (callee or {}).get("_possible_targets", [])
                )
            factories = {
                value
                for value in [
                    _builtin_namespace_factory(callee or {}),
                    *(
                        _builtin_namespace_factory(value)
                        for value in (callee or {}).get("_possible_targets", [])
                    ),
                ]
                if value is not None
            }
            if (
                helper
                and len(helper) == 1
                and helper[0] in {"vars", "locals", "globals"}
            ):
                factories.add(helper[0])
            if not effect or (
                effect.get("kind")
                not in {"attribute-mutator", "namespace-mutator", "namespace-getter"}
                and not effect.get("_possible_targets")
            ):
                effect = self.mutator_value(node.func, env)
            namespace_getter = (
                effect if effect and effect.get("kind") == "namespace-getter" else None
            )
            if isinstance(node.func, ast.Attribute):
                captured = self.namespace_mutator(receiver, node.func.attr)
                if captured:
                    effect = captured
                if (
                    node.func.attr == "__getattribute__"
                    and helper != ["object", "__getattribute__"]
                    and receiver
                    and _dict_namespace(receiver)
                ):
                    namespace_getter = {"kind": "namespace-getter", "target": receiver}
            arguments = [
                self.expression(argument, env, closure, capture=capture)
                for argument in node.args
            ]
            for keyword in node.keywords:
                self.expression(keyword.value, env, closure, capture=capture)
            self.invalidate_members(
                node,
                env,
                recursive=False,
                mutator=effect or {"kind": "no-mutator"},
                arguments=arguments,
            )
            if capture:
                self.calls[id(node)] = binding
                self.call_scopes[id(node)] = self.current_scope
            namespace = self.namespace_value(node, env)
            if (
                namespace
                and namespace.get("kind") == "receiver-namespace"
                and arguments
            ):
                namespace["target"] = arguments[0]
            namespace_getters = (
                [namespace_getter]
                if namespace_getter is not None
                else [
                    value
                    for value in (effect or {}).get("_possible_targets", [])
                    if value.get("kind") == "namespace-getter"
                ]
            )
            retrieved_namespaces = []
            for captured_getter in namespace_getters:
                offset = 0 if "target" in captured_getter else 1
                target = captured_getter.get("target") or (
                    arguments[0] if arguments else None
                )
                if target is not None and len(node.args) > offset:
                    result = _namespace_lookup(target, node.args[offset])
                    if result:
                        retrieved_namespaces.append(result)
            if retrieved_namespaces:
                namespace = (
                    retrieved_namespaces[0]
                    if namespace_getter is not None
                    else {
                        "kind": "unresolved",
                        "_possible_targets": retrieved_namespaces,
                    }
                )
            if getter and len(arguments) >= 2:
                namespace = _namespace_lookup(arguments[0], node.args[1]) or namespace
            if (callee or {}).get("kind") == "non-namespace-factory":
                namespace = None
            possible_namespaces = []
            if "vars" in factories and len(arguments) == 1:
                possible_namespaces.append(
                    {
                        "kind": "receiver-namespace",
                        "target": arguments[0],
                        "qualified": True,
                    }
                )
            if not arguments and (
                "globals" in factories
                or self.module_scope
                and factories & {"vars", "locals"}
            ):
                possible_namespaces.append({"kind": "module-namespace"})
            if possible_namespaces:
                direct_factory = _builtin_namespace_factory(callee or {})
                namespace = (
                    possible_namespaces[0]
                    if direct_factory is not None
                    else {
                        "kind": "unresolved",
                        "_possible_targets": possible_namespaces,
                    }
                )
            private = self.mutator_value(node, env)
            if getter and len(arguments) >= 2:
                if (
                    isinstance(node.args[1], ast.Constant)
                    and node.args[1].value == "__getattribute__"
                    and _dict_namespace(arguments[0])
                ):
                    private = {"kind": "namespace-getter", "target": arguments[0]}
                method = _getter_method(node.args[1])
                if method is not None:
                    private = self.namespace_mutator(arguments[0], method) or private
            if helper == ["vars"] and len(arguments) == 1:
                namespace = {
                    "kind": "receiver-namespace",
                    "target": arguments[0],
                    "qualified": True,
                }
            if (
                helper == ["getattr"]
                and len(arguments) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value in {"__setattr__", "__delattr__"}
            ):
                private = {
                    "kind": "attribute-mutator",
                    "target": arguments[0],
                    "qualified": True,
                }
            if (
                private
                and private.get("target") is not None
                and arguments
                and self.helper_path(node.func, env) == ["getattr"]
            ):
                private["target"] = arguments[0]
            return namespace or private or instance
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if key is not None:
                    self.expression(key, env, closure, capture=capture)
                self.expression(value, env, closure, capture=capture)
            return UNKNOWN
        if isinstance(node, ast.Attribute):
            owner = self.expression(node.value, env, closure, capture=capture)
            if node.attr == "__call__" and _known_callable(owner):
                return owner
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                self.invalidate_members(node, env, recursive=False, store_owner=owner)
            private = (
                self.namespace_mutator(owner, node.attr)
                or self.namespace_value(node, env)
                or self.mutator_value(node, env)
            )
            if private:
                return private
            imported = self.imported_target(node, env)
            return {**UNKNOWN, "_effect_target": imported} if imported else UNKNOWN
        if isinstance(node, ast.Subscript):
            owner = self.expression(node.value, env, closure, capture=capture)
            self.expression(node.slice, env, closure, capture=capture)
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                self.invalidate_members(node, env, recursive=False, store_owner=owner)
            return UNKNOWN
        for child in ast.iter_child_nodes(node):
            self.expression(child, env, closure, capture=capture)
        return UNKNOWN

    def block(
        self, body, env: dict, closure: set[str], *, capture: bool, module: bool = False
    ):
        prior_scope = self.module_scope
        prior_env = self.state.env
        self.state.env = env
        self.module_scope = module
        for statement in body:
            if isinstance(statement, FUNCTIONS):
                for value in _definition_expressions(
                    statement, annotations_eager=self.annotations_eager
                ):
                    self.expression(value, env, closure, capture=capture)
                if capture:
                    self.function(statement, set() if module else closure)
                env[statement.name] = (
                    {"kind": "local", "symbol": statement.name} if module else UNKNOWN
                )
            elif isinstance(statement, ast.ClassDef):
                for value in _definition_expressions(statement):
                    self.expression(value, env, closure, capture=capture)
                class_scope = _scope_names(statement.body)
                outer_writes = class_scope.bound & (
                    class_scope.globals | class_scope.nonlocals
                )
                self.invalidate_names(outer_writes, env)
                self.module_namespace_invalidations.update(
                    class_scope.bound & class_scope.globals
                )

                def class_effect(
                    node, class_env, mutator=None, arguments=None, store_owner=None
                ):
                    previous_scope = self.module_scope
                    self.module_scope = False
                    before = len(self.import_mutations)
                    self.invalidate_members(
                        node,
                        class_env,
                        recursive=mutator is None and store_owner is None,
                        mutator=mutator,
                        arguments=arguments,
                        store_owner=store_owner,
                    )
                    self.module_scope = previous_scope
                    if previous_scope:
                        for mutation in self.import_mutations[before:]:
                            for name, binding in self.module.items():
                                if binding.get("kind") == "import" and _import_contains(
                                    _import_path(binding), _import_path(mutation)
                                ):
                                    self.state.export_invalidations.add(name)

                effects = _ClassNamespaceEffects(
                    statement,
                    env,
                    annotations_eager=self.annotations_eager,
                    side_effects=class_effect,
                )
                self.module_namespace_invalidations.update(effects.global_writes)
                self.invalidate_names(effects.outer_writes, env)
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
                augmented_owner = None
                if isinstance(statement, ast.AugAssign) and isinstance(
                    statement.target, (ast.Attribute, ast.Subscript)
                ):
                    augmented_owner = self.expression(
                        statement.target.value, env, closure, capture=capture
                    )
                    if isinstance(statement.target, ast.Subscript):
                        self.expression(
                            statement.target.slice, env, closure, capture=capture
                        )
                evaluated = (
                    self.expression(value, env, closure, capture=capture)
                    if value is not None
                    else UNKNOWN
                )
                targets = (
                    statement.targets
                    if isinstance(statement, ast.Assign)
                    else [statement.target]
                )
                binding = evaluated
                if isinstance(statement, ast.AugAssign):
                    binding = {"kind": "unresolved", "reason": "receiver-rebound"}
                for target in targets:
                    if augmented_owner is not None:
                        self.invalidate_members(
                            target, env, recursive=False, store_owner=augmented_owner
                        )
                    elif not isinstance(target, ast.Name):
                        self.expression(target, env, closure, capture=capture)
                    for name in _target_names(target):
                        if value is not None:
                            self.bind_value(
                                name,
                                binding if isinstance(target, ast.Name) else UNKNOWN,
                                env,
                                value,
                            )
            elif isinstance(statement, getattr(ast, "TypeAlias", ())):
                for name in _target_names(statement.name):
                    env[name] = {"kind": "unresolved", "reason": "receiver-rebound"}
            elif isinstance(statement, ast.Delete):
                self.expression(statement, env, closure, capture=capture)
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
                names = _scope_names([statement]).bound
                loop = isinstance(statement, (ast.For, ast.AsyncFor, ast.While))
                branch_base = dict(env)
                if loop:
                    self.invalidate_names(names, branch_base)
                    if isinstance(statement, ast.While):
                        self.invalidate_members(statement.test, branch_base)
                    # A body mutation also affects calls on later iterations.
                    # An uncaptured pass propagates member/alias mutations before
                    # recording any loop call, without executing the source.
                    if capture:
                        self.block(
                            statement.body,
                            dict(branch_base),
                            closure,
                            capture=False,
                            module=module,
                        )
                for field in ("test", "iter"):
                    value = getattr(statement, field, None)
                    if value is not None:
                        self.expression(
                            value,
                            branch_base if isinstance(statement, ast.While) else env,
                            closure,
                            capture=capture,
                        )
                branches = [(statement.body, None), (statement.orelse, None)]
                handler_types = {}
                if isinstance(statement, (ast.Try, getattr(ast, "TryStar", ast.Try))):
                    handler_types = {
                        id(handler.body): handler.type
                        for handler in getattr(statement, "handlers", ())
                    }
                    branches.extend(
                        (handler.body, handler.name)
                        for handler in getattr(statement, "handlers", ())
                    )
                    branches.append((getattr(statement, "finalbody", []), None))
                for branch, exception_name in branches:
                    branch_env = dict(branch_base if loop else env)
                    if (
                        isinstance(
                            statement, (ast.Try, getattr(ast, "TryStar", ast.Try))
                        )
                        and branch is not statement.body
                    ):
                        # Handlers can follow any executed prefix; else/finally
                        # follow body writes rather than the pre-try bindings.
                        self.invalidate_names(names, branch_env)
                    if exception_name:
                        branch_env[exception_name] = UNKNOWN
                    handler_type = handler_types.get(id(branch))
                    if handler_type is not None:
                        self.expression(
                            handler_type, branch_env, closure, capture=capture
                        )
                    if isinstance(statement, (ast.For, ast.AsyncFor)):
                        if branch is statement.body:
                            self.expression(
                                statement.target, branch_env, closure, capture=capture
                            )
                        branch_env.update(
                            {name: UNKNOWN for name in _target_names(statement.target)}
                        )
                    self.block(
                        branch, branch_env, closure, capture=capture, module=module
                    )
                    self.invalidate_names(names, branch_env)
                self.invalidate_names(names, env)
            elif isinstance(statement, getattr(ast, "Match", ())):
                self.expression(statement.subject, env, closure, capture=capture)
                for case in statement.cases:
                    names = _ScopeNames()
                    names.visit(case.pattern)
                    branch_env = {**env, **{name: UNKNOWN for name in names.bound}}
                    if case.guard is not None:
                        self.expression(
                            case.guard, branch_env, closure, capture=capture
                        )
                    self.block(
                        case.body, branch_env, closure, capture=capture, module=module
                    )
                    self.invalidate_names(_scope_names(case.body).bound, branch_env)
                self.invalidate_names(_scope_names([statement]).bound, env)
            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                for item in statement.items:
                    self.expression(item.context_expr, env, closure, capture=capture)
                    if item.optional_vars:
                        self.expression(
                            item.optional_vars, env, closure, capture=capture
                        )
                        env.update(
                            {
                                name: UNKNOWN
                                for name in _target_names(item.optional_vars)
                            }
                        )
                self.block(statement.body, env, closure, capture=capture, module=module)
            elif capture:
                self.expression(statement, env, closure)
            else:
                self.expression(statement, env, closure, capture=False)

        self.module_scope = prior_scope
        self.state.env = prior_env


def _public_binding(value, *, constructed=False):
    """Publish only existing public fact shapes; keep owner graphs private."""
    kind = value.get("kind")
    if kind in {"local", "builtin", "receiver"}:
        return {"kind": kind, "symbol": value["symbol"]}
    if kind == "import":
        # A private target path is mutation provenance, not an import alias.
        if "target_members" in value:
            return dict(UNKNOWN)
        result = {key: value[key] for key in ("kind", "module", "name")}
        if "modules" in value:
            result["modules"] = list(value["modules"])
        return result
    if kind == "unresolved":
        return {
            key: value[key]
            for key in ("kind", "reason", "line", "column")
            if key in value
        }
    if kind == "constructed-receiver" and constructed:
        constructor = value["constructor"]
        root = _public_binding(constructor["root_binding"])
        if root["kind"] not in {"local", "import"}:
            return dict(UNKNOWN)
        return {
            "kind": kind,
            "constructor": {
                "root_binding": root,
                "members": list(constructor["members"]),
                "line": constructor["line"],
                "column": constructor["column"],
            },
            "member": value["member"],
            "receiver_origin": value["receiver_origin"],
        }
    return dict(UNKNOWN)


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
                    _import_mutation_affects(constructor, fact["member"], mutation)
                    for mutation in analyzer.import_mutations
                ):
                    analyzer.calls[id(node)] = _unresolved(
                        node, "constructor-member-replaced"
                    )
                else:
                    root = constructor["root_binding"]
                    for scope, effects in analyzer.deferred_effects.items():
                        if scope == analyzer.call_scopes.get(id(node)):
                            continue
                        members = (
                            effects.class_mutations.get(root.get("symbol"), set())
                            if root.get("kind") == "local"
                            else set()
                        )
                        if (
                            "*" in members
                            or fact["member"] in members
                            or members & _DISPATCH_SLOTS
                            or any(
                                _import_mutation_affects(
                                    constructor, fact["member"], mutation
                                )
                                for mutation in effects.import_mutations
                            )
                        ):
                            analyzer.calls[id(node)] = _unresolved(
                                node, "constructor-member-replaced"
                            )
                            break
    module = {
        name: dict(UNKNOWN)
        if name in analyzer.state.export_invalidations
        else _public_binding(value)
        for name, value in analyzer.module.items()
    }
    calls = {
        key: _public_binding(value, constructed=True)
        for key, value in analyzer.calls.items()
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
    return PythonBindings(module, calls, classes)


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
                and (
                    "column" not in call
                    or type(call["column"]) is int
                    and call["column"] >= 0
                )
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
