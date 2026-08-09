# load_governance

**Entry point:** `load_governance` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 3 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_model](../modules/knowledge_model.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_governance
    participant p1 as Path
    participant p2 as first_unsafe_path_component
    participant p3 as fspath
    participant p4 as abspath
    participant p5 as is_absolute
    participant p6 as cwd
    participant p7 as list
    participant p8 as pop
    participant p9 as lstat
    participant p10 as getattr
    participant p11 as S_ISLNK
    participant p12 as bool
    participant p13 as trusted_symlink_owner
    participant p14 as callable
    participant p15 as readlink
    participant p16 as GovernanceError
    participant p17 as _read_governance_bytes
    p0-->>p1: Path
    p0->>p2: first_unsafe_path_component
    p2-->>p1: Path
    p2-->>p3: fspath
    p2-->>p1: Path
    p2-->>p4: abspath
    p2-->>p5: is_absolute
    p2-->>p6: cwd
    p2-->>p1: Path
    p2-->>p7: list
    p2-->>p8: pop
    p2-->>p9: lstat
    p2-->>p10: getattr
    p2-->>p10: getattr
    p2-->>p11: S_ISLNK
    p2-->>p12: bool
    p2-->>p12: bool
    p2-->>p10: getattr
    p2-->>p13: trusted_symlink_owner
    p2-->>p14: callable
    p2-->>p10: getattr
    p2-->>p1: Path
    p2-->>p1: Path
    p2-->>p15: readlink
    p2-->>p5: is_absolute
    p2-->>p1: Path
    p2-->>p7: list
    p0->>p16: GovernanceError
    p0->>p17: _read_governance_bytes
    p17-->>p9: lstat
```

> Call sequence diagram shows 30 of 472 interactions; 442 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_governance"]
    s2["2. Path"]
    s3["3. first_unsafe_path_component"]
    s4["4. Path"]
    s5["5. fspath"]
    s6["6. Path"]
    s7["7. abspath"]
    s8["8. is_absolute"]
    s9["9. cwd"]
    s10["10. Path"]
    s11["11. list"]
    s12["12. pop"]
    s1 -. "Path(wiki_dir)" .-> s2
    s1 -->|"first_unsafe_path_component(root)"| s3
    s3 -. "Path(os.fspath(...))" .-> s4
    s3 -. "os.fspath(path)" .-> s5
    s3 -. "Path(os.path.abspath(...))" .-> s6
    s3 -. "os.path.abspath(lexical)" .-> s7
    s3 -. "lexical.is_absolute(data not statically known)" .-> s8
    s3 -. "Path.cwd(data not statically known)" .-> s9
    s3 -. "Path(absolute.anchor)" .-> s10
    s3 -. "list(...)" .-> s11
    s3 -. "pending_parts.pop(0)" .-> s12
    b0["mutation pending_parts.pop"]
    s3 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/knowledge_governance.md"
    click s3 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `load_governance` | `wiki_dir: str \| Path`, `expected_bundle_id: str \| None` | `GOVERNANCE_FILENAME`, `GOVERNANCE_FILENAME` | - | `GovernanceLoadResult(...)` |
| `Path` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path` | - | - | - | - |
| `fspath` | - | - | - | - |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `is_absolute` | - | - | - | - |
| `cwd` | - | - | - | - |
| `Path` | - | - | - | - |
| `list` | - | - | - | - |
| `pop` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_governance | Path | 765 | `Path(wiki_dir)` |
| load_governance | first_unsafe_path_component | 766 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path | 50 | `Path(os.fspath(...))` |
| first_unsafe_path_component | fspath | 50 | `os.fspath(path)` |
| first_unsafe_path_component | Path | 58 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | abspath | 58 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | is_absolute | 59 | `lexical.is_absolute(data not statically known)` |
| first_unsafe_path_component | cwd | 65 | `Path.cwd(data not statically known)` |
| first_unsafe_path_component | Path | 66 | `Path(absolute.anchor)` |
| first_unsafe_path_component | list | 67 | `list(...)` |
| first_unsafe_path_component | pop | 70 | `pending_parts.pop(0)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 70 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `first_unsafe_path_component` | `os.fspath` | 50 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 58 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 59 |
| external_call | `first_unsafe_path_component` | `Path.cwd` | 65 |
| step_limit | `load_governance` | `first 12 steps` | 0 |
| truncated_flow | `load_governance` | `depth limit` | 0 |

## Behavior

This flow starts at `load_governance` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
