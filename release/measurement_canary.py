"""Run the complete bounded measurement consumer on native Windows.

PR mode retains base-owned collection/JUnit readers. Frozen mode verifies the
candidate against its authenticated source archive and transferred harness.
This canary never replaces normal qualification or grants publication authority.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
import tarfile
import time
import tomllib

MODULE = "tests/test_developer_value_measure.py"
GROUPS = (
    "context-v1-v2",
    "changed-sync",
    "unchanged-sync",
    "prose-reanchor",
    "strict-validation",
)
READERS = ("pr_ci_pytest.py", "core_shards.py", "qualification.py")
MAX_REPORT_BYTES = 128 * 1024 * 1024
MAX_REPORT_FILES = 5000
REPOSITORY = "Denissvgn/python-wiki-llm"


class CanaryError(ValueError):
    """The native consumer did not establish its bounded complete result."""


def require(value, message):
    if not value:
        raise CanaryError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(out, name, value):
    with (out / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def redirected(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def safe(path):
    path = Path(os.path.abspath(path))
    require(
        not any(redirected(p) for p in (*reversed(path.parents), path)),
        "Redirected canary path",
    )
    return path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CanaryError("Unavailable canary reader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.__file__ is None:
        raise CanaryError("Unavailable canary reader origin")
    require(
        Path(module.__file__).resolve() == Path(path).resolve(),
        "Reader module origin differs",
    )
    return module


def provider_files(root):
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    package = root / "src/llm_wiki_cli"
    paths = set(package.rglob("*.py"))
    for pattern in project["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]:
        paths.update(package.glob(pattern))
    files = {}
    for path in sorted(paths):
        safe(path)
        if path.is_file():
            require(
                path.stat().st_nlink == 1 and path.stat().st_size <= 64 * 1024 * 1024,
                "Invalid provider source file",
            )
            files[path.relative_to(package).as_posix()] = sha(path)
    require(bool(files), "Provider namespace is empty")
    return {"version": project["project"]["version"], "files": files}


def verify_provider(expected):
    import importlib.metadata
    import llm_wiki_cli

    package = Path(llm_wiki_cli.__file__).resolve().parent
    require(
        package.is_relative_to(Path(sys.prefix).resolve())
        and "site-packages" in package.parts,
        "Provider is not a noneditable isolated installation",
    )
    distribution = importlib.metadata.distribution("agent-wiki-cli")
    direct = json.loads(distribution.read_text("direct_url.json") or "{}")
    require(
        direct.get("dir_info", {}).get("editable") is not True,
        "Editable provider refused",
    )
    actual = {}
    for path in package.rglob("*"):
        require(not redirected(path), "Redirected installed provider")
        if (
            path.is_file()
            and "__pycache__" not in path.relative_to(package).parts
            and path.suffix != ".pyc"
        ):
            actual[path.relative_to(package).as_posix()] = sha(path)
    require(
        actual == expected["files"] and distribution.version == expected["version"],
        "Installed provider differs from candidate namespace",
    )
    return {
        "provider": str(package),
        "files": len(actual),
        "version": distribution.version,
    }


def capture_reports(basetemp, out):
    capture = {
        "complete": False,
        "data_only": True,
        "limit_bytes": MAX_REPORT_BYTES,
        "limit_files": MAX_REPORT_FILES,
        "files": {},
        "temporary_aliases_not_followed": [],
        "measurement_roots": [],
    }
    total = 0
    try:
        with tarfile.open(
            out / "measurement-reports.tar", "x", dereference=True
        ) as archive:
            for measurements in sorted(basetemp.glob("*/measurements")):
                case_root = measurements.parent
                if redirected(case_root):
                    capture["temporary_aliases_not_followed"].append(case_root.name)
                    continue
                require(
                    measurements.is_dir() and not redirected(measurements),
                    "Redirected measurement root",
                )
                capture["measurement_roots"].append(
                    measurements.relative_to(basetemp).as_posix()
                )
                for path in sorted(measurements.rglob("*")):
                    require(not redirected(path), "Redirected measurement report")
                    if not path.is_file():
                        continue
                    before = path.stat()
                    require(
                        stat.S_ISREG(before.st_mode), "Invalid measurement report type"
                    )
                    total += before.st_size
                    require(
                        total <= MAX_REPORT_BYTES
                        and len(capture["files"]) < MAX_REPORT_FILES,
                        "Raw measurement evidence exceeds bound",
                    )
                    name = path.relative_to(basetemp).as_posix()
                    checksum = sha(path)
                    archive.add(path, arcname=name, recursive=False)
                    after = path.stat()
                    require(
                        (before.st_size, before.st_mtime_ns, before.st_ino)
                        == (after.st_size, after.st_mtime_ns, after.st_ino),
                        "Report changed during capture",
                    )
                    capture["files"][name] = {
                        "sha256": checksum,
                        "bytes": before.st_size,
                        "mode": oct(before.st_mode & 0o777),
                    }
        capture.update(
            complete=True,
            bytes=total,
            archive_sha256=sha(out / "measurement-reports.tar"),
        )
    except (OSError, ValueError, tarfile.TarError) as error:
        capture.update(
            error_type=type(error).__name__, error=str(error)[:1000], bytes=total
        )
    save(out, "raw-reports-inventory.json", capture)
    return capture


def validate_results(collection, started, cases, capture):
    collected = collection["collected"]
    require(
        isinstance(collected, list)
        and len(collected) >= 18
        and len(set(collected)) == len(collected),
        "Incomplete or duplicated module collection",
    )
    require(
        collection["deselected"] == []
        and Counter(collection["selected"]) == Counter(collected),
        "Measurement module was deselected",
    )
    require(
        all(node.startswith(MODULE + "::") for node in collected),
        "Unexpected consumer selector",
    )
    critical = MODULE + "::test_timed_read_and_mutation_restore_equivalent_inputs"
    require(
        {critical + "[" + group + "]" for group in GROUPS} <= set(collected),
        "A bounded measurement group is missing",
    )
    require(
        Counter(started) == Counter(collected),
        "Started inventory differs from collection",
    )
    require(set(cases) == set(collected), "JUnit differs from complete collection")
    require(
        all(
            not any(
                case.find(tag) is not None for tag in ("failure", "error", "skipped")
            )
            for case in cases.values()
        ),
        "Measurement consumer failed or unexpectedly skipped",
    )
    require(
        capture["complete"] and len(capture["measurement_roots"]) == len(GROUPS),
        "Inner measurement evidence is incomplete",
    )
    return {
        "collected": len(collected),
        "started": len(started),
        "passed": len(cases),
        "skipped": 0,
        "deselected": 0,
    }


def run(args):
    root, out = safe(args.root), safe(args.output)
    require(
        not out.is_relative_to(root), "Canary evidence must be outside candidate source"
    )
    require(
        sys.platform == "win32" and platform.python_version() == args.expected_python,
        "Canary needs the exact native Windows interpreter",
    )
    require(
        platform.machine().lower() in {"amd64", "x86_64"} and sys.maxsize > 2**32,
        "Canary needs the declared x64 architecture",
    )
    require(
        Path(sys.prefix).resolve()
        == Path(args.expected_prefix or root / ".venv").resolve()
        and sys.prefix != sys.base_prefix,
        "Canary virtual environment differs",
    )
    require(
        re.fullmatch(r"[0-9a-f]{40}", args.source_sha) is not None,
        "Invalid candidate SHA",
    )
    require(
        os.environ.get("GITHUB_REPOSITORY") == REPOSITORY, "Canary repository differs"
    )
    require(
        all(
            re.fullmatch(r"[1-9][0-9]*", os.environ.get(name, ""))
            for name in ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT")
        ),
        "Canary run/attempt identity unavailable",
    )
    require(
        not os.environ.get("PYTEST_ADDOPTS") and not os.environ.get("PYTEST_PLUGINS"),
        "Ambient pytest options/plugins refused",
    )
    if out.exists():
        allowed = {
            "bootstrap-identity.json",
            "pip-install.log",
            "pip-check.log",
            "dependencies.txt",
            "native-module.log",
        }
        require(
            all(
                p.name in allowed and p.is_file() and not redirected(p)
                for p in out.iterdir()
            ),
            "Occupied canary evidence refused",
        )
        if (out / "bootstrap-identity.json").exists():
            bootstrap = json.loads(
                (out / "bootstrap-identity.json").read_text(encoding="utf-8-sig")
            )
            require(
                bootstrap.get("candidate_sha") == args.source_sha
                and str(bootstrap.get("run_id")) == os.environ.get("GITHUB_RUN_ID")
                and str(bootstrap.get("attempt"))
                == os.environ.get("GITHUB_RUN_ATTEMPT"),
                "Bootstrap identity differs",
            )
    else:
        out.mkdir(parents=True)

    def git(*command):
        return subprocess.check_output(["git", *command], cwd=root)

    tools = out / "base-tools"
    tools.mkdir()
    if args.frozen_identity is not None:
        require(
            args.harness_root is not None,
            "Frozen canary requires the transferred harness",
        )
        harness = safe(args.harness_root)
        for name in READERS:
            (tools / name).write_bytes((harness / "release" / name).read_bytes())
        reader = load("measurement_core_reader", tools / "core_shards.py")
        frozen = reader.q._validate_identity(
            reader.q.load_json(safe(args.frozen_identity))
        )
        require(
            frozen["mode"] == "candidate"
            and frozen["repository"] == REPOSITORY
            and frozen["source"]["sha"] == args.source_sha,
            "Frozen source identity differs",
        )
        source_reader = load(
            "measurement_source_reader", harness / "release/core_shard_runner.py"
        )
        archive = Path(args.frozen_identity).absolute().parent / "candidate-source.tar"
        source_reader.verify_source(root, archive, frozen)

        def unchanged():
            source_reader.verify_source(root, archive, frozen)

        source = {
            "mode": "frozen",
            "tree": frozen["source"]["tree"],
            "source_archive_sha256": frozen["source"]["archive_sha256"],
            "commit_epoch": frozen["source"]["commit_epoch"],
        }
    else:
        base, head = os.environ.get("BASE_SHA", ""), os.environ.get("HEAD_SHA", "")
        require(
            all(re.fullmatch(r"[0-9a-f]{40}", value) for value in (base, head)),
            "PR base/head identity unavailable",
        )
        require(
            git("rev-parse", "HEAD").decode().strip() == args.source_sha
            and git("show", "-s", "--format=%P", args.source_sha).decode().split()
            == [base, head],
            "PR merge identity differs",
        )
        require(not git("status", "--porcelain").strip(), "PR source is not clean")
        remote = git("remote", "get-url", "origin").decode().strip()
        require(
            remote
            in {
                "https://github.com/" + REPOSITORY,
                "https://github.com/" + REPOSITORY + ".git",
                "git@github.com:" + REPOSITORY + ".git",
            },
            "PR source origin differs",
        )
        for name in READERS:
            (tools / name).write_bytes(git("show", base + ":release/" + name))
        reader = load("measurement_core_reader", tools / "core_shards.py")

        def unchanged():
            require(
                not git("status", "--porcelain", "--untracked-files=no").strip(),
                "PR tracked source changed",
            )

        unchanged()
        workflow = ".github/workflows/windows-measurement.yml"
        require(
            git("show", args.source_sha + ":" + workflow)
            == (root / workflow).read_bytes(),
            "PR workflow source differs",
        )
        source = {
            "mode": "pull-request",
            "tree": git("rev-parse", "HEAD^{tree}").decode().strip(),
            "head_sha": head,
            "base_sha": base,
            "canonical_origin": remote,
            "workflow_blob": git("rev-parse", args.source_sha + ":" + workflow)
            .decode()
            .strip(),
        }
    workflow_sha, workflow_ref = (
        os.environ.get("GITHUB_WORKFLOW_SHA", ""),
        os.environ.get("GITHUB_WORKFLOW_REF", ""),
    )
    workflow_path = (
        "release-qualification.yml"
        if args.frozen_identity is not None
        else "windows-measurement.yml"
    )
    require(
        re.fullmatch(r"[0-9a-f]{40}", workflow_sha) is not None
        and workflow_ref.startswith(
            REPOSITORY + "/.github/workflows/" + workflow_path + "@"
        ),
        "Workflow execution identity unavailable",
    )
    if args.frozen_identity is not None:
        require(
            workflow_sha == args.source_sha
            and workflow_ref.endswith("@refs/heads/main"),
            "Frozen canary workflow identity differs",
        )
    identity = {
        "schema_version": "native-measurement-regression/v2",
        "purpose": "fixed-module native regression; not full qualification or policy ownership",
        "repository": REPOSITORY,
        "candidate_sha": args.source_sha,
        **source,
        "run_id": os.environ["GITHUB_RUN_ID"],
        "attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "module": MODULE,
        "module_sha256": sha(root / MODULE),
        "python": platform.python_version(),
        "platform": sys.platform,
        "machine": platform.machine(),
        "executable": sys.executable,
        "prefix": sys.prefix,
        "workflow_sha": workflow_sha,
        "workflow_ref": workflow_ref,
        "publication_authority": False,
    }
    save(out, "identity.json", identity)
    save(out, "base-reader-hashes.json", {p.name: sha(p) for p in tools.iterdir()})
    witness = load("measurement_collection", tools / "pr_ci_pytest.py")
    expected = provider_files(root)
    save(out, "expected-provider.json", expected)
    save(out, "installed-origin-before.json", verify_provider(expected))
    sys.path.insert(0, str(root))
    os.environ["PR_CI_COLLECTION"] = str(out / "collection.json")
    pytest = importlib.import_module("pytest")

    class Started:
        def pytest_runtest_logstart(self, nodeid, location):
            with (out / "started.jsonl").open("a", encoding="utf-8") as journal:
                journal.write(json.dumps(nodeid) + "\n")

    (out / "started.jsonl").write_bytes(b"")
    basetemp = out / "pytest"
    command = [
        MODULE,
        "-q",
        "-p",
        "no:cacheprovider",
        "--strict-config",
        "--strict-markers",
        "-W",
        "error",
        "-o",
        "xfail_strict=true",
        "--junitxml=" + str(out / "junit.xml"),
        "--basetemp=" + str(basetemp),
    ]
    save(
        out,
        "command.json",
        {
            "actual_runner_orig_argv": sys.orig_argv,
            "actual_runner_argv": sys.argv,
            "pytest_args": command,
            "executed_via": "isolated maintained controller invokes pytest.main",
            "collection_witness": {
                "file": str(tools / "pr_ci_pytest.py"),
                "sha256": sha(tools / "pr_ci_pytest.py"),
            },
            "arbitrary_selector_input": False,
        },
    )
    started_at, exit_code = time.time(), None
    try:
        previous = Path.cwd()
        os.chdir(root)
        try:
            exit_code = int(pytest.main(command, plugins=[witness, Started()]))
        finally:
            os.chdir(previous)
    finally:
        capture = capture_reports(basetemp, out)
        save(
            out,
            "execution.json",
            {
                "pytest_exit_code": exit_code,
                "seconds": time.time() - started_at,
                "raw_capture_complete": capture["complete"],
            },
        )
    require(exit_code == 0, "Measurement module failed")
    collection = reader.q.load_json(out / "collection.json")
    nodes = reader.inventory(collection["collected"])
    started = [
        json.loads(line)
        for line in (out / "started.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    counts = validate_results(
        collection, started, reader.junit(out / "junit.xml"), capture
    )
    require(set(nodes) == set(collection["collected"]), "Collection reader differs")
    unchanged()
    save(out, "installed-origin-after.json", verify_provider(expected))
    save(
        out,
        "result.json",
        {
            **identity,
            **counts,
            "status": "passed",
            "junit_sha256": sha(out / "junit.xml"),
            "raw_capture_complete": True,
            "qualification": False,
            "source_tracked_tree_unchanged": True,
        },
    )
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-python", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--frozen-identity", type=Path)
    parser.add_argument("--harness-root", type=Path)
    parser.add_argument("--expected-prefix", type=Path)
    args = parser.parse_args(argv)
    try:
        return run(args)
    except (OSError, ValueError) as error:
        print("Native measurement canary failed: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
