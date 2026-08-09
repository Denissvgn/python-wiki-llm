# consumed_inputs_from_captured_hashes

**Entry point:** `consumed_inputs_from_captured_hashes` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as consumed_inputs_from_captured_hashes
    participant p1 as isinstance
    participant p2 as KnowledgeEnvelopeError
    participant p3 as any
    participant p4 as set
    participant p5 as _repository_relative_path
    participant p6 as require_repository_relative_path
    participant p7 as strip
    participant p8 as ord
    participant p9 as startswith
    participant p10 as match
    participant p11 as split
    participant p12 as PurePosixPath
    participant p13 as normpath
    participant p14 as require_portable_relative_path
    participant p15 as _default_path_error
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p3: any
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p3: any
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p4: set
    p0-->>p4: set
    p0->>p2: KnowledgeEnvelopeError
    p0->>p5: _repository_relative_path
    p5->>p6: require_repository_relative_path
    p6-->>p1: isinstance
    p6-->>p7: strip
    p6-->>p3: any
    p6-->>p8: ord
    p6-->>p8: ord
    p6-->>p9: startswith
    p6-->>p9: startswith
    p6-->>p10: match
    p6-->>p11: split
    p6-->>p12: PurePosixPath
    p6-->>p3: any
    p6-->>p13: normpath
    p6->>p14: require_portable_relative_path
    p14-->>p1: isinstance
    p14->>p15: _default_path_error
```

> Call sequence diagram shows 30 of 94 interactions; 64 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. consumed_inputs_from_captured_hashes"]
    s2["2. isinstance"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. isinstance"]
    s5["5. KnowledgeEnvelopeError"]
    s6["6. any"]
    s7["7. isinstance"]
    s8["8. KnowledgeEnvelopeError"]
    s9["9. any"]
    s10["10. isinstance"]
    s11["11. KnowledgeEnvelopeError"]
    s12["12. set"]
    s1 -. "isinstance(content_hashes, Mapping)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('captured_content_hashes', 'must be an object')"| s3
    s1 -. "isinstance(candidate_kinds, Mapping)" .-> s4
    s1 -->|"KnowledgeEnvelopeError('captured_input_kinds', 'must be an object')"| s5
    s1 -. "any(...)" .-> s6
    s1 -. "isinstance(path, str)" .-> s7
    s1 -->|"KnowledgeEnvelopeError('captured_content_hashes', 'must use string repository paths')"| s8
    s1 -. "any(...)" .-> s9
    s1 -. "isinstance(path, str)" .-> s10
    s1 -->|"KnowledgeEnvelopeError('captured_input_kinds', 'must use string repository paths')"| s11
    s1 -. "set(content_hashes)" .-> s12
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s5 "../modules/knowledge_envelope.md"
    click s8 "../modules/knowledge_envelope.md"
    click s11 "../modules/knowledge_envelope.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `consumed_inputs_from_captured_hashes` | `content_hashes: Mapping[str, str]`, `candidate_kinds: Mapping[str, ConsumedInputKind \| str \| Iterable[ConsumedInputKind \| str]]` | `Mapping`, `Mapping` | - | `tuple(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `any` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `any` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `set` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| consumed_inputs_from_captured_hashes | isinstance | 179 | `isinstance(content_hashes, Mapping)` |
| consumed_inputs_from_captured_hashes | KnowledgeEnvelopeError | 180 | `KnowledgeEnvelopeError('captured_content_hashes', 'must be an object')` |
| consumed_inputs_from_captured_hashes | isinstance | 181 | `isinstance(candidate_kinds, Mapping)` |
| consumed_inputs_from_captured_hashes | KnowledgeEnvelopeError | 182 | `KnowledgeEnvelopeError('captured_input_kinds', 'must be an object')` |
| consumed_inputs_from_captured_hashes | any | 183 | `any(...)` |
| consumed_inputs_from_captured_hashes | isinstance | 183 | `isinstance(path, str)` |
| consumed_inputs_from_captured_hashes | KnowledgeEnvelopeError | 184 | `KnowledgeEnvelopeError('captured_content_hashes', 'must use string repository paths')` |
| consumed_inputs_from_captured_hashes | any | 188 | `any(...)` |
| consumed_inputs_from_captured_hashes | isinstance | 188 | `isinstance(path, str)` |
| consumed_inputs_from_captured_hashes | KnowledgeEnvelopeError | 189 | `KnowledgeEnvelopeError('captured_input_kinds', 'must use string repository paths')` |
| consumed_inputs_from_captured_hashes | set | 193 | `set(content_hashes)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `consumed_inputs_from_captured_hashes` | `isinstance` | 179 |
| unresolved_call | `consumed_inputs_from_captured_hashes` | `isinstance` | 181 |
| unresolved_call | `consumed_inputs_from_captured_hashes` | `any` | 183 |
| unresolved_call | `consumed_inputs_from_captured_hashes` | `isinstance` | 183 |
| unresolved_call | `consumed_inputs_from_captured_hashes` | `any` | 188 |
| unresolved_call | `consumed_inputs_from_captured_hashes` | `isinstance` | 188 |
| step_limit | `consumed_inputs_from_captured_hashes` | `first 12 steps` | 0 |

## Behavior

This flow starts at `consumed_inputs_from_captured_hashes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
