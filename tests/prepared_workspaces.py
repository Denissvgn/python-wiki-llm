"""Opt-in, process-local prepared fixtures with one exact root per input variant.

Only bytes are shared. Each lease restores fresh regular files, and every test
continues through the real consumer/validator. Failed roots are quarantined
before the next lease instead of being overwritten by another test.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
from typing import Callable

import pytest

ENVIRONMENT = "LLM_WIKI_TEST_PREPARED_WORKSPACES"
MAX_BYTES = 32 * 1024 * 1024
MAX_FILES = 10_000


def _check_path(root: Path) -> None:
    for path in (root, *root.parents):
        if path.is_symlink() or path.exists() and getattr(path.lstat(), "st_file_attributes", 0) & 0x400:
            raise ValueError("prepared workspace path was redirected")


def _snapshot(root: Path) -> tuple[dict[str, tuple[bytes, int]], dict[str, int]]:
    _check_path(root)
    result, directories = {}, {}
    total = 0
    for index, path in enumerate(sorted(root.rglob("*"))):
        if index >= MAX_FILES:
            raise ValueError("prepared fixture exceeds its entry budget")
        metadata = path.lstat()
        if path.is_symlink() or getattr(metadata, "st_file_attributes", 0) & 0x400:
            raise ValueError("prepared fixtures cannot contain redirected paths")
        if path.is_dir():
            directories[path.relative_to(root).as_posix()] = stat.S_IMODE(metadata.st_mode)
            continue
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError("prepared fixtures require regular single-link files")
        raw = path.read_bytes()
        total += len(raw)
        if len(result) >= MAX_FILES or total > MAX_BYTES:
            raise ValueError("prepared fixture exceeds its byte/file budget")
        result[path.relative_to(root).as_posix()] = (raw, stat.S_IMODE(metadata.st_mode))
    return result, directories


def _remove(root: Path) -> None:
    _check_path(root)
    if root.is_symlink() or getattr(root.lstat(), "st_file_attributes", 0) & 0x400:
        raise ValueError("prepared workspace root was redirected")
    def writable(function, path, _error):
        # Windows can retain a test-owned read-only leaf after a rejection case.
        if Path(path).is_symlink():
            raise ValueError("cleanup refuses a redirected failed operation")
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        function(path)
    shutil.rmtree(root, onerror=writable)


@dataclass
class Lease:
    pool: Pool
    key: str
    root: Path
    failed: Callable[[], bool]
    active: bool = True
    populated: bool = False

    def populate(self, builder: Callable[[Path], object]) -> Path:
        _check_path(self.root)
        if not self.active or self.populated or any(self.root.iterdir()):
            raise ValueError("prepared fixture lease is closed or already occupied")
        self.populated = True
        image = self.pool.images.get(self.key)
        if image is None or not self.pool.enabled:
            metadata = builder(self.root)
            image = _snapshot(self.root)
            self.pool.builds[self.key] = self.pool.builds.get(self.key, 0) + 1
            if self.pool.enabled:
                self.pool.images[self.key] = image
                if isinstance(metadata, dict):
                    self.pool.metadata[self.key] = json.loads(json.dumps(metadata, allow_nan=False))
        else:
            self.pool.restores[self.key] = self.pool.restores.get(self.key, 0) + 1
            files, directories = image
            for name in sorted(directories, key=lambda p: (p.count("/"), p)):
                (self.root / name).mkdir(parents=True, exist_ok=True)
            for name, (raw, mode) in files.items():
                path = self.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                path.chmod(mode)
            for name, mode in directories.items():
                (self.root / name).chmod(mode)
            if _snapshot(self.root) != image:
                raise ValueError("restored prepared fixture differs from its original complete image")
        return self.root

    @property
    def metadata(self):
        return json.loads(json.dumps(self.pool.metadata.get(self.key, {})))


class Pool:
    def __init__(self, root: Path, *, enabled: bool):
        self.root = root
        self.enabled = enabled
        self.leases: dict[str, Lease] = {}
        self.images: dict[str, tuple[dict[str, tuple[bytes, int]], dict[str, int]]] = {}
        self.metadata: dict[str, dict] = {}
        self.builds: dict[str, int] = {}
        self.restores: dict[str, int] = {}
        self.failures: list[Path] = []

    def reserve(self, key: str, *, failed: Callable[[], bool] = lambda: False) -> Lease:
        _check_path(self.root)
        if not key or len(key) > 256:
            raise ValueError("invalid prepared fixture key")
        old = self.leases.get(key)
        if old is not None and old.active:
            raise ValueError("another test still owns the prepared workspace")
        folder = hashlib.sha256(key.encode()).hexdigest()
        root = self.root / folder
        if root.exists() or root.is_symlink():
            if root.is_symlink() or getattr(root.lstat(), "st_file_attributes", 0) & 0x400:
                raise ValueError("prepared workspace root was redirected")
            if old is not None and old.failed():
                destination = self.root / (folder + ".failed-" + str(len(self.failures)))
                root.rename(destination)
                self.failures.append(destination)
            else:
                _remove(root)
        root.mkdir()
        lease = Lease(self, key, root, failed)
        self.leases[key] = lease
        return lease


@pytest.fixture(scope="session", autouse=True)
def _prepared_workspace_pool(tmp_path_factory):
    value = os.environ.get(ENVIRONMENT, "0")
    if value not in {"0", "1"}:
        raise ValueError(ENVIRONMENT + " must be 0 or 1")
    pool = Pool(tmp_path_factory.mktemp("prepared-workspaces"), enabled=value == "1")
    yield pool
    report = os.environ.get("LLM_WIKI_TEST_PREPARED_WORKSPACE_REPORT")
    if report and os.environ.get("LLM_WIKI_TEST_PREPARED_REPORT_PID") == str(os.getpid()):
        path = Path(report)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            json.dump({"schema_version": "llm-wiki-prepared-test-workspaces/v1", "qualifying": False,
                       "enabled": pool.enabled, "builds": pool.builds, "restores": pool.restores,
                       "quarantined_failures": len(pool.failures), "shared_mutable_files": False}, stream, sort_keys=True)
            stream.write("\n")


@pytest.fixture
def prepared_workspace(_prepared_workspace_pool, request):
    pool = _prepared_workspace_pool
    failures_before = request.session.testsfailed
    leases = []
    class Factory:
        enabled = pool.enabled
        def __call__(self, key):
            lease = pool.reserve(key, failed=lambda: request.session.testsfailed > failures_before)
            leases.append(lease)
            return lease
    try:
        yield Factory()
    finally:
        for lease in leases:
            lease.active = False
