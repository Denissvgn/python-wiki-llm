# commit_knowledge_artifacts

**Entry point:** `commit_knowledge_artifacts` (`api`)
**Source:** [knowledge_artifacts](../modules/knowledge_artifacts.md)
**Modules touched:** [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as commit_knowledge_artifacts
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as callable
    participant p4 as _apply_write
    participant p5 as write_bytes_atomic
    participant p6 as Path
    participant p7 as mkdir
    participant p8 as mkstemp
    participant p9 as fdopen
    participant p10 as write
    participant p11 as replace
    participant p12 as unlink
    participant p13 as fault_injector
    participant p14 as _verify_persisted
    participant p15 as read_bytes
    participant p16 as KnowledgeArtifactError
    participant p17 as sha256_bytes
    participant p18 as hexdigest
    participant p19 as sha256
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p3: callable
    p0-->>p2: TypeError
    p0->>p4: _apply_write
    p4->>p5: write_bytes_atomic
    p5-->>p1: isinstance
    p5-->>p2: TypeError
    p5-->>p6: Path
    p5-->>p7: mkdir
    p5-->>p8: mkstemp
    p5-->>p9: fdopen
    p5-->>p10: write
    p5-->>p11: replace
    p5-->>p12: unlink
    p4-->>p13: fault_injector
    p0->>p4: _apply_write
    p0->>p14: _verify_persisted
    p14-->>p15: read_bytes
    p14->>p16: KnowledgeArtifactError
    p14->>p17: sha256_bytes
    p17-->>p18: hexdigest
    p17-->>p19: sha256
    p14->>p16: KnowledgeArtifactError
    p0->>p14: _verify_persisted
    p0->>p4: _apply_write
    p0->>p14: _verify_persisted
    p0->>p14: _verify_persisted
```

> Call sequence diagram shows 30 of 32 interactions; 2 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. commit_knowledge_artifacts"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. isinstance"]
    s5["5. TypeError"]
    s6["6. callable"]
    s7["7. TypeError"]
    s8["8. _apply_write"]
    s9["9. write_bytes_atomic"]
    s10["10. isinstance"]
    s11["11. TypeError"]
    s12["12. Path"]
    s1 -. "isinstance(plan, KnowledgeCommitPlan)" .-> s2
    s1 -. "TypeError('plan must be a KnowledgeCommitPlan')" .-> s3
    s1 -. "isinstance(dry_run, bool)" .-> s4
    s1 -. "TypeError('dry_run must be a bool')" .-> s5
    s1 -. "callable(fault_injector)" .-> s6
    s1 -. "TypeError('fault_injector must be callable')" .-> s7
    s1 -->|"_apply_write(plan.surface_index, CommitStage.SURFACE_INDEX_WRITTEN, fault_injector)"| s8
    s8 -->|"write_bytes_atomic(artifact.path, artifact.content)"| s9
    s9 -. "isinstance(content, bytes)" .-> s10
    s9 -. "TypeError('content must be bytes')" .-> s11
    s9 -. "Path(path)" .-> s12
    b0["filesystem_write os.unlink"]
    s9 -. "filesystem_write os.unlink" .-> b0
    click s1 "../modules/knowledge_artifacts.md"
    click s8 "../modules/knowledge_artifacts.md"
    click s9 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `commit_knowledge_artifacts` | `plan: KnowledgeCommitPlan`, `dry_run: bool`, `fault_injector: FaultInjector \| None` | `KnowledgeCommitPlan`, `CommitStage`, `CommitStage`, `CommitStage` | - | `KnowledgeCommitResult(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `callable` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_apply_write` | `artifact: PlannedArtifactWrite`, `stage: CommitStage`, `fault_injector: FaultInjector \| None` | - | - | `none` |
| `write_bytes_atomic` | `path: str \| Path`, `content: bytes` | - | - | `target` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `Path` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| commit_knowledge_artifacts | isinstance | 405 | `isinstance(plan, KnowledgeCommitPlan)` |
| commit_knowledge_artifacts | TypeError | 406 | `TypeError('plan must be a KnowledgeCommitPlan')` |
| commit_knowledge_artifacts | isinstance | 407 | `isinstance(dry_run, bool)` |
| commit_knowledge_artifacts | TypeError | 408 | `TypeError('dry_run must be a bool')` |
| commit_knowledge_artifacts | callable | 409 | `callable(fault_injector)` |
| commit_knowledge_artifacts | TypeError | 410 | `TypeError('fault_injector must be callable')` |
| commit_knowledge_artifacts | _apply_write | 413 | `_apply_write(plan.surface_index, CommitStage.SURFACE_INDEX_WRITTEN, fault_injector)` |
| _apply_write | write_bytes_atomic | 478 | `write_bytes_atomic(artifact.path, artifact.content)` |
| write_bytes_atomic | isinstance | 164 | `isinstance(content, bytes)` |
| write_bytes_atomic | TypeError | 165 | `TypeError('content must be bytes')` |
| write_bytes_atomic | Path | 166 | `Path(path)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `os.unlink` | `write_bytes_atomic` | 179 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `commit_knowledge_artifacts` | `isinstance` | 405 |
| unresolved_call | `commit_knowledge_artifacts` | `TypeError` | 406 |
| unresolved_call | `commit_knowledge_artifacts` | `isinstance` | 407 |
| unresolved_call | `commit_knowledge_artifacts` | `TypeError` | 408 |
| unresolved_call | `commit_knowledge_artifacts` | `callable` | 409 |
| unresolved_call | `commit_knowledge_artifacts` | `TypeError` | 410 |
| unresolved_call | `write_bytes_atomic` | `isinstance` | 164 |
| unresolved_call | `write_bytes_atomic` | `TypeError` | 165 |
| step_limit | `commit_knowledge_artifacts` | `first 12 steps` | 0 |

## Behavior

This flow starts at `commit_knowledge_artifacts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
