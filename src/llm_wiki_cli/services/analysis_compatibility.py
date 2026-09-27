"""Pure, versioned comparison of application-owned analysis commitments.

This module is also shipped in the isolated release harness. Keep it stdlib-only
and never resolve executable paths or declarations from knowledge documents.
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Callable, ParamSpec, TypeVar
import hashlib
import json
import re

EXTENSION = "llm-wiki/analysis-compatibility-v1"
SCHEMA = "llm-wiki-analysis-compatibility/v1"
COMPARISON_SCHEMA = "llm-wiki-analysis-comparison/v1"
POLICIES = frozenset({"auto", "exact-v1", "analysis-v1"})
_ACTIVE: ContextVar[str] = ContextVar("analysis_comparison_policy", default="auto")
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_FIELDS = frozenset({"schema_version", "component", "contract", "implementation",
                     "configuration", "runtime", "provenance", "identity"})


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                     allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def selected_policy(value: str | None = None) -> str:
    value = _ACTIVE.get() if value is None else value
    if not isinstance(value, str) or value not in POLICIES:
        raise ValueError("comparison_policy must be auto, exact-v1 or analysis-v1")
    return value


@contextmanager
def comparison_scope(value: str):
    token = _ACTIVE.set(selected_policy(value))
    try:
        yield
    finally:
        _ACTIVE.reset(token)


def validate_record(value: object, component: str | None = None) -> dict:
    if not isinstance(value, Mapping) or set(value) != _FIELDS:
        raise ValueError("analysis compatibility fields do not match v1")
    result = dict(value)
    if result["schema_version"] != SCHEMA:
        raise ValueError("unsupported analysis compatibility schema")
    for key in ("component", "contract"):
        if not isinstance(result[key], str) or not 0 < len(result[key]) <= 256:
            raise ValueError("invalid analysis component/contract")
    if component is not None and result["component"] != component:
        raise ValueError("analysis compatibility belongs to another component")
    if result["contract"] != "structural-observations/v1":
        raise ValueError("unsupported observation contract")
    if result["component"] not in {"agent-wiki-cli", *("llm-wiki/extractor/" + x for x in ("python", "typescript", "javascript", "go", "rust", "haskell", "infrastructure"))}:
        raise ValueError("unsupported analysis component")
    for key in ("implementation", "configuration", "runtime", "identity"):
        if not isinstance(result[key], str) or not _HASH.fullmatch(result[key]):
            raise ValueError("invalid analysis commitment")
    provenance = result["provenance"]
    if not isinstance(provenance, Mapping) or set(provenance) != {"python", "platform", "helper"}:
        raise ValueError("invalid analysis runtime provenance")
    if any(not isinstance(v, str) or len(v) > 8192 for v in provenance.values()):
        raise ValueError("invalid analysis runtime provenance value")
    if result["identity"] != digest({k: result[k] for k in sorted(_FIELDS - {"identity", "provenance"})}):
        raise ValueError("analysis compatibility identity differs from its inputs")
    return result


def make_record(component: str, contract: str, implementation: str,
                configuration: str, runtime: str, provenance: Mapping) -> dict:
    result = dict(schema_version=SCHEMA, component=component, contract=contract,
                  implementation=implementation, configuration=configuration,
                  runtime=runtime, provenance=dict(provenance))
    result["identity"] = digest({k: v for k, v in result.items() if k != "provenance"})
    return validate_record(result, component)


def component_record(component) -> dict | None:
    extensions = component.get("extensions", {}) if isinstance(component, Mapping) else component.extensions
    value = extensions.get(EXTENSION)
    if value is None:
        return None
    name = component["id"] if isinstance(component, Mapping) else component.component_id
    record = validate_record(value, name)
    configured = component["configuration_hash"] if isinstance(component, Mapping) else component.configuration_hash
    if configured != configuration_commitment(record):
        raise ValueError("analysis metadata is not bound by producer configuration")
    return record


def has_contract(producer) -> bool:
    return component_record(producer.tool) is not None


def committed_configuration(configuration: Mapping, record: Mapping) -> dict:
    return {"analysis_configuration": record["configuration"], "analysis_compatibility": record["identity"]}


def configuration_commitment(record: Mapping) -> str:
    return digest({"domain": "llm-wiki/component-configuration/v1", "configuration": committed_configuration({}, record)})


def compare_components(recorded, live, *, policy: str = "auto", plugins: bool = False, configuration_required: bool = True) -> str | None:
    """Return the differing basis, or None; callers map it to their contract."""
    policy = selected_policy(policy)
    def get(component, name):
        if isinstance(component, Mapping):
            return component["id" if name == "component_id" else name]
        return getattr(component, name)
    if get(recorded, "component_id") != get(live, "component_id"):
        return "id"
    for item in (recorded, live):
        if get(item, "version") == "unknown" or "version-unknown" in get(item, "limitations"):
            return "version"
        if "configuration-basis-unknown" in get(item, "limitations") or (configuration_required and get(item, "configuration_hash") is None):
            return "configuration"
    left, right = component_record(recorded), component_record(live)
    if left is not None:
        if right is None:
            return "configuration"
        if any(left[k] != right[k] for k in ("contract", "implementation", "configuration", "runtime")):
            return "configuration"
    elif policy == "analysis-v1":
        return "configuration"
    exact = policy == "exact-v1" or plugins or left is None or right is None
    if exact and get(recorded, "version") != get(live, "version"):
        return "version"
    if get(recorded, "configuration_hash") != get(live, "configuration_hash"):
        return "configuration"
    if get(recorded, "limitations") != get(live, "limitations"):
        return "limitations"
    return None


def report_schema(requested: str, details: Mapping | None, *, legacy: str = "v1") -> str:
    migrated = bool(details and details.get("schema_version") == "llm-wiki-health-details/v2")
    if requested == "auto":
        return "v4" if migrated else legacy
    if migrated and details is not None and requested != "v4" and details["basis"]["policy"] != "exact-v1":
        raise ValueError("migrated knowledge requires report-schema v4 or comparison-policy exact-v1")
    return requested


def legacy_details(details: Mapping) -> dict:
    result = json.loads(json.dumps(details))
    result["schema_version"] = "llm-wiki-health-details/v1"
    result["basis"]["policy"] = "exact-producer-versions"
    result["basis"]["analysis_contract"] = None
    result["basis"].pop("comparison", None)
    return result


_P = ParamSpec("_P")
_R = TypeVar("_R")


def comparison_entrypoint(function: Callable[_P, _R]) -> Callable[_P, _R]:
    @wraps(function)
    def wrapped(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        value = kwargs.get("comparison_policy")
        if value is None:
            return function(*args, **kwargs)
        if kwargs.get("service") is not None:
            raise ValueError("service owns its captured comparison policy")
        if not isinstance(value, str):
            raise ValueError("comparison_policy must be a string")
        with comparison_scope(value):
            return function(*args, **kwargs)
    return wrapped



def detailed_v2(details: Mapping) -> dict:
    result = json.loads(json.dumps(details))
    if result["schema_version"] == "llm-wiki-health-details/v2":
        return result
    result["schema_version"] = "llm-wiki-health-details/v2"
    result["basis"]["policy"] = "exact-v1"
    contracts: dict = {"schema_version": COMPARISON_SCHEMA}
    for side in ("recorded", "live"):
        producer = result["basis"][side]
        contracts[side] = None if producer is None else {
            c["id"]: None for c in [producer["tool"], *producer["extractors"], *producer["plugins"]]
        }
    result["basis"]["analysis_contract"] = contracts
    result["basis"]["comparison"] = basis_decision(result["basis"])
    return result



def producer_contracts(producer) -> dict:
    return {c.component_id: component_record(c) for c in (producer.tool, *producer.extractors, *producer.plugins)}


def captured_components(basis: Mapping, side: str) -> dict:
    producer = basis[side]
    if not isinstance(producer, Mapping):
        raise ValueError("analysis producer is unavailable")
    components = [producer["tool"], *producer["extractors"], *producer["plugins"]]
    analysis = basis["analysis_contract"]
    if not isinstance(analysis, Mapping) or set(analysis) != {"schema_version", "recorded", "live"} or analysis["schema_version"] != COMPARISON_SCHEMA:
        raise ValueError("unsupported analysis comparison contract")
    records = analysis[side]
    if not isinstance(records, Mapping) or set(records) != {c["id"] for c in components}:
        raise ValueError("analysis records do not cover the producer")
    result = {}
    for component in components:
        record = records[component["id"]]
        if record is not None:
            validate_record(record, component["id"])
        result[component["id"]] = {**component, "extensions": {} if record is None else {EXTENSION: record}}
        component_record(result[component["id"]])
    return result


def basis_decision(basis: Mapping) -> dict:
    def decision(state, reason, component=None):
        return {"state": state, "reason": reason, "component": component}
    if basis["recorded"] is None or basis["live"] is None:
        return decision("unavailable", "basis-unavailable")
    left, right = captured_components(basis, "recorded"), captured_components(basis, "live")
    recorded, live = basis["recorded"], basis["live"]
    for key in ("knowledge_schema_version", "generation_options_hash"):
        if recorded[key] != live[key]:
            return decision("incompatible", "schema-changed" if key == "knowledge_schema_version" else "generation-options-changed")
    if {c["id"] for c in recorded["plugins"]} != {c["id"] for c in live["plugins"]}:
        return decision("incompatible", "plugin-set-changed")
    policy = selected_policy(basis["policy"])
    for key, value in left.items():
        if key not in right:
            return decision("unavailable", "producer-component-absent", key)
        difference = compare_components(value, right[key], policy=policy,
            plugins=bool(recorded["plugins"] or live["plugins"]), configuration_required=key != recorded["tool"]["id"])
        if difference is not None:
            return decision("incompatible", {"version": "producer-version-changed", "configuration": "analysis-configuration-changed", "limitations": "producer-limitations-changed", "id": "producer-id-changed"}[difference], key)
    mode = "matching-exact-inputs" if policy == "exact-v1" or component_record(left[recorded["tool"]["id"]]) is None else "matching-analysis-inputs"
    if recorded["plugins"]:
        mode = "matching-analysis-and-exact-plugin-inputs"
    return decision("compatible", mode)


def compatible_basis(basis: Mapping) -> bool:
    return basis_decision(basis)["state"] == "compatible"



def bound_comparison(function: Callable[_P, _R]) -> Callable[_P, _R]:
    @wraps(function)
    def wrapped(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        owner = args[0]
        with comparison_scope(getattr(owner, "comparison_policy", "auto")):
            return function(*args, **kwargs)
    return wrapped
