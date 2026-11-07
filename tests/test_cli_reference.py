"""Reference contracts reuse declarations without executing CLI behavior."""

from __future__ import annotations

import argparse
from copy import deepcopy
from importlib import resources
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator
import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services import cli_reference as reference
from llm_wiki_cli.services.knowledge_evidence import hash_json


PACKAGE = {"name": "example-app", "version": "1.2.3", "requires_python": ">=3.11"}


def positive(value):
    pytest.fail("reference generation must not run argument converters")


class RecordOnlyAction(argparse.Action):
    def __call__(self, *args, **kwargs):
        pytest.fail("reference generation must not execute actions")


def parser():
    value = argparse.ArgumentParser(
        prog="/private/host/argv.py", description="A <script> & [link](javascript:x)."
    )
    setattr(value, "reference_notes", "Compatibility remains supported.")
    value.add_argument("--route", default="/mcp", help="A declared HTTP route")
    value.add_argument("--hidden", help=argparse.SUPPRESS, default=argparse.SUPPRESS)
    value.add_argument("--record", action=RecordOnlyAction, type=positive, default=1)
    commands = value.add_subparsers(dest="command", required=True)
    options = {"deprecated": True} if sys.version_info >= (3, 13) else {}
    run = commands.add_parser("run", aliases=["r"], help="Run a thing", **options)
    setattr(run, "deprecated", True)
    setattr(run, "reference_notes", ["Keep existing invocation spellings."])
    run.set_defaults(requested_jobs=1)
    group = run.add_argument_group("Output", "Choose a presentation.")
    exclusive = group.add_mutually_exclusive_group(required=True)
    exclusive.add_argument("--json", action="store_const", const="json", dest="format")
    exclusive.add_argument("--text", action="store_const", const="text", dest="format")
    argument = run.add_argument(
        "values", nargs="+", type=int, choices=[1, 2], metavar="VALUE"
    )
    setattr(argument, "reference_notes", ["Declared integer choices."])
    setattr(argument, "deprecated", True)
    nested = run.add_subparsers(dest="operation")
    nested.add_parser("run", help="A repeated canonical path component")
    return value


def contract():
    return reference.build_cli_contract(parser(), package=PACKAGE, program="example")


def reseal(value):
    value["contract_id"] = hash_json(
        {key: item for key, item in value.items() if key != "contract_id"}
    )
    return value


def walk(command):
    yield command
    for child in command["commands"]:
        yield from walk(child)


def test_parser_capture_retains_nested_alias_option_and_group_contracts():
    value = contract()
    root, run, repeated = list(walk(value["root"]))
    assert value == contract()
    assert root["notes"] == ["Compatibility remains supported."]
    assert root["subcommands_required"] is True
    assert run["path"] == ["run"] and run["aliases"] == ["r"]
    assert repeated["path"] == ["run", "run"]
    assert run["help"] == "Run a thing" and run["deprecated"] is True
    assert run["defaults"] == {"requested_jobs": 1}
    arguments = {item["dest"]: item for item in root["arguments"]}
    assert arguments["route"]["default"]["value"] == "/mcp"
    assert arguments["hidden"]["hidden"] is True
    assert arguments["hidden"]["default"] == {"state": "suppressed", "value": None}
    assert arguments["record"]["action"] == "custom:RecordOnlyAction"
    assert arguments["record"]["type"] == "custom:positive"
    selected = next(item for item in run["arguments"] if item["dest"] == "values")
    assert selected["nargs"] == "+" and selected["choices"] == [1, 2]
    assert selected["type"] == "integer" and selected["metavar"] == "VALUE"
    assert selected["deprecated"] and selected["notes"] == ["Declared integer choices."]
    assert run["exclusive_groups"][0]["required"] is True
    assert len(run["exclusive_groups"][0]["members"]) == 2
    assert any(group["title"] == "Output" for group in run["groups"])
    assert "/private/host" not in json.dumps(value)


def test_exported_data_passes_the_packaged_closed_json_schema():
    schema = json.loads(
        resources.files("llm_wiki_cli.schemas")
        .joinpath("llm-wiki-cli-contract-v1.schema.json")
        .read_text()
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract())


@pytest.mark.parametrize("command_path", [[], ["run"]])
def test_saved_contract_requires_explicit_namespace_defaults(command_path):
    value = contract()
    node = value["root"]
    for name in command_path:
        node = next(child for child in node["commands"] if child["name"] == name)
    del node["defaults"]
    reseal(value)
    with pytest.raises(reference.CLIReferenceError, match="missing required fields"):
        reference.validate_cli_contract(value)
    with pytest.raises(reference.CLIReferenceError, match="missing required fields"):
        reference.parse_cli_contract(json.dumps(value))


def test_installed_reference_uses_public_parser_owner_and_is_independent_of_argv(
    monkeypatch,
):
    original = cli.build_cli_parser
    calls = []

    def build():
        calls.append(True)
        return original()

    monkeypatch.setattr(cli, "build_cli_parser", build)
    monkeypatch.setattr(sys, "argv", ["/private/arbitrary/runner"])
    first = reference.get_cli_contract()
    monkeypatch.setattr(sys, "argv", ["different-command", "unrelated"])
    second = reference.get_cli_contract()
    assert calls == [True, True] and first == second
    assert (
        first["program"] == "llm-wiki" and first["package"]["name"] == "agent-wiki-cli"
    )
    assert first["package"]["requires_python"] is None or isinstance(
        first["package"]["requires_python"], str
    )
    commands = {node["name"] for node in first["root"]["commands"]}
    assert {"sync", "knowledge", "docs", "reference"} <= commands
    sync = next(node for node in first["root"]["commands"] if node["name"] == "sync")
    assert sync["defaults"]["requested_jobs"] == 1
    assert "/private/arbitrary" not in json.dumps(first)


def test_reference_changes_when_owner_declarations_change():
    original = contract()
    changed = parser()
    changed.add_argument("--new-option", choices=("first", "second"), default="second")
    current = reference.build_cli_contract(changed, package=PACKAGE, program="example")
    assert current["contract_id"] != original["contract_id"]
    assert reference.render_cli_reference(current) != reference.render_cli_reference(
        original
    )


def test_markdown_is_deterministic_preserves_notes_and_treats_help_as_data():
    value = contract()
    before = deepcopy(value)
    output = reference.render_cli_reference(value)
    assert output == reference.render_cli_reference(value)
    assert value == before
    for expected in (
        "example run run",
        "Compatibility remains supported",
        "--hidden",
        "Hidden.",
        "Deprecated.",
        "Choose exactly one",
        "Namespace defaults",
    ):
        assert expected in output
    assert "<script>" not in output and "&lt;script&gt;" in output
    assert "[link](javascript:x)" not in output
    assert "/private/host" not in output


def test_markdown_code_spans_preserve_literal_reference_values():
    value = parser()
    value.add_argument("--template", default="<script> & `name`", metavar="<VALUE>")
    data = reference.build_cli_contract(value, package=PACKAGE, program="example")
    output = reference.render_cli_reference(data)
    assert "Requires Python ` >=3.11 `." in output
    assert "<script> & `name`" in output
    assert "<VALUE>" in output
    assert "&gt;=3.11" not in output
    assert "&lt;VALUE&gt;" not in output


@pytest.mark.parametrize(
    "damage",
    ["extra", "nested-extra", "hash", "path", "alias", "group", "default", "nonfinite"],
)
def test_supplied_contracts_fail_closed_on_tampering_or_inconsistent_data(damage):
    value = contract()
    if damage == "extra":
        value["unknown"] = True
    elif damage == "nested-extra":
        value["root"]["arguments"][0]["executable"] = "run.py"
    elif damage == "hash":
        value["package"]["version"] = "2.0.0"
    elif damage == "path":
        value["root"]["commands"][0]["path"] = ["wrong"]
    elif damage == "alias":
        value["root"]["commands"][0]["aliases"] = ["run"]
    elif damage == "group":
        value["root"]["groups"][0]["members"] = ["missing"]
    elif damage == "default":
        next(item for item in value["root"]["arguments"] if item["hidden"])["default"][
            "value"
        ] = "not-null"
    else:
        value["root"]["arguments"][0]["const"] = float("inf")
    if damage not in {"hash", "nonfinite"}:
        reseal(value)
    with pytest.raises(reference.CLIReferenceError):
        reference.validate_cli_contract(value)
    with pytest.raises(reference.CLIReferenceError):
        reference.render_cli_reference(value)


@pytest.mark.parametrize(
    "raw", [b"\xff", b'{"a":1,"a":2}', "NaN", "Infinity", "{", "{}"]
)
def test_contract_parser_requires_unique_finite_utf8_json(raw):
    with pytest.raises(reference.CLIReferenceError):
        reference.parse_cli_contract(raw)


def test_file_contract_roundtrip_and_non_llm_wiki_identity(tmp_path):
    value = contract()
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
    path = tmp_path / "application.json"
    path.write_bytes(raw)
    assert reference.parse_cli_contract(raw) == value
    assert reference.load_cli_contract(path) == value
    assert reference.load_cli_contract(path)["package"]["name"] == "example-app"


@pytest.mark.parametrize(
    "default", [object(), Path("/private/host/default"), lambda: None]
)
def test_unrepresentable_parser_defaults_are_not_stringified(default):
    value = argparse.ArgumentParser()
    value.add_argument("--value", default=default)
    with pytest.raises(reference.CLIReferenceError):
        reference.build_cli_contract(value, package=PACKAGE, program="example")
