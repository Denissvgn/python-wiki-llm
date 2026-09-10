# compare_source_snapshot_baseline

**Entry point:** `compare_source_snapshot_baseline` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as compare_source_snapshot_baseline
    participant p1 as source_snapshot_tree_baseline
    participant p2 as isinstance
    participant p3 as DocumentationPolicyError
    participant p4 as snapshot.hashes_for
    participant p5 as TreeBaseline
    participant p6 as _hash_labeled_hashes
    participant p7 as hashlib.sha256
    participant p8 as sorted (src/llm_wiki_cli/services…cy.py:_hash_labeled_hashes)
    participant p9 as file_hashes.items
    participant p10 as digest.update
    participant p11 as path.replace(…).encode
    participant p12 as path.replace
    participant p13 as file_hash.encode
    participant p14 as digest.hexdigest
    participant p15 as IntegrityDifference
    participant p16 as tuple
    participant p17 as sorted (src/llm_wiki_cli/services…e_source_snapshot_baseline)
    participant p18 as set
    p0->>p1: source_snapshot_tree_baseline
    p1-->>p2: isinstance
    p1->>p3: DocumentationPolicyError
    p1-->>p4: snapshot.hashes_for
    p1->>p5: TreeBaseline
    p1->>p6: _hash_labeled_hashes
    p6-->>p7: hashlib.sha256
    p6-->>p8: sorted (src/llm_wiki_cli/services…cy.py:_hash_labeled_hashes)
    p6-->>p9: file_hashes.items
    p6-->>p10: digest.update
    p6-->>p11: path.replace(…).encode
    p6-->>p12: path.replace
    p6-->>p10: digest.update
    p6-->>p10: digest.update
    p6-->>p13: file_hash.encode
    p6-->>p10: digest.update
    p6-->>p14: digest.hexdigest
    p0->>p15: IntegrityDifference
    p0-->>p16: tuple
    p0-->>p17: sorted (src/llm_wiki_cli/services…e_source_snapshot_baseline)
    p0-->>p18: set
    p0-->>p18: set
    p0-->>p16: tuple
    p0-->>p17: sorted (src/llm_wiki_cli/services…e_source_snapshot_baseline)
    p0-->>p18: set
    p0-->>p18: set
    p0-->>p16: tuple
    p0-->>p17: sorted (src/llm_wiki_cli/services…e_source_snapshot_baseline)
    p0-->>p18: set
    p0-->>p18: set
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. compare_source_snapshot_baseline"]
    s2["2. source_snapshot_tree_baseline"]
    s3["3. isinstance"]
    s4["4. DocumentationPolicyError"]
    s5["5. snapshot.hashes_for"]
    s6["6. TreeBaseline"]
    s7["7. _hash_labeled_hashes"]
    s8["8. hashlib.sha256"]
    s9["9. sorted (src/llm_wiki_cli/services…cy.py:_hash_labeled_hashes)"]
    s10["10. file_hashes.items"]
    s11["11. digest.update"]
    s12["12. path.replace(…).encode"]
    s1 -->|"source_snapshot_tree_baseline(snapshot)"| s2
    s2 -. "isinstance(snapshot, SourceSnapshot)" .-> s3
    s2 -->|"DocumentationPolicyError('source snapshot baseline requires a SourceSnapshot instance.')"| s4
    s2 -. "snapshot.hashes_for(data not statically known)" .-> s5
    s2 -->|"TreeBaseline(root_display='source', tree_hash=_hash_labeled_hashes(...), file_hashes=file_hashes)"| s6
    s2 -->|"_hash_labeled_hashes(file_hashes)"| s7
    s7 -. "hashlib.sha256(data not statically known)" .-> s8
    s7 -. "sorted (src/llm_wiki_cli/services…cy.py:_hash_labeled_hashes)(file_hashes.items(...))" .-> s9
    s7 -. "file_hashes.items(data not statically known)" .-> s10
    s7 -. "digest.update(...)" .-> s11
    s7 -. "path.replace(…).encode('utf-8')" .-> s12
    b0["mutation digest.update"]
    s7 -. "mutation digest.update" .-> b0
    b1["mutation digest.update"]
    s7 -. "mutation digest.update" .-> b1
    b2["mutation digest.update"]
    s7 -. "mutation digest.update" .-> b2
    b3["mutation digest.update"]
    s7 -. "mutation digest.update" .-> b3
    click s1 "../modules/documentation_policy.md"
    click s2 "../modules/documentation_policy.md"
    click s4 "../modules/documentation_policy.md"
    click s6 "../modules/documentation_policy.md"
    click s7 "../modules/documentation_policy.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `compare_source_snapshot_baseline` | `baseline: TreeBaseline`, `snapshot: SourceSnapshot` | - | - | `IntegrityDifference(...)` |
| `source_snapshot_tree_baseline` | `snapshot: SourceSnapshot` | - | - | `TreeBaseline(...)` |
| `isinstance` | - | - | - | - |
| `DocumentationPolicyError` | - | - | - | - |
| `snapshot.hashes_for` | - | - | - | - |
| `TreeBaseline` | - | - | - | - |
| `_hash_labeled_hashes` | `file_hashes: dict[str, str]` | - | - | `...` |
| `hashlib.sha256` | - | - | - | - |
| `sorted (src/llm_wiki_cli/services…cy.py:_hash_labeled_hashes)` | - | - | - | - |
| `file_hashes.items` | - | - | - | - |
| `digest.update` | - | - | - | - |
| `path.replace(…).encode` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| compare_source_snapshot_baseline | source_snapshot_tree_baseline | 404 | `source_snapshot_tree_baseline(snapshot)` |
| source_snapshot_tree_baseline | isinstance | 386 | `isinstance(snapshot, SourceSnapshot)` |
| source_snapshot_tree_baseline | DocumentationPolicyError | 387 | `DocumentationPolicyError('source snapshot baseline requires a SourceSnapshot instance.')` |
| source_snapshot_tree_baseline | snapshot.hashes_for | 390 | `snapshot.hashes_for(data not statically known)` |
| source_snapshot_tree_baseline | TreeBaseline | 391 | `TreeBaseline(root_display='source', tree_hash=_hash_labeled_hashes(...), file_hashes=file_hashes)` |
| source_snapshot_tree_baseline | _hash_labeled_hashes | 393 | `_hash_labeled_hashes(file_hashes)` |
| _hash_labeled_hashes | hashlib.sha256 | 905 | `hashlib.sha256(data not statically known)` |
| _hash_labeled_hashes | sorted (src/llm_wiki_cli/services…cy.py:_hash_labeled_hashes) | 906 | `sorted(file_hashes.items(...))` |
| _hash_labeled_hashes | file_hashes.items | 906 | `file_hashes.items(data not statically known)` |
| _hash_labeled_hashes | digest.update | 907 | `digest.update(...)` |
| _hash_labeled_hashes | path.replace(…).encode | 907 | `path.replace('\\', '/').encode('utf-8')` |

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
| external_call | `source_snapshot_tree_baseline` | `isinstance` | 386 |
| unresolved_call | `source_snapshot_tree_baseline` | `snapshot.hashes_for` | 390 |
| external_call | `_hash_labeled_hashes` | `hashlib.sha256` | 905 |
| external_call | `_hash_labeled_hashes` | `sorted` | 906 |
| unresolved_call | `_hash_labeled_hashes` | `file_hashes.items` | 906 |
| step_limit | `compare_source_snapshot_baseline` | `first 12 steps` | 0 |

## Behavior

This flow starts at `compare_source_snapshot_baseline` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
