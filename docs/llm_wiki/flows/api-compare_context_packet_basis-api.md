# compare_context_packet_basis

**Entry point:** `compare_context_packet_basis` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_context_packet_basis
    participant p1 as PathPolicyError
    participant p2 as str
    participant p3 as InvalidRequestError
    p0-->>p0: compare_context_packet_basis
    p0-->>p1: PathPolicyError
    p0-->>p2: str
    p0->>p3: InvalidRequestError
    p0-->>p2: str
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. compare_context_packet_basis"]
    s2["2. compare_context_packet_basis"]
    s3["3. PathPolicyError"]
    s4["4. str"]
    s5["5. InvalidRequestError"]
    s6["6. str"]
    s1 -. "context_packet_service.compare_context_packet_basis(packet_bytes, expected_basis)" .-> s2
    s1 -. "PathPolicyError(str(...))" .-> s3
    s1 -. "str(exc)" .-> s4
    s1 -->|"InvalidRequestError(str(...))"| s5
    s1 -. "str(exc)" .-> s6
    click s1 "../modules/api.md"
    click s5 "../modules/api.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compare_context_packet_basis` | `packet_bytes: bytes \| bytearray \| memoryview`, `expected_basis: Mapping[str, Any]` | `context_packet_service`, `context_packet_service` | - | `comparison` |
| `compare_context_packet_basis` | - | - | - | - |
| `PathPolicyError` | - | - | - | - |
| `str` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `str` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compare_context_packet_basis | compare_context_packet_basis | 960 | `context_packet_service.compare_context_packet_basis(packet_bytes, expected_basis)` |
| compare_context_packet_basis | PathPolicyError | 965 | `PathPolicyError(str(...))` |
| compare_context_packet_basis | str | 965 | `str(exc)` |
| compare_context_packet_basis | InvalidRequestError | 967 | `InvalidRequestError(str(...))` |
| compare_context_packet_basis | str | 967 | `str(exc)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `compare_context_packet_basis` | `context_packet_service.compare_context_packet_basis` | 960 |
| unresolved_call | `compare_context_packet_basis` | `PathPolicyError` | 965 |

## Behavior

This flow starts at `compare_context_packet_basis` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
