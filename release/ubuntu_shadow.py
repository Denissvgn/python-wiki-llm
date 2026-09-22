"""One-runner shadow comparison with independent sources and virtual environments."""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import venv
from typing import Any

_spec = importlib.util.spec_from_file_location(
    "_shadow_suites", Path(__file__).with_name("ubuntu_suites.py")
)
assert _spec is not None and _spec.loader is not None
suites = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(suites)
q = suites.q

GROUPS = {
    "legacy-slow": ("slow", "determinism"),
    "legacy-security": ("security-ubuntu-24.04",),
    "legacy-product": ("product-ubuntu-24.04",),
    "union": (),
}


def lane_environment(directory: Path, temporary: Path) -> dict[str, str]:
    environment = os.environ.copy()
    # Preserve the original OS temporary-root semantics. Relocating pytest's
    # temp files under an arbitrary checkout/work root changes path-sensitive
    # contracts (including host-path redaction). Each lane still gets its own
    # private directory, independently of source/cache placement.
    for name, target in {
        "TMPDIR": temporary,
        "TEMP": temporary,
        "TMP": temporary,
        "XDG_CACHE_HOME": directory / "cache",
        "PIP_CACHE_DIR": directory / "cache/pip",
        "LLM_WIKI_CACHE_DIR": directory / "cache/llm-wiki",
    }.items():
        target.mkdir(parents=True, exist_ok=True)
        environment[name] = str(target)
    # Keep the runner's interpreter/install state out of each fresh process.
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "PYTEST_ADDOPTS",
        "PIP_CONSTRAINT",
        "PIP_BUILD_CONSTRAINT",
        "PIP_REQUIREMENT",
        "PIP_TARGET",
        "PIP_PREFIX",
    ):
        environment.pop(name, None)
    return environment


def invoke(
    command: list[str],
    directory: Path,
    environment: dict[str, str],
    log: Path,
    timeout: int = 900,
) -> dict[str, Any]:
    started = time.monotonic()
    result: dict[str, Any] = {"exit_code": None, "seconds": None, "error": None}
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("wb") as stream:
        try:
            with subprocess.Popen(
                command,
                cwd=directory,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=os.name == "posix",
            ) as process:
                try:
                    result["exit_code"] = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # A timed-out coordinator child may own pytest grandchildren.
                    # Reap the entire owned process group before starting a lane.
                    if os.name == "posix":
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    else:
                        process.kill()
                    process.wait(timeout=10)
                    result.update(exit_code=124, error=f"timed out after {timeout}s")
        except OSError as exc:
            result.update(exit_code=127, error=str(exc))
    result["seconds"] = time.monotonic() - started
    return result


def prepare(
    args: argparse.Namespace,
    name: str,
    constraints: Path | None,
    control: dict[str, Any],
) -> tuple[Path, Path, dict[str, str], float]:
    started = time.time()
    directory = args.work / name
    directory.mkdir()
    temporary = args.temporary_root / name
    environment = lane_environment(directory, temporary)
    candidate = directory / "candidate"
    q.extract_source(
        argparse.Namespace(
            archive=args.archive,
            sha256=control["identity"]["source"]["archive_sha256"],
            destination=candidate,
        )
    )
    venv_path = directory / ".venv"
    venv.EnvBuilder(with_pip=True).create(venv_path)
    interpreter = venv_path / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    environment["PATH"] = (
        str(interpreter.parent) + os.pathsep + environment.get("PATH", "")
    )
    command = [str(interpreter), "-m", "pip", "install", "--no-cache-dir"]
    if constraints is not None:
        command += ["--constraint", str(constraints), "--requirement", str(constraints)]
    command += [str(candidate) + "[dev]"]
    install = invoke(
        command,
        directory,
        environment,
        args.output / "diagnostics" / f"{name}-install.log",
    )
    control["preparations"][name] = {
        "source": str(candidate),
        "venv": str(venv_path),
        "temporary": str(temporary),
        "install": install,
    }
    q.write_json(args.output / "diagnostics/orchestration.json", control)
    suites.require(install["exit_code"] == 0, f"{name} dependency installation failed")
    return candidate, interpreter, environment, started


def constraints_text(environment: dict[str, Any]) -> str:
    suites.validate_environment(environment)
    packages = environment["packages"]
    for name, version in packages.items():
        suites.require(
            re.fullmatch(r"[a-z0-9][a-z0-9.-]*", name) is not None
            and re.fullmatch(r"[A-Za-z0-9.!+_-]+", version) is not None,
            "unsafe resolved dependency pin",
        )
    return "".join(
        f"{name}=={version}\n"
        for name, version in sorted(packages.items())
        if name != "agent-wiki-cli"
    )


def _run(args: argparse.Namespace) -> int:
    args.work, args.output = args.work.resolve(), args.output.resolve()
    suites.require(
        not args.work.exists() and not args.output.exists(),
        "shadow work and evidence directories must be new",
    )
    suites.require(
        args.work != args.output
        and args.work not in args.output.parents
        and args.output not in args.work.parents,
        "shadow work and evidence directories must be separate",
    )
    args.work.mkdir(parents=True)
    args.output.mkdir(parents=True)
    diagnostic = suites.comparison_diagnostic("prepare")
    comparison = args.output / "diagnostics/ubuntu-shadow-comparison.json"
    q.write_json(comparison, diagnostic)
    control: dict[str, Any] = {
        "schema_version": "agent-wiki-ubuntu-shadow-orchestration/v1",
        "qualifying": False,
        "complete": False,
        "passed": False,
        "preparations": {},
        "producers": {},
        "errors": [],
    }
    control_path = args.output / "diagnostics/orchestration.json"
    q.write_json(control_path, control)
    started = time.monotonic()
    try:
        inputs = suites.frozen_inputs(args)
        identity = inputs["identity"]
        control.update(
            identity=identity,
            harness_sha256=args.harness_sha256,
            registry_sha256=q.sha256_file(args.registry),
        )
        suites.require(
            q.sha256_file(args.harness) == args.harness_sha256,
            "harness digest mismatch",
        )
        suites.require(
            q.sha256_file(args.archive) == identity["source"]["archive_sha256"],
            "source archive digest mismatch",
        )
        # Capture one resolver result, then use that exact version set for four
        # independent installs. No environment or candidate build is shared.
        candidate, interpreter, environment, _ = prepare(
            args, "resolver", None, control
        )
        env_path = args.output / "diagnostics/resolved-environment.json"
        result = invoke(
            [
                str(interpreter),
                "-I",
                str(Path(__file__).with_name("ubuntu_suites.py")),
                "environment",
                "--root",
                str(candidate),
                "--output",
                str(env_path),
            ],
            candidate.parent,
            environment,
            args.output / "diagnostics/resolver-environment.log",
        )
        suites.require(
            result["exit_code"] == 0,
            "dependency resolution did not satisfy the Ubuntu profile",
        )
        resolved = q.load_json(env_path)
        constraints = args.output / "diagnostics/constraints.txt"
        constraints.write_text(constraints_text(resolved), encoding="utf-8")
        control["constraints_sha256"] = q.sha256_file(constraints)
        control["environment"] = resolved
        control["resolution_seconds"] = time.monotonic() - started
        for name, lanes in GROUPS.items():
            control["producers"][name] = {"result": "running", "error": None}
            diagnostic["stage"] = "execution"
            diagnostic["producer_results"] = {
                label: control["producers"].get(label, {}).get("result", "not-run")
                for label in GROUPS
            }
            q.write_json(comparison, diagnostic)
            q.write_json(control_path, control)
            try:
                candidate, interpreter, environment, setup_started = prepare(
                    args, name, constraints, control
                )
                command = [
                    str(interpreter),
                    "-I",
                    str(Path(__file__).with_name("ubuntu_suites.py")),
                    "run",
                    "--mode",
                    "union" if name == "union" else "legacy",
                    "--root",
                    str(candidate),
                    "--output",
                    str(args.output / name),
                    "--identity",
                    str(args.identity),
                    "--harness",
                    str(args.harness),
                    "--harness-sha256",
                    args.harness_sha256,
                    "--registry",
                    str(args.registry),
                    "--setup-started",
                    str(setup_started),
                ]
                for lane in lanes:
                    command += ["--lane", lane]
                result = invoke(
                    command,
                    candidate.parent,
                    environment,
                    args.output / "diagnostics" / f"{name}-runner.log",
                    timeout=2 * suites.TIMEOUT + 120,
                )
                suites.require(
                    result["exit_code"] == 0, f"{name} execution failed: {result}"
                )
                execution = q.load_json(args.output / name / "execution.json")
                suites.require(
                    execution["environment"] == resolved,
                    f"{name} differs from the resolved environment",
                )
                control["producers"][name] = {
                    "result": "success",
                    "execution": result,
                    "execution_sha256": q.sha256_file(
                        args.output / name / "execution.json"
                    ),
                }
            except (
                q.QualificationError,
                OSError,
                ValueError,
                KeyError,
                TypeError,
                tarfile.TarError,
                subprocess.SubprocessError,
            ) as exc:
                control["producers"][name] = {"result": "failure", "error": str(exc)}
            q.write_json(control_path, control)
        suites.compare(
            argparse.Namespace(
                identity=args.identity,
                harness_sha256=args.harness_sha256,
                registry=args.registry,
                union=args.output / "union",
                legacy=[args.output / name for name in GROUPS if name != "union"],
                allowlist=args.work / "resolver/candidate/release/skip-allowlist.json",
                output=comparison,
                producer_result=[
                    f"{name}={control['producers'][name]['result']}" for name in GROUPS
                ],
            )
        )
        control.update(complete=True, passed=True)
        return 0
    except (
        q.QualificationError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        tarfile.TarError,
        subprocess.SubprocessError,
    ) as exc:
        control["errors"].append(str(exc))
        report = q.load_json(comparison)
        if not report["errors"]:
            report["errors"].append({"type": type(exc).__name__, "message": str(exc)})
        report["producer_results"] = {
            name: control["producers"].get(name, {}).get("result", "not-run")
            for name in GROUPS
        }
        q.write_json(comparison, report)
        print(f"Ubuntu shadow refused: {exc}", file=sys.stderr)
        return 1
    finally:
        control["elapsed_seconds"] = time.monotonic() - started
        q.write_json(control_path, control)


def run(args: argparse.Namespace) -> int:
    # This root follows the caller's normal OS temp policy, not --work. Cleanup
    # occurs only after all subprocesses have exited and reports were retained.
    with tempfile.TemporaryDirectory(prefix="agent-wiki-shadow-") as temporary:
        args.temporary_root = Path(temporary).resolve()
        return _run(args)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "identity", "harness", "registry", "work", "output"):
        parser.add_argument(
            "--" + name, type=lambda value: Path(value).resolve(), required=True
        )
    parser.add_argument("--harness-sha256", required=True)
    args = parser.parse_args()
    try:
        return run(args)
    except (
        q.QualificationError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        tarfile.TarError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"Ubuntu shadow refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
