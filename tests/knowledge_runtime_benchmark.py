"""Serial local runtime benchmark with full-builder equivalence checks."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import statistics
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services import knowledge_orchestration
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions
from llm_wiki_cli.services.lint_service import build_report
from llm_wiki_cli.services.progress import Progress

ARTIFACTS = (
    ".llm-wiki-surface.json",
    ".llm-wiki-knowledge.json",
    ".llm-wiki-manifest.json",
)


def _bytes(wiki: Path) -> dict[str, bytes]:
    return {name: (wiki / name).read_bytes() for name in ARTIFACTS}


def _sync(wiki: str = "wiki", **kwargs) -> None:
    values = dict(src_dir="src", wiki_dir=wiki, cache_dir="cache", force=True)
    values.update(kwargs)
    sync_cmd.run(SimpleNamespace(**values))


def _measure(label: str, operation) -> dict:
    progress = Progress(
        "sync" if label != "warm_lint" else "lint",
        mode="always",
        output_format="json",
        stream=io.StringIO(),
    )
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        with patch.object(
            knowledge_orchestration,
            "build_knowledge_generation_plan",
            wraps=knowledge_orchestration.build_knowledge_generation_plan,
        ) as build:
            start = time.perf_counter()
            with progress.run():
                result = operation()
            elapsed = time.perf_counter() - start
    if result is not None and hasattr(result, "passed") and not result.passed:
        raise RuntimeError(
            f"{label} fixture failed validation: {[issue.category for issue in result.issues]}"
        )
    return {
        "case": label,
        "seconds": elapsed,
        "knowledge_builder_calls": build.call_count,
        "phase_seconds": progress.durations,
        "counts": progress.counts,
    }


def _fixture(count: int) -> None:
    Path("src").mkdir()
    Path(".git").mkdir()
    Path("src/pyproject.toml").write_text(
        '[project]\nname="runtime-sample"\nversion="1.0.0"\n', encoding="utf-8"
    )
    for index in range(count):
        Path(f"src/part_{index}.py").write_text(
            f"from pathlib import Path\nclass Record{index}:\n    pass\n\ndef save_{index}(value):\n    Path('output').write_text(value)\n    return value\n",
            encoding="utf-8",
        )
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        bootstrap_cmd.run(
            SimpleNamespace(
                src_dir="src",
                wiki_dir="wiki",
                depth="full",
                overwrite=False,
                source_adapter=True,
                skip_workflows=True,
            )
        )


def _delta(label: str, mutate) -> dict:
    shutil.copytree("wiki", "oracle")
    mutate()
    measured = _measure(label, _sync)
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        _sync("oracle", rebuild_knowledge=True, no_cache=True, cache_dir=None)
    measured["oracle_equal"] = _bytes(Path("wiki")) == _bytes(Path("oracle"))
    if not measured["oracle_equal"]:
        raise AssertionError(f"{label} differs from the full builder")
    shutil.rmtree("oracle")
    return measured


def run_benchmark(source_count: int, repeats: int) -> dict:
    rows = []
    artifact_sizes = []
    original = Path.cwd()
    for repeat in range(repeats):
        print(f"Runtime benchmark repetition {repeat + 1}/{repeats}", flush=True)
        with tempfile.TemporaryDirectory(
            prefix="llm-wiki-runtime-benchmark-"
        ) as temporary:
            os.chdir(temporary)
            try:
                _fixture(source_count)
                rows.append(_measure("cold_sync", _sync))
                rows.append(
                    _measure(
                        "warm_lint",
                        lambda: build_report(
                            "wiki",
                            "src",
                            strict=True,
                            cache_options=InventoryCacheOptions(
                                enabled=True, cache_dir="cache", stats_enabled=True
                            ),
                        ),
                    )
                )
                rows.append(_measure("noop_sync", _sync))
                assert rows[-1]["knowledge_builder_calls"] == 0
                artifact_sizes.append(
                    {
                        name: len(content)
                        for name, content in _bytes(Path("wiki")).items()
                    }
                )
                rows.append(
                    _delta(
                        "source_edit",
                        lambda: Path("src/part_0.py").write_text(
                            "class Changed: pass\n", encoding="utf-8"
                        ),
                    )
                )
                rows.append(
                    _delta("source_delete", lambda: Path("src/part_1.py").unlink())
                )
                rows.append(
                    _delta(
                        "source_rename",
                        lambda: Path("src/part_2.py").rename("src/renamed.py"),
                    )
                )

                def markdown():
                    for wiki in ("wiki", "oracle"):
                        path = Path(wiki) / "modules/part_3.md"
                        path.write_text(
                            path.read_text(encoding="utf-8")
                            + "\n## Operator notes\nStable authored note.\n",
                            encoding="utf-8",
                        )

                rows.append(_delta("markdown_edit", markdown))
                rows.append(
                    _delta(
                        "configuration_change",
                        lambda: Path("src/pyproject.toml").write_text(
                            '[project]\nname="runtime-sample"\nversion="1.0.0"\ndependencies=["requests"]\n',
                            encoding="utf-8",
                        ),
                    )
                )
            finally:
                os.chdir(original)
    summaries = {}
    for label in sorted({row["case"] for row in rows}):
        selected = [row for row in rows if row["case"] == label]
        summaries[label] = {
            "median_seconds": statistics.median(row["seconds"] for row in selected),
            "max_seconds": max(row["seconds"] for row in selected),
            "runs": len(selected),
        }
    return {
        "source_count": source_count,
        "repeats": repeats,
        "cases": summaries,
        "runs": rows,
        "artifact_sizes": artifact_sizes,
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=int, default=12)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.sources < 4 or args.repeats < 1:
        parser.error("at least four sources and one repetition are required")
    args.output.write_text(
        json.dumps(run_benchmark(args.sources, args.repeats), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
