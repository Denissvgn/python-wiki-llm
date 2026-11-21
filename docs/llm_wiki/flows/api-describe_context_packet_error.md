# describe_context_packet_error

**Entry point:** `describe_context_packet_error` (`api`)
**Source:** [context_packet_builder](../modules/context_packet_builder.md)
**Modules touched:** [context_packet_builder](../modules/context_packet_builder.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as describe_context_packet_error
    participant p1 as isinstance
    participant p2 as str
    participant p3 as deepcopy
    participant p4 as getattr
    participant p5 as {'source': 'source_snapshot', 'wiki': 'wiki_dir'}.get
    participant p6 as re.match
    participant p7 as flag.group
    participant p8 as set
    participant p9 as id
    participant p10 as seen.add
    participant p11 as candidate.group
    participant p12 as re.split
    participant p13 as field.lstrip
    p0-->>p1: isinstance(error, HelperPreparationError)
    p0-->>p1: isinstance(error, ContextPacketAuthorityError)
    p0-->>p2: str(error)
    p0-->>p3: deepcopy(error.details)
    p0-->>p4: getattr(error, 'field', None)
    p0-->>p1: isinstance(error, ContextPacketMalformedError)
    p0-->>p1: isinstance(error, ContextPacketSourceMutationError)
    p0-->>p5: {'source': 'source_snapshot', 'wiki': 'wiki_dir'}.get(error.facet, error.facet)
    p0-->>p1: isinstance(error, ContextPacketUnavailableError)
    p0-->>p1: isinstance(error, (...))
    p0-->>p1: isinstance(error, PathValidationError)
    p0-->>p6: re.match('^(?:Error:\\s*)?--(src|wiki)-dir\\b', str(...))
    p0-->>p2: str(error)
    p0-->>p7: flag.group(1)
    p0-->>p8: set
    p0-->>p9: id(cause)
    p0-->>p10: seen.add(id(...))
    p0-->>p9: id(cause)
    p0-->>p1: isinstance(cause, OSError)
    p0-->>p1: isinstance(cause, OSError)
    p0-->>p1: isinstance(error, context_service.ProtocolRequestError)
    p0-->>p1: isinstance(error, (...))
    p0-->>p6: re.match('^([a-z_]+)\\b', str(...))
    p0-->>p2: str(error)
    p0-->>p11: candidate.group(1)
    p0-->>p11: candidate.group(1)
    p0-->>p1: isinstance(field, str)
    p0-->>p12: re.split('[.\\[/]', field.lstrip(...))
    p0-->>p13: field.lstrip('$./')
```

> Call sequence diagram shows 29 of 29 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 23 of 23 (0 omitted); unresolved 6 of 6 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 13, emitted: 13, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. describe_context_packet_error"]
    s2["2. isinstance"]
    s3["3. isinstance"]
    s4["4. str"]
    s5["5. deepcopy"]
    s6["6. getattr"]
    s7["7. isinstance"]
    s8["8. isinstance"]
    s9["9. {'source': 'source_snapshot', 'wiki': 'wiki_dir'}.get"]
    s10["10. isinstance"]
    s11["11. isinstance"]
    s12["12. isinstance"]
    s1 -. "isinstance(error, HelperPreparationError)" .-> s2
    s1 -. "isinstance(error, ContextPacketAuthorityError)" .-> s3
    s1 -. "str(error)" .-> s4
    s1 -. "deepcopy(error.details)" .-> s5
    s1 -. "getattr(error, 'field', None)" .-> s6
    s1 -. "isinstance(error, ContextPacketMalformedError)" .-> s7
    s1 -. "isinstance(error, ContextPacketSourceMutationError)" .-> s8
    s1 -. "{'source': 'source_snapshot', 'wiki': 'wiki_dir'}.get(error.facet, error.facet)" .-> s9
    s1 -. "isinstance(error, ContextPacketUnavailableError)" .-> s10
    s1 -. "isinstance(error, (...))" .-> s11
    s1 -. "isinstance(error, PathValidationError)" .-> s12
    b0["mutation seen.add"]
    s1 -. "mutation seen.add" .-> b0
    click s1 "../modules/context_packet_builder.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `describe_context_packet_error` | `error: BaseException` | `ContextPacketAuthorityError`, `ContextPacketMalformedError`, `ContextPacketSourceMutationError`, `ContextPacketUnavailableError`, `ContextPacketPathPolicyError`, `PathValidationError`, `PathValidationError`, `context_service` | - | `{...}`, `{...}`, `{...}` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `str` | - | - | - | - |
| `deepcopy` | - | - | - | - |
| `getattr` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `{'source': 'source_snapshot', 'wiki': 'wiki_dir'}.get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| describe_context_packet_error | isinstance | 176 | `isinstance(error, HelperPreparationError)` |
| describe_context_packet_error | isinstance | 184 | `isinstance(error, ContextPacketAuthorityError)` |
| describe_context_packet_error | str | 185 | `str(error)` |
| describe_context_packet_error | deepcopy | 185 | `deepcopy(error.details)` |
| describe_context_packet_error | getattr | 186 | `getattr(error, 'field', None)` |
| describe_context_packet_error | isinstance | 189 | `isinstance(error, ContextPacketMalformedError)` |
| describe_context_packet_error | isinstance | 200 | `isinstance(error, ContextPacketSourceMutationError)` |
| describe_context_packet_error | {'source': 'source_snapshot', 'wiki': 'wiki_dir'}.get | 202 | `{'source': 'source_snapshot', 'wiki': 'wiki_dir'}.get(error.facet, error.facet)` |
| describe_context_packet_error | isinstance | 206 | `isinstance(error, ContextPacketUnavailableError)` |
| describe_context_packet_error | isinstance | 209 | `isinstance(error, (...))` |
| describe_context_packet_error | isinstance | 211 | `isinstance(error, PathValidationError)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen.add` | `describe_context_packet_error` | 217 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `describe_context_packet_error` | `isinstance` | 176 |
| external_call | `describe_context_packet_error` | `isinstance` | 184 |
| external_call | `describe_context_packet_error` | `deepcopy` | 185 |
| external_call | `describe_context_packet_error` | `getattr` | 186 |
| external_call | `describe_context_packet_error` | `isinstance` | 189 |
| external_call | `describe_context_packet_error` | `isinstance` | 200 |
| unresolved_call | `describe_context_packet_error` | `{'source': 'source_snapshot', 'wiki': 'wiki_dir'}.get` | 202 |
| external_call | `describe_context_packet_error` | `isinstance` | 206 |
| external_call | `describe_context_packet_error` | `isinstance` | 209 |
| external_call | `describe_context_packet_error` | `isinstance` | 211 |
| step_limit | `describe_context_packet_error` | `first 12 steps` | 0 |

## Behavior

This flow starts at `describe_context_packet_error` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
