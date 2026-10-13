# build_p0_calibration_shadow

**Entry point:** `build_p0_calibration_shadow` (`api`)
**Source:** [documentation_run_dependencies](../modules/documentation_run_dependencies.md)
**Modules touched:** [calibration_contracts](../modules/calibration_contracts.md), [documentation_run_dependencies](../modules/documentation_run_dependencies.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_p0_calibration_shadow (src/llm_wiki_cli/services…ation_run/dependencies.py)
    participant p1 as build_p0_calibration_shadow (src/llm_wiki_cli/services/calibration/contracts.py)
    participant p2 as validate_flow_evidence_census
    participant p3 as _candidate_shadow
    participant p4 as _json_mapping
    participant p5 as _text_list
    participant p6 as _optional_text
    participant p7 as DocumentationCalibrationError
    participant p8 as filtered_trimmed_text_list
    participant p9 as trimmed_text_or_none
    participant p10 as isinstance (src/llm_wiki_cli/services…ild_p0_calibration_shadow)
    participant p11 as worklist.get
    participant p12 as item.get (src/llm_wiki_cli/services…ild_p0_calibration_shadow)
    participant p13 as canonical_path.startswith
    participant p14 as PurePosixPath
    participant p15 as structural_controls.append
    participant p16 as record.get
    participant p17 as str
    participant p18 as current_by_flow.get
    participant p19 as candidates.get
    participant p20 as shadow_items.append
    participant p21 as current.get
    p0->>p1: build_p0_calibration_shadow (src/llm_wiki_cli/services/calibration/contracts.py)
    p1->>p2: validate_flow_evidence_census
    p1->>p3: _candidate_shadow
    p3->>p4: _json_mapping
    p3->>p5: _text_list
    p3->>p6: _optional_text
    p1->>p7: DocumentationCalibrationError
    p5->>p8: filtered_trimmed_text_list
    p6->>p9: trimmed_text_or_none
    p1-->>p10: isinstance (src/llm_wiki_cli/services…ild_p0_calibration_shadow)(items, list)
    p1-->>p11: worklist.get('items')
    p1-->>p10: isinstance (src/llm_wiki_cli/services…ild_p0_calibration_shadow)(item, Mapping)
    p1-->>p12: item.get (src/llm_wiki_cli/services…ild_p0_calibration_shadow)('canonical_path')
    p1-->>p10: isinstance (src/llm_wiki_cli/services…ild_p0_calibration_shadow)(canonical_path, str)
    p1-->>p13: canonical_path.startswith('flows/')
    p1-->>p14: PurePosixPath(canonical_path)
    p1-->>p12: item.get (src/llm_wiki_cli/services…ild_p0_calibration_shadow)('priority')
    p1-->>p12: item.get (src/llm_wiki_cli/services…ild_p0_calibration_shadow)('category')
    p1-->>p15: structural_controls.append({...})
    p1-->>p12: item.get (src/llm_wiki_cli/services…ild_p0_calibration_shadow)('id')
    p1-->>p12: item.get (src/llm_wiki_cli/services…ild_p0_calibration_shadow)('category')
    p1-->>p10: isinstance (src/llm_wiki_cli/services…ild_p0_calibration_shadow)(record, Mapping)
    p1-->>p16: record.get('flow_id')
    p1-->>p16: record.get('candidate_priority')
    p1-->>p10: isinstance (src/llm_wiki_cli/services…ild_p0_calibration_shadow)(flow_id, str)
    p1-->>p17: str(capsule[...])
    p1-->>p18: current_by_flow.get(flow_id)
    p1-->>p19: candidates.get(flow_id)
    p1-->>p20: shadow_items.append({...})
    p1-->>p21: current.get('id')
```

> Call sequence diagram shows 30 of 185 interactions; 155 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 7 of 79 (72 omitted); unresolved 14 of 63 (49 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/calibration/contracts.py:validate_flow_evidence_census` | 3 | - | unresolved | 33 |
| `src/llm_wiki_cli/services/calibration/contracts.py:validate_flow_evidence_census` | 3 | [src/llm_wiki_cli/services/calibration/contracts.py](../modules/calibration_contracts.md) | internal | 24 |
| `src/llm_wiki_cli/services/calibration/contracts.py:validate_flow_evidence_census` | 3 | - | external | 44 |
| `src/llm_wiki_cli/services/calibration/contracts.py:build_p0_calibration_shadow` | 2 | [src/llm_wiki_cli/services/calibration/contracts.py](../modules/calibration_contracts.md) | internal | 4 |
| `src/llm_wiki_cli/services/calibration/contracts.py:build_p0_calibration_shadow` | 2 | - | unresolved | 6 |
| `src/llm_wiki_cli/services/calibration/contracts.py:build_p0_calibration_shadow` | 2 | - | external | 11 |
| `src/llm_wiki_cli/services/calibration/contracts.py:_candidate_shadow` | 133 | - | unresolved | 7 |
| `src/llm_wiki_cli/services/calibration/contracts.py:_candidate_shadow` | 133 | - | external | 9 |
> Omission summary shows 8 of 15 groups; 7 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_p0_calibration_shadow (src/llm_wiki_cli/services…ation_run/dependencies.py)"]
    s2["2. build_p0_calibration_shadow (src/llm_wiki_cli/services/calibration/contracts.py)"]
    s3["3. validate_flow_evidence_census"]
    s4["4. payload.get"]
    s5["5. DocumentationCalibrationError"]
    s6["6. payload.get"]
    s7["7. DocumentationCalibrationError"]
    s8["8. payload.get"]
    s9["9. isinstance (src/llm_wiki_cli/services…date_flow_evidence_census)"]
    s10["10. isinstance (src/llm_wiki_cli/services…date_flow_evidence_census)"]
    s11["11. population.get"]
    s12["12. DocumentationCalibrationError"]
    s1 -->|"build_p0_calibration_shadow (src/llm_wiki_cli/services/calibration/contracts.py)(…)"| s2
    s2 -->|"validate_flow_evidence_census(census)"| s3
    s3 -. "payload.get('schema_version')" .-> s4
    s3 -->|"DocumentationCalibrationError('Unsupported flow-census schema_version.')"| s5
    s3 -. "payload.get('priority_blind')" .-> s6
    s3 -->|"DocumentationCalibrationError('Flow census must remain priority_blind.')"| s7
    s3 -. "payload.get('population')" .-> s8
    s3 -. "isinstance (src/llm_wiki_cli/services…date_flow_evidence_census)(population, Mapping)" .-> s9
    s3 -. "isinstance (src/llm_wiki_cli/services…date_flow_evidence_census)(population.get(...), bool)" .-> s10
    s3 -. "population.get('complete')" .-> s11
    s3 -->|"DocumentationCalibrationError('Flow census population is malformed.')"| s12
    b0["mutation structural_controls.append"]
    s2 -. "mutation structural_controls.append" .-> b0
    b1["mutation shadow_items.append"]
    s2 -. "mutation shadow_items.append" .-> b1
    b2["mutation family_ids.add"]
    s3 -. "mutation family_ids.add" .-> b2
    b3["mutation family_members.extend"]
    s3 -. "mutation family_members.extend" .-> b3
    b4["mutation family_by_member.update"]
    s3 -. "mutation family_by_member.update" .-> b4
    click s1 "../modules/documentation_run_dependencies.md"
    click s2 "../modules/calibration_contracts.md"
    click s3 "../modules/calibration_contracts.md"
    click s5 "../modules/calibration_contracts.md"
    click s7 "../modules/calibration_contracts.md"
    click s12 "../modules/calibration_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_p0_calibration_shadow (src/llm_wiki_cli/services…ation_run/dependencies.py)` | `worklist: Mapping[str, Any]`, `census: Mapping[str, Any]`, `candidate_records: Optional[Iterable[Mapping[str, Any]]]`, `policy_version: str` | - | - | `implementation(...)` |
| `build_p0_calibration_shadow (src/llm_wiki_cli/services/calibration/contracts.py)` | `worklist: Mapping[str, Any]`, `census: Mapping[str, Any]`, `candidate_records: Optional[Iterable[Mapping[str, Any]]]`, `policy_version: str` | `Mapping`, `Mapping`, `_CALIBRATION_PRIORITIES`, `P0_CALIBRATION_SHADOW_SCHEMA_VERSION` | `current_by_flow[...]`, `candidates[...]` | `{...}` |
| `validate_flow_evidence_census` | `payload: Mapping[str, Any]` | `P0_FLOW_CENSUS_SCHEMA_VERSION`, `Mapping`, `Mapping`, `_SOURCE_PROVENANCE`, `Mapping`, `Mapping`, `Mapping`, `Mapping` | - | - |
| `payload.get` | - | - | - | - |
| `DocumentationCalibrationError` | - | - | - | - |
| `payload.get` | - | - | - | - |
| `DocumentationCalibrationError` | - | - | - | - |
| `payload.get` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…date_flow_evidence_census)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…date_flow_evidence_census)` | - | - | - | - |
| `population.get` | - | - | - | - |
| `DocumentationCalibrationError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_p0_calibration_shadow (src/llm_wiki_cli/services…ation_run/dependencies.py) | build_p0_calibration_shadow (src/llm_wiki_cli/services/calibration/contracts.py) | 165 | `implementation(worklist, census, candidate_records=candidate_records, policy_version=policy_version)` |
| build_p0_calibration_shadow (src/llm_wiki_cli/services/calibration/contracts.py) | validate_flow_evidence_census | 381 | `validate_flow_evidence_census(census)` |
| validate_flow_evidence_census | payload.get | 237 | `payload.get('schema_version')` |
| validate_flow_evidence_census | DocumentationCalibrationError | 238 | `DocumentationCalibrationError('Unsupported flow-census schema_version.')` |
| validate_flow_evidence_census | payload.get | 239 | `payload.get('priority_blind')` |
| validate_flow_evidence_census | DocumentationCalibrationError | 240 | `DocumentationCalibrationError('Flow census must remain priority_blind.')` |
| validate_flow_evidence_census | payload.get | 241 | `payload.get('population')` |
| validate_flow_evidence_census | isinstance (src/llm_wiki_cli/services…date_flow_evidence_census) | 242 | `isinstance(population, Mapping)` |
| validate_flow_evidence_census | isinstance (src/llm_wiki_cli/services…date_flow_evidence_census) | 242 | `isinstance(population.get(...), bool)` |
| validate_flow_evidence_census | population.get | 243 | `population.get('complete')` |
| validate_flow_evidence_census | DocumentationCalibrationError | 245 | `DocumentationCalibrationError('Flow census population is malformed.')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `structural_controls.append` | `build_p0_calibration_shadow` | 398 |
| mutation | `shadow_items.append` | `build_p0_calibration_shadow` | 430 |
| mutation | `family_ids.add` | `validate_flow_evidence_census` | 351 |
| mutation | `family_members.extend` | `validate_flow_evidence_census` | 353 |
| mutation | `family_by_member.update` | `validate_flow_evidence_census` | 354 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_flow_evidence_census` | `payload.get` | 237 |
| unresolved_call | `validate_flow_evidence_census` | `payload.get` | 239 |
| unresolved_call | `validate_flow_evidence_census` | `payload.get` | 241 |
| external_call | `validate_flow_evidence_census` | `isinstance` | 242 |
| unresolved_call | `validate_flow_evidence_census` | `population.get` | 243 |
| step_limit | `build_p0_calibration_shadow` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_p0_calibration_shadow` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
