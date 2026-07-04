"""Bundled agent skill management for LLM Wiki.

The package ships agent skills (Claude Code-compatible ``SKILL.md``
workflow directories) under ``llm_wiki_cli/skills/``.  This module lists
them, exports them to an arbitrary destination (e.g. a personal
``~/.claude/skills`` directory), and installs them into the current
project's ``.claude/skills`` directory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .io import read_md, write_md

DEFAULT_INSTALL_TARGET = Path(".claude") / "skills"
BUNDLED_SKILLS_ROOT = Path(__file__).resolve().parents[1] / "skills"
SKILL_MANIFEST_NAME = "SKILL.md"


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
    for skill in selected:
        for rel in skill.files:
            source_text = read_md(skill.path / rel)
            target = dest / skill.skill_id / rel
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                write_md(target, source_text)
                report.operations.append(SkillOperation("write", str(target)))
            elif read_md(target) == source_text:
                report.operations.append(SkillOperation("keep", str(target)))
            elif force:
                write_md(target, source_text)
                report.operations.append(SkillOperation("overwrite", str(target)))
            else:
                report.issues.append(
                    {
                        "category": "existing_file_differs",
                        "path": str(target),
                        "message": (
                            f"Existing file differs from bundled skill "
                            f"'{skill.skill_id}'; re-run with --force to overwrite."
                        ),
                    }
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
    return export_skills(dest, skills=skills, force=force, skills_root=skills_root)


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
    if path.name in {"", ".", ".."}:
        raise SkillsError(f"Invalid destination directory: {path}")
