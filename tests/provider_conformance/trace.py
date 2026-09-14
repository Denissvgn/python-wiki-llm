"""Join source facts to actual Markdown, native records, and bounded packets."""

from __future__ import annotations

from collections import Counter
import re
from pathlib import Path

from .inventory import compare_records, paired, supported_source
from .markdown import named_rows, signature, tables
from .model import Finding, Incomplete, compare_sets, digest
from .python_ast import calls


def module_page(surface: dict, path: str) -> dict:
    pages = [
        p
        for p in surface["pages"]
        if p.get("source_path") == path and p["kind"] == "modules"
    ]
    if len(pages) != 1:
        raise Incomplete(f"Expected one source-attributed module page for {path}")
    return pages[0]


def entity_pages(surface: dict, path: str, name: str) -> list[dict]:
    return [
        p
        for p in surface["pages"]
        if p.get("source_path") == path
        and p["kind"] == "entities"
        and p["title"] == name
    ]


def markdown_observations(
    wiki: Path, surface: dict, path: str, lang: str
) -> list[dict]:
    page = module_page(surface, path)
    body = (wiki / page["canonical_path"]).read_text(encoding="utf-8")
    result = []
    for table in tables(body):
        if table["section"] in {"Classes", "Declarations"} and table["rows"]:
            header = table["rows"][0]
            for values in table["rows"][1:]:
                row = dict(zip(header, values))
                name = row.get(
                    "Class", row.get("Type", row.get("Name", row.get("Declaration")))
                )
                if name:
                    result.append(
                        {
                            "kind": "class",
                            "owner": "",
                            "name": name,
                            "line": int(row["Line"])
                            if row.get("Line", "").isdigit()
                            else 0,
                        }
                    )
    for row in named_rows(body, "Functions", "Function"):
        item = {"kind": "function", "owner": "", "name": row["Function"]}
        if row.get("Line", "").isdigit():
            item["line"] = int(row["Line"])
        if row.get("Signature") not in (None, "", "—"):
            item.update(signature(row["Signature"], lang))
        result.append(item)
    for cls in [r for r in result if r["kind"] == "class"]:
        pages = entity_pages(surface, path, cls["name"])
        if len(pages) > 1:
            pages = [
                p
                for p in pages
                if f"{path}:{cls['line']}"
                in (wiki / p["canonical_path"]).read_text(encoding="utf-8")
            ]
        if len(pages) != 1:
            raise Incomplete(f"Missing/ambiguous entity page for {path}:{cls['name']}")
        entity = (wiki / pages[0]["canonical_path"]).read_text(encoding="utf-8")
        bases = re.search(r"^\*\*Bases:\*\* (.+)$", entity, re.MULTILINE)
        cls["bases"] = re.findall(r"`([^`]+)`", bases[1]) if bases else []
        for row in named_rows(entity, "Attributes", "Name"):
            item = {
                "kind": "attribute",
                "name": row["Name"],
                "owner": cls["name"],
                "type": row.get("Type", ""),
            }
            default = row.get("Default")
            if default not in (None, "", "—", "required"):
                item["default"] = default
            if lang == "typescript":
                item["optional"] = row.get("Required", "Yes") == "No"
            result.append(item)
        for row in named_rows(entity, "Methods", "Method"):
            item = {"kind": "method", "name": row["Method"], "owner": cls["name"]}
            if row.get("Signature") not in (None, "", "—"):
                item.update(signature(row["Signature"], lang))
            result.append(item)
    return result


def compare_markdown(
    observation: dict, wiki: Path, surface: dict, path: str, lang: str, normalize
) -> list[Finding]:
    expected = supported_source(observation, lang)
    actual = markdown_observations(wiki, surface, path, lang)
    findings = compare_sets(expected, actual, fact=path, representation="markdown")
    for identity, source, observed in paired(expected, actual):
        if observed is None:
            continue
        source = dict(source)
        fact = path + ":" + "/".join(map(str, identity))
        findings.extend(
            compare_records(
                source,
                observed,
                lang,
                normalize,
                fact=fact,
                representation="markdown",
                reference=module_page(surface, path)["canonical_path"],
            )
        )
    return findings


def native_findings(
    surface: dict, knowledge: dict, native: dict, source: Path, paths: list[str]
) -> list[Finding]:
    model = {c["locator"]: c for c in knowledge["concepts"]}
    findings = []
    for page in surface["pages"]:
        path = page.get("source_path")
        if path not in paths or page["kind"] not in {"modules", "entities"}:
            continue
        locator = page["mcp_uri"]
        result = native.get(locator, {})
        concept = result.get("concept") or {}
        basis = (
            model.get(locator, {})
            .get("facets", {})
            .get("structure", {})
            .get("basis", {})
        )
        okay = (
            result.get("found") is True
            and concept.get("source_path") == path
            and concept.get("canonical_path") == page["canonical_path"]
            and concept.get("title") == page["title"]
            and basis.get("source_path") == path
            and basis.get("source_content_hash")
            == "sha256:" + digest((source / path).read_bytes())
        )
        findings.append(
            Finding(
                locator,
                "native",
                "pass" if okay else "fail",
                "source-and-observation-binding",
                {"source_path": path, "page": page["canonical_path"]},
                {"concept": concept, "basis": basis},
                page["canonical_path"],
            )
        )
    if not findings:
        raise Incomplete("No native source bindings were examined")
    return findings


def packet_entry(packet: dict, path: str) -> tuple[dict | None, Finding]:
    response = packet["response"]
    if response.get("format") == "markdown":
        raise Incomplete("Markdown packet requires rendered-record decoding")
    files = response.get("files", {})
    entry = files.get(path)
    if entry is None:
        omitted = response.get("omitted_files", [])
        explained = path in omitted or any(
            isinstance(item, dict) and item.get("path") == path for item in omitted
        )
        return None, Finding(
            path,
            "packet",
            "bounded-omission" if explained else "fail",
            "omitted-file" if explained else "unexplained-empty-selection",
            observed=response.get("bounds"),
        )
    detail = entry.get("detail", "deep")
    if detail != "deep":
        disclosed = path in response.get("downgraded_files", {})
        return entry, Finding(
            path,
            "packet",
            "bounded-omission" if disclosed else "fail",
            "downgraded-file" if disclosed else "undisclosed-downgrade",
            observed=detail,
        )
    return entry, Finding(
        path, "packet", "pass", "intended-deep-source-selection", observed=path
    )


def compact_packet_records(packet: dict, path: str) -> list[dict]:
    content = packet["response"].get("content", "")
    match = re.search(r"^### `" + re.escape(path) + r"`\s*$", content, re.MULTILINE)
    if not match:
        return []
    body = content[match.end() :].split("\n##", 1)[0]
    records, owner = [], ""
    for line in body.splitlines():
        cls = re.match(r"^- class \*\*(.+?)\*\*(?:\((.*)\))?$", line)
        function = re.match(
            r"^- (?:async )?def \*\*(.+?)\*\*\((.*?)\)(?: → (.*))?$", line
        )
        method = re.match(r"^  - (?:async )?`(.+?)\((.*?)\)`(?: → (.*))?$", line)
        if cls:
            owner = cls[1]
            records.append({"kind": "class", "name": owner, "owner": ""})
        elif function or method:
            item = function or method
            assert item is not None
            records.append(
                {
                    "kind": "function" if function else "method",
                    "name": item[1],
                    "owner": "" if function else owner,
                    "parameter_names": [
                        p.strip() for p in item[2].split(",") if p.strip()
                    ],
                    "return_type": item[3] or "",
                }
            )
    return records


def compact_claim(
    expected: dict,
    packet: dict,
    path: str,
    lang: str,
    normalize,
    fact: str,
    occurrence: int = 0,
) -> list[Finding]:
    if path in packet["response"].get("downgraded_files", {}) or path in packet[
        "response"
    ].get("omitted_files", []):
        return [
            Finding(
                fact,
                "packet-markdown",
                "bounded-omission",
                "compact-packet-source-downgraded",
            )
        ]
    records = [
        r
        for r in compact_packet_records(packet, path)
        if r["name"] == expected["name"]
        and r["owner"] == expected["owner"]
        and r["kind"] == expected["kind"]
    ]
    if occurrence >= len(records):
        return [
            Finding(
                fact,
                "packet-markdown",
                "fail",
                "missing-compact-declaration",
                expected,
                records,
            )
        ]
    actual = records[occurrence]
    findings = [
        Finding(
            fact,
            "packet-markdown",
            "pass",
            "compact-declaration-identity",
            reference=path,
        )
    ]
    if "params" in expected:
        names = [p["name"] for p in expected["params"]]
        findings.append(
            Finding(
                fact,
                "packet-markdown",
                "pass" if names == actual["parameter_names"] else "fail",
                "compact-parameter-names",
                names,
                actual["parameter_names"],
            )
        )
    if expected.get("return_type"):
        same = normalize(lang, "type", expected["return_type"]) == normalize(
            lang, "type", actual["return_type"]
        )
        findings.append(
            Finding(
                fact,
                "packet-markdown",
                "pass" if same else "fail",
                "compact-return-type",
                expected["return_type"],
                actual["return_type"],
            )
        )
    if "signature" in expected:
        findings.append(
            Finding(
                fact,
                "packet-markdown",
                "not-applicable",
                "compact-context-does-not-expose-Haskell-signatures",
            )
        )
    return findings


def flow_findings(markdown: str, source_text: str, fact: str) -> list[Finding]:
    observations = calls(source_text)
    if "sequenceDiagram" not in markdown:
        raise Incomplete(f"No sequence edges for {fact}")
    sequence = markdown.split("sequenceDiagram", 1)[1].split("```", 1)[0]
    names = dict(re.findall(r"participant (p\d+) as (.+)", sequence))
    edges = re.findall(r"(p\d+)(--?>>)(p\d+):", sequence)
    if not edges:
        raise Incomplete(f"Empty flow audit for {fact}")
    findings, uses = [], Counter()
    for index, (start, arrow, end) in enumerate(edges):
        caller, callee = names[start], names[end]
        resolution = "local" if arrow == "->>" else "external-or-unresolved"
        candidates = [
            c for c in observations if c["caller"] == caller and c["callee"] == callee
        ]
        owner_ids = {
            (c["caller"], c["occurrence"], c["caller_line"]) for c in candidates
        }
        key = (caller, callee, resolution)
        uses[key] += 1
        matching = [c for c in candidates if c["resolution"] == resolution]
        okay = len(owner_ids) == 1 and len(matching) >= uses[key]
        findings.append(
            Finding(
                f"{fact}:edge:{index}",
                "flow",
                "pass" if okay else "fail",
                "lexical-call-and-resolution",
                {"caller": caller, "callee": callee, "resolution": resolution},
                candidates,
            )
        )
    for index, row in enumerate(named_rows(markdown, "Call data", "From")):
        matches = [
            c
            for c in observations
            if c["caller"] == row["From"]
            and c["callee"] == row["To"]
            and str(c["line"]) == row["Line"]
        ]
        findings.append(
            Finding(
                f"{fact}:call-data:{index}",
                "flow",
                "pass" if len(matches) == 1 else "fail",
                "exact-call-coordinate",
                row,
                matches,
            )
        )
    return findings
