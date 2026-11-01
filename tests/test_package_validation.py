"""Release artifact validation follows the built package version."""

from __future__ import annotations

import io
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

from tests import verify_installed_knowledge_schema as package_check


_EVIDENCE_INPUTS = tuple("tests/fixtures/knowledge-evidence/" + name for name in (
    "concept-observation-inventories.json", "producer-evidence-inventories.json",
    "producer-evidence-expectations.json", "released-2.5.0-large.json",
    "released-2.5.0-large-files.json",
))


def _artifacts(tmp_path: Path, version: str, sdist_root: str) -> tuple[Path, Path]:
    """Fabricate the current required payload under variable identity labels."""
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
            *_EVIDENCE_INPUTS,
            *(
                f"{package_check._SAMPLE_ROOT}/{name}"
                for name in package_check._SAMPLE_FILES
            ),
            *(
                f"src/llm_wiki_cli/{package_check._SAMPLE_ROOT}/{name}"
                for name in package_check._SAMPLE_FILES
            ),
        ):
            raw = (Path(__file__).parents[1] / name).read_bytes() if name in _EVIDENCE_INPUTS else b""
            member = tarfile.TarInfo(f"{sdist_root}/{name}")
            member.size = len(raw)
            archive.addfile(member, io.BytesIO(raw))
    return wheel, sdist


@pytest.mark.parametrize("version", ["1.8.0", "1.8.1", "2.0.0"])
def test_matching_release_artifacts_accept_each_version(tmp_path, version):
    artifacts = _artifacts(tmp_path, version, f"agent_wiki_cli-{version}")

    package_check._verify_contents(*artifacts)


@pytest.mark.parametrize(
    "sdist_root", ["agent_wiki_cli-1.8.0", "another_package-1.8.1"]
)
def test_release_artifacts_reject_mismatched_sdist_identity(tmp_path, sdist_root):
    artifacts = _artifacts(tmp_path, "1.8.1", sdist_root)

    with pytest.raises(RuntimeError, match="sdist has an unexpected root"):
        package_check._verify_contents(*artifacts)


@pytest.mark.parametrize("missing", _EVIDENCE_INPUTS)
def test_current_release_inputs_cannot_be_omitted(tmp_path, missing):
    wheel, sdist = _artifacts(tmp_path, "9.0.0", "agent_wiki_cli-9.0.0")
    with tarfile.open(sdist, "r:gz") as archive:
        records = []
        for member in archive.getmembers():
            if member.name != "agent_wiki_cli-9.0.0/" + missing:
                stream = archive.extractfile(member)
                assert stream is not None
                records.append((member, stream.read()))
    with tarfile.open(sdist, "w:gz") as archive:
        for member, raw in records:
            archive.addfile(member, io.BytesIO(raw))
    with pytest.raises(RuntimeError, match="sdist is missing release inputs"):
        package_check._verify_contents(wheel, sdist)


@pytest.mark.parametrize(
    "name",
    [
        "examples/python-basic/project/app.py",
        "examples/fastapi-contracts/requirements.txt",
        "src/llm_wiki_cli/examples/go-http/project/go.mod",
        "llm_wiki_cli/examples/plugin-hooks/project/tasks.py",
        "agent_wiki_cli-2.2.0/examples/native-workflow/project/src",
        "agent_wiki_cli-2.2.0/examples/native-workflow/project/client.py",
        "llm_wiki_cli/examples/native-workflow/project/request.json",
        "examples/README.md",
    ],
)
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


def test_locked_validation_explicitly_uses_its_backend_without_caching_candidate_wheels(
    tmp_path, monkeypatch
):
    commands = []
    monkeypatch.setattr(
        package_check.subprocess,
        "run",
        lambda command, **kwargs: commands.append((command, kwargs)),
    )
    package_check._verify_install(
        tmp_path / "candidate.tar.gz", tmp_path, build_isolation=False
    )
    install = commands[0][0]
    assert (
        "--no-build-isolation" in install
        and "--no-cache-dir" in install
        and "--no-deps" in install
    )
    assert commands[1][1]["env"]["PYTHONPATH"].startswith(str(tmp_path))


def test_default_artifact_validation_keeps_build_isolation_for_existing_callers(
    tmp_path, monkeypatch
):
    commands = []
    monkeypatch.setattr(
        package_check.subprocess,
        "run",
        lambda command, **kwargs: commands.append(command),
    )
    package_check._verify_install(tmp_path / "candidate.tar.gz", tmp_path)
    assert "--no-build-isolation" not in commands[0] and "--no-cache-dir" in commands[0]


def test_installed_probe_and_cli_child_use_utf8_under_a_legacy_parent(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONUTF8", "0")
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252")
    monkeypatch.setattr(package_check, "_PROBE", (
        "import subprocess, sys\n"
        "result = subprocess.run([sys.executable, '-c', 'print(chr(0x2705))'], "
        "capture_output=True, encoding='utf-8', check=True)\n"
        "sys.stdout.write(result.stdout)\n"
    ))
    original = subprocess.run
    outputs = []

    def run(command, **kwargs):
        if command[1:3] == ["-m", "pip"]:
            return subprocess.CompletedProcess(command, 0)
        result = original(command, capture_output=True, encoding="utf-8", **kwargs)
        outputs.append(result.stdout)
        return result

    monkeypatch.setattr(package_check.subprocess, "run", run)
    package_check._verify_install(tmp_path / "candidate.whl", tmp_path)
    assert outputs == ["\u2705\n"]
