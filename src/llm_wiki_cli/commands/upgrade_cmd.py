"""llm-wiki upgrade — refresh all framework-managed artifacts in place.

Replaces the uninstall → init → install-hook cycle with a single idempotent
command that:
1. Replaces the agent constraint block with the latest version
2. Ensures wiki directory structure is complete
3. Reinstalls git hooks
4. Optionally switches agents
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..config import (
    AGENT_CHOICES,
    AgentConfigInspection,
    AgentConfigState,
    CLI_AGENTS,
    DEFAULT_WIKI_DIR,
    PathValidationError,
    config_requires_manual_recovery,
    get_agent_config_path,
    inspect_config,
    require_committed_config,
    require_config_inspection_unchanged,
    require_safe_config_path,
    validate_path,
    write_config,
)
from ..services.filesystem_guard import (
    atomic_write_guarded_bytes,
    ensure_guarded_directory,
    guarded_tree_manifest,
    remove_guarded_tree,
    unlink_guarded_bytes,
    windows_object_identity,
)
from ..services.knowledge_evidence import formatted_json_bytes
from ..services.rendering_lifecycle import (
    reference_recovery_command,
    select_render_profile,
)
from ..services.schema import (
    SCHEMA_FILENAMES,
    ManagedSchemaBlockError,
    ManagedSchemaBlockState,
    ManagedSchemaPathError,
    SchemaRenderProfile,
    build_schema_content,
    build_upgraded_schema_content,
    classify_managed_schema_block,
    installed_skill_block_contents,
    require_managed_schema_profile,
    require_replaceable_managed_schema,
    require_safe_schema_path,
    strip_wiki_block,
)
from ..services.skills import (
    REFERENCE_SKILL_ID,
    ReferenceSkillState,
    _provision_reference_skill_guarded as provision_reference_skill,
    skills_install_dir,
    verify_reference_skill,
)
from ..services.source_selection import (
    SourceSelectionError,
    resolve_source_selection,
)
from ..services.wiki_lifecycle import (
    WikiScaffoldPathError,
    provision_wiki_scaffold,
    require_safe_wiki_scaffold,
)

# Re-use hook builders from hook_cmd to avoid duplication
from .hook_cmd import (
    _build_ide_post_commit,
    _build_validation_pre_commit,
    _install_hook,
    is_managed_hook_content,
    require_hook_installable,
    require_safe_hook_arguments,
    require_safe_hook_paths,
)


@dataclass(frozen=True)
class StructureUpgradeResult:
    """Paths created while refreshing the framework-owned wiki structure."""

    directories: tuple[str, ...]
    gitkeeps: tuple[str, ...]
    files: tuple[str, ...]

    @property
    def created_count(self) -> int:
        return len(self.directories) + len(self.gitkeeps) + len(self.files)


@dataclass(frozen=True)
class SchemaCleanupReceipt:
    """Reversible source-schema mutation held until cleanup is committed."""

    path: Path
    before: bytes
    after: bytes | None


@dataclass(frozen=True)
class ReferenceCleanupOutcome:
    """Whether source-reference cleanup completed and schema must roll back."""

    complete: bool
    restore_schema: bool = False
    authority_changed: bool = False


@dataclass(frozen=True)
class SourceCleanupOutcome:
    """Result of one recorded-source cleanup transaction."""

    complete: bool
    authority_changed: bool = False


def _decode_schema_bytes(data: bytes) -> str:
    """Decode one immutable schema snapshot using the shared Markdown policy."""

    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        content = data.decode("cp1252")
    return content.replace("\r\n", "\n").replace("\r", "\n")


def _require_replaceable_schema_path(
    path: str | Path,
) -> tuple[Path, str, bytes | None]:
    """Read one coherent schema snapshot and preflight its managed markers."""

    safe_path = require_safe_schema_path(path)
    try:
        raw_bytes = safe_path.read_bytes() if safe_path.exists() else None
        content = _decode_schema_bytes(raw_bytes) if raw_bytes is not None else ""
    except (OSError, UnicodeError) as exc:
        raise ManagedSchemaPathError(
            f"managed schema path is unreadable: {safe_path}"
        ) from exc
    try:
        require_replaceable_managed_schema(content)
    except ManagedSchemaBlockError as exc:
        raise ManagedSchemaBlockError(f"{safe_path}: {exc}") from exc
    return safe_path, content, raw_bytes


def _resolve_agent(
    args,
    wiki_dir: str,
    inspection: AgentConfigInspection | None = None,
) -> str:
    """Resolve agent: CLI --agent flag > persisted config > error."""
    agent = getattr(args, "agent", None)
    if agent:
        return agent

    snapshot = inspection if inspection is not None else inspect_config(wiki_dir)
    if snapshot.state is AgentConfigState.INVALID:
        print(
            f"Error: local agent config is invalid ({snapshot.reason}).\n"
            "  Pass --agent explicitly to repair it without guessing.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    stored_value = snapshot.data.get("agent")
    stored = (
        str(stored_value)
        if snapshot.state in {AgentConfigState.VALID, AgentConfigState.LEGACY}
        and isinstance(stored_value, str)
        else None
    )
    if stored:
        return stored

    print(
        "Error: Cannot determine agent.\n"
        f"  No --agent flag provided and no config found at .git/.llm-wiki-agent\n\n"
        "  Either run `llm-wiki init --agent <agent>` first,\n"
        "  or pass --agent to this command:\n"
        f"    llm-wiki upgrade --agent <{'|'.join(AGENT_CHOICES)}>",
        file=sys.stderr,
    )
    sys.exit(1)


def _upgrade_schema(
    agent: str,
    wiki_dir: str,
    *,
    render_profile: SchemaRenderProfile,
    quality_hints: bool = True,
    issue_reporting: bool = False,
    source_selection: str | Path | None = None,
) -> tuple[str, bytes | None]:
    """Atomically write the target schema without cleaning any source path."""
    new_content = build_schema_content(
        agent,
        wiki_dir,
        render_profile=render_profile,
        quality_hints=quality_hints,
        issue_reporting=issue_reporting,
        source_selection=source_selection,
    )
    new_filename = SCHEMA_FILENAMES.get(agent)

    if new_filename:
        schema_candidate = Path(new_filename)
        schema_absolute = (
            schema_candidate
            if schema_candidate.is_absolute()
            else Path.cwd().resolve() / schema_candidate
        )
        ensure_guarded_directory(schema_absolute.parent)
        schema_path, existing, existing_bytes = _require_replaceable_schema_path(
            new_filename
        )
        blocks = installed_skill_block_contents()
        schema_path, _current, current_bytes = _require_replaceable_schema_path(
            new_filename
        )
        if current_bytes != existing_bytes:
            raise ManagedSchemaPathError(
                f"managed schema changed while staging plugin blocks: {schema_path}"
            )
        updated, _refreshed = build_upgraded_schema_content(
            existing,
            new_content,
            blocks,
        )
        require_managed_schema_profile(updated, render_profile)
        updated_bytes = updated.encode("utf-8")
        atomic_write_guarded_bytes(
            schema_absolute,
            updated_bytes,
            mode=0o644,
            require_single_link=False,
            expected_existing=existing_bytes,
        )
        require_safe_schema_path(schema_path)
        return new_filename, updated_bytes
    return "(no schema file)", None


def _clean_old_schema(
    old_agent: str | None,
    new_agent: str,
    *,
    pre_mutation_check: Callable[[], None] | None = None,
) -> SchemaCleanupReceipt | None:
    """Clean the source schema and return a receipt for guarded rollback."""

    if not old_agent or old_agent == new_agent:
        return None
    old_filename = SCHEMA_FILENAMES.get(old_agent)
    new_filename = SCHEMA_FILENAMES.get(new_agent)
    if not old_filename or old_filename == new_filename:
        return None
    old_path, existing, existing_bytes = _require_replaceable_schema_path(old_filename)
    if existing_bytes is None:
        return None
    block = classify_managed_schema_block(existing)
    if block.state is ManagedSchemaBlockState.ABSENT:
        return None
    stripped = strip_wiki_block(existing)
    if (
        classify_managed_schema_block(stripped).state
        is not ManagedSchemaBlockState.ABSENT
    ):
        raise ManagedSchemaBlockError(
            f"managed schema cleanup did not remove one complete block from {old_filename}"
        )
    old_absolute = (
        old_path if old_path.is_absolute() else Path.cwd().resolve() / old_path
    )
    try:
        require_safe_schema_path(old_path)
        if pre_mutation_check is not None:
            pre_mutation_check()
        if stripped:
            stripped_bytes = stripped.encode("utf-8")
            atomic_write_guarded_bytes(
                old_absolute,
                stripped_bytes,
                mode=0o644,
                require_single_link=False,
                expected_existing=existing_bytes,
            )
            print(f"  Cleaned constraint block from: {old_filename}")
            return SchemaCleanupReceipt(
                path=old_absolute,
                before=existing_bytes,
                after=stripped_bytes,
            )
        else:
            unlink_guarded_bytes(old_absolute, expected=existing_bytes)
            print(f"  Removed: {old_filename} (only contained wiki constraints)")
            return SchemaCleanupReceipt(
                path=old_absolute,
                before=existing_bytes,
                after=None,
            )
    except OSError as exc:
        raise ManagedSchemaPathError(
            f"managed schema changed or could not be cleaned safely: {old_path}"
        ) from exc


def _restore_old_schema(receipt: SchemaCleanupReceipt | None) -> None:
    """Restore an already-cleaned source schema without overwriting new bytes."""

    if receipt is None:
        return
    try:
        atomic_write_guarded_bytes(
            receipt.path,
            receipt.before,
            mode=0o644,
            require_single_link=False,
            expected_existing=receipt.after,
        )
    except OSError as exc:
        raise ManagedSchemaPathError(
            "source schema could not be restored after lifecycle authority changed: "
            f"{receipt.path}"
        ) from exc
    print(f"  Restored source schema after lifecycle authority changed: {receipt.path}")


def _preflight_cleanup_agent(source_agent: str | None, active_agent: str) -> None:
    """Reject an unsafe or malformed recorded switch source before mutation."""

    if not source_agent or source_agent == active_agent:
        return
    source_filename = SCHEMA_FILENAMES.get(source_agent)
    target_filename = SCHEMA_FILENAMES.get(active_agent)
    if not source_filename or source_filename == target_filename:
        return
    source_path = Path(source_filename)
    _require_replaceable_schema_path(source_path)


def _target_cleanup_is_ready(
    agent: str,
    *,
    target_profile: SchemaRenderProfile,
    target_schema_bytes: bytes | None,
    require_target_reference: bool,
) -> bool:
    """Revalidate the committed target immediately before source destruction."""

    reference_ready = bool(
        not require_target_reference
        or verify_reference_skill(agent=agent).state is ReferenceSkillState.CURRENT
    )
    filename = SCHEMA_FILENAMES.get(agent)
    try:
        if filename is None:
            schema_ready = target_schema_bytes is None
        else:
            _path, content, current_bytes = _require_replaceable_schema_path(filename)
            block = classify_managed_schema_block(content)
            schema_ready = bool(
                current_bytes is not None
                and current_bytes == target_schema_bytes
                and block.state is ManagedSchemaBlockState.PROFILED
                and block.profile is target_profile
            )
    except (ManagedSchemaBlockError, ManagedSchemaPathError, OSError):
        schema_ready = False
    if not schema_ready or not reference_ready:
        print(
            "  Warning: the committed target schema or managed reference changed "
            "before lifecycle completion"
        )
        return False
    return True


def _cleanup_config_is_current(wiki_dir: str, committed_config: dict) -> bool:
    """Keep destructive cleanup bound to the exact pending config commit."""

    try:
        require_committed_config(wiki_dir, committed_config)
    except PathValidationError as exc:
        print(
            "  Warning: local agent config changed before source cleanup; "
            f"preserved recorded source artifacts ({exc})"
        )
        return False
    return True


def _cleanup_recorded_source(
    active_agent: str,
    source_agent: str | None,
    *,
    wiki_dir: str,
    committed_config: dict,
    remove_references: bool,
    target_profile: SchemaRenderProfile,
    target_schema_bytes: bytes | None,
    require_target_reference: bool,
) -> SourceCleanupOutcome:
    """Clean only the source explicitly recorded by the switch transaction."""

    if not source_agent or source_agent == active_agent:
        return SourceCleanupOutcome(True)
    if not _target_cleanup_is_ready(
        active_agent,
        target_profile=target_profile,
        target_schema_bytes=target_schema_bytes,
        require_target_reference=require_target_reference,
    ):
        return SourceCleanupOutcome(False)
    if not _cleanup_config_is_current(wiki_dir, committed_config):
        return SourceCleanupOutcome(False, authority_changed=True)

    def config_guard() -> None:
        require_committed_config(wiki_dir, committed_config)

    try:
        schema_receipt = _clean_old_schema(
            source_agent,
            active_agent,
            pre_mutation_check=config_guard,
        )
    except PathValidationError:
        return SourceCleanupOutcome(False, authority_changed=True)
    if not _target_cleanup_is_ready(
        active_agent,
        target_profile=target_profile,
        target_schema_bytes=target_schema_bytes,
        require_target_reference=require_target_reference,
    ):
        _restore_old_schema(schema_receipt)
        return SourceCleanupOutcome(False)
    if not _cleanup_config_is_current(wiki_dir, committed_config):
        _restore_old_schema(schema_receipt)
        return SourceCleanupOutcome(False, authority_changed=True)
    if remove_references:
        reference_outcome = _migrate_reference_skill(
            source_agent,
            active_agent,
            target_current=True,
            target_profile=target_profile,
            target_schema_bytes=target_schema_bytes,
            pre_mutation_check=config_guard,
        )
        if reference_outcome.restore_schema:
            _restore_old_schema(schema_receipt)
        return SourceCleanupOutcome(
            reference_outcome.complete,
            authority_changed=reference_outcome.authority_changed,
        )
    return SourceCleanupOutcome(True)


def _migrate_reference_skill(
    old_agent: str | None,
    new_agent: str,
    *,
    target_current: bool,
    target_profile: SchemaRenderProfile,
    target_schema_bytes: bytes | None,
    pre_mutation_check: Callable[[], None] | None = None,
) -> ReferenceCleanupOutcome:
    """Remove only a verified-current source after a usable target commit."""

    if not target_current:
        return ReferenceCleanupOutcome(False, restore_schema=True)
    try:
        if pre_mutation_check is not None:
            pre_mutation_check()
    except PathValidationError:
        return ReferenceCleanupOutcome(
            False,
            restore_schema=True,
            authority_changed=True,
        )
    if not _target_cleanup_is_ready(
        new_agent,
        target_profile=target_profile,
        target_schema_bytes=target_schema_bytes,
        require_target_reference=True,
    ):
        return ReferenceCleanupOutcome(False, restore_schema=True)
    old_dir = skills_install_dir(old_agent)
    if old_dir == skills_install_dir(new_agent):
        return ReferenceCleanupOutcome(True)
    verification = verify_reference_skill(target=old_dir)
    if verification.state is ReferenceSkillState.CURRENT:
        try:
            metadata = verification.path.lstat()
            identity = windows_object_identity(
                metadata,
                context=str(verification.path),
            )
            absolute = (
                verification.path
                if verification.path.is_absolute()
                else Path.cwd().resolve() / verification.path
            )
            manifest = guarded_tree_manifest(absolute)
            confirmed = verify_reference_skill(target=old_dir)
            if confirmed.state is not ReferenceSkillState.CURRENT:
                print(
                    f"  Kept {REFERENCE_SKILL_ID} skill in {old_dir}/ "
                    "(source tree changed after verification)"
                )
                return ReferenceCleanupOutcome(False)
            if not _target_cleanup_is_ready(
                new_agent,
                target_profile=target_profile,
                target_schema_bytes=target_schema_bytes,
                require_target_reference=True,
            ):
                print(
                    f"  Kept {REFERENCE_SKILL_ID} skill in {old_dir}/ "
                    "(target changed before source removal)"
                )
                return ReferenceCleanupOutcome(
                    False,
                    restore_schema=True,
                )
            try:
                if pre_mutation_check is not None:
                    pre_mutation_check()
            except PathValidationError:
                print(
                    f"  Kept {REFERENCE_SKILL_ID} skill in {old_dir}/ "
                    "(local agent config changed before source removal)"
                )
                return ReferenceCleanupOutcome(
                    False,
                    restore_schema=True,
                    authority_changed=True,
                )
            remove_guarded_tree(
                absolute,
                expected_identity=(identity.device, identity.file_id),
                expected_manifest=manifest,
            )
        except OSError as exc:
            print(
                f"  Kept {REFERENCE_SKILL_ID} skill in {old_dir}/ "
                f"(source path changed or could not be removed safely: {exc})"
            )
            return ReferenceCleanupOutcome(False)
        print(f"  Removed {REFERENCE_SKILL_ID} skill from {old_dir}/ (relocating)")
        return ReferenceCleanupOutcome(True)
    if verification.state in {
        ReferenceSkillState.ABSENT,
        ReferenceSkillState.PACKAGE_MISSING,
    } and not (verification.path.exists() or verification.path.is_symlink()):
        return ReferenceCleanupOutcome(True)
    if verification.state not in {
        ReferenceSkillState.ABSENT,
        ReferenceSkillState.PACKAGE_MISSING,
    }:
        print(
            f"  Kept {REFERENCE_SKILL_ID} skill in {old_dir}/ "
            f"({verification.state.value} — remove manually if unwanted)"
        )
    return ReferenceCleanupOutcome(False)


def _upgrade_dirs(wiki_dir: str) -> StructureUpgradeResult:
    """Ensure all standard wiki subdirectories and tracking files exist."""
    provisioned = provision_wiki_scaffold(wiki_dir)
    return StructureUpgradeResult(
        directories=provisioned.directories,
        gitkeeps=provisioned.gitkeeps,
        files=provisioned.files,
    )


def _upgrade_hooks(
    agent: str,
    wiki_dir: str,
    *,
    force: bool = False,
    source_selection: str | Path | None = None,
    post_commit_before: bytes | None,
    validation_before: bytes | None,
    refresh_validation: bool,
) -> None:
    """Reinstall git hooks for the resolved agent."""
    git_dir = Path(".git")
    if not git_dir.exists():
        print("  Skipped hooks (no .git directory)")
        return

    require_safe_hook_paths()
    hooks_dir = git_dir / "hooks"
    ensure_guarded_directory(Path.cwd().resolve() / hooks_dir)

    _install_hook(
        hooks_dir,
        "post-commit",
        _build_ide_post_commit(
            wiki_dir,
            source_selection=source_selection,
        ),
        force=force,
        expected_existing=post_commit_before,
    )
    if refresh_validation:
        _install_hook(
            hooks_dir,
            "pre-commit",
            _build_validation_pre_commit(
                wiki_dir,
                source_selection=source_selection,
            ),
            force=True,
            expected_existing=validation_before,
        )
    print(f"  Hooks: prompt-generation mode ({agent})")


def run(args):
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")
    try:
        require_safe_wiki_scaffold(wiki_dir)
        require_safe_config_path(wiki_dir)
    except (WikiScaffoldPathError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    # Resolve every preference from one config snapshot. Invalid state is never
    # allowed to select a target agent implicitly.
    config_inspection = inspect_config(wiki_dir)
    canonical_config_path = get_agent_config_path(wiki_dir)
    canonical_config_snapshot = (
        config_inspection.raw_bytes
        if config_inspection.path == canonical_config_path
        else None
    )
    migrated_config_path: Path | None = None
    migrated_config_bytes: bytes | None = None
    if config_inspection.path != canonical_config_path:
        if config_inspection.state is AgentConfigState.INVALID:
            print(
                "Error: alternate agent config must be inspected and repaired or "
                f"moved aside before upgrade ({config_inspection.reason}; "
                f"{config_inspection.path})",
                file=sys.stderr,
            )
            raise SystemExit(2)
        if config_inspection.state in {
            AgentConfigState.VALID,
            AgentConfigState.LEGACY,
        }:
            if config_inspection.raw_bytes is None:
                print(
                    "Error: alternate agent config has no stable read snapshot: "
                    f"{config_inspection.path}",
                    file=sys.stderr,
                )
                raise SystemExit(2)
            migrated_config_path = config_inspection.path
            migrated_config_bytes = config_inspection.raw_bytes
    stored = dict(config_inspection.data)
    if config_requires_manual_recovery(config_inspection):
        if config_inspection.reason == "multiple-agent-config-homes":
            print(
                "Error: both .git/.llm-wiki-agent and "
                f"{Path(wiki_dir) / '.llm-wiki-agent'} exist; inspect and preserve "
                "both, select the authoritative config, and move the other aside "
                "before upgrade",
                file=sys.stderr,
            )
            raise SystemExit(2)
        print(
            "Error: local agent config must be inspected and repaired or moved aside "
            f"before upgrade ({config_inspection.reason}); preserve any pending "
            "cleanup evidence and acknowledge its source explicitly after repair",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if (
        config_inspection.state is AgentConfigState.INVALID
        and config_inspection.reason == "config-path-unsafe"
    ):
        print("Error: local agent config path is unsafe", file=sys.stderr)
        raise SystemExit(2)
    requested_selection = getattr(args, "source_selection", None)
    stored_selection = stored.get("source_selection")
    if stored_selection is not None and not isinstance(stored_selection, str):
        print("Error: stored source_selection must be a string", file=sys.stderr)
        raise SystemExit(2)
    selection_override = (
        requested_selection if requested_selection is not None else stored_selection
    )
    try:
        selection_policy = resolve_source_selection(".", selection_override)
    except SourceSelectionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    source_selection = selection_policy.path if selection_policy is not None else None
    try:
        require_safe_hook_arguments(wiki_dir, source_selection)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    agent = _resolve_agent(args, wiki_dir, config_inspection)
    target_filename = SCHEMA_FILENAMES.get(agent)
    try:
        if target_filename:
            _require_replaceable_schema_path(target_filename)
        stored_pending = (
            stored.get("pending_cleanup_agent")
            if config_inspection.state is AgentConfigState.VALID
            else None
        )
        pending_cleanup_agent = (
            str(stored_pending) if isinstance(stored_pending, str) else None
        )
        stored_pending_reference = (
            stored.get("pending_cleanup_reference")
            if config_inspection.state is AgentConfigState.VALID
            else None
        )
        untrusted_pending_agent = (
            str(stored.get("pending_cleanup_agent"))
            if config_inspection.state is AgentConfigState.INVALID
            and isinstance(stored.get("pending_cleanup_agent"), str)
            else None
        )
    except (ManagedSchemaBlockError, ManagedSchemaPathError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    try:
        require_safe_hook_paths()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    hooks_dir = Path(".git/hooks")
    post_commit_before = require_hook_installable(
        hooks_dir,
        "post-commit",
        force=bool(getattr(args, "force", False)),
    )
    validation_path = hooks_dir / "pre-commit"
    if validation_path.exists():
        validation_before = validation_path.read_bytes()
        refresh_validation = is_managed_hook_content(
            "pre-commit",
            validation_before.decode("utf-8", errors="replace"),
        )
    else:
        validation_before = None
        refresh_validation = False
    stored_agent = stored.get("agent")
    old_agent = (
        str(stored_agent)
        if config_inspection.state in {AgentConfigState.VALID, AgentConfigState.LEGACY}
        and isinstance(stored_agent, str)
        else None
    )
    switching = bool(old_agent and old_agent != agent)
    explicit_cleanup_value = getattr(args, "cleanup_source_agent", None)
    explicit_cleanup_agent = (
        str(explicit_cleanup_value) if isinstance(explicit_cleanup_value, str) else None
    )
    if untrusted_pending_agent == agent:
        print(
            "Error: invalid config records the target agent as its own untrusted "
            "cleanup source; inspect the config, remove or repair the pending pair, "
            "then rerun upgrade without a same-agent cleanup flag",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if explicit_cleanup_agent == agent:
        print(
            "Error: --cleanup-source-agent must differ from the target --agent",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if untrusted_pending_agent and explicit_cleanup_agent != untrusted_pending_agent:
        print(
            "Error: invalid config contains untrusted pending cleanup evidence for "
            f"{untrusted_pending_agent}; inspect it and pass "
            f"--cleanup-source-agent {untrusted_pending_agent} explicitly",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if pending_cleanup_agent and explicit_cleanup_agent not in {
        None,
        pending_cleanup_agent,
    }:
        print(
            "Error: --cleanup-source-agent does not match the persisted pending "
            f"source {pending_cleanup_agent}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if switching and pending_cleanup_agent not in {None, old_agent}:
        print(
            "Error: a prior agent switch still has pending cleanup for "
            f"{pending_cleanup_agent}; rerun upgrade for the configured agent first",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if switching and explicit_cleanup_agent not in {None, old_agent}:
        print(
            "Error: --cleanup-source-agent must match the configured source agent "
            f"{old_agent} during a switch",
            file=sys.stderr,
        )
        raise SystemExit(2)
    cleanup_agent = (
        explicit_cleanup_agent
        or (old_agent if switching else None)
        or pending_cleanup_agent
    )
    try:
        _preflight_cleanup_agent(cleanup_agent, agent)
    except (ManagedSchemaBlockError, ManagedSchemaPathError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    cli_hints = getattr(args, "quality_hints", None)
    if cli_hints is not None:
        quality_hints = cli_hints
    else:
        quality_hints = bool(stored.get("quality_hints", True))
    cli_skills = getattr(args, "skills", None)
    if cli_skills is not None:
        reference_skill = cli_skills
    else:
        reference_skill = bool(stored.get("reference_skill", True))
    if cleanup_agent and cleanup_agent != agent:
        if pending_cleanup_agent == cleanup_agent:
            cleanup_reference_required = bool(
                reference_skill and stored_pending_reference
            )
        else:
            source_reference = verify_reference_skill(agent=cleanup_agent)
            distinct_reference_roots = skills_install_dir(
                cleanup_agent
            ) != skills_install_dir(agent)
            cleanup_reference_required = bool(
                reference_skill
                and source_reference.state is ReferenceSkillState.CURRENT
                and distinct_reference_roots
            )
            if (
                distinct_reference_roots
                and not cleanup_reference_required
                and (
                    source_reference.path.exists() or source_reference.path.is_symlink()
                )
            ):
                print(
                    f"  Kept {REFERENCE_SKILL_ID} skill in "
                    f"{source_reference.path.parent}/ "
                    f"({source_reference.state.value} — remove manually if unwanted)"
                )
    else:
        cleanup_reference_required = False
    cli_issue_reporting = getattr(args, "issue_reporting", None)
    if cli_issue_reporting is not None:
        issue_reporting = cli_issue_reporting
    else:
        issue_reporting = bool(stored.get("issue_reporting", False))

    if migrated_config_path is not None and migrated_config_bytes is not None:
        try:
            if migrated_config_path.read_bytes() != migrated_config_bytes:
                raise OSError("content changed")
        except OSError as exc:
            print(
                "Error: alternate agent config changed after inspection; rerun "
                f"upgrade after reviewing {migrated_config_path}",
                file=sys.stderr,
            )
            raise SystemExit(2) from exc

    print("LLM Wiki Upgrade")
    print("=" * 40)

    if switching:
        print(f"\n  Switching agent: {old_agent} → {agent}")
    else:
        print(f"\n  Agent: {agent}")

    # 1. Provision and verify the target before rendering it. A force refresh
    # preserves the established upgrade contract for expected regular files;
    # extras and unsafe/conflicting entries remain preserved and non-current.
    print("\n1. Agent Schema:")
    if reference_skill:
        pre_mutation_check = (
            (lambda: require_config_inspection_unchanged(wiki_dir, config_inspection))
            if cli_skills is None
            else None
        )
        try:
            provision = provision_reference_skill(
                agent=agent,
                force=True,
                pre_mutation_check=pre_mutation_check,
            )
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        reference_state = provision.state
        if provision.state is ReferenceSkillState.CURRENT:
            report = provision.report
            destination = (
                report.dest_dir if report is not None else str(provision.path.parent)
            )
            print(f"  Refreshed {REFERENCE_SKILL_ID} skill in {destination}/")
        else:
            if provision.state is ReferenceSkillState.PACKAGE_MISSING:
                recovery = "repair or update the installed llm-wiki package, then retry"
            else:
                recovery = reference_recovery_command(
                    skills_dir=skills_install_dir(agent).as_posix(),
                    details=provision.details,
                )
            print(
                f"  Warning: {REFERENCE_SKILL_ID} is {provision.state.value} "
                f"({provision.reason.value}); writing expanded inline instructions. "
                f"Recovery: {recovery}"
            )
    else:
        reference_state = verify_reference_skill(agent=agent).state
        print(
            f"  Warning: skipped {REFERENCE_SKILL_ID} skill refresh (opted out); "
            "using expanded inline instructions (managed-reference-disabled)"
        )

    decision = select_render_profile(
        reference_enabled=bool(reference_skill),
        reference_state=reference_state,
    )
    try:
        schema_file, target_schema_bytes = _upgrade_schema(
            agent,
            wiki_dir,
            render_profile=decision.profile,
            quality_hints=quality_hints,
            issue_reporting=issue_reporting,
            source_selection=source_selection,
        )
    except (ManagedSchemaBlockError, ManagedSchemaPathError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"  Updated: {schema_file}")

    # 2. Wiki directories
    print("\n2. Wiki Structure:")
    try:
        structure_result = _upgrade_dirs(wiki_dir)
    except WikiScaffoldPathError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    if structure_result.created_count:
        print(f"  Created {structure_result.created_count} new entries in {wiki_dir}/")
        for rel in structure_result.directories:
            print(f"  Created directory: {rel}")
        for rel in structure_result.gitkeeps:
            print(f"  Created .gitkeep: {rel}")
        for rel in structure_result.files:
            print(f"  Created file: {rel}")
    else:
        print(f"  All directories present in {wiki_dir}/")

    # 3. Git hooks
    print("\n3. Git Hooks:")
    _upgrade_hooks(
        agent,
        wiki_dir,
        force=getattr(args, "force", False),
        source_selection=source_selection,
        post_commit_before=post_commit_before,
        validation_before=validation_before,
        refresh_validation=refresh_validation,
    )

    # 4. Persist only after the target reference/schema/plugin composition is
    # usable. Unknown compatible config fields survive the merge.
    config: dict[str, object] = dict(stored)
    config.update(
        {
            "agent": agent,
            "quality_hints": quality_hints,
            "reference_skill": bool(reference_skill),
            "issue_reporting": issue_reporting,
            "rendered_profile": decision.profile.value,
            "render_profile_version": decision.version,
            "render_reason": decision.reason.value,
        }
    )
    if cleanup_agent and cleanup_agent != agent:
        config["pending_cleanup_agent"] = cleanup_agent
        config["pending_cleanup_reference"] = cleanup_reference_required
    else:
        config.pop("pending_cleanup_agent", None)
        config.pop("pending_cleanup_reference", None)
    if source_selection is not None:
        config["source_selection"] = source_selection
    else:
        config.pop("source_selection", None)
    committed_config_bytes = formatted_json_bytes(config)
    write_config(
        wiki_dir,
        config,
        expected_existing=canonical_config_snapshot,
    )
    if migrated_config_path is not None and migrated_config_bytes is not None:
        try:
            migrated_absolute = (
                migrated_config_path
                if migrated_config_path.is_absolute()
                else Path.cwd().resolve() / migrated_config_path
            )
            unlink_guarded_bytes(
                migrated_absolute,
                expected=migrated_config_bytes,
            )
            print(
                f"  Migrated local agent config to {canonical_config_path.as_posix()}"
            )
        except OSError as exc:
            print(
                "  Error: alternate agent config changed or could not be "
                "retired safely after the canonical commit at "
                f"{migrated_config_path}: {exc}; source cleanup was not attempted",
                file=sys.stderr,
            )
            raise SystemExit(2) from exc

    try:
        require_committed_config(wiki_dir, config)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    require_target_reference = decision.profile is SchemaRenderProfile.COMPACT
    target_state_incomplete = not _target_cleanup_is_ready(
        agent,
        target_profile=decision.profile,
        target_schema_bytes=target_schema_bytes,
        require_target_reference=require_target_reference,
    )

    # 5. Destructive source cleanup is deliberately last. A failed reference
    # refresh keeps the old procedural path even though the target has a safe
    # expanded fallback. Opt-out may clean the obsolete schema but keeps refs.
    source_cleanup_incomplete = False
    transaction_authority_changed = False
    if target_state_incomplete:
        source_cleanup_incomplete = bool(cleanup_agent and cleanup_agent != agent)
        if source_cleanup_incomplete:
            print(
                "  Warning: recorded source cleanup remains pending because the "
                "target changed after commit"
            )
    elif not reference_skill or reference_state is ReferenceSkillState.CURRENT:
        cleanup_outcome = _cleanup_recorded_source(
            agent,
            cleanup_agent,
            wiki_dir=wiki_dir,
            committed_config=config,
            remove_references=cleanup_reference_required,
            target_profile=decision.profile,
            target_schema_bytes=target_schema_bytes,
            require_target_reference=require_target_reference,
        )
        if cleanup_outcome.complete and cleanup_agent and cleanup_agent != agent:
            config.pop("pending_cleanup_agent", None)
            config.pop("pending_cleanup_reference", None)
            write_config(
                wiki_dir,
                config,
                expected_existing=committed_config_bytes,
            )
            require_committed_config(wiki_dir, config)
        elif cleanup_outcome.authority_changed:
            transaction_authority_changed = True
            source_cleanup_incomplete = True
            print(
                "  Error: local config authority changed during source cleanup; "
                "source artifacts were preserved or restored. Rerun status before "
                "retrying."
            )
        elif not cleanup_outcome.complete:
            source_cleanup_incomplete = True
            print(
                "  Warning: recorded source cleanup is incomplete; preserved the "
                "pending cleanup marker for explicit recovery"
            )
    elif cleanup_agent and cleanup_agent != agent:
        source_cleanup_incomplete = True
        print(
            "  Warning: target managed-reference refresh is not current; source "
            "cleanup remains pending and was not attempted"
        )

    if not target_state_incomplete and not _target_cleanup_is_ready(
        agent,
        target_profile=decision.profile,
        target_schema_bytes=target_schema_bytes,
        require_target_reference=require_target_reference,
    ):
        target_state_incomplete = True

    if not transaction_authority_changed:
        try:
            require_committed_config(wiki_dir, config)
        except ValueError as exc:
            transaction_authority_changed = True
            print(
                "  Error: local config authority changed before lifecycle "
                f"completion ({exc}). Rerun status before retrying."
            )

    # Warn if CLI agent executable missing
    executable = CLI_AGENTS.get(agent)
    if executable and not shutil.which(executable):
        print(
            f"\nWarning: '{executable}' not found on PATH.\n"
            f"  Manual `llm-wiki trigger-agent --agent {agent}` won't work until "
            f"'{executable}' is installed."
        )

    if transaction_authority_changed:
        print(
            "\nUpgrade stopped because local config authority changed; source "
            "cleanup was not claimed complete."
        )
        raise SystemExit(2)
    elif target_state_incomplete:
        print(
            "\nUpgrade did not reach a verified terminal target state; run status "
            "and retry explicitly."
        )
        raise SystemExit(2)
    elif source_cleanup_incomplete:
        print("\nUpgrade target is usable; source cleanup remains incomplete.")
    else:
        print("\nUpgrade complete.")
