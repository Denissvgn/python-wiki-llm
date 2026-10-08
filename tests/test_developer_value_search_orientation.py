"""Owned design negatives, separate from the independently reviewed real source."""

from copy import deepcopy
import ast
import hashlib
import json

import pytest

from tests.developer_value.search_orientation import (
    BUDGETS,
    QUALIFICATIONS,
    REQUIRED_SOURCES,
    commitment,
    source_reference,
    validate_design as _validate_design,
)


def packet(tmp_path):
    source = "src/llm_wiki_cli/"
    texts = {
        source
        + "commands/search_cmd.py": "def run():\n    normalize_search()\n    def deferred():\n        normalize_search()\n    return 1\n",
        source
        + "services/search_service.py": "def normalize_search():\n    return 1\ndef search_prevalidated_roots():\n    return 2\ndef page_records():\n    return 3\ndef search_records():\n    return 4\n",
        source + "services/search_lexical.py": "def rank_pages():\n    return []\n",
    }
    for path, text in texts.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    policy = {
        "schema_version": "llm-wiki-source-selection/v1",
        "include": ["src/llm_wiki_cli"],
        "exclude": [],
    }
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps(policy))
    semantic = (
        json.dumps(policy, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        + "\n"
    )
    refs = {}
    for stage_sources in REQUIRED_SOURCES.values():
        for path, symbol in stage_sources:
            lines = texts[path].splitlines()
            first = next(
                i
                for i, line in enumerate(lines, 1)
                if line.startswith("def " + symbol + "(")
            )
            last = next(
                (
                    i - 1
                    for i, line in enumerate(lines, 1)
                    if i > first and line.startswith("def ")
                ),
                len(lines),
            )
            refs[path, symbol] = source_reference(tmp_path, path, symbol, first, last)
    hashes = {
        path: hashlib.sha256(text.encode()).hexdigest() for path, text in texts.items()
    }
    binding = {
        "root": str(tmp_path.resolve()),
        "entrypoint": refs[source + "commands/search_cmd.py", "run"],
        "source_selection": {
            "path": "selection.json",
            "sha256": hashlib.sha256(selection.read_bytes()).hexdigest(),
            "identity": {
                "schema_version": "llm-wiki-source-selection-identity/v1",
                "path": "selection.json",
                "fingerprint": "sha256:"
                + hashlib.sha256(semantic.encode()).hexdigest(),
            },
        },
        "selected_source_hashes": hashes,
        "provider_hashes": dict(hashes),
    }
    caller = binding["entrypoint"]
    target = refs[source + "services/search_service.py", "normalize_search"]
    target_coordinate = {"file": target["path"], "symbol": target["qualified_name"]}
    original_edge = {
        "from": {"file": caller["path"], "symbol": caller["qualified_name"]},
        "to": target_coordinate,
        "callsite": {"line": 2, "column": 4},
    }
    trace = {
        "status": "captured",
        "scope": "whole-selected-provider",
        "binding_sha256": commitment(binding),
        "original_flow": {
            "steps": [
                {"depth": 0},
                {"depth": 1, "kind": "internal", "edge": original_edge},
            ],
            "coverage": {
                "steps": {
                    "observed": 2,
                    "emitted": 2,
                    "omitted": 0,
                    "truncated": False,
                    "depth_limit": 6,
                }
            },
        },
        "original_rendered": "sequenceDiagram\n    A->>B: normalize_search\n",
        "occurrences": [
            {
                "occurrence_id": "step-2",
                "step_index": 2,
                "from": caller,
                "to": target_coordinate,
                "kind": "internal",
                "call_line": 2,
                "call_column": 4,
                "callsite_status": "captured",
                "callee_text": "normalize_search",
            }
        ],
        "displayed_occurrence_ids": ["step-2"],
        "counts": {
            "captured": 1,
            "displayed": 1,
            "omitted": 0,
            "unresolved": 0,
            "external": 0,
        },
        "traversal": {
            "total": 2,
            "returned": 2,
            "omitted": 0,
            "truncated": False,
            "depth_limit": 6,
        },
        "historical_baseline": None,
    }
    manifest = {
        "schema_version": "af12-source-orientation-design/v1",
        "status": "proposed-af13",
        "approach": "A2",
        "binding": deepcopy(binding),
        "budgets": dict(BUDGETS),
        "stages": [
            {
                "id": stage,
                "refs": [refs[path, symbol] for path, symbol in sorted(required)],
                "qualifications": deepcopy(QUALIFICATIONS[stage]),
                "evidence": "source-reviewed",
                "runtime": "unestablished",
            }
            for stage, required in REQUIRED_SOURCES.items()
        ],
        "navigation": [
            {
                "from_ref": caller,
                "to_ref": target,
                "evidence": "captured-static",
                "runtime": "unestablished",
                "occurrence_id": "step-2",
                "kind": "internal",
            }
        ],
        "generated_trace_stage_coverage": "mitigated/not-met",
        "source_grounded_orientation_coverage": "source-reviewed-design",
        "runtime_acceptance": "unestablished",
    }
    freeze(manifest, trace)
    review = review_receipt(tmp_path, binding)
    manifest["source_review_sha256"] = commitment(review)
    (tmp_path / "source-review-receipt.json").write_text(json.dumps(review))
    pin_trace(tmp_path, trace)
    return manifest, binding, trace


def review_receipt(root, binding):
    # This fixture tests provenance structure; it is not a semantic source oracle.
    (root / "review.json").write_text("owned independent review fixture")
    return {
        "status": "source-reviewed-design",
        "reviewer_id": "independent-reviewer",
        "author_id": "design-author",
        "source_selection_identity": deepcopy(binding["source_selection"]["identity"]),
        "selected_source_hashes": deepcopy(binding["selected_source_hashes"]),
        "stage_ids": list(QUALIFICATIONS),
        "runtime_acceptance": "unestablished",
        "artifact": {
            "path": "review.json",
            "sha256": hashlib.sha256((root / "review.json").read_bytes()).hexdigest(),
        },
    }


def pin_trace(root, trace):
    (root / "origin-trace.sha256").write_text(commitment(trace))


def validate_design(manifest, *, root, binding, trace):
    return _validate_design(
        manifest,
        root=root,
        binding=binding,
        trace=trace,
        trace_sha256=(root / "origin-trace.sha256").read_text(),
        source_review=json.loads((root / "source-review-receipt.json").read_text()),
    )


def freeze(manifest, trace):
    manifest["trace_sha256"] = commitment(trace)
    manifest["current_counts"] = deepcopy(trace["counts"])
    for field in ("original_flow", "original_rendered"):
        manifest[field + "_sha256"] = (
            None if trace[field] is None else commitment(trace[field])
        )


def test_design_is_only_proposed_and_does_not_mutate_evidence(tmp_path):
    manifest, binding, trace = packet(tmp_path)
    before = deepcopy((manifest, binding, trace))
    result = validate_design(manifest, root=tmp_path, binding=binding, trace=trace)
    assert result == {
        "valid_design": True,
        "status": "proposed-af13",
        "generated_trace_stage_coverage": "mitigated/not-met",
        "runtime_acceptance": "unestablished",
        "structural_validation_only": True,
    }
    assert (manifest, binding, trace) == before


@pytest.mark.parametrize(
    "change",
    [
        "hash",
        "selection",
        "provider",
        "entry",
        "binding",
        "excluded",
        "escape",
        "outside",
        "name-only",
        "quote",
    ],
)
def test_source_and_binding_drift_is_rejected(tmp_path, change):
    manifest, binding, trace = packet(tmp_path)
    ref = manifest["stages"][0]["refs"][0]
    if change in {"hash", "provider"}:
        (tmp_path / ref["path"]).write_text("def run():\n    return 7\n")
    elif change == "selection":
        (tmp_path / "selection.json").write_text("{}")
    elif change == "entry":
        binding["entrypoint"]["qualified_name"] = "different"
    elif change == "binding":
        manifest["binding"]["root"] = "/other"
    elif change == "excluded":
        binding["selected_source_hashes"].pop(ref["path"])
        manifest["binding"] = deepcopy(binding)
        trace["binding_sha256"] = commitment(binding)
        freeze(manifest, trace)
    elif change == "escape":
        ref["path"] = "../outside.py"
    elif change == "outside":
        ref["end_line"] = 999
    elif change == "name-only":
        ref.pop("qualified_name")
    else:
        ref["quote"] = "unsupported prose"
    with pytest.raises(ValueError):
        validate_design(manifest, root=tmp_path, binding=binding, trace=trace)


@pytest.mark.parametrize(
    "change",
    [
        "missing-stage",
        "duplicate-stage",
        "missing-qualification",
        "mode",
        "runtime",
        "generated-pass",
        "delivered",
        "name-group",
        "budget",
    ],
)
def test_stage_qualifications_and_acceptance_cannot_be_weakened(tmp_path, change):
    manifest, binding, trace = packet(tmp_path)
    if change == "missing-stage":
        manifest["stages"].pop()
    elif change == "duplicate-stage":
        manifest["stages"][1] = deepcopy(manifest["stages"][0])
    elif change == "missing-qualification":
        manifest["stages"][1]["qualifications"].pop("guard")
    elif change == "mode":
        manifest["stages"][2]["qualifications"]["current-mode"] = (
            "default uses search_rank.py"
        )
    elif change == "runtime":
        manifest["navigation"][0]["runtime"] = "established"
    elif change == "generated-pass":
        manifest["generated_trace_stage_coverage"] = "passed"
    elif change == "delivered":
        manifest["status"] = "delivered"
    elif change == "name-group":
        manifest["stages"][0]["refs"] = [{"symbol": "run"}]
    else:
        manifest["budgets"]["interactions"] = 31
    with pytest.raises(ValueError):
        validate_design(manifest, root=tmp_path, binding=binding, trace=trace)


@pytest.mark.parametrize(
    "change",
    [
        "arrow",
        "kind",
        "endpoint",
        "callsite",
        "nested-call",
        "missing-callsite",
        "unknown",
        "omission",
        "traversal",
        "raw",
        "render",
        "prototype",
        "over-lines",
        "hidden-arrow",
    ],
)
def test_original_occurrences_and_separate_exact_counts_are_required(tmp_path, change):
    manifest, binding, trace = packet(tmp_path)
    item = trace["occurrences"][0]
    if change == "arrow":
        manifest["navigation"][0]["occurrence_id"] = "invented"
    elif change == "kind":
        manifest["navigation"][0]["kind"] = "external"
    elif change == "endpoint":
        item["to"] = {"file": "other.py", "symbol": "normalize_search"}
    elif change == "callsite":
        item["call_column"] = 5
    elif change == "nested-call":
        item["call_line"], item["call_column"] = 4, 8
        trace["original_flow"]["steps"][1]["edge"]["callsite"] = {
            "line": 4,
            "column": 8,
        }
    elif change == "missing-callsite":
        trace["original_flow"]["steps"][1]["edge"].pop("callsite")
    elif change == "unknown":
        trace["counts"].pop("unresolved")
    elif change == "omission":
        trace["counts"]["omitted"] = 10
    elif change == "traversal":
        trace["traversal"]["omitted"] = 3
    elif change == "raw":
        trace["original_flow"]["steps"].pop()
    elif change == "render":
        trace["original_rendered"] = "changed"
    elif change == "prototype":
        trace["scope"] = "isolated-AST"
    elif change == "over-lines":
        trace["original_rendered"] = "line\n" * 81
    else:
        trace["original_rendered"] += "    B->>C: invented\n"
    if change != "render":
        freeze(manifest, trace)
    with pytest.raises(ValueError):
        validate_design(manifest, root=tmp_path, binding=binding, trace=trace)


def unavailable(manifest, trace, tmp_path):
    (tmp_path / "historical.md").write_text("30 of 114 historical interactions")
    trace.update(
        status="timed-out",
        original_flow=None,
        original_rendered=None,
        occurrences=[],
        displayed_occurrence_ids=[],
        traversal=None,
        failure_reason="whole selected inventory timed out",
        counts=dict.fromkeys(trace["counts"]),
        historical_baseline={
            "status": "historical-only",
            "captured": 114,
            "displayed": 30,
            "artifact": {
                "path": "historical.md",
                "sha256": hashlib.sha256(
                    (tmp_path / "historical.md").read_bytes()
                ).hexdigest(),
            },
        },
    )
    manifest["navigation"][0].update(evidence="source-reviewed", occurrence_id=None)
    freeze(manifest, trace)
    pin_trace(tmp_path, trace)


def test_unavailable_graph_has_null_current_counts_and_distinct_saved_baseline(
    tmp_path,
):
    manifest, binding, trace = packet(tmp_path)
    unavailable(manifest, trace, tmp_path)
    assert validate_design(manifest, root=tmp_path, binding=binding, trace=trace)[
        "valid_design"
    ]
    assert trace["counts"]["captured"] is None
    assert trace["historical_baseline"]["captured"] == 114


@pytest.mark.parametrize(
    "change", ["current114", "historic-current", "empty-zero", "reason", "saved-graph"]
)
def test_timeout_cannot_become_favorable_current_proof(tmp_path, change):
    manifest, binding, trace = packet(tmp_path)
    unavailable(manifest, trace, tmp_path)
    if change == "current114":
        trace["counts"]["captured"] = 114
    elif change == "historic-current":
        trace["historical_baseline"]["status"] = "current"
    elif change == "empty-zero":
        trace["counts"] = dict.fromkeys(trace["counts"], 0)
    elif change == "reason":
        trace["failure_reason"] = ""
    else:
        trace["original_flow"] = {"steps": []}
    freeze(manifest, trace)
    with pytest.raises(ValueError):
        validate_design(manifest, root=tmp_path, binding=binding, trace=trace)


def test_unavailable_callsite_is_disclosed_without_invented_coordinates(tmp_path):
    manifest, binding, trace = packet(tmp_path)
    trace["original_flow"]["steps"][1]["edge"].pop("callsite")
    trace["occurrences"][0].update(
        callsite_status="unavailable", call_line=None, call_column=None
    )
    freeze(manifest, trace)
    pin_trace(tmp_path, trace)
    assert validate_design(manifest, root=tmp_path, binding=binding, trace=trace)[
        "valid_design"
    ]


def test_recommitted_policy_still_cannot_include_excluded_source(tmp_path):
    manifest, binding, trace = packet(tmp_path)
    policy = json.loads((tmp_path / "selection.json").read_text())
    policy["exclude"] = ["src/llm_wiki_cli/services"]
    raw = json.dumps(policy)
    (tmp_path / "selection.json").write_text(raw)
    binding["source_selection"]["sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    canonical = (
        json.dumps(policy, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        + "\n"
    )
    binding["source_selection"]["identity"]["fingerprint"] = (
        "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
    )
    manifest["binding"] = deepcopy(binding)
    trace["binding_sha256"] = commitment(binding)
    freeze(manifest, trace)
    with pytest.raises(ValueError, match="excluded"):
        validate_design(manifest, root=tmp_path, binding=binding, trace=trace)


def test_same_named_methods_require_qualified_ast_identity(tmp_path):
    (tmp_path / "methods.py").write_text(
        "class One:\n    def run(self):\n        return 1\nclass Two:\n    def run(self):\n        return 2\n"
    )
    assert (
        source_reference(tmp_path, "methods.py", "One.run", 2, 3)["qualified_name"]
        == "One.run"
    )
    with pytest.raises(ValueError, match="unique AST"):
        source_reference(tmp_path, "methods.py", "run", 2, 3)


def test_decorators_are_part_of_source_identity_without_runtime_target_claim(tmp_path):
    (tmp_path / "decorated.py").write_text("@wrapper\ndef run():\n    return 1\n")
    ref = source_reference(tmp_path, "decorated.py", "run", 1, 3)
    assert ref["function_start_line"] == 1 and ref["quote"].startswith("@wrapper\n")


def refresh_provenance(root, manifest, binding, trace):
    """Pin a newly constructed owned fixture before asking its structural gate."""
    manifest["binding"] = deepcopy(binding)
    trace["binding_sha256"] = commitment(binding)
    review = review_receipt(root, binding)
    manifest["source_review_sha256"] = commitment(review)
    (root / "source-review-receipt.json").write_text(json.dumps(review))
    freeze(manifest, trace)
    pin_trace(root, trace)


def test_bare_required_source_path_cannot_replace_exact_project_path(tmp_path):
    manifest, binding, trace = packet(tmp_path)
    path = "src/llm_wiki_cli/services/search_service.py"
    bare_path = "services/search_service.py"
    (tmp_path / bare_path).parent.mkdir()
    (tmp_path / bare_path).write_bytes((tmp_path / path).read_bytes())
    binding["selected_source_hashes"][bare_path] = binding["selected_source_hashes"][
        path
    ]
    policy = json.loads((tmp_path / "selection.json").read_text())
    policy["include"].append("services")
    raw = json.dumps(policy)
    (tmp_path / "selection.json").write_text(raw)
    binding["source_selection"]["sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    canonical = {**policy, "include": sorted(policy["include"])}
    semantic = json.dumps(canonical, sort_keys=True, separators=(",", ":")) + "\n"
    binding["source_selection"]["identity"]["fingerprint"] = (
        "sha256:" + hashlib.sha256(semantic.encode()).hexdigest()
    )
    for stage in manifest["stages"]:
        stage["refs"] = [
            source_reference(
                tmp_path,
                bare_path,
                ref["qualified_name"],
                ref["start_line"],
                ref["end_line"],
            )
            if ref["path"] == path
            else ref
            for ref in stage["refs"]
        ]
    refresh_provenance(tmp_path, manifest, binding, trace)
    with pytest.raises(ValueError, match="exact full owning-function"):
        validate_design(manifest, root=tmp_path, binding=binding, trace=trace)


def test_final_returns_cannot_replace_required_full_owning_function_refs(tmp_path):
    manifest, binding, trace = packet(tmp_path)
    for stage in manifest["stages"]:
        stage["refs"] = [
            source_reference(
                tmp_path,
                ref["path"],
                ref["qualified_name"],
                ref["function_end_line"],
                ref["function_end_line"],
            )
            for ref in stage["refs"]
        ]
    with pytest.raises(ValueError, match="exact full owning-function"):
        validate_design(manifest, root=tmp_path, binding=binding, trace=trace)


@pytest.mark.parametrize(
    "declaration",
    [
        "@wrapper(normalize_search())\ndef run():\n    return 1\n",
        "def run(value=normalize_search()):\n    return 1\n",
    ],
)
def test_decorator_and_default_calls_are_not_owned_by_function_body(
    tmp_path, declaration
):
    manifest, binding, trace = packet(tmp_path)
    path = "src/llm_wiki_cli/commands/search_cmd.py"
    (tmp_path / path).write_text(declaration)
    caller = source_reference(tmp_path, path, "run", 1, len(declaration.splitlines()))
    binding["entrypoint"] = caller
    binding["selected_source_hashes"][path] = caller["whole_file_sha256"]
    binding["provider_hashes"][path] = caller["whole_file_sha256"]
    for stage in manifest["stages"]:
        stage["refs"] = [
            caller if ref["path"] == path else ref for ref in stage["refs"]
        ]
    manifest["navigation"][0]["from_ref"] = caller
    call = next(
        node
        for node in ast.walk(ast.parse(declaration))
        if isinstance(node, ast.Call) and ast.unparse(node.func) == "normalize_search"
    )
    trace["occurrences"][0].update(
        {"from": caller, "call_line": call.lineno, "call_column": call.col_offset}
    )
    trace["original_flow"]["steps"][1]["edge"]["callsite"] = {
        "line": call.lineno,
        "column": call.col_offset,
    }
    refresh_provenance(tmp_path, manifest, binding, trace)
    with pytest.raises(ValueError, match="original AST call occurrence"):
        validate_design(manifest, root=tmp_path, binding=binding, trace=trace)


def test_same_count_fabricated_diagram_cannot_recommit_original_trace(tmp_path):
    manifest, binding, trace = packet(tmp_path)
    trace["original_rendered"] = (
        "sequenceDiagram\n    Invented->>Target: fabricated_call\n"
    )
    freeze(manifest, trace)
    with pytest.raises(ValueError, match="original trace evidence changed"):
        validate_design(manifest, root=tmp_path, binding=binding, trace=trace)


@pytest.mark.parametrize(
    "change", ["same-author", "missing-stage", "hash-scope", "artifact", "runtime"]
)
def test_source_review_requires_independent_bound_metadata(tmp_path, change):
    manifest, binding, trace = packet(tmp_path)
    receipt = json.loads((tmp_path / "source-review-receipt.json").read_text())
    if change == "same-author":
        receipt["reviewer_id"] = receipt["author_id"]
    elif change == "missing-stage":
        receipt["stage_ids"].pop()
    elif change == "hash-scope":
        receipt["selected_source_hashes"] = {}
    elif change == "artifact":
        (tmp_path / "review.json").write_text("different review")
    else:
        receipt["runtime_acceptance"] = "passed"
    (tmp_path / "source-review-receipt.json").write_text(json.dumps(receipt))
    manifest["source_review_sha256"] = commitment(receipt)
    with pytest.raises(ValueError):
        validate_design(manifest, root=tmp_path, binding=binding, trace=trace)


def test_actual_selection_identity_object_is_required(tmp_path):
    manifest, binding, trace = packet(tmp_path)
    binding["source_selection"]["identity"] = binding["source_selection"]["identity"][
        "fingerprint"
    ]
    refresh_provenance(tmp_path, manifest, binding, trace)
    with pytest.raises(ValueError, match="source-selection identity drift"):
        validate_design(manifest, root=tmp_path, binding=binding, trace=trace)


def test_narrow_additional_refs_are_allowed_beside_required_full_refs(tmp_path):
    manifest, binding, trace = packet(tmp_path)
    full = manifest["stages"][0]["refs"][0]
    manifest["stages"][0]["refs"].append(
        source_reference(
            tmp_path,
            full["path"],
            full["qualified_name"],
            full["end_line"],
            full["end_line"],
        )
    )
    assert validate_design(manifest, root=tmp_path, binding=binding, trace=trace)[
        "structural_validation_only"
    ]
