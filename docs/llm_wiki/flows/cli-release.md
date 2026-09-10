# release

**Entry point:** `run` (`cli`)
**Source:** [release_cmd](../modules/release_cmd.md)
**Modules touched:** [release_cmd](../modules/release_cmd.md), [versioning](../modules/versioning.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as Path (src/llm_wiki_cli/commands/release_cmd.py:run)
    participant p3 as changelog_path.exists
    participant p4 as print
    participant p5 as sys.exit
    participant p6 as find_version_file
    participant p7 as Path (src/llm_wiki_cli/services…ning.py:find_version_file)
    participant p8 as candidate.exists
    participant p9 as read_version
    participant p10 as path.read_text
    participant p11 as _read_pyproject_version
    participant p12 as tomllib.loads
    participant p13 as isinstance
    participant p14 as data.get
    participant p15 as project.get
    participant p16 as VERSION_RE.match (src/llm_wiki_cli/services…y:_read_pyproject_version)
    participant p17 as data.get(…).get
    participant p18 as poetry.get
    participant p19 as _table_body
    p0-->>p1: getattr
    p0-->>p2: Path (src/llm_wiki_cli/commands/release_cmd.py:run)
    p0-->>p1: getattr
    p0-->>p3: changelog_path.exists
    p0-->>p4: print
    p0-->>p5: sys.exit
    p0->>p6: find_version_file
    p6-->>p7: Path (src/llm_wiki_cli/services…ning.py:find_version_file)
    p6-->>p8: candidate.exists
    p0-->>p4: print
    p0-->>p5: sys.exit
    p0->>p9: read_version
    p9-->>p10: path.read_text
    p9->>p11: _read_pyproject_version
    p11-->>p12: tomllib.loads
    p11-->>p13: isinstance
    p11-->>p14: data.get
    p11-->>p13: isinstance
    p11-->>p15: project.get
    p11-->>p15: project.get
    p11-->>p13: isinstance
    p11-->>p16: VERSION_RE.match (src/llm_wiki_cli/services…y:_read_pyproject_version)
    p11-->>p13: isinstance
    p11-->>p17: data.get(…).get
    p11-->>p14: data.get
    p11-->>p13: isinstance
    p11-->>p18: poetry.get
    p11-->>p13: isinstance
    p11-->>p16: VERSION_RE.match (src/llm_wiki_cli/services…y:_read_pyproject_version)
    p11->>p19: _table_body
```

> Call sequence diagram shows 30 of 100 interactions; 70 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. Path (src/llm_wiki_cli/commands/release_cmd.py:run)"]
    s4["4. getattr"]
    s5["5. changelog_path.exists"]
    s6["6. print"]
    s7["7. sys.exit"]
    s8["8. find_version_file"]
    s9["9. Path (src/llm_wiki_cli/services…ning.py:find_version_file)"]
    s10["10. candidate.exists"]
    s11["11. print"]
    s12["12. sys.exit"]
    s1 -. "getattr(args, 'root', '.')" .-> s2
    s1 -. "Path (src/llm_wiki_cli/commands/release_cmd.py:run)(getattr(...))" .-> s3
    s1 -. "getattr(args, 'changelog', 'CHANGELOG.md')" .-> s4
    s1 -. "changelog_path.exists(data not statically known)" .-> s5
    s1 -. "print(...)" .-> s6
    s1 -. "sys.exit(1)" .-> s7
    s1 -->|"find_version_file(root)"| s8
    s8 -. "Path (src/llm_wiki_cli/services…ning.py:find_version_file)(root)" .-> s9
    s8 -. "candidate.exists(data not statically known)" .-> s10
    s1 -. "print('Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).')" .-> s11
    s1 -. "sys.exit(1)" .-> s12
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
    b5["filesystem_write changelog_path.write_bytes"]
    s1 -. "filesystem_write changelog_path.write_bytes" .-> b5
    b6["output print"]
    s1 -. "output print" .-> b6
    b7["process subprocess.run"]
    s1 -. "process subprocess.run" .-> b7
    click s1 "../modules/release_cmd.md"
    click s8 "../modules/versioning.md"
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
| `run` | `args` | `sys`, `subprocess`, `sys`, `sys` | - | `none` |
| `getattr` | - | - | - | - |
| `Path (src/llm_wiki_cli/commands/release_cmd.py:run)` | - | - | - | - |
| `getattr` | - | - | - | - |
| `changelog_path.exists` | - | - | - | - |
| `print` | - | - | - | - |
| `sys.exit` | - | - | - | - |
| `find_version_file` | `root: str` | `VERSION_PATTERNS` | - | `candidate`, `None` |
| `Path (src/llm_wiki_cli/services…ning.py:find_version_file)` | - | - | - | - |
| `candidate.exists` | - | - | - | - |
| `print` | - | - | - | - |
| `sys.exit` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 118 | `getattr(args, 'root', '.')` |
| run | Path (src/llm_wiki_cli/commands/release_cmd.py:run) | 119 | `Path(getattr(...))` |
| run | getattr | 119 | `getattr(args, 'changelog', 'CHANGELOG.md')` |
| run | changelog_path.exists | 121 | `changelog_path.exists(data not statically known)` |
| run | print | 122 | `print(...)` |
| run | sys.exit | 123 | `sys.exit(1)` |
| run | find_version_file | 126 | `find_version_file(root)` |
| find_version_file | Path (src/llm_wiki_cli/services…ning.py:find_version_file) | 31 | `Path(root)` |
| find_version_file | candidate.exists | 34 | `candidate.exists(data not statically known)` |
| run | print | 128 | `print('Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).')` |
| run | sys.exit | 131 | `sys.exit(1)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 122 |
| output | `print` | `run` | 128 |
| output | `print` | `run` | 135 |
| output | `print` | `run` | 141 |
| output | `print` | `run` | 145 |
| filesystem_write | `changelog_path.write_bytes` | `run` | 150 |
| output | `print` | `run` | 151 |
| process | `subprocess.run` | `run` | 155 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 118 |
| external_call | `run` | `getattr` | 119 |
| unresolved_call | `run` | `changelog_path.exists` | 121 |
| external_call | `run` | `sys.exit` | 123 |
| unresolved_call | `find_version_file` | `candidate.exists` | 34 |
| external_call | `run` | `sys.exit` | 131 |
| step_limit | `run` | `first 12 steps` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
