# CapturedContextRead

**Location:** `src/llm_wiki_cli/services/context_packet.py:301`
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
| `basis_incompatible` | `bool` | `False` | — |
| `strict_wiki_symlinks` | `bool` | `False` | — |
| `allow_external_src` | `bool` | `False` | — |

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
    n2["_build_knowledge_context_from_captured_read (src/llm_wiki_cli/services/context_packet.py)"]
    n3["_build_legacy_context_from_captured_read (src/llm_wiki_cli/services/context_packet.py)"]
    n4["_build_protocol_enrichment_from_captured_read (src/llm_wiki_cli/services/context_packet.py)"]
    n5["_candidate_packet_size (src/llm_wiki_cli/services/context_packet.py)"]
    n6["_captured_query_service (src/llm_wiki_cli/services/context_packet.py)"]
    n7["_captured_source_classification (src/llm_wiki_cli/services/context_packet.py)"]
    n8["_fit_knowledge_packet_response (src/llm_wiki_cli/services/context_packet.py)"]
    n9["_packet_basis (src/llm_wiki_cli/services/context_packet.py)"]
    n10["_packet_body (src/llm_wiki_cli/services/context_packet.py)"]
    n11["build_context_from_captured_read (src/llm_wiki_cli/services/context_packet.py)"]
    n12["capture_context_read (src/llm_wiki_cli/services/context_packet.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    n12 --> n0
    click n0 "../modules/context_packet.md"
    click n1 "../modules/context_packet.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/context_packet.md"
    click n6 "../modules/context_packet.md"
    click n7 "../modules/context_packet.md"
    click n8 "../modules/context_packet.md"
    click n9 "../modules/context_packet.md"
    click n10 "../modules/context_packet.md"
    click n11 "../modules/context_packet.md"
    click n12 "../modules/context_packet.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_packet](../modules/context_packet.md) | 1 | `allow_external_src`, `basis_incompatible`, `call_edges`, `changed_files`, `data_flows`, `dependency_analysis`, `entrypoints`, `flows`, `inventory`, `inventory_result`, `knowledge_view`, `source_anchor` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_assert_selection_unchanged` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_build_knowledge_context_from_captured_read` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_build_legacy_context_from_captured_read` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_build_protocol_enrichment_from_captured_read` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_candidate_packet_size` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_captured_query_service` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_captured_source_classification` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_fit_knowledge_packet_response` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_packet_basis` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_packet_body` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `build_context_from_captured_read` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `capture_context_read` | call | [context_packet](../modules/context_packet.md) | 1 |

> References: showing 12 of 13 logical references; 1 omitted by the 12-row generated summary limit.
