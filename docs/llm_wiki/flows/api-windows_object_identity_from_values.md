# windows_object_identity_from_values

**Entry point:** `windows_object_identity_from_values` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as windows_object_identity_from_values
    participant p1 as WindowsIdentityUnavailableError
    participant p2 as WindowsObjectIdentity
    participant p3 as int
    p0->>p1: WindowsIdentityUnavailableError
    p0->>p2: WindowsObjectIdentity
    p0-->>p3: int
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. windows_object_identity_from_values"]
    s2["2. WindowsIdentityUnavailableError"]
    s3["3. WindowsObjectIdentity"]
    s4["4. int"]
    s1 -->|"WindowsIdentityUnavailableError(...)"| s2
    s1 -->|"WindowsObjectIdentity(device=int(...), file_id=file_id)"| s3
    s1 -. "int(device)" .-> s4
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s3 "../modules/filesystem_guard.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `windows_object_identity_from_values` | `device: int`, `file_id: int`, `context: str` | - | - | `WindowsObjectIdentity(...)` |
| `WindowsIdentityUnavailableError` | - | - | - | - |
| `WindowsObjectIdentity` | - | - | - | - |
| `int` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| windows_object_identity_from_values | WindowsIdentityUnavailableError | 124 | `WindowsIdentityUnavailableError(...)` |
| windows_object_identity_from_values | WindowsObjectIdentity | 127 | `WindowsObjectIdentity(device=int(...), file_id=file_id)` |
| windows_object_identity_from_values | int | 128 | `int(device)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

*No static analysis gaps detected.*

## Behavior

This flow starts at `windows_object_identity_from_values` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
