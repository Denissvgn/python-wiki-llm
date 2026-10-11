# PageTransitionError

**Location:** `src/llm_wiki_cli/services/sync_transitions.py:22`
**Kind:** Class
**Bases:** `SyncOwnershipError`
**Module:** [sync_transitions](../modules/sync_transitions.md)

## Description

The intended page writes cannot preserve verified ownership.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PageTransitionError (src/llm_wiki_cli/services/sync_transitions.py)"]
    n1["SyncOwnershipError (src/llm_wiki_cli/services/sync_analysis.py)"]
    n2["_preserve_cells (src/llm_wiki_cli/services/sync_generated_sections.py)"]
    n3["_source_markdown (src/llm_wiki_cli/services/sync_generated_sections.py)"]
    n4["plan_generated_source_repairs (src/llm_wiki_cli/services/sync_generated_sections.py)"]
    n5["repair_source_sections (src/llm_wiki_cli/services/sync_generated_sections.py)"]
    n6["assert_no_pending_page_moves (src/llm_wiki_cli/services/sync_transition_execution.py)"]
    n7["PageTransitionExecution.__exit__ (src/llm_wiki_cli/services/sync_transition_execution.py)"]
    n8["PageTransitionExecution._cleanup (src/llm_wiki_cli/services/sync_transition_execution.py)"]
    n9["PageTransitionExecution._expected (src/llm_wiki_cli/services/sync_transition_execution.py)"]
    n10["PageTransitionExecution._verified_recovery_manifest (src/llm_wiki_cli/services/sync_transition_execution.py)"]
    n11["PageTransitionExecution.apply (src/llm_wiki_cli/services/sync_transition_execution.py)"]
    n12["PageTransitionExecution.read_text (src/llm_wiki_cli/services/sync_transition_execution.py)"]
    n13["PageTransitionExecution.write (src/llm_wiki_cli/services/sync_transition_execution.py)"]
    n0 --> n1
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
    n13 --> n0
    click n0 "../modules/sync_transitions.md"
    click n1 "../modules/sync_analysis.md"
    click n2 "../modules/sync_generated_sections.md"
    click n3 "../modules/sync_generated_sections.md"
    click n4 "../modules/sync_generated_sections.md"
    click n5 "../modules/sync_generated_sections.md"
    click n6 "../modules/sync_transition_execution.md"
    click n7 "../modules/sync_transition_execution.md"
    click n8 "../modules/sync_transition_execution.md"
    click n9 "../modules/sync_transition_execution.md"
    click n10 "../modules/sync_transition_execution.md"
    click n11 "../modules/sync_transition_execution.md"
    click n12 "../modules/sync_transition_execution.md"
    click n13 "../modules/sync_transition_execution.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_transitions](../modules/sync_transitions.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `SyncOwnershipError` | [sync_analysis](../modules/sync_analysis.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_preserve_cells` | call | [sync_generated_sections](../modules/sync_generated_sections.md) | 2 |
| `_source_markdown` | call | [sync_generated_sections](../modules/sync_generated_sections.md) | 1 |
| `plan_generated_source_repairs` | call | [sync_generated_sections](../modules/sync_generated_sections.md) | 1 |
| `repair_source_sections` | call | [sync_generated_sections](../modules/sync_generated_sections.md) | 3 |
| `assert_no_pending_page_moves` | call | [sync_transition_execution](../modules/sync_transition_execution.md) | 1 |
| `PageTransitionExecution.__exit__` | call | [sync_transition_execution](../modules/sync_transition_execution.md) | 1 |
| `PageTransitionExecution._cleanup` | call | [sync_transition_execution](../modules/sync_transition_execution.md) | 1 |
| `PageTransitionExecution._expected` | call | [sync_transition_execution](../modules/sync_transition_execution.md) | 1 |
| `PageTransitionExecution._verified_recovery_manifest` | call | [sync_transition_execution](../modules/sync_transition_execution.md) | 2 |
| `PageTransitionExecution.apply` | call | [sync_transition_execution](../modules/sync_transition_execution.md) | 3 |
| `PageTransitionExecution.read_text` | call | [sync_transition_execution](../modules/sync_transition_execution.md) | 3 |
| `PageTransitionExecution.write` | call | [sync_transition_execution](../modules/sync_transition_execution.md) | 1 |

> References: showing 12 of 20 logical references; 8 omitted by the 12-row generated summary limit.
