"""Smoke-test the knowledge schema from built wheel and sdist installations."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
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
    with tempfile.TemporaryDirectory(prefix="llm-wiki-package-check-") as temporary:
        root = Path(temporary)
        for artifact in artifacts:
            _verify_install(artifact, root)
            print(f"verified installed schema from {artifact.name}")


if __name__ == "__main__":
    main()
