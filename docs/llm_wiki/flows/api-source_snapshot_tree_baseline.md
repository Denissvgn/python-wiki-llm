# source_snapshot_tree_baseline

**Entry point:** `source_snapshot_tree_baseline` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as source_snapshot_tree_baseline
    participant p1 as isinstance
    participant p2 as DocumentationPolicyError
    participant p3 as hashes_for
    participant p4 as TreeBaseline
    participant p5 as _hash_labeled_hashes
    participant p6 as sha256
    participant p7 as sorted
    participant p8 as items
    participant p9 as update
    participant p10 as encode
    participant p11 as replace
    participant p12 as hexdigest
    p0-->>p1: isinstance
    p0->>p2: DocumentationPolicyError
    p0-->>p3: hashes_for
    p0->>p4: TreeBaseline
    p0->>p5: _hash_labeled_hashes
    p5-->>p6: sha256
    p5-->>p7: sorted
    p5-->>p8: items
    p5-->>p9: update
    p5-->>p10: encode
    p5-->>p11: replace
    p5-->>p9: update
    p5-->>p9: update
    p5-->>p10: encode
    p5-->>p9: update
    p5-->>p12: hexdigest
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. source_snapshot_tree_baseline"]
    s2["2. isinstance"]
    s3["3. DocumentationPolicyError"]
    s4["4. hashes_for"]
    s5["5. TreeBaseline"]
    s6["6. _hash_labeled_hashes"]
    s7["7. sha256"]
    s8["8. sorted"]
    s9["9. items"]
    s10["10. update"]
    s11["11. encode"]
    s12["12. replace"]
    s1 -. "isinstance(snapshot, SourceSnapshot)" .-> s2
    s1 -->|"DocumentationPolicyError('source snapshot baseline requires a SourceSnapshot instance.')"| s3
    s1 -. "snapshot.hashes_for(data not statically known)" .-> s4
    s1 -->|"TreeBaseline(root_display='source', tree_hash=_hash_labeled_hashes(...), file_hashes=file_hashes)"| s5
    s1 -->|"_hash_labeled_hashes(file_hashes)"| s6
    s6 -. "hashlib.sha256(data not statically known)" .-> s7
    s6 -. "sorted(file_hashes.items(...))" .-> s8
    s6 -. "file_hashes.items(data not statically known)" .-> s9
    s6 -. "digest.update(...)" .-> s10
    s6 -. "path.replace('\\', '/').encode('utf-8')" .-> s11
    s6 -. "path.replace('\\', '/')" .-> s12
    b0["mutation digest.update"]
    s6 -. "mutation digest.update" .-> b0
    b1["mutation digest.update"]
    s6 -. "mutation digest.update" .-> b1
    b2["mutation digest.update"]
    s6 -. "mutation digest.update" .-> b2
    b3["mutation digest.update"]
    s6 -. "mutation digest.update" .-> b3
    click s1 "../modules/documentation_policy.md"
    click s3 "../modules/documentation_policy.md"
    click s5 "../modules/documentation_policy.md"
    click s6 "../modules/documentation_policy.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `source_snapshot_tree_baseline` | `snapshot: SourceSnapshot` | - | - | `TreeBaseline(...)` |
| `isinstance` | - | - | - | - |
| `DocumentationPolicyError` | - | - | - | - |
| `hashes_for` | - | - | - | - |
| `TreeBaseline` | - | - | - | - |
| `_hash_labeled_hashes` | `file_hashes: dict[str, str]` | - | - | `...` |
| `sha256` | - | - | - | - |
| `sorted` | - | - | - | - |
| `items` | - | - | - | - |
| `update` | - | - | - | - |
| `encode` | - | - | - | - |
| `replace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| source_snapshot_tree_baseline | isinstance | 386 | `isinstance(snapshot, SourceSnapshot)` |
| source_snapshot_tree_baseline | DocumentationPolicyError | 387 | `DocumentationPolicyError('source snapshot baseline requires a SourceSnapshot instance.')` |
| source_snapshot_tree_baseline | hashes_for | 390 | `snapshot.hashes_for(data not statically known)` |
| source_snapshot_tree_baseline | TreeBaseline | 391 | `TreeBaseline(root_display='source', tree_hash=_hash_labeled_hashes(...), file_hashes=file_hashes)` |
| source_snapshot_tree_baseline | _hash_labeled_hashes | 393 | `_hash_labeled_hashes(file_hashes)` |
| _hash_labeled_hashes | sha256 | 905 | `hashlib.sha256(data not statically known)` |
| _hash_labeled_hashes | sorted | 906 | `sorted(file_hashes.items(...))` |
| _hash_labeled_hashes | items | 906 | `file_hashes.items(data not statically known)` |
| _hash_labeled_hashes | update | 907 | `digest.update(...)` |
| _hash_labeled_hashes | encode | 907 | `path.replace('\\', '/').encode('utf-8')` |
| _hash_labeled_hashes | replace | 907 | `path.replace('\\', '/')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `digest.update` | `_hash_labeled_hashes` | 907 |
| mutation | `digest.update` | `_hash_labeled_hashes` | 908 |
| mutation | `digest.update` | `_hash_labeled_hashes` | 909 |
| mutation | `digest.update` | `_hash_labeled_hashes` | 910 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `source_snapshot_tree_baseline` | `isinstance` | 386 |
| unresolved_call | `source_snapshot_tree_baseline` | `snapshot.hashes_for` | 390 |
| external_call | `_hash_labeled_hashes` | `hashlib.sha256` | 905 |
| unresolved_call | `_hash_labeled_hashes` | `sorted` | 906 |
| unresolved_call | `_hash_labeled_hashes` | `file_hashes.items` | 906 |
| step_limit | `source_snapshot_tree_baseline` | `first 12 steps` | 0 |

## Behavior

This flow starts at `source_snapshot_tree_baseline` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
