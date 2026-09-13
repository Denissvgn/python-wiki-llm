"""Resolve captured Go call bindings only within evidenced package scopes."""

from __future__ import annotations

from pathlib import PurePosixPath


def attach_go_receiver_methods(inventory: dict) -> None:
    """Project per-file facts after cache/chunk merging, never into cached facts."""
    classes = {}
    for path, data in inventory.items():
        if data.get("language") != "go":
            continue
        scope = (PurePosixPath(path).parent, data.get("go_package"))
        for cls in data.get("classes", []):
            classes.setdefault((*scope, cls["name"]), []).append((path, cls))
    for path, data in inventory.items():
        if data.get("language") != "go":
            continue
        scope = (PurePosixPath(path).parent, data.get("go_package"))
        remaining = []
        for function in data.get("functions", []):
            owners = (
                classes.get((*scope, function.get("receiver")), [])
                if function.get("receiver")
                else []
            )
            if len(owners) != 1:
                remaining.append(function)
                continue
            owner_path, cls = owners[0]
            method = {
                key: value for key, value in function.items() if key != "receiver"
            }
            if owner_path != path:
                method["source_file"] = path
            cls.setdefault("methods", []).append(method)
        data["functions"] = remaining
    for owners in classes.values():
        for path, cls in owners:
            if "methods" in cls:
                cls["methods"].sort(
                    key=lambda method: (
                        method.get("source_file", path),
                        method.get("line", 0),
                        method["name"],
                    )
                )


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
            if fn_symbol == symbol and (kind != "import" or fn.get("exported") is True):
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
