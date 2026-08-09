# compute_sync_diff

**Entry point:** `compute_sync_diff` (`api`)
**Source:** [sync_analysis](../modules/sync_analysis.md)
**Modules touched:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [knowledge_evidence](../modules/knowledge_evidence.md), [sync_analysis](../modules/sync_analysis.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compute_sync_diff
    participant p1 as SyncDiff
    participant p2 as items
    participant p3 as get
    participant p4 as add
    participant p5 as setdefault
    participant p6 as set
    participant p7 as len
    participant p8 as next
    participant p9 as iter
    participant p10 as append
    participant p11 as hash_file
    participant p12 as sha256_bytes
    participant p13 as hexdigest
    participant p14 as sha256
    participant p15 as read_bytes
    participant p16 as Path
    p0->>p1: SyncDiff
    p0-->>p2: items
    p0-->>p3: get
    p0-->>p4: add
    p0-->>p5: setdefault
    p0-->>p6: set
    p0-->>p2: items
    p0-->>p3: get
    p0-->>p4: add
    p0-->>p5: setdefault
    p0-->>p6: set
    p0-->>p2: items
    p0-->>p3: get
    p0-->>p6: set
    p0-->>p7: len
    p0-->>p7: len
    p0-->>p8: next
    p0-->>p9: iter
    p0-->>p8: next
    p0-->>p9: iter
    p0-->>p2: items
    p0-->>p10: append
    p0->>p11: hash_file
    p11->>p12: sha256_bytes
    p12-->>p13: hexdigest
    p12-->>p14: sha256
    p11-->>p15: read_bytes
    p0-->>p16: Path
    p0-->>p3: get
    p0-->>p10: append
```

> Call sequence diagram shows 30 of 140 interactions; 110 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. compute_sync_diff"]
    s2["2. SyncDiff"]
    s3["3. items"]
    s4["4. get"]
    s5["5. add"]
    s6["6. setdefault"]
    s7["7. set"]
    s8["8. items"]
    s9["9. get"]
    s10["10. add"]
    s11["11. setdefault"]
    s12["12. set"]
    s1 -->|"SyncDiff(data not statically known)"| s2
    s1 -. "manifest.sources.items(data not statically known)" .-> s3
    s1 -. "info.get('entities', [...])" .-> s4
    s1 -. "old_cls_to_files.setdefault(class_name, set()).add(filepath)" .-> s5
    s1 -. "old_cls_to_files.setdefault(class_name, set(...))" .-> s6
    s1 -. "set(data not statically known)" .-> s7
    s1 -. "inventory.items(data not statically known)" .-> s8
    s1 -. "file_data.get('classes', [...])" .-> s9
    s1 -. "new_cls_to_files.setdefault(class_record['name'], set()).add(filepath)" .-> s10
    s1 -. "new_cls_to_files.setdefault(class_record[...], set(...))" .-> s11
    s1 -. "set(data not statically known)" .-> s12
    b0["mutation diff.new_files.append"]
    s1 -. "mutation diff.new_files.append" .-> b0
    b1["mutation diff.unchanged_files.append"]
    s1 -. "mutation diff.unchanged_files.append" .-> b1
    b2["mutation diff.metadata_only_files.append"]
    s1 -. "mutation diff.metadata_only_files.append" .-> b2
    b3["mutation diff.changed_files.append"]
    s1 -. "mutation diff.changed_files.append" .-> b3
    b4["mutation diff.removed_files.append"]
    s1 -. "mutation diff.removed_files.append" .-> b4
    click s1 "../modules/sync_analysis.md"
    click s2 "../modules/sync_analysis.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compute_sync_diff` | `manifest: SyncManifest`, `inventory: dict`, `src_dir: str`, `entity_page_cache: dict[tuple[str, str], str] \| None`, `module_page_map: dict[str, str] \| None`, `source_content_hashes: Mapping[str, str] \| None` | - | `diff.moved_entities[...]`, `diff.renamed_module_pages[...]` | `diff` |
| `SyncDiff` | - | - | - | - |
| `items` | - | - | - | - |
| `get` | - | - | - | - |
| `add` | - | - | - | - |
| `setdefault` | - | - | - | - |
| `set` | - | - | - | - |
| `items` | - | - | - | - |
| `get` | - | - | - | - |
| `add` | - | - | - | - |
| `setdefault` | - | - | - | - |
| `set` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compute_sync_diff | SyncDiff | 58 | `SyncDiff(data not statically known)` |
| compute_sync_diff | items | 61 | `manifest.sources.items(data not statically known)` |
| compute_sync_diff | get | 62 | `info.get('entities', [...])` |
| compute_sync_diff | add | 63 | `old_cls_to_files.setdefault(class_name, set()).add(filepath)` |
| compute_sync_diff | setdefault | 63 | `old_cls_to_files.setdefault(class_name, set(...))` |
| compute_sync_diff | set | 63 | `set(data not statically known)` |
| compute_sync_diff | items | 66 | `inventory.items(data not statically known)` |
| compute_sync_diff | get | 67 | `file_data.get('classes', [...])` |
| compute_sync_diff | add | 68 | `new_cls_to_files.setdefault(class_record['name'], set()).add(filepath)` |
| compute_sync_diff | setdefault | 68 | `new_cls_to_files.setdefault(class_record[...], set(...))` |
| compute_sync_diff | set | 68 | `set(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `diff.new_files.append` | `compute_sync_diff` | 81 |
| mutation | `diff.unchanged_files.append` | `compute_sync_diff` | 89 |
| mutation | `diff.metadata_only_files.append` | `compute_sync_diff` | 93 |
| mutation | `diff.changed_files.append` | `compute_sync_diff` | 95 |
| mutation | `diff.removed_files.append` | `compute_sync_diff` | 99 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `compute_sync_diff` | `manifest.sources.items` | 61 |
| unresolved_call | `compute_sync_diff` | `info.get` | 62 |
| unresolved_call | `compute_sync_diff` | `old_cls_to_files.setdefault(class_name, set()).add` | 63 |
| unresolved_call | `compute_sync_diff` | `old_cls_to_files.setdefault` | 63 |
| unresolved_call | `compute_sync_diff` | `inventory.items` | 66 |
| unresolved_call | `compute_sync_diff` | `file_data.get` | 67 |
| unresolved_call | `compute_sync_diff` | `new_cls_to_files.setdefault(class_record['name'], set()).add` | 68 |
| unresolved_call | `compute_sync_diff` | `new_cls_to_files.setdefault` | 68 |
| step_limit | `compute_sync_diff` | `first 12 steps` | 0 |
| truncated_flow | `compute_sync_diff` | `depth limit` | 0 |

## Behavior

This flow starts at `compute_sync_diff` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
