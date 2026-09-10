"""Shared Python call resolution using captured lexical binding evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .imports import ModulePathResolver


@dataclass(frozen=True)
class PythonCallContext:
    callable: dict
    call_index: int
    resolver: ModulePathResolver
    class_name: str | None = None


def _declared_symbol(data: Mapping, name: str) -> bool:
    if any(fn.get("name") == name for fn in data.get("functions", [])):
        return True
    for cls in data.get("classes", []):
        if cls.get("name") == name:
            return True
        if any(
            f"{cls.get('name')}.{method.get('name')}" == name
            for method in cls.get("methods", [])
        ):
            return True
    return False


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
    def __init__(self, resolver: ModulePathResolver, fallback: str):
        self.resolver = resolver
        self.inventory = resolver.inventory
        self.fallback = fallback
        self.visited: set[tuple] = set()

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
            if _declared_symbol(data, symbol):
                return filepath, symbol, "internal", []
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
            binding = _module_binding(data, members[0])
            binding_key = (target, repr(sorted(binding.items())), tuple(members[1:]))
            if binding.get("kind") != "unresolved" and binding_key not in self.visited:
                return self.binding(binding, members[1:], target)
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


def resolve_python_call(
    call: dict, filepath: str, data: dict, context: PythonCallContext
):
    name = call["name"]
    expression = call.get("attr") or name
    parts = expression.split(".")
    if not all(part.isidentifier() for part in parts):
        return None, name, "unresolved", []
    facts = context.callable.get("call_bindings")
    if isinstance(facts, list):
        if len(facts) != len(context.callable.get("calls", [])):
            return None, name, "unresolved", []
        binding = facts[context.call_index]
        if not isinstance(binding, Mapping):
            return None, name, "unresolved", []
    elif context.class_name and parts[0] in {"self", "cls"} and len(parts) == 2:
        binding = {"kind": "receiver", "symbol": context.class_name}
    elif parts[0] in {
        param.get("name") for param in context.callable.get("params", [])
    }:
        binding = {"kind": "unresolved"}
    else:
        binding = _module_binding(data, parts[0])
    return _PythonCallResolver(context.resolver, name).binding(
        binding, parts[1:], filepath
    )
