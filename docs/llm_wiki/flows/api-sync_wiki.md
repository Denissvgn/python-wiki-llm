# sync_wiki

**Entry point:** `sync_wiki` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [api](../modules/api.md), [api_contracts](../modules/api_contracts.md), and 58 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [api](../modules/api.md)
- [api_contracts](../modules/api_contracts.md)
- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
- [data_flow](../modules/data_flow.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [helper_runtime](../modules/helper_runtime.md)
- [host](../modules/host.md)
- [immutable](../modules/immutable.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_recovery](../modules/maintenance_recovery.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [path_policy](../modules/path_policy.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_implementation](../modules/python_implementation.md)
- [runtime_output](../modules/runtime_output.md)
- [scoped_sync_repair](../modules/scoped_sync_repair.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_retirement](../modules/source_retirement.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [storage_spool](../modules/storage_spool.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)
- [sync_analysis_storage](../modules/sync_analysis_storage.md)
- [sync_generated_sections](../modules/sync_generated_sections.md)
- [sync_manifest](../modules/sync_manifest.md)
- [sync_recovery](../modules/sync_recovery.md)
- [sync_runtime](../modules/sync_runtime.md)
- [sync_service](../modules/sync_service.md)
- [sync_transition_execution](../modules/sync_transition_execution.md)
- [sync_transitions](../modules/sync_transitions.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as sync_wiki
    participant p1 as discarding_output
    participant p2 as execute_sync
    participant p3 as SyncRequest
    participant p4 as InvalidRequestError
    participant p5 as WorkspaceStateError
    participant p6 as recording_errors
    participant p7 as run_request
    participant p8 as _sync_run_options_from_request
    participant p9 as _outside_tree
    participant p10 as maintenance_write_operation
    participant p11 as _run_sync_options
    participant p12 as finalize_knowledge_storage
    participant p13 as _absolute_path
    participant p14 as _prepare_sync_run
    participant p15 as cache_options_for
    participant p16 as guard_maintenance_owner
    participant p17 as governance_writer_lock
    participant p18 as storage_writer_lock
    participant p19 as prepare_boundary
    participant p20 as storage_report
    participant p21 as _job_request
    participant p22 as _surface_args
    participant p23 as _capture_spooled_wiki
    participant p24 as prune_knowledge_storage
    participant p25 as _flow_category_args
    participant p26 as repair_paths
    participant p27 as _recovery_directory
    participant p28 as report_capture
    participant p29 as str (src/llm_wiki_cli/api.py:sync_wiki)
    participant p30 as current_host().with_output (src/llm_wiki_engine/host.py:discarding_output)
    p0->>p1: discarding_output
    p0->>p2: execute_sync
    p0->>p3: SyncRequest
    p0->>p4: InvalidRequestError
    p0->>p5: WorkspaceStateError
    p2->>p6: recording_errors
    p2->>p7: run_request
    p7->>p8: _sync_run_options_from_request
    p7->>p9: _outside_tree
    p7->>p10: maintenance_write_operation
    p7->>p11: _run_sync_options
    p7->>p12: finalize_knowledge_storage
    p9->>p13: _absolute_path
    p11->>p14: _prepare_sync_run
    p8->>p15: cache_options_for
    p10->>p16: guard_maintenance_owner
    p10->>p17: governance_writer_lock
    p10->>p18: storage_writer_lock
    p11->>p19: prepare_boundary
    p12->>p20: storage_report
    p8->>p21: _job_request
    p8->>p22: _surface_args
    p10->>p23: _capture_spooled_wiki
    p12->>p24: prune_knowledge_storage
    p8->>p25: _flow_category_args
    p8->>p26: repair_paths
    p10->>p27: _recovery_directory
    p11->>p28: report_capture
    p0-->>p29: str (src/llm_wiki_cli/api.py:sync_wiki)(exc)
    p1-->>p30: current_host().with_output (src/llm_wiki_engine/host.py:discarding_output)(stdout=_Discard(...), stderr=_Discard(...))
```

> Call sequence diagram shows 30 of 1635 interactions; 1605 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 517 (516 omitted); unresolved 1 of 401 (400 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_engine/host.py:discarding_output` | 3 | [src/llm_wiki_engine/host.py](../modules/host.md) | internal | 4 |
| `src/llm_wiki_engine/host.py:using_host` | 4 | - | external | 2 |
| `src/llm_wiki_engine/host.py:using_host` | 4 | - | unresolved | 2 |
| `src/llm_wiki_engine/host.py:current_host` | 10 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/sync_runtime.py:execute_sync` | 14 | - | external | 6 |
| `src/llm_wiki_cli/services/sync_runtime.py:execute_sync` | 14 | [src/llm_wiki_cli/services/sync_runtime.py](../modules/sync_runtime.md) | internal | 3 |
| `src/llm_wiki_cli/services/sync_runtime.py:execute_sync` | 14 | - | unresolved | 4 |
| `src/llm_wiki_engine/host.py:recording_errors` | 19 | [src/llm_wiki_engine/host.py](../modules/host.md) | internal | 3 |
> Omission summary shows 8 of 474 groups; 466 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 718; effect analysis evaluated: 509, partial: 37, unavailable: 172. Counts include steps omitted from the displayed trace.

Collector observations for 546 source steps with known totals: observed: 3690, emitted: 3447, omitted: 243. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `sync_wiki` | `available` | `partial` | `available` | `19` | `11` | `8` |
| `SyncRequest` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `discarding_output` | `available` | `evaluated` | `available` | `0` | `0` | `0` |
| `using_host` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `isinstance (src/llm_wiki_engine/host.py:using_host)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_engine/host.py:using_host)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_ACTIVE.set` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_ACTIVE.reset` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `current_host().with_output (src/llm_wiki_engine/host.py:discarding_output)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `current_host` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_ACTIVE.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_Discard` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. sync_wiki"]
    s2["2. SyncRequest"]
    s3["3. discarding_output"]
    s4["4. using_host"]
    s5["5. isinstance (src/llm_wiki_engine/host.py:using_host)"]
    s6["6. TypeError (src/llm_wiki_engine/host.py:using_host)"]
    s7["7. _ACTIVE.set"]
    s8["8. _ACTIVE.reset"]
    s9["9. current_host().with_output (src/llm_wiki_engine/host.py:discarding_output)"]
    s10["10. current_host"]
    s11["11. _ACTIVE.get"]
    s12["12. _Discard"]
    s1 -->|"SyncRequest(…)"| s2
    s1 -->|"discarding_output(data not statically known)"| s3
    s3 -->|"using_host(...)"| s4
    s4 -. "isinstance (src/llm_wiki_engine/host.py:using_host)(host, Host)" .-> s5
    s4 -. "TypeError (src/llm_wiki_engine/host.py:using_host)('host must be a Host instance')" .-> s6
    s4 -. "_ACTIVE.set(host)" .-> s7
    s4 -. "_ACTIVE.reset(token)" .-> s8
    s3 -. "current_host().with_output (src/llm_wiki_engine/host.py:discarding_output)(stdout=_Discard(...), stderr=_Discard(...))" .-> s9
    s3 -->|"current_host(data not statically known)"| s10
    s10 -. "_ACTIVE.get(data not statically known)" .-> s11
    s3 -->|"_Discard(data not statically known)"| s12
    click s1 "../modules/api.md"
    click s2 "../modules/sync_service.md"
    click s3 "../modules/host.md"
    click s4 "../modules/host.md"
    click s10 "../modules/host.md"
    click s12 "../modules/host.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `sync_wiki` | `source_root: str`, `wiki_root: str`, `dry_run: bool`, `force: bool`, `preserve_semantic: bool`, `initialize_surfaces: list[str] \| None`, `flow_categories: list[str] \| None`, `exclude_tests: bool` | `SyncRequestError`, `SyncError` | - | `execute_sync(...)` |
| `SyncRequest` | - | - | - | - |
| `discarding_output` | - | - | - | - |
| `using_host` | `host: Host` | `Host` | - | - |
| `isinstance (src/llm_wiki_engine/host.py:using_host)` | - | - | - | - |
| `TypeError (src/llm_wiki_engine/host.py:using_host)` | - | - | - | - |
| `_ACTIVE.set` | - | - | - | - |
| `_ACTIVE.reset` | - | - | - | - |
| `current_host().with_output (src/llm_wiki_engine/host.py:discarding_output)` | - | - | - | - |
| `current_host` | - | `_DEFAULT` | - | `...` |
| `_ACTIVE.get` | - | - | - | - |
| `_Discard` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| sync_wiki | SyncRequest | 1273 | `SyncRequest(source_root=source_root, wiki_root=wiki_root, dry_run=dry_run, force=force, plugins=trust_source_plugins, preserve_semantic=preserve_semantic, initialize_surfaces=initialize_surfaces, flow_categories=flow_categories, exclude_tests=exclude_tests, include_tests=include_tests, openapi_file=openapi_file, clear_openapi_file=clear_openapi_file, helper_cache_dir=helper_cache_dir, source_selection=source_selection, knowledge_format=knowledge_format, rebuild_knowledge=rebuild_knowledge)` |
| sync_wiki | discarding_output | 1292 | `discarding_output(data not statically known)` |
| discarding_output | using_host | 255 | `using_host(...)` |
| using_host | isinstance (src/llm_wiki_engine/host.py:using_host) | 172 | `isinstance(host, Host)` |
| using_host | TypeError (src/llm_wiki_engine/host.py:using_host) | 173 | `TypeError('host must be a Host instance')` |
| using_host | _ACTIVE.set | 174 | `_ACTIVE.set(host)` |
| using_host | _ACTIVE.reset | 178 | `_ACTIVE.reset(token)` |
| discarding_output | current_host().with_output (src/llm_wiki_engine/host.py:discarding_output) | 255 | `current_host().with_output(stdout=_Discard(...), stderr=_Discard(...))` |
| discarding_output | current_host | 255 | `current_host(data not statically known)` |
| current_host | _ACTIVE.get | 166 | `_ACTIVE.get(data not statically known)` |
| discarding_output | _Discard | 255 | `_Discard(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `using_host` | `isinstance` | 172 |
| external_call | `using_host` | `TypeError` | 173 |
| unresolved_call | `using_host` | `_ACTIVE.reset` | 178 |
| unresolved_call | `discarding_output` | `current_host().with_output` | 255 |
| unresolved_call | `current_host` | `_ACTIVE.get` | 166 |
| step_limit | `sync_wiki` | `first 12 steps` | 0 |
| truncated_flow | `sync_wiki` | `depth limit` | 0 |

## Behavior

This flow starts at `sync_wiki` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.

Classifies the wiki lifecycle, validates the persisted source-selection and
generation policy, captures one live source snapshot, and computes source,
infrastructure, and optional-surface changes. Dry-run prints the complete plan;
broad unforced updates stop before page application. An applied run preserves supported
semantic prose, rebuilds navigation, appends the log, and commits mutually
consistent generated state so repeating the same command converges to no work.

Removed declarations in surviving documentable modules are retained as qualified
source history. Exact recorded owner revival can restore live generation without
inventing lifecycle or approval. Previously owned empty modules receive scoped parser qualification; their
module page remains current while removed declarations become retained history.
Parser/coverage gaps and ambiguous duplicate custody still stop before writes.

An applied operation retains exact bytes and identities for newly created
Markdown pages. Rejected publication emits the recovery journal hash and leaves
mandatory ownership checks active. Explicit `maintenance recover-new-pages`
previews and removes only unchanged new pages before retry; readers and sync
never perform that recovery implicitly. Adopted full-preimage recovery remains
available independently.

Broad-update errors distinguish source changes from additional generator
refresh inputs and expose bounded path samples with omitted counts. A copied,
platform-quoted preview preserves the caller's roots and planning bindings;
dry-run reveals every affected input path and its source-change reason. Source
inputs are not rewritten, and a preview never grants broad-write approval.

After successful staging, a broad preview explains how to explicitly authorize
the reviewed update by replacing dry-run with force. Force computes a fresh plan;
source, helper, selection, provider or wiki changes require renewed preview and
review. Matching generated page writes are skipped, while changed generated
content and current evidence are committed through the existing owning path.
The normal repeat run leaves active wiki state unchanged; adopted maintenance
may separately capture a recovery preimage outside the wiki. Ownership,
integrity and explicit recovery requirements remain active throughout.

Current deep normalization can also schedule an unchanged source with captured
invalid evidence for an owning refresh. The preview distinguishes this from
source edits and generator transitions, and broad guards remain active. Full
reconciliation replaces only evidence supported by fresh observations, including
same-version repairs, without a fabricated source edit or a scoped-write promise.

An explicit `--no-plugins --repair-evidence` request limits application to selected
unchanged sources with complete current producer commitments and adopted custody.
A producer transition must reproduce retained known observations. Identical
executable observations can re-anchor to their actual captured issuer, reopening
review without losing history or acknowledging it.
It repairs existing module/entity evidence together and preserves other unknowns.
Full discovery, analysis, graph reconciliation, native artifacts, an isolated
preflight copy and recovery preimages still require global work. Wider logical or
typed-graph changes refuse; broad review remains active. A matching known selected
basis causes no scoped publication, and success does not certify unselected
source evidence. Repeat strict validation after the repair.

Help connects captured evidence diagnosis and raw inspection to previewing the
ordinary owning update. Broad changes still require review and explicit authority;
force is never implied by a failure or an upgrade. Fresh malformed evidence stays
blocking. After repair, supported prose review, re-anchor and strict validation
retain their established ownership and integrity checks.

