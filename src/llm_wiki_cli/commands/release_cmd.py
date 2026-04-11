"""release_cmd — stamp the [Unreleased] CHANGELOG section with the current version.

Transforms::

    ## [Unreleased]
    ...changes...

    ## [0.1.5] - 2026-04-11
    ...

Into::

    ## [Unreleased]

    ## [0.1.6] - 2026-04-12
    ...changes...

    ## [0.1.5] - 2026-04-11
    ...

And updates the reference links at the bottom of the file.
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from ..services.versioning import find_version_file, read_version

# Matches the [Unreleased] section heading
_UNRELEASED_RE = re.compile(r"^## \[Unreleased\]", re.MULTILINE)
# Matches any existing version reference link: [x.y.z]: https://...
_REF_LINK_RE = re.compile(r"^\[[\w.]+\]: https://.*$", re.MULTILINE)

_GITHUB_REPO_RE = re.compile(r"https://github\.com/([^/]+/[^/]+)/compare/")

# Matches content between [Unreleased] heading and the next ## heading or end-of-file ref-links
_UNRELEASED_BODY_RE = re.compile(
    r"^## \[Unreleased\]\s*\n(.*?)(?=^## \[|^\[|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _unreleased_has_content(text: str) -> bool:
    """Return True if the [Unreleased] section contains at least one non-blank line."""
    m = _UNRELEASED_BODY_RE.search(text)
    if not m:
        return False
    body = m.group(1)
    return any(line.strip() for line in body.splitlines())


def _detect_repo_url(changelog_text: str) -> str | None:
    """Extract the GitHub compare base URL from existing reference links."""
    m = _GITHUB_REPO_RE.search(changelog_text)
    if m:
        return f"https://github.com/{m.group(1)}"
    return None


def stamp_changelog(changelog_path: Path, version: str, today: str | None = None) -> tuple[str, bool]:
    """Stamp the [Unreleased] section with *version* and return ``(new_text, stamped)``.

    *stamped* is ``False`` (and the original text is returned unchanged) when the
    ``[Unreleased]`` section is empty — i.e. the agent has not written any entries yet.

    Raises ``ValueError`` if no ``## [Unreleased]`` section is found.
    """
    text = changelog_path.read_text(encoding="utf-8")
    release_date = today or date.today().isoformat()

    if not _UNRELEASED_RE.search(text):
        raise ValueError("No '## [Unreleased]' section found in CHANGELOG.")

    # Skip stamp when [Unreleased] has no substantive content yet
    if not _unreleased_has_content(text):
        return text, False

    # Replace the first [Unreleased] heading with [Unreleased] + new version heading
    new_version_heading = f"## [Unreleased]\n\n## [{version}] - {release_date}"
    new_text = _UNRELEASED_RE.sub(new_version_heading, text, count=1)

    # Update reference links section
    repo_url = _detect_repo_url(text)
    if repo_url:
        # Remove all existing reference links (we'll rebuild them)
        new_text = _REF_LINK_RE.sub("", new_text).rstrip() + "\n"

        # Find previously highest version to build the compare URL for new version
        # Collect all version tags already mentioned in headings
        heading_versions = re.findall(r"## \[(\d+\.\d+\.\d+)\]", new_text)

        links: list[str] = []
        links.append(f"[Unreleased]: {repo_url}/compare/v{version}...HEAD")

        # Build compare links between consecutive versions (newest first)
        for i, ver in enumerate(heading_versions):
            if i + 1 < len(heading_versions):
                prev = heading_versions[i + 1]
                links.append(f"[{ver}]: {repo_url}/compare/v{prev}...v{ver}")
            else:
                links.append(f"[{ver}]: {repo_url}/releases/tag/v{ver}")

        new_text += "\n" + "\n".join(links) + "\n"

    return new_text, True


def run(args):
    root = getattr(args, "root", ".")
    changelog_path = Path(getattr(args, "changelog", "CHANGELOG.md"))

    if not changelog_path.exists():
        print(f"Error: {changelog_path} not found.")
        sys.exit(1)

    # Read version from project file
    version_file = find_version_file(root)
    if version_file is None:
        print("Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).")
        sys.exit(1)

    version = read_version(version_file)
    if version is None:
        print(f"Error: Could not parse version from {version_file}")
        sys.exit(1)

    try:
        new_text, stamped = stamp_changelog(changelog_path, version)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not stamped:
        print("CHANGELOG.md: [Unreleased] is empty — nothing to stamp (run after the agent adds entries).")
        return

    changelog_path.write_text(new_text, encoding="utf-8")
    print(f"CHANGELOG.md: [Unreleased] → [{version}] ({date.today().isoformat()})")

    if getattr(args, "stage", False):
        subprocess.run(["git", "add", str(changelog_path)], check=False)
        print(f"Staged: {changelog_path}")
