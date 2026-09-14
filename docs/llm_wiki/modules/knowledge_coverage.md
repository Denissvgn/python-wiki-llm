# knowledge_coverage Module

**Path:** `src/llm_wiki_cli/services/knowledge_coverage.py`

## Description

Bounded native coverage diagnostics, separate from frozen context payloads.

## Imports

| Source | Symbols |
|--------|---------|
| `.knowledge_consumption` | `KnowledgeReadView` |
| `.knowledge_freshness` | `KNOWN_FRESHNESS_REASON_CODES`, `structural_freshness_modeled` |
| `.knowledge_model` | `ComputedFreshness`, `ConceptKind` |
| `collections` | `Counter` |
| `collections.abc` | `Mapping` |
| `json` | `json` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n2["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n3["src/llm_wiki_cli/services/knowledge_coverage.py"]
    n4["src/llm_wiki_cli/services/knowledge_freshness.py"]
    n5["src/llm_wiki_cli/services/knowledge_model.py"]
    n6["src/llm_wiki_cli/services/native_inspection.py"]
    n0 --> n2
    n0 --> n3
    n0 --> n6
    n1 --> n0
    n1 --> n2
    n1 --> n3
    n1 --> n5
    n2 --> n4
    n2 --> n5
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n4 --> n5
    n6 --> n3
    click n0 "../modules/api.md"
    click n1 "../modules/knowledge_cmd.md"
    click n2 "../modules/knowledge_consumption.md"
    click n3 "../modules/knowledge_coverage.md"
    click n4 "../modules/knowledge_freshness.md"
    click n5 "../modules/knowledge_model.md"
    click n6 "../modules/native_inspection.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [knowledge_cmd](../modules/knowledge_cmd.md) |
| Inbound | [native_inspection](../modules/native_inspection.md) |
| Outbound | [knowledge_consumption](../modules/knowledge_consumption.md) |
| Outbound | [knowledge_freshness](../modules/knowledge_freshness.md) |
| Outbound | [knowledge_model](../modules/knowledge_model.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `build_knowledge_coverage` | `(view: KnowledgeReadView) -> dict[str, Any]` | — | Count eligibility before evidence outcomes; never publish input identities. |
| `render_knowledge_coverage` | `(payload: Mapping[str, Any]) -> str` | — | — |
