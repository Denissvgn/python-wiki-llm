"""Go AST extractor for agent-wiki-cli.

Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol` by delegating
to a bundled Go script (``go_scripts/main.go``) that uses ``go/ast`` and
``go/parser`` for Go AST traversal.

Requirements
------------
* Go helper prepared with ``llm-wiki prepare-extractors``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .common import (
    chunk_source_files_for_cli,
    discover_source_files,
    filter_bundled_inventory,
    normalize_include_tests,
)
from ..services.extractor_helpers import get_prepared_binary, missing_helper_message

_GO_SCRIPTS_DIR = Path(__file__).parent / "go_scripts"


@dataclass(frozen=True)
class GoExtractionRequest:
    """Internal request object for Go extraction orchestration."""

    src_dir: str
    only_files: list[str] | None = None
    deep: bool = False
    source_files: list[str] | None = None
    helper_cache_dir: str | None = None
    include_tests: Iterable[str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "include_tests", normalize_include_tests(self.include_tests)
        )


class GoExtractor:
    """Extractor for Go source files using a prepared helper binary.

    Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.

    Each returned file entry includes ``"language": "go"``.
    """

    last_error: str | None = None

    def extract(
        self,
        src_dir: str | GoExtractionRequest,
        only_files: list[str] | None = None,
        deep: bool = False,
    ) -> dict:
        """Scan Go files and return an inventory dict."""
        self.last_error = None
        request = self._coerce_request(src_dir, only_files, deep)
        source_files = self._resolve_source_files(request)
        if not source_files:
            return {}

        helper_binary = self._prepared_helper(request)
        if helper_binary is None:
            return {}

        inventory = self._load_chunked_inventory(request, source_files, helper_binary)
        if not inventory:
            return {}

        return self._normalize_inventory(request.src_dir, inventory)

    def _coerce_request(
        self,
        src_dir: str | GoExtractionRequest,
        only_files: list[str] | None,
        deep: bool,
    ) -> GoExtractionRequest:
        if isinstance(src_dir, GoExtractionRequest):
            return src_dir
        return GoExtractionRequest(src_dir=src_dir, only_files=only_files, deep=deep)

    def _resolve_source_files(self, request: GoExtractionRequest) -> list[str]:
        if request.source_files is not None:
            return request.source_files
        return discover_source_files(
            request.src_dir,
            (".go",),
            only_files=request.only_files,
            language="go",
            include_tests=request.include_tests,
        )

    def _prepared_helper(self, request: GoExtractionRequest) -> Path | None:
        helper_binary = get_prepared_binary(
            "go", request.src_dir, request.helper_cache_dir
        )
        if helper_binary is None:
            self.last_error = missing_helper_message(
                "go",
                request.src_dir,
                request.helper_cache_dir,
            )
            print(f"llm-wiki Go extractor: {self.last_error}", file=sys.stderr)
        return helper_binary

    def _load_chunked_inventory(
        self,
        request: GoExtractionRequest,
        source_files: list[str],
        helper_binary: Path,
    ) -> dict:
        inventory: dict = {}
        for chunk in chunk_source_files_for_cli(source_files):
            cmd = self._build_command(request, chunk, helper_binary)
            result = self._run_helper(cmd, helper_binary)
            if result is None:
                return {}
            chunk_inventory = self._load_inventory(result)
            if self.last_error:
                return {}
            inventory.update(chunk_inventory)
        return inventory

    def _build_command(
        self,
        request: GoExtractionRequest,
        source_files: list[str],
        helper_binary: Path,
    ) -> list[str]:
        cmd = [
            str(helper_binary),
            "--src-dir",
            str(Path(request.src_dir).resolve()),
        ]
        cmd += ["--only-files", ",".join(source_files)]
        if request.deep:
            cmd.append("--deep")
        if request.include_tests and "go" in request.include_tests:
            cmd.append("--include-tests")
        return cmd

    def _run_helper(
        self,
        cmd: list[str],
        helper_binary: Path,
    ) -> subprocess.CompletedProcess | None:
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=120,
                cwd=str(helper_binary.parent),
            )
        except subprocess.CalledProcessError as exc:
            self.last_error = "extraction failed"
            print(
                f"llm-wiki Go extractor: extraction failed.\n{exc.stderr}",
                file=sys.stderr,
            )
            return None
        except subprocess.TimeoutExpired:
            self.last_error = "extraction timed out after 120 s"
            print(
                "llm-wiki Go extractor: extraction timed out after 120 s.",
                file=sys.stderr,
            )
            return None
        except FileNotFoundError:
            self.last_error = "prepared Go helper executable not found"
            print(
                "llm-wiki Go extractor: prepared Go helper executable not found.",
                file=sys.stderr,
            )
            return None

    def _load_inventory(self, result: subprocess.CompletedProcess) -> dict:
        # Forward any warnings the Go script wrote to stderr.
        if result.stderr.strip():
            sys.stderr.write(result.stderr)

        if not result.stdout.strip():
            return {}

        try:
            inventory: dict = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.last_error = "malformed JSON output"
            print(
                f"llm-wiki Go extractor: malformed JSON output — {exc}",
                file=sys.stderr,
            )
            return {}

        for entry in inventory.values():
            entry["language"] = "go"

        inventory = filter_bundled_inventory(inventory, _GO_SCRIPTS_DIR)
        return inventory

    def _normalize_inventory(self, src_dir: str, inventory: dict) -> dict:
        src_root = Path(src_dir).resolve()
        normalized_inventory: dict = {}
        for fp, data in inventory.items():
            try:
                rel = Path(fp).resolve().relative_to(src_root).as_posix()
            except ValueError:
                rel = fp.replace("\\", "/")
            normalized_inventory[rel] = data

        return normalized_inventory
