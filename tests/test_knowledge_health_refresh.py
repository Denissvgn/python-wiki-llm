"""Producer refresh preserves packed evidence and the health failure boundary."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.api_types import DoctorResult
from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services import (
    bootstrap_runtime,
    knowledge_orchestration,
    knowledge_reuse,
)
from llm_wiki_cli.services.ci_report import build_ci_check_payload
from llm_wiki_cli.services.doctor_service import compose_doctor_report
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.lint_service import build_report
from llm_wiki_cli.services.markdown_sections import replace_section_body


def _version(monkeypatch, value):
    for module in (
        bootstrap_cmd, sync_cmd, bootstrap_runtime,
        knowledge_orchestration, knowledge_reuse,
    ):
        monkeypatch.setattr(module, "__version__", value)


def _files(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*") if path.is_file()
    }


def _command(arguments):
    with patch.object(sys, "argv", ["llm-wiki", *arguments]):
        cli.main()


def _sync(*flags):
    _command([
        "sync", "--src-dir", "source", "--wiki-dir", "wiki",
        "--no-plugins", *flags,
    ])


def _health(**kwargs):
    report = build_report(
        "wiki", "source", strict=True, knowledge_drift_report=True,
        include_plugins=False, **kwargs,
    )
    strict = cast(DoctorResult, compose_doctor_report(
        report, strict=True, wiki_dir="wiki", src_dir="source",
    ).to_payload())
    return report, strict, build_ci_check_payload(report)


@pytest.fixture
def recorded_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subprocess.run(
        ["git", "init", "-q"], check=True, capture_output=True,
    )
    source = tmp_path / "source"
    source.mkdir()
    (source / "models.py").write_text(
        'class User:\n    """A named user."""\n    name: str\n', encoding="utf-8",
    )
    (source / "service.py").write_text(
        "from models import User\n\ndef main(user: User) -> str:\n"
        "    return user.name\n", encoding="utf-8",
    )
    (source / "pyproject.toml").write_text(
        '[project]\nname="health-fixture"\nversion="0.1.0"\n'
        '[project.scripts]\nhealth-fixture="service:main"\n', encoding="utf-8",
    )
    _version(monkeypatch, "9.8.6")
    _command([
        "bootstrap", "--src-dir", "source", "--wiki-dir", "wiki",
        "--source-adapter", "--knowledge-format", "packed-v4-deflate",
    ])
    wiki = tmp_path / "wiki"
    page = wiki / "modules/service.md"
    authored = "Maintained usage notes: callers receive a stable user label."
    page.write_text(
        replace_section_body(page.read_text(encoding="utf-8"), "Description", authored),
        encoding="utf-8",
    )
    _sync()
    report, health, _ = _health()
    assert report.passed and health["status"] == "healthy"
    assert json.loads((wiki / ".llm-wiki-knowledge.json").read_text())["schema_version"] == "llm-wiki-knowledge/v4"
    return source, wiki, page, authored


@pytest.mark.parametrize("flags", [(), ("--no-cache",), ("--rebuild-knowledge",)])
@pytest.mark.parametrize("source_changed", [False, True])
def test_producer_upgrade_refreshes_packed_health_and_preserves_authorship(
    recorded_project, monkeypatch, source_changed, flags,
):
    source, wiki, page, authored = recorded_project
    before = load_knowledge_state(wiki).knowledge
    assert before is not None and before.bundle.producer.tool.version == "9.8.6"
    if source_changed:
        model = source / "models.py"
        model.write_text(
            model.read_text().replace("    name: str", "    name: str\n    active: bool"),
            encoding="utf-8",
        )
    _version(monkeypatch, "9.8.7")
    report, strict, ci = _health()
    assert report.passed is (not source_changed)
    assert ci["ok"] is (not source_changed)
    if source_changed:
        assert any(issue.category == "sync_manifest" for issue in report.issues)
    assert ci["knowledge_drift_gate"] is False
    assert cast(DoctorResult, ci["knowledge_health"])["status"] == "degraded"
    assert strict["status"] == "unhealthy"
    assert strict["drift"]["reasons"] == ["producer-tool-version-changed"]
    assert strict["drift"]["indeterminate"] > 0

    _sync(*flags)

    after = load_knowledge_state(wiki).knowledge
    assert after is not None and after.bundle.producer.tool.version == "9.8.7"
    assert {component.version for component in after.bundle.producer.extractors} == {"9.8.7"}
    assert before.bundle.snapshot.generation_options_hash == after.bundle.snapshot.generation_options_hash
    assert authored in page.read_text(encoding="utf-8")
    if source_changed:
        assert "active" in (wiki / "entities/User.md").read_text(encoding="utf-8")
    source_files, wiki_files = _files(source), _files(wiki)
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"])
    report, strict, ci = _health()
    assert report.passed and strict["status"] == "healthy"
    assert cast(DoctorResult, ci["knowledge_health"])["status"] == "healthy"
    assert strict["drift"]["state"] == "current"
    assert strict["drift"]["indeterminate"] == strict["drift"]["confirmed_stale"] == 0
    counts = strict["freshness"]["counts_by_state"]
    assert counts is not None and counts["current"] > 0 and counts["unknown"] > 0
    assert strict["governance"]["state"] == "not-present"
    assert strict["verification_receipt"]["state"] == "absent"
    assert _files(source) == source_files and _files(wiki) == wiki_files
    assert subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"]) == status

    _sync(*flags)
    assert _files(wiki) == wiki_files
    assert _files(source) == source_files


@pytest.mark.parametrize("change, expected_state, expected_reason", [
    ("source", "stale-confirmed", "concept-observation-changed"),
    ("missing", "stale-confirmed", "reliably-mapped-source-missing"),
    ("comment", "nonsemantic-change", "source-bytes-changed-concept-observation-unchanged"),
    ("unknown-producer", "indeterminate", "version-unknown"),
    ("options", "indeterminate", "generation-options-changed"),
])
def test_refreshed_evidence_does_not_mask_later_drift(
    recorded_project, monkeypatch, change, expected_state, expected_reason,
):
    source, wiki, _page, _authored = recorded_project
    _version(monkeypatch, "9.8.7")
    _sync()
    model = source / "models.py"
    kwargs = {}
    if change == "source":
        model.write_text(model.read_text() + "    active: bool\n", encoding="utf-8")
    elif change == "missing":
        model.unlink()
    elif change == "comment":
        model.write_text(model.read_text() + "\n# Clarified explanation.\n", encoding="utf-8")
    elif change == "unknown-producer":
        _version(monkeypatch, "unknown")
    else:
        kwargs["include_tests"] = ["go"]
    before = _files(wiki)

    _report, strict, ci = _health(**kwargs)

    assert strict["status"] == "unhealthy"
    assert strict["drift"]["state"] == expected_state
    assert expected_reason in strict["drift"]["reasons"]
    assert cast(DoctorResult, ci["knowledge_health"])["status"] == (
        "unhealthy" if expected_state == "stale-confirmed" else "degraded"
    )
    assert _files(wiki) == before
