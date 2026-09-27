"""Exercise real installed distributions against one independent knowledge fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

PROBE = r'''
import json, pathlib, sys
sys.path.insert(0, sys.argv[1])
import llm_wiki_cli
from llm_wiki_cli import api
assert pathlib.Path(llm_wiki_cli.__file__).resolve().is_relative_to(pathlib.Path(sys.argv[1]).resolve())
if sys.argv[2] == "bootstrap":
    api.bootstrap_wiki("source", "wiki", skip_workflows=True, skip_flows=True, skip_dependencies=True)
else:
    result = api.doctor("source", wiki_dir="wiki", strict=True, report_schema="v4")
    pathlib.Path(sys.argv[3]).write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    native = api.get_knowledge_coverage(src_dir="source", wiki_dir="wiki", live=True)
    from llm_wiki_cli.services.mcp_server import McpWikiService
    mcp = McpWikiService("source", "wiki").get_knowledge_coverage(live=True)
    assert native["counts"] == mcp["counts"]
    counts = native["counts"]
    assert counts and counts["modeled"] > 0
    outcomes = counts["modeled_freshness"]
    assert outcomes
    assert (outcomes["current"] == counts["modeled"]) == (result["status"] == "healthy")
    pathlib.Path(sys.argv[3] + ".native.json").write_text(json.dumps(native, sort_keys=True), encoding="utf-8")
    pathlib.Path(sys.argv[3] + ".mcp.json").write_text(json.dumps(mcp, sort_keys=True), encoding="utf-8")
'''


def run(root: Path, work: Path) -> dict:
    root, work = root.resolve(), work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    fixture = work / "fixture"
    (fixture / "source").mkdir(parents=True)
    (fixture / "source/model.py").write_bytes(b"class User:\n    name: str\n")
    commands = []

    def execute(command, cwd, name):
        result = subprocess.run(command, cwd=cwd, stdin=subprocess.DEVNULL,
            env={**os.environ, "PIP_NO_INPUT": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"},
            capture_output=True, check=False, timeout=180)
        (work / (name + ".stdout")).write_bytes(result.stdout)
        (work / (name + ".stderr")).write_bytes(result.stderr)
        commands.append({"command": command, "cwd": str(cwd), "exit": result.returncode})
        if result.returncode:
            raise ValueError(f"installed compatibility command failed: {name}; see retained stderr")

    original_project = (root / "pyproject.toml").read_text("utf-8")
    version_match = re.search(r'(?m)^version = "([^"]+)"$', original_project)
    if version_match is None:
        raise ValueError("project requires an explicit version")
    version = version_match[1]
    # Disposable metadata-only variant, never a published release version.
    changed_version = version + ".post1"
    rows = []
    for name, selected_version, mutated in (
        ("baseline", version, False), ("version-only", changed_version, False),
        ("same-version-analysis-change", version, True), ("new-version-analysis-change", changed_version, True),
    ):
        candidate = work / name / "candidate"
        candidate.mkdir(parents=True)
        shutil.copytree(root / "src", candidate / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", "node_modules", "target"))
        for filename in ("README.md", "LICENSE", "release_build_backend.py", "MANIFEST.in"):
            shutil.copyfile(root / filename, candidate / filename)
        (candidate / "docs").mkdir()
        for filename in ("standalone-documentation.md", "wiki-guide.md", "cli-reference.md", "automation.md", "security-model.md", "native-knowledge-provider.md", "native-agent-workflow.md"):
            shutil.copyfile(root / "docs" / filename, candidate / "docs" / filename)
        (candidate / "pyproject.toml").write_text(original_project.replace(f'version = "{version}"', f'version = "{selected_version}"', 1), encoding="utf-8")
        if mutated:
            with (candidate / "src/llm_wiki_cli/extractors/python_extractor.py").open("ab") as stream:
                stream.write(b"\n# Controlled analysis implementation mutation.\n")
        dist = work / name / "dist"
        execute([sys.executable, "-I", "-c", "import sys; sys.path.insert(0, '.'); import release_build_backend as b; b.build_wheel(sys.argv[1])", str(dist)], candidate, name + "-build")
        wheels = list(dist.glob("*.whl"))
        if len(wheels) != 1:
            raise ValueError("expected one candidate wheel")
        installed = work / name / "installed"
        execute([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--no-deps", "--no-compile", "--target", str(installed), str(wheels[0])], work, name + "-install")
        if name == "baseline":
            execute([sys.executable, "-I", "-c", PROBE, str(installed), "bootstrap"], fixture, name + "-bootstrap")
        report_path = work / (name + "-doctor.json")
        execute([sys.executable, "-I", "-c", PROBE, str(installed), "doctor", str(report_path)], fixture, name + "-doctor")
        report = json.loads(report_path.read_text("utf-8"))
        expected = "unhealthy" if mutated else "healthy"
        if report["status"] != expected or report["schema_version"] != "llm-wiki-doctor/v4":
            raise ValueError(f"unexpected installed compatibility result: {name}")
        basis = report["health_details"]["basis"]
        if basis["recorded"]["tool"]["version"] != version or basis["live"]["tool"]["version"] != selected_version:
            raise ValueError("installed report lost exact version provenance")
        rows.append({"name": name, "version": selected_version, "status": report["status"],
            "wheel_sha256": hashlib.sha256(wheels[0].read_bytes()).hexdigest(),
            "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
            "native_sha256": hashlib.sha256(Path(str(report_path) + ".native.json").read_bytes()).hexdigest(),
            "mcp_sha256": hashlib.sha256(Path(str(report_path) + ".mcp.json").read_bytes()).hexdigest()})
    result = {"schema_version": "llm-wiki-installed-analysis-pairs/v1", "status": "pass", "cases": rows, "commands": commands}
    (work / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.work)


if __name__ == "__main__":
    main()
