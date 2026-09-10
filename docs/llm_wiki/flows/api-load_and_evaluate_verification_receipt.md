# load_and_evaluate_verification_receipt

**Entry point:** `load_and_evaluate_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_and_evaluate_verification_receipt
    participant p1 as load_verification_receipt
    participant p2 as Path (src/llm_wiki_cli/services…load_verification_receipt)
    participant p3 as first_unsafe_path_component
    participant p4 as Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p5 as os.fspath
    participant p6 as os.path.abspath
    participant p7 as lexical.is_absolute
    participant p8 as Path.cwd
    participant p9 as list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p10 as pending_parts.pop
    participant p11 as current.lstat
    participant p12 as getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p13 as stat.S_ISLNK (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p14 as bool
    participant p15 as trusted_symlink_owner
    participant p16 as callable
    participant p17 as os.readlink
    participant p18 as link_target.is_absolute
    participant p19 as VerificationReceiptError
    participant p20 as root.is_symlink
    p0->>p1: load_verification_receipt
    p1-->>p2: Path (src/llm_wiki_cli/services…load_verification_receipt)
    p1->>p3: first_unsafe_path_component
    p3-->>p4: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p5: os.fspath
    p3-->>p4: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p6: os.path.abspath
    p3-->>p7: lexical.is_absolute
    p3-->>p8: Path.cwd
    p3-->>p4: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p9: list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p10: pending_parts.pop
    p3-->>p11: current.lstat
    p3-->>p12: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p12: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p13: stat.S_ISLNK (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p14: bool
    p3-->>p14: bool
    p3-->>p12: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p15: trusted_symlink_owner
    p3-->>p16: callable
    p3-->>p12: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p4: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p4: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p17: os.readlink
    p3-->>p18: link_target.is_absolute
    p3-->>p4: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p3-->>p9: list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p1->>p19: VerificationReceiptError
    p1-->>p20: root.is_symlink
```

> Call sequence diagram shows 30 of 247 interactions; 217 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_and_evaluate_verification_receipt"]
    s2["2. load_verification_receipt"]
    s3["3. Path (src/llm_wiki_cli/services…load_verification_receipt)"]
    s4["4. first_unsafe_path_component"]
    s5["5. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s6["6. os.fspath"]
    s7["7. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s8["8. os.path.abspath"]
    s9["9. lexical.is_absolute"]
    s10["10. Path.cwd"]
    s11["11. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s12["12. list (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s1 -->|"load_verification_receipt(wiki_dir, missing_ok=missing_ok)"| s2
    s2 -. "Path (src/llm_wiki_cli/services…load_verification_receipt)(wiki_dir)" .-> s3
    s2 -->|"first_unsafe_path_component(root)"| s4
    s4 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))" .-> s5
    s4 -. "os.fspath(path)" .-> s6
    s4 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.path.abspath(...))" .-> s7
    s4 -. "os.path.abspath(lexical)" .-> s8
    s4 -. "lexical.is_absolute(data not statically known)" .-> s9
    s4 -. "Path.cwd(data not statically known)" .-> s10
    s4 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(absolute.anchor)" .-> s11
    s4 -. "list (src/llm_wiki_cli/services…rst_unsafe_path_component)(...)" .-> s12
    b0["mutation pending_parts.pop"]
    s4 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/verification_contracts.md"
    click s2 "../modules/verification_contracts.md"
    click s4 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `load_and_evaluate_verification_receipt` | `wiki_dir: str \| Path`, `context: VerificationContext`, `missing_ok: bool` | - | - | `None`, `evaluate_verification_receipt(...)` |
| `load_verification_receipt` | `wiki_dir: str \| Path`, `missing_ok: bool` | - | - | `None`, `deserialize_verification_receipt(...)` |
| `Path (src/llm_wiki_cli/services…load_verification_receipt)` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `os.path.abspath` | - | - | - | - |
| `lexical.is_absolute` | - | - | - | - |
| `Path.cwd` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `list (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_and_evaluate_verification_receipt | load_verification_receipt | 1087 | `load_verification_receipt(wiki_dir, missing_ok=missing_ok)` |
| load_verification_receipt | Path (src/llm_wiki_cli/services…load_verification_receipt) | 956 | `Path(wiki_dir)` |
| load_verification_receipt | first_unsafe_path_component | 957 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 50 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath | 50 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 58 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath | 58 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 59 | `lexical.is_absolute(data not statically known)` |
| first_unsafe_path_component | Path.cwd | 65 | `Path.cwd(data not statically known)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 66 | `Path(absolute.anchor)` |
| first_unsafe_path_component | list (src/llm_wiki_cli/services…rst_unsafe_path_component) | 67 | `list(...)` |

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
| step_limit | `load_and_evaluate_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `load_and_evaluate_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `load_and_evaluate_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
