# trigger-agent

**Entry point:** `run` (`cli`)
**Source:** [trigger_cmd](../modules/trigger_cmd.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [documentation_query_builder](../modules/documentation_query_builder.md), [extraction_jobs](../modules/extraction_jobs.md), and 20 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [generate_prompt_cmd](../modules/generate_prompt_cmd.md)
- [imports](../modules/imports.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [lockfile](../modules/lockfile.md)
- [metrics](../modules/metrics.md)
- [packages](../modules/packages.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [redaction](../modules/redaction.md)
- [secure_file](../modules/secure_file.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [team](../modules/team.md)
- [trigger_cmd](../modules/trigger_cmd.md)
- [validation](../modules/validation.md)
- [wiki_git_policy](../modules/wiki_git_policy.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as reset_breaker
    participant p3 as print
    participant p4 as exit
    participant p5 as WikiLock
    participant p6 as _lock_wait_seconds
    participant p7 as get
    participant p8 as strip
    participant p9 as float
    participant p10 as ValueError
    participant p11 as isfinite
    participant p12 as _run_sync
    participant p13 as validate_path
    participant p14 as PathValidationError
    participant p15 as resolve
    participant p16 as cwd
    participant p17 as relative_to
    participant p18 as _validated_trigger_source
    participant p19 as str
    participant p20 as bool
    p0-->>p1: getattr
    p0-->>p2: reset_breaker
    p0-->>p3: print
    p0-->>p3: print
    p0-->>p3: print
    p0-->>p3: print
    p0-->>p4: exit
    p0->>p5: WikiLock
    p0->>p6: _lock_wait_seconds
    p6-->>p7: get
    p6-->>p8: strip
    p6-->>p9: float
    p6-->>p10: ValueError
    p6-->>p11: isfinite
    p6-->>p10: ValueError
    p0->>p12: _run_sync
    p12-->>p1: getattr
    p12->>p13: validate_path
    p13->>p14: PathValidationError
    p13-->>p15: resolve
    p13-->>p16: cwd
    p13-->>p15: resolve
    p13-->>p16: cwd
    p13-->>p17: relative_to
    p13->>p14: PathValidationError
    p12->>p18: _validated_trigger_source
    p18-->>p19: str
    p18-->>p1: getattr
    p18-->>p20: bool
    p18-->>p1: getattr
```

> Call sequence diagram shows 30 of 1094 interactions; 1064 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. reset_breaker"]
    s4["4. print"]
    s5["5. print"]
    s6["6. print"]
    s7["7. print"]
    s8["8. exit"]
    s9["9. WikiLock"]
    s10["10. _lock_wait_seconds"]
    s11["11. get"]
    s12["12. strip"]
    s1 -. "getattr(args, 'reset_breaker', False)" .-> s2
    s1 -. "circuit_breaker.reset_breaker(GIT_DIR)" .-> s3
    s1 -. "print('Circuit breaker reset. Manual trigger-agent sync is re-enabled.')" .-> s4
    s1 -. "print(...)" .-> s5
    s1 -. "print(#34;To use trigger-agent, you must specify a CLI-native agent like 'claude' or 'aider'.#34;)" .-> s6
    s1 -. "print('Example: llm-wiki trigger-agent --agent claude')" .-> s7
    s1 -. "sys.exit(1)" .-> s8
    s1 -->|"WikiLock(GIT_DIR, wait_seconds=_lock_wait_seconds(...))"| s9
    s1 -->|"_lock_wait_seconds(data not statically known)"| s10
    s10 -. "os.environ.get('LLM_WIKI_LOCK_WAIT')" .-> s11
    s10 -. "raw_value.strip(data not statically known)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["output print"]
    s1 -. "output print" .-> b4
    b5["environment_read os.environ.get"]
    s10 -. "environment_read os.environ.get" .-> b5
    click s1 "../modules/trigger_cmd.md"
    click s9 "../modules/lockfile.md"
    click s10 "../modules/trigger_cmd.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `GIT_DIR`, `IDE_AGENTS`, `GIT_DIR`, `LockAcquisitionError` | - | `none` |
| `getattr` | - | - | - | - |
| `reset_breaker` | - | - | - | - |
| `print` | - | - | - | - |
| `print` | - | - | - | - |
| `print` | - | - | - | - |
| `print` | - | - | - | - |
| `exit` | - | - | - | - |
| `WikiLock` | - | - | - | - |
| `_lock_wait_seconds` | - | - | - | `0.0`, `wait_seconds` |
| `get` | - | - | - | - |
| `strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 41 | `getattr(args, 'reset_breaker', False)` |
| run | reset_breaker | 42 | `circuit_breaker.reset_breaker(GIT_DIR)` |
| run | print | 43 | `print('Circuit breaker reset. Manual trigger-agent sync is re-enabled.')` |
| run | print | 47 | `print(...)` |
| run | print | 48 | `print("To use trigger-agent, you must specify a CLI-native agent like 'claude' or 'aider'.")` |
| run | print | 51 | `print('Example: llm-wiki trigger-agent --agent claude')` |
| run | exit | 52 | `sys.exit(1)` |
| run | WikiLock | 56 | `WikiLock(GIT_DIR, wait_seconds=_lock_wait_seconds(...))` |
| run | _lock_wait_seconds | 56 | `_lock_wait_seconds(data not statically known)` |
| _lock_wait_seconds | get | 481 | `os.environ.get('LLM_WIKI_LOCK_WAIT')` |
| _lock_wait_seconds | strip | 482 | `raw_value.strip(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 43 |
| output | `print` | `run` | 47 |
| output | `print` | `run` | 48 |
| output | `print` | `run` | 51 |
| output | `print` | `run` | 59 |
| environment_read | `os.environ.get` | `_lock_wait_seconds` | 481 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 41 |
| external_call | `run` | `circuit_breaker.reset_breaker` | 42 |
| external_call | `run` | `sys.exit` | 52 |
| unresolved_call | `_lock_wait_seconds` | `raw_value.strip` | 482 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
