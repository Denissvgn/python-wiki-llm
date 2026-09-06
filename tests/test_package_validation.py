"""Release artifact validation follows the built package version."""

from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from tests import verify_installed_knowledge_schema as package_check


def _artifacts(tmp_path: Path, version: str, sdist_root: str) -> tuple[Path, Path]:
    wheel = tmp_path / f"agent_wiki_cli-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            f"agent_wiki_cli-{version}.dist-info/METADATA",
            f"Metadata-Version: 2.1\nName: agent-wiki-cli\nVersion: {version}\n",
        )
        for name in package_check._REQUIRED_HELPERS:
            archive.writestr(name, b"")
        archive.writestr(
            f"agent_wiki_cli-{version}.data/data/share/doc/agent-wiki-cli/"
            "standalone-documentation.md",
            b"",
        )
    sdist = tmp_path / f"{sdist_root}.tar.gz"
    with tarfile.open(sdist, "w:gz") as archive:
        for name in (
            *(f"src/{name}" for name in package_check._REQUIRED_HELPERS),
            "docs/standalone-documentation.md",
            "release_build_backend.py",
        ):
            archive.addfile(tarfile.TarInfo(f"{sdist_root}/{name}"), io.BytesIO())
    return wheel, sdist


@pytest.mark.parametrize("version", ["1.8.0", "1.8.1", "2.0.0"])
def test_matching_release_artifacts_accept_each_version(tmp_path, version):
    artifacts = _artifacts(tmp_path, version, f"agent_wiki_cli-{version}")

    package_check._verify_contents(*artifacts)


@pytest.mark.parametrize("sdist_root", ["agent_wiki_cli-1.8.0", "another_package-1.8.1"])
def test_release_artifacts_reject_mismatched_sdist_identity(tmp_path, sdist_root):
    artifacts = _artifacts(tmp_path, "1.8.1", sdist_root)

    with pytest.raises(RuntimeError, match="sdist has an unexpected root"):
        package_check._verify_contents(*artifacts)
