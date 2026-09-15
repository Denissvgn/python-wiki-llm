"""Foreign caller fixture for real composite actions; no target code execution."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def hashes(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for directory in (root / "source", root / "wiki")
        for p in directory.rglob("*")
        if p.is_file()
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "check"))
    parser.add_argument("--case", choices=("clean", "drift", "corrupt"), required=True)
    parser.add_argument("--kind", choices=("context", "integrity"), required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--helper-cache", type=Path)
    parser.add_argument("--action-evidence", type=Path)
    parser.add_argument("--outcome")
    args = parser.parse_args(argv)
    root = Path.cwd()
    args.evidence.mkdir(parents=True, exist_ok=True)
    if args.operation == "prepare":
        from llm_wiki_cli import api

        if (
            (root / ".git").exists()
            or (root / "source").exists()
            or (root / "wiki").exists()
        ):
            raise ValueError(
                "The caller workspace must be fresh and distinct from .provider"
            )
        (root / "source/go").mkdir(parents=True)
        (root / "source/caller.py").write_text(
            "raise RuntimeError('caller code must not execute')\nclass CallerOnly:\n    value: int\n"
        )
        (root / "source/go/hook.go").write_text(
            'package caller\nfunc CallerHook(value string) string { panic("must not execute") }\n'
        )
        if args.helper_cache is None:
            raise ValueError("An explicit bootstrap helper cache is required")
        subprocess.run(
            [
                sys.executable,
                "-I",
                "-m",
                "llm_wiki_cli.cli",
                "prepare-extractors",
                "--src-dir",
                "source",
                "--cache-dir",
                str(args.helper_cache),
                "--language",
                "go",
            ],
            check=True,
        )
        api.bootstrap_wiki("source", "wiki", helper_cache_dir=str(args.helper_cache))
        manifest = json.loads((root / "wiki/.llm-wiki-manifest.json").read_text())
        assert set(manifest["sources"]) == {"caller.py", "go/hook.go"}
        if args.case == "drift":
            source = root / "source/caller.py"
            source.write_text(source.read_text().replace("value: int", "value: str"))
        elif args.case == "corrupt":
            (root / "wiki/.llm-wiki-surface.json").write_text("{broken")
        (root / ".gitignore").write_text(".provider/\n")
        commands = [
            ["git", "init", "--initial-branch=caller-fixture"],
            ["git", "add", ".gitignore", "source", "wiki"],
            [
                "git",
                "-c",
                "user.name=Caller fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-m",
                "Freeze synthetic caller input",
            ],
        ]
        for command in commands:
            subprocess.run(command, check=True, stdout=subprocess.PIPE)
        upstream = subprocess.check_output(
            [
                "git",
                "for-each-ref",
                "--format=%(upstream:short)",
                "refs/heads/caller-fixture",
            ],
            text=True,
        ).strip()
        assert not upstream
        (args.evidence / "before.json").write_text(
            json.dumps(hashes(root), indent=2) + "\n"
        )
        return
    assert hashes(root) == json.loads((args.evidence / "before.json").read_text()), (
        "action changed caller files"
    )
    assert not subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], text=True
    ).strip()
    assert args.outcome == ("success" if args.case == "clean" else "failure")
    if args.action_evidence is None:
        raise ValueError("Actual action evidence is required")
    plan = json.loads((args.action_evidence / "extractor-plan.json").read_text())
    assert plan == {
        "schema": "llm-wiki-prepare-extractors-plan/v1",
        "languages": ["go"],
    }
    report_name = "doctor.json" if args.kind == "context" else "llm-wiki-ci-report.json"
    report = json.loads((args.action_evidence / report_name).read_text())
    if args.kind == "context":
        assert report["status"] == ("healthy" if args.case == "clean" else "unhealthy")
        if args.case == "drift":
            assert report["drift"]["confirmed_stale"] >= 1
    else:
        assert report["ok"] is (args.case == "clean")
        if args.case == "drift":
            assert any(
                issue["category"] == "sync_manifest" for issue in report["issues"]
            )
            assert any(
                d["category"] == "knowledge_freshness" and d["severity"] == "warning"
                for d in report["diagnostics"]
            )
        elif args.case == "corrupt":
            assert "surface" in json.dumps(report["issues"]).lower()
    (args.evidence / "result.json").write_text(
        json.dumps(
            {
                "case": args.case,
                "integration": args.kind,
                "status": "pass",
                "caller_unchanged": True,
                "source_files": ["caller.py", "go/hook.go"],
                "helper_languages": plan["languages"],
                "outcome": args.outcome,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
