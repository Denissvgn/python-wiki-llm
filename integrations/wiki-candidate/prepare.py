"""Prepare the selected helpers and check a consumer's existing native evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from llm_wiki_cli.services.documentation_native import (
    evaluate_documentation_native_freshness,
)
from llm_wiki_cli.services.helper_cache import ensure_helper
from llm_wiki_cli.services.helper_preparation import selected_helper_languages
from llm_wiki_cli.services.helper_runtime import helper_operation
from llm_wiki_cli.services.knowledge_evidence import hash_json
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.publication_config import (
    load_publication_config,
    publication_path,
    publication_source_root,
)
from llm_wiki_cli.services.source_retirement import retired_entity_mappings


_PROVIDER = Path(__file__).resolve().parents[2]
_LOCK = _PROVIDER / "release/toolchain-lock.json"
_MODES = {
    "typescript": "routine",
    "go": "extractor-go",
    "rust": "extractor-rust",
    "haskell": "extractor-haskell",
}


def _write(path: Path, document: dict) -> None:
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def prepare(
    mode: str,
    consumer: Path,
    config_path: str,
    source_dir: str,
    evidence: Path,
    cache: Path,
) -> None:
    policy = load_publication_config(consumer, config_path=config_path)
    if "content" not in policy:
        raise ValueError(
            "Candidate generation requires an explicit publication content profile"
        )
    architecture = policy["architecture"]
    existing = architecture["baseline"] == "existing-wiki"
    relative_source = publication_source_root(architecture, source_dir)
    source = publication_path(consumer, relative_source)
    if not source.is_dir():
        raise ValueError(f"Source directory is missing: {relative_source}")
    languages = selected_helper_languages(source)
    plan = {
        "source": relative_source,
        "languages": languages,
        "baseline": architecture["baseline"],
        "toolchain_lock_sha256": hashlib.sha256(_LOCK.read_bytes()).hexdigest(),
    }
    plan_path = evidence / "helper-plan.json"
    if mode == "toolchains":
        _write(plan_path, plan)
        for language in languages:
            subprocess.run(
                [
                    str(_PROVIDER / ".github/scripts/setup-llm-wiki-ci-toolchains.sh"),
                    "--mode",
                    _MODES[language],
                    "--install-root",
                    str(cache.parent / "toolchains"),
                    "--lock",
                    str(_LOCK),
                    "--python",
                    sys.executable,
                ],
                cwd=cache.parent,
                check=True,
            )
        return
    if mode != "check" or json.loads(plan_path.read_bytes()) != plan:
        raise ValueError("Source/helper selection changed after toolchain planning")
    helpers = {}
    for language in languages:
        handle = ensure_helper(language, source, str(cache))
        helpers[language] = {
            "profile": handle.key,
            "receipt_hash": hash_json(dict(handle.receipt)),
        }
    _write(evidence / "helpers.json", helpers)
    if not existing:
        return

    wiki = publication_path(consumer, architecture["root"])
    report_path = evidence / "native-integrity.json"
    with report_path.open("wb") as report:
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-m",
                "llm_wiki_cli.cli",
                "ci-check",
                "--src-dir",
                relative_source,
                "--wiki-dir",
                architecture["root"],
                "--no-plugins",
                "--no-cache",
                "--no-report",
                "--helper-preparation",
                "never",
                "--helper-cache-dir",
                str(cache),
                "--jobs",
                "1",
                "--format",
                "json",
                "--report-schema",
                "v4",
                "--comparison-policy",
                "auto",
            ],
            cwd=consumer,
            stdout=report,
            check=False,
        )
    if result.returncode or json.loads(report_path.read_bytes()).get("ok") is not True:
        raise ValueError(
            "Native wiki integrity failed. Inspect native-integrity.json and repair the source wiki."
        )

    # ci-check's integrity verdict and the documentation workflow's source
    # freshness verdict answer different questions. Require both before export.
    state = load_knowledge_state(wiki)
    if state.knowledge is None or state.manifest_basis is None:
        raise ValueError(
            "A valid committed native wiki is required for candidate generation"
        )
    with helper_operation("never", cache_dir=cache):
        freshness = evaluate_documentation_native_freshness(
            knowledge=state.knowledge,
            manifest=state.manifest_basis,
            source_root=source,
            trust_source_plugins=False,
            helper_cache_dir=cache,
        )
    # Historical members make no current structural promise, so ordinary
    # freshness can be healthy while this publication baseline remains blocked.
    retired = retired_entity_mappings(state.manifest_basis)
    retained_pages = sorted({
        concept.document.canonical_path
        for concept in state.knowledge.concepts
        if concept.document.canonical_path in retired
    })
    reasons = list(freshness.reasons)
    report = {"current": freshness.current and not retained_pages, "reasons": reasons}
    if retained_pages:
        reasons.append("retained-source-history")
        report["retained_source_pages"] = retained_pages
    _write(evidence / "native-freshness.json", report)
    if retained_pages and freshness.current:
        raise ValueError(
            "Native wiki freshness is blocked by retained source history; see retained_source_pages "
            "in native-freshness.json. Preserve the historical wiki. To document current source, "
            "prepare a fresh baseline in a separate directory and review the publication bindings."
        )
    if not freshness.current:
        raise ValueError(
            "Native wiki evidence is stale. Inspect native-freshness.json and refresh the source wiki."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("toolchains", "check"))
    parser.add_argument("consumer", type=Path)
    parser.add_argument("config")
    parser.add_argument("source_dir")
    parser.add_argument("evidence", type=Path)
    parser.add_argument("cache", type=Path)
    args = parser.parse_args()
    prepare(
        args.mode,
        args.consumer,
        args.config,
        args.source_dir,
        args.evidence,
        args.cache,
    )
