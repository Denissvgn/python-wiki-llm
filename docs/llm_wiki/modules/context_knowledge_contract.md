# context_knowledge_contract Module

**Path:** `src/llm_wiki_engine/context_knowledge_contract.py`

## Description

Frozen compatibility and failure contracts for context knowledge selection.

The current v2 descriptor distinguishes plain compatibility context responses
from qualified packets, which default to v2 with automatic native knowledge.
An explicitly requested v1 descriptor retains its original canonical contents.
Both versions enforce the same complete safety and recovery matrices; unknown
descriptor versions fail instead of being interpreted as a supported version.

The lifecycle and evidence matrices are data rather than prose.  Consumers can
validate a serialized copy before using it as implementation or release
evidence.  Nothing in this module reads, writes, initializes, or repairs a
knowledge projection or a managed reference.

## Imports

| Source | Symbols |
|--------|---------|
| `.contracts` | `CONTEXT_KNOWLEDGE_PROTOCOL_VERSION`, `CONTEXT_PROTOCOL_VERSION`, `QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION`, `QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping`, `Sequence` |
| `copy` | `deepcopy` |
| `json` | `json` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/services/context_service.py"]
    n2["src/llm_wiki_cli/services/mcp_server.py"]
    n3["src/llm_wiki_engine/context_knowledge_contract.py"]
    n4["src/llm_wiki_engine/context_request_format.py"]
    n5["src/llm_wiki_engine/context_response_format.py"]
    n6["src/llm_wiki_engine/contracts.py"]
    n0 --> n1
    n0 --> n3
    n0 --> n6
    n1 --> n3
    n1 --> n4
    n1 --> n6
    n2 --> n0
    n2 --> n1
    n2 --> n3
    n3 --> n6
    n4 --> n3
    n4 --> n6
    n5 --> n3
    n5 --> n4
    n5 --> n6
    click n0 "../modules/api.md"
    click n1 "../modules/context_service.md"
    click n2 "../modules/mcp_server.md"
    click n3 "../modules/context_knowledge_contract.md"
    click n4 "../modules/context_request_format.md"
    click n5 "../modules/context_response_format.md"
    click n6 "../modules/llm_wiki_engine_contracts.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [context_service](../modules/context_service.md) |
| Inbound | [mcp_server](../modules/mcp_server.md) |
| Inbound | [context_request_format](../modules/context_request_format.md) |
| Inbound | [context_response_format](../modules/context_response_format.md) |
| Outbound | [llm_wiki_engine_contracts](../modules/llm_wiki_engine_contracts.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [ContextKnowledgeContractError](../entities/ContextKnowledgeContractError.md) | 1393 | `ValueError` | A serialized context-knowledge contract violates the frozen shape. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_signal` | `(level: str, code: str \| None) -> dict[str, str \| None]` | — | — |
| `_wire_mapping` | `(*, availability: str, reason: str, auto_status: str, required_status: str, basis_state: str, basis_availability: str, basis_reason: str) -> dict[str, Any]` | — | — |
| `_combined_signals` | `(lifecycle: Mapping[str, Any], evidence: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]` | — | — |
| `_combined_recovery_routes` | `(lifecycle: Mapping[str, Any], evidence: Mapping[str, Any]) -> list[dict[str, Any]]` | — | — |
| `_contract_snapshot` | `(schema_version) -> tuple[dict[str, Any], str]` | — | — |
| `_matrix_by_state` | `(value: object, *, field: str, expected_states: Sequence[str], required_fields: frozenset[str]) -> dict[str, Mapping[str, Any]]` | — | — |
| `_validate_context_knowledge_contract` | `(contract: Mapping[str, Any]) -> None` | — | Validate completeness and the fail-safe cross-row invariants. |
| `validate_context_knowledge_contract` | `(contract: Mapping[str, Any]) -> None` | — | Reject every non-canonical candidate with the declared error type. |
| `context_knowledge_contract` | `(*, schema_version: str \| None = None) -> dict[str, Any]` | — | Return current defaults, or an explicitly selected frozen legacy descriptor. |
