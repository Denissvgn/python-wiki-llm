"""Preparation and lookup for external extractor helper tools."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .inventory_cache import ENV_CACHE_DIR

ENV_GO_BINARY = "LLM_WIKI_GO"
ENV_GHC_BINARY = "LLM_WIKI_GHC"
ENV_EXTRACTOR_TIMEOUT = "LLM_WIKI_EXTRACTOR_TIMEOUT"
DEFAULT_EXTRACTOR_TIMEOUT_SECONDS = 120
HELPER_CACHE_DIRNAME = "llm-wiki-extractors"
HELPER_MANIFEST = "current.json"
HELPER_MANIFEST_VERSION = 1
SUPPORTED_HELPERS = ("typescript", "go", "rust", "haskell")
SUPPORTED_GHC_MAJOR = 9
SUPPORTED_GHC_MINOR = 6

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
TS_SCRIPTS_DIR = _PACKAGE_ROOT / "extractors" / "ts_scripts"
GO_SCRIPTS_DIR = _PACKAGE_ROOT / "extractors" / "go_scripts"
RUST_SCRIPTS_DIR = _PACKAGE_ROOT / "extractors" / "rust_scripts"
HASKELL_SCRIPTS_DIR = _PACKAGE_ROOT / "extractors" / "haskell_scripts"

_TS_FILES = ("extract.js", "package.json", "package-lock.json")
_GO_FILES = ("main.go", "go.mod", "go.sum")
_RUST_FILES = ("Cargo.toml", "Cargo.lock", "src/main.rs")
_HASKELL_FILES = ("Main.hs", "Inventory.hs", "Parser.hs", "Paths.hs", "Json.hs")


@dataclass(frozen=True)
class HelperPrepareResult:
    language: str
    status: str  # prepared | already_current | skipped | failed
    message: str
    path: str | None = None


def extractor_timeout_seconds() -> int:
    """Return the configured extractor runtime timeout, with a one-second floor."""

    raw_value = os.environ.get(ENV_EXTRACTOR_TIMEOUT)
    if raw_value is None:
        return DEFAULT_EXTRACTOR_TIMEOUT_SECONDS
    try:
        configured = int(raw_value)
    except ValueError:
        return DEFAULT_EXTRACTOR_TIMEOUT_SECONDS
    return max(1, configured)


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
    raw_path = text[len(prefix) :].strip()
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
    elif language == "haskell":
        root = HASKELL_SCRIPTS_DIR
        names = _HASKELL_FILES
    else:
        raise ValueError(f"Unsupported helper language: {language}")
    return [(name, root / name) for name in names if (root / name).exists()]


def helper_source_fingerprint(language: str) -> str:
    return _hash_labeled_files(helper_source_files(language))


def command_output(
    cmd: list[str], *, cwd: Path | None = None, timeout: int = 15
) -> str | None:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
            cwd=str(cwd) if cwd is not None else None,
        )
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return None
    return (result.stdout or result.stderr).strip()


def _resolve_go_executable(env: dict[str, str] | None = None) -> str | None:
    env_map = env if env is not None else os.environ
    configured = env_map.get(ENV_GO_BINARY)
    if configured:
        expanded = str(Path(configured).expanduser())
        search_path = env_map.get("PATH")
        resolved = shutil.which(expanded, path=search_path)
        return resolved
    return shutil.which("go", path=env_map.get("PATH"))


def _resolve_ghc_executable(env: dict[str, str] | None = None) -> str | None:
    env_map = env if env is not None else os.environ
    configured = env_map.get(ENV_GHC_BINARY)
    if configured:
        expanded = str(Path(configured).expanduser())
        search_path = env_map.get("PATH")
        return shutil.which(expanded, path=search_path)
    return shutil.which("ghc", path=env_map.get("PATH"))


def _go_version(go_executable: str, *, timeout: int = 15) -> tuple[str | None, str]:
    try:
        result = subprocess.run(
            [go_executable, "version"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return None, "executable not found"
    except subprocess.TimeoutExpired:
        return None, f"timed out after {timeout} s"

    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        detail = (
            result.stderr or result.stdout
        ).strip() or f"exit code {result.returncode}"
        return None, detail
    return output, ""


def _ghc_version(ghc_executable: str, *, timeout: int = 15) -> tuple[str | None, str]:
    try:
        result = subprocess.run(
            [ghc_executable, "--numeric-version"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return None, "executable not found"
    except subprocess.TimeoutExpired:
        return None, f"version probe timed out after {timeout} s"

    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        detail = (
            result.stderr or result.stdout
        ).strip() or f"exit code {result.returncode}"
        return None, detail
    version = output.splitlines()[0].strip() if output else ""
    return f"ghc {version}" if version else "ghc", ""


def _parse_ghc_version(toolchain: str) -> tuple[int, int, int] | None:
    match = re.search(r"(?<!\d)(\d+)\.(\d+)(?:\.(\d+))?(?!\d)", toolchain)
    if match is None:
        return None
    patch = int(match.group(3) or 0)
    return int(match.group(1)), int(match.group(2)), patch


def _ghc_support_error(toolchain: str) -> str | None:
    version = _parse_ghc_version(toolchain)
    if version is None:
        return (
            "unsupported GHC version output: "
            f"{toolchain}; expected a numeric version such as ghc 9.6.7"
        )
    major, minor, _patch = version
    if major != SUPPORTED_GHC_MAJOR or minor < SUPPORTED_GHC_MINOR:
        return (
            "Haskell helper requires GHC 9.6.x for the supported release line "
            "or newer GHC 9.x on a best-effort basis; "
            f"found {toolchain}"
        )
    return None


def _env_has_value(env: dict[str, str], name: str) -> bool:
    """Return True when *env* contains a non-empty variable named *name*.

    Windows environment variables are case-insensitive.  Treating only the
    exact spelling as present can override a user-provided ``GoCache`` or
    ``gocache`` value when building helper binaries.
    """
    if env.get(name):
        return True
    if os.name == "nt":
        wanted = name.upper()
        return any(key.upper() == wanted and bool(value) for key, value in env.items())
    return False


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
    tmp_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
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
    if language in {"go", "rust", "haskell"}:
        if not isinstance(path_value, str) or not Path(path_value).is_file():
            return None
    return manifest


def _prepared_message(language: str) -> str:
    return (
        f"{language} helper is not prepared. Run "
        "`llm-wiki prepare-extractors` before lint/extract."
    )


def get_prepared_binary(
    language: str, src_dir: str | Path = ".", cache_dir: str | None = None
) -> Path | None:
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


def missing_helper_message(
    language: str, src_dir: str | Path = ".", cache_dir: str | None = None
) -> str:
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
        return HelperPrepareResult(
            "typescript", "already_current", "TypeScript dependencies already installed"
        )
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
        return HelperPrepareResult(
            "typescript", "failed", f"npm install failed: {exc.stderr.strip()}"
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return HelperPrepareResult(
            "typescript", "failed", "npm install timed out or was not found"
        )

    if not typescript_dependencies_ready():
        return HelperPrepareResult(
            "typescript", "failed", "ts-morph dependency missing after npm install"
        )

    data = {
        "version": HELPER_MANIFEST_VERSION,
        "language": "typescript",
        "platform": platform_id(),
        "source_fingerprint": helper_source_fingerprint("typescript"),
        "path": str(TS_SCRIPTS_DIR / "node_modules" / "ts-morph"),
    }
    _write_manifest(cache_root, "typescript", data)
    return HelperPrepareResult(
        "typescript", "prepared", "TypeScript dependencies installed", data["path"]
    )


def prepare_go(cache_root: Path) -> HelperPrepareResult:
    go_executable = _resolve_go_executable()
    if go_executable is None:
        return HelperPrepareResult("go", "failed", "go not found")

    toolchain, version_error = _go_version(go_executable)
    if toolchain is None:
        return HelperPrepareResult(
            "go",
            "failed",
            f"go found at {go_executable} but failed to run: {version_error}; "
            f"set {ENV_GO_BINARY}=/path/to/go or fix the Go installation",
        )

    key = helper_cache_key("go", toolchain_version=toolchain)
    out_dir = cache_root / "go" / key
    binary_path = out_dir / _binary_name("llm-wiki-go-extractor")
    current = _manifest_current(cache_root, "go")
    if current and Path(str(current["path"])) == binary_path and binary_path.is_file():
        return HelperPrepareResult(
            "go", "already_current", "Go helper already prepared", str(binary_path)
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    build_env = os.environ.copy()
    if not _env_has_value(build_env, "GOCACHE"):
        build_env["GOCACHE"] = str(cache_root / "go-build-cache")
    try:
        subprocess.run(
            [go_executable, "build", "-o", str(binary_path), "."],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
            cwd=str(GO_SCRIPTS_DIR),
            env=build_env,
        )
    except subprocess.CalledProcessError as exc:
        return HelperPrepareResult(
            "go", "failed", f"go build failed: {exc.stderr.strip()}"
        )
    except subprocess.TimeoutExpired:
        return HelperPrepareResult("go", "failed", "go build timed out after 120 s")
    except FileNotFoundError:
        return HelperPrepareResult(
            "go", "failed", f"go build failed: executable not found at {go_executable}"
        )
    if not binary_path.is_file():
        return HelperPrepareResult(
            "go", "failed", "go build did not produce the expected helper binary"
        )

    data = {
        "version": HELPER_MANIFEST_VERSION,
        "language": "go",
        "platform": platform_id(),
        "source_fingerprint": helper_source_fingerprint("go"),
        "toolchain": toolchain,
        "go_executable": go_executable,
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
        return HelperPrepareResult(
            "rust", "already_current", "Rust helper already prepared", str(binary_path)
        )

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
        return HelperPrepareResult(
            "rust", "failed", f"cargo build failed: {exc.stderr.strip()}"
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return HelperPrepareResult(
            "rust", "failed", "cargo build timed out or cargo was not found"
        )
    if not binary_path.is_file():
        return HelperPrepareResult(
            "rust", "failed", "cargo build did not produce the expected helper binary"
        )

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
    return HelperPrepareResult(
        "rust", "prepared", "Rust helper built", str(binary_path)
    )


def prepare_haskell(cache_root: Path) -> HelperPrepareResult:
    ghc_executable = _resolve_ghc_executable()
    if ghc_executable is None:
        return HelperPrepareResult(
            "haskell",
            "failed",
            f"ghc not found; set {ENV_GHC_BINARY}=/path/to/ghc or install GHC",
        )

    toolchain, version_error = _ghc_version(ghc_executable)
    if toolchain is None:
        return HelperPrepareResult(
            "haskell",
            "failed",
            f"ghc found at {ghc_executable} but failed to run: {version_error}; "
            f"set {ENV_GHC_BINARY}=/path/to/ghc or fix the GHC installation",
        )
    support_error = _ghc_support_error(toolchain)
    if support_error is not None:
        return HelperPrepareResult("haskell", "failed", support_error)

    key = helper_cache_key("haskell", toolchain_version=toolchain)
    out_dir = cache_root / "haskell" / key
    build_dir = out_dir / "build"
    binary_path = out_dir / _binary_name("llm-wiki-haskell-extractor")
    current = _manifest_current(cache_root, "haskell")
    if current and Path(str(current["path"])) == binary_path and binary_path.is_file():
        return HelperPrepareResult(
            "haskell",
            "already_current",
            "Haskell helper already prepared",
            str(binary_path),
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                ghc_executable,
                "-package",
                "ghc",
                "-outputdir",
                str(build_dir),
                f"-i{HASKELL_SCRIPTS_DIR}",
                "-o",
                str(binary_path),
                str(HASKELL_SCRIPTS_DIR / "Main.hs"),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=180,
            cwd=str(HASKELL_SCRIPTS_DIR),
        )
    except subprocess.CalledProcessError as exc:
        return HelperPrepareResult(
            "haskell", "failed", f"ghc build failed: {exc.stderr.strip()}"
        )
    except subprocess.TimeoutExpired:
        return HelperPrepareResult(
            "haskell", "failed", "ghc build timed out after 180 s"
        )
    except FileNotFoundError:
        return HelperPrepareResult(
            "haskell",
            "failed",
            f"ghc build failed: executable not found at {ghc_executable}",
        )
    if not binary_path.is_file():
        return HelperPrepareResult(
            "haskell", "failed", "ghc build did not produce the expected helper binary"
        )

    data = {
        "version": HELPER_MANIFEST_VERSION,
        "language": "haskell",
        "platform": platform_id(),
        "source_fingerprint": helper_source_fingerprint("haskell"),
        "toolchain": toolchain,
        "ghc_executable": ghc_executable,
        "key": key,
        "path": str(binary_path),
    }
    _write_manifest(cache_root, "haskell", data)
    return HelperPrepareResult(
        "haskell", "prepared", "Haskell helper built", str(binary_path)
    )


def prepare_helper(language: str, cache_root: Path) -> HelperPrepareResult:
    if language == "typescript":
        return prepare_typescript(cache_root)
    if language == "go":
        return prepare_go(cache_root)
    if language == "rust":
        return prepare_rust(cache_root)
    if language == "haskell":
        return prepare_haskell(cache_root)
    return HelperPrepareResult(
        language, "failed", f"Unsupported helper language: {language}"
    )
