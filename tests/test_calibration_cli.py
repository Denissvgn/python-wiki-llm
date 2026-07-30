"""Focused public CLI coverage for the documentation calibration lifecycle."""

from __future__ import annotations

import io
import json
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import docs_cmd
from llm_wiki_cli.services.documentation_calibration_controller import (
    P0CalibrationIntegrityError,
)
from llm_wiki_cli.services.documentation_run import DocumentationRunError


class _Payload:
    def __init__(self, **payload):
        self.payload = payload

    def to_dict(self):
        return dict(self.payload)


class _ParsedReceipt:
    @classmethod
    def from_dict(cls, payload):
        return cls(), dict(payload)


class _ParsedResult:
    @classmethod
    def from_dict(cls, payload):
        return cls(), dict(payload)


def test_calibration_help_lists_nested_lifecycle(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        ["llm-wiki", "docs", "calibration", "--help"],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    for action in (
        "prepare",
        "admit",
        "status",
        "packet",
        "dispatch",
        "record-result",
        "verify",
    ):
        assert action in help_text


@pytest.mark.parametrize(
    ("arguments", "action"),
    [
        (
            [
                "prepare",
                "--root",
                "cohort",
                "--control-workspace",
                "control-a",
                "--control-workspace",
                "control-b",
                "--execution-manifest",
                "manifest.json",
            ],
            "prepare",
        ),
        (
            [
                "admit",
                "--root",
                "cohort",
                "--authority-grant",
                "grant.json",
                "--broker-attestation",
                "attestation.json",
            ],
            "admit",
        ),
        (["status", "--root", "cohort"], "status"),
        (
            [
                "packet",
                "--root",
                "cohort",
                "--role",
                "intake-a",
                "--output",
                "packet.json",
            ],
            "packet",
        ),
        (
            ["dispatch", "--root", "cohort", "--role", "verifier"],
            "dispatch",
        ),
        (
            [
                "record-result",
                "--root",
                "cohort",
                "--dispatch-receipt",
                "receipt.json",
                "--result",
                "result.json",
            ],
            "record-result",
        ),
        (["verify", "--root", "cohort", "--no-advance"], "verify"),
    ],
)
def test_calibration_parser_locks_nested_actions_and_flags(arguments, action):
    args = cli._build_parser().parse_args(
        ["docs", "calibration", *arguments],
    )

    assert args.command == "docs"
    assert args.docs_action == "calibration"
    assert args.calibration_action == action
    assert args.root == "cohort"


def test_calibration_prepare_reads_manifest_and_requires_two_controls(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"schema_version":"manifest/v1"}', encoding="utf-8")
    captured = {}
    controller = SimpleNamespace(
        prepare_calibration_run=lambda root, **kwargs: (
            captured.update(root=root, **kwargs)
            or _Payload(schema_version="run/v1", state="BASELINE_FROZEN")
        )
    )
    monkeypatch.setattr(docs_cmd, "_calibration_controller", lambda: controller)
    args = cli._build_parser().parse_args(
        [
            "docs",
            "calibration",
            "prepare",
            "--root",
            str(tmp_path / "cohort"),
            "--control-workspace",
            "control-a",
            "--control-workspace",
            "control-b",
            "--execution-manifest",
            str(manifest_path),
        ]
    )

    docs_cmd.run(args)

    assert captured == {
        "root": str(tmp_path / "cohort"),
        "control_workspaces": ("control-a", "control-b"),
        "execution_manifest": {"schema_version": "manifest/v1"},
    }
    assert json.loads(capsys.readouterr().out)["state"] == "BASELINE_FROZEN"

    args.control_workspace = ["control-a"]
    with pytest.raises(SystemExit) as exc_info:
        docs_cmd.run(args)
    assert exc_info.value.code == 1


def test_calibration_admit_status_and_dispatch_forward_strict_inputs(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    authority_path = tmp_path / "authority.json"
    authority_path.write_text('{"grant_id":"grant-1"}', encoding="utf-8")
    attestation_path = tmp_path / "attestation.json"
    attestation_path.write_text('{"attestation_id":"att-1"}', encoding="utf-8")
    captured = {}

    def admit(root, *, authority_grant, broker_attestation):
        captured["admit"] = {
            "root": root,
            "authority_grant": authority_grant,
            "broker_attestation": broker_attestation,
        }
        return _Payload(schema_version="run/v1", state="ADMISSION_AUTHORIZED")

    def dispatch(root, *, role):
        captured["dispatch"] = {"root": root, "role": role}
        return _Payload(
            schema_version="receipt/v1",
            receipt_id="receipt-1",
            status="complete",
        )

    controller = SimpleNamespace(
        admit_calibration_run=admit,
        get_calibration_run_status=lambda root: (
            captured.update(status=root)
            or _Payload(cohort_id="cohort-1", state="ADMISSION_AUTHORIZED")
        ),
        dispatch_calibration_agent=dispatch,
    )
    monkeypatch.setattr(docs_cmd, "_calibration_controller", lambda: controller)

    admit_args = cli._build_parser().parse_args(
        [
            "docs",
            "calibration",
            "admit",
            "--root",
            "cohort",
            "--authority-grant",
            str(authority_path),
            "--broker-attestation",
            str(attestation_path),
        ]
    )
    docs_cmd.run(admit_args)
    assert json.loads(capsys.readouterr().out)["state"] == "ADMISSION_AUTHORIZED"

    status_args = cli._build_parser().parse_args(
        ["docs", "calibration", "status", "--root", "cohort"]
    )
    docs_cmd.run(status_args)
    assert json.loads(capsys.readouterr().out)["cohort_id"] == "cohort-1"

    dispatch_args = cli._build_parser().parse_args(
        [
            "docs",
            "calibration",
            "dispatch",
            "--root",
            "cohort",
            "--role",
            "intake-c",
        ]
    )
    docs_cmd.run(dispatch_args)
    assert json.loads(capsys.readouterr().out)["receipt_id"] == "receipt-1"

    assert captured == {
        "admit": {
            "root": "cohort",
            "authority_grant": {"grant_id": "grant-1"},
            "broker_attestation": {"attestation_id": "att-1"},
        },
        "status": "cohort",
        "dispatch": {"root": "cohort", "role": "intake-c"},
    }


def test_calibration_packet_writes_bounded_json_only_to_explicit_output(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    output = tmp_path / "packet.json"

    def validate_output(root, requested):
        protected = Path(root).resolve()
        target = Path(requested).resolve()
        if target == protected or protected in target.parents:
            raise P0CalibrationIntegrityError("outside the protected root")
        return target

    controller = SimpleNamespace(
        validate_p0_calibration_packet_output=validate_output,
        build_calibration_agent_packet=lambda root, *, role: _Payload(
            schema_version="packet/v1",
            root=root,
            role=role,
            private_evidence="bounded",
        ),
    )
    monkeypatch.setattr(docs_cmd, "_calibration_controller", lambda: controller)
    args = cli._build_parser().parse_args(
        [
            "docs",
            "calibration",
            "packet",
            "--root",
            "cohort",
            "--role",
            "intake-b",
            "--output",
            str(output),
        ]
    )

    docs_cmd.run(args)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert json.loads(output.read_text(encoding="utf-8")) == {
        "schema_version": "packet/v1",
        "root": "cohort",
        "role": "intake-b",
        "private_evidence": "bounded",
    }
    if os.name != "nt":
        assert stat.S_IMODE(output.stat().st_mode) == 0o600

    args.output = "-"
    with pytest.raises(SystemExit) as exc_info:
        docs_cmd.run(args)
    assert exc_info.value.code == 1
    assert "not stdout" in capsys.readouterr().err

    bounded_output = tmp_path / "oversized.json"
    args.output = str(bounded_output)
    monkeypatch.setattr(docs_cmd, "_MAX_CALIBRATION_PACKET_BYTES", 16)
    with pytest.raises(SystemExit) as exc_info:
        docs_cmd.run(args)
    assert exc_info.value.code == 1
    assert not bounded_output.exists()
    assert "output limit" in capsys.readouterr().err

    protected_root = tmp_path / "protected"
    protected_root.mkdir()
    args.root = str(protected_root)
    args.output = str(protected_root / "packet.json")
    with pytest.raises(SystemExit) as exc_info:
        docs_cmd.run(args)
    assert exc_info.value.code == 1
    assert "outside the protected root" in capsys.readouterr().err


def test_calibration_record_result_parses_both_contracts_before_import(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text('{"receipt_id":"receipt-1"}', encoding="utf-8")
    result_path = tmp_path / "result.json"
    result_path.write_text('{"status":"complete"}', encoding="utf-8")
    captured = {}
    controller = SimpleNamespace(
        P0CalibrationDispatchReceipt=_ParsedReceipt,
        P0CalibrationAgentResult=_ParsedResult,
        record_calibration_agent_result=lambda root, **kwargs: (
            captured.update(root=root, **kwargs)
            or _Payload(schema_version="run/v1", state="INTAKE_OPEN")
        ),
    )
    monkeypatch.setattr(docs_cmd, "_calibration_controller", lambda: controller)
    args = cli._build_parser().parse_args(
        [
            "docs",
            "calibration",
            "record-result",
            "--root",
            "cohort",
            "--dispatch-receipt",
            str(receipt_path),
            "--result",
            str(result_path),
        ]
    )

    docs_cmd.run(args)

    assert captured["root"] == "cohort"
    assert captured["dispatch_receipt"][1] == {"receipt_id": "receipt-1"}
    assert captured["result"][1] == {"status": "complete"}
    assert json.loads(capsys.readouterr().out)["state"] == "INTAKE_OPEN"


def test_calibration_verify_forwards_no_advance_and_fails_closed(
    monkeypatch,
    capsys,
):
    captured = {}
    controller = SimpleNamespace(
        verify_calibration_run=lambda root, *, advance: (
            captured.update(root=root, advance=advance)
            or _Payload(schema_version="verification/v1", ok=False)
        )
    )
    monkeypatch.setattr(docs_cmd, "_calibration_controller", lambda: controller)
    args = cli._build_parser().parse_args(
        [
            "docs",
            "calibration",
            "verify",
            "--root",
            "cohort",
            "--no-advance",
        ]
    )

    with pytest.raises(SystemExit) as exc_info:
        docs_cmd.run(args)

    assert exc_info.value.code == 1
    assert captured == {"root": "cohort", "advance": False}
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_calibration_admit_reports_terminal_failure_with_nonzero_exit(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    authority = tmp_path / "authority.json"
    authority.write_text('{"grant_id":"grant-1"}', encoding="utf-8")
    controller = SimpleNamespace(
        admit_calibration_run=lambda *_args, **_kwargs: _Payload(
            schema_version="run/v1",
            state="BLOCKED_NO_SHIP",
        )
    )
    monkeypatch.setattr(docs_cmd, "_calibration_controller", lambda: controller)
    args = cli._build_parser().parse_args(
        [
            "docs",
            "calibration",
            "admit",
            "--root",
            "cohort",
            "--authority-grant",
            str(authority),
        ]
    )

    with pytest.raises(SystemExit) as exc_info:
        docs_cmd.run(args)

    assert exc_info.value.code == 1
    assert json.loads(capsys.readouterr().out)["state"] == "BLOCKED_NO_SHIP"


def test_calibration_dispatch_reports_failed_receipt_with_nonzero_exit(
    monkeypatch,
    capsys,
):
    controller = SimpleNamespace(
        dispatch_calibration_agent=lambda *_args, **_kwargs: _Payload(
            schema_version="receipt/v1",
            receipt_id="receipt-1",
            status="timed_out",
        )
    )
    monkeypatch.setattr(docs_cmd, "_calibration_controller", lambda: controller)
    args = cli._build_parser().parse_args(
        [
            "docs",
            "calibration",
            "dispatch",
            "--root",
            "cohort",
            "--role",
            "intake-a",
        ]
    )

    with pytest.raises(SystemExit) as exc_info:
        docs_cmd.run(args)

    assert exc_info.value.code == 1
    assert json.loads(capsys.readouterr().out)["status"] == "timed_out"


@pytest.mark.parametrize("via_stdin", [False, True])
def test_calibration_json_inputs_reject_duplicate_keys_and_nonfinite_values(
    tmp_path: Path,
    monkeypatch,
    via_stdin: bool,
):
    duplicate_payload = '{"grant_id":"first","grant_id":"second"}'
    source: Path | None = None
    if via_stdin:
        monkeypatch.setattr("sys.stdin", io.StringIO(duplicate_payload))
        path = "-"
    else:
        source = tmp_path / "duplicate.json"
        source.write_text(duplicate_payload, encoding="utf-8")
        path = str(source)

    with pytest.raises(DocumentationRunError, match="Duplicate JSON object key"):
        docs_cmd._read_calibration_json_object(path, label="authority grant")

    nonfinite_payload = '{"grant_id":"first","value":NaN}'
    if via_stdin:
        monkeypatch.setattr("sys.stdin", io.StringIO(nonfinite_payload))
    else:
        assert source is not None
        source.write_text(nonfinite_payload, encoding="utf-8")

    with pytest.raises(DocumentationRunError, match="Non-finite JSON number"):
        docs_cmd._read_calibration_json_object(path, label="authority grant")

    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"value":Infinity}', encoding="utf-8")
    with pytest.raises(DocumentationRunError, match="Non-finite JSON"):
        docs_cmd._read_calibration_json_object(
            str(nonfinite),
            label="execution manifest",
        )


def test_legacy_json_reader_preserves_duplicate_and_nonfinite_behavior(
    tmp_path: Path,
):
    source = tmp_path / "legacy.json"
    source.write_text(
        '{"value":"first","value":"second","number":NaN}',
        encoding="utf-8",
    )

    payload = docs_cmd._read_json_object(str(source), label="legacy agent result")

    assert payload["value"] == "second"
    assert payload["number"] != payload["number"]


def test_calibration_json_reader_uses_four_mibibyte_bound(tmp_path: Path):
    accepted = tmp_path / "accepted.json"
    padding = "x" * 1_100_000
    accepted.write_text(
        json.dumps({"padding": padding}, separators=(",", ":")),
        encoding="utf-8",
    )

    payload = docs_cmd._read_calibration_json_object(
        str(accepted),
        label="calibration result",
    )

    assert payload["padding"] == padding

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b'{"padding":"' + b"x" * (4 * 1024 * 1024) + b'"}')
    with pytest.raises(DocumentationRunError, match="4194304-byte input limit"):
        docs_cmd._read_calibration_json_object(
            str(oversized),
            label="calibration result",
        )
