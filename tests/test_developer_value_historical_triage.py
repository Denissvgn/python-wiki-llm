"""Historical evidence gaps cannot disappear from retrospective denominators."""

from copy import deepcopy

import pytest

from tests.developer_value.historical_triage import (
    legacy_commitment,
    pointer,
    replay_semantic_insert,
    retrospective_score,
    source_at_stage,
    text_hash,
    validate_row_index,
)
from tests.test_developer_value_triage_oracle import judgment, packet


def historical_index():
    raw = [
        {
            "case": "owned",
            "stage": "after",
            "path": "entities/Policy.md",
            "provider_classification": "actionable",
        }
        for _ in range(122)
    ]
    source_hash = "a" * 64
    rows = [
        {
            "row_id": f"dv23:{source_hash}:rows:{n:06d}",
            "case_id": r["case"],
            "observation_stage": r["stage"],
            "page_path": r["path"],
            "source_row": {
                "json_pointer": f"/rows/{n}",
                "row_canonical_sha256": legacy_commitment(r),
            },
        }
        for n, r in enumerate(raw)
    ]
    return (
        {"required_row_count": 122, "source": {"sha256": source_hash}, "rows": rows},
        {"rows": raw},
        source_hash,
    )


@pytest.mark.parametrize("defect", [None, "row-id", "path", "hash", "denominator"])
def test_original_index_requires_every_exact_occurrence_and_row_commitment(defect):
    index, raw, h = historical_index()
    if defect == "row-id":
        index["rows"][1]["row_id"] = index["rows"][0]["row_id"]
    elif defect == "path":
        raw["rows"][1]["path"] = "other.md"
    elif defect == "hash":
        h = "b" * 64
    elif defect == "denominator":
        index["rows"].pop()
    if defect:
        with pytest.raises(ValueError):
            validate_row_index(index, raw, h)
    else:
        validate_row_index(index, raw, h)


def source_capture():
    before = {"policy.py": "value = 3\n", "other.py": "value = 7\n"}
    after = {**before, "policy.py": "value = 4\n"}
    prose = {"guides/index.md": "A stable guide.\n"}
    reads = [
        {
            "stage": stage,
            "source": s,
            "source_hashes": {p: text_hash(t) for p, t in s.items()},
            "authored": prose,
            "authored_hashes": {p: text_hash(t) for p, t in prose.items()},
        }
        for stage, s in (("before", before), ("mutation", after))
    ]
    return {
        "direct_source": {"reads": reads},
        "events": [
            {
                "step": {"action": "apply-declared-source-mutation"},
                "result": {
                    "path": "policy.py",
                    "before_text": before["policy.py"],
                    "after_text": after["policy.py"],
                    "before_sha256": text_hash(before["policy.py"]),
                    "after_sha256": text_hash(after["policy.py"]),
                },
            }
        ],
    }


@pytest.mark.parametrize(
    "stage", ["before", "after", "after-edit", "after-sync", "after-restart"]
)
def test_source_lineage_preserves_before_and_distinct_post_edit_stages(stage):
    expected = "value = 3\n" if stage == "before" else "value = 4\n"
    assert source_at_stage(source_capture(), stage)["policy.py"] == expected


@pytest.mark.parametrize(
    "defect", ["bytes", "authored", "extra-change", "event", "stage"]
)
def test_ambiguous_or_corrupt_stage_bytes_cannot_be_used_as_evidence(defect):
    c = source_capture()
    if defect == "bytes":
        c["direct_source"]["reads"][1]["source"]["policy.py"] = "today's source"
    elif defect == "authored":
        c["direct_source"]["reads"][1]["authored_hashes"]["guides/index.md"] = "wrong"
    elif defect == "extra-change":
        c["direct_source"]["reads"][1]["source"]["other.py"] = "value = 8\n"
        c["direct_source"]["reads"][1]["source_hashes"]["other.py"] = text_hash(
            "value = 8\n"
        )
    elif defect == "event":
        c["events"].append(deepcopy(c["events"][0]))
    with pytest.raises(ValueError):
        source_at_stage(c, "unscheduled" if defect == "stage" else "after-sync")


def test_exact_semantic_edit_restores_page_without_regenerating_provider_content():
    before = "# Policy\n\n## Description\n\nExisting description.\n"
    authored = "Retained authored statement.\n"
    after = before.replace("## Description\n", "## Description\n\n" + authored + "\n")
    edit = {
        "before_sha256": text_hash(before),
        "after_sha256": text_hash(after),
        "semantic_edit": {
            "heading": "Description",
            "kind": "insert-after-heading",
            "preserve_existing_prose": True,
            "text": authored,
            "text_sha256": text_hash(authored),
        },
    }
    assert replay_semantic_insert(before, edit) == after
    edit["after_sha256"] = "today's regenerated page hash"
    with pytest.raises(ValueError):
        replay_semantic_insert(before, edit)


def score_inputs():
    expected = [
        {
            "row_id": f"row-{n}",
            "case_id": f"case-{n % 4}",
            "observation_stage": "after-edit",
            "page_path": "entities/Policy.md",
        }
        for n in range(122)
    ]
    required = [
        {
            "case_id": f"case-{n}",
            "page": "entities/Policy.md",
            "owner": "entities/Policy.md:Policy",
            "eligible_stages": ["after-edit", "after-sync", "after-restart"],
            "operations": ["revise-claim"],
        }
        for n in range(4)
    ]
    return expected, required


def submission(row, label="actionable"):
    capsule = packet(row["row_id"], row["observation_stage"])
    capsule.update(case_id=row["case_id"], page=row["page_path"])
    return {
        "row_id": row["row_id"],
        "capsule": capsule,
        "reviews": [judgment(capsule, label), judgment(capsule, label, "reviewer-b")],
    }


def test_missing_120_reviews_stay_in_122_denominator_and_four_owner_coverage():
    expected, required = score_inputs()
    result = retrospective_score(
        expected, [submission(r) for r in expected[:2]], required
    )
    assert (
        result["actionable"],
        result["unknown"],
        result["denominator"],
        result["covered"],
        result["required"],
    ) == (2, 120, 122, 2, 4)
    assert result["fraction"] == 2 / 122 and not result["retrospective_thresholds_met"]
    assert result["original_independent_actionability"] == "historical-unmeasured"
    assert result["original_path_surfacing"] == {"surfaced": 4, "required": 4}


def test_missing_prose_even_with_source_and_provider_claim_earns_no_credit():
    expected, required = score_inputs()
    r = submission(expected[0])
    r["capsule"]["artifacts"].pop("page.md")
    result = retrospective_score(expected, [r], required)
    assert result["unknown"] == 122 and result["covered"] == 0


def test_repeated_stage_is_retained_and_duplicate_same_stage_is_not_double_credited():
    expected, required = score_inputs()
    expected[1].update(case_id=expected[0]["case_id"], observation_stage="after-sync")
    expected[2].update(case_id=expected[0]["case_id"])
    result = retrospective_score(
        expected, [submission(r) for r in expected[:3]], required
    )
    assert (
        result["actionable"] == 2
        and result["nonactionable"] == 1
        and result["unknown"] == 119
    )
    assert len(result["rows"]) == 122 and result["covered"] == 1


def test_exact_required_owner_action_is_stronger_than_path_surfacing():
    expected, required = score_inputs()
    required[0]["operations"] = ["inspect-pending-mapping"]
    result = retrospective_score(expected, [submission(expected[0])], required)
    assert result["actionable"] == 1 and result["covered"] == 0


def test_duplicate_or_unindexed_submission_is_rejected():
    expected, required = score_inputs()
    r = submission(expected[0])
    with pytest.raises(ValueError):
        retrospective_score(expected, [r, r], required)
    r["row_id"] = "not-indexed"
    with pytest.raises(ValueError):
        retrospective_score(expected, [r], required)


def test_json_pointer_preserves_escaped_paths_and_occurrence_indices():
    assert (
        pointer({"reads": [{"x/y": {"~name": "text"}}]}, "/reads/0/x~1y/~0name")
        == "text"
    )


def test_declared_source_root_prefix_matches_owned_transcript_without_guessing():
    capture = source_capture()
    capture["events"][0]["result"]["path"] = "src/policy.py"
    assert source_at_stage(capture, "after")["policy.py"] == "value = 4\n"
    capture["events"][0]["result"]["path"] = "unowned/policy.py"
    with pytest.raises(ValueError):
        source_at_stage(capture, "after")


def test_authored_input_without_authenticated_stage_prose_cannot_earn_credit():
    expected, required = score_inputs()
    row = submission(expected[0])
    capsule = row["capsule"]
    capsule["artifacts"]["page.md"]["kind"] = "authored-input"
    row["reviews"] = [judgment(capsule), judgment(capsule, role="reviewer-b")]
    result = retrospective_score(expected, [row], required)
    assert result["unknown"] == 122 and result["covered"] == 0
