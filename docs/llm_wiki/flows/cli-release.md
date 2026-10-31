# release

**Entry point:** `run` (`cli`)
**Source:** [release_cmd](../modules/release_cmd.md)
**Modules touched:** [release_cmd](../modules/release_cmd.md), [versioning](../modules/versioning.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as read_version
    participant p2 as stamp_changelog
    participant p3 as find_version_file
    participant p4 as _read_pyproject_version
    participant p5 as _table_body
    participant p6 as _unreleased_has_content
    participant p7 as _detect_repo_url
    participant p8 as _project_version_is_dynamic
    participant p9 as _static_version_from_body
    participant p10 as _table_bounds
    participant p11 as getattr
    participant p12 as changelog_path.exists
    participant p13 as Path (src/llm_wiki_cli/commands/release_cmd.py:run)
    participant p14 as print
    participant p15 as sys.exit
    participant p16 as changelog_path.write_bytes
    participant p17 as new_text.encode
    participant p18 as date.today().isoformat (src/llm_wiki_cli/commands/release_cmd.py:run)
    participant p19 as date.today (src/llm_wiki_cli/commands/release_cmd.py:run)
    participant p20 as subprocess.run
    p0->>p1: read_version
    p0->>p2: stamp_changelog
    p0->>p3: find_version_file
    p1->>p4: _read_pyproject_version
    p4->>p5: _table_body
    p2->>p6: _unreleased_has_content
    p2->>p7: _detect_repo_url
    p4->>p8: _project_version_is_dynamic
    p4->>p9: _static_version_from_body
    p5->>p10: _table_bounds
    p0-->>p11: getattr(args, 'root', '.')
    p0-->>p12: changelog_path.exists
    p0-->>p13: Path (src/llm_wiki_cli/commands/release_cmd.py:run)(getattr(...))
    p0-->>p11: getattr(args, 'changelog', 'CHANGELOG.md')
    p0-->>p14: print(..., file=sys.stderr)
    p0-->>p15: sys.exit(1)
    p0-->>p14: print('Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).', file=sys.stderr)
    p0-->>p15: sys.exit(1)
    p0-->>p14: print(..., file=sys.stderr)
    p0-->>p15: sys.exit(1)
    p0-->>p14: print(..., file=sys.stderr)
    p0-->>p15: sys.exit(1)
    p0-->>p14: print('CHANGELOG.md: [Unreleased] is empty — nothing to stamp (run after the agent adds entries).')
    p0-->>p16: changelog_path.write_bytes(new_text.encode(...))
    p0-->>p17: new_text.encode('utf-8')
    p0-->>p14: print(...)
    p0-->>p18: date.today().isoformat (src/llm_wiki_cli/commands/release_cmd.py:run)
    p0-->>p19: date.today (src/llm_wiki_cli/commands/release_cmd.py:run)
    p0-->>p11: getattr(args, 'stage', False)
    p0-->>p20: subprocess.run([...], check=True, capture_output=True, shell=False, text=True)
```

> Call sequence diagram shows 30 of 100 interactions; 70 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 16 of 43 (27 omitted); unresolved 4 of 45 (41 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/versioning.py:find_version_file` | 8 | - | external | 1 |
| `src/llm_wiki_cli/services/versioning.py:find_version_file` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/versioning.py:read_version` | 13 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/versioning.py:_read_pyproject_version` | 15 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/versioning.py:_read_pyproject_version` | 15 | - | external | 6 |
| `src/llm_wiki_cli/services/versioning.py:_table_bounds` | 32 | - | unresolved | 6 |
| `src/llm_wiki_cli/services/versioning.py:_table_bounds` | 32 | - | external | 1 |
| `src/llm_wiki_cli/services/versioning.py:_project_version_is_dynamic` | 40 | - | external | 3 |
> Omission summary shows 8 of 19 groups; 11 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 13; effect analysis evaluated: 12, partial: 1, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 13 source steps with known totals: observed: 75, emitted: 71, omitted: 4. Unavailable totals are excluded.

- Effect collector omitted observations before flow assembly; displayed effects are partial.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `run` | `available` | `partial` | `available` | `22` | `18` | `4` |
| `getattr` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path (src/llm_wiki_cli/commands/release_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `getattr` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `changelog_path.exists` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `print` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `sys.exit` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `find_version_file` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `Path (src/llm_wiki_cli/services…ning.py:find_version_file)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `candidate.exists` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `print` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `sys.exit` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

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
    s1 -. "print(..., file=sys.stderr)" .-> s6
    s1 -. "sys.exit(1)" .-> s7
    s1 -->|"find_version_file(root)"| s8
    s8 -. "Path (src/llm_wiki_cli/services…ning.py:find_version_file)(root)" .-> s9
    s8 -. "candidate.exists(data not statically known)" .-> s10
    s1 -. "print('Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).', file=sys.stderr)" .-> s11
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
| `run` | `args` | `sys`, `sys`, `sys`, `sys`, `sys`, `subprocess`, `sys`, `sys` | - | `none` |
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
| run | print | 122 | `print(..., file=sys.stderr)` |
| run | sys.exit | 123 | `sys.exit(1)` |
| run | find_version_file | 126 | `find_version_file(root)` |
| find_version_file | Path (src/llm_wiki_cli/services…ning.py:find_version_file) | 31 | `Path(root)` |
| find_version_file | candidate.exists | 34 | `candidate.exists(data not statically known)` |
| run | print | 128 | `print('Error: No version file found (pyproject.toml, setup.cfg, package.json, VERSION).', file=sys.stderr)` |
| run | sys.exit | 132 | `sys.exit(1)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 122 |
| output | `print` | `run` | 128 |
| output | `print` | `run` | 136 |
| output | `print` | `run` | 142 |
| output | `print` | `run` | 146 |
| filesystem_write | `changelog_path.write_bytes` | `run` | 151 |
| output | `print` | `run` | 152 |
| process | `subprocess.run` | `run` | 156 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 118 |
| external_call | `run` | `getattr` | 119 |
| unresolved_call | `run` | `changelog_path.exists` | 121 |
| external_call | `run` | `sys.exit` | 123 |
| unresolved_call | `find_version_file` | `candidate.exists` | 34 |
| external_call | `run` | `sys.exit` | 132 |
| step_limit | `run` | `first 12 steps` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
