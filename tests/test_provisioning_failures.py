"""Failure and downgrade coverage for managed-reference provisioning."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli.commands import init_cmd, status_cmd, upgrade_cmd
from llm_wiki_cli.config import (
    AgentConfigState,
    get_agent_config_path,
    inspect_config,
    read_config,
    write_config,
)
from llm_wiki_cli.services import skills
from llm_wiki_cli.services.rendering_lifecycle import (
    ManagedLifecycleState,
    classify_lifecycle_status,
)
from llm_wiki_cli.services.schema import (
    CONSTRAINT_END,
    CONSTRAINT_START,
    ManagedSchemaBlock,
    ManagedSchemaBlockState,
    ManagedSchemaPathError,
    SchemaRenderProfile,
    build_schema_content,
    build_skill_block,
    classify_managed_schema_block,
    replace_schema_block_content,
    strip_wiki_block,
)
from llm_wiki_cli.services.skills import (
    REFERENCE_SKILL_ID,
    ReferenceSkillProvisionResult,
    ReferenceSkillReason,
    ReferenceSkillState,
    ReferenceSkillVerification,
    SkillsReport,
    skills_install_dir,
    verify_reference_skill,
)

WIKI_DIR = "docs/llm_wiki"


def _init_args(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "agent": "generic",
        "wiki_dir": WIKI_DIR,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _upgrade_args(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "agent": None,
        "wiki_dir": WIKI_DIR,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _status_args() -> SimpleNamespace:
    return SimpleNamespace(
        wiki_dir=WIKI_DIR,
        src_dir=".",
        allow_external_src=False,
        source_selection=None,
    )


def _profile(path: str | Path) -> SchemaRenderProfile:
    block = classify_managed_schema_block(Path(path).read_text(encoding="utf-8"))
    assert block.state is ManagedSchemaBlockState.PROFILED
    assert block.profile is not None
    return block.profile


def _provision_result(
    state: ReferenceSkillState,
    *,
    agent: str,
) -> ReferenceSkillProvisionResult:
    reason_by_state = {
        ReferenceSkillState.ABSENT: ReferenceSkillReason.ABSENT,
        ReferenceSkillState.CURRENT: ReferenceSkillReason.CURRENT,
        ReferenceSkillState.LOCALLY_MODIFIED: ReferenceSkillReason.LOCALLY_MODIFIED,
        ReferenceSkillState.INCOMPLETE: ReferenceSkillReason.INCOMPLETE,
        ReferenceSkillState.PACKAGE_MISSING: ReferenceSkillReason.PACKAGE_MISSING,
        ReferenceSkillState.INSTALL_ERROR: ReferenceSkillReason.INSTALL_ERROR,
    }
    path = skills_install_dir(agent) / REFERENCE_SKILL_ID
    verification = ReferenceSkillVerification(
        state=state,
        reason=reason_by_state[state],
        path=path,
    )
    return ReferenceSkillProvisionResult(
        state=state,
        reason=reason_by_state[state],
        path=path,
        details=(),
        verification=verification,
        report=None,
    )


def _initialize_current(agent: str = "generic") -> None:
    init_cmd.run(_init_args(agent=agent))
    assert verify_reference_skill(agent=agent).current


def test_default_init_commits_compact_only_after_exact_reference(tmp_project) -> None:
    init_cmd.run(_init_args())

    config = read_config(WIKI_DIR)
    assert _profile("AGENTS.md") is SchemaRenderProfile.COMPACT
    assert verify_reference_skill(agent="generic").current
    assert config["reference_skill"] is True
    assert config["rendered_profile"] == "compact"
    assert config["render_profile_version"] == 1
    assert config["render_reason"] == "reference-current"


def test_no_skills_init_is_expanded_even_when_a_stale_reference_exists(
    tmp_project,
    capsys,
) -> None:
    _initialize_current()
    reference = Path(".llm-wiki/skills/wiki-reference/reference.md")
    reference.write_text("local copy\n", encoding="utf-8")

    init_cmd.run(_init_args(no_skills=True))

    config = read_config(WIKI_DIR)
    assert reference.read_text(encoding="utf-8") == "local copy\n"
    assert _profile("AGENTS.md") is SchemaRenderProfile.EXPANDED_INLINE
    assert config["reference_skill"] is False
    assert config["rendered_profile"] == "expanded_inline"
    assert config["render_reason"] == "skills-disabled"
    output = capsys.readouterr().out
    assert "managed-reference-disabled" in output
    assert "llm-wiki upgrade --skills" in output
    assert "init or upgrade option" not in output


@pytest.mark.parametrize("failure_mode", ["exception", "failed-report"])
def test_init_install_failure_never_emits_compact(
    tmp_project,
    monkeypatch,
    capsys,
    failure_mode: str,
) -> None:
    if failure_mode == "exception":

        def fail_install(*_args, **_kwargs):
            raise OSError("injected install failure")

        monkeypatch.setattr(skills, "install_reference_skill", fail_install)
    else:

        def failed_report(*_args, **_kwargs) -> SkillsReport:
            return SkillsReport(
                ok=False,
                dest_dir=".llm-wiki/skills",
                skills=[REFERENCE_SKILL_ID],
                issues=[
                    {
                        "category": "write_failed",
                        "path": ".llm-wiki/skills/wiki-reference/SKILL.md",
                    }
                ],
            )

        monkeypatch.setattr(skills, "install_reference_skill", failed_report)

    init_cmd.run(_init_args())

    output = capsys.readouterr().out
    config = read_config(WIKI_DIR)
    assert _profile("AGENTS.md") is SchemaRenderProfile.EXPANDED_INLINE
    assert config["rendered_profile"] == "expanded_inline"
    assert config["render_reason"] == "install-error"
    assert "managed-reference-install-failed" in output
    assert (
        "llm-wiki skills install --dest .llm-wiki/skills --skill wiki-reference --force"
    ) in output


def test_missing_packaged_topic_is_preflighted_before_destination_mutation(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    broken_root = Path("broken-bundled-skills")
    shutil.copytree(
        skills.BUNDLED_SKILLS_ROOT / REFERENCE_SKILL_ID,
        broken_root / REFERENCE_SKILL_ID,
    )
    (broken_root / REFERENCE_SKILL_ID / "references/governance.md").unlink()
    monkeypatch.setattr(skills, "BUNDLED_SKILLS_ROOT", broken_root)

    init_cmd.run(_init_args())

    output = capsys.readouterr().out
    config = read_config(WIKI_DIR)
    assert _profile("AGENTS.md") is SchemaRenderProfile.EXPANDED_INLINE
    assert config["render_reason"] == "package-missing"
    assert not Path(".llm-wiki/skills/wiki-reference").exists()
    assert "repair or update the installed llm-wiki package" in output
    assert "knowledge init" not in output


@pytest.mark.parametrize(
    ("damage", "expected_reason"),
    [
        ("modified", "reference-modified"),
        ("incomplete", "reference-incomplete"),
    ],
)
def test_init_preserves_damaged_tree_and_uses_expanded_profile(
    tmp_project,
    damage: str,
    expected_reason: str,
) -> None:
    _initialize_current()
    target = Path(".llm-wiki/skills/wiki-reference/reference.md")
    if damage == "modified":
        target.write_text("local policy\n", encoding="utf-8")
    else:
        target.unlink()
        target.mkdir()

    init_cmd.run(_init_args())

    config = read_config(WIKI_DIR)
    assert target.exists()
    if damage == "modified":
        assert target.read_text(encoding="utf-8") == "local policy\n"
    else:
        assert target.is_dir()
    assert _profile("AGENTS.md") is SchemaRenderProfile.EXPANDED_INLINE
    assert config["rendered_profile"] == "expanded_inline"
    assert config["render_reason"] == expected_reason


def test_init_with_local_drift_and_missing_topic_rejects_compact(
    tmp_project,
    capsys,
) -> None:
    _initialize_current()
    reference = Path(".llm-wiki/skills/wiki-reference")
    modified = reference / "references/maintenance.md"
    missing = reference / "references/governance.md"
    modified.write_text("local policy\n", encoding="utf-8")
    missing.unlink()

    init_cmd.run(_init_args())

    output = capsys.readouterr().out
    config = read_config(WIKI_DIR)
    assert modified.read_text(encoding="utf-8") == "local policy\n"
    assert missing.is_file()
    assert _profile("AGENTS.md") is SchemaRenderProfile.EXPANDED_INLINE
    assert config["rendered_profile"] == "expanded_inline"
    assert config["render_reason"] == "reference-modified"
    assert "managed-reference-modified" in output
    assert "--skill wiki-reference --force" in output


@pytest.mark.parametrize("command", ["init", "upgrade"])
def test_reference_extra_entry_recovery_requires_move_aside_before_retry(
    tmp_project,
    capsys,
    command: str,
) -> None:
    _initialize_current()
    extra = Path(".llm-wiki/skills/wiki-reference/references/local-preserved-note.md")
    extra.write_text("local note\n", encoding="utf-8")

    if command == "init":
        init_cmd.run(_init_args())
    else:
        upgrade_cmd.run(_upgrade_args(agent="generic"))

    output = capsys.readouterr().out
    assert extra.read_text(encoding="utf-8") == "local note\n"
    assert "inspect and back up preserved extra" in output
    assert "move those entries aside" in output
    assert "--skill wiki-reference --force" in output


def test_init_event_order_is_inspect_provision_select_render_schema_config(
    tmp_project,
    monkeypatch,
) -> None:
    events: list[str] = []
    original_inspect = init_cmd.inspect_config
    original_provision = init_cmd.provision_reference_skill
    original_select = init_cmd.select_render_profile
    original_build = init_cmd._build_schema_content
    original_schema_write = init_cmd.atomic_write_guarded_bytes
    original_write_config = init_cmd.write_config

    def inspect(wiki_dir):
        events.append("inspect")
        return original_inspect(wiki_dir)

    def provision(*args, **kwargs):
        events.append("provision")
        return original_provision(*args, **kwargs)

    def select(*args, **kwargs):
        events.append("select")
        return original_select(*args, **kwargs)

    def render(*args, **kwargs):
        events.append("render")
        return original_build(*args, **kwargs)

    def write_markdown(path, content, **kwargs):
        if Path(path).name == "AGENTS.md":
            events.append("schema")
        return original_schema_write(path, content, **kwargs)

    def persist(wiki_dir, data, **kwargs):
        events.append("config")
        return original_write_config(wiki_dir, data, **kwargs)

    monkeypatch.setattr(init_cmd, "inspect_config", inspect)
    monkeypatch.setattr(init_cmd, "provision_reference_skill", provision)
    monkeypatch.setattr(init_cmd, "select_render_profile", select)
    monkeypatch.setattr(init_cmd, "_build_schema_content", render)
    monkeypatch.setattr(init_cmd, "atomic_write_guarded_bytes", write_markdown)
    monkeypatch.setattr(init_cmd, "write_config", persist)

    init_cmd.run(_init_args())

    assert events == ["inspect", "provision", "select", "render", "schema", "config"]


def test_init_replaces_legacy_block_without_touching_user_or_plugin_text(
    tmp_project,
) -> None:
    plugin = build_skill_block("third-party", "review", "# Review\n\nKeep me.")
    Path("AGENTS.md").write_text(
        "# User preface\n\n"
        f"{CONSTRAINT_START}\nold inline instructions\n{CONSTRAINT_END}\n\n"
        "# User appendix\n\n" + plugin,
        encoding="utf-8",
    )

    init_cmd.run(_init_args(no_skills=True))

    content = Path("AGENTS.md").read_text(encoding="utf-8")
    assert content.startswith("# User preface\n\n")
    assert "old inline instructions" not in content
    assert "# User appendix\n" in content
    assert plugin.strip() in content
    assert content.count(CONSTRAINT_START) == 1
    assert _profile("AGENTS.md") is SchemaRenderProfile.EXPANDED_INLINE


def test_init_schema_write_failure_keeps_prior_safe_schema_and_config(
    tmp_project,
    monkeypatch,
) -> None:
    init_cmd.run(_init_args(no_skills=True))
    schema_before = Path("AGENTS.md").read_bytes()
    config_path = get_agent_config_path(WIKI_DIR)
    config_before = config_path.read_bytes()
    original_schema_write = init_cmd.atomic_write_guarded_bytes

    def fail_schema(path, content, **kwargs):
        if Path(path).name == "AGENTS.md":
            raise OSError("injected schema write failure")
        return original_schema_write(path, content, **kwargs)

    monkeypatch.setattr(init_cmd, "atomic_write_guarded_bytes", fail_schema)

    with pytest.raises(SystemExit) as exc_info:
        init_cmd.run(_init_args(no_skills=False))
    assert exc_info.value.code == 2

    assert Path("AGENTS.md").read_bytes() == schema_before
    assert config_path.read_bytes() == config_before
    assert _profile("AGENTS.md") is SchemaRenderProfile.EXPANDED_INLINE
    assert verify_reference_skill(agent="generic").current


def test_init_config_write_failure_leaves_new_expanded_schema_and_old_config(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current()
    config_path = get_agent_config_path(WIKI_DIR)
    config_before = config_path.read_bytes()

    def fail_config(*_args, **_kwargs):
        raise OSError("injected config write failure")

    monkeypatch.setattr(init_cmd, "write_config", fail_config)

    with pytest.raises(OSError, match="config write failure"):
        init_cmd.run(_init_args(no_skills=True))

    assert _profile("AGENTS.md") is SchemaRenderProfile.EXPANDED_INLINE
    assert config_path.read_bytes() == config_before
    assert read_config(WIKI_DIR)["rendered_profile"] == "compact"


def test_init_and_upgrade_preserve_compatible_config_extensions(tmp_project) -> None:
    write_config(
        WIKI_DIR,
        {
            "agent": "generic",
            "quality_hints": True,
            "reference_skill": True,
            "issue_reporting": False,
            "extension_state": {"owner": "local", "version": 3},
        },
    )

    init_cmd.run(_init_args())
    assert read_config(WIKI_DIR)["extension_state"] == {
        "owner": "local",
        "version": 3,
    }

    upgrade_cmd.run(_upgrade_args())
    assert read_config(WIKI_DIR)["extension_state"] == {
        "owner": "local",
        "version": 3,
    }


def test_custom_wiki_lifecycle_leaves_default_tree_byte_unchanged(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    custom_wiki = "managed/custom-wiki"
    default_wiki = Path(WIKI_DIR)
    default_wiki.mkdir(parents=True)
    sentinel = default_wiki / "owner-notes.bin"
    sentinel.write_bytes(b"default owner bytes: \x81\r\n")
    before = {
        path.relative_to(default_wiki).as_posix(): path.read_bytes()
        for path in default_wiki.rglob("*")
        if path.is_file()
    }

    init_cmd.run(_init_args(wiki_dir=custom_wiki))
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)
    status_cmd.run(
        SimpleNamespace(
            wiki_dir=custom_wiki,
            src_dir=".",
            allow_external_src=False,
            source_selection=None,
        )
    )
    status_output = capsys.readouterr().out
    upgrade_cmd.run(_upgrade_args(wiki_dir=custom_wiki, agent="generic"))

    after = {
        path.relative_to(default_wiki).as_posix(): path.read_bytes()
        for path in default_wiki.rglob("*")
        if path.is_file()
    }
    schema = Path("AGENTS.md").read_text(encoding="utf-8")
    assert before == after == {"owner-notes.bin": b"default owner bytes: \x81\r\n"}
    assert Path(custom_wiki, "index.md").is_file()
    assert custom_wiki in schema
    assert WIKI_DIR not in schema
    assert "Managed lifecycle: compact/current" in status_output


@pytest.mark.parametrize(
    ("source_agent", "target_agent", "source_schema", "target_schema"),
    [
        ("generic", "claude", "AGENTS.md", "CLAUDE.md"),
        ("claude", "generic", "CLAUDE.md", "AGENTS.md"),
    ],
)
def test_upgrade_relocates_current_reference_in_both_directions_target_first(
    tmp_project,
    source_agent: str,
    target_agent: str,
    source_schema: str,
    target_schema: str,
) -> None:
    _initialize_current(source_agent)
    source_reference = skills_install_dir(source_agent) / REFERENCE_SKILL_ID
    target_reference = skills_install_dir(target_agent) / REFERENCE_SKILL_ID
    assert source_reference.is_dir()
    assert not target_reference.exists()

    upgrade_cmd.run(_upgrade_args(agent=target_agent))

    assert not source_reference.exists()
    assert verify_reference_skill(agent=target_agent).current
    assert _profile(target_schema) is SchemaRenderProfile.COMPACT
    assert not Path(source_schema).exists()
    assert read_config(WIKI_DIR)["agent"] == target_agent


def test_upgrade_event_order_commits_target_and_config_before_source_cleanup(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    events: list[str] = []
    original_provision = upgrade_cmd.provision_reference_skill
    original_upgrade_schema = upgrade_cmd._upgrade_schema
    original_write_config = upgrade_cmd.write_config
    original_clean = upgrade_cmd._clean_old_schema
    original_migrate = upgrade_cmd._migrate_reference_skill

    def provision(*args, **kwargs):
        events.append("provision-target")
        return original_provision(*args, **kwargs)

    def write_target(*args, **kwargs):
        events.append("write-target-schema")
        return original_upgrade_schema(*args, **kwargs)

    def persist(*args, **kwargs):
        payload = args[1] if len(args) > 1 else kwargs["data"]
        events.append(
            "persist-target-config-pending"
            if payload.get("pending_cleanup_agent") == "generic"
            else "persist-target-config-clear"
        )
        return original_write_config(*args, **kwargs)

    def clean(*args, **kwargs):
        assert verify_reference_skill(agent="claude").current
        assert _profile("CLAUDE.md") is SchemaRenderProfile.COMPACT
        events.append("clean-source-schema")
        return original_clean(*args, **kwargs)

    def migrate(*args, **kwargs):
        assert not Path("AGENTS.md").exists()
        events.append("remove-source-reference")
        return original_migrate(*args, **kwargs)

    monkeypatch.setattr(upgrade_cmd, "provision_reference_skill", provision)
    monkeypatch.setattr(upgrade_cmd, "_upgrade_schema", write_target)
    monkeypatch.setattr(upgrade_cmd, "write_config", persist)
    monkeypatch.setattr(upgrade_cmd, "_clean_old_schema", clean)
    monkeypatch.setattr(upgrade_cmd, "_migrate_reference_skill", migrate)

    upgrade_cmd.run(_upgrade_args(agent="claude"))
    assert events == [
        "provision-target",
        "write-target-schema",
        "persist-target-config-pending",
        "clean-source-schema",
        "remove-source-reference",
        "persist-target-config-clear",
    ]


def test_upgrade_install_failure_writes_expanded_target_and_keeps_source(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    source_schema = Path("AGENTS.md")
    source_schema_before = source_schema.read_bytes()
    source_reference = Path(".llm-wiki/skills/wiki-reference")
    source_reference_file = source_reference / "reference.md"
    source_reference_before = source_reference_file.read_bytes()
    monkeypatch.setattr(
        upgrade_cmd,
        "provision_reference_skill",
        lambda **_kwargs: _provision_result(
            ReferenceSkillState.INSTALL_ERROR,
            agent="claude",
        ),
    )

    upgrade_cmd.run(_upgrade_args(agent="claude"))
    output = capsys.readouterr().out
    config = read_config(WIKI_DIR)
    assert source_schema.read_bytes() == source_schema_before
    assert source_reference_file.read_bytes() == source_reference_before
    assert _profile("CLAUDE.md") is SchemaRenderProfile.EXPANDED_INLINE
    assert not Path(".claude/skills/wiki-reference").exists()
    assert config["agent"] == "claude"
    assert config["render_reason"] == "install-error"
    assert (
        "llm-wiki skills install --dest .claude/skills --skill wiki-reference --force"
    ) in output
    assert "source cleanup remains pending and was not attempted" in output
    assert "source cleanup remains incomplete" in output
    assert "Upgrade complete." not in output

    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)
    status_cmd.run(_status_args())
    status_output = capsys.readouterr().out
    assert "interrupted-agent-switch" in status_output
    assert "managed schema remains at AGENTS.md" in status_output


def test_upgrade_refresh_exception_does_not_promote_coincidentally_current_tree(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    reference = Path(".llm-wiki/skills/wiki-reference/reference.md")
    reference_before = reference.read_bytes()

    def fail_refresh(*_args, **_kwargs):
        raise OSError("injected refresh failure")

    monkeypatch.setattr(skills, "install_reference_skill", fail_refresh)

    upgrade_cmd.run(_upgrade_args())

    config = read_config(WIKI_DIR)
    assert reference.read_bytes() == reference_before
    assert verify_reference_skill(agent="generic").current
    assert _profile("AGENTS.md") is SchemaRenderProfile.EXPANDED_INLINE
    assert config["rendered_profile"] == "expanded_inline"
    assert config["render_reason"] == "install-error"


def test_upgrade_plugin_staging_failure_preserves_both_schema_snapshots_and_source(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    source_schema = Path("AGENTS.md")
    source_schema_before = source_schema.read_bytes()
    source_reference = Path(".llm-wiki/skills/wiki-reference/reference.md")
    source_reference_before = source_reference.read_bytes()
    target_schema = Path("CLAUDE.md")
    target_schema.write_text(
        "# Target user rules\n\n"
        + build_skill_block("third-party", "review", "Keep the old plugin block."),
        encoding="utf-8",
    )
    target_schema_before = target_schema.read_bytes()
    config_path = get_agent_config_path(WIKI_DIR)
    config_before = config_path.read_bytes()

    def fail_plugin_load():
        raise OSError("injected plugin read failure")

    monkeypatch.setattr(
        upgrade_cmd,
        "installed_skill_block_contents",
        fail_plugin_load,
    )

    with pytest.raises(SystemExit) as exc_info:
        upgrade_cmd.run(_upgrade_args(agent="claude"))
    assert exc_info.value.code == 2

    assert source_schema.read_bytes() == source_schema_before
    assert source_reference.read_bytes() == source_reference_before
    assert target_schema.read_bytes() == target_schema_before
    assert config_path.read_bytes() == config_before
    assert verify_reference_skill(agent="claude").current


def test_upgrade_target_schema_write_failure_preserves_source_and_target_bytes(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    source_schema = Path("AGENTS.md")
    source_schema_before = source_schema.read_bytes()
    source_reference = Path(".llm-wiki/skills/wiki-reference/reference.md")
    source_reference_before = source_reference.read_bytes()
    target_schema = Path("CLAUDE.md")
    target_schema.write_text("# Existing target rules\n", encoding="utf-8")
    target_schema_before = target_schema.read_bytes()
    config_path = get_agent_config_path(WIKI_DIR)
    config_before = config_path.read_bytes()
    original_schema_write = upgrade_cmd.atomic_write_guarded_bytes

    def fail_target_schema(path, content, **kwargs):
        if Path(path).name == target_schema.name:
            raise OSError("injected target schema write failure")
        return original_schema_write(path, content, **kwargs)

    monkeypatch.setattr(
        upgrade_cmd,
        "atomic_write_guarded_bytes",
        fail_target_schema,
    )

    with pytest.raises(SystemExit) as exc_info:
        upgrade_cmd.run(_upgrade_args(agent="claude"))
    assert exc_info.value.code == 2

    assert source_schema.read_bytes() == source_schema_before
    assert source_reference.read_bytes() == source_reference_before
    assert target_schema.read_bytes() == target_schema_before
    assert config_path.read_bytes() == config_before
    assert verify_reference_skill(agent="claude").current


def test_upgrade_config_write_failure_keeps_source_after_target_commit(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    source_schema = Path("AGENTS.md")
    source_schema_before = source_schema.read_bytes()
    source_reference = Path(".llm-wiki/skills/wiki-reference/reference.md")
    source_reference_before = source_reference.read_bytes()
    config_path = get_agent_config_path(WIKI_DIR)
    config_before = config_path.read_bytes()

    def fail_config(*_args, **_kwargs):
        raise OSError("injected target config write failure")

    monkeypatch.setattr(upgrade_cmd, "write_config", fail_config)

    with pytest.raises(OSError, match="target config write failure"):
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert source_schema.read_bytes() == source_schema_before
    assert source_reference.read_bytes() == source_reference_before
    assert config_path.read_bytes() == config_before
    assert _profile("CLAUDE.md") is SchemaRenderProfile.COMPACT
    assert verify_reference_skill(agent="claude").current


def test_upgrade_old_schema_cleanup_failure_does_not_remove_old_reference(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    source_schema = Path("AGENTS.md")
    source_schema_before = source_schema.read_bytes()
    source_reference = Path(".llm-wiki/skills/wiki-reference/reference.md")
    source_reference_before = source_reference.read_bytes()
    migrated = False

    def fail_cleanup(*_args, **_kwargs):
        raise OSError("injected old schema cleanup failure")

    def record_migration(*_args, **_kwargs):
        nonlocal migrated
        migrated = True

    monkeypatch.setattr(upgrade_cmd, "_clean_old_schema", fail_cleanup)
    monkeypatch.setattr(upgrade_cmd, "_migrate_reference_skill", record_migration)

    with pytest.raises(OSError, match="old schema cleanup failure"):
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert source_schema.read_bytes() == source_schema_before
    assert source_reference.read_bytes() == source_reference_before
    assert migrated is False
    assert _profile("CLAUDE.md") is SchemaRenderProfile.COMPACT
    assert verify_reference_skill(agent="claude").current
    assert read_config(WIKI_DIR)["agent"] == "claude"


def test_upgrade_old_reference_removal_failure_leaves_usable_target(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    old_reference = Path(".llm-wiki/skills/wiki-reference/reference.md")
    old_reference_before = old_reference.read_bytes()
    original_remove = upgrade_cmd.remove_guarded_tree

    def fail_old_reference(path, *args, **kwargs):
        if Path(path).name == "wiki-reference":
            raise OSError("injected old reference removal failure")
        return original_remove(path, *args, **kwargs)

    monkeypatch.setattr(upgrade_cmd, "remove_guarded_tree", fail_old_reference)

    upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert not Path("AGENTS.md").exists()
    assert old_reference.read_bytes() == old_reference_before
    assert _profile("CLAUDE.md") is SchemaRenderProfile.COMPACT
    assert verify_reference_skill(agent="claude").current
    config = read_config(WIKI_DIR)
    assert config["agent"] == "claude"
    assert config["pending_cleanup_agent"] == "generic"
    assert "source cleanup remains incomplete" in capsys.readouterr().out


def test_status_uses_live_broken_reference_over_stale_compact_config(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    Path(".llm-wiki/skills/wiki-reference/references/knowledge-consumption.md").unlink()
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    recovery = next(
        line for line in output.splitlines() if line.startswith("Recovery command:")
    )
    assert "Managed lifecycle: compact/broken" in output
    assert "Reference state: incomplete" in output
    assert "Reference current: no" in output
    assert "Read-only knowledge: independent" in output
    assert "persisted-render-state-does-not-match-live-files" in output
    assert (
        "llm-wiki upgrade --wiki-dir docs/llm_wiki --agent generic --skills" in recovery
    )
    assert all(
        forbidden not in recovery.lower()
        for forbidden in ("knowledge init", "git ", "plugin", "http://", "https://")
    )


def test_status_reports_interrupted_switch_without_following_stale_source_config(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    config = read_config(WIKI_DIR)
    config["agent"] = "claude"
    write_config(WIKI_DIR, config)
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "Managed schema:  CLAUDE.md" in output
    assert "Managed lifecycle: missing-schema" in output
    assert "interrupted-agent-switch" in output
    assert "managed schema remains at AGENTS.md" in output
    assert "Read-only knowledge: independent" in output
    assert "llm-wiki upgrade --wiki-dir docs/llm_wiki --agent claude --skills" in output


def test_lifecycle_recovery_is_authority_bounded_for_compact_broken() -> None:
    schema = ManagedSchemaBlock(
        ManagedSchemaBlockState.PROFILED,
        SchemaRenderProfile.COMPACT,
        1,
        "compact",
    )
    reference = ReferenceSkillVerification(
        ReferenceSkillState.ABSENT,
        ReferenceSkillReason.ABSENT,
        Path(".llm-wiki/skills/wiki-reference"),
    )

    status = classify_lifecycle_status(
        schema=schema,
        reference=reference,
        reference_enabled=True,
        skills_dir=".llm-wiki/skills",
        configured_profile="compact",
        configured_reason="reference-current",
    )

    assert status.state is ManagedLifecycleState.COMPACT_BROKEN
    assert status.read_only_knowledge == "independent"
    assert status.recovery_command == (
        "llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} --skills"
    )
    assert status.config_mismatch is True
    assert all(
        forbidden not in status.recovery_command.lower()
        for forbidden in ("knowledge init", "git ", "plugin", "http://", "https://")
    )


def test_old_cli_outer_marker_replace_remove_and_forward_upgrade_preserve_text() -> (
    None
):
    modern = build_schema_content(
        "generic",
        WIKI_DIR,
        render_profile=SchemaRenderProfile.COMPACT,
    )
    plugin = build_skill_block("third-party", "review", "# Review\n\nKeep me.")
    document = "# User preface\n\n" + modern + "\n" + plugin + "\n# User appendix\n"
    legacy = f"{CONSTRAINT_START}\nolder CLI expanded instructions\n{CONSTRAINT_END}\n"

    downgraded = replace_schema_block_content(document, legacy)
    assert classify_managed_schema_block(downgraded).state is (
        ManagedSchemaBlockState.LEGACY_EXPANDED_INLINE
    )
    assert "# User preface" in downgraded
    assert plugin.strip() in downgraded
    assert "# User appendix" in downgraded

    upgraded = replace_schema_block_content(downgraded, modern)
    assert _profile_from_content(upgraded) is SchemaRenderProfile.COMPACT
    assert "# User preface" in upgraded
    assert plugin.strip() in upgraded
    assert "# User appendix" in upgraded

    removed = strip_wiki_block(upgraded)
    assert CONSTRAINT_START not in removed
    assert "# User preface" in removed
    assert plugin.strip() in removed
    assert "# User appendix" in removed


def _profile_from_content(content: str) -> SchemaRenderProfile:
    block = classify_managed_schema_block(content)
    assert block.state is ManagedSchemaBlockState.PROFILED
    assert block.profile is not None
    return block.profile


def test_old_cli_replacement_fails_closed_on_unbalanced_outer_marker() -> None:
    malformed = (
        "# User preface\n\n"
        f"{CONSTRAINT_START}\n"
        "unterminated older block\n"
        "# User appendix\n"
    )
    modern = build_schema_content(
        "generic",
        WIKI_DIR,
        render_profile=SchemaRenderProfile.EXPANDED_INLINE,
    )

    assert replace_schema_block_content(malformed, modern) == malformed


@pytest.mark.parametrize("duplicate_end", [False, True])
def test_init_rejects_ambiguous_existing_markers_before_provisioning(
    tmp_project,
    monkeypatch,
    duplicate_end: bool,
) -> None:
    malformed = (
        "# User text\n"
        f"{CONSTRAINT_START}\nfirst\n"
        f"{CONSTRAINT_START if not duplicate_end else CONSTRAINT_END}\n"
        f"{CONSTRAINT_END}\n"
    )
    Path("AGENTS.md").write_text(malformed, encoding="utf-8")
    monkeypatch.setattr(
        init_cmd,
        "provision_reference_skill",
        lambda **_kwargs: pytest.fail("malformed schema must fail before provision"),
    )

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args())

    assert caught.value.code == 2
    assert Path("AGENTS.md").read_text(encoding="utf-8") == malformed
    assert not Path(".llm-wiki/skills/wiki-reference").exists()
    assert not Path(WIKI_DIR).exists()


@pytest.mark.parametrize("malformed_path", ["AGENTS.md", "CLAUDE.md"])
def test_upgrade_rejects_malformed_source_or_target_before_provisioning(
    tmp_project,
    monkeypatch,
    malformed_path: str,
) -> None:
    _initialize_current("generic")
    malformed = (
        "# User text\n"
        f"{CONSTRAINT_START}\nfirst\n{CONSTRAINT_START}\nsecond\n"
        f"{CONSTRAINT_END}\n"
    )
    Path(malformed_path).write_text(malformed, encoding="utf-8")
    config_before = get_agent_config_path(WIKI_DIR).read_bytes()
    monkeypatch.setattr(
        upgrade_cmd,
        "provision_reference_skill",
        lambda **_kwargs: pytest.fail("malformed schema must fail before provision"),
    )

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    assert Path(malformed_path).read_text(encoding="utf-8") == malformed
    assert get_agent_config_path(WIKI_DIR).read_bytes() == config_before
    assert not Path(".claude/skills/wiki-reference").exists()


def test_init_rejects_symlinked_schema_parent_without_outside_write(
    tmp_project,
) -> None:
    outside = tmp_project.parent / f"{tmp_project.name}-outside-schema"
    outside.mkdir()
    Path(".github").symlink_to(outside, target_is_directory=True)

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args(agent="copilot"))

    assert caught.value.code == 2
    assert not (outside / "copilot-instructions.md").exists()
    assert not Path(WIKI_DIR).exists()


def test_upgrade_rejects_symlinked_hook_parent_without_outside_write(
    tmp_project,
) -> None:
    _initialize_current("generic")
    hooks = Path(".git/hooks")
    shutil.rmtree(hooks)
    outside = tmp_project.parent / f"{tmp_project.name}-outside-hooks"
    outside.mkdir()
    hooks.symlink_to(outside, target_is_directory=True)

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args())

    assert caught.value.code == 2
    assert not (outside / "post-commit").exists()
    assert not (outside / "pre-commit").exists()


def test_successful_switch_preserves_source_only_plugin_block(tmp_project) -> None:
    _initialize_current("generic")
    plugin = build_skill_block("removed-plugin", "review", "# Local plugin\n\nKeep.")
    source = Path("AGENTS.md")
    source.write_text(
        source.read_text(encoding="utf-8") + "\n" + plugin, encoding="utf-8"
    )

    upgrade_cmd.run(_upgrade_args(agent="claude"))
    remaining = source.read_text(encoding="utf-8")
    assert CONSTRAINT_START not in remaining
    assert plugin.strip() in remaining


def test_upgrade_retry_finishes_recorded_schema_cleanup(
    tmp_project, monkeypatch
) -> None:
    _initialize_current("generic")
    original_clean = upgrade_cmd._clean_old_schema
    with monkeypatch.context() as scoped:
        scoped.setattr(
            upgrade_cmd,
            "_clean_old_schema",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                OSError("injected cleanup failure")
            ),
        )
        with pytest.raises(OSError, match="cleanup failure"):
            upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert read_config(WIKI_DIR)["pending_cleanup_agent"] == "generic"
    assert Path("AGENTS.md").exists()
    assert original_clean is upgrade_cmd._clean_old_schema

    upgrade_cmd.run(_upgrade_args(agent="claude"))
    assert "pending_cleanup_agent" not in read_config(WIKI_DIR)
    assert not Path("AGENTS.md").exists()
    assert not Path(".llm-wiki/skills/wiki-reference").exists()


def test_upgrade_retry_finishes_recorded_reference_cleanup(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    original_remove = upgrade_cmd.remove_guarded_tree
    with monkeypatch.context() as scoped:
        scoped.setattr(
            upgrade_cmd,
            "remove_guarded_tree",
            lambda path, *args, **kwargs: (
                (_ for _ in ()).throw(OSError("injected reference cleanup failure"))
                if Path(path).name == "wiki-reference"
                else original_remove(path, *args, **kwargs)
            ),
        )
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert read_config(WIKI_DIR)["pending_cleanup_agent"] == "generic"
    assert not Path("AGENTS.md").exists()
    assert Path(".llm-wiki/skills/wiki-reference").exists()

    upgrade_cmd.run(_upgrade_args(agent="claude"))
    assert "pending_cleanup_agent" not in read_config(WIKI_DIR)
    assert not Path(".llm-wiki/skills/wiki-reference").exists()


def test_status_infers_unique_live_agent_when_config_write_never_landed(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("claude")
    get_agent_config_path(WIKI_DIR).unlink()
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "Managed schema:  CLAUDE.md" in output
    assert "live-agent-inferred-from-managed-schema:claude" in output
    assert "--agent claude --skills" in output
    assert "--agent generic --skills" not in output


def test_status_requires_agent_choice_for_multiple_configless_schemas(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    get_agent_config_path(WIKI_DIR).parent.mkdir(parents=True, exist_ok=True)
    _write = build_schema_content
    Path("AGENTS.md").write_text(
        _write("generic", WIKI_DIR, render_profile=SchemaRenderProfile.COMPACT),
        encoding="utf-8",
    )
    Path("CLAUDE.md").write_text(
        _write("claude", WIKI_DIR, render_profile=SchemaRenderProfile.COMPACT),
        encoding="utf-8",
    )
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "agent-config-does-not-identify-one-live-managed-schema" in output
    assert "--agent generic --skills --cleanup-source-agent claude" in output
    assert "--agent claude --skills --cleanup-source-agent generic" in output


def test_partial_reference_removal_keeps_pending_until_manual_recovery(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    original_remove = upgrade_cmd.remove_guarded_tree
    with monkeypatch.context() as scoped:

        def partial_remove(path, *args, **kwargs):
            target = Path(path)
            if target.name == "wiki-reference":
                (target / "SKILL.md").unlink()
                raise OSError("injected partial reference removal")
            return original_remove(path, *args, **kwargs)

        scoped.setattr(upgrade_cmd, "remove_guarded_tree", partial_remove)
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    upgrade_cmd.run(_upgrade_args(agent="claude"))
    output = capsys.readouterr().out
    config = read_config(WIKI_DIR)
    assert config["pending_cleanup_agent"] == "generic"
    assert config["pending_cleanup_reference"] is True
    assert Path(".llm-wiki/skills/wiki-reference").exists()
    assert "source cleanup remains incomplete" in output

    upgrade_cmd.shutil.rmtree(Path(".llm-wiki/skills/wiki-reference"))
    upgrade_cmd.run(_upgrade_args(agent="claude"))
    assert "pending_cleanup_agent" not in read_config(WIKI_DIR)


def test_invalid_config_pending_evidence_requires_explicit_cleanup_authority(
    tmp_project,
) -> None:
    _initialize_current("generic")
    config = read_config(WIKI_DIR)
    config.update(
        {
            "agent": "claude",
            "quality_hints": "invalid",
            "pending_cleanup_agent": "generic",
            "pending_cleanup_reference": True,
        }
    )
    write_config(WIKI_DIR, config)
    source_before = Path("AGENTS.md").read_bytes()

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    assert Path("AGENTS.md").read_bytes() == source_before
    assert verify_reference_skill(agent="generic").current

    upgrade_cmd.run(_upgrade_args(agent="claude", cleanup_source_agent="generic"))
    assert not Path("AGENTS.md").exists()
    assert not Path(".llm-wiki/skills/wiki-reference").exists()


def test_init_refuses_to_discard_pending_cleanup_evidence_from_invalid_config(
    tmp_project,
) -> None:
    _initialize_current("generic")
    config = read_config(WIKI_DIR)
    config.update(
        {
            "agent": "claude",
            "quality_hints": "invalid",
            "pending_cleanup_agent": "generic",
            "pending_cleanup_reference": True,
        }
    )
    write_config(WIKI_DIR, config)
    before = get_agent_config_path(WIKI_DIR).read_bytes()

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args(agent="claude"))

    assert caught.value.code == 2
    assert get_agent_config_path(WIKI_DIR).read_bytes() == before


def test_explicit_cleanup_choice_converges_aborted_target_or_resumed_switch(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    config_before = get_agent_config_path(WIKI_DIR).read_bytes()
    with monkeypatch.context() as scoped:
        scoped.setattr(
            upgrade_cmd,
            "write_config",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                OSError("injected config failure")
            ),
        )
        with pytest.raises(OSError, match="config failure"):
            upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert get_agent_config_path(WIKI_DIR).read_bytes() == config_before
    assert Path("AGENTS.md").exists() and Path("CLAUDE.md").exists()
    upgrade_cmd.run(_upgrade_args(agent="generic", cleanup_source_agent="claude"))
    assert Path("AGENTS.md").exists()
    assert not Path("CLAUDE.md").exists()
    assert not Path(".claude/skills/wiki-reference").exists()

    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)
    status_cmd.run(_status_args())
    terminal = capsys.readouterr().out
    assert "interrupted-agent-switch" not in terminal


def test_install_error_remains_visible_as_last_render_reason(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        init_cmd,
        "provision_reference_skill",
        lambda **_kwargs: _provision_result(
            ReferenceSkillState.INSTALL_ERROR,
            agent="generic",
        ),
    )
    init_cmd.run(_init_args())
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "Last render reason: install-error" in output
    assert "persisted-render-state-does-not-match-live-files" not in output


def test_final_cleanup_marker_write_failure_is_truthful_and_retryable(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    original_write = upgrade_cmd.write_config
    writes = 0
    with monkeypatch.context() as scoped:

        def fail_clear(wiki_dir, data, **kwargs):
            nonlocal writes
            writes += 1
            if writes == 2:
                raise OSError("injected pending marker clear failure")
            return original_write(wiki_dir, data, **kwargs)

        scoped.setattr(upgrade_cmd, "write_config", fail_clear)
        with pytest.raises(OSError, match="marker clear failure"):
            upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert read_config(WIKI_DIR)["pending_cleanup_agent"] == "generic"
    assert not Path("AGENTS.md").exists()
    assert not Path(".llm-wiki/skills/wiki-reference").exists()
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)
    status_cmd.run(_status_args())
    output = capsys.readouterr().out
    assert "pending-source-cleanup:generic" in output
    assert "pending cleanup marker remains for generic" in output
    assert "managed schema remains at CLAUDE.md" not in output

    upgrade_cmd.run(_upgrade_args(agent="claude"))
    assert "pending_cleanup_agent" not in read_config(WIKI_DIR)


def test_switch_rejects_empty_symlinked_source_parent_before_target_mutation(
    tmp_project,
) -> None:
    _initialize_current("copilot")
    config_before = get_agent_config_path(WIKI_DIR).read_bytes()
    shutil.rmtree(Path(".github"))
    outside = tmp_project.parent / f"{tmp_project.name}-empty-source-parent"
    outside.mkdir()
    Path(".github").symlink_to(outside, target_is_directory=True)

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="generic"))

    assert caught.value.code == 2
    assert not Path("AGENTS.md").exists()
    assert get_agent_config_path(WIKI_DIR).read_bytes() == config_before
    assert not list(outside.iterdir())


def test_status_reports_unsafe_schema_component_without_touching_leaf(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    write_config(
        WIKI_DIR,
        {
            "agent": "copilot",
            "quality_hints": True,
            "reference_skill": True,
            "issue_reporting": False,
        },
    )
    outside = tmp_project.parent / f"{tmp_project.name}-unsafe-status-schema"
    outside.mkdir()
    Path(".github").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "unsafe-managed-schema-path:" in output
    assert "path component .github" in output
    assert "repair or move aside malformed managed markers" not in output
    assert not list(outside.iterdir())


def test_status_preflights_absent_recorded_source_under_unsafe_parent(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    config = read_config(WIKI_DIR)
    config.update(
        {
            "pending_cleanup_agent": "copilot",
            "pending_cleanup_reference": False,
        }
    )
    write_config(WIKI_DIR, config)
    outside = tmp_project.parent / f"{tmp_project.name}-pending-copilot-parent"
    outside.mkdir()
    Path(".github").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "unsafe-managed-schema-path:" in output
    assert "move aside unsafe managed-schema path component .github" in output
    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="generic"))
    assert caught.value.code == 2
    Path(".github").unlink()
    upgrade_cmd.run(_upgrade_args(agent="generic"))
    assert "pending_cleanup_agent" not in read_config(WIKI_DIR)
    assert not list(outside.iterdir())


def test_status_unsafe_config_requires_quarantined_pending_evidence_review(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    config_path = get_agent_config_path(WIKI_DIR)
    outside = tmp_project.parent / f"{tmp_project.name}-unsafe-status-config.json"
    outside.write_text('{"pending_cleanup_agent":"generic"}', encoding="utf-8")
    config_path.symlink_to(outside)
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "unsafe local-config path component .git/.llm-wiki-agent" in output
    assert "quarantined config bytes for pending cleanup evidence" in output
    assert "llm-wiki status --wiki-dir docs/llm_wiki" in output
    assert "before any init or upgrade" in output
    assert outside.read_text(encoding="utf-8") == '{"pending_cleanup_agent":"generic"}'


@pytest.mark.parametrize("command", ["init", "upgrade"])
@pytest.mark.parametrize(
    "unsafe_relative",
    ["modules", "modules/.gitkeep", "index.md", "log.md"],
)
def test_lifecycle_preflights_every_scaffold_path_before_mutation(
    tmp_project,
    command: str,
    unsafe_relative: str,
) -> None:
    wiki = Path(WIKI_DIR)
    wiki.mkdir(parents=True)
    unsafe_path = wiki / unsafe_relative
    unsafe_path.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_project.parent / (
        f"{tmp_project.name}-{command}-{unsafe_relative.replace('/', '-')}-outside"
    )
    if unsafe_relative == "modules":
        outside.mkdir()
        unsafe_path.symlink_to(outside, target_is_directory=True)
    else:
        outside.write_text("sentinel", encoding="utf-8")
        unsafe_path.symlink_to(outside)

    runner = init_cmd.run if command == "init" else upgrade_cmd.run
    args = (
        _init_args(agent="generic")
        if command == "init"
        else _upgrade_args(agent="generic")
    )
    with pytest.raises(SystemExit) as caught:
        runner(args)

    assert caught.value.code == 2
    assert not Path("AGENTS.md").exists()
    assert not Path(".llm-wiki/skills/wiki-reference").exists()
    assert not get_agent_config_path(WIKI_DIR).exists()
    if outside.is_file():
        assert outside.read_text(encoding="utf-8") == "sentinel"
    else:
        assert not list(outside.iterdir())


@pytest.mark.parametrize("command", ["init", "upgrade"])
def test_nonregular_config_is_rejected_before_lifecycle_mutation(
    tmp_project,
    command: str,
) -> None:
    config_path = get_agent_config_path(WIKI_DIR)
    config_path.mkdir()
    runner = init_cmd.run if command == "init" else upgrade_cmd.run
    args = (
        _init_args(agent="generic")
        if command == "init"
        else _upgrade_args(agent="generic")
    )

    with pytest.raises(SystemExit) as caught:
        runner(args)

    assert caught.value.code == 2
    assert config_path.is_dir()
    assert not Path("AGENTS.md").exists()
    assert not Path(WIKI_DIR).exists()
    assert not Path(".llm-wiki/skills/wiki-reference").exists()


def test_status_requires_nonregular_config_move_aside_before_recovery(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    get_agent_config_path(WIKI_DIR).mkdir()
    Path("AGENTS.md").write_text(
        build_schema_content(
            "generic",
            WIKI_DIR,
            render_profile=SchemaRenderProfile.EXPANDED_INLINE,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "config-path-not-regular" in output
    assert (
        "move aside or repair invalid, non-regular, or unreadable local-config path"
        in output
    )
    assert "Reference repair: run `llm-wiki upgrade`" not in output
    assert "agent config is missing" not in output
    assert "agent config is invalid or unusable" in output


@pytest.mark.parametrize("command", ["init", "upgrade"])
def test_nonregular_target_schema_is_rejected_before_mutation(
    tmp_project,
    command: str,
) -> None:
    Path("AGENTS.md").mkdir()
    runner = init_cmd.run if command == "init" else upgrade_cmd.run
    args = (
        _init_args(agent="generic")
        if command == "init"
        else _upgrade_args(agent="generic")
    )

    with pytest.raises(SystemExit) as caught:
        runner(args)

    assert caught.value.code == 2
    assert Path("AGENTS.md").is_dir()
    assert not Path(WIKI_DIR).exists()
    assert not Path(".llm-wiki/skills/wiki-reference").exists()


def test_fifo_schema_is_rejected_by_stat_without_opening(tmp_project) -> None:
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFOs are unavailable on this platform")
    os.mkfifo("AGENTS.md")

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args(agent="generic"))

    assert caught.value.code == 2
    assert not Path(WIKI_DIR).exists()
    assert not Path(".llm-wiki/skills/wiki-reference").exists()


@pytest.mark.parametrize("replacement", ["directory", "fifo"])
def test_init_revalidates_schema_after_reference_provision(
    tmp_project,
    monkeypatch,
    replacement: str,
) -> None:
    if replacement == "fifo" and not hasattr(os, "mkfifo"):
        pytest.skip("FIFOs are unavailable on this platform")
    original_provision = init_cmd.provision_reference_skill

    def provision_then_replace(**kwargs):
        result = original_provision(**kwargs)
        if replacement == "directory":
            Path("AGENTS.md").mkdir()
        else:
            os.mkfifo("AGENTS.md")
        return result

    monkeypatch.setattr(init_cmd, "provision_reference_skill", provision_then_replace)

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args(agent="generic"))

    assert caught.value.code == 2
    assert verify_reference_skill(agent="generic").current
    assert Path(WIKI_DIR).is_dir()
    assert not get_agent_config_path(WIKI_DIR).exists()
    if replacement == "directory":
        assert Path("AGENTS.md").is_dir()
    else:
        assert Path("AGENTS.md").exists()
        assert not Path("AGENTS.md").is_file()


def test_nonregular_source_schema_is_rejected_before_switch_mutation(
    tmp_project,
) -> None:
    _initialize_current("generic")
    config_before = get_agent_config_path(WIKI_DIR).read_bytes()
    shutil.rmtree(Path("AGENTS.md")) if Path("AGENTS.md").is_dir() else Path(
        "AGENTS.md"
    ).unlink()
    Path("AGENTS.md").mkdir()

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    assert not Path("CLAUDE.md").exists()
    assert not Path(".claude/skills/wiki-reference").exists()
    assert get_agent_config_path(WIKI_DIR).read_bytes() == config_before


def test_nonregular_hook_is_rejected_before_upgrade_mutation(tmp_project) -> None:
    _initialize_current("generic")
    hook = Path(".git/hooks/post-commit")
    if hook.exists():
        hook.unlink()
    hook.mkdir(parents=True)
    schema_before = Path("AGENTS.md").read_bytes()
    config_before = get_agent_config_path(WIKI_DIR).read_bytes()
    reference_before = Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args())

    assert caught.value.code == 2
    assert Path("AGENTS.md").read_bytes() == schema_before
    assert get_agent_config_path(WIKI_DIR).read_bytes() == config_before
    assert (
        Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()
        == reference_before
    )


@pytest.mark.parametrize("hook_shape", ["directory", "invalid-utf8", "unreadable"])
def test_status_reports_unverifiable_hook_without_crashing(
    tmp_project,
    monkeypatch,
    capsys,
    hook_shape: str,
) -> None:
    _initialize_current("generic")
    hook = Path(".git/hooks/post-commit")
    if hook.exists():
        hook.unlink()
    if hook_shape == "directory":
        hook.mkdir(parents=True)
    else:
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_bytes(b"\xff" if hook_shape == "invalid-utf8" else b"hook")
    if hook_shape == "unreadable":
        original_read_text = Path.read_text

        def fail_hook_read(path, *args, **kwargs):
            if path == hook:
                raise PermissionError("injected unreadable hook")
            return original_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", fail_hook_read)
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert (
        "Hooks:           unavailable (non-regular, unreadable, or "
        "non-executable: post-commit)" in output
    )


@pytest.mark.parametrize("breaker_shape", ["symlink", "directory", "unreadable"])
def test_status_rejects_unsafe_or_unverifiable_breaker_state(
    tmp_project,
    monkeypatch,
    capsys,
    breaker_shape: str,
) -> None:
    _initialize_current("generic")
    breaker = Path(".git/llm-wiki-breaker.json")
    if breaker.exists() or breaker.is_symlink():
        breaker.unlink()
    if breaker_shape == "symlink":
        outside = tmp_project.parent / f"{tmp_project.name}-outside-breaker.json"
        outside.write_text('{"state":"open"}', encoding="utf-8")
        breaker.symlink_to(outside)
    elif breaker_shape == "directory":
        breaker.mkdir()
    else:
        breaker.write_text("{}", encoding="utf-8")
        original_read_bytes = Path.read_bytes

        def fail_breaker_read(path):
            if path == breaker:
                raise PermissionError("injected unreadable breaker")
            return original_read_bytes(path)

        monkeypatch.setattr(Path, "read_bytes", fail_breaker_read)
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "Circuit breaker: unavailable" in output


@pytest.mark.parametrize(
    ("source", "target", "reference_file"),
    [
        ("generic", "claude", ".llm-wiki/skills/wiki-reference/reference.md"),
        ("claude", "generic", ".claude/skills/wiki-reference/reference.md"),
    ],
)
def test_opt_out_switch_reports_and_preserves_modified_source_reference(
    tmp_project,
    capsys,
    source: str,
    target: str,
    reference_file: str,
) -> None:
    _initialize_current(source)
    init_cmd.run(_init_args(agent=source, no_skills=True))
    reference = Path(reference_file)
    reference.write_text(
        reference.read_text(encoding="utf-8") + "\nlocal note\n",
        encoding="utf-8",
    )
    before = reference.read_bytes()

    upgrade_cmd.run(_upgrade_args(agent=target))

    output = capsys.readouterr().out
    assert reference.read_bytes() == before
    assert f"Kept wiki-reference skill in {reference.parent.parent}/" in output
    assert "locally_modified" in output


def test_invalid_pending_equal_to_inferred_agent_never_emits_same_agent_cleanup(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    config = read_config(WIKI_DIR)
    config.update(
        {
            "agent": "claude",
            "quality_hints": "invalid",
            "pending_cleanup_agent": "generic",
            "pending_cleanup_reference": True,
        }
    )
    write_config(WIKI_DIR, config)
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "--agent generic --skills --cleanup-source-agent generic" not in output
    assert "remove the untrusted pending cleanup pair" in output
    assert "--agent generic --skills`" in output
    assert "--agent claude --skills --cleanup-source-agent generic" in output

    upgrade_cmd.run(_upgrade_args(agent="claude", cleanup_source_agent="generic"))
    status_cmd.run(_status_args())
    terminal = capsys.readouterr().out
    assert "interrupted-agent-switch" not in terminal


def test_three_live_schemas_require_manual_choice_without_arbitrary_cleanup(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    get_agent_config_path(WIKI_DIR).parent.mkdir(parents=True, exist_ok=True)
    for agent, path in (
        ("generic", Path("AGENTS.md")),
        ("claude", Path("CLAUDE.md")),
        ("copilot", Path(".github/copilot-instructions.md")),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            build_schema_content(
                agent,
                WIKI_DIR,
                render_profile=SchemaRenderProfile.COMPACT,
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "select one intended agent explicitly" in output
    assert "back up candidate managed-reference trees" in output
    assert "rerun status before upgrade" in output
    assert "--cleanup-source-agent" not in output


def test_untrusted_third_agent_pending_is_resolved_before_schema_ambiguity(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    modified_reference = Path(".llm-wiki/skills/wiki-reference/SKILL.md")
    modified_reference.write_text(
        modified_reference.read_text(encoding="utf-8") + "\nlocal note\n",
        encoding="utf-8",
    )
    Path("AGENTS.md").unlink()
    for agent, path in (
        ("claude", Path("CLAUDE.md")),
        ("copilot", Path(".github/copilot-instructions.md")),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            build_schema_content(
                agent,
                WIKI_DIR,
                render_profile=SchemaRenderProfile.COMPACT,
            ),
            encoding="utf-8",
        )
    config = read_config(WIKI_DIR)
    config.update(
        {
            "agent": "claude",
            "quality_hints": "invalid",
            "pending_cleanup_agent": "generic",
            "pending_cleanup_reference": True,
        }
    )
    write_config(WIKI_DIR, config)
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "untrusted pending cleanup evidence for generic" in output
    assert "--agent claude --skills --cleanup-source-agent generic" in output
    assert "--agent copilot --skills --cleanup-source-agent generic" in output
    assert "--cleanup-source-agent copilot" not in output
    assert "--cleanup-source-agent claude" not in output

    upgrade_cmd.run(_upgrade_args(agent="claude", cleanup_source_agent="generic"))
    assert modified_reference.exists()
    upgrade_cmd.run(_upgrade_args(agent="claude", cleanup_source_agent="copilot"))
    status_cmd.run(_status_args())
    terminal = capsys.readouterr().out
    assert "interrupted-agent-switch" not in terminal
    assert modified_reference.exists()


def test_invalid_agent_does_not_erase_reference_only_pending_cleanup(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    original_remove = upgrade_cmd.remove_guarded_tree
    with monkeypatch.context() as scoped:
        scoped.setattr(
            upgrade_cmd,
            "remove_guarded_tree",
            lambda path, *args, **kwargs: (
                (_ for _ in ()).throw(OSError("injected source reference failure"))
                if Path(path).name == "wiki-reference"
                else original_remove(path, *args, **kwargs)
            ),
        )
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    config = read_config(WIKI_DIR)
    config["agent"] = "future-agent"
    write_config(WIKI_DIR, config)
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "untrusted-pending-source-cleanup-evidence:generic" in output
    assert "--agent claude --skills --cleanup-source-agent generic" in output
    assert Path(".llm-wiki/skills/wiki-reference").exists()

    upgrade_cmd.run(_upgrade_args(agent="claude", cleanup_source_agent="generic"))
    assert not Path(".llm-wiki/skills/wiki-reference").exists()
    assert "pending_cleanup_agent" not in read_config(WIKI_DIR)


@pytest.mark.parametrize("with_schema", [False, True])
def test_invalid_agent_same_pending_requires_manual_pair_repair(
    tmp_project,
    monkeypatch,
    capsys,
    with_schema: bool,
) -> None:
    get_agent_config_path(WIKI_DIR).parent.mkdir(parents=True, exist_ok=True)
    if with_schema:
        Path("AGENTS.md").write_text(
            build_schema_content(
                "generic",
                WIKI_DIR,
                render_profile=SchemaRenderProfile.EXPANDED_INLINE,
            ),
            encoding="utf-8",
        )
    write_config(
        WIKI_DIR,
        {
            "agent": "future-agent",
            "quality_hints": True,
            "reference_skill": False,
            "issue_reporting": False,
            "pending_cleanup_agent": "generic",
            "pending_cleanup_reference": False,
        },
    )
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "remove the untrusted pending cleanup pair" in output
    assert "--cleanup-source-agent generic" not in output
    config = read_config(WIKI_DIR)
    config.update({"agent": "generic", "quality_hints": True})
    config.pop("pending_cleanup_agent", None)
    config.pop("pending_cleanup_reference", None)
    write_config(WIKI_DIR, config)
    if with_schema:
        upgrade_cmd.run(_upgrade_args(agent="generic"))
    else:
        init_cmd.run(_init_args(agent="generic", no_skills=True))

    status_cmd.run(_status_args())
    terminal = capsys.readouterr().out
    assert "interrupted-agent-switch" not in terminal


def test_opaque_invalid_config_quarantines_reference_only_transaction(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    original_remove = upgrade_cmd.remove_guarded_tree
    with monkeypatch.context() as scoped:
        scoped.setattr(
            upgrade_cmd,
            "remove_guarded_tree",
            lambda path, *args, **kwargs: (
                (_ for _ in ()).throw(OSError("injected source reference failure"))
                if Path(path).name == "wiki-reference"
                else original_remove(path, *args, **kwargs)
            ),
        )
        upgrade_cmd.run(_upgrade_args(agent="claude"))
    config_path = get_agent_config_path(WIKI_DIR)
    config_path.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "invalid, non-regular, or unreadable local-config path" in output
    assert "inspect alternate managed-reference homes" in output
    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))
    assert caught.value.code == 2
    assert Path(".llm-wiki/skills/wiki-reference").exists()

    write_config(
        WIKI_DIR,
        {
            "agent": "claude",
            "quality_hints": True,
            "reference_skill": True,
            "issue_reporting": False,
            "rendered_profile": "compact",
            "render_profile_version": 1,
            "render_reason": "reference-current",
            "pending_cleanup_agent": "generic",
            "pending_cleanup_reference": True,
        },
    )
    upgrade_cmd.run(_upgrade_args(agent="claude"))
    assert not Path(".llm-wiki/skills/wiki-reference").exists()
    assert "pending_cleanup_agent" not in read_config(WIKI_DIR)


@pytest.mark.parametrize("agent", ["generic", "claude"])
def test_upgrade_custom_post_commit_collision_fails_before_mutation(
    tmp_project,
    capsys,
    agent: str,
) -> None:
    _initialize_current("generic")
    before_schema = Path("AGENTS.md").read_bytes()
    before_config = get_agent_config_path(WIKI_DIR).read_bytes()
    custom_hook = Path(".git/hooks/post-commit")
    custom_hook.parent.mkdir(parents=True, exist_ok=True)
    custom_hook.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")
    target_schema = Path("AGENTS.md" if agent == "generic" else "CLAUDE.md")
    target_reference = skills_install_dir(agent) / REFERENCE_SKILL_ID
    if agent == "claude":
        assert not target_schema.exists()
        assert not target_reference.exists()

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent=agent, force=False))

    assert caught.value.code == 1
    assert "Use --force to replace it intentionally" in capsys.readouterr().err
    assert Path("AGENTS.md").read_bytes() == before_schema
    assert get_agent_config_path(WIKI_DIR).read_bytes() == before_config
    assert custom_hook.read_text(encoding="utf-8") == "#!/bin/sh\necho custom\n"
    if agent == "claude":
        assert not target_schema.exists()
        assert not target_reference.exists()


def test_upgrade_preserves_edited_managed_hook_before_switch_mutation(
    tmp_project,
    capsys,
) -> None:
    from llm_wiki_cli.commands import hook_cmd

    _initialize_current("generic")
    before_schema = Path("AGENTS.md").read_bytes()
    before_config = get_agent_config_path(WIKI_DIR).read_bytes()
    hook = Path(".git/hooks/post-commit")
    edited = hook_cmd._build_ide_post_commit(WIKI_DIR) + "echo user-tail\n"
    hook.write_text(edited, encoding="utf-8")

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude", force=False))

    assert caught.value.code == 1
    assert "Use --force to replace it intentionally" in capsys.readouterr().err
    assert hook.read_text(encoding="utf-8") == edited
    assert Path("AGENTS.md").read_bytes() == before_schema
    assert get_agent_config_path(WIKI_DIR).read_bytes() == before_config
    assert not Path("CLAUDE.md").exists()
    assert not (skills_install_dir("claude") / REFERENCE_SKILL_ID).exists()


def test_invalid_future_agent_without_live_evidence_is_not_guessed(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    write_config(
        WIKI_DIR,
        {
            "agent": "future-agent",
            "quality_hints": True,
            "reference_skill": False,
            "issue_reporting": False,
        },
    )
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "Diagnostic fallback agent: generic" in output
    assert "explicitly select one supported agent" in output
    assert "before init or upgrade" in output
    assert "llm-wiki init --wiki-dir" not in output
    assert "llm-wiki upgrade --wiki-dir" not in output


def test_init_migrates_valid_non_git_config_after_git_appears(
    tmp_project,
) -> None:
    git_dir = Path(".git")
    held_git = Path(".git-held")
    git_dir.rename(held_git)
    try:
        init_cmd.run(_init_args(agent="claude", no_skills=True))
        fallback = Path(WIKI_DIR) / ".llm-wiki-agent"
        assert fallback.exists()
        assert read_config(WIKI_DIR)["agent"] == "claude"
    finally:
        held_git.rename(git_dir)

    init_cmd.run(_init_args(agent=None))

    config = read_config(WIKI_DIR)
    assert config["agent"] == "claude"
    assert config["reference_skill"] is False
    assert Path("CLAUDE.md").exists()
    assert not Path("AGENTS.md").exists()
    assert not (Path(WIKI_DIR) / ".llm-wiki-agent").exists()
    assert get_agent_config_path(WIKI_DIR) == Path(".git/.llm-wiki-agent")


def test_upgrade_adopts_pending_fallback_config_after_git_appears(
    tmp_project,
) -> None:
    git_dir = Path(".git")
    held_git = Path(".git-held")
    git_dir.rename(held_git)
    try:
        init_cmd.run(_init_args(agent="generic", no_skills=True))
        upgrade_cmd.run(_upgrade_args(agent="claude", skills=False))
        fallback = Path(WIKI_DIR) / ".llm-wiki-agent"
        config = read_config(WIKI_DIR)
        config["pending_cleanup_agent"] = "generic"
        config["pending_cleanup_reference"] = False
        write_config(WIKI_DIR, config)
        assert fallback.exists()
    finally:
        held_git.rename(git_dir)

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args(agent=None))
    assert caught.value.code == 2

    upgrade_cmd.run(_upgrade_args(agent=None))

    config = read_config(WIKI_DIR)
    assert config["agent"] == "claude"
    assert "pending_cleanup_agent" not in config
    assert Path("CLAUDE.md").exists()
    assert not Path("AGENTS.md").exists()
    assert not (Path(WIKI_DIR) / ".llm-wiki-agent").exists()


def test_status_honors_fallback_opt_out_after_git_appears(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    git_dir = Path(".git")
    held_git = Path(".git-held")
    git_dir.rename(held_git)
    try:
        init_cmd.run(_init_args(agent="claude", no_skills=True))
    finally:
        held_git.rename(git_dir)
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "Agent:           claude" in output
    assert "Managed lifecycle: expanded/skills-disabled" in output
    assert "none required; optional re-enable:" in output
    assert "--agent claude --skills" in output


def test_opt_out_reenable_recovery_requires_moving_preserved_extra_entry(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    init_cmd.run(_init_args(agent="generic", no_skills=True))
    extra = Path(".llm-wiki/skills/wiki-reference/references/local-extra.md")
    extra.write_text("preserved\n", encoding="utf-8")
    monkeypatch.setattr(status_cmd, "_print_knowledge_status", lambda *_a, **_k: None)

    status_cmd.run(_status_args())

    output = capsys.readouterr().out
    assert "none required while disabled; optional re-enable:" in output
    assert "move them aside or remove them if intended" in output
    assert "--agent generic --skills" in output


def test_init_never_retires_fallback_changed_after_its_parsed_snapshot(
    tmp_project,
    monkeypatch,
) -> None:
    fallback = Path(WIKI_DIR) / ".llm-wiki-agent"
    fallback.parent.mkdir(parents=True)
    original = {
        "agent": "claude",
        "quality_hints": True,
        "reference_skill": False,
        "issue_reporting": False,
    }
    fallback.write_text(json.dumps(original), encoding="utf-8")
    real_inspect = init_cmd.inspect_config

    def inspect_then_change(wiki_dir: str):
        inspection = real_inspect(wiki_dir)
        changed = dict(original)
        changed.update({"agent": "generic", "extension_state": {"owner": "concurrent"}})
        fallback.write_text(json.dumps(changed), encoding="utf-8")
        return inspection

    monkeypatch.setattr(init_cmd, "inspect_config", inspect_then_change)

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args(agent=None))

    assert caught.value.code == 2
    assert fallback.exists()
    assert "extension_state" in fallback.read_text(encoding="utf-8")
    assert not get_agent_config_path(WIKI_DIR).exists()
    assert not Path("CLAUDE.md").exists()


def test_init_infers_unique_live_schema_before_generic_default(
    tmp_project,
) -> None:
    Path("CLAUDE.md").write_text(
        build_schema_content(
            "claude",
            WIKI_DIR,
            render_profile=SchemaRenderProfile.EXPANDED_INLINE,
        ),
        encoding="utf-8",
    )

    init_cmd.run(_init_args(agent=None, no_skills=True))

    assert read_config(WIKI_DIR)["agent"] == "claude"
    assert Path("CLAUDE.md").exists()
    assert not Path("AGENTS.md").exists()


def test_init_without_agent_rejects_multiple_live_managed_schemas(
    tmp_project,
) -> None:
    for agent, path in (
        ("generic", Path("AGENTS.md")),
        ("claude", Path("CLAUDE.md")),
    ):
        path.write_text(
            build_schema_content(
                agent,
                WIKI_DIR,
                render_profile=SchemaRenderProfile.EXPANDED_INLINE,
            ),
            encoding="utf-8",
        )
    before = {
        path: path.read_bytes() for path in (Path("AGENTS.md"), Path("CLAUDE.md"))
    }

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args(agent=None, no_skills=True))

    assert caught.value.code == 2
    assert not get_agent_config_path(WIKI_DIR).exists()
    assert {path: path.read_bytes() for path in before} == before


def test_init_revalidates_scaffold_after_config_inspection(
    tmp_project,
    monkeypatch,
) -> None:
    outside = tmp_project.parent / f"{tmp_project.name}-late-init-scaffold"
    outside.mkdir()
    real_inspect = init_cmd.inspect_config

    def inspect_then_redirect(wiki_dir: str):
        inspection = real_inspect(wiki_dir)
        modules = Path(WIKI_DIR) / "modules"
        modules.parent.mkdir(parents=True, exist_ok=True)
        modules.symlink_to(outside, target_is_directory=True)
        return inspection

    monkeypatch.setattr(init_cmd, "inspect_config", inspect_then_redirect)

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args(no_skills=True))

    assert caught.value.code == 2
    assert not list(outside.iterdir())
    assert not Path("AGENTS.md").exists()
    assert not get_agent_config_path(WIKI_DIR).exists()


def test_upgrade_revalidates_scaffold_after_reference_provision(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    outside = tmp_project.parent / f"{tmp_project.name}-late-upgrade-scaffold"
    outside.mkdir()
    modules = Path(WIKI_DIR) / "modules"
    real_provision = upgrade_cmd.provision_reference_skill

    def provision_then_redirect(*args, **kwargs):
        result = real_provision(*args, **kwargs)
        shutil.rmtree(modules)
        modules.symlink_to(outside, target_is_directory=True)
        return result

    monkeypatch.setattr(
        upgrade_cmd,
        "provision_reference_skill",
        provision_then_redirect,
    )

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="generic"))

    assert caught.value.code == 2
    assert not list(outside.iterdir())


def test_upgrade_revalidates_nested_schema_parent_after_plugin_staging(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    outside = tmp_project.parent / f"{tmp_project.name}-late-target-schema"
    outside.mkdir()
    held = Path(".github-held")
    real_blocks = upgrade_cmd.installed_skill_block_contents

    def stage_then_redirect():
        blocks = real_blocks()
        Path(".github").rename(held)
        Path(".github").symlink_to(outside, target_is_directory=True)
        return blocks

    monkeypatch.setattr(
        upgrade_cmd,
        "installed_skill_block_contents",
        stage_then_redirect,
    )

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="copilot"))

    assert caught.value.code == 2
    assert not (outside / "copilot-instructions.md").exists()
    assert Path("AGENTS.md").exists()
    assert read_config(WIKI_DIR)["agent"] == "generic"


def test_upgrade_revalidates_source_schema_parent_before_cleanup(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("copilot")
    outside = tmp_project.parent / f"{tmp_project.name}-late-source-schema"
    outside.mkdir()
    outside_schema = outside / "copilot-instructions.md"
    outside_schema.write_text("outside user schema\n", encoding="utf-8")
    held = Path(".github-held")
    real_strip = upgrade_cmd.strip_wiki_block
    redirected = False

    def strip_then_redirect(content: str) -> str:
        nonlocal redirected
        stripped = real_strip(content)
        if not redirected:
            redirected = True
            Path(".github").rename(held)
            Path(".github").symlink_to(outside, target_is_directory=True)
        return stripped

    monkeypatch.setattr(upgrade_cmd, "strip_wiki_block", strip_then_redirect)

    with pytest.raises(ManagedSchemaPathError):
        upgrade_cmd.run(_upgrade_args(agent="generic"))

    assert outside_schema.read_text(encoding="utf-8") == "outside user schema\n"
    config = read_config(WIKI_DIR)
    assert config["agent"] == "generic"
    assert config["pending_cleanup_agent"] == "copilot"


def test_upgrade_guarded_reference_cleanup_rejects_late_parent_redirect(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    outside = tmp_project.parent / f"{tmp_project.name}-late-source-reference"
    outside_reference = outside / "skills/wiki-reference"
    outside_reference.mkdir(parents=True)
    sentinel = outside_reference / "outside.txt"
    sentinel.write_text("outside\n", encoding="utf-8")
    held = Path(".llm-wiki-held")
    real_remove = upgrade_cmd.remove_guarded_tree

    def redirect_then_remove(path, **kwargs):
        Path(".llm-wiki").rename(held)
        Path(".llm-wiki").symlink_to(outside, target_is_directory=True)
        return real_remove(path, **kwargs)

    monkeypatch.setattr(upgrade_cmd, "remove_guarded_tree", redirect_then_remove)

    upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert sentinel.read_text(encoding="utf-8") == "outside\n"
    assert (held / "skills/wiki-reference/reference.md").exists()
    config = read_config(WIKI_DIR)
    assert config["agent"] == "claude"
    assert config["pending_cleanup_agent"] == "generic"


def test_init_config_commit_is_bound_to_absent_inspected_snapshot(
    tmp_project,
    monkeypatch,
) -> None:
    config_path = get_agent_config_path(WIKI_DIR)
    real_write = init_cmd.write_config
    concurrent = {
        "agent": "generic",
        "quality_hints": True,
        "reference_skill": False,
        "issue_reporting": False,
        "pending_cleanup_agent": "claude",
        "pending_cleanup_reference": True,
        "extension_state": {"owner": "concurrent"},
    }
    injected = False

    def inject_before_commit(wiki_dir, data, **kwargs):
        nonlocal injected
        if not injected:
            injected = True
            config_path.write_text(json.dumps(concurrent), encoding="utf-8")
        return real_write(wiki_dir, data, **kwargs)

    monkeypatch.setattr(init_cmd, "write_config", inject_before_commit)

    with pytest.raises(OSError, match="appeared after preflight"):
        init_cmd.run(_init_args())

    assert json.loads(config_path.read_text(encoding="utf-8")) == concurrent


def test_upgrade_first_config_commit_preserves_concurrent_intent(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    config_path = get_agent_config_path(WIKI_DIR)
    real_write = upgrade_cmd.write_config
    concurrent = read_config(WIKI_DIR)
    concurrent.update(
        {
            "reference_skill": False,
            "extension_state": {"owner": "concurrent"},
        }
    )
    injected = False

    def inject_before_commit(wiki_dir, data, **kwargs):
        nonlocal injected
        if not injected:
            injected = True
            config_path.write_text(json.dumps(concurrent), encoding="utf-8")
        return real_write(wiki_dir, data, **kwargs)

    monkeypatch.setattr(upgrade_cmd, "write_config", inject_before_commit)

    with pytest.raises(OSError, match="changed after preflight"):
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert json.loads(config_path.read_text(encoding="utf-8")) == concurrent
    assert Path("AGENTS.md").exists()
    assert verify_reference_skill(agent="generic").current


def test_upgrade_marker_clear_is_bound_to_pending_config_commit(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    config_path = get_agent_config_path(WIKI_DIR)
    real_write = upgrade_cmd.write_config
    writes = 0
    concurrent_bytes = b""

    def inject_before_clear(wiki_dir, data, **kwargs):
        nonlocal writes, concurrent_bytes
        writes += 1
        if writes == 2:
            concurrent = json.loads(config_path.read_text(encoding="utf-8"))
            concurrent["extension_state"] = {"owner": "concurrent"}
            concurrent_bytes = json.dumps(concurrent).encode("utf-8")
            config_path.write_bytes(concurrent_bytes)
        return real_write(wiki_dir, data, **kwargs)

    monkeypatch.setattr(upgrade_cmd, "write_config", inject_before_clear)

    with pytest.raises(OSError, match="changed after preflight"):
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert config_path.read_bytes() == concurrent_bytes
    concurrent_config = json.loads(concurrent_bytes)
    assert concurrent_config["pending_cleanup_agent"] == "generic"
    assert not Path("AGENTS.md").exists()


def test_upgrade_late_fallback_change_blocks_source_cleanup_and_future_guessing(
    tmp_project,
    monkeypatch,
) -> None:
    git_dir = Path(".git")
    held_git = Path(".git-held")
    git_dir.rename(held_git)
    try:
        _initialize_current("generic")
        fallback = Path(WIKI_DIR) / ".llm-wiki-agent"
        assert fallback.exists()
    finally:
        held_git.rename(git_dir)

    real_unlink = upgrade_cmd.unlink_guarded_bytes
    concurrent = read_config(WIKI_DIR)
    concurrent.update(
        {
            "reference_skill": False,
            "extension_state": {"owner": "concurrent"},
        }
    )

    def change_fallback_then_unlink(path, **kwargs):
        fallback.write_text(json.dumps(concurrent), encoding="utf-8")
        return real_unlink(path, **kwargs)

    monkeypatch.setattr(
        upgrade_cmd,
        "unlink_guarded_bytes",
        change_fallback_then_unlink,
    )

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    assert Path("AGENTS.md").exists()
    assert verify_reference_skill(agent="generic").current
    assert fallback.exists()
    assert get_agent_config_path(WIKI_DIR).exists()
    inspection = inspect_config(WIKI_DIR)
    assert inspection.state is AgentConfigState.INVALID
    assert inspection.reason == "multiple-agent-config-homes"


def test_source_schema_cleanup_uses_one_coherent_content_snapshot(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    source = Path("AGENTS.md")
    real_read_bytes = Path.read_bytes
    concurrent = "# Concurrent user edit\n"
    changed = False

    def read_then_change(path: Path) -> bytes:
        nonlocal changed
        data = real_read_bytes(path)
        if path == source and not changed:
            changed = True
            path.write_text(concurrent, encoding="utf-8")
        return data

    monkeypatch.setattr(Path, "read_bytes", read_then_change)

    with pytest.raises(ManagedSchemaPathError, match="changed or could not"):
        upgrade_cmd._clean_old_schema("generic", "claude")

    assert source.read_text(encoding="utf-8") == concurrent


def test_init_does_not_report_success_when_second_config_home_appears_after_commit(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    real_write = init_cmd.write_config
    fallback = Path(WIKI_DIR) / ".llm-wiki-agent"

    def commit_then_create_fallback(wiki_dir, data, **kwargs):
        result = real_write(wiki_dir, data, **kwargs)
        fallback.write_text(
            json.dumps(
                {
                    "agent": "claude",
                    "reference_skill": False,
                    "extension_state": {"owner": "concurrent"},
                }
            ),
            encoding="utf-8",
        )
        return result

    monkeypatch.setattr(init_cmd, "write_config", commit_then_create_fallback)

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args())

    assert caught.value.code == 2
    assert "initialized successfully" not in capsys.readouterr().out
    assert inspect_config(WIKI_DIR).reason == "multiple-agent-config-homes"


def test_upgrade_rechecks_config_homes_before_source_cleanup(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    real_write = upgrade_cmd.write_config
    fallback = Path(WIKI_DIR) / ".llm-wiki-agent"
    writes = 0

    def commit_then_create_fallback(wiki_dir, data, **kwargs):
        nonlocal writes
        result = real_write(wiki_dir, data, **kwargs)
        writes += 1
        if writes == 1:
            fallback.write_text(
                json.dumps(
                    {
                        "agent": "generic",
                        "reference_skill": False,
                        "pending_cleanup_agent": "copilot",
                        "pending_cleanup_reference": False,
                        "extension_state": {"owner": "concurrent"},
                    }
                ),
                encoding="utf-8",
            )
        return result

    monkeypatch.setattr(upgrade_cmd, "write_config", commit_then_create_fallback)

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    assert Path("AGENTS.md").exists()
    assert verify_reference_skill(agent="generic").current
    assert inspect_config(WIKI_DIR).reason == "multiple-agent-config-homes"


@pytest.mark.parametrize("changed_target", ["schema", "reference"])
def test_upgrade_revalidates_target_before_source_cleanup(
    tmp_project,
    monkeypatch,
    changed_target: str,
    capsys,
) -> None:
    _initialize_current("generic")
    real_cleanup = upgrade_cmd._cleanup_recorded_source

    def change_target_then_cleanup(*args, **kwargs):
        if changed_target == "schema":
            Path("CLAUDE.md").unlink()
        else:
            target = Path(".claude/skills/wiki-reference/reference.md")
            target.write_text(
                target.read_text(encoding="utf-8") + "\nconcurrent edit\n",
                encoding="utf-8",
            )
        return real_cleanup(*args, **kwargs)

    monkeypatch.setattr(
        upgrade_cmd,
        "_cleanup_recorded_source",
        change_target_then_cleanup,
    )

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    output = capsys.readouterr().out
    assert "source cleanup is incomplete" in output
    assert Path("AGENTS.md").exists()
    assert verify_reference_skill(agent="generic").current
    config = read_config(WIKI_DIR)
    assert config["pending_cleanup_agent"] == "generic"


@pytest.mark.parametrize("changed_target", ["schema", "reference"])
def test_init_revalidates_compact_target_before_reporting_success(
    tmp_project,
    monkeypatch,
    changed_target: str,
    capsys,
) -> None:
    real_write = init_cmd.write_config

    def commit_then_change_target(wiki_dir, data, **kwargs):
        result = real_write(wiki_dir, data, **kwargs)
        if changed_target == "schema":
            Path("AGENTS.md").unlink()
        else:
            target = Path(".llm-wiki/skills/wiki-reference/reference.md")
            target.write_text(
                target.read_text(encoding="utf-8") + "\nconcurrent edit\n",
                encoding="utf-8",
            )
        return result

    monkeypatch.setattr(init_cmd, "write_config", commit_then_change_target)

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args())

    assert caught.value.code == 2
    assert "initialized successfully" not in capsys.readouterr().out


def test_init_rejects_agent_change_without_switch_transaction(tmp_project) -> None:
    _initialize_current("generic")
    Path("AGENTS.md").unlink()
    source_reference = Path(".llm-wiki/skills/wiki-reference/reference.md")
    source_reference_before = source_reference.read_bytes()

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args(agent="claude"))

    assert caught.value.code == 2
    assert read_config(WIKI_DIR)["agent"] == "generic"
    assert not Path("AGENTS.md").exists()
    assert source_reference.read_bytes() == source_reference_before
    assert not Path("CLAUDE.md").exists()
    assert not Path(".claude/skills/wiki-reference").exists()


def test_init_rejects_parallel_schema_even_when_config_selects_target(
    tmp_project,
) -> None:
    _initialize_current("generic")
    Path("CLAUDE.md").write_text(
        build_schema_content(
            "claude",
            WIKI_DIR,
            render_profile=SchemaRenderProfile.EXPANDED_INLINE,
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args(agent="generic"))

    assert caught.value.code == 2
    assert read_config(WIKI_DIR)["agent"] == "generic"


def test_opt_out_upgrade_rechecks_target_after_source_schema_cleanup(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    init_cmd.run(_init_args(agent="generic", no_skills=True))
    real_clean = upgrade_cmd._clean_old_schema

    def clean_then_remove_target(*args, **kwargs):
        result = real_clean(*args, **kwargs)
        Path("CLAUDE.md").unlink()
        return result

    monkeypatch.setattr(upgrade_cmd, "_clean_old_schema", clean_then_remove_target)

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude", skills=False))

    assert caught.value.code == 2
    output = capsys.readouterr().out
    assert "source cleanup is incomplete" in output
    assert "did not reach a verified terminal target state" in output
    assert "Upgrade complete" not in output
    config = read_config(WIKI_DIR)
    assert config["pending_cleanup_agent"] == "generic"
    assert config["pending_cleanup_reference"] is False


def test_init_rechecks_parallel_schemas_before_reporting_success(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    real_write = init_cmd.write_config

    def commit_then_create_parallel(wiki_dir, data, **kwargs):
        result = real_write(wiki_dir, data, **kwargs)
        Path("CLAUDE.md").write_text(
            build_schema_content(
                "claude",
                WIKI_DIR,
                render_profile=SchemaRenderProfile.EXPANDED_INLINE,
            ),
            encoding="utf-8",
        )
        return result

    monkeypatch.setattr(init_cmd, "write_config", commit_then_create_parallel)

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args(agent="generic"))

    assert caught.value.code == 2
    assert "initialized successfully" not in capsys.readouterr().out


def test_same_agent_upgrade_revalidates_target_before_reporting_success(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    real_write = upgrade_cmd.write_config

    def commit_then_remove_schema(wiki_dir, data, **kwargs):
        result = real_write(wiki_dir, data, **kwargs)
        Path("AGENTS.md").unlink()
        return result

    monkeypatch.setattr(upgrade_cmd, "write_config", commit_then_remove_schema)

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="generic"))

    assert caught.value.code == 2
    output = capsys.readouterr().out
    assert "did not reach a verified terminal target state" in output
    assert "Upgrade complete" not in output


def test_upgrade_revalidates_target_after_pending_marker_clear(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    real_write = upgrade_cmd.write_config
    writes = 0

    def clear_then_remove_schema(wiki_dir, data, **kwargs):
        nonlocal writes
        result = real_write(wiki_dir, data, **kwargs)
        writes += 1
        if writes == 2:
            Path("CLAUDE.md").unlink()
        return result

    monkeypatch.setattr(upgrade_cmd, "write_config", clear_then_remove_schema)

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    output = capsys.readouterr().out
    assert "did not reach a verified terminal target state" in output
    assert "Upgrade complete" not in output


def test_source_reference_removal_rechecks_target_after_source_manifest(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    real_manifest = upgrade_cmd.guarded_tree_manifest
    changed = False

    def manifest_then_change_target(path):
        nonlocal changed
        manifest = real_manifest(path)
        if not changed and Path(path).name == "wiki-reference":
            changed = True
            target = Path(".claude/skills/wiki-reference/reference.md")
            target.write_text(
                target.read_text(encoding="utf-8") + "\nconcurrent edit\n",
                encoding="utf-8",
            )
        return manifest

    monkeypatch.setattr(
        upgrade_cmd,
        "guarded_tree_manifest",
        manifest_then_change_target,
    )

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    assert Path(".llm-wiki/skills/wiki-reference/reference.md").exists()
    config = read_config(WIKI_DIR)
    assert config["pending_cleanup_agent"] == "generic"


def test_init_rechecks_derived_reference_intent_inside_provisioning(
    tmp_project,
    monkeypatch,
) -> None:
    real_provision = init_cmd.provision_reference_skill
    concurrent = {
        "agent": "generic",
        "quality_hints": True,
        "reference_skill": False,
        "issue_reporting": False,
        "extension_state": {"owner": "concurrent"},
    }

    def change_intent_then_provision(*args, **kwargs):
        write_config(WIKI_DIR, concurrent)
        return real_provision(*args, **kwargs)

    monkeypatch.setattr(
        init_cmd,
        "provision_reference_skill",
        change_intent_then_provision,
    )

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args())

    assert caught.value.code == 2
    assert not Path(".llm-wiki/skills/wiki-reference").exists()
    assert not Path("AGENTS.md").exists()
    assert read_config(WIKI_DIR)["extension_state"] == {"owner": "concurrent"}


def test_upgrade_rechecks_derived_reference_intent_inside_provisioning(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    source_schema = Path("AGENTS.md").read_bytes()
    source_reference = Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()
    real_provision = upgrade_cmd.provision_reference_skill

    def change_intent_then_provision(*args, **kwargs):
        concurrent = read_config(WIKI_DIR)
        concurrent["reference_skill"] = False
        concurrent["extension_state"] = {"owner": "concurrent"}
        write_config(WIKI_DIR, concurrent)
        return real_provision(*args, **kwargs)

    monkeypatch.setattr(
        upgrade_cmd,
        "provision_reference_skill",
        change_intent_then_provision,
    )

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    assert not Path(".claude/skills/wiki-reference").exists()
    assert not Path("CLAUDE.md").exists()
    assert Path("AGENTS.md").read_bytes() == source_schema
    assert (
        Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()
        == source_reference
    )
    assert read_config(WIKI_DIR)["extension_state"] == {"owner": "concurrent"}


def test_upgrade_rechecks_pending_config_before_source_cleanup(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    source_schema = Path("AGENTS.md").read_bytes()
    source_reference = Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()
    real_cleanup = upgrade_cmd._cleanup_recorded_source
    concurrent_bytes: bytes | None = None

    def change_config_then_cleanup(*args, **kwargs):
        nonlocal concurrent_bytes
        concurrent = read_config(WIKI_DIR)
        concurrent["reference_skill"] = False
        concurrent["extension_state"] = {"owner": "concurrent"}
        concurrent.pop("pending_cleanup_agent", None)
        concurrent.pop("pending_cleanup_reference", None)
        write_config(WIKI_DIR, concurrent)
        concurrent_bytes = get_agent_config_path(WIKI_DIR).read_bytes()
        return real_cleanup(*args, **kwargs)

    monkeypatch.setattr(
        upgrade_cmd,
        "_cleanup_recorded_source",
        change_config_then_cleanup,
    )

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    assert Path("AGENTS.md").read_bytes() == source_schema
    assert (
        Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()
        == source_reference
    )
    assert concurrent_bytes is not None
    assert get_agent_config_path(WIKI_DIR).read_bytes() == concurrent_bytes
    assert "config authority changed" in capsys.readouterr().out


def test_upgrade_rechecks_pending_config_at_source_schema_commit(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    source_schema = Path("AGENTS.md").read_bytes()
    source_reference = Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()
    real_strip = upgrade_cmd.strip_wiki_block
    changed = False
    concurrent_bytes: bytes | None = None

    def strip_then_change_config(content: str) -> str:
        nonlocal changed, concurrent_bytes
        stripped = real_strip(content)
        if not changed:
            changed = True
            concurrent = read_config(WIKI_DIR)
            concurrent["reference_skill"] = False
            concurrent["extension_state"] = {"owner": "concurrent"}
            concurrent.pop("pending_cleanup_agent", None)
            concurrent.pop("pending_cleanup_reference", None)
            write_config(WIKI_DIR, concurrent)
            concurrent_bytes = get_agent_config_path(WIKI_DIR).read_bytes()
        return stripped

    monkeypatch.setattr(upgrade_cmd, "strip_wiki_block", strip_then_change_config)

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    assert Path("AGENTS.md").read_bytes() == source_schema
    assert (
        Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()
        == source_reference
    )
    assert concurrent_bytes is not None
    assert get_agent_config_path(WIKI_DIR).read_bytes() == concurrent_bytes


def test_upgrade_restores_source_schema_when_config_changes_during_manifest(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    source_schema = Path("AGENTS.md").read_bytes()
    source_reference = Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()
    real_manifest = upgrade_cmd.guarded_tree_manifest
    changed = False
    concurrent_bytes: bytes | None = None

    def manifest_then_change_config(path):
        nonlocal changed, concurrent_bytes
        manifest = real_manifest(path)
        if not changed and Path(path).name == "wiki-reference":
            changed = True
            concurrent = read_config(WIKI_DIR)
            concurrent["reference_skill"] = False
            concurrent["extension_state"] = {"owner": "concurrent"}
            concurrent.pop("pending_cleanup_agent", None)
            concurrent.pop("pending_cleanup_reference", None)
            write_config(WIKI_DIR, concurrent)
            concurrent_bytes = get_agent_config_path(WIKI_DIR).read_bytes()
        return manifest

    monkeypatch.setattr(
        upgrade_cmd,
        "guarded_tree_manifest",
        manifest_then_change_config,
    )

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    assert Path("AGENTS.md").read_bytes() == source_schema
    assert (
        Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()
        == source_reference
    )
    assert concurrent_bytes is not None
    assert get_agent_config_path(WIKI_DIR).read_bytes() == concurrent_bytes


def test_source_removal_checks_config_after_late_target_verification(
    tmp_project,
    monkeypatch,
) -> None:
    _initialize_current("generic")
    source_schema = Path("AGENTS.md").read_bytes()
    source_reference = Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()
    real_manifest = upgrade_cmd.guarded_tree_manifest
    real_target_check = upgrade_cmd._target_cleanup_is_ready
    source_manifest_seen = False
    changed = False
    concurrent_bytes: bytes | None = None

    def observe_source_manifest(path):
        nonlocal source_manifest_seen
        manifest = real_manifest(path)
        if Path(path).name == "wiki-reference":
            source_manifest_seen = True
        return manifest

    def verify_target_then_change_config(*args, **kwargs):
        nonlocal changed, concurrent_bytes
        result = real_target_check(*args, **kwargs)
        if source_manifest_seen and not changed:
            changed = True
            concurrent = read_config(WIKI_DIR)
            concurrent["reference_skill"] = False
            concurrent["extension_state"] = {"owner": "concurrent"}
            concurrent.pop("pending_cleanup_agent", None)
            concurrent.pop("pending_cleanup_reference", None)
            write_config(WIKI_DIR, concurrent)
            concurrent_bytes = get_agent_config_path(WIKI_DIR).read_bytes()
        return result

    monkeypatch.setattr(
        upgrade_cmd,
        "guarded_tree_manifest",
        observe_source_manifest,
    )
    monkeypatch.setattr(
        upgrade_cmd,
        "_target_cleanup_is_ready",
        verify_target_then_change_config,
    )

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="claude"))

    assert caught.value.code == 2
    assert Path("AGENTS.md").read_bytes() == source_schema
    assert (
        Path(".llm-wiki/skills/wiki-reference/reference.md").read_bytes()
        == source_reference
    )
    assert concurrent_bytes is not None
    assert get_agent_config_path(WIKI_DIR).read_bytes() == concurrent_bytes


@pytest.mark.parametrize("late_change", ["config", "schema"])
def test_init_checks_config_and_schema_after_final_reference_verification(
    tmp_project,
    monkeypatch,
    capsys,
    late_change: str,
) -> None:
    real_verify = init_cmd.verify_reference_skill
    concurrent_bytes: bytes | None = None

    def verify_then_change(*args, **kwargs):
        nonlocal concurrent_bytes
        result = real_verify(*args, **kwargs)
        if late_change == "schema":
            Path("AGENTS.md").unlink()
        else:
            concurrent = read_config(WIKI_DIR)
            concurrent["reference_skill"] = False
            concurrent["extension_state"] = {"owner": "concurrent"}
            write_config(WIKI_DIR, concurrent)
            concurrent_bytes = get_agent_config_path(WIKI_DIR).read_bytes()
        return result

    monkeypatch.setattr(init_cmd, "verify_reference_skill", verify_then_change)

    with pytest.raises(SystemExit) as caught:
        init_cmd.run(_init_args())

    assert caught.value.code == 2
    assert "initialized successfully" not in capsys.readouterr().out
    if late_change == "config":
        assert concurrent_bytes is not None
        assert get_agent_config_path(WIKI_DIR).read_bytes() == concurrent_bytes
    else:
        assert not Path("AGENTS.md").exists()


def test_upgrade_checks_schema_after_final_reference_verification(
    tmp_project,
    monkeypatch,
    capsys,
) -> None:
    _initialize_current("generic")
    real_verify = upgrade_cmd.verify_reference_skill
    calls = 0

    def verify_then_remove_schema(*args, **kwargs):
        nonlocal calls
        result = real_verify(*args, **kwargs)
        if kwargs.get("agent") == "generic":
            calls += 1
            if calls == 2:
                Path("AGENTS.md").unlink()
        return result

    monkeypatch.setattr(upgrade_cmd, "verify_reference_skill", verify_then_remove_schema)

    with pytest.raises(SystemExit) as caught:
        upgrade_cmd.run(_upgrade_args(agent="generic"))

    assert caught.value.code == 2
    output = capsys.readouterr().out
    assert "did not reach a verified terminal target state" in output
    assert "Upgrade complete" not in output
