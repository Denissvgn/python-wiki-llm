# trigger-agent

**Entry point:** `run` (`cli`)
**Source:** [trigger_cmd](../modules/trigger_cmd.md)
**Modules touched:** [circuit_breaker](../modules/circuit_breaker.md), [common](../modules/common.md), [config](../modules/config.md), [extraction_service](../modules/extraction_service.md), and 22 more

**Complete modules touched:**

- [circuit_breaker](../modules/circuit_breaker.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [generate_prompt_cmd](../modules/generate_prompt_cmd.md)
- [imports](../modules/imports.md)
- [io](../modules/io.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [lockfile](../modules/lockfile.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [metrics](../modules/metrics.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [redaction](../modules/redaction.md)
- [secure_file](../modules/secure_file.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [team](../modules/team.md)
- [trigger_cmd](../modules/trigger_cmd.md)
- [validation](../modules/validation.md)
- [wiki_git_policy](../modules/wiki_git_policy.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as reset_breaker
    participant p2 as _run_sync
    participant p3 as WikiLock
    participant p4 as _lock_wait_seconds
    participant p5 as save_state
    participant p6 as validate_path
    participant p7 as _validated_trigger_source
    participant p8 as _is_breaker_open
    participant p9 as _record_trigger_start
    participant p10 as _prepare_and_run_sync
    participant p11 as check_breaker
    participant p12 as record_event
    participant p13 as _preflight_trigger_source_selection
    participant p14 as _fetch_last_commit_diff
    participant p15 as _filter_trigger_diff
    participant p16 as _skip_large_diff
    participant p17 as validate_source_root
    participant p18 as _build_sync_prompt
    participant p19 as _skip_large_prompt
    participant p20 as _write_prompt_file
    participant p21 as _run_agent
    participant p22 as load_state
    participant p23 as SyncManifest.load
    participant p24 as filter_source_diff
    participant p25 as _redact_prompt_artifact
    participant p26 as _iso_now
    participant p27 as _record_trigger_failure
    participant p28 as get_inventory_result
    participant p29 as getattr (src/llm_wiki_cli/commands/trigger_cmd.py:run)
    participant p30 as raw_value.strip
    p0->>p1: reset_breaker
    p0->>p2: _run_sync
    p0->>p3: WikiLock
    p0->>p4: _lock_wait_seconds
    p1->>p5: save_state
    p2->>p6: validate_path
    p2->>p7: _validated_trigger_source
    p2->>p8: _is_breaker_open
    p2->>p9: _record_trigger_start
    p2->>p10: _prepare_and_run_sync
    p8->>p11: check_breaker
    p9->>p12: record_event
    p10->>p13: _preflight_trigger_source_selection
    p10->>p14: _fetch_last_commit_diff
    p10->>p15: _filter_trigger_diff
    p10->>p16: _skip_large_diff
    p7->>p17: validate_source_root
    p10->>p18: _build_sync_prompt
    p10->>p19: _skip_large_prompt
    p10->>p20: _write_prompt_file
    p10->>p21: _run_agent
    p11->>p22: load_state
    p13->>p23: SyncManifest.load
    p15->>p24: filter_source_diff
    p20->>p25: _redact_prompt_artifact
    p12->>p26: _iso_now
    p14->>p27: _record_trigger_failure
    p18->>p28: get_inventory_result
    p0-->>p29: getattr (src/llm_wiki_cli/commands/trigger_cmd.py:run)(args, 'reset_breaker', False)
    p4-->>p30: raw_value.strip
```

> Call sequence diagram shows 30 of 858 interactions; 828 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 328 (327 omitted); unresolved 1 of 197 (196 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/circuit_breaker.py:save_state` | 4 | [src/llm_wiki_cli/services/circuit_breaker.py](../modules/circuit_breaker.md) | internal | 1 |
| `src/llm_wiki_cli/services/circuit_breaker.py:save_state` | 4 | - | external | 5 |
| `src/llm_wiki_cli/services/circuit_breaker.py:reset_breaker` | 3 | - | external | 1 |
| `src/llm_wiki_cli/commands/trigger_cmd.py:run` | 1 | - | external | 7 |
| `src/llm_wiki_cli/commands/trigger_cmd.py:_lock_wait_seconds` | 18 | - | external | 5 |
| `src/llm_wiki_cli/commands/trigger_cmd.py:_run_sync` | 25 | - | external | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 27 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 27 | - | unresolved | 3 |
> Omission summary shows 8 of 230 groups; 222 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 334; effect analysis evaluated: 255, partial: 0, unavailable: 79. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `run` | `available` | `evaluated` | `available` |
| `getattr (src/llm_wiki_cli/commands/trigger_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `reset_breaker` | `available` | `evaluated` | `available` |
| `save_state` | `available` | `evaluated` | `available` |
| `_state_path` | `available` | `evaluated` | `available` |
| `tempfile.mkstemp` | `not_applicable` | `not_applicable` | `not_applicable` |
| `os.fdopen` | `not_applicable` | `not_applicable` | `not_applicable` |
| `json.dump` | `not_applicable` | `not_applicable` | `not_applicable` |
| `os.replace` | `not_applicable` | `not_applicable` | `not_applicable` |
| `os.unlink` | `not_applicable` | `not_applicable` | `not_applicable` |
| `dict (src/llm_wiki_cli/services…_breaker.py:reset_breaker)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `print (src/llm_wiki_cli/commands/trigger_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` |

```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/trigger_cmd.py:run)"]
    s3["3. reset_breaker"]
    s4["4. save_state"]
    s5["5. _state_path"]
    s6["6. tempfile.mkstemp"]
    s7["7. os.fdopen"]
    s8["8. json.dump"]
    s9["9. os.replace"]
    s10["10. os.unlink"]
    s11["11. dict (src/llm_wiki_cli/services…_breaker.py:reset_breaker)"]
    s12["12. print (src/llm_wiki_cli/commands/trigger_cmd.py:run)"]
    s1 -. "getattr (src/llm_wiki_cli/commands/trigger_cmd.py:run)(args, 'reset_breaker', False)" .-> s2
    s1 -->|"reset_breaker(GIT_DIR)"| s3
    s3 -->|"save_state(git_dir, dict(...))"| s4
    s4 -->|"_state_path(git_dir)"| s5
    s4 -. "tempfile.mkstemp(dir=git_dir, suffix='.tmp')" .-> s6
    s4 -. "os.fdopen(fd, 'w')" .-> s7
    s4 -. "json.dump(state, f, indent=2)" .-> s8
    s4 -. "os.replace(tmp, path)" .-> s9
    s4 -. "os.unlink(tmp)" .-> s10
    s3 -. "dict (src/llm_wiki_cli/services…_breaker.py:reset_breaker)(_DEFAULT_STATE)" .-> s11
    s1 -. "print (src/llm_wiki_cli/commands/trigger_cmd.py:run)('Circuit breaker reset. Manual trigger-agent sync is re-enabled.')" .-> s12
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
    b5["filesystem_write os.unlink"]
    s4 -. "filesystem_write os.unlink" .-> b5
    click s1 "../modules/trigger_cmd.md"
    click s3 "../modules/circuit_breaker.md"
    click s4 "../modules/circuit_breaker.md"
    click s5 "../modules/circuit_breaker.md"
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
| `run` | `args` | `GIT_DIR`, `IDE_AGENTS`, `GIT_DIR`, `LockAcquisitionError`, `TriggerFailure` | - | `none` |
| `getattr (src/llm_wiki_cli/commands/trigger_cmd.py:run)` | - | - | - | - |
| `reset_breaker` | `git_dir: Path` | `_DEFAULT_STATE` | - | - |
| `save_state` | `git_dir: Path`, `state: dict` | - | - | - |
| `_state_path` | `git_dir: Path` | `_STATE_FILE` | - | `...` |
| `tempfile.mkstemp` | - | - | - | - |
| `os.fdopen` | - | - | - | - |
| `json.dump` | - | - | - | - |
| `os.replace` | - | - | - | - |
| `os.unlink` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…_breaker.py:reset_breaker)` | - | - | - | - |
| `print (src/llm_wiki_cli/commands/trigger_cmd.py:run)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/trigger_cmd.py:run) | 49 | `getattr(args, 'reset_breaker', False)` |
| run | reset_breaker | 50 | `circuit_breaker.reset_breaker(GIT_DIR)` |
| reset_breaker | save_state | 139 | `save_state(git_dir, dict(...))` |
| save_state | _state_path | 55 | `_state_path(git_dir)` |
| save_state | tempfile.mkstemp | 56 | `tempfile.mkstemp(dir=git_dir, suffix='.tmp')` |
| save_state | os.fdopen | 58 | `os.fdopen(fd, 'w')` |
| save_state | json.dump | 59 | `json.dump(state, f, indent=2)` |
| save_state | os.replace | 60 | `os.replace(tmp, path)` |
| save_state | os.unlink | 63 | `os.unlink(tmp)` |
| reset_breaker | dict (src/llm_wiki_cli/services…_breaker.py:reset_breaker) | 139 | `dict(_DEFAULT_STATE)` |
| run | print (src/llm_wiki_cli/commands/trigger_cmd.py:run) | 51 | `print('Circuit breaker reset. Manual trigger-agent sync is re-enabled.')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 51 |
| output | `print` | `run` | 55 |
| output | `print` | `run` | 56 |
| output | `print` | `run` | 59 |
| output | `print` | `run` | 67 |
| filesystem_write | `os.unlink` | `save_state` | 63 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 49 |
| external_call | `save_state` | `tempfile.mkstemp` | 56 |
| external_call | `save_state` | `os.fdopen` | 58 |
| external_call | `save_state` | `json.dump` | 59 |
| external_call | `save_state` | `os.replace` | 60 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
