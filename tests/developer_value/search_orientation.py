"""Test-owned AF12 design checks; source review is not generated/runtime acceptance."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


BUDGETS = {"interactions": 30, "nodes": 40, "lines": 80, "characters": 6000, "depth": 6}
QUALIFICATIONS = {
    "validation": {
        "roots": "CLI validates roots; service validates request before its roots",
        "request": "query/kinds/mode validated; positive limit capped at 100",
        "failures": "validation can raise; diagram order is not execution order",
    },
    "corpus-selection": {
        "selection": "query cannot widen committed source selection",
        "kinds": "requested wiki kinds and ownership eligibility filter pages",
        "guard": "selected-source guard captures snapshots; legacy unguarded path returns early",
        "source-index": "include_source is explicit and requires ranked-v2; snapshot is not indexing",
    },
    "ranking": {
        "current-mode": "ranked and ranked-v2 use search_lexical.rank_pages",
        "legacy-mode": "ranked-v1 uses search_rank.rank_pages; substring is separate",
        "bounds": "page/byte/result bounds apply; ranked-v2 does not imply include_source",
    },
    "results": {
        "publication": "guarded path rechecks captures; unguarded return skips final checks",
        "output": "bounded results return to CLI JSON/text; discovery rendering is optional",
        "answer": "results are candidates, not definitive task answers or runtime proof",
    },
}
REQUIRED_SOURCES = {
    "validation": {
        ("commands/search_cmd.py", "run"),
        ("services/search_service.py", "normalize_search"),
    },
    "corpus-selection": {
        ("services/search_service.py", "search_prevalidated_roots"),
        ("services/search_service.py", "page_records"),
    },
    "ranking": {
        ("services/search_service.py", "search_records"),
        ("services/search_lexical.py", "rank_pages"),
    },
    "results": {
        ("services/search_service.py", "search_prevalidated_roots"),
        ("commands/search_cmd.py", "run"),
    },
}
REQUIRED_SOURCES = {
    stage: {("src/llm_wiki_cli/" + path, name) for path, name in sources}
    for stage, sources in REQUIRED_SOURCES.items()
}


def commitment(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _file(root: Path, path: str) -> Path:
    _require(isinstance(path, str) and bool(path), "relative path required")
    parts = PurePosixPath(path)
    _require(
        not parts.is_absolute()
        and parts.as_posix() == path
        and not ({".", ".."} & set(parts.parts)),
        "path escape or noncanonical path",
    )
    result = root / path
    _require(result.resolve().is_relative_to(root.resolve()), "path escape")
    _require(
        not any(
            (root.joinpath(*parts.parts[:i])).is_symlink()
            for i in range(1, len(parts.parts) + 1)
        ),
        "source symlink",
    )
    return result


def _functions(tree: ast.AST, prefix: str = ""):
    for child in ast.iter_child_nodes(tree):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = prefix + child.name
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield name, child
            yield from _functions(child, name + ".")
        else:
            yield from _functions(child, prefix)


def source_reference(
    root: Path, path: str, qualified_name: str, start_line: int, end_line: int
) -> dict[str, Any]:
    """Construct byte-bound coordinates without importing inspected source."""
    content = _file(root, path).read_bytes()
    matches = [
        node for name, node in _functions(ast.parse(content)) if name == qualified_name
    ]
    _require(len(matches) == 1, "unique AST function identity required")
    node = matches[0]
    first = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
    _require(
        type(start_line) is int
        and type(end_line) is int
        and first <= start_line <= end_line <= (node.end_lineno or 0),
        "source reference outside function",
    )
    quote = b"".join(
        content.splitlines(keepends=True)[start_line - 1 : end_line]
    ).decode("utf-8")
    return {
        "path": path,
        "whole_file_sha256": hashlib.sha256(content).hexdigest(),
        "qualified_name": qualified_name,
        "function_start_line": first,
        "function_end_line": node.end_lineno,
        "start_line": start_line,
        "end_line": end_line,
        "slice_sha256": hashlib.sha256(quote.encode()).hexdigest(),
        "quote": quote,
    }


def _reference(root: Path, ref: dict, selected: dict) -> None:
    _require(
        isinstance(ref, dict) and ref.get("path") in selected,
        "excluded or unselected source reference",
    )
    expected = source_reference(
        root, ref["path"], ref["qualified_name"], ref["start_line"], ref["end_line"]
    )
    _require(
        ref == expected and selected[ref["path"]] == ref["whole_file_sha256"],
        "source reference hash or identity drift",
    )


def _coordinate(ref: dict) -> dict:
    return {"file": ref["path"], "symbol": ref["qualified_name"]}


def _calls_in_body(node: ast.AST):
    for child in ast.iter_child_nodes(node):
        if isinstance(
            child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            continue
        if isinstance(child, ast.Call):
            yield child
        yield from _calls_in_body(child)


def _scope_calls(node: ast.FunctionDef | ast.AsyncFunctionDef):
    # Defaults, decorators and annotations run outside the owning function body.
    for statement in node.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        yield from _calls_in_body(statement)


def _binding(root: Path, binding: dict) -> dict:
    _require(binding["root"] == str(root.resolve()), "root binding drift")
    selection = binding["source_selection"]
    raw = _file(root, selection["path"]).read_bytes()
    _require(
        hashlib.sha256(raw).hexdigest() == selection["sha256"],
        "source-selection hash drift",
    )
    policy = json.loads(raw)
    canonical = {
        "schema_version": policy["schema_version"],
        "include": sorted(policy["include"]),
        "exclude": sorted(policy["exclude"]),
    }
    semantic = (
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    )
    _require(
        selection["identity"]
        == {
            "schema_version": "llm-wiki-source-selection-identity/v1",
            "path": selection["path"],
            "fingerprint": "sha256:" + hashlib.sha256(semantic.encode()).hexdigest(),
        },
        "source-selection identity drift",
    )
    selected = binding["selected_source_hashes"]
    for path, digest in selected.items():

        def under(base):
            return path == base or path.startswith(base + "/")

        _require(
            any(under(base) for base in policy["include"])
            and not any(under(base) for base in policy["exclude"]),
            "excluded selected source",
        )
        _require(
            hashlib.sha256(_file(root, path).read_bytes()).hexdigest() == digest,
            "selected source hash drift",
        )
    _require(bool(binding["provider_hashes"]), "provider binding required")
    for path, digest in binding["provider_hashes"].items():
        _require(
            hashlib.sha256(_file(root, path).read_bytes()).hexdigest() == digest,
            "provider hash drift",
        )
    _reference(root, binding["entrypoint"], selected)
    _require(
        _coordinate(binding["entrypoint"])
        == {"file": "src/llm_wiki_cli/commands/search_cmd.py", "symbol": "run"},
        "entrypoint drift",
    )
    return selected


def _trace(root: Path, trace: dict, binding: dict, selected: dict) -> dict:
    _require(trace["binding_sha256"] == commitment(binding), "trace binding drift")
    counts = trace["counts"]
    _require(
        set(counts) == {"captured", "displayed", "omitted", "unresolved", "external"},
        "unknown counts hidden",
    )
    historical = trace["historical_baseline"]
    if historical is not None:
        artifact = historical["artifact"]
        _require(
            historical["status"] == "historical-only", "historical/current conflation"
        )
        _require(
            hashlib.sha256(_file(root, artifact["path"]).read_bytes()).hexdigest()
            == artifact["sha256"],
            "historical artifact drift",
        )
        _require(
            all(
                type(historical[k]) is int and historical[k] >= 0
                for k in ("captured", "displayed")
            ),
            "invalid historical counts",
        )
        _require(
            historical["displayed"] <= historical["captured"],
            "invalid historical counts",
        )
    if trace["status"] in {"timed-out", "unavailable"}:
        _require(
            all(value is None for value in counts.values())
            and trace["traversal"] is None,
            "unavailable current counts must be null",
        )
        _require(
            trace["original_flow"] is None
            and trace["original_rendered"] is None
            and not trace["occurrences"]
            and not trace["displayed_occurrence_ids"],
            "unavailable graph must not borrow evidence",
        )
        _require(bool(trace.get("failure_reason")), "unavailable reason required")
        return {}
    _require(trace["status"] == "captured", "whole-provider capture status required")
    _require(
        trace.get("scope") == "whole-selected-provider",
        "isolated AST prototype is not whole-provider evidence",
    )
    occurrences = trace["occurrences"]
    ids = [item["occurrence_id"] for item in occurrences]
    _require(len(set(ids)) == len(ids), "duplicate occurrence")
    displayed = trace["displayed_occurrence_ids"]
    _require(
        len(set(displayed)) == len(displayed) and set(displayed) <= set(ids),
        "fabricated displayed occurrence",
    )
    expected = {
        "captured": len(ids),
        "displayed": len(displayed),
        "omitted": len(ids) - len(displayed),
        "unresolved": sum(o["kind"] == "unresolved" for o in occurrences),
        "external": sum(o["kind"] == "external" for o in occurrences),
    }
    _require(
        counts == expected and all(type(v) is int for v in counts.values()),
        "exact presentation/unknown counts required",
    )
    flow = trace["original_flow"]
    _require(
        len(occurrences) == sum(step["depth"] > 0 for step in flow["steps"]),
        "original flow occurrences omitted",
    )
    indexes = []
    for item in occurrences:
        _reference(root, item["from"], selected)
        step = flow["steps"][item["step_index"] - 1]
        indexes.append(item["step_index"])
        edge = step["edge"]
        _require(
            item["kind"] in {"internal", "external", "unresolved"}
            and step["kind"] == item["kind"]
            and edge["from"] == _coordinate(item["from"])
            and edge["to"] == item["to"],
            "original from/to/kind occurrence drift",
        )
        raw_callsite = edge.get("callsite")
        if raw_callsite is None:
            _require(
                item["callsite_status"] == "unavailable"
                and item["call_line"] is None
                and item["call_column"] is None,
                "unavailable callsite metadata must remain explicit",
            )
        else:
            _require(
                item["callsite_status"] == "captured"
                and raw_callsite["line"] == item["call_line"]
                and raw_callsite["column"] == item["call_column"],
                "original callsite metadata drift",
            )
            node = next(
                n
                for name, n in _functions(
                    ast.parse(_file(root, item["from"]["path"]).read_bytes())
                )
                if name == item["from"]["qualified_name"]
            )
            calls = [
                n
                for n in _scope_calls(node)
                if n.lineno == item["call_line"]
                and n.col_offset == item["call_column"]
                and ast.unparse(n.func) == item["callee_text"]
            ]
            _require(
                len(calls) == 1
                and item["from"]["start_line"]
                <= item["call_line"]
                <= item["from"]["end_line"],
                "original AST call occurrence required",
            )
    _require(len(set(indexes)) == len(indexes), "duplicate original step")
    traversal = trace["traversal"]
    raw_coverage = flow["coverage"]["steps"]
    _require(
        traversal
        == {
            "total": raw_coverage["observed"],
            "returned": raw_coverage["emitted"],
            "omitted": raw_coverage["omitted"],
            "truncated": raw_coverage["truncated"],
            "depth_limit": raw_coverage["depth_limit"],
        },
        "original traversal evidence drift",
    )
    _require(
        all(
            type(traversal[k]) is int and traversal[k] >= 0
            for k in ("total", "returned", "omitted")
        )
        and type(traversal["truncated"]) is bool
        and traversal["returned"] == len(flow["steps"])
        and traversal["total"] == traversal["returned"] + traversal["omitted"]
        and traversal["truncated"] == (traversal["omitted"] > 0)
        and traversal["depth_limit"] == 6,
        "exact traversal totals required",
    )
    rendered = trace["original_rendered"]
    _require(
        isinstance(rendered, str)
        and len(displayed) <= 30
        and len(rendered.splitlines()) <= 80
        and len(rendered) <= 6000,
        "render budget exceeded",
    )
    arrows = re.findall(
        r"^\s*\S+?\s*(?:-->>|->>|-->|->|--x|-x)\s*\S+?\s*:", rendered, re.MULTILINE
    )
    _require(len(arrows) == len(displayed), "rendered arrow/display count drift")
    _require(
        len(
            {
                commitment(o[key])
                for o in occurrences
                if o["occurrence_id"] in displayed
                for key in ("from", "to")
            }
        )
        <= 40,
        "node budget exceeded",
    )
    return dict(zip(ids, occurrences))


def validate_design(
    manifest: dict,
    *,
    root: Path,
    binding: dict,
    trace: dict,
    trace_sha256: str,
    source_review: dict,
) -> dict:
    """Check structure and bound provenance, not independently prove source semantics.

    The controller must pin original capture bytes before submitting a design and
    supply separately obtained source-review metadata. Neither comes from the
    manifest under review. This check does not replace the independent reviewer.
    """
    try:
        _require(
            manifest["schema_version"] == "af12-source-orientation-design/v1"
            and manifest["status"] == "proposed-af13"
            and manifest["approach"] == "A2",
            "proposed AF13 design status required",
        )
        _require(manifest["binding"] == binding, "design binding drift")
        _require(
            manifest["budgets"] == BUDGETS
            and all(type(v) is int for v in manifest["budgets"].values()),
            "fixed budgets required",
        )
        selected = _binding(root, binding)
        _require(
            manifest["trace_sha256"] == commitment(trace) == trace_sha256,
            "original trace evidence changed",
        )
        _require(
            manifest["source_review_sha256"] == commitment(source_review),
            "source-review receipt drift",
        )
        _require(
            source_review["status"] == "source-reviewed-design"
            and source_review["runtime_acceptance"] == "unestablished",
            "independent source-review metadata required",
        )
        _require(
            isinstance(source_review["reviewer_id"], str)
            and bool(source_review["reviewer_id"])
            and isinstance(source_review["author_id"], str)
            and bool(source_review["author_id"])
            and source_review["reviewer_id"] != source_review["author_id"],
            "independent source reviewer required",
        )
        _require(
            source_review["source_selection_identity"]
            == binding["source_selection"]["identity"]
            and source_review["selected_source_hashes"] == selected
            and source_review["stage_ids"] == list(QUALIFICATIONS),
            "source-review scope drift",
        )
        review_artifact = source_review["artifact"]
        _require(
            hashlib.sha256(
                _file(root, review_artifact["path"]).read_bytes()
            ).hexdigest()
            == review_artifact["sha256"],
            "source-review artifact drift",
        )
        occurrences = _trace(root, trace, binding, selected)
        for field in ("original_flow", "original_rendered"):
            expected = None if trace[field] is None else commitment(trace[field])
            _require(
                manifest[field + "_sha256"] == expected,
                "original flow/render evidence changed",
            )
        _require(
            manifest["current_counts"] == trace["counts"],
            "current/historical counts conflated",
        )
        stages = manifest["stages"]
        _require(
            [s["id"] for s in stages] == list(QUALIFICATIONS),
            "four required stages in reading order",
        )
        for stage in stages:
            _require(
                stage["evidence"] == "source-reviewed"
                and stage["runtime"] == "unestablished",
                "source review is not runtime proof",
            )
            _require(
                stage["qualifications"] == QUALIFICATIONS[stage["id"]],
                "required mode/guard/output qualification",
            )
            for ref in stage["refs"]:
                _reference(root, ref, selected)
            identities = {
                (r["path"], r["qualified_name"])
                for r in stage["refs"]
                if r["start_line"] == r["function_start_line"]
                and r["end_line"] == r["function_end_line"]
            }
            _require(
                REQUIRED_SOURCES[stage["id"]] <= identities,
                "stage exact full owning-function source identities required",
            )
        _require(bool(manifest["navigation"]), "reading navigation required")
        for edge in manifest["navigation"]:
            _reference(root, edge["from_ref"], selected)
            _reference(root, edge["to_ref"], selected)
            _require(edge["runtime"] == "unestablished", "runtime edge claim forbidden")
            if edge["evidence"] == "source-reviewed":
                _require(
                    edge["occurrence_id"] is None,
                    "source navigation is not captured evidence",
                )
            else:
                _require(
                    edge["evidence"] == "captured-static"
                    and edge["occurrence_id"] in occurrences,
                    "fabricated captured arrow",
                )
                original = occurrences[edge["occurrence_id"]]
                _require(
                    original["from"] == edge["from_ref"]
                    and original["to"] == _coordinate(edge["to_ref"])
                    and original["kind"] == edge["kind"],
                    "captured arrow from/to/kind drift",
                )
        _require(
            manifest["generated_trace_stage_coverage"] == "mitigated/not-met"
            and manifest["source_grounded_orientation_coverage"]
            == "source-reviewed-design"
            and manifest["runtime_acceptance"] == "unestablished",
            "A2 cannot pass generated/runtime acceptance",
        )
    except (KeyError, TypeError, IndexError, AttributeError) as exc:
        raise ValueError("malformed design or evidence") from exc
    return {
        "valid_design": True,
        "status": "proposed-af13",
        "generated_trace_stage_coverage": "mitigated/not-met",
        "runtime_acceptance": "unestablished",
        "structural_validation_only": True,
    }
