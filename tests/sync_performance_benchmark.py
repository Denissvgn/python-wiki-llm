"""Measure one sync in a disposable checkout with explicit provider provenance.

Timing runs use bounded wrappers at operation boundaries, never cProfile.
The caller must supply a disposable checkout; original issue-report wikis must
not be passed directly. Raw evidence belongs outside the tracked source tree.
"""

from __future__ import annotations

import argparse
from collections import Counter
import functools
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import sys
import time

try:
    import resource
except ImportError:
    resource = None


def tree_summary(root: Path, *, exclude_bytecode=False) -> dict:
    checksum = hashlib.sha256()
    count = total = 0
    if root.exists():
        for path in sorted(root.rglob("*")):
            if exclude_bytecode and ("__pycache__" in path.parts or path.suffix == ".pyc"):
                continue
            if path.is_symlink():
                raise ValueError("benchmark inputs must not contain symbolic links")
            if not path.is_file():
                continue
            name = path.relative_to(root).as_posix()
            encoded_name = name.encode("utf-8")
            file_hash = hashlib.sha256()
            size = 0
            with path.open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    file_hash.update(chunk)
                    size += len(chunk)
            checksum.update(len(encoded_name).to_bytes(8, "big"))
            checksum.update(encoded_name)
            checksum.update(size.to_bytes(8, "big"))
            checksum.update(file_hash.digest())
            total += size
            count += 1
    return {"files": count, "bytes": total, "sha256": checksum.hexdigest(),
            "hash_encoding": "path-size-content-sha256/v1"}


def instrument() -> tuple[Counter, list]:
    """Wrap shared aliases too; imported function names otherwise evade counts."""
    targets = {
        "llm_wiki_cli.commands.sync_cmd": ("_extract_current_inventory", "_build_sync_graph_observations"),
        "llm_wiki_cli.services.knowledge_generation": ("build_knowledge_generation_plan",),
        "llm_wiki_cli.services.knowledge_graph": ("materialize_typed_graph",),
        "llm_wiki_cli.services.knowledge_index": ("build_knowledge_index",),
        "llm_wiki_cli.services.knowledge_model": ("parse_knowledge_index",),
        "llm_wiki_cli.services.knowledge_artifacts": ("validate_knowledge_artifacts",),
        "llm_wiki_cli.services.knowledge_packs": ("build_packed_store",),
        "llm_wiki_cli.services.maintenance_protocol": ("snapshot_wiki", "save_recovery_snapshot"),
        "llm_wiki_cli.extractors.python_bindings": ("analyze_python_bindings",),
    }
    for module in targets:
        importlib.import_module(module)
    from llm_wiki_cli.services.progress import phase
    counts: Counter = Counter()
    replacements = []
    for module_name, names in targets.items():
        module = sys.modules[module_name]
        for name in names:
            original = getattr(module, name)

            def wrapped(*args, _original=original, _name=name, **kwargs):
                counts[_name] += 1
                with phase(_name.lstrip("_")[:48]):
                    return _original(*args, **kwargs)

            functools.update_wrapper(wrapped, original)
            for loaded_name, loaded in tuple(sys.modules.items()):
                if loaded_name.startswith("llm_wiki_cli") and loaded is not None:
                    for alias, value in tuple(vars(loaded).items()):
                        if value is original:
                            replacements.append((loaded, alias, original))
                            setattr(loaded, alias, wrapped)
    return counts, replacements


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--wiki", default="docs/llm_wiki")
    parser.add_argument("--source", default=".")
    parser.add_argument("--provider", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-writes", action="store_true", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--rebuild-knowledge", action="store_true")
    args = parser.parse_args(argv)
    root = args.checkout.resolve()
    if not (root / ".sync-performance-disposable").is_file():
        parser.error("checkout requires an explicit .sync-performance-disposable marker")
    wiki = (root / args.wiki).resolve()
    source = (root / args.source).resolve()
    if not wiki.is_relative_to(root) or not source.is_relative_to(root):
        parser.error("source and wiki must remain inside the disposable checkout")
    import llm_wiki_cli
    package = Path(llm_wiki_cli.__file__).resolve().parent
    if not package.is_relative_to(args.provider.resolve()):
        parser.error(f"wrong imported provider: {package}")
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    os.chdir(root)
    from llm_wiki_cli.cli import main as cli
    before = tree_summary(wiki)
    recovery = root / ".git" / "maintenance-preimages"
    recovery_before = tree_summary(recovery)
    counts, replacements = instrument()
    command = ["llm-wiki", "sync", "--jobs", "1", "--progress", "always", "--cache-stats",
               "--src-dir", str(source), "--wiki-dir", str(wiki), "--helper-cache-dir", str(root / ".git")]
    if args.dry_run:
        command.append("--dry-run")
    if args.force:
        command.append("--force")
    if args.rebuild_knowledge:
        command.append("--rebuild-knowledge")
    previous_argv = sys.argv
    sys.argv = command
    started, cpu = time.perf_counter(), time.process_time()
    error = None
    try:
        cli()
    except SystemExit as exc:
        if exc.code not in (None, 0):
            error = f"SystemExit: {exc.code}"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        wall, used_cpu = time.perf_counter() - started, time.process_time() - cpu
        sys.argv = previous_argv
        for module, name, original in reversed(replacements):
            setattr(module, name, original)
    result = {
        "schema": "llm-wiki-sync-performance/v1", "ok": error is None, "error": error,
        "command": command, "tool_version": llm_wiki_cli.__version__, "provider": str(package),
        "provider_tree": tree_summary(package, exclude_bytecode=True),
        "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
        "conditions": "fresh process; warm/uncontrolled OS cache; operation wrappers, no profiler",
        "wall_seconds": wall, "cpu_seconds": used_cpu,
        "peak_rss_bytes": None if resource is None else resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024),
        "work_counts": dict(counts), "wiki_before": before, "wiki_after": tree_summary(wiki),
        "recovery_before": recovery_before, "recovery_after": tree_summary(recovery),
    }
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("ok", "error", "wall_seconds", "peak_rss_bytes", "work_counts")}))
    return 0 if error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
