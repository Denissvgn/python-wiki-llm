# require_receipt_authentication

**Entry point:** `require_receipt_authentication` (`api`)
**Source:** [host_broker](../modules/host_broker.md)
**Modules touched:** [host_broker](../modules/host_broker.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_receipt_authentication
    participant p1 as require_process_host_broker_authenticator
    participant p2 as get
    participant p3 as HostBrokerAuthenticationUnavailable
    participant p4 as isinstance
    participant p5 as _require_bounded_text
    participant p6 as require_bounded_text
    participant p7 as len
    participant p8 as strip
    participant p9 as any
    participant p10 as ord
    participant p11 as HostBrokerAuthenticationError
    participant p12 as authenticate_receipt
    p0->>p1: require_process_host_broker_authenticator
    p1-->>p2: get
    p1->>p3: HostBrokerAuthenticationUnavailable
    p1-->>p4: isinstance
    p1->>p3: HostBrokerAuthenticationUnavailable
    p1->>p5: _require_bounded_text
    p5->>p6: require_bounded_text
    p6-->>p4: isinstance
    p6-->>p7: len
    p6-->>p7: len
    p6-->>p8: strip
    p6-->>p9: any
    p6-->>p10: ord
    p6-->>p10: ord
    p5->>p11: HostBrokerAuthenticationError
    p0-->>p12: authenticate_receipt
    p0->>p11: HostBrokerAuthenticationError
    p0-->>p4: isinstance
    p0->>p11: HostBrokerAuthenticationError
    p0->>p11: HostBrokerAuthenticationError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_receipt_authentication"]
    s2["2. require_process_host_broker_authenticator"]
    s3["3. get"]
    s4["4. HostBrokerAuthenticationUnavailable"]
    s5["5. isinstance"]
    s6["6. HostBrokerAuthenticationUnavailable"]
    s7["7. _require_bounded_text"]
    s8["8. require_bounded_text"]
    s9["9. isinstance"]
    s10["10. len"]
    s11["11. len"]
    s12["12. strip"]
    s1 -->|"require_process_host_broker_authenticator(data not statically known)"| s2
    s2 -. "_HOST_BROKER_AUTHENTICATOR.get(data not statically known)" .-> s3
    s2 -->|"HostBrokerAuthenticationUnavailable('External admission requires a separately authenticated host broker; this process has no host authenticator.')"| s4
    s2 -. "isinstance(authenticator, HostBrokerAuthenticator)" .-> s5
    s2 -->|"HostBrokerAuthenticationUnavailable('The process host broker authenticator is malformed.')"| s6
    s2 -->|"_require_bounded_text(authenticator.authenticator_id, 'authenticator_id')"| s7
    s7 -->|"require_bounded_text(value, maximum=512, error=HostBrokerAuthenticationError(...))"| s8
    s8 -. "isinstance(value, str)" .-> s9
    s8 -. "len(value)" .-> s10
    s8 -. "len(value)" .-> s11
    s8 -. "value.strip(data not statically known)" .-> s12
    click s1 "../modules/host_broker.md"
    click s2 "../modules/host_broker.md"
    click s4 "../modules/host_broker.md"
    click s6 "../modules/host_broker.md"
    click s7 "../modules/host_broker.md"
    click s8 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_receipt_authentication` | `cohort_id: str`, `execution_manifest: Mapping[str, Any]`, `attestation: Mapping[str, Any]`, `receipt: Mapping[str, Any]`, `receipt_hash: str`, `result: Mapping[str, Any]`, `result_hash: str` | `HostBrokerAuthenticationProof` | - | `proof` |
| `require_process_host_broker_authenticator` | - | `HostBrokerAuthenticator` | - | `authenticator` |
| `get` | - | - | - | - |
| `HostBrokerAuthenticationUnavailable` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `HostBrokerAuthenticationUnavailable` | - | - | - | - |
| `_require_bounded_text` | `value: Any`, `label: str` | - | - | `require_bounded_text(...)` |
| `require_bounded_text` | `value: object`, `maximum: int`, `error: Exception`, `minimum: int`, `control_error: Exception \| None`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `len` | - | - | - | - |
| `len` | - | - | - | - |
| `strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_receipt_authentication | require_process_host_broker_authenticator | 294 | `require_process_host_broker_authenticator(data not statically known)` |
| require_process_host_broker_authenticator | get | 234 | `_HOST_BROKER_AUTHENTICATOR.get(data not statically known)` |
| require_process_host_broker_authenticator | HostBrokerAuthenticationUnavailable | 236 | `HostBrokerAuthenticationUnavailable('External admission requires a separately authenticated host broker; this process has no host authenticator.')` |
| require_process_host_broker_authenticator | isinstance | 240 | `isinstance(authenticator, HostBrokerAuthenticator)` |
| require_process_host_broker_authenticator | HostBrokerAuthenticationUnavailable | 241 | `HostBrokerAuthenticationUnavailable('The process host broker authenticator is malformed.')` |
| require_process_host_broker_authenticator | _require_bounded_text | 244 | `_require_bounded_text(authenticator.authenticator_id, 'authenticator_id')` |
| _require_bounded_text | require_bounded_text | 321 | `require_bounded_text(value, maximum=512, error=HostBrokerAuthenticationError(...))` |
| require_bounded_text | isinstance | 605 | `isinstance(value, str)` |
| require_bounded_text | len | 606 | `len(value)` |
| require_bounded_text | len | 607 | `len(value)` |
| require_bounded_text | strip | 608 | `value.strip(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_process_host_broker_authenticator` | `_HOST_BROKER_AUTHENTICATOR.get` | 234 |
| unresolved_call | `require_process_host_broker_authenticator` | `isinstance` | 240 |
| unresolved_call | `require_bounded_text` | `isinstance` | 605 |
| unresolved_call | `require_bounded_text` | `value.strip` | 608 |
| step_limit | `require_receipt_authentication` | `first 12 steps` | 0 |

## Behavior

This flow starts at `require_receipt_authentication` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
