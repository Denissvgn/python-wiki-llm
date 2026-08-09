# parse_governance_ledger

**Entry point:** `parse_governance_ledger` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 4 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_model](../modules/knowledge_model.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as parse_governance_ledger
    participant p1 as _object
    participant p2 as require_mapping
    participant p3 as isinstance
    participant p4 as encode
    participant p5 as GovernanceError
    participant p6 as dict
    participant p7 as _exact_fields
    participant p8 as require_exact_fields
    participant p9 as str
    participant p10 as set
    participant p11 as tuple
    participant p12 as sorted
    participant p13 as invalid_error
    participant p14 as error_factory
    participant p15 as _bundle_id
    participant p16 as validate_bundle_id
    participant p17 as _machine_text
    participant p18 as ConceptIdentityError
    p0->>p1: _object
    p1->>p2: require_mapping
    p2-->>p3: isinstance
    p2-->>p3: isinstance
    p2-->>p4: encode
    p1->>p5: GovernanceError
    p1->>p5: GovernanceError
    p1-->>p6: dict
    p0->>p7: _exact_fields
    p7->>p8: require_exact_fields
    p8-->>p3: isinstance
    p8-->>p9: str
    p8-->>p10: set
    p8-->>p10: set
    p8-->>p10: set
    p8-->>p11: tuple
    p8-->>p12: sorted
    p8-->>p11: tuple
    p8-->>p12: sorted
    p8-->>p13: invalid_error
    p8-->>p14: error_factory
    p7->>p5: GovernanceError
    p7->>p5: GovernanceError
    p7->>p5: GovernanceError
    p0->>p5: GovernanceError
    p0->>p15: _bundle_id
    p15->>p16: validate_bundle_id
    p16->>p17: _machine_text
    p17-->>p3: isinstance
    p17->>p18: ConceptIdentityError
```

> Call sequence diagram shows 30 of 436 interactions; 406 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. parse_governance_ledger"]
    s2["2. _object"]
    s3["3. require_mapping"]
    s4["4. isinstance"]
    s5["5. isinstance"]
    s6["6. encode"]
    s7["7. GovernanceError"]
    s8["8. GovernanceError"]
    s9["9. dict"]
    s10["10. _exact_fields"]
    s11["11. require_exact_fields"]
    s12["12. isinstance"]
    s1 -->|"_object(payload, 'governance')"| s2
    s2 -->|"require_mapping(value, error=GovernanceError(...), require_string_keys=True, key_error=GovernanceError(...))"| s3
    s3 -. "isinstance(value, Mapping)" .-> s4
    s3 -. "isinstance(key, str)" .-> s5
    s3 -. "key.encode('utf-8')" .-> s6
    s2 -->|"GovernanceError(path, 'must be an object')"| s7
    s2 -->|"GovernanceError(path, 'must use string keys')"| s8
    s2 -. "dict(selected)" .-> s9
    s1 -->|"_exact_fields(root, 'governance', {...})"| s10
    s10 -->|"require_shared_exact_fields(value, allowed=..., required=required, mapping_error=GovernanceError(...), missing_error=..., unknown_error=...)"| s11
    s11 -. "isinstance(value, Mapping)" .-> s12
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s3 "../modules/validation.md"
    click s7 "../modules/knowledge_governance.md"
    click s8 "../modules/knowledge_governance.md"
    click s10 "../modules/knowledge_governance.md"
    click s11 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `parse_governance_ledger` | `payload: object`, `expected_bundle_id: str \| None` | `GOVERNANCE_SCHEMA_VERSION`, `GOVERNANCE_SCHEMA_VERSION`, `ALIAS_NATURAL_KEY`, `ALIAS_LOCATOR` | `concepts[...]`, `aliases[...]` | `validate_governance_ledger(...)` |
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `dict` | - | - | - | - |
| `_exact_fields` | `value: Mapping[str, object]`, `path: str`, `required: set[str]`, `optional: set[str] \| frozenset[str]` | - | - | `require_shared_exact_fields(...)` |
| `require_exact_fields` | `value: object`, `allowed: Iterable[str]`, `required: Iterable[str]`, `mapping_error: Exception`, `missing_error: _ErrorFactory`, `unknown_error: _ErrorFactory`, `invalid_error: Callable[[tuple[str, ...], tuple[str, ...]], Exception] \| None`, `stringify_keys: bool` | `Mapping` | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| parse_governance_ledger | _object | 419 | `_object(payload, 'governance')` |
| _object | require_mapping | 3136 | `require_mapping(value, error=GovernanceError(...), require_string_keys=True, key_error=GovernanceError(...))` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance | 731 | `isinstance(key, str)` |
| require_mapping | encode | 736 | `key.encode('utf-8')` |
| _object | GovernanceError | 3138 | `GovernanceError(path, 'must be an object')` |
| _object | GovernanceError | 3140 | `GovernanceError(path, 'must use string keys')` |
| _object | dict | 3142 | `dict(selected)` |
| parse_governance_ledger | _exact_fields | 420 | `_exact_fields(root, 'governance', {...})` |
| _exact_fields | require_exact_fields | 3159 | `require_shared_exact_fields(value, allowed=..., required=required, mapping_error=GovernanceError(...), missing_error=..., unknown_error=...)` |
| require_exact_fields | isinstance | 1205 | `isinstance(value, Mapping)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| unresolved_call | `require_exact_fields` | `isinstance` | 1205 |
| step_limit | `parse_governance_ledger` | `first 12 steps` | 0 |
| truncated_flow | `parse_governance_ledger` | `depth limit` | 0 |

## Behavior

This flow starts at `parse_governance_ledger` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
