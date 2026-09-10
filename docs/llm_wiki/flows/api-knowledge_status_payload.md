# knowledge_status_payload

**Entry point:** `knowledge_status_payload` (`api`)
**Source:** [knowledge_observability](../modules/knowledge_observability.md)
**Modules touched:** [knowledge_observability](../modules/knowledge_observability.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as knowledge_status_payload
    participant p1 as isinstance (src/llm_wiki_cli/services…y:knowledge_status_payload)
    participant p2 as TypeError (src/llm_wiki_cli/services…y:knowledge_status_payload)
    participant p3 as knowledge_freshness_disclosure
    participant p4 as isinstance (src/llm_wiki_cli/services…ledge_freshness_disclosure)
    participant p5 as TypeError (src/llm_wiki_cli/services…ledge_freshness_disclosure)
    participant p6 as _freshness_disclosure
    participant p7 as sum
    participant p8 as int
    participant p9 as view.freshness.counts.values
    p0-->>p1: isinstance (src/llm_wiki_cli/services…y:knowledge_status_payload)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…y:knowledge_status_payload)
    p0->>p3: knowledge_freshness_disclosure
    p3-->>p4: isinstance (src/llm_wiki_cli/services…ledge_freshness_disclosure)
    p3-->>p5: TypeError (src/llm_wiki_cli/services…ledge_freshness_disclosure)
    p3->>p6: _freshness_disclosure
    p3-->>p7: sum
    p3-->>p8: int
    p3-->>p9: view.freshness.counts.values
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. knowledge_status_payload"]
    s2["2. isinstance (src/llm_wiki_cli/services…y:knowledge_status_payload)"]
    s3["3. TypeError (src/llm_wiki_cli/services…y:knowledge_status_payload)"]
    s4["4. knowledge_freshness_disclosure"]
    s5["5. isinstance (src/llm_wiki_cli/services…ledge_freshness_disclosure)"]
    s6["6. TypeError (src/llm_wiki_cli/services…ledge_freshness_disclosure)"]
    s7["7. _freshness_disclosure"]
    s8["8. sum"]
    s9["9. int"]
    s10["10. view.freshness.counts.values"]
    s1 -. "isinstance (src/llm_wiki_cli/services…y:knowledge_status_payload)(view, KnowledgeReadView)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…y:knowledge_status_payload)('view must be a KnowledgeReadView or None')" .-> s3
    s1 -->|"knowledge_freshness_disclosure(view)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…ledge_freshness_disclosure)(view, KnowledgeReadView)" .-> s5
    s4 -. "TypeError (src/llm_wiki_cli/services…ledge_freshness_disclosure)('view must be a KnowledgeReadView')" .-> s6
    s4 -->|"_freshness_disclosure(evaluated=True, concepts_evaluated=sum(...))"| s7
    s4 -. "sum(...)" .-> s8
    s4 -. "int(count)" .-> s9
    s4 -. "view.freshness.counts.values(data not statically known)" .-> s10
    click s1 "../modules/knowledge_observability.md"
    click s4 "../modules/knowledge_observability.md"
    click s7 "../modules/knowledge_observability.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `knowledge_status_payload` | `view: KnowledgeReadView \| None` | `KnowledgeAvailability`, `KnowledgeReadReason`, `UNEVALUATED_FRESHNESS_DISCLOSURE`, `KnowledgeReadView` | - | `{...}`, `{...}` |
| `isinstance (src/llm_wiki_cli/services…y:knowledge_status_payload)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…y:knowledge_status_payload)` | - | - | - | - |
| `knowledge_freshness_disclosure` | `view: KnowledgeReadView` | `KnowledgeReadView`, `UNEVALUATED_FRESHNESS_DISCLOSURE` | - | `UNEVALUATED_FRESHNESS_DISCLOSURE`, `_freshness_disclosure(...)` |
| `isinstance (src/llm_wiki_cli/services…ledge_freshness_disclosure)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ledge_freshness_disclosure)` | - | - | - | - |
| `_freshness_disclosure` | `evaluated: bool`, `concepts_evaluated: int` | `UNEVALUATED_FRESHNESS_DISCLOSURE` | - | `UNEVALUATED_FRESHNESS_DISCLOSURE`, `...` |
| `sum` | - | - | - | - |
| `int` | - | - | - | - |
| `view.freshness.counts.values` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| knowledge_status_payload | isinstance (src/llm_wiki_cli/services…y:knowledge_status_payload) | 507 | `isinstance(view, KnowledgeReadView)` |
| knowledge_status_payload | TypeError (src/llm_wiki_cli/services…y:knowledge_status_payload) | 508 | `TypeError('view must be a KnowledgeReadView or None')` |
| knowledge_status_payload | knowledge_freshness_disclosure | 512 | `knowledge_freshness_disclosure(view)` |
| knowledge_freshness_disclosure | isinstance (src/llm_wiki_cli/services…ledge_freshness_disclosure) | 448 | `isinstance(view, KnowledgeReadView)` |
| knowledge_freshness_disclosure | TypeError (src/llm_wiki_cli/services…ledge_freshness_disclosure) | 449 | `TypeError('view must be a KnowledgeReadView')` |
| knowledge_freshness_disclosure | _freshness_disclosure | 453 | `_freshness_disclosure(evaluated=True, concepts_evaluated=sum(...))` |
| knowledge_freshness_disclosure | sum | 455 | `sum(...)` |
| knowledge_freshness_disclosure | int | 455 | `int(count)` |
| knowledge_freshness_disclosure | view.freshness.counts.values | 455 | `view.freshness.counts.values(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `knowledge_status_payload` | `isinstance` | 507 |
| external_call | `knowledge_status_payload` | `TypeError` | 508 |
| external_call | `knowledge_freshness_disclosure` | `isinstance` | 448 |
| external_call | `knowledge_freshness_disclosure` | `TypeError` | 449 |
| external_call | `knowledge_freshness_disclosure` | `sum` | 455 |
| unresolved_call | `knowledge_freshness_disclosure` | `view.freshness.counts.values` | 455 |

## Behavior

This flow starts at `knowledge_status_payload` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
