# is_unmodified_managed_workflow

**Entry point:** `is_unmodified_managed_workflow` (`api`)
**Source:** [ci_installer](../modules/ci_installer.md)
**Modules touched:** [ci_installer](../modules/ci_installer.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_unmodified_managed_workflow
    participant p1 as _normalize_newlines
    participant p2 as content.decode
    participant p3 as text.replace(…).replace(…).encode
    participant p4 as text.replace(…).replace
    participant p5 as text.replace
    participant p6 as normalized.decode
    participant p7 as _MANAGED_HEADER_RE.match
    participant p8 as text[…].encode
    participant p9 as match.end
    participant p10 as hashlib.sha256(…).hexdigest
    participant p11 as hashlib.sha256
    participant p12 as hmac.compare_digest
    participant p13 as match.group
    p0->>p1: _normalize_newlines
    p1-->>p2: content.decode
    p1-->>p3: text.replace(…).replace(…).encode
    p1-->>p4: text.replace(…).replace
    p1-->>p5: text.replace
    p0-->>p6: normalized.decode
    p0-->>p7: _MANAGED_HEADER_RE.match
    p0-->>p8: text[…].encode
    p0-->>p9: match.end
    p0-->>p10: hashlib.sha256(…).hexdigest
    p0-->>p11: hashlib.sha256
    p0-->>p12: hmac.compare_digest
    p0-->>p13: match.group
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
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
    s9["9. text[…].encode"]
    s10["10. match.end"]
    s11["11. hashlib.sha256(…).hexdigest"]
    s12["12. hashlib.sha256"]
    s1 -->|"_normalize_newlines(content)"| s2
    s2 -. "content.decode('utf-8')" .-> s3
    s2 -. "text.replace(…).replace(…).encode('utf-8')" .-> s4
    s2 -. "text.replace(…).replace('\r', '\n')" .-> s5
    s2 -. "text.replace('\r\n', '\n')" .-> s6
    s1 -. "normalized.decode('utf-8')" .-> s7
    s1 -. "_MANAGED_HEADER_RE.match(text)" .-> s8
    s1 -. "text[…].encode('utf-8')" .-> s9
    s1 -. "match.end(data not statically known)" .-> s10
    s1 -. "hashlib.sha256(…).hexdigest(data not statically known)" .-> s11
    s1 -. "hashlib.sha256(body)" .-> s12
    click s1 "../modules/ci_installer.md"
    click s2 "../modules/ci_installer.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_unmodified_managed_workflow` | `content: bytes` | - | - | `False`, `False`, `hmac.compare_digest(...)` |
| `_normalize_newlines` | `content: bytes` | - | - | `None`, `...` |
| `content.decode` | - | - | - | - |
| `text.replace(…).replace(…).encode` | - | - | - | - |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `normalized.decode` | - | - | - | - |
| `_MANAGED_HEADER_RE.match` | - | - | - | - |
| `text[…].encode` | - | - | - | - |
| `match.end` | - | - | - | - |
| `hashlib.sha256(…).hexdigest` | - | - | - | - |
| `hashlib.sha256` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_unmodified_managed_workflow | _normalize_newlines | 240 | `_normalize_newlines(content)` |
| _normalize_newlines | content.decode | 231 | `content.decode('utf-8')` |
| _normalize_newlines | text.replace(…).replace(…).encode | 234 | `text.replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')` |
| _normalize_newlines | text.replace(…).replace | 234 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| _normalize_newlines | text.replace | 234 | `text.replace('\r\n', '\n')` |
| is_unmodified_managed_workflow | normalized.decode | 243 | `normalized.decode('utf-8')` |
| is_unmodified_managed_workflow | _MANAGED_HEADER_RE.match | 244 | `_MANAGED_HEADER_RE.match(text)` |
| is_unmodified_managed_workflow | text[…].encode | 247 | `text[match.end():].encode('utf-8')` |
| is_unmodified_managed_workflow | match.end | 247 | `match.end(data not statically known)` |
| is_unmodified_managed_workflow | hashlib.sha256(…).hexdigest | 248 | `hashlib.sha256(body).hexdigest(data not statically known)` |
| is_unmodified_managed_workflow | hashlib.sha256 | 248 | `hashlib.sha256(body)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalize_newlines` | `content.decode` | 231 |
| unresolved_call | `_normalize_newlines` | `text.replace('\r\n', '\n').replace('\r', '\n').encode` | 234 |
| unresolved_call | `_normalize_newlines` | `text.replace('\r\n', '\n').replace` | 234 |
| unresolved_call | `_normalize_newlines` | `text.replace` | 234 |
| unresolved_call | `is_unmodified_managed_workflow` | `normalized.decode` | 243 |
| unresolved_call | `is_unmodified_managed_workflow` | `_MANAGED_HEADER_RE.match` | 244 |
| unresolved_call | `is_unmodified_managed_workflow` | `text[match.end():].encode` | 247 |
| unresolved_call | `is_unmodified_managed_workflow` | `match.end` | 247 |
| unresolved_call | `is_unmodified_managed_workflow` | `hashlib.sha256(body).hexdigest` | 248 |
| external_call | `is_unmodified_managed_workflow` | `hashlib.sha256` | 248 |
| step_limit | `is_unmodified_managed_workflow` | `first 12 steps` | 0 |

## Behavior

This flow starts at `is_unmodified_managed_workflow` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
