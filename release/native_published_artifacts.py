"""Probe exact published archives with the existing native Windows consumers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time


class ProbeError(ValueError):
    pass


def is_native_windows() -> bool:
    return os.name == "nt" and sys.platform == "win32"


def artifact_names(version: str, *, engine: bool = False) -> dict[str, str]:
    """Release file names; releases since the engine split also ship the engine pair."""
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ProbeError("version must be a stable X.Y.Z release")
    names = {
        "wheel": f"agent_wiki_cli-{version}-py3-none-any.whl",
        "sdist": f"agent_wiki_cli-{version}.tar.gz",
    }
    if engine:
        names["engine-wheel"] = f"llm_wiki_engine-{version}-py3-none-any.whl"
        names["engine-sdist"] = f"llm_wiki_engine-{version}.tar.gz"
    return names


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
        raise ProbeError("artifact directory must contain only the expected archives")
    for kind, name in names.items():
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ProbeError(f"{kind} archive must be a regular file")
        if hashlib.sha256(path.read_bytes()).hexdigest() != hashes[kind]:
            raise ProbeError(f"published {kind} archive digest differs")


def verify_comparison(output: Path, hashes: dict[str, str], version: str) -> None:
    engine = "engine-wheel" in hashes
    for kind in ("wheel", "sdist"):
        value = json.loads((output / f"{kind}.json").read_text(encoding="utf-8"))
        if value["artifact"]["sha256"] != hashes[kind]:
            raise ProbeError(f"{kind} smoke result belongs to another archive")
        if engine and value.get("engine_artifact", {}).get("sha256") != hashes["engine-" + kind]:
            raise ProbeError(f"{kind} smoke ran with another engine archive")
    value = json.loads((output / "comparison.json").read_text(encoding="utf-8"))
    if (
        value.get("equal") is not True
        or value.get("version") != version
        or value.get("wheel_sha256") != hashes["wheel"]
        or value.get("sdist_sha256") != hashes["sdist"]
        or (engine and value.get("engine_wheel_sha256") != hashes["engine-wheel"])
        or (engine and value.get("engine_sdist_sha256") != hashes["engine-sdist"])
    ):
        raise ProbeError("complete native wheel/sdist comparison did not agree")


def diagnose_failed_harness(args, record, run, save, environment) -> None:
    """Attribute the original failure without substituting a passing fallback."""
    attempt = record["commands"][-1]
    if attempt.get("status") == "timeout" or attempt.get("seconds", 1800) > 1500:
        record["diagnostic"] = {"status": "unavailable", "release_acceptance": False,
                                "reason": "insufficient remaining native owner budget"}
        save()
        return
    commands_path = args.output / "commands.json"
    commands = json.loads(commands_path.read_text(encoding="utf-8")) if commands_path.exists() else []
    kind = "sdist" if commands and commands[-1].get("label") == "sdist-smoke" else "wheel"
    python = args.work / f"{kind}-mcp/.venv/Scripts/python.exe"
    if not python.is_file():
        record["diagnostic"] = {"status": "unavailable", "release_acceptance": False,
                                "reason": "original installed MCP consumer unavailable"}
        save()
        return
    record["diagnostic"] = {"status": "running", "release_acceptance": False, "artifact": kind}
    save()
    digest = args.wheel_sha256 if kind == "wheel" else args.sdist_sha256
    try:
        run("native-session-diagnostic", [python, "-I",
            Path(__file__).with_name("native_session_diagnostics.py"),
            "--harness", args.harness_dir, "--harness-sha", args.harness_sha,
            "--work", args.work / "diagnostic-caller",
            "--output", args.output / "native-session-diagnostic", "--version", args.version,
            "--archive-sha256", digest], timeout=300,
            env={**environment, "PYTHONDONTWRITEBYTECODE": "1"})
    except (ProbeError, OSError, ValueError) as error:
        record["diagnostic"].update(status="failed", reason=str(error))
    else:
        record["diagnostic"]["status"] = "complete"
    save()


def prepare_git_adapter(harness: Path, output: Path, environment, run) -> tuple[dict, dict]:
    """Prepare an explicit external helper; never patch installed Python code."""
    real = shutil.which("git", path=environment.get("PATH"))
    if real is None:
        raise ProbeError("original Git executable is unavailable")
    compiler = Path(environment.get("SystemRoot", r"C:\Windows")) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    if not compiler.is_file():
        raise ProbeError("native .NET Framework compiler is unavailable for explicit Git adapter")
    folder = output / "git-adapter"
    folder.mkdir()
    executable = folder / "git.exe"
    source = Path(__file__).with_name("git_stdin_adapter.cs")
    run("git-adapter-build", [compiler, "/nologo", "/target:exe", "/platform:anycpu", "/optimize+",
                             "/out:" + str(executable), source], env=environment)
    adapted = {**environment, "AGENT_WIKI_REAL_GIT": str(Path(real).resolve()),
               "PATH": str(folder) + os.pathsep + environment.get("PATH", "")}
    assertions = []
    for arguments in (["--version"], ["-C", str(harness), "rev-parse", "--absolute-git-dir", "--git-path", "index"],
                      ["-C", str(harness), "rev-parse", "--verify", "HEAD"]):
        original = run("git-original-" + str(len(assertions)), [real, *arguments], env=environment)
        current = run("git-adapted-" + str(len(assertions)), [executable, *arguments], env=adapted)
        if original != current:
            raise ProbeError("external Git adapter changed original Git output")
        assertions.append({"arguments": arguments, "stdout_sha256": hashlib.sha256(original).hexdigest()})
    contracts = json.loads(run("git-adapter-contracts", [sys.executable, "-I",
        Path(__file__).with_name("git_adapter_contracts.py"), executable, real, output], env=adapted))
    if contracts.get("status") != "pass" or contracts.get("native") != "win32":
        raise ProbeError("external Git adapter native contracts did not pass")
    receipt = {"kind": "external-git-stdin-isolation/v1", "provider_modified": False,
        "qualification": "Explicit external Git stdin adapter selected; archive acceptance still requires the complete gate. The plain 2.5.0 remains affected.",
        "original_executable": str(real), "original_sha256": hashlib.sha256(Path(real).read_bytes()).hexdigest(),
        "adapter_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "parity": assertions,
        "contracts": contracts,
        "policy": "Only the three context-session identity probes receive EOF stdin; other commands retain owned stdin/stdout/stderr/arguments/exit codes."}
    (output / "git-adapter.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return adapted, receipt


ORIGIN = """
from importlib.metadata import distribution
from pathlib import Path
from llm_wiki_cli import api
import json, sys
assert Path(api.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
d = distribution('agent-wiki-cli')
try:
    e = distribution('llm-wiki-engine')
except Exception:
    engine = None
else:
    import llm_wiki_engine
    assert Path(llm_wiki_engine.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    engine = {'version': e.version, 'direct_url': json.loads(e.read_text('direct_url.json'))}
print(json.dumps({'version': d.version, 'module': api.__file__, 'prefix': sys.prefix,
                  'direct_url': json.loads(d.read_text('direct_url.json')), 'engine': engine}))
"""


def archive_digest(direct_url: dict) -> str | None:
    archive = direct_url["archive_info"]
    digest = archive.get("hashes", {}).get("sha256")
    if digest is None:
        digest = archive.get("hash", "").removeprefix("sha256=")
    return digest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--harness-dir", type=Path, required=True)
    parser.add_argument("--harness-sha", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--sdist-sha256", required=True)
    parser.add_argument("--engine-wheel-sha256")
    parser.add_argument("--engine-sdist-sha256")
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--git-stdin-adapter", action="store_true")
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
            **({"engine-wheel": args.engine_wheel_sha256,
                "engine-sdist": args.engine_sdist_sha256}
               if args.engine_wheel_sha256 or args.engine_sdist_sha256 else {}),
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
        engine = bool(args.engine_wheel_sha256 or args.engine_sdist_sha256)
        names = artifact_names(args.version, engine=engine)
        require_digest(args.harness_sha, 40, "harness SHA")
        hashes = {"wheel": args.wheel_sha256, "sdist": args.sdist_sha256}
        if engine:
            hashes.update({"engine-wheel": args.engine_wheel_sha256 or "",
                           "engine-sdist": args.engine_sdist_sha256 or ""})
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
                         *(word for name in names.values() for word in ("--pattern", name))])
        verify_archives(args.artifacts, names, hashes)
        consumer_environment = dict(environment)
        for key in ("GH_TOKEN", "GITHUB_TOKEN"):
            consumer_environment.pop(key, None)
        if args.git_stdin_adapter:
            consumer_environment, receipt = prepare_git_adapter(harness, args.output, consumer_environment, run)
            record["runtime_adapter"] = receipt
            save()
        try:
            run("installed-artifact-harness", [sys.executable, "-I",
                harness / "tests/run_provider_artifact_checks.py",
                "--artifacts", args.artifacts, "--work", args.work,
                "--output", args.output, "--version", args.version],
                timeout=1800, env=consumer_environment)
        except ProbeError:
            # Profiling occurs only after the immutable acceptance owner fails.
            # It cannot warm that attempt, replace its result or extend its limit.
            try:
                diagnose_failed_harness(args, record, run, save, consumer_environment)
            except Exception as error:
                # Optional attribution failures must preserve the primary gate
                # failure, including malformed receipts or diagnostic defects.
                record["diagnostic"] = {"status": "failed", "release_acceptance": False,
                                        "reason": str(error)}
            raise
        verify_archives(args.artifacts, names, hashes)
        verify_comparison(args.output, hashes, args.version)
        origins = {}
        for kind in ("wheel", "sdist"):
            for extra in ("base", "mcp"):
                python = args.work / f"{kind}-{extra}/.venv/Scripts/python.exe"
                origin = json.loads(run(f"{kind}-{extra}-origin",
                    [python, "-X", "utf8", "-I", "-c", ORIGIN],
                    env=consumer_environment))
                digest = archive_digest(origin["direct_url"])
                if origin["version"] != args.version or digest != hashes[kind]:
                    raise ProbeError("consumer origin differs from the published archive")
                if engine and (
                    origin["engine"] is None
                    or origin["engine"]["version"] != args.version
                    or archive_digest(origin["engine"]["direct_url"]) != hashes["engine-" + kind]
                ):
                    raise ProbeError("consumer engine differs from the published engine archive")
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
