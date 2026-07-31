"""Authoritative validation and fallback boundary for generated knowledge state."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any

from .io import read_md
from .knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    KnowledgeArtifactError,
    validate_knowledge_artifacts,
    validate_surface_index_bytes,
)
from .knowledge_envelope import KnowledgeEnvelopeError, hash_markdown_snapshot
from .knowledge_model import KnowledgeIndex, KnowledgeLoadState
from .knowledge_governance import (
    GOVERNANCE_EXTENSION_KEY,
    GOVERNANCE_FILENAME,
    GovernanceError,
    load_governance,
    validate_governance_projection,
)
from .sync_manifest import (
    MANIFEST_FILENAME,
    SyncManifest,
    SyncManifestError,
)
from .wiki_surface import collect_wiki_pages
from .wiki_surface_index import SURFACE_INDEX_FILENAME


class KnowledgeMismatchPolicy(str, Enum):
    """Caller-selected behavior when a present artifact set is not valid."""

    REJECT = "reject"
    REBUILD = "rebuild"
    DEGRADED = "degraded"


@dataclass(frozen=True)
class KnowledgeLoadIssue:
    """One stable, path-safe artifact load diagnostic."""

    code: str
    artifact_path: str
    message: str
    field: str | None = None


@dataclass(frozen=True)
class KnowledgeLoadResult:
    """Validated knowledge state or an explicit compatibility fallback."""

    status: KnowledgeLoadState
    surface: Mapping[str, Any] | None
    knowledge: KnowledgeIndex | None
    manifest_basis: SyncManifest | None
    issues: tuple[KnowledgeLoadIssue, ...] = ()
    underlying_status: KnowledgeLoadState | None = None
    rebuilt: bool = False


class KnowledgeStateLoadError(ValueError):
    """Raised by reject/rebuild policy when no valid state can be returned."""

    def __init__(
        self,
        status: KnowledgeLoadState,
        issues: tuple[KnowledgeLoadIssue, ...],
    ):
        self.status = status
        self.issues = issues
        details = "; ".join(
            f"{issue.code} ({issue.artifact_path}): {issue.message}" for issue in issues
        )
        super().__init__(
            f"knowledge state is {status.value}" + (f": {details}" if details else "")
        )


RebuildCallback = Callable[[tuple[KnowledgeLoadIssue, ...]], None]


def load_knowledge_state(
    wiki_dir: str | Path,
    *,
    policy: KnowledgeMismatchPolicy | str = KnowledgeMismatchPolicy.REJECT,
    rebuild_callback: RebuildCallback | None = None,
    markdown_pages: Mapping[str, str | bytes] | None = None,
) -> KnowledgeLoadResult:
    """Load one coherent surface/knowledge/manifest state.

    The loader never writes.  A rebuild policy must supply an explicit callback;
    it is invoked at most once, after which the filesystem is read and validated
    again under reject semantics.
    """

    try:
        selected_policy = (
            policy
            if isinstance(policy, KnowledgeMismatchPolicy)
            else KnowledgeMismatchPolicy(policy)
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("policy must be 'reject', 'rebuild', or 'degraded'") from exc
    if selected_policy is KnowledgeMismatchPolicy.REBUILD and rebuild_callback is None:
        raise ValueError("rebuild policy requires rebuild_callback")
    if rebuild_callback is not None and not callable(rebuild_callback):
        raise TypeError("rebuild_callback must be callable")

    root = Path(wiki_dir)
    result, surface_is_current = _load_once(root, markdown_pages=markdown_pages)
    if result.status in {KnowledgeLoadState.VALID, KnowledgeLoadState.ABSENT}:
        return result

    if selected_policy is KnowledgeMismatchPolicy.REBUILD:
        assert rebuild_callback is not None
        rebuild_callback(result.issues)
        rebuilt, _ = _load_once(root, markdown_pages=markdown_pages)
        if rebuilt.status is KnowledgeLoadState.VALID:
            return replace(rebuilt, rebuilt=True)
        raise KnowledgeStateLoadError(rebuilt.status, rebuilt.issues)

    if (
        selected_policy is KnowledgeMismatchPolicy.DEGRADED
        and result.surface is not None
        and surface_is_current
    ):
        return KnowledgeLoadResult(
            status=KnowledgeLoadState.DEGRADED,
            surface=result.surface,
            knowledge=None,
            manifest_basis=result.manifest_basis,
            issues=result.issues,
            underlying_status=result.status,
        )
    raise KnowledgeStateLoadError(result.status, result.issues)


def _load_once(
    root: Path,
    *,
    markdown_pages: Mapping[str, str | bytes] | None,
) -> tuple[KnowledgeLoadResult, bool]:
    surface_bytes, surface_read_issue = _read_artifact(
        root,
        SURFACE_INDEX_FILENAME,
    )
    if surface_read_issue is not None:
        return (
            KnowledgeLoadResult(
                status=KnowledgeLoadState.INVALID,
                surface=None,
                knowledge=None,
                manifest_basis=None,
                issues=(surface_read_issue,),
            ),
            False,
        )
    assert surface_bytes is not None
    try:
        surface = validate_surface_index_bytes(surface_bytes)
    except KnowledgeArtifactError as exc:
        issue = _issue_from_artifact_error(
            (
                "surface-schema-version-unsupported"
                if exc.code == "unsupported-schema-version"
                else "surface-invalid"
            ),
            SURFACE_INDEX_FILENAME,
            exc,
        )
        return (
            KnowledgeLoadResult(
                status=KnowledgeLoadState.INVALID,
                surface=None,
                knowledge=None,
                manifest_basis=None,
                issues=(issue,),
            ),
            False,
        )

    try:
        current_pages = _current_markdown(root, markdown_pages)
    except (
        KnowledgeEnvelopeError,
        OSError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as exc:
        issue = KnowledgeLoadIssue(
            code="markdown-snapshot-invalid",
            artifact_path=SURFACE_INDEX_FILENAME,
            field=getattr(exc, "field", None),
            message="current canonical Markdown could not be evaluated",
        )
        return (
            KnowledgeLoadResult(
                status=KnowledgeLoadState.INVALID,
                surface=surface,
                knowledge=None,
                manifest_basis=None,
                issues=(issue,),
            ),
            False,
        )
    surface_paths = {
        page["canonical_path"] for page in surface["pages"] if isinstance(page, Mapping)
    }
    live_paths = set(current_pages)
    surface_is_current = surface_paths == live_paths
    page_issue = (
        None
        if surface_is_current
        else KnowledgeLoadIssue(
            code="page-parity-mismatch",
            artifact_path=SURFACE_INDEX_FILENAME,
            field="pages",
            message=_page_parity_message(surface_paths, live_paths),
        )
    )

    manifest, manifest_issue = _load_manifest(root)
    knowledge_bytes, knowledge_read_issue = _read_artifact(
        root,
        KNOWLEDGE_INDEX_FILENAME,
        absent_is_issue=False,
    )
    if knowledge_bytes is None and knowledge_read_issue is None:
        issues = tuple(
            issue for issue in (manifest_issue, page_issue) if issue is not None
        )
        if manifest_issue is not None and manifest_issue.code != "manifest-absent":
            return (
                KnowledgeLoadResult(
                    status=KnowledgeLoadState.INVALID,
                    surface=surface,
                    knowledge=None,
                    manifest_basis=None,
                    issues=issues,
                ),
                surface_is_current,
            )
        if manifest is not None and manifest.artifact_hashes is not None:
            issues += (
                KnowledgeLoadIssue(
                    code="declared-artifact-missing",
                    artifact_path=KNOWLEDGE_INDEX_FILENAME,
                    message="the manifest commits a knowledge index that is absent",
                ),
            )
            return (
                KnowledgeLoadResult(
                    status=KnowledgeLoadState.INVALID,
                    surface=surface,
                    knowledge=None,
                    manifest_basis=manifest,
                    issues=issues,
                ),
                surface_is_current,
            )
        if page_issue is not None:
            return (
                KnowledgeLoadResult(
                    status=KnowledgeLoadState.INVALID,
                    surface=surface,
                    knowledge=None,
                    manifest_basis=manifest,
                    issues=issues,
                ),
                False,
            )
        return (
            KnowledgeLoadResult(
                status=KnowledgeLoadState.ABSENT,
                surface=surface,
                knowledge=None,
                manifest_basis=manifest,
                issues=issues,
            ),
            True,
        )

    if knowledge_read_issue is not None:
        return (
            KnowledgeLoadResult(
                status=KnowledgeLoadState.INVALID,
                surface=surface,
                knowledge=None,
                manifest_basis=manifest,
                issues=tuple(
                    issue
                    for issue in (manifest_issue, page_issue, knowledge_read_issue)
                    if issue is not None
                ),
            ),
            surface_is_current,
        )
    assert knowledge_bytes is not None
    if manifest is None:
        issue = manifest_issue or KnowledgeLoadIssue(
            code="manifest-absent",
            artifact_path=MANIFEST_FILENAME,
            message="a present knowledge index requires a v5 commit manifest",
        )
        return (
            KnowledgeLoadResult(
                status=KnowledgeLoadState.INVALID,
                surface=surface,
                knowledge=None,
                manifest_basis=None,
                issues=tuple(item for item in (page_issue, issue) if item is not None),
            ),
            surface_is_current,
        )
    marker = manifest.artifact_hashes
    if marker is None:
        issue = KnowledgeLoadIssue(
            code="manifest-marker-missing",
            artifact_path=MANIFEST_FILENAME,
            field="artifact_hashes",
            message="a present knowledge index requires a complete artifact marker",
        )
        return (
            KnowledgeLoadResult(
                status=KnowledgeLoadState.INVALID,
                surface=surface,
                knowledge=None,
                manifest_basis=manifest,
                issues=tuple(
                    item
                    for item in (manifest_issue, page_issue, issue)
                    if item is not None
                ),
            ),
            surface_is_current,
        )

    try:
        validated = validate_knowledge_artifacts(
            surface_index_bytes=surface_bytes,
            knowledge_index_bytes=knowledge_bytes,
            manifest=manifest,
        )
    except KnowledgeArtifactError as exc:
        is_invalid = exc.field.startswith("knowledge_index_bytes")
        error_code = exc.code if isinstance(exc.code, str) else ""
        is_unsupported = error_code == "unsupported-schema-version"
        is_governance = error_code.startswith("governance-")
        status = (
            KnowledgeLoadState.INVALID
            if is_invalid
            else KnowledgeLoadState.MIXED_SNAPSHOT
        )
        issue = _issue_from_artifact_error(
            (
                error_code
                if is_governance
                else "knowledge-schema-version-unsupported"
                if is_unsupported
                else "knowledge-invalid"
                if is_invalid
                else "artifact-parity-mismatch"
            ),
            (
                KNOWLEDGE_INDEX_FILENAME
                if is_invalid or exc.field.startswith("knowledge_index")
                else MANIFEST_FILENAME
                if exc.field.startswith("manifest")
                else SURFACE_INDEX_FILENAME
            ),
            exc,
        )
        return (
            KnowledgeLoadResult(
                status=status,
                surface=surface,
                knowledge=None,
                manifest_basis=manifest,
                issues=tuple(
                    item
                    for item in (manifest_issue, page_issue, issue)
                    if item is not None
                ),
            ),
            surface_is_current,
        )

    marker_issues = _marker_issues(
        marker.surface_index_hash,
        marker.knowledge_index_hash,
        marker.evaluated_envelope_hash,
        validated.surface_index_hash,
        validated.knowledge_index_hash,
        validated.evaluated_envelope_hash,
        marker.governance_hash,
        validated.governance_hash,
    )
    governance_issues, governance_state = _live_governance_issues(
        root,
        validated.knowledge,
        committed_hash=marker.governance_hash,
        projected_hash=validated.governance_hash,
    )
    marker_issues += governance_issues
    if page_issue is not None:
        marker_issues += (page_issue,)
    try:
        markdown_hash = hash_markdown_snapshot(current_pages)
    except KnowledgeEnvelopeError as exc:
        marker_issues += (
            KnowledgeLoadIssue(
                code="markdown-snapshot-invalid",
                artifact_path=KNOWLEDGE_INDEX_FILENAME,
                field=exc.field,
                message=exc.message,
            ),
        )
    else:
        if markdown_hash != validated.knowledge.bundle.snapshot.markdown_snapshot_hash:
            marker_issues += (
                KnowledgeLoadIssue(
                    code="markdown-snapshot-mismatch",
                    artifact_path=KNOWLEDGE_INDEX_FILENAME,
                    field="bundle.snapshot.markdown_snapshot_hash",
                    message="current canonical Markdown does not match the committed snapshot",
                ),
            )
    if marker_issues:
        return (
            KnowledgeLoadResult(
                status=(
                    governance_state
                    if governance_state is not None
                    else KnowledgeLoadState.MIXED_SNAPSHOT
                ),
                surface=surface,
                knowledge=None,
                manifest_basis=manifest,
                issues=tuple(
                    item
                    for item in (manifest_issue, *marker_issues)
                    if item is not None
                ),
            ),
            surface_is_current,
        )
    return (
        KnowledgeLoadResult(
            status=KnowledgeLoadState.VALID,
            surface=validated.surface_payload,
            knowledge=validated.knowledge,
            manifest_basis=manifest,
            issues=(),
        ),
        True,
    )


def _read_artifact(
    root: Path,
    filename: str,
    *,
    absent_is_issue: bool = True,
) -> tuple[bytes | None, KnowledgeLoadIssue | None]:
    path = root / filename
    if path.is_symlink():
        return None, KnowledgeLoadIssue(
            code="artifact-not-regular",
            artifact_path=filename,
            message="artifact must be a regular file, not a symbolic link",
        )
    if not path.exists():
        if not absent_is_issue:
            return None, None
        return None, KnowledgeLoadIssue(
            code="artifact-absent",
            artifact_path=filename,
            message="required artifact is absent",
        )
    if not path.is_file():
        return None, KnowledgeLoadIssue(
            code="artifact-not-regular",
            artifact_path=filename,
            message="artifact must be a regular file",
        )
    try:
        return path.read_bytes(), None
    except OSError:
        return None, KnowledgeLoadIssue(
            code="artifact-unreadable",
            artifact_path=filename,
            message="artifact could not be read",
        )


def _load_manifest(
    root: Path,
) -> tuple[SyncManifest | None, KnowledgeLoadIssue | None]:
    path = root / MANIFEST_FILENAME
    if path.is_symlink():
        return None, KnowledgeLoadIssue(
            code="manifest-invalid",
            artifact_path=MANIFEST_FILENAME,
            message="manifest must be a regular file, not a symbolic link",
        )
    try:
        return SyncManifest.load(root), None
    except FileNotFoundError:
        return None, KnowledgeLoadIssue(
            code="manifest-absent",
            artifact_path=MANIFEST_FILENAME,
            message="manifest is absent",
        )
    except SyncManifestError as exc:
        return None, KnowledgeLoadIssue(
            code=(
                "manifest-version-unsupported"
                if exc.code == "unsupported-version"
                else "manifest-invalid"
            ),
            artifact_path=MANIFEST_FILENAME,
            field=exc.field,
            message=exc.message,
        )
    except (OSError, UnicodeError, ValueError):
        return None, KnowledgeLoadIssue(
            code="manifest-invalid",
            artifact_path=MANIFEST_FILENAME,
            message="manifest is not valid UTF-8 JSON",
        )


def _current_markdown(
    root: Path,
    supplied: Mapping[str, str | bytes] | None,
) -> dict[str, str | bytes]:
    if supplied is not None:
        if not isinstance(supplied, Mapping):
            raise TypeError("markdown_pages must be a mapping")
        copied = dict(supplied)
        # This validates paths and strict content encoding without retaining a
        # second derived hash.
        hash_markdown_snapshot(copied)
        return copied
    return {page.relative_path: read_md(page.path) for page in collect_wiki_pages(root)}


def _marker_issues(
    committed_surface: str,
    committed_knowledge: str,
    committed_envelope: str,
    actual_surface: str,
    actual_knowledge: str,
    actual_envelope: str,
    committed_governance: str | None = None,
    actual_governance: str | None = None,
) -> tuple[KnowledgeLoadIssue, ...]:
    issues: list[KnowledgeLoadIssue] = []
    for code, artifact, field, committed, actual, message in (
        (
            "surface-hash-mismatch",
            SURFACE_INDEX_FILENAME,
            "artifact_hashes.surface_index_hash",
            committed_surface,
            actual_surface,
            "surface-index bytes do not match the manifest marker",
        ),
        (
            "knowledge-hash-mismatch",
            KNOWLEDGE_INDEX_FILENAME,
            "artifact_hashes.knowledge_index_hash",
            committed_knowledge,
            actual_knowledge,
            "knowledge-index bytes do not match the manifest marker",
        ),
        (
            "envelope-hash-mismatch",
            MANIFEST_FILENAME,
            "artifact_hashes.evaluated_envelope_hash",
            committed_envelope,
            actual_envelope,
            "knowledge envelope does not match the manifest marker",
        ),
        (
            "governance-hash-mismatch",
            GOVERNANCE_FILENAME,
            "artifact_hashes.governance_hash",
            committed_governance,
            actual_governance,
            "governance projection does not match the manifest marker",
        ),
    ):
        if committed != actual:
            issues.append(
                KnowledgeLoadIssue(
                    code=code,
                    artifact_path=artifact,
                    field=field,
                    message=message,
                )
            )
    return tuple(issues)


def _live_governance_issues(
    root: Path,
    knowledge: KnowledgeIndex,
    *,
    committed_hash: str | None,
    projected_hash: str | None,
) -> tuple[tuple[KnowledgeLoadIssue, ...], KnowledgeLoadState | None]:
    """Validate the non-rebuildable live ledger without exposing stale state."""

    path = root / GOVERNANCE_FILENAME
    ledger_present = path.exists() or path.is_symlink()
    if not ledger_present:
        if committed_hash is None and projected_hash is None:
            return (), None
        return (
            (
                KnowledgeLoadIssue(
                    code="governance-missing",
                    artifact_path=GOVERNANCE_FILENAME,
                    message=(
                        "prior artifacts are governed but the authoritative "
                        "ledger is absent; restore it from version control"
                    ),
                ),
            ),
            KnowledgeLoadState.INVALID,
        )
    try:
        loaded = load_governance(root)
    except GovernanceError as exc:
        return (
            (
                KnowledgeLoadIssue(
                    code=exc.code,
                    artifact_path=GOVERNANCE_FILENAME,
                    field=exc.field,
                    message=exc.message,
                ),
            ),
            KnowledgeLoadState.INVALID,
        )
    except (OSError, UnicodeError, ValueError):
        return (
            (
                KnowledgeLoadIssue(
                    code="governance-invalid",
                    artifact_path=GOVERNANCE_FILENAME,
                    message="governance ledger could not be validated",
                ),
            ),
            KnowledgeLoadState.INVALID,
        )
    if projected_hash is None or committed_hash is None:
        return (
            (
                KnowledgeLoadIssue(
                    code="governance-projection-missing",
                    artifact_path=KNOWLEDGE_INDEX_FILENAME,
                    field=f"extensions.{GOVERNANCE_EXTENSION_KEY}",
                    message=(
                        "a governance ledger exists but the generated "
                        "projection/manifest does not commit it"
                    ),
                ),
            ),
            KnowledgeLoadState.MIXED_SNAPSHOT,
        )
    issues: list[KnowledgeLoadIssue] = []
    if loaded.content_hash != projected_hash:
        issues.append(
            KnowledgeLoadIssue(
                code="governance-live-hash-mismatch",
                artifact_path=GOVERNANCE_FILENAME,
                message=(
                    "governance ledger changed after the generated projection"
                ),
            )
        )
    try:
        validate_governance_projection(knowledge, ledger=loaded.ledger)
    except GovernanceError as exc:
        issues.append(
            KnowledgeLoadIssue(
                code=exc.code,
                artifact_path=KNOWLEDGE_INDEX_FILENAME,
                field=exc.field,
                message=exc.message,
            )
        )
    return (
        tuple(issues),
        KnowledgeLoadState.MIXED_SNAPSHOT if issues else None,
    )


def _page_parity_message(surface_paths: set[str], live_paths: set[str]) -> str:
    missing = sorted(live_paths - surface_paths)
    if missing:
        return f"surface index is missing active canonical page {missing[0]!r}"
    extra = sorted(surface_paths - live_paths)
    return f"surface index contains non-active canonical page {extra[0]!r}"


def _issue_from_artifact_error(
    code: str,
    artifact_path: str,
    error: KnowledgeArtifactError,
) -> KnowledgeLoadIssue:
    return KnowledgeLoadIssue(
        code=code,
        artifact_path=artifact_path,
        field=error.field,
        message=error.message,
    )


__all__ = [
    "KnowledgeLoadIssue",
    "KnowledgeLoadResult",
    "KnowledgeMismatchPolicy",
    "KnowledgeStateLoadError",
    "load_knowledge_state",
]
