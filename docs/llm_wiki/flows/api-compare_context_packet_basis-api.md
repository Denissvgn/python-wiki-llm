# compare_context_packet_basis

**Entry point:** `compare_context_packet_basis` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [context_packet](../modules/context_packet.md), [context_service](../modules/context_service.md), [knowledge_evidence](../modules/knowledge_evidence.md), and 2 more

**Complete modules touched:**

- [api](../modules/api.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [maintenance_status](../modules/maintenance_status.md)
- [packet_field_policy](../modules/packet_field_policy.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_context_packet_basis (src/llm_wiki_cli/api.py)
    participant p1 as compare_context_packet_basis (src/llm_wiki_cli/services/context_packet.py)
    participant p2 as _raise_context_packet_api_error
    participant p3 as validate_context_packet
    participant p4 as _raise_required_knowledge_api_error
    participant p5 as _coerce_packet_bytes
    participant p6 as _strict_json_payload
    participant p7 as _packet_contract_for_schema
    participant p8 as _validate_packet_shape
    participant p9 as _encode_packet_payload
    participant p10 as _packet_id
    participant p11 as _path_policy_receipt
    participant p12 as QualifiedContextPacket._from_validated_payload
    participant p13 as _exact_fields
    participant p14 as canonical_json_bytes
    participant p15 as _freeze_json
    participant p16 as _validate_assurance
    participant p17 as _validate_packet_request
    participant p18 as _validate_response
    participant p19 as _validate_basis
    participant p20 as _validate_response_basis_consistency
    participant p21 as _validate_delivery
    participant p22 as _validate_path_policy_shape
    participant p23 as _mapping
    participant p24 as _validate_protocol_request
    participant p25 as _path_policy_digest
    participant p26 as _nonnegative_integer
    participant p27 as _validate_repository_basis
    participant p28 as _validate_knowledge_basis
    participant p29 as isinstance (src/llm_wiki_cli/services…pare_context_packet_basis)
    participant p30 as leaf
    p0->>p1: compare_context_packet_basis (src/llm_wiki_cli/services/context_packet.py)
    p0->>p2: _raise_context_packet_api_error
    p1->>p3: validate_context_packet
    p2->>p4: _raise_required_knowledge_api_error
    p3->>p5: _coerce_packet_bytes
    p3->>p6: _strict_json_payload
    p3->>p7: _packet_contract_for_schema
    p3->>p8: _validate_packet_shape
    p3->>p9: _encode_packet_payload
    p3->>p10: _packet_id
    p3->>p11: _path_policy_receipt
    p3->>p12: QualifiedContextPacket._from_validated_payload
    p8->>p13: _exact_fields
    p9->>p14: canonical_json_bytes
    p12->>p15: _freeze_json
    p8->>p16: _validate_assurance
    p8->>p17: _validate_packet_request
    p8->>p18: _validate_response
    p8->>p19: _validate_basis
    p8->>p20: _validate_response_basis_consistency
    p8->>p21: _validate_delivery
    p8->>p22: _validate_path_policy_shape
    p16->>p23: _mapping
    p17->>p24: _validate_protocol_request
    p22->>p25: _path_policy_digest
    p19->>p26: _nonnegative_integer
    p19->>p27: _validate_repository_basis
    p19->>p28: _validate_knowledge_basis
    p1-->>p29: isinstance (src/llm_wiki_cli/services…pare_context_packet_basis)(expected_basis, Mapping)
    p2-->>p30: leaf(failure[...], code=failure[...], details=failure[...])
```

> Call sequence diagram shows 30 of 470 interactions; 440 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 143 (142 omitted); unresolved 1 of 94 (93 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/context_packet.py:_coerce_packet_bytes` | 4 | - | external | 5 |
| `src/llm_wiki_cli/services/context_packet.py:_coerce_packet_bytes` | 4 | [src/llm_wiki_cli/services/context_packet.py](../modules/context_packet.md) | internal | 4 |
| `src/llm_wiki_cli/services/context_packet.py:_coerce_packet_bytes` | 4 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/context_packet.py:_strict_json_payload` | 17 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/context_packet.py:_strict_json_payload` | 17 | [src/llm_wiki_cli/services/context_packet.py](../modules/context_packet.md) | internal | 4 |
| `src/llm_wiki_cli/services/context_packet.py:_strict_json_payload` | 17 | - | external | 2 |
| `src/llm_wiki_cli/services/context_packet.py:_validate_json_tree` | 24 | - | external | 1 |
| `src/llm_wiki_cli/services/context_packet.py:_validate_json_tree` | 24 | - | unresolved | 1 |
> Omission summary shows 8 of 109 groups; 101 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 234; effect analysis evaluated: 112, partial: 2, unavailable: 120. Counts include steps omitted from the displayed trace.

Collector observations for 114 source steps with known totals: observed: 478, emitted: 471, omitted: 7. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `compare_context_packet_basis (src/llm_wiki_cli/api.py)` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `compare_context_packet_basis (src/llm_wiki_cli/services/context_packet.py)` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `validate_context_packet` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_coerce_packet_bytes` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ContextPacketMalformedError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ContextPacketMalformedError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `raw.startswith` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. compare_context_packet_basis (src/llm_wiki_cli/api.py)"]
    s2["2. compare_context_packet_basis (src/llm_wiki_cli/services/context_packet.py)"]
    s3["3. validate_context_packet"]
    s4["4. _coerce_packet_bytes"]
    s5["5. isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s6["6. isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s7["7. bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s8["8. TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s9["9. ContextPacketMalformedError"]
    s10["10. len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s11["11. ContextPacketMalformedError"]
    s12["12. raw.startswith"]
    s1 -->|"compare_context_packet_basis (src/llm_wiki_cli/services/context_packet.py)(packet_bytes, expected_basis)"| s2
    s2 -->|"validate_context_packet(packet_bytes)"| s3
    s3 -->|"_coerce_packet_bytes(packet_bytes)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value, bytes)" .-> s5
    s4 -. "isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value, (...))" .-> s6
    s4 -. "bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value)" .-> s7
    s4 -. "TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)('packet_bytes must be bytes-like')" .-> s8
    s4 -->|"ContextPacketMalformedError('packet_bytes', 'must not be empty')"| s9
    s4 -. "len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(raw)" .-> s10
    s4 -->|"ContextPacketMalformedError('packet_bytes', ...)"| s11
    s4 -. "raw.startswith(b'\xef\xbb\xbf')" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/context_packet.md"
    click s3 "../modules/context_packet.md"
    click s4 "../modules/context_packet.md"
    click s9 "../modules/context_packet.md"
    click s11 "../modules/context_packet.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compare_context_packet_basis (src/llm_wiki_cli/api.py)` | `packet_bytes: bytes \| bytearray \| memoryview`, `expected_basis: Mapping[str, Any]` | `context_packet_service` | - | `comparison` |
| `compare_context_packet_basis (src/llm_wiki_cli/services/context_packet.py)` | `packet_bytes: bytes \| bytearray \| memoryview`, `expected_basis: Mapping[str, Any]` | `Mapping` | - | `ContextBasisComparison(...)` |
| `validate_context_packet` | `packet_bytes: bytes \| bytearray \| memoryview` | - | - | `ContextPacketValidation(...)` |
| `_coerce_packet_bytes` | `value: bytes \| bytearray \| memoryview` | `_MAX_PACKET_BYTES`, `_MAX_PACKET_BYTES` | - | `raw` |
| `isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |
| `len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |
| `raw.startswith` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compare_context_packet_basis (src/llm_wiki_cli/api.py) | compare_context_packet_basis (src/llm_wiki_cli/services/context_packet.py) | 1774 | `context_packet_service.compare_context_packet_basis(packet_bytes, expected_basis)` |
| compare_context_packet_basis (src/llm_wiki_cli/services/context_packet.py) | validate_context_packet | 1820 | `validate_context_packet(packet_bytes)` |
| validate_context_packet | _coerce_packet_bytes | 1771 | `_coerce_packet_bytes(packet_bytes)` |
| _coerce_packet_bytes | isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2547 | `isinstance(value, bytes)` |
| _coerce_packet_bytes | isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2549 | `isinstance(value, (...))` |
| _coerce_packet_bytes | bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2550 | `bytes(value)` |
| _coerce_packet_bytes | TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2552 | `TypeError('packet_bytes must be bytes-like')` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2554 | `ContextPacketMalformedError('packet_bytes', 'must not be empty')` |
| _coerce_packet_bytes | len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2555 | `len(raw)` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2556 | `ContextPacketMalformedError('packet_bytes', ...)` |
| _coerce_packet_bytes | raw.startswith | 2560 | `raw.startswith(b'\xef\xbb\xbf')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_coerce_packet_bytes` | `isinstance` | 2547 |
| external_call | `_coerce_packet_bytes` | `isinstance` | 2549 |
| external_call | `_coerce_packet_bytes` | `bytes` | 2550 |
| external_call | `_coerce_packet_bytes` | `TypeError` | 2552 |
| unresolved_call | `_coerce_packet_bytes` | `raw.startswith` | 2560 |
| step_limit | `compare_context_packet_basis` | `first 12 steps` | 0 |
| truncated_flow | `compare_context_packet_basis` | `depth limit` | 0 |

## Behavior

This flow starts at `compare_context_packet_basis` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
