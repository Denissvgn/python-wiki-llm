"""Portable provenance controls and real disposable search command boundaries."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from tests.developer_value.search_orientation import (
    BUDGETS, QUALIFICATIONS, REQUIRED_SOURCES, commitment, source_reference,
)
from tests.developer_value.search_route import (
    evidence_notice, module_statement_reference, validate_authored_route,
)


def sha(content):
    return hashlib.sha256(content).hexdigest()


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {"path": name, "sha256": sha(path.read_bytes())}


def tree(root):
    return {
        path.relative_to(root).as_posix(): sha(path.read_bytes())
        for path in root.rglob("*") if path.is_file()
    }


def authored_packet(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Synthetic provenance, explicitly not an independent semantic source oracle."""
    texts = {
        "src/llm_wiki_cli/commands/search_cmd.py": "def run():\n    return 1\n",
        "src/llm_wiki_cli/services/search_service.py": (
            "def normalize_search():\n    return 1\n"
            "def search_prevalidated_roots():\n    return 2\n"
            "def page_records():\n    return 3\n"
            "def search_records():\n    return 4\n"
            "def extra_boundary():\n    return 5\n"
            "class Hidden:\n    SECRET = 1\n    def hidden(self):\n        return 6\n"
        ),
        "src/llm_wiki_cli/services/search_lexical.py": (
            "def rank_pages():\n    return []\n"
            "MAX_NODES = 40\nMAX_LINES = 80\nMAX_CHARACTERS = 6000\n"
        ),
    }
    hashes = {path: write(root, path, text)["sha256"] for path, text in texts.items()}
    refs = {}
    for path, text in texts.items():
        for node in ast.parse(text).body:
            if isinstance(node, ast.FunctionDef):
                assert node.end_lineno is not None
                refs[path, node.name] = source_reference(
                    root, path, node.name, node.lineno, node.end_lineno,
                )
    policy = {
        "schema_version": "llm-wiki-source-selection/v1",
        "include": ["src/llm_wiki_cli"], "exclude": [],
    }
    selection = write(root, "selection.json", json.dumps(policy))
    semantic = json.dumps(policy, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
    binding = {
        "root": str(root.resolve()),
        "entrypoint": refs["src/llm_wiki_cli/commands/search_cmd.py", "run"],
        "source_selection": {
            **selection,
            "identity": {
                "schema_version": "llm-wiki-source-selection-identity/v1",
                "path": "selection.json", "fingerprint": "sha256:" + sha(semantic.encode()),
            },
        },
        "selected_source_hashes": hashes, "provider_hashes": dict(hashes),
    }
    historical = write(root, "docs/llm_wiki/flows/search.json", '{"historical": true}\n')
    trace = {
        "status": "timed-out", "binding_sha256": commitment(binding),
        "counts": {key: None for key in ("captured", "displayed", "omitted", "unresolved", "external")},
        "traversal": None, "original_flow": None, "original_rendered": None,
        "occurrences": [], "displayed_occurrence_ids": [],
        "failure_reason": "owned whole-provider capture timeout",
        "historical_baseline": {
            "status": "historical-only", "artifact": historical, "displayed": 30, "captured": 114,
        },
    }
    source_review = {
        "status": "source-reviewed-design", "reviewer_id": "source-reviewer",
        "author_id": "design-author", "runtime_acceptance": "unestablished",
        "source_selection_identity": deepcopy(binding["source_selection"]["identity"]),
        "selected_source_hashes": deepcopy(hashes), "stage_ids": list(QUALIFICATIONS),
        "artifact": write(root, "receipts/source-review.txt", "independent synthetic source receipt"),
    }
    stages = [
        {
            "id": stage, "refs": [refs[item] for item in sorted(required)],
            "qualifications": deepcopy(QUALIFICATIONS[stage]),
            "evidence": "source-reviewed", "runtime": "unestablished",
        }
        for stage, required in REQUIRED_SOURCES.items()
    ]
    design = {
        "schema_version": "af12-source-orientation-design/v1", "status": "proposed-af13",
        "approach": "A2", "binding": deepcopy(binding), "budgets": dict(BUDGETS),
        "trace_sha256": commitment(trace), "source_review_sha256": commitment(source_review),
        "current_counts": deepcopy(trace["counts"]), "original_flow_sha256": None,
        "original_rendered_sha256": None, "stages": stages,
        "navigation": [{
            "from_ref": stages[0]["refs"][0], "to_ref": stages[0]["refs"][1],
            "runtime": "unestablished", "evidence": "source-reviewed", "occurrence_id": None,
        }],
        "generated_trace_stage_coverage": "mitigated/not-met",
        "source_grounded_orientation_coverage": "source-reviewed-design",
        "runtime_acceptance": "unestablished",
    }
    claims = [
        {
            "id": stage + "." + key, "stage_id": stage, "qualification_key": key,
            "qualification": value, "text": value, "refs": deepcopy(stages[i]["refs"]),
            "evidence": "source-reviewed", "runtime": "unestablished",
        }
        for i, (stage, qualifications) in enumerate(QUALIFICATIONS.items())
        for key, value in qualifications.items()
    ]
    register = {"schema_version": "af13-search-route-claims/v1", "claims": claims}
    links = []
    for (path, symbol), ref in sorted(refs.items()):
        if (path, symbol) not in set().union(*REQUIRED_SOURCES.values()):
            continue
        links.append({
            "href": "../../../" + path + f"#L{ref['start_line']}-L{ref['end_line']}",
            "target": path, "kind": "source", "sha256": hashes[path],
        })
    module = write(root, "docs/llm_wiki/modules/search.md", "# Search module\n")
    links += [
        {"href": "../modules/search.md", "target": module["path"], "kind": "module", "sha256": module["sha256"]},
        {"href": "../flows/search.json", "target": historical["path"], "kind": "raw-flow", "sha256": historical["sha256"]},
    ]
    markdown = (
        "# Search reading route\n\n" + evidence_notice(trace) + "\n\n"
        + "\n".join(claim["text"] for claim in claims) + "\n\n"
        + "\n".join(f"[source {i}]({link['href']})" for i, link in enumerate(links)) + "\n"
    )
    route = {
        "schema_version": "af13-authored-search-route/v1", "status": "source-reviewed-route",
        "author_id": "route-author", "authority": "authored-only",
        "generated_region_policy": "preserve", "runtime_arrows": False,
        "design_sha256": commitment(design),
        "intended_path": "docs/llm_wiki/guides/search-reading-route.md",
        "artifact": write(root, "drafts/search.md", markdown),
        "claim_register": write(root, "drafts/claims.json", json.dumps(register)),
        "links": links, "notice": evidence_notice(trace),
    }
    route_review = {
        "status": "source-reviewed-authored-route", "reviewer_id": "route-reviewer",
        "author_id": route["author_id"], "runtime_acceptance": "unestablished",
        "material_claim_scope": "whole-authored-guide",
        "guide_sha256": route["artifact"]["sha256"],
        "claim_register_sha256": route["claim_register"]["sha256"],
        "source_selection_identity": deepcopy(binding["source_selection"]["identity"]),
        "selected_source_hashes": deepcopy(hashes), "provider_hashes": deepcopy(hashes),
        "stage_ids": list(QUALIFICATIONS),
        "claim_sha256": {claim["id"]: commitment(claim) for claim in claims},
        "artifact": write(root, "receipts/route-review.txt", "independent synthetic claim review"),
    }
    return route, dict(
        root=root, binding=binding, design=design, trace=trace,
        trace_sha256=commitment(trace), source_review=source_review, route_review=route_review,
    )


def repin_register(route, context, register):
    descriptor = write(context["root"], route["claim_register"]["path"], json.dumps(register))
    route["claim_register"] = descriptor
    context["route_review"]["claim_register_sha256"] = descriptor["sha256"]
    context["route_review"]["claim_sha256"] = {
        claim["id"]: commitment(claim) for claim in register["claims"]
    }


def test_authored_route_acceptance_is_readonly_and_separate_from_runtime(tmp_path):
    route, context = authored_packet(tmp_path)
    before = tree(tmp_path), deepcopy((route, context))
    result = validate_authored_route(route, **context)
    assert result == {
        "valid_route": True, "source_grounded_orientation_coverage": "source-reviewed-route",
        "generated_trace_stage_coverage": "mitigated/not-met",
        "runtime_acceptance": "unestablished", "structural_validation_only": True,
    }
    assert (tree(tmp_path), (route, context)) == before
    assert "30 of 114" in route["notice"] and "84 display omissions" in route["notice"]
    assert context["trace"]["counts"]["captured"] is None
    assert context["trace"]["status"] == "timed-out"


@pytest.mark.parametrize("change", [
    "false-path", "wrong-future-path", "missing-link", "link-hash", "guide-hash",
    "register-hash", "provider-drift", "source-drift", "selection-drift", "excluded-selection",
    "false-generated", "false-runtime", "readonly-authority", "generated-policy", "runtime-arrows",
    "missing-stage-review", "same-reviewer", "claim-review-missing", "review-hash", "notice",
    "source-anchor",
])
def test_route_rejects_forged_or_incomplete_provenance(tmp_path, change):
    route, context = authored_packet(tmp_path)
    if change == "false-path":
        route["links"][0]["target"] = "src/does-not-exist.py"
    elif change == "wrong-future-path":
        route["intended_path"] = "drafts/search.md"
    elif change == "missing-link":
        route["links"].pop()
    elif change == "link-hash":
        route["links"][0]["sha256"] = "0" * 64
    elif change == "guide-hash":
        (tmp_path / route["artifact"]["path"]).write_text("different authored guide")
    elif change == "register-hash":
        (tmp_path / route["claim_register"]["path"]).write_text("{}")
    elif change == "provider-drift":
        context["binding"]["provider_hashes"][next(iter(context["binding"]["provider_hashes"]))] = "0" * 64
    elif change == "source-drift":
        path = next(iter(context["binding"]["selected_source_hashes"]))
        (tmp_path / path).write_text("def run():\n    return 'different'\n")
    elif change in {"selection-drift", "excluded-selection"}:
        policy = json.loads((tmp_path / "selection.json").read_text())
        policy["exclude"] = ["src/llm_wiki_cli"] if change == "excluded-selection" else ["excluded"]
        (tmp_path / "selection.json").write_text(json.dumps(policy))
    elif change == "false-generated":
        context["design"]["generated_trace_stage_coverage"] = "passed"
        route["design_sha256"] = commitment(context["design"])
    elif change == "false-runtime":
        context["route_review"]["runtime_acceptance"] = "passed"
    elif change == "readonly-authority":
        route["authority"] = "generated-region-write"
    elif change == "generated-policy":
        route["generated_region_policy"] = "patch"
    elif change == "runtime-arrows":
        route["runtime_arrows"] = True
    elif change == "missing-stage-review":
        context["route_review"]["stage_ids"].pop()
    elif change == "same-reviewer":
        context["route_review"]["reviewer_id"] = route["author_id"]
    elif change == "claim-review-missing":
        context["route_review"]["claim_sha256"].pop(next(iter(context["route_review"]["claim_sha256"])))
    elif change == "review-hash":
        (tmp_path / context["route_review"]["artifact"]["path"]).write_text("drifted review")
    elif change == "source-anchor":
        route["links"][0]["href"] = route["links"][0]["href"].split("#")[0] + "#L999-L1000"
    else:
        route["notice"] = "A fresh trace proves current runtime behavior."
    with pytest.raises(ValueError):
        validate_authored_route(route, **context)


@pytest.mark.parametrize("change", [
    "missing-stage", "missing-qualification", "source-index-implied", "legacy-provider",
    "generated-claim", "runtime-claim", "uncited-claim", "missing-ref", "slice-drift", "claim-text",
])
def test_material_claim_controls_even_with_rebound_synthetic_receipt(tmp_path, change):
    route, context = authored_packet(tmp_path)
    register = json.loads((tmp_path / route["claim_register"]["path"]).read_text())
    claim = register["claims"][0]
    if change == "missing-stage":
        register["claims"] = [c for c in register["claims"] if c["stage_id"] != "results"]
    elif change == "missing-qualification":
        register["claims"].pop()
    elif change == "source-index-implied":
        claim = next(c for c in register["claims"] if c["qualification_key"] == "source-index")
        claim["qualification"] = "ranked-v2 automatically indexes selected source"
    elif change == "legacy-provider":
        claim = next(c for c in register["claims"] if c["qualification_key"] == "current-mode")
        claim["qualification"] = "ranked uses search_rank.rank_pages"
    elif change == "generated-claim":
        claim["evidence"] = "generated-invocation"
    elif change == "runtime-claim":
        claim["runtime"] = "established"
    elif change == "uncited-claim":
        ref = claim["refs"][0]
        claim["refs"][0] = source_reference(
            tmp_path, ref["path"], ref["qualified_name"], ref["end_line"], ref["end_line"],
        )
    elif change == "missing-ref":
        claim["refs"] = []
    elif change == "slice-drift":
        claim["refs"][0]["slice_sha256"] = "0" * 64
    else:
        claim["text"] = "A fabricated material claim absent from the authored guide."
    repin_register(route, context, register)
    with pytest.raises(ValueError):
        validate_authored_route(route, **context)


@pytest.mark.parametrize("extra", [
    "\n\n```mermaid\nsequenceDiagram\nA->>B: runtime\n```\n",
    "\n<!-- llm-wiki:generated:start -->\npatched\n<!-- llm-wiki:generated:end -->\n",
    "\n[unbound citation](../missing.md)\n",
])
def test_authored_guide_cannot_supply_generated_patches_or_unbound_navigation(tmp_path, extra):
    route, context = authored_packet(tmp_path)
    path = tmp_path / route["artifact"]["path"]
    descriptor = write(tmp_path, route["artifact"]["path"], path.read_text() + extra)
    route["artifact"] = descriptor
    context["route_review"]["guide_sha256"] = descriptor["sha256"]
    with pytest.raises(ValueError):
        validate_authored_route(route, **context)


def test_raw_flow_cannot_be_replaced_by_another_hash_bound_page(tmp_path):
    route, context = authored_packet(tmp_path)
    raw_link = next(link for link in route["links"] if link["kind"] == "raw-flow")
    replacement = write(tmp_path, "docs/llm_wiki/flows/unrelated.json", '{"unrelated": true}')
    old_href = raw_link["href"]
    raw_link.update(
        href="../flows/unrelated.json", target=replacement["path"], sha256=replacement["sha256"],
    )
    markdown = (tmp_path / route["artifact"]["path"]).read_text().replace(old_href, raw_link["href"])
    route["artifact"] = write(tmp_path, route["artifact"]["path"], markdown)
    context["route_review"]["guide_sha256"] = route["artifact"]["sha256"]
    with pytest.raises(ValueError, match="original historical artifact"):
        validate_authored_route(route, **context)


def repin_guide(route, context, markdown):
    route["artifact"] = write(context["root"], route["artifact"]["path"], markdown)
    context["route_review"]["guide_sha256"] = route["artifact"]["sha256"]


@pytest.mark.parametrize("fence", [
    "~~~mermaid\nsequenceDiagram\nA->>B: runtime\n~~~",
    " ```mermaid\nsequenceDiagram\nA->>B: runtime\n ```",
    "   ````Mermaid\nsequenceDiagram\nA->>B: runtime\n   ````",
    "  ~~~~mermaid\nsequenceDiagram\nA->>B: runtime\n  ~~~~~",
    "~~~mermaid\nsequenceDiagram\nA->>B: runtime",
])
def test_commonmark_mermaid_fences_cannot_supply_runtime_diagrams(tmp_path, fence):
    route, context = authored_packet(tmp_path)
    markdown = (tmp_path / route["artifact"]["path"]).read_text()
    repin_guide(route, context, markdown + "\n\n" + fence + "\n")
    with pytest.raises(ValueError, match="Mermaid"):
        validate_authored_route(route, **context)


def test_nested_literal_fences_are_not_active_mermaid_diagrams(tmp_path):
    route, context = authored_packet(tmp_path)
    markdown = (tmp_path / route["artifact"]["path"]).read_text()
    literal = "\n\n````text\n```mermaid\nA->>B: literal code\n```\n````\n"
    repin_guide(route, context, markdown + literal)
    assert validate_authored_route(route, **context)["valid_route"] is True


@pytest.mark.parametrize("role_target", ["unselected-python", "selected-python", "other-markdown"])
def test_module_role_cannot_launder_other_source_or_markdown_paths(tmp_path, role_target):
    route, context = authored_packet(tmp_path)
    if role_target == "unselected-python":
        replacement = write(tmp_path, "src/unselected.py", "def hidden():\n    return 0\n")
        href = "../../../src/unselected.py"
    elif role_target == "selected-python":
        name = next(iter(context["binding"]["selected_source_hashes"]))
        replacement = {"path": name, "sha256": context["binding"]["selected_source_hashes"][name]}
        href = "../../../" + name
    else:
        replacement = write(tmp_path, "docs/llm_wiki/guides/other.md", "# Other guide\n")
        href = "other.md"
    link = next(link for link in route["links"] if link["kind"] == "module")
    old_href = link["href"]
    link.update(href=href, target=replacement["path"], sha256=replacement["sha256"])
    markdown = (tmp_path / route["artifact"]["path"]).read_text().replace(old_href, href)
    repin_guide(route, context, markdown)
    with pytest.raises(ValueError, match="canonical module Markdown"):
        validate_authored_route(route, **context)


@pytest.mark.parametrize("hidden_in", ["html-comment", "tilde-fence", "indented-code"])
def test_required_claims_must_appear_in_visible_prose(tmp_path, hidden_in):
    route, context = authored_packet(tmp_path)
    register = json.loads((tmp_path / route["claim_register"]["path"]).read_text())
    claims = "\n".join(claim["text"] for claim in register["claims"])
    if hidden_in == "html-comment":
        hidden = "<!--\n" + claims + "\n-->"
    elif hidden_in == "tilde-fence":
        hidden = "~~~text\n" + claims + "\n~~~"
    else:
        hidden = "\n".join("    " + line for line in claims.splitlines())
    markdown = (tmp_path / route["artifact"]["path"]).read_text().replace(claims, hidden)
    repin_guide(route, context, markdown)
    with pytest.raises(ValueError, match="visible prose"):
        validate_authored_route(route, **context)


def test_source_citations_hidden_in_comments_do_not_supply_visible_navigation(tmp_path):
    route, context = authored_packet(tmp_path)
    markdown = (tmp_path / route["artifact"]["path"]).read_text()
    first = markdown.index("[source 0]")
    repin_guide(route, context, markdown[:first] + "<!--\n" + markdown[first:] + "\n-->")
    with pytest.raises(ValueError, match="bound citations"):
        validate_authored_route(route, **context)


def test_independent_receipt_must_cover_all_material_prose_in_whole_guide(tmp_path):
    route, context = authored_packet(tmp_path)
    context["route_review"]["material_claim_scope"] = "registered-clauses-only"
    with pytest.raises(ValueError, match="independent authored source review"):
        validate_authored_route(route, **context)


def with_optional_navigation(route, context):
    root = context["root"]
    guide = write(root, "docs/llm_wiki/guides/other.md", "# Other guide\n")
    route["links"].extend([
        {"href": "other.md", "target": guide["path"], "kind": "guide", "sha256": guide["sha256"]},
        {
            "href": "../../../selection.json", "kind": "selection",
            "target": context["binding"]["source_selection"]["path"],
            "sha256": context["binding"]["source_selection"]["sha256"],
        },
    ])
    markdown = (root / route["artifact"]["path"]).read_text()
    markdown += "\n" + "\n".join(
        f"[optional {link['kind']}]({link['href']})" for link in route["links"][-2:]
    ) + "\n"
    repin_guide(route, context, markdown)


def test_optional_guide_and_selection_roles_preserve_bound_navigation(tmp_path):
    route, context = authored_packet(tmp_path)
    with_optional_navigation(route, context)
    before = tree(tmp_path)
    assert validate_authored_route(route, **context)["valid_route"] is True
    assert tree(tmp_path) == before


@pytest.mark.parametrize("change", [
    "guide-wrong-directory", "guide-python", "guide-target-escape",
    "selection-substitute", "selection-hash", "selection-target-escape", "unknown-role",
])
def test_optional_roles_reject_escapes_and_artifact_substitutions(tmp_path, change):
    route, context = authored_packet(tmp_path)
    with_optional_navigation(route, context)
    role = "selection" if change.startswith("selection") else "guide"
    link = next(link for link in route["links"] if link["kind"] == role)
    old_href = link["href"]
    if change == "guide-wrong-directory":
        replacement = write(tmp_path, "docs/llm_wiki/modules/other.md", "# Another module\n")
        link.update(href="../modules/other.md", target=replacement["path"], sha256=replacement["sha256"])
    elif change == "guide-python":
        replacement = write(tmp_path, "docs/llm_wiki/guides/other.py", "def other():\n    return 1\n")
        link.update(href="other.py", target=replacement["path"], sha256=replacement["sha256"])
    elif change == "guide-target-escape":
        link["target"] = "docs/llm_wiki/guides/../modules/search.md"
    elif change == "selection-substitute":
        replacement = write(tmp_path, "other-selection.json", (tmp_path / "selection.json").read_text())
        link.update(href="../../../other-selection.json", target=replacement["path"], sha256=replacement["sha256"])
    elif change == "selection-hash":
        link["sha256"] = "0" * 64
    elif change == "selection-target-escape":
        link["target"] = "../selection.json"
    else:
        link["kind"] = "unreviewed"
    markdown = (tmp_path / route["artifact"]["path"]).read_text().replace(old_href, link["href"])
    repin_guide(route, context, markdown)
    with pytest.raises(ValueError):
        validate_authored_route(route, **context)


@pytest.mark.parametrize("extra", [
    "\n[unbound navigation][outside]\n\n[outside]: ../../../src/unselected.py\n",
    "\n[unbound navigation](<../../../src/unselected.py>)\n",
    '\n<a href="../../../src/unselected.py">unbound navigation</a>\n',
    '\n<A\n HREF="../../../src/unselected.py">unbound navigation</A>\n',
    '\n<https://example.invalid/guide> <a href="../../../src/unselected.py">unbound</a>\n',
])
def test_every_rendered_local_link_requires_bound_typed_navigation(tmp_path, extra):
    route, context = authored_packet(tmp_path)
    markdown = (tmp_path / route["artifact"]["path"]).read_text()
    repin_guide(route, context, markdown + extra)
    with pytest.raises(ValueError):
        validate_authored_route(route, **context)


def test_literal_inline_code_cannot_supply_clickable_source_citations(tmp_path):
    route, context = authored_packet(tmp_path)
    markdown = (tmp_path / route["artifact"]["path"]).read_text()
    source_link = next(link for link in route["links"] if link["kind"] == "source")
    literal = f"[source 0]({source_link['href']})"
    assert literal in markdown
    repin_guide(route, context, markdown.replace(literal, "`" + literal + "`"))
    with pytest.raises(ValueError, match="bound citations"):
        validate_authored_route(route, **context)


def test_bound_reference_and_angle_links_use_actual_commonmark_destinations(tmp_path):
    route, context = authored_packet(tmp_path)
    markdown = (tmp_path / route["artifact"]["path"]).read_text()
    source_link = next(link for link in route["links"] if link["kind"] == "source")
    original = f"[source 0]({source_link['href']})"
    markdown = markdown.replace(original, "[source 0][bound-source]")
    markdown += f"\n[bound-source]: <{source_link['href']}>\n"
    repin_guide(route, context, markdown)
    assert validate_authored_route(route, **context)["valid_route"] is True


def test_suppressed_file_autolink_is_literal_text_without_navigation(tmp_path):
    route, context = authored_packet(tmp_path)
    markdown = (tmp_path / route["artifact"]["path"]).read_text()
    repin_guide(route, context, markdown + "\n<file:///unselected.py>\n")
    assert validate_authored_route(route, **context)["valid_route"] is True


def test_http_autolink_cannot_be_claimed_as_relative_selected_source_evidence(tmp_path):
    route, context = authored_packet(tmp_path)
    selected = next(link for link in route["links"] if link["kind"] == "source")
    href = "https://example.invalid/unselected.py"
    route["links"].append({**selected, "href": href})
    markdown = (tmp_path / route["artifact"]["path"]).read_text()
    repin_guide(route, context, markdown + f"\n<{href}>\n")
    with pytest.raises(ValueError, match="bound citations"):
        validate_authored_route(route, **context)


def test_link_destination_or_title_cannot_supply_hidden_material_claims(tmp_path):
    route, context = authored_packet(tmp_path)
    register = json.loads((tmp_path / route["claim_register"]["path"]).read_text())
    clauses = "\n".join(claim["text"] for claim in register["claims"])
    markdown = (tmp_path / route["artifact"]["path"]).read_text()
    hidden = '[metadata](../modules/search.md "' + clauses + '")'
    repin_guide(route, context, markdown.replace(clauses, hidden))
    with pytest.raises(ValueError, match="visible prose"):
        validate_authored_route(route, **context)


def test_inline_formatting_preserves_visible_authored_claim_text(tmp_path):
    route, context = authored_packet(tmp_path)
    markdown = (tmp_path / route["artifact"]["path"]).read_text()
    assert "CLI validates roots" in markdown
    repin_guide(route, context, markdown.replace("CLI validates roots", "CLI **validates** roots"))
    assert validate_authored_route(route, **context)["valid_route"] is True


def supplemental_packet(root):
    route, context = authored_packet(root)
    module = module_statement_reference(
        root, "src/llm_wiki_cli/services/search_lexical.py", 3, 5,
    )
    function = source_reference(
        root, "src/llm_wiki_cli/services/search_service.py", "extra_boundary", 9, 10,
    )
    route["source_citations"] = [module, function]
    authored = {
        "schema_version": "owned-author-source-evidence/v1", "runtime": "unestablished",
        "function_refs": [function],
        "supplemental": [{"id": "budget-statements", **{
            key: value for key, value in module.items() if key != "scope"
        }}],
    }
    route["source_citations_artifact"] = write(root, "drafts/sources.json", json.dumps(authored))
    context["route_review"]["source_citations_artifact"] = deepcopy(route["source_citations_artifact"])
    context["route_review"]["source_citations_sha256"] = commitment(route["source_citations"])
    for citation in route["source_citations"]:
        route["links"].append({
            "href": "../../../" + citation["path"] + f"#L{citation['start_line']}-L{citation['end_line']}",
            "target": citation["path"], "kind": "source",
            "sha256": citation["whole_file_sha256"],
        })
    markdown = (root / route["artifact"]["path"]).read_text()
    markdown += "\n" + "\n".join(
        f"[supplement {i}]({link['href']})" for i, link in enumerate(route["links"][-2:])
    ) + "\n"
    repin_guide(route, context, markdown)
    return route, context


def test_module_constants_and_supplemental_function_links_bind_actual_author_source(tmp_path):
    route, context = supplemental_packet(tmp_path)
    before = tree(tmp_path), deepcopy((route, context))
    assert validate_authored_route(route, **context)["valid_route"] is True
    assert (tree(tmp_path), (route, context)) == before
    assert route["source_citations"][0]["scope"] == "module-level-statements"
    assert "qualified_name" not in route["source_citations"][0]


def test_function_citation_can_match_exact_author_supplement_without_invented_wrapper(tmp_path):
    route, context = supplemental_packet(tmp_path)
    artifact = json.loads((tmp_path / route["source_citations_artifact"]["path"]).read_text())
    function = artifact["function_refs"].pop()
    artifact["supplemental"].append({
        "id": "extra-function-slice", **{
            key: function[key] for key in (
                "path", "whole_file_sha256", "start_line", "end_line", "slice_sha256", "quote",
            )
        },
    })
    route["source_citations_artifact"] = write(tmp_path, "drafts/sources.json", json.dumps(artifact))
    context["route_review"]["source_citations_artifact"] = deepcopy(route["source_citations_artifact"])
    assert validate_authored_route(route, **context)["valid_route"] is True


@pytest.mark.parametrize("selector", [
    ("src/llm_wiki_cli/services/search_lexical.py", 1, 1),
    ("src/llm_wiki_cli/services/search_lexical.py", 1, 2),
    ("src/llm_wiki_cli/services/search_service.py", 11, 14),
    ("src/llm_wiki_cli/services/search_service.py", 12, 12),
    ("src/llm_wiki_cli/services/search_service.py", 13, 14),
])
def test_module_statement_scope_cannot_counterfeit_function_or_class_ownership(tmp_path, selector):
    authored_packet(tmp_path)
    with pytest.raises(ValueError, match="top-level nonfunction/nonclass"):
        module_statement_reference(tmp_path, *selector)


@pytest.mark.parametrize("change", [
    "scope", "whole-file-hash", "slice-hash", "quote", "selector",
    "unselected", "unreviewed-list", "artifact-hash", "artifact-review",
    "author-slice-substitution", "author-function-substitution", "function-owner",
])
def test_supplemental_citations_reject_scope_byte_author_and_review_drift(tmp_path, change):
    route, context = supplemental_packet(tmp_path)
    citation = route["source_citations"][0]
    if change == "scope":
        citation["scope"] = "function-body"
    elif change == "whole-file-hash":
        citation["whole_file_sha256"] = "0" * 64
    elif change == "slice-hash":
        citation["slice_sha256"] = "0" * 64
    elif change == "quote":
        citation["quote"] += "# forged\n"
    elif change == "selector":
        citation["end_line"] += 1
    elif change == "unselected":
        citation["path"] = "src/unselected.py"
    elif change == "unreviewed-list":
        context["route_review"]["source_citations_sha256"] = "0" * 64
    elif change == "artifact-hash":
        route["source_citations_artifact"]["sha256"] = "0" * 64
    elif change == "artifact-review":
        context["route_review"]["source_citations_artifact"]["path"] = "drafts/substitute.json"
    elif change in {"author-slice-substitution", "author-function-substitution"}:
        name = route["source_citations_artifact"]["path"]
        artifact = json.loads((tmp_path / name).read_text())
        artifact["supplemental" if change == "author-slice-substitution" else "function_refs"] = []
        route["source_citations_artifact"] = write(tmp_path, name, json.dumps(artifact))
        context["route_review"]["source_citations_artifact"] = deepcopy(route["source_citations_artifact"])
    else:
        route["source_citations"][1]["qualified_name"] = "search_records"
    if change != "unreviewed-list":
        context["route_review"]["source_citations_sha256"] = commitment(route["source_citations"])
    with pytest.raises(ValueError):
        validate_authored_route(route, **context)


_CHILD = """
import json, sys, traceback
from types import SimpleNamespace
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from llm_wiki_cli.commands import search_cmd
try:
    search_cmd.run(SimpleNamespace(**json.loads(sys.argv[2])))
except Exception as exc:
    chain, cursor = [], exc
    while cursor is not None:
        chain.append({"exception_type": type(cursor).__name__, "message": str(cursor),
                      "code": getattr(cursor, "code", None)})
        cursor = cursor.__cause__
    print(json.dumps({
        "exception_type": type(exc).__name__, "message": str(exc),
        "code": getattr(exc, "code", None),
        "cause_type": type(exc.__cause__).__name__ if exc.__cause__ else None,
        "cause_code": getattr(exc.__cause__, "code", None), "exception_chain": chain,
    }, sort_keys=True), file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
"""


def actual_command_case(tmp_path, *, selection=False, **options):
    """Approved runtime adapter scope; extraction never imports fixture source."""
    project = tmp_path / "owned"
    selected = project / "selected"
    selected.mkdir(parents=True)
    # If any search route executes inspected Python rather than reading it, fail.
    write(project, "selected/owner.py",
          "from pathlib import Path\nPath('SOURCE_EXECUTED').write_text('executed')\n"
          "def boundary():\n    return 'source-only cobalt'\n")
    write(project, "wiki/modules/owner.md", "# Owner\nWiki cobalt candidate.\n")
    if selection:
        write(project, ".llm-wiki/source-selection.json", json.dumps({
            "schema_version": "llm-wiki-source-selection/v1",
            "include": ["selected"], "exclude": [],
        }) + "\n")
    before = tree(project)
    root = Path(__file__).resolve().parents[1]
    source_files = [
        "src/llm_wiki_cli/commands/search_cmd.py", "src/llm_wiki_cli/api.py",
        "src/llm_wiki_cli/services/search_service.py",
        "src/llm_wiki_cli/services/search_lexical.py",
        "src/llm_wiki_cli/services/search_rank.py",
        "src/llm_wiki_cli/services/source_selection.py",
        "src/llm_wiki_cli/services/source_snapshot.py",
        "src/llm_wiki_cli/services/search_source.py",
    ]
    provenance = {path: sha((root / path).read_bytes()) for path in source_files}
    request = dict(
        src_dir=".", wiki_dir="wiki", allow_external_src=False,
        query="cobalt", kind=["modules"], limit=1, mode="ranked",
        source_selection=None, include_source=False, discovery=None, format="json",
    )
    request.update(options)
    argv = [sys.executable, "-c", _CHILD, str(root / "src"), json.dumps(request)]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(argv, cwd=project, env=env, capture_output=True, text=True, timeout=30)
    retained = {
        "scope": "actual read-only CLI/API search adapter on disposable owned inputs",
        "argv": argv, "request": request, "source_hashes": provenance,
        "fixture_before": before, "fixture_after": tree(project),
        "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode,
    }
    write(tmp_path, "raw-case.json", json.dumps(retained, sort_keys=True, indent=2))
    # -s retains successful raw case output in the campaign command transcript.
    print(json.dumps(retained, sort_keys=True))
    assert retained["fixture_after"] == before
    assert not (project / "SOURCE_EXECUTED").exists()
    return retained


@pytest.mark.parametrize("options,selection,message,cause", [
    ({"mode": "invented"}, False, "Search mode must", None),
    ({"query": ""}, False, "query must be a non-empty string", None),
    ({"mode": "ranked", "include_source": True}, False,
     "Explicit source indexing requires ranked-v2", None),
    ({}, True, "Selected search requires a valid committed ownership manifest", "storage-missing"),
])
def test_real_command_failure_boundaries_retained_without_publication(
    tmp_path, options, selection, message, cause,
):
    retained = actual_command_case(tmp_path, selection=selection, **options)
    assert retained["returncode"] == 1
    assert retained["stdout"] == ""
    assert message in retained["stderr"]
    exception = json.loads(retained["stderr"].splitlines()[0])
    assert exception["exception_type"] == "InvalidRequestError"
    assert exception["cause_type"] == "ValueError"
    assert exception["exception_chain"][1]["exception_type"] == "ValueError"
    assert [entry["code"] for entry in exception["exception_chain"] if entry["code"]] == ([cause] if cause else [])
    assert "Traceback" in retained["stderr"]


@pytest.mark.parametrize("mode,ranking", [
    ("ranked", "llm-wiki-search/lexical-v2"),
    ("ranked-v2", "llm-wiki-search/lexical-v2"),
    ("ranked-v1", "llm-wiki-search/lexical-v1"), ("substring", None),
])
def test_actual_unguarded_modes_are_bounded_candidates_without_implicit_source_index(
    tmp_path, mode, ranking,
):
    retained = actual_command_case(tmp_path, mode=mode)
    assert retained["returncode"] == 0, retained["stderr"]
    payload = json.loads(retained["stdout"])
    assert payload["mode"] == mode
    assert payload.get("ranking") == ranking
    assert payload["returned"] == 1
    assert payload["bounds"]["results"]["returned"] == 1
    assert "source_indexing" not in payload
    assert "discovery" not in payload
    if mode in {"ranked", "ranked-v2"}:
        assert payload["experimental"] is False
        assert payload["definitive_answer"] is False
