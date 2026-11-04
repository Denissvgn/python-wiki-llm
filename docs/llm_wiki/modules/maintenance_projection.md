# maintenance_projection Module

**Path:** `src/llm_wiki_cli/services/maintenance_projection.py`

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
    n1["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n2["src/llm_wiki_cli/services/knowledge_generation.py"]
    n3["src/llm_wiki_cli/services/knowledge_index.py"]
    n4["src/llm_wiki_cli/services/knowledge_model.py"]
    n5["src/llm_wiki_cli/services/knowledge_storage.py"]
    n6["src/llm_wiki_cli/services/knowledge_storage_access.py"]
    n7["src/llm_wiki_cli/services/knowledge_storage_lifecycle.py"]
    n8["src/llm_wiki_cli/services/maintenance_evidence.py"]
    n9["src/llm_wiki_cli/services/maintenance_projection.py"]
    n10["src/llm_wiki_cli/services/maintenance_service.py"]
    n11["src/llm_wiki_cli/services/maintenance_state.py"]
    n0 --> n1
    n0 --> n4
    n0 --> n5
    n0 --> n9
    n0 --> n11
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n9
    n1 --> n11
    n2 --> n1
    n2 --> n3
    n2 --> n4
    n2 --> n8
    n2 --> n9
    n3 --> n4
    n3 --> n9
    n3 --> n11
    n4 --> n9
    n5 --> n4
    n6 --> n1
    n6 --> n4
    n6 --> n5
    n6 --> n9
    n6 --> n11
    n7 --> n1
    n7 --> n3
    n7 --> n5
    n7 --> n9
    n7 --> n11
    n8 --> n5
    n8 --> n11
    n9 --> n5
    n9 --> n8
    n9 --> n11
    n10 --> n1
    n10 --> n5
    n10 --> n8
    n10 --> n9
    n10 --> n11
    n11 --> n5
    click n0 "../modules/documentation_wiki_input.md"
    click n1 "../modules/knowledge_artifacts.md"
    click n2 "../modules/knowledge_generation.md"
    click n3 "../modules/knowledge_index.md"
    click n4 "../modules/knowledge_model.md"
    click n5 "../modules/knowledge_storage.md"
    click n6 "../modules/knowledge_storage_access.md"
    click n7 "../modules/knowledge_storage_lifecycle.md"
    click n8 "../modules/maintenance_evidence.md"
    click n9 "../modules/maintenance_projection.md"
    click n10 "../modules/maintenance_service.md"
    click n11 "../modules/maintenance_state.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| Inbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Inbound | [knowledge_generation](../modules/knowledge_generation.md) |
| Inbound | [knowledge_index](../modules/knowledge_index.md) |
| Inbound | [knowledge_model](../modules/knowledge_model.md) |
| Inbound | [knowledge_storage_access](../modules/knowledge_storage_access.md) |
| Inbound | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) |
| Inbound | [maintenance_service](../modules/maintenance_service.md) |
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
