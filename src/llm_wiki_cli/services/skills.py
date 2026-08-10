"""Bundled agent skill management for LLM Wiki.

The package ships agent skills (Claude Code-compatible ``SKILL.md``
workflow directories) under ``llm_wiki_cli/skills/``.  This module lists
them, exports them to an arbitrary destination (e.g. a personal
``~/.claude/skills`` directory), and installs them into the current
project's ``.claude/skills`` directory.
"""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
    ok: bool = True
    dest_dir: str = ""
    skills: list[str] = field(default_factory=list)
    operations: list[SkillOperation] = field(default_factory=list)
    issues: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dest_dir": self.dest_dir,
            "skills": self.skills,
            "operations": [op.__dict__ for op in self.operations],
            "issues": self.issues,
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
    reported as issues and the report is marked not ok.
    """
    dest = Path(dest_dir).expanduser()
    _ensure_safe_base(dest)
    selected = _select_skills(skills, skills_root=skills_root)

    report = SkillsReport(dest_dir=str(dest), skills=[s.skill_id for s in selected])
    if not _ensure_regular_directory(dest, report=report):
        report.ok = False
        return report
    for skill in selected:
        expected_files = _expected_skill_files(skill)
        skill_target = dest / skill.skill_id
        if not _ensure_regular_directory(skill_target, root=dest, report=report):
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

        if skill.skill_id == REFERENCE_SKILL_ID and not _skill_tree_matches(
            skill_target, skill
        ):
            _append_issue(
                report,
                category="managed_tree_not_exact",
                path=skill_target,
                message=(
                    f"Installed skill '{skill.skill_id}' is not the exact bundled "
                    "tree; expected files remain missing or modified, or local "
                    "extra/conflicting entries were preserved."
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


def reference_skill_state(
    project_dir: str | Path = ".",
    *,
    agent: str | None = None,
    target: str | Path | None = None,
    skills_root: Path | None = None,
) -> str:
    """Classify the installed `wiki-reference` copy: absent, unmodified, or modified.

    Extra files, missing files, or content drift against the bundled skill all
    count as modified so callers never delete local edits.
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

    bundled = {skill.skill_id: skill for skill in list_bundled_skills(skills_root)}.get(
        REFERENCE_SKILL_ID
    )
    if bundled is None:
        return "modified"
    return "unmodified" if _skill_tree_matches(installed_dir, bundled) else "modified"


def render_report_text(report: SkillsReport, *, action: str) -> str:
    lines = [f"Skills {action}: {', '.join(report.skills) or 'none'}"]
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


def _select_skills(
    requested: list[str] | None, *, skills_root: Path | None = None
) -> list[BundledSkill]:
    available = list_bundled_skills(skills_root)
    if not available:
        raise SkillsError("No bundled skills are available in this installation.")
    if not requested:
        return available

    by_id = {skill.skill_id: skill for skill in available}
    selected: list[BundledSkill] = []
    for skill_id in requested:
        if skill_id not in by_id:
            raise SkillsError(
                f"Unknown skill '{skill_id}'. Available: {', '.join(sorted(by_id))}"
            )
        if by_id[skill_id] not in selected:
            selected.append(by_id[skill_id])
    return selected


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


def _tree_entries(root: Path) -> tuple[set[str], set[str]] | None:
    """Return regular files/directories, rejecting every other tree entry."""

    files: set[str] = set()
    directories: set[str] = set()
    try:
        for directory, names, filenames in os.walk(
            root, topdown=True, followlinks=False
        ):
            names.sort()
            filenames.sort()
            parent = Path(directory)
            for name in names:
                candidate = parent / name
                if _path_kind(candidate) != "directory":
                    return None
                directories.add(candidate.relative_to(root).as_posix())
            for name in filenames:
                candidate = parent / name
                if _path_kind(candidate) != "file":
                    return None
                files.add(candidate.relative_to(root).as_posix())
    except OSError:
        return None
    return files, directories


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
    except OSError:
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
