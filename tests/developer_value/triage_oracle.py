"""Source-cited triage reviews and occurrence scoring, independent of providers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from hashlib import sha256
import json
from typing import Any


LABELS = frozenset({"actionable", "nonactionable", "unknown"})
OPERATIONS = frozenset(
    {"revise-claim", "inspect-pending-mapping", "repair-link", "explain-gap"}
)


def commitment(value: Any) -> str:
    return sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def occurrence_id(
    campaign: str, case: str, stage: str, response_hash: str, index: int
) -> str:
    if type(index) is not int or index < 0:
        raise ValueError("Occurrence index must be nonnegative.")
    if not all(
        isinstance(v, str) and v for v in (campaign, case, stage, response_hash)
    ):
        raise ValueError(
            "Occurrence identity requires campaign, case, stage and response commitment."
        )
    return commitment([campaign, case, stage, response_hash, index])


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def citation_valid(capsule: Mapping[str, Any], citation: Mapping[str, Any]) -> bool:
    artifacts = capsule.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        return False
    artifact = artifacts.get(citation.get("artifact"))
    if not isinstance(artifact, Mapping) or not isinstance(artifact.get("text"), str):
        return False
    text = artifact["text"]
    actual = sha256(text.encode()).hexdigest()
    if artifact.get("sha256") != actual or citation.get("sha256") != actual:
        return False
    first, last = citation.get("first_line"), citation.get("last_line")
    lines = text.splitlines()
    if (
        type(first) is not int
        or type(last) is not int
        or not 1 <= first <= last <= len(lines)
    ):
        return False
    return citation.get("quote") == "\n".join(lines[first - 1 : last])


def review_valid(capsule: Mapping[str, Any], review: Mapping[str, Any]) -> bool:
    if review.get("row_id") != capsule.get("row_id") or review.get(
        "capsule_manifest_sha256"
    ) != commitment(capsule):
        return False
    if review.get("label") not in LABELS or not _text(
        review.get("disconfirming_condition")
    ):
        return False
    actor, visibility = review.get("actor"), review.get("visibility")
    if not isinstance(actor, Mapping) or not all(
        _text(actor.get(k)) for k in ("agent_id", "session_id", "role")
    ):
        return False
    if actor["role"] not in {"reviewer-a", "reviewer-b", "adjudicator"}:
        return False
    if (
        not isinstance(visibility, Mapping)
        or visibility.get("provider_labels_seen") is not False
    ):
        return False
    if (
        type(visibility.get("prior_reviews_seen")) is not bool
        or type(visibility.get("oracle_results_seen")) is not bool
    ):
        return False
    if not isinstance(review.get("limitations"), list):
        return False
    citations = review.get("evidence_citations")
    if not isinstance(citations, list) or not all(
        isinstance(c, Mapping) and citation_valid(capsule, c) for c in citations
    ):
        return False
    label = review["label"]
    if label == "unknown":
        return _text(review.get("uncertainty_reason")) and not review.get(
            "supported_actions"
        )
    if not citations or not _text(review.get("completion_condition")):
        return False
    kinds = {capsule["artifacts"][c["artifact"]].get("kind") for c in citations}
    if not {"source", "prose", "ownership", "task"} <= kinds:
        return False
    actions = review.get("supported_actions", [])
    if label == "nonactionable":
        return not actions and _text(review.get("rationale"))
    if (
        not _text(review.get("proposed_action"))
        or not isinstance(actions, list)
        or not actions
    ):
        return False
    return all(
        isinstance(a, Mapping)
        and a.get("owner") == capsule.get("owner")
        and a.get("operation") in OPERATIONS
        for a in actions
    )


def resolve_review(
    capsule: Mapping[str, Any],
    reviews: Sequence[Mapping[str, Any]],
    adjudication: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(reviews, (list, tuple)) or any(
        not isinstance(r, Mapping) for r in reviews
    ):
        return {
            "row_id": capsule["row_id"],
            "label": "unknown",
            "supported_actions": [],
            "reviewer_independence": False,
            "agreement": False,
            "valid_reviews": False,
            "capsule_manifest_sha256": commitment(capsule),
            "review_a_sha256": None,
            "review_b_sha256": None,
            "adjudication_sha256": None,
            "invalid_review_submission_sha256": commitment(reviews),
        }
    if not isinstance(adjudication, Mapping):
        adjudication = None
    valid = (
        len(reviews) == 2
        and all(review_valid(capsule, r) for r in reviews)
        and [r["actor"]["role"] for r in reviews] == ["reviewer-a", "reviewer-b"]
    )
    agreed = (
        valid
        and reviews[0]["label"] == reviews[1]["label"]
        and reviews[0].get("supported_actions", [])
        == reviews[1].get("supported_actions", [])
    )
    independent = (
        valid
        and reviews[0]["actor"]["agent_id"] != reviews[1]["actor"]["agent_id"]
        and reviews[0]["actor"]["session_id"] != reviews[1]["actor"]["session_id"]
        and all(
            r["actor"].get("fresh_no_fork") is True
            and r["visibility"].get("prior_reviews_seen") is False
            and r["visibility"].get("oracle_results_seen") is False
            for r in reviews
        )
    )
    if agreed:
        selected = reviews[0]
    elif (
        adjudication is not None
        and review_valid(capsule, adjudication)
        and adjudication["actor"]["role"] == "adjudicator"
        and len(reviews) == 2
    ):
        binding = adjudication.get("adjudication", {})
        if (
            not isinstance(binding, Mapping)
            or binding.get("review_a_sha256") != commitment(reviews[0])
            or binding.get("review_b_sha256") != commitment(reviews[1])
            or not _text(binding.get("resolution_reason"))
        ):
            selected = {"label": "unknown", "supported_actions": []}
        else:
            selected = adjudication
    else:
        selected = {"label": "unknown", "supported_actions": []}
    return {
        "row_id": capsule["row_id"],
        "label": selected["label"],
        "supported_actions": selected.get("supported_actions", []),
        "reviewer_independence": bool(independent),
        "agreement": bool(agreed),
        "valid_reviews": bool(valid),
        "capsule_manifest_sha256": commitment(capsule),
        "review_a_sha256": commitment(reviews[0]) if reviews else None,
        "review_b_sha256": commitment(reviews[1]) if len(reviews) > 1 else None,
        "adjudication_sha256": commitment(adjudication) if adjudication else None,
    }


def score_campaign(
    campaign: str,
    schedule: Sequence[Mapping[str, str]],
    obligations: Sequence[Mapping[str, str]],
    captures: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Score every returned occurrence; malformed/incomplete captures cannot pass."""
    expected = [(s["case_id"], s["stage"]) for s in schedule]
    if not expected or len(expected) != len(set(expected)):
        raise ValueError(
            "Freeze a nonempty schedule with unique case/stage identities."
        )
    obligation_keys = [
        (o["case_id"], o["stage"], o["owner"], o["operation"]) for o in obligations
    ]
    if len(obligation_keys) != len(set(obligation_keys)) or any(
        k[:2] not in expected for k in obligation_keys
    ):
        raise ValueError(
            "Required actions must have unique scheduled owner/action identities."
        )
    issues: list[str] = []
    counts: Counter[str] = Counter()
    covered: set[tuple[str, str, str, str]] = set()
    rows: list[dict[str, Any]] = []
    seen_stages: list[tuple[str, str]] = []
    for capture in captures:
        case, stage = capture.get("case_id"), capture.get("stage")
        if not _text(case) or not _text(stage):
            issues.append("invalid-capture-identity")
        case, stage = str(case), str(stage)
        key = (case, stage)
        seen_stages.append(key)
        repetition = seen_stages.count(key) - 1
        raw = capture.get("response")
        if not isinstance(raw, Mapping) or not isinstance(raw.get("items"), list):
            issues.append("invalid-response")
            continue
        response_hash = commitment(raw)
        items = raw["items"]
        if capture.get("response_sha256") != response_hash:
            issues.append("response-commitment-mismatch")
        if any(
            type(raw.get(k)) is not int or raw[k] < 0
            for k in ("total", "returned", "omitted")
        ):
            issues.append("invalid-capture-counts")
        elif (
            raw["returned"] != len(items)
            or raw["total"] != raw["returned"] + raw["omitted"]
        ):
            issues.append("capture-counts-mismatch")
        if raw.get("omitted") != 0 or raw.get("truncated") is not False:
            issues.append("truncated-response")
        resolutions = capture.get("resolutions", {})
        capsules = capture.get("capsules", {})
        if not isinstance(resolutions, Mapping) or not isinstance(capsules, Mapping):
            issues.append("invalid-review-index")
            resolutions, capsules = {}, {}
        within_response: set[tuple[str, str]] = set()
        for index, item in enumerate(items):
            row_commitment = (
                response_hash
                if not repetition
                else commitment([response_hash, repetition])
            )
            ident = occurrence_id(
                campaign, str(case), str(stage), row_commitment, index
            )
            resolved = resolutions.get(ident, {})
            capsule = capsules.get(ident)
            label = "unknown"
            actions: list[Any] = []
            # Final resolutions are checked against the submitted source capsule,
            # not trusted as provider labels or caller-authored final verdicts.
            if (
                isinstance(item, Mapping)
                and isinstance(resolved, Mapping)
                and isinstance(capsule, Mapping)
                and capsule.get("row_id") == ident
                and capsule.get("case_id") == case
                and capsule.get("stage") == stage
                and capsule.get("owner") == item.get("owner")
            ):
                checked = resolve_review(
                    capsule, resolved.get("reviews", []), resolved.get("adjudication")
                )
                label, actions = checked["label"], checked["supported_actions"]
            credited = []
            if label == "actionable":
                for action in actions:
                    action_key = (action["owner"], action["operation"])
                    if action_key not in within_response:
                        credited.append(action)
                        within_response.add(action_key)
                if not credited:
                    label = "nonactionable"
            counts[label] += 1
            for action in credited:
                covered.add(
                    (str(case), str(stage), action["owner"], action["operation"])
                )
            rows.append(
                {
                    "row_id": ident,
                    "case_id": case,
                    "stage": stage,
                    "index": index,
                    "label": label,
                    "supported_actions": credited,
                }
            )
    if Counter(seen_stages) != Counter(expected):
        issues.append("incomplete-or-repeated-schedule")
    required = set(obligation_keys)
    matched = required & covered
    denominator = sum(counts.values())
    fraction = counts["actionable"] / denominator if denominator else None
    coverage = len(matched) / len(required) if required else None
    passed = (
        not issues
        and denominator > 0
        and counts["actionable"] * 5 >= denominator * 4
        and bool(required)
        and matched == required
    )
    return {
        "campaign": campaign,
        "actionable": counts["actionable"],
        "nonactionable": counts["nonactionable"],
        "unknown": counts["unknown"],
        "denominator": denominator,
        "fraction": fraction,
        "required_count": len(required),
        "covered_count": len(matched),
        "coverage": coverage,
        "missed": [list(k) for k in sorted(required - matched)],
        "issues": issues,
        "rows": rows,
        "passed": bool(passed),
    }
