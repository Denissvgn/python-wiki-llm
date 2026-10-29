# load_machine_verification_read_view

**Entry point:** `load_machine_verification_read_view` (`api`)
**Source:** [knowledge_verification](../modules/knowledge_verification.md)
**Modules touched:** [io](../modules/io.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_verification](../modules/knowledge_verification.md), and 2 more

**Complete modules touched:**

- [io](../modules/io.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_machine_verification_read_view
    participant p1 as load_verification_receipt
    participant p2 as evaluate_verification_receipt
    participant p3 as MachineVerificationReadView
    participant p4 as hash_json
    participant p5 as machine_verification_summary
    participant p6 as _read_regular_receipt
    participant p7 as deserialize_verification_receipt
    participant p8 as validate_verification_receipt
    participant p9 as serialize_verification_receipt
    participant p10 as formatted_json_bytes
    participant p11 as verification_receipt_to_payload
    participant p12 as _object
    participant p13 as _exact_fields
    participant p14 as _string
    participant p15 as _receipt_hash
    participant p16 as _scope_uid
    participant p17 as _receipt_anchor_mapping
    participant p18 as _parse_check
    participant p19 as _sha256
    participant p20 as _checker_id
    participant p21 as _normalized_anchor_mapping
    participant p22 as canonical_json_bytes
    participant p23 as _checker_version
    participant p24 as _array
    participant p25 as _parse_diagnostic
    participant p26 as _parse_coverage
    participant p27 as first_unsafe_path_component
    participant p28 as VerificationReceiptError
    participant p29 as isinstance (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p30 as context
    p0->>p1: load_verification_receipt
    p0->>p2: evaluate_verification_receipt
    p0->>p3: MachineVerificationReadView
    p0->>p4: hash_json
    p0->>p5: machine_verification_summary
    p1->>p6: _read_regular_receipt
    p1->>p7: deserialize_verification_receipt
    p7->>p8: validate_verification_receipt
    p7->>p9: serialize_verification_receipt
    p9->>p10: formatted_json_bytes
    p9->>p11: verification_receipt_to_payload
    p8->>p12: _object
    p8->>p13: _exact_fields
    p8->>p14: _string
    p8->>p15: _receipt_hash
    p8->>p16: _scope_uid
    p8->>p17: _receipt_anchor_mapping
    p8->>p18: _parse_check
    p15->>p19: _sha256
    p18->>p20: _checker_id
    p17->>p21: _normalized_anchor_mapping
    p4->>p22: canonical_json_bytes
    p18->>p23: _checker_version
    p18->>p24: _array
    p18->>p25: _parse_diagnostic
    p18->>p26: _parse_coverage
    p1->>p27: first_unsafe_path_component
    p1->>p28: VerificationReceiptError
    p0-->>p29: isinstance (src/llm_wiki_cli/services…ne_verification_read_view)(knowledge_view, KnowledgeReadView)
    p0-->>p30: context(None)
```

> Call sequence diagram shows 30 of 272 interactions; 242 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 103 (102 omitted); unresolved 1 of 43 (42 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_verification.py:load_machine_verification_read_view` | 1 | - | external | 10 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 5 | - | external | 1 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 7 | - | external | 20 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 7 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 5 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 5 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:verification_receipt_path` | 36 | - | external | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 38 | - | unresolved | 3 |
> Omission summary shows 8 of 75 groups; 67 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 127; effect analysis evaluated: 67, partial: 2, unavailable: 58. Counts include steps omitted from the displayed trace.

Collector observations for 69 source steps with known totals: observed: 298, emitted: 294, omitted: 4. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `load_machine_verification_read_view` | `available` | `evaluated` | `available` | `13` | `13` | `0` |
| `isinstance (src/llm_wiki_cli/services…ne_verification_read_view)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…ne_verification_read_view)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `MachineVerificationReadView` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `load_verification_receipt` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `Path (src/llm_wiki_cli/services…load_verification_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `first_unsafe_path_component` | `available` | `evaluated` | `available` | `14` | `14` | `0` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `os.fspath` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `os.path.abspath` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `lexical.is_absolute` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. load_machine_verification_read_view"]
    s2["2. isinstance (src/llm_wiki_cli/services…ne_verification_read_view)"]
    s3["3. TypeError (src/llm_wiki_cli/services…ne_verification_read_view)"]
    s4["4. MachineVerificationReadView"]
    s5["5. load_verification_receipt"]
    s6["6. Path (src/llm_wiki_cli/services…load_verification_receipt)"]
    s7["7. first_unsafe_path_component"]
    s8["8. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s9["9. os.fspath"]
    s10["10. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s11["11. os.path.abspath"]
    s12["12. lexical.is_absolute"]
    s1 -. "isinstance (src/llm_wiki_cli/services…ne_verification_read_view)(knowledge_view, KnowledgeReadView)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…ne_verification_read_view)('knowledge_view must be a KnowledgeReadView')" .-> s3
    s1 -->|"MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')"| s4
    s1 -->|"load_verification_receipt(Path(...))"| s5
    s5 -. "Path (src/llm_wiki_cli/services…load_verification_receipt)(wiki_dir)" .-> s6
    s5 -->|"first_unsafe_path_component(root)"| s7
    s7 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))" .-> s8
    s7 -. "os.fspath(path)" .-> s9
    s7 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.path.abspath(...))" .-> s10
    s7 -. "os.path.abspath(lexical)" .-> s11
    s7 -. "lexical.is_absolute(data not statically known)" .-> s12
    b0["mutation pending_parts.pop"]
    s7 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/knowledge_verification.md"
    click s4 "../modules/knowledge_consumption.md"
    click s5 "../modules/verification_contracts.md"
    click s7 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `load_machine_verification_read_view` | `wiki_dir: str \| Path`, `knowledge_view: KnowledgeReadView` | `KnowledgeReadView`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `GOVERNANCE_EXTENSION_KEY`, `Mapping`, `MachineVerificationAvailability` | - | `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)` |
| `isinstance (src/llm_wiki_cli/services…ne_verification_read_view)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ne_verification_read_view)` | - | - | - | - |
| `MachineVerificationReadView` | - | - | - | - |
| `load_verification_receipt` | `wiki_dir: str \| Path`, `missing_ok: bool` | - | - | `None`, `deserialize_verification_receipt(...)` |
| `Path (src/llm_wiki_cli/services…load_verification_receipt)` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `os.path.abspath` | - | - | - | - |
| `lexical.is_absolute` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_machine_verification_read_view | isinstance (src/llm_wiki_cli/services…ne_verification_read_view) | 75 | `isinstance(knowledge_view, KnowledgeReadView)` |
| load_machine_verification_read_view | TypeError (src/llm_wiki_cli/services…ne_verification_read_view) | 76 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| load_machine_verification_read_view | MachineVerificationReadView | 80 | `MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')` |
| load_machine_verification_read_view | load_verification_receipt | 86 | `load_verification_receipt(Path(...))` |
| load_verification_receipt | Path (src/llm_wiki_cli/services…load_verification_receipt) | 956 | `Path(wiki_dir)` |
| load_verification_receipt | first_unsafe_path_component | 957 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath | 51 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 59 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath | 59 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 60 | `lexical.is_absolute(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 71 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `load_machine_verification_read_view` | `isinstance` | 75 |
| external_call | `load_machine_verification_read_view` | `TypeError` | 76 |
| external_call | `first_unsafe_path_component` | `os.fspath` | 51 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 59 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 60 |
| step_limit | `load_machine_verification_read_view` | `first 12 steps` | 0 |
| truncated_flow | `load_machine_verification_read_view` | `depth limit` | 0 |

## Behavior

This flow starts at `load_machine_verification_read_view` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
