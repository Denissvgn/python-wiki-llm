"""Transactional, project-independent storage for bundled extractor helpers.

Lookups observe existing receipts only. Preparation owns a per-profile lock and
an unpublished staging tree; consumers receive the exact validated artifact,
never a mutable language-wide current pointer.
"""

from __future__ import annotations

import ast
from contextlib import contextmanager
from dataclasses import dataclass
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Callable, TYPE_CHECKING
import uuid

from . import extractor_helpers as helpers
from .io import first_unsafe_path_component, write_json_atomic
from .knowledge_storage_io import read_guarded

if TYPE_CHECKING:
    from .helper_runtime import PreparedHelperHandle


RECEIPT = "ready.json"
SCHEMA = "llm-wiki-prepared-helper/v1"
RECIPE = "host-native/v1"
MAX_RECEIPT_BYTES = 1024 * 1024
MAX_HELPER_PROFILES = 128
MAX_NATIVE_BYTES = 512 * 1024 * 1024
LOCK_WAIT_SECONDS = 120


class HelperPreparationError(RuntimeError):
    """The selected bundled helper could not be prepared once."""

    def __init__(self, language: str, message: str, cache_root: Path | None = None):
        self.language = language
        self.reason = message
        self.cache_root = cache_root
        self.runtime_executables: dict[str, str] = {}
        super().__init__(f"{language} helper preparation failed: {message}")


def _safe(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    if first_unsafe_path_component(path) is not None:
        raise ValueError("Helper cache traverses a link or reparse point: " + str(path))
    return path


def user_helper_cache_root() -> Path:
    """Resolve the managed helper cache without inspecting or creating it."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData/Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    return Path(os.path.abspath(base.expanduser() / "agent-wiki" / helpers.HELPER_CACHE_DIRNAME))


def cache_roots(src_dir: str | Path = ".", cache_dir: str | None = None) -> tuple[Path, ...]:
    """Keep explicit/environment scope authoritative; otherwise reuse legacy data."""
    from .helper_runtime import current_helper_operation
    operation = current_helper_operation()
    if cache_dir is None and operation is not None:
        cache_dir = operation.cache_dir
    configured = cache_dir or os.environ.get(helpers.ENV_CACHE_DIR)
    if configured:
        root = helpers.resolve_helper_cache_root(src_dir, configured)
        assert root is not None
        return (Path(os.path.abspath(root)),)
    legacy = helpers.resolve_helper_cache_root(src_dir)
    shared = user_helper_cache_root()
    return tuple(dict.fromkeys([*([] if legacy is None else [legacy]), shared]))


def preparation_cache_root(src_dir: str | Path = ".", cache_dir: str | None = None) -> Path:
    roots = cache_roots(src_dir, cache_dir)
    return roots[0] if cache_dir or os.environ.get(helpers.ENV_CACHE_DIR) else roots[-1]


def _json(path: Path) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate helper receipt field")
            result[key] = value
        return result

    value = json.loads(read_guarded(_safe(path), MAX_RECEIPT_BYTES).content,
                       object_pairs_hook=unique,
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    if not isinstance(value, dict):
        raise ValueError("helper receipt must be an object")
    return value


def _machine() -> str:
    machine = platform.machine().lower()
    return {"aarch64": "arm64", "amd64": "x86_64", "x64": "x86_64",
            "i686": "i386", "i586": "i386"}.get(machine, machine)


def _system() -> str:
    return {"Darwin": "darwin", "Windows": "windows", "Linux": "linux"}.get(
        platform.system(), platform.system().lower())


def _native_binary(path: Path) -> None:
    """Reject foreign-target outputs without executing a newly built binary."""
    _safe(path)
    metadata = path.lstat()
    if (not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1
            or not 0 < metadata.st_size <= MAX_NATIVE_BYTES):
        raise ValueError("native helper is not a regular single-link file")
    with path.open("rb") as stream:
        header = stream.read(4096)
    machine, system = _machine(), _system()
    valid = False
    if system in {"linux", "freebsd", "openbsd", "netbsd"} and header[:4] == b"\x7fELF":
        expected = {"x86_64": 62, "arm64": 183, "i386": 3,
                    "armv7l": 40, "armv6l": 40, "riscv64": 243,
                    "ppc64": 21, "ppc64le": 21}.get(machine)
        if len(header) >= 20 and header[5] in {1, 2}:
            order = "little" if header[5] == 1 else "big"
            valid = expected is not None and int.from_bytes(header[18:20], order) == expected
    elif system == "windows" and header[:2] == b"MZ" and len(header) >= 64:
        offset = int.from_bytes(header[60:64], "little")
        expected = {"x86_64": 0x8664, "arm64": 0xAA64, "i386": 0x14C}.get(machine)
        if 0 <= offset <= 4090 and header[offset:offset + 4] == b"PE\0\0":
            valid = expected is not None and int.from_bytes(header[offset + 4:offset + 6], "little") == expected
    elif system == "darwin":
        expected = {"x86_64": 0x1000007, "arm64": 0x100000C, "i386": 7}.get(machine)
        little = {b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe"}
        big = {b"\xfe\xed\xfa\xcf", b"\xfe\xed\xfa\xce"}
        if header[:4] in little | big and len(header) >= 8:
            order = "little" if header[:4] in little else "big"
            valid = expected is not None and int.from_bytes(header[4:8], order) == expected
        elif header[:4] in {b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf"} and len(header) >= 8:
            count = int.from_bytes(header[4:8], "big")
            step = 20 if header[:4] == b"\xca\xfe\xba\xbe" else 32
            if 0 < count <= 16 and 8 + count * step <= len(header):
                valid = expected in {int.from_bytes(header[8 + i * step:12 + i * step], "big") for i in range(count)}
    if not valid:
        raise ValueError(f"helper output is not native for {system}/{machine}")
    if os.name != "nt" and not os.access(path, os.X_OK):
        raise ValueError("native helper is not executable")


def _runtime_paths(language: str) -> dict[str, str]:
    # Compilers are preparation inputs, not execution dependencies of a cached
    # native helper. TypeScript alone needs its selected Node process at use.
    if language != "typescript":
        return {}
    node = shutil.which("node")
    return {} if node is None else {"node": str(Path(node).resolve())}


def _native_fingerprint(path: Path) -> str:
    content = read_guarded(_safe(path), MAX_NATIVE_BYTES).content
    value = hashlib.sha256(path.name.encode("utf-8") + b"\0" + content + b"\0")
    return "sha256:" + value.hexdigest()


def _handle(cache_root: Path, language: str, key: str, root: Path,
            path: Path, receipt: dict, runtime_executables=None) -> PreparedHelperHandle:
    from .helper_runtime import PreparedHelperHandle
    return PreparedHelperHandle(language, cache_root, key, root, path, receipt,
                                runtime_executables=(_runtime_paths(language) if runtime_executables is None
                                                     else runtime_executables))


def _with_runtime(handle: PreparedHelperHandle, executables: dict[str, str]) -> PreparedHelperHandle:
    selected = {"node": executables["node"]} if handle.language == "typescript" else {}
    return _handle(handle.cache_root, handle.language, handle.key, handle.root,
                   handle.path, dict(handle.receipt), selected)


def _validate_artifact(language: str, cache_root: Path, root: Path, manifest: dict) -> Path:
    _safe(root)
    if manifest.get("language") != language or manifest.get("platform") != helpers.platform_id():
        raise ValueError("helper platform/language differs")
    if manifest.get("source_fingerprint") != helpers.helper_source_fingerprint(language):
        raise ValueError("helper source is stale")
    path = _safe(Path(manifest["path"]))
    if not root.is_relative_to(cache_root) or not path.is_relative_to(root):
        raise ValueError("helper receipt redirects outside its cache slot")
    if language == "typescript":
        if path != root / "node_modules/ts-morph" or manifest.get("root") != str(root):
            raise ValueError("TypeScript receipt path differs")
        if helpers.ts_identity.execution_source_fingerprint(root, helpers._TS_FILES) != manifest["source_fingerprint"]:
            raise ValueError("TypeScript execution source differs")
        actual = helpers.ts_identity.dependency_fingerprint(root / "node_modules")
        if manifest.get("artifact_scope") != helpers.ts_identity.ARTIFACT_SCOPE:
            raise ValueError("TypeScript artifact scope differs")
    else:
        _native_binary(path)
        actual = _native_fingerprint(path)
    if actual != manifest.get("artifact_fingerprint"):
        raise ValueError("helper artifact changed")
    return path


def _slot_handle(cache_root: Path, language: str, slot: Path) -> PreparedHelperHandle | None:
    try:
        value = _json(slot / RECEIPT)
        if set(value) != {"schema_version", "key", "profile", "manifest"} or value["schema_version"] != SCHEMA:
            return None
        key, profile, manifest = value["key"], value["profile"], value["manifest"]
        if not isinstance(key, str) or re.fullmatch(r"[0-9a-f]{64}", key) is None or slot.name != key:
            return None
        if not isinstance(profile, dict) or not isinstance(manifest, dict):
            return None
        if profile.get("recipe") != RECIPE or profile.get("host") != helpers.platform_id():
            return None
        if profile.get("source") != helpers.helper_source_fingerprint(language):
            return None
        if (_profile_key(language, profile) != key or manifest.get("key") != key
                or manifest.get("preparation_profile") != profile):
            return None
        path = _validate_artifact(language, cache_root, slot, manifest)
        return _handle(cache_root, language, key, slot, path, manifest)
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _legacy_handle(cache_root: Path, language: str) -> PreparedHelperHandle | None:
    try:
        # Validate containment and budgets before reading any artifact named by
        # a legacy current pointer. Its general legacy reader is deliberately
        # not used here: native receipts predate the guarded shared-cache API.
        manifest = _json(cache_root / language / helpers.HELPER_MANIFEST)
        expected_version = helpers.TYPESCRIPT_HELPER_MANIFEST_VERSION if language == "typescript" else helpers.HELPER_MANIFEST_VERSION
        key, toolchain = manifest.get("key"), manifest.get("toolchain")
        if (type(manifest.get("version")) is not int or manifest["version"] != expected_version
                or not isinstance(key, str) or re.fullmatch(r"[0-9a-f]{64}", key) is None
                or not isinstance(toolchain, str) or not toolchain
                or key != helpers.helper_cache_key(language, toolchain_version=toolchain)):
            return None
        path = _safe(Path(manifest["path"]))
        root = cache_root / language / key
        if not path.is_relative_to(root):
            return None
        path = _validate_artifact(language, cache_root, root, manifest)
        return _handle(cache_root, language, key, root, path, dict(manifest))
    except (OSError, ValueError, KeyError, TypeError):
        return None


def lookup_helper(language: str, src_dir: str | Path = ".", cache_dir: str | None = None) -> PreparedHelperHandle | None:
    """Inspect valid existing project/shared artifacts without writes or builds."""
    if language not in helpers.SUPPORTED_HELPERS:
        raise ValueError("Unsupported helper language: " + language)
    for root in cache_roots(src_dir, cache_dir):
        _safe(root)
        legacy = _legacy_handle(root, language)
        if legacy is not None:
            return legacy
        directory = root / language
        _safe(directory)
        if not directory.is_dir():
            continue
        slots = []
        for path in directory.iterdir():
            if re.fullmatch(r"[0-9a-f]{64}", path.name) and path.is_dir():
                slots.append(path)
                if len(slots) > MAX_HELPER_PROFILES:
                    raise ValueError("helper profile inventory exceeds bound")
        for slot in sorted(slots, key=lambda path: path.name):
            handle = _slot_handle(root, language, slot)
            if handle is not None:
                return handle
    return None


def validate_handle(handle: PreparedHelperHandle) -> bool:
    """Re-observe exactly the pinned bytes; never repair, rebind or run tools."""
    try:
        root = _safe(handle.cache_root)
        _validate_artifact(handle.language, root, handle.root, dict(handle.receipt))
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def _profile_key(language: str, profile: dict) -> str:
    value = {"language": language, **profile}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _executable_identity(executables: dict[str, str]) -> dict:
    result = {}
    for name, value in sorted(executables.items()):
        # Toolchain launchers commonly use trusted installation symlinks. They
        # are selected by the operator, unlike redirects inside managed cache.
        path = Path(value).resolve(strict=True)
        before = path.stat()
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_NATIVE_BYTES:
            raise ValueError("toolchain executable exceeds regular-file budget")
        checksum = hashlib.sha256()
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise ValueError("toolchain executable changed during inspection")
            remaining = before.st_size
            while remaining:
                data = stream.read(min(1024 * 1024, remaining))
                if not data:
                    raise ValueError("toolchain executable changed during inspection")
                checksum.update(data)
                remaining -= len(data)
            if stream.read(1):
                raise ValueError("toolchain executable changed during inspection")
        after = path.stat()
        def identity(item):
            return (item.st_dev, item.st_ino, item.st_mode, item.st_size,
                    item.st_mtime_ns, item.st_ctime_ns, item.st_nlink)
        if identity(before) != identity(after):
            raise ValueError("toolchain executable changed during inspection")
        result[name] = {"path": str(path), "sha256": checksum.hexdigest()}
    return result


@dataclass(frozen=True)
class _Profile:
    identity: dict
    executables: dict[str, str]
    environment: dict[str, str]


def _build_environment(cache_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    for name in list(env):
        upper = name.upper()
        if (upper in {"GOOS", "GOARCH", "GOARM", "GOAMD64", "GO386", "GOFLAGS", "GOWORK", "GOENV", "GOROOT", "GOEXPERIMENT",
                      "CARGO_BUILD_TARGET", "CARGO_ENCODED_RUSTFLAGS", "RUSTFLAGS", "RUSTDOCFLAGS",
                      "RUSTC", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "RUSTC_BOOTSTRAP",
                      "GHC_PACKAGE_PATH", "GHC_ENVIRONMENT", "NODE_ENV", "NODE_OPTIONS", "NODE_PATH"}
                or upper.startswith(("CARGO_TARGET_", "CARGO_BUILD_", "CARGO_PROFILE_", "NPM_CONFIG_"))):
            env.pop(name)
    dependencies = cache_root / ".dependencies"
    for path in (dependencies, dependencies / "go/build", dependencies / "go/modules",
                 dependencies / "cargo", dependencies / "npm"):
        _safe(path)
    env.update(GOENV="off", GOWORK="off", GOTOOLCHAIN="local", CGO_ENABLED="0", GOFLAGS="",
               GOCACHE=str(dependencies / "go/build"), GOMODCACHE=str(dependencies / "go/modules"),
               CARGO_HOME=str(dependencies / "cargo"), RUSTUP_AUTO_INSTALL="0",
               GHC_ENVIRONMENT="-", npm_config_cache=str(dependencies / "npm"),
               npm_config_global="false")
    return env


def _output(command: list[str], *, cwd: Path, env: dict[str, str]) -> str:
    return _run(command, cwd=cwd, env=env, timeout=30).strip()


def _target_matches(target: str) -> bool:
    architecture = target.partition("-")[0]
    arch = {"aarch64": "arm64", "x86_64": "x86_64", "i686": "i386",
            "armv7": "armv7l", "arm": "armv7l"}.get(architecture, architecture)
    system = _system()
    return arch == _machine() and (
        (system == "darwin" and "darwin" in target)
        or (system == "windows" and any(name in target for name in ("windows", "mingw32", "mingw64")))
        or (system == "linux" and "linux" in target)
        or (system not in {"darwin", "windows", "linux"} and system in target)
    )


def _profile(language: str, cache_root: Path, cwd: Path) -> _Profile:
    env = _build_environment(cache_root)
    identity: dict[str, object] = {"recipe": RECIPE, "host": helpers.platform_id(),
                                   "source": helpers.helper_source_fingerprint(language)}
    executables = {}
    if language == "typescript":
        path = shutil.which("node", path=env.get("PATH"))
        if path is None:
            raise HelperPreparationError(language, "node not found")
        # Node is executed directly, unlike compiler dispatch proxies such as
        # rustup. Pin its selected physical target rather than an nvm/current
        # alias which can be retargeted after identity capture.
        executables["node"] = str(Path(path).resolve(strict=True))
        node = _output([executables["node"], "--version"], cwd=cwd, env=env)
        actual = _output([executables["node"], "-p", "process.platform+' '+process.arch"], cwd=cwd, env=env)
        expected_os = {"windows": "win32"}.get(_system(), _system())
        expected_arch = {"x86_64": "x64", "i386": "ia32"}.get(_machine(), _machine())
        if actual != expected_os + " " + expected_arch:
            raise HelperPreparationError(language, "Node is not native for the active platform")
        path = shutil.which("npm", path=env.get("PATH"))
        if path is None:
            error = HelperPreparationError(language, "npm not found")
            error.runtime_executables = {"node": executables["node"]}
            raise error
        executables["npm"] = str(Path(os.path.abspath(path)))
        # npm commonly launches through /usr/bin/env node. Its preparation
        # process must use the same physical Node selected above even if a
        # version-manager alias in the original PATH changes during this call.
        env["PATH"] = str(Path(executables["node"]).parent) + os.pathsep + env.get("PATH", "")
        selected_node = shutil.which("node", path=env["PATH"])
        if selected_node is None or Path(selected_node).resolve(strict=True) != Path(executables["node"]):
            error = HelperPreparationError(language, "npm cannot use the selected Node executable")
            error.runtime_executables = {"node": executables["node"]}
            raise error
        try:
            npm = _output([executables["npm"], "--version"], cwd=cwd, env=env)
        except (OSError, RuntimeError, subprocess.SubprocessError) as original:
            error = HelperPreparationError(language, "npm version unavailable: " + str(original))
            error.runtime_executables = {"node": executables["node"]}
            raise error from original
        identity["toolchain"] = f"node {node}; npm {npm}"
    elif language == "go":
        executable = helpers._resolve_go_executable(env)
        if executable is None:
            raise HelperPreparationError(language, "Go compiler not found")
        executables["go"] = executable
        version = _output([executable, "version"], cwd=cwd, env=env)
        target = version.rsplit(" ", 1)[-1]
        expected_arch = {"x86_64": "amd64", "i386": "386", "armv7l": "arm"}.get(_machine(), _machine())
        if target != _system() + "/" + expected_arch:
            raise HelperPreparationError(language, "Go compiler host differs from the active platform")
        env.update(GOOS=_system(), GOARCH=expected_arch)
        identity.update(toolchain=version, target=target)
    elif language == "rust":
        for name in ("cargo", "rustc"):
            path = shutil.which(name, path=env.get("PATH"))
            if path is None:
                raise HelperPreparationError(language, name + " not found")
            executables[name] = str(Path(os.path.abspath(path)))
        version = _output([executables["cargo"], "--version"], cwd=cwd, env=env)
        rust = _output([executables["rustc"], "-vV"], cwd=cwd, env=env)
        targets = [row.partition(":")[2].strip() for row in rust.splitlines() if row.startswith("host:")]
        if len(targets) != 1 or not _target_matches(targets[0]):
            raise HelperPreparationError(language, "Rust compiler host differs from the active platform")
        env.update(RUSTC=executables["rustc"], RUSTC_WRAPPER="", RUSTC_WORKSPACE_WRAPPER="")
        identity.update(toolchain=version + "; " + rust, target=targets[0])
    elif language == "haskell":
        executable = helpers._resolve_ghc_executable(env)
        if executable is None:
            raise HelperPreparationError(language, "GHC compiler not found")
        executables["ghc"] = executable
        version = _output([executable, "--numeric-version"], cwd=cwd, env=env)
        support = helpers._ghc_support_error(version)
        if support:
            raise HelperPreparationError(language, support)
        try:
            info = dict(ast.literal_eval(_output([executable, "--info"], cwd=cwd, env=env)))
            target = info["Target platform"]
        except (ValueError, KeyError, TypeError, SyntaxError) as error:
            raise HelperPreparationError(language, "GHC target identity unavailable") from error
        if not isinstance(target, str) or not _target_matches(target):
            raise HelperPreparationError(language, "GHC compiler target differs from the active platform")
        identity.update(toolchain=version, target=target)
    identity["executables"] = _executable_identity(executables)
    return _Profile(identity, executables, env)


def _run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: float) -> str:
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=log, start_new_session=os.name != "nt")
        try:
            code = process.wait(timeout=timeout)
        except BaseException:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                               timeout=10, check=False)
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            raise
        log.seek(0)
        output = log.read(1024 * 1024).decode("utf-8", errors="replace")
    if code:
        raise RuntimeError(f"{Path(command[0]).name} exited {code}: {output[-4000:].strip()}")
    return output


@contextmanager
def _lock(path: Path, wait_seconds: float):
    deadline = time.monotonic() + wait_seconds
    _safe(path)
    if path.exists():
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError("helper lock must be a regular single-link file")
    with path.open("a+b") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError("helper lock must be a regular single-link file")
        if os.name == "nt" and stream.tell() == 0:
            stream.write(b"\0")
            stream.flush()
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as error:
                if error.errno not in {errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK}:
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError("another process is preparing this helper") from error
                time.sleep(min(0.05, max(0, deadline - time.monotonic())))
        yield


def _sandbox(source_root: Path):
    source_root = source_root.resolve()
    candidates = [Path(tempfile.gettempdir())]
    if os.name == "nt":
        if os.environ.get("LOCALAPPDATA"):
            candidates.append(Path(os.environ["LOCALAPPDATA"]) / "Temp")
        if os.environ.get("SystemRoot"):
            candidates.append(Path(os.environ["SystemRoot"]) / "Temp")
    else:
        candidates += [Path("/tmp"), Path("/var/tmp")]
    for parent in dict.fromkeys(candidates):
        parent = parent.resolve()
        if parent.is_relative_to(source_root):
            continue
        try:
            return tempfile.TemporaryDirectory(prefix="llm-wiki-helper-", dir=parent)
        except OSError:
            continue
    raise OSError("no writable helper build directory outside target source")


def _build(language: str, stage: Path, profile: _Profile, cwd: Path) -> dict:
    source = stage / "source"
    source.mkdir()
    for name, path in helpers.helper_source_files(language):
        destination = source / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    temporary = stage / "temporary"
    temporary.mkdir()
    env = dict(profile.environment, TMPDIR=str(temporary), TEMP=str(temporary), TMP=str(temporary))
    artifact = stage / "artifact"
    artifact.mkdir()
    if language == "typescript":
        for name in helpers._TS_FILES:
            shutil.copyfile(source / name, artifact / name)
        _run([profile.executables["npm"], "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
             cwd=artifact, env=env, timeout=120)
        path = artifact / "node_modules/ts-morph"
        fingerprint = helpers.ts_identity.dependency_fingerprint(artifact / "node_modules")
    else:
        path = artifact / helpers._binary_name("llm-wiki-" + language + "-extractor")
        if language == "go":
            _run([profile.executables["go"], "build", "-mod=readonly", "-o", str(path), "."],
                 cwd=source, env=env, timeout=120)
        elif language == "rust":
            target_dir = stage / "target"
            _run([profile.executables["cargo"], "build", "--locked", "--release",
                  "--manifest-path", str(source / "Cargo.toml"), "--target", profile.identity["target"],
                  "--target-dir", str(target_dir)], cwd=cwd, env=env, timeout=180)
            built = target_dir / profile.identity["target"] / "release" / path.name
            shutil.copyfile(built, path)
            shutil.copymode(built, path)
        else:
            build = stage / "ghc-build"
            build.mkdir()
            _run([profile.executables["ghc"], "-Wall", "-package-env", "-", "-package", "ghc",
                  "-outputdir", str(build), "-i" + str(source), "-o", str(path), str(source / "Main.hs")],
                 cwd=cwd, env=env, timeout=180)
        _native_binary(path)
        fingerprint = _native_fingerprint(path)
    if _executable_identity(profile.executables) != profile.identity["executables"]:
        raise ValueError("toolchain changed while preparing helper")
    return {"version": helpers.TYPESCRIPT_HELPER_MANIFEST_VERSION if language == "typescript" else helpers.HELPER_MANIFEST_VERSION,
            "language": language, "platform": helpers.platform_id(),
            "source_fingerprint": helpers.helper_source_fingerprint(language),
            "artifact_fingerprint": fingerprint, "toolchain": profile.identity["toolchain"],
            "preparation_profile": profile.identity,
            **({"artifact_scope": helpers.ts_identity.ARTIFACT_SCOPE} if language == "typescript" else {})}


def _artifact_path(language: str, root: Path) -> Path:
    return (root / "node_modules/ts-morph" if language == "typescript"
            else root / helpers._binary_name("llm-wiki-" + language + "-extractor"))


def _copy_artifact(language: str, source: Path, destination: Path) -> None:
    """Copy only verified execution inputs to the cache-local publish stage."""
    destination.mkdir()
    if language == "typescript":
        for name in helpers._TS_FILES:
            shutil.copy2(source / name, destination / name)
        shutil.copytree(source / "node_modules", destination / "node_modules")
    else:
        shutil.copy2(_artifact_path(language, source), _artifact_path(language, destination))


def ensure_helper(language: str, src_dir: str | Path = ".", cache_dir: str | None = None,
                  *, progress: Callable[[str], None] | None = None,
                  wait_seconds: float = LOCK_WAIT_SECONDS) -> PreparedHelperHandle:
    """Prepare one selected helper once, publishing only fully validated data."""
    if language not in helpers.SUPPORTED_HELPERS:
        raise ValueError("Unsupported helper language: " + language)
    if type(wait_seconds) not in (int, float) or not 0 <= wait_seconds <= 600:
        raise ValueError("helper lock wait must be between 0 and 600 seconds")
    source_root = Path(src_dir).resolve()
    root = None
    try:
        root = _safe(preparation_cache_root(src_dir, cache_dir))
        current = lookup_helper(language, src_dir, cache_dir)
        # A valid installed helper remains useful without its compiler/package
        # manager. If available, an active profile selects its own immutable key.
        with _sandbox(source_root) as directory:
            cwd = Path(directory)
            try:
                profile = _profile(language, root, cwd)
            except (HelperPreparationError, OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                if current is not None and language != "typescript":
                    return current
                if current is not None and isinstance(error, HelperPreparationError) and error.runtime_executables:
                    return _with_runtime(current, error.runtime_executables)
                raise
            key = _profile_key(language, profile.identity)
            if current is not None and (current.key == key or (
                current.receipt.get("toolchain") == profile.identity["toolchain"]
                and not (current.root / RECEIPT).exists()
            )):
                return _with_runtime(current, profile.executables)
            root.mkdir(parents=True, exist_ok=True, mode=0o700)
            _safe(root)
            locks = root / ".locks"
            _safe(locks)
            locks.mkdir(exist_ok=True)
            _safe(locks)
            destination = root / language / key
            _safe(destination.parent)
            destination.parent.mkdir(exist_ok=True)
            _safe(destination)
            with _lock(locks / (language + "-" + key + ".lock"), wait_seconds):
                ready = _slot_handle(root, language, destination)
                if ready is not None:
                    return _with_runtime(ready, profile.executables)
                if progress is not None:
                    progress(f"Preparing {language} helper (first use or changed profile)…")
                # Package managers inspect ancestor workspace/configuration
                # even when given our own package.json. An explicit cache may
                # live inside the target project, so all builds stay in the
                # already verified external sandbox. The cache stage is only
                # populated after a successful, verified build.
                build_stage = cwd / "build"
                build_stage.mkdir()
                manifest = _build(language, build_stage, profile, cwd)
                built = build_stage / "artifact"
                manifest.update(key=key, root=str(built), path=str(_artifact_path(language, built)))
                _validate_artifact(language, cwd, built, manifest)
                staging = root / (".prepare-" + language + "-" + uuid.uuid4().hex)
                staging.mkdir(mode=0o700)
                try:
                    artifact = staging / "artifact"
                    _copy_artifact(language, built, artifact)
                    manifest.update(root=str(artifact), path=str(_artifact_path(language, artifact)))
                    _validate_artifact(language, root, artifact, manifest)
                    manifest.update(root=str(destination), path=str(_artifact_path(language, destination)))
                    if language == "typescript":
                        manifest.update(node_executable=profile.executables["node"],
                                        npm_executable=profile.executables["npm"])
                    write_json_atomic(artifact / RECEIPT, {"schema_version": SCHEMA, "key": key,
                                      "profile": profile.identity, "manifest": manifest})
                    _safe(destination)
                    if destination.exists():
                        _safe(destination)
                        os.rename(destination, destination.with_name(".rejected-" + key + "-" + uuid.uuid4().hex))
                    os.rename(artifact, destination)
                    ready = _slot_handle(root, language, destination)
                    if ready is None:
                        raise HelperPreparationError(language, "published helper failed receipt verification")
                    return _with_runtime(ready, profile.executables)
                finally:
                    shutil.rmtree(staging)
    except HelperPreparationError as error:
        if error.cache_root is None:
            error.cache_root = root
        raise
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        raise HelperPreparationError(language, str(error), root) from error
