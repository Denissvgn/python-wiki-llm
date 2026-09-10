# is_portable_path_component

**Entry point:** `is_portable_path_component` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_portable_path_component
    participant p1 as require_portable_path_component
    participant p2 as component.encode
    participant p3 as SharedValidationError
    participant p4 as unicodedata.normalize
    participant p5 as any
    participant p6 as ord
    participant p7 as component.endswith
    participant p8 as component.split(…)[…].casefold
    participant p9 as component.split
    p0->>p1: require_portable_path_component
    p1-->>p2: component.encode
    p1->>p3: SharedValidationError
    p1-->>p4: unicodedata.normalize
    p1->>p3: SharedValidationError
    p1-->>p5: any
    p1-->>p6: ord
    p1-->>p6: ord
    p1->>p3: SharedValidationError
    p1-->>p7: component.endswith
    p1-->>p5: any
    p1->>p3: SharedValidationError
    p1-->>p8: component.split(…)[…].casefold
    p1-->>p9: component.split
    p1->>p3: SharedValidationError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. is_portable_path_component"]
    s2["2. require_portable_path_component"]
    s3["3. component.encode"]
    s4["4. SharedValidationError"]
    s5["5. unicodedata.normalize"]
    s6["6. SharedValidationError"]
    s7["7. any"]
    s8["8. ord"]
    s9["9. ord"]
    s10["10. SharedValidationError"]
    s11["11. component.endswith"]
    s12["12. any"]
    s1 -->|"require_portable_path_component(component)"| s2
    s2 -. "component.encode('utf-8')" .-> s3
    s2 -->|"SharedValidationError(...)"| s4
    s2 -. "unicodedata.normalize('NFC', component)" .-> s5
    s2 -->|"SharedValidationError(...)"| s6
    s2 -. "any(...)" .-> s7
    s2 -. "ord(character)" .-> s8
    s2 -. "ord(character)" .-> s9
    s2 -->|"SharedValidationError(...)"| s10
    s2 -. "component.endswith((...))" .-> s11
    s2 -. "any(...)" .-> s12
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s4 "../modules/validation.md"
    click s6 "../modules/validation.md"
    click s10 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_portable_path_component` | `component: str` | `SharedValidationError` | - | `False`, `True` |
| `require_portable_path_component` | `component: str`, `context: str \| None`, `defer_non_nfc_error: bool`, `reject_delete_character: bool`, `utf8_error: Exception \| None`, `control_error: Exception \| None`, `non_nfc_error: Exception \| None`, `nonportable_error: Exception \| None` | `_WINDOWS_FORBIDDEN_PATH_CHARS`, `_WINDOWS_RESERVED_NAMES` | - | `component` |
| `component.encode` | - | - | - | - |
| `SharedValidationError` | - | - | - | - |
| `unicodedata.normalize` | - | - | - | - |
| `SharedValidationError` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |
| `ord` | - | - | - | - |
| `SharedValidationError` | - | - | - | - |
| `component.endswith` | - | - | - | - |
| `any` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_portable_path_component | require_portable_path_component | 131 | `require_portable_path_component(component)` |
| require_portable_path_component | component.encode | 93 | `component.encode('utf-8')` |
| require_portable_path_component | SharedValidationError | 95 | `SharedValidationError(...)` |
| require_portable_path_component | unicodedata.normalize | 100 | `unicodedata.normalize('NFC', component)` |
| require_portable_path_component | SharedValidationError | 102 | `SharedValidationError(...)` |
| require_portable_path_component | any | 105 | `any(...)` |
| require_portable_path_component | ord | 106 | `ord(character)` |
| require_portable_path_component | ord | 107 | `ord(character)` |
| require_portable_path_component | SharedValidationError | 110 | `SharedValidationError(...)` |
| require_portable_path_component | component.endswith | 113 | `component.endswith((...))` |
| require_portable_path_component | any | 113 | `any(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_portable_path_component` | `component.encode` | 93 |
| external_call | `require_portable_path_component` | `unicodedata.normalize` | 100 |
| external_call | `require_portable_path_component` | `any` | 105 |
| external_call | `require_portable_path_component` | `ord` | 106 |
| external_call | `require_portable_path_component` | `ord` | 107 |
| unresolved_call | `require_portable_path_component` | `component.endswith` | 113 |
| external_call | `require_portable_path_component` | `any` | 113 |
| step_limit | `is_portable_path_component` | `first 12 steps` | 0 |

## Behavior

This flow starts at `is_portable_path_component` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
