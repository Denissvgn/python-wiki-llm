"""Tests for commands/status_cmd.py"""

import json
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import context_cmd, extract_cmd, status_cmd
from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.services import knowledge_consumption
from llm_wiki_cli.services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from llm_wiki_cli.services.rendering_lifecycle import (
    LifecycleStatus,
    ManagedLifecycleState,
)
from llm_wiki_cli.services.schema import (
    CONSTRAINT_END,
    CONSTRAINT_START,
    ManagedSchemaBlockState,
    SchemaRenderProfile,
)
from llm_wiki_cli.services.skills import (
    ReferenceSkillReason,
    ReferenceSkillState,
    ReferenceSkillVerification,
)
from tests.knowledge_fixtures import fail_if_extraction_runs
from tests.test_knowledge_loader import _committed_state


def _make_args(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _status_counts(output: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in output.splitlines():
        label, sep, rest = line.strip().partition(":")
        if not sep:
            continue
        value = rest.strip().split(maxsplit=1)[0] if rest.strip() else ""
        if value.isdigit():
            counts[label] = int(value)
    return counts


def _write_agent_config(project: Path, **overrides: object) -> None:
    config: dict[str, object] = {
        "agent": "generic",
        "quality_hints": True,
        "reference_skill": True,
        "issue_reporting": False,
    }
    config.update(overrides)
    (project / ".git" / ".llm-wiki-agent").write_text(
        json.dumps(config),
        encoding="utf-8",
    )


def _write_profiled_schema(path: Path, profile: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{CONSTRAINT_START}\n"
        f"<!-- llm-wiki-schema: version=1 profile={profile} -->\n"
        "managed instructions\n"
        f"{CONSTRAINT_END}\n",
        encoding="utf-8",
    )


def test_managed_schema_reader_accepts_preserved_non_utf8_user_bytes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "AGENTS.md"
    managed = (
        f"{CONSTRAINT_START}\r\n"
        "<!-- llm-wiki-schema: version=1 profile=compact -->\r\n"
        "managed instructions\r\n"
        f"{CONSTRAINT_END}\r\n"
    ).encode("ascii")
    path.write_bytes(b"# User byte: \x81\r\n" + managed)

    block = status_cmd._read_managed_schema(path)

    assert block.state is ManagedSchemaBlockState.PROFILED
    assert block.profile is SchemaRenderProfile.COMPACT


@pytest.mark.parametrize(
    ("state", "reason", "details"),
    [
        (
            ReferenceSkillState.PACKAGE_MISSING,
            ReferenceSkillReason.PACKAGE_MISSING,
            (),
        ),
        (
            ReferenceSkillState.LOCALLY_MODIFIED,
            ReferenceSkillReason.LOCALLY_MODIFIED,
            ("content_mismatch:reference.md",),
        ),
        (
            ReferenceSkillState.INCOMPLETE,
            ReferenceSkillReason.INCOMPLETE,
            ("extra:references/local.md",),
        ),
    ],
)
def test_disabled_compact_recovery_never_requires_reference_mutation(
    state: ReferenceSkillState,
    reason: ReferenceSkillReason,
    details: tuple[str, ...],
) -> None:
    lifecycle = LifecycleStatus(
        state=ManagedLifecycleState.COMPACT_BROKEN,
        rendered_profile="compact",
        reference_state=state.value,
        reference_path=".llm-wiki/skills/wiki-reference",
        reference_current=False,
        read_only_knowledge="independent",
        warning="compact-profile-with-managed-reference-disabled",
        recovery_command=None,
    )
    reference = ReferenceSkillVerification(
        state=state,
        reason=reason,
        path=Path(".llm-wiki/skills/wiki-reference"),
        details=details,
    )

    guidance = status_cmd._recovery_guidance(
        lifecycle=lifecycle,
        reference=reference,
        wiki_dir="docs/llm_wiki",
        agent="generic",
        reference_enabled=False,
        interrupted_switch=False,
    )

    assert guidance.endswith("--agent generic --no-skills")
    assert "repair or upgrade" not in guidance
    assert "move them aside" not in guidance
    assert "back up local managed-reference" not in guidance


def _write_legacy_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{CONSTRAINT_START}\nmanaged instructions\n{CONSTRAINT_END}\n",
        encoding="utf-8",
    )


def _guard_live_knowledge_evaluation(monkeypatch) -> None:
    monkeypatch.setattr(
        extract_cmd,
        "build_extract_payload",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        extract_cmd,
        "get_inventory_result",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        context_cmd,
        "get_inventory_result",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        knowledge_consumption,
        "evaluate_knowledge_freshness",
        fail_if_extraction_runs,
    )


class TestStatusWiki:
    def test_shows_wiki_exists(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        for d in ["entities", "modules", "workflows", "flows", "infrastructure"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "index.md").write_text("# Index\n")
        (wiki / "log.md").write_text("# Log\n")
        (wiki / "entities" / "User.md").write_text("# User\n")
        (wiki / "modules" / "main.md").write_text("# main\n")
        (wiki / "workflows" / "signup.md").write_text("# signup\n")
        (wiki / "flows" / "checkout.md").write_text("# checkout\n")
        (wiki / "infrastructure" / "Dockerfile.md").write_text("# Dockerfile\n")
        (wiki / "api-contracts.md").write_text("# API contracts\n")
        (wiki / "dependencies.md").write_text("# Dependencies\n")
        (wiki / "load-order.md").write_text("# Load Order\n")

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        counts = _status_counts(out)

        assert "exists" in out
        assert counts["Index"] == 1
        assert counts["Log"] == 1
        assert counts["Entities"] == 1
        assert counts["Modules"] == 1
        assert counts["Workflows"] == 1
        assert counts["Flows"] == 1
        assert counts["Infrastructure"] == 1
        assert counts["API contracts"] == 1
        assert counts["Dependencies"] == 1
        assert counts["Load order"] == 1
        assert counts["Architecture pages"] == 3

    def test_counts_wiki_pages_without_materializing_globs(
        self, tmp_project, capsys, monkeypatch
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        for d in ["entities", "modules", "workflows", "flows", "infrastructure"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "entities" / "User.md").write_text("# User\n")
        (wiki / "modules" / "main.md").write_text("# main\n")
        (wiki / "workflows" / "signup.md").write_text("# signup\n")
        (wiki / "flows" / "checkout.md").write_text("# checkout\n")
        (wiki / "infrastructure" / "Dockerfile.md").write_text("# Dockerfile\n")

        def fail_if_materialized(*_args, **_kwargs):
            raise AssertionError(
                "status should count glob results without list allocation"
            )

        monkeypatch.setattr(status_cmd, "list", fail_if_materialized, raising=False)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        counts = _status_counts(out)

        assert counts["Entities"] == 1
        assert counts["Modules"] == 1
        assert counts["Workflows"] == 1
        assert counts["Flows"] == 1
        assert counts["Infrastructure"] == 1

    def test_missing_optional_registry_surfaces_count_as_zero(
        self, tmp_project, capsys
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        for d in ["entities", "modules", "workflows"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "entities" / "User.md").write_text("# User\n")

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        counts = _status_counts(out)

        assert counts["Index"] == 0
        assert counts["Log"] == 0
        assert counts["Entities"] == 1
        assert counts["Modules"] == 0
        assert counts["Workflows"] == 0
        assert counts["Flows"] == 0
        assert counts["Infrastructure"] == 0
        assert counts["API contracts"] == 0
        assert counts["Dependencies"] == 0
        assert counts["Load order"] == 0
        assert counts["Architecture pages"] == 0

    def test_shows_wiki_missing(self, tmp_project, capsys):
        status_cmd.run(_make_args(wiki_dir="nonexistent"))
        out = capsys.readouterr().out
        assert "not found" in out


class TestStatusKnowledge:
    def test_ready_projection_reports_snapshot_only_aggregates(
        self,
        tmp_project,
        capsys,
        monkeypatch,
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        _committed_state(wiki)
        _guard_live_knowledge_evaluation(monkeypatch)

        status_cmd.run(_make_args(wiki_dir=str(wiki), src_dir="."))

        out = capsys.readouterr().out
        assert (
            "Knowledge:       ready (reason: all-projection-commitments-match)"
        ) in out
        assert "Concepts evaluated: 0" in out
        assert "Evidence issues: invalid=0, missing=0, unknown=1" in out
        assert "Freshness: unevaluated (snapshot-only read)" in out
        assert "llm-wiki://entities/User" not in out
        assert "sha256:" not in out

    def test_legacy_projection_reports_absent_without_live_evaluation(
        self,
        tmp_project,
        capsys,
        monkeypatch,
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)
        (wiki / "index.md").write_bytes(b"\xff")
        _guard_live_knowledge_evaluation(monkeypatch)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        assert (
            "Knowledge:       absent (reason: knowledge-projection-not-present)"
        ) in out
        assert "Evidence issues: unavailable" in out
        assert "Freshness: unevaluated (snapshot-only read)" in out

    def test_invalid_projection_reports_degraded_without_serving_evidence(
        self,
        tmp_project,
        capsys,
        monkeypatch,
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        _committed_state(wiki)
        (wiki / KNOWLEDGE_INDEX_FILENAME).write_bytes(b"{not-json\n")
        _guard_live_knowledge_evaluation(monkeypatch)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        assert (
            "Knowledge:       degraded "
            "(reason: policy-selected-surface-only-fallback-after-invalid)"
        ) in out
        assert "Concepts evaluated: 0" in out
        assert "Evidence issues: unavailable" in out
        assert "Freshness: unevaluated (snapshot-only read)" in out
        assert "llm-wiki://entities/User" not in out
        assert "sha256:" not in out


class TestStatusAgent:
    def test_shows_configured_agent(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)
        (tmp_project / ".git" / ".llm-wiki-agent").write_text("claude")

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "claude" in out
        assert "CLI" in out
        assert "Issue reporting: disabled" in out

    def test_shows_issue_reporting_enabled(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)
        config = {
            "agent": "copilot",
            "quality_hints": True,
            "issue_reporting": True,
        }
        (tmp_project / ".git" / ".llm-wiki-agent").write_text(
            json.dumps(config), encoding="utf-8"
        )

        status_cmd.run(_make_args(wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        assert "Issue reporting: enabled" in out

    def test_shows_ide_agent(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)
        (tmp_project / ".git" / ".llm-wiki-agent").write_text("copilot")

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "copilot" in out
        assert "IDE" in out

    def test_shows_not_configured(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "not configured" in out


class TestStatusHooks:
    def test_detects_installed_hooks(self, tmp_project, capsys):
        from llm_wiki_cli.commands import hook_cmd

        hooks_dir = tmp_project / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook = hooks_dir / "post-commit"
        hook.write_text(
            hook_cmd._build_ide_post_commit("docs/llm_wiki"),
            encoding="utf-8",
        )
        hook.chmod(0o755)

        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "post-commit" in out

    def test_exact_managed_hook_without_execute_bit_is_reported_broken(
        self, tmp_project, capsys
    ):
        from llm_wiki_cli.commands import hook_cmd

        hook = tmp_project / ".git" / "hooks" / "post-commit"
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text(
            hook_cmd._build_ide_post_commit("docs/llm_wiki"),
            encoding="utf-8",
        )
        hook.chmod(0o644)
        (tmp_project / "docs" / "llm_wiki").mkdir(parents=True)

        status_cmd.run(_make_args())

        output = capsys.readouterr().out
        assert "non-executable: post-commit" in output
        assert "install-hook --force" in output

    def test_does_not_claim_signature_substring_hook_is_managed(
        self, tmp_project, capsys
    ):
        hooks_dir = tmp_project / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        (hooks_dir / "post-commit").write_text(
            '#!/bin/sh\necho "check whether LLM Wiki is stale"\n',
            encoding="utf-8",
        )
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        assert "Hooks:           none installed" in out

    def test_rejects_wiki_symlink_outside_project_before_reading(
        self,
        tmp_project,
        tmp_path,
    ):
        outside = tmp_path / "outside-wiki"
        (outside / "entities").mkdir(parents=True)
        (outside / "entities/secret.md").write_text("secret\n", encoding="utf-8")
        wiki_link = Path("wiki")
        try:
            wiki_link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:  # pragma: no cover - platform policy
            pytest.skip(f"symlinks unavailable: {exc}")

        with pytest.raises(PathValidationError):
            status_cmd.run(_make_args(wiki_dir="wiki", src_dir="."))

    @pytest.mark.parametrize("damage", ["root-file", "root-link", "child-link"])
    def test_scaffold_path_damage_blocks_nonconvergent_lifecycle_recovery(
        self,
        tmp_project,
        monkeypatch,
        capsys,
        damage: str,
    ):
        wiki = Path("wiki")
        outside = Path("outside")
        outside.mkdir()
        if damage == "root-file":
            wiki.write_text("not a directory\n", encoding="utf-8")
        elif damage == "root-link":
            target = Path("internal-wiki")
            target.mkdir()
            try:
                wiki.symlink_to(target, target_is_directory=True)
            except OSError as exc:  # pragma: no cover - platform policy
                pytest.skip(f"symlinks unavailable: {exc}")
        else:
            wiki.mkdir()
            try:
                (wiki / "modules").symlink_to(outside, target_is_directory=True)
            except OSError as exc:  # pragma: no cover - platform policy
                pytest.skip(f"symlinks unavailable: {exc}")
        monkeypatch.setattr(
            status_cmd, "_print_knowledge_status", lambda *_a, **_k: None
        )

        status_cmd.run(_make_args(wiki_dir=wiki.as_posix(), src_dir="."))

        output = capsys.readouterr().out
        assert "wiki-scaffold-unavailable" in output
        assert "move aside or repair the unavailable wiki scaffold path" in output
        assert "then rerun `llm-wiki status" in output
        assert "before init or upgrade" in output
        assert "llm-wiki init --wiki-dir wiki" not in output
        assert not (outside / ".gitkeep").exists()

    def test_shows_no_hooks(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "none installed" in out


class TestStatusBreaker:
    def test_shows_closed(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "closed" in out

    def test_shows_open(self, tmp_project, capsys):
        git_dir = tmp_project / ".git"
        state = {
            "consecutive_failures": 3,
            "last_failure_ts": "2026-01-01T00:00:00+00:00",
            "state": "open",
        }
        (git_dir / "llm-wiki-breaker.json").write_text(json.dumps(state))

        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "OPEN" in out
        assert "3" in out
        assert "next trigger evaluates automatic recovery" in out.lower()

    def test_shows_active_half_open_recovery_probe(self, tmp_project, capsys):
        git_dir = tmp_project / ".git"
        state = {
            "consecutive_failures": 3,
            "last_failure_ts": "2026-01-01T00:00:00+00:00",
            "probe_started_ts": "2026-01-01T01:00:00+00:00",
            "state": "half-open",
        }
        (git_dir / "llm-wiki-breaker.json").write_text(json.dumps(state))
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        assert "HALF-OPEN" in out
        assert "recovery probe lease persisted" in out
        assert "next trigger evaluates the probe lease" in out.lower()


class TestStatusReferenceSkill:
    def test_not_installed(self, tmp_project, capsys):
        status_cmd.run(_make_args())
        out = capsys.readouterr().out
        assert "Reference skill: not installed" in out
        assert (
            "skills install --dest .llm-wiki/skills --skill wiki-reference --force"
            in out
        )

    def test_not_installed_claude_recovery_uses_native_target(
        self, tmp_project, capsys
    ):
        (tmp_project / ".git" / ".llm-wiki-agent").write_text(
            "claude",
            encoding="utf-8",
        )

        status_cmd.run(_make_args())

        out = capsys.readouterr().out
        assert (
            "skills install --dest .claude/skills --skill wiki-reference --force" in out
        )

    def test_current(self, tmp_project, capsys):
        from llm_wiki_cli.services.skills import install_reference_skill

        install_reference_skill(agent="generic")
        status_cmd.run(_make_args())
        out = capsys.readouterr().out
        assert "Reference skill: wiki-reference (current)" in out

    def test_differs_from_bundled(self, tmp_project, capsys):
        from llm_wiki_cli.services.skills import install_reference_skill

        install_reference_skill(agent="generic")
        Path(".llm-wiki/skills/wiki-reference/references/maintenance.md").write_text(
            "old\n", encoding="utf-8"
        )
        status_cmd.run(_make_args())
        out = capsys.readouterr().out
        assert "differs from bundled" in out
        assert "Reference repair: use the explicit state-aware Recovery command" in out
        assert "llm-wiki init --wiki-dir docs/llm_wiki --agent generic" in out
        assert (
            "skills install --dest .llm-wiki/skills --skill wiki-reference --force"
            in out
        )

    def test_missing_nested_topic_differs_from_bundled(self, tmp_project, capsys):
        from llm_wiki_cli.services.skills import install_reference_skill

        install_reference_skill(agent="generic")
        Path(".llm-wiki/skills/wiki-reference/references/governance.md").unlink()

        status_cmd.run(_make_args())

        assert "differs from bundled" in capsys.readouterr().out

    def test_extra_nested_topic_differs_from_bundled(self, tmp_project, capsys):
        from llm_wiki_cli.services.skills import install_reference_skill

        install_reference_skill(agent="generic")
        Path(".llm-wiki/skills/wiki-reference/references/local-notes.md").write_text(
            "notes\n", encoding="utf-8"
        )

        status_cmd.run(_make_args())

        assert "differs from bundled" in capsys.readouterr().out


class TestStatusManagedLifecycle:
    def test_live_compact_current_overrides_stale_persisted_profile(
        self, tmp_project, capsys
    ):
        from llm_wiki_cli.services.skills import install_reference_skill

        _write_agent_config(
            tmp_project,
            rendered_profile="expanded_inline",
            render_profile_version=1,
            render_reason="reference-absent",
        )
        _write_profiled_schema(tmp_project / "AGENTS.md", "compact")
        install_reference_skill(agent="generic")

        status_cmd.run(_make_args())

        out = capsys.readouterr().out
        assert "Managed lifecycle: compact/current" in out
        assert "Rendered profile: compact" in out
        assert "Reference state: current" in out
        assert "Reference path:  .llm-wiki/skills/wiki-reference" in out
        assert "Reference current: yes" in out
        assert "Read-only knowledge: independent" in out
        assert "persisted-render-state-does-not-match-live-files" in out

    def test_live_reference_drift_makes_configured_compact_broken(
        self, tmp_project, capsys
    ):
        _write_agent_config(
            tmp_project,
            rendered_profile="compact",
            render_profile_version=1,
            render_reason="reference-current",
        )
        _write_profiled_schema(tmp_project / "AGENTS.md", "compact")

        status_cmd.run(_make_args())

        out = capsys.readouterr().out
        assert "Managed lifecycle: compact/broken" in out
        assert "Reference state: absent" in out
        assert "Reference current: no" in out
        assert "compact-profile-with-managed-reference-absent" in out
        assert (
            "llm-wiki upgrade --wiki-dir docs/llm_wiki --agent generic --skills" in out
        )

    def test_expanded_opt_out_stays_disabled_even_with_current_reference(
        self, tmp_project, capsys
    ):
        from llm_wiki_cli.services.skills import install_reference_skill

        _write_agent_config(
            tmp_project,
            reference_skill=False,
            rendered_profile="expanded_inline",
            render_profile_version=1,
            render_reason="skills-disabled",
        )
        _write_profiled_schema(tmp_project / "AGENTS.md", "expanded_inline")
        install_reference_skill(agent="generic")

        status_cmd.run(_make_args())

        out = capsys.readouterr().out
        assert "Managed lifecycle: expanded/skills-disabled" in out
        assert "Reference current: yes" in out
        assert "Warning:         managed-reference-disabled" in out
        assert "Recovery command: none required; optional re-enable:" in out

    def test_expanded_reports_unavailable_reference(self, tmp_project, capsys):
        _write_agent_config(
            tmp_project,
            rendered_profile="expanded_inline",
            render_profile_version=1,
            render_reason="reference-absent",
        )
        _write_profiled_schema(tmp_project / "AGENTS.md", "expanded_inline")

        status_cmd.run(_make_args())

        out = capsys.readouterr().out
        assert "Managed lifecycle: expanded/reference-unavailable" in out
        assert "Reference reason: managed-reference-absent" in out
        assert "Read-only knowledge: independent" in out

    def test_legacy_managed_block_is_reported_without_prose_inference(
        self, tmp_project, capsys
    ):
        (tmp_project / ".git" / ".llm-wiki-agent").write_text(
            "generic",
            encoding="utf-8",
        )
        _write_legacy_schema(tmp_project / "AGENTS.md")

        status_cmd.run(_make_args())

        out = capsys.readouterr().out
        assert "Managed lifecycle: legacy-expanded" in out
        assert "Rendered profile: expanded_inline" in out
        assert "managed-schema-profile-marker-absent" in out

    def test_legacy_recovery_preserves_persisted_opt_out(self, tmp_project, capsys):
        _write_agent_config(tmp_project, reference_skill=False)
        _write_legacy_schema(tmp_project / "AGENTS.md")

        status_cmd.run(_make_args())

        out = capsys.readouterr().out
        assert (
            "llm-wiki upgrade --wiki-dir docs/llm_wiki --agent generic --no-skills"
            in out
        )

    def test_invalid_config_is_explicit_during_fallback_diagnostics(
        self, tmp_project, capsys
    ):
        (tmp_project / ".git" / ".llm-wiki-agent").write_text(
            "{not-json",
            encoding="utf-8",
        )
        _write_profiled_schema(tmp_project / "AGENTS.md", "compact")

        status_cmd.run(_make_args())

        out = capsys.readouterr().out
        assert "Agent:           invalid configuration" in out
        assert "invalid-config-json" in out
        assert "Diagnostic fallback agent: generic" in out
        assert "agent-config-invalid:invalid-config-json" in out
        assert "skills install" not in out
        assert " --skills" not in out

    def test_multiple_config_homes_require_intent_reconciliation_before_repair(
        self, tmp_project, capsys
    ):
        wiki = tmp_project / "docs/llm_wiki"
        wiki.mkdir(parents=True, exist_ok=True)
        (tmp_project / ".git/.llm-wiki-agent").write_text(
            '{"agent":"generic","reference_skill":true}',
            encoding="utf-8",
        )
        (wiki / ".llm-wiki-agent").write_text(
            '{"agent":"claude","reference_skill":false}',
            encoding="utf-8",
        )

        status_cmd.run(_make_args())

        out = capsys.readouterr().out
        assert "multiple-agent-config-homes" in out
        assert ".git/.llm-wiki-agent" in out
        assert "docs/llm_wiki/.llm-wiki-agent" in out
        assert "inspect and preserve both local agent configs" in out
        assert "skills install" not in out
        assert " --skills" not in out

    def test_missing_target_detects_managed_schema_from_interrupted_switch(
        self, tmp_project, capsys
    ):
        _write_agent_config(
            tmp_project,
            agent="claude",
            rendered_profile="compact",
            render_profile_version=1,
            render_reason="reference-current",
        )
        _write_profiled_schema(tmp_project / "AGENTS.md", "expanded_inline")

        status_cmd.run(_make_args())

        out = capsys.readouterr().out
        assert "Managed schema:  CLAUDE.md" in out
        assert "Managed lifecycle: missing-schema" in out
        assert "Switch state:    interrupted-agent-switch" in out
        assert "managed schema remains at AGENTS.md" in out
        assert "Reference path:  .claude/skills/wiki-reference" in out
        assert (
            "llm-wiki upgrade --wiki-dir docs/llm_wiki --agent claude --skills" in out
        )
