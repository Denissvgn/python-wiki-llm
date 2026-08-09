# preserve_level_two_section_exact

**Entry point:** `preserve_level_two_section_exact` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as preserve_level_two_section_exact
    participant p1 as compile
    participant p2 as escape
    participant p3 as search
    participant p4 as group
    participant p5 as start
    participant p6 as (end)
    p0-->>p1: compile
    p0-->>p2: escape
    p0-->>p3: search
    p0-->>p3: search
    p0-->>p4: group
    p0-->>p4: group
    p0-->>p5: start
    p0-->>p6: (end)
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. preserve_level_two_section_exact"]
    s2["2. compile"]
    s3["3. escape"]
    s4["4. search"]
    s5["5. search"]
    s6["6. group"]
    s7["7. group"]
    s8["8. start"]
    s9["9. end"]
    s1 -. "re.compile(...)" .-> s2
    s1 -. "re.escape(heading)" .-> s3
    s1 -. "pattern.search(existing)" .-> s4
    s1 -. "pattern.search(generated)" .-> s5
    s1 -. "old_match.group(0)" .-> s6
    s1 -. "new_match.group(0)" .-> s7
    s1 -. "new_match.start(data not statically known)" .-> s8
    s1 -. "new_match.end(data not statically known)" .-> s9
    click s1 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `preserve_level_two_section_exact` | `existing: str`, `generated: str`, `heading: str` | - | - | `generated`, `generated`, `...` |
| `compile` | - | - | - | - |
| `escape` | - | - | - | - |
| `search` | - | - | - | - |
| `search` | - | - | - | - |
| `group` | - | - | - | - |
| `group` | - | - | - | - |
| `start` | - | - | - | - |
| `end` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| preserve_level_two_section_exact | compile | 720 | `re.compile(...)` |
| preserve_level_two_section_exact | escape | 721 | `re.escape(heading)` |
| preserve_level_two_section_exact | search | 724 | `pattern.search(existing)` |
| preserve_level_two_section_exact | search | 725 | `pattern.search(generated)` |
| preserve_level_two_section_exact | group | 728 | `old_match.group(0)` |
| preserve_level_two_section_exact | group | 729 | `new_match.group(0)` |
| preserve_level_two_section_exact | start | 732 | `new_match.start(data not statically known)` |
| preserve_level_two_section_exact | end | 734 | `new_match.end(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `preserve_level_two_section_exact` | `re.compile` | 720 |
| external_call | `preserve_level_two_section_exact` | `re.escape` | 721 |
| unresolved_call | `preserve_level_two_section_exact` | `pattern.search` | 724 |
| unresolved_call | `preserve_level_two_section_exact` | `pattern.search` | 725 |
| unresolved_call | `preserve_level_two_section_exact` | `old_match.group` | 728 |
| unresolved_call | `preserve_level_two_section_exact` | `new_match.group` | 729 |
| unresolved_call | `preserve_level_two_section_exact` | `new_match.start` | 732 |
| unresolved_call | `preserve_level_two_section_exact` | `new_match.end` | 734 |

## Behavior

This flow starts at `preserve_level_two_section_exact` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
