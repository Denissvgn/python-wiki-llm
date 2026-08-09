# redact_credentials

**Entry point:** `redact_credentials` (`api`)
**Source:** [redaction](../modules/redaction.md)
**Modules touched:** [redaction](../modules/redaction.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as redact_credentials
    participant p1 as apply
    participant p2 as str
    participant p3 as group
    p0-->>p1: apply
    p0-->>p1: apply
    p0-->>p1: apply
    p0-->>p1: apply
    p0-->>p1: apply
    p0-->>p1: apply
    p0-->>p1: apply
    p0-->>p1: apply
    p0-->>p2: str
    p0-->>p3: group
    p0-->>p1: apply
    p0-->>p2: str
    p0-->>p3: group
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. redact_credentials"]
    s2["2. apply"]
    s3["3. apply"]
    s4["4. apply"]
    s5["5. apply"]
    s6["6. apply"]
    s7["7. apply"]
    s8["8. apply"]
    s9["9. apply"]
    s10["10. str"]
    s11["11. group"]
    s12["12. apply"]
    s1 -. "apply(PRIVATE_KEY_BLOCK_RE, REDACTED_CREDENTIAL)" .-> s2
    s1 -. "apply(pattern, REDACTED_CREDENTIAL)" .-> s3
    s1 -. "apply(_AUTHORIZATION_VALUE_RE, REDACTED_CREDENTIAL)" .-> s4
    s1 -. "apply(CREDENTIAL_VALUE_RE, REDACTED_CREDENTIAL)" .-> s5
    s1 -. "apply(LIKELY_SECRET_RE, _likely_secret_replacement)" .-> s6
    s1 -. "apply(_REDACTION_SENSITIVE_ASSIGNMENT_RE, _assignment_replacement)" .-> s7
    s1 -. "apply(_REDACTION_SENSITIVE_NATURAL_LANGUAGE_RE, _assignment_replacement)" .-> s8
    s1 -. "apply(_REDACTABLE_URI_USERINFO_RE, ...)" .-> s9
    s1 -. "str(match.group(...))" .-> s10
    s1 -. "match.group('scheme')" .-> s11
    s1 -. "apply(_REDACTABLE_PROJECTION_URI_USERINFO_RE, ...)" .-> s12
    click s1 "../modules/redaction.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `redact_credentials` | `text: str` | `PRIVATE_KEY_BLOCK_RE`, `REDACTED_CREDENTIAL`, `COMMON_TOKEN_PATTERNS`, `REDACTED_CREDENTIAL`, `_AUTHORIZATION_VALUE_RE`, `REDACTED_CREDENTIAL`, `CREDENTIAL_VALUE_RE`, `REDACTED_CREDENTIAL` | - | `(...)` |
| `apply` | - | - | - | - |
| `apply` | - | - | - | - |
| `apply` | - | - | - | - |
| `apply` | - | - | - | - |
| `apply` | - | - | - | - |
| `apply` | - | - | - | - |
| `apply` | - | - | - | - |
| `apply` | - | - | - | - |
| `str` | - | - | - | - |
| `group` | - | - | - | - |
| `apply` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| redact_credentials | apply | 326 | `apply(PRIVATE_KEY_BLOCK_RE, REDACTED_CREDENTIAL)` |
| redact_credentials | apply | 328 | `apply(pattern, REDACTED_CREDENTIAL)` |
| redact_credentials | apply | 329 | `apply(_AUTHORIZATION_VALUE_RE, REDACTED_CREDENTIAL)` |
| redact_credentials | apply | 330 | `apply(CREDENTIAL_VALUE_RE, REDACTED_CREDENTIAL)` |
| redact_credentials | apply | 331 | `apply(LIKELY_SECRET_RE, _likely_secret_replacement)` |
| redact_credentials | apply | 332 | `apply(_REDACTION_SENSITIVE_ASSIGNMENT_RE, _assignment_replacement)` |
| redact_credentials | apply | 333 | `apply(_REDACTION_SENSITIVE_NATURAL_LANGUAGE_RE, _assignment_replacement)` |
| redact_credentials | apply | 334 | `apply(_REDACTABLE_URI_USERINFO_RE, ...)` |
| redact_credentials | str | 336 | `str(match.group(...))` |
| redact_credentials | group | 336 | `match.group('scheme')` |
| redact_credentials | apply | 338 | `apply(_REDACTABLE_PROJECTION_URI_USERINFO_RE, ...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `redact_credentials` | `apply` | 326 |
| unresolved_call | `redact_credentials` | `apply` | 328 |
| unresolved_call | `redact_credentials` | `apply` | 329 |
| unresolved_call | `redact_credentials` | `apply` | 330 |
| unresolved_call | `redact_credentials` | `apply` | 331 |
| unresolved_call | `redact_credentials` | `apply` | 332 |
| unresolved_call | `redact_credentials` | `apply` | 333 |
| unresolved_call | `redact_credentials` | `apply` | 334 |
| unresolved_call | `redact_credentials` | `match.group` | 336 |
| unresolved_call | `redact_credentials` | `apply` | 338 |
| step_limit | `redact_credentials` | `first 12 steps` | 0 |

## Behavior

This flow starts at `redact_credentials` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
