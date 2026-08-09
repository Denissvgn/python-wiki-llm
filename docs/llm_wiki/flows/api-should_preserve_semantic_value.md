# should_preserve_semantic_value

**Entry point:** `should_preserve_semantic_value` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as should_preserve_semantic_value
    participant p1 as is_placeholder_description
    participant p2 as strip
    participant p3 as match
    p0->>p1: is_placeholder_description
    p1-->>p2: strip
    p1-->>p3: match
    p0-->>p2: strip
    p0-->>p2: strip
    p0-->>p2: strip
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. should_preserve_semantic_value"]
    s2["2. is_placeholder_description"]
    s3["3. strip"]
    s4["4. match"]
    s5["5. strip"]
    s6["6. strip"]
    s7["7. strip"]
    s1 -->|"is_placeholder_description(existing)"| s2
    s2 -. "value.strip(data not statically known)" .-> s3
    s2 -. "_AUTO_GENERATED_RE.match(stripped)" .-> s4
    s1 -. "(existing or '').strip(data not statically known)" .-> s5
    s1 -. "(generated or '').strip(data not statically known)" .-> s6
    s1 -. "old_generated.strip(data not statically known)" .-> s7
    click s1 "../modules/markdown_sections.md"
    click s2 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `should_preserve_semantic_value` | `existing: str \| None`, `generated: str \| None`, `old_generated: str \| None` | - | - | `False`, `...`, `False`, `...` |
| `is_placeholder_description` | `value: str \| None` | - | - | `True`, `True`, `...` |
| `strip` | - | - | - | - |
| `match` | - | - | - | - |
| `strip` | - | - | - | - |
| `strip` | - | - | - | - |
| `strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| should_preserve_semantic_value | is_placeholder_description | 543 | `is_placeholder_description(existing)` |
| is_placeholder_description | strip | 530 | `value.strip(data not statically known)` |
| is_placeholder_description | match | 533 | `_AUTO_GENERATED_RE.match(stripped)` |
| should_preserve_semantic_value | strip | 545 | `(existing or '').strip(data not statically known)` |
| should_preserve_semantic_value | strip | 546 | `(generated or '').strip(data not statically known)` |
| should_preserve_semantic_value | strip | 549 | `old_generated.strip(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `is_placeholder_description` | `value.strip` | 530 |
| unresolved_call | `is_placeholder_description` | `_AUTO_GENERATED_RE.match` | 533 |
| unresolved_call | `should_preserve_semantic_value` | `(existing or '').strip` | 545 |
| unresolved_call | `should_preserve_semantic_value` | `(generated or '').strip` | 546 |
| unresolved_call | `should_preserve_semantic_value` | `old_generated.strip` | 549 |

## Behavior

This flow starts at `should_preserve_semantic_value` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
