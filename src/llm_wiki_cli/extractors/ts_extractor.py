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

    try:
        subprocess.run(
            ["npm", "install"],
            capture_output=True,
            check=True,
            timeout=120,
            # Run from the ts_scripts directory so npm finds package.json
            # there.  Using --prefix instead is unreliable on Windows where
            # modern npm still reads package.json from CWD.
            cwd=str(_TS_SCRIPTS_DIR),
            # npm is a .cmd batch script on Windows; CreateProcess cannot
            # execute .cmd files directly, so we need shell=True there.
            shell=(sys.platform == "win32"),
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
        if not shutil.which("node"):
            print(
                "llm-wiki TypeScript extractor: node not found. "
                "Install Node.js (https://nodejs.org) to enable TypeScript extraction.",
                file=sys.stderr,
            )
            return {}

        if not _ensure_npm_deps():
            return {}

        cmd = [
            "node",
            str(_TS_SCRIPTS_DIR / "extract.js"),
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
                cwd=_TS_SCRIPTS_DIR,
            )
        except subprocess.CalledProcessError as exc:
            print(
                f"llm-wiki TypeScript extractor: extraction failed.\n{exc.stderr}",
                file=sys.stderr,
            )
            return {}
        except subprocess.TimeoutExpired:
            print(
                "llm-wiki TypeScript extractor: extraction timed out after 120 s.",
                file=sys.stderr,
            )
            return {}
        except FileNotFoundError:
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
            print(
                f"llm-wiki TypeScript extractor: malformed JSON output — {exc}",
                file=sys.stderr,
            )
            return {}

        for entry in inventory.values():
            entry["language"] = "typescript"

        # Exclude files from the extractor's own bundled scripts directory.
        scripts_abs = str(_TS_SCRIPTS_DIR.resolve()) + "/"
        inventory = {
            fp: data for fp, data in inventory.items()
            if not str(Path(fp).resolve()).startswith(scripts_abs)
        }

        return inventory
