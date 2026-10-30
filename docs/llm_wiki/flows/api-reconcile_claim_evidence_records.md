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
    participant p19 as _text
    participant p20 as require_exact_choice
    participant p21 as _identifier
    participant p22 as require_portable_relative_path
    participant p23 as _bound_record
    participant p24 as _reason
    participant p25 as _bound
    participant p26 as _analyzer_bounds
    participant p27 as _string_list
    participant p28 as require_trimmed_text
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
    p6->>p19: _text
    p7->>p20: require_exact_choice
    p8->>p21: _identifier
    p6->>p22: require_portable_relative_path
    p15->>p23: _bound_record
    p11->>p24: _reason
    p18->>p25: _bound
    p15->>p26: _analyzer_bounds
    p13->>p27: _string_list
    p19->>p28: require_trimmed_text
    p0-->>p29: isinstance (src/llm_wiki_cli/services…le_claim_evidence_records)(record_freshness, Mapping)
    p0-->>p30: record.get (src/llm_wiki_cli/services…le_claim_evidence_records)('section_locator')
```

> Call sequence diagram shows 30 of 345 interactions; 315 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 99 (98 omitted); unresolved 1 of 86 (85 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_claim_evidence.py:_mapping` | 3 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/documentation_claim_evidence.py:_mapping` | 3 | [src/llm_wiki_cli/services/documentation_claim_evidence.py](../modules/documentation_claim_evidence.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_claim_evidence.py:_exact_fields` | 9 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 10 | - | external | 9 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 10 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/documentation_claim_evidence.py:_exact_fields` | 9 | [src/llm_wiki_cli/services/documentation_claim_evidence.py](../modules/documentation_claim_evidence.md) | internal | 3 |
> Omission summary shows 8 of 88 groups; 80 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 161; effect analysis evaluated: 107, partial: 4, unavailable: 50. Counts include steps omitted from the displayed trace.

Collector observations for 111 source steps with known totals: observed: 469, emitted: 456, omitted: 13. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `reconcile_claim_evidence_records` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `_normalize_claim_record` | `available` | `evaluated` | `available` | `8` | `8` | `0` |
| `_mapping` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `require_mapping` | `available` | `evaluated` | `available` | `8` | `8` | `0` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `key.encode` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `DocumentationClaimEvidenceError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_exact_fields` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `require_exact_fields` | `available` | `partial` | `available` | `10` | `9` | `1` |
| `isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `str (src/llm_wiki_cli/services…n.py:require_exact_fields)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. reconcile_claim_evidence_records"]
    s2["2. _normalize_claim_record"]
    s3["3. _mapping"]
    s4["4. require_mapping"]
    s5["5. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s6["6. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s7["7. key.encode"]
    s8["8. DocumentationClaimEvidenceError"]
    s9["9. _exact_fields"]
    s10["10. require_exact_fields"]
    s11["11. isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)"]
    s12["12. str (src/llm_wiki_cli/services…n.py:require_exact_fields)"]
    s1 -->|"_normalize_claim_record(raw, 'claim_evidence')"| s2
    s2 -->|"_mapping(value, field_name)"| s3
    s3 -->|"require_mapping(value, error=DocumentationClaimEvidenceError(...), require_string_keys=True)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s5
    s4 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s6
    s4 -. "key.encode('utf-8')" .-> s7
    s3 -->|"DocumentationClaimEvidenceError(...)"| s8
    s2 -->|"_exact_fields(record, _CLAIM_FIELDS, _CLAIM_REQUIRED, field_name)"| s9
    s9 -->|"require_exact_fields(value, allowed=allowed, required=required, mapping_error=DocumentationClaimEvidenceError(...), missing_error=..., unknown_error=...)"| s10
    s10 -. "isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)(value, Mapping)" .-> s11
    s10 -. "str (src/llm_wiki_cli/services…n.py:require_exact_fields)(key)" .-> s12
    b0["mutation legacy_freshness.pop"]
    s1 -. "mutation legacy_freshness.pop" .-> b0
    b1["mutation reconciled.append"]
    s1 -. "mutation reconciled.append" .-> b1
    click s1 "../modules/documentation_claim_evidence.md"
    click s2 "../modules/documentation_claim_evidence.md"
    click s3 "../modules/documentation_claim_evidence.md"
    click s4 "../modules/validation.md"
    click s8 "../modules/documentation_claim_evidence.md"
    click s9 "../modules/documentation_claim_evidence.md"
    click s10 "../modules/validation.md"
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
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `key.encode` | - | - | - | - |
| `DocumentationClaimEvidenceError` | - | - | - | - |
| `_exact_fields` | `value: Mapping[str, Any]`, `allowed: frozenset[str]`, `required: frozenset[str]`, `field_name: str` | - | - | `require_exact_fields(...)` |
| `require_exact_fields` | `value: object`, `allowed: Iterable[str]`, `required: Iterable[str]`, `mapping_error: Exception`, `missing_error: _ErrorFactory`, `unknown_error: _ErrorFactory`, `invalid_error: Callable[[tuple[str, ...], tuple[str, ...]], Exception] \| None`, `stringify_keys: bool` | `Mapping` | - | - |
| `isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)` | - | - | - | - |
| `str (src/llm_wiki_cli/services…n.py:require_exact_fields)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| reconcile_claim_evidence_records | _normalize_claim_record | 400 | `_normalize_claim_record(raw, 'claim_evidence')` |
| _normalize_claim_record | _mapping | 592 | `_mapping(value, field_name)` |
| _mapping | require_mapping | 1423 | `require_mapping(value, error=DocumentationClaimEvidenceError(...), require_string_keys=True)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 773 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 777 | `isinstance(key, str)` |
| require_mapping | key.encode | 782 | `key.encode('utf-8')` |
| _mapping | DocumentationClaimEvidenceError | 1425 | `DocumentationClaimEvidenceError(...)` |
| _normalize_claim_record | _exact_fields | 593 | `_exact_fields(record, _CLAIM_FIELDS, _CLAIM_REQUIRED, field_name)` |
| _exact_fields | require_exact_fields | 1447 | `require_exact_fields(value, allowed=allowed, required=required, mapping_error=DocumentationClaimEvidenceError(...), missing_error=..., unknown_error=...)` |
| require_exact_fields | isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields) | 1251 | `isinstance(value, Mapping)` |
| require_exact_fields | str (src/llm_wiki_cli/services…n.py:require_exact_fields) | 1253 | `str(key)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `legacy_freshness.pop` | `reconcile_claim_evidence_records` | 418 |
| mutation | `reconciled.append` | `reconcile_claim_evidence_records` | 433 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_mapping` | `isinstance` | 773 |
| external_call | `require_mapping` | `isinstance` | 777 |
| unresolved_call | `require_mapping` | `key.encode` | 782 |
| external_call | `require_exact_fields` | `isinstance` | 1251 |
| step_limit | `reconcile_claim_evidence_records` | `first 12 steps` | 0 |
| truncated_flow | `reconcile_claim_evidence_records` | `depth limit` | 0 |

## Behavior

This flow starts at `reconcile_claim_evidence_records` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
