"""Test-owned checks for authored search routes; acceptance is source review only."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

from .search_orientation import (
    QUALIFICATIONS, REQUIRED_SOURCES, _file, _reference, _require,
    commitment, validate_design,
)


def evidence_notice(trace: dict) -> str:
    """Keep current limitations separate from saved historical counts."""
    notice = (
        "This is a source-grounded reading route, not a generated runtime diagram. "
        "Current generated trace coverage is unestablished."
    )
    if trace["status"] == "timed-out":
        notice += " The current whole-provider trace capture timed out."
    elif trace["status"] == "unavailable":
        notice += " A current whole-provider trace capture is unavailable."
    historical = trace["historical_baseline"]
    if historical is not None:
        notice += (
            f" The saved static flow shows {historical['displayed']} of "
            f"{historical['captured']} interactions with "
            f"{historical['captured'] - historical['displayed']} display omissions; "
            "these saved counts are not a fresh trace for current code."
        )
    notice += " Static presentation order does not prove runtime execution."
    return notice


def _artifact(root: Path, descriptor: dict) -> bytes:
    content = _file(root, descriptor["path"]).read_bytes()
    _require(
        hashlib.sha256(content).hexdigest() == descriptor["sha256"],
        "authored or review artifact hash drift",
    )
    return content


def module_statement_reference(
    root: Path, path: str, start_line: int, end_line: int,
) -> dict:
    """Bind a static module statement slice without inventing a function owner."""
    content = _file(root, path).read_bytes()
    tree = ast.parse(content)
    _require(
        path.endswith(".py") and type(start_line) is int and type(end_line) is int
        and 1 <= start_line <= end_line <= len(content.splitlines()),
        "module statement source coordinates required",
    )
    definitions = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    statements = [node for node in tree.body if not isinstance(node, definitions)]
    excluded = []
    for node in ast.walk(tree):
        if isinstance(node, definitions):
            first = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
            excluded.append((first, node.end_lineno or node.lineno))
    _require(
        all(
            any(node.lineno <= line <= (node.end_lineno or node.lineno) for node in statements)
            and not any(first <= line <= last for first, last in excluded)
            for line in range(start_line, end_line + 1)
        ),
        "module slice must lie wholly in top-level nonfunction/nonclass statements",
    )
    quote = b"".join(content.splitlines(keepends=True)[start_line - 1:end_line]).decode("utf-8")
    return {
        "scope": "module-level-statements", "path": path,
        "whole_file_sha256": hashlib.sha256(content).hexdigest(),
        "start_line": start_line, "end_line": end_line,
        "slice_sha256": hashlib.sha256(quote.encode()).hexdigest(), "quote": quote,
    }


def _source_citations(root: Path, route: dict, binding: dict, review: dict) -> list:
    citations = route.get("source_citations", [])
    _require(isinstance(citations, list), "source citations must be a list")
    if not citations:
        return []
    descriptor = route["source_citations_artifact"]
    authored = json.loads(_artifact(root, descriptor))
    _require(
        isinstance(authored, dict)
        and isinstance(authored.get("function_refs"), list)
        and isinstance(authored.get("supplemental"), list),
        "independently authored source JSON evidence required",
    )
    _require(
        review["source_citations_sha256"] == commitment(citations)
        and review["source_citations_artifact"] == descriptor,
        "independent source review must pin supplemental citations and author artifact",
    )
    selected = binding["selected_source_hashes"]
    for citation in citations:
        _require(
            isinstance(citation, dict)
            and citation.get("path") in selected
            and citation["path"].endswith(".py"),
            "supplemental citation must name selected Python source",
        )
        if "scope" in citation:
            _require(
                citation["scope"] == "module-level-statements",
                "typed module statement citation scope required",
            )
            expected = module_statement_reference(
                root, citation["path"], citation["start_line"], citation["end_line"],
            )
            _require(
                citation == expected and selected[citation["path"]] == citation["whole_file_sha256"],
                "module statement citation hash or coordinates drift",
            )
            original = {key: value for key, value in citation.items() if key != "scope"}
            _require(
                any(
                    isinstance(item, dict)
                    and {key: value for key, value in item.items() if key != "id"} == original
                    for item in authored["supplemental"]
                ),
                "module citation must match independently authored supplemental evidence",
            )
        else:
            _reference(root, citation, selected)
            _require(
                citation in authored["function_refs"]
                or any(
                    isinstance(item, dict)
                    and {key: value for key, value in item.items() if key != "id"}
                    == {
                        key: citation[key] for key in (
                            "path", "whole_file_sha256", "start_line",
                            "end_line", "slice_sha256", "quote",
                        )
                    }
                    for item in authored["supplemental"]
                ),
                "function citation must match independently authored source evidence",
            )
    return citations


def _markdown_view(markdown: str) -> tuple[str, set[str]]:
    """Read CommonMark prose and actual visible hyperlinks.

    The parser handles fence closing rules, reference links, autolinks and
    literal code spans. Noncomment HTML is outside this authored guide format.
    """
    tokens = MarkdownIt("commonmark").parse(markdown)
    prose, hyperlinks = [], set()

    def without_comments(text: str) -> str:
        return re.sub(r"<!--.*?(?:-->|$)", "", text, flags=re.DOTALL)

    for token in tokens:
        if token.type == "fence":
            language = token.info.strip().split(maxsplit=1)
            _require(
                not language or language[0].casefold() != "mermaid",
                "authored Mermaid cannot supply runtime arrows",
            )
        if token.type == "html_block":
            _require(
                not without_comments(token.content).strip(),
                "noncomment HTML forbidden in authored guide",
            )
        if token.type != "inline":
            continue
        prose.append("".join(
            child.content if child.type in {"text", "code_inline"}
            else "\n" if child.type in {"softbreak", "hardbreak"} else ""
            for child in token.children or []
        ))
        for child in token.children or []:
            if child.type == "html_inline":
                _require(
                    not without_comments(child.content).strip(),
                    "noncomment HTML forbidden in authored guide",
                )
            if child.type == "link_open":
                href = child.attrGet("href")
                if href is not None:
                    hyperlinks.add(href)
    return "\n".join(prose), hyperlinks


def _links(root: Path, route: dict, markdown: str, hyperlinks: set[str], claims: list, citations: list, binding: dict, trace: dict) -> None:
    intended = _file(root, route["intended_path"])
    _require(
        not re.search(r"<!--[^>]*(?:generated|llm-wiki)", markdown, re.IGNORECASE),
        "generated regions must be preserved outside authored companion",
    )
    local = {
        href for href in hyperlinks
        if urlsplit(href).scheme.casefold() == "file"
        or (not urlsplit(href).scheme and not urlsplit(href).netloc)
    }
    links = route["links"]
    _require(
        len({link["href"] for link in links}) == len(links)
        and {link["href"] for link in links} == local,
        "all local authored links require unique bound citations",
    )
    roles = {link["kind"] for link in links}
    _require(
        {"source", "module", "raw-flow"} <= roles
        and roles <= {"source", "module", "raw-flow", "guide", "selection"},
        "source/module/raw-flow navigation and known optional roles required",
    )
    refs = [ref for claim in claims for ref in claim["refs"]]
    authorized = refs + citations
    cited = set()
    for link in links:
        parsed = urlsplit(link["href"])
        _require(
            not parsed.scheme and not parsed.netloc and not parsed.query
            and bool(parsed.path) and "\\" not in parsed.path,
            "relative authored link required",
        )
        resolved = (intended.parent / unquote(parsed.path)).resolve()
        _require(resolved.is_relative_to(root.resolve()), "authored link escapes root")
        _require(
            resolved == _file(root, link["target"]).resolve(),
            "authored link resolves against wrong future guide path",
        )
        content = _artifact(root, {"path": link["target"], "sha256": link["sha256"]})
        if link["kind"] == "source":
            _require(
                link["target"].endswith(".py")
                and binding["selected_source_hashes"].get(link["target"]) == link["sha256"],
                "excluded or unselected source citation",
            )
            matches = [
                ref for ref in authorized
                if ref["path"] == link["target"]
                and parsed.fragment == f"L{ref['start_line']}-L{ref['end_line']}"
            ]
            _require(bool(matches), "source citation requires exact current AST lines")
            cited.update(commitment(ref) for ref in matches)
        else:
            if link["kind"] == "module":
                _require(
                    link["target"].startswith("docs/llm_wiki/modules/")
                    and link["target"].endswith(".md"),
                    "module navigation requires a canonical module Markdown page",
                )
            if link["kind"] == "guide":
                _require(
                    link["target"].startswith("docs/llm_wiki/guides/")
                    and link["target"].endswith(".md"),
                    "guide navigation requires a canonical guide Markdown page",
                )
            if link["kind"] == "selection":
                selection = binding["source_selection"]
                _require(
                    link["target"] == selection["path"]
                    and link["sha256"] == selection["sha256"],
                    "selection navigation must bind the current source-selection artifact",
                )
            if link["kind"] == "raw-flow" and trace["historical_baseline"] is not None:
                historical = trace["historical_baseline"]["artifact"]
                _require(
                    link["target"] == historical["path"]
                    and link["sha256"] == historical["sha256"],
                    "raw-flow navigation must bind the original historical artifact",
                )
        if link["kind"] != "source" and parsed.fragment:
            _require(link["target"].endswith(".md"), "unsupported artifact anchor")
            headings = re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", content.decode(), re.MULTILINE)
            anchors = {
                re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
                for heading in headings
            }
            _require(unquote(parsed.fragment) in anchors, "missing Markdown link anchor")
    _require(
        {commitment(ref) for ref in refs} <= cited,
        "material source claims require authored source citations",
    )


def validate_authored_route(
    route: dict, *, root: Path, binding: dict, design: dict, trace: dict,
    trace_sha256: str, source_review: dict, route_review: dict,
) -> dict:
    """Validate pinned provenance, never generate, patch, or execute inspected code.

    Both review receipts and original trace commitment must come from the
    controller, separately from the authored route. Structural checks do not
    independently establish the truth of prose or replace semantic source review.
    The receipt covers every material claim in the whole guide, including prose
    absent from the register; structural checks cannot judge that prose semantically.
    """
    try:
        validate_design(
            design, root=root, binding=binding, trace=trace,
            trace_sha256=trace_sha256, source_review=source_review,
        )
        _require(
            route["schema_version"] == "af13-authored-search-route/v1"
            and route["status"] == "source-reviewed-route",
            "authored source-reviewed route status required",
        )
        _require(
            route["authority"] == "authored-only"
            and route["generated_region_policy"] == "preserve"
            and route["runtime_arrows"] is False,
            "readonly authored authority required",
        )
        _require(
            route["design_sha256"] == commitment(design),
            "provider/design binding drift",
        )
        markdown = _artifact(root, route["artifact"]).decode("utf-8")
        prose, hyperlinks = _markdown_view(markdown)
        register = json.loads(_artifact(root, route["claim_register"]))
        _require(
            register["schema_version"] == "af13-search-route-claims/v1",
            "bound material claim register required",
        )
        claims = register["claims"]
        _require(isinstance(claims, list) and bool(claims), "material claims required")
        ids = [claim["id"] for claim in claims]
        _require(
            all(isinstance(identity, str) and identity for identity in ids)
            and len(set(ids)) == len(ids),
            "unique material claim ids required",
        )
        expected = {
            (stage, key)
            for stage, qualifications in QUALIFICATIONS.items()
            for key in qualifications
        }
        covered = set()
        for claim in claims:
            stage, key = claim["stage_id"], claim["qualification_key"]
            _require(
                (stage, key) in expected
                and claim["qualification"] == QUALIFICATIONS[stage][key],
                "required current/default/legacy/guard/index/output qualification",
            )
            covered.add((stage, key))
            _require(
                claim["evidence"] == "source-reviewed"
                and claim["runtime"] == "unestablished",
                "authored route cannot claim generated invocation/render/runtime acceptance",
            )
            _require(
                isinstance(claim["text"], str) and bool(claim["text"].strip()),
                "material claim text required",
            )
            claim_prose, _ = _markdown_view(claim["text"])
            _require(
                bool(claim_prose.strip()) and claim_prose in prose,
                "material claim text must be present in visible prose",
            )
            _require(bool(claim["refs"]), "material source refs required")
            for ref in claim["refs"]:
                _reference(root, ref, binding["selected_source_hashes"])
        _require(covered == expected, "all four stages and material qualifications required")
        for stage, required in REQUIRED_SOURCES.items():
            full = {
                (ref["path"], ref["qualified_name"])
                for claim in claims if claim["stage_id"] == stage
                for ref in claim["refs"]
                if ref["start_line"] == ref["function_start_line"]
                and ref["end_line"] == ref["function_end_line"]
            }
            _require(required <= full, "stage full owning-function refs required")
        _require(
            route["notice"] == evidence_notice(trace) and route["notice"] in prose,
            "current limitation and historical-only notice required",
        )
        citations = _source_citations(root, route, binding, route_review)
        _links(root, route, markdown, hyperlinks, claims, citations, binding, trace)
        _require(
            route_review["status"] == "source-reviewed-authored-route"
            and route_review["runtime_acceptance"] == "unestablished"
            and route_review["material_claim_scope"] == "whole-authored-guide",
            "independent authored source review receipt required",
        )
        author = route["author_id"]
        _require(
            isinstance(author, str) and bool(author)
            and route_review["author_id"] == author
            and isinstance(route_review["reviewer_id"], str)
            and bool(route_review["reviewer_id"])
            and route_review["reviewer_id"] != author,
            "independent material claim reviewer required",
        )
        _require(
            route_review["guide_sha256"] == route["artifact"]["sha256"]
            and route_review["claim_register_sha256"] == route["claim_register"]["sha256"]
            and route_review["source_selection_identity"] == binding["source_selection"]["identity"]
            and route_review["selected_source_hashes"] == binding["selected_source_hashes"]
            and route_review["provider_hashes"] == binding["provider_hashes"]
            and route_review["stage_ids"] == list(QUALIFICATIONS)
            and route_review["claim_sha256"] == {
                claim["id"]: commitment(claim) for claim in claims
            },
            "independent review must bind all authored claims and current source/provider",
        )
        _artifact(root, route_review["artifact"])
    except (KeyError, TypeError, IndexError, AttributeError, UnicodeError, OSError) as exc:
        raise ValueError("malformed authored route or review evidence") from exc
    return {
        "valid_route": True,
        "source_grounded_orientation_coverage": "source-reviewed-route",
        "generated_trace_stage_coverage": "mitigated/not-met",
        "runtime_acceptance": "unestablished",
        "structural_validation_only": True,
    }
