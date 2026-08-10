from __future__ import annotations

from pathlib import Path

import pytest

from llm_wiki_cli.services.rendering_lifecycle import (
    ManagedLifecycleState,
    RenderReason,
    classify_lifecycle_status,
    reference_recovery_command,
    select_render_profile,
)
from llm_wiki_cli.services.schema import (
    ManagedSchemaBlock,
    ManagedSchemaBlockState,
    SchemaRenderProfile,
)
from llm_wiki_cli.services.skills import (
    ReferenceSkillReason,
    ReferenceSkillState,
    ReferenceSkillVerification,
)


def _reference(state: ReferenceSkillState) -> ReferenceSkillVerification:
    reason = {
        ReferenceSkillState.ABSENT: ReferenceSkillReason.ABSENT,
        ReferenceSkillState.CURRENT: ReferenceSkillReason.CURRENT,
        ReferenceSkillState.LOCALLY_MODIFIED: ReferenceSkillReason.LOCALLY_MODIFIED,
        ReferenceSkillState.INCOMPLETE: ReferenceSkillReason.INCOMPLETE,
        ReferenceSkillState.PACKAGE_MISSING: ReferenceSkillReason.PACKAGE_MISSING,
        ReferenceSkillState.INSTALL_ERROR: ReferenceSkillReason.INSTALL_ERROR,
    }[state]
    return ReferenceSkillVerification(
        state=state,
        reason=reason,
        path=Path(".llm-wiki/skills/wiki-reference"),
    )


@pytest.mark.parametrize("state", list(ReferenceSkillState))
def test_profile_selection_requires_enabled_current_reference(
    state: ReferenceSkillState,
) -> None:
    enabled = select_render_profile(
        reference_enabled=True,
        reference_state=state,
    )
    if state is ReferenceSkillState.CURRENT:
        assert enabled.profile is SchemaRenderProfile.COMPACT
        assert enabled.reason is RenderReason.REFERENCE_CURRENT
    else:
        assert enabled.profile is SchemaRenderProfile.EXPANDED_INLINE
        assert enabled.reason is not RenderReason.REFERENCE_CURRENT

    disabled = select_render_profile(
        reference_enabled=False,
        reference_state=state,
    )
    assert disabled.profile is SchemaRenderProfile.EXPANDED_INLINE
    assert disabled.reason is RenderReason.SKILLS_DISABLED


def test_recovery_is_scoped_to_exact_reference_destination() -> None:
    assert reference_recovery_command(skills_dir=".claude/skills") == (
        "llm-wiki skills install --dest .claude/skills --skill wiki-reference --force"
    )


def test_recovery_requires_manual_resolution_for_preserved_extra_entries() -> None:
    recovery = reference_recovery_command(
        skills_dir=".llm-wiki/skills",
        details=("extra:references/local.md",),
    )

    assert "inspect and back up" in recovery
    assert "move those entries aside" in recovery
    assert "--dest .llm-wiki/skills --skill wiki-reference --force" in recovery


@pytest.mark.parametrize(
    ("schema", "reference_state", "enabled", "expected"),
    [
        (
            ManagedSchemaBlock(
                ManagedSchemaBlockState.PROFILED,
                SchemaRenderProfile.COMPACT,
                1,
                "compact",
            ),
            ReferenceSkillState.CURRENT,
            True,
            ManagedLifecycleState.COMPACT_CURRENT,
        ),
        (
            ManagedSchemaBlock(
                ManagedSchemaBlockState.PROFILED,
                SchemaRenderProfile.EXPANDED_INLINE,
                1,
                "expanded_inline",
            ),
            ReferenceSkillState.ABSENT,
            False,
            ManagedLifecycleState.EXPANDED_SKILLS_DISABLED,
        ),
        (
            ManagedSchemaBlock(
                ManagedSchemaBlockState.PROFILED,
                SchemaRenderProfile.EXPANDED_INLINE,
                1,
                "expanded_inline",
            ),
            ReferenceSkillState.INCOMPLETE,
            True,
            ManagedLifecycleState.EXPANDED_REFERENCE_UNAVAILABLE,
        ),
        (
            ManagedSchemaBlock(
                ManagedSchemaBlockState.LEGACY_EXPANDED_INLINE,
            ),
            ReferenceSkillState.CURRENT,
            True,
            ManagedLifecycleState.LEGACY_EXPANDED,
        ),
        (
            ManagedSchemaBlock(ManagedSchemaBlockState.ABSENT),
            ReferenceSkillState.CURRENT,
            True,
            ManagedLifecycleState.MISSING_SCHEMA,
        ),
    ],
)
def test_live_status_cross_product(
    schema: ManagedSchemaBlock,
    reference_state: ReferenceSkillState,
    enabled: bool,
    expected: ManagedLifecycleState,
) -> None:
    status = classify_lifecycle_status(
        schema=schema,
        reference=_reference(reference_state),
        reference_enabled=enabled,
        skills_dir=".llm-wiki/skills",
    )

    assert status.state is expected
    assert status.reference_current is (reference_state is ReferenceSkillState.CURRENT)
    assert status.read_only_knowledge == "independent"


@pytest.mark.parametrize(
    "reference_state",
    [
        state
        for state in ReferenceSkillState
        if state is not ReferenceSkillState.CURRENT
    ],
)
def test_compact_with_noncurrent_reference_is_broken(
    reference_state: ReferenceSkillState,
) -> None:
    status = classify_lifecycle_status(
        schema=ManagedSchemaBlock(
            ManagedSchemaBlockState.PROFILED,
            SchemaRenderProfile.COMPACT,
            1,
            "compact",
        ),
        reference=_reference(reference_state),
        reference_enabled=True,
        skills_dir=".llm-wiki/skills",
    )

    assert status.state is ManagedLifecycleState.COMPACT_BROKEN
    assert status.warning
    assert status.recovery_command == (
        "llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} --skills"
    )


def test_compact_current_reference_with_disabled_intent_is_broken() -> None:
    status = classify_lifecycle_status(
        schema=ManagedSchemaBlock(
            ManagedSchemaBlockState.PROFILED,
            SchemaRenderProfile.COMPACT,
            1,
            "compact",
        ),
        reference=_reference(ReferenceSkillState.CURRENT),
        reference_enabled=False,
        skills_dir=".llm-wiki/skills",
    )

    assert status.state is ManagedLifecycleState.COMPACT_BROKEN
    assert status.warning == "compact-profile-with-managed-reference-disabled"
    assert status.recovery_command == (
        "llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} --no-skills"
    )


def test_live_files_override_stale_persisted_profile() -> None:
    status = classify_lifecycle_status(
        schema=ManagedSchemaBlock(
            ManagedSchemaBlockState.PROFILED,
            SchemaRenderProfile.COMPACT,
            1,
            "compact",
        ),
        reference=_reference(ReferenceSkillState.CURRENT),
        reference_enabled=True,
        skills_dir=".llm-wiki/skills",
        configured_profile="expanded_inline",
        configured_reason="reference-absent",
    )

    assert status.state is ManagedLifecycleState.COMPACT_CURRENT
    assert status.config_mismatch is True
    assert "persisted-render-state" in str(status.warning)


@pytest.mark.parametrize(
    ("profile", "enabled"),
    [
        (SchemaRenderProfile.EXPANDED_INLINE, False),
        (SchemaRenderProfile.COMPACT, True),
    ],
)
def test_historical_install_error_is_only_valid_for_enabled_expanded_fallback(
    profile: SchemaRenderProfile,
    enabled: bool,
) -> None:
    status = classify_lifecycle_status(
        schema=ManagedSchemaBlock(
            ManagedSchemaBlockState.PROFILED,
            profile,
            1,
            profile.value,
        ),
        reference=_reference(ReferenceSkillState.CURRENT),
        reference_enabled=enabled,
        skills_dir=".llm-wiki/skills",
        configured_profile=profile.value,
        configured_reason="install-error",
    )

    assert status.config_mismatch is True
    assert "persisted-render-state" in str(status.warning)


def test_enabled_expanded_install_error_remains_valid_historical_evidence() -> None:
    status = classify_lifecycle_status(
        schema=ManagedSchemaBlock(
            ManagedSchemaBlockState.PROFILED,
            SchemaRenderProfile.EXPANDED_INLINE,
            1,
            "expanded_inline",
        ),
        reference=_reference(ReferenceSkillState.ABSENT),
        reference_enabled=True,
        skills_dir=".llm-wiki/skills",
        configured_profile="expanded_inline",
        configured_reason="install-error",
    )

    assert status.config_mismatch is False
