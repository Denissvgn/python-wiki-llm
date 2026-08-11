from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from ..config import (
    AgentConfigInspection,
    AgentConfigState,
    DEFAULT_WIKI_DIR,
    IDE_AGENTS,
    config_requires_manual_recovery,
    inspect_config,
    validate_path,
    validate_source_root,
)
from ..services import circuit_breaker
from ..services.io import first_unsafe_path_component
from ..services.knowledge_observability import (
    knowledge_status_payload,
    load_snapshot_knowledge_observability,
)
from ..services.paths import shell_quote
from ..services.rendering_lifecycle import (
    LifecycleStatus,
    ManagedLifecycleState,
    classify_lifecycle_status,
)
from ..services.schema import (
    SCHEMA_FILENAMES,
    ManagedSchemaBlock,
    ManagedSchemaBlockState,
    classify_managed_schema_block,
    decode_managed_document_bytes,
    require_safe_schema_path,
)
from ..services.skills import (
    ReferenceSkillState,
    ReferenceSkillVerification,
    skills_install_dir,
    verify_reference_skill,
)
from ..services.wiki_surface import PageKind, canonical_path, iter_page_kinds
from ..services.wiki_lifecycle import (
    WikiScaffoldPathError,
    require_safe_wiki_scaffold,
)
from .hook_cmd import is_managed_hook_content


def _count_markdown_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    return sum(1 for _ in directory.glob("*.md"))


def _status_label(kind: PageKind, fallback: str) -> str:
    if kind == PageKind.FLOWS:
        return "Flows"
    return fallback


def _count_surface_pages(wiki_path: Path, entry) -> int:
    if entry.requires_page_id:
        if entry.directory is None:
            return 0
        return _count_markdown_files(wiki_path / entry.directory)
    return int((wiki_path / canonical_path(entry.kind)).is_file())


def _architecture_page_count(wiki_path: Path) -> int:
    return sum(
        1
        for kind in (
            PageKind.API_CONTRACTS,
            PageKind.DEPENDENCIES,
            PageKind.LOAD_ORDER,
        )
        if (wiki_path / canonical_path(kind)).is_file()
    )


def _format_counts(counts: object) -> str:
    if not isinstance(counts, dict):
        return "unavailable"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


def _print_knowledge_status(
    wiki_path: Path,
    src_dir: str,
    *,
    source_selection: str | Path | None = None,
) -> None:
    observability = load_snapshot_knowledge_observability(
        wiki_path,
        src_dir=src_dir,
        source_selection=source_selection,
    )
    status = knowledge_status_payload(observability.view)
    summary = observability.summary.to_payload()

    print(f"Knowledge:       {status['availability']} (reason: {status['reason']})")
    print(f"  Concepts evaluated: {summary['concepts_evaluated']}")
    print(f"  Evidence issues: {_format_counts(summary['evidence_issue_counts'])}")
    print(f"  Freshness: {status['freshness']}")
    phase_durations = summary["phase_durations_ms"]
    load_ms = (
        phase_durations.get("load") if isinstance(phase_durations, Mapping) else None
    )
    if load_ms is not None:
        print(f"  Snapshot load: {load_ms} ms")


def _configured_agent(config: AgentConfigInspection) -> str:
    """Return the validated agent value supplied by config inspection."""

    agent = config.data["agent"]
    assert isinstance(agent, str)
    return agent


def _display_project_path(path: Path) -> str:
    """Render checkout-local diagnostics without leaking temporary roots."""

    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_managed_schema(path: Path) -> ManagedSchemaBlock:
    """Classify one schema path without allowing read errors to abort status."""

    if first_unsafe_path_component(path) is not None:
        return ManagedSchemaBlock(ManagedSchemaBlockState.MALFORMED)
    if not path.exists() and not path.is_symlink():
        return ManagedSchemaBlock(ManagedSchemaBlockState.ABSENT)
    try:
        safe_path = require_safe_schema_path(path)
        if not safe_path.is_file():
            return ManagedSchemaBlock(ManagedSchemaBlockState.MALFORMED)
        content = decode_managed_document_bytes(safe_path.read_bytes())
    except (OSError, UnicodeError, ValueError):
        return ManagedSchemaBlock(ManagedSchemaBlockState.MALFORMED)
    return classify_managed_schema_block(content)


def _managed_schema_candidates() -> tuple[tuple[str, Path, ManagedSchemaBlock], ...]:
    """Return actionable current agent schema paths with any managed state."""

    found: list[tuple[str, Path, ManagedSchemaBlock]] = []
    seen: set[Path] = set()
    for agent, filename in SCHEMA_FILENAMES.items():
        path = Path(filename)
        if path in seen:
            continue
        seen.add(path)
        if not path.exists() and not path.is_symlink():
            continue
        block = _read_managed_schema(path)
        if block.state is not ManagedSchemaBlockState.ABSENT:
            found.append((agent, path, block))
    return tuple(found)


def _diagnostic_schema_target(
    config: AgentConfigInspection,
) -> tuple[str, Path, ManagedSchemaBlock, bool, bool]:
    """Choose live evidence for status without treating it as persisted intent."""

    configured_agent = _configured_agent(config)
    if config.state in {AgentConfigState.VALID, AgentConfigState.LEGACY}:
        path = Path(SCHEMA_FILENAMES[configured_agent])
        return configured_agent, path, _read_managed_schema(path), False, False

    candidates = _managed_schema_candidates()
    if len(candidates) == 1:
        agent, path, block = candidates[0]
        return agent, path, block, True, False

    path = Path(SCHEMA_FILENAMES[configured_agent])
    return (
        configured_agent,
        path,
        _read_managed_schema(path),
        False,
        len(candidates) > 1,
    )


def _upgrade_recovery(
    *,
    wiki_dir: str,
    agent: str,
    enable_reference: bool,
    cleanup_source_agent: str | None = None,
) -> str:
    skills_option = "--skills" if enable_reference else "--no-skills"
    command = (
        f"llm-wiki upgrade --wiki-dir {shell_quote(wiki_dir)} --agent {agent} "
        f"{skills_option}"
    )
    if cleanup_source_agent is not None:
        command += f" --cleanup-source-agent {cleanup_source_agent}"
    return command


def _init_recovery(
    *,
    wiki_dir: str,
    agent: str,
    reference_enabled: bool,
) -> str:
    command = f"llm-wiki init --wiki-dir {shell_quote(wiki_dir)} --agent {agent}"
    return command if reference_enabled else f"{command} --no-skills"


def _reference_recovery_prerequisites(
    reference: ReferenceSkillVerification,
) -> tuple[str, ...]:
    """Explain what must happen before a reference refresh can converge."""

    if reference.state is ReferenceSkillState.PACKAGE_MISSING:
        return ("repair or upgrade the installed llm-wiki package",)
    if reference.state is ReferenceSkillState.LOCALLY_MODIFIED:
        return ("inspect or back up local managed-reference changes",)
    if reference.state is ReferenceSkillState.INCOMPLETE:
        missing_only = bool(reference.details) and all(
            detail.startswith(("missing:", "missing_directory:"))
            for detail in reference.details
        )
        if not missing_only:
            return (
                "inspect and back up preserved extra, conflicting, unsafe, or "
                "unreadable managed-reference entries; move them aside or remove "
                "them if intended",
            )
    return ()


def _recovery_guidance(
    *,
    lifecycle: LifecycleStatus,
    reference: ReferenceSkillVerification,
    wiki_dir: str,
    agent: str,
    reference_enabled: bool,
    interrupted_switch: bool,
    malformed_paths: tuple[Path, ...] = (),
    unsafe_config_path: Path | None = None,
    config_problem_reason: str | None = None,
    ambiguous_paths: tuple[Path, ...] = (),
    obsolete_references: tuple[ReferenceSkillVerification, ...] = (),
    cleanup_source_agent: str | None = None,
    ambiguous_agents: tuple[str, ...] = (),
    unsafe_schema_paths: tuple[tuple[Path, Path], ...] = (),
    ambiguous_references: tuple[tuple[str, ReferenceSkillVerification], ...] = (),
    untrusted_pending_agent: str | None = None,
    invalid_agent_selection: bool = False,
    scaffold_error: str | None = None,
) -> str:
    """Return a state-aware command that also rerenders the managed block."""

    final_command = (
        _init_recovery(
            wiki_dir=wiki_dir,
            agent=agent,
            reference_enabled=reference_enabled,
        )
        if lifecycle.state is ManagedLifecycleState.MISSING_SCHEMA
        and not interrupted_switch
        else _upgrade_recovery(
            wiki_dir=wiki_dir,
            agent=agent,
            enable_reference=reference_enabled,
            cleanup_source_agent=cleanup_source_agent,
        )
    )
    final_command_is_instruction = False
    if untrusted_pending_agent == agent and not ambiguous_paths:
        repaired_command = (
            _init_recovery(
                wiki_dir=wiki_dir,
                agent=agent,
                reference_enabled=reference_enabled,
            )
            if lifecycle.state is ManagedLifecycleState.MISSING_SCHEMA
            else _upgrade_recovery(
                wiki_dir=wiki_dir,
                agent=agent,
                enable_reference=reference_enabled,
            )
        )
        final_command = (
            f"retain {agent}: inspect the invalid config, remove the untrusted "
            "pending cleanup pair, repair the agent field, then run "
            f"`{repaired_command}`"
        )
        final_command_is_instruction = True
    prerequisites: list[str] = []
    if unsafe_config_path is not None:
        if config_problem_reason == "multiple-agent-config-homes":
            config_homes = tuple(
                dict.fromkeys(
                    (
                        Path(".git/.llm-wiki-agent"),
                        Path(wiki_dir) / ".llm-wiki-agent",
                    )
                )
            )
            displayed = " and ".join(
                _display_project_path(path) for path in config_homes
            )
            return (
                f"inspect and preserve both local agent configs at {displayed}; "
                "select the authoritative config and move the other aside without "
                "discarding pending cleanup or extension state, then rerun "
                f"`llm-wiki status --wiki-dir {shell_quote(wiki_dir)}` before init "
                "or upgrade"
            )
        unsafe_component = first_unsafe_path_component(unsafe_config_path)
        displayed_component = _display_project_path(
            unsafe_component if unsafe_component is not None else unsafe_config_path
        )
        config_path_problem = (
            "unsafe local-config path component"
            if unsafe_component is not None
            else "invalid, non-regular, or unreadable local-config path"
        )
        return (
            f"move aside or repair {config_path_problem} "
            f"{displayed_component} before accessing "
            f"{_display_project_path(unsafe_config_path)}"
            + "; inspect any quarantined config bytes for pending cleanup evidence "
            "and inspect alternate managed-reference homes; then rerun "
            f"`llm-wiki status --wiki-dir {shell_quote(wiki_dir)}` before any init "
            "or upgrade, preserving or explicitly confirming any source cleanup"
        )
    if scaffold_error is not None:
        return (
            "inspect and move aside or repair the unavailable wiki scaffold path "
            f"({scaffold_error}), then rerun "
            f"`llm-wiki status --wiki-dir {shell_quote(wiki_dir)}` before init or "
            "upgrade"
        )
    if invalid_agent_selection:
        return (
            "inspect and repair the invalid agent field, explicitly select one "
            "supported agent, then rerun "
            f"`llm-wiki status --wiki-dir {shell_quote(wiki_dir)}` before init or "
            "upgrade"
        )
    if unsafe_schema_paths:
        prerequisites.extend(
            "move aside unsafe managed-schema path component "
            f"{_display_project_path(unsafe)} before accessing "
            f"{_display_project_path(path)}"
            for path, unsafe in unsafe_schema_paths
        )
    if malformed_paths:
        paths = ", ".join(path.as_posix() for path in malformed_paths)
        prerequisites.append(
            f"inspect and repair or move aside malformed managed markers at {paths}"
        )
    if ambiguous_paths:
        paths = ", ".join(path.as_posix() for path in ambiguous_paths)
        prerequisites.append(
            f"choose the intended agent from managed schema candidates at {paths}"
        )
        alternatives = tuple(dict.fromkeys((agent, *ambiguous_agents)))
        if len(alternatives) == 1 and untrusted_pending_agent == alternatives[0]:
            retained_command = _upgrade_recovery(
                wiki_dir=wiki_dir,
                agent=agent,
                enable_reference=reference_enabled,
            )
            final_command = (
                f"retain {agent}: inspect the invalid config, remove the untrusted "
                "pending cleanup pair, repair the agent field, then run "
                f"`{retained_command}`"
            )
        elif len(alternatives) == 2:
            first, second = alternatives
            reference_by_agent = dict(ambiguous_references)

            def branch(agent_name: str, command: str) -> str:
                candidate = reference_by_agent.get(agent_name)
                candidate_prerequisites = (
                    _reference_recovery_prerequisites(candidate)
                    if candidate is not None and reference_enabled
                    else ()
                )
                if candidate is not None and candidate_prerequisites:
                    return "; ".join(candidate_prerequisites) + (
                        f" at {candidate.path.as_posix()}, then run `{command}`"
                    )
                return f"run `{command}`"

            if untrusted_pending_agent in alternatives:
                pending = untrusted_pending_agent
                continuation = second if pending == first else first
                continuation_command = _upgrade_recovery(
                    wiki_dir=wiki_dir,
                    agent=continuation,
                    enable_reference=reference_enabled,
                    cleanup_source_agent=pending,
                )
                retained_command = _upgrade_recovery(
                    wiki_dir=wiki_dir,
                    agent=pending,
                    enable_reference=reference_enabled,
                )
                final_command = (
                    f"retain {pending}: inspect the invalid config, remove the "
                    "untrusted pending cleanup pair, repair its invalid fields, then "
                    f"{branch(pending, retained_command)}; or continue {continuation}: "
                    f"{branch(continuation, continuation_command)}"
                )
            elif untrusted_pending_agent is not None:
                pending = untrusted_pending_agent
                first_command = _upgrade_recovery(
                    wiki_dir=wiki_dir,
                    agent=first,
                    enable_reference=reference_enabled,
                    cleanup_source_agent=pending,
                )
                second_command = _upgrade_recovery(
                    wiki_dir=wiki_dir,
                    agent=second,
                    enable_reference=reference_enabled,
                    cleanup_source_agent=pending,
                )
                final_command = (
                    f"first inspect the invalid config and its untrusted pending "
                    f"cleanup evidence for {pending}; select {first}: "
                    f"{branch(first, first_command)}, or select {second}: "
                    f"{branch(second, second_command)}; then rerun status before "
                    "resolving any remaining managed schema"
                )
            else:
                first_command = _upgrade_recovery(
                    wiki_dir=wiki_dir,
                    agent=first,
                    enable_reference=reference_enabled,
                    cleanup_source_agent=second,
                )
                second_command = _upgrade_recovery(
                    wiki_dir=wiki_dir,
                    agent=second,
                    enable_reference=reference_enabled,
                    cleanup_source_agent=first,
                )
                final_command = (
                    f"select {first}: {branch(first, first_command)}, or select "
                    f"{second}: {branch(second, second_command)}"
                )
        else:
            pending_prefix = (
                "inspect the invalid config and resolve its untrusted pending "
                f"cleanup evidence for {untrusted_pending_agent}; "
                if untrusted_pending_agent is not None
                else ""
            )
            final_command = pending_prefix + (
                "back up candidate managed-reference trees, select one intended "
                "agent explicitly, move aside every other managed schema, then "
                "rerun status before upgrade"
            )
        final_command_is_instruction = True
    if lifecycle.state is ManagedLifecycleState.EXPANDED_SKILLS_DISABLED and not (
        interrupted_switch
        or lifecycle.config_mismatch
        or malformed_paths
        or unsafe_config_path is not None
        or unsafe_schema_paths
        or ambiguous_paths
    ):
        optional = _upgrade_recovery(
            wiki_dir=wiki_dir,
            agent=agent,
            enable_reference=True,
        )
        opt_out_prerequisites = list(_reference_recovery_prerequisites(reference))
        if opt_out_prerequisites:
            return (
                "none required while disabled; optional re-enable: "
                + "; ".join(opt_out_prerequisites)
                + f", then run `{optional}`"
            )
        return "none required; optional re-enable: " + optional
    if reference_enabled:
        prerequisites.extend(_reference_recovery_prerequisites(reference))
    preserved_obsolete = tuple(
        item
        for item in obsolete_references
        if item.state is not ReferenceSkillState.CURRENT
    )
    if preserved_obsolete and reference_enabled:
        prerequisites.append(
            "back up any user-owned content, then move aside or remove the recorded "
            "obsolete managed-reference trees at "
            + ", ".join(item.path.as_posix() for item in preserved_obsolete)
        )
    if prerequisites:
        suffix = (
            final_command if final_command_is_instruction else f"run `{final_command}`"
        )
        return "; ".join(prerequisites) + f", then {suffix}"
    if lifecycle.state is ManagedLifecycleState.COMPACT_CURRENT and not (
        interrupted_switch or lifecycle.config_mismatch
    ):
        return "none required"
    return final_command


def _print_reference_summary(
    reference: ReferenceSkillVerification,
    *,
    skills_dir: Path,
    reference_enabled: bool,
    intent_trusted: bool,
) -> None:
    if reference.state is ReferenceSkillState.CURRENT:
        print("Reference skill: wiki-reference (current)")
    elif reference.state is ReferenceSkillState.LOCALLY_MODIFIED:
        print("Reference skill: wiki-reference differs from bundled (locally modified)")
    elif reference.state is ReferenceSkillState.INCOMPLETE:
        print("Reference skill: wiki-reference differs from bundled (incomplete)")
    elif reference.state is ReferenceSkillState.PACKAGE_MISSING:
        print("Reference skill: bundled wiki-reference package files are unavailable")
    elif reference.state is ReferenceSkillState.INSTALL_ERROR:
        print("Reference skill: wiki-reference installation failed")
    else:
        print("Reference skill: not installed")

    if reference_enabled and reference.state in {
        ReferenceSkillState.ABSENT,
        ReferenceSkillState.INCOMPLETE,
        ReferenceSkillState.INSTALL_ERROR,
        ReferenceSkillState.LOCALLY_MODIFIED,
    }:
        print(
            "Reference repair: use the explicit state-aware Recovery command below; "
            "a tree-only repair can use `llm-wiki skills install --dest "
            f"{skills_dir.as_posix()} --skill wiki-reference --force`"
        )
    incomplete_conflict = reference.state is ReferenceSkillState.INCOMPLETE and not (
        reference.details
        and all(
            detail.startswith(("missing:", "missing_directory:"))
            for detail in reference.details
        )
    )
    if intent_trusted and (
        reference.state is ReferenceSkillState.LOCALLY_MODIFIED or incomplete_conflict
    ):
        print("                  Inspect preserved extra or conflicting entries")


def _print_managed_lifecycle(
    *,
    wiki_dir: str,
    config: AgentConfigInspection,
    scaffold_error: str | None = None,
) -> None:
    """Report live schema/reference state; persisted fields are evidence only."""

    configured_agent_hint = _configured_agent(config)
    agent, schema_path, schema, inferred, ambiguous = _diagnostic_schema_target(config)
    skills_dir = skills_install_dir(agent)
    reference = verify_reference_skill(agent=agent, target=skills_dir)
    # An absent config uses the documented product defaults. Only opaque or
    # ambiguous bytes that require manual recovery suppress mutation guidance;
    # independently invalid known fields retain their normalized intent.
    reference_intent_trusted = not config_requires_manual_recovery(config)
    configured_reference_enabled = config.data["reference_skill"]
    assert isinstance(configured_reference_enabled, bool)
    reference_enabled = (
        configured_reference_enabled if reference_intent_trusted else False
    )
    lifecycle = classify_lifecycle_status(
        schema=schema,
        reference=reference,
        reference_enabled=reference_enabled,
        skills_dir=skills_dir.as_posix(),
        configured_profile=config.data.get("rendered_profile"),
        configured_reason=config.data.get("render_reason"),
    )

    candidates = _managed_schema_candidates()
    candidate_others = tuple(
        path for _candidate_agent, path, _block in candidates if path != schema_path
    )
    pending_value = config.data.get("pending_cleanup_agent")
    pending_trusted = config.state is AgentConfigState.VALID
    pending_agent = (
        str(pending_value)
        if config.state in {AgentConfigState.VALID, AgentConfigState.INVALID}
        and isinstance(pending_value, str)
        else None
    )
    untrusted_pending_conflicts_with_diagnostic = bool(
        not pending_trusted and pending_agent == agent
    )
    pending_schema_path = (
        Path(SCHEMA_FILENAMES[pending_agent])
        if pending_agent in SCHEMA_FILENAMES and pending_agent != agent
        else None
    )
    if pending_schema_path is not None:
        other_managed = tuple(
            path for path in candidate_others if path == pending_schema_path
        )
    elif (
        config.state in {AgentConfigState.VALID, AgentConfigState.LEGACY}
        and schema.state is ManagedSchemaBlockState.ABSENT
        and len(candidate_others) == 1
    ):
        other_managed = candidate_others
    elif config.state not in {AgentConfigState.VALID, AgentConfigState.LEGACY}:
        other_managed = candidate_others
    else:
        # A parallel managed schema may be intentional, or it may be the target
        # left by a config-write failure. Status must surface the ambiguity but
        # never guess which agent path is authoritative.
        other_managed = candidate_others
    ambiguous_parallel = bool(
        other_managed
        and pending_agent is None
        and config.state in {AgentConfigState.VALID, AgentConfigState.LEGACY}
        and schema.state is not ManagedSchemaBlockState.ABSENT
    )
    ambiguous_cleanup = (
        ambiguous_parallel
        or bool(other_managed and pending_agent is None)
        or untrusted_pending_conflicts_with_diagnostic
    )
    config_interrupted = bool(pending_agent) or (
        (inferred or ambiguous)
        and (schema.state is not ManagedSchemaBlockState.ABSENT or bool(candidates))
    )
    pending_reference = (
        verify_reference_skill(agent=pending_agent)
        if pending_agent is not None
        and pending_agent != agent
        and skills_install_dir(pending_agent) != skills_dir
        and config.data.get("pending_cleanup_reference") is True
        else None
    )
    obsolete_references = (
        (pending_reference,)
        if pending_reference is not None
        and (
            pending_reference.state
            not in {ReferenceSkillState.ABSENT, ReferenceSkillState.PACKAGE_MISSING}
            or pending_reference.path.exists()
            or pending_reference.path.is_symlink()
        )
        else ()
    )
    interrupted_switch = bool(other_managed) or config_interrupted
    relevant_managed_paths = {schema_path, *other_managed}
    if pending_schema_path is not None:
        relevant_managed_paths.add(pending_schema_path)
    unsafe_schema_paths = tuple(
        (path, unsafe)
        for path in relevant_managed_paths
        if (unsafe := first_unsafe_path_component(path)) is not None
    )
    unsafe_schema_path_set = {path for path, _unsafe in unsafe_schema_paths}
    malformed_paths = tuple(
        path
        for _candidate_agent, path, block in candidates
        if block.state is ManagedSchemaBlockState.MALFORMED
        and (ambiguous or path in relevant_managed_paths)
        and path not in unsafe_schema_path_set
    )
    warning_parts = [lifecycle.warning] if lifecycle.warning else []
    if config.state is AgentConfigState.INVALID:
        warning_parts.append(f"agent-config-invalid:{config.reason}")
    elif config.state is AgentConfigState.ABSENT and config_interrupted:
        warning_parts.append("agent-config-absent-with-live-managed-schema")
    if inferred:
        warning_parts.append(f"live-agent-inferred-from-managed-schema:{agent}")
    if ambiguous:
        warning_parts.append("agent-config-does-not-identify-one-live-managed-schema")
    if ambiguous_cleanup:
        warning_parts.append(
            "agent-switch-intent-ambiguous;explicit-agent-choice-required"
        )
    if other_managed:
        warning_parts.append(
            "interrupted-agent-switch:managed-schema-remains-at-"
            + ",".join(path.as_posix() for path in other_managed)
        )
    if unsafe_schema_paths:
        warning_parts.append(
            "unsafe-managed-schema-path:"
            + ",".join(
                f"{path.as_posix()}@{unsafe.as_posix()}"
                for path, unsafe in unsafe_schema_paths
            )
        )
    parallel_candidates = tuple(
        path for path in candidate_others if path not in other_managed
    )
    if parallel_candidates:
        warning_parts.append(
            "additional-managed-agent-schema-present:"
            + ",".join(path.as_posix() for path in parallel_candidates)
        )
    if obsolete_references:
        warning_parts.append(
            "interrupted-agent-switch:managed-reference-remains-at-"
            + ",".join(item.path.as_posix() for item in obsolete_references)
        )
    if pending_agent:
        warning_parts.append(
            (
                "pending-source-cleanup:"
                if pending_trusted
                else "untrusted-pending-source-cleanup-evidence:"
            )
            + pending_agent
        )

    recovery_ambiguous_paths = (
        tuple(path for _candidate_agent, path, _block in candidates)
        if ambiguous or untrusted_pending_conflicts_with_diagnostic
        else other_managed
        if ambiguous_cleanup
        else ()
    )
    recovery_ambiguous_agents = (
        tuple(
            dict.fromkeys(
                (
                    *(
                        candidate_agent
                        for candidate_agent, path, _block in candidates
                        if path
                        in (other_managed or tuple(path for _, path, _ in candidates))
                        and candidate_agent != agent
                    ),
                    *(
                        (configured_agent_hint,)
                        if untrusted_pending_conflicts_with_diagnostic
                        else ()
                    ),
                )
            )
        )
        if ambiguous or ambiguous_cleanup
        else ()
    )
    recovery_reference_agents = tuple(
        dict.fromkeys((agent, *recovery_ambiguous_agents))
    )

    print(f"Managed schema:  {schema_path.as_posix()}")
    print(f"Managed lifecycle: {lifecycle.state.value}")
    print(f"Rendered profile: {lifecycle.rendered_profile}")
    configured_render_reason = config.data.get("render_reason")
    if isinstance(configured_render_reason, str):
        print(f"Last render reason: {configured_render_reason}")
    _print_reference_summary(
        reference,
        skills_dir=skills_dir,
        reference_enabled=reference_enabled,
        intent_trusted=reference_intent_trusted,
    )
    print(f"Reference state: {lifecycle.reference_state}")
    print(f"Reference reason: {reference.reason.value}")
    print(f"Reference path:  {lifecycle.reference_path}")
    print(f"Reference current: {'yes' if lifecycle.reference_current else 'no'}")
    print(f"Read-only knowledge: {lifecycle.read_only_knowledge}")
    print(f"Warning:         {'; '.join(warning_parts) if warning_parts else 'none'}")
    if interrupted_switch:
        if other_managed:
            detail = f"managed schema remains at {', '.join(map(str, other_managed))}"
        elif obsolete_references:
            detail = "obsolete managed-reference tree remains"
        elif pending_agent:
            detail = f"pending cleanup marker remains for {pending_agent}"
        elif inferred:
            detail = (
                f"agent config is missing for live schema {schema_path}"
                if config.state is AgentConfigState.ABSENT
                else f"agent config is invalid or unusable at {config.path} "
                f"({config.reason}) for live schema {schema_path}"
            )
        else:
            detail = "managed agent selection is unresolved"
        print(f"Switch state:    interrupted-agent-switch ({detail})")
    if obsolete_references:
        print(
            "Reference switch state: managed reference remains at "
            + ", ".join(item.path.as_posix() for item in obsolete_references)
        )
    recovery = _recovery_guidance(
        lifecycle=lifecycle,
        reference=reference,
        wiki_dir=wiki_dir,
        agent=agent,
        reference_enabled=reference_enabled,
        interrupted_switch=interrupted_switch,
        malformed_paths=malformed_paths,
        unsafe_config_path=(
            config.path if config_requires_manual_recovery(config) else None
        ),
        config_problem_reason=config.reason,
        ambiguous_paths=recovery_ambiguous_paths,
        obsolete_references=obsolete_references,
        cleanup_source_agent=(
            pending_agent
            if pending_agent is not None
            and pending_agent != agent
            and not pending_trusted
            else next(
                (
                    candidate_agent
                    for candidate_agent, path, _block in candidates
                    if path in other_managed
                ),
                None,
            )
            if len(other_managed) == 1
            and not ambiguous_cleanup
            and pending_agent is None
            else None
        ),
        ambiguous_agents=recovery_ambiguous_agents,
        unsafe_schema_paths=unsafe_schema_paths,
        ambiguous_references=(
            tuple(
                (candidate_agent, verify_reference_skill(agent=candidate_agent))
                for candidate_agent in recovery_reference_agents
            )
            if ambiguous or ambiguous_cleanup
            else ()
        ),
        untrusted_pending_agent=(pending_agent if not pending_trusted else None),
        invalid_agent_selection=bool(
            config.state is AgentConfigState.INVALID
            and config.reason == "invalid-config-field:agent"
            and not candidates
            and pending_agent is None
        ),
        scaffold_error=scaffold_error,
    )
    print(f"Recovery command: {recovery}")


def run(args) -> None:
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(str(wiki_dir), "--wiki-dir")
    try:
        require_safe_wiki_scaffold(wiki_dir)
        scaffold_error: str | None = None
    except WikiScaffoldPathError as exc:
        scaffold_error = str(exc)
    src_dir = getattr(args, "src_dir", ".")
    allow_external = bool(getattr(args, "allow_external_src", False))
    source_root = validate_source_root(
        src_dir,
        "--src-dir",
        allow_external=allow_external,
    )
    if allow_external:
        src_dir = str(source_root)
    wiki_path = Path(wiki_dir)
    git_dir = Path(".git")

    print("LLM Wiki Status")
    print("=" * 40)

    # Wiki directory
    if scaffold_error is not None:
        print(f"Wiki directory:  {wiki_dir} (unavailable: {scaffold_error})")
    elif wiki_path.exists():
        print(f"Wiki directory:  {wiki_dir} (exists)")
        for entry in iter_page_kinds():
            label = _status_label(entry.kind, entry.label)
            count = _count_surface_pages(wiki_path, entry)
            print(f"  {label + ':':<15}{count}")
        print(f"  {'Architecture pages:':<15}{_architecture_page_count(wiki_path)}")
    else:
        print(f"Wiki directory:  {wiki_dir} (not found)")

    if scaffold_error is not None:
        print("Knowledge:       unavailable (reason: wiki-scaffold-unavailable)")
    else:
        _print_knowledge_status(
            wiki_path,
            src_dir,
            source_selection=getattr(args, "source_selection", None),
        )

    # Agent config and live managed-schema lifecycle
    config = inspect_config(wiki_dir)
    if config.state is not AgentConfigState.ABSENT:
        agent = _configured_agent(config)
        mode = "IDE" if agent in IDE_AGENTS else "CLI"
        if config.state is AgentConfigState.INVALID:
            print(
                "Agent:           invalid configuration "
                f"(reason: {config.reason}; path: {config.path})"
            )
            print(
                f"Agent config:    invalid "
                f"(reason: {config.reason}; path: {config.path})"
            )
            print(f"  Diagnostic fallback agent: {agent} ({mode})")
        else:
            print(f"Agent:           {agent} ({mode})")
            print(
                f"Agent config:    {config.state.value} "
                f"(reason: {config.reason}; path: {config.path})"
            )
        hints = config.data["quality_hints"]
        print(f"Quality hints:   {'enabled' if hints else 'disabled'}")
        issue_reporting = config.data["issue_reporting"]
        print(f"Issue reporting: {'enabled' if issue_reporting else 'disabled'}")
    else:
        print("Agent:           not configured (run `llm-wiki init --agent <agent>`)")
        print(f"Agent config:    absent (reason: {config.reason}; path: {config.path})")

    _print_managed_lifecycle(
        wiki_dir=wiki_dir,
        config=config,
        scaffold_error=scaffold_error,
    )

    # Hooks
    hooks_dir = git_dir / "hooks"
    hooks_unsafe = first_unsafe_path_component(hooks_dir)
    if hooks_unsafe is not None:
        print(f"Hooks:           unavailable (unsafe path: {hooks_unsafe})")
    elif hooks_dir.exists():
        installed = []
        unavailable = []
        non_executable = []
        for hook_name in ["post-commit", "pre-commit", "pre-push"]:
            hook_file = hooks_dir / hook_name
            if first_unsafe_path_component(hook_file) is not None:
                unavailable.append(hook_name)
                continue
            if not hook_file.exists():
                continue
            if not hook_file.is_file():
                unavailable.append(hook_name)
                continue
            try:
                content = hook_file.read_text(encoding="utf-8")
                mode = hook_file.stat().st_mode
            except (OSError, UnicodeError):
                unavailable.append(hook_name)
                continue
            if is_managed_hook_content(hook_name, content):
                if os.name != "nt" and mode & 0o111 == 0:
                    unavailable.append(hook_name)
                    non_executable.append(hook_name)
                else:
                    installed.append(hook_name)
        if unavailable:
            print(
                "Hooks:           unavailable (non-regular, unreadable, or "
                "non-executable: " + ", ".join(unavailable) + ")"
            )
            if set(unavailable) == set(non_executable):
                print(
                    "Hook recovery:  rerun `llm-wiki install-hook --force` to "
                    "restore executable managed hooks"
                )
            else:
                print(
                    "Hook recovery:  inspect and move aside unsafe or non-regular "
                    "hook entries, then rerun `llm-wiki install-hook --force`"
                )
        elif installed:
            print(f"Hooks:           {', '.join(installed)}")
        else:
            print("Hooks:           none installed")
    else:
        print("Hooks:           no .git/hooks directory")

    # Circuit breaker
    git_unsafe = first_unsafe_path_component(git_dir)
    breaker_path = git_dir / "llm-wiki-breaker.json"
    breaker_unsafe = first_unsafe_path_component(breaker_path)
    if git_unsafe is not None:
        print(f"Circuit breaker: unavailable (unsafe path: {git_unsafe})")
    elif breaker_unsafe is not None:
        print(f"Circuit breaker: unavailable (unsafe path: {breaker_unsafe})")
    elif breaker_path.exists() and not breaker_path.is_file():
        print("Circuit breaker: unavailable (non-regular state file)")
    elif git_dir.exists():
        try:
            if breaker_path.exists():
                breaker_path.read_bytes()
        except OSError:
            print("Circuit breaker: unavailable (unreadable state file)")
            return
        state = circuit_breaker.load_state(git_dir)
        breaker_state = state.get("state", "closed")
        failures = state.get("consecutive_failures", 0)
        if breaker_state == "open":
            print(f"Circuit breaker: OPEN ({failures} consecutive failures)")
            ttl_seconds = circuit_breaker.breaker_ttl_seconds()
            if ttl_seconds == 0:
                print(
                    "                 Automatic recovery is disabled; run "
                    "`llm-wiki trigger-agent --reset-breaker` to re-enable"
                )
            else:
                print(
                    "                 The next trigger evaluates automatic recovery "
                    f"after {ttl_seconds:g}s; use `--reset-breaker` to recover now"
                )
        elif breaker_state == "half-open":
            print(
                "Circuit breaker: HALF-OPEN "
                f"({failures} consecutive failures; recovery probe lease persisted)"
            )
            ttl_seconds = circuit_breaker.breaker_ttl_seconds()
            if ttl_seconds == 0:
                print(
                    "                 Automatic recovery is disabled; run "
                    "`llm-wiki trigger-agent --reset-breaker` to re-enable"
                )
            else:
                print(
                    "                 The next trigger evaluates the probe lease "
                    f"after {ttl_seconds:g}s; use `--reset-breaker` to recover now"
                )
        else:
            print(f"Circuit breaker: closed ({failures} recent failures)")
    else:
        print("Circuit breaker: no .git directory")
