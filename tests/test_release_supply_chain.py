"""Release supply-chain lock contract tests."""

from __future__ import annotations

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def test_release_python_tools_are_exact_and_hash_locked():
    requirements = (PROJECT_ROOT / "release" / "requirements.txt").read_text(
        encoding="utf-8"
    )
    for requirement in (
        "bandit==1.9.4",
        "build==1.5.0",
        "pip-audit==2.10.1",
        "pyright==1.1.411",
        "ruff==0.15.22",
        "setuptools==83.0.0",
        "twine==7.0.0",
    ):
        start = requirements.index(requirement)
        next_requirement = requirements.find("\n", start)
        stanza_end = requirements.find("\n    # via", next_requirement)
        assert "--hash=sha256:" in requirements[start:stanza_end]


def test_release_toolchains_are_exact_and_checksum_bound():
    lock = json.loads(
        (PROJECT_ROOT / "release" / "toolchain-lock.json").read_text(
            encoding="utf-8"
        )
    )

    assert lock["schema_version"] == "agent-wiki-release-toolchains/v1"
    assert {
        name: entry["version"]
        for name, entry in lock["toolchains"].items()
    } == {
        "go": "1.26.5",
        "haskell": "9.6.7",
        "node": "24.18.0",
        "npm": "11.16.0",
        "rust": "1.95.0",
    }
    for name in ("go", "haskell", "node", "npm"):
        artifact = lock["toolchains"][name]["artifact"]
        assert artifact["url"].startswith("https://")
        assert SHA256_RE.fullmatch(artifact["sha256"])

    for name in ("haskell", "node"):
        assert SHA256_RE.fullmatch(
            lock["toolchains"][name]["checksum_manifest_sha256"]
        )
    for artifact_name in ("artifact", "clippy_artifact"):
        artifact = lock["toolchains"]["rust"][artifact_name]
        assert artifact["url"].startswith(
            "https://static.rust-lang.org/dist/2026-04-16/"
        )
        assert SHA256_RE.fullmatch(artifact["sha256"])
    assert SHA256_RE.fullmatch(
        lock["toolchains"]["rust"]["checksum_manifest"]["sha256"]
    )
    assert lock["oci_images"] == {
        "python_base": {
            "platform": "linux/amd64",
            "reference": (
                "python@sha256:"
                "399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0"
            ),
        },
        "registry": {
            "platform": "linux/amd64",
            "reference": (
                "registry@sha256:"
                "a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373"
            ),
        },
    }
    assert {
        name: entry["version"]
        for name, entry in lock["qualification_tools"].items()
    } == {
        "actionlint": "1.7.12",
        "cargo-audit": "0.22.2",
        "govulncheck": "1.1.4",
    }
    assert {
        name: entry["version_output"]
        for name, entry in lock["qualification_tools"].items()
    } == {
        "actionlint": "v1.7.12",
        "cargo-audit": "cargo-audit 0.22.2",
        "govulncheck": "govulncheck@v1.1.4",
    }
    for entry in lock["qualification_tools"].values():
        assert entry["source"]["url"].startswith("https://")
        assert SHA256_RE.fullmatch(entry["source"]["sha256"])
