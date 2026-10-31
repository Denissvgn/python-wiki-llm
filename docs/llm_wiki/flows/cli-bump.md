# bump

**Entry point:** `run` (`cli`)
**Source:** [bump_cmd](../modules/bump_cmd.md)
**Modules touched:** [bump_cmd](../modules/bump_cmd.md), [versioning](../modules/versioning.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as read_version
    participant p2 as write_version
    participant p3 as find_version_file
    participant p4 as bump_patch
    participant p5 as bump_minor
    participant p6 as _read_pyproject_version
    participant p7 as _write_pyproject_version
    participant p8 as _table_body
    participant p9 as _table_bounds
    participant p10 as _project_version_is_dynamic
    participant p11 as _replace_static_version_line
    participant p12 as _static_version_from_body
    participant p13 as getattr
    participant p14 as (…).strip
    participant p15 as print
    participant p16 as sys.exit
    participant p17 as subprocess.run
    participant p18 as str
    participant p19 as Path
    p0->>p1: read_version
    p0->>p2: write_version
    p0->>p3: find_version_file
    p0->>p4: bump_patch
    p0->>p5: bump_minor
    p1->>p6: _read_pyproject_version
    p2->>p7: _write_pyproject_version
    p6->>p8: _table_body
    p7->>p9: _table_bounds
    p7->>p10: _project_version_is_dynamic
    p7->>p11: _replace_static_version_line
    p6->>p12: _static_version_from_body
    p0-->>p13: getattr(args, 'root', '.')
    p0-->>p14: (…).strip
    p0-->>p15: print('Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).', file=sys.stderr)
    p0-->>p16: sys.exit(1)
    p0-->>p15: print(..., file=sys.stderr)
    p0-->>p16: sys.exit(1)
    p0-->>p15: print(..., file=sys.stderr)
    p0-->>p16: sys.exit(1)
    p0-->>p15: print(...)
    p0-->>p13: getattr(args, 'stage', False)
    p0-->>p17: subprocess.run([...], check=True, capture_output=True, text=True)
    p0-->>p18: str(version_file)
    p0-->>p15: print('Error: git not found could not stage version file.', file=sys.stderr)
    p0-->>p16: sys.exit(1)
    p0-->>p15: print(..., file=sys.stderr)
    p0-->>p15: print(detail, file=sys.stderr)
    p0-->>p16: sys.exit(1)
    p3-->>p19: Path(root)
```

> Call sequence diagram shows 30 of 99 interactions; 69 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 17 of 40 (23 omitted); unresolved 1 of 41 (40 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/versioning.py:find_version_file` | 3 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/versioning.py:read_version` | 8 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/versioning.py:_read_pyproject_version` | 10 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/versioning.py:_read_pyproject_version` | 10 | - | external | 6 |
| `src/llm_wiki_cli/services/versioning.py:_table_body` | 26 | [src/llm_wiki_cli/services/versioning.py](../modules/versioning.md) | internal | 1 |
| `src/llm_wiki_cli/services/versioning.py:_table_bounds` | 27 | - | unresolved | 6 |
| `src/llm_wiki_cli/services/versioning.py:_table_bounds` | 27 | - | external | 1 |
| `src/llm_wiki_cli/services/versioning.py:_read_pyproject_version` | 10 | [src/llm_wiki_cli/services/versioning.py](../modules/versioning.md) | internal | 3 |
> Omission summary shows 8 of 22 groups; 14 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 19; effect analysis evaluated: 19, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 19 source steps with known totals: observed: 86, emitted: 86, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. find_version_file"]
    s4["4. Path"]
    s5["5. candidate.exists"]
    s6["6. print"]
    s7["7. sys.exit"]
    s8["8. read_version"]
    s9["9. path.read_text (src/llm_wiki_cli/services…ersioning.py:read_version)"]
    s10["10. _read_pyproject_version"]
    s11["11. tomllib.loads"]
    s12["12. isinstance"]
    s1 -. "getattr(args, 'root', '.')" .-> s2
    s1 -->|"find_version_file(root)"| s3
    s3 -. "Path(root)" .-> s4
    s3 -. "candidate.exists(data not statically known)" .-> s5
    s1 -. "print('Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).', file=sys.stderr)" .-> s6
    s1 -. "sys.exit(1)" .-> s7
    s1 -->|"read_version(version_file)"| s8
    s8 -. "path.read_text (src/llm_wiki_cli/services…ersioning.py:read_version)(encoding='utf-8')" .-> s9
    s8 -->|"_read_pyproject_version(content)"| s10
    s10 -. "tomllib.loads(text)" .-> s11
    s10 -. "isinstance(data, dict)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["process subprocess.run"]
    s1 -. "process subprocess.run" .-> b4
    b5["output print"]
    s1 -. "output print" .-> b5
    b6["output print"]
    s1 -. "output print" .-> b6
    b7["output print"]
    s1 -. "output print" .-> b7
    click s1 "../modules/bump_cmd.md"
    click s3 "../modules/versioning.md"
    click s8 "../modules/versioning.md"
    click s10 "../modules/versioning.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
    class b7 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `sys`, `sys`, `sys`, `sys`, `subprocess`, `sys`, `sys` | - | - |
| `getattr` | - | - | - | - |
| `find_version_file` | `root: str` | `VERSION_PATTERNS` | - | `candidate`, `None` |
| `Path` | - | - | - | - |
| `candidate.exists` | - | - | - | - |
| `print` | - | - | - | - |
| `sys.exit` | - | - | - | - |
| `read_version` | `path: Path` | `VERSION_PATTERNS` | - | `_read_pyproject_version(...)`, `g`, `None` |
| `path.read_text (src/llm_wiki_cli/services…ersioning.py:read_version)` | - | - | - | - |
| `_read_pyproject_version` | `text: str` | - | - | `None`, `version`, `version`, `None`, `version`, `_static_version_from_body(...)`, `None` |
| `tomllib.loads` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 14 | `getattr(args, 'root', '.')` |
| run | find_version_file | 15 | `find_version_file(root)` |
| find_version_file | Path | 31 | `Path(root)` |
| find_version_file | candidate.exists | 34 | `candidate.exists(data not statically known)` |
| run | print | 18 | `print('Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).', file=sys.stderr)` |
| run | sys.exit | 22 | `sys.exit(1)` |
| run | read_version | 24 | `read_version(version_file)` |
| read_version | path.read_text (src/llm_wiki_cli/services…ersioning.py:read_version) | 41 | `path.read_text(encoding='utf-8')` |
| read_version | _read_pyproject_version | 43 | `_read_pyproject_version(content)` |
| _read_pyproject_version | tomllib.loads | 90 | `tomllib.loads(text)` |
| _read_pyproject_version | isinstance | 93 | `isinstance(data, dict)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 18 |
| output | `print` | `run` | 26 |
| output | `print` | `run` | 34 |
| output | `print` | `run` | 38 |
| process | `subprocess.run` | `run` | 43 |
| output | `print` | `run` | 50 |
| output | `print` | `run` | 56 |
| output | `print` | `run` | 58 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 14 |
| unresolved_call | `find_version_file` | `candidate.exists` | 34 |
| external_call | `run` | `sys.exit` | 22 |
| unresolved_call | `read_version` | `path.read_text` | 41 |
| unresolved_call | `_read_pyproject_version` | `tomllib.loads` | 90 |
| external_call | `_read_pyproject_version` | `isinstance` | 93 |
| step_limit | `run` | `first 12 steps` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
