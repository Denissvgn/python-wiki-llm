"""Rust AST extractor for agent-wiki-cli.

Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol` by delegating
to a bundled Rust binary (``rust_scripts/src/main.rs``) that uses the ``syn``
crate for Rust AST parsing.

Requirements
------------
* Rust helper prepared with ``llm-wiki prepare-extractors``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .common import (
    chunk_source_files_for_cli,
    discover_source_files,
    filter_bundled_inventory,
)
from ..services.extractor_helpers import (
    ENV_EXTRACTOR_TIMEOUT,
    extractor_timeout_seconds,
    get_prepared_binary,
    missing_helper_message,
)

_RUST_SCRIPTS_DIR = Path(__file__).parent / "rust_scripts"


@dataclass(frozen=True)
class RustExtractionRequest:
    """Internal request object for Rust extraction orchestration."""

    src_dir: str
    only_files: list[str] | None = None
    deep: bool = False
    source_files: list[str] | None = None
    helper_cache_dir: str | None = None


class RustExtractor:
    """Extractor for Rust source files using a prepared helper binary.

    Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.

    Each returned file entry includes ``"language": "rust"``.
    """

    last_error: str | None = None

    def extract(
        self,
        src_dir: str | RustExtractionRequest,
        only_files: list[str] | None = None,
        deep: bool = False,
    ) -> dict:
        """Scan Rust files and return an inventory dict."""
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
        src_dir: str | RustExtractionRequest,
        only_files: list[str] | None,
        deep: bool,
    ) -> RustExtractionRequest:
        if isinstance(src_dir, RustExtractionRequest):
            return src_dir
        return RustExtractionRequest(src_dir=src_dir, only_files=only_files, deep=deep)

    def _resolve_source_files(self, request: RustExtractionRequest) -> list[str]:
        if request.source_files is not None:
            return request.source_files
        return discover_source_files(
            request.src_dir,
            (".rs",),
            only_files=request.only_files,
            language="rust",
        )

    def _prepared_helper(self, request: RustExtractionRequest) -> Path | None:
        helper_binary = get_prepared_binary(
            "rust", request.src_dir, request.helper_cache_dir
        )
        if helper_binary is None:
            self.last_error = missing_helper_message(
                "rust",
                request.src_dir,
                request.helper_cache_dir,
            )
            print(f"llm-wiki Rust extractor: {self.last_error}", file=sys.stderr)
        return helper_binary

    def _load_chunked_inventory(
        self,
        request: RustExtractionRequest,
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
        request: RustExtractionRequest,
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
        return cmd

    def _run_helper(
        self,
        cmd: list[str],
        helper_binary: Path,
    ) -> subprocess.CompletedProcess | None:
        timeout_seconds = extractor_timeout_seconds()
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout_seconds,
                cwd=str(helper_binary.parent),
            )
        except subprocess.CalledProcessError as exc:
            self.last_error = "extraction failed"
            print(
                f"llm-wiki Rust extractor: extraction failed.\n{exc.stderr}",
                file=sys.stderr,
            )
            return None
        except subprocess.TimeoutExpired:
            self.last_error = (
                f"extraction timed out after {timeout_seconds} s; configure "
                f"{ENV_EXTRACTOR_TIMEOUT} to allow more time"
            )
            print(
                f"llm-wiki Rust extractor: {self.last_error}.",
                file=sys.stderr,
            )
            return None
        except FileNotFoundError:
            self.last_error = "prepared Rust helper executable not found"
            print(
                "llm-wiki Rust extractor: prepared Rust helper executable not found.",
                file=sys.stderr,
            )
            return None

    def _load_inventory(self, result: subprocess.CompletedProcess) -> dict:
        # Forward any warnings the Rust script wrote to stderr.
        if result.stderr.strip():
            sys.stderr.write(result.stderr)

        if not result.stdout.strip():
            return {}

        try:
            inventory: dict = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.last_error = "malformed JSON output"
            print(
                f"llm-wiki Rust extractor: malformed JSON output — {exc}",
                file=sys.stderr,
            )
            return {}

        for entry in inventory.values():
            entry["language"] = "rust"

        inventory = filter_bundled_inventory(inventory, _RUST_SCRIPTS_DIR)
        return inventory

    def _normalize_inventory(self, src_dir: str, inventory: dict) -> dict:
        inventory = filter_bundled_inventory(
            inventory,
            _RUST_SCRIPTS_DIR,
            source_root=src_dir,
        )
        src_root = Path(src_dir).resolve()
        normalized_inventory: dict = {}
        for fp, data in inventory.items():
            try:
                rel = Path(fp).resolve().relative_to(src_root).as_posix()
            except ValueError:
                rel = fp.replace("\\", "/")
            normalized_inventory[rel] = data

        return normalized_inventory
