"""Deterministic bundle, snapshot, and producer envelope construction.

The pure builder in this module consumes already captured content digests,
inventory values, canonical Markdown text, exact surface-index bytes, effective
generation options, and producer metadata.  It never scans or reads the source
tree.  Local Git inspection is available as an explicit, separate collection
step whose result is inert input to the builder.
"""

from __future__ import annotations

import math
import os
import re
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from .contracts import GOVERNANCE_HASH_EXTENSION_KEY, KNOWLEDGE_SCHEMA_VERSION
from .knowledge_evidence import (
    canonical_json_bytes,
    formatted_json_text,
    is_valid_sha256,
    sha256_bytes,
)
from .knowledge_model import (
    EVALUATED_REVISION_PATTERN,
    LIMITATION_CODE_PATTERN,
    REPOSITORY_IDENTITY_PATTERN,
    REPOSITORY_IDENTITY_SOURCE_EXTENSION,
    BundleRecord,
    KnowledgeIndex,
    KnowledgeModelError,
    ProducerComponent,
    ProducerRecord,
    RepositoryIdentitySource,
    RepositoryRecord,
    SnapshotRecord,
    WorkingTreeState,
    knowledge_index_to_payload,
)
from .validation import require_repository_relative_path

EVALUATED_ENVELOPE_VERSION = "llm-wiki-evaluated-envelope/v1"
INVENTORY_HASH_EXTENSION = "llm-wiki/inventory-hash"

SOURCE_SNAPSHOT_DOMAIN = "llm-wiki/source-snapshot/v1"
INVENTORY_SNAPSHOT_DOMAIN = "llm-wiki/inventory-snapshot/v1"
MARKDOWN_SNAPSHOT_DOMAIN = "llm-wiki/markdown-snapshot/v1"
GENERATION_OPTIONS_DOMAIN = "llm-wiki/generation-options/v1"
COMPONENT_CONFIGURATION_DOMAIN = "llm-wiki/component-configuration/v1"
AGGREGATE_INPUT_DOMAIN = "llm-wiki/aggregate-input/v1"

CONFIGURATION_BASIS_UNKNOWN = "configuration-basis-unknown"
VERSION_UNKNOWN = "version-unknown"
UNKNOWN_COMPONENT_VERSION = "unknown"

_REPOSITORY_IDENTITY_RE = re.compile(REPOSITORY_IDENTITY_PATTERN)
_EVALUATED_REVISION_RE = re.compile(EVALUATED_REVISION_PATTERN)
_LIMITATION_CODE_RE = re.compile(LIMITATION_CODE_PATTERN)
_COMPONENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_INPUT_KIND_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_WINDOWS_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:")
_MALFORMED_PERCENT_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_SCP_REMOTE_RE = re.compile(
    r"^(?:(?P<userinfo>[^@/:\s]+)@)?"
    r"(?P<host>[A-Za-z0-9][A-Za-z0-9.-]*):(?P<path>.+)$"
)


@dataclass(frozen=True)
class _GitCommandResult:
    available: bool
    returncode: int | None
    output: str = ""

    @property
    def succeeded(self) -> bool:
        return self.available and self.returncode == 0


class KnowledgeEnvelopeError(ValueError):
    """Field-specific validation failure while constructing an envelope."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class ConsumedInputKind(str, Enum):
    """Known classes of repository/configuration input consumed by a run."""

    SOURCE = "source"
    DOCKER = "docker"
    COMPOSE = "compose"
    YAML = "yaml"
    PACKAGE = "package"
    OPENAPI = "openapi"
    PLUGIN = "plugin"
    SELECTION = "selection"


CONSUMED_INPUT_KIND_PRECEDENCE = (
    ConsumedInputKind.OPENAPI,
    ConsumedInputKind.COMPOSE,
    ConsumedInputKind.DOCKER,
    ConsumedInputKind.PACKAGE,
    ConsumedInputKind.PLUGIN,
    ConsumedInputKind.SELECTION,
    ConsumedInputKind.YAML,
    ConsumedInputKind.SOURCE,
)


@dataclass(frozen=True)
class ConsumedInput:
    """One already captured repository-relative content commitment."""

    path: str
    content_hash: str
    kind: ConsumedInputKind | str = ConsumedInputKind.SOURCE

    def __post_init__(self) -> None:
        _repository_relative_path(self.path, "source_inputs.path")
        if not is_valid_sha256(self.content_hash):
            raise KnowledgeEnvelopeError(
                "source_inputs.content_hash",
                "must be a canonical lowercase SHA-256 value",
            )
        kind = (
            self.kind.value if isinstance(self.kind, ConsumedInputKind) else self.kind
        )
        if not isinstance(kind, str) or _INPUT_KIND_RE.fullmatch(kind) is None:
            raise KnowledgeEnvelopeError(
                "source_inputs.kind",
                "must be a lowercase hyphen-separated machine code",
            )

    @classmethod
    def from_bytes(
        cls,
        path: str,
        content: bytes,
        *,
        kind: ConsumedInputKind | str = ConsumedInputKind.SOURCE,
    ) -> ConsumedInput:
        """Capture exact bytes without retaining them in the envelope input."""

        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")
        return cls(path=path, content_hash=sha256_bytes(content), kind=kind)

    @property
    def kind_value(self) -> str:
        return (
            self.kind.value if isinstance(self.kind, ConsumedInputKind) else self.kind
        )


def consumed_inputs_from_captured_hashes(
    content_hashes: Mapping[str, str],
    candidate_kinds: Mapping[
        str,
        ConsumedInputKind | str | Iterable[ConsumedInputKind | str],
    ],
) -> tuple[ConsumedInput, ...]:
    """Adapt already captured exact hashes into canonical consumed inputs.

    The function performs no I/O.  Multiple candidate classifications for an
    overlapping physical input are collapsed using
    :data:`CONSUMED_INPUT_KIND_PRECEDENCE`.
    """

    if not isinstance(content_hashes, Mapping):
        raise KnowledgeEnvelopeError("captured_content_hashes", "must be an object")
    if not isinstance(candidate_kinds, Mapping):
        raise KnowledgeEnvelopeError("captured_input_kinds", "must be an object")
    if any(not isinstance(path, str) for path in content_hashes):
        raise KnowledgeEnvelopeError(
            "captured_content_hashes",
            "must use string repository paths",
        )
    if any(not isinstance(path, str) for path in candidate_kinds):
        raise KnowledgeEnvelopeError(
            "captured_input_kinds",
            "must use string repository paths",
        )
    if set(content_hashes) != set(candidate_kinds):
        raise KnowledgeEnvelopeError(
            "captured_inputs",
            "content hashes and selected-kind candidates must cover identical paths",
        )
    for path in content_hashes:
        _repository_relative_path(path, "captured_inputs.path")

    return tuple(
        ConsumedInput(
            path=path,
            content_hash=content_hashes[path],
            kind=_canonical_consumed_input_kind(
                candidate_kinds[path],
                f"captured_input_kinds.{path}",
            ),
        )
        for path in sorted(content_hashes)
    )


@dataclass(frozen=True)
class ProducerComponentInput:
    """Safe, already selected producer metadata.

    ``configuration`` must be an application-owned allowlist of effective,
    non-secret, behavior-affecting values.  ``None`` explicitly means that the
    complete safe configuration basis was unavailable.
    """

    component_id: str
    version: str | None
    configuration: Mapping[str, Any] | None = None
    limitations: tuple[str, ...] = ()
    extensions: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositoryEvidence:
    """Already collected local VCS evidence; raw remotes are never serialized."""

    remotes: Mapping[str, str | None] = field(default_factory=dict)
    remotes_evaluated: bool = True
    upstream_remote: str | None = None
    upstream_remote_evaluated: bool = True
    evaluated_revision: str | None = None
    working_tree: WorkingTreeState = WorkingTreeState.UNKNOWN


@dataclass(frozen=True)
class EnvelopeInputs:
    """Complete in-memory inputs for one evaluated envelope."""

    repository: RepositoryRecord
    source_inputs: tuple[ConsumedInput, ...]
    inventory: Mapping[str, Any]
    markdown_pages: Mapping[str, str | bytes]
    surface_index_bytes: bytes
    generation_options: Mapping[str, Any]
    generation_option_defaults: Mapping[str, Any]
    generation_option_allowlist: tuple[str, ...]
    tool: ProducerComponentInput
    extractors: tuple[ProducerComponentInput, ...] = ()
    plugins: tuple[ProducerComponentInput, ...] = ()
    bundle_extensions: Mapping[str, Any] = field(default_factory=dict)
    snapshot_extensions: Mapping[str, Any] = field(default_factory=dict)
    producer_extensions: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluatedEnvelope:
    """Version-tagged evaluated basis committed by manifest v5 in KNOW-107."""

    bundle: BundleRecord
    schema_version: str = EVALUATED_ENVELOPE_VERSION

    @property
    def inventory_hash(self) -> str:
        value = self.bundle.snapshot.extensions.get(INVENTORY_HASH_EXTENSION)
        if not isinstance(value, str) or not is_valid_sha256(value):
            raise KnowledgeEnvelopeError(
                f"bundle.snapshot.extensions.{INVENTORY_HASH_EXTENSION}",
                "must contain the normalized inventory commitment",
            )
        return value

    def to_payload(self) -> dict[str, Any]:
        return evaluated_envelope_to_payload(self)

    def to_json(self) -> str:
        return serialize_evaluated_envelope(self)

    def content_hash(self) -> str:
        return hash_evaluated_envelope(self)


def collect_git_repository_evidence(
    root: str | Path,
    *,
    excluded_worktree_paths: Iterable[str | Path] = (),
) -> RepositoryEvidence:
    """Collect local-only Git evidence without scanning source content.

    Git commands never contact a remote.  Any unavailable or malformed command
    result is represented conservatively as unknown evidence.  Callers that
    generate self-describing repository artifacts may exclude those exact
    output paths from working-tree evaluation to avoid making the envelope
    depend recursively on its own persisted bytes.
    """

    checkout = Path(root)
    inside = _run_git(checkout, "rev-parse", "--is-inside-work-tree")
    if inside != "true":
        return RepositoryEvidence()

    raw_revision = _run_git(checkout, "rev-parse", "--verify", "HEAD")
    revision = raw_revision if _is_full_git_oid(raw_revision) else None

    status_pathspecs = _excluded_worktree_pathspecs(
        checkout,
        excluded_worktree_paths,
    )
    if status_pathspecs is None:
        status = None
    else:
        status = _run_git(
            checkout,
            "-c",
            "core.fsmonitor=false",
            "status",
            "--porcelain=v1",
            "--untracked-files=normal",
            "--ignored=no",
            *status_pathspecs,
            preserve_empty=True,
        )
    if status is None:
        working_tree = WorkingTreeState.UNKNOWN
    elif status:
        working_tree = WorkingTreeState.DIRTY
    else:
        working_tree = WorkingTreeState.CLEAN

    remote_config = _run_git_result(
        checkout,
        "config",
        "--local",
        "--no-includes",
        "--get-regexp",
        r"^remote\..*\.url$",
    )
    remotes, remotes_evaluated = _parse_local_remote_config(remote_config)

    branch_result = _run_git_result(
        checkout,
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
    )
    if branch_result.succeeded and branch_result.output:
        branch = branch_result.output
        remote_evaluated, branch_remotes = _local_config_values(
            checkout,
            f"branch.{branch}.remote",
        )
        merge_evaluated, branch_merges = _local_config_values(
            checkout,
            f"branch.{branch}.merge",
        )
        upstream_remote_evaluated = (
            remote_evaluated
            and merge_evaluated
            and len(branch_remotes) <= 1
            and len(branch_merges) <= 1
        )
        if (
            upstream_remote_evaluated
            and len(branch_remotes) == 1
            and len(branch_merges) == 1
        ):
            upstream_remote = branch_remotes[0]
        else:
            upstream_remote = None
    elif branch_result.available and branch_result.returncode == 1:
        upstream_remote = None
        upstream_remote_evaluated = True
    else:
        upstream_remote = None
        upstream_remote_evaluated = False
    return RepositoryEvidence(
        remotes=remotes,
        remotes_evaluated=remotes_evaluated,
        upstream_remote=upstream_remote,
        upstream_remote_evaluated=upstream_remote_evaluated,
        evaluated_revision=revision,
        working_tree=working_tree,
    )


def _excluded_worktree_pathspecs(
    checkout: Path,
    excluded_paths: Iterable[str | Path],
) -> tuple[str, ...] | None:
    """Return literal top-level Git exclusions, or ``None`` if unevaluable."""

    if isinstance(excluded_paths, (str, bytes)):
        raise TypeError("excluded_worktree_paths must be an iterable of paths")
    selected = tuple(excluded_paths)
    if not selected:
        return ()

    raw_top_level = _run_git(checkout, "rev-parse", "--show-toplevel")
    if raw_top_level is None:
        return None
    try:
        top_level = Path(raw_top_level).resolve()
        checkout_root = checkout.resolve()
    except OSError:
        return None

    normalized: set[str] = set()
    for index, raw_path in enumerate(selected):
        if not isinstance(raw_path, (str, Path)):
            raise TypeError(
                f"excluded_worktree_paths[{index}] must be a string or Path"
            )
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = checkout_root / candidate
        try:
            relative = candidate.resolve().relative_to(top_level).as_posix()
        except (OSError, ValueError):
            continue
        normalized.add(
            _repository_relative_path(
                relative,
                f"excluded_worktree_paths[{index}]",
            )
        )
    if not normalized:
        return ()
    return (
        "--",
        ":(top)**",
        *(f":(top,literal,exclude){path}" for path in sorted(normalized)),
    )


def build_repository_record(
    *,
    configured_public_identity: str | None = None,
    evidence: RepositoryEvidence | None = None,
) -> RepositoryRecord:
    """Apply configured/VCS/unknown identity precedence to collected evidence."""

    current = evidence or RepositoryEvidence()
    if not isinstance(current.remotes_evaluated, bool):
        raise KnowledgeEnvelopeError(
            "remotes_evaluated",
            "must be a boolean",
        )
    if not isinstance(current.upstream_remote_evaluated, bool):
        raise KnowledgeEnvelopeError(
            "upstream_remote_evaluated",
            "must be a boolean",
        )
    if configured_public_identity is None and not (
        current.remotes_evaluated and current.upstream_remote_evaluated
    ):
        identity, source = "unknown", RepositoryIdentitySource.UNKNOWN
    else:
        identity, source = select_repository_identity(
            configured_public_identity=configured_public_identity,
            vcs_remotes=current.remotes,
            upstream_remote=current.upstream_remote,
        )
    revision = _evaluated_revision(current.evaluated_revision)
    working_tree = _working_tree(current.working_tree)
    extensions: dict[str, Any] = {}
    if source is not RepositoryIdentitySource.UNKNOWN:
        extensions[REPOSITORY_IDENTITY_SOURCE_EXTENSION] = source.value
    return RepositoryRecord(
        identity=identity,
        evaluated_revision=revision,
        working_tree=working_tree,
        extensions=extensions,
    )


def select_repository_identity(
    *,
    configured_public_identity: str | None,
    vcs_remotes: Mapping[str, str | None],
    upstream_remote: str | None,
) -> tuple[str, RepositoryIdentitySource]:
    """Select one portable identity without persisting raw remote evidence."""

    if configured_public_identity is not None:
        configured_identity = validate_configured_public_identity(
            configured_public_identity
        )
        return configured_identity, RepositoryIdentitySource.CONFIGURED_PUBLIC

    remotes = _remote_mapping(vcs_remotes)
    if upstream_remote is not None:
        selected: str | None = upstream_remote
    elif "origin" in remotes:
        selected = "origin"
    elif len(remotes) == 1:
        selected = next(iter(remotes))
    else:
        selected = None
    if selected is None:
        return "unknown", RepositoryIdentitySource.UNKNOWN

    remote = remotes.get(selected)
    normalized_identity = (
        normalize_vcs_remote(remote) if isinstance(remote, str) else None
    )
    if normalized_identity is None:
        return "unknown", RepositoryIdentitySource.UNKNOWN
    return normalized_identity, RepositoryIdentitySource.NORMALIZED_VCS


def validate_configured_public_identity(value: object) -> str:
    """Validate one explicitly configured public repository identity."""

    if not isinstance(value, str) or value == "unknown":
        raise KnowledgeEnvelopeError(
            "configured_public_identity",
            "must be a qualified public namespace path",
        )
    if (
        value != value.strip()
        or _REPOSITORY_IDENTITY_RE.fullmatch(value) is None
        or value.casefold().endswith(".git")
    ):
        raise KnowledgeEnvelopeError(
            "configured_public_identity",
            "must be a normalized public namespace path without scheme, "
            "credentials, port, query, fragment, dot segment, or '.git' suffix",
        )
    return value


def normalize_vcs_remote(value: object) -> str | None:
    """Return a safe portable identity for one HTTPS/SSH/SCP remote."""

    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(char) < 0x20 for char in value)
        or "\\" in value
        or value.startswith(("/", "//"))
        or _WINDOWS_DRIVE_PREFIX_RE.match(value)
        or _MALFORMED_PERCENT_RE.search(value)
    ):
        return None

    if "://" in value:
        parsed_remote = _normalize_scheme_remote(value)
    else:
        parsed_remote = _normalize_scp_remote(value)
    if parsed_remote is None:
        return None
    host, raw_path = parsed_remote
    return _normalized_remote_identity(host, raw_path)


def hash_source_snapshot(inputs: Iterable[ConsumedInput]) -> str:
    """Hash the exact selected input set in canonical kind/path order."""

    records: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for index, item in enumerate(inputs):
        if not isinstance(item, ConsumedInput):
            raise KnowledgeEnvelopeError(
                f"source_inputs[{index}]",
                "must be a ConsumedInput",
            )
        if item.path in seen_paths:
            raise KnowledgeEnvelopeError(
                f"source_inputs[{index}]",
                f"duplicates consumed repository path {item.path}",
            )
        seen_paths.add(item.path)
        records.append(
            {
                "kind": item.kind_value,
                "path": item.path,
                "content_hash": item.content_hash,
            }
        )
    records.sort(key=lambda item: (item["kind"], item["path"]))
    return _hash_structured(
        SOURCE_SNAPSHOT_DOMAIN,
        {"inputs": records},
        "source_inputs",
    )


def hash_inventory(inventory: Mapping[str, Any]) -> str:
    """Hash the canonical normalized extracted inventory."""

    if not isinstance(inventory, Mapping):
        raise KnowledgeEnvelopeError("inventory", "must be an object")
    normalized: dict[str, Any] = {}
    for source_path, file_data in inventory.items():
        if not isinstance(source_path, str):
            raise KnowledgeEnvelopeError("inventory", "must use string source keys")
        normalized[_repository_relative_path(source_path, "inventory.source_path")] = (
            file_data
        )
    return _hash_structured(
        INVENTORY_SNAPSHOT_DOMAIN,
        {"inventory": normalized},
        "inventory",
    )


def hash_markdown_snapshot(pages: Mapping[str, str | bytes]) -> str:
    """Hash active canonical Markdown paths and LF-normalized UTF-8 content."""

    if not isinstance(pages, Mapping):
        raise KnowledgeEnvelopeError("markdown_pages", "must be an object")
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for path, content in pages.items():
        canonical_path = _repository_relative_path(path, "markdown_pages.path")
        if not canonical_path.endswith(".md"):
            raise KnowledgeEnvelopeError(
                f"markdown_pages.{canonical_path}",
                "must identify a canonical Markdown document",
            )
        if canonical_path in seen:
            raise KnowledgeEnvelopeError(
                f"markdown_pages.{canonical_path}",
                "duplicates a canonical Markdown path",
            )
        seen.add(canonical_path)
        normalized = _normalized_markdown_bytes(
            content,
            f"markdown_pages.{canonical_path}",
        )
        records.append(
            {
                "path": canonical_path,
                "content_hash": sha256_bytes(normalized),
            }
        )
    records.sort(key=lambda item: item["path"])
    return _hash_structured(
        MARKDOWN_SNAPSHOT_DOMAIN,
        {"pages": records},
        "markdown_pages",
    )


def hash_generation_options(
    values: Mapping[str, Any],
    *,
    defaults: Mapping[str, Any],
    allowlist: Iterable[str],
) -> str:
    """Hash effective allowlisted behavior options, including defaults."""

    if not isinstance(values, Mapping):
        raise KnowledgeEnvelopeError("generation_options", "must be an object")
    if not isinstance(defaults, Mapping):
        raise KnowledgeEnvelopeError(
            "generation_option_defaults",
            "must be an object",
        )
    allowed = _normalized_allowlist(allowlist)
    _reject_unknown_option_keys(values, allowed, "generation_options")
    _reject_unknown_option_keys(defaults, allowed, "generation_option_defaults")
    effective: dict[str, Any] = {}
    for key in allowed:
        if key in values:
            effective[key] = values[key]
        elif key in defaults:
            effective[key] = defaults[key]
        else:
            raise KnowledgeEnvelopeError(
                f"generation_options.{key}",
                "requires an explicit value or effective default",
            )
    _reject_machine_local_paths(effective, "generation_options")
    return _hash_structured(
        GENERATION_OPTIONS_DOMAIN,
        {"options": effective},
        "generation_options",
    )


def hash_component_configuration(configuration: Mapping[str, Any]) -> str:
    """Hash one complete safe component configuration allowlist."""

    if not isinstance(configuration, Mapping):
        raise KnowledgeEnvelopeError("configuration", "must be an object")
    _reject_machine_local_paths(configuration, "configuration")
    return _hash_structured(
        COMPONENT_CONFIGURATION_DOMAIN,
        {"configuration": configuration},
        "configuration",
    )


def hash_aggregate_inputs(inputs: Sequence[Any] | Iterable[Any]) -> str:
    """Hash ordered aggregate evidence while retaining order and multiplicity."""

    if isinstance(inputs, (str, bytes, Mapping, set, frozenset)):
        raise KnowledgeEnvelopeError(
            "aggregate_inputs",
            "must be an ordered iterable of contributor records",
        )
    try:
        records = list(inputs)
    except TypeError as exc:
        raise KnowledgeEnvelopeError(
            "aggregate_inputs",
            "must be an iterable of finite canonical JSON values",
        ) from exc
    return _hash_structured(
        AGGREGATE_INPUT_DOMAIN,
        {"inputs": records},
        "aggregate_inputs",
    )


def build_evaluated_envelope(inputs: EnvelopeInputs) -> EvaluatedEnvelope:
    """Build and typed-validate a complete envelope without performing I/O."""

    if not isinstance(inputs, EnvelopeInputs):
        raise TypeError("inputs must be an EnvelopeInputs")
    if not isinstance(inputs.repository, RepositoryRecord):
        raise KnowledgeEnvelopeError(
            "repository",
            "must be a pre-evaluated RepositoryRecord",
        )
    _extensions_copy(inputs.repository.extensions, "repository.extensions")
    if not isinstance(inputs.surface_index_bytes, bytes):
        raise KnowledgeEnvelopeError("surface_index_bytes", "must be bytes")

    source_snapshot_hash = hash_source_snapshot(inputs.source_inputs)
    inventory_hash = hash_inventory(inputs.inventory)
    _validate_inventory_source_parity(inputs.inventory, inputs.source_inputs)
    snapshot_extensions = _extensions_copy(
        inputs.snapshot_extensions,
        "snapshot_extensions",
    )
    existing_inventory_hash = snapshot_extensions.get(INVENTORY_HASH_EXTENSION)
    if (
        existing_inventory_hash is not None
        and existing_inventory_hash != inventory_hash
    ):
        raise KnowledgeEnvelopeError(
            f"snapshot_extensions.{INVENTORY_HASH_EXTENSION}",
            "conflicts with the computed normalized inventory hash",
        )
    snapshot_extensions[INVENTORY_HASH_EXTENSION] = inventory_hash

    snapshot = SnapshotRecord(
        source_snapshot_hash=source_snapshot_hash,
        markdown_snapshot_hash=hash_markdown_snapshot(inputs.markdown_pages),
        surface_index_hash=sha256_bytes(inputs.surface_index_bytes),
        generation_options_hash=hash_generation_options(
            inputs.generation_options,
            defaults=inputs.generation_option_defaults,
            allowlist=inputs.generation_option_allowlist,
        ),
        extensions=snapshot_extensions,
    )
    producer = build_producer_record(
        tool=inputs.tool,
        extractors=inputs.extractors,
        plugins=inputs.plugins,
        extensions=inputs.producer_extensions,
    )
    bundle = BundleRecord(
        repository=inputs.repository,
        snapshot=snapshot,
        producer=producer,
        extensions=_extensions_copy(inputs.bundle_extensions, "bundle_extensions"),
    )
    envelope = EvaluatedEnvelope(bundle=bundle)
    # Normalize and validate the manually constructed v1 bundle immediately.
    evaluated_envelope_to_payload(envelope)
    return envelope


def build_producer_record(
    *,
    tool: ProducerComponentInput,
    extractors: Iterable[ProducerComponentInput] = (),
    plugins: Iterable[ProducerComponentInput] = (),
    extensions: Mapping[str, Any] | None = None,
) -> ProducerRecord:
    """Build canonical producer evidence from safe selected metadata."""

    tool_record = _build_component(tool, "producer.tool", analyzer=False)
    extractor_records = tuple(
        sorted(
            (
                _build_component(item, f"producer.extractors[{index}]", analyzer=True)
                for index, item in enumerate(extractors)
            ),
            key=lambda component: component.component_id,
        )
    )
    plugin_records = tuple(
        sorted(
            (
                _build_component(item, f"producer.plugins[{index}]", analyzer=True)
                for index, item in enumerate(plugins)
            ),
            key=lambda component: component.component_id,
        )
    )
    producer = ProducerRecord(
        tool=tool_record,
        extractors=extractor_records,
        plugins=plugin_records,
        extensions=_extensions_copy(extensions or {}, "producer.extensions"),
    )
    ids = [
        producer.tool.component_id,
        *(component.component_id for component in producer.extractors),
        *(component.component_id for component in producer.plugins),
    ]
    if len(ids) != len(set(ids)):
        duplicate = next(item for item in ids if ids.count(item) > 1)
        raise KnowledgeEnvelopeError(
            "producer",
            f"duplicates producer component {duplicate!r}",
        )
    return producer


def plugin_producer_inputs(
    components: Iterable[Mapping[str, Any]],
    *,
    plugin_configurations: Mapping[str, Mapping[str, Any] | None] | None = None,
    plugin_limitations: Mapping[str, Iterable[str]] | None = None,
) -> tuple[ProducerComponentInput, ...]:
    """Project installed component records into safe per-plugin producer input.

    Absolute ``plugin_dir``, install source, timestamps, and raw lock records
    are deliberately ignored.  Only the stable behavior-bearing component
    allowlist below participates in the configuration commitment.
    """

    grouped: dict[str, dict[str, Any]] = {}
    for index, component in enumerate(components):
        if not isinstance(component, Mapping):
            raise KnowledgeEnvelopeError(
                f"plugin_components[{index}]",
                "must be an object",
            )
        plugin_id = component.get("plugin_id")
        if (
            not isinstance(plugin_id, str)
            or _COMPONENT_ID_RE.fullmatch(plugin_id) is None
        ):
            raise KnowledgeEnvelopeError(
                f"plugin_components[{index}].plugin_id",
                "must be a normalized stable plugin ID",
            )
        version = component.get("plugin_version")
        if version is not None and not isinstance(version, str):
            raise KnowledgeEnvelopeError(
                f"plugin_components[{index}].plugin_version",
                "must be a string when available",
            )
        if isinstance(version, str):
            if version != version.strip() or any(ord(char) < 0x20 for char in version):
                raise KnowledgeEnvelopeError(
                    f"plugin_components[{index}].plugin_version",
                    "must be a normalized string when available",
                )
            _reject_machine_local_paths(
                version,
                f"plugin_components[{index}].plugin_version",
            )
        entry = grouped.setdefault(
            plugin_id,
            {"versions": set(), "components": [], "coordinates": set()},
        )
        entry["versions"].add(version or None)
        safe_component = _safe_plugin_component_metadata(
            component,
            f"plugin_components[{index}]",
        )
        coordinate = (safe_component["type"], safe_component["id"])
        if coordinate in entry["coordinates"]:
            raise KnowledgeEnvelopeError(
                f"plugin_components[{index}].id",
                f"duplicates selected component {coordinate[0]}:{coordinate[1]}",
            )
        entry["coordinates"].add(coordinate)
        entry["components"].append(safe_component)

    configurations = _plugin_metadata_mapping(
        plugin_configurations,
        "plugin_configurations",
    )
    limitations = _plugin_metadata_mapping(
        plugin_limitations,
        "plugin_limitations",
    )
    for field_name, metadata in (
        ("plugin_configurations", configurations),
        ("plugin_limitations", limitations),
    ):
        unknown = set(metadata) - set(grouped)
        if unknown:
            plugin_id = min(unknown)
            raise KnowledgeEnvelopeError(
                f"{field_name}.{plugin_id}",
                "does not identify a selected plugin",
            )
    results: list[ProducerComponentInput] = []
    for plugin_id in sorted(grouped):
        entry = grouped[plugin_id]
        versions = entry["versions"]
        if len(versions) > 1:
            raise KnowledgeEnvelopeError(
                f"plugin_components.{plugin_id}.version",
                "contains conflicting plugin versions",
            )
        version = next(iter(versions)) if versions else None
        component_metadata = sorted(
            entry["components"],
            key=lambda item: (item.get("type", ""), item.get("id", "")),
        )
        supplied_configuration = configurations.get(plugin_id)
        if supplied_configuration is not None and not isinstance(
            supplied_configuration,
            Mapping,
        ):
            raise KnowledgeEnvelopeError(
                f"plugin_configurations.{plugin_id}",
                "must be an object or unavailable",
            )
        configuration = (
            None
            if supplied_configuration is None
            else {
                "components": component_metadata,
                "settings": supplied_configuration,
            }
        )
        raw_limitations = limitations.get(plugin_id, ())
        if isinstance(raw_limitations, (str, bytes)):
            raise KnowledgeEnvelopeError(
                f"plugin_limitations.{plugin_id}",
                "must be an iterable of machine codes, not scalar text or bytes",
            )
        try:
            selected_limitations = tuple(raw_limitations)
        except TypeError as exc:
            raise KnowledgeEnvelopeError(
                f"plugin_limitations.{plugin_id}",
                "must be an iterable of machine codes",
            ) from exc
        results.append(
            ProducerComponentInput(
                component_id=plugin_id,
                version=version,
                configuration=configuration,
                limitations=selected_limitations,
            )
        )
    return tuple(results)


def evaluated_envelope_to_payload(envelope: EvaluatedEnvelope) -> dict[str, Any]:
    """Return a deterministic JSON-compatible evaluated-envelope payload."""

    if not isinstance(envelope, EvaluatedEnvelope):
        raise TypeError("envelope must be an EvaluatedEnvelope")
    if envelope.schema_version != EVALUATED_ENVELOPE_VERSION:
        raise KnowledgeEnvelopeError(
            "schema_version",
            f"must be {EVALUATED_ENVELOPE_VERSION!r}",
        )
    bundle_payload = _validated_bundle_payload(envelope.bundle)
    inventory_hash = (
        bundle_payload["snapshot"].get("extensions", {}).get(INVENTORY_HASH_EXTENSION)
    )
    if not is_valid_sha256(inventory_hash):
        raise KnowledgeEnvelopeError(
            f"bundle.snapshot.extensions.{INVENTORY_HASH_EXTENSION}",
            "must contain a canonical normalized inventory hash",
        )
    return {
        "schema_version": envelope.schema_version,
        "bundle": bundle_payload,
    }


def serialize_evaluated_envelope(envelope: EvaluatedEnvelope) -> str:
    """Serialize with sorted keys, UTF-8 semantics, LF, and one final newline."""

    try:
        return formatted_json_text(evaluated_envelope_to_payload(envelope))
    except KnowledgeEnvelopeError:
        raise
    except (RecursionError, TypeError, UnicodeEncodeError, ValueError) as exc:
        raise KnowledgeEnvelopeError(
            "envelope",
            "cannot be serialized as finite JSON",
        ) from exc


def hash_evaluated_envelope(envelope: EvaluatedEnvelope) -> str:
    """Hash the exact canonical evaluated-envelope bytes."""

    return sha256_bytes(serialize_evaluated_envelope(envelope).encode("utf-8"))


def _run_git(
    root: Path,
    *args: str,
    preserve_empty: bool = False,
) -> str | None:
    result = _run_git_result(root, *args)
    if not result.succeeded:
        return None
    if result.output or preserve_empty:
        return result.output
    return None


def _run_git_result(root: Path, *args: str) -> _GitCommandResult:
    git_environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    git_environment["LC_ALL"] = "C"
    git_environment["GIT_CONFIG_GLOBAL"] = os.devnull
    git_environment["GIT_CONFIG_NOSYSTEM"] = "1"
    git_environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=git_environment,
            timeout=15,
            check=False,
        )
    except (
        FileNotFoundError,
        OSError,
        subprocess.TimeoutExpired,
        UnicodeError,
    ):
        return _GitCommandResult(available=False, returncode=None)
    output = result.stdout.strip()
    return _GitCommandResult(
        available=True,
        returncode=result.returncode,
        output=output,
    )


def _parse_local_remote_config(
    result: _GitCommandResult,
) -> tuple[dict[str, str | None], bool]:
    if not result.available:
        return {}, False
    if result.returncode == 1:
        return {}, True
    if not result.succeeded:
        return {}, False

    values_by_remote: dict[str, list[str]] = {}
    for line in result.output.splitlines():
        key, separator, value = line.partition(" ")
        if not separator or not key.startswith("remote.") or not key.endswith(".url"):
            return {}, False
        remote_name = key[len("remote.") : -len(".url")]
        if not remote_name:
            return {}, False
        values_by_remote.setdefault(remote_name, []).append(value)
    return (
        {
            remote_name: values[0] if len(values) == 1 else None
            for remote_name, values in sorted(values_by_remote.items())
        },
        True,
    )


def _local_config_values(root: Path, key: str) -> tuple[bool, tuple[str, ...]]:
    result = _run_git_result(
        root,
        "config",
        "--local",
        "--no-includes",
        "--get-all",
        key,
    )
    if not result.available:
        return False, ()
    if result.returncode == 1:
        return True, ()
    if not result.succeeded:
        return False, ()
    values = tuple(line for line in result.output.splitlines() if line)
    return True, values


def _is_full_git_oid(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) in {40, 64}
        and all(char in "0123456789abcdef" for char in value)
    )


def _evaluated_revision(value: str | None) -> str:
    if value is None:
        return "unknown"
    if not isinstance(value, str):
        raise KnowledgeEnvelopeError(
            "evaluated_revision",
            "must be a complete lowercase 40- or 64-hex Git object ID",
        )
    candidate = value if value.startswith("git:") else f"git:{value}"
    if _EVALUATED_REVISION_RE.fullmatch(candidate) is None:
        raise KnowledgeEnvelopeError(
            "evaluated_revision",
            "must be a complete lowercase 40- or 64-hex Git object ID",
        )
    return candidate


def _working_tree(value: object) -> WorkingTreeState:
    if isinstance(value, WorkingTreeState):
        return value
    try:
        return WorkingTreeState(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise KnowledgeEnvelopeError(
            "working_tree",
            "must be 'unknown', 'clean', or 'dirty'",
        ) from exc


def _remote_mapping(value: Mapping[str, str | None]) -> dict[str, str | None]:
    if not isinstance(value, Mapping):
        raise KnowledgeEnvelopeError("vcs_remotes", "must be an object")
    result: dict[str, str | None] = {}
    for name, remote in value.items():
        if not isinstance(name, str) or not name:
            raise KnowledgeEnvelopeError(
                "vcs_remotes",
                "must use non-empty string remote names",
            )
        if remote is not None and not isinstance(remote, str):
            raise KnowledgeEnvelopeError(
                f"vcs_remotes.{name}",
                "must be a string or unavailable",
            )
        result[name] = remote
    return result


def _normalize_scheme_remote(value: str) -> tuple[str, str] | None:
    try:
        parsed = urlsplit(value)
        port = parsed.port
        host = parsed.hostname
    except ValueError:
        return None
    scheme = parsed.scheme.casefold()
    if scheme not in {"https", "ssh"} or not host:
        return None
    authority = parsed.netloc.rsplit("@", 1)[-1]
    if authority.endswith(":"):
        return None
    default_port = 443 if scheme == "https" else 22
    if port is not None and port != default_port:
        return None
    if not parsed.path:
        return None
    return host.casefold(), parsed.path


def _normalize_scp_remote(value: str) -> tuple[str, str] | None:
    match = _SCP_REMOTE_RE.fullmatch(value)
    if match is None:
        return None
    path = match.group("path").split("#", 1)[0].split("?", 1)[0]
    if not path:
        return None
    return match.group("host").casefold(), path


def _normalized_remote_identity(host: str, raw_path: str) -> str | None:
    try:
        decoded_path = unquote(raw_path)
    except (UnicodeDecodeError, ValueError):
        return None
    if "\\" in decoded_path:
        return None
    path = decoded_path.removeprefix("/")
    path = path.removesuffix("/")
    if path.casefold().endswith(".git"):
        path = path[:-4]
    parts = path.split("/")
    if not path or any(part in {"", ".", ".."} for part in parts):
        return None
    identity = f"{host}/{'/'.join(parts)}"
    if _REPOSITORY_IDENTITY_RE.fullmatch(
        identity
    ) is None or identity.casefold().endswith(".git"):
        return None
    return identity


def _repository_relative_path(value: object, field_name: str) -> str:
    return require_repository_relative_path(
        value,
        text_error=KnowledgeEnvelopeError(
            field_name, "must be a non-empty repository-relative path"
        ),
        posix_error=KnowledgeEnvelopeError(
            field_name, "must be a repository-relative POSIX path"
        ),
        normalized_error=KnowledgeEnvelopeError(
            field_name, "must be a normalized repository-relative path"
        ),
    )


def _canonical_consumed_input_kind(
    value: ConsumedInputKind | str | Iterable[ConsumedInputKind | str],
    field_name: str,
) -> ConsumedInputKind | str:
    if isinstance(value, (ConsumedInputKind, str)):
        candidates: tuple[ConsumedInputKind | str, ...] = (value,)
    else:
        if isinstance(value, bytes):
            raise KnowledgeEnvelopeError(
                field_name,
                "must contain one or more input-kind codes",
            )
        try:
            candidates = tuple(value)
        except TypeError as exc:
            raise KnowledgeEnvelopeError(
                field_name,
                "must contain one or more input-kind codes",
            ) from exc
    if not candidates:
        raise KnowledgeEnvelopeError(
            field_name,
            "must contain one or more input-kind codes",
        )

    normalized: set[str] = set()
    for candidate in candidates:
        kind = (
            candidate.value if isinstance(candidate, ConsumedInputKind) else candidate
        )
        if not isinstance(kind, str) or _INPUT_KIND_RE.fullmatch(kind) is None:
            raise KnowledgeEnvelopeError(
                field_name,
                "must contain lowercase hyphen-separated input-kind codes",
            )
        normalized.add(kind)

    rank = {
        kind.value: index for index, kind in enumerate(CONSUMED_INPUT_KIND_PRECEDENCE)
    }
    selected = min(
        normalized,
        key=lambda kind: (rank.get(kind, len(rank)), kind),
    )
    try:
        return ConsumedInputKind(selected)
    except ValueError:
        return selected


def _validate_inventory_source_parity(
    inventory: Mapping[str, Any],
    source_inputs: Iterable[ConsumedInput],
) -> None:
    consumed_paths = {item.path for item in source_inputs}
    if not set(inventory).issubset(consumed_paths):
        raise KnowledgeEnvelopeError(
            "inventory.source_path",
            "must identify a path committed by source_inputs",
        )


def _normalized_markdown_bytes(value: str | bytes, field_name: str) -> bytes:
    if isinstance(value, bytes):
        try:
            text = value.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise KnowledgeEnvelopeError(
                field_name,
                "must be valid UTF-8 Markdown",
            ) from exc
    elif isinstance(value, str):
        text = value
    else:
        raise KnowledgeEnvelopeError(
            field_name,
            "must be UTF-8 text or bytes",
        )
    try:
        return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    except UnicodeEncodeError as exc:
        raise KnowledgeEnvelopeError(
            field_name,
            "must be valid UTF-8 Markdown",
        ) from exc


def _hash_structured(domain: str, payload: Mapping[str, Any], field_name: str) -> str:
    try:
        for value in payload.values():
            _validate_json_tree(value, field_name)
        return sha256_bytes(
            canonical_json_bytes(
                {
                    "domain": domain,
                    **payload,
                }
            )
        )
    except KnowledgeEnvelopeError:
        raise
    except (RecursionError, TypeError, UnicodeEncodeError, ValueError) as exc:
        raise KnowledgeEnvelopeError(
            field_name,
            "must contain finite canonical JSON values with string object keys",
        ) from exc


def _validate_json_tree(value: object, field_name: str) -> None:
    """Reject non-JSON, non-finite, non-string-keyed, and cyclic values."""

    active: set[int] = set()

    def walk(item: object, path: str) -> None:
        if item is None or isinstance(item, (str, bool, int)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise KnowledgeEnvelopeError(path, "must be finite")
            return
        if isinstance(item, Mapping):
            identity = id(item)
            if identity in active:
                raise KnowledgeEnvelopeError(path, "must not be cyclic")
            active.add(identity)
            try:
                for key, child in item.items():
                    if not isinstance(key, str):
                        raise KnowledgeEnvelopeError(
                            path,
                            "must use string object keys",
                        )
                    walk(child, f"{path}.{key}")
            finally:
                active.remove(identity)
            return
        if isinstance(item, (list, tuple)):
            identity = id(item)
            if identity in active:
                raise KnowledgeEnvelopeError(path, "must not be cyclic")
            active.add(identity)
            try:
                for index, child in enumerate(item):
                    walk(child, f"{path}[{index}]")
            finally:
                active.remove(identity)
            return
        raise KnowledgeEnvelopeError(
            path,
            "must contain only canonical JSON values",
        )

    walk(value, field_name)


def _normalized_allowlist(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise KnowledgeEnvelopeError(
            "generation_option_allowlist",
            "must be an iterable of option names, not scalar text or bytes",
        )
    try:
        items = tuple(value)
    except TypeError as exc:
        raise KnowledgeEnvelopeError(
            "generation_option_allowlist",
            "must be an iterable of option names",
        ) from exc
    if any(not isinstance(item, str) or not item for item in items):
        raise KnowledgeEnvelopeError(
            "generation_option_allowlist",
            "must contain non-empty string option names",
        )
    if len(items) != len(set(items)):
        raise KnowledgeEnvelopeError(
            "generation_option_allowlist",
            "must not contain duplicate option names",
        )
    return tuple(sorted(items))


def _reject_unknown_option_keys(
    value: Mapping[str, Any],
    allowlist: tuple[str, ...],
    field_name: str,
) -> None:
    if any(not isinstance(key, str) for key in value):
        raise KnowledgeEnvelopeError(field_name, "must use string option names")
    unknown = set(value) - set(allowlist)
    if unknown:
        key = min(unknown)
        raise KnowledgeEnvelopeError(
            f"{field_name}.{key}",
            "is not in the application-owned behavior option allowlist",
        )


def _reject_machine_local_paths(value: object, field_name: str) -> None:
    active: set[int] = set()

    def walk(item: object, path: str) -> None:
        if isinstance(item, str):
            if _is_machine_local_path_string(item):
                raise KnowledgeEnvelopeError(
                    path,
                    "must not contain a machine-local absolute path",
                )
            return
        if item is None or isinstance(item, (bool, int, float)):
            return
        if isinstance(item, Mapping):
            identity = id(item)
            if identity in active:
                raise KnowledgeEnvelopeError(path, "must not be cyclic")
            active.add(identity)
            try:
                for key, child in item.items():
                    if not isinstance(key, str):
                        raise KnowledgeEnvelopeError(
                            path,
                            "must use string object keys",
                        )
                    if _is_machine_local_path_string(key):
                        raise KnowledgeEnvelopeError(
                            path,
                            "must not use a machine-local absolute path as a key",
                        )
                    walk(child, f"{path}.{key}")
            finally:
                active.remove(identity)
            return
        if isinstance(item, (list, tuple)):
            identity = id(item)
            if identity in active:
                raise KnowledgeEnvelopeError(path, "must not be cyclic")
            active.add(identity)
            try:
                for index, child in enumerate(item):
                    walk(child, f"{path}[{index}]")
            finally:
                active.remove(identity)

    walk(value, field_name)


def _is_machine_local_path_string(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return bool(
        normalized.startswith("/")
        or _WINDOWS_DRIVE_PREFIX_RE.match(normalized)
        or normalized.lstrip().casefold().startswith("file:")
    )


def _extensions_copy(value: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeEnvelopeError(field_name, "must be an object")
    if any(not isinstance(key, str) for key in value):
        raise KnowledgeEnvelopeError(field_name, "must use string extension keys")
    _reject_machine_local_paths(value, field_name)
    return dict(value)


def _build_component(
    value: ProducerComponentInput,
    field_name: str,
    *,
    analyzer: bool,
) -> ProducerComponent:
    if not isinstance(value, ProducerComponentInput):
        raise KnowledgeEnvelopeError(
            field_name,
            "must be a ProducerComponentInput",
        )
    if (
        not isinstance(value.component_id, str)
        or _COMPONENT_ID_RE.fullmatch(value.component_id) is None
    ):
        raise KnowledgeEnvelopeError(
            f"{field_name}.id",
            "must be a normalized producer component ID",
        )
    limitations = set(_validated_limitations(value.limitations, field_name))
    if value.version is None or value.version == UNKNOWN_COMPONENT_VERSION:
        version = UNKNOWN_COMPONENT_VERSION
        limitations.add(VERSION_UNKNOWN)
    elif (
        not isinstance(value.version, str)
        or not value.version
        or value.version.strip() != value.version
        or any(ord(char) < 0x20 for char in value.version)
    ):
        raise KnowledgeEnvelopeError(
            f"{field_name}.version",
            "must be a normalized non-empty string or unavailable",
        )
    else:
        version = value.version
        _reject_machine_local_paths(version, f"{field_name}.version")
        if VERSION_UNKNOWN in limitations:
            raise KnowledgeEnvelopeError(
                f"{field_name}.limitations",
                f"must omit {VERSION_UNKNOWN!r} when version is known",
            )

    configuration_hash: str | None
    if value.configuration is None:
        configuration_hash = None
        if analyzer:
            limitations.add(CONFIGURATION_BASIS_UNKNOWN)
    else:
        if CONFIGURATION_BASIS_UNKNOWN in limitations:
            raise KnowledgeEnvelopeError(
                f"{field_name}.limitations",
                f"must omit {CONFIGURATION_BASIS_UNKNOWN!r} when configuration "
                "is complete",
            )
        configuration_hash = hash_component_configuration(value.configuration)

    return ProducerComponent(
        component_id=value.component_id,
        version=version,
        configuration_hash=configuration_hash,
        limitations=tuple(sorted(limitations)),
        extensions=_extensions_copy(value.extensions, f"{field_name}.extensions"),
    )


def _validated_limitations(
    value: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise KnowledgeEnvelopeError(
            f"{field_name}.limitations",
            "must be an iterable of machine codes, not scalar text or bytes",
        )
    try:
        limitations = tuple(value)
    except TypeError as exc:
        raise KnowledgeEnvelopeError(
            f"{field_name}.limitations",
            "must be an iterable of machine codes",
        ) from exc
    for index, limitation in enumerate(limitations):
        if (
            not isinstance(limitation, str)
            or _LIMITATION_CODE_RE.fullmatch(limitation) is None
        ):
            raise KnowledgeEnvelopeError(
                f"{field_name}.limitations[{index}]",
                "must be a lowercase stable machine code",
            )
    return limitations


def _safe_plugin_component_metadata(
    component: Mapping[str, Any],
    field_name: str,
) -> dict[str, Any]:
    component_type = component.get("type")
    component_id = component.get("id")
    if not isinstance(component_type, str) or not component_type:
        raise KnowledgeEnvelopeError(
            f"{field_name}.type",
            "must be a stable non-empty component type",
        )
    if (
        not isinstance(component_id, str)
        or _COMPONENT_ID_RE.fullmatch(component_id) is None
    ):
        raise KnowledgeEnvelopeError(
            f"{field_name}.id",
            "must be a normalized stable component ID",
        )
    safe_fields = (
        "type",
        "id",
        "language",
        "entry_point",
        "parallel_safe",
        "path",
        "ref",
    )
    result: dict[str, Any] = {}
    for key in safe_fields:
        if key not in component:
            continue
        field_value = component[key]
        if key == "parallel_safe":
            if not isinstance(field_value, bool):
                raise KnowledgeEnvelopeError(
                    f"{field_name}.{key}",
                    "must be a boolean",
                )
        elif not isinstance(field_value, str) or not field_value:
            raise KnowledgeEnvelopeError(
                f"{field_name}.{key}",
                "must be a non-empty string",
            )
        result[key] = field_value
    _reject_machine_local_paths(result, field_name)
    return result


def _plugin_metadata_mapping(
    value: Mapping[str, Any] | None,
    field_name: str,
) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise KnowledgeEnvelopeError(field_name, "must be an object")
    if any(not isinstance(key, str) or not key for key in value):
        raise KnowledgeEnvelopeError(
            field_name,
            "must use non-empty plugin ID keys",
        )
    return value


def _validated_bundle_payload(bundle: BundleRecord) -> dict[str, Any]:
    # Governance is a separate, non-rebuildable commit input rather than an
    # evaluated source-envelope input.  The knowledge snapshot and manifest
    # commit it directly.  Excluding it here also avoids constructing a
    # deliberately incomplete governance projection merely to validate a
    # standalone bundle.
    snapshot_extensions = dict(bundle.snapshot.extensions)
    snapshot_extensions.pop(GOVERNANCE_HASH_EXTENSION_KEY, None)
    envelope_bundle = replace(
        bundle,
        snapshot=replace(
            bundle.snapshot,
            extensions=snapshot_extensions,
        ),
    )
    try:
        payload = knowledge_index_to_payload(
            KnowledgeIndex(
                schema_version=KNOWLEDGE_SCHEMA_VERSION,
                bundle=envelope_bundle,
                concepts=(),
                relationships=(),
            )
        )
    except KnowledgeModelError as exc:
        raise KnowledgeEnvelopeError(
            "bundle",
            f"does not satisfy the knowledge v1 bundle contract: {exc}",
        ) from exc
    return payload["bundle"]


__all__ = [
    "AGGREGATE_INPUT_DOMAIN",
    "COMPONENT_CONFIGURATION_DOMAIN",
    "CONFIGURATION_BASIS_UNKNOWN",
    "CONSUMED_INPUT_KIND_PRECEDENCE",
    "EVALUATED_ENVELOPE_VERSION",
    "GENERATION_OPTIONS_DOMAIN",
    "INVENTORY_HASH_EXTENSION",
    "INVENTORY_SNAPSHOT_DOMAIN",
    "MARKDOWN_SNAPSHOT_DOMAIN",
    "SOURCE_SNAPSHOT_DOMAIN",
    "UNKNOWN_COMPONENT_VERSION",
    "VERSION_UNKNOWN",
    "ConsumedInput",
    "ConsumedInputKind",
    "EnvelopeInputs",
    "EvaluatedEnvelope",
    "KnowledgeEnvelopeError",
    "ProducerComponentInput",
    "RepositoryEvidence",
    "build_evaluated_envelope",
    "build_producer_record",
    "build_repository_record",
    "collect_git_repository_evidence",
    "consumed_inputs_from_captured_hashes",
    "evaluated_envelope_to_payload",
    "hash_aggregate_inputs",
    "hash_component_configuration",
    "hash_evaluated_envelope",
    "hash_generation_options",
    "hash_inventory",
    "hash_markdown_snapshot",
    "hash_source_snapshot",
    "normalize_vcs_remote",
    "plugin_producer_inputs",
    "select_repository_identity",
    "serialize_evaluated_envelope",
    "validate_configured_public_identity",
]
