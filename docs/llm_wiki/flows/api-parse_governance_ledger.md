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
    participant p3 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p4 as key.encode
    participant p5 as GovernanceError
    participant p6 as dict (src/llm_wiki_cli/services…dge_governance.py:_object)
    participant p7 as _exact_fields
    participant p8 as require_exact_fields
    participant p9 as isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p10 as str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p11 as set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p12 as tuple (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p13 as sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p14 as invalid_error
    participant p15 as error_factory
    participant p16 as _bundle_id
    participant p17 as validate_bundle_id
    participant p18 as _machine_text
    participant p19 as isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p20 as ConceptIdentityError
    p0->>p1: _object
    p1->>p2: require_mapping
    p2-->>p3: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p2-->>p3: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p2-->>p4: key.encode
    p1->>p5: GovernanceError
    p1->>p5: GovernanceError
    p1-->>p6: dict (src/llm_wiki_cli/services…dge_governance.py:_object)
    p0->>p7: _exact_fields
    p7->>p8: require_exact_fields
    p8-->>p9: isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p8-->>p10: str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p8-->>p11: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p8-->>p11: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p8-->>p11: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p8-->>p12: tuple (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p8-->>p13: sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p8-->>p12: tuple (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p8-->>p13: sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p8-->>p14: invalid_error
    p8-->>p15: error_factory
    p7->>p5: GovernanceError
    p7->>p5: GovernanceError
    p7->>p5: GovernanceError
    p0->>p5: GovernanceError
    p0->>p16: _bundle_id
    p16->>p17: validate_bundle_id
    p17->>p18: _machine_text
    p18-->>p19: isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)
    p18->>p20: ConceptIdentityError
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
    s4["4. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s5["5. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s6["6. key.encode"]
    s7["7. GovernanceError"]
    s8["8. GovernanceError"]
    s9["9. dict (src/llm_wiki_cli/services…dge_governance.py:_object)"]
    s10["10. _exact_fields"]
    s11["11. require_exact_fields"]
    s12["12. isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)"]
    s1 -->|"_object(payload, 'governance')"| s2
    s2 -->|"require_mapping(value, error=GovernanceError(...), require_string_keys=True, key_error=GovernanceError(...))"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s4
    s3 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s5
    s3 -. "key.encode('utf-8')" .-> s6
    s2 -->|"GovernanceError(path, 'must be an object')"| s7
    s2 -->|"GovernanceError(path, 'must use string keys')"| s8
    s2 -. "dict (src/llm_wiki_cli/services…dge_governance.py:_object)(selected)" .-> s9
    s1 -->|"_exact_fields(root, 'governance', {...})"| s10
    s10 -->|"require_exact_fields(value, allowed=..., required=required, mapping_error=GovernanceError(...), missing_error=..., unknown_error=...)"| s11
    s11 -. "isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)(value, Mapping)" .-> s12
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
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `key.encode` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…dge_governance.py:_object)` | - | - | - | - |
| `_exact_fields` | `value: Mapping[str, object]`, `path: str`, `required: set[str]`, `optional: set[str] \| frozenset[str]` | - | - | `require_shared_exact_fields(...)` |
| `require_exact_fields` | `value: object`, `allowed: Iterable[str]`, `required: Iterable[str]`, `mapping_error: Exception`, `missing_error: _ErrorFactory`, `unknown_error: _ErrorFactory`, `invalid_error: Callable[[tuple[str, ...], tuple[str, ...]], Exception] \| None`, `stringify_keys: bool` | `Mapping` | - | - |
| `isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| parse_governance_ledger | _object | 419 | `_object(payload, 'governance')` |
| _object | require_mapping | 3136 | `require_mapping(value, error=GovernanceError(...), require_string_keys=True, key_error=GovernanceError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 731 | `isinstance(key, str)` |
| require_mapping | key.encode | 736 | `key.encode('utf-8')` |
| _object | GovernanceError | 3138 | `GovernanceError(path, 'must be an object')` |
| _object | GovernanceError | 3140 | `GovernanceError(path, 'must use string keys')` |
| _object | dict (src/llm_wiki_cli/services…dge_governance.py:_object) | 3142 | `dict(selected)` |
| parse_governance_ledger | _exact_fields | 420 | `_exact_fields(root, 'governance', {...})` |
| _exact_fields | require_exact_fields | 3159 | `require_shared_exact_fields(value, allowed=..., required=required, mapping_error=GovernanceError(...), missing_error=..., unknown_error=...)` |
| require_exact_fields | isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields) | 1205 | `isinstance(value, Mapping)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_mapping` | `isinstance` | 727 |
| external_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| external_call | `require_exact_fields` | `isinstance` | 1205 |
| step_limit | `parse_governance_ledger` | `first 12 steps` | 0 |
| truncated_flow | `parse_governance_ledger` | `depth limit` | 0 |

## Behavior

This flow starts at `parse_governance_ledger` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
