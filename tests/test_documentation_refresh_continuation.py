"""Focused source-revision continuation tests for documentation workspaces."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import llm_wiki_cli.services.documentation_run as documentation_run_service
from llm_wiki_cli.services.bootstrap_service import BootstrapResult
from llm_wiki_cli.services.contracts import DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION
from llm_wiki_cli.services.documentation_run import (
    DocumentationIntegrityError,
    build_documentation_agent_packet,
    prepare_documentation_run,
    record_documentation_agent_result,
)


def _install_fake_bootstrap(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_execute(request):
        source = Path(request.source_root)
        wiki = Path(request.wiki_root)
        revision_text = (source / "app.py").read_text(encoding="utf-8").strip()
        revision = "v2" if "second revision" in revision_text else "v1"
        (wiki / "modules").mkdir(parents=True, exist_ok=True)
        (wiki / "index.md").write_text(
            "# LLM Wiki Index\n\nUse this landing page to choose the right wiki surface.\n\n"
            "## Modules\n\n- [app](modules/app.md)\n",
            encoding="utf-8",
        )
        generated_description = "_Auto-generated from `app.py`._"
        (wiki / "modules" / "app.md").write_text(
            "# app Module\n\n**Path:** `app.py`\n\n## Description\n\n"
            f"{generated_description}\n\n## Local dependency map\n\n"
            "<!-- Auto-generated local dependency summary. Do not edit by hand. -->\n\n"
            f"Generated dependency evidence for {revision}.\n",
            encoding="utf-8",
        )
        (wiki / ".llm-wiki-manifest.json").write_text(
            json.dumps(
                {
                    "version": 4,
                    "sources": {
                        "app.py": {
                            "hash": (
                                "sha256:" + ("1" if revision == "v1" else "2") * 64
                            ),
                            "module_page": "app",
                            "entity_pages": {},
                            "entity_page_occurrences": [],
                            "generated_semantics": {
                                "module": {
                                    "description": generated_description,
                                    "classes": {},
                                    "functions": {},
                                },
                                "entities": {},
                            },
                        }
                    },
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (wiki / ".llm-wiki-surface.json").write_text(
            json.dumps(
                {
                    "schema_version": "llm-wiki-surface/v1",
                    "pages": [
                        {
                            "canonical_path": "modules/app.md",
                            "source_path": "app.py",
                        }
                    ],
                    "flows": [],
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return BootstrapResult(
            summary={
                "schema_version": "llm-wiki-bootstrap/v1",
                "src_dir": str(source),
                "generated_wiki_path": str(wiki),
                "created_files": [],
                "updated_files": [],
                "skipped_files": [],
                "unsupported_sources": {},
                "dependencies": {},
            }
        )

    monkeypatch.setattr(
        "llm_wiki_cli.commands.bootstrap_cmd.execute_bootstrap", fake_execute
    )
    monkeypatch.setattr(
        "llm_wiki_cli.services.documentation_run._run_wiki_validation_pair",
        lambda *args, **kwargs: True,
    )


def _prepare_source_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _install_fake_bootstrap(monkeypatch)
    source = tmp_path / "source Ω"
    source.mkdir()
    (source / "app.py").write_text("first revision\n", encoding="utf-8")
    workspace = tmp_path / "documentation workspace Ω"
    run = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Continuation Docs",
    )
    return source, workspace, run


def test_explicit_refresh_preserves_semantics_and_requires_regrounding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, prior = _prepare_source_run(tmp_path, monkeypatch)
    build_documentation_agent_packet(workspace, stage="wiki-enrichment")
    module = workspace / "wiki" / "modules" / "app.md"
    module.write_text(
        module.read_text(encoding="utf-8").replace(
            "_Auto-generated from `app.py`._",
            "The prior agent explains how the application coordinates operator requests.",
        ),
        encoding="utf-8",
    )
    worklist = json.loads(
        (workspace / prior.evidence["semantic_worklist"]).read_text(encoding="utf-8")
    )
    items = [item for item in worklist["items"] if item.get("canonical_path")]
    record_documentation_agent_result(
        workspace,
        {
            "schema_version": DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
            "run_id": prior.run_id,
            "stage": "wiki-enrichment",
            "status": "complete",
            "changed_wiki_paths": ["modules/app.md"],
            "reused_work_ids": [],
            "completed_work_ids": [item["id"] for item in items],
            "deferred_work_ids": [],
            "claims_evidence_pages": sorted(
                {str(item["canonical_path"]) for item in items}
            ),
            "unresolved_unknowns": [],
            "unsupported_source_notices": [],
            "requested_follow_up_checks": [],
            "reported_source_writes": [],
            "reported_input_wiki_writes": [],
            "reported_generated_block_edits": [],
            "deferral_rationales": {},
            "findings": [],
        },
    )

    (source / "app.py").write_text("second revision\n", encoding="utf-8")
    refreshed = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Continuation Docs",
        refresh=True,
    )

    assert refreshed.run_id != prior.run_id
    refreshed_text = module.read_text(encoding="utf-8")
    assert "prior agent explains" in refreshed_text
    assert "Generated dependency evidence for v2" in refreshed_text
    assert "Generated dependency evidence for v1" not in refreshed_text

    continuation = json.loads(
        (workspace / refreshed.evidence["continuation"]).read_text(encoding="utf-8")
    )
    assert continuation["prior_run_id"] == prior.run_id
    assert continuation["prior_source_revision"] == prior.source["revision"]
    assert continuation["source_revision"] == refreshed.source["revision"]
    assert continuation["preserved_semantic_paths"] == ["modules/app.md"]
    assert continuation["preserved_semantic_hash"].startswith("sha256:")
    archive = workspace / continuation["archive_path"]
    assert (archive / "run.json").is_file()
    assert (archive / "wiki" / "modules" / "app.md").is_file()

    refreshed_worklist = json.loads(
        (workspace / refreshed.evidence["semantic_worklist"]).read_text(
            encoding="utf-8"
        )
    )
    continued = next(
        item
        for item in refreshed_worklist["items"]
        if item.get("canonical_path") == "modules/app.md"
    )
    assert continued["imported_classification"] == "needs_grounding"
    assert continued["grounding_status"] == "unknown"
    assert continued["status"] == "open"
    assert "continuation:source_revision_changed" in continued["signals"]
    assert "evidence:continuation.json" in continued["suggested_context"]


def test_refresh_refuses_changed_generated_ownership_before_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, prior = _prepare_source_run(tmp_path, monkeypatch)
    module = workspace / "wiki" / "modules" / "app.md"
    module.write_text(
        module.read_text(encoding="utf-8").replace(
            "Generated dependency evidence for v1",
            "Agent changed a protected generated block",
        ),
        encoding="utf-8",
    )
    (source / "app.py").write_text("second revision\n", encoding="utf-8")

    with pytest.raises(DocumentationIntegrityError, match="generated ownership"):
        prepare_documentation_run(
            workspace,
            source_root=source,
            site_name="Continuation Docs",
            refresh=True,
        )

    assert (
        json.loads(
            (workspace / ".llm-wiki-docs" / "run.json").read_text(encoding="utf-8")
        )["run_id"]
        == prior.run_id
    )
    history = workspace / ".llm-wiki-docs" / "history"
    assert not history.exists() or not any(history.iterdir())


def test_refresh_failure_after_archive_restores_prior_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, prior = _prepare_source_run(tmp_path, monkeypatch)
    prior_module = (workspace / "wiki" / "modules" / "app.md").read_bytes()
    (source / "app.py").write_text("second revision\n", encoding="utf-8")

    def fail_after_archive(_workspace_root):
        raise RuntimeError("injected post-archive failure")

    monkeypatch.setattr(
        documentation_run_service,
        "_export_documentation_skills",
        fail_after_archive,
    )
    with pytest.raises(RuntimeError, match="post-archive"):
        prepare_documentation_run(
            workspace,
            source_root=source,
            site_name="Continuation Docs",
            refresh=True,
        )

    restored = json.loads(
        (workspace / ".llm-wiki-docs" / "run.json").read_text(encoding="utf-8")
    )
    assert restored["run_id"] == prior.run_id
    assert (workspace / "wiki" / "modules" / "app.md").read_bytes() == prior_module
    assert not (workspace / ".llm-wiki-docs" / "refresh-transaction.json").exists()


def test_prepare_recovers_interrupted_refresh_archive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, workspace, prior = _prepare_source_run(tmp_path, monkeypatch)
    transaction = documentation_run_service._RefreshArchiveTransaction()
    documentation_run_service._archive_owned_run(
        workspace,
        prior,
        transaction=transaction,
    )
    assert not (workspace / ".llm-wiki-docs" / "run.json").exists()
    assert (workspace / ".llm-wiki-docs" / "refresh-transaction.json").is_file()

    resumed = prepare_documentation_run(
        workspace,
        source_root=source,
        site_name="Continuation Docs",
    )

    assert resumed.run_id == prior.run_id
    assert not (workspace / ".llm-wiki-docs" / "refresh-transaction.json").exists()
