"""Compare isolated builder dependencies and cache controls; never qualify a release."""

from __future__ import annotations

import argparse
import importlib.util
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import time


def sibling(name):
    spec = importlib.util.spec_from_file_location(
        "_dependency_probe_" + name, Path(__file__).with_name(name + ".py")
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


d = sibling("dependency_downloads")
q = sibling("qualification")
SCHEMA = "agent-wiki-dependency-comparison/v1"
FILES = (
    "candidate-source.tar",
    "dependency_setup_probe.py",
    "dependency_downloads.py",
    "qualification.py",
)
CASES = ("baseline", "cold", "warm", "stale", "corrupt", "unavailable")


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, stdin=subprocess.DEVNULL)


def freeze(args):
    q._require_sha(args.candidate, "dependency comparison candidate")
    root, output = args.root.resolve(), args.output.resolve()
    d.require(
        git(root, "rev-parse", "HEAD").decode().strip() == args.candidate,
        "comparison checkout differs",
    )
    d.require(
        not git(root, "status", "--porcelain=v1", "--untracked-files=all").strip(),
        "comparison source must be clean",
    )
    d.require(
        not output.exists() and root not in output.parents,
        "comparison inputs must be new and outside source",
    )
    output.mkdir(parents=True)
    for name in FILES[1:]:
        raw = git(root, "show", f"{args.candidate}:release/{name}")
        d.require(
            raw == Path(__file__).with_name(name).read_bytes(),
            "running comparison helper differs: " + name,
        )
        (output / name).write_bytes(raw)
    git(
        root,
        "archive",
        "--format=tar",
        "--output=" + str(output / FILES[0]),
        args.candidate,
    )
    record = {
        "schema_version": SCHEMA,
        "qualifying": False,
        "candidate_sha": args.candidate,
        "tree": git(root, "rev-parse", "HEAD^{tree}").decode().strip(),
        "commit_epoch": int(git(root, "show", "-s", "--format=%ct", "HEAD")),
        "files": {name: d.sha256(output / name) for name in FILES},
    }
    d.write_json(output / "inputs.json", record)
    d.outputs({"inputs-sha256": d.sha256(output / "inputs.json")})
    return 0


def inputs(directory, expected):
    d.require(
        d.sha256(directory / "inputs.json") == expected,
        "comparison input digest differs",
    )
    value = d.read_json(directory / "inputs.json")
    d.require(
        set(value)
        == {
            "schema_version",
            "qualifying",
            "candidate_sha",
            "tree",
            "commit_epoch",
            "files",
        }
        and value["schema_version"] == SCHEMA
        and value["qualifying"] is False,
        "invalid dependency comparison inputs",
    )
    q._require_sha(value["candidate_sha"], "comparison candidate")
    d.require(set(value["files"]) == set(FILES), "comparison input membership differs")
    for name, digest in value["files"].items():
        d.require(
            d.sha256(directory / name) == digest,
            "comparison frozen input differs: " + name,
        )
    for name in FILES[1:]:
        d.require(
            (directory / name).read_bytes()
            == Path(__file__).with_name(name).read_bytes(),
            "running helper differs from frozen comparison",
        )
    with tarfile.open(directory / FILES[0]) as archive:
        d.require(
            archive.pax_headers.get("comment") == value["candidate_sha"],
            "archive candidate differs",
        )
    return value


def environment(epoch):
    result = d.command_environment()
    for name in ("GITHUB_OUTPUT", "GITHUB_PATH", "GITHUB_ENV", "VIRTUAL_ENV"):
        result.pop(name, None)
    result.update(
        SOURCE_DATE_EPOCH=str(epoch),
        PIP_NO_CACHE_DIR="1",
        PIP_NO_INPUT="1",
        PIP_DISABLE_PIP_VERSION_CHECK="1",
    )
    return result


def invoke(command, log, env):
    started = time.monotonic()
    with log.open("wb") as stream:
        process = subprocess.Popen(
            [str(part) for part in command],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=os.name != "nt",
        )
        try:
            code = process.wait(timeout=1800)
        except BaseException:
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        stdin=subprocess.DEVNULL,
                        stdout=stream,
                        stderr=subprocess.STDOUT,
                        check=True,
                        timeout=10,
                    )
                else:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
            raise
    d.require(code == 0, "comparison command failed: " + log.name)
    return time.monotonic() - started


def interpreter(path):
    return path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def install_tools(root, output, cache_root, case, profile, helper, namespace, env):
    root.mkdir(parents=True)
    venv = root / ".venv"
    setup_seconds = invoke(
        [sys.executable, "-I", "-m", "venv", venv],
        output / (profile + "-venv.log"),
        env,
    )
    executable = interpreter(venv)
    source = root.parent / "source"
    lock = (
        source
        / "release"
        / ("requirements.txt" if case == "baseline" else profile + "-requirements.txt")
    )
    state = output / (profile + "-identity.json")
    setup_seconds += invoke(
        [
            executable,
            "-I",
            helper,
            "key",
            "--lock",
            lock,
            "--profile",
            profile,
            "--namespace",
            namespace,
            "--output",
            state,
        ],
        output / (profile + "-key.log"),
        env,
    )
    identity = d.read_json(state)
    cache = root / "restored-downloads"
    if case in {"warm", "stale", "corrupt"}:
        d.require(
            cache_root is not None, "cache control needs original verified downloads"
        )
        shutil.copytree(cache_root / profile, cache, symlinks=True)
        if case == "stale":
            manifest = d.read_json(cache / "manifest.json")
            manifest["identity"]["key"] = "old-key"
            d.write_json(cache / "manifest.json", manifest)
        elif case == "corrupt":
            wheel = next(cache.glob("*.whl"))
            wheel.write_bytes(wheel.read_bytes() + b"owned corruption control")
    command = [
        executable,
        "-I",
        helper,
        "setup",
        "--lock",
        lock,
        "--profile",
        profile,
        "--namespace",
        namespace,
        "--identity",
        state,
        "--output",
        output / profile,
    ]
    if case != "baseline":
        command += ["--cache", cache]
        if case == "unavailable":
            command += ["--no-cache-available"]
    setup_seconds += invoke(command, output / (profile + "-setup.log"), env)
    record = d.read_json(output / profile / "setup.json")
    expected = {
        "baseline": "disabled",
        "cold": "miss",
        "warm": "hit",
        "stale": "rejected",
        "corrupt": "rejected",
        "unavailable": "unavailable",
    }[case]
    d.require(
        record["complete"] is True and record["cache_state"] == expected,
        "cache control did not exercise the required path: " + case,
    )
    d.require(record["identity"] == identity, "cache control identity differs")
    record["venv_and_setup_seconds"] = setup_seconds
    record["installed_bytes"] = sum(
        path.stat().st_size
        for path in venv.rglob("*")
        if path.is_file() and not path.is_symlink()
    )
    if (
        case == "cold"
        and cache_root is not None
        and not (cache_root / profile).exists()
    ):
        cache_root.mkdir(parents=True, exist_ok=True)
        d.copy_verified(cache, cache_root / profile, identity, d.read_lock(lock))
        d.outputs({profile + "-cache-key": identity["key"]})
    return executable, record


def run_case(args):
    frozen = inputs(args.inputs, args.inputs_sha256)
    d.require(
        math.isfinite(args.cache_restore_seconds)
        and 0 <= args.cache_restore_seconds < 3600,
        "invalid cache transfer observation",
    )
    work, output = args.work.resolve(), args.output.resolve()
    d.require(
        not work.exists() and not output.exists(),
        "comparison work and evidence must be fresh",
    )
    work.mkdir(parents=True)
    output.mkdir(parents=True)
    record = {
        "schema_version": SCHEMA,
        "qualifying": False,
        "complete": False,
        "candidate_sha": frozen["candidate_sha"],
        "tree": frozen["tree"],
        "inputs_sha256": args.inputs_sha256,
        "case": args.case,
        "context": d.environment_identity(),
        "runner_image": os.environ.get("ImageVersion", "local"),
        "cache_namespace": args.namespace,
        "cache_restore_seconds": args.cache_restore_seconds,
        "builders": {},
        "artifacts": {},
        "validation": None,
        "error": None,
    }
    started = time.monotonic()
    env = environment(frozen["commit_epoch"])
    helper = args.inputs.resolve() / "dependency_downloads.py"
    try:
        for copy in ("a", "b"):
            root = work / copy
            source = root / "source"
            q.extract_source(
                argparse.Namespace(
                    archive=args.inputs / "candidate-source.tar",
                    sha256=frozen["files"]["candidate-source.tar"],
                    destination=source,
                )
            )
            evidence = output / copy
            evidence.mkdir()
            executable, setup = install_tools(
                root / "builder",
                evidence,
                args.cache,
                args.case,
                "build",
                helper,
                args.namespace,
                env,
            )
            dist = root / "dist"
            dist.mkdir()
            build_seconds = invoke(
                [
                    executable,
                    "-I",
                    "-m",
                    "build",
                    "--no-isolation",
                    "--sdist",
                    "--wheel",
                    "--outdir",
                    dist,
                    source,
                ],
                evidence / "build.log",
                env,
            )
            wheel, sdist = q._dist_files(dist)
            artifacts = {path.name: d.sha256(path) for path in (wheel, sdist)}
            record["builders"][copy] = {
                "setup": setup,
                "build_seconds": build_seconds,
                "artifacts": artifacts,
            }
            if copy == "a":
                if args.case == "baseline":
                    validator, validation_setup = executable, None
                else:
                    validator, validation_setup = install_tools(
                        root / "validator",
                        evidence,
                        args.cache,
                        args.case,
                        "validation",
                        helper,
                        args.namespace,
                        env,
                    )
                validation_seconds = invoke(
                    [validator, "-I", "-m", "twine", "check", wheel, sdist],
                    evidence / "twine.log",
                    env,
                )
                flags = [] if args.case == "baseline" else ["--no-build-isolation"]
                validation_seconds += invoke(
                    [
                        validator,
                        "-I",
                        source / "tests/verify_installed_knowledge_schema.py",
                        dist,
                        *flags,
                    ],
                    evidence / "artifact-validation.log",
                    env,
                )
                record["validation"] = {
                    "setup": validation_setup,
                    "seconds": validation_seconds,
                    "result": "PASS",
                    "artifacts": artifacts,
                }
        q.compare_builds(
            argparse.Namespace(
                first=work / "a/dist",
                second=work / "b/dist",
                output=output / "reproducible",
            )
        )
        d.require(
            record["builders"]["a"]["artifacts"]
            == record["builders"]["b"]["artifacts"],
            "independent build bytes differ",
        )
        record["artifacts"] = record["builders"]["a"]["artifacts"]
        record["complete"] = True
    except BaseException as exc:
        record["error"] = str(exc)
        raise
    finally:
        record["elapsed_seconds"] = time.monotonic() - started
        d.write_json(output / "comparison.json", record)
    return 0


def validate_result(value):
    d.require(
        isinstance(value, dict)
        and value.get("schema_version") == SCHEMA
        and value.get("qualifying") is False
        and value.get("complete") is True
        and value.get("error") is None
        and value.get("case") in CASES,
        "partial, unknown or qualifying cache comparison",
    )
    q._require_sha(value["candidate_sha"], "comparison candidate")
    q._require_sha(value["tree"], "comparison tree")
    q._require_sha256(value["inputs_sha256"], "comparison inputs")
    for field in ("elapsed_seconds", "cache_restore_seconds"):
        d.require(
            type(value[field]) in (int, float)
            and math.isfinite(value[field])
            and 0 <= value[field] < 14400,
            "invalid comparison duration",
        )
    artifacts = value["artifacts"]
    d.require(
        isinstance(artifacts, dict)
        and len(artifacts) == 2
        and sum(name.endswith(".whl") for name in artifacts) == 1
        and sum(name.endswith(".tar.gz") for name in artifacts) == 1,
        "incomplete comparison artifacts",
    )
    for digest in artifacts.values():
        q._require_sha256(digest, "comparison artifact")
    d.require(set(value["builders"]) == {"a", "b"}, "missing independent builder")
    setup = []
    for builder in value["builders"].values():
        d.require(
            builder["artifacts"] == artifacts, "independent builder artifacts differ"
        )
        setup.append(builder["setup"])
    validation = value["validation"]
    d.require(
        validation["result"] == "PASS" and validation["artifacts"] == artifacts,
        "installed consumer result differs",
    )
    if value["case"] == "baseline":
        d.require(
            validation["setup"] is None, "baseline validation environment differs"
        )
    else:
        setup.append(validation["setup"])
    expected = {
        "baseline": "disabled",
        "cold": "miss",
        "warm": "hit",
        "stale": "rejected",
        "corrupt": "rejected",
        "unavailable": "unavailable",
    }[value["case"]]
    for receipt in setup:
        d.require(
            receipt["schema_version"] == d.SCHEMA
            and receipt["complete"] is True
            and receipt["error"] is None
            and receipt["cache_state"] == expected,
            "cache control or fresh setup did not complete",
        )
        d.require(
            bool(receipt["installed"]) and bool(receipt["files"]),
            "missing installed dependency evidence",
        )
        d.require(
            receipt["identity"]["namespace"] == value["cache_namespace"],
            "cache namespace differs",
        )
    return value


def compare(args):
    values = [validate_result(d.read_json(path)) for path in args.result]
    d.require(
        len(values) == len(CASES) and {value["case"] for value in values} == set(CASES),
        "comparison cases are missing or repeated",
    )
    reference = values[0]
    for value in values:
        d.require(
            value["schema_version"] == SCHEMA
            and value["qualifying"] is False
            and value["complete"] is True
            and value["error"] is None,
            "partial or qualifying cache comparison",
        )
        for key in (
            "candidate_sha",
            "tree",
            "inputs_sha256",
            "artifacts",
            "context",
            "cache_namespace",
        ):
            d.require(
                value[key] == reference[key],
                "comparison inputs or artifact bytes differ: " + key,
            )
        d.require(
            value["validation"]["result"] == "PASS"
            and set(value["builders"]) == {"a", "b"},
            "comparison validation or builders incomplete",
        )
    d.write_json(
        args.output,
        {
            "schema_version": SCHEMA,
            "qualifying": False,
            "complete": True,
            "candidate_sha": reference["candidate_sha"],
            "inputs_sha256": reference["inputs_sha256"],
            "artifacts": reference["artifacts"],
            "cases": {
                value["case"]: {
                    "elapsed_seconds": value["elapsed_seconds"],
                    "cache_restore_seconds": value["cache_restore_seconds"],
                    "runner_image": value["runner_image"],
                }
                for value in values
            },
            "cache_default_enabled": False,
            "decision": "Await native cache-transfer measurements and full qualification before enabling by default",
        },
    )
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    frozen = commands.add_parser("freeze")
    frozen.add_argument("--root", type=Path, default=Path("."))
    frozen.add_argument("--candidate", required=True)
    frozen.add_argument("--output", type=Path, required=True)
    frozen.set_defaults(function=freeze)
    run = commands.add_parser("run")
    for name in ("inputs", "work", "output"):
        run.add_argument("--" + name, type=Path, required=True)
    run.add_argument("--inputs-sha256", required=True)
    run.add_argument("--case", choices=CASES, required=True)
    run.add_argument("--cache", type=Path)
    run.add_argument("--namespace", default="release")
    run.add_argument("--cache-restore-seconds", type=float, default=0.0)
    run.set_defaults(function=run_case)
    comparison = commands.add_parser("compare")
    comparison.add_argument("--result", type=Path, action="append", required=True)
    comparison.add_argument("--output", type=Path, required=True)
    comparison.set_defaults(function=compare)
    args = parser.parse_args()
    return args.function(args)


if __name__ == "__main__":
    raise SystemExit(main())
