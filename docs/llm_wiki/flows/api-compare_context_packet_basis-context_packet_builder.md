# compare_context_packet_basis

**Entry point:** `compare_context_packet_basis` (`api`)
**Source:** [context_packet_builder](../modules/context_packet_builder.md)
**Modules touched:** [canonical_json](../modules/canonical_json.md), [context_packet](../modules/context_packet.md), [context_packet_builder](../modules/context_packet_builder.md), and 3 more

**Complete modules touched:**

- [canonical_json](../modules/canonical_json.md)
- [context_packet](../modules/context_packet.md)
- [context_packet_builder](../modules/context_packet_builder.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [maintenance_status](../modules/maintenance_status.md)
- [packet_field_policy](../modules/packet_field_policy.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_context_packet_basis
    participant p1 as validate_context_packet
    participant p2 as ContextPacketMalformedError
    participant p3 as ContextBasisComparison
    participant p4 as _validate_context_packet_bytes
    participant p5 as _coerce_packet_bytes
    participant p6 as _strict_json_payload
    participant p7 as _packet_contract_for_schema
    participant p8 as _validate_packet_shape
    participant p9 as _encode_packet_payload
    participant p10 as _packet_id
    participant p11 as _path_policy_receipt
    participant p12 as QualifiedContextPacket._from_validated_payload
    participant p13 as _exact_fields
    participant p14 as compact_bytes
    participant p15 as _freeze_json
    participant p16 as _validate_assurance
    participant p17 as _validate_packet_request
    participant p18 as _validate_response
    participant p19 as _validate_basis
    participant p20 as _validate_response_basis_consistency
    participant p21 as _validate_delivery
    participant p22 as _validate_path_policy_shape
    participant p23 as _mapping
    participant p24 as _path_policy_digest
    participant p25 as _nonnegative_integer
    participant p26 as _validate_repository_basis
    participant p27 as _validate_knowledge_basis
    participant p28 as _validate_explicit_ranking_policy
    participant p29 as isinstance (src/llm_wiki_cli/services…pare_context_packet_basis)
    participant p30 as validation.packet.to_payload
    p0->>p1: validate_context_packet
    p0->>p2: ContextPacketMalformedError
    p0->>p3: ContextBasisComparison
    p1->>p4: _validate_context_packet_bytes
    p4->>p5: _coerce_packet_bytes
    p4->>p6: _strict_json_payload
    p4->>p7: _packet_contract_for_schema
    p4->>p8: _validate_packet_shape
    p4->>p9: _encode_packet_payload
    p4->>p10: _packet_id
    p4->>p11: _path_policy_receipt
    p4->>p12: QualifiedContextPacket._from_validated_payload
    p8->>p13: _exact_fields
    p9->>p14: compact_bytes
    p12->>p15: _freeze_json
    p8->>p16: _validate_assurance
    p8->>p17: _validate_packet_request
    p8->>p18: _validate_response
    p8->>p19: _validate_basis
    p8->>p20: _validate_response_basis_consistency
    p8->>p21: _validate_delivery
    p8->>p22: _validate_path_policy_shape
    p16->>p23: _mapping
    p22->>p24: _path_policy_digest
    p19->>p25: _nonnegative_integer
    p19->>p26: _validate_repository_basis
    p19->>p27: _validate_knowledge_basis
    p18->>p28: _validate_explicit_ranking_policy
    p0-->>p29: isinstance (src/llm_wiki_cli/services…pare_context_packet_basis)(expected_basis, Mapping)
    p0-->>p30: validation.packet.to_payload
```

> Call sequence diagram shows 30 of 429 interactions; 399 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 114 (113 omitted); unresolved 1 of 88 (87 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_engine/context_packet.py:_coerce_packet_bytes` | 4 | - | external | 5 |
| `src/llm_wiki_engine/context_packet.py:_coerce_packet_bytes` | 4 | [src/llm_wiki_engine/context_packet.py](../modules/context_packet.md) | internal | 4 |
| `src/llm_wiki_engine/context_packet.py:_coerce_packet_bytes` | 4 | - | unresolved | 3 |
| `src/llm_wiki_engine/context_packet.py:_strict_json_payload` | 17 | - | unresolved | 1 |
| `src/llm_wiki_engine/context_packet.py:_strict_json_payload` | 17 | [src/llm_wiki_engine/context_packet.py](../modules/context_packet.md) | internal | 4 |
| `src/llm_wiki_engine/context_packet.py:_strict_json_payload` | 17 | - | external | 2 |
| `src/llm_wiki_engine/context_packet.py:_validate_json_tree` | 24 | - | external | 1 |
| `src/llm_wiki_engine/context_packet.py:_validate_json_tree` | 24 | - | unresolved | 1 |
> Omission summary shows 8 of 102 groups; 94 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 228; effect analysis evaluated: 108, partial: 1, unavailable: 119. Counts include steps omitted from the displayed trace.

Collector observations for 109 source steps with known totals: observed: 437, emitted: 432, omitted: 5. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `compare_context_packet_basis` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `validate_context_packet` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_validate_context_packet_bytes` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_coerce_packet_bytes` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `bytes (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ContextPacketMalformedError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `len (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ContextPacketMalformedError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `raw.startswith` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. compare_context_packet_basis"]
    s2["2. validate_context_packet"]
    s3["3. _validate_context_packet_bytes"]
    s4["4. _coerce_packet_bytes"]
    s5["5. isinstance (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)"]
    s6["6. isinstance (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)"]
    s7["7. bytes (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)"]
    s8["8. TypeError (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)"]
    s9["9. ContextPacketMalformedError"]
    s10["10. len (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)"]
    s11["11. ContextPacketMalformedError"]
    s12["12. raw.startswith"]
    s1 -->|"validate_context_packet(packet_bytes)"| s2
    s2 -->|"_validate_context_packet_bytes(packet_bytes)"| s3
    s3 -->|"_coerce_packet_bytes(packet_bytes)"| s4
    s4 -. "isinstance (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)(value, bytes)" .-> s5
    s4 -. "isinstance (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)(value, (...))" .-> s6
    s4 -. "bytes (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)(value)" .-> s7
    s4 -. "TypeError (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)('packet_bytes must be bytes-like')" .-> s8
    s4 -->|"ContextPacketMalformedError('packet_bytes', 'must not be empty')"| s9
    s4 -. "len (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)(raw)" .-> s10
    s4 -->|"ContextPacketMalformedError('packet_bytes', ...)"| s11
    s4 -. "raw.startswith(b'\xef\xbb\xbf')" .-> s12
    click s1 "../modules/context_packet_builder.md"
    click s2 "../modules/context_packet.md"
    click s3 "../modules/context_packet.md"
    click s4 "../modules/context_packet.md"
    click s9 "../modules/context_packet.md"
    click s11 "../modules/context_packet.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compare_context_packet_basis` | `packet_bytes: bytes \| bytearray \| memoryview`, `expected_basis: Mapping[str, Any]` | `Mapping` | - | `ContextBasisComparison(...)` |
| `validate_context_packet` | `packet_bytes: bytes \| bytearray \| memoryview`, `accepted_generators: Iterable[str] \| None` | - | - | `_validate_context_packet_bytes(...)`, `_validate_context_packet_bytes(...)` |
| `_validate_context_packet_bytes` | `packet_bytes: bytes \| bytearray \| memoryview` | - | - | `ContextPacketValidation(...)` |
| `_coerce_packet_bytes` | `value: bytes \| bytearray \| memoryview` | `_MAX_PACKET_BYTES`, `_MAX_PACKET_BYTES` | - | `raw` |
| `isinstance (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `isinstance (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `bytes (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `TypeError (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |
| `len (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |
| `raw.startswith` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compare_context_packet_basis | validate_context_packet | 1549 | `validate_context_packet(packet_bytes)` |
| validate_context_packet | _validate_context_packet_bytes | 319 | `_validate_context_packet_bytes(packet_bytes)` |
| _validate_context_packet_bytes | _coerce_packet_bytes | 335 | `_coerce_packet_bytes(packet_bytes)` |
| _coerce_packet_bytes | isinstance (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes) | 616 | `isinstance(value, bytes)` |
| _coerce_packet_bytes | isinstance (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes) | 618 | `isinstance(value, (...))` |
| _coerce_packet_bytes | bytes (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes) | 619 | `bytes(value)` |
| _coerce_packet_bytes | TypeError (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes) | 621 | `TypeError('packet_bytes must be bytes-like')` |
| _coerce_packet_bytes | ContextPacketMalformedError | 623 | `ContextPacketMalformedError('packet_bytes', 'must not be empty')` |
| _coerce_packet_bytes | len (src/llm_wiki_engine/conte…t.py:_coerce_packet_bytes) | 624 | `len(raw)` |
| _coerce_packet_bytes | ContextPacketMalformedError | 625 | `ContextPacketMalformedError('packet_bytes', ...)` |
| _coerce_packet_bytes | raw.startswith | 629 | `raw.startswith(b'\xef\xbb\xbf')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_coerce_packet_bytes` | `isinstance` | 616 |
| external_call | `_coerce_packet_bytes` | `isinstance` | 618 |
| external_call | `_coerce_packet_bytes` | `bytes` | 619 |
| external_call | `_coerce_packet_bytes` | `TypeError` | 621 |
| unresolved_call | `_coerce_packet_bytes` | `raw.startswith` | 629 |
| step_limit | `compare_context_packet_basis` | `first 12 steps` | 0 |
| truncated_flow | `compare_context_packet_basis` | `depth limit` | 0 |

## Behavior

This flow starts at `compare_context_packet_basis` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
