"""Check public inline typing from an explicitly installed consumer environment."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def run_check(python: Path, work: Path, analyzer_python: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    origin = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            """
import json, sys
from pathlib import Path
from llm_wiki_cli import api
root = Path(api.__file__).resolve().parent
assert root.is_relative_to(Path(sys.prefix).resolve()), 'provider import is not installed'
assert (root / 'py.typed').is_file(), 'installed typing marker is absent'
print(json.dumps({'module': str(root / 'api.py'), 'prefix': sys.prefix}))
""",
        ],
        env=environment,
        cwd=work,
        capture_output=True,
        text=True,
        timeout=30,
    )
    (work / "origin.stdout").write_text(origin.stdout, encoding="utf-8")
    (work / "origin.stderr").write_text(origin.stderr, encoding="utf-8")
    origin.check_returncode()
    fixtures = Path(__file__).parent / "fixtures"
    expected = set()
    for line, content in enumerate(
        (fixtures / "provider-typing-invalid.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    ):
        match = re.search(r"# expected: (\w+)", content)
        if match:
            expected.add((line, match.group(1)))
    assert expected, "negative typing control has no expectations"
    version = ""
    for case, filename in (
        ("valid", "provider-typing-valid.py"),
        ("invalid", "provider-typing-invalid.txt"),
    ):
        client = work / f"{case}.py"
        client.write_bytes((fixtures / filename).read_bytes())
        config = work / f"{case}.json"
        config.write_text(
            json.dumps(
                {
                    "include": [client.name],
                    "typeCheckingMode": "strict",
                    "pythonVersion": "3.10",
                    "useLibraryCodeForTypes": False,
                    "reportMissingTypeStubs": "error",
                }
            ),
            encoding="utf-8",
        )
        checked = subprocess.run(
            [
                str(analyzer_python),
                "-m",
                "pyright",
                "--pythonpath",
                str(python),
                "--project",
                str(config),
                "--outputjson",
            ],
            env=environment,
            cwd=work,
            capture_output=True,
            text=True,
            timeout=120,
        )
        (work / f"{case}-result.json").write_text(checked.stdout, encoding="utf-8")
        (work / f"{case}-stderr.txt").write_text(checked.stderr, encoding="utf-8")
        result = json.loads(checked.stdout)
        version = result["version"]
        diagnostics = result["generalDiagnostics"]
        errors = {
            (item["range"]["start"]["line"], item.get("rule"))
            for item in diagnostics
            if item["severity"] == "error"
        }
        if case == "valid":
            assert checked.returncode == 0 and not diagnostics, diagnostics
        else:
            assert checked.returncode == 1 and errors == expected, diagnostics
            assert len(diagnostics) == len(expected), diagnostics
    return {
        "valid_client": "pass",
        "invalid_calls_rejected": len(expected),
        "inference_from_untyped_library": False,
        "analyzer": f"pyright {version}",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--analyzer-python", type=Path, default=Path(sys.executable))
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Keep venv interpreter symlinks intact; resolving them loses site-packages.
    result = run_check(
        args.python.absolute(), args.work.resolve(), args.analyzer_python.absolute()
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
