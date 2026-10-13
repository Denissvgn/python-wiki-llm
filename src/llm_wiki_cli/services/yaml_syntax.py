"""Bounded YAML composition for static configuration observations.

Nodes are inspected directly rather than invoking YAML constructors. Scalar
lexemes remain strings, including GitHub's unquoted ``on`` mapping key.
"""

from __future__ import annotations

import yaml
from yaml.events import CollectionEndEvent, CollectionStartEvent, DocumentStartEvent
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode


MAX_YAML_BYTES = 1_048_576
MAX_YAML_EVENTS = 20_000
MAX_YAML_EXPANDED_NODES = 20_000
MAX_YAML_DEPTH = 64
MAX_YAML_DOCUMENTS = 128
_TAG_PREFIX = "tag:yaml.org,2002:"
_SCALAR_TAGS = {
    f"{_TAG_PREFIX}{name}"
    for name in ("str", "null", "bool", "int", "float", "timestamp")
}


class _InvalidYaml(ValueError):
    """An unsupported or over-budget YAML observation."""


def yaml_mapping(value: object) -> dict:
    """Return a composed mapping, or an empty mapping for another shape."""
    return value if isinstance(value, dict) else {}


def yaml_scalar(value: object) -> str:
    """Return composed scalar text without stringifying collections."""
    return value if isinstance(value, str) else ""


def load_yaml_documents(text: str) -> tuple[list[object], list[str]]:
    """Compose YAML into string-keyed models, or return a qualified failure.

    Supported syntax includes flow collections, block scalars, anchors, aliases,
    and mapping merges. Duplicate explicit keys, custom tags, recursive aliases,
    complex keys, and bounded-workload violations reject the entire stream.
    """
    if len(text.encode("utf-8", errors="replace")) > MAX_YAML_BYTES:
        return [], [f"YAML byte budget exceeded ({MAX_YAML_BYTES} bytes)."]
    try:
        _check_events(text)
        expanded = [0]
        documents: list[object] = []
        for node in yaml.compose_all(text, Loader=yaml.SafeLoader):
            if node is not None and not (
                isinstance(node, ScalarNode)
                and node.tag == f"{_TAG_PREFIX}null"
                and node.value == ""
            ):
                documents.append(_convert_node(node, set(), expanded, 0))
        return documents, []
    except _InvalidYaml as exc:
        return [], [f"YAML observation rejected: {exc}."]
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        position = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        return [], [f"Malformed YAML{position}; no observations were retained."]
    except (RecursionError, UnicodeError):
        return [], ["YAML nesting or encoding could not be observed safely."]


def _check_events(text: str) -> None:
    depth = 0
    documents = 0
    for count, event in enumerate(yaml.parse(text, Loader=yaml.SafeLoader), 1):
        if count > MAX_YAML_EVENTS:
            raise _InvalidYaml(f"event budget exceeded ({MAX_YAML_EVENTS} events)")
        if isinstance(event, CollectionStartEvent):
            depth += 1
            if depth > MAX_YAML_DEPTH:
                raise _InvalidYaml(f"depth budget exceeded ({MAX_YAML_DEPTH} levels)")
        elif isinstance(event, CollectionEndEvent):
            depth -= 1
        elif isinstance(event, DocumentStartEvent):
            documents += 1
            if documents > MAX_YAML_DOCUMENTS:
                raise _InvalidYaml(
                    f"document budget exceeded ({MAX_YAML_DOCUMENTS} documents)"
                )


def _convert_node(
    node: Node, active: set[int], expanded: list[int], depth: int
) -> object:
    expanded[0] += 1
    if expanded[0] > MAX_YAML_EXPANDED_NODES:
        raise _InvalidYaml(
            f"expanded-node budget exceeded ({MAX_YAML_EXPANDED_NODES} nodes)"
        )
    if depth > MAX_YAML_DEPTH:
        raise _InvalidYaml(f"depth budget exceeded ({MAX_YAML_DEPTH} levels)")
    if id(node) in active:
        raise _InvalidYaml("recursive alias")
    if isinstance(node, ScalarNode):
        if node.tag not in _SCALAR_TAGS:
            raise _InvalidYaml("unsupported YAML tag")
        return node.value
    active.add(id(node))
    try:
        if isinstance(node, SequenceNode) and node.tag == f"{_TAG_PREFIX}seq":
            return [
                _convert_node(child, active, expanded, depth + 1)
                for child in node.value
            ]
        if isinstance(node, MappingNode) and node.tag == f"{_TAG_PREFIX}map":
            return _convert_mapping(node, active, expanded, depth)
        raise _InvalidYaml("unsupported YAML tag or node")
    finally:
        active.remove(id(node))


def _convert_mapping(
    node: MappingNode, active: set[int], expanded: list[int], depth: int
) -> dict[str, object]:
    explicit: dict[str, object] = {}
    merged: dict[str, object] = {}
    has_merge = False
    for key_node, value_node in node.value:
        if not isinstance(key_node, ScalarNode):
            raise _InvalidYaml("complex mapping key")
        if key_node.tag == f"{_TAG_PREFIX}merge":
            if has_merge:
                raise _InvalidYaml("duplicate merge key")
            has_merge = True
            values = _convert_node(value_node, active, expanded, depth + 1)
            sources = values if isinstance(values, list) else [values]
            for source in reversed(sources):
                if not isinstance(source, dict):
                    raise _InvalidYaml("mapping merge requires mappings")
                merged.update(source)
            continue
        key = _convert_node(key_node, active, expanded, depth + 1)
        if not isinstance(key, str):
            raise _InvalidYaml("non-scalar mapping key")
        if key in explicit:
            raise _InvalidYaml("duplicate mapping key")
        explicit[key] = _convert_node(value_node, active, expanded, depth + 1)
    merged.update(explicit)
    return merged
