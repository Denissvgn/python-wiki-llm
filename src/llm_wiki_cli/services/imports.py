from __future__ import annotations

import posixpath
from pathlib import Path


def module_path_candidates(module: str, importer_filepath: str, inventory: dict) -> set[str]:
    """Resolve an import module string to inventory file paths when possible."""
    if not module:
        return set()

    normalized = module.strip().strip('"').strip("'").replace("\\", "/")
    if not normalized:
        return set()

    importer_parent = Path(importer_filepath).parent
    candidate_stems: set[str] = set()
    has_relative_candidate = False

    if normalized.startswith(("./", "../")):
        rel = normalized
        while rel.startswith("./"):
            rel = rel[2:]
        if rel.startswith("../") or rel:
            candidate_stems.add(
                posixpath.normpath((importer_parent / rel).as_posix()).strip("/")
            )
            has_relative_candidate = True
    elif normalized.startswith("."):
        dot_count = len(normalized) - len(normalized.lstrip("."))
        remainder = normalized[dot_count:]
        base = importer_parent
        for _ in range(max(dot_count - 1, 0)):
            base = base.parent
        if remainder:
            candidate_stems.add(
                posixpath.normpath((base / remainder.replace(".", "/")).as_posix()).strip("/")
            )
        else:
            base_candidate = posixpath.normpath(base.as_posix()).strip("/")
            if base_candidate:
                candidate_stems.add(base_candidate)
                candidate_stems.add(f"{base_candidate}/__init__")
            else:
                candidate_stems.add("__init__")
        has_relative_candidate = True

    if not has_relative_candidate:
        module_path = normalized.replace("::", "/").replace(".", "/")
        clean_module_path = module_path.strip("/")
        if clean_module_path:
            candidate_stems.add(clean_module_path)
            if "/" not in clean_module_path:
                candidate_stems.add(Path(clean_module_path).name)

    matches: set[str] = set()
    for filepath in inventory:
        path_no_suffix = Path(filepath).with_suffix("").as_posix()
        path_parts = Path(filepath).parts
        stripped_src = (
            "/".join(path_parts[1:])
            if path_parts and path_parts[0] == "src"
            else filepath
        )
        stripped_src_no_suffix = Path(stripped_src).with_suffix("").as_posix()
        comparable = {path_no_suffix, stripped_src_no_suffix, Path(filepath).stem}
        for candidate in candidate_stems:
            candidate = candidate.strip("/")
            if not candidate:
                continue
            if (
                candidate in comparable
                or path_no_suffix.endswith(f"/{candidate}")
                or stripped_src_no_suffix.endswith(f"/{candidate}")
            ):
                matches.add(filepath)
    return matches
