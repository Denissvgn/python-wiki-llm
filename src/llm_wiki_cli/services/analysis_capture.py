"""Operation-owned capture of installed analysis implementation and runtimes."""

from __future__ import annotations

from collections.abc import Mapping
from contextvars import ContextVar
from functools import wraps
import hashlib
import json
from pathlib import Path
import platform
import sys

from . import analysis_compatibility as ac
from .immutable import FrozenDict, freeze

_ISSUER = object()


class _CapturedAnalysis(FrozenDict):
    def __init__(self, values, token):
        if token is not _ISSUER:
            raise TypeError("analysis capture must be issued by its I/O owner")
        dict.__init__(self, freeze(values))

    def __deepcopy__(self, memo):
        return self


def _issued(values):
    return _CapturedAnalysis(values, _ISSUER)


_CAPTURE: ContextVar[dict | None] = ContextVar("analysis_capture", default=None)


def capture_operation(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        token = _CAPTURE.set({})
        try:
            return function(*args, **kwargs)
        finally:
            _CAPTURE.reset(token)
    return wrapped


REGISTRY_PATH = Path(__file__).with_name("analysis_contracts.json")


def registry(root: Path | None = None) -> dict:
    path = REGISTRY_PATH if root is None else root / "services/analysis_contracts.json"
    value = json.loads(path.read_text("utf-8"))
    if value.get("schema_version") != "llm-wiki-analysis-registry/v1":
        raise ValueError("unsupported analysis registry")
    return value


def implementation_hash(root: Path, paths: list[str]) -> str:
    hashes = {}
    for name in sorted(set(paths)):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("missing or redirected analysis input: " + name)
        raw = path.read_bytes()
        hashes[name] = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    return ac.digest(hashes)


def capture_analysis(registry_entries: Mapping[str, str], *, helper_cache_dir=None,
                     source_root: str | Path = ".", languages=None, package_root: Path | None = None) -> dict:
    """Capture immutable JSON inputs once; unavailable providers stay unknown."""
    from . import extractor_helpers
    root = package_root or Path(__file__).resolve().parents[1]
    cache = _CAPTURE.get()
    selected = set(registry_entries if languages is None else languages)
    if "javascript" in selected and "javascript" not in registry_entries:
        selected.discard("javascript")
        selected.add("typescript")
    selected.add("infrastructure")
    cache_key = (str(root), str(source_root), str(helper_cache_dir), tuple(sorted(registry_entries.items())), tuple(sorted(selected)))
    if cache is not None and cache_key in cache:
        return cache[cache_key]
    rules = registry(root)
    discovered = {v.relative_to(root).as_posix() for v in root.rglob("*.py") if not set(v.parts) & {"__pycache__", "node_modules", "target"} and not v.relative_to(root).as_posix().startswith("examples/")}
    helper_files = {v.relative_to(root).as_posix() for directory in (root / "extractors").glob("*_scripts") for v in directory.rglob("*") if v.is_file() and not set(v.parts) & {"__pycache__", "node_modules", "target"}}
    if helper_files - set(rules.get("classified_helper_files", [])):
        return _issued({})
    if discovered - set(rules["classified_python_files"]):
        return _issued({})
    profile = [sys.platform, sys.version_info.major, sys.version_info.minor]
    runtime = {"implementation": platform.python_implementation(), "version": platform.python_version(),
               "platform": sys.platform, "machine": platform.machine()}
    if not all(isinstance(value, str) and value for value in runtime.values()):
        return _issued({})
    portable = (platform.python_implementation() == "CPython" and profile in rules["portable_python_profiles"]
                and platform.machine().casefold() in {"x86_64", "amd64", "arm64", "aarch64"})
    python_identity = {"profile": "qualified-python-observations/v1"} if portable else runtime
    provenance = {"python": platform.python_version(), "platform": sys.platform + "/" + platform.machine(), "helper": ""}
    result = {}
    try:
        common = implementation_hash(root, rules["shared"])
    except (OSError, ValueError):
        return _issued(result)
    result["agent-wiki-cli"] = {"implementation": common, "runtime": ac.digest(python_identity), "provenance": provenance}
    for language in sorted(selected):
        owner = "typescript" if language == "javascript" and "javascript" not in registry_entries else language
        if owner not in rules["providers"]:
            continue
        if owner != "infrastructure" and registry_entries.get(owner) != rules["executors"].get(owner):
            continue
        try:
            implementation = implementation_hash(root, rules["providers"][owner])
            helper = ""
            if owner not in {"python", "infrastructure"}:
                helper_root = extractor_helpers.resolve_helper_cache_root(source_root, helper_cache_dir)
                prepared = None if helper_root is None else extractor_helpers._manifest_current(helper_root, owner)
                if prepared is None or not prepared.get("toolchain"):
                    continue
                helper = prepared["toolchain"]
            dependencies = {}
            if owner == "infrastructure":
                from importlib.metadata import version
                dependencies["PyYAML"] = version("PyYAML")
            result["llm-wiki/extractor/" + language] = {
                "implementation": implementation,
                "runtime": ac.digest({"python": python_identity if owner == "python" or sys.platform in rules.get("portable_helper_platforms", {}).get(owner, []) else runtime, "helper": helper, "dependencies": dependencies}),
                "provenance": {**provenance, "helper": helper},
            }
        except (OSError, ValueError):
            continue
    if "llm-wiki/extractor/typescript" in result and "javascript" not in registry_entries:
        result["llm-wiki/extractor/javascript"] = result["llm-wiki/extractor/typescript"]
    if cache is not None:
        cache[cache_key] = _issued(result)
    return _issued(result)


def attach(component, captured: Mapping | None):
    from dataclasses import replace
    from .knowledge_envelope import hash_component_configuration
    if ac.EXTENSION in component.extensions:
        raise ValueError("analysis compatibility is owned by the producer")
    if captured is None:
        return component
    if not isinstance(captured, _CapturedAnalysis):
        raise ValueError("analysis input must be an owner-issued immutable capture")
    row = captured.get(component.component_id)
    if row is None:
        return replace(component, configuration=None, limitations=tuple(sorted(set(component.limitations) | {"configuration-basis-unknown"})))
    if component.configuration is None:
        return component
    record = ac.make_record(component.component_id, "structural-observations/v1", row["implementation"],
                            hash_component_configuration(component.configuration), row["runtime"], row["provenance"])
    return replace(component, configuration=ac.committed_configuration(component.configuration, record),
                   extensions={**component.extensions, ac.EXTENSION: record})
