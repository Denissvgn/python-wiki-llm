# build_compact_task_context

**Entry point:** `build_compact_task_context` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [context_session](../modules/context_session.md), [task_compact_delivery](../modules/task_compact_delivery.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_compact_task_context (src/llm_wiki_cli/api.py)
    participant p1 as build_compact_task_context (src/llm_wiki_cli/services/task_compact_delivery.py)
    participant p2 as ContextSession
    participant p3 as session.read_compact
    p0->>p1: build_compact_task_context (src/llm_wiki_cli/services/task_compact_delivery.py)
    p1->>p2: ContextSession
    p1-->>p3: session.read_compact(request, view_options=view_options, reuse=False, cancelled=cancelled)
```

> Call sequence diagram shows 3 of 3 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 3; effect analysis evaluated: 0, partial: 2, unavailable: 1. Counts include steps omitted from the displayed trace.

Collector observations for 2 source steps with known totals: observed: 25, emitted: 18, omitted: 7. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `build_compact_task_context (src/llm_wiki_cli/api.py)` | `available` | `partial` | `available` | `13` | `9` | `4` |
| `build_compact_task_context (src/llm_wiki_cli/services/task_compact_delivery.py)` | `available` | `partial` | `available` | `12` | `9` | `3` |
| `ContextSession` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `session.read_compact` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. build_compact_task_context (src/llm_wiki_cli/api.py)"]
    s2["2. build_compact_task_context (src/llm_wiki_cli/services/task_compact_delivery.py)"]
    s3["3. ContextSession"]
    s4["4. session.read_compact"]
    s1 -->|"build_compact_task_context (src/llm_wiki_cli/services/task_compact_delivery.py)(…)"| s2
    s2 -->|"ContextSession(…)"| s3
    s2 -. "session.read_compact(request, view_options=view_options, reuse=False, cancelled=cancelled)" .-> s4
    click s1 "../modules/api.md"
    click s2 "../modules/task_compact_delivery.md"
    click s3 "../modules/context_session.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_compact_task_context (src/llm_wiki_cli/api.py)` | `request: Mapping[str, Any]`, `view_options: Mapping[str, Any] \| None`, `src_dir: str`, `wiki_dir: str`, `profile: WorkflowProfile \| Mapping[str, Any] \| None`, `policy: WorkflowPolicy \| None`, `counter: TokenCounter \| None`, `allow_external_src: bool` | - | - | `build(...)` |
| `build_compact_task_context (src/llm_wiki_cli/services/task_compact_delivery.py)` | `request`, `view_options`, `src_dir`, `wiki_dir`, `profile`, `policy`, `counter`, `allow_external_src` | - | - | `reply.view` |
| `ContextSession` | - | - | - | - |
| `session.read_compact` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_compact_task_context (src/llm_wiki_cli/api.py) | build_compact_task_context (src/llm_wiki_cli/services/task_compact_delivery.py) | 1443 | `build(request, view_options=view_options, src_dir=src_dir, wiki_dir=wiki_dir, profile=profile, policy=policy, counter=counter, allow_external_src=allow_external_src, source_selection=source_selection, helper_cache_dir=helper_cache_dir, cancelled=cancelled)` |
| build_compact_task_context (src/llm_wiki_cli/services/task_compact_delivery.py) | ContextSession | 18 | `ContextSession(src_dir=src_dir, wiki_dir=wiki_dir, profile=profile, policy=policy, counter=counter, allow_external_src=allow_external_src, source_selection=source_selection, helper_cache_dir=helper_cache_dir, max_entries=0, max_bytes=0)` |
| build_compact_task_context (src/llm_wiki_cli/services/task_compact_delivery.py) | session.read_compact | 22 | `session.read_compact(request, view_options=view_options, reuse=False, cancelled=cancelled)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_compact_task_context` | `session.read_compact` | 22 |

## Behavior

This flow starts at `build_compact_task_context` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
