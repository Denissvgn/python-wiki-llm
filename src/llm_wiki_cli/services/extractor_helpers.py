"""Preparation and lookup for external extractor helper tools."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .inventory_cache import ENV_CACHE_DIR

HELPER_CACHE_DIRNAME = "llm-wiki-extractors"
HELPER_MANIFEST = "current.json"
HELPER_MANIFEST_VERSION = 1
SUPPORTED_HELPERS = ("typescript", "go", "rust")

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
TS_SCRIPTS_DIR = _PACKAGE_ROOT / "extractors" / "ts_scripts"
GO_SCRIPTS_DIR = _PACKAGE_ROOT / "extractors" / "go_scripts"
RUST_SCRIPTS_DIR = _PACKAGE_ROOT / "extractors" / "rust_scripts"

_TS_FILES = ("extract.js", "package.json", "package-lock.json")
_GO_FILES = ("main.go", "go.mod", "go.sum")
_RUST_FILES = ("Cargo.toml", "Cargo.lock", "src/main.rs")


@dataclass(frozen=True)
class HelperPrepareResult:
    language: str
    status: str  # prepared | already_current | skipped | failed
    message: str
    path: str | None = None


def _binary_name(base: str) -> str:
    return f"{base}.exe" if sys.platform == "win32" else base


def _resolve_gitdir_file(git_file: Path) -> Path | None:
    try:
        text = git_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    prefix = "gitdir:"
    if not text.lower().startswith(prefix):
        return None
    raw_path = text[len(prefix):].strip()
    gitdir = Path(raw_path)
    if not gitdir.is_absolute():
        gitdir = git_file.parent / gitdir
    return gitdir.resolve()


def _nearest_git_dir(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        dot_git = candidate / ".git"
        if dot_git.is_dir():
            return dot_git
        if dot_git.is_file():
            gitdir = _resolve_gitdir_file(dot_git)
            if gitdir is not None:
                return gitdir
    return None


def resolve_helper_cache_root(
    src_dir: str | Path,
    cache_dir: str | None = None,
    *,
    env: dict[str, str] | None = None,
) -> Path | None:
    """Resolve the helper cache root using CLI/env/git precedence."""
    env_map = env if env is not None else os.environ
    configured_dir = cache_dir or env_map.get(ENV_CACHE_DIR)
    if configured_dir:
        base = Path(configured_dir).expanduser()
        if not base.is_absolute():
            base = Path.cwd() / base
        return base.resolve() / HELPER_CACHE_DIRNAME

    git_dir = _nearest_git_dir(Path(src_dir))
    if git_dir is None:
        return None
    return git_dir / HELPER_CACHE_DIRNAME


def platform_id() -> str:
    return f"{platform.system().lower()}-{platform.machine().lower()}"


def _hash_labeled_files(paths: list[tuple[str, Path]]) -> str:
    hasher = hashlib.sha256()
    for label, path in sorted(paths, key=lambda item: item[0]):
        hasher.update(label.replace("\\", "/").encode("utf-8"))
        hasher.update(b"\0")
        try:
            hasher.update(path.read_bytes())
        except OSError:
            hasher.update(b"<missing>")
        hasher.update(b"\0")
    return "sha256:" + hasher.hexdigest()


def helper_source_files(language: str) -> list[tuple[str, Path]]:
    if language == "typescript":
        root = TS_SCRIPTS_DIR
        names = _TS_FILES
    elif language == "go":
        root = GO_SCRIPTS_DIR
        names = _GO_FILES
    elif language == "rust":
        root = RUST_SCRIPTS_DIR
        names = _RUST_FILES
    else:
        raise ValueError(f"Unsupported helper language: {language}")
    return [
        (name, root / name)
        for name in names
        if (root / name).exists()
    ]


def helper_source_fingerprint(language: str) -> str:
    return _hash_labeled_files(helper_source_files(language))


def command_output(cmd: list[str], *, cwd: Path | None = None, timeout: int = 15) -> str | None:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            cwd=str(cwd) if cwd is not None else None,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None
    return (result.stdout or result.stderr).strip()


def helper_cache_key(
    language: str,
    *,
    toolchain_version: str | None = None,
    platform_value: str | None = None,
) -> str:
    payload = {
        "language": language,
        "platform": platform_value or platform_id(),
        "source": helper_source_fingerprint(language),
        "toolchain": toolchain_version or "",
    }
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _manifest_path(cache_root: Path, language: str) -> Path:
    return cache_root / language / HELPER_MANIFEST


def _load_manifest(cache_root: Path, language: str) -> dict[str, Any] | None:
    path = _manifest_path(cache_root, language)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_manifest(cache_root: Path, language: str, data: dict[str, Any]) -> None:
    path = _manifest_path(cache_root, language)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _manifest_current(cache_root: Path, language: str) -> dict[str, Any] | None:
    manifest = _load_manifest(cache_root, language)
    if not manifest:
        return None
    if manifest.get("version") != HELPER_MANIFEST_VERSION:
        return None
    if manifest.get("language") != language:
        return None
    if manifest.get("platform") != platform_id():
        return None
    if manifest.get("source_fingerprint") != helper_source_fingerprint(language):
        return None
    path_value = manifest.get("path")
    if language in {"go", "rust"}:
        if not isinstance(path_value, str) or not Path(path_value).is_file():
            return None
    return manifest


def _prepared_message(language: str) -> str:
    return (
        f"{language} helper is not prepared. Run "
        "`llm-wiki prepare-extractors` before lint/extract."
    )


def get_prepared_binary(language: str, src_dir: str | Path = ".", cache_dir: str | None = None) -> Path | None:
    cache_root = resolve_helper_cache_root(src_dir, cache_dir)
    if cache_root is None:
        return None
    manifest = _manifest_current(cache_root, language)
    if not manifest:
        return None
    path_value = manifest.get("path")
    if not isinstance(path_value, str):
        return None
    path = Path(path_value)
    return path if path.is_file() else None


def missing_helper_message(language: str, src_dir: str | Path = ".", cache_dir: str | None = None) -> str:
    cache_root = resolve_helper_cache_root(src_dir, cache_dir)
    if cache_root is None:
        return (
            f"{language} helper cache directory is unavailable. Run "
            "`llm-wiki prepare-extractors --cache-dir PATH` before lint/extract."
        )
    return _prepared_message(language)


def typescript_dependencies_ready() -> bool:
    return (TS_SCRIPTS_DIR / "node_modules" / "ts-morph").exists()


def prepare_typescript(cache_root: Path) -> HelperPrepareResult:
    if shutil.which("node") is None:
        return HelperPrepareResult("typescript", "failed", "node not found")
    if typescript_dependencies_ready():
        return HelperPrepareResult("typescript", "already_current", "TypeScript dependencies already installed")
    if shutil.which("npm") is None:
        return HelperPrepareResult("typescript", "failed", "npm not found")

    try:
        subprocess.run(
            ["npm", "install"],
            capture_output=True,
            check=True,
            timeout=120,
            cwd=str(TS_SCRIPTS_DIR),
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        return HelperPrepareResult("typescript", "failed", f"npm install failed: {exc.stderr.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return HelperPrepareResult("typescript", "failed", "npm install timed out or was not found")

    if not typescript_dependencies_ready():
        return HelperPrepareResult("typescript", "failed", "ts-morph dependency missing after npm install")

    data = {
        "version": HELPER_MANIFEST_VERSION,
        "language": "typescript",
        "platform": platform_id(),
        "source_fingerprint": helper_source_fingerprint("typescript"),
        "path": str(TS_SCRIPTS_DIR / "node_modules" / "ts-morph"),
    }
    _write_manifest(cache_root, "typescript", data)
    return HelperPrepareResult("typescript", "prepared", "TypeScript dependencies installed", data["path"])


def prepare_go(cache_root: Path) -> HelperPrepareResult:
    toolchain = command_output(["go", "version"])
    if toolchain is None:
        return HelperPrepareResult("go", "failed", "go not found")

    key = helper_cache_key("go", toolchain_version=toolchain)
    out_dir = cache_root / "go" / key
    binary_path = out_dir / _binary_name("llm-wiki-go-extractor")
    current = _manifest_current(cache_root, "go")
    if current and Path(str(current["path"])) == binary_path and binary_path.is_file():
        return HelperPrepareResult("go", "already_current", "Go helper already prepared", str(binary_path))

    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["go", "build", "-o", str(binary_path), "."],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
            cwd=str(GO_SCRIPTS_DIR),
        )
    except subprocess.CalledProcessError as exc:
        return HelperPrepareResult("go", "failed", f"go build failed: {exc.stderr.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return HelperPrepareResult("go", "failed", "go build timed out or go was not found")
    if not binary_path.is_file():
        return HelperPrepareResult("go", "failed", "go build did not produce the expected helper binary")

    data = {
        "version": HELPER_MANIFEST_VERSION,
        "language": "go",
        "platform": platform_id(),
        "source_fingerprint": helper_source_fingerprint("go"),
        "toolchain": toolchain,
        "key": key,
        "path": str(binary_path),
    }
    _write_manifest(cache_root, "go", data)
    return HelperPrepareResult("go", "prepared", "Go helper built", str(binary_path))


def prepare_rust(cache_root: Path) -> HelperPrepareResult:
    toolchain = command_output(["cargo", "--version"])
    if toolchain is None:
        return HelperPrepareResult("rust", "failed", "cargo not found")

    key = helper_cache_key("rust", toolchain_version=toolchain)
    build_root = cache_root / "rust" / key
    target_dir = build_root / "target"
    binary_path = target_dir / "release" / _binary_name("llm-wiki-rust-extractor")
    current = _manifest_current(cache_root, "rust")
    if current and Path(str(current["path"])) == binary_path and binary_path.is_file():
        return HelperPrepareResult("rust", "already_current", "Rust helper already prepared", str(binary_path))

    build_root.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["cargo", "build", "--release", "--target-dir", str(target_dir)],
            capture_output=True,
            text=True,
            check=True,
            timeout=180,
            cwd=str(RUST_SCRIPTS_DIR),
        )
    except subprocess.CalledProcessError as exc:
        return HelperPrepareResult("rust", "failed", f"cargo build failed: {exc.stderr.strip()}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return HelperPrepareResult("rust", "failed", "cargo build timed out or cargo was not found")
    if not binary_path.is_file():
        return HelperPrepareResult("rust", "failed", "cargo build did not produce the expected helper binary")

    data = {
        "version": HELPER_MANIFEST_VERSION,
        "language": "rust",
        "platform": platform_id(),
        "source_fingerprint": helper_source_fingerprint("rust"),
        "toolchain": toolchain,
        "key": key,
        "path": str(binary_path),
    }
    _write_manifest(cache_root, "rust", data)
    return HelperPrepareResult("rust", "prepared", "Rust helper built", str(binary_path))


def prepare_helper(language: str, cache_root: Path) -> HelperPrepareResult:
    if language == "typescript":
        return prepare_typescript(cache_root)
    if language == "go":
        return prepare_go(cache_root)
    if language == "rust":
        return prepare_rust(cache_root)
    return HelperPrepareResult(language, "failed", f"Unsupported helper language: {language}")
