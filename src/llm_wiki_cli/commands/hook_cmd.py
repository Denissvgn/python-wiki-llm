import os
from pathlib import Path
import stat

_DEFAULT_WIKI_DIR = "docs/llm_wiki"

# Agents that support headless CLI execution (can be used in post-commit hook)
_CLI_AGENTS = {"claude", "aider", "opencode"}
# Agents that are IDE-only and cannot run headlessly
_UI_ONLY_AGENTS = {"cursor", "copilot", "generic"}


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

nohup $CLI trigger-agent --agent {agent} --timeout "$LLM_WIKI_TIMEOUT" --max-diff-lines "$LLM_WIKI_MAX_DIFF" > .git/llm-wiki-sync.log 2>&1 &
"""

# ── Pre-commit: patch bump (opt-in) ──────────────────────────────────
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

$CLI bump --patch --stage
"""

# ── Pre-push: minor bump (opt-in) ────────────────────────────────────
PRE_PUSH_CONTENT = """#!/bin/sh

# LLM Wiki Version Bump — minor on every push (resets patch to 0)

# Guard: prevent recursion when we re-push from inside this hook
if [ -n "$LLM_WIKI_PUSHING" ]; then
    exit 0
fi

if [ -f ".venv/bin/llm-wiki" ]; then
    CLI=".venv/bin/llm-wiki"
else
    CLI="llm-wiki"
fi

$CLI bump --minor --stage

# Commit the version bump, skipping pre-commit hook to avoid extra patch bump
LLM_WIKI_SKIP_BUMP=1 git commit --no-verify -m "chore: bump minor version [auto]"

# Re-push with recursion guard, including the new commit
REMOTE="$1"
# Read the ref info from stdin (passed by git)
while read local_ref local_sha remote_ref remote_sha; do
    LLM_WIKI_PUSHING=1 git push --no-verify "$REMOTE" "$local_ref:$remote_ref"
done

# Abort the original push (ours already went through)
exit 1
"""


def _install_hook(hooks_dir: Path, name: str, content: str) -> None:
    """Write a hook file and make it executable."""
    hook_path = hooks_dir / name
    with open(hook_path, "w") as f:
        f.write(content)
    st = os.stat(hook_path)
    os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
    print(f"  Installed: {hook_path}")


def run(args):
    git_dir = Path(".git")
    if not git_dir.exists():
        print("Error: No .git directory found. Are you in the root of a git repository?")
        return

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    enable_versioning = getattr(args, "enable_versioning", False)
    wiki_dir = getattr(args, "wiki_dir", _DEFAULT_WIKI_DIR)

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

    # Warn (and skip hook install) if agent is UI-only
    if agent in _UI_ONLY_AGENTS:
        print(
            f"Note: Agent '{agent}' is a UI-based IDE assistant and does not support\n"
            f"headless background execution. The post-commit wiki sync hook will not be installed.\n"
            f"If you want background auto-sync, re-initialize with a CLI agent:\n"
            f"  llm-wiki init --agent claude\n"
            f"  llm-wiki install-hook"
        )
        if enable_versioning:
            _install_hook(hooks_dir, "pre-commit", PRE_COMMIT_CONTENT)
            _install_hook(hooks_dir, "pre-push", PRE_PUSH_CONTENT)
            print("\nVersion auto-bump hooks installed (these do not require a CLI agent).")
        return

    # Always install post-commit (wiki sync) with the resolved agent baked in
    _install_hook(hooks_dir, "post-commit", _build_post_commit(agent))
    print(f"  Agent: {agent}")

    if enable_versioning:
        _install_hook(hooks_dir, "pre-commit", PRE_COMMIT_CONTENT)
        _install_hook(hooks_dir, "pre-push", PRE_PUSH_CONTENT)
        print("\nVersion auto-bump enabled:")
        print("  • pre-commit  → patch bump (0.1.5 → 0.1.6)")
        print("  • pre-push    → minor bump (0.1.6 → 0.2.0)")
    else:
        print("\nVersion auto-bump: disabled (use --enable-versioning to activate)")

    print("\nHook installation complete.")
