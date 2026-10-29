# require_attestation_authentication

**Entry point:** `require_attestation_authentication` (`api`)
**Source:** [host_broker](../modules/host_broker.md)
**Modules touched:** [host_broker](../modules/host_broker.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_attestation_authentication
    participant p1 as require_process_host_broker_authenticator
    participant p2 as authenticator.authenticate_attestation
    participant p3 as HostBrokerAuthenticationError
    participant p4 as isinstance (src/llm_wiki_cli/services…attestation_authentication)
    participant p5 as _HOST_BROKER_AUTHENTICATOR.get
    participant p6 as HostBrokerAuthenticationUnavailable
    participant p7 as isinstance (src/llm_wiki_cli/services…_host_broker_authenticator)
    participant p8 as _require_bounded_text
    participant p9 as require_bounded_text
    participant p10 as isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text)
    participant p11 as len
    participant p12 as value.strip
    participant p13 as contains_control_character
    participant p14 as pattern.search
    p0->>p1: require_process_host_broker_authenticator
    p0-->>p2: authenticator.authenticate_attestation(…)
    p0->>p3: HostBrokerAuthenticationError
    p0-->>p4: isinstance (src/llm_wiki_cli/services…attestation_authentication)(proof, HostBrokerAuthenticationProof)
    p0->>p3: HostBrokerAuthenticationError
    p0->>p3: HostBrokerAuthenticationError
    p1-->>p5: _HOST_BROKER_AUTHENTICATOR.get
    p1->>p6: HostBrokerAuthenticationUnavailable
    p1-->>p7: isinstance (src/llm_wiki_cli/services…_host_broker_authenticator)(authenticator, HostBrokerAuthenticator)
    p1->>p6: HostBrokerAuthenticationUnavailable
    p1->>p8: _require_bounded_text
    p8->>p9: require_bounded_text
    p8->>p3: HostBrokerAuthenticationError
    p9-->>p10: isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text)(value, str)
    p9-->>p11: len(value)
    p9-->>p11: len(value)
    p9-->>p12: value.strip
    p9->>p13: contains_control_character
    p13-->>p14: pattern.search(value)
```

> Call sequence diagram shows 19 of 19 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 5 (0 omitted); unresolved 4 of 4 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 11; effect analysis evaluated: 5, partial: 0, unavailable: 6. Counts include steps omitted from the displayed trace.

Collector observations for 5 source steps with known totals: observed: 26, emitted: 26, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `require_attestation_authentication` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `require_process_host_broker_authenticator` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_HOST_BROKER_AUTHENTICATOR.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `HostBrokerAuthenticationUnavailable` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…_host_broker_authenticator)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `HostBrokerAuthenticationUnavailable` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_require_bounded_text` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `require_bounded_text` | `available` | `evaluated` | `available` | `9` | `9` | `0` |
| `isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `value.strip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. require_attestation_authentication"]
    s2["2. require_process_host_broker_authenticator"]
    s3["3. _HOST_BROKER_AUTHENTICATOR.get"]
    s4["4. HostBrokerAuthenticationUnavailable"]
    s5["5. isinstance (src/llm_wiki_cli/services…_host_broker_authenticator)"]
    s6["6. HostBrokerAuthenticationUnavailable"]
    s7["7. _require_bounded_text"]
    s8["8. require_bounded_text"]
    s9["9. isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text)"]
    s10["10. len"]
    s11["11. len"]
    s12["12. value.strip"]
    s1 -->|"require_process_host_broker_authenticator(data not statically known)"| s2
    s2 -. "_HOST_BROKER_AUTHENTICATOR.get(data not statically known)" .-> s3
    s2 -->|"HostBrokerAuthenticationUnavailable('External admission requires a separately authenticated host broker; this process has no host authenticator.')"| s4
    s2 -. "isinstance (src/llm_wiki_cli/services…_host_broker_authenticator)(authenticator, HostBrokerAuthenticator)" .-> s5
    s2 -->|"HostBrokerAuthenticationUnavailable('The process host broker authenticator is malformed.')"| s6
    s2 -->|"_require_bounded_text(authenticator.authenticator_id, 'authenticator_id')"| s7
    s7 -->|"require_bounded_text(value, maximum=512, error=HostBrokerAuthenticationError(...))"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text)(value, str)" .-> s9
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
| `require_attestation_authentication` | `cohort_id: str`, `authority_grant: Mapping[str, Any]`, `execution_manifest: Mapping[str, Any]`, `attestation: Mapping[str, Any]`, `attestation_hash: str` | `HostBrokerAuthenticationProof` | - | `proof` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_attestation_authentication | require_process_host_broker_authenticator | 258 | `require_process_host_broker_authenticator(data not statically known)` |
| require_process_host_broker_authenticator | _HOST_BROKER_AUTHENTICATOR.get | 234 | `_HOST_BROKER_AUTHENTICATOR.get(data not statically known)` |
| require_process_host_broker_authenticator | HostBrokerAuthenticationUnavailable | 236 | `HostBrokerAuthenticationUnavailable('External admission requires a separately authenticated host broker; this process has no host authenticator.')` |
| require_process_host_broker_authenticator | isinstance (src/llm_wiki_cli/services…_host_broker_authenticator) | 240 | `isinstance(authenticator, HostBrokerAuthenticator)` |
| require_process_host_broker_authenticator | HostBrokerAuthenticationUnavailable | 241 | `HostBrokerAuthenticationUnavailable('The process host broker authenticator is malformed.')` |
| require_process_host_broker_authenticator | _require_bounded_text | 244 | `_require_bounded_text(authenticator.authenticator_id, 'authenticator_id')` |
| _require_bounded_text | require_bounded_text | 321 | `require_bounded_text(value, maximum=512, error=HostBrokerAuthenticationError(...))` |
| require_bounded_text | isinstance (src/llm_wiki_cli/services…on.py:require_bounded_text) | 650 | `isinstance(value, str)` |
| require_bounded_text | len | 651 | `len(value)` |
| require_bounded_text | len | 652 | `len(value)` |
| require_bounded_text | value.strip | 653 | `value.strip(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_process_host_broker_authenticator` | `_HOST_BROKER_AUTHENTICATOR.get` | 234 |
| external_call | `require_process_host_broker_authenticator` | `isinstance` | 240 |
| external_call | `require_bounded_text` | `isinstance` | 650 |
| unresolved_call | `require_bounded_text` | `value.strip` | 653 |
| step_limit | `require_attestation_authentication` | `first 12 steps` | 0 |

## Behavior

This flow starts at `require_attestation_authentication` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
