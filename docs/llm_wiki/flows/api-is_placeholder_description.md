# is_placeholder_description

**Entry point:** `is_placeholder_description` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_placeholder_description
    participant p1 as strip
    participant p2 as match
    p0-->>p1: strip
    p0-->>p2: match
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. is_placeholder_description"]
    s2["2. strip"]
    s3["3. match"]
    s1 -. "value.strip(data not statically known)" .-> s2
    s1 -. "_AUTO_GENERATED_RE.match(stripped)" .-> s3
    click s1 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_placeholder_description` | `value: str \| None` | - | - | `True`, `True`, `...` |
| `strip` | - | - | - | - |
| `match` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_placeholder_description | strip | 530 | `value.strip(data not statically known)` |
| is_placeholder_description | match | 533 | `_AUTO_GENERATED_RE.match(stripped)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `is_placeholder_description` | `value.strip` | 530 |
| unresolved_call | `is_placeholder_description` | `_AUTO_GENERATED_RE.match` | 533 |

## Behavior

This flow starts at `is_placeholder_description` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
