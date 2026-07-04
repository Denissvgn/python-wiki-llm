from __future__ import annotations

import re
from pathlib import Path

try:  # Python 3.11+
    import tomllib  # type: ignore[reportMissingImports]
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.9/3.10
    try:
        import tomli as tomllib  # type: ignore[reportMissingImports]
    except ModuleNotFoundError:  # pragma: no cover - dependency missing in ad-hoc envs
        tomllib = None

# Supported version file patterns in priority order
VERSION_PATTERNS = [
    ("pyproject.toml", re.compile(r"")),
    ("setup.cfg", re.compile(r"^(version\s*=\s*)(\d+\.\d+\.\d+)", re.MULTILINE)),
    (
        "package.json",
        re.compile(r'("version"\s*:\s*")(\d+\.\d+\.\d+)(")', re.MULTILINE),
    ),
    ("VERSION", re.compile(r"^(\d+\.\d+\.\d+)$", re.MULTILINE)),
]

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_TABLE_RE = re.compile(r"(?m)^\s*\[([^\]]+)\]\s*(?:#.*)?$")


def find_version_file(root: str = ".") -> Path | None:
    """Auto-detect the version file in a project root."""
    root_path = Path(root)
    for filename, _ in VERSION_PATTERNS:
        candidate = root_path / filename
        if candidate.exists():
            return candidate
    return None


def read_version(path: Path) -> str | None:
    """Parse X.Y.Z version from a detected file."""
    content = path.read_text(encoding="utf-8")
    if path.name == "pyproject.toml":
        return _read_pyproject_version(content)
    for filename, pattern in VERSION_PATTERNS:
        if path.name == filename:
            match = pattern.search(content)
            if match:
                # VERSION file has no prefix/suffix groups
                groups = match.groups()
                for g in groups:
                    if VERSION_RE.match(g):
                        return g
            break
    return None


def write_version(path: Path, new_version: str) -> None:
    """Update the version string in-place, preserving file format."""
    content = path.read_text(encoding="utf-8")
    if path.name == "pyproject.toml":
        updated = _write_pyproject_version(content, new_version, path)
        path.write_bytes(updated.encode("utf-8"))
        return

    original = content
    for filename, pattern in VERSION_PATTERNS:
        if path.name == filename:
            if filename == "VERSION":
                content = pattern.sub(new_version, content)
            else:

                def _replacer(m):
                    groups = list(m.groups())
                    for i, g in enumerate(groups):
                        if VERSION_RE.match(g):
                            groups[i] = new_version
                            break
                    return "".join(groups)

                content = pattern.sub(_replacer, content, count=1)
            break
    if content == original:
        raise ValueError(f"Version pattern not found in {path}")
    path.write_bytes(content.encode("utf-8"))


def _read_pyproject_version(text: str) -> str | None:
    if tomllib is not None:
        try:
            data = tomllib.loads(text)
        except Exception:
            data = {}
        project = data.get("project", {}) if isinstance(data, dict) else {}
        if isinstance(project, dict):
            if "version" in project.get("dynamic", []):
                return None
            version = project.get("version")
            if isinstance(version, str) and VERSION_RE.match(version):
                return version
        poetry = (
            data.get("tool", {}).get("poetry", {}) if isinstance(data, dict) else {}
        )
        if isinstance(poetry, dict):
            version = poetry.get("version")
            if isinstance(version, str) and VERSION_RE.match(version):
                return version

    project = _table_body(text, "project")
    if project is not None:
        if _project_version_is_dynamic(project):
            return None
        version = _static_version_from_body(project)
        if version:
            return version

    poetry = _table_body(text, "tool.poetry")
    if poetry is not None:
        return _static_version_from_body(poetry)
    return None


def _write_pyproject_version(text: str, new_version: str, path: Path) -> str:
    project_bounds = _table_bounds(text, "project")
    if project_bounds is not None:
        start, end = project_bounds
        body = text[start:end]
        if _project_version_is_dynamic(body):
            raise ValueError(
                f"{path}: [project].version is dynamic; cannot bump a static version"
            )
        updated_body, changed = _replace_static_version_line(body, new_version)
        if changed:
            return text[:start] + updated_body + text[end:]

    poetry_bounds = _table_bounds(text, "tool.poetry")
    if poetry_bounds is not None:
        start, end = poetry_bounds
        body = text[start:end]
        updated_body, changed = _replace_static_version_line(body, new_version)
        if changed:
            return text[:start] + updated_body + text[end:]

    raise ValueError(f"Version pattern not found in {path}")


def _table_bounds(text: str, table_name: str) -> tuple[int, int] | None:
    for match in _TABLE_RE.finditer(text):
        if match.group(1).strip() != table_name:
            continue
        start = match.end()
        next_match = _TABLE_RE.search(text, start)
        end = next_match.start() if next_match else len(text)
        return start, end
    return None


def _table_body(text: str, table_name: str) -> str | None:
    bounds = _table_bounds(text, table_name)
    if bounds is None:
        return None
    start, end = bounds
    return text[start:end]


def _static_version_from_body(body: str) -> str | None:
    match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', body)
    if match and VERSION_RE.match(match.group(1)):
        return match.group(1)
    return None


def _replace_static_version_line(body: str, new_version: str) -> tuple[str, bool]:
    pattern = re.compile(r'(?m)^(\s*version\s*=\s*")([^"]+)(".*)$')

    def repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}{new_version}{match.group(3)}"

    updated, count = pattern.subn(repl, body, count=1)
    return updated, count > 0


def _project_version_is_dynamic(body: str) -> bool:
    match = re.search(r"(?ms)^\s*dynamic\s*=\s*\[(.*?)\]", body)
    return bool(match and re.search(r'["\']version["\']', match.group(1)))


def bump_patch(version: str) -> str:
    """0.1.5 -> 0.1.6"""
    m = VERSION_RE.match(version)
    if not m:
        raise ValueError(f"Invalid version format: {version}")
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return f"{major}.{minor}.{patch + 1}"


def bump_minor(version: str) -> str:
    """0.1.6 -> 0.2.0"""
    m = VERSION_RE.match(version)
    if not m:
        raise ValueError(f"Invalid version format: {version}")
    major, minor, _ = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return f"{major}.{minor + 1}.0"
