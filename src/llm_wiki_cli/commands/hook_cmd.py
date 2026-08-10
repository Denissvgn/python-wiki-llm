from __future__ import annotations

import hashlib
import shlex
import sys
from pathlib import Path

from ..config import (
    AGENT_CHOICES,
    AgentConfigState,
    DEFAULT_WIKI_DIR,
    get_agent_config_path,
    inspect_config,
    require_committed_config,
    require_safe_config_path,
    validate_path,
    write_config,
)
from ..services.filesystem_guard import (
    atomic_write_executable_bytes,
    ensure_guarded_directory,
    unlink_guarded_bytes,
)
from ..services.io import first_unsafe_path_component
from ..services.paths import shell_quote
from ..services.source_selection import (
    SourceSelectionError,
    resolve_source_selection,
)

HOOK_SIGNATURE = "LLM Wiki"
_EXPECTED_HOOK_UNSET = object()

_EXACT_LEGACY_MANAGED_HOOKS = {
    "post-commit": {
        "#!/bin/sh\n# LLM Wiki old hook\n",
        "#!/bin/sh\n# LLM Wiki sync\nnohup llm-wiki trigger-agent &\n",
    },
    "pre-commit": {
        "#!/bin/sh\n# LLM Wiki\nllm-wiki lint --strict\n",
    },
}
_STATIC_LEGACY_HOOK_DIGESTS = {
    "post-commit": {
        "dd4ec6c0dd3b9e143e9f6cb2c0ab283168c32dd8aa2221a4c9afba66eb1521f8",
    },
    "pre-commit": {
        "1009dce4df2de3bc54f76b68c65b4ae7cfdce07383c12aa6f162a8a51b04b7b1",
        "ae5d94d8424b804ee40e239d0a98d1bd3feebce3899a34a2191773e6730d7101",
    },
    "pre-push": {
        "eb628d35ea158e86c0bd762abae8f7f11e383e4dd4a321e6601eae12e3b794d6",
        "5f093180f9d4614a3d642270f4ddd2d278abb1e82c413174144c201b3e69d37d",
    },
}
_DYNAMIC_LEGACY_HOOK_SKELETON_DIGESTS = {
    "post-commit": {
        "557e1fb4a0a6f9a119ae2312f627ed928f4a8c64c684d6361a79b613100f5c3d",
        "80f2fe89755b9f8644735429d29df37ed7252fbd86eb284ed9838f4b36505003",
        "b38753e51c2187334356352f0e69b15f318d57959d347fdf348510440c7269fd",
        "6281bc04963e62a7c54920aa43903a158ace661eb9583f0a3ffcee777a2ac7f9",
        "e090c34d8f2773e670952e4fc60a630b7794bfd9c4d386e5aaf8350673c10aa9",
        "3d2150689b0026c14a8c092a5a90c71cdcd9d73872dc0e2e433519df8ce86609",
        "cd30a93bb8a1242d6b6b7d10319ebb98fbd1b6907699cbb83064fdb03cbb0b4c",
        "c36adc4813369856e7e2a2609bfc8b436f1d78a2fa1bb0099dec44845f69d420",
    }
}


def _read_agent_config(wiki_dir: str) -> str | None:
    """Read the agent name persisted by `llm-wiki init`."""
    inspection = inspect_config(wiki_dir)
    if inspection.state in {AgentConfigState.VALID, AgentConfigState.LEGACY}:
        agent = inspection.data.get("agent")
        return str(agent) if isinstance(agent, str) else None
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
    require_safe_hook_arguments(wiki_dir, source_selection)
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
    require_safe_hook_arguments(wiki_dir, source_selection)
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


def require_safe_hook_arguments(
    wiki_dir: str | Path,
    source_selection: str | Path | None = None,
) -> None:
    """Reject control characters that cannot round-trip through hook scripts."""

    for label, value in (
        ("--wiki-dir", wiki_dir),
        ("--source-selection", source_selection),
    ):
        if value is None:
            continue
        text = str(value)
        if text.splitlines(keepends=True) != [text] or any(
            ord(character) < 32 or ord(character) == 127 for character in text
        ):
            raise ValueError(f"{label} must not contain control characters")


def _hook_parameters_are_within_project(
    wiki_dir: str,
    source_selection: str | None = None,
) -> bool:
    try:
        require_safe_hook_arguments(wiki_dir, source_selection)
        validate_path(wiki_dir, "--wiki-dir")
        if source_selection is not None:
            validate_path(source_selection, "--source-selection")
    except ValueError:
        return False
    return True


def _current_post_commit_parameters(content: str) -> tuple[str, str | None] | None:
    lines = [line for line in content.splitlines() if "generate-prompt" in line]
    if len(lines) != 1:
        return None
    try:
        tokens = shlex.split(lines[0])
    except ValueError:
        return None
    if tokens[:3] != ["$CLI", "generate-prompt", "--wiki-dir"]:
        return None
    if len(tokens) == 6 and tokens[4:] == [
        "--output",
        ".git/llm-wiki-prompt.txt",
    ]:
        return tokens[3], None
    if (
        len(tokens) == 8
        and tokens[4] == "--source-selection"
        and tokens[6:]
        == [
            "--output",
            ".git/llm-wiki-prompt.txt",
        ]
    ):
        return tokens[3], tokens[5]
    return None


def _current_pre_commit_parameters(content: str) -> tuple[str, str | None] | None:
    lines = [line for line in content.splitlines() if '"$CLI" lint --strict' in line]
    if len(lines) != 1:
        return None
    try:
        tokens = shlex.split(lines[0])
    except ValueError:
        return None
    if tokens[:4] != ["$CLI", "lint", "--strict", "--wiki-dir"]:
        return None
    if len(tokens) == 7 and tokens[5:] == ["--src-dir", "."]:
        return tokens[4], None
    if (
        len(tokens) == 9
        and tokens[5:7] == ["--src-dir", "."]
        and tokens[7] == "--source-selection"
    ):
        return tokens[4], tokens[8]
    return None


def _legacy_ide_post_commit(wiki_dir: str) -> str:
    quoted_wiki_dir = shell_quote(wiki_dir)
    return f"""#!/bin/sh

# LLM Wiki -- IDE Agent Prompt Helper (Post-Commit Hook)
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

"$CLI" generate-prompt --wiki-dir {quoted_wiki_dir} --output .git/llm-wiki-prompt.txt

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


def _legacy_auto_sync_post_commit(agent: str, wiki_dir: str) -> str:
    quoted_agent = shell_quote(agent)
    quoted_wiki_dir = shell_quote(wiki_dir)
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
LLM_WIKI_MAX_PROMPT_BYTES="${{LLM_WIKI_MAX_PROMPT_BYTES:-2000000}}"

# Find the virtual environment if it exists, or run globally
if [ -f ".venv/bin/llm-wiki" ]; then
    CLI=".venv/bin/llm-wiki"
else
    CLI="llm-wiki"
fi

nohup "$CLI" trigger-agent --agent {quoted_agent} --wiki-dir {quoted_wiki_dir} --timeout "$LLM_WIKI_TIMEOUT" --max-diff-lines "$LLM_WIKI_MAX_DIFF" --max-prompt-bytes "$LLM_WIKI_MAX_PROMPT_BYTES" > .git/llm-wiki-sync.log 2>&1 &
"""


def _legacy_auto_sync_parameters(content: str) -> tuple[str, str] | None:
    lines = [
        line for line in content.splitlines() if 'nohup "$CLI" trigger-agent' in line
    ]
    if len(lines) != 1:
        return None
    try:
        tokens = shlex.split(lines[0])
    except ValueError:
        return None
    expected_tail = [
        "--timeout",
        "$LLM_WIKI_TIMEOUT",
        "--max-diff-lines",
        "$LLM_WIKI_MAX_DIFF",
        "--max-prompt-bytes",
        "$LLM_WIKI_MAX_PROMPT_BYTES",
        ">",
        ".git/llm-wiki-sync.log",
        "2>&1",
        "&",
    ]
    if (
        len(tokens) == 17
        and tokens[:4] == ["nohup", "$CLI", "trigger-agent", "--agent"]
        and tokens[4] in AGENT_CHOICES
        and tokens[5] == "--wiki-dir"
        and tokens[7:] == expected_tail
    ):
        if not _hook_parameters_are_within_project(tokens[6]):
            return None
        return tokens[4], tokens[6]
    return None


def _is_legacy_trigger_invocation(line: str) -> bool:
    try:
        tokens = shlex.split(line)
    except ValueError:
        return False
    if tokens[:4] != ["nohup", "$CLI", "trigger-agent", "--agent"]:
        return False
    agent = tokens[4] if len(tokens) > 4 else None
    if agent not in AGENT_CHOICES:
        return False
    index = 5
    wiki_dir: str | None = None
    if len(tokens) > index and tokens[index] == "--wiki-dir":
        if len(tokens) <= index + 1:
            return False
        wiki_dir = tokens[index + 1]
        index += 2
    expected = [
        "--timeout",
        "$LLM_WIKI_TIMEOUT",
        "--max-diff-lines",
        "$LLM_WIKI_MAX_DIFF",
    ]
    if tokens[index : index + len(expected)] != expected:
        return False
    index += len(expected)
    if tokens[index : index + 2] == [
        "--max-prompt-bytes",
        "$LLM_WIKI_MAX_PROMPT_BYTES",
    ]:
        index += 2
    if tokens[index:] != [
        ">",
        ".git/llm-wiki-sync.log",
        "2>&1",
        "&",
    ]:
        return False
    if wiki_dir is not None and not _hook_parameters_are_within_project(wiki_dir):
        return False

    quoted_agent = shell_quote(agent)
    base_prefixes = (
        f'nohup "$CLI" trigger-agent --agent {quoted_agent}',
        f"nohup $CLI trigger-agent --agent {quoted_agent}",
    )
    wiki_segment = (
        f" --wiki-dir {shell_quote(wiki_dir)}" if wiki_dir is not None else ""
    )
    base_tail = ' --timeout "$LLM_WIKI_TIMEOUT" --max-diff-lines "$LLM_WIKI_MAX_DIFF"'
    prompt_tail = ' --max-prompt-bytes "$LLM_WIKI_MAX_PROMPT_BYTES"'
    redirect = " > .git/llm-wiki-sync.log 2>&1 &"
    return line in {
        prefix + wiki_segment + base_tail + suffix + redirect
        for prefix in base_prefixes
        for suffix in ("", prompt_tail)
    }


def _is_legacy_prompt_invocation(line: str, content: str) -> bool:
    parameters = _current_post_commit_parameters(content)
    if parameters is None:
        return False
    wiki_dir, source_selection = parameters
    if not _hook_parameters_are_within_project(wiki_dir, source_selection):
        return False
    selection = (
        f" --source-selection {shell_quote(source_selection)}"
        if source_selection is not None
        else ""
    )
    suffix = " --output .git/llm-wiki-prompt.txt"
    return line in {
        prefix
        + " generate-prompt --wiki-dir "
        + shell_quote(wiki_dir)
        + selection
        + suffix
        for prefix in ("$CLI", '"$CLI"')
    }


def _legacy_skeleton_digest(name: str, content: str) -> str | None:
    lines = content.splitlines(keepends=True)
    matches = [
        index
        for index, line in enumerate(lines)
        if "generate-prompt" in line or "trigger-agent" in line
    ]
    if len(matches) != 1:
        return None
    invocation = lines[matches[0]].rstrip("\r\n")
    if "generate-prompt" in invocation:
        if not _is_legacy_prompt_invocation(invocation, content):
            return None
    elif not _is_legacy_trigger_invocation(invocation):
        return None
    lines[matches[0]] = "__LLM_WIKI_INVOCATION__\n"
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def is_managed_hook_content(name: str, content: str) -> bool:
    """Return whether ``content`` exactly matches a recognized managed hook."""

    if content in _EXACT_LEGACY_MANAGED_HOOKS.get(name, set()):
        return True
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if digest in _STATIC_LEGACY_HOOK_DIGESTS.get(name, set()):
        return True
    if name == "post-commit":
        parameters = _current_post_commit_parameters(content)
        if parameters is not None:
            wiki_dir, source_selection = parameters
            if not _hook_parameters_are_within_project(
                wiki_dir,
                source_selection,
            ):
                return False
            try:
                if content == _build_ide_post_commit(
                    wiki_dir,
                    source_selection=source_selection,
                ):
                    return True
            except ValueError:
                return False
            if source_selection is None and content == _legacy_ide_post_commit(
                wiki_dir
            ):
                return True
        legacy_parameters = _legacy_auto_sync_parameters(content)
        if legacy_parameters is not None and content == _legacy_auto_sync_post_commit(
            *legacy_parameters
        ):
            return True
        skeleton = _legacy_skeleton_digest(name, content)
        return skeleton in _DYNAMIC_LEGACY_HOOK_SKELETON_DIGESTS.get(name, set())
    if name == "pre-commit":
        parameters = _current_pre_commit_parameters(content)
        if parameters is None:
            return False
        wiki_dir, source_selection = parameters
        if not _hook_parameters_are_within_project(wiki_dir, source_selection):
            return False
        try:
            return content == _build_validation_pre_commit(
                wiki_dir,
                source_selection=source_selection,
            )
        except ValueError:
            return False
    return False


def require_safe_hook_paths() -> None:
    """Reject redirected, non-regular, or unreadable managed hook paths."""

    git_dir = Path(".git")
    if not git_dir.exists() and not git_dir.is_symlink():
        return
    hooks_dir = git_dir / "hooks"
    candidates = (
        git_dir,
        hooks_dir,
        hooks_dir / "post-commit",
        hooks_dir / "pre-commit",
    )
    for candidate in candidates:
        unsafe = first_unsafe_path_component(candidate)
        if unsafe is not None:
            raise ValueError(f"managed hook path contains unsafe component: {unsafe}")
    for directory in (git_dir, hooks_dir):
        if directory.exists() and not directory.is_dir():
            raise ValueError(
                f"managed hook directory must be a regular directory: {directory}"
            )
    for hook in candidates[2:]:
        if not hook.exists():
            continue
        if not hook.is_file():
            raise ValueError(f"managed hook must be a regular file: {hook}")
        try:
            hook.read_bytes()
        except OSError as exc:
            raise ValueError(f"managed hook is unreadable: {hook}") from exc


def require_hook_installable(
    hooks_dir: Path,
    name: str,
    *,
    force: bool,
) -> bytes | None:
    """Reject a custom hook collision before any lifecycle mutation."""

    require_safe_hook_paths()
    hook_path = hooks_dir / name
    if not hook_path.exists():
        return None
    existing_bytes = hook_path.read_bytes()
    existing = existing_bytes.decode("utf-8", errors="replace")
    if not is_managed_hook_content(name, existing) and not force:
        print(
            f"Error: {hook_path} already exists and does not look like an LLM Wiki hook.\n"
            "Use --force to replace it intentionally.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return existing_bytes


def _install_hook(
    hooks_dir: Path,
    name: str,
    content: str,
    *,
    force: bool = False,
    expected_existing: bytes | None | object = _EXPECTED_HOOK_UNSET,
) -> None:
    """Write a hook file and make it executable."""
    hook_path = hooks_dir / name
    if expected_existing is _EXPECTED_HOOK_UNSET:
        expected_existing = require_hook_installable(
            hooks_dir,
            name,
            force=force,
        )
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    target = Path.cwd().resolve() / hook_path
    try:
        atomic_write_executable_bytes(
            target,
            normalized.encode("utf-8"),
            expected_existing=expected_existing,
        )
        require_safe_hook_paths()
    except (OSError, ValueError) as exc:
        print(f"Error: cannot safely install managed hook {hook_path}: {exc}")
        raise SystemExit(2) from exc
    print(f"  Installed: {hook_path}")


def run(args):
    git_dir = Path(".git")
    if not git_dir.exists() and not git_dir.is_symlink():
        print(
            "Error: No .git directory found. Are you in the root of a git repository?"
        )
        sys.exit(1)

    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")
    try:
        require_safe_hook_arguments(wiki_dir)
        require_safe_hook_paths()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    hooks_dir = git_dir / "hooks"
    force = bool(getattr(args, "force", False))
    post_commit_before = require_hook_installable(
        hooks_dir,
        "post-commit",
        force=force,
    )
    pre_commit_before: bytes | None | object = _EXPECTED_HOOK_UNSET
    if getattr(args, "enable_validation", False):
        pre_commit_before = require_hook_installable(
            hooks_dir,
            "pre-commit",
            force=force,
        )

    config_inspection = inspect_config(wiki_dir)
    if config_inspection.state is AgentConfigState.INVALID:
        if config_inspection.reason == "multiple-agent-config-homes":
            print(
                "Error: both .git/.llm-wiki-agent and "
                f"{Path(wiki_dir) / '.llm-wiki-agent'} exist; inspect and preserve "
                "both, select the authoritative config, and move the other aside "
                "before installing hooks",
                file=sys.stderr,
            )
            raise SystemExit(2)
        print(
            "Error: local agent config must be inspected and repaired or moved "
            f"aside before installing hooks ({config_inspection.reason}; "
            f"{config_inspection.path})",
            file=sys.stderr,
        )
        raise SystemExit(2)
    stored = dict(config_inspection.data)
    canonical_config_path = get_agent_config_path(wiki_dir)
    canonical_config_snapshot = (
        config_inspection.raw_bytes
        if config_inspection.path == canonical_config_path
        else None
    )
    migrated_config_path = (
        config_inspection.path
        if config_inspection.path != canonical_config_path
        and config_inspection.state in {AgentConfigState.VALID, AgentConfigState.LEGACY}
        else None
    )
    migrated_config_bytes = (
        config_inspection.raw_bytes if migrated_config_path is not None else None
    )
    requested_selection = getattr(args, "source_selection", None)
    if requested_selection is not None:
        try:
            require_safe_config_path(wiki_dir)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
    stored_selection = stored.get("source_selection")
    if stored_selection is not None and not isinstance(stored_selection, str):
        print("Error: stored source_selection must be a string", file=sys.stderr)
        raise SystemExit(2)
    selection_override = (
        requested_selection if requested_selection is not None else stored_selection
    )
    try:
        selection_policy = resolve_source_selection(".", selection_override)
    except SourceSelectionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    source_selection = selection_policy.path if selection_policy is not None else None
    try:
        require_safe_hook_arguments(wiki_dir, source_selection)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    try:
        ensure_guarded_directory(Path.cwd().resolve() / hooks_dir)
    except OSError as exc:
        print(f"Error: cannot safely create managed hooks directory: {exc}")
        raise SystemExit(2) from exc

    # Resolve agent only for user-facing status. Managed hooks no longer launch
    # CLI agents directly.
    agent = getattr(args, "agent", None)
    if not agent:
        stored_agent = stored.get("agent")
        agent = (
            str(stored_agent)
            if config_inspection.state
            in {AgentConfigState.VALID, AgentConfigState.LEGACY}
            and isinstance(stored_agent, str)
            else None
        )

    _install_hook(
        hooks_dir,
        "post-commit",
        _build_ide_post_commit(
            wiki_dir,
            source_selection=source_selection,
        ),
        force=force,
        expected_existing=post_commit_before,
    )
    if getattr(args, "enable_validation", False):
        _install_hook(
            hooks_dir,
            "pre-commit",
            _build_validation_pre_commit(
                wiki_dir,
                source_selection=source_selection,
            ),
            force=force,
            expected_existing=pre_commit_before,
        )
    if requested_selection is not None:
        stored["source_selection"] = source_selection
        try:
            write_config(
                wiki_dir,
                stored,
                expected_existing=canonical_config_snapshot,
            )
            if migrated_config_path is not None and migrated_config_bytes is not None:
                migrated_absolute = (
                    migrated_config_path
                    if migrated_config_path.is_absolute()
                    else Path.cwd().resolve() / migrated_config_path
                )
                unlink_guarded_bytes(
                    migrated_absolute,
                    expected=migrated_config_bytes,
                )
            require_committed_config(wiki_dir, stored)
        except (OSError, ValueError) as exc:
            print(f"Error: cannot safely persist source selection: {exc}")
            raise SystemExit(2) from exc
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
        "You can also generate it manually at any time:\n" + manual_command
    )

    print("\nHook installation complete.")
