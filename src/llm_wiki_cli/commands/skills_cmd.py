"""Commands for listing, exporting, and installing bundled agent skills."""

from __future__ import annotations

import sys

from ..config import (
    DEFAULT_WIKI_DIR,
    get_agent_config_path,
    read_config,
    validate_path,
)
from ..services.skills import (
    DEFAULT_INSTALL_TARGET,
    SkillsError,
    export_skills,
    install_skills,
    list_bundled_skills,
    render_report_json,
    render_report_text,
    render_skill_list_json,
    render_skill_list_text,
    skills_install_dir,
)


def _default_install_dest() -> str:
    """Resolve the install destination from the configured agent.

    Unconfigured projects keep the historical `.claude/skills` default.
    """
    if get_agent_config_path(DEFAULT_WIKI_DIR).exists():
        agent = read_config(DEFAULT_WIKI_DIR).get("agent")
        return str(skills_install_dir(agent))
    return str(DEFAULT_INSTALL_TARGET)


def _print_report(report, output_format: str, *, action: str) -> None:
    if output_format == "json":
        print(render_report_json(report), end="")
    else:
        print(render_report_text(report, action=action), end="")


def run(args) -> None:
    action = getattr(args, "skills_action", None)
    output_format = getattr(args, "format", "text")

    try:
        if action == "list":
            skills = list_bundled_skills()
            if output_format == "json":
                print(render_skill_list_json(skills), end="")
            else:
                print(render_skill_list_text(skills), end="")
            return

        if action == "export":
            report = export_skills(
                getattr(args, "dest"),
                skills=getattr(args, "skill", None),
                force=bool(getattr(args, "force", False)),
            )
            _print_report(report, output_format, action="export")
            if not report.ok:
                raise SystemExit(1)
            return

        if action == "install":
            dest = getattr(args, "dest", None) or _default_install_dest()
            validate_path(dest, "--dest")
            report = install_skills(
                ".",
                skills=getattr(args, "skill", None),
                force=bool(getattr(args, "force", False)),
                target=dest,
            )
            _print_report(report, output_format, action="install")
            if not report.ok:
                raise SystemExit(1)
            return
    except SkillsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print("Error: missing skills action.", file=sys.stderr)
    raise SystemExit(1)
