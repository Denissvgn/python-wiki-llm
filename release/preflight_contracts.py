#!/usr/bin/env python3
"""Shared nonpromoting release contracts and early regression drivers.

Checking the registry reads declarations only. Executing a named group uses
maintained repository tests, never a command supplied by a plan or receipt.
Normal hosted qualification and its evidence admission remain authoritative.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any
import xml.etree.ElementTree as ET

SCHEMA = "agent-wiki-preflight-contracts/v1"
REGISTRY = "release/preflight-contracts.json"
WORKFLOW = ".github/workflows/release-qualification.yml"
MAX_BYTES = 4 * 1024 * 1024
JOB = re.compile(r"^  ([A-Za-z_][A-Za-z0-9_-]*):[ \t]*$", re.MULTILINE)
GROUPS: dict[str, tuple[str, ...]] = {
    "inventory": (
        "tests/test_source_selection.py",
        "tests/test_analysis_input_preflight.py",
        "tests/test_architecture_layers.py",
        "tests/test_api_exception_taxonomy.py",
    ),
    "defaults": (
        "tests/test_current_install_defaults.py",
        "tests/test_default_development_workflow.py",
        "tests/test_skills.py",
        "tests/test_evidence_recovery_guidance.py",
        "tests/test_agent_instruction_decisions.py",
        "tests/test_skill_policy_routes.py",
        "tests/test_helper_preparation.py",
        "tests/test_instruction_ownership.py",
        "tests/test_schema.py",
        "tests/test_schema_context_baselines.py",
        "tests/test_reference_skill_verifier.py",
        "tests/test_native_skill_preflight_and_reanchor.py",
        "tests/test_skill_contracts.py",
        "tests/test_wiki_reference_skill.py",
        "tests/test_skill_ownership_boundaries.py",
        "tests/test_skill_contracts_all.py",
    ),
    "packet": (
        "tests/test_context_packet.py",
        "tests/test_context_packet_knowledge.py",
        "tests/test_packet_field_policy.py",
        "tests/test_native_knowledge_semantics_docs.py",
    ),
    "storage": (
        "tests/test_knowledge_storage.py",
        "tests/test_wiki_review_snapshot.py",
        "tests/test_sync_recovery.py",
    ),
    "release": (
        "tests/test_preflight.py",
        "tests/test_preflight_contracts.py",
        "tests/test_preflight_runner.py",
        "tests/test_release_workflows.py",
        "tests/test_release_qualification.py",
        "tests/test_core_shards.py",
        "tests/test_core_shard_workflow.py",
        "tests/test_core_shard_runner.py",
    ),
    "portability": (
        "tests/test_readonly_subprocess_stdin.py",
        "tests/test_native_helper_path_diagnostics.py",
        "tests/test_python_go_path_diagnostics.py",
    ),
    "sdk": ("tests/test_mcp_sdk.py",),
    "action": ("tests/test_github_action.py", "tests/test_github_action_shell.py"),
    "incidents": (
        "tests/test_context_budget.py",
        "tests/test_context_knowledge_contract.py",
        "tests/test_developer_value_comparison.py::test_current_provider_adapter_exercises_frozen_cases",
        "tests/test_enriched_projection_resilience.py",
        "tests/test_sync_analysis_capture.py::test_unqualified_owner_skips_without_analysis_probe",
        "tests/test_knowledge_packs.py::test_logical_review_distinguishes_json_boolean_and_number",
        "tests/test_sync_runtime_regressions.py",
        "tests/test_real_caller_action_fixture.py",
        "tests/test_ts_extract.py::test_unresolved_import_producer_consumer_contract",
        "tests/test_ts_extract.py::test_dynamic_import_gap_survives_bootstrap_sync_and_strict_gates",
        "tests/test_ts_extract.py::test_released_unknown_evidence_guarded_upgrade_and_refresh",
        "tests/test_knowledge_evidence.py",
        "tests/test_extractor_inventory_contracts.py",
        "tests/test_sync_guard_diagnostics.py",
        "tests/test_captured_evidence_diagnostics.py",
        "tests/test_scoped_sync_repair.py",
        "tests/test_normalization_diagnostics.py",
        "tests/test_evidence_explanation_query.py",
    ),
}

OPTIONAL_JOBS = frozenset(
    {"dependency-controls", "dependency-warm", "discovery-allowlist", "ubuntu-shadow"}
)

CAPABILITIES = frozenset(
    {
        "python",
        "git",
        "hosted-actions",
        "native-linux",
        "native-macos",
        "native-windows",
        "node-typescript",
        "mcp-sdk",
        "loopback-sockets",
        "go",
        "rust",
        "haskell",
        "native-linux-x86_64",
        "oci-linux-amd64",
        "actionlint",
        "dependency-registry",
        "authenticated-hosted-policy",
        "native-linux-runtime-basis",
        "attestation-oidc",
        "package-registry",
    }
)

INCIDENT_IDS = frozenset(
    {
        "default-maintenance-static-cache",
        "missing-authority-not-empty",
        "legacy-selected-scaffold",
        "team-native-packed-scan",
        "rejected-sync-new-pages",
        "mcp-defaults-hosted-fixtures",
        "cli-default-packet",
        "action-current-schema-default",
        "packet-migration-contract",
        "current-provider-L01-oracle",
        "ranked-current-negative",
        "native-refresh-owned-default",
        "projection-bootstrap-isolation",
        "current-descriptor-omission",
        "release-target-metadata",
        "managed-packet-parity",
        "bundled-route-fallback",
        "product-census-membership",
        "unqualified-advisory-owner-cache",
        "installed-artifact-packet-parity",
        "budget-before-final-validation",
        "windows-action-file-uri",
        "typescript-thin-manifest-root",
        "javascript-gap-wire-contract",
        "unowned-javascript-skips",
        "logical-review-json-types",
        "native-shard-deep-git",
        "aggregation-output-order",
        "generator-refresh-review-convergence",
        "scoped-evidence-repair-atomicity",
        "captured-evidence-diagnosis-recovery",
    }
)


class ContractError(ValueError):
    """A local release contract is unknown, incomplete, or changed."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ContractError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _nonfinite(value: str) -> None:
    raise ContractError(f"non-finite JSON number: {value}")


def _read(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ContractError(f"required regular input is absent or unsafe: {path.name}")
    with path.open("rb") as stream:
        value = stream.read(MAX_BYTES + 1)
    if len(value) > MAX_BYTES:
        raise ContractError(f"contract input exceeds {MAX_BYTES} bytes: {path.name}")
    return value


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            _read(path), object_pairs_hook=_pairs, parse_constant=_nonfinite
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read contract {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("contract root must be an object")
    return value


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def workflow_declarations(repository_root: Path) -> tuple[bytes, dict[str, bytes]]:
    """Return exact job declarations without installing a YAML parser.

    The admitted workflow grammar has one top-level jobs mapping with two-space
    job names. Hashing complete blocks binds all steps, expressions, matrix and
    output contracts, including constructs outside the metadata projection.
    """
    raw = _read(repository_root / WORKFLOW)
    text = raw.decode("utf-8")
    if text.count("\njobs:\n") != 1:
        raise ContractError("workflow must declare exactly one jobs mapping")
    prefix, jobs_text = text.split("\njobs:\n")
    matches = list(JOB.finditer(jobs_text))
    if not matches or jobs_text[: matches[0].start()].strip():
        raise ContractError("unsupported qualification job declaration")
    jobs: dict[str, bytes] = {}
    for index, match in enumerate(matches):
        name = match.group(1)
        if name in jobs:
            raise ContractError(f"duplicate qualification producer: {name}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(jobs_text)
        jobs[name] = jobs_text[match.start() : end].encode("utf-8")
    return prefix.encode("utf-8"), jobs


def _job_field(block: bytes, key: str) -> str:
    lines = block.decode("utf-8").splitlines()
    for index, line in enumerate(lines):
        prefix = "    " + key + ":"
        if line.startswith(prefix):
            value = line[len(prefix) :].strip()
            tail = []
            for continuation in lines[index + 1 :]:
                if continuation.strip() and not continuation.startswith("      "):
                    break
                if continuation.strip():
                    tail.append(continuation.strip())
            return " ".join(
                ([value] if value not in {">-", ">", "|", "|-", ""} else []) + tail
            )
    return ""


def _selector_exists(repository_root: Path, selector: str) -> bool:
    parts = selector.split("::")
    path = repository_root / parts[0]
    if not path.is_file():
        return False
    if len(parts) == 1:
        return True
    nodes = ast.parse(_read(path)).body
    for part in parts[1:]:
        name = part.split("[")[0]
        matches = [
            node
            for node in nodes
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == name
        ]
        if len(matches) != 1:
            return False
        nodes = matches[0].body
    return True


def supported_agents(repository_root: Path) -> tuple[str, ...]:
    """Read the authoritative literal membership without importing provider code."""
    tree = ast.parse(_read(repository_root / "src/llm_wiki_cli/config.py"))
    values = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "AGENT_CHOICES"
            for target in node.targets
        )
    ]
    if len(values) != 1:
        raise ContractError("AGENT_CHOICES must have one authoritative declaration")
    agents = ast.literal_eval(values[0])
    if (
        not isinstance(agents, list)
        or not agents
        or any(not isinstance(a, str) or not a for a in agents)
        or len(set(agents)) != len(agents)
    ):
        raise ContractError("AGENT_CHOICES must be a nonempty unique literal list")
    return tuple(agents)


def contract_groups() -> dict[str, tuple[str, ...]]:
    return dict(GROUPS)


def validate_workflow_contracts(repository_root: Path) -> list[str]:
    """Refuse missing/extra producers and drift in any checked declaration."""
    try:
        registry = _load(repository_root / REGISTRY)
        if (
            set(registry)
            != {
                "schema_version",
                "workflow",
                "preamble_sha256",
                "jobs",
                "maintenance_dependencies",
                "groups",
                "incident_cases",
            }
            or registry["schema_version"] != SCHEMA
            or registry["workflow"] != WORKFLOW
        ):
            raise ContractError("unknown preflight registry schema or fields")
        prefix, actual = workflow_declarations(repository_root)
        rows = registry["jobs"]
        if not isinstance(rows, list) or not rows:
            raise ContractError("producer mapping must be a nonempty list")
        expected: dict[str, dict[str, Any]] = {}
        required_fields = {
            "id",
            "owner",
            "normal_required",
            "applicability",
            "gates",
            "needs",
            "environments",
            "capabilities",
            "cost",
            "timeout_minutes",
            "declaration_sha256",
            "expected_evidence",
            "condition",
            "matrix",
        }
        for row in rows:
            if not isinstance(row, dict) or set(row) != required_fields:
                raise ContractError("producer mapping has missing or extra fields")
            name = row["id"]
            if not isinstance(name, str) or name in expected:
                raise ContractError(
                    "producer mapping has invalid or duplicate identity"
                )
            if (
                not isinstance(row["owner"], str)
                or not row["owner"]
                or not (repository_root / row["owner"]).is_file()
            ):
                raise ContractError(f"producer {name} has no maintained command owner")
            if type(row["normal_required"]) is not bool or row["applicability"] not in {
                "normal",
                "diagnostic-only",
                "conditional-normal",
            }:
                raise ContractError(f"producer {name} has unknown applicability")
            for field in (
                "gates",
                "needs",
                "environments",
                "capabilities",
                "expected_evidence",
            ):
                if (
                    not isinstance(row[field], list)
                    or any(not isinstance(v, str) or not v for v in row[field])
                    or len(set(row[field])) != len(row[field])
                ):
                    raise ContractError(f"producer {name} has invalid {field}")
            if (
                not row["environments"]
                or not row["capabilities"]
                or not row["expected_evidence"]
                or row["cost"] not in {"cheap", "moderate", "heavy", "hosted"}
                or type(row["timeout_minutes"]) is not int
                or row["timeout_minutes"] <= 0
            ):
                raise ContractError(
                    f"producer {name} has incomplete capability or evidence contract"
                )
            if (
                not isinstance(row["condition"], str)
                or not isinstance(row["matrix"], dict)
                or not re.fullmatch(r"[0-9a-f]{64}", str(row["declaration_sha256"]))
            ):
                raise ContractError(
                    f"producer {name} has malformed declaration identity"
                )
            if any(
                not re.fullmatch(r"RD-(?:0[0-9]|1[0-3])", gate) for gate in row["gates"]
            ):
                raise ContractError(f"producer {name} has unknown release gate")
            if set(row["capabilities"]) - CAPABILITIES:
                raise ContractError(f"producer {name} has unknown capability")
            if row["normal_required"] is not (name not in OPTIONAL_JOBS):
                raise ContractError(
                    f"producer {name} changed mandatory normal qualification applicability"
                )
            expected[name] = row
        errors = []
        if registry["preamble_sha256"] != _digest(prefix):
            errors.append(
                "qualification inputs, permissions or global conditions changed"
            )
        for name in sorted(actual.keys() - expected.keys()):
            errors.append(f"unmapped qualification producer: {name}")
        for name in sorted(expected.keys() - actual.keys()):
            errors.append(f"mapped qualification producer is missing: {name}")
        for name in sorted(actual.keys() & expected.keys()):
            if expected[name]["declaration_sha256"] != _digest(actual[name]):
                errors.append(
                    f"qualification declaration changed: {name}; review commands, conditions, dependencies and evidence before updating its mapping"
                )
            condition = " ".join(expected[name]["condition"].split())
            if condition != " ".join(_job_field(actual[name], "if").split()):
                errors.append(f"qualification condition metadata differs: {name}")
            needs = re.findall(
                r"[A-Za-z_][A-Za-z0-9_-]*", _job_field(actual[name], "needs")
            )
            if needs != expected[name]["needs"]:
                errors.append(f"qualification dependencies metadata differs: {name}")
            runner = _job_field(actual[name], "runs-on")
            if runner == "${{ matrix.os }}":
                runners = []
                # Matrix fields retain their YAML indentation in the original block.
                runners = []
                for token in re.findall(
                    r"^ +os: ([^\n]+)", actual[name].decode(), re.MULTILINE
                ):
                    runners.extend(part.strip(" []\"'") for part in token.split(","))
            else:
                runners = [runner.strip("\"'")]
            if list(dict.fromkeys(runners)) != expected[name]["environments"]:
                errors.append(f"qualification environment metadata differs: {name}")
            timeout = _job_field(actual[name], "timeout-minutes") or "360"
            if str(expected[name]["timeout_minutes"]) != timeout:
                errors.append(f"qualification timeout metadata differs: {name}")
            if any(dep not in expected for dep in expected[name]["needs"]):
                errors.append(
                    f"qualification producer {name} has an unmapped dependency"
                )
        gates = {
            gate for row in rows if row["normal_required"] for gate in row["gates"]
        }
        if gates != {f"RD-{n:02d}" for n in range(14)}:
            errors.append("normal producer coverage must retain RD-00 through RD-13")
        if registry["groups"] != {name: list(paths) for name, paths in GROUPS.items()}:
            errors.append(
                "shared contract group declarations differ from maintained driver"
            )
        for name, paths in GROUPS.items():
            if any(not _selector_exists(repository_root, path) for path in paths):
                errors.append(f"contract group {name} has a missing maintained family")
        dependencies = registry["maintenance_dependencies"]
        if not isinstance(dependencies, list) or not dependencies:
            raise ContractError("maintenance dependencies must be explicitly mapped")
        if len(
            {row.get("path") for row in dependencies if isinstance(row, dict)}
        ) != len(dependencies):
            raise ContractError("duplicate maintenance dependency")
        for dependency in dependencies:
            if (
                not isinstance(dependency, dict)
                or set(dependency) != {"path", "owner", "purpose"}
                or any(not isinstance(v, str) or not v for v in dependency.values())
            ):
                raise ContractError("malformed maintenance dependency")
            if (
                not (repository_root / dependency["path"]).is_file()
                or not (repository_root / dependency["owner"]).is_file()
            ):
                errors.append(
                    f"missing maintenance dependency or owner: {dependency['path']}"
                )
        incidents = registry["incident_cases"]
        if not isinstance(incidents, list) or not incidents:
            raise ContractError("frozen incident corpus is absent")
        if {
            row.get("id") for row in incidents if isinstance(row, dict)
        } != INCIDENT_IDS or len(incidents) != len(INCIDENT_IDS):
            errors.append(
                "frozen incident corpus has missing, extra or duplicate dispositions"
            )
        for incident in incidents:
            if (
                not isinstance(incident, dict)
                or set(incident) != {"id", "selectors", "remaining_boundary"}
                or not isinstance(incident["id"], str)
                or not isinstance(incident["selectors"], list)
                or not incident["selectors"]
                or not isinstance(incident["remaining_boundary"], str)
            ):
                raise ContractError("malformed incident disposition")
            if any(
                not isinstance(selector, str)
                or not _selector_exists(repository_root, selector)
                for selector in incident["selectors"]
            ):
                errors.append(f"missing incident regression owner: {incident['id']}")
        policy_ast = ast.parse(
            _read(repository_root / "release/knowledge_maintenance.py")
        )
        constants = {}
        policy_inputs_seen = 0
        for node in policy_ast.body:
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                name = node.targets[0].id
                if name in {"LEAF_PATH", "POLICY_PATH"}:
                    constants[name] = ast.literal_eval(node.value)
                if name == "POLICY_INPUTS" and isinstance(
                    node.value, (ast.Tuple, ast.List)
                ):
                    policy_inputs_seen += 1
                    inputs = [
                        constants[element.id]
                        if isinstance(element, ast.Name)
                        else ast.literal_eval(element)
                        for element in node.value.elts
                    ]
                    missing = set(inputs) - {row["path"] for row in dependencies}
                    if missing:
                        errors.append(
                            "unmapped maintenance policy inputs: "
                            + ", ".join(sorted(missing))
                        )
        if policy_inputs_seen != 1:
            errors.append(
                "maintenance policy input membership must have one explicit declaration"
            )
        supported_agents(repository_root)
        return errors
    except (
        ContractError,
        OSError,
        UnicodeError,
        SyntaxError,
        ValueError,
        KeyError,
    ) as exc:
        return [str(exc)]


def qualification_contract(repository_root: Path) -> dict[str, Any]:
    errors = validate_workflow_contracts(repository_root)
    if errors:
        raise ContractError("; ".join(errors))
    value = _load(repository_root / REGISTRY)
    dependencies = [
        {**row, "sha256": _digest(_read(repository_root / row["path"]))}
        for row in value["maintenance_dependencies"]
    ]
    result = {
        **value,
        "maintenance_dependencies": dependencies,
        "supported_agents": list(supported_agents(repository_root)),
        "workflow_sha256": _digest(_read(repository_root / WORKFLOW)),
        "authority": "local-nonpromoting",
        "group_input_sha256": {
            path.split("::")[0]: _digest(_read(repository_root / path.split("::")[0]))
            for paths in GROUPS.values()
            for path in paths
        },
    }
    result["identity"] = _digest(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    )
    return result


def audit_agent_variants(repository_root: Path, junit: Path) -> list[str]:
    """Independently require every authoritative agent/fallback variant to pass."""
    root = ET.fromstring(_read(junit))
    names = [
        node.get("name", "")
        for node in root.iter("testcase")
        if not list(node.findall("skipped"))
        and not list(node.findall("failure"))
        and not list(node.findall("error"))
    ]
    required = {
        f"test_all_agents_init_and_upgrade_install_current_defaults[{fallback}-{agent}]"
        for agent in supported_agents(repository_root)
        for fallback in ("False", "True")
    }
    required |= {
        f"test_default_workflow_installation_and_upgrade_preserve_project_policy[{flavor}-{fallback}-{agent}]"
        for agent in supported_agents(repository_root)
        for fallback in ("False", "True")
        for flavor in ("posix-input", "windows-input")
    }
    required |= {
        f"test_installed_recovery_recipes_work_after_init_and_upgrade[{mode}-{agent}]"
        for agent in supported_agents(repository_root)
        for mode in ("skills", "inline")
    }
    return [
        f"agent/fallback variant must pass exactly once: {name}"
        for name in sorted(required)
        if names.count(name) != 1
    ]


def run_contract_groups(
    repository_root: Path,
    groups: list[str],
    output_dir: Path,
    *,
    python: str = ".venv/bin/python",
) -> dict[str, Any]:
    """Run serial independent groups, preserving every failure and skip.

    Caller owns scratch isolation. This adapter itself rejects occupied output
    roots, symlinks, unknown groups and ambient pytest option injection.
    """
    contract = qualification_contract(repository_root)
    if not groups or len(set(groups)) != len(groups) or set(groups) - GROUPS.keys():
        raise ContractError("contract groups must be known, unique and nonempty")
    if output_dir.exists() or output_dir.is_symlink():
        raise ContractError("contract output must be a fresh operation-owned directory")
    interpreter = Path(python)
    if not interpreter.is_absolute():
        interpreter = repository_root / interpreter
    if not interpreter.is_file():
        raise ContractError(
            "contract driver requires an explicit existing Python launcher"
        )
    output_dir.mkdir(parents=True, exist_ok=False)
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTEST_ADDOPTS", "PYTHONPATH", "PYTHONHOME"}
    }
    rows: list[dict[str, Any]] = []
    for group in groups:
        junit = output_dir / f"{group}.xml"
        command = [
            str(interpreter),
            "-m",
            "pytest",
            "-q",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
            "--strict-config",
            "--strict-markers",
            "-W",
            "error",
            "-o",
            "xfail_strict=true",
            *GROUPS[group],
            f"--junitxml={junit}",
        ]
        start = time.monotonic()
        with (output_dir / f"{group}.log").open("wb") as log:
            try:
                result = subprocess.run(
                    command,
                    cwd=repository_root,
                    env=environment,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=False,
                    timeout=1800,
                )
                returncode = result.returncode
            except subprocess.TimeoutExpired:
                returncode = -1
                log.write(b"\nContract group exceeded its 1800-second timeout.\n")
        errors = []
        counts = {"passed": 0, "skipped": 0, "failed": 0}
        if junit.is_file():
            try:
                for node in ET.fromstring(_read(junit)).iter("testcase"):
                    key = (
                        "skipped"
                        if node.find("skipped") is not None
                        else "failed"
                        if node.find("failure") is not None
                        or node.find("error") is not None
                        else "passed"
                    )
                    counts[key] += 1
                if group == "defaults":
                    errors.extend(audit_agent_variants(repository_root, junit))
            except (ET.ParseError, ContractError) as exc:
                errors.append(f"invalid JUnit: {exc}")
        else:
            errors.append("driver produced no JUnit")
        if not sum(counts.values()):
            errors.append("driver produced no collected cases")
        state = (
            "failed"
            if returncode or counts["failed"] or errors
            else "blocked"
            if counts["skipped"]
            else "passed"
        )
        rows.append(
            {
                "group": group,
                "state": state,
                "returncode": returncode,
                "elapsed_seconds": round(time.monotonic() - start, 6),
                "counts": counts,
                "errors": errors,
                "command": command,
                "junit": str(junit),
            }
        )
    state = (
        "failed"
        if any(r["state"] == "failed" for r in rows)
        else "blocked"
        if any(r["state"] == "blocked" for r in rows)
        else "passed"
    )
    value = {
        "schema_version": "agent-wiki-preflight-contract-results/v1",
        "authority": "local-nonpromoting",
        "contract_identity": contract["identity"],
        "state": state,
        "groups": rows,
    }
    (output_dir / "results.json").write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--repo", type=Path, default=Path.cwd())
    groups = subparsers.add_parser("groups")
    groups.add_argument("--repo", type=Path, default=Path.cwd())
    groups.add_argument(
        "--group", action="append", choices=tuple(GROUPS), required=True
    )
    groups.add_argument("--output", type=Path, required=True)
    groups.add_argument("--python", default=sys.executable)
    args = parser.parse_args(argv)
    try:
        value = (
            qualification_contract(args.repo)
            if args.operation == "check"
            else run_contract_groups(
                args.repo, args.group, args.output, python=args.python
            )
        )
        print(json.dumps(value, sort_keys=True, indent=2))
        return 0 if value.get("state", "passed") == "passed" else 1
    except (ContractError, OSError) as exc:
        print(
            json.dumps(
                {
                    "state": "blocked",
                    "authority": "local-nonpromoting",
                    "error": str(exc),
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
