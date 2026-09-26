"""Compare static-check policies on identical frozen inputs; never qualify a release."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import gc
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time
import tracemalloc
import types

SCHEMA = "agent-wiki-core-check-comparison/v1"
INPUT_SCHEMA = "agent-wiki-core-check-inputs/v1"
TARGETS = {
    "adapters": (
        "test_architecture_layers.py",
        "test_shared_validation_adapters_remain_thin",
    ),
    "duplicates": (
        "test_architecture_layers.py",
        "test_duplicated_validation_bodies_delegate_to_shared_module",
    ),
    "documentation": (
        "test_public_docs_vocabulary.py",
        "test_tracked_public_documentation_has_no_internal_vocabulary_or_dead_links",
    ),
}
FILES = ("baseline-source.tar", "candidate-source.tar", "core_check_performance.py")
TIMEOUT = 900


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def git(root: Path, *arguments: str) -> bytes:
    return subprocess.check_output(
        ["git", *arguments], cwd=root, stdin=subprocess.DEVNULL
    )


def freeze(args) -> int:
    for sha in (args.baseline, args.candidate):
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("comparison revisions must be full immutable Git SHAs")
        git(args.root, "cat-file", "-e", sha + "^{commit}")
    helper = git(
        args.root, "show", f"{args.candidate}:release/core_check_performance.py"
    )
    if helper != Path(__file__).read_bytes():
        raise ValueError("comparison helper differs from the candidate")
    if os.environ.get("GITHUB_SHA", args.candidate) != args.candidate:
        raise ValueError("workflow and comparison candidate revisions differ")
    if args.output.exists():
        raise ValueError("comparison inputs must be new")
    args.output.mkdir(parents=True)
    for role, sha in [("baseline", args.baseline), ("candidate", args.candidate)]:
        git(
            args.root,
            "archive",
            "--format=tar",
            f"--output={args.output / (role + '-source.tar')}",
            sha,
        )
    (args.output / "core_check_performance.py").write_bytes(helper)
    write(
        args.output / "inputs.json",
        {
            "schema_version": INPUT_SCHEMA,
            "qualifying": False,
            "baseline_sha": args.baseline,
            "candidate_sha": args.candidate,
            "baseline_tree": git(args.root, "rev-parse", args.baseline + "^{tree}")
            .decode()
            .strip(),
            "candidate_tree": git(args.root, "rev-parse", args.candidate + "^{tree}")
            .decode()
            .strip(),
            "files": {name: digest(args.output / name) for name in FILES},
        },
    )
    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a", encoding="utf-8") as stream:
            stream.write(f"inputs-sha256={digest(args.output / 'inputs.json')}\n")
    return 0


def inputs(directory: Path, expected: str) -> dict:
    if digest(directory / "inputs.json") != expected:
        raise ValueError("comparison input manifest digest differs")
    value = json.loads((directory / "inputs.json").read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or set(value)
        != {
            "schema_version",
            "qualifying",
            "baseline_sha",
            "candidate_sha",
            "baseline_tree",
            "candidate_tree",
            "files",
        }
        or value.get("schema_version") != INPUT_SCHEMA
        or value.get("qualifying") is not False
        or not isinstance(value.get("files"), dict)
        or set(value["files"]) != set(FILES)
        or any(
            not isinstance(value[key], str)
            or not re.fullmatch(r"[0-9a-f]{40}", value[key])
            for key in (
                "baseline_sha",
                "candidate_sha",
                "baseline_tree",
                "candidate_tree",
            )
        )
    ):
        raise ValueError("invalid comparison input manifest")
    for name in FILES:
        if digest(directory / name) != value["files"][name]:
            raise ValueError(f"comparison input differs: {name}")
    if digest(Path(__file__)) != value["files"]["core_check_performance.py"]:
        raise ValueError("running comparison helper differs from frozen inputs")
    return value


def prepare(args) -> int:
    value = inputs(args.inputs, args.inputs_sha256)
    # Extraction filters were security-backported to Python 3.10.12. Check the
    # capability rather than the minor version, and never extract unfiltered.
    if not hasattr(tarfile, "data_filter"):
        raise RuntimeError(
            "safe source extraction requires tarfile.data_filter; "
            "use a security-patched Python runtime (backported in 3.10.12)"
        )
    if args.work.exists():
        raise ValueError("comparison workspace must be new")
    args.work.mkdir(parents=True)
    for role in ("baseline", "candidate"):
        with tarfile.open(args.inputs / f"{role}-source.tar", "r:") as archive:
            if archive.pax_headers.get("comment") != value[role + "_sha"]:
                raise ValueError(f"{role} archive identity differs")
            archive.extractall(args.work / role, filter="data")
    return 0


def verify_extracted(archive_path: Path, root: Path) -> None:
    """Allow build metadata, but never a changed committed input or policy."""
    with tarfile.open(archive_path, "r:") as archive:
        for member in archive:
            path = root / member.name
            if member.isreg():
                stream = archive.extractfile(member)
                if (
                    stream is None
                    or path.is_symlink()
                    or hashlib.sha256(stream.read()).hexdigest() != digest(path)
                ):
                    raise ValueError(f"extracted source differs: {member.name}")
            elif member.issym() and (
                not path.is_symlink() or os.readlink(path) != member.linkname
            ):
                raise ValueError(f"extracted source link differs: {member.name}")


def load_policy(policy_root: Path, source_root: Path, filename: str, label: str):
    # Dependencies come from the policy revision; all repository input paths
    # resolve to the same candidate tree. Each timing observation is a fresh
    # process, and controls can load both versions without namespace leakage.
    for name in list(sys.modules):
        if name == "tests" or name.startswith("tests."):
            del sys.modules[name]
    sys.path.insert(0, str(policy_root))
    module = types.ModuleType("_core_policy_" + label + "_" + Path(filename).stem)
    module.__file__ = str(source_root / "tests" / filename)
    module.__package__ = "tests"
    sys.modules[module.__name__] = module
    code = (policy_root / "tests" / filename).read_text(encoding="utf-8")
    exec(compile(code, str(policy_root / "tests" / filename), "exec"), module.__dict__)
    return module


def tree_identity(root: Path) -> str:
    rows = []
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.is_symlink():
            rows.append((path.relative_to(root).as_posix(), "link", os.readlink(path)))
        elif path.is_file():
            rows.append((path.relative_to(root).as_posix(), "file", digest(path)))
    return hashlib.sha256(json.dumps(rows, ensure_ascii=True).encode()).hexdigest()


@contextmanager
def coverage_context(enabled: bool):
    if not enabled:
        yield
        return
    import coverage

    trace = coverage.Coverage(source=["llm_wiki_cli"], data_file=None)
    trace.start()
    try:
        # Match an active core coverage tracer, without claiming a full-suite
        # coverage percentage from a focused performance observation.
        import llm_wiki_cli  # noqa: F401

        yield
    finally:
        trace.stop()


def worker(args) -> int:
    filename, function = TARGETS[args.target]
    policy_root = args.work / args.role
    candidate = args.work / "candidate"
    before = tree_identity(candidate)
    os.environ["LLM_WIKI_QUALIFICATION_SOURCE_ARCHIVE"] = str(
        (args.inputs / "candidate-source.tar").resolve()
    )
    module = load_policy(policy_root, candidate, filename, args.role)
    gc.collect()
    if args.memory:
        tracemalloc.start()
    try:
        with coverage_context(args.coverage and not args.memory):
            start = time.perf_counter()
            getattr(module, function)()
            seconds = time.perf_counter() - start
        peak = tracemalloc.get_traced_memory()[1] if args.memory else None
    finally:
        if args.memory:
            tracemalloc.stop()
    if tree_identity(candidate) != before:
        raise ValueError("static check modified its candidate inputs")
    write(
        args.output,
        {
            "target": args.target,
            "role": args.role,
            "passed": True,
            "seconds": seconds,
            "python_peak_bytes": peak,
            "coverage": args.coverage and not args.memory,
            "input_tree_sha256": before,
            "policy_sha256": digest(policy_root / "tests" / filename),
        },
    )
    return 0


def _doc_control_texts(module) -> list[str]:
    texts = set()
    for name, function in vars(module).items():
        if not name.startswith("test_"):
            continue
        for mark in getattr(function, "pytestmark", []):
            if mark.name != "parametrize":
                continue
            names = mark.args[0]
            names = (
                [n.strip() for n in names.split(",")]
                if isinstance(names, str)
                else list(names)
            )
            for row in mark.args[1]:
                values = (
                    row.values
                    if hasattr(row, "marks")
                    else (row,)
                    if len(names) == 1
                    else row
                )
                for key, item in zip(names, values):
                    if isinstance(item, str):
                        if key in {"text", "snippet"}:
                            texts.add(item)
                        elif key == "destination":
                            texts.add(f"[owned]({item})")
    return sorted(texts)


def control_parity(args) -> dict:
    candidate = args.work / "candidate"
    baseline = load_policy(
        args.work / "baseline", candidate, "test_public_docs_vocabulary.py", "baseline"
    )
    current = load_policy(
        candidate, candidate, "test_public_docs_vocabulary.py", "candidate"
    )
    texts = _doc_control_texts(baseline)
    if not texts:
        raise ValueError("baseline documentation controls are missing")
    tracked = {
        "README.md",
        "docs/guide.md",
        "docs/native-knowledge.md",
        "docs/standalone-documentation.md",
    }
    for text in texts:
        old = [
            f.render()
            for f in baseline.scan_public_document(
                text, path="docs/guide.md", tracked_files=tracked
            )
        ]
        new = [
            f.render()
            for f in current.scan_public_document(
                text, path="docs/guide.md", tracked_files=tracked
            )
        ]
        if old != new:
            raise ValueError("documentation control outcomes or diagnostics differ")
    baseline = load_policy(
        args.work / "baseline", candidate, "test_architecture_layers.py", "baseline"
    )
    current = load_policy(
        candidate, candidate, "test_architecture_layers.py", "candidate"
    )
    observed = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        validation = root / "validation.py"
        validation.write_text(
            "def require_value(value):\n    return value\n", encoding="utf-8"
        )
        path = root / "first.py"
        other = root / "second.py"
        changes = [
            "def _required_first(value):\n    return str(value)\n",
            "from .validation import require_value\ndef _required_first(value):\n    return require_value(value)\n",
            "from .validation import require_value as shared\ndef _required_first(value):\n    alias = shared\n    return alias(value)\n",
        ]
        other.write_text(
            "def _required_second(raw):\n    return str(raw)\n", encoding="utf-8"
        )
        for source in changes:
            path.write_text(source, encoding="utf-8")
            old = baseline._duplicated_unshared_validation_helpers(
                services_root=root, validation_path=validation
            )
            new = current._duplicated_unshared_validation_helpers(
                services_root=root, validation_path=validation
            )
            if old != new:
                raise ValueError("architecture control outcomes or diagnostics differ")
            observed.append(old)
    return {
        "passed": True,
        "documentation_cases": len(texts),
        "architecture_cases": len(observed),
        "architecture_results": observed,
    }


def validate_observation(
    row, *, target: str, role: str, coverage: bool, memory: bool, policy_sha256: str
) -> None:
    if not isinstance(row, dict) or set(row) != {
        "target",
        "role",
        "passed",
        "seconds",
        "python_peak_bytes",
        "coverage",
        "input_tree_sha256",
        "policy_sha256",
    }:
        raise ValueError("comparison observation fields differ")
    if (
        row["target"] != target
        or row["role"] != role
        or row["passed"] is not True
        or row["coverage"] is not (coverage and not memory)
        or row["policy_sha256"] != policy_sha256
        or not isinstance(row["input_tree_sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", row["input_tree_sha256"])
        or type(row["seconds"]) not in (int, float)
        or not math.isfinite(row["seconds"])
        or row["seconds"] <= 0
        or (
            memory
            and (
                type(row["python_peak_bytes"]) is not int
                or row["python_peak_bytes"] < 0
            )
        )
        or (not memory and row["python_peak_bytes"] is not None)
    ):
        raise ValueError("comparison observation identity, outcome or metrics differ")


def run_observation(command, *, cwd, env, log, platform_name: str | None = None) -> int:
    system = os.name if platform_name is None else platform_name
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=system != "nt",
    )
    try:
        return process.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        # Windows venv executables may be launchers with an interpreter child.
        # Bound cleanup to this owned tree rather than terminating only its root.
        try:
            if system == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=10,
                    check=True,
                )
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        except (OSError, subprocess.SubprocessError) as exc:
            process.kill()
            process.wait(timeout=10)
            raise RuntimeError("comparison worker tree cleanup failed") from exc
        process.wait(timeout=10)
        raise


def compare(args) -> int:
    value = inputs(args.inputs, args.inputs_sha256)
    if args.samples not in (2, 4, 6):
        raise ValueError("use an even paired sample count: 2, 4 or 6")
    if args.output.exists():
        raise ValueError("comparison output must be new")
    args.output.mkdir(parents=True)
    for role in ("baseline", "candidate"):
        verify_extracted(args.inputs / f"{role}-source.tar", args.work / role)
    candidate = args.work / "candidate"
    provider = importlib.metadata.distribution("agent-wiki-cli")
    direct = json.loads(provider.read_text("direct_url.json") or "{}")
    if (
        sys.prefix == sys.base_prefix
        or direct.get("dir_info", {}).get("editable") is True
        or direct.get("url") != candidate.resolve().as_uri()
    ):
        raise ValueError(
            "compare inside a fresh venv with the candidate installed noneditably"
        )
    report = {
        "schema_version": SCHEMA,
        "qualifying": False,
        "complete": False,
        "passed": False,
        "inputs_sha256": args.inputs_sha256,
        "baseline_sha": value["baseline_sha"],
        "candidate_sha": value["candidate_sha"],
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "runner_image": os.environ.get("ImageVersion", "unreported"),
            "coverage": args.coverage,
            "packages": dict(
                sorted(
                    (d.metadata["Name"].lower(), d.version)
                    for d in importlib.metadata.distributions()
                )
            ),
        },
        "observations": [],
        "targets": {},
        "errors": [],
        "limits": "Fresh processes; paired order alternates. Timing excludes imports. Memory is a separate uninstrumented tracemalloc observation, not total RSS. No speed SLO or full-core timing claim.",
    }
    write(args.output / "comparison.json", report)
    try:
        report["controls"] = control_parity(args)
        for target in TARGETS:
            for sample in range(args.samples + 1):
                memory = sample == args.samples
                roles = (
                    ("baseline", "candidate")
                    if sample % 2 == 0
                    else ("candidate", "baseline")
                )
                for role in roles:
                    label = f"{target}-{role}-{'memory' if memory else sample}"
                    output = args.output / (label + ".json")
                    command = [
                        sys.executable,
                        "-I",
                        "-B",
                        str(Path(__file__).resolve()),
                        "worker",
                        "--work",
                        str(args.work.resolve()),
                        "--inputs",
                        str(args.inputs.resolve()),
                        "--role",
                        role,
                        "--target",
                        target,
                        "--output",
                        str(output.resolve()),
                    ]
                    if memory:
                        command.append("--memory")
                    elif args.coverage:
                        command.append("--coverage")
                    environment = {
                        **os.environ,
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "PYTHONUTF8": "1",
                        "PYTHONIOENCODING": "utf-8",
                    }
                    with (args.output / (label + ".log")).open("wb") as log:
                        result = run_observation(
                            command, cwd=candidate, env=environment, log=log
                        )
                    if result != 0:
                        raise ValueError(
                            f"comparison observation failed: {label}; see retained log"
                        )
                    row = json.loads(output.read_text(encoding="utf-8"))
                    validate_observation(
                        row,
                        target=target,
                        role=role,
                        coverage=args.coverage,
                        memory=memory,
                        policy_sha256=digest(
                            args.work / role / "tests" / TARGETS[target][0]
                        ),
                    )
                    report["observations"].append(row)
                    write(args.output / "comparison.json", report)
        if len({r["input_tree_sha256"] for r in report["observations"]}) != 1:
            raise ValueError(
                "baseline and candidate observations did not use identical inputs"
            )
        for target in TARGETS:
            rows = [r for r in report["observations"] if r["target"] == target]
            summary = {}
            for role in ("baseline", "candidate"):
                times = [
                    r["seconds"]
                    for r in rows
                    if r["role"] == role and r["python_peak_bytes"] is None
                ]
                summary[role] = {
                    "samples": times,
                    "median_seconds": statistics.median(times),
                    "python_peak_bytes": next(
                        r["python_peak_bytes"]
                        for r in rows
                        if r["role"] == role and r["python_peak_bytes"] is not None
                    ),
                }
            summary["time_ratio"] = (
                summary["candidate"]["median_seconds"]
                / summary["baseline"]["median_seconds"]
            )
            report["targets"][target] = summary
        report["complete"] = report["passed"] = True
    except (
        OSError,
        ValueError,
        RuntimeError,
        AssertionError,
        SyntaxError,
        ImportError,
        subprocess.SubprocessError,
    ) as exc:
        report["errors"].append(str(exc))
        raise
    finally:
        write(args.output / "comparison.json", report)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    frozen = commands.add_parser("freeze")
    frozen.add_argument("--root", type=Path, default=Path.cwd())
    frozen.add_argument("--baseline", required=True)
    frozen.add_argument("--candidate", required=True)
    frozen.add_argument("--output", type=Path, required=True)
    frozen.set_defaults(function=freeze)
    for name, function in [("prepare", prepare), ("compare", compare)]:
        command = commands.add_parser(name)
        command.add_argument("--inputs", type=Path, required=True)
        command.add_argument("--inputs-sha256", required=True)
        command.add_argument("--work", type=Path, required=True)
        if name == "compare":
            command.add_argument("--output", type=Path, required=True)
            command.add_argument("--samples", type=int, default=2)
            command.add_argument("--coverage", action="store_true")
        command.set_defaults(function=function)
    observation = commands.add_parser("worker")
    observation.add_argument("--inputs", type=Path, required=True)
    observation.add_argument("--work", type=Path, required=True)
    observation.add_argument("--output", type=Path, required=True)
    observation.add_argument("--role", choices=("baseline", "candidate"), required=True)
    observation.add_argument("--target", choices=tuple(TARGETS), required=True)
    observation.add_argument("--coverage", action="store_true")
    observation.add_argument("--memory", action="store_true")
    observation.set_defaults(function=worker)
    args = parser.parse_args()
    try:
        return args.function(args)
    except (
        OSError,
        ValueError,
        RuntimeError,
        AssertionError,
        SyntaxError,
        ImportError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"Core comparison refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
