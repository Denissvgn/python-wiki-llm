# load_verification_receipt

**Entry point:** `load_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_verification_receipt
    participant p1 as Path (src/llm_wiki_cli/services…load_verification_receipt)
    participant p2 as first_unsafe_path_component
    participant p3 as VerificationReceiptError
    participant p4 as root.is_symlink
    participant p5 as verification_receipt_path
    participant p6 as _read_regular_receipt
    participant p7 as deserialize_verification_receipt
    participant p8 as Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p9 as Path (src/llm_wiki_cli/services…verification_receipt_path)
    participant p10 as path.lstat
    participant p11 as isinstance (src/llm_wiki_cli/services…lize_verification_receipt)
    participant p12 as os.fspath
    participant p13 as TypeError
    participant p14 as len (src/llm_wiki_cli/services…lize_verification_receipt)
    participant p15 as os.path.abspath
    participant p16 as stat.S_ISLNK (src/llm_wiki_cli/services….py:_read_regular_receipt)
    participant p17 as lexical.is_absolute
    participant p18 as content.decode
    participant p19 as Path.cwd
    participant p20 as stat.S_ISREG
    participant p21 as json.loads
    p0-->>p1: Path (src/llm_wiki_cli/services…load_verification_receipt)(wiki_dir)
    p0->>p2: first_unsafe_path_component
    p0->>p3: VerificationReceiptError
    p0-->>p4: root.is_symlink
    p0->>p3: VerificationReceiptError
    p0->>p5: verification_receipt_path
    p0->>p6: _read_regular_receipt
    p0->>p7: deserialize_verification_receipt
    p2-->>p8: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))
    p5-->>p9: Path (src/llm_wiki_cli/services…verification_receipt_path)(wiki_dir)
    p6-->>p10: path.lstat
    p7-->>p11: isinstance (src/llm_wiki_cli/services…lize_verification_receipt)(content, bytes)
    p2-->>p12: os.fspath(path)
    p6->>p3: VerificationReceiptError
    p7-->>p13: TypeError('content must be bytes')
    p2-->>p8: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.path.abspath(...))
    p6->>p3: VerificationReceiptError
    p7-->>p14: len (src/llm_wiki_cli/services…lize_verification_receipt)(content)
    p2-->>p15: os.path.abspath(lexical)
    p6-->>p16: stat.S_ISLNK (src/llm_wiki_cli/services….py:_read_regular_receipt)(metadata.st_mode)
    p7->>p3: VerificationReceiptError
    p2-->>p17: lexical.is_absolute
    p6->>p3: VerificationReceiptError
    p7-->>p18: content.decode('utf-8')
    p2-->>p19: Path.cwd
    p6-->>p20: stat.S_ISREG(metadata.st_mode)
    p7->>p3: VerificationReceiptError
    p2-->>p8: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(absolute.anchor)
    p6->>p3: VerificationReceiptError
    p7-->>p21: json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)
```

> Call sequence diagram shows 30 of 236 interactions; 206 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 14 of 88 (74 omitted); unresolved 4 of 29 (25 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 3 | - | external | 14 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 3 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 34 | - | external | 10 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 34 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 3 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 34 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:deserialize_verification_receipt` | 57 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 4 |
| `src/llm_wiki_cli/services/verification_contracts.py:validate_verification_receipt` | 66 | - | external | 7 |
| `src/llm_wiki_cli/services/verification_contracts.py:validate_verification_receipt` | 66 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 25 |
> Omission summary shows 8 of 70 groups; 62 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_verification_receipt"]
    s2["2. Path (src/llm_wiki_cli/services…load_verification_receipt)"]
    s3["3. first_unsafe_path_component"]
    s4["4. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s5["5. os.fspath"]
    s6["6. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s7["7. os.path.abspath"]
    s8["8. lexical.is_absolute"]
    s9["9. Path.cwd"]
    s10["10. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s11["11. list (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s12["12. pending_parts.pop"]
    s1 -. "Path (src/llm_wiki_cli/services…load_verification_receipt)(wiki_dir)" .-> s2
    s1 -->|"first_unsafe_path_component(root)"| s3
    s3 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))" .-> s4
    s3 -. "os.fspath(path)" .-> s5
    s3 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.path.abspath(...))" .-> s6
    s3 -. "os.path.abspath(lexical)" .-> s7
    s3 -. "lexical.is_absolute(data not statically known)" .-> s8
    s3 -. "Path.cwd(data not statically known)" .-> s9
    s3 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(absolute.anchor)" .-> s10
    s3 -. "list (src/llm_wiki_cli/services…rst_unsafe_path_component)(...)" .-> s11
    s3 -. "pending_parts.pop(0)" .-> s12
    b0["mutation pending_parts.pop"]
    s3 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/verification_contracts.md"
    click s3 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `pending_parts.pop` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_verification_receipt | Path (src/llm_wiki_cli/services…load_verification_receipt) | 956 | `Path(wiki_dir)` |
| load_verification_receipt | first_unsafe_path_component | 957 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath | 51 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 59 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath | 59 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 60 | `lexical.is_absolute(data not statically known)` |
| first_unsafe_path_component | Path.cwd | 66 | `Path.cwd(data not statically known)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 67 | `Path(absolute.anchor)` |
| first_unsafe_path_component | list (src/llm_wiki_cli/services…rst_unsafe_path_component) | 68 | `list(...)` |
| first_unsafe_path_component | pending_parts.pop | 71 | `pending_parts.pop(0)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 71 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `first_unsafe_path_component` | `os.fspath` | 51 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 59 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 60 |
| external_call | `first_unsafe_path_component` | `Path.cwd` | 66 |
| step_limit | `load_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `load_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `load_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
