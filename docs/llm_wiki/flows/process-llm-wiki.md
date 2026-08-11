# llm-wiki

**Entry point:** `main` (`process`)
**Source:** [cli](../modules/cli.md)
**Modules touched:** [cli](../modules/cli.md), [resource_diagnostics](../modules/resource_diagnostics.md)

**Related modules:** [config](../modules/config.md), [extraction_jobs](../modules/extraction_jobs.md), [resource_diagnostics](../modules/resource_diagnostics.md), [services_contracts](../modules/services_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as main
    participant p1 as _build_parser
    participant p2 as ArgumentParser
    participant p3 as add_argument
    participant p4 as add_subparsers
    participant p5 as _register_commands
    participant p6 as _add_init_command
    participant p7 as add_parser
    participant p8 as add_mutually_exclusive_group
    participant p9 as _add_source_selection_argument
    participant p10 as _add_extract_command
    participant p11 as _add_include_tests_argument
    participant p12 as _add_helper_cache_argument
    p0->>p1: _build_parser
    p1-->>p2: ArgumentParser
    p1-->>p3: add_argument
    p1-->>p4: add_subparsers
    p1->>p5: _register_commands
    p5->>p6: _add_init_command
    p6-->>p7: add_parser
    p6-->>p3: add_argument
    p6-->>p3: add_argument
    p6-->>p3: add_argument
    p6-->>p3: add_argument
    p6-->>p8: add_mutually_exclusive_group
    p6-->>p3: add_argument
    p6-->>p3: add_argument
    p6->>p9: _add_source_selection_argument
    p9-->>p3: add_argument
    p5->>p10: _add_extract_command
    p10-->>p7: add_parser
    p10-->>p3: add_argument
    p10-->>p3: add_argument
    p10-->>p3: add_argument
    p10-->>p3: add_argument
    p10-->>p3: add_argument
    p10-->>p3: add_argument
    p10-->>p3: add_argument
    p10-->>p3: add_argument
    p10->>p11: _add_include_tests_argument
    p11-->>p3: add_argument
    p10->>p12: _add_helper_cache_argument
    p12-->>p3: add_argument
```

> Call sequence diagram shows 30 of 533 interactions; 503 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. main"]
    s2["2. _build_parser"]
    s3["3. ArgumentParser"]
    s4["4. add_argument"]
    s5["5. add_subparsers"]
    s6["6. _register_commands"]
    s7["7. _add_init_command"]
    s8["8. add_parser"]
    s9["9. add_argument"]
    s10["10. add_argument"]
    s11["11. add_argument"]
    s12["12. add_argument"]
    s1 -->|"_build_parser(data not statically known)"| s2
    s2 -. "argparse.ArgumentParser(description='LLM Wiki CLI')" .-> s3
    s2 -. "parser.add_argument('--version', action='version', version=...)" .-> s4
    s2 -. "parser.add_subparsers(dest='command', required=True)" .-> s5
    s2 -->|"_register_commands(subparsers)"| s6
    s6 -->|"_add_init_command(subparsers)"| s7
    s7 -. "subparsers.add_parser('init', help='Scaffold LLM Wiki structure and schema')" .-> s8
    s7 -. "init_parser.add_argument('--agent', choices=AGENT_CHOICES, default=None, help='Target agent format (default: stored agent, or generic for a new project)')" .-> s9
    s7 -. "init_parser.add_argument('--wiki-dir', default=DEFAULT_WIKI_DIR, help='Wiki directory to create (default: docs/llm_wiki)')" .-> s10
    s7 -. "init_parser.add_argument('--no-quality-hints', action='store_true', default=None, help='Omit agent quality guidelines from the constraint block')" .-> s11
    s7 -. "init_parser.add_argument('--no-skills', action='store_true', default=None, help=#34;Skip installing the wiki-reference skill into the agent's skills directory (.c…" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["environment_read os.environ.get"]
    s1 -. "environment_read os.environ.get" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["output print"]
    s1 -. "output print" .-> b4
    click s1 "../modules/cli.md"
    click s2 "../modules/cli.md"
    click s6 "../modules/cli.md"
    click s7 "../modules/cli.md"
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
| `main` | - | `PathValidationError`, `sys`, `sys`, `sys` | - | - |
| `_build_parser` | - | `__version__` | - | `parser` |
| `ArgumentParser` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `add_subparsers` | - | - | - | - |
| `_register_commands` | `subparsers` | - | - | - |
| `_add_init_command` | `subparsers` | `AGENT_CHOICES`, `DEFAULT_WIKI_DIR` | - | - |
| `add_parser` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `add_argument` | - | - | - | - |
| `add_argument` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| main | _build_parser | 2314 | `_build_parser(data not statically known)` |
| _build_parser | ArgumentParser | 162 | `argparse.ArgumentParser(description='LLM Wiki CLI')` |
| _build_parser | add_argument | 163 | `parser.add_argument('--version', action='version', version=...)` |
| _build_parser | add_subparsers | 166 | `parser.add_subparsers(dest='command', required=True)` |
| _build_parser | _register_commands | 167 | `_register_commands(subparsers)` |
| _register_commands | _add_init_command | 172 | `_add_init_command(subparsers)` |
| _add_init_command | add_parser | 242 | `subparsers.add_parser('init', help='Scaffold LLM Wiki structure and schema')` |
| _add_init_command | add_argument | 245 | `init_parser.add_argument('--agent', choices=AGENT_CHOICES, default=None, help='Target agent format (default: stored agent, or generic for a new project)')` |
| _add_init_command | add_argument | 251 | `init_parser.add_argument('--wiki-dir', default=DEFAULT_WIKI_DIR, help='Wiki directory to create (default: docs/llm_wiki)')` |
| _add_init_command | add_argument | 256 | `init_parser.add_argument('--no-quality-hints', action='store_true', default=None, help='Omit agent quality guidelines from the constraint block')` |
| _add_init_command | add_argument | 262 | `init_parser.add_argument('--no-skills', action='store_true', default=None, help="Skip installing the wiki-reference skill into the agent's skills directory (.claude/skills for claude, .llm-wiki/skills otherwise)")` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `main` | 2320 |
| output | `print` | `main` | 2323 |
| environment_read | `os.environ.get` | `main` | 2326 |
| output | `print` | `main` | 2328 |
| output | `print` | `main` | 2331 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_build_parser` | `argparse.ArgumentParser` | 162 |
| unresolved_call | `_build_parser` | `parser.add_argument` | 163 |
| unresolved_call | `_build_parser` | `parser.add_subparsers` | 166 |
| unresolved_call | `_add_init_command` | `subparsers.add_parser` | 242 |
| unresolved_call | `_add_init_command` | `init_parser.add_argument` | 245 |
| unresolved_call | `_add_init_command` | `init_parser.add_argument` | 251 |
| unresolved_call | `_add_init_command` | `init_parser.add_argument` | 256 |
| unresolved_call | `_add_init_command` | `init_parser.add_argument` | 262 |
| step_limit | `main` | `first 12 steps` | 0 |

## Behavior

Serves as the installed `llm-wiki` process entry point. It builds the full
argument parser, handles version output, and dispatches the selected command to
its command or service module. Missing commands are rejected with usage
guidance; validated
path-policy failures are rendered as concise errors and return a nonzero
process status.
