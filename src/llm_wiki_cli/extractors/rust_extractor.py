"""Rust AST extractor for llm-wiki-cli.

Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol` by delegating
to a bundled Rust binary (``rust_scripts/src/main.rs``) that uses the ``syn``
crate for Rust AST parsing.

Requirements
------------
* Rust toolchain (``cargo``) on PATH.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from .common import discover_source_files, filter_bundled_inventory

_RUST_SCRIPTS_DIR = Path(__file__).parent / "rust_scripts"


class RustExtractor:
    """Extractor for Rust source files using a ``cargo run`` subprocess.

    Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.

    Each returned file entry includes ``"language": "rust"``.
    """

    last_error: str | None = None

    def extract(
        self,
        src_dir: str,
        only_files: list[str] | None = None,
        deep: bool = False,
    ) -> dict:
        """Scan *src_dir* for Rust files and return an inventory dict.

        Parameters
        ----------
        src_dir:
            Root directory to scan.
        only_files:
            Optional list of paths (relative to *src_dir*) to restrict
            extraction to.  When ``None``, all ``.rs`` files found under
            *src_dir* are scanned (excluding ``target/``, ``vendor/``, etc.).
        deep:
            When ``True``, include enriched data (doc comments, struct fields,
            method details, imports).  When ``False``, return a slim format.

        Returns
        -------
        dict
            ``{filepath: file_entry}`` where each ``file_entry`` contains at
            minimum ``"classes"``, ``"functions"``, and ``"language"``.
        """
        self.last_error = None
        if not discover_source_files(src_dir, (".rs",), only_files=only_files, language="rust"):
            return {}

        if not shutil.which("cargo"):
            self.last_error = "cargo not found. Install Rust (https://rustup.rs/) to enable Rust extraction."
            print(f"llm-wiki Rust extractor: {self.last_error}", file=sys.stderr)
            return {}

        cmd = [
            "cargo", "run", "--quiet", "--",
            "--src-dir", str(Path(src_dir).resolve()),
        ]
        if only_files:
            cmd += ["--only-files", ",".join(only_files)]
        if deep:
            cmd.append("--deep")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=180,
                cwd=str(_RUST_SCRIPTS_DIR),
            )
        except subprocess.CalledProcessError as exc:
            self.last_error = "extraction failed"
            print(
                f"llm-wiki Rust extractor: extraction failed.\n{exc.stderr}",
                file=sys.stderr,
            )
            return {}
        except subprocess.TimeoutExpired:
            self.last_error = "extraction timed out after 180 s"
            print(
                "llm-wiki Rust extractor: extraction timed out after 180 s.",
                file=sys.stderr,
            )
            return {}
        except FileNotFoundError:
            self.last_error = "cargo executable not found"
            print(
                "llm-wiki Rust extractor: cargo executable not found.",
                file=sys.stderr,
            )
            return {}

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

        src_root = Path(src_dir).resolve()
        normalized_inventory: dict = {}
        for fp, data in inventory.items():
            try:
                rel = Path(fp).resolve().relative_to(src_root).as_posix()
            except ValueError:
                rel = fp.replace("\\", "/")
            normalized_inventory[rel] = data

        return normalized_inventory
