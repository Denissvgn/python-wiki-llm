"""Static FastAPI and exported OpenAPI contract assembly.

The service consumes syntax-only inventory.  It never imports a target
application and never resolves remote OpenAPI references.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml  # pyright: ignore[reportMissingModuleSource]

from .imports import build_module_path_resolver
from .paths import is_test_source_path


_HTTP_METHODS = (
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "trace",
)
_SCALAR_TYPES = {
    "Any",
    "bool",
    "bytes",
    "date",
    "datetime",
    "Decimal",
    "float",
    "int",
    "str",
    "time",
    "UUID",
}
_INJECTED_TYPES = {"BackgroundTasks", "Request", "Response", "WebSocket"}
_RESPONSE_MEDIA_TYPES = {
    "FileResponse": "application/octet-stream",
    "HTMLResponse": "text/html",
    "JSONResponse": "application/json",
    "ORJSONResponse": "application/json",
    "PlainTextResponse": "text/plain",
    "RedirectResponse": "text/plain",
    "StreamingResponse": "application/octet-stream",
    "UJSONResponse": "application/json",
}
_OPENAPI_INPUT_LIMIT = 16 * 1024 * 1024
_STATUS_REF_RE = re.compile(r"(?:^|\.)HTTP_(\d{3})(?:_|$)")
_PATH_PARAMETER_RE = re.compile(r"\{([^}:]+)(?::[^}]+)?\}")
_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_NONE_ANNOTATION_RE = re.compile(r"(?:^|\W)None(?:$|\W)")
_UNKNOWN = object()


class ApiContractError(ValueError):
    """Raised when an API-contract input cannot be consumed safely."""


def _diagnostic(
    code: str,
    message: str,
    *,
    severity: str = "warning",
    **context: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
    }
    result.update({key: value for key, value in context.items() if value is not None})
    return result


def _record_value(record: Any, *, allow_references: bool = False) -> Any:
    if not isinstance(record, Mapping):
        return record
    kind = record.get("kind")
    if kind == "literal":
        return record.get("value")
    if kind == "reference":
        return record.get("value") if allow_references else _UNKNOWN
    if kind == "expression":
        return record.get("value") if allow_references else _UNKNOWN
    if kind == "ellipsis":
        return Ellipsis
    if kind == "sequence":
        sequence = [
            _record_value(item, allow_references=allow_references)
            for item in record.get("items", [])
        ]
        return _UNKNOWN if any(item is _UNKNOWN for item in sequence) else sequence
    if kind == "mapping":
        result: dict[Any, Any] = {}
        for item in record.get("items", []):
            if not isinstance(item, Mapping):
                continue
            key = _record_value(
                item.get("key"), allow_references=allow_references
            )
            value = _record_value(
                item.get("value"), allow_references=allow_references
            )
            if key is _UNKNOWN or value is _UNKNOWN:
                return _UNKNOWN
            if isinstance(key, (str, int, float, bool)) or key is None:
                result[key] = value
        return result
    if kind == "call":
        return _UNKNOWN
    return _UNKNOWN


def _display_call(record: Mapping[str, Any]) -> str:
    call = str(record.get("call") or "unknown")
    args = [_display_value(item) for item in record.get("args", [])]
    kwargs = [
        f"{name}={_display_value(value)}"
        for name, value in (record.get("kwargs") or {}).items()
    ]
    return f"{call}({', '.join((*args, *kwargs))})"


def _display_value(value: Any) -> str:
    if value is _UNKNOWN:
        return "unknown"
    if value is Ellipsis:
        return "..."
    if isinstance(value, Mapping):
        kind = value.get("kind")
        if kind == "literal":
            return repr(value.get("value"))
        if kind == "reference":
            return str(value.get("value") or "unknown")
        if kind == "expression":
            return str(value.get("value") or "unknown")
        if kind == "ellipsis":
            return "..."
        if kind == "call":
            return _display_call(value)
        if kind == "sequence":
            return "[" + ", ".join(_display_value(v) for v in value.get("items", [])) + "]"
        if kind == "mapping":
            return "{...}"
        return "unknown"
    return repr(value) if isinstance(value, str) else str(value)


def _kwargs(record: Mapping[str, Any]) -> Mapping[str, Any]:
    value = record.get("kwargs")
    return value if isinstance(value, Mapping) else {}


def _kw_value(
    record: Mapping[str, Any],
    name: str,
    default: Any = None,
    *,
    allow_references: bool = False,
) -> Any:
    raw = _kwargs(record).get(name)
    if raw is None:
        return default
    value = _record_value(raw, allow_references=allow_references)
    return default if value is _UNKNOWN else value


def _first_arg(record: Mapping[str, Any], *, allow_references: bool = False) -> Any:
    args = record.get("args")
    if not isinstance(args, list) or not args:
        return None
    value = _record_value(args[0], allow_references=allow_references)
    return None if value is _UNKNOWN else value


def _kw_unknown(
    record: Mapping[str, Any], name: str, *, allow_references: bool = False
) -> bool:
    raw = _kwargs(record).get(name)
    return raw is not None and _record_value(
        raw, allow_references=allow_references
    ) is _UNKNOWN


def _join_paths(*parts: Any) -> str | None:
    if any(part is None for part in parts):
        return None
    cleaned = [str(part).strip("/") for part in parts if str(part) not in {"", "/"}]
    suffix = "/".join(cleaned)
    result = f"/{suffix}" if suffix else "/"
    if parts and str(parts[-1]).endswith("/") and result != "/":
        result += "/"
    return result


def _node_key(filepath: str, scope: str, binding: str) -> tuple[str, str, str]:
    return filepath, scope, binding


def _framework_records(inventory: Mapping[str, Mapping[str, Any]]):
    for filepath, file_data in inventory.items():
        frameworks = file_data.get("frameworks")
        fastapi = frameworks.get("fastapi") if isinstance(frameworks, Mapping) else None
        if isinstance(fastapi, Mapping):
            yield filepath, file_data, fastapi


def _declaration_nodes(inventory: Mapping[str, Mapping[str, Any]]):
    nodes: dict[tuple[str, str, str], dict[str, Any]] = {}
    applications: list[tuple[str, str, str]] = []
    for filepath, _file_data, fastapi in _framework_records(inventory):
        for kind, plural in (("application", "applications"), ("router", "routers")):
            for record in fastapi.get(plural, []):
                if not isinstance(record, Mapping):
                    continue
                binding = str(record.get("binding") or "")
                scope = str(record.get("scope") or "<module>")
                if not binding:
                    continue
                key = _node_key(filepath, scope, binding)
                nodes[key] = {"kind": kind, "file": filepath, **dict(record)}
                if kind == "application":
                    applications.append(key)
    for filepath, _file_data, fastapi in _framework_records(inventory):
        for record in fastapi.get("aliases", []):
            if not isinstance(record, Mapping):
                continue
            binding = str(record.get("binding") or "")
            target = str(record.get("target") or "")
            scope = str(record.get("scope") or "<module>")
            if not binding or not target:
                continue
            target_key = None
            for candidate_scope in _candidate_scopes(scope):
                candidate = _node_key(filepath, candidate_scope, target)
                if candidate in nodes:
                    target_key = _canonical_node_key(candidate, nodes)
                    break
            if target_key is None:
                continue
            nodes[_node_key(filepath, scope, binding)] = {
                "kind": "alias",
                "canonical_key": target_key,
                **dict(record),
            }
    return nodes, sorted(applications)


def _canonical_node_key(
    key: tuple[str, str, str],
    nodes: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> tuple[str, str, str]:
    node = nodes.get(key, {})
    canonical = node.get("canonical_key")
    if isinstance(canonical, tuple) and len(canonical) == 3:
        return canonical
    return key


def _import_bindings(file_data: Mapping[str, Any]) -> dict[str, tuple[str, str | None]]:
    result: dict[str, tuple[str, str | None]] = {}
    for record in file_data.get("imports", []):
        if not isinstance(record, Mapping):
            continue
        import_type = record.get("type")
        module = str(record.get("module") or "")
        name = str(record.get("name") or "")
        if import_type == "from" and name:
            result[str(record.get("alias") or name)] = (module, name)
        elif import_type == "import" and module:
            recorded_name = str(record.get("name") or "")
            binding = (
                recorded_name
                if recorded_name and recorded_name != module
                else module.split(".", 1)[0]
            )
            result[binding] = (module, None)
    return result


def _canonical_imported_reference(value: Any, file_data: Mapping[str, Any]) -> Any:
    if not isinstance(value, str):
        return value
    normalized = value
    for binding, (_module, imported_name) in _import_bindings(file_data).items():
        if imported_name:
            normalized = re.sub(
                rf"\b{re.escape(binding)}\b", imported_name, normalized
            )
    if normalized != value:
        return normalized
    root, dot, rest = value.partition(".")
    imported = _import_bindings(file_data).get(root)
    if imported is None:
        return value
    _module, imported_name = imported
    if imported_name:
        return f"{imported_name}.{rest}" if dot else imported_name
    return rest or value


def _candidate_scopes(scope: str) -> list[str]:
    if scope == "<module>":
        return [scope]
    parts = scope.split(".")
    return [".".join(parts[:index]) for index in range(len(parts), 0, -1)] + ["<module>"]


def _resolve_binding(
    ref: str,
    *,
    filepath: str,
    scope: str,
    nodes: Mapping[tuple[str, str, str], Mapping[str, Any]],
    inventory: Mapping[str, Mapping[str, Any]],
    resolver: Any,
) -> tuple[str, str, str] | None:
    if not ref:
        return None
    root, dot, rest = ref.partition(".")
    local_binding = root if not dot else ref
    for candidate_scope in _candidate_scopes(scope):
        key = _node_key(filepath, candidate_scope, local_binding)
        if key in nodes:
            return _canonical_node_key(key, nodes)

    file_data = inventory.get(filepath, {})
    imported = _import_bindings(file_data).get(root)
    if imported is None:
        return None
    module, imported_name = imported
    candidates: list[tuple[str, str]] = []
    if imported_name is None:
        target_binding = rest
        module_leaf = module.rsplit(".", 1)[-1]
        if target_binding.startswith(module_leaf + "."):
            target_binding = target_binding[len(module_leaf) + 1 :]
        if target_binding:
            candidates.append((module, target_binding))
    else:
        candidates.append(
            (module, f"{imported_name}.{rest}" if rest else imported_name)
        )
        if rest:
            separator = "" if module.endswith(".") else "."
            candidates.append((f"{module}{separator}{imported_name}", rest))

    resolved: set[tuple[str, str, str]] = set()
    for target_module, target_binding in candidates:
        matches = resolver.candidates(target_module, filepath)
        for target_file in matches:
            key = _node_key(target_file, "<module>", target_binding)
            if key in nodes:
                resolved.add(_canonical_node_key(key, nodes))
    if len(resolved) == 1:
        return next(iter(resolved))
    return None


def _router_prefix(record: Mapping[str, Any]) -> str | None:
    if _kw_unknown(record, "prefix"):
        return None
    value = _kw_value(record, "prefix", "")
    return value if isinstance(value, str) else None


def _tags(record: Mapping[str, Any]) -> tuple[list[str], bool]:
    if _kw_unknown(record, "tags"):
        return [], False
    value = _kw_value(record, "tags", [])
    if value in (None, []):
        return [], True
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value), True
    return [], False


def _operation_methods(record: Mapping[str, Any]) -> tuple[list[str], bool]:
    decorator = str(record.get("decorator") or "")
    if decorator in _HTTP_METHODS:
        return [decorator.upper()], True
    value = _kw_value(record, "methods")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return [item.upper() for item in value], True
    return [], False


def _status_code(value: Any) -> int | str | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        match = _STATUS_REF_RE.search(value)
        if match:
            return int(match.group(1))
        if value.isdigit():
            return int(value)
        return value
    return None


def _leaf_type(annotation: str) -> str:
    value = annotation.strip()
    value = re.sub(r"\s*\|\s*None\b", "", value)
    value = re.sub(r"^Optional\[(.*)\]$", r"\1", value)
    return value.rsplit(".", 1)[-1]


def _parameter_default(
    marker: Mapping[str, Any] | None,
) -> tuple[bool, bool, Any, bool]:
    """Return required, has-default, value, and unresolved-default state."""
    if marker is None:
        return True, False, None, False
    args = marker.get("args")
    default_record = (
        args[0]
        if isinstance(args, list) and args
        else _kwargs(marker).get("default")
    )
    if default_record is None:
        if "default_factory" in _kwargs(marker):
            return False, False, None, False
        return True, False, None, False
    value = _record_value(default_record)
    if value is Ellipsis:
        return True, False, None, False
    if value is _UNKNOWN:
        return False, False, None, True
    return False, True, value, False


def _normalize_parameters(
    record: Mapping[str, Any], route_path: str | None
) -> tuple[list[dict[str, Any]], dict[str, Any] | None, list[dict[str, Any]]]:
    parameters: list[dict[str, Any]] = []
    body_parameters: list[dict[str, Any]] = []
    unknowns: list[dict[str, Any]] = []
    path_names = set(_PATH_PARAMETER_RE.findall(route_path or ""))
    for raw in record.get("parameters", []):
        if not isinstance(raw, Mapping):
            continue
        python_name = str(raw.get("name") or "")
        annotation = str(raw.get("annotation") or "")
        marker = raw.get("marker") if isinstance(raw.get("marker"), Mapping) else None
        marker_name = str(marker.get("marker") or "") if marker else ""
        if marker_name in {"depends", "security"}:
            unknowns.append(
                {
                    "field": f"parameter:{python_name}",
                    "reason": "dependency_parameters_not_expanded",
                }
            )
            continue
        if _leaf_type(annotation) in _INJECTED_TYPES:
            continue
        if marker_name:
            location = marker_name
        elif python_name in path_names:
            location = "path"
        elif _leaf_type(annotation).split("[", 1)[0] in _SCALAR_TYPES:
            location = "query"
        else:
            location = "body"
            if annotation:
                unknowns.append(
                    {
                        "field": f"parameter:{python_name}.location",
                        "reason": "inferred_body_from_non_scalar_annotation",
                    }
                )
        required, has_default, default, default_unknown = _parameter_default(marker)
        raw_default = raw.get("default")
        marker_from_default = bool(marker and marker.get("source") == "default")
        if raw_default is not None and not marker_from_default:
            raw_value = _record_value(raw_default)
            if raw_value is Ellipsis:
                required = True
                has_default = False
                default = None
            elif raw_value is _UNKNOWN:
                required = False
                has_default = False
                default_unknown = True
            else:
                default = raw_value
                required = False
                has_default = True
        if location == "path":
            required = True
        alias = _kw_value(marker or {}, "alias") if marker else None
        if marker and _kw_unknown(marker, "alias"):
            unknowns.append(
                {
                    "field": f"parameter:{python_name}.alias",
                    "reason": "not_statically_resolvable",
                }
            )
        wire_name = alias if isinstance(alias, str) else python_name
        if location == "header" and not isinstance(alias, str):
            convert = _kw_value(marker or {}, "convert_underscores", True)
            if convert is not False:
                wire_name = python_name.replace("_", "-")
        parameter: dict[str, Any] = {
            "python_name": python_name,
            "wire_name": wire_name,
            "location": location,
            "type": annotation or "unknown",
            "required": required,
            "nullable": bool(
                _NONE_ANNOTATION_RE.search(annotation)
                or annotation.startswith("Optional[")
            ),
        }
        if has_default:
            parameter["default"] = default
        if default_unknown:
            unknowns.append(
                {
                    "field": f"parameter:{python_name}.default",
                    "reason": "not_statically_resolvable",
                }
            )
        description = _kw_value(marker or {}, "description") if marker else None
        if isinstance(description, str):
            parameter["description"] = description
        elif marker and _kw_unknown(marker, "description"):
            unknowns.append(
                {
                    "field": f"parameter:{python_name}.description",
                    "reason": "not_statically_resolvable",
                }
            )
        parameters.append(parameter)
        if location in {"body", "form", "file"}:
            body_parameters.append(parameter)

    request_body = None
    if body_parameters:
        locations = {item["location"] for item in body_parameters}
        if "file" in locations:
            media_type = "multipart/form-data"
        elif locations <= {"form"}:
            media_type = "application/x-www-form-urlencoded"
        else:
            media_type = "application/json"
        models = [
            item["type"]
            for item in body_parameters
            if _leaf_type(str(item["type"])).split("[", 1)[0] not in _SCALAR_TYPES
        ]
        request_body = {
            "content_types": [media_type],
            "models": list(dict.fromkeys(models)),
            "required": any(item["required"] for item in body_parameters),
        }
    return parameters, request_body, unknowns


def _response_media_type(response_class: Any) -> str:
    if response_class is _UNKNOWN:
        return "unknown"
    if isinstance(response_class, str):
        return _RESPONSE_MEDIA_TYPES.get(response_class.rsplit(".", 1)[-1], "unknown")
    return "application/json"


def _additional_responses(
    record: Mapping[str, Any],
    file_data: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    raw_record = _kwargs(record).get("responses")
    if raw_record is None:
        return [], True
    raw = _record_value(raw_record, allow_references=True)
    if raw is _UNKNOWN:
        return [], False
    if not isinstance(raw, Mapping):
        return [], False
    responses = []
    for status, details in raw.items():
        detail_map = details if isinstance(details, Mapping) else {}
        model = detail_map.get("model")
        content = detail_map.get("content")
        content_types = sorted(str(key) for key in content) if isinstance(content, Mapping) else []
        response: dict[str, Any] = {
            "status_code": _status_code(status) or str(status),
            "description": str(detail_map.get("description") or ""),
            "content_types": content_types,
        }
        if model is not None:
            response["model"] = str(
                _canonical_imported_reference(model, file_data or {})
            )
        responses.append(response)
    return responses, True


def _merge_responses(
    *groups: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for group in groups:
        for raw in group:
            response = dict(raw)
            key = str(response.get("status_code"))
            if key not in merged:
                order.append(key)
                merged[key] = response
                continue
            current = merged[key]
            for field in ("description", "model"):
                if response.get(field) not in (None, ""):
                    current[field] = response[field]
            content_types = list(
                dict.fromkeys(
                    [
                        *current.get("content_types", []),
                        *response.get("content_types", []),
                    ]
                )
            )
            current["content_types"] = content_types
    return [merged[key] for key in order]


def _operation_responses(
    record: Mapping[str, Any],
    inherited_response_class: Any,
    inherited_responses: Sequence[Mapping[str, Any]],
    file_data: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    unknowns: list[dict[str, Any]] = []
    status_record = _kwargs(record).get("status_code")
    if status_record is None:
        status: int | str = 200
    else:
        status_value = _record_value(status_record, allow_references=True)
        parsed_status = (
            _status_code(status_value) if status_value is not _UNKNOWN else None
        )
        if not isinstance(parsed_status, int) or isinstance(parsed_status, bool):
            status = "unknown"
            unknowns.append(
                {"field": "responses.primary.status_code", "reason": "not_statically_resolvable"}
            )
        else:
            status = parsed_status

    response_model_record = _kwargs(record).get("response_model")
    if response_model_record is None:
        return_annotation = str(record.get("return_annotation") or "")
        response_model = return_annotation or None
    else:
        response_model = _record_value(response_model_record, allow_references=True)
        if response_model is _UNKNOWN:
            response_model = None
            unknowns.append(
                {"field": "responses.primary.model", "reason": "not_statically_resolvable"}
            )
    response_model = _canonical_imported_reference(response_model, file_data)

    response_class_record = _kwargs(record).get("response_class")
    if response_class_record is None:
        response_class = inherited_response_class
    else:
        response_class = _record_value(
            response_class_record, allow_references=True
        )
        if response_class is _UNKNOWN:
            unknowns.append(
                {
                    "field": "responses.primary.content_types",
                    "reason": "response_class_not_statically_resolvable",
                }
            )
    response_class = _canonical_imported_reference(response_class, file_data)
    response_description = _kw_value(record, "response_description")
    if _kw_unknown(record, "response_description"):
        response_description = ""
        unknowns.append(
            {
                "field": "responses.primary.description",
                "reason": "not_statically_resolvable",
            }
        )
    elif response_description is None:
        response_description = ""
    elif not isinstance(response_description, str):
        response_description = ""
        unknowns.append(
            {
                "field": "responses.primary.description",
                "reason": "not_statically_resolvable",
            }
        )
    primary: dict[str, Any] = {
        "status_code": status,
        "description": response_description,
        "content_types": [_response_media_type(response_class)],
    }
    if response_model is not None:
        primary["model"] = str(response_model)
    additional, additional_known = _additional_responses(record, file_data)
    if not additional_known:
        unknowns.append(
            {"field": "responses.additional", "reason": "not_statically_resolvable"}
        )
    return _merge_responses([primary], inherited_responses, additional), unknowns


def _operation_id(method: str, path: str, index: int) -> str:
    base = _SAFE_ID_RE.sub("-", f"{method.lower()}-{path.strip('/')}").strip("-")
    return base or f"operation-{index}"


def build_static_api_contracts(inventory: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Assemble production FastAPI operations from syntax-only inventory."""
    nodes, app_keys = _declaration_nodes(inventory)
    resolver = build_module_path_resolver(dict(inventory))
    operations_by_owner: dict[tuple[str, str, str], list[tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    includes_by_owner: dict[tuple[str, str, str], list[tuple[tuple[str, str, str], Mapping[str, Any]]]] = defaultdict(list)
    diagnostics: list[dict[str, Any]] = []

    for filepath, file_data, fastapi in _framework_records(inventory):
        for record in fastapi.get("operations", []):
            if not isinstance(record, Mapping):
                continue
            owner = _resolve_binding(
                str(record.get("owner") or ""),
                filepath=filepath,
                scope=str(record.get("handler_scope") or "<module>"),
                nodes=nodes,
                inventory=inventory,
                resolver=resolver,
            )
            if owner is None:
                diagnostics.append(
                    _diagnostic(
                        "fastapi_owner_unresolved",
                        "Route decorator owner could not be resolved to FastAPI/APIRouter.",
                        file=filepath,
                        line=record.get("line"),
                    )
                )
                continue
            operations_by_owner[owner].append((filepath, record))

        for record in fastapi.get("includes", []):
            if not isinstance(record, Mapping):
                continue
            scope = str(record.get("scope") or "<module>")
            owner = _resolve_binding(
                str(record.get("owner") or ""),
                filepath=filepath,
                scope=scope,
                nodes=nodes,
                inventory=inventory,
                resolver=resolver,
            )
            router_ref = _first_arg(record, allow_references=True)
            if router_ref is None:
                router_ref = _kw_value(
                    record, "router", allow_references=True
                )
            target = _resolve_binding(
                router_ref if isinstance(router_ref, str) else "",
                filepath=filepath,
                scope=scope,
                nodes=nodes,
                inventory=inventory,
                resolver=resolver,
            )
            if owner is None or target is None:
                diagnostics.append(
                    _diagnostic(
                        "fastapi_include_unresolved",
                        "include_router owner or router target could not be resolved.",
                        file=filepath,
                        line=record.get("line"),
                    )
                )
                continue
            includes_by_owner[owner].append((target, record))

    applications = []
    for key in app_keys:
        node = nodes[key]
        config: dict[str, Any] = {}
        unknowns: list[dict[str, Any]] = []
        if node.get("conditional"):
            unknowns.append(
                {
                    "field": "declaration",
                    "reason": "conditional_declaration",
                }
            )
        for name, raw in _kwargs(node).items():
            value = _record_value(raw)
            if value is _UNKNOWN:
                unknowns.append(
                    {
                        "field": f"config.{name}",
                        "reason": "not_statically_resolvable",
                        "expression": _display_value(raw),
                    }
                )
            else:
                config[name] = value
        applications.append(
            {
                "file": key[0],
                "binding": key[2],
                "scope": key[1],
                "line": node.get("line"),
                "config": config,
                "unknowns": unknowns,
            }
        )

    assembled: list[dict[str, Any]] = []
    excluded = {"test_source": 0, "schema_excluded": 0, "conditional": 0}

    def walk(
        key: tuple[str, str, str],
        *,
        prefix: str,
        inherited_tags: Sequence[str],
        inherited_response_class: Any,
        inherited_responses: Sequence[Mapping[str, Any]],
        include_in_schema: bool,
        stack: tuple[tuple[str, str, str], ...],
    ) -> None:
        if key in stack:
            diagnostics.append(
                _diagnostic(
                    "fastapi_router_cycle",
                    "Router inclusion cycle detected; recursive branch was stopped.",
                    file=key[0],
                )
            )
            return
        node = nodes[key]
        if node.get("conditional"):
            excluded["conditional"] += 1
            diagnostics.append(
                _diagnostic(
                    "fastapi_conditional_declaration",
                    "Conditional FastAPI application/router was retained only as a raw declaration.",
                    file=key[0],
                    line=node.get("line"),
                )
            )
            return
        node_prefix = _router_prefix(node) if node.get("kind") == "router" else ""
        effective_prefix = _join_paths(prefix, node_prefix)
        if effective_prefix is None:
            diagnostics.append(
                _diagnostic(
                    "fastapi_prefix_unknown",
                    "Router prefix is not statically known.",
                    file=key[0],
                    line=node.get("line"),
                )
            )
            return
        node_tags, tags_known = _tags(node)
        if not tags_known:
            diagnostics.append(
                _diagnostic(
                    "fastapi_tags_unknown",
                    "Router tags are not statically known.",
                    file=key[0],
                    line=node.get("line"),
                )
            )
        effective_tags = list(dict.fromkeys((*inherited_tags, *node_tags)))
        node_file_data = inventory.get(key[0], {})
        response_class = _kw_value(
            node,
            "default_response_class",
            inherited_response_class,
            allow_references=True,
        )
        response_class = _canonical_imported_reference(
            response_class, node_file_data
        )
        if _kw_unknown(node, "default_response_class", allow_references=True):
            response_class = _UNKNOWN
            diagnostics.append(
                _diagnostic(
                    "fastapi_response_class_unknown",
                    "Router default response class is not statically known.",
                    file=key[0],
                    line=node.get("line"),
                )
            )
        node_responses, node_responses_known = _additional_responses(
            node, node_file_data
        )
        effective_responses = _merge_responses(inherited_responses, node_responses)
        if not node_responses_known:
            diagnostics.append(
                _diagnostic(
                    "fastapi_responses_unknown",
                    "Router responses are not statically known.",
                    file=key[0],
                    line=node.get("line"),
                )
            )
        node_schema = _kw_value(node, "include_in_schema", True)
        if _kw_unknown(node, "include_in_schema"):
            diagnostics.append(
                _diagnostic(
                    "fastapi_schema_visibility_unknown",
                    "Router schema visibility is not statically known; default visibility was retained.",
                    file=key[0],
                    line=node.get("line"),
                )
            )
        schema_visible = include_in_schema and node_schema is not False

        for filepath, raw in operations_by_owner.get(key, []):
            if raw.get("conditional"):
                excluded["conditional"] += 1
                diagnostics.append(
                    _diagnostic(
                        "fastapi_conditional_declaration",
                        "Conditional route was not asserted as a production operation.",
                        file=filepath,
                        line=raw.get("line"),
                    )
                )
                continue
            methods, methods_known = _operation_methods(raw)
            relative_path = _first_arg(raw)
            if relative_path is None:
                relative_path = _kw_value(raw, "path")
            path_known = isinstance(relative_path, str)
            if not path_known:
                relative_path = None
            full_path = _join_paths(effective_prefix, relative_path)
            unknowns: list[dict[str, Any]] = []
            if not methods_known:
                unknowns.append({"field": "method", "reason": "not_statically_resolvable"})
            if full_path is None or not path_known:
                unknowns.append({"field": "path", "reason": "not_statically_resolvable"})
            route_tags, route_tags_known = _tags(raw)
            if not route_tags_known:
                unknowns.append({"field": "tags", "reason": "not_statically_resolvable"})
            if _kw_unknown(raw, "include_in_schema"):
                unknowns.append(
                    {"field": "include_in_schema", "reason": "not_statically_resolvable"}
                )
            visible = schema_visible and _kw_value(raw, "include_in_schema", True) is not False
            if not visible:
                excluded["schema_excluded"] += max(1, len(methods))
                continue
            if is_test_source_path(filepath):
                excluded["test_source"] += max(1, len(methods))
                continue
            parameters, request_body, parameter_unknowns = _normalize_parameters(raw, full_path)
            unknowns.extend(parameter_unknowns)
            responses, response_unknowns = _operation_responses(
                raw,
                response_class,
                effective_responses,
                inventory.get(filepath, {}),
            )
            unknowns.extend(response_unknowns)
            summary = _kw_value(raw, "summary")
            if summary is not None and not isinstance(summary, str):
                summary = None
            if _kw_unknown(raw, "summary") or (
                "summary" in _kwargs(raw) and summary is None
            ):
                unknowns.append({"field": "summary", "reason": "not_statically_resolvable"})
            operation_id = _kw_value(raw, "operation_id")
            if operation_id is not None and not isinstance(operation_id, str):
                operation_id = None
            if _kw_unknown(raw, "operation_id") or (
                "operation_id" in _kwargs(raw) and operation_id is None
            ):
                unknowns.append(
                    {"field": "operation_id", "reason": "not_statically_resolvable"}
                )
            for method in methods or ["UNKNOWN"]:
                operation = {
                    "method": method,
                    "path": full_path,
                    "relative_path": relative_path,
                    "handler": {
                        "file": filepath,
                        "symbol": raw.get("handler"),
                        "qualname": raw.get("handler_qualname"),
                        "line": raw.get("line"),
                    },
                    "summary": summary,
                    "tags": list(dict.fromkeys((*effective_tags, *route_tags))),
                    "parameters": parameters,
                    "request_body": request_body,
                    "responses": responses,
                    "operation_id": operation_id,
                    "unknowns": unknowns,
                    "provenance": "static",
                }
                assembled.append(operation)

        for child, include in includes_by_owner.get(key, []):
            if include.get("conditional"):
                excluded["conditional"] += 1
                diagnostics.append(
                    _diagnostic(
                        "fastapi_conditional_declaration",
                        "Conditional include_router edge was not asserted in the production graph.",
                        file=key[0],
                        line=include.get("line"),
                    )
                )
                continue
            if _kw_unknown(include, "prefix"):
                diagnostics.append(
                    _diagnostic(
                        "fastapi_prefix_unknown",
                        "include_router prefix is not statically known.",
                        file=key[0],
                        line=include.get("line"),
                    )
                )
                continue
            include_prefix = _kw_value(include, "prefix", "")
            if not isinstance(include_prefix, str):
                diagnostics.append(
                    _diagnostic(
                        "fastapi_prefix_unknown",
                        "include_router prefix is not statically known.",
                        file=key[0],
                        line=include.get("line"),
                    )
                )
                continue
            include_tags, include_tags_known = _tags(include)
            if not include_tags_known:
                diagnostics.append(
                    _diagnostic(
                        "fastapi_tags_unknown",
                        "include_router tags are not statically known.",
                        file=key[0],
                        line=include.get("line"),
                    )
                )
            include_schema = _kw_value(include, "include_in_schema", True) is not False
            if _kw_unknown(include, "include_in_schema"):
                diagnostics.append(
                    _diagnostic(
                        "fastapi_schema_visibility_unknown",
                        "include_router schema visibility is not statically known; default visibility was retained.",
                        file=key[0],
                        line=include.get("line"),
                    )
                )
            include_response_class = _kw_value(
                include,
                "default_response_class",
                response_class,
                allow_references=True,
            )
            include_response_class = _canonical_imported_reference(
                include_response_class, node_file_data
            )
            if _kw_unknown(
                include, "default_response_class", allow_references=True
            ):
                include_response_class = _UNKNOWN
                diagnostics.append(
                    _diagnostic(
                        "fastapi_response_class_unknown",
                        "include_router default response class is not statically known.",
                        file=key[0],
                        line=include.get("line"),
                    )
                )
            include_responses, include_responses_known = _additional_responses(
                include, node_file_data
            )
            if not include_responses_known:
                diagnostics.append(
                    _diagnostic(
                        "fastapi_responses_unknown",
                        "include_router responses are not statically known.",
                        file=key[0],
                        line=include.get("line"),
                    )
                )
            walk(
                child,
                prefix=_join_paths(effective_prefix, include_prefix) or "/",
                inherited_tags=(*effective_tags, *include_tags),
                inherited_response_class=include_response_class,
                inherited_responses=_merge_responses(
                    effective_responses, include_responses
                ),
                include_in_schema=schema_visible and include_schema,
                stack=(*stack, key),
            )

    for app_key in app_keys:
        app_node = nodes[app_key]
        app_response_class = _kw_value(
            app_node, "default_response_class", allow_references=True
        )
        app_response_class = _canonical_imported_reference(
            app_response_class, inventory.get(app_key[0], {})
        )
        if _kw_unknown(
            app_node, "default_response_class", allow_references=True
        ):
            app_response_class = _UNKNOWN
            diagnostics.append(
                _diagnostic(
                    "fastapi_response_class_unknown",
                    "Application default response class is not statically known.",
                    file=app_key[0],
                    line=app_node.get("line"),
                )
            )
        walk(
            app_key,
            prefix="",
            inherited_tags=(),
            inherited_response_class=app_response_class,
            inherited_responses=(),
            include_in_schema=True,
            stack=(),
        )

    assembled.sort(
        key=lambda item: (
            str(item.get("path") or ""),
            str(item.get("method") or ""),
            str((item.get("handler") or {}).get("file") or ""),
            int((item.get("handler") or {}).get("line") or 0),
        )
    )
    ids: defaultdict[str, int] = defaultdict(int)
    for index, operation in enumerate(assembled, start=1):
        base = _operation_id(str(operation["method"]), str(operation.get("path") or "unknown"), index)
        ids[base] += 1
        operation["id"] = base if ids[base] == 1 else f"{base}-{ids[base]}"

    return {
        "source": "static",
        "applications": applications,
        "operations": assembled,
        "diagnostics": sorted(
            diagnostics,
            key=lambda item: (str(item.get("file") or ""), int(item.get("line") or 0), item["code"]),
        ),
        "excluded_counts": excluded,
    }


def _resolve_openapi_path(path: str | Path, source_root: str | Path) -> tuple[Path, str]:
    root = Path(source_root).resolve()
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ApiContractError(
            f"--openapi-file '{path}' resolves outside source root '{root}'."
        ) from exc
    if not resolved.is_file():
        raise ApiContractError(f"OpenAPI file not found: {relative}")
    return resolved, relative


def load_openapi_document(
    path: str | Path, *, source_root: str | Path = "."
) -> dict[str, Any]:
    """Load and validate a source-contained OpenAPI JSON/YAML document."""
    resolved, relative = _resolve_openapi_path(path, source_root)
    suffix = resolved.suffix.lower()
    try:
        data = resolved.read_bytes()
    except OSError as exc:
        raise ApiContractError(f"Unable to read OpenAPI file '{relative}': {exc}") from exc
    if len(data) > _OPENAPI_INPUT_LIMIT:
        raise ApiContractError("OpenAPI input exceeds the 16 MiB safety limit.")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ApiContractError("OpenAPI input must be UTF-8 encoded.") from exc
    try:
        if suffix == ".json":
            document = json.loads(text)
            format_name = "json"
        elif suffix in {".yaml", ".yml"}:
            document = yaml.safe_load(text)
            format_name = "yaml"
        else:
            try:
                document = json.loads(text)
                format_name = "json"
            except json.JSONDecodeError:
                document = yaml.safe_load(text)
                format_name = "yaml"
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ApiContractError(f"Invalid OpenAPI document: {exc}") from exc
    if not isinstance(document, Mapping):
        raise ApiContractError("OpenAPI document root must be an object.")
    version = str(document.get("openapi") or "")
    if not (version.startswith("3.0.") or version.startswith("3.1.")):
        raise ApiContractError("OpenAPI version must be 3.0.x or 3.1.x.")
    if not isinstance(document.get("paths"), Mapping):
        raise ApiContractError("OpenAPI document must contain an object-valued paths field.")
    return {
        "document": dict(document),
        "version": version,
        "path": relative,
        "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
        "format": format_name,
    }


def _json_pointer(document: Mapping[str, Any], ref: str) -> Any:
    if not ref.startswith("#/"):
        return None
    value: Any = document
    for part in ref[2:].split("/"):
        token = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, Mapping) or token not in value:
            return None
        value = value[token]
    return value


def _dereference(
    value: Any,
    document: Mapping[str, Any],
    diagnostics: list[dict[str, Any]],
    *,
    context: str,
) -> Any:
    current = value
    seen: set[str] = set()
    while isinstance(current, Mapping) and "$ref" in current:
        ref = str(current.get("$ref") or "")
        if not ref.startswith("#/"):
            diagnostic = _diagnostic(
                "openapi_external_ref",
                f"External OpenAPI reference was not fetched: {ref}",
                context=context,
            )
            if diagnostic not in diagnostics:
                diagnostics.append(diagnostic)
            return None
        if ref in seen:
            diagnostic = _diagnostic(
                "openapi_ref_cycle",
                f"Local OpenAPI reference cycle detected at: {ref}",
                context=context,
            )
            if diagnostic not in diagnostics:
                diagnostics.append(diagnostic)
            return None
        seen.add(ref)
        current = _json_pointer(document, ref)
        if current is None:
            diagnostic = _diagnostic(
                "openapi_ref_unresolved",
                f"Local OpenAPI reference could not be resolved: {ref}",
                context=context,
            )
            if diagnostic not in diagnostics:
                diagnostics.append(diagnostic)
            return None
    return current


def _schema_name(
    schema: Any,
    document: Mapping[str, Any],
    diagnostics: list[dict[str, Any]],
    *,
    context: str,
) -> str | None:
    if not isinstance(schema, Mapping):
        return None
    ref = schema.get("$ref")
    if isinstance(ref, str):
        if _dereference(schema, document, diagnostics, context=context) is None:
            return None
        return ref.rsplit("/", 1)[-1]
    schema_type = schema.get("type")
    if isinstance(schema_type, str):
        if schema_type == "array":
            item_name = _schema_name(
                schema.get("items"),
                document,
                diagnostics,
                context=f"{context}.items",
            )
            return f"array[{item_name or 'unknown'}]"
        return schema_type
    if isinstance(schema_type, list):
        names = [str(item) for item in schema_type if item != "null"]
        return " | ".join(names) or "null"
    for keyword in ("oneOf", "anyOf", "allOf"):
        variants = schema.get(keyword)
        if not isinstance(variants, list):
            continue
        names = []
        for index, variant in enumerate(variants):
            name = _schema_name(
                variant,
                document,
                diagnostics,
                context=f"{context}.{keyword}[{index}]",
            )
            if name and name != "null":
                names.append(name)
        if names:
            return " & ".join(names) if keyword == "allOf" else " | ".join(names)
    return None


def _schema_nullable(schema: Any) -> bool:
    if not isinstance(schema, Mapping):
        return False
    if schema.get("nullable") is True:
        return True
    schema_type = schema.get("type")
    if isinstance(schema_type, list) and "null" in schema_type:
        return True
    for keyword in ("oneOf", "anyOf"):
        variants = schema.get(keyword)
        if isinstance(variants, list) and any(
            isinstance(item, Mapping) and item.get("type") == "null"
            for item in variants
        ):
            return True
    return False


def _openapi_parameter(
    raw: Any,
    document: Mapping[str, Any],
    diagnostics: list[dict[str, Any]],
    context: str,
) -> dict[str, Any] | None:
    value = _dereference(raw, document, diagnostics, context=context)
    if not isinstance(value, Mapping):
        return None
    location = str(value.get("in") or "unknown")
    name = str(value.get("name") or "unknown")
    raw_schema = value.get("schema")
    content_types: list[str] = []
    if raw_schema is None:
        content = value.get("content")
        if isinstance(content, Mapping) and len(content) == 1:
            media_type, media = next(iter(content.items()))
            content_types = [str(media_type)]
            if isinstance(media, Mapping):
                raw_schema = media.get("schema")
        elif content is not None:
            diagnostics.append(
                _diagnostic(
                    "openapi_parameter_content_unknown",
                    "Parameter content must contain exactly one media type to reconstruct its schema.",
                    context=context,
                )
            )
    resolved_schema = _dereference(
        raw_schema,
        document,
        diagnostics,
        context=f"{context}.parameter:{name}",
    )
    result: dict[str, Any] = {
        "wire_name": name,
        "location": location,
        "type": _schema_name(
            raw_schema, document, diagnostics, context=f"{context}.parameter:{name}"
        )
        or "unknown",
        "required": True if location == "path" else bool(value.get("required", False)),
        "nullable": _schema_nullable(resolved_schema),
    }
    if content_types:
        result["content_types"] = content_types
    if isinstance(resolved_schema, Mapping) and "default" in resolved_schema:
        result["default"] = resolved_schema["default"]
    if isinstance(value.get("description"), str):
        result["description"] = value["description"]
    return result


def _openapi_request_body(
    raw: Any,
    document: Mapping[str, Any],
    diagnostics: list[dict[str, Any]],
    context: str,
) -> dict[str, Any] | None:
    value = _dereference(raw, document, diagnostics, context=context)
    if not isinstance(value, Mapping):
        return None
    content = value.get("content")
    if not isinstance(content, Mapping):
        return {"content_types": [], "models": [], "required": bool(value.get("required", False))}
    models = []
    for media in content.values():
        if not isinstance(media, Mapping):
            continue
        schema = media.get("schema")
        name = _schema_name(
            schema,
            document,
            diagnostics,
            context=f"{context}.requestBody",
        )
        if name:
            models.append(name)
    return {
        "content_types": sorted(str(item) for item in content),
        "models": list(dict.fromkeys(models)),
        "required": bool(value.get("required", False)),
    }


def _openapi_responses(
    raw: Any,
    document: Mapping[str, Any],
    diagnostics: list[dict[str, Any]],
    context: str,
) -> list[dict[str, Any]]:
    if not isinstance(raw, Mapping):
        diagnostics.append(
            _diagnostic("openapi_responses_missing", "Operation has no responses object.", context=context)
        )
        return []
    responses = []
    for status, response in raw.items():
        value = _dereference(response, document, diagnostics, context=context)
        if not isinstance(value, Mapping):
            continue
        content = value.get("content")
        models = []
        if isinstance(content, Mapping):
            for media in content.values():
                if isinstance(media, Mapping):
                    name = _schema_name(
                        media.get("schema"),
                        document,
                        diagnostics,
                        context=f"{context}.response:{status}",
                    )
                    if name:
                        models.append(name)
        item: dict[str, Any] = {
            "status_code": _status_code(status) or str(status),
            "description": str(value.get("description") or ""),
            "content_types": sorted(str(key) for key in content) if isinstance(content, Mapping) else [],
        }
        if models:
            item["model"] = models[0] if len(models) == 1 else models
        responses.append(item)
    return responses


def _openapi_operations(loaded: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    document = loaded["document"]
    diagnostics: list[dict[str, Any]] = []
    operations = []
    for path, path_item in sorted(document.get("paths", {}).items()):
        path_value = _dereference(path_item, document, diagnostics, context=str(path))
        if not isinstance(path_value, Mapping):
            continue
        path_parameters = path_value.get("parameters", [])
        for method in _HTTP_METHODS:
            raw = path_value.get(method)
            if not isinstance(raw, Mapping):
                continue
            context = f"{method.upper()} {path}"
            parameter_map: dict[tuple[str, str], dict[str, Any]] = {}
            for source in (path_parameters, raw.get("parameters", [])):
                if not isinstance(source, list):
                    continue
                for parameter in source:
                    normalized = _openapi_parameter(parameter, document, diagnostics, context)
                    if normalized is not None:
                        parameter_map[(normalized["wire_name"], normalized["location"])] = normalized
            operations.append(
                {
                    "id": str(raw.get("operationId") or _operation_id(method, str(path), len(operations) + 1)),
                    "method": method.upper(),
                    "path": str(path),
                    "relative_path": str(path),
                    "handler": None,
                    "summary": raw.get("summary"),
                    "tags": list(raw.get("tags") or []),
                    "parameters": list(parameter_map.values()),
                    "request_body": _openapi_request_body(raw.get("requestBody"), document, diagnostics, context),
                    "responses": _openapi_responses(raw.get("responses"), document, diagnostics, context),
                    "operation_id": raw.get("operationId"),
                    "unknowns": [],
                    "provenance": "openapi",
                }
            )
    return operations, diagnostics


def _parameter_contract(operation: Mapping[str, Any]) -> set[tuple[Any, ...]]:
    return {
        (
            str(item.get("wire_name")),
            str(item.get("location")),
            _canonical_schema_token(item.get("type")),
            bool(item.get("required")),
            bool(item.get("nullable")),
        )
        for item in operation.get("parameters", [])
        if isinstance(item, Mapping)
    }


def _response_keys(operation: Mapping[str, Any]) -> set[str]:
    return {
        str(item.get("status_code"))
        for item in operation.get("responses", [])
        if isinstance(item, Mapping)
    }


def _canonical_schema_token(value: Any) -> str:
    token = str(value or "").replace(" ", "")
    replacements = {
        "boolean": "bool",
        "integer": "int",
        "number": "float",
        "string": "str",
    }
    return replacements.get(token, token)


def _schema_contract(operation: Mapping[str, Any]) -> tuple[Any, ...]:
    request = operation.get("request_body")
    request_models = ()
    if isinstance(request, Mapping):
        request_models = tuple(
            sorted(_canonical_schema_token(item) for item in request.get("models", []))
        )
    responses = []
    for item in operation.get("responses", []):
        if not isinstance(item, Mapping):
            continue
        model = item.get("model")
        models = model if isinstance(model, list) else [model] if model else []
        responses.append(
            (
                str(item.get("status_code")),
                tuple(sorted(_canonical_schema_token(value) for value in models)),
            )
        )
    return request_models, tuple(sorted(responses))


def _content_type_contract(operation: Mapping[str, Any]) -> tuple[Any, ...]:
    request = operation.get("request_body")
    request_types = ()
    if isinstance(request, Mapping):
        request_types = tuple(sorted(str(item) for item in request.get("content_types", [])))
    response_types = tuple(
        sorted(
            (
                str(item.get("status_code")),
                tuple(sorted(str(value) for value in item.get("content_types", []))),
            )
            for item in operation.get("responses", [])
            if isinstance(item, Mapping)
        )
    )
    return request_types, response_types


def _attach_static_parameter_names(
    openapi_operation: dict[str, Any], static_operation: Mapping[str, Any]
) -> None:
    names = {
        (str(item.get("wire_name")), str(item.get("location"))): item.get(
            "python_name"
        )
        for item in static_operation.get("parameters", [])
        if isinstance(item, Mapping) and item.get("python_name")
    }
    for parameter in openapi_operation.get("parameters", []):
        if not isinstance(parameter, dict):
            continue
        python_name = names.get(
            (str(parameter.get("wire_name")), str(parameter.get("location")))
        )
        if python_name:
            parameter["python_name"] = python_name


def _reconcile_openapi(
    static: Mapping[str, Any], loaded: Mapping[str, Any]
) -> dict[str, Any]:
    operations, diagnostics = _openapi_operations(loaded)
    static_operations = list(static.get("operations", []))
    by_route: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    by_operation_id: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for operation in static_operations:
        by_route[(str(operation.get("method")), str(operation.get("path")))].append(operation)
        operation_id = operation.get("operation_id")
        if operation_id:
            by_operation_id[str(operation_id)].append(operation)
    matched_static: set[str] = set()
    for operation in operations:
        candidates = by_route.get((operation["method"], operation["path"]), [])
        match = candidates[0] if len(candidates) == 1 else None
        if match is None and operation.get("operation_id"):
            id_candidates = by_operation_id.get(str(operation["operation_id"]), [])
            if len(id_candidates) == 1:
                match = id_candidates[0]
                if match.get("path") != operation.get("path"):
                    diagnostics.append(
                        _diagnostic(
                            "openapi_path_mismatch",
                            "Explicit operation_id matched a static handler with a different path.",
                            method=operation["method"],
                            path=operation["path"],
                        )
                    )
                if match.get("method") != operation.get("method"):
                    diagnostics.append(
                        _diagnostic(
                            "openapi_method_mismatch",
                            "Explicit operation_id matched a static handler with a different method.",
                            method=operation["method"],
                            path=operation["path"],
                        )
                    )
        if match is None:
            diagnostics.append(
                _diagnostic(
                    "openapi_operation_unlinked",
                    "OpenAPI operation has no unique static handler match.",
                    method=operation["method"],
                    path=operation["path"],
                )
            )
            continue
        operation["handler"] = match.get("handler")
        _attach_static_parameter_names(operation, match)
        if match.get("flow_id"):
            operation["flow_id"] = match["flow_id"]
        matched_static.add(str(match.get("id")))
        if _parameter_contract(operation) != _parameter_contract(match):
            diagnostics.append(
                _diagnostic(
                    "openapi_parameter_mismatch",
                    "Static and OpenAPI wire parameter contracts differ.",
                    method=operation["method"],
                    path=operation["path"],
                )
            )
        if _response_keys(operation) != _response_keys(match):
            diagnostics.append(
                _diagnostic(
                    "openapi_response_mismatch",
                    "Static and OpenAPI declared response statuses differ.",
                    method=operation["method"],
                    path=operation["path"],
                )
            )
        if _schema_contract(operation) != _schema_contract(match):
            diagnostics.append(
                _diagnostic(
                    "openapi_schema_mismatch",
                    "Static and OpenAPI request/response schemas differ.",
                    method=operation["method"],
                    path=operation["path"],
                )
            )
        if _content_type_contract(operation) != _content_type_contract(match):
            diagnostics.append(
                _diagnostic(
                    "openapi_content_type_mismatch",
                    "Static and OpenAPI request/response content types differ.",
                    method=operation["method"],
                    path=operation["path"],
                )
            )
    for operation in static_operations:
        if str(operation.get("id")) not in matched_static:
            diagnostics.append(
                _diagnostic(
                    "static_operation_missing_from_openapi",
                    "Static production operation is absent or unmatched in OpenAPI.",
                    method=operation.get("method"),
                    path=operation.get("path"),
                )
            )
    return {
        "source": "openapi",
        "applications": [
            {
                key: application.get(key)
                for key in ("file", "binding", "scope", "line")
                if application.get(key) is not None
            }
            for application in static.get("applications", [])
            if isinstance(application, Mapping)
        ],
        "operations": operations,
        "diagnostics": diagnostics,
        "excluded_counts": {
            "test_source": 0,
            "schema_excluded": 0,
            "conditional": 0,
        },
        "openapi": {
            key: loaded[key] for key in ("version", "path", "sha256", "format")
        },
    }


def build_api_contracts(
    inventory: Mapping[str, Mapping[str, Any]],
    *,
    openapi_file: str | Path | None = None,
    source_root: str | Path = ".",
) -> dict[str, Any]:
    """Build static contracts or reconcile them with authoritative OpenAPI."""
    loaded = (
        load_openapi_document(openapi_file, source_root=source_root)
        if openapi_file is not None
        else None
    )
    static = build_static_api_contracts(inventory)
    if loaded is None:
        return static
    return _reconcile_openapi(static, loaded)


def attach_routes_to_entry_points(
    entry_points: Sequence[Mapping[str, Any]], contracts: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Keep one HTTP flow per handler while attaching all resolved routes."""
    routes: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    leaf_qualnames: dict[tuple[str, str], set[str]] = defaultdict(set)
    for operation in contracts.get("operations", []):
        handler = operation.get("handler")
        if not isinstance(handler, Mapping):
            continue
        filepath = str(handler.get("file") or "")
        symbol = str(handler.get("symbol") or "")
        qualname = str(handler.get("qualname") or symbol)
        routes[(filepath, qualname)].append(
            {
                "method": operation.get("method"),
                "path": operation.get("path"),
                "operation_id": operation.get("operation_id"),
            }
        )
        leaf_qualnames[(filepath, symbol)].add(qualname)
    result = []
    for entry in entry_points:
        item = dict(entry)
        filepath = str(item.get("file") or "")
        symbol = str(item.get("symbol") or "")
        handler_routes = routes.get((filepath, symbol))
        if handler_routes is None:
            qualnames = leaf_qualnames.get((filepath, symbol.rsplit(".", 1)[-1]), set())
            if len(qualnames) == 1:
                handler_routes = routes.get((filepath, next(iter(qualnames))))
        if item.get("category") == "http" and handler_routes:
            item["routes"] = sorted(
                handler_routes, key=lambda route: (str(route["path"]), str(route["method"]))
            )
        result.append(item)
    return result


def _md_text(value: Any) -> str:
    if value in (None, ""):
        return "—"
    return (
        str(value)
        .replace("|", "\\|")
        .replace("`", "\\`")
        .replace("\n", " ")
    )


def _md_code(value: Any) -> str:
    text = (
        "—"
        if value in (None, "")
        else str(value).replace("|", "\\|").replace("\n", " ")
    )
    longest = max((len(match) for match in re.findall(r"`+", text)), default=0)
    fence = "`" * max(1, longest + 1)
    padding = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{padding}{text}{padding}{fence}"


def _operation_anchor(operation: Mapping[str, Any]) -> str:
    identity = operation.get("id") or (
        f"{operation.get('method', '')}-{operation.get('path', '')}"
    )
    normalized = _SAFE_ID_RE.sub("-", str(identity)).strip("-").lower()
    return f"operation-{normalized or 'unknown'}"


def _entity_link(name: Any, entity_page_map: Mapping[Any, str] | None) -> str:
    text = str(name)
    if not entity_page_map:
        return _md_code(text)
    matches = {
        page
        for key, page in entity_page_map.items()
        if (key[0] if isinstance(key, tuple) and key else key) == text
    }
    if len(matches) == 1:
        page = next(iter(matches))
        return f"[{_md_text(text)}](entities/{page}.md)"
    return _md_code(text)


def _handler_link(handler: Any, module_page_map: Mapping[str, str] | None) -> str:
    if not isinstance(handler, Mapping):
        return "Unknown"
    filepath = str(handler.get("file") or "")
    symbol = str(handler.get("qualname") or handler.get("symbol") or "unknown")
    if module_page_map and filepath in module_page_map:
        return f"[{_md_code(symbol)}](modules/{module_page_map[filepath]}.md)"
    return _md_code(f"{filepath}:{symbol}")


def render_api_contracts_markdown(
    contracts: Mapping[str, Any],
    *,
    module_page_map: Mapping[str, str] | None = None,
    entity_page_map: Mapping[Any, str] | None = None,
) -> str:
    """Render the canonical mixed ``api-contracts.md`` surface."""
    lines = ["# API contracts", ""]
    openapi = contracts.get("openapi")
    if isinstance(openapi, Mapping):
        lines.extend(
            [
                f"**Authority:** OpenAPI {openapi.get('version')} from {_md_code(openapi.get('path'))}",
                f"**Source hash:** {_md_code(openapi.get('sha256'))}",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "**Authority:** syntax-only static analysis",
                "",
                "> Values that cannot be reconstructed statically remain explicitly unknown.",
                "",
            ]
        )
    applications = list(contracts.get("applications", []))
    lines.extend(["## Applications", ""])
    if applications:
        lines.extend(
            [
                "| Binding | Scope | Source | Configuration |",
                "|---|---|---|---|",
            ]
        )
        for application in applications:
            config = application.get("config")
            config_text = (
                ", ".join(
                    f"{key}={_md_text(value)}"
                    for key, value in sorted(config.items())
                )
                if isinstance(config, Mapping) and config
                else "—"
            )
            source = f"{application.get('file', 'unknown')}:{application.get('line', '?')}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_code(application.get("binding")),
                        _md_code(application.get("scope")),
                        _md_code(source),
                        config_text,
                    ]
                )
                + " |"
            )
    else:
        lines.append("*No statically linked FastAPI application declaration.*")
    application_unknowns = [
        (application, unknown)
        for application in applications
        for unknown in application.get("unknowns", [])
        if isinstance(unknown, Mapping)
    ]
    if application_unknowns:
        lines.extend(["", "### Application unknowns", ""])
        for application, unknown in application_unknowns:
            lines.append(
                f"- {_md_code(application.get('binding'))} "
                f"{_md_code(unknown.get('field'))}: {_md_text(unknown.get('reason'))}"
            )
    lines.append("")

    operations = list(contracts.get("operations", []))
    lines.extend(["## Operations", ""])
    if operations:
        lines.extend(
            [
                "| Method | Path | Summary | Handler | Flow |",
                "|---|---|---|---|---|",
            ]
        )
        for operation in operations:
            flow = operation.get("flow_id")
            flow_text = f"[{_md_text(flow)}](flows/{flow}.md)" if flow else "—"
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_code(operation.get("method")),
                        _md_code(operation.get("path") or "unknown"),
                        _md_text(operation.get("summary")),
                        _handler_link(operation.get("handler"), module_page_map),
                        flow_text,
                    ]
                )
                + " |"
            )
    else:
        lines.append("*No production HTTP operations were assembled.*")
    lines.append("")

    for operation in operations:
        lines.extend(
            [
                f'<a id="{_operation_anchor(operation)}"></a>',
                "",
                f"## {_md_text(operation.get('method'))} {_md_text(operation.get('path') or 'unknown')}",
                "",
                f"**Operation id:** {_md_code(operation.get('operation_id') or operation.get('id'))}",
                f"**Handler:** {_handler_link(operation.get('handler'), module_page_map)}",
                "",
                "### Parameters",
                "",
            ]
        )
        parameters = operation.get("parameters", [])
        if parameters:
            lines.extend(
                [
                    "| Python name | Wire name | In | Type | Required | Nullable | Default | Description |",
                    "|---|---|---|---|---:|---:|---|---|",
                ]
            )
            for parameter in parameters:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _md_code(parameter.get("python_name")),
                            _md_code(parameter.get("wire_name")),
                            _md_text(parameter.get("location")),
                            _md_code(parameter.get("type")),
                            "yes" if parameter.get("required") else "no",
                            "yes" if parameter.get("nullable") else "no",
                            _md_code(parameter.get("default")) if "default" in parameter else "—",
                            _md_text(parameter.get("description")),
                        ]
                    )
                    + " |"
                )
        else:
            lines.append("*No declared wire parameters.*")
        lines.extend(["", "### Request body", ""])
        request_body = operation.get("request_body")
        if isinstance(request_body, Mapping):
            models = ", ".join(
                _entity_link(model, entity_page_map) for model in request_body.get("models", [])
            ) or "—"
            lines.append(
                f"- Content types: {', '.join(_md_code(item) for item in request_body.get('content_types', [])) or 'unknown'}"
            )
            lines.append(f"- Models: {models}")
            lines.append(f"- Required: {'yes' if request_body.get('required') else 'no'}")
        else:
            lines.append("*No declared request body.*")
        lines.extend(["", "### Responses", ""])
        responses = operation.get("responses", [])
        if responses:
            lines.extend(
                [
                    "| Status | Model | Content types | Description |",
                    "|---|---|---|---|",
                ]
            )
            for response in responses:
                model = response.get("model")
                if isinstance(model, list):
                    model_text = ", ".join(_entity_link(item, entity_page_map) for item in model)
                elif model:
                    model_text = _entity_link(model, entity_page_map)
                else:
                    model_text = "—"
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _md_code(response.get("status_code")),
                            model_text,
                            ", ".join(_md_code(item) for item in response.get("content_types", [])) or "unknown",
                            _md_text(response.get("description")),
                        ]
                    )
                    + " |"
                )
        else:
            lines.append("*Response contract unknown.*")
        unknowns = operation.get("unknowns", [])
        if unknowns:
            lines.extend(["", "### Unknowns", ""])
            for unknown in unknowns:
                lines.append(
                    f"- {_md_code(unknown.get('field'))}: {_md_text(unknown.get('reason'))}"
                )
        lines.append("")

    lines.extend(["## Diagnostics", ""])
    diagnostics = contracts.get("diagnostics", [])
    if diagnostics:
        for item in diagnostics:
            location = " ".join(
                part for part in (str(item.get("method") or ""), str(item.get("path") or "")) if part
            )
            suffix = f" ({location})" if location else ""
            lines.append(
                f"- **{_md_text(item.get('code'))}**{suffix}: {_md_text(item.get('message'))}"
            )
    else:
        lines.append("*No contract diagnostics.*")
    excluded = contracts.get("excluded_counts", {})
    lines.extend(
        [
            "",
            "## Excluded operations",
            "",
            f"- Test-source operations: {int(excluded.get('test_source', 0))}",
            f"- Schema-excluded operations: {int(excluded.get('schema_excluded', 0))}",
            f"- Conditional declarations: {int(excluded.get('conditional', 0))}",
            "",
            "## Notes",
            "",
            "_Record reviewed runtime-only contract details and reconciliation decisions here._",
            "",
        ]
    )
    return "\n".join(lines)


def render_flow_api_contract_section(operations: Sequence[Mapping[str, Any]]) -> str:
    """Render a concise generated section for one handler flow."""
    if not operations:
        return ""
    lines = ["## API contract", ""]
    for operation in sorted(
        operations, key=lambda item: (str(item.get("path") or ""), str(item.get("method") or ""))
    ):
        anchor = _operation_anchor(operation)
        route_label = f"{operation.get('method')} {operation.get('path') or 'unknown'}"
        lines.append(
            f"- {_md_code(route_label)} "
            f"([full contract](../api-contracts.md#{anchor}))"
        )
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "ApiContractError",
    "attach_routes_to_entry_points",
    "build_api_contracts",
    "build_static_api_contracts",
    "load_openapi_document",
    "render_api_contracts_markdown",
    "render_flow_api_contract_section",
]
