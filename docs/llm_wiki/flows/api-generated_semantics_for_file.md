# generated_semantics_for_file

**Entry point:** `generated_semantics_for_file` (`api`)
**Source:** [sync_manifest](../modules/sync_manifest.md)
**Modules touched:** [sync_manifest](../modules/sync_manifest.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as generated_semantics_for_file
    participant p1 as file_data.get
    participant p2 as _first_doc_line
    participant p3 as cls.get
    participant p4 as attr.get
    participant p5 as Counter
    participant p6 as duplicate_semantics.setdefault(…).append
    participant p7 as duplicate_semantics.setdefault
    participant p8 as info.get
    participant p9 as docstring.split
    p0-->>p1: file_data.get('module_docstring', '')
    p0->>p2: _first_doc_line
    p0-->>p1: file_data.get('classes', [...])
    p0->>p2: _first_doc_line
    p0-->>p1: file_data.get('functions', [...])
    p0-->>p3: cls.get('docstring', '')
    p0-->>p4: attr.get('description')
    p0-->>p3: cls.get('attributes', [...])
    p0->>p2: _first_doc_line
    p0-->>p3: cls.get('methods', [...])
    p0-->>p1: file_data.get('classes', [...])
    p0-->>p5: Counter(...)
    p0-->>p1: file_data.get('classes', [...])
    p0-->>p1: file_data.get('classes', [...])
    p0->>p0: generated_semantics_for_file
    p0-->>p6: duplicate_semantics.setdefault(…).append(...)
    p0-->>p7: duplicate_semantics.setdefault(name, [...])
    p2-->>p8: info.get('docstring', '')
    p2-->>p9: docstring.split('\n')
```

> Call sequence diagram shows 19 of 19 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1 (0 omitted); unresolved 14 of 14 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 5; effect analysis evaluated: 5, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. generated_semantics_for_file"]
    s2["2. file_data.get"]
    s3["3. _first_doc_line"]
    s4["4. info.get"]
    s5["5. docstring.split"]
    s6["6. file_data.get"]
    s7["7. _first_doc_line"]
    s8["8. file_data.get"]
    s9["9. cls.get"]
    s10["10. attr.get"]
    s11["11. cls.get"]
    s12["12. _first_doc_line"]
    s1 -. "file_data.get('module_docstring', '')" .-> s2
    s1 -->|"_first_doc_line(cls)"| s3
    s3 -. "info.get('docstring', '')" .-> s4
    s3 -. "docstring.split('\n')" .-> s5
    s1 -. "file_data.get('classes', [...])" .-> s6
    s1 -->|"_first_doc_line(fn)"| s7
    s1 -. "file_data.get('functions', [...])" .-> s8
    s1 -. "cls.get('docstring', '')" .-> s9
    s1 -. "attr.get('description')" .-> s10
    s1 -. "cls.get('attributes', [...])" .-> s11
    s1 -->|"_first_doc_line(method)"| s12
    click s1 "../modules/sync_manifest.md"
    click s3 "../modules/sync_manifest.md"
    click s7 "../modules/sync_manifest.md"
    click s12 "../modules/sync_manifest.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `generated_semantics_for_file` | `filepath: str`, `file_data: Mapping[str, Any]` | - | `result[...]` | `result` |
| `file_data.get` | - | - | - | - |
| `_first_doc_line` | `info: Mapping[str, Any]` | - | - | `...` |
| `info.get` | - | - | - | - |
| `docstring.split` | - | - | - | - |
| `file_data.get` | - | - | - | - |
| `_first_doc_line` | `info: Mapping[str, Any]` | - | - | `...` |
| `file_data.get` | - | - | - | - |
| `cls.get` | - | - | - | - |
| `attr.get` | - | - | - | - |
| `cls.get` | - | - | - | - |
| `_first_doc_line` | `info: Mapping[str, Any]` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| generated_semantics_for_file | file_data.get | 683 | `file_data.get('module_docstring', '')` |
| generated_semantics_for_file | _first_doc_line | 689 | `_first_doc_line(cls)` |
| _first_doc_line | info.get | 529 | `info.get('docstring', '')` |
| _first_doc_line | docstring.split | 530 | `docstring.split('\n')` |
| generated_semantics_for_file | file_data.get | 690 | `file_data.get('classes', [...])` |
| generated_semantics_for_file | _first_doc_line | 693 | `_first_doc_line(fn)` |
| generated_semantics_for_file | file_data.get | 693 | `file_data.get('functions', [...])` |
| generated_semantics_for_file | cls.get | 698 | `cls.get('docstring', '')` |
| generated_semantics_for_file | attr.get | 701 | `attr.get('description')` |
| generated_semantics_for_file | cls.get | 702 | `cls.get('attributes', [...])` |
| generated_semantics_for_file | _first_doc_line | 705 | `_first_doc_line(method)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `generated_semantics_for_file` | `file_data.get` | 683 |
| unresolved_call | `_first_doc_line` | `info.get` | 529 |
| unresolved_call | `_first_doc_line` | `docstring.split` | 530 |
| unresolved_call | `generated_semantics_for_file` | `file_data.get` | 690 |
| unresolved_call | `generated_semantics_for_file` | `file_data.get` | 693 |
| unresolved_call | `generated_semantics_for_file` | `cls.get` | 698 |
| unresolved_call | `generated_semantics_for_file` | `attr.get` | 701 |
| unresolved_call | `generated_semantics_for_file` | `cls.get` | 702 |
| step_limit | `generated_semantics_for_file` | `first 12 steps` | 0 |

## Behavior

This flow starts at `generated_semantics_for_file` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
