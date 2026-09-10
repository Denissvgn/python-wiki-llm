# authored_event_time

**Entry point:** `authored_event_time` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [knowledge_governance](../modules/knowledge_governance.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as authored_event_time
    participant p1 as datetime.now
    participant p2 as isinstance
    participant p3 as datetime.fromisoformat
    participant p4 as raw.replace
    participant p5 as GovernanceError
    participant p6 as parsed.utcoffset
    participant p7 as parsed.astimezone
    participant p8 as utc.isoformat(…).replace (src/llm_wiki_cli/services…nce.py:authored_event_time)
    participant p9 as utc.isoformat
    participant p10 as utc.isoformat(…).replace (src/llm_wiki_cli/services….py:authored_event_time, 1)
    p0-->>p1: datetime.now
    p0-->>p2: isinstance
    p0-->>p3: datetime.fromisoformat
    p0-->>p4: raw.replace
    p0->>p5: GovernanceError
    p0-->>p2: isinstance
    p0->>p5: GovernanceError
    p0-->>p6: parsed.utcoffset
    p0->>p5: GovernanceError
    p0-->>p7: parsed.astimezone
    p0-->>p8: utc.isoformat(…).replace (src/llm_wiki_cli/services…nce.py:authored_event_time)
    p0-->>p9: utc.isoformat
    p0-->>p10: utc.isoformat(…).replace (src/llm_wiki_cli/services….py:authored_event_time, 1)
    p0-->>p9: utc.isoformat
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. authored_event_time"]
    s2["2. datetime.now"]
    s3["3. isinstance"]
    s4["4. datetime.fromisoformat"]
    s5["5. raw.replace"]
    s6["6. GovernanceError"]
    s7["7. isinstance"]
    s8["8. GovernanceError"]
    s9["9. parsed.utcoffset"]
    s10["10. GovernanceError"]
    s11["11. parsed.astimezone"]
    s12["12. utc.isoformat(…).replace (src/llm_wiki_cli/services…nce.py:authored_event_time)"]
    s1 -. "datetime.now(timezone.utc)" .-> s2
    s1 -. "isinstance(selected, str)" .-> s3
    s1 -. "datetime.fromisoformat(raw.replace(...))" .-> s4
    s1 -. "raw.replace('Z', '+00:00')" .-> s5
    s1 -->|"GovernanceError('authored_at', 'must be an RFC 3339 timestamp with timezone')"| s6
    s1 -. "isinstance(selected, datetime)" .-> s7
    s1 -->|"GovernanceError('authored_at', 'must be an RFC 3339 timestamp or datetime')"| s8
    s1 -. "parsed.utcoffset(data not statically known)" .-> s9
    s1 -->|"GovernanceError('authored_at', 'must include a timezone')"| s10
    s1 -. "parsed.astimezone(timezone.utc)" .-> s11
    s1 -. "utc.isoformat(…).replace (src/llm_wiki_cli/services…nce.py:authored_event_time)('+00:00', 'Z')" .-> s12
    click s1 "../modules/knowledge_governance.md"
    click s6 "../modules/knowledge_governance.md"
    click s8 "../modules/knowledge_governance.md"
    click s10 "../modules/knowledge_governance.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `authored_event_time` | `value: object` | `timezone`, `datetime`, `timezone` | - | `...`, `...` |
| `datetime.now` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `datetime.fromisoformat` | - | - | - | - |
| `raw.replace` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `parsed.utcoffset` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `parsed.astimezone` | - | - | - | - |
| `utc.isoformat(…).replace (src/llm_wiki_cli/services…nce.py:authored_event_time)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| authored_event_time | datetime.now | 1414 | `datetime.now(timezone.utc)` |
| authored_event_time | isinstance | 1415 | `isinstance(selected, str)` |
| authored_event_time | datetime.fromisoformat | 1418 | `datetime.fromisoformat(raw.replace(...))` |
| authored_event_time | raw.replace | 1418 | `raw.replace('Z', '+00:00')` |
| authored_event_time | GovernanceError | 1420 | `GovernanceError('authored_at', 'must be an RFC 3339 timestamp with timezone')` |
| authored_event_time | isinstance | 1424 | `isinstance(selected, datetime)` |
| authored_event_time | GovernanceError | 1427 | `GovernanceError('authored_at', 'must be an RFC 3339 timestamp or datetime')` |
| authored_event_time | parsed.utcoffset | 1431 | `parsed.utcoffset(data not statically known)` |
| authored_event_time | GovernanceError | 1432 | `GovernanceError('authored_at', 'must include a timezone')` |
| authored_event_time | parsed.astimezone | 1433 | `parsed.astimezone(timezone.utc)` |
| authored_event_time | utc.isoformat(…).replace (src/llm_wiki_cli/services…nce.py:authored_event_time) | 1435 | `utc.isoformat(timespec='microseconds').replace('+00:00', 'Z')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `authored_event_time` | `datetime.now` | 1414 |
| external_call | `authored_event_time` | `isinstance` | 1415 |
| external_call | `authored_event_time` | `datetime.fromisoformat` | 1418 |
| unresolved_call | `authored_event_time` | `raw.replace` | 1418 |
| external_call | `authored_event_time` | `isinstance` | 1424 |
| unresolved_call | `authored_event_time` | `parsed.utcoffset` | 1431 |
| unresolved_call | `authored_event_time` | `parsed.astimezone` | 1433 |
| unresolved_call | `authored_event_time` | `utc.isoformat(timespec='microseconds').replace` | 1435 |
| step_limit | `authored_event_time` | `first 12 steps` | 0 |

## Behavior

This flow starts at `authored_event_time` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
