#!/bin/sh

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
