# collect_git_repository_evidence

**Entry point:** `collect_git_repository_evidence` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as collect_git_repository_evidence
    participant p1 as Path
    participant p2 as _run_git
    participant p3 as _run_git_result
    participant p4 as items
    participant p5 as startswith
    participant p6 as run
    participant p7 as str
    participant p8 as _GitCommandResult
    participant p9 as strip
    participant p10 as RepositoryEvidence
    participant p11 as _is_full_git_oid
    participant p12 as isinstance
    participant p13 as len
    participant p14 as all
    participant p15 as _worktree_pathspecs
    participant p16 as TypeError
    participant p17 as tuple
    participant p18 as resolve
    p0-->>p1: Path
    p0->>p2: _run_git
    p2->>p3: _run_git_result
    p3-->>p4: items
    p3-->>p5: startswith
    p3-->>p6: run
    p3-->>p7: str
    p3->>p8: _GitCommandResult
    p3-->>p9: strip
    p3->>p8: _GitCommandResult
    p0->>p10: RepositoryEvidence
    p0->>p2: _run_git
    p0->>p11: _is_full_git_oid
    p11-->>p12: isinstance
    p11-->>p13: len
    p11-->>p14: all
    p0->>p15: _worktree_pathspecs
    p15-->>p12: isinstance
    p15-->>p16: TypeError
    p15-->>p12: isinstance
    p15-->>p16: TypeError
    p15-->>p12: isinstance
    p15-->>p16: TypeError
    p15-->>p17: tuple
    p15-->>p17: tuple
    p15-->>p17: tuple
    p15->>p2: _run_git
    p15-->>p18: resolve
    p15-->>p1: Path
    p15-->>p18: resolve
```

> Call sequence diagram shows 30 of 145 interactions; 115 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. collect_git_repository_evidence"]
    s2["2. Path"]
    s3["3. _run_git"]
    s4["4. _run_git_result"]
    s5["5. items"]
    s6["6. startswith"]
    s7["7. run"]
    s8["8. str"]
    s9["9. _GitCommandResult"]
    s10["10. strip"]
    s11["11. _GitCommandResult"]
    s12["12. RepositoryEvidence"]
    s1 -. "Path(root)" .-> s2
    s1 -->|"_run_git(checkout, 'rev-parse', '--is-inside-work-tree')"| s3
    s3 -->|"_run_git_result(root, ...)"| s4
    s4 -. "os.environ.items(data not statically known)" .-> s5
    s4 -. "key.startswith('GIT_')" .-> s6
    s4 -. "subprocess.run([...], capture_output=True, text=True, encoding='utf-8', errors='strict', env=git_environment, timeout=15, check=False)" .-> s7
    s4 -. "str(root)" .-> s8
    s4 -->|"_GitCommandResult(available=False, returncode=None)"| s9
    s4 -. "result.stdout.strip(data not statically known)" .-> s10
    s4 -->|"_GitCommandResult(available=True, returncode=result.returncode, output=output)"| s11
    s1 -->|"RepositoryEvidence(data not statically known)"| s12
    b0["process subprocess.run"]
    s4 -. "process subprocess.run" .-> b0
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s4 "../modules/knowledge_envelope.md"
    click s9 "../modules/knowledge_envelope.md"
    click s11 "../modules/knowledge_envelope.md"
    click s12 "../modules/knowledge_envelope.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `collect_git_repository_evidence` | `root: str \| Path`, `included_worktree_paths: Iterable[str \| Path] \| None`, `excluded_worktree_paths: Iterable[str \| Path]`, `excluded_worktree_globs: Iterable[str]`, `worktree_path_filter: Callable[[Path], bool] \| None` | `WorkingTreeState`, `WorkingTreeState`, `WorkingTreeState` | - | `RepositoryEvidence(...)`, `RepositoryEvidence(...)` |
| `Path` | - | - | - | - |
| `_run_git` | `root: Path`, `args: str`, `preserve_empty: bool` | - | - | `None`, `result.output`, `None` |
| `_run_git_result` | `root: Path`, `args: str`, `preserve_output: bool` | `os`, `subprocess` | `git_environment[...]`, `git_environment[...]`, `git_environment[...]`, `git_environment[...]` | `_GitCommandResult(...)`, `_GitCommandResult(...)` |
| `items` | - | - | - | - |
| `startswith` | - | - | - | - |
| `run` | - | - | - | - |
| `str` | - | - | - | - |
| `_GitCommandResult` | - | - | - | - |
| `strip` | - | - | - | - |
| `_GitCommandResult` | - | - | - | - |
| `RepositoryEvidence` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| collect_git_repository_evidence | Path | 307 | `Path(root)` |
| collect_git_repository_evidence | _run_git | 308 | `_run_git(checkout, 'rev-parse', '--is-inside-work-tree')` |
| _run_git | _run_git_result | 1178 | `_run_git_result(root, ...)` |
| _run_git_result | items | 1192 | `os.environ.items(data not statically known)` |
| _run_git_result | startswith | 1192 | `key.startswith('GIT_')` |
| _run_git_result | run | 1199 | `subprocess.run([...], capture_output=True, text=True, encoding='utf-8', errors='strict', env=git_environment, timeout=15, check=False)` |
| _run_git_result | str | 1200 | `str(root)` |
| _run_git_result | _GitCommandResult | 1215 | `_GitCommandResult(available=False, returncode=None)` |
| _run_git_result | strip | 1216 | `result.stdout.strip(data not statically known)` |
| _run_git_result | _GitCommandResult | 1217 | `_GitCommandResult(available=True, returncode=result.returncode, output=output)` |
| collect_git_repository_evidence | RepositoryEvidence | 310 | `RepositoryEvidence(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| process | `subprocess.run` | `_run_git_result` | 1199 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_run_git_result` | `os.environ.items` | 1192 |
| unresolved_call | `_run_git_result` | `key.startswith` | 1192 |
| unresolved_call | `_run_git_result` | `result.stdout.strip` | 1216 |
| step_limit | `collect_git_repository_evidence` | `first 12 steps` | 0 |

## Behavior

This flow starts at `collect_git_repository_evidence` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
