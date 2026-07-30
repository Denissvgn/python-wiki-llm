"""Focused CLI coverage for standalone documentation workspaces."""

from __future__ import annotations

import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import docs_cmd
from llm_wiki_cli.services.contracts import (
    DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
)


def _status_payload() -> dict[str, object]:
    return {
        "run_id": "doc-run-1",
        "state": "baseline_ready",
        "baseline_strategy": "bootstrap_source",
        "source_available": True,
        "freshness": "verified_current",
        "current_stage": None,
        "next_actions": ["build wiki-enrichment packet"],
        "limitations": [],
        "healthy": True,
        "integration_mode": "external_agent_docs",
    }


class _FakeStatus:
    def to_dict(self) -> dict[str, object]:
        return _status_payload()


def test_docs_help_lists_all_lifecycle_actions(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm-wiki", "docs", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    normalized_help = " ".join(help_text.split())
    for action in (
        "prepare",
        "status",
        "packet",
        "record-result",
        "verify",
        "export",
        "calibration",
    ):
        assert action in help_text
    assert "evidence-backed documentation calibration cohort" in normalized_help
    assert "P0 calibration" not in normalized_help


@pytest.mark.parametrize(
    ("argv", "expected_action"),
    [
        (["docs", "status", "--workspace", "docs-work"], "status"),
        (
            [
                "docs",
                "packet",
                "--workspace",
                "docs-work",
                "--stage",
                "wiki-enrichment",
            ],
            "packet",
        ),
        (
            [
                "docs",
                "record-result",
                "--workspace",
                "docs-work",
                "--result",
                "result.json",
            ],
            "record-result",
        ),
        (["docs", "verify", "--workspace", "docs-work"], "verify"),
        (["docs", "export", "--workspace", "docs-work"], "export"),
    ],
)
def test_docs_actions_dispatch_to_docs_command(argv, expected_action, monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.docs_cmd,
        "run",
        lambda args: seen.update(action=args.docs_action, workspace=args.workspace),
    )
    monkeypatch.setattr("sys.argv", ["llm-wiki", *argv])

    cli.main()

    assert seen == {"action": expected_action, "workspace": "docs-work"}


def test_docs_prepare_maps_supervisor_intake_without_prompting(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "source project"
    source.mkdir()
    brief = tmp_path / "purpose.md"
    brief.write_text("A cross-platform package for operators.\n", encoding="utf-8")
    captured = {}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        docs_cmd,
        "prepare_documentation_run",
        lambda workspace, **kwargs: captured.update(workspace=workspace, **kwargs),
    )
    monkeypatch.setattr(
        docs_cmd, "get_documentation_run_status", lambda _workspace: _FakeStatus()
    )
    args = cli._build_parser().parse_args(
        [
            "docs",
            "prepare",
            "--workspace",
            "published docs",
            "--baseline",
            "bootstrap-source",
            "--src-dir",
            str(source),
            "--site-name",
            "Operator Guide",
            "--project-brief",
            str(brief),
            "--audience",
            "user,operator",
            "--audience-intent",
            "operator=complete the first safe operation",
            "--site-format",
            "mkdocs",
            "--file-friendly",
            "--knowledge-mode",
            "public-portable",
            "--knowledge-public-repository-identity",
            "example.invalid/operator-guide",
            "--output-format",
            "json",
        ]
    )

    docs_cmd.run(args)

    assert captured["workspace"] == "published docs"
    assert captured["baseline_strategy"] == "bootstrap_source"
    assert captured["source_root"] == str(source.resolve())
    assert captured["input_wiki_root"] is None
    assert captured["project_purpose"] == "A cross-platform package for operators."
    assert captured["audiences"] == ["user", "operator"]
    assert captured["audience_intent"] == {
        "operator": "complete the first safe operation"
    }
    assert captured["link_mode"] == "file"
    assert captured["knowledge_mode"] == "public-portable"
    assert captured["knowledge_public_repository_identity"] == (
        "example.invalid/operator-guide"
    )
    assert captured["trust_source_plugins"] is False
    assert json.loads(capsys.readouterr().out)["integration_mode"] == (
        "external_agent_docs"
    )


def test_docs_projection_policy_defaults_to_explicit_off_contract():
    args = cli._build_parser().parse_args(
        [
            "docs",
            "prepare",
            "--workspace",
            "docs-work",
            "--baseline",
            "bootstrap-source",
            "--src-dir",
            ".",
            "--site-name",
            "Operator Guide",
        ]
    )

    assert args.knowledge_mode == "off"
    assert args.knowledge_public_repository_identity is None


def test_docs_prepare_reads_structured_intake_and_external_existing_wiki(
    tmp_path, monkeypatch
):
    input_wiki = tmp_path / "existing wiki"
    input_wiki.mkdir()
    intake = tmp_path / "intake.json"
    intake.write_text(
        json.dumps(
            {
                "project_purpose": "Explain the product",
                "audiences": ["user"],
                "audience_intent": {"user": "finish setup"},
                "live_service": {
                    "address": "https://staging.example.test",
                    "access_mode": "anonymous",
                    "observation_allowed": False,
                },
            }
        ),
        encoding="utf-8",
    )
    captured = {}
    monkeypatch.setattr(
        docs_cmd,
        "prepare_documentation_run",
        lambda workspace, **kwargs: captured.update(workspace=workspace, **kwargs),
    )
    monkeypatch.setattr(
        docs_cmd, "get_documentation_run_status", lambda _workspace: _FakeStatus()
    )
    args = cli._build_parser().parse_args(
        [
            "docs",
            "prepare",
            "--workspace",
            str(tmp_path / "workspace"),
            "--baseline",
            "existing-wiki",
            "--input-wiki-dir",
            str(input_wiki),
            "--wiki-freshness",
            "allow-unverified",
            "--site-name",
            "Product",
            "--intake-file",
            str(intake),
            "--allow-external-src",
        ]
    )

    docs_cmd.run(args)

    assert captured["baseline_strategy"] == "adopt_existing_wiki"
    assert captured["input_wiki_root"] == str(input_wiki.resolve())
    assert captured["freshness_policy"] == "allow-unverified"
    assert captured["project_purpose"] == "Explain the product"
    assert captured["live_service_url"] == "https://staging.example.test"
    assert captured["live_service_access_mode"] == "anonymous"


def test_docs_prepare_rejects_intake_file_mixed_with_direct_answers(tmp_path, capsys):
    intake = tmp_path / "intake.json"
    intake.write_text("{}", encoding="utf-8")
    args = cli._build_parser().parse_args(
        [
            "docs",
            "prepare",
            "--workspace",
            str(tmp_path / "workspace"),
            "--baseline",
            "existing-wiki",
            "--input-wiki-dir",
            str(tmp_path),
            "--wiki-freshness",
            "allow-unverified",
            "--site-name",
            "Product",
            "--intake-file",
            str(intake),
            "--audience",
            "user",
            "--allow-external-src",
        ]
    )

    with pytest.raises(SystemExit) as exc_info:
        docs_cmd.run(args)

    assert exc_info.value.code == 1
    assert "cannot be combined" in capsys.readouterr().err


def test_docs_text_input_is_read_with_the_declared_byte_bound(monkeypatch):
    reads: list[int | None] = []

    class RecordingStream(io.BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            reads.append(size)
            return super().read(size)

    monkeypatch.setattr(docs_cmd, "_MAX_INTAKE_BYTES", 4)
    monkeypatch.setattr(
        Path,
        "open",
        lambda self, mode="r", *args, **kwargs: RecordingStream(b"okay"),
    )

    assert docs_cmd._read_bounded_text("brief.md", label="project brief") == "okay"
    assert reads == [5]


def test_docs_packet_prints_selected_provider_neutral_representation(
    monkeypatch, capsys
):
    packet = SimpleNamespace(
        to_json=lambda: '{"schema_version":"packet/v1"}\n',
        to_markdown=lambda: "# Agent packet\n",
    )
    monkeypatch.setattr(
        docs_cmd,
        "build_documentation_agent_packet",
        lambda workspace, *, stage: packet,
    )
    args = cli._build_parser().parse_args(
        [
            "docs",
            "packet",
            "--workspace",
            "docs-work",
            "--stage",
            "user-docs",
            "--format",
            "json",
        ]
    )

    docs_cmd.run(args)

    assert json.loads(capsys.readouterr().out) == {"schema_version": "packet/v1"}


def test_docs_record_result_validates_json_contract_before_recording(
    tmp_path, monkeypatch, capsys
):
    result_file = tmp_path / "agent-result.json"
    result_file.write_text(
        json.dumps(
            {
                "schema_version": DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
                "run_id": "doc-run-1",
                "stage": "wiki-enrichment",
                "status": "complete",
                "changed_wiki_paths": [],
                "reused_work_ids": [],
                "completed_work_ids": [],
                "deferred_work_ids": [],
                "claims_evidence_pages": [],
                "unresolved_unknowns": [],
                "unsupported_source_notices": [],
                "requested_follow_up_checks": [],
                "reported_source_writes": [],
                "reported_input_wiki_writes": [],
                "reported_generated_block_edits": [],
                "findings": [],
            }
        ),
        encoding="utf-8",
    )
    captured = {}
    monkeypatch.setattr(
        docs_cmd,
        "record_documentation_agent_result",
        lambda workspace, result: captured.update(
            workspace=workspace,
            result=result,
        ),
    )
    monkeypatch.setattr(
        docs_cmd, "get_documentation_run_status", lambda _workspace: _FakeStatus()
    )
    args = cli._build_parser().parse_args(
        [
            "docs",
            "record-result",
            "--workspace",
            "docs-work",
            "--result",
            str(result_file),
            "--format",
            "json",
        ]
    )

    docs_cmd.run(args)

    assert captured["workspace"] == "docs-work"
    assert captured["result"].run_id == "doc-run-1"
    assert captured["result"].stage == "wiki-enrichment"
    assert json.loads(capsys.readouterr().out)["healthy"] is True


@pytest.mark.parametrize(("ok", "expected_exit"), [(True, None), (False, 1)])
def test_docs_verify_reports_checks_and_fails_closed(
    ok, expected_exit, monkeypatch, capsys
):
    report = SimpleNamespace(
        run_id="doc-run-1",
        state="review",
        ok=ok,
        checks=({"check": "source_integrity", "ok": ok},),
        limitations=(),
        next_state="publish_ready" if ok else None,
        to_dict=lambda: {
            "run_id": "doc-run-1",
            "state": "review",
            "ok": ok,
            "checks": [{"check": "source_integrity", "ok": ok}],
            "limitations": [],
            "next_state": "publish_ready" if ok else None,
        },
    )
    captured = {}
    monkeypatch.setattr(
        docs_cmd,
        "verify_documentation_run",
        lambda workspace, *, advance: (
            captured.update(workspace=workspace, advance=advance) or report
        ),
    )
    args = cli._build_parser().parse_args(
        [
            "docs",
            "verify",
            "--workspace",
            "docs-work",
            "--format",
            "json",
            "--no-advance",
        ]
    )

    if expected_exit is None:
        docs_cmd.run(args)
    else:
        with pytest.raises(SystemExit) as exc_info:
            docs_cmd.run(args)
        assert exc_info.value.code == expected_exit

    assert captured == {"workspace": "docs-work", "advance": False}
    assert json.loads(capsys.readouterr().out)["ok"] is ok


def test_docs_export_passes_builder_as_argv_without_shell_parsing(monkeypatch, capsys):
    monkeypatch.setattr(
        docs_cmd,
        "load_documentation_run",
        lambda _workspace: SimpleNamespace(
            publication={
                "format": "mkdocs",
                "link_mode": "file",
                "knowledge_mode": "public-portable",
                "knowledge_public_repository_identity": None,
            }
        ),
    )
    captured = {}

    def fake_export(
        workspace,
        *,
        build,
        builder_command,
        knowledge_mode,
        knowledge_public_repository_identity,
    ):
        captured.update(
            workspace=workspace,
            build=build,
            builder_command=builder_command,
            knowledge_mode=knowledge_mode,
            knowledge_public_repository_identity=(
                knowledge_public_repository_identity
            ),
        )
        return {
            "run_id": "doc-run-1",
            "state": "review",
            "verdict": "local_artifact_ready_with_limitations",
            "limitations": ["built_site_not_verified"],
            "deployment_handoff": {"instructions": "Run an authorized deploy."},
        }

    monkeypatch.setattr(docs_cmd, "export_documentation_run", fake_export)
    args = cli._build_parser().parse_args(
        [
            "docs",
            "export",
            "--workspace",
            "docs-work",
            "--format",
            "mkdocs",
            "--file-friendly",
            "--knowledge-mode",
            "public-portable",
            "--build",
            "--output-format",
            "json",
            "--builder-command",
            "mkdocs",
            "build",
            "--strict",
        ]
    )

    docs_cmd.run(args)

    assert captured == {
        "workspace": "docs-work",
        "build": True,
        "builder_command": ["mkdocs", "build", "--strict"],
        "knowledge_mode": "public-portable",
        "knowledge_public_repository_identity": None,
    }
    assert json.loads(capsys.readouterr().out)["verdict"] == (
        "local_artifact_ready_with_limitations"
    )
