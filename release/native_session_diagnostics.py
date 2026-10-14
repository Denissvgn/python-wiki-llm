"""Read-only timing attribution for a failed installed-artifact session gate.

This diagnostic never qualifies a release. It runs in the original installed
consumer, with trusted fixture resources, after the full pinned harness fails.
"""

from __future__ import annotations

import argparse
import cProfile
import faulthandler
import hashlib
from importlib.metadata import distribution
import json
import os
from pathlib import Path
import platform
import pstats
import re
import runpy
import subprocess
import sys
import time
from types import ModuleType
from typing import Any
from unittest.mock import patch
from urllib.parse import urlparse


FIXTURE = "tests/fixtures/workflow-artifact-consumer.py"
MARKER = "async def transport(transport_name):"


def preparation_source(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.count(MARKER) != 1:
        raise ValueError("trusted fixture preparation boundary is unavailable or ambiguous")
    return text.split(MARKER)[0]


def require_roots(harness: Path, work: Path, output: Path) -> None:
    protected = (harness, Path(sys.prefix).resolve(), Path(__file__).resolve().parents[1])
    for root in (work, output):
        if any(root == p or root in p.parents or p in root.parents for p in protected):
            raise ValueError("diagnostic roots must be separate from provider and harness")
    if work == output or work in output.parents or output in work.parents:
        raise ValueError("diagnostic output must be outside its caller")
    if work.exists():
        raise ValueError("diagnostic caller must be fresh")
    if output.exists() and any(output.iterdir()):
        raise ValueError("diagnostic output must be fresh")


def installed_origin(version: str, archive_hash: str) -> dict:
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) or not re.fullmatch(r"[0-9a-f]{64}", archive_hash):
        raise ValueError("diagnostic requires a stable version and full archive digest")
    from llm_wiki_cli import api

    module = Path(api.__file__).resolve()
    prefix = Path(sys.prefix).resolve()
    d = distribution("agent-wiki-cli")
    direct = json.loads(d.read_text("direct_url.json") or "{}")
    archive = direct.get("archive_info", {})
    digest = archive.get("hashes", {}).get("sha256")
    if digest is None:
        digest = archive.get("hash", "").removeprefix("sha256=")
    if (sys.prefix == sys.base_prefix or not module.is_relative_to(prefix)
            or d.version != version or digest != archive_hash
            or urlparse(direct.get("url", "")).scheme != "file"):
        raise ValueError("diagnostic must use the original pinned installed archive")
    return {"module": str(module), "prefix": str(prefix), "version": d.version,
            "api_sha256": hashlib.sha256(module.read_bytes()).hexdigest(), "direct_url": direct}


def require_harness(harness: Path, expected: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise ValueError("diagnostic harness requires a full pinned commit")
    def git(*arguments):
        return subprocess.check_output(["git", "-C", str(harness), *arguments], timeout=5,
                                       env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}).strip()
    if git("rev-parse", "HEAD").decode() != expected or git("status", "--porcelain"):
        raise ValueError("diagnostic harness differs from the clean pinned checkout")


def profile_read(name, session, request, expected, validate, counter, record, save, output,
                 *, if_result_id=None):
    phase: dict[str, Any] = {"name": name, "status": "running"}
    record["phases"].append(phase)
    save()
    profiler = cProfile.Profile()
    started = time.perf_counter()
    try:
        profiler.enable()
        result = session.read(request, if_result_id=if_result_id)
        profiler.disable()
        if if_result_id is None:
            if result.context is None or result.context.rendered != expected:
                raise ValueError("diagnostic session differs from independent canonical task text")
            validate(result.context.rendered, request, counter=counter)
        elif result.state != "unchanged" or result.result_id != if_result_id:
            raise ValueError("diagnostic warm read failed its exact retained-result check")
        phase.update(status="complete", metadata=result.metadata())
        return result.result_id
    except Exception as error:
        phase.update(status="failed", error={"type": type(error).__name__, "message": str(error)})
        raise
    finally:
        profiler.disable()
        phase["seconds"] = time.perf_counter() - started
        stats = vars(pstats.Stats(profiler))["stats"]
        phase["profile"] = [
            {"file": key[0], "line": key[1], "function": key[2], "calls": value[1],
             "own_seconds": value[2], "cumulative_seconds": value[3]}
            for key, value in sorted(stats.items(), key=lambda item: item[1][3], reverse=True)[:40]
        ]
        profiler.dump_stats(str(output / (name + ".pstats")))
        save()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", type=Path, required=True)
    parser.add_argument("--harness-sha", required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--archive-sha256", required=True)
    args = parser.parse_args(argv)
    harness, work, output = (p.resolve() for p in (args.harness, args.work, args.output))
    # Guards precede every diagnostic write, including failure receipts.
    require_roots(harness, work, output)
    require_harness(harness, args.harness_sha)
    origin = installed_origin(args.version, args.archive_sha256)
    code = preparation_source(harness / FIXTURE)
    output.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "schema_version": "agent-wiki-native-session-diagnostic/v1", "status": "running",
        "release_acceptance": False, "origin": origin,
        "platform": {"os_name": os.name, "sys_platform": sys.platform,
                     "python": sys.version, "machine": platform.machine()},
        "fixture_sha256": hashlib.sha256((harness / FIXTURE).read_bytes()).hexdigest(),
        "fixture_clock_sha256": hashlib.sha256((harness / "tests/artifact_fixture_clock.py").read_bytes()).hexdigest(),
        "harness_sha": args.harness_sha,
        "worker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "preparation": {"status": "running"}, "phases": [],
        "qualification": "Profiled API attribution only; cold/warm refer to session retention after fixture preparation. Does not certify SDK latency or native acceptance.",
    }

    def save():
        (output / "session-profile.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    save()
    previous_cwd, previous_argv, previous_main = Path.cwd(), sys.argv, sys.modules["__main__"]
    try:
        work.mkdir()
        os.chdir(work)
        sys.argv = [str(harness / FIXTURE), str(harness / "examples/native-workflow"),
                    "base", str(harness / "tests/mcp_probe.py"), str(output / "unused.json")]
        fixture_main = ModuleType("__main__")
        namespace: dict[str, Any] = vars(fixture_main)
        sys.modules["__main__"] = fixture_main
        with (output / "stacks.log").open("w", encoding="utf-8") as stacks:
            # Stack samples survive an externally enforced process deadline.
            faulthandler.dump_traceback_later(5, repeat=True, file=stacks)
            try:
                started = time.perf_counter()
                try:
                    from llm_wiki_cli.commands import sync_cmd
                    from llm_wiki_cli.services import bootstrap_runtime
                    clock = runpy.run_path(str(harness / "tests/artifact_fixture_clock.py"))["FixtureDate"]
                    # Preserve the frozen owner's date input and -c namespace.
                    # Runtime clocks, subprocess deadlines and SDK budgets stay real.
                    with patch.object(sync_cmd, "date", clock), patch.object(bootstrap_runtime, "date", clock):
                        exec(compile(code, str(harness / FIXTURE), "exec", dont_inherit=True), namespace)
                except Exception:
                    record["preparation"]["status"] = "failed"
                    raise
                else:
                    record["preparation"]["status"] = "complete"
                finally:
                    record["preparation"]["seconds"] = time.perf_counter() - started
                    save()
                api, counter = namespace["api"], namespace["ByteCounter"]()
                project, tree = namespace["project"], namespace["tree"]
                before = tree(project)
                for kind, request in (("scoped", namespace["scoped_request"]), ("full", namespace["request"])):
                    expected = api.build_task_context(request, src_dir="src", wiki_dir="wiki", counter=counter)
                    with api.open_context_session(src_dir="src", wiki_dir="wiki", counter=counter) as session:
                        identity = profile_read(kind + "-cold", session, request, expected.rendered,
                            api.validate_task_context, counter, record, save, output)
                        profile_read(kind + "-warm", session, request, expected.rendered,
                            api.validate_task_context, counter, record, save, output, if_result_id=identity)
                if tree(project) != before:
                    raise ValueError("diagnostic reads changed caller files")
                if installed_origin(args.version, args.archive_sha256) != origin:
                    raise ValueError("diagnostic provider origin changed")
                record.update(status="complete", caller_unchanged=True)
            finally:
                faulthandler.cancel_dump_traceback_later()
    except Exception as error:
        record.update(status="failed", error={"type": type(error).__name__, "message": str(error)})
        raise
    finally:
        os.chdir(previous_cwd)
        sys.argv = previous_argv
        sys.modules["__main__"] = previous_main
        save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
