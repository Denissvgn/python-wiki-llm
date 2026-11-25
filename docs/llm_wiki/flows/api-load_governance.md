# load_governance

**Entry point:** `load_governance` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [canonical_json](../modules/canonical_json.md), [concept_identity](../modules/concept_identity.md), [host](../modules/host.md), [io](../modules/io.md), and 5 more

**Complete modules touched:**

- [canonical_json](../modules/canonical_json.md)
- [concept_identity](../modules/concept_identity.md)
- [host](../modules/host.md)
- [io](../modules/io.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_model](../modules/knowledge_model.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_governance
    participant p1 as first_unsafe_path_component
    participant p2 as _read_governance_bytes
    participant p3 as _decode_unique_json
    participant p4 as parse_governance_ledger
    participant p5 as GovernanceError
    participant p6 as GovernanceLoadResult
    participant p7 as sha256_digest
    participant p8 as _object
    participant p9 as _exact_fields
    participant p10 as _bundle_id
    participant p11 as _concept_uid
    participant p12 as _concept_kind
    participant p13 as _identity_value
    participant p14 as _parse_lifecycle_event
    participant p15 as _parse_review_event
    participant p16 as validate_governance_ledger
    participant p17 as require_mapping
    participant p18 as require_exact_fields
    participant p19 as validate_bundle_id
    participant p20 as validate_concept_uid
    participant p21 as validate_concept_kind
    participant p22 as _alias_type
    participant p23 as _event_id
    participant p24 as validate_alias_value
    participant p25 as _section_locator
    participant p26 as _hash
    participant p27 as _parse_review_evidence
    participant p28 as _parse_actor
    participant p29 as Path (src/llm_wiki_engine/knowl…rnance.py:load_governance)
    participant p30 as ledger.to_bytes
    p0->>p1: first_unsafe_path_component
    p0->>p2: _read_governance_bytes
    p0->>p3: _decode_unique_json
    p0->>p4: parse_governance_ledger
    p0->>p5: GovernanceError
    p0->>p6: GovernanceLoadResult
    p0->>p7: sha256_digest
    p4->>p8: _object
    p4->>p9: _exact_fields
    p4->>p10: _bundle_id
    p4->>p11: _concept_uid
    p4->>p12: _concept_kind
    p4->>p13: _identity_value
    p4->>p14: _parse_lifecycle_event
    p4->>p15: _parse_review_event
    p4->>p16: validate_governance_ledger
    p8->>p17: require_mapping
    p9->>p18: require_exact_fields
    p10->>p19: validate_bundle_id
    p11->>p20: validate_concept_uid
    p12->>p21: validate_concept_kind
    p13->>p22: _alias_type
    p14->>p23: _event_id
    p13->>p24: validate_alias_value
    p15->>p25: _section_locator
    p15->>p26: _hash
    p15->>p27: _parse_review_evidence
    p14->>p28: _parse_actor
    p0-->>p29: Path (src/llm_wiki_engine/knowl…rnance.py:load_governance)(wiki_dir)
    p0-->>p30: ledger.to_bytes
```

> Call sequence diagram shows 30 of 515 interactions; 485 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 126 (125 omitted); unresolved 1 of 110 (109 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_engine/io.py:first_unsafe_path_component` | 3 | - | external | 19 |
| `src/llm_wiki_engine/io.py:first_unsafe_path_component` | 3 | - | unresolved | 6 |
| `src/llm_wiki_engine/io.py:first_unsafe_path_component` | 3 | [src/llm_wiki_engine/host.py](../modules/host.md) | internal | 1 |
| `src/llm_wiki_engine/host.py:current_host` | 10 | - | unresolved | 1 |
| `src/llm_wiki_engine/knowledge_governance.py:_read_governance_bytes` | 32 | - | unresolved | 3 |
| `src/llm_wiki_engine/knowledge_governance.py:_read_governance_bytes` | 32 | [src/llm_wiki_engine/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 7 |
| `src/llm_wiki_engine/knowledge_governance.py:_read_governance_bytes` | 32 | - | external | 16 |
| `src/llm_wiki_engine/knowledge_governance.py:_decode_unique_json` | 59 | - | external | 1 |
> Omission summary shows 8 of 133 groups; 125 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 280; effect analysis evaluated: 152, partial: 3, unavailable: 125. Counts include steps omitted from the displayed trace.

Collector observations for 155 source steps with known totals: observed: 712, emitted: 697, omitted: 15. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `load_governance` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `Path (src/llm_wiki_engine/knowl…rnance.py:load_governance)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `first_unsafe_path_component` | `available` | `evaluated` | `available` | `14` | `14` | `0` |
| `Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `os.fspath` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `os.path.abspath` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `lexical.is_absolute` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `current_host().cwd` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `current_host` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_ACTIVE.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. load_governance"]
    s2["2. Path (src/llm_wiki_engine/knowl…rnance.py:load_governance)"]
    s3["3. first_unsafe_path_component"]
    s4["4. Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)"]
    s5["5. os.fspath"]
    s6["6. Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)"]
    s7["7. os.path.abspath"]
    s8["8. lexical.is_absolute"]
    s9["9. current_host().cwd"]
    s10["10. current_host"]
    s11["11. _ACTIVE.get"]
    s12["12. Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)"]
    s1 -. "Path (src/llm_wiki_engine/knowl…rnance.py:load_governance)(wiki_dir)" .-> s2
    s1 -->|"first_unsafe_path_component(root)"| s3
    s3 -. "Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)(os.fspath(...))" .-> s4
    s3 -. "os.fspath(path)" .-> s5
    s3 -. "Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)(os.path.abspath(...))" .-> s6
    s3 -. "os.path.abspath(lexical)" .-> s7
    s3 -. "lexical.is_absolute(data not statically known)" .-> s8
    s3 -. "current_host().cwd(data not statically known)" .-> s9
    s3 -->|"current_host(data not statically known)"| s10
    s10 -. "_ACTIVE.get(data not statically known)" .-> s11
    s3 -. "Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)(absolute.anchor)" .-> s12
    b0["mutation pending_parts.pop"]
    s3 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/knowledge_governance.md"
    click s3 "../modules/io.md"
    click s10 "../modules/host.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `load_governance` | `wiki_dir: str \| Path`, `expected_bundle_id: str \| None` | `GOVERNANCE_FILENAME`, `GOVERNANCE_FILENAME` | - | `GovernanceLoadResult(...)` |
| `Path (src/llm_wiki_engine/knowl…rnance.py:load_governance)` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)` | - | - | - | - |
| `os.path.abspath` | - | - | - | - |
| `lexical.is_absolute` | - | - | - | - |
| `current_host().cwd` | - | - | - | - |
| `current_host` | - | `_DEFAULT` | - | `...` |
| `_ACTIVE.get` | - | - | - | - |
| `Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_governance | Path (src/llm_wiki_engine/knowl…rnance.py:load_governance) | 779 | `Path(wiki_dir)` |
| load_governance | first_unsafe_path_component | 780 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component) | 52 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath | 52 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component) | 60 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath | 60 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 61 | `lexical.is_absolute(data not statically known)` |
| first_unsafe_path_component | current_host().cwd | 67 | `current_host().cwd(data not statically known)` |
| first_unsafe_path_component | current_host | 67 | `current_host(data not statically known)` |
| current_host | _ACTIVE.get | 167 | `_ACTIVE.get(data not statically known)` |
| first_unsafe_path_component | Path (src/llm_wiki_engine/io.py…rst_unsafe_path_component) | 68 | `Path(absolute.anchor)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 72 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `first_unsafe_path_component` | `os.fspath` | 52 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 60 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 61 |
| unresolved_call | `first_unsafe_path_component` | `current_host().cwd` | 67 |
| unresolved_call | `current_host` | `_ACTIVE.get` | 167 |
| step_limit | `load_governance` | `first 12 steps` | 0 |
| truncated_flow | `load_governance` | `depth limit` | 0 |

## Behavior

This flow starts at `load_governance` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
