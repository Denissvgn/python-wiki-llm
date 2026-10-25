#!/usr/bin/env python3
"""Preview an exact release capture; apply only a matching caller-approved preview."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 source-check environments.
    import tomli as tomllib


SCHEMA = "agent-wiki-reviewed-capture-preview/v1"
WIKI = "docs/llm_wiki"
MAX_LOG_BYTES = 16 * 1024 * 1024


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(root: Path, *arguments: str) -> bytes:
    return subprocess.check_output(["git", *arguments], cwd=root, timeout=60)


def status(root: Path, *paths: str) -> bytes:
    return git(root, "status", "--porcelain=v1", "--untracked-files=all",
               "--ignore-submodules=none", *(('--', *paths) if paths else ()))


def context(root: Path) -> dict:
    """Use the maintained helper readiness check, including actual cached bytes."""
    sys.path.insert(0, str(root))
    import llm_wiki_cli
    from release import preflight

    versions = {
        name: subprocess.check_output([name, "--version"], text=True, timeout=60).strip()
        for name in ("node", "npm")
    }
    helper = preflight._helper(
        root, {"tools": {name: {"version": value} for name, value in versions.items()}}
    )
    require(helper["status"] == "ready", "selected TypeScript helper is not ready")
    version = importlib.metadata.version("agent-wiki-cli")
    require(version == tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"],
            "installed version differs from the candidate")
    package = Path(llm_wiki_cli.__file__).parent
    files = {}
    for path in sorted(package.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            require(not path.is_symlink(), "installed package contains a symlink")
            relative = path.relative_to(package)
            raw = path.read_bytes()
            require(raw == (root / "src/llm_wiki_cli" / relative).read_bytes(),
                    "installed package differs from the candidate")
            files[relative.as_posix()] = digest(raw)
    require(bool(files), "installed package is empty")
    return {
        "source_sha": git(root, "rev-parse", "HEAD").decode().strip(),
        "source_tree": git(root, "rev-parse", "HEAD^{tree}").decode().strip(),
        "wiki_tree": git(root, "rev-parse", f"HEAD:{WIKI}").decode().strip(),
        "python": sys.version,
        "python_implementation": {
            "name": sys.implementation.name, "cache_tag": sys.implementation.cache_tag,
            "abi_flags": getattr(sys, "abiflags", ""), "flags": list(sys.flags),
            "byteorder": sys.byteorder,
        },
        "platform": [platform.system(), platform.machine()],
        "version": version,
        "package_files_sha256": digest(canonical(files)),
        "helper": helper,
        "tool_versions": versions,
    }


def run_sync(root: Path, evidence: Path, *, dry_run: bool) -> subprocess.CompletedProcess:
    argv = [sys.executable, "-I", "-m", "llm_wiki_cli.cli", "sync",
            "--src-dir", ".", "--wiki-dir", WIKI,
            "--helper-cache-dir", str(root / ".git"),
            "--cache-dir", str(evidence / "inventory"),
            "--jobs", "1", "--no-plugins", "--progress", "never",
            "--dry-run" if dry_run else "--force"]
    return subprocess.run(argv, cwd=root, capture_output=True, timeout=1800)


def write(path: Path, raw: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(raw)


def capture(root: Path, evidence: Path, *, operation: str, candidate: str,
            approved: str | None, run_id: int, attempt: int) -> dict:
    require(re.fullmatch(r"[0-9a-f]{40}", candidate) is not None, "invalid candidate SHA")
    require(operation in {"preview", "apply"}, "unsupported operation")
    require(run_id > 0 and attempt > 0, "invalid run identity")
    require(Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root.resolve(),
            "capture must run from the repository root")
    require(git(root, "rev-parse", "HEAD").decode().strip() == candidate, "candidate changed")
    require(not status(root), "source worktree must be clean")
    require(not evidence.is_relative_to(root), "evidence must be outside source")
    require(not evidence.exists() and not evidence.is_symlink(), "occupied evidence directory")
    if operation == "apply":
        require(isinstance(approved, str) and re.fullmatch(r"[0-9a-f]{64}", approved) is not None,
                "apply requires the reviewed preview SHA-256")
    else:
        require(not approved, "preview does not accept approval")
    observed = context(root)
    require(observed["source_sha"] == candidate, "source changed during context capture")
    evidence.mkdir(mode=0o700)
    preview = run_sync(root, evidence, dry_run=True)
    require(len(preview.stdout) <= MAX_LOG_BYTES and len(preview.stderr) <= MAX_LOG_BYTES,
            "preview output exceeds bound")
    write(evidence / "preview.stdout", preview.stdout)
    write(evidence / "preview.stderr", preview.stderr)
    require(preview.returncode == 0, "preview failed; original output retained")
    require(b"Sync dry-run plan:" in preview.stdout and
            b"DRY-RUN: no files modified." in preview.stdout, "incomplete preview")
    require(not status(root), "preview changed the source worktree")
    require(context(root) == observed, "source, installed provider or helper changed during preview")
    preview_hash = digest(canonical(observed) + b"\n" + preview.stdout)
    record = {
        "schema_version": SCHEMA, "operation": operation, "candidate_sha": candidate,
        "workflow_run_id": run_id, "run_attempt": attempt, "context": observed,
        "preview_stdout_sha256": digest(preview.stdout), "preview_sha256": preview_hash,
        "approved_preview_sha256": approved,
        "qualification": "Preview and caller-supplied hash only; not independent review, policy approval or release proof.",
    }
    write(evidence / "preview.json", json.dumps(record, indent=2, sort_keys=True).encode() + b"\n")
    if operation == "preview":
        return {"status": "previewed", "preview_sha256": preview_hash, "writer_succeeded": False}
    require(preview_hash == approved, "reviewed preview differs; no writer was invoked")
    require(not status(root), "source worktree changed before apply")
    before = status(root, WIKI)
    result = run_sync(root, evidence, dry_run=False)
    require(len(result.stdout) + len(result.stderr) <= MAX_LOG_BYTES, "sync output exceeds bound")
    write(evidence / "sync.stdout", result.stdout)
    write(evidence / "sync.stderr", result.stderr)
    scoped, whole = status(root, WIKI), status(root)
    patch = git(root, "diff", "--no-ext-diff", "--no-textconv", "--binary",
                "--full-index", "--no-color", "HEAD", "--", WIKI)
    payloads = {"wiki-status-before.txt": before, "wiki-status-after.txt": scoped,
                "worktree-status-after.txt": whole, "wiki-diff.patch": patch,
                "sync.log": result.stdout + result.stderr}
    for name, raw in payloads.items():
        write(evidence / name, raw)
    scoped_only = scoped == whole
    convergence = {
        "schema_version": "llm-wiki-convergence/v1", "candidate_sha": candidate,
        "wiki_dir": WIKI, "decision": "PASS" if result.returncode == 0 and not whole else "FAIL",
        "sync": {"started": True, "exit_code": result.returncode, "plugins_enabled": False},
        "captures": {"wiki_diff": {"exit_code": 0}},
        "checks": {"pre_sync_status_available": True, "pre_sync_wiki_clean": not before,
                   "pre_sync_worktree_clean": True, "post_sync_status_available": True,
                   "post_sync_diff_available": True, "post_sync_wiki_clean": not scoped,
                   "worktree_changes_scoped_to_wiki": scoped_only},
        "evidence": {name: {"filename": name, "bytes": len(raw),
                            "records": len(raw.splitlines()), "sha256": digest(raw)}
                     for name, raw in payloads.items()},
    }
    write(evidence / "convergence-result.json",
          json.dumps(convergence, indent=2, sort_keys=True).encode() + b"\n")
    require(result.returncode == 0 and scoped_only, "writer failed or changed files outside the wiki")
    return {"status": "unchanged" if not whole else "drift", "preview_sha256": preview_hash,
            "writer_succeeded": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=("preview", "apply"), required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--approved-preview-sha256")
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        require(os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and
                os.environ.get("GITHUB_REF") == "refs/heads/main" and
                os.environ.get("GITHUB_REPOSITORY") == "Denissvgn/python-wiki-llm",
                "manual main dispatch in the maintained repository required")
        require(args.candidate_sha == os.environ.get("GITHUB_SHA"), "dispatch candidate differs")
        root = Path.cwd().resolve()
        evidence = args.evidence_dir.absolute()
        expected = Path(os.environ["RUNNER_TEMP"]).resolve() / "reviewed-wiki-capture"
        require(evidence == expected and not evidence.is_symlink(), "unexpected evidence destination")
        result = capture(root, evidence, operation=args.operation, candidate=args.candidate_sha,
                         approved=args.approved_preview_sha256,
                         run_id=int(os.environ["GITHUB_RUN_ID"]),
                         attempt=int(os.environ["GITHUB_RUN_ATTEMPT"]))
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
            stream.write(f"writer-succeeded={str(result['writer_succeeded']).lower()}\n")
        print(json.dumps(result, sort_keys=True))
        return 1 if result["status"] == "drift" else 0
    except (ValueError, OSError, subprocess.SubprocessError, KeyError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
