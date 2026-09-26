"""Capture detailed health once from an operation's already evaluated inputs.

This module performs no I/O or source extraction. Serialized capture prevents
later changes to a caller's view, source files or installed version from
rewriting the evidence subsequently rendered by doctor or CI.
"""

from __future__ import annotations

from collections import Counter
from bisect import insort
from dataclasses import dataclass
import json
from typing import Any

from .contracts import HEALTH_DETAILS_SCHEMA_VERSION
from .health_contract import (
    COMPARABLE_STATES,
    EXAMPLE_LIMIT,
    FRESHNESS_STATES,
    HealthDetailsError,
)
from .knowledge_artifacts import require_validated_artifacts
from .knowledge_consumption import KnowledgeReadView
from .knowledge_evidence import canonical_json_text, hash_json
from .knowledge_envelope import hash_source_snapshot
from .knowledge_freshness import structural_freshness_modeled
from .knowledge_model import ProducerComponent, ProducerRecord
from .source_snapshot import SourceSnapshot


@dataclass(frozen=True)
class CapturedHealthDetails:
    """An immutable capture with independently owned output dictionaries."""

    encoded: str

    def to_payload(self) -> dict[str, Any]:
        return json.loads(self.encoded)


def _component(component: ProducerComponent) -> dict[str, Any]:
    return {
        "id": component.component_id,
        "version": component.version,
        "configuration_hash": component.configuration_hash,
        "limitations": list(component.limitations),
    }


def _producer(
    producer: ProducerRecord, schema: str, options_hash: str
) -> dict[str, Any]:
    return {
        "knowledge_schema_version": schema,
        "generation_options_hash": options_hash,
        "tool": _component(producer.tool),
        "extractors": [
            _component(item)
            for item in sorted(producer.extractors, key=lambda item: item.component_id)
        ],
        "plugins": [
            _component(item)
            for item in sorted(producer.plugins, key=lambda item: item.component_id)
        ],
    }


def capture_health_details(
    view: KnowledgeReadView | None,
    *,
    wiki_dir: str,
    src_dir: str,
    source_snapshot: SourceSnapshot | None = None,
    evaluation_failed: bool = False,
) -> CapturedHealthDetails:
    """Capture inventory, exact comparison basis and bounded primary examples."""
    knowledge = None if view is None else view.knowledge
    freshness = None if view is None else view.freshness
    live = None if freshness is None else freshness.live_producer
    evaluated = knowledge is not None and live is not None
    state = (
        ("partial" if evaluation_failed else "evaluated")
        if evaluated
        else "failed"
        if evaluation_failed
        else "not-evaluated"
        if knowledge is not None
        else "unavailable"
    )
    reason = {
        "evaluated": "captured-live-evaluation",
        "partial": "source-extraction-incomplete",
        "failed": "evaluation-failed",
        "not-evaluated": "live-evaluation-not-performed",
        "unavailable": "recorded-knowledge-unavailable",
    }[state]
    selection: dict[str, Any] = {
        "state": "unavailable",
        "fingerprint": None,
        "inputs_hash": None,
    }
    if source_snapshot is not None:
        configured = source_snapshot.source_selection_policy is not None
        selection.update(
            state="configured" if configured else "legacy",
            fingerprint=source_snapshot.source_selection_fingerprint,
            inputs_hash=hash_json(source_snapshot.source_selection_inputs)
            if configured
            else None,
        )
    snapshot: dict[str, Any] = {
        "validated": False,
        "knowledge_index_hash": None,
        "evaluated_envelope_hash": None,
        "surface_index_hash": None,
        "recorded_source_hash": None,
        "recorded_markdown_hash": None,
        # Reuse the persisted snapshot hashing contract over captured inputs.
        "live_source_hash": None
        if source_snapshot is None
        else hash_source_snapshot(source_snapshot.to_consumed_inputs()),
    }
    if view is not None:
        try:
            artifacts = require_validated_artifacts(view.validated_artifacts)
        except TypeError:
            artifacts = None
        if artifacts is not None and artifacts.knowledge is knowledge:
            snapshot.update(
                validated=True,
                knowledge_index_hash=artifacts.knowledge_index_hash,
                evaluated_envelope_hash=artifacts.evaluated_envelope_hash,
                surface_index_hash=artifacts.surface_index_hash,
            )
    basis: dict[str, Any] = {
        "policy": "exact-producer-versions",
        "analysis_contract": None,
        "recorded": None,
        "live": None,
    }
    coverage: dict[str, Any] = dict.fromkeys(
        (
            "total",
            "modeled",
            "unmodeled",
            "evaluated",
            "comparison_attempted",
            "comparable",
            "outcomes",
        )
    )
    reasons = []
    if knowledge is not None:
        snapshot.update(
            recorded_source_hash=knowledge.bundle.snapshot.source_snapshot_hash,
            recorded_markdown_hash=knowledge.bundle.snapshot.markdown_snapshot_hash,
        )
        basis["recorded"] = _producer(
            knowledge.bundle.producer,
            knowledge.schema_version,
            knowledge.bundle.snapshot.generation_options_hash,
        )
        modeled = sum(
            structural_freshness_modeled(concept) for concept in knowledge.concepts
        )
        total = len(knowledge.concepts)
        coverage.update(total=total, modeled=modeled, unmodeled=total - modeled)
        if evaluated:
            assert freshness is not None and live is not None
            if len(freshness.by_locator) != total:
                raise HealthDetailsError(
                    "freshness results do not cover the recorded inventory"
                )
            assert freshness.live_schema_version is not None
            assert freshness.live_generation_options_hash is not None
            basis["live"] = _producer(
                live,
                freshness.live_schema_version,
                freshness.live_generation_options_hash,
            )
            outcomes: Counter[str] = Counter()
            reason_counts: Counter[str] = Counter()
            examples: dict[str, list[str]] = {}
            attempted = 0
            for concept in knowledge.concepts:
                result = freshness.by_locator.get(concept.locator)
                if result is None or result.locator != concept.locator:
                    raise HealthDetailsError(
                        "freshness result does not match its recorded locator"
                    )
                if structural_freshness_modeled(concept):
                    outcomes[result.state.value] += 1
                    attempted += result.live_comparison_performed
                reason_counts[result.reason_code] += 1
                sample = examples.setdefault(result.reason_code, [])
                if len(sample) < EXAMPLE_LIMIT or concept.locator < sample[-1]:
                    insort(sample, concept.locator)
                    del sample[EXAMPLE_LIMIT:]
            coverage.update(
                evaluated=modeled,
                comparison_attempted=attempted,
                comparable=sum(outcomes[state] for state in COMPARABLE_STATES),
                outcomes={state: outcomes[state] for state in sorted(FRESHNESS_STATES)},
            )
            reasons = [
                {
                    "code": code,
                    "concepts": count,
                    "examples": examples[code],
                    "omitted": count - len(examples[code]),
                }
                for code, count in sorted(reason_counts.items())
            ]
    payload = {
        "schema_version": HEALTH_DETAILS_SCHEMA_VERSION,
        "scope": {"wiki_dir": wiki_dir, "src_dir": src_dir, "selection": selection},
        "evaluation": {"state": state, "reason": reason},
        "snapshot": snapshot,
        "basis": basis,
        "coverage": coverage,
        "reasons": reasons,
    }
    return CapturedHealthDetails(canonical_json_text(payload))
