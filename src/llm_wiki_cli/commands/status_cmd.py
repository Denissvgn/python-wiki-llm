from __future__ import annotations

import json
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, IDE_AGENTS, read_config, get_agent_config_path
from ..services import circuit_breaker


def run(args) -> None:
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    wiki_path = Path(wiki_dir)
    git_dir = Path(".git")

    print("LLM Wiki Status")
    print("=" * 40)

    # Wiki directory
    if wiki_path.exists():
        entity_count = len(list((wiki_path / "entities").glob("*.md"))) if (wiki_path / "entities").exists() else 0
        module_count = len(list((wiki_path / "modules").glob("*.md"))) if (wiki_path / "modules").exists() else 0
        workflow_count = len(list((wiki_path / "workflows").glob("*.md"))) if (wiki_path / "workflows").exists() else 0
        print(f"Wiki directory:  {wiki_dir} (exists)")
        print(f"  Entities:      {entity_count}")
        print(f"  Modules:       {module_count}")
        print(f"  Workflows:     {workflow_count}")
    else:
        print(f"Wiki directory:  {wiki_dir} (not found)")

    # Agent config
    agent_config = get_agent_config_path(wiki_dir)
    if agent_config.exists():
        config = read_config(wiki_dir)
        agent = config.get("agent", "unknown")
        mode = "IDE" if agent in IDE_AGENTS else "CLI"
        print(f"Agent:           {agent} ({mode})")
        hints = config.get("quality_hints", True)
        print(f"Quality hints:   {'enabled' if hints else 'disabled'}")
    else:
        print("Agent:           not configured (run `llm-wiki init --agent <agent>`)")

    # Hooks
    hooks_dir = git_dir / "hooks"
    if hooks_dir.exists():
        installed = []
        for hook_name in ["post-commit", "pre-commit", "pre-push"]:
            hook_file = hooks_dir / hook_name
            if hook_file.exists():
                content = hook_file.read_text()
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
            print("                 Run `llm-wiki trigger-agent --reset-breaker` to re-enable")
        else:
            print(f"Circuit breaker: closed ({failures} recent failures)")
    else:
        print("Circuit breaker: no .git directory")
