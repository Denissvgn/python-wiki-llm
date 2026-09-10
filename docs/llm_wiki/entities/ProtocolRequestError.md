# ProtocolRequestError

**Location:** `src/llm_wiki_cli/services/context_service.py:176`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [context_service](../modules/context_service.md)

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
    n0["ProtocolRequestError (src/llm_wiki_cli/services/context_service.py)"]
    n1["ValueError"]
    n2["_build_protocol_enrichment_from_captured_read (src/llm_wiki_cli/services/context_packet.py)"]
    n3["_captured_query_service (src/llm_wiki_cli/services/context_packet.py)"]
    n4["_normalized_request (src/llm_wiki_cli/services/context_packet.py)"]
    n5["_packet_contract_for_request (src/llm_wiki_cli/services/context_packet.py)"]
    n6["capture_context_read (src/llm_wiki_cli/services/context_packet.py)"]
    n7["_build_context (src/llm_wiki_cli/services/context_service.py)"]
    n8["_build_context_impl (src/llm_wiki_cli/services/context_service.py)"]
    n9["_capture_protocol_enrichment_session (src/llm_wiki_cli/services/context_service.py)"]
    n10["_emit_protocol_error (src/llm_wiki_cli/services/context_service.py)"]
    n11["_normalise_protocol_filters (src/llm_wiki_cli/services/context_service.py)"]
    n12["_normalise_protocol_focus (src/llm_wiki_cli/services/context_service.py)"]
    n13["_protocol_error_payload (src/llm_wiki_cli/services/context_service.py)"]
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
    click n0 "../modules/context_service.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/context_packet.md"
    click n6 "../modules/context_packet.md"
    click n7 "../modules/context_service.md"
    click n8 "../modules/context_service.md"
    click n9 "../modules/context_service.md"
    click n10 "../modules/context_service.md"
    click n11 "../modules/context_service.md"
    click n12 "../modules/context_service.md"
    click n13 "../modules/context_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_service](../modules/context_service.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_build_protocol_enrichment_from_captured_read` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_captured_query_service` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_normalized_request` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_packet_contract_for_request` | call | [context_packet](../modules/context_packet.md) | 1 |
| `capture_context_read` | call | [context_packet](../modules/context_packet.md) | 7 |
| `_build_context` | call | [context_service](../modules/context_service.md) | 1 |
| `_build_context_impl` | call | [context_service](../modules/context_service.md) | 8 |
| `_capture_protocol_enrichment_session` | call | [context_service](../modules/context_service.md) | 4 |
| `_emit_protocol_error` | type_reference | [context_service](../modules/context_service.md) | — |
| `_normalise_protocol_filters` | call | [context_service](../modules/context_service.md) | 6 |
| `_normalise_protocol_focus` | call | [context_service](../modules/context_service.md) | 6 |
| `_protocol_error_payload` | type_reference | [context_service](../modules/context_service.md) | — |

> References: showing 12 of 19 logical references; 7 omitted by the 12-row generated summary limit.
