# is_unmodified_managed_workflow

**Entry point:** `is_unmodified_managed_workflow` (`api`)
**Source:** [ci_installer](../modules/ci_installer.md)
**Modules touched:** [ci_installer](../modules/ci_installer.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_unmodified_managed_workflow
    participant p1 as _normalize_newlines
    participant p2 as normalized.decode
    participant p3 as _MANAGED_HEADER_RE.match
    participant p4 as match.group
    participant p5 as schemas.get
    participant p6 as text[…].encode
    participant p7 as match.end
    participant p8 as hashlib.sha256(…).hexdigest
    participant p9 as hashlib.sha256
    participant p10 as hmac.compare_digest
    participant p11 as content.decode
    participant p12 as text.replace(…).replace(…).encode
    participant p13 as text.replace(…).replace
    participant p14 as text.replace
    p0->>p1: _normalize_newlines
    p0-->>p2: normalized.decode('utf-8')
    p0-->>p3: _MANAGED_HEADER_RE.match(text)
    p0-->>p4: match.group(1)
    p0-->>p5: schemas.get(workflow_path)
    p0-->>p6: text[…].encode('utf-8')
    p0-->>p7: match.end
    p0-->>p8: hashlib.sha256(…).hexdigest
    p0-->>p9: hashlib.sha256(body)
    p0-->>p10: hmac.compare_digest(match.group(...), actual)
    p0-->>p4: match.group(2)
    p1-->>p11: content.decode('utf-8')
    p1-->>p12: text.replace(…).replace(…).encode('utf-8')
    p1-->>p13: text.replace(…).replace('\r', '\n')
    p1-->>p14: text.replace('\r\n', '\n')
```

> Call sequence diagram shows 15 of 15 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 2 of 2 (0 omitted); unresolved 12 of 12 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 2; effect analysis evaluated: 2, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 2 source steps with known totals: observed: 13, emitted: 13, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. is_unmodified_managed_workflow"]
    s2["2. _normalize_newlines"]
    s3["3. content.decode"]
    s4["4. text.replace(…).replace(…).encode"]
    s5["5. text.replace(…).replace"]
    s6["6. text.replace"]
    s7["7. normalized.decode"]
    s8["8. _MANAGED_HEADER_RE.match"]
    s9["9. match.group"]
    s10["10. schemas.get"]
    s11["11. text[…].encode"]
    s12["12. match.end"]
    s1 -->|"_normalize_newlines(content)"| s2
    s2 -. "content.decode('utf-8')" .-> s3
    s2 -. "text.replace(…).replace(…).encode('utf-8')" .-> s4
    s2 -. "text.replace(…).replace('\r', '\n')" .-> s5
    s2 -. "text.replace('\r\n', '\n')" .-> s6
    s1 -. "normalized.decode('utf-8')" .-> s7
    s1 -. "_MANAGED_HEADER_RE.match(text)" .-> s8
    s1 -. "match.group(1)" .-> s9
    s1 -. "schemas.get(workflow_path)" .-> s10
    s1 -. "text[…].encode('utf-8')" .-> s11
    s1 -. "match.end(data not statically known)" .-> s12
    click s1 "../modules/ci_installer.md"
    click s2 "../modules/ci_installer.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_unmodified_managed_workflow` | `content: bytes`, `workflow_path: Path \| None` | `MANAGED_WORKFLOW_PATH`, `DOCUMENTATION_WORKFLOW_PATH`, `MANAGED_WORKFLOW_SCHEMA`, `DOCUMENTATION_WORKFLOW_SCHEMA` | - | `False`, `False`, `False`, `hmac.compare_digest(...)` |
| `_normalize_newlines` | `content: bytes` | - | - | `None`, `...` |
| `content.decode` | - | - | - | - |
| `text.replace(…).replace(…).encode` | - | - | - | - |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `normalized.decode` | - | - | - | - |
| `_MANAGED_HEADER_RE.match` | - | - | - | - |
| `match.group` | - | - | - | - |
| `schemas.get` | - | - | - | - |
| `text[…].encode` | - | - | - | - |
| `match.end` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_unmodified_managed_workflow | _normalize_newlines | 262 | `_normalize_newlines(content)` |
| _normalize_newlines | content.decode | 251 | `content.decode('utf-8')` |
| _normalize_newlines | text.replace(…).replace(…).encode | 254 | `text.replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')` |
| _normalize_newlines | text.replace(…).replace | 254 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| _normalize_newlines | text.replace | 254 | `text.replace('\r\n', '\n')` |
| is_unmodified_managed_workflow | normalized.decode | 265 | `normalized.decode('utf-8')` |
| is_unmodified_managed_workflow | _MANAGED_HEADER_RE.match | 266 | `_MANAGED_HEADER_RE.match(text)` |
| is_unmodified_managed_workflow | match.group | 274 | `match.group(1)` |
| is_unmodified_managed_workflow | schemas.get | 274 | `schemas.get(workflow_path)` |
| is_unmodified_managed_workflow | text[…].encode | 276 | `text[match.end():].encode('utf-8')` |
| is_unmodified_managed_workflow | match.end | 276 | `match.end(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalize_newlines` | `content.decode` | 251 |
| unresolved_call | `_normalize_newlines` | `text.replace('\r\n', '\n').replace('\r', '\n').encode` | 254 |
| unresolved_call | `_normalize_newlines` | `text.replace('\r\n', '\n').replace` | 254 |
| unresolved_call | `_normalize_newlines` | `text.replace` | 254 |
| unresolved_call | `is_unmodified_managed_workflow` | `normalized.decode` | 265 |
| unresolved_call | `is_unmodified_managed_workflow` | `_MANAGED_HEADER_RE.match` | 266 |
| unresolved_call | `is_unmodified_managed_workflow` | `match.group` | 274 |
| unresolved_call | `is_unmodified_managed_workflow` | `schemas.get` | 274 |
| unresolved_call | `is_unmodified_managed_workflow` | `text[match.end():].encode` | 276 |
| unresolved_call | `is_unmodified_managed_workflow` | `match.end` | 276 |
| step_limit | `is_unmodified_managed_workflow` | `first 12 steps` | 0 |

## Behavior

This flow starts at `is_unmodified_managed_workflow` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
