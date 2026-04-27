"""Go AST extractor for llm-wiki-cli.

Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol` by delegating
to a bundled Go script (``go_scripts/main.go``) that uses ``go/ast`` and
``go/parser`` for Go AST traversal.

Requirements
------------
* Go toolchain (``go``) on PATH.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

_GO_SCRIPTS_DIR = Path(__file__).parent / "go_scripts"


class GoExtractor:
    """Extractor for Go source files using a ``go run`` subprocess.

    Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.

    Each returned file entry includes ``"language": "go"``.
    """

    def extract(
        self,
        src_dir: str,
        only_files: list[str] | None = None,
        deep: bool = False,
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
        if not shutil.which("go"):
            print(
                "llm-wiki Go extractor: go not found. "
                "Install Go (https://go.dev/dl/) to enable Go extraction.",
                file=sys.stderr,
            )
            return {}

        cmd = [
            "go", "run", ".",
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
                timeout=120,
                cwd=str(_GO_SCRIPTS_DIR),
            )
        except subprocess.CalledProcessError as exc:
            print(
                f"llm-wiki Go extractor: extraction failed.\n{exc.stderr}",
                file=sys.stderr,
            )
            return {}
        except subprocess.TimeoutExpired:
            print(
                "llm-wiki Go extractor: extraction timed out after 120 s.",
                file=sys.stderr,
            )
            return {}
        except FileNotFoundError:
            print(
                "llm-wiki Go extractor: go executable not found.",
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
            print(
                f"llm-wiki Go extractor: malformed JSON output — {exc}",
                file=sys.stderr,
            )
            return {}

        for entry in inventory.values():
            entry["language"] = "go"

        # Exclude files from the extractor's own bundled scripts directory.
        scripts_abs = _GO_SCRIPTS_DIR.resolve().as_posix() + "/"
        inventory = {
            fp.replace("\\", "/"): data for fp, data in inventory.items()
            if not fp.replace("\\", "/").startswith(scripts_abs)
            and not Path(fp).resolve().as_posix().startswith(scripts_abs)
        }

        return inventory
