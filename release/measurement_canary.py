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
from pathlib import Path, PurePosixPath, PureWindowsPath
import platform
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import time

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
MAX_GIT_OUTPUT = 16 * 1024 * 1024
MAX_TRACKED_SOURCE_FILES = 50000
MAX_TRACKED_FILE_BYTES = 64 * 1024 * 1024
MAX_TRACKED_SOURCE_BYTES = 512 * 1024 * 1024
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
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & 0x400
    )


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
    import tomllib

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
    return {
        "version": project["project"]["version"],
        "files": files,
        "source_origin": root.resolve().as_uri(),
    }


def _observe_installed_provider(expected):
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
        direct.get("dir_info", {}).get("editable") is not True
        and direct.get("url") == expected["source_origin"],
        "Installed source origin differs or is editable",
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
        "source_origin": direct["url"],
    }


def verify_provider(expected):
    # The measurement runtime deliberately imports ROOT/src in the controller.
    # Verify the noneditable installation in another isolated interpreter so
    # that this probe cannot pin the controller to site-packages beforehand.
    probe = """import importlib.util,json,sys
spec=importlib.util.spec_from_file_location('canary_provider_probe',sys.argv[1])
assert spec is not None and spec.loader is not None
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
print(json.dumps(module._observe_installed_provider(json.load(sys.stdin))))
"""
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-c", probe, str(Path(__file__).resolve())],
            input=json.dumps(expected, sort_keys=True),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise CanaryError("Isolated provider verification timed out") from error
    require(
        result.returncode == 0,
        "Isolated provider verification failed: " + result.stderr[-2000:],
    )
    observation = json.loads(result.stdout)
    require(isinstance(observation, dict), "Provider observation is not an object")
    return observation


def workflow_identity(source_sha, *, frozen, environment):
    workflow_sha = environment.get("GITHUB_WORKFLOW_SHA", "")
    workflow_ref = environment.get("GITHUB_WORKFLOW_REF", "")
    workflow_path = "release-qualification.yml" if frozen else "windows-measurement.yml"
    prefix = REPOSITORY + "/.github/workflows/" + workflow_path + "@"
    require(
        re.fullmatch(r"[0-9a-f]{40}", workflow_sha) is not None
        and workflow_ref.startswith(prefix),
        "Workflow execution identity unavailable",
    )
    if frozen:
        run_ref = environment.get("GITHUB_REF", "")
        require(
            run_ref.startswith("refs/heads/")
            and workflow_sha == source_sha
            and workflow_ref == prefix + run_ref,
            "Frozen canary workflow identity differs",
        )
    return workflow_sha, workflow_ref


def git_output(root, *command):
    """Read original Git objects even when local replacement refs exist."""
    with tempfile.TemporaryFile() as output:
        try:
            subprocess.run(
                ["git", "--no-replace-objects", *command], cwd=root,
                stdout=output, stderr=subprocess.PIPE, timeout=30, check=True,
            )
        except subprocess.SubprocessError as error:
            raise CanaryError("Original Git source inspection failed") from error
        output.seek(0)
        raw = output.read(MAX_GIT_OUTPUT + 1)
    require(len(raw) <= MAX_GIT_OUTPUT, "Git source metadata exceeds bound")
    return raw


def _source_redirected(path: Path) -> bool:
    return path.is_symlink() or bool(
        getattr(path.lstat(), "st_file_attributes", 0) & 0x400
    )


def _literal_ignored_directories(path: Path) -> set[str]:
    """Read only frozen literal directory rules, not arbitrary ignore patterns."""
    return {
        line.strip("/")
        for line in path.read_text(encoding="utf-8", errors="surrogateescape").splitlines()
        if re.fullmatch(r"/?[A-Za-z0-9_.-]+/", line)
        and line.strip("/") not in {".", ".."}
    }


def _verify_source_additions(root: Path, names: set[str]) -> None:
    """Bind frozen input trees without traversing unrelated checkout scratch."""
    input_roots = {"src", "tests", "release"}.intersection(
        name.partition("/")[0] for name in names
    )
    directories = {parent.as_posix() for name in names
                   for parent in PurePosixPath(name).parents if parent != PurePosixPath(".")}
    config_files = {
        ".coveragerc", ".coveragerc.toml", "pytest.ini", ".pytest.ini", "pytest.toml",
        ".pytest.toml", "setup.cfg", "tox.ini", "pyproject.toml",
    }
    executable_suffixes = {".py", ".pyc", ".pyo", ".so", ".pyd", ".dll", ".dylib"}
    # Keep declared top-level scratch, such as reports and .venv, opaque. Only
    # literal directory rules are needed here; this is not a Gitignore matcher.
    ignored_roots = {".git"}
    if ".gitignore" in names:
        ignored_roots.update(_literal_ignored_directories(root / ".gitignore"))
    # Native helper assets have their own tracked build-output rules. These
    # non-Python caches are not shipped or imported by core execution. Keep
    # them opaque without extending that exception to Python/fixture inputs.
    native_outputs = set()
    for name in names:
        parts = PurePosixPath(name).parts
        if (len(parts) == 5 and parts[:3] == ("src", "llm_wiki_cli", "extractors")
                and parts[3].endswith("_scripts") and parts[4] == ".gitignore"):
            parent = PurePosixPath(name).parent
            if any(row.startswith(parent.as_posix() + "/") and row.endswith(".py") for row in names):
                continue
            for folder in _literal_ignored_directories(root / name):
                output = (parent / folder).as_posix()
                if output not in names and output not in directories:
                    native_outputs.add(output)
    archived_roots = {name.partition("/")[0] for name in names}
    limit = max(10000, len(names) * 4)
    entries = 0
    for path in root.iterdir():
        entries += 1
        require(entries <= limit, "source input inventory exceeds bound")
        if path.name in archived_roots:
            continue
        if not path.is_dir():
            require(path.suffix.casefold() not in executable_suffixes
                      and path.name.casefold() not in config_files,
                      f"unfrozen source input: {path.name}")
        elif path.name not in ignored_roots:
            require(not _source_redirected(path),
                    f"redirected source input: {path.name}")
            # Namespace packages do not require __init__.py. Inspect only
            # unknown, unignored roots and share the input-tree entry budget.
            for current, folders, files in os.walk(path, followlinks=False):
                for child in [*folders, *files]:
                    entries += 1
                    require(entries <= limit, "source input inventory exceeds bound")
                    extra = Path(current) / child
                    text = extra.relative_to(root).as_posix()
                    require(not _source_redirected(extra),
                            f"redirected source input: {text}")
                    if not extra.is_dir():
                        require(extra.suffix.casefold() not in executable_suffixes,
                                f"unfrozen source package: {text}")
    for name in sorted(input_roots):
        top = root / name
        if not top.is_dir() or top.is_symlink():
            continue  # The archived member/parent checks reject changed types.
        for current, folders, files in os.walk(top, followlinks=False):
            directory = Path(current)
            folders[:] = [folder for folder in folders
                          if (directory / folder).relative_to(root).as_posix() not in native_outputs]
            for child in [*folders, *files]:
                entries += 1
                require(entries <= limit, "source input inventory exceeds bound")
                path = directory / child
                relative = path.relative_to(root)
                text = relative.as_posix()
                if text in names or text in directories:
                    continue
                require(not _source_redirected(path),
                          f"redirected source input: {text}")
                if path.is_dir():
                    continue  # Git does not record benign empty directories.
                # These are generated by the interpreter and setuptools in the
                # source tree. They never authorize extra Python input files.
                cache = "__pycache__" in relative.parts
                metadata = (len(relative.parts) >= 2
                            and relative.parts[0] == "src"
                            and relative.parts[1].endswith(".egg-info"))
                generated = ((cache and path.suffix == ".pyc")
                             or (metadata and path.suffix.casefold() not in executable_suffixes)
                             or (path.name == ".DS_Store" and path.is_file()))
                require(generated, f"unfrozen source input: {text}")


def verify_tracked_source(root, source_sha):
    """Compare actual tracked bytes, independently of Git's index/stat shortcuts."""
    raw = git_output(root, "ls-tree", "-rlz", "--full-tree", source_sha)
    records = raw.split(b"\0")
    require(records[-1] == b"" and 0 < len(records) - 1 <= MAX_TRACKED_SOURCE_FILES,
            "Tracked source inventory exceeds file bound")
    files, total, names = [], 0, set()
    for record in records[:-1]:
        header, separator, raw_name = record.partition(b"\t")
        fields = header.split()
        require(separator and len(fields) == 4
                and fields[0] in {b"100644", b"100755"} and fields[1] == b"blob"
                and re.fullmatch(rb"[0-9a-f]{40}", fields[2]) is not None
                and fields[3].isdigit(), "Unsupported tracked source type")
        name = raw_name.decode("utf-8")
        path = Path(name)
        require(0 < len(raw_name) <= 4096 and not path.is_absolute()
                and not path.drive and not PureWindowsPath(name).drive
                and path.as_posix() == name and ".." not in path.parts
                and "\\" not in name and name not in names,
                "Invalid tracked source path")
        names.add(name)
        size = int(fields[3])
        total += size
        require(size <= MAX_TRACKED_FILE_BYTES and total <= MAX_TRACKED_SOURCE_BYTES,
                "Tracked source exceeds byte bound")
        files.append((path, size, fields[2].decode("ascii")))
    for relative, size, expected in files:
        path = safe(root / relative)
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_size == size,
                "Canonical tracked source bytes differ")
        # Git blob IDs include this header. Executable bits are represented by
        # the canonical tree; Windows need not expose POSIX executable modes.
        checksum = hashlib.sha1(usedforsecurity=False)
        checksum.update(b"blob " + str(size).encode("ascii") + b"\0")
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            require((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino),
                    "Tracked source changed during inspection")
            remaining = size
            while remaining:
                data = stream.read(min(1024 * 1024, remaining))
                require(bool(data), "Canonical tracked source bytes differ")
                checksum.update(data)
                remaining -= len(data)
            require(not stream.read(1), "Canonical tracked source bytes differ")
        after = path.lstat()
        require((before.st_dev, before.st_ino, before.st_size,
                 before.st_mtime_ns, before.st_ctime_ns)
                == (after.st_dev, after.st_ino, after.st_size,
                    after.st_mtime_ns, after.st_ctime_ns)
                and checksum.hexdigest() == expected,
                "Canonical tracked source bytes differ")
    return names


def verify_pr_source(root, source_sha, base_sha, head_sha, *, tree_sha=None,
                     include_untracked=False):
    """Bind each PR observation to the same clean test-merge commit and tree."""
    def git(*command):
        return git_output(root, *command)

    observed_tree = git("rev-parse", "HEAD^{tree}").decode().strip()
    require(
        git("rev-parse", "HEAD").decode().strip() == source_sha
        and git("show", "-s", "--format=%P", source_sha).decode().split()
        == [base_sha, head_sha]
        and (tree_sha is None or observed_tree == tree_sha),
        "PR merge identity differs",
    )
    require(
        not git("status", "--porcelain",
                "--untracked-files=all" if include_untracked else "--untracked-files=no").strip(),
        "PR source is not clean" if include_untracked else "PR tracked source changed",
    )
    names = verify_tracked_source(root, source_sha)
    _verify_source_additions(root, names)
    return observed_tree


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
        return git_output(root, *command)

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
        source_tree = verify_pr_source(
            root, args.source_sha, base, head, include_untracked=True
        )
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
            verify_pr_source(root, args.source_sha, base, head, tree_sha=source_tree)

        unchanged()
        workflow = ".github/workflows/windows-measurement.yml"
        require(
            git("show", args.source_sha + ":" + workflow)
            == (root / workflow).read_bytes(),
            "PR workflow source differs",
        )
        source = {
            "mode": "pull-request",
            "tree": source_tree,
            "head_sha": head,
            "base_sha": base,
            "canonical_origin": remote,
            "workflow_blob": git("rev-parse", args.source_sha + ":" + workflow)
            .decode()
            .strip(),
        }
    workflow_sha, workflow_ref = workflow_identity(
        args.source_sha, frozen=args.frozen_identity is not None, environment=os.environ
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
    require(
        "llm_wiki_cli" not in sys.modules,
        "Canary controller imported a provider before measurement selection",
    )
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
    unchanged()
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
