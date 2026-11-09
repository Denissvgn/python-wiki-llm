"""Observe committed sibling-wiki changes against the last delivered checkpoint."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import sys

from llm_wiki_cli.services.publication_config import (
    DELIVERY_CHECKPOINT_PATH,
    load_publication_config,
    publication_path,
    publication_ref_name,
    publication_repository,
)

# -I keeps the caller off the import path. Use the same bounded Git tree and
# checkpoint readers as delivery, including their first-parent history checks.
sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "wiki-candidate" / "delivery")
)
git = importlib.import_module("git_transport")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "wiki-candidate"))
checkout = importlib.import_module("checkout")


def _head(repo: Path) -> str:
    return git._oid(git._text(repo, "rev-parse", "--verify", "HEAD^{commit}"))


def _branch(repo: Path) -> str:
    ref = git._text(repo, "symbolic-ref", "HEAD")
    if not ref.startswith("refs/heads/"):
        raise ValueError("Observation needs the selected wiki branch checked out")
    return publication_ref_name(ref.removeprefix("refs/heads/"), "target branch")


def _entry(value):
    if value is None:
        return None
    mode, blob, size = value
    return {"mode": mode.decode("ascii"), "blob": blob, "bytes": size}


def observe(consumer: Path, *, repository: str, config: str, target_dir: str) -> dict:
    """Read two local Git revisions; review records and Git refs are never advanced."""
    source = publication_repository(repository, "source repository").lower()
    policy = load_publication_config(consumer, config_path=config)
    if not target_dir:
        raise ValueError("Drift observation requires target-dir")
    target = publication_path(consumer, target_dir)
    if target == consumer or not target.is_dir():
        raise ValueError("Drift observation requires an independent wiki Git checkout")
    top = git._git(target, "rev-parse", "--show-toplevel").stdout
    if Path(os.fsdecode(top.rstrip(b"\n"))).resolve() != target:
        raise ValueError(
            "Drift observation requires the root of an independent wiki Git checkout"
        )
    if git._text(target, "rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("Drift observation requires a full wiki history")
    partial = git._git(
        target,
        "config",
        "--includes",
        "--name-only",
        "--get-regexp",
        r"(^extensions\.partialclone$|^remote\..*\.promisor$)",
        check=False,
    )
    if partial.returncode not in (0, 1) or partial.stdout:
        raise ValueError(
            "Drift observation requires a locally complete wiki object database"
        )
    branch = _branch(target)
    if policy["target"].get("branch", branch) != branch:
        raise ValueError("Wiki checkout branch differs from the configured target")
    source_root = checkout._repository(consumer)
    source_sha, tip = _head(source_root), _head(target)
    configured = policy["target"]["repository"]
    target_name = source if configured == "self" else configured.lower()
    report = {
        "schema_version": "llm-wiki-drift/v1",
        "status": "unmanaged",
        "complete": True,
        "remote_verified": False,
        "source_repository": source,
        "source_revision": source_sha,
        "target_repository": target_name,
        "target_branch": branch,
        "target_revision": tip,
        "checkpoint_revision": None,
        "checkpoint_id": None,
        "last_delivered_source": None,
        "source_changed": None,
        "owned_changes": [],
        "unmanaged_changes": [],
    }
    introduced = git._last_checkpoint_commit(target, tip)
    if introduced:
        # Validate the original delivery tree first. Validating the live tree
        # against its marker here would discard the exact conflicts we need to report.
        original, before = git._read(target, introduced)
        checkpoint = git._checkpoint(target, introduced, original)
        if checkpoint is None:
            raise ValueError(
                "The last checkpoint was removed; reconcile the wiki history"
            )
        if (
            checkpoint["source_repository"],
            checkpoint["target_repository"],
            checkpoint["target_branch"],
            checkpoint["source_policy"],
        ) != (source, target_name, branch, policy["source_policy"]):
            raise ValueError(
                "Checkpoint belongs to a different source, source policy or wiki branch"
            )
        files, after = (
            git._read(target, tip) if tip != introduced else (original, before)
        )
        if files.get(DELIVERY_CHECKPOINT_PATH) != original[DELIVERY_CHECKPOINT_PATH]:
            raise ValueError("Checkpoint differs from the recorded delivery")
        for path in sorted((before.keys() | after.keys()) - {DELIVERY_CHECKPOINT_PATH}):
            old, new = before.get(path), after.get(path)
            if old == new:
                continue
            bucket = (
                "owned_changes" if path in checkpoint["owned"] else "unmanaged_changes"
            )
            report[bucket].append(
                {"path": path, "before": _entry(old), "after": _entry(new)}
            )
        report.update(
            checkpoint_revision=introduced,
            checkpoint_id=checkpoint["checkpoint_id"],
            last_delivered_source=checkpoint["source_revision"],
            source_changed=source_sha != checkpoint["source_revision"],
            status="owned-conflict"
            if report["owned_changes"]
            else "unmanaged-edits"
            if report["unmanaged_changes"]
            else "unchanged",
        )
    if (
        _head(target) != tip
        or _branch(target) != branch
        or _head(source_root) != source_sha
    ):
        raise ValueError("The observed Git revisions changed; take a fresh observation")
    return report


def main() -> int:
    evidence = Path(os.environ["IMPACT_EVIDENCE"]) / "drift.json"
    try:
        report = observe(
            Path(os.environ["IMPACT_CONSUMER"]),
            repository=os.environ["GITHUB_REPOSITORY"],
            config=os.environ["INPUT_CONFIG"],
            target_dir=os.environ["INPUT_TARGET_DIR"],
        )
        message = (
            f"Wiki status: {report['status']}. Owned file changes: {len(report['owned_changes'])}. "
            f"Unmanaged file changes: {len(report['unmanaged_changes'])}."
        )
        if report["source_changed"]:
            message += " The source differs from the delivery checkpoint; prepare a candidate to compare the output."
    except (ValueError, OSError, KeyError) as exc:
        report = {
            "schema_version": "llm-wiki-drift/v1",
            "status": "indeterminate",
            "complete": False,
            "remote_verified": False,
            "error": str(exc),
        }
        message = "The wiki history could not be verified. Inspect drift.json before reconciling."
    evidence.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"status={report['status']}\npath={evidence.as_posix()}\n")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
        summary.write("\n## Sibling wiki drift\n\n" + message + "\n")
    return int(report["status"] in {"owned-conflict", "indeterminate"})


if __name__ == "__main__":
    raise SystemExit(main())
