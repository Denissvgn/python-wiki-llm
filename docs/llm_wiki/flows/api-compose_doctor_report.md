# compose_doctor_report

**Entry point:** `compose_doctor_report` (`api`)
**Source:** [doctor_service](../modules/doctor_service.md)
**Modules touched:** [doctor_service](../modules/doctor_service.md), [knowledge_observability](../modules/knowledge_observability.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compose_doctor_report
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as Path
    participant p4 as _availability_section
    participant p5 as _knowledge_declared
    participant p6 as exists
    participant p7 as is_symlink
    participant p8 as load
    participant p9 as _freshness_section
    participant p10 as int
    participant p11 as knowledge_freshness_disclosure
    participant p12 as _freshness_disclosure
    participant p13 as sum
    participant p14 as values
    participant p15 as _snapshot_section
    participant p16 as sorted
    participant p17 as len
    participant p18 as _governance_section
    participant p19 as _issues
    participant p20 as _reasons
    participant p21 as set
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p3: Path
    p0->>p4: _availability_section
    p4->>p5: _knowledge_declared
    p5-->>p6: exists
    p5-->>p7: is_symlink
    p5-->>p8: load
    p4->>p5: _knowledge_declared
    p0->>p9: _freshness_section
    p9-->>p10: int
    p9-->>p10: int
    p9->>p11: knowledge_freshness_disclosure
    p11-->>p1: isinstance
    p11-->>p2: TypeError
    p11->>p12: _freshness_disclosure
    p11-->>p13: sum
    p11-->>p10: int
    p11-->>p14: values
    p9-->>p13: sum
    p9-->>p14: values
    p0->>p15: _snapshot_section
    p15-->>p16: sorted
    p15-->>p17: len
    p0->>p18: _governance_section
    p18->>p19: _issues
    p18->>p20: _reasons
    p20-->>p21: set
```

> Call sequence diagram shows 30 of 84 interactions; 54 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. compose_doctor_report"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. isinstance"]
    s5["5. TypeError"]
    s6["6. Path"]
    s7["7. _availability_section"]
    s8["8. _knowledge_declared"]
    s9["9. exists"]
    s10["10. is_symlink"]
    s11["11. load"]
    s12["12. _knowledge_declared"]
    s1 -. "isinstance(lint, LintReport)" .-> s2
    s1 -. "TypeError('lint must be a LintReport')" .-> s3
    s1 -. "isinstance(strict, bool)" .-> s4
    s1 -. "TypeError('strict must be a boolean')" .-> s5
    s1 -. "Path(wiki_dir)" .-> s6
    s1 -->|"_availability_section(lint, view, wiki_root)"| s7
    s7 -->|"_knowledge_declared(wiki_root)"| s8
    s8 -. "path.exists(data not statically known)" .-> s9
    s8 -. "path.is_symlink(data not statically known)" .-> s10
    s8 -. "SyncManifest.load(wiki_root)" .-> s11
    s7 -->|"_knowledge_declared(wiki_root)"| s12
    click s1 "../modules/doctor_service.md"
    click s7 "../modules/doctor_service.md"
    click s8 "../modules/doctor_service.md"
    click s12 "../modules/doctor_service.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compose_doctor_report` | `lint: LintReport`, `strict: bool`, `wiki_dir: str`, `src_dir: str` | `LintReport` | - | `DoctorReport(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `Path` | - | - | - | - |
| `_availability_section` | `lint: LintReport`, `view: KnowledgeReadView \| None`, `wiki_root: Path` | `KnowledgeAvailability`, `KnowledgeAvailability`, `KnowledgeAvailability`, `KnowledgeAvailability`, `KnowledgeAvailability` | - | `{...}`, `{...}`, `{...}`, `{...}` |
| `_knowledge_declared` | `wiki_root: Path` | `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `GOVERNANCE_FILENAME`, `VERIFICATION_RECEIPT_FILENAME` | - | `True`, `False`, `...` |
| `exists` | - | - | - | - |
| `is_symlink` | - | - | - | - |
| `load` | - | - | - | - |
| `_knowledge_declared` | `wiki_root: Path` | `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `GOVERNANCE_FILENAME`, `VERIFICATION_RECEIPT_FILENAME` | - | `True`, `False`, `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compose_doctor_report | isinstance | 175 | `isinstance(lint, LintReport)` |
| compose_doctor_report | TypeError | 176 | `TypeError('lint must be a LintReport')` |
| compose_doctor_report | isinstance | 177 | `isinstance(strict, bool)` |
| compose_doctor_report | TypeError | 178 | `TypeError('strict must be a boolean')` |
| compose_doctor_report | Path | 181 | `Path(wiki_dir)` |
| compose_doctor_report | _availability_section | 182 | `_availability_section(lint, view, wiki_root)` |
| _availability_section | _knowledge_declared | 286 | `_knowledge_declared(wiki_root)` |
| _knowledge_declared | exists | 320 | `path.exists(data not statically known)` |
| _knowledge_declared | is_symlink | 320 | `path.is_symlink(data not statically known)` |
| _knowledge_declared | load | 323 | `SyncManifest.load(wiki_root)` |
| _availability_section | _knowledge_declared | 299 | `_knowledge_declared(wiki_root)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `compose_doctor_report` | `isinstance` | 175 |
| unresolved_call | `compose_doctor_report` | `TypeError` | 176 |
| unresolved_call | `compose_doctor_report` | `isinstance` | 177 |
| unresolved_call | `compose_doctor_report` | `TypeError` | 178 |
| unresolved_call | `_knowledge_declared` | `path.exists` | 320 |
| unresolved_call | `_knowledge_declared` | `path.is_symlink` | 320 |
| external_call | `_knowledge_declared` | `SyncManifest.load` | 323 |
| step_limit | `compose_doctor_report` | `first 12 steps` | 0 |

## Behavior

This flow starts at `compose_doctor_report` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
