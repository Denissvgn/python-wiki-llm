# skills

**Entry point:** `run` (`cli`)
**Source:** [skills_cmd](../modules/skills_cmd.md)
**Modules touched:** [config](../modules/config.md), [io](../modules/io.md), [skills](../modules/skills.md), [skills_cmd](../modules/skills_cmd.md), [validation](../modules/validation.md), [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as list_bundled_skills
    participant p3 as print (src/llm_wiki_cli/commands/skills_cmd.py:run)
    participant p4 as render_skill_list_json
    participant p5 as render_skill_list_text
    participant p6 as export_skills
    participant p7 as bool
    participant p8 as _print_report
    participant p9 as SystemExit
    participant p10 as _default_install_dest
    participant p11 as validate_path
    participant p12 as install_skills
    participant p13 as root.is_dir
    participant p14 as json.dumps (src/llm_wiki_cli/services…py:render_skill_list_json)
    participant p15 as lines.append (src/llm_wiki_cli/services…py:render_skill_list_text)
    p0-->>p1: getattr(args, 'skills_action', None)
    p0-->>p1: getattr(args, 'format', 'text')
    p0->>p2: list_bundled_skills
    p0-->>p3: print (src/llm_wiki_cli/commands/skills_cmd.py:run)(render_skill_list_json(...), end='')
    p0->>p4: render_skill_list_json
    p0-->>p3: print (src/llm_wiki_cli/commands/skills_cmd.py:run)(render_skill_list_text(...), end='')
    p0->>p5: render_skill_list_text
    p0->>p6: export_skills
    p0-->>p1: getattr(args, 'dest')
    p0-->>p1: getattr(args, 'skill', None)
    p0-->>p7: bool(getattr(...))
    p0-->>p1: getattr(args, 'force', False)
    p0->>p8: _print_report
    p0-->>p9: SystemExit(1)
    p0-->>p1: getattr(args, 'dest', None)
    p0->>p10: _default_install_dest
    p0->>p11: validate_path
    p0->>p12: install_skills
    p0-->>p1: getattr(args, 'skill', None)
    p0-->>p7: bool(getattr(...))
    p0-->>p1: getattr(args, 'force', False)
    p0->>p8: _print_report
    p0-->>p9: SystemExit(1)
    p0-->>p3: print (src/llm_wiki_cli/commands/skills_cmd.py:run)(..., file=sys.stderr)
    p0-->>p9: SystemExit(1)
    p0-->>p3: print (src/llm_wiki_cli/commands/skills_cmd.py:run)('Error: missing skills action.', file=sys.stderr)
    p0-->>p9: SystemExit(1)
    p2-->>p13: root.is_dir
    p4-->>p14: json.dumps (src/llm_wiki_cli/services…py:render_skill_list_json)({...}, indent=2)
    p5-->>p15: lines.append (src/llm_wiki_cli/services…py:render_skill_list_text)(...)
```

> Call sequence diagram shows 30 of 298 interactions; 268 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 19 of 98 (79 omitted); unresolved 2 of 106 (104 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/skills.py:list_bundled_skills` | 4 | - | external | 1 |
| `src/llm_wiki_cli/services/skills.py:list_bundled_skills` | 4 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/skills.py:list_bundled_skills` | 4 | [src/llm_wiki_cli/services/skills.py](../modules/skills.md) | internal | 3 |
| `src/llm_wiki_cli/services/skills.py:_parse_skill_frontmatter` | 10 | - | unresolved | 10 |
| `src/llm_wiki_cli/services/skills.py:list_bundled_skills` | 4 | [src/llm_wiki_cli/services/io.py](../modules/io.md) | internal | 1 |
| `src/llm_wiki_cli/services/io.py:read_md` | 21 | [src/llm_wiki_cli/services/io.py](../modules/io.md) | internal | 1 |
| `src/llm_wiki_cli/services/io.py:decode_markdown_bytes` | 22 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/io.py:read_md` | 21 | - | unresolved | 1 |
> Omission summary shows 8 of 76 groups; 68 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. getattr"]
    s4["4. list_bundled_skills"]
    s5["5. root.is_dir"]
    s6["6. sorted (src/llm_wiki_cli/services…ls.py:list_bundled_skills)"]
    s7["7. root.iterdir"]
    s8["8. skill_dir.is_dir"]
    s9["9. manifest.is_file"]
    s10["10. _parse_skill_frontmatter"]
    s11["11. content.replace(…).replace(…).split"]
    s12["12. content.replace(…).replace"]
    s1 -. "getattr(args, 'skills_action', None)" .-> s2
    s1 -. "getattr(args, 'format', 'text')" .-> s3
    s1 -->|"list_bundled_skills(data not statically known)"| s4
    s4 -. "root.is_dir(data not statically known)" .-> s5
    s4 -. "sorted (src/llm_wiki_cli/services…ls.py:list_bundled_skills)(root.iterdir(...), key=...)" .-> s6
    s4 -. "root.iterdir(data not statically known)" .-> s7
    s4 -. "skill_dir.is_dir(data not statically known)" .-> s8
    s4 -. "manifest.is_file(data not statically known)" .-> s9
    s4 -->|"_parse_skill_frontmatter(read_md(...))"| s10
    s10 -. "content.replace(…).replace(…).split('\n')" .-> s11
    s10 -. "content.replace(…).replace('\r', '\n')" .-> s12
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
| `root.is_dir` | - | - | - | - |
| `sorted (src/llm_wiki_cli/services…ls.py:list_bundled_skills)` | - | - | - | - |
| `root.iterdir` | - | - | - | - |
| `skill_dir.is_dir` | - | - | - | - |
| `manifest.is_file` | - | - | - | - |
| `_parse_skill_frontmatter` | `content: str` | - | - | `(...)`, `(...)` |
| `content.replace(…).replace(…).split` | - | - | - | - |
| `content.replace(…).replace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 46 | `getattr(args, 'skills_action', None)` |
| run | getattr | 47 | `getattr(args, 'format', 'text')` |
| run | list_bundled_skills | 51 | `list_bundled_skills(data not statically known)` |
| list_bundled_skills | root.is_dir | 268 | `root.is_dir(data not statically known)` |
| list_bundled_skills | sorted (src/llm_wiki_cli/services…ls.py:list_bundled_skills) | 272 | `sorted(root.iterdir(...), key=...)` |
| list_bundled_skills | root.iterdir | 272 | `root.iterdir(data not statically known)` |
| list_bundled_skills | skill_dir.is_dir | 274 | `skill_dir.is_dir(data not statically known)` |
| list_bundled_skills | manifest.is_file | 274 | `manifest.is_file(data not statically known)` |
| list_bundled_skills | _parse_skill_frontmatter | 276 | `_parse_skill_frontmatter(read_md(...))` |
| _parse_skill_frontmatter | content.replace(…).replace(…).split | 1345 | `content.replace('\r\n', '\n').replace('\r', '\n').split('\n')` |
| _parse_skill_frontmatter | content.replace(…).replace | 1345 | `content.replace('\r\n', '\n').replace('\r', '\n')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 53 |
| output | `print` | `run` | 55 |
| output | `print` | `run` | 83 |
| output | `print` | `run` | 86 |
| mutation | `skills.append` | `list_bundled_skills` | 277 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 46 |
| external_call | `run` | `getattr` | 47 |
| unresolved_call | `list_bundled_skills` | `root.is_dir` | 268 |
| external_call | `list_bundled_skills` | `sorted` | 272 |
| unresolved_call | `list_bundled_skills` | `root.iterdir` | 272 |
| unresolved_call | `list_bundled_skills` | `skill_dir.is_dir` | 274 |
| unresolved_call | `list_bundled_skills` | `manifest.is_file` | 274 |
| unresolved_call | `_parse_skill_frontmatter` | `content.replace('\r\n', '\n').replace('\r', '\n').split` | 1345 |
| unresolved_call | `_parse_skill_frontmatter` | `content.replace('\r\n', '\n').replace` | 1345 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
