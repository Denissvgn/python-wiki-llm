"""Operation-owned capture of installed analysis implementation and runtimes."""

from __future__ import annotations

from collections.abc import Mapping
from contextvars import ContextVar
from functools import wraps
import hashlib
import json
from pathlib import Path
import platform
import re
import sys

from . import analysis_compatibility as ac
from .immutable import FrozenDict, freeze
from copy import deepcopy

_ISSUER = object()


class _CapturedAnalysis(FrozenDict):
    _diagnostics: dict | None

    def __init__(self, values, token, diagnostics=None):
        if token is not _ISSUER:
            raise TypeError("analysis capture must be issued by its I/O owner")
        dict.__init__(self, freeze(values))
        object.__setattr__(self, "_diagnostics", freeze(diagnostics))

    def __setattr__(self, name, value):
        raise TypeError("analysis capture is immutable")

    def __deepcopy__(self, memo):
        return self


def _issued(values, diagnostics=None):
    return _CapturedAnalysis(values, _ISSUER, diagnostics)


INPUT_STATUS_SCHEMA = "llm-wiki-analysis-input-status/v1"
INPUT_STATUS_MAX_BYTES = 8192


def analysis_diagnostics(captured):
    """Return informational owner-captured diagnostics, never producer identity."""
    return deepcopy(captured._diagnostics) if isinstance(captured, _CapturedAnalysis) else None


def _input_rows(root, rules):
    excluded = {"__pycache__", "node_modules", "target"}
    python = {v.relative_to(root).as_posix() for v in root.rglob("*.py")
              if not set(v.parts) & excluded
              and not v.relative_to(root).as_posix().startswith("examples/")}
    helpers = {v.relative_to(root).as_posix() for d in (root / "extractors").glob("*_scripts")
               for v in d.rglob("*") if v.is_file() and not set(v.parts) & excluded}
    rows = [{"kind": "unclassified-python", "path": p}
            for p in sorted(python - set(rules["classified_python_files"]))]
    rows += [{"kind": "unclassified-helper", "path": p}
             for p in sorted(helpers - set(rules.get("classified_helper_files", [])))]
    return rows


def _status(rows, *, limit=20, reason=None):
    reason = reason or ("unclassified-analysis-inputs" if rows else None)
    value = {"schema_version": INPUT_STATUS_SCHEMA,
             "status": "unavailable" if reason else "ready", "reason": reason,
             "scope": "installed-provider-inputs", "registry": "services/analysis_contracts.json",
             "paths": [], "bounds": {"total": len(rows), "returned": 0,
                 "omitted": len(rows), "truncated": bool(rows),
                 "max_paths": limit, "max_bytes": INPUT_STATUS_MAX_BYTES},
             "next_action": "Review the installed provider's analysis_contracts.json census and producer input lists; classify deliberately, then rerun the preflight. Do not automatically trust or register new files.",
             "qualification": "Classification/file coverage only; not runtime/helper readiness or analysis authority."}
    if not reason:
        value["next_action"] = None
    for row in rows:
        if len(value["paths"]) == limit:
            break
        trial = deepcopy(value)
        trial["paths"].append(row)
        returned = len(trial["paths"])
        trial["bounds"].update(returned=returned, omitted=len(rows)-returned,
                               truncated=returned != len(rows))
        try:
            row["path"].encode("utf-8")
            size = len(json.dumps(trial, ensure_ascii=True, sort_keys=True).encode("utf-8"))
        except UnicodeError:
            continue
        if size <= INPUT_STATUS_MAX_BYTES:
            value = trial
    return value


def analysis_input_status(*, package_root=None, limit=20):
    """Read installed provider classification; never inventory target source or execute it."""
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("analysis input path limit must be an integer from 1 to 100")
    root = Path(package_root) if package_root is not None else Path(__file__).resolve().parents[1]
    try:
        rules = registry(root)
        rows = _input_rows(root, rules)
        required = set(rules["shared"]) | {p for paths in rules["providers"].values() for p in paths}
        for name in sorted(required):
            path = Path(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name:
                return _status([], limit=limit, reason="unsafe-registry-input")
            target = root / path
            if target.is_symlink() or not target.is_file():
                rows.append({"kind": "missing-or-unsafe-producer-input", "path": name})
        return _status(rows, limit=limit, reason="analysis-inputs-unavailable" if rows and not any(r["kind"].startswith("unclassified") for r in rows) else None)
    except (OSError, ValueError, KeyError, TypeError):
        return _status([], limit=limit, reason="analysis-registry-unavailable")


def validate_analysis_diagnostics(value):
    """Validate bounded informational task diagnostics without reading installed files."""
    keys = {"schema_version", "status", "reason", "scope", "registry", "paths", "bounds", "next_action", "qualification"}
    if not isinstance(value, dict) or set(value) != keys or value.get("schema_version") != INPUT_STATUS_SCHEMA:
        raise ValueError("invalid analysis input diagnostic")
    if (value.get("status") != "unavailable"
            or value.get("reason") not in {"unclassified-analysis-inputs", "analysis-inputs-unavailable", "analysis-registry-unavailable", "unsafe-registry-input"}
            or value.get("scope") != "installed-provider-inputs"
            or value.get("registry") != "services/analysis_contracts.json"
            or not all(isinstance(value[k], str) and value[k] for k in ("next_action", "qualification"))):
        raise ValueError("analysis diagnostic cannot establish authority")
    bounds, paths = value.get("bounds"), value.get("paths")
    if (not isinstance(bounds, dict) or set(bounds) != {"total", "returned", "omitted", "truncated", "max_paths", "max_bytes"}
            or not isinstance(paths, list)):
        raise ValueError("invalid analysis diagnostic bounds")
    for key in ("total", "returned", "omitted", "max_paths", "max_bytes"):
        if type(bounds.get(key)) is not int or bounds[key] < 0:
            raise ValueError("invalid analysis diagnostic counts")
    if (bounds["returned"] != len(paths) or bounds["total"] != bounds["returned"] + bounds["omitted"]
            or not 1 <= bounds["max_paths"] <= 100 or len(paths) > bounds["max_paths"]
            or bounds["max_bytes"] != INPUT_STATUS_MAX_BYTES
            or bounds.get("truncated") is not (bounds["omitted"] > 0)):
        raise ValueError("inconsistent analysis diagnostic bounds")
    if len(json.dumps(value, ensure_ascii=True, sort_keys=True).encode()) > INPUT_STATUS_MAX_BYTES:
        raise ValueError("analysis diagnostic exceeds byte ceiling")
    for row in paths:
        if not isinstance(row, dict) or set(row) != {"kind", "path"}:
            raise ValueError("invalid analysis diagnostic row")
        if row["kind"] not in {"unclassified-python", "unclassified-helper", "missing-or-unsafe-producer-input"}:
            raise ValueError("invalid analysis diagnostic kind")
        p = row["path"]
        if not isinstance(p, str) or Path(p).is_absolute() or ".." in Path(p).parts or "\\" in p:
            raise ValueError("invalid analysis diagnostic path")


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
    try:
        rules = registry(root)
        unclassified = _input_rows(root, rules)
    except (OSError, ValueError, KeyError, TypeError):
        return _issued({}, _status([], reason="analysis-registry-unavailable"))
    if unclassified:
        return _issued({}, _status(unclassified))
    cache_key += (ac.digest(rules),)
    required = set(rules["shared"]) | {
        p for language in selected
        for p in rules["providers"].get("typescript" if language == "javascript" else language, [])
    }
    present = all((root / p).is_file() and not (root / p).is_symlink() for p in required)
    if present and cache is not None and cache_key in cache:
        return cache[cache_key]
    profile = [sys.platform, sys.version_info.major, sys.version_info.minor, platform.machine().casefold()]
    runtime = {"implementation": platform.python_implementation(), "version": platform.python_version(),
               "platform": sys.platform, "machine": platform.machine()}
    if not all(isinstance(value, str) and value for value in runtime.values()):
        return _issued({})
    portable = platform.python_implementation() == "CPython" and profile in rules["portable_python_profiles"]
    python_identity = {"profile": "qualified-python-observations/v1"} if portable else runtime
    provenance = {"python": platform.python_version(), "platform": sys.platform + "/" + platform.machine(), "helper": ""}
    result = {}
    diagnostics = None
    try:
        common = implementation_hash(root, rules["shared"])
    except (OSError, ValueError):
        return _issued(result, analysis_input_status(package_root=root))
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
            dependencies = {}
            portable_helper = False
            if owner not in {"python", "infrastructure"}:
                helper_root = extractor_helpers.resolve_helper_cache_root(source_root, helper_cache_dir)
                prepared = None if helper_root is None else extractor_helpers._manifest_current(helper_root, owner)
                if prepared is None or not prepared.get("toolchain"):
                    continue
                helper = prepared["toolchain"]
                if owner == "typescript":
                    artifact = prepared.get("artifact_fingerprint")
                    if (prepared.get("artifact_scope") != extractor_helpers.ts_identity.ARTIFACT_SCOPE
                            or not isinstance(artifact, str)
                            or re.fullmatch(r"sha256:[0-9a-f]{64}", artifact) is None):
                        continue
                    dependencies["helper_artifact"] = {
                        "scope": prepared["artifact_scope"],
                        "fingerprint": artifact,
                    }
                    active_node = extractor_helpers.command_output(["node", "--version"])
                    if not active_node or re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:[-+].+)?", active_node) is None:
                        continue
                    portable_helper = (
                        helper == rules.get("portable_helper_toolchains", {}).get(owner)
                        and helper.startswith("node " + active_node + ";")
                        and sys.platform in rules.get("portable_helper_platforms", {}).get(owner, [])
                    )
                    helper += "; active-node " + active_node
            if owner == "infrastructure":
                from importlib.metadata import version
                dependencies["PyYAML"] = version("PyYAML")
            result["llm-wiki/extractor/" + language] = {
                "implementation": implementation,
                "runtime": ac.digest({"python": python_identity if owner == "python" or portable_helper else runtime, "helper": helper, "dependencies": dependencies}),
                "provenance": {**provenance, "helper": helper},
            }
        except (OSError, ValueError):
            status = analysis_input_status(package_root=root)
            if status["status"] == "unavailable":
                diagnostics = status
            continue
    if "llm-wiki/extractor/typescript" in result and "javascript" not in registry_entries:
        result["llm-wiki/extractor/javascript"] = result["llm-wiki/extractor/typescript"]
    if cache is not None:
        cache[cache_key] = _issued(result, diagnostics)
    return _issued(result, diagnostics)


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
