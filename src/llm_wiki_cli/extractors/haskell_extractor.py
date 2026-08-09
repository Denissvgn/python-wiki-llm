"""Haskell source extractor backed by a prepared helper binary."""

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
)

_HASKELL_SCRIPTS_DIR = Path(__file__).parent / "haskell_scripts"


@dataclass(frozen=True)
class HaskellExtractionRequest:
    """Internal request object for Haskell extraction orchestration."""

    src_dir: str
    only_files: list[str] | None = None
    deep: bool = False
    source_files: list[str] | None = None
    helper_cache_dir: str | None = None


class HaskellExtractor:
    """Extractor for Haskell source files using a prepared helper binary."""

    last_error: str | None = None

    def extract(
        self,
        src_dir: str | HaskellExtractionRequest,
        only_files: list[str] | None = None,
        deep: bool = False,
    ) -> dict:
        """Scan Haskell files and return an inventory dict."""
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
        src_dir: str | HaskellExtractionRequest,
        only_files: list[str] | None,
        deep: bool,
    ) -> HaskellExtractionRequest:
        if isinstance(src_dir, HaskellExtractionRequest):
            return src_dir
        return HaskellExtractionRequest(
            src_dir=src_dir,
            only_files=only_files,
            deep=deep,
        )

    def _resolve_source_files(self, request: HaskellExtractionRequest) -> list[str]:
        if request.source_files is not None:
            return request.source_files
        return discover_source_files(
            request.src_dir,
            (".hs", ".lhs"),
            only_files=request.only_files,
            language="haskell",
        )

    def _prepared_helper(self, request: HaskellExtractionRequest) -> Path | None:
        helper_binary = get_prepared_binary(
            "haskell", request.src_dir, request.helper_cache_dir
        )
        if helper_binary is None:
            self.last_error = _missing_haskell_helper_message(request)
            print(f"llm-wiki Haskell extractor: {self.last_error}", file=sys.stderr)
        return helper_binary

    def _load_chunked_inventory(
        self,
        request: HaskellExtractionRequest,
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
        request: HaskellExtractionRequest,
        source_files: list[str],
        helper_binary: Path,
    ) -> list[str]:
        cmd = [
            str(helper_binary),
            "--src-dir",
            str(Path(request.src_dir).resolve()),
            "--only-files",
            ",".join(source_files),
        ]
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
                f"llm-wiki Haskell extractor: extraction failed.\n{exc.stderr}",
                file=sys.stderr,
            )
            return None
        except subprocess.TimeoutExpired:
            self.last_error = (
                f"extraction timed out after {timeout_seconds} s; configure "
                f"{ENV_EXTRACTOR_TIMEOUT} to allow more time"
            )
            print(
                f"llm-wiki Haskell extractor: {self.last_error}.",
                file=sys.stderr,
            )
            return None
        except FileNotFoundError:
            self.last_error = "prepared Haskell helper executable not found"
            print(
                "llm-wiki Haskell extractor: prepared Haskell helper executable "
                "not found.",
                file=sys.stderr,
            )
            return None

    def _load_inventory(self, result: subprocess.CompletedProcess) -> dict:
        if result.stderr.strip():
            sys.stderr.write(result.stderr)

        if not result.stdout.strip():
            return {}

        try:
            inventory: dict = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.last_error = "malformed JSON output"
            print(
                f"llm-wiki Haskell extractor: malformed JSON output - {exc}",
                file=sys.stderr,
            )
            return {}

        for entry in inventory.values():
            entry["language"] = "haskell"

        return filter_bundled_inventory(inventory, _HASKELL_SCRIPTS_DIR)

    def _normalize_inventory(self, src_dir: str, inventory: dict) -> dict:
        inventory = filter_bundled_inventory(
            inventory,
            _HASKELL_SCRIPTS_DIR,
            source_root=src_dir,
        )
        src_root = Path(src_dir).resolve()
        normalized_inventory: dict = {}
        for fp, data in inventory.items():
            rel = _normalize_inventory_path(src_root, str(fp))
            normalized_inventory[rel] = data
        return normalized_inventory


def _missing_haskell_helper_message(request: HaskellExtractionRequest) -> str:
    return (
        "haskell helper is not prepared. Run "
        "`llm-wiki prepare-extractors --language haskell` before "
        "extract/bootstrap/sync/lint/ci-check."
    )


def _normalize_inventory_path(src_root: Path, raw_path: str) -> str:
    posix_path = raw_path.replace("\\", "/")
    root_prefix = src_root.as_posix().rstrip("/") + "/"
    if posix_path.startswith(root_prefix):
        return posix_path[len(root_prefix) :]
    try:
        return Path(raw_path).resolve().relative_to(src_root).as_posix()
    except (OSError, ValueError):
        return posix_path
