"""Source-owned member retirement, separate from authored concept lifecycle."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from pathlib import PurePosixPath

from .sync_manifest import ManifestPageSource, SyncManifest, SyncManifestError
from .validation import portable_path_key
from .wiki_surface import PageKind, WikiSurfaceError, canonical_path

ENTITY_RETIREMENT_INPUT_KEY = "entity_retirement"
ENTITY_RETIREMENT_SCHEMA_VERSION = "llm-wiki-entity-retirement/v1"
SOURCE_RETIREMENT_EXTENSION_KEY = "llm-wiki/source-retirement"
SOURCE_MEMBER_REMOVED_HEADER = (
    "> **Retired source member:** This declaration is no longer in the selected "
    "source inventory. The content below is retained history, not current source "
    "evidence or an authored lifecycle decision.\n\n"
)


class SourceRetirementError(ValueError):
    """A retirement record cannot be reconciled with authoritative ownership."""


def retained_empty_module_paths(manifest: SyncManifest | None) -> tuple[str, ...]:
    """Return source paths whose last owning run retained a parser-empty module."""
    if manifest is None:
        return ()
    result = []
    for path, source in manifest.sources.items():
        if "empty_module" not in source:
            continue
        if source["empty_module"] is not True or source.get("entities") != []:
            raise SourceRetirementError(f"Invalid empty module source commitment: {path!r}")
        result.append(path)
    return tuple(sorted(result))


def retained_empty_module_paths_from_wiki(wiki_dir) -> tuple[str, ...]:
    """Read only the configured manifest to select parser retention, not evidence."""
    try:
        manifest = SyncManifest.load(wiki_dir)
    except FileNotFoundError:
        return ()
    return retained_empty_module_paths(manifest)


def read_entity_retirement_state(generation_inputs: Mapping[str, object]) -> dict[str, ManifestPageSource]:
    """Decode exact machine records without deriving ownership from Markdown."""
    if ENTITY_RETIREMENT_INPUT_KEY not in generation_inputs:
        return {}
    value = generation_inputs[ENTITY_RETIREMENT_INPUT_KEY]
    if not isinstance(value, Mapping) or not {"schema_version", "pages"} <= set(value) or set(value) - {"schema_version", "pages", "generated_semantics"}:
        raise SourceRetirementError("Invalid entity retirement record shape")
    if value["schema_version"] != ENTITY_RETIREMENT_SCHEMA_VERSION or not isinstance(value["pages"], Mapping):
        raise SourceRetirementError("Unsupported entity retirement schema or pages")
    result = {}
    keys = set()
    for path, payload in value["pages"].items():
        try:
            valid_path = isinstance(path, str) and path == canonical_path(PageKind.ENTITIES, PurePosixPath(path).stem)
        except WikiSurfaceError:
            valid_path = False
        if not valid_path:
            raise SourceRetirementError("Retirement path must be a canonical entity page")
        key = portable_path_key(path)
        if key in keys:
            raise SourceRetirementError("Portable retirement page collision")
        keys.add(key)
        try:
            owner = ManifestPageSource.from_payload(payload, f"entity_retirement.pages.{path}")
        except (SyncManifestError, ValueError) as exc:
            raise SourceRetirementError(f"Invalid retirement owner for {path!r}") from exc
        if owner.scope != "entity":
            raise SourceRetirementError("Retirement requires an entity source coordinate")
        result[path] = owner
    if len(set(result.values())) != len(result):
        raise SourceRetirementError("Multiple retirement pages claim the same coordinate")
    semantics = value.get("generated_semantics", {})
    if not isinstance(semantics, Mapping) or set(semantics) - set(result):
        raise SourceRetirementError("Invalid retained generated semantics page bindings")
    for baseline in semantics.values():
        if (
            not isinstance(baseline, Mapping) or set(baseline) != {"description", "attributes", "methods"}
            or not isinstance(baseline["description"], str)
            or any(not isinstance(baseline[field], Mapping) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in baseline[field].items()) for field in ("attributes", "methods"))
        ):
            raise SourceRetirementError("Invalid retained generated semantic baseline")
    return result


def entity_owner_present(owner: ManifestPageSource, sources: Mapping[str, Mapping]) -> bool:
    """Compare the exact declaration occurrence with captured source membership."""
    info = sources.get(owner.source_path)
    if info is None:
        return False
    entities = info.get("entities")
    if not isinstance(entities, list) or any(not isinstance(name, str) or not name for name in entities):
        raise SourceRetirementError("Source membership is unavailable for retirement qualification")
    return Counter(entities)[owner.entity_name] >= (owner.occurrence or 1)


def retired_entity_mappings(manifest: SyncManifest) -> dict[str, ManifestPageSource]:
    """Validate committed retirements against mappings and historical tombstones."""
    result = read_entity_retirement_state(manifest.generation_inputs)
    for path, owner in result.items():
        if (
            manifest.page_source_mappings.get(path) != owner
            or path not in manifest.tombstones
            or path in manifest.evidence_baselines
            or entity_owner_present(owner, manifest.sources)
        ):
            raise SourceRetirementError(f"Retirement is not bound to a removed historical member: {path!r}")
    return result


def with_entity_retirement_state(
    generation_inputs: Mapping[str, object], mappings: Mapping[str, ManifestPageSource],
    *, generated_semantics: Mapping[str, dict] | None = None,
) -> dict[str, object]:
    """Retain the planned coordinates without minting evidence or lifecycle."""
    result = dict(generation_inputs)
    if mappings:
        read_entity_retirement_state(generation_inputs)
        previous = generation_inputs.get(ENTITY_RETIREMENT_INPUT_KEY, {})
        old_semantics = previous.get("generated_semantics", {}) if isinstance(previous, Mapping) else {}
        baselines = {path: value for path, value in old_semantics.items() if path in mappings}
        baselines.update(generated_semantics or {})
        payload: dict[str, object] = {
            "schema_version": ENTITY_RETIREMENT_SCHEMA_VERSION,
            "pages": {path: owner.to_payload() for path, owner in sorted(mappings.items())},
        }
        if baselines:
            payload["generated_semantics"] = baselines
        result[ENTITY_RETIREMENT_INPUT_KEY] = payload
        read_entity_retirement_state(result)
    else:
        result.pop(ENTITY_RETIREMENT_INPUT_KEY, None)
    return result


def historical_entity_semantics(manifest: SyncManifest, owner: ManifestPageSource) -> dict | None:
    """Return recorded generated defaults for attribution when the owner revives."""
    marked = read_entity_retirement_state(manifest.generation_inputs)
    state = manifest.generation_inputs.get(ENTITY_RETIREMENT_INPUT_KEY, {})
    assert isinstance(state, Mapping)
    for path, recorded_owner in marked.items():
        if recorded_owner == owner:
            baseline = state.get("generated_semantics", {}).get(path)
            if baseline is not None:
                return dict(baseline)
    source = manifest.sources.get(owner.source_path, {})
    generated = source.get("generated_semantics", {})
    if not isinstance(generated, Mapping):
        return None
    duplicates = generated.get("entity_occurrences", {})
    occurrences = duplicates.get(owner.entity_name) if isinstance(duplicates, Mapping) else None
    if isinstance(occurrences, list) and owner.occurrence and owner.occurrence <= len(occurrences):
        value = occurrences[owner.occurrence - 1]
    elif Counter(source.get("entities", []))[owner.entity_name] == 1:
        entities = generated.get("entities", {})
        value = entities.get(owner.entity_name) if isinstance(entities, Mapping) else None
    else:
        return None
    return dict(value) if isinstance(value, Mapping) else None


def discover_retired_entities(manifest: SyncManifest, inventory: Mapping[str, Mapping]) -> dict[str, ManifestPageSource]:
    """Plan fresh removals and recover exact persisted, previously unmarked owners."""
    from .sync_analysis import _recorded_entity_pages

    recorded = _recorded_entity_pages(manifest)
    _check_duplicate_removal_custody(manifest, inventory, recorded)
    current = {
        path: {"entities": [str(cls["name"]) for cls in data.get("classes", [])]}
        for path, data in inventory.items()
    }
    marked = read_entity_retirement_state(manifest.generation_inputs)
    candidates = dict(manifest.page_source_mappings)
    for (source, name, occurrence), paths in recorded.pages.items():
        owner = ManifestPageSource("entity", source, name, occurrence)
        if source not in current or entity_owner_present(owner, current):
            continue
        if len(paths) != 1:
            raise SourceRetirementError(f"Ambiguous removed entity page for {owner!r}")
        page = recorded.resolve((source, name, occurrence))
        if page is not None:
            path = canonical_path(PageKind.ENTITIES, page)
            if path in candidates and candidates[path] != owner:
                raise SourceRetirementError(f"Conflicting removed page ownership: {path!r}")
            candidates[path] = owner
    result = {}
    for path, owner in candidates.items():
        if owner.scope != "entity" or entity_owner_present(owner, current):
            continue
        if owner.source_path not in current and path not in marked:
            continue
        claims = recorded.owners.get(portable_path_key(PurePosixPath(path).stem))
        coordinate = (owner.source_path, owner.entity_name, owner.occurrence)
        if claims != {coordinate}:
            raise SourceRetirementError(f"Removed page has ambiguous ownership: {path!r}")
        result[path] = owner
    if len(set(result.values())) != len(result):
        raise SourceRetirementError("Removed coordinate has multiple retained page bindings")
    return result


def _check_duplicate_removal_custody(manifest, inventory, recorded) -> None:
    """Require an unchanged, distinguishable surviving prefix before retiring suffixes."""
    from .knowledge_evidence import entity_observation_hash

    for source, data in inventory.items():
        previous = manifest.sources.get(source, {})
        old_counts = Counter(previous.get("entities", []))
        current_counts = Counter(cls["name"] for cls in data.get("classes", []))
        for name, old_count in old_counts.items():
            count = current_counts[name]
            if not 0 < count < old_count or old_count < 2:
                continue
            defaults = [historical_entity_semantics(manifest, ManifestPageSource("entity", source, name, n)) for n in range(1, old_count + 1)]
            for occurrence in range(1, count + 1):
                page = recorded.resolve((source, name, occurrence))
                baseline = manifest.evidence_baselines.get(canonical_path(PageKind.ENTITIES, page)) if page else None
                current_hash = entity_observation_hash(data, name, occurrence, inventory_complete=True)
                expected = defaults[occurrence - 1]
                if (
                    expected is None or defaults.count(expected) != 1
                    or baseline is None or baseline.basis is None
                    or current_hash is None or current_hash != baseline.basis.concept_observation_hash
                ):
                    raise SourceRetirementError(f"Ambiguous duplicate removal for {name!r} in {source!r}; review declaration and page custody before retrying")
                from .sync_manifest import generated_semantics_for_file
                generated = generated_semantics_for_file(source, data)
                current_defaults = generated.get("entity_occurrences", {}).get(name)
                actual = current_defaults[occurrence - 1] if current_defaults else generated.get("entities", {}).get(name)
                if actual != expected:
                    raise SourceRetirementError(f"Ambiguous duplicate removal for {name!r} in {source!r}; surviving declaration defaults changed")
