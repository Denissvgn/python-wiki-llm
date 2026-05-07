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
from pathlib import Path

from .common import discover_source_files, filter_bundled_inventory
from ..services.extractor_helpers import get_prepared_binary, missing_helper_message

_GO_SCRIPTS_DIR = Path(__file__).parent / "go_scripts"


class GoExtractor:
    """Extractor for Go source files using a prepared helper binary.

    Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.

    Each returned file entry includes ``"language": "go"``.
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
        """Scan *src_dir* for Go files and return an inventory dict.

        Parameters
        ----------
        src_dir:
            Root directory to scan.
        only_files:
            Optional list of paths (relative to *src_dir*) to restrict
            extraction to.  When ``None``, all ``.go`` files found under
            *src_dir* are scanned (excluding ``_test.go``, ``vendor/``, etc.).
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
        if source_files is None:
            source_files = discover_source_files(
                src_dir, (".go",), only_files=only_files, language="go",
            )
        if not source_files:
            return {}

        helper_binary = get_prepared_binary("go", src_dir, helper_cache_dir)
        if helper_binary is None:
            self.last_error = missing_helper_message("go", src_dir, helper_cache_dir)
            print(f"llm-wiki Go extractor: {self.last_error}", file=sys.stderr)
            return {}

        cmd = [
            str(helper_binary),
            "--src-dir", str(Path(src_dir).resolve()),
        ]
        cmd += ["--only-files", ",".join(source_files)]
        if deep:
            cmd.append("--deep")

        try:
            result = subprocess.run(
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
            return {}
        except subprocess.TimeoutExpired:
            self.last_error = "extraction timed out after 120 s"
            print(
                "llm-wiki Go extractor: extraction timed out after 120 s.",
                file=sys.stderr,
            )
            return {}
        except FileNotFoundError:
            self.last_error = "prepared Go helper executable not found"
            print(
                "llm-wiki Go extractor: prepared Go helper executable not found.",
                file=sys.stderr,
            )
            return {}

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

        src_root = Path(src_dir).resolve()
        normalized_inventory: dict = {}
        for fp, data in inventory.items():
            try:
                rel = Path(fp).resolve().relative_to(src_root).as_posix()
            except ValueError:
                rel = fp.replace("\\", "/")
            normalized_inventory[rel] = data

        return normalized_inventory
