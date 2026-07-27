"""Read-only adoption of an existing canonical LLM Wiki.

The importer is deliberately independent from command modules.  It validates the
entire input before creating the workspace copy, copies regular files without
text decoding or newline normalization, and records enough provenance for the
documentation-run service to persist ``wiki-input.json`` later.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import unicodedata
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Mapping
from urllib.parse import urlsplit

from .filesystem_guard import (
    WindowsDirectoryGuardError,
    _WindowsDirectoryGuardUnavailableError,
    WindowsFileGuardError,
    WindowsIdentityUnavailableError,
    WindowsObjectIdentity,
    _WindowsPathHandleMetadata,
    fresh_no_follow_stat,
    guard_windows_directory_chain,
    open_windows_readonly_file,
    windows_object_identity,
    windows_object_identity_from_values,
    _windows_path_handle_metadata,
)
from .knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    KnowledgeArtifactError,
    ValidatedKnowledgeArtifacts,
    validate_knowledge_artifacts,
    validate_surface_index_bytes,
)
from .knowledge_envelope import KnowledgeEnvelopeError, hash_markdown_snapshot
from .source_snapshot import build_source_snapshot
from .sync_manifest import (
    LEGACY_MANIFEST_VERSION,
    MANIFEST_VERSION,
    ManifestArtifactHashes,
    SyncManifest,
    SyncManifestError,
)
from .wiki_media import (
    iter_markdown_link_targets,
    local_link_path,
    strip_fenced_code_blocks,
)
from .wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
)
from .wiki_surface import is_safe_page_id, iter_page_kinds


MANIFEST_FILENAME = ".llm-wiki-manifest.json"
# Keep the singular legacy name until the documentation-run v1 baseline
# validator is widened to represent both accepted forms.  Import validation
# itself uses the explicit set below.
SUPPORTED_MANIFEST_VERSION = LEGACY_MANIFEST_VERSION
SUPPORTED_MANIFEST_VERSIONS = frozenset(
    {LEGACY_MANIFEST_VERSION, MANIFEST_VERSION}
)

# Fixed fail-closed bounds for untrusted existing-wiki inputs.  These limits are
# deliberately well above the 352-file/~1.6 MiB stable Documentator archive
# pilot while still preventing an adopted tree from consuming unbounded
# descriptors, memory, I/O, or recursion depth during inventory, hashing,
# semantic inspection, and copy.
MAX_INPUT_WIKI_ENTRIES = 8_192
MAX_INPUT_WIKI_FILES = 4_096
MAX_INPUT_WIKI_FILE_BYTES = 64 * 1024 * 1024
MAX_INPUT_WIKI_TOTAL_BYTES = 512 * 1024 * 1024
MAX_INPUT_WIKI_DEPTH = 16
MAX_INPUT_WIKI_SEMANTIC_FILE_BYTES = 4 * 1024 * 1024
MAX_INPUT_WIKI_SEMANTIC_TOTAL_BYTES = 16 * 1024 * 1024
MAX_GENERATED_MARKER_RECORDS_PER_PAGE = 8
MAX_GENERATED_MARKER_RECORDS_TOTAL = 128
MAX_GENERATED_MARKER_EVIDENCE_BYTES = 64 * 1024
_INPUT_READ_CHUNK_BYTES = 1024 * 1024
_MARKER_HASH_CHUNK_CHARS = 16 * 1024

GENERATED_MARKER_EVIDENCE_SCHEMA_VERSION = "llm-wiki-generated-marker-evidence/v1"

FRESHNESS_POLICIES = frozenset(
    {"require-current", "allow-unverified", "refresh-snapshot"}
)

_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_OPENAPI_GENERATION_INPUT_FIELDS = frozenset({"path", "sha256", "format"})
_SUPPORTED_GENERATION_INPUTS = frozenset({"openapi"})
_GENERATED_MARKER_RE = re.compile(
    r"<!--\s*Auto-generated\b.*?-->|"
    r"_Auto-generated from `[^`]+`(?: in `[^`]+`)?\._",
    re.IGNORECASE | re.DOTALL,
)
_WINDOWS_RESERVED_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{number}" for number in range(1, 10)}
    | {f"lpt{number}" for number in range(1, 10)}
)
_WINDOWS_FORBIDDEN_CHARS = frozenset('<>:"/\\|?*')
_SECURE_DIRECTORY_FD_COPY_AVAILABLE = (
    os.open in getattr(os, "supports_dir_fd", set())
    and os.mkdir in getattr(os, "supports_dir_fd", set())
    and os.stat in getattr(os, "supports_dir_fd", set())
    and os.stat in getattr(os, "supports_follow_symlinks", set())
    and bool(getattr(os, "O_DIRECTORY", 0))
    and bool(getattr(os, "O_NOFOLLOW", 0))
)
_SECURE_INPUT_FD_TRAVERSAL_AVAILABLE = (
    os.name != "nt"
    and os.scandir in getattr(os, "supports_fd", set())
    and os.open in getattr(os, "supports_dir_fd", set())
    and os.stat in getattr(os, "supports_dir_fd", set())
    and os.stat in getattr(os, "supports_follow_symlinks", set())
    and bool(getattr(os, "O_DIRECTORY", 0))
    and bool(getattr(os, "O_NOFOLLOW", 0))
)

_CANONICAL_ROOT_FILES = frozenset(
    {
        "index.md",
        "log.md",
        "api-contracts.md",
        "dependencies.md",
        "load-order.md",
        "bootstrap-remainder.md",
        MANIFEST_FILENAME,
        SURFACE_INDEX_FILENAME,
        KNOWLEDGE_INDEX_FILENAME,
    }
)
_CANONICAL_MARKDOWN_DIRS = frozenset(
    {"entities", "modules", "workflows", "guides", "flows", "infrastructure"}
)

_REJECTED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".claude",
        ".codex",
        ".cursor",
        ".idea",
        ".llm-wiki",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".vscode",
        "__pycache__",
        "node_modules",
        "_site",
    }
)
_REJECTED_FILE_NAMES = frozenset(
    {
        ".cursorrules",
        ".ds_store",
        ".aider.conf.yml",
        ".aider.conf.yaml",
        "agents.md",
        "claude.md",
        "copilot-instructions.md",
        "llm-wiki-inventory-cache.json",
        "opencode.json",
        "opencode.jsonc",
        "thumbs.db",
    }
)
_REJECTED_GITHUB_PREFIXES = (
    ".github/instructions/",
    ".github/prompts/",
)


class DocumentationWikiInputError(ValueError):
    """Raised when a wiki cannot be adopted without weakening isolation."""

    def __init__(
        self,
        message: str,
        *,
        category: str = "invalid_wiki_input",
        path: str | None = None,
        rejected_entries: tuple[str, ...] = (),
        diagnostics: tuple[str, ...] = (),
    ) -> None:
        self.category = category
        self.path = path
        self.rejected_entries = rejected_entries
        self.diagnostics = diagnostics
        super().__init__(f"[{category}] {message}")


@dataclass(frozen=True)
class DocumentationWikiSnapshot:
    """Typed provenance for an adopted, byte-preserved wiki snapshot."""

    input_wiki_dir: str
    workspace_wiki_dir: str
    input_tree_hash: str
    initial_snapshot_hash: str
    file_hashes: Mapping[str, str]
    copied_paths: tuple[str, ...]
    manifest_schema_version: int | None
    surface_schema_version: str | None
    legacy_index_only: bool
    unknown_entries: tuple[str, ...]
    rejected_entries: tuple[str, ...]
    generated_markers: Mapping[str, Any]
    semantic_markdown_paths: tuple[str, ...]
    semantic_pages: tuple[Mapping[str, Any], ...]
    diagnostics: tuple[str, ...]
    source_available: bool
    source_root: str | None
    freshness_policy: str
    freshness: str
    source_mismatches: tuple[str, ...]
    workspace_refresh_required: bool
    resource_usage: Mapping[str, int]
    resource_limits: Mapping[str, int]
    knowledge_schema_version: str | None = None
    artifact_form: str = "legacy_index_only"
    baseline_strategy: str = field(default="adopt_existing_wiki", init=False)

    @property
    def source_verified_publish_ready(self) -> bool:
        """Whether this import can support a source-verified publish verdict."""

        return (
            self.freshness == "verified_current" and not self.workspace_refresh_required
        )

    @property
    def recognized_schemas(self) -> dict[str, int | str]:
        """Return only metadata schemas recognized on the imported input."""

        schemas: dict[str, int | str] = {}
        if self.manifest_schema_version is not None:
            schemas["manifest"] = self.manifest_schema_version
        if self.surface_schema_version is not None:
            schemas["surface"] = self.surface_schema_version
        if self.knowledge_schema_version is not None:
            schemas["knowledge"] = self.knowledge_schema_version
        return schemas

    @property
    def compatibility(self) -> str:
        """Compatibility classification used by lifecycle/status surfaces."""

        return "legacy_index_only" if self.legacy_index_only else "current"

    @property
    def refresh_decision(self) -> str:
        """Describe the only permitted follow-up mutation decision."""

        if self.workspace_refresh_required:
            return "workspace_only_required"
        if (
            self.freshness_policy == "allow-unverified"
            and self.freshness != "verified_current"
        ):
            return "allow_unverified"
        return "not_required"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable evidence payload."""

        return {
            "baseline_strategy": self.baseline_strategy,
            "input_wiki_dir": self.input_wiki_dir,
            "workspace_wiki_dir": self.workspace_wiki_dir,
            "input_tree_hash": self.input_tree_hash,
            "initial_snapshot_hash": self.initial_snapshot_hash,
            "file_hashes": dict(self.file_hashes),
            "copied_paths": list(self.copied_paths),
            "resource_usage": dict(self.resource_usage),
            "resource_limits": dict(self.resource_limits),
            "recognized_schemas": self.recognized_schemas,
            "manifest_version": self.manifest_schema_version,
            "surface_schema_version": self.surface_schema_version,
            "knowledge_schema_version": self.knowledge_schema_version,
            "artifact_form": self.artifact_form,
            "compatibility": self.compatibility,
            "legacy_index_only": self.legacy_index_only,
            "unknown_entries": list(self.unknown_entries),
            "rejected_entries": list(self.rejected_entries),
            "generated_markers": dict(self.generated_markers),
            "semantic_markdown_paths": list(self.semantic_markdown_paths),
            "semantic_pages": [dict(page) for page in self.semantic_pages],
            "diagnostics": list(self.diagnostics),
            "freshness_policy": self.freshness_policy,
            "freshness": self.freshness,
            "source_available": self.source_available,
            "source_mismatches": list(self.source_mismatches),
            "refresh_decision": self.refresh_decision,
            "source": {
                "available": self.source_available,
                "root": self.source_root,
                "freshness_policy": self.freshness_policy,
                "freshness": self.freshness,
                "mismatches": list(self.source_mismatches),
                "workspace_refresh_required": self.workspace_refresh_required,
                "source_verified_publish_ready": self.source_verified_publish_ready,
            },
        }


@dataclass(frozen=True)
class _InputFile:
    path: Path
    relative_path: str
    sha256: str
    size: int
    mtime_ns: int
    ctime_ns: int
    device: int
    inode: int
    root_descriptor: int | None = None


@dataclass(frozen=True)
class _HashedInputFile:
    sha256: str
    opened_stat: os.stat_result


@dataclass(frozen=True)
class _InputTree:
    root: Path
    files: tuple[_InputFile, ...]
    tree_hash: str
    entry_count: int
    directory_count: int
    maximum_depth: int

    @property
    def file_hashes(self) -> dict[str, str]:
        return {entry.relative_path: entry.sha256 for entry in self.files}

    @property
    def by_path(self) -> dict[str, _InputFile]:
        return {entry.relative_path: entry for entry in self.files}

    @property
    def total_bytes(self) -> int:
        return sum(entry.size for entry in self.files)

    @property
    def resource_usage(self) -> dict[str, int]:
        return {
            "entry_count": self.entry_count,
            "file_count": len(self.files),
            "directory_count": self.directory_count,
            "total_bytes": self.total_bytes,
            "maximum_depth": self.maximum_depth,
        }


@dataclass(frozen=True)
class _ValidatedWikiMetadata:
    """One fully classified metadata form built only from guarded input bytes."""

    manifest_payload: Mapping[str, Any] | None
    surface_payload: Mapping[str, Any] | None
    sync_manifest: SyncManifest | None
    knowledge_artifacts: ValidatedKnowledgeArtifacts | None
    artifact_form: str
    legacy_index_only: bool

    @property
    def manifest_version(self) -> int | None:
        if self.manifest_payload is None:
            return None
        version = self.manifest_payload.get("version")
        return (
            version
            if isinstance(version, int) and not isinstance(version, bool)
            else None
        )

    @property
    def surface_schema_version(self) -> str | None:
        if self.surface_payload is None:
            return None
        schema = self.surface_payload.get("schema_version")
        return schema if isinstance(schema, str) else None

    @property
    def knowledge_schema_version(self) -> str | None:
        if self.knowledge_artifacts is None:
            return None
        return self.knowledge_artifacts.knowledge.schema_version


@dataclass(frozen=True)
class _MarkdownInspection:
    semantic_paths: tuple[str, ...]
    generated_marker_counts: Mapping[str, int]
    generated_markers: Mapping[str, Any]
    semantic_file_count: int
    semantic_total_bytes: int


@dataclass
class _InputResourceBudget:
    entry_count: int = 0
    file_count: int = 0
    directory_count: int = 0
    total_bytes: int = 0
    maximum_depth: int = 0

    def observe_entry(self, relative: PurePosixPath) -> None:
        relative_text = relative.as_posix()
        self.entry_count += 1
        depth = len(relative.parts)
        self.maximum_depth = max(self.maximum_depth, depth)
        if self.entry_count > MAX_INPUT_WIKI_ENTRIES:
            _raise_input_resource_limit(
                category="input_entry_count_limit_exceeded",
                message=(
                    f"Input wiki contains more than {MAX_INPUT_WIKI_ENTRIES} entries; "
                    f"the limit was exceeded at {relative_text!r}. Remove or split "
                    "the wiki before adoption."
                ),
                path=relative_text,
                diagnostic=(
                    f"entry_count={self.entry_count} "
                    f"max_entry_count={MAX_INPUT_WIKI_ENTRIES}"
                ),
            )
        if depth > MAX_INPUT_WIKI_DEPTH:
            _raise_input_resource_limit(
                category="input_depth_limit_exceeded",
                message=(
                    f"Input wiki path depth {depth} exceeds the "
                    f"{MAX_INPUT_WIKI_DEPTH}-component limit at "
                    f"{relative_text!r}. Flatten the wiki before adoption."
                ),
                path=relative_text,
                diagnostic=f"depth={depth} max_depth={MAX_INPUT_WIKI_DEPTH}",
            )

    def account_directory(self) -> None:
        self.directory_count += 1

    def account_file(self, relative_path: str, size: int) -> None:
        next_file_count = self.file_count + 1
        if next_file_count > MAX_INPUT_WIKI_FILES:
            _raise_input_resource_limit(
                category="input_file_count_limit_exceeded",
                message=(
                    f"Input wiki contains more than {MAX_INPUT_WIKI_FILES} regular "
                    f"files; the limit was exceeded at {relative_path!r}. Remove or "
                    "split the wiki before adoption."
                ),
                path=relative_path,
                diagnostic=(
                    f"file_count={next_file_count} "
                    f"max_file_count={MAX_INPUT_WIKI_FILES}"
                ),
            )
        if size > MAX_INPUT_WIKI_FILE_BYTES:
            _raise_input_resource_limit(
                category="input_file_size_limit_exceeded",
                message=(
                    f"Input wiki file {relative_path!r} is {size} bytes, exceeding "
                    f"the {MAX_INPUT_WIKI_FILE_BYTES}-byte per-file limit. Reduce "
                    "or externally host the asset before adoption."
                ),
                path=relative_path,
                diagnostic=(
                    f"file_bytes={size} max_file_bytes={MAX_INPUT_WIKI_FILE_BYTES}"
                ),
            )
        next_total = self.total_bytes + size
        if next_total > MAX_INPUT_WIKI_TOTAL_BYTES:
            _raise_input_resource_limit(
                category="input_total_size_limit_exceeded",
                message=(
                    f"Input wiki regular-file content would total {next_total} bytes, "
                    f"exceeding the {MAX_INPUT_WIKI_TOTAL_BYTES}-byte aggregate "
                    f"limit at {relative_path!r}. Remove or split content before "
                    "adoption."
                ),
                path=relative_path,
                diagnostic=(
                    f"total_bytes={next_total} "
                    f"max_total_bytes={MAX_INPUT_WIKI_TOTAL_BYTES}"
                ),
            )
        self.file_count = next_file_count
        self.total_bytes = next_total


def documentation_wiki_input_resource_limits() -> dict[str, int]:
    """Return the fixed resource policy applied to every input-tree pass."""

    return {
        "max_entry_count": MAX_INPUT_WIKI_ENTRIES,
        "max_file_count": MAX_INPUT_WIKI_FILES,
        "max_file_bytes": MAX_INPUT_WIKI_FILE_BYTES,
        "max_total_bytes": MAX_INPUT_WIKI_TOTAL_BYTES,
        "max_depth": MAX_INPUT_WIKI_DEPTH,
        "max_semantic_file_bytes": MAX_INPUT_WIKI_SEMANTIC_FILE_BYTES,
        "max_semantic_total_bytes": MAX_INPUT_WIKI_SEMANTIC_TOTAL_BYTES,
        "max_generated_marker_records_per_page": (
            MAX_GENERATED_MARKER_RECORDS_PER_PAGE
        ),
        "max_generated_marker_records_total": MAX_GENERATED_MARKER_RECORDS_TOTAL,
        "max_generated_marker_evidence_bytes": MAX_GENERATED_MARKER_EVIDENCE_BYTES,
    }


def _raise_input_resource_limit(
    *,
    category: str,
    message: str,
    path: str,
    diagnostic: str,
) -> None:
    raise DocumentationWikiInputError(
        message,
        category=category,
        path=path,
        diagnostics=(diagnostic,),
    )


def _assert_input_files_resource_bounds(files: tuple[_InputFile, ...]) -> None:
    budget = _InputResourceBudget()
    for entry in files:
        budget.account_file(entry.relative_path, entry.size)


def _assert_input_tree_resource_bounds(input_tree: _InputTree) -> None:
    if input_tree.entry_count > MAX_INPUT_WIKI_ENTRIES:
        _raise_input_resource_limit(
            category="input_entry_count_limit_exceeded",
            message=(
                f"Input wiki contains {input_tree.entry_count} entries, exceeding "
                f"the {MAX_INPUT_WIKI_ENTRIES}-entry limit. Remove or split the "
                "wiki before adoption."
            ),
            path=".",
            diagnostic=(
                f"entry_count={input_tree.entry_count} "
                f"max_entry_count={MAX_INPUT_WIKI_ENTRIES}"
            ),
        )
    if input_tree.maximum_depth > MAX_INPUT_WIKI_DEPTH:
        _raise_input_resource_limit(
            category="input_depth_limit_exceeded",
            message=(
                f"Input wiki path depth {input_tree.maximum_depth} exceeds the "
                f"{MAX_INPUT_WIKI_DEPTH}-component limit. Flatten the wiki before "
                "adoption."
            ),
            path=".",
            diagnostic=(
                f"depth={input_tree.maximum_depth} max_depth={MAX_INPUT_WIKI_DEPTH}"
            ),
        )
    _assert_input_files_resource_bounds(input_tree.files)


def fingerprint_documentation_wiki_input(input_wiki_dir: str | Path) -> str:
    """Return the secure tree hash used by existing-wiki adoption.

    This read-only recheck uses the same content policy, portable-path rules,
    descriptor-rooted traversal, no-follow opens, and tree-hash algorithm as
    ``adopt_documentation_wiki_snapshot``.
    """

    input_root, input_identity = _validate_input_root(input_wiki_dir)
    with _open_input_root_descriptor(
        input_root,
        expected_identity=input_identity,
    ) as root_descriptor:
        initial = _collect_input_tree(
            input_root,
            enforce_content_policy=True,
            root_descriptor=root_descriptor,
        )
        final = _collect_input_tree(
            input_root,
            enforce_content_policy=True,
            root_descriptor=root_descriptor,
        )
        if final.file_hashes != initial.file_hashes:
            raise DocumentationWikiInputError(
                "Input wiki changed while its secure fingerprint was being computed.",
                category="input_changed_during_snapshot",
            )
        if root_descriptor is not None:
            _assert_input_root_path_binding(input_root, root_descriptor)
        return initial.tree_hash


def adopt_documentation_wiki_snapshot(
    input_wiki_dir: str | Path,
    workspace_wiki_dir: str | Path,
    *,
    source_root: str | Path | None = None,
    freshness_policy: str = "require-current",
) -> DocumentationWikiSnapshot:
    """Validate and copy an existing LLM Wiki into an isolated workspace.

    ``refresh-snapshot`` never performs a refresh itself.  When the imported
    baseline is stale or legacy, the returned result records that a later
    deterministic refresh must target only ``workspace_wiki_dir``.
    """

    return _adopt_documentation_wiki_snapshot_with_runtime(
        input_wiki_dir,
        workspace_wiki_dir,
        source_root=source_root,
        freshness_policy=freshness_policy,
        trust_source_plugins=False,
        helper_cache_dir=None,
    )


def _adopt_documentation_wiki_snapshot_with_runtime(
    input_wiki_dir: str | Path,
    workspace_wiki_dir: str | Path,
    *,
    source_root: str | Path | None,
    freshness_policy: str,
    trust_source_plugins: bool,
    helper_cache_dir: str | Path | None,
) -> DocumentationWikiSnapshot:
    """Adopt with controller-approved native live-evaluation inputs."""

    _validate_freshness_policy(freshness_policy)
    if not isinstance(trust_source_plugins, bool):
        raise TypeError("trust_source_plugins must be a bool")
    input_root, input_identity = _validate_input_root(input_wiki_dir)
    workspace_root = _validate_workspace_root(workspace_wiki_dir)
    resolved_source_root = _validate_source_root(source_root)
    _validate_root_isolation(input_root, workspace_root, resolved_source_root)

    with _open_input_root_descriptor(
        input_root,
        expected_identity=input_identity,
    ) as root_descriptor:
        return _adopt_validated_wiki_snapshot(
            input_root,
            workspace_root,
            source_root=resolved_source_root,
            freshness_policy=freshness_policy,
            root_descriptor=root_descriptor,
            trust_source_plugins=trust_source_plugins,
            helper_cache_dir=helper_cache_dir,
        )


def _adopt_validated_wiki_snapshot(
    input_root: Path,
    workspace_root: Path,
    *,
    source_root: Path | None,
    freshness_policy: str,
    root_descriptor: int | None,
    trust_source_plugins: bool,
    helper_cache_dir: str | Path | None,
) -> DocumentationWikiSnapshot:
    """Adopt from already validated roots while the input root remains pinned."""

    input_tree = _collect_input_tree(
        input_root,
        enforce_content_policy=True,
        root_descriptor=root_descriptor,
    )
    input_files = input_tree.by_path
    if "index.md" not in input_files:
        raise DocumentationWikiInputError(
            f"Canonical wiki index is missing: {input_root / 'index.md'}",
            category="missing_index",
            path="index.md",
        )

    metadata = _load_and_validate_metadata(input_files)
    surface = metadata.surface_payload
    legacy = metadata.legacy_index_only
    unknown_entries = _unknown_entries(input_tree.files)
    markdown_inspection = _inspect_markdown(input_tree.files)
    semantic_pages = _semantic_page_records(
        input_tree.files,
        surface,
        generated_marker_counts=markdown_inspection.generated_marker_counts,
    )
    freshness, source_mismatches, diagnostics = _resolve_metadata_freshness(
        metadata,
        source_root=source_root,
        trust_source_plugins=trust_source_plugins,
        helper_cache_dir=helper_cache_dir,
    )
    refresh_required = _enforce_freshness_policy(
        freshness_policy,
        freshness,
        source_available=source_root is not None,
        diagnostics=diagnostics,
    )

    workspace_existed = os.path.lexists(workspace_root)
    _require_empty_workspace(workspace_root)
    workspace_identity: os.stat_result | None = None
    try:
        workspace_root.mkdir(parents=True, exist_ok=True)
        workspace_identity = workspace_root.lstat()
        _assert_safe_workspace_directory(workspace_identity, path=workspace_root)
        _copy_input_tree(input_tree, workspace_root)
        snapshot_tree = _collect_input_tree(
            workspace_root,
            enforce_content_policy=False,
        )
        if snapshot_tree.file_hashes != input_tree.file_hashes:
            raise DocumentationWikiInputError(
                "Workspace snapshot does not match the validated input file hashes.",
                category="snapshot_hash_mismatch",
            )

        final_input_tree = _collect_input_tree(
            input_root,
            enforce_content_policy=True,
            root_descriptor=root_descriptor,
        )
        if final_input_tree.file_hashes != input_tree.file_hashes:
            raise DocumentationWikiInputError(
                "Input wiki changed while its workspace snapshot was being created.",
                category="input_changed_during_snapshot",
            )
        if root_descriptor is not None:
            _assert_input_root_path_binding(input_root, root_descriptor)
    except BaseException as original:
        if workspace_identity is not None:
            try:
                _rollback_partial_workspace_snapshot(
                    workspace_root,
                    expected_identity=workspace_identity,
                    preserve_root=workspace_existed,
                )
            except Exception as rollback_error:
                raise DocumentationWikiInputError(
                    "Wiki adoption failed and its partial workspace snapshot could "
                    f"not be removed: {rollback_error}",
                    category="workspace_rollback_failed",
                    path=str(workspace_root),
                ) from original
        raise

    if legacy:
        diagnostics.append(
            "legacy_index_only: metadata seeding or migration must occur only in "
            "the workspace snapshot"
        )
    if refresh_required:
        diagnostics.append(
            "workspace_refresh_required: refresh or migration must target only the "
            "workspace snapshot"
        )
    if freshness != "verified_current":
        diagnostics.append(
            "publish_ready_limited: this baseline cannot claim source-verified "
            "publish readiness"
        )

    return DocumentationWikiSnapshot(
        input_wiki_dir=str(input_root),
        workspace_wiki_dir=str(workspace_root),
        input_tree_hash=input_tree.tree_hash,
        initial_snapshot_hash=snapshot_tree.tree_hash,
        file_hashes=input_tree.file_hashes,
        copied_paths=tuple(entry.relative_path for entry in input_tree.files),
        manifest_schema_version=metadata.manifest_version,
        surface_schema_version=metadata.surface_schema_version,
        legacy_index_only=legacy,
        unknown_entries=unknown_entries,
        rejected_entries=(),
        generated_markers=markdown_inspection.generated_markers,
        semantic_markdown_paths=markdown_inspection.semantic_paths,
        semantic_pages=semantic_pages,
        diagnostics=tuple(diagnostics),
        source_available=source_root is not None,
        source_root=(str(source_root) if source_root is not None else None),
        freshness_policy=freshness_policy,
        freshness=freshness,
        source_mismatches=source_mismatches,
        workspace_refresh_required=refresh_required,
        resource_usage={
            **input_tree.resource_usage,
            "semantic_file_count": markdown_inspection.semantic_file_count,
            "semantic_total_bytes": markdown_inspection.semantic_total_bytes,
        },
        resource_limits=documentation_wiki_input_resource_limits(),
        knowledge_schema_version=metadata.knowledge_schema_version,
        artifact_form=metadata.artifact_form,
    )


def _validate_freshness_policy(policy: str) -> None:
    if policy not in FRESHNESS_POLICIES:
        allowed = ", ".join(sorted(FRESHNESS_POLICIES))
        raise DocumentationWikiInputError(
            f"Unknown freshness policy {policy!r}; choose from: {allowed}.",
            category="invalid_freshness_policy",
        )


def _validate_input_root(path: str | Path) -> tuple[Path, os.stat_result]:
    candidate = Path(path).expanduser()
    try:
        root_stat = candidate.lstat()
    except FileNotFoundError as exc:
        raise DocumentationWikiInputError(
            f"Input wiki directory does not exist: {candidate}",
            category="input_missing",
            path=str(candidate),
        ) from exc
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot inspect input wiki directory {candidate}: {exc}",
            category="input_unreadable",
            path=str(candidate),
        ) from exc
    if stat.S_ISLNK(root_stat.st_mode) or _is_reparse_point(root_stat):
        raise DocumentationWikiInputError(
            f"Input wiki root must not be a symlink or reparse point: {candidate}",
            category="symlink_rejected",
            path=str(candidate),
            rejected_entries=(".",),
        )
    if not stat.S_ISDIR(root_stat.st_mode):
        raise DocumentationWikiInputError(
            f"Input wiki root is not a directory: {candidate}",
            category="input_not_directory",
            path=str(candidate),
        )
    try:
        resolved = candidate.resolve(strict=True)
        resolved_stat = resolved.lstat()
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Input wiki root changed during validation: {candidate}: {exc}",
            category="input_changed_during_snapshot",
            path=str(candidate),
        ) from exc
    if _uses_windows_guarded_input_fallback():
        _assert_windows_input_identity(
            root_stat,
            resolved_stat,
            path=str(candidate),
            operation="input-root validation",
        )
    else:
        _assert_same_input_identity(
            root_stat,
            resolved_stat,
            path=str(candidate),
            operation="input-root validation",
        )
    return resolved, root_stat


def _validate_workspace_root(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot resolve workspace wiki directory {candidate}: {exc}",
            category="workspace_path_invalid",
            path=str(candidate),
        ) from exc

    if candidate.exists() or candidate.is_symlink():
        try:
            workspace_stat = candidate.lstat()
        except OSError as exc:
            raise DocumentationWikiInputError(
                f"Cannot inspect workspace wiki directory {candidate}: {exc}",
                category="workspace_path_invalid",
                path=str(candidate),
            ) from exc
        if stat.S_ISLNK(workspace_stat.st_mode) or _is_reparse_point(workspace_stat):
            raise DocumentationWikiInputError(
                f"Workspace wiki root must not be a symlink: {candidate}",
                category="workspace_symlink_rejected",
                path=str(candidate),
            )
        if not stat.S_ISDIR(workspace_stat.st_mode):
            raise DocumentationWikiInputError(
                f"Workspace wiki path is not a directory: {candidate}",
                category="workspace_not_directory",
                path=str(candidate),
            )
    return resolved


def _validate_source_root(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise DocumentationWikiInputError(
            f"Source root is unavailable: {candidate}",
            category="source_unavailable",
            path=str(candidate),
        ) from exc
    if not resolved.is_dir():
        raise DocumentationWikiInputError(
            f"Source root is not a directory: {resolved}",
            category="source_not_directory",
            path=str(resolved),
        )
    return resolved


def _validate_root_isolation(
    input_root: Path, workspace_root: Path, source_root: Path | None
) -> None:
    if _paths_overlap(input_root, workspace_root):
        raise DocumentationWikiInputError(
            "Workspace wiki directory must be outside the adopted input wiki.",
            category="workspace_input_overlap",
            path=str(workspace_root),
        )
    if source_root is not None and _is_relative_to(workspace_root, source_root):
        raise DocumentationWikiInputError(
            "Workspace wiki directory must be outside the read-only source root.",
            category="workspace_source_overlap",
            path=str(workspace_root),
        )


def _paths_overlap(left: Path, right: Path) -> bool:
    return _is_relative_to(left, right) or _is_relative_to(right, left)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _supports_secure_input_fd_traversal() -> bool:
    return _SECURE_INPUT_FD_TRAVERSAL_AVAILABLE


def _uses_windows_guarded_input_fallback() -> bool:
    return os.name == "nt"


def _input_directory_open_flags(*, root: bool = False) -> int:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    if root:
        no_follow = getattr(os, "O_NOFOLLOW_ANY", no_follow)
    return (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | no_follow
    )


@contextmanager
def _open_input_root_descriptor(
    root: Path,
    *,
    expected_identity: os.stat_result,
) -> Iterator[int | None]:
    """Pin a POSIX input root for the complete validation/copy transaction."""

    try:
        inspected = root.lstat()
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Input wiki root changed before it could be pinned: {root}: {exc}",
            category="input_changed_during_snapshot",
            path=str(root),
        ) from exc
    _assert_input_directory(inspected, path=".")
    if _uses_windows_guarded_input_fallback():
        _assert_windows_input_identity(
            expected_identity,
            inspected,
            path=".",
            operation="pre-open input-root verification",
        )
    else:
        _assert_same_input_identity(
            expected_identity,
            inspected,
            path=".",
            operation="pre-open input-root verification",
        )

    if not _supports_secure_input_fd_traversal():
        if not _uses_windows_guarded_input_fallback():
            raise DocumentationWikiInputError(
                "This platform lacks descriptor-rooted no-follow input traversal.",
                category="secure_input_traversal_unavailable",
                path=str(root),
            )
        with ExitStack() as guard_stack:
            try:
                guard_stack.enter_context(guard_windows_directory_chain(root, ()))
            except _WindowsDirectoryGuardUnavailableError as exc:
                raise DocumentationWikiInputError(
                    f"Cannot securely pin Windows input wiki root {root}: {exc}",
                    category="secure_input_traversal_unavailable",
                    path=".",
                ) from exc
            except OSError as exc:
                raise DocumentationWikiInputError(
                    f"Cannot pin Windows input wiki root {root}: {exc}",
                    category="input_changed_during_snapshot",
                    path=".",
                ) from exc
            try:
                pinned = root.lstat()
            except OSError as exc:
                raise DocumentationWikiInputError(
                    f"Cannot verify pinned Windows input wiki root {root}: {exc}",
                    category="input_changed_during_snapshot",
                    path=".",
                ) from exc
            _assert_input_directory(pinned, path=".")
            _assert_windows_input_identity(
                inspected,
                pinned,
                path=".",
                operation="Windows input-root guard acquisition",
            )

            # Caller exceptions must cross this boundary unchanged.  Only
            # acquisition and the explicit post-yield guard verification are
            # translated into input-root diagnostics.
            yield None
            try:
                after = root.lstat()
            except OSError as exc:
                raise DocumentationWikiInputError(
                    f"Cannot recheck pinned Windows input wiki root {root}: {exc}",
                    category="input_changed_during_snapshot",
                    path=".",
                ) from exc
            _assert_input_directory(after, path=".")
            _assert_windows_input_identity(
                pinned,
                after,
                path=".",
                operation="Windows input-root guard release",
            )
        return

    try:
        descriptor = os.open(root, _input_directory_open_flags(root=True))
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot pin input wiki root {root}: {exc}",
            category="input_unreadable",
            path=str(root),
        ) from exc
    try:
        opened = os.fstat(descriptor)
        _assert_input_directory(opened, path=".")
        _assert_same_input_identity(
            inspected,
            opened,
            path=".",
            operation="input-root open",
        )
        _assert_input_root_path_binding(root, descriptor)
        yield descriptor
    finally:
        os.close(descriptor)


def _assert_input_root_path_binding(root: Path, descriptor: int) -> None:
    try:
        path_stat = root.lstat()
        opened = os.fstat(descriptor)
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Input wiki root changed while it was pinned: {root}: {exc}",
            category="input_changed_during_snapshot",
            path=".",
        ) from exc
    _assert_input_directory(path_stat, path=".")
    _assert_input_directory(opened, path=".")
    _assert_same_input_identity(
        opened,
        path_stat,
        path=".",
        operation="input-root path verification",
    )


def _assert_input_directory(entry_stat: os.stat_result, *, path: str) -> None:
    if (
        stat.S_ISLNK(entry_stat.st_mode)
        or _is_reparse_point(entry_stat)
        or not stat.S_ISDIR(entry_stat.st_mode)
    ):
        raise DocumentationWikiInputError(
            f"Input wiki directory changed or became redirected: {path}",
            category="input_changed_during_snapshot",
            path=path,
        )


def _assert_same_input_identity(
    expected: os.stat_result,
    actual: os.stat_result,
    *,
    path: str,
    operation: str,
) -> None:
    expected_identity = (expected.st_dev, expected.st_ino)
    actual_identity = (actual.st_dev, actual.st_ino)
    if expected_identity != actual_identity:
        raise DocumentationWikiInputError(
            f"Input wiki path changed identity during {operation}: {path}",
            category="input_changed_during_snapshot",
            path=path,
        )


def _assert_windows_input_identity(
    expected: os.stat_result,
    actual: os.stat_result,
    *,
    path: str,
    operation: str,
) -> None:
    try:
        expected_identity = windows_object_identity(
            expected,
            context=f"{operation} before {path}",
        )
        actual_identity = windows_object_identity(
            actual,
            context=f"{operation} after {path}",
        )
    except WindowsIdentityUnavailableError as exc:
        raise DocumentationWikiInputError(
            f"Windows input identity is unavailable during {operation}: {path}",
            category="secure_input_traversal_unavailable",
            path=path,
        ) from exc
    if expected_identity != actual_identity:
        raise DocumentationWikiInputError(
            f"Input wiki path changed identity during {operation}: {path}",
            category="input_changed_during_snapshot",
            path=path,
        )


def _stable_input_metadata(entry_stat: os.stat_result) -> tuple[int, int, int, int]:
    return (
        entry_stat.st_mode,
        entry_stat.st_size,
        entry_stat.st_mtime_ns,
        entry_stat.st_ctime_ns,
    )


def _assert_stable_input_metadata(
    before: os.stat_result,
    after: os.stat_result,
    *,
    path: str,
) -> None:
    if _stable_input_metadata(before) != _stable_input_metadata(after):
        raise DocumentationWikiInputError(
            f"Input wiki file changed while it was being read: {path}",
            category="input_changed_during_snapshot",
            path=path,
        )


def _assert_windows_path_handle_metadata(
    path_metadata: _WindowsPathHandleMetadata,
    handle_metadata: _WindowsPathHandleMetadata,
    *,
    path: str,
    operation: str,
) -> None:
    if path_metadata != handle_metadata:
        raise DocumentationWikiInputError(
            f"Input wiki file changed during {operation}: {path}",
            category="input_changed_during_snapshot",
            path=path,
        )


def _collect_input_tree(
    root: Path,
    *,
    enforce_content_policy: bool,
    root_descriptor: int | None = None,
) -> _InputTree:
    if root_descriptor is not None:
        return _collect_input_tree_descriptor(
            root,
            root_descriptor,
            enforce_content_policy=enforce_content_policy,
        )

    files: list[_InputFile] = []
    rejected: list[str] = []
    portable_paths: dict[str, str] = {}
    budget = _InputResourceBudget()

    def visit_guarded(directory: Path, relative_directory: PurePosixPath) -> None:
        inspected_entries: list[tuple[str, str, os.stat_result]] = []
        try:
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    relative = (
                        PurePosixPath(entry.name)
                        if relative_directory == PurePosixPath(".")
                        else relative_directory / entry.name
                    )
                    budget.observe_entry(relative)
                    inspected_entries.append(
                        (
                            entry.name,
                            entry.path,
                            fresh_no_follow_stat(entry.path),
                        )
                    )
        except OSError as exc:
            rel = relative_directory.as_posix()
            raise DocumentationWikiInputError(
                f"Cannot read wiki directory {rel!r}: {exc}",
                category="input_unreadable",
                path=rel,
            ) from exc

        for name, entry_path, entry_stat in sorted(
            inspected_entries,
            key=lambda item: (item[0].casefold(), item[0]),
        ):
            relative = (
                PurePosixPath(name)
                if relative_directory == PurePosixPath(".")
                else relative_directory / name
            )
            relative_text = relative.as_posix()
            _validate_portable_relative_path(relative, portable_paths)

            if stat.S_ISLNK(entry_stat.st_mode) or _is_reparse_point(entry_stat):
                rejected.append(relative_text)
                continue
            if enforce_content_policy and _is_rejected_content(relative, entry_stat):
                rejected.append(relative_text)
                continue
            if stat.S_ISDIR(entry_stat.st_mode):
                budget.account_directory()
                visit(Path(entry_path), relative, expected_directory=entry_stat)
                continue
            if not stat.S_ISREG(entry_stat.st_mode):
                rejected.append(relative_text)
                continue

            budget.account_file(relative_text, entry_stat.st_size)
            path = Path(entry_path)
            _ensure_resolved_inside(path, root, relative_text)
            hashed = _hash_regular_file(
                path,
                relative_text,
                expected_size=entry_stat.st_size,
                maximum_bytes=MAX_INPUT_WIKI_FILE_BYTES,
                expected_stat=entry_stat,
                windows_guarded=_uses_windows_guarded_input_fallback(),
            )
            inventory_stat = hashed.opened_stat
            files.append(
                _InputFile(
                    path=path,
                    relative_path=relative_text,
                    sha256=hashed.sha256,
                    size=inventory_stat.st_size,
                    mtime_ns=inventory_stat.st_mtime_ns,
                    ctime_ns=inventory_stat.st_ctime_ns,
                    device=inventory_stat.st_dev,
                    inode=inventory_stat.st_ino,
                )
            )

    def visit(
        directory: Path,
        relative_directory: PurePosixPath,
        *,
        expected_directory: os.stat_result | None = None,
    ) -> None:
        if not _uses_windows_guarded_input_fallback():
            visit_guarded(directory, relative_directory)
            return
        components = (
            () if relative_directory == PurePosixPath(".") else relative_directory.parts
        )
        try:
            with guard_windows_directory_chain(root, components):
                if expected_directory is not None:
                    opened_directory = directory.lstat()
                    _assert_input_directory(
                        opened_directory,
                        path=relative_directory.as_posix(),
                    )
                    _assert_windows_input_identity(
                        expected_directory,
                        opened_directory,
                        path=relative_directory.as_posix(),
                        operation="Windows guarded directory traversal",
                    )
                visit_guarded(directory, relative_directory)
        except OSError as exc:
            relative_text = relative_directory.as_posix()
            raise DocumentationWikiInputError(
                "Input wiki directory changed or became redirected while it was "
                f"being inventoried: {relative_text}: {exc}",
                category="input_changed_during_snapshot",
                path=relative_text,
            ) from exc

    root_expected = root.lstat() if _uses_windows_guarded_input_fallback() else None
    visit(root, PurePosixPath("."), expected_directory=root_expected)
    if rejected:
        rejected_entries = tuple(
            sorted(rejected, key=lambda value: (value.casefold(), value))
        )
        raise DocumentationWikiInputError(
            "Input wiki contains symlinked, non-regular, agent-policy, cache, or "
            f"otherwise rejected content: {', '.join(rejected_entries)}",
            category="rejected_input_entries",
            rejected_entries=rejected_entries,
        )

    ordered = tuple(
        sorted(
            files,
            key=lambda entry: (entry.relative_path.casefold(), entry.relative_path),
        )
    )
    return _InputTree(
        root=root,
        files=ordered,
        tree_hash=_tree_hash(ordered),
        entry_count=budget.entry_count,
        directory_count=budget.directory_count,
        maximum_depth=budget.maximum_depth,
    )


def _collect_input_tree_descriptor(
    root: Path,
    root_descriptor: int,
    *,
    enforce_content_policy: bool,
) -> _InputTree:
    """Inventory an input tree without resolving any child through a pathname."""

    files: list[_InputFile] = []
    rejected: list[str] = []
    portable_paths: dict[str, str] = {}
    budget = _InputResourceBudget()

    def visit(directory_descriptor: int, relative_directory: PurePosixPath) -> None:
        inspected_entries: list[tuple[str, os.stat_result]] = []
        try:
            with os.scandir(directory_descriptor) as iterator:
                for entry in iterator:
                    relative = (
                        PurePosixPath(entry.name)
                        if relative_directory == PurePosixPath(".")
                        else relative_directory / entry.name
                    )
                    budget.observe_entry(relative)
                    inspected_entries.append(
                        (entry.name, entry.stat(follow_symlinks=False))
                    )
        except OSError as exc:
            relative_text = relative_directory.as_posix()
            raise DocumentationWikiInputError(
                f"Cannot read pinned wiki directory {relative_text!r}: {exc}",
                category="input_unreadable",
                path=relative_text,
            ) from exc

        for name, entry_stat in sorted(
            inspected_entries,
            key=lambda item: (item[0].casefold(), item[0]),
        ):
            relative = (
                PurePosixPath(name)
                if relative_directory == PurePosixPath(".")
                else relative_directory / name
            )
            relative_text = relative.as_posix()
            _validate_portable_relative_path(relative, portable_paths)

            if stat.S_ISLNK(entry_stat.st_mode) or _is_reparse_point(entry_stat):
                rejected.append(relative_text)
                continue
            if enforce_content_policy and _is_rejected_content(relative, entry_stat):
                rejected.append(relative_text)
                continue
            if stat.S_ISDIR(entry_stat.st_mode):
                budget.account_directory()
                child_descriptor = _open_input_directory_at(
                    directory_descriptor,
                    name,
                    relative_text,
                    inspected=entry_stat,
                )
                try:
                    visit(child_descriptor, relative)
                finally:
                    os.close(child_descriptor)
                continue
            if not stat.S_ISREG(entry_stat.st_mode):
                rejected.append(relative_text)
                continue

            budget.account_file(relative_text, entry_stat.st_size)
            hashed = _hash_input_file_at(
                directory_descriptor,
                name,
                relative_text,
                inspected=entry_stat,
            )
            inventory_stat = hashed.opened_stat
            files.append(
                _InputFile(
                    path=root.joinpath(*relative.parts),
                    relative_path=relative_text,
                    sha256=hashed.sha256,
                    size=inventory_stat.st_size,
                    mtime_ns=inventory_stat.st_mtime_ns,
                    ctime_ns=inventory_stat.st_ctime_ns,
                    device=inventory_stat.st_dev,
                    inode=inventory_stat.st_ino,
                    root_descriptor=root_descriptor,
                )
            )

    visit(root_descriptor, PurePosixPath("."))
    if rejected:
        rejected_entries = tuple(
            sorted(rejected, key=lambda value: (value.casefold(), value))
        )
        raise DocumentationWikiInputError(
            "Input wiki contains symlinked, non-regular, agent-policy, cache, or "
            f"otherwise rejected content: {', '.join(rejected_entries)}",
            category="rejected_input_entries",
            rejected_entries=rejected_entries,
        )
    ordered = tuple(
        sorted(
            files,
            key=lambda entry: (entry.relative_path.casefold(), entry.relative_path),
        )
    )
    return _InputTree(
        root=root,
        files=ordered,
        tree_hash=_tree_hash(ordered),
        entry_count=budget.entry_count,
        directory_count=budget.directory_count,
        maximum_depth=budget.maximum_depth,
    )


def _open_input_directory_at(
    parent_descriptor: int,
    name: str,
    relative_path: str,
    *,
    inspected: os.stat_result,
) -> int:
    try:
        descriptor = os.open(
            name,
            _input_directory_open_flags(),
            dir_fd=parent_descriptor,
        )
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot safely open input wiki directory {relative_path!r}: {exc}",
            category="input_changed_during_snapshot",
            path=relative_path,
        ) from exc
    try:
        opened = os.fstat(descriptor)
        _assert_input_directory(opened, path=relative_path)
        _assert_same_input_identity(
            inspected,
            opened,
            path=relative_path,
            operation="descriptor-relative directory open",
        )
        after = os.stat(
            name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        _assert_input_directory(after, path=relative_path)
        _assert_same_input_identity(
            opened,
            after,
            path=relative_path,
            operation="post-open directory verification",
        )
    except Exception:
        os.close(descriptor)
        raise
    return descriptor


def _assert_input_regular(entry_stat: os.stat_result, *, path: str) -> None:
    if (
        stat.S_ISLNK(entry_stat.st_mode)
        or _is_reparse_point(entry_stat)
        or not stat.S_ISREG(entry_stat.st_mode)
    ):
        raise DocumentationWikiInputError(
            f"Input wiki file changed or became redirected: {path}",
            category="input_changed_during_snapshot",
            path=path,
        )


def _open_input_regular_at(
    parent_descriptor: int,
    name: str,
    relative_path: str,
    *,
    inspected: os.stat_result,
) -> tuple[int, os.stat_result]:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot safely open input wiki file {relative_path!r}: {exc}",
            category="input_changed_during_snapshot",
            path=relative_path,
        ) from exc
    try:
        opened = os.fstat(descriptor)
        _assert_input_regular(opened, path=relative_path)
        _assert_same_input_identity(
            inspected,
            opened,
            path=relative_path,
            operation="descriptor-relative file open",
        )
        _assert_stable_input_metadata(inspected, opened, path=relative_path)
        after = os.stat(
            name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        _assert_input_regular(after, path=relative_path)
        _assert_same_input_identity(
            opened,
            after,
            path=relative_path,
            operation="post-open file verification",
        )
        _assert_stable_input_metadata(opened, after, path=relative_path)
    except Exception:
        os.close(descriptor)
        raise
    return descriptor, opened


def _hash_input_file_at(
    parent_descriptor: int,
    name: str,
    relative_path: str,
    *,
    inspected: os.stat_result,
) -> _HashedInputFile:
    descriptor, opened = _open_input_regular_at(
        parent_descriptor,
        name,
        relative_path,
        inspected=inspected,
    )
    digest = hashlib.sha256()
    bytes_read = 0
    try:
        while True:
            chunk = os.read(
                descriptor,
                min(_INPUT_READ_CHUNK_BYTES, opened.st_size - bytes_read + 1),
            )
            if not chunk:
                break
            bytes_read += len(chunk)
            if bytes_read > opened.st_size:
                raise DocumentationWikiInputError(
                    f"Input wiki file grew while being hashed: {relative_path}",
                    category="input_changed_during_snapshot",
                    path=relative_path,
                )
            digest.update(chunk)
        if bytes_read != opened.st_size:
            raise DocumentationWikiInputError(
                f"Input wiki file size changed while being hashed: {relative_path}",
                category="input_changed_during_snapshot",
                path=relative_path,
            )
        after = os.fstat(descriptor)
        _assert_same_input_identity(
            opened,
            after,
            path=relative_path,
            operation="file hashing",
        )
        _assert_stable_input_metadata(opened, after, path=relative_path)
    finally:
        os.close(descriptor)
    return _HashedInputFile(
        sha256="sha256:" + digest.hexdigest(),
        opened_stat=opened,
    )


@contextmanager
def _open_windows_input_leaf(
    path: Path,
    relative_path: str,
    *,
    expected_stat: os.stat_result | None = None,
    expected_entry: _InputFile | None = None,
):
    """Open a fallback input leaf while its Windows parent chain is pinned."""

    try:
        with open_windows_readonly_file(path) as (handle, opened):
            _assert_input_regular(opened, path=relative_path)
            if expected_stat is not None:
                _assert_windows_input_identity(
                    expected_stat,
                    opened,
                    path=relative_path,
                    operation="Windows guarded file open",
                )
                _assert_windows_path_handle_metadata(
                    _windows_path_handle_metadata(expected_stat),
                    _windows_path_handle_metadata(opened),
                    path=relative_path,
                    operation="Windows guarded file open",
                )
            if expected_entry is not None:
                try:
                    expected_identity = windows_object_identity_from_values(
                        device=expected_entry.device,
                        file_id=expected_entry.inode,
                        context=f"inventoried input {relative_path}",
                    )
                    opened_identity = windows_object_identity(
                        opened,
                        context=f"reopened input {relative_path}",
                    )
                except WindowsIdentityUnavailableError as exc:
                    raise DocumentationWikiInputError(
                        f"Windows input file identity is unavailable: {relative_path}",
                        category="secure_input_traversal_unavailable",
                        path=relative_path,
                    ) from exc
                if (
                    opened_identity != expected_identity
                    or opened.st_size != expected_entry.size
                    or opened.st_mtime_ns != expected_entry.mtime_ns
                    or opened.st_ctime_ns != expected_entry.ctime_ns
                ):
                    raise DocumentationWikiInputError(
                        "Windows input file no longer matches its inventoried "
                        f"identity, size, or timestamps: {relative_path}",
                        category="input_changed_during_snapshot",
                        path=relative_path,
                    )
            yield handle
            after = os.fstat(handle.fileno())
            _assert_windows_input_identity(
                opened,
                after,
                path=relative_path,
                operation="Windows guarded file read",
            )
            _assert_stable_input_metadata(opened, after, path=relative_path)
            try:
                rebound = fresh_no_follow_stat(path)
            except OSError as exc:
                raise DocumentationWikiInputError(
                    "Windows input file disappeared before its guarded path "
                    f"could be rebound: {relative_path}: {exc}",
                    category="input_changed_during_snapshot",
                    path=relative_path,
                ) from exc
            _assert_input_regular(rebound, path=relative_path)
            _assert_windows_input_identity(
                opened,
                rebound,
                path=relative_path,
                operation="Windows guarded file path rebind",
            )
            _assert_windows_path_handle_metadata(
                _windows_path_handle_metadata(rebound),
                _windows_path_handle_metadata(after),
                path=relative_path,
                operation="Windows guarded file path rebind",
            )
    except WindowsFileGuardError as exc:
        raise DocumentationWikiInputError(
            f"Cannot safely open Windows input file {relative_path!r}: {exc}",
            category="input_changed_during_snapshot",
            path=relative_path,
        ) from exc


@contextmanager
def _open_input_entry(entry: _InputFile):
    """Open an inventoried file through its pinned input root when available."""

    if entry.root_descriptor is None:
        if _uses_windows_guarded_input_fallback():
            relative = PurePosixPath(entry.relative_path)
            input_root = entry.path.parents[len(relative.parts) - 1]
            try:
                with guard_windows_directory_chain(
                    input_root,
                    relative.parent.parts,
                ):
                    with _open_windows_input_leaf(
                        entry.path,
                        entry.relative_path,
                        expected_entry=entry,
                    ) as handle:
                        yield handle
            except WindowsDirectoryGuardError as exc:
                raise DocumentationWikiInputError(
                    "Input wiki parent changed before the inventoried file could "
                    f"be opened: {entry.relative_path}: {exc}",
                    category="input_changed_during_snapshot",
                    path=entry.relative_path,
                ) from exc
            return
        with _open_regular_file(entry.path, entry.relative_path) as handle:
            yield handle
        return

    relative = PurePosixPath(entry.relative_path)
    try:
        parent_descriptor = os.dup(entry.root_descriptor)
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot duplicate the pinned input root for {entry.relative_path!r}: "
            f"{exc}",
            category="input_unreadable",
            path=entry.relative_path,
        ) from exc

    file_descriptor: int | None = None
    relative_parent = PurePosixPath(".")
    try:
        for component in relative.parent.parts:
            if component == ".":
                continue
            relative_parent /= component
            try:
                inspected = os.stat(
                    component,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            except OSError as exc:
                raise DocumentationWikiInputError(
                    "Input wiki parent changed before the inventoried file could "
                    f"be opened: {relative_parent.as_posix()}: {exc}",
                    category="input_changed_during_snapshot",
                    path=relative_parent.as_posix(),
                ) from exc
            _assert_input_directory(
                inspected,
                path=relative_parent.as_posix(),
            )
            child_descriptor = _open_input_directory_at(
                parent_descriptor,
                component,
                relative_parent.as_posix(),
                inspected=inspected,
            )
            os.close(parent_descriptor)
            parent_descriptor = child_descriptor

        try:
            inspected = os.stat(
                relative.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise DocumentationWikiInputError(
                "Input wiki file changed before it could be reopened from the "
                f"pinned root: {entry.relative_path}: {exc}",
                category="input_changed_during_snapshot",
                path=entry.relative_path,
            ) from exc
        _assert_input_regular(inspected, path=entry.relative_path)
        file_descriptor, opened = _open_input_regular_at(
            parent_descriptor,
            relative.name,
            entry.relative_path,
            inspected=inspected,
        )
        if (
            opened.st_dev != entry.device
            or opened.st_ino != entry.inode
            or opened.st_size != entry.size
            or opened.st_mtime_ns != entry.mtime_ns
            or opened.st_ctime_ns != entry.ctime_ns
        ):
            raise DocumentationWikiInputError(
                "Input wiki file no longer matches its validated identity or "
                f"metadata: {entry.relative_path}",
                category="input_changed_during_snapshot",
                path=entry.relative_path,
            )

        handle = os.fdopen(file_descriptor, "rb")
        file_descriptor = None
        try:
            yield handle
            after = os.fstat(handle.fileno())
            _assert_same_input_identity(
                opened,
                after,
                path=entry.relative_path,
                operation="descriptor-rooted file read",
            )
            _assert_stable_input_metadata(
                opened,
                after,
                path=entry.relative_path,
            )
        finally:
            handle.close()
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        os.close(parent_descriptor)


def _validate_portable_relative_path(
    relative: PurePosixPath, seen: dict[str, str]
) -> None:
    if relative.is_absolute() or ".." in relative.parts:
        raise DocumentationWikiInputError(
            f"Wiki entry escapes its root: {relative.as_posix()}",
            category="path_escape",
            path=relative.as_posix(),
        )
    for component in relative.parts:
        if component in {"", ".", ".."}:
            raise DocumentationWikiInputError(
                f"Invalid wiki path component in {relative.as_posix()!r}.",
                category="nonportable_path",
                path=relative.as_posix(),
            )
        if component.endswith((" ", ".")) or any(
            char in _WINDOWS_FORBIDDEN_CHARS or ord(char) < 32 for char in component
        ):
            raise DocumentationWikiInputError(
                f"Wiki path is not portable across supported systems: {relative.as_posix()}",
                category="nonportable_path",
                path=relative.as_posix(),
            )
        stem = component.split(".", 1)[0].casefold()
        if stem in _WINDOWS_RESERVED_NAMES:
            raise DocumentationWikiInputError(
                f"Wiki path uses a reserved Windows name: {relative.as_posix()}",
                category="nonportable_path",
                path=relative.as_posix(),
            )

    portable_key = unicodedata.normalize("NFC", relative.as_posix()).casefold()
    previous = seen.setdefault(portable_key, relative.as_posix())
    if previous != relative.as_posix():
        raise DocumentationWikiInputError(
            "Wiki paths collide on a case-insensitive or Unicode-normalizing "
            f"filesystem: {previous!r} and {relative.as_posix()!r}",
            category="nonportable_path_collision",
            path=relative.as_posix(),
            rejected_entries=(previous, relative.as_posix()),
        )


def _is_reparse_point(entry_stat: os.stat_result) -> bool:
    attributes = int(getattr(entry_stat, "st_file_attributes", 0))
    return bool(
        getattr(entry_stat, "st_reparse_tag", 0)
        or attributes & 0x00000400  # FILE_ATTRIBUTE_REPARSE_POINT
    )


def _is_rejected_content(relative: PurePosixPath, entry_stat: os.stat_result) -> bool:
    parts = tuple(part.casefold() for part in relative.parts)
    name = parts[-1]
    if stat.S_ISDIR(entry_stat.st_mode) and name in _REJECTED_DIRECTORY_NAMES:
        return True
    if name in _REJECTED_FILE_NAMES:
        return True
    if name.endswith((".pyc", ".pyo", ".tmp")):
        return True
    relative_lower = "/".join(parts)
    if relative_lower == ".github/copilot-instructions.md":
        return True
    return any(
        relative_lower.startswith(prefix) for prefix in _REJECTED_GITHUB_PREFIXES
    )


def _ensure_resolved_inside(path: Path, root: Path, relative_path: str) -> None:
    try:
        path.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as exc:
        raise DocumentationWikiInputError(
            f"Wiki entry resolves outside its root: {relative_path}",
            category="path_escape",
            path=relative_path,
            rejected_entries=(relative_path,),
        ) from exc


def _hash_regular_file(
    path: Path,
    relative_path: str,
    *,
    expected_size: int | None = None,
    maximum_bytes: int | None = None,
    expected_stat: os.stat_result | None = None,
    windows_guarded: bool = False,
) -> _HashedInputFile:
    hasher = hashlib.sha256()
    bytes_read = 0
    opened_stat: os.stat_result | None = None
    try:
        opener = (
            _open_windows_input_leaf(
                path,
                relative_path,
                expected_stat=expected_stat,
            )
            if windows_guarded
            else _open_regular_file(path, relative_path)
        )
        with opener as handle:
            opened_stat = os.fstat(handle.fileno())
            while True:
                read_size = _INPUT_READ_CHUNK_BYTES
                if expected_size is not None:
                    read_size = min(
                        read_size,
                        expected_size - bytes_read + 1,
                    )
                chunk = handle.read(read_size)
                if not chunk:
                    break
                bytes_read += len(chunk)
                if expected_size is not None and bytes_read > expected_size:
                    raise DocumentationWikiInputError(
                        f"Wiki file grew while being hashed: {relative_path}",
                        category="input_changed_during_snapshot",
                        path=relative_path,
                    )
                if maximum_bytes is not None and bytes_read > maximum_bytes:
                    _raise_input_resource_limit(
                        category="input_file_size_limit_exceeded",
                        message=(
                            f"Input wiki file {relative_path!r} exceeded the "
                            f"{maximum_bytes}-byte per-file limit while being "
                            "hashed. Reduce or externally host the asset before "
                            "adoption."
                        ),
                        path=relative_path,
                        diagnostic=(
                            f"file_bytes>{maximum_bytes} max_file_bytes={maximum_bytes}"
                        ),
                    )
                hasher.update(chunk)
            if expected_size is not None and bytes_read != expected_size:
                raise DocumentationWikiInputError(
                    f"Wiki file size changed while being hashed: {relative_path}",
                    category="input_changed_during_snapshot",
                    path=relative_path,
                )
    except DocumentationWikiInputError:
        raise
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot read wiki file {relative_path!r}: {exc}",
            category="input_unreadable",
            path=relative_path,
        ) from exc
    if opened_stat is None:  # pragma: no cover - the opener either yields or raises
        raise AssertionError("Input file opener yielded no handle metadata.")
    return _HashedInputFile(
        sha256="sha256:" + hasher.hexdigest(),
        opened_stat=opened_stat,
    )


def _open_regular_file(path: Path, relative_path: str):
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot safely open wiki file {relative_path!r}: {exc}",
            category="input_unreadable",
            path=relative_path,
        ) from exc
    try:
        opened_stat = os.fstat(descriptor)
        if not stat.S_ISREG(opened_stat.st_mode) or _is_reparse_point(opened_stat):
            raise DocumentationWikiInputError(
                f"Wiki entry is no longer a regular file: {relative_path}",
                category="input_changed_during_snapshot",
                path=relative_path,
            )
        return os.fdopen(descriptor, "rb")
    except Exception:
        os.close(descriptor)
        raise


def _tree_hash(files: tuple[_InputFile, ...]) -> str:
    hasher = hashlib.sha256()
    for entry in files:
        hasher.update(entry.relative_path.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(entry.sha256.encode("ascii"))
        hasher.update(b"\0")
    return "sha256:" + hasher.hexdigest()


def _load_and_validate_metadata(
    files: Mapping[str, _InputFile],
) -> _ValidatedWikiMetadata:
    manifest_entry = files.get(MANIFEST_FILENAME)
    surface_entry = files.get(SURFACE_INDEX_FILENAME)
    knowledge_entry = files.get(KNOWLEDGE_INDEX_FILENAME)
    if manifest_entry is None and surface_entry is None:
        if knowledge_entry is not None:
            raise DocumentationWikiInputError(
                "A knowledge index cannot be adopted without a manifest and "
                "surface index.",
                category="knowledge_artifact_orphan",
                path=KNOWLEDGE_INDEX_FILENAME,
            )
        return _ValidatedWikiMetadata(
            manifest_payload=None,
            surface_payload=None,
            sync_manifest=None,
            knowledge_artifacts=None,
            artifact_form="legacy_index_only",
            legacy_index_only=True,
        )
    if manifest_entry is None or surface_entry is None:
        missing = (
            MANIFEST_FILENAME if manifest_entry is None else SURFACE_INDEX_FILENAME
        )
        raise DocumentationWikiInputError(
            "Current wiki metadata must include the manifest and surface index "
            f"together; missing {missing}.",
            category="metadata_pair_incomplete",
            path=missing,
        )

    manifest_bytes = _read_verified_bytes(manifest_entry)
    manifest = _decode_json_object(
        manifest_bytes,
        manifest_entry,
        "manifest",
    )
    manifest_version = _validated_manifest_version(manifest)

    surface_bytes = _read_verified_bytes(surface_entry)
    if manifest_version == LEGACY_MANIFEST_VERSION:
        if "artifact_hashes" in manifest or knowledge_entry is not None:
            raise DocumentationWikiInputError(
                "Manifest v4 supports only the legacy manifest/surface pair; "
                "native knowledge requires a marked manifest v5 trio.",
                category="native_artifact_form_invalid",
                path=(
                    KNOWLEDGE_INDEX_FILENAME
                    if knowledge_entry is not None
                    else MANIFEST_FILENAME
                ),
            )
        _validate_legacy_manifest(manifest)
        sync_manifest = _validated_sync_manifest(manifest)
        surface = _decode_json_object(
            surface_bytes,
            surface_entry,
            "surface index",
        )
        _validate_surface_index(surface, files)
        return _ValidatedWikiMetadata(
            manifest_payload=manifest,
            surface_payload=surface,
            sync_manifest=sync_manifest,
            knowledge_artifacts=None,
            artifact_form="manifest_v4_surface",
            legacy_index_only=False,
        )

    sync_manifest = _validated_sync_manifest(manifest)
    surface = _validated_native_surface(surface_bytes)
    canonical_markdown = _validate_native_page_parity(surface, files)
    marker = sync_manifest.artifact_hashes
    if marker is None:
        if knowledge_entry is not None:
            raise DocumentationWikiInputError(
                "A present knowledge index requires the complete manifest v5 "
                "artifact marker.",
                category="native_artifact_marker_missing",
                path=MANIFEST_FILENAME,
            )
        return _ValidatedWikiMetadata(
            manifest_payload=manifest,
            surface_payload=surface,
            sync_manifest=sync_manifest,
            knowledge_artifacts=None,
            artifact_form="manifest_v5_surface",
            legacy_index_only=False,
        )

    if knowledge_entry is None:
        raise DocumentationWikiInputError(
            "The manifest v5 artifact marker commits a knowledge index that is "
            "absent.",
            category="native_artifact_set_incomplete",
            path=KNOWLEDGE_INDEX_FILENAME,
        )
    knowledge_bytes = _read_verified_bytes(knowledge_entry)
    validated = _validated_native_artifacts(
        surface_bytes=surface_bytes,
        knowledge_bytes=knowledge_bytes,
        manifest=sync_manifest,
    )
    _validate_native_marker(marker, validated)
    _validate_native_markdown_snapshot(
        canonical_markdown,
        files,
        validated,
    )
    return _ValidatedWikiMetadata(
        manifest_payload=manifest,
        surface_payload=validated.surface_payload,
        sync_manifest=sync_manifest,
        knowledge_artifacts=validated,
        artifact_form="manifest_v5_native",
        legacy_index_only=False,
    )


def _read_json_object(entry: _InputFile, label: str) -> dict[str, Any]:
    raw = _read_verified_bytes(entry)
    return _decode_json_object(raw, entry, label)


def _decode_json_object(
    raw: bytes,
    entry: _InputFile,
    label: str,
) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate object key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite number {value!r}")

    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise DocumentationWikiInputError(
            f"Corrupt {label} metadata in {entry.relative_path}: {exc}",
            category="metadata_corrupt",
            path=entry.relative_path,
        ) from exc
    if not isinstance(payload, dict):
        raise DocumentationWikiInputError(
            f"Corrupt {label} metadata in {entry.relative_path}: expected an object.",
            category="metadata_corrupt",
            path=entry.relative_path,
        )
    return payload


def _read_verified_bytes(entry: _InputFile) -> bytes:
    _assert_input_files_resource_bounds((entry,))
    try:
        with _open_input_entry(entry) as handle:
            raw = handle.read(entry.size + 1)
    except DocumentationWikiInputError:
        raise
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot read wiki file {entry.relative_path!r}: {exc}",
            category="input_unreadable",
            path=entry.relative_path,
        ) from exc
    if len(raw) != entry.size:
        raise DocumentationWikiInputError(
            f"Wiki file size changed during validation: {entry.relative_path}",
            category="input_changed_during_snapshot",
            path=entry.relative_path,
        )
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    if digest != entry.sha256:
        raise DocumentationWikiInputError(
            f"Wiki file changed during validation: {entry.relative_path}",
            category="input_changed_during_snapshot",
            path=entry.relative_path,
        )
    return raw


def _validated_manifest_version(manifest: Mapping[str, Any]) -> int:
    version = manifest.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise DocumentationWikiInputError(
            "Manifest version must be an integer.",
            category="manifest_schema_invalid",
            path=MANIFEST_FILENAME,
        )
    if version not in SUPPORTED_MANIFEST_VERSIONS:
        relation = "future" if version > MANIFEST_VERSION else "unsupported"
        raise DocumentationWikiInputError(
            f"Manifest version {version} is {relation}; supported versions are "
            f"{LEGACY_MANIFEST_VERSION} and {MANIFEST_VERSION}.",
            category="manifest_schema_unsupported",
            path=MANIFEST_FILENAME,
        )
    return version


def _validated_sync_manifest(manifest: Mapping[str, Any]) -> SyncManifest:
    try:
        return SyncManifest.from_payload(manifest)
    except SyncManifestError as exc:
        raise DocumentationWikiInputError(
            f"Manifest metadata is invalid: {exc}",
            category=(
                "manifest_schema_unsupported"
                if exc.code == "unsupported-version"
                else "manifest_schema_invalid"
            ),
            path=MANIFEST_FILENAME,
            diagnostics=(f"field={exc.field}",),
        ) from exc


def _validate_legacy_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("version") != LEGACY_MANIFEST_VERSION:
        raise DocumentationWikiInputError(
            "Legacy manifest validation requires manifest version 4.",
            category="manifest_schema_invalid",
            path=MANIFEST_FILENAME,
        )
    sources = manifest.get("sources")
    if not isinstance(sources, dict):
        raise DocumentationWikiInputError(
            "Manifest sources must be an object.",
            category="manifest_schema_invalid",
            path=MANIFEST_FILENAME,
        )
    for source_path, info in sources.items():
        if not isinstance(source_path, str) or not _is_safe_posix_relative(source_path):
            raise DocumentationWikiInputError(
                f"Manifest contains an unsafe source path: {source_path!r}.",
                category="manifest_schema_invalid",
                path=MANIFEST_FILENAME,
            )
        if not isinstance(info, dict) or not _is_sha256(info.get("hash")):
            raise DocumentationWikiInputError(
                f"Manifest source {source_path!r} lacks a valid content hash.",
                category="manifest_schema_invalid",
                path=MANIFEST_FILENAME,
            )
        semantic_hash = info.get("semantic_hash")
        if semantic_hash is not None and not _is_sha256(semantic_hash):
            raise DocumentationWikiInputError(
                f"Manifest source {source_path!r} has an invalid semantic hash.",
                category="manifest_schema_invalid",
                path=MANIFEST_FILENAME,
            )
    for field_name in ("surfaces", "generation_inputs"):
        value = manifest.get(field_name, {})
        if not isinstance(value, dict):
            raise DocumentationWikiInputError(
                f"Manifest {field_name} must be an object.",
                category="manifest_schema_invalid",
                path=MANIFEST_FILENAME,
            )
    _validate_generation_inputs(manifest.get("generation_inputs", {}))


def _validate_generation_inputs(generation_inputs: Mapping[str, Any]) -> None:
    unsupported = sorted(set(generation_inputs) - _SUPPORTED_GENERATION_INPUTS)
    if unsupported:
        raise DocumentationWikiInputError(
            f"Manifest generation_inputs contains unsupported key {unsupported[0]!r}.",
            category="manifest_schema_invalid",
            path=MANIFEST_FILENAME,
        )
    if "openapi" not in generation_inputs:
        return

    openapi = generation_inputs["openapi"]
    if not isinstance(openapi, dict):
        raise DocumentationWikiInputError(
            "Manifest generation_inputs.openapi must be an object.",
            category="manifest_schema_invalid",
            path=MANIFEST_FILENAME,
        )
    fields = set(openapi)
    if fields != _OPENAPI_GENERATION_INPUT_FIELDS:
        missing = sorted(_OPENAPI_GENERATION_INPUT_FIELDS - fields)
        extra = sorted(fields - _OPENAPI_GENERATION_INPUT_FIELDS)
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"unsupported {', '.join(extra)}")
        raise DocumentationWikiInputError(
            "Manifest generation_inputs.openapi fields are invalid: "
            + "; ".join(details)
            + ".",
            category="manifest_schema_invalid",
            path=MANIFEST_FILENAME,
        )

    openapi_path = openapi["path"]
    if not isinstance(openapi_path, str) or not _is_portable_source_relative_path(
        openapi_path
    ):
        raise DocumentationWikiInputError(
            "Manifest generation_inputs.openapi.path must be a portable, "
            "source-relative POSIX path.",
            category="manifest_schema_invalid",
            path=MANIFEST_FILENAME,
        )
    if not _is_sha256(openapi["sha256"]):
        raise DocumentationWikiInputError(
            "Manifest generation_inputs.openapi.sha256 must use sha256:<hex> form.",
            category="manifest_schema_invalid",
            path=MANIFEST_FILENAME,
        )
    openapi_format = openapi["format"]
    if not isinstance(openapi_format, str) or openapi_format not in {"json", "yaml"}:
        raise DocumentationWikiInputError(
            "Manifest generation_inputs.openapi.format must be 'json' or 'yaml'.",
            category="manifest_schema_invalid",
            path=MANIFEST_FILENAME,
        )


def _validated_native_surface(surface_bytes: bytes) -> Mapping[str, Any]:
    try:
        return validate_surface_index_bytes(surface_bytes)
    except KnowledgeArtifactError as exc:
        raise DocumentationWikiInputError(
            f"Native surface index is invalid: {exc}",
            category=(
                "surface_schema_unsupported"
                if exc.code == "unsupported-schema-version"
                else "surface_schema_invalid"
            ),
            path=SURFACE_INDEX_FILENAME,
            diagnostics=(f"field={exc.field}",),
        ) from exc


def _validated_native_artifacts(
    *,
    surface_bytes: bytes,
    knowledge_bytes: bytes,
    manifest: SyncManifest,
) -> ValidatedKnowledgeArtifacts:
    try:
        return validate_knowledge_artifacts(
            surface_index_bytes=surface_bytes,
            knowledge_index_bytes=knowledge_bytes,
            manifest=manifest,
        )
    except KnowledgeArtifactError as exc:
        if exc.field.startswith("knowledge_index"):
            path = KNOWLEDGE_INDEX_FILENAME
            category = (
                "knowledge_schema_unsupported"
                if exc.code == "unsupported-schema-version"
                else "native_artifact_invalid"
            )
        elif exc.field.startswith("surface_index"):
            path = SURFACE_INDEX_FILENAME
            category = (
                "surface_schema_unsupported"
                if exc.code == "unsupported-schema-version"
                else "native_artifact_invalid"
            )
        else:
            path = MANIFEST_FILENAME
            category = "native_artifact_invalid"
        raise DocumentationWikiInputError(
            f"Native artifact set is invalid: {exc}",
            category=category,
            path=path,
            diagnostics=(f"field={exc.field}",),
        ) from exc


def _validate_native_marker(
    marker: ManifestArtifactHashes,
    validated: ValidatedKnowledgeArtifacts,
) -> None:
    for field_name, committed, actual in (
        (
            "surface_index_hash",
            marker.surface_index_hash,
            validated.surface_index_hash,
        ),
        (
            "knowledge_index_hash",
            marker.knowledge_index_hash,
            validated.knowledge_index_hash,
        ),
        (
            "evaluated_envelope_hash",
            marker.evaluated_envelope_hash,
            validated.evaluated_envelope_hash,
        ),
    ):
        if committed == actual:
            continue
        raise DocumentationWikiInputError(
            f"Manifest artifact marker {field_name} does not match the validated "
            "native projection.",
            category="native_artifact_marker_mismatch",
            path=MANIFEST_FILENAME,
            diagnostics=(f"field=artifact_hashes.{field_name}",),
        )


def _validate_native_page_parity(
    surface: Mapping[str, Any],
    files: Mapping[str, _InputFile],
) -> Mapping[str, _InputFile]:
    canonical = _canonical_markdown_entries(files)
    pages = surface["pages"]
    assert isinstance(pages, list)
    surface_paths = {
        str(page["canonical_path"]) for page in pages if isinstance(page, Mapping)
    }
    canonical_paths = set(canonical)
    if surface_paths != canonical_paths:
        missing = sorted(canonical_paths - surface_paths)
        if missing:
            detail = f"surface index is missing active canonical page {missing[0]!r}"
        else:
            extra = sorted(surface_paths - canonical_paths)
            detail = f"surface index points to missing canonical page {extra[0]!r}"
        raise DocumentationWikiInputError(
            f"Native surface/page parity is invalid: {detail}.",
            category="native_page_parity_mismatch",
            path=SURFACE_INDEX_FILENAME,
        )
    return canonical


def _canonical_markdown_entries(
    files: Mapping[str, _InputFile],
) -> dict[str, _InputFile]:
    root_paths: set[str] = set()
    directories: set[str] = set()
    for entry in iter_page_kinds():
        if entry.requires_page_id:
            if entry.directory is not None:
                directories.add(entry.directory)
        else:
            root_paths.add(entry.path_pattern)

    canonical: dict[str, _InputFile] = {}
    for relative_path, input_file in files.items():
        if relative_path in root_paths:
            canonical[relative_path] = input_file
            continue
        path = PurePosixPath(relative_path)
        if (
            len(path.parts) == 2
            and path.parts[0] in directories
            and path.suffix.casefold() == ".md"
            and is_safe_page_id(path.stem)
        ):
            canonical[relative_path] = input_file
    return canonical


def _validate_native_markdown_snapshot(
    canonical_markdown: Mapping[str, _InputFile],
    files: Mapping[str, _InputFile],
    validated: ValidatedKnowledgeArtifacts,
) -> None:
    # Require the exact mapping returned by the parity check to still identify
    # the guarded inventory before any file bytes are read.
    if any(files.get(path) is not entry for path, entry in canonical_markdown.items()):
        raise DocumentationWikiInputError(
            "Canonical Markdown inventory changed during native validation.",
            category="input_changed_during_snapshot",
        )
    markdown_bytes = {
        path: _read_verified_bytes(entry)
        for path, entry in sorted(canonical_markdown.items())
    }
    try:
        markdown_hash = hash_markdown_snapshot(markdown_bytes)
    except (KnowledgeEnvelopeError, TypeError, UnicodeError, ValueError) as exc:
        raise DocumentationWikiInputError(
            f"Canonical Markdown cannot be validated: {exc}",
            category="native_markdown_snapshot_invalid",
            path=getattr(exc, "field", None),
        ) from exc
    committed_hash = validated.knowledge.bundle.snapshot.markdown_snapshot_hash
    if markdown_hash != committed_hash:
        raise DocumentationWikiInputError(
            "Canonical Markdown does not match the committed native knowledge "
            "snapshot.",
            category="native_markdown_snapshot_mismatch",
            path=KNOWLEDGE_INDEX_FILENAME,
            diagnostics=("field=bundle.snapshot.markdown_snapshot_hash",),
        )


def _validate_surface_index(
    surface: Mapping[str, Any], files: Mapping[str, _InputFile]
) -> None:
    schema = surface.get("schema_version")
    if schema != WIKI_SURFACE_INDEX_SCHEMA_VERSION:
        relation = "future or unsupported"
        raise DocumentationWikiInputError(
            f"Surface schema {schema!r} is {relation}; supported schema is "
            f"{WIKI_SURFACE_INDEX_SCHEMA_VERSION!r}.",
            category="surface_schema_unsupported",
            path=SURFACE_INDEX_FILENAME,
        )
    pages = surface.get("pages")
    if not isinstance(pages, list):
        raise DocumentationWikiInputError(
            "Surface index pages must be an array.",
            category="surface_schema_invalid",
            path=SURFACE_INDEX_FILENAME,
        )
    seen: set[str] = set()
    for page in pages:
        if not isinstance(page, dict):
            raise DocumentationWikiInputError(
                "Surface index page entries must be objects.",
                category="surface_schema_invalid",
                path=SURFACE_INDEX_FILENAME,
            )
        canonical_path = page.get("canonical_path")
        if not isinstance(canonical_path, str) or not _is_safe_posix_relative(
            canonical_path
        ):
            raise DocumentationWikiInputError(
                f"Surface index contains an unsafe canonical path: {canonical_path!r}.",
                category="surface_schema_invalid",
                path=SURFACE_INDEX_FILENAME,
            )
        if canonical_path in seen:
            raise DocumentationWikiInputError(
                f"Surface index repeats canonical path {canonical_path!r}.",
                category="surface_schema_invalid",
                path=SURFACE_INDEX_FILENAME,
            )
        seen.add(canonical_path)
        if canonical_path not in files:
            raise DocumentationWikiInputError(
                f"Surface index points to missing wiki page {canonical_path!r}.",
                category="surface_schema_invalid",
                path=SURFACE_INDEX_FILENAME,
            )
    source_hash = surface.get("source_hash")
    if source_hash is not None and not _is_sha256(source_hash):
        raise DocumentationWikiInputError(
            "Surface index source_hash must use sha256:<hex> form.",
            category="surface_schema_invalid",
            path=SURFACE_INDEX_FILENAME,
        )


def _is_safe_posix_relative(value: str) -> bool:
    if not value or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "." not in path.parts


def _is_portable_source_relative_path(value: str) -> bool:
    raw_components = value.split("/")
    if not _is_safe_posix_relative(value) or any(
        component in {"", ".", ".."} for component in raw_components
    ):
        return False
    for component in raw_components:
        if component.endswith((" ", ".")) or any(
            char in _WINDOWS_FORBIDDEN_CHARS or ord(char) < 32 for char in component
        ):
            return False
        if component.split(".", 1)[0].casefold() in _WINDOWS_RESERVED_NAMES:
            return False
    return True


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(_HASH_RE.fullmatch(value))


def _unknown_entries(files: tuple[_InputFile, ...]) -> tuple[str, ...]:
    unknown = [
        entry.relative_path
        for entry in files
        if not _is_known_wiki_path(entry.relative_path)
    ]
    return tuple(unknown)


def _is_known_wiki_path(relative_path: str) -> bool:
    path = PurePosixPath(relative_path)
    if len(path.parts) == 1:
        return relative_path in _CANONICAL_ROOT_FILES
    first = path.parts[0]
    if first == "assets":
        return True
    return (
        first in _CANONICAL_MARKDOWN_DIRS
        and len(path.parts) == 2
        and path.suffix.casefold() == ".md"
        and is_safe_page_id(path.stem)
    )


def _inspect_markdown(
    files: tuple[_InputFile, ...],
) -> _MarkdownInspection:
    _assert_input_files_resource_bounds(files)
    markdown_files = tuple(
        entry
        for entry in files
        if PurePosixPath(entry.relative_path).suffix.casefold() == ".md"
    )
    semantic_total_bytes = _assert_semantic_markdown_resource_bounds(markdown_files)
    semantic_paths: list[str] = []
    generated_marker_counts: dict[str, int] = {}
    captured_markers: dict[str, list[dict[str, Any]]] = {}
    captured_total = 0
    for entry in markdown_files:
        raw = _read_verified_bytes(entry)
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentationWikiInputError(
                f"Markdown page is not valid UTF-8: {entry.relative_path}",
                category="markdown_invalid_encoding",
                path=entry.relative_path,
            ) from exc
        _validate_markdown_link_targets(entry.relative_path, content)
        semantic_paths.append(entry.relative_path)
        marker_count = 0
        page_records: list[dict[str, Any]] = []
        for match in _GENERATED_MARKER_RE.finditer(content):
            marker_count += 1
            if (
                len(page_records) < MAX_GENERATED_MARKER_RECORDS_PER_PAGE
                and captured_total < MAX_GENERATED_MARKER_RECORDS_TOTAL
            ):
                page_records.append(_generated_marker_record(content, match))
                captured_total += 1
        if marker_count:
            generated_marker_counts[entry.relative_path] = marker_count
        if page_records:
            captured_markers[entry.relative_path] = page_records

    generated_markers = _build_generated_marker_evidence(
        generated_marker_counts,
        captured_markers,
    )
    return _MarkdownInspection(
        semantic_paths=tuple(semantic_paths),
        generated_marker_counts=generated_marker_counts,
        generated_markers=generated_markers,
        semantic_file_count=len(markdown_files),
        semantic_total_bytes=semantic_total_bytes,
    )


def _assert_semantic_markdown_resource_bounds(
    markdown_files: tuple[_InputFile, ...],
) -> int:
    total_bytes = 0
    for entry in markdown_files:
        if entry.size > MAX_INPUT_WIKI_SEMANTIC_FILE_BYTES:
            _raise_input_resource_limit(
                category="input_semantic_file_size_limit_exceeded",
                message=(
                    f"Markdown page {entry.relative_path!r} is {entry.size} bytes, "
                    f"exceeding the {MAX_INPUT_WIKI_SEMANTIC_FILE_BYTES}-byte "
                    "semantic-inspection limit. Split the page before adoption."
                ),
                path=entry.relative_path,
                diagnostic=(
                    f"semantic_file_bytes={entry.size} "
                    "max_semantic_file_bytes="
                    f"{MAX_INPUT_WIKI_SEMANTIC_FILE_BYTES}"
                ),
            )
        total_bytes += entry.size
        if total_bytes > MAX_INPUT_WIKI_SEMANTIC_TOTAL_BYTES:
            _raise_input_resource_limit(
                category="input_semantic_total_size_limit_exceeded",
                message=(
                    f"Markdown content would total {total_bytes} bytes, exceeding "
                    f"the {MAX_INPUT_WIKI_SEMANTIC_TOTAL_BYTES}-byte aggregate "
                    f"semantic-inspection limit at {entry.relative_path!r}. Split "
                    "the wiki before adoption."
                ),
                path=entry.relative_path,
                diagnostic=(
                    f"semantic_total_bytes={total_bytes} "
                    "max_semantic_total_bytes="
                    f"{MAX_INPUT_WIKI_SEMANTIC_TOTAL_BYTES}"
                ),
            )
    return total_bytes


def _generated_marker_record(content: str, match: re.Match[str]) -> dict[str, Any]:
    digest, byte_length = _hash_text_span(content, match.start(), match.end())
    marker_type = (
        "html_comment" if content.startswith("<!--", match.start()) else "legacy_line"
    )
    return {
        "type": marker_type,
        "sha256": digest,
        "byte_length": byte_length,
    }


def _hash_text_span(content: str, start: int, end: int) -> tuple[str, int]:
    hasher = hashlib.sha256()
    byte_length = 0
    offset = start
    while offset < end:
        chunk_end = min(end, offset + _MARKER_HASH_CHUNK_CHARS)
        encoded = content[offset:chunk_end].encode("utf-8")
        hasher.update(encoded)
        byte_length += len(encoded)
        offset = chunk_end
    return "sha256:" + hasher.hexdigest(), byte_length


def _build_generated_marker_evidence(
    marker_counts: Mapping[str, int],
    captured_markers: Mapping[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    retained = {path: list(records) for path, records in captured_markers.items()}
    while True:
        payload = _generated_marker_evidence_payload(marker_counts, retained)
        encoded = json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(encoded) <= MAX_GENERATED_MARKER_EVIDENCE_BYTES:
            return payload
        last_path = next(
            (path for path in reversed(tuple(retained)) if retained[path]),
            None,
        )
        if last_path is None:
            raise DocumentationWikiInputError(
                "Generated-marker evidence metadata exceeds its fixed byte limit.",
                category="generated_marker_evidence_limit_exceeded",
                diagnostics=(
                    "max_generated_marker_evidence_bytes="
                    f"{MAX_GENERATED_MARKER_EVIDENCE_BYTES}",
                ),
            )
        retained[last_path].pop()
        if not retained[last_path]:
            del retained[last_path]


def _generated_marker_evidence_payload(
    marker_counts: Mapping[str, int],
    captured_markers: Mapping[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    captured_count = sum(len(records) for records in captured_markers.values())
    total_count = sum(marker_counts.values())
    pages = {
        path: {
            "count": marker_counts[path],
            "captured_count": len(records),
            "truncated": marker_counts[path] > len(records),
            "markers": list(records),
        }
        for path, records in captured_markers.items()
    }
    return {
        "schema_version": GENERATED_MARKER_EVIDENCE_SCHEMA_VERSION,
        "total_count": total_count,
        "captured_count": captured_count,
        "pages_with_markers": len(marker_counts),
        "truncated": captured_count < total_count,
        "limits": {
            "records_per_page": MAX_GENERATED_MARKER_RECORDS_PER_PAGE,
            "records_total": MAX_GENERATED_MARKER_RECORDS_TOTAL,
            "serialized_bytes": MAX_GENERATED_MARKER_EVIDENCE_BYTES,
        },
        "pages": pages,
    }


def _validate_markdown_link_targets(relative_path: str, content: str) -> None:
    page_parent = PurePosixPath(relative_path).parent
    for link in iter_markdown_link_targets(strip_fenced_code_blocks(content)):
        target = link.target
        try:
            parsed = urlsplit(target)
        except ValueError as exc:
            raise DocumentationWikiInputError(
                f"Markdown page contains an invalid link target: {relative_path}",
                category="unsafe_markdown_link",
                path=relative_path,
            ) from exc
        if parsed.scheme:
            if parsed.scheme.casefold() not in {"http", "https", "mailto"}:
                raise DocumentationWikiInputError(
                    "Markdown page contains a non-portable or unsafe link scheme "
                    f"{parsed.scheme!r}: {relative_path}",
                    category="unsafe_markdown_link",
                    path=relative_path,
                )
            continue
        if parsed.netloc:
            continue
        local_path = local_link_path(link.raw_target)
        if local_path is None:
            continue
        if local_path.startswith(("/", "//")) or re.match(r"^[A-Za-z]:/", local_path):
            raise DocumentationWikiInputError(
                f"Markdown link escapes the wiki root: {relative_path} -> {local_path}",
                category="unsafe_markdown_link",
                path=relative_path,
            )
        stack: list[str] = []
        for component in (page_parent / PurePosixPath(local_path)).parts:
            if component in {"", "."}:
                continue
            if component == "..":
                if not stack:
                    raise DocumentationWikiInputError(
                        "Markdown link escapes the wiki root: "
                        f"{relative_path} -> {local_path}",
                        category="unsafe_markdown_link",
                        path=relative_path,
                    )
                stack.pop()
                continue
            if component.endswith((" ", ".")) or any(
                character in _WINDOWS_FORBIDDEN_CHARS or ord(character) < 32
                for character in component
            ):
                raise DocumentationWikiInputError(
                    "Markdown link uses a non-portable path: "
                    f"{relative_path} -> {local_path}",
                    category="unsafe_markdown_link",
                    path=relative_path,
                )
            if component.split(".", 1)[0].casefold() in _WINDOWS_RESERVED_NAMES:
                raise DocumentationWikiInputError(
                    "Markdown link uses a reserved Windows path: "
                    f"{relative_path} -> {local_path}",
                    category="unsafe_markdown_link",
                    path=relative_path,
                )
            stack.append(component)


def _semantic_page_records(
    files: tuple[_InputFile, ...],
    surface: Mapping[str, Any] | None,
    *,
    generated_marker_counts: Mapping[str, int],
) -> tuple[Mapping[str, Any], ...]:
    source_by_page: dict[str, str | None] = {}
    if surface is not None:
        for page in surface.get("pages", []):
            canonical_path = page.get("canonical_path")
            source_path = page.get("source_path")
            if isinstance(canonical_path, str):
                source_by_page[canonical_path] = (
                    source_path if isinstance(source_path, str) else None
                )

    records: list[Mapping[str, Any]] = []
    for entry in files:
        if PurePosixPath(entry.relative_path).suffix.casefold() != ".md":
            continue
        compatible = _is_known_wiki_path(entry.relative_path)
        records.append(
            {
                "canonical_path": entry.relative_path,
                "sha256": entry.sha256,
                "source_path": source_by_page.get(entry.relative_path),
                "compatible": compatible,
                "compatibility": "recognized" if compatible else "unknown_path",
                "imported_classification": (
                    "needs_grounding" if compatible else "incompatible"
                ),
                "grounding_status": "unknown",
                "preserved_byte_for_byte": True,
                "generated_marker_count": generated_marker_counts.get(
                    entry.relative_path, 0
                ),
            }
        )
    return tuple(records)


def _resolve_metadata_freshness(
    metadata: _ValidatedWikiMetadata,
    *,
    source_root: Path | None,
    trust_source_plugins: bool,
    helper_cache_dir: str | Path | None,
) -> tuple[str, tuple[str, ...], list[str]]:
    """Select legacy comparison or the fail-closed native evaluation seam.

    A run-specific private adapter can extend this function with trusted plugin
    and helper-cache inputs while the exported adoption signature remains
    unchanged.  The validated v5 ``SyncManifest`` and knowledge bundle are
    available together on ``metadata`` and no input path needs to be reopened.
    """

    if metadata.artifact_form == "manifest_v5_surface":
        if source_root is None:
            return (
                "unverified",
                (),
                ["source_unavailable: source freshness cannot be verified"],
            )
        return (
            "unverified",
            (),
            [
                "native_freshness_pending: validated manifest v5 state requires "
                "shared live generation and producer evaluation"
            ],
        )
    if metadata.artifact_form == "manifest_v5_native":
        if source_root is None:
            return (
                "unverified",
                (),
                ["source_unavailable: source freshness cannot be verified"],
            )
        if (
            metadata.sync_manifest is None
            or metadata.knowledge_artifacts is None
        ):
            return (
                "unverified",
                (),
                [
                    "native_freshness_invalid: validated native state is "
                    "incomplete"
                ],
            )
        from .documentation_native import evaluate_documentation_native_freshness

        try:
            evaluated = evaluate_documentation_native_freshness(
                knowledge=metadata.knowledge_artifacts.knowledge,
                manifest=metadata.sync_manifest,
                source_root=source_root,
                trust_source_plugins=trust_source_plugins,
                helper_cache_dir=helper_cache_dir,
            )
        except Exception:  # Fail closed across extractor/plugin/runtime boundaries.
            return (
                "unverified",
                (),
                [
                    "native_freshness_invalid: live native evaluation could not "
                    "be constructed"
                ],
            )
        if evaluated.current:
            return (
                "verified_current",
                (),
                [
                    "native_verified_current: source inventory and native "
                    "generation and producer bases match"
                ],
            )
        diagnostics = [
            f"native_basis_incompatible:{reason}"
            for reason in evaluated.reasons
        ]
        if not diagnostics:
            diagnostics.append(
                "native_basis_incompatible: live native evaluation did not "
                "establish a current state"
            )
        return (
            "verified_stale",
            tuple(evaluated.source_mismatches),
            diagnostics,
        )
    return _resolve_freshness(
        metadata.manifest_payload,
        legacy=metadata.legacy_index_only,
        source_root=source_root,
    )


def _resolve_freshness(
    manifest: Mapping[str, Any] | None,
    *,
    legacy: bool,
    source_root: Path | None,
) -> tuple[str, tuple[str, ...], list[str]]:
    diagnostics: list[str] = []
    if source_root is None:
        diagnostics.append("source_unavailable: source freshness cannot be verified")
        return "unverified", (), diagnostics
    if legacy or manifest is None:
        diagnostics.append(
            "legacy_provenance: source exists but the input wiki has no manifest "
            "to compare"
        )
        return "unverified", (), diagnostics
    sources = manifest["sources"]
    include_tests = (
        ("go",)
        if any(PurePosixPath(path).name.endswith("_test.go") for path in sources)
        else ()
    )
    current_source_paths = set(
        build_source_snapshot(
            source_root,
            include_tests=include_tests,
        ).all_source_paths
    )
    manifest_source_paths = set(sources)
    generation_inputs = manifest.get("generation_inputs", {})
    if not sources and not current_source_paths and not generation_inputs:
        diagnostics.append(
            "empty_manifest_sources: source freshness cannot be established from an "
            "empty manifest"
        )
        return "unverified", (), diagnostics

    mismatches = [
        f"added:{relative_path}"
        for relative_path in sorted(current_source_paths - manifest_source_paths)
    ]
    mismatches.extend(
        f"removed:{relative_path}"
        for relative_path in sorted(manifest_source_paths - current_source_paths)
    )
    for relative_path in sorted(current_source_paths & manifest_source_paths):
        info = sources[relative_path]
        mismatch = _compare_source_file(source_root, relative_path, info["hash"])
        if mismatch is not None:
            if mismatch == f"missing:{relative_path}":
                mismatch = f"removed:{relative_path}"
            mismatches.append(mismatch)
    mismatches.extend(_compare_generation_inputs(source_root, generation_inputs))
    if mismatches:
        diagnostics.append(
            f"source_stale: {len(mismatches)} source inventory item(s) differ"
        )
        return "verified_stale", tuple(mismatches), diagnostics
    diagnostics.append(
        "source_verified_current: supported source inventory, generation inputs, "
        "and manifest hashes match"
    )
    return "verified_current", (), diagnostics


def _compare_generation_inputs(
    source_root: Path,
    generation_inputs: Mapping[str, Any],
) -> list[str]:
    openapi = generation_inputs.get("openapi")
    if not isinstance(openapi, Mapping):
        return []
    relative_path = str(openapi["path"])
    mismatch = _compare_source_file(
        source_root,
        relative_path,
        str(openapi["sha256"]),
    )
    if mismatch is None:
        return []
    reason, _, _ = mismatch.partition(":")
    if reason == "missing":
        reason = "removed"
    return [f"generation_input_{reason}:openapi:{relative_path}"]


def _compare_source_file(
    source_root: Path, relative_path: str, expected_hash: str
) -> str | None:
    relative = PurePosixPath(relative_path)
    candidate = source_root.joinpath(*relative.parts)
    try:
        source_stat = candidate.lstat()
    except FileNotFoundError:
        return f"missing:{relative_path}"
    except OSError:
        return f"unreadable:{relative_path}"
    if stat.S_ISLNK(source_stat.st_mode) or _is_reparse_point(source_stat):
        return f"symlink:{relative_path}"
    if not stat.S_ISREG(source_stat.st_mode):
        return f"non_regular:{relative_path}"
    try:
        candidate.resolve(strict=True).relative_to(source_root)
    except (OSError, ValueError):
        return f"path_escape:{relative_path}"
    actual_hash = _hash_regular_file(candidate, relative_path).sha256
    if actual_hash != expected_hash:
        return f"changed:{relative_path}"
    return None


def _enforce_freshness_policy(
    policy: str,
    freshness: str,
    *,
    source_available: bool,
    diagnostics: list[str],
) -> bool:
    if freshness == "verified_current":
        return False
    if policy == "require-current":
        raise DocumentationWikiInputError(
            f"Input wiki freshness is {freshness}; require-current refuses adoption. "
            "Choose allow-unverified or refresh-snapshot explicitly.",
            category="freshness_not_current",
            diagnostics=tuple(diagnostics),
        )
    if policy == "allow-unverified":
        diagnostics.append(
            f"allow_unverified_selected: continuing with {freshness} input"
        )
        return False
    if not source_available:
        raise DocumentationWikiInputError(
            "refresh-snapshot requires a readable source root; use allow-unverified "
            "for wiki-only authoring.",
            category="refresh_source_required",
            diagnostics=tuple(diagnostics),
        )
    return True


def _require_empty_workspace(workspace_root: Path) -> None:
    if workspace_root.exists():
        try:
            with os.scandir(workspace_root) as entries:
                first_entry = next(entries, None)
        except OSError as exc:
            raise DocumentationWikiInputError(
                f"Cannot inspect workspace wiki directory {workspace_root}: {exc}",
                category="workspace_unreadable",
                path=str(workspace_root),
            ) from exc
        if first_entry is not None:
            raise DocumentationWikiInputError(
                f"Workspace wiki directory must be empty: {workspace_root}",
                category="workspace_not_empty",
                path=str(workspace_root),
            )


def _rollback_partial_workspace_snapshot(
    workspace_root: Path,
    *,
    expected_identity: os.stat_result,
    preserve_root: bool,
) -> None:
    """Remove only the empty workspace root populated by this adoption attempt."""

    try:
        current = workspace_root.lstat()
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot inspect the partial workspace snapshot: {workspace_root}: {exc}",
            category="workspace_rollback_failed",
            path=str(workspace_root),
        ) from exc
    _assert_safe_workspace_directory(current, path=workspace_root)
    _assert_same_workspace_identity(
        expected_identity,
        current,
        path=workspace_root,
        operation="failed-adoption rollback",
    )

    try:
        shutil.rmtree(workspace_root)
        if preserve_root:
            workspace_root.mkdir(parents=False, exist_ok=False)
            restored = workspace_root.lstat()
            _assert_safe_workspace_directory(restored, path=workspace_root)
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot remove the partial workspace snapshot: {workspace_root}: {exc}",
            category="workspace_rollback_failed",
            path=str(workspace_root),
        ) from exc


def _supports_secure_directory_fd_copy() -> bool:
    """Return whether descriptor-relative, no-follow output creation is available."""

    return _SECURE_DIRECTORY_FD_COPY_AVAILABLE


def _uses_windows_guarded_copy_fallback() -> bool:
    return os.name == "nt"


def _workspace_identity(
    entry_stat: os.stat_result,
    *,
    path: Path | str,
    operation: str,
) -> tuple[int, int] | WindowsObjectIdentity:
    if os.name != "nt":
        return entry_stat.st_dev, entry_stat.st_ino
    try:
        return windows_object_identity(
            entry_stat,
            context=f"{operation} workspace {path}",
        )
    except WindowsIdentityUnavailableError as exc:
        raise DocumentationWikiInputError(
            f"Windows workspace identity is unavailable during {operation}: {path}",
            category="workspace_redirection_rejected",
            path=str(path),
        ) from exc


def _assert_same_workspace_identity(
    expected: os.stat_result,
    actual: os.stat_result,
    *,
    path: Path | str,
    operation: str,
) -> None:
    if _workspace_identity(
        expected,
        path=path,
        operation=operation,
    ) != _workspace_identity(
        actual,
        path=path,
        operation=operation,
    ):
        raise DocumentationWikiInputError(
            f"Workspace path changed identity during {operation}: {path}",
            category="workspace_redirection_rejected",
            path=str(path),
        )


def _assert_safe_workspace_directory(
    entry_stat: os.stat_result,
    *,
    path: Path | str,
) -> None:
    if stat.S_ISLNK(entry_stat.st_mode) or _is_reparse_point(entry_stat):
        raise DocumentationWikiInputError(
            f"Workspace directory became a symlink or reparse point: {path}",
            category="workspace_redirection_rejected",
            path=str(path),
        )
    if not stat.S_ISDIR(entry_stat.st_mode):
        raise DocumentationWikiInputError(
            f"Workspace parent is no longer a directory: {path}",
            category="workspace_redirection_rejected",
            path=str(path),
        )


def _assert_safe_workspace_file(
    entry_stat: os.stat_result,
    *,
    path: Path | str,
) -> None:
    if (
        stat.S_ISLNK(entry_stat.st_mode)
        or _is_reparse_point(entry_stat)
        or not stat.S_ISREG(entry_stat.st_mode)
    ):
        raise DocumentationWikiInputError(
            f"Workspace destination is not a regular no-follow file: {path}",
            category="workspace_redirection_rejected",
            path=str(path),
        )


def _workspace_lstat(path: Path, *, operation: str) -> os.stat_result:
    try:
        return path.lstat()
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot inspect workspace path during {operation}: {path}: {exc}",
            category="workspace_redirection_rejected",
            path=str(path),
        ) from exc


def _canonical_path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def _assert_workspace_path_bounded(
    path: Path,
    workspace_root: Path,
    *,
    operation: str,
) -> None:
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(workspace_root)
    except (OSError, ValueError) as exc:
        raise DocumentationWikiInputError(
            f"Workspace path escaped its root during {operation}: {path}",
            category="workspace_redirection_rejected",
            path=str(path),
        ) from exc


def _inspect_workspace_root(workspace_root: Path) -> os.stat_result:
    inspected = _workspace_lstat(workspace_root, operation="root verification")
    _assert_safe_workspace_directory(inspected, path=workspace_root)
    try:
        resolved = workspace_root.resolve(strict=True)
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot resolve workspace root safely: {workspace_root}: {exc}",
            category="workspace_redirection_rejected",
            path=str(workspace_root),
        ) from exc
    if _canonical_path_key(resolved) != _canonical_path_key(workspace_root):
        raise DocumentationWikiInputError(
            f"Workspace root was redirected after validation: {workspace_root}",
            category="workspace_redirection_rejected",
            path=str(workspace_root),
        )
    return inspected


def _open_workspace_root_descriptor(
    workspace_root: Path,
) -> tuple[int | None, os.stat_result]:
    inspected = _inspect_workspace_root(workspace_root)
    if not _supports_secure_directory_fd_copy():
        return None, inspected

    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(workspace_root, flags)
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot safely open workspace root {workspace_root}: {exc}",
            category="workspace_redirection_rejected",
            path=str(workspace_root),
        ) from exc
    try:
        opened = os.fstat(descriptor)
        _assert_safe_workspace_directory(opened, path=workspace_root)
        _assert_same_workspace_identity(
            inspected,
            opened,
            path=workspace_root,
            operation="no-follow root open",
        )
        after = _inspect_workspace_root(workspace_root)
        _assert_same_workspace_identity(
            opened,
            after,
            path=workspace_root,
            operation="post-open root verification",
        )
    except Exception:
        os.close(descriptor)
        raise
    return descriptor, opened


def _copy_input_tree(input_tree: _InputTree, workspace_root: Path) -> None:
    _assert_input_tree_resource_bounds(input_tree)
    try:
        workspace_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot create workspace wiki directory {workspace_root}: {exc}",
            category="workspace_unwritable",
            path=str(workspace_root),
        ) from exc

    root_descriptor, root_identity = _open_workspace_root_descriptor(workspace_root)
    try:
        for entry in input_tree.files:
            try:
                _copy_regular_file(
                    entry,
                    workspace_root,
                    root_descriptor=root_descriptor,
                    root_identity=root_identity,
                )
            except DocumentationWikiInputError:
                raise
            except OSError as exc:
                raise DocumentationWikiInputError(
                    f"Cannot copy {entry.relative_path!r} into the workspace: {exc}",
                    category="workspace_unwritable",
                    path=entry.relative_path,
                ) from exc
    finally:
        if root_descriptor is not None:
            os.close(root_descriptor)


def _open_or_create_workspace_subdirectory(
    parent_descriptor: int,
    component: str,
    *,
    relative_path: PurePosixPath,
) -> int:
    try:
        os.mkdir(component, dir_fd=parent_descriptor)
    except FileExistsError:
        pass
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot create workspace directory {relative_path.as_posix()!r}: {exc}",
            category="workspace_redirection_rejected",
            path=relative_path.as_posix(),
        ) from exc

    try:
        inspected = os.stat(
            component,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot inspect workspace directory {relative_path.as_posix()!r}: {exc}",
            category="workspace_redirection_rejected",
            path=relative_path.as_posix(),
        ) from exc
    _assert_safe_workspace_directory(inspected, path=relative_path.as_posix())

    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(component, flags, dir_fd=parent_descriptor)
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot safely open workspace directory {relative_path.as_posix()!r}: {exc}",
            category="workspace_redirection_rejected",
            path=relative_path.as_posix(),
        ) from exc
    try:
        opened = os.fstat(descriptor)
        _assert_safe_workspace_directory(opened, path=relative_path.as_posix())
        _assert_same_workspace_identity(
            inspected,
            opened,
            path=relative_path.as_posix(),
            operation="no-follow directory open",
        )
        after = os.stat(
            component,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        _assert_safe_workspace_directory(after, path=relative_path.as_posix())
        _assert_same_workspace_identity(
            opened,
            after,
            path=relative_path.as_posix(),
            operation="post-open directory verification",
        )
    except Exception:
        os.close(descriptor)
        raise
    return descriptor


def _open_workspace_destination_at(
    relative: PurePosixPath,
    *,
    root_descriptor: int,
) -> tuple[int, int, os.stat_result]:
    parent_descriptor = os.dup(root_descriptor)
    destination_descriptor: int | None = None
    relative_parent = PurePosixPath(".")
    try:
        for component in relative.parent.parts:
            if component == ".":
                continue
            relative_parent /= component
            child_descriptor = _open_or_create_workspace_subdirectory(
                parent_descriptor,
                component,
                relative_path=relative_parent,
            )
            os.close(parent_descriptor)
            parent_descriptor = child_descriptor

        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        destination_descriptor = os.open(
            relative.name,
            flags,
            0o666,
            dir_fd=parent_descriptor,
        )
        opened = os.fstat(destination_descriptor)
        _assert_safe_workspace_file(opened, path=relative.as_posix())
        after = os.stat(
            relative.name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        _assert_safe_workspace_file(after, path=relative.as_posix())
        _assert_same_workspace_identity(
            opened,
            after,
            path=relative.as_posix(),
            operation="destination creation",
        )
    except Exception:
        if destination_descriptor is not None:
            os.close(destination_descriptor)
        os.close(parent_descriptor)
        raise
    if destination_descriptor is None:
        os.close(parent_descriptor)
        raise DocumentationWikiInputError(
            "Workspace destination descriptor was not created.",
            category="workspace_copy_failed",
            path=relative.as_posix(),
        )
    return destination_descriptor, parent_descriptor, opened


def _assert_workspace_fallback_chain(
    workspace_root: Path,
    relative_parent: PurePosixPath,
    *,
    root_identity: os.stat_result,
) -> tuple[Path, os.stat_result]:
    current = workspace_root
    current_identity = _inspect_workspace_root(workspace_root)
    _assert_same_workspace_identity(
        root_identity,
        current_identity,
        path=workspace_root,
        operation="fallback root verification",
    )
    for component in relative_parent.parts:
        if component == ".":
            continue
        parent_before = _workspace_lstat(
            current,
            operation="fallback parent verification",
        )
        _assert_safe_workspace_directory(parent_before, path=current)
        _assert_same_workspace_identity(
            current_identity,
            parent_before,
            path=current,
            operation="fallback parent verification",
        )
        child = current / component
        try:
            child.mkdir(exist_ok=True)
        except OSError as exc:
            raise DocumentationWikiInputError(
                f"Cannot create workspace directory {child}: {exc}",
                category="workspace_redirection_rejected",
                path=str(child),
            ) from exc
        child_identity = _workspace_lstat(
            child,
            operation="fallback child verification",
        )
        _assert_safe_workspace_directory(child_identity, path=child)
        _assert_workspace_path_bounded(
            child,
            workspace_root,
            operation="fallback child verification",
        )
        parent_after = _workspace_lstat(
            current,
            operation="fallback post-create parent verification",
        )
        _assert_same_workspace_identity(
            parent_before,
            parent_after,
            path=current,
            operation="fallback directory creation",
        )
        current = child
        current_identity = child_identity
    return current, current_identity


def _open_workspace_destination_fallback(
    relative: PurePosixPath,
    *,
    workspace_root: Path,
    root_identity: os.stat_result,
) -> tuple[int, Path, os.stat_result, os.stat_result]:
    parent, parent_identity = _assert_workspace_fallback_chain(
        workspace_root,
        relative.parent,
        root_identity=root_identity,
    )
    target = parent / relative.name
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(target, flags, 0o666)
    except OSError as exc:
        raise DocumentationWikiInputError(
            f"Cannot safely create workspace file {relative.as_posix()!r}: {exc}",
            category="workspace_redirection_rejected",
            path=relative.as_posix(),
        ) from exc
    try:
        opened = os.fstat(descriptor)
        _assert_safe_workspace_file(opened, path=relative.as_posix())
        inspected = _workspace_lstat(
            target,
            operation="fallback destination verification",
        )
        _assert_safe_workspace_file(inspected, path=relative.as_posix())
        _assert_same_workspace_identity(
            opened,
            inspected,
            path=relative.as_posix(),
            operation="fallback destination creation",
        )
        _assert_workspace_path_bounded(
            target,
            workspace_root,
            operation="fallback destination creation",
        )
        parent_after = _workspace_lstat(
            parent,
            operation="fallback post-open parent verification",
        )
        _assert_same_workspace_identity(
            parent_identity,
            parent_after,
            path=parent,
            operation="fallback destination open",
        )
    except Exception:
        os.close(descriptor)
        raise
    return descriptor, target, opened, parent_identity


def _copy_file_bytes(
    entry: _InputFile,
    destination_descriptor: int,
) -> tuple[str, os.stat_result]:
    _assert_input_files_resource_bounds((entry,))
    hasher = hashlib.sha256()
    copied_bytes = 0
    with os.fdopen(destination_descriptor, "wb") as destination:
        with _open_input_entry(entry) as source:
            while True:
                chunk = source.read(
                    min(
                        _INPUT_READ_CHUNK_BYTES,
                        entry.size - copied_bytes + 1,
                    )
                )
                if not chunk:
                    break
                copied_bytes += len(chunk)
                if copied_bytes > entry.size:
                    raise DocumentationWikiInputError(
                        f"Input wiki file grew while being copied: {entry.relative_path}",
                        category="input_changed_during_snapshot",
                        path=entry.relative_path,
                    )
                destination.write(chunk)
                hasher.update(chunk)
            if copied_bytes != entry.size:
                raise DocumentationWikiInputError(
                    "Input wiki file size changed while being copied: "
                    f"{entry.relative_path}",
                    category="input_changed_during_snapshot",
                    path=entry.relative_path,
                )
            destination.flush()
            copied_stat = os.fstat(destination.fileno())
    return "sha256:" + hasher.hexdigest(), copied_stat


def _copy_regular_file(
    entry: _InputFile,
    workspace_root: Path,
    *,
    root_descriptor: int | None,
    root_identity: os.stat_result,
) -> None:
    relative = PurePosixPath(entry.relative_path)
    if root_descriptor is not None:
        destination_descriptor, parent_descriptor, opened = (
            _open_workspace_destination_at(
                relative,
                root_descriptor=root_descriptor,
            )
        )
        try:
            copied_hash, copied_stat = _copy_file_bytes(
                entry,
                destination_descriptor,
            )
            after = os.stat(
                relative.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            _assert_safe_workspace_file(after, path=relative.as_posix())
            _assert_same_workspace_identity(
                opened,
                copied_stat,
                path=relative.as_posix(),
                operation="destination write",
            )
            _assert_same_workspace_identity(
                copied_stat,
                after,
                path=relative.as_posix(),
                operation="post-write destination verification",
            )
        finally:
            os.close(parent_descriptor)
    else:
        if not _uses_windows_guarded_copy_fallback():
            raise DocumentationWikiInputError(
                "This platform lacks descriptor-relative no-follow copy support "
                "and a qualified safe fallback.",
                category="secure_copy_unavailable",
                path=relative.as_posix(),
            )
        try:
            with guard_windows_directory_chain(
                workspace_root,
                relative.parent.parts,
                create_missing=True,
            ):
                destination_descriptor, target, opened, parent_identity = (
                    _open_workspace_destination_fallback(
                        relative,
                        workspace_root=workspace_root,
                        root_identity=root_identity,
                    )
                )
                copied_hash, copied_stat = _copy_file_bytes(
                    entry, destination_descriptor
                )
                after = _workspace_lstat(
                    target,
                    operation="fallback post-write destination verification",
                )
                _assert_safe_workspace_file(after, path=relative.as_posix())
                _assert_same_workspace_identity(
                    opened,
                    copied_stat,
                    path=relative.as_posix(),
                    operation="fallback destination write",
                )
                _assert_same_workspace_identity(
                    copied_stat,
                    after,
                    path=relative.as_posix(),
                    operation="fallback post-write destination verification",
                )
                parent_after = _workspace_lstat(
                    target.parent,
                    operation="fallback final parent verification",
                )
                _assert_same_workspace_identity(
                    parent_identity,
                    parent_after,
                    path=target.parent,
                    operation="fallback destination write",
                )
                _assert_workspace_path_bounded(
                    target,
                    workspace_root,
                    operation="fallback post-write verification",
                )
        except WindowsDirectoryGuardError as exc:
            raise DocumentationWikiInputError(
                f"Cannot pin the Windows workspace copy path: {exc}",
                category="workspace_redirection_rejected",
                path=relative.as_posix(),
            ) from exc

    root_after = _inspect_workspace_root(workspace_root)
    _assert_same_workspace_identity(
        root_identity,
        root_after,
        path=workspace_root,
        operation="post-copy root verification",
    )
    if copied_hash != entry.sha256:
        raise DocumentationWikiInputError(
            f"Input wiki file changed while being copied: {entry.relative_path}",
            category="input_changed_during_snapshot",
            path=entry.relative_path,
        )
