"""Probe exact published archives with the existing native Windows consumers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time


class ProbeError(ValueError):
    pass


def is_native_windows() -> bool:
    return os.name == "nt" and sys.platform == "win32"


def artifact_names(version: str) -> dict[str, str]:
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ProbeError("version must be a stable X.Y.Z release")
    return {
        "wheel": f"agent_wiki_cli-{version}-py3-none-any.whl",
        "sdist": f"agent_wiki_cli-{version}.tar.gz",
    }


def require_digest(value: str, length: int, label: str) -> None:
    if not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
        raise ProbeError(f"{label} must be an exact lowercase {length}-digit digest")


def require_separate_roots(harness: Path, tools: Path, roots: list[Path]) -> None:
    for path in roots:
        if any(path == root or root in path.parents or path in root.parents
               for root in (harness, tools)):
            raise ProbeError("consumer/evidence paths must be separate from source")
    if any(a == b or a in b.parents or b in a.parents
           for i, a in enumerate(roots) for b in roots[i + 1:]):
        raise ProbeError("artifact, consumer and evidence roots must be separate")


def verify_archives(directory: Path, names: dict[str, str], hashes: dict[str, str]):
    expected_files = set(names.values())
    if {p.name for p in directory.iterdir()} != expected_files:
        raise ProbeError("artifact directory must contain only the two expected archives")
    for kind, name in names.items():
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ProbeError(f"{kind} archive must be a regular file")
        if hashlib.sha256(path.read_bytes()).hexdigest() != hashes[kind]:
            raise ProbeError(f"published {kind} archive digest differs")


def verify_comparison(output: Path, hashes: dict[str, str], version: str) -> None:
    for kind in ("wheel", "sdist"):
        value = json.loads((output / f"{kind}.json").read_text(encoding="utf-8"))
        if value["artifact"]["sha256"] != hashes[kind]:
            raise ProbeError(f"{kind} smoke result belongs to another archive")
    value = json.loads((output / "comparison.json").read_text(encoding="utf-8"))
    if (
        value.get("equal") is not True
        or value.get("version") != version
        or value.get("wheel_sha256") != hashes["wheel"]
        or value.get("sdist_sha256") != hashes["sdist"]
    ):
        raise ProbeError("complete native wheel/sdist comparison did not agree")


ORIGIN = """
from importlib.metadata import distribution
from pathlib import Path
from llm_wiki_cli import api
import json, sys
assert Path(api.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
d = distribution('agent-wiki-cli')
print(json.dumps({'version': d.version, 'module': api.__file__, 'prefix': sys.prefix,
                  'direct_url': json.loads(d.read_text('direct_url.json'))}))
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--harness-dir", type=Path, required=True)
    parser.add_argument("--harness-sha", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--sdist-sha256", required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    harness = args.harness_dir.resolve()
    tools = Path(__file__).resolve().parents[1]
    try:
        require_separate_roots(
            harness, tools,
            [args.artifacts.resolve(), args.work.resolve(), args.output.resolve()],
        )
    except ProbeError as error:
        # Even a failure receipt must not write into either protected source root.
        print(str(error), file=sys.stderr)
        return 2
    args.output.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": "agent-wiki-native-published-probe/v1",
        "status": "running",
        "repository": args.repository,
        "version": args.version,
        "harness_sha": args.harness_sha,
        "controller_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "expected_archives": {
            "wheel": args.wheel_sha256,
            "sdist": args.sdist_sha256,
        },
        "native": {
            "os_name": os.name,
            "sys_platform": sys.platform,
            "platform": platform.platform() if is_native_windows() else sys.platform,
            "machine": platform.machine() if is_native_windows() else "not-evaluated",
            "python": sys.version,
            "executable": sys.executable,
        },
        "commands": [],
    }
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")

    def save():
        (args.output / "probe.json").write_text(
            json.dumps(record, indent=2) + "\n", encoding="utf-8"
        )

    def run(label, command, *, timeout=180, env=None) -> bytes:
        started = time.monotonic()
        try:
            result = subprocess.run(
                [str(word) for word in command],
                env=environment if env is None else env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            record["commands"].append(
                {"label": label, "status": "timeout", "timeout_seconds": timeout}
            )
            save()
            # Keep partial stdout/stderr without discarding an incomplete attempt.
            (args.output / f"{label}.stdout").write_bytes(error.stdout or b"")
            (args.output / f"{label}.stderr").write_bytes(error.stderr or b"")
            raise ProbeError(f"{label} exceeded {timeout}s") from error
        (args.output / f"{label}.stdout").write_bytes(result.stdout)
        (args.output / f"{label}.stderr").write_bytes(result.stderr)
        record["commands"].append(
            {"label": label, "exit_code": result.returncode,
             "seconds": round(time.monotonic() - started, 6)}
        )
        save()
        if result.returncode:
            raise ProbeError(f"{label} failed; see retained command evidence")
        return result.stdout

    try:
        names = artifact_names(args.version)
        require_digest(args.harness_sha, 40, "harness SHA")
        hashes = {"wheel": args.wheel_sha256, "sdist": args.sdist_sha256}
        for kind, value in hashes.items():
            require_digest(value, 64, kind)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
            raise ProbeError("repository must be an owner/name coordinate")
        if not is_native_windows():
            record["status"] = "incomplete"
            raise ProbeError("an actual native Windows interpreter is required")
        if sys.prefix == sys.base_prefix:
            raise ProbeError("the controller must use its project virtual environment")
        if args.artifacts.exists() or args.work.exists():
            raise ProbeError("archive and consumer roots must be fresh")
        head = run("harness-head", ["git", "-C", harness, "rev-parse", "HEAD"])
        if head.decode().strip() != args.harness_sha:
            raise ProbeError("native harness checkout differs from the pinned SHA")
        if run("harness-clean", ["git", "-C", harness, "status", "--porcelain"]).strip():
            raise ProbeError("native harness checkout must be clean")
        record["controller_source"] = run(
            "controller-head", ["git", "-C", tools, "rev-parse", "HEAD"]
        ).decode().strip()
        args.artifacts.mkdir(parents=True)
        run("download", ["gh", "release", "download", f"v{args.version}",
                         "--repo", args.repository, "--dir", args.artifacts,
                         "--pattern", names["wheel"], "--pattern", names["sdist"]])
        verify_archives(args.artifacts, names, hashes)
        consumer_environment = dict(environment)
        for key in ("GH_TOKEN", "GITHUB_TOKEN"):
            consumer_environment.pop(key, None)
        run("installed-artifact-harness", [sys.executable, "-I",
            harness / "tests/run_provider_artifact_checks.py",
            "--artifacts", args.artifacts, "--work", args.work,
            "--output", args.output, "--version", args.version],
            timeout=1800, env=consumer_environment)
        verify_archives(args.artifacts, names, hashes)
        verify_comparison(args.output, hashes, args.version)
        origins = {}
        for kind in ("wheel", "sdist"):
            for extra in ("base", "mcp"):
                python = args.work / f"{kind}-{extra}/.venv/Scripts/python.exe"
                origin = json.loads(run(f"{kind}-{extra}-origin",
                    [python, "-X", "utf8", "-I", "-c", ORIGIN],
                    env=consumer_environment))
                archive = origin["direct_url"]["archive_info"]
                digest = archive.get("hashes", {}).get("sha256")
                if digest is None:
                    digest = archive.get("hash", "").removeprefix("sha256=")
                if origin["version"] != args.version or digest != hashes[kind]:
                    raise ProbeError("consumer origin differs from the published archive")
                origins[f"{kind}-{extra}"] = origin
                if extra == "base":
                    census = json.loads(run(f"{kind}-analysis-inputs",
                        [python, "-I", "-m", "llm_wiki_cli.cli", "doctor",
                         "--analysis-inputs", "--format", "json"],
                        env=consumer_environment))
                    if census.get("status") != "ready":
                        raise ProbeError("installed analysis-input census is not ready")
        record.update(status="pass", origins=origins, comparison="equal")
        save()
        return 0
    except (ProbeError, OSError, KeyError, ValueError) as error:
        if record["status"] != "incomplete":
            record["status"] = "fail"
        record["reason"] = str(error)
        save()
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
