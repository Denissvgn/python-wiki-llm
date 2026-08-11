"""Bundled agent skill management for LLM Wiki.

The package ships agent skills (Claude Code-compatible ``SKILL.md``
workflow directories) under ``llm_wiki_cli/skills/``.  This module lists
them, exports them to an arbitrary destination (for example, a personal
``~/.claude/skills`` directory), and installs them into the configured
agent's project directory: ``.claude/skills`` for Claude and the neutral
``.llm-wiki/skills`` directory for other configured agents.
"""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .io import first_unsafe_path_component, read_md, write_md
from .validation import require_safe_base_path

DEFAULT_INSTALL_TARGET = Path(".claude") / "skills"
BUNDLED_SKILLS_ROOT = Path(__file__).resolve().parents[1] / "skills"
SKILL_MANIFEST_NAME = "SKILL.md"

# CLI-owned deep-reference skill the agent constraint block points at.
# Init preserves regular-file drift, while upgrade and an explicit forced
# install refresh expected files. Unexpected or unsafe entries are preserved.
REFERENCE_SKILL_ID = "wiki-reference"

# Keep the managed reference contract independent from the contents that happen
# to survive in a damaged installation.  Release packaging and live state
# checks both use this exact file set.
REFERENCE_SKILL_FILES: tuple[str, ...] = (
    SKILL_MANIFEST_NAME,
    "reference.md",
    "references/context-query.md",
    "references/extractors-dependencies.md",
    "references/governance.md",
    "references/knowledge-consumption.md",
    "references/maintenance.md",
    "references/publishing.md",
    "references/repository-handoff.md",
    "references/resources-context.md",
    "references/surfaces-naming.md",
)

# Bundled workflow prerequisites live in package-owned Python rather than
# frontmatter so every supported skills runtime sees the same portable
# manifests.  Values are ordered tuples: their order is part of deterministic
# transitive expansion, and every dependency is installed before its consumer.
SKILL_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    skill_id: (REFERENCE_SKILL_ID,)
    for skill_id in (
        "agent-docs",
        "dep-audit",
        "doc-hub",
        "doc-review",
        "impact-analysis",
        "infra-review",
        "onboarding-guide",
        "publish-docs",
        "usage-examples",
        "user-docs-author",
        "wiki-bootstrap",
        "wiki-semantic-enhance",
        "wiki-sync",
    )
}

# Compatibility view used by the documentation-run integrity contract.  New
# selection code must consume SKILL_DEPENDENCIES through the resolver below.
REFERENCE_DEPENDENT_SKILLS: frozenset[str] = frozenset(
    skill_id
    for skill_id, dependencies in SKILL_DEPENDENCIES.items()
    if REFERENCE_SKILL_ID in dependencies
)

# Platform-neutral skills home for agents without a native skills runtime.
# Skills are plain Markdown, so any agent that can read files can follow the
# constraint block's explicit pointer into this directory.
GENERIC_INSTALL_TARGET = Path(".llm-wiki") / "skills"

# Agents with a native, auto-indexed skills directory. Everything else gets
# the neutral target; extend this map when a platform grows skill support.
AGENT_INSTALL_TARGETS: dict[str, Path] = {
    "claude": DEFAULT_INSTALL_TARGET,
}

# Every directory provisioning may have used — uninstall sweeps all of them.
KNOWN_INSTALL_TARGETS: tuple[Path, ...] = (
    DEFAULT_INSTALL_TARGET,
    GENERIC_INSTALL_TARGET,
)


def skills_install_dir(agent: str | None) -> Path:
    """Project-relative skills directory for *agent*.

    ``None`` (agent unknown/unconfigured) keeps the historical
    ``.claude/skills`` default.
    """
    if agent is None:
        return DEFAULT_INSTALL_TARGET
    return AGENT_INSTALL_TARGETS.get(agent, GENERIC_INSTALL_TARGET)


class SkillsError(ValueError):
    """Raised for invalid skill list/export/install requests."""


class ReferenceSkillState(str, Enum):
    """Stable live/provisioning states for the managed reference skill."""

    ABSENT = "absent"
    CURRENT = "current"
    LOCALLY_MODIFIED = "locally_modified"
    INCOMPLETE = "incomplete"
    PACKAGE_MISSING = "package_missing"
    INSTALL_ERROR = "install_error"


class ReferenceSkillReason(str, Enum):
    """Stable lifecycle reason codes paired with :class:`ReferenceSkillState`."""

    ABSENT = "managed-reference-absent"
    CURRENT = "managed-reference-current"
    LOCALLY_MODIFIED = "managed-reference-modified"
    INCOMPLETE = "managed-reference-incomplete"
    PACKAGE_MISSING = "managed-reference-package-missing"
    INSTALL_ERROR = "managed-reference-install-failed"


@dataclass(frozen=True)
class BundledSkill:
    skill_id: str
    name: str
    description: str
    path: Path
    files: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "files": list(self.files),
        }


@dataclass
class SkillOperation:
    action: str
    path: str
    message: str = ""


@dataclass
class SkillsReport:
    """One export/install result with requested and effective skill identities.

    ``skills`` is the dependency-first effective order. ``requested_skills``
    preserves the de-duplicated roots supplied by the caller (or every bundled
    skill for the all-skills default), while ``dependency_skills`` contains
    only closure members that were not themselves requested.
    """

    ok: bool = True
    dest_dir: str = ""
    skills: list[str] = field(default_factory=list)
    operations: list[SkillOperation] = field(default_factory=list)
    issues: list[dict[str, str]] = field(default_factory=list)
    requested_skills: list[str] = field(default_factory=list)
    dependency_skills: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dest_dir": self.dest_dir,
            "skills": self.skills,
            "operations": [op.__dict__ for op in self.operations],
            "issues": self.issues,
            "requested_skills": self.requested_skills,
            "dependency_skills": self.dependency_skills,
        }


@dataclass(frozen=True)
class ReferenceSkillVerification:
    """One read-only classification of the live managed-reference tree.

    ``path`` is always the requested installed ``wiki-reference`` directory.
    ``details`` contains sorted, machine-stable diagnostics. Entry diagnostics
    use paths relative to the installed or bundled skill root; install report
    diagnostics retain the exact path supplied by the report.
    """

    state: ReferenceSkillState
    reason: ReferenceSkillReason
    path: Path
    details: tuple[str, ...] = ()

    @property
    def current(self) -> bool:
        """Return whether the exact normalized bundled tree is installed."""

        return self.state is ReferenceSkillState.CURRENT

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable lifecycle payload."""

        return {
            "state": self.state.value,
            "reason": self.reason.value,
            "path": str(self.path),
            "details": list(self.details),
            "current": self.current,
        }


@dataclass(frozen=True)
class ReferenceSkillProvisionResult:
    """Safe installation attempt plus its authoritative live verification.

    ``state``/``reason`` describe the provisioning outcome used for profile
    selection. ``verification`` retains the post-attempt live-tree result when
    an installation write or exception makes the outcome ``install_error``.
    """

    state: ReferenceSkillState
    reason: ReferenceSkillReason
    path: Path
    details: tuple[str, ...]
    verification: ReferenceSkillVerification
    report: SkillsReport | None = None

    @property
    def ok(self) -> bool:
        """Return whether installation completed and verified as current."""

        return (
            self.state is ReferenceSkillState.CURRENT
            and self.report is not None
            and self.report.ok
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable provisioning payload."""

        return {
            "ok": self.ok,
            "state": self.state.value,
            "reason": self.reason.value,
            "path": str(self.path),
            "details": list(self.details),
            "verification": self.verification.to_dict(),
            "report": self.report.to_dict() if self.report is not None else None,
        }


def list_bundled_skills(skills_root: Path | None = None) -> list[BundledSkill]:
    """Collect bundled skills in deterministic order."""
    root = skills_root if skills_root is not None else BUNDLED_SKILLS_ROOT
    if not root.is_dir():
        return []

    skills: list[BundledSkill] = []
    for skill_dir in sorted(root.iterdir(), key=lambda p: p.name):
        manifest = skill_dir / SKILL_MANIFEST_NAME
        if not skill_dir.is_dir() or not manifest.is_file():
            continue
        name, description = _parse_skill_frontmatter(read_md(manifest))
        skills.append(
            BundledSkill(
                skill_id=skill_dir.name,
                name=name or skill_dir.name,
                description=description,
                path=skill_dir,
                files=_skill_files(skill_dir),
            )
        )
    return skills


def export_skills(
    dest_dir: str | Path,
    *,
    skills: list[str] | None = None,
    force: bool = False,
    skills_root: Path | None = None,
) -> SkillsReport:
    """Copy bundled skills into ``dest_dir`` (one directory per skill).

    Existing identical files are kept, missing files are written, and
    differing files are only overwritten with ``force`` — otherwise they are
    reported as issues and the report is marked not ok. Explicit selections
    are expanded to their complete bundled dependency closure before any
    destination write. An exact ``wiki-reference`` tree is still required
    before a reference-dependent workflow is written.
    """
    dest = Path(dest_dir).expanduser()
    _ensure_safe_base(dest)
    selection = _select_skills(skills, skills_root=skills_root)
    selected = list(selection.skills)
    reference_requirement = _preflight_reference_requirement(
        selected,
        skills_root=skills_root,
    )

    report = SkillsReport(
        dest_dir=str(dest),
        requested_skills=list(selection.requested_ids),
        dependency_skills=list(selection.dependency_ids),
        skills=[skill.skill_id for skill in selected],
    )
    if not _ensure_regular_directory(dest, report=report):
        report.ok = False
        return report
    reference_verified = False
    consumers = reference_requirement or ()

    for skill in selected:
        expected_files = _expected_skill_files(skill)
        skill_target = dest / skill.skill_id
        if not _ensure_regular_directory(skill_target, root=dest, report=report):
            if reference_requirement is not None and skill.skill_id == (
                REFERENCE_SKILL_ID
            ):
                break
            continue
        for rel in expected_files:
            source = skill.path / rel
            if not _is_regular_file(source):
                _append_issue(
                    report,
                    category="bundled_file_unavailable",
                    path=source,
                    message=(
                        f"Bundled skill '{skill.skill_id}' is missing a regular "
                        f"file: {rel}."
                    ),
                )
                continue
            try:
                source_text = read_md(source)
            except OSError as exc:
                _append_issue(
                    report,
                    category="bundled_file_unavailable",
                    path=source,
                    message=f"Could not read bundled skill file '{rel}': {exc}",
                )
                continue
            canonical_source = source_text.encode("utf-8")
            target = skill_target / rel
            if not _ensure_regular_directory(
                target.parent, root=skill_target, report=report
            ):
                continue
            target_kind = _path_kind(target)
            if target_kind == "missing":
                try:
                    write_md(target, source_text)
                except OSError as exc:
                    _append_issue(
                        report,
                        category="write_failed",
                        path=target,
                        message=f"Could not write skill file '{rel}': {exc}",
                    )
                else:
                    report.operations.append(SkillOperation("write", str(target)))
                continue
            if target_kind != "file":
                _append_issue(
                    report,
                    category="unsafe_or_conflicting_entry",
                    path=target,
                    message=(
                        f"Existing path for skill '{skill.skill_id}' is not a "
                        f"regular file and was preserved: {target}."
                    ),
                )
                continue
            try:
                installed_text = read_md(target)
                installed_bytes = target.read_bytes()
            except OSError as exc:
                _append_issue(
                    report,
                    category="existing_file_unreadable",
                    path=target,
                    message=f"Could not verify existing skill file '{rel}': {exc}",
                )
                continue
            if installed_text == source_text:
                if force and installed_bytes != canonical_source:
                    try:
                        write_md(target, source_text)
                    except OSError as exc:
                        _append_issue(
                            report,
                            category="write_failed",
                            path=target,
                            message=f"Could not canonicalize skill file '{rel}': {exc}",
                        )
                    else:
                        report.operations.append(
                            SkillOperation("overwrite", str(target))
                        )
                else:
                    report.operations.append(SkillOperation("keep", str(target)))
                continue
            if force:
                try:
                    write_md(target, source_text)
                except OSError as exc:
                    _append_issue(
                        report,
                        category="write_failed",
                        path=target,
                        message=f"Could not overwrite skill file '{rel}': {exc}",
                    )
                else:
                    report.operations.append(SkillOperation("overwrite", str(target)))
                continue
            _append_issue(
                report,
                category="existing_file_differs",
                path=target,
                message=(
                    f"Existing file differs from bundled skill '{skill.skill_id}' "
                    "and was preserved; re-run with --force to overwrite it."
                ),
            )

        if skill.skill_id == REFERENCE_SKILL_ID:
            exact_reference = _skill_tree_matches(skill_target, skill)
            if not exact_reference:
                _append_issue(
                    report,
                    category="managed_tree_not_exact",
                    path=skill_target,
                    message=(
                        f"Installed skill '{skill.skill_id}' is not the exact "
                        "bundled tree; expected files remain missing or modified, "
                        "or local extra/conflicting entries were preserved."
                    ),
                )
            if reference_requirement is not None:
                if not exact_reference:
                    break
                report.operations.append(
                    SkillOperation(
                        "verify",
                        str(skill_target),
                        "Required by: " + ", ".join(consumers),
                    )
                )
                reference_verified = True

    if reference_requirement is not None and not reference_verified:
        reference_target = dest / REFERENCE_SKILL_ID
        _append_issue(
            report,
            category="required_skill_unavailable",
            path=reference_target,
            message=(
                "Selected workflow skill(s) require an exact "
                f"'{REFERENCE_SKILL_ID}' tree: {', '.join(consumers)}. "
                "The prerequisite was not current before workflow export."
            ),
        )

    report.ok = not report.issues
    return report


def install_skills(
    project_dir: str | Path = ".",
    *,
    skills: list[str] | None = None,
    force: bool = False,
    target: str | Path = DEFAULT_INSTALL_TARGET,
    skills_root: Path | None = None,
) -> SkillsReport:
    """Install bundled skills into a project's agent skills directory."""
    dest = Path(project_dir) / target
    return export_skills(
        dest,
        skills=skills,
        force=force,
        skills_root=skills_root,
    )


def install_reference_skill(
    project_dir: str | Path = ".",
    *,
    agent: str | None = None,
    force: bool = False,
    target: str | Path | None = None,
    skills_root: Path | None = None,
) -> SkillsReport:
    """Install (or refresh) the CLI-owned `wiki-reference` skill.

    The destination comes from *target* when given, otherwise from the
    *agent*'s skills directory (see :func:`skills_install_dir`).
    """
    return install_skills(
        project_dir,
        skills=[REFERENCE_SKILL_ID],
        force=force,
        target=target if target is not None else skills_install_dir(agent),
        skills_root=skills_root,
    )


def verify_reference_skill(
    project_dir: str | Path = ".",
    *,
    agent: str | None = None,
    target: str | Path | None = None,
    skills_root: Path | None = None,
) -> ReferenceSkillVerification:
    """Verify the live managed-reference tree without mutating the filesystem.

    The bundled payload is validated first. Compact rendering is safe only when
    this function returns :attr:`ReferenceSkillState.CURRENT`; every other state
    carries a stable reason and deterministic diagnostics for lifecycle callers.
    Text comparison uses :func:`read_md`, so supported encodings and line endings
    are normalized identically for source-tree and installed-wheel payloads.
    """

    installed_dir = _reference_install_path(project_dir, agent=agent, target=target)
    package_contents, package_details = _reference_package_contents(skills_root)
    if package_contents is None:
        return _reference_verification(
            ReferenceSkillState.PACKAGE_MISSING,
            installed_dir,
            package_details,
        )

    unsafe_component = first_unsafe_path_component(
        installed_dir,
        trusted_symlink_uids=frozenset(),
    )
    if unsafe_component is not None:
        return _reference_verification(
            ReferenceSkillState.INCOMPLETE,
            installed_dir,
            (f"unsafe:{unsafe_component}",),
        )
    installed_kind = _path_kind(installed_dir)
    if installed_kind == "missing":
        return _reference_verification(ReferenceSkillState.ABSENT, installed_dir)
    if installed_kind != "directory":
        return _reference_verification(
            ReferenceSkillState.INCOMPLETE,
            installed_dir,
            (f"{installed_kind}:.",),
        )
    if not _directory_ancestry_is_safe(installed_dir):
        return _reference_verification(
            ReferenceSkillState.INCOMPLETE,
            installed_dir,
            (f"unsafe:{installed_dir}",),
        )

    snapshot = _tree_snapshot(installed_dir)
    expected_files = frozenset(REFERENCE_SKILL_FILES)
    expected_directories = _reference_expected_directories()
    incomplete_details = _snapshot_details(
        snapshot,
        expected_files=expected_files,
        expected_directories=expected_directories,
    )
    if incomplete_details:
        return _reference_verification(
            ReferenceSkillState.INCOMPLETE,
            installed_dir,
            incomplete_details,
        )

    unreadable: list[str] = []
    modified: list[str] = []
    for relative in REFERENCE_SKILL_FILES:
        try:
            installed_text = read_md(installed_dir / relative)
        except (OSError, UnicodeError):
            unreadable.append(f"unreadable:{relative}")
            continue
        if installed_text != package_contents[relative]:
            modified.append(f"content_mismatch:{relative}")
    if unreadable:
        return _reference_verification(
            ReferenceSkillState.INCOMPLETE,
            installed_dir,
            unreadable,
        )
    if modified:
        return _reference_verification(
            ReferenceSkillState.LOCALLY_MODIFIED,
            installed_dir,
            modified,
        )
    return _reference_verification(ReferenceSkillState.CURRENT, installed_dir)


def provision_reference_skill(
    project_dir: str | Path = ".",
    *,
    agent: str | None = None,
    force: bool = False,
    target: str | Path | None = None,
    skills_root: Path | None = None,
) -> ReferenceSkillProvisionResult:
    """Install and verify ``wiki-reference`` without leaking routine failures."""

    return _provision_reference_skill_guarded(
        project_dir,
        agent=agent,
        force=force,
        target=target,
        skills_root=skills_root,
    )


def _provision_reference_skill_guarded(
    project_dir: str | Path = ".",
    *,
    agent: str | None = None,
    force: bool = False,
    target: str | Path | None = None,
    skills_root: Path | None = None,
    pre_mutation_check: Callable[[], None] | None = None,
) -> ReferenceSkillProvisionResult:
    """Provision after an optional caller-owned authority revalidation.

    Exceptions deriving from ``Exception`` and failed reports become structured
    results. Process-control exceptions such as ``KeyboardInterrupt`` and
    ``SystemExit`` intentionally continue to propagate. Preserved local drift or
    incomplete/unsafe trees retain their live state; actual write failures use
    the distinct ``install_error`` state.
    """

    installed_dir = _reference_install_path(project_dir, agent=agent, target=target)
    package_contents, package_details = _reference_package_contents(skills_root)
    if package_contents is None:
        verification = _reference_verification(
            ReferenceSkillState.PACKAGE_MISSING,
            installed_dir,
            package_details,
        )
        return ReferenceSkillProvisionResult(
            state=verification.state,
            reason=verification.reason,
            path=installed_dir,
            details=verification.details,
            verification=verification,
        )
    if pre_mutation_check is not None:
        pre_mutation_check()
    try:
        report = install_reference_skill(
            project_dir,
            agent=agent,
            force=force,
            target=target,
            skills_root=skills_root,
        )
    except Exception as exc:
        verification = _safe_reference_verification(
            project_dir,
            agent=agent,
            target=target,
            skills_root=skills_root,
        )
        exception_detail = f"exception:{type(exc).__name__}:{exc}"
        if verification.state is ReferenceSkillState.PACKAGE_MISSING:
            details = _merge_details(verification.details, (exception_detail,))
            return ReferenceSkillProvisionResult(
                state=verification.state,
                reason=verification.reason,
                path=installed_dir,
                details=details,
                verification=verification,
            )
        return ReferenceSkillProvisionResult(
            state=ReferenceSkillState.INSTALL_ERROR,
            reason=ReferenceSkillReason.INSTALL_ERROR,
            path=installed_dir,
            details=_merge_details(verification.details, (exception_detail,)),
            verification=verification,
        )

    verification = _safe_reference_verification(
        project_dir,
        agent=agent,
        target=target,
        skills_root=skills_root,
    )
    report_details = tuple(
        f"report:{issue.get('category', 'unknown')}:{issue.get('path', '')}"
        for issue in report.issues
    )
    details = _merge_details(verification.details, report_details)
    issue_categories = {issue.get("category") for issue in report.issues}
    inconsistent_success = report.ok and verification.state not in {
        ReferenceSkillState.CURRENT,
        ReferenceSkillState.PACKAGE_MISSING,
    }
    failed_without_live_explanation = not report.ok and (
        "write_failed" in issue_categories
        or not report.issues
        or verification.state
        in {ReferenceSkillState.ABSENT, ReferenceSkillState.CURRENT}
    )
    if inconsistent_success or failed_without_live_explanation:
        return ReferenceSkillProvisionResult(
            state=ReferenceSkillState.INSTALL_ERROR,
            reason=ReferenceSkillReason.INSTALL_ERROR,
            path=installed_dir,
            details=details,
            verification=verification,
            report=report,
        )
    return ReferenceSkillProvisionResult(
        state=verification.state,
        reason=verification.reason,
        path=installed_dir,
        details=details,
        verification=verification,
        report=report,
    )


def reference_skill_state(
    project_dir: str | Path = ".",
    *,
    agent: str | None = None,
    target: str | Path | None = None,
    skills_root: Path | None = None,
) -> str:
    """Compatibility classification: absent, unmodified, or modified.

    Extra files, missing files, or content drift against the bundled skill all
    count as modified so callers never delete local edits. New lifecycle callers
    should use :func:`verify_reference_skill` for structured states and reasons.
    """
    resolved = target if target is not None else skills_install_dir(agent)
    installed_dir = Path(project_dir) / resolved / REFERENCE_SKILL_ID
    if not _directory_ancestry_is_safe(installed_dir):
        return "modified"
    installed_kind = _path_kind(installed_dir)
    if installed_kind == "missing":
        return "absent"
    if installed_kind != "directory":
        return "modified"
    verification = verify_reference_skill(
        project_dir,
        agent=agent,
        target=target,
        skills_root=skills_root,
    )
    return "unmodified" if verification.current else "modified"


def render_report_text(report: SkillsReport, *, action: str) -> str:
    lines = [f"Skills {action}: {', '.join(report.skills) or 'none'}"]
    lines.append(
        "Requested skills: " + (", ".join(report.requested_skills) or "none")
    )
    lines.append(
        "Dependency-included skills: "
        + (", ".join(report.dependency_skills) or "none")
    )
    lines.append(f"Destination: {report.dest_dir}")
    for op in report.operations:
        lines.append(f"  {op.action.upper()} {op.path}")
    for issue in report.issues:
        lines.append(f"  ISSUE [{issue['category']}] {issue['message']}")
    lines.append("OK" if report.ok else "FAILED")
    return "\n".join(lines) + "\n"


def render_report_json(report: SkillsReport) -> str:
    return json.dumps(report.to_dict(), indent=2) + "\n"


def render_skill_list_text(skills: list[BundledSkill]) -> str:
    if not skills:
        return "No bundled skills found.\n"
    lines = []
    for skill in skills:
        lines.append(f"{skill.skill_id}: {skill.description or skill.name}")
        lines.append(f"  files: {', '.join(skill.files)}")
    return "\n".join(lines) + "\n"


def render_skill_list_json(skills: list[BundledSkill]) -> str:
    return json.dumps({"skills": [s.to_dict() for s in skills]}, indent=2) + "\n"


@dataclass(frozen=True)
class _SkillSelection:
    """One validated, dependency-closed skill selection."""

    requested_ids: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    skills: tuple[BundledSkill, ...]


def _select_skills(
    requested: list[str] | None, *, skills_root: Path | None = None
) -> _SkillSelection:
    """Resolve requested skills and their deterministic transitive closure."""

    available = list_bundled_skills(skills_root)
    if not available:
        raise SkillsError("No bundled skills are available in this installation.")

    by_id = {skill.skill_id: skill for skill in available}
    requested_ids: list[str] = []
    for skill_id in requested or list(by_id):
        if skill_id not in by_id:
            raise SkillsError(
                f"Unknown skill '{skill_id}'. Available: {', '.join(sorted(by_id))}"
            )
        if skill_id not in requested_ids:
            requested_ids.append(skill_id)

    ordered_ids: list[str] = []
    visit_state: dict[str, str] = {}
    stack: list[str] = []

    def visit(skill_id: str, *, required_by: str | None = None) -> None:
        if skill_id not in by_id:
            assert required_by is not None
            raise SkillsError(
                f"Skill dependency unavailable: '{required_by}' requires "
                f"bundled '{skill_id}'."
            )
        state = visit_state.get(skill_id)
        if state == "done":
            return
        if state == "visiting":
            cycle_start = stack.index(skill_id)
            cycle = (*stack[cycle_start:], skill_id)
            raise SkillsError(
                "Skill dependency cycle detected: " + " -> ".join(cycle) + "."
            )

        visit_state[skill_id] = "visiting"
        stack.append(skill_id)
        for dependency_id in SKILL_DEPENDENCIES.get(skill_id, ()):
            visit(dependency_id, required_by=skill_id)
        stack.pop()
        visit_state[skill_id] = "done"
        ordered_ids.append(skill_id)

    for skill_id in requested_ids:
        visit(skill_id)

    requested_set = set(requested_ids)
    dependency_ids = tuple(
        skill_id for skill_id in ordered_ids if skill_id not in requested_set
    )
    return _SkillSelection(
        requested_ids=tuple(requested_ids),
        dependency_ids=dependency_ids,
        skills=tuple(by_id[skill_id] for skill_id in ordered_ids),
    )


def _preflight_reference_requirement(
    selected: list[BundledSkill],
    *,
    skills_root: Path | None,
) -> tuple[str, ...] | None:
    """Require a current managed reference for selected dependent workflows.

    Every selection is dependency-closed. This preflight additionally proves
    the special managed reference package tree is exact before destination
    mutation, including the default all-skills operation.
    """
    consumers = tuple(
        sorted(
            skill.skill_id
            for skill in selected
            if skill.skill_id != REFERENCE_SKILL_ID
            and _declares_transitive_dependency(
                skill.skill_id,
                REFERENCE_SKILL_ID,
            )
        )
    )
    if not consumers:
        return None

    selected_ids = {skill.skill_id for skill in selected}
    if REFERENCE_SKILL_ID not in selected_ids:
        raise SkillsError(
            "Resolved skill selection omitted required bundled "
            f"'{REFERENCE_SKILL_ID}': {', '.join(consumers)}."
        )

    available = list_bundled_skills(skills_root)
    reference_skill = next(
        (skill for skill in available if skill.skill_id == REFERENCE_SKILL_ID),
        None,
    )
    if reference_skill is None:
        raise SkillsError(
            f"Selected skill(s) require bundled '{REFERENCE_SKILL_ID}', but "
            "that prerequisite is unavailable in this installation: "
            f"{', '.join(consumers)}."
        )
    if not _skill_tree_matches(reference_skill.path, reference_skill):
        raise SkillsError(
            f"Selected skill(s) require bundled '{REFERENCE_SKILL_ID}', but "
            "that prerequisite package tree is incomplete or modified: "
            f"{', '.join(consumers)}."
        )

    return consumers


def _declares_transitive_dependency(skill_id: str, dependency_id: str) -> bool:
    """Return whether the active central map links one skill to another."""

    pending = list(SKILL_DEPENDENCIES.get(skill_id, ()))
    visited: set[str] = set()
    while pending:
        candidate = pending.pop()
        if candidate == dependency_id:
            return True
        if candidate in visited:
            continue
        visited.add(candidate)
        pending.extend(SKILL_DEPENDENCIES.get(candidate, ()))
    return False


def _skill_files(skill_dir: Path) -> tuple[str, ...]:
    files = [
        path.relative_to(skill_dir).as_posix()
        for path in sorted(skill_dir.rglob("*"))
        if path.is_file()
    ]
    # SKILL.md is the manifest; keep it first for readable reports.
    files.sort(key=lambda rel: (rel != SKILL_MANIFEST_NAME, rel))
    return tuple(files)


def _expected_skill_files(skill: BundledSkill) -> tuple[str, ...]:
    if skill.skill_id == REFERENCE_SKILL_ID:
        return REFERENCE_SKILL_FILES
    return skill.files


_REFERENCE_REASONS: dict[ReferenceSkillState, ReferenceSkillReason] = {
    ReferenceSkillState.ABSENT: ReferenceSkillReason.ABSENT,
    ReferenceSkillState.CURRENT: ReferenceSkillReason.CURRENT,
    ReferenceSkillState.LOCALLY_MODIFIED: ReferenceSkillReason.LOCALLY_MODIFIED,
    ReferenceSkillState.INCOMPLETE: ReferenceSkillReason.INCOMPLETE,
    ReferenceSkillState.PACKAGE_MISSING: ReferenceSkillReason.PACKAGE_MISSING,
    ReferenceSkillState.INSTALL_ERROR: ReferenceSkillReason.INSTALL_ERROR,
}


@dataclass(frozen=True)
class _TreeSnapshot:
    files: frozenset[str]
    directories: frozenset[str]
    unsafe: tuple[str, ...] = ()
    unreadable: tuple[str, ...] = ()


def _reference_install_path(
    project_dir: str | Path,
    *,
    agent: str | None,
    target: str | Path | None,
) -> Path:
    resolved = target if target is not None else skills_install_dir(agent)
    return Path(project_dir) / resolved / REFERENCE_SKILL_ID


def _reference_verification(
    state: ReferenceSkillState,
    path: Path,
    details: tuple[str, ...] | list[str] = (),
) -> ReferenceSkillVerification:
    return ReferenceSkillVerification(
        state=state,
        reason=_REFERENCE_REASONS[state],
        path=path,
        details=_merge_details(details),
    )


def _safe_reference_verification(
    project_dir: str | Path,
    *,
    agent: str | None,
    target: str | Path | None,
    skills_root: Path | None,
) -> ReferenceSkillVerification:
    installed_dir = _reference_install_path(project_dir, agent=agent, target=target)
    try:
        return verify_reference_skill(
            project_dir,
            agent=agent,
            target=target,
            skills_root=skills_root,
        )
    except Exception as exc:
        return _reference_verification(
            ReferenceSkillState.INCOMPLETE,
            installed_dir,
            (f"verification_exception:{type(exc).__name__}:{exc}",),
        )


def _merge_details(*groups: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(sorted({detail for group in groups for detail in group}))


def _reference_expected_directories() -> frozenset[str]:
    directories: set[str] = set()
    for relative in REFERENCE_SKILL_FILES:
        parent = Path(relative).parent
        while parent != Path("."):
            directories.add(parent.as_posix())
            parent = parent.parent
    return frozenset(directories)


def _reference_package_contents(
    skills_root: Path | None,
) -> tuple[dict[str, str] | None, tuple[str, ...]]:
    root = skills_root if skills_root is not None else BUNDLED_SKILLS_ROOT
    package_dir = root / REFERENCE_SKILL_ID
    unsafe_component = first_unsafe_path_component(
        package_dir,
        trusted_symlink_uids=frozenset(),
    )
    if unsafe_component is not None:
        return None, (f"package_unsafe:{unsafe_component}",)
    root_kind = _path_kind(root)
    if root_kind != "directory":
        return None, (f"package_root_{root_kind}:{root}",)
    package_kind = _path_kind(package_dir)
    if package_kind != "directory":
        return None, (f"package_{package_kind}:.",)
    if not _directory_ancestry_is_safe(package_dir):
        return None, (f"package_unsafe:{package_dir}",)

    snapshot = _tree_snapshot(package_dir)
    details = _snapshot_details(
        snapshot,
        expected_files=frozenset(REFERENCE_SKILL_FILES),
        expected_directories=_reference_expected_directories(),
        prefix="package_",
    )
    if details:
        return None, details

    contents: dict[str, str] = {}
    unreadable: list[str] = []
    for relative in REFERENCE_SKILL_FILES:
        try:
            contents[relative] = read_md(package_dir / relative)
        except (OSError, UnicodeError):
            unreadable.append(f"package_unreadable:{relative}")
    if unreadable:
        return None, _merge_details(unreadable)
    return contents, ()


def _snapshot_details(
    snapshot: _TreeSnapshot,
    *,
    expected_files: frozenset[str],
    expected_directories: frozenset[str],
    prefix: str = "",
) -> tuple[str, ...]:
    details = [f"{prefix}missing:{path}" for path in expected_files - snapshot.files]
    details.extend(f"{prefix}extra:{path}" for path in snapshot.files - expected_files)
    details.extend(
        f"{prefix}missing_directory:{path}"
        for path in expected_directories - snapshot.directories
    )
    details.extend(
        f"{prefix}extra_directory:{path}"
        for path in snapshot.directories - expected_directories
    )
    details.extend(f"{prefix}unsafe:{path}" for path in snapshot.unsafe)
    details.extend(f"{prefix}unreadable:{path}" for path in snapshot.unreadable)
    return _merge_details(details)


def _path_kind(path: Path) -> str:
    """Classify a path without following symlinks or reparse points."""

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return "missing"
    except OSError:
        return "unreadable"
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if stat.S_ISLNK(metadata.st_mode) or (
        bool(reparse_flag) and bool(attributes & reparse_flag)
    ):
        return "unsafe"
    if stat.S_ISREG(metadata.st_mode):
        return "file"
    if stat.S_ISDIR(metadata.st_mode):
        return "directory"
    return "unsafe"


def _is_regular_file(path: Path) -> bool:
    return _path_kind(path) == "file" and _directory_ancestry_is_safe(path.parent)


def _directory_ancestry_is_safe(path: Path) -> bool:
    """Reject unsafe aliases or non-directories in the existing path prefix."""

    return _nearest_existing_directory(path) is not None


def _nearest_existing_directory(path: Path) -> Path | None:
    """Return the nearest existing directory after strict alias validation."""

    # Empty trusted-owner policy remains fail-closed for every user-controlled
    # link while letting the shared path walker process lexical parent
    # components and root-owned platform aliases in their real sequence.
    if first_unsafe_path_component(path, trusted_symlink_uids=frozenset()) is not None:
        return None
    current = path
    while not current.exists():
        if current.parent == current:
            return None
        current = current.parent
    return current if current.is_dir() else None


def _append_issue(
    report: SkillsReport,
    *,
    category: str,
    path: Path,
    message: str,
) -> None:
    identity = (category, str(path))
    if any(
        (item.get("category"), item.get("path")) == identity for item in report.issues
    ):
        return
    report.issues.append({"category": category, "path": str(path), "message": message})


def _ensure_regular_directory(
    path: Path,
    *,
    root: Path | None = None,
    report: SkillsReport,
) -> bool:
    """Create a missing directory without traversing an unsafe existing entry."""

    if root is None:
        missing: list[Path] = []
        current = path
        existing = _nearest_existing_directory(path)
        if existing is None:
            unsafe = (
                first_unsafe_path_component(
                    path,
                    trusted_symlink_uids=frozenset(),
                )
                or path
            )
            _append_issue(
                report,
                category="unsafe_or_conflicting_entry",
                path=unsafe,
                message=(
                    "Skill destination contains a symlink, reparse point, or "
                    f"non-directory entry and was preserved: {unsafe}."
                ),
            )
            return False
        while current != existing:
            missing.append(current)
            current = current.parent
        chain = tuple(reversed(missing))
    else:
        if not _ensure_regular_directory(root, report=report):
            return False
        try:
            relative = path.relative_to(root)
        except ValueError:
            _append_issue(
                report,
                category="unsafe_or_conflicting_entry",
                path=path,
                message=f"Skill destination escapes its managed root: {path}.",
            )
            return False
        chain = tuple(
            root.joinpath(*relative.parts[:index])
            for index in range(1, len(relative.parts) + 1)
        )
    for directory in chain:
        kind = _path_kind(directory)
        if kind == "missing":
            try:
                directory.mkdir()
            except OSError as exc:
                _append_issue(
                    report,
                    category="write_failed",
                    path=directory,
                    message=f"Could not create skill directory: {exc}",
                )
                return False
            continue
        if kind != "directory":
            _append_issue(
                report,
                category="unsafe_or_conflicting_entry",
                path=directory,
                message=(
                    "Skill destination contains a symlink, reparse point, or "
                    f"non-directory entry and was preserved: {directory}."
                ),
            )
            return False
    return True


def _tree_snapshot(root: Path) -> _TreeSnapshot:
    """Inventory one tree without following aliases or hiding read failures."""

    files: set[str] = set()
    directories: set[str] = set()
    unsafe: set[str] = set()
    unreadable: set[str] = set()

    def relative(path: Path) -> str:
        try:
            value = path.relative_to(root).as_posix()
        except ValueError:
            value = str(path)
        return value or "."

    def onerror(exc: OSError) -> None:
        filename = getattr(exc, "filename", None)
        unreadable.add(relative(Path(filename)) if filename else ".")

    try:
        walker = os.walk(root, topdown=True, onerror=onerror, followlinks=False)
        for directory, names, filenames in walker:
            names.sort()
            filenames.sort()
            parent = Path(directory)
            retained_names: list[str] = []
            for name in names:
                candidate = parent / name
                kind = _path_kind(candidate)
                entry = relative(candidate)
                if kind == "directory":
                    directories.add(entry)
                    retained_names.append(name)
                elif kind == "unreadable":
                    unreadable.add(entry)
                else:
                    unsafe.add(entry)
            names[:] = retained_names
            for name in filenames:
                candidate = parent / name
                kind = _path_kind(candidate)
                entry = relative(candidate)
                if kind == "file":
                    files.add(entry)
                elif kind == "unreadable":
                    unreadable.add(entry)
                else:
                    unsafe.add(entry)
    except OSError as exc:
        onerror(exc)
    return _TreeSnapshot(
        files=frozenset(files),
        directories=frozenset(directories),
        unsafe=tuple(sorted(unsafe)),
        unreadable=tuple(sorted(unreadable)),
    )


def _tree_entries(root: Path) -> tuple[set[str], set[str]] | None:
    """Return regular files/directories, rejecting every other tree entry."""

    snapshot = _tree_snapshot(root)
    if snapshot.unsafe or snapshot.unreadable:
        return None
    return set(snapshot.files), set(snapshot.directories)


def _skill_tree_matches(installed_dir: Path, skill: BundledSkill) -> bool:
    expected_files = _expected_skill_files(skill)
    if set(skill.files) != set(expected_files):
        return False
    if not _directory_ancestry_is_safe(skill.path) or not _directory_ancestry_is_safe(
        installed_dir
    ):
        return False
    installed_entries = _tree_entries(installed_dir)
    bundled_entries = _tree_entries(skill.path)
    if installed_entries is None or bundled_entries is None:
        return False
    installed_files, installed_directories = installed_entries
    bundled_files, bundled_directories = bundled_entries
    if bundled_files != set(expected_files):
        return False
    if installed_files != bundled_files or installed_directories != bundled_directories:
        return False
    try:
        return all(
            read_md(installed_dir / rel) == read_md(skill.path / rel)
            for rel in expected_files
        )
    except (OSError, UnicodeError):
        return False


def _parse_skill_frontmatter(content: str) -> tuple[str, str]:
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return "", ""
    name = ""
    description = ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, _, value = line.partition(":")
        if key.strip() == "name":
            name = value.strip()
        elif key.strip() == "description":
            description = value.strip()
    return name, description


def _ensure_safe_base(path: Path) -> None:
    require_safe_base_path(
        path,
        error=SkillsError(f"Invalid destination directory: {path}"),
    )
