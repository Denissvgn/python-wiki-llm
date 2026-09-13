"""Read-only provider preparation and plugin metadata diagnostics."""

from __future__ import annotations

import os
import shlex
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
_LANGUAGE_LABELS = {
    "python": "Python",
    "typescript": "TypeScript/JavaScript",
    "go": "Go",
    "rust": "Rust",
    "haskell": "Haskell",
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
        label = _LANGUAGE_LABELS[language]
        tools = {}
        for name in tool_names:
            resolver = {
                "go": helpers._resolve_go_executable,
                "ghc": helpers._resolve_ghc_executable,
            }.get(name)
            tools[name] = resolver() if resolver is not None else shutil.which(name)
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
        if language == "python":
            status_reason = (
                "Python analysis is built in; no extractor helper is needed."
            )
        elif artifact:
            status_reason = f"The {label} extractor helper is prepared."
        elif helper_state == "missing":
            status_reason = (
                f"The bundled {label} extractor helper has not been prepared."
            )
        else:
            status_reason = f"The cached {label} extractor helper is outdated, incomplete, or unreadable."
        if state == "missing-toolchain":
            needed_tools = ["node"] if artifact else missing
            status_reason += (
                " Required commands were not found: " + ", ".join(needed_tools) + "."
            )
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
                ]
                if artifact is None
                else None,
                "prerequisite": (
                    "Install Node.js or make node available on PATH"
                    if artifact
                    else _TOOL_HINTS[language]
                    if missing
                    else None
                ),
                "next_step": (
                    "Make the required commands available, then run the preparation command."
                    if missing and artifact is None
                    else "Make node available, then rerun doctor; the helper is already prepared."
                    if artifact
                    else f"Run the preparation command to build or restore the {label} extractor helper."
                ),
                "effect": "Explicit preparation may download dependencies or compile the bundled helper"
                if artifact is None
                else None,
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
                "status_reason": status_reason,
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
    recheck = None
    if capabilities["blocked_languages"]:
        argv = [
            sys.executable,
            "-m",
            "llm_wiki_cli.cli",
            "doctor",
            "--capabilities",
            "--src-dir",
            str(src_dir),
            "--wiki-dir",
            str(wiki_dir),
            "--helper-cache-dir",
            str(Path(capabilities["helper_cache"]).parent),
        ]
        for name in ("strict", "allow_external_src"):
            if kwargs.get(name):
                argv.append("--" + name.replace("_", "-"))
        if kwargs.get("source_selection") is not None:
            argv.extend(["--source-selection", str(kwargs["source_selection"])])
        for language in sorted(kwargs.get("include_tests") or ()):
            argv.extend(["--include-tests", language])
        recheck = {"argv": argv, "cwd": str(Path.cwd())}
    return {
        "schema_version": DOCTOR_CAPABILITY_VERSION,
        "status": health["status"] if health else "unknown",
        "exit_code": health["exit_code"] if health else 2,
        "health": health,
        "capabilities": capabilities,
        "recheck": recheck,
        "health_reason": None
        if health
        else "Selected source providers need setup; knowledge health was not evaluated",
    }


def render_capability_doctor(report):
    from .doctor_service import _render_doctor_payload

    def command(argv):
        if os.name == "nt":
            # PowerShell recognizes typographic single quotes as delimiters too.
            quotes = str.maketrans({char: char * 2 for char in "'‘’‚‛"})
            return "& " + " ".join("'" + arg.translate(quotes) + "'" for arg in argv)
        return shlex.join(argv)

    shell = "PowerShell" if os.name == "nt" else "POSIX shell"
    lines = [f"Doctor: {report['status']} ({DOCTOR_CAPABILITY_VERSION})"]
    for provider in report["capabilities"]["providers"]:
        if provider["selected_files"]:
            lines.append(
                f"{provider['language']}: {provider['status']} — {provider['provider']}, {provider['tier']}, helper {provider['helper']['status']}"
            )
            if provider.get("status_reason"):
                lines.append("  " + provider["status_reason"])
            if provider.get("tools"):
                lines.append(
                    "  Commands: "
                    + ", ".join(
                        name + (" found" if path else " missing")
                        for name, path in provider["tools"].items()
                    )
                )
            if provider["remedy"]:
                if provider["remedy"]["prerequisite"]:
                    lines.append("  " + provider["remedy"]["prerequisite"])
                if provider["remedy"].get("next_step"):
                    lines.append("  Next step: " + provider["remedy"]["next_step"])
                if provider["remedy"]["argv"]:
                    lines.append(
                        f"  Preparation command ({shell}): "
                        + command(provider["remedy"]["argv"])
                    )
                if provider["remedy"].get("effect"):
                    lines.append("  " + provider["remedy"]["effect"])
    for item in report["capabilities"]["unsupported_inputs"]:
        lines.append(
            f"{item['language']}: {item['status']} ({len(item['paths'])} files)"
        )
    for item in report["capabilities"]["plugins"]:
        lines.append(f"Plugin {item['id']}: {item['status']}")
        if item.get("reason"):
            lines.append("  " + item["reason"])
        if item.get("remedy"):
            lines.append(
                f"  Validation command ({shell}): " + command(item["remedy"]["argv"])
            )
    if report["health_reason"]:
        lines.append(report["health_reason"])
    elif report["health"]:
        lines.append(_render_doctor_payload(report["health"]).rstrip("\n"))
    if report.get("recheck"):
        lines.append("After setup, rerun from: " + report["recheck"]["cwd"])
        lines.append(
            f"  Recheck command ({shell}): " + command(report["recheck"]["argv"])
        )
    return "\n".join(lines) + "\n"
