"""TypeScript AST extractor for llm-wiki-cli.

Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol` by delegating
to a bundled Node.js script (``ts_scripts/extract.js``) that uses ``ts-morph``
for TypeScript AST traversal.

Requirements
------------
* Node.js (``node``) on PATH.
* ``npm`` on PATH (used once to install ts-morph into ``ts_scripts/node_modules``).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from .common import discover_source_files, filter_bundled_inventory

_TS_SCRIPTS_DIR = Path(__file__).parent / "ts_scripts"


def _ensure_npm_deps() -> bool:
    """Install ts-morph if ``node_modules`` is absent.

    Returns True on success, False if npm is unavailable or the install fails.
    """
    if (_TS_SCRIPTS_DIR / "node_modules").exists():
        return True

    if not shutil.which("npm"):
        print(
            "llm-wiki TypeScript extractor: npm not found. "
            "Install Node.js (https://nodejs.org) to enable TypeScript extraction.",
            file=sys.stderr,
        )
        return False

    scripts_dir = str(_TS_SCRIPTS_DIR.resolve())
    try:
        if sys.platform == "win32":
            # npm on Windows is a .cmd batch script — it requires shell=True.
            # Using subprocess `cwd=` with shell=True can be unreliable
            # when the Python process CWD has been changed (e.g. by tests),
            # so we embed an explicit `cd /d` to guarantee the directory.
            subprocess.run(
                f'cd /d "{scripts_dir}" && npm install',
                capture_output=True,
                check=True,
                timeout=120,
                shell=True,
            )
        else:
            subprocess.run(
                ["npm", "install"],
                capture_output=True,
                check=True,
                timeout=120,
                cwd=scripts_dir,
            )
        return True
    except subprocess.CalledProcessError as exc:
        print(
            f"llm-wiki TypeScript extractor: npm install failed.\n"
            f"{exc.stderr.decode(errors='replace')}",
            file=sys.stderr,
        )
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(
            "llm-wiki TypeScript extractor: npm install timed out or not found.",
            file=sys.stderr,
        )
        return False


class TypeScriptExtractor:
    """Extractor for TypeScript source files using a Node.js/ts-morph subprocess.

    Implements :class:`~llm_wiki_cli.extractors.ExtractorProtocol`.

    Each returned file entry includes ``"language": "typescript"``.
    """

    last_error: str | None = None

    def extract(
        self,
        src_dir: str,
        only_files: list[str] | None = None,
        deep: bool = False,
    ) -> dict:
        """Scan *src_dir* for TypeScript files and return an inventory dict.

        Parameters
        ----------
        src_dir:
            Root directory to scan.
        only_files:
            Optional list of paths (relative to *src_dir*) to restrict
            extraction to.  When ``None``, all ``.ts``/``.tsx`` files found
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
        source_files = discover_source_files(
            src_dir, (".ts", ".tsx"), only_files=only_files, language="typescript",
        )
        if not source_files:
            return {}

        if not shutil.which("node"):
            self.last_error = (
                "node not found. Install Node.js (https://nodejs.org) "
                "to enable TypeScript extraction."
            )
            print(f"llm-wiki TypeScript extractor: {self.last_error}", file=sys.stderr)
            return {}

        if not _ensure_npm_deps():
            self.last_error = "npm dependencies unavailable"
            return {}

        cmd = [
            "node",
            str(_TS_SCRIPTS_DIR / "extract.js"),
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
                cwd=_TS_SCRIPTS_DIR,
            )
        except subprocess.CalledProcessError as exc:
            self.last_error = "extraction failed"
            print(
                f"llm-wiki TypeScript extractor: extraction failed.\n{exc.stderr}",
                file=sys.stderr,
            )
            return {}
        except subprocess.TimeoutExpired:
            self.last_error = "extraction timed out after 120 s"
            print(
                "llm-wiki TypeScript extractor: extraction timed out after 120 s.",
                file=sys.stderr,
            )
            return {}
        except FileNotFoundError:
            self.last_error = "node executable not found"
            print(
                "llm-wiki TypeScript extractor: node executable not found.",
                file=sys.stderr,
            )
            return {}

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

        for entry in inventory.values():
            entry["language"] = "typescript"

        inventory = filter_bundled_inventory(inventory, _TS_SCRIPTS_DIR)

        src_root = Path(src_dir).resolve()
        normalized_inventory: dict = {}
        for fp, data in inventory.items():
            try:
                rel = Path(fp).resolve().relative_to(src_root).as_posix()
            except ValueError:
                rel = fp.replace("\\", "/")
            normalized_inventory[rel] = data

        return normalized_inventory
