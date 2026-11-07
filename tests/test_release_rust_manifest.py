"""Selected Rust archives remain bound to the exact locked channel manifest."""

from __future__ import annotations

import hashlib
import json

import pytest

from release import qualification


TARGETS = ("x86_64-unknown-linux-gnu", "aarch64-unknown-linux-gnu")


@pytest.fixture
def locked_manifest(tmp_path):
    artifacts = {
        (package, target): {
            "url": f"https://example.invalid/{package}-1.95.0-{target}.tar.xz",
            "sha256": hashlib.sha256((package + target).encode()).hexdigest(),
        }
        for package in ("rust", "clippy-preview")
        for target in TARGETS
    }
    lines = ['manifest-version = "2"', '[pkg.rust]', 'version = "1.95.0 (fixture)"']
    for (package, target), artifact in artifacts.items():
        lines.extend([
            f"[pkg.{package}.target.{target}]", "available = true",
            "xz_url = " + json.dumps(artifact["url"]),
            "xz_hash = " + json.dumps(artifact["sha256"]),
        ])
    manifest = tmp_path / "rust-channel.toml"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload = {"toolchains": {"rust": {
        "version": "1.95.0",
        "artifact": artifacts[("rust", TARGETS[0])],
        "clippy_artifact": artifacts[("clippy-preview", TARGETS[0])],
        "platform_artifacts": {"linux_arm64": artifacts[("rust", TARGETS[1])]},
        "platform_clippy_artifacts": {"linux_arm64": artifacts[("clippy-preview", TARGETS[1])]},
        "checksum_manifest": {"url": manifest.as_uri(), "sha256": qualification.sha256_file(manifest)},
    }}}
    lock = tmp_path / "toolchain-lock.json"
    return lock, manifest, payload


def invoke(fixture, target):
    lock, manifest, payload = fixture
    lock.write_text(json.dumps(payload), encoding="utf-8")
    return qualification.main([
        "verify-rust-manifest", "--lock", str(lock),
        "--manifest", str(manifest), "--target", target,
    ])


@pytest.mark.parametrize("target", TARGETS)
def test_selected_archives_match_their_locked_manifest(locked_manifest, target, capsys):
    assert invoke(locked_manifest, target) == 0
    assert capsys.readouterr().out == target + "\n"


@pytest.mark.parametrize("damage", [
    "corrupt", "wrong-target", "url", "hash", "version", "missing-clippy-lock",
    "missing-clippy-manifest", "unavailable", "manifest-version", "invalid-toml",
])
def test_manifest_or_selected_artifact_mismatch_fails_closed(locked_manifest, damage, capsys):
    _lock, manifest, payload = locked_manifest
    rust = payload["toolchains"]["rust"]
    if damage == "corrupt":
        manifest.write_bytes(manifest.read_bytes() + b"# changed\n")
    elif damage == "wrong-target":
        rust["platform_artifacts"]["linux_arm64"] = rust["artifact"]
    elif damage in {"url", "hash"}:
        key = "url" if damage == "url" else "sha256"
        rust["platform_artifacts"]["linux_arm64"][key] = (
            "https://example.invalid/wrong.tar.xz" if damage == "url" else "f" * 64
        )
    elif damage == "version":
        rust["version"] = "1.94.0"
    elif damage == "missing-clippy-lock":
        rust["platform_clippy_artifacts"].clear()
    else:
        text = manifest.read_text(encoding="utf-8")
        if damage == "missing-clippy-manifest":
            text = text.split("[pkg.clippy-preview.", 1)[0]
        elif damage == "unavailable":
            text = text.replace("available = true", "available = false")
        elif damage == "manifest-version":
            text = text.replace('manifest-version = "2"', 'manifest-version = "3"')
        else:
            text = "invalid = ["
        manifest.write_text(text, encoding="utf-8")
        rust["checksum_manifest"]["sha256"] = qualification.sha256_file(manifest)
    assert invoke(locked_manifest, TARGETS[1]) == 2
    assert capsys.readouterr().err


def test_arm_selection_does_not_replace_the_existing_x86_contract(locked_manifest):
    rust = locked_manifest[2]["toolchains"]["rust"]
    rust["artifact"] = {"url": "wrong", "sha256": "f" * 64}
    assert invoke(locked_manifest, TARGETS[1]) == 0
    assert invoke(locked_manifest, TARGETS[0]) == 2
