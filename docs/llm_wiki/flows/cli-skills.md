# skills

**Entry point:** `run` (`cli`)
**Source:** [skills_cmd](../modules/skills_cmd.md)
**Modules touched:** [config](../modules/config.md), [io](../modules/io.md), [skills](../modules/skills.md), [skills_cmd](../modules/skills_cmd.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as list_bundled_skills
    participant p3 as is_dir
    participant p4 as sorted
    participant p5 as iterdir
    participant p6 as is_file
    participant p7 as _parse_skill_frontmatter
    participant p8 as split
    participant p9 as replace
    participant p10 as strip
    participant p11 as partition
    participant p12 as read_md
    participant p13 as read_bytes
    participant p14 as decode
    participant p15 as append
    participant p16 as BundledSkill
    participant p17 as _skill_files
    participant p18 as as_posix
    participant p19 as relative_to
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0->>p2: list_bundled_skills
    p2-->>p3: is_dir
    p2-->>p4: sorted
    p2-->>p5: iterdir
    p2-->>p3: is_dir
    p2-->>p6: is_file
    p2->>p7: _parse_skill_frontmatter
    p7-->>p8: split
    p7-->>p9: replace
    p7-->>p9: replace
    p7-->>p10: strip
    p7-->>p10: strip
    p7-->>p11: partition
    p7-->>p10: strip
    p7-->>p10: strip
    p7-->>p10: strip
    p7-->>p10: strip
    p2->>p12: read_md
    p12-->>p13: read_bytes
    p12-->>p14: decode
    p12-->>p14: decode
    p12-->>p9: replace
    p12-->>p9: replace
    p2-->>p15: append
    p2->>p16: BundledSkill
    p2->>p17: _skill_files
    p17-->>p18: as_posix
    p17-->>p19: relative_to
```

> Call sequence diagram shows 30 of 274 interactions; 244 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. getattr"]
    s4["4. list_bundled_skills"]
    s5["5. is_dir"]
    s6["6. sorted"]
    s7["7. iterdir"]
    s8["8. is_dir"]
    s9["9. is_file"]
    s10["10. _parse_skill_frontmatter"]
    s11["11. split"]
    s12["12. replace"]
    s1 -. "getattr(args, 'skills_action', None)" .-> s2
    s1 -. "getattr(args, 'format', 'text')" .-> s3
    s1 -->|"list_bundled_skills(data not statically known)"| s4
    s4 -. "root.is_dir(data not statically known)" .-> s5
    s4 -. "sorted(root.iterdir(...), key=...)" .-> s6
    s4 -. "root.iterdir(data not statically known)" .-> s7
    s4 -. "skill_dir.is_dir(data not statically known)" .-> s8
    s4 -. "manifest.is_file(data not statically known)" .-> s9
    s4 -->|"_parse_skill_frontmatter(read_md(...))"| s10
    s10 -. "content.replace('\r\n', '\n').replace('\r', '\n').split('\n')" .-> s11
    s10 -. "content.replace('\r\n', '\n').replace('\r', '\n')" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["mutation skills.append"]
    s4 -. "mutation skills.append" .-> b4
    click s1 "../modules/skills_cmd.md"
    click s4 "../modules/skills.md"
    click s10 "../modules/skills.md"
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
| `run` | `args` | `SkillsError`, `sys`, `sys` | - | `none`, `none`, `none` |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `list_bundled_skills` | `skills_root: Path \| None` | `BUNDLED_SKILLS_ROOT`, `SKILL_MANIFEST_NAME` | - | `[...]`, `skills` |
| `is_dir` | - | - | - | - |
| `sorted` | - | - | - | - |
| `iterdir` | - | - | - | - |
| `is_dir` | - | - | - | - |
| `is_file` | - | - | - | - |
| `_parse_skill_frontmatter` | `content: str` | - | - | `(...)`, `(...)` |
| `split` | - | - | - | - |
| `replace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 46 | `getattr(args, 'skills_action', None)` |
| run | getattr | 47 | `getattr(args, 'format', 'text')` |
| run | list_bundled_skills | 51 | `list_bundled_skills(data not statically known)` |
| list_bundled_skills | is_dir | 245 | `root.is_dir(data not statically known)` |
| list_bundled_skills | sorted | 249 | `sorted(root.iterdir(...), key=...)` |
| list_bundled_skills | iterdir | 249 | `root.iterdir(data not statically known)` |
| list_bundled_skills | is_dir | 251 | `skill_dir.is_dir(data not statically known)` |
| list_bundled_skills | is_file | 251 | `manifest.is_file(data not statically known)` |
| list_bundled_skills | _parse_skill_frontmatter | 253 | `_parse_skill_frontmatter(read_md(...))` |
| _parse_skill_frontmatter | split | 1269 | `content.replace('\r\n', '\n').replace('\r', '\n').split('\n')` |
| _parse_skill_frontmatter | replace | 1269 | `content.replace('\r\n', '\n').replace('\r', '\n')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 53 |
| output | `print` | `run` | 55 |
| output | `print` | `run` | 83 |
| output | `print` | `run` | 86 |
| mutation | `skills.append` | `list_bundled_skills` | 254 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 46 |
| unresolved_call | `run` | `getattr` | 47 |
| unresolved_call | `list_bundled_skills` | `root.is_dir` | 245 |
| unresolved_call | `list_bundled_skills` | `sorted` | 249 |
| unresolved_call | `list_bundled_skills` | `root.iterdir` | 249 |
| unresolved_call | `list_bundled_skills` | `skill_dir.is_dir` | 251 |
| unresolved_call | `list_bundled_skills` | `manifest.is_file` | 251 |
| unresolved_call | `_parse_skill_frontmatter` | `content.replace('\r\n', '\n').replace('\r', '\n').split` | 1269 |
| unresolved_call | `_parse_skill_frontmatter` | `content.replace('\r\n', '\n').replace` | 1269 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
