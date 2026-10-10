# load_governance

**Entry point:** `load_governance` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 4 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_model](../modules/knowledge_model.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_governance
    participant p1 as Path (src/llm_wiki_cli/services…rnance.py:load_governance)
    participant p2 as first_unsafe_path_component
    participant p3 as GovernanceError
    participant p4 as _read_governance_bytes
    participant p5 as _decode_unique_json
    participant p6 as parse_governance_ledger
    participant p7 as ledger.to_bytes
    participant p8 as GovernanceLoadResult
    participant p9 as sha256_bytes
    participant p10 as Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p11 as path.lstat
    participant p12 as json.loads
    participant p13 as _object
    participant p14 as os.fspath
    participant p15 as content.decode
    participant p16 as _exact_fields
    participant p17 as getattr (src/llm_wiki_cli/services…py:_read_governance_bytes)
    participant p18 as os.path.abspath
    participant p19 as _bundle_id
    participant p20 as lexical.is_absolute
    participant p21 as stat.S_ISLNK (src/llm_wiki_cli/services…py:_read_governance_bytes)
    participant p22 as Path.cwd
    participant p23 as bool (src/llm_wiki_cli/services…py:_read_governance_bytes)
    p0-->>p1: Path (src/llm_wiki_cli/services…rnance.py:load_governance)(wiki_dir)
    p0->>p2: first_unsafe_path_component
    p0->>p3: GovernanceError
    p0->>p4: _read_governance_bytes
    p0->>p5: _decode_unique_json
    p0->>p6: parse_governance_ledger
    p0-->>p7: ledger.to_bytes
    p0->>p3: GovernanceError
    p0->>p8: GovernanceLoadResult
    p0->>p9: sha256_bytes
    p2-->>p10: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))
    p4-->>p11: path.lstat
    p5-->>p12: json.loads(content.decode(...), object_pairs_hook=unique_object, parse_constant=reject_constant)
    p6->>p13: _object
    p2-->>p14: os.fspath(path)
    p4->>p3: GovernanceError
    p5-->>p15: content.decode('utf-8')
    p6->>p16: _exact_fields
    p2-->>p10: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.path.abspath(...))
    p4-->>p17: getattr (src/llm_wiki_cli/services…py:_read_governance_bytes)(metadata, 'st_file_attributes', 0)
    p5->>p3: GovernanceError
    p6->>p3: GovernanceError
    p2-->>p18: os.path.abspath(lexical)
    p4-->>p17: getattr (src/llm_wiki_cli/services…py:_read_governance_bytes)(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)
    p6->>p19: _bundle_id
    p2-->>p20: lexical.is_absolute
    p4-->>p21: stat.S_ISLNK (src/llm_wiki_cli/services…py:_read_governance_bytes)(metadata.st_mode)
    p6->>p3: GovernanceError
    p2-->>p22: Path.cwd
    p4-->>p23: bool (src/llm_wiki_cli/services…py:_read_governance_bytes)(reparse_flag)
```

> Call sequence diagram shows 30 of 503 interactions; 473 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 11 of 127 (116 omitted); unresolved 4 of 106 (102 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 3 | - | external | 15 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 3 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_read_governance_bytes` | 30 | - | external | 12 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_read_governance_bytes` | 30 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 6 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_read_governance_bytes` | 30 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_object` | 62 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 63 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 63 | - | unresolved | 1 |
> Omission summary shows 8 of 127 groups; 119 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_governance"]
    s2["2. Path (src/llm_wiki_cli/services…rnance.py:load_governance)"]
    s3["3. first_unsafe_path_component"]
    s4["4. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s5["5. os.fspath"]
    s6["6. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s7["7. os.path.abspath"]
    s8["8. lexical.is_absolute"]
    s9["9. Path.cwd"]
    s10["10. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s11["11. list"]
    s12["12. pending_parts.pop"]
    s1 -. "Path (src/llm_wiki_cli/services…rnance.py:load_governance)(wiki_dir)" .-> s2
    s1 -->|"first_unsafe_path_component(root)"| s3
    s3 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))" .-> s4
    s3 -. "os.fspath(path)" .-> s5
    s3 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.path.abspath(...))" .-> s6
    s3 -. "os.path.abspath(lexical)" .-> s7
    s3 -. "lexical.is_absolute(data not statically known)" .-> s8
    s3 -. "Path.cwd(data not statically known)" .-> s9
    s3 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(absolute.anchor)" .-> s10
    s3 -. "list(...)" .-> s11
    s3 -. "pending_parts.pop(0)" .-> s12
    b0["mutation pending_parts.pop"]
    s3 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/knowledge_governance.md"
    click s3 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `load_governance` | `wiki_dir: str \| Path`, `expected_bundle_id: str \| None` | `GOVERNANCE_FILENAME`, `GOVERNANCE_FILENAME` | - | `GovernanceLoadResult(...)` |
| `Path (src/llm_wiki_cli/services…rnance.py:load_governance)` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `os.path.abspath` | - | - | - | - |
| `lexical.is_absolute` | - | - | - | - |
| `Path.cwd` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `list` | - | - | - | - |
| `pending_parts.pop` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_governance | Path (src/llm_wiki_cli/services…rnance.py:load_governance) | 767 | `Path(wiki_dir)` |
| load_governance | first_unsafe_path_component | 768 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath | 51 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 59 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath | 59 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 60 | `lexical.is_absolute(data not statically known)` |
| first_unsafe_path_component | Path.cwd | 66 | `Path.cwd(data not statically known)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 67 | `Path(absolute.anchor)` |
| first_unsafe_path_component | list | 68 | `list(...)` |
| first_unsafe_path_component | pending_parts.pop | 71 | `pending_parts.pop(0)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 71 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `first_unsafe_path_component` | `os.fspath` | 51 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 59 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 60 |
| external_call | `first_unsafe_path_component` | `Path.cwd` | 66 |
| step_limit | `load_governance` | `first 12 steps` | 0 |
| truncated_flow | `load_governance` | `depth limit` | 0 |

## Behavior

This flow starts at `load_governance` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
