# compare_generated_ownership

**Entry point:** `compare_generated_ownership` (`api`)
**Source:** [integrity](../modules/integrity.md)
**Modules touched:** [integrity](../modules/integrity.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_generated_ownership
    participant p1 as capture_generated_ownership
    participant p2 as _generated_sections
    participant p3 as dict
    participant p4 as sorted (src/llm_wiki_cli/services…ompare_generated_ownership)
    participant p5 as set
    participant p6 as Path(…).expanduser().resolve
    participant p7 as Path(…).expanduser
    participant p8 as Path
    participant p9 as path.is_symlink
    participant p10 as DocumentationIntegrityError
    participant p11 as path.is_file
    participant p12 as hash_bytes
    participant p13 as path.read_bytes
    participant p14 as sorted (src/llm_wiki_cli/services…apture_generated_ownership)
    participant p15 as root.rglob
    participant p16 as path.relative_to(…).as_posix
    participant p17 as path.relative_to
    participant p18 as path.read_text
    participant p19 as section.encode
    p0->>p1: capture_generated_ownership
    p1->>p2: _generated_sections
    p0-->>p3: dict(baseline)
    p0-->>p4: sorted (src/llm_wiki_cli/services…ompare_generated_ownership)(...)
    p0-->>p5: set(current)
    p0-->>p5: set(before)
    p0-->>p4: sorted (src/llm_wiki_cli/services…ompare_generated_ownership)(...)
    p0-->>p5: set(before)
    p0-->>p5: set(current)
    p0-->>p4: sorted (src/llm_wiki_cli/services…ompare_generated_ownership)(...)
    p0-->>p5: set(before)
    p0-->>p5: set(current)
    p1-->>p6: Path(…).expanduser().resolve
    p1-->>p7: Path(…).expanduser
    p1-->>p8: Path(wiki_root)
    p1-->>p9: path.is_symlink
    p1-->>p10: DocumentationIntegrityError(...)
    p1-->>p11: path.is_file
    p1-->>p12: hash_bytes(path.read_bytes(...))
    p1-->>p13: path.read_bytes
    p1-->>p14: sorted (src/llm_wiki_cli/services…apture_generated_ownership)(root.rglob(...))
    p1-->>p15: root.rglob('*.md')
    p1-->>p9: path.is_symlink
    p1-->>p11: path.is_file
    p1-->>p10: DocumentationIntegrityError(...)
    p1-->>p16: path.relative_to(…).as_posix
    p1-->>p17: path.relative_to(root)
    p1-->>p18: path.read_text(encoding='utf-8')
    p1-->>p12: hash_bytes(section.encode(...))
    p1-->>p19: section.encode('utf-8')
```

> Call sequence diagram shows 30 of 43 interactions; 13 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 28 of 41 (13 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_run/integrity.py:_generated_sections` | 19 | - | unresolved | 13 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. compare_generated_ownership"]
    s2["2. capture_generated_ownership"]
    s3["3. Path(…).expanduser().resolve"]
    s4["4. Path(…).expanduser"]
    s5["5. Path"]
    s6["6. path.is_symlink"]
    s7["7. DocumentationIntegrityError"]
    s8["8. path.is_file"]
    s9["9. hash_bytes"]
    s10["10. path.read_bytes"]
    s11["11. sorted (src/llm_wiki_cli/services…apture_generated_ownership)"]
    s12["12. root.rglob"]
    s1 -->|"capture_generated_ownership(wiki_root)"| s2
    s2 -. "Path(…).expanduser().resolve(data not statically known)" .-> s3
    s2 -. "Path(…).expanduser(data not statically known)" .-> s4
    s2 -. "Path(wiki_root)" .-> s5
    s2 -. "path.is_symlink(data not statically known)" .-> s6
    s2 -. "DocumentationIntegrityError(...)" .-> s7
    s2 -. "path.is_file(data not statically known)" .-> s8
    s2 -. "hash_bytes(path.read_bytes(...))" .-> s9
    s2 -. "path.read_bytes(data not statically known)" .-> s10
    s2 -. "sorted (src/llm_wiki_cli/services…apture_generated_ownership)(root.rglob(...))" .-> s11
    s2 -. "root.rglob('*.md')" .-> s12
    b0["filesystem_read path.read_bytes"]
    s2 -. "filesystem_read path.read_bytes" .-> b0
    b1["filesystem_read path.read_text"]
    s2 -. "filesystem_read path.read_text" .-> b1
    click s1 "../modules/integrity.md"
    click s2 "../modules/integrity.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compare_generated_ownership` | `baseline: Mapping[str, str]`, `wiki_root: str \| Path` | - | - | `{...}` |
| `capture_generated_ownership` | `wiki_root: str \| Path` | - | `fingerprints[...]` | `fingerprints` |
| `Path(…).expanduser().resolve` | - | - | - | - |
| `Path(…).expanduser` | - | - | - | - |
| `Path` | - | - | - | - |
| `path.is_symlink` | - | - | - | - |
| `DocumentationIntegrityError` | - | - | - | - |
| `path.is_file` | - | - | - | - |
| `hash_bytes` | - | - | - | - |
| `path.read_bytes` | - | - | - | - |
| `sorted (src/llm_wiki_cli/services…apture_generated_ownership)` | - | - | - | - |
| `root.rglob` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compare_generated_ownership | capture_generated_ownership | 44 | `capture_generated_ownership(wiki_root)` |
| capture_generated_ownership | Path(…).expanduser().resolve | 13 | `Path(wiki_root).expanduser().resolve(data not statically known)` |
| capture_generated_ownership | Path(…).expanduser | 13 | `Path(wiki_root).expanduser(data not statically known)` |
| capture_generated_ownership | Path | 13 | `Path(wiki_root)` |
| capture_generated_ownership | path.is_symlink | 23 | `path.is_symlink(data not statically known)` |
| capture_generated_ownership | DocumentationIntegrityError | 24 | `DocumentationIntegrityError(...)` |
| capture_generated_ownership | path.is_file | 27 | `path.is_file(data not statically known)` |
| capture_generated_ownership | hash_bytes | 28 | `hash_bytes(path.read_bytes(...))` |
| capture_generated_ownership | path.read_bytes | 28 | `path.read_bytes(data not statically known)` |
| capture_generated_ownership | sorted (src/llm_wiki_cli/services…apture_generated_ownership) | 29 | `sorted(root.rglob(...))` |
| capture_generated_ownership | root.rglob | 29 | `root.rglob('*.md')` |

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
| unresolved_call | `capture_generated_ownership` | `DocumentationIntegrityError` | 24 |
| unresolved_call | `capture_generated_ownership` | `path.is_file` | 27 |
| unresolved_call | `capture_generated_ownership` | `sorted` | 29 |
| unresolved_call | `capture_generated_ownership` | `root.rglob` | 29 |
| step_limit | `compare_generated_ownership` | `first 12 steps` | 0 |

## Behavior

This flow starts at `compare_generated_ownership` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
