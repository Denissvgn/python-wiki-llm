"""Verify third-party wheel downloads and install a locked fresh tool environment."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import itertools
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import sysconfig
import tempfile
import time

SCHEMA = "agent-wiki-dependency-downloads/v1"
MAX_WHEEL = 128 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
PROFILES = {"build", "validation"}


class DependencyError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise DependencyError(message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
    )


def read_json(path):
    require(
        not path.is_symlink() and path.is_file() and path.stat().st_size <= 1024 * 1024,
        "invalid cache metadata",
    )

    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate cache metadata key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise DependencyError("nonfinite cache metadata: " + value)

    return json.loads(
        path.read_bytes(), object_pairs_hook=unique, parse_constant=invalid_constant
    )


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def read_lock(path):
    require(
        not path.is_symlink() and path.is_file() and path.stat().st_size < 1024 * 1024,
        "invalid dependency lock",
    )
    records = {}
    pending = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pending += " " + line.removesuffix("\\").strip()
        if line.endswith("\\"):
            continue
        words = pending.split()
        match = re.fullmatch(
            r"([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9.!+_-]*)", words[0]
        )
        require(match is not None, "only exact third-party pins are accepted")
        assert match is not None
        name, version = normalized(match[1]), match[2]
        require(
            name not in records and name != "agent-wiki-cli",
            "duplicate or candidate requirement in download lock",
        )
        require(
            len(words) > 1
            and all(
                re.fullmatch(r"--hash=sha256:[0-9a-f]{64}", word) for word in words[1:]
            ),
            "every dependency needs trusted SHA-256 hashes",
        )
        records[name] = {
            "version": version,
            "hashes": sorted({word.split(":", 1)[1] for word in words[1:]}),
        }
        pending = ""
    require(
        not pending and 0 < len(records) <= 100,
        "incomplete or excessive dependency lock",
    )
    return records


def environment_identity():
    system = platform.system()
    if system == "Linux":
        release = platform.freedesktop_os_release()
        os_version = {name: release.get(name, "") for name in ("ID", "VERSION_ID")}
    else:
        os_version = platform.mac_ver()[0] if system == "Darwin" else platform.version()
    return {
        "os": system,
        "os_version": os_version,
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "abi": sysconfig.get_config_var("SOABI"),
        "platform": sysconfig.get_platform(),
        "bootstrap_pip": importlib.metadata.version("pip"),
    }


def identity(lock, profile, namespace="release"):
    require(
        profile in PROFILES and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", namespace),
        "invalid dependency cache profile/namespace",
    )
    read_lock(lock)
    value = {
        "schema_version": SCHEMA,
        "profile": profile,
        "namespace": namespace,
        "lock_sha256": sha256(lock),
        "policy_sha256": sha256(Path(__file__)),
        "environment": environment_identity(),
    }
    value["key"] = (
        "agent-wiki-wheels-v1-" + hashlib.sha256(canonical(value)).hexdigest()
    )
    return value


def outputs(values):
    if destination := os.environ.get("GITHUB_OUTPUT"):
        with open(destination, "a", encoding="utf-8", newline="\n") as stream:
            for key, value in values.items():
                stream.write(f"{key}={value}\n")


def key_command(args):
    value = identity(args.lock, args.profile, args.namespace)
    write_json(args.output, value)
    outputs({"cache-key": value["key"]})
    return 0


def wheel_inventory(directory, lock):
    require(
        directory.is_dir() and not directory.is_symlink(),
        "wheel directory is absent or redirected",
    )
    children = list(itertools.islice(directory.iterdir(), len(lock) + 2))
    require(len(children) <= len(lock) + 1, "unexpected files in wheel directory")
    result, names, total = {}, set(), 0
    for path in children:
        if path.name == "manifest.json":
            require(
                not path.is_symlink() and path.is_file(), "redirected wheel manifest"
            )
            continue
        require(
            re.fullmatch(r"[A-Za-z0-9_.+!-]+\.whl", path.name) is not None,
            "cache contains a non-wheel or unsafe filename",
        )
        require(
            not path.is_symlink() and stat.S_ISREG(path.stat().st_mode),
            "cache contains a redirected or nonregular wheel",
        )
        pieces = path.name[:-4].split("-")
        require(len(pieces) in {5, 6}, "malformed wheel name")
        name, version = normalized(pieces[0]), pieces[1]
        require(
            name in lock and name not in names and version == lock[name]["version"],
            "unexpected or repeated wheel dependency",
        )
        size = path.stat().st_size
        require(0 < size <= MAX_WHEEL, "wheel exceeds byte bounds")
        total += size
        require(total <= MAX_TOTAL, "wheelhouse exceeds byte bounds")
        digest = sha256(path)
        require(
            digest in lock[name]["hashes"],
            "wheel digest differs from trusted lock: " + path.name,
        )
        result[path.name] = {"sha256": digest, "bytes": size}
        names.add(name)
    require(names == set(lock), "wheelhouse does not contain every locked dependency")
    return dict(sorted(result.items()))


def verify_cache(directory, expected, lock):
    require(
        directory.is_dir() and not directory.is_symlink(),
        "cache is absent or redirected",
    )
    manifest = read_json(directory / "manifest.json")
    require(
        isinstance(manifest, dict) and set(manifest) == {"identity", "files"},
        "invalid wheel manifest fields",
    )
    require(
        manifest["identity"] == expected,
        "stale or incompatible dependency cache identity",
    )
    actual = wheel_inventory(directory, lock)
    require(manifest["files"] == actual, "wheel cache membership or digest differs")
    return actual


def verify_command(args):
    expected = read_json(args.identity)
    current = identity(args.lock, args.profile, args.namespace)
    # Setup intentionally replaces bootstrap pip with the locked installer.
    # Every other compatibility/policy field must still match before saving.
    current["environment"]["bootstrap_pip"] = expected["environment"]["bootstrap_pip"]
    del current["key"]
    current["key"] = (
        "agent-wiki-wheels-v1-" + hashlib.sha256(canonical(current)).hexdigest()
    )
    require(expected == current, "dependency cache identity changed before saving")
    verify_cache(args.cache, expected, read_lock(args.lock))
    outputs({"cache-ready": "true"})
    return 0


def command_environment():
    result = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("PIP_") and key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    result.update(PIP_CONFIG_FILE=os.devnull, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    return result


def run(command, log):
    started = time.monotonic()
    with log.open("wb") as stream:
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            env=command_environment(),
            timeout=900,
        )
    require(
        result.returncode == 0,
        f"dependency command failed (exit {result.returncode}); see {log.name}",
    )
    return time.monotonic() - started


def pip_command(operation, lock, *, find_links=None, destination=None):
    command = [
        sys.executable,
        "-I",
        "-m",
        "pip",
        "--isolated",
        "--disable-pip-version-check",
        operation,
        "--no-cache-dir",
        "--only-binary=:all:",
        "--require-hashes",
        "-r",
        str(lock),
    ]
    if find_links is None:
        command += ["--index-url", "https://pypi.org/simple"]
    else:
        command += ["--no-index", "--find-links", str(find_links)]
    if destination is not None:
        command += ["--dest", str(destination)]
    if operation == "install":
        require(find_links is not None, "tool installation must be offline")
        command += ["--force-reinstall"]
    return command


def installed():
    result = {}
    for distribution in importlib.metadata.distributions():
        name = normalized(distribution.metadata["Name"])
        require(name not in result, "duplicate installed dependency")
        result[name] = distribution.version
    return dict(sorted(result.items()))


def copy_verified(source, target, expected, lock):
    before = verify_cache(source, expected, lock)
    target.mkdir()
    for name in before:
        shutil.copyfile(source / name, target / name, follow_symlinks=False)
    write_json(target / "manifest.json", {"identity": expected, "files": before})
    verify_cache(target, expected, lock)


def setup(args):
    lock_path = args.lock.resolve()
    lock = read_lock(lock_path)
    current = identity(lock_path, args.profile, args.namespace)
    require(read_json(args.identity) == current, "dependency setup identity changed")
    require(
        sys.prefix != sys.base_prefix and set(installed()) <= {"pip", "setuptools"},
        "dependency tools require a fresh isolated environment",
    )
    output = args.output.absolute()
    require(
        not output.exists() and not output.is_symlink(), "dependency output must be new"
    )
    cache = args.cache.absolute() if args.cache is not None else None
    if cache is not None:
        require(
            output != cache
            and output not in cache.parents
            and cache not in output.parents,
            "cache and private installation evidence must be separate",
        )
    output.mkdir(parents=True)
    wheels = output / "wheels"
    wheels.mkdir()
    record = {
        "schema_version": SCHEMA,
        "identity": current,
        "complete": False,
        "cache_state": "disabled" if cache is None else "miss",
        "cache_error": None,
        "files": {},
        "installed": {},
        "seconds": {},
        "cache_exported": False,
        "error": None,
    }
    started = time.monotonic()
    try:
        if cache is not None and args.cache_available:
            if cache.exists() or cache.is_symlink():
                try:
                    with tempfile.TemporaryDirectory(
                        prefix="dependency-snapshot-", dir=output
                    ) as temporary:
                        snapshot = Path(temporary) / "verified"
                        copy_verified(cache, snapshot, current, lock)
                        record["seconds"]["cache_resolution"] = run(
                            pip_command(
                                "download",
                                lock_path,
                                find_links=snapshot,
                                destination=wheels,
                            ),
                            output / "cache-resolution.log",
                        )
                    record["cache_state"] = "hit"
                except (
                    DependencyError,
                    OSError,
                    ValueError,
                    subprocess.SubprocessError,
                ) as exc:
                    record.update(cache_state="rejected", cache_error=str(exc))
                    shutil.rmtree(wheels)
                    wheels.mkdir()
        elif cache is not None:
            record["cache_state"] = "unavailable"
        if record["cache_state"] != "hit":
            record["seconds"]["download"] = run(
                pip_command("download", lock_path, destination=wheels),
                output / "download.log",
            )
        files = wheel_inventory(wheels, lock)
        write_json(wheels / "manifest.json", {"identity": current, "files": files})
        record["files"] = files
        record["seconds"]["install"] = run(
            pip_command("install", lock_path, find_links=wheels), output / "install.log"
        )
        record["seconds"]["pip_check"] = run(
            [sys.executable, "-I", "-m", "pip", "check"], output / "pip-check.log"
        )
        # Query in a new process: the installer has replaced its own pip files.
        raw = subprocess.check_output(
            [sys.executable, "-I", str(Path(__file__).resolve()), "inventory"],
            stdin=subprocess.DEVNULL,
            env=command_environment(),
            timeout=30,
        )
        record["installed"] = json.loads(raw)
        require(
            record["installed"] == {name: row["version"] for name, row in lock.items()},
            "installed tool environment differs from the complete lock",
        )
        verify_cache(wheels, current, lock)
        if cache is not None:
            # Only job-local restored downloads are replaced. Candidate artifacts,
            # environments and build outputs never enter this directory.
            try:
                if cache.is_symlink() or cache.is_file():
                    cache.unlink()
                elif cache.exists():
                    shutil.rmtree(cache)
                cache.parent.mkdir(parents=True, exist_ok=True)
                copy_verified(wheels, cache, current, lock)
                record["cache_exported"] = True
            except OSError as exc:
                record["cache_error"] = str(exc)
        record["complete"] = True
        outputs(
            {
                "cache-ready": str(record["cache_exported"]).lower(),
                "cache-state": record["cache_state"],
            }
        )
    except BaseException as exc:
        record["error"] = str(exc)
        raise
    finally:
        record["seconds"]["total"] = time.monotonic() - started
        write_json(output / "setup.json", record)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inventory = commands.add_parser("inventory")
    inventory.set_defaults(function=lambda args: print(json.dumps(installed())) or 0)
    for name, function in (
        ("key", key_command),
        ("setup", setup),
        ("verify-cache", verify_command),
    ):
        command = commands.add_parser(name)
        command.add_argument("--lock", type=Path, required=True)
        command.add_argument("--profile", choices=sorted(PROFILES), required=True)
        command.add_argument("--namespace", default="release")
        if name != "verify-cache":
            command.add_argument("--output", type=Path, required=True)
        if name == "setup":
            command.add_argument("--identity", type=Path, required=True)
            command.add_argument("--cache", type=Path)
            command.add_argument(
                "--cache-available", action=argparse.BooleanOptionalAction, default=True
            )
        elif name == "verify-cache":
            command.add_argument("--identity", type=Path, required=True)
            command.add_argument("--cache", type=Path, required=True)
        command.set_defaults(function=function)
    args = parser.parse_args()
    return args.function(args)


if __name__ == "__main__":
    raise SystemExit(main())
