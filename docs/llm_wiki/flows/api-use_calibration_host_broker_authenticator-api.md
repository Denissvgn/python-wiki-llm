# use_calibration_host_broker_authenticator

**Entry point:** `use_calibration_host_broker_authenticator` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [context_packet](../modules/context_packet.md), [host_broker](../modules/host_broker.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as use_calibration_host_broker_authenticator (src/llm_wiki_cli/api.py)
    participant p1 as use_calibration_host_broker_authenticator (src/llm_wiki_cli/services…alibration/host_broker.py)
    participant p2 as _raise_api_error
    participant p3 as _raise_required_knowledge_api_error
    participant p4 as _require_bounded_text
    participant p5 as _raise_context_packet_api_error
    participant p6 as _raise_maintenance_api_error
    participant p7 as _calibration_error_category
    participant p8 as require_bounded_text
    participant p9 as HostBrokerAuthenticationUnavailable
    participant p10 as InvalidRequestError
    participant p11 as _is_maintenance_error
    participant p12 as _wiki_path_policy_details
    participant p13 as ArtifactIntegrityError
    participant p14 as WorkspaceStateError
    participant p15 as _caused_by
    participant p16 as _required_knowledge_failure
    participant p17 as _has_exception_origin
    participant p18 as HostBrokerAuthenticationError
    participant p19 as describe_context_packet_error
    participant p20 as contains_control_character
    participant p21 as type (src/llm_wiki_cli/api.py:u…host_broker_authenticator)
    participant p22 as manager.__enter__
    participant p23 as manager.__exit__
    participant p24 as isinstance (src/llm_wiki_cli/api.py:u…host_broker_authenticator)
    participant p25 as isinstance (src/llm_wiki_cli/services…host_broker_authenticator)
    participant p26 as isinstance (src/llm_wiki_cli/api.py:_raise_api_error)
    participant p27 as _HOST_BROKER_AUTHENTICATOR.set
    participant p28 as _HOST_BROKER_AUTHENTICATOR.reset
    p0->>p1: use_calibration_host_broker_authenticator (src/llm_wiki_cli/services…alibration/host_broker.py)
    p0->>p2: _raise_api_error
    p2->>p3: _raise_required_knowledge_api_error
    p1->>p4: _require_bounded_text
    p2->>p5: _raise_context_packet_api_error
    p2->>p6: _raise_maintenance_api_error
    p2->>p7: _calibration_error_category
    p4->>p8: require_bounded_text
    p1->>p9: HostBrokerAuthenticationUnavailable
    p2->>p10: InvalidRequestError
    p2->>p11: _is_maintenance_error
    p2->>p12: _wiki_path_policy_details
    p2->>p13: ArtifactIntegrityError
    p2->>p14: WorkspaceStateError
    p2->>p15: _caused_by
    p3->>p16: _required_knowledge_failure
    p7->>p17: _has_exception_origin
    p4->>p18: HostBrokerAuthenticationError
    p5->>p19: describe_context_packet_error
    p8->>p20: contains_control_character
    p0-->>p21: type (src/llm_wiki_cli/api.py:u…host_broker_authenticator)(body_exc)
    p0-->>p22: manager.__enter__
    p0-->>p23: manager.__exit__(type(...), body_exc, body_exc.__traceback__)
    p0-->>p24: isinstance (src/llm_wiki_cli/api.py:u…host_broker_authenticator)(exit_exc, Exception)
    p0-->>p23: manager.__exit__(None, None, None)
    p1-->>p25: isinstance (src/llm_wiki_cli/services…host_broker_authenticator)(authenticator, HostBrokerAuthenticator)
    p2-->>p26: isinstance (src/llm_wiki_cli/api.py:_raise_api_error)(exc, context_packet_service.ContextPacketError)
    p1-->>p27: _HOST_BROKER_AUTHENTICATOR.set(authenticator)
    p2-->>p26: isinstance (src/llm_wiki_cli/api.py:_raise_api_error)(exc, WorkflowRequestError)
    p1-->>p28: _HOST_BROKER_AUTHENTICATOR.reset(token)
```

> Call sequence diagram shows 30 of 139 interactions; 109 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 82 (77 omitted); unresolved 5 of 19 (14 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:require_bounded_text` | 6 | - | external | 3 |
| `src/llm_wiki_cli/services/validation.py:require_bounded_text` | 6 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:contains_control_character` | 11 | - | unresolved | 1 |
| `src/llm_wiki_cli/api.py:_required_knowledge_failure` | 19 | - | external | 10 |
| `src/llm_wiki_cli/api.py:_required_knowledge_failure` | 19 | - | unresolved | 2 |
| `src/llm_wiki_cli/api.py:_raise_required_knowledge_api_error` | 18 | [src/llm_wiki_cli/api.py](../modules/api.md) | internal | 1 |
| `src/llm_wiki_cli/api.py:_raise_required_knowledge_api_error` | 18 | - | external | 1 |
| `src/llm_wiki_cli/api.py:_raise_context_packet_api_error` | 35 | [src/llm_wiki_cli/api.py](../modules/api.md) | internal | 1 |
> Omission summary shows 8 of 25 groups; 17 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. use_calibration_host_broker_authenticator (src/llm_wiki_cli/api.py)"]
    s2["2. use_calibration_host_broker_authenticator (src/llm_wiki_cli/services…alibration/host_broker.py)"]
    s3["3. isinstance (src/llm_wiki_cli/services…host_broker_authenticator)"]
    s4["4. HostBrokerAuthenticationUnavailable"]
    s5["5. _require_bounded_text"]
    s6["6. require_bounded_text"]
    s7["7. isinstance (src/llm_wiki_cli/services…n.py:require_bounded_text)"]
    s8["8. len"]
    s9["9. len"]
    s10["10. value.strip"]
    s11["11. contains_control_character"]
    s12["12. pattern.search"]
    s1 -->|"use_calibration_host_broker_authenticator (src/llm_wiki_cli/services…alibration/host_broker.py)(authenticator)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…host_broker_authenticator)(authenticator, HostBrokerAuthenticator)" .-> s3
    s2 -->|"HostBrokerAuthenticationUnavailable('The host broker authenticator is malformed.')"| s4
    s2 -->|"_require_bounded_text(authenticator.authenticator_id, 'authenticator_id')"| s5
    s5 -->|"require_bounded_text(value, maximum=512, error=HostBrokerAuthenticationError(...))"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…n.py:require_bounded_text)(value, str)" .-> s7
    s6 -. "len(value)" .-> s8
    s6 -. "len(value)" .-> s9
    s6 -. "value.strip(data not statically known)" .-> s10
    s6 -->|"contains_control_character(value, reject_delete_character=reject_delete_character)"| s11
    s11 -. "pattern.search(value)" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/host_broker.md"
    click s4 "../modules/host_broker.md"
    click s5 "../modules/host_broker.md"
    click s6 "../modules/validation.md"
    click s11 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `use_calibration_host_broker_authenticator (src/llm_wiki_cli/api.py)` | `authenticator: HostBrokerAuthenticator` | - | - | - |
| `use_calibration_host_broker_authenticator (src/llm_wiki_cli/services…alibration/host_broker.py)` | `authenticator: HostBrokerAuthenticator` | `HostBrokerAuthenticator` | - | - |
| `isinstance (src/llm_wiki_cli/services…host_broker_authenticator)` | - | - | - | - |
| `HostBrokerAuthenticationUnavailable` | - | - | - | - |
| `_require_bounded_text` | `value: Any`, `label: str` | - | - | `require_bounded_text(...)` |
| `require_bounded_text` | `value: object`, `maximum: int`, `error: Exception`, `minimum: int`, `control_error: Exception \| None`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…n.py:require_bounded_text)` | - | - | - | - |
| `len` | - | - | - | - |
| `len` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `contains_control_character` | `value: str`, `reject_delete_character: bool` | `_ASCII_CONTROL_DELETE`, `_ASCII_CONTROL` | - | `...` |
| `pattern.search` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| use_calibration_host_broker_authenticator (src/llm_wiki_cli/api.py) | use_calibration_host_broker_authenticator (src/llm_wiki_cli/services…alibration/host_broker.py) | 3479 | `implementation(authenticator)` |
| use_calibration_host_broker_authenticator (src/llm_wiki_cli/services…alibration/host_broker.py) | isinstance (src/llm_wiki_cli/services…host_broker_authenticator) | 195 | `isinstance(authenticator, HostBrokerAuthenticator)` |
| use_calibration_host_broker_authenticator (src/llm_wiki_cli/services…alibration/host_broker.py) | HostBrokerAuthenticationUnavailable | 196 | `HostBrokerAuthenticationUnavailable('The host broker authenticator is malformed.')` |
| use_calibration_host_broker_authenticator (src/llm_wiki_cli/services…alibration/host_broker.py) | _require_bounded_text | 199 | `_require_bounded_text(authenticator.authenticator_id, 'authenticator_id')` |
| _require_bounded_text | require_bounded_text | 321 | `require_bounded_text(value, maximum=512, error=HostBrokerAuthenticationError(...))` |
| require_bounded_text | isinstance (src/llm_wiki_cli/services…n.py:require_bounded_text) | 650 | `isinstance(value, str)` |
| require_bounded_text | len | 651 | `len(value)` |
| require_bounded_text | len | 652 | `len(value)` |
| require_bounded_text | value.strip | 653 | `value.strip(data not statically known)` |
| require_bounded_text | contains_control_character | 656 | `contains_control_character(value, reject_delete_character=reject_delete_character)` |
| contains_control_character | pattern.search | 685 | `pattern.search(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `use_calibration_host_broker_authenticator` | `isinstance` | 195 |
| external_call | `require_bounded_text` | `isinstance` | 650 |
| unresolved_call | `require_bounded_text` | `value.strip` | 653 |
| unresolved_call | `contains_control_character` | `pattern.search` | 685 |
| step_limit | `use_calibration_host_broker_authenticator` | `first 12 steps` | 0 |

## Behavior

This flow starts at `use_calibration_host_broker_authenticator` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
