"""Check or explicitly regenerate KNOW-003 golden contract files."""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Sequence
from pathlib import Path

GOLDEN_ROOT = Path(__file__).parent / "fixtures" / "knowledge"
PROJECT_ROOT = Path(__file__).parents[1]
if __package__ in {None, ""}:
    sys.path[:0] = [str(PROJECT_ROOT), str(PROJECT_ROOT / "src")]
render_knowledge_goldens = importlib.import_module(
    "tests.knowledge_fixtures"
).render_knowledge_goldens


def _write_atomically(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(content)
    temporary.replace(path)


def _display_path(path: Path) -> Path:
    try:
        return path.relative_to(PROJECT_ROOT)
    except ValueError:
        return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="replace committed goldens; without this flag the command only checks",
    )
    args = parser.parse_args(argv)

    rendered = render_knowledge_goldens()
    expected_paths = {GOLDEN_ROOT / name for name in rendered}
    unexpected_paths = set(GOLDEN_ROOT.glob("*.json")) - expected_paths
    mismatches: list[Path] = []
    for name, content in rendered.items():
        path = GOLDEN_ROOT / name
        if path.exists() and path.read_bytes() == content:
            continue
        mismatches.append(path)
        if args.write:
            _write_atomically(path, content)
            print(f"updated {_display_path(path)}")

    if unexpected_paths and args.write:
        for path in sorted(unexpected_paths):
            path.unlink()
            print(f"removed {_display_path(path)}")

    drifted_paths = set(mismatches) | unexpected_paths
    if drifted_paths and not args.write:
        names = ", ".join(str(path) for path in sorted(drifted_paths))
        parser.error(
            f"golden drift detected: {names}; rerun with --write and review the diff"
        )
    if not drifted_paths:
        print("knowledge goldens are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
