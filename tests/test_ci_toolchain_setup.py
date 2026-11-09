"""Hermetic contracts for the CI toolchain setup."""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SETUP_SCRIPT = ROOT / ".github" / "scripts" / "setup-llm-wiki-ci-toolchains.sh"
LOCK_PATH = ROOT / "release" / "toolchain-lock.json"

pytestmark = pytest.mark.skipif(
    os.name == "nt",
    reason="the Bash setup supports Ubuntu and Darwin hosts",
)

NODE_VERSION = "91.2.3"
NPM_VERSION = "91.4.5"
GO_VERSION = "91.6.7"
CARGO_VERSION_OUTPUT = "cargo 91.8.9 (fixture 2099-01-01)"
GHC_VERSION = "91.10.11"
GO_PLATFORM = (
    "darwin/arm64" if platform.system() == "Darwin" else "linux/amd64"
)


@dataclass(frozen=True)
class SetupHarness:
    root: Path
    script: Path
    python: Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _add_tar_file(
    archive: tarfile.TarFile,
    name: str,
    content: str,
    *,
    mode: int = 0o644,
) -> None:
    payload = content.encode("utf-8")
    info = tarfile.TarInfo(name)
    info.mode = mode
    info.size = len(payload)
    archive.addfile(info, io.BytesIO(payload))


def _write_fake_node_archive(path: Path) -> None:
    node = f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "${{1:-}}" == "--version" ]]; then
  printf '%s\\n' 'v{NODE_VERSION}'
  exit 0
fi
if [[ "${{1:-}}" == */npm-cli.js && "${{2:-}}" == "--version" ]]; then
  printf '%s\\n' '{NPM_VERSION}'
  exit 0
fi
printf 'unexpected fixture node invocation: %s\\n' "$*" >&2
exit 64
"""
    with tarfile.open(path, "w:xz") as archive:
        _add_tar_file(archive, "node-fixture/bin/node", node, mode=0o755)
        _add_tar_file(
            archive,
            "node-fixture/lib/node_modules/npm/bin/npm-cli.js",
            "// fixture: the node shim handles this path\n",
        )


def _write_fake_npm_archive(path: Path, *, direct_failure: bool = False) -> None:
    npm_cli = f"""#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' '{NPM_VERSION}'
"""
    if direct_failure:
        npm_cli = "#!/usr/bin/env bash\nexit 42\n"
    with tarfile.open(path, "w:gz") as archive:
        _add_tar_file(
            archive,
            "package/package.json",
            json.dumps({"name": "npm", "version": NPM_VERSION}) + "\n",
        )
        _add_tar_file(
            archive,
            "package/bin/npm-cli.js",
            npm_cli,
            mode=0o755,
        )
        _add_tar_file(
            archive,
            "package/bin/npx-cli.js",
            npm_cli,
            mode=0o755,
        )


def _write_fake_go_archive(path: Path, *, target: str = GO_PLATFORM) -> None:
    go = f"""#!/usr/bin/env bash
set -euo pipefail
test "${{1:-}}" = version
printf '%s\\n' 'go version go{GO_VERSION} {target}'
"""
    with tarfile.open(path, "w:gz") as archive:
        _add_tar_file(archive, "go/bin/go", go, mode=0o755)


def _write_fake_rust_archive(
    path: Path, *, target: str = "x86_64-unknown-linux-gnu", release: str = "91.8.9"
) -> None:
    install = f"""#!/usr/bin/env bash
set -euo pipefail
prefix=""
for argument in "$@"; do
  case "${{argument}}" in
    --prefix=*) prefix="${{argument#--prefix=}}" ;;
    --disable-ldconfig) ;;
    *) printf 'unexpected fixture Rust install argument: %s\\n' "${{argument}}" >&2; exit 64 ;;
  esac
done
test -n "${{prefix}}"
mkdir -p -- "${{prefix}}/bin"
cat > "${{prefix}}/bin/cargo" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
test "${{1:-}}" = --version
printf '%s\\n' '{CARGO_VERSION_OUTPUT}'
EOF
cat > "${{prefix}}/bin/rustc" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
test "${{1:-}}" = -vV
printf '%s\\n' 'rustc fixture' 'host: {target}' 'release: {release}'
EOF
chmod 0755 "${{prefix}}/bin/cargo" "${{prefix}}/bin/rustc"
"""
    with tarfile.open(path, "w:xz") as archive:
        _add_tar_file(archive, "rust-fixture/install.sh", install, mode=0o755)


def _write_fake_ghc_archive(
    path: Path, *, host: str = "x86_64-unknown-linux", target: str | None = None
) -> None:
    target = host if target is None else target
    configure = """#!/usr/bin/env bash
set -euo pipefail
prefix=""
for argument in "$@"; do
  case "${argument}" in
    --prefix=*) prefix="${argument#--prefix=}" ;;
    *) printf 'unexpected fixture GHC configure argument: %s\n' "${argument}" >&2; exit 64 ;;
  esac
done
test -n "${prefix}"
cat > Makefile <<EOF
install:
\tmkdir -p "$prefix/bin"
\tcp ghc-shim "$prefix/bin/ghc"
\tchmod 0755 "$prefix/bin/ghc"
EOF
"""
    ghc = f"""#!/usr/bin/env bash
set -euo pipefail
case "${{1:-}}" in
  --numeric-version) printf '%s\\n' '{GHC_VERSION}' ;;
  --print-host-platform) printf '%s\\n' '{host}' ;;
  --print-target-platform) printf '%s\\n' '{target}' ;;
  *) exit 64 ;;
esac
"""
    with tarfile.open(path, "w:xz") as archive:
        _add_tar_file(archive, "ghc-fixture/configure", configure, mode=0o755)
        _add_tar_file(archive, "ghc-fixture/ghc-shim", ghc, mode=0o755)


def _write_fake_rust_manifest(payload: dict, manifest: Path) -> None:
    lines = ['manifest-version = "2"', '[pkg.rust]',
             f'version = "{payload["toolchains"]["rust"]["version"]} (fixture)"']
    rust = payload["toolchains"]["rust"]
    for package, base_key, platforms_key in (
        ("rust", "artifact", "platform_artifacts"),
        ("clippy-preview", "clippy_artifact", "platform_clippy_artifacts"),
    ):
        for target, artifact in (
            ("x86_64-unknown-linux-gnu", rust[base_key]),
            ("aarch64-unknown-linux-gnu", rust[platforms_key]["linux_arm64"]),
        ):
            lines.extend([
                f"[pkg.{package}.target.{target}]", "available = true",
                "xz_url = " + json.dumps(artifact["url"]),
                "xz_hash = " + json.dumps(artifact["sha256"]),
            ])
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rust["checksum_manifest"]["sha256"] = _sha256(manifest)


@pytest.fixture
def fake_lock(tmp_path: Path) -> Path:
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    node = downloads / "node.tar.xz"
    npm = downloads / "npm.tgz"
    go = downloads / "go.tar.gz"
    rust_channel = downloads / "rust-channel.toml"
    rust = downloads / "rust.tar.xz"
    rust_arm = downloads / "rust-arm64.tar.xz"
    clippy = downloads / "clippy.tar.xz"
    clippy_arm = downloads / "clippy-arm64.tar.xz"
    ghc = downloads / "ghc.tar.xz"
    ghc_arm = downloads / "ghc-arm64.tar.xz"
    go_arm = downloads / "go-arm64.tar.gz"
    _write_fake_node_archive(node)
    _write_fake_npm_archive(npm)
    _write_fake_go_archive(go)
    _write_fake_go_archive(go_arm, target="linux/arm64")
    _write_fake_rust_archive(rust)
    _write_fake_rust_archive(rust_arm, target="aarch64-unknown-linux-gnu")
    shutil.copyfile(rust, clippy)
    shutil.copyfile(rust_arm, clippy_arm)
    _write_fake_ghc_archive(ghc)
    _write_fake_ghc_archive(ghc_arm, host="aarch64-unknown-linux")

    node_artifact = {"url": node.as_uri(), "sha256": _sha256(node)}
    go_artifact = {"url": go.as_uri(), "sha256": _sha256(go)}
    payload = {
        "schema_version": "agent-wiki-release-toolchains/v1",
        "toolchains": {
            "node": {
                "artifact": node_artifact,
                "platform_artifacts": {
                    "darwin_arm64": node_artifact,
                    "linux_arm64": node_artifact,
                },
                "version": NODE_VERSION,
                "version_output": f"v{NODE_VERSION}",
            },
            "npm": {
                "artifact": {"url": npm.as_uri(), "sha256": _sha256(npm)},
                "version": NPM_VERSION,
                "version_output": NPM_VERSION,
            },
            "go": {
                "artifact": go_artifact,
                # These archives contain native shell shims, not Go binaries.
                "platform_artifacts": {"darwin_arm64": go_artifact,
                                       "linux_arm64": {"url": go_arm.as_uri(), "sha256": _sha256(go_arm)}},
                "version": GO_VERSION,
                "version_output": f"go version go{GO_VERSION}",
            },
            "rust": {
                "artifact": {"url": rust.as_uri(), "sha256": _sha256(rust)},
                "platform_artifacts": {"linux_arm64": {"url": rust_arm.as_uri(), "sha256": _sha256(rust_arm)}},
                "clippy_artifact": {"url": clippy.as_uri(), "sha256": _sha256(clippy)},
                "platform_clippy_artifacts": {"linux_arm64": {"url": clippy_arm.as_uri(), "sha256": _sha256(clippy_arm)}},
                "checksum_manifest": {
                    "url": rust_channel.as_uri(),
                    "sha256": "0" * 64,
                },
                "version": "91.8.9",
                "version_output": CARGO_VERSION_OUTPUT,
            },
            "haskell": {
                "artifact": {"url": ghc.as_uri(), "sha256": _sha256(ghc)},
                "platform_artifacts": {"linux_arm64": {"url": ghc_arm.as_uri(), "sha256": _sha256(ghc_arm)}},
                "version": GHC_VERSION,
                "version_output": GHC_VERSION,
            },
        },
    }
    _write_fake_rust_manifest(payload, rust_channel)
    path = tmp_path / "toolchain-lock.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def setup_harness(tmp_path: Path) -> SetupHarness:
    root = tmp_path / "checkout"
    script = root / ".github" / "scripts" / SETUP_SCRIPT.name
    qualification = root / "release" / "qualification.py"
    python = root / ".venv" / "bin" / "python"
    for parent in (script.parent, qualification.parent, python.parent):
        parent.mkdir(parents=True)
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    (root / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    (root / "ignored").mkdir()
    subprocess.run(
        ["git", "-C", str(root), "add", ".gitignore"],
        check=True,
    )
    shutil.copy2(SETUP_SCRIPT, script)
    shutil.copy2(ROOT / "release" / "qualification.py", qualification)
    python.symlink_to(Path(sys.executable))
    return SetupHarness(root=root, script=script, python=python)


def _run_setup(
    harness: SetupHarness,
    *arguments: object,
    environment: dict[str, str] | None = None,
    github_actions: bool = False,
    simulate_supported_go_target: bool = False,
) -> subprocess.CompletedProcess[str]:
    command_environment = dict(
        os.environ if environment is None else environment
    )
    if simulate_supported_go_target and platform.system() == "Linux" and platform.machine() in {"aarch64", "arm64"}:
        # Asset-selection simulation only: the fixture executes native shell
        # shims, never an x86 compiler, image or instruction-set emulator.
        command_environment = _with_fake_uname(harness.root.parent, command_environment, system="Linux", machine="x86_64")
    if not github_actions:
        for name in (
            "GITHUB_ACTIONS",
            "GITHUB_ENV",
            "GITHUB_PATH",
            "RUNNER_TEMP",
            "pythonLocation",
        ):
            command_environment.pop(name, None)
    return subprocess.run(
        ["bash", str(harness.script), *(str(value) for value in arguments)],
        cwd=harness.root,
        env=command_environment,
        check=False,
        capture_output=True,
        text=True,
    )


def _local_arguments(
    *,
    mode: str,
    install_root: Path,
    environment_file: Path,
    lock: Path,
) -> tuple[object, ...]:
    return (
        "--mode",
        mode,
        "--install-root",
        install_root,
        "--environment-file",
        environment_file,
        "--lock",
        lock,
    )


def _assert_success(completed: subprocess.CompletedProcess[str]) -> None:
    assert completed.returncode == 0, (completed.stdout, completed.stderr)


def _with_fake_uname(
    tmp_path: Path,
    environment: dict[str, str],
    *,
    system: str,
    machine: str,
) -> dict[str, str]:
    fixture_bin = tmp_path / f"uname-{system}-{machine}"
    fixture_bin.mkdir()
    uname = fixture_bin / "uname"
    uname.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
case "${{1:-}}" in
  -s) printf '%s\\n' '{system}' ;;
  -m) printf '%s\\n' '{machine}' ;;
  *) printf 'unexpected fixture uname invocation: %s\\n' "$*" >&2; exit 64 ;;
esac
""",
        encoding="utf-8",
    )
    uname.chmod(0o755)
    return {
        **environment,
        "PATH": os.pathsep.join([str(fixture_bin), environment["PATH"]]),
    }


def _github_environment(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, str]]:
    runner_temp = tmp_path / "runner"
    runner_temp.mkdir()
    github_path = tmp_path / "github-path"
    github_env = tmp_path / "github-env"
    github_path.touch()
    github_env.touch()
    environment = {
        **os.environ,
        "GITHUB_ACTIONS": "true",
        "GITHUB_PATH": str(github_path),
        "GITHUB_ENV": str(github_env),
        "RUNNER_TEMP": str(runner_temp),
    }
    return runner_temp, github_path, github_env, environment


@pytest.mark.parametrize("mode", ["qualification-go", "extractor-go"])
def test_missing_arm64_go_lock_refusal_precedes_cache_or_environment_writes(fake_lock, setup_harness, tmp_path, mode):
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    del payload["toolchains"]["go"]["platform_artifacts"]["linux_arm64"]
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    environment = _with_fake_uname(tmp_path, dict(os.environ), system="Linux", machine="aarch64")
    install_root = setup_harness.root / "ignored" / "unsupported-go-target"
    environment_file = setup_harness.root / "ignored" / "unsupported-go-target.env"
    completed = _run_setup(setup_harness, *_local_arguments(mode=mode, install_root=install_root, environment_file=environment_file, lock=fake_lock), environment=environment)
    assert completed.returncode != 0
    assert f"no locked {mode} artifact for Linux/aarch64" in completed.stderr
    assert not install_root.exists() and not environment_file.exists()


def test_routine_local_setup_uses_lock_and_writes_sourceable_environment(
    fake_lock: Path,
    setup_harness: SetupHarness,
) -> None:
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    payload["toolchains"]["go"]["artifact"]["url"] = "file:///not-requested-go"
    payload["toolchains"]["go"]["platform_artifacts"]["darwin_arm64"][
        "url"
    ] = "file:///not-requested-go"
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    local_root = setup_harness.root / "ignored"
    install_root = local_root / "routine tools 'quoted'"
    environment_file = local_root / "routine.env"
    poison_bin = local_root / "ambient-bin"
    poison_bin.mkdir()
    for name in ("python", "python3"):
        executable = poison_bin / name
        executable.write_text("#!/bin/sh\nexit 97\n", encoding="utf-8")
        executable.chmod(0o755)
    environment = {
        **os.environ,
        "PATH": os.pathsep.join([str(poison_bin), os.environ["PATH"]]),
    }

    completed = _run_setup(
        setup_harness,
        *_local_arguments(
            mode="routine",
            install_root=install_root,
            environment_file=environment_file,
            lock=fake_lock,
        ),
        environment=environment,
    )

    _assert_success(completed)
    sourced = subprocess.run(
        [
            "bash",
            "-c",
            'set -euo pipefail; source "$1"; node --version; npm --version; '
            'test -z "${LLM_WIKI_GO+x}"',
            "bash",
            str(environment_file),
        ],
        cwd=setup_harness.root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert sourced.returncode == 0, (sourced.stdout, sourced.stderr)
    assert sourced.stdout.splitlines() == [f"v{NODE_VERSION}", NPM_VERSION]
    assert "export PATH=" in environment_file.read_text(encoding="utf-8")
    assert not (install_root / "go").exists()


@pytest.mark.parametrize("machine", ["aarch64", "arm64"])
def test_linux_arm64_routine_uses_only_its_locked_artifact(
    tmp_path: Path, fake_lock: Path, setup_harness: SetupHarness, machine: str,
) -> None:
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    payload["toolchains"]["node"]["artifact"]["url"] = "file:///not-requested-x64"
    payload["toolchains"]["node"]["platform_artifacts"]["darwin_arm64"]["url"] = "file:///not-requested-darwin"
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    install_root = setup_harness.root / ".git" / "llm-wiki-ci-arm64"
    environment_file = setup_harness.root / ".git" / "llm-wiki-ci-arm64.env"
    environment = _with_fake_uname(tmp_path, dict(os.environ), system="Linux", machine=machine)
    completed = _run_setup(
        setup_harness,
        *_local_arguments(mode="routine", install_root=install_root,
                          environment_file=environment_file, lock=fake_lock),
        environment=environment,
    )
    _assert_success(completed)
    sourced = subprocess.run(
        ["bash", "-c", 'source "$1"; node --version; npm --version', "bash", str(environment_file)],
        cwd=setup_harness.root, env=environment, capture_output=True, text=True, check=False,
    )
    assert sourced.returncode == 0, (sourced.stdout, sourced.stderr)
    assert sourced.stdout.splitlines() == [f"v{NODE_VERSION}", NPM_VERSION]
    assert not (install_root / "go").exists()


@pytest.mark.parametrize("toolchain", ["node", "npm"])
def test_linux_arm64_routine_rejects_corrupt_download_before_publication(
    tmp_path: Path, fake_lock: Path, setup_harness: SetupHarness, toolchain: str,
) -> None:
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    artifact = (payload["toolchains"]["node"]["platform_artifacts"]["linux_arm64"]
                if toolchain == "node" else payload["toolchains"]["npm"]["artifact"])
    artifact["sha256"] = "0" * 64
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    install_root = setup_harness.root / ".git" / "llm-wiki-ci-arm64-corrupt"
    environment_file = setup_harness.root / ".git" / "llm-wiki-ci-arm64-corrupt.env"
    completed = _run_setup(
        setup_harness,
        *_local_arguments(mode="routine", install_root=install_root,
                          environment_file=environment_file, lock=fake_lock),
        environment=_with_fake_uname(tmp_path, dict(os.environ), system="Linux", machine="aarch64"),
    )
    assert completed.returncode != 0
    assert "digest mismatch" in completed.stderr
    assert not (install_root / "node").exists()
    assert not environment_file.exists()


@pytest.mark.parametrize("mode", ["qualification-go", "extractor-go", "extractor-rust", "extractor-haskell"])
def test_linux_arm64_requires_an_explicit_locked_host_artifact(
    tmp_path: Path, fake_lock: Path, setup_harness: SetupHarness, mode: str,
) -> None:
    toolchain = {"qualification-go": "go", "extractor-go": "go", "extractor-rust": "rust", "extractor-haskell": "haskell"}[mode]
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    del payload["toolchains"][toolchain]["platform_artifacts"]["linux_arm64"]
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    install_root = setup_harness.root / ".git" / "llm-wiki-ci-arm64-unsupported"
    environment_file = setup_harness.root / ".git" / "llm-wiki-ci-arm64-unsupported.env"
    completed = _run_setup(
        setup_harness,
        *_local_arguments(mode=mode, install_root=install_root,
                          environment_file=environment_file, lock=fake_lock),
        environment=_with_fake_uname(tmp_path, dict(os.environ), system="Linux", machine="aarch64"),
    )
    assert completed.returncode != 0
    assert f"no locked {mode} artifact for Linux/aarch64" in completed.stderr
    assert not install_root.exists()
    assert not environment_file.exists()


@pytest.mark.parametrize("mode", ["qualification-go", "extractor-go", "extractor-rust", "extractor-haskell"])
@pytest.mark.parametrize("machine", ["aarch64", "arm64"])
def test_linux_arm64_installs_only_the_selected_locked_native_toolchain(
    tmp_path, fake_lock, setup_harness, mode, machine,
):
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    toolchain = {"qualification-go": "go", "extractor-go": "go", "extractor-rust": "rust", "extractor-haskell": "haskell"}[mode]
    payload["toolchains"][toolchain]["artifact"]["url"] = "file:///must-not-download-x86"
    if toolchain == "rust":
        # The unselected x86 entries remain internally consistent with the fixture manifest.
        _write_fake_rust_manifest(payload, fake_lock.parent / "downloads/rust-channel.toml")
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    runner_temp, github_path, github_env, environment = _github_environment(tmp_path)
    environment = _with_fake_uname(tmp_path, environment, system="Linux", machine=machine)
    install_root = runner_temp / "native-toolchains"
    result = _run_setup(setup_harness, "--mode", mode, "--install-root", install_root,
                        "--lock", fake_lock, "--python", setup_harness.python,
                        environment=environment, github_actions=True)
    _assert_success(result)
    target = "haskell" if toolchain == "haskell" else toolchain
    assert github_path.read_text(encoding="utf-8") == f"{install_root / target / 'bin'}\n"
    assert (install_root / target / "bin").is_dir()
    assert not list(install_root.glob(".setup-*"))


@pytest.mark.parametrize("mode", ["routine", "qualification-go", "extractor-go", "extractor-rust", "extractor-haskell"])
def test_unknown_architecture_fails_before_download_or_output_creation(
    tmp_path, fake_lock, setup_harness, mode,
):
    runner_temp, github_path, github_env, environment = _github_environment(tmp_path)
    environment = _with_fake_uname(tmp_path, environment, system="Linux", machine="riscv64")
    install_root = runner_temp / "unsupported"
    result = _run_setup(setup_harness, "--mode", mode, "--install-root", install_root,
                        "--lock", fake_lock, "--python", setup_harness.python,
                        environment=environment, github_actions=True)
    assert result.returncode != 0
    assert f"no locked {mode} artifact for Linux/riscv64" in result.stderr
    assert not install_root.exists()
    assert not github_path.read_text() and not github_env.read_text()


@pytest.mark.parametrize("member", ["platform_artifacts", "platform_clippy_artifacts"])
def test_rust_missing_arm64_artifact_is_rejected_before_manifest_download(
    tmp_path, fake_lock, setup_harness, member,
):
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    del payload["toolchains"]["rust"][member]["linux_arm64"]
    payload["toolchains"]["rust"]["checksum_manifest"]["url"] = "file:///must-not-download-manifest"
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    install_root = setup_harness.root / "ignored/native-rust"
    environment_file = setup_harness.root / "ignored/native-rust.env"
    result = _run_setup(setup_harness, *_local_arguments(mode="extractor-rust", install_root=install_root,
                                                       environment_file=environment_file, lock=fake_lock),
                        environment=_with_fake_uname(tmp_path, dict(os.environ), system="Linux", machine="arm64"))
    assert result.returncode != 0
    assert "no locked extractor-rust artifact" in result.stderr
    assert not install_root.exists() and not environment_file.exists()


@pytest.mark.parametrize("mode,wrong", [
    ("extractor-go", "go"), ("extractor-rust", "rust-host"), ("extractor-rust", "rust-release"),
    ("extractor-haskell", "ghc-host"), ("extractor-haskell", "ghc-target"),
])
def test_arm64_compiler_platform_or_release_mismatch_never_publishes(
    tmp_path, fake_lock, setup_harness, mode, wrong,
):
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    toolchain = {"extractor-go": "go", "extractor-rust": "rust", "extractor-haskell": "haskell"}[mode]
    artifact = payload["toolchains"][toolchain]["platform_artifacts"]["linux_arm64"]
    archive = fake_lock.parent / "downloads" / {"go": "go-arm64.tar.gz", "rust": "rust-arm64.tar.xz", "haskell": "ghc-arm64.tar.xz"}[toolchain]
    if wrong == "go":
        _write_fake_go_archive(archive, target="linux/amd64")
    elif wrong.startswith("rust"):
        _write_fake_rust_archive(archive, target="x86_64-unknown-linux-gnu" if wrong == "rust-host" else "aarch64-unknown-linux-gnu",
                                 release="0.0.0" if wrong == "rust-release" else "91.8.9")
    else:
        _write_fake_ghc_archive(archive, host="x86_64-unknown-linux" if wrong == "ghc-host" else "aarch64-unknown-linux",
                                target="x86_64-unknown-linux" if wrong == "ghc-target" else "aarch64-unknown-linux")
    artifact["sha256"] = _sha256(archive)
    if toolchain == "rust":
        _write_fake_rust_manifest(payload, fake_lock.parent / "downloads/rust-channel.toml")
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    runner_temp, github_path, github_env, environment = _github_environment(tmp_path)
    result = _run_setup(setup_harness, "--mode", mode, "--install-root", runner_temp / "native-tools",
                        "--lock", fake_lock, "--python", setup_harness.python,
                        environment=_with_fake_uname(tmp_path, environment, system="Linux", machine="aarch64"),
                        github_actions=True)
    assert result.returncode != 0
    assert "platform mismatch" in result.stderr or "version mismatch" in result.stderr
    assert not (runner_temp / "native-tools" / toolchain).exists()
    assert not github_path.read_text() and not github_env.read_text()


def test_qualification_go_is_isolated_and_exports_exact_go_path(
    fake_lock: Path,
    setup_harness: SetupHarness,
) -> None:
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    payload["toolchains"]["node"]["artifact"]["url"] = (
        "file:///not-requested-node"
    )
    payload["toolchains"]["node"]["platform_artifacts"]["darwin_arm64"][
        "url"
    ] = "file:///not-requested-node"
    payload["toolchains"]["npm"]["artifact"]["url"] = (
        "file:///not-requested-npm"
    )
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    install_root = (
        setup_harness.root / ".git" / "llm-wiki-ci-qualification-go-test"
    )
    environment_file = (
        setup_harness.root / ".git" / "llm-wiki-ci-qualification-go-test.env"
    )

    completed = _run_setup(
        setup_harness,
        *_local_arguments(
            mode="qualification-go",
            install_root=install_root,
            environment_file=environment_file,
            lock=fake_lock,
        ),
        simulate_supported_go_target=True,
    )

    _assert_success(completed)
    go_binary = install_root / "go" / "bin" / "go"
    sourced = subprocess.run(
        [
            "bash",
            "-c",
            'set -euo pipefail; source "$1"; '
            'test "${LLM_WIKI_GO}" = "$2"; "${LLM_WIKI_GO}" version',
            "bash",
            str(environment_file),
            str(go_binary),
        ],
        cwd=setup_harness.root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert sourced.returncode == 0, (sourced.stdout, sourced.stderr)
    assert sourced.stdout == f"go version go{GO_VERSION} {GO_PLATFORM}\n"
    assert not (install_root / "node").exists()
    assert not (install_root / "npm.tgz").exists()


@pytest.mark.parametrize(
    ("mode", "expected_path", "expected_env"),
    [
        ("routine", "node/bin", None),
        ("qualification-go", "go/bin", "LLM_WIKI_GO="),
        ("extractor-go", "go/bin", "LLM_WIKI_GO="),
    ],
)
def test_github_setup_persists_tools_across_steps(
    fake_lock: Path,
    tmp_path: Path,
    setup_harness: SetupHarness,
    mode: str,
    expected_path: str,
    expected_env: str | None,
) -> None:
    runner_temp = tmp_path / "runner"
    runner_temp.mkdir()
    github_path = tmp_path / f"{mode}.github-path"
    github_env = tmp_path / f"{mode}.github-env"
    github_path.touch()
    github_env.touch()
    environment = {
        **os.environ,
        "GITHUB_ACTIONS": "true",
        "GITHUB_PATH": str(github_path),
        "GITHUB_ENV": str(github_env),
        "RUNNER_TEMP": str(runner_temp),
    }
    install_root = runner_temp / mode

    completed = _run_setup(
        setup_harness,
        "--mode",
        mode,
        "--install-root",
        install_root,
        "--lock",
        fake_lock,
        "--python",
        setup_harness.python,
        environment=environment,
        github_actions=True,
        simulate_supported_go_target=mode in {"qualification-go", "extractor-go"},
    )

    _assert_success(completed)
    persisted_paths = github_path.read_text(encoding="utf-8").splitlines()
    assert len(persisted_paths) == 1
    assert persisted_paths[0].endswith(expected_path)
    persisted_env = github_env.read_text(encoding="utf-8")
    if expected_env is None:
        assert persisted_env == ""
    else:
        assert persisted_env == (
            f"{expected_env}{install_root}/go/bin/go\n"
        )
    cross_step_environment = {
        **os.environ,
        "PATH": os.pathsep.join([*persisted_paths, os.environ["PATH"]]),
    }
    for line in persisted_env.splitlines():
        name, value = line.split("=", maxsplit=1)
        cross_step_environment[name] = value
    commands = (
        [
            (("node", "--version"), f"v{NODE_VERSION}\n"),
            (("npm", "--version"), f"{NPM_VERSION}\n"),
        ]
        if mode == "routine"
        else [
            (("go", "version"), f"go version go{GO_VERSION} {GO_PLATFORM}\n"),
            (
                (cross_step_environment["LLM_WIKI_GO"], "version"),
                f"go version go{GO_VERSION} {GO_PLATFORM}\n",
            ),
        ]
    )
    for command, expected_output in commands:
        cross_step = subprocess.run(
            command,
            env=cross_step_environment,
            check=False,
            capture_output=True,
            text=True,
        )
        assert cross_step.returncode == 0, (cross_step.stdout, cross_step.stderr)
        assert cross_step.stdout == expected_output


@pytest.mark.parametrize(
    ("mode", "target_name", "environment_name", "command", "expected_output"),
    [
        (
            "extractor-rust",
            "rust",
            None,
            ("cargo", "--version"),
            f"{CARGO_VERSION_OUTPUT}\n",
        ),
        (
            "extractor-haskell",
            "haskell",
            "LLM_WIKI_GHC",
            ("ghc", "--numeric-version"),
            f"{GHC_VERSION}\n",
        ),
    ],
)
def test_linux_extractor_compiler_setup_persists_exact_tool_across_steps(
    fake_lock: Path,
    setup_harness: SetupHarness,
    tmp_path: Path,
    mode: str,
    target_name: str,
    environment_name: str | None,
    command: tuple[str, str],
    expected_output: str,
) -> None:
    runner_temp, github_path, github_env, environment = _github_environment(tmp_path)
    environment = _with_fake_uname(
        tmp_path,
        environment,
        system="Linux",
        machine="x86_64",
    )
    install_root = runner_temp / "extractor-toolchains"

    completed = _run_setup(
        setup_harness,
        "--mode",
        mode,
        "--install-root",
        install_root,
        "--lock",
        fake_lock,
        "--python",
        setup_harness.python,
        environment=environment,
        github_actions=True,
    )

    _assert_success(completed)
    expected_bin = install_root / target_name / "bin"
    assert github_path.read_text(encoding="utf-8") == f"{expected_bin}\n"
    persisted_environment = github_env.read_text(encoding="utf-8")
    if environment_name is None:
        assert persisted_environment == ""
    else:
        expected_binary = expected_bin / command[0]
        assert persisted_environment == (
            f"{environment_name}={expected_binary}\n"
        )

    cross_step_environment = {
        **os.environ,
        "PATH": os.pathsep.join([str(expected_bin), os.environ["PATH"]]),
    }
    if environment_name is not None:
        name, value = persisted_environment.rstrip("\n").split("=", maxsplit=1)
        cross_step_environment[name] = value
    cross_step = subprocess.run(
        command,
        env=cross_step_environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert cross_step.returncode == 0, (cross_step.stdout, cross_step.stderr)
    assert cross_step.stdout == expected_output


@pytest.mark.parametrize("mode", ["extractor-rust", "extractor-haskell"])
def test_non_linux_extractor_compiler_modes_fail_closed_before_download(
    fake_lock: Path,
    setup_harness: SetupHarness,
    tmp_path: Path,
    mode: str,
) -> None:
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    toolchain = "rust" if mode == "extractor-rust" else "haskell"
    payload["toolchains"][toolchain]["artifact"]["url"] = (
        "file:///must-not-download"
    )
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    runner_temp, github_path, github_env, environment = _github_environment(tmp_path)
    environment = _with_fake_uname(
        tmp_path,
        environment,
        system="Darwin",
        machine="arm64",
    )
    install_root = runner_temp / "extractor-toolchains"

    completed = _run_setup(
        setup_harness,
        "--mode",
        mode,
        "--install-root",
        install_root,
        "--lock",
        fake_lock,
        "--python",
        setup_harness.python,
        environment=environment,
        github_actions=True,
    )

    assert completed.returncode != 0
    assert f"no locked {mode} artifact for Darwin/arm64" in completed.stderr
    assert not install_root.exists()
    assert github_path.read_text(encoding="utf-8") == ""
    assert github_env.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    ("mode", "toolchain", "target_name"),
    [
        ("routine", "node", "node"),
        ("routine", "npm", "node"),
        ("qualification-go", "go", "go"),
        ("extractor-go", "go", "go"),
    ],
)
def test_corrupt_locked_download_fails_before_install_or_environment_publish(
    fake_lock: Path,
    setup_harness: SetupHarness,
    mode: str,
    toolchain: str,
    target_name: str,
) -> None:
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    payload["toolchains"][toolchain]["artifact"]["sha256"] = "0" * 64
    if toolchain in {"node", "go"}:
        for artifact in payload["toolchains"][toolchain]["platform_artifacts"].values():
            artifact["sha256"] = "0" * 64
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    install_root = (
        setup_harness.root / ".git" / f"llm-wiki-ci-corrupt-{toolchain}"
    )
    environment_file = (
        setup_harness.root / ".git" / "llm-wiki-ci-must-not-exist.env"
    )

    completed = _run_setup(
        setup_harness,
        *_local_arguments(
            mode=mode,
            install_root=install_root,
            environment_file=environment_file,
            lock=fake_lock,
        ),
        simulate_supported_go_target=mode in {"qualification-go", "extractor-go"},
    )

    assert completed.returncode != 0
    assert "digest mismatch" in completed.stderr
    assert not (install_root / target_name).exists()
    assert not environment_file.exists()


@pytest.mark.parametrize(
    ("mode", "toolchain", "mismatched_output"),
    [
        ("routine", "node", "v0.0.0"),
        ("routine", "npm", "0.0.0"),
        ("qualification-go", "go", "go version go0.0.0"),
        ("extractor-go", "go", "go version go0.0.0"),
    ],
)
def test_exact_version_mismatch_fails_before_environment_publish(
    fake_lock: Path,
    setup_harness: SetupHarness,
    mode: str,
    toolchain: str,
    mismatched_output: str,
) -> None:
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    payload["toolchains"][toolchain]["version_output"] = mismatched_output
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    environment_file = (
        setup_harness.root / ".git" / "llm-wiki-ci-must-not-exist.env"
    )
    install_root = (
        setup_harness.root
        / ".git"
        / f"llm-wiki-ci-wrong-{toolchain}-version"
    )

    completed = _run_setup(
        setup_harness,
        *_local_arguments(
            mode=mode,
            install_root=install_root,
            environment_file=environment_file,
            lock=fake_lock,
        )
    )

    assert completed.returncode != 0
    assert not (install_root / ("node" if mode == "routine" else "go")).exists()
    assert not environment_file.exists()


@pytest.mark.parametrize(
    ("mode", "toolchain", "lock_member", "target_name"),
    [
        ("extractor-rust", "rust", "checksum_manifest", "rust"),
        ("extractor-rust", "rust", "artifact", "rust"),
        ("extractor-haskell", "haskell", "artifact", "haskell"),
    ],
)
def test_extractor_compiler_digest_mismatch_never_publishes_partial_install(
    fake_lock: Path,
    setup_harness: SetupHarness,
    tmp_path: Path,
    mode: str,
    toolchain: str,
    lock_member: str,
    target_name: str,
) -> None:
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    payload["toolchains"][toolchain][lock_member]["sha256"] = "0" * 64
    if toolchain == "rust" and lock_member == "artifact":
        # Keep locked metadata coherent so this case reaches the archive digest check.
        _write_fake_rust_manifest(payload, fake_lock.parent / "downloads/rust-channel.toml")
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    runner_temp, github_path, github_env, environment = _github_environment(tmp_path)
    environment = _with_fake_uname(
        tmp_path,
        environment,
        system="Linux",
        machine="x86_64",
    )
    install_root = runner_temp / "extractor-toolchains"

    completed = _run_setup(
        setup_harness,
        "--mode",
        mode,
        "--install-root",
        install_root,
        "--lock",
        fake_lock,
        "--python",
        setup_harness.python,
        environment=environment,
        github_actions=True,
    )

    assert completed.returncode != 0
    assert "digest mismatch" in completed.stderr
    assert not (install_root / target_name).exists()
    assert github_path.read_text(encoding="utf-8") == ""
    assert github_env.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    ("mode", "toolchain", "target_name"),
    [
        ("extractor-rust", "rust", "rust"),
        ("extractor-haskell", "haskell", "haskell"),
    ],
)
def test_extractor_compiler_version_mismatch_removes_install_before_publish(
    fake_lock: Path,
    setup_harness: SetupHarness,
    tmp_path: Path,
    mode: str,
    toolchain: str,
    target_name: str,
) -> None:
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    payload["toolchains"][toolchain]["version_output"] = "wrong-version"
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    runner_temp, github_path, github_env, environment = _github_environment(tmp_path)
    environment = _with_fake_uname(
        tmp_path,
        environment,
        system="Linux",
        machine="x86_64",
    )
    install_root = runner_temp / "extractor-toolchains"

    completed = _run_setup(
        setup_harness,
        "--mode",
        mode,
        "--install-root",
        install_root,
        "--lock",
        fake_lock,
        "--python",
        setup_harness.python,
        environment=environment,
        github_actions=True,
    )

    assert completed.returncode != 0
    assert "version mismatch" in completed.stderr
    assert not (install_root / target_name).exists()
    assert github_path.read_text(encoding="utf-8") == ""
    assert github_env.read_text(encoding="utf-8") == ""


def test_post_move_install_failure_is_transactional_and_retryable(
    fake_lock: Path,
    setup_harness: SetupHarness,
    tmp_path: Path,
) -> None:
    payload = json.loads(fake_lock.read_text(encoding="utf-8"))
    good_artifact = dict(payload["toolchains"]["npm"]["artifact"])
    bad_npm = tmp_path / "npm-direct-failure.tgz"
    _write_fake_npm_archive(bad_npm, direct_failure=True)
    payload["toolchains"]["npm"]["artifact"] = {
        "url": bad_npm.as_uri(),
        "sha256": _sha256(bad_npm),
    }
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    install_root = setup_harness.root / ".git" / "llm-wiki-ci-transaction"
    environment_file = (
        setup_harness.root / ".git" / "llm-wiki-ci-transaction.env"
    )
    arguments = _local_arguments(
        mode="routine",
        install_root=install_root,
        environment_file=environment_file,
        lock=fake_lock,
    )

    failed = _run_setup(setup_harness, *arguments)

    assert failed.returncode != 0
    assert not (install_root / "node").exists()
    assert not environment_file.exists()

    payload["toolchains"]["npm"]["artifact"] = good_artifact
    fake_lock.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    retried = _run_setup(setup_harness, *arguments)
    _assert_success(retried)


def test_local_environment_file_rejects_force_tracked_ignored_path(
    fake_lock: Path,
    setup_harness: SetupHarness,
) -> None:
    environment_file = setup_harness.root / "ignored" / "tracked.env"
    environment_file.write_text("tracked-sentinel\n", encoding="utf-8")
    subprocess.run(
        [
            "git",
            "-C",
            str(setup_harness.root),
            "add",
            "--force",
            "ignored/tracked.env",
        ],
        check=True,
    )
    install_root = (
        setup_harness.root / ".git" / "llm-wiki-ci-adversarial-env"
    )

    completed = _run_setup(
        setup_harness,
        *_local_arguments(
            mode="routine",
            install_root=install_root,
            environment_file=environment_file,
            lock=fake_lock,
        ),
    )

    assert completed.returncode != 0
    assert "environment file must not be tracked" in completed.stderr
    assert environment_file.read_text(encoding="utf-8") == "tracked-sentinel\n"
    assert not install_root.exists()


def test_local_install_root_rejects_force_tracked_descendant(
    fake_lock: Path,
    setup_harness: SetupHarness,
) -> None:
    install_root = setup_harness.root / "ignored" / "toolchains"
    tracked_descendant = install_root / "preserve.txt"
    tracked_descendant.parent.mkdir()
    tracked_descendant.write_text("tracked-sentinel\n", encoding="utf-8")
    subprocess.run(
        [
            "git",
            "-C",
            str(setup_harness.root),
            "add",
            "--force",
            "ignored/toolchains/preserve.txt",
        ],
        check=True,
    )
    environment_file = (
        setup_harness.root / ".git" / "llm-wiki-ci-adversarial-root.env"
    )

    completed = _run_setup(
        setup_harness,
        *_local_arguments(
            mode="routine",
            install_root=install_root,
            environment_file=environment_file,
            lock=fake_lock,
        ),
    )

    assert completed.returncode != 0
    assert "install root must not be tracked or contain tracked paths" in (
        completed.stderr
    )
    assert tracked_descendant.read_text(encoding="utf-8") == "tracked-sentinel\n"
    assert not (install_root / "node").exists()
    assert not environment_file.exists()


def test_local_install_root_rejects_force_tracked_exact_path(
    fake_lock: Path,
    setup_harness: SetupHarness,
) -> None:
    install_root = setup_harness.root / "ignored" / "tracked-root"
    install_root.write_text("tracked-sentinel\n", encoding="utf-8")
    subprocess.run(
        [
            "git",
            "-C",
            str(setup_harness.root),
            "add",
            "--force",
            "ignored/tracked-root",
        ],
        check=True,
    )
    environment_file = (
        setup_harness.root / ".git" / "llm-wiki-ci-adversarial-exact.env"
    )

    completed = _run_setup(
        setup_harness,
        *_local_arguments(
            mode="routine",
            install_root=install_root,
            environment_file=environment_file,
            lock=fake_lock,
        ),
    )

    assert completed.returncode != 0
    assert "install root must not be tracked or contain tracked paths" in (
        completed.stderr
    )
    assert install_root.read_text(encoding="utf-8") == "tracked-sentinel\n"
    assert not environment_file.exists()


def test_local_git_metadata_paths_are_limited_to_dedicated_namespace(
    fake_lock: Path,
    setup_harness: SetupHarness,
) -> None:
    git_config = setup_harness.root / ".git" / "config"
    original_config = git_config.read_bytes()

    completed = _run_setup(
        setup_harness,
        *_local_arguments(
            mode="routine",
            install_root=(
                setup_harness.root / ".git" / "llm-wiki-ci-safe-validation"
            ),
            environment_file=git_config,
            lock=fake_lock,
        ),
    )

    assert completed.returncode != 0
    assert "environment file must be ignored" in completed.stderr
    assert git_config.read_bytes() == original_config


@pytest.mark.parametrize("environment_kind", ["directory", "symlink"])
def test_local_environment_file_rejects_non_regular_target(
    fake_lock: Path,
    setup_harness: SetupHarness,
    environment_kind: str,
) -> None:
    environment_file = (
        setup_harness.root
        / ".git"
        / f"llm-wiki-ci-invalid-{environment_kind}.env"
    )
    if environment_kind == "directory":
        environment_file.mkdir()
    else:
        symlink_target = setup_harness.root / "ignored" / "symlink-target.env"
        symlink_target.write_text("preserve-target\n", encoding="utf-8")
        environment_file.symlink_to(symlink_target)
    install_root = (
        setup_harness.root
        / ".git"
        / f"llm-wiki-ci-invalid-{environment_kind}-install"
    )

    completed = _run_setup(
        setup_harness,
        *_local_arguments(
            mode="routine",
            install_root=install_root,
            environment_file=environment_file,
            lock=fake_lock,
        ),
    )

    assert completed.returncode != 0
    assert "must be absent or a non-symlink regular file" in completed.stderr
    assert not install_root.exists()
    assert not list(environment_file.parent.glob(f"{environment_file.name}.tmp.*"))
    if environment_kind == "directory":
        assert environment_file.is_dir()
        assert not list(environment_file.iterdir())
    else:
        assert environment_file.is_symlink()
        assert environment_file.read_text(encoding="utf-8") == "preserve-target\n"


def test_failed_environment_publication_removes_target_and_temporary_file(
    fake_lock: Path,
    setup_harness: SetupHarness,
) -> None:
    poison_bin = setup_harness.root / "ignored" / "publication-poison-bin"
    poison_bin.mkdir()
    chmod_wrapper = poison_bin / "chmod"
    chmod_wrapper.write_text("#!/bin/sh\nexit 75\n", encoding="utf-8")
    chmod_wrapper.chmod(0o755)
    environment = {
        **os.environ,
        "PATH": os.pathsep.join([str(poison_bin), os.environ["PATH"]]),
    }
    install_root = (
        setup_harness.root / ".git" / "llm-wiki-ci-publication-failure"
    )
    environment_file = (
        setup_harness.root / ".git" / "llm-wiki-ci-publication-failure.env"
    )

    completed = _run_setup(
        setup_harness,
        *_local_arguments(
            mode="routine",
            install_root=install_root,
            environment_file=environment_file,
            lock=fake_lock,
        ),
        environment=environment,
    )

    assert completed.returncode != 0
    assert not (install_root / "node").exists()
    assert not environment_file.exists()
    assert not list(environment_file.parent.glob(f"{environment_file.name}.tmp.*"))


def test_install_root_rejects_path_separator_character(
    fake_lock: Path,
    setup_harness: SetupHarness,
) -> None:
    install_root = setup_harness.root / "ignored" / "colon:root"
    environment_file = (
        setup_harness.root / ".git" / "llm-wiki-ci-colon-root.env"
    )

    completed = _run_setup(
        setup_harness,
        *_local_arguments(
            mode="routine",
            install_root=install_root,
            environment_file=environment_file,
            lock=fake_lock,
        ),
    )

    assert completed.returncode != 0
    assert "install root must not contain ':'" in completed.stderr
    assert not install_root.exists()
    assert not environment_file.exists()


def test_setup_source_treats_lock_and_checksum_verifier_as_authoritative() -> None:
    script = SETUP_SCRIPT.read_text(encoding="utf-8")
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    serialized_values = json.dumps(lock)
    for toolchain in ("node", "go"):
        artifact = lock["toolchains"][toolchain]["platform_artifacts"][
            "darwin_arm64"
        ]
        assert set(artifact) == {"sha256", "url"}
        assert artifact["url"].startswith("https://")
        assert "darwin-arm64" in artifact["url"]
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    arm64 = lock["toolchains"]["node"]["platform_artifacts"]["linux_arm64"]
    assert set(arm64) == {"sha256", "url"}
    assert arm64["url"] == f"https://nodejs.org/dist/v{lock['toolchains']['node']['version']}/node-v{lock['toolchains']['node']['version']}-linux-arm64.tar.xz"
    assert re.fullmatch(r"[0-9a-f]{64}", arm64["sha256"])
    for toolchain in ("go", "rust", "haskell"):
        artifact = lock["toolchains"][toolchain]["platform_artifacts"]["linux_arm64"]
        assert set(artifact) == {"sha256", "url"}
        assert artifact["url"].startswith("https://")
        assert "arm64" in artifact["url"] or "aarch64" in artifact["url"]
        assert re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])
    clippy = lock["toolchains"]["rust"]["platform_clippy_artifacts"]["linux_arm64"]
    assert set(clippy) == {"sha256", "url"}
    assert "aarch64-unknown-linux-gnu" in clippy["url"]
    assert re.fullmatch(r"[0-9a-f]{64}", clippy["sha256"])
    assert "release/qualification.py" in script
    assert "lock-value" in script
    assert "verify-download" in script
    assert "toolchains.node.version_output" in script
    assert "toolchains.npm.version_output" in script
    assert "toolchains.go.version_output" in script
    assert "toolchains.rust.checksum_manifest" in script
    assert "verify-rust-manifest" in script
    assert "--print-host-platform" in script and "--print-target-platform" in script
    assert "toolchains.rust.version_output" in script
    assert "toolchains.haskell.version_output" in script
    assert "https://" not in script
    assert not re.search(r"\b[0-9a-f]{64}\b", script)
    for match in re.findall(r'"sha256": "([0-9a-f]{64})"', serialized_values):
        assert match not in script


def test_setup_has_no_privileged_or_qualification_only_dependency_surface() -> None:
    script = SETUP_SCRIPT.read_text(encoding="utf-8").lower()

    for forbidden in (
        "secrets.",
        "permissions:",
        "contents: write",
        "id-token: write",
        "github_token",
        "gh_token",
        "actions/cache",
        "cargo-audit",
        "govulncheck",
        "rustup",
        "sudo",
    ):
        assert forbidden not in script
    # Selected Clippy metadata participates in the shared Rust manifest binding;
    # this installer must not download or invoke qualification-only components.
    clippy_metadata = re.compile(
        r'(?:rust_clippy_key="toolchains\.rust\.(?:clippy_artifact|platform_clippy_artifacts\.linux_arm64)"'
        r'|require_locked_artifact "\$\{rust_clippy_key\}")'
    )
    assert all(
        clippy_metadata.fullmatch(line.strip())
        for line in script.splitlines() if "clippy" in line
    )
    assert re.search(r"(^|\n)\s*uses:\s*", script) is None
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    import yaml
    job = yaml.safe_load(ci)["jobs"]["test"]
    ghc = next(step for step in job["steps"] if step.get("name") == "Install selected locked haskell compiler")
    assert ghc["if"] == "${{ matrix.haskell }}"
    assert "toolchains.haskell.artifact" in ghc["run"]
    assert 'test "$(uname -m)" = x86_64' in ghc["run"]


def test_local_python_contract_is_project_virtualenv_only() -> None:
    script = SETUP_SCRIPT.read_text(encoding="utf-8")

    assert ".venv/bin/python" in script
    assert "GITHUB_ACTIONS" in script
    assert re.search(r"(^|[;&|]\s*)python(?:3)?\s", script) is None


def test_every_toolchain_setup_shell_script_has_valid_bash_syntax() -> None:
    scripts = sorted((ROOT / ".github" / "scripts").glob("*toolchain*.sh"))
    assert scripts

    for script in scripts:
        completed = subprocess.run(
            ["bash", "-n", str(script)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, (script, completed.stderr)


@pytest.fixture
def worktree_setup_harness(setup_harness: SetupHarness, tmp_path: Path) -> SetupHarness:
    root = setup_harness.root
    (root / ".gitignore").write_text("ignored/\n.venv/\n", encoding="utf-8")
    common = ["git", "-C", str(root), "-c", "user.name=Worktree installer",
              "-c", "user.email=installer@example.invalid", "-c", "commit.gpgsign=false",
              "-c", f"core.hooksPath={tmp_path / 'no-hooks'}"]
    subprocess.run([*common, "add", ".gitignore", ".github", "release"], check=True, capture_output=True)
    subprocess.run([*common, "commit", "-qm", "Installer fixture"], check=True, capture_output=True)
    linked = tmp_path / "linked checkout"
    subprocess.run([*common, "worktree", "add", "--detach", str(linked), "HEAD"], check=True, capture_output=True)
    python = linked / ".venv/bin/python"
    python.parent.mkdir(parents=True)
    python.symlink_to(Path(sys.executable))
    (linked / "ignored").mkdir()
    return SetupHarness(root=linked, script=linked / ".github/scripts" / SETUP_SCRIPT.name, python=python)


def _worktree_metadata(harness: SetupHarness) -> Path:
    return Path(subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(harness.root),
         "--git-dir", str(harness.root / ".git"), "rev-parse", "--absolute-git-dir"], text=True,
    ).strip())


def test_local_worktree_setup_installs_only_in_its_metadata_and_defaults_handoff(
    worktree_setup_harness: SetupHarness, setup_harness: SetupHarness, fake_lock: Path,
) -> None:
    metadata = _worktree_metadata(worktree_setup_harness)
    install_root = metadata / "llm-wiki-ci-toolchains"
    environment = {**os.environ, "GIT_DIR": str(setup_harness.root / ".git"),
                   "GIT_COMMON_DIR": str(setup_harness.root / ".git"),
                   "GIT_WORK_TREE": str(setup_harness.root),
                   "GIT_INDEX_FILE": str(setup_harness.root / ".git/index")}
    completed = _run_setup(worktree_setup_harness, "--mode", "routine", "--install-root", install_root,
                           "--lock", fake_lock, environment=environment)
    _assert_success(completed)
    handoff = metadata / "llm-wiki-ci-toolchains.env"
    assert handoff.is_file() and (install_root / "node/bin/node").is_file()
    assert not (setup_harness.root / ".git/llm-wiki-ci-toolchains").exists()
    assert (worktree_setup_harness.root / ".git").is_file()
    observed = subprocess.run(
        ["bash", "-c", 'source "$1"; node --version; npm --version', "bash", str(handoff)],
        capture_output=True, text=True, check=False,
    )
    assert observed.returncode == 0 and observed.stdout == f"v{NODE_VERSION}\n{NPM_VERSION}\n"


@pytest.mark.parametrize("location", ["unreserved-metadata", "common-metadata", "unrelated-outside"])
@pytest.mark.parametrize("destination", ["install", "environment"])
def test_local_worktree_metadata_namespace_does_not_authorize_other_locations(
    worktree_setup_harness: SetupHarness, setup_harness: SetupHarness,
    fake_lock: Path, tmp_path: Path, location: str, destination: str,
) -> None:
    metadata = _worktree_metadata(worktree_setup_harness)
    roots = {"unreserved-metadata": metadata / "not-reserved",
             "common-metadata": setup_harness.root / ".git/llm-wiki-ci-not-this-checkout",
             "unrelated-outside": tmp_path / "llm-wiki-ci-not-owned"}
    install_root = roots[location] if destination == "install" else metadata / "llm-wiki-ci-refused"
    environment_file = roots[location] if destination == "environment" else metadata / "llm-wiki-ci-refused.env"
    completed = _run_setup(worktree_setup_harness, "--mode", "routine", "--install-root", install_root,
                           "--environment-file", environment_file, "--lock", fake_lock)
    expected = "local install root must be ignored" if destination == "install" else "local environment file must be ignored"
    assert completed.returncode != 0 and expected in completed.stderr
    assert not install_root.exists()
    assert not environment_file.exists()


def test_local_worktree_tracking_protection_ignores_ambient_alternate_index(
    worktree_setup_harness: SetupHarness, setup_harness: SetupHarness, fake_lock: Path,
) -> None:
    metadata = _worktree_metadata(worktree_setup_harness)
    tracked = worktree_setup_harness.root / "ignored/tracked.env"
    tracked.write_text("retained tracked bytes\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(worktree_setup_harness.root), "add", "--force", "ignored/tracked.env"],
                   check=True, capture_output=True)
    completed = _run_setup(worktree_setup_harness, "--mode", "routine", "--install-root", metadata / "llm-wiki-ci-refused",
                           "--environment-file", tracked, "--lock", fake_lock,
                           environment={**os.environ, "GIT_INDEX_FILE": str(setup_harness.root / ".git/index"),
                                        "GIT_DIR": str(setup_harness.root / ".git")})
    assert completed.returncode != 0 and "environment file must not be tracked" in completed.stderr
    assert tracked.read_text(encoding="utf-8") == "retained tracked bytes\n"
    assert not (metadata / "llm-wiki-ci-refused").exists()


def test_hosted_extracted_source_setup_does_not_require_git(
    setup_harness: SetupHarness, fake_lock: Path, tmp_path: Path,
) -> None:
    root = tmp_path / "extracted"
    script = root / ".github/scripts" / SETUP_SCRIPT.name
    helper = root / "release/qualification.py"
    for path in (script, helper):
        path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SETUP_SCRIPT, script)
    shutil.copy2(ROOT / "release/qualification.py", helper)
    harness = SetupHarness(root=root, script=script, python=setup_harness.python)
    runner_temp, github_path, github_env, environment = _github_environment(tmp_path)
    bin_dir = tmp_path / "no-git"
    bin_dir.mkdir()
    sentinel = tmp_path / "git-called"
    git = bin_dir / "git"
    git.write_text(f'#!/usr/bin/env bash\nprintf invoked > "{sentinel}"\nexit 91\n', encoding="utf-8")
    git.chmod(0o755)
    environment["PATH"] = str(bin_dir) + os.pathsep + environment["PATH"]
    install_root = runner_temp / "routine"
    completed = _run_setup(harness, "--mode", "routine", "--install-root", install_root,
                           "--lock", fake_lock, "--python", harness.python,
                           environment=environment, github_actions=True)
    _assert_success(completed)
    assert not (root / ".git").exists() and not sentinel.exists()
    assert github_path.read_text(encoding="utf-8").strip() == str(install_root / "node/bin")
    assert github_env.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize("marker", ["missing", "redirected"])
def test_local_setup_requires_its_own_nonredirected_git_marker(
    setup_harness: SetupHarness, fake_lock: Path, tmp_path: Path, marker: str,
) -> None:
    git_dir = setup_harness.root / ".git"
    retained = tmp_path / "retained-metadata"
    git_dir.rename(retained)
    before = (retained / "config").read_bytes()
    if marker == "redirected":
        git_dir.symlink_to(retained, target_is_directory=True)
    install_root = setup_harness.root / "ignored/toolchains"
    environment_file = setup_harness.root / "ignored/toolchains.env"
    completed = _run_setup(setup_harness, *_local_arguments(
        mode="routine", install_root=install_root, environment_file=environment_file, lock=fake_lock,
    ))
    assert completed.returncode != 0 and "requires non-redirected checkout Git metadata" in completed.stderr
    assert not install_root.exists() and not environment_file.exists()
    assert (retained / "config").read_bytes() == before
