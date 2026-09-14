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
import re
import shlex
import subprocess
import sys

import llm_wiki_cli
from llm_wiki_cli.services.contracts import KNOWLEDGE_SCHEMA_VERSION
from llm_wiki_cli.services.knowledge_model import load_knowledge_schema

target = Path(sys.argv[1]).resolve()
Path(llm_wiki_cli.__file__).resolve().relative_to(target)
schema = load_knowledge_schema()
assert KNOWLEDGE_SCHEMA_VERSION == "llm-wiki-knowledge/v1"
assert schema["properties"]["schema_version"]["const"] == KNOWLEDGE_SCHEMA_VERSION

# Exercise the installed sample using only its exported, self-contained README.
from llm_wiki_cli.services.plugin_samples import export_sample

project = Path.cwd() / (target.name + "-plugin-demo")
project.mkdir()
plugin = project / "vendor/documentation-hooks"
export_sample("documentation-hooks", plugin, root=project)
assert {path.name for path in plugin.iterdir()} == {
    "README.md", "detectors.py", "styles.py", "llm-wiki-plugin.json"
}
readme = (plugin / "README.md").read_text(encoding="utf-8")
(project / "tasks.py").write_text(re.findall(r"```python\n(.*?)```", readme, re.S)[0], encoding="utf-8")
(project / ".gitignore").write_text(re.findall(r"```gitignore\n(.*?)```", readme, re.S)[0], encoding="utf-8")
blocks = re.findall(r"```sh\n(.*?)```", readme, re.S)
assert len(blocks) == 2
for stage, block in enumerate(blocks):
    if stage == 1:
        tasks = project / "tasks.py"
        tasks.write_text(tasks.read_text(encoding="utf-8").replace("handle_task", "task_handler"), encoding="utf-8")
    for line in block.splitlines():
        command = shlex.split(line)
        assert command[0] == "llm-wiki"
        # The README explicitly skips export when these files already exist.
        if command[1:4] == ["plugins", "samples", "export"]:
            continue
        result = subprocess.run(
            [sys.executable, "-m", "llm_wiki_cli.cli", *command[1:]],
            cwd=project, capture_output=True, text=True, encoding="utf-8", timeout=90,
        )
        assert result.returncode == 0, (command, result.stdout, result.stderr)
    markdown = (project / "wiki/flows/task-task-handler.md").read_text(encoding="utf-8")
    symbol = "handle_task" if stage == 0 else "task_handler"
    assert f's1["1. {symbol}"]' in markdown
    assert "classDef entry fill:#2E7D32,stroke:#2E7D32" in markdown
    assert "class s1 entry" in markdown
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
    "llm_wiki_cli/py.typed",
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
_SAMPLE_ROOT = "examples/plugins/documentation-hooks"
_SAMPLE_FILES = ("README.md", "detectors.py", "styles.py", "llm-wiki-plugin.json")


def _validate_member_names(names: set[str]) -> None:
    for name in names:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise RuntimeError(f"artifact contains an unsafe member: {name}")
        if _FORBIDDEN_PARTS.intersection(path.parts):
            raise RuntimeError(f"artifact contains a private/generated member: {name}")
        if path.suffix == ".pyc" or path.name in {".coverage", ".DS_Store", ".env"}:
            raise RuntimeError(f"artifact contains a cache/secret member: {name}")
        if "examples" in path.parts:
            parts = path.parts[path.parts.index("examples") + 1:]
            if parts and parts[0] != "plugins":
                raise RuntimeError(f"artifact contains a repository-only tutorial: {name}")


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
        wheel_sample = {}
        for filename in _SAMPLE_FILES:
            name = f"llm_wiki_cli/{_SAMPLE_ROOT}/{filename}"
            if name not in wheel_names:
                raise RuntimeError(f"wheel is missing a bundled sample file: {name}")
            wheel_sample[filename] = archive.read(name)
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
    with tarfile.open(sdist, "r:gz") as archive:
        for prefix in (_SAMPLE_ROOT, f"src/llm_wiki_cli/{_SAMPLE_ROOT}"):
            for filename in _SAMPLE_FILES:
                name = f"{prefix}/{filename}"
                if name not in sdist_names:
                    raise RuntimeError(f"sdist is missing a sample file: {name}")
                stream = archive.extractfile(f"agent_wiki_cli-{version}/{name}")
                if stream is None or stream.read() != wheel_sample[filename]:
                    raise RuntimeError(f"source and packaged sample differ: {name}")


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
