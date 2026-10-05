"""Guarded snapshot inputs for opt-in discovery; no extraction or writes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

from .knowledge_artifacts import _decode_json_object
from .knowledge_model import parse_knowledge_index
from .knowledge_storage import ROOT_FILENAME, LOGICAL_SCHEMA, MAX_ROOT_BYTES, KnowledgeStorageError, canonical_bytes, digest
from .knowledge_storage_access import ScopedKnowledgeRead, capture_knowledge_slice
from .knowledge_storage_io import StorageReadSession
from .maintenance_protocol import ADOPTION_FILENAME, MaintenanceProtocolError, guard_maintenance_owner
from .maintenance_status import build_maintenance_status
from .search_source import captured_manifest
from .sync_manifest import MANIFEST_FILENAME, SyncManifest


@dataclass
class DiscoveryCapture:
    manifest: SyncManifest | None
    native_payload: dict[str, Any]
    recorded_reviews: dict[str, Any]
    wiki_reads: StorageReadSession
    native: ScopedKnowledgeRead | None
    absent_paths: tuple[str, ...]
    guard_marker_bytes: int = 0

    def finish(self):
        receipt = self.native.finish() if self.native is not None else None
        self.wiki_reads.recheck()
        for relative in self.absent_paths:
            path = self.wiki_reads.root / relative
            if path.exists() or path.is_symlink():
                raise KnowledgeStorageError("discovery", "Previously absent authority appeared", code="storage-mutation")
        # Reuse the typed captured owner. This guard independently rereads the
        # marker, whose bytes were also captured in wiki_reads and rechecked.
        marker = guard_maintenance_owner(self.wiki_reads.root, self.manifest) if self.manifest is not None else None
        if marker is not None:
            self.guard_marker_bytes += len(self.wiki_reads.observations[ADOPTION_FILENAME].content)
        self.wiki_reads.recheck()
        return receipt


def _optional_read(reads, relative, maximum, absent):
    try:
        return reads.read(relative, maximum)
    except KnowledgeStorageError as exc:
        if exc.code != "storage-missing":
            raise
        absent.append(relative)
        return None


def capture_discovery(wiki_root: Path, reads: StorageReadSession, pages_by_path: dict,
                      *, manifest: SyncManifest | None = None) -> DiscoveryCapture:
    """Read one adopted owner and one selected native concepts/sections slice."""
    absent = []
    marker_raw = _optional_read(reads, ADOPTION_FILENAME, 65_536, absent)
    if manifest is None:
        try:
            manifest = captured_manifest(reads)
        except KnowledgeStorageError as exc:
            if exc.code != "storage-missing" or (reads.root / MANIFEST_FILENAME).exists():
                raise
            absent.append(MANIFEST_FILENAME)
    if manifest is None:
        if marker_raw is not None:
            raise MaintenanceProtocolError("owner-missing", "Captured maintenance owner is missing; complete recovery is required")
        marker = None
    else:
        marker = guard_maintenance_owner(wiki_root, manifest)
    if marker_raw is None and marker is not None:
        raise KnowledgeStorageError("maintenance", "Marker appeared during discovery", code="storage-mutation")
    if marker_raw is not None and marker is None:
        raise KnowledgeStorageError("maintenance", "Marker disappeared during discovery", code="storage-mutation")
    if marker is not None and marker_raw != canonical_bytes(marker):
        raise KnowledgeStorageError("maintenance", "Guarded marker differs from captured bytes", code="storage-mutation")
    guard_bytes = len(marker_raw or b"")
    reviews = {"availability": "unadopted", "reason": "maintenance-not-adopted", "adoption_id": None,
               "state_hash": None, "by_path": {}}
    if marker is not None:
        assert manifest is not None and manifest.maintenance_state is not None
        report = build_maintenance_status(manifest.maintenance_state, marker, capture=None,
            analysis_scope="snapshot", native_prose_coherent=False)
        reviews.update(availability="ready", reason=None, adoption_id=report.payload["adoption_id"],
                       state_hash=report.payload["state_hash"])
        keys = {"record_id", "coordinate", "target", "recorded_status", "mapping", "reasons", "acknowledgment",
                "acknowledgment_history", "history_bounds", "effective_status", "recorded_basis", "qualification",
                "governance_effect", "expected_basis", "basis_available", "source_location"}
        for path in pages_by_path:
            scoped = report.for_path(path)
            rows = []
            for row in scoped["records"]:
                selected = {key: row[key] for key in keys if key in row}
                selected["recorded_target_presence"] = manifest.maintenance_state["observations"][row["record_id"]]["target_presence"]
                rows.append(selected)
            reviews["by_path"][path] = {"records": rows, "bounds": scoped["bounds"]}
    native_payload = {"availability": "unavailable", "reason": "native-absent", "root_hash": None,
        "lookup_complete": False, "validation_scope": None, "whole_store_validated": False, "concepts": []}
    root_raw = _optional_read(reads, ROOT_FILENAME, MAX_ROOT_BYTES, absent)
    native = None
    if root_raw is None and manifest is not None and manifest.artifact_hashes is not None:
        raise KnowledgeStorageError("root", "Declared committed knowledge root is missing", code="storage-mixed-generation")
    if root_raw is not None:
        if (manifest is None or manifest.artifact_hashes is None
                or manifest.artifact_hashes.knowledge_index_hash != digest(root_raw)):
            raise KnowledgeStorageError("root", "Native root has no matching captured generation", code="storage-mixed-generation")
        root = _decode_json_object(root_raw, "knowledge.root")
        schema = root.get("schema_version")
        if schema == LOGICAL_SCHEMA:
            try:
                parse_knowledge_index(root)
            except ValueError as exc:
                raise KnowledgeStorageError("root", "Invalid legacy knowledge model") from exc
            native_payload["reason"] = "selected-native-layout-unsupported"
        elif not isinstance(schema, str) or re.fullmatch(r"llm-wiki-knowledge/v[0-9]+", schema) is None:
            raise KnowledgeStorageError("root", "Invalid knowledge schema")
        elif schema not in {"llm-wiki-knowledge/v2", "llm-wiki-knowledge/v3", "llm-wiki-knowledge/v4"}:
            raise KnowledgeStorageError("root", "Unknown knowledge layout cannot be validated", code="unsupported-schema-version")
        else:
            native = capture_knowledge_slice(wiki_root, ["page:" + path for path in pages_by_path],
                max_bytes=8_388_608, max_records=1000, max_expanded_bytes=16_777_216,
                include_graph=False, collections=("concepts", "sections"))
            payload = native.slice.to_payload()
            if manifest is not None and native.manifest.artifact_hashes != manifest.artifact_hashes:
                raise KnowledgeStorageError("manifest", "Discovery owner differs from selected native owner", code="storage-mixed-generation")
            for path, text in native.markdown.items():
                if path in pages_by_path and pages_by_path[path]["content"] != text:
                    raise KnowledgeStorageError("discovery", "Selected Markdown differs from ranked input", code="storage-mutation")
            native_payload.update(availability="scoped", reason=None, root_hash=digest(root_raw),
                lookup_complete=payload["lookup_complete"], validation_scope=payload["validation_scope"],
                concepts=[row["value"] for row in payload["records"]["concepts"]])
    return DiscoveryCapture(manifest, native_payload, reviews, reads, native, tuple(absent), guard_bytes)
