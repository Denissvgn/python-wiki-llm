"""Deterministic CLI reference data and inert Markdown from parser declarations."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from functools import lru_cache
import html
from importlib import resources
import json
import math
from pathlib import Path
import re
from typing import Any

from .. import _provider_package_identity
from .knowledge_evidence import hash_json
from .knowledge_storage_io import read_guarded


CLI_CONTRACT_SCHEMA_VERSION = "llm-wiki-cli-contract/v1"
_SCHEMA_NAME = "llm-wiki-cli-contract-v1.schema.json"
MAX_CLI_CONTRACT_BYTES = 8 * 1024 * 1024
_MAX_NODES = 100_000
_MAX_DEPTH = 32
_IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
_MODULE = re.compile(_IDENTIFIER + r"(?:\." + _IDENTIFIER + ")*")
_QUALNAME = re.compile(_IDENTIFIER + r"(?:\.(?:<locals>\.)?" + _IDENTIFIER + ")*")
_ACTIONS = {
    argparse._StoreAction: "store",
    argparse._StoreConstAction: "store_const",
    argparse._StoreTrueAction: "store_true",
    argparse._StoreFalseAction: "store_false",
    argparse._AppendAction: "append",
    argparse._AppendConstAction: "append_const",
    argparse._CountAction: "count",
    argparse._ExtendAction: "extend",
    argparse._HelpAction: "help",
    argparse._VersionAction: "version",
    argparse._SubParsersAction: "subparsers",
    argparse.BooleanOptionalAction: "boolean_optional",
}


class CLIReferenceError(ValueError):
    """CLI declarations or supplied reference data violate the portable contract."""


def _text(value: object) -> str | None:
    if value is None or value == argparse.SUPPRESS:
        return None
    if not isinstance(value, str):
        raise CLIReferenceError("Reference text must be a string or null")
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _notes(owner: object) -> list[str]:
    value = getattr(owner, "reference_notes", ())
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (tuple, list)) or not all(
        isinstance(item, str) for item in value
    ):
        raise CLIReferenceError("reference_notes must be text or a list of text")
    return [item.replace("\r\n", "\n").replace("\r", "\n") for item in value]


def _value(value: object, depth: int = 0) -> Any:
    if depth > _MAX_DEPTH:
        raise CLIReferenceError("Reference values exceed the supported nesting depth")
    if isinstance(value, Path):
        if value.is_absolute():
            raise CLIReferenceError(
                "Reference defaults cannot contain live absolute Path objects"
            )
        value = value.as_posix()
    if value is None or type(value) in {bool, int}:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return [_value(item, depth + 1) for item in value]
    if isinstance(value, Mapping) and all(isinstance(key, str) for key in value):
        return {key: _value(item, depth + 1) for key, item in value.items()}
    raise CLIReferenceError(
        "Reference values must be portable JSON data, not executable objects"
    )


def _custom_symbol(value: object) -> str:
    module = getattr(value, "__module__", None)
    qualname = getattr(value, "__qualname__", None)
    if (
        not isinstance(module, str)
        or not _MODULE.fullmatch(module)
        or not isinstance(qualname, str)
        or not _QUALNAME.fullmatch(qualname)
    ):
        raise CLIReferenceError(
            "Custom parser declarations require stable module and qualified names"
        )
    return "custom:" + module + ":" + qualname


def _symbol(value: object) -> str | None:
    if value is None:
        return None
    if value in (str, int, float, bool, Path):
        return {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            Path: "path",
        }[value]
    return _custom_symbol(value)


def _argument(action, identity, group, exclusive):
    action_name = _ACTIONS.get(type(action))
    if action_name is None:
        action_name = _custom_symbol(type(action))
    nargs = action.nargs
    if nargs == argparse.REMAINDER:
        nargs = "remainder"
    elif nargs == argparse.PARSER:
        nargs = "parser"
    choices = action.choices
    if choices is not None:
        choices = [_value(item) for item in choices]
        if isinstance(action.choices, (set, frozenset)):
            choices.sort(key=lambda item: json.dumps(item, sort_keys=True))
    default_suppressed = action.default == argparse.SUPPRESS
    return {
        "id": identity,
        "dest": action.dest,
        "option_strings": list(action.option_strings),
        "positional": not bool(action.option_strings),
        "required": bool(action.required),
        "action": action_name,
        "type": _symbol(action.type),
        "nargs": nargs,
        "default": {
            "state": "suppressed" if default_suppressed else "value",
            "value": None if default_suppressed else _value(action.default),
        },
        "const": _value(action.const),
        "choices": choices,
        "metavar": _value(action.metavar),
        "help": _text(action.help),
        "hidden": action.help == argparse.SUPPRESS,
        "deprecated": bool(getattr(action, "deprecated", False)),
        "notes": _notes(action),
        "group": group,
        "exclusive_groups": exclusive,
        "version": _text(getattr(action, "version", None)),
    }


def _command(parser, name, path, *, help_text=None, deprecated=False, seen=None):
    seen = set() if seen is None else seen
    if id(parser) in seen or len(path) > 16:
        raise CLIReferenceError(
            "CLI parser has a cyclic or excessively deep command tree"
        )
    seen = seen | {id(parser)}
    identities = {
        id(action): f"argument:{index}" for index, action in enumerate(parser._actions)
    }
    groups, group_by_action = [], {}
    for index, group in enumerate(parser._action_groups):
        key = f"group:{index}"
        members = [identities[id(action)] for action in group._group_actions]
        groups.append(
            {
                "id": key,
                "title": _text(group.title),
                "description": _text(group.description),
                "members": members,
            }
        )
        group_by_action.update({id(action): key for action in group._group_actions})
    exclusive, exclusive_by_action = [], {}
    for index, group in enumerate(parser._mutually_exclusive_groups):
        key = f"exclusive:{index}"
        exclusive.append(
            {
                "id": key,
                "required": bool(group.required),
                "members": [identities[id(action)] for action in group._group_actions],
            }
        )
        for action in group._group_actions:
            exclusive_by_action.setdefault(id(action), []).append(key)
    arguments, commands = [], []
    required = False
    for action in parser._actions:
        arguments.append(
            _argument(
                action,
                identities[id(action)],
                group_by_action.get(id(action)),
                exclusive_by_action.get(id(action), []),
            )
        )
        if not isinstance(action, argparse._SubParsersAction):
            continue
        required = required or bool(action.required)
        helps = {item.dest: item.help for item in action._choices_actions}
        children = {}
        for child_name, child in action.choices.items():
            children.setdefault(id(child), (child, []))[1].append(child_name)
        for child, names in children.values():
            canonical, *aliases = names
            node = _command(
                child,
                canonical,
                [*path, canonical],
                help_text=helps.get(canonical),
                deprecated=any(
                    item in getattr(action, "_deprecated", ()) for item in names
                ),
                seen=seen,
            )
            node["aliases"] = aliases
            commands.append(node)
    return {
        "name": name,
        "path": path,
        "aliases": [],
        "help": _text(help_text),
        "description": _text(parser.description),
        "epilog": _text(parser.epilog),
        "deprecated": deprecated or bool(getattr(parser, "deprecated", False)),
        "notes": _notes(parser),
        "arguments": arguments,
        "groups": groups,
        "exclusive_groups": exclusive,
        "commands": commands,
        "subcommands_required": required,
        "defaults": _value(dict(parser._defaults)),
        "settings": {
            "prefix_chars": parser.prefix_chars,
            "allow_abbrev": parser.allow_abbrev,
            "fromfile_prefix_chars": parser.fromfile_prefix_chars,
        },
    }


def build_cli_contract(
    parser: argparse.ArgumentParser, *, package: Mapping[str, Any], program: str
) -> dict[str, Any]:
    """Capture declarations without parsing arguments or executing application code."""
    if not isinstance(parser, argparse.ArgumentParser):
        raise CLIReferenceError("Reference generation requires an ArgumentParser")
    payload = {
        "schema_version": CLI_CONTRACT_SCHEMA_VERSION,
        "package": _value(dict(package)),
        "program": program,
        "root": _command(parser, program, []),
    }
    result = {**payload, "contract_id": hash_json(payload)}
    validate_cli_contract(result)
    return result


def get_cli_contract() -> dict[str, Any]:
    """Describe the installed llm-wiki CLI through its public parser owner."""
    from ..cli import build_cli_parser

    return build_cli_contract(
        build_cli_parser(), package=_provider_package_identity(), program="llm-wiki"
    )


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    return json.loads(
        resources.files("llm_wiki_cli.schemas")
        .joinpath(_SCHEMA_NAME)
        .read_text(encoding="utf-8")
    )


def _json_tree(value: object, depth: int = 0, budget=None) -> None:
    budget = [_MAX_NODES] if budget is None else budget
    budget[0] -= 1
    if budget[0] < 0 or depth > _MAX_DEPTH:
        raise CLIReferenceError("CLI contract exceeds its structural bounds")
    if value is None or type(value) in {str, int, bool}:
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for item in value:
            _json_tree(item, depth + 1, budget)
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for item in value.values():
            _json_tree(item, depth + 1, budget)
        return
    raise CLIReferenceError("CLI contract requires finite JSON data")


def _matches_type(value, kind):
    return {
        "null": value is None,
        "boolean": type(value) is bool,
        "string": type(value) is str,
        "integer": type(value) is int,
        "number": type(value) in {int, float},
        "array": type(value) is list,
        "object": type(value) is dict,
    }[kind]


def _validate_schema(value, rule, root, field):
    if "$ref" in rule:
        return _validate_schema(
            value, root["$defs"][rule["$ref"].rsplit("/", 1)[1]], root, field
        )
    if "anyOf" in rule:
        for candidate in rule["anyOf"]:
            try:
                _validate_schema(value, candidate, root, field)
                return
            except CLIReferenceError:
                pass
        raise CLIReferenceError(field + " has an invalid value")
    kinds = rule.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    if kinds and not any(_matches_type(value, kind) for kind in kinds):
        raise CLIReferenceError(field + " has an invalid type")
    if (
        "const" in rule
        and value != rule["const"]
        or "enum" in rule
        and value not in rule["enum"]
    ):
        raise CLIReferenceError(field + " has an unsupported value")
    if isinstance(value, str):
        if (
            len(value) < rule.get("minLength", 0)
            or "pattern" in rule
            and not re.fullmatch(rule["pattern"], value)
        ):
            raise CLIReferenceError(field + " has invalid text")
    if type(value) is int and value < rule.get("minimum", value):
        raise CLIReferenceError(field + " is below its minimum")
    if isinstance(value, dict):
        properties = rule.get("properties", {})
        if set(rule.get("required", [])) - set(value):
            raise CLIReferenceError(field + " is missing required fields")
        extra = set(value) - set(properties)
        additional = rule.get("additionalProperties", True)
        if extra and additional is False:
            raise CLIReferenceError(field + " has unknown fields")
        for key, item in value.items():
            selected = properties.get(
                key, additional if isinstance(additional, dict) else {}
            )
            _validate_schema(item, selected, root, field + "." + key)
    if isinstance(value, list):
        if rule.get("uniqueItems") and len(
            {json.dumps(item, sort_keys=True) for item in value}
        ) != len(value):
            raise CLIReferenceError(field + " contains duplicate items")
        for index, item in enumerate(value):
            _validate_schema(item, rule.get("items", {}), root, field + f"[{index}]")


def _validate_command(node, expected_path, program):
    if node["path"] != expected_path or not expected_path and node["name"] != program:
        raise CLIReferenceError("Command path differs from its declared parent")
    arguments = {item["id"]: item for item in node["arguments"]}
    groups = {item["id"]: item for item in node["groups"]}
    exclusive = {item["id"]: item for item in node["exclusive_groups"]}
    if (
        len(arguments) != len(node["arguments"])
        or len(groups) != len(node["groups"])
        or len(exclusive) != len(node["exclusive_groups"])
    ):
        raise CLIReferenceError("Command argument/group identities must be distinct")
    options = set()
    for argument in arguments.values():
        if argument["positional"] != (not argument["option_strings"]):
            raise CLIReferenceError("Positional argument flags disagree")
        for flag in argument["option_strings"]:
            if (
                not flag.startswith(tuple(node["settings"]["prefix_chars"]))
                or flag in options
            ):
                raise CLIReferenceError("Option names must be distinct flags")
            options.add(flag)
        if (
            argument["default"]["state"] == "suppressed"
            and argument["default"]["value"] is not None
        ):
            raise CLIReferenceError("Suppressed defaults must carry a null value")
        group = argument["group"]
        if group is not None and (
            group not in groups or argument["id"] not in groups[group]["members"]
        ):
            raise CLIReferenceError("Argument references an inconsistent group")
        for key in argument["exclusive_groups"]:
            if key not in exclusive or argument["id"] not in exclusive[key]["members"]:
                raise CLIReferenceError(
                    "Argument references an inconsistent exclusive group"
                )
    for group in [*groups.values(), *exclusive.values()]:
        if len(set(group["members"])) != len(group["members"]) or set(
            group["members"]
        ) - set(arguments):
            raise CLIReferenceError(
                "Group references duplicate or unknown argument identities"
            )
        for member in group["members"]:
            argument = arguments[member]
            if group["id"] in groups and argument["group"] != group["id"]:
                raise CLIReferenceError("Group membership disagrees with its argument")
            if (
                group["id"] in exclusive
                and group["id"] not in argument["exclusive_groups"]
            ):
                raise CLIReferenceError(
                    "Exclusive membership disagrees with its argument"
                )
    names = set()
    for child in node["commands"]:
        for name in [child["name"], *child["aliases"]]:
            if name in names:
                raise CLIReferenceError(
                    "Sibling command names and aliases must be distinct"
                )
            names.add(name)
        _validate_command(child, [*expected_path, child["name"]], program)
    selectors = [item for item in arguments.values() if item["action"] == "subparsers"]
    if node["subcommands_required"] != any(item["required"] for item in selectors):
        raise CLIReferenceError("Subcommand requirement disagrees with its declaration")
    if node["commands"] and not selectors:
        raise CLIReferenceError("Nested commands require a subparser declaration")
    if (
        selectors
        and set(value for item in selectors for value in item["choices"] or []) != names
    ):
        raise CLIReferenceError(
            "Subparser choices disagree with command names and aliases"
        )


def validate_cli_contract(contract: object) -> None:
    """Validate closed portable reference data and its complete commitment."""
    try:
        _json_tree(contract)
        encoded = json.dumps(contract, ensure_ascii=False, allow_nan=False).encode(
            "utf-8"
        )
        if len(encoded) > MAX_CLI_CONTRACT_BYTES:
            raise CLIReferenceError("CLI contract exceeds its byte bound")
        schema = _schema()
        _validate_schema(contract, schema, schema, "contract")
        assert isinstance(contract, dict)
        _validate_command(contract["root"], [], contract["program"])
        if contract["contract_id"] != hash_json(
            {key: value for key, value in contract.items() if key != "contract_id"}
        ):
            raise CLIReferenceError(
                "CLI contract commitment does not match its contents"
            )
    except CLIReferenceError:
        raise
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        RecursionError,
        UnicodeError,
    ) as exc:
        raise CLIReferenceError("CLI contract is invalid") from exc


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise CLIReferenceError("CLI contract JSON contains duplicate keys")
        value[key] = item
    return value


def parse_cli_contract(raw: bytes | str) -> dict[str, Any]:
    """Validate exact observed UTF-8 JSON bytes without reopening their source."""
    try:
        if not isinstance(raw, (bytes, str)):
            raise CLIReferenceError("CLI contract input must be UTF-8 bytes or text")
        if (
            len(raw if isinstance(raw, bytes) else raw.encode("utf-8"))
            > MAX_CLI_CONTRACT_BYTES
        ):
            raise CLIReferenceError("CLI contract exceeds its byte bound")
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        value = json.loads(text, object_pairs_hook=_pairs)
        validate_cli_contract(value)
        return value
    except CLIReferenceError:
        raise
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        raise CLIReferenceError("CLI contract file is invalid") from exc


def load_cli_contract(path: str | Path) -> dict[str, Any]:
    """Read one guarded contract file as data; never load an application CLI."""
    try:
        return parse_cli_contract(
            read_guarded(Path(path), MAX_CLI_CONTRACT_BYTES).content
        )
    except CLIReferenceError:
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise CLIReferenceError("CLI contract file is invalid") from exc


def _prose(value: str) -> str:
    value = html.escape(value, quote=False)
    return re.sub(r"([\\`*_{}\[\]#|!])", r"\\\1", value).replace("\n", "<br>")


def _code(value: object) -> str:
    text = str(value).replace("\r", "\\r").replace("\n", "\\n")
    fence = "`" * (max((len(run) for run in re.findall(r"`+", text)), default=0) + 1)
    return fence + " " + text.replace("|", "\\|") + " " + fence


def render_cli_reference(contract: object) -> str:
    """Render validated metadata deterministically, including hidden declarations."""
    validate_cli_contract(contract)
    assert isinstance(contract, dict)
    package, program = contract["package"], contract["program"]
    lines = [
        f"# {_prose(program)} command reference",
        "",
        "Package: " + _code(package["name"] + " " + package["version"]) + ".",
        "",
    ]
    if package["requires_python"] is not None:
        lines.extend(["Requires Python " + _code(package["requires_python"]) + ".", ""])

    def render(command):
        label = " ".join([program, *command["path"]])
        lines.extend(["## " + _code(label), ""])
        settings = command["settings"]
        lines.extend(
            [
                "Option prefixes: "
                + _code(settings["prefix_chars"])
                + ". Long option abbreviations: "
                + ("enabled" if settings["allow_abbrev"] else "disabled")
                + ". Argument file prefixes: "
                + (
                    _code(settings["fromfile_prefix_chars"])
                    if settings["fromfile_prefix_chars"]
                    else "disabled"
                )
                + ".",
                "",
            ]
        )
        for key in ("help", "description"):
            if command[key]:
                lines.extend([_prose(command[key]), ""])
        if command["aliases"]:
            lines.extend(
                [
                    "Aliases: "
                    + ", ".join(_code(value) for value in command["aliases"])
                    + ".",
                    "",
                ]
            )
        if command["deprecated"]:
            lines.extend(["Deprecated command.", ""])
        for note in command["notes"]:
            lines.extend([_prose(note), ""])
        if command.get("defaults"):
            lines.extend(
                [
                    "Namespace defaults: "
                    + _code(
                        json.dumps(
                            command["defaults"], ensure_ascii=False, sort_keys=True
                        )
                    )
                    + ".",
                    "",
                ]
            )
        if command["arguments"]:
            lines.extend(
                [
                    "| Argument | Action / type | Values | Required | Default | Help |",
                    "| --- | --- | --- | --- | --- | --- |",
                ]
            )
            for argument in command["arguments"]:
                flags = ", ".join(argument["option_strings"]) or argument["dest"]
                metadata_text = argument["action"] + (
                    " / " + argument["type"] if argument["type"] else ""
                )
                values = "nargs=" + json.dumps(argument["nargs"])
                if argument["choices"] is not None:
                    values += "; choices=" + json.dumps(
                        argument["choices"], ensure_ascii=False, sort_keys=True
                    )
                if argument["metavar"] is not None:
                    values += "; metavar=" + json.dumps(
                        argument["metavar"], ensure_ascii=False
                    )
                if argument["const"] is not None or argument["action"] in {
                    "store_const",
                    "append_const",
                }:
                    values += "; const=" + json.dumps(
                        argument["const"], ensure_ascii=False, sort_keys=True
                    )
                if argument["version"] is not None:
                    values += "; version=" + argument["version"]
                default = argument["default"]
                default_text = (
                    "suppressed"
                    if default["state"] == "suppressed"
                    else json.dumps(
                        default["value"], ensure_ascii=False, sort_keys=True
                    )
                )
                help_text = argument["help"] or ""
                markers = (["Hidden."] if argument["hidden"] else []) + (
                    ["Deprecated."] if argument["deprecated"] else []
                )
                help_text = " ".join([help_text, *markers, *argument["notes"]]).strip()
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _code(flags),
                            _code(metadata_text),
                            _code(values),
                            "yes" if argument["required"] else "no",
                            _code(default_text),
                            _prose(help_text),
                        ]
                    )
                    + " |"
                )
            lines.append("")
        for group in command["groups"]:
            if group["members"]:
                flags = [
                    ", ".join(item["option_strings"]) or item["dest"]
                    for item in command["arguments"]
                    if item["id"] in group["members"]
                ]
                lines.extend(
                    [
                        _prose(group["title"] or "Arguments")
                        + ": "
                        + ", ".join(_code(value) for value in flags)
                        + ".",
                        "",
                    ]
                )
                if group["description"]:
                    lines.extend([_prose(group["description"]), ""])
        for group in command["exclusive_groups"]:
            names = [
                ", ".join(item["option_strings"]) or item["dest"]
                for item in command["arguments"]
                if item["id"] in group["members"]
            ]
            lines.extend(
                [
                    (
                        "Choose exactly one: "
                        if group["required"]
                        else "Mutually exclusive: "
                    )
                    + ", ".join(_code(value) for value in names)
                    + ".",
                    "",
                ]
            )
        if command["epilog"]:
            lines.extend([_prose(command["epilog"]), ""])
        for child in command["commands"]:
            render(child)

    render(contract["root"])
    return "\n".join(lines).rstrip() + "\n"
