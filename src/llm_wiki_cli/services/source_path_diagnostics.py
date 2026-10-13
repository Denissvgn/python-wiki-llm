"""Supplied-path facts derived from captured discovery policy and extraction."""

from __future__ import annotations

import stat
from pathlib import Path

from ..config import EXCLUDED_DIRS, GitIgnoreMatcher, PathValidationError, is_agent_worktree_path
from ..extractors.common import is_bundled_helper_implementation_path, is_generated_javascript_bundle_path
from .source_selection import path_is_selected
from .source_snapshot import SourceSnapshot, _language_selection_for_path, _is_rescuable_typescript_src_lib_file


def source_path_diagnostics(snapshot: SourceSnapshot, paths: tuple[str, ...]) -> dict[str, dict]:
    """Observe selected path metadata without following links or reading content.

    Inventory absence proves none of these facts. Selection exclusions prevent
    even a metadata read; ignore decisions use the snapshot's captured rules.
    """
    matcher = GitIgnoreMatcher(list(snapshot.gitignore_rules))
    result = {}
    for path in paths:
        relative = Path(path)
        candidate = snapshot.root / relative
        row = {"filesystem_state": "unknown", "selection_state": "included",
               "extraction_state": "not-attempted", "reason": "not-attempted"}
        policy = snapshot.source_selection_policy
        if policy is not None and (path == policy.path or not path_is_selected(policy, path)):
            row.update(selection_state="excluded", reason="source-selection")
            result[path] = row
            continue
        try:
            current = snapshot.root
            for component in relative.parts:
                current /= component
                metadata = current.lstat()
                if stat.S_ISLNK(metadata.st_mode):
                    raise PathValidationError(f"supplied source path must not traverse a symlink: {path}")
            row["filesystem_state"] = "file" if stat.S_ISREG(metadata.st_mode) else "not-file"
        except FileNotFoundError:
            row["filesystem_state"] = "missing"
        except OSError:
            row["reason"] = "filesystem-unavailable"
        language, test_exclusion = _language_selection_for_path(candidate, snapshot.include_tests)
        exclusion = None
        if not EXCLUDED_DIRS.isdisjoint(relative.parts[:-1]):
            exclusion = "excluded-directory"
        elif is_agent_worktree_path(path):
            exclusion = "worktree"
        elif is_bundled_helper_implementation_path(candidate):
            exclusion = "bundled-helper"
        elif matcher.is_ignored(path) and not _is_rescuable_typescript_src_lib_file(matcher, relative, language):
            exclusion = "gitignore"
        elif is_generated_javascript_bundle_path(path):
            exclusion = "generated-bundle"
        if exclusion:
            row.update(selection_state="excluded", reason=exclusion)
        elif test_exclusion:
            row.update(selection_state="excluded", reason=test_exclusion)
        elif row["filesystem_state"] != "file":
            if row["filesystem_state"] != "unknown":
                row["reason"] = row["filesystem_state"]
        elif language is None:
            row.update(extraction_state="unsupported", reason="unsupported-extension")
        else:
            row.update(extraction_state="unavailable", reason="outcome-not-reported")
        result[path] = row
    return result
