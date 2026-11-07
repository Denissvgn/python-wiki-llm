"""Explicit, inert reference inputs for public documentation review."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Mapping

from .knowledge_evidence import hash_json
from .publication_config import publication_path


MAX_REFERENCE_BYTES = 8 * 1024 * 1024
MAX_CAPTURE_BYTES = 64 * 1024 * 1024


def reference_identity(provider: str, configuration: Mapping[str, Any]) -> str:
    return hash_json({"provider": provider, "configuration": configuration})


def capture_reference_inputs(config, baseline, root, session):
    """Read current and former providers through the caller's guarded session."""
    declarations = {}
    for policy in ([] if baseline is None else [baseline["config"]]) + [config]:
        for provider, configuration in policy.get("reference_providers", {}).items():
            key = reference_identity(provider, configuration)
            declarations[key] = (provider, configuration)
    if not declarations:
        return {}
    from .cli_reference import get_cli_contract, parse_cli_contract

    captured = {}
    builtin = None
    total = 0
    for key, (provider, configuration) in sorted(declarations.items()):
        if configuration["kind"] == "llm-wiki-cli":
            if builtin is None:
                builtin = get_cli_contract()
            contract = deepcopy(builtin)
        else:
            path = publication_path(root, configuration["path"])
            contract = None
            if path.exists():
                raw = session.read(configuration["path"], MAX_REFERENCE_BYTES)
                contract = parse_cli_contract(raw)
        total += len(json.dumps(contract, sort_keys=True).encode("utf-8"))
        if total > MAX_CAPTURE_BYTES:
            raise ValueError(
                "Captured reference contracts exceed the publication budget"
            )
        captured[key] = {
            "provider": provider,
            "configuration": deepcopy(configuration),
            "contract": contract,
        }
    return captured


def recheck_reference_inputs(captured, root):
    """Recheck missing files and installed declarations after capture."""
    if not captured:
        return
    from .cli_reference import get_cli_contract

    builtin = None
    for reference in captured.values():
        configuration = reference["configuration"]
        if configuration["kind"] == "llm-wiki-cli":
            if builtin is None:
                builtin = get_cli_contract()
            if builtin != reference["contract"]:
                raise ValueError(
                    "Installed CLI declarations changed during publication capture"
                )
        elif (
            reference["contract"] is None
            and publication_path(root, configuration["path"]).exists()
        ):
            raise ValueError("Reference contract appeared during publication capture")


def reference_dependency_basis(dep, basis, providers):
    """Select one command subtree, retaining the provider's origin binding."""
    configuration = providers.get(dep["reference"])
    if configuration is None:
        return None
    key = reference_identity(dep["reference"], configuration)
    reference = basis.get("references", {}).get(key)
    if reference is None or reference["contract"] is None:
        return None
    contract = reference["contract"]
    path = dep.get("command", [])
    if not path:
        selected = contract["contract_id"]
    else:
        node = contract["root"]
        ancestors = []
        for token in path:
            ancestors.append(_ancestor_context(node))
            node = next(
                (
                    child
                    for child in node["commands"]
                    if token == child["name"] or token in child["aliases"]
                ),
                None,
            )
            if node is None:
                return None
        # Bind the declared subtree. Whole-contract dependencies additionally
        # bind release-version and unrelated-command metadata.
        selected = hash_json(
            {
                "schema_version": contract["schema_version"],
                "program": contract["program"],
                "package": {
                    key: value
                    for key, value in contract["package"].items()
                    if key != "version"
                },
                "command": node,
                "ancestors": ancestors,
            }
        )
    return {"provider": deepcopy(configuration), "contract": selected}


def _ancestor_context(command):
    """Global parser declarations also govern a selected descendant command."""
    arguments = [
        arg
        for arg in command["arguments"]
        if arg["action"] not in {"subparsers", "help", "version"}
    ]
    identities = {arg["id"]: f"argument:{index}" for index, arg in enumerate(arguments)}

    def project_groups(key, prefix):
        groups, identities_for_groups = [], {}
        for group in command[key]:
            members = [
                identities[member]
                for member in group["members"]
                if member in identities
            ]
            if members:
                identity = f"{prefix}:{len(groups)}"
                identities_for_groups[group["id"]] = identity
                groups.append({**group, "id": identity, "members": members})
        return groups, identities_for_groups

    groups, group_ids = project_groups("groups", "group")
    exclusive, exclusive_ids = project_groups("exclusive_groups", "exclusive")
    # IDs are local coordinates in the full declaration. Rebase retained IDs
    # so an excluded help/version action cannot shift a scoped review basis.
    arguments = [
        {
            **arg,
            "id": identities[arg["id"]],
            "group": group_ids[arg["group"]],
            "exclusive_groups": [
                exclusive_ids[identity] for identity in arg["exclusive_groups"]
            ],
        }
        for arg in arguments
    ]
    return {
        "path": command["path"],
        "aliases": command["aliases"],
        "deprecated": command["deprecated"],
        "notes": command["notes"],
        "defaults": command["defaults"],
        "settings": command["settings"],
        "arguments": arguments,
        "groups": groups,
        "exclusive_groups": exclusive,
    }
