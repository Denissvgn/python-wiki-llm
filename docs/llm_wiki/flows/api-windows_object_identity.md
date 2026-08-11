# windows_object_identity

**Entry point:** `windows_object_identity` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as windows_object_identity
    participant p1 as windows_object_identity_from_values
    participant p2 as WindowsIdentityUnavailableError
    participant p3 as WindowsObjectIdentity
    participant p4 as int
    participant p5 as getattr
    p0->>p1: windows_object_identity_from_values
    p1->>p2: WindowsIdentityUnavailableError
    p1->>p3: WindowsObjectIdentity
    p1-->>p4: int
    p0-->>p4: int
    p0-->>p5: getattr
    p0-->>p4: int
    p0-->>p5: getattr
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. windows_object_identity"]
    s2["2. windows_object_identity_from_values"]
    s3["3. WindowsIdentityUnavailableError"]
    s4["4. WindowsObjectIdentity"]
    s5["5. int"]
    s6["6. int"]
    s7["7. getattr"]
    s8["8. int"]
    s9["9. getattr"]
    s1 -->|"windows_object_identity_from_values(device=int(...), file_id=int(...), context=context)"| s2
    s2 -->|"WindowsIdentityUnavailableError(...)"| s3
    s2 -->|"WindowsObjectIdentity(device=int(...), file_id=file_id)"| s4
    s2 -. "int(device)" .-> s5
    s1 -. "int(getattr(...))" .-> s6
    s1 -. "getattr(result, 'st_dev', 0)" .-> s7
    s1 -. "int(getattr(...))" .-> s8
    s1 -. "getattr(result, 'st_ino', 0)" .-> s9
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s3 "../modules/filesystem_guard.md"
    click s4 "../modules/filesystem_guard.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `windows_object_identity` | `result: os.stat_result`, `context: str` | - | - | `windows_object_identity_from_values(...)` |
| `windows_object_identity_from_values` | `device: int`, `file_id: int`, `context: str` | - | - | `WindowsObjectIdentity(...)` |
| `WindowsIdentityUnavailableError` | - | - | - | - |
| `WindowsObjectIdentity` | - | - | - | - |
| `int` | - | - | - | - |
| `int` | - | - | - | - |
| `getattr` | - | - | - | - |
| `int` | - | - | - | - |
| `getattr` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| windows_object_identity | windows_object_identity_from_values | 108 | `windows_object_identity_from_values(device=int(...), file_id=int(...), context=context)` |
| windows_object_identity_from_values | WindowsIdentityUnavailableError | 124 | `WindowsIdentityUnavailableError(...)` |
| windows_object_identity_from_values | WindowsObjectIdentity | 127 | `WindowsObjectIdentity(device=int(...), file_id=file_id)` |
| windows_object_identity_from_values | int | 128 | `int(device)` |
| windows_object_identity | int | 109 | `int(getattr(...))` |
| windows_object_identity | getattr | 109 | `getattr(result, 'st_dev', 0)` |
| windows_object_identity | int | 110 | `int(getattr(...))` |
| windows_object_identity | getattr | 110 | `getattr(result, 'st_ino', 0)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `windows_object_identity` | `getattr` | 109 |
| unresolved_call | `windows_object_identity` | `getattr` | 110 |

## Behavior

This flow starts at `windows_object_identity` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
