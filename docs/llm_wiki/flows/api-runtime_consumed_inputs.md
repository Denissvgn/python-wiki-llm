# runtime_consumed_inputs

**Entry point:** `runtime_consumed_inputs` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_generation](../modules/knowledge_generation.md), and 1 more

**Complete modules touched:**

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as runtime_consumed_inputs
    participant p1 as isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)
    participant p2 as TypeError
    participant p3 as source_snapshot.to_consumed_inputs
    participant p4 as _merge_explicit_consumed_input
    participant p5 as KnowledgeGenerationError
    participant p6 as is_valid_sha256
    participant p7 as isinstance (src/llm_wiki_cli/services…vidence.py:is_valid_sha256)
    participant p8 as _SHA256_RE.fullmatch
    participant p9 as isinstance (src/llm_wiki_cli/services…ge_explicit_consumed_input)
    participant p10 as consumed_by_path.get
    participant p11 as ConsumedInput
    participant p12 as generation_inputs.get
    participant p13 as tuple
    participant p14 as sorted
    participant p15 as openapi.get
    p0-->>p1: isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)
    p0-->>p2: TypeError
    p0-->>p1: isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)
    p0-->>p2: TypeError
    p0-->>p3: source_snapshot.to_consumed_inputs
    p0->>p4: _merge_explicit_consumed_input
    p4->>p5: KnowledgeGenerationError
    p4->>p5: KnowledgeGenerationError
    p4->>p6: is_valid_sha256
    p6-->>p7: isinstance (src/llm_wiki_cli/services…vidence.py:is_valid_sha256)
    p6-->>p8: _SHA256_RE.fullmatch
    p4->>p5: KnowledgeGenerationError
    p4-->>p9: isinstance (src/llm_wiki_cli/services…ge_explicit_consumed_input)
    p4-->>p10: consumed_by_path.get
    p4->>p5: KnowledgeGenerationError
    p4->>p11: ConsumedInput
    p0-->>p12: generation_inputs.get
    p0-->>p13: tuple
    p0-->>p14: sorted
    p0-->>p1: isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)
    p0->>p5: KnowledgeGenerationError
    p0-->>p15: openapi.get
    p0-->>p1: isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)
    p0->>p5: KnowledgeGenerationError
    p0-->>p15: openapi.get
    p0->>p6: is_valid_sha256
    p0->>p5: KnowledgeGenerationError
    p0-->>p1: isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)
    p0->>p4: _merge_explicit_consumed_input
    p0-->>p13: tuple
```

> Call sequence diagram shows 30 of 31 interactions; 1 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. runtime_consumed_inputs"]
    s2["2. isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)"]
    s3["3. TypeError"]
    s4["4. isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)"]
    s5["5. TypeError"]
    s6["6. source_snapshot.to_consumed_inputs"]
    s7["7. _merge_explicit_consumed_input"]
    s8["8. KnowledgeGenerationError"]
    s9["9. KnowledgeGenerationError"]
    s10["10. is_valid_sha256"]
    s11["11. isinstance (src/llm_wiki_cli/services…vidence.py:is_valid_sha256)"]
    s12["12. _SHA256_RE.fullmatch"]
    s1 -. "isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)(source_snapshot, SourceSnapshot)" .-> s2
    s1 -. "TypeError('source_snapshot must be a SourceSnapshot')" .-> s3
    s1 -. "isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)(generation_inputs, Mapping)" .-> s4
    s1 -. "TypeError('generation_inputs must be a mapping')" .-> s5
    s1 -. "source_snapshot.to_consumed_inputs(data not statically known)" .-> s6
    s1 -->|"_merge_explicit_consumed_input(consumed_by_path, path=plugin_lock_path, content_hash=plugin_lock_hash, kind=ConsumedInputKind.PLUGIN, field='plugin_lock')"| s7
    s7 -->|"KnowledgeGenerationError(field, 'path and content hash must be supplied together')"| s8
    s7 -->|"KnowledgeGenerationError(..., 'must be a non-empty repository-relative path')"| s9
    s7 -->|"is_valid_sha256(content_hash)"| s10
    s10 -. "isinstance (src/llm_wiki_cli/services…vidence.py:is_valid_sha256)(value, str)" .-> s11
    s10 -. "_SHA256_RE.fullmatch(value)" .-> s12
    click s1 "../modules/knowledge_orchestration.md"
    click s7 "../modules/knowledge_orchestration.md"
    click s8 "../modules/knowledge_generation.md"
    click s9 "../modules/knowledge_generation.md"
    click s10 "../modules/knowledge_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `runtime_consumed_inputs` | `source_snapshot: SourceSnapshot`, `generation_inputs: Mapping[str, object]`, `plugin_lock_path: str \| None`, `plugin_lock_hash: str \| None` | `SourceSnapshot`, `Mapping`, `ConsumedInputKind`, `Mapping`, `ConsumedInputKind` | - | `tuple(...)`, `tuple(...)` |
| `isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `source_snapshot.to_consumed_inputs` | - | - | - | - |
| `_merge_explicit_consumed_input` | `consumed_by_path: dict[str, ConsumedInput]`, `path: str \| None`, `content_hash: str \| None`, `kind: ConsumedInputKind`, `field: str` | - | `consumed_by_path[...]` | `none` |
| `KnowledgeGenerationError` | - | - | - | - |
| `KnowledgeGenerationError` | - | - | - | - |
| `is_valid_sha256` | `value: object` | - | - | `...` |
| `isinstance (src/llm_wiki_cli/services…vidence.py:is_valid_sha256)` | - | - | - | - |
| `_SHA256_RE.fullmatch` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| runtime_consumed_inputs | isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs) | 1396 | `isinstance(source_snapshot, SourceSnapshot)` |
| runtime_consumed_inputs | TypeError | 1397 | `TypeError('source_snapshot must be a SourceSnapshot')` |
| runtime_consumed_inputs | isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs) | 1398 | `isinstance(generation_inputs, Mapping)` |
| runtime_consumed_inputs | TypeError | 1399 | `TypeError('generation_inputs must be a mapping')` |
| runtime_consumed_inputs | source_snapshot.to_consumed_inputs | 1401 | `source_snapshot.to_consumed_inputs(data not statically known)` |
| runtime_consumed_inputs | _merge_explicit_consumed_input | 1403 | `_merge_explicit_consumed_input(consumed_by_path, path=plugin_lock_path, content_hash=plugin_lock_hash, kind=ConsumedInputKind.PLUGIN, field='plugin_lock')` |
| _merge_explicit_consumed_input | KnowledgeGenerationError | 1469 | `KnowledgeGenerationError(field, 'path and content hash must be supplied together')` |
| _merge_explicit_consumed_input | KnowledgeGenerationError | 1476 | `KnowledgeGenerationError(..., 'must be a non-empty repository-relative path')` |
| _merge_explicit_consumed_input | is_valid_sha256 | 1480 | `is_valid_sha256(content_hash)` |
| is_valid_sha256 | isinstance (src/llm_wiki_cli/services…vidence.py:is_valid_sha256) | 153 | `isinstance(value, str)` |
| is_valid_sha256 | _SHA256_RE.fullmatch | 153 | `_SHA256_RE.fullmatch(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `runtime_consumed_inputs` | `isinstance` | 1396 |
| external_call | `runtime_consumed_inputs` | `TypeError` | 1397 |
| external_call | `runtime_consumed_inputs` | `isinstance` | 1398 |
| external_call | `runtime_consumed_inputs` | `TypeError` | 1399 |
| unresolved_call | `runtime_consumed_inputs` | `source_snapshot.to_consumed_inputs` | 1401 |
| external_call | `is_valid_sha256` | `isinstance` | 153 |
| unresolved_call | `is_valid_sha256` | `_SHA256_RE.fullmatch` | 153 |
| step_limit | `runtime_consumed_inputs` | `first 12 steps` | 0 |

## Behavior

This flow starts at `runtime_consumed_inputs` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
