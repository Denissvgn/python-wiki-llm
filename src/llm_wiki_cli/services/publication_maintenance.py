"""Turn independently reviewed workspace edits into consumer-owned Markdown patches."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import difflib
from io import StringIO
import json
import os.path
from pathlib import Path
from typing import Any

from .documentation_run.integrity import _verify_read_only_inputs
from .documentation_run.workspace import (
    _load_bound_runtime_policy,
    load_documentation_run,
)
from .knowledge_evidence import hash_json, sha256_bytes
from .knowledge_storage_io import StorageReadSession, _absolute_path
from .publication_candidate import (
    MAX_FILE_BYTES,
    MAX_TREE_BYTES,
    _candidate_path,
    _hashes,
    _read_tree,
    check_publication_candidate,
)
from .publication_config import (
    PUBLICATION_CONFIG_PATH,
    publication_control_overlap,
    publication_path,
)
from .publication_links import check_github_wiki, prepare_wiki_markdown
from .source_selection import resolve_source_selection


_BINDING_SCHEMA = "llm-wiki-publication-maintenance-binding/v1"
_PROPOSAL_SCHEMA = "llm-wiki-publication-maintenance/v1"
_MAX_TOPICS = 32
_MAX_BINDING_BYTES = 1_000_000


def _binding(checked, topic_ids):
    impact = checked["impact"]
    if not impact["complete"]:
        raise ValueError(
            "Repair incomplete publication evidence before semantic maintenance"
        )
    findings = {
        f["subject"]: f
        for f in impact["findings"]
        if f["kind"] == "topic" and f["status"] == "needs-review"
    }
    topics = {
        t["id"]: t
        for t in checked["basis"]["config"]["topics"]
        if t["edit_at"] == "repository" and t["id"] in findings
    }
    if topic_ids is not None:
        if (
            not isinstance(topic_ids, Sequence)
            or isinstance(topic_ids, (str, bytes))
            or not topic_ids
            or not all(isinstance(key, str) and key for key in topic_ids)
            or len(set(topic_ids)) != len(topic_ids)
        ):
            raise ValueError("Select distinct nonempty topic IDs")
        if set(topic_ids) - topics.keys():
            raise ValueError(
                "Every selected topic must be a current repository-owned topic needing review"
            )
        topics = {key: topics[key] for key in topic_ids}
    if len(topics) > _MAX_TOPICS:
        raise ValueError(
            f"Select at most {_MAX_TOPICS} topics per maintenance workspace"
        )
    selected = []
    for key, topic in sorted(topics.items()):
        path = topic["source_document"]
        selected.append(
            {
                "id": key,
                "owner": topic["owner"],
                "wiki_page": topic["wiki_page"],
                "source_document": path,
                "before_hash": checked["basis"]["files"][path],
                "depends_on": topic["depends_on"],
                "finding": findings[key],
            }
        )
    binding = {
        "schema_version": _BINDING_SCHEMA,
        "candidate_id": checked["candidate_id"],
        "receipt_id": checked["receipt_id"],
        "config_hash": checked["config_hash"],
        "basis_id": checked["basis"]["basis_id"],
        "impact_id": impact["report_id"],
        "topics": selected,
    }
    if (
        len(json.dumps(binding, ensure_ascii=False).encode("utf-8"))
        > _MAX_BINDING_BYTES
    ):
        raise ValueError(
            "Selected topic evidence exceeds the maintenance packet budget; narrow the selection"
        )
    return {**binding, "binding_id": hash_json(binding)}


def _validate_workspace(workspace, root, candidate_dir, config):
    if any(
        publication_control_overlap(workspace, path)
        for path in (root, _candidate_path(root, candidate_dir))
    ):
        raise ValueError(
            "Prepare a documentation workspace outside the consumer checkout and candidate tree"
        )
    run = load_documentation_run(workspace)
    runtime = _load_bound_runtime_policy(workspace, run)
    if (
        run.baseline.get("freshness") != "verified_current"
        or run.baseline.get("freshness_policy") != "require-current"
        or run.policy.get("source_plugins_trusted")
    ):
        raise ValueError(
            "Semantic maintenance requires a verified-current workspace prepared without source plugins"
        )
    arch = config["architecture"]
    architecture_root = publication_path(root, arch["root"])
    source = runtime["source_root"]
    if source is None or not source.is_dir() or not source.is_relative_to(root):
        raise ValueError(
            "The documentation workspace must be based on this consumer's source"
        )
    if arch["baseline"] == "bootstrap-source":
        if run.baseline_strategy != "bootstrap_source" or source != architecture_root:
            raise ValueError(
                "The workspace source must match the publication bootstrap root"
            )
        selection = resolve_source_selection(source)
        if run.policy.get("source_selection") != (
            None if selection is None else selection.identity
        ):
            raise ValueError(
                "The workspace source selection differs from the publication source selection"
            )
    elif (
        run.baseline_strategy != "adopt_existing_wiki"
        or runtime["input_wiki_root"] != architecture_root
        or (
            "source_root" in arch
            and source != publication_path(root, arch["source_root"])
        )
    ):
        raise ValueError(
            "The workspace must adopt the configured native wiki and verify its source"
        )
    _verify_read_only_inputs(workspace, run)
    return run.run_id


def _line_count(text: str) -> int:
    return text.count("\n") + int(bool(text) and not text.endswith("\n"))


def _linear_hunk(old: str, new: str, old_name: str, new_name: str):
    """Use a single contextual hunk without quadratic matching of long documents."""
    shared = len(os.path.commonprefix((old, new)))
    first = old.rfind("\n", 0, shared) + 1
    tail = len(os.path.commonprefix((old[first:][::-1], new[first:][::-1])))
    end_old, end_new = len(old) - tail, len(new) - tail
    if tail and not (
        (end_old == 0 or old[end_old - 1] == "\n")
        and (end_new == 0 or new[end_new - 1] == "\n")
    ):
        # A matching partial last line belongs to the edit.
        newline = old.find("\n", end_old)
        skip = len(old) - end_old if newline < 0 else newline + 1 - end_old
        end_old += skip
        end_new += skip
    start, stop = first, end_old
    for _ in range(3):
        start = old.rfind("\n", 0, max(0, start - 1)) + 1
        newline = old.find("\n", stop)
        stop = len(old) if newline < 0 else newline + 1
    leading, trailing = old[start:first], old[end_old:stop]
    removed, added = old[first:end_old], new[first:end_new]
    context = _line_count(leading) + _line_count(trailing)
    left, right = context + _line_count(removed), context + _line_count(added)
    preceding = old.count("\n", 0, start)
    yield f"--- {old_name}\n"
    yield f"+++ {new_name}\n"
    yield f"@@ -{preceding + bool(left)},{left} +{preceding + bool(right)},{right} @@\n"
    for prefix, segment in (
        (" ", leading),
        ("-", removed),
        ("+", added),
        (" ", trailing),
    ):
        for line in StringIO(segment, newline="\n"):
            yield prefix + line


def _document_patch(path: str, before: bytes, after: bytes) -> str:
    if type(after) is not bytes or len(after) > MAX_FILE_BYTES or b"\0" in after:
        raise ValueError(
            "Reviewed Markdown must be bounded UTF-8 text without NUL bytes"
        )
    old, new = before.decode("utf-8"), after.decode("utf-8")
    # Git splits at LF only. Preserve CR, Unicode separators and a missing final LF.
    old_name, new_name = (
        json.dumps(prefix + path, ensure_ascii=False) for prefix in ("a/", "b/")
    )
    rows, columns = _line_count(old), _line_count(new)
    if max(rows, columns) <= 20_000 and rows * columns <= 4_000_000:
        hunk = difflib.unified_diff(
            list(StringIO(old, newline="\n")),
            list(StringIO(new, newline="\n")),
            fromfile=old_name,
            tofile=new_name,
        )
    else:
        hunk = _linear_hunk(old, new, old_name, new_name)
    stream = StringIO(newline="\n")
    stream.write(f"diff --git {old_name} {new_name}\n")
    for line in hunk:
        stream.write(line)
        if not line.endswith("\n"):
            stream.write("\n\\ No newline at end of file\n")
    return stream.getvalue()


def _checked_preview(candidate: Path, checked, edited):
    files = _read_tree(candidate)
    if _hashes(files) != checked["files"]:
        raise ValueError(
            "Candidate tree changed before validation of the proposed patch"
        )
    pages = {}
    assets = {}
    for output, owner in checked["ownership"].items():
        mappings = pages if owner["kind"] == "page" else assets
        mappings[owner["source_document"]] = output
    for source, raw in edited.items():
        files[pages[source]] = prepare_wiki_markdown(
            raw.decode("utf-8"),
            source_path=source,
            source_pages=pages,
            source_assets=assets,
            repository_url=checked["basis"]["config"]["content"].get("repository_url"),
            source_revision=checked["context"]["source_revision"],
        ).encode("utf-8")
    checks = check_github_wiki(files)
    if not checks["ok"]:
        first = checks["findings"][0]
        raise ValueError(
            f"Patched candidate failed its wiki checks: {first['path']}: {first['message']}"
        )
    return hash_json(_hashes(files))


def _maintenance(
    root, workspace, candidate_dir, receipt, topic_ids, options, *, produce_patch
):
    from .documentation_run.publication import (
        bind_publication_workspace,
        collect_reviewed_publication_edits,
    )

    root = _absolute_path(Path(root))
    workspace = _absolute_path(Path(workspace))
    checked = check_publication_candidate(
        root, candidate_dir=candidate_dir, receipt=receipt, **options
    )
    if checked["receipt_id"] != receipt["receipt_id"]:
        raise ValueError(
            "Supply the rechecked receipt and its exact baseline and review inputs"
        )
    binding = _binding(checked, topic_ids)
    result = {
        "schema_version": _PROPOSAL_SCHEMA,
        "binding": binding,
        "ready_for_repository_review": False,
        "delivery_ready": False,
    }
    if not binding["topics"]:
        if produce_patch:
            raise ValueError(
                "There are no unresolved repository-owned topic edits to patch"
            )
        return {
            **result,
            "status": "no-mapped-findings",
            "next_actions": [
                "Inspect the impact report for manual topics or coverage gaps."
            ],
        }
    result["run_id"] = _validate_workspace(
        workspace, root, candidate_dir, checked["basis"]["config"]
    )
    session = StorageReadSession(root, max_bytes=3 * MAX_TREE_BYTES)
    documents = {}
    with session.phase():
        for topic in binding["topics"]:
            path = topic["source_document"]
            raw = session.read(path, MAX_FILE_BYTES)
            if sha256_bytes(raw) != topic["before_hash"]:
                raise ValueError(
                    f"Canonical Markdown changed since the checked receipt: {path}"
                )
            documents[path] = raw
    if not produce_patch:
        session.recheck()
        bind_publication_workspace(workspace, binding=binding, documents=documents)
        return {
            **result,
            "status": "awaiting-workspace-review",
            "next_actions": [
                "Follow docs status and dispatch the bounded workspace packets to your configured host.",
                "Record the author result and a separate review result for the exact edited Markdown.",
                "Run docs verify, then docs wiki patch using the same candidate, inputs and topic selection.",
            ],
        }

    review, edited = collect_reviewed_publication_edits(workspace, binding=binding)
    if set(edited) != set(documents):
        raise ValueError(
            "The reviewed edit inventory differs from the bound source documents"
        )
    if (
        review["mapped_files"] != _hashes(edited)
        or review["binding_id"] != binding["binding_id"]
    ):
        raise ValueError("Workspace review does not bind these exact edited bytes")
    parts, changes = [], []
    total = 0
    for path, original in sorted(documents.items()):
        updated = edited[path]
        if not updated.decode("utf-8").strip() or (
            updated.replace(b"\r\n", b"\n").rstrip(b"\n")
            == original.replace(b"\r\n", b"\n").rstrip(b"\n")
        ):
            raise ValueError(
                f"No reviewed prose change for {path}; resolve a still-current topic separately"
            )
        patch = _document_patch(path, original, updated)
        total += len(patch.encode("utf-8"))
        if total > MAX_TREE_BYTES:
            raise ValueError(
                "Patch exceeds the publication byte budget; narrow the topic selection"
            )
        parts.append(patch)
        changes.append(
            {
                "path": path,
                "before_hash": sha256_bytes(original),
                "after_hash": sha256_bytes(updated),
            }
        )
    preview_hash = _checked_preview(
        _candidate_path(root, candidate_dir), checked, edited
    )
    # Recheck both sides after composing and validating the artifact.
    session.recheck()
    current = check_publication_candidate(
        root, candidate_dir=candidate_dir, receipt=checked, **options
    )
    if current["receipt_id"] != checked["receipt_id"]:
        raise ValueError("Publication inputs changed during semantic patch preparation")
    final_review, final_documents = collect_reviewed_publication_edits(
        workspace, binding=binding
    )
    if final_review != review or final_documents != edited:
        raise ValueError("Reviewed workspace changed while constructing the patch")
    patch_text = "".join(parts)
    proposal = {
        **result,
        "status": "patch-proposed",
        "ready_for_repository_review": True,
        "preview_tree_hash": preview_hash,
        "review": review,
        "changes": changes,
        "patch_sha256": sha256_bytes(patch_text.encode("utf-8")),
    }
    return {**proposal, "proposal_id": hash_json(proposal), "patch": patch_text}


def prepare_publication_maintenance(
    consumer_root: str | Path = ".",
    *,
    workspace: str | Path,
    candidate_dir: str | Path,
    receipt: Mapping[str, Any],
    topic_ids: Sequence[str] | None = None,
    config_path: str | Path = PUBLICATION_CONFIG_PATH,
    target_dir: str | Path | None = None,
    baseline: Mapping[str, Any] | None = None,
    reviews: Mapping[str, Any] | None = None,
    previous_receipt: Mapping[str, Any] | None = None,
    candidate_review: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Seed a prepared documentation workspace with unresolved mapped source text."""
    return _maintenance(
        consumer_root,
        workspace,
        candidate_dir,
        receipt,
        topic_ids,
        dict(
            config_path=config_path,
            target_dir=target_dir,
            baseline=baseline,
            reviews=reviews,
            previous_receipt=previous_receipt,
            candidate_review=candidate_review,
        ),
        produce_patch=False,
    )


def build_publication_patch(
    consumer_root: str | Path = ".",
    *,
    workspace: str | Path,
    candidate_dir: str | Path,
    receipt: Mapping[str, Any],
    topic_ids: Sequence[str] | None = None,
    config_path: str | Path = PUBLICATION_CONFIG_PATH,
    target_dir: str | Path | None = None,
    baseline: Mapping[str, Any] | None = None,
    reviews: Mapping[str, Any] | None = None,
    previous_receipt: Mapping[str, Any] | None = None,
    candidate_review: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Propose an exact Git patch from verified author and independent review results."""
    return _maintenance(
        consumer_root,
        workspace,
        candidate_dir,
        receipt,
        topic_ids,
        dict(
            config_path=config_path,
            target_dir=target_dir,
            baseline=baseline,
            reviews=reviews,
            previous_receipt=previous_receipt,
            candidate_review=candidate_review,
        ),
        produce_patch=True,
    )
