"""Bounded native coverage diagnostics, separate from frozen context payloads."""

from collections import Counter
from collections.abc import Mapping
import json
from typing import Any

from .knowledge_consumption import KnowledgeReadView
from .knowledge_freshness import (
    KNOWN_FRESHNESS_REASON_CODES,
    structural_freshness_modeled,
)
from .knowledge_model import ComputedFreshness, ConceptKind


KNOWLEDGE_COVERAGE_SCHEMA_VERSION = "llm-wiki-knowledge-coverage/v1"
_KINDS = frozenset(kind.value for kind in ConceptKind)
MAX_COVERAGE_BYTES = 16 * 1024


def build_knowledge_coverage(view: KnowledgeReadView) -> dict[str, Any]:
    """Count eligibility before evidence outcomes; never publish input identities."""
    if not isinstance(view, KnowledgeReadView):
        raise TypeError("view must be a validated knowledge read view")
    payload: dict[str, Any] = {
        "schema_version": KNOWLEDGE_COVERAGE_SCHEMA_VERSION,
        "availability": view.availability.value,
        "reason": view.reason_code,
        "read_scope": view.mode.value,
        "freshness_evaluated": view.freshness_evaluated,
        "counts": None,
        "by_kind": None,
        "reasons": None,
    }
    if not view.ready or view.knowledge is None:
        return payload

    freshness = view.freshness
    concepts = view.knowledge.concepts
    if freshness is not None and set(freshness.by_locator) != {
        item.locator for item in concepts
    }:
        raise ValueError("coverage requires one freshness outcome per concept")

    def counts() -> dict[str, Any]:
        return {
            "total": 0,
            "modeled": 0,
            "unmodeled": 0,
            "compared": 0,
            "modeled_freshness": None
            if freshness is None
            else {state.value: 0 for state in ComputedFreshness},
        }

    total = counts()
    by_kind: dict[str, dict[str, Any]] = {}
    reasons: Counter[str] = Counter()
    for concept in concepts:
        value = getattr(concept.concept_kind, "value", concept.concept_kind)
        kind = value if value in _KINDS else "other"
        row = by_kind.setdefault(kind, counts())
        modeled = structural_freshness_modeled(concept)
        outcome = None if freshness is None else freshness.by_locator[concept.locator]
        if outcome is not None and outcome.live_comparison_performed and not modeled:
            raise ValueError("an unmodeled concept cannot claim a live comparison")
        for target in (total, row):
            target["total"] += 1
            target["modeled" if modeled else "unmodeled"] += 1
            if outcome is not None:
                target["compared"] += int(outcome.live_comparison_performed)
                if modeled:
                    target["modeled_freshness"][outcome.state.value] += 1
        if outcome is not None:
            reason = (
                outcome.reason_code
                if outcome.reason_code in KNOWN_FRESHNESS_REASON_CODES
                else "other"
            )
            reasons[reason] += 1
    payload.update(
        counts=total,
        by_kind=dict(sorted(by_kind.items())),
        reasons=None if freshness is None else dict(sorted(reasons.items())),
    )
    if (
        len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        > MAX_COVERAGE_BYTES
    ):
        raise ValueError("coverage exceeds its fixed diagnostic byte bound")
    return payload


def render_knowledge_coverage(payload: Mapping[str, Any]) -> str:
    lines = [
        f"Knowledge coverage: {payload['availability']} ({payload['reason']})",
        f"Read scope: {payload['read_scope']}",
    ]
    counts = payload["counts"]
    if counts is None:
        lines.append("Concept counts: unavailable; this is not an empty trusted model.")
        return "\n".join(lines) + "\n"
    lines.append(
        f"Concepts: {counts['total']}; modeled: {counts['modeled']}; unmodeled: {counts['unmodeled']}"
    )
    if payload["freshness_evaluated"]:
        lines.append(
            f"Live comparisons: {counts['compared']} of {counts['modeled']} modeled concepts"
        )
        states = ", ".join(
            f"{name}={count}" for name, count in counts["modeled_freshness"].items()
        )
        lines.append(f"Modeled freshness: {states}")
    else:
        lines.append(
            "Freshness: not evaluated; snapshot-only counts do not establish currentness."
        )
    for kind, row in payload["by_kind"].items():
        lines.append(
            f"  {kind}: {row['modeled']} modeled, {row['unmodeled']} unmodeled, {row['compared']} compared"
        )
    if payload["reasons"]:
        lines.append(
            "Reasons: "
            + ", ".join(f"{code}={count}" for code, count in payload["reasons"].items())
        )
    lines.append(
        "Unmodeled is not stale. Current means the recorded observation is unchanged."
    )
    return "\n".join(lines) + "\n"
