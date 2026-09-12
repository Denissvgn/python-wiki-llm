"""Portable, explicit change selection and shared source-to-page mapping."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from typing import Mapping

from .bootstrap_runtime import (
    build_entity_occurrence_page_map,
    build_entity_page_map,
    build_module_page_map,
)
from .extraction_service import _git_name_status_paths, _partition_snapshot_git_changes


def portable_path(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Changed paths must be strings")
    value = value.replace("\\", "/")
    if value.startswith("./"):
        value = value[2:]
    if (
        not value
        or value.startswith("/")
        or re.match(r"^[A-Za-z]:", value)
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise ValueError("Changed paths must be normalized source-relative paths")
    return value


def validate_changes(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("changes must be an object")
    mode = value.get("mode")
    fields = {
        "paths": {"mode", "paths"},
        "range": {"mode", "base", "head"},
        "staged": {"mode"},
    }
    if not isinstance(mode, str) or mode not in fields or set(value) != fields[mode]:
        raise ValueError("changes must specify paths, staged, or a base/head range")
    if mode == "paths":
        if not isinstance(value["paths"], list):
            raise ValueError("changes.paths must be an array")
        return {
            "mode": mode,
            "paths": sorted({portable_path(p) for p in value["paths"]}),
        }
    if mode == "range":
        for field in ("base", "head"):
            ref = value[field]
            if (
                not isinstance(ref, str)
                or not ref
                or ref.startswith("-")
                or any(ord(c) < 32 for c in ref)
            ):
                raise ValueError(f"changes.{field} must be a Git revision")
    return dict(value)


def changes_from_args(args) -> dict | None:
    base, head = getattr(args, "base", None), getattr(args, "head", None)
    staged, paths = getattr(args, "staged", False), getattr(args, "changed_path", None)
    if sum((bool(base or head), bool(staged), paths is not None)) > 1:
        raise ValueError("Choose one of --base/--head, --staged, or --changed-path")
    if base or head:
        return validate_changes({"mode": "range", "base": base, "head": head})
    if staged:
        return {"mode": "staged"}
    if paths is not None:
        return validate_changes({"mode": "paths", "paths": paths})
    return None


def _git(root, *arguments) -> str:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=30,
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("Could not resolve the requested Git changes") from exc


def source_relative_paths(paths, root, *, prefix=None) -> list[str]:
    """Map repo-relative Git/patch paths through an exact source-root prefix."""
    if prefix is None:
        try:
            prefix = _git(root, "rev-parse", "--show-prefix").strip()
        except ValueError:
            prefix = ""
    result = set()
    for raw in paths:
        path = portable_path(raw)
        if prefix:
            if not path.startswith(prefix):
                continue
            path = path[len(prefix) :]
        result.add(path)
    return sorted(result)


def select_changes(root, request, *, snapshot=None) -> dict:
    request = validate_changes(request)
    provenance = dict(request)
    if request["mode"] == "paths":
        paths = request["paths"]
    else:
        args = ["diff", "--name-status", "-z", "--no-ext-diff", "--no-textconv"]
        if request["mode"] == "range":
            identities = {
                field: _git(
                    root,
                    "rev-parse",
                    "--verify",
                    "--end-of-options",
                    f"{request[field]}^{{commit}}",
                ).strip()
                for field in ("base", "head")
            }
            provenance["commits"] = identities
            args += [identities["base"], identities["head"]]
        else:
            args.append("--cached")
            provenance["index_id"] = (
                "sha256:"
                + hashlib.sha256(
                    _git(root, "ls-files", "--stage", "-z").encode("utf-8")
                ).hexdigest()
            )
        paths = source_relative_paths(
            _git_name_status_paths(_git(root, *args, "--")), root
        )
    boundary = False
    if snapshot is not None:
        paths, boundary = _partition_snapshot_git_changes(paths, snapshot)
        if boundary:
            paths = sorted(set(paths) | set(snapshot.all_source_paths))
    paths = sorted(set(paths))
    return {
        "request": provenance,
        "paths": paths,
        "path_basis": "source-root",
        "selection_boundary_changed": boundary,
        "paths_id": "sha256:"
        + hashlib.sha256(
            json.dumps(paths, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }


def patch_paths(text: str) -> list[str]:
    """Include both sides of renames/deletions, including Git's C quoting."""
    paths = set()
    for line in text.splitlines():
        for prefix in ("--- ", "+++ ", "rename from ", "rename to "):
            if not line.startswith(prefix):
                continue
            value = line[len(prefix) :]
            if value.startswith('"'):
                try:
                    # Git quotes UTF-8 bytes with octal escapes.
                    value = ast.literal_eval(value).encode("latin-1").decode("utf-8")
                except (ValueError, SyntaxError, UnicodeError):
                    raise ValueError("Malformed quoted patch path") from None
            else:
                value = value.split("\t", 1)[0]
            if value == "/dev/null":
                continue
            if prefix in {"--- ", "+++ "} and value.startswith(("a/", "b/")):
                value = value[2:]
            paths.add(portable_path(value))
            break
    return sorted(paths)


def affected_page_map(
    paths, inventory: Mapping, surface_pages=()
) -> dict[str, list[str]]:
    """Map exact sources to canonical pages; never match ambiguous suffixes."""
    inventory = dict(inventory)
    modules = build_module_page_map(inventory)
    entities = build_entity_page_map(inventory)
    occurrences = build_entity_occurrence_page_map(inventory, modules)
    mapped = {path: set() for path in sorted(set(paths))}
    for path in mapped:
        if path not in inventory:
            continue
        mapped[path].add(f"modules/{modules[path]}.md")
        seen = {}
        for item in inventory[path].get("classes", []):
            name = item["name"]
            seen[name] = seen.get(name, 0) + 1
            page = occurrences.get((name, path, seen[name]), entities[(name, path)])
            mapped[path].add(f"entities/{page}.md")
    for page in surface_pages:
        source, target = page.get("source_path"), page.get("canonical_path")
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        try:
            source, target = portable_path(source), portable_path(target)
        except ValueError:
            continue
        if source in mapped:
            mapped[source].add(target)
    return {path: sorted(pages) for path, pages in mapped.items()}
