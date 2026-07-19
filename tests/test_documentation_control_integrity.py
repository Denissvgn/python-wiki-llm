"""Adversarial checks for supervisor-owned documentation control artifacts."""

from __future__ import annotations

import errno
import json
from contextlib import contextmanager
from pathlib import Path

import pytest

import llm_wiki_cli.services.documentation_run as documentation_run_service
from llm_wiki_cli.services.contracts import (
    DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
)
from llm_wiki_cli.services.documentation_run import (
    DocumentationIntegrityError,
    DocumentationRunError,
    DocumentationSchemaError,
    build_documentation_agent_packet,
    capture_generated_ownership,
    prepare_documentation_run,
    record_documentation_agent_result,
)
from llm_wiki_cli.services.documentation_policy import source_tree_baseline


def _prepare(tmp_path: Path):
    input_wiki = tmp_path / "input wiki"
    input_wiki.mkdir()
    (input_wiki / "index.md").write_text(
        "# Example\n\nExisting agent-authored context.\n",
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"
    run = prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        input_wiki_root=input_wiki,
        freshness_policy="allow-unverified",
        site_name="Example",
    )
    return workspace, run


def _result(run_id: str) -> dict:
    return {
        "schema_version": DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
        "run_id": run_id,
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
        "deferral_rationales": {},
        "findings": [],
    }


def _rewrite_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


@pytest.mark.parametrize(
    "field",
    [
        "access_token",
        "auth_token",
        "client_secret",
        "base_url",
        "provider_name",
        "model_name",
        "openai_api_key",
    ],
)
def test_packet_rejects_tampered_worklist_count_fields(tmp_path: Path, field: str):
    workspace, _ = _prepare(tmp_path)
    worklist_path = workspace / ".llm-wiki-docs" / "evidence" / "semantic-worklist.json"
    worklist = json.loads(worklist_path.read_text(encoding="utf-8"))
    worklist["counts"][field] = "untrusted"
    _rewrite_json(worklist_path, worklist)

    with pytest.raises(DocumentationSchemaError, match="counts"):
        build_documentation_agent_packet(workspace, stage="wiki-enrichment")


@pytest.mark.parametrize("directory", ["packets", "evidence"])
def test_packet_build_rejects_post_prepare_control_redirect(
    tmp_path: Path, directory: str
):
    workspace, _ = _prepare(tmp_path)
    control_directory = workspace / ".llm-wiki-docs" / directory
    outside = tmp_path / f"outside-{directory}"
    outside.mkdir()
    for path in sorted(control_directory.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    control_directory.rmdir()
    try:
        control_directory.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks are unavailable: {exc}")

    with pytest.raises(DocumentationIntegrityError, match="symlink|reparse"):
        build_documentation_agent_packet(workspace, stage="wiki-enrichment")

    assert not list(outside.iterdir())


def test_result_write_rejects_post_packet_results_redirect(tmp_path: Path):
    workspace, run = _prepare(tmp_path)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    result_directory = workspace / ".llm-wiki-docs" / "results"
    outside = tmp_path / "outside-results"
    outside.mkdir()
    result_directory.rmdir()
    try:
        result_directory.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks are unavailable: {exc}")

    with pytest.raises(DocumentationIntegrityError, match="symlink|reparse"):
        record_documentation_agent_result(workspace, _result(run.run_id))

    assert not list(outside.iterdir())


@pytest.mark.skipif(
    not documentation_run_service._supports_descriptor_bound_workspace_writes(),
    reason="descriptor-relative writer is unavailable on this platform",
)
def test_result_write_pins_parent_against_swap_before_temp_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    workspace, run = _prepare(tmp_path)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    results = workspace / ".llm-wiki-docs" / "results"
    pinned = workspace / ".llm-wiki-docs" / "results-pinned"
    outside = tmp_path / "outside-race"
    outside.mkdir()
    real_open = documentation_run_service.os.open
    swapped = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if (
            not swapped
            and dir_fd is not None
            and flags & documentation_run_service.os.O_CREAT
        ):
            results.rename(pinned)
            results.symlink_to(outside, target_is_directory=True)
            swapped = True
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(documentation_run_service.os, "open", racing_open)
    monkeypatch.setattr(
        documentation_run_service,
        "_supports_descriptor_bound_workspace_writes",
        lambda: True,
    )

    with pytest.raises(DocumentationIntegrityError, match="parent"):
        record_documentation_agent_result(workspace, _result(run.run_id))

    assert swapped is True
    assert not list(outside.iterdir())
    assert not list(pinned.iterdir())


def test_result_rejects_schema_valid_run_change_after_dispatch(tmp_path: Path):
    workspace, run = _prepare(tmp_path)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    run_path = workspace / ".llm-wiki-docs" / "run.json"
    payload = json.loads(run_path.read_text(encoding="utf-8"))
    payload["verdict_limitations"].append("tampered_but_schema_valid")
    _rewrite_json(run_path, payload)

    with pytest.raises(DocumentationIntegrityError, match="control state changed"):
        record_documentation_agent_result(workspace, _result(run.run_id))


def test_result_rejects_supervisor_control_artifact_change(tmp_path: Path):
    workspace, run = _prepare(tmp_path)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    ownership_path = (
        workspace / ".llm-wiki-docs" / "evidence" / "generated-ownership.json"
    )
    ownership = json.loads(ownership_path.read_text(encoding="utf-8"))
    ownership["fingerprints"]["forged#generated"] = "sha256:" + "0" * 64
    _rewrite_json(ownership_path, ownership)

    with pytest.raises(DocumentationIntegrityError, match="control artifacts changed"):
        record_documentation_agent_result(workspace, _result(run.run_id))


def test_packet_rejects_source_baseline_rewritten_to_hide_source_change(
    tmp_path: Path,
):
    source = tmp_path / "source"
    source.mkdir()
    source_file = source / "app.py"
    source_file.write_text("VALUE = 1\n", encoding="utf-8")
    input_wiki = tmp_path / "input wiki"
    input_wiki.mkdir()
    (input_wiki / "index.md").write_text("# Example\n", encoding="utf-8")
    source_hash = source_tree_baseline(source).file_hashes["app.py"]
    _rewrite_json(
        input_wiki / ".llm-wiki-manifest.json",
        {
            "version": 4,
            "sources": {"app.py": {"hash": source_hash}},
            "surfaces": {},
            "generation_inputs": {},
        },
    )
    _rewrite_json(
        input_wiki / ".llm-wiki-surface.json",
        {
            "schema_version": "llm-wiki-surface-index/v1",
            "source_hash": "sha256:" + "0" * 64,
            "pages": [
                {
                    "kind": "index",
                    "id": "index",
                    "canonical_path": "index.md",
                    "source_path": None,
                    "role": "mixed",
                }
            ],
        },
    )
    workspace = tmp_path / "workspace"
    prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        source_root=source,
        input_wiki_root=input_wiki,
        freshness_policy="allow-unverified",
        site_name="Example",
    )

    source_file.write_text("VALUE = 2\n", encoding="utf-8")
    baseline_path = workspace / ".llm-wiki-docs" / "evidence" / "source-baseline.json"
    _rewrite_json(baseline_path, source_tree_baseline(source).to_dict())

    with pytest.raises(DocumentationIntegrityError, match="source-baseline evidence"):
        build_documentation_agent_packet(workspace, stage="wiki-enrichment")


def test_resume_rejects_source_baseline_rewritten_to_hide_source_change(
    tmp_path: Path,
):
    source = tmp_path / "source"
    source.mkdir()
    source_file = source / "app.py"
    source_file.write_text("VALUE = 1\n", encoding="utf-8")
    workspace = tmp_path / "workspace"
    prepare_documentation_run(
        workspace,
        baseline_strategy="bootstrap_source",
        source_root=source,
        site_name="Example",
    )

    source_file.write_text("VALUE = 2\n", encoding="utf-8")
    baseline_path = workspace / ".llm-wiki-docs" / "evidence" / "source-baseline.json"
    _rewrite_json(baseline_path, source_tree_baseline(source).to_dict())

    with pytest.raises(
        (DocumentationIntegrityError, DocumentationRunError),
        match="source-baseline evidence",
    ):
        prepare_documentation_run(
            workspace,
            baseline_strategy="bootstrap_source",
            source_root=source,
            site_name="Example",
        )


def test_packet_rejects_rewritten_generated_baseline_before_dispatch(tmp_path: Path):
    input_wiki = tmp_path / "input wiki"
    (input_wiki / "modules").mkdir(parents=True)
    (input_wiki / "index.md").write_text("# Example\n", encoding="utf-8")
    module = input_wiki / "modules" / "core.md"
    module.write_text(
        "# core\n\n## Relationships\n\n"
        "<!-- Auto-generated relationship summary. Do not edit by hand. -->\n"
        "original\n",
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"
    prepare_documentation_run(
        workspace,
        baseline_strategy="adopt_existing_wiki",
        input_wiki_root=input_wiki,
        freshness_policy="allow-unverified",
        site_name="Example",
    )

    workspace_module = workspace / "wiki" / "modules" / "core.md"
    workspace_module.write_text(
        workspace_module.read_text(encoding="utf-8").replace("original", "forged"),
        encoding="utf-8",
    )
    ownership_path = (
        workspace / ".llm-wiki-docs" / "evidence" / "generated-ownership.json"
    )
    _rewrite_json(
        ownership_path,
        {"fingerprints": capture_generated_ownership(workspace / "wiki")},
    )

    with pytest.raises(
        DocumentationIntegrityError, match="generated-ownership evidence"
    ):
        build_documentation_agent_packet(workspace, stage="wiki-enrichment")


def test_result_rejects_packet_bytes_changed_after_dispatch(tmp_path: Path):
    workspace, run = _prepare(tmp_path)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    packet_path = workspace / ".llm-wiki-docs" / "packets" / "wiki-enrichment-01.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    packet["tampered_note"] = "changed after supervisor dispatch"
    _rewrite_json(packet_path, packet)

    with pytest.raises(DocumentationIntegrityError, match="packet bytes"):
        record_documentation_agent_result(workspace, _result(run.run_id))


def test_result_rejects_dispatch_receipt_change(tmp_path: Path):
    workspace, run = _prepare(tmp_path)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    receipt_path = (
        workspace / ".llm-wiki-docs" / "stages" / "02-wiki-enrichment-01-packet.json"
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["pre_stage_evidence_hash"] = "sha256:" + "0" * 64
    _rewrite_json(receipt_path, receipt)

    with pytest.raises(DocumentationIntegrityError, match="Pre-stage evidence bytes"):
        record_documentation_agent_result(workspace, _result(run.run_id))


@pytest.mark.parametrize("error_number", [errno.EINVAL, errno.ENOTSUP])
def test_directory_fsync_unsupported_after_replace_is_not_false_failure(
    monkeypatch: pytest.MonkeyPatch,
    error_number: int,
):
    def unsupported(_descriptor):
        raise OSError(error_number, "directory fsync unsupported")

    monkeypatch.setattr(documentation_run_service.os, "fsync", unsupported)
    assert documentation_run_service._fsync_directory_after_replace(42) is False


def test_directory_fsync_real_io_error_remains_fatal(
    monkeypatch: pytest.MonkeyPatch,
):
    def failed(_descriptor):
        raise OSError(errno.EIO, "storage failure")

    monkeypatch.setattr(documentation_run_service.os, "fsync", failed)
    with pytest.raises(OSError, match="storage failure"):
        documentation_run_service._fsync_directory_after_replace(42)


def test_pathname_fallback_enters_windows_guard_before_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    workspace, _ = _prepare(tmp_path)
    target = workspace / ".llm-wiki-docs" / "evidence" / "fallback-write.json"
    events: list[str] = []

    @contextmanager
    def fake_guard(root, components, *, create_missing=False):
        assert root == workspace
        assert components == (".llm-wiki-docs", "evidence")
        assert create_missing is False
        events.append("guard-enter")
        try:
            yield target.parent
        finally:
            events.append("guard-exit")

    def guarded_write(path, text):
        assert events == ["guard-enter"]
        events.append("write")
        Path(path).write_text(text, encoding="utf-8")

    monkeypatch.setattr(
        documentation_run_service,
        "_supports_descriptor_bound_workspace_writes",
        lambda: False,
    )
    monkeypatch.setattr(
        documentation_run_service,
        "_uses_windows_guarded_path_writes",
        lambda: True,
    )
    monkeypatch.setattr(
        documentation_run_service,
        "guard_windows_directory_chain",
        fake_guard,
    )
    monkeypatch.setattr(
        documentation_run_service,
        "write_text_output",
        guarded_write,
    )

    documentation_run_service._write_workspace_text(workspace, target, "{}\n")

    assert events == ["guard-enter", "write", "guard-exit"]
