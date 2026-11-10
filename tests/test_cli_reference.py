"""Reference contracts reuse declarations without executing CLI behavior."""

from __future__ import annotations

import argparse
from copy import deepcopy
from importlib import resources
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
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
    assert arguments["record"]["action"] == f"custom:{__name__}:RecordOnlyAction"
    assert arguments["record"]["type"] == f"custom:{__name__}:positive"
    selected = next(item for item in run["arguments"] if item["dest"] == "values")
    assert selected["nargs"] == "+" and selected["choices"] == [1, 2]
    assert selected["type"] == "integer" and selected["metavar"] == "VALUE"
    assert selected["deprecated"] and selected["notes"] == ["Declared integer choices."]
    assert run["exclusive_groups"][0]["required"] is True
    assert len(run["exclusive_groups"][0]["members"]) == 2
    assert any(group["title"] == "Output" for group in run["groups"])
    assert "/private/host" not in json.dumps(value)


def test_application_parsers_preserve_non_dash_prefixes_and_parsing_rules():
    value = argparse.ArgumentParser(
        prefix_chars="+", allow_abbrev=False, fromfile_prefix_chars="@"
    )
    value.add_argument("++value", default="guest")
    data = reference.build_cli_contract(value, package=PACKAGE, program="example")
    assert data["root"]["settings"] == {
        "prefix_chars": "+",
        "allow_abbrev": False,
        "fromfile_prefix_chars": "@",
    }
    assert any(
        argument["option_strings"] == ["++value"]
        for argument in data["root"]["arguments"]
    )
    output = reference.render_cli_reference(data)
    assert "Option prefixes: ` + `" in output
    assert "Long option abbreviations: disabled" in output
    assert "Argument file prefixes: ` @ `" in output
    data["root"]["settings"]["prefix_chars"] = "-"
    reseal(data)
    with pytest.raises(reference.CLIReferenceError, match="distinct flags"):
        reference.validate_cli_contract(data)


def test_custom_converter_module_changes_reopen_the_contract():
    def first(value):
        return "first:" + value

    def second(value):
        return "second:" + value

    first.__module__ = "app.first"
    second.__module__ = "app.second"
    first.__qualname__ = second.__qualname__ = "parse"
    contracts = []
    parsed = []
    for converter in (first, second):
        value = argparse.ArgumentParser()
        value.add_argument("--value", type=converter)
        contracts.append(
            reference.build_cli_contract(value, package=PACKAGE, program="example")
        )
        parsed.append(value.parse_args(["--value", "input"]).value)
    assert parsed == ["first:input", "second:input"]
    assert contracts[0]["contract_id"] != contracts[1]["contract_id"]
    assert contracts[0]["root"]["arguments"][1]["type"] == "custom:app.first:parse"
    assert contracts[1]["root"]["arguments"][1]["type"] == "custom:app.second:parse"


def test_custom_action_symbols_preserve_underscores_and_local_identity():
    class _Record(argparse.Action):
        def __call__(self, *args, **kwargs):
            pytest.fail("capture must not execute an action")

    class Record(_Record):
        pass

    contracts = []
    for action in (_Record, Record):
        value = argparse.ArgumentParser()
        value.add_argument("--record", action=action)
        data = reference.build_cli_contract(value, package=PACKAGE, program="example")
        assert data["root"]["arguments"][1]["action"] == (
            f"custom:{action.__module__}:{action.__qualname__}"
        )
        contracts.append(data)
    assert contracts[0]["contract_id"] != contracts[1]["contract_id"]


def test_custom_action_named_like_a_builtin_is_not_misclassified():
    class _StoreAction(argparse.Action):
        def __call__(self, *args, **kwargs):
            pytest.fail("capture must not execute an action")

    value = argparse.ArgumentParser()
    value.add_argument("--value", action=_StoreAction)
    data = reference.build_cli_contract(value, package=PACKAGE, program="example")
    assert data["root"]["arguments"][1]["action"] == (
        f"custom:{_StoreAction.__module__}:{_StoreAction.__qualname__}"
    )


def test_legacy_custom_symbols_remain_readable_and_change_on_new_capture():
    current = contract()
    legacy = deepcopy(current)
    argument = next(
        item for item in legacy["root"]["arguments"] if item["dest"] == "record"
    )
    argument["action"] = "custom:RecordOnlyAction"
    argument["type"] = "custom:positive"
    reseal(legacy)
    reference.validate_cli_contract(legacy)
    assert reference.parse_cli_contract(json.dumps(legacy)) == legacy
    assert (
        "custom:RecordOnlyAction / custom:positive"
        in reference.render_cli_reference(legacy)
    )
    assert legacy["contract_id"] != current["contract_id"]


@pytest.mark.parametrize(
    "settings",
    [{"prefix_chars": "+"}, {"allow_abbrev": False}, {"fromfile_prefix_chars": "@"}],
)
def test_parser_rule_changes_reopen_the_reference_contract(settings):
    original = reference.build_cli_contract(
        argparse.ArgumentParser(add_help=False), package=PACKAGE, program="example"
    )
    current = reference.build_cli_contract(
        argparse.ArgumentParser(add_help=False, **settings),
        package=PACKAGE,
        program="example",
    )
    assert current["contract_id"] != original["contract_id"]
    assert reference.render_cli_reference(current) != reference.render_cli_reference(
        original
    )


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


def test_markdown_choice_objects_are_identical_before_and_after_json_export():
    value = argparse.ArgumentParser()
    value.add_argument(
        "--value", type=json.loads, choices=[{"z": 1, "a": {"y": 2, "b": 3}}]
    )
    data = reference.build_cli_contract(value, package=PACKAGE, program="example")
    saved = reference.parse_cli_contract(json.dumps(data, sort_keys=True))
    assert data == saved
    assert reference.render_cli_reference(data) == reference.render_cli_reference(saved)


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


@pytest.mark.parametrize("compact", [False, True])
def test_cli_json_output_roundtrips_with_unicode_and_byte_limits(
    tmp_path, monkeypatch, compact
):
    value = argparse.ArgumentParser(description="é" * 1_400_000)
    expected = reference.build_cli_contract(value, package=PACKAGE, program="example")
    if compact:
        # Bound the accepted input tightly enough that pretty-print whitespace
        # would produce an unreadable artifact, even with UTF-8 serialization.
        monkeypatch.setattr(
            reference,
            "MAX_CLI_CONTRACT_BYTES",
            len(json.dumps(expected, ensure_ascii=False).encode("utf-8")),
        )
    monkeypatch.setattr(reference, "get_cli_contract", lambda: expected)
    destination = tmp_path / "reference.json"
    monkeypatch.setattr(
        "sys.argv", ["llm-wiki", "reference", "cli", "--output", str(destination)]
    )
    cli.main()
    assert destination.stat().st_size <= reference.MAX_CLI_CONTRACT_BYTES
    assert reference.load_cli_contract(destination) == expected
    markdown = tmp_path / "reference.md"
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "reference",
            "render",
            "--input",
            str(destination),
            "--format",
            "markdown",
            "--output",
            str(markdown),
        ],
    )
    cli.main()
    assert markdown.read_text(encoding="utf-8") == reference.render_cli_reference(
        expected
    )


def test_saved_renderer_preserves_input_through_case_aliases(tmp_path, monkeypatch):
    expected = contract()
    source = tmp_path / "reference.json"
    source.write_text(json.dumps(expected), encoding="utf-8")
    destination = tmp_path / "REFERENCE.json"
    aliases_input = destination.exists()
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "reference",
            "render",
            "--input",
            str(source),
            "--format",
            "markdown",
            "--output",
            str(destination),
        ],
    )
    if aliases_input:
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 2
    else:
        cli.main()
        assert destination.read_text(
            encoding="utf-8"
        ) == reference.render_cli_reference(expected)
    assert reference.load_cli_contract(source) == expected


@pytest.mark.parametrize(
    "default", [object(), Path("/private/host/default"), lambda: None]
)
def test_unrepresentable_parser_defaults_are_not_stringified(default):
    value = argparse.ArgumentParser()
    value.add_argument("--value", default=default)
    with pytest.raises(reference.CLIReferenceError):
        reference.build_cli_contract(value, package=PACKAGE, program="example")


@pytest.mark.parametrize("default", [
    PureWindowsPath(r"\private\host\default"),
    PureWindowsPath("C:private/host/default"),
    PureWindowsPath("C:/private/host/default"),
    PureWindowsPath(r"\\host\share\default"),
])
def test_host_anchored_windows_path_defaults_are_rejected(default, monkeypatch):
    monkeypatch.setattr(reference, "Path", PureWindowsPath)
    value = argparse.ArgumentParser()
    value.add_argument("--value", default=default)
    with pytest.raises(reference.CLIReferenceError):
        reference.build_cli_contract(value, package=PACKAGE, program="example")


@pytest.mark.parametrize("path_type, spelling, expected", [
    (PureWindowsPath, "relative/folder", "relative/folder"),
    (PurePosixPath, r"literal\name", r"literal\name"),
])
def test_relative_path_defaults_preserve_their_native_spelling(path_type, spelling, expected, monkeypatch):
    monkeypatch.setattr(reference, "Path", path_type)
    value = argparse.ArgumentParser()
    value.add_argument("--value", default=path_type(spelling))
    data = reference.build_cli_contract(value, package=PACKAGE, program="example")
    argument = next(item for item in data["root"]["arguments"] if item["dest"] == "value")
    assert argument["default"]["value"] == expected
