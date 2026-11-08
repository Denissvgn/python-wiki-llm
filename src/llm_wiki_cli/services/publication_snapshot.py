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
from .validation import require_portable_relative_path


PUBLICATION_SNAPSHOT_SCHEMA_VERSION = "llm-wiki-publication-snapshot/v1"


class PublicationSnapshotError(ValueError):
    """A complete, coherent publication input could not be established."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def _output_payload_path(value: object) -> str:
    return require_portable_relative_path(value)


def assert_bootstrap_output_excluded(
    source_root: Path, destination: Path, files: Mapping[str, bytes]
) -> None:
    """Reject future output files that would become bootstrap producer inputs.

    Only prospective source, infrastructure, package or selection inputs need
    an exclusion. Ordinary Markdown and public media remain usable beneath a
    source root. This reads the consumer's current selection; it never edits
    ignore rules or silently adds an exclusion.
    """
    from ..config import EXCLUDED_DIRS, GitIgnoreMatcher, is_agent_worktree_path
    from .source_snapshot import (
        _is_compose_candidate,
        _is_dockerfile_candidate,
        _is_package_marker,
        _is_rescuable_typescript_src_lib_file,
        _language_for_path,
        _unsupported_language_for_path,
        build_source_snapshot,
    )

    source = _absolute_path(Path(source_root))
    output = _absolute_path(Path(destination))
    try:
        prefix = output.relative_to(source)
    except ValueError:
        prefix = None
        # On case-insensitive filesystems, lexical ancestors can spell the
        # same existing source root differently. Compare actual identities.
        if source.exists():
            for ancestor in (output, *output.parents):
                if ancestor.exists() and ancestor.samefile(source):
                    prefix = output.relative_to(ancestor)
                    break
        if prefix is None:
            return
    if not isinstance(files, Mapping):
        raise ValueError("Bootstrap output requires a file mapping")
    prospective = []
    for raw_path, raw in files.items():
        path = Path(_output_payload_path(raw_path))
        if type(raw) is not bytes:
            raise ValueError("Bootstrap output file values must be bytes")
        relative = prefix / path
        if not EXCLUDED_DIRS.isdisjoint(relative.parts) or is_agent_worktree_path(
            relative
        ):
            continue
        # Language test files are conservatively potential producer inputs too.
        language = _language_for_path(relative, frozenset({"go"}))
        if (
            language is not None
            or _unsupported_language_for_path(relative) is not None
            or _is_dockerfile_candidate(relative)
            or _is_compose_candidate(relative)
            or _is_package_marker(relative)
            or relative.suffix.lower() in {".yml", ".yaml"}
            or relative.name in {"Kustomization", ".gitignore"}
        ):
            prospective.append((relative, language))
    if not prospective:
        return
    snapshot = build_source_snapshot(
        source, respect_ignores=True, respect_discovery=True, coherent=True
    )
    ignored = GitIgnoreMatcher(list(snapshot.gitignore_rules))
    for relative, language in prospective:
        name = relative.as_posix()
        if snapshot.source_selection_policy is not None:
            selected = snapshot.path_is_effectively_selected(name)
        else:
            selected = not ignored.is_ignored(
                name
            ) or _is_rescuable_typescript_src_lib_file(ignored, relative, language)
        if selected:
            raise ValueError(
                "Candidate output would become a bootstrap source input: "
                f"{name}. Choose an excluded output location or explicitly "
                "exclude it through the consumer's source selection or ignore policy."
            )


def build_publication_snapshot(
    wiki_dir: str | Path, *, source_root: Path | None = None
) -> dict[str, Any]:
    """Commit every canonical native page and optionally verify its live source.

    Current packed knowledge and indexed manifests use their validated readers.
    The result is complete for the canonical native page registry, including
    every ATX section, rather than a bounded search/query projection. Unmapped
    source evidence remains explicit: this is not a complete claim dependency
    graph. Without an explicit source root, freshness remains snapshot-only.
    """
    try:
        return _build_snapshot(_absolute_path(Path(wiki_dir)), source_root)
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
    Temporary history identifies the configured source root independently of
    the execution date and working directory; its full contents are committed.
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
                    ),
                    publication_snapshot=True,
                )
            return build_publication_snapshot(wiki)
    except PublicationSnapshotError:
        raise
    except (OSError, ValueError, TypeError, BootstrapServiceError) as exc:
        raise PublicationSnapshotError(
            "publication-bootstrap-failed",
            "A complete isolated bootstrap snapshot could not be established.",
        ) from exc


def _build_snapshot(root: Path, source_root: Path | None = None) -> dict[str, Any]:
    state, session, captured = _committed_inputs(root)
    assert state.knowledge is not None
    assert state.manifest_basis is not None
    assert state.validated_artifacts is not None
    knowledge = state.knowledge
    manifest = state.manifest_basis
    artifacts = state.validated_artifacts
    freshness = {"scope": "snapshot-only", "state": "not-evaluated"}
    if source_root is not None:
        from .documentation_native import (
            DocumentationNativeError,
            evaluate_documentation_native_freshness,
        )
        from .helper_runtime import helper_operation

        try:
            with helper_operation("never"):
                live = evaluate_documentation_native_freshness(
                    knowledge=knowledge,
                    manifest=manifest,
                    source_root=source_root,
                    trust_source_plugins=False,
                )
        except DocumentationNativeError as exc:
            raise PublicationSnapshotError(
                "publication-native-freshness", str(exc)
            ) from exc
        if not live.current:
            raise PublicationSnapshotError(
                "publication-native-stale",
                "Native wiki evidence is stale for architecture.source_root: "
                + ", ".join(live.reasons[:5]),
            )
        freshness = {"scope": "live-source", "state": "verified-current"}
    extension = knowledge.extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY)
    ownership_by_page = (
        {
            page["page_locator"]: {
                section["locator"]: section for section in page["sections"]
            }
            for page in extension.get("pages", [])
        }
        if isinstance(extension, Mapping)
        else {}
    )
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
            ownership = ownership_by_page.get(concept.locator, {})
            sections = []
            for section in document.sections:
                payload = section.to_payload()
                observed = ownership.get(section.locator, {})
                if observed and observed["exact_hash"] != section.exact_hash:
                    raise KnowledgeStorageError(
                        path, "section commitment differs", code="storage-mutation"
                    )
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
            preamble_locator = concept.locator + "#section/@preamble"
            preamble = ownership.get(preamble_locator)
            if preamble is not None:
                extent = (
                    document.sections[0].start_byte
                    if document.sections
                    else len(document.normalized_bytes)
                )
                if preamble["exact_hash"] != sha256_bytes(
                    document.normalized_bytes[:extent]
                ):
                    raise KnowledgeStorageError(
                        path, "preamble commitment differs", code="storage-mutation"
                    )
                pages[-1]["preamble"] = {
                    "locator": preamble_locator,
                    "page_locator": concept.locator,
                    "exact_hash": preamble["exact_hash"],
                    "ownership": preamble["ownership"],
                    **{
                        key: preamble[key]
                        for key in ("structural_hash", "semantic_hash")
                        if preamble.get(key) is not None
                    },
                }
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
        "freshness": freshness,
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
