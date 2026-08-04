"""Read-only Git policy for handing generated wiki files to version control.

Git itself is the authority for this decision.  The source-inventory ignore
matcher intentionally implements only the subset of ignore semantics needed by
repository scans; it cannot account for repository-local excludes, configured
global excludes, linked worktrees, or paths which are already in the index.

The classifier is deliberately fail-closed.  Only an explicit ``included``
result permits callers to consider Git handoff guidance, and that result is not
itself authorization to stage or commit anything.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

_DEFAULT_TIMEOUT_SECONDS = 15.0

# These variables can cause ``git -C <root>`` to inspect a different repository
# or index.  Configuration-selection variables such as ``GIT_CONFIG_GLOBAL``
# are intentionally retained: Git's configured exclude files are part of the
# effective local policy that this module must honor.
_GIT_REPOSITORY_REDIRECTION_ENV = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_DIR",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_WORK_TREE",
    }
)


class WikiGitDisposition(str, Enum):
    """Whether Git permits wiki handoff instructions for a path."""

    INCLUDED = "included"
    IGNORED = "ignored"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class WikiGitPolicy:
    """A bounded, non-sensitive result from local Git policy evaluation."""

    disposition: WikiGitDisposition
    reason: str
    repository_root: Path | None = None
    wiki_path: str | None = None

    @property
    def allows_commit_guidance(self) -> bool:
        """Return whether callers may consider separately authorized guidance."""

        return self.disposition is WikiGitDisposition.INCLUDED


@dataclass(frozen=True)
class _GitResult:
    returncode: int | None
    stdout: str = ""
    failure: str | None = None


def classify_wiki_git_policy(
    wiki_dir: str | Path,
    *,
    cwd: Path | None = None,
    timeout: float = _DEFAULT_TIMEOUT_SECONDS,
) -> WikiGitPolicy:
    """Classify the configured wiki path using the effective Git ignore rules.

    ``wiki_dir`` may be absent: the directory spelling and a canonical
    ``index.md`` descendant are both probed so first-run prompts still respect
    directory and file ignore rules.  ``git check-ignore --no-index`` is used
    intentionally so an indexed path later covered by a repository rule is not
    given stale commit guidance.
    """

    working_directory = Path.cwd() if cwd is None else Path(cwd)
    try:
        working_directory = working_directory.resolve(strict=True)
    except (OSError, RuntimeError):
        return _indeterminate("invalid-working-directory")
    if not working_directory.is_dir():
        return _indeterminate("invalid-working-directory")

    repository = _run_git(
        working_directory,
        "rev-parse",
        "--show-toplevel",
        timeout=timeout,
    )
    if repository.failure is not None:
        return _indeterminate(repository.failure)
    if repository.returncode == 128:
        return _indeterminate("not-repository")
    if repository.returncode != 0:
        return _indeterminate("git-error")

    root_text = repository.stdout.rstrip("\r\n")
    if not root_text or "\n" in root_text or "\r" in root_text or "\0" in root_text:
        return _indeterminate("git-error")
    try:
        repository_root = Path(root_text).resolve(strict=True)
    except (OSError, RuntimeError):
        return _indeterminate("git-error")
    if not repository_root.is_dir():
        return _indeterminate("git-error")

    candidate = Path(wiki_dir)
    if not candidate.is_absolute():
        candidate = working_directory / candidate
    try:
        candidate = candidate.resolve(strict=False)
        relative = candidate.relative_to(repository_root)
    except (OSError, RuntimeError, ValueError):
        return _indeterminate(
            "outside-repository",
            repository_root=repository_root,
        )

    relative_path = relative.as_posix()
    if relative_path == ".":
        directory_probe = "./"
        index_probe = "index.md"
    else:
        directory_probe = f"{relative_path.rstrip('/')}/"
        index_probe = f"{relative_path.rstrip('/')}/index.md"
    # ``check-ignore`` accepts pathnames rather than general pathspecs and
    # rejects pathspec-magic prefixes.  A leading ``./`` is Git's supported
    # literal spelling for an actual filename beginning with ``:``.
    if directory_probe.startswith(":"):
        directory_probe = f"./{directory_probe}"
        index_probe = f"./{index_probe}"

    ignored = _run_git(
        repository_root,
        "check-ignore",
        "--no-index",
        "--",
        directory_probe,
        index_probe,
        timeout=timeout,
    )
    if ignored.failure is not None:
        return _indeterminate(
            ignored.failure,
            repository_root=repository_root,
            wiki_path=relative_path,
        )
    if ignored.returncode == 0:
        return WikiGitPolicy(
            disposition=WikiGitDisposition.IGNORED,
            reason="ignored",
            repository_root=repository_root,
            wiki_path=relative_path,
        )
    if ignored.returncode == 1:
        return WikiGitPolicy(
            disposition=WikiGitDisposition.INCLUDED,
            reason="included",
            repository_root=repository_root,
            wiki_path=relative_path,
        )
    return _indeterminate(
        "git-error",
        repository_root=repository_root,
        wiki_path=relative_path,
    )


def _indeterminate(
    reason: str,
    *,
    repository_root: Path | None = None,
    wiki_path: str | None = None,
) -> WikiGitPolicy:
    return WikiGitPolicy(
        disposition=WikiGitDisposition.INDETERMINATE,
        reason=reason,
        repository_root=repository_root,
        wiki_path=wiki_path,
    )


def _run_git(
    root: Path,
    *arguments: str,
    timeout: float,
) -> _GitResult:
    environment = dict(os.environ)
    for key in _GIT_REPOSITORY_REDIRECTION_ENV:
        environment.pop(key, None)
    environment.pop("GIT_CONFIG_PARAMETERS", None)
    environment.pop("GIT_CONFIG_COUNT", None)
    for key in tuple(environment):
        if key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            environment.pop(key, None)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["LC_ALL"] = "C"

    command = [
        "git",
        "-c",
        "core.fsmonitor=false",
        "-C",
        str(root),
        *arguments,
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=environment,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except FileNotFoundError:
        return _GitResult(returncode=None, failure="git-unavailable")
    except subprocess.TimeoutExpired:
        return _GitResult(returncode=None, failure="git-timeout")
    except (OSError, UnicodeError, ValueError):
        return _GitResult(returncode=None, failure="git-error")
    return _GitResult(returncode=completed.returncode, stdout=completed.stdout)
