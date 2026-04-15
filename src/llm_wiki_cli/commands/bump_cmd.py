import subprocess
import sys
from pathlib import Path

from ..services.versioning import (
    find_version_file,
    read_version,
    write_version,
    bump_patch,
    bump_minor,
)


def run(args):
    root = getattr(args, "root", ".")
    version_file = find_version_file(root)

    if version_file is None:
        print("Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).")
        sys.exit(1)

    current = read_version(version_file)
    if current is None:
        print(f"Error: Could not parse version from {version_file}")
        sys.exit(1)

    if args.bump_type == "patch":
        new_version = bump_patch(current)
    elif args.bump_type == "minor":
        new_version = bump_minor(current)
    else:
        print(f"Error: Unknown bump type '{args.bump_type}'")
        sys.exit(1)

    write_version(version_file, new_version)
    print(f"{current} -> {new_version}  ({version_file})")

    # If --stage is set, git-add the version file so it's included in the current commit
    if getattr(args, "stage", False):
        try:
            subprocess.run(["git", "add", str(version_file)], check=False)
        except FileNotFoundError:
            pass  # git not available; skip staging
