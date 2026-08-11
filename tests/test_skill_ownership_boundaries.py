"""Executable ownership contracts for hub aggregation and site publication."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

from llm_wiki_cli import cli
from llm_wiki_cli.services.skills import BUNDLED_SKILLS_ROOT, list_bundled_skills


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HUB_ROOT = BUNDLED_SKILLS_ROOT / "doc-hub"
PUBLISH_ROOT = BUNDLED_SKILLS_ROOT / "publish-docs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _combined(root: Path) -> str:
    return f"{_read(root / 'SKILL.md')}\n{_read(root / 'reference.md')}"


def _bash_commands(markdown: str) -> list[str]:
    commands: list[str] = []
    for block in re.findall(r"```bash\n(.*?)```", markdown, flags=re.DOTALL):
        pending = ""
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            pending = f"{pending} {line}".strip()
            if pending.endswith("\\"):
                pending = pending[:-1].rstrip()
                continue
            if pending.startswith("llm-wiki "):
                commands.append(pending)
            pending = ""
    return commands


def _parse(command: str):
    argv = shlex.split(command)
    assert argv[0] == "llm-wiki"
    return cli._build_parser().parse_args(argv[1:])


def test_hub_aggregation_and_publication_build_ownership_are_disjoint() -> None:
    hub = _combined(HUB_ROOT)
    publish = _combined(PUBLISH_ROOT)

    assert "site export --wiki-root" in hub
    assert "site check --wiki-root" in hub
    assert "multi-wiki source selection, aggregation, hub export" in hub
    assert "mkdocs build" not in hub
    assert "npm run build" not in hub

    assert not any(
        "site export --wiki-root" in command for command in _bash_commands(publish)
    )
    assert "site check --wiki-root" in publish
    assert "single-wiki publication export, builder detection" in publish
    assert "mkdocs build" in publish
    assert "npm run build" in publish
    assert "confirm with the user before doing it" in publish


def test_hub_handoff_routes_common_policy_without_repeating_native_table() -> None:
    hub_manifest = _read(HUB_ROOT / "SKILL.md")
    hub_reference = _read(HUB_ROOT / "reference.md")
    publish_manifest = _read(PUBLISH_ROOT / "SKILL.md")
    publish_reference = _read(PUBLISH_ROOT / "reference.md")

    for manifest in (hub_manifest, publish_manifest):
        normalized = " ".join(manifest.split())
        assert ".claude/skills/wiki-reference/references/knowledge-consumption.md" in manifest
        assert ".llm-wiki/skills/wiki-reference/references/knowledge-consumption.md" in manifest
        assert ".claude/skills/wiki-reference/references/publishing.md" in manifest
        assert ".llm-wiki/skills/wiki-reference/references/publishing.md" in manifest
        assert ".claude/skills/wiki-reference/references/resources-context.md" in manifest
        assert ".llm-wiki/skills/wiki-reference/references/resources-context.md" in manifest
        assert "supervisor owns fan-out" in normalized
        assert "repository-handoff.md" not in manifest

    assert "../wiki-reference/references/knowledge-consumption.md" in hub_reference
    assert "../wiki-reference/references/publishing.md" in hub_reference
    assert "../wiki-reference/references/resources-context.md" in hub_reference
    assert "| `ready`" not in hub_reference
    assert "| `degraded`" not in hub_reference
    assert "../wiki-reference/references/knowledge-consumption.md" in publish_reference
    assert "../wiki-reference/references/publishing.md" in publish_reference
    assert "../wiki-reference/references/resources-context.md" in publish_reference
    assert "| `ready`" not in publish_reference
    assert "| `degraded`" not in publish_reference


def test_existing_hub_cli_parses_while_skill_handoff_changes() -> None:
    args = _parse(
        "llm-wiki site export --wiki-root sources/code_wikis --out-dir site "
        "--format docusaurus --profile reference --front-matter "
        "--output-format json"
    )
    assert args.command == "site"
    assert args.site_action == "export"
    assert args.wiki_root == "sources/code_wikis"

    publish_hub_checks = [
        _parse(command)
        for command in _bash_commands(_read(PUBLISH_ROOT / "SKILL.md"))
        if "site check --wiki-root" in command
    ]
    assert len(publish_hub_checks) == 1
    assert publish_hub_checks[0].site_action == "check"
    assert publish_hub_checks[0].profile == "reference"
    assert publish_hub_checks[0].link_mode == "http"


def test_public_migration_guidance_matches_skill_ownership() -> None:
    readme = _read(PROJECT_ROOT / "README.md")
    changelog = _read(PROJECT_ROOT / "CHANGELOG.md")

    for text in (readme, changelog):
        normalized = " ".join(text.split())
        assert "`doc-hub`" in normalized
        assert "`publish-docs`" in normalized
        assert "public" in normalized and "CLI" in normalized
    assert "No durable authored hub-overview surface exists" in readme
    assert "move only their aggregation/export/first-check stage" in readme
    assert "move only their hub aggregation stage" in " ".join(changelog.split())


def test_hub_and_publication_descriptions_are_bounded_and_trigger_specific() -> None:
    by_id = {skill.skill_id: skill for skill in list_bundled_skills()}
    hub = by_id["doc-hub"].description
    publish = by_id["publish-docs"].description

    assert 25 <= len(hub.split()) <= 40
    assert 25 <= len(publish.split()) <= 40
    assert "Aggregate two or more" in hub
    assert "never invent" in hub
    assert "publishable site" in publish
    assert "never aggregate" in publish
