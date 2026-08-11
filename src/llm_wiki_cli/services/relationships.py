"""Pure entity and callable relationship summaries.

The summaries in this module are intentionally plain dictionaries derived from
the source inventory, optional resolved call edges, and optional entry-point
flows. They do not read or write files and do not render Markdown.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath
from typing import Iterable, Mapping, Optional

from .imports import build_module_path_resolver
from .validation import positive_int_or_none

_RELATION_LIMIT = 12
_RELATIONSHIP_SUMMARIES_SCHEMA = "llm-wiki-relationship-summaries/v1"


def _sort_key(value: object) -> tuple[str, str]:
    text = "" if value is None else str(value)
    return text.casefold(), text


def _module_name(filepath: Optional[str]) -> Optional[str]:
    if not filepath:
        return None
    return PurePosixPath(filepath).stem


def _class_ref(name: str, filepath: Optional[str]) -> dict:
    return {"name": name, "file": filepath, "module": _module_name(filepath)}


def _endpoint_ref(endpoint: Mapping, edge: Mapping) -> dict:
    filepath = endpoint.get("file")
    return {
        "file": filepath,
        "module": _module_name(str(filepath)) if filepath else None,
        "symbol": endpoint.get("symbol"),
        "kind": edge.get("kind", "unknown"),
        "line": edge.get("line", 0),
    }


def _bounded(
    records: Iterable[dict], limit: int | None = _RELATION_LIMIT
) -> list[dict]:
    values = list(records)
    return values if limit is None else values[:limit]


def _record_sort_key(record: Mapping) -> tuple:
    ordered_keys = (
        "file",
        "module",
        "symbol",
        "name",
        "id",
        "category",
        "label",
        "role",
        "kind",
        "line",
        "depth",
    )
    parts = [_sort_key(record.get(key)) for key in ordered_keys if key in record]
    remaining = sorted(key for key in record if key not in ordered_keys)
    parts.extend(_sort_key(record.get(key)) for key in remaining)
    return tuple(parts)


def _dedupe_sorted(
    records: Iterable[dict], limit: int | None = _RELATION_LIMIT
) -> list[dict]:
    unique = {}
    for record in records:
        key = tuple(sorted(record.items()))
        unique[key] = dict(record)
    ordered = sorted(unique, key=lambda item: _record_sort_key(unique[item]))
    return _bounded((unique[key] for key in ordered), limit)


def _iter_class_records(inventory: Mapping) -> Iterable[tuple[str, str, Mapping]]:
    for filepath in sorted(inventory, key=_sort_key):
        data = inventory[filepath] or {}
        for cls in data.get("classes", []) or []:
            name = cls.get("name")
            if name:
                yield filepath, str(name), cls


def _build_class_index(inventory: Mapping) -> tuple[dict, dict]:
    by_key = {}
    by_name = defaultdict(list)
    for filepath, name, cls in _iter_class_records(inventory):
        key = (str(filepath), name)
        by_key[key] = cls
        by_name[name].append(key)
    for name in by_name:
        by_name[name].sort(key=lambda item: (_sort_key(item[0]), _sort_key(item[1])))
    return by_key, dict(by_name)


def _imported_class_bindings(
    inventory: Mapping, filepath: str, by_key: Mapping, resolver
) -> dict[str, tuple[str, str]]:
    data = inventory.get(filepath) or {}
    bindings = {}
    for imp in data.get("imports", []) or []:
        source_name = imp.get("name")
        if not source_name:
            continue
        candidates = [
            candidate
            for candidate in resolver.candidates(imp.get("module", ""), filepath)
            if (candidate, source_name) in by_key
        ]
        if len(candidates) == 1:
            bindings[str(imp.get("alias") or source_name)] = (
                candidates[0],
                str(source_name),
            )
    return bindings


def _resolve_base_key(
    raw_base: str,
    filepath: str,
    by_key: Mapping[tuple[str, str], Mapping],
    by_name: Mapping[str, list[tuple[str, str]]],
    imported: Mapping[str, tuple[str, str]],
    resolver,
) -> Optional[tuple[str, str]]:
    base = raw_base.strip()
    if not base:
        return None
    leaf = base.replace("::", ".").rsplit(".", 1)[-1]

    same_file = (filepath, leaf)
    if same_file in by_key:
        return same_file

    if leaf in imported:
        return imported[leaf]

    if "." in base or "::" in base:
        module, _, name = base.replace("::", ".").rpartition(".")
        candidates = [
            candidate
            for candidate in resolver.candidates(module, filepath)
            if (candidate, name) in by_key
        ]
        if len(candidates) == 1:
            return candidates[0], name

    candidates = by_name.get(leaf, [])
    if len(candidates) == 1:
        return candidates[0]
    return None


def _resolved_bases(
    inventory: Mapping,
    by_key: Mapping[tuple[str, str], Mapping],
    by_name: Mapping[str, list[tuple[str, str]]],
    relation_limit: int | None = _RELATION_LIMIT,
) -> dict[tuple[str, str], list[dict]]:
    resolver = build_module_path_resolver(dict(inventory))
    imported_cache = {}
    bases = {}
    for filepath, name, cls in _iter_class_records(inventory):
        imported_cache.setdefault(
            filepath, _imported_class_bindings(inventory, filepath, by_key, resolver)
        )
        resolved = []
        for raw_base in cls.get("bases", []) or []:
            raw_text = str(raw_base)
            key = _resolve_base_key(
                raw_text,
                filepath,
                by_key,
                by_name,
                imported_cache[filepath],
                resolver,
            )
            if key is None:
                resolved.append(_class_ref(raw_text, None))
            else:
                resolved.append(_class_ref(key[1], key[0]))
        bases[(filepath, name)] = _dedupe_sorted(resolved, relation_limit)
    return bases


def _subclasses_by_base(
    bases_by_class: Mapping[tuple[str, str], list[dict]],
    relation_limit: int | None = _RELATION_LIMIT,
) -> dict[tuple[str, str], list[dict]]:
    subclasses = defaultdict(list)
    for (filepath, name), bases in bases_by_class.items():
        child = _class_ref(name, filepath)
        for base in bases:
            if base.get("file"):
                subclasses[(base["file"], base["name"])].append(child)
    return {
        key: _dedupe_sorted(value, relation_limit)
        for key, value in subclasses.items()
    }


def _iter_callable_records(inventory: Mapping) -> Iterable[tuple[str, str, dict]]:
    for filepath in sorted(inventory, key=_sort_key):
        data = inventory[filepath] or {}
        for fn in data.get("functions", []) or []:
            name = fn.get("name")
            if name:
                yield (
                    filepath,
                    str(name),
                    {
                        "record": fn,
                        "name": str(name),
                        "kind": "function",
                        "owner_class": None,
                    },
                )
        for cls in data.get("classes", []) or []:
            owner = cls.get("name")
            if not owner:
                continue
            for method in cls.get("methods", []) or []:
                name = method.get("name")
                if name:
                    yield (
                        filepath,
                        f"{owner}.{name}",
                        {
                            "record": method,
                            "name": str(name),
                            "kind": "method",
                            "owner_class": str(owner),
                        },
                    )
        for fn in data.get("nested_functions", []) or []:
            name = fn.get("name")
            if name:
                yield (
                    filepath,
                    str(name),
                    {
                        "record": fn,
                        "name": str(name),
                        "kind": "nested_function",
                        "owner_class": None,
                    },
                )


def _callable_index(inventory: Mapping) -> dict[tuple[str, str], dict]:
    return {
        (filepath, symbol): dict(info)
        for filepath, symbol, info in _iter_callable_records(inventory)
    }


def _mentions_any(text: object, visible_names: Iterable[str]) -> bool:
    value = "" if text is None else str(text)
    return any(name and name in value for name in visible_names)


def _callable_mentions_class(callable_info: Mapping, visible_names: set[str]) -> bool:
    fn = callable_info.get("record", {})
    for param in fn.get("params", []) or []:
        if _mentions_any(param.get("type", ""), visible_names):
            return True
    if _mentions_any(fn.get("return_type", ""), visible_names):
        return True
    for decorator in fn.get("decorators", []) or []:
        if _mentions_any(decorator, visible_names):
            return True
    return False


def _visible_class_bindings(
    inventory: Mapping,
    filepath: str,
    by_key: Mapping[tuple[str, str], Mapping],
    resolver,
) -> dict[str, tuple[str, str]]:
    bindings = _imported_class_bindings(inventory, filepath, by_key, resolver)
    data = inventory.get(filepath) or {}
    for cls in data.get("classes", []) or []:
        name = cls.get("name")
        if name:
            bindings.setdefault(str(name), (filepath, str(name)))
    return bindings


def _type_reference_records(
    inventory: Mapping,
    by_key: Mapping[tuple[str, str], Mapping],
    callables: Mapping[tuple[str, str], dict],
) -> dict[tuple[str, str], list[dict]]:
    resolver = build_module_path_resolver(dict(inventory))
    references = defaultdict(list)
    binding_cache = {}

    for (filepath, symbol), callable_info in callables.items():
        binding_cache.setdefault(
            filepath, _visible_class_bindings(inventory, filepath, by_key, resolver)
        )
        bindings = binding_cache[filepath]
        for visible_name, class_key in bindings.items():
            if _callable_mentions_class(callable_info, {visible_name}):
                references[class_key].append(
                    {
                        "file": filepath,
                        "module": _module_name(filepath),
                        "symbol": symbol,
                        "kind": "type_reference",
                    }
                )
    return references


def _class_call_references(
    call_edges: Iterable[Mapping],
    by_key: Mapping[tuple[str, str], Mapping],
) -> dict[tuple[str, str], list[dict]]:
    references = defaultdict(list)
    for edge in call_edges or []:
        target = edge.get("to", {}) or {}
        target_file = target.get("file")
        target_symbol = target.get("symbol")
        if (target_file, target_symbol) not in by_key:
            continue
        source = edge.get("from", {}) or {}
        source_file = source.get("file")
        references[(target_file, target_symbol)].append(
            {
                "file": source_file,
                "module": _module_name(str(source_file)) if source_file else None,
                "symbol": source.get("symbol"),
                "kind": "call",
                "line": edge.get("line", 0),
            }
        )
    return references


def _import_reference_records(
    inventory: Mapping,
    by_key: Mapping[tuple[str, str], Mapping],
    existing_references: Mapping[tuple[str, str], list[dict]],
) -> dict[tuple[str, str], list[dict]]:
    resolver = build_module_path_resolver(dict(inventory))
    references = defaultdict(list)
    for filepath in sorted(inventory, key=_sort_key):
        imported = _imported_class_bindings(inventory, filepath, by_key, resolver)
        for class_key in imported.values():
            if any(
                reference.get("file") == filepath
                for reference in existing_references.get(class_key, [])
            ):
                continue
            references[class_key].append(
                {
                    "file": filepath,
                    "module": _module_name(filepath),
                    "symbol": None,
                    "kind": "import",
                }
            )
    return references


def _merge_reference_maps(
    *maps: Mapping[tuple[str, str], list[dict]],
    relation_limit: int | None = _RELATION_LIMIT,
) -> dict:
    merged = defaultdict(list)
    for reference_map in maps:
        for key, records in reference_map.items():
            merged[key].extend(records)
    return {
        key: _dedupe_sorted(records, relation_limit)
        for key, records in merged.items()
    }


def _function_links(
    call_edges: Iterable[Mapping],
    callables: Mapping[tuple[str, str], dict],
    relation_limit: int | None = _RELATION_LIMIT,
) -> tuple[dict, dict]:
    callers = defaultdict(list)
    callees = defaultdict(list)
    for edge in call_edges or []:
        source = edge.get("from", {}) or {}
        target = edge.get("to", {}) or {}
        source_key = (source.get("file"), source.get("symbol"))
        target_key = (target.get("file"), target.get("symbol"))
        if source_key in callables:
            callees[source_key].append(_endpoint_ref(target, edge))
        if target_key in callables:
            callers[target_key].append(_endpoint_ref(source, edge))
    return (
        {
            key: _dedupe_sorted(value, relation_limit)
            for key, value in callers.items()
        },
        {
            key: _dedupe_sorted(value, relation_limit)
            for key, value in callees.items()
        },
    )


def _flow_id(flow: Mapping) -> str:
    entry = flow.get("entry", {}) or {}
    return str(flow.get("id") or entry.get("id") or entry.get("label") or "entry")


def _flow_category(flow: Mapping) -> str:
    entry = flow.get("entry", {}) or {}
    return str(flow.get("category") or entry.get("category") or "")


def _flow_label(flow: Mapping) -> str:
    entry = flow.get("entry", {}) or {}
    return str(flow.get("label") or entry.get("label") or entry.get("symbol") or "")


def _flow_memberships(
    flows: Iterable[Mapping],
    callables: Mapping[tuple[str, str], dict],
    relation_limit: int | None = _RELATION_LIMIT,
) -> dict[tuple[str, str], list[dict]]:
    memberships = defaultdict(list)
    for flow in flows or []:
        entry = flow.get("entry", {}) or {}
        entry_key = (entry.get("file"), entry.get("symbol"))
        for step in flow.get("steps", []) or []:
            key = (step.get("file"), step.get("symbol"))
            if key not in callables:
                continue
            role = (
                "entry" if key == entry_key or step.get("kind") == "entry" else "step"
            )
            memberships[key].append(
                {
                    "id": _flow_id(flow),
                    "category": _flow_category(flow),
                    "label": _flow_label(flow),
                    "role": role,
                    "depth": step.get("depth", 0),
                }
            )
    return {
        key: _dedupe_sorted(value, relation_limit)
        for key, value in memberships.items()
    }


def _class_summary(
    filepath: str,
    name: str,
    cls: Mapping,
    bases_by_class: Mapping[tuple[str, str], list[dict]],
    subclasses_by_class: Mapping[tuple[str, str], list[dict]],
    references_by_class: Mapping[tuple[str, str], list[dict]],
    relation_limit: int | None = _RELATION_LIMIT,
) -> dict:
    key = (filepath, name)
    attributes = sorted(
        {
            str(attribute.get("name"))
            for attribute in cls.get("attributes", []) or []
            if attribute.get("name")
        },
        key=_sort_key,
    )
    summary = {
        "name": name,
        "file": filepath,
        "module": _module_name(filepath),
        "bases": bases_by_class.get(key, []),
        "subclasses": subclasses_by_class.get(key, []),
        "methods_count": len(cls.get("methods", []) or []),
        "attributes": (
            list(attributes)
            if relation_limit is None
            else list(attributes)[:relation_limit]
        ),
        "references": references_by_class.get(key, []),
    }
    if cls.get("kind"):
        summary["kind"] = cls.get("kind")
    return summary


def _function_summary(
    filepath: str,
    symbol: str,
    callable_info: Mapping,
    callers: Mapping[tuple[str, str], list[dict]],
    callees: Mapping[tuple[str, str], list[dict]],
    entrypoints: Mapping[tuple[str, str], list[dict]],
) -> dict:
    key = (filepath, symbol)
    return {
        "symbol": symbol,
        "name": callable_info["name"],
        "file": filepath,
        "module": _module_name(filepath),
        "kind": callable_info["kind"],
        "owner_class": callable_info["owner_class"],
        "callers": callers.get(key, []),
        "callees": callees.get(key, []),
        "entrypoints": entrypoints.get(key, []),
    }


def _build_entity_relationship_summaries(
    inventory: Mapping,
    call_edges: Optional[Iterable[Mapping]] = None,
    flows: Optional[Iterable[Mapping]] = None,
    *,
    relation_limit: int | None,
) -> dict:
    inventory = inventory or {}
    edges = list(call_edges or [])
    flow_list = list(flows or [])

    classes_by_key, classes_by_name = _build_class_index(inventory)
    bases_by_class = _resolved_bases(
        inventory,
        classes_by_key,
        classes_by_name,
        relation_limit,
    )
    subclasses = _subclasses_by_base(bases_by_class, relation_limit)
    callables = _callable_index(inventory)
    type_references = _type_reference_records(inventory, classes_by_key, callables)
    call_references = _class_call_references(edges, classes_by_key)
    specific_references = _merge_reference_maps(
        type_references,
        call_references,
        relation_limit=relation_limit,
    )
    import_references = _import_reference_records(
        inventory, classes_by_key, specific_references
    )
    class_references = _merge_reference_maps(
        specific_references,
        import_references,
        relation_limit=relation_limit,
    )
    callers, callees = _function_links(edges, callables, relation_limit)
    entrypoints = _flow_memberships(flow_list, callables, relation_limit)

    class_summaries = [
        _class_summary(
            filepath,
            name,
            cls,
            bases_by_class,
            subclasses,
            class_references,
            relation_limit,
        )
        for (filepath, name), cls in sorted(
            classes_by_key.items(),
            key=lambda item: (_sort_key(item[0][0]), _sort_key(item[0][1])),
        )
    ]
    function_summaries = [
        _function_summary(filepath, symbol, info, callers, callees, entrypoints)
        for (filepath, symbol), info in sorted(
            callables.items(),
            key=lambda item: (_sort_key(item[0][0]), _sort_key(item[0][1])),
        )
    ]
    return {"classes": class_summaries, "functions": function_summaries}


def _detail_line(value: object) -> int | None:
    return positive_int_or_none(value)


def _normalize_detailed_record(value: object, *, key: str | None = None) -> object:
    if key == "line":
        return _detail_line(value)
    if isinstance(value, Mapping):
        return {
            str(child_key): _normalize_detailed_record(
                child_value, key=str(child_key)
            )
            for child_key, child_value in value.items()
        }
    if isinstance(value, list):
        return [_normalize_detailed_record(item) for item in value]
    return value


def _summary_collection_coverage(observed: int, emitted: int) -> dict:
    omitted = max(0, observed - emitted)
    return {
        "observed": observed,
        "emitted": emitted,
        "limit": _RELATION_LIMIT,
        "truncated": omitted > 0,
        "omitted": omitted,
        "limitations": ["presentation-summary-limit"],
    }


def _detailed_summary(summary: Mapping, collection_fields: tuple[str, ...]) -> dict:
    detailed = dict(summary)
    coverage = {}
    for field in collection_fields:
        values = list(summary.get(field, []) or [])
        emitted = values[:_RELATION_LIMIT]
        detailed[field] = _normalize_detailed_record(emitted)
        coverage[field] = _summary_collection_coverage(len(values), len(emitted))
    detailed["coverage"] = coverage
    normalized = _normalize_detailed_record(detailed)
    assert isinstance(normalized, dict)
    return normalized


def _unbounded_summary_coverage(observed: int) -> dict:
    return {
        "observed": observed,
        "emitted": observed,
        "limit": None,
        "truncated": False,
        "omitted": 0,
        "limitations": [],
    }


def _page_reference_projection(records: Iterable[dict]) -> tuple[list[dict], dict]:
    """Return bounded logical references for generated entity pages.

    Raw call references remain line-specific in the public summary builders.  A
    generated page, however, presents the source callable rather than each
    individual call site, so collapse calls only after exact record
    deduplication and expose their distinct site count separately.
    """
    exact_records = _dedupe_sorted(records, limit=None)
    logical_records = []
    calls: dict[tuple[object, ...], dict] = {}
    for record in exact_records:
        if record.get("kind") != "call":
            logical_records.append(dict(record))
            continue

        key = tuple(record.get(field) for field in ("file", "module", "symbol", "kind"))
        grouped = calls.get(key)
        if grouped is None:
            grouped = {
                "file": record.get("file"),
                "module": record.get("module"),
                "symbol": record.get("symbol"),
                "kind": "call",
                "call_site_count": 0,
            }
            calls[key] = grouped
        grouped["call_site_count"] += 1

    logical_records.extend(calls.values())
    ordered = _dedupe_sorted(logical_records, limit=None)
    emitted = ordered[:_RELATION_LIMIT]
    observed_count = len(ordered)
    emitted_count = len(emitted)
    omitted_count = observed_count - emitted_count
    return emitted, {
        "observed": observed_count,
        "emitted": emitted_count,
        "limit": _RELATION_LIMIT,
        "truncated": omitted_count > 0,
        "omitted": omitted_count,
    }


def build_entity_page_relationship_summaries(
    inventory: Mapping,
    call_edges: Optional[Iterable[Mapping]] = None,
    flows: Optional[Iterable[Mapping]] = None,
) -> dict:
    """Build the internal relationship projection used by generated pages.

    Entity-page references are logical source relationships: repeated call
    sites from the same source callable are represented once with a
    ``call_site_count``.  Other relationship collections retain the legacy
    presentation limit.  Public and versioned summary builders intentionally
    do not use this projection.
    """
    full = _build_entity_relationship_summaries(
        inventory,
        call_edges,
        flows,
        relation_limit=None,
    )
    classes = []
    for summary in full["classes"]:
        page_summary = dict(summary)
        for field in ("bases", "subclasses", "attributes"):
            page_summary[field] = list(summary.get(field, []) or [])[
                :_RELATION_LIMIT
            ]
        references, coverage = _page_reference_projection(
            summary.get("references", []) or []
        )
        page_summary["references"] = references
        page_summary["reference_coverage"] = coverage
        classes.append(page_summary)

    functions = []
    for summary in full["functions"]:
        page_summary = dict(summary)
        for field in ("callers", "callees", "entrypoints"):
            page_summary[field] = list(summary.get(field, []) or [])[
                :_RELATION_LIMIT
            ]
        functions.append(page_summary)
    return {"classes": classes, "functions": functions}


def build_detailed_entity_relationship_summaries(
    inventory: Mapping,
    call_edges: Optional[Iterable[Mapping]] = None,
    flows: Optional[Iterable[Mapping]] = None,
) -> dict:
    """Build a versioned relationship-summary view with exact omissions."""
    full = _build_entity_relationship_summaries(
        inventory,
        call_edges,
        flows,
        relation_limit=None,
    )
    classes = [
        _detailed_summary(
            summary,
            ("bases", "subclasses", "attributes", "references"),
        )
        for summary in full["classes"]
    ]
    functions = [
        _detailed_summary(summary, ("callers", "callees", "entrypoints"))
        for summary in full["functions"]
    ]
    collection_coverages = [
        coverage
        for summary in [*classes, *functions]
        for coverage in summary["coverage"].values()
    ]
    observed = sum(item["observed"] for item in collection_coverages)
    emitted = sum(item["emitted"] for item in collection_coverages)
    omitted = sum(item["omitted"] for item in collection_coverages)
    return {
        "schema_version": _RELATIONSHIP_SUMMARIES_SCHEMA,
        "classes": classes,
        "functions": functions,
        "coverage": {
            "classes": _unbounded_summary_coverage(len(classes)),
            "functions": _unbounded_summary_coverage(len(functions)),
            "relationships": {
                "observed": observed,
                "emitted": emitted,
                "limit": None,
                "truncated": omitted > 0,
                "omitted": omitted,
                "limitations": [
                    "limit-applies-per-summary-relationship-collection"
                ],
            },
        },
    }


def build_entity_relationship_summaries(
    inventory: Mapping,
    call_edges: Optional[Iterable[Mapping]] = None,
    flows: Optional[Iterable[Mapping]] = None,
    *,
    detailed: bool = False,
) -> dict:
    """Build bounded class and callable relationship summaries.

    ``inventory`` is the existing deep or shallow extractor inventory. Optional
    ``call_edges`` should use the shape returned by
    ``extract_cmd.resolve_call_edges``; optional ``flows`` should use the shape
    returned by ``entrypoints.build_flow``. Missing optional metadata simply
    yields empty relationship lists.  Set ``detailed=True`` for the explicit
    versioned shape with per-collection totals and omissions; the default
    result remains the legacy byte/shape-compatible mapping.
    """
    if detailed:
        return build_detailed_entity_relationship_summaries(
            inventory,
            call_edges,
            flows,
        )
    return _build_entity_relationship_summaries(
        inventory,
        call_edges,
        flows,
        relation_limit=_RELATION_LIMIT,
    )
