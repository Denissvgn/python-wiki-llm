# capture_generated_ownership

**Entry point:** `capture_generated_ownership` (`api`)
**Source:** [integrity](../modules/integrity.md)
**Modules touched:** [integrity](../modules/integrity.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as capture_generated_ownership
    participant p1 as Path(…).expanduser().resolve
    participant p2 as Path(…).expanduser
    participant p3 as Path
    participant p4 as path.is_symlink
    participant p5 as DocumentationIntegrityError
    participant p6 as path.is_file
    participant p7 as hash_bytes
    participant p8 as path.read_bytes
    participant p9 as sorted
    participant p10 as root.rglob
    participant p11 as path.relative_to(…).as_posix
    participant p12 as path.relative_to
    participant p13 as path.read_text
    participant p14 as _generated_sections
    participant p15 as section.encode
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
    p0-->>p1: Path(…).expanduser().resolve
    p0-->>p2: Path(…).expanduser
    p0-->>p3: Path(wiki_root)
    p0-->>p4: path.is_symlink
    p0-->>p5: DocumentationIntegrityError(...)
    p0-->>p6: path.is_file
    p0-->>p7: hash_bytes(path.read_bytes(...))
    p0-->>p8: path.read_bytes
    p0-->>p9: sorted(root.rglob(...))
    p0-->>p10: root.rglob('*.md')
    p0-->>p4: path.is_symlink
    p0-->>p6: path.is_file
    p0-->>p5: DocumentationIntegrityError(...)
    p0-->>p11: path.relative_to(…).as_posix
    p0-->>p12: path.relative_to(root)
    p0-->>p13: path.read_text(encoding='utf-8')
    p0->>p14: _generated_sections
    p0-->>p7: hash_bytes(section.encode(...))
    p0-->>p15: section.encode('utf-8')
    p14-->>p16: text.splitlines(keepends=True)
    p14-->>p17: enumerate(lines)
    p14-->>p18: line.startswith(' ')
    p14-->>p19: starts.append(len(...))
    p14-->>p20: len(lines)
    p14-->>p17: enumerate(...)
    p14-->>p21: ''.join(...)
    p14-->>p22: lines[…][…].strip().lower
    p14-->>p23: lines[…][…].strip
    p14-->>p24: re.sub(…).strip('-')
    p14-->>p25: re.sub('[^a-z0-9]+', '-', heading)
```

> Call sequence diagram shows 30 of 32 interactions; 2 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 29 of 31 (2 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_run/integrity.py:_generated_sections` | 18 | - | unresolved | 2 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. capture_generated_ownership"]
    s2["2. Path(…).expanduser().resolve"]
    s3["3. Path(…).expanduser"]
    s4["4. Path"]
    s5["5. path.is_symlink"]
    s6["6. DocumentationIntegrityError"]
    s7["7. path.is_file"]
    s8["8. hash_bytes"]
    s9["9. path.read_bytes"]
    s10["10. sorted"]
    s11["11. root.rglob"]
    s12["12. path.is_symlink"]
    s1 -. "Path(…).expanduser().resolve(data not statically known)" .-> s2
    s1 -. "Path(…).expanduser(data not statically known)" .-> s3
    s1 -. "Path(wiki_root)" .-> s4
    s1 -. "path.is_symlink(data not statically known)" .-> s5
    s1 -. "DocumentationIntegrityError(...)" .-> s6
    s1 -. "path.is_file(data not statically known)" .-> s7
    s1 -. "hash_bytes(path.read_bytes(...))" .-> s8
    s1 -. "path.read_bytes(data not statically known)" .-> s9
    s1 -. "sorted(root.rglob(...))" .-> s10
    s1 -. "root.rglob('*.md')" .-> s11
    s1 -. "path.is_symlink(data not statically known)" .-> s12
    b0["filesystem_read path.read_bytes"]
    s1 -. "filesystem_read path.read_bytes" .-> b0
    b1["filesystem_read path.read_text"]
    s1 -. "filesystem_read path.read_text" .-> b1
    click s1 "../modules/integrity.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `capture_generated_ownership` | `wiki_root: str \| Path` | - | `fingerprints[...]` | `fingerprints` |
| `Path(…).expanduser().resolve` | - | - | - | - |
| `Path(…).expanduser` | - | - | - | - |
| `Path` | - | - | - | - |
| `path.is_symlink` | - | - | - | - |
| `DocumentationIntegrityError` | - | - | - | - |
| `path.is_file` | - | - | - | - |
| `hash_bytes` | - | - | - | - |
| `path.read_bytes` | - | - | - | - |
| `sorted` | - | - | - | - |
| `root.rglob` | - | - | - | - |
| `path.is_symlink` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| capture_generated_ownership | Path(…).expanduser().resolve | 13 | `Path(wiki_root).expanduser().resolve(data not statically known)` |
| capture_generated_ownership | Path(…).expanduser | 13 | `Path(wiki_root).expanduser(data not statically known)` |
| capture_generated_ownership | Path | 13 | `Path(wiki_root)` |
| capture_generated_ownership | path.is_symlink | 23 | `path.is_symlink(data not statically known)` |
| capture_generated_ownership | DocumentationIntegrityError | 24 | `DocumentationIntegrityError(...)` |
| capture_generated_ownership | path.is_file | 27 | `path.is_file(data not statically known)` |
| capture_generated_ownership | hash_bytes | 28 | `hash_bytes(path.read_bytes(...))` |
| capture_generated_ownership | path.read_bytes | 28 | `path.read_bytes(data not statically known)` |
| capture_generated_ownership | sorted | 29 | `sorted(root.rglob(...))` |
| capture_generated_ownership | root.rglob | 29 | `root.rglob('*.md')` |
| capture_generated_ownership | path.is_symlink | 30 | `path.is_symlink(data not statically known)` |

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
| unresolved_call | `capture_generated_ownership` | `path.is_symlink` | 30 |
| step_limit | `capture_generated_ownership` | `first 12 steps` | 0 |

## Behavior

This flow starts at `capture_generated_ownership` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
