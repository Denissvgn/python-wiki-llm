from __future__ import annotations

import shutil
import sys
from pathlib import Path

from ..config import (
    AgentConfigState,
    CLI_AGENTS,
    DEFAULT_WIKI_DIR,
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
    unlink_guarded_bytes,
)
from ..services.rendering_lifecycle import (
    reference_recovery_command,
    select_render_profile,
)
from ..services.schema import (
    CONSTRAINT_START as _CONSTRAINT_START,
    SCHEMA_FILENAMES,
    ManagedSchemaBlockError,
    ManagedSchemaBlockState,
    ManagedSchemaPathError,
    SchemaRenderProfile,
    build_schema_content as _build_schema_content,
    classify_managed_schema_block,
    decode_managed_document_bytes,
    encode_managed_document_text,
    replace_schema_block_content,
    require_managed_schema_profile,
    require_replaceable_managed_schema,
    require_safe_schema_path,
)
from ..services.source_selection import (
    SourceSelectionError,
    resolve_source_selection,
)
from ..services.skills import (
    REFERENCE_SKILL_ID,
    ReferenceSkillState,
    _provision_reference_skill_guarded as provision_reference_skill,
    list_bundled_skills,
    skills_install_dir,
    verify_reference_skill,
)
from ..services.wiki_lifecycle import (
    WikiScaffoldPathError,
    provision_wiki_scaffold,
    require_safe_wiki_scaffold,
)


# Agents that have a real CLI executable for explicit trigger-agent use.
_CLI_AGENTS = CLI_AGENTS


def _managed_schema_agents() -> tuple[str, ...]:
    """Return agents with one safely readable managed schema in the checkout."""

    managed: list[str] = []
    for agent, filename in SCHEMA_FILENAMES.items():
        path = Path(filename)
        if not path.exists() and not path.is_symlink():
            continue
        safe_path = require_safe_schema_path(path)
        try:
            content = decode_managed_document_bytes(safe_path.read_bytes())
        except (OSError, UnicodeError) as exc:
            raise ManagedSchemaPathError(
                f"managed schema path is unreadable: {safe_path}"
            ) from exc
        state = classify_managed_schema_block(content).state
        if state is ManagedSchemaBlockState.MALFORMED:
            raise ManagedSchemaBlockError(
                f"managed schema block is malformed: {safe_path}"
            )
        if state is not ManagedSchemaBlockState.ABSENT:
            managed.append(agent)
    return tuple(managed)


def run(args):
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")
    try:
        require_safe_wiki_scaffold(wiki_dir)
        require_safe_config_path(wiki_dir)
    except (WikiScaffoldPathError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
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
                f"moved aside before initialization ({config_inspection.reason}; "
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
                    f"Error: alternate agent config has no stable read snapshot: "
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
                "before initialization",
                file=sys.stderr,
            )
            raise SystemExit(2)
        print(
            "Error: local agent config must be inspected and repaired or moved aside "
            f"before initialization ({config_inspection.reason}); preserve any "
            "pending cleanup evidence and resume it with upgrade explicitly",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if config_inspection.state is AgentConfigState.INVALID:
        if isinstance(stored.get("pending_cleanup_agent"), str):
            print(
                "Error: invalid config also contains pending agent-switch cleanup "
                "evidence; inspect and repair or remove the untrusted pair when "
                "retaining that source, or use `llm-wiki upgrade --agent <target> "
                "--cleanup-source-agent <source>` for a distinct target",
                file=sys.stderr,
            )
            raise SystemExit(2)
        stored.pop("pending_cleanup_agent", None)
        stored.pop("pending_cleanup_reference", None)
    elif config_inspection.state is AgentConfigState.VALID and isinstance(
        stored.get("pending_cleanup_agent"), str
    ):
        print(
            "Error: an agent switch still has pending source cleanup; run "
            "`llm-wiki upgrade` to resume it before re-initializing",
            file=sys.stderr,
        )
        raise SystemExit(2)
    requested_agent = getattr(args, "agent", None)
    if (
        config_inspection.state is AgentConfigState.INVALID
        and config_inspection.reason == "config-path-unsafe"
    ):
        print("Error: local agent config path is unsafe", file=sys.stderr)
        raise SystemExit(2)
    if config_inspection.state is AgentConfigState.INVALID and not requested_agent:
        print(
            f"Error: local agent config is invalid ({config_inspection.reason}); "
            "pass --agent to repair it safely",
            file=sys.stderr,
        )
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
    if requested_agent is None and config_inspection.state is AgentConfigState.ABSENT:
        try:
            live_agents = _managed_schema_agents()
        except (ManagedSchemaBlockError, ManagedSchemaPathError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        if len(live_agents) > 1:
            print(
                "Error: multiple managed agent schemas exist without an agent "
                "config; pass --agent explicitly after inspecting the live paths",
                file=sys.stderr,
            )
            raise SystemExit(2)
        inferred_agent = live_agents[0] if live_agents else "generic"
    else:
        inferred_agent = str(stored.get("agent") or "generic")
    agent = requested_agent or inferred_agent
    configured_agent = stored.get("agent")
    if (
        config_inspection.state in {AgentConfigState.VALID, AgentConfigState.LEGACY}
        and isinstance(configured_agent, str)
        and configured_agent != agent
    ):
        print(
            "Error: init cannot change the configured agent from "
            f"{configured_agent} to {agent}; use `llm-wiki upgrade --agent {agent}` "
            "so source schema and reference cleanup are recorded",
            file=sys.stderr,
        )
        raise SystemExit(2)
    try:
        parallel_agents = tuple(
            live_agent for live_agent in _managed_schema_agents() if live_agent != agent
        )
    except (ManagedSchemaBlockError, ManagedSchemaPathError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    if parallel_agents:
        if len(parallel_agents) == 1:
            recovery = (
                f"llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} "
                f"--cleanup-source-agent {parallel_agents[0]}"
            )
        else:
            recovery = "inspect the managed schemas and reconcile one source at a time"
        print(
            "Error: init will not create or bless an unrecorded parallel agent "
            f"schema ({', '.join(parallel_agents)}); use {recovery}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    filename = SCHEMA_FILENAMES.get(agent)
    schema_path: Path | None = None
    committed_schema_bytes: bytes | None = None
    existing_schema_content = ""
    if filename:
        try:
            schema_path = require_safe_schema_path(filename)
            try:
                existing_schema_content = (
                    decode_managed_document_bytes(schema_path.read_bytes())
                    if schema_path.exists()
                    else ""
                )
            except (OSError, UnicodeError) as exc:
                raise ManagedSchemaPathError(
                    f"managed schema path is unreadable: {schema_path}"
                ) from exc
            try:
                require_replaceable_managed_schema(existing_schema_content)
            except ManagedSchemaBlockError as exc:
                raise ManagedSchemaBlockError(f"{schema_path}: {exc}") from exc
        except (ManagedSchemaBlockError, ManagedSchemaPathError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc

    # Resolve every persisted/rendered preference before provisioning or writing.
    cli_no_quality_hints = getattr(args, "no_quality_hints", None)
    if cli_no_quality_hints is None:
        quality_hints = bool(stored.get("quality_hints", True))
    else:
        quality_hints = not cli_no_quality_hints
    cli_issue_reporting = getattr(args, "issue_reporting", None)
    if cli_issue_reporting is None:
        issue_reporting = bool(stored.get("issue_reporting", False))
    else:
        issue_reporting = cli_issue_reporting
    cli_no_skills = getattr(args, "no_skills", None)
    if cli_no_skills is None:
        install_skill = bool(stored.get("reference_skill", True))
    else:
        install_skill = not cli_no_skills

    if migrated_config_path is not None and migrated_config_bytes is not None:
        try:
            if migrated_config_path.read_bytes() != migrated_config_bytes:
                raise OSError("content changed")
        except OSError as exc:
            print(
                "Error: alternate agent config changed after inspection; rerun "
                f"initialization after reviewing {migrated_config_path}",
                file=sys.stderr,
            )
            raise SystemExit(2) from exc

    print(f"Initializing LLM Wiki with {agent} schema...")

    # Warn if the agent has a CLI executable that isn't installed.
    executable = _CLI_AGENTS.get(agent)
    if executable and not shutil.which(executable):
        print(
            f"\nWarning: '{executable}' is not installed or not on PATH.\n"
            f"The schema file will be created, but manual agent execution\n"
            f"(`llm-wiki trigger-agent --agent {agent}`) will not work\n"
            f"until '{executable}' is installed.\n"
        )

    # Create the additive wiki scaffold before committing the managed schema.
    try:
        provision_wiki_scaffold(wiki_dir)
    except WikiScaffoldPathError as exc:
        print(f"Error creating wiki directories: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    base_dir = Path(wiki_dir)
    print(f"Created wiki directories in {base_dir}/")

    # Provision and verify before selecting the profile. A failed attempt is
    # intentionally not promoted by a coincidentally current post-state.
    if install_skill:
        pre_mutation_check = (
            (lambda: require_config_inspection_unchanged(base_dir, config_inspection))
            if cli_no_skills is None
            else None
        )
        try:
            provision = provision_reference_skill(
                agent=agent,
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
            print(f"Installed {REFERENCE_SKILL_ID} skill in {destination}/")
        else:
            if provision.state is ReferenceSkillState.PACKAGE_MISSING:
                recovery = (
                    "repair or update the installed llm-wiki package, then rerun init"
                )
            else:
                recovery = reference_recovery_command(
                    skills_dir=skills_install_dir(agent).as_posix(),
                    details=provision.details,
                )
            print(
                f"Warning: {REFERENCE_SKILL_ID} is {provision.state.value} "
                f"({provision.reason.value}); using expanded inline instructions. "
                f"Recovery: {recovery}"
            )
            if provision.state in {
                ReferenceSkillState.LOCALLY_MODIFIED,
                ReferenceSkillState.INCOMPLETE,
            }:
                print(
                    f"Kept existing {REFERENCE_SKILL_ID} skill tree in "
                    f"{provision.path.parent}/ (not an exact bundled copy; local, "
                    "extra, and conflicting entries were preserved)"
                )
        try:
            other_skills = len(list_bundled_skills()) - 1
        except Exception:
            other_skills = 0
        if other_skills > 0:
            print(
                f"{other_skills} more bundled workflow skills are available: "
                "run `llm-wiki skills list`"
            )
    else:
        reference_state = verify_reference_skill(agent=agent).state
        print(
            "Warning: managed reference installation is disabled; using expanded "
            "inline instructions (managed-reference-disabled). Read-only knowledge "
            "remains available; re-enable it explicitly with "
            "`llm-wiki upgrade --skills`."
        )

    decision = select_render_profile(
        reference_enabled=install_skill,
        reference_state=reference_state,
    )
    if schema_path is not None:
        try:
            schema_absolute = (
                schema_path
                if schema_path.is_absolute()
                else Path.cwd().resolve() / schema_path
            )
            ensure_guarded_directory(schema_absolute.parent)
            schema_path = require_safe_schema_path(schema_path)
            try:
                if schema_path.exists():
                    existing_schema_bytes = schema_path.read_bytes()
                    existing_content = decode_managed_document_bytes(
                        existing_schema_bytes
                    )
                else:
                    existing_schema_bytes = None
                    existing_content = ""
            except (OSError, UnicodeError) as exc:
                raise ManagedSchemaPathError(
                    f"managed schema path is unreadable: {schema_path}"
                ) from exc
            require_replaceable_managed_schema(existing_content)
            managed_content = _build_schema_content(
                agent,
                wiki_dir,
                render_profile=decision.profile,
                quality_hints=quality_hints,
                issue_reporting=issue_reporting,
                source_selection=source_selection,
            )
            updated_content = replace_schema_block_content(
                existing_content,
                managed_content,
            )
            require_managed_schema_profile(updated_content, decision.profile)
            committed_schema_bytes = encode_managed_document_text(updated_content)
            atomic_write_guarded_bytes(
                schema_absolute,
                committed_schema_bytes,
                mode=0o644,
                require_single_link=False,
                expected_existing=existing_schema_bytes,
            )
            require_safe_schema_path(schema_path)
        except (ManagedSchemaBlockError, ManagedSchemaPathError, OSError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        if not existing_content:
            print(f"Created agent schema file: {schema_path}")
        elif _CONSTRAINT_START in existing_content:
            print(f"Refreshed agent constraints in existing file: {schema_path}")
        else:
            print(f"Appended agent constraints to existing file: {schema_path}")

    # Persist only after the schema write succeeds. Unknown compatible config
    # fields survive the merge; the triplet explains the actual rendered block.
    config: dict[str, object] = dict(stored)
    config.update(
        {
            "agent": agent,
            "quality_hints": quality_hints,
            "reference_skill": install_skill,
            "issue_reporting": issue_reporting,
            "rendered_profile": decision.profile.value,
            "render_profile_version": decision.version,
            "render_reason": decision.reason.value,
        }
    )
    if source_selection is not None:
        config["source_selection"] = source_selection
    else:
        config.pop("source_selection", None)
    write_config(
        base_dir,
        config,
        expected_existing=canonical_config_snapshot,
    )

    if migrated_config_path is not None and migrated_config_bytes is not None:
        canonical_config_path = get_agent_config_path(base_dir)
        if migrated_config_path != canonical_config_path:
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
                    f"Migrated local agent config to {canonical_config_path.as_posix()}"
                )
            except OSError as exc:
                print(
                    "Error: alternate agent config changed or could not be "
                    "retired safely after the canonical commit at "
                    f"{migrated_config_path}: {exc}; inspect both config homes "
                    "before retrying",
                    file=sys.stderr,
                )
                raise SystemExit(2) from exc

    try:
        if (
            decision.profile is SchemaRenderProfile.COMPACT
            and verify_reference_skill(agent=agent).state
            is not ReferenceSkillState.CURRENT
        ):
            raise ManagedSchemaBlockError(
                "managed reference changed after compact schema commit"
            )
        final_parallel_agents = tuple(
            live_agent for live_agent in _managed_schema_agents() if live_agent != agent
        )
        if final_parallel_agents:
            raise ManagedSchemaBlockError(
                "a parallel managed agent schema appeared during initialization: "
                + ", ".join(final_parallel_agents)
            )
        if schema_path is not None:
            current_schema_path = require_safe_schema_path(schema_path)
            current_schema_bytes = (
                current_schema_path.read_bytes()
                if current_schema_path.exists()
                else None
            )
            if current_schema_bytes != committed_schema_bytes:
                raise ManagedSchemaPathError(
                    f"managed schema changed after commit: {current_schema_path}"
                )
            if current_schema_bytes is None:
                raise ManagedSchemaPathError(
                    f"managed schema is missing after commit: {current_schema_path}"
                )
            block = classify_managed_schema_block(
                decode_managed_document_bytes(current_schema_bytes)
            )
            if (
                block.state is not ManagedSchemaBlockState.PROFILED
                or block.profile is not decision.profile
            ):
                raise ManagedSchemaBlockError(
                    f"managed schema profile changed after commit: {current_schema_path}"
                )
        require_committed_config(base_dir, config)
    except (ValueError, OSError, UnicodeError, ManagedSchemaBlockError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print("LLM Wiki initialized successfully.")
