"""Local plugin marketplace support for llm-wiki.

Plugins are installed from local directories only.  Each plugin must provide a
``llm-wiki-plugin.json`` manifest and is copied into ``.llm-wiki/plugins`` so
runtime behavior is reproducible from project-local state.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import re
import shutil
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import __version__
from ..config import EXTRACTOR_REGISTRY
from .validation import (
    path_is_within as shared_path_is_within,
    require_existing_file,
    resolve_portable_workspace_path,
)

MANIFEST_FILENAME = "llm-wiki-plugin.json"
PLUGIN_HOME = ".llm-wiki"
PLUGIN_DIRNAME = "plugins"
LOCK_FILENAME = "plugins.lock.json"
PROJECT_CATALOG = Path(PLUGIN_HOME) / "catalog.json"
USER_CATALOG = Path.home() / ".llm-wiki" / "catalog.json"

SUPPORTED_COMPONENT_TYPES = {
    "diagram_style",
    "entrypoint_detector",
    "extractor",
    "lint_rule",
    "prompt_template",
    "skill",
}
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_MODULE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
_ATTR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
_PROMPT_GIT_MUTATION_RE = re.compile(
    r"(?i)(?<![A-Za-z0-9_-])git\b[^\r\n]*?(?<![A-Za-z0-9_-])(?:add|commit)\b"
)
_RUNTIME_CACHE_DIRECTORIES = frozenset(
    {".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__"}
)


class PluginError(ValueError):
    """Raised when a plugin manifest, install, or lookup is invalid."""


def plugin_home(root: str | Path = ".") -> Path:
    return Path(root) / PLUGIN_HOME


def plugin_store(root: str | Path = ".") -> Path:
    return plugin_home(root) / PLUGIN_DIRNAME


def lock_path(root: str | Path = ".") -> Path:
    return plugin_home(root) / LOCK_FILENAME


def _default_lock() -> dict[str, Any]:
    return {"version": 1, "plugins": {}}


def read_lock(root: str | Path = ".") -> dict[str, Any]:
    path = lock_path(root)
    if not path.exists():
        return _default_lock()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PluginError(f"Invalid plugin lockfile {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("plugins"), dict):
        raise PluginError(f"Invalid plugin lockfile {path}: missing plugins object.")
    data.setdefault("version", 1)
    return data


def write_lock(data: dict[str, Any], root: str | Path = ".") -> None:
    path = lock_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_catalog(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PluginError(f"Invalid plugin catalog {path}: {exc}") from exc

    if isinstance(raw, dict) and isinstance(raw.get("plugins"), dict):
        raw = raw["plugins"]
    if not isinstance(raw, dict):
        raise PluginError(f"Invalid plugin catalog {path}: expected an object.")

    result: dict[str, str] = {}
    for name, value in raw.items():
        if isinstance(value, str):
            result[str(name)] = value
        elif isinstance(value, dict) and isinstance(value.get("path"), str):
            result[str(name)] = value["path"]
        else:
            raise PluginError(
                f"Invalid catalog entry {name!r} in {path}: expected a path."
            )
    return result


def resolve_plugin_ref(ref: str, root: str | Path = ".") -> Path:
    """Resolve a direct local path or a project/user catalog name."""
    direct = Path(ref).expanduser()
    if direct.exists():
        resolved = direct.resolve()
        project_root = Path(root).resolve()
        try:
            resolved.relative_to(project_root)
        except ValueError as exc:
            raise PluginError(
                f"Direct plugin paths must stay inside the project root: {resolved}"
            ) from exc
        return resolved

    catalogs = [
        (Path(root) / PROJECT_CATALOG, Path(root) / PROJECT_CATALOG.parent),
        (USER_CATALOG, USER_CATALOG.parent),
    ]
    for catalog_path, base_dir in catalogs:
        catalog = _load_catalog(catalog_path)
        if ref not in catalog:
            continue
        configured = Path(catalog[ref]).expanduser()
        if not configured.is_absolute():
            configured = base_dir / configured
        if not configured.exists():
            raise PluginError(
                f"Catalog entry {ref!r} points to missing path: {configured}"
            )
        return configured.resolve()

    raise PluginError(
        f"Plugin {ref!r} is not a local path or configured catalog entry."
    )


def _manifest_root(ref: str | Path) -> tuple[Path, Path]:
    path = Path(ref).expanduser().resolve()
    if path.is_file():
        if path.name != MANIFEST_FILENAME:
            raise PluginError(f"Plugin file must be named {MANIFEST_FILENAME}: {path}")
        return path.parent, path
    manifest_path = path / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise PluginError(f"Missing plugin manifest: {manifest_path}")
    return path, manifest_path


def _ensure_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.match(value):
        raise PluginError(f"{field} must be a non-empty identifier.")
    return value


def _parse_version(value: str) -> tuple[int, int, int]:
    parts = re.findall(r"\d+", value)
    if not parts:
        return (0, 0, 0)
    ints = [int(part) for part in parts[:3]]
    while len(ints) < 3:
        ints.append(0)
    return tuple(ints)  # type: ignore[return-value]


def _current_llm_wiki_version() -> str:
    if __version__ != "0.0.0":
        return __version__
    pyproject = Path(__file__).resolve().parents[3] / "pyproject.toml"
    if not pyproject.exists():
        return __version__
    match = re.search(
        r'^\s*version\s*=\s*"([^"]+)"',
        pyproject.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    return match.group(1) if match else __version__


def _version_satisfies(current: str, requirement: str) -> bool:
    requirement = requirement.strip()
    if requirement in {"", "*"}:
        return True
    if requirement.startswith(">="):
        return _parse_version(current) >= _parse_version(requirement[2:].strip())
    if requirement.startswith("=="):
        return _parse_version(current) == _parse_version(requirement[2:].strip())
    return _parse_version(current) == _parse_version(requirement)


def _is_relative_to(path: Path, root: Path) -> bool:
    return shared_path_is_within(path, root)


def _entry_point_module_source(plugin_dir: Path, module: str) -> Path | None:
    root = plugin_dir.resolve()
    parts = module.split(".")

    for index in range(1, len(parts)):
        package_init = root.joinpath(*parts[:index], "__init__.py")
        try:
            package_init = package_init.resolve(strict=True)
        except FileNotFoundError:
            return None
        if not _is_relative_to(package_init, root) or not package_init.is_file():
            return None

    module_path = root.joinpath(*parts)
    candidates = [module_path.with_suffix(".py"), module_path / "__init__.py"]
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError:
            continue
        if _is_relative_to(resolved, root) and resolved.is_file():
            return resolved
    return None


def _ensure_entry_point(
    value: Any, field: str, *, plugin_dir: Path | None = None
) -> str:
    if not isinstance(value, str) or ":" not in value:
        raise PluginError(f"{field} must use 'module:attribute' format.")
    module, attr = value.split(":", 1)
    if not _MODULE_RE.match(module) or not _ATTR_RE.match(attr):
        raise PluginError(f"{field} must use a valid Python module and attribute.")
    if "__pycache__" in module.split("."):
        raise PluginError(
            f"{field} module must not use the reserved __pycache__ directory."
        )
    if (
        plugin_dir is not None
        and _entry_point_module_source(plugin_dir, module) is None
    ):
        raise PluginError(
            f"{field} module must resolve to a Python file inside the plugin directory: {module}"
        )
    return value


def _ensure_no_reserved_plugin_sources(plugin_dir: Path) -> None:
    """Reject authored Python hidden inside interpreter cache directories.

    ``__pycache__`` is excluded from executable-input commitments because the
    interpreter writes volatile bytecode there.  Python source is never a
    legitimate cache artifact, so allowing it below that directory would make
    executable bytes invisible to the integrity baseline.
    """

    try:
        hidden_sources = sorted(
            path.relative_to(plugin_dir).as_posix()
            for path in plugin_dir.rglob("*.py")
            if "__pycache__" in path.relative_to(plugin_dir).parts
        )
    except OSError as exc:
        raise PluginError(
            f"Cannot inspect plugin sources under {plugin_dir}: {exc}"
        ) from exc
    if hidden_sources:
        raise PluginError(
            "Plugin Python source must not be stored under the reserved "
            f"__pycache__ directory: {hidden_sources[0]}"
        )


def _safe_component_path(plugin_dir: Path, value: Any, field: str) -> str:
    return require_existing_file(
        resolve_portable_workspace_path(
            plugin_dir,
            value,  # type: ignore[arg-type]
            path_error=PluginError(f"{field} must be a relative file path."),
            escape_error=PluginError(
                f"{field} must be relative to the plugin directory."
            ),
            traversal_error=PluginError(
                f"{field} escapes the plugin directory: {value}"
            ),
        ),
        error=PluginError(f"{field} does not exist: {value}"),
    ).relative_to(plugin_dir.resolve()).as_posix()


def _normalize_component(plugin_dir: Path, raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise PluginError("Each plugin component must be an object.")
    component_type = raw.get("type")
    if component_type not in SUPPORTED_COMPONENT_TYPES:
        raise PluginError(f"Unsupported plugin component type: {component_type!r}")

    component: dict[str, Any] = {
        "type": component_type,
        "id": _ensure_id(raw.get("id"), "component.id"),
    }
    if isinstance(raw.get("description"), str):
        component["description"] = raw["description"]

    if component_type == "extractor":
        component["language"] = _ensure_id(raw.get("language"), "extractor.language")
        component["entry_point"] = _ensure_entry_point(
            raw.get("entry_point"),
            "extractor.entry_point",
            plugin_dir=plugin_dir,
        )
        parallel_safe = raw.get("parallel_safe", False)
        if not isinstance(parallel_safe, bool):
            raise PluginError("extractor.parallel_safe must be a boolean.")
        component["parallel_safe"] = parallel_safe
    elif component_type == "lint_rule":
        component["entry_point"] = _ensure_entry_point(
            raw.get("entry_point"),
            "lint_rule.entry_point",
            plugin_dir=plugin_dir,
        )
    elif component_type in {"entrypoint_detector", "diagram_style"}:
        component["entry_point"] = _ensure_entry_point(
            raw.get("entry_point"),
            f"{component_type}.entry_point",
            plugin_dir=plugin_dir,
        )
    elif component_type == "prompt_template":
        component["path"] = _safe_component_path(
            plugin_dir, raw.get("path"), "prompt_template.path"
        )
        _validate_prompt_template_vcs_boundary(
            (plugin_dir / component["path"]).read_text(encoding="utf-8")
        )
    elif component_type == "skill":
        component["path"] = _safe_component_path(
            plugin_dir, raw.get("path"), "skill.path"
        )

    return component


def validate_plugin(ref: str | Path) -> dict[str, Any]:
    """Validate and normalize a plugin manifest without installing it."""
    plugin_dir, manifest_path = _manifest_root(ref)
    _ensure_no_reserved_plugin_sources(plugin_dir)
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PluginError(f"Invalid plugin manifest {manifest_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise PluginError("Plugin manifest must be a JSON object.")

    plugin_id = _ensure_id(raw.get("id"), "id")
    version = raw.get("version")
    llm_wiki_version = raw.get("llm_wiki_version")
    components = raw.get("components")

    if not isinstance(version, str) or not version:
        raise PluginError("version must be a non-empty string.")
    if not isinstance(llm_wiki_version, str) or not llm_wiki_version:
        raise PluginError("llm_wiki_version must be a non-empty string.")
    current_version = _current_llm_wiki_version()
    if not _version_satisfies(current_version, llm_wiki_version):
        raise PluginError(
            f"Plugin {plugin_id} requires llm-wiki {llm_wiki_version}, current version is {current_version}."
        )
    if not isinstance(components, list) or not components:
        raise PluginError("components must be a non-empty list.")

    normalized_components = [
        _normalize_component(plugin_dir, item) for item in components
    ]
    seen_refs: set[tuple[str, str]] = set()
    for component in normalized_components:
        ref_key = (component["type"], component["id"])
        if ref_key in seen_refs:
            raise PluginError(
                f"Duplicate component id for type {component['type']}: {component['id']}"
            )
        seen_refs.add(ref_key)

    return {
        "id": plugin_id,
        "version": version,
        "llm_wiki_version": llm_wiki_version,
        "description": raw.get("description", "")
        if isinstance(raw.get("description"), str)
        else "",
        "components": normalized_components,
        "_source_dir": str(plugin_dir),
    }


def _installed_extractor_languages(lock: dict[str, Any]) -> set[str]:
    languages: set[str] = set()
    for plugin in lock.get("plugins", {}).values():
        for component in plugin.get("components", []):
            if component.get("type") == "extractor" and isinstance(
                component.get("language"), str
            ):
                languages.add(component["language"])
    return languages


def _check_install_collisions(manifest: dict[str, Any], lock: dict[str, Any]) -> None:
    plugin_id = manifest["id"]
    if plugin_id in lock.get("plugins", {}):
        raise PluginError(f"Plugin {plugin_id!r} is already installed.")

    existing_languages = set(EXTRACTOR_REGISTRY) | _installed_extractor_languages(lock)
    for component in manifest["components"]:
        if (
            component.get("type") == "extractor"
            and component.get("language") in existing_languages
        ):
            raise PluginError(
                f"Extractor language {component['language']!r} is already registered."
            )


def _copy_ignore(_dir: str, names: list[str]) -> set[str]:
    ignored = {".git", *_RUNTIME_CACHE_DIRECTORIES}
    return {name for name in names if name in ignored}


def install_plugin(
    ref: str,
    *,
    root: str | Path = ".",
    dry_run: bool = False,
    yes: bool = False,
) -> dict[str, Any]:
    source = resolve_plugin_ref(ref, root=root)
    manifest = validate_plugin(source)
    lock = read_lock(root)
    _check_install_collisions(manifest, lock)

    if not yes and not dry_run:
        response = input(
            f"Install llm-wiki plugin {manifest['id']} {manifest['version']}? [y/N] "
        )
        if response.strip().lower() not in {"y", "yes"}:
            raise PluginError("Installation cancelled.")

    install_dir = plugin_store(root) / manifest["id"]
    if install_dir.exists():
        raise PluginError(f"Plugin install directory already exists: {install_dir}")

    entry = {
        "id": manifest["id"],
        "version": manifest["version"],
        "llm_wiki_version": manifest["llm_wiki_version"],
        "description": manifest.get("description", ""),
        "source": str(source),
        "installed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "components": manifest["components"],
    }

    if dry_run:
        return entry

    install_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(Path(manifest["_source_dir"]), install_dir, ignore=_copy_ignore)
    lock.setdefault("version", 1)
    lock.setdefault("plugins", {})[manifest["id"]] = entry
    write_lock(lock, root)
    return entry


def remove_plugin(plugin_id: str, *, root: str | Path = ".") -> dict[str, Any]:
    lock = read_lock(root)
    plugins = lock.setdefault("plugins", {})
    if plugin_id not in plugins:
        raise PluginError(f"Plugin {plugin_id!r} is not installed.")
    removed = plugins.pop(plugin_id)
    install_dir = plugin_store(root) / plugin_id
    if install_dir.exists():
        shutil.rmtree(install_dir)
    write_lock(lock, root)
    return removed


def list_plugins(root: str | Path = ".") -> list[dict[str, Any]]:
    lock = read_lock(root)
    return [dict(plugin) for plugin in lock.get("plugins", {}).values()]


def iter_components(
    component_type: str | None = None, *, root: str | Path = "."
) -> list[dict[str, Any]]:
    lock = read_lock(root)
    components: list[dict[str, Any]] = []
    for plugin_id, plugin in lock.get("plugins", {}).items():
        plugin_dir = plugin_store(root) / plugin_id
        for component in plugin.get("components", []):
            if component_type is not None and component.get("type") != component_type:
                continue
            item = dict(component)
            item["plugin_id"] = plugin_id
            item["plugin_version"] = plugin.get("version", "")
            item["plugin_dir"] = str(plugin_dir)
            item["ref"] = f"{plugin_id}/{component.get('id')}"
            components.append(item)
    return components


_ACTIVATED_PATHS: set[str] = set()
_PLUGIN_CODE_FINGERPRINTS: dict[str, str] = {}
_PLUGIN_LOAD_LOCK = threading.RLock()


def _activate_plugin_path(path: Path) -> None:
    resolved = str(path.resolve())
    if resolved not in _ACTIVATED_PATHS:
        sys.path.insert(0, resolved)
        _ACTIVATED_PATHS.add(resolved)


def activate_plugin_paths(root: str | Path = ".") -> None:
    for plugin in list_plugins(root):
        _activate_plugin_path(plugin_store(root) / plugin["id"])


def runtime_plugin_fallback_root(
    source_root: str | Path,
    *,
    source_selection_configured: bool,
    source_plugins_only: bool = False,
) -> Path | None:
    """Return the ambient plugin fallback only for legacy compatible reads."""

    if (source_selection_configured or source_plugins_only) and Path(
        source_root
    ).resolve() != Path.cwd().resolve():
        return None
    return Path.cwd()


def runtime_project_plugins_enabled(
    source_root: str | Path,
    *,
    source_selection_configured: bool,
    source_plugins_only: bool = False,
    include_plugins: bool = True,
) -> bool:
    """Return whether project plugin code is authorized for this source read.

    A source-selection profile constrains readable data; it is not consent to
    execute code from an external source tree.  Explicit trusted-source modes
    retain that authority, while same-project and unconfigured legacy reads
    preserve their existing plugin behavior.
    """

    if not include_plugins:
        return False
    if source_plugins_only or not source_selection_configured:
        return True
    return Path(source_root).resolve() == Path.cwd().resolve()


def _entry_point_components(
    entry_point: str, *, root: str | Path = "."
) -> list[dict[str, Any]]:
    return [
        component
        for component in iter_components(root=root)
        if component.get("entry_point") == entry_point
    ]


def _installed_entry_point_plugin_dir(
    entry_point: str, *, root: str | Path = "."
) -> Path:
    components = _entry_point_components(entry_point, root=root)
    if not components:
        raise PluginError(
            f"Entry point {entry_point!r} is not registered by an installed plugin."
        )

    plugin_dirs = {Path(component["plugin_dir"]).resolve() for component in components}
    if len(plugin_dirs) > 1:
        refs = ", ".join(sorted(str(component["ref"]) for component in components))
        raise PluginError(
            f"Entry point {entry_point!r} is ambiguous across installed plugins: {refs}"
        )
    return next(iter(plugin_dirs))


def _module_loaded_from_plugin(module: Any, plugin_dir: Path) -> bool:
    root = plugin_dir.resolve()
    module_file = getattr(module, "__file__", None)
    if module_file:
        return _is_relative_to(Path(module_file).resolve(), root)
    module_paths = getattr(module, "__path__", None)
    if module_paths:
        return all(_is_relative_to(Path(path).resolve(), root) for path in module_paths)
    return False


def _ensure_loaded_module_not_shadowed(module_name: str, plugin_dir: Path) -> None:
    parts = module_name.split(".")
    for index in range(1, len(parts) + 1):
        prefix = ".".join(parts[:index])
        loaded = sys.modules.get(prefix)
        if loaded is not None and not _module_loaded_from_plugin(loaded, plugin_dir):
            raise PluginError(
                f"Entry point {module_name!r} resolves outside its installed plugin directory."
            )


def _plugin_code_fingerprint(plugin_dir: Path) -> str:
    digest = hashlib.sha256()
    _ensure_no_reserved_plugin_sources(plugin_dir)
    try:
        committed_files = sorted(
            path
            for path in plugin_dir.rglob("*")
            if path.is_file()
            and not _RUNTIME_CACHE_DIRECTORIES.intersection(
                path.relative_to(plugin_dir).parts
            )
        )
        for path in committed_files:
            digest.update(path.relative_to(plugin_dir).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    except OSError as exc:
        raise PluginError(
            f"Cannot bind installed plugin code under {plugin_dir}: {exc}"
        ) from exc
    return "sha256:" + digest.hexdigest()


def _purge_changed_plugin_modules(plugin_dir: Path) -> None:
    for module_name, module in list(sys.modules.items()):
        if module is not None and _module_loaded_from_plugin(module, plugin_dir):
            sys.modules.pop(module_name, None)
    for source in plugin_dir.rglob("*.py"):
        try:
            cache_path = Path(importlib.util.cache_from_source(str(source)))
            cache_path.unlink(missing_ok=True)
        except (NotImplementedError, OSError) as exc:
            raise PluginError(
                f"Cannot invalidate changed installed plugin code under "
                f"{plugin_dir}: {exc}"
            ) from exc


def load_entry_point(entry_point: str, *, root: str | Path = ".") -> Any:
    entry_point = _ensure_entry_point(entry_point, "entry_point")
    module_name, attr_path = entry_point.split(":", 1)
    plugin_dir = _installed_entry_point_plugin_dir(entry_point, root=root)
    _ensure_no_reserved_plugin_sources(plugin_dir)
    if _entry_point_module_source(plugin_dir, module_name) is None:
        raise PluginError(
            f"Entry point {entry_point!r} for an installed plugin must resolve to "
            "a Python file inside the plugin directory."
        )
    with _PLUGIN_LOAD_LOCK:
        plugin_key = str(plugin_dir.resolve())
        fingerprint = _plugin_code_fingerprint(plugin_dir)
        previous_fingerprint = _PLUGIN_CODE_FINGERPRINTS.get(plugin_key)
        if previous_fingerprint is not None and previous_fingerprint != fingerprint:
            _purge_changed_plugin_modules(plugin_dir)
        _PLUGIN_CODE_FINGERPRINTS[plugin_key] = fingerprint
        _ensure_loaded_module_not_shadowed(module_name, plugin_dir)
        _activate_plugin_path(plugin_dir)
        importlib.invalidate_caches()
        obj = importlib.import_module(module_name)
    if not _module_loaded_from_plugin(obj, plugin_dir):
        raise PluginError(
            f"Entry point {entry_point!r} resolved outside its installed plugin directory."
        )
    for attr in attr_path.split("."):
        obj = getattr(obj, attr)
    return obj


def get_extractor_registry(root: str | Path = ".") -> dict[str, str]:
    registry = dict(EXTRACTOR_REGISTRY)
    for component in iter_components("extractor", root=root):
        language = component["language"]
        if language not in registry:
            registry[language] = component["entry_point"]
    return registry


def parallel_safe_extractor_entry_points(root: str | Path = ".") -> set[str]:
    return {
        component["entry_point"]
        for component in iter_components("extractor", root=root)
        if component.get("parallel_safe") is True
    }


def entrypoint_detector_components(root: str | Path = ".") -> list[dict[str, Any]]:
    return iter_components("entrypoint_detector", root=root)


def diagram_style_components(root: str | Path = ".") -> list[dict[str, Any]]:
    return iter_components("diagram_style", root=root)


def read_component_text(component: dict[str, Any]) -> str:
    path = Path(component["plugin_dir"]) / component["path"]
    return path.read_text(encoding="utf-8")


def find_prompt_template(template_id: str, *, root: str | Path = ".") -> dict[str, Any]:
    components = iter_components("prompt_template", root=root)
    exact = [component for component in components if component["ref"] == template_id]
    if exact:
        return exact[0]
    matches = [component for component in components if component["id"] == template_id]
    if not matches:
        raise PluginError(f"Prompt template {template_id!r} is not installed.")
    if len(matches) > 1:
        raise PluginError(
            f"Prompt template {template_id!r} is ambiguous; use plugin_id/template_id."
        )
    return matches[0]


class _SafeFormat(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _validate_prompt_template_vcs_boundary(template: str) -> None:
    if "LLM_WIKI_AUTO_COMMIT" in template or _PROMPT_GIT_MUTATION_RE.search(
        template
    ):
        raise PluginError(
            "Prompt templates cannot contain Git staging or commit commands; "
            "repository-policy handoff is owned by llm-wiki."
        )


def render_prompt_template(
    template_id: str, values: dict[str, Any], *, root: str | Path = "."
) -> str:
    component = find_prompt_template(template_id, root=root)
    template = read_component_text(component)
    _validate_prompt_template_vcs_boundary(template)
    return template.format_map(
        _SafeFormat(
            {key: "" if value is None else str(value) for key, value in values.items()}
        )
    )
