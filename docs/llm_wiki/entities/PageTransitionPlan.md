# PageTransitionPlan

**Location:** `src/llm_wiki_cli/services/sync_transitions.py:65`
**Kind:** Class
**Bases:** —
**Module:** [sync_transitions](../modules/sync_transitions.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `PageTransitionPlan` in `src/llm_wiki_cli/services/sync_transitions.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `transitions` | `tuple[PageTransition, ...]` | *required* | — |
| `staged_moves` | `tuple[StagedPageMove, ...]` | *required* | — |
| `reserved_path_keys` | `tuple[str, ...]` | *required* | — |
| `retained_page_repairs` | `tuple[RetainedPageRepair, ...]` | `()` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PageTransitionPlan (src/llm_wiki_cli/services/sync_transitions.py)"]
    n1["src/llm_wiki_cli/services/knowledge_generation.py"]
    n2["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n3["plan_generated_source_repairs (src/llm_wiki_cli/services/sync_generated_sections.py)"]
    n4["_governance_moves_for_sync (src/llm_wiki_cli/services/sync_runtime.py)"]
    n5["_plan_source_page_transitions (src/llm_wiki_cli/services/sync_runtime.py)"]
    n6["plan_page_transitions (src/llm_wiki_cli/services/sync_transitions.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/sync_transitions.md"
    click n1 "../modules/knowledge_generation.md"
    click n2 "../modules/knowledge_orchestration.md"
    click n3 "../modules/sync_generated_sections.md"
    click n4 "../modules/sync_runtime.md"
    click n5 "../modules/sync_runtime.md"
    click n6 "../modules/sync_transitions.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_transitions](../modules/sync_transitions.md) | 0 | `reserved_path_keys`, `retained_page_repairs`, `staged_moves`, `transitions` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `knowledge_orchestration` | import | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `plan_generated_source_repairs` | type_reference | [sync_generated_sections](../modules/sync_generated_sections.md) | — |
| `_governance_moves_for_sync` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_plan_source_page_transitions` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `plan_page_transitions` | call | [sync_transitions](../modules/sync_transitions.md) | 1 |
| `plan_page_transitions` | type_reference | [sync_transitions](../modules/sync_transitions.md) | — |
