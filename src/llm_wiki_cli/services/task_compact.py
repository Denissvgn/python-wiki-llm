"""Pure, canonical-bound task presentation with separately counted view budgets."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
import json
from typing import Any

from .context_budget import _accounted_render
from .immutable import freeze
from .request_json import _pairs, _constant
from .task_context import validate_task_context, _counter, _LIMITATIONS
from .task_contract import TaskContext, TASK_REQUEST_SCHEMA_V2, normalize_task_request
from .workflow_profile import canonical_json, content_id
from .task_compact_readable import readable_projection, readable_expansion

COMPACT_SCHEMA = "llm-wiki-task-compact/v1"
VIEW_REQUEST_SCHEMA = "llm-wiki-task-view-request/v1"
COMPACT_SCHEMA_V2 = "llm-wiki-task-compact/v2"
VIEW_REQUEST_SCHEMA_V2 = "llm-wiki-task-view-request/v2"
FACT_COLUMNS = (
    "fact_id",
    "facet",
    "selector",
    "state",
    "observation",
    "citation_refs",
    "qualification",
)
REQUIREMENT_COLUMNS = (
    "id",
    "facet",
    "selector",
    "criterion",
    "state",
    "satisfied",
    "reason",
    "fact_refs",
)

_LIMIT_SUMMARIES = (
    "Emitted evidence does not evaluate semantic/task adequacy.",
    "Static graph observations never prove runtime absence.",
    "Selected reads may inspect control/package/infrastructure metadata.",
    "Input byte ceilings exclude parser/revalidation work.",
    "Unsaved buffers are excluded; follow-ups remain inert.",
)
_NATIVE_OFF = {
    "status": "off",
    "reason": None,
    "lookup_complete": False,
    "validation_scope": "selected-committed-records",
    "whole_store_validated": False,
    "unverified_records": {},
}


def _encode_limits(values):
    return [
        {"summary": _LIMIT_SUMMARIES[_LIMITATIONS.index(value)]}
        if value in _LIMITATIONS
        else {"text": value}
        for value in values
    ]


def _decode_limits(values):
    return [
        _LIMITATIONS[_LIMIT_SUMMARIES.index(value["summary"])]
        if "summary" in value
        else value["text"]
        for value in values
    ]


class TaskCompactError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class CompactTaskContext:
    ok: bool
    rendered: str
    accounting: Mapping[str, Any]
    canonical_text: str
    canonical_accounting: Mapping[str, Any]
    error: str | None = None
    schema_version: str = COMPACT_SCHEMA
    diagnostic_rendered: str = ""

    def __post_init__(self):
        object.__setattr__(self, "accounting", freeze(deepcopy(dict(self.accounting))))
        object.__setattr__(
            self,
            "canonical_accounting",
            freeze(deepcopy(dict(self.canonical_accounting))),
        )

    @property
    def view_id(self):
        return self.to_payload().get("view_id")

    def to_payload(self):
        if self.ok:
            return json.loads(self.rendered)
        if self.diagnostic_rendered:
            return json.loads(self.diagnostic_rendered)
        return {
            "schema_version": self.schema_version,
            "ok": False,
            "error": self.error,
            "accounting": deepcopy(dict(self.accounting)),
        }


def normalize_view_options(value, *, ceiling):
    if not isinstance(value, Mapping) or set(value) != {
        "schema_version",
        "budget_tokens",
    }:
        raise TaskCompactError(
            "invalid-view-request",
            "View options require schema_version and budget_tokens",
        )
    budget = value["budget_tokens"]
    if (
        value["schema_version"] not in (VIEW_REQUEST_SCHEMA, VIEW_REQUEST_SCHEMA_V2)
        or type(budget) is not int
        or not 1 <= budget <= ceiling
    ):
        raise TaskCompactError(
            "invalid-view-request",
            "Compact budget must narrow the trusted effective ceiling",
        )
    return {"schema_version": value["schema_version"], "budget_tokens": budget}


class _CheckedCounter:
    def __init__(self, counter):
        self.counter = counter
        self.identity = counter.identity
        self.exact = counter.exact

    def count(self, text):
        if (
            self.counter.identity != self.identity
            or self.counter.exact is not self.exact
        ):
            raise TaskCompactError(
                "invalid-counter", "Trusted counter identity changed"
            )
        result = self.counter.count(text)
        if type(result) is not int or result < 0:
            raise TaskCompactError(
                "invalid-counter", "Trusted counts must be nonnegative integers"
            )
        if (
            self.counter.identity != self.identity
            or self.counter.exact is not self.exact
        ):
            raise TaskCompactError(
                "invalid-counter", "Trusted counter identity changed"
            )
        return result


def _validated(canonical_text, request, profile, policy, counter):
    if isinstance(canonical_text, TaskContext):
        if not canonical_text.ok:
            raise TaskCompactError(
                "canonical-unavailable",
                "An unsuccessful canonical result has no compact context",
            )
        canonical_text = canonical_text.rendered
    if not isinstance(canonical_text, str):
        raise TaskCompactError(
            "canonical-invalid", "Canonical context must be original text"
        )
    normalized, effective = normalize_task_request(
        request, profile=profile, policy=policy
    )
    if normalized["schema_version"] != TASK_REQUEST_SCHEMA_V2:
        raise TaskCompactError(
            "unsupported-canonical-schema", "Compact presentation requires task v2"
        )
    trusted = _counter(effective.settings, counter)
    if type(trusted.exact) is not bool:
        raise TaskCompactError(
            "invalid-counter", "Counter exactness must be a trusted boolean"
        )
    trusted = _CheckedCounter(trusted)
    payload = validate_task_context(
        canonical_text, request, profile=profile, policy=policy, counter=trusted
    )
    return canonical_text, payload, normalized, effective, trusted


def _same(first, second):
    return canonical_json(first) == canonical_json(second)


def _encode_contract(value):
    """Only explicit, present known defaults can use a reversible codec."""
    if not isinstance(value, dict):
        return {"codec": "qualified-json", "value": deepcopy(value)}
    defaults = {"docstring": "", "decorators": [], "is_async": False}
    method_fields = {"name", "line", "params", "return_type", "data_effects", *defaults}
    if method_fields == set(value):
        result = {
            key: deepcopy(item)
            for key, item in value.items()
            if key not in defaults or not _same(item, defaults[key])
        }
        inputs_from_parameters = False
        effects = result.get("data_effects")
        params = value["params"]
        if isinstance(effects, dict) and isinstance(params, list):
            derived = [
                {
                    "kind": "param",
                    "parameter_kind": p["kind"],
                    **{key: item for key, item in p.items() if key != "kind"},
                }
                for p in params
                if isinstance(p, dict) and "kind" in p
            ]
            if (
                len(derived) == len(params)
                and "inputs" in effects
                and _same(effects["inputs"], derived)
            ):
                effects.pop("inputs")
                inputs_from_parameters = True
        return {
            "codec": "method-v1",
            "value": result,
            "inputs_from_parameters": inputs_from_parameters,
        }
    class_defaults = {"attributes": [], "bases": [], "decorators": []}
    class_fields = {
        "name",
        "kind",
        "line",
        "docstring",
        "methods",
        "python_constructor_dispatch",
        *class_defaults,
    }
    if class_fields == set(value) and isinstance(value["methods"], list):
        result = {
            key: deepcopy(item)
            for key, item in value.items()
            if key not in class_defaults or not _same(item, class_defaults[key])
        }
        result["methods"] = [_encode_contract(method) for method in value["methods"]]
        return {"codec": "class-v1", "value": result}
    return {"codec": "qualified-json", "value": deepcopy(value)}


def _decode_contract(value):
    codec, result = value["codec"], deepcopy(value["value"])
    if codec == "class-v1":
        result = {"attributes": [], "bases": [], "decorators": [], **result}
        result["methods"] = [_decode_contract(method) for method in result["methods"]]
    elif codec == "method-v1":
        result = {"docstring": "", "decorators": [], "is_async": False, **result}
        effects = result.get("data_effects")
        if value.get("inputs_from_parameters") is True:
            if not isinstance(effects, dict):
                raise TaskCompactError("invalid-projection", "Derived inputs require a captured effects map")
            effects["inputs"] = [
                {
                    "kind": "param",
                    "parameter_kind": p["kind"],
                    **{key: item for key, item in p.items() if key != "kind"},
                }
                for p in result["params"]
            ]
    elif codec != "qualified-json":
        raise TaskCompactError("invalid-projection", "Unknown contract codec")
    return result


def _encode_observation(facet, value):
    if facet == "source-contract" and isinstance(value, dict) and "contract" in value:
        return {
            "codec": "source-contract-v1",
            "value": {
                **deepcopy(value),
                "contract": _encode_contract(value["contract"]),
            },
        }
    if facet in {"callers", "callees"} and isinstance(value, dict):
        owner = value.get("callable")
        if owner is not None and _same(value.get("matches"), [owner]):
            result = {
                key: deepcopy(item) for key, item in value.items() if key != "matches"
            }
            return {"codec": "selected-calls-v1", "value": result}
    # Unknown/new facets, extensions and qualification shapes retain full data.
    return {"codec": "qualified-json", "value": deepcopy(value)}


def _decode_observation(value):
    codec, result = value["codec"], deepcopy(value["value"])
    if codec == "source-contract-v1":
        result["contract"] = _decode_contract(result["contract"])
    elif codec == "selected-calls-v1":
        result["matches"] = [deepcopy(result["callable"])]
    elif codec != "qualified-json":
        raise TaskCompactError("invalid-projection", "Unknown observation codec")
    return result


def _projection(canonical, request):
    facts = canonical["facts"]
    shared = {}
    if facts:
        shared = {
            key: deepcopy(value)
            for key, value in facts[0]["qualification"].items()
            if all(
                key in fact["qualification"]
                and _same(value, fact["qualification"][key])
                for fact in facts
            )
        }
    citations, rows = [], []
    for fact in facts:
        references = []
        for citation in fact["citations"]:
            index = next(
                (i for i, item in enumerate(citations) if _same(item, citation)), None
            )
            if index is None:
                index = len(citations)
                citations.append(deepcopy(citation))
            references.append(index)
        rows.append(
            [
                fact["fact_id"],
                fact["facet"],
                fact["selector"],
                fact["state"],
                _encode_observation(fact["facet"], fact["observation"]),
                references,
                {
                    key: deepcopy(value)
                    for key, value in fact["qualification"].items()
                    if key not in shared
                },
            ]
        )
    indexes = {fact["fact_id"]: index for index, fact in enumerate(facts)}
    requirements = []
    coverage = {item["requirement_id"]: item for item in canonical["coverage"]}
    for requirement in request["requirements"]:
        item = coverage[requirement["id"]]
        requirements.append(
            [
                requirement["id"],
                requirement["facet"],
                requirement["selector"],
                requirement["criterion"],
                item["state"],
                item["satisfied"],
                item["reason"],
                [indexes[key] for key in item["fact_ids"]],
            ]
        )
    storage = canonical["storage"]
    native = {
        key: deepcopy(storage[key])
        for key in (
            "status",
            "reason",
            "lookup_complete",
            "validation_scope",
            "whole_store_validated",
            "unverified_records",
        )
    }
    intent = {key: request[key] for key in ("kind", "text", "task_ref")}
    if intent["text"] == "":
        intent.pop("text")
    if intent["task_ref"] is None:
        intent.pop("task_ref")
    return {
        "canonical": {
            key: canonical[key]
            for key in ("task_id", "request_id", "result_id", "profile_id")
        },
        "intent": intent,
        "state": canonical["state"],
        "capture": {
            key: deepcopy(canonical["basis"][key])
            for key in (
                "scope",
                "paths",
                "changes",
                "native_availability_required",
                "source_selection_compatible",
            )
        },
        "native": {"status": "off"} if _same(native, _NATIVE_OFF) else native,
        "anchors": deepcopy(canonical["anchors"]),
        "facts": {"columns": list(FACT_COLUMNS), "rows": rows},
        "citations": citations,
        "shared_qualification": shared,
        "requirements": {"columns": list(REQUIREMENT_COLUMNS), "rows": requirements},
        "omissions": deepcopy(canonical["omissions"]),
        "followups": deepcopy(canonical["followups"]),
        "limitations": _encode_limits(canonical["limitations"]),
    }


def _expanded(payload):
    facts = []
    for row in payload["facts"]["rows"]:
        fact: dict[str, Any] = dict(zip(FACT_COLUMNS, row))
        fact["observation"] = _decode_observation(fact["observation"])
        fact["citations"] = [
            deepcopy(payload["citations"][index]) for index in fact.pop("citation_refs")
        ]
        fact["qualification"] = {
            **deepcopy(payload["shared_qualification"]),
            **fact["qualification"],
        }
        facts.append(fact)
    requirements, coverage = [], []
    for row in payload["requirements"]["rows"]:
        item = dict(zip(REQUIREMENT_COLUMNS, row))
        requirements.append(
            {key: item[key] for key in ("id", "facet", "selector", "criterion")}
        )
        coverage.append(
            {
                "requirement_id": item["id"],
                "state": item["state"],
                "satisfied": item["satisfied"],
                "reason": item["reason"],
                "fact_ids": [facts[index]["fact_id"] for index in item["fact_refs"]],
            }
        )
    common = {
        key: deepcopy(payload[key])
        for key in (
            "canonical",
            "state",
            "capture",
            "anchors",
            "omissions",
            "followups",
        )
    }
    common["intent"] = {"text": "", "task_ref": None, **deepcopy(payload["intent"])}
    common["native"] = deepcopy(
        _NATIVE_OFF if payload["native"] == {"status": "off"} else payload["native"]
    )
    common["limitations"] = _decode_limits(payload["limitations"])
    return {
        **common,
        "facts": facts,
        "requirements": requirements,
        "coverage": coverage,
    }


def render_compact_task_context(
    canonical_text, request, *, view_options, profile=None, policy=None, counter=None
):
    text, canonical, normalized, effective, trusted = _validated(
        canonical_text, request, profile, policy, counter
    )
    options = normalize_view_options(
        view_options, ceiling=effective.settings["budget_tokens"]
    )
    schema = (COMPACT_SCHEMA_V2 if options["schema_version"] == VIEW_REQUEST_SCHEMA_V2
              else COMPACT_SCHEMA)
    projection = (readable_projection(canonical, normalized) if schema == COMPACT_SCHEMA_V2
                  else _projection(canonical, normalized))
    accounting = {
        "budget_tokens": options["budget_tokens"],
        "used_tokens": 0,
        "counter_id": trusted.identity,
        "mode": effective.settings["budget_mode"],
        "exact_compliance": effective.settings["budget_mode"] == "exact"
        and trusted.exact,
        "usage_kind": "upper-bound-including-accounting",
        "scope": "emitted-text-without-host-chat-framing",
    }

    def render(value):
        payload = {
            "schema_version": schema,
            "ok": True,
            **projection,
            "accounting": dict(value),
        }
        payload["view_id"] = content_id(schema, payload)
        return canonical_json(payload).decode("utf-8")

    rendered = _accounted_render(render, accounting, trusted)
    if accounting["used_tokens"] > options["budget_tokens"]:
        failure = {
            **accounting,
            "minimum_tokens": accounting["used_tokens"],
            "exact_compliance": False,
        }
        diagnostic_accounting = {
            "budget_tokens": options["budget_tokens"],
            "used_tokens": 0,
            "counter_id": trusted.identity,
            "mode": effective.settings["budget_mode"],
            "usage_kind": "upper-bound-including-accounting",
            "scope": "failure-diagnostic-text-without-host-framing",
        }

        def render_diagnostic(value):
            return canonical_json(
                {
                    "schema_version": schema,
                    "ok": False,
                    "error": "cannot-fit-compact",
                    "accounting": failure,
                    "diagnostic_accounting": dict(value),
                }
            ).decode("utf-8")

        diagnostic = _accounted_render(
            render_diagnostic, diagnostic_accounting, trusted
        )
        return CompactTaskContext(
            False,
            "",
            failure,
            text,
            canonical["accounting"],
            "cannot-fit-compact",
            schema_version=schema,
            diagnostic_rendered=diagnostic,
        )
    return CompactTaskContext(True, rendered, accounting, text, canonical["accounting"],
                              schema_version=schema)


def validate_compact_task_context(
    compact_text,
    canonical_text,
    request,
    *,
    view_options,
    profile=None,
    policy=None,
    counter=None,
):
    expected = render_compact_task_context(
        canonical_text,
        request,
        view_options=view_options,
        profile=profile,
        policy=policy,
        counter=counter,
    )
    if not expected.ok or not isinstance(compact_text, str):
        raise TaskCompactError(
            "compact-unavailable", "No successful compact context fits this request"
        )
    try:
        payload = json.loads(
            compact_text, object_pairs_hook=_pairs, parse_constant=_constant
        )
    except (ValueError, TypeError, RecursionError) as exc:
        raise TaskCompactError(
            "compact-invalid", "Compact context must be canonical JSON"
        ) from exc
    if (
        canonical_json(payload).decode("utf-8") != compact_text
        or compact_text != expected.rendered
    ):
        raise TaskCompactError(
            "compact-mismatch",
            "Compact context differs from the validated canonical projection",
        )
    return deepcopy(payload)


def expand_compact_task_context(
    compact_text,
    canonical_text,
    request,
    *,
    view_options,
    profile=None,
    policy=None,
    counter=None,
):
    payload = validate_compact_task_context(
        compact_text,
        canonical_text,
        request,
        view_options=view_options,
        profile=profile,
        policy=policy,
        counter=counter,
    )
    return (readable_expansion(payload) if payload["schema_version"] == COMPACT_SCHEMA_V2
            else _expanded(payload))
