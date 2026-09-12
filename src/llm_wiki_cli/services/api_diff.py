"""Conservative compatibility checks over supplied OpenAPI exports only."""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from collections.abc import Mapping

from .api_contracts import (
    ApiContractError,
    _dereference,
    _openapi_operations,
    load_openapi_document,
)

API_DIFF_VERSION = "llm-wiki-api-diff/v1"
_UNCERTAIN_SCHEMA = {
    "allOf",
    "anyOf",
    "oneOf",
    "not",
    "if",
    "then",
    "else",
    "$dynamicRef",
    "dependentRequired",
}


def _hash(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()


def _route(path):
    return re.sub(r"\{[^}]+\}", "{}", path)


def _key(operation):
    return operation["method"], _route(operation["path"])


def _wire_key(parameter, path):
    name, location = parameter["wire_name"], parameter["location"]
    if location == "header":
        name = name.casefold()
        if name in {"accept", "content-type", "authorization"}:
            return None
    if location == "path":
        slots = re.findall(r"\{([^}]+)\}", path)
        name = str(slots.index(name)) if name in slots else name
    return location, name


def _requirements(schema, document, *, prefix="", seen=(), depth=0):
    """Only plain object/array schemas; composition and recursion stay unknown."""
    if depth > 32 or not isinstance(schema, Mapping):
        return set(), True
    ref = schema.get("$ref")
    if ref and (ref in seen or len(schema) > 1):
        return set(), True
    diagnostics = []
    schema = _dereference(schema, document, diagnostics, context="request schema")
    if (
        diagnostics
        or not isinstance(schema, Mapping)
        or _UNCERTAIN_SCHEMA & schema.keys()
    ):
        return set(), True
    seen = (*seen, ref) if ref else seen
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    if (
        not isinstance(required, list)
        or not all(isinstance(x, str) for x in required)
        or not isinstance(properties, Mapping)
    ):
        return set(), True
    result, unknown = set(), False
    for name in required:
        prop = _dereference(
            properties.get(name, {}), document, diagnostics, context=name
        )
        if not isinstance(prop, Mapping):
            unknown = True
        elif prop.get("readOnly") is not True:
            result.add(prefix + "/" + name.replace("~", "~0").replace("/", "~1"))
    for name, prop in properties.items():
        if isinstance(prop, Mapping) and prop.get("readOnly") is True:
            continue
        nested, uncertain = _requirements(
            prop,
            document,
            prefix=prefix + "/" + str(name).replace("~", "~0").replace("/", "~1"),
            seen=seen,
            depth=depth + 1,
        )
        result.update(nested)
        unknown |= uncertain
    if "items" in schema:
        nested, uncertain = _requirements(
            schema["items"], document, prefix=prefix + "/*", seen=seen, depth=depth + 1
        )
        result.update(nested)
        unknown |= uncertain
    return result, unknown or bool(diagnostics)


def _raw_operation(loaded, operation):
    diagnostics = []
    item = _dereference(
        loaded["document"]["paths"][operation["path"]],
        loaded["document"],
        diagnostics,
        context=operation["path"],
    )
    return item[operation["method"].lower()]


def _body_requirements(loaded, operation):
    diagnostics = []
    raw = _raw_operation(loaded, operation).get("requestBody")
    if raw is None:
        return {}, False
    body = _dereference(raw, loaded["document"], diagnostics, context="request body")
    if not isinstance(body, Mapping) or not isinstance(body.get("content"), Mapping):
        return {}, True
    result, unknown = {}, bool(diagnostics)
    for media, value in body["content"].items():
        if not isinstance(value, Mapping):
            unknown = True
            continue
        required, uncertain = _requirements(value.get("schema", {}), loaded["document"])
        result[media] = required
        unknown |= uncertain
    return result, unknown


def _normalization_diagnostics(loaded, diagnostics):
    """Do not interpret an unreadable path or operation as a known removal."""
    document = loaded["document"]
    for path, raw in document["paths"].items():
        item = _dereference(raw, document, diagnostics, context=str(path))
        if not isinstance(item, Mapping):
            diagnostics.append(
                {
                    "context": str(path),
                    "message": "Path Item is unavailable or malformed",
                }
            )
            continue
        for method in (
            "get",
            "put",
            "post",
            "delete",
            "options",
            "head",
            "patch",
            "trace",
        ):
            if method in item and not isinstance(item[method], Mapping):
                diagnostics.append(
                    {
                        "context": str(path),
                        "message": f"{method.upper()} operation is malformed",
                    }
                )


def compare_exports(baseline, candidate):
    """Compare already loaded exports, reusing the authoritative normalizer."""
    old_ops, old_diagnostics = _openapi_operations(baseline)
    new_ops, new_diagnostics = _openapi_operations(candidate)
    _normalization_diagnostics(baseline, old_diagnostics)
    _normalization_diagnostics(candidate, new_diagnostics)
    findings = []

    def finding(code, severity, operation, detail):
        value = {
            "code": code,
            "severity": severity,
            "operation": operation,
            "detail": detail,
        }
        value["id"] = "sha256:" + _hash(value)
        if value not in findings:
            findings.append(value)

    for side, diagnostics in (
        ("baseline", old_diagnostics),
        ("candidate", new_diagnostics),
    ):
        for item in diagnostics:
            finding(
                "unresolved-contract",
                "advisory",
                str(item.get("context", "")),
                f"{side}: {item['message']}",
            )
    new = {_key(op): op for op in new_ops}
    duplicates = {
        key
        for operations in (new_ops, old_ops)
        for key, count in Counter(_key(op) for op in operations).items()
        if count > 1
    }
    if baseline["document"].get("components") != candidate["document"].get(
        "components"
    ):
        finding(
            "components-changed",
            "advisory",
            "",
            "Shared schema, security, or reference components changed; review their consumers",
        )
    for old in old_ops:
        key = _key(old)
        label = f"{old['method']} {old['path']}"
        updated = new.get(key)
        if key in duplicates:
            finding(
                "ambiguous-route",
                "advisory",
                label,
                "Multiple paths have the same wire route shape",
            )
            continue
        if updated is None:
            ambiguous = any(
                _route(str(item.get("context", ""))) == key[1]
                for item in new_diagnostics
            )
            finding(
                "operation-removed",
                "advisory" if ambiguous else "breaking",
                label,
                "Candidate operation is unresolved"
                if ambiguous
                else "Operation is absent from candidate",
            )
            continue
        new_label = f"{updated['method']} {updated['path']}"
        uncertain = any(
            str(item.get("context", "")) == op["path"]
            or str(item.get("context", "")).startswith(ctx)
            for diagnostics, op, ctx in (
                (old_diagnostics, old, label),
                (new_diagnostics, updated, new_label),
            )
            for item in diagnostics
        )
        severity = "advisory" if uncertain else "breaking"
        old_params = {_wire_key(p, old["path"]): p for p in old["parameters"]}
        for parameter in updated["parameters"]:
            wire = _wire_key(parameter, updated["path"])
            if wire is None:
                continue
            previous = old_params.get(wire)
            if parameter["required"] and not (previous and previous["required"]):
                valid = (
                    wire[0] in {"query", "header", "cookie", "path"}
                    and wire[1] != "unknown"
                )
                finding(
                    "required-input-added",
                    severity if valid else "advisory",
                    label,
                    f"Newly required {wire[0]} input: {wire[1]}",
                )
        old_body, new_body = old.get("request_body"), updated.get("request_body")
        if (
            new_body
            and new_body["required"]
            and not (old_body and old_body["required"])
        ):
            finding(
                "required-input-added",
                severity,
                label,
                "Request body is newly required",
            )
        old_fields, old_unknown = _body_requirements(baseline, old)
        new_fields, new_unknown = _body_requirements(candidate, updated)
        if old_unknown or new_unknown:
            finding(
                "request-schema-unknown",
                "advisory",
                label,
                "Request schema composition, recursion, or unresolved references require review",
            )
        else:
            for media in sorted(old_fields.keys() & new_fields.keys()):
                for field in sorted(new_fields[media] - old_fields[media]):
                    finding(
                        "required-input-added",
                        severity,
                        label,
                        f"Newly required {media} body property: {field}",
                    )
        old_codes = {str(r["status_code"]) for r in old["responses"]}
        new_codes = {str(r["status_code"]) for r in updated["responses"]}
        for code in sorted(old_codes - new_codes):
            if re.fullmatch(r"2\d\d", code) and not {"2XX", "default"} & new_codes:
                finding(
                    "success-response-removed",
                    severity,
                    label,
                    f"Success response {code} is absent from candidate",
                )
            elif code == "2XX":
                finding(
                    "response-range-changed",
                    "advisory",
                    label,
                    "Success response range changed; inspect remaining coverage",
                )
        if _raw_operation(baseline, old) != _raw_operation(candidate, updated):
            finding(
                "contract-changed",
                "advisory",
                label,
                "Other schema, security, serialization, or metadata changes are outside this gate; review the exports",
            )
    findings.sort(key=lambda f: (f["operation"], f["code"], f["detail"], f["severity"]))
    breaking = sum(f["severity"] == "breaking" for f in findings)

    def identity(loaded):
        return {
            "path": loaded["path"],
            "sha256": loaded["sha256"],
            "openapi": loaded["version"],
            "document_id": "sha256:" + _hash(loaded["document"]),
        }

    return {
        "schema_version": API_DIFF_VERSION,
        "baseline": identity(baseline),
        "candidate": identity(candidate),
        "status": "breaking" if breaking else "advisory" if findings else "compatible",
        "breaking_count": breaking,
        "advisory_count": len(findings) - breaking,
        "findings": findings,
        "scope": [
            "operation-removals",
            "required-wire-inputs",
            "explicit-success-response-removals",
        ],
        "limitations": [
            "No application execution or external reference fetching",
            "Schema narrowing is advisory; this is not a complete compatibility proof",
        ],
    }


def compare_openapi(baseline, candidate, *, source_root="."):
    try:
        return compare_exports(
            load_openapi_document(baseline, source_root=source_root),
            load_openapi_document(candidate, source_root=source_root),
        )
    except (TypeError, KeyError, RecursionError) as exc:
        raise ApiContractError(
            f"Malformed or excessively nested exported contract: {exc}"
        ) from exc


def render_markdown(report):
    lines = [
        "# OpenAPI compatibility",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Baseline: `{report['baseline']['document_id']}`",
        f"Candidate: `{report['candidate']['document_id']}`",
        "",
    ]
    for item in report["findings"]:
        value = html.escape(f"{item['operation']}: {item['detail']}").replace("\n", " ")
        lines.append(f"- **{item['severity']}** — {value}")
    return "\n".join(lines) + "\n"
