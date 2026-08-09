# knowledge

**Entry point:** `run` (`cli`)
**Source:** [knowledge_cmd](../modules/knowledge_cmd.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_cmd](../modules/knowledge_cmd.md), and 11 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_cmd](../modules/knowledge_cmd.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as _run_init
    participant p2 as _wiki_root
    participant p3 as Path
    participant p4 as first_unsafe_path_component
    participant p5 as fspath
    participant p6 as abspath
    participant p7 as is_absolute
    participant p8 as cwd
    participant p9 as list
    participant p10 as pop
    participant p11 as lstat
    participant p12 as getattr
    participant p13 as S_ISLNK
    participant p14 as bool
    participant p15 as trusted_symlink_owner
    participant p16 as callable
    participant p17 as readlink
    participant p18 as GovernanceError
    p0->>p1: _run_init
    p1->>p2: _wiki_root
    p2-->>p3: Path
    p2->>p4: first_unsafe_path_component
    p4-->>p3: Path
    p4-->>p5: fspath
    p4-->>p3: Path
    p4-->>p6: abspath
    p4-->>p7: is_absolute
    p4-->>p8: cwd
    p4-->>p3: Path
    p4-->>p9: list
    p4-->>p10: pop
    p4-->>p11: lstat
    p4-->>p12: getattr
    p4-->>p12: getattr
    p4-->>p13: S_ISLNK
    p4-->>p14: bool
    p4-->>p14: bool
    p4-->>p12: getattr
    p4-->>p15: trusted_symlink_owner
    p4-->>p16: callable
    p4-->>p12: getattr
    p4-->>p3: Path
    p4-->>p3: Path
    p4-->>p17: readlink
    p4-->>p7: is_absolute
    p4-->>p3: Path
    p4-->>p9: list
    p2->>p18: GovernanceError
```

> Call sequence diagram shows 30 of 1103 interactions; 1073 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. _run_init"]
    s3["3. _wiki_root"]
    s4["4. Path"]
    s5["5. first_unsafe_path_component"]
    s6["6. Path"]
    s7["7. fspath"]
    s8["8. Path"]
    s9["9. abspath"]
    s10["10. is_absolute"]
    s11["11. cwd"]
    s12["12. Path"]
    s1 -->|"_run_init(args)"| s2
    s2 -->|"_wiki_root(args.wiki_dir)"| s3
    s3 -. "Path(value)" .-> s4
    s3 -->|"first_unsafe_path_component(root)"| s5
    s5 -. "Path(os.fspath(...))" .-> s6
    s5 -. "os.fspath(path)" .-> s7
    s5 -. "Path(os.path.abspath(...))" .-> s8
    s5 -. "os.path.abspath(lexical)" .-> s9
    s5 -. "lexical.is_absolute(data not statically known)" .-> s10
    s5 -. "Path.cwd(data not statically known)" .-> s11
    s5 -. "Path(absolute.anchor)" .-> s12
    b0["mutation pending_parts.pop"]
    s5 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/knowledge_cmd.md"
    click s2 "../modules/knowledge_cmd.md"
    click s3 "../modules/knowledge_cmd.md"
    click s5 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `Lifecycle`, `Lifecycle`, `Lifecycle`, `Lifecycle` | - | - |
| `_run_init` | `args` | - | - | `none` |
| `_wiki_root` | `value: str \| Path` | - | - | `root` |
| `Path` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path` | - | - | - | - |
| `fspath` | - | - | - | - |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `is_absolute` | - | - | - | - |
| `cwd` | - | - | - | - |
| `Path` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | _run_init | 922 | `_run_init(args)` |
| _run_init | _wiki_root | 419 | `_wiki_root(args.wiki_dir)` |
| _wiki_root | Path | 106 | `Path(value)` |
| _wiki_root | first_unsafe_path_component | 107 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path | 50 | `Path(os.fspath(...))` |
| first_unsafe_path_component | fspath | 50 | `os.fspath(path)` |
| first_unsafe_path_component | Path | 58 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | abspath | 58 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | is_absolute | 59 | `lexical.is_absolute(data not statically known)` |
| first_unsafe_path_component | cwd | 65 | `Path.cwd(data not statically known)` |
| first_unsafe_path_component | Path | 66 | `Path(absolute.anchor)` |

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
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
