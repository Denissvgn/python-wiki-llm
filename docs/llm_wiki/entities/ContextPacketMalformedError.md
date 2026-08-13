# ContextPacketMalformedError

**Location:** `src/llm_wiki_cli/services/context_packet.py:233`
**Kind:** Class
**Bases:** `ContextPacketError`
**Module:** [context_packet](../modules/context_packet.md)

## Description

The supplied bytes do not satisfy the canonical packet contract.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextPacketMalformedError (src/llm_wiki_cli/services/context_packet.py)"]
    n1["ContextPacketError (src/llm_wiki_cli/services/context_packet.py)"]
    n2["_coerce_packet_bytes (src/llm_wiki_cli/services/context_packet.py)"]
    n3["_encode_packet_payload (src/llm_wiki_cli/services/context_packet.py)"]
    n4["_exact_fields (src/llm_wiki_cli/services/context_packet.py)"]
    n5["_explicit_response_source_priorities (src/llm_wiki_cli/services/context_packet.py)"]
    n6["_mapping (src/llm_wiki_cli/services/context_packet.py)"]
    n7["_nonnegative_integer (src/llm_wiki_cli/services/context_packet.py)"]
    n8["_object_list (src/llm_wiki_cli/services/context_packet.py)"]
    n9["_packet_contract_for_schema (src/llm_wiki_cli/services/context_packet.py)"]
    n10["_stable_code (src/llm_wiki_cli/services/context_packet.py)"]
    n11["_strict_json_payload (src/llm_wiki_cli/services/context_packet.py)"]
    n12["_string_list (src/llm_wiki_cli/services/context_packet.py)"]
    n13["_validate_assurance (src/llm_wiki_cli/services/context_packet.py)"]
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
    click n13 "../modules/context_packet.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_packet](../modules/context_packet.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ContextPacketError` | [context_packet](../modules/context_packet.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_coerce_packet_bytes` | call | [context_packet](../modules/context_packet.md) | 4 |
| `_encode_packet_payload` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_exact_fields` | call | [context_packet](../modules/context_packet.md) | 2 |
| `_explicit_response_source_priorities` | call | [context_packet](../modules/context_packet.md) | 5 |
| `_mapping` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_nonnegative_integer` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_object_list` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_packet_contract_for_schema` | call | [context_packet](../modules/context_packet.md) | 2 |
| `_stable_code` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_strict_json_payload` | call | [context_packet](../modules/context_packet.md) | 3 |
| `_string_list` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_validate_assurance` | call | [context_packet](../modules/context_packet.md) | 2 |

> References: showing 12 of 40 logical references; 28 omitted by the 12-row generated summary limit.
