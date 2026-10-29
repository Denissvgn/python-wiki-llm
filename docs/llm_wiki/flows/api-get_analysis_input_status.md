# get_analysis_input_status

**Entry point:** `get_analysis_input_status` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [api](../modules/api.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_analysis_input_status
    participant p1 as analysis_input_status
    participant p2 as registry
    participant p3 as _input_rows
    participant p4 as _status
    participant p5 as type
    participant p6 as Path(…).resolve
    participant p7 as ValueError (src/llm_wiki_cli/services…e.py:analysis_input_status)
    participant p8 as Path
    participant p9 as set (src/llm_wiki_cli/services…e.py:analysis_input_status)
    participant p10 as rules[…].values
    participant p11 as sorted (src/llm_wiki_cli/services…e.py:analysis_input_status)
    participant p12 as path.is_absolute
    participant p13 as target.is_symlink
    participant p14 as target.is_file
    participant p15 as rows.append
    participant p16 as any
    participant p17 as r[…].startswith
    participant p18 as json.loads
    participant p19 as v.relative_to(…).as_posix
    participant p20 as len
    participant p21 as path.read_text
    participant p22 as v.relative_to
    participant p23 as value.get
    participant p24 as root.rglob
    participant p25 as bool
    participant p26 as ValueError (src/llm_wiki_cli/services…alysis_capture.py:registry)
    participant p27 as set (src/llm_wiki_cli/services…sis_capture.py:_input_rows)
    p0->>p1: analysis_input_status
    p1->>p2: registry
    p1->>p3: _input_rows
    p1->>p4: _status
    p1-->>p5: type(limit)
    p1-->>p6: Path(…).resolve
    p1-->>p7: ValueError (src/llm_wiki_cli/services…e.py:analysis_input_status)('analysis input path limit must be an integer from 1 to 100')
    p1-->>p8: Path(package_root)
    p1-->>p8: Path(__file__)
    p1-->>p9: set (src/llm_wiki_cli/services…e.py:analysis_input_status)(rules[...])
    p1-->>p10: rules[…].values
    p1-->>p11: sorted (src/llm_wiki_cli/services…e.py:analysis_input_status)(required)
    p1-->>p8: Path(name)
    p1-->>p12: path.is_absolute
    p1-->>p13: target.is_symlink
    p1-->>p14: target.is_file
    p1-->>p15: rows.append({...})
    p1-->>p16: any(...)
    p1-->>p17: r[…].startswith('unclassified')
    p2-->>p18: json.loads(path.read_text(...))
    p3-->>p19: v.relative_to(…).as_posix
    p4-->>p20: len(rows)
    p2-->>p21: path.read_text('utf-8')
    p3-->>p22: v.relative_to(root)
    p4-->>p20: len(rows)
    p2-->>p23: value.get('schema_version')
    p3-->>p24: root.rglob('*.py')
    p4-->>p25: bool(rows)
    p2-->>p26: ValueError (src/llm_wiki_cli/services…alysis_capture.py:registry)('unsupported analysis registry')
    p3-->>p27: set (src/llm_wiki_cli/services…sis_capture.py:_input_rows)(v.parts)
```

> Call sequence diagram shows 30 of 57 interactions; 27 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 14 of 26 (12 omitted); unresolved 12 of 25 (13 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/analysis_capture.py:_input_rows` | 13 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/analysis_capture.py:_input_rows` | 13 | - | external | 5 |
| `src/llm_wiki_cli/services/analysis_capture.py:_status` | 37 | - | external | 7 |
| `src/llm_wiki_cli/services/analysis_capture.py:_status` | 37 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/analysis_capture.py:analysis_input_status` | 2 | [src/llm_wiki_cli/services/analysis_capture.py](../modules/analysis_capture.md) | internal | 2 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 7; effect analysis evaluated: 7, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. get_analysis_input_status"]
    s2["2. analysis_input_status"]
    s3["3. type"]
    s4["4. ValueError (src/llm_wiki_cli/services…e.py:analysis_input_status)"]
    s5["5. Path"]
    s6["6. Path(…).resolve"]
    s7["7. Path"]
    s8["8. registry"]
    s9["9. json.loads"]
    s10["10. path.read_text"]
    s11["11. value.get"]
    s12["12. ValueError (src/llm_wiki_cli/services…alysis_capture.py:registry)"]
    s1 -->|"analysis_input_status(limit=limit)"| s2
    s2 -. "type(limit)" .-> s3
    s2 -. "ValueError (src/llm_wiki_cli/services…e.py:analysis_input_status)('analysis input path limit must be an integer from 1 to 100')" .-> s4
    s2 -. "Path(package_root)" .-> s5
    s2 -. "Path(…).resolve(data not statically known)" .-> s6
    s2 -. "Path(__file__)" .-> s7
    s2 -->|"registry(root)"| s8
    s8 -. "json.loads(path.read_text(...))" .-> s9
    s8 -. "path.read_text('utf-8')" .-> s10
    s8 -. "value.get('schema_version')" .-> s11
    s8 -. "ValueError (src/llm_wiki_cli/services…alysis_capture.py:registry)('unsupported analysis registry')" .-> s12
    b0["mutation rows.append"]
    s2 -. "mutation rows.append" .-> b0
    b1["filesystem_read path.read_text"]
    s8 -. "filesystem_read path.read_text" .-> b1
    click s1 "../modules/api.md"
    click s2 "../modules/analysis_capture.md"
    click s8 "../modules/analysis_capture.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_analysis_input_status` | `limit: int` | - | - | `analysis_input_status(...)` |
| `analysis_input_status` | `package_root`, `limit` | - | - | `_status(...)`, `_status(...)`, `_status(...)` |
| `type` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…e.py:analysis_input_status)` | - | - | - | - |
| `Path` | - | - | - | - |
| `Path(…).resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `registry` | `root: Path \| None` | `REGISTRY_PATH` | - | `value` |
| `json.loads` | - | - | - | - |
| `path.read_text` | - | - | - | - |
| `value.get` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…alysis_capture.py:registry)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_analysis_input_status | analysis_input_status | 1851 | `analysis_input_status(limit=limit)` |
| analysis_input_status | type | 97 | `type(limit)` |
| analysis_input_status | ValueError (src/llm_wiki_cli/services…e.py:analysis_input_status) | 98 | `ValueError('analysis input path limit must be an integer from 1 to 100')` |
| analysis_input_status | Path | 99 | `Path(package_root)` |
| analysis_input_status | Path(…).resolve | 99 | `Path(__file__).resolve(data not statically known)` |
| analysis_input_status | Path | 99 | `Path(__file__)` |
| analysis_input_status | registry | 101 | `registry(root)` |
| registry | json.loads | 170 | `json.loads(path.read_text(...))` |
| registry | path.read_text | 170 | `path.read_text('utf-8')` |
| registry | value.get | 171 | `value.get('schema_version')` |
| registry | ValueError (src/llm_wiki_cli/services…alysis_capture.py:registry) | 172 | `ValueError('unsupported analysis registry')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `rows.append` | `analysis_input_status` | 110 |
| filesystem_read | `path.read_text` | `registry` | 170 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `analysis_input_status` | `type` | 97 |
| external_call | `analysis_input_status` | `ValueError` | 98 |
| unresolved_call | `analysis_input_status` | `Path(__file__).resolve` | 99 |
| unresolved_call | `registry` | `value.get` | 171 |
| external_call | `registry` | `ValueError` | 172 |
| step_limit | `get_analysis_input_status` | `first 12 steps` | 0 |

## Behavior

This flow starts at `get_analysis_input_status` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
