# reconcile_claim_evidence_records

**Entry point:** `reconcile_claim_evidence_records` (`api`)
**Source:** [documentation_claim_evidence](../modules/documentation_claim_evidence.md)
**Modules touched:** [documentation_claim_evidence](../modules/documentation_claim_evidence.md), [knowledge_graph](../modules/knowledge_graph.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as reconcile_claim_evidence_records
    participant p1 as _normalize_claim_record
    participant p2 as qualify_claim_evidence
    participant p3 as DocumentationClaimEvidenceError
    participant p4 as _mapping
    participant p5 as _exact_fields
    participant p6 as _portable_path
    participant p7 as _enum
    participant p8 as _optional_identifier
    participant p9 as _optional_locator
    participant p10 as _section_locator
    participant p11 as _structural_evidence
    participant p12 as _freshness
    participant p13 as _lifecycle_review
    participant p14 as _normalize_graph_query
    participant p15 as _bounds
    participant p16 as _safe_evidence_link
    participant p17 as _internal_evidence_ref
    participant p18 as _current_lifecycle_review
    participant p19 as require_mapping
    participant p20 as require_exact_fields
    participant p21 as _text
    participant p22 as require_exact_choice
    participant p23 as _identifier
    participant p24 as require_portable_relative_path
    participant p25 as _bound_record
    participant p26 as _reason
    participant p27 as _bound
    participant p28 as _analyzer_bounds
    participant p29 as isinstance (src/llm_wiki_cli/services…le_claim_evidence_records)
    participant p30 as record.get (src/llm_wiki_cli/services…le_claim_evidence_records)
    p0->>p1: _normalize_claim_record
    p0->>p2: qualify_claim_evidence
    p0->>p3: DocumentationClaimEvidenceError
    p1->>p4: _mapping
    p1->>p5: _exact_fields
    p1->>p6: _portable_path
    p1->>p7: _enum
    p1->>p8: _optional_identifier
    p1->>p9: _optional_locator
    p1->>p10: _section_locator
    p1->>p11: _structural_evidence
    p1->>p12: _freshness
    p1->>p13: _lifecycle_review
    p1->>p14: _normalize_graph_query
    p1->>p15: _bounds
    p1->>p16: _safe_evidence_link
    p1->>p17: _internal_evidence_ref
    p2->>p18: _current_lifecycle_review
    p4->>p19: require_mapping
    p5->>p20: require_exact_fields
    p6->>p21: _text
    p7->>p22: require_exact_choice
    p8->>p23: _identifier
    p6->>p24: require_portable_relative_path
    p15->>p25: _bound_record
    p11->>p26: _reason
    p18->>p27: _bound
    p15->>p28: _analyzer_bounds
    p0-->>p29: isinstance (src/llm_wiki_cli/services…le_claim_evidence_records)(record_freshness, Mapping)
    p0-->>p30: record.get (src/llm_wiki_cli/services…le_claim_evidence_records)('section_locator')
```

> Call sequence diagram shows 30 of 358 interactions; 328 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 100 (99 omitted); unresolved 1 of 87 (86 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 3 |
| `src/llm_wiki_cli/services/validation.py:_validation_error` | 6 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_validation_error` | 6 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/documentation_claim_evidence.py:_mapping` | 3 | [src/llm_wiki_cli/services/documentation_claim_evidence.py](../modules/documentation_claim_evidence.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 15 | - | external | 9 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 15 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
> Omission summary shows 8 of 92 groups; 84 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 172; effect analysis evaluated: 118, partial: 4, unavailable: 50. Counts include steps omitted from the displayed trace.

Collector observations for 122 source steps with known totals: observed: 509, emitted: 495, omitted: 14. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `reconcile_claim_evidence_records` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `_normalize_claim_record` | `available` | `evaluated` | `available` | `8` | `8` | `0` |
| `_mapping` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `require_mapping` | `available` | `evaluated` | `available` | `9` | `9` | `0` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validation_error` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `error` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validation_error` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `key.encode` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validation_error` | `available` | `evaluated` | `available` | `3` | `3` | `0` |

```mermaid
flowchart LR
    s1["1. reconcile_claim_evidence_records"]
    s2["2. _normalize_claim_record"]
    s3["3. _mapping"]
    s4["4. require_mapping"]
    s5["5. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s6["6. _validation_error"]
    s7["7. isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)"]
    s8["8. error"]
    s9["9. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s10["10. _validation_error"]
    s11["11. key.encode"]
    s12["12. _validation_error"]
    s1 -->|"_normalize_claim_record(raw, 'claim_evidence')"| s2
    s2 -->|"_mapping(value, field_name)"| s3
    s3 -->|"require_mapping(value, error=DocumentationClaimEvidenceError(...), require_string_keys=True)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s5
    s4 -->|"_validation_error(error, error_context)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)(error, Exception)" .-> s7
    s6 -. "error(context)" .-> s8
    s4 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s9
    s4 -->|"_validation_error(..., error_context)"| s10
    s4 -. "key.encode('utf-8')" .-> s11
    s4 -->|"_validation_error(..., error_context)"| s12
    b0["mutation legacy_freshness.pop"]
    s1 -. "mutation legacy_freshness.pop" .-> b0
    b1["mutation reconciled.append"]
    s1 -. "mutation reconciled.append" .-> b1
    click s1 "../modules/documentation_claim_evidence.md"
    click s2 "../modules/documentation_claim_evidence.md"
    click s3 "../modules/documentation_claim_evidence.md"
    click s4 "../modules/validation.md"
    click s6 "../modules/validation.md"
    click s10 "../modules/validation.md"
    click s12 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `reconcile_claim_evidence_records` | `records: Iterable[Mapping[str, Any]]`, `service: DocumentationGraphQueryService` | `Mapping`, `_CLAIM_FIELDS` | - | `tuple(...)` |
| `_normalize_claim_record` | `value: object`, `field_name: str` | `_CLAIM_FIELDS`, `_CLAIM_REQUIRED`, `CLAIM_EVIDENCE_SCHEMA_VERSION`, `_RESOLUTIONS`, `CLAIM_EVIDENCE_SCHEMA_VERSION` | - | `{...}` |
| `_mapping` | `value: object`, `field_name: str` | - | - | `require_mapping(...)` |
| `require_mapping` | `value: object`, `error: _ValidationError`, `error_context: str`, `require_string_keys: bool`, `key_error: _ValidationError \| None`, `require_utf8_keys: bool`, `utf8_key_error: _ValidationError \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)` | - | - | - | - |
| `error` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `key.encode` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| reconcile_claim_evidence_records | _normalize_claim_record | 400 | `_normalize_claim_record(raw, 'claim_evidence')` |
| _normalize_claim_record | _mapping | 592 | `_mapping(value, field_name)` |
| _mapping | require_mapping | 1423 | `require_mapping(value, error=DocumentationClaimEvidenceError(...), require_string_keys=True)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 783 | `isinstance(value, Mapping)` |
| require_mapping | _validation_error | 784 | `_validation_error(error, error_context)` |
| _validation_error | isinstance (src/llm_wiki_cli/services…tion.py:_validation_error) | 95 | `isinstance(error, Exception)` |
| _validation_error | error | 95 | `error(context)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 787 | `isinstance(key, str)` |
| require_mapping | _validation_error | 788 | `_validation_error(..., error_context)` |
| require_mapping | key.encode | 792 | `key.encode('utf-8')` |
| require_mapping | _validation_error | 794 | `_validation_error(..., error_context)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `legacy_freshness.pop` | `reconcile_claim_evidence_records` | 418 |
| mutation | `reconciled.append` | `reconcile_claim_evidence_records` | 433 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_mapping` | `isinstance` | 783 |
| external_call | `_validation_error` | `isinstance` | 95 |
| unresolved_call | `_validation_error` | `error` | 95 |
| external_call | `require_mapping` | `isinstance` | 787 |
| unresolved_call | `require_mapping` | `key.encode` | 792 |
| step_limit | `reconcile_claim_evidence_records` | `first 12 steps` | 0 |
| truncated_flow | `reconcile_claim_evidence_records` | `depth limit` | 0 |

## Behavior

This flow starts at `reconcile_claim_evidence_records` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
