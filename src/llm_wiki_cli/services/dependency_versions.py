"""Lossless, scope-aware dependency version observations.

The legacy reconciliation contract intentionally keeps one convenient version
per package.  This module supplies the additive vulnerability-triage contract:
one deterministic record per declaration, selected resolution, or checksum
observation, retaining repository scope and ecosystem semantics.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..config import is_agent_worktree_path
from .contracts import DEPENDENCY_VERSION_DETAILS_SCHEMA_VERSION
from .source_snapshot import SourceSnapshot

try:  # Python 3.11+
    import tomllib  # type: ignore[reportMissingImports]
except ModuleNotFoundError:  # pragma: no cover - Python 3.9/3.10
    try:
        import tomli as tomllib  # type: ignore[reportMissingImports]
    except ModuleNotFoundError:  # pragma: no cover
        tomllib = None  # type: ignore[assignment]


_EXCLUDED_DIRS = frozenset(
    {
        ".cache",
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "env",
        "node_modules",
        "site-packages",
        "target",
        "venv",
        "vendor",
    }
)
_SOURCE_NAMES = frozenset(
    {
        "Cargo.lock",
        "Cargo.toml",
        "Pipfile",
        "Pipfile.lock",
        "go.mod",
        "go.sum",
        "package-lock.json",
        "package.json",
        "pnpm-lock.yaml",
        "poetry.lock",
        "pyproject.toml",
        "uv.lock",
    }
)
_SELECTION_STATES = {
    "selected": "selected",
    "observed": "observed_only",
    "declared": "unknown",
}
_PYTHON_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _normal_python(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _normal_rust(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _scope(root: Path, path: Path) -> str:
    relative = path.parent.relative_to(root).as_posix()
    return "." if relative == "." else relative


def _source_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _record(
    *,
    ecosystem: str,
    package: str,
    version: str | None,
    version_kind: str,
    selection_confidence: str,
    source_semantics: str,
    source_path: str,
    scope: str,
    declaration: str | None,
    reach: str,
    declared_as: str | None = None,
) -> dict[str, Any]:
    return {
        "ecosystem": ecosystem,
        "package": package,
        "version": version,
        "version_kind": version_kind,
        "selection_confidence": selection_confidence,
        "selection_state": _SELECTION_STATES[selection_confidence],
        "source_semantics": source_semantics,
        "source_path": source_path,
        "scope": scope,
        "declaration": declaration,
        "reach": reach,
        "declared_as": declared_as,
    }


def _record_sort_key(record: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        "" if record.get(key) is None else str(record.get(key))
        for key in (
            "ecosystem",
            "scope",
            "package",
            "selection_confidence",
            "version",
            "source_path",
            "declaration",
            "reach",
            "declared_as",
        )
    )


def _deduplicate(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, ...], dict[str, Any]] = {}
    for record in records:
        key = tuple(
            json.dumps(record.get(field), sort_keys=True)
            for field in sorted(record)
        )
        by_key.setdefault(key, record)
    return sorted(by_key.values(), key=_record_sort_key)


def _dependency_source_names(files: Iterable[str]) -> set[str]:
    return {
        value
        for value in files
        if value in _SOURCE_NAMES
        or (value.startswith("requirements") and value.endswith(".txt"))
    }


def _snapshot_sources(root: Path, snapshot: SourceSnapshot) -> list[Path]:
    paths: set[Path] = set()
    for marker in snapshot.package_markers:
        try:
            marker.abs_path.relative_to(root)
        except ValueError:
            continue
        if marker.abs_path.name in _dependency_source_names(
            [marker.abs_path.name]
        ):
            paths.add(marker.abs_path)

    rust_paths = snapshot.files_by_language.get("rust", ())
    candidate_directories = {root}
    for source_file in rust_paths:
        current = source_file.abs_path.parent
        while current == root or root in current.parents:
            candidate_directories.add(current)
            if current == root:
                break
            current = current.parent
    for directory in candidate_directories:
        cargo = directory / "Cargo.toml"
        if cargo.is_file():
            paths.add(cargo)

    for manifest in list(paths):
        siblings: tuple[str, ...]
        if manifest.name == "pyproject.toml":
            siblings = ("poetry.lock", "uv.lock", "Pipfile.lock")
        elif manifest.name.startswith("requirements"):
            siblings = ("pyproject.toml", "poetry.lock", "uv.lock")
        elif manifest.name == "package.json":
            siblings = ("package-lock.json", "pnpm-lock.yaml")
        elif manifest.name == "go.mod":
            siblings = ("go.sum",)
        elif manifest.name == "Cargo.toml":
            siblings = ("Cargo.lock",)
        else:
            siblings = ()
        for sibling_name in siblings:
            sibling = manifest.parent / sibling_name
            if sibling.is_file():
                paths.add(sibling)
    return sorted(paths, key=lambda path: _source_path(root, path))


def _walk_sources(root: Path) -> list[Path]:
    paths: list[Path] = []
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in _EXCLUDED_DIRS
            and not is_agent_worktree_path(
                (current_path / dirname).relative_to(root).as_posix()
            )
        ]
        selected = _dependency_source_names(filenames)
        paths.extend(current_path / filename for filename in selected)
    return sorted(paths, key=lambda path: _source_path(root, path))


def _load_toml(path: Path) -> dict[str, Any] | None:
    if tomllib is None:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        value = tomllib.loads(text)
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _constraint(value: object) -> tuple[str | None, str]:
    if isinstance(value, Mapping):
        value = value.get("version")
    if not isinstance(value, str):
        return None, "unknown"
    clean = value.strip()
    if not clean or clean == "*":
        return None, "unknown"
    exact = re.fullmatch(r"(?:==|=)?\s*(v?[0-9][^\s,;]*)", clean)
    if exact:
        return exact.group(1), "exact"
    return clean, "constraint"


def _python_requirement(spec: str) -> tuple[str, str | None, str]:
    clean = spec.split(";", 1)[0].strip()
    match = _PYTHON_NAME_RE.match(clean)
    if match is None:
        return "", None, "unknown"
    name = _normal_python(match.group(1))
    remainder = clean[match.end() :].strip()
    if remainder.startswith("["):
        closing = remainder.find("]")
        remainder = remainder[closing + 1 :].strip() if closing >= 0 else ""
    if remainder.startswith("@"):
        return name, None, "unknown"
    return (name, *_constraint(remainder))


def _append_python_declaration(
    records: list[dict[str, Any]],
    *,
    root: Path,
    path: Path,
    spec: str,
    declaration: str,
    source_semantics: str,
) -> bool:
    package, version, version_kind = _python_requirement(spec)
    if not package:
        return False
    records.append(
        _record(
            ecosystem="python",
            package=package,
            version=version,
            version_kind=version_kind,
            selection_confidence="declared",
            source_semantics=source_semantics,
            source_path=_source_path(root, path),
            scope=_scope(root, path),
            declaration=declaration,
            reach="direct",
        )
    )
    return True


def _python_pyproject_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
) -> int:
    data = _load_toml(path)
    if data is None:
        return 1
    malformed = 0
    project = data.get("project")
    if isinstance(project, Mapping):
        dependencies = project.get("dependencies", [])
        if isinstance(dependencies, list):
            for spec in dependencies:
                if not isinstance(spec, str) or not _append_python_declaration(
                    records,
                    root=root,
                    path=path,
                    spec=spec,
                    declaration="required",
                    source_semantics="python-project-declaration",
                ):
                    malformed += 1
        optional = project.get("optional-dependencies", {})
        if isinstance(optional, Mapping):
            for group in optional.values():
                if not isinstance(group, list):
                    malformed += 1
                    continue
                for spec in group:
                    if not isinstance(spec, str) or not _append_python_declaration(
                        records,
                        root=root,
                        path=path,
                        spec=spec,
                        declaration="optional",
                        source_semantics="python-extra-declaration",
                    ):
                        malformed += 1

    build_system = data.get("build-system")
    if isinstance(build_system, Mapping):
        requires = build_system.get("requires", [])
        if isinstance(requires, list):
            for spec in requires:
                if not isinstance(spec, str) or not _append_python_declaration(
                    records,
                    root=root,
                    path=path,
                    spec=spec,
                    declaration="build",
                    source_semantics="python-build-declaration",
                ):
                    malformed += 1

    tool = data.get("tool")
    poetry = tool.get("poetry") if isinstance(tool, Mapping) else None
    if isinstance(poetry, Mapping):
        sections: list[tuple[object, str, str]] = [
            (
                poetry.get("dependencies"),
                "required",
                "poetry-project-declaration",
            ),
            (
                poetry.get("dev-dependencies"),
                "dev",
                "poetry-dev-declaration",
            ),
        ]
        groups = poetry.get("group")
        if isinstance(groups, Mapping):
            for name, value in sorted(groups.items(), key=lambda item: str(item[0])):
                dependencies = (
                    value.get("dependencies") if isinstance(value, Mapping) else None
                )
                declaration = "dev" if str(name).lower() == "dev" else "optional"
                sections.append(
                    (
                        dependencies,
                        declaration,
                        "poetry-group-declaration",
                    )
                )
        for raw_section, declaration, semantics in sections:
            if raw_section is None:
                continue
            if not isinstance(raw_section, Mapping):
                malformed += 1
                continue
            for raw_name, raw_value in sorted(
                raw_section.items(), key=lambda item: str(item[0])
            ):
                package = _normal_python(str(raw_name))
                if package == "python":
                    continue
                version, version_kind = _constraint(raw_value)
                record_declaration = (
                    "optional"
                    if declaration == "required"
                    and isinstance(raw_value, Mapping)
                    and raw_value.get("optional") is True
                    else declaration
                )
                records.append(
                    _record(
                        ecosystem="python",
                        package=package,
                        version=version,
                        version_kind=version_kind,
                        selection_confidence="declared",
                        source_semantics=semantics,
                        source_path=_source_path(root, path),
                        scope=_scope(root, path),
                        declaration=record_declaration,
                        reach="direct",
                    )
                )
    return malformed


def _requirements_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
) -> int:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return 1
    malformed = 0
    lowered = path.name.lower()
    declaration = (
        "dev"
        if path.name != "requirements.txt"
        and any(value in lowered for value in ("dev", "test", "tests"))
        else "required"
    )
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(
            ("-r", "--requirement", "-c", "--constraint", "-e", "--editable")
        ):
            continue
        if line.startswith(("git+", "http://", "https://")):
            continue
        if not _append_python_declaration(
            records,
            root=root,
            path=path,
            spec=line,
            declaration=declaration,
            source_semantics="python-requirements-declaration",
        ):
            malformed += 1
    return malformed


def _selected_python_toml_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
    *,
    local_projects: Iterable[tuple[str, str, str | None]] = (),
) -> int:
    data = _load_toml(path)
    if data is None:
        return 1
    packages = data.get("package")
    if not isinstance(packages, list):
        return 1
    lock_scope = _scope(root, path)
    direct_scopes = _direct_package_scopes(records, "python", lock_scope)
    package_counts: dict[str, int] = {}
    for value in packages:
        if (
            not isinstance(value, Mapping)
            or not isinstance(value.get("name"), str)
            or not isinstance(value.get("version"), str)
        ):
            continue
        package = _normal_python(str(value["name"]))
        if _is_local_project_selection(
            package,
            str(value["version"]),
            lock_scope=lock_scope,
            local_projects=local_projects,
        ):
            continue
        package_counts[package] = package_counts.get(package, 0) + 1
    malformed = 0
    for value in packages:
        if not isinstance(value, Mapping):
            malformed += 1
            continue
        name = value.get("name")
        version = value.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            malformed += 1
            continue
        package = _normal_python(name)
        if _is_local_project_selection(
            package,
            version,
            lock_scope=lock_scope,
            local_projects=local_projects,
        ):
            continue
        records.append(
            _record(
                ecosystem="python",
                package=package,
                version=version,
                version_kind="exact",
                selection_confidence="selected",
                source_semantics=(
                    "poetry-lock-selection"
                    if path.name == "poetry.lock"
                    else "uv-lock-selection"
                ),
                source_path=_source_path(root, path),
                scope=lock_scope,
                declaration=None,
                reach=_unstructured_lock_reach(
                    package,
                    lock_scope=lock_scope,
                    direct_scopes=direct_scopes,
                    selected_count=package_counts.get(package, 0),
                ),
            )
        )
    return malformed


def _pipfile_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
) -> int:
    data = _load_json(path)
    if data is None:
        return 1
    direct = _direct_packages(records, "python", _scope(root, path))
    malformed = 0
    for block_name in ("default", "develop"):
        block = data.get(block_name, {})
        if not isinstance(block, Mapping):
            malformed += 1
            continue
        for raw_name, raw_value in sorted(
            block.items(), key=lambda item: str(item[0])
        ):
            version, version_kind = _constraint(raw_value)
            package = _normal_python(str(raw_name))
            if version is None:
                malformed += 1
                continue
            records.append(
                _record(
                    ecosystem="python",
                    package=package,
                    version=version,
                    version_kind=version_kind,
                    selection_confidence="selected",
                    source_semantics="pipfile-lock-selection",
                    source_path=_source_path(root, path),
                    scope=_scope(root, path),
                    declaration=None,
                    reach="direct" if package in direct else "transitive",
                )
            )
    return malformed


def _pipfile_manifest_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
) -> int:
    data = _load_toml(path)
    if data is None:
        return 1
    malformed = 0
    for section_name, declaration in (
        ("packages", "required"),
        ("dev-packages", "dev"),
    ):
        section = data.get(section_name, {})
        if not isinstance(section, Mapping):
            malformed += 1
            continue
        for raw_name, raw_value in sorted(
            section.items(), key=lambda item: str(item[0])
        ):
            package = _normal_python(str(raw_name))
            version, version_kind = _constraint(raw_value)
            records.append(
                _record(
                    ecosystem="python",
                    package=package,
                    version=version,
                    version_kind=version_kind,
                    selection_confidence="declared",
                    source_semantics=f"pipfile-{section_name}-declaration",
                    source_path=_source_path(root, path),
                    scope=_scope(root, path),
                    declaration=declaration,
                    reach="direct",
                )
            )
    return malformed


def _direct_packages(
    records: Iterable[Mapping[str, Any]], ecosystem: str, scope: str
) -> set[str]:
    return {
        str(record["package"])
        for record in records
        if record.get("ecosystem") == ecosystem
        and record.get("scope") == scope
        and record.get("selection_confidence") == "declared"
        and record.get("reach") == "direct"
    }


def _scope_is_within(candidate: str, parent: str) -> bool:
    return (
        parent == "."
        or candidate == parent
        or candidate.startswith(f"{parent}/")
    )


def _direct_package_scopes(
    records: Iterable[Mapping[str, Any]],
    ecosystem: str,
    lock_scope: str,
) -> dict[str, set[str]]:
    """Return declarations a lock may cover without claiming workspace ownership."""

    scopes: dict[str, set[str]] = {}
    for record in records:
        record_scope = str(record.get("scope", ""))
        if (
            record.get("ecosystem") != ecosystem
            or record.get("selection_confidence") != "declared"
            or record.get("reach") != "direct"
            or not _scope_is_within(record_scope, lock_scope)
        ):
            continue
        scopes.setdefault(str(record["package"]), set()).add(record_scope)
    return scopes


def _unstructured_lock_reach(
    package: str,
    *,
    lock_scope: str,
    direct_scopes: Mapping[str, set[str]],
    selected_count: int = 1,
) -> str:
    """Classify a flat lock row conservatively across workspace scopes."""

    package_scopes = direct_scopes.get(package, set())
    if lock_scope in package_scopes:
        return "direct" if selected_count == 1 else "unknown"
    if package_scopes:
        return "unknown"
    return "transitive"


def _local_project_identities(
    root: Path,
    paths: Iterable[Path],
    *,
    ecosystem: str,
) -> tuple[tuple[str, str, str | None], ...]:
    """Read local package identities from already-discovered manifests."""

    identities: set[tuple[str, str, str | None]] = set()
    for path in paths:
        if ecosystem == "python" and path.name == "pyproject.toml":
            data = _load_toml(path)
            if data is None:
                continue
            candidates: list[Mapping[str, Any]] = []
            project = data.get("project")
            if isinstance(project, Mapping):
                candidates.append(project)
            tool = data.get("tool")
            poetry = tool.get("poetry") if isinstance(tool, Mapping) else None
            if isinstance(poetry, Mapping):
                candidates.append(poetry)
            for candidate in candidates:
                name = candidate.get("name")
                version = candidate.get("version")
                if isinstance(name, str) and name.strip():
                    identities.add(
                        (
                            _scope(root, path),
                            _normal_python(name),
                            version.strip()
                            if isinstance(version, str) and version.strip()
                            else None,
                        )
                    )
        elif ecosystem == "rust" and path.name == "Cargo.toml":
            data = _load_toml(path)
            package = data.get("package") if isinstance(data, Mapping) else None
            if not isinstance(package, Mapping):
                continue
            name = package.get("name")
            version = package.get("version")
            if isinstance(name, str) and name.strip():
                identities.add(
                    (
                        _scope(root, path),
                        _normal_rust(name),
                        version.strip()
                        if isinstance(version, str) and version.strip()
                        else None,
                    )
                )
    return tuple(sorted(identities))


def _is_local_project_selection(
    package: str,
    version: str,
    *,
    lock_scope: str,
    local_projects: Iterable[tuple[str, str, str | None]],
) -> bool:
    return any(
        _scope_is_within(project_scope, lock_scope)
        and project_package == package
        and (project_version is None or project_version == version)
        for project_scope, project_package, project_version in local_projects
    )


def _typescript_manifest_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
) -> int:
    data = _load_json(path)
    if data is None:
        return 1
    malformed = 0
    sections = (
        ("dependencies", "required"),
        ("peerDependencies", "required"),
        ("optionalDependencies", "optional"),
        ("devDependencies", "dev"),
    )
    for section_name, declaration in sections:
        section = data.get(section_name, {})
        if not isinstance(section, Mapping):
            malformed += 1
            continue
        for raw_name, raw_version in sorted(
            section.items(), key=lambda item: str(item[0])
        ):
            package = str(raw_name).lower()
            version, version_kind = _constraint(raw_version)
            records.append(
                _record(
                    ecosystem="typescript",
                    package=package,
                    version=version,
                    version_kind=version_kind,
                    selection_confidence="declared",
                    source_semantics=f"npm-{section_name}-declaration",
                    source_path=_source_path(root, path),
                    scope=_scope(root, path),
                    declaration=declaration,
                    reach="direct",
                )
            )
    return malformed


def _package_lock_package_name(package_path: str, metadata: Mapping) -> str:
    normalized = package_path.strip("/")
    if "node_modules/" not in normalized:
        return ""
    raw_name = metadata.get("name")
    if isinstance(raw_name, str) and raw_name:
        return raw_name.lower()
    return normalized.rsplit("node_modules/", 1)[1].strip("/").lower()


def _package_lock_install_scope(package_path: str, lock_scope: str) -> str:
    prefix = package_path.strip("/").split("node_modules/", 1)[0].strip("/")
    if not prefix:
        return lock_scope
    return prefix if lock_scope == "." else f"{lock_scope}/{prefix}"


def _package_lock_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
) -> int:
    data = _load_json(path)
    if data is None:
        return 1
    lock_scope = _scope(root, path)
    direct_scopes = _direct_package_scopes(records, "typescript", lock_scope)
    malformed = 0
    packages = data.get("packages")
    if isinstance(packages, Mapping):
        for package_path, metadata in sorted(
            packages.items(), key=lambda item: str(item[0])
        ):
            if not isinstance(package_path, str) or not isinstance(metadata, Mapping):
                malformed += 1
                continue
            package = _package_lock_package_name(package_path, metadata)
            version = metadata.get("version")
            if not package:
                continue
            if not isinstance(version, str) or not version:
                malformed += 1
                continue
            root_level = package_path.strip("/").count("node_modules/") == 1
            installed_scope = _package_lock_install_scope(
                package_path,
                lock_scope,
            )
            package_scopes = direct_scopes.get(package, set())
            records.append(
                _record(
                    ecosystem="typescript",
                    package=package,
                    version=version,
                    version_kind="exact",
                    selection_confidence="selected",
                    source_semantics="npm-package-lock-selection",
                    source_path=_source_path(root, path),
                    scope=lock_scope,
                    declaration=None,
                    reach=(
                        "direct"
                        if root_level and installed_scope in package_scopes
                        else "unknown"
                        if root_level and package_scopes
                        else "transitive"
                    ),
                )
            )
        return malformed

    dependencies = data.get("dependencies")
    if not isinstance(dependencies, Mapping):
        return 1

    def visit(values: Mapping, depth: int) -> None:
        nonlocal malformed
        for raw_name, metadata in sorted(
            values.items(), key=lambda item: str(item[0])
        ):
            if not isinstance(metadata, Mapping):
                malformed += 1
                continue
            package = str(raw_name).lower()
            version = metadata.get("version")
            if isinstance(version, str) and version:
                records.append(
                    _record(
                        ecosystem="typescript",
                        package=package,
                        version=version,
                        version_kind="exact",
                        selection_confidence="selected",
                        source_semantics="npm-package-lock-selection",
                        source_path=_source_path(root, path),
                        scope=lock_scope,
                        declaration=None,
                        reach=(
                            "direct"
                            if (
                                depth == 0
                                and lock_scope
                                in direct_scopes.get(package, set())
                            )
                            else "unknown"
                            if depth == 0 and direct_scopes.get(package)
                            else "transitive"
                        ),
                    )
                )
            else:
                malformed += 1
            nested = metadata.get("dependencies")
            if isinstance(nested, Mapping):
                visit(nested, depth + 1)

    visit(dependencies, 0)
    return malformed


def _pnpm_key(value: str) -> tuple[str, str]:
    key = value.strip().strip("'\"")
    if not key.endswith(":"):
        return "", ""
    key = key[:-1].strip().strip("'\"").lstrip("/")
    key = key.split("(", 1)[0]
    if key.startswith("@") and key.count("@") == 1 and key.count("/") >= 2:
        name, version = key.rsplit("/", 1)
    elif "@" in key:
        name, version = key.rsplit("@", 1)
    elif "/" in key:
        name, version = key.rsplit("/", 1)
    else:
        return "", ""
    if not name or not version or not version[0].isdigit():
        return "", ""
    return name.lower(), version


def _pnpm_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
) -> int:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return 1
    direct = _direct_packages(records, "typescript", _scope(root, path))
    malformed = 0
    in_packages = False
    packages_indent = 0
    package_content = 0
    emitted = 0
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        if not in_packages:
            if stripped == "packages:":
                in_packages = True
                packages_indent = indent
            continue
        if indent <= packages_indent:
            break
        package_content += 1
        package, version = _pnpm_key(stripped)
        if not package:
            continue
        emitted += 1
        records.append(
            _record(
                ecosystem="typescript",
                package=package,
                version=version,
                version_kind="exact",
                selection_confidence="selected",
                source_semantics="pnpm-lock-selection",
                source_path=_source_path(root, path),
                scope=_scope(root, path),
                declaration=None,
                reach="unknown",
            )
        )
    if in_packages and package_content and emitted == 0:
        malformed += 1
    return malformed


def _go_mod_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
) -> int:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return 1
    malformed = 0
    in_require = False
    for raw in lines:
        code, _, comment = raw.partition("//")
        clean = code.strip()
        if not clean:
            continue
        if in_require and clean.startswith(")"):
            in_require = False
            continue
        if clean.startswith("require"):
            clean = clean[len("require") :].strip()
            if clean.startswith("("):
                in_require = True
                continue
        elif not in_require:
            continue
        tokens = clean.split()
        if len(tokens) < 2:
            malformed += 1
            continue
        package, version = tokens[0].strip('"'), tokens[1].strip('"')
        indirect = "indirect" in comment.split()
        records.append(
            _record(
                ecosystem="go",
                package=package,
                version=version,
                version_kind="exact",
                selection_confidence="selected",
                source_semantics="go-mod-selection",
                source_path=_source_path(root, path),
                scope=_scope(root, path),
                declaration="required",
                reach="transitive" if indirect else "direct",
            )
        )
    return malformed


def _go_sum_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
) -> int:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return 1
    malformed = 0
    for raw in lines:
        tokens = raw.split()
        if not tokens:
            continue
        if len(tokens) < 3:
            malformed += 1
            continue
        package, version = tokens[0], tokens[1]
        if version.endswith("/go.mod"):
            version = version[: -len("/go.mod")]
        records.append(
            _record(
                ecosystem="go",
                package=package,
                version=version,
                version_kind="exact",
                selection_confidence="observed",
                source_semantics="go-checksum-observation",
                source_path=_source_path(root, path),
                scope=_scope(root, path),
                declaration=None,
                reach="unknown",
            )
        )
    return malformed


def _rust_manifest_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
) -> int:
    data = _load_toml(path)
    if data is None:
        return 1
    malformed = 0
    sections = (
        ("dependencies", "required"),
        ("dev-dependencies", "dev"),
        ("build-dependencies", "build"),
    )
    for section_name, declaration in sections:
        section = data.get(section_name, {})
        if not isinstance(section, Mapping):
            malformed += 1
            continue
        for raw_name, raw_value in sorted(
            section.items(), key=lambda item: str(item[0])
        ):
            declared_as = _normal_rust(str(raw_name))
            actual_name = (
                _normal_rust(str(raw_value.get("package")))
                if isinstance(raw_value, Mapping) and raw_value.get("package")
                else declared_as
            )
            version, version_kind = _constraint(raw_value)
            record_declaration = (
                "optional"
                if declaration == "required"
                and isinstance(raw_value, Mapping)
                and raw_value.get("optional") is True
                else declaration
            )
            records.append(
                _record(
                    ecosystem="rust",
                    package=actual_name,
                    version=version,
                    version_kind=version_kind,
                    selection_confidence="declared",
                    source_semantics=f"cargo-{section_name}-declaration",
                    source_path=_source_path(root, path),
                    scope=_scope(root, path),
                    declaration=record_declaration,
                    reach="direct",
                    declared_as=(
                        declared_as if declared_as != actual_name else None
                    ),
                )
            )
    return malformed


def _cargo_lock_records(
    root: Path,
    path: Path,
    records: list[dict[str, Any]],
    *,
    local_projects: Iterable[tuple[str, str, str | None]] = (),
) -> int:
    data = _load_toml(path)
    if data is None:
        return 1
    packages = data.get("package")
    if not isinstance(packages, list):
        return 1
    lock_scope = _scope(root, path)
    direct_scopes = _direct_package_scopes(records, "rust", lock_scope)
    package_counts: dict[str, int] = {}
    for value in packages:
        if (
            not isinstance(value, Mapping)
            or not isinstance(value.get("name"), str)
            or not isinstance(value.get("version"), str)
        ):
            continue
        package = _normal_rust(str(value["name"]))
        if (
            not isinstance(value.get("source"), str)
            and _is_local_project_selection(
                package,
                str(value["version"]),
                lock_scope=lock_scope,
                local_projects=local_projects,
            )
        ):
            continue
        package_counts[package] = package_counts.get(package, 0) + 1
    malformed = 0
    for value in packages:
        if not isinstance(value, Mapping):
            malformed += 1
            continue
        name = value.get("name")
        version = value.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            malformed += 1
            continue
        package = _normal_rust(name)
        if (
            not isinstance(value.get("source"), str)
            and _is_local_project_selection(
                package,
                version,
                lock_scope=lock_scope,
                local_projects=local_projects,
            )
        ):
            continue
        records.append(
            _record(
                ecosystem="rust",
                package=package,
                version=version,
                version_kind="exact",
                selection_confidence="selected",
                source_semantics="cargo-lock-selection",
                source_path=_source_path(root, path),
                scope=lock_scope,
                declaration=None,
                reach=_unstructured_lock_reach(
                    package,
                    lock_scope=lock_scope,
                    direct_scopes=direct_scopes,
                    selected_count=package_counts.get(package, 0),
                ),
            )
        )
    return malformed


def build_dependency_version_details(
    project_root: str | Path = ".",
    *,
    source_snapshot: SourceSnapshot | None = None,
) -> dict[str, Any]:
    """Return the additive complete, scoped dependency-version contract."""
    root = Path(project_root).resolve()
    paths = (
        _snapshot_sources(root, source_snapshot)
        if source_snapshot is not None
        else _walk_sources(root)
    )
    records: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    malformed = 0

    declarations = [
        path
        for path in paths
        if path.name
        in {"Pipfile", "pyproject.toml", "package.json", "go.mod", "Cargo.toml"}
        or (path.name.startswith("requirements") and path.name.endswith(".txt"))
    ]
    resolutions = [path for path in paths if path not in declarations]
    local_python_projects = _local_project_identities(
        root,
        declarations,
        ecosystem="python",
    )
    local_rust_projects = _local_project_identities(
        root,
        declarations,
        ecosystem="rust",
    )

    def evaluate(path: Path) -> int:
        if path.name == "pyproject.toml":
            return _python_pyproject_records(root, path, records)
        if path.name == "Pipfile":
            return _pipfile_manifest_records(root, path, records)
        if path.name.startswith("requirements") and path.name.endswith(".txt"):
            return _requirements_records(root, path, records)
        if path.name in {"poetry.lock", "uv.lock"}:
            return _selected_python_toml_records(
                root,
                path,
                records,
                local_projects=local_python_projects,
            )
        if path.name == "Pipfile.lock":
            return _pipfile_records(root, path, records)
        if path.name == "package.json":
            return _typescript_manifest_records(root, path, records)
        if path.name == "package-lock.json":
            return _package_lock_records(root, path, records)
        if path.name == "pnpm-lock.yaml":
            return _pnpm_records(root, path, records)
        if path.name == "go.mod":
            return _go_mod_records(root, path, records)
        if path.name == "go.sum":
            return _go_sum_records(root, path, records)
        if path.name == "Cargo.toml":
            return _rust_manifest_records(root, path, records)
        if path.name == "Cargo.lock":
            return _cargo_lock_records(
                root,
                path,
                records,
                local_projects=local_rust_projects,
            )
        return 0

    for path in (*declarations, *resolutions):
        before = len(records)
        omitted = evaluate(path)
        malformed += omitted
        if omitted:
            diagnostics.append(
                {
                    "source_path": _source_path(root, path),
                    "state": "partial" if len(records) > before else "malformed",
                    "reason": "unsupported-or-malformed-records",
                }
            )

    normalized = _deduplicate(records)
    limitations = [
        "declarations-do-not-prove-a-selected-version",
        "static-lock-analysis-does-not-claim-runtime-installation",
    ]
    if malformed:
        limitations.append("malformed-or-unsupported-version-records")
    if any(
        record["selection_confidence"] == "declared"
        and not any(
            selected["ecosystem"] == record["ecosystem"]
            and selected["scope"] == record["scope"]
            and selected["package"] == record["package"]
            and selected["selection_confidence"] == "selected"
            for selected in normalized
        )
        for record in normalized
    ):
        limitations.append("unknown-selection-without-lock-evidence")

    emitted = len(normalized)
    return {
        "schema_version": DEPENDENCY_VERSION_DETAILS_SCHEMA_VERSION,
        "records": normalized,
        "coverage": {
            "observed": emitted + malformed,
            "emitted": emitted,
            "omitted": malformed,
            "limit": None,
            "truncated": False,
            "limitations": sorted(limitations),
        },
        "diagnostics": sorted(
            diagnostics,
            key=lambda value: (
                value["source_path"],
                value["state"],
                value["reason"],
            ),
        ),
    }


__all__ = ["build_dependency_version_details"]
