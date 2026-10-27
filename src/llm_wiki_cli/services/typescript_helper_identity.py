"""Bounded observations of the complete prepared TypeScript dependency tree."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat

from .filesystem_guard import fresh_no_follow_stat
from .io import first_unsafe_path_component
from .knowledge_storage_io import read_guarded
from .validation import is_portable_relative_path

MANIFEST_VERSION = 3
ARTIFACT_SCOPE = "typescript-node-modules/v1"
MAX_ENTRIES = 10_000
MAX_BYTES = 128 * 1024 * 1024
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_DEPTH = 32
MAX_RECEIPT_BYTES = 1024 * 1024


def read_receipt(path: Path):
    """Read bounded regular receipt bytes without following redirects."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("TypeScript receipt contains duplicate keys")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("TypeScript receipt contains a non-finite value")

    return json.loads(read_guarded(path, MAX_RECEIPT_BYTES).content,
                      object_pairs_hook=unique, parse_constant=invalid_constant)


def _identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns, value.st_nlink)


def _snapshot(root):
    pending = [root]
    result = {}
    total = 0
    while pending:
        path = pending.pop()
        relative = path.relative_to(root).as_posix()
        if relative != "." and (not is_portable_relative_path(relative)
                                or len(Path(relative).parts) > MAX_DEPTH):
            raise ValueError("TypeScript dependency path is unsafe or too deep")
        metadata = fresh_no_follow_stat(path)
        if (stat.S_ISLNK(metadata.st_mode)
                or getattr(metadata, "st_file_attributes", 0) & 0x400):
            raise ValueError("TypeScript dependencies must not contain links or reparse points")
        result[relative] = _identity(metadata)
        if len(result) > MAX_ENTRIES:
            raise ValueError("TypeScript dependency entry limit exceeded")
        if stat.S_ISDIR(metadata.st_mode):
            with os.scandir(path) as entries:
                for entry in entries:
                    if len(pending) + len(result) >= MAX_ENTRIES:
                        raise ValueError("TypeScript dependency entry limit exceeded")
                    pending.append(path / entry.name)
        elif stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1:
            total += metadata.st_size
            if metadata.st_size > MAX_FILE_BYTES or total > MAX_BYTES:
                raise ValueError("TypeScript dependency byte limit exceeded")
        else:
            raise ValueError("TypeScript dependencies require regular files and directories")
    return result


def dependency_fingerprint(node_modules: Path) -> str:
    """Hash all paths and regular bytes; refuse unsafe, oversized or changing trees.

    This observes cached bytes, not their authenticity or future immutability.
    Each file read pins its ancestors. A second bounded namespace observation
    rejects detected additions, removals, replacements and in-read mutations.
    """
    root = Path(os.path.abspath(node_modules))
    if first_unsafe_path_component(root) is not None:
        raise ValueError("TypeScript dependency root traverses an unsafe link")
    try:
        before = _snapshot(root)
        if not stat.S_ISDIR(before["."][2]):
            raise ValueError("TypeScript dependency root must be a directory")
        digest = hashlib.sha256(ARTIFACT_SCOPE.encode() + b"\0")
        remaining = MAX_BYTES
        for name in sorted(before):
            if name == ".":
                continue
            label = name.encode("utf-8")
            directory = stat.S_ISDIR(before[name][2])
            digest.update(b"d" if directory else b"f")
            digest.update(len(label).to_bytes(4, "big") + label)
            if not directory:
                content = read_guarded(root / name, min(MAX_FILE_BYTES, remaining)).content
                remaining -= len(content)
                digest.update(len(content).to_bytes(8, "big") + hashlib.sha256(content).digest())
        if before != _snapshot(root):
            raise ValueError("TypeScript dependencies changed during identity observation")
        return "sha256:" + digest.hexdigest()
    except (OSError, UnicodeError) as error:
        raise ValueError("TypeScript dependency identity is unavailable") from error


def execution_source_fingerprint(root: Path, names) -> str:
    """Retain the existing labeled source contract using guarded bounded reads."""
    digest = hashlib.sha256()
    for name in sorted(names):
        content = read_guarded(root / name, MAX_FILE_BYTES).content
        digest.update(name.encode("utf-8") + b"\0" + content + b"\0")
    return "sha256:" + digest.hexdigest()
