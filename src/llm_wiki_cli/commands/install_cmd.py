from __future__ import annotations

import sys

from ..config import DEFAULT_WIKI_DIR, read_config, validate_path
from ..services.plugins import PluginError, install_plugin
from ..services.schema import refresh_skill_blocks


def _component_summary(plugin: dict) -> str:
    counts: dict[str, int] = {}
    for component in plugin.get("components", []):
        counts[component["type"]] = counts.get(component["type"], 0) + 1
    if not counts:
        return "no components"
    return ", ".join(f"{count} {kind}" for kind, count in sorted(counts.items()))


def run(args) -> None:
    wiki_dir: str = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")

    try:
        plugin = install_plugin(
            getattr(args, "ref"),
            dry_run=bool(getattr(args, "dry_run", False)),
            yes=bool(getattr(args, "yes", False)),
        )
    except PluginError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if getattr(args, "dry_run", False):
        print(f"Plugin valid: {plugin['id']} {plugin['version']} ({_component_summary(plugin)})")
        print("Dry run: no files were changed.")
        return

    config = read_config(wiki_dir)
    refreshed = refresh_skill_blocks(str(config.get("agent", "generic")), wiki_dir)
    print(f"Installed plugin: {plugin['id']} {plugin['version']}")
    print(f"Components: {_component_summary(plugin)}")
    if refreshed:
        print(f"Updated {len(refreshed)} skill block(s) in agent schema.")
