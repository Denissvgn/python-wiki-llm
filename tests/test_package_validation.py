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
        for name in package_check._SAMPLE_FILES:
            archive.writestr(f"llm_wiki_cli/{package_check._SAMPLE_ROOT}/{name}", b"")
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
            *(f"{package_check._SAMPLE_ROOT}/{name}" for name in package_check._SAMPLE_FILES),
            *(f"src/llm_wiki_cli/{package_check._SAMPLE_ROOT}/{name}" for name in package_check._SAMPLE_FILES),
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


@pytest.mark.parametrize("name", [
    "examples/python-basic/project/app.py",
    "examples/fastapi-contracts/requirements.txt",
    "src/llm_wiki_cli/examples/go-http/project/go.mod",
    "llm_wiki_cli/examples/plugin-hooks/project/tasks.py",
    "agent_wiki_cli-2.2.0/examples/native-workflow/project/src",
    "agent_wiki_cli-2.2.0/examples/native-workflow/project/client.py",
    "llm_wiki_cli/examples/native-workflow/project/request.json",
    "examples/README.md",
])
def test_repository_tutorials_are_rejected_from_distributions(name):
    with pytest.raises(RuntimeError, match="repository-only tutorial"):
        package_check._validate_member_names({name})


def test_bundled_readme_must_match_the_source_mirror(tmp_path):
    wheel, sdist = _artifacts(tmp_path, "2.1.0", "agent_wiki_cli-2.1.0")
    with zipfile.ZipFile(wheel) as archive:
        # Rebuild the ZIP to change the README without duplicate members.
        name = f"llm_wiki_cli/{package_check._SAMPLE_ROOT}/README.md"
        records = {member: archive.read(member) for member in archive.namelist()}
    records[name] = b"changed README"
    with zipfile.ZipFile(wheel, "w") as archive:
        for member, data in records.items():
            archive.writestr(member, data)
    with pytest.raises(RuntimeError, match="source and packaged sample differ"):
        package_check._verify_contents(wheel, sdist)
