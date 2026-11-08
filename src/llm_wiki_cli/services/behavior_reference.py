"""Versioned reference data derived from the llm-wiki provider's declarations."""

from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
from importlib import resources
import json
from pathlib import Path
from typing import Any

from .. import config
from . import cli_reference, current_contracts, skills, task_compact, task_contract
from .helper_runtime import resolve_helper_policy
from .knowledge_evidence import hash_json
from .knowledge_storage_io import read_guarded
from .validation import require_portable_relative_path


BEHAVIOR_FACTS_SCHEMA_VERSION = "llm-wiki-behavior-facts/v1"
BEHAVIOR_FACT_GROUPS = ("package", "setup", "storage", "task", "skills")
MAX_BEHAVIOR_FACTS_BYTES = 1024 * 1024
_SCHEMA_NAME = "llm-wiki-behavior-facts-v1.schema.json"


def _argument(root, commands, dest):
    try:
        node = root
        for command in commands:
            node = next(child for child in node["commands"] if child["name"] == command)
        return next(arg for arg in node["arguments"] if arg["dest"] == dest)
    except StopIteration as exc:
        raise ValueError(
            f"Missing CLI declaration for {' '.join(commands)}: {dest}"
        ) from exc


def _request_defaults(schema: str) -> dict[str, Any]:
    request, _ = task_contract.normalize_task_request({"schema_version": schema})
    return {
        "schema_version": request["schema_version"],
        "storage_options": request.get("storage_options"),
    }


def _task_facts(root, current) -> dict[str, Any]:
    default, _ = task_contract.normalize_task_request({})
    v2_empty, _ = task_contract.normalize_task_request(
        {
            "schema_version": task_contract.TASK_REQUEST_SCHEMA_V2,
            "storage_options": {},
        }
    )
    view = task_compact.normalize_view_options(
        None, ceiling=default["profile"]["settings"]["budget_tokens"]
    )
    return {
        "setup_and_upgrade": {
            key: current[key]
            for key in (
                "task_request",
                "compact_view",
                "storage_selection",
                "storage_receipt",
            )
        },
        "default_request": {
            key: default[key]
            for key in ("schema_version", "kind", "storage_options", "profile")
        },
        "explicit_v1": _request_defaults(task_contract.TASK_REQUEST_SCHEMA),
        "explicit_v2": {
            **_request_defaults(task_contract.TASK_REQUEST_SCHEMA_V2),
            "empty_storage_options": v2_empty["storage_options"],
        },
        "compact_view": {
            "default_schema": view["schema_version"],
            "explicit_schemas": [
                task_compact.VIEW_REQUEST_SCHEMA,
                task_compact.VIEW_REQUEST_SCHEMA_V2,
            ],
        },
        "cli_view": _argument(root, ("task-context",), "view")["default"]["value"],
    }


def get_behavior_facts() -> dict[str, Any]:
    """Return detached declarations for the loaded provider without inspecting a consumer wiki."""
    contract = cli_reference.get_cli_contract()
    root = contract["root"]
    current = current_contracts.current_contract_defaults()
    facts = {
        "package": contract["package"],
        "setup": {
            "policy": current["policy"],
            "wiki_directory": config.DEFAULT_WIKI_DIR,
            "new_project": dict(config._DEFAULT_CONFIG),
            "agents": sorted(config.AGENT_CHOICES),
            "reference_skill": skills.REFERENCE_SKILL_ID,
            "init_prepares_extractors": _argument(
                root, ("init",), "prepare_extractors"
            )["default"]["value"],
            "helper_policy": {
                "analysis": resolve_helper_policy(),
                "preview": resolve_helper_policy(preview=True),
                "offline": resolve_helper_policy(offline=True),
                "strict_read_only": resolve_helper_policy(strict_read_only=True),
            },
        },
        "storage": {
            "setup_and_upgrade": {
                key: current[key] for key in ("knowledge_format", "manifest_format")
            },
            "explicit_knowledge_formats": sorted(
                _argument(root, ("bootstrap",), "knowledge_format")["choices"]
            ),
            "migration_targets": sorted(
                _argument(root, ("knowledge", "migrate"), "to")["choices"]
            ),
            "export_formats": sorted(
                _argument(root, ("knowledge", "export-storage"), "to")["choices"]
            ),
            "observed_wiki_formats": None,
        },
        "task": _task_facts(root, current),
        "skills": [skill.to_dict() for skill in skills.list_bundled_skills()],
    }
    payload = {"schema_version": BEHAVIOR_FACTS_SCHEMA_VERSION, "facts": facts}
    result = {**payload, "contract_id": hash_json(payload)}
    validate_behavior_facts(result)
    return result


@lru_cache(maxsize=1)
def _schema() -> dict:
    return json.loads(
        resources.files("llm_wiki_cli.schemas")
        .joinpath(_SCHEMA_NAME)
        .read_text(encoding="utf-8")
    )


def _validate_paths(paths) -> None:
    for path in paths:
        require_portable_relative_path(path)


def validate_behavior_facts(contract: object) -> None:
    """Validate a saved provider declaration and its commitment independently of the live provider."""
    if isinstance(contract, Mapping):
        contract = dict(contract)
    cli_reference._json_tree(contract)
    if (
        len(
            json.dumps(
                contract, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
        )
        > MAX_BEHAVIOR_FACTS_BYTES
    ):
        raise ValueError("Behavior facts exceed the document byte limit")
    schema = _schema()
    cli_reference._validate_schema(contract, schema, schema, "behavior facts")
    assert isinstance(contract, dict)
    facts = contract["facts"]
    _validate_paths([facts["setup"]["wiki_directory"]])
    inventory = facts["skills"]
    ids = [skill["id"] for skill in inventory]
    if ids != sorted(set(ids)):
        raise ValueError("Behavior skill IDs must be unique and sorted")
    for skill in inventory:
        if skills.SKILL_MANIFEST_NAME not in skill["files"]:
            raise ValueError("Each bundled skill must include a skill manifest")
        _validate_paths(skill["files"])
    if facts["setup"]["new_project"]["agent"] not in facts["setup"]["agents"]:
        raise ValueError("The new-project agent must be one of the available agents")
    if (
        facts["task"]["compact_view"]["default_schema"]
        not in facts["task"]["compact_view"]["explicit_schemas"]
    ):
        raise ValueError("The default compact view must be a supported view schema")
    expected = hash_json(
        {key: value for key, value in contract.items() if key != "contract_id"}
    )
    if contract["contract_id"] != expected:
        raise ValueError("Behavior facts commitment does not match its contents")


def parse_behavior_facts(raw: bytes | str) -> dict[str, Any]:
    """Decode a bounded behavior contract with unique keys and finite JSON values."""
    if not isinstance(raw, (bytes, str)):
        raise ValueError("Behavior facts must be UTF-8 JSON")
    if len(raw) > MAX_BEHAVIOR_FACTS_BYTES:
        raise ValueError("Behavior facts exceed the document byte limit")
    data = raw if isinstance(raw, bytes) else raw.encode("utf-8")
    if len(data) > MAX_BEHAVIOR_FACTS_BYTES:
        raise ValueError("Behavior facts exceed the document byte limit")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=cli_reference._pairs)
        validate_behavior_facts(value)
    except RecursionError as exc:
        raise ValueError("Behavior facts exceed the nesting limit") from exc
    return value


def load_behavior_facts(path: str | Path) -> dict[str, Any]:
    """Read a saved behavior reference as bounded data."""
    return parse_behavior_facts(
        read_guarded(Path(path), MAX_BEHAVIOR_FACTS_BYTES).content
    )


def _rows(entries) -> list[str]:
    lines = ["| Setting | Value |", "| --- | --- |"]
    for label, value in entries:
        if value is None:
            display = "Omitted"
        elif isinstance(value, list):
            display = ", ".join(cli_reference._code(item) for item in value)
        else:
            display = cli_reference._code(
                value if isinstance(value, str) else json.dumps(value, sort_keys=True)
            )
        lines.append(f"| {label} | {display} |")
    return lines


def render_behavior_reference(contract: object) -> str:
    """Render a validated contract as Markdown using only its recorded facts."""
    validate_behavior_facts(contract)
    assert isinstance(contract, Mapping)
    facts = contract["facts"]
    package, setup, storage, task = (
        facts[key] for key in ("package", "setup", "storage", "task")
    )
    new = setup["new_project"]
    defaults = task["default_request"]
    lines = [
        "# llm-wiki behavior reference",
        "",
        "## Installed package",
        "",
        *_rows(
            [
                ("Distribution", package["name"]),
                ("Version", package["version"]),
                ("Requires Python", package["requires_python"]),
            ]
        ),
        "",
        "## Setup defaults",
        "",
        *_rows(
            [
                ("Setup policy", setup["policy"]),
                ("Wiki directory", setup["wiki_directory"]),
                ("New-project agent", new["agent"]),
                ("Available agents", setup["agents"]),
                ("Quality hints", new["quality_hints"]),
                ("Install reference skill", new["reference_skill"]),
                ("Reference skill", setup["reference_skill"]),
                ("Issue reporting", new["issue_reporting"]),
                ("Prepare extractors during init", setup["init_prepares_extractors"]),
            ]
        ),
        "",
        "### Helper preparation",
        "",
        *_rows(
            (key.replace("_", " ").capitalize(), value)
            for key, value in sorted(setup["helper_policy"].items())
        ),
        "",
        "## Native storage",
        "",
        *_rows(
            [
                (
                    "Setup and upgrade knowledge format",
                    storage["setup_and_upgrade"]["knowledge_format"],
                ),
                (
                    "Setup and upgrade manifest format",
                    storage["setup_and_upgrade"]["manifest_format"],
                ),
                (
                    "Explicit bootstrap knowledge formats",
                    storage["explicit_knowledge_formats"],
                ),
                ("Explicit migration targets", storage["migration_targets"]),
                ("Compatibility export formats", storage["export_formats"]),
            ]
        ),
        "",
        "Use `llm-wiki knowledge storage-check` to inspect an existing wiki's storage.",
        "",
        "## Task defaults",
        "",
        *_rows(
            [
                (
                    "Request recorded by setup and upgrade",
                    task["setup_and_upgrade"]["task_request"],
                ),
                (
                    "Compact view recorded by setup and upgrade",
                    task["setup_and_upgrade"]["compact_view"],
                ),
                (
                    "Storage selection recorded by setup and upgrade",
                    task["setup_and_upgrade"]["storage_selection"],
                ),
                (
                    "Storage receipt recorded by setup and upgrade",
                    task["setup_and_upgrade"]["storage_receipt"],
                ),
                ("Omitted request schema", defaults["schema_version"]),
                ("Task kind", defaults["kind"]),
                (
                    "Storage options for an omitted request schema",
                    defaults["storage_options"],
                ),
                ("CLI delivery view", task["cli_view"]),
                ("Default compact view schema", task["compact_view"]["default_schema"]),
                (
                    "Explicit compact view schemas",
                    task["compact_view"]["explicit_schemas"],
                ),
                ("Explicit v1 request", task["explicit_v1"]["schema_version"]),
                (
                    "Omitted storage options in explicit v1",
                    task["explicit_v1"]["storage_options"],
                ),
                ("Explicit v2 request", task["explicit_v2"]["schema_version"]),
                (
                    "Omitted storage options in explicit v2",
                    task["explicit_v2"]["storage_options"],
                ),
                (
                    "Empty storage options in explicit v2",
                    task["explicit_v2"]["empty_storage_options"],
                ),
            ]
        ),
        "",
        "### Default workflow profile",
        "",
        *_rows(
            [
                ("Schema", defaults["profile"]["schema_version"]),
                *sorted(defaults["profile"]["settings"].items()),
            ]
        ),
        "",
        "## Bundled skills",
        "",
    ]
    for skill in facts["skills"]:
        lines.extend(
            [
                "### " + cli_reference._code(skill["id"]),
                "",
                "Name " + cli_reference._code(skill["name"]),
                "",
                cli_reference._prose(skill["description"]),
                "",
                "Files "
                + ", ".join(cli_reference._code(name) for name in skill["files"]),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
