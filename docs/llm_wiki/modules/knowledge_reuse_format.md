# knowledge_reuse_format Module

**Path:** `src/llm_wiki_engine/knowledge_reuse_format.py`

## Description

Knowledge reuse commitments: their format and their binding to artifacts.

A sync may reuse a committed knowledge projection only when the manifest and
the knowledge bundle carry the same versioned commitment to every input.

## Imports

| Source | Symbols |
|--------|---------|
| `.knowledge_envelope` | `INVENTORY_HASH_EXTENSION` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `dataclasses` | `asdict`, `replace` |
| `llm_wiki_engine.contracts` | `KNOWLEDGE_REUSE_SCHEMA_VERSION` |
| `llm_wiki_engine.knowledge_evidence` | `hash_json`, `is_valid_sha256` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n1["src/llm_wiki_cli/services/knowledge_reuse.py"]
    n2["src/llm_wiki_engine/contracts.py"]
    n3["src/llm_wiki_engine/knowledge_artifacts.py"]
    n4["src/llm_wiki_engine/knowledge_envelope.py"]
    n5["src/llm_wiki_engine/knowledge_evidence.py"]
    n6["src/llm_wiki_engine/knowledge_model.py"]
    n7["src/llm_wiki_engine/knowledge_reuse_format.py"]
    n8["src/llm_wiki_engine/sync_manifest.py"]
    n0 --> n2
    n0 --> n3
    n0 --> n4
    n0 --> n5
    n0 --> n6
    n0 --> n7
    n0 --> n8
    n1 --> n0
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n7
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n3 --> n7
    n3 --> n8
    n4 --> n2
    n4 --> n5
    n4 --> n6
    n6 --> n2
    n6 --> n5
    n6 --> n7
    n7 --> n2
    n7 --> n4
    n7 --> n5
    n8 --> n5
    n8 --> n7
    click n0 "../modules/knowledge_orchestration.md"
    click n1 "../modules/knowledge_reuse.md"
    click n2 "../modules/llm_wiki_engine_contracts.md"
    click n3 "../modules/knowledge_artifacts.md"
    click n4 "../modules/knowledge_envelope.md"
    click n5 "../modules/knowledge_evidence.md"
    click n6 "../modules/knowledge_model.md"
    click n7 "../modules/knowledge_reuse_format.md"
    click n8 "../modules/sync_manifest.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| Inbound | [knowledge_reuse](../modules/knowledge_reuse.md) |
| Inbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Inbound | [knowledge_model](../modules/knowledge_model.md) |
| Inbound | [sync_manifest](../modules/sync_manifest.md) |
| Outbound | [llm_wiki_engine_contracts](../modules/llm_wiki_engine_contracts.md) |
| Outbound | [knowledge_envelope](../modules/knowledge_envelope.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `validate_reuse_commitment` | `(value: object) -> dict` | — | — |
| `manifest_lifecycle_hash` | `(manifest) -> str` | — | — |
| `repository_input_hash` | `(record) -> str` | — | — |
| `validate_reuse_artifact_parity` | `(knowledge, manifest) -> None` | — | A manifest hint alone never authorizes reuse of a projection. |
