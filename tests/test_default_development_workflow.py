"""Project initialization and portable development consumer qualification."""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.commands import init_cmd, upgrade_cmd, uninstall_cmd
from llm_wiki_cli.config import read_config
from llm_wiki_cli.services.schema import SCHEMA_FILENAMES, SchemaRenderProfile, build_schema_content
from llm_wiki_cli.services.skills import ReferenceSkillState, skills_install_dir, verify_reference_skill


@pytest.mark.parametrize("agent", ["generic", "claude", "cursor", "copilot", "aider", "opencode"])
@pytest.mark.parametrize("no_skills", [False, True])
def test_default_workflow_installation_and_upgrade_preserve_project_policy(tmp_path, monkeypatch, agent, no_skills):
    monkeypatch.chdir(tmp_path)
    wiki = "knowledge/project notes"
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("def cap(limit=3):\n    return limit\n")
    selection = Path("config/public sources.json")
    selection.parent.mkdir()
    selection.write_text(json.dumps({"schema_version": "llm-wiki-source-selection/v1", "include": ["src"], "exclude": []}))
    schema = Path(SCHEMA_FILENAMES[agent])
    schema.parent.mkdir(parents=True, exist_ok=True)
    prefix = b"# Preserve this project convention.\r\n\r\n"
    schema.write_bytes(prefix)
    init_cmd.run(SimpleNamespace(agent=agent, wiki_dir=wiki, no_skills=no_skills, source_selection=str(selection)))
    content = schema.read_bytes()
    assert content.startswith(prefix)
    expected_profile = b"expanded_inline" if no_skills else b"compact"
    assert b"profile=" + expected_profile in content
    assert b"development-workflow.md" in content
    reference = skills_install_dir(agent) / "wiki-reference"
    assert (reference / "references/development-workflow.md").is_file() is not no_skills
    assert not (skills_install_dir(agent) / "native-coding").exists()
    assert read_config(wiki)["reference_skill"] is not no_skills
    assert read_config(wiki)["issue_reporting"] is False
    assert not (Path(wiki) / ".llm-wiki-maintenance-adoption.json").exists()
    if no_skills:
        # The fallback must supply operations without relying on a missing topic.
        for obligation in [b"independent acceptance criteria", b"run those checks", b"reconcile or", b"every required", b"environment failure"]:
            assert obligation in content
        assert not reference.exists()
        assert b"doctor --analysis-inputs --format json" in content
    else:
        assert verify_reference_skill(agent=agent).state is ReferenceSkillState.CURRENT
        assert "doctor --analysis-inputs --format json" in (reference / "references/development-workflow.md").read_text()
        # Simulate the previous exact tree; upgrade must recover the new topic.
        (reference / "references/development-workflow.md").unlink()
        assert verify_reference_skill(agent=agent).state is ReferenceSkillState.INCOMPLETE
    upgrade_cmd.run(SimpleNamespace(agent=None, wiki_dir=wiki))
    upgraded = schema.read_bytes()
    assert upgraded.startswith(prefix)
    assert b"profile=" + expected_profile in upgraded
    assert read_config(wiki)["source_selection"] == str(selection)
    if not no_skills:
        assert verify_reference_skill(agent=agent).state is ReferenceSkillState.CURRENT
    else:
        assert not reference.exists()


@pytest.mark.parametrize("agent", list(SCHEMA_FILENAMES))
def test_missing_reference_falls_back_to_complete_inline_workflow(tmp_path, monkeypatch, agent):
    from llm_wiki_cli.services.skills import provision_reference_skill
    monkeypatch.chdir(tmp_path)
    provision_reference_skill(agent=agent)
    topic = skills_install_dir(agent) / "wiki-reference/references/development-workflow.md"
    topic.write_text("# Locally authored guidance\nPreserve me.\n")
    init_cmd.run(SimpleNamespace(agent=agent, wiki_dir="knowledge"))
    assert topic.read_text() == "# Locally authored guidance\nPreserve me.\n"
    schema = Path(SCHEMA_FILENAMES[agent]).read_text()
    assert "profile=expanded_inline" in schema
    assert "run those checks" in schema and "every required" in schema


@pytest.mark.parametrize("agent", list(SCHEMA_FILENAMES))
@pytest.mark.parametrize("profile", list(SchemaRenderProfile))
def test_all_maintenance_recipes_preserve_custom_wiki_and_selection(agent, profile):
    wiki = "knowledge/project notes"
    selection = "config/public sources.json"
    content = build_schema_content(agent, wiki, render_profile=profile, source_selection=selection)
    parser = cli._build_parser()
    # Parse each executable recipe, including multiline inline code.
    commands = re.findall(r"`(llm-wiki (?:sync|lint|generate-prompt)\b[^`]+)`", content)
    commands += re.findall(r"^\s*(llm-wiki (?:sync|lint|generate-prompt)\b[^\n]+)$", content, re.M)
    if profile is SchemaRenderProfile.EXPANDED_INLINE:
        assert {shlex.split(c)[1] for c in commands} == {"sync", "lint", "generate-prompt"}
    for command in commands:
        argv = shlex.split(command)
        args = parser.parse_args(argv[1:])
        assert args.wiki_dir == wiki, command
        assert args.source_selection == selection, command


def test_helper_recovery_routes_are_valid_and_keep_read_selection():
    # Validate through the actual CLI planning route rather than installing tools.
    for argv in [
        ["prepare-extractors", "--language", "typescript", "--plan", "--format", "json"],
        ["prepare-extractors", "--src-dir", ".", "--source-selection", ".llm-wiki/source-selection.json", "--plan", "--format", "json"],
    ]:
        run = subprocess.run([sys.executable, "-m", "llm_wiki_cli.cli", *argv], capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        assert "typescript" in json.loads(run.stdout)["languages"]


def test_source_only_consumer_can_verify_and_resume_without_adoption(tmp_path, monkeypatch):
    consumer = Path(__file__).resolve().parents[1] / "examples/native-workflow/project"
    shutil.copytree(consumer, tmp_path, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    monkeypatch.chdir(tmp_path)
    init_cmd.run(SimpleNamespace(agent="generic", wiki_dir="knowledge", no_skills=True))
    request = {"schema_version": "llm-wiki-task-request/v2", "kind": "contract-change",
               "requirements": [{"id": "cap", "facet": "source-contract", "selector": "policy.py:cap"},
                                {"id": "behavior", "facet": "behavior", "selector": "policy.py:cap"}],
               "options": {"knowledge_mode": "off", "read_scope": "selected", "budget_tokens": 16000}}
    captured = api.build_task_context(request, src_dir="src", wiki_dir="knowledge")
    assert captured.ok
    payload = api.validate_task_context(captured.rendered, request)
    assert payload["state"] == "incomplete"
    behavior = next(row for row in payload["coverage"] if row["requirement_id"] == "behavior")
    assert not behavior["satisfied"]
    code = f"import sys; sys.path.insert(0, {str(tmp_path / 'src')!r}); from policy import cap; assert cap([1,2,3], 3) == [1,2,3]"
    before = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True)
    assert before.returncode != 0
    path = Path("src/policy.py")
    text = path.read_text()
    assert "values[:limit - 1]" in text
    path.write_text(text.replace("values[:limit - 1]", "values[:limit]"))
    after = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True)
    assert after.returncode == 0, after.stderr
    resumed = api.reconcile_task_context(captured.rendered, request, src_dir="src", wiki_dir="knowledge")
    assert not resumed["basis_matches"]
    assert not (Path("knowledge") / ".llm-wiki-maintenance-adoption.json").exists()
    assert not (Path("knowledge") / ".llm-wiki-knowledge.json").exists()


@pytest.mark.parametrize("modified", [False, True])
def test_uninstall_removes_owned_workflow_but_preserves_local_drift(tmp_path, monkeypatch, modified):
    monkeypatch.chdir(tmp_path)
    schema = Path("AGENTS.md")
    schema.write_text("# Keep project rules.\n")
    init_cmd.run(SimpleNamespace(agent="generic", wiki_dir="knowledge"))
    reference = skills_install_dir("generic") / "wiki-reference"
    topic = reference / "references/development-workflow.md"
    if modified:
        topic.write_text("# Local workflow\nKeep this authored content.\n")
    monkeypatch.setattr(uninstall_cmd, "_confirm", lambda prompt: True)
    uninstall_cmd.run(SimpleNamespace(wiki_dir="knowledge", remove_wiki=False, dry_run=False))
    assert schema.read_text().strip() == "# Keep project rules."
    assert Path("knowledge/index.md").exists()
    if modified:
        assert topic.read_text() == "# Local workflow\nKeep this authored content.\n"
    else:
        assert not reference.exists()
