# bump

**Entry point:** `run` (`cli`)
**Source:** [bump_cmd](../modules/bump_cmd.md)
**Modules touched:** [bump_cmd](../modules/bump_cmd.md), [versioning](../modules/versioning.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as find_version_file
    participant p3 as Path
    participant p4 as exists
    participant p5 as print
    participant p6 as exit
    participant p7 as read_version
    participant p8 as read_text
    participant p9 as _read_pyproject_version
    participant p10 as loads
    participant p11 as isinstance
    participant p12 as get
    participant p13 as match
    participant p14 as _table_body
    participant p15 as _table_bounds
    participant p16 as finditer
    participant p17 as strip
    participant p18 as group
    participant p19 as (end)
    p0-->>p1: getattr
    p0->>p2: find_version_file
    p2-->>p3: Path
    p2-->>p4: exists
    p0-->>p5: print
    p0-->>p6: exit
    p0->>p7: read_version
    p7-->>p8: read_text
    p7->>p9: _read_pyproject_version
    p9-->>p10: loads
    p9-->>p11: isinstance
    p9-->>p12: get
    p9-->>p11: isinstance
    p9-->>p12: get
    p9-->>p12: get
    p9-->>p11: isinstance
    p9-->>p13: match
    p9-->>p11: isinstance
    p9-->>p12: get
    p9-->>p12: get
    p9-->>p11: isinstance
    p9-->>p12: get
    p9-->>p11: isinstance
    p9-->>p13: match
    p9->>p14: _table_body
    p14->>p15: _table_bounds
    p15-->>p16: finditer
    p15-->>p17: strip
    p15-->>p18: group
    p15-->>p19: (end)
```

> Call sequence diagram shows 30 of 99 interactions; 69 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. find_version_file"]
    s4["4. Path"]
    s5["5. exists"]
    s6["6. print"]
    s7["7. exit"]
    s8["8. read_version"]
    s9["9. read_text"]
    s10["10. _read_pyproject_version"]
    s11["11. loads"]
    s12["12. isinstance"]
    s1 -. "getattr(args, 'root', '.')" .-> s2
    s1 -->|"find_version_file(root)"| s3
    s3 -. "Path(root)" .-> s4
    s3 -. "candidate.exists(data not statically known)" .-> s5
    s1 -. "print('Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).')" .-> s6
    s1 -. "sys.exit(1)" .-> s7
    s1 -->|"read_version(version_file)"| s8
    s8 -. "path.read_text(encoding='utf-8')" .-> s9
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
| `run` | `args` | `sys`, `subprocess`, `sys`, `sys` | - | - |
| `getattr` | - | - | - | - |
| `find_version_file` | `root: str` | `VERSION_PATTERNS` | - | `candidate`, `None` |
| `Path` | - | - | - | - |
| `exists` | - | - | - | - |
| `print` | - | - | - | - |
| `exit` | - | - | - | - |
| `read_version` | `path: Path` | `VERSION_PATTERNS` | - | `_read_pyproject_version(...)`, `g`, `None` |
| `read_text` | - | - | - | - |
| `_read_pyproject_version` | `text: str` | - | - | `None`, `version`, `version`, `None`, `version`, `_static_version_from_body(...)`, `None` |
| `loads` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 14 | `getattr(args, 'root', '.')` |
| run | find_version_file | 15 | `find_version_file(root)` |
| find_version_file | Path | 31 | `Path(root)` |
| find_version_file | exists | 34 | `candidate.exists(data not statically known)` |
| run | print | 18 | `print('Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).')` |
| run | exit | 21 | `sys.exit(1)` |
| run | read_version | 23 | `read_version(version_file)` |
| read_version | read_text | 41 | `path.read_text(encoding='utf-8')` |
| read_version | _read_pyproject_version | 43 | `_read_pyproject_version(content)` |
| _read_pyproject_version | loads | 90 | `tomllib.loads(text)` |
| _read_pyproject_version | isinstance | 93 | `isinstance(data, dict)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 18 |
| output | `print` | `run` | 25 |
| output | `print` | `run` | 33 |
| output | `print` | `run` | 37 |
| process | `subprocess.run` | `run` | 42 |
| output | `print` | `run` | 49 |
| output | `print` | `run` | 55 |
| output | `print` | `run` | 57 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 14 |
| unresolved_call | `find_version_file` | `candidate.exists` | 34 |
| external_call | `run` | `sys.exit` | 21 |
| unresolved_call | `read_version` | `path.read_text` | 41 |
| external_call | `_read_pyproject_version` | `tomllib.loads` | 90 |
| unresolved_call | `_read_pyproject_version` | `isinstance` | 93 |
| step_limit | `run` | `first 12 steps` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
