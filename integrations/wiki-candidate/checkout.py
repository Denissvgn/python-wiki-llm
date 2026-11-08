"""Bind a local candidate action to the consumer checkout and accepted inputs."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.knowledge_storage_io import read_guarded
from llm_wiki_cli.services.publication_candidate import MAX_FILE_BYTES, _read_tree
from llm_wiki_cli.services.publication_config import (
    DELIVERY_CHECKPOINT_PATH,
    _relative_path,
    publication_control_overlap,
    publication_path,
)
from llm_wiki_cli.services.publication_impact import MAX_JSON_BYTES


def _git(directory: Path, *args: str) -> bytes:
    return subprocess.check_output(
        [
            "git",
            "--no-replace-objects",
            "--literal-pathspecs",
            "-c",
            "core.fsmonitor=false",
            "-C",
            str(directory),
            *args,
        ],
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )


def _revision(value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", value):
        raise ValueError("Expected a full lowercase Git commit ID")
    return value


def _repository(directory: Path) -> Path:
    return Path(
        os.fsdecode(_git(directory, "rev-parse", "--show-toplevel").rstrip(b"\n"))
    ).resolve()


def _clean(directory: Path, separate_target: Path | None = None) -> None:
    # ls-files --others includes ignored files. These can still be explicitly
    # mapped in a publication config and would otherwise lack a source revision.
    if _git(
        directory,
        "diff",
        "--no-ext-diff",
        "--ignore-submodules=none",
        "--name-only",
        "-z",
        "HEAD",
        "--",
        ".",
    ):
        raise ValueError("Candidate sources must match the checked-out commit")
    for name in _git(directory, "ls-files", "--others", "-z", "--", ".").split(b"\0"):
        if not name:
            continue
        path = directory / os.fsdecode(name)
        if separate_target is None or not path.is_relative_to(separate_target):
            raise ValueError(
                "Untracked or ignored files are present in the consumer checkout"
            )
    # Git does not enumerate ignored files inside tracked gitlinks from their
    # parent. A mapped source may live there, so bind populated submodules to
    # the recorded commit and check their worktrees under the same policy.
    for row in _git(directory, "ls-files", "--stage", "-z", "--", ".").split(b"\0"):
        if not row.startswith(b"160000 "):
            continue
        metadata, name = row.split(b"\t", 1)
        path = publication_path(directory, os.fsdecode(name))
        if not path.exists() or (path.is_dir() and not any(path.iterdir())):
            continue
        if (
            not path.is_dir()
            or _repository(path) != path
            or _git(path, "rev-parse", "HEAD").strip() != metadata.split()[1]
        ):
            raise ValueError("Populated submodule differs from its recorded Git revision")
        _clean(path, separate_target)


def _verify_target_blobs(
    target: Path, pin: str, receipt_files: dict[str, str] | None
) -> None:
    """Bind the public bytes used by the exporter to the unfiltered Git tree."""
    files = _read_tree(target, target_snapshot=True)
    if (
        receipt_files is not None
        and {path: sha256_bytes(raw) for path, raw in files.items()} != receipt_files
    ):
        raise ValueError("Target bytes changed since the candidate was checked")
    # The private checkpoint participates in the Git revision but is excluded
    # from the public candidate and receipt inventory.
    marker = target / DELIVERY_CHECKPOINT_PATH
    if marker.exists():
        files[DELIVERY_CHECKPOINT_PATH] = read_guarded(marker, MAX_FILE_BYTES).content
    algorithm = "sha256" if len(pin) == 64 else "sha1"
    for entry in _git(target, "ls-tree", "-rz", "--full-tree", pin).split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, kind, expected = metadata.split()
        path = name.decode("utf-8")
        if kind != b"blob" or mode not in {b"100644", b"100755"} or path not in files:
            raise ValueError(
                f"Pinned target requires a complete checkout of regular files: {path}"
            )
        raw = files.pop(path)
        blob = hashlib.new(
            algorithm, f"blob {len(raw)}\0".encode("ascii"), usedforsecurity=False
        )
        blob.update(raw)
        if blob.hexdigest() != expected.decode("ascii"):
            raise ValueError(
                f"Target checkout bytes differ from the pinned Git blob: {path}. "
                "Use a fresh checkout without line-ending conversion or checkout filters."
            )
    if files:
        raise ValueError("Target contains files outside its pinned Git tree")


def verified_target(
    consumer: Path,
    target_dir: str,
    target_revision: str,
    *,
    receipt_files: dict[str, str] | None = None,
) -> str | None:
    if not target_dir:
        if target_revision:
            raise ValueError("target-revision requires a local target-dir")
        return None
    target = publication_path(consumer, target_dir)
    if not target.is_dir() or target == consumer:
        raise ValueError("target-dir must be a separate local directory")
    if _repository(target) != target:
        if target_revision:
            raise ValueError(
                "An independent target-revision requires a separate Git checkout"
            )
        return None
    head = _revision(_git(target, "rev-parse", "HEAD").decode().strip())
    if target_revision and _revision(target_revision) != head:
        raise ValueError("Target checkout differs from target-revision")
    _clean(target)
    _verify_target_blobs(target, head, receipt_files)
    return head


def committed_blob(
    root: Path, pin: str, relative: str, maximum: int
) -> tuple[str, bytes]:
    """Read one regular blob from a pinned commit, without checking out or filtering it."""
    if _git(root, "cat-file", "-t", _revision(pin)).strip() != b"commit":
        raise ValueError("Accepted state requires an available Git commit")
    entry = _git(root, "ls-tree", "-z", pin, "--", relative)
    metadata, _, listed = entry.partition(b"\t")
    mode, _, rest = metadata.partition(b" ")
    if (
        listed != relative.encode("utf-8") + b"\0"
        or mode not in {b"100644", b"100755"}
        or not rest.startswith(b"blob ")
    ):
        raise ValueError(f"Accepted input must be a regular file at {pin}: {relative}")
    oid = rest.split()[1].decode("ascii")
    if int(_git(root, "cat-file", "-s", oid)) > maximum:
        raise ValueError(
            f"Accepted input exceeds the publication document limit: {relative}"
        )
    return oid, _git(root, "cat-file", "blob", oid)


def verified_checkout(
    consumer: Path, source_revision: str, target_dir: str, accepted: dict[str, str]
) -> str:
    consumer = consumer.resolve(strict=True)
    root = _repository(consumer)
    head = _revision(_git(consumer, "rev-parse", "HEAD").decode().strip())
    if source_revision and _revision(source_revision) != head:
        raise ValueError("Source checkout differs from source-revision")
    separate_target = None
    if target_dir:
        target = publication_path(consumer, target_dir)
        if _repository(target) == target and target != root:
            separate_target = target
            _clean(target)
    _clean(consumer, separate_target)

    for path in accepted.values():
        # This coordinate belongs to the accepted revision. A proposal can
        # rename it even on a case-insensitive filesystem.
        configured = consumer / _relative_path(path, "accepted input")
        if target_dir and publication_control_overlap(configured, target):
            raise ValueError(
                "Accepted metadata must stay outside the public target copy"
            )
    return head


def accepted_inputs(
    consumer: Path, accepted: dict[str, str], revision: str, runtime: Path,
    *, workspace: Path | None = None,
) -> tuple[dict[str, str], str | None]:
    """Read explicitly accepted metadata from Git, independently of the source commit."""
    if not accepted:
        return {}, None
    root = _repository(consumer)
    if os.environ.get("GITHUB_EVENT_NAME") in {"pull_request", "pull_request_target"}:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_bytes())
        base = _revision(event["pull_request"]["base"]["sha"])
        if revision and _revision(revision) != base:
            raise ValueError("Pull request review state must come from its base commit")
        revision = base
    pin = _revision(revision or _git(root, "rev-parse", "HEAD").decode().strip())
    directory = runtime / "accepted-inputs"
    directory.mkdir(mode=0o700)
    paths = {}
    records = {}
    for option, path in accepted.items():
        if option not in {
            "baseline",
            "reviews",
            "previous-receipt",
            "candidate-review",
        }:
            raise ValueError("Unknown accepted artifact type")
        input_root = root
        if workspace is not None and Path(path).is_absolute():
            # The impact action also accepts an independent base checkout.
            # Read the committed blob there, regardless of its working bytes.
            supplied = Path(path)
            boundary = workspace.resolve(strict=True)
            if ".." in supplied.parts or not supplied.is_relative_to(boundary):
                raise ValueError("Accepted Git input must stay inside the Actions workspace")
            if not supplied.is_relative_to(root):
                input_root = _repository(supplied.parent)
                if not input_root.is_relative_to(boundary):
                    raise ValueError("Accepted checkout must stay inside the Actions workspace")
            relative = _relative_path(supplied.relative_to(input_root).as_posix(), "accepted input")
        else:
            relative = (
                consumer.relative_to(root) / _relative_path(path, "accepted input")
            ).as_posix()
        oid, raw = committed_blob(input_root, pin, relative, MAX_JSON_BYTES)
        destination = directory / (option + ".json")
        destination.write_bytes(raw)
        paths[option] = str(destination)
        records[option] = {
            "path": relative,
            "git_blob": oid,
            "sha256": sha256_bytes(raw),
        }
    (runtime / "evidence" / "accepted-state.json").write_text(
        json.dumps({"revision": pin, "files": records}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return paths, pin
