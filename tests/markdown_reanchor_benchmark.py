"""Disposable CLI timings for cold, unchanged and authored-Markdown syncs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

from tests.knowledge_performance_fixture import source_corpus


def run(work: Path, provider: Path, output: Path, *, repetitions=3, profile=False):
    """Use fresh provider processes and retain each command receipt separately."""
    work = work.resolve()
    provider = provider.resolve()
    output = output.resolve()
    if work.exists() and any(work.iterdir()):
        raise ValueError("benchmark workspace must be absent or empty")
    work.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    source = work / "source"
    source.mkdir()
    files, oracle = source_corpus("large")
    for name, content in list(files.items()):
        if name.startswith("unit_"):
            owner = name.removeprefix("unit_").removesuffix(".py")
            for number in range(8):
                content += f"\nclass Additional{owner}_{number}:\n    def execute(self):\n        return step_0(2)\n"
            files[name] = content
    oracle["additional_classes_per_owner"] = 8
    for path, content in files.items():
        (source / path).write_text(content, encoding="utf-8")
    environment = dict(os.environ, PYTHONPATH=str(provider))
    rows = []

    def command(case, *arguments, profiled=False):
        script = "from llm_wiki_cli.cli import main; main()"
        if profiled:
            script = (
                "import cProfile; from llm_wiki_cli.cli import main; "
                f"cProfile.runctx('main()', globals(), locals(), {str(output / 'sync.prof')!r})"
            )
        started = time.perf_counter()
        result = subprocess.run(
            [sys.executable, "-c", script, *arguments], cwd=work,
            env=environment, text=True, capture_output=True, timeout=900,
        )
        row = {"case": case, "arguments": arguments,
               "seconds": time.perf_counter() - started, "returncode": result.returncode}
        (output / f"{case}.stdout").write_text(result.stdout)
        (output / f"{case}.stderr").write_text(result.stderr)
        rows.append(row)
        write()
        if result.returncode:
            raise RuntimeError(f"{case} failed: {result.stderr[-3000:]}")
        print(json.dumps(row), flush=True)

    def write():
        (output / "measurements.json").write_text(json.dumps({
            "schema_version": "llm-wiki-markdown-benchmark/v1", "environment": {
                "python": sys.version, "platform": platform.platform(),
                "machine": platform.machine(), "executable": sys.executable,
                "provider": str(provider), "jobs": 1,
                "cache_dir": "cache", "fresh_process_per_command": True,
            }, "oracle": oracle, "source_sha256": {
                name: hashlib.sha256(content.encode()).hexdigest() for name, content in files.items()
            }, "rows": rows,
        }, indent=2) + "\n")

    common = ("--src-dir", "source", "--wiki-dir", "wiki", "--jobs", "1",
              "--no-plugins", "--progress", "always", "--cache-dir", "cache")
    command("setup", "bootstrap", "--src-dir", "source", "--wiki-dir", "wiki",
            "--knowledge-format", "packed-v4-deflate")
    page = work / "wiki/modules/unit_0000.md"
    def edit(number):
        text = page.read_text()
        if "## Operator notes" in text:
            text = text.split("## Operator notes", 1)[0]
        page.write_text(text.rstrip() + f"\n\n## Operator notes\n\nBounded recursion receipt {number}.\n")

    edit("cold")
    command("cold", "sync", *common)
    shutil.copytree(work / "wiki", output / "cold-wiki")
    for repetition in range(repetitions):
        command(f"unchanged-{repetition}", "sync", *common)
        edit(repetition)
        command(f"markdown-{repetition}", "sync", *common)
    # A fresh cache is a genuine cold analysis fallback on an established wiki.
    shutil.rmtree(work / "cache", ignore_errors=True)
    command("cold-established", "sync", *common)
    command("strict-lint", "lint", "--strict", "--profile", "--src-dir", "source",
            "--wiki-dir", "wiki", "--jobs", "1", "--cache-dir", "cache")
    command("ci", "ci-check", "--no-report", "--format", "json", *common)
    if profile:
        edit("profile")
        command("profile-markdown", "sync", *common, profiled=True)
    oracle["pages"] = len(list((work / "wiki").rglob("*.md")))
    if oracle["pages"] < 2000:
        raise AssertionError("qualification corpus must contain thousands of generated pages")
    write()
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--provider", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()
    run(args.work, args.provider, args.output, repetitions=args.repetitions, profile=args.profile)
