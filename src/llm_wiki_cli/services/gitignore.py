"""Gitignore matching for source discovery.

``llm_wiki_cli.config`` re-exports every name for existing callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from .path_policy import EXCLUDED_DIRS, is_agent_worktree_path


@dataclass(frozen=True)
class _GitignoreRule:
    base: str
    pattern: str
    negated: bool
    directory_only: bool
    anchored: bool

class GitIgnoreMatcher:
    """Ordered gitignore matcher for repository scans.

    This supports the semantics the extractors need without reparsing the same
    .gitignore file for every source file: negation, root-anchored patterns,
    nested .gitignore files, directory-only rules, and common ``**`` patterns.
    """

    def __init__(self, rules: list[_GitignoreRule]):
        self._rules = rules

    def last_matching_rule(self, rel_path: str) -> _GitignoreRule | None:
        """Return the final gitignore rule that matches *rel_path*, if any."""
        rel_path = rel_path.replace("\\", "/").strip("/")
        last_rule: _GitignoreRule | None = None
        for rule in self._rules:
            if _rule_matches(rel_path, rule):
                last_rule = rule
        return last_rule

    def is_ignored(self, rel_path: str) -> bool:
        rule = self.last_matching_rule(rel_path)
        return rule is not None and not rule.negated

def _normalize_gitignore_trailing_spaces(line: str) -> str:
    """Remove Git-insignificant trailing spaces from one ignore pattern.

    Backslashes quote the next character, so escaped spaces are retained while
    an unescaped trailing run is removed.  Decode only quoted spaces here;
    broader gitignore escape and wildmatch semantics remain unchanged.  Tabs
    are intentionally untouched.
    """
    first_trailing_space: int | None = None
    index = 0
    while index < len(line):
        if line[index] == "\\":
            first_trailing_space = None
            index += 2
            continue
        if line[index] == " ":
            if first_trailing_space is None:
                first_trailing_space = index
        else:
            first_trailing_space = None
        index += 1

    if first_trailing_space is not None:
        line = line[:first_trailing_space]

    normalized: list[str] = []
    index = 0
    while index < len(line):
        if line[index] != "\\":
            normalized.append(line[index])
            index += 1
            continue

        run_start = index
        while index < len(line) and line[index] == "\\":
            index += 1
        backslash_count = index - run_start
        if index < len(line) and line[index] == " " and backslash_count % 2:
            normalized.append("\\" * (backslash_count - 1))
            normalized.append(" ")
            index += 1
            continue
        normalized.append("\\" * backslash_count)

    return "".join(normalized)

def _parse_gitignore_text(raw_text: str, base: str = "") -> list[_GitignoreRule]:
    """Parse already captured gitignore text without performing file I/O."""
    rules: list[_GitignoreRule] = []
    for raw in raw_text.splitlines():
        line = _normalize_gitignore_trailing_spaces(raw)
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        if negated:
            line = line[1:]
        anchored = line.startswith("/")
        if anchored:
            line = line[1:]
        directory_only = line.endswith("/")
        line = line.rstrip("/")
        if line:
            rules.append(
                _GitignoreRule(
                    base=base.strip("/"),
                    pattern=line.replace("\\", "/"),
                    negated=negated,
                    directory_only=directory_only,
                    anchored=anchored,
                )
            )
    return rules

def _parse_gitignore_file(gitignore_path: Path, base: str = "") -> list[_GitignoreRule]:
    rules: list[_GitignoreRule] = []
    if not gitignore_path.exists():
        return rules

    try:
        return _parse_gitignore_text(
            gitignore_path.read_text(encoding="utf-8"),
            base,
        )
    except OSError:
        return rules

def _match_gitignore_pattern(
    rel_path: str, pattern: str, *, directory_only: bool = False
) -> bool:
    """Check if a relative path matches a gitignore pattern."""
    rel_path = rel_path.replace("\\", "/").strip("/")
    pattern = pattern.replace("\\", "/").strip("/")

    if not rel_path or not pattern:
        return False

    if directory_only:
        if "/" in pattern:
            return (
                rel_path == pattern
                or rel_path.startswith(pattern + "/")
                or fnmatch(rel_path, pattern + "/**")
            )
        parts = rel_path.split("/")
        return any(fnmatch(part, pattern) for part in parts[:-1])

    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return rel_path == prefix or rel_path.startswith(prefix + "/")

    if "/" in pattern:
        return fnmatch(rel_path, pattern) or fnmatch(rel_path, pattern + "/**")

    return any(fnmatch(part, pattern) for part in rel_path.split("/"))

def _rule_matches(rel_path: str, rule: _GitignoreRule) -> bool:
    if rule.base:
        if rel_path == rule.base:
            candidate = ""
        elif rel_path.startswith(rule.base + "/"):
            candidate = rel_path[len(rule.base) + 1 :]
        else:
            return False
    else:
        candidate = rel_path
    if not candidate:
        return False

    if rule.anchored:
        pattern = rule.pattern
        if rule.directory_only:
            return (
                candidate == pattern
                or candidate.startswith(pattern + "/")
                or fnmatch(candidate, pattern + "/**")
            )
        if "/" not in pattern:
            return "/" not in candidate and fnmatch(candidate, pattern)
        return fnmatch(candidate, pattern) or fnmatch(candidate, pattern + "/**")

    return _match_gitignore_pattern(
        candidate,
        rule.pattern,
        directory_only=rule.directory_only,
    )

def build_gitignore_matcher(root: "str | Path") -> GitIgnoreMatcher:
    """Parse root and nested .gitignore files once for a source scan."""
    root_path = Path(root)
    rules: list[_GitignoreRule] = []
    if not root_path.exists():
        return GitIgnoreMatcher(rules)

    for gitignore in sorted(root_path.rglob(".gitignore")):
        try:
            rel_parent = gitignore.parent.relative_to(root_path)
        except ValueError:
            continue
        if not EXCLUDED_DIRS.isdisjoint(rel_parent.parts) or is_agent_worktree_path(
            rel_parent
        ):
            continue
        base = "" if rel_parent == Path(".") else rel_parent.as_posix()
        rules.extend(_parse_gitignore_file(gitignore, base))
    return GitIgnoreMatcher(rules)

def is_ignored_by_gitignore(
    rel_path: str, gitignore_path: Path = Path(".gitignore")
) -> bool:
    """Check if a relative path is ignored according to one .gitignore file."""
    matcher = GitIgnoreMatcher(_parse_gitignore_file(gitignore_path, ""))
    return matcher.is_ignored(rel_path)
