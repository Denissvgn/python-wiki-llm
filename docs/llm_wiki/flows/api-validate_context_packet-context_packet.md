# validate_context_packet

**Entry point:** `validate_context_packet` (`api`)
**Source:** [context_packet](../modules/context_packet.md)
**Modules touched:** [context_packet](../modules/context_packet.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_context_packet
    participant p1 as _coerce_packet_bytes
    participant p2 as isinstance
    participant p3 as bytes
    participant p4 as TypeError
    participant p5 as ContextPacketMalformedError
    participant p6 as len
    participant p7 as startswith
    participant p8 as endswith
    participant p9 as _strict_json_payload
    participant p10 as decode
    participant p11 as loads
    participant p12 as _validate_json_tree
    participant p13 as set
    participant p14 as visit
    participant p15 as _validate_packet_shape
    participant p16 as _exact_fields
    participant p17 as sorted
    p0->>p1: _coerce_packet_bytes
    p1-->>p2: isinstance
    p1-->>p2: isinstance
    p1-->>p3: bytes
    p1-->>p4: TypeError
    p1->>p5: ContextPacketMalformedError
    p1-->>p6: len
    p1->>p5: ContextPacketMalformedError
    p1-->>p7: startswith
    p1->>p5: ContextPacketMalformedError
    p1-->>p8: endswith
    p1-->>p8: endswith
    p1->>p5: ContextPacketMalformedError
    p0->>p9: _strict_json_payload
    p9-->>p10: decode
    p9->>p5: ContextPacketMalformedError
    p9-->>p11: loads
    p9->>p5: ContextPacketMalformedError
    p9-->>p2: isinstance
    p9->>p5: ContextPacketMalformedError
    p9->>p12: _validate_json_tree
    p12-->>p13: set
    p12-->>p14: visit
    p0->>p15: _validate_packet_shape
    p15->>p16: _exact_fields
    p16-->>p13: set
    p16-->>p17: sorted
    p16-->>p13: set
    p16->>p5: ContextPacketMalformedError
    p16-->>p17: sorted
```

> Call sequence diagram shows 30 of 212 interactions; 182 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_context_packet"]
    s2["2. _coerce_packet_bytes"]
    s3["3. isinstance"]
    s4["4. isinstance"]
    s5["5. bytes"]
    s6["6. TypeError"]
    s7["7. ContextPacketMalformedError"]
    s8["8. len"]
    s9["9. ContextPacketMalformedError"]
    s10["10. startswith"]
    s11["11. ContextPacketMalformedError"]
    s12["12. endswith"]
    s1 -->|"_coerce_packet_bytes(packet_bytes)"| s2
    s2 -. "isinstance(value, bytes)" .-> s3
    s2 -. "isinstance(value, (...))" .-> s4
    s2 -. "bytes(value)" .-> s5
    s2 -. "TypeError('packet_bytes must be bytes-like')" .-> s6
    s2 -->|"ContextPacketMalformedError('packet_bytes', 'must not be empty')"| s7
    s2 -. "len(raw)" .-> s8
    s2 -->|"ContextPacketMalformedError('packet_bytes', ...)"| s9
    s2 -. "raw.startswith(b'\xef\xbb\xbf')" .-> s10
    s2 -->|"ContextPacketMalformedError('packet_bytes', 'must not contain a UTF-8 byte-order mark')"| s11
    s2 -. "raw.endswith(b'\n')" .-> s12
    click s1 "../modules/context_packet.md"
    click s2 "../modules/context_packet.md"
    click s7 "../modules/context_packet.md"
    click s9 "../modules/context_packet.md"
    click s11 "../modules/context_packet.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `endswith` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_context_packet | _coerce_packet_bytes | 859 | `_coerce_packet_bytes(packet_bytes)` |
| _coerce_packet_bytes | isinstance | 1557 | `isinstance(value, bytes)` |
| _coerce_packet_bytes | isinstance | 1559 | `isinstance(value, (...))` |
| _coerce_packet_bytes | bytes | 1560 | `bytes(value)` |
| _coerce_packet_bytes | TypeError | 1562 | `TypeError('packet_bytes must be bytes-like')` |
| _coerce_packet_bytes | ContextPacketMalformedError | 1564 | `ContextPacketMalformedError('packet_bytes', 'must not be empty')` |
| _coerce_packet_bytes | len | 1565 | `len(raw)` |
| _coerce_packet_bytes | ContextPacketMalformedError | 1566 | `ContextPacketMalformedError('packet_bytes', ...)` |
| _coerce_packet_bytes | startswith | 1570 | `raw.startswith(b'\xef\xbb\xbf')` |
| _coerce_packet_bytes | ContextPacketMalformedError | 1571 | `ContextPacketMalformedError('packet_bytes', 'must not contain a UTF-8 byte-order mark')` |
| _coerce_packet_bytes | endswith | 1575 | `raw.endswith(b'\n')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_coerce_packet_bytes` | `isinstance` | 1557 |
| unresolved_call | `_coerce_packet_bytes` | `isinstance` | 1559 |
| unresolved_call | `_coerce_packet_bytes` | `bytes` | 1560 |
| unresolved_call | `_coerce_packet_bytes` | `TypeError` | 1562 |
| unresolved_call | `_coerce_packet_bytes` | `raw.startswith` | 1570 |
| unresolved_call | `_coerce_packet_bytes` | `raw.endswith` | 1575 |
| step_limit | `validate_context_packet` | `first 12 steps` | 0 |
| truncated_flow | `validate_context_packet` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_context_packet` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
