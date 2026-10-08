"""Authenticate historical stage bytes and score a fixed occurrence denominator."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from hashlib import sha256
import json
from typing import Any

from tests.developer_value.triage_oracle import resolve_review


def text_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def legacy_commitment(value: Any) -> str:
    """Preserve the historical index's original canonicalization convention."""
    return sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def pointer(value: Any, path: str) -> Any:
    if not path.startswith("/"):
        raise ValueError("An absolute JSON pointer is required.")
    for token in path[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def validate_row_index(
    index: Mapping[str, Any], triage: Mapping[str, Any], source_sha256: str
) -> None:
    rows = index["rows"]
    if (
        index["required_row_count"] != 122
        or len(rows) != 122
        or len(triage["rows"]) != 122
    ):
        raise ValueError("The historical denominator is exactly 122.")
    if index["source"]["sha256"] != source_sha256:
        raise ValueError("Historical source commitment differs.")
    for position, row in enumerate(rows):
        expected = f"dv23:{source_sha256}:rows:{position:06d}"
        raw = triage["rows"][position]
        if (
            row["row_id"] != expected
            or row["source_row"]["json_pointer"] != f"/rows/{position}"
        ):
            raise ValueError("Historical occurrence identity was altered.")
        if legacy_commitment(raw) != row["source_row"]["row_canonical_sha256"]:
            raise ValueError("Historical row bytes were altered.")
        if (raw["case"], raw["stage"], raw["path"]) != (
            row["case_id"],
            row["observation_stage"],
            row["page_path"],
        ):
            raise ValueError("Historical case/stage/target identity differs.")


def validate_read(read: Mapping[str, Any]) -> None:
    for field in ("source", "authored"):
        text = read[field]
        if set(text) != set(read[field + "_hashes"]):
            raise ValueError("Read transcript hash inventory is incomplete.")
        if any(
            text_hash(value) != read[field + "_hashes"][name]
            for name, value in text.items()
        ):
            raise ValueError("Read transcript bytes do not match its commitments.")


def source_at_stage(capture: Mapping[str, Any], stage: str) -> dict[str, str]:
    """Only mutation/source lineage establishes post-edit source, never labels."""
    reads = capture["direct_source"]["reads"]
    before = next(r for r in reads if r["stage"] == "before")
    after = next(r for r in reads if r["stage"] == "mutation")
    validate_read(before)
    validate_read(after)
    mutations = [
        e
        for e in capture["events"]
        if e["step"].get("action") == "apply-declared-source-mutation"
    ]
    if len(mutations) != 1:
        raise ValueError("Source mutation lineage is ambiguous.")
    mutation = mutations[0]["result"]
    name = mutation["path"]
    if name.startswith("src/"):
        name = name[4:]
    if (
        before["source"].get(name) != mutation["before_text"]
        or after["source"].get(name) != mutation["after_text"]
    ):
        raise ValueError("Mutation event does not bind the source transcripts.")
    if (
        text_hash(mutation["before_text"]) != mutation["before_sha256"]
        or text_hash(mutation["after_text"]) != mutation["after_sha256"]
    ):
        raise ValueError("Mutation source commitment differs.")
    if set(before["source"]) != set(after["source"]) or any(
        before["source"][p] != after["source"][p] for p in before["source"] if p != name
    ):
        raise ValueError("Additional unrecorded source changes exist.")
    if stage not in {"before", "after", "after-edit", "after-sync", "after-restart"}:
        raise ValueError("Unresolved historical source stage.")
    return dict(before["source"] if stage == "before" else after["source"])


def replay_semantic_insert(base: str, edit: Mapping[str, Any]) -> str:
    """Restore recorded prose in memory; both full-page hashes must authenticate it."""
    if text_hash(base) != edit["before_sha256"]:
        raise ValueError("Retained pre-edit page is not the recorded base.")
    patch = edit["semantic_edit"]
    heading = "## " + patch["heading"] + "\n"
    if (
        patch["kind"] != "insert-after-heading"
        or patch["preserve_existing_prose"] is not True
        or base.count(heading) != 1
    ):
        raise ValueError("Semantic prose edit cannot be replayed unambiguously.")
    text = patch["text"]
    if text_hash(text) != patch["text_sha256"]:
        raise ValueError("Recorded authored fragment is corrupted.")
    restored = base.replace(heading, heading + "\n" + text + "\n", 1)
    if text_hash(restored) != edit["after_sha256"]:
        raise ValueError("Reconstruction does not match the recorded post-edit bytes.")
    return restored


def retrospective_score(
    expected: Sequence[Mapping[str, Any]],
    submitted: Sequence[Mapping[str, Any]],
    required: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Missing judgments/capsules earn no credit; original surfacing is separate."""
    ids = [r["row_id"] for r in expected]
    if len(ids) != 122 or len(set(ids)) != 122:
        raise ValueError("Keep all 122 original occurrence identities.")
    if len(required) != 4 or len({(r["case_id"], r["page"]) for r in required}) != 4:
        raise ValueError("Keep the fixed four case/owner obligations.")
    by_id = {r["row_id"]: r for r in submitted}
    if len(by_id) != len(submitted) or set(by_id) - set(ids):
        raise ValueError("Duplicate or unexpected retrospective submissions.")
    counts: Counter[str] = Counter()
    final = []
    covered: set[int] = set()
    seen: set[tuple[str, str, str, str]] = set()
    for row in expected:
        incoming = by_id.get(row["row_id"], {})
        capsule = incoming.get("capsule")
        label, actions = "unknown", []
        if isinstance(capsule, Mapping) and (
            capsule.get("row_id"),
            capsule.get("case_id"),
            capsule.get("stage"),
            capsule.get("page"),
        ) == (
            row["row_id"],
            row["case_id"],
            row["observation_stage"],
            row["page_path"],
        ):
            decision = resolve_review(
                capsule, incoming.get("reviews", []), incoming.get("adjudication")
            )
            label, actions = decision["label"], decision["supported_actions"]
        fresh = []
        if label == "actionable":
            for action in actions:
                identity = (
                    row["case_id"],
                    row["observation_stage"],
                    action["owner"],
                    action["operation"],
                )
                if identity not in seen:
                    fresh.append(action)
                    seen.add(identity)
            if not fresh:
                label = "nonactionable"
        counts[label] += 1
        for n, obligation in enumerate(required):
            if (
                row["case_id"] == obligation["case_id"]
                and row["page_path"] == obligation["page"]
                and row["observation_stage"] in obligation["eligible_stages"]
                and any(
                    a["owner"] == obligation["owner"]
                    and a["operation"] in obligation["operations"]
                    for a in fresh
                )
            ):
                covered.add(n)
        final.append(
            {
                "row_id": row["row_id"],
                "case_id": row["case_id"],
                "stage": row["observation_stage"],
                "page": row["page_path"],
                "label": label,
                "supported_actions": fresh,
            }
        )
    return {
        "kind": "supplemental-retrospective",
        "denominator": 122,
        "actionable": counts["actionable"],
        "nonactionable": counts["nonactionable"],
        "unknown": counts["unknown"],
        "fraction": counts["actionable"] / 122,
        "required": 4,
        "covered": len(covered),
        "required_coverage": len(covered) / 4,
        "missed": [r for n, r in enumerate(required) if n not in covered],
        "rows": final,
        "retrospective_thresholds_met": counts["actionable"] * 5 >= 122 * 4
        and len(covered) == 4,
        "original_independent_actionability": "historical-unmeasured",
        "original_path_surfacing": {"surfaced": 4, "required": 4},
        "prospective_product_gate": "not-established-by-retrospective-score",
    }
