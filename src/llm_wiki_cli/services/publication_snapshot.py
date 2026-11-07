"""Complete, read-only native page commitments for documentation publication."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .contracts import GOVERNANCE_EXTENSION_KEY, SECTION_OWNERSHIP_EXTENSION_KEY
from .io import decode_markdown_bytes
from .knowledge_evidence import hash_json, sha256_bytes
from .knowledge_governance import GOVERNANCE_FILENAME
from .knowledge_model import _bundle_to_payload
from .knowledge_storage import MAX_EXPANDED_BYTES, KnowledgeStorageError
from .knowledge_storage_io import _absolute_path
from .knowledge_storage_lifecycle import _committed_inputs
from .markdown_sections import parse_markdown_document
from .maintenance_protocol import guard_maintenance_owner
from .sync_manifest import MANIFEST_FILENAME
from .wiki_surface import collect_wiki_pages


PUBLICATION_SNAPSHOT_SCHEMA_VERSION = "llm-wiki-publication-snapshot/v1"


class PublicationSnapshotError(ValueError):
    """A complete, coherent publication input could not be established."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def build_publication_snapshot(wiki_dir: str | Path) -> dict[str, Any]:
    """Commit every canonical native page without extracting source or writing.

    Current packed knowledge and indexed manifests use their validated readers.
    The result is complete for the canonical native page registry, including
    every ATX section, rather than a bounded search/query projection. Unmapped
    source evidence remains explicit: this is not a complete claim dependency
    graph and makes no live source freshness or semantic review assertion.
    """
    try:
        return _build_snapshot(_absolute_path(Path(wiki_dir)))
    except PublicationSnapshotError:
        raise
    except (OSError, ValueError, TypeError) as exc:
        code = getattr(exc, "code", None)
        raise PublicationSnapshotError(
            code if isinstance(code, str) else "publication-snapshot-invalid",
            "A complete valid native snapshot is required for publication.",
        ) from exc


def build_bootstrap_publication_snapshot(source_root: Path) -> dict[str, Any]:
    """Build an isolated source-adapter wiki and return its native commitments.

    The typed bootstrap accepts an external absolute source root and uses its
    ordinary source-selection discovery with one extraction worker. Plugins and
    automatic helper preparation are disabled; prepared helpers may be reused.
    Explicit packed storage avoids ephemeral maintenance-adoption identities.
    Bootstrap's generated history still records its execution date, so source
    and publication policy must account for that history when comparing dates.
    """
    from .bootstrap_runtime import execute_bootstrap
    from .bootstrap_service import BootstrapRequest, BootstrapServiceError
    from .helper_runtime import helper_operation

    try:
        source = _absolute_path(Path(source_root))
        if not source.is_dir():
            raise PublicationSnapshotError(
                "publication-bootstrap-source",
                "Bootstrap source must be an existing directory.",
            )
        with TemporaryDirectory(prefix="llm-wiki-publication-") as temporary:
            wiki = Path(temporary) / "wiki"
            with helper_operation("never"):
                execute_bootstrap(
                    BootstrapRequest(
                        source_root=source,
                        wiki_root=wiki,
                        source_adapter=True,
                        trust_source_plugins=False,
                        knowledge_format="packed-v4-deflate",
                    )
                )
            return build_publication_snapshot(wiki)
    except PublicationSnapshotError:
        raise
    except (OSError, ValueError, TypeError, BootstrapServiceError) as exc:
        raise PublicationSnapshotError(
            "publication-bootstrap-failed",
            "A complete isolated bootstrap snapshot could not be established.",
        ) from exc


def _build_snapshot(root: Path) -> dict[str, Any]:
    state, session, captured = _committed_inputs(root)
    assert state.knowledge is not None
    assert state.manifest_basis is not None
    assert state.validated_artifacts is not None
    knowledge = state.knowledge
    manifest = state.manifest_basis
    artifacts = state.validated_artifacts
    pages = []
    with session.phase():
        for concept in sorted(
            knowledge.concepts, key=lambda item: item.document.canonical_path
        ):
            path = concept.document.canonical_path
            raw = session.read(path, MAX_EXPANDED_BYTES)
            document = parse_markdown_document(
                decode_markdown_bytes(raw), concept.locator
            )
            if document.exact_hash != concept.facets.semantics.page_hash:
                raise KnowledgeStorageError(
                    path, "authored input changed", code="storage-mutation"
                )
            extension = concept.extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY)
            ownership = (
                {
                    section["locator"]: section
                    for section in extension.get("sections", [])
                }
                if isinstance(extension, Mapping)
                else {}
            )
            sections = []
            for section in document.sections:
                payload = section.to_payload()
                observed = ownership.get(section.locator, {})
                payload["ownership"] = observed.get("ownership", "unknown")
                for name in ("structural_hash", "semantic_hash"):
                    if observed.get(name) is not None:
                        payload[name] = observed[name]
                sections.append(payload)
            governance = concept.extensions.get(GOVERNANCE_EXTENSION_KEY)
            basis = concept.facets.structure.basis
            source_basis = (
                None
                if basis is None
                else {
                    "scope": basis.scope.value,
                    "source_path": basis.source_path,
                    "extractor_ref": basis.extractor_ref,
                    "source_content_hash": basis.source_content_hash,
                    "concept_observation_hash": basis.concept_observation_hash,
                    "aggregate_input_hash": basis.aggregate_input_hash,
                    "extensions": deepcopy(dict(basis.extensions)),
                }
            )
            mapping = manifest.page_source_mappings.get(path)
            pages.append(
                {
                    "canonical_path": path,
                    "kind": concept.document.page_kind.value,
                    "id": concept.document.page_id,
                    "locator": concept.locator,
                    "mcp_uri": concept.locator,
                    "uid": governance.get("uid")
                    if isinstance(governance, Mapping)
                    else None,
                    "role": concept.document.role.value,
                    "raw_hash": sha256_bytes(raw),
                    "normalized_hash": document.exact_hash,
                    "source_basis": source_basis,
                    "source_mapping": None if mapping is None else mapping.to_payload(),
                    "section_ordering_hash": document.ordering_hash,
                    "sections": sections,
                }
            )
    # Include every captured native root/object and page in the same final
    # guarded recheck. A mutation cannot yield a partial or apparently ready view.
    session.recheck()
    if {page.relative_path for page in collect_wiki_pages(root)} != {
        page["canonical_path"] for page in pages
    }:
        raise KnowledgeStorageError(
            "pages", "canonical page set changed", code="storage-mutation"
        )
    guard_maintenance_owner(root, manifest)
    if artifacts.governance_hash is None and os.path.lexists(
        root / GOVERNANCE_FILENAME
    ):
        raise KnowledgeStorageError(
            "governance", "uncommitted authority appeared", code="storage-mutation"
        )
    snapshot = knowledge.bundle.snapshot
    result = {
        "schema_version": PUBLICATION_SNAPSHOT_SCHEMA_VERSION,
        "complete": True,
        "coverage": {
            "scope": "canonical-native-pages",
            "page_count": len(pages),
            "section_model": "native-atx/v1",
            "source_mapping": "non-exhaustive",
        },
        "freshness": {"scope": "snapshot-only", "state": "not-evaluated"},
        "commitments": {
            "source_snapshot_hash": snapshot.source_snapshot_hash,
            "markdown_snapshot_hash": snapshot.markdown_snapshot_hash,
            "generation_options_hash": snapshot.generation_options_hash,
            "producer_hash": hash_json(
                _bundle_to_payload(knowledge.bundle)["producer"]
            ),
            "surface_index_hash": artifacts.surface_index_hash,
            "knowledge_index_hash": artifacts.knowledge_index_hash,
            "evaluated_envelope_hash": artifacts.evaluated_envelope_hash,
            "governance_hash": artifacts.governance_hash,
            "manifest_hash": sha256_bytes(captured[MANIFEST_FILENAME]),
            "manifest_storage_version": manifest.storage_version,
        },
        "pages": pages,
    }
    return {**result, "snapshot_id": hash_json(result)}
