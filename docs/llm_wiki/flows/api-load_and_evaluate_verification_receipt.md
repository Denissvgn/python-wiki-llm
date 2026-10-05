# load_and_evaluate_verification_receipt

**Entry point:** `load_and_evaluate_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_and_evaluate_verification_receipt
    participant p1 as load_verification_receipt
    participant p2 as evaluate_verification_receipt
    participant p3 as Path (src/llm_wiki_cli/services…load_verification_receipt)
    participant p4 as validate_verification_receipt
    participant p5 as first_unsafe_path_component
    participant p6 as isinstance (src/llm_wiki_cli/services…uate_verification_receipt)
    participant p7 as VerificationReceiptError
    participant p8 as TypeError (src/llm_wiki_cli/services…uate_verification_receipt)
    participant p9 as root.is_symlink
    participant p10 as add
    participant p11 as verification_receipt_path
    participant p12 as dict (src/llm_wiki_cli/services…uate_verification_receipt)
    participant p13 as _read_regular_receipt
    participant p14 as deserialize_verification_receipt
    participant p15 as _CHECKER_REGISTRY.get
    participant p16 as VerificationReceiptEvaluation
    participant p17 as tuple (src/llm_wiki_cli/services…uate_verification_receipt)
    participant p18 as Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p19 as Path (src/llm_wiki_cli/services…verification_receipt_path)
    participant p20 as path.lstat
    participant p21 as isinstance (src/llm_wiki_cli/services…lize_verification_receipt)
    p0->>p1: load_verification_receipt
    p0->>p2: evaluate_verification_receipt
    p1-->>p3: Path (src/llm_wiki_cli/services…load_verification_receipt)(wiki_dir)
    p2->>p4: validate_verification_receipt
    p1->>p5: first_unsafe_path_component
    p2-->>p6: isinstance (src/llm_wiki_cli/services…uate_verification_receipt)(context, VerificationContext)
    p1->>p7: VerificationReceiptError
    p2-->>p8: TypeError (src/llm_wiki_cli/services…uate_verification_receipt)('context must be a VerificationContext')
    p1-->>p9: root.is_symlink
    p2-->>p10: add(VerificationInvalidationReason.KNOWLEDGE_CHANGED)
    p1->>p7: VerificationReceiptError
    p2-->>p10: add(VerificationInvalidationReason.SCOPE_CHANGED)
    p1->>p11: verification_receipt_path
    p2-->>p12: dict (src/llm_wiki_cli/services…uate_verification_receipt)(current_receipt.evidence)
    p1->>p13: _read_regular_receipt
    p2-->>p12: dict (src/llm_wiki_cli/services…uate_verification_receipt)(context.evidence)
    p1->>p14: deserialize_verification_receipt
    p2-->>p10: add(VerificationInvalidationReason.EVIDENCE_CHANGED)
    p2-->>p12: dict (src/llm_wiki_cli/services…uate_verification_receipt)(current_receipt.evaluated_snapshot)
    p2-->>p12: dict (src/llm_wiki_cli/services…uate_verification_receipt)(context.evaluated_snapshot)
    p2-->>p10: add(VerificationInvalidationReason.SNAPSHOT_CHANGED)
    p2-->>p15: _CHECKER_REGISTRY.get(check.checker_id)
    p2-->>p10: add(VerificationInvalidationReason.UNKNOWN_CHECKER)
    p2-->>p10: add(VerificationInvalidationReason.CHECKER_VERSION_CHANGED)
    p2->>p16: VerificationReceiptEvaluation
    p2-->>p17: tuple (src/llm_wiki_cli/services…uate_verification_receipt)(reasons)
    p5-->>p18: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))
    p11-->>p19: Path (src/llm_wiki_cli/services…verification_receipt_path)(wiki_dir)
    p13-->>p20: path.lstat
    p14-->>p21: isinstance (src/llm_wiki_cli/services…lize_verification_receipt)(content, bytes)
```

> Call sequence diagram shows 30 of 247 interactions; 217 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 11 of 92 (81 omitted); unresolved 9 of 35 (26 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 4 | - | external | 19 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 4 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 35 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 7 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 35 | - | external | 12 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 35 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:deserialize_verification_receipt` | 58 | - | external | 3 |
| `src/llm_wiki_cli/services/verification_contracts.py:deserialize_verification_receipt` | 58 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 6 |
| `src/llm_wiki_cli/services/verification_contracts.py:deserialize_verification_receipt` | 58 | - | unresolved | 1 |
> Omission summary shows 8 of 65 groups; 57 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath | 51 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 59 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath | 59 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 60 | `lexical.is_absolute(data not statically known)` |
| first_unsafe_path_component | Path.cwd | 66 | `Path.cwd(data not statically known)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 67 | `Path(absolute.anchor)` |
| first_unsafe_path_component | list (src/llm_wiki_cli/services…rst_unsafe_path_component) | 68 | `list(...)` |

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
| step_limit | `load_and_evaluate_verification_receipt` | `first 12 steps` | 0 |
| truncated_flow | `load_and_evaluate_verification_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `load_and_evaluate_verification_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
