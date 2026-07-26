"""Service-level persistence boundary for the sync manifest v5 contract."""

from __future__ import annotations

import json
import posixpath
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from ..extractors.common import LANGUAGE_EXTENSIONS, inventory_language_for_path
from .io import write_json_atomic
from .knowledge_evidence import (
    ENTITY_OBSERVATION_SCOPE,
    MODULE_OBSERVATION_SCOPE,
    ConceptObservationBasis,
    formatted_json_text,
    hash_file,
    is_valid_sha256,
    semantic_hash_for_file,
)

MANIFEST_FILENAME = ".llm-wiki-manifest.json"
MANIFEST_VERSION = 5
LEGACY_MANIFEST_VERSION = 4

EVIDENCE_NOT_RECORDED = "evidence-not-recorded"
LEGACY_EVIDENCE_UNAVAILABLE = "legacy-manifest-no-evidence"
MANIFEST_STATE_UNAVAILABLE = "manifest-state-unavailable"
MANIFEST_REPAIR_UNAVAILABLE = "manifest-repair-unavailable"
SOURCE_MAPPING_CHANGED = "source-mapping-changed"
PRODUCER_BASIS_INCOMPATIBLE = "producer-basis-incompatible"

TOMBSTONE_SOURCE_MISSING = "source-missing"
TOMBSTONE_UNKNOWN_PROVENANCE = "unknown-provenance"

_UNSAFE_PAGE_ID_CHARS_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_WINDOWS_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:")
_REASON_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_CONCEPT_PAGE_RE = re.compile(r"^(modules|entities)/([^/]+)\.md$")


class SyncManifestError(ValueError):
    """Field-specific validation failure for decoded manifest state."""

    def __init__(self, field: str, message: str, *, code: str | None = None):
        self.field = field
        self.message = message
        self.code = code
        super().__init__(f"{field}: {message}")


def _validate_reason(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _REASON_RE.fullmatch(value) is None:
        raise SyncManifestError(
            field_name,
            "must be a lowercase hyphen-separated machine reason",
        )
    return value


def _validate_repository_path(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise SyncManifestError(
            field_name, "must be a non-empty repository-relative path"
        )
    if (
        value != value.strip()
        or any(ord(char) < 0x20 for char in value)
        or value.startswith("/")
        or _WINDOWS_DRIVE_PREFIX_RE.match(value)
        or "\\" in value
    ):
        raise SyncManifestError(field_name, "must be a repository-relative POSIX path")
    parts = value.split("/")
    if (
        any(part in {"", ".", ".."} for part in parts)
        or posixpath.normpath(value) != value
    ):
        raise SyncManifestError(
            field_name, "must be a normalized repository-relative path"
        )
    return value


def _validate_concept_page_path(value: object, field_name: str) -> str:
    path = _validate_repository_path(value, field_name)
    match = _CONCEPT_PAGE_RE.fullmatch(path)
    if match is None or match.group(2) in {".", ".."}:
        raise SyncManifestError(
            field_name,
            "must be a canonical modules/<page>.md or entities/<page>.md path",
        )
    return path


def _validate_exact_keys(
    value: Mapping[str, object],
    *,
    field_name: str,
    required: set[str],
    optional: Iterable[str] = (),
) -> None:
    missing = required - set(value)
    if missing:
        name = min(missing)
        raise SyncManifestError(f"{field_name}.{name}", "is required")
    unknown = set(value) - required - set(optional)
    if unknown:
        name = min(unknown)
        raise SyncManifestError(f"{field_name}.{name}", "is not supported")


def _mapping_value(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise SyncManifestError(field_name, "must be an object")
    if any(not isinstance(key, str) for key in value):
        raise SyncManifestError(field_name, "must use string keys")
    return value


@dataclass(frozen=True)
class ManifestPageSource:
    """Last observed source coordinate for one module or entity page."""

    scope: str
    source_path: str
    entity_name: str | None = None
    occurrence: int | None = None

    def __post_init__(self) -> None:
        if self.scope not in {
            MODULE_OBSERVATION_SCOPE,
            ENTITY_OBSERVATION_SCOPE,
        }:
            raise SyncManifestError(
                "page_source_mappings.scope",
                "must be 'module' or 'entity'",
            )
        _validate_repository_path(self.source_path, "page_source_mappings.source_path")
        if self.scope == MODULE_OBSERVATION_SCOPE:
            if self.entity_name is not None or self.occurrence is not None:
                raise SyncManifestError(
                    "page_source_mappings",
                    "module mappings cannot carry entity coordinates",
                )
            return
        if not isinstance(self.entity_name, str) or not self.entity_name:
            raise SyncManifestError(
                "page_source_mappings.entity_name",
                "must be a non-empty string for entity mappings",
            )
        if (
            isinstance(self.occurrence, bool)
            or not isinstance(self.occurrence, int)
            or self.occurrence < 1
        ):
            raise SyncManifestError(
                "page_source_mappings.occurrence",
                "must be a positive integer for entity mappings",
            )

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "scope": self.scope,
            "source_path": self.source_path,
        }
        if self.scope == ENTITY_OBSERVATION_SCOPE:
            payload["entity_name"] = self.entity_name
            payload["occurrence"] = self.occurrence
        return payload

    @classmethod
    def from_payload(cls, value: object, field_name: str) -> ManifestPageSource:
        data = _mapping_value(value, field_name)
        _validate_exact_keys(
            data,
            field_name=field_name,
            required={"scope", "source_path"},
            optional={"entity_name", "occurrence"},
        )
        try:
            return cls(
                scope=data["scope"],  # type: ignore[arg-type]
                source_path=data["source_path"],  # type: ignore[arg-type]
                entity_name=data.get("entity_name"),  # type: ignore[arg-type]
                occurrence=data.get("occurrence"),  # type: ignore[arg-type]
            )
        except SyncManifestError as exc:
            suffix = exc.field.split(".")[-1]
            raise SyncManifestError(f"{field_name}.{suffix}", exc.message) from exc


def _basis_from_payload(
    value: object,
    field_name: str,
    *,
    unknown_reason: str | None,
) -> ConceptObservationBasis:
    data = _mapping_value(value, field_name)
    _validate_exact_keys(
        data,
        field_name=field_name,
        required={
            "scope",
            "source_path",
            "extractor_ref",
            "source_content_hash",
        },
        optional={"concept_observation_hash"},
    )
    try:
        return ConceptObservationBasis(
            scope=data["scope"],  # type: ignore[arg-type]
            source_path=data["source_path"],  # type: ignore[arg-type]
            extractor_ref=data["extractor_ref"],  # type: ignore[arg-type]
            source_content_hash=data["source_content_hash"],  # type: ignore[arg-type]
            concept_observation_hash=data.get(  # type: ignore[arg-type]
                "concept_observation_hash"
            ),
            unknown_reason=unknown_reason,
        )
    except (TypeError, ValueError) as exc:
        raise SyncManifestError(field_name, str(exc)) from exc


@dataclass(frozen=True)
class ManifestEvidenceBaseline:
    """Known or explicitly unknown evidence for one active concept page."""

    basis: ConceptObservationBasis | None = None
    unknown_reason: str | None = None

    def __post_init__(self) -> None:
        if self.basis is not None and self.basis.is_known:
            if self.unknown_reason is not None:
                raise SyncManifestError(
                    "evidence_baselines.unknown_reason",
                    "must be absent for a known basis",
                )
            return
        reason = _validate_reason(
            self.unknown_reason, "evidence_baselines.unknown_reason"
        )
        if (
            self.basis is not None
            and self.basis.unknown_reason is not None
            and self.basis.unknown_reason != reason
        ):
            raise SyncManifestError(
                "evidence_baselines.unknown_reason",
                "must match the partial basis unknown reason",
            )

    @property
    def is_known(self) -> bool:
        return self.basis is not None and self.basis.is_known

    @classmethod
    def from_basis(cls, basis: ConceptObservationBasis) -> ManifestEvidenceBaseline:
        return cls(
            basis=basis,
            unknown_reason=None if basis.is_known else basis.unknown_reason,
        )

    @classmethod
    def unknown(
        cls,
        reason: str,
        *,
        basis: ConceptObservationBasis | None = None,
    ) -> ManifestEvidenceBaseline:
        return cls(basis=basis, unknown_reason=reason)

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {"state": "known" if self.is_known else "unknown"}
        if self.basis is not None:
            payload["basis"] = self.basis.to_evidence_payload()
        if not self.is_known:
            payload["unknown_reason"] = self.unknown_reason
        return payload

    @classmethod
    def from_payload(cls, value: object, field_name: str) -> ManifestEvidenceBaseline:
        data = _mapping_value(value, field_name)
        _validate_exact_keys(
            data,
            field_name=field_name,
            required={"state"},
            optional={"basis", "unknown_reason"},
        )
        state = data["state"]
        if state == "known":
            if "basis" not in data:
                raise SyncManifestError(f"{field_name}.basis", "is required")
            if "unknown_reason" in data:
                raise SyncManifestError(
                    f"{field_name}.unknown_reason",
                    "must be absent for a known basis",
                )
            known_basis = _basis_from_payload(
                data["basis"], f"{field_name}.basis", unknown_reason=None
            )
            if not known_basis.is_known:
                raise SyncManifestError(
                    f"{field_name}.basis.concept_observation_hash",
                    "is required for a known basis",
                )
            return cls(basis=known_basis)
        if state != "unknown":
            raise SyncManifestError(
                f"{field_name}.state", "must be 'known' or 'unknown'"
            )
        reason = _validate_reason(
            data.get("unknown_reason"), f"{field_name}.unknown_reason"
        )
        basis: ConceptObservationBasis | None = None
        if "basis" in data:
            basis = _basis_from_payload(
                data["basis"],
                f"{field_name}.basis",
                unknown_reason=reason,
            )
            if basis.is_known:
                raise SyncManifestError(
                    f"{field_name}.basis.concept_observation_hash",
                    "must be absent for unknown evidence",
                )
        return cls(basis=basis, unknown_reason=reason)


@dataclass(frozen=True)
class ManifestTombstone:
    """Evidence retained for a stale module/entity page."""

    reason: str
    last_valid_basis: ConceptObservationBasis | None = None
    unknown_reason: str | None = None

    def __post_init__(self) -> None:
        if self.reason == TOMBSTONE_SOURCE_MISSING:
            if self.last_valid_basis is None or not self.last_valid_basis.is_known:
                raise SyncManifestError(
                    "tombstones.last_valid_basis",
                    "a source-missing tombstone requires a known basis",
                )
            if self.unknown_reason is not None:
                raise SyncManifestError(
                    "tombstones.unknown_reason",
                    "must be absent when a last valid basis is present",
                )
            return
        if self.reason != TOMBSTONE_UNKNOWN_PROVENANCE:
            raise SyncManifestError(
                "tombstones.reason",
                "must be 'source-missing' or 'unknown-provenance'",
            )
        if self.last_valid_basis is not None:
            raise SyncManifestError(
                "tombstones.last_valid_basis",
                "must be absent for unknown provenance",
            )
        _validate_reason(self.unknown_reason, "tombstones.unknown_reason")

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {"reason": self.reason}
        if self.last_valid_basis is not None:
            payload["last_valid_basis"] = self.last_valid_basis.to_evidence_payload()
        else:
            payload["unknown_reason"] = self.unknown_reason
        return payload

    @classmethod
    def from_payload(cls, value: object, field_name: str) -> ManifestTombstone:
        data = _mapping_value(value, field_name)
        _validate_exact_keys(
            data,
            field_name=field_name,
            required={"reason"},
            optional={"last_valid_basis", "unknown_reason"},
        )
        reason = data["reason"]
        if reason == TOMBSTONE_SOURCE_MISSING:
            if "last_valid_basis" not in data:
                raise SyncManifestError(f"{field_name}.last_valid_basis", "is required")
            if "unknown_reason" in data:
                raise SyncManifestError(
                    f"{field_name}.unknown_reason",
                    "must be absent for source-missing",
                )
            basis = _basis_from_payload(
                data["last_valid_basis"],
                f"{field_name}.last_valid_basis",
                unknown_reason=None,
            )
            if not basis.is_known:
                raise SyncManifestError(
                    f"{field_name}.last_valid_basis.concept_observation_hash",
                    "is required",
                )
            return cls(reason=TOMBSTONE_SOURCE_MISSING, last_valid_basis=basis)
        if reason == TOMBSTONE_UNKNOWN_PROVENANCE:
            if "last_valid_basis" in data:
                raise SyncManifestError(
                    f"{field_name}.last_valid_basis",
                    "must be absent for unknown provenance",
                )
            unknown_reason = _validate_reason(
                data.get("unknown_reason"), f"{field_name}.unknown_reason"
            )
            return cls(
                reason=TOMBSTONE_UNKNOWN_PROVENANCE,
                unknown_reason=unknown_reason,
            )
        raise SyncManifestError(
            f"{field_name}.reason",
            "must be 'source-missing' or 'unknown-provenance'",
        )


@dataclass(frozen=True)
class ManifestArtifactHashes:
    """All-or-none exact-byte commitment to the generated artifact set."""

    surface_index_hash: str
    knowledge_index_hash: str
    evaluated_envelope_hash: str

    def __post_init__(self) -> None:
        for name, value in (
            ("surface_index_hash", self.surface_index_hash),
            ("knowledge_index_hash", self.knowledge_index_hash),
            ("evaluated_envelope_hash", self.evaluated_envelope_hash),
        ):
            if not is_valid_sha256(value):
                raise SyncManifestError(
                    f"artifact_hashes.{name}",
                    "must be 'sha256:' followed by 64 lowercase hexadecimal digits",
                )

    def to_payload(self) -> dict[str, str]:
        return {
            "surface_index_hash": self.surface_index_hash,
            "knowledge_index_hash": self.knowledge_index_hash,
            "evaluated_envelope_hash": self.evaluated_envelope_hash,
        }

    @classmethod
    def from_payload(
        cls, value: object, field_name: str = "artifact_hashes"
    ) -> ManifestArtifactHashes:
        data = _mapping_value(value, field_name)
        required = {
            "surface_index_hash",
            "knowledge_index_hash",
            "evaluated_envelope_hash",
        }
        _validate_exact_keys(data, field_name=field_name, required=required)
        try:
            return cls(
                surface_index_hash=data["surface_index_hash"],  # type: ignore[arg-type]
                knowledge_index_hash=data["knowledge_index_hash"],  # type: ignore[arg-type]
                evaluated_envelope_hash=data["evaluated_envelope_hash"],  # type: ignore[arg-type]
            )
        except SyncManifestError as exc:
            suffix = exc.field.split(".")[-1]
            raise SyncManifestError(f"{field_name}.{suffix}", exc.message) from exc


def _infer_language_from_path(filepath: str) -> str | None:
    suffix = Path(filepath).suffix
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if suffix in extensions:
            return inventory_language_for_path(language, filepath)
    return None


def _first_doc_line(info: Mapping[str, Any]) -> str:
    docstring = info.get("docstring", "")
    return docstring.split("\n")[0] if docstring else "—"


def _safe_page_component(value: object, *, fallback: str = "page") -> str:
    raw = str(value).strip() if value not in (None, "") else ""
    safe = _UNSAFE_PAGE_ID_CHARS_RE.sub("_", raw).strip("_")
    safe = re.sub(r"_+", "_", safe).lstrip(".")
    return safe or fallback


def _page_name_with_extension(filepath: str) -> str:
    path = Path(filepath)
    base = path.with_suffix("").as_posix()
    base = base.replace("/", "_").replace("\\", "_").replace(".", "_")
    extension = path.suffix.lower().lstrip(".") or "file"
    return f"{base}_{extension.replace('.', '_')}"


def _page_name_from_source_path(filepath: str) -> str:
    path = Path(filepath)
    base = path.with_suffix("").as_posix()
    base = base.replace("/", "_").replace("\\", "_").replace(".", "_")
    return _safe_page_component(base, fallback=path.stem)


def _disambiguate_module_paths(filepaths: list[str], stem: str) -> dict[str, str]:
    max_depth = max(len(Path(filepath).parts) for filepath in filepaths)
    for depth in range(1, max_depth):
        candidates: dict[str, str] = {}
        for filepath in filepaths:
            directory_parts = Path(filepath).parts[:-1]
            prefix_parts = (
                directory_parts[-depth:]
                if len(directory_parts) >= depth
                else directory_parts
            )
            candidates[filepath] = "_".join(prefix_parts) + "_" + stem
        if len(set(candidates.values())) == len(filepaths):
            return candidates

    candidates = {
        filepath: _page_name_with_extension(filepath) for filepath in filepaths
    }
    if len(set(candidates.values())) == len(filepaths):
        return candidates

    seen: defaultdict[str, int] = defaultdict(int)
    unique: dict[str, str] = {}
    for filepath in sorted(filepaths):
        name = candidates[filepath]
        seen[name] += 1
        unique[filepath] = name if seen[name] == 1 else f"{name}_{seen[name]}"
    return unique


def _build_module_page_map(
    inventory: Mapping[str, Mapping[str, Any]],
) -> dict[str, str]:
    stem_groups: defaultdict[str, list[str]] = defaultdict(list)
    for filepath in inventory:
        stem_groups[Path(filepath).stem].append(filepath)

    page_map: dict[str, str] = {}
    for stem, filepaths in stem_groups.items():
        if len(filepaths) == 1:
            page_map[filepaths[0]] = stem
        else:
            page_map.update(_disambiguate_module_paths(filepaths, stem))

    page_counts = Counter(page_map.values())
    colliding_pages = {page for page, count in page_counts.items() if count > 1}
    if not colliding_pages:
        return page_map

    resolved = dict(page_map)
    used = {page for filepath, page in page_map.items() if page not in colliding_pages}
    for filepath in sorted(page_map):
        if page_map[filepath] not in colliding_pages:
            continue
        base = _page_name_from_source_path(filepath)
        candidates = [base, _page_name_with_extension(filepath)]
        candidate = next((item for item in candidates if item not in used), base)
        suffix = 2
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        resolved[filepath] = candidate
        used.add(candidate)
    return resolved


def _build_entity_occurrence_page_map(
    inventory: Mapping[str, Mapping[str, Any]],
    module_page_map: Mapping[str, str],
) -> dict[tuple[str, str, int], str]:
    """Preserve the legacy occurrence-map fallback without command imports."""

    occurrences: list[tuple[tuple[str, str, int], Mapping[str, Any]]] = []
    for filepath, file_data in inventory.items():
        seen_names: defaultdict[str, int] = defaultdict(int)
        for cls_info in file_data.get("classes", []):
            name = cls_info.get("name")
            if not name:
                continue
            name_text = str(name)
            seen_names[name_text] += 1
            occurrences.append(((name_text, filepath, seen_names[name_text]), cls_info))

    name_counts = Counter(key[0] for key, _ in occurrences)
    files_by_name: defaultdict[str, set[str]] = defaultdict(set)
    for (name, filepath, _occurrence), _ in occurrences:
        files_by_name[name].add(filepath)

    effective_module_page_map = dict(
        module_page_map or _build_module_page_map(inventory)
    )
    proposed_pages: list[tuple[tuple[str, str, int], str, str]] = []
    for key, _ in occurrences:
        name, filepath, occurrence = key
        safe_name = _safe_page_component(name, fallback="entity")
        if name_counts[name] > 1 and len(files_by_name[name]) > 1:
            page_name = _safe_page_component(
                f"{effective_module_page_map[filepath]}_{safe_name}"
            )
        else:
            page_name = safe_name
        if occurrence > 1:
            page_name = _safe_page_component(f"{page_name}_{occurrence}")
        proposed_pages.append((key, page_name, effective_module_page_map[filepath]))

    page_counts = Counter(page for _, page, _ in proposed_pages)
    used: set[str] = set()
    page_map: dict[tuple[str, str, int], str] = {}
    for key, page_name, module_page in proposed_pages:
        candidate = page_name
        if page_counts[page_name] > 1:
            candidate = _safe_page_component(f"{module_page}_{page_name}")
        suffix = 2
        while candidate in used:
            candidate = f"{page_name}_{suffix}"
            suffix += 1
        page_map[key] = candidate
        used.add(candidate)
    return page_map


def generated_semantics_for_file(
    filepath: str, file_data: Mapping[str, Any]
) -> dict[str, Any]:
    """Return generated description fields retained by current sync behavior."""

    module_docstring = file_data.get("module_docstring", "")
    module_description = module_docstring or f"_Auto-generated from `{filepath}`._"
    return {
        "module": {
            "description": module_description,
            "classes": {
                cls["name"]: _first_doc_line(cls)
                for cls in file_data.get("classes", [])
            },
            "functions": {
                fn["name"]: _first_doc_line(fn) for fn in file_data.get("functions", [])
            },
        },
        "entities": {
            cls["name"]: {
                "description": cls.get("docstring", "")
                or f"_Auto-generated from `{cls['name']}` in `{filepath}`._",
                "attributes": {
                    attr["name"]: attr.get("description") or "—"
                    for attr in cls.get("attributes", [])
                },
                "methods": {
                    method["name"]: _first_doc_line(method)
                    for method in cls.get("methods", [])
                },
            }
            for cls in file_data.get("classes", [])
        },
    }


def retained_concept_page_paths(wiki_dir: Path) -> tuple[str, ...]:
    """Return retained module/entity Markdown paths without reading page text."""

    paths: list[str] = []
    for directory in ("modules", "entities"):
        root = wiki_dir / directory
        if not root.is_dir():
            continue
        paths.extend(
            f"{directory}/{path.name}" for path in root.glob("*.md") if path.is_file()
        )
    return tuple(sorted(paths))


def _page_path(scope: str, page_name: object, field_name: str) -> str:
    if not isinstance(page_name, str) or not page_name:
        raise SyncManifestError(field_name, "must be a non-empty page name")
    directory = "modules" if scope == MODULE_OBSERVATION_SCOPE else "entities"
    return _validate_concept_page_path(
        f"{directory}/{page_name}.md",
        field_name,
    )


def _put_page_mapping(
    mappings: dict[str, ManifestPageSource],
    page_path: str,
    mapping: ManifestPageSource,
) -> None:
    existing = mappings.get(page_path)
    if existing is not None and existing != mapping:
        raise SyncManifestError(
            f"page_source_mappings.{page_path}",
            "collides with another source coordinate",
        )
    mappings[page_path] = mapping


def _legacy_operational_state(
    sources: Mapping[str, Mapping[str, Any]],
) -> tuple[
    dict[str, ManifestPageSource],
    dict[str, ManifestEvidenceBaseline],
]:
    mappings: dict[str, ManifestPageSource] = {}
    ambiguous_paths: set[str] = set()

    def put_unambiguous(
        page_path: str,
        mapping: ManifestPageSource,
    ) -> None:
        if page_path in ambiguous_paths:
            return
        existing = mappings.get(page_path)
        if existing is not None and existing != mapping:
            mappings.pop(page_path)
            ambiguous_paths.add(page_path)
            return
        mappings[page_path] = mapping

    for filepath, info in sources.items():
        try:
            source_path = _validate_repository_path(filepath, f"sources.{filepath}")
        except SyncManifestError:
            continue

        module_page = info.get("module_page")
        if isinstance(module_page, str) and module_page:
            try:
                module_path = _page_path(
                    MODULE_OBSERVATION_SCOPE,
                    module_page,
                    f"sources.{filepath}.module_page",
                )
                put_unambiguous(
                    module_path,
                    ManifestPageSource(
                        scope=MODULE_OBSERVATION_SCOPE,
                        source_path=source_path,
                    ),
                )
            except SyncManifestError:
                pass

        occurrences = info.get("entity_page_occurrences")
        if isinstance(occurrences, list):
            for index, item in enumerate(occurrences):
                if not isinstance(item, Mapping):
                    continue
                name = item.get("name")
                page_name = item.get("page")
                occurrence = item.get("occurrence")
                if (
                    not isinstance(name, str)
                    or not name
                    or not isinstance(page_name, str)
                    or not page_name
                    or isinstance(occurrence, bool)
                    or not isinstance(occurrence, int)
                    or occurrence < 1
                ):
                    continue
                try:
                    entity_path = _page_path(
                        ENTITY_OBSERVATION_SCOPE,
                        page_name,
                        (f"sources.{filepath}.entity_page_occurrences[{index}].page"),
                    )
                    put_unambiguous(
                        entity_path,
                        ManifestPageSource(
                            scope=ENTITY_OBSERVATION_SCOPE,
                            source_path=source_path,
                            entity_name=name,
                            occurrence=occurrence,
                        ),
                    )
                except SyncManifestError:
                    continue
            continue

        entities = info.get("entities")
        entity_pages = info.get("entity_pages")
        if not isinstance(entities, list) or not isinstance(entity_pages, Mapping):
            continue
        seen_names: dict[str, int] = {}
        for name_value in entities:
            if not isinstance(name_value, str) or not name_value:
                continue
            seen_names[name_value] = seen_names.get(name_value, 0) + 1
            occurrence = seen_names[name_value]
            page_name = entity_pages.get(name_value)
            # Older manifests collapsed duplicate names. Only the first
            # occurrence has an unambiguous recoverable page coordinate.
            if occurrence != 1 or not isinstance(page_name, str) or not page_name:
                continue
            try:
                entity_path = _page_path(
                    ENTITY_OBSERVATION_SCOPE,
                    page_name,
                    f"sources.{filepath}.entity_pages.{name_value}",
                )
                put_unambiguous(
                    entity_path,
                    ManifestPageSource(
                        scope=ENTITY_OBSERVATION_SCOPE,
                        source_path=source_path,
                        entity_name=name_value,
                        occurrence=occurrence,
                    ),
                )
            except SyncManifestError:
                continue

    baselines = {
        page_path: ManifestEvidenceBaseline.unknown(LEGACY_EVIDENCE_UNAVAILABLE)
        for page_path in mappings
    }
    return mappings, baselines


def _copy_sources(value: object, field_name: str) -> dict[str, dict]:
    data = _mapping_value(value, field_name)
    sources: dict[str, dict] = {}
    for filepath, raw_info in data.items():
        if not isinstance(raw_info, Mapping):
            raise SyncManifestError(f"{field_name}.{filepath}", "must be an object")
        info = deepcopy(dict(raw_info))
        if "language" not in info:
            info["language"] = _infer_language_from_path(filepath)
        sources[filepath] = info
    return sources


def _copy_mapping(value: object, field_name: str) -> dict[str, object]:
    data = _mapping_value(value, field_name)
    return deepcopy(dict(data))


def _captured_source_hashes(
    inventory: Mapping[str, object],
    value: Mapping[str, str] | None,
) -> dict[str, str] | None:
    """Validate an optional exact-hash replacement for source file reads."""

    inventory_paths = tuple(
        _validate_repository_path(
            path,
            "page_source_mappings.source_path",
        )
        for path in inventory
    )
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise SyncManifestError("source_content_hashes", "must be an object")
    if any(not isinstance(path, str) for path in value):
        raise SyncManifestError(
            "source_content_hashes",
            "must use string repository paths",
        )
    actual_paths = {
        _validate_repository_path(path, f"source_content_hashes.{path}")
        for path in value
    }
    expected_paths = set(inventory_paths)
    if actual_paths != expected_paths:
        missing = expected_paths - actual_paths
        if missing:
            path = min(missing)
            raise SyncManifestError(
                f"source_content_hashes.{path}",
                "is required for every inventory source",
            )
        path = min(actual_paths - expected_paths)
        raise SyncManifestError(
            f"source_content_hashes.{path}",
            "does not identify an inventory source",
        )

    captured: dict[str, str] = {}
    for path in sorted(actual_paths):
        content_hash = value[path]
        if not is_valid_sha256(content_hash):
            raise SyncManifestError(
                f"source_content_hashes.{path}",
                "must be a canonical lowercase SHA-256 value",
            )
        captured[path] = content_hash
    return captured


@dataclass
class SyncManifest:
    """Persistent v5 operational state used to generate the wiki."""

    sources: dict[str, dict] = field(default_factory=dict)
    surfaces: dict[str, dict] = field(default_factory=dict)
    generation_inputs: dict[str, object] = field(default_factory=dict)
    page_source_mappings: dict[str, ManifestPageSource] = field(default_factory=dict)
    evidence_baselines: dict[str, ManifestEvidenceBaseline] = field(
        default_factory=dict
    )
    tombstones: dict[str, ManifestTombstone] = field(default_factory=dict)
    artifact_hashes: ManifestArtifactHashes | None = None

    @classmethod
    def from_payload(cls, value: object) -> SyncManifest:
        """Validate and migrate one decoded manifest payload."""

        data = _mapping_value(value, "manifest")
        version = data.get("version")
        if isinstance(version, bool) or not isinstance(version, int):
            raise SyncManifestError("version", "must be an integer")
        if version < 1:
            raise SyncManifestError("version", "must be positive")
        if version > MANIFEST_VERSION:
            raise SyncManifestError(
                "version",
                f"unsupported future manifest version {version}",
                code="unsupported-version",
            )

        sources = _copy_sources(data.get("sources", {}), "sources")
        if version <= LEGACY_MANIFEST_VERSION:
            raw_surfaces = data.get("surfaces", {})
            raw_generation_inputs = data.get("generation_inputs", {})
            if not isinstance(raw_surfaces, Mapping):
                if version == LEGACY_MANIFEST_VERSION:
                    raise SyncManifestError("surfaces", "must be an object")
                raw_surfaces = {}
            if not isinstance(raw_generation_inputs, Mapping):
                if version == LEGACY_MANIFEST_VERSION:
                    raise SyncManifestError("generation_inputs", "must be an object")
                raw_generation_inputs = {}
            legacy_surfaces: dict[str, dict] = {}
            for key, raw_surface in raw_surfaces.items():
                if not isinstance(key, str):
                    raise SyncManifestError("surfaces", "must use string keys")
                if not isinstance(raw_surface, Mapping):
                    raise SyncManifestError(
                        f"surfaces.{key}",
                        "must be an object",
                    )
                legacy_surfaces[key] = deepcopy(dict(raw_surface))
            generation_inputs = deepcopy(dict(raw_generation_inputs))
            page_source_mappings, evidence_baselines = _legacy_operational_state(
                sources
            )
            manifest = cls(
                sources=sources,
                surfaces=legacy_surfaces,
                generation_inputs=generation_inputs,
                page_source_mappings=page_source_mappings,
                evidence_baselines=evidence_baselines,
            )
            manifest._validate_operational_state()
            return manifest

        for filepath in sources:
            _validate_repository_path(filepath, f"sources.{filepath}")
        _validate_exact_keys(
            data,
            field_name="manifest",
            required={
                "version",
                "sources",
                "surfaces",
                "generation_inputs",
                "page_source_mappings",
                "evidence_baselines",
                "tombstones",
            },
            optional={"artifact_hashes"},
        )
        surfaces_raw = _copy_mapping(data["surfaces"], "surfaces")
        generation_inputs = _copy_mapping(
            data["generation_inputs"], "generation_inputs"
        )
        surfaces: dict[str, dict] = {}
        for key, raw_surface in surfaces_raw.items():
            if not isinstance(raw_surface, Mapping):
                raise SyncManifestError(f"surfaces.{key}", "must be an object")
            surfaces[key] = deepcopy(dict(raw_surface))

        mappings_raw = _mapping_value(
            data["page_source_mappings"], "page_source_mappings"
        )
        page_source_mappings = {
            _validate_concept_page_path(
                page_path, f"page_source_mappings.{page_path}"
            ): ManifestPageSource.from_payload(
                raw_mapping, f"page_source_mappings.{page_path}"
            )
            for page_path, raw_mapping in mappings_raw.items()
        }
        baselines_raw = _mapping_value(data["evidence_baselines"], "evidence_baselines")
        evidence_baselines = {
            _validate_concept_page_path(
                page_path, f"evidence_baselines.{page_path}"
            ): ManifestEvidenceBaseline.from_payload(
                raw_baseline, f"evidence_baselines.{page_path}"
            )
            for page_path, raw_baseline in baselines_raw.items()
        }
        tombstones_raw = _mapping_value(data["tombstones"], "tombstones")
        tombstones = {
            _validate_concept_page_path(
                page_path, f"tombstones.{page_path}"
            ): ManifestTombstone.from_payload(raw_tombstone, f"tombstones.{page_path}")
            for page_path, raw_tombstone in tombstones_raw.items()
        }
        artifact_hashes = (
            ManifestArtifactHashes.from_payload(data["artifact_hashes"])
            if "artifact_hashes" in data
            else None
        )
        manifest = cls(
            sources=sources,
            surfaces=surfaces,
            generation_inputs=generation_inputs,
            page_source_mappings=page_source_mappings,
            evidence_baselines=evidence_baselines,
            tombstones=tombstones,
            artifact_hashes=artifact_hashes,
        )
        manifest._validate_operational_state()
        return manifest

    @classmethod
    def load(cls, wiki_dir: Path) -> SyncManifest:
        """Load a manifest; raise ``FileNotFoundError`` when it is absent."""

        manifest_path = wiki_dir / MANIFEST_FILENAME
        if not manifest_path.exists():
            raise FileNotFoundError(manifest_path)

        def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, item in pairs:
                if key in result:
                    raise SyncManifestError(
                        "manifest",
                        f"contains duplicate JSON key {key!r}",
                    )
                result[key] = item
            return result

        def reject_constant(value: str) -> None:
            raise SyncManifestError(
                "manifest",
                f"contains non-finite JSON number {value!r}",
            )

        data = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
        return cls.from_payload(data)

    def _validate_operational_state(self) -> None:
        for filepath in self.sources:
            _validate_repository_path(filepath, f"sources.{filepath}")

        mapping_paths = set(self.page_source_mappings)
        baseline_paths = set(self.evidence_baselines)
        tombstone_paths = set(self.tombstones)
        overlap = baseline_paths & tombstone_paths
        if overlap:
            page_path = min(overlap)
            raise SyncManifestError(
                f"evidence_baselines.{page_path}",
                "cannot also be a tombstone",
            )
        missing_state = mapping_paths - baseline_paths - tombstone_paths
        if missing_state:
            page_path = min(missing_state)
            raise SyncManifestError(
                f"page_source_mappings.{page_path}",
                "requires an evidence baseline or tombstone",
            )

        for page_path, mapping in self.page_source_mappings.items():
            _validate_concept_page_path(page_path, f"page_source_mappings.{page_path}")
            if not isinstance(mapping, ManifestPageSource):
                raise SyncManifestError(
                    f"page_source_mappings.{page_path}",
                    "must be a ManifestPageSource",
                )
            expected_prefix = (
                "modules/" if mapping.scope == MODULE_OBSERVATION_SCOPE else "entities/"
            )
            if not page_path.startswith(expected_prefix):
                raise SyncManifestError(
                    f"page_source_mappings.{page_path}.scope",
                    "does not match the page path",
                )

        for page_path, baseline in self.evidence_baselines.items():
            _validate_concept_page_path(page_path, f"evidence_baselines.{page_path}")
            if not isinstance(baseline, ManifestEvidenceBaseline):
                raise SyncManifestError(
                    f"evidence_baselines.{page_path}",
                    "must be a ManifestEvidenceBaseline",
                )
            baseline_mapping = self.page_source_mappings.get(page_path)
            if baseline_mapping is None:
                raise SyncManifestError(
                    f"evidence_baselines.{page_path}",
                    "requires a page source mapping",
                )
            source_info = self.sources.get(baseline_mapping.source_path)
            if source_info is None:
                raise SyncManifestError(
                    f"page_source_mappings.{page_path}.source_path",
                    "does not identify a current manifest source",
                )
            self._validate_basis_mapping(
                baseline.basis,
                baseline_mapping,
                f"evidence_baselines.{page_path}.basis",
            )
            source_hash = source_info.get("hash")
            if (
                baseline.basis is not None
                and is_valid_sha256(source_hash)
                and baseline.basis.source_content_hash != source_hash
            ):
                raise SyncManifestError(
                    (f"evidence_baselines.{page_path}.basis.source_content_hash"),
                    "does not match the current manifest source hash",
                )

        for page_path, tombstone in self.tombstones.items():
            _validate_concept_page_path(page_path, f"tombstones.{page_path}")
            if not isinstance(tombstone, ManifestTombstone):
                raise SyncManifestError(
                    f"tombstones.{page_path}",
                    "must be a ManifestTombstone",
                )
            if tombstone.last_valid_basis is None:
                continue
            tombstone_mapping = self.page_source_mappings.get(page_path)
            if tombstone_mapping is None:
                raise SyncManifestError(
                    f"tombstones.{page_path}",
                    "a last valid basis requires a page source mapping",
                )
            self._validate_basis_mapping(
                tombstone.last_valid_basis,
                tombstone_mapping,
                f"tombstones.{page_path}.last_valid_basis",
            )

        if self.artifact_hashes is not None and not isinstance(
            self.artifact_hashes, ManifestArtifactHashes
        ):
            raise SyncManifestError(
                "artifact_hashes", "must be a ManifestArtifactHashes"
            )

    @staticmethod
    def _validate_basis_mapping(
        basis: ConceptObservationBasis | None,
        mapping: ManifestPageSource,
        field_name: str,
    ) -> None:
        if basis is None:
            return
        if basis.scope != mapping.scope:
            raise SyncManifestError(
                f"{field_name}.scope",
                "does not match the page source mapping",
            )
        if basis.source_path != mapping.source_path:
            raise SyncManifestError(
                f"{field_name}.source_path",
                "does not match the page source mapping",
            )

    def to_payload(self) -> dict[str, object]:
        """Return the validated deterministic manifest v5 payload."""

        self._validate_operational_state()
        payload: dict[str, object] = {
            "version": MANIFEST_VERSION,
            "sources": self.sources,
            "surfaces": self.surfaces,
            "generation_inputs": self.generation_inputs,
            "page_source_mappings": {
                path: mapping.to_payload()
                for path, mapping in self.page_source_mappings.items()
            },
            "evidence_baselines": {
                path: baseline.to_payload()
                for path, baseline in self.evidence_baselines.items()
            },
            "tombstones": {
                path: tombstone.to_payload()
                for path, tombstone in self.tombstones.items()
            },
        }
        if self.artifact_hashes is not None:
            payload["artifact_hashes"] = self.artifact_hashes.to_payload()
        return payload

    def to_json(self) -> str:
        """Return deterministic UTF-8-ready JSON with one trailing newline."""

        return formatted_json_text(self.to_payload())

    def save(self, wiki_dir: Path) -> None:
        """Atomically write the manifest through the shared JSON boundary."""

        write_json_atomic(wiki_dir / MANIFEST_FILENAME, self.to_payload())

    def with_artifact_hashes(
        self,
        *,
        surface_index_hash: str,
        knowledge_index_hash: str,
        evaluated_envelope_hash: str,
    ) -> SyncManifest:
        """Return a copy carrying one complete artifact-set commitment."""

        return replace(
            self,
            artifact_hashes=ManifestArtifactHashes(
                surface_index_hash=surface_index_hash,
                knowledge_index_hash=knowledge_index_hash,
                evaluated_envelope_hash=evaluated_envelope_hash,
            ),
        )

    def without_artifact_hashes(self) -> SyncManifest:
        """Return a copy with no artifact-set commitment."""

        return replace(self, artifact_hashes=None)

    def with_generation_state(
        self,
        *,
        surfaces: Mapping[str, Mapping],
        generation_inputs: Mapping[str, object],
    ) -> SyncManifest:
        """Replace generation policy while invalidating any prior commitment."""

        return replace(
            self,
            surfaces={
                str(key): deepcopy(dict(value))
                for key, value in surfaces.items()
                if isinstance(value, Mapping)
            },
            generation_inputs=deepcopy(dict(generation_inputs)),
            artifact_hashes=None,
        )

    @classmethod
    def build_from_inventory(
        cls,
        inventory: dict,
        src_dir: str,
        entity_page_cache: dict[tuple[str, str], str],
        module_page_map: dict[str, str],
        *,
        entity_occurrence_page_cache: dict[tuple[str, str, int], str] | None = None,
        surfaces: Mapping[str, Mapping] | None = None,
        generation_inputs: Mapping[str, object] | None = None,
        previous_manifest: SyncManifest | None = None,
        evidence_baselines: Mapping[
            str, ConceptObservationBasis | ManifestEvidenceBaseline
        ]
        | None = None,
        source_content_hashes: Mapping[str, str] | None = None,
        retained_page_paths: Iterable[str] | None = None,
        unknown_evidence_reason: str = EVIDENCE_NOT_RECORDED,
    ) -> SyncManifest:
        """Build current state and reconcile retained prior page evidence.

        No evidence is inferred from page text. Callers may supply already
        evaluated KNOW-102 bases keyed by canonical page path. Without one, a
        compatible prior basis is retained or the page is explicitly unknown.
        ``source_content_hashes`` lets orchestration reuse hashes captured by
        its source snapshot; when omitted, the compatibility path reads and
        hashes each source as before. Rebuilding always clears artifact hashes;
        KNOW-107 installs a complete commitment only after both projections
        have been written.
        """

        sources: dict[str, dict] = {}
        page_source_mappings: dict[str, ManifestPageSource] = {}
        captured_hashes = _captured_source_hashes(
            inventory,
            source_content_hashes,
        )
        effective_module_page_map = dict(
            module_page_map or _build_module_page_map(inventory)
        )
        if entity_occurrence_page_cache is None:
            entity_occurrence_page_cache = _build_entity_occurrence_page_map(
                inventory, effective_module_page_map
            )
        for filepath, file_data in inventory.items():
            seen_entity_names: dict[str, int] = {}
            entity_page_occurrences = []
            first_entity_pages: dict[str, str] = {}
            for cls_info in file_data.get("classes", []):
                name = str(cls_info["name"])
                seen_entity_names[name] = seen_entity_names.get(name, 0) + 1
                occurrence = seen_entity_names[name]
                page_name = entity_occurrence_page_cache.get(
                    (name, filepath, occurrence),
                    entity_page_cache.get((name, filepath), name),
                )
                first_entity_pages.setdefault(name, page_name)
                entity_page_occurrences.append(
                    {
                        "name": name,
                        "page": page_name,
                        "occurrence": occurrence,
                    }
                )
                entity_path = _page_path(
                    ENTITY_OBSERVATION_SCOPE,
                    page_name,
                    f"entity_page_occurrences.{filepath}.{name}.{occurrence}",
                )
                _put_page_mapping(
                    page_source_mappings,
                    entity_path,
                    ManifestPageSource(
                        scope=ENTITY_OBSERVATION_SCOPE,
                        source_path=filepath,
                        entity_name=name,
                        occurrence=occurrence,
                    ),
                )
            module_page = effective_module_page_map.get(filepath, Path(filepath).stem)
            module_path = _page_path(
                MODULE_OBSERVATION_SCOPE,
                module_page,
                f"module_page_map.{filepath}",
            )
            _put_page_mapping(
                page_source_mappings,
                module_path,
                ManifestPageSource(
                    scope=MODULE_OBSERVATION_SCOPE,
                    source_path=filepath,
                ),
            )
            sources[filepath] = {
                "hash": (
                    captured_hashes[filepath]
                    if captured_hashes is not None
                    else hash_file(Path(src_dir) / filepath)
                ),
                "semantic_hash": semantic_hash_for_file(file_data),
                "generated_semantics": generated_semantics_for_file(
                    filepath, file_data
                ),
                "language": file_data.get("language")
                or _infer_language_from_path(filepath),
                "entities": [str(c["name"]) for c in file_data.get("classes", [])],
                "entity_pages": first_entity_pages,
                "entity_page_occurrences": entity_page_occurrences,
                "module_page": module_page,
            }

        _validate_reason(unknown_evidence_reason, "unknown_evidence_reason")
        provided = dict(evidence_baselines or {})
        extra_baselines = set(provided) - set(page_source_mappings)
        if extra_baselines:
            page_path = min(extra_baselines)
            raise SyncManifestError(
                f"evidence_baselines.{page_path}",
                "does not identify a current inventory page",
            )

        current_baselines: dict[str, ManifestEvidenceBaseline] = {}
        for page_path, mapping in page_source_mappings.items():
            source_hash = sources[mapping.source_path]["hash"]
            supplied = provided.get(page_path)
            if supplied is not None:
                baseline = (
                    supplied
                    if isinstance(supplied, ManifestEvidenceBaseline)
                    else ManifestEvidenceBaseline.from_basis(supplied)
                )
                cls._validate_basis_mapping(
                    baseline.basis,
                    mapping,
                    f"evidence_baselines.{page_path}.basis",
                )
                if (
                    baseline.basis is not None
                    and baseline.basis.source_content_hash != source_hash
                ):
                    raise SyncManifestError(
                        (f"evidence_baselines.{page_path}.basis.source_content_hash"),
                        "does not match the current source content hash",
                    )
                current_baselines[page_path] = baseline
                continue

            prior_mapping = (
                previous_manifest.page_source_mappings.get(page_path)
                if previous_manifest is not None
                else None
            )
            prior_baseline = (
                previous_manifest.evidence_baselines.get(page_path)
                if previous_manifest is not None
                else None
            )
            if (
                prior_mapping == mapping
                and prior_baseline is not None
                and (
                    prior_baseline.basis is None
                    or prior_baseline.basis.source_content_hash == source_hash
                )
            ):
                current_baselines[page_path] = prior_baseline
                continue

            prior_tombstone = (
                previous_manifest.tombstones.get(page_path)
                if previous_manifest is not None
                else None
            )
            if prior_mapping == mapping and prior_tombstone is not None:
                basis = prior_tombstone.last_valid_basis
                if basis is not None and basis.source_content_hash == source_hash:
                    current_baselines[page_path] = ManifestEvidenceBaseline.from_basis(
                        basis
                    )
                    continue
                if prior_tombstone.unknown_reason is not None:
                    current_baselines[page_path] = ManifestEvidenceBaseline.unknown(
                        prior_tombstone.unknown_reason
                    )
                    continue

            current_baselines[page_path] = ManifestEvidenceBaseline.unknown(
                unknown_evidence_reason
            )

        retained = (
            {
                _validate_concept_page_path(path, "retained_page_paths")
                for path in retained_page_paths
            }
            if retained_page_paths is not None
            else None
        )
        tombstones: dict[str, ManifestTombstone] = {}
        if previous_manifest is not None:
            current_coordinates = set(page_source_mappings.values())
            prior_paths = set(previous_manifest.page_source_mappings) | set(
                previous_manifest.tombstones
            )
            for page_path in prior_paths - set(page_source_mappings):
                if retained is not None and page_path not in retained:
                    continue
                prior_mapping = previous_manifest.page_source_mappings.get(page_path)
                coordinate_is_current = (
                    prior_mapping is not None and prior_mapping in current_coordinates
                )
                if prior_mapping is not None:
                    page_source_mappings[page_path] = prior_mapping
                prior_tombstone = previous_manifest.tombstones.get(page_path)
                if coordinate_is_current:
                    remap_reason = (
                        prior_tombstone.unknown_reason
                        if prior_tombstone is not None
                        and prior_tombstone.unknown_reason is not None
                        else SOURCE_MAPPING_CHANGED
                    )
                    tombstones[page_path] = ManifestTombstone(
                        reason=TOMBSTONE_UNKNOWN_PROVENANCE,
                        unknown_reason=remap_reason,
                    )
                    continue
                if prior_tombstone is not None:
                    tombstones[page_path] = prior_tombstone
                    continue
                prior_baseline = previous_manifest.evidence_baselines.get(page_path)
                if prior_baseline is not None and prior_baseline.is_known:
                    tombstones[page_path] = ManifestTombstone(
                        reason=TOMBSTONE_SOURCE_MISSING,
                        last_valid_basis=prior_baseline.basis,
                    )
                else:
                    unknown_reason = (
                        prior_baseline.unknown_reason
                        if prior_baseline is not None
                        else MANIFEST_STATE_UNAVAILABLE
                    ) or MANIFEST_STATE_UNAVAILABLE
                    tombstones[page_path] = ManifestTombstone(
                        reason=TOMBSTONE_UNKNOWN_PROVENANCE,
                        unknown_reason=unknown_reason,
                    )

        if retained is not None:
            for page_path in retained - set(page_source_mappings):
                tombstones[page_path] = ManifestTombstone(
                    reason=TOMBSTONE_UNKNOWN_PROVENANCE,
                    unknown_reason=MANIFEST_STATE_UNAVAILABLE,
                )

        manifest = cls(
            sources=sources,
            surfaces={
                str(key): deepcopy(dict(value))
                for key, value in (surfaces or {}).items()
                if isinstance(value, Mapping)
            },
            generation_inputs=deepcopy(dict(generation_inputs or {})),
            page_source_mappings=page_source_mappings,
            evidence_baselines=current_baselines,
            tombstones=tombstones,
            artifact_hashes=None,
        )
        manifest._validate_operational_state()
        return manifest


__all__ = [
    "EVIDENCE_NOT_RECORDED",
    "LEGACY_EVIDENCE_UNAVAILABLE",
    "LEGACY_MANIFEST_VERSION",
    "MANIFEST_FILENAME",
    "MANIFEST_REPAIR_UNAVAILABLE",
    "MANIFEST_STATE_UNAVAILABLE",
    "MANIFEST_VERSION",
    "PRODUCER_BASIS_INCOMPATIBLE",
    "SOURCE_MAPPING_CHANGED",
    "TOMBSTONE_SOURCE_MISSING",
    "TOMBSTONE_UNKNOWN_PROVENANCE",
    "ManifestArtifactHashes",
    "ManifestEvidenceBaseline",
    "ManifestPageSource",
    "ManifestTombstone",
    "SyncManifest",
    "SyncManifestError",
    "generated_semantics_for_file",
    "retained_concept_page_paths",
]
