"""Explicit corpus runner and trace accounting; campaign data stays external."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess

from .frontends import language
from .inventory import (
    compare_inventory,
    compare_original,
    compare_records,
    flatten,
    require_unique_facts,
    supported_source,
)
from .model import (
    Finding,
    Incomplete,
    canonical_json,
    conclude,
    digest,
    read_json,
    require_hash,
    require_installed_archive,
)
from .trace import (
    compare_markdown,
    compact_claim,
    entity_pages,
    flow_findings,
    markdown_observations,
    module_page,
    native_findings,
    packet_entry,
)


def resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path.absolute() if path.is_absolute() else (base / path).absolute()


def tree_hashes(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): digest(p.read_bytes())
        for p in root.rglob("*")
        if p.is_file() and not p.is_symlink() and ".git" not in p.parts
    }


def validate_manifest(manifest: dict) -> None:
    if manifest.get("schema_version") != "provider-conformance/v1" or not manifest.get(
        "projects"
    ):
        raise Incomplete("Missing supported nonempty corpus manifest")
    ids = [p["id"] for p in manifest["projects"]]
    if len(ids) != len(set(ids)) or set(ids) != set(
        manifest.get("required_project_ids", ids)
    ):
        raise Incomplete("Missing or duplicate required projects")
    lanes = set(manifest.get("provider", {}).get("interpreters", {}))
    required = (
        {"wheel", "mcp-wheel"}
        if manifest.get("preview_only")
        else {"wheel", "sdist", "mcp-wheel", "mcp-sdist"}
    )
    if not required <= lanes:
        raise Incomplete("Missing required installed artifact/SDK consumer lanes")
    if any(
        not p.get("primary") or not p.get("source_hashes") for p in manifest["projects"]
    ):
        raise Incomplete("An exhaustive module and bound source inventory are required")


def execute(
    argv: list[str], *, cwd: Path, output: Path, environment: dict, timeout=1800
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with (
        output.with_suffix(".stdout").open("wb") as stdout,
        output.with_suffix(".stderr").open("wb") as stderr,
    ):
        try:
            result = subprocess.run(
                argv,
                cwd=cwd,
                env=environment,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise Incomplete(f"Consumer execution unavailable: {error}") from error
    output.with_suffix(".command.json").write_bytes(
        canonical_json({"argv": argv, "cwd": str(cwd), "exit_code": result.returncode})
    )
    if result.returncode:
        raise Incomplete(
            f"Consumer exit {result.returncode}; see {output.with_suffix('.stderr')}"
        )


def packet_markdown_fact(fact: dict, packet: dict) -> Finding:
    """Markdown context is a compact declaration view, not an inventory dump."""
    path = fact["path"]
    content = packet["response"].get("content", "")
    match = re.search(r"^### `" + re.escape(path) + r"`\s*$", content, re.MULTILINE)
    if match is None:
        return Finding(
            fact["id"],
            "packet-markdown",
            "bounded-omission"
            if path in packet["response"].get("omitted_files", [])
            else "fail",
            "source-section-absent",
        )
    section = content[match.end() :].split("\n##", 1)[0]
    selector = fact["selector"]
    if len(selector) == 2 and selector[0] in {"classes", "functions"}:
        present = (
            re.search(r"\*\*" + re.escape(selector[1]) + r"\*\*", section) is not None
        )
        return Finding(
            fact["id"],
            "packet-markdown",
            "pass" if present else "bounded-omission",
            "compact-declaration-name"
            if present
            else "compact-view-omits-declaration-detail",
            observed=selector[1],
        )
    return Finding(
        fact["id"],
        "packet-markdown",
        "not-applicable",
        "compact-Markdown-does-not-encode-this-inventory-field",
        reference=path,
    )


def assess(
    project: dict,
    base: Path,
    frontends,
    capture: Path,
    observations: dict,
    facts: list[dict],
    claims: list[dict],
) -> dict:
    source, wiki = resolve(base, project["source"]), resolve(base, project["wiki"])
    inventory = read_json(capture / "inventory.json")["inventory"]
    surface, knowledge, native = (
        read_json(capture / name)
        for name in ("surface.json", "knowledge.json", "native.json")
    )
    cases = read_json(capture / "cases.json")
    by_file = {
        (c["source_path"], c["format"]): read_json(capture / c["packet"]) for c in cases
    }
    findings = []
    markdown_cache = {}

    def rendered(path):
        if path not in markdown_cache:
            markdown_cache[path] = markdown_observations(
                wiki, surface, path, language(path)
            )
        return markdown_cache[path]

    for path in project["primary"]:
        lang = language(path)
        findings.extend(
            compare_inventory(
                observations[path],
                inventory.get(path, {}),
                lang,
                frontends.normalize,
                path=path,
            )
        )
        findings.extend(
            compare_markdown(
                observations[path], wiki, surface, path, lang, frontends.normalize
            )
        )
    bindings = native_findings(surface, knowledge, native, source, list(observations))
    findings.extend(bindings)
    binding_map = {f.fact: f for f in bindings}
    for fact in facts:
        path = fact["path"]
        lang = language(path)
        findings.append(
            compare_original(
                fact, inventory.get(path, {}), lang, frontends.normalize, "inventory"
            )
        )
        if fact["applicability"] != "supported":
            for representation in (
                "markdown",
                "native",
                "packet-json",
                "packet-markdown",
            ):
                findings.append(
                    Finding(
                        fact["id"],
                        representation,
                        "not-applicable",
                        fact["proposition"],
                    )
                )
            continue
        page = module_page(surface, path)
        selector = fact["selector"]
        if len(selector) >= 2 and selector[0] == "classes":
            matches = entity_pages(surface, path, selector[1])
            if len(matches) != 1:
                raise Incomplete(f"Ambiguous original native fact: {fact['id']}")
            page = matches[0]
        binding = binding_map.get(page["mcp_uri"])
        findings.append(
            Finding(
                fact["id"],
                "native",
                binding.status if binding else "fail",
                "parent-source-observation-link",
                reference=page["mcp_uri"],
            )
        )
        body = (wiki / page["canonical_path"]).read_text(encoding="utf-8")
        if selector[0] in {"module", "imports"}:
            needle = (
                fact["expected"].get("value") if selector == ["module"] else selector[1]
            )
            findings.append(
                Finding(
                    fact["id"],
                    "markdown",
                    "pass" if needle in body else "fail",
                    "source-module-or-import",
                    observed=needle,
                    reference=page["canonical_path"],
                )
            )
        else:
            markdown_records = rendered(path)
            kind = (
                "class"
                if len(selector) == 2 and selector[0] == "classes"
                else "function"
                if len(selector) == 2
                else "attribute"
                if selector[2] == "attributes"
                else "method"
            )
            name = selector[-1]
            owner = selector[1] if len(selector) > 2 else ""
            expected_records = [
                r
                for r in supported_source(observations[path], lang)
                if r["kind"] == kind and r["name"] == name and r["owner"] == owner
            ]
            actual_records = [
                r
                for r in markdown_records
                if r["kind"] == kind and r["name"] == name and r["owner"] == owner
            ]
            if len(expected_records) > 1:
                exact = [
                    r for r in expected_records if r.get("line") == fact["lines"][0]
                ]
                expected_records = exact or [
                    r
                    for r in expected_records
                    if fact["lines"][0] <= r.get("line", -1) <= fact["lines"][1]
                ]
                actual_records = [
                    r
                    for r in actual_records
                    if r.get("line") in {e["line"] for e in expected_records}
                ]
            okay = len(expected_records) == len(actual_records) == 1
            findings.append(
                Finding(
                    fact["id"],
                    "markdown",
                    "pass" if okay else "fail",
                    "exact-declaration-owner-and-occurrence",
                    reference=page["canonical_path"],
                )
            )
            if okay:
                expected = dict(expected_records[0])
                findings.extend(
                    compare_records(
                        expected,
                        actual_records[0],
                        lang,
                        frontends.normalize,
                        fact=fact["id"],
                        representation="markdown",
                        reference=page["canonical_path"],
                    )
                )
        packet = by_file[(path, "json")]
        entry, selection = packet_entry(packet, path)
        if selection.status == "pass" and entry is not None:
            findings.append(
                compare_original(fact, entry, lang, frontends.normalize, "packet-json")
            )
        else:
            findings.append(
                Finding(
                    fact["id"],
                    "packet-json",
                    selection.status,
                    selection.reason,
                    reference=path,
                )
            )
        findings.append(packet_markdown_fact(fact, by_file[(path, "markdown")]))
        if selector[0] == "functions":
            source_records = [
                r
                for r in supported_source(observations[path], lang)
                if r["kind"] == "function" and r["name"] == selector[1]
            ]
            selected_record = next(
                (r for r in source_records if r["line"] == fact["lines"][0]), None
            )
            if selected_record is not None:
                position = sorted(source_records, key=lambda r: r["line"]).index(
                    selected_record
                )
                findings.extend(
                    compact_claim(
                        selected_record,
                        by_file[(path, "markdown")],
                        path,
                        lang,
                        frontends.normalize,
                        fact["id"],
                        position,
                    )
                )
        selected = packet["response"].get("knowledge", {})
        included = {
            c["locator"] for c in selected.get("selection", {}).get("concepts", [])
        }
        truncated = (
            selected.get("bounds", {}).get("concepts", {}).get("truncated") is True
        )
        findings.append(
            Finding(
                fact["id"],
                "packet-native",
                "pass"
                if page["mcp_uri"] in included
                else "bounded-omission"
                if truncated
                else "fail",
                "included-native-link"
                if page["mcp_uri"] in included
                else "native-selection-bound",
                reference=page["mcp_uri"],
            )
        )
    for index, frozen in enumerate(claims):
        path, claim = frozen["path"], frozen["claim"]
        lang = language(path)
        fact_id = f"{project['id']}-emitted-{index + 1:03d}"
        candidates = [
            r
            for r in supported_source(observations[path], lang)
            if r["name"] == claim["name"]
            and r.get("line") == claim["line"]
            and r["kind"] in {"function", "method"}
        ]
        actual = [
            r
            for r in flatten(inventory.get(path, {}))
            if r["name"] == claim["name"] and r.get("line") == claim["line"]
        ]
        if len(candidates) != 1 or len(actual) != 1:
            findings.append(
                Finding(
                    fact_id,
                    "inventory",
                    "fail",
                    "frozen-emitted-claim-identity",
                    claim,
                    candidates,
                )
            )
            continue
        expected = candidates[0]
        findings.extend(
            compare_records(
                expected,
                actual[0],
                lang,
                frontends.normalize,
                fact=fact_id,
                representation="inventory",
            )
        )
        page = module_page(surface, path)
        md = [
            r
            for r in rendered(path)
            if r["kind"] == expected["kind"]
            and r["name"] == expected["name"]
            and r["owner"] == expected["owner"]
        ]
        same_name = [
            r
            for r in supported_source(observations[path], lang)
            if r["kind"] == expected["kind"]
            and r["name"] == expected["name"]
            and r["owner"] == expected["owner"]
        ]
        position = sorted(same_name, key=lambda r: r["line"]).index(expected)
        if position >= len(md) or len(md) != len(same_name):
            findings.append(
                Finding(
                    fact_id,
                    "markdown",
                    "fail",
                    "emitted-claim-occurrence",
                    expected,
                    md,
                )
            )
        else:
            exp = dict(expected)
            findings.extend(
                compare_records(
                    exp,
                    md[position],
                    lang,
                    frontends.normalize,
                    fact=fact_id,
                    representation="markdown",
                    reference=page["canonical_path"],
                )
            )
        findings.append(
            Finding(
                fact_id,
                "native",
                binding_map[page["mcp_uri"]].status,
                "source-module-observation-link",
                reference=page["mcp_uri"],
            )
        )
        findings.extend(
            compact_claim(
                expected,
                by_file[(path, "markdown")],
                path,
                lang,
                frontends.normalize,
                fact_id,
                position,
            )
        )
        entry, selection = packet_entry(by_file[(path, "json")], path)
        if selection.status == "pass" and entry is not None:
            rows = [
                r
                for r in flatten(entry)
                if r["name"] == claim["name"] and r.get("line") == claim["line"]
            ]
            if len(rows) == 1:
                findings.extend(
                    compare_records(
                        expected,
                        rows[0],
                        lang,
                        frontends.normalize,
                        fact=fact_id,
                        representation="packet-json",
                    )
                )
            else:
                findings.append(
                    Finding(
                        fact_id,
                        "packet-json",
                        "fail",
                        "emitted-claim-missing",
                        expected,
                        rows,
                    )
                )
        else:
            findings.append(
                Finding(fact_id, "packet-json", selection.status, selection.reason)
            )
    for flow in project.get("flows", []):
        findings.extend(
            flow_findings(
                (wiki / flow["page"]).read_text(),
                (source / flow["source"]).read_text(),
                flow["page"],
            )
        )
    result = conclude(findings)
    result["project"] = project["id"]
    result["question_evidence"] = {
        "discovery": [
            f.payload()
            for f in findings
            if f.reason
            in {
                "parent-source-observation-link",
                "exact-declaration-owner-and-occurrence",
            }
        ],
        "dependencies": [
            f.payload()
            for f in findings
            if f.representation == "flow" or f.reason == "source-module-or-import"
        ],
        "contracts": [
            f.payload()
            for f in findings
            if "parameter" in f.reason
            or f.reason
            in {
                "declaration-type",
                "declaration-return_type",
                "declaration-signature",
                "declaration-optional",
            }
        ],
        "follow_up": [
            f.payload()
            for f in findings
            if f.status in {"bounded-omission", "not-applicable", "blocked", "fail"}
        ],
    }
    return result


def run(manifest_path: Path, frontends, output: Path) -> dict:
    manifest_path = manifest_path.absolute()
    base = manifest_path.parent
    manifest = read_json(manifest_path)
    validate_manifest(manifest)
    for artifact in manifest["provider"]["artifacts"]:
        require_hash(resolve(base, artifact["path"]), artifact["sha256"])
    verifier = digest(
        b"".join(
            p.read_bytes()
            for p in sorted(Path(__file__).parent.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts
        )
    )
    results = []
    for project in manifest["projects"]:
        project_output = output / project["id"]
        project_output.mkdir(parents=True, exist_ok=True)
        try:
            source = resolve(base, project["source"])
            require_hash(resolve(base, project["facts"]), project["facts_sha256"])
            require_hash(resolve(base, project["claims"]), project["claims_sha256"])
            for path, sha in project["source_hashes"].items():
                require_hash(source / path, sha)
            facts = [
                json.loads(line)
                for line in resolve(base, project["facts"]).read_text().splitlines()
            ]
            claims = read_json(resolve(base, project["claims"]))
            require_unique_facts(facts)
            if any(
                f["commit"] != project["commit"] or f["project"] != project["id"]
                for f in facts
            ):
                raise Incomplete(
                    "Frozen fact target identity differs from the manifest"
                )
            if len(claims) != 20:
                raise Incomplete("The frozen 20-claim sample must not be replaced")
            paths = sorted(
                set(project["primary"])
                | {f["path"] for f in facts}
                | {c["path"] for c in claims}
            )
            if set(paths) != set(project["source_hashes"]):
                raise Incomplete(
                    "Source hash inventory does not bind every audited file"
                )
            observations = {path: frontends.observe(source / path) for path in paths}
            (project_output / "source-observations.json").write_bytes(
                canonical_json(observations)
            )
            for lane, interpreter in manifest["provider"]["interpreters"].items():
                if lane not in {"wheel", "sdist"}:
                    continue
                artifact_sha256 = next(
                    a["sha256"]
                    for a in manifest["provider"]["artifacts"]
                    if a["kind"] == lane
                )
                capture = resolve(base, project["captures"][lane])
                mcp_capture = resolve(
                    base,
                    project.get("mcp_captures", {}).get(
                        lane, str(capture.with_name(lane + "-mcp"))
                    ),
                )
                environment = {
                    **os.environ,
                    **manifest.get("environment", {}),
                    "LLM_WIKI_CACHE_DIR": str(resolve(base, manifest["helper_cache"])),
                }
                environment.pop("PYTHONPATH", None)
                environment.pop("PYTHONHOME", None)
                if not manifest.get("reuse_captures", False):
                    config = {
                        "source": str(source),
                        "wiki": str(resolve(base, project["wiki"])),
                        "output": str(capture),
                        "helper_cache": environment["LLM_WIKI_CACHE_DIR"],
                        "files": paths,
                        "adapter_files": project["primary"],
                        "api_contracts": project["id"] == "P2",
                        "artifact_sha256": artifact_sha256,
                    }
                    config_path = project_output / (lane + "-capture-config.json")
                    config_path.write_bytes(canonical_json(config))
                    execute(
                        [
                            str(resolve(base, interpreter)),
                            "-X",
                            "utf8",
                            "-I",
                            str(Path(__file__).with_name("consumer.py")),
                            str(config_path),
                        ],
                        cwd=resolve(base, project["workspace"]),
                        output=project_output / (lane + "-capture"),
                        environment=environment,
                    )
                    mcp = manifest["provider"]["interpreters"].get("mcp-" + lane)
                    if not mcp:
                        raise Incomplete(f"Missing actual SDK consumer for {lane}")
                    config.update(
                        capture=str(capture),
                        output=str(mcp_capture),
                    )
                    mcp_path = project_output / (lane + "-mcp-config.json")
                    mcp_path.write_bytes(canonical_json(config))
                    execute(
                        [
                            str(resolve(base, mcp)),
                            "-X",
                            "utf8",
                            "-I",
                            str(Path(__file__).with_name("mcp_consumer.py")),
                            str(mcp_path),
                        ],
                        cwd=resolve(base, project["workspace"]),
                        output=project_output / (lane + "-mcp"),
                        environment=environment,
                    )
                captured = read_json(capture / "capture.json")
                require_installed_archive(
                    captured.get("archive_origin", {}), artifact_sha256
                )
                if captured.get("status") != "pass" or captured["files"] != paths:
                    raise Incomplete("Incomplete or mismatched installed capture")
                for path, sha in project["source_hashes"].items():
                    if captured["source"].get(path) != sha:
                        raise Incomplete("Capture source provenance mismatch")
                for path, sha in captured["wiki"].items():
                    require_hash(resolve(base, project["wiki"]) / path, sha)
                if (
                    tree_hashes(source) != captured["source"]
                    or tree_hashes(resolve(base, project["wiki"])) != captured["wiki"]
                ):
                    raise Incomplete(
                        "The installed readers changed the caller source/wiki tree"
                    )
                sdk = read_json(mcp_capture / "result.json")
                require_installed_archive(
                    sdk.get("archive_origin", {}), artifact_sha256
                )
                expected_cases = [
                    c for c in read_json(capture / "cases.json") if c["adapter"]
                ]
                expected_digests = {
                    c["label"]: digest((capture / c["packet"]).read_bytes())
                    for c in expected_cases
                }
                if (
                    sdk.get("status") != "pass"
                    or not expected_digests
                    or {c["case"]: c["sha256"] for c in sdk["cases"]}
                    != expected_digests
                ):
                    raise Incomplete("Missing or mismatched actual MCP packet evidence")
                assessment = assess(
                    project, base, frontends, capture, observations, facts, claims
                )
                assessment["lane"] = lane
                (project_output / (lane + "-assessment.json")).write_bytes(
                    canonical_json(assessment)
                )
                results.append(
                    {
                        k: v
                        for k, v in assessment.items()
                        if k in {"status", "project", "lane", "counts"}
                    }
                )
        except (Incomplete, OSError, ValueError, KeyError) as error:
            results.append(
                {"project": project["id"], "status": "incomplete", "reason": str(error)}
            )
    state = (
        "incomplete"
        if any(r["status"] == "incomplete" for r in results)
        else "fail"
        if any(r["status"] == "fail" for r in results)
        else "pass"
    )
    result = {
        "status": state,
        "verifier_sha256": verifier,
        "manifest_sha256": digest(manifest_path.read_bytes()),
        "provider": manifest["provider"],
        "frontends": frontends.identities,
        "results": results,
        "preview_only": bool(manifest.get("preview_only")),
    }
    after = digest(
        b"".join(
            p.read_bytes()
            for p in sorted(Path(__file__).parent.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts
        )
    )
    if after != verifier:
        result["status"] = state = "incomplete"
        result["reason"] = "verifier-changed-during-run"
    lines = [
        "# Provider conformance result",
        "",
        f"Status: **{state}**",
        "",
        "| Project | Lane | Verdict | Counts / reason |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| {r['project']} | {r.get('lane', 'preflight')} | {r['status']} | {json.dumps(r.get('counts', r.get('reason')))} |"
        for r in results
    )
    (output / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result
