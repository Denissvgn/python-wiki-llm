from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

from ..config import CLI_AGENTS, DEFAULT_WIKI_DIR, IDE_AGENTS, validate_path

# Agents that support headless CLI execution (can be used in post-commit hook)
_CLI_AGENTS = set(CLI_AGENTS)
# Agents that are IDE-only and cannot run headlessly
_UI_ONLY_AGENTS = IDE_AGENTS


def _read_agent_config(wiki_dir: str) -> str | None:
    """Read the agent name persisted by `llm-wiki init`."""
    config_path = Path(wiki_dir) / ".llm-wiki-agent"
    if config_path.exists():
        return config_path.read_text().strip()
    return None


def _build_post_commit(agent: str) -> str:
    return f"""#!/bin/sh

# LLM Wiki Auto-Sync Post-Commit Hook
# Triggers the wiki update in the background so it doesn't block the developer

# Skip if this commit was made by the pre-push auto-bump
if [ -n "$LLM_WIKI_AUTO_COMMIT" ]; then
    exit 0
fi

echo "Triggering LLM Wiki subagent sync in the background..."

# Configurable via environment variables (no need to re-install hook)
LLM_WIKI_TIMEOUT="${{LLM_WIKI_TIMEOUT:-300}}"
LLM_WIKI_MAX_DIFF="${{LLM_WIKI_MAX_DIFF:-1000}}"

# Find the virtual environment if it exists, or run globally
if [ -f ".venv/bin/llm-wiki" ]; then
    CLI=".venv/bin/llm-wiki"
else
    CLI="llm-wiki"
fi

nohup "$CLI" trigger-agent --agent {agent} --timeout "$LLM_WIKI_TIMEOUT" --max-diff-lines "$LLM_WIKI_MAX_DIFF" > .git/llm-wiki-sync.log 2>&1 &
"""


def _build_ide_post_commit(wiki_dir: str) -> str:
    return f"""#!/bin/sh

# LLM Wiki — IDE Agent Prompt Helper (Post-Commit Hook)
# Generates a ready-to-paste sync prompt for IDE agents (Copilot, Cursor, etc.)
# The agent cannot run headlessly, so this hook prepares the work for you.

# Skip if this commit was made by the pre-push auto-bump
if [ -n "$LLM_WIKI_AUTO_COMMIT" ]; then
    exit 0
fi

if [ -f ".venv/bin/llm-wiki" ]; then
    CLI=".venv/bin/llm-wiki"
else
    CLI="llm-wiki"
fi

"$CLI" generate-prompt --wiki-dir {wiki_dir} --output .git/llm-wiki-prompt.txt

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  LLM Wiki: paste the sync prompt into your IDE agent chat.  ║"
echo "║  File: .git/llm-wiki-prompt.txt                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Auto-open in VS Code if running inside the integrated terminal
if [ -n "$TERM_PROGRAM" ] && [ "$TERM_PROGRAM" = "vscode" ]; then
    code .git/llm-wiki-prompt.txt 2>/dev/null || true
fi
"""


PRE_COMMIT_CONTENT = """#!/bin/sh

# LLM Wiki Version Bump — patch on every commit
# Skip if this commit was made by the pre-push minor-bump (--no-verify)

# Guard: skip if LLM_WIKI_SKIP_BUMP is set
if [ -n "$LLM_WIKI_SKIP_BUMP" ]; then
    exit 0
fi

if [ -f ".venv/bin/llm-wiki" ]; then
    CLI=".venv/bin/llm-wiki"
else
    CLI="llm-wiki"
fi

"$CLI" bump --patch --stage
"""

# ── Pre-push: minor bump + CHANGELOG stamp (opt-in) ─────────────────
PRE_PUSH_CONTENT = """#!/bin/sh

# LLM Wiki Version Bump — minor on every push (resets patch to 0)
# Also stamps the [Unreleased] CHANGELOG section with the new version.

# Guard: prevent recursion when we re-push from inside this hook
if [ -n "$LLM_WIKI_PUSHING" ]; then
    exit 0
fi

if [ -f ".venv/bin/llm-wiki" ]; then
    CLI=".venv/bin/llm-wiki"
else
    CLI="llm-wiki"
fi

# 1. Bump the version (minor) and stage the version file
"$CLI" bump --minor --stage

# 2. Stamp the CHANGELOG [Unreleased] section with the new version and stage it
"$CLI" release --stage

# Commit the version bump + CHANGELOG stamp, skipping pre-commit hook
# LLM_WIKI_AUTO_COMMIT suppresses the post-commit hook (wiki sync / IDE prompt)
LLM_WIKI_SKIP_BUMP=1 LLM_WIKI_AUTO_COMMIT=1 git commit --no-verify -m "chore: bump minor version [auto]"

# Re-push with recursion guard, including the new commit
REMOTE="$1"
# Read the ref info from stdin (passed by git)
while read local_ref local_sha remote_ref remote_sha; do
    LLM_WIKI_PUSHING=1 git push --no-verify "$REMOTE" "${local_ref}:${remote_ref}"
done

echo ""
echo "==> Push completed successfully (version bumped + CHANGELOG stamped)."
echo "    Ignore the 'failed to push' message below — it is expected."
echo "    (The hook must abort the original push because its bump commit"
echo "     was already pushed by the inner push above.)"

# Abort the original push (ours already went through).
# Git will print 'error: failed to push some refs' — this is cosmetic only.
exit 1
"""


def _install_hook(hooks_dir: Path, name: str, content: str) -> None:
    """Write a hook file and make it executable."""
    hook_path = hooks_dir / name
    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(content)
    st = os.stat(hook_path)
    os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
    print(f"  Installed: {hook_path}")


def run(args):
    git_dir = Path(".git")
    if not git_dir.exists():
        print("Error: No .git directory found. Are you in the root of a git repository?")
        sys.exit(1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    enable_versioning = getattr(args, "enable_versioning", False)
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")

    # Resolve agent: CLI override > config file > fallback
    agent = getattr(args, "agent", None)
    if not agent:
        agent = _read_agent_config(wiki_dir)
        if not agent:
            print(
                f"Warning: No agent config found at {wiki_dir}/.llm-wiki-agent.\n"
                f"Run `llm-wiki init --agent <agent>` first, or pass --agent to this command.\n"
                f"Defaulting to 'claude'."
            )
            agent = "claude"

    # IDE-only agent: install the prompt-generation hook instead of the headless sync hook
    if agent in _UI_ONLY_AGENTS:
        _install_hook(hooks_dir, "post-commit", _build_ide_post_commit(wiki_dir))
        print(f"  Agent: {agent} (IDE mode — prompt-generation hook)")
        print(
            f"\nIDE sync hook installed. After each commit, a prompt file will be generated at\n"
            f"  .git/llm-wiki-prompt.txt\n"
            f"Paste its contents into your {agent} chat to sync the wiki.\n"
            f"You can also generate it manually at any time:\n"
            f"  llm-wiki generate-prompt"
        )
        if enable_versioning:
            _install_hook(hooks_dir, "pre-push", PRE_PUSH_CONTENT)
            print("\nVersion auto-bump + CHANGELOG stamping enabled:")
            print("  • pre-push  → minor bump + stamp [Unreleased] → [new version]")
        else:
            print("\nVersion auto-bump: disabled (use --enable-versioning to activate)")
        print("\nHook installation complete.")
        return

    # CLI agent: install headless auto-sync hook with agent baked in
    _install_hook(hooks_dir, "post-commit", _build_post_commit(agent))
    print(f"  Agent: {agent}")

    if enable_versioning:
        _install_hook(hooks_dir, "pre-push", PRE_PUSH_CONTENT)
        print("\nVersion auto-bump + CHANGELOG stamping enabled:")
        print("  • pre-push  → minor bump + stamp [Unreleased] → [new version]")
    else:
        print("\nVersion auto-bump: disabled (use --enable-versioning to activate)")

    print("\nHook installation complete.")
