"""Profile selection and live managed-schema lifecycle classification.

This module is deliberately free of filesystem mutation.  Commands provision
and verify the managed reference first, then use these helpers to choose a
render profile or explain the live schema/reference combination.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .schema import (
    SCHEMA_BLOCK_VERSION,
    ManagedSchemaBlock,
    ManagedSchemaBlockState,
    SchemaRenderProfile,
)
from .skills import ReferenceSkillState, ReferenceSkillVerification


class RenderReason(str, Enum):
    """Stable reasons persisted alongside the last rendered profile."""

    REFERENCE_CURRENT = "reference-current"
    SKILLS_DISABLED = "skills-disabled"
    REFERENCE_ABSENT = "reference-absent"
    REFERENCE_MODIFIED = "reference-modified"
    REFERENCE_INCOMPLETE = "reference-incomplete"
    PACKAGE_MISSING = "package-missing"
    INSTALL_ERROR = "install-error"


class ManagedLifecycleState(str, Enum):
    """Stable live combinations reported by ``llm-wiki status``."""

    COMPACT_CURRENT = "compact/current"
    EXPANDED_SKILLS_DISABLED = "expanded/skills-disabled"
    EXPANDED_REFERENCE_UNAVAILABLE = "expanded/reference-unavailable"
    EXPANDED_REFERENCE_CURRENT = "expanded/reference-current"
    LEGACY_EXPANDED = "legacy-expanded"
    COMPACT_BROKEN = "compact/broken"
    MISSING_SCHEMA = "missing-schema"
    UNSUPPORTED_SCHEMA = "unsupported-schema"
    MALFORMED_SCHEMA = "malformed-schema"


@dataclass(frozen=True)
class RenderDecision:
    """One deterministic profile choice from intent and verified state."""

    profile: SchemaRenderProfile
    reason: RenderReason

    @property
    def version(self) -> int:
        """Return the managed marker version persisted with this decision."""

        return SCHEMA_BLOCK_VERSION


@dataclass(frozen=True)
class LifecycleStatus:
    """Live status fields required by the managed lifecycle contract."""

    state: ManagedLifecycleState
    rendered_profile: str
    reference_state: str
    reference_path: str
    reference_current: bool
    read_only_knowledge: str
    warning: str | None
    recovery_command: str | None
    config_mismatch: bool = False

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic machine-friendly representation."""

        return {
            "state": self.state.value,
            "rendered_profile": self.rendered_profile,
            "reference_state": self.reference_state,
            "reference_path": self.reference_path,
            "reference_current": self.reference_current,
            "read_only_knowledge": self.read_only_knowledge,
            "warning": self.warning,
            "recovery_command": self.recovery_command,
            "config_mismatch": self.config_mismatch,
        }


_STATE_REASON: dict[ReferenceSkillState, RenderReason] = {
    ReferenceSkillState.ABSENT: RenderReason.REFERENCE_ABSENT,
    ReferenceSkillState.CURRENT: RenderReason.REFERENCE_CURRENT,
    ReferenceSkillState.LOCALLY_MODIFIED: RenderReason.REFERENCE_MODIFIED,
    ReferenceSkillState.INCOMPLETE: RenderReason.REFERENCE_INCOMPLETE,
    ReferenceSkillState.PACKAGE_MISSING: RenderReason.PACKAGE_MISSING,
    ReferenceSkillState.INSTALL_ERROR: RenderReason.INSTALL_ERROR,
}


def select_render_profile(
    *,
    reference_enabled: bool,
    reference_state: ReferenceSkillState,
) -> RenderDecision:
    """Choose compact only for an enabled, verified-current reference."""

    if type(reference_enabled) is not bool:
        raise TypeError("reference_enabled must be a bool")
    if not isinstance(reference_state, ReferenceSkillState):
        raise TypeError("reference_state must be a ReferenceSkillState")
    if not reference_enabled:
        return RenderDecision(
            SchemaRenderProfile.EXPANDED_INLINE,
            RenderReason.SKILLS_DISABLED,
        )
    if reference_state is ReferenceSkillState.CURRENT:
        return RenderDecision(
            SchemaRenderProfile.COMPACT,
            RenderReason.REFERENCE_CURRENT,
        )
    return RenderDecision(
        SchemaRenderProfile.EXPANDED_INLINE, _STATE_REASON[reference_state]
    )


def reference_recovery_command(
    *,
    skills_dir: str,
    details: tuple[str, ...] = (),
) -> str:
    """Return a state-aware, authority-bounded managed-reference recovery."""

    if not isinstance(skills_dir, str) or not skills_dir:
        raise ValueError("skills_dir must be a non-empty string")
    command = (
        f"llm-wiki skills install --dest {skills_dir} --skill wiki-reference --force"
    )
    repairable_prefixes = ("missing:", "missing_directory:")
    if details and not all(
        detail.startswith(repairable_prefixes) for detail in details
    ):
        return (
            "inspect and back up preserved extra, conflicting, unsafe, or "
            f"unreadable entries in {skills_dir}/wiki-reference; move those "
            f"entries aside or remove them if intended, then run `{command}`"
        )
    return command


def classify_lifecycle_status(
    *,
    schema: ManagedSchemaBlock,
    reference: ReferenceSkillVerification,
    reference_enabled: bool,
    skills_dir: str,
    configured_profile: object = None,
    configured_reason: object = None,
) -> LifecycleStatus:
    """Combine live marker/reference state; config is mismatch evidence only."""

    if not isinstance(schema, ManagedSchemaBlock):
        raise TypeError("schema must be a ManagedSchemaBlock")
    if not isinstance(reference, ReferenceSkillVerification):
        raise TypeError("reference must be a ReferenceSkillVerification")
    if type(reference_enabled) is not bool:
        raise TypeError("reference_enabled must be a bool")

    if not isinstance(skills_dir, str) or not skills_dir:
        raise ValueError("skills_dir must be a non-empty string")
    upgrade_recovery = "llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} " + (
        "--skills" if reference_enabled else "--no-skills"
    )
    reference_state = reference.state.value
    reference_path = reference.path.as_posix()
    current = reference.current

    if schema.state is ManagedSchemaBlockState.ABSENT:
        state = ManagedLifecycleState.MISSING_SCHEMA
        rendered = "not-rendered"
        warning = "managed-schema-absent"
        recovery_command = "llm-wiki init --wiki-dir {wiki_dir} --agent {agent}"
        if not reference_enabled:
            recovery_command += " --no-skills"
    elif schema.state is ManagedSchemaBlockState.LEGACY_EXPANDED_INLINE:
        state = ManagedLifecycleState.LEGACY_EXPANDED
        rendered = SchemaRenderProfile.EXPANDED_INLINE.value
        warning = "managed-schema-profile-marker-absent"
        recovery_command = upgrade_recovery
    elif schema.state in {
        ManagedSchemaBlockState.UNSUPPORTED_VERSION,
        ManagedSchemaBlockState.UNSUPPORTED_PROFILE,
    }:
        state = ManagedLifecycleState.UNSUPPORTED_SCHEMA
        rendered = "unknown"
        warning = "managed-schema-profile-unsupported"
        recovery_command = upgrade_recovery
    elif schema.state is ManagedSchemaBlockState.MALFORMED:
        state = ManagedLifecycleState.MALFORMED_SCHEMA
        rendered = "unknown"
        warning = "managed-schema-profile-malformed"
        recovery_command = (
            "repair-or-move-aside-malformed-managed-markers; then " + upgrade_recovery
        )
    elif (
        schema.profile is SchemaRenderProfile.COMPACT and current and reference_enabled
    ):
        state = ManagedLifecycleState.COMPACT_CURRENT
        rendered = SchemaRenderProfile.COMPACT.value
        warning = None
        recovery_command = None
    elif schema.profile is SchemaRenderProfile.COMPACT:
        state = ManagedLifecycleState.COMPACT_BROKEN
        rendered = SchemaRenderProfile.COMPACT.value
        warning = (
            "compact-profile-with-managed-reference-disabled"
            if not reference_enabled
            else f"compact-profile-with-{reference.reason.value}"
        )
        recovery_command = upgrade_recovery
    elif not reference_enabled:
        state = ManagedLifecycleState.EXPANDED_SKILLS_DISABLED
        rendered = SchemaRenderProfile.EXPANDED_INLINE.value
        warning = "managed-reference-disabled"
        recovery_command = (
            "llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} --skills"
        )
    elif current:
        state = ManagedLifecycleState.EXPANDED_REFERENCE_CURRENT
        rendered = SchemaRenderProfile.EXPANDED_INLINE.value
        warning = "expanded-profile-with-current-reference"
        recovery_command = upgrade_recovery
    else:
        state = ManagedLifecycleState.EXPANDED_REFERENCE_UNAVAILABLE
        rendered = SchemaRenderProfile.EXPANDED_INLINE.value
        warning = reference.reason.value
        recovery_command = upgrade_recovery

    expected_reason = (
        RenderReason.SKILLS_DISABLED.value
        if not reference_enabled
        else _STATE_REASON[reference.state].value
    )
    reason_mismatch = (
        configured_reason is not None
        and configured_reason != expected_reason
        # An install failure is historical attempt evidence. A later read-only
        # verifier can observe only the resulting static tree, not recreate that
        # operation outcome.  It is compatible only with the enabled-reference
        # expanded fallback that an installation failure actually renders.
        and not (
            configured_reason == RenderReason.INSTALL_ERROR.value
            and reference_enabled
            and rendered == SchemaRenderProfile.EXPANDED_INLINE.value
        )
    )
    config_mismatch = (
        configured_profile is not None and configured_profile != rendered
    ) or reason_mismatch
    if config_mismatch:
        mismatch = "persisted-render-state-does-not-match-live-files"
        warning = f"{warning}; {mismatch}" if warning else mismatch
        if recovery_command is None:
            recovery_command = upgrade_recovery

    return LifecycleStatus(
        state=state,
        rendered_profile=rendered,
        reference_state=reference_state,
        reference_path=reference_path,
        reference_current=current,
        read_only_knowledge="independent",
        warning=warning,
        recovery_command=recovery_command,
        config_mismatch=config_mismatch,
    )
