# _PacketWireContract

**Location:** `src/llm_wiki_cli/services/context_packet.py:180`
**Kind:** Class
**Bases:** —
**Module:** [context_packet](../modules/context_packet.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One immutable schema/protocol/policy binding for canonical packets.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `schema_version` | `str` | *required* | — |
| `context_protocol` | `str` | *required* | — |
| `policy_version` | `str` | *required* | — |
| `packet_digest_domain` | `bytes` | *required* | — |
| `policy_digest_domain` | `str` | *required* | — |
| `max_packet_bytes` | `int` | *required* | — |
| `knowledge_mode_required` | `bool` | *required* | — |
| `knowledge_concept_limit` | `int \| None` | *required* | — |
| `knowledge_page_limit` | `int \| None` | *required* | — |
| `knowledge_relationship_limit` | `int \| None` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_PacketWireContract (src/llm_wiki_cli/services/context_packet.py)"]
    n1["_candidate_packet_size (src/llm_wiki_cli/services/context_packet.py)"]
    n2["_fit_knowledge_packet_response (src/llm_wiki_cli/services/context_packet.py)"]
    n3["_packet_basis (src/llm_wiki_cli/services/context_packet.py)"]
    n4["_packet_body (src/llm_wiki_cli/services/context_packet.py)"]
    n5["_packet_contract_for_request (src/llm_wiki_cli/services/context_packet.py)"]
    n6["_packet_contract_for_schema (src/llm_wiki_cli/services/context_packet.py)"]
    n7["_validate_basis (src/llm_wiki_cli/services/context_packet.py)"]
    n8["_validate_freshness_basis (src/llm_wiki_cli/services/context_packet.py)"]
    n9["_validate_knowledge_basis (src/llm_wiki_cli/services/context_packet.py)"]
    n10["_validate_packet_request (src/llm_wiki_cli/services/context_packet.py)"]
    n11["_validate_packet_shape (src/llm_wiki_cli/services/context_packet.py)"]
    n12["_validate_response (src/llm_wiki_cli/services/context_packet.py)"]
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
| [context_packet](../modules/context_packet.md) | 0 | `context_protocol`, `knowledge_concept_limit`, `knowledge_mode_required`, `knowledge_page_limit`, `knowledge_relationship_limit`, `max_packet_bytes`, `packet_digest_domain`, `policy_digest_domain`, `policy_version`, `schema_version` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_candidate_packet_size` | type_reference | [context_packet](../modules/context_packet.md) |
| `_fit_knowledge_packet_response` | type_reference | [context_packet](../modules/context_packet.md) |
| `_packet_basis` | type_reference | [context_packet](../modules/context_packet.md) |
| `_packet_body` | type_reference | [context_packet](../modules/context_packet.md) |
| `_packet_contract_for_request` | type_reference | [context_packet](../modules/context_packet.md) |
| `_packet_contract_for_schema` | type_reference | [context_packet](../modules/context_packet.md) |
| `_validate_basis` | type_reference | [context_packet](../modules/context_packet.md) |
| `_validate_freshness_basis` | type_reference | [context_packet](../modules/context_packet.md) |
| `_validate_knowledge_basis` | type_reference | [context_packet](../modules/context_packet.md) |
| `_validate_packet_request` | type_reference | [context_packet](../modules/context_packet.md) |
| `_validate_packet_shape` | type_reference | [context_packet](../modules/context_packet.md) |
| `_validate_response` | type_reference | [context_packet](../modules/context_packet.md) |
