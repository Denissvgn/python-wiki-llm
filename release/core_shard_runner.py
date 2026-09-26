"""Run isolated core shards with separate shadow and qualification contracts."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any

_spec = importlib.util.spec_from_file_location(
    "_core_shards", Path(__file__).with_name("core_shards.py")
)
assert _spec is not None and _spec.loader is not None
s = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s)
q = s.q
TIMEOUT = 5 * 60 * 60
COVERAGE_SCHEMA = "agent-wiki-core-shard-coverage/v1"
HARNESS_FILES = (
    "qualification.py",
    "core_shards.py",
    "core_shard_runner.py",
    "core-shard-timings.json",
)


def freeze(args) -> int:
    """Freeze shadow inputs independently of release tag/registry eligibility."""
    root, output = args.root.resolve(), args.output.resolve()
    q._require_sha(args.candidate_sha, "shadow candidate")

    def git(*words):
        return subprocess.check_output(
            ["git", *words], cwd=root, stdin=subprocess.DEVNULL
        )

    s.require(
        git("rev-parse", "HEAD").decode().strip() == args.candidate_sha,
        "shadow checkout differs",
    )
    s.require(
        not git("status", "--porcelain=v1", "--untracked-files=all").strip(),
        "shadow source must be clean",
    )
    s.require(
        not output.exists() and root not in output.parents,
        "frozen shadow output must be new and outside source",
    )
    for name in HARNESS_FILES:
        s.require(
            git("show", f"{args.candidate_sha}:release/{name}")
            == Path(__file__).with_name(name).read_bytes(),
            f"shadow freezer differs from candidate: {name}",
        )
    output.mkdir(parents=True)
    archive = output / "candidate-source.tar"
    git("archive", "--format=tar", f"--output={archive}", args.candidate_sha)
    harness = output / "qualification-harnesses.tar"
    git(
        "archive",
        "--format=tar",
        f"--output={harness}",
        args.candidate_sha,
        "--",
        *("release/" + name for name in HARNESS_FILES),
    )
    version = q._project_version(root)
    identity = {
        "schema_version": q.IDENTITY_SCHEMA,
        "repository": args.repository,
        "mode": "candidate",
        "version": version,
        "tag": "v" + version,
        "source": {
            "sha": args.candidate_sha,
            "tree": git("rev-parse", "HEAD^{tree}").decode().strip(),
            "commit_epoch": int(git("show", "-s", "--format=%ct", "HEAD")),
            "archive_sha256": q.sha256_file(archive),
        },
    }
    q._validate_identity(identity)
    q.write_json(output / "identity.json", identity)
    q.write_json(
        output / "freeze.json",
        {
            "schema_version": "agent-wiki-core-shard-freeze/v1",
            "purpose": "shadow",
            "qualifying": False,
            "identity": identity,
            "harness_sha256": q.sha256_file(harness),
        },
    )
    q._github_output(
        {
            "source-sha256": identity["source"]["archive_sha256"],
            "harness-sha256": q.sha256_file(harness),
        }
    )
    return 0


def verify_plan_input(args) -> int:
    value = s.validate_plan(
        s.read(args.plan), purpose=getattr(args, "purpose", "shadow")
    )
    current = value["context"]
    s.require(
        current["identity"] == q._validate_identity(s.read(args.identity))
        and current["harness_sha256"] == args.harness_sha256
        and current["run_id"] == args.run_id
        and current["run_attempt"] == args.run_attempt
        and current["environment"]["profile"] == s.profile(args.lane),
        "downloaded shard plan source, lane or run attempt differs",
    )
    s.require(
        args.constraints.read_text(encoding="utf-8")
        == constraints(current["environment"]),
        "downloaded dependency pins differ from the reference environment",
    )
    return 0


def environment(root: Path, lane: str) -> dict:
    expected = s.profile(lane)
    s.require(
        sys.prefix != sys.base_prefix,
        "core execution requires a fresh virtual environment",
    )
    s.require(
        platform.system()
        == {"ubuntu-24.04": "Linux", "windows-2025": "Windows", "macos-15": "Darwin"}[
            expected["os"]
        ],
        "core platform differs",
    )
    if expected["os"] == "ubuntu-24.04":
        distro = platform.freedesktop_os_release()
        s.require(
            distro.get("ID") == "ubuntu" and distro.get("VERSION_ID") == "24.04",
            "core requires Ubuntu 24.04",
        )
    elif expected["os"] == "macos-15":
        s.require(platform.mac_ver()[0].startswith("15."), "core requires macOS 15")
    else:
        s.require("2025" in platform.release(), "core requires Windows Server 2025")
    packages = {}
    for dist in importlib.metadata.distributions():
        name = re.sub(r"[-_.]+", "-", dist.metadata["Name"]).lower()
        s.require(name not in packages, f"duplicate installed distribution: {name}")
        packages[name] = dist.version
    provider = importlib.metadata.distribution("agent-wiki-cli")
    direct = json.loads(provider.read_text("direct_url.json") or "{}")
    s.require(
        direct.get("dir_info", {}).get("editable") is not True
        and direct.get("url") == root.resolve().as_uri(),
        "installed candidate source differs or is editable",
    )
    s.require(
        Path(sys.prefix).resolve()
        in Path(str(provider.locate_file(""))).resolve().parents,
        "candidate installation is outside the isolated environment",
    )
    result = {
        "profile": expected,
        "python": platform.python_version(),
        "machine": platform.machine(),
        "runner_image": os.environ.get("ImageVersion", "unreported"),
        "packages": dict(sorted(packages.items())),
    }
    s.validate_environment(result, lane)
    return result


def verify_source(root: Path, archive_path: Path, identity: dict) -> None:
    s.require(
        q.sha256_file(archive_path) == identity["source"]["archive_sha256"],
        "source archive digest differs",
    )
    with tarfile.open(archive_path, "r:") as archive:
        s.require(
            archive.pax_headers.get("comment") == identity["source"]["sha"],
            "source archive revision differs",
        )
        for member in archive:
            path = root / member.name
            if member.isfile():
                stream = archive.extractfile(member)
                s.require(
                    stream is not None and not path.is_symlink(),
                    "source member differs",
                )
                assert stream is not None
                with stream:
                    s.require(
                        stream.read() == path.read_bytes(),
                        f"source content differs: {member.name}",
                    )
            elif member.issym():
                s.require(
                    path.is_symlink() and os.readlink(path) == member.linkname,
                    "source symlink differs",
                )


def context(args) -> dict:
    identity = q._validate_identity(s.read(args.identity))
    s.require(
        q.sha256_file(args.harness) == args.harness_sha256,
        "core harness digest differs",
    )
    with tarfile.open(args.harness, "r:") as archive:
        s.require(
            archive.pax_headers.get("comment") == identity["source"]["sha"],
            "core harness revision differs",
        )
        for name in HARNESS_FILES:
            stream = archive.extractfile("release/" + name)
            s.require(stream is not None, f"missing core harness member: {name}")
            assert stream is not None
            with stream:
                s.require(
                    stream.read() == Path(__file__).with_name(name).read_bytes(),
                    f"running core harness differs: {name}",
                )
    verify_source(args.root, args.archive, identity)
    result = {
        "identity": identity,
        "harness_sha256": args.harness_sha256,
        "run_id": args.run_id,
        "run_attempt": args.run_attempt,
        "environment": environment(args.root, args.lane),
    }
    s.validate_context(result)
    return result


def constraints(value: dict) -> str:
    return s.constraints(value)


def child_environment(
    directory: Path, temporary: Path, archive: Path
) -> dict[str, str]:
    result = os.environ.copy()
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "COVERAGE_PROCESS_START",
        # This product option overrides repository/worktree cache precedence.
        # Isolation belongs to the job and temporary roots, not application flags.
        "LLM_WIKI_CACHE_DIR",
    ):
        result.pop(name, None)
    # The OS temporary root is retained so path-redaction assertions retain
    # their native meaning. Each worker receives its own private subdirectory.
    for name, path in {
        "TMPDIR": temporary,
        "TEMP": temporary,
        "TMP": temporary,
        "XDG_CACHE_HOME": directory / "cache",
        "PIP_CACHE_DIR": directory / "cache/pip",
    }.items():
        path.mkdir(parents=True, exist_ok=True)
        result[name] = str(path)
    result.update(
        PYTHONUTF8="1",
        PYTHONIOENCODING="utf-8",
        PYTHONDONTWRITEBYTECODE="1",
        LLM_WIKI_QUALIFICATION_SOURCE_ARCHIVE=str(archive.resolve()),
    )
    return result


def invoke(
    command: list[str], root: Path, env: dict, log: Path, timeout: int = TIMEOUT
) -> dict:
    started = time.monotonic()
    with log.open("wb") as stream:
        process = subprocess.Popen(
            command,
            cwd=root,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=os.name != "nt",
        )
        error = None
        try:
            code = process.wait(timeout=timeout)
        except BaseException as original:
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        stdin=subprocess.DEVNULL,
                        stdout=stream,
                        stderr=subprocess.STDOUT,
                        timeout=10,
                        check=True,
                    )
                else:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            except (OSError, subprocess.SubprocessError) as cleanup:
                process.kill()
                process.wait(timeout=10)
                raise RuntimeError(
                    "core worker process-tree cleanup failed"
                ) from cleanup
            process.wait(timeout=10)
            if not isinstance(original, subprocess.TimeoutExpired):
                raise
            code, error = 124, f"worker timed out after {timeout}s"
    return {"exit_code": code, "seconds": time.monotonic() - started, "error": error}


def source_manifest(package: Path) -> dict:
    return {
        path.relative_to(package).as_posix(): {
            "sha256": q.sha256_file(path),
            "line_count": len(path.read_bytes().splitlines()),
        }
        for path in sorted(package.rglob("*.py"))
        if not path.is_symlink()
    }


def package_root(root: Path) -> Path:
    package = Path(
        str(
            importlib.metadata.distribution("agent-wiki-cli").locate_file(
                "llm_wiki_cli"
            )
        )
    ).resolve()
    s.require(
        source_manifest(package) == source_manifest(root / "src/llm_wiki_cli"),
        "installed coverage source bytes differ",
    )
    return package


def coverage_rows(data_path: Path, source_roots: list[str], sources: dict) -> dict:
    from coverage import CoverageData

    data = CoverageData(basename=str(data_path))
    data.read()
    s.require(
        not data.has_arcs() and bool(data.measured_files()),
        "coverage data is absent or has a different branch policy",
    )
    # Only canonical Linux emits coverage. Decode stored POSIX paths explicitly
    # instead of allowing an artifact to choose arbitrary local source paths.
    s.require(
        isinstance(source_roots, list)
        and 1 <= len(source_roots) <= 2
        and all(isinstance(root, str) for root in source_roots)
        and len(set(source_roots)) == len(source_roots),
        "invalid coverage source roots",
    )
    prefixes = [PurePosixPath(root) for root in source_roots]
    s.require(
        all(prefix.is_absolute() and ".." not in prefix.parts for prefix in prefixes),
        "invalid coverage source prefix",
    )
    result: dict[str, set[int]] = {}
    for filename in data.measured_files():
        path = PurePosixPath(filename)
        matches = [prefix for prefix in prefixes if path.is_relative_to(prefix)]
        s.require(
            len(matches) == 1 and ".." not in path.parts,
            "coverage measured outside candidate provider",
        )
        name = path.relative_to(matches[0]).as_posix()
        s.require(name in sources, "coverage source is not in the frozen provider")
        lines = sorted(data.lines(filename) or [])
        # The native Python 3.10 tracer can record module entry at line 1 for
        # an empty file. Preserve that raw event: coverage's source analysis
        # still counts zero statements, and all other line bounds stay strict.
        last_line = max(1, sources[name]["line_count"])
        s.require(
            all(type(line) is int and 0 < line <= last_line for line in lines),
            f"invalid executed coverage line in {name} (maximum {last_line})",
        )
        result.setdefault(name, set()).update(lines)
    return {name: sorted(lines) for name, lines in result.items()}


def export_coverage(root: Path, output: Path) -> None:
    package = package_root(root)
    sources = source_manifest(package)
    roots = [package.as_posix(), (root / "src/llm_wiki_cli").resolve().as_posix()]
    rows = coverage_rows(output / "coverage.data", roots, sources)
    q.write_json(
        output / "coverage.json",
        {
            "schema_version": COVERAGE_SCHEMA,
            "source_roots": roots,
            "sources": sources,
            "lines": rows,
        },
    )


def worker(args) -> int:
    import pytest

    output = args.output.resolve()
    purpose = getattr(args, "purpose", "shadow")
    value = (
        None if args.collect else s.validate_plan(s.read(args.plan), purpose=purpose)
    )
    if args.index is not None:
        s.require(
            value is not None
            and type(args.index) is int
            and 0 <= args.index < value["shard_count"],
            "invalid worker shard index",
        )
    expected = None if value is None else value["inventory"]
    selected = (
        None
        if value is None
        else (
            value["inventory"]
            if args.index is None
            else value["shards"][args.index]["nodes"]
        )
    )
    started_path = output / "started.jsonl"
    with started_path.open("w", encoding="utf-8", buffering=1) as journal:

        class InventoryPlugin:
            @pytest.hookimpl(trylast=True)
            def pytest_collection_modifyitems(self, session, config, items):
                collected = s.inventory([item.nodeid for item in items])
                q.write_json(output / "collected.json", collected)
                if expected is not None:
                    s.require(
                        collected == expected,
                        "worker full collection differs from plan",
                    )
                    chosen = set(selected or [])
                    rejected = [item for item in items if item.nodeid not in chosen]
                    items[:] = [item for item in items if item.nodeid in chosen]
                    config.hook.pytest_deselected(items=rejected)
                    q.write_json(
                        output / "selected.json", sorted(item.nodeid for item in items)
                    )

            def pytest_runtest_logstart(self, nodeid, location):
                journal.write(json.dumps(nodeid) + "\n")

            def pytest_collection_finish(self, session):
                final = sorted(item.nodeid for item in session.items)
                s.require(
                    final
                    == (
                        selected
                        if selected is not None
                        else s.read(output / "collected.json")
                    ),
                    "a later plugin changed the planned selection",
                )

        flags = ["tests", *s.FLAGS]
        if args.collect:
            flags.append("--collect-only")
        else:
            flags.append(f"--junitxml={output / 'junit.xml'}")
            assert value is not None
            if value["context"]["environment"]["profile"]["coverage"]:
                os.environ["COVERAGE_FILE"] = str(output / "coverage.data")
                flags += [
                    "--cov=llm_wiki_cli",
                    "--cov-report=",
                    "--cov-fail-under=" + ("87" if args.index is None else "0"),
                ]
        code = int(pytest.main(flags, plugins=[InventoryPlugin()]))
    if (
        not args.collect
        and value is not None
        and value["context"]["environment"]["profile"]["coverage"]
    ):
        export_coverage(Path.cwd(), output)
    return code


def worker_command(output: Path, purpose: str) -> list[str]:
    return [
        sys.executable,
        "-I",
        "-X",
        "utf8",
        str(Path(__file__).resolve()),
        "worker",
        "--output",
        str(output),
        "--purpose",
        purpose,
    ]


def collect_plan(args, current: dict, env: dict, purpose: str) -> dict:
    collected = invoke(
        worker_command(args.output, purpose) + ["--collect"],
        args.root,
        env,
        args.output / "collection.log",
    )
    s.require(
        collected["exit_code"] == 0, "full core collection failed; see collection.log"
    )
    value = s.plan(
        s.read(args.output / "collected.json"),
        current,
        args.shards,
        s.read(Path(__file__).with_name("core-shard-timings.json")),
        purpose=purpose,
    )
    q.write_json(args.output / "plan.json", value)
    (args.output / "constraints.txt").write_text(
        constraints(current["environment"]), encoding="utf-8"
    )
    return value


def prepare(args) -> int:
    args.root, args.output = args.root.resolve(), args.output.resolve()
    s.require(
        not args.output.exists() and args.root not in args.output.parents,
        "preparation output must be new and outside source",
    )
    args.output.mkdir(parents=True)
    record: dict[str, Any] = {
        "schema_version": s.PREPARATION_SCHEMA,
        "purpose": "qualification",
        "qualifying": True,
        "complete": False,
        "context": None,
        "plan_sha256": None,
        "exit_code": None,
        "seconds": None,
        "files": {},
        "error": None,
    }
    q.write_json(args.output / "preparation.json", record)
    started = time.monotonic()
    try:
        current = context(args)
        s.validate_purpose("qualification", current, args.shards)
        record["context"] = current
        with tempfile.TemporaryDirectory(prefix="core-plan-") as temporary:
            env = child_environment(
                Path(temporary) / "state", Path(temporary) / "tmp", args.archive
            )
            value = collect_plan(args, current, env, "qualification")
        verify_source(args.root, args.archive, current["identity"])
        s.require(
            environment(args.root, args.lane) == current["environment"],
            "preparation environment changed",
        )
        record.update(
            plan_sha256=s.digest(value),
            exit_code=0,
            complete=True,
            seconds=time.monotonic() - started,
            files={
                name: q.sha256_file(args.output / name)
                for name in (
                    "plan.json",
                    "collected.json",
                    "constraints.txt",
                    "collection.log",
                    "started.jsonl",
                )
            },
        )
        q.write_json(args.output / "preparation.json", record)
        s.validate_preparation(args.output, value)
    except BaseException as error:
        record.update(
            complete=False, error=str(error), seconds=time.monotonic() - started
        )
        raise
    finally:
        q.write_json(args.output / "preparation.json", record)
    return 0


def execute(args) -> int:
    purpose = getattr(args, "purpose", "shadow")
    args.root, args.output = args.root.resolve(), args.output.resolve()
    s.require(
        not args.output.exists() and args.root not in args.output.parents,
        "worker output must be new and outside source",
    )
    args.output.mkdir(parents=True)
    receipt: dict[str, Any] = {
        "schema_version": s.execution_schema(purpose),
        "purpose": purpose,
        "qualifying": purpose == "qualification",
        "complete": False,
        "plan_sha256": None,
        "context": None,
        "index": args.index,
        "exit_code": None,
        "seconds": None,
        "files": {},
        "error": None,
    }
    q.write_json(args.output / "execution.json", receipt)
    started = time.monotonic()
    try:
        current = context(args)
        s.validate_purpose(purpose, current, args.shards)
        if purpose == "qualification":
            s.require(
                args.plan is not None,
                "qualifying workers require independently collected plans",
            )
        receipt["context"] = current
        with tempfile.TemporaryDirectory(prefix="core-shard-") as temporary:
            env = child_environment(
                Path(temporary) / "state", Path(temporary) / "tmp", args.archive
            )
            command = worker_command(args.output, purpose)
            if args.plan is None:
                s.require(args.index is None, "reference must not select a shard")
                value = collect_plan(args, current, env, purpose)
                args.plan = args.output / "plan.json"
            else:
                value = s.validate_plan(s.read(args.plan), current, purpose=purpose)
                s.require(
                    type(args.index) is int and 0 <= args.index < value["shard_count"],
                    "invalid shard index",
                )
            receipt["plan_sha256"] = s.digest(value)
            q.write_json(args.output / "execution.json", receipt)
            command += ["--plan", str(args.plan.resolve())]
            if args.index is not None:
                command += ["--index", str(args.index)]
            observed = invoke(command, args.root, env, args.output / "worker.log")
        receipt.update(observed)
        verify_source(args.root, args.archive, current["identity"])
        # Imports in fresh workers do not mutate their parent's package set.
        s.require(
            environment(args.root, args.lane) == current["environment"],
            "core environment changed during execution",
        )
        names = [
            "collected.json",
            "selected.json",
            "started.jsonl",
            "junit.xml",
            "worker.log",
        ]
        if current["environment"]["profile"]["coverage"]:
            names += ["coverage.data", "coverage.json"]
        receipt["files"] = {
            name: q.sha256_file(args.output / name)
            for name in names
            if (args.output / name).is_file()
        }
        receipt["complete"] = observed["exit_code"] == 0 and len(
            receipt["files"]
        ) == len(names)
        receipt["seconds"] = time.monotonic() - started
        q.write_json(args.output / "execution.json", receipt)
        if observed["exit_code"] != 0:
            # Surface the same bounded failure detail retained in the artifact.
            # A generic completeness rejection hides the original pytest/export
            # failure and makes a failed reference look like a matrix problem.
            log_path = args.output / "worker.log"
            with log_path.open("rb") as log:
                log.seek(0, os.SEEK_END)
                log.seek(max(0, log.tell() - 64 * 1024))
                tail = log.read().decode("utf-8", errors="replace").splitlines()[-60:]
            print("\n".join(tail), file=sys.stderr)
            role = "reference" if args.index is None else f"shard {args.index}"
            detail = (
                observed["error"] or f"worker exited with code {observed['exit_code']}"
            )
            raise q.QualificationError(f"core {role} {detail}; see retained worker.log")
        missing = sorted(set(names) - receipt["files"].keys())
        s.require(
            not missing, f"core worker did not produce required evidence: {missing}"
        )
        s.validate_execution(args.output, value, args.index, purpose=purpose)
    except BaseException as error:
        receipt.update(
            complete=False, error=str(error), seconds=time.monotonic() - started
        )
        raise
    finally:
        q.write_json(args.output / "execution.json", receipt)
    return 0


def aggregate_qualification(args) -> int:
    args.root, args.output = args.root.resolve(), args.output.resolve()
    s.require(
        not args.output.exists() and args.root not in args.output.parents,
        "qualifying aggregation output must be new and outside source",
    )
    args.output.mkdir(parents=True)
    record: dict[str, Any] = {
        "schema_version": s.AGGREGATION_SCHEMA,
        "purpose": "qualification",
        "qualifying": True,
        "complete": False,
        "context": None,
        "plan_sha256": None,
        "preparation_sha256": None,
        "shards": {},
        "files": {},
    }
    q.write_json(args.output / "aggregation.json", record)
    try:
        current = context(args)
        value = s.validate_plan(
            s.read(args.preparation / "plan.json"), current, purpose="qualification"
        )
        s.validate_preparation(args.preparation, value)
        directories = sorted(args.shards_root.iterdir())
        s.require(
            all(path.is_dir() and not path.is_symlink() for path in directories),
            "unexpected qualifying shard artifact",
        )
        xml = args.output / (s.WINDOWS_LANE + ".xml")
        merged = s.merge_junit(value, directories, xml, purpose="qualification")
        result = args.output / ("result-" + s.WINDOWS_LANE + ".json")
        q.verify_junit(
            argparse.Namespace(
                junit=xml,
                lane=s.WINDOWS_LANE,
                allowlist=args.root / "release/skip-allowlist.json",
                minimum_collected=5322,
                minimum_passed=5070,
                discovery=False,
                output=result,
            )
        )
        record.update(
            complete=True,
            context=current,
            plan_sha256=s.digest(value),
            preparation_sha256=q.sha256_file(args.preparation / "preparation.json"),
            shards={
                str(row["index"]): q.sha256_file(directory / "execution.json")
                for directory, row in zip(directories, merged["receipts"])
            },
            files={path.name: q.sha256_file(path) for path in (xml, result)},
        )
        q.write_json(args.output / "aggregation.json", record)
        s.validate_aggregation(
            args.output,
            args.preparation,
            directories,
            current["identity"],
            current["harness_sha256"],
            current["run_id"],
            current["run_attempt"],
            args.root / "release/skip-allowlist.json",
        )
    except BaseException:
        record["complete"] = False
        raise
    finally:
        q.write_json(args.output / "aggregation.json", record)
    return 0


def combine_coverage(
    value: dict, directories: list[Path], root: Path, output: Path
) -> dict:
    from coverage import Coverage

    package = package_root(root)
    sources = source_manifest(package)
    combined: dict[str, set[int]] = {}
    for directory in directories:
        recorded = s.read(directory / "coverage.json")
        s.fields(
            recorded,
            {"schema_version", "source_roots", "sources", "lines"},
            "coverage receipt",
        )
        s.require(
            recorded["schema_version"] == COVERAGE_SCHEMA
            and recorded["sources"] == sources,
            "coverage source identity differs",
        )
        lines = coverage_rows(
            directory / "coverage.data", recorded["source_roots"], sources
        )
        s.require(lines == recorded["lines"], "coverage receipt differs from raw data")
        for name, observed in lines.items():
            combined.setdefault(name, set()).update(observed)
    # The existing pytest pythonpath imports the byte-identical source checkout.
    # Rebase both verified copies to that canonical source for the same XML paths.
    canonical = (root / "src/llm_wiki_cli").resolve()
    output = output.resolve()
    xml = output / (
        "coverage-" + value["context"]["environment"]["profile"]["lane"] + ".xml"
    )
    previous = Path.cwd()
    try:
        os.chdir(root)
        coverage = Coverage(data_file=str(output / "coverage.data"))
        coverage.get_data().add_lines(
            {str(canonical / name): lines for name, lines in combined.items()}
        )
        coverage.save()
        coverage.xml_report(outfile=str(xml))
        percent = coverage.report(file=io.StringIO())
    finally:
        os.chdir(previous)
    s.require(percent >= 87, "combined canonical core coverage is below 87%")
    result = {
        "schema_version": COVERAGE_SCHEMA,
        "source_roots": [canonical.as_posix()],
        "sources": sources,
        "lines": {name: sorted(lines) for name, lines in combined.items()},
    }
    q.write_json(output / "coverage.json", result)
    return {
        "percent": percent,
        "xml_sha256": q.sha256_file(xml),
        "coverage_sha256": q.sha256_file(output / "coverage.json"),
    }


def compare(args) -> int:
    args.root, args.output = args.root.resolve(), args.output.resolve()
    s.require(not args.output.exists(), "comparison output must be new")
    args.output.mkdir(parents=True)
    report: dict[str, Any] = {
        "schema_version": "agent-wiki-core-shard-comparison/v2",
        "environment_policy": s.ENVIRONMENT_POLICY,
        "qualifying": False,
        "purpose": "shadow",
        "complete": False,
        "passed": False,
        "error": None,
    }
    q.write_json(args.output / "comparison.json", report)
    try:
        current = context(args)
        value = s.validate_plan(s.read(args.plan), current)
        reference = s.validate_execution(args.reference, value, None)
        directories = sorted(args.shards_root.iterdir())
        s.require(
            all(path.is_dir() and not path.is_symlink() for path in directories),
            "unexpected shard artifact",
        )
        lane = args.lane
        xml = args.output / f"{lane}.xml"
        merged = s.merge_junit(value, directories, xml)
        s.require(
            merged["outcomes"] == s.outcomes(s.junit(args.reference / "junit.xml")),
            "sharded/reference outcomes or skip reasons differ",
        )
        q.verify_junit(
            argparse.Namespace(
                junit=xml,
                lane=lane,
                allowlist=args.root / "release/skip-allowlist.json",
                minimum_collected=5322,
                minimum_passed=5070,
                discovery=False,
                output=args.output / f"result-{lane}.json",
            )
        )
        report.update(
            plan_sha256=s.digest(value),
            context=current,
            collected=len(value["inventory"]),
            shard_count=value["shard_count"],
            runner_images={
                "reference": reference["context"]["environment"]["runner_image"],
                "shards": {
                    str(row["index"]): row["context"]["environment"]["runner_image"]
                    for row in merged["receipts"]
                },
                "aggregation": current["environment"]["runner_image"],
            },
        )
        if current["environment"]["profile"]["coverage"]:
            report["coverage"] = combine_coverage(
                value, directories, args.root, args.output
            )
            ref_coverage = s.read(args.reference / "coverage.json")
            joined = s.read(args.output / "coverage.json")
            s.require(
                ref_coverage["sources"] == joined["sources"],
                "reference coverage sources differ",
            )
            s.require(
                ref_coverage["lines"]
                == coverage_rows(
                    args.reference / "coverage.data",
                    ref_coverage["source_roots"],
                    ref_coverage["sources"],
                ),
                "reference raw coverage differs",
            )
            s.require(
                set(ref_coverage["lines"]) == set(joined["lines"]),
                "sharding changed the measured source inventory",
            )
            lost = {
                name: sorted(set(lines) - set(joined["lines"][name]))
                for name, lines in ref_coverage["lines"].items()
            }
            s.require(not any(lost.values()), "sharding lost reference covered lines")
            report["coverage"]["additional_lines"] = sum(
                len(set(lines) - set(ref_coverage["lines"][name]))
                for name, lines in joined["lines"].items()
            )
        if lane == "core-windows-3.13":
            registry = s.read(args.root / "release/ubuntu-suites.json")
            for label in ("security", "product"):
                target = label + "-windows-2025"
                q.project_junit(
                    argparse.Namespace(
                        identity=args.identity,
                        source_junit=xml,
                        source_lane="core-shard-shadow-windows",
                        target_lane=target,
                        selector=registry["gates"][label + "-ubuntu-24.04"],
                        projected_junit=args.output / f"{target}.xml",
                        receipt=args.output / f"{target}-projection.json",
                    )
                )
        report["timing"] = {
            "reference_seconds": reference["seconds"],
            "shard_execution_seconds": [row["seconds"] for row in merged["receipts"]],
            "summed_shard_seconds": sum(row["seconds"] for row in merged["receipts"]),
            "longest_shard_seconds": max(row["seconds"] for row in merged["receipts"]),
            "worker_images_identical": len(
                {
                    report["runner_images"]["reference"],
                    *report["runner_images"]["shards"].values(),
                }
            )
            == 1,
            "comparison_limit": "Hosted image revisions are recorded per job. Different builds can affect timing; functional parity does not establish image equality or a speedup.",
            "scope": "Collection and execution only. Runner setup, queueing and artifact transfer must be measured from job metadata before rollout.",
        }
        report.update(complete=True, passed=True)
    except BaseException as error:
        report["error"] = str(error)
        raise
    finally:
        q.write_json(args.output / "comparison.json", report)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    frozen = commands.add_parser("freeze")
    frozen.add_argument("--root", type=Path, required=True)
    frozen.add_argument("--output", type=Path, required=True)
    frozen.add_argument("--candidate-sha", required=True)
    frozen.add_argument("--repository", required=True)
    frozen.set_defaults(function=freeze)
    verify = commands.add_parser("verify-plan")
    for name in ("plan", "constraints", "identity"):
        verify.add_argument("--" + name, type=Path, required=True)
    verify.add_argument("--harness-sha256", required=True)
    verify.add_argument("--run-id", type=int, required=True)
    verify.add_argument("--run-attempt", type=int, required=True)
    verify.add_argument("--lane", choices=sorted(s.PROFILES), required=True)
    verify.add_argument(
        "--purpose", choices=("shadow", "qualification"), default="shadow"
    )
    verify.set_defaults(function=verify_plan_input)
    raw = commands.add_parser("worker")
    raw.add_argument("--output", type=Path, required=True)
    raw.add_argument("--plan", type=Path)
    raw.add_argument("--index", type=int)
    raw.add_argument("--collect", action="store_true")
    raw.add_argument("--purpose", choices=("shadow", "qualification"), default="shadow")
    raw.set_defaults(function=worker)
    for command, function in (
        ("execute", execute),
        ("compare", compare),
        ("prepare", prepare),
        ("aggregate", aggregate_qualification),
    ):
        child = commands.add_parser(command)
        for name in ("root", "identity", "archive", "harness", "output"):
            child.add_argument("--" + name, type=Path, required=True)
        child.add_argument("--harness-sha256", required=True)
        child.add_argument("--run-id", type=int, required=True)
        child.add_argument("--run-attempt", type=int, required=True)
        child.add_argument("--lane", choices=sorted(s.PROFILES), required=True)
        if command in {"execute", "compare"}:
            child.add_argument("--plan", type=Path, required=command == "compare")
        if command in {"execute", "prepare"}:
            child.add_argument("--shards", type=int, default=2)
        if command == "execute":
            child.add_argument("--index", type=int)
            child.add_argument(
                "--purpose",
                choices=("shadow", "qualification"),
                default="shadow",
            )
        elif command == "compare":
            child.add_argument("--reference", type=Path, required=True)
            child.add_argument("--shards-root", type=Path, required=True)
        elif command == "aggregate":
            child.add_argument("--preparation", type=Path, required=True)
            child.add_argument("--shards-root", type=Path, required=True)
        child.set_defaults(function=function)
    args = parser.parse_args()
    return args.function(args)


if __name__ == "__main__":
    raise SystemExit(main())
