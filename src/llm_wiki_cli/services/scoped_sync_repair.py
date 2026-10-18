"""Fail-closed boundaries for scoped evidence application after full analysis."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from . import analysis_capture, analysis_compatibility as ac
from .contracts import SECTION_OWNERSHIP_EXTENSION_KEY
from .knowledge_artifacts import KnowledgeCommitPlan, validate_knowledge_artifacts
from .knowledge_model import knowledge_index_to_payload
from .knowledge_storage import canonical_bytes
from .knowledge_reuse import implementation_hash, wiki_input_hashes
from .source_snapshot import SourceSnapshotError, source_snapshot_matches_current_files
from .validation import require_repository_relative_path


class ScopedRepairError(ValueError):
    """The requested repair cannot preserve its declared scope."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ScopedRepairError(
            f"Scoped evidence repair refused: {reason}. "
            "Use ordinary sync --dry-run with the same roots/options to review the full owning update."
        )


def repair_paths(value) -> tuple[str, ...]:
    if value is None:
        return ()
    result = []
    for path in value:
        error = ScopedRepairError("--repair-evidence paths must be canonical POSIX paths relative to --src-dir")
        result.append(require_repository_relative_path(
            path, text_error=error, posix_error=error, normalized_error=error,
        ))
    return tuple(sorted(set(result)))


@analysis_capture.capture_operation
def _recapture(registry, root, helper_cache, languages):
    # A new operation is deliberate: the original capture's cache must not
    # conceal a provider/helper mutation after planning or isolated preview.
    return analysis_capture.capture_analysis(
        registry, source_root=root, helper_cache_dir=helper_cache, languages=languages,
    )


def _multiset(values):
    return Counter(json.dumps(v, sort_keys=True, separators=(",", ":")) for v in values)


def _markdown_hashes(root):
    from .knowledge_storage import MAX_EXPANDED_BYTES
    from .knowledge_storage_io import read_guarded
    from .wiki_surface import collect_wiki_pages

    return {page.relative_path: hashlib.sha256(read_guarded(page.path, MAX_EXPANDED_BYTES).content).hexdigest()
            for page in collect_wiki_pages(root)}


def _source_current(snapshot):
    try:
        return source_snapshot_matches_current_files(snapshot)
    except (OSError, SourceSnapshotError):
        return False


@dataclass(frozen=True)
class ScopedRepairBoundary:
    """Original global inputs and the only concept pages allowed to change."""

    options: Any
    prepared_inputs: Any
    paths: frozenset[str]
    pages: frozenset[str]
    wiki_hashes: tuple[str, str]
    producer: Any
    markdown_hashes: dict[str, str]
    package_hash: str

    def assert_current(self) -> None:
        p = self.prepared_inputs
        p.committed_state.assert_current()
        _require(_source_current(p.source_snapshot), "source or selection changed during repair")
        _require(wiki_input_hashes(self.options.wiki_dir) == self.wiki_hashes, "wiki inputs changed during repair")
        _require(_markdown_hashes(self.options.wiki_dir) == self.markdown_hashes, "Markdown bytes changed during repair")
        self.assert_analysis_current()

    def assert_analysis_current(self) -> None:
        p = self.prepared_inputs
        _require(_source_current(p.source_snapshot), "source or selection changed during repair")
        _require(implementation_hash() == self.package_hash, "installed provider changed during repair")
        current = _recapture(
            p.inventory_result.extractor_registry, p.source_snapshot.root,
            self.options.helper_cache_dir, {language for language, files in p.source_snapshot.files_by_language.items() if files},
        )
        _require(current == p.inventory_result.analysis_components, "provider, helper or runtime changed during repair")

    def validate_markdown(self, root) -> None:
        candidate = _markdown_hashes(root)
        _require(candidate.keys() == self.markdown_hashes.keys(), "page creation/removal needs full review")
        allowed = self.pages | {"log.md"}
        _require(all(candidate[k] == v for k, v in self.markdown_hashes.items() if k not in allowed),
                 "unselected Markdown bytes changed")

    def validate_plan(self, plan: KnowledgeCommitPlan) -> None:
        """Verify the full candidate, including globals, before root publication."""
        p = self.prepared_inputs
        self.assert_analysis_current()
        self.validate_markdown(self.options.wiki_dir)
        old = p.committed_state.artifacts.knowledge
        writes = {item.relative_path: item for item in plan.storage_objects}

        def read_object(name, maximum):
            item = writes.get(name)
            data = item.content if item is not None else p.committed_state.artifacts.storage_objects[name]
            _require(len(data) <= maximum, "planned native object exceeds its reader limit")
            return data

        validated = validate_knowledge_artifacts(
            surface_index_bytes=plan.surface_index.content,
            knowledge_index_bytes=plan.knowledge_index.content,
            manifest=plan.committed_manifest,
            object_reader=read_object,
        )
        new = validated.knowledge
        _require(old.bundle.producer == new.bundle.producer == self.producer, "producer transition requires a full owning update")
        before, after = (json.loads(json.dumps(knowledge_index_to_payload(k))) for k in (old, new))
        # Revision and snapshot roots are transaction metadata. All modeled
        # source inputs/options and repository identity must remain unchanged.
        for payload in (before, after):
            payload["bundle"]["repository"].pop("evaluated_revision", None)
            payload["bundle"]["snapshot"].pop("markdown_snapshot_hash", None)
            payload["bundle"]["snapshot"].pop("surface_index_hash", None)
        _require(canonical_bytes(before["bundle"]) == canonical_bytes(after["bundle"]),
                 "global source, options or repository basis changed")
        allowed = {c["locator"] for c in before["concepts"] if c["document"]["canonical_path"] in self.pages | {"log.md"}}
        left = {c["locator"]: c for c in before["concepts"]}
        right = {c["locator"]: c for c in after["concepts"]}
        _require(left.keys() == right.keys(), "concept creation or retirement needs full review")
        _require(all(canonical_bytes(left[k]) == canonical_bytes(right[k]) for k in left.keys() - allowed),
                 "unselected concept facts changed")
        _require(
            _multiset(r for r in before["relationships"] if r["from"] not in allowed)
            == _multiset(r for r in after["relationships"] if r["from"] not in allowed),
            "unselected relationship facts changed",
        )
        for payload in (before, after):
            extensions = payload["extensions"]
            # This closed operational extension commits globally collected
            # observations/cache inputs, not refreshed per-concept evidence.
            extensions.pop("llm-wiki/sync-analysis-v2", None)
            binding = extensions.get("llm-wiki/maintenance-binding")
            if binding is not None:
                binding.pop("state_hash", None)
            sections = extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY)
            if sections is not None:
                sections["pages"] = [row for row in sections["pages"] if row["page_locator"] not in allowed]
        changed = [key for key in before["extensions"].keys() | after["extensions"].keys()
                   if key not in before["extensions"] or key not in after["extensions"]
                   or canonical_bytes(before["extensions"][key]) != canonical_bytes(after["extensions"][key])]
        _require(not changed, "global graph, custody or unselected sections changed: "
                 + ", ".join(json.dumps(key[:128]) for key in sorted(changed)[:3]))
        left_manifest, right_manifest = (json.loads(json.dumps(m.to_payload()))
                                         for m in (p.manifest, plan.committed_manifest))
        left_state, right_state = left_manifest["maintenance_state"], right_manifest["maintenance_state"]
        _require(left_state is not None and right_state is not None, "maintenance custody disappeared")
        assert left_state is not None and right_state is not None
        _require(right_state["generation"] >= left_state["generation"], "maintenance generation regressed")
        for record_id, observation in list(left_state["observations"].items()):
            if observation["target"]["canonical_path"] not in self.pages:
                continue
            _require(record_id in right_state["observations"] and record_id in right_state["records"],
                     "selected maintenance identity disappeared")
            prior_record, current_record = left_state["records"][record_id], right_state["records"][record_id]
            _require(all(canonical_bytes(prior_record[k]) == canonical_bytes(current_record[k]) for k in
                         ("acknowledgment_history", "coordinate_history", "target_history")),
                     "repair changed review history or semantic identity")
            _require(current_record["current_acknowledgment_id"] in (None, prior_record["current_acknowledgment_id"])
                     and (prior_record["status"] != "pending" or current_record["status"] == "pending"),
                     "repair cannot acknowledge review")
            for state in (left_state, right_state):
                state["observations"].pop(record_id)
                state["records"].pop(record_id)
        for state in (left_state, right_state):
            state.pop("generation")
        for payload in (left_manifest, right_manifest):
            payload.pop("artifact_hashes", None)
            payload.pop("maintenance_state_hash", None)
            evidence = payload["evidence_baselines"]
            assert isinstance(evidence, dict)
            for page in self.pages:
                evidence.pop(page, None)
        _require(canonical_bytes(left_manifest) == canonical_bytes(right_manifest),
                 "unselected manifest facts or maintenance history changed")


def prepare_boundary(options, prepared) -> ScopedRepairBoundary:
    """Accept only an adopted, coherent, stable-producer unchanged-source repair."""
    from .knowledge_orchestration import (
        RuntimeLiveEvaluationInputs, build_runtime_live_evaluation,
        runtime_generation_options, RUNTIME_GENERATION_OPTION_DEFAULTS,
    )

    p = prepared
    _require(not p.seed_manifest and not p.repair_only and p.committed_state is not None
             and p.committed_state.artifacts is not None, "complete committed authority is required")
    assert p.committed_state is not None and p.committed_state.artifacts is not None
    _require(not p.generator_refresh_required, "global generator transition cannot be applied partially")
    _require(p.manifest.maintenance_state is not None, "ordinary maintenance ownership and its recovery preimage are required")
    _require(not p.runtime_provenance_changed, "global source or generation policy changed")
    _require(not p.diff.has_changes and not p.diff.missing_pages and not p.diff.generated_page_repairs,
             "mixed source edits, retirement or projection repairs require full review")
    _require(not p.surface_plan.has_work and not p.infrastructure_plan.has_changes
             and not p.source_selection_prune.deselected_source_paths,
             "surface, infrastructure or selection changes require full review")
    paths = frozenset(options.repair_paths)
    for path in sorted(paths):
        _require(path in p.manifest.sources and path in p.inventory
                 and path in p.source_snapshot.captured_content_hashes,
                 f"requested source is not previously owned, selected and documentable: {json.dumps(path[:256])}")
        baselines = [b for name, b in p.manifest.evidence_baselines.items()
                     if p.manifest.page_source_mappings[name].source_path == path]
        _require(bool(baselines) and all(b.is_known or b.unknown_reason == "invalid-inventory-shape" for b in baselines),
                 "requested evidence has unsupported or unavailable provenance")
        _require(all(b.is_known for b in baselines) or path in p.evidence_refresh_sources,
                 "requested invalid evidence does not normalize successfully")
    artifacts = p.committed_state.artifacts
    wiki_hashes = wiki_input_hashes(options.wiki_dir)
    _require(wiki_hashes[0] == artifacts.knowledge.bundle.snapshot.markdown_snapshot_hash,
             "canonical Markdown changed since the committed snapshot")
    live = build_runtime_live_evaluation(RuntimeLiveEvaluationInputs(
        knowledge=artifacts.knowledge, manifest=p.manifest, inventory=p.inventory,
        source_snapshot=p.source_snapshot,
        generation_options=runtime_generation_options(
            surfaces=p.surface_plan.surfaces, generation_inputs=p.surface_plan.generation_inputs,
            include_tests=options.include_tests, preserve_semantic=options.preserve_semantic,
        ), generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS,
        generation_option_allowlist=tuple(RUNTIME_GENERATION_OPTION_DEFAULTS),
        analysis_components=p.inventory_result.analysis_components,
        infrastructure_inventory=p.infrastructure_plan.inventory,
        extractor_registry=p.inventory_result.extractor_registry,
        plugin_extractor_components=p.inventory_result.plugin_components,
        plugin_components=p.inventory_result.producer_plugin_components,
    ))
    prior = artifacts.knowledge.bundle.producer
    _require(not prior.plugins and prior == live.producer,
             "producer/helper/runtime transition or plugin capture requires a full owning update")
    _require(all(ac.component_record(c) is not None for c in (prior.tool, *prior.extractors)),
             "complete producer analysis commitments are required; version labels are insufficient")
    pages = frozenset(name for name, owner in p.manifest.page_source_mappings.items() if owner.source_path in paths)
    for concept in artifacts.knowledge.concepts:
        page = concept.document.canonical_path
        if page not in pages:
            continue
        recorded = p.manifest.evidence_baselines[page].basis
        current = live.concept_bases.get(concept.locator)
        _require(recorded is not None and current is not None and current.is_known,
                 "complete captured source coordinates and valid fresh evidence are required")
        assert recorded is not None and current is not None
        _require((recorded.scope, recorded.source_path, recorded.extractor_ref, recorded.source_content_hash)
                 == (current.scope, current.source_path, current.extractor_ref, current.source_content_hash),
                 "captured source coordinates or bytes differ from current evidence")
        _require(not recorded.is_known or recorded.concept_observation_hash == current.concept_observation_hash,
                 "known observation changed despite unchanged source; full review is required")
    package_hash = implementation_hash()
    _require(package_hash is not None, "installed provider identity is unavailable")
    assert package_hash is not None
    boundary = ScopedRepairBoundary(options, p, paths, pages, wiki_hashes, live.producer,
                                    _markdown_hashes(options.wiki_dir), package_hash)
    boundary.assert_current()
    return boundary
