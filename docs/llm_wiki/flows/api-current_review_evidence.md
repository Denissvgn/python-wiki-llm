# current_review_evidence

**Entry point:** `current_review_evidence` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [knowledge_governance](../modules/knowledge_governance.md), [validation](../modules/validation.md), [wiki_media](../modules/wiki_media.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as current_review_evidence
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as ReviewEvidence
    participant p4 as _review_evidence
    participant p5 as GovernanceError
    participant p6 as tuple
    participant p7 as sorted
    participant p8 as _safe_name
    participant p9 as strip
    participant p10 as len
    participant p11 as search
    participant p12 as _safe_text
    participant p13 as require_no_control_characters
    participant p14 as contains_control_character
    participant p15 as any
    participant p16 as ord
    participant p17 as contains_uri_authority_userinfo
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: ReviewEvidence
    p0->>p3: ReviewEvidence
    p0->>p4: _review_evidence
    p4-->>p1: isinstance
    p4->>p5: GovernanceError
    p4->>p5: GovernanceError
    p4->>p5: GovernanceError
    p4->>p3: ReviewEvidence
    p4->>p5: GovernanceError
    p4-->>p6: tuple
    p4-->>p7: sorted
    p4->>p8: _safe_name
    p8-->>p1: isinstance
    p8-->>p9: strip
    p8-->>p10: len
    p8-->>p11: search
    p8->>p5: GovernanceError
    p8->>p12: _safe_text
    p12->>p13: require_no_control_characters
    p13-->>p1: isinstance
    p13->>p14: contains_control_character
    p14-->>p15: any
    p14-->>p16: ord
    p14-->>p16: ord
    p12->>p5: GovernanceError
    p12-->>p11: search
    p12->>p5: GovernanceError
    p12->>p17: contains_uri_authority_userinfo
```

> Call sequence diagram shows 30 of 71 interactions; 41 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. current_review_evidence"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. ReviewEvidence"]
    s5["5. ReviewEvidence"]
    s6["6. _review_evidence"]
    s7["7. isinstance"]
    s8["8. GovernanceError"]
    s9["9. GovernanceError"]
    s10["10. GovernanceError"]
    s11["11. ReviewEvidence"]
    s12["12. GovernanceError"]
    s1 -. "isinstance(concept, ConceptRecord)" .-> s2
    s1 -. "TypeError('concept must be a ConceptRecord')" .-> s3
    s1 -->|"ReviewEvidence(mode='no-source')"| s4
    s1 -->|"ReviewEvidence(mode='no-source')"| s5
    s1 -->|"_review_evidence(ReviewEvidence(...), 'evidence')"| s6
    s6 -. "isinstance(value, ReviewEvidence)" .-> s7
    s6 -->|"GovernanceError(path, 'must be ReviewEvidence')"| s8
    s6 -->|"GovernanceError(..., #34;must be 'source' or 'no-source'#34;)"| s9
    s6 -->|"GovernanceError(path, 'no-source evidence cannot carry basis IDs or hashes')"| s10
    s6 -->|"ReviewEvidence(mode='no-source')"| s11
    s6 -->|"GovernanceError(path, 'source evidence requires basis IDs and hashes')"| s12
    click s1 "../modules/knowledge_governance.md"
    click s4 "../modules/knowledge_governance.md"
    click s5 "../modules/knowledge_governance.md"
    click s6 "../modules/knowledge_governance.md"
    click s8 "../modules/knowledge_governance.md"
    click s9 "../modules/knowledge_governance.md"
    click s10 "../modules/knowledge_governance.md"
    click s11 "../modules/knowledge_governance.md"
    click s12 "../modules/knowledge_governance.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `current_review_evidence` | `concept: ConceptRecord` | `ConceptRecord`, `EvidenceState`, `EvidenceState`, `EvidenceState` | - | `ReviewEvidence(...)`, `ReviewEvidence(...)`, `None`, `None`, `_review_evidence(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `ReviewEvidence` | - | - | - | - |
| `ReviewEvidence` | - | - | - | - |
| `_review_evidence` | `value: ReviewEvidence`, `path: str` | `ReviewEvidence`, `REVIEW_EVIDENCE_MODES` | - | `ReviewEvidence(...)`, `ReviewEvidence(...)` |
| `isinstance` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `ReviewEvidence` | - | - | - | - |
| `GovernanceError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| current_review_evidence | isinstance | 1492 | `isinstance(concept, ConceptRecord)` |
| current_review_evidence | TypeError | 1493 | `TypeError('concept must be a ConceptRecord')` |
| current_review_evidence | ReviewEvidence | 1497 | `ReviewEvidence(mode='no-source')` |
| current_review_evidence | ReviewEvidence | 1501 | `ReviewEvidence(mode='no-source')` |
| current_review_evidence | _review_evidence | 1520 | `_review_evidence(ReviewEvidence(...), 'evidence')` |
| _review_evidence | isinstance | 2889 | `isinstance(value, ReviewEvidence)` |
| _review_evidence | GovernanceError | 2890 | `GovernanceError(path, 'must be ReviewEvidence')` |
| _review_evidence | GovernanceError | 2892 | `GovernanceError(..., "must be 'source' or 'no-source'")` |
| _review_evidence | GovernanceError | 2898 | `GovernanceError(path, 'no-source evidence cannot carry basis IDs or hashes')` |
| _review_evidence | ReviewEvidence | 2902 | `ReviewEvidence(mode='no-source')` |
| _review_evidence | GovernanceError | 2904 | `GovernanceError(path, 'source evidence requires basis IDs and hashes')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `current_review_evidence` | `isinstance` | 1492 |
| unresolved_call | `current_review_evidence` | `TypeError` | 1493 |
| unresolved_call | `_review_evidence` | `isinstance` | 2889 |
| step_limit | `current_review_evidence` | `first 12 steps` | 0 |

## Behavior

This flow starts at `current_review_evidence` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
