# compare_context_packet_basis

**Entry point:** `compare_context_packet_basis` (`api`)
**Source:** [context_packet](../modules/context_packet.md)
**Modules touched:** [context_packet](../modules/context_packet.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_context_packet_basis
    participant p1 as validate_context_packet
    participant p2 as _coerce_packet_bytes
    participant p3 as isinstance
    participant p4 as bytes
    participant p5 as TypeError
    participant p6 as ContextPacketMalformedError
    participant p7 as len
    participant p8 as startswith
    participant p9 as endswith
    participant p10 as _strict_json_payload
    participant p11 as decode
    participant p12 as loads
    participant p13 as _validate_json_tree
    participant p14 as set
    participant p15 as visit
    participant p16 as _packet_contract_for_schema
    participant p17 as get
    p0->>p1: validate_context_packet
    p1->>p2: _coerce_packet_bytes
    p2-->>p3: isinstance
    p2-->>p3: isinstance
    p2-->>p4: bytes
    p2-->>p5: TypeError
    p2->>p6: ContextPacketMalformedError
    p2-->>p7: len
    p2->>p6: ContextPacketMalformedError
    p2-->>p8: startswith
    p2->>p6: ContextPacketMalformedError
    p2-->>p9: endswith
    p2-->>p9: endswith
    p2->>p6: ContextPacketMalformedError
    p1->>p10: _strict_json_payload
    p10-->>p11: decode
    p10->>p6: ContextPacketMalformedError
    p10-->>p12: loads
    p10->>p6: ContextPacketMalformedError
    p10-->>p3: isinstance
    p10->>p6: ContextPacketMalformedError
    p10->>p13: _validate_json_tree
    p13-->>p14: set
    p13-->>p15: visit
    p1->>p16: _packet_contract_for_schema
    p16-->>p3: isinstance
    p16->>p6: ContextPacketMalformedError
    p16-->>p17: get
    p16->>p6: ContextPacketMalformedError
    p1-->>p17: get
```

> Call sequence diagram shows 30 of 499 interactions; 469 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. compare_context_packet_basis"]
    s2["2. validate_context_packet"]
    s3["3. _coerce_packet_bytes"]
    s4["4. isinstance"]
    s5["5. isinstance"]
    s6["6. bytes"]
    s7["7. TypeError"]
    s8["8. ContextPacketMalformedError"]
    s9["9. len"]
    s10["10. ContextPacketMalformedError"]
    s11["11. startswith"]
    s12["12. ContextPacketMalformedError"]
    s1 -->|"validate_context_packet(packet_bytes)"| s2
    s2 -->|"_coerce_packet_bytes(packet_bytes)"| s3
    s3 -. "isinstance(value, bytes)" .-> s4
    s3 -. "isinstance(value, (...))" .-> s5
    s3 -. "bytes(value)" .-> s6
    s3 -. "TypeError('packet_bytes must be bytes-like')" .-> s7
    s3 -->|"ContextPacketMalformedError('packet_bytes', 'must not be empty')"| s8
    s3 -. "len(raw)" .-> s9
    s3 -->|"ContextPacketMalformedError('packet_bytes', ...)"| s10
    s3 -. "raw.startswith(b'\xef\xbb\xbf')" .-> s11
    s3 -->|"ContextPacketMalformedError('packet_bytes', 'must not contain a UTF-8 byte-order mark')"| s12
    click s1 "../modules/context_packet.md"
    click s2 "../modules/context_packet.md"
    click s3 "../modules/context_packet.md"
    click s8 "../modules/context_packet.md"
    click s10 "../modules/context_packet.md"
    click s12 "../modules/context_packet.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compare_context_packet_basis` | `packet_bytes: bytes \| bytearray \| memoryview`, `expected_basis: Mapping[str, Any]` | `Mapping` | - | `ContextBasisComparison(...)` |
| `validate_context_packet` | `packet_bytes: bytes \| bytearray \| memoryview` | - | - | `ContextPacketValidation(...)` |
| `_coerce_packet_bytes` | `value: bytes \| bytearray \| memoryview` | `_MAX_PACKET_BYTES`, `_MAX_PACKET_BYTES` | - | `raw` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `bytes` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |
| `len` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |
| `startswith` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compare_context_packet_basis | validate_context_packet | 1537 | `validate_context_packet(packet_bytes)` |
| validate_context_packet | _coerce_packet_bytes | 1488 | `_coerce_packet_bytes(packet_bytes)` |
| _coerce_packet_bytes | isinstance | 2251 | `isinstance(value, bytes)` |
| _coerce_packet_bytes | isinstance | 2253 | `isinstance(value, (...))` |
| _coerce_packet_bytes | bytes | 2254 | `bytes(value)` |
| _coerce_packet_bytes | TypeError | 2256 | `TypeError('packet_bytes must be bytes-like')` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2258 | `ContextPacketMalformedError('packet_bytes', 'must not be empty')` |
| _coerce_packet_bytes | len | 2259 | `len(raw)` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2260 | `ContextPacketMalformedError('packet_bytes', ...)` |
| _coerce_packet_bytes | startswith | 2264 | `raw.startswith(b'\xef\xbb\xbf')` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2265 | `ContextPacketMalformedError('packet_bytes', 'must not contain a UTF-8 byte-order mark')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_coerce_packet_bytes` | `isinstance` | 2251 |
| unresolved_call | `_coerce_packet_bytes` | `isinstance` | 2253 |
| unresolved_call | `_coerce_packet_bytes` | `bytes` | 2254 |
| unresolved_call | `_coerce_packet_bytes` | `TypeError` | 2256 |
| unresolved_call | `_coerce_packet_bytes` | `raw.startswith` | 2264 |
| step_limit | `compare_context_packet_basis` | `first 12 steps` | 0 |
| truncated_flow | `compare_context_packet_basis` | `depth limit` | 0 |

## Behavior

This flow starts at `compare_context_packet_basis` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
