# validate_context_packet

**Entry point:** `validate_context_packet` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [context_budget](../modules/context_budget.md), [context_packet](../modules/context_packet.md), [context_service](../modules/context_service.md), and 4 more

**Complete modules touched:**

- [api](../modules/api.md)
- [context_budget](../modules/context_budget.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [maintenance_status](../modules/maintenance_status.md)
- [packet_field_policy](../modules/packet_field_policy.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_context_packet (src/llm_wiki_cli/api.py)
    participant p1 as validate_context_packet (src/llm_wiki_cli/services/context_packet.py)
    participant p2 as _raise_context_packet_api_error
    participant p3 as _coerce_packet_bytes
    participant p4 as _raise_required_knowledge_api_error
    participant p5 as _strict_json_payload
    participant p6 as describe_context_packet_error
    participant p7 as _packet_contract_for_schema
    participant p8 as leaf
    participant p9 as payload.get
    participant p10 as len (src/llm_wiki_cli/services…y:validate_context_packet)
    participant p11 as ContextPacketMalformedError
    participant p12 as _validate_packet_shape
    participant p13 as _encode_packet_payload
    participant p14 as payload.items
    participant p15 as _packet_id
    participant p16 as _path_policy_receipt
    participant p17 as ContextPacketPathPolicyError
    participant p18 as QualifiedContextPacket._from_validated_payload
    participant p19 as ContextPacketValidation
    participant p20 as isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)
    participant p21 as raw.decode
    participant p22 as isinstance (src/llm_wiki_cli/services…acket_contract_for_schema)
    participant p23 as _exact_fields
    participant p24 as _validate_json_tree
    participant p25 as validate_field_coverage
    participant p26 as QualifiedContextPacket
    p0->>p1: validate_context_packet (src/llm_wiki_cli/services/context_packet.py)
    p0->>p2: _raise_context_packet_api_error
    p1->>p3: _coerce_packet_bytes
    p2->>p4: _raise_required_knowledge_api_error
    p1->>p5: _strict_json_payload
    p2->>p6: describe_context_packet_error
    p1->>p7: _packet_contract_for_schema
    p2-->>p8: leaf(failure[...], code=failure[...], details=failure[...])
    p1-->>p9: payload.get('schema_version')
    p1-->>p10: len (src/llm_wiki_cli/services…y:validate_context_packet)(raw)
    p1->>p11: ContextPacketMalformedError
    p1->>p12: _validate_packet_shape
    p1->>p13: _encode_packet_payload
    p1->>p11: ContextPacketMalformedError
    p1-->>p14: payload.items
    p1->>p15: _packet_id
    p1->>p11: ContextPacketMalformedError
    p1-->>p14: payload.items
    p1->>p16: _path_policy_receipt
    p1->>p17: ContextPacketPathPolicyError
    p1->>p18: QualifiedContextPacket._from_validated_payload
    p1->>p19: ContextPacketValidation
    p3-->>p20: isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value, bytes)
    p5-->>p21: raw.decode('utf-8')
    p7-->>p22: isinstance (src/llm_wiki_cli/services…acket_contract_for_schema)(schema_version, str)
    p12->>p23: _exact_fields
    p13->>p24: _validate_json_tree
    p15->>p7: _packet_contract_for_schema
    p16->>p25: validate_field_coverage
    p18->>p26: QualifiedContextPacket
```

> Call sequence diagram shows 30 of 611 interactions; 581 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 205 (202 omitted); unresolved 5 of 114 (109 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/context_packet.py:_coerce_packet_bytes` | 3 | - | external | 4 |
| `src/llm_wiki_cli/services/context_packet.py:_coerce_packet_bytes` | 3 | [src/llm_wiki_cli/services/context_packet.py](../modules/context_packet.md) | internal | 4 |
| `src/llm_wiki_cli/services/context_packet.py:_coerce_packet_bytes` | 3 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/context_packet.py:_strict_json_payload` | 16 | [src/llm_wiki_cli/services/context_packet.py](../modules/context_packet.md) | internal | 4 |
| `src/llm_wiki_cli/services/context_packet.py:_strict_json_payload` | 16 | - | external | 2 |
| `src/llm_wiki_cli/services/context_packet.py:_validate_json_tree` | 23 | - | external | 1 |
| `src/llm_wiki_cli/services/context_packet.py:_validate_json_tree` | 23 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/context_packet.py:_packet_contract_for_schema` | 26 | [src/llm_wiki_cli/services/context_packet.py](../modules/context_packet.md) | internal | 2 |
> Omission summary shows 8 of 113 groups; 105 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_context_packet (src/llm_wiki_cli/api.py)"]
    s2["2. validate_context_packet (src/llm_wiki_cli/services/context_packet.py)"]
    s3["3. _coerce_packet_bytes"]
    s4["4. isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s5["5. isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s6["6. bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s7["7. TypeError"]
    s8["8. ContextPacketMalformedError"]
    s9["9. len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s10["10. ContextPacketMalformedError"]
    s11["11. raw.startswith"]
    s12["12. ContextPacketMalformedError"]
    s1 -->|"validate_context_packet (src/llm_wiki_cli/services/context_packet.py)(packet_bytes)"| s2
    s2 -->|"_coerce_packet_bytes(packet_bytes)"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value, bytes)" .-> s4
    s3 -. "isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value, (...))" .-> s5
    s3 -. "bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value)" .-> s6
    s3 -. "TypeError('packet_bytes must be bytes-like')" .-> s7
    s3 -->|"ContextPacketMalformedError('packet_bytes', 'must not be empty')"| s8
    s3 -. "len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(raw)" .-> s9
    s3 -->|"ContextPacketMalformedError('packet_bytes', ...)"| s10
    s3 -. "raw.startswith(b'\xef\xbb\xbf')" .-> s11
    s3 -->|"ContextPacketMalformedError('packet_bytes', 'must not contain a UTF-8 byte-order mark')"| s12
    click s1 "../modules/api.md"
    click s2 "../modules/context_packet.md"
    click s3 "../modules/context_packet.md"
    click s8 "../modules/context_packet.md"
    click s10 "../modules/context_packet.md"
    click s12 "../modules/context_packet.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_context_packet (src/llm_wiki_cli/api.py)` | `packet_bytes: bytes \| bytearray \| memoryview` | `context_packet_service` | - | `validation` |
| `validate_context_packet (src/llm_wiki_cli/services/context_packet.py)` | `packet_bytes: bytes \| bytearray \| memoryview` | - | - | `ContextPacketValidation(...)` |
| `_coerce_packet_bytes` | `value: bytes \| bytearray \| memoryview` | `_MAX_PACKET_BYTES`, `_MAX_PACKET_BYTES` | - | `raw` |
| `isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |
| `len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |
| `raw.startswith` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_context_packet (src/llm_wiki_cli/api.py) | validate_context_packet (src/llm_wiki_cli/services/context_packet.py) | 1753 | `context_packet_service.validate_context_packet(packet_bytes)` |
| validate_context_packet (src/llm_wiki_cli/services/context_packet.py) | _coerce_packet_bytes | 1712 | `_coerce_packet_bytes(packet_bytes)` |
| _coerce_packet_bytes | isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2493 | `isinstance(value, bytes)` |
| _coerce_packet_bytes | isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2495 | `isinstance(value, (...))` |
| _coerce_packet_bytes | bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2496 | `bytes(value)` |
| _coerce_packet_bytes | TypeError | 2498 | `TypeError('packet_bytes must be bytes-like')` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2500 | `ContextPacketMalformedError('packet_bytes', 'must not be empty')` |
| _coerce_packet_bytes | len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2501 | `len(raw)` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2502 | `ContextPacketMalformedError('packet_bytes', ...)` |
| _coerce_packet_bytes | raw.startswith | 2506 | `raw.startswith(b'\xef\xbb\xbf')` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2507 | `ContextPacketMalformedError('packet_bytes', 'must not contain a UTF-8 byte-order mark')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_coerce_packet_bytes` | `isinstance` | 2493 |
| external_call | `_coerce_packet_bytes` | `isinstance` | 2495 |
| external_call | `_coerce_packet_bytes` | `bytes` | 2496 |
| external_call | `_coerce_packet_bytes` | `TypeError` | 2498 |
| unresolved_call | `_coerce_packet_bytes` | `raw.startswith` | 2506 |
| step_limit | `validate_context_packet` | `first 12 steps` | 0 |
| truncated_flow | `validate_context_packet` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_context_packet` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
