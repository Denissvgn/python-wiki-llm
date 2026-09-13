"""Resolve captured Go call bindings only within evidenced package scopes."""

from __future__ import annotations

from pathlib import PurePosixPath


def resolve_go_call(call: dict, filepath: str, resolver) -> tuple:
    binding = call.get("go_binding") or {}
    kind = binding.get("kind")
    name = str(call.get("name") or "<dynamic>")
    inventory = resolver.inventory
    data = inventory[filepath]
    symbol = name
    if kind == "builtin":
        return None, name, "external", []
    if kind == "import":
        files = resolver.candidates(str(binding.get("module") or ""), filepath)
        if not files:
            module = str(binding.get("module") or "")
            internal = any(
                module == scope.module or module.startswith(scope.module + "/")
                for scope in resolver.go_module_scopes
            )
            return None, name, "unresolved" if internal else "external", []
    elif kind in {"package", "receiver"}:
        files = {
            path
            for path, other in inventory.items()
            if other.get("language") == "go"
            and other.get("go_package") == data.get("go_package")
            and PurePosixPath(path).parent == PurePosixPath(filepath).parent
        }
        if kind == "receiver":
            symbol = f"{binding.get('receiver')}.{name}"
    else:
        return None, name, "unresolved", []

    candidates = set()
    for path in files:
        other = inventory[path]
        for fn in other.get("functions", []):
            fn_symbol = (
                f"{fn['receiver']}.{fn['name']}" if fn.get("receiver") else fn["name"]
            )
            if fn_symbol == symbol and (kind != "import" or fn.get("exported", True)):
                candidates.add((path, symbol))
        if kind == "receiver":
            for cls in other.get("classes", []):
                if (
                    cls["name"] != binding.get("receiver")
                    or cls.get("kind") == "interface"
                ):
                    continue
                for method in cls.get("methods", []):
                    if method["name"] == name:
                        source = method.get("source_file", path)
                        if source in files:
                            candidates.add((source, symbol))
    ordered = [{"file": path, "symbol": target} for path, target in sorted(candidates)]
    if len(ordered) == 1:
        return ordered[0]["file"], symbol, "internal", []
    return None, symbol, "ambiguous" if ordered else "unresolved", ordered
