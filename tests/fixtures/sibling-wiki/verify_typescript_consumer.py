"""Verify the installed publication CLI in fresh source-only consumer checkouts."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


CONFIG = Path("Review settings") / "Wiki policy.json"
SOURCE = Path("Application code")
DOCUMENT = Path("Public guide") / "Getting started.md"


def create_consumer(root, language):
    filename, code = {
        "python": ("billing.py", "class Ledger:\n    pass\n"),
        "typescript": (
            "billing.ts",
            "export class Ledger { balance(): number { return 10; } }\n",
        ),
    }[language]
    selected = SOURCE / "selected" / filename
    files = {
        selected: code,
        SOURCE / "elsewhere" / "other.go": "package ignored\n",
        SOURCE / ".llm-wiki" / "source-selection.json": json.dumps(
            {
                "schema_version": "llm-wiki-source-selection/v1",
                "include": ["selected"],
                "exclude": [],
            }
        ),
        DOCUMENT: "# Billing\n\nThe ledger records a balance.\n",
        CONFIG: json.dumps(
            {
                "schema_version": "llm-wiki-publication/v1",
                "architecture": {
                    "baseline": "bootstrap-source",
                    "root": SOURCE.as_posix(),
                },
                "target": {"kind": "github-wiki", "repository": "self"},
                "enforcement": "advisory",
                "publish": False,
                "content": {"root": DOCUMENT.parent.as_posix()},
                "topics": [
                    {
                        "id": "billing",
                        "owner": "billing-maintainers",
                        "wiki_page": "Home.md",
                        "edit_at": "repository",
                        "source_document": DOCUMENT.as_posix(),
                        "depends_on": [
                            {"architecture_page": "modules/billing.md"},
                            {"source_file": selected.as_posix()},
                        ],
                    }
                ],
                "exclusions": [
                    {"pattern": "*", "reason": "Only the billing overview is public."}
                ],
            }
        ),
    }
    for name, value in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode("utf-8"))
    return selected.as_posix()


def cli(cwd, cache, *args, expected=0):
    environment = dict(os.environ)
    for name in (
        "OPENAI_API_KEY",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "WIKI_TOKEN",
        "SSH_AUTH_SOCK",
    ):
        environment.pop(name, None)
    if cache is None:
        environment.pop("LLM_WIKI_CACHE_DIR", None)
    else:
        environment["LLM_WIKI_CACHE_DIR"] = str(cache)
    environment.update(
        GIT_TERMINAL_PROMPT="0",
        PIP_NO_INDEX="1",
        npm_config_offline="true",
        PYTHONIOENCODING="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-m", "llm_wiki_cli.cli", *map(str, args)],
        cwd=cwd,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    if result.returncode != expected:
        diagnostic = (result.stderr or result.stdout).decode("utf-8", "replace")
        raise RuntimeError(f"{args}: exit {result.returncode}: {diagnostic[:4096]}")
    return result


def tree(root):
    return {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def verify(workspace, cache, language):
    import llm_wiki_cli

    package = Path(llm_wiki_cli.__file__).resolve()
    assert package.is_relative_to(Path(sys.prefix).resolve()), package
    workspace.mkdir(parents=True, exist_ok=True)
    assert not any(workspace.iterdir()), "Verification requires an empty workspace"
    consumer = workspace / "Billing project"
    selected = create_consumer(consumer, language)
    original = tree(consumer)
    relocated = workspace / "Relocated checkout"
    shutil.copytree(consumer, relocated)
    plan = json.loads(
        cli(
            consumer,
            cache,
            "prepare-extractors",
            "--src-dir",
            SOURCE,
            "--plan",
            "--format",
            "json",
        ).stdout
    )
    expected_helpers = ["typescript"] if language == "typescript" else []
    assert plan["languages"] == expected_helpers
    if not expected_helpers:
        # A Python-only project can run setup before git init or selecting a cache.
        cli(consumer, None, "prepare-extractors", "--src-dir", SOURCE)

    candidate = workspace / "Wiki artifact"
    receipt_path = workspace / "Wiki receipt.json"
    args = ["--receipt", receipt_path, "--config", CONFIG]
    cli(
        workspace,
        cache,
        "docs",
        "wiki",
        "export",
        "--consumer-root",
        consumer,
        "--output-dir",
        candidate,
        *args,
    )
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt["checks"]["ok"] and receipt["impact"]["complete"]
    assert not receipt["ready"] and not receipt["delivery_ready"]
    assert receipt["target"]["mode"] == "artifact-only"
    assert list(receipt["files"]) == ["Home.md"]
    assert (candidate / "Home.md").read_bytes() == original[DOCUMENT]
    architecture = receipt["basis"]["architecture"]
    assert architecture["complete"]
    assert "entities/Ledger.md" in {
        page["canonical_path"] for page in architecture["pages"]
    }
    assert {
        page["source_mapping"]["source_path"]
        for page in architecture["pages"]
        if page["source_mapping"]
    } == {Path(selected).relative_to(SOURCE).as_posix()}
    assert selected in receipt["basis"]["files"]

    check = [
        "docs",
        "wiki",
        "check",
        "--consumer-root",
        relocated,
        "--candidate-dir",
        candidate,
        *args,
    ]
    assert json.loads(cli(consumer, cache, *check).stdout) == receipt
    assert (
        json.loads(cli(consumer, cache, *check, "--require-ready", expected=1).stdout)
        == receipt
    )
    assert tree(consumer) == tree(relocated) == original
    return {
        "language": language,
        "provider": str(package),
        "helpers": plan["languages"],
        "source": selected,
        "candidate_id": receipt["candidate_id"],
        "receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "tree_hash": receipt["tree_hash"],
        "relocated_receipt_matches": True,
        "consumer_unchanged": True,
        "delivery_ready": receipt["delivery_ready"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--helper-cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--language", choices=["typescript", "python"], default="typescript"
    )
    options = parser.parse_args()
    result = verify(
        options.workspace.resolve(), options.helper_cache.resolve(), options.language
    )
    options.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
