#!/bin/sh

# LLM Wiki Version Bump -- minor on every push (resets patch to 0)
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
echo "    Ignore the 'failed to push' message below -- it is expected."
echo "    (The hook must abort the original push because its bump commit"
echo "     was already pushed by the inner push above.)"

# Abort the original push (ours already went through).
# Git will print 'error: failed to push some refs' -- this is cosmetic only.
exit 1
