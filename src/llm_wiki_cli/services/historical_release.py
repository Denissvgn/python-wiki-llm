"""Release a verified historical binding without updating or adopting any source."""

from dataclasses import replace
import hashlib
from pathlib import Path

from llm_wiki_engine import historical_sources as history
from llm_wiki_engine.contracts import SECTION_OWNERSHIP_EXTENSION_KEY
from llm_wiki_engine.io import decode_markdown_bytes, write_bytes_atomic
from llm_wiki_engine.knowledge_artifacts import (
    build_knowledge_commit_plan, commit_knowledge_artifacts, validated_artifact_bytes,
)
from llm_wiki_engine.knowledge_envelope import EvaluatedEnvelope, hash_markdown_snapshot
from llm_wiki_engine.knowledge_index import KnowledgeIndexInputs, _assemble_knowledge_index
from llm_wiki_engine.knowledge_links import collect_link_observations
from llm_wiki_engine.knowledge_storage import MAX_EXPANDED_BYTES
from llm_wiki_engine.knowledge_storage_io import StorageReadSession, read_guarded
from llm_wiki_engine.maintenance_protocol import guard_maintenance_owner
from llm_wiki_engine.section_ownership import observe_page_sections
from llm_wiki_engine.source_retirement import SourceRetirementError
from llm_wiki_engine.sync_manifest import MANIFEST_FILENAME, SyncManifest
from llm_wiki_engine.wiki_media import build_asset_index
from llm_wiki_engine.wiki_surface import PageKind, collect_wiki_pages
from .infrastructure_sync import infrastructure_evidence_by_page
from .knowledge_orchestration import capture_committed_knowledge
from .knowledge_reuse import REUSE_INPUT_KEY, REUSE_EXTENSION_KEY
from .sync_analysis_cache import EXTENSION as SYNC_ANALYSIS
from .sync_transition_execution import _bounded_page_digest


def _read_originals(root, canonical_pages):
    with StorageReadSession(root).phase() as reader:
        files = {p.relative_path: reader.read(p.relative_path, MAX_EXPANDED_BYTES) for p in canonical_pages}
        commitments = {path: (len(observed.content), hashlib.sha256(observed.content).digest(),
                             (observed.identity, observed.directories))
                       for path, observed in reader.observations.items()}
    return files, commitments


def _project(artifacts, manifest, root, pages, content, released):
    """Refresh Markdown-derived index facts only. Keep the evaluated source snapshot."""
    model = artifacts.knowledge
    old_index = next(c for c in model.concepts if c.document.page_kind is PageKind.INDEX)
    new_snapshot = replace(model.bundle.snapshot, markdown_snapshot_hash=hash_markdown_snapshot(content))
    bundle = replace(model.bundle, snapshot=new_snapshot)
    extensions = dict(model.extensions)
    extensions.pop(REUSE_EXTENSION_KEY, None)
    extensions.pop(SYNC_ANALYSIS, None)
    extensions[history.RELEASE_EXTENSION] = manifest.generation_inputs[history.RELEASES]
    old_sections = model.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]
    new_sections = observe_page_sections(content["index.md"], old_index.locator, PageKind.INDEX).to_payload()
    extensions[SECTION_OWNERSHIP_EXTENSION_KEY] = {
        **old_sections, "pages": [new_sections if r["page_locator"] == old_index.locator else r
                                 for r in old_sections["pages"]],
    }
    surface, _ = validated_artifact_bytes(artifacts)
    assets = build_asset_index(root, content).existing_paths
    evaluated = _assemble_knowledge_index(KnowledgeIndexInputs(
        envelope=EvaluatedEnvelope(bundle), pages=pages, content_by_page=content, surface_index_bytes=surface,
        page_source_mappings=manifest.page_source_mappings, evidence_baselines=manifest.evidence_baselines,
        tombstones=manifest.tombstones, infrastructure_bases=infrastructure_evidence_by_page(manifest.generation_inputs),
        link_observations=collect_link_observations(pages, content, existing_asset_paths=assets),
    ))
    index = next(c for c in evaluated.concepts if c.locator == old_index.locator)
    concepts = []
    for concept in model.concepts:
        if concept.locator == old_index.locator:
            semantic = replace(concept.facets.semantics, page_hash=index.facets.semantics.page_hash)
            concept = replace(concept, facets=replace(concept.facets, semantics=semantic))
        elif concept.document.canonical_path in released:
            kept = dict(concept.extensions)
            del kept[history.EXTENSION]
            concept = replace(concept, extensions=kept)
        concepts.append(concept)
    index_links = [r for r in evaluated.relationships if r.source_locator == old_index.locator]
    relationships = []
    emitted = False
    for relation in model.relationships:
        if relation.source_locator != old_index.locator:
            relationships.append(relation)
        elif not emitted:
            relationships.extend(index_links)
            emitted = True
    if not emitted:
        relationships.extend(index_links)
    return replace(model, bundle=bundle, concepts=tuple(concepts), relationships=tuple(relationships), extensions=extensions)


def run_release(options, write_basis):
    """Plan and publish one manifest-last release. Source changes are deliberately deferred."""
    root = Path(options.wiki_dir)
    selection = set(options.release_historical_pages)
    expected = options.expected_historical_release
    manifest = SyncManifest.load(root)
    state = capture_committed_knowledge(root, manifest)
    artifacts = state.artifacts
    if artifacts is None:
        raise SourceRetirementError("Restore the intact native snapshot before releasing a historical page")
    events = history.release_events(manifest.generation_inputs)
    records = history.check_projections(manifest, artifacts.knowledge)
    if selection.isdisjoint(records) and expected:
        for event in events:
            if event["digest"] == expected and set(event["basis"]["pages"]) == selection:
                return {"digest": expected, "pages": sorted(selection), "applied": not options.dry_run, "replayed": True}
    if not selection <= records.keys():
        raise SourceRetirementError("Release requires the exact canonical paths of currently enrolled historical pages")
    pages = collect_wiki_pages(root)
    files, commitments = _read_originals(root, pages)
    if not selection <= files.keys() or "index.md" not in files:
        raise SourceRetirementError("Restore each selected page and its exact historical index from verified backups before release")
    history.check_content(records, files)
    content = {name: decode_markdown_bytes(raw) for name, raw in files.items()}
    if hash_markdown_snapshot(content) != artifacts.knowledge.bundle.snapshot.markdown_snapshot_hash:
        locators = {c.locator: c.document.canonical_path for c in artifacts.knowledge.concepts}
        sections = artifacts.knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]["pages"]
        expected_hashes = {locators[row["page_locator"]]: row["source_hash"] for row in sections}
        changed = set(expected_hashes) ^ content.keys()
        changed.update(path for path in expected_hashes.keys() & content.keys()
                       if "sha256:" + hashlib.sha256(content[path].encode("utf-8")).hexdigest() != expected_hashes[path])
        first = min(changed) if changed else "index.md"
        raise SourceRetirementError(f"Restore the whole wiki Markdown to its authenticated snapshot; first difference: {first!r}")
    selected_bytes = {path: files[path] for path in selection}
    inputs, event = history.make_release(manifest, artifacts, files["index.md"], selected_bytes)
    digest = event["digest"]
    if (expected and expected != digest) or (not options.dry_run and not expected):
        raise SourceRetirementError("Historical release needs the matching digest from --dry-run in --expected-historical-release")
    inputs.pop(REUSE_INPUT_KEY, None)
    next_manifest = manifest.with_generation_state(surfaces=manifest.surfaces, generation_inputs=inputs)
    remaining = history.bound_records(next_manifest)
    index = history.remove_bound_registry(content["index.md"], records)
    if remaining:
        index = history.insert_registry(index, remaining)
    content["index.md"] = index
    knowledge = _project(artifacts, next_manifest, root, pages, content, selection)
    history.validate_release_transition(manifest, artifacts, next_manifest, files["index.md"], selected_bytes, digest)
    surface, _ = validated_artifact_bytes(artifacts)
    plan = build_knowledge_commit_plan(root, surface_index_bytes=surface, knowledge_index=knowledge,
        manifest=next_manifest, prior=artifacts, maintenance_adoption=guard_maintenance_owner(root, manifest))
    if plan.maintenance_adoption is not None and plan.maintenance_adoption.needs_write:
        raise SourceRetirementError("Historical release cannot create or replace the adopted maintenance marker")
    history.validate_release_transition(manifest, artifacts, plan.committed_manifest, files["index.md"], selected_bytes, digest)

    def check_markdown(expected_index):
        if {p.relative_path for p in collect_wiki_pages(root)} != files.keys():
            raise SourceRetirementError("Wiki page membership changed during historical release; preview again")
        for path, (size, digest, identity) in commitments.items():
            if path == "index.md" and expected_index != files[path]:
                actual, _ = _bounded_page_digest(root / path, len(expected_index))
                valid = actual == hashlib.sha256(expected_index).digest()
            else:
                valid = _bounded_page_digest(root / path, size) == (digest, identity)
            if not valid:
                raise SourceRetirementError(f"Wiki page {path!r} changed during historical release; restore it and preview again")

    planned_index = index.encode("utf-8")
    state.assert_current()
    check_markdown(files["index.md"])
    if not options.dry_run:
        if write_basis is not None:
            write_basis.assert_current()
        write_bytes_atomic(root / "index.md", planned_index)
        try:
            state.assert_current()
            check_markdown(planned_index)

            def confirm_release():
                # The native writer has verified its new projection roots. The
                # old manifest and the author's files must still authorize this release.
                if read_guarded(root / MANIFEST_FILENAME, MAX_EXPANDED_BYTES).content != state.captured_bytes[MANIFEST_FILENAME]:
                    raise SourceRetirementError("Native manifest changed during historical release; preview again")
                check_markdown(planned_index)

            commit_knowledge_artifacts(plan, before_manifest=confirm_release)
        except BaseException:
            # Restore only bytes this operation still owns, and only while the
            # original manifest is authoritative. Preserve any concurrency conflict.
            before = state.captured_bytes[MANIFEST_FILENAME]
            if read_guarded(root / MANIFEST_FILENAME, MAX_EXPANDED_BYTES).content == before:
                for published in (plan.knowledge_index, plan.surface_index):
                    previous_raw = state.captured_bytes[published.relative_path]
                    if (published.needs_write and previous_raw is not None
                            and read_guarded(published.path, MAX_EXPANDED_BYTES).content == published.content):
                        write_bytes_atomic(published.path, previous_raw)
                if read_guarded(root / "index.md", MAX_EXPANDED_BYTES).content == planned_index:
                    write_bytes_atomic(root / "index.md", files["index.md"])
            raise
    else:
        commit_knowledge_artifacts(plan, dry_run=True)
        state.assert_current()
        check_markdown(files["index.md"])
    return {"digest": digest, "pages": sorted(selection), "applied": not options.dry_run, "replayed": False}
