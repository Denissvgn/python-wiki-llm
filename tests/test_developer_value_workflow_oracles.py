"""Independent oracle controls use supplied literals, never product execution."""

from copy import deepcopy

import pytest

from tests.developer_value.workflow_oracles import (
    REQUIRED_GAP_STATES, assert_clip_behavior, assert_source_change,
    assert_read_only, assert_coverage_gap, assert_coverage_preserved,
)

SOURCE = b'''class Window:
    def clip(self, values: list[int], limit: int = 3) -> list[int]:
        return values[:limit] if limit > 0 else []

def public_clip(values):
    return Window().clip(values)
'''
BODY = SOURCE.replace(b"values[:limit]", b"values[max(0, len(values) - limit):]")
DEFAULT = SOURCE.replace(b"limit: int = 3", b"limit: int = 2")
BEFORE = {"default": [0, 1, 2], "limits": {"3": [0, 1, 2], "1": [0], "0": [], "-1": [], "9": [0, 1, 2, 3, 4]}}
LAST = {"default": [2, 3, 4], "limits": {"3": [2, 3, 4], "1": [4], "0": [], "-1": [], "9": [0, 1, 2, 3, 4]}}
CHANGED_DEFAULT = {**deepcopy(BEFORE), "default": [0, 1]}


def gap(state="missing", reason="no-exact-declaration"):
    row = {"requirement_id": "missing", "state": state, "satisfied": False, "reason": reason}
    return {"state": "partial", "coverage": [row], "omissions": [deepcopy(row)]}


@pytest.mark.parametrize("observations,change", [(BEFORE, "before"), (LAST, "body"), (CHANGED_DEFAULT, "default")])
def test_declared_behavior_controls(observations, change):
    assert_clip_behavior(observations, change)


@pytest.mark.parametrize("observations", [
    LAST,
    {**BEFORE, "limits": {"3": [0, 1, 2]}},
    {**deepcopy(BEFORE), "default": [0, True, 2]},
])
def test_wrong_missing_or_noninteger_behavior_is_rejected(observations):
    with pytest.raises(AssertionError):
        assert_clip_behavior(observations, "before")


@pytest.mark.parametrize("after,change", [(BODY, "body"), (DEFAULT, "default")])
def test_exact_admitted_ast_change(after, change):
    assert_source_change(SOURCE, after, change)


@pytest.mark.parametrize("after,change", [
    (BODY.replace(b"= 3", b"= 2"), "body"),
    (BODY.replace(b"return Window().clip(values)", b"return []"), "body"),
    (SOURCE + b"\n# new comment\n", "body"),
    (BODY.replace(b"= 3", b"= 2"), "default"),
])
def test_signature_unrelated_or_wrong_kind_ast_drift_is_rejected(after, change):
    with pytest.raises(AssertionError):
        assert_source_change(SOURCE, after, change)


@pytest.mark.parametrize("before,after,allowed", [
    ({"source.py": b"bytes"}, {"source.py": b"bytes"}, ()),
    ({"source.py": b"old"}, {"source.py": b"new"}, ("source.py",)),
])
def test_exact_artifacts_or_explicitly_authorized_change(before, after, allowed):
    assert_read_only(before, after, allowed_changes=allowed)


@pytest.mark.parametrize("before,after", [({}, {"source.py": b"new"}), ({"source.py": b"old"}, {})])
def test_unapproved_artifact_creation_or_deletion_is_rejected(before, after):
    with pytest.raises(AssertionError):
        assert_read_only(before, after)


def test_missing_control_requires_exact_missing_gap():
    assert_coverage_gap(gap(), "missing", states=REQUIRED_GAP_STATES["missing"])


def test_bounded_omission_can_be_an_honest_gap():
    assert_coverage_gap(gap("omitted", "read-round-budget"), "missing", states=("omitted",))


def test_bounded_omission_cannot_prove_absence():
    with pytest.raises(AssertionError):
        assert_coverage_gap(gap("omitted", "read-round-budget"), "missing", states=REQUIRED_GAP_STATES["missing"])


def test_required_gap_cannot_be_reported_covered():
    with pytest.raises(AssertionError):
        assert_coverage_gap({**gap(), "state": "covered"}, "missing")


def test_required_gap_identity_cannot_disappear():
    with pytest.raises(AssertionError):
        assert_coverage_gap({**gap(), "coverage": []}, "missing")


def test_known_stale_snapshot_remains_unsatisfied():
    assert_coverage_gap(gap("stale", "captured-native-source-basis-changed"), "missing", states=("stale",))


def test_stale_snapshot_cannot_prove_absence():
    with pytest.raises(AssertionError):
        assert_coverage_gap(gap("stale", "captured-native-source-basis-changed"), "missing", states=REQUIRED_GAP_STATES["missing"])


def canonical_and_expanded():
    canonical = {**gap(), "facts": [], "limitations": ["behavior-not-evaluated"], "result_id": "known-identity"}
    return canonical, {**deepcopy(canonical), "canonical": {"result_id": "known-identity"}}


def test_compact_expansion_preserves_checked_facts_and_gaps():
    canonical, expanded = canonical_and_expanded()
    assert_coverage_preserved(canonical, expanded)


def test_compact_expansion_cannot_erase_gaps():
    canonical, expanded = canonical_and_expanded()
    with pytest.raises(AssertionError):
        assert_coverage_preserved(canonical, {**expanded, "omissions": []})
