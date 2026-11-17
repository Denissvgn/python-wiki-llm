# load_machine_verification_read_view

**Entry point:** `load_machine_verification_read_view` (`api`)
**Source:** [knowledge_verification](../modules/knowledge_verification.md)
**Modules touched:** [canonical_json](../modules/canonical_json.md), [host](../modules/host.md), [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), and 5 more

**Complete modules touched:**

- [canonical_json](../modules/canonical_json.md)
- [host](../modules/host.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
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
    participant p2 as _validated_artifacts_for_view
    participant p3 as evaluate_verification_receipt
    participant p4 as MachineVerificationReadView
    participant p5 as hash_json
    participant p6 as machine_verification_summary
    participant p7 as first_unsafe_path_component
    participant p8 as _read_regular_receipt
    participant p9 as deserialize_verification_receipt
    participant p10 as validate_verification_receipt
    participant p11 as serialize_verification_receipt
    participant p12 as formatted_json_bytes
    participant p13 as verification_receipt_to_payload
    participant p14 as _object
    participant p15 as _exact_fields
    participant p16 as _string
    participant p17 as _receipt_hash
    participant p18 as _scope_uid
    participant p19 as _receipt_anchor_mapping
    participant p20 as _parse_check
    participant p21 as require_mapping
    participant p22 as require_string
    participant p23 as _sha256
    participant p24 as _checker_id
    participant p25 as require_exact_fields
    participant p26 as _normalized_anchor_mapping
    participant p27 as compact_bytes
    participant p28 as _checker_version
    participant p29 as isinstance (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p30 as context
    p0->>p1: load_verification_receipt
    p0->>p2: _validated_artifacts_for_view
    p0->>p3: evaluate_verification_receipt
    p0->>p4: MachineVerificationReadView
    p0->>p5: hash_json
    p0->>p6: machine_verification_summary
    p1->>p7: first_unsafe_path_component
    p1->>p8: _read_regular_receipt
    p1->>p9: deserialize_verification_receipt
    p9->>p10: validate_verification_receipt
    p9->>p11: serialize_verification_receipt
    p11->>p12: formatted_json_bytes
    p11->>p13: verification_receipt_to_payload
    p10->>p14: _object
    p10->>p15: _exact_fields
    p10->>p16: _string
    p10->>p17: _receipt_hash
    p10->>p18: _scope_uid
    p10->>p19: _receipt_anchor_mapping
    p10->>p20: _parse_check
    p14->>p21: require_mapping
    p16->>p22: require_string
    p17->>p23: _sha256
    p20->>p24: _checker_id
    p15->>p25: require_exact_fields
    p19->>p26: _normalized_anchor_mapping
    p5->>p27: compact_bytes
    p20->>p28: _checker_version
    p0-->>p29: isinstance (src/llm_wiki_cli/services…ne_verification_read_view)(knowledge_view, KnowledgeReadView)
    p0-->>p30: context(None)
```

> Call sequence diagram shows 30 of 286 interactions; 256 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 106 (105 omitted); unresolved 1 of 45 (44 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_verification.py:load_machine_verification_read_view` | 1 | - | external | 10 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 5 | - | external | 1 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 7 | - | external | 19 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 7 | - | unresolved | 6 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 7 | [src/llm_wiki_cli/services/host.py](../modules/host.md) | internal | 1 |
| `src/llm_wiki_cli/services/host.py:current_host` | 14 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 5 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 3 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 5 | - | unresolved | 1 |
> Omission summary shows 8 of 79 groups; 71 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 136; effect analysis evaluated: 76, partial: 2, unavailable: 58. Counts include steps omitted from the displayed trace.

Collector observations for 78 source steps with known totals: observed: 333, emitted: 328, omitted: 5. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
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
| load_machine_verification_read_view | isinstance (src/llm_wiki_cli/services…ne_verification_read_view) | 76 | `isinstance(knowledge_view, KnowledgeReadView)` |
| load_machine_verification_read_view | TypeError (src/llm_wiki_cli/services…ne_verification_read_view) | 77 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| load_machine_verification_read_view | MachineVerificationReadView | 81 | `MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')` |
| load_machine_verification_read_view | load_verification_receipt | 87 | `load_verification_receipt(Path(...))` |
| load_verification_receipt | Path (src/llm_wiki_cli/services…load_verification_receipt) | 985 | `Path(wiki_dir)` |
| load_verification_receipt | first_unsafe_path_component | 986 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 52 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath | 52 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 60 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath | 60 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 61 | `lexical.is_absolute(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 72 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `load_machine_verification_read_view` | `isinstance` | 76 |
| external_call | `load_machine_verification_read_view` | `TypeError` | 77 |
| external_call | `first_unsafe_path_component` | `os.fspath` | 52 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 60 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 61 |
| step_limit | `load_machine_verification_read_view` | `first 12 steps` | 0 |
| truncated_flow | `load_machine_verification_read_view` | `depth limit` | 0 |

## Behavior

This flow starts at `load_machine_verification_read_view` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
