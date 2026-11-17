# extractor_registry Module

**Path:** `src/llm_wiki_cli/services/extractor_registry.py`

## Description

Code-documentation source tables: built-in extractors by language and
container build file patterns.

``llm_wiki_cli.config`` re-exports every name for existing callers.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/config.py"]
    n1["src/llm_wiki_cli/services/extraction_service.py"]
    n2["src/llm_wiki_cli/services/extractor_registry.py"]
    n3["src/llm_wiki_cli/services/helper_runtime.py"]
    n4["src/llm_wiki_cli/services/inventory_cache.py"]
    n5["src/llm_wiki_cli/services/knowledge_maintenance.py"]
    n6["src/llm_wiki_cli/services/source_snapshot.py"]
    n7["src/llm_wiki_cli/services/sync_analysis_cache.py"]
    n0 --> n2
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n6
    n3 --> n2
    n3 --> n6
    n4 --> n2
    n4 --> n6
    n5 --> n2
    n5 --> n6
    n6 --> n2
    n7 --> n1
    n7 --> n2
    n7 --> n4
    click n0 "../modules/config.md"
    click n1 "../modules/extraction_service.md"
    click n2 "../modules/extractor_registry.md"
    click n3 "../modules/helper_runtime.md"
    click n4 "../modules/inventory_cache.md"
    click n5 "../modules/knowledge_maintenance.md"
    click n6 "../modules/source_snapshot.md"
    click n7 "../modules/sync_analysis_cache.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [config](../modules/config.md) |
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Inbound | [helper_runtime](../modules/helper_runtime.md) |
| Inbound | [inventory_cache](../modules/inventory_cache.md) |
| Inbound | [knowledge_maintenance](../modules/knowledge_maintenance.md) |
| Inbound | [source_snapshot](../modules/source_snapshot.md) |
| Inbound | [sync_analysis_cache](../modules/sync_analysis_cache.md) |
