# PageTransitionPlan

**Location:** `src/llm_wiki_cli/services/sync_transitions.py:68`
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

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PageTransitionPlan (src/llm_wiki_cli/services/sync_transitions.py)"]
    n1["_governance_moves_for_sync (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n2["_plan_source_page_transitions (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n3["src/llm_wiki_cli/services/knowledge_generation.py"]
    n4["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n5["src/llm_wiki_cli/services/maintenance_evidence.py"]
    n6["plan_generated_source_repairs (src/llm_wiki_cli/services/sync_generated_sections.py)"]
    n7["PageTransitionExecution.__init__ (src/llm_wiki_cli/services/sync_transition_execution.py)"]
    n8["PageTransitionExecution.apply (src/llm_wiki_cli/services/sync_transition_execution.py)"]
    n9["plan_page_transitions (src/llm_wiki_cli/services/sync_transitions.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/sync_transitions.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/knowledge_generation.md"
    click n4 "../modules/knowledge_orchestration.md"
    click n5 "../modules/maintenance_evidence.md"
    click n6 "../modules/sync_generated_sections.md"
    click n7 "../modules/sync_transition_execution.md"
    click n8 "../modules/sync_transition_execution.md"
    click n9 "../modules/sync_transitions.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_transitions](../modules/sync_transitions.md) | 0 | `reserved_path_keys`, `retained_page_repairs`, `staged_moves`, `transitions` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_governance_moves_for_sync` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_plan_source_page_transitions` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `knowledge_orchestration` | import | [knowledge_orchestration](../modules/knowledge_orchestration.md) | — |
| `maintenance_evidence` | import | [maintenance_evidence](../modules/maintenance_evidence.md) | — |
| `plan_generated_source_repairs` | type_reference | [sync_generated_sections](../modules/sync_generated_sections.md) | — |
| `PageTransitionExecution.__init__` | type_reference | [sync_transition_execution](../modules/sync_transition_execution.md) | — |
| `PageTransitionExecution.apply` | type_reference | [sync_transition_execution](../modules/sync_transition_execution.md) | — |
| `plan_page_transitions` | call | [sync_transitions](../modules/sync_transitions.md) | 1 |
| `plan_page_transitions` | type_reference | [sync_transitions](../modules/sync_transitions.md) | — |
