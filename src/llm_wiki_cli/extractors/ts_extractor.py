"""TypeScript AST extractor for agent-wiki-cli.

Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol` by delegating
to a bundled Node.js script (``ts_scripts/extract.js``) that uses ``ts-morph``
for TypeScript AST traversal.

Requirements
------------
* Node.js (``node``) on PATH.
* TypeScript dependencies prepared with ``llm-wiki prepare-extractors``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from .common import (
    TYPESCRIPT_FAMILY_EXTENSIONS,
    chunk_source_files_for_cli,
    discover_source_files,
    filter_bundled_inventory,
    inventory_language_for_path,
)
from ..services.extractor_helpers import (
    ENV_EXTRACTOR_TIMEOUT,
    extractor_timeout_seconds,
    get_prepared_typescript_root,
    missing_helper_message,
)

_TS_SCRIPTS_DIR = Path(__file__).parent / "ts_scripts"


class TypeScriptExtractor:
    """Extractor for TypeScript source files using a Node.js/ts-morph subprocess.

    Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.

    Each returned file entry includes ``"language": "typescript"`` for
    ``.ts``/``.tsx`` files or ``"language": "javascript"`` for
    ``.js``/``.jsx`` files.
    """

    last_error: str | None = None

    def extract(
        self,
        src_dir: str,
        only_files: list[str] | None = None,
        deep: bool = False,
        source_files: list[str] | None = None,
        helper_cache_dir: str | None = None,
    ) -> dict:
        """Scan *src_dir* for TypeScript files and return an inventory dict.

        Parameters
        ----------
        src_dir:
            Root directory to scan.
        only_files:
            Optional list of paths (relative to *src_dir*) to restrict
            extraction to.  When ``None``, all TypeScript-family files found
            under *src_dir* are scanned.
        deep:
            When ``True``, include enriched data (JSDoc docstrings, attributes,
            method details, imports).  When ``False``, return a slim format.

        Returns
        -------
        dict
            ``{filepath: file_entry}`` where each ``file_entry`` contains at
            minimum ``"classes"``, ``"functions"``, and ``"language"``.
        """
        self.last_error = None
        source_files = self._resolve_source_files(src_dir, only_files, source_files)
        if not source_files:
            return {}

        helper_root = self._toolchain_root(src_dir, helper_cache_dir)
        if helper_root is None:
            return {}

        inventory: dict = {}
        for chunk in chunk_source_files_for_cli(source_files):
            cmd = self._build_command(src_dir, chunk, deep, helper_root)
            result = self._run_node_extractor(cmd, helper_root)
            if result is None:
                return {}
            chunk_inventory = self._load_inventory(result)
            if self.last_error:
                return {}
            inventory.update(chunk_inventory)
        if not inventory:
            return {}

        return self._normalize_inventory(src_dir, inventory, helper_root)

    def _resolve_source_files(
        self,
        src_dir: str,
        only_files: list[str] | None,
        source_files: list[str] | None,
    ) -> list[str]:
        if source_files is None:
            return discover_source_files(
                src_dir,
                TYPESCRIPT_FAMILY_EXTENSIONS,
                only_files=only_files,
                language="typescript",
            )
        return source_files

    def _toolchain_root(
        self, src_dir: str, helper_cache_dir: str | None = None
    ) -> Path | None:
        if not shutil.which("node"):
            self.last_error = (
                "node not found. Install Node.js (https://nodejs.org) "
                "to enable TypeScript extraction."
            )
            print(f"llm-wiki TypeScript extractor: {self.last_error}", file=sys.stderr)
            return None

        helper_root = get_prepared_typescript_root(src_dir, helper_cache_dir)
        if helper_root is None and helper_cache_dir is None:
            helper_root = get_prepared_typescript_root()
        if helper_root is None:
            self.last_error = missing_helper_message(
                "typescript", src_dir, helper_cache_dir
            )
            print(f"llm-wiki TypeScript extractor: {self.last_error}", file=sys.stderr)
            return None

        return helper_root

    def _build_command(
        self,
        src_dir: str,
        source_files: list[str],
        deep: bool,
        helper_root: Path,
    ) -> list[str]:
        cmd = [
            "node",
            str(helper_root / "extract.js"),
            "--src-dir",
            str(Path(src_dir).resolve()),
        ]
        cmd += ["--only-files", ",".join(source_files)]
        cmd += ["--extensions", ",".join(TYPESCRIPT_FAMILY_EXTENSIONS)]
        if deep:
            cmd.append("--deep")

        return cmd

    def _run_node_extractor(
        self, cmd: list[str], helper_root: Path
    ) -> subprocess.CompletedProcess | None:
        timeout_seconds = extractor_timeout_seconds()
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout_seconds,
                cwd=helper_root,
            )
        except subprocess.CalledProcessError as exc:
            self.last_error = "extraction failed"
            print(
                f"llm-wiki TypeScript extractor: extraction failed.\n{exc.stderr}",
                file=sys.stderr,
            )
            return None
        except subprocess.TimeoutExpired:
            self.last_error = (
                f"extraction timed out after {timeout_seconds} s; configure "
                f"{ENV_EXTRACTOR_TIMEOUT} to allow more time"
            )
            print(
                f"llm-wiki TypeScript extractor: {self.last_error}.",
                file=sys.stderr,
            )
            return None
        except FileNotFoundError:
            self.last_error = "node executable not found"
            print(
                "llm-wiki TypeScript extractor: node executable not found.",
                file=sys.stderr,
            )
            return None

    def _load_inventory(self, result: subprocess.CompletedProcess) -> dict:
        # Forward any warnings the Node.js script wrote to stderr (e.g. skipped files).
        if result.stderr.strip():
            sys.stderr.write(result.stderr)

        if not result.stdout.strip():
            return {}

        try:
            inventory: dict = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.last_error = "malformed JSON output"
            print(
                f"llm-wiki TypeScript extractor: malformed JSON output — {exc}",
                file=sys.stderr,
            )
            return {}

        for fp, entry in inventory.items():
            entry["language"] = inventory_language_for_path("typescript", fp)

        inventory = filter_bundled_inventory(inventory, _TS_SCRIPTS_DIR)
        return inventory

    def _normalize_inventory(
        self, src_dir: str, inventory: dict, helper_root: Path
    ) -> dict:
        inventory = filter_bundled_inventory(inventory, helper_root)
        inventory = filter_bundled_inventory(
            inventory,
            _TS_SCRIPTS_DIR,
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
