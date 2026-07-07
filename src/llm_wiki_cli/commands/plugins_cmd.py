from __future__ import annotations

import sys

from ..config import DEFAULT_WIKI_DIR, validate_path
from ..services.plugins import PluginError, list_plugins, remove_plugin, validate_plugin
from ..services.plugin_samples import export_sample, list_samples
from ..services.schema import strip_plugin_skill_blocks


def _render_components(plugin: dict) -> str:
    parts = []
    for component in plugin.get("components", []):
        detail = (
            component.get("language")
            or component.get("path")
            or component.get("entry_point")
            or ""
        )
        suffix = f":{detail}" if detail else ""
        parts.append(f"{component['type']}/{component['id']}{suffix}")
    return ", ".join(parts) if parts else "none"


def run(args) -> None:
    action = getattr(args, "plugins_action", None)

    if action == "list":
        plugins = list_plugins()
        if not plugins:
            print("No llm-wiki plugins installed.")
            return
        for plugin in plugins:
            print(f"{plugin['id']} {plugin['version']}")
            print(f"  components: {_render_components(plugin)}")
        return

    if action == "samples":
        samples_action = getattr(args, "samples_action", None)
        if samples_action == "list":
            samples = list_samples()
            if not samples:
                print("No bundled plugin samples found.")
                return
            for sample in samples:
                print(f"{sample['id']}: {sample['description']}")
            return

        if samples_action == "export":
            try:
                exported = export_sample(
                    getattr(args, "sample_id"),
                    getattr(args, "dest"),
                    force=bool(getattr(args, "force", False)),
                )
                validate_plugin(exported["path"])
            except PluginError as exc:
                print(f"Error: {exc}", file=sys.stderr)
                sys.exit(1)
            print(f"Exported plugin sample: {exported['id']}")
            print(f"Destination: {exported['path']}")
            return

    if action == "remove":
        wiki_dir: str = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
        validate_path(wiki_dir, "--wiki-dir")
        plugin_id = getattr(args, "plugin_id")
        try:
            removed = remove_plugin(plugin_id)
        except PluginError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        touched = strip_plugin_skill_blocks(plugin_id)
        print(f"Removed plugin: {removed['id']}")
        if touched:
            print(f"Removed skill blocks from {len(touched)} schema file(s).")
        return

    if action == "validate":
        try:
            plugin = validate_plugin(getattr(args, "path"))
        except PluginError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Plugin valid: {plugin['id']} {plugin['version']}")
        print(f"Components: {_render_components(plugin)}")
        return

    print("Error: missing plugins action.", file=sys.stderr)
    sys.exit(1)
