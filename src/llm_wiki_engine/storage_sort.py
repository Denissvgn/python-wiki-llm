"""Bounded private merge runs for complete storage audits."""

from __future__ import annotations

from contextlib import ExitStack
import heapq
import json
from pathlib import Path
import tempfile

from .knowledge_storage import KnowledgeStorageError, canonical_bytes


class SortedRuns:
    """External merge sort with at most 32 input handles and fixed batch bytes."""

    def __init__(self, key=lambda row: row, *, batch_bytes=1_048_576,
                 record_bytes=1_048_576, disk_bytes=2_147_483_648):
        self._directory = tempfile.TemporaryDirectory(prefix="llm-wiki-sort-")
        self.key = key
        self.batch_limit, self.record_limit, self.disk_limit = batch_bytes, record_bytes, disk_bytes
        self.pending = []
        self.pending_bytes = self.written = self.count = 0
        self.paths: list[Path] = []
        self.sealed = False
        self._sequence = 0
        self._readers = set()

    def _path(self):
        self._sequence += 1
        return Path(self._directory.name) / str(self._sequence)

    def _write(self, stream, raw):
        self.written += len(raw)
        if self.written > self.disk_limit:
            raise KnowledgeStorageError("audit", "merge spill quota exhausted", code="storage-limit")
        stream.write(raw)

    def add(self, row):
        if self.sealed:
            raise ValueError("sorted runs already sealed")
        raw = canonical_bytes(row)
        if len(raw) > self.record_limit:
            raise KnowledgeStorageError("audit", "record exceeds streaming record limit", code="storage-limit")
        if self.pending and self.pending_bytes + len(raw) > self.batch_limit:
            self._flush()
        self.pending.append((self.key(row), raw))
        self.pending_bytes += len(raw)
        self.count += 1

    def _flush(self):
        if not self.pending:
            return
        path = self._path()
        self.pending.sort(key=lambda row: row[0])
        with path.open("wb") as stream:
            for _, raw in self.pending:
                self._write(stream, raw)
        self.paths.append(path)
        self.pending.clear()
        self.pending_bytes = 0

    def _lines(self, stream):
        while raw := stream.readline(self.record_limit + 1):
            if len(raw) > self.record_limit or not raw.endswith(b"\n"):
                raise KnowledgeStorageError("audit", "invalid private merge record")
            yield self.key(json.loads(raw)), raw

    def _merge(self, paths):
        with ExitStack() as stack:
            self._readers.add(stack)
            try:
                inputs = [self._lines(stack.enter_context(path.open("rb"))) for path in paths]
                yield from heapq.merge(*inputs, key=lambda row: row[0])
            finally:
                self._readers.discard(stack)

    def seal(self):
        if self.sealed:
            return
        self._flush()
        while len(self.paths) > 32:
            following = []
            for i in range(0, len(self.paths), 32):
                group = self.paths[i:i + 32]
                path = self._path()
                with path.open("wb") as stream:
                    for _, raw in self._merge(group):
                        self._write(stream, raw)
                following.append(path)
                for old in group:
                    old.unlink()
            self.paths = following
        self.sealed = True

    def __iter__(self):
        self.seal()
        for _, raw in self._merge(self.paths):
            yield json.loads(raw)

    def close(self):
        self.pending.clear()
        # Suspended consumers can still hold generators after an exception.
        # Release their handles before deleting runs, including on Windows.
        for stack in tuple(self._readers):
            stack.close()
        self._readers.clear()
        self._directory.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
