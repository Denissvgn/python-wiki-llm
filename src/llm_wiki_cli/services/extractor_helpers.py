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
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .inventory_cache import ENV_CACHE_DIR
from .paths import render_shell_command
from . import typescript_helper_identity as ts_identity
from .io import first_unsafe_path_component

ENV_GO_BINARY = "LLM_WIKI_GO"
ENV_GHC_BINARY = "LLM_WIKI_GHC"
ENV_EXTRACTOR_TIMEOUT = "LLM_WIKI_EXTRACTOR_TIMEOUT"
DEFAULT_EXTRACTOR_TIMEOUT_SECONDS = 120
HELPER_CACHE_DIRNAME = "llm-wiki-extractors"
HELPER_MANIFEST = "current.json"
HELPER_MANIFEST_VERSION = 2
TYPESCRIPT_HELPER_MANIFEST_VERSION = ts_identity.MANIFEST_VERSION
SUPPORTED_HELPERS = ("typescript", "go", "rust", "haskell")
HELPER_TOOLCHAIN_HINTS = {
    "typescript": "Install Node.js with npm, or make node and npm available on PATH",
    "go": "Install Go or set LLM_WIKI_GO to a working Go executable",
    "rust": "Install the Rust toolchain with Cargo, or make cargo available on PATH",
    "haskell": "Install GHC 9.6.x or set LLM_WIKI_GHC to a supported GHC executable",
}
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
    from .helper_runtime import current_helper_operation
    operation = current_helper_operation()
    if cache_dir is None and operation is not None:
        cache_dir = operation.cache_dir
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


def helper_artifact_fingerprint(path: Path) -> str:
    if path.is_file():
        return _hash_labeled_files([(path.name, path)])
    if path.is_dir():
        files = [
            (candidate.relative_to(path).as_posix(), candidate)
            for candidate in path.rglob("*")
            if candidate.is_file()
        ]
        return _hash_labeled_files(files)
    return _hash_labeled_files([("<missing>", path)])


def command_output(
    cmd: list[str], *, cwd: Path | None = None, timeout: int = 15
) -> str | None:
    try:
        result = subprocess.run(
            cmd,
            input="",
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
            input="",
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
            input="",
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
    if language == "typescript":
        payload["artifact_scope"] = ts_identity.ARTIFACT_SCOPE
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _manifest_path(cache_root: Path, language: str) -> Path:
    return cache_root / language / HELPER_MANIFEST


def _write_manifest(cache_root: Path, language: str, data: dict[str, Any]) -> None:
    path = _manifest_path(cache_root, language)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    tmp_path.replace(path)


def _typescript_receipt_root(cache_root: Path, manifest: dict[str, Any]) -> Path | None:
    root = manifest.get("root")
    key = manifest.get("key")
    if (not isinstance(root, str) or "\0" in root
            or not isinstance(key, str) or re.fullmatch(r"[0-9a-f]{64}", key) is None):
        return None
    expected = cache_root / "typescript" / key
    return expected if (Path(root) == expected
                        and manifest.get("path") == str(expected / "node_modules/ts-morph")) else None


def _manifest_current(cache_root: Path, language: str) -> dict[str, Any] | None:
    # Prewarming, release inspection, and extraction must agree about which
    # legacy receipt is valid. In particular, a matching digest alone does
    # not make a foreign native executable usable on this host.
    from .helper_cache import _legacy_handle

    handle = _legacy_handle(cache_root, language)
    return None if handle is None else dict(handle.receipt)


def helper_preparation_argv(
    language: str, src_dir: str | Path = ".", cache_dir: str | None = None
) -> list[str]:
    """Describe cache-only recovery for one helper without executing or writing.

    An explicit language avoids scanning a different source-selection profile.
    The resolved cache base preserves CLI, environment, Git and worktree lookup.
    """
    if language not in SUPPORTED_HELPERS:
        raise ValueError(f"Unsupported helper language: {language}")
    from .helper_cache import cache_roots, user_helper_cache_root
    from .helper_runtime import pinned_helper

    source_root = Path(src_dir).resolve()
    cache_root = resolve_helper_cache_root(source_root, cache_dir)
    pinned = pinned_helper(language, source_root=source_root)
    if pinned is not None and pinned.cache_root in cache_roots(source_root, cache_dir):
        cache_root = pinned.cache_root
    cache_base = cache_root.parent if cache_root is not None else user_helper_cache_root().parent
    argv = [
        "llm-wiki",
        "prepare-extractors",
        "--language",
        language,
        "--src-dir",
        str(source_root),
    ]
    if not source_root.is_relative_to(Path.cwd().resolve()):
        argv.append("--allow-external-src")
    argv.extend(["--cache-dir", str(cache_base)])
    return argv


def helper_preparation_failure_hint(language: str) -> str:
    return (
        f"{HELPER_TOOLCHAIN_HINTS[language]}. "
        "If the toolchain is available, resolve the reported build/download or "
        "cache-write error. Then rerun the same preparation command."
    )


def get_prepared_binary(
    language: str, src_dir: str | Path = ".", cache_dir: str | None = None
) -> Path | None:
    from .helper_runtime import pinned_helper
    from .helper_cache import cache_roots, lookup_helper, validate_handle
    pinned = pinned_helper(language, source_root=src_dir)
    if pinned is not None and pinned.cache_root not in cache_roots(src_dir, cache_dir):
        return None
    if pinned is not None:
        return pinned.path if validate_handle(pinned) else None
    selected = lookup_helper(language, src_dir, cache_dir)
    return selected.path if selected is not None and selected.path.is_file() else None


def get_prepared_typescript_root(
    src_dir: str | Path = ".", cache_dir: str | None = None
) -> Path | None:
    from .helper_runtime import pinned_helper
    from .helper_cache import cache_roots, lookup_helper, validate_handle
    pinned = pinned_helper("typescript", source_root=src_dir)
    if pinned is not None and pinned.cache_root not in cache_roots(src_dir, cache_dir):
        return None
    if pinned is not None:
        return pinned.root if validate_handle(pinned) else None
    selected = lookup_helper("typescript", src_dir, cache_dir)
    return None if selected is None else selected.root


def missing_helper_message(
    language: str, src_dir: str | Path = ".", cache_dir: str | None = None
) -> str:
    argv = helper_preparation_argv(language, src_dir, cache_dir)
    shell = "PowerShell" if os.name == "nt" else "POSIX shell"
    command = render_shell_command(argv, windows=os.name == "nt")
    reason = f"{language} helper is not prepared (missing, stale, or invalid)."
    retry = "Then retry the original command with the same source selection and helper cache."
    return (
        f"{reason} Recovery ({shell}): `{command}`. "
        "Preparation writes the helper cache and may download dependencies or "
        "compile bundled helpers; run it only when setup is authorized. "
        f"{retry} Read-only commands never prepare helpers. "
        "If setup is unavailable, report the limitation and use targeted source/wiki evidence."
    )


def helper_identity(
    language: str, src_dir: str | Path = ".", cache_dir: str | None = None
) -> dict[str, Any]:
    """Inspect existing preparation receipts and execution runtime without setup.

    A receipt describes preparation, not the runtime currently selected by PATH.
    Fingerprints are observed identities, not a claim of release authenticity.
    """
    if language not in SUPPORTED_HELPERS:
        raise ValueError(f"Unsupported helper language: {language}")
    from . import helper_cache
    from .helper_runtime import current_helper_operation, pinned_helper

    operation = current_helper_operation()
    selected_cache = cache_dir if cache_dir is not None else operation.cache_dir if operation is not None else None
    root = resolve_helper_cache_root(src_dir, selected_cache)
    handle = pinned_helper(language, source_root=src_dir)
    issues: list[str] = []
    if handle is not None:
        if handle.cache_root not in helper_cache.cache_roots(src_dir, selected_cache):
            issues.append("helper-cache-scope-mismatch")
            handle = None
            receipt = None
        else:
            root = handle.cache_root
            receipt = dict(handle.receipt)
            if not helper_cache.validate_handle(handle):
                issues.append("artifact-unavailable-or-mismatch")
    elif operation is not None and (missing := operation.missing_scope(src_dir, language)) is not None:
        root = root or helper_cache.preparation_cache_root(src_dir, selected_cache)
        if missing != helper_cache.cache_roots(src_dir, selected_cache):
            issues.append("helper-cache-scope-mismatch")
        receipt = None
    else:
        try:
            handle = helper_cache.lookup_helper(language, src_dir, selected_cache)
        except (OSError, ValueError):
            issues.append("helper-cache-unavailable")
        if handle is not None:
            root = handle.cache_root
            receipt = dict(handle.receipt)
        else:
            if root is None:
                root = helper_cache.preparation_cache_root(src_dir, selected_cache)
            try:
                receipt = (ts_identity.read_receipt(_manifest_path(root, language)) if language == "typescript"
                           else helper_cache._json(_manifest_path(root, language)))
            except (OSError, ValueError):
                receipt = None
    if not isinstance(receipt, dict):
        receipt = None
    source = helper_source_fingerprint(language)
    current = receipt if handle is not None and not issues else None
    artifact = None
    execution_source = None
    if receipt is None:
        issues.append("receipt-unavailable")
    else:
        expected_version = TYPESCRIPT_HELPER_MANIFEST_VERSION if language == "typescript" else HELPER_MANIFEST_VERSION
        for key, expected in (("version", expected_version),
                              ("language", language), ("platform", platform_id()),
                              ("source_fingerprint", source)):
            if receipt.get(key) != expected:
                issues.append(key.replace("_", "-") + "-mismatch")
        if language == "typescript" and (
                type(receipt.get("version")) is not int
                or receipt["version"] != TYPESCRIPT_HELPER_MANIFEST_VERSION
                or receipt.get("artifact_scope") != ts_identity.ARTIFACT_SCOPE):
            issues.append("typescript-dependency-identity-unavailable")
        try:
            if current is not None:
                artifact = current.get("artifact_fingerprint")
            elif language == "typescript" and receipt.get("artifact_scope") == ts_identity.ARTIFACT_SCOPE:
                prepared_root = None if root is None else _typescript_receipt_root(root, receipt)
                if prepared_root is not None:
                    helper_cache._safe(prepared_root)
                    artifact = ts_identity.dependency_fingerprint(prepared_root / "node_modules")
            elif language != "typescript":
                key, path = receipt.get("key"), receipt.get("path")
                if (root is not None and isinstance(key, str) and re.fullmatch(r"[0-9a-f]{64}", key)
                        and isinstance(path, str)):
                    candidate = Path(os.path.abspath(path))
                    if candidate.is_relative_to(root / language / key):
                        helper_cache._safe(candidate)
                        helper_cache._native_binary(candidate)
                        artifact = helper_cache._native_fingerprint(candidate)
            if artifact != receipt.get("artifact_fingerprint") or artifact is None:
                issues.append("artifact-unavailable-or-mismatch")
        except (OSError, ValueError):
            issues.append("artifact-unavailable")
        if current is None and not issues:
            issues.append("invalid-receipt")
        if language == "typescript":
            try:
                prepared_root = None if root is None else _typescript_receipt_root(root, receipt)
                if prepared_root is not None:
                    helper_cache._safe(prepared_root)
                if prepared_root is None or not (prepared_root / "extract.js").is_file():
                    issues.append("typescript-root-unavailable")
                if prepared_root is not None:
                    execution_source = ts_identity.execution_source_fingerprint(prepared_root, _TS_FILES)
                    if execution_source != source:
                        issues.append("execution-source-mismatch")
            except (OSError, ValueError):
                issues.append("typescript-root-unavailable")
    runtime: dict[str, Any] = {"kind": "native-helper", "path": None if current is None else current.get("path")}
    if language == "typescript":
        node = (handle.runtime_executables.get("node") if handle is not None else
                None if "helper-cache-scope-mismatch" in issues else shutil.which("node"))
        version = command_output([node, "--version"]) if node else None
        runtime = {"kind": "node", "path": node, "version": version}
        if not version:
            issues.append("active-runtime-unavailable")
        elif receipt is not None and not str(receipt.get("toolchain", "")).startswith("node " + version + ";"):
            issues.append("active-runtime-mismatch")
    runtime_only = bool(issues) and all(issue.startswith("active-runtime-") for issue in issues)
    recovery = None
    if runtime_only:
        recovery = (
            "The prepared helper is current. Select the Node runtime recorded in "
            f"the preparation toolchain before retrying with the same source selection and helper cache {root}. "
            "Preparing an already-current helper does not change active PATH."
        )
    elif issues:
        recovery = missing_helper_message(language, src_dir, None if root is None else str(root.parent))
    return {
        "language": language,
        "status": "ready" if not issues else "unavailable-or-mismatched",
        "issues": issues,
        "cache_root": None if root is None else str(root),
        "current_source_fingerprint": source,
        "current_artifact_fingerprint": artifact,
        "execution_source_fingerprint": execution_source,
        "prepared": None if receipt is None else {
            key: receipt.get(key) for key in (
                "version", "language", "platform", "source_fingerprint",
                "artifact_fingerprint", "path", "toolchain",
            )
        },
        "active_runtime": runtime,
        "recovery": recovery,
        "preparation_argv": helper_preparation_argv(language, src_dir, None if root is None else str(root.parent)),
        "qualification": (
            "Observed receipt and local bytes; no dependencies installed, no release authenticity established."
            + (" TypeScript scope: complete prepared node_modules tree."
               if language == "typescript" and current is not None else
               " TypeScript dependency-tree identity is unqualified; older artifact-path hashes are not promoted."
               if language == "typescript" else "")
        ),
    }


def typescript_dependencies_ready(
    src_dir: str | Path = ".", cache_dir: str | None = None
) -> bool:
    return get_prepared_typescript_root(src_dir, cache_dir) is not None


def prepare_typescript(cache_root: Path) -> HelperPrepareResult:
    node_executable = shutil.which("node")
    if node_executable is None:
        return HelperPrepareResult("typescript", "failed", "node not found")
    npm_executable = shutil.which("npm")
    if npm_executable is None:
        return HelperPrepareResult("typescript", "failed", "npm not found")
    node_version = command_output([node_executable, "--version"])
    npm_version = command_output([npm_executable, "--version"])
    if node_version is None:
        return HelperPrepareResult(
            "typescript", "failed", "node version probe failed"
        )
    if npm_version is None:
        return HelperPrepareResult("typescript", "failed", "npm version probe failed")

    toolchain = f"node {node_version}; npm {npm_version}"
    key = helper_cache_key("typescript", toolchain_version=toolchain)
    build_root = cache_root / "typescript" / key
    dependency_path = build_root / "node_modules" / "ts-morph"
    if (first_unsafe_path_component(dependency_path) is not None
            or any(first_unsafe_path_component(build_root / name) is not None for name in _TS_FILES)):
        return HelperPrepareResult("typescript", "failed", "TypeScript helper cache traverses an unsafe link")
    current = _manifest_current(cache_root, "typescript")
    if (
        current
        and current.get("key") == key
        and Path(str(current["path"])) == dependency_path
    ):
        return HelperPrepareResult(
            "typescript",
            "already_current",
            "TypeScript helper already prepared",
            str(dependency_path),
        )

    build_root.mkdir(parents=True, exist_ok=True)
    for relative_name, source_path in helper_source_files("typescript"):
        destination = build_root / relative_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)

    try:
        subprocess.run(
            [
                npm_executable,
                "ci",
                "--ignore-scripts",
                "--no-audit",
                "--no-fund",
                # An in-project cache can match its parent's npm workspaces.
                # Pin the local package before npm decides which tree to clean.
                "--prefix", str(build_root.resolve()),
                "--workspaces=false",
            ],
            capture_output=True,
            check=True,
            timeout=120,
            cwd=str(build_root),
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        return HelperPrepareResult(
            "typescript", "failed", f"npm ci failed: {exc.stderr.strip()}"
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return HelperPrepareResult(
            "typescript", "failed", "npm ci timed out or was not found"
        )

    if not dependency_path.is_dir():
        return HelperPrepareResult(
            "typescript", "failed", "ts-morph dependency missing after npm ci"
        )

    try:
        artifact_fingerprint = ts_identity.dependency_fingerprint(build_root / "node_modules")
    except (OSError, ValueError) as exc:
        return HelperPrepareResult("typescript", "failed", f"TypeScript dependency identity unavailable: {exc}")
    data = {
        "version": TYPESCRIPT_HELPER_MANIFEST_VERSION,
        "artifact_scope": ts_identity.ARTIFACT_SCOPE,
        "language": "typescript",
        "platform": platform_id(),
        "source_fingerprint": helper_source_fingerprint("typescript"),
        "artifact_fingerprint": artifact_fingerprint,
        "toolchain": toolchain,
        "node_executable": node_executable,
        "npm_executable": npm_executable,
        "key": key,
        "root": str(build_root),
        "path": str(dependency_path),
    }
    _write_manifest(cache_root, "typescript", data)
    return HelperPrepareResult(
        "typescript", "prepared", "TypeScript helper prepared", data["path"]
    )


def _unsafe_native_output(path: Path) -> bool:
    if first_unsafe_path_component(path) is not None:
        return True
    return path.exists() and (not path.is_file() or path.stat().st_nlink != 1)


def _publish_native_helper(
    cache_root: Path, language: str, binary_path: Path, key: str,
    toolchain: str, *, staged: Path | None = None, **metadata: str,
) -> HelperPrepareResult:
    from .helper_cache import _native_binary, _native_fingerprint

    try:
        output = staged if staged is not None else binary_path
        _native_binary(output)
        fingerprint = _native_fingerprint(output)
        if staged is not None:
            os.replace(staged, binary_path)
    except (OSError, ValueError) as error:
        return HelperPrepareResult(language, "failed", f"Unusable {language} build output: {error}")

    _write_manifest(cache_root, language, {
        "version": HELPER_MANIFEST_VERSION,
        "language": language,
        "platform": platform_id(),
        "source_fingerprint": helper_source_fingerprint(language),
        "artifact_fingerprint": fingerprint,
        "toolchain": toolchain,
        "key": key,
        "path": str(binary_path),
        **metadata,
    })
    return HelperPrepareResult(language, "prepared", f"{language.capitalize()} helper built", str(binary_path))


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
    if _unsafe_native_output(binary_path):
        return HelperPrepareResult("go", "failed", "Native helper output is not a safe cache file")
    current = _manifest_current(cache_root, "go")
    if current and Path(str(current["path"])) == binary_path and binary_path.is_file():
        return HelperPrepareResult(
            "go", "already_current", "Go helper already prepared", str(binary_path)
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    build_env = os.environ.copy()
    if not _env_has_value(build_env, "GOCACHE"):
        build_env["GOCACHE"] = str(cache_root / "go-build-cache")
    # Go refuses to overwrite a damaged non-object file. Build beside the
    # recorded output, then replace it only after checking the native binary.
    with tempfile.TemporaryDirectory(prefix=".build-", dir=out_dir) as temporary:
        output = Path(temporary) / binary_path.name
        try:
            subprocess.run(
                [go_executable, "build", "-o", str(output), "."],
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
        if not output.is_file():
            return HelperPrepareResult(
                "go", "failed", "go build did not produce the expected helper binary"
            )

        return _publish_native_helper(cache_root, "go", binary_path, key, toolchain, staged=output, go_executable=go_executable)


def prepare_rust(cache_root: Path) -> HelperPrepareResult:
    toolchain = command_output(["cargo", "--version"])
    if toolchain is None:
        return HelperPrepareResult("rust", "failed", "cargo not found")

    key = helper_cache_key("rust", toolchain_version=toolchain)
    build_root = cache_root / "rust" / key
    binary_path = build_root / _binary_name("llm-wiki-rust-extractor")
    if _unsafe_native_output(binary_path):
        return HelperPrepareResult("rust", "failed", "Native helper output is not a safe cache file")
    current = _manifest_current(cache_root, "rust")
    legacy_path = build_root / "target" / "release" / binary_path.name
    if current and Path(current["path"]) in (binary_path, legacy_path):
        return HelperPrepareResult(
            "rust", "already_current", "Rust helper already prepared", str(current["path"])
        )

    build_root.mkdir(parents=True, exist_ok=True)
    # Cargo may hardlink its executable to a file in target/release/deps.
    # Keep Cargo's whole tree private, then publish an independently owned
    # executable through the same native validation as the other helpers.
    with tempfile.TemporaryDirectory(prefix=".build-", dir=build_root) as temporary:
        stage = Path(temporary)
        target_dir = stage / "target"
        try:
            subprocess.run(
                ["cargo", "build", "--locked", "--release", "--target-dir", str(target_dir)],
                capture_output=True, text=True, check=True, timeout=180,
                cwd=str(RUST_SCRIPTS_DIR),
            )
        except subprocess.CalledProcessError as exc:
            return HelperPrepareResult("rust", "failed", f"cargo build failed: {exc.stderr.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return HelperPrepareResult("rust", "failed", "cargo build timed out or cargo was not found")

        built = target_dir / "release" / binary_path.name
        if first_unsafe_path_component(built) is not None or not built.is_file():
            return HelperPrepareResult("rust", "failed", "cargo build did not produce a regular helper binary")
        staged = stage / binary_path.name
        shutil.copy2(built, staged)
        return _publish_native_helper(cache_root, "rust", binary_path, key, toolchain, staged=staged)



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
    if _unsafe_native_output(binary_path):
        return HelperPrepareResult("haskell", "failed", "Native helper output is not a safe cache file")
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
                "-Wall",
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

    return _publish_native_helper(cache_root, "haskell", binary_path, key, toolchain, ghc_executable=ghc_executable)


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
