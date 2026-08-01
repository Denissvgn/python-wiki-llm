"""Calibration package-boundary and compatibility regression tests."""

from __future__ import annotations

import base64
import importlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

import pytest


CALIBRATION_PACKAGE = "llm_wiki_cli.services.calibration"
LEGACY_CALIBRATION_PREFIX = "llm_wiki_cli.services.documentation_calibration"
MODULE_PAIRS = (
    (
        "llm_wiki_cli.services.documentation_calibration",
        f"{CALIBRATION_PACKAGE}.contracts",
    ),
    (
        "llm_wiki_cli.services.documentation_calibration_broker",
        f"{CALIBRATION_PACKAGE}.broker",
    ),
    (
        "llm_wiki_cli.services.documentation_calibration_controller",
        f"{CALIBRATION_PACKAGE}.controller",
    ),
    (
        "llm_wiki_cli.services.documentation_calibration_host_broker",
        f"{CALIBRATION_PACKAGE}.host_broker",
    ),
)


def _run_isolation_script(script: str) -> dict:
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_base_cli_import_and_parser_construction_do_not_load_calibration() -> None:
    script = """
import json
import sys
import tempfile

import llm_wiki_cli.cli as cli

prefix = "llm_wiki_cli.services.calibration"
loaded = lambda: sorted(
    name for name in sys.modules if name == prefix or name.startswith(prefix + ".")
)
before_parser = loaded()
parser = cli._build_parser()
after_parser = loaded()
with tempfile.TemporaryDirectory() as root:
    args = parser.parse_args(
        ["docs", "calibration", "status", "--root", root]
    )
    exit_code = None
    try:
        cli._dispatch_command(args)
    except SystemExit as exc:
        exit_code = exc.code
after_calibration_command = loaded()
print(
    json.dumps(
        {
            "before_parser": before_parser,
            "after_parser": after_parser,
            "after_calibration_command": after_calibration_command,
            "exit_code": exit_code,
        },
        sort_keys=True,
    )
)
"""

    result = _run_isolation_script(script)

    assert result["before_parser"] == []
    assert result["after_parser"] == []
    assert result["exit_code"] == 1
    assert CALIBRATION_PACKAGE in result["after_calibration_command"]
    assert (
        f"{CALIBRATION_PACKAGE}.controller"
        in result["after_calibration_command"]
    )


def test_public_api_import_does_not_load_calibration() -> None:
    result = _run_isolation_script(
        """
import json
import sys

import llm_wiki_cli.api

prefixes = (
    "llm_wiki_cli.services.calibration",
    "llm_wiki_cli.services.documentation_calibration",
)
print(json.dumps(sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in prefixes)
)))
"""
    )

    assert result == []


def test_public_api_type_hints_resolve_before_lazy_type_access() -> None:
    result = _run_isolation_script(
        """
import json
import inspect
import sys
import typing

import llm_wiki_cli.api as api

prefixes = (
    "llm_wiki_cli.services.calibration",
    "llm_wiki_cli.services.documentation_calibration",
)
loaded = lambda: sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in prefixes)
)
before = loaded()
names = (
    "prepare_calibration_run",
    "admit_calibration_run",
    "get_calibration_run_status",
    "build_calibration_agent_packet",
    "dispatch_calibration_agent",
    "record_calibration_agent_result",
    "verify_calibration_run",
    "use_calibration_host_broker_authenticator",
)
legacy_replacements = {
    "prepare_p0_calibration_run": "prepare_calibration_run",
    "admit_p0_calibration_run": "admit_calibration_run",
    "get_p0_calibration_run_status": "get_calibration_run_status",
    "build_p0_calibration_agent_packet": "build_calibration_agent_packet",
    "dispatch_p0_calibration_agent": "dispatch_calibration_agent",
    "record_p0_calibration_agent_result": "record_calibration_agent_result",
    "verify_p0_calibration_run": "verify_calibration_run",
    "use_p0_calibration_host_broker_authenticator": (
        "use_calibration_host_broker_authenticator"
    ),
}
hints = {
    name: typing.get_type_hints(getattr(api, name))
    for name in names + tuple(legacy_replacements)
}
unwrapped_hints = {
    name: typing.get_type_hints(inspect.unwrap(getattr(api, name)))
    for name in names + tuple(legacy_replacements)
}
expected_returns = {
    "prepare_calibration_run": api.P0CalibrationRun,
    "admit_calibration_run": api.P0CalibrationRun,
    "get_calibration_run_status": api.P0CalibrationStatus,
    "build_calibration_agent_packet": api.P0CalibrationAgentPacket,
    "dispatch_calibration_agent": api.P0CalibrationDispatchReceipt,
    "record_calibration_agent_result": api.P0CalibrationRun,
    "verify_calibration_run": api.P0CalibrationVerificationReport,
}
for name, expected in expected_returns.items():
    assert hints[name]["return"] is expected
assert (
    hints["use_calibration_host_broker_authenticator"]["authenticator"]
    is api.HostBrokerAuthenticator
)
assert api.P0CalibrationDispatchReceipt in typing.get_args(
    hints["record_calibration_agent_result"]["dispatch_receipt"]
)
assert api.P0CalibrationAgentResult in typing.get_args(
    hints["record_calibration_agent_result"]["result"]
)
for legacy, replacement in legacy_replacements.items():
    assert hints[legacy] == hints[replacement]
for name in names + tuple(legacy_replacements):
    assert unwrapped_hints[name] == hints[name]
print(json.dumps({"before": before, "after": loaded()}))
"""
    )

    assert result["before"] == []
    assert f"{CALIBRATION_PACKAGE}.controller" in result["after"]
    assert f"{CALIBRATION_PACKAGE}.host_broker" in result["after"]


def test_non_calibration_public_api_call_does_not_load_calibration() -> None:
    result = _run_isolation_script(
        """
import json
import os
import sys
import tempfile

import llm_wiki_cli.api as api

with tempfile.TemporaryDirectory() as root:
    previous_cwd = os.getcwd()
    try:
        os.chdir(root)
        payload = api.extract_source(".", read_only=True)
    finally:
        os.chdir(previous_cwd)
assert payload["schema_version"] == "llm-wiki-extract/v1"

prefixes = (
    "llm_wiki_cli.services.calibration",
    "llm_wiki_cli.services.documentation_calibration",
)
print(json.dumps(sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in prefixes)
)))
"""
    )

    assert result == []


def test_mcp_module_and_service_import_do_not_load_calibration() -> None:
    result = _run_isolation_script(
        """
import json
import sys

from llm_wiki_cli.commands import mcp_cmd
from llm_wiki_cli.services import mcp_server

mcp_cmd._mcp_service_export("McpServerConfig")
mcp_server.McpWikiService()

prefixes = (
    "llm_wiki_cli.services.calibration",
    "llm_wiki_cli.services.documentation_calibration",
)
print(json.dumps(sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in prefixes)
)))
"""
    )

    assert result == []


@pytest.mark.parametrize(("legacy_name", "implementation_name"), MODULE_PAIRS)
def test_legacy_calibration_modules_alias_relocated_implementations(
    legacy_name: str,
    implementation_name: str,
) -> None:
    legacy = importlib.import_module(legacy_name)
    implementation = importlib.import_module(implementation_name)

    assert legacy is implementation
    assert {
        name
        for name, value in vars(implementation).items()
        if getattr(value, "__module__", None) == implementation_name
    } == set()


@pytest.mark.parametrize(
    ("legacy_name", "implementation_name", "target"),
    [
        (*MODULE_PAIRS[0], "_digest"),
        (*MODULE_PAIRS[1], "_bytes_sha256"),
        (*MODULE_PAIRS[2], "_bounded_error"),
        (*MODULE_PAIRS[3], "_require_hash"),
    ],
)
def test_legacy_monkeypatch_targets_update_implementation_globals(
    legacy_name: str,
    implementation_name: str,
    target: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = importlib.import_module(legacy_name)
    implementation = importlib.import_module(implementation_name)
    replacement = object()

    monkeypatch.setattr(legacy, target, replacement)

    assert getattr(implementation, target) is replacement


@pytest.mark.parametrize(
    ("module_name", "class_name", "function_name"),
    [
        (
            MODULE_PAIRS[0][0],
            "DocumentationCalibrationError",
            "canonical_json_sha256",
        ),
        (MODULE_PAIRS[1][0], "OciBrokerError", "canonical_result_json_bytes"),
        (MODULE_PAIRS[2][0], "P0CalibrationError", "get_calibration_run_status"),
        (
            MODULE_PAIRS[3][0],
            "HostBrokerAuthenticationError",
            "require_process_host_broker_authenticator",
        ),
    ],
)
def test_relocated_calibration_definitions_keep_legacy_pickle_paths(
    module_name: str,
    class_name: str,
    function_name: str,
) -> None:
    module = importlib.import_module(module_name)
    exception_type = getattr(module, class_name)
    function = getattr(module, function_name)
    exception = exception_type("sentinel")

    assert exception_type.__module__ == module_name
    assert function.__module__ == module_name
    encoded_exception = base64.b64encode(pickle.dumps(exception)).decode("ascii")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import base64,pickle,sys;"
                "value=pickle.loads(base64.b64decode(sys.argv[1]));"
                "print(value.__class__.__module__);"
                "print(value.__class__.__name__);"
                "print(value.args[0])"
            ),
            encoded_exception,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout.splitlines() == [
        module_name,
        class_name,
        "sentinel",
    ]
    assert pickle.loads(pickle.dumps(function)) is function


def test_calibration_package_contains_only_the_isolated_service_roles() -> None:
    package_root = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "llm_wiki_cli"
        / "services"
        / "calibration"
    )

    assert {path.name for path in package_root.glob("*.py")} == {
        "__init__.py",
        "broker.py",
        "contracts.py",
        "controller.py",
        "host_broker.py",
    }
