# require_enum_value

**Entry point:** `require_enum_value` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_enum_value
    participant p1 as require_string
    participant p2 as isinstance
    participant p3 as encode
    participant p4 as enum_type
    participant p5 as choice_error
    p0->>p1: require_string
    p1-->>p2: isinstance
    p1-->>p3: encode
    p0-->>p4: enum_type
    p0-->>p5: choice_error
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_enum_value"]
    s2["2. require_string"]
    s3["3. isinstance"]
    s4["4. encode"]
    s5["5. enum_type"]
    s6["6. choice_error"]
    s1 -->|"require_string(value, error=text_error)"| s2
    s2 -. "isinstance(value, str)" .-> s3
    s2 -. "value.encode('utf-8')" .-> s4
    s1 -. "enum_type(parsed)" .-> s5
    s1 -. "choice_error(data not statically known)" .-> s6
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_enum_value` | `value: object`, `enum_type: Callable[[str], _EnumValue]`, `text_error: Exception`, `choice_error: Callable[[], Exception]` | - | - | `enum_type(...)` |
| `require_string` | `value: object`, `error: Exception`, `utf8_error: Exception \| None` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `enum_type` | - | - | - | - |
| `choice_error` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_enum_value | require_string | 1069 | `require_string(value, error=text_error)` |
| require_string | isinstance | 706 | `isinstance(value, str)` |
| require_string | encode | 710 | `value.encode('utf-8')` |
| require_enum_value | enum_type | 1071 | `enum_type(parsed)` |
| require_enum_value | choice_error | 1073 | `choice_error(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_string` | `isinstance` | 706 |
| unresolved_call | `require_string` | `value.encode` | 710 |
| unresolved_call | `require_enum_value` | `enum_type` | 1071 |
| unresolved_call | `require_enum_value` | `choice_error` | 1073 |

## Behavior

This flow starts at `require_enum_value` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
