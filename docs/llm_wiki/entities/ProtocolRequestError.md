# ProtocolRequestError

**Location:** `src/llm_wiki_cli/services/context_request_format.py:118`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [context_request_format](../modules/context_request_format.md)

## Description

Validation error for Wiki-as-Context protocol requests.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(message: str, field: str \| None = None, *, protocol: str = PROTOCOL_VERSION)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ProtocolRequestError (src/llm_wiki_cli/services/context_request_format.py)"]
    n1["ValueError"]
    n2["_build_protocol_enrichment_from_captured_read (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n3["_captured_query_service (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n4["_normalized_request (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n5["_packet_contract_for_request (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n6["capture_context_read (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n7["_normalise_protocol_filters (src/llm_wiki_cli/services/context_request_format.py)"]
    n8["_normalise_protocol_focus (src/llm_wiki_cli/services/context_request_format.py)"]
    n9["_validate_enum_filter (src/llm_wiki_cli/services/context_request_format.py)"]
    n10["_validate_protocol_request_impl (src/llm_wiki_cli/services/context_request_format.py)"]
    n11["_validate_relationship_kind_filter (src/llm_wiki_cli/services/context_request_format.py)"]
    n12["_validate_surface_filter (src/llm_wiki_cli/services/context_request_format.py)"]
    n13["validate_budget_request (src/llm_wiki_cli/services/context_request_format.py)"]
    n0 --> n1
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
    n13 --> n0
    click n0 "../modules/context_request_format.md"
    click n2 "../modules/context_packet_builder.md"
    click n3 "../modules/context_packet_builder.md"
    click n4 "../modules/context_packet_builder.md"
    click n5 "../modules/context_packet_builder.md"
    click n6 "../modules/context_packet_builder.md"
    click n7 "../modules/context_request_format.md"
    click n8 "../modules/context_request_format.md"
    click n9 "../modules/context_request_format.md"
    click n10 "../modules/context_request_format.md"
    click n11 "../modules/context_request_format.md"
    click n12 "../modules/context_request_format.md"
    click n13 "../modules/context_request_format.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_request_format](../modules/context_request_format.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_build_protocol_enrichment_from_captured_read` | call | [context_packet_builder](../modules/context_packet_builder.md) | 1 |
| `_captured_query_service` | call | [context_packet_builder](../modules/context_packet_builder.md) | 1 |
| `_normalized_request` | call | [context_packet_builder](../modules/context_packet_builder.md) | 1 |
| `_packet_contract_for_request` | call | [context_packet_builder](../modules/context_packet_builder.md) | 1 |
| `capture_context_read` | call | [context_packet_builder](../modules/context_packet_builder.md) | 7 |
| `_normalise_protocol_filters` | call | [context_request_format](../modules/context_request_format.md) | 6 |
| `_normalise_protocol_focus` | call | [context_request_format](../modules/context_request_format.md) | 6 |
| `_validate_enum_filter` | call | [context_request_format](../modules/context_request_format.md) | 1 |
| `_validate_protocol_request_impl` | call | [context_request_format](../modules/context_request_format.md) | 10 |
| `_validate_relationship_kind_filter` | call | [context_request_format](../modules/context_request_format.md) | 1 |
| `_validate_surface_filter` | call | [context_request_format](../modules/context_request_format.md) | 1 |
| `validate_budget_request` | call | [context_request_format](../modules/context_request_format.md) | 6 |

> References: showing 12 of 22 logical references; 10 omitted by the 12-row generated summary limit.
