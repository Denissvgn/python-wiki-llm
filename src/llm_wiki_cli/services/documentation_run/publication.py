"""Supervisor-owned binding between a documentation run and mapped public prose."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping
import unicodedata

from ..documentation_policy import capture_tree_baseline, hash_bytes
from ..documentation_review import DocumentationReviewLedger
from ..filesystem_guard import (
    atomic_write_private_bytes,
    ensure_guarded_directory,
    unlink_guarded_bytes,
)
from ..knowledge_evidence import hash_json
from ..knowledge_governance import governance_lock
from ..publication_candidate import _read_tree
from .contracts import (
    DocumentationAgentResult,
    DocumentationIntegrityError,
    DocumentationRun,
    DocumentationTransitionError,
    RUN_CONTROL_DIR,
    _utc_now,
)
from .workspace import (
    _read_json,
    _resolve_workspace_root_argument,
    _workspace_path,
    documentation_run_path,
    load_documentation_run,
)


MAPPED = "mapped-docs"
KEY = "mapped_publication"
BINDING = f"{RUN_CONTROL_DIR}/evidence/publication-binding.json"


def _hashes(files: Mapping[str, bytes]) -> dict[str, str]:
    return {path: hash_bytes(raw) for path, raw in files.items()}


def _binding(root: Path, run: DocumentationRun) -> dict[str, Any]:
    document = _read_json(_workspace_path(root, BINDING))
    identity = document.get("binding_id")
    if identity != run.extensions[KEY]["binding_id"] or identity != hash_json(
        {k: v for k, v in document.items() if k != "binding_id"}
    ):
        raise DocumentationIntegrityError("The mapped publication binding changed.")
    return document


def _initial_hashes(binding: Mapping[str, Any]) -> dict[str, str]:
    return {
        topic["source_document"]: topic["before_hash"] for topic in binding["topics"]
    }


def _documents(root: Path, run: DocumentationRun) -> dict[str, bytes]:
    files = _read_tree(_workspace_path(root, MAPPED))
    if set(files) != set(_initial_hashes(_binding(root, run))):
        raise DocumentationIntegrityError(
            "Mapped documents cannot be added, removed, or renamed."
        )
    for raw in files.values():
        raw.decode("utf-8")
        if b"\0" in raw:
            raise DocumentationIntegrityError(
                "Mapped documents must contain UTF-8 Markdown."
            )
    return files


def bind_publication_workspace(
    workspace: str | Path, *, binding: Mapping[str, Any], documents: Mapping[str, bytes]
) -> None:
    """Seed an undispatched external workspace with the explicitly mapped originals."""
    root = _resolve_workspace_root_argument(workspace)
    if not documentation_run_path(root).is_file():
        raise DocumentationTransitionError(
            "Prepare the documentation run before binding public documents."
        )
    with governance_lock(_workspace_path(root, RUN_CONTROL_DIR)):
        _bind_publication(root, binding, documents)


def _stage_publication_documents(staging: Path, documents: Mapping[str, bytes]) -> None:
    """Validate, copy and re-read each declared Markdown file before committing the binding."""
    for name, raw in documents.items():
        path = _workspace_path(staging, name)
        if not name.lower().endswith(".md") or b"\0" in raw:
            raise DocumentationIntegrityError(
                "Only mapped UTF-8 Markdown files can be imported."
            )
        raw.decode("utf-8")
        ensure_guarded_directory(path.parent, mode=0o700)
        atomic_write_private_bytes(path, raw, expected_existing=None)
    if _read_tree(staging) != documents:
        raise DocumentationIntegrityError(
            "Mapped inputs changed while preparing the workspace."
        )


def _bind_publication(
    root: Path, binding: Mapping[str, Any], documents: Mapping[str, bytes]
) -> None:
    from .integrity import _verify_read_only_inputs

    run_path = documentation_run_path(root)
    original = run_path.read_bytes()
    run = load_documentation_run(root)
    _verify_read_only_inputs(root, run)
    if run.baseline.get("freshness") != "verified_current":
        raise DocumentationTransitionError(
            "Mapped publication requires verified-current workspace evidence."
        )
    identity = binding.get("binding_id")
    if (
        binding.get("schema_version") != "llm-wiki-publication-maintenance-binding/v1"
        or identity
        != hash_json({k: v for k, v in binding.items() if k != "binding_id"})
        or not documents
        or _initial_hashes(binding) != _hashes(documents)
    ):
        raise DocumentationIntegrityError(
            "Mapped documents do not match their publication binding."
        )
    if KEY in run.extensions:
        if _binding(root, run) != binding:
            raise DocumentationIntegrityError(
                "A different binding requires a fresh documentation workspace."
            )
        if not run.stage_attempts:
            wiki = capture_tree_baseline(root / "wiki", display="wiki")
            publication_packet(root, run, wiki.tree_hash)
        return
    if run.state != "baseline_ready" or run.stage_attempts:
        raise DocumentationTransitionError(
            "Bind the mapped documents before the first worker packet."
        )
    initial_wiki = _read_json(_workspace_path(root, run.evidence["wiki_baseline"]))[
        "tree_hash"
    ]
    if capture_tree_baseline(root / "wiki", display="wiki").tree_hash != initial_wiki:
        raise DocumentationIntegrityError(
            "Workspace wiki changed before publication preparation."
        )
    destination = _workspace_path(root, MAPPED)
    marker = _workspace_path(root, BINDING)
    marker_bytes = (json.dumps(binding, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    recovering = marker.is_file() and marker.read_bytes() == marker_bytes
    if (os.path.lexists(destination) or os.path.lexists(marker)) and not recovering:
        raise DocumentationIntegrityError(
            "The mapped workspace is occupied by another binding."
        )
    with TemporaryDirectory(prefix=".mapped-docs-", dir=root) as scratch:
        staging = Path(scratch) / MAPPED
        _stage_publication_documents(staging, documents)
        run.extensions[KEY] = {
            "binding_id": identity,
            "documents": _hashes(documents),
            "wiki_tree_hash": initial_wiki,
            "authors": [],
            "artifacts": {},
        }
        run.evidence["publication_binding"] = BINDING
        run.updated_at = _utc_now()
        payload = run.to_dict()
        DocumentationRun.from_dict(payload)
        updated = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
        if not recovering:
            atomic_write_private_bytes(marker, marker_bytes, expected_existing=None)
        installed = False
        try:
            if not os.path.lexists(destination):
                staging.rename(destination)
                installed = True
            elif _read_tree(destination) != documents:
                raise DocumentationIntegrityError(
                    "Interrupted publication binding differs from the requested documents."
                )
            atomic_write_private_bytes(run_path, updated, expected_existing=original)
        except BaseException:
            # A post-replacement fault may leave the new run authoritative.
            if run_path.read_bytes() != updated:
                if installed and _read_tree(destination) == documents:
                    destination.rename(staging)
                if not recovering and not os.path.lexists(destination):
                    unlink_guarded_bytes(marker, expected=marker_bytes)
            raise


def publication_packet(
    root: Path, run: DocumentationRun, wiki_tree_hash: str
) -> dict[str, Any]:
    """Check the last accepted workspace before another packet can redefine its baseline."""
    state = run.extensions[KEY]
    files = _documents(root, run)
    if (
        _hashes(files) != state["documents"]
        or wiki_tree_hash != state["wiki_tree_hash"]
    ):
        raise DocumentationIntegrityError(
            "Publication workspace changed outside a recorded worker stage."
        )
    for path, digest in state["artifacts"].items():
        if hash_bytes(_workspace_path(root, path).read_bytes()) != digest:
            raise DocumentationIntegrityError(
                "A recorded publication packet, result or review ledger changed."
            )
    return {
        "binding_id": state["binding_id"],
        "binding_path": BINDING,
        "root": MAPPED,
        "documents": state["documents"],
        "topics": [
            {
                "id": t["id"],
                "source_document": t["source_document"],
                "wiki_page": t["wiki_page"],
            }
            for t in _binding(root, run)["topics"]
        ],
    }


def protected_stage_hash(root: Path, stage: str, event: Path) -> str:
    """Cover supervisor controls, site outputs and unexpected workspace files."""
    files = capture_tree_baseline(root, display="publication workspace").file_hashes
    writable = {
        event.relative_to(root).as_posix(),
        f"{RUN_CONTROL_DIR}/results/{stage}.json",
    }
    return hash_json(
        {
            name: value
            for name, value in files.items()
            if name not in writable and not name.startswith(("wiki/", MAPPED + "/"))
        }
    )


def reconcile_publication(
    root: Path,
    run: DocumentationRun,
    result: DocumentationAgentResult,
    actor: str | None,
    actual_wiki_changes: list[str],
) -> dict[str, Any]:
    """Reconcile the author's precise write scope and the reviewer's read-only scope."""
    if (
        not isinstance(actor, str)
        or not actor.strip()
        or len(actor.encode("utf-8")) > 256
        or any(ord(char) < 32 or ord(char) == 127 for char in actor)
    ):
        raise DocumentationTransitionError(
            "The supervisor must name the actor recording each mapped stage."
        )
    actor = unicodedata.normalize("NFC", actor.strip())
    if actor.casefold() == "host-supervisor":
        raise DocumentationTransitionError(
            "The host supervisor identity is reserved for verification."
        )
    state = run.extensions[KEY]
    current = _hashes(_documents(root, run))
    changed = sorted(
        p for p, digest in current.items() if digest != state["documents"][p]
    )
    if result.stage != "user-docs" and changed:
        raise DocumentationIntegrityError(
            "Only the user-docs author may edit mapped documents."
        )
    if result.stage == "user-docs" and actual_wiki_changes:
        raise DocumentationIntegrityError(
            "Mapped authors may only edit their assigned document copies."
        )
    if sorted(result.changed_document_paths) != changed:
        raise DocumentationIntegrityError(
            "Reported changed_document_paths differ from the mapped document edits."
        )
    if result.stage == "review" and actor.casefold() in {
        a.casefold() for a in state["authors"]
    }:
        raise DocumentationTransitionError(
            "The independent reviewer must differ from every documentation author."
        )
    if result.stage in {"user-docs", "review"} and result.status == "complete":
        if not result.claims_evidence_pages:
            raise DocumentationTransitionError(
                "A completed mapped stage must cite its native evidence pages."
            )
        if any(
            current[p] == digest
            for p, digest in _initial_hashes(_binding(root, run)).items()
        ):
            raise DocumentationTransitionError(
                "Every selected topic needs a reviewed edit to its mapped document."
            )
    return {
        "actor": actor,
        "binding_id": state["binding_id"],
        "documents": current,
        "changed": changed,
    }


def record_publication_evidence(
    root: Path,
    run: DocumentationRun,
    stage: str,
    record: Mapping[str, Any],
    wiki_tree_hash: str,
) -> None:
    state = run.extensions[KEY]
    if stage != "review" and record["actor"] not in state["authors"]:
        state["authors"].append(record["actor"])
    state["documents"] = record["documents"]
    state["wiki_tree_hash"] = wiki_tree_hash
    for key in (f"{stage}_packet", f"{stage}_result", "review_ledger"):
        path = run.evidence.get(key)
        if path:
            state["artifacts"][path] = hash_bytes(
                _workspace_path(root, path).read_bytes()
            )


def reviewed_publication(
    root: Path, run: DocumentationRun, *, approved: bool
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Read the same accepted bytes and independent packet/result hashes that were reconciled."""
    from .integrity import _verify_read_only_inputs

    if (
        run.state != "review"
        or not run.evidence.get("review_result")
        or not run.evidence.get("review_ledger")
    ):
        raise DocumentationTransitionError(
            "Complete the user-docs and independent review stages before patching."
        )
    _verify_read_only_inputs(root, run)
    wiki = capture_tree_baseline(root / "wiki", display="reviewed wiki")
    publication_packet(root, run, wiki.tree_hash)
    ledger = DocumentationReviewLedger.from_dict(
        _read_json(_workspace_path(root, run.evidence["review_ledger"]))
    )
    if (
        ledger.run_id != run.run_id
        or ledger.unresolved_findings
        or ledger.state
        not in (
            {"publish_ready"} if approved else {"awaiting_supervisor", "publish_ready"}
        )
    ):
        raise DocumentationTransitionError(
            "The mapped review requires a clean ledger and supervisor verification."
        )
    for key in ("ci_check", "lint"):
        if not _read_json(_workspace_path(root, run.evidence[key])).get("ok"):
            raise DocumentationIntegrityError(
                "Mapped review requires successful lifecycle-owned wiki checks."
            )
    if not _read_json(_workspace_path(root, run.evidence["semantic_readiness"])).get(
        "passed"
    ):
        raise DocumentationIntegrityError(
            "Mapped review requires completed semantic readiness."
        )
    files = _documents(root, run)
    hashes = _hashes(files)
    identity = {
        "run_id": run.run_id,
        "binding_id": run.extensions[KEY]["binding_id"],
        "mapped_files": hashes,
    }
    for name, stage, packet in (
        ("author", "user-docs", ledger.worker_packets[-1]),
        ("reviewer", "review", ledger.reviewer_packets[-1]),
    ):
        result_path = _workspace_path(root, run.evidence[f"{stage}_result"])
        payload = _read_json(result_path)
        recorded = payload["reconciliation"]["mapped_publication"]
        if (
            payload["status"] != "complete"
            or payload["run_id"] != run.run_id
            or recorded["documents"] != hashes
            or recorded["binding_id"] != identity["binding_id"]
            or recorded["actor"] != packet.actor_id
            or packet.result_hash != hash_bytes(result_path.read_bytes())
            or packet.packet_hash
            != hash_bytes(
                _workspace_path(root, run.evidence[f"{stage}_packet"]).read_bytes()
            )
        ):
            raise DocumentationIntegrityError(
                "The accepted publication result does not describe these exact edits."
            )
        identity[name] = packet.actor_id
        identity[name + "_packet_hash"] = packet.packet_hash
        identity[name + "_result_hash"] = packet.result_hash
    if identity["reviewer"].casefold() in {
        a.casefold() for a in run.extensions[KEY]["authors"]
    }:
        raise DocumentationIntegrityError("Publication review is not independent.")
    return identity, files


def collect_reviewed_publication_edits(
    workspace: str | Path,
    *,
    binding: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, bytes]]:
    root = _resolve_workspace_root_argument(workspace)
    run = load_documentation_run(root)
    if KEY not in run.extensions or _binding(root, run) != binding:
        raise DocumentationIntegrityError(
            "This workspace does not match the current publication basis."
        )
    return reviewed_publication(root, run, approved=True)
