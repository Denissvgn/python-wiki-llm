# current_review_evidence

**Entry point:** `current_review_evidence` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [knowledge_governance](../modules/knowledge_governance.md), [validation](../modules/validation.md), [wiki_media](../modules/wiki_media.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as current_review_evidence
    participant p1 as isinstance (src/llm_wiki_cli/services…py:current_review_evidence)
    participant p2 as TypeError
    participant p3 as ReviewEvidence
    participant p4 as _review_evidence
    participant p5 as isinstance (src/llm_wiki_cli/services…rnance.py:_review_evidence)
    participant p6 as GovernanceError
    participant p7 as tuple
    participant p8 as sorted
    participant p9 as _safe_name
    participant p10 as isinstance (src/llm_wiki_cli/services…e_governance.py:_safe_name)
    participant p11 as value.strip (src/llm_wiki_cli/services…e_governance.py:_safe_name)
    participant p12 as len (src/llm_wiki_cli/services…e_governance.py:_safe_name)
    participant p13 as _CONTROL_RE.search
    participant p14 as _safe_text
    participant p15 as require_no_control_characters
    participant p16 as isinstance (src/llm_wiki_cli/services…uire_no_control_characters)
    participant p17 as contains_control_character
    participant p18 as any (src/llm_wiki_cli/services…contains_control_character)
    participant p19 as ord (src/llm_wiki_cli/services…contains_control_character)
    participant p20 as _SENSITIVE_RE.search
    participant p21 as contains_uri_authority_userinfo
    p0-->>p1: isinstance (src/llm_wiki_cli/services…py:current_review_evidence)
    p0-->>p2: TypeError
    p0->>p3: ReviewEvidence
    p0->>p3: ReviewEvidence
    p0->>p4: _review_evidence
    p4-->>p5: isinstance (src/llm_wiki_cli/services…rnance.py:_review_evidence)
    p4->>p6: GovernanceError
    p4->>p6: GovernanceError
    p4->>p6: GovernanceError
    p4->>p3: ReviewEvidence
    p4->>p6: GovernanceError
    p4-->>p7: tuple
    p4-->>p8: sorted
    p4->>p9: _safe_name
    p9-->>p10: isinstance (src/llm_wiki_cli/services…e_governance.py:_safe_name)
    p9-->>p11: value.strip (src/llm_wiki_cli/services…e_governance.py:_safe_name)
    p9-->>p12: len (src/llm_wiki_cli/services…e_governance.py:_safe_name)
    p9-->>p13: _CONTROL_RE.search
    p9->>p6: GovernanceError
    p9->>p14: _safe_text
    p14->>p15: require_no_control_characters
    p15-->>p16: isinstance (src/llm_wiki_cli/services…uire_no_control_characters)
    p15->>p17: contains_control_character
    p17-->>p18: any (src/llm_wiki_cli/services…contains_control_character)
    p17-->>p19: ord (src/llm_wiki_cli/services…contains_control_character)
    p17-->>p19: ord (src/llm_wiki_cli/services…contains_control_character)
    p14->>p6: GovernanceError
    p14-->>p20: _SENSITIVE_RE.search
    p14->>p6: GovernanceError
    p14->>p21: contains_uri_authority_userinfo
```

> Call sequence diagram shows 30 of 71 interactions; 41 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. current_review_evidence"]
    s2["2. isinstance (src/llm_wiki_cli/services…py:current_review_evidence)"]
    s3["3. TypeError"]
    s4["4. ReviewEvidence"]
    s5["5. ReviewEvidence"]
    s6["6. _review_evidence"]
    s7["7. isinstance (src/llm_wiki_cli/services…rnance.py:_review_evidence)"]
    s8["8. GovernanceError"]
    s9["9. GovernanceError"]
    s10["10. GovernanceError"]
    s11["11. ReviewEvidence"]
    s12["12. GovernanceError"]
    s1 -. "isinstance (src/llm_wiki_cli/services…py:current_review_evidence)(concept, ConceptRecord)" .-> s2
    s1 -. "TypeError('concept must be a ConceptRecord')" .-> s3
    s1 -->|"ReviewEvidence(mode='no-source')"| s4
    s1 -->|"ReviewEvidence(mode='no-source')"| s5
    s1 -->|"_review_evidence(ReviewEvidence(...), 'evidence')"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…rnance.py:_review_evidence)(value, ReviewEvidence)" .-> s7
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
| `isinstance (src/llm_wiki_cli/services…py:current_review_evidence)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `ReviewEvidence` | - | - | - | - |
| `ReviewEvidence` | - | - | - | - |
| `_review_evidence` | `value: ReviewEvidence`, `path: str` | `ReviewEvidence`, `REVIEW_EVIDENCE_MODES` | - | `ReviewEvidence(...)`, `ReviewEvidence(...)` |
| `isinstance (src/llm_wiki_cli/services…rnance.py:_review_evidence)` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `ReviewEvidence` | - | - | - | - |
| `GovernanceError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| current_review_evidence | isinstance (src/llm_wiki_cli/services…py:current_review_evidence) | 1492 | `isinstance(concept, ConceptRecord)` |
| current_review_evidence | TypeError | 1493 | `TypeError('concept must be a ConceptRecord')` |
| current_review_evidence | ReviewEvidence | 1497 | `ReviewEvidence(mode='no-source')` |
| current_review_evidence | ReviewEvidence | 1501 | `ReviewEvidence(mode='no-source')` |
| current_review_evidence | _review_evidence | 1520 | `_review_evidence(ReviewEvidence(...), 'evidence')` |
| _review_evidence | isinstance (src/llm_wiki_cli/services…rnance.py:_review_evidence) | 2889 | `isinstance(value, ReviewEvidence)` |
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
| external_call | `current_review_evidence` | `isinstance` | 1492 |
| external_call | `current_review_evidence` | `TypeError` | 1493 |
| external_call | `_review_evidence` | `isinstance` | 2889 |
| step_limit | `current_review_evidence` | `first 12 steps` | 0 |

## Behavior

This flow starts at `current_review_evidence` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
