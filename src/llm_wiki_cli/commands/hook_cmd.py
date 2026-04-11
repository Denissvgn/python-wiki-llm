import os
from pathlib import Path
import stat

# ── Post-commit: wiki sync (always installed) ─────────────────────────
POST_COMMIT_CONTENT = """#!/bin/sh

# LLM Wiki Auto-Sync Post-Commit Hook
# Triggers the wiki update in the background so it doesn't block the developer

echo "Triggering LLM Wiki subagent sync in the background..."

# Configurable via environment variables (no need to re-install hook)
LLM_WIKI_TIMEOUT="${LLM_WIKI_TIMEOUT:-300}"
LLM_WIKI_MAX_DIFF="${LLM_WIKI_MAX_DIFF:-1000}"

# Find the virtual environment if it exists, or run globally
if [ -f ".venv/bin/llm-wiki" ]; then
    CLI=".venv/bin/llm-wiki"
else
    CLI="llm-wiki"
fi

nohup $CLI trigger-agent --timeout "$LLM_WIKI_TIMEOUT" --max-diff-lines "$LLM_WIKI_MAX_DIFF" > .git/llm-wiki-sync.log 2>&1 &
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

    # Always install post-commit (wiki sync)
    _install_hook(hooks_dir, "post-commit", POST_COMMIT_CONTENT)

    if enable_versioning:
        _install_hook(hooks_dir, "pre-commit", PRE_COMMIT_CONTENT)
        _install_hook(hooks_dir, "pre-push", PRE_PUSH_CONTENT)
        print("\nVersion auto-bump enabled:")
        print("  • pre-commit  → patch bump (0.1.5 → 0.1.6)")
        print("  • pre-push    → minor bump (0.1.6 → 0.2.0)")
    else:
        print("\nVersion auto-bump: disabled (use --enable-versioning to activate)")

    print("\nHook installation complete.")
