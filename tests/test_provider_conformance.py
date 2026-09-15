"""Regression checks for independent, non-vacuous provider assessments."""

from copy import deepcopy
import json

import pytest

from tests.provider_conformance import python_ast
from tests.provider_conformance.frontends import Frontends
from tests.provider_conformance.inventory import (
    compare_inventory,
    compare_original,
    require_unique_facts,
)
from tests.provider_conformance.markdown import signature, tables
from tests.provider_conformance.model import (
    Finding,
    Incomplete,
    compare_sets,
    conclude,
    require_hash,
)
from tests.provider_conformance.trace import flow_findings, packet_entry


SOURCE = """class Box:
    value: str
    def run(self, first: int=3, /, second: str='a b', *, flag: bool=False) -> str:
        return second
"""


def inventory():
    return {
        "classes": [
            {
                "name": "Box",
                "kind": "class",
                "line": 1,
                "bases": [],
                "attributes": [{"name": "value", "line": 2, "type": "str"}],
                "methods": [
                    {
                        "name": "run",
                        "line": 3,
                        "is_async": False,
                        "params": [
                            {
                                "name": "first",
                                "kind": "positional_only",
                                "type": "int",
                                "default": "3",
                            },
                            {
                                "name": "second",
                                "kind": "positional_or_keyword",
                                "type": "str",
                                "default": "'a b'",
                            },
                            {
                                "name": "flag",
                                "kind": "keyword_only",
                                "type": "bool",
                                "default": "False",
                            },
                        ],
                        "return_type": "str",
                    }
                ],
            }
        ],
        "functions": [],
    }


def normalize(lang, mode, value):
    assert lang == "python"
    return python_ast.normalize(mode, value)


def findings(entry):
    return compare_inventory(
        python_ast.observe(SOURCE), entry, "python", normalize, path="model.py"
    )


def test_correct_source_contract_passes_without_target_execution():
    assert conclude(findings(inventory()))["status"] == "pass"
    source = "raise RuntimeError('do not execute')\n" + SOURCE
    assert python_ast.observe(source)["declarations"]


@pytest.mark.parametrize(
    "change,reason",
    [
        ("default", "parameter-default"),
        ("literal", "parameter-default"),
        ("order", "parameter-order-or-name"),
        ("kind", "parameter-kind"),
        ("arity", "parameter-count"),
        ("return", "declaration-return_type"),
        ("type", "declaration-type"),
        ("line", "declaration-coordinate"),
    ],
)
def test_corrupt_signature_is_rejected_for_its_actual_reason(change, reason):
    entry = inventory()
    method = entry["classes"][0]["methods"][0]
    if change == "default":
        method["params"][0]["default"] = "4"
    elif change == "literal":
        method["params"][1]["default"] = "'ab'"
    elif change == "order":
        method["params"].reverse()
    elif change == "kind":
        method["params"][0]["kind"] = "positional_or_keyword"
    elif change == "arity":
        method["params"].pop()
    elif change == "return":
        method["return_type"] = "int"
    elif change == "type":
        entry["classes"][0]["attributes"][0]["type"] = "int"
    else:
        method["line"] = 99
    assert reason in {f.reason for f in findings(entry) if f.status == "fail"}


@pytest.mark.parametrize("change", ["missing", "extra", "duplicate", "wrong-owner"])
def test_complete_census_rejects_wrong_declaration_sets(change):
    entry = inventory()
    if change == "missing":
        entry["classes"][0]["methods"] = []
    elif change == "extra":
        entry["functions"] = [{"name": "unexpected"}]
    elif change == "duplicate":
        entry["classes"].append(deepcopy(entry["classes"][0]))
    else:
        entry["classes"][0]["name"] = "Other"
    assert any(
        f.reason == "declaration-set-mismatch" and f.status == "fail"
        for f in findings(entry)
    )


def test_duplicate_overloads_require_the_frozen_coordinate():
    fact = {
        "id": "f1",
        "applicability": "supported",
        "selector": ["functions", "f"],
        "expected": {"return_type": "str"},
        "lines": [1, 1],
    }
    entry = {
        "functions": [
            {"name": "f", "line": 1, "return_type": "int"},
            {"name": "f", "line": 3, "return_type": "str"},
        ]
    }
    assert (
        compare_original(fact, entry, "python", normalize, "inventory").status == "fail"
    )
    entry["functions"][0]["return_type"] = "str"
    assert (
        compare_original(fact, entry, "python", normalize, "inventory").status == "pass"
    )


def test_identically_named_class_occurrences_do_not_share_member_ownership():
    source = "class Box:\n    first: int\nclass Box:\n    second: str\n"
    entry = {
        "classes": [
            {
                "name": "Box",
                "line": 1,
                "bases": [],
                "attributes": [{"name": "second", "line": 4, "type": "str"}],
            },
            {
                "name": "Box",
                "line": 3,
                "bases": [],
                "attributes": [{"name": "first", "line": 2, "type": "int"}],
            },
        ]
    }
    result = compare_inventory(
        python_ast.observe(source), entry, "python", normalize, path="model.py"
    )
    assert any(
        f.status == "fail" and f.reason == "declaration-set-mismatch" for f in result
    )


def test_installed_artifact_identity_is_required():
    from tests.provider_conformance.model import require_installed_archive

    with pytest.raises(Incomplete, match="frozen artifact"):
        require_installed_archive(
            {"archive_info": {"hashes": {"sha256": "old"}}}, "new"
        )
    require_installed_archive({"archive_info": {"hashes": {"sha256": "new"}}}, "new")


@pytest.mark.parametrize("missing", ["wheel", "sdist", "mcp-wheel", "mcp-sdist"])
def test_missing_required_consumer_lane_cannot_produce_a_green_summary(missing):
    from tests.provider_conformance.campaign import validate_manifest

    lanes = {name: name for name in ("wheel", "sdist", "mcp-wheel", "mcp-sdist")}
    lanes.pop(missing)
    manifest = {
        "schema_version": "provider-conformance/v1",
        "projects": [
            {
                "id": "control",
                "primary": ["model.py"],
                "source_hashes": {"model.py": "hash"},
            }
        ],
        "provider": {"interpreters": lanes},
    }
    with pytest.raises(Incomplete, match="consumer lanes"):
        validate_manifest(manifest)


def test_empty_and_duplicate_assessments_cannot_pass(tmp_path):
    with pytest.raises(Incomplete, match="Empty assessment"):
        conclude([])
    with pytest.raises(Incomplete, match="No required declarations"):
        compare_sets([], [], fact="empty", representation="inventory")
    with pytest.raises(Incomplete, match="Duplicate frozen"):
        require_unique_facts([{"id": "same"}, {"id": "same"}])
    path = tmp_path / "source.py"
    path.write_text("changed")
    with pytest.raises(Incomplete, match="provenance changed"):
        require_hash(path, "0" * 64)
    assert (
        conclude(
            [
                Finding("f", "inventory", "pass", "exists"),
                Finding("g", "native", "blocked", "missing"),
            ]
        )["status"]
        == "incomplete"
    )


def test_missing_compiler_is_incomplete_not_a_lexical_fallback(tmp_path):
    with pytest.raises(Incomplete, match="Explicit haskell"):
        Frontends({}, tmp_path).normalize("haskell", "type", "a -> b")


def test_markdown_signature_keeps_literal_spaces_defaults_and_parameter_kinds():
    parsed = signature(
        "(first: int = 3, /, second: str = 'a b', *, flag: bool = False) -> str",
        "python",
    )
    assert parsed["params"] == inventory()["classes"][0]["methods"][0]["params"]
    assert parsed["return_type"] == "str"
    rows = tables(
        "## Attributes\n\n| Name | Type | Default |\n|---|---|---|\n| `x` | `str \\| None` | `'a b'` |\n"
    )
    assert rows[0]["rows"][1] == ["x", "str | None", "'a b'"]


def test_empty_packets_and_undisclosed_downgrades_fail():
    packet = {"response": {"files": {}, "omitted_files": [], "format": "json"}}
    assert packet_entry(packet, "model.py")[1].status == "fail"
    packet["response"]["omitted_files"] = ["model.py"]
    assert packet_entry(packet, "model.py")[1].status == "bounded-omission"

    packet["response"]["files"] = {"model.py": {"detail": "slim"}}
    assert packet_entry(packet, "model.py")[1].status == "fail"
    packet["response"]["downgraded_files"] = {"model.py": "slim"}
    assert packet_entry(packet, "model.py")[1].status == "bounded-omission"


def test_import_and_module_facts_cannot_match_unrelated_prose():
    from tests.provider_conformance.trace import module_fact_present

    body = "# Example\n\n## Description\nData.Hashable\n\n## Imports\n\n| Module | Alias |\n|---|---|\n| `Data.Other` | H |\n"
    assert not module_fact_present(body, ["imports", "Data.Hashable"], {})
    assert module_fact_present(body, ["imports", "Data.Other"], {})
    assert not module_fact_present(body, ["module"], {"value": "Data.Hashable"})
    assert module_fact_present(
        body + "\n**Declared module:** `Data.Hashable`\n",
        ["module"],
        {"value": "Data.Hashable"},
    )


def test_flow_scope_excludes_nested_calls_and_shadowed_targets():
    source = """def target():
    pass
def outer(target):
    target()
    def nested():
        hidden()
def other():
    target()
"""
    observed = python_ast.calls(source)
    assert not any(c["caller"] == "outer" and c["callee"] == "hidden" for c in observed)
    assert (
        next(c for c in observed if c["caller"] == "outer")["resolution"]
        == "external-or-unresolved"
    )
    assert next(c for c in observed if c["caller"] == "other")["resolution"] == "local"
    flow = "```mermaid\nsequenceDiagram\n participant p0 as outer\n participant p1 as target\n p0->>p1: target\n```"
    assert flow_findings(flow, source, "flow")[0].status == "fail"
    assert (
        flow_findings(flow.replace("->>", "-->>"), source, "flow")[0].status == "pass"
    )


def test_cli_missing_manifest_emits_machine_readable_incomplete(tmp_path):
    from tests.provider_conformance.__main__ import main

    tools = tmp_path / "tools.json"
    tools.write_text("{}")
    output = tmp_path / "result.json"
    assert (
        main(
            [
                "--toolchains",
                str(tools),
                "--work",
                str(tmp_path / "work"),
                "--output",
                str(output),
            ]
        )
        == 2
    )
    assert json.loads(output.read_text())["status"] == "incomplete"


@pytest.mark.parametrize(
    "prose",
    [
        "package.module\n~~~~~~~~~~~~~~\n\nSource documentation.",
        "Example:\n```python\nprint('source only')",
        "Example:\n~~~~text\n``` is content within the tilde fence",
    ],
)
def test_unterminated_source_fence_cannot_swallow_generated_tables(
    tmp_path, monkeypatch, prose
):
    from llm_wiki_cli import api

    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "model.py").write_text(
        repr(prose) + "\n\nclass Box:\n    value: str\n", encoding="utf-8"
    )
    api.bootstrap_wiki(str(source), "wiki")
    body = (tmp_path / "wiki/modules/model.md").read_text(encoding="utf-8")
    assert any(
        t["section"] == "Classes" and any("Box" in row for row in t["rows"])
        for t in tables(body)
    )


def test_balanced_source_fences_are_preserved():
    from llm_wiki_cli.services.bootstrap_runtime import _sanitize_source_doc_markdown

    prose = "Example:\n````text\n``` is not the closing marker\n````\n\nMore prose."
    assert _sanitize_source_doc_markdown(prose) == prose
