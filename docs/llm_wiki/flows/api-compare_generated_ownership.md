# compare_generated_ownership

**Entry point:** `compare_generated_ownership` (`api`)
**Source:** [integrity](../modules/integrity.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [documentation_run_contracts](../modules/documentation_run_contracts.md), [integrity](../modules/integrity.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_generated_ownership
    participant p1 as capture_generated_ownership
    participant p2 as resolve
    participant p3 as expanduser
    participant p4 as Path
    participant p5 as is_symlink
    participant p6 as DocumentationIntegrityError
    participant p7 as is_file
    participant p8 as hash_bytes
    participant p9 as hexdigest
    participant p10 as sha256
    participant p11 as read_bytes
    participant p12 as sorted
    participant p13 as rglob
    participant p14 as as_posix
    participant p15 as relative_to
    participant p16 as read_text
    participant p17 as _generated_sections
    participant p18 as splitlines
    participant p19 as enumerate
    participant p20 as startswith
    participant p21 as append
    participant p22 as len
    participant p23 as join
    participant p24 as lower
    participant p25 as strip
    p0->>p1: capture_generated_ownership
    p1-->>p2: resolve
    p1-->>p3: expanduser
    p1-->>p4: Path
    p1-->>p5: is_symlink
    p1->>p6: DocumentationIntegrityError
    p1-->>p7: is_file
    p1->>p8: hash_bytes
    p8-->>p9: hexdigest
    p8-->>p10: sha256
    p1-->>p11: read_bytes
    p1-->>p12: sorted
    p1-->>p13: rglob
    p1-->>p5: is_symlink
    p1-->>p7: is_file
    p1->>p6: DocumentationIntegrityError
    p1-->>p14: as_posix
    p1-->>p15: relative_to
    p1-->>p16: read_text
    p1->>p17: _generated_sections
    p17-->>p18: splitlines
    p17-->>p19: enumerate
    p17-->>p20: startswith
    p17-->>p21: append
    p17-->>p22: len
    p17-->>p19: enumerate
    p17-->>p23: join
    p17-->>p24: lower
    p17-->>p25: strip
    p17-->>p25: strip
```

> Call sequence diagram shows 30 of 45 interactions; 15 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. compare_generated_ownership"]
    s2["2. capture_generated_ownership"]
    s3["3. resolve"]
    s4["4. expanduser"]
    s5["5. Path"]
    s6["6. is_symlink"]
    s7["7. DocumentationIntegrityError"]
    s8["8. is_file"]
    s9["9. hash_bytes"]
    s10["10. hexdigest"]
    s11["11. sha256"]
    s12["12. read_bytes"]
    s1 -->|"capture_generated_ownership(wiki_root)"| s2
    s2 -. "Path(wiki_root).expanduser().resolve(data not statically known)" .-> s3
    s2 -. "Path(wiki_root).expanduser(data not statically known)" .-> s4
    s2 -. "Path(wiki_root)" .-> s5
    s2 -. "path.is_symlink(data not statically known)" .-> s6
    s2 -->|"DocumentationIntegrityError(...)"| s7
    s2 -. "path.is_file(data not statically known)" .-> s8
    s2 -->|"hash_bytes(path.read_bytes(...))"| s9
    s9 -. "hashlib.sha256(data).hexdigest(data not statically known)" .-> s10
    s9 -. "hashlib.sha256(data)" .-> s11
    s2 -. "path.read_bytes(data not statically known)" .-> s12
    b0["filesystem_read path.read_bytes"]
    s2 -. "filesystem_read path.read_bytes" .-> b0
    b1["filesystem_read path.read_text"]
    s2 -. "filesystem_read path.read_text" .-> b1
    click s1 "../modules/integrity.md"
    click s2 "../modules/integrity.md"
    click s7 "../modules/documentation_run_contracts.md"
    click s9 "../modules/documentation_policy.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compare_generated_ownership` | `baseline: Mapping[str, str]`, `wiki_root: str \| Path` | - | - | `{...}` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compare_generated_ownership | capture_generated_ownership | 44 | `capture_generated_ownership(wiki_root)` |
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
| step_limit | `compare_generated_ownership` | `first 12 steps` | 0 |

## Behavior

This flow starts at `compare_generated_ownership` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
