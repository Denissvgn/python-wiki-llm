# windows_object_identity

**Entry point:** `windows_object_identity` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as windows_object_identity
    participant p1 as windows_object_identity_from_values
    participant p2 as int (src/llm_wiki_cli/services…py:windows_object_identity)
    participant p3 as getattr
    participant p4 as WindowsIdentityUnavailableError
    participant p5 as WindowsObjectIdentity
    participant p6 as int (src/llm_wiki_cli/services…bject_identity_from_values)
    p0->>p1: windows_object_identity_from_values
    p0-->>p2: int (src/llm_wiki_cli/services…py:windows_object_identity)(getattr(...))
    p0-->>p3: getattr(result, 'st_dev', 0)
    p0-->>p2: int (src/llm_wiki_cli/services…py:windows_object_identity)(getattr(...))
    p0-->>p3: getattr(result, 'st_ino', 0)
    p1->>p4: WindowsIdentityUnavailableError
    p1->>p5: WindowsObjectIdentity
    p1-->>p6: int (src/llm_wiki_cli/services…bject_identity_from_values)(device)
```

> Call sequence diagram shows 8 of 8 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 5 (0 omitted); unresolved 0 of 0 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 4; effect analysis evaluated: 2, partial: 0, unavailable: 2. Counts include steps omitted from the displayed trace.

Collector observations for 2 source steps with known totals: observed: 7, emitted: 7, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `windows_object_identity` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `windows_object_identity_from_values` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `WindowsIdentityUnavailableError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `WindowsObjectIdentity` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `int (src/llm_wiki_cli/services…bject_identity_from_values)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `int (src/llm_wiki_cli/services…py:windows_object_identity)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `getattr` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `int (src/llm_wiki_cli/services…py:windows_object_identity)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `getattr` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. windows_object_identity"]
    s2["2. windows_object_identity_from_values"]
    s3["3. WindowsIdentityUnavailableError"]
    s4["4. WindowsObjectIdentity"]
    s5["5. int (src/llm_wiki_cli/services…bject_identity_from_values)"]
    s6["6. int (src/llm_wiki_cli/services…py:windows_object_identity)"]
    s7["7. getattr"]
    s8["8. int (src/llm_wiki_cli/services…py:windows_object_identity)"]
    s9["9. getattr"]
    s1 -->|"windows_object_identity_from_values(device=int(...), file_id=int(...), context=context)"| s2
    s2 -->|"WindowsIdentityUnavailableError(...)"| s3
    s2 -->|"WindowsObjectIdentity(device=int(...), file_id=file_id)"| s4
    s2 -. "int (src/llm_wiki_cli/services…bject_identity_from_values)(device)" .-> s5
    s1 -. "int (src/llm_wiki_cli/services…py:windows_object_identity)(getattr(...))" .-> s6
    s1 -. "getattr(result, 'st_dev', 0)" .-> s7
    s1 -. "int (src/llm_wiki_cli/services…py:windows_object_identity)(getattr(...))" .-> s8
    s1 -. "getattr(result, 'st_ino', 0)" .-> s9
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s3 "../modules/filesystem_guard.md"
    click s4 "../modules/filesystem_guard.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `windows_object_identity` | `result: os.stat_result`, `context: str` | - | - | `windows_object_identity_from_values(...)` |
| `windows_object_identity_from_values` | `device: int`, `file_id: int`, `context: str` | - | - | `WindowsObjectIdentity(...)` |
| `WindowsIdentityUnavailableError` | - | - | - | - |
| `WindowsObjectIdentity` | - | - | - | - |
| `int (src/llm_wiki_cli/services…bject_identity_from_values)` | - | - | - | - |
| `int (src/llm_wiki_cli/services…py:windows_object_identity)` | - | - | - | - |
| `getattr` | - | - | - | - |
| `int (src/llm_wiki_cli/services…py:windows_object_identity)` | - | - | - | - |
| `getattr` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| windows_object_identity | windows_object_identity_from_values | 108 | `windows_object_identity_from_values(device=int(...), file_id=int(...), context=context)` |
| windows_object_identity_from_values | WindowsIdentityUnavailableError | 124 | `WindowsIdentityUnavailableError(...)` |
| windows_object_identity_from_values | WindowsObjectIdentity | 127 | `WindowsObjectIdentity(device=int(...), file_id=file_id)` |
| windows_object_identity_from_values | int (src/llm_wiki_cli/services…bject_identity_from_values) | 128 | `int(device)` |
| windows_object_identity | int (src/llm_wiki_cli/services…py:windows_object_identity) | 109 | `int(getattr(...))` |
| windows_object_identity | getattr | 109 | `getattr(result, 'st_dev', 0)` |
| windows_object_identity | int (src/llm_wiki_cli/services…py:windows_object_identity) | 110 | `int(getattr(...))` |
| windows_object_identity | getattr | 110 | `getattr(result, 'st_ino', 0)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `windows_object_identity` | `getattr` | 109 |
| external_call | `windows_object_identity` | `getattr` | 110 |

## Behavior

This flow starts at `windows_object_identity` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
