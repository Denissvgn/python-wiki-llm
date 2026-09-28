# analysis_capture Module

**Path:** `src/llm_wiki_cli/services/analysis_capture.py`

## Description

Operation-owned capture of installed analysis implementation and runtimes.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `analysis_compatibility`, `extractor_helpers` |
| `.immutable` | `FrozenDict`, `freeze` |
| `.knowledge_envelope` | `hash_component_configuration` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `contextvars` | `ContextVar` |
| `dataclasses` | `replace` |
| `functools` | `wraps` |
| `hashlib` | `hashlib` |
| `importlib.metadata` | `version` |
| `json` | `json` |
| `pathlib` | `Path` |
| `platform` | `platform` |
| `re` | `re` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/analysis_capture.py"]
    n1["src/llm_wiki_cli/services/analysis_compatibility.py"]
    n2["src/llm_wiki_cli/services/extraction_service.py"]
    n3["src/llm_wiki_cli/services/extractor_helpers.py"]
    n4["src/llm_wiki_cli/services/immutable.py"]
    n5["src/llm_wiki_cli/services/inventory_cache.py"]
    n6["src/llm_wiki_cli/services/knowledge_envelope.py"]
    n7["src/llm_wiki_cli/services/knowledge_maintenance.py"]
    n8["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n0 --> n1
    n0 --> n3
    n0 --> n4
    n0 --> n6
    n2 --> n0
    n2 --> n5
    n3 --> n5
    n5 --> n0
    n5 --> n1
    n7 --> n0
    n7 --> n1
    n7 --> n3
    n7 --> n6
    n7 --> n8
    n8 --> n0
    n8 --> n1
    n8 --> n4
    n8 --> n6
    click n0 "../modules/analysis_capture.md"
    click n1 "../modules/analysis_compatibility.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/extractor_helpers.md"
    click n4 "../modules/immutable.md"
    click n5 "../modules/inventory_cache.md"
    click n6 "../modules/knowledge_envelope.md"
    click n7 "../modules/knowledge_maintenance.md"
    click n8 "../modules/knowledge_orchestration.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Inbound | [inventory_cache](../modules/inventory_cache.md) |
| Inbound | [knowledge_maintenance](../modules/knowledge_maintenance.md) |
| Inbound | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| Outbound | [analysis_compatibility](../modules/analysis_compatibility.md) |
| Outbound | [extractor_helpers](../modules/extractor_helpers.md) |
| Outbound | [immutable](../modules/immutable.md) |
| Outbound | [knowledge_envelope](../modules/knowledge_envelope.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [_CapturedAnalysis](../entities/CapturedAnalysis.md) | 21 | `FrozenDict` | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_issued` | `(values)` | — | — |
| `capture_operation` | `(function)` | — | — |
| `registry` | `(root: Path \| None = None) -> dict` | — | — |
| `implementation_hash` | `(root: Path, paths: list[str]) -> str` | — | — |
| `capture_analysis` | `(registry_entries: Mapping[str, str], *, helper_cache_dir = None, source_root: str \| Path = '.', languages = None, package_root: Path \| None = None) -> dict` | — | Capture immutable JSON inputs once; unavailable providers stay unknown. |
| `attach` | `(component, captured: Mapping \| None)` | — | — |
