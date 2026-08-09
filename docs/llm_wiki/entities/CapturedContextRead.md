# CapturedContextRead

**Location:** `src/llm_wiki_cli/services/context_packet.py:178`
**Kind:** Class
**Bases:** —
**Module:** [context_packet](../modules/context_packet.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One coordinated in-memory source/wiki read used by a packet response.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `source_root` | `Path` | *required* | — |
| `wiki_root` | `Path` | *required* | — |
| `inventory_result` | `InventoryResult` | *required* | — |
| `source_snapshot` | `SourceSnapshot` | *required* | — |
| `inventory` | `Mapping[str, Any]` | *required* | — |
| `changed_files` | `tuple[str, ...] \| None` | *required* | — |
| `entrypoints` | `tuple[Mapping[str, Any], ...]` | *required* | — |
| `call_edges` | `tuple[Mapping[str, Any], ...]` | *required* | — |
| `flows` | `tuple[Mapping[str, Any], ...]` | *required* | — |
| `data_flows` | `tuple[Mapping[str, Any], ...]` | *required* | — |
| `dependency_analysis` | `Mapping[str, Any]` | *required* | — |
| `surface_evaluation` | `SurfaceIndexEvaluation` | *required* | — |
| `knowledge_view` | `KnowledgeReadView` | *required* | — |
| `source_anchor` | `str` | *required* | — |
| `wiki_anchor` | `str` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["CapturedContextRead (src/llm_wiki_cli/services/context_packet.py)"]
    n1["_assert_selection_unchanged (src/llm_wiki_cli/services/context_packet.py)"]
    n2["_build_protocol_enrichment_from_captured_read (src/llm_wiki_cli/services/context_packet.py)"]
    n3["_packet_basis (src/llm_wiki_cli/services/context_packet.py)"]
    n4["_packet_body (src/llm_wiki_cli/services/context_packet.py)"]
    n5["build_context_from_captured_read (src/llm_wiki_cli/services/context_packet.py)"]
    n6["capture_context_read (src/llm_wiki_cli/services/context_packet.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/context_packet.md"
    click n1 "../modules/context_packet.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/context_packet.md"
    click n6 "../modules/context_packet.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_packet](../modules/context_packet.md) | 1 | `call_edges`, `changed_files`, `data_flows`, `dependency_analysis`, `entrypoints`, `flows`, `inventory`, `inventory_result`, `knowledge_view`, `source_anchor`, `source_root`, `source_snapshot` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_assert_selection_unchanged` | type_reference | [context_packet](../modules/context_packet.md) |
| `_build_protocol_enrichment_from_captured_read` | type_reference | [context_packet](../modules/context_packet.md) |
| `_packet_basis` | type_reference | [context_packet](../modules/context_packet.md) |
| `_packet_body` | type_reference | [context_packet](../modules/context_packet.md) |
| `build_context_from_captured_read` | type_reference | [context_packet](../modules/context_packet.md) |
| `capture_context_read` | call | [context_packet](../modules/context_packet.md) |
| `capture_context_read` | type_reference | [context_packet](../modules/context_packet.md) |
