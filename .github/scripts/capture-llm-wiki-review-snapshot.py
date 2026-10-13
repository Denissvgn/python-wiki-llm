"""Retain a complete, bounded writer-owned wiki for independent review."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tarfile

MAX_CONTENT_BYTES = 512 * 1024 * 1024
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_FILES = 20_000
MAX_ARCHIVE_BYTES = 600 * 1024 * 1024
PATH_DESCRIPTOR_CTIME_COMPARABLE = os.name != "nt"


def identity(value, *, include_ctime=True):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_mtime_ns,
            value.st_ctime_ns if include_ctime else None)


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(
        ["git", "-c", "core.quotePath=true", *args], cwd=root,
        env={**os.environ, "LC_ALL": "C"},
    )


def capture(root: Path, evidence: Path, candidate: str, run_id: int, attempt: int) -> dict:
    root = root.resolve(strict=True)
    evidence = evidence.resolve(strict=True)
    if evidence.is_relative_to(root) or run_id <= 0 or attempt <= 0:
        raise ValueError("evidence must be outside source with a positive run identity")
    if git(root, "rev-parse", "HEAD").decode().strip() != candidate:
        raise ValueError("candidate differs from the checked-out source")
    result_path = evidence / "convergence-result.json"
    if result_path.is_symlink() or result_path.stat().st_size > 64 * 1024:
        raise ValueError("convergence result is unsafe or oversized")
    result = json.loads(result_path.read_bytes())
    required_checks = (
        "pre_sync_status_available", "pre_sync_wiki_clean", "pre_sync_worktree_clean",
        "post_sync_status_available", "post_sync_diff_available", "worktree_changes_scoped_to_wiki",
    )
    if (result.get("schema_version") != "llm-wiki-convergence/v1"
            or result.get("candidate_sha") != candidate
            or result.get("sync") != {"exit_code": 0, "plugins_enabled": False, "started": True}
            or not all(result.get("checks", {}).get(k) is True for k in required_checks)):
        raise ValueError("successful scoped convergence evidence is required")
    wiki = PurePosixPath(result["wiki_dir"])
    if wiki.is_absolute() or str(wiki) != result["wiki_dir"] or str(wiki) in {".", ""} or ".." in wiki.parts or "\\" in str(wiki):
        raise ValueError("wiki must be a canonical repository-relative directory")
    expected_evidence = {"wiki-status-before.txt", "wiki-status-after.txt", "worktree-status-after.txt", "wiki-diff.patch", "sync.log"}
    if set(result["evidence"]) != expected_evidence:
        raise ValueError("complete convergence evidence is required")
    for name, record in result["evidence"].items():
        if name not in {"wiki-status-before.txt", "wiki-status-after.txt", "worktree-status-after.txt", "wiki-diff.patch", "sync.log"}:
            raise ValueError("unexpected convergence evidence")
        path = evidence / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_ARCHIVE_BYTES:
            raise ValueError("unsafe convergence evidence")
        raw = path.read_bytes()
        if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("convergence evidence changed")
    status_args = ("status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none")
    if git(root, *status_args) != (evidence / "worktree-status-after.txt").read_bytes():
        raise ValueError("worktree changed after convergence")
    if git(root, *status_args, "--", str(wiki)) != (evidence / "wiki-status-after.txt").read_bytes():
        raise ValueError("wiki changed after convergence")
    changed = git(root, "diff", "--no-renames", "--name-only", "-z", "HEAD").split(b"\0")
    changed += git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    for spelling in filter(None, changed):
        PurePosixPath(spelling.decode("utf-8")).relative_to(wiki)
    paths = set(git(root, "ls-files", "-z", "--cached", "--", str(wiki)).split(b"\0"))
    paths.update(git(root, "ls-files", "-z", "--others", "--exclude-standard", "--", str(wiki)).split(b"\0"))
    paths.discard(b"")
    if len(paths) > MAX_FILES:
        raise ValueError("wiki file inventory exceeds the bound")
    entries, total = [], 0
    for spelling in sorted(paths):
        relative = PurePosixPath(spelling.decode("utf-8"))
        member = relative.relative_to(wiki)
        if ".." in relative.parts or not member.parts or "\\" in str(member):
            raise ValueError("unsafe wiki member")
        path = root.joinpath(*relative.parts)
        if not path.exists() and not path.is_symlink():
            continue  # Tracked removals are absent from the complete snapshot.
        for ancestor in (path, *path.parents):
            if ancestor == root:
                break
            if ancestor.is_symlink():
                raise ValueError("wiki members must not traverse symbolic links")
        observed = path.lstat()
        if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1 or observed.st_size > MAX_FILE_BYTES:
            raise ValueError("wiki member is not one bounded regular file")
        total += observed.st_size
        if total > MAX_CONTENT_BYTES:
            raise ValueError("wiki contents exceed the bound")
        entries.append((path, member.as_posix(), observed))
    archive = evidence / "wiki-review-snapshot.tar"
    manifest = evidence / "wiki-review-snapshot.json"
    if archive.exists() or archive.is_symlink() or manifest.exists() or manifest.is_symlink():
        raise ValueError("snapshot outputs are already occupied")
    records = []
    archive_owned = manifest_owned = False
    epoch = int(git(root, "show", "-s", "--format=%ct", "HEAD"))
    try:
        output = archive.open("xb")
        archive_owned = True
        with output, tarfile.open(fileobj=output, mode="w") as bundle:
            for path, member, observed in entries:
                descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
                with os.fdopen(descriptor, "rb") as stream:
                    opened = os.fstat(stream.fileno())
                    # Windows 3.13 lstat reports creation time as ctime;
                    # fstat reports metadata-change time. Keep strict ctime
                    # comparisons within each API below, rather than comparing
                    # those two different meanings across APIs.
                    comparable = PATH_DESCRIPTOR_CTIME_COMPARABLE
                    if identity(opened, include_ctime=comparable) != identity(observed, include_ctime=comparable):
                        raise ValueError("wiki member changed before capture")
                    raw = stream.read(observed.st_size + 1)
                    after = os.fstat(stream.fileno())
                if len(raw) != observed.st_size or identity(after) != identity(opened) or identity(path.lstat()) != identity(observed):
                    raise ValueError("wiki member changed during capture")
                item = tarfile.TarInfo(member)
                item.size, item.mode, item.mtime = len(raw), stat.S_IMODE(observed.st_mode), epoch
                bundle.addfile(item, io.BytesIO(raw))
                records.append({"path": member, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "mode": item.mode})
        if archive.stat().st_size > MAX_ARCHIVE_BYTES:
            raise ValueError("snapshot archive exceeds the bound")
        if git(root, *status_args) != (evidence / "worktree-status-after.txt").read_bytes():
            raise ValueError("worktree changed during capture")
        digest = hashlib.sha256()
        with archive.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        checksum = digest.hexdigest()
        payload = {
            "schema_version": "llm-wiki-review-snapshot/v1", "candidate_sha": candidate,
            "candidate_tree": git(root, "rev-parse", "HEAD^{tree}").decode().strip(),
            "workflow_run_id": run_id, "run_attempt": attempt, "wiki_dir": str(wiki),
            "archive": {"filename": archive.name, "bytes": archive.stat().st_size, "sha256": checksum},
            "entries": records, "content_bytes": total,
            "limits": {"files": MAX_FILES, "file_bytes": MAX_FILE_BYTES, "content_bytes": MAX_CONTENT_BYTES, "archive_bytes": MAX_ARCHIVE_BYTES},
            "qualification": "Complete Git-eligible writer output for review; not release approval or promotion evidence.",
        }
        output = manifest.open("x", encoding="utf-8", newline="\n")
        manifest_owned = True
        with output:
            json.dump(payload, output, indent=2, sort_keys=True)
            output.write("\n")
        return payload
    except BaseException:
        if archive_owned:
            archive.unlink(missing_ok=True)
        if manifest_owned:
            manifest.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    result = capture(args.root, args.evidence_dir, args.candidate_sha, args.run_id, args.attempt)
    print(json.dumps({"files": len(result["entries"]), "bytes": result["content_bytes"], "archive_sha256": result["archive"]["sha256"]}))


if __name__ == "__main__":
    main()
