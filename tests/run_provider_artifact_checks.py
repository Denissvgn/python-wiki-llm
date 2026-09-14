"""Run the existing artifact harness in fresh wheel/sdist consumer environments."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    args.work.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    environment = {
        **os.environ,
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "PIP_NO_INPUT": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    }
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    commands = []

    def run(label, command):
        with (args.output / (label + ".log")).open("w", encoding="utf-8") as log:
            result = subprocess.run(
                [str(x) for x in command],
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=900,
            )
        commands.append(
            {
                "label": label,
                "argv": [str(x) for x in command],
                "exit_code": result.returncode,
            }
        )
        (args.output / "commands.json").write_text(
            json.dumps(commands, indent=2) + "\n", encoding="utf-8"
        )
        result.check_returncode()

    for kind, pattern in (("wheel", "*.whl"), ("sdist", "*.tar.gz")):
        artifacts = list(args.artifacts.glob(pattern))
        if len(artifacts) != 1:
            raise ValueError(f"Expected exactly one {kind}")
        artifact = artifacts[0].absolute()
        interpreters = []
        for extra in ("base", "mcp"):
            prefix = args.work / f"{kind}-{extra}" / ".venv"
            if prefix.exists():
                raise ValueError("Consumer environments must be fresh")
            run(kind + "-" + extra + "-venv", [sys.executable, "-m", "venv", prefix])
            python = prefix / (
                "Scripts/python.exe" if os.name == "nt" else "bin/python"
            )
            interpreters.append(python)
            requirement = str(artifact) + ("[mcp]" if extra == "mcp" else "")
            run(
                kind + "-" + extra + "-install",
                [python, "-I", "-m", "pip", "install", requirement],
            )
            run(kind + "-" + extra + "-check", [python, "-I", "-m", "pip", "check"])
        run(
            kind + "-smoke",
            [
                sys.executable,
                root / "tests/release_artifact_smoke.py",
                "--artifact",
                artifact,
                "--python",
                interpreters[0],
                "--mcp-python",
                interpreters[1],
                "--expected-version",
                args.version,
                "--work",
                args.work / "shared-smoke",
                "--output",
                args.output / (kind + ".json"),
            ],
        )
    run(
        "comparison",
        [
            sys.executable,
            "-I",
            root / "release/qualification.py",
            "compare-smoke",
            "--wheel",
            args.output / "wheel.json",
            "--sdist",
            args.output / "sdist.json",
            "--output",
            args.output / "comparison.json",
        ],
    )


if __name__ == "__main__":
    main()
