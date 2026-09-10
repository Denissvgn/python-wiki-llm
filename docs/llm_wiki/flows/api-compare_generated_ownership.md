# compare_generated_ownership

**Entry point:** `compare_generated_ownership` (`api`)
**Source:** [integrity](../modules/integrity.md)
**Modules touched:** [integrity](../modules/integrity.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_generated_ownership
    participant p1 as capture_generated_ownership
    participant p2 as Path(…).expanduser().resolve
    participant p3 as Path(…).expanduser
    participant p4 as Path
    participant p5 as path.is_symlink
    participant p6 as DocumentationIntegrityError
    participant p7 as path.is_file
    participant p8 as hash_bytes
    participant p9 as path.read_bytes
    participant p10 as sorted (src/llm_wiki_cli/services…apture_generated_ownership)
    participant p11 as root.rglob
    participant p12 as path.relative_to(…).as_posix
    participant p13 as path.relative_to
    participant p14 as path.read_text
    participant p15 as _generated_sections
    participant p16 as text.splitlines
    participant p17 as enumerate
    participant p18 as line.startswith
    participant p19 as starts.append
    participant p20 as len
    participant p21 as ''.join
    participant p22 as lines[…][…].strip().lower
    participant p23 as lines[…][…].strip
    participant p24 as re.sub(…).strip
    participant p25 as re.sub
    participant p26 as str
    p0->>p1: capture_generated_ownership
    p1-->>p2: Path(…).expanduser().resolve
    p1-->>p3: Path(…).expanduser
    p1-->>p4: Path
    p1-->>p5: path.is_symlink
    p1-->>p6: DocumentationIntegrityError
    p1-->>p7: path.is_file
    p1-->>p8: hash_bytes
    p1-->>p9: path.read_bytes
    p1-->>p10: sorted (src/llm_wiki_cli/services…apture_generated_ownership)
    p1-->>p11: root.rglob
    p1-->>p5: path.is_symlink
    p1-->>p7: path.is_file
    p1-->>p6: DocumentationIntegrityError
    p1-->>p12: path.relative_to(…).as_posix
    p1-->>p13: path.relative_to
    p1-->>p14: path.read_text
    p1->>p15: _generated_sections
    p15-->>p16: text.splitlines
    p15-->>p17: enumerate
    p15-->>p18: line.startswith
    p15-->>p19: starts.append
    p15-->>p20: len
    p15-->>p17: enumerate
    p15-->>p21: ''.join
    p15-->>p22: lines[…][…].strip().lower
    p15-->>p23: lines[…][…].strip
    p15-->>p24: re.sub(…).strip
    p15-->>p25: re.sub
    p15-->>p26: str
```

> Call sequence diagram shows 30 of 43 interactions; 13 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

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
