from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

from ..config import (
    DEFAULT_WIKI_DIR,
    get_agent_config_path,
    read_config,
    validate_path,
    write_config,
)
from ..services.paths import shell_quote
from ..services.source_selection import (
    SourceSelectionError,
    resolve_source_selection,
)

HOOK_SIGNATURE = "LLM Wiki"


def _read_agent_config(wiki_dir: str) -> str | None:
    """Read the agent name persisted by `llm-wiki init`."""
    config_path = get_agent_config_path(wiki_dir)
    if config_path.exists():
        config = read_config(wiki_dir)
        return config.get("agent")
    return None


def _build_post_commit(
    agent: str,
    wiki_dir: str,
    source_selection: str | Path | None = None,
) -> str:
    """Build the managed post-commit hook.

    The ``agent`` argument is retained for callers from older versions; managed
    hooks now always generate a prompt for human review instead of launching an
    agent process.
    """
    _ = agent
    return _build_ide_post_commit(wiki_dir, source_selection=source_selection)


def _build_ide_post_commit(
    wiki_dir: str,
    *,
    source_selection: str | Path | None = None,
) -> str:
    quoted_wiki_dir = shell_quote(wiki_dir)
    selection_args = _source_selection_args(source_selection)
    return f"""#!/bin/sh

# LLM Wiki Prompt Post-Commit Hook
# Generates a ready-to-paste sync prompt after each commit.

# Skip if this commit was made by the pre-push auto-bump
if [ -n "$LLM_WIKI_AUTO_COMMIT" ]; then
    exit 0
fi

if [ -f ".venv/bin/llm-wiki" ]; then
    CLI=".venv/bin/llm-wiki"
else
    CLI="llm-wiki"
fi

"$CLI" generate-prompt --wiki-dir {quoted_wiki_dir}{selection_args} --output .git/llm-wiki-prompt.txt

echo ""
echo "+--------------------------------------------------------------+"
echo "|  LLM Wiki: paste the sync prompt into your IDE agent chat.  |"
echo "|  File: .git/llm-wiki-prompt.txt                             |"
echo "+--------------------------------------------------------------+"

# Auto-open in VS Code only when explicitly enabled
if [ "${{LLM_WIKI_OPEN_PROMPT:-0}}" = "1" ] && [ "$TERM_PROGRAM" = "vscode" ]; then
    code .git/llm-wiki-prompt.txt 2>/dev/null || true
fi
"""


def _build_validation_pre_commit(
    wiki_dir: str,
    *,
    source_selection: str | Path | None = None,
) -> str:
    quoted_wiki_dir = shell_quote(wiki_dir)
    selection_args = _source_selection_args(source_selection)
    return f"""#!/bin/sh

# LLM Wiki Strict Validation Pre-Commit Hook
# Opt-in guard for teams that want stale wiki coverage to block commits.

if [ -n "$LLM_WIKI_AUTO_COMMIT" ]; then
    exit 0
fi

if [ -f ".venv/bin/llm-wiki" ]; then
    CLI=".venv/bin/llm-wiki"
else
    CLI="llm-wiki"
fi

"$CLI" lint --strict --wiki-dir {quoted_wiki_dir} --src-dir .{selection_args}
"""


def _source_selection_args(source_selection: str | Path | None) -> str:
    if source_selection is None:
        return ""
    return f" --source-selection {shell_quote(source_selection)}"


def _install_hook(
    hooks_dir: Path, name: str, content: str, *, force: bool = False
) -> None:
    """Write a hook file and make it executable."""
    hook_path = hooks_dir / name
    if hook_path.exists():
        existing = hook_path.read_text(encoding="utf-8", errors="replace")
        if HOOK_SIGNATURE not in existing and not force:
            print(
                f"Error: {hook_path} already exists and does not look like an LLM Wiki hook.\n"
                "Use --force to replace it intentionally.",
                file=sys.stderr,
            )
            sys.exit(1)
    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(content)
    st = os.stat(hook_path)
    os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
    print(f"  Installed: {hook_path}")


def run(args):
    git_dir = Path(".git")
    if not git_dir.exists():
        print(
            "Error: No .git directory found. Are you in the root of a git repository?"
        )
        sys.exit(1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")
    stored = read_config(wiki_dir)
    requested_selection = getattr(args, "source_selection", None)
    stored_selection = stored.get("source_selection")
    if stored_selection is not None and not isinstance(stored_selection, str):
        print("Error: stored source_selection must be a string", file=sys.stderr)
        raise SystemExit(2)
    selection_override = (
        requested_selection
        if requested_selection is not None
        else stored_selection
    )
    try:
        selection_policy = resolve_source_selection(".", selection_override)
    except SourceSelectionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    source_selection = (
        selection_policy.path if selection_policy is not None else None
    )
    if requested_selection is not None:
        stored["source_selection"] = source_selection
        write_config(wiki_dir, stored)

    # Resolve agent only for user-facing status. Managed hooks no longer launch
    # CLI agents directly.
    agent = getattr(args, "agent", None)
    if not agent:
        agent = _read_agent_config(wiki_dir)

    _install_hook(
        hooks_dir,
        "post-commit",
        _build_ide_post_commit(
            wiki_dir,
            source_selection=source_selection,
        ),
        force=getattr(args, "force", False),
    )
    if getattr(args, "enable_validation", False):
        _install_hook(
            hooks_dir,
            "pre-commit",
            _build_validation_pre_commit(
                wiki_dir,
                source_selection=source_selection,
            ),
            force=getattr(args, "force", False),
        )
    if agent:
        print(f"  Agent preference: {agent} (prompt-generation hook)")
    else:
        print("  Agent preference: not configured (prompt-generation hook)")
    manual_command = (
        "  llm-wiki generate-prompt --wiki-dir "
        + shell_quote(wiki_dir)
        + _source_selection_args(source_selection)
    )
    print(
        "\nPrompt hook installed. After each commit, a prompt file will be generated at\n"
        "  .git/llm-wiki-prompt.txt\n"
        "Review it, then paste it into your agent chat to sync the wiki.\n"
        "You can also generate it manually at any time:\n"
        + manual_command
    )

    print("\nHook installation complete.")
