# commit_knowledge_artifacts

**Entry point:** `commit_knowledge_artifacts` (`api`)
**Source:** [knowledge_artifacts](../modules/knowledge_artifacts.md)
**Modules touched:** [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as commit_knowledge_artifacts
    participant p1 as isinstance (src/llm_wiki_cli/services…commit_knowledge_artifacts)
    participant p2 as TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)
    participant p3 as callable
    participant p4 as _apply_write
    participant p5 as write_bytes_atomic
    participant p6 as isinstance (src/llm_wiki_cli/services/io.py:write_bytes_atomic)
    participant p7 as TypeError (src/llm_wiki_cli/services/io.py:write_bytes_atomic)
    participant p8 as Path
    participant p9 as target.parent.mkdir
    participant p10 as tempfile.mkstemp
    participant p11 as os.fdopen
    participant p12 as f.write
    participant p13 as os.replace
    participant p14 as os.unlink
    participant p15 as fault_injector
    participant p16 as _verify_persisted
    participant p17 as artifact.path.read_bytes
    participant p18 as KnowledgeArtifactError
    participant p19 as sha256_bytes
    participant p20 as hashlib.sha256(…).hexdigest
    participant p21 as hashlib.sha256
    p0-->>p1: isinstance (src/llm_wiki_cli/services…commit_knowledge_artifacts)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…commit_knowledge_artifacts)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)
    p0-->>p3: callable
    p0-->>p2: TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)
    p0->>p4: _apply_write
    p4->>p5: write_bytes_atomic
    p5-->>p6: isinstance (src/llm_wiki_cli/services/io.py:write_bytes_atomic)
    p5-->>p7: TypeError (src/llm_wiki_cli/services/io.py:write_bytes_atomic)
    p5-->>p8: Path
    p5-->>p9: target.parent.mkdir
    p5-->>p10: tempfile.mkstemp
    p5-->>p11: os.fdopen
    p5-->>p12: f.write
    p5-->>p13: os.replace
    p5-->>p14: os.unlink
    p4-->>p15: fault_injector
    p0->>p4: _apply_write
    p0->>p16: _verify_persisted
    p16-->>p17: artifact.path.read_bytes
    p16->>p18: KnowledgeArtifactError
    p16->>p19: sha256_bytes
    p19-->>p20: hashlib.sha256(…).hexdigest
    p19-->>p21: hashlib.sha256
    p16->>p18: KnowledgeArtifactError
    p0->>p16: _verify_persisted
    p0->>p4: _apply_write
    p0->>p16: _verify_persisted
    p0->>p16: _verify_persisted
```

> Call sequence diagram shows 30 of 32 interactions; 2 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. commit_knowledge_artifacts"]
    s2["2. isinstance (src/llm_wiki_cli/services…commit_knowledge_artifacts)"]
    s3["3. TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)"]
    s4["4. isinstance (src/llm_wiki_cli/services…commit_knowledge_artifacts)"]
    s5["5. TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)"]
    s6["6. callable"]
    s7["7. TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)"]
    s8["8. _apply_write"]
    s9["9. write_bytes_atomic"]
    s10["10. isinstance (src/llm_wiki_cli/services/io.py:write_bytes_atomic)"]
    s11["11. TypeError (src/llm_wiki_cli/services/io.py:write_bytes_atomic)"]
    s12["12. Path"]
    s1 -. "isinstance (src/llm_wiki_cli/services…commit_knowledge_artifacts)(plan, KnowledgeCommitPlan)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)('plan must be a KnowledgeCommitPlan')" .-> s3
    s1 -. "isinstance (src/llm_wiki_cli/services…commit_knowledge_artifacts)(dry_run, bool)" .-> s4
    s1 -. "TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)('dry_run must be a bool')" .-> s5
    s1 -. "callable(fault_injector)" .-> s6
    s1 -. "TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)('fault_injector must be callable')" .-> s7
    s1 -->|"_apply_write(plan.surface_index, CommitStage.SURFACE_INDEX_WRITTEN, fault_injector)"| s8
    s8 -->|"write_bytes_atomic(artifact.path, artifact.content)"| s9
    s9 -. "isinstance (src/llm_wiki_cli/services/io.py:write_bytes_atomic)(content, bytes)" .-> s10
    s9 -. "TypeError (src/llm_wiki_cli/services/io.py:write_bytes_atomic)('content must be bytes')" .-> s11
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
| `isinstance (src/llm_wiki_cli/services…commit_knowledge_artifacts)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…commit_knowledge_artifacts)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)` | - | - | - | - |
| `callable` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts)` | - | - | - | - |
| `_apply_write` | `artifact: PlannedArtifactWrite`, `stage: CommitStage`, `fault_injector: FaultInjector \| None` | - | - | `none` |
| `write_bytes_atomic` | `path: str \| Path`, `content: bytes` | - | - | `target` |
| `isinstance (src/llm_wiki_cli/services/io.py:write_bytes_atomic)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services/io.py:write_bytes_atomic)` | - | - | - | - |
| `Path` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| commit_knowledge_artifacts | isinstance (src/llm_wiki_cli/services…commit_knowledge_artifacts) | 477 | `isinstance(plan, KnowledgeCommitPlan)` |
| commit_knowledge_artifacts | TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts) | 478 | `TypeError('plan must be a KnowledgeCommitPlan')` |
| commit_knowledge_artifacts | isinstance (src/llm_wiki_cli/services…commit_knowledge_artifacts) | 479 | `isinstance(dry_run, bool)` |
| commit_knowledge_artifacts | TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts) | 480 | `TypeError('dry_run must be a bool')` |
| commit_knowledge_artifacts | callable | 481 | `callable(fault_injector)` |
| commit_knowledge_artifacts | TypeError (src/llm_wiki_cli/services…commit_knowledge_artifacts) | 482 | `TypeError('fault_injector must be callable')` |
| commit_knowledge_artifacts | _apply_write | 485 | `_apply_write(plan.surface_index, CommitStage.SURFACE_INDEX_WRITTEN, fault_injector)` |
| _apply_write | write_bytes_atomic | 550 | `write_bytes_atomic(artifact.path, artifact.content)` |
| write_bytes_atomic | isinstance (src/llm_wiki_cli/services/io.py:write_bytes_atomic) | 164 | `isinstance(content, bytes)` |
| write_bytes_atomic | TypeError (src/llm_wiki_cli/services/io.py:write_bytes_atomic) | 165 | `TypeError('content must be bytes')` |
| write_bytes_atomic | Path | 166 | `Path(path)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `os.unlink` | `write_bytes_atomic` | 179 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `commit_knowledge_artifacts` | `isinstance` | 477 |
| external_call | `commit_knowledge_artifacts` | `TypeError` | 478 |
| external_call | `commit_knowledge_artifacts` | `isinstance` | 479 |
| external_call | `commit_knowledge_artifacts` | `TypeError` | 480 |
| external_call | `commit_knowledge_artifacts` | `callable` | 481 |
| external_call | `commit_knowledge_artifacts` | `TypeError` | 482 |
| external_call | `write_bytes_atomic` | `isinstance` | 164 |
| external_call | `write_bytes_atomic` | `TypeError` | 165 |
| step_limit | `commit_knowledge_artifacts` | `first 12 steps` | 0 |

## Behavior

This flow starts at `commit_knowledge_artifacts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
