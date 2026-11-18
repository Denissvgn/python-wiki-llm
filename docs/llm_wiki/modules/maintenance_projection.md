# maintenance_projection Module

**Path:** `src/llm_wiki_engine/maintenance_projection.py`

## Description

Bounded inspection projections of the separately owned maintenance ledger.

## Imports

| Source | Symbols |
|--------|---------|
| `.knowledge_storage` | `canonical_bytes` |
| `.maintenance_evidence` | `captured_semantic_sections` |
| `.maintenance_state` | `LIMITS`, `MaintenanceError`, `canonical_hash`, `maintenance_core`, `validate_maintenance_adoption`, `validate_maintenance_state`, `_identity` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `copy` | `deepcopy` |
| `dataclasses` | `replace` |
| `re` | `re` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n1["src/llm_wiki_cli/services/knowledge_generation.py"]
    n2["src/llm_wiki_cli/services/maintenance_service.py"]
    n3["src/llm_wiki_engine/knowledge_artifacts.py"]
    n4["src/llm_wiki_engine/knowledge_storage.py"]
    n5["src/llm_wiki_engine/knowledge_storage_access.py"]
    n6["src/llm_wiki_engine/knowledge_storage_lifecycle.py"]
    n7["src/llm_wiki_engine/knowledge_validators.py"]
    n8["src/llm_wiki_engine/maintenance_evidence.py"]
    n9["src/llm_wiki_engine/maintenance_projection.py"]
    n10["src/llm_wiki_engine/maintenance_state.py"]
    n0 --> n3
    n0 --> n4
    n0 --> n9
    n0 --> n10
    n1 --> n3
    n1 --> n8
    n1 --> n9
    n2 --> n3
    n2 --> n4
    n2 --> n8
    n2 --> n9
    n2 --> n10
    n3 --> n4
    n3 --> n9
    n3 --> n10
    n5 --> n3
    n5 --> n4
    n5 --> n9
    n5 --> n10
    n6 --> n3
    n6 --> n4
    n6 --> n9
    n6 --> n10
    n7 --> n9
    n8 --> n4
    n8 --> n10
    n9 --> n4
    n9 --> n8
    n9 --> n10
    n10 --> n4
    click n0 "../modules/documentation_wiki_input.md"
    click n1 "../modules/knowledge_generation.md"
    click n2 "../modules/maintenance_service.md"
    click n3 "../modules/knowledge_artifacts.md"
    click n4 "../modules/knowledge_storage.md"
    click n5 "../modules/knowledge_storage_access.md"
    click n6 "../modules/knowledge_storage_lifecycle.md"
    click n7 "../modules/knowledge_validators.md"
    click n8 "../modules/maintenance_evidence.md"
    click n9 "../modules/maintenance_projection.md"
    click n10 "../modules/maintenance_state.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| Inbound | [knowledge_generation](../modules/knowledge_generation.md) |
| Inbound | [maintenance_service](../modules/maintenance_service.md) |
| Inbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Inbound | [knowledge_storage_access](../modules/knowledge_storage_access.md) |
| Inbound | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) |
| Inbound | [knowledge_validators](../modules/knowledge_validators.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [maintenance_evidence](../modules/maintenance_evidence.md) |
| Outbound | [maintenance_state](../modules/maintenance_state.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_fields` | `(value, fields, label)` | — | — |
| `validate_maintenance_binding` | `(value) -> dict` | — | — |
| `_parts` | `(concept)` | — | — |
| `validate_maintenance_concept_projection` | `(concept, *, binding, state = None) -> dict` | — | — |
| `project_maintenance_knowledge` | `(knowledge, state, marker)` | — | Derive root/concept projections; history remains exclusively in the owner. |
| `validate_maintenance_projection` | `(knowledge, state = None, marker = None, *, complete = True, raw_content_by_page = None) -> None` | — | — |
| `validate_maintenance_prose` | `(state, knowledge, raw_content_by_page, *, selected_paths = None) -> None` | — | Validate supplied exact pages; unavailable prose makes no byte claim. |
