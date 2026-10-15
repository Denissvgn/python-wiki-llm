"""Pinned real source callers for the existing composite Action owner."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
from urllib.parse import urlparse
from urllib.request import url2pathname


PROVIDER_SHA = "63c8fa7b264610b57f0f1e24c9327eb92d8b0819"


def specs():
    return json.loads(Path(__file__).with_name("real_callers.json").read_text())


def hashes(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): (
            "symlink:" + os.readlink(p) if p.is_symlink()
            else hashlib.sha256(p.read_bytes()).hexdigest()
        )
        for name in ("source", "wiki", "private")
        for p in (root / name).rglob("*")
        if p.is_file() or p.is_symlink()
    }


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True
    ).strip()


def commit(root, message):
    subprocess.run([
        "git", "-C", str(root), "-c", "user.name=Caller fixture",
        "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
        "commit", "-m", message,
    ], check=True, stdout=subprocess.PIPE)


def check_declarations(inventory: dict, expected: dict) -> None:
    for path, contracts in expected.items():
        entry = inventory.get(path, {})
        for key, names in contracts.items():
            if key == "methods":
                for owner, method_names in names.items():
                    owners = [cls for cls in entry.get("classes", []) if cls["name"] == owner]
                    if len(owners) != 1 or not set(method_names) <= {m["name"] for m in owners[0].get("methods", [])}:
                        raise ValueError(f"Required selected declarations were not analyzed: {path}/methods/{owner}")
                continue
            records = entry.get(key, [])
            if not set(names) <= {r["name"] for r in records}:
                raise ValueError(f"Required selected declarations were not analyzed: {path}/{key}")


def require_provider(provider: Path, expected: str):
    if not re.fullmatch(r"[0-9a-f]{40}", expected) or git(provider, "rev-parse", "HEAD") != expected:
        raise ValueError("Provider resource checkout differs from the pinned SHA")
    if git(provider, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Pinned provider source has tracked modifications")


def origin_code():
    return """
from importlib.metadata import distribution
from llm_wiki_cli import api
from pathlib import Path
import json, sys, hashlib
assert Path(api.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
d = distribution('agent-wiki-cli')
print(json.dumps({'module': api.__file__, 'prefix': sys.prefix, 'version': d.version,
                  'api_sha256': hashlib.sha256(Path(api.__file__).read_bytes()).hexdigest(),
                  'direct_url': json.loads(d.read_text('direct_url.json'))}))
"""


def validate_origin(value, provider):
    url = urlparse(value["direct_url"]["url"])
    if (
        value["version"] != "2.5.0" or url.scheme != "file" or url.netloc
        or Path(url2pathname(url.path)).resolve() != provider.resolve()
        or value["direct_url"].get("dir_info", {}).get("editable") is True
    ):
        raise ValueError("Action runtime is not the pinned provider source install")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "mutate", "check"))
    parser.add_argument("--project", choices=tuple(specs()), required=True)
    parser.add_argument("--provider", type=Path, required=True)
    parser.add_argument("--provider-sha", default=PROVIDER_SHA)
    parser.add_argument("--checkout", type=Path)
    parser.add_argument("--helper-cache", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--case", choices=("clean", "drift", "corrupt"), default="clean")
    parser.add_argument("--kind", choices=("context", "integrity"))
    parser.add_argument("--outcome")
    parser.add_argument("--action-evidence", type=Path)
    parser.add_argument("--action-python", type=Path)
    args = parser.parse_args(argv)
    root = Path.cwd()
    spec = specs()[args.project]
    args.evidence.mkdir(parents=True, exist_ok=True)
    require_provider(args.provider, args.provider_sha)

    def save(name, value):
        (args.evidence / name).write_text(json.dumps(value, indent=2) + "\n")

    if args.operation == "prepare":
        from llm_wiki_cli import api

        if any((root / name).exists() for name in (".git", "source", "wiki")):
            raise ValueError("Caller roots must be fresh and separate from provider resources")
        if args.checkout is None or args.helper_cache is None:
            raise ValueError("Exact caller checkout and prepared helper cache are required")
        if git(args.checkout, "rev-parse", "HEAD") != spec["commit"]:
            raise ValueError("Caller source checkout differs from its frozen commit")
        origin = json.loads(subprocess.check_output([sys.executable, "-I", "-c", origin_code()]))
        validate_origin(origin, args.provider)
        raw = subprocess.check_output(["git", "-C", str(args.checkout), "archive", "--format=tar", spec["commit"]])
        source = root / "source"
        source.mkdir()
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            archive.extractall(source, filter="data")
        (source / ".llm-wiki").mkdir(exist_ok=True)
        (source / ".llm-wiki/source-selection.json").write_text(json.dumps(spec["selection"], indent=2) + "\n")
        selected_plan = json.loads(subprocess.check_output([
            sys.executable, "-I", "-m", "llm_wiki_cli.cli", "prepare-extractors",
            "--src-dir", "source", "--plan", "--format", "json",
        ]))
        if selected_plan["languages"] != spec["helper_languages"]:
            raise ValueError("Caller helper plan differs from its declared languages")
        subprocess.run([sys.executable, "-I", "-m", "llm_wiki_cli.cli", "prepare-extractors",
                        "--src-dir", "source", "--cache-dir", str(args.helper_cache)], check=True)
        os.environ["LLM_WIKI_CACHE_DIR"] = str(args.helper_cache)
        (root / "private").mkdir()
        (root / "private/notes.md").write_text("Private caller sentinel; not an application input.\n")
        (root / ".gitignore").write_text(".provider/\n.tools/\n.caller-input/\nprivate/\n")
        branch = "codex/foreign-" + args.project
        subprocess.run(["git", "init", "--initial-branch=" + branch], check=True, stdout=subprocess.PIPE)
        branch_status = git(root, "status", "-sb").splitlines()[0]
        if git(root, "for-each-ref", "--format=%(upstream:short)", "refs/heads/" + branch):
            raise ValueError("Fresh caller branch must have no upstream")
        save("branch-safety.json", {"branch": branch, "status": branch_status, "upstream": None})
        inventory = api.extract_source("source", deep=True, read_only=True)
        check_declarations(inventory["inventory"], spec["expected_declarations"])
        api.bootstrap_wiki("source", "wiki", helper_cache_dir=str(args.helper_cache), api_contracts=args.project == "fastapi")
        save("analyzed-source.json", {"source_commit": spec["commit"], "helper_plan": selected_plan,
            "declarations_checked": spec["expected_declarations"],
            "inventory_paths": sorted(inventory["inventory"]),
            "provider_ref": args.provider_sha, "bootstrap_origin": origin,
            "caller_source_archive_sha256": hashlib.sha256(raw).hexdigest()})
        subprocess.run(["git", "add", ".gitignore", "source", "wiki"], check=True)
        commit(root, "Freeze real caller input")
        if git(root, "for-each-ref", "--format=%(upstream:short)", "refs/heads/" + branch):
            raise ValueError("Committed caller branch must still have no upstream")
        save("initial.json", hashes(root))
    elif args.operation == "mutate":
        if args.case == "drift":
            mutation = spec["mutation"]
            path = root / "source" / mutation["path"]
            before = path.read_text()
            if mutation["needle"] not in before:
                raise ValueError("Frozen mutation declaration is absent")
            save("mutation-preimage.json", {"path": mutation["path"], "text": before})
            path.write_text(before.replace(mutation["needle"], mutation["replacement"], 1))
        elif args.case == "corrupt":
            preimage = args.evidence / "mutation-preimage.json"
            if preimage.exists():
                before = json.loads(preimage.read_text())
                (root / "source" / before["path"]).write_text(before["text"])
            else:
                initial = json.loads((args.evidence / "initial.json").read_text())
                if {p: h for p, h in hashes(root).items() if p.startswith("source/")} != {
                    p: h for p, h in initial.items() if p.startswith("source/")
                }:
                    raise ValueError("Independent corrupt case must start with frozen source")
            (root / "wiki/.llm-wiki-surface.json").write_text("{broken")
        subprocess.run(["git", "add", "source", "wiki"], check=True)
        if git(root, "status", "--porcelain"):
            commit(root, "Record controlled " + args.case)
    else:
        if args.action_evidence is None or args.action_python is None or args.kind is None:
            raise ValueError("Actual Action evidence, interpreter and integration are required")
        if hashes(root) != json.loads((args.evidence / (args.case + "-before.json")).read_text()):
            raise ValueError("Action changed caller source/wiki/private data")
        if git(root, "status", "--porcelain", "--untracked-files=all"):
            raise ValueError("Action wrote untracked caller data")
        if args.outcome != ("success" if args.case == "clean" else "failure"):
            raise ValueError("Actual Action outcome differs from the caller state")
        plan = json.loads((args.action_evidence / "extractor-plan.json").read_text())
        if plan["languages"] != spec["helper_languages"]:
            raise ValueError("Actual Action helpers did not match the real caller")
        filename = "doctor.json" if args.kind == "context" else "llm-wiki-ci-report.json"
        report = json.loads((args.action_evidence / filename).read_text())
        if args.kind == "context":
            if report["status"] != ("healthy" if args.case == "clean" else "unhealthy"):
                raise ValueError("Real caller health result differs")
            if args.case == "drift" and report["drift"]["confirmed_stale"] < 1:
                raise ValueError("Source drift was not observed by the actual Action")
        else:
            if report["ok"] is not (args.case == "clean"):
                raise ValueError("Real caller integrity result differs")
            if args.case == "drift" and not any(d["category"] == "knowledge_freshness" and d["severity"] == "warning" for d in report["diagnostics"]):
                raise ValueError("Native source drift must remain advisory")
            if args.case == "corrupt" and "surface" not in json.dumps(report["issues"]).lower():
                raise ValueError("Corrupt native commitment was not rejected")
        baseline = json.loads((args.evidence / (args.case + "-baseline.json")).read_text())
        expected = 0 if args.case == "clean" else 1
        if baseline["exit_code"] != expected:
            raise ValueError("Ordinary integrity baseline differs from the expected state")
        if args.kind == "integrity" and report["ok"] != baseline["report"]["ok"]:
            raise ValueError("Native advisory changed the baseline integrity outcome")
        origin = json.loads(subprocess.check_output([str(args.action_python), "-I", "-c", origin_code()]))
        validate_origin(origin, args.provider)
        save(args.case + "-" + args.kind + "-result.json", {"status": "pass", "case": args.case,
            "integration": args.kind, "project": args.project, "provider_ref": args.provider_sha,
            "caller_source_commit": spec["commit"], "caller_head": git(root, "rev-parse", "HEAD"),
            "runtime_origin": origin, "helper_languages": plan["languages"], "caller_unchanged": True})
        # Preserve fixed Action evidence before a later invocation quarantines its directories.
        import shutil
        shutil.copytree(args.action_evidence, args.evidence / (args.case + "-" + args.kind + "-action"), symlinks=True)
        return
    save(args.case + "-before.json", hashes(root))
    # Ordinary producer baseline; the Action adds advisory native diagnostics.
    baseline = subprocess.run([sys.executable, "-I", "-m", "llm_wiki_cli.cli", "ci-check",
        "--src-dir", "source", "--wiki-dir", "wiki", "--helper-cache-dir", str(args.helper_cache),
        "--jobs", "1", "--report-schema", "v2", "--comparison-policy", "exact-v1",
        "--format", "json", "--no-plugins", "--no-report"], capture_output=True, timeout=180)
    if baseline.returncode != (0 if args.case == "clean" else 1):
        raise ValueError("Caller setup did not produce the expected ordinary integrity baseline")
    save(args.case + "-baseline.json", {"exit_code": baseline.returncode, "report": json.loads(baseline.stdout)})


if __name__ == "__main__":
    main()
