"""Read-only provider preparation and plugin metadata diagnostics."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from ..config import validate_source_root
from ..extractors.common import LANGUAGE_EXTENSIONS
from . import extractor_helpers as helpers, plugins
from .source_snapshot import build_source_snapshot

DOCTOR_CAPABILITY_VERSION = "llm-wiki-doctor/v2"
_PROVIDERS = {
    "python": ("stdlib-ast", ()),
    "typescript": ("ts-morph", ("node", "npm")),
    "go": ("go-parser", ("go",)),
    "rust": ("syn", ("cargo",)),
    "haskell": ("ghc-parser", ("ghc",)),
}
_TOOL_HINTS = {
    "typescript": "Install Node.js with npm",
    "go": "Install Go or set LLM_WIKI_GO",
    "rust": "Install the Rust toolchain with Cargo",
    "haskell": "Install GHC 9.6 or later in the supported 9.x series, or set LLM_WIKI_GHC",
}


def build_capability_diagnostics(
    src_dir=".",
    *,
    helper_cache_dir=None,
    source_selection=None,
    allow_external_src=False,
    include_tests=None,
):
    root = validate_source_root(
        str(src_dir), "--src-dir", allow_external=allow_external_src
    )
    snapshot = build_source_snapshot(
        root, source_selection=source_selection, include_tests=include_tests
    )
    cache = helpers.resolve_helper_cache_root(root, helper_cache_dir)
    cache_base = cache.parent if cache is not None else root / ".llm-wiki"
    effective_cache = cache or cache_base / helpers.HELPER_CACHE_DIRNAME
    providers = []
    for language, (provider, tool_names) in _PROVIDERS.items():
        tools = {}
        for name in tool_names:
            override = {"go": helpers.ENV_GO_BINARY, "ghc": helpers.ENV_GHC_BINARY}.get(
                name
            )
            requested = os.environ.get(override, "") if override else ""
            tools[name] = shutil.which(requested or name)
        missing = [name for name, path in tools.items() if path is None]
        artifact = None
        if language == "python":
            state, helper_state = "ready", "not-required"
        else:
            artifact = (
                helpers.get_prepared_typescript_root(root, helper_cache_dir)
                if language == "typescript"
                else helpers.get_prepared_binary(language, root, helper_cache_dir)
            )
            exists = (
                cache is not None and helpers._manifest_path(cache, language).exists()
            )
            helper_state = (
                "current" if artifact else "stale-or-invalid" if exists else "missing"
            )
            runtime_missing = language == "typescript" and tools["node"] is None
            state = (
                "missing-toolchain"
                if missing and (not artifact or runtime_missing)
                else "ready"
                if artifact
                else "unprepared"
            )
        remedy = None
        if state != "ready":
            remedy = {
                "argv": [
                    sys.executable,
                    "-m",
                    "llm_wiki_cli.cli",
                    "prepare-extractors",
                    "--src-dir",
                    str(root),
                    "--allow-external-src",
                    "--language",
                    language,
                    "--cache-dir",
                    str(cache_base),
                ],
                "prerequisite": _TOOL_HINTS[language] if missing else None,
                "effect": "Explicit preparation may download dependencies or compile the bundled helper",
            }
        providers.append(
            {
                "language": language,
                "provider": provider,
                "tier": "static-analysis",
                "capabilities": ["declarations", "inventory"],
                "selected_files": len(snapshot.files_by_language.get(language, ())),
                "extensions": list(LANGUAGE_EXTENSIONS[language]),
                "status": state,
                "helper": {
                    "status": helper_state,
                    "path": str(artifact) if artifact else None,
                },
                "tools": tools,
                "missing_tools": missing,
                "tool_versions": "unknown-not-executed",
                "remedy": remedy,
            }
        )
    plugin_states = []
    try:
        lock = plugins.read_lock(root)
        for plugin_id in sorted(lock["plugins"]):
            # Validate the ID before using it as a path. Never import plugin code.
            if (
                not isinstance(plugin_id, str)
                or Path(plugin_id).name != plugin_id
                or plugin_id in {".", ".."}
                or "\\" in plugin_id
            ):
                raise plugins.PluginError("Invalid installed plugin ID")
            try:
                manifest = plugins.validate_plugin(
                    plugins.plugin_store(root) / plugin_id
                )
                state = {
                    "id": plugin_id,
                    "status": "installed-not-executed",
                    "tier": "unknown",
                    "components": [
                        {
                            key: item[key]
                            for key in ("id", "type", "language")
                            if key in item
                        }
                        for item in manifest["components"]
                    ],
                    "remedy": None,
                }
            except (ValueError, OSError) as exc:
                state = {
                    "id": plugin_id,
                    "status": "invalid",
                    "tier": "unknown",
                    "reason": str(exc),
                    "remedy": {
                        "argv": [
                            sys.executable,
                            "-m",
                            "llm_wiki_cli.cli",
                            "plugins",
                            "validate",
                            str(plugins.plugin_store(root) / plugin_id),
                        ]
                    },
                }
            plugin_states.append(state)
    except (ValueError, OSError, TypeError) as exc:
        plugin_states.append(
            {
                "id": None,
                "status": "unknown",
                "tier": "unknown",
                "reason": str(exc),
                "remedy": None,
            }
        )
    unsupported = [
        {
            "language": language,
            "status": "unsupported",
            "paths": [item.rel_path for item in files],
            "remedy": None,
        }
        for language, files in sorted(snapshot.unsupported_files_by_language.items())
        if files
    ]
    known_suffixes = {
        suffix for suffixes in LANGUAGE_EXTENSIONS.values() for suffix in suffixes
    }
    unknown_sources = sorted(
        path
        for path in snapshot.selected_regular_paths
        if Path(path).suffix.lower()
        in {".java", ".cs", ".cpp", ".c", ".rb", ".php", ".kt"} - known_suffixes
    )
    if unknown_sources:
        unsupported.append(
            {
                "language": "unknown-provider",
                "status": "unknown",
                "paths": unknown_sources,
                "remedy": None,
            }
        )
    blocked = [
        p["language"]
        for p in providers
        if p["selected_files"] and p["status"] != "ready"
    ]
    return {
        "providers": providers,
        "plugins": plugin_states,
        "unsupported_inputs": unsupported,
        "blocked_languages": blocked,
        "helper_cache": str(effective_cache),
        "limitations": [
            "Tool versions and execution viability are unknown until explicitly invoked",
            "Plugin metadata is inspected; plugin code is not loaded",
            "Dynamic application behavior is not analyzed",
        ],
    }


def build_capability_doctor(wiki_dir="docs/llm_wiki", src_dir=".", **kwargs):
    from .doctor_service import build_doctor_report

    capabilities = build_capability_diagnostics(
        src_dir,
        **{
            key: value
            for key, value in kwargs.items()
            if key
            in {
                "helper_cache_dir",
                "source_selection",
                "allow_external_src",
                "include_tests",
            }
        },
    )
    health = None
    if not capabilities["blocked_languages"]:
        health = build_doctor_report(wiki_dir, src_dir, **kwargs).to_payload()
    return {
        "schema_version": DOCTOR_CAPABILITY_VERSION,
        "status": health["status"] if health else "unknown",
        "exit_code": health["exit_code"] if health else 2,
        "health": health,
        "capabilities": capabilities,
        "health_reason": None
        if health
        else "Selected source providers need preparation; knowledge health was not evaluated",
    }


def render_capability_doctor(report):
    lines = [f"Doctor: {report['status']} ({DOCTOR_CAPABILITY_VERSION})"]
    for provider in report["capabilities"]["providers"]:
        if provider["selected_files"]:
            lines.append(
                f"{provider['language']}: {provider['status']} — {provider['provider']}, {provider['tier']}, helper {provider['helper']['status']}"
            )
            if provider["remedy"]:
                if provider["remedy"]["prerequisite"]:
                    lines.append("  " + provider["remedy"]["prerequisite"])
                lines.append("  Preparation argv: " + repr(provider["remedy"]["argv"]))
    for item in report["capabilities"]["unsupported_inputs"]:
        lines.append(
            f"{item['language']}: {item['status']} ({len(item['paths'])} files)"
        )
    for item in report["capabilities"]["plugins"]:
        lines.append(f"Plugin {item['id']}: {item['status']}")
    if report["health_reason"]:
        lines.append(report["health_reason"])
    elif report["health"]:
        lines.append("Knowledge health: " + report["health"]["status"])
    return "\n".join(lines) + "\n"
