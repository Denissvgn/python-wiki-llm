"""Native custody of explicitly retained pages from a removed source file."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePosixPath
from urllib.parse import quote

from .contracts import SECTION_OWNERSHIP_EXTENSION_KEY
from .knowledge_evidence import hash_json, is_valid_sha256, sha256_bytes
from .knowledge_envelope import EvaluatedEnvelope
from .source_retirement import SourceRetirementError
from .sync_manifest import (PRODUCER_BASIS_INCOMPATIBLE, ManifestEvidenceBaseline, ManifestPageSource, SyncManifest)
from .validation import portable_path_key
from .wiki_surface import PageKind, canonical_path

INPUT = "historical_source_files"
SCHEMA = "llm-wiki-historical-source-files/v1"
EXTENSION = "llm-wiki/historical-source-file"
RELEASES = "historical_source_releases"
RELEASE_EXTENSION = "llm-wiki/historical-source-releases"
RELEASE_SCHEMA = "llm-wiki-historical-source-releases/v1"
HEADING = "### Historical source files"
STALE_HEADER = (
    "> ⚠️ **Stale:** Source no longer found in codebase. "
    "Run `llm-wiki lint` to audit.\n\n"
)


def _refuse(message: str) -> SourceRetirementError:
    return SourceRetirementError(f"Historical source retirement: {message}")


def read_records(inputs: Mapping) -> dict:
    if INPUT not in inputs:
        return {}
    value = inputs[INPUT]
    if (not isinstance(value, Mapping) or set(value) != {"schema_version", "pages"}
            or value["schema_version"] != SCHEMA or not isinstance(value["pages"], Mapping)
            or not value["pages"]):
        raise _refuse("invalid registry schema")
    claimed_paths = set()
    claimed_owners = set()
    pages = {}
    for path, row in value["pages"].items():
        if not isinstance(row, Mapping) or set(row) != {
            "owner", "basis", "page_hash", "marked_page_hash", "producer_hash", "knowledge_hash"
        }:
            raise _refuse(f"invalid predecessor record for {path!r}")
        try:
            owner = ManifestPageSource.from_payload(row["owner"], "historical.owner")
            basis = ManifestEvidenceBaseline.from_payload(
                {"state": "known", "basis": row["basis"]}, "historical.basis"
            ).basis
            if basis is None:
                raise ValueError("a known basis is required")
            kind = PageKind.MODULES if owner.scope == "module" else PageKind.ENTITIES
            expected = canonical_path(kind, PurePosixPath(path).stem)
        except (ValueError, TypeError) as exc:
            raise _refuse(f"invalid page or source evidence for {path!r}") from exc
        if (path != expected or portable_path_key(path) in claimed_paths or owner in claimed_owners
                or basis.scope != owner.scope or basis.source_path != owner.source_path
                or any(not is_valid_sha256(row[key]) for key in ("page_hash", "marked_page_hash", "producer_hash", "knowledge_hash"))):
            raise _refuse(f"inconsistent predecessor proof for {path!r}")
        claimed_paths.add(portable_path_key(path))
        claimed_owners.add(owner)
        pages[path] = row
    return pages


def release_events(inputs: Mapping) -> list:
    """Validate append order, subject commitments and the retained original proofs."""
    if RELEASES not in inputs:
        return []
    value = inputs[RELEASES]
    if (not isinstance(value, Mapping) or set(value) != {"schema_version", "events"}
            or value["schema_version"] != RELEASE_SCHEMA or not isinstance(value["events"], (list, tuple))
            or not value["events"]):
        raise _refuse("invalid release ledger")
    previous = None
    for event in value["events"]:
        if not isinstance(event, Mapping) or set(event) != {"digest", "basis"}:
            raise _refuse("invalid release event")
        basis = event["basis"]
        if (not isinstance(basis, Mapping) or set(basis) != {"parent", "knowledge_hash", "index_hash", "pages"}
                or basis["parent"] != previous or not is_valid_sha256(basis["knowledge_hash"])
                or not is_valid_sha256(basis["index_hash"]) or not isinstance(basis["pages"], Mapping)
                or not basis["pages"] or len(basis["pages"]) > 4096):
            raise _refuse("invalid release predecessor")
        records = {}
        for path, page in basis["pages"].items():
            if not isinstance(page, Mapping) or set(page) != {"record", "retained_page_hash"}:
                raise _refuse("invalid released page")
            records[path] = page["record"]
        read_records({INPUT: {"schema_version": SCHEMA, "pages": records}})
        for path, page in basis["pages"].items():
            if page["retained_page_hash"] not in {records[path]["page_hash"], records[path]["marked_page_hash"]}:
                raise _refuse("released bytes do not belong to the original owner")
        if event["digest"] != hash_json(basis):
            raise _refuse("release digest does not match its original evidence")
        previous = event["digest"]
    return list(value["events"])


def latest_released_pages(inputs: Mapping) -> dict:
    """Return the most recent release entry for each canonical page."""
    latest = {}
    for event in release_events(inputs):
        latest.update(event["basis"]["pages"])
    return latest


def make_release(previous, prior, index_bytes, page_bytes):
    records = bound_records(previous)
    events = release_events(previous.generation_inputs)
    if not page_bytes or not set(page_bytes) <= records.keys():
        raise _refuse("each released page must belong to the active historical registry")
    selected = {}
    for path, raw in sorted(page_bytes.items()):
        original = records[path]
        if not page_matches(raw, original["page_hash"]):
            raise _refuse(f"restore the exact historical Markdown at {path!r} from its verified backup before release")
        selected[path] = {"record": original, "retained_page_hash": sha256_bytes(raw)}
    basis = {"parent": events[-1]["digest"] if events else None, "knowledge_hash": prior.knowledge_index_hash,
             "index_hash": sha256_bytes(index_bytes), "pages": selected}
    event = {"basis": basis, "digest": hash_json(basis)}
    inputs = dict(previous.generation_inputs)
    remaining = {path: row for path, row in records.items() if path not in selected}
    if remaining:
        inputs[INPUT] = {"schema_version": SCHEMA, "pages": remaining}
    else:
        del inputs[INPUT]
    inputs[RELEASES] = {"schema_version": RELEASE_SCHEMA, "events": [*events, event]}
    return inputs, event


def bound_records(manifest: SyncManifest) -> dict:
    pages = read_records(manifest.generation_inputs)
    for path, row in pages.items():
        owner = manifest.page_source_mappings.get(path)
        tombstone = manifest.tombstones.get(path)
        if (owner is None or owner.to_payload() != row["owner"]
                or owner.source_path in manifest.sources or path in manifest.evidence_baselines
                or tombstone is None or (tombstone.last_valid_basis is None
                    and tombstone.unknown_reason != PRODUCER_BASIS_INCOMPATIBLE)
                or (tombstone.last_valid_basis is not None
                    and tombstone.last_valid_basis.to_evidence_payload() != row["basis"])):
            raise _refuse(f"historical record has no matching removed native owner at {path!r}")
    return pages


def predecessor_records(manifest, artifacts, pages):
    """Derive proof from a validated native predecessor, never from a client receipt."""
    from .knowledge_artifacts import require_validated_artifacts

    if manifest is None or manifest.artifact_hashes is None or artifacts is None:
        raise _refuse("an intact committed predecessor is required")
    artifacts = require_validated_artifacts(artifacts)
    marker = manifest.artifact_hashes
    if (marker.knowledge_index_hash != artifacts.knowledge_index_hash
            or marker.surface_index_hash != artifacts.surface_index_hash
            or marker.evaluated_envelope_hash != artifacts.evaluated_envelope_hash):
        raise _refuse("the predecessor manifest does not bind its validated native projections")
    sections = artifacts.knowledge.extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY, {}).get("pages", ())
    page_hashes = {row["page_locator"]: row["source_hash"] for row in sections}
    concepts = {c.document.canonical_path: c for c in artifacts.knowledge.concepts}
    producer = EvaluatedEnvelope(artifacts.knowledge.bundle).to_payload()["bundle"]["producer"]
    producer_hash = hash_json(producer)
    result = {}
    for path, raw in pages.items():
        owner = manifest.page_source_mappings.get(path)
        baseline = manifest.evidence_baselines.get(path)
        concept = concepts.get(path)
        if owner is None or baseline is None or not baseline.is_known or concept is None:
            raise _refuse(f"{path!r} has no validated active predecessor")
        old_source = manifest.sources.get(owner.source_path)
        basis = baseline.basis
        historic = basis.to_evidence_payload()
        native = concept.facets.structure.basis
        page_hash = page_hashes.get(concept.locator)
        if (not isinstance(old_source, Mapping) or basis.scope != owner.scope
                or basis.source_path != owner.source_path or basis.source_content_hash != old_source.get("hash")
                or native is None or native.scope.value != basis.scope or native.source_path != basis.source_path
                or native.source_content_hash != basis.source_content_hash or native.extractor_ref != basis.extractor_ref
                or native.concept_observation_hash != basis.concept_observation_hash or not is_valid_sha256(page_hash)):
            raise _refuse(f"inconsistent structural evidence or missing Markdown commitment at {path!r}")
        if sha256_bytes(raw) != page_hash:
            raise _refuse(f"{path!r} has no exact Markdown preimage in the authenticated predecessor")
        result[path] = {"owner": owner.to_payload(), "basis": historic, "page_hash": page_hash,
                        "marked_page_hash": sha256_bytes(STALE_HEADER.encode("utf-8") + raw),
                        "producer_hash": producer_hash, "knowledge_hash": artifacts.knowledge_index_hash}
    return result


def validate_transition(previous, prior_artifacts, manifest, confirmed_missing, content):
    """Validate fresh claims, immutable retained proofs, and positive source revival."""
    old_events = [] if previous is None else release_events(previous.generation_inputs)
    if release_events(manifest.generation_inputs) != old_events:
        raise _refuse("ordinary source sync cannot create or rewrite a historical release event")
    old = {} if previous is None else bound_records(previous)
    new = bound_records(manifest)
    if not old and not new:
        return new
    if {row["owner"]["source_path"] for row in new.values()} - set(confirmed_missing):
        raise _refuse("historical sources are not confirmed missing from this complete source evaluation")
    for path in old.keys() & new.keys():
        if old[path] != new[path]:
            raise _refuse(f"historical predecessor proof changed for {path!r}")
    added = new.keys() - old.keys()
    if added:
        originals = {}
        for path in added:
            value = content.get(path)
            if isinstance(value, str):
                value = value.encode("utf-8")
            if not isinstance(value, bytes):
                raise _refuse(f"enrolled page {path!r} has no Markdown")
            originals[path] = value if sha256_bytes(value) == new[path]["page_hash"] else value.removeprefix(STALE_HEADER.encode("utf-8"))
        required = predecessor_records(previous, prior_artifacts, originals)
        if any(new[path] != required[path] for path in added):
            raise _refuse("new native historical proof differs from its actual predecessor")
    for path in old.keys() - new.keys():
        record = old[path]
        owner = manifest.page_source_mappings.get(path)
        baseline = manifest.evidence_baselines.get(path)
        if (owner is None or owner.to_payload() != record["owner"] or baseline is None or not baseline.is_known
                or baseline.basis.source_content_hash != record["basis"]["source_content_hash"]):
            raise _refuse(f"historical page {path!r} can only return with its original positive source owner")
    return new


def check_projections(manifest, knowledge):
    records = bound_records(manifest)
    releases = release_events(manifest.generation_inputs)
    projection = knowledge.extensions.get(RELEASE_EXTENSION)
    if (releases and projection != manifest.generation_inputs[RELEASES]) or (
        not releases and RELEASE_EXTENSION in knowledge.extensions
    ):
        raise _refuse("native historical release ledger differs from its manifest owner")
    seen = set()
    hashes = {}
    if records:
        sections = knowledge.extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY, {}).get("pages", ())
        hashes = {row["page_locator"]: row["source_hash"] for row in sections}
    for concept in knowledge.concepts:
        row = records.get(concept.document.canonical_path)
        if row is None:
            if EXTENSION in concept.extensions:
                raise _refuse(f"unbound historical projection on {concept.locator!r}")
            continue
        if concept.extensions.get(EXTENSION) != row or hashes.get(concept.locator) not in {
            row["page_hash"], row["marked_page_hash"]
        }:
            raise _refuse(f"historical projection or its Markdown differs from the native record at {concept.locator!r}")
        structural = concept.facets.structure
        last = manifest.tombstones[concept.document.canonical_path].last_valid_basis
        actual = structural.basis
        if last is None:
            valid = structural.evidence.value == "unknown" and structural.origin.value == "unknown" and actual is None
        else:
            valid = (structural.evidence.value == "present" and structural.origin.value == "extracted"
                     and actual is not None and actual.scope.value == last.scope and actual.source_path == last.source_path
                     and actual.extractor_ref == last.extractor_ref and actual.source_content_hash == last.source_content_hash
                     and actual.concept_observation_hash == last.concept_observation_hash)
        if not valid:
            raise _refuse(f"current structural evidence disagrees with the historical tombstone at {concept.locator!r}")
        seen.add(concept.document.canonical_path)
    if seen != set(records):
        raise _refuse("an enrolled historical page is missing from the native projection")
    return records


def registry_block(records: Mapping) -> str:
    if not records:
        return ""
    lines = [HEADING, "", "<!-- llm-wiki:historical-source-files/v1 -->",
             "These pages preserve documentation from earlier source revisions.", ""]
    for path in sorted(records):
        label = path.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
        lines.append(f"- [{label}]({quote(path, safe='/._-')})")
    lines.append("<!-- /llm-wiki:historical-source-files/v1 -->")
    return "\n".join(lines)


def insert_registry(index: str, records: Mapping) -> str:
    """Place the historical subregistry inside the generated Surface Overview section."""
    from .markdown_sections import parse_markdown_document

    sections = parse_markdown_document(index, "index.md").sections
    overviews = [section for section in sections if section.level == 2 and section.title == "Surface Overview"]
    if len(overviews) != 1:
        raise _refuse("the index renderer must provide one generated Surface Overview section")
    end = next((s.start for s in sections if s.level <= 2 and s.start > overviews[0].start), len(index))
    left, right = index[:end].rstrip("\n"), index[end:].lstrip("\n")
    return left + "\n\n" + registry_block(records) + ("\n\n" + right if right else "\n")


def remove_bound_registry(index: str, records: Mapping) -> str:
    """Only consume the exact native registry. Never consume an authored namesake."""
    block = registry_block(records)
    if block:
        if index.splitlines().count(HEADING) != 1 or index.count(block) != 1:
            raise _refuse("the historical source registry does not match its native records")
        before, _, after = index.partition(block)
        if next((line for line in reversed(before.splitlines()) if line.startswith("## ")), None) != "## Surface Overview":
            raise _refuse("the historical registry is outside its generated index section")
        return before + after
    if HEADING in index.splitlines():
        raise _refuse("an authored section occupies the historical registry heading")
    return index


def page_matches(data: bytes, expected: str) -> bool:
    if sha256_bytes(data) == expected:
        return True
    header = STALE_HEADER.encode("utf-8")
    return data.startswith(header) and sha256_bytes(data[len(header):]) == expected


def check_content(records: Mapping, content: Mapping) -> None:
    if not records:
        return
    if "index.md" not in content:
        raise _refuse("the historical source index is missing")
    index = content["index.md"]
    remove_bound_registry(index.decode("utf-8") if isinstance(index, bytes) else index, records)
    for path, row in records.items():
        value = content.get(path)
        if isinstance(value, str):
            value = value.encode("utf-8")
        if not isinstance(value, bytes) or not page_matches(value, row["page_hash"]):
            raise _refuse(f"retained page bytes differ from the authenticated predecessor at {path!r}")


def validate_release_transition(previous, prior, next_manifest, index_bytes, pages, expected_digest):
    """Authorize only a metadata release derived from the exact current native owner."""
    from .knowledge_artifacts import require_validated_artifacts

    prior = require_validated_artifacts(prior)
    if previous.artifact_hashes is None or previous.artifact_hashes.knowledge_index_hash != prior.knowledge_index_hash:
        raise _refuse("release source is not the authenticated previous native owner")
    check_projections(previous, prior.knowledge)
    inputs, event = make_release(previous, prior, index_bytes, pages)
    if (event["digest"] != expected_digest or read_records(inputs) != bound_records(next_manifest)
            or release_events(inputs) != release_events(next_manifest.generation_inputs)
            or previous.maintenance_state != next_manifest.maintenance_state
            or previous.page_source_mappings != next_manifest.page_source_mappings
            or previous.evidence_baselines != next_manifest.evidence_baselines
            or previous.tombstones != next_manifest.tombstones or previous.sources != next_manifest.sources):
        raise _refuse("release changed source/maintenance custody or differs from its checked preview")
