# compare_publication_impact

**Entry point:** `compare_publication_impact` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [knowledge_evidence](../modules/knowledge_evidence.md), [publication_contracts](../modules/publication_contracts.md), [publication_impact](../modules/publication_impact.md), and 1 more

**Complete modules touched:**

- [api](../modules/api.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [publication_contracts](../modules/publication_contracts.md)
- [publication_impact](../modules/publication_impact.md)
- [publication_references](../modules/publication_references.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_publication_impact (src/llm_wiki_cli/api.py)
    participant p1 as compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py)
    participant p2 as validate_publication_basis
    participant p3 as _topic_findings
    participant p4 as validate_publication_reviews
    participant p5 as _seal
    participant p6 as _guard
    participant p7 as _topic_versions
    participant p8 as _topic_inputs
    participant p9 as _finding
    participant p10 as _json_tree
    participant p11 as _dependency_basis
    participant p12 as hash_json
    participant p13 as reference_dependency_basis
    participant p14 as _fail
    participant p15 as canonical_json_bytes
    participant p16 as PublicationProtocolError
    participant p17 as _reviewable_target
    participant p18 as sha256_bytes
    participant p19 as canonical_json_text
    participant p20 as reference_identity
    participant p21 as _ancestor_context
    participant p22 as deepcopy (src/llm_wiki_cli/services…ompare_publication_impact)
    participant p23 as findings.append (src/llm_wiki_cli/services…ompare_publication_impact)
    participant p24 as dict
    participant p25 as any (src/llm_wiki_cli/services…ompare_publication_impact)
    participant p26 as fnmatchcase
    participant p27 as sorted (src/llm_wiki_cli/services…ompare_publication_impact)
    p0->>p1: compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py)
    p1->>p2: validate_publication_basis
    p1->>p3: _topic_findings
    p1->>p4: validate_publication_reviews
    p1->>p5: _seal
    p2->>p6: _guard
    p3->>p7: _topic_versions
    p3->>p8: _topic_inputs
    p3->>p9: _finding
    p6->>p10: _json_tree
    p8->>p11: _dependency_basis
    p7->>p12: hash_json
    p11->>p13: reference_dependency_basis
    p10->>p14: _fail
    p12->>p15: canonical_json_bytes
    p1->>p16: PublicationProtocolError
    p1->>p17: _reviewable_target
    p12->>p18: sha256_bytes
    p15->>p19: canonical_json_text
    p13->>p20: reference_identity
    p13->>p21: _ancestor_context
    p1-->>p22: deepcopy (src/llm_wiki_cli/services…ompare_publication_impact)(dict(...))
    p1-->>p23: findings.append (src/llm_wiki_cli/services…ompare_publication_impact)(_finding(...))
    p1-->>p24: dict(candidate)
    p1-->>p22: deepcopy (src/llm_wiki_cli/services…ompare_publication_impact)(dict(...))
    p1-->>p24: dict(baseline)
    p1-->>p25: any (src/llm_wiki_cli/services…ompare_publication_impact)(...)
    p1-->>p26: fnmatchcase(p, e[...])
    p1-->>p27: sorted (src/llm_wiki_cli/services…ompare_publication_impact)(...)
    p1-->>p25: any (src/llm_wiki_cli/services…ompare_publication_impact)(...)
```

> Call sequence diagram shows 30 of 122 interactions; 92 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 32 (24 omitted); unresolved 1 of 52 (51 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/publication_contracts.py:_json_tree` | 9 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/publication_contracts.py:_fail` | 11 | [src/llm_wiki_cli/services/publication_contracts.py](../modules/publication_contracts.md) | internal | 1 |
| `src/llm_wiki_cli/services/publication_contracts.py:_json_tree` | 9 | - | external | 7 |
| `src/llm_wiki_cli/services/publication_contracts.py:_json_tree` | 9 | [src/llm_wiki_cli/services/publication_contracts.py](../modules/publication_contracts.md) | internal | 3 |
| `src/llm_wiki_cli/services/publication_contracts.py:_guard` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/publication_contracts.py:_guard` | 8 | [src/llm_wiki_cli/services/publication_contracts.py](../modules/publication_contracts.md) | internal | 1 |
| `src/llm_wiki_cli/services/publication_impact.py:compare_publication_impact` | 2 | [src/llm_wiki_cli/services/publication_contracts.py](../modules/publication_contracts.md) | internal | 2 |
| `src/llm_wiki_cli/services/publication_impact.py:_topic_versions` | 32 | - | external | 1 |
> Omission summary shows 8 of 31 groups; 23 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 39; effect analysis evaluated: 34, partial: 0, unavailable: 5. Counts include steps omitted from the displayed trace.

Collector observations for 34 source steps with known totals: observed: 121, emitted: 121, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `compare_publication_impact (src/llm_wiki_cli/api.py)` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py)` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `deepcopy (src/llm_wiki_cli/services…ompare_publication_impact)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `dict` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `deepcopy (src/llm_wiki_cli/services…ompare_publication_impact)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `dict` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `validate_publication_basis` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_guard` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_json_tree` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `pending.pop` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_fail` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `PublicationProtocolError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. compare_publication_impact (src/llm_wiki_cli/api.py)"]
    s2["2. compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py)"]
    s3["3. deepcopy (src/llm_wiki_cli/services…ompare_publication_impact)"]
    s4["4. dict"]
    s5["5. deepcopy (src/llm_wiki_cli/services…ompare_publication_impact)"]
    s6["6. dict"]
    s7["7. validate_publication_basis"]
    s8["8. _guard"]
    s9["9. _json_tree"]
    s10["10. pending.pop"]
    s11["11. _fail"]
    s12["12. PublicationProtocolError"]
    s1 -->|"compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py)(candidate, baseline, reviews=reviews)"| s2
    s2 -. "deepcopy (src/llm_wiki_cli/services…ompare_publication_impact)(dict(...))" .-> s3
    s2 -. "dict(candidate)" .-> s4
    s2 -. "deepcopy (src/llm_wiki_cli/services…ompare_publication_impact)(dict(...))" .-> s5
    s2 -. "dict(baseline)" .-> s6
    s2 -->|"validate_publication_basis(after)"| s7
    s7 -->|"_guard(_basis, value)"| s8
    s8 -->|"_json_tree(value)"| s9
    s9 -. "pending.pop(data not statically known)" .-> s10
    s9 -->|"_fail('document', 'exceeds JSON structural bounds')"| s11
    s11 -->|"PublicationProtocolError(...)"| s12
    b0["mutation findings.append"]
    s2 -. "mutation findings.append" .-> b0
    b1["mutation pending.pop"]
    s9 -. "mutation pending.pop" .-> b1
    b2["mutation pending.extend"]
    s9 -. "mutation pending.extend" .-> b2
    b3["mutation pending.extend"]
    s9 -. "mutation pending.extend" .-> b3
    click s1 "../modules/api.md"
    click s2 "../modules/publication_impact.md"
    click s7 "../modules/publication_contracts.md"
    click s8 "../modules/publication_contracts.md"
    click s9 "../modules/publication_contracts.md"
    click s11 "../modules/publication_contracts.md"
    click s12 "../modules/publication_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compare_publication_impact (src/llm_wiki_cli/api.py)` | `candidate: Mapping[str, Any]`, `baseline: Mapping[str, Any] \| None`, `reviews: Mapping[str, Any] \| None` | - | - | `compare(...)` |
| `compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py)` | `candidate: Mapping[str, Any]`, `baseline: Mapping[str, Any] \| None`, `reviews: Mapping[str, Any] \| None` | `IMPACT_SCHEMA` | `finding[...]` | `_seal(...)` |
| `deepcopy (src/llm_wiki_cli/services…ompare_publication_impact)` | - | - | - | - |
| `dict` | - | - | - | - |
| `deepcopy (src/llm_wiki_cli/services…ompare_publication_impact)` | - | - | - | - |
| `dict` | - | - | - | - |
| `validate_publication_basis` | `value: object` | `_basis` | - | - |
| `_guard` | `callback`, `value: object` | `PublicationProtocolError` | - | `callback(...)` |
| `_json_tree` | `value: object` | `Mapping` | - | - |
| `pending.pop` | - | - | - | - |
| `_fail` | `field: str`, `message: str` | - | - | - |
| `PublicationProtocolError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compare_publication_impact (src/llm_wiki_cli/api.py) | compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py) | 3606 | `compare(candidate, baseline, reviews=reviews)` |
| compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py) | deepcopy (src/llm_wiki_cli/services…ompare_publication_impact) | 373 | `deepcopy(dict(...))` |
| compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py) | dict | 373 | `dict(candidate)` |
| compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py) | deepcopy (src/llm_wiki_cli/services…ompare_publication_impact) | 374 | `deepcopy(dict(...))` |
| compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py) | dict | 374 | `dict(baseline)` |
| compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py) | validate_publication_basis | 375 | `validate_publication_basis(after)` |
| validate_publication_basis | _guard | 880 | `_guard(_basis, value)` |
| _guard | _json_tree | 870 | `_json_tree(value)` |
| _json_tree | pending.pop | 134 | `pending.pop(data not statically known)` |
| _json_tree | _fail | 137 | `_fail('document', 'exceeds JSON structural bounds')` |
| _fail | PublicationProtocolError | 42 | `PublicationProtocolError(...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `findings.append` | `compare_publication_impact` | 399 |
| mutation | `pending.pop` | `_json_tree` | 134 |
| mutation | `pending.extend` | `_json_tree` | 141 |
| mutation | `pending.extend` | `_json_tree` | 143 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `compare_publication_impact` | `deepcopy` | 373 |
| external_call | `compare_publication_impact` | `deepcopy` | 374 |
| step_limit | `compare_publication_impact` | `first 12 steps` | 0 |
| truncated_flow | `compare_publication_impact` | `depth limit` | 0 |

## Behavior

This flow starts at `compare_publication_impact` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
