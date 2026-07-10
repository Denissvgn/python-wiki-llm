from __future__ import annotations

from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, IDE_AGENTS, read_config, get_agent_config_path
from ..services import circuit_breaker
from ..services.skills import reference_skill_state
from ..services.wiki_surface import PageKind, canonical_path, iter_page_kinds


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


def run(args) -> None:
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    wiki_path = Path(wiki_dir)
    git_dir = Path(".git")

    print("LLM Wiki Status")
    print("=" * 40)

    # Wiki directory
    if wiki_path.exists():
        print(f"Wiki directory:  {wiki_dir} (exists)")
        for entry in iter_page_kinds():
            label = _status_label(entry.kind, entry.label)
            count = _count_surface_pages(wiki_path, entry)
            print(f"  {label + ':':<15}{count}")
        print(f"  {'Architecture pages:':<15}{_architecture_page_count(wiki_path)}")
    else:
        print(f"Wiki directory:  {wiki_dir} (not found)")

    # Agent config
    agent_config = get_agent_config_path(wiki_dir)
    config = read_config(wiki_dir)
    if agent_config.exists():
        agent = config.get("agent", "unknown")
        mode = "IDE" if agent in IDE_AGENTS else "CLI"
        print(f"Agent:           {agent} ({mode})")
        hints = config.get("quality_hints", True)
        print(f"Quality hints:   {'enabled' if hints else 'disabled'}")
    else:
        print("Agent:           not configured (run `llm-wiki init --agent <agent>`)")

    # Reference skill (the constraint block points at it); its home follows
    # the configured agent
    skill_state = reference_skill_state(agent=config.get("agent"))
    if skill_state == "unmodified":
        print("Reference skill: wiki-reference (current)")
    elif skill_state == "modified":
        print(
            "Reference skill: wiki-reference differs from bundled\n"
            "                 Run `llm-wiki upgrade` or "
            "`llm-wiki skills install --force` to refresh"
        )
    else:
        print(
            "Reference skill: not installed "
            "(run `llm-wiki init` or `llm-wiki skills install`)"
        )

    # Hooks
    hooks_dir = git_dir / "hooks"
    if hooks_dir.exists():
        installed = []
        for hook_name in ["post-commit", "pre-commit", "pre-push"]:
            hook_file = hooks_dir / hook_name
            if hook_file.exists():
                content = hook_file.read_text(encoding="utf-8")
                if "LLM Wiki" in content:
                    installed.append(hook_name)
        if installed:
            print(f"Hooks:           {', '.join(installed)}")
        else:
            print("Hooks:           none installed")
    else:
        print("Hooks:           no .git/hooks directory")

    # Circuit breaker
    if git_dir.exists():
        state = circuit_breaker.load_state(git_dir)
        breaker_state = state.get("state", "closed")
        failures = state.get("consecutive_failures", 0)
        if breaker_state == "open":
            print(f"Circuit breaker: OPEN ({failures} consecutive failures)")
            print(
                "                 Run `llm-wiki trigger-agent --reset-breaker` to re-enable"
            )
        else:
            print(f"Circuit breaker: closed ({failures} recent failures)")
    else:
        print("Circuit breaker: no .git directory")
