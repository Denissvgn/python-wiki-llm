# capture_generated_ownership

**Entry point:** `capture_generated_ownership` (`api`)
**Source:** [integrity](../modules/integrity.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [documentation_run_contracts](../modules/documentation_run_contracts.md), [integrity](../modules/integrity.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as capture_generated_ownership
    participant p1 as resolve
    participant p2 as expanduser
    participant p3 as Path
    participant p4 as is_symlink
    participant p5 as DocumentationIntegrityError
    participant p6 as is_file
    participant p7 as hash_bytes
    participant p8 as hexdigest
    participant p9 as sha256
    participant p10 as read_bytes
    participant p11 as sorted
    participant p12 as rglob
    participant p13 as as_posix
    participant p14 as relative_to
    participant p15 as read_text
    participant p16 as _generated_sections
    participant p17 as splitlines
    participant p18 as enumerate
    participant p19 as startswith
    participant p20 as append
    participant p21 as len
    participant p22 as join
    participant p23 as lower
    participant p24 as strip
    participant p25 as sub
    p0-->>p1: resolve
    p0-->>p2: expanduser
    p0-->>p3: Path
    p0-->>p4: is_symlink
    p0->>p5: DocumentationIntegrityError
    p0-->>p6: is_file
    p0->>p7: hash_bytes
    p7-->>p8: hexdigest
    p7-->>p9: sha256
    p0-->>p10: read_bytes
    p0-->>p11: sorted
    p0-->>p12: rglob
    p0-->>p4: is_symlink
    p0-->>p6: is_file
    p0->>p5: DocumentationIntegrityError
    p0-->>p13: as_posix
    p0-->>p14: relative_to
    p0-->>p15: read_text
    p0->>p16: _generated_sections
    p16-->>p17: splitlines
    p16-->>p18: enumerate
    p16-->>p19: startswith
    p16-->>p20: append
    p16-->>p21: len
    p16-->>p18: enumerate
    p16-->>p22: join
    p16-->>p23: lower
    p16-->>p24: strip
    p16-->>p24: strip
    p16-->>p25: sub
```

> Call sequence diagram shows 30 of 34 interactions; 4 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. capture_generated_ownership"]
    s2["2. resolve"]
    s3["3. expanduser"]
    s4["4. Path"]
    s5["5. is_symlink"]
    s6["6. DocumentationIntegrityError"]
    s7["7. is_file"]
    s8["8. hash_bytes"]
    s9["9. hexdigest"]
    s10["10. sha256"]
    s11["11. read_bytes"]
    s12["12. sorted"]
    s1 -. "Path(wiki_root).expanduser().resolve(data not statically known)" .-> s2
    s1 -. "Path(wiki_root).expanduser(data not statically known)" .-> s3
    s1 -. "Path(wiki_root)" .-> s4
    s1 -. "path.is_symlink(data not statically known)" .-> s5
    s1 -->|"DocumentationIntegrityError(...)"| s6
    s1 -. "path.is_file(data not statically known)" .-> s7
    s1 -->|"hash_bytes(path.read_bytes(...))"| s8
    s8 -. "hashlib.sha256(data).hexdigest(data not statically known)" .-> s9
    s8 -. "hashlib.sha256(data)" .-> s10
    s1 -. "path.read_bytes(data not statically known)" .-> s11
    s1 -. "sorted(root.rglob(...))" .-> s12
    b0["filesystem_read path.read_bytes"]
    s1 -. "filesystem_read path.read_bytes" .-> b0
    b1["filesystem_read path.read_text"]
    s1 -. "filesystem_read path.read_text" .-> b1
    click s1 "../modules/integrity.md"
    click s6 "../modules/documentation_run_contracts.md"
    click s8 "../modules/documentation_policy.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `capture_generated_ownership` | `wiki_root: str \| Path` | - | `fingerprints[...]` | `fingerprints` |
| `resolve` | - | - | - | - |
| `expanduser` | - | - | - | - |
| `Path` | - | - | - | - |
| `is_symlink` | - | - | - | - |
| `DocumentationIntegrityError` | - | - | - | - |
| `is_file` | - | - | - | - |
| `hash_bytes` | `data: bytes` | - | - | `...` |
| `hexdigest` | - | - | - | - |
| `sha256` | - | - | - | - |
| `read_bytes` | - | - | - | - |
| `sorted` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| capture_generated_ownership | resolve | 13 | `Path(wiki_root).expanduser().resolve(data not statically known)` |
| capture_generated_ownership | expanduser | 13 | `Path(wiki_root).expanduser(data not statically known)` |
| capture_generated_ownership | Path | 13 | `Path(wiki_root)` |
| capture_generated_ownership | is_symlink | 23 | `path.is_symlink(data not statically known)` |
| capture_generated_ownership | DocumentationIntegrityError | 24 | `DocumentationIntegrityError(...)` |
| capture_generated_ownership | is_file | 27 | `path.is_file(data not statically known)` |
| capture_generated_ownership | hash_bytes | 28 | `hash_bytes(path.read_bytes(...))` |
| hash_bytes | hexdigest | 520 | `hashlib.sha256(data).hexdigest(data not statically known)` |
| hash_bytes | sha256 | 520 | `hashlib.sha256(data)` |
| capture_generated_ownership | read_bytes | 28 | `path.read_bytes(data not statically known)` |
| capture_generated_ownership | sorted | 29 | `sorted(root.rglob(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `path.read_bytes` | `capture_generated_ownership` | 28 |
| filesystem_read | `path.read_text` | `capture_generated_ownership` | 35 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `capture_generated_ownership` | `Path(wiki_root).expanduser().resolve` | 13 |
| unresolved_call | `capture_generated_ownership` | `Path(wiki_root).expanduser` | 13 |
| unresolved_call | `capture_generated_ownership` | `path.is_symlink` | 23 |
| unresolved_call | `capture_generated_ownership` | `path.is_file` | 27 |
| external_call | `hash_bytes` | `hashlib.sha256(data).hexdigest` | 520 |
| external_call | `hash_bytes` | `hashlib.sha256` | 520 |
| unresolved_call | `capture_generated_ownership` | `sorted` | 29 |
| step_limit | `capture_generated_ownership` | `first 12 steps` | 0 |

## Behavior

This flow starts at `capture_generated_ownership` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
