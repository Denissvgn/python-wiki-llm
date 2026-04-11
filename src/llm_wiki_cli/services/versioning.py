from __future__ import annotations

import re
from pathlib import Path

# Supported version file patterns in priority order
VERSION_PATTERNS = [
    ("pyproject.toml", re.compile(r'^(version\s*=\s*")(\d+\.\d+\.\d+)(")', re.MULTILINE)),
    ("setup.cfg", re.compile(r'^(version\s*=\s*)(\d+\.\d+\.\d+)', re.MULTILINE)),
    ("package.json", re.compile(r'("version"\s*:\s*")(\d+\.\d+\.\d+)(")', re.MULTILINE)),
    ("VERSION", re.compile(r'^(\d+\.\d+\.\d+)$', re.MULTILINE)),
]

VERSION_RE = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')


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
    content = path.read_text()
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
    content = path.read_text()
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
    path.write_text(content)


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
