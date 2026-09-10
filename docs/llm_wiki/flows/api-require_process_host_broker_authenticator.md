# require_process_host_broker_authenticator

**Entry point:** `require_process_host_broker_authenticator` (`api`)
**Source:** [host_broker](../modules/host_broker.md)
**Modules touched:** [host_broker](../modules/host_broker.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_process_host_broker_authenticator
    participant p1 as _HOST_BROKER_AUTHENTICATOR.get
    participant p2 as HostBrokerAuthenticationUnavailable
    participant p3 as isinstance (src/llm_wiki_cli/services…_host_broker_authenticator)
    participant p4 as _require_bounded_text
    participant p5 as require_bounded_text
    participant p6 as isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text)
    participant p7 as len
    participant p8 as value.strip
    participant p9 as any
    participant p10 as ord
    participant p11 as HostBrokerAuthenticationError
    p0-->>p1: _HOST_BROKER_AUTHENTICATOR.get
    p0->>p2: HostBrokerAuthenticationUnavailable
    p0-->>p3: isinstance (src/llm_wiki_cli/services…_host_broker_authenticator)
    p0->>p2: HostBrokerAuthenticationUnavailable
    p0->>p4: _require_bounded_text
    p4->>p5: require_bounded_text
    p5-->>p6: isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text)
    p5-->>p7: len
    p5-->>p7: len
    p5-->>p8: value.strip
    p5-->>p9: any
    p5-->>p10: ord
    p5-->>p10: ord
    p4->>p11: HostBrokerAuthenticationError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_process_host_broker_authenticator"]
    s2["2. _HOST_BROKER_AUTHENTICATOR.get"]
    s3["3. HostBrokerAuthenticationUnavailable"]
    s4["4. isinstance (src/llm_wiki_cli/services…_host_broker_authenticator)"]
    s5["5. HostBrokerAuthenticationUnavailable"]
    s6["6. _require_bounded_text"]
    s7["7. require_bounded_text"]
    s8["8. isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text)"]
    s9["9. len"]
    s10["10. len"]
    s11["11. value.strip"]
    s12["12. any"]
    s1 -. "_HOST_BROKER_AUTHENTICATOR.get(data not statically known)" .-> s2
    s1 -->|"HostBrokerAuthenticationUnavailable('External admission requires a separately authenticated host broker; this process has no host authenticator.')"| s3
    s1 -. "isinstance (src/llm_wiki_cli/services…_host_broker_authenticator)(authenticator, HostBrokerAuthenticator)" .-> s4
    s1 -->|"HostBrokerAuthenticationUnavailable('The process host broker authenticator is malformed.')"| s5
    s1 -->|"_require_bounded_text(authenticator.authenticator_id, 'authenticator_id')"| s6
    s6 -->|"require_bounded_text(value, maximum=512, error=HostBrokerAuthenticationError(...))"| s7
    s7 -. "isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text)(value, str)" .-> s8
    s7 -. "len(value)" .-> s9
    s7 -. "len(value)" .-> s10
    s7 -. "value.strip(data not statically known)" .-> s11
    s7 -. "any(...)" .-> s12
    click s1 "../modules/host_broker.md"
    click s3 "../modules/host_broker.md"
    click s5 "../modules/host_broker.md"
    click s6 "../modules/host_broker.md"
    click s7 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_process_host_broker_authenticator` | - | `HostBrokerAuthenticator` | - | `authenticator` |
| `_HOST_BROKER_AUTHENTICATOR.get` | - | - | - | - |
| `HostBrokerAuthenticationUnavailable` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…_host_broker_authenticator)` | - | - | - | - |
| `HostBrokerAuthenticationUnavailable` | - | - | - | - |
| `_require_bounded_text` | `value: Any`, `label: str` | - | - | `require_bounded_text(...)` |
| `require_bounded_text` | `value: object`, `maximum: int`, `error: Exception`, `minimum: int`, `control_error: Exception \| None`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text)` | - | - | - | - |
| `len` | - | - | - | - |
| `len` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `any` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_process_host_broker_authenticator | _HOST_BROKER_AUTHENTICATOR.get | 234 | `_HOST_BROKER_AUTHENTICATOR.get(data not statically known)` |
| require_process_host_broker_authenticator | HostBrokerAuthenticationUnavailable | 236 | `HostBrokerAuthenticationUnavailable('External admission requires a separately authenticated host broker; this process has no host authenticator.')` |
| require_process_host_broker_authenticator | isinstance (src/llm_wiki_cli/services…_host_broker_authenticator) | 240 | `isinstance(authenticator, HostBrokerAuthenticator)` |
| require_process_host_broker_authenticator | HostBrokerAuthenticationUnavailable | 241 | `HostBrokerAuthenticationUnavailable('The process host broker authenticator is malformed.')` |
| require_process_host_broker_authenticator | _require_bounded_text | 244 | `_require_bounded_text(authenticator.authenticator_id, 'authenticator_id')` |
| _require_bounded_text | require_bounded_text | 321 | `require_bounded_text(value, maximum=512, error=HostBrokerAuthenticationError(...))` |
| require_bounded_text | isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text) | 605 | `isinstance(value, str)` |
| require_bounded_text | len | 606 | `len(value)` |
| require_bounded_text | len | 607 | `len(value)` |
| require_bounded_text | value.strip | 608 | `value.strip(data not statically known)` |
| require_bounded_text | any | 611 | `any(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_process_host_broker_authenticator` | `_HOST_BROKER_AUTHENTICATOR.get` | 234 |
| external_call | `require_process_host_broker_authenticator` | `isinstance` | 240 |
| external_call | `require_bounded_text` | `isinstance` | 605 |
| unresolved_call | `require_bounded_text` | `value.strip` | 608 |
| external_call | `require_bounded_text` | `any` | 611 |
| step_limit | `require_process_host_broker_authenticator` | `first 12 steps` | 0 |

## Behavior

This flow starts at `require_process_host_broker_authenticator` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
