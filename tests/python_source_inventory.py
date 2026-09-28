"""Content-bound Python inputs owned by one static-analysis consumer.

Each context is single-use. ASTs can be shared by that consumer's helpers, but
are never shared between checks. Revalidation prevents a changed input set from
producing a stale pass, including edits whose timestamps have been preserved.
"""

from __future__ import annotations

import ast
from collections import OrderedDict, deque
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Iterable

_SHARED_NODE_TYPES = frozenset(
    kind
    for base in (ast.operator, ast.unaryop, ast.boolop, ast.cmpop, ast.expr_context)
    for kind in base.__subclasses__()
)


def _owned_nodes(tree: ast.Module) -> tuple[ast.AST, ...]:
    """Keep ast.walk ordering while detaching CPython's shared leaf nodes."""
    leaves: dict[type[ast.AST], ast.AST] = {}
    nodes = []
    pending: deque[ast.AST] = deque([tree])
    while pending:
        node = pending.popleft()
        nodes.append(node)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for index, child in enumerate(value):
                    if isinstance(child, ast.AST):
                        kind = type(child)
                        if kind in _SHARED_NODE_TYPES:
                            if kind not in leaves:
                                leaves[kind] = kind()
                            child = value[index] = leaves[kind]
                        pending.append(child)
            elif isinstance(value, ast.AST):
                kind = type(value)
                if kind in _SHARED_NODE_TYPES:
                    if kind not in leaves:
                        leaves[kind] = kind()
                    value = leaves[kind]
                    setattr(node, field, value)
                pending.append(value)
    return tuple(nodes)


@dataclass(frozen=True)
class ParsedSource:
    tree: ast.Module
    nodes: tuple[ast.AST, ...]


class PythonSourceInventory:
    """A fresh source snapshot with bounded, consumer-owned parse reuse."""

    def __init__(
        self,
        roots: Iterable[Path],
        *,
        candidate: str | None = None,
        max_source_bytes: int = 8 * 1024 * 1024,
        max_ast_nodes: int = 120_000,
        max_cached_files: int = 128,
    ) -> None:
        if not all(
            type(value) is int and value >= 0
            for value in (max_source_bytes, max_ast_nodes, max_cached_files)
        ):
            raise ValueError("source inventory budgets must be nonnegative")
        self.roots = tuple(roots)
        self.candidate = candidate or os.environ.get("GITHUB_SHA", "working-tree")
        self.max_source_bytes = max_source_bytes
        self.max_ast_nodes = max_ast_nodes
        self.max_cached_files = max_cached_files
        self.paths: tuple[Path, ...] = ()
        self.identity = ""
        self._state = "new"
        self._digests: dict[str, str] = {}
        self._raw: OrderedDict[str, bytes] = OrderedDict()
        self._parsed: OrderedDict[str, ParsedSource] = OrderedDict()
        self._source_bytes = 0
        self._ast_nodes = 0
        self.stats = {
            "source_reads": 0,
            "parse_calls": 0,
            "parse_hits": 0,
            "peak_source_bytes": 0,
            "peak_ast_nodes": 0,
        }

    def _files(self) -> tuple[Path, ...]:
        for root in self.roots:
            if not root.is_dir():
                raise AssertionError(f"Python source root is unavailable: {root}")
        # Path equality is case-folded on Windows, even for a case-sensitive
        # directory. Preserve distinct lexical file names and diagnostics.
        paths = {str(path): path for root in self.roots for path in root.rglob("*.py")}
        return tuple(paths[name] for name in sorted(paths))

    def _read(self, path: Path) -> bytes:
        self.stats["source_reads"] += 1
        return path.read_bytes()

    def _retain_source(self, path: Path, raw: bytes) -> None:
        if len(raw) > self.max_source_bytes or self.max_cached_files == 0:
            return
        while (
            self._source_bytes + len(raw) > self.max_source_bytes
            or len(self._raw) >= self.max_cached_files
        ):
            _, discarded = self._raw.popitem(last=False)
            self._source_bytes -= len(discarded)
        self._raw[str(path)] = raw
        self._source_bytes += len(raw)
        self.stats["peak_source_bytes"] = max(
            self.stats["peak_source_bytes"], self._source_bytes
        )

    def __enter__(self) -> PythonSourceInventory:
        if self._state != "new":
            raise RuntimeError("a Python source inventory has only one consumer")
        self._state = "active"
        try:
            self.paths = self._files()
            for path in self.paths:
                raw = self._read(path)
                self._digests[str(path)] = hashlib.sha256(raw).hexdigest()
                self._retain_source(path, raw)
            payload = {
                "candidate": self.candidate,
                "roots": [str(path.absolute()) for path in self.roots],
                "sources": {
                    str(Path(path).absolute()): digest
                    for path, digest in self._digests.items()
                },
                "parser": [
                    sys.implementation.cache_tag,
                    list(sys.version_info[:3]),
                    sys.flags.optimize,
                    "exec",
                    False,
                    None,
                ],
            }
            self.identity = hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode()
            ).hexdigest()
            return self
        except BaseException:
            self._clear()
            raise

    def module(self, path: Path) -> ParsedSource:
        if self._state != "active":
            raise RuntimeError("Python source inventory is not active")
        key = str(path)
        if key not in self._digests:
            raise AssertionError(
                f"Python source is outside the captured inventory: {path}"
            )
        cached = self._parsed.get(key)
        if cached is not None:
            self._parsed.move_to_end(key)
            self.stats["parse_hits"] += 1
            return cached
        raw = self._raw.get(key)
        if raw is None:
            raw = self._read(path)
            if hashlib.sha256(raw).hexdigest() != self._digests[key]:
                raise AssertionError(f"Python source changed during analysis: {path}")
            self._retain_source(path, raw)
        else:
            self._raw.move_to_end(key)
        # Match Path.read_text(encoding="utf-8") universal-newline semantics.
        text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        tree = ast.parse(text, filename=str(path))
        parsed = ParsedSource(tree, _owned_nodes(tree))
        self.stats["parse_calls"] += 1
        count = len(parsed.nodes)
        if count <= self.max_ast_nodes and self.max_cached_files:
            while (
                self._ast_nodes + count > self.max_ast_nodes
                or len(self._parsed) >= self.max_cached_files
            ):
                _, discarded = self._parsed.popitem(last=False)
                self._ast_nodes -= len(discarded.nodes)
            self._parsed[key] = parsed
            self._ast_nodes += count
            self.stats["peak_ast_nodes"] = max(
                self.stats["peak_ast_nodes"], self._ast_nodes
            )
        return parsed

    def _clear(self) -> None:
        self._raw.clear()
        self._parsed.clear()
        self._digests.clear()
        self.paths = ()
        self._source_bytes = self._ast_nodes = 0
        self._state = "closed"

    def __exit__(self, kind, error, traceback) -> None:
        try:
            if kind is None:
                if tuple(map(str, self._files())) != tuple(map(str, self.paths)):
                    raise AssertionError(
                        "Python source inventory changed during analysis"
                    )
                for path, expected in self._digests.items():
                    if hashlib.sha256(self._read(Path(path))).hexdigest() != expected:
                        raise AssertionError(
                            f"Python source changed during analysis: {path}"
                        )
        finally:
            self._clear()
