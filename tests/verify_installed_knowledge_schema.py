"""Smoke-test the knowledge schema from built wheel and sdist installations."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

_PROBE = r"""
from pathlib import Path
import sys

import llm_wiki_cli
from llm_wiki_cli.services.contracts import KNOWLEDGE_SCHEMA_VERSION
from llm_wiki_cli.services.knowledge_model import load_knowledge_schema

target = Path(sys.argv[1]).resolve()
Path(llm_wiki_cli.__file__).resolve().relative_to(target)
schema = load_knowledge_schema()
assert KNOWLEDGE_SCHEMA_VERSION == "llm-wiki-knowledge/v1"
assert schema["properties"]["schema_version"]["const"] == KNOWLEDGE_SCHEMA_VERSION
"""

_FORBIDDEN_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "private",
    "reports",
    "secrets",
}
_REQUIRED_HELPERS = {
    "llm_wiki_cli/extractors/go_scripts/go.mod",
    "llm_wiki_cli/extractors/go_scripts/main.go",
    "llm_wiki_cli/extractors/haskell_scripts/Main.hs",
    "llm_wiki_cli/extractors/rust_scripts/Cargo.lock",
    "llm_wiki_cli/extractors/rust_scripts/Cargo.toml",
    "llm_wiki_cli/extractors/rust_scripts/src/main.rs",
    "llm_wiki_cli/extractors/ts_scripts/extract.js",
    "llm_wiki_cli/extractors/ts_scripts/package-lock.json",
    "llm_wiki_cli/extractors/ts_scripts/package.json",
}


def _validate_member_names(names: set[str]) -> None:
    for name in names:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise RuntimeError(f"artifact contains an unsafe member: {name}")
        if _FORBIDDEN_PARTS.intersection(path.parts):
            raise RuntimeError(f"artifact contains a private/generated member: {name}")
        if path.suffix == ".pyc" or path.name in {".coverage", ".DS_Store", ".env"}:
            raise RuntimeError(f"artifact contains a cache/secret member: {name}")


def _verify_contents(wheel: Path, sdist: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = set(archive.namelist())
        metadata_paths = {
            name
            for name in wheel_names
            if len(Path(name).parts) == 2 and name.endswith(".dist-info/METADATA")
        }
        if len(metadata_paths) != 1:
            raise RuntimeError("wheel must contain exactly one package metadata file")
        metadata = BytesParser().parsebytes(archive.read(metadata_paths.pop()))
        versions = metadata.get_all("Version", [])
        if len(versions) != 1 or not versions[0].strip():
            raise RuntimeError("wheel metadata must contain exactly one version")
        version = versions[0].strip()
    _validate_member_names(wheel_names)
    missing_helpers = _REQUIRED_HELPERS - wheel_names
    if missing_helpers:
        raise RuntimeError(f"wheel is missing helper sources/locks: {missing_helpers}")
    wheel_docs = {
        name
        for name in wheel_names
        if name.endswith("/share/doc/agent-wiki-cli/standalone-documentation.md")
    }
    if len(wheel_docs) != 1:
        raise RuntimeError("wheel must contain one canonical standalone document")

    with tarfile.open(sdist, "r:gz") as archive:
        raw_sdist_names = {member.name for member in archive.getmembers()}
    _validate_member_names(raw_sdist_names)
    roots = {Path(name).parts[0] for name in raw_sdist_names if Path(name).parts}
    if roots != {f"agent_wiki_cli-{version}"}:
        raise RuntimeError(f"sdist has an unexpected root: {sorted(roots)}")
    sdist_names = {
        Path(*Path(name).parts[1:]).as_posix()
        for name in raw_sdist_names
        if len(Path(name).parts) > 1
    }
    required_sdist = {
        *(f"src/{name}" for name in _REQUIRED_HELPERS),
        "docs/standalone-documentation.md",
        "release_build_backend.py",
    }
    missing_sdist = required_sdist - sdist_names
    if missing_sdist:
        raise RuntimeError(f"sdist is missing release inputs: {missing_sdist}")


def _single_artifact(dist_dir: Path, pattern: str) -> Path:
    matches = sorted(dist_dir.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {pattern!r} artifact in {dist_dir}, "
            f"found {[path.name for path in matches]}"
        )
    return matches[0]


def _verify_install(artifact: Path, root: Path) -> None:
    target = root / artifact.name.replace(".", "-")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "--no-deps",
            "--target",
            str(target),
            str(artifact),
        ],
        check=True,
    )
    environment = os.environ.copy()
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONPATH"] = str(target)
    subprocess.run(
        [sys.executable, "-c", _PROBE, str(target)],
        cwd=root,
        env=environment,
        check=True,
    )


def main() -> None:
    dist_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "dist").resolve()
    artifacts = (
        _single_artifact(dist_dir, "*.whl"),
        _single_artifact(dist_dir, "*.tar.gz"),
    )
    _verify_contents(*artifacts)
    with tempfile.TemporaryDirectory(prefix="llm-wiki-package-check-") as temporary:
        root = Path(temporary)
        for artifact in artifacts:
            _verify_install(artifact, root)
            print(f"verified installed schema from {artifact.name}")


if __name__ == "__main__":
    main()
