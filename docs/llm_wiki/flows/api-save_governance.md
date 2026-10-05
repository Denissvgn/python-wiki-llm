# save_governance

**Entry point:** `save_governance` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 4 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as save_governance
    participant p1 as validate_governance_ledger
    participant p2 as validated.to_bytes
    participant p3 as len (src/llm_wiki_cli/services…rnance.py:save_governance)
    participant p4 as GovernanceError
    participant p5 as Path (src/llm_wiki_cli/services…rnance.py:save_governance)
    participant p6 as first_unsafe_path_component
    participant p7 as _read_governance_bytes
    participant p8 as sha256_bytes
    participant p9 as is_valid_sha256
    participant p10 as GovernanceConflictError
    participant p11 as GovernanceWriteResult
    participant p12 as _write_durable_atomic
    participant p13 as isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)
    participant p14 as Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p15 as path.lstat
    participant p16 as isinstance (src/llm_wiki_cli/services…idence.py:is_valid_sha256)
    participant p17 as before_wiki_write
    participant p18 as TypeError
    participant p19 as os.fspath
    participant p20 as _SHA256_RE.fullmatch (src/llm_wiki_cli/services…idence.py:is_valid_sha256)
    participant p21 as path.parent.mkdir
    participant p22 as getattr (src/llm_wiki_cli/services…py:_read_governance_bytes)
    participant p23 as tempfile.mkstemp
    p0->>p1: validate_governance_ledger
    p0-->>p2: validated.to_bytes
    p0-->>p3: len (src/llm_wiki_cli/services…rnance.py:save_governance)(content)
    p0->>p4: GovernanceError
    p0-->>p5: Path (src/llm_wiki_cli/services…rnance.py:save_governance)(wiki_dir)
    p0->>p6: first_unsafe_path_component
    p0->>p4: GovernanceError
    p0->>p7: _read_governance_bytes
    p0->>p8: sha256_bytes
    p0->>p9: is_valid_sha256
    p0->>p4: GovernanceError
    p0->>p10: GovernanceConflictError
    p0->>p8: sha256_bytes
    p0->>p11: GovernanceWriteResult
    p0->>p12: _write_durable_atomic
    p0->>p11: GovernanceWriteResult
    p1-->>p13: isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)(ledger, GovernanceLedger)
    p6-->>p14: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))
    p7-->>p15: path.lstat
    p9-->>p16: isinstance (src/llm_wiki_cli/services…idence.py:is_valid_sha256)(value, str)
    p12->>p17: before_wiki_write
    p1-->>p18: TypeError('ledger must be a GovernanceLedger')
    p6-->>p19: os.fspath(path)
    p7->>p4: GovernanceError
    p9-->>p20: _SHA256_RE.fullmatch (src/llm_wiki_cli/services…idence.py:is_valid_sha256)(value)
    p12-->>p21: path.parent.mkdir(parents=True, exist_ok=True)
    p1->>p4: GovernanceError
    p6-->>p14: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.path.abspath(...))
    p7-->>p22: getattr (src/llm_wiki_cli/services…py:_read_governance_bytes)(metadata, 'st_file_attributes', 0)
    p12-->>p23: tempfile.mkstemp(dir=path.parent, prefix=..., suffix='.tmp')
```

> Call sequence diagram shows 30 of 414 interactions; 384 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 10 of 116 (106 omitted); unresolved 4 of 96 (92 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_ledger` | 2 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 26 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_bundle_id` | 6 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 4 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 25 | - | unresolved | 2 |
> Omission summary shows 8 of 108 groups; 100 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. save_governance"]
    s2["2. validate_governance_ledger"]
    s3["3. isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)"]
    s4["4. TypeError"]
    s5["5. GovernanceError"]
    s6["6. _bundle_id"]
    s7["7. validate_bundle_id"]
    s8["8. _machine_text"]
    s9["9. isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s10["10. ConceptIdentityError"]
    s11["11. len (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s12["12. ConceptIdentityError"]
    s1 -->|"validate_governance_ledger(ledger)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)(ledger, GovernanceLedger)" .-> s3
    s2 -. "TypeError('ledger must be a GovernanceLedger')" .-> s4
    s2 -->|"GovernanceError('schema_version', ..., code='governance-version-unsupported')"| s5
    s2 -->|"_bundle_id(ledger.bundle_id, 'bundle_id')"| s6
    s6 -->|"validate_bundle_id(value)"| s7
    s7 -->|"_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)(value, str)" .-> s9
    s8 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s10
    s8 -. "len (src/llm_wiki_cli/services…identity.py:_machine_text)(value)" .-> s11
    s8 -->|"ConceptIdentityError(field, ...)"| s12
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s5 "../modules/knowledge_governance.md"
    click s6 "../modules/knowledge_governance.md"
    click s7 "../modules/concept_identity.md"
    click s8 "../modules/concept_identity.md"
    click s10 "../modules/concept_identity.md"
    click s12 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `save_governance` | `wiki_dir: str \| Path`, `ledger: GovernanceLedger`, `expected_hash: str \| None \| object`, `fault_injector: FaultInjector \| None` | `MAX_LEDGER_BYTES`, `GOVERNANCE_FILENAME`, `MAX_LEDGER_BYTES`, `GOVERNANCE_FILENAME`, `_MISSING`, `GOVERNANCE_FILENAME` | - | `GovernanceWriteResult(...)`, `GovernanceWriteResult(...)` |
| `validate_governance_ledger` | `ledger: GovernanceLedger`, `expected_bundle_id: str \| None` | `GovernanceLedger`, `GOVERNANCE_SCHEMA_VERSION`, `GOVERNANCE_SCHEMA_VERSION`, `GovernanceAllocation`, `ConceptIdentityError`, `ALIAS_NATURAL_KEY`, `ALIAS_LOCATOR`, `ALIAS_NATURAL_KEY` | `current_keys[...]`, `alias_counts[...]`, `alias_owners[...]` | `GovernanceLedger(...)` |
| `isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `_bundle_id` | `value: object`, `path: str` | `ConceptIdentityError` | - | `validate_bundle_id(...)` |
| `validate_bundle_id` | `value: object` | `_MAX_BUNDLE_ID_LENGTH` | - | `text` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| save_governance | validate_governance_ledger | 809 | `validate_governance_ledger(ledger)` |
| validate_governance_ledger | isinstance (src/llm_wiki_cli/services…alidate_governance_ledger) | 525 | `isinstance(ledger, GovernanceLedger)` |
| validate_governance_ledger | TypeError | 526 | `TypeError('ledger must be a GovernanceLedger')` |
| validate_governance_ledger | GovernanceError | 528 | `GovernanceError('schema_version', ..., code='governance-version-unsupported')` |
| validate_governance_ledger | _bundle_id | 533 | `_bundle_id(ledger.bundle_id, 'bundle_id')` |
| _bundle_id | validate_bundle_id | 3367 | `validate_bundle_id(value)` |
| validate_bundle_id | _machine_text | 289 | `_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)` |
| _machine_text | isinstance (src/llm_wiki_cli/services…identity.py:_machine_text) | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len (src/llm_wiki_cli/services…identity.py:_machine_text) | 944 | `len(value)` |
| _machine_text | ConceptIdentityError | 945 | `ConceptIdentityError(field, ...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_governance_ledger` | `isinstance` | 525 |
| external_call | `validate_governance_ledger` | `TypeError` | 526 |
| external_call | `_machine_text` | `isinstance` | 942 |
| step_limit | `save_governance` | `first 12 steps` | 0 |
| truncated_flow | `save_governance` | `depth limit` | 0 |

## Behavior

This flow starts at `save_governance` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
