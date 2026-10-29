# load_verification_receipt

**Entry point:** `load_verification_receipt` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_verification_receipt
    participant p1 as _read_regular_receipt
    participant p2 as deserialize_verification_receipt
    participant p3 as first_unsafe_path_component
    participant p4 as VerificationReceiptError
    participant p5 as verification_receipt_path
    participant p6 as validate_verification_receipt
    participant p7 as serialize_verification_receipt
    participant p8 as formatted_json_bytes
    participant p9 as verification_receipt_to_payload
    participant p10 as _object
    participant p11 as _exact_fields
    participant p12 as _string
    participant p13 as _receipt_hash
    participant p14 as _scope_uid
    participant p15 as _receipt_anchor_mapping
    participant p16 as hash_json
    participant p17 as _parse_check
    participant p18 as _sha256
    participant p19 as _checker_id
    participant p20 as _normalized_anchor_mapping
    participant p21 as canonical_json_bytes
    participant p22 as _checker_version
    participant p23 as _array
    participant p24 as _parse_diagnostic
    participant p25 as _parse_coverage
    participant p26 as require_sha256
    participant p27 as _nonnegative_int
    participant p28 as _receipt_to_payload
    participant p29 as Path (src/llm_wiki_cli/services…load_verification_receipt)
    participant p30 as root.is_symlink
    p0->>p1: _read_regular_receipt
    p0->>p2: deserialize_verification_receipt
    p0->>p3: first_unsafe_path_component
    p0->>p4: VerificationReceiptError
    p0->>p5: verification_receipt_path
    p2->>p6: validate_verification_receipt
    p2->>p7: serialize_verification_receipt
    p7->>p8: formatted_json_bytes
    p7->>p9: verification_receipt_to_payload
    p6->>p10: _object
    p6->>p11: _exact_fields
    p6->>p12: _string
    p6->>p13: _receipt_hash
    p6->>p14: _scope_uid
    p6->>p15: _receipt_anchor_mapping
    p6->>p16: hash_json
    p6->>p17: _parse_check
    p13->>p18: _sha256
    p17->>p19: _checker_id
    p15->>p20: _normalized_anchor_mapping
    p16->>p21: canonical_json_bytes
    p17->>p22: _checker_version
    p17->>p23: _array
    p17->>p24: _parse_diagnostic
    p17->>p25: _parse_coverage
    p18->>p26: require_sha256
    p25->>p27: _nonnegative_int
    p6->>p28: _receipt_to_payload
    p0-->>p29: Path (src/llm_wiki_cli/services…load_verification_receipt)(wiki_dir)
    p0-->>p30: root.is_symlink
```

> Call sequence diagram shows 30 of 236 interactions; 206 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 88 (87 omitted); unresolved 1 of 29 (28 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 3 | - | external | 20 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 3 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 1 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:verification_receipt_path` | 32 | - | external | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 34 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 34 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 7 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 34 | - | external | 12 |
| `src/llm_wiki_cli/services/verification_contracts.py:deserialize_verification_receipt` | 57 | - | external | 4 |
> Omission summary shows 8 of 72 groups; 64 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 120; effect analysis evaluated: 66, partial: 0, unavailable: 54. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `load_verification_receipt` | `available` | `evaluated` | `available` |
| `Path (src/llm_wiki_cli/services…load_verification_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `first_unsafe_path_component` | `available` | `evaluated` | `available` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `os.fspath` | `not_applicable` | `not_applicable` | `not_applicable` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `os.path.abspath` | `not_applicable` | `not_applicable` | `not_applicable` |
| `lexical.is_absolute` | `not_applicable` | `not_applicable` | `not_applicable` |
| `Path.cwd` | `not_applicable` | `not_applicable` | `not_applicable` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `list (src/llm_wiki_cli/services…rst_unsafe_path_component)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `pending_parts.pop` | `not_applicable` | `not_applicable` | `not_applicable` |

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
