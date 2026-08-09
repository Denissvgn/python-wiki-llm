# require_exact_fields

**Entry point:** `require_exact_fields` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_exact_fields
    participant p1 as isinstance
    participant p2 as str
    participant p3 as set
    participant p4 as tuple
    participant p5 as sorted
    participant p6 as invalid_error
    participant p7 as error_factory
    p0-->>p1: isinstance
    p0-->>p2: str
    p0-->>p3: set
    p0-->>p3: set
    p0-->>p3: set
    p0-->>p4: tuple
    p0-->>p5: sorted
    p0-->>p4: tuple
    p0-->>p5: sorted
    p0-->>p6: invalid_error
    p0-->>p7: error_factory
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_exact_fields"]
    s2["2. isinstance"]
    s3["3. str"]
    s4["4. set"]
    s5["5. set"]
    s6["6. set"]
    s7["7. tuple"]
    s8["8. sorted"]
    s9["9. tuple"]
    s10["10. sorted"]
    s11["11. invalid_error"]
    s12["12. error_factory"]
    s1 -. "isinstance(value, Mapping)" .-> s2
    s1 -. "str(key)" .-> s3
    s1 -. "set(value)" .-> s4
    s1 -. "set(allowed)" .-> s5
    s1 -. "set(required)" .-> s6
    s1 -. "tuple(sorted(...))" .-> s7
    s1 -. "sorted(..., key=str)" .-> s8
    s1 -. "tuple(sorted(...))" .-> s9
    s1 -. "sorted(..., key=str)" .-> s10
    s1 -. "invalid_error(missing, unknown)" .-> s11
    s1 -. "error_factory(fields)" .-> s12
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_exact_fields` | `value: object`, `allowed: Iterable[str]`, `required: Iterable[str]`, `mapping_error: Exception`, `missing_error: _ErrorFactory`, `unknown_error: _ErrorFactory`, `invalid_error: Callable[[tuple[str, ...], tuple[str, ...]], Exception] \| None`, `stringify_keys: bool` | `Mapping` | - | - |
| `isinstance` | - | - | - | - |
| `str` | - | - | - | - |
| `set` | - | - | - | - |
| `set` | - | - | - | - |
| `set` | - | - | - | - |
| `tuple` | - | - | - | - |
| `sorted` | - | - | - | - |
| `tuple` | - | - | - | - |
| `sorted` | - | - | - | - |
| `invalid_error` | - | - | - | - |
| `error_factory` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_exact_fields | isinstance | 1205 | `isinstance(value, Mapping)` |
| require_exact_fields | str | 1207 | `str(key)` |
| require_exact_fields | set | 1207 | `set(value)` |
| require_exact_fields | set | 1208 | `set(allowed)` |
| require_exact_fields | set | 1209 | `set(required)` |
| require_exact_fields | tuple | 1210 | `tuple(sorted(...))` |
| require_exact_fields | sorted | 1210 | `sorted(..., key=str)` |
| require_exact_fields | tuple | 1211 | `tuple(sorted(...))` |
| require_exact_fields | sorted | 1211 | `sorted(..., key=str)` |
| require_exact_fields | invalid_error | 1213 | `invalid_error(missing, unknown)` |
| require_exact_fields | error_factory | 1221 | `error_factory(fields)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_exact_fields` | `isinstance` | 1205 |
| unresolved_call | `require_exact_fields` | `sorted` | 1210 |
| unresolved_call | `require_exact_fields` | `sorted` | 1211 |
| unresolved_call | `require_exact_fields` | `invalid_error` | 1213 |
| unresolved_call | `require_exact_fields` | `error_factory` | 1221 |

## Behavior

This flow starts at `require_exact_fields` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
