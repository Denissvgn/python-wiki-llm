"""Bind independently installed parser controls to the repository tool locks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .controls import self_test
from .frontends import Frontends


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    args.work.mkdir(parents=True, exist_ok=True)
    lock = json.loads((root / "release/toolchain-lock.json").read_text())["toolchains"]
    tools = {
        key: shutil.which(command)
        for key, command in {
            "node": "node",
            "go": "go",
            "cargo": "cargo",
            "ghc": "ghc",
        }.items()
    }
    if not all(tools.values()):
        raise RuntimeError(
            "All locked compiler frontends are mandatory in the owner lane"
        )
    tools = {key: str(value) for key, value in tools.items()}
    ts = args.work / "typescript"
    ts.mkdir(exist_ok=True)
    for name in ("package.json", "package-lock.json"):
        shutil.copy2(root / "src/llm_wiki_cli/extractors/ts_scripts" / name, ts / name)
    subprocess.run(
        [
            shutil.which("npm") or "npm",
            "ci",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
            "--prefix",
            str(ts),
        ],
        check=True,
        timeout=180,
    )
    go_version = subprocess.check_output([tools["go"], "version"], text=True).strip()
    if not go_version.startswith(lock["go"]["version_output"] + " "):
        raise RuntimeError("Unpinned Go toolchain")
    config = {
        **tools,
        "typescript_module": str(ts / "node_modules/ts-morph"),
        "versions": {
            "typescript": lock["node"]["version_output"],
            "go": go_version,
            "haskell": lock["haskell"]["version_output"],
            "rust": lock["rust"]["version_output"],
        },
    }
    result = self_test(Frontends(config, args.work / "observers"))
    result["controller_python"] = sys.version
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
