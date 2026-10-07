"""Shared Python call resolution using captured lexical binding evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from copy import deepcopy

from .immutable import freeze
from ..extractors.python_bindings import (
    valid_python_constructor_facts,
    CONSTRUCTOR_DISPATCH_VERSION,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .imports import ModulePathResolver


@dataclass(frozen=True)
class PythonCallContext:
    callable: dict
    call_index: int
    resolver: ModulePathResolver
    class_name: str | None = None


@dataclass(frozen=True)
class PythonCallDecision:
    file: str | None
    symbol: str
    kind: str
    candidates: tuple[Mapping, ...] = ()
    reason: str | None = None
    location: Mapping | None = None
    constructor: Mapping | None = None

    def __post_init__(self):
        for field in ("candidates", "location", "constructor"):
            object.__setattr__(self, field, freeze(deepcopy(getattr(self, field))))

    def as_tuple(self):
        return (
            self.file,
            self.symbol,
            self.kind,
            [deepcopy(dict(candidate)) for candidate in self.candidates],
        )

    def metadata(self):
        value = {}
        for field in ("reason", "location", "constructor"):
            item = getattr(self, field)
            if item is not None:
                value[field] = deepcopy(item)
        if self.candidates:
            value["candidates"] = [deepcopy(candidate) for candidate in self.candidates]
        if self.kind == "ambiguous":
            value["resolution"] = "ambiguous"
        return value


def _declarations(data: Mapping, name: str):
    records = [
        fn
        for fn in data.get("functions", [])
        if isinstance(fn, Mapping) and fn.get("name") == name
    ]
    for cls in data.get("classes", []):
        if not isinstance(cls, Mapping):
            continue
        if cls.get("name") == name:
            records.append(cls)
        records.extend(
            method
            for method in cls.get("methods", [])
            if isinstance(method, Mapping)
            and f"{cls.get('name')}.{method.get('name')}" == name
        )
    return records


def _declared_symbol(data: Mapping, name: str) -> bool:
    return bool(_declarations(data, name))


def _module_binding(data: Mapping, name: str) -> dict:
    bindings = data.get("python_bindings")
    if isinstance(bindings, Mapping):
        binding = bindings.get(name)
        return dict(binding) if isinstance(binding, Mapping) else {"kind": "unresolved"}
    # Legacy inventories have no lexical facts. Only direct declarations and
    # module-scope imports are justified; never borrow another file's symbols.
    if _declared_symbol(data, name):
        return {"kind": "local", "symbol": name}
    matches = []
    for record in data.get("imports", []):
        if record.get("scope") in {"deferred", "type_checking"}:
            continue
        module = record.get("module", "")
        imported = record.get("name", "")
        if record.get("type") == "import":
            visible = imported.split(".", 1)[0]
            binding = {
                "kind": "import",
                "module": module if imported != module else visible,
                "name": "",
                "modules": [module],
            }
        else:
            visible = record.get("alias") or imported
            binding = {"kind": "import", "module": module, "name": imported}
        if visible == name:
            matches.append(binding)
    return matches[0] if len(matches) == 1 else {"kind": "unresolved"}


class _PythonCallResolver:
    def __init__(
        self, resolver: ModulePathResolver, fallback: str, *, constructor_mode=False
    ):
        self.resolver = resolver
        self.inventory = resolver.inventory
        self.fallback = fallback
        self.visited: set[tuple] = set()
        self.constructor_mode = constructor_mode
        self.invalid_constructor_authority = False

    def unknown(self, kind="unresolved"):
        return None, self.fallback, kind, []

    def binding(self, binding: Mapping, tail: list[str], filepath: str):
        key = (filepath, repr(sorted(binding.items())), tuple(tail))
        if key in self.visited or len(self.visited) >= 32:
            return self.unknown()
        self.visited.add(key)
        kind = binding.get("kind")
        if kind == "builtin":
            return self.unknown("external")
        if kind in {"local", "receiver"}:
            symbol = str(binding.get("symbol") or "")
            if tail:
                symbol = ".".join((symbol, *tail))
            data = self.inventory.get(filepath, {})
            matches = _declarations(data, symbol)
            if len(matches) == 1:
                return filepath, symbol, "internal", []
            if len(matches) > 1:
                return (
                    None,
                    self.fallback,
                    "ambiguous",
                    [
                        {
                            "file": filepath,
                            "symbol": symbol,
                            **(
                                {"line": item["line"]}
                                if isinstance(item.get("line"), int)
                                else {}
                            ),
                        }
                        for item in matches
                    ],
                )
            return self.unknown()
        if kind != "import":
            return self.unknown()
        module = str(binding.get("module") or "")
        name = binding.get("name")
        if name:
            if name == "*":
                return self.unknown()
            return self.member(module, [str(name), *tail], filepath, child_import=True)
        if not tail:
            return self.unknown()
        qualified = ".".join((module, *tail))
        known_modules = [
            str(value)
            for value in binding.get("modules", [])
            if qualified.startswith(str(value) + ".")
        ]
        if known_modules:
            module = max(known_modules, key=len)
            tail = qualified[len(module) + 1 :].split(".")
        return self.member(module, tail, filepath)

    def member(
        self, module: str, members: list[str], origin: str, *, child_import=False
    ):
        candidates = self.resolver.candidates(module, origin)
        if len(candidates) > 1:
            return (
                None,
                self.fallback,
                "ambiguous",
                [
                    {"file": path, "symbol": ".".join(members)}
                    for path in sorted(candidates)
                ],
            )
        if len(candidates) == 1:
            target = next(iter(candidates))
            data = self.inventory[target]
            if self.constructor_mode and not valid_python_constructor_facts(data):
                self.invalid_constructor_authority = True
                return self.unknown()
            binding = _module_binding(data, members[0])
            binding_key = (target, repr(sorted(binding.items())), tuple(members[1:]))
            if binding.get("kind") != "unresolved" and binding_key not in self.visited:
                return self.binding(binding, members[1:], target)
            if (
                self.constructor_mode
                and binding.get("kind") == "unresolved"
                and members[0] in data.get("python_bindings", {})
            ):
                return self.unknown()
            # Only a from-import may load an otherwise unbound child module.
            # Dynamic module attributes cannot prove which object is returned.
            if not child_import or _declared_symbol(data, "__getattr__"):
                return self.unknown()
        if child_import:
            separator = "" if module.endswith(".") else "."
            child = f"{module}{separator}{members[0]}"
            child_candidates = self.resolver.candidates(child, origin)
            if child_candidates:
                if len(members) > 1:
                    return self.member(child, members[1:], origin)
                return self.unknown()  # modules themselves are not callable
        return self.unknown(
            "unresolved" if candidates or module.startswith(".") else "external"
        )


def _invocation_location(call, binding, filepath):
    location = {"source_path": filepath}
    for field, minimum in (("line", 1), ("column", 0)):
        value = binding.get(field, call.get(field))
        if type(value) is int and value >= minimum:
            location[field] = value
    return location


def resolve_python_call_decision(
    call: dict, filepath: str, data: dict, context: PythonCallContext
) -> PythonCallDecision:
    """Make one immutable static decision from captured lexical evidence."""
    name = call["name"]
    facts = context.callable.get("call_bindings")
    binding = None
    if isinstance(facts, list):
        if len(facts) != len(
            context.callable.get("calls", [])
        ) or not 0 <= context.call_index < len(facts):
            return PythonCallDecision(
                None,
                name,
                "unresolved",
                reason="call-binding-alignment-invalid",
                location=_invocation_location(call, {}, filepath),
            )
        binding = facts[context.call_index]
        if not isinstance(binding, Mapping):
            return PythonCallDecision(
                None,
                name,
                "unresolved",
                reason="call-binding-invalid",
                location=_invocation_location(call, {}, filepath),
            )
    if binding is not None and binding.get("kind") == "constructed-receiver":
        if not valid_python_constructor_facts(data):
            return PythonCallDecision(
                None,
                name,
                "unresolved",
                reason="constructor-facts-invalid",
                location=_invocation_location(call, {}, filepath),
            )
        constructor = {
            **dict(binding["constructor"]),
            "receiver_origin": binding["receiver_origin"],
            "source_path": filepath,
        }
        location = _invocation_location(call, {}, filepath)
        resolver = _PythonCallResolver(context.resolver, name, constructor_mode=True)
        target, owner, kind, candidates = resolver.binding(
            constructor["root_binding"], constructor["members"], filepath
        )

        def decision(
            reason, state="unresolved", target_file=None, symbol=name, matches=()
        ):
            return PythonCallDecision(
                target_file,
                symbol,
                state,
                tuple(matches),
                reason,
                location,
                constructor,
            )

        if kind != "internal" or target is None:
            if resolver.invalid_constructor_authority:
                return decision("constructor-dispatch-unavailable")
            return decision(
                "constructor-target-ambiguous"
                if kind == "ambiguous"
                else "constructor-source-unavailable",
                kind if kind == "ambiguous" else "unresolved",
                matches=candidates,
            )
        target_data = context.resolver.inventory[target]
        classes = [
            cls
            for cls in target_data.get("classes", [])
            if isinstance(cls, Mapping)
            and cls.get("name") == owner
            and cls.get("kind") != "type_alias"
        ]
        if len(classes) != 1:
            return decision(
                "constructor-not-class"
                if not classes
                else "constructor-class-ambiguous",
                "ambiguous" if classes else "unresolved",
            )
        cls = classes[0]
        if not valid_python_constructor_facts(target_data):
            return decision("constructor-dispatch-unavailable")
        dispatch = cls.get("python_constructor_dispatch")
        if (
            not isinstance(dispatch, Mapping)
            or dispatch.get("schema_version") != CONSTRUCTOR_DISPATCH_VERSION
        ):
            return decision("constructor-dispatch-unavailable")
        if dispatch.get("eligible") is not True:
            return decision("constructor-dispatch-unsupported")
        member = binding["member"]
        methods = [
            method
            for method in cls.get("methods", [])
            if isinstance(method, Mapping) and method.get("name") == member
        ]
        if len(methods) > 1:
            return decision(
                "constructor-method-ambiguous",
                "ambiguous",
                matches=[
                    {
                        "file": target,
                        "symbol": f"{owner}.{member}",
                        "line": method.get("line"),
                    }
                    for method in methods
                ],
            )
        if member in dispatch.get("blocked_members", []):
            return decision("constructor-member-replaced")
        if len(methods) != 1:
            return decision("constructor-method-unavailable")
        return decision(
            "constructed-receiver-resolved", "internal", target, f"{owner}.{member}"
        )
    expression = call.get("attr") or name
    parts = expression.split(".")
    if not all(part.isidentifier() for part in parts):
        reason = (
            binding.get("reason") if binding is not None else "call-binding-unavailable"
        )
        return PythonCallDecision(
            None,
            name,
            "unresolved",
            reason=reason,
            location=_invocation_location(call, binding or {}, filepath)
            if reason
            else None,
        )
    if binding is None:
        if context.class_name and parts[0] in {"self", "cls"} and len(parts) == 2:
            binding = {"kind": "receiver", "symbol": context.class_name}
        elif parts[0] in {
            param.get("name") for param in context.callable.get("params", [])
        }:
            binding = {"kind": "unresolved"}
        else:
            binding = _module_binding(data, parts[0])
    target, symbol, kind, candidates = _PythonCallResolver(
        context.resolver, name
    ).binding(binding, parts[1:], filepath)
    reason = binding.get("reason") if binding.get("kind") == "unresolved" else None
    if reason is None and facts is None and kind == "unresolved":
        reason = "call-binding-unavailable"
    return PythonCallDecision(
        target,
        symbol,
        kind,
        tuple(candidates),
        reason,
        _invocation_location(call, binding, filepath) if reason else None,
    )


def resolve_python_call(
    call: dict, filepath: str, data: dict, context: PythonCallContext
):
    """Retain the four-tuple compatibility adapter for the shared decision."""
    return resolve_python_call_decision(call, filepath, data, context).as_tuple()
