"""Recognize and retire historical LLM Wiki Git hooks without installing hooks.

The frozen script renderers below are ownership fingerprints for migrations.
They are never executed or written to a hook path.
"""

from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..config import AGENT_CHOICES, validate_path
from .filesystem_guard import unlink_guarded_bytes
from .io import first_unsafe_path_component
from .paths import display_project_path, shell_quote

HOOK_NAMES = ("post-commit", "pre-commit", "pre-push")


class LegacyHookError(ValueError):
    """Hook ownership or its filesystem snapshot cannot be verified safely."""


@dataclass(frozen=True)
class LegacyHookInspection:
    """Exact hook bytes classified before a lifecycle operation changes files."""

    name: str
    path: Path
    content: str
    content_bytes: bytes
    owned: bool


def _require_safe_path(path: Path) -> Path:
    unsafe = first_unsafe_path_component(path)
    if unsafe is not None:
        raise LegacyHookError(
            f"hook path contains unsafe component: {display_project_path(unsafe)}"
        )
    return path


def _git_value(root: Path, *arguments: str, optional: bool = False) -> str | None:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError as exc:
        if optional:
            return None
        raise LegacyHookError(
            "Git is required to locate linked-worktree hooks"
        ) from exc
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LegacyHookError("cannot inspect repository Git hook locations") from exc
    if optional and result.returncode == 1:
        return None
    if result.returncode != 0 or (not optional and not result.stdout.rstrip("\r\n")):
        raise LegacyHookError("cannot resolve repository Git hook locations")
    return result.stdout.removesuffix("\n").removesuffix("\r")


def _hook_directories() -> tuple[Path, ...]:
    """Locate repository-owned hooks, including a linked worktree's common Git dir."""
    root = Path.cwd().resolve()
    git_entry = _require_safe_path(root / ".git")
    if not git_entry.exists():
        return ()
    if git_entry.is_dir():
        common = git_entry
        # Also support old installations in a plain .git directory without Git.
        configured_repository = (git_entry / "HEAD").is_file()
    elif git_entry.is_file():
        location = _git_value(root, "rev-parse", "--git-common-dir")
        assert location is not None
        common = Path(os.path.abspath(root / location))
        configured_repository = True
    else:
        raise LegacyHookError("Git metadata must be a directory or a regular gitfile")
    _require_safe_path(common)
    if not common.is_dir():
        raise LegacyHookError("Git common directory is not a regular directory")
    directories = [common / "hooks"]
    if configured_repository:
        configured = _git_value(
            root, "config", "--path", "--get", "core.hooksPath", optional=True
        )
        if configured:
            custom = Path(os.path.abspath(root / configured))
            # External/global hooks are user-managed, not installation artifacts.
            if custom.is_relative_to(root) or custom.is_relative_to(common):
                directories.append(custom)
    return tuple(dict.fromkeys(directories))


def inspect_legacy_hooks() -> tuple[LegacyHookInspection, ...]:
    """Capture known hook candidates without executing them or following links."""
    inspections: list[LegacyHookInspection] = []
    for hooks_dir in _hook_directories():
        _require_safe_path(hooks_dir)
        if not hooks_dir.exists():
            continue
        if not hooks_dir.is_dir():
            raise LegacyHookError("hook directory is not a regular directory")
        for name in HOOK_NAMES:
            path = _require_safe_path(hooks_dir / name)
            if not path.exists():
                continue
            if not path.is_file():
                raise LegacyHookError(
                    f"hook path is not a regular file: {display_project_path(path)}"
                )
            try:
                content_bytes = path.read_bytes()
                content = content_bytes.decode("utf-8")
            except (OSError, UnicodeError) as exc:
                raise LegacyHookError(
                    f"hook path cannot be verified safely: {display_project_path(path)}"
                ) from exc
            inspections.append(
                LegacyHookInspection(
                    name=name,
                    path=path,
                    content=content,
                    content_bytes=content_bytes,
                    owned=is_managed_hook_content(name, content),
                )
            )
    return tuple(inspections)


def remove_legacy_hooks(
    *,
    plan: tuple[LegacyHookInspection, ...] | None = None,
    dry_run: bool = False,
) -> int:
    """Remove exact, unmodified library hooks from one rechecked ownership snapshot."""
    inspections = inspect_legacy_hooks() if plan is None else plan
    if not dry_run and inspect_legacy_hooks() != inspections:
        raise LegacyHookError("managed hook candidates changed after cleanup preflight")
    removed = 0
    for inspection in inspections:
        if not inspection.owned:
            print(
                f"  SKIP hook {inspection.name} (not ours — contains custom user content)"
            )
            continue
        if dry_run:
            print(f"  WOULD REMOVE hook: {display_project_path(inspection.path)}")
        else:
            try:
                unlink_guarded_bytes(inspection.path, expected=inspection.content_bytes)
            except OSError as exc:
                raise LegacyHookError(
                    f"managed hook changed during guarded removal: {display_project_path(inspection.path)}"
                ) from exc
            print(f"  REMOVED hook: {display_project_path(inspection.path)}")
        removed += 1
    return removed


HOOK_SIGNATURE = "LLM Wiki"

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
    """Return whether ``content`` exactly matches a recognized managed hook.

    Git hooks are shell scripts, so Windows text writes may represent their
    generated LF line endings as CRLF. Normalize only that representation at
    this ownership boundary; callers retain the original bytes for guarded
    replacement or removal.
    """

    content = content.replace("\r\n", "\n")

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
